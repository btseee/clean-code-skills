#!/usr/bin/env python3
"""Symbols declared in brace-delimited languages, found by one engine.

A language contributes a Grammar: patterns for its type and function
declarations, which blocks are only namespaces, how its decorators and doc
comments look, and what makes a name exported. The engine applies the same rules
to all of them: top level versus member, body extent by brace matching, context,
doc summary, and duplicate fingerprints.

Standard library only.
"""

from __future__ import annotations

import bisect
import re
from typing import Callable, NamedTuple, Optional

from source import lexer as source_lexer

from . import model as symbol_model
from .model import Symbol


class Pattern(NamedTuple):
    """One kind of declaration. The regex defines a `name` group; it may define
    `kind` (overrides the default kind) and `parent` (an explicit owner, such as a
    Go receiver or a C++ `Class::` qualifier)."""

    regex: re.Pattern
    kind: str
    container: bool = False
    emit: bool = True
    on_raw: bool = False
    confirm: Optional[Callable] = None
    require_body: bool = False


# Multi-word declaration keywords, reduced to the kind the rest of the scanner uses.
KIND_ALIASES = {
    "enum class": "enum", "annotation class": "interface", "@interface": "interface",
    "fun interface": "interface", "record class": "record", "record struct": "record",
    "mixin": "class", "mixin class": "class", "actor": "class", "union": "struct",
}


class Grammar(NamedTuple):
    language: str
    lexer: str
    types: tuple
    functions: tuple
    members: tuple
    transparent: Optional[re.Pattern]
    decorators: tuple
    doc_markers: tuple
    keywords: frozenset
    exported: Callable
    abstract: Callable
    skip: Optional[re.Pattern] = None
    finish: Optional[Callable] = None
    purpose: Optional[Callable] = None
    indent_blocks: bool = False
    regions: Optional[Callable] = None
    # Matches the signature text before a `{` that opens a type, not the body: Go's
    # `interface{}` in `func Get() interface{} {`.
    type_literal: Optional[re.Pattern] = None


# member_indent: None for a brace body (members sit one brace deeper), a column for an
# indentation body, or REGION for a keyword-delimited body such as Objective-C's
# `@implementation ... @end`, whose members sit at the region's own brace depth.
REGION = -1


class Container(NamedTuple):
    open: int
    close: int
    name: str
    member_indent: Optional[int] = None


# rustfmt, Swift, and C# may put a generic `where` clause at the declaration's own
# indentation, between the signature and the body.
_WHERE = re.compile(r"where\b")


def _open_brackets(text: str) -> int:
    """How many `(` or `[` text leaves unclosed."""
    depth = 0
    for character in text:
        if character in "([":
            depth += 1
        elif character in ")]" and depth:
            depth -= 1
    return depth


