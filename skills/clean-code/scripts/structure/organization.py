#!/usr/bin/env python3
"""Whether each folder holds one concept: families, junk drawers, flat folders, dead and
over-commented files, and the moves that would fix them.

The misplaced finder judges symbols against their roles' homes; these findings judge folders
and whole files. Files that share a concept and import each other belong in a folder named for
it (Common Closure Principle, Screaming Architecture); a folder named for no concept collects
unrelated code (G17); a crowded folder hides its groups (CCP, CRP); a file nothing reaches may
be dead (G9); a file mostly comments is a candidate for the comment workflow (C1-C5, G12).
plan_moves turns the findings into moves for an audit to confirm. Evidence for judgement,
never a verdict.

Standard library only.
"""

from __future__ import annotations

import posixpath
import re
from collections import Counter, defaultdict
from typing import NamedTuple, Optional

import symbols as project_symbols
from source import files as project_files
from source import lexer as source_lexer
from symbols import model as symbol_model

from . import findings as structure_findings

FAMILY_MINIMUM = 3
FLAT_FOLDER_LIMIT = 15
ONE_KIND_SHARE = 0.75
COMMENT_RATIO = 0.4
COMMENT_MINIMUM = 20

# --- Families -------------------------------------------------------------------------------

# Leading words that say what kind of thing a file holds, never which concept: React's `use`
# hooks, `with` wrappers, accessors, WordPress's `class-` files, test doubles, junk-drawer words.
NO_CONCEPT_TOKENS = project_files.JUNK_DRAWER_NAMES | frozenset({
    "use", "with", "get", "set", "is", "has", "on", "to", "from", "base", "abstract", "default",
    "generic", "class", "interface", "trait", "enum", "test", "tests", "mock", "fake", "stub", "my",
    "new", "old", "the", "init",
})
# Route files frameworks name by convention: `+page.svelte`, `[id].tsx`, `(group)`, `$types`.
_ROUTE_MARKS = "+[($@~"
_INTERFACE_PREFIX = re.compile(r"I(?=[A-Z][a-z])")
# Java, Kotlin, and Scala name package folders in lowercase; C# and PHP namespaces keep their case.
LOWERCASE_PACKAGE_SUFFIXES = frozenset({".java", ".kt", ".kts", ".scala"})


def _inside(folder: str, name: str) -> str:
    return f"{folder}/{name}/" if folder else f"{name}/"


def _leading_token(path: str) -> Optional[str]:
    """The concept a file name opens with, as written: `billing` for `billing_tax.py`, `Billing`
    for `BillingTax.cs`, `User` for `IUserService.cs`; None when the name opens with no concept."""
    stem = posixpath.basename(path).split(".")[0]
    if not stem or stem[0] in _ROUTE_MARKS:
        return None
    if _INTERFACE_PREFIX.match(stem):
        stem = stem[1:]
    words = structure_findings.split_identifier(stem)
    token = words[0] if words else ""
    if len(token) < 2 or token.isdigit() or token in NO_CONCEPT_TOKENS \
            or token in structure_findings.ENTRY_POINT_STEMS:
        return None
    start = stem.lower().find(token)
    return stem[start:start + len(token)]


def _plurals(word: str) -> set:
    forms = {word, word + "s", word + "es"}
    if word.endswith("y"):
        forms.add(word[:-1] + "ies")
    return forms


def _same_word(first: str, second: str) -> bool:
    """Whether two lowercase words are one, singular or plural: `user` and `users`."""
    return first in _plurals(second) or second in _plurals(first)


def _names_a_folder(token: str, folder: str) -> bool:
    """Whether a folder the files already sit in names the token as a word of its name: `users/`
    for `user`, `BusinessProcess/` for `Business`, `Acme.Service/` for `Service`."""
    return any(_same_word(word, token.lower()) for word in structure_findings.split_identifier(folder))


def _largest_connected(members: list, file_imports) -> list:
    """The largest group of members that imports connect, directly or through each other."""
    member_set = set(members)
    neighbours = defaultdict(set)
    for path in members:
        for target in file_imports.get(path, ()):
            if target in member_set and target != path:
                neighbours[path].add(target)
                neighbours[target].add(path)
    largest, seen = [], set()
    for start in sorted(members):
        if start in seen:
            continue
        group, frontier = set(), [start]
        while frontier:
            path = frontier.pop()
            if path not in group:
                group.add(path)
                frontier.extend(neighbours[path] - group)
        seen |= group
        if len(group) > len(largest):
            largest = sorted(group)
    return largest


