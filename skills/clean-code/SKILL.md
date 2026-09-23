---
name: clean-code
description: Use when writing, editing, reviewing, testing, or refactoring code in any language or framework; when creating files or deciding where code and folders belong; when designing or changing module boundaries, layers, and dependencies; when starting a new project; or when auditing or cleaning up an existing one. Covers naming, functions, comments, error handling, tests, concurrency, security, code placement and folder structure, single responsibility, duplication, code smells, SOLID, the dependency rule, component boundaries, layering, testability, architectural drift, and verified surgical or whole-project refactoring, with rule packs for 19 languages and 21 frameworks.
license: MIT
compatibility: Works with no tooling. Optional scripts in scripts/ need Python 3.8+ and read-only filesystem access; they write only to .clean/ and never use the network.
argument-hint: "[init | audit | clean-up | new-project <description>]"
metadata:
  version: "3.2.0"
---

# Clean Code And Clean Architecture

Clean code makes intent, behavior, boundaries, and failure modes easy for the next maintainer to
understand and safely change. Clean architecture keeps the cost of a change proportional to its
scope. You forget everything between sessions: structure, names, placement, and written decisions
are how your work survives you.

## Before The First Edit: Load Context

This file's folder is the skill root; `scripts/` and `references/` resolve from it. In order, each
step with its manual equivalent:

1. **Stack.** Read `.clean/context.json`. Missing? Run `scripts/detect_stack.py`, or read the
   manifests and file extensions.
2. **Packs.** Read every pack listed under `packs`, or printed as "Read next". By hand: look the
   language and framework up in the `clean-packs` index in `references/framework-map.md`. No pack?
   Answer that file's adaptation questions.
3. **Layers.** Read `.clean/architecture.md`. Declared layers make the layer rules below strict, and
   `scripts/check_boundaries.py` enforces them. No declaration: follow the framework pack's
   idiomatic structure.
4. **Decisions.** Read `.clean/decisions.md` and `.clean/ledger.md`. A recorded decision is settled;
   a campaign in progress is resumed, never restarted.
5. **Structure.** Read the rows of `.clean/structure.md` for the area you will change (grep the
   path), or run `scripts/map_structure.py --path <area>`. By hand: list the folder and open the two
   or three most similar files.
6. **Project instructions.** `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`,
   `README.md`.

When rules conflict, the first wins: project instructions, recorded decisions, declared layers,
existing local conventions, the framework pack, the language pack, this skill. Only `init` and
`audit` create `.clean/`; a plain session reads it and offers to persist at the end.

## Operating Loop

1. **Frame** the behavior to change, the assumptions that matter, the smallest scope, and the check
   that proves it. Ask only when ambiguity changes the implementation.
2. **Read** nearby code, naming, tests, error style, and framework idiom — and search for an
   existing implementation before writing one.
3. **Place** it: which unit owns the responsibility, and which side of which boundary it sits on.
4. **Edit surgically.** Every changed line traces to the request. Targeted edits, never whole-file
   regeneration; remove what your change orphaned; report unrelated smells instead of fixing them.
5. **Verify** with the narrowest meaningful check, then broader ones as risk demands: a reproducer
   test first for a bug, tests before and after a refactor. Never claim success without running
   something.
6. **Review the diff** with `references/review-checklist.md`, including its self-check.

## Rules That Always Apply

**Placement.** A unit's role decides its folder: middleware lives with middleware, controllers with
controllers, per the framework pack's roles and the project's existing layout. Mirror the two or
three most similar files. Create a file only when no cohesive home exists, then wire it in
completely — imports, exports, registration, routes, DI, build config; an unreferenced file is dead
code. Never default to the repository root or the current directory. Never create sibling variants
(`_v2`, `_new`, `_final`, `_copy`). Never grow junk drawers (`utils`, `helpers`, `common`); name
the concept. Default to the narrowest access modifier.

**One job per unit**, at every scale. If a unit's job needs "and" to describe, split it. Parsing,
domain rules, persistence, external calls, presentation, and wiring live in their own homes; an
orchestrator sequences collaborators and holds no business rule. New behavior goes to the unit that
owns it, not the file that is open. At module scale, code answering to different actors belongs
apart, even when it looks identical today.

