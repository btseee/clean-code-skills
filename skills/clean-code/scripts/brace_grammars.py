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

# Annotations or decorators written on the declaration's own line: `@Override public`,
# `@HostListener('resize') onResize(`.
_ANNOTATIONS = r"(?:@[\w.]+(?:\((?:[^()\n]|\([^()\n]*\))*\))?[ \t]+)*"

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
        # No two runs of spaces may meet with only optional parts between them: the lexer
        # blanks comments and strings into long space runs, and every split of such a run
        # between two `[ \t]*` is a way to backtrack. So `(?:[ \t]*\*)?[ \t]*`, never
        # `[ \t]*\*?[ \t]*`.
        functions=(
            Pattern(re.compile(
                rf"^[ \t]*(?P<mods>(?:export[ \t]+)?(?:default[ \t]+)?(?:async[ \t]+)?)function"
                rf"(?:[ \t]*\*)?[ \t]*(?P<name>{_JS_IDENT})[ \t]*[<(]", re.M), "function"),
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
                rf"^[ \t]*(?P<cjs>module\.exports)[ \t]*=[ \t]*(?:async[ \t]+)?function"
                rf"(?:[ \t]*\*)?[ \t]*(?P<name>{_JS_IDENT})", re.M), "function"),
        ),
        members=(
            Pattern(re.compile(
                rf"^[ \t]*{_ANNOTATIONS}(?P<mods>(?:(?:public|private|protected|static|async|readonly|"
                rf"override|abstract|declare|get|set|accessor)[ \t]+)*)(?:\*[ \t]*)?"
                rf"(?P<name>#?{_JS_IDENT})(?:[ \t]*<[^>\n]*>)?[ \t]*\(", re.M), "method"),
            Pattern(re.compile(
                rf"^[ \t]*{_ANNOTATIONS}(?P<mods>(?:(?:public|private|protected|static|readonly|"
                rf"override)[ \t]+)*)(?P<name>#?{_JS_IDENT})(?:[ \t]*[?!])?[ \t]*(?::[^=\n]+)?=[ \t]*"
                rf"(?:async[ \t]+)?(?P<start>function\b|\(|{_JS_IDENT}[ \t]*=>)", re.M), "method",
                confirm=_arrow_or_function),
        ),
        # A namespace needs a name, so `module.exports = function (app) {` is a function.
        transparent=re.compile(
            r"^[ \t]*(?:export[ \t]+)?(?:declare[ \t]+)?(?:namespace|module)[ \t]+"
            r"(?:[\w.$]+|'[^'\n]*'|\"[^\"\n]*\")[ \t]*\{|^[ \t]*(?:declare[ \t]+)?global[ \t]*\{",
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


# --- JVM languages, C#, PHP, Dart ------------------------------------------------------

_WORD = r"[A-Za-z_]\w*"

# One declared type: a dotted name with optional generic arguments, array brackets, and
# a nullable or pointer marker, or a parenthesised tuple. Each part is unambiguous, so a
# line that is not a declaration fails fast instead of backtracking through it.
_TYPE = (r"(?:\((?:[^()\n]|\([^()\n]*\))*\)|[\w.]+(?:<[^;{}()\n]*?>)?(?:\[[, ]*\])*[?*]?)")


def _mods(match) -> str:
    return match.groupdict().get("mods") or ""


def _has(match, *words) -> bool:
    mods = _mods(match).split()
    return any(word in mods for word in words)


def _pattern(regex: str, kind: str, **options) -> Pattern:
    return Pattern(re.compile(regex, re.M), kind, **options)


_JVM_KEYWORDS = frozenset("""
if for while switch catch return new throw else do try synchronized assert super this
when is in as typeof yield await
""".split())

# A capitalized name with a lowercase letter after the first. The lookahead checks for
# the lowercase letter once; `[A-Z]\w*[a-z]\w*` tried every split of a long name.
_CONSTRUCTOR_NAME = r"[A-Z](?=\w*[a-z])\w*"

JAVA = Grammar(
    language="java",
    lexer="java",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|protected|private|abstract|final|static|sealed|"
                 rf"non-sealed|strictfp)[ \t]+)*)(?P<kind>class|interface|enum|record|@interface)"
                 rf"[ \t]+(?P<name>{_WORD})", "class", container=True),
    ),
    functions=(),
    members=(
        _pattern(rf"^[ \t]*{_ANNOTATIONS}(?P<mods>(?:(?:public|protected|private|abstract|final|static|"
                 rf"synchronized|native|default|strictfp)[ \t]+)*)(?:<[^>\n]+>[ \t]+)?"
                 rf"{_TYPE}[ \t]+(?P<name>[a-zA-Z_]\w*)[ \t]*\(", "method"),
        _pattern(rf"^[ \t]*{_ANNOTATIONS}(?P<mods>(?:(?:public|protected|private)[ \t]+)?)"
                 rf"(?P<name>{_CONSTRUCTOR_NAME})[ \t]*\(", "method"),
    ),
    transparent=None,
    decorators=("@",),
    doc_markers=C_DOC,
    keywords=_JVM_KEYWORDS,
    exported=lambda match, name, kind, member: (
        not _has(match, "private") if member else _has(match, "public")),
    abstract=lambda match, kind, body: kind == "interface" or _has(match, "abstract"),
)

