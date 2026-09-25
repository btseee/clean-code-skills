#!/usr/bin/env python3
"""Names that break Clean Code's naming rules, each finding citing the rule it breaks.

Classes, functions, and methods come from the symbols of every language the map reads;
variables and parameters from the declarations its extractors read reliably (Python,
JavaScript, TypeScript: symbols.declarations). This module only judges names: the rules
weigh names their author chose. Evidence for judgement, never a verdict.

Standard library only.
"""

from __future__ import annotations

import posixpath
import re
from collections import Counter, defaultdict
from typing import NamedTuple, Optional

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
# utf8, base64, b64, cp1252), standards (iso8601, rfc3339, pep8, html5, css3), sized types and
# vectors (int32, float64, u8, Vector3), platforms, formats, and protocols (win32, x86, arm64,
# zip64, uuid4, http2, ipv6, oauth2, x509, h264, mp4, es2015, python3, webgl2), services (s3,
# ec2), models (ResNet18, vgg16, mobilenet_v2, yolov8, gpt4, llama3), math (log10, l2),
# coordinates (x2, lat1), rankings (top10), and quarters (q3).
_TERM_DIGITS = re.compile(
    r"(?:sha|md|crc|adler|blake|murmur|utf|ucs|base|b|latin|cp|iso|rfc|pep|html|css|aes|rsa|win|"
    r"arm|amd|aarch|int|uint|float|double|half|bool|bigint|i|u|f|vec|vector|mat|matrix|zip|uuid|"
    r"http|ipv|oauth|tls|ssl|x|y|z|lat|lon|lng|h|mp|es|py|python|web|webgl|s|ec|net|resnet|vgg|"
    r"mobilenet|efficientnet|inception|yolo|gpt|llama|log|l|top|q)v?\d+")
# A copy is numbered 1, 2, or 10; three digits or more are a value: a year, a threshold, a code.
MAX_COPY_NUMBER_DIGITS = 2
# An API version is no copy beside a word that says so: `api_v1`, `v2_router`.
_API_WORDS = frozenset({"api", "route", "routes", "router", "endpoint", "endpoints", "blueprint"})
COPY_SUFFIXES = frozenset({"new", "old", "copy", "final"})
# Words that join a verb to its object without naming anything: `mark_as_new`, `clear_all_old`.
_FILLER_WORDS = frozenset({"as", "all", "the", "a", "to"})
# A term that ends in a copy suffix: `show_whats_new`, `WhatsNew`.
_TERMS_ENDING_IN_A_SUFFIX = frozenset({"whats new"})
_PREDICATE_WORDS = frozenset({"is", "has", "was", "can", "should", "will", "did", "does"})
# `deep_copy` performs a copy; it is not one.
_COPY_OPERATIONS = frozenset({"deep", "shallow"})

NOISE_WORDS = frozenset({"manager", "processor", "data", "info", "helper", "util", "utils", "stuff"})
# Of the vague words, only a real noun can be a project's own vocabulary (`item` beside its
# `Item`); a noise word or an abbreviation stays vague even as a type's name (`type Data`).
_OWNABLE_VAGUE_NAMES = VAGUE_NAMES - NOISE_WORDS - {"obj", "tmp", "temp", "val", "res", "ret", "foo", "bar"}
# A compound term that ends in a noise word yet names one thing: Python's context manager protocol.
TERMS_OF_ART = frozenset({"context manager"})
_CLASS_LIKE_KINDS = frozenset({"class", "struct", "record", "object"})
# Verbs that open an action's name: `ProcessOrder`, `HandleLogin`. Verbs that as often modify a
# noun (`LoadBalancer`, `CheckBox`, `BuildConfig`, `SearchBar`) are left out.
ACTION_VERBS = frozenset({"process", "handle", "manage", "do", "perform", "execute", "create",
                          "delete", "remove", "add", "get", "fetch", "retrieve", "send", "save",
                          "update", "calculate", "validate", "generate", "convert", "transform",
                          "apply", "notify", "dispatch", "submit", "make", "insert"})
# Verbs a copy suffix can be the object of: `create_new`, `StartNew`, `remove_old`, `mark_final`.
_VERBS_TAKING_A_SUFFIX = ACTION_VERBS | {"start", "stop", "open", "close", "show", "hide", "run", "load",
                                         "clear", "clean", "purge", "mark", "reset", "begin", "keep", "use"}