def find_families(file_imports, paths) -> list:
    """Production files in one folder whose names open with one concept and that import each
    other, with a folder named for the concept to hold them.

    A family is the largest group of such files that one import graph connects, direct or
    through each other, of at least FAMILY_MINIMUM files: a shared name alone is no evidence
    they change together. A header and its source (`Feed.h`, `Feed.m`) count as one file. A
    concept a folder above them is already named for proposes nothing. The folder takes the
    token's casing, lowercased where packages are (LOWERCASE_PACKAGE_SUFFIXES).
    """
    groups = defaultdict(list)
    for path in paths:
        token = None if project_files.is_test_path(path) else _leading_token(path)
        if token:
            groups[(posixpath.dirname(path), token.lower())].append((path, token))
    found = []
    for (folder, lowered), members in groups.items():
        first_path, written = sorted(members)[0]
        if posixpath.splitext(first_path)[1].lower() in LOWERCASE_PACKAGE_SUFFIXES:
            written = lowered
        if len(members) < FAMILY_MINIMUM or _names_a_folder(written, folder):
            continue
        connected = _largest_connected([path for path, _ in members], file_imports)
        units = {posixpath.splitext(path)[0] for path in connected}
        if len(units) >= FAMILY_MINIMUM:
            found.append({"folder": folder, "token": written, "files": connected,
                          "suggestion": _inside(folder, written)})
    return sorted(found, key=lambda item: (item["folder"], item["token"].lower()))


# --- Junk drawers ------------------------------------------------------------------------------

def _single_role(roled_file) -> Optional[str]:
    """The one role a file plays: its home's, else the one its symbols show; None when mixed."""
    if roled_file.home_role:
        return roled_file.home_role
    roles = {item.role for item in structure_findings.role_bearing(roled_file)}
    return roles.pop() if len(roles) == 1 else None


def _nearest_home(role: str, folder: str, homes: dict, project_roots) -> Optional[str]:
    """The home folder of role nearest to folder, in folder's project; None when it has none."""
    project = structure_findings.project_of(folder + "/", project_roots)
    counts = homes.get(role, {})
    candidates = [home for home in counts if home != folder
                  and (not project or home == project or home.startswith(project + "/"))]
    if not candidates:
        return None

    def closeness(home):
        shared = [part for part in posixpath.commonpath([home, folder]).split("/") if part]
        return len(shared), counts[home], -len(home)

    nearest = max(candidates, key=closeness)
    return nearest + "/" if nearest else "./"


def _pluralized(word: str) -> str:
    """A role's conventional folder name: `repository` -> `repositories`, `service` -> `services`."""
    if word.endswith("y") and word[-2:-1] not in ("a", "e", "i", "o", "u"):
        return word[:-1] + "ies"
    return word + ("es" if word.endswith(("s", "x", "ch", "sh")) else "s")


def _drawer_groups(drawer_files, family_of: dict) -> tuple:
    """((by, name) -> paths, unsorted paths): each file by its family, else its one role, else
    the leading name it shares with another file; the rest unsorted."""
    groups = defaultdict(list)
    by_name = defaultdict(list)
    for roled_file in drawer_files:
        token = family_of.get(roled_file.path)
        # Inside its role's home folder, a file is where its role belongs: the drawer's name is what
        # is wrong. A home its file name grants (`**/*Service.*`) says nothing about the folder.
        in_home_folder = roled_file.home_role and not roled_file.home_by_name
        role = None if token or in_home_folder else _single_role(roled_file)
        if token or role:
            groups[("family", token) if token else ("role", role)].append(roled_file.path)
        else:
            by_name[(_leading_token(roled_file.path) or "").lower()].append(roled_file.path)
    unsorted = []
    for name, paths in by_name.items():
        if name and len(paths) >= 2:
            groups[("name", name)] = paths
        else:
            unsorted += paths
    return groups, unsorted


