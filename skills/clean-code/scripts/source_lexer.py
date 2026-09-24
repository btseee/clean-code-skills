#!/usr/bin/env python3
"""Blank out comments and string literals while keeping every offset.

Symbol extraction finds declarations with regular expressions and measures
bodies by matching braces. Both go wrong inside comments and strings: a `}` in
a string ends a function early, and a commented-out class looks declared. So
they run over a copy of the source where comments and string contents are
spaces. Lines and offsets stay identical, so every match maps straight back.

The lexer is deliberately approximate: it knows each language's comment and
string forms well enough for declarations and braces, not for compilation.

Standard library only.
"""

from __future__ import annotations

import re
from typing import NamedTuple, Optional


class Stripped(NamedTuple):
    """The same text twice: without comments or strings, and without comments."""

    code: str
    no_comments: str


class _Syntax(NamedTuple):
    line_comments: tuple = ()
    block_comments: tuple = ()
    nested_blocks: bool = False
    quotes: str = '"'
    multiline_quotes: bool = False
    raw_single_quotes: bool = False
    escape: str = "\\"
    doubled_quote_escape: bool = False
    char_quote: bool = False
    triple_quotes: str = ""
    template_backtick: bool = False
    raw_backtick: bool = False
    regex_literals: bool = False
    regex_keywords: frozenset = frozenset()
    percent_literals: bool = False
    verbatim_at: bool = False
    rust_raw: bool = False
    hash_word_start: bool = False
    php_attributes: bool = False
    heredoc: str = ""


# Words after which a `/` starts a regex rather than dividing.
_JS_REGEX_KEYWORDS = frozenset({"return", "typeof", "case", "do", "else", "in", "of", "new", "delete",
                                "void", "throw", "yield", "await"})
_RUBY_REGEX_KEYWORDS = frozenset({"if", "elsif", "unless", "when", "while", "until", "and", "or",
                                  "not", "return", "then", "in", "case"})

_C_BLOCK = (("/*", "*/"),)
_JS = _Syntax(("//",), _C_BLOCK, quotes="\"'", template_backtick=True, regex_literals=True,
              regex_keywords=_JS_REGEX_KEYWORDS)
_C = _Syntax(("//",), _C_BLOCK, char_quote=True)

SYNTAX = {
    "javascript": _JS,
    "typescript": _JS,
    "java": _Syntax(("//",), _C_BLOCK, char_quote=True, triple_quotes='"'),
    "kotlin": _Syntax(("//",), _C_BLOCK, nested_blocks=True, char_quote=True, triple_quotes='"'),
    "scala": _Syntax(("//",), _C_BLOCK, nested_blocks=True, char_quote=True, triple_quotes='"'),
    "swift": _Syntax(("//",), _C_BLOCK, nested_blocks=True, triple_quotes='"'),
    "csharp": _Syntax(("//",), _C_BLOCK, char_quote=True, triple_quotes='"', verbatim_at=True),
    "go": _Syntax(("//",), _C_BLOCK, char_quote=True, raw_backtick=True),
    "rust": _Syntax(("//",), _C_BLOCK, nested_blocks=True, char_quote=True, rust_raw=True),
    "dart": _Syntax(("//",), _C_BLOCK, nested_blocks=True, quotes="\"'", triple_quotes="\"'"),
    "php": _Syntax(("//", "#"), _C_BLOCK, quotes="\"'", multiline_quotes=True,
                   php_attributes=True, heredoc="php"),
    "c": _C,
    "cpp": _C,
    "objc": _C,
    "python": _Syntax(("#",), (), quotes="\"'", triple_quotes="\"'"),
    "ruby": _Syntax(("#",), (("=begin", "=end"),), quotes="\"'", multiline_quotes=True,
                    regex_literals=True, regex_keywords=_RUBY_REGEX_KEYWORDS, percent_literals=True,
                    heredoc="ruby"),
    "shell": _Syntax(("#",), (), quotes="\"'", multiline_quotes=True, raw_single_quotes=True,
                     hash_word_start=True, heredoc="shell"),
    "powershell": _Syntax(("#",), (("<#", "#>"),), quotes="\"'", multiline_quotes=True,
                          raw_single_quotes=True, escape="`", doubled_quote_escape=True,
                          heredoc="powershell"),
    "r": _Syntax(("#",), (), quotes="\"'", multiline_quotes=True),
}

