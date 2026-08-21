---
name: clean-code
description: Use when writing, editing, reviewing, testing, or refactoring code in any language or framework, when creating new files or deciding where code and files belong, when splitting mixed responsibilities, or when running a project-wide cleanup. Covers naming, functions, comments, boundaries, error handling, tests, concurrency, security, code placement, single responsibility, code smells, and verified surgical or whole-project refactoring.
license: MIT
metadata:
  version: "2.1.0"
---

# Clean Code

Clean code makes its intent, behavior, boundaries, and failure modes easy for the next maintainer to understand and safely change.

This skill is written for AI coding agents of any vendor and is language-agnostic. It does not mean "write Java everywhere" or "add object-oriented patterns everywhere." Adapt every rule to the project's language, framework, runtime, and local style. Two agent-specific truths shape everything below:

1. You read faster than humans but forget context between sessions. Structure, names, and placement are how work survives you.
2. Your most common failures are not syntax errors. They are code in the wrong place, duplicated knowledge, mixed responsibilities, invented APIs, and unverified claims of success.

## When To Use

Use this skill for new features, bug fixes, refactors, tests, reviews, scripts, SQL and data transformations, infrastructure as code, UI components, backend services, and libraries — and specifically whenever you are about to:

- create a new file, module, class, or directory
- add behavior to an existing unit
- decide where a piece of logic belongs
- clean up part or all of a project

Use a lighter touch for trivial edits, but still avoid unrelated changes.

## Operating Loop

### 1. Frame The Change

Before editing, identify:

- the exact behavior or maintainability problem being solved
- assumptions that could change the implementation
- the smallest useful scope
- the verification command or manual check that will prove the change

Ask a question only when ambiguity changes the implementation. Otherwise state the assumption and proceed.

### 2. Read Local Context

Inspect the surrounding project before changing it:

- naming vocabulary and casing conventions
- directory layout: where do sources, tests, helpers, types, and config live?
- module and file boundaries; how files are registered, exported, or wired
- error handling style, test style, dependency patterns, framework idioms
- whether the logic you are about to write already exists somewhere

Search before you write. Local consistency beats generic preference.

### 3. Put Code In Its Place

Decide where the change belongs before writing it. See "Where Code Lives" below. Prefer extending the existing owner of a concern over creating a new home for it.

### 4. Change The Smallest Slice

Every changed line should trace to the request or to cleanup caused by the request.

Do:

- keep the diff narrow and reviewable; prefer targeted edits over regenerating whole files
- preserve unrelated formatting, comments, and behavior
- remove imports, variables, functions, or files made unused by your change
- leave the lines you touched slightly cleaner than you found them — a better name, a removed dead branch — without widening the diff
- mention unrelated smells instead of fixing them silently

Do not:

- rewrite a module because it could be cleaner
- add new layers, factories, managers, config systems, caches, queues, or plugin points unless required
- change public behavior without tests or an explicit reason
- mix refactoring and behavior change in one step when separating them is safer
- defer trivial in-scope cleanup with a TODO; deferred mess tends to become permanent

### 5. Verify The Claim

Match verification to risk:

- Small pure function: focused unit test or direct command.
- Bug fix: reproducer test first when feasible, then green test.
- Refactor: relevant tests before and after when practical.
- API or boundary change: integration or contract check.
- UI change: component test, browser check, or screenshot when appropriate.
- Concurrency or timing change: deterministic stress or race-focused test where available.

If verification cannot be run, say exactly what was not run and what risk remains. Never claim success from memory of what the code should do.

### 6. Review The Diff

Before completion, scan for:

- unrelated edits and speculative abstractions
- files created in the wrong place, or new files that duplicate existing ones
- functions or modules that now do more than one job
- unclear names, comments compensating for confusing code
- swallowed errors, hidden shared state
- missing edge-case tests
- new code that nothing references, or wiring that was never completed

## Where Code Lives

Misplaced files and misplaced logic are among the most common agent failures. Placement is a design decision, not an afterthought.

### Placement Procedure