def _rename(folder: str, splits: list) -> Optional[str]:
    """For a drawer of one concept, the folder named for it; None when it holds several, or one
    role that already has a home to move to."""
    if len(splits) != 1 or splits[0]["by"] == "unsorted" or (splits[0]["by"] == "role" and splits[0]["to"]):
        return None
    name = splits[0]["name"]
    return _inside(posixpath.dirname(folder), _pluralized(name) if splits[0]["by"] == "role" else name)


def find_junk_drawers(roled_files, families, project_roots=()) -> list:
    """Folders named for no concept (project_files.JUNK_DRAWER_NAMES) holding two or more
    production files besides a package marker (`__init__.py`, `index.ts`), their files grouped by
    concept, and the folder named for its one concept.

    A family moves to a folder named for it beside the drawer and a role to its nearest home in
    the same project (None when it has none): only these propose moves. A file already inside its
    role's home (`components/helper/`) groups by name, since the drawer's name is what is wrong.
    Files sharing a leading name form a group with no destination; the rest are unsorted, waiting
    for a name. `project_roots` are the folders holding a manifest.
    """
    family_of = {path: family["token"] for family in families for path in family["files"]}
    by_folder = defaultdict(list)
    for roled_file in roled_files:
        folder = posixpath.dirname(roled_file.path)
        is_marker = posixpath.basename(roled_file.path).split(".")[0] in _INDEX_STEMS     # `__init__.py`
        if not roled_file.is_test and not is_marker \
                and posixpath.basename(folder).lower() in project_files.JUNK_DRAWER_NAMES:
            by_folder[folder].append(roled_file)
    # The homes misplaced symbols move to: one definition, so both findings agree on them.
    homes = structure_findings.home_folders(roled_files)
    found = []
    for folder, drawer_files in sorted(by_folder.items()):
        # A folder whose every file an `entry` names is one the framework chose by name: Nuxt's utils/.
        if len(drawer_files) < 2 or all(roled_file.entry for roled_file in drawer_files):
            continue
        groups, unsorted = _drawer_groups(drawer_files, family_of)
        splits = [{"by": by, "name": name, "files": sorted(paths),
                   "to": _inside(posixpath.dirname(folder), name) if by == "family"
                   else _nearest_home(name, folder, homes, project_roots) if by == "role" else None}
                  for (by, name), paths in sorted(groups.items())]
        if unsorted:
            splits.append({"by": "unsorted", "name": None, "files": sorted(unsorted), "to": None})
        found.append({"folder": folder, "splits": splits, "rename": _rename(folder, splits)})
    return found


# --- Flat folders ------------------------------------------------------------------------------

def _of_one_kind(paths: list) -> bool:
    """Whether at least ONE_KIND_SHARE of the files end their names with one word, the kind they
    are: `DateTokenizer.cs`, `OrderController.cs`, `country.api.ts`."""
    kinds = Counter()
    for path in paths:
        words = structure_findings.split_identifier(posixpath.splitext(posixpath.basename(path))[0])
        kinds[words[-1] if words else ""] += 1
    kind, count = kinds.most_common(1)[0]
    return bool(kind) and count >= ONE_KIND_SHARE * len(paths)


def _of_one_role(paths: list, roles: dict) -> bool:
    """Whether at least ONE_KIND_SHARE of the files play one role: a role's home by content."""
    counted = Counter(roles[path] for path in paths if roles.get(path))
    return bool(counted) and counted.most_common(1)[0][1] >= ONE_KIND_SHARE * len(paths)


def find_flat_folders(paths, families, limit=FLAT_FOLDER_LIMIT, roled_files=()) -> list:
    """Folders holding more than limit production files, with the families to group them by.

    A folder whose files are mostly one kind is left out, and so is one without families whose
    files mostly play one role (from roled_files): they form one concept, and nothing groups them.
    """
    by_folder = defaultdict(list)
    for path in paths:
        if not project_files.is_test_path(path):
            by_folder[posixpath.dirname(path)].append(path)
    tokens = defaultdict(list)
    for family in families:
        tokens[family["folder"]].append(family["token"])
    roles = {roled_file.path: _single_role(roled_file) for roled_file in roled_files}
    found = [{"folder": folder, "file_count": len(files), "families": sorted(tokens.get(folder, ()))}
             for folder, files in by_folder.items()
             if len(files) > limit and not _of_one_kind(files)
             and (tokens.get(folder) or not _of_one_role(files, roles))]
    return sorted(found, key=lambda item: (-item["file_count"], item["folder"]))


