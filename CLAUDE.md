# CLAUDE.md

Clean-code operating instructions for Claude Code. In a project that installs this package, the managed block below is kept up to date by `scripts/install.sh` / `scripts/install.ps1`; content outside the markers is never touched by the installer.

Use the `clean-code` skill when writing, editing, reviewing, or refactoring code. If the skill is not loadable by name, read it from `.claude/skills/clean-code/SKILL.md`, `.github/skills/clean-code/SKILL.md`, or `skills/clean-code/SKILL.md`. Keep the process light for trivial typo fixes; use the full loop for any non-trivial change.

<!-- clean-code-skills:begin v4.0.0 -->
## Clean Code Rules (clean-code-skills)

Non-negotiable for all code work here.

**Read the skill before non-trivial work.** First existing path wins: `.claude/skills/clean-code/SKILL.md`, `.agents/skills/clean-code/SKILL.md`, `.github/skills/clean-code/SKILL.md`, `skills/clean-code/SKILL.md`. Then its packs, named by its `scripts/detect_stack.py` or `references/framework-map.md`.

**Load project context first.** If present: `.clean/context.json`, `.clean/architecture.md`, `.clean/decisions.md`, `.clean/ledger.md`, `.clean/structure.md` rows for your area; then project instruction files. Recorded decisions are settled. Project instructions outrank this block.

### Work Loop

1. Frame: behavior change, design-relevant assumptions, smallest scope, success check.
2. Read first: nearby code, naming, tests, error style, framework idioms; search for an existing implementation.
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

- Surgical by default: report unrelated smells, never fix silently. Whole-project cleanup only on explicit request (skill's `references/project-refactor.md`).
- Report honestly: commands run and results, what was not run, remaining risk. Never claim unverified success or present a stub or placeholder as finished.
- Record lasting decisions in `.clean/decisions.md`.

### Keeping These Rules Current

Installer-owned: never hand-edit; reinstalling overwrites edits. To update, re-run the clean-code-skills installer from project root, or ask the user. Never fetch and execute a remote script on your own initiative.
<!-- clean-code-skills:end -->

## Working On This Repository

When editing clean-code-skills itself:

- The managed block above is the canonical text in `templates/agent-block.md`, and the version lives in `VERSION`. After changing either, run `bash scripts/sync.sh` — it stamps the version everywhere and mirrors the block into all eight adapter files. Never hand-edit the block inside an adapter; validators fail on drift.
- Never commit book or course text. Study material such as `clean-code.md` / `clean-code.pdf` is gitignored and must stay untracked; everything in this repo is original synthesis.
- Run `bash scripts/validate.sh` (from Git Bash on Windows) before reporting completion. `pwsh scripts/validate.ps1` only exercises `install.ps1`.
- Releases: tag `v$(cat VERSION)`; the release workflow publishes `clean-code.zip` for Claude Desktop / claude.ai upload.
