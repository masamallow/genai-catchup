#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Check the Markdown writing rules used in this repository.

R1  Semantic line breaks: one sentence per line.
    A line must not continue after a sentence-ending "。", nor after a "." that ends a
    sentence (a period, optional closing quote or bracket, whitespace, then a capital
    letter, an opening quote or a bracket). Common abbreviations such as "e.g." and
    single-letter initials are ignored, and so are link titles and inline code.
R2  Hard breaks: a prose line directly followed by another prose line at the same
    quote depth must end with two spaces, and no other line may end with two spaces.
R3  Slide density (reports/ directories only): a topic slide column holds at most 8 list
    items, each at most 68 em of display width (full-width characters count 1, others
    0.55), a summary slide holds at most 5 cards, and an Other topics slide holds 2 to 4
    cards with at most 6, 3 or 2 list items each (for 2, 3 or 4 cards) of the same width.
R4  Note density (research/ notes dated 2026-10-17 or later, and work/sections/): a topic
    has at most 7 source sub-headings ("#### [A|B|C] ..."), at most 3 A, 3 B and 2 C, and
    at most 30 bullets under them; the first source (the primary) has at most 10 bullets,
    a later A or B source 4 and a C source 2; a source bullet is never nested and is at
    most 110 em wide (one sentence). Notes dated 2026-10-18 or later and work/sections/
    also name one URL per source, hold at most 10 links on the Also-read lines of a topic,
    and hold nothing but such bullets in a topic's sections, at most 2 in the continuation,
    10 in the notes and 5 in the ideas; the "###" section headings and the Also-read label
    of each edition come from templates/<lang>/research.md. A numbered topic heading of
    such a note is at most 110 em wide, the one sentence that names the topic.
R5  Topic anchors (research/ directories only): every numbered "## N. ..." heading ends
    with <a id="topic-N"></a>, the anchor that slide and continuation links use and that
    GitHub and the site both honour.

