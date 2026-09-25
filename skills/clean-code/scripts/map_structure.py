#!/usr/bin/env python3
"""Map every source file: what it declares, which role it plays, whether it belongs.

One walk reads each file once. Symbols come from the symbols package, roles from
the clean-roles conventions (the project's .clean/roles.md, then the framework
packs, then the generic block), dependencies from source.resolution. The result
is evidence for judgement -- misplaced, mixed, duplicated, clashing,
synonymous, and badly named code, component metrics, cycles, file families,
junk drawers, flat folders, unreferenced and comment-heavy files, and the moves
they propose -- never a verdict.

Standard library only. Reads files; writes only .clean/structure.md and
.clean/structure.json, and only with --write.

Usage:
    python map_structure.py                   # summary for the current project
    python map_structure.py --path src/api    # the rows and findings for one folder
    python map_structure.py --changed         # findings for the files git reports as changed
    python map_structure.py --write           # save .clean/structure.md and .json
    python map_structure.py --json            # the full map as JSON
"""

from __future__ import annotations

import argparse
import json
import posixpath
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import NamedTuple

import detect_stack
import symbols as project_symbols
from source import files as project_files
from source import imports as project_imports
from source import resolution as import_resolution
from structure import findings as structure_findings
from structure import metrics as component_metrics
from structure import naming as structure_naming
from structure import organization as structure_organization
from structure import report as structure_report
from structure import roles as structure_roles

SCHEMA_VERSION = 1
SKILL_ROOT = Path(__file__).resolve().parent.parent


def _commit(root: Path):
    try:
        completed = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                                   capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _changed_paths(root: Path):
    """Root-relative paths git reports as changed against HEAD, or untracked; None when git
    cannot tell: no repository, no commit yet, or no git."""
    listed = set()
    # --relative and -z: paths relative to root, even below the repository's top, and unquoted.
    for command in (["git", "diff", "--name-only", "--relative", "-z", "HEAD"],
                    ["git", "ls-files", "--others", "--exclude-standard", "-z"]):
        try:
            completed = subprocess.run(command, cwd=str(root), capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=30)
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        listed.update(name for name in completed.stdout.split("\0") if name)
    return listed


