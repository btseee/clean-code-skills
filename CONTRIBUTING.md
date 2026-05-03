# Contributing

This repository is behavior-shaping documentation for coding agents. Treat changes like code: small diffs, clear motivation, and verification.

## Before Editing

1. Read `skills/clean-code/SKILL.md`.
2. Read the file you plan to change.
3. Define what agent behavior should improve.
4. Decide how to verify the package still installs and validates.

## Content Rules

- Keep guidance language-agnostic unless a section is explicitly stack-specific.
- Do not copy copyrighted book, article, or course text into this repo.
- Prefer original synthesis, short examples, and practical checks.
- Do not add broad workflow requirements unless they reduce real agent failure modes.
- Avoid duplicating long sections across files. If you change a core rule, keep the root agent files, Copilot instructions, Cursor rule, and skill aligned.

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

If you change shell scripts, also run:

```bash
bash -n scripts/install.sh
bash -n scripts/validate.sh
```

## Pull Request Checklist

- The change has one clear purpose.
- Agent-facing files stay consistent.
- Examples are original and minimal.
- Plugin JSON remains valid.
- Validation passes.
- Any unverified risk is reported honestly.
