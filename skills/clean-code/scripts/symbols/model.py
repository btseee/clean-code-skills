#!/usr/bin/env python3
"""What a declared symbol is, and the facts every extractor records the same way.

Extractors differ per language; the record they produce, the doc summary, the
declaration context, and the duplicate fingerprints must not, or a Python
duplicate and a Go duplicate would be judged by different rules.

Standard library only.
"""

from __future__ import annotations

import hashlib
import re
from typing import NamedTuple, Optional

TYPE_KINDS = frozenset({"class", "interface", "enum", "struct", "trait", "protocol",
                        "record", "object"})

# A body shorter than this is too small for a duplicate to mean anything.
MIN_FINGERPRINT_LINES = 5

LICENSE_WORDS = re.compile(r"copyright|licen[cs]e|spdx|all rights reserved", re.IGNORECASE)

# Tool directives that sit where a file description would: not a purpose.
MAGIC_COMMENT = re.compile(
    r"^(?:frozen_string_literal|encoding|coding|typed|warn_indent|shellcheck|eslint|prettier|"
    r"@ts-|-\*-|#region|region\b|pylint|mypy|noqa|type:)", re.IGNORECASE)


class Symbol(NamedTuple):
    """One declaration: where it is, what it is, and what it is for."""

    name: str
    kind: str
    line: int
    end_line: int
    exported: bool
    parent: Optional[str] = None
    doc: str = ""
    context: str = ""
    exact: Optional[str] = None
    shape: Optional[str] = None
    abstract: bool = False


class Declaration(NamedTuple):
    """A variable or a parameter a file declares, where its extractor reads them reliably."""

    name: str
    kind: str                   # variable or parameter
    line: int
    owner: Optional[str] = None     # the class whose method declares this parameter


class FileSymbols(NamedTuple):
    """Everything one source file declares."""

    path: str
    language: str
    purpose: str
    lines: int
    symbols: list
    types: int
    abstract_types: int
    unparsed: str = ""          # why the file could not be read, so its symbols are missing
    declarations: tuple = ()    # its variables and parameters, by line


def file_symbols(path: str, language: str, purpose: str, text: str, symbols: list,
                 unparsed: str = "", declarations=()) -> FileSymbols:
    top_types = [s for s in symbols if s.kind in TYPE_KINDS and s.parent is None]
    return FileSymbols(
        path=path,
        language=language,
        purpose=purpose,
        lines=text.count("\n") + (0 if text.endswith("\n") or not text else 1),
        symbols=sorted(symbols, key=lambda symbol: (symbol.line, symbol.name)),
        types=len(top_types),
        abstract_types=sum(1 for symbol in top_types if symbol.abstract),
        unparsed=unparsed,
        declarations=tuple(declarations),
    )


_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


def first_sentence(text: str, limit: int = 100) -> str:
    """The first sentence of text, collapsed to one line and at most limit characters."""
    text = " ".join(text.split())
    if not text:
        return ""
    match = _SENTENCE_END.search(text)
    sentence = text[:match.start()] if match else text
    if len(sentence) > limit:
        sentence = sentence[:limit - 3].rstrip() + "..."
    return sentence


_COMMENT_MARKERS = re.compile(r"^(?:/\*\*?|\*/|\*|///?|//!|#'|#|--)\s?")
_XML_TAG = re.compile(r"</?\w+[^>]*>")


def comment_text(lines: list) -> str:
    """The prose inside a comment block, markers and doc tags removed."""
    words = []
    for raw in lines:
        line = raw.strip()
        if line.endswith("*/"):
            line = line[:-2].rstrip()
        line = _COMMENT_MARKERS.sub("", line).strip()
        line = _XML_TAG.sub("", line).strip()
        if not line or line.startswith("@"):
            continue
        words.append(line)
    return " ".join(words)


def is_comment_line(line: str, markers: tuple) -> bool:
    stripped = line.strip()
    return bool(stripped) and (stripped.startswith(markers) or stripped.endswith("*/"))


def doc_above(raw_lines: list, index: int, markers: tuple, skip: int = 0) -> str:
    """First sentence of the comment block ending just above line index (0-based).

    skip is the number of decorator or attribute lines between the comment and
    the declaration.
    """
    cursor = index - skip - 1
    block = []
    while cursor >= 0 and is_comment_line(raw_lines[cursor], markers):
        block.append(raw_lines[cursor])
        cursor -= 1
    return first_sentence(comment_text(list(reversed(block))))


