# Clean Code Skills

Install-ready clean-code guidance for coding agents. This repo packages one language-agnostic skill plus companion instruction files for Claude Code, Codex-style agents, Gemini, GitHub Copilot, Cursor, and generic agent harnesses.

The content is an original synthesis of durable clean-code practices: meaningful names, small functions, focused modules, readable tests, explicit boundaries, honest error handling, safe concurrency, incremental refactoring, and verification before completion. It was shaped to behave like the Karpathy-style guideline repo: agents should think before coding, keep changes simple, edit surgically, and define verifiable success criteria.

## What This Repo Gives Agents

| Target | File |
| --- | --- |
| Agent Skill spec | `skills/clean-code/SKILL.md` |
| Claude Code plugin | `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` |
| Codex-style plugin | `.codex-plugin/plugin.json` |
| Claude project instructions | `CLAUDE.md` |
| Gemini project instructions | `GEMINI.md` |
| Generic agent instructions | `AGENTS.md` |
| GitHub Copilot repository instructions | `.github/copilot-instructions.md` |
| GitHub Copilot path instructions | `.github/instructions/clean-code.instructions.md` |
| Cursor project rule | `.cursor/rules/clean-code.mdc` |
| Cross-language adaptation guide | `FRAMEWORKS.md` |
| Behavior examples | `EXAMPLES.md` |
| Full chapter coverage map | `skills/clean-code/references/chapter-map.md` |

## Install

### Claude Code Plugin

From Claude Code, add this repo as a marketplace and install the plugin:

```text
/plugin marketplace add btseee/clean-code-skills
/plugin install clean-code-skills@clean-code-skills
```

The plugin exposes the reusable `clean-code` skill from `skills/clean-code`.

### Per-Project Install

Copy the agent files into another project:

```bash
bash scripts/install.sh --target /path/to/project all
```

Install only specific harness files when you want a smaller footprint:

```bash
bash scripts/install.sh --target /path/to/project claude cursor copilot skill
```

The installer refuses to overwrite existing files unless `--force` is provided.

### Manual Install

Use the file that matches your agent:

- Claude Code: copy or merge `CLAUDE.md`.
- Gemini: copy or merge `GEMINI.md`.
- Generic agents and Codex-style CLIs: copy or merge `AGENTS.md`.
- Cursor: copy `.cursor/rules/clean-code.mdc` into `.cursor/rules/`.
- GitHub Copilot: copy `.github/copilot-instructions.md` and optionally `.github/instructions/clean-code.instructions.md`.
- Agent Skills: copy `skills/clean-code/` into your skill directory. The installer places it in both `skills/clean-code/` and `.github/skills/clean-code/` for broad agent compatibility.

## Core Behavior

Agents using this repo should follow six gates on any non-trivial code task:

1. Clarify the goal and name assumptions.
2. Inspect local style before editing.
3. Choose the smallest change that solves the current problem.
4. Keep code readable through names, structure, tests, and explicit boundaries.
5. Verify with the narrowest meaningful command, then broader checks when risk demands it.
6. Review the diff for unrelated edits, speculative abstractions, dead code introduced by the change, and hidden failure paths.

Clean code is not one language's style guide. It adapts to the local ecosystem: Go should remain idiomatic Go, Rust should use ownership and types, SQL should stay set-oriented, React should keep rendering predictable, and shell scripts should stay boring and explicit.

## Skill Scope

Use this skill for:

- writing new code
- fixing bugs
- refactoring existing code
- reviewing pull requests
- creating or updating tests
- designing APIs, modules, classes, functions, scripts, queries, components, jobs, and infrastructure code

Do not use it to justify broad rewrites, personal style churn, new dependencies, or framework swaps without a task-specific reason and verification plan.

## Source Notes

The local `clean-code.pdf` was used as study material, but this repository does not redistribute or copy that text. The guidance here is an original, agent-oriented synthesis intended for practical engineering work across languages and frameworks. The detailed chapter map covers the 17-chapter structure, the concurrency appendix, the legacy refactoring appendix, and the heuristic cross-reference appendix as actionable checklists.

## Validate

Run:

```bash
bash scripts/validate.sh
```

The validator checks required files, skill front matter, plugin JSON, shell syntax, installer output, and CRLF line endings.

## How To Know It Is Working

You should see:

- smaller diffs with fewer drive-by edits
- clearer assumptions before implementation
- fewer speculative abstractions
- tests or concrete checks tied to the requested behavior
- names and structure that explain intent without excessive comments
- explicit handling of errors, boundaries, and concurrency risks

## License

MIT. See `LICENSE`.
