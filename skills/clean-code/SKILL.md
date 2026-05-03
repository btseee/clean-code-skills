---
name: clean-code
description: Use when writing, editing, reviewing, testing, or refactoring code in any language or framework where readability, maintainability, naming, functions, tests, boundaries, error handling, concurrency, security, or code-smell prevention matter.
license: MIT
---

# Clean Code

Clean code is code that makes its intent, behavior, boundaries, and failure modes easy for the next maintainer to understand and safely change.

This skill is language-agnostic. It does not mean "write Java everywhere" or "add object-oriented patterns everywhere." It means adapt clean-code principles to the project's language, framework, runtime, and local style.

For chapter-by-chapter depth, use `references/chapter-map.md`. It maps the full 17-chapter clean-code structure, concurrency appendix, legacy refactoring appendix, and heuristic cross-references into agent checklists.

## When To Use

Use this skill for:

- new features
- bug fixes
- refactors
- tests
- reviews
- scripts and automation
- SQL and data transformations
- infrastructure as code
- UI components
- backend services
- libraries and public APIs

Use a lighter version for trivial edits, but still avoid unrelated changes.

## Operating Loop

### 1. Frame The Change

Before editing, identify:

- the exact behavior or maintainability problem being solved
- assumptions that could change the implementation
- the smallest useful scope
- the verification command or manual check that will prove the change

Ask a question only when ambiguity changes the implementation. Otherwise state the assumption and proceed.

### 2. Read Local Context

Inspect the nearby code before changing it:

- naming vocabulary
- module and file boundaries
- error handling style
- test style and fixtures
- dependency patterns
- formatting conventions
- framework idioms

Local consistency beats generic preference.

### 3. Change The Smallest Slice

Every changed line should trace to the request or to cleanup caused by the request.

Do:

- keep the diff narrow
- preserve unrelated formatting and comments
- remove imports, variables, functions, or files made unused by your change
- mention unrelated smells instead of fixing them silently

Do not:

- rewrite a module because it could be cleaner
- add new layers, factories, managers, config systems, caches, queues, or plugin points unless required
- change public behavior without tests or an explicit reason
- mix refactoring and feature work when separate steps are safer

### 4. Verify The Claim

Match verification to risk:

- Small pure function: focused unit test or direct command.
- Bug fix: reproducer test first when feasible, then green test.
- Refactor: relevant tests before and after when practical.
- API or boundary change: integration or contract check.
- UI change: component test, browser check, or screenshot when appropriate.
- Concurrency or timing change: deterministic stress or race-focused test where available.

If verification cannot be run, say what was not run and why.

### 5. Review The Diff

Before completion, scan for:

- unrelated edits
- speculative abstractions
- unclear names
- long or mixed-purpose functions
- comments that compensate for confusing code
- swallowed errors
- hidden shared state
- missing edge-case tests
- security-sensitive logging or input handling

## Principles

These principles summarize the working core. When a task needs deeper coverage, cross-check the matching chapter in `references/chapter-map.md`.

### Meaningful Names

Names should reveal intent without requiring mental decoding.

Use:

- domain vocabulary from the project
- searchable names for important concepts
- consistent terms for the same idea
- boolean names that read as predicates
- units in names when values need units

Avoid:

- misleading names
- generic names like `data`, `manager`, `helper`, `util`, `info`, or `result` when a domain name exists
- type encodings unless the language ecosystem expects them
- abbreviations that are not common in the project
- names that differ only by noise words

### Small Focused Functions

A function should have one reason to change and one level of abstraction.

Prefer:

- early exits for invalid or terminal cases when idiomatic
- extraction when a block has a clear independent purpose
- few parameters; group related values when the domain has a real concept
- command-query separation: either answer a question or cause a change, not both
- explicit side effects in names and call sites

Avoid:

- boolean flags that select unrelated behaviors
- functions that validate, transform, persist, log, notify, and render at once
- hidden mutation of inputs
- nested conditionals that hide the main path
- copy-pasted branches with tiny differences

### Comments And Documentation

Good comments explain why the code must be this way.

Keep comments for:

- non-obvious constraints
- legal or compliance requirements
- algorithmic tradeoffs
- external system quirks
- TODOs with context and ownership when the project uses them

Remove or avoid comments that:

- repeat the code
- lie because they are stale
- explain names that should be clearer
- preserve commented-out code
- create noise banners unless the project already uses them consistently

### Formatting And Layout

Formatting is part of communication.

- Match the project's formatter and import order.
- Keep related code near related tests or call sites when the project structure allows it.
- Separate concepts with whitespace, not decorative noise.
- Keep file organization predictable.
- Do not reformat an entire file while making a small change unless the formatter is the requested change.

### Data, Objects, And Modules

Choose the shape that makes invariants clear.

- Use data structures for plain data.
- Use objects, modules, records, structs, or types to protect invariants and behavior when needed.
- Keep classes and modules cohesive.
- Prefer explicit dependencies over hidden globals.
- Keep public APIs smaller than internal implementation details.
- Avoid god objects, kitchen-sink services, and catch-all utility modules.

### Error Handling

Errors are part of the design, not a cleanup afterthought.

