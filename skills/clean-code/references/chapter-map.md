# Clean-Code Chapter Map

This is an agent-oriented synthesis of the full clean-code source structure: 17 chapters, the deeper concurrency appendix, the SerialDate appendix, and the cross-reference appendix. It is not a replacement for the source text. Use it as a checklist so no major clean-code area is skipped during writing, refactoring, or review.

## How To Use This Map

- For a narrow task, jump to the relevant chapter area.
- For a review, scan chapters 2-13 plus the chapter 17 smell groups.
- For refactoring, scan chapters 3, 5, 10, 12, 14, 16, and 17. For whole-project cleanup, follow `project-refactor.md` and use this map inside each batch.
- For concurrent code, scan chapter 13 and Appendix A.
- For tests, scan chapter 9 and the tests smell group in chapter 17.
- For "where does this code or file belong" questions, combine chapter 10 (cohesion), G6, G17, G24, and the Where Code Lives section of the skill.

## Chapter 1: Clean Code

Core agent lesson: clean code is a professional obligation because mess compounds cost.

Apply this as:

- Treat code as read more than written.
- Prefer maintainable clarity over clever completion.
- Do not excuse mess because schedules are tight; "clean it later" almost always means never.
- Boy-scout rule: leave every touched area slightly cleaner than you found it — a better name, one removed dead branch — while staying inside task scope.
- Recognize that redesign pressure often comes from accumulated small neglect.
- Write for future maintainers as an author writes for readers.

Agent questions:

- Does this change reduce or add future ownership cost?
- Am I improving only the touched path, or drifting into unrelated cleanup?
- Would a maintainer understand why this code exists six months from now?

## Chapter 2: Meaningful Names

Core agent lesson: names are the primary documentation layer.

Cover these concerns:

- intention-revealing names
- avoiding misleading names and false distinctions
- pronounceable, searchable names
- avoiding type or member encodings unless idiomatic locally
- avoiding mental mapping from terse names to meaning
- noun-like names for types and objects; verb-like names for behavior
- one consistent word per concept
- solution-domain terms when the implementation concept matters
- problem-domain terms when the business concept matters
- enough context without bloated prefixes everywhere

Agent questions:

- Does the name say why the value exists, not only what type it is?
- Are two names different only because of filler words?
- Would search find all uses of this domain concept?
- Does a function name disclose side effects such as persist, enqueue, notify, delete, mutate, or publish?

## Chapter 3: Functions

Core agent lesson: functions should be small, focused, and readable top to bottom.

Cover these concerns:

- small blocks and clear indentation
- one thing per function
- one abstraction level per function
- top-to-bottom stepdown flow
- careful handling of switch or selector logic
- descriptive function names
- few arguments, with related values grouped into real concepts
- avoiding flag arguments and output arguments
- avoiding hidden side effects
- separating commands from queries
- using idiomatic exceptions or error flows instead of ignorable status codes
- extracting error-handling blocks when they obscure the main path
- keeping error handling as one responsibility
- using structured control flow without clever jumps

Agent questions:

- Can I summarize this function without using "and"?
- Does each line sit at the same abstraction level?
- Does a boolean argument mean this is really two functions?
- Is the function secretly changing input, global state, or external systems?

## Chapter 4: Comments

Core agent lesson: comments are useful when they explain intent, constraints, warnings, or public contracts; they are harmful when they compensate for unclear code.

Keep comments for:

- legal requirements when needed
- useful context that code cannot express directly
- intent behind a non-obvious decision
- clarification of unavoidable ambiguity
- warnings about consequences
- TODOs with actionable context
- amplification of a subtle point
- public API documentation where the ecosystem expects it

Avoid comments that are:

- redundant with code
- misleading or stale
- mandated noise
- journal logs
- decorative markers
- closing-brace labels caused by oversized functions
- attributions that belong in version control
- commented-out code
- too much nonlocal background
- function headers for obvious private helpers

Agent questions:

- Can clearer names or extraction remove this comment?
- Does the comment explain why, or merely restate what?
- Could this comment become false when nearby code changes?

## Chapter 5: Formatting

Core agent lesson: formatting communicates structure before the reader understands the code.

Cover these concerns:

- file opens with high-level intent, then details below
- related concepts stay close together
- blank lines separate concepts, not every line
- variable declarations are near use when idiomatic
- dependent functions are close and ordered for reading
- horizontal spacing shows grouping without alignment theater
- indentation reflects scope honestly
- team formatter rules override personal preference

Agent questions:

- Did I preserve local formatter behavior?
- Did I reformat unrelated code?
- Are related lines close enough that a reader does not hunt?

