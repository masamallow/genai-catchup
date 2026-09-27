#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "feedparser>=6.0.11",
#   "httpx>=0.27",
#   "pyyaml>=6",
# ]
# ///
"""Fetch curated feeds and write candidate items for one catch-up run.

Usage:
    uv run scripts/fetch_feeds.py fetch [--since YYYY-MM-DD | --days N] [--out work] [--include-disabled] [--source ID ...]
    uv run scripts/fetch_feeds.py mark-seen [--candidates work/candidates.json]

The window starts at the date of the previous run, taken from the newest note under
content/*/research/ in any language (a run every Tuesday, Thursday and Saturday
therefore collects "since the last run"). `--since` or `--days` override it, and are
required when there is no note. A window always starts at local midnight of a
date, never at a time of day: the previous run's date is fetched again in full, whatever
time that run fetched, so no item falls between two windows. Items already recorded in
state/seen.json are dropped, and the agent judges the rest against the previous note.

`fetch` never writes to state/: it only produces work/candidates.json and
work/candidates.md. Run `mark-seen` after the research note is written, so a
failed run does not hide items from the next one.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "sources.yaml"
SEEN_FILE = ROOT / "state" / "seen.json"
CONTENT_DIR = ROOT / "content"
NOTE_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
USER_AGENT = "genai-catchup/1.0 (personal feed reader)"
ACCEPT = "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "ref", "fbclid", "gclid", "mc_cid", "mc_eid",
}
SEEN_TTL_DAYS = 180
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


@dataclass
class Item:
    source_id: str
    title: str
    link: str
    published: str | None
    summary: str
    tier: int
    kind: str
    reliability: str
    track: str
    role: str


def normalize_url(url: str) -> str:
    """Drop tracking parameters so the same article dedupes across feeds.

    The fragment is kept: changelog and release-note feeds link every entry as
    `page#entry`, and dropping it would mark all future entries of the page as seen.
    """
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), parts.fragment))


def strip_html(text: str) -> str:
    return WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", text or ""))).strip()


def entry_date(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            try:
                return datetime(*value[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def entry_summary(entry) -> str:
    content = entry.get("content")
    raw = entry.get("summary") or (content[0].get("value") if content else "") or ""
    return strip_html(raw)[:320]


def load_sources(include_disabled: bool, only: set[str] | None) -> list[dict]:
    data = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    selected = []
    for src in data["sources"]:
        merged = {**defaults, **src}
        if only:
            if merged["id"] in only:
                selected.append(merged)
            continue
        if merged.get("enabled", True) or include_disabled:
            selected.append(merged)
    return selected


def previous_run_date() -> date | None:
    """Date of the newest research note in any language, i.e. the previous run."""
    dates = []
    for note in CONTENT_DIR.glob("*/research/*.md"):
        m = NOTE_DATE_RE.match(note.name)
        if m:
            dates.append(date.fromisoformat(m.group(1)))
    return max(dates) if dates else None


def local_midnight(day: date) -> datetime:
    """Start of `day` in the local timezone, the one `date +%F` uses to name the notes."""
    return datetime.combine(day, time.min).astimezone()


def resolve_window(args: argparse.Namespace, now: datetime) -> tuple[datetime, str]:
    """Return the window start (local midnight of a date) and how it was chosen."""
    today = now.astimezone().date()
    if args.since:
        day = date.fromisoformat(args.since)
        return local_midnight(day), f"--since {day}"
    if args.days:
        return local_midnight(today - timedelta(days=args.days)), f"--days {args.days}"
    prev = previous_run_date()
    if prev is None:
        raise SystemExit("no research note under content/*/research/: give the window with --since or --days")
    return local_midnight(prev), f"previous run {prev}, whole day included"


def load_seen() -> dict:
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text(encoding="utf-8") or "{}")
    return {}


def matches_filter(src: dict, title: str, summary: str) -> bool:
    keywords = (src.get("filter") or {}).get("any")
    if not keywords:
        return True
    haystack = f"{title} {summary}".lower()
    return any(str(k).lower() in haystack for k in keywords)


def fetch_one(src: dict, client: httpx.Client, since: datetime, seen: dict):
    try:
        resp = client.get(src["feed"])
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception as exc:  # noqa: BLE001 - a failing source must not stop the run
        return src, [], f"{type(exc).__name__}: {' '.join(str(exc).split())[:140]}"
    if parsed.bozo and not parsed.entries:
        return src, [], f"unparsable feed: {str(getattr(parsed, 'bozo_exception', ''))[:140]}"

    items: list[Item] = []
    for entry in parsed.entries:
        link = (entry.get("link") or "").strip()
        if not link or normalize_url(link) in seen:
            continue
        title = strip_html(entry.get("title", "")) or "(no title)"
        published = entry_date(entry)
        if published and published < since:
            continue
        summary = entry_summary(entry)
        if not matches_filter(src, title, summary):
            continue
        items.append(Item(
            source_id=src["id"], title=title, link=link,
            # local time, so the dates in candidates.md are on the same calendar as the window
            published=published.astimezone().isoformat(timespec="minutes") if published else None,
            summary=summary, tier=int(src["tier"]), kind=src["kind"],
            reliability=src["reliability"], track=src["track"], role=src.get("role", ""),
        ))
    items.sort(key=lambda i: i.published or "", reverse=True)
    return src, items[: int(src.get("max_items", 15))], None


def render_markdown(payload: dict, sources: list[dict]) -> str:
    by_source: dict[str, list[dict]] = {}
    for item in payload["items"]:
        by_source.setdefault(item["source_id"], []).append(item)
    status = {s["id"]: s for s in payload["sources"]}
    ok = [s for s in payload["sources"] if s["ok"]]
    failed = [s for s in payload["sources"] if not s["ok"]]

    lines = [
        f"# Candidates — generated {payload['generated_at']}",
        "",
        f"- Window: since {payload['since']} ({payload['window_reason']})",
        f"- Sources: {len(payload['sources'])} fetched, {len(ok)} ok, {len(failed)} failed",
        f"- New items: {len(payload['items'])} (already-seen items removed)",
        "",
    ]
    if failed:
        lines += ["## Failed sources", ""]
        lines += [f"- `{s['id']}`: {s['error']}" for s in failed]
        lines.append("")
    for tier in (1, 2, 3):
        tier_sources = [s for s in sources if int(s["tier"]) == tier]
        if not tier_sources:
            continue
        lines += [f"## Tier {tier}", ""]
        for src in tier_sources:
            items = by_source.get(src["id"], [])
            meta = f"{src['kind']}, {src.get('lang', 'en')}, {src['reliability']}, {src['track']}, {src.get('role', '')}"
            lines.append(f"### {src['name']} `{src['id']}` ({meta}) — {len(items)} new")
            lines.append("")
            if not items:
                note = "failed" if not status[src["id"]]["ok"] else "nothing new"
                lines += [f"- ({note})", ""]
                continue
            for item in items:
                day = (item["published"] or "undated")[:10]
                lines.append(f"- {day} | [{item['title']}]({item['link']})")
                if item["summary"]:
                    lines.append(f"    - {item['summary']}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_fetch(args: argparse.Namespace) -> int:
    sources = load_sources(args.include_disabled, set(args.source) if args.source else None)
    now = datetime.now(timezone.utc)
    since, window_reason = resolve_window(args, now)
    seen = load_seen()
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": USER_AGENT, "Accept": ACCEPT}
    timeout = httpx.Timeout(30.0, connect=15.0)
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda s: fetch_one(s, client, since, seen), sources))

    source_status, items = [], []
    for src, found, error in results:
        source_status.append({
            "id": src["id"], "name": src["name"], "tier": int(src["tier"]),
            "ok": error is None, "error": error, "count": len(found),
        })
        items.extend(found)
    order = {s["id"]: i for i, s in enumerate(sources)}
    items.sort(key=lambda i: (i.tier, order[i.source_id], i.published or ""))

    payload = {
        "generated_at": now.isoformat(timespec="minutes"),
        "since": since.isoformat(timespec="minutes"),
        "window_reason": window_reason,
        "sources": source_status,
        "items": [asdict(i) for i in items],
    }
    (out_dir / "candidates.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "candidates.md").write_text(render_markdown(payload, sources), encoding="utf-8")

    failed = [s for s in source_status if not s["ok"]]
    print(f"window since {since.isoformat(timespec='minutes')} ({window_reason})")
    print(f"{len(items)} new items from {len(sources) - len(failed)}/{len(sources)} sources -> {out_dir / 'candidates.md'}")
    for s in failed:
        print(f"  failed: {s['id']}: {s['error']}", file=sys.stderr)
    return 0


def cmd_mark_seen(args: argparse.Namespace) -> int:
    payload = json.loads((ROOT / args.candidates).read_text(encoding="utf-8"))
    seen = load_seen()
    today = date.today().isoformat()
    added = 0
    for item in payload["items"]:
        key = normalize_url(item["link"])
        if key not in seen:
            seen[key] = {"first_seen": today, "source": item["source_id"]}
            added += 1
    cutoff = (date.today() - timedelta(days=SEEN_TTL_DAYS)).isoformat()
    seen = {k: v for k, v in seen.items() if v.get("first_seen", today) >= cutoff}
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(dict(sorted(seen.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"marked {added} new URLs as seen ({len(seen)} kept, TTL {SEEN_TTL_DAYS} days)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch feeds and write work/candidates.{json,md}")
    window = fetch.add_mutually_exclusive_group()
    window.add_argument("--since", metavar="YYYY-MM-DD", help="first day of the window (default: date of the previous research note)")
    window.add_argument("--days", type=int, help="start the window N days before today instead of at the previous note")
    fetch.add_argument("--out", default="work", help="output directory relative to the repo root")
    fetch.add_argument("--include-disabled", action="store_true", help="also fetch sources with enabled: false")
    fetch.add_argument("--source", action="append", metavar="ID", help="fetch only these source ids (repeatable)")
    fetch.set_defaults(func=cmd_fetch)

    mark = sub.add_parser("mark-seen", help="record all current candidates in state/seen.json")
    mark.add_argument("--candidates", default="work/candidates.json")
    mark.set_defaults(func=cmd_mark_seen)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
