---
name: clean-code
description: Use when writing, editing, reviewing, testing, planning, or refactoring code in any language or framework; creating files or deciding where code and folders belong; designing or changing module boundaries, layers, and dependencies; starting a new project; auditing or cleaning up an existing one; or compressing agent instruction files. Covers SOLID, design patterns, and the dependency rule.
license: MIT
compatibility: Works with no tooling; optional scripts need Python 3.8+, write only to .clean/, never use the network.
argument-hint: "[init | audit | clean-up | new-project <description> | plan <task> | review [files] | compress [files]]"
metadata:
  version: "4.0.0"
---

# Clean Code And Clean Architecture

## Before The First Edit: Load Context

You forget everything between sessions. `scripts/` and `references/` resolve from this file's
folder. Read in order; trivial edits (typo, comment) skip this gate and the review checklist.

1. **Stack.** `.clean/context.json`; missing: run `scripts/detect_stack.py`, or read manifests and
   file extensions.
2. **Packs.** Open each pack in `packs` or under "Read next" with the file-read tool (naming a pack
   is not reading it), except framework packs whose `pack_scopes` exclude your area. By hand:
   `clean-packs` index in `references/framework-map.md`; none: answer its adaptation questions.
3. **Layers.** `.clean/architecture.md`; see Layer Rules.
4. **Decisions.** `.clean/decisions.md`, `.clean/ledger.md`. Recorded decisions are settled; resume,
   never restart, campaigns in progress.
5. **Structure.** Your area's `.clean/structure.md` rows (grep path) or
   `scripts/map_structure.py --path <area>`; by hand, list the folder, open the two or three most
   similar files.
6. **Project instructions.** `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`,
   `README.md`.

On conflict, first wins: project instructions, recorded decisions, declared layers, local
conventions, framework pack, language pack, this skill. Only `init`, `audit`, `new-project` create
`.clean/`; plain sessions read it, offer to persist at the end.

## Operating Loop

1. **Frame**: behavior change, assumptions, smallest scope, success check. Ask only if ambiguity
   changes the implementation.
2. **Read** nearby code, naming, tests, error style, framework idiom; search for existing
   implementations first.
3. **Place**: owning unit; which side of which boundary.
4. **Edit surgically**: every changed line traces to the request; targeted edits, never whole-file
   regeneration; remove what your change orphaned.
5. **Verify**: narrowest meaningful check, then what the risk level owes (`review-checklist.md`);
   bug: reproducer test first; refactor: tests before and after. Never claim success without
   running something.
6. **Review the diff** with `references/review-checklist.md`, self-check included.

## Rules That Always Apply

**Placement.** Role decides folder, per pack roles and project layout; mirror similar files. New
file only without a cohesive home, then fully wired: imports, exports, registration, routes, DI,
build config; unreferenced files are dead code. Never default to repository root or current
directory. Never create sibling variants (`_v2`, `_new`, `_final`, `_copy`) or grow junk drawers
(`utils`, `helpers`, `common`); name the concept. Narrowest access modifier.

**One job per unit**, every scale: needs "and" to describe? Split. Parsing, domain rules,
persistence, external calls, presentation, wiring: separate homes. Orchestrators sequence
collaborators, hold no business rules. New behavior goes to its owning unit, not the open file.
Different actors' code stays apart, even if identical today.

**Minimal code.** Before writing code, stop at the first yes: Unneeded (YAGNI)? Write nothing.
Already in the codebase? Reuse it. Standard library, platform, or installed dependency does it? Use
that. One line? Write it. Else write the minimum. Never cut safety: validation, error handling,
security, accessibility.

**Code.** Names reveal intent in project vocabulary, one word per concept. Functions: one thing,
one abstraction level, few arguments, no flag arguments. Comments: why, briefly. Never swallow
errors: handle where a decision can be made, keep causes, model expected outcomes as values. Tests:
Three Laws of TDD, F.I.R.S.T.; never weaken, skip, or delete failing tests. Verify every API
against installed versions in `.clean/context.json`, never memory. Deduplicate only copies that
must change together (DRY). Formatter owns formatting. Design priority: tests pass, no duplicated
knowledge, intent expressed, fewest elements.

