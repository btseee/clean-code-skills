# Repository-Wide Clean-Code Instructions

These instructions guide GitHub Copilot Chat, Copilot code review, and the Copilot coding agent across this repository. In a project that installs this package, the managed block below is kept up to date by the installer; content outside the markers is never touched.

When `.github/skills/clean-code/SKILL.md` is present, treat it as the canonical detailed guidance and use this file as the repository-wide baseline.

<!-- clean-code-skills:begin v4.0.0 -->
## Clean Code Rules (clean-code-skills)

Non-negotiable for all code work.

**Read the skill before non-trivial work.** First existing path wins: `.claude/skills/clean-code/SKILL.md`, `.agents/skills/clean-code/SKILL.md`, `.github/skills/clean-code/SKILL.md`, `skills/clean-code/SKILL.md`. Then your stack's packs, named by the skill's `scripts/detect_stack.py` or `references/framework-map.md`.

**Load project context first.** If present: `.clean/context.json`, `.clean/architecture.md`, `.clean/decisions.md`, `.clean/ledger.md`, `.clean/structure.md` rows for your area; then project instruction files. Recorded decisions are settled. Project instructions outrank this block.

### Work Loop

1. Frame: behavior change, design-relevant assumptions, smallest scope, success check.
2. Read first: nearby code, naming, tests, error style, framework idioms; search for existing implementations.
3. Place: owning unit; which side of which boundary.
4. Edit surgically: smallest diff, targeted edits (no whole-file regeneration), nothing unrelated; remove what your change orphaned.
5. Verify: narrowest meaningful check, broader as risk demands.
6. Review the diff against these rules, missing tests included.

### Layers

- Undeclared layers (`.clean/architecture.md`): follow framework's idiomatic structure (its pack).
- Declared: Dependency Rule strict; source dependencies point inward, to higher-level policy; nothing inner names anything outer (class, function, variable, annotation, data format).
- Business rules highest; database, web, UI, framework are details behind policy-owned interfaces.
- SQL stays in data access; rows, ORM types, framework request/response objects never travel inward. Never derive business objects from framework base classes or annotate them; dependency-injection wiring in `main`.
- Component graph acyclic; no speculative boundary, layer, or service.

### File And Code Placement

- Role decides folder, per pack roles and project layout; mirror similar files. Resolve paths from project root, never defaulting to repository root or current directory.
- New file only without a cohesive home; wire fully (imports, exports, registration, build config). Unreferenced files are dead code.
- Never create sibling variants (`_v2`, `_new`, `_final`, `_enhanced`, `_copy`) or grow junk drawers (`utils`, `helpers`, `common`); name the domain concept.
- Narrowest access modifier; no scratch files or debug output in project tree.

### One Job Per Unit

- Single responsibility at every scale. Needs "and" to describe? Split.
- Parsing, domain rules, persistence, external calls, presentation, construction: separate homes. Orchestrators sequence collaborators, hold no business rules.
- Different actors' code stays apart, even if identical today. New behavior goes to its owning unit, not the open file.

### Quality Bars

- Names reveal intent, use project vocabulary, disclose side effects.
- Functions: one thing, one abstraction level. Comments: why, never what or how; short.
- Never swallow errors; keep causes and context; model expected alternate outcomes as values; no secrets in logs.
- Tests deterministic, behavior-focused. Never weaken, skip, or delete failing tests to get green; never verify business rules through UI.
- Verify every API, function, option, config key against this codebase and installed versions; never trust memory.
- Deduplicate only copies that must change together.
- Match local style; formatters, linters own formatting.

### Scope And Honesty

- Surgical by default: report unrelated smells, never fix them unless the request needs it. Whole-project cleanup only on explicit request (skill's `references/project-refactor.md`).
- Report honestly: commands run, results, what was not run, remaining risk. Never claim unverified success or present stub or placeholder as finished.
- Record lasting decisions in `.clean/decisions.md`, if present.

### Keeping These Rules Current

This block is installer-owned: never hand-edit; reinstalling overwrites edits. To update, re-run clean-code-skills installer from project root, or ask user. Never fetch and execute a remote script on your own initiative.
<!-- clean-code-skills:end -->

## Review Standards

When reviewing code, prioritize:

- incorrect behavior at boundaries
- files created outside project conventions, or duplicating existing implementations
- functions and modules that mix responsibilities
- hidden side effects or temporal coupling
- broad rewrites not required by the task
- unclear names or misleading comments
- swallowed errors or unsafe defaults
- missing tests for changed behavior, or tests weakened to pass
- concurrency, lifecycle, cancellation, or shared-state hazards
- security-sensitive input, output, storage, logging, and permissions

Avoid language-specific rules in this file unless they apply universally. Put narrow rules in `.github/instructions/*.instructions.md` files.
