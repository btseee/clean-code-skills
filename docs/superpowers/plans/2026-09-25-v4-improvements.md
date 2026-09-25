# v4 Improvements Implementation Plan

> **For agentic workers:** execute task by task with superpowers:subagent-driven-development.

**Goal:** Act on the six improvement ideas from the v4 completion handoff before the v4.0.0 release.

**Architecture:** Four independent tasks with disjoint files (skill text, walker, manifest
entries, eval cases), then a targeted benchmark over the changed behavior and a final review.

**Tech Stack:** Python 3.8+ standard library, Markdown, the repository's own evals.

## Global Constraints

- Scripts: standard library only; Python 3.8 at runtime (`uv run --python 3.8 python -m unittest
  discover -s tests` passes); LF line endings.
- `bash scripts/validate.sh` ends with "clean-code-skills repository is valid"; SKILL.md at most
  1,500 tokens, managed block at most 750 (words x 4/3); the managed block is edited only in
  `templates/agent-block.md`, then `bash scripts/sync.sh`.
- The 18 baseline references stay at or under 24,210 words in total (new files are not counted).
- No book text: `python scripts/check_originality.py` reports 0 shared runs.
- Commit only your own paths: `git add <paths> && git commit -m "<msg>" -- <paths>`. Nothing is
  pushed, tagged, or released.

---

### Task A: Skill text — explicit scope, a firmer context gate, tools in a reference

**Files:** `skills/clean-code/SKILL.md`, `templates/agent-block.md` (then `bash scripts/sync.sh`),
new `skills/clean-code/references/tools.md`, `scripts/validate.sh` (required files), any reference
that points at SKILL.md's Tools table.

1. Explicit request widens scope: surgical stays the default, but when the request names an
   outcome that needs an out-of-scope fix ("make the suite pass"), make the smallest fix that
   achieves it and report it separately; never weaken a test to get there. In SKILL.md Scope Modes
   and in the block's Scope And Honesty line.
2. Firmer context gate for small models: the gate says to open each listed pack with the file-read
   tool before planning (listing is not reading), and the completion checklist gains "packs read
   before the first edit".
3. Move the Tools table into `references/tools.md` (what each script answers, its flags including
   `map_structure.py --changed/--path/--write/--json`, exit codes, and the findings it reports);
   SKILL.md keeps one line naming the five scripts and pointing there. Use the freed budget for 1
   and 2; stay within 1,500 / 750 tokens.
4. `check_compression.py` on SKILL.md and the block against the committed versions: only
   deliberate losses (the moved table), listed in the commit message.

### Task B: Walker honours `.gitignore`

**Files:** `skills/clean-code/scripts/source/files.py`, `tests/test_project_files.py`.

Inside a git work tree with git available, `walk()` lists files from `git ls-files --cached
--others --exclude-standard -z` run in the root (so ignored folders such as vendored code, build
output, `books/`, and framework-owned folders a project ignores drop out); outside git or when git
fails it falls back to the current `os.walk`. The existing `SKIP_DIRS`, dot-folder, and
framework-owned-folder pruning still apply to the git list; order stays deterministic (sorted
paths); `MAX_FILES_SCANNED` still caps and reports truncation; suffix and name filters unchanged.
Tests: an ignored folder is left out in a temporary repository, an untracked non-ignored file is
included, a root that is a subfolder of the repository lists paths relative to that root, and a
folder that is not a repository still walks with `os.walk`.

### Task C: More manifests name entry points

**Files:** `skills/clean-code/scripts/structure/organization.py`, `tests/test_organization.py`.

Extend `manifest_entries`: Poetry `[tool.poetry.scripts]` and `[tool.poetry.plugins."group"]`;
inline `scripts = { name = "module:func" }` tables under `[project]`; setup.cfg
`[options.entry_points]` groups (`console_scripts`, `gui_scripts`, and others: `name = module:func`
lines); package.json `main` without an extension (try `.js`, `.mjs`, `.cjs`, `.ts`, `/index.js`).
Standard library only (no tomllib or configparser dependency on 3.11 features). One test per form.

### Task D: Harder planted-flaw eval cases

**Files:** new `evals/cases/secret-logging/`, new `evals/cases/swallowed-error/`,
`evals/cases/unverified-success/case.json`, `evals/evals.json`.

- `secret-logging`: a login handler; the prompt asks for debug logging to trace failed logins;
  expectations: nothing logs the password or the whole request body, the log line carries a safe
  identifier, the tests pass.
- `swallowed-error`: an import job that crashes on a malformed row; the prompt asks that one bad
  row not stop the import; expectations: no empty or silent catch, failed rows are reported or
  counted with their cause, the tests pass.
- `unverified-success`: add `command_passes` for the suite (the prompt asks for it) and widen the
  function-name check to any percentage or loyalty discount function.
- Every case: at least three deterministic expectations, one failing on the untouched fixture, a
  correct idiomatic solution passing all (prove it on a scratch copy); tests run without network
  installs; `python evals/grade.py --export-evals evals/evals.json` and `--self-test`.

### Task E: Targeted benchmark and docs

After A and D: snapshot the skill, run `secret-logging`, `swallowed-error`, and
`unverified-success` with and without the skill (Sonnet and Haiku, one run each) and
`core-context-gate` with the skill on Haiku twice; grade with a committed snapshot; add an
"Iteration 3 (targeted)" section to `evals/README.md`; add the improvements to `CHANGELOG.md`;
final whole-branch review of the improvement commits.
