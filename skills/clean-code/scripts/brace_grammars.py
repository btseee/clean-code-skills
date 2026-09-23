#!/usr/bin/env python3
"""Declaration grammars for the brace-delimited languages.

Each grammar tells symbols_braces what a declaration looks like in one language.
The engine never names a language; this module never walks a file.

Standard library only.
"""

from __future__ import annotations

import re
from pathlib import Path

import source_lexer
import symbol_model
import symbols_braces
from symbol_model import Symbol
from symbols_braces import Grammar, Pattern

C_DOC = ("//", "/*", "*")
HASH_DOC = ("#",)

# --- JavaScript and TypeScript --------------------------------------------------------

_JS_IDENT = r"[A-Za-z_$][\w$]*"
_JS_KEYWORDS = frozenset("""
if for while switch catch return function new await typeof super import export else do try
throw case default delete void yield with in of instanceof let const var class extends
""".split())


def _arrow_or_function(source, match) -> bool:
    """A `const x = (...)` declaration is a function only when an arrow follows."""
    token = match.group("start")
    if token.startswith("function") or token.endswith("=>"):
        return True
    code = source.code
    start = match.start("start")
    if token == "<":
        start = code.find("(", start)
        if start < 0:
            return False
    close = source_lexer.closing_paren(code, start)
    if close < 0:
        return False
    return bool(re.match(r"\s*(?::[^=;{]*?)?=>", code[close + 1:close + 240]))


def _js_exported(match, name, kind, is_member) -> bool:
    if is_member:
        return not name.startswith("#") and "private" not in (match.group("mods") or "")
    return "export" in (match.groupdict().get("mods") or "") or bool(match.groupdict().get("cjs"))


def _js_abstract(match, kind, body) -> bool:
    return kind == "interface" or "abstract" in (match.groupdict().get("mods") or "")


_EXPORT_LIST = re.compile(r"^[ \t]*export[ \t]*\{([^}]*)\}", re.M)
_EXPORT_DEFAULT = re.compile(rf"^[ \t]*export[ \t]+default[ \t]+({_JS_IDENT})[ \t]*;?[ \t]*$", re.M)
_CJS_OBJECT = re.compile(r"module\.exports[ \t]*=[ \t]*\{([^}]*)\}")
_CJS_SINGLE = re.compile(rf"module\.exports[ \t]*=[ \t]*({_JS_IDENT})[ \t]*;?[ \t]*$", re.M)
_IDENTIFIER = re.compile(rf"^{_JS_IDENT}$")


def _js_exported_names(code: str) -> set:
    names = set()
    for match in _EXPORT_LIST.finditer(code):
        for part in match.group(1).split(","):
            name = part.strip().split(" as ")[0].strip()
            if _IDENTIFIER.match(name):
                names.add(name)
    for match in _CJS_OBJECT.finditer(code):
        for part in match.group(1).split(","):
            value = part.split(":", 1)[-1].strip()
            if _IDENTIFIER.match(value):
                names.add(value)
    names.update(match.group(1) for match in _EXPORT_DEFAULT.finditer(code))
    names.update(match.group(1) for match in _CJS_SINGLE.finditer(code))
    return names


def _js_finish(symbols, source):
    exported = _js_exported_names(source.code)
    return [
        symbol._replace(exported=True)
        if symbol.parent is None and symbol.name in exported else symbol
        for symbol in symbols
    ]


