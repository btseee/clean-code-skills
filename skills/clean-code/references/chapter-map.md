# Clean-Code Chapter Map

Agent-oriented synthesis of the clean-code source: 17 chapters plus the concurrency, SerialDate,
and cross-reference appendices — a checklist, not a source-text replacement, so no area is skipped
writing, refactoring, or reviewing.

## Contents

- How to use this map
- Chapters 1–16: clean code, names, functions, comments, formatting, objects/data, errors,
  boundaries, unit tests, classes, systems, emergence, concurrency, successive refinement, JUnit
  internals, SerialDate
- Chapter 17: smells — catalogue with IDs (C, E, F, G1–G36, J, N, T), plus agent smells A1–A10
- Appendix A: concurrency II; B: SerialDate source; C: cross references
- Coverage pressure scenarios

## How To Use This Map

- Narrow task: jump to the relevant chapter.
- Review: chapters 2-13 plus the chapter 17 smell groups.
- Refactoring: chapters 3, 5, 10, 12, 14, 16, 17. Whole-project cleanup: `project-refactor.md`
  per batch.
- Concurrent code: chapter 13, Appendix A. Tests: chapter 9, chapter 17's tests smell group.
- "Where does this belong": chapter 10 (cohesion), G6, G17, G24, `SKILL.md`'s Placement rule, the
  pack's roles.

## Chapter 1: Clean Code

Clean code is a professional obligation: mess compounds cost.

- Treat code as read more than written; prefer maintainable clarity over clever completion.
- **LeBlanc's law**: later equals never — schedule pressure excusing mess just cancels the
  cleanup.
- Redesign pressure comes from accumulated small neglect — write for future maintainers, as an
  author writes for readers.

### The Boy Scout Rule, and where this skill departs from it

Source rule: leave code a little cleaner every check-in — rename a variable, split an oversized
function, remove a small duplication.

**This skill narrows that rule.** A human's drive-by is a two-line diff; the same habit across
every file an agent opens is unreviewable, dragging in untested code and burying the fix. So:
**clean only the lines your task touches, report the rest** — in your summary, or campaign mode
(`project-refactor.md`), which gives cleanup a baseline, batches, review.

Intent survives: leave it better, never worse. Dropped: license to widen scope — for an agent,
that costs more than it returns.

Ask: understandable to a maintainer in six months?

## Chapter 2: Meaningful Names

Names are the primary documentation layer.

Cover: intention-revealing, pronounceable, searchable names; no misleading names, false
distinctions, mental mapping, or bloated prefixes; no type/member encodings unless idiomatic;
noun-like for types, verb-like for behavior; one word per concept; solution- vs. problem-domain
terms as the concept demands.

Ask: side effects disclosed — persist, enqueue, notify, delete, mutate, publish?

## Chapter 3: Functions

Functions should be small, focused, and readable top to bottom.

Cover: small blocks, clear indentation, top-down stepdown flow; one thing per function, one
abstraction level; careful switch/selector handling; descriptive names; few, grouped arguments; no
flag/output arguments or hidden side effects; commands vs. queries; idiomatic exceptions over
status codes; error-handling extracted when it obscures the main path; no clever jumps.

## Chapter 4: Comments

Comments help when they explain intent, constraints, warnings, or public contracts; harm when
compensating for unclear code.

Keep: legal requirements; inexpressible context; non-obvious intent; ambiguity clarified;
warnings; actionable TODOs; a subtle point amplified; public API docs where expected.

Avoid: redundancy with the code; misleading/stale comments; mandated noise; journal logs;
decorative markers; closing-brace labels from oversized functions; version-control attributions;
commented-out code; nonlocal background; headers for obvious private helpers.

Ask: could it go stale as the code changes?

## Chapter 5: Formatting

Formatting communicates structure before the reader understands the code.

Cover: the **newspaper metaphor**; **vertical openness/density/distance/ordering**; **conceptual
affinity**; horizontal openness/density — **skip alignment theater**; honest indentation, no
**dummy scopes**; team formatter rules over personal preference. Each term is defined in
`canon.md`.

The formatter owns whitespace, not **ordering** — a design decision no tool makes. See
`principles.md`.

