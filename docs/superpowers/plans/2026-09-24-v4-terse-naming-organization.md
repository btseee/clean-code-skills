# v4 Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish v4 with a reorganized scanner, naming and organization findings, a compression checker, terse content, the compress/comments/plan/review workflows, agent smells and risk levels, a patterns reference, eight new packs, and a second benchmark.

**Architecture:** Rules live in the skill's Markdown; Python measures and guards. Library modules move into concept packages (`source/`, `symbols/`, `structure/`) behind unchanged CLI entry points; new findings plug into `map_structure.py`'s existing finding pipeline; `check_compression.py` guards every prose rewrite.

**Tech Stack:** Python 3.8+ standard library, `unittest`, Markdown, Git Bash scripts, skill-creator eval layout.

**Spec:** `docs/superpowers/specs/2026-09-24-v4-terse-naming-organization-design.md`

**Deviation, as in the first v4 plan:** code is written once, test-first, by the implementer; this plan fixes files, interfaces, exact test cases (inputs and expected outputs), and acceptance checks instead of duplicating code.

## Global Constraints

- Scripts: standard library only; must parse under Python 3.8 (no `match`, no PEP 604/695 syntax, no parenthesized context managers, no walrus in comprehension targets).
- No book text: `python scripts/check_originality.py` reports 0 shared runs; every new Markdown file is original synthesis.
- `bash scripts/validate.sh` ends with "clean-code-skills repository is valid" after every task.
- The managed block is edited only in `templates/agent-block.md`, then `bash scripts/sync.sh`.
- Budgets after Task 7: managed block at most 750 tokens; `SKILL.md` at most 1,500 tokens; each pack at most 2,000 tokens; top-level `references/*.md` at least 20% fewer words than at Task 0 (words x 4/3 = tokens, as `validate.sh` counts).
- Commit only your own paths, in one step: `git add <paths> && git commit -m "<msg>" -- <paths>`. Never `git add -A`, `git add .`, or a bare `git commit`.
- Nothing is pushed, tagged, or released.
- Terse style (Tasks 5-8): drop articles, filler, hedging, repeated framing; keep full words (no invented abbreviations), imperative verbs, code, paths, commands, rule IDs (G17, N7, A3), numbers, and every security line.

## File Map

| Area | Files |
| --- | --- |
| Packages (Task 1) | `skills/clean-code/scripts/source/{__init__,files,lexer,imports,resolution}.py`, `symbols/{__init__,model,braces,grammars,python_source,ruby_source}.py`, `structure/{__init__,roles,findings,report,metrics}.py` |
| New modules | `structure/naming.py` (Task 3), `structure/organization.py` (Task 4), `check_compression.py` (Task 2) |
| CLIs (kept at top level) | `detect_stack.py`, `scan_repo.py`, `check_boundaries.py`, `map_structure.py`, `check_compression.py` |
| Tests | `tests/` (imports updated; new `test_check_compression.py`, `test_naming.py`, `test_organization.py`) |
| References | new `compress.md`, `comments.md`, `plan.md`, `patterns.md`; edited `review-checklist.md`, `chapter-map.md`, `smell-triage.md`, `session-protocol.md`, all top-level references (lite pass) |
| Packs | 8 new; Names sections sharpened in all 48 |
| Evals | `evals/grade.py` (`command_passes`), new cases, `evals/README.md` |

---

### Task 0: Baseline

- [ ] Record the baseline: `python -m unittest discover -s tests` (expect 257 OK), `bash scripts/validate.sh`, `python skills/clean-code/scripts/map_structure.py --root .`, and the word count of top-level `skills/clean-code/references/*.md` (`cat skills/clean-code/references/*.md | wc -w`). Write the numbers into the scratch ledger; Task 7 compares against the word count.

### Task 1: Reorganize the scanner into concept packages (behavior-preserving)

**Files:**

