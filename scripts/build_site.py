#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "markdown>=3.7",
#   "pyyaml>=6",
# ]
# ///
"""Build the static site into dist/, one tree per language.

For every language directory content/<lang>/:
1. content/<lang>/reports/*.md  -> dist/<lang>/reports/*.html   (Marp CLI; options come from marp.config.mjs)
2. content/<lang>/research/*.md -> dist/<lang>/research/*.html  (python-markdown with a small stylesheet)
3. dist/<lang>/index.html                                        (newest first, from research front matter)

The strings of the site chrome (language name, link labels, tagline) come from
templates/<lang>/site.yaml.

dist/index.html is the index of the default language (en when present) pointing into
its tree, and every index and research page links to the other languages.
Links to sibling Markdown files such as `./2026-09-22.md#3`, `../research/x.md` or
`../../ja/research/x.md` are rewritten to `.html`, so the same links work on GitHub
and on the site.
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
DEFAULT_LANG = "en"
SITE_TITLE = "GenAI Catch-up Reports"
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
MD_LINK_RE = re.compile(r'(href=")(\.\.?/[^"#?]*?)\.md(#[^"]*)?(")')
ALERT_RE = re.compile(r"^(>\s*)\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", re.M)

TEMPLATES = ROOT / "templates"
# Strings of the site chrome come from templates/<lang>/site.yaml; these are the fallbacks.
DEFAULT_UI = {
    "name": "",
    "tagline": "A regular watch on generative AI engineering and AI coding tools. Newest first.",
    "note": "📝 Research note",
    "slides": "🖥️ Slides",
    "index": "← Index",
    "empty": "No reports yet.",
}
_UI_CACHE: dict[str, dict[str, str]] = {}

FONT_STACK = '"Inter", system-ui, -apple-system, "Segoe UI", sans-serif'  # every page carries its lang attribute, so browsers pick the script fallback
PAGE_CSS = f"""
:root {{ --ink: #1f2933; --muted: #5f6b7a; --line: #e5e9ef; --accent: #2f6fed; --accent-soft: #eaf1ff; --card: #f7f9fc; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #fff; color: var(--ink); font-family: {FONT_STACK}; line-height: 1.7; font-size: 16px; }}
main {{ max-width: 860px; margin: 0 auto; padding: 32px 20px 80px; }}
nav.top {{ display: flex; flex-wrap: wrap; gap: 16px; font-size: 14px; color: var(--muted); margin-bottom: 24px; }}
nav.top .langs {{ margin-left: auto; display: flex; gap: 12px; }}
nav.top a, article a {{ color: var(--accent); text-decoration: none; }}
nav.top a:hover, article a:hover {{ text-decoration: underline; }}
h1 {{ font-size: 28px; line-height: 1.3; margin: 0 0 8px; letter-spacing: -0.01em; }}
h2 {{ font-size: 21px; margin: 40px 0 8px; padding-bottom: 6px; border-bottom: 1px solid var(--line); }}
h3 {{ font-size: 17px; margin: 24px 0 6px; color: var(--accent); }}
p, ul, ol {{ margin: 0 0 12px; }}
li {{ margin: 2px 0; }}
code {{ background: var(--card); padding: 1px 6px; border-radius: 4px; font-size: 0.92em; }}
pre {{ background: var(--card); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
table {{ border-collapse: collapse; font-size: 14px; margin: 0 0 16px; }}
th, td {{ border: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }}
th {{ background: var(--card); }}
blockquote {{ margin: 0 0 12px; padding: 8px 14px; border-left: 4px solid var(--accent-soft); color: var(--muted); }}
.meta {{ color: var(--muted); font-size: 14px; margin-bottom: 28px; }}
.cards {{ display: grid; gap: 14px; }}
.card {{ border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; background: #fff; }}
.card h2 {{ margin: 0 0 6px; border: 0; padding: 0; font-size: 19px; }}
.card .themes {{ margin: 6px 0 10px; padding-left: 1.2em; color: var(--ink); }}
.card .links {{ font-size: 14px; }}
.card .links a + a {{ margin-left: 14px; }}
.tag {{ display: inline-block; background: var(--accent-soft); color: var(--accent); border-radius: 999px; padding: 0 10px; font-size: 12px; font-weight: 600; margin-right: 6px; }}
"""


def ui(lang: str) -> dict[str, str]:
    """Site strings of a language: templates/<lang>/site.yaml over the defaults."""
    if lang not in _UI_CACHE:
        path = TEMPLATES / lang / "site.yaml"
        custom = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}
        strings = {**DEFAULT_UI, **{k: str(v) for k, v in custom.items()}}
        strings["name"] = strings["name"] or lang
        _UI_CACHE[lang] = strings
    return _UI_CACHE[lang]


def languages() -> list[str]:
    """Language directories under content/, default language first."""
    if not CONTENT.exists():
        return []
    langs = sorted(d.name for d in CONTENT.iterdir() if d.is_dir() and not d.name.startswith("."))
    return sorted(langs, key=lambda code: (code != DEFAULT_LANG, code))


def split_front_matter(text: str) -> tuple[dict, str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def rewrite_links(page_html: str) -> str:
    return MD_LINK_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}.html{m.group(3) or ''}{m.group(4)}", page_html)


def language_switch(lang: str, others: list[str], href_for: Callable[[str], str]) -> str:
    if not others:
        return ""
    items = [f'<span lang="{lang}">{html.escape(ui(lang)["name"])}</span>']
    items += [f'<a href="{href_for(o)}" lang="{o}" hreflang="{o}">{html.escape(ui(o)["name"])}</a>' for o in others]
    return '<span class="langs">' + "".join(items) + "</span>"


def page(title: str, body: str, nav: str, lang: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<main>
<nav class="top">{nav}</nav>
{body}
</main>
</body>
</html>
"""


def build_reports(lang: str) -> set[str]:
    src_dir = CONTENT / lang / "reports"
    if not any(src_dir.glob("*.md")):
        return set()
    out_dir = DIST / lang / "reports"
    subprocess.run(
        ["pnpm", "exec", "marp", "--no-stdin", "--input-dir", str(src_dir.relative_to(ROOT)), "-o", str(out_dir.relative_to(ROOT))],
        cwd=ROOT, check=True,
    )
    built: set[str] = set()
    for out in out_dir.glob("*.html"):
        out.write_text(rewrite_links(out.read_text(encoding="utf-8")), encoding="utf-8")
        built.add(out.stem)
    return built


def build_research(lang: str, report_stems: set[str], langs: list[str]) -> list[dict]:
    entries = []
    src_dir = CONTENT / lang / "research"
    out_dir = DIST / lang / "research"
    out_dir.mkdir(parents=True, exist_ok=True)
    strings = ui(lang)
    for src in sorted(src_dir.glob("*.md")):
        front, body = split_front_matter(src.read_text(encoding="utf-8"))
        body = ALERT_RE.sub(lambda m: f"{m.group(1)}**{m.group(2)}**", body)
        rendered = markdown.markdown(body, extensions=["extra", "toc", "sane_lists"])
        nav = f'<a href="../index.html">{strings["index"]}</a>'
        if src.stem in report_stems:
            nav += f'<a href="../reports/{src.stem}.html">{strings["slides"]} →</a>'
        others = [o for o in langs if o != lang and (CONTENT / o / "research" / src.name).exists()]
        nav += language_switch(lang, others, lambda o: f"../../{o}/research/{src.stem}.html")
        title = str(front.get("title") or src.stem)
        (out_dir / f"{src.stem}.html").write_text(rewrite_links(page(title, rendered, nav, lang)), encoding="utf-8")
        entries.append({"stem": src.stem, "front": front, "has_report": src.stem in report_stems})
    return entries


def render_index(lang: str, entries: list[dict], langs: list[str], tree: str, index_for: Callable[[str], str]) -> str:
    """Index of one language. `tree` is the path prefix to that language's tree, `index_for` the link to another language's index."""
    strings = ui(lang)
    cards = []
    for e in sorted(entries, key=lambda x: str(x["front"].get("date") or x["stem"]), reverse=True):
        front = e["front"]
        themes = "".join(
            f"<li>{html.escape(str(t.get('emoji', '')))} {html.escape(str(t.get('title', '')))}</li>"
            for t in (front.get("themes") or [])
        )
        links = f'<a href="{tree}research/{e["stem"]}.html">{strings["note"]}</a>'
        if e["has_report"]:
            links = f'<a href="{tree}reports/{e["stem"]}.html">{strings["slides"]}</a>' + links
        cards.append(
            f'<article class="card"><h2>{html.escape(str(front.get("date") or e["stem"]))}</h2>'
            f'<ul class="themes">{themes}</ul><p class="links">{links}</p></article>'
        )
    body = f'<h1>{SITE_TITLE}</h1><p class="meta">{html.escape(strings["tagline"])}</p>'
    body += ('<div class="cards">' + "".join(cards) + "</div>") if cards else f'<p>{html.escape(strings["empty"])}</p>'
    nav = language_switch(lang, [o for o in langs if o != lang], index_for)
    return page(SITE_TITLE, body, nav, lang)


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    langs = languages()
    entries_by_lang: dict[str, list[dict]] = {}
    for lang in langs:
        stems = build_reports(lang)
        entries = build_research(lang, stems, langs)
        entries_by_lang[lang] = entries
        (DIST / lang / "index.html").write_text(
            render_index(lang, entries, langs, tree="", index_for=lambda o: f"../{o}/index.html"), encoding="utf-8"
        )
        print(f"{lang}: {len(stems)} slide deck(s), {len(entries)} research note(s)")
    if langs:
        root = langs[0]  # default language when present, otherwise the first one
        (DIST / "index.html").write_text(
            render_index(root, entries_by_lang[root], langs, tree=f"{root}/", index_for=lambda o: f"{o}/index.html"), encoding="utf-8"
        )
        print(f"index.html: {root}")
    else:
        (DIST / "index.html").write_text(page(SITE_TITLE, f"<h1>{SITE_TITLE}</h1><p>{DEFAULT_UI['empty']}</p>", "", "en"), encoding="utf-8")
        print("content/: nothing to build")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
