# Code-Level Principles

The detail behind `SKILL.md`'s one-line rules: security, trust boundaries, data versus objects,
performance. Read the section you need when a decision is unclear.

Every rule here yields to the project's own idiom — clean code reads like a senior maintainer of
*that* stack wrote it. See `framework-map.md` for an unfamiliar ecosystem.

## Meaningful Names

Names reveal intent without mental decoding: domain vocabulary sized to scope; one word per
concept, never two; predicate-shaped booleans; units where values carry them; names that disclose
side effects (a function that saves, deletes, publishes, or mutates says so).

Avoid misleading names, false distinctions, and mental mapping the reader must translate back;
generic names (`data`, `manager`, `helper`, `util`, `info`, `process`, `result`) when a domain name
exists; unexpected type encodings, loose abbreviations, and names differing only by noise words.

**Verbs and keywords.** Put misreadable argument order or meaning into the name itself:
`assertExpectedEqualsActual(expected, actual)` cannot be called backwards by accident;
`assertEquals(a, b)` can.

## Small Focused Functions

A function does one thing at one level of abstraction — often misattributed to the Single
Responsibility Principle. Real and useful, but not the SRP, which is about actors, not
one-thing-ness (see `architecture.md`).

Prefer: early exits for invalid or terminal cases; extraction once a block has a clear independent
purpose; **the Stepdown Rule** (the file reads top-down, callers above callees, each level one
step more detailed); few parameters — niladic (none, ideal), monadic (one), dyadic (two, if
naturally ordered), triadic (three, needs justification), polyadic (more — an unnamed object
waiting to be created); command-query separation; explanatory variables for intermediate steps;
named, positive conditionals over an inlined tangle of negations.

Avoid: boolean flags and mode selectors that make one function do unrelated jobs; validating,
transforming, persisting, logging, notifying, and rendering all at once; hidden mutation of
inputs, globals, or output parameters; nested conditionals hiding the main path; copy-pasted
branches with tiny differences; one type-switch or if/else chain repeated across the codebase
instead of routed through a single dispatch point (polymorphism, a handler map, pattern matching).

Decompose until every unit is falsifiable by a test — untestable-by-design code is an
architectural defect, not a coverage gap. Tests show the presence of bugs, never their absence;
correctness is failing to prove incorrectness.

## Comments And Documentation

Good comments explain why code must be this way.

Keep: non-obvious constraints, legal requirements, algorithmic tradeoffs, external system quirks,
warnings of consequences, and TODOs with context and ownership.

Drop comments that repeat the code, go stale and lie, explain a name that should be clearer
instead, preserve commented-out code, narrate your edit, or add banners the project does not use.
Never explain where code came from, why a change is correct, or what the next line does — noise
the moment it merges.

**Size discipline.** A good comment is one to three lines; one needing a paragraph belongs as a
better name, an extracted function, or a doc file the comment points to instead. Never write
banner or divider comments — structure is shown by structure. `scan_repo.py` flags runs of eight
or more consecutive comment lines (a license header is exempt); the gap between three and eight is
deliberate, a coarse net for the worst offenders, while one-to-three lines is the standard you
write to.

## Formatting And Layout

The formatter owns whitespace, not ordering — ordering is where the design shows.

- Match the project's formatter and import order; never hand-format against it or reformat for an
  unrelated change.
- **The newspaper metaphor** — the file opens with high-level intent and descends into detail; a
  reader stops after the first screen already knowing what the file is for.
- **Vertical distance** keeps related things close: a variable near its first use, a caller
  adjacent to its callee, caller first.
- **Conceptual affinity** — code reading as one idea belongs together even with no call between: a
  family of overloads, related constants.
- **Vertical ordering** — dependency runs down the file, so top-to-bottom reading never needs
  what comes later.
- **Vertical openness and density** — blank lines separate concepts, adjacency signals one
  thought; neither is decoration.
- Horizontal spacing shows grouping; **skip alignment theater** — aligned columns break the
  moment a name changes, drawing the eye to the wrong axis.
- **Indentation reflects scope honestly**: no collapsing a block onto one line, and no **dummy
  scopes** — an empty loop or `if` body behind a bare semicolon. Make the body visible or delete
  the construct.

## Data, Objects, And Modules

- Use plain data structures for plain data; objects, records, or types where an invariant needs
  protecting. **Data/object anti-symmetry**: an object hides data and exposes behavior, a data
  structure exposes data and implies none — opposites; a new *type* is cheap with one, a new
  *operation* cheap with the other. Treating one as the other is where "anemic" and "god object"
  designs come from.
- Avoid the **hybrid** — public fields *and* behavior pretending to protect invariants, the
  disadvantages of both. Pick one.
- **The Law of Demeter**: ask a collaborator for a decision rather than navigating its internals —
  talk to what a method directly holds, not what those things return. A **train wreck**
  (`a.b().c().d()`) couples you to every link in the chain (smell G36); splitting it across named
  locals does not fix it, since coupling is the problem, not line length.
- Keep public APIs smaller than internal details — narrowest access modifier by default; every
  public type is a potential inbound dependency.
- Prefer explicit dependencies over hidden globals and singletons.
- Be precise: money, time, time zones, encodings, identity, and units deserve exact types, not
  floats and strings by default.
