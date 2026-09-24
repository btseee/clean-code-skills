#!/usr/bin/env python3
"""Which role a file and each of its symbols plays, from clean-roles declarations.

A role is a kind of responsibility with a conventional home: middleware lives
with middleware, controllers with controllers. Conventions are declared, not
hard-coded, in fenced `clean-roles` blocks: the generic block in
references/framework-map.md, one block per framework pack, and optionally the
project's own .clean/roles.md. The project's declarations win, then the packs in
the order detect_stack lists them, then the generic block.

    role <name> = <glob>[, <glob>...]      files matching are homes for <name>
    name <name> [<exts>] = <regex>         symbol names matching have role <name>
    signal <name> [<exts>] = <regex>       declaration context matching has role <name>
    allow <home> = <role>[, <role>...]     symbols of these roles may live in a <home> file
    accept <glob> [= <symbol>[, ...]]      a recorded exception: matching files, or only the
                                           listed symbols in them, are never misplaced or mixed
    ignore-name = <regex>                  names left out of clash and synonym findings

The allow statements of every source apply together. An accept glob matches the
path from the repository root; it belongs in the project's .clean/roles.md, beside
the decision that justifies it.

Standard library only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple, Optional

from source import files as project_files

BLOCK = re.compile(r"```clean-roles[ \t]*\n(.*?)```", re.S)
_STATEMENT = re.compile(r"^(?P<kind>role|name|signal)[ \t]+(?P<role>[^\s\[=]+)[ \t]*"
                        r"(?:\[(?P<suffixes>[^\]]*)\])?[ \t]*=[ \t]*(?P<value>.+)$")
_IGNORE = re.compile(r"^ignore-name[ \t]*=[ \t]*(?P<value>.+)$")
_ALLOW = re.compile(r"^allow[ \t]+(?P<home>[^\s=]+)[ \t]*=[ \t]*(?P<roles>.*\S)$")
_ACCEPT = re.compile(r"^accept[ \t]+(?P<glob>[^\s=]+)(?:[ \t]*=[ \t]*(?P<symbols>.*\S))?$")
_ROLE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

GENERIC_ROLES = "references/framework-map.md"
PROJECT_ROLES = ".clean/roles.md"


class RolesError(Exception):
    """A clean-roles declaration could not be read."""


class Statement(NamedTuple):
    kind: str
    role: Optional[str]
    suffixes: tuple
    value: object
    source: str
    scope: tuple = ()           # project folders the statement speaks for; empty means everywhere

    def _folder_of(self, relative_path: str) -> Optional[str]:
        folders = [folder for folder in self.scope if relative_path.startswith(folder + "/")]
        return max(folders, key=len) if folders else None

    def applies_to(self, relative_path: Optional[str]) -> bool:
        return not self.scope or relative_path is None or self._folder_of(relative_path) is not None

    def project_path(self, relative_path: str) -> str:
        """The path as seen from the statement's own project folder, where its globs start."""
        folder = self._folder_of(relative_path) if self.scope else None
        return relative_path[len(folder) + 1:] if folder else relative_path


def _compile(pattern: str, where: str) -> re.Pattern:
    try:
        return re.compile(pattern)
    except re.error as error:
        raise RolesError(f"{where}: invalid regex {pattern!r}: {error}") from error


def _role_name(role: str, where: str) -> str:
    if not _ROLE_NAME.match(role):
        raise RolesError(f"{where}: role names are lowercase words joined by hyphens, "
                         f"not {role!r}")
    return role