def file_purpose(raw_lines: list, markers: tuple) -> str:
    """The file's leading comment block, if it stands apart and is not a license."""
    cursor = 0
    if raw_lines and raw_lines[0].startswith("#!"):
        cursor = 1
    while cursor < len(raw_lines) and not raw_lines[cursor].strip():
        cursor += 1
    block = []
    while cursor < len(raw_lines) and is_comment_line(raw_lines[cursor], markers):
        block.append(raw_lines[cursor])
        cursor += 1
    if not block:
        return ""
    stands_apart = cursor >= len(raw_lines) or not raw_lines[cursor].strip()
    text = comment_text(block)
    if not stands_apart or LICENSE_WORDS.search(text) or MAGIC_COMMENT.match(text):
        return ""
    return first_sentence(text)


def _is_decorator(stripped: str, decorators: tuple) -> bool:
    """A decorator is a line prefix, or a compiled pattern for shapes a prefix cannot name."""
    return any(stripped.startswith(decorator) if isinstance(decorator, str)
               else decorator.match(stripped) for decorator in decorators)


def declaration_context(raw_lines: list, code_lines: list, index: int, prefixes: tuple,
                        max_above: int = 12, max_declaration: int = 3):
    """(context text, number of decorator lines) for the declaration at line index.

    Decorator, annotation, and attribute lines directly above are included,
    including the continuation lines of a multi-line decorator, then the
    declaration itself up to the line that opens its body.
    """
    above = []
    pending = 0
    cursor = index - 1
    while cursor >= 0 and len(above) < max_above:
        stripped = code_lines[cursor].strip()
        if not stripped:
            break
        opens = sum(stripped.count(character) for character in "([{")
        closes = sum(stripped.count(character) for character in ")]}")
        # `})` can end a multi-line decorator; a lone `}` ends the previous block.
        ends_arguments = stripped[0] in ")]}" and (
            stripped.count(")") + stripped.count("]") > stripped.count("(") + stripped.count("["))
        if pending > 0 or _is_decorator(stripped, prefixes) or ends_arguments:
            above.append(raw_lines[cursor].rstrip())
            pending = max(pending + closes - opens, 0)
            cursor -= 1
            continue
        break
    declaration = []
    for offset in range(max_declaration):
        if index + offset >= len(raw_lines):
            break
        declaration.append(raw_lines[index + offset].rstrip())
        code = code_lines[index + offset]
        if "{" in code or code.rstrip().endswith((":", ";", "=>")):
            break
    return "\n".join(list(reversed(above)) + declaration), len(above)


_TOKEN = re.compile(r"""[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\S""")

KEYWORDS = frozenset("""
if else elif for while do switch case default break continue return try catch except finally
raise throw throws new delete class struct interface enum def fn func function fun let const var
val mut pub static async await yield in of is not and or null nil None true false True False
this self super import from as with lambda match when where select using namespace package
public private protected internal final abstract override virtual void int long float double
bool boolean char string str byte short unsigned signed type typeof instanceof sizeof go defer
chan map range end begin then unless until module require include extends implements get set
""".split())


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def fingerprints(body_lines: list):
    """(exact, shape) digests of a function body, or (None, None) when it is too short.

    exact ignores only layout; shape also abstracts identifiers and literals, so
    a renamed copy still matches.
    """
    lines = [" ".join(line.split()) for line in body_lines]
    lines = [line for line in lines if line]
    if len(lines) < MIN_FINGERPRINT_LINES:
        return None, None
    exact = "\n".join(lines)
    tokens = []
    for token in _TOKEN.findall(exact):
        first = token[0]
        if first.isalpha() or first == "_":
            tokens.append(token if token in KEYWORDS else "I")
        elif first.isdigit():
            tokens.append("N")
        elif first in "\"'":
            tokens.append("S")
        else:
            tokens.append(token)
    return _digest(exact), _digest(" ".join(tokens))


def pascal_case(stem: str) -> str:
    """`user-card` -> `UserCard`; `+page` -> `Page`."""
    words = re.findall(r"[A-Za-z0-9]+", stem)
    return "".join(word[:1].upper() + word[1:] for word in words) or stem
