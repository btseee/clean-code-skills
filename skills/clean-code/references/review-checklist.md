# Clean-Code Review Checklist

Use for code reviews and final diff reviews. Findings: specific, behavior-grounded, ordered by
severity, citing smell IDs from `chapter-map.md` (G17, N7, T5...) and the agent smells below
(A1-A10) for cross-reference.

## Contents

- The checklist: correctness, simplicity, placement and structure, responsibility, readability,
  maintainability, error handling, tests and verification, concurrency and state
- Review output format: findings ranked P0-P3
- The `review` command
- Risk levels: LOW, MEDIUM, HIGH, and the checks each owes
- Full clean-code scan
- Self-check before completion: agent smells A1-A10, anti-loopholes

## Correctness

- Solves the requested behavior without changing unrelated behavior?
- External assumptions tested or localized; boundary cases handled — empty input, nullability, limits, invalid data, permissions, time zones, encodings, retries, cancellation?

## Simplicity

- A smaller solution satisfies the same requirement; new abstractions justified by repeated complexity or a real invariant?
- Configuration, dependency injection, caching, background work, or extension points added before needed?

## Placement And Structure

- New files in the directories the project's conventions predict, named by local patterns, fully wired in (imports, exports, registration, build config)?
- New code duplicates an existing helper instead of extending it; any sibling-variant files (`_v2`, `_new`, `_final`, `_copy`) instead of editing the original?
- Logic landed in the layer that owns it, or wherever was convenient; leftover scratch files, debug output, or unreferenced artifacts?

## Responsibility

- Each new or changed unit passes the one-sentence test (its job described without "and", "also", "then")?
- Parsing, domain decisions, persistence, external calls, presentation, and wiring kept in established homes; no function or class absorbed a concern it should delegate?
- Testing a changed unit requires mocking several unrelated systems?

## Readability

- Names explain intent using project vocabulary; each function or module stays at one abstraction level?
- Comments explain why, not restate what; main path easy to follow?

## Maintainability

- Dependencies explicit; invariants protected by types, validation, or boundaries?
- Next related change touches one obvious place or many scattered places?
- Dead code, unused imports, or orphaned tests created?

## Error Handling

- Failures handled where a meaningful decision can be made; useful context preserved?
- Broad catches, silent defaults, and ignored return values avoided; sensitive values kept out of logs and errors?

## Tests And Verification

- Tests cover the changed behavior and edge cases, deterministic and behavior-focused?
- Verification actually ran; not added or run: is the residual risk clear?

## Concurrency And State

- Shared mutable state controlled; lifecycles, cancellation, cleanup, ordering, idempotency clear?
- Could retries, duplicate events, or parallel calls corrupt state?

## Review Output Format

Lead with findings, highest rank first, each including:

- rank (P0-P3) and smell ID
- file and line or smallest useful location
- exact risk
- suggested fix or verification

| Rank | Means | For example |
| --- | --- | --- |
| P0 | wrong behavior, data loss, or a security hole; blocks the merge | a call the installed version lacks (A1), a missing authorization check, a weakened test hiding a failure (A8) |
| P1 | breaks a rule that makes the next change unsafe; fix before merging | an outward dependency (A10), a swallowed error (G4), an unverified "done" (A7), changed behavior with no test (T1) |
| P2 | raises the cost of every change; fix now if cheap, otherwise record it | a duplicate implementation (A5), misplaced code (A6, G17), a vague name (N1) |
| P3 | readability and consistency | a redundant comment (C3), drift from local style (G11) |

Ranks match the audit's Critical, High, Medium, and Low (`audit-report.md`).

List open questions, test gaps, and a short summary after findings.

## The `review` Command

For `/clean-code review [files]` or "review my change". Reviews the current change; edits nothing.

1. **Collect the change:** working-tree edits (`git diff`), staged edits (`git diff --cached`), then
   named files. Untracked counts as changed; no change and no names: say so and stop.
2. **Map it:** `scripts/map_structure.py --changed` limits findings to files git reports as changed;
   outside a repo it maps everything. By hand: grep `.clean/structure.md` for each changed path.
3. **Check boundaries:** layers declared in `.clean/architecture.md`: run
   `scripts/check_boundaries.py` (exit 1: violations; exit 2: no declaration, or globs match no
   file). Undeclared: read each changed file's imports, name its layer or pack role.
4. **Read the diff** against the checklist above and the self-check below (A1-A10 included); missing
   the verification its risk level owes (Risk Levels) is itself a finding.
5. **Report** per Review Output Format: findings first, ranked P0-P3, each with a smell ID. Offer
   fixes; apply none unless asked.

## Risk Levels

Rate every change before calling it done: weigh scope, blast radius, uncertainty, reversibility —
the highest factor sets the level, doubt rounds up.