def stack_for(root: Path, explicit) -> tuple:
    """Packs whose role conventions apply, and the folders each framework pack is scoped to.

    From --packs (everywhere), else .clean/context.json, else a fresh detection.
    """
    if explicit is not None:
        return [pack.strip() if pack.strip().startswith("references/") else
                "references/" + pack.strip() for pack in explicit.split(",") if pack.strip()], {}
    context = root / ".clean" / "context.json"
    if context.is_file():
        try:
            recorded = json.loads(context.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            recorded = None
        if isinstance(recorded, dict) and isinstance(recorded.get("packs"), list):
            scopes = recorded.get("pack_scopes")
            return recorded["packs"], scopes if isinstance(scopes, dict) else {}
    detected = detect_stack.build_context(root)
    return detected.get("packs", []), detected.get("pack_scopes", {})


def _file_role(roled_file) -> str:
    if roled_file.home_role:
        return roled_file.home_role
    roles = {item.role for item in structure_findings.role_bearing(roled_file)}
    if len(roles) == 1:
        return roles.pop()
    return "mixed" if roles else "-"


def _file_entry(roled_file, imports: list) -> dict:
    return {
        "path": roled_file.path,
        "language": roled_file.language,
        "role": _file_role(roled_file),
        "home_role": roled_file.home_role,
        "test": roled_file.is_test,
        "purpose": roled_file.purpose,
        "lines": roled_file.lines,
        "imports": imports,
        "symbols": [
            {"name": item.symbol.name, "kind": item.symbol.kind, "line": item.symbol.line,
             "end_line": item.symbol.end_line, "exported": item.symbol.exported,
             "parent": item.symbol.parent, "role": item.role, "doc": item.symbol.doc}
            for item in roled_file.symbols
        ],
    }


def _project_roots(root: Path, paths) -> list:
    """Every folder holding a manifest: each is one project in a monorepo or solution."""
    manifests = detect_stack.find_manifests(root, [(Path(path), Path(path).name) for path in paths])
    return sorted({manifest["path"].rpartition("/")[0] for manifest in manifests})


class _Imports(NamedTuple):
    """Which project files each file imports, as resolved once for every finding."""

    file_imports: dict      # production file -> the production files it depends on
    references: dict        # every file, tests included, -> the production files it imports
    unresolved: dict        # file -> the imports that named no project file


def _resolve_imports(index, modules: dict, test_modules: dict) -> _Imports:
    """Every file's imports, resolved once. References count a file tests import as used, which
    is no dependency between production files; an unresolved import is recorded by its module."""
    sources = set(modules)
    references = {}
    unresolved = {}
    for path, imported in list(modules.items()) + list(test_modules.items()):
        targets = set(index.resolve_type_references(path))
        for module in imported:
            found = index.resolve(path, module)
            targets.update(found)
            if not found:
                unresolved.setdefault(path, []).append(project_imports.imported_module(module))
        references[path] = sorted(target for target in targets if target in sources and target != path)
    return _Imports({path: references[path] for path in modules}, references, unresolved)


def _organization_findings(roled_files, roles, project_roots, imports: _Imports, programs,
                           comment_heavy) -> dict:
    """Families, junk drawers, flat folders, unreferenced and comment-heavy files, less the files
    and folders the project `accept`s."""
    production = [roled.path for roled in roled_files if not roled.is_test]
    families = structure_organization.find_families(imports.file_imports, production)
    found = {
        "family": families,
        "junk_drawer": structure_organization.find_junk_drawers(roled_files, families, project_roots),
        "flat_folder": structure_organization.find_flat_folders(production, families,
                                                                roled_files=roled_files),
        "unreferenced": structure_organization.find_unreferenced(
            imports.references, roled_files, structure_organization.REFERENCE_TRACED_LANGUAGES,
            imports.unresolved, programs),
        "comment_heavy": sorted(comment_heavy, key=lambda finding: finding["path"]),
    }
    return {kind: structure_organization.without_accepted(kind_findings, roles)
            for kind, kind_findings in found.items()}


def _limited_to(findings: dict, changed) -> dict:
    """The findings that touch a changed path: name its file, the folder holding it directly (a
    folder finding judges only those files), or a component above it."""
    folders = {posixpath.dirname(path) for path in changed}

    def touches(kind, finding) -> bool:
        for path in structure_report.finding_paths(kind, finding):
            if not path.endswith("/"):
                if path in changed:
                    return True
            elif kind in structure_report.FOLDER_FINDINGS:
                if path[:-1] in folders:
                    return True
            elif any(changed_path.startswith(path) for changed_path in changed):
                return True
        return False

    return {kind: [finding for finding in found if touches(kind, finding)]
            for kind, found in findings.items()}


def build_map(root: Path, packs, depth: int, scopes=None, changed=None) -> dict:
    """The whole structure map of the project at root, as JSON-ready data.

    With `changed`, root-relative paths, the findings and moves are only those touching them.
    """
    roles = structure_roles.load_roles(SKILL_ROOT, packs, root, scopes)
    # One walk finds the sources and the manifests that mark each project.
    wanted = project_symbols.SUPPORTED_SUFFIXES | set(detect_stack.MANIFEST_SUFFIXES)
    walk = project_files.walk(root, wanted, frozenset(detect_stack.MANIFESTS))
    project_roots = _project_roots(root, walk.paths)
    index = import_resolution.ModuleIndex(root)
    roled_files = []
    modules = {}
    test_modules = {}
    programs = set()
    comment_heavy = []
    unparsed = []
    for path in walk.paths:
        if Path(path).suffix.lower() not in project_symbols.SUPPORTED_SUFFIXES:
            continue
        text = project_files.read_text(root / path)
        if text is None or project_files.is_generated(path, text):
            continue
        try:
            symbols = project_symbols.extract(path, text)
            if symbols is None:
                continue
            roled = structure_roles.assign(symbols, roles, project_files.is_test_path(path))
            index.add(path, text, symbols)
        except Exception as error:  # one pathological file must not cost the whole map
            unparsed.append({"path": path, "reason": f"{type(error).__name__}: {error}"[:160]})
            continue
        if symbols.unparsed:
            unparsed.append({"path": path, "reason": symbols.unparsed})
        roled_files.append(roled)
        imported = project_imports.resolvable_imports(Path(path).suffix, text)
        if roled.is_test:
            test_modules[path] = imported
            continue
        modules[path] = imported
        if structure_organization.runs_as_program(text):
            programs.add(path)
        # Counted here, so no file's text outlives the walk.
        comment_heavy += structure_organization.find_comment_heavy({path: text}, {path: roled.language})

    imports = _resolve_imports(index, modules, test_modules)
    file_imports = imports.file_imports
    type_counts = {roled.path: (roled.types, roled.abstract_types)
                   for roled in roled_files if not roled.is_test}
    metrics = component_metrics.analyze(file_imports, type_counts, depth)
    production = [roled for roled in roled_files if not roled.is_test]
    findings = {
        "misplaced": structure_findings.find_misplaced(roled_files, roles, project_roots),
        "mixed": structure_findings.find_mixed(roled_files, roles),
        "duplicates": structure_findings.find_duplicates(roled_files),
        "name_clashes": structure_findings.find_name_clashes(roled_files, roles, project_roots),
        "synonyms": structure_findings.find_synonyms(roled_files, roles),
        "names": structure_naming.find_names(roled_files, roles, project_roots),
        "cycles": metrics["cycles"],
    }
    findings.update(_organization_findings(roled_files, roles, project_roots, imports, programs,
                                           comment_heavy))
    if changed is not None:
        findings = _limited_to(findings, set(changed))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "clean-code skill / map_structure.py",
        "generated": time.strftime("%Y-%m-%d", time.gmtime()),
        "commit": _commit(root),
        "root": str(root),
        "packs": list(packs),
        "depth": depth,
        "truncated": walk.truncated,
        "unparsed": unparsed,
        "languages": dict(Counter(roled.language for roled in production).most_common()),
        "file_count": len(production),
        "test_file_count": len(roled_files) - len(production),
        "symbol_count": sum(1 for roled in production for item in roled.symbols
                            if item.symbol.parent is None),
        "changed": sorted(changed) if changed is not None else None,
        "findings": findings,
        "moves": structure_organization.plan_moves(findings),
        "components": metrics["components"],
        "edges": metrics["edges"],
        "files": [_file_entry(roled, file_imports.get(roled.path, [])) for roled in roled_files],
    }


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Map every source file: its symbols, role, purpose, and whether it belongs.")
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--write", action="store_true",
                        help="save <root>/.clean/structure.md and <root>/.clean/structure.json")
    parser.add_argument("--json", action="store_true", help="print the full map as JSON")
    parser.add_argument("--path", default=None,
                        help="summarize only files and findings under this folder")
    parser.add_argument("--changed", action="store_true",
                        help="keep only findings and moves touching files git reports as changed "
                             "against HEAD, or untracked (outside a repository: every file)")
    parser.add_argument("--depth", type=int, default=2,
                        help="folder depth that defines a component (default: 2)")
    parser.add_argument("--top", type=int, default=25,
                        help="findings listed per kind in structure.md (default: 25)")
    parser.add_argument("--packs", default=None,
                        help="comma-separated pack paths whose roles apply (default: from "
                             ".clean/context.json, else detected)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = parse_arguments(argv if argv is not None else sys.argv[1:])
    # A pipe on Windows defaults to the ANSI code page, which cannot encode most names;
    # UTF-8 can, and it is what JSON consumers expect.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    root = Path(arguments.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    if arguments.changed and arguments.write:
        print("error: --changed maps only the changed files, so it cannot replace .clean/structure.md; "
              "save the whole map with --write alone", file=sys.stderr)
        return 2
    changed = _changed_paths(root) if arguments.changed else None
    if arguments.changed and changed is None:
        print("note: git could not list changed files (no repository, no commit, or no git); "
              "mapping every file", file=sys.stderr)
    try:
        packs, scopes = stack_for(root, arguments.packs)
        data = build_map(root, packs, max(1, arguments.depth), scopes, changed)
    except structure_roles.RolesError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    # Save first, so a failure to print never costs the saved map.
    destination = root / ".clean"
    if arguments.write:
        try:
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "structure.md").write_text(
                structure_report.render_markdown(data, arguments.top), encoding="utf-8")
            (destination / "structure.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except OSError as error:
            print(f"error: could not write {destination}: {error}", file=sys.stderr)
            return 1

    if arguments.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(structure_report.render_summary(data, arguments.path))
    if arguments.write and not arguments.json:
        print(f"\nSaved: {destination / 'structure.md'} and structure.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
