#!/usr/bin/env python3
"""Names that break Clean Code's naming rules, each finding citing the rule it breaks.

Classes, functions, and methods come from the symbols of every language the map reads.
Variables and parameters come only where declarations read reliably: Python through its own
parser, JavaScript and TypeScript through `const`, `let`, `var`, and parameter lists on the
lexer's code view. A name that a loop, a catch, a lambda, or another author dictates is not
read: the rules judge only names their author chose. Evidence for judgement, never a verdict.

Standard library only.
"""

from __future__ import annotations

import ast
import bisect
import posixpath
import re
import warnings
from collections import Counter, defaultdict
from typing import NamedTuple, Optional

from source import lexer as source_lexer
from symbols import model as symbol_model

from . import findings as structure_findings

RULE_CITES = {
    "vague": "N1",
    "encoded": "N6",
    "numbered": "N1, N4",
    "noise-word": "N1, G17",
    "verb-class": "N1",
    "too-short": "N5",
    "convention": "N3, G24",
    "file-mismatch": "N4, G17",
}

# Languages whose variables and parameters are read, not only their classes and functions.
VARIABLE_LANGUAGES = frozenset({"python", "javascript", "typescript"})

MIN_NAME_LENGTH = 3
# The project's own convention wins over the language's when at least this many of its names
# take a side, and more than this share of them agree: the casing of its function and method
# names, and the I prefix of its interfaces.
MAJORITY_MIN_NAMES = 10
MAJORITY_SHARE = 0.6

# --- What each rule looks for ----------------------------------------------------------------

VAGUE_NAMES = frozenset({"data", "info", "obj", "item", "thing", "stuff", "temp", "tmp", "val",
                         "res", "ret", "foo", "bar"})
# A bare verb names no object: `handle`, `process`, `doIt`, `manage`, alone or with `Data`.
VAGUE_VERBS = frozenset({"handle", "process", "doit", "manage"})
# Parameters a language or framework names: receivers, varargs, and a web handler's request,
# response, next, and context. `res` stays vague as a variable.
DICTATED_PARAMETERS = frozenset({"self", "cls", "args", "kwargs", "kw", "request", "req", "res",
                                 "next", "ctx"})

# A type or scope glued to the front: `strName`, `iCount`, `szTitle`, `lpBuffer`, `m_count`. A
# snake_case prefix is left alone: `obj_type` and `str_count` name whose type or count it is.
_HUNGARIAN = re.compile(r"(?:lpsz|psz|str|sz|lp|dw|int|arr|obj|bln|bool|dbl|flt|ptr|i|b|s)"
                        r"(?=[A-Z][a-z])|[mg]_(?=[A-Za-z])")
# Words that only look prefixed.
_PREFIX_LIKE_WORDS = frozenset({"iframe", "iphone", "ipad", "ipod", "imac", "itunes", "icloud"})
_INTERFACE_PREFIX = re.compile(r"I[A-Z][a-z]")
# .NET (C#, PowerShell) and C++ (COM, Unreal Engine) prefix interfaces with an I by convention;
# so does any project whose interfaces in a language family mostly carry one.
I_PREFIX_LANGUAGES = frozenset({"csharp", "powershell", "cpp"})
_INTERFACE_KINDS = frozenset({"interface", "protocol", "trait"})
_ABSTRACTION_KINDS = _INTERFACE_KINDS | {"type"}

# Digits that belong to a term rather than number a copy: hashes and encodings (sha256, md5,
# utf8, base64, b64, cp1252), standards (iso8601, rfc3339, pep8), sized types and vectors
# (int32, float64, u8, Vector3), platforms, formats, and protocols (win32, x86, arm64, zip64,
# uuid4, http2, ipv6, oauth2, x509, h264, mp4, es2015, python3), services (s3, ec2), math
# (log10, l2), coordinates (x2, lat1), rankings (top10), and quarters (q3).
_TERM_DIGITS = re.compile(
    r"(?:sha|md|crc|adler|blake|murmur|utf|ucs|base|b|latin|cp|iso|rfc|pep|aes|rsa|win|arm|amd|"
    r"aarch|int|uint|float|double|half|bool|bigint|i|u|f|vec|vector|mat|matrix|zip|uuid|http|ipv|"
    r"oauth|tls|ssl|x|y|z|lat|lon|lng|h|mp|es|py|python|web|s|ec|log|l|top|q)\d+")
# A copy is numbered 1, 2, or 10; three digits or more are a value: a year, a threshold, a code.
MAX_COPY_NUMBER_DIGITS = 2
# An API version is no copy beside a word that says so: `api_v1`, `v2_router`.
_API_WORDS = frozenset({"api", "route", "routes", "router", "endpoint", "endpoints", "blueprint"})
COPY_SUFFIXES = frozenset({"new", "old", "copy", "final"})
_PREDICATE_WORDS = frozenset({"is", "has", "was", "can", "should", "will", "did", "does"})
# `deep_copy` performs a copy; it is not one.
_COPY_OPERATIONS = frozenset({"deep", "shallow"})

