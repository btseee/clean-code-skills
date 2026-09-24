#!/usr/bin/env python3
"""What the structure map reports: code in the wrong place, and knowledge in two.

Every finding is evidence for a judgement, never a verdict. A misplaced symbol
may be a deliberate exception; two identical functions may belong to different
actors and rightly change apart. The map shows the candidates; the reader
decides, citing a decision when the answer is "leave it".

Standard library only.
"""

from __future__ import annotations

import posixpath
import re
from collections import Counter, defaultdict
from typing import Optional

# Abstractions legitimately live beside the code that consumes them (the
# Dependency Inversion Principle), so a repository interface in the domain is
# never "misplaced".
ROLE_EXEMPT_KINDS = frozenset({"interface", "type", "enum", "protocol", "trait"})

# Languages that mark what a file exports; elsewhere every top-level symbol counts.
EXPORT_AWARE_LANGUAGES = frozenset({"javascript", "typescript", "python", "go", "rust", "dart",
                                    "vue", "svelte"})

SOURCE_ROOTS = frozenset({"src", "lib", "app", "source", "sources", "pkg", "internal"})

# Files that start a program or a package stay where the toolchain expects them,
# whatever roles they hold.
ENTRY_POINT_STEMS = frozenset({"main", "index", "app", "program", "application", "server",
                               "__main__", "__init__", "manage", "wsgi", "asgi", "mod", "lib"})

# Two `User` classes confuse every reader; two `parse` functions in different modules
# do not, because a module-scoped language keeps them apart. Where every function
# shares one namespace, a repeated function name is a real clash.
CLASHING_KINDS = frozenset({"class", "interface", "enum", "struct", "trait", "protocol",
                            "record", "object", "module", "component", "type"})
GLOBAL_FUNCTION_LANGUAGES = frozenset({"c", "shell", "powershell", "r", "php"})
# Frameworks give route files fixed names (`+page.svelte`, `pages/users/index.vue`). The
# component the scanner names after such a file is known by its path, so it never clashes.
PATH_NAMED_STEMS = frozenset({"index", "default", "error"})

LANGUAGE_FAMILY = {"typescript": "js", "javascript": "js", "vue": "js", "svelte": "js",
                   "java": "jvm", "kotlin": "jvm", "scala": "jvm",
                   "c": "c", "cpp": "c", "objc": "c"}

SYNONYM_GROUPS = {
    "retrieve": ("get", "fetch", "load", "retrieve"),
    "create": ("create", "add", "insert", "make"),
    "update": ("update", "modify", "edit", "change"),
    "delete": ("delete", "remove", "destroy", "erase"),
}
_VERB_GROUP = {verb: group for group, verbs in SYNONYM_GROUPS.items() for verb in verbs}
_TRIVIAL_NOUNS = frozenset({"all", "by", "data", "item", "items", "list", "value", "values",
                            "one", "it", "info", "details", "result", "results", "many"})
_NOUN_ENDS = frozenset({"by", "for", "with", "from", "in", "to", "of", "on", "at", "if", "or",
                        "and", "as"})
_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
_FOLDER_GLOB = re.compile(r"^\*\*/([^*?/]+)/\*\*$")
_LITERAL_FOLDER_GLOB = re.compile(r"^([^*?]+)/\*\*$")


def split_identifier(name: str) -> list:
    """`getHTTPResponse` -> get, http, response; `load_users` -> load, users."""
    words = []
    for part in re.split(r"[_\-\s.]+", name):
        words += _WORD.findall(part)
    return [word.lower() for word in words if word]


def _singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us")):
        return word[:-1]
    return word


def role_bearing(roled_file) -> list:
    """Top-level symbols whose own declaration shows a role, abstractions excepted."""
    return [
        item for item in roled_file.symbols
        if item.role and item.symbol.parent is None
        and item.symbol.kind not in ROLE_EXEMPT_KINDS
        and (item.symbol.exported or roled_file.language not in EXPORT_AWARE_LANGUAGES)
    ]