## Chapter 6: Objects And Data Structures

Core agent lesson: objects hide data behind behavior; data structures expose data for external behavior. Mixing both casually creates confusion.

Cover these concerns:

- data abstraction instead of leaking representation
- object/data tradeoff: adding new types vs adding new operations
- Law of Demeter and avoiding train-wreck navigation
- avoiding hybrids that expose fields while pretending to protect invariants
- DTOs for plain transport data
- Active Record patterns when the framework uses them, with domain behavior kept clear

Agent questions:

- Is this value just data, or does it protect behavior and invariants?
- Am I reaching through object internals instead of asking for behavior?
- Is a framework model becoming a dumping ground for unrelated logic?

## Chapter 7: Error Handling

Core agent lesson: error handling must preserve clarity in the happy path and context in the failure path.

Cover these concerns:

- prefer idiomatic exceptions/results over ignorable codes
- design the failure path first: sketch the error skeleton for a risky operation before filling in the happy path
- design try/catch or error branches around the caller's needs
- preserve context and original cause
- distinguish normal alternative flows from true failures; model expected alternate outcomes (not found, empty, declined) as values, result types, or special-case objects so callers do not need exceptional control flow for ordinary cases
- avoid returning or passing null-like values when the language has safer options
- keep error handling localized and cohesive

Agent questions:

- Can the caller make a useful decision from this error?
- Did I hide the original cause?
- Did I replace a real failure with a silent default?
- Is nullability or absence explicit in the type or contract?

## Chapter 8: Boundaries

Core agent lesson: external boundaries should be wrapped, learned, and tested so third-party change does not leak everywhere.

Cover these concerns:

- isolating third-party APIs behind local adapters
- learning tests for unfamiliar libraries
- contract tests for boundary behavior
- interfaces for code that does not exist yet
- keeping framework/vendor types out of core domains when possible
- validating serialization, time, encoding, and units at the edge

Agent questions:

- How many files know this third-party API shape?
- Is there a narrow local interface around the boundary?
- What happens when the vendor changes, times out, or returns malformed data?

## Chapter 9: Unit Tests

Core agent lesson: tests are production assets that enable change.

Cover these concerns:

- write tests before implementation when feasible
- keep test code clean, readable, and maintainable
- use a test-specific language or helpers only when they clarify intent
- allow different efficiency standards in tests without making them unclear
- prefer one behavior concept per test
- use enough assertions to describe the behavior without obscuring the point
- FIRST: fast, independent, repeatable, self-validating, timely

Agent questions:

- Would this test fail for the right reason?
- Is the fixture readable?
- Does this test describe behavior or mirror implementation?
- Are boundary cases and near-bug cases covered?

## Chapter 10: Classes

Core agent lesson: classes and modules should be small, cohesive, and organized around one reason to change.

Cover these concerns:

- organization of public surface, internals, and helpers
- encapsulation without hiding important design facts
- small classes or modules
- Single Responsibility Principle
- cohesion among fields and methods
- splitting classes when cohesion drops
- organizing for change
- isolating from change through narrow dependencies

Agent questions:

- Why would this class or module change?
- Do its methods use the same state and concepts?
- Is it a real domain role or a vague manager bucket?
- Is it easy to test without unrelated collaborators?

## Chapter 11: Systems

Core agent lesson: construction, wiring, runtime policy, and domain behavior should not be tangled.

Cover these concerns:

- separate system construction from system use
- keep main/wiring code distinct from domain logic
- use factories and dependency injection only when they clarify construction
- scale architecture incrementally rather than upfront
- isolate cross-cutting concerns
- test-drive architecture decisions where possible
- make decisions at the last responsible moment
- use standards only when they add demonstrable value
- build domain-specific language where it makes repeated intent clearer

Agent questions:

- Is wiring mixed into business behavior?
- Is the abstraction justified by real construction complexity?
- Does this framework feature buy clarity or only ceremony?

## Chapter 12: Emergence

Core agent lesson: clean design emerges through four simple rules applied in strict priority order.

Cover these concerns, in order of importance:

1. runs all tests — correctness outranks every aesthetic concern
2. contains no duplication — one authoritative home per piece of knowledge
3. expresses the intent of the programmer — a reader can tell what and why
4. minimizes classes, methods, and moving parts — subject to the first three

Use the order as a tie-breaker: never remove duplication in a way that breaks tests, and never add elements that rules 1-3 do not require.

Agent questions:

- Are tests strong enough to allow cleanup?
- What duplication represents shared knowledge rather than accidental similarity?
- Can I remove a construct without losing clarity or behavior?