NOISE_WORDS = frozenset({"manager", "processor", "data", "info", "helper", "util", "utils", "stuff"})
# A compound term that ends in a noise word yet names one thing: Python's context manager protocol.
TERMS_OF_ART = frozenset({"context manager"})
_CLASS_LIKE_KINDS = frozenset({"class", "struct", "record", "object"})
# Verbs that open an action's name: `ProcessOrder`, `HandleLogin`. Verbs that as often modify a
# noun (`LoadBalancer`, `CheckBox`, `BuildConfig`, `SearchBar`) are left out.
ACTION_VERBS = frozenset({"process", "handle", "manage", "do", "perform", "execute", "create",
                          "delete", "remove", "add", "get", "fetch", "retrieve", "send", "save",
                          "update", "calculate", "validate", "generate", "convert", "transform",
                          "apply", "notify", "dispatch", "submit", "make", "insert"})
# A last word that says what the type is, so a verb before it names what the type carries or
# does, or is a noun itself: `CreateOrderCommand`, `GetUserQuery`, `SendEmailJob`,
# `ProcessPoolExecutor`, `SaveButton`.
ROLE_NOUNS = NOISE_WORDS | frozenset({
    "command", "query", "request", "response", "input", "output", "dto", "event", "message",
    "mutation", "payload", "params", "options", "result", "action", "job", "task", "case",
    "handler", "service", "controller", "listener", "builder", "factory", "executor", "runner",
    "monitor", "form", "view", "page", "component", "button", "dialog", "modal", "screen", "panel",
    "menu", "widget", "list", "set", "map", "queue", "pool", "group", "handle", "state", "status",
    "type", "config", "error", "exception", "warning", "id", "test",
})

# Short names every reader knows: the spec's math idioms (x, y, i, j, k, e, id) and their kin,
# bisect's lo and hi, two-letter words, and the handles an ecosystem fixes: pandas' df,
# matplotlib's ax, a database db, Django's pk, an ip address, a file descriptor fd, a traceback
# tb, a time zone tz, the DOM element el of Vue's directive hooks.
READABLE_SHORT_NAMES = frozenset({
    "x", "y", "z", "i", "j", "k", "n", "e", "t", "id", "pi", "dx", "dy", "dz", "dt", "lo", "hi",
    "on", "is", "as", "do", "go", "to", "up", "at", "by", "of", "in", "or", "ok", "it",
    "df", "ax", "db", "pk", "ip", "fd", "tb", "tz", "el",
})
_COORDINATE = re.compile(r"[xyz]\d", re.IGNORECASE)

SNAKE, CAMEL, PASCAL, UPPER, LOWER, MIXED = "snake", "camel", "pascal", "upper", "lower", "mixed"
_SNAKE_CASE = frozenset({SNAKE, LOWER})
_CAMEL_CASE = frozenset({CAMEL, LOWER})
_CAMEL_OR_PASCAL_CASE = frozenset({CAMEL, PASCAL, LOWER})
_PASCAL_CASE = frozenset({PASCAL, UPPER})
_MIXED_CAPS = frozenset({CAMEL, PASCAL, LOWER, UPPER})
# The casings each language accepts, per kind of name; a language or kind left out is not
# judged. JavaScript, TypeScript, and Kotlin functions may be PascalCase: components,
# constructors, and factories named for what they build. Go's MixedCaps allows any casing
# without an underscore.
LANGUAGE_CASING = {
    "python": {"function": _SNAKE_CASE, "method": _SNAKE_CASE, "class": _PASCAL_CASE},
    "javascript": {"function": _CAMEL_OR_PASCAL_CASE, "method": _CAMEL_CASE, "class": _PASCAL_CASE},
    "typescript": {"function": _CAMEL_OR_PASCAL_CASE, "method": _CAMEL_CASE, "class": _PASCAL_CASE},
    "java": {"method": _CAMEL_CASE, "class": _PASCAL_CASE},
    "kotlin": {"function": _CAMEL_OR_PASCAL_CASE, "method": _CAMEL_CASE, "class": _PASCAL_CASE},
    "csharp": {"method": _PASCAL_CASE, "class": _PASCAL_CASE},
    "go": {"function": _MIXED_CAPS, "method": _MIXED_CAPS, "class": _MIXED_CAPS},
    "rust": {"function": _SNAKE_CASE, "method": _SNAKE_CASE, "class": _PASCAL_CASE},
    "ruby": {"function": _SNAKE_CASE, "method": _SNAKE_CASE},
    "php": {"method": _CAMEL_CASE},
}
# Handler names a framework fixes: HTTP verbs (web.py, Next.js, SvelteKit), and a word joined to
# a type or constant name, as `visit_FunctionDef`, `do_GET`, and `btnSave_Click` are.
HTTP_VERBS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})
_DISPATCH_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*_[A-Z]\w*")