Skipped: YAML front matter, fenced code, tables, lines that are HTML tags or comments;
without a PATH, also what git ignores or a nested worktree holds (node_modules/, .claude/worktrees/).
Usage: uv run scripts/lint_md.py [PATH ...]   (default: content, templates and the rule documents)
"""

from __future__ import annotations

import functools
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ("content", "templates", "AGENTS.md", "README.md", "docs", ".claude")  # the rule documents too, never _me/
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
IDEOGRAPHIC_PERIOD_RE = re.compile(r"。(?![\s)）」』]*$)")
SENTENCE_PERIOD_RE = re.compile(r"\.[\"'’”)\]]*\s+(?=[A-Z\"“'(\[])")
WORD_BEFORE_PERIOD_RE = re.compile(r"([A-Za-z][A-Za-z.]*)$")
ABBREVIATIONS = {
    "e.g", "i.e", "etc", "vs", "cf", "ca", "approx", "no", "fig", "vol", "ver",
    "mr", "ms", "mrs", "dr", "prof", "st", "inc", "ltd", "co", "corp", "jr", "sr", "al", "u.s", "u.k",
}
QUOTE_PREFIX_RE = re.compile(r"^((?:>\s?)*)")
# a list marker or a numbered heading ("1. Title") is not a sentence end
LEADING_MARKER_RE = re.compile(r"^\s*(?:>\s?)*(?:#+\s+)?(?:(?:[-*+]|\d+\.)\s+)?(?:\d+\.\s+)?")


def quote_depth(line: str) -> int:
    return QUOTE_PREFIX_RE.match(line).group(1).count(">")


def kind(line: str) -> str:
    body = QUOTE_PREFIX_RE.sub("", line).strip()
    if not body:
        return "blank"
    if body.startswith("#"):
        return "heading"
    if re.match(r"^([-*+]|\d+\.)\s", body) or body in ("-", "*", "+"):
        return "list"
    if body.startswith("|"):
        return "table"
    if body.startswith("<"):
        return "html"
    if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", body):
        return "rule"
    if body.startswith("[!"):
        return "alert"
    if body.startswith("!["):
        return "image"
    return "text"


def continues_after_en_period(plain: str) -> bool:
    """True when a sentence-ending period is followed by more text on the same line."""
    for m in SENTENCE_PERIOD_RE.finditer(plain):
        w = WORD_BEFORE_PERIOD_RE.search(plain[: m.start()])
        token = w.group(1).lower() if w else ""
        if token in ABBREVIATIONS or len(token) == 1:
            continue
        return True
    return False


MAX_ITEM_WIDTH_EM = 68.0  # two lines in a topic-slide column at the theme font size
MAX_ITEMS_PER_COLUMN = 8
MAX_SUMMARY_CARDS = 5
MAX_ITEMS_PER_OTHER_CARD = {2: 6, 3: 3, 4: 2}  # cards on an Other topics slide -> items per card
LIST_ITEM_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+(.*)$")

R4_SINCE = "2026-10-17"  # earlier notes stay as the record (AGENTS.md, "The two documents")
R4_WHOLE_TOPIC_SINCE = "2026-10-18"  # the 2026-10-17 note moved what the source caps cut into its other sections
MAX_SOURCES_PER_TOPIC = 7
MAX_SOURCES_PER_GRADE = {"A": 3, "B": 3, "C": 2}  # the primary counts in its own grade
MAX_BULLETS_PRIMARY = 10  # the first source of a topic
MAX_BULLETS_PER_SOURCE = {"A": 4, "B": 4, "C": 2}  # every later source
MAX_BULLETS_PER_TOPIC = 30
MAX_TOPIC_BULLET_WIDTH_EM = 110.0  # one sentence: about 200 Latin or 110 Japanese characters
MAX_TOPIC_HEADING_WIDTH_EM = 110.0  # the one-sentence description of a topic, as wide as a bullet
MAX_ALSO_READ_LINKS = 10
TOPIC_SECTION_ROLES = ("continued", "collected", "notes", "ideas")  # the "###" headings of a topic template, in order
MAX_SECTION_BULLETS = {"continued": 2, "notes": 10, "ideas": 5}
ALSO_READ_LINE_RE = re.compile(r"^([^\s\[<#>|*+-][^:]*:)\s*\[[^\]]*\]\(")  # "Also read: [Title](URL)" in a template
AUTOLINK_RE = re.compile(r"<https?://[^>\s]+>")
SOURCE_HEADING_RE = re.compile(r"^#### \[([ABC])\]")
HEADING_RE = re.compile(r"^#{1,6} ")
NUMBERED_H2_RE = re.compile(r"^## (\d+)\. ")
TOPIC_ANCHOR_RE = re.compile(r'<a id="topic-(\d+)"></a>\s*$')


def display_width(text: str) -> float:
    """Approximate rendered width in em: full-width glyphs are 1, the rest about 0.55."""
    return sum(1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.55 for ch in text)


def item_width_problem(
    path: Path, lineno: int, item: str, limit: float = MAX_ITEM_WIDTH_EM, rule: str = "R3", what: str = "list item"
) -> list[str]:
    plain = INLINE_CODE_RE.sub(lambda c: c.group(0).strip("`"), LINK_RE.sub(r"\1", item))
    width = display_width(plain)
    if width > limit:
        return [f"{path}:{lineno}: {rule} {what} is about {width:.0f} em wide (max {limit:.0f})"]
    return []


def lint_topic_slide(path: Path, offset: int, slide: list[str]) -> list[str]:
    problems: list[str] = []
    column_items = 0
    for j, line in enumerate(slide):
        if line.strip() == "<div>":
            column_items = 0
        elif line.strip() == "</div>" and column_items > MAX_ITEMS_PER_COLUMN:
            problems.append(f"{path}:{offset + j + 1}: R3 column has {column_items} list items (max {MAX_ITEMS_PER_COLUMN})")
        m = LIST_ITEM_RE.match(line)
        if m:
            column_items += 1
            problems += item_width_problem(path, offset + j + 1, m.group(2))
    return problems


def lint_others_slide(path: Path, offset: int, slide: list[str]) -> list[str]:
    cards = sum(line.lstrip().startswith("<article") for line in slide)
    if cards not in MAX_ITEMS_PER_OTHER_CARD:
        return [f"{path}:{offset + 1}: R3 Other topics slide has {cards} cards (2 to 4)"]
    limit = MAX_ITEMS_PER_OTHER_CARD[cards]
    problems: list[str] = []
    card_items = 0
    for j, line in enumerate(slide):
        if line.lstrip().startswith("<article"):
            card_items = 0
        elif line.strip() == "</article>" and card_items > limit:
            problems.append(f"{path}:{offset + j + 1}: R3 card has {card_items} list items (max {limit} with {cards} cards)")
        m = LIST_ITEM_RE.match(line)
        if m:
            card_items += 1
            problems += item_width_problem(path, offset + j + 1, m.group(2))
    return problems


def lint_density(path: Path, lines: list[str], start: int) -> list[str]:
    """R3: keep summary, topic and Other topics slides inside the 1280x720 frame (reports/ only)."""
    problems: list[str] = []
    slide_start = start
    slides: list[tuple[int, list[str]]] = []
    for i in range(start, len(lines) + 1):
        if i == len(lines) or lines[i].strip() == "---":
            slides.append((slide_start, lines[slide_start:i]))
            slide_start = i + 1
    for offset, slide in slides:
        text = "\n".join(slide)
        if "_class: summary" in text:
            cards = text.count("<article")
            if cards > MAX_SUMMARY_CARDS:
                problems.append(f"{path}:{offset + 1}: R3 summary slide has {cards} cards (max {MAX_SUMMARY_CARDS})")
        elif "_class: topic" in text:
            problems += lint_topic_slide(path, offset, slide)
        elif "_class: others" in text:
            problems += lint_others_slide(path, offset, slide)
    return problems


def r4_applies(path: Path) -> bool:
    """R4 covers the researchers' section files and the notes written since the rule exists."""
    if path.parent.name == "sections":
        return True
    return path.parent.name == "research" and path.stem[:10] >= R4_SINCE