KOTLIN = Grammar(
    language="kotlin",
    lexer="kotlin",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|private|internal|protected|open|abstract|sealed|"
                 rf"data|inner|value|inline|expect|actual)[ \t]+)*)(?P<kind>enum[ \t]+class|"
                 rf"annotation[ \t]+class|fun[ \t]+interface|class|interface|object)[ \t]+"
                 rf"(?P<name>{_WORD})", "class", container=True),
    ),
    functions=(
        _pattern(rf"^[ \t]*{_ANNOTATIONS}(?P<mods>(?:(?:public|private|internal|protected|open|"
                 rf"abstract|override|suspend|inline|operator|infix|tailrec|external|actual|expect|"
                 rf"final)[ \t]+)*)fun[ \t]+(?:<[^>\n]+>[ \t]*)?(?:[\w<>?][\w.<>?, ]*\.)?"
                 rf"(?P<name>{_WORD})[ \t]*\(", "function"),
    ),
    members=(),
    transparent=None,
    decorators=("@",),
    doc_markers=C_DOC,
    keywords=_JVM_KEYWORDS,
    exported=lambda match, name, kind, member: not _has(match, "private"),
    abstract=lambda match, kind, body: kind == "interface" or _has(match, "abstract", "sealed"),
)

SCALA = Grammar(
    language="scala",
    lexer="scala",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:private|protected|final|sealed|abstract|implicit|lazy|"
                 rf"case|override|open)(?:\[[^\]\n]*\])?[ \t]+)*)(?P<kind>class|trait|object|enum)"
                 rf"[ \t]+(?P<name>{_WORD})", "class", container=True),
    ),
    functions=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:private|protected|final|override|implicit|inline|"
                 rf"transparent|lazy)(?:\[[^\]\n]*\])?[ \t]+)*)def[ \t]+(?P<name>{_WORD})",
                 "function"),
    ),
    members=(),
    transparent=None,
    decorators=("@",),
    doc_markers=C_DOC,
    keywords=_JVM_KEYWORDS,
    exported=lambda match, name, kind, member: not _has(match, "private"),
    abstract=lambda match, kind, body: kind == "trait" or _has(match, "abstract"),
    indent_blocks=True,
)

# Attributes written on the member's own line: `[HttpGet("{id}")] public async Task Get(`.
_CSHARP_ATTRIBUTES = r"(?:\[[^\]\n]*\][ \t]*)*"

