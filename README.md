# Clean Code Skills

Install-ready clean-code **and clean-architecture** guidance for AI coding agents — Claude Code, Claude Desktop / claude.ai, Codex CLI, opencode, Jules, Gemini CLI, GitHub Copilot, Cursor, Windsurf, Cline, and any tool that reads `AGENTS.md` or Agent Skills.

One language-agnostic `clean-code` skill is the source of truth. Thin adapters carry an identical, versioned rules block to every agent, so all your tools enforce the same behavior at both scales:

- **Code level** — meaningful names, focused functions, correct file and code placement, one job per unit, honest error handling, deterministic tests, agent-failure-mode checks.
- **Architecture level** — the dependency rule, SOLID as dependency rules, component cohesion and coupling, boundaries and their real costs, keeping the database, web, and framework as details, and testability as a structural property.

It is built for agents that start with no memory of your project: durable context lives in a `.clean/` directory on disk, and three optional standard-library Python scripts turn "does this obey the architecture?" from an opinion into a check.

Every workflow works with **no tooling at all** — the scripts are accelerators, never requirements.

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

### Or use the cross-host skills CLI

If you only want the skill itself (no adapter blocks), the standard Agent Skills installer works too. It installs into `.agents/skills/` and symlinks into each agent directory it detects:

```bash
npx skills add btseee/clean-code-skills --skill clean-code
```

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

Update with the same one-liner you installed with, plus `--detect`, which refreshes exactly the pieces already present and leaves everything else alone:

```bash
curl -fsSL https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.sh | bash -s -- --detect
```

Native channels update natively: Claude Code via the plugin marketplace, Gemini CLI via `gemini extensions update`, Claude Desktop by uploading the new release zip.

The rules block carries its version in its begin marker, so you can always see what a project is running. Agents are told not to fetch and execute remote update scripts on their own initiative — updating is your call, not theirs.

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
| Agent skill (canonical) | `skills/clean-code/SKILL.md` | Router and non-negotiables for any skill-aware agent, kept under the spec's 500-line / 5k-token budget |
| Architecture rules | `skills/clean-code/references/architecture.md` | Dependency rule, SOLID, component cohesion and coupling, boundaries, packaging, testability, decoupling modes |
| Architecture map | `skills/clean-code/references/architecture-map.md` | Routing table: the question you face, and the rule that answers it |
| Code principles | `skills/clean-code/references/principles.md` | Naming, functions, errors, tests, concurrency, security, performance in full |
| Workflows | `references/session-protocol.md`, `new-project.md`, `project-refactor.md`, `audit-report.md` | One per situation: a normal session, a greenfield start, a cleanup campaign, a report |
| Smell triage | `skills/clean-code/references/smell-triage.md` | Every code and architectural smell with its usual response and fix order |
| Chapter and smell map | `skills/clean-code/references/chapter-map.md` | Deep review coverage with stable smell IDs (G17, N7, T5...) |
| Review checklist | `skills/clean-code/references/review-checklist.md` | Finding-first review scan including placement and responsibility |
| Framework map | `skills/clean-code/references/framework-map.md` | Per-language idioms and file-placement conventions |
| Canon index | `skills/clean-code/references/canon.md` | Every named rule from both books with its operational meaning — the fastest way in when you know the name |
| Test discipline | `skills/clean-code/references/tests.md` | Three Laws of TDD, F.I.R.S.T., BUILD-OPERATE-CHECK, and the test failure modes |
| Concurrency | `skills/clean-code/references/concurrency.md` | Execution models, the four deadlock conditions, and the seven tactics that actually catch a race |
| Worked examples | `skills/clean-code/references/examples.md` | Before-and-after cases in Python, TypeScript, Go and SQL, plus output templates |
| Memory protocol | `skills/clean-code/references/memory-protocol.md` | What to persist in `.clean/` so a memoryless session can resume |
| Host matrix | `skills/clean-code/references/host-matrix.md` | Per-host skill paths, capabilities, and portable substitutes |
| Tools | `skills/clean-code/scripts/*.py` | `detect_stack.py` (context), `scan_repo.py` (measurable smells), `check_boundaries.py` (dependency direction) |
| Templates and hooks | `skills/clean-code/assets/` | `.clean/` file templates, a portable git pre-commit hook, Claude Code hook settings |
| Managed rules block | `templates/agent-block.md` | The single text inserted into every agent's instruction file |
| Adapters | `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/`, `.cursor/`, `.windsurf/`, `.clinerules/` | Per-client carriers of the same block |
| Manifests | `.claude-plugin/`, `.codex-plugin/`, `gemini-extension.json` | Native packaging for Claude Code, Codex-style registries, Gemini CLI |
| Installers | `scripts/install.sh` / `.ps1`, `scripts/remote-install.sh` / `.ps1` | Local and no-clone install, update (`--detect`), global mode, uninstall |
| Validators & CI | `scripts/validate.sh` / `.ps1`, `.github/workflows/` | Repo integrity, block/version sync, installer behavior on Linux and Windows |

