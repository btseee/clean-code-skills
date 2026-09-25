# Tools

Five scripts in `scripts/`, each saving many file reads. Python 3.8+, standard library, no
network; they write only when asked, under `.clean/` or where `--output` points. Output is
evidence, never a verdict: confirm each finding against the code. No Python: use a step's manual
equivalent where the workflow names one; otherwise report the check as not run.

All take `--json` for machine-readable output; all but `check_compression.py` take `--root <dir>`
(default `.`). Exit 2 means the run could not start: a bad root, flag, or input. Inside a git
work tree they list files through `git ls-files`, so gitignored paths are skipped.

## detect_stack.py

Which languages, frameworks, and packs apply (`packs`, `pack_scopes`); test runners and suggested
verification commands; source roots, layer candidates, quality tools, dependency versions.

- `--write` saves `.clean/context.json`, merging (its `confirmed` object and unknown keys
  survive); `--output <path>` writes elsewhere, resolved from the current directory.
- Exit 0 done; 1 could not write.

## scan_repo.py

Smell evidence by measurement, any language: large files, sibling variants, junk drawers, debug
output, commented-out code, comment blocks, TODO markers, skipped tests, long lines, areas without
tests.

- `--changed` scans only files changed against HEAD, staged, or untracked (outside git: nothing,
  with a warning); `--top N` caps each summary list (default 15; `--json` is complete).
- Exit 0 whatever it finds.

## map_structure.py

Every source file's symbols, role, and purpose; the component graph; whether code sits where its
role belongs.

- `--path <folder>` summarizes one area; `--changed` keeps findings and moves touching files git
  reports changed against HEAD, or untracked (outside a repository: every file); `--write` saves
  `.clean/structure.md` and `.clean/structure.json`, never with `--changed`; `--depth N` sets the
  folder depth of a component (default 2); `--top N` caps findings per kind in `structure.md`
  (default 25); `--packs a,b` overrides the packs whose roles apply, as paths under `references/`
  (`frameworks/django.md`): a bare `django` matches no file and is silently skipped.
- Findings, keyed as in `structure.json`: `misplaced` (symbol or file outside its role's home),
  `mixed` (homeless file holding two or more roles), `duplicates` (identical function bodies, or
  identical but for names and literals), `name_clashes` (one public type or global function name
  in several files), `synonyms` (one concept behind several same-meaning verbs), `cycles`
  (components depending on each other), `names` (a name breaking a naming rule, cited by ID),
  `family` (three or more files sharing a name and importing each other), `junk_drawer` (folder
  named for no concept), `flat_folder` (more than fifteen production files), `unreferenced`
  (possibly unused, G9), `comment_heavy` (comments at least 40% of non-blank lines, twenty or
  more).
- Also in the JSON: `truncated` (the file cap cut the walk short), `unparsed` (files whose symbols
  could not be read, with the reason), `moves` (the proposed moves).
- `structure.md` opens with the findings, then `## Proposed moves` (`from -> to (why)`), which the
  clean-up placement batch confirms before moving anything.
- Exit 0 done; 1 could not write; 2 also for `--changed` with `--write`, or a roles block that does
  not parse.

## check_boundaries.py

Does every import obey the layers declared in `.clean/architecture.md` (or `ARCHITECTURE.md`,
`docs/architecture.md`)?

- `--config <path>` reads another declaration; `--print-config` shows the parsed layering.
- Exit 0 no violation; 1 violations; 2 no declaration, or its globs match no file.

## check_compression.py

What a terse rewrite lost: headings, fenced code, inline code, URLs, rule IDs, numbers; prints the
token change (words x 4/3).

- `python check_compression.py ORIGINAL COMPRESSED [--json]`
- Exit 0 nothing lost; 1 something lost.
