#!/usr/bin/env python3
"""Which symbols a source file declares, for every language the scanners know.

The entry point for the structure map: pick the extractor for a file's language
and return one FileSymbols record. Extraction is evidence, never a verdict: a
construct the patterns do not recognise is left out, never guessed.

Standard library only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import brace_grammars
import symbols_braces
import symbols_python
from symbol_model import FileSymbols, Symbol  # noqa: F401  (re-exported for callers)

LANGUAGE_BY_SUFFIX = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".vue": "vue", ".svelte": "svelte",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala",
    ".cs": "csharp", ".php": "php", ".dart": "dart",
    ".go": "go", ".rs": "rust", ".swift": "swift",
    ".c": "c", ".h": "cpp", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".hh": "cpp", ".m": "objc", ".mm": "objc",
}

SUPPORTED_SUFFIXES = frozenset(LANGUAGE_BY_SUFFIX)

_BRACE_GRAMMARS = {
    "javascript": brace_grammars.JAVASCRIPT,
    "typescript": brace_grammars.TYPESCRIPT,
    "java": brace_grammars.JAVA,
    "kotlin": brace_grammars.KOTLIN,
    "scala": brace_grammars.SCALA,
    "csharp": brace_grammars.CSHARP,
    "php": brace_grammars.PHP,
    "dart": brace_grammars.DART,
    "go": brace_grammars.GO,
    "rust": brace_grammars.RUST,
    "swift": brace_grammars.SWIFT,
    "c": brace_grammars.C,
    "cpp": brace_grammars.CPP,
    "objc": brace_grammars.OBJC,
}


def language_of(path: str) -> Optional[str]:
    return LANGUAGE_BY_SUFFIX.get(Path(path).suffix.lower())


def extract(path: str, text: str) -> Optional[FileSymbols]:
    """The symbols declared in text, the contents of the file at path; None when
    the language is not supported."""
    language = language_of(path)
    if language is None:
        return None
    if language == "python":
        return symbols_python.extract(path, text)
    if language in {"vue", "svelte"}:
        return brace_grammars.extract_component(path, text, language)
    return symbols_braces.extract(_BRACE_GRAMMARS[language], path, text)