# Languages whose files each hold one public type named like the file.
ONE_TYPE_PER_FILE_LANGUAGES = frozenset({"java", "csharp", "kotlin", "swift", "php", "dart"})


class Declared(NamedTuple):
    """A name its author chose, and where."""

    name: str
    kind: str               # class, function, method, variable, parameter, or file
    line: int
    symbol: Optional[symbol_model.Symbol] = None    # behind a class, function, method, or file


class ProjectConventions(NamedTuple):
    """What the project itself establishes about names."""

    casing: dict                    # language -> kind -> accepted casings
    type_names: frozenset           # the project's own type names, lowercased: its vocabulary
    i_prefix_families: frozenset    # language families whose interfaces mostly carry an I prefix


# --- Classes, functions, and methods ------------------------------------------------------------

_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*[?!=]?")


def _kind_of(symbol) -> Optional[str]:
    """What a finding calls the symbol; None for a component, which is named after its file."""
    if symbol.kind in ("function", "method"):
        return symbol.kind
    if symbol.kind in symbol_model.TYPE_KINDS or symbol.kind in ("type", "module"):
        return "class"
    return None


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def _symbol_names(roled_file) -> list:
    """The file's classes, functions, and methods, except a constructor, named for its class, and
    a dunder, named by the language."""
    names = []
    for item in roled_file.symbols:
        symbol = item.symbol
        kind = _kind_of(symbol)
        if kind is None or not _IDENTIFIER.fullmatch(symbol.name) or _is_dunder(symbol.name):
            continue
        if kind == "method" and symbol.name == symbol.parent:
            continue
        names.append(Declared(symbol.name, kind, symbol.line, symbol))
    return names


# --- Python variables and parameters ------------------------------------------------------------

def _parameters(arguments) -> list:
    """Every parameter of a signature, positional-only to `**kwargs`."""
    listed = arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    return listed + [parameter for parameter in (arguments.vararg, arguments.kwarg) if parameter]


def _assigned_targets(statement) -> list:
    if isinstance(statement, ast.Assign):
        return statement.targets
    if isinstance(statement, ast.AnnAssign):
        return [statement.target]
    return []


def _nested_statements(statement) -> list:
    """The statements inside a compound statement: its bodies, and each handler's or case's."""
    nested = []
    for field in ("body", "orelse", "finalbody"):
        nested += getattr(statement, field, None) or []
    clauses = (getattr(statement, "handlers", None) or []) + (getattr(statement, "cases", None) or [])
    for clause in clauses:
        nested += clause.body
    return nested


def _bound_names(target) -> list:
    """The plain names a target binds: `a` and `b` in `a, (b, *rest) = ...`, never `self.a`."""
    if isinstance(target, ast.Name):
        return [target]
    if isinstance(target, ast.Starred):
        return _bound_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for element in target.elts for name in _bound_names(element)]
    return []


def _bind(first_bindings: dict, scope, name: str, line: int, kind: str) -> None:
    """Record name's binding in scope unless an earlier line bound it: rebinding a parameter or a
    variable declares nothing new."""
    key = (scope, name)
    if key not in first_bindings or line < first_bindings[key][0]:
        first_bindings[key] = (line, kind)


def _python_names(text: str) -> list:
    """Parameters and assigned variables, each at its first binding in its scope.

    Only statements are walked: loop and `with` targets, `except` names, comprehension targets,
    and lambda parameters are short-lived, a walrus target lives inside an expression, and class
    attributes are fields, so none are read. A stack, not recursion, keeps deep nesting safe.
    """
    try:
        with warnings.catch_warnings():
            # The scanned file's own warnings (invalid escapes, say) are not ours to print.
            warnings.simplefilter("ignore")
            tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return []       # the file's symbols record why it could not be read
    first_bindings = {}
    # Each entry: a statement, the scope its names bind in, and whether it sits in a class body.
    pending = [(statement, tree, False) for statement in tree.body]
    while pending:
        statement, scope, in_class = pending.pop()
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for parameter in _parameters(statement.args):
                _bind(first_bindings, statement, parameter.arg, parameter.lineno, "parameter")
            pending += [(nested, statement, False) for nested in statement.body]
        elif isinstance(statement, ast.ClassDef):
            pending += [(nested, statement, True) for nested in statement.body]
        else:
            if not in_class:
                for target in _assigned_targets(statement):
                    for name in _bound_names(target):
                        _bind(first_bindings, scope, name.id, name.lineno, "variable")
            pending += [(nested, scope, in_class) for nested in _nested_statements(statement)]
    return [Declared(name, kind, line) for (_, name), (line, kind) in first_bindings.items()]


# --- JavaScript and TypeScript variables and parameters ---------------------------------------

