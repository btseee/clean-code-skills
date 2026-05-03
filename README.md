# Clean Code Skills

Install-ready clean-code guidance for AI coding agents.

This repo packages one language-agnostic `clean-code` skill plus companion files for Claude Code, Codex-style agents, Gemini, GitHub Copilot, Cursor, and generic agent harnesses. The guidance covers meaningful names, focused functions, cohesive modules, clear tests, explicit boundaries, honest error handling, safe concurrency, incremental refactoring, and verified completion.

## Included

| Target | File |
| --- | --- |
| Agent Skill | `skills/clean-code/SKILL.md` |
| Deep chapter map | `skills/clean-code/references/chapter-map.md` |
| Claude Code plugin | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` |
| Codex-style plugin | `.codex-plugin/plugin.json` |
| Claude instructions | `CLAUDE.md` |
| Gemini instructions | `GEMINI.md` |
| Generic agent instructions | `AGENTS.md` |
| GitHub Copilot instructions | `.github/copilot-instructions.md`, `.github/instructions/clean-code.instructions.md` |
| Cursor rule | `.cursor/rules/clean-code.mdc` |
| Framework guide | `FRAMEWORKS.md` |
| Examples | `EXAMPLES.md` |

## Install

### Claude Code

```text
/plugin marketplace add btseee/clean-code-skills
/plugin install clean-code-skills@clean-code-skills
```

### Per Project

Install every supported agent file into another project:

```bash
bash scripts/install.sh --target /path/to/project all
```

Install only selected targets:

```bash
bash scripts/install.sh --target /path/to/project claude cursor copilot skill
```

The installer will not overwrite existing files unless you pass `--force`.

### Manual

- Claude Code: copy or merge `CLAUDE.md`.
- Gemini: copy or merge `GEMINI.md`.
- Generic agents and Codex-style CLIs: copy or merge `AGENTS.md`.
- Cursor: copy `.cursor/rules/clean-code.mdc`.
- GitHub Copilot: copy `.github/copilot-instructions.md` and `.github/instructions/clean-code.instructions.md`.
- Agent Skills: copy `skills/clean-code/` into the target skill directory.

## Publish

Make the repo public at `https://github.com/btseee/clean-code-skills`, then run:

```bash
bash scripts/validate.sh
git tag v1.0.0
git push origin main --tags
```

Recommended GitHub topics: `clean-code`, `agent-skills`, `claude-code`, `codex`, `cursor`, `github-copilot`, `ai-agents`, `code-review`, `refactoring`.

| Platform | Status | How to share |
| --- | --- | --- |
| Claude Code | Ready | Users add this repo as a plugin marketplace and install `clean-code-skills@clean-code-skills`. |
| Codex-style agents | Manifest ready | Share the GitHub URL and `.codex-plugin/plugin.json`; call it "Codex-ready" unless accepted into a specific registry. |
| Cursor | Rule ready | Share the project-rule install. A marketplace listing requires a separate Cursor or VS Code extension package. |
| GitHub Copilot | Repo install ready | Users install `copilot skill`; for discovery, submit to a Copilot resource catalog such as `github/awesome-copilot` if it accepts external plugins. |

## Core Behavior

Agents using this skill should:

1. Clarify assumptions that affect behavior, data, tests, security, or architecture.
2. Inspect nearby code and match local idioms before editing.
3. Make the smallest change that solves the request.
4. Use names, structure, tests, and boundaries to make intent obvious.
5. Verify with the narrowest meaningful check, then broaden checks when risk requires it.
6. Review the diff for unrelated edits, speculative abstractions, dead code, and hidden failure paths.

Clean code is not one language's style guide. Go should remain idiomatic Go, Rust should use ownership and types, SQL should stay set-oriented, React should keep rendering predictable, and shell scripts should stay boring and explicit.

## Scope

Use this skill for writing, fixing, refactoring, reviewing, testing, and designing code across languages, frameworks, scripts, queries, components, jobs, APIs, infrastructure, and libraries.

Do not use it to justify broad rewrites, personal style churn, new dependencies, or framework swaps without a task-specific reason and verification plan.

## Source Notes

The local `clean-code.pdf` was used as study material, but this repo does not redistribute or copy that text. The chapter map is an original, agent-oriented synthesis of the 17-chapter structure, concurrency appendix, legacy refactoring appendix, and heuristic cross-reference appendix.

## Validate

```bash
bash scripts/validate.sh
```

The validator checks required files, skill front matter, plugin JSON, shell syntax, installer output, LF line endings, and final newlines.

## License

MIT. See `LICENSE`.