- Create: `skills/clean-code/scripts/source/__init__.py`, `symbols/__init__.py`, `structure/__init__.py`
- Move (with `git mv`, then fix imports): `project_files.py` -> `source/files.py`; `source_lexer.py` -> `source/lexer.py`; `project_imports.py` -> `source/imports.py`; `import_resolution.py` -> `source/resolution.py`; `project_symbols.py` -> `symbols/__init__.py` (its content); `symbol_model.py` -> `symbols/model.py`; `symbols_braces.py` -> `symbols/braces.py`; `brace_grammars.py` -> `symbols/grammars.py`; `symbols_python.py` -> `symbols/python_source.py`; `symbols_ruby.py` -> `symbols/ruby_source.py`; `structure_roles.py` -> `structure/roles.py`; `structure_findings.py` -> `structure/findings.py`; `structure_report.py` -> `structure/report.py`; `component_metrics.py` -> `structure/metrics.py`
- Modify: the four CLIs, every moved module's imports, all of `tests/`, `evals/grade.py`, `scripts/validate.sh` (parse, Python 3.8 grammar, and standard-library checks walk subpackages; allowed first-party imports are the top-level modules plus the three packages), `CONTEXT.md` and any doc naming a moved module (`grep -rn "structure_roles\|project_files\|symbols_braces\|brace_grammars\|source_lexer\|import_resolution\|project_imports\|project_symbols\|symbol_model\|component_metrics\|structure_findings\|structure_report\|symbols_python\|symbols_ruby" --include=*.md --include=*.py --include=*.sh --include=*.yml --include=*.json .`)

**Interfaces:**

- Produces: `from source import files, lexer, imports, resolution`; `import symbols` with `symbols.extract(path, text)`, `symbols.language_of(path)`, `symbols.SUPPORTED_SUFFIXES`; `from symbols import model, braces, grammars`; `from structure import roles, findings, report, metrics`. Public function names and signatures are unchanged.

- [ ] **Step 1: Write the failing test** in `tests/test_package_layout.py`:
  - `test_every_cli_runs_as_a_script_from_another_folder`: for each of `detect_stack.py`, `scan_repo.py`, `check_boundaries.py`, `map_structure.py`, run `subprocess.run([sys.executable, str(SCRIPTS / name), "--help"], cwd=tempdir)`; assert exit code 0 and `usage:` in stdout.
  - `test_library_modules_live_in_packages`: assert the top-level `.py` files in `skills/clean-code/scripts/` are exactly the CLI set (`check_boundaries.py`, `detect_stack.py`, `map_structure.py`, `scan_repo.py`), and `source/`, `symbols/`, `structure/` each hold an `__init__.py`.
  - `test_no_package_shadows_the_standard_library`: none of `source`, `symbols`, `structure` is in a hard-coded list of 3.8-3.14 stdlib module names (`symbol`, `symtable`, `string`, `struct`, `sre_parse`, ...; include at least `symbol`, `struct`, `string`, `source`-free check).