1. Find two or three existing artifacts most similar to what you are adding.
2. Mirror their directory, file naming pattern, internal structure, and registration.
3. Create a new file only when no cohesive home exists — a file is cohesive when its contents change for the same reason.
4. Wire the file in completely: imports, exports, barrel or index files, module lists, route tables, DI registration, build config, migrations. An unreferenced file is dead code, not a feature.
5. If two homes are plausible, choose the one closest to the code that uses it, and say why in your summary.

### Placement Rules

- Resolve paths from the project root and its source layout, never from whatever directory happens to be current. Confirm the target directory exists in the project's convention before creating it.
- Never default to the repository root. Root-level files are for project-wide concerns only.
- Put tests where the project keeps tests, mirroring its convention (alongside sources, or under a test tree that mirrors the source path).
- Place logic by responsibility, not by convenience: domain rules do not go in controllers, views, route handlers, or scripts; I/O does not go in pure domain modules; UI state does not go in data access code.
- Do not grow junk drawers. Adding to `utils`, `helpers`, `common`, or `misc` requires the same justification as creating a new module: name the domain concept instead.
- Never create sibling variants of an existing file: no `_v2`, `_new`, `_final`, `_enhanced`, `_improved`, `_copy`, `enhanced_`, `my_`, or date-suffixed names. Improve the original in place; version control preserves history.
- Scratch files, experiments, and one-off scripts go to a temp location outside the project tree, or are deleted before completion. Do not leave debug output, generated artifacts, or abandoned drafts in the repo.

## One Job Per Unit

Mixed responsibility is the smell agents produce most. Enforce single responsibility at every scale: function, class, module, file, directory, service.

### The One-Sentence Test

Describe the unit's job in one sentence without "and", "also", or "then". If you cannot, it has more than one job. Apply the test to every unit you create or grow.

### Kinds Of Responsibility

Treat these as distinct concerns that live in distinct units, following however the project separates them:

- parsing and input validation
- domain decisions and business rules
- persistence and data access
- calls to external systems
- presentation and formatting
- orchestration: sequencing the above
- logging, metrics, and other cross-cutting policy
- construction and wiring: building the object graph, reading config

An orchestrator may compose several concerns, but then it contains no business rules of its own — only the sequence.

### Rules

- New behavior goes to the unit that owns that responsibility, not the file you happen to be editing. Resist nearest-file gravity: code landing "where the cursor is" is how god files grow.
- If a requirement changes a unit's one-sentence job, extract a collaborator instead of inflating the unit.
- Keep construction separate from use: wiring, configuration reading, and object-graph assembly stay out of business logic.
- Dependency check: a module that imports the web framework, the database driver, and the mailer at once is probably doing all three jobs.
- Test-pain check: needing to mock three unrelated systems to test one function means the function mixes concerns.
- When you find existing mixed responsibility, apply Smell Triage below — split it when your task touches it, report it when it does not.

## Principles

### Meaningful Names

Names should reveal intent without requiring mental decoding.

Use:

- domain vocabulary from the project
- searchable names for important concepts; name length proportional to scope
- one word per concept across the codebase — and never one word for two different concepts
- boolean names that read as predicates
- units in names when values carry units
- names that disclose side effects: a function that saves, deletes, publishes, or mutates should say so

Avoid:

- misleading names and false distinctions
- generic names like `data`, `manager`, `helper`, `util`, `info`, `process`, or `result` when a domain name exists
- type encodings unless the language ecosystem expects them
- abbreviations that are not established in the project
- names that differ only by noise words

### Small Focused Functions

A function should do one thing at one level of abstraction.

Prefer:

- early exits for invalid or terminal cases when idiomatic
- extraction when a block has a clear independent purpose
- ordering functions so the file reads top-down: callers above callees, each level descending one step in detail
- few parameters; group related values when the domain has a real concept
- command-query separation: either answer a question or cause a change, not both
- explanatory variables that name intermediate steps of a computation
- positive, encapsulated conditionals: name a complex condition instead of inlining a tangle of negations

Avoid:

