# AGENTS.md

Instructions for AI coding agents working in this repository or in projects that install this package.

## Use The Clean-Code Skill

Load and apply the `clean-code` skill before non-trivial code writing, editing, review, testing, or refactoring. Depending on the install target, the skill may live at `skills/clean-code/SKILL.md`, `.github/skills/clean-code/SKILL.md`, or in the agent's global skill registry as `clean-code`.

## Required Agent Behavior

- Surface assumptions before implementation when they affect behavior, architecture, data, tests, security, or user-visible outcomes.
- Read local conventions before editing. Existing idioms beat generic advice.
- Keep changes minimal and directly traceable to the request.
- Prefer simple, boring code until requirements prove complexity is needed.
- Use names, structure, and tests to communicate intent.
- Make failure modes explicit. Do not swallow errors or invent silent fallbacks.
- Verify the claim you plan to make. Evidence comes before completion language.

## Repository Development

When changing this repository:

- Keep root instruction files, Cursor rules, Copilot instructions, and the skill aligned.
- Do not copy proprietary or copyrighted source text into this repo.
- Keep `skills/clean-code/SKILL.md` under the Agent Skills spec: front matter with `name` and `description`, followed by markdown instructions.
- Run `bash scripts/validate.sh` before reporting completion.

## Review Bias

Prefer findings about behavior, maintainability, testing gaps, security, failure handling, and unnecessary complexity. Do not spend review energy on style issues that automation or local formatters already enforce.
