# Clean-Code Review Checklist

Use this for code reviews and final diff reviews. Findings should be specific, behavior-grounded, and ordered by severity. Cite smell IDs from `chapter-map.md` (G17, N7, T5...) and the agent smells below (A1-A10) when they apply, so findings stay unambiguous and cross-referenceable.

## Contents

- The checklist: correctness, simplicity, placement and structure, responsibility, readability,
  maintainability, error handling, tests and verification, concurrency and state
- Review output format: findings ranked P0-P3
- The `review` command
- Risk levels: LOW, MEDIUM, HIGH, and the checks each owes
- Full clean-code scan
- Self-check before completion: agent smells A1-A10, anti-loopholes

## Correctness

- Does the code solve the requested behavior without changing unrelated behavior?
- Are boundary cases handled: empty input, nullability, limits, invalid data, permissions, time zones, encodings, retries, cancellation?
- Are external assumptions tested or localized?

## Simplicity

- Is there a smaller solution that satisfies the same requirement?
- Are new abstractions justified by repeated complexity or a real invariant?
- Did the change add configuration, dependency injection, caching, background work, or extension points before they were needed?

## Placement And Structure

- Are new files in the directories the project's conventions predict, named by local patterns, and fully wired in (imports, exports, registration, build config)?
- Does any new code duplicate an existing helper, utility, or module instead of extending it?
- Were any sibling-variant files created (`_v2`, `_new`, `_final`, `_copy`) instead of editing the original?
- Did logic land in the layer that owns it, or in whatever file was convenient?
- Are there leftover scratch files, debug output, or unreferenced artifacts?

## Responsibility

- Does each new or changed unit pass the one-sentence test (its job described without "and", "also", "then")?
- Are parsing, domain decisions, persistence, external calls, presentation, and wiring kept in their established homes?
- Did any function or class absorb a new concern it should have delegated?
- Would testing a changed unit require mocking several unrelated systems?

## Readability

- Do names explain intent using project vocabulary?
- Does each function or module stay at one abstraction level?
- Are comments explaining why, not restating what?
- Is the main path easy to follow?

## Maintainability

- Are dependencies explicit?
- Are invariants protected by types, validation, or boundaries?
- Will the next related change touch one obvious place or many scattered places?
- Did the change create dead code, unused imports, or orphaned tests?

## Error Handling

- Are failures handled where a meaningful decision can be made?
- Is useful context preserved?
- Are broad catches, silent defaults, and ignored return values avoided?
- Are sensitive values kept out of logs and error messages?

## Tests And Verification

- Do tests cover the changed behavior and relevant edge cases?
- Are tests deterministic and behavior-focused?
- Did verification actually run?
- If tests were not added or run, is the residual risk clear?

## Concurrency And State

- Is shared mutable state controlled?
- Are lifecycles, cancellation, cleanup, ordering, and idempotency clear?
- Could retries, duplicate events, or parallel calls corrupt state?

## Review Output Format

Lead with findings, highest rank first. For each finding, include:

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

The ranks match the audit's Critical, High, Medium, and Low (`audit-report.md`).

Then list open questions, test gaps, and a short summary only after findings.

## The `review` Command

For `/clean-code review [files]` or "review my change". Reviews the current change and edits
nothing.

1. **Collect the change:** working-tree edits (`git diff`), then staged edits (`git diff --cached`),
   then any files named in the command. Untracked files count as changed. No change and no names:
   say so and stop.
2. **Map it:** `scripts/map_structure.py --changed` limits the map's findings to files git reports
   as changed; outside a git repository it maps everything. By hand: grep `.clean/structure.md` for
   each changed path.
3. **Check boundaries:** with layers declared in `.clean/architecture.md`, run
   `scripts/check_boundaries.py` (exit 1: violations; exit 2: no declaration, or its globs match no
   file). Without a declaration, read each changed file's imports and name each one's layer or pack
   role.
4. **Read the diff** against the checklist above and the self-check below, A1-A10 included. Check
   that the change got the verification its risk level owes (Risk Levels); a missing check is a
   finding.
5. **Report** per Review Output Format: findings first, ranked P0-P3, each with a smell ID. Offer
   fixes; apply none unless asked.

## Risk Levels

Rate every change before calling it done. Weigh scope, blast radius, uncertainty, and
reversibility; the highest factor sets the level, and doubt rounds up.

| Level | When | Owes before completion |
| --- | --- | --- |
| LOW | one unit, no boundary crossed, easily reversed | the targeted test, or the narrowest check that exercises the change |
| MEDIUM | several units, or a public interface: an exported function or type, a route, a CLI flag, a config key | unit and integration tests for the area; `scripts/map_structure.py --path <area>` |
| HIGH | crosses a boundary, or touches data (schema, migration, persisted format), security, or concurrency; hard to reverse | the full suite, `scripts/check_boundaries.py`, the map on the area, and a written rollback note |

