# Compress Protocol

For `/clean-code compress [files]` or "shrink our agent instructions". Rewrites a project's
instruction files tersely: same rules, fewer tokens. Hosts load these files on every turn, so each
word cut is saved on every request. Invoking the command is consent to rewrite the named files.
With none named, list the default targets that exist and wait for the user's confirmation before
rewriting. Changes no code.

## Targets

Default, at the project root and in package folders: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`DESIGN.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `.cursor/rules/*.mdc`,
`.github/copilot-instructions.md`, and `.github/instructions/*.instructions.md`.

Never touch:

- The managed block, from `<!-- clean-code-skills:begin v<version> -->` to
  `<!-- clean-code-skills:end -->`. The installer owns it: validators fail on drift, and the next
  install overwrites any edit. Compress only text outside the markers.
- Files the installer owns outright: `.cursor/rules/clean-code.mdc`,
  `.github/instructions/clean-code.instructions.md`, `.windsurf/rules/clean-code.md`,
  `.clinerules/clean-code.md`, and every installed `skills/clean-code/` folder.
- Generated files, license text, changelogs, and anything the user puts off-limits.

Before the first edit, list the targets with their token counts (words x 4/3).

## Steps

1. **Back up.** Copy each target to `<name>.original.md` beside it: `CLAUDE.md` becomes
   `CLAUDE.original.md`. Inside a rules folder a host scans (`.cursor/rules/`,
   `.github/instructions/`), put the backup one folder up, so no host loads it as a second rule
   set. If the backup already exists, stop and ask: it may hold the only true original, so never
   overwrite it. Keep backups until the user deletes them.
2. **Rewrite**, one file at a time:
   - Cut articles where meaning holds, filler ("please note", "it is important to"), hedging ("try
     to", "generally"), pleasantries, repeated framing, and any rule a file states twice.
   - Keep exactly: headings, fenced code, inline code, paths, commands, URLs, rule IDs, numbers,
     tool and file names, and front matter, which hosts parse.
   - Keep every security line whole: secrets, credentials, permissions, validation, destructive
     commands.
   - Keep every modal and condition (`never`, `must`, `only`, `always`, `unless`, `when`); dropping
     one inverts or widens a rule.
   - Keep full words, no invented abbreviations. Prefer imperatives: "Run tests before committing",
     not "Tests should be run".
   - Agent-only files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, rule files) may use fragments; files
     people also read (`CONTRIBUTING.md`, `ARCHITECTURE.md`, `DESIGN.md`) keep tight, complete
     sentences.
   - Never merge files or move rules between them: different hosts read different files.
3. **Check:** `python <skill>/scripts/check_compression.py <backup> <file>`, where `<skill>` is the
   folder holding `SKILL.md`. It compares headings, code blocks, inline code, URLs, rule IDs, and
   numbers as multisets, then prints token counts and the reduction. Exit 0: nothing
   technical lost. Exit 1: each loss on its own line. Exit 2: bad arguments or an unreadable file.
   Without Python, compare those item kinds by hand.
4. **Stop on any loss.** Restore the file from its backup, report the losses, and redo that file
   keeping them. A deliberate removal, such as a command repeated twice or a path the user confirms
   is obsolete, stays out only when the user approves it by name.
5. **Read the diff** for what the checker cannot see: each rule's meaning, modality, conditions, and
   security lines. Read every rewritten file once as the agent that will load it.

## Report

| File | Tokens before | Tokens after | Reduction | Checker |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` | 1,480 | 910 | 39% | exit 0 |

Counts cover the whole file; the managed block is unchanged, so it sits on both sides. Then list the
backups and where they are, skipped files and why, and removals the user approved. Tell the user to
delete the backups once satisfied and to commit the rewrite on its own.

## Rules

- Terse is not vague: when the shorter sentence is ambiguous, keep the longer one.
- Never compress a file that holds someone else's uncommitted changes.
- A rewrite that changes what an agent would do has failed, whatever the checker says.