- boolean flags and mode selectors that make one function do unrelated jobs
- functions that validate, transform, persist, log, notify, and render at once
- hidden mutation of inputs or global state; mutating parameters as outputs
- nested conditionals that hide the main path
- copy-pasted branches with tiny differences
- the same type-switch or if/else chain repeated in multiple places — route variation through one dispatch point (polymorphism, a handler map, pattern matching) when the language supports it

### Comments And Documentation

Good comments explain why the code must be this way.

Keep comments for: non-obvious constraints, legal requirements, algorithmic tradeoffs, external system quirks, warnings of consequences, and TODOs with context and ownership where the project uses them.

Remove or avoid comments that: repeat the code, go stale and lie, explain names that should be clearer, preserve commented-out code, narrate your editing process ("added this function to..."), or add banners the project does not use.

### Formatting And Layout

- Match the project's formatter and import order; never hand-format against it.
- Keep related code vertically close; declare variables near use when idiomatic.
- Separate concepts with whitespace, not decorative noise.
- Do not reformat a file while making a small change unless formatting is the requested change.

### Data, Objects, And Modules

- Use plain data structures for plain data; use objects, records, or types to protect real invariants.
- Ask collaborators for behavior instead of navigating through their internals (`a.b().c().d()` chains couple you to every link).
- Keep public APIs smaller than internal implementation details.
- Prefer explicit dependencies over hidden globals and singletons.
- Be precise: money, time, time zones, encodings, identity, and units deserve exact types and explicit handling, not floats and strings by default.
- Keep configurable values at the top levels of the system, passed down — not buried as literals in low-level functions.

### Error Handling

Errors are part of the design, not a cleanup afterthought.

Do:

- design the failure path when you write the happy path, not after; for risky operations, sketch the error contract first
- handle errors at the level that can make a meaningful decision
- preserve context and original causes when wrapping
- model expected alternate outcomes (not found, empty, declined) as values, result types, or special-case objects — reserve exceptions for genuine failures
- make retry, fallback, timeout, and cancellation behavior explicit
- keep the happy path readable: extract error handling when it drowns the main logic

Do not:

- swallow errors silently or catch broadly without rethrowing, wrapping, or reporting
- return null-like values or ignorable sentinels where the language has safer options
- pass null where an absence type or overload is available
- log secrets, tokens, personal data, or sensitive payloads

### Boundaries

Boundaries are where bugs multiply: external APIs, databases, file systems, clocks, queues, UI events, network calls, subprocesses, generated code.

- Validate inputs at trust boundaries.
- Keep third-party API assumptions localized behind an interface you own; do not let a vendor type spread through the codebase.
- Write a small learning test when adopting an unfamiliar library — it documents your assumptions and catches upgrades that break them.
- Make serialization, time zones, encodings, units, and nullability explicit at the edge.
- Add contract or integration tests when boundary behavior matters.

### Tests

Tests should make behavior easy to understand and safe to change. Treat test code as production code.

Prefer tests that:

- use behavior-focused names and test one concept each
- assert outcomes, not implementation details
- cover the changed edge cases and the boundaries where bugs were just found
- are deterministic, isolated, and fast enough to run constantly
- use readable fixtures and fail for the right reason

Avoid:

- broad snapshots as the only assertion
- sleeps and timing guesses
- excessive mocking of your own code
- tests that duplicate implementation logic
- weakening, skipping, or deleting a failing test to make the suite pass — a failing test is information about the code, not an obstacle

### Concurrency And State

Concurrent code must make ownership and ordering visible.

Check: shared mutable state, cancellation and timeout behavior, lock ordering, idempotency under retries, lifecycle cleanup, event ordering and backpressure, race-prone tests.

Prefer immutability, message passing, transactions, actor-like isolation, or language-native concurrency guarantees when idiomatic. Keep concurrency policy separate from business logic. Treat sporadic test failures as possible concurrency bugs, not noise to retry away.

### Security As Clean Code