def r4_covers_whole_topic(path: Path) -> bool:
    """Beyond the sources, R4 checks the rest of a topic in section files and in notes since R4_WHOLE_TOPIC_SINCE."""
    return path.parent.name == "sections" or path.stem[:10] >= R4_WHOLE_TOPIC_SINCE


@functools.cache
def topic_template() -> tuple[dict[str, str], tuple[str, ...]]:
    """Each edition's "###" headings of a topic mapped to their roles, and its Also-read labels, from templates/<lang>/research.md."""
    roles: dict[str, str] = {}
    labels: list[str] = []
    for template in sorted((ROOT / "templates").glob("*/research.md")):
        lines = template.read_text(encoding="utf-8").split("\n")
        headings = [line[4:].strip() for line in lines if line.startswith("### ")]
        if len(headings) != len(TOPIC_SECTION_ROLES):
            sys.exit(f"{template}: R4 needs the '###' headings of a topic in this order: {', '.join(TOPIC_SECTION_ROLES)}")
        roles.update(zip(headings, TOPIC_SECTION_ROLES))
        labels += [m.group(1) for m in map(ALSO_READ_LINE_RE.match, lines) if m]
    return roles, tuple(labels)


def lint_note_density(path: Path, lines: list[str], start: int, kinds: list[str | None], whole_topic: bool) -> list[str]:
    """R4: cap the sources of a topic and their bullets, and with whole_topic the rest of the topic's sections."""
    problems: list[str] = []
    roles, also_read_labels = topic_template()
    topic_at = 0  # line of the current "## " heading; a section file has none and is one topic
    role: str | None = None  # role of the current "###" section of the topic
    topic_sources = topic_bullets = also_read_links = 0
    grades: dict[str, int] = {}
    source: list | None = None  # [grade, line, bullets, cap] of the current "#### [A|B|C]" block
    section: list | None = None  # [role, line, bullets] of the current continuation, notes or ideas section

    def close_source() -> None:
        nonlocal source
        if source:
            grade, at, n, cap = source
            if n > cap:
                problems.append(f"{path}:{at + 1}: R4 [{grade}] source has {n} bullets (max {cap})")
        source = None

    def close_section() -> None:
        nonlocal section
        close_source()
        if section:
            name, at, n = section
            if n > MAX_SECTION_BULLETS[name]:
                problems.append(f"{path}:{at + 1}: R4 {name} section has {n} bullets (max {MAX_SECTION_BULLETS[name]})")
        section = None

    def close_topic() -> None:
        nonlocal topic_sources, topic_bullets, also_read_links
        close_section()
        if topic_sources > MAX_SOURCES_PER_TOPIC:
            problems.append(f"{path}:{topic_at + 1}: R4 topic has {topic_sources} sources (max {MAX_SOURCES_PER_TOPIC})")
        for grade, n in sorted(grades.items()):
            if n > MAX_SOURCES_PER_GRADE[grade]:
                problems.append(f"{path}:{topic_at + 1}: R4 topic has {n} [{grade}] sources (max {MAX_SOURCES_PER_GRADE[grade]})")
        if topic_bullets > MAX_BULLETS_PER_TOPIC:
            problems.append(f"{path}:{topic_at + 1}: R4 topic has {topic_bullets} source bullets (max {MAX_BULLETS_PER_TOPIC})")
        if also_read_links > MAX_ALSO_READ_LINKS:
            problems.append(f"{path}:{topic_at + 1}: R4 topic has {also_read_links} Also-read links (max {MAX_ALSO_READ_LINKS})")
        topic_sources = topic_bullets = also_read_links = 0
        grades.clear()

    for i in range(start, len(lines)):
        line = lines[i]
        if kinds[i] == "fence":
            if whole_topic and role and (i == start or kinds[i - 1] != "fence"):
                problems.append(f"{path}:{i + 1}: R4 code block in a topic -> a topic's sections hold bullets only")
            continue
        if line.startswith("## "):
            close_topic()
            topic_at, role = i, None
            if whole_topic and NUMBERED_H2_RE.match(line):
                title = NUMBERED_H2_RE.sub("", TOPIC_ANCHOR_RE.sub("", line)).strip()
                problems += item_width_problem(path, i + 1, title, MAX_TOPIC_HEADING_WIDTH_EM, "R4", "topic heading")
            continue
        if line.startswith("### "):
            close_section()
            role = roles.get(line[4:].strip())
            if whole_topic and role is None:
                problems.append(f"{path}:{i + 1}: R4 unknown section -> use the '###' headings of templates/<lang>/research.md")
            elif whole_topic and role in MAX_SECTION_BULLETS:
                section = [role, i, 0]
            continue
        m = SOURCE_HEADING_RE.match(line)
        if m:
            close_source()
            grade = m.group(1)
            source = [grade, i, 0, MAX_BULLETS_PER_SOURCE[grade] if topic_sources else MAX_BULLETS_PRIMARY]
            topic_sources += 1
            grades[grade] = grades.get(grade, 0) + 1
            continue
        if HEADING_RE.match(line):
            if whole_topic and role:  # report it, but keep counting the section it sits in
                problems.append(f"{path}:{i + 1}: R4 sub-heading that is not a source -> a topic's sections hold bullets only")
            else:
                close_section()
            continue
        if not whole_topic and source is None:
            continue
        item = LIST_ITEM_RE.match(line)
        if item and (source or section):
            where = "under a source" if source else f"in the {section[0]} section"
            if line[0] in " \t":
                problems.append(f"{path}:{i + 1}: R4 nested bullet {where} -> one sentence per bullet, no nesting")
            problems += item_width_problem(path, i + 1, item.group(2), MAX_TOPIC_BULLET_WIDTH_EM, "R4")
            if source:
                source[2] += 1
                topic_bullets += 1
            else:
                section[2] += 1
        elif not whole_topic or not role or kinds[i] == "blank":
            continue
        elif role == "collected" and line.startswith(also_read_labels):
            also_read_links += len(LINK_RE.findall(line))
        elif source and AUTOLINK_RE.search(line):
            urls = len(AUTOLINK_RE.findall(line)) + len(LINK_RE.findall(line))
            if urls > 1:
                problems.append(f"{path}:{i + 1}: R4 source names {urls} URLs -> one page per sub-heading")
        else:
            problems.append(f"{path}:{i + 1}: R4 stray line in a topic -> its sections hold only bullets, each source's URL and the Also-read line")
    close_topic()
    return problems