CSHARP = Grammar(
    language="csharp",
    lexer="csharp",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|private|protected|internal|static|abstract|sealed|"
                 rf"partial|readonly|ref|unsafe|file|new)[ \t]+)*)(?P<kind>record[ \t]+struct|"
                 rf"record[ \t]+class|record|class|interface|struct|enum)[ \t]+(?P<name>{_WORD})",
                 "class", container=True),
    ),
    functions=(),
    members=(
        _pattern(rf"^[ \t]*{_CSHARP_ATTRIBUTES}(?P<mods>(?:(?:public|private|protected|internal|static|"
                 rf"virtual|override|abstract|sealed|async|extern|unsafe|new|partial|readonly)[ \t]+)*)"
                 rf"{_TYPE}[ \t]+(?P<name>{_WORD})(?:[ \t]*<[^>\n]*>)?[ \t]*\(",
                 "method"),
        _pattern(rf"^[ \t]*{_CSHARP_ATTRIBUTES}(?P<mods>(?:(?:public|private|protected|internal|"
                 rf"static)[ \t]+)*)(?P<name>{_CONSTRUCTOR_NAME})[ \t]*\(", "method"),
    ),
    transparent=re.compile(r"^[ \t]*namespace[ \t]+[\w.]+[ \t\r\n]*\{", re.M),
    decorators=("[",),
    doc_markers=C_DOC,
    keywords=_JVM_KEYWORDS | {"using", "lock", "foreach", "fixed", "checked", "unchecked", "nameof"},
    exported=lambda match, name, kind, member: (
        _has(match, "public", "internal", "protected") if member
        else not _has(match, "private", "file")),
    abstract=lambda match, kind, body: kind == "interface" or _has(match, "abstract"),
)

PHP = Grammar(
    language="php",
    lexer="php",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:abstract|final|readonly)[ \t]+)*)"
                 rf"(?P<kind>class|interface|trait|enum)[ \t]+(?P<name>{_WORD})", "class",
                 container=True),
    ),
    functions=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|protected|private|static|abstract|final)[ \t]+)*)"
                 rf"function[ \t]+(?:&[ \t]*)?(?P<name>{_WORD})[ \t]*\(", "function"),
    ),
    members=(),
    transparent=re.compile(r"^[ \t]*namespace[ \t]+[\w\\]+[ \t\r\n]*\{", re.M),
    decorators=("#[",),
    doc_markers=C_DOC,
    keywords=frozenset({"if", "for", "foreach", "while", "switch", "catch", "return", "new",
                        "fn", "match", "echo", "print", "isset", "unset", "empty", "list"}),
    exported=lambda match, name, kind, member: not _has(match, "private", "protected"),
    abstract=lambda match, kind, body: kind == "interface" or _has(match, "abstract"),
)

def _outside_brackets(source, match) -> bool:
    """Dart needs no keyword before a function, so `GoRoute(` inside `routes: [` or a
    widget list would read as one. A declaration never sits inside an argument list."""
    return source.bracket_depth_before(match.start()) == 0


DART = Grammar(
    language="dart",
    lexer="dart",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:abstract|base|final|interface|sealed)[ \t]+)*)"
                 rf"(?P<kind>mixin[ \t]+class|class|mixin|enum)[ \t]+(?P<name>{_WORD})", "class",
                 container=True),
        _pattern(rf"^[ \t]*extension[ \t]+(?P<name>{_WORD})", "class", container=True, emit=False),
    ),
    functions=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:static|external|factory|abstract|const|late|covariant)"
                 rf"[ \t]+)*)(?:{_TYPE}[ \t]+)?(?P<name>{_WORD})"
                 rf"(?:\.{_WORD})?(?:[ \t]*<[^>\n]*>)?[ \t]*\(", "function",
                 confirm=_outside_brackets),
    ),
    members=(),
    transparent=None,
    decorators=("@",),
    doc_markers=C_DOC,
    keywords=frozenset({"if", "for", "while", "switch", "catch", "return", "assert", "super",
                        "this", "new", "throw", "await", "yield", "else", "do", "try",
                        "rethrow", "get", "set", "import", "export", "part", "library"}),
    exported=lambda match, name, kind, member: not name.startswith("_"),
    abstract=lambda match, kind, body: _has(match, "abstract", "interface", "sealed"),
)


# --- Go, Rust, Swift ------------------------------------------------------------------

_PACKAGE_LINE = re.compile(r"^package[ \t]+\w+", re.M)


