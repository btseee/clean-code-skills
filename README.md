# Clean Code Skills

Install-ready clean-code guidance for AI coding agents — Claude Code, Claude Desktop / claude.ai, Codex CLI, opencode, Jules, Gemini CLI, GitHub Copilot, Cursor, Windsurf, Cline, and any tool that reads `AGENTS.md` or Agent Skills.

One language-agnostic `clean-code` skill is the source of truth. Thin adapters carry an identical, versioned rules block to every agent, so all your tools enforce the same behavior: meaningful names, focused functions, correct file and code placement, one job per unit, explicit boundaries, honest error handling, deterministic tests, agent-failure-mode checks, and verified surgical or whole-project refactoring. Agents are instructed to keep the rules current themselves (see Updates).

## Quick Install (no clone needed)

Run inside your project. Linux, macOS, Git Bash:

```bash
curl -fsSL https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.sh | bash -s -- all
```

Windows PowerShell:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.ps1))) all
```

Replace `all` with just the agents you use: `claude cursor copilot`. Both commands fetch the latest GitHub release (falling back to `main`) and run the packaged installer against the current directory.

## Native Installs Per Client

| Client | Native path |
| --- | --- |
| Claude Code | `/plugin marketplace add btseee/clean-code-skills` then `/plugin install clean-code-skills@clean-code-skills` — updates come through the plugin marketplace |
| Claude Desktop / claude.ai | Download `clean-code.zip` from the [latest release](https://github.com/btseee/clean-code-skills/releases/latest), then Settings → Capabilities → Skills → upload. Works for the Skills API too |
| Gemini CLI | `gemini extensions install https://github.com/btseee/clean-code-skills` — update later with `gemini extensions update clean-code-skills` |
| Codex CLI, opencode, Jules, Amp | Quick-install with the `agents` profile (writes the `AGENTS.md` block), or `--global` below |
| Cursor / Windsurf / Cline | Quick-install with the `cursor`, `windsurf`, or `cline` profile |
| GitHub Copilot | Quick-install with the `copilot` profile (instructions + `.github/skills/`) |
| Anything else | Paste `templates/agent-block.md` into whatever instruction file the tool reads, and copy `skills/clean-code/` next to it |

### Install Once For All Projects (CLIs)

Global mode writes into the home-directory config that CLI agents read everywhere:

```bash
bash scripts/install.sh --global all      # ~/.claude, ~/.codex, ~/.config/opencode, ~/.gemini
```

```powershell
pwsh scripts/install.ps1 -Global all
```

Editor rules (Cursor, Windsurf, Cline, Copilot) are project-scoped by design and are skipped in global mode.

## Updates

**Agents update themselves.** The installed rules block contains a "Keeping These Rules Current" section: when you ask your agent to update the clean-code rules (or before it starts a cleanup campaign), it compares the block's version against the repo's `VERSION` file and re-runs the installer with `--detect`, which refreshes exactly the pieces already present — after asking you first.

Manual update is the same one-liner as installing, with `--detect`:

```bash
curl -fsSL https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.sh | bash -s -- --detect
```

Native channels update natively: Claude Code via the plugin marketplace, Gemini CLI via `gemini extensions update`, Claude Desktop by uploading the new release zip.

### How Installs And Updates Behave

- **Shared files** (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`) get a managed block between `<!-- clean-code-skills:begin -->` markers. Everything you wrote outside the markers is preserved; updates replace only the block. The begin marker carries the version so you can see what a project runs.
- **Dedicated files and skill folders** (`.cursor/rules/clean-code.mdc`, `.windsurf/`, `.clinerules/`, `skills/clean-code/`, `.claude/skills/clean-code/`, `.github/skills/clean-code/`) are owned by this package and replaced on each run. A file that exists but was not created by this package is skipped unless you pass `--force`.
- `--detect` inspects the target and operates only on profiles that are already installed — the right mode for updates.

## Uninstall

```bash
bash scripts/install.sh --target /path/to/project --uninstall all
```

Removes managed blocks (keeping your own content) and deletes package-owned files and folders. Works with `--global` too.

## What Is Included

| Piece | Path | Purpose |
| --- | --- | --- |
| Agent skill (canonical) | `skills/clean-code/SKILL.md` | Full operating rules for any skill-aware agent |
| Project-refactor protocol | `skills/clean-code/references/project-refactor.md` | Campaign mode: whole-project cleanup with batches, ledger, verification |
| Chapter and smell map | `skills/clean-code/references/chapter-map.md` | Deep review coverage with stable smell IDs (G17, N7, T5...) |
| Review checklist | `skills/clean-code/references/review-checklist.md` | Finding-first review scan including placement and responsibility |
| Framework map | `skills/clean-code/references/framework-map.md` | Per-language idioms and file-placement conventions |
| Managed rules block | `templates/agent-block.md` | The single text inserted into every agent's instruction file |
| Adapters | `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/`, `.cursor/`, `.windsurf/`, `.clinerules/` | Per-client carriers of the same block |
| Manifests | `.claude-plugin/`, `.codex-plugin/`, `gemini-extension.json` | Native packaging for Claude Code, Codex-style registries, Gemini CLI |
| Installers | `scripts/install.sh` / `.ps1`, `scripts/remote-install.sh` / `.ps1` | Local and no-clone install, update (`--detect`), global mode, uninstall |
| Validators & CI | `scripts/validate.sh` / `.ps1`, `.github/workflows/` | Repo integrity, block/version sync, installer behavior on Linux and Windows |

## Core Behavior

Agents using this package must:

1. Frame the change: behavior, assumptions, smallest scope, and the check that proves it.
2. Read local context and search for existing implementations before writing anything new.
3. Put code and files where the project's conventions say they belong — and wire new files in completely.
4. Keep one job per unit; route behavior to the module that owns the responsibility.
5. Edit surgically; never regenerate whole files when a targeted edit will do.
6. Verify with real commands and report honestly what ran and what did not.

Whole-project cleanup is a distinct mode: baseline verification, small behavior-preserving batches, a written ledger, and a checkpoint per batch (`skills/clean-code/references/project-refactor.md`).

Clean code is not one language's style guide. Go stays idiomatic Go, Rust uses ownership and types, SQL stays set-oriented, React keeps rendering predictable, and shell scripts stay boring and explicit.

## Validate

```bash
bash scripts/validate.sh
```

```powershell
pwsh scripts/validate.ps1
```

Both check required files, front matter, version sync (template marker, `VERSION`, skill metadata, all manifests), managed-block consistency across all eight adapters, JSON and script syntax, and full installer behavior: fresh install, content-preserving merge, idempotent re-install, `--detect` updates, global mode, and clean uninstall. CI runs both on every push and pull request.

## Releases And Versioning

`VERSION` is the single source. To release: update `VERSION` (and the template block if rules changed), run `bash scripts/sync.sh` to propagate everywhere, validate, then tag:

```bash
git tag "v$(cat VERSION)"
git push origin main --tags
```

The release workflow validates, checks the tag against `VERSION`, and publishes a GitHub release with `clean-code.zip` — the skill folder packaged for Claude Desktop / claude.ai / Skills API upload. Pin any project to a specific version with `CLEAN_CODE_REF=v2.1.0` before running the remote installer.

## Source Notes

This repository contains only original, agent-oriented synthesis of widely known clean-code principles. Copyrighted study material (such as a local `clean-code.md` or `clean-code.pdf`) is gitignored and must never be committed or redistributed with this repo.

## License

MIT. See `LICENSE`.
