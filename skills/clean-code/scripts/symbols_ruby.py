#!/usr/bin/env python3
"""Symbols declared in a Ruby file.

Ruby closes blocks with `end`, not braces, and idiomatic Ruby is indented
consistently, so a declaration's extent is the first following `end` at its own
indentation. Classes count as top-level even inside namespacing modules: that is
how Rails and gems nest `Admin::UsersController`.

Standard library only.
"""

from __future__ import annotations

import bisect
import re
from typing import NamedTuple, Optional

import source_lexer
import symbol_model
from symbol_model import Symbol

_CLASS = re.compile(r"^(?P<indent>[ \t]*)class[ \t]+(?P<name>[A-Z]\w*(?:::[A-Z]\w*)*)(?P<rest>[^\n]*)",
                    re.M)
_MODULE = re.compile(r"^(?P<indent>[ \t]*)module[ \t]+(?P<name>[A-Z]\w*(?:::[A-Z]\w*)*)", re.M)
_DEF = re.compile(r"^(?P<indent>[ \t]*)def[ \t]+(?:self\.)?(?P<name>[\w?!=]+|\[\]=?|[+\-*/<=>!%&|^~]+)",
                  re.M)
_ONE_LINER = re.compile(r"(?:;\s*end|\bend)\s*$|\)\s*=\s*\S|^\s*def\s+[\w.?!]+\s*=\s*\S")
_END = re.compile(r"^end\b")

DOC_MARKERS = ("#",)


class _Block(NamedTuple):
    name: str
    kind: str
    line: int
    end_line: int
    indent: int


def _end_line(code_lines: list, index: int, indent: int) -> int:
    """1-based line of the `end` closing the declaration on line index."""
    if _ONE_LINER.search(code_lines[index]):
        return index + 1
    for cursor in range(index + 1, len(code_lines)):
        line = code_lines[cursor]
        stripped = line.strip()
        if not stripped:
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= indent:
            return cursor + 1 if _END.match(stripped) else cursor
    return len(code_lines)


def _innermost(blocks: list, line: int, indent: int) -> Optional[_Block]:
    found = None
    for block in blocks:
        if block.line < line <= block.end_line and block.indent < indent and (
                found is None or block.line > found.line):
            found = block
    return found


def extract(path: str, text: str) -> symbol_model.FileSymbols:
    stripped = source_lexer.strip(text, "ruby")
    code = stripped.code
    code_lines = code.split("\n")
    raw_lines = text.split("\n")
    nc_lines = stripped.no_comments.split("\n")
    line_starts = [0] + [match.end() for match in re.finditer("\n", code)]

    def line_of(offset: int) -> int:
        return bisect.bisect_right(line_starts, offset)

    blocks = []
    for pattern, kind in ((_CLASS, "class"), (_MODULE, "module")):
        for match in pattern.finditer(code):
            if kind == "class" and match.group("rest").lstrip().startswith("<<"):
                continue
            index = line_of(match.start()) - 1
            indent = len(match.group("indent"))
            blocks.append(_Block(match.group("name").split("::")[-1], kind, index + 1,
                                 _end_line(code_lines, index, indent), indent))

    symbols = []
    for block in blocks:
        index = block.line - 1
        symbols.append(Symbol(
            name=block.name,
            kind=block.kind,
            line=block.line,
            end_line=block.end_line,
            exported=True,
            doc=symbol_model.doc_above(raw_lines, index, DOC_MARKERS),
            context=raw_lines[index].rstrip(),
        ))

    for match in _DEF.finditer(code):
        index = line_of(match.start()) - 1
        indent = len(match.group("indent"))
        end_line = _end_line(code_lines, index, indent)
        owner = _innermost(blocks, index + 1, indent)
        exact, shape = symbol_model.fingerprints(nc_lines[index + 1:end_line])
        symbols.append(Symbol(
            name=match.group("name"),
            kind="method" if owner else "function",
            line=index + 1,
            end_line=end_line,
            exported=True,
            parent=owner.name if owner else None,
            doc=symbol_model.doc_above(raw_lines, index, DOC_MARKERS),
            context=raw_lines[index].rstrip(),
            exact=exact,
            shape=shape,
        ))

    purpose = symbol_model.file_purpose(raw_lines, DOC_MARKERS)
    return symbol_model.file_symbols(path, "ruby", purpose, text, symbols)
