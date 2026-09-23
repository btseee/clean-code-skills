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
    ignore-name = <regex>                  names left out of clash and synonym findings

Standard library only.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple, Optional

import project_files

BLOCK = re.compile(r"```clean-roles[ \t]*\n(.*?)```", re.S)
_STATEMENT = re.compile(r"^(?P<kind>role|name|signal)[ \t]+(?P<role>[^\s\[=]+)[ \t]*"
                        r"(?:\[(?P<suffixes>[^\]]*)\])?[ \t]*=[ \t]*(?P<value>.+)$")
_IGNORE = re.compile(r"^ignore-name[ \t]*=[ \t]*(?P<value>.+)$")
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


def _compile(pattern: str, where: str) -> re.Pattern:
    try:
        return re.compile(pattern)
    except re.error as error:
        raise RolesError(f"{where}: invalid regex {pattern!r}: {error}") from error


def parse_roles(text: str, source: str) -> list:
    """The statements in text's clean-roles block; [] when there is none."""
    match = BLOCK.search(text)
    if match is None:
        return []
    first_line = text[:match.start(1)].count("\n") + 1
    statements = []
    for offset, raw in enumerate(match.group(1).split("\n")):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{source}:{first_line + offset}"
        ignored = _IGNORE.match(line)
        if ignored:
            statements.append(Statement("ignore-name", None, (),
                                        _compile(ignored.group("value"), where), where))
            continue
        parsed = _STATEMENT.match(line)
        if parsed is None:
            raise RolesError(f"{where}: cannot parse {line!r}")
        role = parsed.group("role")
        if not _ROLE_NAME.match(role):
            raise RolesError(f"{where}: role names are lowercase words joined by hyphens, "
                             f"not {role!r}")
        if parsed.group("kind") == "role":
            if parsed.group("suffixes") is not None:
                raise RolesError(f"{where}: a role statement takes globs, not an extension list")
            globs = tuple(glob.strip() for glob in parsed.group("value").split(",") if glob.strip())
            statements.append(Statement("role", role, (), globs, where))
            continue
        suffixes = tuple(suffix.strip().lstrip(".").lower()
                         for suffix in (parsed.group("suffixes") or "").split(",") if suffix.strip())
        statements.append(Statement(parsed.group("kind"), role, suffixes,
                                    _compile(parsed.group("value"), where), where))
    return statements


class Roles:
    """Every declared convention, highest precedence first."""

    def __init__(self, statements):
        self.statements = list(statements)

    def home_role(self, relative_path: str) -> Optional[str]:
        """The role a file's location promises: the most specific matching glob."""
        best_key = None
        best_role = None
        for index, statement in enumerate(self.statements):
            if statement.kind != "role":
                continue
            for glob in statement.value:
                if project_files.glob_match(glob, relative_path):
                    key = (project_files.literal_weight(glob), -index)
                    if best_key is None or key > best_key:
                        best_key, best_role = key, statement.role
        return best_role

    def intrinsic_role(self, name: str, context: str, suffix: str) -> Optional[str]:
        """The role a symbol's own declaration shows, whatever file it sits in."""
        suffix = suffix.lstrip(".").lower()
        for kind, text in (("signal", context), ("name", name)):
            for statement in self.statements:
                if statement.kind != kind:
                    continue
                if statement.suffixes and suffix not in statement.suffixes:
                    continue
                if statement.value.search(text):
                    return statement.role
        return None

    def is_ignored_name(self, name: str) -> bool:
        return any(statement.value.search(name) for statement in self.statements
                   if statement.kind == "ignore-name")

    def home_globs(self, role: str) -> list:
        return [glob for statement in self.statements
                if statement.kind == "role" and statement.role == role for glob in statement.value]


def load_roles(skill_root: Path, packs, project_root: Path) -> Roles:
    """Project roles, then each pack's, then the generic conventions."""
    sources = [(Path(project_root) / PROJECT_ROLES, PROJECT_ROLES)]
    for pack in packs:
        relative = pack if pack.startswith("references/") else "references/" + pack
        sources.append((Path(skill_root) / relative, relative))
    sources.append((Path(skill_root) / GENERIC_ROLES, GENERIC_ROLES))
    statements = []
    for path, label in sources:
        if path.is_file():
            statements += parse_roles(path.read_text(encoding="utf-8", errors="replace"), label)
    return Roles(statements)


class RoledSymbol(NamedTuple):
    symbol: object
    role: Optional[str]


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


def assign(file_symbols, roles: Roles, is_test: bool) -> RoledFile:
    """A file's home role, and an intrinsic role for each of its top-level symbols."""
    suffix = Path(file_symbols.path).suffix.lower().lstrip(".")
    symbols = [
        RoledSymbol(symbol, roles.intrinsic_role(symbol.name, symbol.context, suffix)
                    if symbol.parent is None else None)
        for symbol in file_symbols.symbols
    ]
    return RoledFile(
        path=file_symbols.path,
        language=file_symbols.language,
        suffix=suffix,
        home_role=roles.home_role(file_symbols.path),
        is_test=is_test,
        symbols=symbols,
        purpose=file_symbols.purpose,
        lines=file_symbols.lines,
        types=file_symbols.types,
        abstract_types=file_symbols.abstract_types,
    )
