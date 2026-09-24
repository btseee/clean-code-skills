#!/usr/bin/env python3
"""Prove a terse rewrite lost nothing technical.

Compares an original instruction file or comment against its compressed
rewrite and reports anything a fact-checker would flag: headings, fenced code
blocks, inline code spans, URLs, rule IDs, and numbers. Losing a sentence of
connective prose is the point of compression; losing one of these is a bug in
the rewrite.

Each kind of item is counted as its own multiset (collections.Counter) and
compared independently: a number that also sits inside a rule ID, a URL, or
an inline code span is still counted once for each kind it matches, and the
kinds are never reconciled against each other. Headings and inline code are
only recognised outside a fenced code block, so a `#` or a stray backtick
inside an example is never mistaken for markdown syntax; URLs, rule IDs, and
numbers are counted everywhere, fenced code included.

Tokens are estimated as round(words * 4 / 3) -- Python's built-in round(),
which breaks .5 ties to even -- with words counted as whitespace-separated
chunks. That is a rough proxy to size a reduction, not a real tokenizer.

Standard library only. Reads the two files named on the command line; writes
nothing.

Usage:
    python check_compression.py ORIGINAL COMPRESSED
    python check_compression.py ORIGINAL COMPRESSED --json

Exits 0 when nothing technical was lost, 1 when something was, 2 on a usage
or read error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import NamedTuple

CATEGORIES = ("heading", "code block", "inline code", "url", "rule id", "number")

# A line that only opens or closes a fenced block; what is on it otherwise
# (a language tag on the opening line) does not matter.
FENCE_MARKER = re.compile(r"^(`{3,}|~{3,})")
INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
URL_ANGLE_PATTERN = re.compile(r"<(https?://[^>\s]+)>")
URL_BARE_PATTERN = re.compile(r"https?://\S+")
RULE_ID_PATTERN = re.compile(r"\b[A-Z]{1,2}\d{1,2}\b")
NUMBER_PATTERN = re.compile(r"\b\d[\d,.]*\b")


class Report(NamedTuple):
    """What the compressed text lost against the original, and how much smaller it got."""

    losses: list
    original_tokens: int
    compressed_tokens: int
    reduction: float


def _count_tokens(text: str) -> int:
    return round(len(text.split()) * 4 / 3)


def _mask(text: str, spans) -> str:
    """`text` with each (start, end) span blanked to spaces, same length, same offsets."""
    if not spans:
        return text
    characters = list(text)
    for start, end in spans:
        for index in range(start, end):
            characters[index] = " "
    return "".join(characters)


def _find_urls(text: str):
    """(url, offset) pairs: angle-wrapped URLs first, then bare ones outside those spans.

    `<https://example.com/a>` must not also be picked up by the bare pattern as
    "https://example.com/a>" -- its span is blanked out before the bare pattern runs.
    """
    found = []
    spans = []
    for match in URL_ANGLE_PATTERN.finditer(text):
        found.append((match.group(1), match.start(1)))
        spans.append(match.span())
    masked = _mask(text, spans)
    for match in URL_BARE_PATTERN.finditer(masked):
        url = match.group(0).rstrip(".,;:!?)]}'\"")
        found.append((url, match.start()))
    return found


def _closes_fence(stripped: str, opener: str) -> bool:
    """CommonMark: only a run of the opener's character, at least as long, with nothing after it."""
    run = len(stripped) - len(stripped.lstrip(opener[0]))
    return run >= len(opener) and not stripped[run:]


def _extract(text: str):
    """(category -> Counter of items, [(category, item), ...] in first-seen order)."""
    counts = {category: Counter() for category in CATEGORIES}
    first_seen = {}

    def record(category, item, position):
        counts[category][item] += 1
        first_seen.setdefault((category, item), position)

    in_fence = False
    fence_open_offset = 0
    fence_marker = ""
    block_lines = []
    block_offset = None
    offset = 0

    def close_block():
        record("code block", "\n".join(block_lines),
                block_offset if block_offset is not None else fence_open_offset)

    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        line_offset = offset
        offset += len(line)
        stripped = body.strip()

        fence_match = None if in_fence else FENCE_MARKER.match(stripped)
        if fence_match:
            fence_marker = fence_match.group(1)
            fence_open_offset = line_offset
            block_lines = []
            block_offset = None
            in_fence = True
            continue

        if in_fence:
            if _closes_fence(stripped, fence_marker):
                close_block()
                in_fence = False
                continue
            if block_offset is None:
                block_offset = line_offset
            block_lines.append(body)
            continue

        if stripped.startswith("#"):
            record("heading", stripped.strip("# "), line_offset)
        for match in INLINE_CODE_PATTERN.finditer(body):
            record("inline code", match.group(1), line_offset + match.start())

    if in_fence:
        close_block()

    for url, position in _find_urls(text):
        record("url", url, position)
    for match in RULE_ID_PATTERN.finditer(text):
        record("rule id", match.group(0), match.start())
    for match in NUMBER_PATTERN.finditer(text):
        record("number", match.group(0), match.start())

    order = sorted(first_seen, key=first_seen.get)
    return counts, order


def _format_loss(category: str, item: str) -> str:
    if category == "code block":
        first_line = item.splitlines()[0] if item else ""
        return f"code block: {first_line}"
    return f"{category}: {item}"


def compare(original_text: str, compressed_text: str) -> Report:
    """Everything preserved-item multiset comparison says the rewrite dropped."""
    original_counts, original_order = _extract(original_text)
    compressed_counts, _ = _extract(compressed_text)

    losses = [
        _format_loss(category, item)
        for category, item in original_order
        if compressed_counts[category][item] < original_counts[category][item]
    ]

    original_tokens = _count_tokens(original_text)
    compressed_tokens = _count_tokens(compressed_text)
    reduction = 0.0 if original_tokens == 0 else round(1 - compressed_tokens / original_tokens, 3)
    return Report(losses, original_tokens, compressed_tokens, reduction)


def render_report(report: Report) -> str:
    label = "nothing lost" if not report.losses else f"{len(report.losses)} lost"
    summary = (f"{label}: {report.original_tokens:,} -> {report.compressed_tokens:,} tokens "
               f"({report.reduction * 100:.1f}% smaller)")
    return "\n".join([*report.losses, summary])


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare an original text against its compressed rewrite and report "
                     "anything technical that went missing.",
    )
    parser.add_argument("original", help="path to the original file")
    parser.add_argument("compressed", help="path to the compressed rewrite")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = parse_arguments(argv if argv is not None else sys.argv[1:])
    # A pipe on Windows defaults to the ANSI code page, which cannot encode most names;
    # UTF-8 can, and it is what JSON consumers expect.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

    try:
        # utf-8-sig drops a byte-order mark: Windows tools write one, and it would
        # otherwise sit in front of the first heading or shebang.
        original_text = Path(arguments.original).read_text(encoding="utf-8-sig", errors="replace")
        compressed_text = Path(arguments.compressed).read_text(encoding="utf-8-sig", errors="replace")
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    report = compare(original_text, compressed_text)

    if arguments.json:
        print(json.dumps({
            "losses": report.losses,
            "original_tokens": report.original_tokens,
            "compressed_tokens": report.compressed_tokens,
            "reduction": report.reduction,
        }, indent=2, ensure_ascii=False))
    else:
        print(render_report(report))

    return 1 if report.losses else 0


if __name__ == "__main__":
    sys.exit(main())
