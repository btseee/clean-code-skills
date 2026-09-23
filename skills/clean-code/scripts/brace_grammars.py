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


# --- JVM languages, C#, PHP, Dart ------------------------------------------------------

_WORD = r"[A-Za-z_]\w*"


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
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|protected|private|abstract|final|static|"
                 rf"synchronized|native|default|strictfp)[ \t]+)*)(?:<[^>\n]+>[ \t]+)?"
                 rf"[\w<>\[\],.? ]*?[\w>\]][ \t]+(?P<name>[a-zA-Z_]\w*)[ \t]*\(", "method"),
        _pattern(r"^[ \t]*(?P<mods>(?:(?:public|protected|private)[ \t]+)?)"
                 r"(?P<name>[A-Z]\w*[a-z]\w*)[ \t]*\(", "method"),
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
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|private|internal|protected|open|abstract|override|"
                 rf"suspend|inline|operator|infix|tailrec|external|actual|expect|final)[ \t]+)*)"
                 rf"fun[ \t]+(?:<[^>\n]+>[ \t]*)?(?:[\w.<>?, ]+\.)?(?P<name>{_WORD})[ \t]*\(",
                 "function"),
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
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:public|private|protected|internal|static|virtual|override|"
                 rf"abstract|sealed|async|extern|unsafe|new|partial|readonly)[ \t]+)*)"
                 rf"[\w<>\[\],.?() ]*?[\w>\]?)][ \t]+(?P<name>{_WORD})[ \t]*(?:<[^>\n]*>)?[ \t]*\(",
                 "method"),
        _pattern(r"^[ \t]*(?P<mods>(?:(?:public|private|protected|internal|static)[ \t]+)*)"
                 r"(?P<name>[A-Z]\w*[a-z]\w*)[ \t]*\(", "method"),
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
                 rf"function[ \t]+&?[ \t]*(?P<name>{_WORD})[ \t]*\(", "function"),
    ),
    members=(),
    transparent=re.compile(r"^[ \t]*namespace[ \t]+[\w\]+[ \t\r\n]*\{", re.M),
    decorators=("#[",),
    doc_markers=C_DOC,
    keywords=frozenset({"if", "for", "foreach", "while", "switch", "catch", "return", "new",
                        "fn", "match", "echo", "print", "isset", "unset", "empty", "list"}),
    exported=lambda match, name, kind, member: not _has(match, "private", "protected"),
    abstract=lambda match, kind, body: kind == "interface" or _has(match, "abstract"),
)

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
                 rf"[ \t]+)*)(?:[\w<>?,\[\]. ]*?[\w>?\]][ \t]+)?(?P<name>{_WORD})"
                 rf"(?:\.{_WORD})?[ \t]*(?:<[^>\n]*>)?[ \t]*\(", "function"),
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
        _pattern(rf"^func[ \t]*\([ \t]*(?:\w+[ \t]+)?\*?[ \t]*(?P<parent>{_WORD})(?:\[[^\]\n]*\])?"
                 rf"[ \t]*\)[ \t]*(?P<name>{_WORD})[ \t]*[\[(]", "method"),
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
)

_RUST_VISIBILITY = r"(?:pub(?:\([^)\n]*\))?[ \t]+)?"

RUST = Grammar(
    language="rust",
    lexer="rust",
    types=(
        _pattern(rf"^[ \t]*(?P<mods>{_RUST_VISIBILITY}(?:unsafe[ \t]+)?)"
                 rf"(?P<kind>struct|enum|trait|union|type)[ \t]+(?P<name>{_WORD})", "struct",
                 container=True),
        _pattern(rf"^[ \t]*(?:unsafe[ \t]+)?impl(?:[ \t]*<[^>\n]*>)?[ \t]+"
                 rf"(?:[\w:<>, ]+?[ \t]+for[ \t]+)?(?P<name>{_WORD})", "struct",
                 container=True, emit=False),
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
_C_RETURN_TYPE = r"(?:[A-Za-z_][\w \t\*&:<>,]*?[\s\*&]+)?"
_C_TYPE = _pattern(rf"^[ \t]*(?:typedef[ \t]+)?(?P<kind>struct|union|enum)[ \t]+(?P<name>{_WORD})"
                   rf"(?=[ \t\r\n]*\{{)", "struct")
_C_FUNCTION = _pattern(
    rf"^(?P<mods>(?:(?:static|inline|extern|const|unsigned|signed|volatile|register)[ \t]+)*)"
    rf"{_C_RETURN_TYPE}(?P<name>{_WORD})[ \t]*\([^;{{}}]*\)(?=[ \t\r\n]*\{{)", "function",
    require_body=True)
_EXTERN_C = r'extern[ \t]+"[^"\n]*"'


def _c_exported(match, name, kind, member) -> bool:
    return member or "static" not in _mods(match).split()


C = Grammar(
    language="c",
    lexer="c",
    types=(_C_TYPE,),
    functions=(_C_FUNCTION,),
    members=(),
    transparent=re.compile(rf"^[ \t]*{_EXTERN_C}[ \t\r\n]*\{{", re.M),
    decorators=(),
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
                 rf"[ \t]+(?:alignas\([^)\n]*\)[ \t]+)?(?P<name>{_WORD})(?:[ \t]+final)?[ \t]*"
                 rf"(?::[^;{{]*)?(?=[ \t\r\n]*\{{)", "class", container=True),
        _pattern(rf"^[ \t]*enum[ \t]+(?:class[ \t]+|struct[ \t]+)?(?P<name>{_WORD})[^;{{\n]*"
                 rf"(?=[ \t\r\n]*\{{)", "enum"),
    ),
    functions=(
        _pattern(rf"^(?P<mods>(?:(?:static|inline|extern|constexpr|consteval|virtual)[ \t]+)*)"
                 rf"{_C_RETURN_TYPE}(?P<parent>{_WORD})(?:<[^>\n]*>)?::(?P<name>~?{_WORD})"
                 rf"[ \t]*\([^;{{}}]*\)[^;{{}}]*?(?=[ \t\r\n]*\{{)", "method", require_body=True),
        _pattern(rf"^(?P<mods>(?:(?:static|inline|extern|constexpr|consteval)[ \t]+)*)"
                 rf"{_C_RETURN_TYPE}(?P<name>{_WORD})[ \t]*\([^;{{}}]*\)[^;{{}}:]*?"
                 rf"(?=[ \t\r\n]*\{{)", "function", require_body=True),
    ),
    members=(
        _pattern(rf"^[ \t]*(?P<mods>(?:(?:virtual|static|inline|explicit|constexpr|consteval|"
                 rf"friend)[ \t]+)*){_C_RETURN_TYPE}(?P<name>~?{_WORD})[ \t]*\([^;{{}}]*\)",
                 "method"),
    ),
    transparent=re.compile(rf"^[ \t]*(?:(?:inline[ \t]+)?namespace[ \t]*[\w:]*|{_EXTERN_C})"
                           rf"[ \t\r\n]*\{{", re.M),
    decorators=("template", "[["),
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
    decorators=(),
    doc_markers=C_DOC,
    keywords=_C_KEYWORDS,
    exported=lambda match, name, kind, member: True,
    abstract=lambda match, kind, body: kind == "protocol",
    regions=_objc_regions,
)
