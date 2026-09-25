# Host Matrix

This skill: a folder of Markdown plus standard-library Python scripts — the entire Agent Skills
standard. Beyond that, hooks, commands, permissions, memory, session-start behavior are
host-specific. This file maps what each host offers.

**Never depend on a host capability for correctness** — deterministic enforcement beats an
instruction the model might skip. Missing? Fall back to the prose step.

## Skill discovery paths

Where each host looks for skills; project-scoped roots are relative to the repo. Paths come from
vendor documentation; an undocumented one says so, not guessed.

| Host | Personal | Project |
| --- | --- | --- |
| Claude Code | `~/.claude/skills` | `.claude/skills` (nested; per `--add-dir`) |
| OpenAI Codex CLI | `~/.agents/skills`, `/etc/codex/skills` (admin) | `.agents/skills`, scanned upward from cwd to repo root |
| Codex App (ChatGPT desktop / web) | in-product only | in-product only |
| GitHub Copilot (CLI and VS Code) | `~/.copilot/skills`, `~/.agents/skills` | `.github/skills`, `.claude/skills`, `.agents/skills` |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `.gemini/skills`, `.agents/skills` |
| Google Antigravity | `~/.gemini/config/skills` | `.agents/skills` (legacy alias `.agent/skills`) |
| Cursor | `~/.agents/skills`, `~/.cursor/skills`, `~/.claude/skills`, `~/.codex/skills` | `.agents/skills`, `.cursor/skills`, `.claude/skills`, `.codex/skills` |
| Amp | `~/.agents/skills`, `~/.config/agents/skills` | `.agents/skills` |
| OpenCode | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` | `.opencode/skills`, `.claude/skills`, `.agents/skills` |
| Factory Droid | `~/.factory/skills`, `~/.agents/skills` | `.factory/skills`, `.agents/skills` |
| Devin CLI | `~/.agents/skills`, `~/.config/devin/skills` | `.agents/skills`, `.devin/skills`, `.windsurf/skills` |
| Kimi Code | `~/.kimi-code/skills`, `~/.agents/skills` | `.kimi-code/skills`, `.agents/skills` |
| Grok Build CLI | `~/.grok/skills`, `~/.agents/skills` | `.grok/skills` |
| Hermes Agent | `~/.hermes/skills` | `.hermes/skills`, `.agents/skills` |
| pi | `~/.pi/agent/skills`, `~/.agents/skills` | `.pi/skills`, `.agents/skills` |

**`.agents/skills` is the shared root: every host above reads it project-side except Claude Code,
Grok Build CLI, and the Codex App** — the installer (`scripts/install.sh`,
github.com/btseee/clean-code-skills) writes it under the `agents` profile.

Three exceptions, paths above: **Claude Code** and **Grok Build CLI** skip the shared root
entirely; **Antigravity**'s personal root differs, though its project root matches it.

The **Codex App** has no on-disk skill directory: install in-product (Plugins → Skills, or
folder/zip); its binary reads the Codex paths above.

## Frontmatter

Standard, and safe to rely on: these fields only.

| Field | Required | Limit |
| --- | --- | --- |
| `name` | yes | 64 chars, lowercase, digits and hyphens, matching the directory name |
| `description` | yes | 1024 chars; what every host matches against for relevance |
| `license` | no | short |
| `compatibility` | no | 500 chars; environment requirements |
| `metadata` | no | string-to-string map |

`allowed-tools` is experimental — **never depend on it.** `user-invocable`,
`disable-model-invocation`, `context`, `argument-hint` are single-host extensions — safe to add
(unrecognized fields are ignored), not safe to rely on.

Body budget: `SKILL.md` under 500 lines, roughly 5,000 tokens; depth belongs in `references/`,
loaded on demand.

## Capability support

| Capability | Where it exists | Portable substitute |
| --- | --- | --- |
| Session-start hook | Claude Code (`SessionStart`), others | Step 1 of `session-protocol.md` |
| Post-edit hook | Claude Code (`PostToolUse` on edits) | Step 16 (dependency direction) |
| Pre-commit enforcement | git, on every host | none needed — see `assets/hooks/pre-commit` |
| Slash commands | varies, see below | name it: "run the audit workflow" |
| Tool permissions | every host, all differently | declare needs in `compatibility`; keep scripts read-only |
| Persistent memory | a few hosts | `.clean/` on disk — portable, host-independent |
| Subagents | several hosts | do the work inline |

## How a user forces a skill

Every host activates by matching the request against `description`; explicit forms diverge:

| Host | Explicit invocation |
| --- | --- |
| Claude Code | `/clean-code`, or `/clean-code-skills:clean-code` as a plugin |
| Codex CLI, IDE extension | `$clean-code`, or `/skills` to browse |
| Codex App | `@clean-code` |
| Kimi Code | `/skill:clean-code` |
| Grok Build CLI, Devin CLI, Copilot CLI | `/clean-code` |
| Hermes Agent | `/clean-code`; stacks as `/skill-one /skill-two <instruction>` |
| Gemini CLI | no syntax — the model calls `activate_skill`, asks approval |
| OpenCode | no syntax — the agent calls a native `skill` tool |
| Cursor, Antigravity, Factory Droid, pi | no documented syntax; name the skill plainly |

Every explicit form also takes the skill's arguments — `init` (alias `questions`), `audit`,
`clean-up`, `new-project <description>`, `plan <task>`, `review [files]`, `compress [files]` —
after the name: `/clean-code init`, `$clean-code audit`, `@clean-code audit`,
`/skill:clean-code audit`.

No explicit form? "Use the clean-code skill for this" works everywhere, naming the skill in the
request `description` matches.

Grok Build CLI, Cursor, and Factory Droid document a `disable-model-invocation` opt-out — unset
here; automatic activation is the point.

## Recommended setup per host

**Any host, first choice:** `assets/hooks/pre-commit` (dependency check, changed-files scan) —
identical everywhere.

**Claude Code:** merge `assets/hooks/claude-settings.json` into `.claude/settings.json`
(session-start print, post-edit scan); optionally add the seven workflows to `.claude/commands/`.

**Codex CLI, Copilot, Gemini CLI, Cursor, Amp, OpenCode, Factory Droid, Devin CLI, Kimi Code,
Antigravity, pi:** installer's `agents` profile → `.agents/skills/clean-code`, read project-side by
all.

**Grok Build CLI:** `grok` profile — project root `.grok/skills`, not the shared one.

**Antigravity, installed globally:** `antigravity` profile, targeting `~/.gemini/config/skills`;
project side needs only the `agents` profile.

**Codex App:** upload in-product (Plugins → Skills, above), or the `clean-code.zip` release asset
(github.com/btseee/clean-code-skills).

The installer's managed instruction block — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`.cursor/rules/`, `.windsurf/rules/`, `.clinerules/`, Copilot instruction files — keeps
non-negotiable rules visible skill-unloaded: the fallback for any unlisted host.

**Hosted or sandboxed agents with no shell:** every workflow works with zero tooling — each step's
script names a manual equivalent too. Report checks skipped.

## Writing for every model, not just the strongest one

Models read this at very different capability levels. What survives:

- **Imperative numbered steps** outperform prose: a weaker model follows "1. Read
  `.clean/context.json`" reliably, "consider the project's context" almost never.
- **Deterministic checks beat instructions.** Code answering a question should — that's what
  `scripts/` are for; save judgement for what needs it.
- **No host-specific vocabulary.** Never name a host's tools, panels, or UI verbs — say "read the
  file", not "use the Read tool".
- **No absolute or personal paths.** Everything relative to the project or the skill root.
- **Capability conditionals, not assumptions.** "If you can run shell commands, run X; otherwise
  check Y by reading Z."
- **Concrete over abstract.** "No `_v2` files" is followed; "maintain good file hygiene" is not.
- **State the failure each rule prevents.** A reason attached survives paraphrase; a bare
  prohibition doesn't.

## Verifying portability before release

Smoke-test two hosts on five things: discovered; activates on a relevant request; a reference file
loads on demand; a script runs under real permissions; output is useful. Works only where written?
Single-host, regardless of frontmatter.