**Security.** Validate and encode input at every trust boundary, parameterize queries, keep
authorization beside the operation it protects, never put secrets in code, committed config, or
logs.

## Layer Rules, When Layers Are Declared

Strict when `.clean/architecture.md` declares layers: check with `scripts/check_boundaries.py`, or
read changed files' imports, naming each layer. Undeclared: follow the framework pack's idiomatic
structure; these rules guide judgement.

- **The Dependency Rule**: source dependencies point only inward, to higher-level policy; nothing
  inner names anything outer (class, function, variable, annotation, data format).
- Business rules highest; database, web, UI, framework, delivery mechanism are details behind
  policy-owned interfaces.
- SQL stays in data access. Rows, ORM types, framework request/response objects never travel
  inward; pass simple structures shaped for the inner side.
- Never derive business objects from framework base classes or annotate them; dependency-injection
  wiring in `main`.
- Component graph acyclic; depend toward stability; split hard-to-test from easy-to-test; no
  speculative boundaries.

## Commands

`/clean-code <argument>` (or `$clean-code`, `@clean-code`, `/skill:clean-code`) and plain language
route identically.

Argument | Follow
--- | ---
`init` (alias `questions`, "interview me") | `references/init.md`
`audit` | `references/audit-report.md`; changes no code
`clean-up` | `references/project-refactor.md` with `.clean/ledger.md`; no ledger: propose an audit (file count), await consent
`new-project <description>` | `references/new-project.md`
`plan <task>` | `references/plan.md`; edits nothing
`review [files]` | `references/review-checklist.md`, The `review` Command; edits nothing
`compress [files]` | `references/compress.md`; never touches the managed block
(none) | this file; `references/session-protocol.md` for multi-step or resumable work

## Load Plan

Read only what the task needs, from `references/`; long files via their Contents:

Task | Read
--- | ---
Review; agent smells A1-A10 | `review-checklist.md`
Risk level: LOW, MEDIUM, HIGH | `review-checklist.md`, Risk Levels
Comment cleanup (C1-C5, G12) | `comments.md`
Architecture style, design pattern, data access | `patterns.md`
New dependency | `framework-map.md`, Dependencies And Package Idioms
New boundary, layer, framework, or database | `architecture.md`
Tests | `tests.md`
Concurrency | `concurrency.md`
Security, trust boundaries, data versus objects, performance | `principles.md`
Naming or triaging a smell | `smell-triage.md`; IDs (G17, N7, T5...) in `chapter-map.md`
A named rule, exactly | `canon.md`
State for the next session | `memory-protocol.md`
Worked examples, templates | `examples.md`
Host hooks, commands, install paths | `host-matrix.md`
Scripts `detect_stack.py`, `scan_repo.py`, `map_structure.py`, `check_boundaries.py`, `check_compression.py`: flags, findings, exit codes; output is evidence, never a verdict | `tools.md`

## Scope Modes

**Surgical** (default): smallest slice; report unrelated smells, never fix them unless a requested
outcome needs it ("make the suite pass"): smallest fix, reported separately, never a weakened test.
**Campaign** (explicit request only): `references/project-refactor.md`; never a behavior change
inside a refactor batch.

## Completion Checklist

- Packs read before the first edit.
- Task solved; each changed line traces to it and obeys the rules above.
- New files placed by role, wired; no sibling variant, duplicate, dead code, scratch file, or
  debug output.
- Tests cover the change; none weakened.
- Verification reported honestly: risk level, results, what did not run, remaining risk.
- Lasting decisions in `.clean/decisions.md`; files added or moved and `.clean/` exists:
  `scripts/map_structure.py --write` run.