## Core Behavior

Agents using this package must:

1. Load project context from `.clean/` and the project's own instruction files before deciding anything.
2. Frame the change: behavior, assumptions, smallest scope, and the check that proves it.
3. Read local context and search for existing implementations before writing anything new.
4. Put code and files where the project's conventions say they belong — and wire new files in completely.
5. Keep one job per unit; route behavior to the module that owns the responsibility.
6. Point every new dependency inward, and keep details — database, web, framework, ORM types — out of business rules.
7. Edit surgically; never regenerate whole files when a targeted edit will do.
8. Verify with real commands and report honestly what ran and what did not.

Whole-project cleanup is a distinct mode: baseline verification, small behavior-preserving batches, a written ledger, and a checkpoint per batch (`skills/clean-code/references/project-refactor.md`).

### Optional enforcement

Instructions are guidance; a model can skip a step. Where determinism matters, let code do the checking:

```bash
python skills/clean-code/scripts/detect_stack.py --write      # cache project context
cp skills/clean-code/assets/templates/architecture.md .clean/ # declare your layers
python skills/clean-code/scripts/check_boundaries.py          # fail on outward dependencies
cp skills/clean-code/assets/hooks/pre-commit .git/hooks/       # enforce it on every commit
```

The pre-commit hook is the only enforcement that behaves identically on every host, because it needs no agent support at all.

Clean code is not one language's style guide. Go stays idiomatic Go, Rust uses ownership and types, SQL stays set-oriented, React keeps rendering predictable, and shell scripts stay boring and explicit.

## Validate

```bash
bash scripts/validate.sh
```

```powershell
pwsh scripts/validate.ps1
```

Both check required files, front matter, version sync (template marker, `VERSION`, skill metadata, all manifests), managed-block consistency across all eight adapters, JSON and script syntax, the `SKILL.md` size budget, that the bundled Python uses only the standard library, that no shipped content carries an absolute machine path, LF line endings across tracked files, and full installer behavior: fresh install, content-preserving merge, idempotent re-install, `--detect` updates, global mode, and clean uninstall. CI runs both on every push and pull request.

## Releases And Versioning

`VERSION` is the single source. To release: update `VERSION` (and the template block if rules changed), run `bash scripts/sync.sh` to propagate everywhere, validate, then tag:

```bash
git tag "v$(cat VERSION)"
git push origin main --tags
```

The release workflow validates, checks the tag against `VERSION`, and publishes a GitHub release with `clean-code.zip` — the skill folder packaged for Claude Desktop / claude.ai / Skills API upload. Pin any project to a specific version with `CLEAN_CODE_REF=v3.0.0` before running the remote installer.

## Source Notes

This repository contains only original, agent-oriented synthesis of widely known clean-code and software-architecture principles. Principle names and their canonical formulations — SRP, OCP, LSP, ISP, DIP, REP, CCP, CRP, ADP, SDP, SAP, the dependency rule, the humble object pattern — are referenced as the established vocabulary of the field, and the guidance around them is written for this project.

No book text is reproduced here. Copyrighted study material used while writing it — a local `books/` directory, `clean-code.md`, `clean-code.pdf` — is gitignored and must never be committed or redistributed with this repo. If you clone this repository to study from, keep it that way.

## License

MIT. See `LICENSE`.
