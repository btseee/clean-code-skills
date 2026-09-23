# Installing Clean Code Skills

The skill itself is Markdown that the agent reads; it needs nothing installed. Everything below is
about putting it where your agents look.

## Requirements

| You need | To |
| --- | --- |
| bash, or PowerShell 7+ | run the installer locally |
| `curl` and `tar`, or PowerShell `irm` | use the no-clone remote installer |
| Python 3.8+ | run the four optional scripts (standard library only, no network) |
| `git` | use the portable pre-commit hook |
| Node / `npx` | contributors only: run markdownlint |

Host support for hooks, slash commands, and permissions varies and is **never required for
correctness** — see `skills/clean-code/references/host-matrix.md`.

## Quick Install, No Clone

Run inside your project. Linux, macOS, Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.sh | bash -s -- all
```

Windows PowerShell:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.ps1))) all
```

Replace `all` with just the agents you use: `claude cursor copilot`. Both commands fetch the latest
release (falling back to `main`) and run the packaged installer against the current directory.

## Skill Only, Across Hosts

Without adapter blocks: installs into `.agents/skills/` and links into each agent directory it
detects.

```bash
npx skills add btseee/clean-code-skills --skill clean-code
```

## Supported Hosts

Every path below comes from that vendor's own documentation. `.agents/skills/` is the shared
cross-agent root, and the `agents` profile installs the whole skill there — not just an instruction
block — which covers most of this table in one step.

| Host | Install with | Reads |
| --- | --- | --- |
| Claude Code | `claude` profile, or `/plugin marketplace add btseee/clean-code-skills` then `/plugin install clean-code-skills@clean-code-skills` | `.claude/skills` |
| Codex CLI | `agents` profile | `.agents/skills` |
| Codex App | Upload in-product: Plugins → Skills, or the `clean-code.zip` release asset | in-product only |
| Cursor | `agents` profile (also reads `.cursor/skills`) | `.agents/skills` |
| Gemini CLI | `agents` profile, or `gemini extensions install https://github.com/btseee/clean-code-skills` | `.agents/skills`, `.gemini/skills` |
| Antigravity | `agents` profile for a project; `antigravity` profile with `--global` | `.agents/skills`, `~/.gemini/config/skills` |
| GitHub Copilot CLI | `copilot` profile, or `agents` | `.github/skills`, `.agents/skills` |
| OpenCode | `agents` profile | `.opencode/skills`, `.agents/skills` |
| Factory Droid | `agents` profile | `.factory/skills`, `.agents/skills` |
| Devin CLI | `agents` profile | `.agents/skills`, `.devin/skills` |
| Kimi Code | `agents` profile | `.kimi-code/skills`, `.agents/skills` |
| Grok Build CLI | `grok` profile — its project root is **not** the shared one | `.grok/skills` |
| Hermes Agent | `agents` profile | `.hermes/skills`, `.agents/skills` |
| Pi | `agents` profile | `.pi/skills`, `.agents/skills` |
| Amp | `agents` profile | `.agents/skills` |
| Claude Desktop / claude.ai | Upload `clean-code.zip` from the [latest release](https://github.com/btseee/clean-code-skills/releases/latest): Settings → Capabilities → Skills. Works for the Skills API too | uploaded |
| Windsurf / Cline | `windsurf` or `cline` profile — rules files, not skills | `.windsurf/rules`, `.clinerules` |
| Anything else | Paste `templates/agent-block.md` into whatever instruction file it reads, and copy `skills/clean-code/` next to it | — |

Three exceptions a generic installer gets wrong, and this one handles: Claude Code does not read the
shared root; Grok Build CLI reads it personally but not inside a project; and Antigravity's personal
root is `~/.gemini/config/skills`, not `~/.agents/skills`. How each host lets you invoke a skill
explicitly is in `skills/clean-code/references/host-matrix.md`.

## Install Profiles

`claude`, `agents`, `codex`, `opencode`, `jules`, `gemini`, `cursor`, `copilot`, `windsurf`,
`cline`, `grok`, `antigravity`, `skill`, `all`. Pass any combination; `--detect` picks the ones
already present.

`agents` is the one that matters most: it writes the `AGENTS.md` block **and** installs the full
skill into `.agents/skills/clean-code/`, the shared root that twelve of the supported hosts read
project-side. `codex`, `opencode`, and `jules` are aliases for it.

## Once For Every Project

Global mode writes into the home-directory configuration that CLI agents read everywhere:

```bash
bash scripts/install.sh --global all      # ~/.claude, ~/.codex, ~/.config/opencode, ~/.gemini,
                                          # ~/.agents/skills, ~/.grok/skills, ~/.gemini/config/skills
```

```powershell
pwsh scripts/install.ps1 -Global all
```

Editor rules (Cursor, Windsurf, Cline, Copilot) and the bare `skill` profile are project-scoped by
design and are skipped in global mode.

## Updating

The same one-liner you installed with, plus `--detect`, which refreshes exactly the pieces already
present and leaves everything else alone:

```bash
curl -fsSL https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.sh | bash -s -- --detect
```

Native channels update natively: Claude Code through the plugin marketplace, Gemini CLI with
`gemini extensions update`, Claude Desktop by uploading the new release zip. The rules block carries
its version in its begin marker, so you can always see what a project runs. Agents are told **not**
to fetch and execute remote update scripts on their own initiative — updating is your call.

How installs and updates behave:

- **Shared files** (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`) get a
  managed block between `<!-- clean-code-skills:begin -->` markers. Everything outside the markers is
  preserved; updates replace only the block.
- **Dedicated files and skill folders** (`.cursor/rules/clean-code.mdc`, `.windsurf/`,
  `.clinerules/`, `skills/clean-code/`, `.claude/skills/clean-code/`, `.github/skills/clean-code/`)
  are owned by this package and replaced on each run. A file that exists but was not created by this
  package is skipped unless you pass `--force`.

## Uninstalling

```bash
bash scripts/install.sh --target /path/to/project --uninstall all
```

Removes managed blocks while keeping your own content, and deletes package-owned files and folders.
Works with `--global` too.

## Environment Variables

| Variable | Effect |
| --- | --- |
| `CLEAN_CODE_REF` | Pin the remote installer to a version, e.g. `CLEAN_CODE_REF=v4.0.0` |
| `CLEAN_CODE_HOME` | Override the home directory global mode installs into |
| `CLEAN_CODE_HOOK=off` | Disable the pre-commit hook for one commit |
| `PYTHON_BIN` | Point the hook at a specific interpreter |