def _go_purpose(source) -> str:
    """Go documents a package in the comment directly above its `package` clause."""
    match = _PACKAGE_LINE.search(source.code)
    if match is None:
        return ""
    index = source.line_of(match.start()) - 1
    return symbol_model.doc_above(source.raw_lines, index, C_DOC)


GO = Grammar(
    language="go",
    lexer="go",
    types=(
        _pattern(rf"^[ \t]*(?:type[ \t]+)?(?P<name>{_WORD})(?:\[[^\]\n]*\])?[ \t]+"
                 rf"(?P<kind>struct|interface)\b", "struct"),
        _pattern(rf"^type[ \t]+(?P<name>{_WORD})(?:\[[^\]\n]*\])?[ \t]+(?!struct\b|interface\b)"
                 rf"[\w*\[\].]", "type"),
    ),
    functions=(
        _pattern(rf"^func[ \t]+(?P<name>{_WORD})[ \t]*[\[(]", "function"),
        _pattern(rf"^func[ \t]*\([ \t]*(?:\w+[ \t]+)?(?:\*[ \t]*)?(?P<parent>{_WORD})"
                 rf"(?:\[[^\]\n]*\])?[ \t]*\)[ \t]*(?P<name>{_WORD})[ \t]*[\[(]", "method"),
    ),
    members=(),
    transparent=None,
    decorators=(),
    doc_markers=C_DOC,
    keywords=frozenset({"type", "var", "const", "func", "return", "if", "for", "switch",
                        "select", "go", "defer", "package", "import", "map", "chan"}),
    exported=lambda match, name, kind, member: name[:1].isupper(),
    abstract=lambda match, kind, body: kind == "interface",
    purpose=_go_purpose,
    type_literal=re.compile(r"\b(?:interface|struct)[ \t]*$"),
)

_RUST_VISIBILITY = r"(?:pub(?:\([^)\n]*\))?[ \t]+)?"
# One word of an impl header, such as `fmt::Display`, `Vec<T>`, or `From<&'a`. Words are
# separated by spaces, never contain them, so a header splits only one way.
_RUST_HEADER_WORD = r"[\w:<>,'&]+"

RUST = Grammar(
    language="rust",
    lexer="rust",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>{_RUST_VISIBILITY}(?:unsafe[ \t]+)?)"
                 rf"(?P<kind>struct|enum|trait|union|type)[ \t]+(?P<name>{_WORD})", "struct",
                 container=True),
        _pattern(rf"^[ \t]*(?:unsafe[ \t]+)?impl(?:[ \t]*<(?:[^<>\n]|<[^<>\n]*>)*>)?[ \t]+"
                 rf"(?:{_RUST_HEADER_WORD}(?:[ \t]+{_RUST_HEADER_WORD})*?[ \t]+for[ \t]+)?"
                 rf"(?P<name>{_WORD})", "struct", container=True, emit=False),
    ),
    functions=(
        _pattern(rf"^[ \t]*(?P<mods>{_RUST_VISIBILITY}(?:(?:const|async|unsafe|extern"
                 r'(?:[ \t]+"[^"\n]*")?)[ \t]+)*)' rf"fn[ \t]+(?P<name>{_WORD})", "function"),
    ),
    members=(),
    transparent=re.compile(rf"^[ \t]*{_RUST_VISIBILITY}mod[ \t]+\w+[ \t]*\{{", re.M),
    decorators=("#[",),
    doc_markers=C_DOC,
    keywords=frozenset({"fn", "struct", "enum", "trait", "impl", "type", "mod", "use"}),
    exported=lambda match, name, kind, member: "pub" in _mods(match),
    abstract=lambda match, kind, body: kind == "trait",
    skip=re.compile(rf"^[ \t]*(?:#\[cfg\(test\)\][ \t\r\n]*{_RUST_VISIBILITY}mod[ \t]+\w+|"
                    rf"{_RUST_VISIBILITY}mod[ \t]+tests?)[ \t]*\{{", re.M),
)