def _js_grammar(language: str) -> Grammar:
    return Grammar(
        language=language,
        lexer=language,
        types=(
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?(?:default[ \t]+)?(?:declare[ \t]+)?"
                rf"(?:abstract[ \t]+)?)class[ \t]+(?P<name>{_JS_IDENT})", re.M), "class",
                container=True),
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?(?:declare[ \t]+)?)interface[ \t]+"
                rf"(?P<name>{_JS_IDENT})", re.M), "interface"),
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?(?:declare[ \t]+)?)type[ \t]+"
                rf"(?P<name>{_JS_IDENT})\b[^=\n;]*=", re.M), "type"),
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?(?:declare[ \t]+)?(?:const[ \t]+)?)enum[ \t]+"
                rf"(?P<name>{_JS_IDENT})", re.M), "enum"),
        ),
        functions=(
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?(?:default[ \t]+)?(?:async[ \t]+)?)function"
                rf"[ \t]*\*?[ \t]*(?P<name>{_JS_IDENT})[ \t]*[<(]", re.M), "function"),
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?)(?:const|let|var)[ \t]+(?P<name>{_JS_IDENT})"
                rf"[ \t]*(?::[^=\n]+)?=[ \t]*(?:async[ \t]+)?"
                rf"(?P<start>function\b|\(|<|{_JS_IDENT}[ \t]*=>)", re.M), "function",
                confirm=_arrow_or_function),
            Pattern(re.compile(
                rf"^[ \t]*(?P<cjs>(?:module\.)?exports)\.(?P<name>{_JS_IDENT})[ \t]*=[ \t]*"
                rf"(?:async[ \t]+)?(?P<start>function\b|\(|{_JS_IDENT}[ \t]*=>)", re.M),
                "function", confirm=_arrow_or_function),
            Pattern(re.compile(
                rf"^[ \t]*(?P<cjs>module\.exports)[ \t]*=[ \t]*(?:async[ \t]+)?function[ \t]*\*?"
                rf"[ \t]*(?P<name>{_JS_IDENT})", re.M), "function"),
        ),
        members=(
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:(?:public|private|protected|static|async|readonly|override|"
                rf"abstract|declare|get|set|accessor)[ \t]+)*)\*?[ \t]*(?P<name>#?{_JS_IDENT})"
                rf"[ \t]*(?:<[^>\n]*>)?[ \t]*\(", re.M), "method"),
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:(?:public|private|protected|static|readonly|override)[ \t]+)*)"
                rf"(?P<name>#?{_JS_IDENT})[ \t]*[?!]?[ \t]*(?::[^=\n]+)?=[ \t]*(?:async[ \t]+)?"
                rf"(?P<start>function\b|\(|{_JS_IDENT}[ \t]*=>)", re.M), "method",
                confirm=_arrow_or_function),
        ),
        transparent=re.compile(
            r"^[ \t]*(?:export[ \t]+)?(?:declare[ \t]+)?(?:namespace|module|global)\b[^{\n;]*\{",
            re.M),
        decorators=("@",),
        doc_markers=C_DOC,
        keywords=_JS_KEYWORDS,
        exported=_js_exported,
        abstract=_js_abstract,
        finish=_js_finish,
    )


JAVASCRIPT = _js_grammar("javascript")
TYPESCRIPT = _js_grammar("typescript")

# --- Single-file components (Vue, Svelte) -------------------------------------------

_SCRIPT_BLOCK = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
_TS_LANG = re.compile(r"""lang\s*=\s*["']ts""", re.I)


def extract_component(path: str, text: str, language: str) -> symbol_model.FileSymbols:
    """A .vue or .svelte file: the file itself is a component; its scripts hold functions."""
    padded = list(re.sub(r"[^\n]", " ", text))
    grammar = JAVASCRIPT
    for match in _SCRIPT_BLOCK.finditer(text):
        if _TS_LANG.search(match.group(1)):
            grammar = TYPESCRIPT
        start, end = match.span(2)
        padded[start:end] = text[start:end]
    inner = symbols_braces.extract(grammar, path, "".join(padded))
    component = Symbol(
        name=symbol_model.pascal_case(Path(path).stem),
        kind="component",
        line=1,
        end_line=max(1, inner.lines),
        exported=True,
        context=text.split("\n", 1)[0][:120],
    )
    return symbol_model.file_symbols(path, language, inner.purpose, text,
                                     [component] + list(inner.symbols))