# A last word that says what the type is, so a verb before it names what the type carries or
# does, or is a noun itself: `CreateOrderCommand`, `GetUserQuery`, `SendEmailJob`,
# `ProcessPoolExecutor`, `SaveButton`.
ROLE_NOUNS = NOISE_WORDS | frozenset({
    "command", "query", "request", "response", "input", "output", "dto", "event", "message",
    "mutation", "payload", "params", "options", "result", "action", "job", "task", "case",
    "handler", "service", "controller", "listener", "builder", "factory", "executor", "runner",
    "monitor", "client", "provider", "adapter", "context", "form", "view", "page", "component",
    "button", "dialog", "modal", "screen", "panel", "menu", "widget", "list", "set", "map", "queue",
    "pool", "group", "handle", "state", "status", "type", "config", "error", "exception", "warning",
    "id", "test",
})
# Roles whose classes each do one action and are named for it by convention: Laravel's actions,
# jobs, and listeners, a use case, a command or message handler, an event subscriber.
ACTION_ROLES = frozenset({"action", "server-action", "job", "listener", "command", "handler",
                          "message-handler", "use-case", "interactor", "subscriber", "event-subscriber"})
# Python bases that shape a class without making it a framework's: its methods are its author's.
STRUCTURAL_BASES = frozenset({"object", "ABC", "Generic", "Protocol", "Enum", "IntEnum", "StrEnum", "Flag",
                              "IntFlag", "NamedTuple", "TypedDict", "Exception", "BaseException"})
_STRUCTURAL_BASE_SUFFIXES = ("Error", "Exception", "Warning")

