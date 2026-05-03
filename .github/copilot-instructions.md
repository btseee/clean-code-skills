# Repository-Wide Clean-Code Instructions

These instructions guide GitHub Copilot Chat, Copilot code review, and Copilot coding agents across this repository.

## Purpose

Apply clean-code discipline to all code changes and reviews, regardless of language or framework.

When `.github/skills/clean-code/SKILL.md` is present, treat it as the canonical detailed guidance and use this file as the repository-wide baseline.

## General Standards

- Inspect nearby code and tests before editing.
- Match local style, architecture, naming, and framework idioms.
- Keep diffs focused on the user's request.
- Avoid speculative abstractions, unused extension points, and new dependencies without evidence.
- Use meaningful names that reveal domain intent.
- Keep functions, methods, components, jobs, modules, and queries cohesive.
- Prefer clear control flow over cleverness.
- Treat error handling, boundaries, validation, security, and concurrency as first-class design concerns.
- Add or update tests when behavior, risk, or regression prevention requires it.
- Verify with relevant commands before claiming success.

## Review Standards

When reviewing code, prioritize:

- incorrect behavior at boundaries
- hidden side effects or temporal coupling
- broad rewrites not required by the task
- unclear names or misleading comments
- swallowed errors or unsafe defaults
- missing tests for changed behavior
- concurrency, lifecycle, cancellation, or shared-state hazards
- security-sensitive input, output, storage, logging, and permissions

Avoid language-specific rules in this file unless they apply universally. Put narrow rules in `.github/instructions/*.instructions.md` files.