_DECLARATION = re.compile(r"(?<![\w$.])(?:const|let|var)\b")
_FOR_HEADER = re.compile(r"\bfor\s*(?:await\s*)?\(\s*$")
_SCRIPT_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")
_PROPERTY_KEY = re.compile(r"[A-Za-z_$][\w$]*|\d+|\"[^\"\n]*\"|'[^'\n]*'")
_REQUIRE_CALL = re.compile(r"\s*require\s*\(")
_SPACE = re.compile(r"\s*")
_FUNCTION_KEYWORD = re.compile(r"(?<![\w$.])function\b(?:\s*\*)?\s*(?:(?P<name>[A-Za-z_$][\w$]*)\s*)?"
                               r"(?:<[^<>()]*>\s*)?\(")
_METHOD = re.compile(r"^[ \t]*(?:(?:public|private|protected|static|async|readonly|override|abstract|"
                     r"get|set|accessor)[ \t]+)*(?:\*[ \t]*)?(?P<name>#?[A-Za-z_$][\w$]*)[ \t]*"
                     r"(?:<[^<>\n]*>[ \t]*)?\(", re.M)
_METHOD_BODY = re.compile(r"\s*(?::[^{};=]*)?\{")
_NOT_METHODS = frozenset({"if", "for", "while", "switch", "catch", "function", "return", "with",
                          "typeof", "new", "delete", "void", "await", "yield", "super", "import",
                          "export", "else", "do", "try", "throw", "case", "default", "in", "of",
                          "instanceof"})
_ARROW = re.compile(r"=>")
_RETURN_TYPE = re.compile(r"\)\s*:[^=;{}()]*$")
_ASSIGNED = re.compile(r"=\s*(?:async\s+)?(?:<[^<>()]*>\s*)?$")
_TYPE_ALIAS = re.compile(r"\btype\s+[A-Za-z_$][\w$]*\s*(?:<[^<>]*>\s*)?=\s*(?:<[^<>()]*>\s*)?$")
_PARAMETER_MODIFIER = re.compile(r"(?:public|private|protected|readonly|override)\s+")
_DECORATOR = re.compile(r"@[\w$.]+")
_DECLARATOR_TOKENS = re.compile(r"[()\[\]{},;<>\n]")
_ELEMENT_TOKENS = re.compile(r"[()\[\]{},]")
_PARAMETER_TOKENS = re.compile(r"=>|[()\[\]{}<>,]")
_ANNOTATION_TOKENS = re.compile(r"=>|[()\[\]{}<>=,;\n]")
# How far back the assignment naming a function, or an arrow's return type, may start.
_LOOKBEHIND = 200
_MAX_PARAMETER_SPAN = 1000
_MAX_PATTERN_NESTING = 8


def _skip_space(code: str, index: int) -> int:
    return _SPACE.match(code, index).end()


def _skip_space_back(code: str, index: int) -> int:
    while index >= 0 and code[index] in " \t\r\n":
        index -= 1
    return index


def _element_end(code: str, index: int) -> int:
    """The offset of the `,` or closing bracket ending the element at index; a default value
    (`= []`) is passed over."""
    depth = 0
    for token in _ELEMENT_TOKENS.finditer(code, index):
        if token.group() in "([{":
            depth += 1
        elif depth == 0:
            return token.start()
        elif token.group() != ",":
            depth -= 1
    return len(code)


def _property_key_end(code: str, index: int) -> int:
    """The offset after the property key at index: a name, a string, a number, or `[computed]`."""
    key = _PROPERTY_KEY.match(code, index)
    if key:
        return key.end()
    if code.startswith("[", index):
        return _element_end(code, index + 1) + 1
    return index


def _binding(code: str, index: int, nesting: int = 0) -> tuple:
    """([(name, offset)], end) for the identifier or destructuring pattern at index.

    A shorthand property (`{ data }`) takes the object's key as its name, chosen by the object's
    author, so it binds no name here; a renamed one (`{ data: rows }`) does.
    """
    index = _skip_space(code, index)
    identifier = _SCRIPT_IDENTIFIER.match(code, index)
    if identifier:
        return [(identifier.group(), index)], identifier.end()
    if nesting > _MAX_PATTERN_NESTING or not code.startswith(("{", "["), index):
        return [], index
    closer = "}" if code[index] == "{" else "]"
    names = []
    index += 1
    while True:
        index = _skip_space(code, index)
        if index >= len(code) or code[index] == closer:
            return names, index + 1
        if code[index] == ",":         # a hole in an array pattern
            index += 1
            continue
        if code.startswith("...", index):
            found, index = _binding(code, index + 3, nesting + 1)
            names += found
        elif closer == "]":
            found, index = _binding(code, index, nesting + 1)
            names += found
        else:
            index = _skip_space(code, _property_key_end(code, index))
            if code.startswith(":", index):
                found, index = _binding(code, index + 1, nesting + 1)
                names += found
        index = _element_end(code, index)
        if index >= len(code) or code[index] not in (",", closer):
            return names, index        # not a pattern after all
        if code[index] == ",":
            index += 1