- Validate and encode at boundaries; use parameterized queries and safe APIs.
- Keep authorization checks close to protected operations or centralized in an enforced policy layer.
- Do not log secrets or sensitive data; do not hardcode credentials.
- Prefer well-maintained standard libraries for crypto, parsing, auth, and serialization.
- Make privilege, trust, and data retention explicit.

### Performance

- Measure before optimizing non-obvious bottlenecks.
- Keep algorithmic complexity visible; avoid hidden N+1 access patterns at boundaries.
- Avoid premature caches, pools, indexes, and background jobs.
- When optimizing, record the measured reason and keep the simpler behavior covered by tests.

### Simple Design Priorities

When design choices conflict, decide in this order:

1. All tests pass — correctness outranks elegance.
2. No duplicated knowledge — one authoritative home per rule or fact.
3. Intent is expressed — a reader can tell what and why.
4. Fewest elements — no class, layer, or indirection that the first three rules do not require.

## Scope Modes

### Surgical Mode (default)

Everything above, applied to the smallest slice that solves the task. Unrelated smells are reported, not fixed.

### Campaign Mode (explicit request only)

When the user asks for a project-wide or module-wide cleanup, the cleanup is the task — but it still needs structure, or it degrades into an unreviewable rewrite. Follow `references/project-refactor.md`. In short:

1. Inventory and baseline first: map the code, run the full verification suite, record what passes before touching anything.
2. Propose a prioritized plan batched by module or by smell; get agreement on order and depth.
3. Refactor in small verified batches — one module or one smell family at a time, behavior-preserving, tests green after each batch, one commit or checkpoint per batch.
4. Never mix behavior changes into a refactor batch; park discovered bugs in the ledger instead of silently fixing them.
5. Keep a written ledger of done, remaining, and found-but-deferred so progress survives context loss and session boundaries.
6. Stop and report rather than push through when the baseline is red, tests are missing for a risky area, or a batch balloons.

## Agent Failure Modes

These are the failure patterns most specific to AI-generated code. Check yourself against them before completion.

| Failure | Counter-behavior |
| --- | --- |
| Invented API: calling functions, methods, options, or config keys that do not exist | Verify against the actual codebase, dependency versions, and lockfile — not memory |
| Reinvented helper: writing logic that already exists in the project or its libraries | Search for existing implementations before writing; extend rather than duplicate |
| Wrong-place file: new files at the repo root, in the current directory, or outside conventions | Follow the Placement Procedure; mirror similar artifacts |
| Sibling-variant file: `service_v2.py`, `utils_new.ts`, `final_component.tsx` | Edit the original; version control keeps history |
| Nearest-file gravity: logic added to whatever file was open, growing god files | Route behavior to the unit that owns the responsibility |
| Regeneration loss: rewriting a whole file and silently dropping error handling, comments, or edge cases | Make targeted edits; when a rewrite is necessary, diff it against the original before finishing |
| Patch-without-understanding: changing code whose behavior you have not traced | Read callers, tests, and data flow first; trace the algorithm before altering it |
| Placeholder as done: stubs, `pass`, "in a real implementation...", hardcoded demo values presented as complete | Ship working code or state plainly what is unfinished |
| Test-blessing: weakening assertions or skipping tests until the suite passes | Fix the code or report the conflict; never bury the signal |
| Unwired artifact: a new file, route, or migration that nothing references | Complete registration and imports; prove reachability |
| Scope creep: drive-by renames, reformatting, dependency bumps | Trace every changed line back to the request |
| False completion: "this should work now" without running anything | Run the verification, quote the result, name what was not run |

## Smell Triage

When you see a smell, decide whether it is in scope. Fix now only if it blocks the requested change, creates immediate risk, or was introduced by your work. Otherwise mention it separately. In campaign mode, log it in the ledger and handle it in its batch.