_SWIFT_ATTRIBUTE = r"@\w+(?:\([^)\n]*\))?"
_SWIFT_MODS = (r"(?:(?:public|private|fileprivate|internal|open|final|static|class|override|"
               r"mutating|nonmutating|required|convenience|indirect|nonisolated|"
               + _SWIFT_ATTRIBUTE + r")[ \t]+)*")

SWIFT = Grammar(
    language="swift",
    lexer="swift",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>{_SWIFT_MODS})(?P<kind>class|struct|enum|protocol|actor)"
                 rf"[ \t]+(?P<name>{_WORD})", "class", container=True),
        _pattern(rf"^[ \t]*(?:(?:public|private|fileprivate|internal)[ \t]+)?extension[ \t]+"
                 rf"(?P<name>{_WORD})", "class", container=True, emit=False),
    ),
    functions=(
        _pattern(rf"^[ \t]*(?P<mods>{_SWIFT_MODS})func[ \t]+(?P<name>{_WORD})", "function"),
    ),
    members=(
        _pattern(rf"^[ \t]*(?P<mods>{_SWIFT_MODS})(?P<name>init)[?!]?[ \t]*[<(]", "method"),
    ),
    transparent=None,
    decorators=("@",),
    doc_markers=C_DOC,
    keywords=frozenset({"func", "var", "let", "if", "for", "while", "switch", "return",
                        "guard", "case", "import"}),
    exported=lambda match, name, kind, member: not _has(match, "private", "fileprivate"),
    abstract=lambda match, kind, body: kind == "protocol",
)

# --- C, C++, Objective-C ----------------------------------------------------------------

_C_KEYWORDS = frozenset({"if", "for", "while", "switch", "return", "sizeof", "else", "do",
                         "case", "typedef", "struct", "union", "enum", "defined", "catch",
                         "alignof", "decltype", "static_assert", "operator", "new", "delete"})
# One word of a return type. `::` joins names, but a lone `:` ends them, so an access
# label (`public:`) is never read as the return type of the member below it.
_C_TYPE_WORD = r"[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*(?:<[^;{}()\n]*?>)?"
# The words before a function's name: on its line, and on at most one line above, where
# GNU style puts the return type. Across any number of lines, a run of one-word lines was
# read again from every line start: quadratic.
_C_RETURN_TYPE = (rf"(?:(?:{_C_TYPE_WORD}[ \t*&]+)*{_C_TYPE_WORD}[ \t*&]*\r?\n[ \t*&]*)?"
                  rf"(?:{_C_TYPE_WORD}[ \t*&]+)*")
# A parenthesised list, nested up to three deep, which may hold `{...}` (a default `= {}`,
# an initializer `x_({n})`). It is balanced, so it matches one way only: `\([^;{}]*\)`
# could end at any `)`, and in a run of macro calls the engine tried each one --
# quadratic, cubic with a qualifier part after it. It also let `__attribute__((noinline))`
# swallow the definition on the next line.
_C_ATOM = r"(?:[^;{}()]|\{[^;{}()]*\})"
_C_PARAMS = rf"\((?:{_C_ATOM}|\((?:{_C_ATOM}|\({_C_ATOM}*\))*\))*\)"
_C_ATTRIBUTE = (r"(?:__attribute__[ \t]*\(\((?:[^()\n]|\([^()\n]*\))*\)\)|__declspec[ \t]*\([^()\n]*\)"
                r"|\[\[[^\]\n]*\]\])")
# A line holding only an all-caps macro call, as `NUMBA_EXPORT_FUNC(double)` or
# `DLLEXPORT(void)` above the name it declares: the doc comment sits above the macro.
_EXPORT_MACRO_LINE = re.compile(r"[A-Z_][A-Z0-9_]*[ \t]*\([^()\n]*\)$")
_C_DECORATORS = ("__attribute__", "__declspec", "[[", _EXPORT_MACRO_LINE)


def _c_mods(keywords: str) -> str:
    """Leading modifiers. A keyword may end its line, as GNU style's `static` above the
    return type does, but only one line break is crossed: from every line of a run of
    keyword-only lines, `\\s+` re-read the rest of the run. An attribute on its own line
    is a decorator instead."""
    one_line = rf"(?:(?:{keywords})[ \t]+|{_C_ATTRIBUTE}[ \t]+)*"
    return rf"(?P<mods>{one_line}(?:(?:{keywords})[ \t]*\r?\n{one_line})?)"