# --- Unreferenced files -------------------------------------------------------------------------

# Languages whose file-to-file references the map traces: imports it resolves to files, and the
# type names code uses. Elsewhere files reach each other in ways it does not read: Go's package
# folders, Rust's `mod`, Dart's `export` and `part`, Swift's one module, C sources the build
# compiles, scripts run by name.
REFERENCE_TRACED_LANGUAGES = frozenset({"python", "javascript", "typescript", "vue", "svelte",
                                        "java", "kotlin", "scala", "csharp", "php", "ruby"})
# Where code reaches another file through the types it declares, a file declaring none is reached
# through functions the map does not trace: Kotlin extensions, PHP helper files.
_TYPE_TRACED_LANGUAGES = frozenset({"java", "kotlin", "scala", "csharp", "php", "ruby"})
_TRACED_TYPE_KINDS = symbol_model.TYPE_KINDS | {"module"}
_PARTIAL = re.compile(r"\bpartial\b")
# Files a tool loads by name, never through an import: build, lint, and test configuration
# (`vite.config.ts`, `karma.conf.js`, `jest.setup.js`, `.eslintrc.js`, `conftest.py`, `setup.py`),
# type declarations, and stories.
_TOOL_LOADED = re.compile(
    r"(?:^|[._-])(?:config|conf|setup)(?:\.[\w-]+)*\.\w+$|^\.\w+rc\.\w+$|\.d\.ts$|\.stor(?:y|ies)\.|"
    r"^(?:conftest|noxfile|fabfile|gulpfile|gruntfile|setuptests|settings|webpack\.[\w.-]+)\.\w+$",
    re.IGNORECASE)
# Folders whose files a web server hands out as they are, readers study, or people run. The walk
# never enters `bin/` (project_files.SKIP_DIRS), so only `scripts/` holds programs to exempt here.
SERVED_FOLDERS = frozenset({"public", "static", "wwwroot"})
EXAMPLE_FOLDERS = frozenset({"sample", "samples", "example", "examples", "demo", "demos"})
PROGRAM_FOLDERS = frozenset({"scripts"})
_PROGRAM_GUARD = re.compile(
    r"""__name__\s*==\s*['"]__main__['"]"""                         # Python
    r"""|\bstatic\s+(?:async\s+)?[\w<>\[\]]+\s+[Mm]ain\s*\("""      # Java, C#
    r"""|^\s*fun\s+main\s*\(|\bextends\s+App\b"""                     # Kotlin, Scala
    r"""|\brequire\.main\s*===?\s*module\b"""                       # Node
    r"""|__FILE__\s*==\s*\$(?:0|PROGRAM_NAME)\b|\$(?:0|PROGRAM_NAME)\s*==\s*__FILE__""",  # Ruby
    re.MULTILINE)
_INDEX_STEMS = frozenset({"index", "__init__", "mod"})
# Path aliases that stand for a project folder: `@/`, `~/`, `#`, SvelteKit's `$lib`.
_ALIAS_SEGMENTS = frozenset({"@", "@@", "~", "~~", "#", "$lib"})
# Where frameworks find classes by an annotation or a base type (Spring, ASP.NET, Laravel,
# Symfony, Android), a class carrying either is loaded without an import.
FRAMEWORK_FOUND_LANGUAGES = frozenset({"java", "kotlin", "csharp", "php"})
_ANNOTATION = re.compile(r"@(?!interface\b)[A-Za-z_]|^\s*#?\[\s*[A-Za-z_]", re.MULTILINE)
_BASE_CLAUSE = re.compile(r"\b(?:extends|implements)\b|:")
_BRACKETED = re.compile(r"<[^<>]*>|\([^()]*\)")
_TYPE_NAME = re.compile(r"[A-Za-z_][\w.\\]*")


def runs_as_program(text: str) -> bool:
    """Whether a file starts a program: a shebang, a main guard, or a main method."""
    return text.startswith("#!") or bool(_PROGRAM_GUARD.search(text))


def _family(language) -> str:
    return structure_findings.LANGUAGE_FAMILY.get(language, language)


