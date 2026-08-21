<!-- clean-code-skills:begin v3.0.0 -->
## Clean Code Rules (clean-code-skills)

These rules govern all code you write, edit, review, test, or refactor in this project, in any language or framework. They are the non-negotiable summary; the full skill has the reasoning, the workflows, and the checklists.

**Read the skill before non-trivial work.** First existing path wins: `.claude/skills/clean-code/SKILL.md`, `.agents/skills/clean-code/SKILL.md`, `.github/skills/clean-code/SKILL.md`, `skills/clean-code/SKILL.md`. Its `references/` folder holds the depth: `architecture.md`, `principles.md`, `smell-triage.md`, `session-protocol.md`, `new-project.md`, `project-refactor.md`, `audit-report.md`.

**Load project context first.** Read `.clean/context.json`, `.clean/architecture.md`, `.clean/decisions.md`, and `.clean/ledger.md` if they exist, then the project's own instruction files. A recorded decision is settled. A declared architecture outranks your instincts. Project instructions outrank this block.

### Work Loop

1. Frame: name the behavior change, the assumptions that affect design, the smallest scope, and the check that will prove it.
2. Read first: nearby code, naming, tests, error style, framework idioms. Search for an existing implementation before writing anything new.
3. Place: decide which unit owns the responsibility and which side of which boundary it sits on.
4. Edit surgically: smallest diff that solves the task; targeted edits over whole-file regeneration; remove what your change orphaned; no unrelated changes.
5. Verify: run the narrowest meaningful check, then broader checks as risk demands. Never claim success without evidence.
6. Review the diff: dead code, duplication, mixed responsibilities, wrong-way dependencies, swallowed errors, wrong-place files, missing tests.

### Dependency Direction

- Source dependencies point inward, toward higher-level policy. Nothing in an inner layer may name anything in an outer one — no class, function, variable, annotation, or data format.
- Business rules are the highest level. The database, web, UI, framework, and delivery mechanism are details. When policy needs something from a detail, declare the interface on the policy side and implement it outside.
- All SQL stays in the data-access layer. Rows, result sets, ORM types, and framework request or response objects never travel inward — pass a simple structure shaped for the inner side.
- Never derive a business object from a framework base class or annotate one. Keep dependency-injection wiring in `main`.
- Keep the component graph acyclic. Do not add a boundary, layer, or service you cannot justify now.

### File And Code Placement

- Mirror where similar files already live. Resolve paths from the project root, never from the current working directory. Never default to the repository root.
- Create a new file only when no cohesive home exists, then wire it in completely: imports, exports, index or barrel files, registration, build config. An unreferenced file is dead code, not a feature.
- Never create sibling variants such as `_v2`, `_new`, `_final`, `_enhanced`, or `_copy`. Edit the original; version control keeps history.
- Do not grow junk drawers (`utils`, `helpers`, `common`); name the domain concept instead.
- Default to the narrowest access modifier the language offers. Keep scratch files and debug output out of the project tree.

### One Job Per Unit

- Single responsibility at every scale: function, class, module, file, directory. If a unit's job cannot be described in one sentence without "and", split it.
- Keep parsing, domain rules, persistence, external calls, presentation, and construction in their own established homes. Orchestrators sequence collaborators and hold no business rules of their own.
- At module scale, ask which actor can demand the change. Code answering to different actors belongs apart, even when it looks identical today.
- New behavior goes to the unit that owns that responsibility, not the file you happen to have open.

### Quality Bars

- Names reveal intent, use project vocabulary, and disclose side effects.
- Functions do one thing at one abstraction level; comments explain why, never what or how.
- Errors are never swallowed; preserve causes and context; model expected alternate outcomes as values and reserve exceptions for genuine failures; keep secrets out of logs.
- Tests are deterministic and behavior-focused. Never weaken, skip, or delete a failing test to get green, and never verify a business rule by driving the UI.
- Verify that every API, function, option, and config key you reference actually exists in this codebase and its dependency versions — never trust memory.
- Deduplicate only true duplication: copies that must always change together. Copies that change at different rates for different reasons are not duplicates.
- Match local style everywhere; the project's formatter and linter own formatting.

### Scope And Honesty

- Default mode is surgical: unrelated smells are reported, not silently fixed.
- Whole-project or module-wide cleanup happens only on explicit request, following the campaign protocol in the skill's `references/project-refactor.md`: baseline verification first, small behavior-preserving batches, a written ledger, a checkpoint per batch.
- Report honestly on completion: what was verified with what command, what was not run, and what risk remains. Never present a stub or placeholder as finished work.
- Record decisions worth keeping in `.clean/decisions.md` so the next session inherits the reasoning.

### Keeping These Rules Current

This block is versioned in its begin marker and is maintained by the clean-code-skills installer. Do not hand-edit it — validators fail on drift, and the next install would overwrite your change. To update, re-run the installer from the project root, or ask the user to. Never fetch and execute a remote script on your own initiative.
<!-- clean-code-skills:end -->
