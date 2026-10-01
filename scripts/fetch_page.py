#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27",
#   "pypdf>=5",
# ]
# ///
"""Save web pages as readable text in work/pages/, the page cache of one catch-up run.

Usage:
    uv run scripts/fetch_page.py URL [URL ...]
    uv run scripts/fetch_page.py --list

The agents of a run read pages through this cache: a page is downloaded once, every
researcher and edition writer reads the same text, and quotes keep the page's exact
wording (WebFetch answers through a small model, so its output is not the page).
`mise run fetch` empties work/pages/ when a run starts, so every cached page was
fetched in this run.

Each file starts with a header between `---` lines (url, final_url, title, fetched,
method, status, content_type, chars, state), followed by the text: headings as `#`
lines, list items as `-` lines, links as [text](url) and code fenced. An HTML page
keeps the content of its <main> or <article> when it has one, and a PDF keeps its text
page by page. A page read by other means, such as the browser, joins the cache when
its file starts with the same header, with `method: browser`; a lookup prefers it to a
thin copy of the same URL.

One line is printed per URL:
    saved   work/pages/<file>.md     12,345 chars  Title
    cached  work/pages/<file>.md     12,345 chars  Title
    thin    work/pages/<file>.md        312 chars  Title  (try WebFetch or the browser)
    failed  403    URL  (try WebFetch or the browser)
A page is thin when it has little text, or when it is short and most of its headings
have no text under them: it probably renders its content with JavaScript. Rate limits and gateway errors are
retried twice. The exit status is 1 when a URL failed or came back thin.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "work" / "pages"
USER_AGENT = "genai-catchup/1.0 (personal feed reader)"
ACCEPT = "text/html,application/xhtml+xml,application/pdf;q=0.9,text/plain;q=0.8,*/*;q=0.5"
MAX_BYTES = 30_000_000
THIN_CHARS = 500
SHORT_CHARS = 5_000
EMPTY_SECTIONS = 3
RETRY_STATUS = {"429", "502", "503"}
RETRY_DELAYS = (2.0, 6.0)
HINT = "(try WebFetch or the browser)"

SKIP_TAGS = {
    "script", "style", "noscript", "svg", "template", "iframe", "canvas", "nav", "footer",
    "aside", "button", "select", "textarea", "dialog", "object",
}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
    "source", "track", "wbr",
}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
PARAGRAPH_TAGS = {"p", "blockquote", "figure", "table", "dl"}
BLOCK_TAGS = {
    "address", "article", "caption", "details", "div", "dd", "dt", "fieldset", "figcaption",
    "header", "main", "section", "summary", "tbody", "tfoot", "thead",
}
ROOT_RE = re.compile(r"<(?:main|article)\b|role=[\"']main[\"']", re.I)
HEADING_RE = re.compile(r"^(#{1,6}) ")
INDENT = "\x00"  # list indentation marker that survives whitespace collapsing


class TextExtractor(HTMLParser):
    """Turn HTML into Markdown-like text.

    With `roots`, text is kept only inside those elements or an element with role="main";
    without, the whole document is kept. Navigation, scripts, forms and similar chrome are
    dropped everywhere, and so is a <header> outside the kept roots.
    """

    def __init__(self, base_url: str, roots: set[str] | None):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.roots = roots
        self.stack: list[tuple[str, bool, bool, bool]] = []  # tag, is_root, is_skip, opened
        self.root_depth = 0
        self.skip_depth = 0
        self.list_depth = 0
        self.pre_depth = 0
        self.row_cells = 0
        self.buffers: list[list[str]] = [[]]
        self.links: list[str | None] = []
        self.title_parts: list[str] = []
        self.in_title = False
        self.title_done = False

    @property
    def keeping(self) -> bool:
        if self.skip_depth:
            return False
        return self.roots is None or self.root_depth > 0

    @property
    def text(self) -> str:
        return tidy("".join(self.buffers[0]))

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.title_parts)).strip()

    def write(self, text: str) -> None:
        if self.keeping:
            self.buffers[-1].append(text)

    def newline(self, count: int = 1) -> None:
        if not self.keeping:
            return
        buf = self.buffers[-1]
        tail = "".join(buf[-4:])
        if tail.endswith(("- ", "# ")):
            return  # keep the text on its bullet or heading line
        have = len(tail) - len(tail.rstrip("\n"))
        if have < count:
            buf.append("\n" * (count - have))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "title":
            self.in_title = not self.title_done and not self.skip_depth
            return
        if tag in VOID_TAGS:
            if tag == "br":
                self.write("\n")
            elif tag == "hr":
                self.newline(2)
            return
        is_root = self.roots is not None and (tag in self.roots or attributes.get("role") == "main")
        is_skip = (
            tag in SKIP_TAGS
            or attributes.get("aria-hidden") == "true"
            or (tag == "header" and self.root_depth == 0 and not is_root)
        )
        opened = not is_skip and not self.skip_depth
        self.stack.append((tag, is_root, is_skip, opened))
        if is_root:
            self.root_depth += 1
        if is_skip:
            self.skip_depth += 1
        if opened:
            self.open_tag(tag, attributes)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            if self.in_title:
                self.title_done = True
            self.in_title = False
            return
        if tag in VOID_TAGS or all(entry[0] != tag for entry in self.stack):
            return
        while self.stack:
            name, is_root, is_skip, opened = self.stack.pop()
            if opened:
                self.close_tag(name)
            if is_skip:
                self.skip_depth -= 1
            if is_root:
                self.root_depth -= 1
            if name == tag:
                break

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        elif self.pre_depth:
            self.write(data)
        else:
            self.write(re.sub(r"\s+", " ", data))

    def open_tag(self, tag: str, attributes: dict[str, str | None]) -> None:
        if tag in HEADING_TAGS:
            self.newline(2)
            self.write("#" * int(tag[1]) + " ")
        elif tag in {"ul", "ol"}:
            self.list_depth += 1
            self.newline(1)
        elif tag == "li":
            self.newline(1)
            self.write(INDENT * max(0, self.list_depth - 1) + "- ")
        elif tag == "pre":
            self.newline(2)
            self.write("```\n")
            self.pre_depth += 1
        elif tag == "code" and not self.pre_depth:
            self.write("`")
        elif tag == "a":
            self.links.append(attributes.get("href"))
            self.buffers.append([])
        elif tag == "tr":
            self.newline(1)
            self.row_cells = 0
        elif tag in {"td", "th"}:
            if self.row_cells:
                self.write(" | ")
            self.row_cells += 1
        elif tag in PARAGRAPH_TAGS:
            self.newline(2)
        elif tag in BLOCK_TAGS:
            self.newline(1)

    def close_tag(self, tag: str) -> None:
        if tag in HEADING_TAGS or tag in PARAGRAPH_TAGS:
            self.newline(2)
        elif tag in {"ul", "ol"}:
            self.list_depth = max(0, self.list_depth - 1)
            self.newline(1)
        elif tag == "li":
            self.newline(1)
        elif tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)
            self.newline(1)
            self.write("```")
            self.newline(2)
        elif tag == "code" and not self.pre_depth:
            self.write("`")
        elif tag == "a":
            self.write(self.link("".join(self.buffers.pop()), self.links.pop()))
        elif tag in BLOCK_TAGS:
            self.newline(1)

    def link(self, text: str, href: str | None) -> str:
        if "\n" in text.strip():
            return text  # a link around blocks, such as a card: keep the blocks
        label = re.sub(r"\s+", " ", text).strip()
        if not label or not href or href.startswith(("#", "javascript:", "mailto:")):
            return text
        url = urljoin(self.base_url, href)
        if not url.startswith(("http://", "https://")) or url == label:
            return text
        before = " " if text[:1].isspace() else ""
        after = " " if text[-1:].isspace() else ""
        return f"{before}[{label}]({url}){after}"


def tidy(text: str) -> str:
    """Normalise whitespace outside code fences and keep at most one blank line."""
    lines: list[str] = []
    fence = False
    for line in text.split("\n"):
        if line.strip() == "```":
            fence = not fence
            lines.append("```")
        elif fence:
            lines.append(line.rstrip())
        else:
            line = re.sub(r"[ \t\u00a0]+", " ", line).strip().replace(INDENT, "  ")
            if line not in {"-", "|", "#", "##", "###", "####", "#####", "######"}:
                lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def section_counts(text: str) -> tuple[int, int]:
    """Count the headings, and the empty ones: followed by a heading of the same or a higher level, or by the end."""
    headings = empty = 0
    fence, open_level = False, None
    for line in text.split("\n"):
        if line.startswith("```"):
            fence, open_level = not fence, None
            continue
        if fence or not line.strip():
            continue
        match = HEADING_RE.match(line)
        if not match:
            open_level = None
            continue
        level = len(match.group(1))
        headings += 1
        if open_level is not None and level <= open_level:
            empty += 1
        open_level = level
    return headings, empty + (open_level is not None)


def is_thin(text: str) -> bool:
    """Little text, or a short page whose headings are mostly empty: it renders its content with JavaScript."""
    if len(text) < THIN_CHARS:
        return True
    headings, empty = section_counts(text)
    return len(text) < SHORT_CHARS and empty >= EMPTY_SECTIONS and 2 * empty >= headings


def html_to_text(html: str, base_url: str) -> tuple[str, str]:
    """Return the title and the text of an HTML page, preferring <main> or <article>."""
    whole = TextExtractor(base_url, None)
    whole.feed(html)
    whole.close()
    if ROOT_RE.search(html):
        main = TextExtractor(base_url, {"main", "article"})
        main.feed(html)
        main.close()
        if len(main.text) >= THIN_CHARS or 3 * len(main.text) >= len(whole.text):
            return main.title or whole.title, main.text
    return whole.title, whole.text


def pdf_to_text(data: bytes) -> tuple[str, str]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [f"[page {n}]\n\n{(page.extract_text() or '').strip()}" for n, page in enumerate(reader.pages, 1)]
    title = (reader.metadata.title if reader.metadata else None) or ""
    text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(pages)).strip() + "\n"
    return str(title).strip(), text


def cache_key(url: str) -> str:
    """The URL without its fragment and trailing slash, with https for http."""
    parts = urlsplit(url.strip())
    scheme = "https" if parts.scheme.lower() in {"http", "https"} else parts.scheme.lower()
    return urlunsplit((scheme, parts.netloc.lower(), parts.path.rstrip("/") or "/", parts.query, ""))


def page_path(url: str) -> Path:
    key = cache_key(url)
    parts = urlsplit(key)
    slug = re.sub(r"[^a-z0-9]+", "-", f"{parts.netloc}{parts.path}".lower()).strip("-")[:72].rstrip("-")
    return PAGES_DIR / f"{slug}-{hashlib.sha1(key.encode()).hexdigest()[:8]}.md"


def read_header(path: Path) -> dict[str, str]:
    header: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        if fh.readline().strip() != "---":
            return header
        for line in fh:
            if line.strip() == "---":
                break
            key, sep, value = line.partition(":")
            if sep:
                header[key.strip()] = value.strip()
    return header


def header_chars(path: Path, header: dict[str, str]) -> int:
    try:
        return int(header.get("chars", "").replace(",", ""))
    except ValueError:
        return len(path.read_text(encoding="utf-8", errors="replace"))


@dataclass
class Result:
    url: str
    state: str  # saved | cached | thin | failed
    path: Path | None = None
    chars: int = 0
    title: str = ""
    detail: str = ""

    def line(self) -> str:
        if self.state == "failed":
            return f"failed  {self.detail:<6} {self.url}  {HINT}"
        rel = self.path.relative_to(ROOT) if self.path else "?"
        text = f"{self.state:<7} {rel}  {self.chars:>9,} chars  {self.title[:80]}"
        return f"{text}  {HINT}" if self.state == "thin" else text


def load_index() -> dict[str, Result]:
    """Map the cache key of every cached url and final_url to its fullest page."""
    index: dict[str, Result] = {}
    for path in sorted(PAGES_DIR.glob("*.md")) if PAGES_DIR.is_dir() else []:
        header = read_header(path)
        chars = header_chars(path, header)
        thin = header.get("state") == "thin" or chars < THIN_CHARS
        page = Result(header.get("url", ""), "thin" if thin else "cached", path, chars, header.get("title", ""))
        for field in ("url", "final_url"):
            if header.get(field):
                key = cache_key(header[field])
                best = index.get(key)
                if best is None or (page.state != "thin", page.chars) > (best.state != "thin", best.chars):
                    index[key] = page
    return index


def save(url: str, final_url: str, title: str, content_type: str, status: int, text: str) -> Path:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    header = {
        "url": url,
        "final_url": final_url,
        "title": re.sub(r"\s+", " ", title).strip(),
        "fetched": datetime.now().astimezone().isoformat(timespec="seconds"),
        "method": "http",
        "status": status,
        "content_type": content_type,
        "chars": len(text),
        "state": "thin" if is_thin(text) else "ok",
    }
    body = "\n".join(["---", *(f"{k}: {v}" for k, v in header.items()), "---", "", text])
    path = page_path(url)
    fd, tmp = tempfile.mkstemp(dir=PAGES_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(body)
    os.replace(tmp, path)
    return path


def fetch(url: str, client: httpx.Client) -> Result:
    for delay in (*RETRY_DELAYS, None):
        result = fetch_once(url, client)
        if delay is None or result.state != "failed" or result.detail not in RETRY_STATUS:
            return result
        time.sleep(delay)
    return result


def fetch_once(url: str, client: httpx.Client) -> Result:
    try:
        with client.stream("GET", url) as response:
            if response.status_code >= 400:
                return Result(url, "failed", detail=str(response.status_code))
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > MAX_BYTES:
                    return Result(url, "failed", detail="size")
            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
            encoding = response.encoding or "utf-8"
            final_url, status = str(response.url), response.status_code
    except httpx.HTTPError as exc:
        return Result(url, "failed", detail=type(exc).__name__)

    raw = bytes(data)
    try:
        if "pdf" in content_type or raw.startswith(b"%PDF"):
            title, text = pdf_to_text(raw)
        elif "html" in content_type or "xml" in content_type:
            title, text = html_to_text(raw.decode(encoding, errors="replace"), final_url)
        elif content_type.startswith("text/") or "json" in content_type:
            title, text = "", raw.decode(encoding, errors="replace").strip() + "\n"
        else:
            return Result(url, "failed", detail=content_type or "type")
    except Exception as exc:  # a broken page must not stop the other URLs
        return Result(url, "failed", detail=type(exc).__name__)
    path = save(url, final_url, title, content_type, status, text)
    return Result(url, "thin" if is_thin(text) else "saved", path, len(text), title)


def list_pages() -> int:
    paths = sorted(PAGES_DIR.glob("*.md")) if PAGES_DIR.is_dir() else []
    for path in paths:
        header = read_header(path)
        chars = header_chars(path, header)
        print(f"{path.relative_to(ROOT)}  {header.get('method', '?'):<7} {chars:>9,}  {header.get('url', '?')}  {header.get('title', '')[:60]}")
    print(f"{len(paths)} page(s) in {PAGES_DIR.relative_to(ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls", nargs="*", metavar="URL")
    parser.add_argument("--list", action="store_true", help="list the pages cached in this run")
    args = parser.parse_args(argv)
    if args.list:
        return list_pages()
    if not args.urls:
        parser.error("give one or more URLs, or --list")

    urls = list(dict.fromkeys(args.urls))
    index = load_index()
    results = {url: index[cache_key(url)] for url in urls if cache_key(url) in index}
    todo = [url for url in urls if url not in results]
    if todo:
        headers = {"User-Agent": USER_AGENT, "Accept": ACCEPT, "Accept-Language": "en"}
        timeout = httpx.Timeout(30.0, connect=15.0)
        with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
            with ThreadPoolExecutor(max_workers=6) as pool:
                results.update(zip(todo, pool.map(lambda u: fetch(u, client), todo)))

    for url in urls:
        print(results[url].line())
    return 1 if any(results[url].state in {"failed", "thin"} for url in urls) else 0


if __name__ == "__main__":
    sys.exit(main())
