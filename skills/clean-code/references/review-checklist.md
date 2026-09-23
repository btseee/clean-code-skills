# Clean-Code Review Checklist

Use this for code reviews and final diff reviews. Findings should be specific, behavior-grounded, and ordered by severity. Cite smell IDs from `chapter-map.md` (G17, N7, T5...) when they apply, so findings stay unambiguous and cross-referenceable.

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

### Agent Failure Modes

| Failure | Counter-behavior |
| --- | --- |
| Invented API: calling functions, methods, options, or config keys that do not exist | Verify against the actual codebase, dependency versions, and lockfile — not memory |
| Reinvented helper: writing logic that already exists in the project or its libraries | Search for existing implementations before writing; extend rather than duplicate |
| Wrong-place file: new files at the repo root, in the current directory, or outside conventions | Put each role in its home per the pack and local layout; mirror similar artifacts |
| Sibling-variant file: `service_v2.py`, `utils_new.ts`, `final_component.tsx` | Edit the original; version control keeps history |
| Nearest-file gravity: logic added to whatever file was open, growing god files | Route behavior to the unit that owns the responsibility |
| Shortest-path wiring: injecting a repository into a controller because it is fewer steps | Go through the layer that owns the rule; the skipped layer may hold the only authorization check |
| Detail leaking inward: an ORM type, framework annotation, or HTTP object in a business rule | Keep the name of every outer-circle thing out of inner-circle code |
| Framework as architecture: structure named after the stack, business objects derived from framework classes | Name packages after the domain; wrap the framework at the edge |
| Regeneration loss: rewriting a whole file and silently dropping error handling, comments, or edge cases | Make targeted edits; when a rewrite is necessary, diff it against the original before finishing |
| Patch-without-understanding: changing code whose behavior you have not traced | Read callers, tests, and data flow first |
| Premature abstraction: a layer, boundary, or service introduced for a need nobody has yet | Leave the option open instead; build the boundary at the inflection point |
| Eager deduplication: merging two similar blocks owned by different actors or changing at different rates | Confirm it is true duplication first; accidental duplication is harder to unmerge than to leave |
| Placeholder as done: stubs, `pass`, "in a real implementation...", hardcoded demo values | Ship working code or state plainly what is unfinished |
| Test-blessing: weakening assertions or skipping tests until the suite passes | Fix the code or report the conflict; never bury the signal |
| Unwired artifact: a new file, route, or migration that nothing references | Complete registration and imports; prove reachability |
| Scope creep: drive-by renames, reformatting, dependency bumps | Trace every changed line back to the request |
| False completion: "this should work now" without running anything | Run the verification, quote the result, name what was not run |

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