_C_TYPE = _pattern(rf"^[ \t]*(?:typedef[ \t]+)?(?P<kind>struct|union|enum)[ \t]+(?P<name>{_WORD})"
                   rf"(?=[ \t\r\n]*\{{)", "struct")
_C_FUNCTION = _pattern(
    rf"^{_c_mods('static|inline|extern|const|unsigned|signed|volatile|register')}"
    rf"{_C_RETURN_TYPE}(?P<name>{_WORD})[ \t]*{_C_PARAMS}(?=[ \t\r\n]*\{{)", "function",
    require_body=True)
_EXTERN_C = r'extern[ \t]+"[^"\n]*"'

# Between a C++ parameter list and its body: `const`, `noexcept(false)`, `-> decltype(x)`,
# and a constructor's initializers `: x_(x), y_{y}`. It continues onto indented lines only,
# so a run of column-0 macro calls never reads as one declaration. Spaces are matched one
# at a time, never as a run, so no run of them can be split two ways.
_CPP_GAP = r"(?:[ \t]|\r?\n(?=[ \t]))*"
_CPP_BRACED = r"\{(?:[^;{}]|\{[^;{}]*\})*\}"
_CPP_TRAILER = rf"(?:{_CPP_GAP}(?:[^;{{}}()\s]|{_C_PARAMS}|{_CPP_BRACED}))*?"
# A free function takes a parenthesised part only after its keyword, so the `MACRO(x)` in
# `MACRO(x) f(y) {` is not read as a function whose qualifiers are `f(y)`.
_CPP_KEYWORD_ARGS = rf"(?:noexcept|throw|decltype|requires|__attribute__)[ \t]*{_C_PARAMS}"
_CPP_FREE_TRAILER = rf"(?:{_CPP_GAP}(?:::|{_CPP_KEYWORD_ARGS}|[^;{{}}():\s]))*?"
# The body's `{`, not an initializer's: `y_{y}` touches a name.
_CPP_BODY = r"(?:(?<!\w)|(?=\s))(?=\s*\{)"
# The initializers of a constructor declared in its class, which the member pattern
# consumes so that `x_(x),` on a later line is not read as a method.
_CPP_INITIALIZER = rf"[\w:]+(?:<[^;{{}}()\n]*>)?(?:{_C_PARAMS}|{_CPP_BRACED})"
_CPP_INITIALIZERS = (rf"(?:{_CPP_GAP}:{_CPP_GAP}{_CPP_INITIALIZER}"
                     rf"(?:{_CPP_GAP},{_CPP_GAP}{_CPP_INITIALIZER})*)?")
_LIST_CONTINUES = re.compile(r"(?:,|\)\s*:)\s*$")
# What may stand between `class` and its name: an export macro (`MYLIB_API`,
# `Q_CORE_EXPORT`), `__declspec(dllexport)`, `alignas(16)`, or an attribute.
_CPP_CLASS_PREFIX = rf"(?:[A-Z_][A-Z0-9_]*|alignas\([^)\n]*\)|{_C_ATTRIBUTE})"


def _starts_declaration(source, match) -> bool:
    """False for a line that continues a list, as an unparsed `x_(x),` initializer does."""
    line_start = source.code.rfind("\n", 0, match.start("name")) + 1
    return not _LIST_CONTINUES.search(source.code, max(0, line_start - 200), line_start)


def _c_exported(match, name, kind, member) -> bool:
    return member or "static" not in _mods(match).split()


C = Grammar(
    language="c",
    lexer="c",
    types=(_C_TYPE,),
    functions=(_C_FUNCTION,),
    members=(),
    transparent=re.compile(rf"^[ \t]*{_EXTERN_C}[ \t\r\n]*\{{", re.M),
    decorators=_C_DECORATORS,
    doc_markers=C_DOC,
    keywords=_C_KEYWORDS,
    exported=_c_exported,
    abstract=lambda match, kind, body: False,
)

