#!/usr/bin/env python3
"""Report runs of eight or more words that a file shares with the local, gitignored books.

Usage:
    python scripts/check_originality.py                 # what the skill ships
    python scripts/check_originality.py <file-or-folder>...

With no arguments it checks skills/, templates/, docs/, and README.md. It exits 1 when it finds a
shared run and 0 when it finds none, or when books/ is absent, since there is nothing to compare.
Standard library only; the books never leave this machine.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK_FOLDER = REPO_ROOT / "books"
DEFAULT_TARGETS = ("skills", "templates", "docs", "README.md")
RUN_LENGTH = 8
# The field's canonical rule statements, principle definitions, and heading-like titles are
# shared vocabulary, quoted so a reader can recognize the named rule, not copied prose.
CANONICAL = (
    "source code dependencies must point only inward toward higher level policies",
    "a module should be responsible to one and only one actor",
    "a software artifact should be open for extension but closed for modification",
    "the granule of reuse is the granule of release",
    "gather into components those classes that change for the same reasons and at the same times",
    "that change at different times and for different reasons",
    "force users of a component to depend on things they",
    "allow no cycles in the component dependency graph",
    "depend in the direction of stability",
    "a component should be as abstract as it is stable",
    "instability i fan out fan in fan out",
    "the web is a detail",
    "the database is a detail",
    "a good architect maximizes the number of decisions not made",
    "leave as many options open as possible for as long as possible",
    "architecture must support the use cases and operation",
    "the use cases and operation of the system",
    "production code until you have written a failing",
    "more production code than is sufficient to pass the currently failing test",
    "j1 avoid long import lists by using wildcards",
)


def words(text: str) -> list:
    return re.findall(r"[a-z0-9']+", text.lower())


def shingles(tokens: list) -> set:
    return {" ".join(tokens[i:i + RUN_LENGTH]) for i in range(len(tokens) - RUN_LENGTH + 1)}


def shared_runs(tokens: list, book: set) -> list:
    """Each maximal run of the file's words whose every eight-word window is in a book."""
    runs = []
    index = 0
    while index <= len(tokens) - RUN_LENGTH:
        if " ".join(tokens[index:index + RUN_LENGTH]) not in book:
            index += 1
            continue
        end = index + RUN_LENGTH
        while end < len(tokens) and " ".join(tokens[end - RUN_LENGTH + 1:end + 1]) in book:
            end += 1
        run = " ".join(tokens[index:end])
        if not any(statement in run for statement in CANONICAL):
            runs.append(run)
        index = end
    return runs


def markdown_files(arguments: list) -> list:
    files = []
    for argument in arguments or DEFAULT_TARGETS:
        path = Path(argument) if arguments else REPO_ROOT / argument
        if path.is_dir():
            files += sorted(path.rglob("*.md"))
        elif path.is_file():
            files.append(path)
    return files


def main(argv: list) -> int:
    books = sorted(BOOK_FOLDER.glob("*.md")) if BOOK_FOLDER.is_dir() else []
    if not books:
        print(f"No books in {BOOK_FOLDER}; nothing to compare.")
        return 0
    book = set()
    for path in books:
        book |= shingles(words(path.read_text(encoding="utf-8", errors="replace")))
    targets = markdown_files(argv)
    hits = 0
    for target in targets:
        for run in shared_runs(words(target.read_text(encoding="utf-8", errors="replace")), book):
            hits += 1
            print(f"{target}: {run}")
    print(f"{len(targets)} file(s), {hits} shared run(s) of {RUN_LENGTH} or more words")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