Do:

- handle errors at the level that can make a meaningful decision
- preserve useful context
- keep original causes where the language supports it
- distinguish expected domain outcomes from exceptional failures
- make retry, fallback, and cancellation behavior explicit

Do not:

- swallow errors silently
- catch broad exceptions without rethrowing, wrapping, or reporting appropriately
- return sentinel values that callers can easily ignore unless that is idiomatic for the language
- log secrets, tokens, personal data, or sensitive payloads

### Boundaries

Boundaries are where bugs multiply: external APIs, databases, file systems, clocks, queues, UI events, network calls, subprocesses, and generated code.

- Validate inputs at trust boundaries.
- Keep third-party API assumptions localized.
- Add contract or integration tests when boundary behavior matters.
- Avoid leaking framework types through core domain code unless the framework is the domain.
- Make serialization, time zones, encodings, units, and nullability explicit.

### Tests

Tests should make behavior easy to understand and safe to change.

Prefer tests that:

- use behavior-focused names
- assert outcomes, not implementation details
- cover the changed edge cases
- are deterministic and isolated
- use readable fixtures
- fail for the right reason

Avoid:

- broad snapshots as the only assertion
- sleeps and timing guesses
- excessive mocking of your own code
- tests that duplicate implementation logic
- test changes that merely bless a bug

### Concurrency And State

Concurrent code must make ownership and ordering visible.

Check:

- shared mutable state
- cancellation and timeout behavior
- lock ordering and deadlock risk
- idempotency and retries
- lifecycle cleanup
- event ordering and backpressure
- race-prone tests

Prefer immutability, message passing, transactions, actor-like isolation, or language-native concurrency guarantees when idiomatic.

### Security As Clean Code

Security-sensitive code should be readable enough to audit.

- Validate and encode at boundaries.
- Use parameterized queries and safe APIs.
- Keep authorization checks close to protected operations or centralized in a clearly enforced policy layer.
- Do not log secrets or sensitive data.
- Prefer well-maintained standard libraries for crypto, parsing, auth, and serialization.
- Make privilege, trust, and data retention explicit.

### Performance

Clean code is not slow code; it is code whose cost is understandable.

- Measure before optimizing non-obvious bottlenecks.
- Keep algorithmic complexity visible.
- Avoid premature caches, pools, indexes, and background jobs.
- When optimizing, document the measured reason and keep the simpler behavior covered by tests.

## Smell Triage

When you see a smell, decide whether it is in scope.

Fix now only if it blocks the requested change, creates immediate risk, or was introduced by your work. Otherwise mention it separately.

Common smells:

| Smell | Look For | Usual Response |
| --- | --- | --- |
| Long function | mixed abstraction levels, many branches | extract named steps if touching the area |
| Duplicate knowledge | same rule in multiple places | centralize the rule when behavior is changing |
| Primitive obsession | repeated loose strings, numbers, maps | introduce a type only when it protects a real invariant |
| Boolean flag argument | one function doing two jobs | split functions or name modes clearly |
| Shotgun surgery | one concept changed in many files | find the missing boundary |
| Feature envy | code reaching into another module's internals | move behavior or expose a clearer API |
| Hidden temporal coupling | calls must happen in secret order | make state transitions explicit |
| Global mutable state | tests order-dependent, hidden inputs | inject dependencies or isolate state |
| Broad catch | failures disappear | handle, wrap, or propagate with context |
| Magic values | unexplained numbers or strings | name constants when they express domain meaning |

## Framework And Language Adaptation

Before applying a rule, adapt it to the ecosystem. Read `references/framework-map.md` when working in an unfamiliar language or stack.

Examples:

- In Go, small interfaces at consumers are often cleaner than deep class hierarchies.
- In Rust, encode invariants in types and ownership instead of defensive runtime checks everywhere.
- In SQL, clean code often means set-based operations, clear aliases, and predictable transaction boundaries.
- In React, clean code often means predictable rendering, separated effects, accessible markup, and state close to where it belongs.
- In shell, clean code means explicit quoting, strict error behavior, and simple command flow.

## Anti-Loopholes

Stop and reassess when you think:

| Rationalization | Reality |
| --- | --- |
| "I will clean this up while I am here." | That is unrelated work unless the task needs it. |
| "A framework will make this cleaner." | A dependency is a cost; prove the need. |
| "This abstraction will help later." | Later requirements can pay for later abstraction. |
| "The code is bad, so a rewrite is cleaner." | Rewrites need explicit scope, tests, and migration risk control. |
| "There are no tests, so verification is impossible." | Use the best available check and report remaining risk. |
| "Comments make it understandable." | Prefer clearer names and structure; comment only the why. |
| "Clean code means following this skill over local style." | Local, idiomatic style wins unless it is unsafe or broken. |

## Completion Checklist

Before saying the work is complete, confirm:

- The change solves the stated task.
- The diff is scoped.
- Names and structure reveal intent.
- Errors, boundaries, and state are explicit enough for the risk.
- Tests or checks match the behavior changed.
- No dead code introduced by the change remains.
- Verification results are known and reported honestly.

For reviews, use `references/review-checklist.md` for a finding-first checklist.
