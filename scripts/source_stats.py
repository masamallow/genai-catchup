#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Count how often each source was actually used in research notes.

Reads `sources_used` from the front matter of content/<lang>/research/*.md (each run is
counted once, from its English edition when present) and joins it with sources.yaml. Use the result for the monthly source review: enabled sources that
never make it into a note are demotion candidates, disabled ones that keep
showing up in web searches are promotion candidates.

Usage: uv run scripts/source_stats.py [--since YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LANG = "en"
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since", default="0000-00-00", help="only count notes dated on or after this day")
    args = parser.parse_args(argv)

    used: Counter[str] = Counter()
    last_used: dict[str, str] = {}
    editions: dict[str, dict[str, dict]] = {}  # day -> lang -> front matter
    for path in sorted((ROOT / "content").glob("*/research/*.md")):
        m = FRONT_MATTER_RE.match(path.read_text(encoding="utf-8"))
        front = (yaml.safe_load(m.group(1)) if m else {}) or {}
        day = str(front.get("date") or path.stem)
        editions.setdefault(day, {})[path.parts[-3]] = front
    notes = 0
    for day, by_lang in sorted(editions.items()):
        if day < args.since:
            continue
        front = by_lang.get(DEFAULT_LANG) or next(iter(by_lang.values()))
        notes += 1
        for sid in front.get("sources_used") or []:
            used[sid] += 1
            last_used[sid] = max(last_used.get(sid, ""), day)

    data = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    rows = []
    for src in data["sources"]:
        merged = {**defaults, **src}
        rows.append((used[merged["id"]], merged["id"], merged["name"], merged["tier"], merged.get("enabled", True), last_used.get(merged["id"], "-")))
    rows.sort(key=lambda r: (-r[0], r[3], r[1]))

    print(f"research notes counted: {notes}\n")
    print("| used | id | name | tier | enabled | last used |")
    print("| ---: | --- | --- | ---: | --- | --- |")
    for count, sid, name, tier, enabled, last in rows:
        print(f"| {count} | `{sid}` | {name} | {tier} | {'yes' if enabled else 'no'} | {last} |")
    idle = [sid for count, sid, _, _, enabled, _ in rows if enabled and count == 0]
    if idle:
        print("\nEnabled but never used (demotion candidates): " + ", ".join(f"`{s}`" for s in idle))
    unknown = sorted(set(used) - {r[1] for r in rows})
    if unknown:
        print("\nUsed in notes but missing from sources.yaml: " + ", ".join(f"`{s}`" for s in unknown))
    return 0


if __name__ == "__main__":
    sys.exit(main())
