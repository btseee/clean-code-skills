# Session Protocol

Default workflow for one coding task in an existing project — features, fixes, small refactors,
short of a full campaign, greenfield start, or report.

Assume no memory: every step reads or writes disk state so the next session (yours or another
agent's) can resume.

## Before

**1. Load context.** Read `.clean/context.json` and its packs, then `.clean/architecture.md`,
`.clean/decisions.md`, `.clean/ledger.md` if present, then project instructions (`AGENTS.md`,
`CLAUDE.md`, `CONTRIBUTING.md`, `README.md`) — these outrank this skill. No `.clean/`? Run
`scripts/detect_stack.py`, or derive by inspection: primary language, frameworks, packs needed
(`framework-map.md`), test command, source/test layout.

**2. Review previous decisions.** A recorded decision is settled: don't reopen it; if it looks
wrong, tell the user.

**3. Confirm the goal.** State in one sentence what will be true when done, and the check proving
it. Ambiguous enough to matter? Ask; otherwise assume and proceed.

**4. Check the constraints.** Declared layers and dependency rules — or, absent those, the framework
pack's structure and roles, naming conventions, no-go areas (generated code, vendored code,
another's in-flight work).

**5. Inspect the related code.** Grep `.clean/structure.md`, or run
`scripts/map_structure.py --path <area>`, for each file's role and any nearby misplacement or
duplication. Read the units, callers, tests; search for an existing implementation first; trace
behavior before altering it.

**6. Plan the edit.** Which unit owns the responsibility, which boundary side it sits on, and the
smallest diff. Non-trivial? Write the plan first, under `plan.md`'s headings.

## During

**7. Prefer what exists.** Extend the current owner of a concern rather than making a new home. A new
dependency, layer, or file needs a stated reason.

**8. Make small changes.** One intent per edit. Targeted edits, not whole-file regeneration.

**9. Keep the change focused.** Every changed line traces to the request or to cleanup it caused.
Report unrelated smells; do not fix them silently.

**10. Stay consistent.** Match local naming, error style, test style, and framework idiom, even
against personal preference.

**11. Refactor as you go, inside the diff.** Improve the lines you already touched — a clearer name,
a removed dead branch — without widening the change.

**12. Remove the duplication you just created.** Copy-paste in your own diff is easiest to catch,
cheapest to fix — confirm it's true duplication before merging away.

**13. Validate assumptions against the code.** Confirm every API, option, and config key you use
exists in this codebase and its installed dependency versions (`.clean/context.json`, or
manifests) — never trust memory (`framework-map.md`, Dependencies And Package Idioms).

## After

**14. Run the checks.** Rate the change LOW, MEDIUM, or HIGH (Risk Levels, `review-checklist.md`);
run what that level owes, narrowest check first. Use the project's real command
(`.clean/context.json` or its docs).

**15. Review the impact.** Who calls what you changed? What did you orphan? Is anything now
unreferenced, half-wired, or newly duplicated?

**16. Verify architecture compliance.** Project declares layers? Every added dependency should point
inward, with no detail — ORM type, raw row, framework object — leaking into a policy module. Run
`scripts/check_boundaries.py`, or check the imports by hand; does each new symbol sit in its role's
home?

**17. Update documentation** your change made wrong; add none unasked. `.clean/` exists, and you
added, moved, or deleted files? Refresh with `scripts/map_structure.py --write`.

**18. Leave it cleaner than found** — within the diff you have, never by widening it.

**19. Record decisions worth keeping.** `.clean/` exists? Append to `.clean/decisions.md` whenever
you chose between alternatives, deferred deliberately, or found a rediscoverable constraint. Not
yet? Offer at the end — that's `init`, `audit`, and `new-project`'s job, never silent
(`memory-protocol.md`).

**20. Hand off cleanly.** Report: what changed and why; what command you ran and its result; what you
did *not* run and the risk that remains; what you found but left alone. Unfinished with `.clean/`
present? Write remaining steps into `.clean/ledger.md` so the next session resumes, not restarts;
otherwise put them in the report and offer to persist them.

## Honesty rules

Not negotiable — they matter more than any style rule in this skill.

- Never claim a check passed without running it — "this should work" isn't a result.
- Name what you skipped — an honest gap is useful, a silent one a defect.
- Never weaken, skip, or delete a failing test to go green. A failing test is information.
- Never present a stub, a placeholder, or a hardcoded demo value as finished work.
- Could not do what was asked? Say so, rather than delivering something adjacent.

## When to stop and ask

- Baseline already broken, and you can't tell whether you caused a failure.
- The change needs a decision only the user can make: a behavior change, a public API break, a new
  dependency, a schema migration.
- Following this skill conflicts with the project's own conventions in a way that isn't obviously a
  bug.
- The task keeps growing past agreed scope, or remaining context is too small to finish the current
  slice safely.