_REGEX_PRECEDERS = set("(,=:[!&|?{};+-*%<>~^")
# Exactly one character or one escape. Allowing more read a Rust lifetime as a literal
# whenever another quote followed: `impl<'a> Parser<'a>` lost `Parser`.
_CHAR_LITERAL = re.compile(r"'(?:[^'\\\n]|\\(?:x[0-9A-Fa-f]{1,8}|u\{[0-9A-Fa-f]{1,6}\}|u[0-9A-Fa-f]{4}"
                           r"|U[0-9A-Fa-f]{8}|[0-7]{1,3}|.))'")
_RUBY_PERCENT = re.compile(r"%([qQwWiIrsx]?)([^\w\s])")
_PAIRED_DELIMITERS = {"(": ")", "[": "]", "{": "}", "<": ">"}
_RUST_RAW = re.compile(r"b?r(#*)\"")
_SHELL_HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_RUBY_HEREDOC = re.compile(r"<<([~-]?)(['\"]?)([A-Z_][A-Z0-9_]*)\2")
_PHP_HEREDOC = re.compile(r"<<<[ \t]*(['\"]?)([A-Za-z_]\w*)\1")
_POWERSHELL_HERESTRING = re.compile(r"@(['\"])[ \t]*\r?\n")


def _openers(syntax: _Syntax) -> re.Pattern:
    tokens = set(syntax.line_comments)
    tokens.update(opener for opener, _ in syntax.block_comments)
    tokens.update(quote * 3 for quote in syntax.triple_quotes)
    tokens.update(syntax.quotes)
    if syntax.char_quote:
        tokens.add("'")
    if syntax.template_backtick or syntax.raw_backtick:
        tokens.add("`")
    if syntax.regex_literals:
        tokens.add("/")
    if syntax.percent_literals:
        tokens.add("%")
    if syntax.verbatim_at:
        tokens.update({'@"', '@$"', '$@"'})
    if syntax.heredoc in {"shell", "ruby"}:
        tokens.add("<<")
    if syntax.heredoc == "php":
        tokens.add("<<<")
    if syntax.heredoc == "powershell":
        tokens.update({'@"', "@'"})
    alternatives = [re.escape(token) for token in sorted(tokens, key=len, reverse=True)]
    if syntax.rust_raw:
        alternatives.insert(0, r"(?<![\w])b?r#*\"")
    return re.compile("|".join(alternatives))


_OPENERS = {name: _openers(syntax) for name, syntax in SYNTAX.items()}


def _line_end(text: str, position: int) -> int:
    end = text.find("\n", position)
    return len(text) if end < 0 else end


def _block_end(text: str, position: int, opener: str, closer: str, nested: bool) -> int:
    if not nested:
        end = text.find(closer, position + len(opener))
        return len(text) if end < 0 else end + len(closer)
    depth = 0
    index = position
    while index < len(text):
        if text.startswith(opener, index):
            depth += 1
            index += len(opener)
            continue
        if text.startswith(closer, index):
            depth -= 1
            index += len(closer)
            if depth == 0:
                return index
            continue
        index += 1
    return len(text)


def _quoted_end(text: str, position: int, syntax: _Syntax) -> int:
    quote = text[position]
    raw = quote == "'" and syntax.raw_single_quotes
    index = position + 1
    while index < len(text):
        character = text[index]
        if character == syntax.escape and not raw:
            index += 2
            continue
        if character == quote:
            if syntax.doubled_quote_escape and text.startswith(quote, index + 1):
                index += 2
                continue
            return index + 1
        if character == "\n" and not syntax.multiline_quotes:
            return index
        index += 1
    return len(text)


def _triple_end(text: str, position: int, delimiter: str) -> int:
    index = position + 3
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text.startswith(delimiter, index):
            return index + 3
        index += 1
    return len(text)


def _template_end(text: str, position: int) -> int:
    """End of the template literal opening at position, nested templates included.

    A stack instead of recursion: templates nested a few thousand deep would overflow
    Python's call stack and abort the whole scan.
    """
    enclosing = []       # brace depth of each `${ }` holding a nested template
    depth = 0            # brace depth inside the current `${ }`; 0 means template text
    index = position + 1
    while index < len(text):
        character = text[index]
        if depth == 0:
            if character == "\\":
                index += 2
                continue
            if character == "`":
                if not enclosing:
                    return index + 1
                depth = enclosing.pop()
            elif text.startswith("${", index):
                depth = 1
                index += 1
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
        elif character == "`":
            enclosing.append(depth)
            depth = 0
        index += 1
    return len(text)