def _segments(module: str) -> list:
    """The names an import walks through, lowercased, with aliases and relative steps dropped:
    `@/widgets/Button.vue` -> widgets, button; `billing.tax` -> billing, tax."""
    module = module.strip().strip("'\"<>").replace("\\", "/")
    if "/" in module:
        parts = module.split("/")
        stem, dot, suffix = parts[-1].rpartition(".")
        if dot and stem and "." + suffix.lower() in project_symbols.SUPPORTED_SUFFIXES:
            parts[-1] = stem
    else:
        parts = re.split(r"[.:]+", module)
    return [part.lower() for part in parts
            if part and part not in (".", "..") and part not in _ALIAS_SEGMENTS]


def _project_names(roled_files) -> set:
    """Every folder name and file stem in the project, lowercased."""
    names = set()
    for roled_file in roled_files:
        parts = roled_file.path.lower().split("/")
        names.update(parts[:-1])
        names.update({posixpath.splitext(parts[-1])[0], parts[-1].split(".")[0]})
    return names


def _imported_names(unresolved_imports, languages: dict, project_names: set) -> tuple:
    """(names, packages), each a language family -> lowercased names: the last segment of every
    unresolved import whose first segment names a project folder or file, and of those in Python,
    where the name may be a package holding the module (`from billing import tax`)."""
    names, packages = defaultdict(set), defaultdict(set)
    for path, modules in unresolved_imports.items():
        family = _family(languages.get(path))
        for module in modules:
            segments = _segments(module)
            if segments and segments[0] in project_names:
                names[family].add(segments[-1])
                if family == "python":
                    packages[family].add(segments[-1])
    return names, packages


def _reached_by_name(roled_file, names: dict, packages: dict) -> bool:
    """Whether an unresolved import in the file's language names it, the folder of its index file,
    or its Python package."""
    family = _family(roled_file.language)
    stem = posixpath.basename(roled_file.path).rsplit(".", 1)[0].lower()
    folder = posixpath.basename(posixpath.dirname(roled_file.path)).lower()
    named = names.get(family, set())
    return (stem in named or (stem in _INDEX_STEMS and folder in named)
            or folder in packages.get(family, set()))


def _base_types(symbol) -> list:
    """The type names a class declaration derives from: `extends A implements B`, `: A(), IB`."""
    declared = re.search(r"\b" + re.escape(symbol.name) + r"\b", symbol.context)
    if declared is None:
        return []
    header = re.split(r"[{;]|\bwhere\b|=>", symbol.context[declared.end():], maxsplit=1)[0]
    unbracketed = None
    while unbracketed != header:
        unbracketed, header = header, _BRACKETED.sub("", header)
    clause = _BASE_CLAUSE.search(header)
    if clause is None:
        return []
    return [re.split(r"[.\\]", name)[-1] for name in _TYPE_NAME.findall(header[clause.start():])
            if name not in ("extends", "implements")]


def _found_by_framework(types: list, declared_types: set) -> bool:
    """Whether a class is annotated (`@Service`, `[ApiController]`, `#[AsCommand]`) or derives
    from a type the project does not declare (`HttpServlet`, `BackgroundService`, `Mailable`)."""
    for symbol in types:
        declared = re.search(r"\b" + re.escape(symbol.name) + r"\b", symbol.context)
        head = symbol.context[:declared.start()] if declared else ""
        if _ANNOTATION.search(head) or any(base not in declared_types for base in _base_types(symbol)):
            return True
    return False


def _reached_without_import(roled_file, declared_types: set) -> bool:
    """Whether something other than an import reaches the file: the toolchain as an entry point
    (an app shell such as `MainActivity` too), a framework through its role, an `entry` line, an
    annotation, or a base type, a tool by its name, a server, a reader, or a person through its
    folder, or, where the map traces types, code it does not read."""
    name = posixpath.basename(roled_file.path)
    stem = name.split(".")[0]
    folders = [folder.lower() for folder in roled_file.path.split("/")[:-1]]
    if stem.lower() in structure_findings.ENTRY_POINT_STEMS or _TOOL_LOADED.search(name) \
            or structure_findings.split_identifier(stem)[:1] == ["main"]:
        return True
    if roled_file.entry or roled_file.home_role or any(item.role for item in roled_file.symbols):
        return True
    if (SERVED_FOLDERS | EXAMPLE_FOLDERS).intersection(folders) \
            or (folders and folders[-1] in PROGRAM_FOLDERS):
        return True
    if roled_file.language not in _TYPE_TRACED_LANGUAGES:
        return False
    types = [item.symbol for item in roled_file.symbols
             if item.symbol.parent is None and item.symbol.kind in _TRACED_TYPE_KINDS]
    if roled_file.language in FRAMEWORK_FOUND_LANGUAGES and _found_by_framework(types, declared_types):
        return True
    # A partial type's other half may live in markup or generated code the map does not read.
    return not types or all(_PARTIAL.search(symbol.context) for symbol in types)