## Chapter 13: Concurrency

Core agent lesson: concurrency creates correctness risks that require explicit ownership, data scope, lifecycle, and testing.

Cover these concerns:

- myths that concurrency is simple or only a performance concern
- separating concurrency policy from business logic
- limiting shared data scope
- using copies or immutable data when useful
- keeping threads/tasks independent when possible
- knowing library concurrency primitives
- understanding execution models such as producer-consumer and readers-writers
- avoiding dependencies between synchronized methods
- keeping critical sections small
- designing shutdown carefully
- treating sporadic failures as possible concurrency bugs
- testing with stress, instrumentation, different platforms, and varied schedules

Agent questions:

- Who owns this state?
- What can run at the same time?
- How does cancellation or shutdown complete safely?
- Can retries or duplicate events corrupt data?

## Chapter 14: Successive Refinement

Core agent lesson: good code is often produced by making a rough version work, then refining in small verified steps.

Apply this as:

- Start with a simple passing implementation.
- Stop when code starts resisting change and clean it immediately.
- Refine incrementally, not by giant rewrite.
- Keep tests green through each refinement.
- Add argument or input variants one at a time with tests.

Agent questions:

- Am I attempting the final architecture before the behavior is proven?
- Can this refactor be split into smaller green steps?
- Did I preserve the tests that let refinement continue safely?

## Chapter 15: JUnit Internals

Core agent lesson: even respected frameworks improve through naming, decomposition, simplification, and focused refactoring.

Apply this beyond JUnit as:

- Review framework-like code for API clarity.
- Keep internals understandable, not merely functional.
- Make comparison, formatting, and failure-reporting code explicit.
- Prefer readable extension points over clever reflection or hidden conventions.

Agent questions:

- Would users of this internal framework understand failures?
- Are extension points named for user intent?
- Is test infrastructure itself clean enough to maintain?

## Chapter 16: Refactoring SerialDate

Core agent lesson: legacy code cleanup should first protect behavior, then improve names, structure, tests, and responsibility.

Apply this as:

- First make behavior observable with tests or characterization checks.
- Then make names accurate and domain-specific.
- Remove misleading comments and dead code only when covered or clearly unused.
- Move misplaced constants, calculations, or responsibilities to clearer homes.
- Keep refactor steps small enough to review.

Agent questions:

- Do I know current behavior before changing it?
- Is this rename behavior-preserving?
- Am I cleaning legacy code or silently changing its contract?

## Chapter 17: Smells And Heuristics

Core agent lesson: smells are review prompts, not automatic rewrite permission.

Use these groups as a review scan. The IDs follow the standard clean-code heuristic numbering so findings can cite a stable code (for example "G17 misplaced responsibility" or "N7 name hides side effects").

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
- G7: dependency direction problems (foundations depending on details)
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

- imports, constants, and enum-like concepts handled against local language idioms
- rules from one language translated into another blindly instead of idiomatically

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

Agent questions:

- Is this smell in the scope of the requested task?
- Does it create immediate risk?
- Did my change introduce it?
- Can I fix it safely with current tests?

## Appendix A: Concurrency II

Core agent lesson: concurrency correctness depends on execution paths, library guarantees, lock strategy, throughput tradeoffs, deadlock prevention, and testing tools.

Cover these concerns:

- client/server threading tradeoffs
- number of possible execution paths
- library support such as executors, nonblocking solutions, and thread-safe collections
- non-thread-safe classes
- dependencies between methods that break under parallel calls
- client-side vs server-side locking tradeoffs
- throughput calculations and bottlenecks
- deadlock conditions: mutual exclusion, hold-and-wait, no preemption, circular wait
- strategies for breaking deadlock conditions
- tools and instrumentation for forcing timing failures

Agent questions:

- Can two valid calls interleave into invalid state?
- Which component owns locking?
- What throughput gain justifies the added correctness risk?
- How can tests force the rare interleaving?

## Appendix B: SerialDate Source

Core agent lesson: a substantial legacy example is useful for characterization, naming, responsibility movement, and behavior-preserving cleanup.

Use this appendix as a reminder to:

- inspect real code before abstracting rules
- preserve public behavior unless the task explicitly changes it
- make date, time, calendar, locale, and boundary assumptions explicit

## Appendix C: Cross References Of Heuristics

Core agent lesson: clean-code review is interconnected. A naming problem may also be a function problem, a test problem, and a boundary problem.

Use this appendix as a reminder to:

- cross-check related smells instead of treating each finding in isolation
- group review findings by root cause when possible
- avoid fixing one smell by introducing another

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
