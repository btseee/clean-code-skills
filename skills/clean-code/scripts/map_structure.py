#!/usr/bin/env python3
"""Map every source file: what it declares, which role it plays, whether it belongs.

One walk reads each file once. Symbols come from project_symbols, roles from
the clean-roles conventions (the project's .clean/roles.md, then the framework
packs, then the generic block), dependencies from import_resolution. The result
is evidence for judgement -- misplaced, mixed, duplicated, clashing, and
synonymous code, component metrics, and cycles -- never a verdict.

Standard library only. Reads files; writes only .clean/structure.md and
.clean/structure.json, and only with --write.

Usage:
    python map_structure.py                   # summary for the current project
    python map_structure.py --path src/api    # the rows and findings for one folder
    python map_structure.py --write           # save .clean/structure.md and .json
    python map_structure.py --json            # the full map as JSON
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import component_metrics
import detect_stack
import import_resolution
import project_files
import project_imports
import project_symbols
import structure_findings
import structure_report
import structure_roles

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


def _project_roots(root: Path) -> list:
    """Every folder holding a manifest: each is one project in a monorepo or solution."""
    paths = [Path(path) for path in project_files.walk(root).paths]
    manifests = detect_stack.find_manifests(root, [(path, path.name) for path in paths])
    return sorted({manifest["path"].rpartition("/")[0] for manifest in manifests})


def build_map(root: Path, packs, depth: int, scopes=None) -> dict:
    """The whole structure map of the project at root, as JSON-ready data."""
    roles = structure_roles.load_roles(SKILL_ROOT, packs, root, scopes)
    walk = project_files.walk(root, project_symbols.SUPPORTED_SUFFIXES)
    index = import_resolution.ModuleIndex(root)
    roled_files = []
    modules = {}
    unparsed = []
    for path in walk.paths:
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
        if not roled.is_test:
            modules[path] = project_imports.resolvable_imports(Path(path).suffix, text)

    sources = set(modules)
    file_imports = {}
    for path, imported in modules.items():
        targets = set(index.resolve_type_references(path))
        for module in imported:
            targets.update(index.resolve(path, module))
        file_imports[path] = sorted(target for target in targets if target in sources and target != path)

    type_counts = {roled.path: (roled.types, roled.abstract_types)
                   for roled in roled_files if not roled.is_test}
    metrics = component_metrics.analyze(file_imports, type_counts, depth)
    production = [roled for roled in roled_files if not roled.is_test]

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
        "findings": {
            "misplaced": structure_findings.find_misplaced(roled_files, roles, _project_roots(root)),
            "mixed": structure_findings.find_mixed(roled_files),
            "duplicates": structure_findings.find_duplicates(roled_files),
            "name_clashes": structure_findings.find_name_clashes(roled_files, roles),
            "synonyms": structure_findings.find_synonyms(roled_files, roles),
            "cycles": metrics["cycles"],
        },
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
    try:
        packs, scopes = stack_for(root, arguments.packs)
        data = build_map(root, packs, max(1, arguments.depth), scopes)
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