**Code.** Names reveal intent in the project's vocabulary, one word per concept. Functions do one
thing at one level of abstraction, with few arguments and no flag arguments. Comments explain why,
briefly. Errors are never swallowed: handle them where a decision can be made, keep causes, model
expected outcomes as values. Tests follow the Three Laws of TDD and F.I.R.S.T.; never weaken, skip,
or delete a failing test. Verify every API against the installed versions in
`.clean/context.json`, never memory. Deduplicate only true duplication (DRY): copies that must
change together. The formatter owns formatting. When rules conflict: tests pass, no duplicated
knowledge, intent expressed, fewest elements.

## Layer Rules, When Layers Are Declared

With a `.clean/architecture.md` declaration these are strict; without one they inform judgement.

- **The Dependency Rule**: source dependencies point only inward, toward higher-level policy.
  Nothing inner names anything outer — no class, function, variable, annotation, or data format.
- Business rules are the highest level; the database, web, UI, framework, and delivery mechanism
  are details. When policy needs a detail, declare the interface on the policy side and implement
  it outside.
- All SQL stays in data access. Rows, ORM types, and framework request or response objects never
  travel inward; pass simple structures shaped for the inner side.
- Never derive a business object from a framework base class or annotate one. Dependency-injection
  wiring lives in `main`.
- Keep the component graph acyclic, depend toward stability, and split the hard-to-test from the
  easy-to-test. Do not add a boundary you cannot justify now.

Read `references/architecture.md` before adding a dependency, boundary, layer, framework, or
database. Check with `scripts/check_boundaries.py`, or read the imports of each file you changed
and name each one's layer.

## Commands

Invoked as `/clean-code <argument>` (or `$clean-code`, `@clean-code`, `/skill:clean-code`) or in
plain language; both route identically.

| Argument | Also triggered by | Follow |
| --- | --- | --- |
| `init` (alias `questions`) | "set up clean-code", "interview me" | `references/init.md`: detect the stack, interview, map the structure, write `.clean/` |
| `audit` | "audit this project" | `references/audit-report.md`: every file reviewed, sweeps until one adds nothing, `.clean/` filled; changes no code |
| `clean-up` | "clean this up" | `references/project-refactor.md`, consuming `.clean/ledger.md`. No ledger? Propose the audit with its file count; wait for consent |
| `new-project <description>` | "start a project" | `references/new-project.md`, seeded with the description |
| (none) | any coding task | this file and `references/session-protocol.md` |

## Load Plan

Beyond this file and your packs, read only what the task needs:

| Task | Read in `references/` |
| --- | --- |
| Review or diff review | `review-checklist.md` |
| New dependency, boundary, layer, framework, or database | `architecture.md`, via its contents |
| Writing or fixing tests | `tests.md` |
| Concurrency | `concurrency.md` |
| Naming or triaging a smell | `smell-triage.md`, and `chapter-map.md` for IDs (G17, N7, T5...) |
| A named rule, exactly | `canon.md` |
| Persisting state for the next session | `memory-protocol.md` |
| Worked examples and output templates | `examples.md` |
| Host hooks, commands, install paths | `host-matrix.md` |

## Tools

Optional, standard-library Python, no network. Output is evidence for your judgement, never a
verdict; every workflow names the manual equivalent.

| Script | Answers |
| --- | --- |
| `detect_stack.py` | which languages, frameworks, packs, test command, and layout? |
| `map_structure.py` | what each file declares, its role and purpose; what is misplaced, mixed, duplicated, or cyclic? |
| `scan_repo.py` | oversized files, sibling variants, junk drawers, debug output, skipped tests? |
| `check_boundaries.py` | does the code obey the declared layers? |

## Scope Modes

**Surgical** (default): everything above, applied to the smallest slice that solves the task;
unrelated smells are reported, not fixed. **Campaign** (explicit request only): follow
`references/project-refactor.md` — baseline first, small behavior-preserving batches, a written
ledger, a checkpoint per batch, and never a behavior change inside a refactor batch.

## Completion Checklist

- The task is solved and every changed line traces to it.
- New files sit where roles and local conventions say, fully wired in; no sibling variant, no
  duplicate implementation.
- Each new or grown unit passes the one-sentence test; every added dependency points a permitted
  way.
- Tests match the behavior changed, and none was weakened.
- No dead code, scratch files, or debug output remains.
- Verification is reported honestly: what ran and its result, what did not run, what risk remains.
- Decisions worth keeping are in `.clean/decisions.md`; if files were added or moved and `.clean/`
  exists, `scripts/map_structure.py --write` has refreshed the map.