def find_unreferenced(file_imports, roled_files, resolvable_languages, unresolved_imports=None,
                      programs=frozenset()) -> list:
    """Production files nothing imports, in resolvable_languages: possibly unused (G9).

    file_imports maps every file, tests included, to the project files it imports: a file only
    tests import is still used. unresolved_imports maps a file to the imports that named no
    project file; a file in the same language family that one names by its last segment counts
    as imported, when its first segment names a project folder or file. Never judged: tests,
    entry points, programs (files runs_as_program says start one), files holding a role or
    matching an `entry` line, which a framework loads, annotated or framework-derived classes
    (FRAMEWORK_FOUND_LANGUAGES), and files a tool or a server loads by name or folder.
    """
    languages = {roled_file.path: roled_file.language for roled_file in roled_files}
    imported = {target for targets in file_imports.values() for target in targets}
    names, packages = _imported_names(unresolved_imports or {}, languages, _project_names(roled_files))
    declared_types = {item.symbol.name for roled_file in roled_files for item in roled_file.symbols
                      if item.symbol.parent is None and item.symbol.kind in _TRACED_TYPE_KINDS}
    found = []
    for roled_file in roled_files:
        path = roled_file.path
        if roled_file.is_test or roled_file.language not in resolvable_languages \
                or path in imported or path in programs:
            continue
        if _reached_by_name(roled_file, names, packages) \
                or _reached_without_import(roled_file, declared_types):
            continue
        found.append({"path": path})
    return sorted(found, key=lambda finding: finding["path"])


# --- Comment-heavy files -----------------------------------------------------------------------

# Line markers of API documentation, which C#, Rust, Swift, and Dart write as `///` (Rust's
# module docs `//!`); JavaDoc, JSDoc, KDoc, and PHPDoc open a `/**` block, and PowerShell's
# comment-based help a `<#` block. A C header's comments document the API it declares.
DOC_COMMENT_MARKERS = ("///", "//!")
DOC_BLOCKS = {"/**": "*/", "<#": "#>"}
HEADER_SUFFIXES = frozenset({".h", ".hh", ".hpp", ".hxx"})


class _Line(NamedTuple):
    text: str
    is_comment: bool        # holds a comment, neither code nor API documentation


def _header_lines(lines: list) -> set:
    """Indexes of the lines a license or a generator wrote atop the file: its first comment block
    after any shebang, PHP open tag, and blank lines, when that block says so."""
    index = 0
    while index < len(lines) and (not lines[index].text.strip() or lines[index].text.startswith("#!")
                                  or lines[index].text.strip() in ("<?php", "<?")):
        index += 1
    block = []
    while index < len(lines) and lines[index].is_comment:
        block.append(index)
        index += 1
    words = "\n".join(lines[line].text for line in block)
    if symbol_model.LICENSE_WORDS.search(words) or \
            any(marker in words.lower() for marker in project_files.GENERATED_MARKERS):
        return set(block)
    return set()


def _documentation_opener(stripped: str) -> Optional[str]:
    """The documentation block a comment line opens (`/**`, `<#`), never an empty `/**/`."""
    for opener, closer in DOC_BLOCKS.items():
        if stripped.startswith(opener) and not stripped.startswith(opener + closer[-1]):
            return opener
    return None


def _classified_lines(text: str, language: str) -> list:
    """Each line of text, marked when it holds only a comment that is not API documentation."""
    views = source_lexer.strip(text, language)
    lines, closer = [], None        # closer: what ends the documentation block the line is in
    for raw, code, kept in zip(text.split("\n"), views.code.split("\n"), views.no_comments.split("\n")):
        stripped = raw.strip()
        comment_only = bool(stripped) and kept != raw and not code.strip()
        opener = _documentation_opener(stripped) if comment_only and closer is None else None
        documentation = closer is not None or opener is not None or stripped.startswith(DOC_COMMENT_MARKERS)
        if opener is not None:
            closer = None if DOC_BLOCKS[opener] in stripped[len(opener):] else DOC_BLOCKS[opener]
        elif closer is not None and closer in stripped:
            closer = None
        lines.append(_Line(raw, comment_only and not documentation))
    return lines


