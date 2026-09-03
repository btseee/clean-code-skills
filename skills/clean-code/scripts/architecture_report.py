#!/usr/bin/env python3
"""One-page architecture report card: what the scanners can measure, in one place.

    Architecture score       84/100   (heuristic)
    Dependency violations     3       (measured; needs a declared layering)
    Circular dependencies     1       (measured on resolved imports)
    Possible god modules      2       (heuristic)
    Unreferenced files        4       (heuristic)
    Duplicate concepts        2       (heuristic)
    Untested areas            3       (measured: file counts, not coverage)

Every number has a detection rule, stated in the report and in this file. Rules
marked *measured* are exact for what they look at; rules marked *heuristic* find
candidates for a person to judge. The score is a weighted sum for comparing two
runs of the same project; it is not comparable across projects, and it is not a
grade.

Reuses check_boundaries.py (imports, resolution, layering), scan_repo.py (sibling
variants, test presence), and project_files.py (which files count). Standard
library only. Reads files; never writes.

Usage:
    python architecture_report.py                # report for the current project
    python architecture_report.py --root ../app --json
    python architecture_report.py --config docs/layers.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import check_boundaries as cb
import project_files
import scan_repo
from detect_stack import SOURCE_DIR_NAMES

GOD_MODULE_LINES = 400
GOD_MODULE_FAN_OUT = 15
GOD_MODULE_AREAS = 3

# Names that are entry points or conventional roots; nothing imports them, by design.
ENTRY_POINT_STEMS = frozenset({
    "index", "main", "app", "server", "cli", "setup", "manage", "conftest",
    "__init__", "__main__", "mod", "lib", "program", "startup", "wsgi", "asgi",
})
# Stems too generic to signal one concept living in two places.
GENERIC_STEMS = frozenset({
    "index", "main", "types", "type", "utils", "util", "helpers", "helper",
    "constants", "config", "settings", "errors", "exceptions", "__init__",
    "mod", "models", "model", "schema", "schemas", "api", "routes", "views",
    "test", "tests", "readme", "styles", "style", "hooks", "components",
})

WEIGHTS = {
    "dependency_violations": 8,
    "circular_dependencies": 10,
    "possible_god_modules": 5,
    "unreferenced_files": 2,
    "duplicate_concepts": 3,
    "untested_areas": 4,
}


def python_module_candidates(module: str, roots) -> list:
    """`app.orders.service` -> app/orders/service.py and app/orders/service/__init__.py, per root."""
    relative = module.replace(".", "/")
    candidates = []
    for root in [""] + list(roots):
        base = f"{root}/{relative}" if root else relative
        candidates.extend([f"{base}.py", f"{base}/__init__.py"])
    return candidates


def build_import_graph(root: Path, files, source_roots) -> dict:
    """File -> set of project files it imports. Only imports that resolve to a file count.

    Relative imports resolve through check_boundaries; Python absolute imports are
    tried against the project root and each source root. Package imports are
    ignored, so the graph is a subset of the truth and the numbers on it are floors.
    """
    file_set = set(files)
    graph = {relative: set() for relative in files}
    for relative in files:
        path = root / relative
        for _, module, _ in cb.extract_imports(path):
            target = cb.resolve_relative_import(relative, module, file_set.__contains__)
            if target is None and relative.endswith((".py", ".pyi")) and not module.startswith("."):
                # Python resolves absolute imports against the importing file's own
                # directory (sys.path[0]) and the project or source roots.
                own_dir = relative.rsplit("/", 1)[0] if "/" in relative else ""
                roots = ([own_dir] if own_dir else []) + list(source_roots)
                target = next((c for c in python_module_candidates(module, roots) if c in file_set), None)
            if target is not None and target != relative:
                graph[relative].add(target)
    return graph


def strongly_connected_components(graph: dict) -> list:
    """Tarjan's algorithm. Returns components with more than one file."""
    sys.setrecursionlimit(max(sys.getrecursionlimit(), len(graph) + 100))
    index: dict = {}
    lowlink: dict = {}
    stack: list = []
    components: list = []

    def visit(node):
        index[node] = lowlink[node] = len(index)
        stack.append(node)
        for succ in graph[node]:
            if succ not in index:
                visit(succ)
                lowlink[node] = min(lowlink[node], lowlink[succ])
            elif succ in stack:
                lowlink[node] = min(lowlink[node], index[succ])
        if lowlink[node] == index[node]:
            component = stack[stack.index(node):]
            del stack[stack.index(node):]
            if len(component) > 1:
                components.append(sorted(component))

    for start in graph:
        if start not in index:
            visit(start)
    return sorted(components)


def line_count(root: Path, relative: str) -> int:
    text = project_files.read_text(root / relative)
    return 0 if text is None else len(text.splitlines())


