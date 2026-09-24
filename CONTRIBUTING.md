# Contributing

This repository is behavior-shaping documentation for coding agents. Treat changes like code: small diffs, clear motivation, and verification.

## Before Editing

1. Read `skills/clean-code/SKILL.md`.
2. Read the file you plan to change.
3. Define what agent behavior should improve.
4. Decide how to verify the package still installs and validates.

## Content Rules

- Keep guidance language-agnostic unless a section is explicitly stack-specific.
- Do not copy copyrighted book, article, or course text into this repo. Local study material (`clean-code.md`, `books/`, and any `*.pdf`) is gitignored and must stay untracked; everything committed here is original synthesis.
- Prefer original synthesis, short examples, and practical checks.
- Do not add broad workflow requirements unless they reduce real agent failure modes.
- Write for agents, not for humans reading a book: rules should be checkable at the moment an agent writes, places, or verifies code.

## Keeping Files In Sync

- The version lives in `VERSION`; the managed rules block is canonical in `templates/agent-block.md`.
- To change either: edit `VERSION` and/or the template, then run `bash scripts/sync.sh`. It stamps the version into the template marker, `skills/clean-code/SKILL.md` front matter, the three plugin manifests, and `gemini-extension.json`, and mirrors the block into all eight adapter files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.github/instructions/clean-code.instructions.md`, `.cursor/rules/clean-code.mdc`, `.windsurf/rules/clean-code.md`, `.clinerules/clean-code.md`).
- Never hand-edit the block inside an adapter; validators fail on any drift or version mismatch.
- Hosts, profiles, and install paths live in `templates/hosts.tsv`; both installers, `sync.sh`, and the validator read it. Adding a host is a row there plus, for a block or owned file, the adapter file itself.

## Releasing

`VERSION` is the single source. To release: update `VERSION`, run `bash scripts/sync.sh` to
propagate it everywhere, update the `CLEAN_CODE_REF` example in `docs/install.md` by hand (sync
does not stamp it), validate, then tag:

```bash
git tag "v$(cat VERSION)"
git push origin main --tags
```

The release workflow validates, checks that the tag equals `v$(cat VERSION)` exactly, and publishes
a GitHub release with `clean-code.zip`, the skill packaged for Claude Desktop, claude.ai, and the
Skills API. Before tagging, run the eval subset described in `evals/README.md` and record its
results there.

## Skill Rules

- `skills/clean-code/SKILL.md` must keep valid Agent Skills front matter.
- The `name` must match the folder: `clean-code`.
- The description should tell agents when to load the skill.
- Keep heavy references in `skills/clean-code/references/`. `SKILL.md` is a router: the validator
  fails it above 500 lines or roughly 3,000 tokens, and the managed block above 1,200 tokens,
  because hosts load them on activation and on every turn.
- Bundled Python in `skills/clean-code/scripts/` must use only the standard library, and every
  workflow step that names a script must also name the manual equivalent — the skill has to work
  with no tooling at all.

## Writing A Pack

A pack is one language's or one framework's rules, in
`skills/clean-code/references/languages/` or `skills/clean-code/references/frameworks/`. Agents
load only the packs their stack needs, so each one must stand alone and stay short.

Language pack template (`Concurrency` is optional; every other heading is required, in order):

```markdown
# <Language>

> Applies to: <versions>. Formatter: <tool>. Linter: <tool>. Read with: <packs, or nothing>.

## Names
## Functions And Types
## Errors
## Modules And Visibility
## Placement
## Tests
## Concurrency
## Layers
## Enforce
## Smells
```

Framework pack template:

```markdown
# <Framework>

> Applies to: <versions>. Language pack: <file>. Read with: <packs, or nothing>.

## Structure
## Roles
## Rules
## Layers
## Tests
## Enforce
## Smells
```

Rules (the unit tests enforce the ones marked checked):

- Headings present and in order; at most 2,000 tokens, aiming for about 1,500 (checked).
- Imperative one-line bullets — "Never ...", "Always ...", "Prefer ..." — citing the book rule by
  canon name or smell ID where one applies: (G5), (F.I.R.S.T.), (DIP), (N1).
- **Structure** gives the framework's idiomatic layout, one line per folder. This skill is
  framework-first: that layout is the default.
- **Layers** opens with "Applies only when `.clean/architecture.md` declares layers." (checked),
  then says which framework types must not cross inward, where interfaces for details go, where the
  composition root lives, and suggests a `clean-architecture` block of at most six lines.
- **Roles** holds exactly one `clean-roles` block that parses (checked). The grammar is in
  `references/framework-map.md`. Put specific signals before general ones: the first match wins.
- **Enforce** names real tools with the rule or configuration key that matters.
- **Smells** lists stack-specific failure patterns, each with its nearest smell ID.
- At most two code examples, each at most eight lines.
- Verify every API, file convention, and configuration key against official documentation for the
  versions in "Applies to", and record the sources in `docs/pack-sources.md`.
- No book text. Before committing, run `python scripts/check_originality.py <pack>`, which compares
  it against the local, gitignored books for shared runs of eight or more words, and rewrite any hit.
- Add the pack to the `clean-packs` index in `references/framework-map.md` (checked: every pack is
  indexed, every indexed path exists, every label is one `detect_stack.py` reports).

## Validation

Run before reporting completion:

```bash
bash scripts/validate.sh
```

On Windows, run the same command from Git Bash. `pwsh scripts/validate.ps1` exercises only `install.ps1`.

If you change shell or PowerShell scripts, also run:

```bash
bash -n scripts/install.sh
bash -n scripts/validate.sh
```

`validate.sh` also runs the unit tests in `tests/` (`python -m unittest discover -s tests`), which
cover the scanners and the shape of the shipped content: pack templates and budgets, the pack
index, role blocks, and contents lists.

CI runs both validators, markdownlint, and a `skill-tools` job that executes the bundled Python
scripts against fixtures — including a boundary check that must fail and then pass, and a structure
map that must flag a misplaced middleware — plus `python evals/grade.py --self-test`, so a change
to `skills/clean-code/scripts/` needs those scripts to keep working end to end.

## Pull Request Checklist

- The change has one clear purpose.
- Agent-facing files stay consistent (block sync passes).
- Versions were bumped together when the block changed.
- `SKILL.md` stays under its budget (500 lines / ~3,000 tokens), the managed block under 1,200
  tokens, and each pack under 2,000; the validator fails above any of them.
- Examples are original and minimal.
- Plugin JSON remains valid.
- Validation passes on at least one platform, ideally both.
- Any unverified risk is reported honestly.
