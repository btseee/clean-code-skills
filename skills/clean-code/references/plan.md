# Plan Protocol

For `/clean-code plan <task>` or "plan this before you code it". Produces a written plan under fixed
headings and **edits nothing**: no source, no tests, no `.clean/` files, no formatter runs. Scripts
run read-only: `detect_stack.py` and `map_structure.py` without `--write`.

Use it before a non-trivial change, when the user wants to approve the approach first, or when
another agent will carry the plan out.

## Steps

1. **Load context.** Follow the gate in `SKILL.md`: `.clean/context.json` and its packs,
   `.clean/architecture.md`, `.clean/decisions.md`, `.clean/ledger.md`, the `.clean/structure.md`
   rows for the area, then the project's instructions. A recorded decision is settled; plan within
   it.
2. **Find existing implementations.** Search for the concept under its likely names and synonyms,
   read the structure rows for the area, or run `scripts/map_structure.py --path <area>`. Name what
   the change extends. A plan that adds a second implementation of something the codebase has is
   wrong (A5).
3. **Verify installed APIs.** For every library call, option, and config key the plan relies on,
   confirm it exists at the installed version: `.clean/context.json` under `dependencies`, the
   lockfile, then the installed package's source, types, or docs for that version. Whatever cannot
   be verified goes under Open questions, never into Steps as fact (A1, A2).
4. **Place the change.** For each unit: which one owns the responsibility, which layer or pack role,
   which folder. A new file only where no cohesive home exists, listed with the wiring it needs:
   imports, exports, registration, routes, DI, build config.
5. **Choose the risk level.** LOW, MEDIUM, or HIGH from the Risk Levels table in
   `review-checklist.md`, with the checks that level owes.
6. **Write the plan** under the headings below, in this order. Keep an empty heading with "None"
   rather than dropping it.

## The plan

```markdown
# Plan: <task>

## Goal
<One sentence: the behavior that is true when done, and the check that proves it.>

## Context read
<Files and .clean/ entries read; the decisions and constraints that shape the plan.>

## Existing code to reuse
<path: symbol, and how the change uses or extends it. Or "None found", with what was searched.>

## Placement
<Per unit: owner, folder, layer or role. New files with their wiring.>

## Steps
1. <Small, verifiable step. For a bug, the reproducing test comes first.>

## Risk level and verification
<LOW, MEDIUM, or HIGH, and why: scope, blast radius, uncertainty, reversibility.
The commands that will prove it. For HIGH, the rollback note.>

## Open questions
<Decisions only the user can make, unverified APIs, assumptions made.>
```

## Rules

- Every path, symbol, and API the plan names exists now, or is marked new or unverified.
- Smallest scope that solves the task: no speculative abstraction (A9), no drive-by work (A4).
- Ask an open question that changes the design; state the rest as assumptions.
- The plan lives in the reply. Write it to a file only where the user asks; `/clean-code plan` never
  creates `.clean/`.
- Carrying out an approved plan follows `session-protocol.md`. Re-read the target files first: the
  code may have moved since the plan was written (A3).