def top_area(relative: str) -> str:
    parts = relative.split("/")
    return parts[0] if len(parts) > 1 else "(repository root)"


def find_god_modules(root: Path, graph: dict) -> list:
    """Heuristic: a big file that also reaches into many places is doing several jobs.

    Flags a file with >= GOD_MODULE_LINES lines that either imports from
    >= GOD_MODULE_AREAS distinct top-level areas or has fan-out >= GOD_MODULE_FAN_OUT.
    """
    found = []
    for relative, targets in graph.items():
        if project_files.is_test_path(relative):
            continue
        lines = line_count(root, relative)
        if lines < GOD_MODULE_LINES:
            continue
        areas = {top_area(t) for t in targets} - {top_area(relative)}
        if len(targets) >= GOD_MODULE_FAN_OUT or len(areas) >= GOD_MODULE_AREAS:
            found.append({"file": relative, "lines": lines, "fan_out": len(targets),
                          "areas_reached": sorted(areas)})
    return sorted(found, key=lambda item: (-item["lines"], item["file"]))


def find_unreferenced(graph: dict) -> list:
    """Heuristic: resolvable source files nothing in the project imports.

    Skips tests and entry-point names. Only meaningful when the graph has edges;
    with no resolved imports at all, every file is 'unreferenced' and the metric
    is withheld rather than reported.
    """
    if not any(graph.values()):
        return []
    referenced = set().union(*graph.values())
    resolvable = tuple(s for s in cb.RESOLVABLE_SUFFIXES if s)
    orphans = []
    for relative in graph:
        if relative in referenced or not relative.endswith(resolvable):
            continue
        stem = Path(relative).stem.lower()
        if project_files.is_test_path(relative) or stem in ENTRY_POINT_STEMS:
            continue
        if stem.endswith((".config", ".d", ".stories")) or ".config." in relative:
            continue
        orphans.append(relative)
    return sorted(orphans)


def find_duplicate_concepts(files) -> list:
    """Heuristic: one file name living in two or more directories, plus sibling variants.

    A `refund-service.ts` in two folders is usually one concept with two owners.
    Generic names (index, utils, types...) are ignored; tests are ignored.
    """
    by_stem: dict = {}
    for relative in files:
        if project_files.is_test_path(relative):
            continue
        path = Path(relative)
        stem = path.stem.lower()
        stem = scan_repo.SIBLING_VARIANT_PATTERN.sub("", stem) or stem
        if stem in GENERIC_STEMS or len(stem) < 4:
            continue
        by_stem.setdefault(stem, set()).add(relative)
    groups = [
        {"concept": stem, "files": sorted(paths)}
        for stem, paths in by_stem.items()
        if len({Path(p).parent for p in paths}) > 1
    ]
    for variant in scan_repo.find_sibling_variants(set(files)):
        groups.append({"concept": Path(variant["suspected_original"]).stem,
                       "files": sorted(set(variant["variants"]) | ({variant["suspected_original"]} if variant["original_exists"] else set()))})
    return sorted(groups, key=lambda g: g["concept"])


def find_untested_areas(files, layering, graph) -> list:
    """Measured: layers (or top-level areas) with production files that no test touches.

    A test touches an area when it lies inside it or imports a file in it. File
    counts and import edges, not coverage: a place no test reaches is a place a
    change cannot be verified, which is the decision that matters.
    """
    def area_of(relative):
        return layering.layer_of_path(relative) if layering else top_area(relative)

    production: dict = {}
    tested: set = set()
    for relative in files:
        area = area_of(relative)
        if area is None:
            continue
        if project_files.is_test_path(relative):
            tested.add(area)
        else:
            production[area] = production.get(area, 0) + 1
    for relative, targets in graph.items():
        if project_files.is_test_path(relative):
            tested.update(a for a in map(area_of, targets) if a is not None)
    return [
        {"area": area, "production": count}
        for area, count in sorted(production.items())
        if area not in tested
    ]


