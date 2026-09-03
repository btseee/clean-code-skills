# Clean-Code Review Checklist

Use this for code reviews and final diff reviews, and for the `review` command below. Findings should be specific, behavior-grounded, and ordered by severity. Cite smell IDs from `chapter-map.md` (G17, N7, T5...) and `agent-smells.md` (A1-A10) when they apply, so findings stay unambiguous and cross-referenceable.

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

## Agent Smells

- Does every API, option, and flag the change uses exist in the installed version (A1)?
- Was any dependency added, bumped, or assumed without a stated reason (A2)?
- Does the change contradict a recorded decision or the declared layering (A3, A10)?
- Do all changed hunks trace to the request (A4)?
- Does anything new duplicate an existing helper, type, or file (A5)?
- Is every new file and unit where its responsibility lives (A6)?
- Is every claim of passing verification backed by a quoted run; is anything a stub (A7)?
- Was any test loosened, skipped, or deleted to get green (A8)?
- Does every new interface, factory, or configuration point have a current consumer (A9)?

## The `review` Command

For `/clean-code review` or "review my current change with the clean-code skill". It reviews the
**change**, not the repository; the whole-repository pass is `audit-report.md`.

**Scope, in order of preference:** `git diff` (the working tree), then `git diff --cached`, then
the files the user names; plus the tests of every changed unit and the architecture boundaries the
change touches (`.clean/architecture.md`, or the imports of the changed inner files). Read callers
of changed functions when the change alters a signature or a contract. Do not widen to files the
change does not touch except to confirm a duplicate (A5) or a boundary (A10).

**Findings first**, ordered by severity:

| Severity | Means |
| --- | --- |
| P0 | Correctness, security, data loss, or a destructive operation: wrong result, missing authorization, secret in a log, unguarded delete, a hallucinated API that will fail at runtime |
| P1 | Architecture or boundary violation: a wrong-way dependency, a skipped layer, a detail type travelling inward, a cycle introduced |
| P2 | Maintainability or responsibility: mixed responsibility, duplicate implementation, misplaced file, speculative abstraction, weakened test, scope creep |
| P3 | Minor quality: naming, comment accuracy, a magic value, a missing edge-case test that is low risk |

Each finding:

```text
P1 - A10 Silent Architecture Drift

src/orders/controller.ts:82

The controller now imports OrderRepository directly. Every other controller
reaches the repository through OrderService.

Why it matters: bypasses the application boundary, and OrderService holds the
ownership check.

Suggested fix: move the behavior into OrderService and keep the controller an
adapter.
```

Rules:

- Cite the smell ID (A1-A10, G, N, T...) when one applies; skip it when none does rather than
  forcing one.
- Every finding has a location. A finding without a file and line is a remark, and goes after
  the findings.
- Do not report what the project's formatter or linter already owns. Do not report style
  preferences that local convention settles.
- Say what was verified (a command you ran, an API you checked) and what was only read.
- After the findings: open questions, test gaps, then a two-line summary. Nothing before them.
- No findings is a valid result; say so in one line with what was checked.

## Review Output Format

The same format applies to any review, not only the command: severity, location, exact risk,
suggested fix or verification; open questions, test gaps, and a short summary only after findings.

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
