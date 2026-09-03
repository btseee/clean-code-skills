#!/usr/bin/env python3
"""Which files count as the project, decided once for every script in this folder.

detect_stack, scan_repo, and check_boundaries each walk the repository. They
must agree on what to skip (dependency and build folders, dot-directories),
what a test file looks like, and how much to read, or the same project shows
different shapes to different tools. Import from here; do not copy.

Standard library only. Reads files; never writes.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import NamedTuple

# Directories that hold dependencies, build output, or tool caches. Walking them
# is slow and tells us nothing about the project's own design.
SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", ".idea", ".vscode", ".vs",
    "node_modules", "bower_components", "jspm_packages", "vendor",
    "__pycache__", ".venv", "venv", "env", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".gradle", ".dart_tool", ".terraform",
    "bin", "obj", "build", "dist", "out", "target", "_build", "deps",
    "coverage", "htmlcov", ".next", ".nuxt", ".svelte-kit", ".parcel-cache",
    "Pods", "Carthage", ".cargo", ".stack-work", "cmake-build-debug", "migrations",
})

TEST_DIR_NAMES = frozenset({
    "test", "tests", "spec", "specs", "__tests__", "testing",
    "unittest", "unittests", "test_suite", "integration-tests",
})

TEST_FILE_PATTERN = re.compile(
    r"(^test_|_test\.|\.test\.|\.spec\.|_spec\.|Tests?\.|Spec\.)", re.IGNORECASE
)

MAX_FILE_BYTES = 2_000_000
MAX_FILES_SCANNED = 40000


class Walk(NamedTuple):
    """Root-relative posix paths in walk order, and whether the cap cut the walk short."""

    paths: list
    truncated: bool


def is_skippable(directory_name: str) -> bool:
    return directory_name in SKIP_DIRS or (
        directory_name.startswith(".") and directory_name != ".github"
    )


def walk(root: Path, suffixes=None) -> Walk:
    """Every project file under root, optionally only those with the given suffixes.

    Stops at MAX_FILES_SCANNED and says so, so a caller never mistakes a partial
    walk for the whole project.
    """
    paths: list = []
    for current_dir, subdirs, filenames in os.walk(root):
        subdirs[:] = sorted(name for name in subdirs if not is_skippable(name))
        for filename in sorted(filenames):
            path = Path(current_dir) / filename
            if suffixes is not None and path.suffix.lower() not in suffixes:
                continue
            if len(paths) >= MAX_FILES_SCANNED:
                return Walk(paths, True)
            try:
                paths.append(path.relative_to(root).as_posix())
            except ValueError:
                continue
    return Walk(paths, False)


def is_test_path(relative_path: str) -> bool:
    parts = relative_path.split("/")
    if any(part.lower() in TEST_DIR_NAMES for part in parts[:-1]):
        return True
    return bool(TEST_FILE_PATTERN.search(parts[-1]))


def read_text(path: Path) -> str | None:
    """The file's text, or None when it is unreadable or too large to be source."""
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None