class Source:
    """One file in the forms extraction needs, with offset and depth lookups."""

    def __init__(self, text: str, lexer: str):
        self.text = text
        stripped = source_lexer.strip(text, lexer)
        self.code = stripped.code
        self.no_comments = stripped.no_comments
        self.raw_lines = text.split("\n")
        self.code_lines = self.code.split("\n")
        self.nc_lines = self.no_comments.split("\n")
        self.line_starts = [0] + [match.end() for match in re.finditer("\n", text)]
        self.braces = source_lexer.match_braces(self.code)
        self._brace_offsets = []
        self._brace_depths = []
        depth = 0
        for match in re.finditer(r"[{}]", self.code):
            depth = depth + 1 if match.group() == "{" else max(depth - 1, 0)
            self._brace_offsets.append(match.start())
            self._brace_depths.append(depth)
        self._bracket_index = None

    def line_of(self, offset: int) -> int:
        """1-based line number of an offset."""
        return bisect.bisect_right(self.line_starts, offset)

    def depth_before(self, offset: int) -> int:
        index = bisect.bisect_left(self._brace_offsets, offset) - 1
        return self._brace_depths[index] if index >= 0 else 0

    def bracket_depth_before(self, offset: int) -> int:
        """The `(` and `[` open at offset, counted from the innermost enclosing `{`."""
        if self._bracket_index is None:
            offsets, depths, open_counts = [], [], [0]
            for match in re.finditer(r"[(){}\[\]]", self.code):
                character = match.group()
                if character == "{":
                    open_counts.append(0)
                elif character == "}":
                    if len(open_counts) > 1:
                        open_counts.pop()
                elif character in "([":
                    open_counts[-1] += 1
                elif open_counts[-1]:
                    open_counts[-1] -= 1
                offsets.append(match.start())
                depths.append(open_counts[-1])
            self._bracket_index = (offsets, depths)
        offsets, depths = self._bracket_index
        index = bisect.bisect_left(offsets, offset) - 1
        return depths[index] if index >= 0 else 0

    def blocks(self, regex: Optional[re.Pattern]) -> list:
        """(open, close) of every block whose opener regex matches, ending at its `{`."""
        spans = []
        if regex is None:
            return spans
        for match in regex.finditer(self.code):
            open_index = self.code.rfind("{", match.start(), match.end())
            if open_index >= 0 and open_index in self.braces:
                spans.append((open_index, self.braces[open_index]))
        return spans

    def indent_of(self, offset: int) -> int:
        line = self.code_lines[self.line_of(offset) - 1]
        return len(line) - len(line.lstrip())

    def indent_block(self, line_index: int):
        """(last line index, member indentation) of an indentation-delimited block
        opened by the declaration on line_index, as in Scala 3 or Python."""
        declaration = self.code_lines[line_index]
        base = len(declaration) - len(declaration.lstrip())
        last = line_index
        member_indent = None
        for index in range(line_index + 1, len(self.code_lines)):
            line = self.code_lines[index]
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base:
                break
            if member_indent is None:
                member_indent = indent
            last = index
        return last, member_indent

    def _next_line(self, offset: int) -> Optional[str]:
        line_number = self.line_of(offset)
        while line_number <= len(self.code_lines):
            line = self.code_lines[line_number - 1]
            if line.strip():
                return line
            line_number += 1
        return None

    def _returned_object(self, paren_index: int) -> Optional[int]:
        """The `{` of `=> ({ ... })`, an arrow whose body is an object literal."""
        code = self.code
        before = paren_index - 1
        while before > 0 and code[before] in " \t\r\n":
            before -= 1
        if code[before - 1:before + 1] != "=>":
            return None
        after = paren_index + 1
        while after < len(code) and code[after] in " \t\r\n":
            after += 1
        return after if after in self.braces else None

    def body_after(self, offset: int, declaration_start: int, open_brackets: int = 0,
                   type_literal: Optional[re.Pattern] = None) -> Optional[int]:
        """Offset of the `{` opening the body of the declaration ending near offset.

        open_brackets counts the `(` or `[` the declaration match left open, as
        `function f(` does, so a `{` inside the parameter list is never the body.
        Stops at a `;`, at a line that ends a braceless declaration (`:`, `=`,
        `=>`), or at a following line that is neither an Allman-style `{`, a
        `where` clause, nor an indented continuation of the signature.
        """
        code = self.code
        indent = self.indent_of(declaration_start)
        paren = open_brackets
        index = offset
        while index < len(code):
            character = code[index]
            if character == "(" and paren <= 0:
                literal = self._returned_object(index)
                if literal is not None:
                    return literal
            if character in "([":
                paren += 1
            elif character in ")]":
                paren -= 1
            elif character == "{" and paren <= 0:
                if index not in self.braces:
                    return None
                if type_literal is None or not type_literal.search(code, offset, index):
                    return index
                index = self.braces[index]
            elif character == ";" and paren <= 0:
                return None
            elif character == "\n" and paren <= 0:
                line_start = self.line_starts[self.line_of(index) - 1]
                if code[line_start:index].rstrip().endswith((":", "=", "=>")):
                    return None
                following = self._next_line(index + 1)
                if following is None:
                    return None
                stripped = following.strip()
                if not (stripped.startswith("{") or _WHERE.match(stripped) or
                        len(following) - len(following.lstrip()) > indent):
                    return None
            index += 1
        return None


def _within(offset: int, spans) -> bool:
    return any(open_index < offset < close for open_index, close in spans)


def _effective_depth(source: Source, offset: int, transparent) -> int:
    return source.depth_before(offset) - sum(
        1 for open_index, close in transparent if open_index < offset < close)


def _innermost(containers, offset: int) -> Optional[Container]:
    found = None
    for container in containers:
        if container.open < offset < container.close and (
                found is None or container.open > found.open):
            found = container
    return found


def _group(match, name: str) -> Optional[str]:
    return match.groupdict().get(name)