## Chapter 6: Objects And Data Structures

Objects hide data behind behavior; data structures expose it. Mixing both casually creates
confusion.

Cover: data abstraction over leaking representation; the object/data tradeoff (new types vs. new
operations); Law of Demeter, no train-wreck navigation; no hybrids exposing fields while
pretending to protect invariants; DTOs for transport; Active Record where used, domain behavior
kept clear.

## Chapter 7: Error Handling

Error handling must preserve happy-path clarity and failure-path context.

Cover: idiomatic exceptions/results over ignorable codes; sketch the error skeleton before the
happy path; try/catch designed around the caller's needs; preserve context and cause; model
expected alternates (not found, empty, declined) as values, not exceptions; avoid null-likes;
error handling localized, cohesive.

Ask: nullability or absence explicit in the type or contract?

## Chapter 8: Boundaries

External boundaries should be wrapped, learned, and tested so third-party change doesn't leak in.

Cover: third-party APIs isolated behind local adapters; learning and contract tests; interfaces
for nonexistent code; framework/vendor types kept out of core domains; serialization, time,
encoding, units validated at the edge.

Ask: what happens when the vendor changes, times out, or returns malformed data?

## Chapter 9: Unit Tests

Tests are production assets that enable change, held to production standards.

Cover: the **Three Laws of TDD**; a **domain-specific testing language**; the **dual standard**;
**single concept per test**; **BUILD-OPERATE-CHECK**; **F.I.R.S.T.** (Fast, Independent,
Repeatable, Self-validating, Timely). Each term is defined in `canon.md`; failure modes and full
detail are in `tests.md`.

## Chapter 10: Classes

Classes and modules should be small, cohesive, and organized around one reason to change.

Cover: organization of public surface, internals, helpers; encapsulation that doesn't hide
design facts; small classes/modules; SRP; field/method cohesion; split when cohesion drops;
organize for change via narrow dependencies.

## Chapter 11: Systems

Construction, wiring, runtime policy, and domain behavior should not be tangled.

Cover: system construction separated from system use; main/wiring distinct from domain logic;
factories and DI only when they clarify construction; incremental architecture; isolated
cross-cutting concerns; decisions test-driven, made at the last responsible moment; standards used
only for demonstrable value; a domain language clarifying repeated intent.

## Chapter 12: Emergence

Clean design emerges through four simple rules applied in strict priority order.

1. Runs all tests — correctness outranks every aesthetic concern.
2. No duplication — one authoritative home per piece of knowledge.
3. Expresses programmer intent — a reader can tell what and why.
4. Minimizes classes, methods, moving parts — subject to the first three.

The order is a tie-breaker: never break tests to remove duplication, never add elements rules 1-3
don't require.

## Chapter 13: Concurrency

Concurrency creates correctness risks that require explicit ownership, data scope, lifecycle, and
testing.

Cover: the named execution models — **Producer-Consumer**, **Readers-Writers**, **Dining
Philosophers**. Myths, defense principles, locking discipline, the four deadlock conditions, and
the seven tactics for actually catching a race are full detail in `concurrency.md`.

Ask: can retries or duplicate events corrupt data?

## Chapter 14: Successive Refinement

Good code is often produced by making a rough version work, then refining in small verified steps.

- Start with a simple passing implementation.
- Stop and clean immediately when code starts resisting change.
- Refine incrementally, not by giant rewrite.
- Keep tests green through each refinement.
- Add argument or input variants one at a time, with tests.

## Chapter 15: JUnit Internals

Code written by experts, already working and respected, still carries obvious debt — cleanup is
unglamorous rename-and-extract work, not redesign.

The case study cleans a string-comparison class; its defects recur everywhere:

- **Redundant member prefixes** — a shared field prefix belongs to the class; drop it.
- **Names that don't say what the value is** — rename encoded members to their concept; reads
  clean unaided.
- **Hidden temporal coupling through member variables** — methods must run in order, each
  leaving state for the next; make the sequence explicit (pass or return values).
- **Negative conditionals and unclear boundary checks**, rewritten positively — where edge-case
  bugs surface.
- **Functions doing slightly more than their name admits**, split until each does one thing.