def _split(raw: str) -> tuple:
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _parse_statement(line: str, where: str) -> Statement:
    ignored = _IGNORE.match(line)
    if ignored:
        return Statement("ignore-name", None, (), _compile(ignored.group("value"), where), where)
    allowed = _ALLOW.match(line)
    guests = _split(allowed.group("roles")) if allowed else ()
    if guests:
        return Statement("allow", _role_name(allowed.group("home"), where), (),
                         tuple(_role_name(role, where) for role in guests), where)
    accepted = _ACCEPT.match(line)
    symbols = _split(accepted.group("symbols") or "") if accepted else ()
    if accepted and (accepted.group("symbols") is None or symbols):
        return Statement("accept", None, (), (accepted.group("glob"), symbols), where)
    parsed = _STATEMENT.match(line)
    if parsed is None:
        raise RolesError(f"{where}: cannot parse {line!r}")
    role = _role_name(parsed.group("role"), where)
    if parsed.group("kind") == "role":
        if parsed.group("suffixes") is not None:
            raise RolesError(f"{where}: a role statement takes globs, not an extension list")
        return Statement("role", role, (), _split(parsed.group("value")), where)
    suffixes = tuple(suffix.lstrip(".").lower() for suffix in _split(parsed.group("suffixes") or ""))
    return Statement(parsed.group("kind"), role, suffixes, _compile(parsed.group("value"), where),
                     where)


def parse_roles(text: str, source: str) -> list:
    """The statements in text's clean-roles block; [] when there is none."""
    match = BLOCK.search(text)
    if match is None:
        return []
    first_line = text[:match.start(1)].count("\n") + 1
    statements = []
    for offset, raw in enumerate(match.group(1).split("\n")):
        line = raw.strip()
        if line and not line.startswith("#"):
            statements.append(_parse_statement(line, f"{source}:{first_line + offset}"))
    return statements


class Home(NamedTuple):
    role: Optional[str]
    by_name: bool       # only a file-name glob (`**/*Service.*`) grants it, never a folder glob
    glob: Optional[str] = None      # the winning glob, as its statement writes it


class Roles:
    """Every declared convention, highest precedence first."""

    def __init__(self, statements):
        self.statements = list(statements)

    def home(self, relative_path: str) -> Home:
        """The role a file's location promises: the most specific matching glob.

        A file-name glob makes the file a home, but not its folder: `app/orders/page.tsx`
        is a component, while `app/orders/` is a route. A folder glob of the same role
        still counts when a file-name glob outweighs it, as in `services/user.service.ts`.
        """
        best_key = None
        best_role = None
        best_glob = None
        folder_roles = set()
        for index, statement in enumerate(self.statements):
            if statement.kind != "role" or not statement.applies_to(relative_path):
                continue
            project_path = statement.project_path(relative_path)
            for glob in statement.value:
                if project_files.glob_match(glob, project_path):
                    if glob.endswith("/**"):
                        folder_roles.add(statement.role)
                    key = (project_files.literal_weight(glob), -index)
                    if best_key is None or key > best_key:
                        best_key, best_role, best_glob = key, statement.role, glob
        return Home(best_role, best_role is not None and best_role not in folder_roles, best_glob)

    def home_role(self, relative_path: str) -> Optional[str]:
        return self.home(relative_path).role

    def intrinsic(self, name: str, context: str, suffix: str,
                  relative_path: Optional[str] = None) -> tuple:
        """(role, signal_only): the role a symbol's own declaration shows, whatever file it
        sits in, and whether only a declaration signal shows it, never the name."""
        suffix = suffix.lstrip(".").lower()
        by_signal = self._first_role("signal", context, suffix, relative_path)
        by_name = self._first_role("name", name, suffix, relative_path)
        role = by_signal or by_name
        return role, by_signal is not None and by_name != by_signal

    def intrinsic_role(self, name: str, context: str, suffix: str,
                       relative_path: Optional[str] = None) -> Optional[str]:
        """The role a symbol's own declaration shows: signals beat names."""
        return self.intrinsic(name, context, suffix, relative_path)[0]

    def _first_role(self, kind: str, text: str, suffix: str, relative_path: Optional[str]):
        for statement in self.statements:
            if statement.kind != kind or not statement.applies_to(relative_path):
                continue
            if statement.suffixes and suffix not in statement.suffixes:
                continue
            if statement.value.search(text):
                return statement.role
        return None

    def allows(self, home_role: str, role: str, relative_path: Optional[str] = None) -> bool:
        """Whether a symbol of role may live in a home of home_role: a Context module
        holds its Provider and its hook."""
        return any(statement.kind == "allow" and statement.role == home_role
                   and role in statement.value and statement.applies_to(relative_path)
                   for statement in self.statements)

    def is_guest(self, role: str, relative_path: Optional[str] = None) -> bool:
        """Whether some convention lets role live in another role's home, as Express lets
        middleware-shaped handlers live in controllers."""
        return any(statement.kind == "allow" and role in statement.value
                   and statement.applies_to(relative_path) for statement in self.statements)

    def accepts(self, relative_path: str, symbol_name: str) -> bool:
        """Whether a recorded exception covers the symbol, or its whole file."""
        for statement in self.statements:
            if statement.kind != "accept" or not statement.applies_to(relative_path):
                continue
            glob, symbols = statement.value
            if project_files.glob_match(glob, relative_path) and (not symbols or symbol_name in symbols):
                return True
        return False

    def is_ignored_name(self, name: str) -> bool:
        return any(statement.value.search(name) for statement in self.statements
                   if statement.kind == "ignore-name")

    def home_globs(self, role: str, relative_path: Optional[str] = None) -> list:
        """The globs that are homes for role, as seen from the repository root."""
        globs = []
        for statement in self.statements:
            if statement.kind != "role" or statement.role != role:
                continue
            if not statement.applies_to(relative_path):
                continue
            folder = statement._folder_of(relative_path) if statement.scope and relative_path else None
            globs += [glob if folder is None or glob.startswith("**/") else f"{folder}/{glob}"
                      for glob in statement.value]
        return globs