def _skip_annotation(code: str, index: int) -> int:
    """The offset after a TypeScript `: Type` annotation at index, if there is one."""
    index = _skip_space(code, index)
    if not code.startswith(":", index):
        return index
    depth = 0
    for token in _ANNOTATION_TOKENS.finditer(code, index + 1):
        character = token.group()
        if character == "=>":
            continue
        if character in "([{<":
            depth += 1
        elif character in ")]}>":
            if depth == 0:
                return token.start()
            depth -= 1
        elif depth == 0:
            return token.start()        # `=`, `,`, `;`, or a line break
    return len(code)


def _declarator_end(code: str, index: int) -> tuple:
    """(offset, whether another declarator follows) for the end of the declarator at index.
    Reading stops at a line break, and at `<` or `>`, which may open JSX or generics."""
    depth = 0
    for token in _DECLARATOR_TOKENS.finditer(code, index):
        character = token.group()
        if character in "([{":
            depth += 1
        elif character in ")]}":
            if depth == 0:
                return token.start(), False
            depth -= 1
        elif depth == 0:
            return token.start(), character == ","
    return len(code), False


def _declared_variables(code: str, declaration) -> list:
    """(name, offset) for each name one `const`, `let`, or `var` declares. A for loop's variable
    is short-lived, and a `require`d module's alias mirrors the module's name: neither is read."""
    start = declaration.start()
    if _FOR_HEADER.search(code, max(0, start - 30), start):
        return []
    index = _skip_space(code, declaration.end())
    names = []
    while True:
        index = _skip_space(code, index)
        is_pattern = code.startswith(("{", "["), index)
        begin = index
        bindings, index = _binding(code, index)
        if index == begin:
            return names
        index = _skip_annotation(code, index)
        initialized = code.startswith("=", index) and not code.startswith("=>", index)
        if is_pattern or not (initialized and _REQUIRE_CALL.match(code, index + 1)):
            names += bindings
        index, more = _declarator_end(code, index)
        if not more:
            return names
        index += 1


def _is_assigned_a_name(code: str, head: int) -> bool:
    """Whether the function whose `function` keyword or parameters start at head is assigned a
    name: `const total = (...) =>`, or a class field. An arrow typed in an alias
    (`type Total = (x) => number`) is no function."""
    window = max(0, head - _LOOKBEHIND)
    return bool(_ASSIGNED.search(code, window, head)) and not _TYPE_ALIAS.search(code, window, head)


def _opening_paren(code: str, close: int) -> Optional[int]:
    depth = 0
    for index in range(close, max(-1, close - _MAX_PARAMETER_SPAN), -1):
        if code[index] == ")":
            depth += 1
        elif code[index] == "(":
            depth -= 1
            if depth == 0:
                return index
    return None


def _arrow_parameters_start(code: str, arrow: int) -> Optional[int]:
    """Where the parameters of the arrow function at arrow start: its `(`, or its lone parameter."""
    end = _skip_space_back(code, arrow - 1)
    if end < 0:
        return None
    if code[end] != ")":
        annotated = _RETURN_TYPE.search(code, max(0, arrow - _LOOKBEHIND), arrow)
        if annotated is not None:
            end = annotated.start()
    if code[end] == ")":
        return _opening_paren(code, end)
    start = end
    while start > 0 and (code[start - 1].isalnum() or code[start - 1] in "_$"):
        start -= 1
    before = _skip_space_back(code, start - 1)
    if not _SCRIPT_IDENTIFIER.fullmatch(code, start, end + 1) or (before >= 0 and code[before] in ":."):
        return None         # a return type, or a member
    return start


def _parameter_list_starts(code: str) -> set:
    """Offsets where the parameters of each function with a chosen name start: a function
    declaration, a method, or a function or arrow assigned to a name. A function passed as an
    argument is a lambda, its parameters short-lived."""
    starts = set()
    for match in _FUNCTION_KEYWORD.finditer(code):
        if match.group("name") or _is_assigned_a_name(code, match.start()):
            starts.add(match.end() - 1)
    for match in _METHOD.finditer(code):
        close = source_lexer.closing_paren(code, match.end() - 1)
        if match.group("name") not in _NOT_METHODS and close >= 0 and _METHOD_BODY.match(code, close + 1):
            starts.add(match.end() - 1)
    for match in _ARROW.finditer(code):
        start = _arrow_parameters_start(code, match.start())
        if start is not None and _is_assigned_a_name(code, start):
            starts.add(start)
    return starts


