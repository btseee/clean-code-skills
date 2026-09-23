#!/usr/bin/env python3
"""Which modules a source file imports, decided once for every scanner.

check_boundaries places each import in a declared layer; map_structure resolves
imports to project files to draw the component graph. Both read imports the same
way, from here.

Standard library only. Reads files; never writes.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

import project_files

_INCLUDE = r"""^\s*#\s*(?:import|include)\s*[<"]([^>"]+)[>"]"""
_JS_FROM = r"""from\s+['"]([^'"]+)['"]"""
_JS_REQUIRE = r"""require\(\s*['"]([^'"]+)['"]"""
_JS_DYNAMIC = r"""import\s*\(\s*['"]([^'"]+)['"]"""
_PYTHON = [r"^\s*from\s+([\w.]+)\s+import\b", r"^\s*import\s+([\w.]+)"]
_SHELL = [r"""^\s*(?:source|\.)\s+["']?(.+?)["']?\s*(?:;.*|#.*)?$"""]
_POWERSHELL = [
    r"""(?i)^\s*\.\s+["']?([^"'\s]+)["']?""",
    r"""(?i)^\s*import-module\s+(?:-name\s+)?["']?([^"'\s;]+)["']?""",
    r"""(?i)^\s*using\s+module\s+["']?([^"'\s;]+)["']?""",
]

# Extension -> patterns that capture the imported module or path.
IMPORT_PATTERNS = {
    ".py": _PYTHON,
    ".pyi": _PYTHON,
    ".js": [_JS_FROM, _JS_REQUIRE, _JS_DYNAMIC],
    ".jsx": [_JS_FROM, _JS_REQUIRE],
    ".mjs": [_JS_FROM, _JS_DYNAMIC],
    ".cjs": [_JS_REQUIRE],
    ".ts": [_JS_FROM, _JS_REQUIRE, _JS_DYNAMIC],
    ".mts": [_JS_FROM, _JS_REQUIRE, _JS_DYNAMIC],
    ".cts": [_JS_FROM, _JS_REQUIRE, _JS_DYNAMIC],
    ".tsx": [_JS_FROM, _JS_REQUIRE],
    ".vue": [_JS_FROM],
    ".svelte": [_JS_FROM],
    ".cs": [r"^\s*global\s+using\s+(?:static\s+)?([\w.]+)\s*;",
            r"^\s*using\s+(?:static\s+)?([\w.]+)\s*;"],
    ".fs": [r"^\s*open\s+([\w.]+)"],
    ".java": [r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;"],
    ".kt": [r"^\s*import\s+([\w.*]+)"],
    ".kts": [r"^\s*import\s+([\w.*]+)"],
    ".scala": [r"^\s*import\s+([\w.{}, _]+)"],
    ".go": [r"""^\s*(?:import\s+)?(?:[\w.]+\s+)?"([^"]+)"\s*$"""],
    ".rs": [r"^\s*(?:pub\s+)?use\s+([\w:]+)"],
    ".rb": [r"""require(?:_relative)?\s+['"]([^'"]+)['"]"""],
    ".php": [r"^\s*use\s+([\w\\]+)"],
    ".swift": [r"^\s*import\s+(\w+)"],
    ".dart": [r"""import\s+['"]([^'"]+)['"]"""],
    ".c": [_INCLUDE],
    ".h": [_INCLUDE],
    ".cc": [_INCLUDE],
    ".cpp": [_INCLUDE],
    ".cxx": [_INCLUDE],
    ".hpp": [_INCLUDE],
    ".hh": [_INCLUDE],
    ".m": [_INCLUDE, r"^\s*@import\s+([\w.]+)\s*;"],
    ".mm": [_INCLUDE, r"^\s*@import\s+([\w.]+)\s*;"],
    ".sh": _SHELL,
    ".bash": _SHELL,
    ".zsh": _SHELL,
    ".ps1": _POWERSHELL,
    ".psm1": _POWERSHELL,
    ".r": [r"""^\s*source\(\s*["']([^"']+)["']""",
           r"""^\s*(?:library|require|requireNamespace)\(\s*["']?([\w.]+)["']?"""],
    ".ex": [r"^\s*alias\s+([\w.]+)", r"^\s*import\s+([\w.]+)"],
    ".exs": [r"^\s*alias\s+([\w.]+)"],
    ".ml": [r"^\s*open\s+([\w.]+)"],
    ".hs": [r"^\s*import\s+(?:qualified\s+)?([\w.]+)"],
}

COMPILED_IMPORT_PATTERNS = {
    extension: [re.compile(pattern) for pattern in patterns]
    for extension, patterns in IMPORT_PATTERNS.items()
}

RESOLVABLE_SUFFIXES = (
    "", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".py", ".dart", ".rb",
)

MAX_IMPORT_LINE = 500


def _scan(suffix: str, text: str):
    patterns = COMPILED_IMPORT_PATTERNS.get(suffix.lower(), [])
    if not patterns:
        return
    for line_number, line in enumerate(text.splitlines(), 1):
        if len(line) > MAX_IMPORT_LINE:
            continue
        for pattern in patterns:
            found = pattern.search(line)
            if found:
                yield line_number, found.group(1).strip(), line.strip()
                break


def imports_in_text(suffix: str, text: str) -> list:
    """(line, module) for every import in text written in the language of suffix."""
    return [(line_number, module) for line_number, module, _ in _scan(suffix, text)]


def extract_imports(path: Path):
    """(line, module, source line) for every import in the file at path."""
    if path.suffix.lower() not in COMPILED_IMPORT_PATTERNS:
        return
    text = project_files.read_text(path)
    if text is None:
        return
    yield from _scan(path.suffix, text)


def resolve_relative_import(source_path: str, module: str, exists) -> str | None:
    """Turn `./x`, `../x`, or Python's `..pkg.mod` into a root-relative path.

    `exists` answers whether a root-relative path is on disk. Returns None when
    the import is not relative, escapes the root, or matches no file: an import
    that cannot be found is unknown, never a guessed path.
    """
    if not module.startswith("."):
        return None
    base = posixpath.dirname(source_path)
    if "/" in module:
        target = posixpath.normpath(posixpath.join(base, module))
    else:
        dots = len(module) - len(module.lstrip("."))
        for _ in range(dots - 1):
            base = posixpath.dirname(base)
        rest = module[dots:].replace(".", "/")
        target = posixpath.normpath(posixpath.join(base, rest)) if rest else (base or ".")
    if target.startswith(".."):
        return None
    for suffix in RESOLVABLE_SUFFIXES:
        if exists(target + suffix):
            return target + suffix
    return None
