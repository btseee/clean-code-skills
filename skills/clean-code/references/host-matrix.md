# Host Matrix

This skill is one folder of Markdown and a few standard-library Python scripts, which is all the
Agent Skills standard guarantees. Everything *beyond* that — hooks, slash commands, tool
permissions, persistent memory, session startup behavior — is host-specific and not part of the
standard. This file records what each host offers and what to do where it offers nothing.

**The rule for portable behavior: never depend on a host capability for correctness.** Use one when
it is there, because deterministic enforcement beats an instruction the model might skip. Fall back
to the prose step when it is not.

## Skill discovery paths

Where each host looks for skills. Project-scoped roots are relative to the repository.

| Host | Personal | Project |
| --- | --- | --- |
| Claude Code | `~/.claude/skills` | `.claude/skills` |
| OpenAI Codex | `~/.agents/skills`, `/etc/codex/skills` | `.agents/skills` |
| GitHub Copilot (CLI and VS Code) | `~/.copilot/skills`, `~/.agents/skills` | `.github/skills`, `.claude/skills`, `.agents/skills` |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `.gemini/skills`, `.agents/skills` |
| Cursor | — | `.cursor/skills` |
| Amp | `~/.agents/skills`, `~/.config/agents/skills` | `.agents/skills` |

`.agents/skills` is the most widely shared root. Installing there and symlinking into the
host-specific directories is what the cross-host installers do, and what `scripts/install.sh` in
this repository does.

## Frontmatter

Only these fields are in the standard, and only these are safe to rely on:

| Field | Required | Limit |
| --- | --- | --- |
| `name` | yes | 64 chars, lowercase, digits and hyphens, must match the directory name |
| `description` | yes | 1024 chars; this is what every host matches against to decide relevance |
| `license` | no | short |
| `compatibility` | no | 500 chars; environment requirements |
| `metadata` | no | string-to-string map |

`allowed-tools` is experimental and inconsistently implemented — **never depend on it for
correctness.** Fields such as `user-invocable`, `disable-model-invocation`, `context`, and
`argument-hint` are single-host extensions. Hosts that do not understand a field ignore it, so
adding one is safe; *relying* on one is not.

Body budget: keep `SKILL.md` under 500 lines and roughly 5,000 tokens. Reference files load on
demand, so depth belongs in `references/`, not in the main file.

## Capability support

| Capability | Where it exists | Portable substitute |
| --- | --- | --- |
| Session-start hook | Claude Code (`SessionStart`) and some others | Step 1 of `session-protocol.md`: read `.clean/` before anything else |
| Post-edit hook | Claude Code (`PostToolUse` on edits) | Step 16: check dependency direction during diff review |
| Pre-commit enforcement | git, on every host | none needed — this is the portable path, see `assets/hooks/pre-commit` |
| Slash commands | Claude Code, Codex (`$name`), Copilot, others | invoke the workflow by name: "run the audit workflow" |
| Tool permissions | every host, all differently | declare needs in `compatibility`; keep scripts read-only |
| Persistent memory | a few hosts | `.clean/` on disk — works everywhere, and survives host changes |
| Subagents | several hosts | do the work inline |

## Recommended setup per host

**Any host, first choice:** install the git pre-commit hook from `assets/hooks/pre-commit`. It needs
no host support at all, runs the dependency check and a scan of changed files, and is the only
enforcement that works identically everywhere.

**Claude Code:** merge `assets/hooks/claude-settings.json` into `.claude/settings.json` for a
session-start context print and a post-edit scan. Optionally expose the four workflows as commands in
`.claude/commands/`.

**Codex, Copilot, Gemini CLI, Cursor, Amp:** install the skill into `.agents/skills/clean-code`
(or the host root above), and rely on the pre-commit hook plus the prose protocol. The managed
instruction block that `scripts/install.sh` writes into `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`.cursor/rules/`, `.windsurf/rules/`, `.clinerules/`, and the Copilot instruction files keeps the
non-negotiable rules visible even when the skill is not loaded.

**Hosted or sandboxed agents with no shell:** every workflow works with zero tooling. Each step that
names a script also names the manual equivalent. Do that instead, and say in your report that the
automated checks did not run.

## Writing for every model, not just the strongest one

This skill is read by models of very different capability. What survives that range:

- **Imperative numbered steps** outperform prose. A weaker model follows "1. Read `.clean/context.json`"
  reliably and "consider the project's context" almost never.
- **Deterministic checks beat instructions.** If code can answer a question, let code answer it —
  that is what `scripts/` are for. Reserve model judgement for the parts that genuinely need
  judgement.
- **No host-specific vocabulary.** Never name a host's tools, panels, or UI verbs in skill content.
  Say "read the file", not "use the Read tool".
- **No absolute paths, no personal paths.** Everything relative to the project or the skill root.
- **Capability conditionals, not assumptions.** "If you can run shell commands, run X; otherwise
  check Y by reading Z."
- **Concrete over abstract.** "No `_v2` files" is followed; "maintain good file hygiene" is not.
- **State the failure each rule prevents.** A rule with a reason attached survives paraphrase and
  summarization; a bare prohibition does not.

## Verifying portability before release

Smoke-test on at least two hosts, checking five things: the skill is discovered; it activates on a
relevant request; a reference file loads on demand; a script runs under that host's real permission
model; and the output is actually useful. A skill that only works where it was written is a
single-host skill regardless of its frontmatter.