def _parameter_start(code: str, index: int, close: int) -> int:
    """The offset of the binding a parameter declares, past decorators, modifiers, and `...`."""
    while index < close:
        index = _skip_space(code, index)
        decorator = _DECORATOR.match(code, index)
        modifier = _PARAMETER_MODIFIER.match(code, index)
        if decorator:
            index = _skip_space(code, decorator.end())
            if code.startswith("(", index):
                end = source_lexer.closing_paren(code, index)
                index = end + 1 if end >= 0 else close
        elif modifier:
            index = modifier.end()
        elif code.startswith("...", index):
            index += 3
        else:
            return index
    return index


def _parameter_end(code: str, index: int, close: int) -> int:
    """The offset of the `,` ending the parameter at index, or close."""
    depth = 0
    for token in _PARAMETER_TOKENS.finditer(code, index, close):
        character = token.group()
        if character == "=>":
            continue
        if character in "([{<":
            depth += 1
        elif character in ")]}>":
            depth = max(depth - 1, 0)
        elif depth == 0:
            return token.start()
    return close


def _parameter_names(code: str, start: int) -> list:
    """(name, offset) for each parameter the list at start declares: a `(` list, or an arrow's
    lone parameter."""
    if code[start] != "(":
        identifier = _SCRIPT_IDENTIFIER.match(code, start)
        return [(identifier.group(), start)] if identifier else []
    close = source_lexer.closing_paren(code, start)
    names = []
    index = start + 1
    while 0 <= index < close:
        index = _parameter_start(code, index, close)
        bindings, index = _binding(code, index)
        names += [(name, offset) for name, offset in bindings if offset < close]
        index = _parameter_end(code, index, close) + 1
    return names


def _script_names(text: str, language: str) -> list:
    """Variables from `const`, `let`, and `var`, and the parameters of named functions."""
    code = source_lexer.strip(text, language).code
    line_starts = [0] + [match.end() for match in re.finditer("\n", code)]

    def declared_at(name: str, offset: int, kind: str) -> Declared:
        return Declared(name, kind, bisect.bisect_right(line_starts, offset))

    names = [declared_at(name, offset, "variable") for declaration in _DECLARATION.finditer(code)
             for name, offset in _declared_variables(code, declaration)]
    names += [declared_at(name, offset, "parameter") for start in sorted(_parameter_list_starts(code))
              for name, offset in _parameter_names(code, start)]
    return names


def _declared_names(roled_file, text: Optional[str]) -> list:
    """Every name the file's author chose: its symbols, then, where declarations read reliably,
    its variables and parameters."""
    names = _symbol_names(roled_file)
    if text is None or roled_file.language not in VARIABLE_LANGUAGES:
        return names
    if roled_file.language == "python":
        variables = _python_names(text)
    else:
        variables = _script_names(text, roled_file.language)
    # A top-level `const load = () => {}` is already a function symbol.
    symbol_lines = {(name.name, name.line) for name in names}
    return names + [name for name in variables if (name.name, name.line) not in symbol_lines]


# --- The rules ---------------------------------------------------------------------------------

def _is_exempt(name: Declared) -> bool:
    """A throwaway `_`, or a parameter a language or framework names."""
    return not name.name.strip("_") or (name.kind == "parameter" and name.name in DICTATED_PARAMETERS)


def _is_vague(name: Declared, type_names: frozenset) -> bool:
    if name.kind in ("variable", "parameter"):
        # An `item` holding the project's own `Item` speaks its vocabulary.
        word = name.name.lower()
        return word in VAGUE_NAMES and word not in type_names
    if name.kind != "function":
        return False
    verb = name.name.lower().replace("_", "")
    return verb in VAGUE_VERBS or (verb.endswith("data") and verb[:-4] in VAGUE_VERBS)


def _family(language: str) -> str:
    return structure_findings.LANGUAGE_FAMILY.get(language, language)


def _is_encoded(name: Declared, language: str, i_prefix_families: frozenset) -> bool:
    if name.kind in ("variable", "parameter"):
        unprefixed = name.name.lstrip("_$")
        if not _HUNGARIAN.match(unprefixed):
            return False
        return "".join(structure_findings.split_identifier(unprefixed)[:2]) not in _PREFIX_LIKE_WORDS
    if name.kind != "class" or language in I_PREFIX_LANGUAGES or _family(language) in i_prefix_families:
        return False
    is_abstraction = name.symbol.kind in _ABSTRACTION_KINDS or name.symbol.abstract
    return is_abstraction and bool(_INTERFACE_PREFIX.match(name.name))


def _is_numbered(name: Declared) -> bool:
    core = name.name.strip("_")
    if len(core) < MIN_NAME_LENGTH or core.upper() == core:
        return False        # too-short owns a short name; a constant's digits name its value
    words = structure_findings.split_identifier(name.name)
    if len(words) < 2:
        return False
    last = words[-1]
    if last.isdigit():
        is_api_version = words[-2] == "v" and bool(_API_WORDS.intersection(words))
        return not (len(last) > MAX_COPY_NUMBER_DIGITS or _TERM_DIGITS.fullmatch(words[-2] + last)
                    or is_api_version)
    if last not in COPY_SUFFIXES or words[0] in _PREDICATE_WORDS:
        return False
    if last == "copy" and words[-2] in _COPY_OPERATIONS:
        return False
    # A variable's old, new, or final value describes it; a class or function so named is a copy.
    if name.kind == "class":
        return True
    return name.kind in ("function", "method") and name.name.lower().endswith("_" + last)