Beyond the case study: clean code you didn't write without changing behavior. Rename first —
problems surface once names are honest. Treat "must run in order" as a defect to design away. Hold
test/framework code to production standards.

Ask: would a failure this API reports be understood?

## Chapter 16: Refactoring SerialDate

Legacy code cleanup should first protect behavior, then improve names, structure, tests, and
responsibility.

- First make behavior observable, with tests or characterization checks.
- Then make names accurate and domain-specific.
- Remove misleading comments and dead code only when covered or unused.
- Move misplaced constants, calculations, or responsibilities to clearer homes.
- Keep steps small enough to review.

## Chapter 17: Smells And Heuristics

Smells are review prompts, not automatic rewrite permission.

Use these groups as a review scan. IDs follow the standard clean-code heuristic numbering, so a
finding cites a stable code ("G17 misplaced responsibility", "N7 name hides side effects").

### Comment Smells (C)

- C1: comment carries background that belongs elsewhere (tickets, history, metadata)
- C2: obsolete comment that no longer matches the code
- C3: redundant comment that restates the code
- C4: sloppy or unclear comment
- C5: commented-out code

### Environment Smells (E)

- E1: build requires more than one step
- E2: tests require more than one step

### Function Smells (F)

- F1: too many arguments
- F2: output arguments that mutate parameters
- F3: flag arguments selecting behaviors
- F4: dead, never-called functions

### General Smells (G)

- G1: mixed languages or paradigms in one file without need
- G2: obvious expected behavior left unimplemented
- G3: incorrect behavior at boundaries and edge cases
- G4: disabled or overridden safeguards (ignored warnings, skipped tests, silenced linters)
- G5: duplication of knowledge
- G6: code at the wrong abstraction level
- G7: base classes depending on their derivatives — a base class naming or reaching into a
  subclass. (Broader layering violations are architectural; see the structural smells in
  `smell-triage.md`, not G7.)
- G8: too much exposed information; wide interfaces
- G9: dead code
- G10: poor vertical separation; related code far apart
- G11: inconsistency; same idea done different ways
- G12: clutter that earns no keep
- G13: artificial coupling between things that do not belong together
- G14: feature envy; code operating on another module's internals
- G15: selector arguments that switch behavior
- G16: obscured intent
- G17: misplaced responsibility; code living where it does not belong
- G18: inappropriate static/global behavior
- G19: missing explanatory variables
- G20: function names that do not say what the function does
- G21: algorithm not understood before changing it
- G22: logical dependency not represented physically
- G23: repeated conditionals that want a single dispatch structure (polymorphism, handler map)
- G24: ignored standard conventions
- G25: magic values without domain names
- G26: imprecision in assumptions, types, or comparisons (money in floats, naive time math)
- G27: relying on convention where explicit structure is needed
- G28: unencapsulated complex conditionals
- G29: negative conditionals where positive ones read clearer
- G30: functions doing more than one thing
- G31: hidden temporal coupling
- G32: arbitrary, unjustified structural choices
- G33: boundary conditions not encapsulated in one place
- G34: functions descending more than one abstraction level
- G35: configurable data buried at low levels instead of the top
- G36: transitive navigation through object graphs (train wrecks)

### Language-Specific Smells (J and equivalents)

Source numbers J1-J3 for Java; two generalize and keep their IDs:

- J2: do not inherit constants — pulling them in through a base type or interface hides where
  they come from; name the source explicitly.
- J3: prefer typed enumerations over bare integer or string constants — an enum carries meaning,
  exhaustiveness, a compiler check; a loose constant carries none.

J1 (avoid long import lists via wildcards) is Java-specific, **intentionally omitted** — numbering
stays auditable, and the formatter/linter own import style.

Never translate another language's idiom literally — apply the principle, not the syntax.

### Naming Smells (N)

- N1: non-descriptive names
- N2: names at the wrong abstraction level
- N3: missing standard nomenclature the team or ecosystem already uses
- N4: ambiguous names
- N5: short names for long scopes, long names for short scopes inverted
- N6: unnecessary encodings and prefixes
- N7: names that hide side effects

### Test Smells (T)

