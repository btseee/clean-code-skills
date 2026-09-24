#!/usr/bin/env python3
"""Check that source dependencies point inward, as the Dependency Rule requires.

Reads the layering you declared in .clean/architecture.md, extracts the imports
from every source file, and reports each import that crosses a boundary in the
forbidden direction. A layer may depend on itself and on layers declared before
it; anything else is a violation unless you allowed it explicitly.

This is a fitness function, not a linter: it answers one question -- does the
code obey the architecture you wrote down? -- and exits non-zero when it does not.

Standard library only. Reads files; never writes.

Usage:
    python check_boundaries.py                     # check the current project
    python check_boundaries.py --root ../app
    python check_boundaries.py --config docs/layers.md
    python check_boundaries.py --json              # machine-readable findings
    python check_boundaries.py --print-config      # show the parsed layering

Declare layers innermost first, in a fenced `clean-architecture` block:

    ```clean-architecture
    layer domain         = src/Domain/**
    layer application    = src/Application/**
    layer adapter        = src/Api/**, src/Web/**
    layer infrastructure = src/Infrastructure/**

    # Optional overrides. The default is inward-only.
    allow infrastructure -> domain
    deny  adapter -> infrastructure
    ```

Globs match the path from the project root; `*` also crosses `/`, and a leading
`**/` also matches a top-level folder.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

import project_files
import project_imports

CONFIG_BLOCK_PATTERN = re.compile(
    r"```(?:clean-architecture|clean-arch|architecture)\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

LAYER_PATTERN = re.compile(r"^layer\s+([\w.-]+)\s*=\s*(.+)$", re.IGNORECASE)
NAMESPACE_PATTERN = re.compile(r"^namespace\s+([\w.-]+)\s*=\s*(.+)$", re.IGNORECASE)
RULE_PATTERN = re.compile(r"^(allow|deny)\s+([\w.-]+)\s*->\s*(.+)$", re.IGNORECASE)

# Folders that hold sources rather than name a concept: `src/main/java`, `include/`, R's `R/`.
SOURCE_ROOT_SEGMENTS = {
    "src", "lib", "app", "source", "sources", "pkg", "internal",
    "main", "java", "kotlin", "scala", "groovy", "include", "r",
}

DEFAULT_CONFIG_PATHS = (
    ".clean/architecture.md",
    ".clean/ARCHITECTURE.md",
    "ARCHITECTURE.md",
    "docs/architecture.md",
)


class ConfigError(Exception):
    """The declared architecture could not be read."""


class Layering:
    """The declared layers and the dependencies allowed between them."""

    def __init__(self, layers, namespaces, allowed, denied):
        self.layers = layers            # ordered: innermost first
        self.namespaces = namespaces    # layer -> [token, ...]
        self.allowed = allowed          # layer -> {layer, ...} explicitly allowed
        self.denied = denied            # layer -> {layer, ...} explicitly denied
        self.order = {name: index for index, name in enumerate(layers)}

    def permits(self, source_layer: str, target_layer: str) -> bool:
        if source_layer == target_layer:
            return True
        denied = self.denied.get(source_layer, ())
        allowed = self.allowed.get(source_layer, ())
        if target_layer in denied or "*" in denied:
            return False
        if target_layer in allowed or "*" in allowed:
            return True
        # The Dependency Rule: a layer may point inward, never outward.
        return self.order[target_layer] < self.order[source_layer]

    def layer_of_path(self, relative_path: str) -> str | None:
        """Innermost matching layer wins, so nested globs stay predictable."""
        for name in self.layers:
            for glob in self.layers[name]:
                normalized = glob.replace("\\", "/")
                candidates = [normalized]
                # `**/domain/**` should also match a top-level `domain/`.
                if normalized.startswith("**/"):
                    candidates.append(normalized[3:])
                for candidate in candidates:
                    if fnmatch.fnmatch(relative_path, candidate):
                        return name
                    # `src/Domain/**` should also match `src/Domain/Order.cs`.
                    if candidate.endswith("/**") and fnmatch.fnmatch(
                        relative_path, candidate[:-3] + "/*"
                    ):
                        return name
        return None

    def layer_of_name(self, module: str) -> str | None:
        """Place a module name such as `App.Domain.Orders` by its namespace tokens."""
        normalized = module.replace("\\", ".").replace("/", ".").lower()
        segments = {segment for segment in normalized.split(".") if segment}
        for name, tokens in self.namespaces.items():
            if any(token in segments for token in tokens):
                return name
        return None

    def layer_of_import(self, module: str, source_path: str, exists) -> str | None:
        """Classify one import from `source_path` into a declared layer.

        A relative import that resolves to a file on disk is placed by that file's
        path and nothing else; one that resolves nowhere falls back to its name,
        so `from ..infra.db import Db` still lands in `infra`. Returns None when
        the import points outside every declared layer or cannot be placed.
        """
        resolved = project_imports.resolve_relative_import(source_path, module, exists)
        if resolved is not None:
            return self.layer_of_path(resolved)
        return self.layer_of_name(module)


def parse_list(raw: str) -> list:
    return [item.strip() for item in raw.split(",") if item.strip()]


def derive_namespace_tokens(globs) -> list:
    """Turn `src/Domain/**` into the token `domain`.

    Import strings are module names, not file paths, so a layer also needs
    name-shaped identifiers to be recognisable inside `using App.Domain.X` or
    `from app.domain.x import y`.
    """
    tokens = set()
    for glob in globs:
        for segment in re.split(r"[\\/]+", glob):
            segment = segment.strip()
            if not segment or "*" in segment or segment in {".", ".."}:
                continue
            if segment.lower() in SOURCE_ROOT_SEGMENTS:
                continue
            tokens.add(segment.lower())
    return sorted(tokens)


def parse_layering(text: str) -> Layering:
    match = CONFIG_BLOCK_PATTERN.search(text)
    if match is None:
        raise ConfigError(
            "no ```clean-architecture block found. Declare the layers before "
            "checking them; see assets/templates/architecture.md for the format."
        )

    layer_globs: dict = {}
    explicit_namespaces: dict = {}
    allowed: dict = {}
    denied: dict = {}

    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        layer_match = LAYER_PATTERN.match(line)
        if layer_match:
            name = layer_match.group(1).lower()
            if name in layer_globs:
                raise ConfigError(f"layer '{name}' is declared twice")
            layer_globs[name] = parse_list(layer_match.group(2))
            continue

        namespace_match = NAMESPACE_PATTERN.match(line)
        if namespace_match:
            name = namespace_match.group(1).lower()
            explicit_namespaces[name] = [
                token.lower() for token in parse_list(namespace_match.group(2))
            ]
            continue

        rule_match = RULE_PATTERN.match(line)
        if rule_match:
            kind, source, targets = rule_match.groups()
            bucket = allowed if kind.lower() == "allow" else denied
            bucket.setdefault(source.lower(), set()).update(
                target.lower() for target in parse_list(targets)
            )
            continue

        raise ConfigError(f"cannot parse line: {line}")

    if len(layer_globs) < 2:
        raise ConfigError("declare at least two layers, innermost first")

    for source, targets in list(allowed.items()) + list(denied.items()):
        for name in {source, *targets}:
            if name not in layer_globs and name != "*":
                raise ConfigError(f"rule refers to undeclared layer '{name}'")

    namespaces = {
        name: explicit_namespaces.get(name) or derive_namespace_tokens(globs)
        for name, globs in layer_globs.items()
    }

    return Layering(layer_globs, namespaces, allowed, denied)


def find_config(root: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = root / candidate
        if not candidate.is_file():
            raise ConfigError(f"config not found: {candidate}")
        return candidate

    for relative in DEFAULT_CONFIG_PATHS:
        candidate = root / relative
        if candidate.is_file():
            return candidate

    raise ConfigError(
        "no architecture declaration found. Looked for: "
        + ", ".join(DEFAULT_CONFIG_PATHS)
        + ". Copy assets/templates/architecture.md to .clean/architecture.md and "
          "declare the layers you intend before checking them."
    )


def check_project(root: Path, layering: Layering) -> dict:
    violations = []
    files_by_layer: dict = {}
    imports_checked = 0
    imports_unplaced = 0

    def exists(relative_path: str) -> bool:
        return (root / relative_path).exists()

    walk = project_files.walk(root, project_imports.COMPILED_IMPORT_PATTERNS)
    for relative_path in walk.paths:
        path = root / relative_path
        source_layer = layering.layer_of_path(relative_path)
        if source_layer is None:
            continue
        files_by_layer[source_layer] = files_by_layer.get(source_layer, 0) + 1

        for line_number, module, line_text in project_imports.extract_imports(path):
            target_layer = layering.layer_of_import(module, relative_path, exists)
            if target_layer is None:
                imports_unplaced += 1
                continue
            imports_checked += 1
            if not layering.permits(source_layer, target_layer):
                violations.append({
                    "file": relative_path,
                    "line": line_number,
                    "from_layer": source_layer,
                    "to_layer": target_layer,
                    "import": module,
                    "source": line_text[:160],
                })

    return {
        "layers": list(layering.layers),
        "files_by_layer": files_by_layer,
        "cross_layer_imports_checked": imports_checked,
        "imports_outside_layers": imports_unplaced,
        "scan_truncated": walk.truncated,
        "violation_count": len(violations),
        "violations": violations,
    }


def render_report(result: dict) -> str:
    lines = ["Dependency Rule check", ""]
    lines.append("  Layers (innermost first): " + " -> ".join(result["layers"]))

    counts = result["files_by_layer"]
    if counts:
        summary = ", ".join(
            f"{name} ({counts.get(name, 0)})" for name in result["layers"]
        )
        lines.append(f"  Files matched           : {summary}")
    else:
        lines.append("  Files matched           : none")
        lines.append("")
        lines.append("  ERROR: no source file matched any declared layer, so nothing was")
        lines.append("  checked. The globs in your architecture declaration do not match")
        lines.append("  this layout. Fix the declaration; a passing check must check files.")
        return "\n".join(lines)

    lines.append(f"  Cross-layer imports     : {result['cross_layer_imports_checked']}")
    lines.append(f"  Imports outside layers  : {result['imports_outside_layers']}")
    lines.append("")

    if not result["violations"]:
        lines.append("  PASS: every source dependency points inward.")
        return "\n".join(lines)

    lines.append(f"  FAIL: {result['violation_count']} dependency-rule violation(s).")
    lines.append("")
    for violation in result["violations"][:60]:
        lines.append(
            f"  {violation['file']}:{violation['line']}: "
            f"{violation['from_layer']} -> {violation['to_layer']} "
            f"(imports {violation['import']})"
        )
    if result["violation_count"] > 60:
        lines.append(f"  ... and {result['violation_count'] - 60} more.")

    lines.append("")
    lines.append("  Each line above is an outward dependency: an inner layer that knows")
    lines.append("  about an outer one. Fix by inverting it -- declare the interface in")
    lines.append("  the inner layer and implement it in the outer one -- not by widening")
    lines.append("  the rules. Add an `allow` line only for a boundary you intend.")
    return "\n".join(lines)


def parse_arguments(argv) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that source dependencies point inward (the Dependency Rule).",
    )
    parser.add_argument("--root", default=".", help="project directory (default: .)")
    parser.add_argument("--config", default=None,
                        help="path to the architecture declaration")
    parser.add_argument("--json", action="store_true", help="print JSON findings")
    parser.add_argument("--print-config", action="store_true",
                        help="show the parsed layering and exit")
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
        config_path = find_config(root, arguments.config)
        layering = parse_layering(config_path.read_text(encoding="utf-8", errors="replace"))
    except (ConfigError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if arguments.print_config:
        for index, name in enumerate(layering.layers):
            globs = ", ".join(layering.layers[name])
            tokens = ", ".join(layering.namespaces[name])
            print(f"{index}. {name}\n   globs : {globs}\n   tokens: {tokens}")
        return 0

    result = check_project(root, layering)
    try:
        result["config"] = config_path.relative_to(root).as_posix()
    except ValueError:
        result["config"] = str(config_path)

    checked_nothing = not result["files_by_layer"]
    if checked_nothing:
        result["error"] = ("no source file matched any declared layer; the globs in "
                           "the architecture declaration do not match this layout")

    if arguments.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_report(result))

    if checked_nothing:
        return 2
    return 1 if result["violation_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