def _base_names(symbol, language: str) -> list:
    """The names a class declaration writes after its own: its bases, interfaces, and traits."""
    declared = re.search(r"\b" + re.escape(symbol.name) + r"\b", symbol.context)
    if declared is None:
        return []
    header = symbol.context[declared.end():]
    if language == "python":
        # `class Name(Base): pass` puts a body on the same line, so only the parentheses name
        # bases, and a long list of them may run past the lines the context holds.
        header = header.lstrip()
        if not header.startswith("("):
            return []
        closing = header.find(")")
        header = header[:closing] if closing >= 0 else header
    else:
        header = re.split(r"[{;]", header, 1)[0]
    return _SCRIPT_IDENTIFIER.findall(header)


def _last_word(identifier: str) -> str:
    words = structure_findings.split_identifier(identifier)
    return words[-1] if words else ""


def _is_class_like(name: Declared) -> bool:
    return name.kind == "class" and name.symbol.kind in _CLASS_LIKE_KINDS


def _is_noise_word(name: Declared, language: str) -> bool:
    """A class named for a noise word, unless a base type ends in the same word and so gives the
    framework's term: `ArticleManager(models.Manager)`, `ZoneInfo(tzinfo)`."""
    if not _is_class_like(name):
        return False
    words = structure_findings.split_identifier(name.name)
    if not words or words[-1] not in NOISE_WORDS or " ".join(words[-2:]) in TERMS_OF_ART:
        return False
    return not any(base.lower().endswith(words[-1]) for base in _base_names(name.symbol, language))


def _is_verb_class(name: Declared, language: str) -> bool:
    if not _is_class_like(name):
        return False
    words = structure_findings.split_identifier(name.name)
    if len(words) < 2 or words[0] not in ACTION_VERBS or words[-1] in ROLE_NOUNS:
        return False
    bases = _base_names(name.symbol, language)
    # A class named for the interface it implements takes that name:
    # `NotifyPropertyChanged : INotifyPropertyChanged`.
    return "I" + name.name not in bases and not any(_last_word(base) in ROLE_NOUNS for base in bases)


def _is_too_short(name: Declared) -> bool:
    core = name.name.strip("_$")
    if len(core) >= MIN_NAME_LENGTH or core.lower() in READABLE_SHORT_NAMES or _COORDINATE.fullmatch(core):
        return False
    # An uppercase variable is a type variable, a matrix, or an acronym: `R = TypeVar("R")`,
    # `X, y = samples`, `_JS = Syntax()`.
    return not (name.kind in ("variable", "parameter") and core.isupper())


def _casing_of(name: str) -> Optional[str]:
    """The casing of a name, ignoring leading `_` and `$` and Ruby's trailing `?`, `!`, or `=`."""
    core = name.rstrip("?!=").strip("_$")
    if not any(character.isalpha() for character in core):
        return None
    if core.upper() == core:
        return UPPER
    if "_" in core:
        return SNAKE if core.lower() == core else MIXED
    if core[0].isupper():
        return PASCAL
    return CAMEL if core.lower() != core else LOWER


def _has_dictated_casing(name: str) -> bool:
    return name in HTTP_VERBS or bool(_DISPATCH_NAME.fullmatch(name))


def _breaks_convention(name: Declared, expected: dict) -> bool:
    accepted = expected.get(name.kind)
    if accepted is None or _has_dictated_casing(name.name):
        return False
    casing = _casing_of(name.name)
    return casing is not None and casing not in accepted


def _is_majority(agreeing: int, total: int) -> bool:
    return total >= MAJORITY_MIN_NAMES and agreeing > MAJORITY_SHARE * total


def _project_casing(files, declared: dict) -> dict:
    """language -> kind -> accepted casings: the language's own, unless most of the project's
    function and method names in that language follow another casing the language rejects, as
    WordPress PHP follows snake_case. Then that casing is the one expected."""
    votes = defaultdict(Counter)
    for roled_file in files:
        for name in declared[roled_file.path]:
            if name.kind in ("function", "method") and not _has_dictated_casing(name.name):
                casing = _casing_of(name.name)
                if casing in (SNAKE, CAMEL, PASCAL, MIXED):
                    votes[roled_file.language][casing] += 1
    expected = {}
    for language, accepted in LANGUAGE_CASING.items():
        expected[language] = dict(accepted)
        counted = votes.get(language)
        if not counted:
            continue
        casing, count = counted.most_common(1)[0]
        function_casings = set().union(*(accepted.get(kind, ()) for kind in ("function", "method")))
        if not _is_majority(count, sum(counted.values())) or casing == MIXED or casing in function_casings:
            continue
        for kind in ("function", "method"):
            if kind in accepted:
                expected[language][kind] = frozenset({casing, LOWER})
    return expected


