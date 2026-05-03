# GEMINI.md

Clean-code instructions for Gemini and other agents that read root project guidance.

## Activation

Apply the clean-code skill whenever a task involves writing, editing, reviewing, testing, or refactoring code. If the skill is not available by name, read it from `skills/clean-code/SKILL.md` or `.github/skills/clean-code/SKILL.md`. This applies to every programming language, framework, query language, script, configuration format, and infrastructure file.

## Behavior Contract

1. Clarify assumptions that would change the implementation.
2. Inspect nearby code before editing.
3. Match the project's existing idioms.
4. Make the smallest change that satisfies the request.
5. Prefer readable names and cohesive structure over comments that explain messy code.
6. Keep functions, components, classes, modules, jobs, and queries focused.
7. Treat errors, boundaries, security, and concurrency as part of the design.
8. Add or update tests when risk, behavior, or regressions require them.
9. Verify before claiming the work is complete.
10. Report limitations honestly.

## Guardrails

- Do not introduce speculative abstractions or configuration.
- Do not rewrite unrelated code.
- Do not change formatting or comments outside the requested area.
- Do not hide failures behind broad catches, null fallbacks, or silent defaults.
- Do not impose one language's style on another language.
- Do not claim tests, builds, or linters pass unless they were run and their output supports the claim.

When a project has more specific instructions, follow those first and use these clean-code rules as the shared baseline.
