# CLAUDE.md

Clean-code operating instructions for Claude Code. Merge these with project-specific instructions when installing into another repository.

## Always Apply

Use the `clean-code` skill when writing, editing, reviewing, or refactoring code in any programming language or framework. If the skill is not available by name, read the installed skill file from `skills/clean-code/SKILL.md` or `.github/skills/clean-code/SKILL.md`.

For trivial typo fixes, keep the process light. For any non-trivial behavior change, use the full loop below.

## Operating Loop

1. **Frame the task.** State assumptions that affect design, data, safety, or tests. Ask only when ambiguity would change the implementation.
2. **Read local context.** Inspect nearby code, tests, naming, error handling, and framework idioms before editing.
3. **Prefer the smallest solution.** Solve today's requirement. Do not add speculative abstractions, options, dependencies, or future features.
4. **Edit surgically.** Touch only files and lines required by the task. Preserve surrounding formatting and comments unless the task requires changing them.
5. **Make intent obvious.** Favor meaningful names, small functions, cohesive modules, explicit boundaries, and tests that describe behavior.
6. **Verify before claiming success.** Run the narrowest meaningful check first, then broader checks when the change has wider risk. Report what ran and what did not.
7. **Review the diff.** Remove dead code introduced by your change, check for hidden failure paths, and call out unrelated issues instead of fixing them silently.

## Clean-Code Rules

- Names should reveal intent, use domain language, and avoid misleading abbreviations.
- Functions should do one thing at one level of abstraction and avoid hidden side effects.
- Comments should explain why, constraints, or non-obvious tradeoffs. They should not narrate unclear code.
- Modules, classes, components, and scripts should be cohesive and have explicit boundaries.
- Error handling should preserve context, avoid swallowed failures, and match language idioms.
- Tests should be deterministic, readable, behavior-focused, and tied to risk.
- Concurrency should make ownership, cancellation, ordering, and shared state explicit.
- Refactors should preserve behavior and be verified before and after when possible.

## Anti-Loopholes

Do not rationalize broad edits with:

- "while I am here"
- "this will be more flexible later"
- "clean code means rewriting the whole thing"
- "there are no tests, so I will assume it works"
- "this framework is different, so the principles do not apply"

If a change cannot be verified, say exactly what was checked and what risk remains.
