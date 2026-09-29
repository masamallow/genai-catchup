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

Skipped: YAML front matter, fenced code, tables, lines that are HTML tags or comments.
Usage: uv run scripts/lint_md.py [PATH ...]   (default: content templates)
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ("content", "templates")
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


def display_width(text: str) -> float:
    """Approximate rendered width in em: full-width glyphs are 1, the rest about 0.55."""
    return sum(1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.55 for ch in text)


def item_width_problem(path: Path, lineno: int, item: str) -> list[str]:
    plain = INLINE_CODE_RE.sub(lambda c: c.group(0).strip("`"), LINK_RE.sub(r"\1", item))
    width = display_width(plain)
    if width > MAX_ITEM_WIDTH_EM:
        return [f"{path}:{lineno}: R3 list item is about {width:.0f} em wide (max {MAX_ITEM_WIDTH_EM:.0f})"]
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
    return problems


def main(argv: list[str]) -> int:
    targets = [ROOT / a for a in argv] if argv else [ROOT / t for t in DEFAULT_TARGETS]
    files: list[Path] = []
    for target in targets:
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
