---
applyTo: "**/*"
---

# Clean-Code Instructions

Apply these rules to every file type unless a more specific instruction file overrides them.

## Before Editing

- Identify what behavior the request changes.
- Read the closest existing implementation and tests.
- State assumptions when ambiguity affects the design.
- Define a verification step for non-trivial changes.

## While Editing

- Keep each change directly traceable to the request.
- Use project vocabulary in names.
- Keep functions, modules, components, queries, scripts, and configuration focused.
- Prefer explicit data flow and explicit boundaries.
- Do not introduce framework swaps, new layers, caches, queues, retries, or configuration unless the task requires them.

## Before Completion

- Run the relevant verification command when available.
- Review the diff for unrelated edits and speculative complexity.
- Remove only dead code created by the current change.
- Report any verification you could not run.