| Level | When | Owes before completion |
| --- | --- | --- |
| LOW | one unit, no boundary crossed, easily reversed | the targeted test, or the narrowest check that exercises the change |
| MEDIUM | several units, or a public interface: an exported function or type, a route, a CLI flag, a config key | unit and integration tests for the area; `scripts/map_structure.py --path <area>` |
| HIGH | crosses a boundary, or touches data (schema, migration, persisted format), security, or concurrency; hard to reverse | the full suite, `scripts/check_boundaries.py`, the map on the area, and a written rollback note |

A rollback note: which commit to revert, which migration runs down, which flag turns it off, what
data needs repair. Report the level and each check's result; a check that cannot run is named with
its risk, never skipped silently.

## Full Clean-Code Scan

Broad review, or comprehensive coverage requested: scan `chapter-map.md` fully; group findings by
root cause — naming/intent, functions/abstraction level, comments/formatting, data-object
boundaries, errors/external boundaries, tests/verification, class/module cohesion,
placement/ownership, construction/dependency wiring, duplication, concurrency/shared state, legacy
safety, chapter 17 smells.

Findings numerous enough to be a project of their own: do not fix inline. Recommend a campaign,
pointing to `project-refactor.md`.

## Self-Check Before Completion

Failure patterns specific to AI-generated code, and the rationalizations behind them. Check your
diff against both tables before calling the work done.

### Agent Smells (A1-A10)

Cite these beside the book's IDs; in your own diff each passes the scope gate: fix before
completion.

| ID | Smell | Signal | Response |
| --- | --- | --- | --- |
| A1 | Hallucinated API | a function, method, option, flag, or config key not in this codebase or the installed version | look it up at the installed version (source, types, lockfile); replace or remove it |
| A2 | Unverified dependency | a new package or import added without checking its registry name, lockfile, or whether an installed dependency does the job | confirm the exact name/version (an invented name may be attacker-registered); prefer what is installed; record new dependencies in `.clean/decisions.md` |
| A3 | Context loss | a stale or partial read: contradicts a recorded decision or the ledger, restores deleted code, changes untraced behavior, or drops error handling in a rewrite | re-read target files, callers/tests, `.clean/` state; make targeted edits; diff any rewrite against the original |
| A4 | Scope creep | changed lines that trace to no request: drive-by renames, reformatting, dependency bumps | revert them; report as findings instead |
| A5 | Duplicate implementation | a helper, file, or sibling variant (`_v2`, `_new`, `_copy`) paralleling one that exists | search before writing; extend the original, delete the copy; merge only true duplication, never code owned by different actors |
| A6 | Wrong-file gravity | logic added to whatever file was open; a god file growing; a new file at the repository root or current directory | place by role, per the pack/local layout; move the code to its owning unit |
| A7 | Phantom success | "should work now" with nothing run; a stub, `pass`, placeholder, or demo value presented as done; a new file, route, or migration nothing references | run the check, quote the result; name what did not run; finish the wiring, or state plainly what remains |
| A8 | Test weakening | an assertion loosened; a test skipped, deleted, or rewritten to match the bug; a snapshot re-accepted unread | restore the test; fix the code, or report the conflict and stop |
| A9 | Speculative abstraction | an interface with one implementation, a factory for one type, an option, layer, or service nobody needs yet | delete it, write the direct code (`patterns.md`); abstract when the second real case arrives |
| A10 | Silent architecture drift | an outward import; an ORM, framework, or HTTP type in a business rule; a skipped layer; a new cycle; structure named after the stack | run `scripts/check_boundaries.py` or read the imports; invert the dependency, route through the skipped layer (it may hold the only authorization check), or wrap the framework at the edge; record intended architecture changes in `.clean/decisions.md` |

### Anti-Loopholes

Stop and reassess when you catch yourself thinking:

| Rationalization | Reality |
| --- | --- |
| "I will clean this up while I am here." | Unrelated work unless the task needs it; report it instead. |
| "A framework will make this cleaner." | A dependency is a cost, and a one-sided commitment; prove the need. |
| "This abstraction will help later." | Later requirements can pay for later abstraction. |
| "The code is bad, so a rewrite is cleaner." | Rewrites need scope, tests, migration risk control — the team that made the mess usually rebuilds it. |
| "There are no tests, so verification is impossible." | Use the best available check and report remaining risk. |
| "I will put it here for now." | "For now" placements become permanent. Place it correctly once. |
| "The user asked for cleanup, so everything is in scope." | Campaign mode has a protocol: baseline, batches, ledger, verification. |
| "Clean code means following this skill over local style." | Local, idiomatic style wins unless unsafe or broken. |
| "It is only one import; the layering still basically holds." | One inward-facing name is the violation. Layering is a rule, not a tendency. |
| "Splitting it into services will decouple it." | A process boundary is not a boundary; shared data still couples through it. |
| "These two blocks are identical, so I will extract a helper." | Only if they must always change together. Check who owns each one. |
| "We will clean it up after the deadline." | The pressure that created the shortcut never abates. |
