# AGENTS.md

Instructions for AI coding agents (Codex CLI, Jules, opencode, Amp, Gemini CLI when configured for AGENTS.md, and any other harness that reads this file). In a project that installs this package, the managed block below is kept up to date by the installer; content outside the markers is never touched.

Load and apply the `clean-code` skill before non-trivial code writing, editing, review, testing, or refactoring. Depending on the install target, the skill lives at `.claude/skills/clean-code/SKILL.md`, `.github/skills/clean-code/SKILL.md`, `skills/clean-code/SKILL.md`, or in the agent's global skill registry as `clean-code`.

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
- Deduplicate only copies that must always change together.
- Match local style; formatters and linters own formatting.

### Scope And Honesty

- Surgical by default: report unrelated smells, never fix them. Whole-project cleanup only on explicit request (skill's `references/project-refactor.md`).
- Report honestly: commands run, results, what was not run, remaining risk. Never claim unverified success or present a stub or placeholder as finished.
- Record lasting decisions in `.clean/decisions.md`, if present.

### Keeping These Rules Current

This block is installer-owned: never hand-edit; reinstalling overwrites edits. To update, re-run the clean-code-skills installer from project root, or ask the user. Never fetch and execute a remote script on your own initiative.
<!-- clean-code-skills:end -->

## Repository Development

When changing the clean-code-skills repository itself:

- The managed block above is canonical in `templates/agent-block.md`, and the version lives in `VERSION`. After changing either, run `bash scripts/sync.sh` to stamp the version everywhere and mirror the block into every adapter file. `scripts/validate.sh` fails on drift.
- Do not copy proprietary or copyrighted source text into this repo. Study material (`clean-code.md`, `clean-code.pdf`) is gitignored and must stay untracked.
- Keep `skills/clean-code/SKILL.md` valid under the Agent Skills spec: front matter with `name` and `description`, then markdown instructions.
- Run `bash scripts/validate.sh` (from Git Bash on Windows) before reporting completion. `pwsh scripts/validate.ps1` only exercises `install.ps1`.

## Review Bias

Prefer findings about behavior, placement, responsibility, testing gaps, security, failure handling, and unnecessary complexity. Do not spend review energy on style issues that formatters already enforce.