def load_roles(skill_root: Path, packs, project_root: Path, scopes=None) -> Roles:
    """Project roles, then each pack's, then the generic conventions.

    `scopes` maps a pack to the folders its framework lives in, so in a monorepo the
    Flutter pack's `pages/` never claims the React app's `pages/`.
    """
    sources = [(Path(project_root) / PROJECT_ROLES, PROJECT_ROLES, ())]
    for pack in packs:
        relative = pack if pack.startswith("references/") else "references/" + pack
        folders = tuple((scopes or {}).get(relative, ()))
        sources.append((Path(skill_root) / relative, relative, () if "" in folders else folders))
    sources.append((Path(skill_root) / GENERIC_ROLES, GENERIC_ROLES, ()))
    statements = []
    for path, label, scope in sources:
        if path.is_file():
            statements += [statement._replace(scope=scope) for statement in
                           parse_roles(path.read_text(encoding="utf-8", errors="replace"), label)]
    return Roles(statements)


class RoledSymbol(NamedTuple):
    symbol: object
    role: Optional[str]
    signal_only: bool = False     # a declaration signal shows the role; the name does not


class RoledFile(NamedTuple):
    path: str
    language: str
    suffix: str
    home_role: Optional[str]
    is_test: bool
    symbols: list
    purpose: str
    lines: int
    types: int
    abstract_types: int
    home_by_name: bool = False    # the home comes from the file's name, so its folder is none


def assign(file_symbols, roles: Roles, is_test: bool) -> RoledFile:
    """A file's home role, and an intrinsic role for each of its top-level symbols."""
    suffix = Path(file_symbols.path).suffix.lower().lstrip(".")
    symbols = [
        RoledSymbol(symbol, *roles.intrinsic(symbol.name, symbol.context, suffix, file_symbols.path))
        if symbol.parent is None else RoledSymbol(symbol, None)
        for symbol in file_symbols.symbols
    ]
    home = roles.home(file_symbols.path)
    return RoledFile(
        path=file_symbols.path,
        language=file_symbols.language,
        suffix=suffix,
        home_role=home.role,
        is_test=is_test,
        symbols=symbols,
        purpose=file_symbols.purpose,
        lines=file_symbols.lines,
        types=file_symbols.types,
        abstract_types=file_symbols.abstract_types,
        home_by_name=home.by_name,
    )