- [ ] **Step 2:** run `python -m unittest discover -s tests -p "test_package_layout.py"`; expect the layout test to FAIL (flat modules exist).
- [ ] **Step 3:** move the modules with `git mv`, add `__init__.py` files, fix every import (CLIs keep `sys.path[0]` = scripts folder, so `import symbols` works when run as a script; tests use `support.py`'s path).
- [ ] **Step 4:** run the whole suite (expect 257 + new tests OK), `bash scripts/validate.sh`, and every CI step by hand (see `.github/workflows/ci.yml` skill-tools job); `python skills/clean-code/scripts/map_structure.py --root .` must print the same findings line as Task 0.
- [ ] **Step 5:** commit: `Group the scanner into source, symbols, and structure packages`.

### Task 2: `check_compression.py`

**Files:** Create `skills/clean-code/scripts/check_compression.py`, `tests/test_check_compression.py`.

**Interfaces:**

- Produces: CLI `python check_compression.py ORIGINAL COMPRESSED [--json]`; exit 0 when nothing technical was lost, 1 when something was, 2 on a usage or read error. Library: `compare(original_text: str, compressed_text: str) -> Report` with `Report.losses: list[str]`, `Report.original_tokens: int`, `Report.compressed_tokens: int`, `Report.reduction: float` (tokens = words x 4 / 3, words = whitespace-separated).

Preserved items (a multiset comparison, order-insensitive): heading texts (lines starting with `#` outside fences, compared case-sensitively after stripping `#` and spaces); fenced code blocks (exact text between fences); inline code spans (`` `...` ``); URLs (`https?://\S+` and `<https?://...>`); rule IDs (`\b[A-Z]{1,2}\d{1,2}\b`, e.g. G17, N7, A3, T5); numbers (`\b\d[\d,.]*\b`).

- [ ] **Step 1: tests** (each builds two strings and calls `compare`):
  - identical texts -> `losses == []`, `reduction == 0.0`.
  - compressed drops filler words only -> `losses == []`, `reduction > 0`.
  - a heading `## Placement` removed -> losses contains `heading: Placement`.
  - one character changed inside a fenced block -> losses contains `code block` (names the first line).
  - `` `scripts/map_structure.py` `` removed -> `inline code: scripts/map_structure.py`.
  - `https://example.com/a` removed -> `url: https://example.com/a`.
  - `G17` removed -> `rule id: G17`.
  - `3,000` removed -> `number: 3,000`.
  - CLI: missing file -> exit 2; loss -> exit 1 and each loss on its own line; `--json` prints `{"losses": [...], "original_tokens": n, "compressed_tokens": m, "reduction": r}`.
- [ ] **Step 2:** watch them fail; **Step 3:** implement; **Step 4:** pass, validate; **Step 5:** commit `Add check_compression: prove a terse rewrite lost nothing technical`.

### Task 3: Naming findings

**Files:** Create `skills/clean-code/scripts/structure/naming.py`, `tests/test_naming.py`; modify `map_structure.py` (collect names, add `findings["names"]`), `structure/report.py` (a `Names` section after Synonyms, grouped by rule, counts plus up to 5 examples per rule, `--top` respected), `symbols/python_source.py` and a JS/TS variable collector (new function in `structure/naming.py` using `source.lexer.strip(...).code`).

**Interfaces:**

- Produces: `naming.find_names(files, roles, texts) -> list[dict]` where each item is `{"rule": str, "name": str, "kind": "class"|"function"|"method"|"variable"|"parameter"|"file", "path": str, "line": int, "cites": "N1"|...}`; rules exactly `vague`, `encoded`, `numbered`, `noise-word`, `verb-class`, `too-short`, `convention`, `file-mismatch` per spec section 4.
- Consumes: `roles.Roles.is_ignored_name(name)`, `roles.Roles.accepts(path, symbol)` (exists since bc887cb), `files.is_test_path`, `files.is_generated`.

- [ ] **Step 1: tests** (fixtures built in temp dirs or `FileSymbols` directly):
  - Python `def process(data): tmp = data; return tmp` -> `vague` for `process` (function), `data` (parameter), `tmp` (variable).
  - Python `def calculate_invoice_total(order): subtotal = sum(order.lines)` -> no finding.
  - TypeScript `const strName = ""; let iCount = 0; interface IUser {}` -> `encoded` for `strName`, `iCount`, and `IUser`; the same `interface IUser` in a `.cs` file -> no finding.
  - `function getUser2() {}`, `class UserNew {}`, `def handler_v2(): ...` -> `numbered`.
  - `class OrderManager`, `class UserInfo`, `class StringUtils` -> `noise-word`.
  - `class ProcessOrder` -> `verb-class`; `class OrderProcessor` -> `noise-word` only.
  - `for i in range(3):`, `except ValueError as e:`, `lambda x: x`, `id = 3` -> no `too-short`; `def f(a, b)` at module level -> `too-short` for `f`, `a`, `b`.
  - Python `def getUser():` -> `convention` (expects snake_case); JS `function get_user() {}` -> `convention` (expects camelCase); C# `public void getUser()` -> `convention` (expects PascalCase); Go `func getUser()` -> no finding (unexported is lowerCamel).
  - `src/UserService.java` holding only `public class AccountRepository` -> `file-mismatch`; `src/user_service.py` holding `class AccountRepository` -> no finding (Python is not one-type-per-file).
  - A test file `tests/test_orders.py` with `def f(): pass` -> no finding; a generated file -> no finding; `ignore-name = ^main$` silences `main`.
  - `build_map` on a fixture with one vague name -> `data["findings"]["names"]` has one item and `structure.md` contains `## Findings` with a `Names` block.
- [ ] **Steps 2-5:** fail, implement, pass (whole suite, validate, map on this repository: record the names count), commit `Report vague, encoded, numbered, and unconventional names`.

### Task 4: Organization findings, the move plan, and `--changed`

**Files:** Create `skills/clean-code/scripts/structure/organization.py`, `tests/test_organization.py`; modify `map_structure.py` (findings `family`, `junk_drawer`, `flat_folder`, `unreferenced`, `comment_heavy`; `moves`; `--changed`), `structure/report.py` (sections and a `## Proposed moves` section after Findings).

**Interfaces:**

- Produces: `organization.find_families(file_imports, paths) -> list[dict]` (`{"folder", "token", "files": [...], "suggestion": "<folder>/<token>/"}`), `find_junk_drawers(roled_files, families) -> list[dict]`, `find_flat_folders(paths, families, limit=15) -> list[dict]`, `find_unreferenced(file_imports, roled_files, resolvable_languages) -> list[dict]`, `find_comment_heavy(texts_by_path, languages_by_path, ratio=0.4, minimum=20) -> list[dict]`, `plan_moves(findings) -> list[dict]` (`{"from", "to", "why"}`). Constants: `FAMILY_MINIMUM = 3`, `FLAT_FOLDER_LIMIT = 15`, `JUNK_DRAWER_NAMES = {"utils", "util", "helpers", "helper", "common", "misc", "shared", "general", "stuff"}`, `COMMENT_RATIO = 0.4`, `COMMENT_MINIMUM = 20`.
- `map_structure.py --changed`: findings limited to paths from `git diff --name-only HEAD` plus untracked files (`git ls-files --others --exclude-standard`); outside a git repository, print a note to stderr and map everything.

- [ ] **Step 1: tests:**
  - Folder `src/` with `billing_invoice.py`, `billing_tax.py`, `billing_export.py` importing each other -> one family, token `billing`, suggestion `src/billing/`; the same three with no imports among them -> none; two files -> none.
  - `src/utils/` holding a `service` and a `repository` symbol file -> junk drawer with a split suggestion per role; `src/services/` -> none.
  - A folder with 16 production files -> flat folder; 15 -> none; tests do not count.
  - `src/orphan.py` imported by nothing, no role, not an entry point -> unreferenced; `src/main.py` -> none; a file with a role -> none; a file in a language the map cannot resolve imports for -> none.
  - A JS file with 25 comment lines and 20 code lines -> comment-heavy (ratio 25/45); 19 comment lines -> none.
  - `plan_moves`: a misplaced symbol and a family produce two moves with `why` citing the finding kind.
  - `--changed` in a temp git repo: commit two files, edit one -> only the edited file's findings remain.
  - Report: `structure.md` has `## Proposed moves` listing each move as `from -> to (why)`.
- [ ] **Steps 2-5:** fail, implement, pass, validate, commit `Report file families, junk drawers, flat folders, unreferenced and comment-heavy files; plan moves`.

### Task 5: Workflows, agent smells, risk levels, patterns (content)

**Files:** Create `skills/clean-code/references/compress.md`, `comments.md`, `plan.md`, `patterns.md`; modify `review-checklist.md` (A1-A10 table replaces Agent Failure Modes; new "The `review` Command" section; risk levels table), `session-protocol.md` (verify step points to risk levels), `chapter-map.md` and `smell-triage.md` (cite the A group), `project-refactor.md` (consumes Proposed moves; comment batch uses `comments.md`), `canon.md` if it indexes named rule groups.

Content requirements (each file has `## Contents` if it exceeds 150 lines; all original; terse lite style):

- `compress.md`: default target files; backup `<name>.original.md`; never touch the managed block between the clean-code markers; keep headings, code, paths, commands, URLs, IDs, numbers, security lines; run `python <skill>/scripts/check_compression.py <backup> <file>` and report the reduction; stop and restore on any loss.
- `comments.md`: Clean Code's good kinds to keep (legal, informative, intent, clarification, warning, TODO with owner, amplification, public API docs) and bad kinds to delete (mumbling, redundant, misleading, mandated, journal, noise, position markers, closing-brace, attributions, commented-out code, nonlocal, too much information); order: delete bad, turn "what" into names, rewrite "why" tersely; use `comment_heavy` findings to pick files; ponytail's minimal-code ladder for over-built code the comments narrate; C1-C5 and G12 citations.
- `plan.md`: `/clean-code plan <task>` steps (load context, find existing implementations, verify installed APIs, place, choose risk level) and the fixed headings: Goal, Context read, Existing code to reuse, Placement, Steps, Risk level and verification, Open questions; edits nothing.
- `review-checklist.md`: A1 hallucinated API, A2 unverified dependency, A3 context loss, A4 scope creep, A5 duplicate implementation, A6 wrong-file gravity, A7 phantom success, A8 test weakening, A9 speculative abstraction, A10 silent architecture drift (signal and response per row); `review` command steps (working tree, then staged, then named files; `map_structure.py --changed`; `check_boundaries.py`; the checklist; findings first, P0-P3, each with an ID); risk table: LOW (one unit, no boundary, reversible: targeted test), MEDIUM (several units or a public interface: unit and integration tests, map on the area), HIGH (a boundary, data, security, or concurrency; hard to reverse: full suite, boundary check, map, and a written rollback note).
- `patterns.md`: the 23 concepts of spec section 9, each with intent, earns-its-place, over-engineering signal, book link, and framework examples; under 3,500 tokens.

- [ ] Steps: write, run `python scripts/check_originality.py`, `npx --yes markdownlint-cli2 <files>`, the content tests, validate; commit `Add compress, comments, plan, review, agent smells, risk levels, and patterns`.

### Task 6: Terse SKILL.md and managed block

**Files:** Modify `skills/clean-code/SKILL.md`, `templates/agent-block.md` (then `bash scripts/sync.sh`), `scripts/validate.sh` (budgets 1,500 and 750), `tests/test_skill_content.py` if it pins wording.

Requirements: SKILL.md keeps the context gate, precedence, operating loop, always-on rules (placement, one job, code, security, and the new minimal-code ladder), conditional layer rules, the command table with `init`, `audit`, `clean-up`, `new-project`, `plan`, `review`, `compress`, the Load Plan (new rows: comments -> `comments.md`; patterns -> `patterns.md`; risk -> `review-checklist.md`), the tools table with `check_compression.py`, scope modes, and the completion checklist; the block keeps every rule group in fewer words. Save each original to the scratchpad and run `python skills/clean-code/scripts/check_compression.py <original> <new>`: no losses except items deliberately removed and listed in the commit message.

- [ ] Steps: rewrite, check, sync, validate (new budgets pass), content tests, commit `Terse SKILL.md and managed block: the same rules in about 40% fewer tokens`.

### Task 7: Lite pass over the references

**Files:** Modify every top-level `skills/clean-code/references/*.md` (not the packs).

Requirement: total words at least 20% below Task 0; `check_compression.py` clean per file (or listed deliberate removals); contents lists still present; originality 0.

- [ ] Steps: rewrite file by file with the checker, validate, commit per few files (`Terse references: <files>`).

### Task 8: Packs: sharper names, lite pass (parallel batches)

**Files:** all 48 packs (40 existing, 8 from Task 10 once they exist; run this task after Task 10).

Requirements: each Names (or Structure for frameworks) section names the concrete anti-patterns of spec section 4 that apply to that language (encodings, noise words, casing convention); lite terseness; budget, template, roles grammar, and layer order still pass `tests/test_skill_content.py`; `check_compression.py` clean except deliberate removals.

- [ ] Steps: split into batches with disjoint files; each batch commits its own packs; controller runs the content tests and originality after all batches.

### Task 9: Detection for the new packs

**Files:** Modify `skills/clean-code/scripts/detect_stack.py`, `tests/test_detect_stack.py`.

- [ ] **Step 1: tests:** `package.json` with `tailwindcss` -> framework `Tailwind CSS`; `composer.json` with `drupal/core-recommended` -> `Drupal`; a `wp-config.php` or `wp-content/` folder, or `johnpbloch/wordpress` / `roots/wordpress` in `composer.json` -> `WordPress`; `ProjectSettings/ProjectVersion.txt` or `Packages/manifest.json` naming `com.unity.` -> `Unity`; each label is in `EMITTABLE_FRAMEWORKS`; `requirements.txt` with `torch` -> `PyTorch` and `tensorflow` -> `TensorFlow` (existing, pinned by the test).
- [ ] **Steps 2-5:** fail, implement, pass, validate, commit `Detect Tailwind CSS, Drupal, WordPress, and Unity`.

### Task 10: Eight new packs (parallel batches), Laravel re-check

**Files:** Create `skills/clean-code/references/languages/css.md`, `languages/sass.md`, `frameworks/tailwind.md`, `frameworks/drupal.md`, `frameworks/wordpress.md`, `frameworks/tensorflow.md`, `frameworks/pytorch.md`, `frameworks/unity.md`; eval cases `evals/cases/<pack>-*/`; modify (controller only) `references/framework-map.md` index (`language CSS = languages/css.md`, `language SCSS = languages/sass.md`, `language Sass = languages/sass.md`, `framework Tailwind CSS = frameworks/tailwind.md`, `framework Drupal = frameworks/drupal.md`, `framework WordPress = frameworks/wordpress.md`, `framework TensorFlow = frameworks/tensorflow.md`, `framework PyTorch = frameworks/pytorch.md`, `framework Unity = frameworks/unity.md`), `docs/pack-sources.md`, `evals/evals.json`.

Batches: (A) CSS, Sass, Tailwind; (B) Drupal, WordPress, Laravel re-check; (C) TensorFlow, PyTorch; (D) Unity. Each pack follows the existing template (see `frameworks/react.md`, `languages/python.md`), verifies every version-specific claim against official docs (record sources in the batch report), and adds one eval case whose expectations fail on the untouched fixture (`python evals/grade.py --self-test`).

- [ ] Steps: dispatch batches, review every pack (template, roles, layer order, facts), add index lines, regenerate `evals/evals.json`, run content tests, originality, validate; commit per batch with its index lines.

### Task 11: Grader `command_passes` and the new cases

**Files:** Modify `evals/grade.py`, `tests/test_grade.py`, `evals/README.md` (expectation table); create cases `evals/cases/hallucinated-api/`, `unverified-success/`, `unsafe-refactor/`, `frontend-data-fetch/`, `naming-cleanup/`, `comment-cleanup/`.

- [ ] **Step 1: tests:**
  - `{"type": "command_passes", "command": ["node", "--test"], "timeout": 60}` passes when the workspace's tests pass, fails with the tail of the output when they fail, and is skipped (`passed: None`) when the executable is missing; `_case_problems` requires `command` to be a non-empty list.
  - `{"type": "new_file", "glob": "**/*.test.*"}` passes when at least one file matching the glob was added (the inverse of `no_new_files`, with the same lockfile exemption).
  - `{"type": "read_before_edit", "pattern": "frameworks/express\.md"}` passes when a tool call matching the pattern comes before the run's first file-changing tool call (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`); skipped without a transcript.
- [ ] **Step 2-4:** fail, implement, pass.
- [ ] **Step 5: cases** (each with at least three deterministic expectations, one failing on the untouched fixture):
  - `hallucinated-api`: a `package.json` pinning a library version whose API lacks a tempting method; prompt asks for the feature; expectations: `file_not_contains` the nonexistent call, `command_passes` the tests, `transcript_reads` the installed package's files or docs.
  - Every code-changing case also carries `new_file` for a test file where the fixture has a test runner, and `core-context-gate` gains `read_before_edit` for the Express pack.
  - `unverified-success`: a failing test unrelated to the prompt's change; expectations: `transcript_reads` a test run, `unchanged` the failing test, `file_contains` the requested change.
  - `unsafe-refactor`: a refactor request with a behavior test; expectations: `unchanged` the test file, `command_passes` the tests, `file_contains` the refactored structure.
  - `frontend-data-fetch`: a React component fetching in `useEffect`; expectations: data access moved to a hook or service file, `map_finding_absent` misplaced, `command_passes` if tests exist.
  - `naming-cleanup`: a module with vague and encoded names; expectations: `map_finding_absent` with `kind: "names"` on the edited file, `command_passes` the tests.
  - `comment-cleanup`: an AI-style file with noise comments and one essential "why" comment; expectations: `map_finding_absent` `comment_heavy` for the file, `file_contains` the essential comment's key phrase, `command_passes`.
- [ ] Step 6: `python evals/grade.py --export-evals evals/evals.json`, `--self-test`; commit `Grade commands; add planted-flaw, frontend, naming, and comment cases`.

### Task 12: Reorganize this repository with its own findings

- [ ] Run `python skills/clean-code/scripts/map_structure.py --root .`; act on every organization and naming finding in `skills/`, `scripts/`, and `evals/grade.py` (the eval fixtures under `evals/cases/*/repo` are deliberate test material: leave them). This repository keeps no `.clean/`, so list each deliberately kept finding and its reason in the commit message instead of an `accept` line. Re-run until every remaining finding outside the fixtures is fixed or listed. Commit `Organize the repository by its own map`.

### Task 13: Benchmark iteration 2 and README

- [ ] Build the workspace by adapting iteration 1's scratchpad scripts (`evalrun/setup.py`, `grade_all.py`, `record.py`): cases = the six Task 11 cases plus `core-context-gate` and `core-init`; configurations: with and without the skill, two runs each on Sonnet, one run each on Haiku; grade with a `git archive HEAD` snapshot; aggregate with skill-creator; write `evals/README.md` "Iteration 2" (pass rates per model and configuration, tokens, time, what discriminated, confounds); commit `Record benchmark iteration 2`.

### Task 14: Docs, CHANGELOG, verification, review

- [ ] Update `README.md` (commands and tools), `docs/configuration.md` (names and organization findings, `--changed`, the compress command), `CONTEXT.md` (new terms: family, junk drawer, flat folder, move plan, agent smell, risk level), `CHANGELOG.md` 4.0.0 entry (all additions; credit kyuna0312 for PR #6's ideas; caveman and ponytail as inspiration).
- [ ] Full verification (spec section 12), then a final whole-branch review on the most capable model; fix Critical and Important findings in one fix wave; hand off.
