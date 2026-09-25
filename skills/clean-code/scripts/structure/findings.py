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

from source import files as project_files
from symbols import model as symbol_model

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
ROUTE_FOLDERS = frozenset({"pages", "routes", "layouts", "app"})

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
# Maven and Gradle keep JVM sources under a source set, then the package path.
_JVM_SOURCE_SET = re.compile(r"^((?:.+/)?src/(?:main/)?(?:java|kotlin|scala))/")


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


def _unaccepted(roled_file, roles) -> list:
    """The role-bearing symbols no recorded exception (`accept`) covers."""
    return [item for item in role_bearing(roled_file)
            if not roles.accepts(roled_file.path, item.symbol.name)]


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


def home_folders(files) -> dict:
    """role -> the folders a folder glob makes its homes, with their file counts.

    A home granted by a file name is not a folder to move code into: `app/orders/` holds
    a `page.tsx`, and `billing/` a `BillingService.java`, yet both are route or feature folders.
    """
    homes = defaultdict(Counter)
    for roled_file in files:
        if roled_file.home_role and not roled_file.home_by_name and not roled_file.is_test:
            homes[roled_file.home_role][posixpath.dirname(roled_file.path)] += 1
    return homes


def project_of(path: str, project_roots) -> str:
    """The deepest folder holding a manifest that contains path; "" for the repository root."""
    owners = [root for root in project_roots if root and path.startswith(root + "/")]
    return max(owners, key=len) if owners else ""


def _all_folders(files) -> set:
    """Every folder that holds a file, directly or below."""
    folders = set()
    for roled_file in files:
        folder = posixpath.dirname(roled_file.path)
        while folder and folder not in folders:
            folders.add(folder)
            folder = posixpath.dirname(folder)
    return folders


def _cased(name: str, parent: str, folders, language: str) -> str:
    """A new folder's name in the casing of the folders beside it: `Validators` in a
    PascalCase solution, and in C# when nothing sits beside it."""
    initials = [posixpath.basename(folder)[0] for folder in folders
                if posixpath.dirname(folder) == parent and posixpath.basename(folder)[:1].isalpha()]
    upper = sum(1 for initial in initials if initial.isupper())
    pascal = upper * 2 > len(initials) if initials else language == "csharp"
    return symbol_model.pascal_case(name) if pascal else name


def _named_homes(files) -> dict:
    """role -> the files that only a file-name glob makes its homes: `models.py`, `OrderService.java`."""
    named = defaultdict(list)
    for roled_file in files:
        if roled_file.home_role and roled_file.home_by_name and not roled_file.is_test:
            named[roled_file.home_role].append(roled_file.path)
    return named


def _common_folder(paths) -> str:
    """The deepest folder that holds every path."""
    common = []
    for parts in zip(*[posixpath.dirname(path).split("/") for path in paths]):
        if len(set(parts)) != 1:
            break
        common.append(parts[0])
    return "/".join(common)


class _Destinations:
    """Where a symbol of one role should move, judged from the homes the project already has.

    A home in another project is never an option: moving code across a manifest boundary
    is a design decision, never a tidy-up.
    """

    def __init__(self, files, roles, project_roots):
        self.roles = roles
        self.project_roots = project_roots
        self.folder_homes = home_folders(files)
        self.named_homes = _named_homes(files)
        self.folders = _all_folders(files)
        self.sources = [roled_file for roled_file in files if not roled_file.is_test]

    def for_symbol(self, role: str, roled_file) -> Optional[str]:
        """A home file beside it, the nearest home folder, a file named like the role's files
        beside it, or the role's conventional folder, in that order."""
        path = roled_file.path
        here = posixpath.dirname(path)
        project = project_of(path, self.project_roots)

        def in_project(where: str) -> bool:
            return not project or where == project or where.startswith(project + "/")

        named = sorted(home for home in self.named_homes.get(role, ()) if in_project(home))
        beside = [home for home in named if posixpath.dirname(home) == here]
        suggestion = self._named_like(beside[0], roled_file) if beside else None
        if suggestion:
            return suggestion
        folders = {folder: count for folder, count in self.folder_homes.get(role, {}).items()
                   if in_project(folder)}
        if folders:
            folder = max(folders, key=lambda name: (_shared_depth(name, here), folders[name], -len(name)))
            return (folder + "/") if folder else "./"
        if named:
            nearest = max(named, key=lambda home: (_shared_depth(posixpath.dirname(home), here), -len(home)))
            suggestion = self._named_like(nearest, roled_file)
            if suggestion:
                return suggestion
        return self._conventional(role, roled_file, project)

    def _named_like(self, home: str, roled_file) -> Optional[str]:
        """A file named as home is, beside roled_file: `shop/orders/models.py`, or a name
        pattern such as `order/*Service.*`. None when roled_file is already named so, and its
        folder, not its name, is the conflict."""
        glob = self.roles.home(home).glob or home
        name = posixpath.basename(glob)
        if project_files.glob_match(name, posixpath.basename(roled_file.path)):
            return None
        here = posixpath.dirname(roled_file.path)
        return f"{here}/{name}" if here else name

    def _conventional(self, role: str, roled_file, project: str) -> Optional[str]:
        """The role's conventional folder, under the language's source root; never a folder
        invented at the repository root."""
        root = self._source_root(roled_file, project)
        globs = self.roles.home_globs(role, roled_file.path)
        for glob in globs:
            conventional = _FOLDER_GLOB.match(glob)
            if conventional and root:
                name = _cased(conventional.group(1), root, self.folders, roled_file.language)
                return f"{root}/{name}/"
            literal = _LITERAL_FOLDER_GLOB.match(glob)
            if literal:
                return literal.group(1) + "/"
        return f"a file matching {globs[0]}" if globs else None

    def _source_root(self, roled_file, project: str) -> str:
        """`src`, `web/src`, the project folder, or a JVM source set's base package such as
        `src/main/java/com/acme/shop`; "" for the repository root."""
        source_set = _JVM_SOURCE_SET.match(roled_file.path)
        if source_set:
            family = LANGUAGE_FAMILY.get(roled_file.language, roled_file.language)
            return _common_folder([source.path for source in self.sources
                                   if source.path.startswith(source_set.group(1) + "/")
                                   and LANGUAGE_FAMILY.get(source.language, source.language) == family])
        source_root = _source_root(roled_file.path)
        return source_root if len(source_root) > len(project) else project