def build_report(root: Path, config: str | None) -> dict:
    walk = project_files.walk(root, cb.COMPILED_IMPORT_PATTERNS)
    files = walk.paths
    source_roots = sorted({p.split("/")[0] for p in files if "/" in p and p.split("/")[0].lower() in SOURCE_DIR_NAMES})

    layering = boundary = None
    try:
        config_path = cb.find_config(root, config)
        layering = cb.parse_layering(config_path.read_text(encoding="utf-8", errors="replace"))
        boundary = cb.check_project(root, layering)
        layering_note = f"declared in {config_path}" + ("" if boundary["files_by_layer"] else " (globs matched no files)")
    except (cb.ConfigError, OSError) as error:
        layering_note = f"none found; violations not measurable ({error})"

    graph = build_import_graph(root, files, source_roots)
    cycles = strongly_connected_components(graph)
    god_modules = find_god_modules(root, graph)
    unreferenced = find_unreferenced(graph)
    duplicates = find_duplicate_concepts(files)
    untested = find_untested_areas(files, layering, graph)

    counts = {
        "dependency_violations": boundary["violation_count"] if boundary else None,
        "circular_dependencies": len(cycles),
        "possible_god_modules": len(god_modules),
        "unreferenced_files": len(unreferenced),
        "duplicate_concepts": len(duplicates),
        "untested_areas": len(untested),
    }
    penalty = sum(WEIGHTS[key] * (value or 0) for key, value in counts.items())
    score = max(0, 100 - penalty)

    return {
        "schema_version": 1,
        "generated_by": "clean-code skill / architecture_report.py",
        "root": str(root),
        "files_considered": len(files),
        "scan_truncated": walk.truncated,
        "resolved_import_edges": sum(len(t) for t in graph.values()),
        "score": {"value": score, "kind": "heuristic",
                  "rule": "100 minus weighted counts; compare runs of the same project only",
                  "weights": WEIGHTS},
        "metrics": {
            "dependency_violations": {"count": counts["dependency_violations"], "kind": "measured",
                                      "rule": "imports crossing the declared layering outward (check_boundaries.py)",
                                      "note": layering_note,
                                      "items": boundary["violations"][:60] if boundary else []},
            "circular_dependencies": {"count": counts["circular_dependencies"], "kind": "measured",
                                      "rule": "strongly connected components of size > 1 in the resolved file-import graph",
                                      "items": cycles[:20]},
            "possible_god_modules": {"count": counts["possible_god_modules"], "kind": "heuristic",
                                     "rule": f">= {GOD_MODULE_LINES} lines and (fan-out >= {GOD_MODULE_FAN_OUT} or imports from >= {GOD_MODULE_AREAS} top-level areas)",
                                     "items": god_modules[:20]},
            "unreferenced_files": {"count": counts["unreferenced_files"], "kind": "heuristic",
                                   "rule": "resolvable non-test, non-entry-point source files with zero resolved importers; withheld when no import resolved",
                                   "items": unreferenced[:40]},
            "duplicate_concepts": {"count": counts["duplicate_concepts"], "kind": "heuristic",
                                   "rule": "one non-generic file stem in two or more directories, or a sibling-variant group",
                                   "items": duplicates[:20]},
            "untested_areas": {"count": counts["untested_areas"], "kind": "measured",
                               "rule": "declared layers (else top-level directories) with production files that no test file lies in or imports; files and edges, not coverage",
                               "items": untested},
        },
    }


SECTIONS = (
    ("Dependency violations", "dependency_violations",
     lambda v: f"{v['file']}:{v['line']} {v['from_layer']} -> {v['to_layer']} (imports {v['import']})"),
    ("Circular dependencies", "circular_dependencies", lambda c: " <-> ".join(c)),
    ("Possible god modules", "possible_god_modules",
     lambda g: f"{g['file']} ({g['lines']} lines, fan-out {g['fan_out']}, reaches {', '.join(g['areas_reached']) or 'own area'})"),
    ("Unreferenced files", "unreferenced_files", str),
    ("Duplicate concepts", "duplicate_concepts", lambda d: f"{d['concept']}: {', '.join(d['files'])}"),
    ("Untested areas", "untested_areas", lambda u: f"{u['area']} ({u['production']} production files, no test lies in or imports it)"),
)


def render(report: dict) -> str:
    m = report["metrics"]
    lines = ["Architecture report card", "",
             f"  {'Architecture score':<26}{report['score']['value']:>3}/100   (heuristic; compare runs of this project only)"]
    for label, key, _ in SECTIONS:
        count = m[key]["count"]
        lines.append(f"  {label:<26}{'n/a' if count is None else count:>5}   ({m[key]['kind']})")
    lines += ["", f"  Files considered: {report['files_considered']}; resolved import edges: {report['resolved_import_edges']}"
              + ("; SCAN TRUNCATED at the file cap" if report["scan_truncated"] else ""),
              f"  Layering: {m['dependency_violations']['note']}", ""]
    for label, key, fmt in SECTIONS:
        items = m[key]["items"]
        if items:
            lines.append(f"  {label}:")
            lines += [f"    - {fmt(item)}" for item in items[:10]]
            if len(items) > 10:
                lines.append(f"    ... and {len(items) - 10} more (see --json)")
            lines.append("")
    lines.append("  Rules: " + "; ".join(f"{k.replace('_', ' ')} = {v['rule']}" for k, v in m.items()))
    return "\n".join(lines)


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Architecture report card from the bundled scanners.")
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--config", default=None, help="path to the architecture declaration")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = parse_arguments(argv if argv is not None else sys.argv[1:])
    root = Path(arguments.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    report = build_report(root, arguments.config)
    if arguments.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