- Keep configurable values at the system's top levels, passed down, not buried as literals deep in
  low-level functions.

## Error Handling

Errors are part of the design, not a cleanup afterthought.

Do: design the failure path alongside the happy path, sketching the error contract first for
risky operations; handle errors at the level that can decide, preserving context and cause when
wrapping; model expected alternatives (not found, empty, declined) as values, result types, or
special-case objects — the **Special Case pattern** — so callers never need exceptional control
flow for an ordinary case; **prefer unchecked exceptions** where the language distinguishes them,
since a checked one forces every signature between throw and handler to declare it, breaking
encapsulation up the whole call chain (reserve checked exceptions for a stable API where the
caller must handle the case); avoid the **dependency magnet** — a shared error enum or constant
class every caller imports, forcing a universal recompile per new value and blocking independent
extension (prefer distinct exception types, or a wrapper that alone knows a third-party API's
error vocabulary); make retry, fallback, timeout, and cancellation behavior explicit, and extract
error handling that drowns the happy path.

Do not: swallow errors silently or catch broadly without rethrowing, wrapping, or reporting;
return null-like values or ignorable sentinels where the language has safer options, or pass null
where an absence type or overload is available; log secrets, tokens, personal data, or sensitive
payloads.

## Boundaries

Boundaries are where bugs multiply: external APIs, databases, file systems, clocks, queues, UI
events, network calls, subprocesses, generated code.

Validate inputs at trust boundaries. Localize third-party API assumptions behind an interface you
own, declared on *your* side — the API belongs to its user, not its implementer. Write a small
learning test when adopting an unfamiliar library: it documents your assumptions and catches
upgrades that break them. Make serialization, time zones, encodings, units, and nullability
explicit at the edge, and add contract or integration tests when boundary behavior matters.

For which direction dependencies may cross a boundary, and what data may cross it, see
`architecture.md`.

## Tests

Tests should make behavior easy to understand and safe to change. Treat test code as production
code — a system component, not scaffolding.

**`tests.md` holds the full discipline**: the Three Laws of TDD, F.I.R.S.T., BUILD-OPERATE-CHECK,
the dual standard, single concept per test, and the testing language. Read it when writing tests;
the summary below is enough for judging existing ones.

Prefer: behavior-focused names, one concept per test, assertions on outcomes rather than
implementation, coverage of the changed edge cases and any boundary where a bug was just found,
determinism, isolation, speed, and readable fixtures that fail for the right reason.

Avoid: broad snapshots as the only assertion, sleeps and timing guesses, excessive mocking of your
own code, tests that duplicate implementation logic, a test class per production class and a test
method per production method (structural coupling that makes tests fragile and production code
rigid), driving business rules through the GUI, and weakening, skipping, or deleting a failing
test to make the suite pass — a failing test is information, not an obstacle.

## Concurrency And State

Concurrent code must make ownership and ordering visible. **`concurrency.md` holds the detail**:
execution models, the four deadlock conditions, locking discipline, and the seven tactics that
actually catch a race. Read it before writing threaded code; a normal unit test proves little
there.

Check: shared mutable state, cancellation/timeout behavior, lock ordering, idempotency under
retries, lifecycle cleanup, event ordering and backpressure, race-prone tests.

Prefer immutability, message passing, transactions, actor-like isolation, or language-native
guarantees. Keep concurrency policy separate from business logic; treat sporadic test failures as
concurrency bugs, not noise to retry away.

Race conditions, deadlocks, and concurrent-update defects trace to mutable variables — no
deadlocks without mutable locks. Default to immutable data; confine mutation to small, named,
deliberately chosen components. Compare-and-swap on one cell is unsafe once several interdependent
values must change together.

## Security As Clean Code

- Validate and encode at boundaries; use parameterized queries and safe APIs.
- Keep authorization checks close to protected operations or centralized in an enforced policy
  layer — a shortcut that bypasses a layer sometimes skips the only per-record authorization in
  the system.
- Do not log secrets or sensitive data; do not hardcode credentials — read secrets from the
  environment or a secret store.
- Prefer well-maintained standard libraries for crypto, parsing, auth, and serialization.
- Make privilege, trust, and data retention explicit.

## Performance

- Measure before optimizing non-obvious bottlenecks.
- Keep algorithmic complexity visible; avoid hidden N+1 access patterns at boundaries.
- Avoid premature caches, pools, indexes, and background jobs.
- When optimizing, record the measured reason and keep the simpler behavior under test.
- Match conversation shape to boundary cost: a chatty exchange free in-process is a performance
  failure once that boundary turns into a network call.

## Simple Design Priorities

When design choices conflict, decide in this order:

1. All tests pass — correctness outranks elegance.
2. No duplicated knowledge — **DRY**, one home per fact. Confirm duplication is *true* first:
   copies changing for different reasons at different rates are not duplicates — merging them is
   harder to undo than leaving them apart.
3. Intent is expressed — a reader can tell what and why.
4. Fewest elements — no class, layer, or indirection the first three rules do not require.

The order is the tie-breaker — never break tests removing duplication, never add an element the
first three do not demand.

**LeBlanc's law — later equals never.** A cleanup deferred to "after the deadline" is a cleanup
cancelled — the pressure that produced the shortcut does not abate. In-scope cleanup happens now;
out-of-scope cleanup gets reported, not promised.