# Short names every reader knows: the spec's math idioms (x, y, i, j, k, e, id) and their kin,
# bisect's lo and hi, a learning rate lr, two-letter words, and the handles an ecosystem fixes:
# pandas' df, matplotlib's ax, a database db, Django's pk, an ip address, a file descriptor fd, a
# traceback tb, a time zone tz, the DOM element el of Vue's directive hooks.
READABLE_SHORT_NAMES = frozenset({
    "x", "y", "z", "i", "j", "k", "n", "e", "t", "id", "pi", "dx", "dy", "dz", "dt", "lo", "hi",
    "lr", "on", "is", "as", "do", "go", "to", "up", "at", "by", "of", "in", "or", "ok", "it",
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
    role: Optional[str] = None      # the role the symbol's own declaration shows
    owner: Optional[str] = None     # the class whose method declares this parameter


class ProjectConventions(NamedTuple):
    """What the project itself establishes about names."""

    casing: dict                    # language -> kind -> accepted casings
    type_names: frozenset           # the project's own type names, lowercased: its vocabulary
    i_prefix_families: frozenset    # language families whose interfaces mostly carry an I prefix
    function_names: frozenset       # every function and method name the project declares


# --- Classes, functions, and methods ------------------------------------------------------------

_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*[?!=]?")
_NAME_TOKEN = re.compile(r"[A-Za-z_$][\w$]*")
_DOTTED_NAME = re.compile(r"[A-Za-z_][\w.]*")
_SUBSCRIPT = re.compile(r"\[[^\[\]]*\]")


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
        names.append(Declared(symbol.name, kind, symbol.line, symbol, item.role))
    return names


def _declared_names(roled_file) -> list:
    """Every name the file's author chose: its symbols, then the variables and parameters its
    extractor declares."""
    names = _symbol_names(roled_file)
    # A top-level `const load = () => {}` is already a function symbol.
    symbol_lines = {(name.name, name.line) for name in names}
    return names + [Declared(declared.name, declared.kind, declared.line, owner=declared.owner)
                    for declared in roled_file.declarations
                    if (declared.name, declared.line) not in symbol_lines]



# --- The rules ---------------------------------------------------------------------------------

def _is_exempt(name: Declared) -> bool:
    """A throwaway `_`, or a parameter a language or framework names."""
    return not name.name.strip("_") or (name.kind == "parameter" and name.name in DICTATED_PARAMETERS)


def _is_vague(name: Declared, type_names: frozenset) -> bool:
    if name.kind in ("variable", "parameter"):
        # An `item` holding the project's own `Item` speaks its vocabulary.
        word = name.name.lower()
        return word in VAGUE_NAMES and not (word in _OWNABLE_VAGUE_NAMES and word in type_names)
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


def _without_suffix(name: str, suffix: str) -> str:
    """`handler_new` -> `handler`, `getUserNew` -> `getUser`."""
    return name[:-len(suffix)].rstrip("_")


def _is_numbered(name: Declared, function_names: frozenset) -> bool:
    core = name.name.strip("_")
    if len(core) < MIN_NAME_LENGTH or core.upper() == core:
        return False        # too-short owns a short name; a constant's digits name its value
    words = structure_findings.split_identifier(name.name)
    if len(words) < 2:
        return False
    last = words[-1]
    if last.isdigit():
        is_version = words[-2] == "v" and len(words) >= 3
        term = "".join(words[-3:]) if is_version else words[-2] + last      # `mobilenet_v2`
        is_api_version = is_version and bool(_API_WORDS.intersection(words))
        return not (len(last) > MAX_COPY_NUMBER_DIGITS or _TERM_DIGITS.fullmatch(term) or is_api_version)
    if last not in COPY_SUFFIXES or words[0] in _PREDICATE_WORDS \
            or " ".join(words[-2:]) in _TERMS_ENDING_IN_A_SUFFIX:
        return False
    if last == "copy" and words[-2] in _COPY_OPERATIONS:
        return False
    # A noun before the suffix makes a copy (`process_order_new`, `getUserNew`, `UserNew`); right
    # after a verb the suffix is its object (`create_new`, `mark_as_new`, `StartNew`).
    content = [word for word in words if word not in _FILLER_WORDS]
    if name.kind == "class":
        return len(content) >= 3 or (len(content) == 2 and content[0] not in _VERBS_TAKING_A_SUFFIX)
    if name.kind not in ("function", "method"):
        return False        # a variable's old, new, or final value describes it
    beside_original = _without_suffix(name.name, last) in function_names
    if last == "copy":
        return beside_original      # else the copy is what it makes: `createLocalCopy`
    # A function opens with its verb; beside its unsuffixed original, it is a copy all the same.
    return len(content) >= 3 or beside_original


def _base_names(symbol, language: str) -> list:
    """The names a class declaration writes after its own: its bases, interfaces, and traits."""
    declared = re.search(r"\b" + re.escape(symbol.name) + r"\b", symbol.context)
    if declared is None:
        return []
    header = symbol.context[declared.end():]
    if language == "python":
        return _python_bases(header.lstrip())
    return _NAME_TOKEN.findall(re.split(r"[{;]", header, maxsplit=1)[0])


def _python_bases(header: str) -> list:
    """Each base a Python class header names, as its last dotted segment: `admin.ModelAdmin` is
    `ModelAdmin`, `Repository[Order]` is `Repository`, and `metaclass=ABCMeta` is no base.

    `class Name(Base): pass` puts a body on the same line, so only the parentheses name bases,
    and a long list of them may run past the lines the context holds."""
    if not header.startswith("("):
        return []
    closing = header.find(")")
    listed = header[1:closing] if closing >= 0 else header[1:]
    while _SUBSCRIPT.search(listed):        # innermost first: `Mapping[str, List[int]]`
        listed = _SUBSCRIPT.sub("", listed)
    bases = []
    for expression in listed.split(","):
        dotted = _DOTTED_NAME.match(expression.strip())
        if dotted and "=" not in expression:
            bases.append(dotted.group().split(".")[-1])
    return bases


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


def _is_verb_class(name: Declared, language: str, home_role: Optional[str]) -> bool:
    """A class named like an action, unless its role is one: a Laravel action or listener, a job."""
    if not _is_class_like(name) or home_role in ACTION_ROLES or name.role in ACTION_ROLES:
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
    if accepted is None or (name.kind in ("function", "method") and _has_dictated_casing(name.name)):
        return False
    casing = _casing_of(name.name)
    return casing is not None and casing not in accepted


def _is_majority(agreeing: int, total: int) -> bool:
    return total >= MAJORITY_MIN_NAMES and agreeing > MAJORITY_SHARE * total


def _project_casing(files, declared: dict) -> dict:
    """language -> kind -> accepted casings: the language's own, unless most of the project's
    function and method names in that language follow another casing the language rejects, as
    WordPress PHP follows snake_case. Then that casing is the one expected. Only the kinds a
    language judges vote: PHP's global helper functions do not set its methods' casing."""
    votes = defaultdict(Counter)
    for roled_file in files:
        judged_kinds = {"function", "method"} & set(LANGUAGE_CASING.get(roled_file.language, ()))
        for name in declared[roled_file.path]:
            if name.kind in judged_kinds and not _has_dictated_casing(name.name):
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


def _is_structural(base: str) -> bool:
    return base in STRUCTURAL_BASES or base.endswith(_STRUCTURAL_BASE_SUFFIXES)


def _framework_classes(files) -> frozenset:
    """The project's Python classes derived from a framework's: a base, directly or through the
    project's own classes, that lies outside the project and is no structural base. The framework
    names their hook methods and those methods' parameters (`ModelAdmin.save_model(self, request,
    obj, ...)`, `JSONEncoder.default(self, o)`, Qt's `closeEvent`, unittest's `setUp`)."""
    bases_of = defaultdict(set)
    for roled_file in files:
        if roled_file.language == "python":
            for item in roled_file.symbols:
                if item.symbol.kind in ("class", "protocol"):
                    bases_of[item.symbol.name].update(_base_names(item.symbol, "python"))
    derived = {name for name, bases in bases_of.items()
               if any(base not in bases_of and not _is_structural(base) for base in bases)}
    inheriting = {name for name, bases in bases_of.items() if name not in derived and bases & derived}
    while inheriting:
        derived |= inheriting
        inheriting = {name for name, bases in bases_of.items() if name not in derived and bases & derived}
    return frozenset(derived)


def _overrides_a_framework(name: Declared, framework_classes: frozenset) -> bool:
    """A method of a framework class, or a parameter of one."""
    if name.kind == "parameter":
        return name.owner in framework_classes
    return name.kind == "method" and name.symbol.parent in framework_classes


def _rules_broken(name: Declared, roled_file, conventions: ProjectConventions,
                  framework_classes: frozenset) -> list:
    if _is_exempt(name):
        return []
    language = roled_file.language
    overrides = _overrides_a_framework(name, framework_classes)
    checks = (
        ("vague", not overrides and _is_vague(name, conventions.type_names)),
        ("encoded", _is_encoded(name, language, conventions.i_prefix_families)),
        ("numbered", _is_numbered(name, conventions.function_names)),
        ("noise-word", _is_noise_word(name, language)),
        ("verb-class", _is_verb_class(name, language, roled_file.home_role)),
        ("too-short", not overrides and _is_too_short(name)),
        ("convention", not overrides and _breaks_convention(name, conventions.casing.get(language, {}))),
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


def _project_findings(sources, roles) -> list:
    """The naming findings of one project's production files, judged by its own conventions."""
    declared = {roled_file.path: _declared_names(roled_file) for roled_file in sources}
    function_names = frozenset(name.name for names in declared.values() for name in names
                               if name.kind in ("function", "method"))
    conventions = ProjectConventions(_project_casing(sources, declared), _project_type_names(sources),
                                     _i_prefix_families(sources), function_names)
    framework_classes = _framework_classes(sources)
    found = []
    for roled_file in sources:
        overridable = framework_classes if roled_file.language == "python" else frozenset()
        judged = [(name, _rules_broken(name, roled_file, conventions, overridable))
                  for name in declared[roled_file.path]]
        mismatch = _file_mismatch(roled_file)
        if mismatch is not None:
            judged.append((mismatch, ["file-mismatch"]))
        for name, rules in judged:
            exempt = roles.is_ignored_name(name.name) or roles.accepts(roled_file.path, name.name)
            if rules and not exempt:
                found += [_finding(rule, name, roled_file.path) for rule in rules]
    return found


def find_names(files, roles, project_roots=()) -> list:
    """Names in production files that break a naming rule, each finding citing the rule.

    files are roled files, carrying their symbols and declarations. `project_roots` are the
    folders holding a manifest: each project of a monorepo keeps its own casing and vocabulary.
    Test files, names an `ignore-name` pattern matches, and files or symbols the project
    `accept`s are exempt; the map passes no generated file.
    """
    projects = defaultdict(list)
    for roled_file in files:
        if not roled_file.is_test:
            projects[structure_findings.project_of(roled_file.path, project_roots)].append(roled_file)
    found = [finding for sources in projects.values() for finding in _project_findings(sources, roles)]
    return sorted(found, key=lambda item: (item["path"], item["line"], item["rule"], item["name"]))