def _source_root(path: str) -> str:
    """The folder holding a project's sources: `src`, or `web/src` in a monorepo."""
    segments = path.split("/")[:-1]
    for index, segment in enumerate(segments):
        if segment in SOURCE_ROOTS:
            return "/".join(segments[:index + 1])
    return ""


def _shared_depth(folder: str, directory: str) -> int:
    shared = 0
    for mine, theirs in zip(folder.split("/"), directory.split("/")):
        if mine != theirs:
            break
        shared += 1
    return shared


def _is_entry_point(path: str) -> bool:
    return posixpath.basename(path).split(".")[0].lower() in ENTRY_POINT_STEMS


def _home_folders(files) -> dict:
    homes = defaultdict(Counter)
    for roled_file in files:
        if roled_file.home_role and not roled_file.is_test:
            homes[roled_file.home_role][posixpath.dirname(roled_file.path)] += 1
    return homes


def _suggest(role: str, path: str, homes: dict, roles) -> Optional[str]:
    root = _source_root(path)
    folders = homes.get(role)
    if folders:
        # The nearest home, so a monorepo never sends code into another project.
        here = posixpath.dirname(path)
        folder = max(folders, key=lambda name: (_shared_depth(name, here), folders[name], -len(name)))
        return (folder + "/") if folder else "./"
    for glob in roles.home_globs(role, path):
        conventional = _FOLDER_GLOB.match(glob)
        if conventional:
            return (root + "/" if root else "") + conventional.group(1) + "/"
        literal = _LITERAL_FOLDER_GLOB.match(glob)
        if literal:
            return literal.group(1) + "/"
    globs = roles.home_globs(role, path)
    return f"a file matching {globs[0]}" if globs else None


def _sibling_home(path: str, folders) -> Optional[str]:
    """A home folder beside the file, as `src/guards/` is beside `src/guards.ts`.

    A distant home is not evidence: feature folders keep a role's files together on
    purpose, far from any shared folder for that role.
    """
    here = posixpath.dirname(path)
    beside = [folder for folder in folders if posixpath.dirname(folder) == here]
    return max(beside, key=lambda folder: folders[folder]) if beside else None


def find_misplaced(files, roles) -> list:
    """Symbols whose role differs from where they live, with a suggested home."""
    homes = _home_folders(files)
    found = []
    for roled_file in files:
        if roled_file.is_test:
            continue
        bearing = role_bearing(roled_file)
        if not bearing:
            continue
        if roled_file.home_role:
            for item in bearing:
                if item.role != roled_file.home_role:
                    found.append({
                        "path": roled_file.path, "line": item.symbol.line,
                        "symbol": item.symbol.name, "role": item.role,
                        "home_role": roled_file.home_role,
                        "suggestion": _suggest(item.role, roled_file.path, homes, roles),
                    })
            continue
        distinct = {item.role for item in bearing}
        if len(distinct) == 1 and not _is_entry_point(roled_file.path):
            role = distinct.pop()
            sibling = _sibling_home(roled_file.path, homes.get(role, {}))
            if sibling is not None:
                found.append({
                    "path": roled_file.path, "line": 1, "symbol": None, "role": role,
                    "home_role": None, "suggestion": sibling + "/",
                })
    return sorted(found, key=lambda item: (item["path"], item["line"]))


def find_mixed(files) -> list:
    """Files with no conventional home whose symbols answer to two or more roles."""
    found = []
    for roled_file in files:
        if roled_file.is_test or roled_file.home_role:
            continue
        by_role = defaultdict(list)
        for item in role_bearing(roled_file):
            by_role[item.role].append(item.symbol.name)
        if len(by_role) >= 2:
            found.append({"path": roled_file.path,
                          "roles": {role: sorted(names) for role, names in sorted(by_role.items())}})
    return sorted(found, key=lambda item: item["path"])