A rollback note says how to undo the change: which commit to revert, which migration runs down,
which flag turns it off, and what data needs repair. Report the level and each check's result in
the handoff. A check that cannot run is named with the risk it leaves, never skipped silently.

## Full Clean-Code Scan

When the review is broad or the user asks for comprehensive clean-code coverage, also scan `chapter-map.md` and group findings by root cause:

- naming and intent
- functions and abstraction level
- comments and formatting
- data/object boundaries
- errors and external boundaries
- tests and verification
- class/module cohesion
- placement and responsibility ownership
- system construction and dependency wiring
- emergent design and duplication
- concurrency and shared state
- successive refinement and legacy safety
- chapter 17 smell groups

If the findings are numerous enough that fixing them becomes a project of its own, do not fix them inline. Recommend a campaign and point to `project-refactor.md`.

## Self-Check Before Completion

The failure patterns most specific to AI-generated code, and the rationalizations that lead to them.
Check your own diff against both tables before saying the work is done.

### Agent Smells (A1-A10)

Cite these beside the book's IDs. In your own diff each one passes the scope gate: fix it before
completion.

| ID | Smell | Signal | Response |
| --- | --- | --- | --- |
| A1 | Hallucinated API | a function, method, option, flag, or config key you did not find in this codebase or the installed version | look it up at the installed version (source, types, lockfile, docs for that version); replace or remove it |
| A2 | Unverified dependency | a new package or import added without checking its registry name, the lockfile, or whether an installed dependency already does the job | confirm the exact name and resolved version, since an invented name may be one an attacker registered; prefer what is installed; record a new dependency in `.clean/decisions.md` |
| A3 | Context loss | an edit from a stale or partial read: it contradicts a recorded decision or the ledger, restores deleted code, changes behavior never traced, or a whole-file rewrite drops error handling and edge cases | re-read the target files, their callers and tests, and the `.clean/` state; make targeted edits; diff any rewrite against the original |
| A4 | Scope creep | changed lines that trace to no request: drive-by renames, reformatting, dependency bumps | revert them; report them as findings instead |
| A5 | Duplicate implementation | a helper, file, or sibling variant (`_v2`, `_new`, `_copy`) paralleling one that exists | search before writing; extend the original and delete the copy; merge only true duplication, never code owned by different actors |
| A6 | Wrong-file gravity | logic added to whatever file was open; a god file growing; a new file at the repository root or in the current directory | place by role, per the pack and the local layout; move the code to the unit that owns it |
| A7 | Phantom success | "should work now" with nothing run; a stub, `pass`, placeholder, or demo value presented as done; a new file, route, or migration nothing references | run the check and quote the result; name what did not run; finish the wiring, or state plainly what is unfinished |
| A8 | Test weakening | an assertion loosened; a test skipped, deleted, or rewritten to match the bug; a snapshot re-accepted unread | restore the test; fix the code, or report the conflict and stop |
| A9 | Speculative abstraction | an interface with one implementation, a factory for one type, an option, layer, or service nobody needs yet | delete it and write the direct code (`patterns.md`); abstract when the second real case arrives |
| A10 | Silent architecture drift | an outward import; an ORM, framework, or HTTP type in a business rule; a skipped layer; a new cycle; structure named after the stack | run `scripts/check_boundaries.py` or read the imports; invert the dependency, route through the skipped layer (it may hold the only authorization check), or wrap the framework at the edge; record any intended architecture change in `.clean/decisions.md` |

### Anti-Loopholes

Stop and reassess when you catch yourself thinking:

| Rationalization | Reality |
| --- | --- |
| "I will clean this up while I am here." | Unrelated work unless the task needs it; report it instead. |
| "A framework will make this cleaner." | A dependency is a cost, and a one-sided commitment; prove the need. |
| "This abstraction will help later." | Later requirements can pay for later abstraction. |
| "The code is bad, so a rewrite is cleaner." | Rewrites need explicit scope, tests, and migration risk control. The team that made the mess usually rebuilds it. |
| "There are no tests, so verification is impossible." | Use the best available check and report remaining risk. |
| "I will put it here for now." | "For now" placements become permanent. Place it correctly once. |
| "The user asked for cleanup, so everything is in scope." | Campaign mode has a protocol: baseline, batches, ledger, verification. |
| "Clean code means following this skill over local style." | Local, idiomatic style wins unless it is unsafe or broken. |
| "It is only one import; the layering still basically holds." | One inward-facing name is the violation. Layering is a rule, not a tendency. |
| "Splitting it into services will decouple it." | A process boundary is not a boundary. Coupling through shared data survives it. |
| "These two blocks are identical, so I will extract a helper." | Only if they must always change together. Check who owns each one. |
| "We will clean it up after the deadline." | The pressure that created the shortcut never abates. |