| Smell | Look For | Usual Response |
| --- | --- | --- |
| Long function | mixed abstraction levels, many branches | extract named steps if touching the area |
| Mixed responsibility | unit fails the one-sentence test | split along responsibility kinds when your task touches it |
| Misplaced code | logic living in the wrong layer or module | move it to its owner, or report the mismatch |
| Junk-drawer module | growing `utils`/`helpers`/`common` | name the domain concept; relocate what you touch |
| Duplicate knowledge | same rule or constant in multiple places | centralize when behavior is changing |
| Duplicate implementation | parallel versions of the same helper or file | consolidate to one; delete the orphan if provably unused |
| Primitive obsession | loose strings, numbers, maps standing in for concepts | introduce a type only when it protects a real invariant |
| Boolean flag argument | one function doing two jobs | split functions or name modes clearly |
| Repeated type-switch | same if/else or switch chain in several places | one dispatch point when idiomatic |
| Shotgun surgery | one concept changed in many files | find the missing boundary |
| Feature envy | code reaching into another module's internals | move behavior or expose a clearer API |
| Hidden temporal coupling | calls that must happen in secret order | make state transitions explicit |
| Global mutable state | order-dependent tests, hidden inputs | inject dependencies or isolate state |
| Broad catch | failures disappear | handle, wrap, or propagate with context |
| Magic values | unexplained numbers or strings | name constants that express domain meaning |
| Buried configuration | tunable values hardcoded deep in call stacks | lift to the top level and pass down |
| Dead code | unreachable branches, unused exports, orphan files | delete what your change orphaned; report the rest |

## Framework And Language Adaptation

Before applying a rule, adapt it to the ecosystem. Read `references/framework-map.md` when working in an unfamiliar language or stack.

Examples:

- In Go, small interfaces at consumers beat deep hierarchies.
- In Rust, encode invariants in types and ownership instead of defensive runtime checks.
- In SQL, clean code means set-based operations, clear aliases, and explicit transaction boundaries.
- In React, clean code means predictable rendering, separated effects, accessible markup, and state near its use.
- In shell, clean code means explicit quoting, strict error behavior, and simple command flow.

## Anti-Loopholes

Stop and reassess when you catch yourself thinking:

| Rationalization | Reality |
| --- | --- |
| "I will clean this up while I am here." | Unrelated work unless the task needs it; report it instead. |
| "A framework will make this cleaner." | A dependency is a cost; prove the need. |
| "This abstraction will help later." | Later requirements can pay for later abstraction. |
| "The code is bad, so a rewrite is cleaner." | Rewrites need explicit scope, tests, and migration risk control. |
| "There are no tests, so verification is impossible." | Use the best available check and report remaining risk. |
| "Comments make it understandable." | Prefer clearer names and structure; comment only the why. |
| "I will create a fresh file; editing the existing one is risky." | A duplicate file is worse than a careful edit. Read, then edit. |
| "I will put it here for now." | "For now" placements become permanent. Place it correctly once. |
| "Regenerating the whole file is easier than a diff." | Whole-file regeneration hides losses and inflates review cost. |
| "This helper probably does not exist yet." | Search first. Assumed absence creates duplicates. |
| "The user asked for cleanup, so everything is in scope." | Campaign mode has a protocol: baseline, batches, ledger, verification. |
| "Clean code means following this skill over local style." | Local, idiomatic style wins unless it is unsafe or broken. |

## Completion Checklist

Before saying the work is complete, confirm:

- The change solves the stated task, and every changed line traces to it.
- New files sit in conventional locations, follow local naming, and are fully wired in.
- No duplicate implementation or sibling-variant file was introduced.
- Each new or grown unit passes the one-sentence test.
- Names and structure reveal intent; errors, boundaries, and state are explicit enough for the risk.
- Tests or checks match the behavior changed; no test was weakened to pass.
- No dead code, scratch files, or debug output introduced by the change remains.
- Verification results are reported honestly, including what did not run.
- In campaign mode: the ledger is current and the batch is verified and checkpointed.

## References

- `references/project-refactor.md` — campaign protocol for whole-project or module-wide cleanup.
- `references/chapter-map.md` — full clean-code chapter and heuristic map with smell IDs, for deep reviews and broad coverage.
- `references/review-checklist.md` — finding-first checklist for code reviews and final diff review.
- `references/framework-map.md` — per-language and per-stack adaptation notes.