_PURE_VIRTUAL = re.compile(r"=\s*0\s*;")

CPP = Grammar(
    language="cpp",
    lexer="cpp",
    types=(
        _pattern(rf"^[ \t]*(?:template[ \t]*<[^>\n]*>[ \t\r\n]*)?(?P<kind>class|struct|union)"
                 rf"[ \t]+(?:{_CPP_CLASS_PREFIX}[ \t]+)*(?P<name>{_WORD})(?:[ \t]+final)?"
                 rf"(?:[ \t]*:(?:[ \t\r\n]*[^;{{\s])*)?(?=[ \t\r\n]*\{{)", "class", container=True),
        _pattern(rf"^[ \t]*enum[ \t]+(?:class[ \t]+|struct[ \t]+)?(?P<name>{_WORD})"
                 rf"(?:[ \t]*[^;{{\s])*(?=[ \t\r\n]*\{{)", "enum"),
    ),
    functions=(
        _pattern(rf"^{_c_mods('static|inline|extern|constexpr|consteval|virtual')}{_C_RETURN_TYPE}"
                 rf"(?P<parent>{_WORD})(?:<[^>\n]*>)?::(?P<name>~?{_WORD})"
                 rf"[ \t]*{_C_PARAMS}{_CPP_TRAILER}{_CPP_BODY}", "method", require_body=True),
        _pattern(rf"^{_c_mods('static|inline|extern|constexpr|consteval')}{_C_RETURN_TYPE}"
                 rf"(?P<name>{_WORD})[ \t]*{_C_PARAMS}{_CPP_FREE_TRAILER}"
                 rf"(?=[ \t\r\n]*\{{)", "function", require_body=True),
    ),
    members=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:virtual|static|inline|explicit|constexpr|consteval|"
                 rf"friend)[ \t]+)*){_C_RETURN_TYPE}(?P<name>~?{_WORD})[ \t]*{_C_PARAMS}"
                 rf"{_CPP_INITIALIZERS}", "method", confirm=_starts_declaration),
    ),
    transparent=re.compile(rf"^[ \t]*(?:(?:inline[ \t]+)?namespace(?:[ \t]+[\w:]+)?|{_EXTERN_C})"
                           rf"[ \t\r\n]*\{{", re.M),
    decorators=("template",) + _C_DECORATORS,
    doc_markers=C_DOC,
    keywords=_C_KEYWORDS | {"public", "private", "protected", "class", "namespace", "template"},
    exported=_c_exported,
    abstract=lambda match, kind, body: bool(_PURE_VIRTUAL.search(body)),
)

_OBJC_REGION = re.compile(r"^@(?P<kind>interface|implementation|protocol)[ \t]+(?P<name>\w+)"
                          r"(?P<rest>[^\n]*)", re.M)
_OBJC_END = re.compile(r"^@end\b", re.M)


def _objc_regions(source) -> list:
    """`@interface`, `@implementation`, and `@protocol` bodies end at `@end`, not a brace."""
    regions = []
    for match in _OBJC_REGION.finditer(source.code):
        if match.group("rest").strip().startswith((";", ",")):
            continue
        end = _OBJC_END.search(source.code, match.end())
        if end is not None:
            regions.append(symbols_braces.Container(
                match.end(), end.start(), match.group("name"), symbols_braces.REGION))
    return regions


OBJC = Grammar(
    language="objc",
    lexer="objc",
    types=(
        _pattern(rf"^@interface[ \t]+(?P<name>{_WORD})(?![ \t]*\()", "class"),
        _pattern(rf"^@protocol[ \t]+(?P<name>{_WORD})(?![ \t]*[;,])", "protocol"),
        _C_TYPE,
    ),
    functions=(_C_FUNCTION,),
    members=(
        _pattern(rf"^[ \t]*(?P<mods>[-+])[ \t]*\([^)\n]*\)[ \t]*(?P<name>{_WORD})", "method"),
    ),
    transparent=None,
    decorators=_C_DECORATORS,
    doc_markers=C_DOC,
    keywords=_C_KEYWORDS,
    exported=lambda match, name, kind, member: True,
    abstract=lambda match, kind, body: kind == "protocol",
    regions=_objc_regions,
)