- T1: insufficient tests; untested reachable behavior
- T2: no coverage signal where coverage would reveal gaps
- T3: skipped trivial tests that would document behavior
- T4: ignored tests that encode unresolved ambiguity
- T5: missing boundary tests
- T6: no extra coverage near recent bugs
- T7: failure patterns not investigated
- T8: coverage patterns not inspected
- T9: slow tests that discourage frequent runs

### Agent Smells (A)

Not from the book: AI-written-code failure patterns cited beside the IDs above. Signal, response:
`review-checklist.md`, Self-Check Before Completion.

- A1: hallucinated API
- A2: unverified dependency
- A3: context loss (related: G21)
- A4: scope creep
- A5: duplicate implementation (related: G5)
- A6: wrong-file gravity (related: G17)
- A7: phantom success (related: G2)
- A8: test weakening (related: G4)
- A9: speculative abstraction (related: G12)
- A10: silent architecture drift (related: the Dependency Rule)

Ask: fixable safely with current tests?

## Appendix A: Concurrency II

Locking, the four deadlock conditions, throughput, and the seven testing tactics are all in
`concurrency.md`, which supersedes this appendix for that detail.

Cover here: client/server threading tradeoffs; number of possible execution paths; non-thread-safe
classes; method dependencies breaking under parallel calls.

Ask: can tests force the rare interleaving?

## Appendix B: SerialDate Source

Before abstracting a rule, read real code. Preserve public behavior unless the task explicitly
changes it, and make date, time, calendar, locale, and boundary assumptions explicit.

## Appendix C: Cross References Of Heuristics

Findings are interconnected: one root cause often surfaces as several smells, so fixing the first
symptom noticed can leave the cause in place, or just trade one smell for another.

Check the related IDs before deciding what to fix; report the root cause, not the symptom. First
column is the ID as catalogued above.

| You found | Also check | Because the shared root cause is usually |
| --- | --- | --- |
| G30 | G34, F1, F3, G16, N1 | one function, several responsibilities: more arguments, a vaguer name |
| F1 | G30, G20, N1, primitive obsession | a missing concept: an unnamed object |
| G5 | G23, G11, G6, N3 | one rule, no authoritative home, reimplemented per site |
| G23 | G5, G6, G13, N3 | a missing dispatch point or a missing type |
| G17 | G6, G14, G22, G13 | a boundary never drawn; behavior settled by convenience |
| G14 | G17, G36, G8 | data and behavior living in different modules |
| G36 | G14, G8, Law of Demeter | a caller navigating structure, not asking a decision |
| G8 | G36, G14, ISP | a wide surface leaking internals as transitive dependencies |
| C1-C5 | G16, N1, G30 | a comment compensating for unclear or oversized code |
| C5 | G9 dead code | uncertainty preserved, not resolved — version control keeps it |
| N1 | G16, G20, G30 | the unit's job is unclear; no name fits |
| N7 | G31, command-query separation | a function both answering and changing |
| T1 | T5, T6, G3, G33 | untested boundaries, exactly where G3 defects live |
| T5 | G3, G26, G33 | boundary conditions never encapsulated in one place |
| T9 | E2, T1 | tests coupled to infrastructure, run rarely, coverage decays |
| E1/E2 | T9, T1 | friction suppressing the feedback loop other rules depend on |
| G31 | N7, G18, G22 | order-dependent state the API does not express |
| G18 | G31, T1 | shared mutable state, also making tests order-dependent |
| G25 | N1, G26, G35 | a domain concept with no name or home |
| G35 | G25, G6 | a tunable value decided at the wrong level |
| G9 | F4, C5, G12 | a change that orphaned code nobody deleted |

## Coverage Pressure Scenarios

Use these scenarios to test whether an agent applies the full map:

| Scenario | Must Consult |
| --- | --- |
| Rename a confusing API | Meaningful Names, Comments, Tests, Smells |
| Split a large service | Functions, Classes, Systems, Emergence, Smells |
| Wrap a vendor SDK | Boundaries, Error Handling, Tests, Systems |
| Refactor legacy date logic | Successive Refinement, SerialDate, Tests, Names |
| Fix flaky parallel job | Concurrency, Appendix A, Error Handling, Tests |
| Review a large PR | Chapters 2-13 plus Chapter 17 smell groups |