def _comment_count(text: str, language: str) -> tuple:
    """(comment lines, judged lines): lines holding only a comment, and every non-blank line but
    a shebang and a license or generator header. A Python docstring is a string and an API doc
    comment (`///`, `/** */`) its counterpart: documentation, not comments."""
    lines = _classified_lines(text, language)
    unjudged = _header_lines(lines) | ({0} if lines and lines[0].text.startswith("#!") else set())
    judged = [line for index, line in enumerate(lines) if index not in unjudged and line.text.strip()]
    return sum(1 for line in judged if line.is_comment), len(judged)


def find_comment_heavy(texts_by_path, languages_by_path, ratio=COMMENT_RATIO,
                       minimum=COMMENT_MINIMUM) -> list:
    """Production files whose comment lines are at least ratio of their non-blank lines and at
    least minimum in number: candidates for the comment workflow.

    Test files, generated files, C headers, and languages the lexer does not know are skipped.
    """
    found = []
    for path, text in texts_by_path.items():
        language = languages_by_path.get(path)
        if language not in source_lexer.SYNTAX or project_files.is_test_path(path) \
                or posixpath.splitext(path)[1].lower() in HEADER_SUFFIXES \
                or project_files.is_generated(path, text):
            continue
        comment_lines, judged_lines = _comment_count(text, language)
        if judged_lines and comment_lines >= minimum and comment_lines / judged_lines >= ratio:
            found.append({"path": path, "comment_lines": comment_lines, "nonblank_lines": judged_lines,
                          "ratio": round(comment_lines / judged_lines, 2)})
    return sorted(found, key=lambda item: item["path"])


# --- The move plan -----------------------------------------------------------------------------

def plan_moves(findings) -> list:
    """Moves for the findings that propose one, each {"from": [...], "to", "why"}, why naming the
    finding kind.

    Misplaced code goes to its role's home: its symbols (`path::symbol`) when their file holds
    more, else the whole file. A junk drawer of one concept moves as a folder, renamed for it;
    else its family and role splits move their files. Families move their files together. A file
    moves once, by the first finding in that order. A finding without a destination, or with only
    a description of one (`a file matching **/Data/**`), proposes nothing.
    """
    moves, moved = [], set()

    def move_files(paths, destination, why):
        remaining = [path for path in paths if path not in moved]
        if remaining and _is_destination(destination):
            moved.update(remaining)
            moves.append({"from": remaining, "to": destination, "why": why})

    symbols = defaultdict(list)     # (file, destination) -> the symbols moving there
    for misplaced in findings.get("misplaced", ()):
        if misplaced["symbol"] is None:
            move_files([misplaced["path"]], misplaced["suggestion"], "misplaced")
        elif _is_destination(misplaced["suggestion"]):
            symbols[(misplaced["path"], misplaced["suggestion"])].append(misplaced["symbol"])
    moves += [{"from": [f"{path}::{name}" for name in names], "to": destination, "why": "misplaced"}
              for (path, destination), names in symbols.items()]
    for drawer in findings.get("junk_drawer", ()):
        if drawer["rename"]:
            moved.update(path for split in drawer["splits"] for path in split["files"])
            moves.append({"from": [drawer["folder"] + "/"], "to": drawer["rename"], "why": "junk_drawer"})
            continue
        for split in drawer["splits"]:
            move_files(split["files"], split["to"], "junk_drawer")
    for family in findings.get("family", ()):
        move_files(family["files"], family["suggestion"], "family")
    return moves


def _is_destination(suggestion) -> bool:
    return bool(suggestion) and not any(character.isspace() for character in suggestion)


def without_accepted(found: list, roles) -> list:
    """The findings no recorded exception covers: an `accept` line for the whole file or folder."""
    return [finding for finding in found
            if not roles.accepts(finding.get("path") or finding.get("folder") or "", "")]