def lint_topic_anchors(path: Path, lines: list[str], start: int, kinds: list[str | None]) -> list[str]:
    """R5: every numbered topic heading of a research note ends with its anchor <a id="topic-N"></a>."""
    problems: list[str] = []
    for i in range(start, len(lines)):
        if kinds[i] == "fence":
            continue
        m = NUMBERED_H2_RE.match(lines[i])
        if not m:
            continue
        anchor = TOPIC_ANCHOR_RE.search(lines[i])
        if not anchor or anchor.group(1) != m.group(1):
            problems.append(f'{path}:{i + 1}: R5 topic heading must end with <a id="topic-{m.group(1)}"></a>')
    return problems


def lint_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").split("\n")
    problems: list[str] = []
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break

    in_fence = False
    kinds: list[str | None] = [None] * len(lines)
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            kinds[i] = "fence"
            continue
        if in_fence:
            kinds[i] = "fence"
            continue
        kinds[i] = kind(lines[i])
        if kinds[i] in ("table", "html"):
            continue
        plain = INLINE_CODE_RE.sub("", LINK_RE.sub("LINK", LEADING_MARKER_RE.sub("", lines[i])))  # link titles are verbatim
        if IDEOGRAPHIC_PERIOD_RE.search(plain):
            problems.append(f"{path}:{i + 1}: R1 sentence continues after '。' -> break the line")
        elif continues_after_en_period(plain):
            problems.append(f"{path}:{i + 1}: R1 sentence continues after \".\" -> break the line")

    for i in range(start, len(lines) - 1):
        cur, nxt = lines[i], lines[i + 1]
        if kinds[i] in (None, "fence"):
            continue
        wants_break = kinds[i] == "text" and kinds[i + 1] == "text" and quote_depth(cur) == quote_depth(nxt)
        has_break = cur.endswith("  ")
        if wants_break and not has_break:
            problems.append(f"{path}:{i + 1}: R2 prose continues on the next line -> end this line with two spaces")
        elif has_break and not wants_break:
            problems.append(f"{path}:{i + 1}: R2 trailing two spaces are not needed here")
    if path.parent.name == "reports":
        problems += lint_density(path, lines, start)
    if r4_applies(path):
        problems += lint_note_density(path, lines, start, kinds, r4_covers_whole_topic(path))
    if path.parent.name == "research":
        problems += lint_topic_anchors(path, lines, start, kinds)
    return problems


def default_files() -> list[Path]:
    """The Markdown files of DEFAULT_TARGETS that git tracks or would add, so none that it ignores and none of a nested worktree."""
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *DEFAULT_TARGETS],
        cwd=ROOT, stdout=subprocess.PIPE, encoding="utf-8", check=True,
    ).stdout
    paths = {ROOT / name for name in listing.split("\0") if name.endswith(".md")}
    return sorted(path for path in paths if path.is_file())  # the index keeps a deleted file until the deletion is staged


def main(argv: list[str]) -> int:
    files = [] if argv else default_files()
    for target in (ROOT / a for a in argv):
        if target.is_dir():
            files += sorted(target.rglob("*.md"))
        elif target.suffix == ".md":
            files.append(target)
    problems: list[str] = []
    for path in files:
        problems += lint_file(path)
    for p in problems:
        print(p)
    print(f"{len(files)} file(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