class _Extraction:
    def __init__(self, grammar: Grammar, source: Source):
        self.grammar = grammar
        self.source = source
        self.transparent = source.blocks(grammar.transparent)
        self.skipped = source.blocks(grammar.skip)
        self.containers = []
        self.symbols = []
        self.seen = set()

    def matches(self, pattern: Pattern):
        text = self.source.no_comments if pattern.on_raw else self.source.code
        for match in pattern.regex.finditer(text):
            name = match.group("name")
            if not name or name in self.grammar.keywords:
                continue
            if _within(match.start(), self.skipped):
                continue
            if pattern.confirm and not pattern.confirm(self.source, match):
                continue
            yield match, name

    def body_of(self, match) -> Optional[int]:
        source = self.source
        return source.body_after(match.end(), match.start(),
                                 _open_brackets(source.code[match.start():match.end()]),
                                 self.grammar.type_literal)

    def add(self, match, name: str, kind: str, parent: Optional[str], is_member: bool,
            emit: bool = True, end_line: Optional[int] = None,
            require_body: bool = False) -> Optional[int]:
        source = self.source
        index = source.line_of(match.start()) - 1
        body = self.body_of(match)
        if require_body and body is None:
            return None
        if end_line is None:
            end_line = source.line_of(source.braces[body]) if body is not None else index + 1
        if not emit or (index + 1, name) in self.seen:
            return body
        self.seen.add((index + 1, name))
        context, decorator_count = symbol_model.declaration_context(
            source.raw_lines, source.code_lines, index, self.grammar.decorators)
        exact = shape = None
        if kind in {"function", "method"} and body is not None:
            exact, shape = symbol_model.fingerprints(source.nc_lines[index + 1:end_line])
        body_code = source.code[body:source.braces[body]] if body is not None else ""
        self.symbols.append(Symbol(
            name=name,
            kind=kind,
            line=index + 1,
            end_line=end_line,
            exported=bool(self.grammar.exported(match, name, kind, is_member)),
            parent=parent,
            doc=symbol_model.doc_above(source.raw_lines, index, self.grammar.doc_markers,
                                       skip=decorator_count),
            context=context,
            exact=exact,
            shape=shape,
            abstract=bool(self.grammar.abstract(match, kind, body_code)),
        ))
        return body

    def types(self):
        for pattern in self.grammar.types:
            for match, name in self.matches(pattern):
                if _effective_depth(self.source, match.start(), self.transparent) != 0:
                    continue
                kind = " ".join((_group(match, "kind") or pattern.kind).split())
                kind = KIND_ALIASES.get(kind, kind)
                owner_name = _group(match, "parent") or name
                indented = self.indented_container(match, owner_name) if pattern.container else None
                end_line = self.source.line_of(indented.close) if indented else None
                body = self.add(match, name, kind, None, False, emit=pattern.emit,
                                end_line=end_line)
                if indented is not None:
                    self.containers.append(indented)
                elif pattern.container and body is not None:
                    self.containers.append(
                        Container(body, self.source.braces[body], owner_name))

    def indented_container(self, match, name: str) -> Optional[Container]:
        """A container whose body is delimited by indentation, when the grammar allows it."""
        source = self.source
        if not self.grammar.indent_blocks:
            return None
        if self.body_of(match) is not None:
            return None
        index = source.line_of(match.start()) - 1
        if not source.code_lines[index].rstrip().endswith(":"):
            return None
        last, member_indent = source.indent_block(index)
        if member_indent is None:
            return None
        close = source.line_starts[last] + len(source.code_lines[last])
        return Container(source.line_starts[index + 1] - 1, close, name, member_indent)

    def functions(self, patterns, members_only: bool):
        for pattern in patterns:
            for match, name in self.matches(pattern):
                start = match.start()
                owner = _innermost(self.containers, start)
                explicit_parent = _group(match, "parent")
                if owner is not None:
                    if not self.is_member_of(owner, start):
                        continue
                    self.add(match, name, "method", owner.name, True,
                             require_body=pattern.require_body)
                elif not members_only and \
                        _effective_depth(self.source, start, self.transparent) == 0:
                    kind = "method" if explicit_parent else pattern.kind
                    self.add(match, name, kind, explicit_parent, bool(explicit_parent),
                             require_body=pattern.require_body)

    def is_member_of(self, owner: Container, start: int) -> bool:
        source = self.source
        if owner.member_indent == REGION:
            return source.depth_before(start) == source.depth_before(owner.open)
        if owner.member_indent is not None:
            return source.indent_of(start) == owner.member_indent
        return source.depth_before(start) == source.depth_before(owner.open) + 1


def extract(grammar: Grammar, path: str, text: str) -> symbol_model.FileSymbols:
    source = Source(text, grammar.lexer)
    extraction = _Extraction(grammar, source)
    if grammar.regions is not None:
        extraction.containers.extend(grammar.regions(source))
    extraction.types()
    extraction.functions(grammar.functions, members_only=False)
    extraction.functions(grammar.members, members_only=True)
    symbols = extraction.symbols
    if grammar.finish is not None:
        symbols = grammar.finish(symbols, source)
    purpose = (grammar.purpose(source) if grammar.purpose is not None
               else symbol_model.file_purpose(source.raw_lines, grammar.doc_markers))
    return symbol_model.file_symbols(path, grammar.language, purpose, text, symbols)