def _starts_regex(text: str, position: int, keywords: frozenset) -> bool:
    """Whether the `/` (or Ruby `%`) at position begins a literal rather than an operator."""
    # `</` closes a JSX tag and `/>` ends one; a regex after `<` needs a space: `a < /re/`.
    if (position > 0 and text[position - 1] == "<") or text.startswith("/>", position):
        return False
    index = position - 1
    while index >= 0 and text[index] in " \t":
        index -= 1
    if index < 0 or text[index] == "\n":
        return True
    if text[index] in _REGEX_PRECEDERS:
        return True
    word = re.search(r"([A-Za-z_]+)$", text[max(0, index - 10):index + 1])
    return bool(word and word.group(1) in keywords)


def _regex_end(text: str, position: int) -> Optional[int]:
    index = position + 1
    in_class = False
    while index < len(text):
        character = text[index]
        if character == "\n":
            return None
        if character == "\\":
            index += 2
            continue
        if character == "[":
            in_class = True
        elif character == "]":
            in_class = False
        elif character == "/" and not in_class:
            return index + 1
        index += 1
    return None


def _percent_span(text: str, position: int, keywords: frozenset):
    """(delimiter start, end) of a Ruby %-literal (`%w[a b]`, `%q(it's)`, `%r{a/b}`), or None.

    `%` is also modulo. A literal starts an expression, or, typed (`%w`), follows a
    space as a method argument: `puts %w[a b]`.
    """
    match = _RUBY_PERCENT.match(text, position)
    if match is None:
        return None
    typed_argument = bool(match.group(1)) and position > 0 and text[position - 1] in " \t"
    if not (typed_argument or _starts_regex(text, position, keywords)):
        return None
    opener = match.group(2)
    closer = _PAIRED_DELIMITERS.get(opener, opener)
    depth = 1
    index = match.end()
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character == closer:
            depth -= 1
            if depth == 0:
                return match.start(2), index + 1
        elif character == opener:
            depth += 1
        index += 1
    return match.start(2), len(text)


def _verbatim_end(text: str, position: int) -> int:
    index = text.index('"', position) + 1
    while index < len(text):
        if text[index] == '"':
            if text.startswith('"', index + 1):
                index += 2
                continue
            return index + 1
        index += 1
    return len(text)


def _heredoc_span(text: str, position: int, syntax: _Syntax):
    """(body start, body end) for a heredoc opening at position, or None."""
    if syntax.heredoc == "shell":
        if text.startswith("<<<", position):
            return None
        # Inside `$(( ))` or `(( ))`, `<<` shifts bits.
        prefix = text[text.rfind("\n", 0, position) + 1:position]
        if prefix.count("((") > prefix.count("))"):
            return None
        match = _SHELL_HEREDOC.match(text, position)
        terminator = match and match.group(3)
    elif syntax.heredoc == "ruby":
        match = _RUBY_HEREDOC.match(text, position)
        terminator = match and match.group(3)
    elif syntax.heredoc == "php":
        match = _PHP_HEREDOC.match(text, position)
        terminator = match and match.group(2)
    else:
        match = _POWERSHELL_HERESTRING.match(text, position)
        terminator = match and (match.group(1) + "@")
    if not match:
        return None
    body_start = _line_end(text, position) + 1
    index = body_start
    while index < len(text):
        line_end = _line_end(text, index)
        line = text[index:line_end].strip()
        if syntax.heredoc == "powershell":
            if text[index:line_end].startswith(terminator):
                return body_start, line_end
        elif line == terminator or (syntax.heredoc == "php" and re.match(
                re.escape(terminator) + r"\b", line)):
            return body_start, line_end
        index = line_end + 1
    return body_start, len(text)