def _project_type_names(files) -> frozenset:
    return frozenset(item.symbol.name.lower() for roled_file in files for item in roled_file.symbols
                     if item.symbol.kind in symbol_model.TYPE_KINDS or item.symbol.kind == "type")


def _i_prefix_families(files) -> frozenset:
    """The language families in which most of the project's interfaces carry an I prefix."""
    prefixed = Counter()
    interfaces = Counter()
    for roled_file in files:
        for item in roled_file.symbols:
            if item.symbol.kind in _INTERFACE_KINDS:
                interfaces[_family(roled_file.language)] += 1
                prefixed[_family(roled_file.language)] += bool(_INTERFACE_PREFIX.match(item.symbol.name))
    return frozenset(family for family, total in interfaces.items() if _is_majority(prefixed[family], total))


def _rules_broken(name: Declared, language: str, conventions: ProjectConventions) -> list:
    if _is_exempt(name):
        return []
    checks = (
        ("vague", _is_vague(name, conventions.type_names)),
        ("encoded", _is_encoded(name, language, conventions.i_prefix_families)),
        ("numbered", _is_numbered(name)),
        ("noise-word", _is_noise_word(name, language)),
        ("verb-class", _is_verb_class(name, language)),
        ("too-short", _is_too_short(name)),
        ("convention", _breaks_convention(name, conventions.casing.get(language, {}))),
    )
    return [rule for rule, broken in checks if broken]


def _file_mismatch(roled_file) -> Optional[Declared]:
    """The only public type of a file named for something else, in a language whose files each
    hold one type named like the file. An entry point holds what its template puts there."""
    stem = posixpath.basename(roled_file.path).split(".")[0]
    if roled_file.language not in ONE_TYPE_PER_FILE_LANGUAGES \
            or stem.lower() in structure_findings.ENTRY_POINT_STEMS:
        return None
    public_types = [item.symbol for item in roled_file.symbols
                    if item.symbol.parent is None and item.symbol.kind in symbol_model.TYPE_KINDS
                    and item.symbol.exported]
    if len(public_types) != 1:
        return None
    only_type = public_types[0]
    file_word = re.sub(r"[^a-z0-9]", "", stem.lower())
    type_word = re.sub(r"[^a-z0-9]", "", only_type.name.lower())
    # The file may name the type with a qualifier (`MetaFieldTypes`, `IComparer_T`,
    # `class-wp-query`), or the type may qualify the file's name (`Repository` for
    # `UserRepository`).
    if not file_word or type_word.endswith(file_word) or file_word.startswith(type_word) \
            or file_word.endswith(type_word):
        return None
    return Declared(only_type.name, "file", only_type.line, only_type)


def _finding(rule: str, name: Declared, path: str) -> dict:
    return {"rule": rule, "name": name.name, "kind": name.kind, "path": path, "line": name.line,
            "cites": RULE_CITES[rule]}


def _project_findings(sources, roles, texts) -> list:
    """The naming findings of one project's production files, judged by its own conventions."""
    declared = {roled_file.path: _declared_names(roled_file, texts.get(roled_file.path))
                for roled_file in sources}
    conventions = ProjectConventions(_project_casing(sources, declared), _project_type_names(sources),
                                     _i_prefix_families(sources))
    found = []
    for roled_file in sources:
        judged = [(name, _rules_broken(name, roled_file.language, conventions))
                  for name in declared[roled_file.path]]
        mismatch = _file_mismatch(roled_file)
        if mismatch is not None:
            judged.append((mismatch, ["file-mismatch"]))
        for name, rules in judged:
            exempt = roles.is_ignored_name(name.name) or roles.accepts(roled_file.path, name.name)
            if rules and not exempt:
                found += [_finding(rule, name, roled_file.path) for rule in rules]
    return found


def find_names(files, roles, texts, project_roots=()) -> list:
    """Names in production files that break a naming rule, each finding citing the rule.

    files are roled files; texts maps a path to its source, for the files whose variables and
    parameters are read (VARIABLE_LANGUAGES). `project_roots` are the folders holding a
    manifest: each project of a monorepo keeps its own casing and vocabulary. Test files, names
    an `ignore-name` pattern matches, and files or symbols the project `accept`s are exempt; the
    map passes no generated file.
    """
    projects = defaultdict(list)
    for roled_file in files:
        if not roled_file.is_test:
            projects[structure_findings._project_of(roled_file.path, project_roots)].append(roled_file)
    found = [finding for sources in projects.values()
             for finding in _project_findings(sources, roles, texts)]
    return sorted(found, key=lambda item: (item["path"], item["line"], item["rule"], item["name"]))
