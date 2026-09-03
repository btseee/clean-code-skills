# Risk-Based Verification

Verification depth should match the change, not the agent's mood. A rename does not need the full
suite; a payment path does not get by on a typecheck. This file gives one classification, three
levels, and what each level owes before completion. It is a heuristic, deliberately light: if
classifying takes longer than the smallest check, run the check.

## Classify

Think of risk as **scope x blast radius x uncertainty x reversibility**. No arithmetic: any one
factor at its worst pulls the change up a level.

| Factor | Pushes risk up when |
| --- | --- |
| **Scope** | many files, many units, a cross-cutting concern, a public surface |
| **Blast radius** | shared code, persistence, money, identity, anything many callers or users depend on |
| **Uncertainty** | unfamiliar stack, an API you had to look up, no tests nearby, behavior you could not trace |
| **Reversibility** | migrations, deletions, published packages, sent messages, anything a revert does not undo |

Take the highest level any factor reaches. When in doubt between two levels, take the higher.

## Levels

### LOW

Rename; formatting-safe local refactor; an isolated pure function; a small UI styling change; a
comment or documentation fix; a test-only change that adds coverage.

**Owes:** the narrowest check that would fail if the change were wrong: a focused test, the
typecheck, or the one command that exercises the line. Quote it.

### MEDIUM

A new endpoint or handler; an external API integration; a database query or index; state
management; a new use of an installed dependency; a change to how a module is wired; a bug fix in
shared code.

**Owes:** LOW, plus the tests of every changed unit and its direct callers; typecheck or build;
an integration or contract check where the change crosses a process or network seam (a real call in
a test mode, a recorded fixture, or a schema check). Say which of these ran.

### HIGH

Authentication; authorization; payment or money movement; a migration or persistence model change;
concurrency, locking, or ordering; a public API or published package; an architecture boundary
change (a new layer, a moved seam, a dependency inverted); deleting data or files; anything the
`.clean/decisions.md` log marks as load-bearing.

**Owes:** MEDIUM, plus the broader relevant suite (the module's tests at minimum, the whole suite
where it runs in minutes); integration or contract validation against the real seam; a boundary
review (`scripts/check_boundaries.py` or the changed inner files' imports listed with direction);
and an **explicit unverified-risk report**: what could not be exercised and what would.

## Report

Whatever the level, the handoff states it and the evidence:

```text
Risk: MEDIUM (new external call; shared pricing module)
Ran: yarn test src/pricing (14 passed); yarn tsc --noEmit (clean)
Not run: contract test against the live rate API (no credentials in this environment)
Remaining risk: rate API response shape assumed from the SDK types, not observed
```

A LOW change gets one line. A HIGH change gets all four, every time.

## Rules

- Classification is stated before verification, so the checks are chosen, not rationalized after.
- A red or missing check does not lower the level; it goes under "Not run" (A7).
- The project's trusted commands (`.clean/commands.json`, or `confirmed.verify_command` in
  `context.json`) outrank the README's claims and your own guess.
- Never weaken a test to make a level's check pass (A8). Report the conflict instead.
- HIGH changes that cannot be verified in the current environment stop at the report and hand the
  decision to the user; they are not shipped on a typecheck.