# --- Shell, PowerShell, R ------------------------------------------------------------------

SHELL = Grammar(
    language="shell",
    lexer="shell",
    types=(),
    functions=(
        _pattern(r"^[ \t]*(?:function[ \t]+)?(?P<name>[A-Za-z_][\w:.-]*)[ \t]*\(\)", "function"),
        _pattern(r"^[ \t]*function[ \t]+(?P<name>[A-Za-z_][\w:.-]*)[ \t]*(?=\{|$)", "function"),
    ),
    members=(),
    transparent=None,
    decorators=(),
    doc_markers=HASH_DOC,
    keywords=frozenset({"if", "then", "else", "elif", "fi", "for", "while", "until", "do",
                        "done", "case", "esac", "function", "select", "time"}),
    exported=lambda match, name, kind, member: True,
    abstract=lambda match, kind, body: False,
)

_SYNOPSIS = re.compile(r"^\s*\.SYNOPSIS\s*$", re.I)


def _powershell_finish(symbols, source):
    """Comment-based help: the line after `.SYNOPSIS`, inside or just above a function."""
    lines = source.raw_lines
    documented = []
    for symbol in symbols:
        if symbol.doc or symbol.kind not in {"function", "method"}:
            documented.append(symbol)
            continue
        doc = ""
        for index in range(max(0, symbol.line - 15), min(symbol.end_line, len(lines))):
            if _SYNOPSIS.match(lines[index]):
                for follow in lines[index + 1:index + 6]:
                    text = follow.strip()
                    if text and not text.startswith((".", "#>")):
                        doc = symbol_model.first_sentence(text)
                        break
                break
        documented.append(symbol._replace(doc=doc))
    return documented


POWERSHELL = Grammar(
    language="powershell",
    lexer="powershell",
    types=(
        _pattern(rf"^[ \t]*(?i:(?P<kind>class|enum))[ \t]+(?P<name>{_WORD})", "class",
                 container=True),
    ),
    functions=(
        _pattern(r"^[ \t]*(?i:function|filter|workflow)[ \t]+(?:(?i:global|script|private):)?"
                 r"(?P<name>[A-Za-z_][\w-]*)", "function"),
    ),
    members=(
        _pattern(rf"^[ \t]*(?:(?i:hidden|static)[ \t]+)*(?:\[[^\]\n]+\][ \t]*)?(?P<name>{_WORD})"
                 rf"[ \t]*\(", "method"),
    ),
    transparent=None,
    decorators=("[",),
    doc_markers=HASH_DOC,
    keywords=frozenset({"if", "else", "elseif", "foreach", "for", "while", "switch", "return",
                        "param", "begin", "process", "end", "try", "catch", "finally",
                        "trap", "throw", "do", "until"}),
    exported=lambda match, name, kind, member: True,
    abstract=lambda match, kind, body: False,
    finish=_powershell_finish,
)

R = Grammar(
    language="r",
    lexer="r",
    types=(
        _pattern(r"""^[ \t]*(?:[\w.]+[ \t]*(?:<-|=)[ \t]*)?(?:methods::)?set(?:Ref)?Class\([ \t]*"""
                 r"""["'](?P<name>[\w.]+)["']""", "class", on_raw=True),
        _pattern(r"^[ \t]*(?P<name>[\w.]+)[ \t]*(?:<-|=)[ \t]*(?:R6::)?R6Class\(", "class"),
    ),
    functions=(
        _pattern(r"^[ \t]*(?P<name>[A-Za-z.][\w.]*)[ \t]*(?:<-|=)[ \t]*function[ \t]*\(",
                 "function"),
    ),
    members=(),
    transparent=None,
    decorators=(),
    doc_markers=HASH_DOC,
    keywords=frozenset({"if", "else", "for", "while", "repeat", "function", "return"}),
    exported=lambda match, name, kind, member: not name.startswith("."),
    abstract=lambda match, kind, body: False,
)