def _sibling_home(path: str, folders) -> Optional[str]:
    """A home folder beside the file, as `src/guards/` is beside `src/guards.ts`.

    A distant home is not evidence: feature folders keep a role's files together on
    purpose, far from any shared folder for that role.
    """
    here = posixpath.dirname(path)
    beside = [folder for folder in folders if posixpath.dirname(folder) == here]
    return max(beside, key=lambda folder: folders[folder]) if beside else None


def find_misplaced(files, roles, project_roots=()) -> list:
    """Symbols whose role differs from where they live, with a suggested home.

    A role the home `allow`s, and a symbol or file the project `accept`s, is not reported.
    `project_roots` are the folders holding a manifest; a suggestion stays in its file's project.
    """
    destinations = _Destinations(files, roles, project_roots)
    found = []
    for roled_file in files:
        if roled_file.is_test:
            continue
        bearing = _unaccepted(roled_file, roles)
        if not bearing:
            continue
        if roled_file.home_role:
            for item in bearing:
                if item.role != roled_file.home_role and \
                        not roles.allows(roled_file.home_role, item.role, roled_file.path):
                    found.append({
                        "path": roled_file.path, "line": item.symbol.line,
                        "symbol": item.symbol.name, "role": item.role,
                        "home_role": roled_file.home_role,
                        "suggestion": destinations.for_symbol(item.role, roled_file),
                    })
            continue
        # A role only a signature shows, which the conventions also let live in other homes
        # (Express 4 handlers take next like middleware), is too weak to move a whole file.
        if any(item.signal_only and roles.is_guest(item.role, roled_file.path) for item in bearing):
            continue
        distinct = {item.role for item in bearing}
        if len(distinct) == 1 and not _is_entry_point(roled_file.path):
            role = distinct.pop()
            sibling = _sibling_home(roled_file.path, destinations.folder_homes.get(role, {}))
            if sibling is not None:
                found.append({
                    "path": roled_file.path, "line": 1, "symbol": None, "role": role,
                    "home_role": None, "suggestion": sibling + "/",
                })
    return sorted(found, key=lambda item: (item["path"], item["line"]))


def find_mixed(files, roles) -> list:
    """Files with no conventional home whose symbols answer to two or more roles."""
    found = []
    for roled_file in files:
        if roled_file.is_test or roled_file.home_role:
            continue
        by_role = defaultdict(list)
        for item in _unaccepted(roled_file, roles):
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
    """A SvelteKit `+page`, or an `index`/`default`/`error` file under a route folder."""
    stem = posixpath.basename(path).split(".")[0]
    in_route_folder = any(folder in ROUTE_FOLDERS for folder in path.split("/")[:-1])
    return symbol.kind == "component" and (
        stem.startswith("+") or (stem.lower() in PATH_NAMED_STEMS and in_route_folder))


def find_name_clashes(files, roles, project_roots=()) -> list:
    """One public type name, or one global function name, declared in several files.

    Only within one project: two services of a solution may each own a `Database`.
    """
    declared = defaultdict(list)
    for roled_file in files:
        if roled_file.is_test:
            continue
        family = LANGUAGE_FAMILY.get(roled_file.language, roled_file.language)
        project = project_of(roled_file.path, project_roots)
        for item in roled_file.symbols:
            symbol = item.symbol
            if not _can_clash(symbol, roled_file.language) or roles.is_ignored_name(symbol.name) \
                    or _named_by_path(symbol, roled_file.path):
                continue
            declared[(project, family, symbol.name)].append(
                {"path": roled_file.path, "line": symbol.line, "kind": symbol.kind})
    found = []
    for (_, family, name), members in declared.items():
        if len({member["path"] for member in members}) >= 2:
            found.append({"name": name, "language": family, "members": members})
    return sorted(found, key=lambda item: (item["name"], item["language"], item["members"][0]["path"]))


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
