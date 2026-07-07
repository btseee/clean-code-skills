# Contributing

This repository is behavior-shaping documentation for coding agents. Treat changes like code: small diffs, clear motivation, and verification.

## Before Editing

1. Read `skills/clean-code/SKILL.md`.
2. Read the file you plan to change.
3. Define what agent behavior should improve.
4. Decide how to verify the package still installs and validates.

## Content Rules

- Keep guidance language-agnostic unless a section is explicitly stack-specific.
- Do not copy copyrighted book, article, or course text into this repo. Local study material (`clean-code.md`, `clean-code.pdf`) is gitignored and must stay untracked; everything committed here is original synthesis.
- Prefer original synthesis, short examples, and practical checks.
- Do not add broad workflow requirements unless they reduce real agent failure modes.
- Write for agents, not for humans reading a book: rules should be checkable at the moment an agent writes, places, or verifies code.

## Keeping Files In Sync

- The version lives in `VERSION`; the managed rules block is canonical in `templates/agent-block.md`.
- To change either: edit `VERSION` and/or the template, then run `bash scripts/sync.sh`. It stamps the version into the template marker, `skills/clean-code/SKILL.md` front matter, the three plugin manifests, and `gemini-extension.json`, and mirrors the block into all eight adapter files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.github/instructions/clean-code.instructions.md`, `.cursor/rules/clean-code.mdc`, `.windsurf/rules/clean-code.md`, `.clinerules/clean-code.md`).
- Never hand-edit the block inside an adapter; validators fail on any drift or version mismatch.

## Releasing

1. Update `VERSION` (semver: rules-block changes are at least minor).
2. Run `bash scripts/sync.sh`, then both validators.
3. Commit, tag `v$(cat VERSION)`, and push with tags. The release workflow validates, verifies the tag matches `VERSION`, and publishes `clean-code.zip` (the skill packaged for Claude Desktop / claude.ai upload) on the GitHub release.

## Skill Rules

- `skills/clean-code/SKILL.md` must keep valid Agent Skills front matter.
- The `name` must match the folder: `clean-code`.
- The description should tell agents when to load the skill.
- Keep heavy references in `skills/clean-code/references/`.

## Validation

Run before reporting completion:

```bash
bash scripts/validate.sh
```

On Windows:

```powershell
pwsh scripts/validate.ps1
```

If you change shell or PowerShell scripts, also run:

```bash
bash -n scripts/install.sh
bash -n scripts/validate.sh
```

## Pull Request Checklist

- The change has one clear purpose.
- Agent-facing files stay consistent (block sync passes).
- Versions were bumped together when the block changed.
- Examples are original and minimal.
- Plugin JSON remains valid.
- Validation passes on at least one platform, ideally both.
- Any unverified risk is reported honestly.