def _member(roled_file, symbol) -> dict:
    return {"path": roled_file.path, "line": symbol.line, "symbol": symbol.name}


def find_duplicates(files) -> list:
    """Functions whose bodies are identical, or identical but for names and literals."""
    exact = defaultdict(list)
    shape = defaultdict(list)
    for roled_file in files:
        if roled_file.is_test:
            continue
        for item in roled_file.symbols:
            symbol = item.symbol
            if symbol.exact:
                exact[symbol.exact].append((roled_file, symbol))
            if symbol.shape:
                shape[symbol.shape].append((roled_file, symbol))
    found = []
    for members in exact.values():
        if len(members) >= 2:
            found.append({"kind": "identical",
                          "lines": members[0][1].end_line - members[0][1].line + 1,
                          "members": [_member(roled_file, symbol) for roled_file, symbol in members]})
    for members in shape.values():
        if len(members) >= 2 and len({symbol.exact for _, symbol in members}) > 1:
            found.append({"kind": "same shape",
                          "lines": members[0][1].end_line - members[0][1].line + 1,
                          "members": [_member(roled_file, symbol) for roled_file, symbol in members]})
    return sorted(found, key=lambda item: (-item["lines"], item["members"][0]["path"],
                                           item["members"][0]["line"]))


def _can_clash(symbol, language: str) -> bool:
    """Type names clash in any language; function names only where they share one namespace."""
    if symbol.parent is not None or not symbol.exported or len(symbol.name) < 4:
        return False
    return symbol.kind in CLASHING_KINDS or language in GLOBAL_FUNCTION_LANGUAGES


def _named_by_path(symbol, path: str) -> bool:
    stem = posixpath.basename(path).split(".")[0]
    return symbol.kind == "component" and (stem.startswith("+") or stem.lower() in PATH_NAMED_STEMS)


def find_name_clashes(files, roles) -> list:
    """One public type name, or one global function name, declared in several files."""
    declared = defaultdict(list)
    for roled_file in files:
        if roled_file.is_test:
            continue
        family = LANGUAGE_FAMILY.get(roled_file.language, roled_file.language)
        for item in roled_file.symbols:
            symbol = item.symbol
            if not _can_clash(symbol, roled_file.language) or roles.is_ignored_name(symbol.name) \
                    or _named_by_path(symbol, roled_file.path):
                continue
            declared[(family, symbol.name)].append(
                {"path": roled_file.path, "line": symbol.line, "kind": symbol.kind})
    found = []
    for (family, name), members in declared.items():
        if len({member["path"] for member in members}) >= 2:
            found.append({"name": name, "language": family, "members": members})
    return sorted(found, key=lambda item: (item["name"], item["language"]))


def _noun(words: list) -> str:
    noun = []
    for word in words:
        if word in _NOUN_ENDS:
            break
        noun.append(_singular(word))
    return " ".join(noun)


def find_synonyms(files, roles) -> list:
    """One concept reached through several verbs of the same meaning (one word per concept)."""
    usages = defaultdict(lambda: defaultdict(list))
    for roled_file in files:
        if roled_file.is_test:
            continue
        for item in roled_file.symbols:
            symbol = item.symbol
            if symbol.kind not in {"function", "method"} or roles.is_ignored_name(symbol.name):
                continue
            words = split_identifier(symbol.name)
            if len(words) < 2 or words[0] not in _VERB_GROUP:
                continue
            noun = _noun(words[1:])
            if not noun or noun in _TRIVIAL_NOUNS:
                continue
            usages[(_VERB_GROUP[words[0]], noun)][words[0]].append(_member(roled_file, symbol))
    found = []
    for (group, noun), verbs in usages.items():
        if len(verbs) >= 2:
            found.append({"noun": noun, "group": group,
                          "verbs": {verb: entries for verb, entries in sorted(verbs.items())}})
    return sorted(found, key=lambda item: (-len(item["verbs"]),
                                           -sum(len(entries) for entries in item["verbs"].values()),
                                           item["noun"]))