def _spans(text: str, language: str) -> list:
    syntax = SYNTAX[language]
    openers = _OPENERS[language]
    spans = []
    position = 0
    block_closers = dict(syntax.block_comments)
    while True:
        match = openers.search(text, position)
        if match is None:
            return spans
        token = match.group(0)
        start = match.start()

        if token in syntax.line_comments:
            if token == "#" and syntax.php_attributes and text.startswith("#[", start):
                position = start + 2
                continue
            if token == "#" and syntax.hash_word_start and start > 0 \
                    and text[start - 1] not in " \t\n;|&(":
                position = start + 1
                continue
            end = _line_end(text, start)
            spans.append((start, end, "comment"))
            position = end
            continue

        if token in block_closers:
            if token == "=begin" and start > 0 and text[start - 1] != "\n":
                position = start + len(token)
                continue
            end = _block_end(text, start, token, block_closers[token], syntax.nested_blocks)
            spans.append((start, end, "comment"))
            position = end
            continue

        if syntax.heredoc and token in {"<<", "<<<", '@"', "@'"} and \
                (syntax.heredoc != "powershell" or token in {'@"', "@'"}):
            heredoc = _heredoc_span(text, start, syntax)
            if heredoc:
                spans.append((heredoc[0], heredoc[1], "heredoc"))
                position = heredoc[1]
                continue
            if token in {"<<", "<<<"}:
                position = start + len(token)
                continue

        if syntax.rust_raw and token.endswith('"') and token.lstrip("b").startswith("r"):
            hashes = _RUST_RAW.match(text, start).group(1)
            closer = '"' + hashes
            end = text.find(closer, match.end())
            end = len(text) if end < 0 else end + len(closer)
            spans.append((start, end, "string"))
            position = end
            continue

        if len(token) == 3 and token[0] == token[1] == token[2]:
            end = _triple_end(text, start, token)
            spans.append((start, end, "string"))
            position = end
            continue

        if syntax.verbatim_at and token in {'@"', '@$"', '$@"'}:
            end = _verbatim_end(text, start)
            spans.append((start, end, "string"))
            position = end
            continue

        if token == "`":
            end = _template_end(text, start) if syntax.template_backtick else (
                text.find("`", start + 1) + 1 or len(text))
            spans.append((start, end, "string"))
            position = end
            continue

        if token == "/":
            end = _regex_end(text, start) if _starts_regex(text, start, syntax.regex_keywords) else None
            if end is None:
                position = start + 1
                continue
            spans.append((start, end, "string"))
            position = end
            continue

        if token == "%":
            literal = _percent_span(text, start, syntax.regex_keywords)
            if literal is None:
                position = start + 1
                continue
            spans.append((literal[0], literal[1], "string"))
            position = literal[1]
            continue

        if token == "'" and syntax.char_quote and "'" not in syntax.quotes:
            literal = _CHAR_LITERAL.match(text, start)
            if literal is None:
                position = start + 1
                continue
            spans.append((start, literal.end(), "string"))
            position = literal.end()
            continue

        if token in syntax.quotes:
            end = _quoted_end(text, start, syntax)
            spans.append((start, end, "string"))
            position = max(end, start + 1)
            continue

        position = start + 1


def _blank(segment: str) -> str:
    if "\n" not in segment:
        return " " * len(segment)
    return "\n".join(" " * len(part) for part in segment.split("\n"))


def strip(text: str, language: str) -> Stripped:
    """text with comments and strings blanked, and with only comments blanked."""
    code_parts = []
    kept_parts = []
    last = 0
    for start, end, kind in _spans(text, language):
        plain = text[last:start]
        code_parts.append(plain)
        kept_parts.append(plain)
        segment = text[start:end]
        if kind == "string" and len(segment) >= 2:
            code_parts.append(segment[0] + _blank(segment[1:-1]) + segment[-1])
        else:
            code_parts.append(_blank(segment))
        kept_parts.append(_blank(segment) if kind == "comment" else segment)
        last = end
    code_parts.append(text[last:])
    kept_parts.append(text[last:])
    return Stripped("".join(code_parts), "".join(kept_parts))


def match_braces(code: str) -> dict:
    """Offset of every matched `{` mapped to the offset of its `}`."""
    pairs = {}
    stack = []
    for match in re.finditer(r"[{}]", code):
        if match.group() == "{":
            stack.append(match.start())
        elif stack:
            pairs[stack.pop()] = match.start()
    return pairs


def closing_paren(code: str, open_index: int) -> int:
    """Offset of the `)` matching the `(` at open_index, or -1."""
    depth = 0
    for index in range(open_index, len(code)):
        character = code[index]
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1
