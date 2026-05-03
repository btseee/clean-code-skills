# Clean-Code Review Checklist

Use this for code reviews and final diff reviews. Findings should be specific, behavior-grounded, and ordered by severity.

## Correctness

- Does the code solve the requested behavior without changing unrelated behavior?
- Are boundary cases handled: empty input, nullability, limits, invalid data, permissions, time zones, encodings, retries, cancellation?
- Are external assumptions tested or localized?

## Simplicity

- Is there a smaller solution that satisfies the same requirement?
- Are new abstractions justified by repeated complexity or a real invariant?
- Did the change add configuration, dependency injection, caching, background work, or extension points before they were needed?

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

Lead with findings. For each finding, include:

- severity
- file and line or smallest useful location
- exact risk
- suggested fix or verification

Then list open questions, test gaps, and a short summary only after findings.

## Full Clean-Code Scan

When the review is broad or the user asks for comprehensive clean-code coverage, also scan `chapter-map.md` and group findings by root cause:

- naming and intent
- functions and abstraction level
- comments and formatting
- data/object boundaries
- errors and external boundaries
- tests and verification
- class/module cohesion
- system construction and dependency wiring
- emergent design and duplication
- concurrency and shared state
- successive refinement and legacy safety
- chapter 17 smell groups
