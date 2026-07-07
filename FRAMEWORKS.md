# Framework And Language Guidance

Clean code is portable as a set of questions, not as a single style. Use this guide to adapt the `clean-code` skill to the stack in front of you.

## Universal Questions

1. What behavior is changing?
2. What local idioms already exist?
3. Where do new files and new logic belong in this project's layout, and what wiring makes them reachable?
4. What names would a maintainer search for?
5. Where is the boundary: user input, API, database, file system, queue, clock, browser, device, or third-party service?
6. What failure mode matters most?
7. What is the narrowest verification that proves the change?
8. Which chapter-map area is most relevant: names, functions, comments, formatting, data structures, errors, boundaries, tests, classes, systems, emergence, concurrency, refinement, legacy refactoring, or smells?

## Language Notes

### JavaScript And TypeScript

- Prefer precise types and discriminated unions over loose objects.
- Keep async flow explicit; do not hide rejected promises.
- Avoid catch-all helpers that erase domain names.
- Keep framework effects, rendering, and data transformation separate when the local architecture supports it.

### Python

- Prefer clear modules and functions over clever dynamic behavior.
- Use exceptions with context; avoid broad `except Exception` unless re-raising or translating intentionally.
- Type hints are useful when they clarify contracts, but do not add noisy annotations in codebases that do not use them.
- Avoid mutable defaults and hidden global state.

### Go

- Return errors with context and check them.
- Keep interfaces small and usually define them at the consumer.
- Avoid package-level mutable state.
- Prefer simple structs and functions over inherited architecture patterns from other languages.

### Java, Kotlin, And C Sharp

- Keep classes cohesive and public APIs small.
- Use types to express nullability, domain concepts, and state transitions.
- Avoid service/manager sprawl that turns every operation into a vague method on a large class.
- Prefer composition over inheritance unless the hierarchy is stable and meaningful.

### Rust

- Encode invariants in types and ownership.
- Avoid `unwrap` and `expect` in production paths unless the invariant is local and obvious.
- Do not clone data just to silence ownership issues without checking cost and intent.
- Use error types that help callers decide what to do.

### Swift

- Use expressive names and value semantics where appropriate.
- Be explicit about actor, thread, and main-queue expectations.
- Avoid force unwraps in production paths.
- Keep view state and domain state distinct.

### PHP And Ruby

- Follow framework conventions, but keep domain behavior discoverable.
- Avoid magic callbacks and metaprogramming unless tests make behavior clear.
- Keep controllers thin when the framework encourages them to grow.
- Use service objects only when they name a real domain operation.

### C And C++

- Make ownership and lifetime explicit.
- Prefer RAII in C++.
- Check return codes and propagate context.
- Avoid macro cleverness and implicit shared state.

### Shell

- Quote variables.
- Make failure behavior explicit.
- Keep parsing simple.
- Use functions for repeated command groups, not for speculative libraries.

### SQL

- Name selected columns.
- Use explicit joins.
- Bind parameters through the database client.
- Keep transaction scope visible.
- Prefer set-based operations over row-by-row loops when possible.

## Framework Notes

### Frontend Components

- Keep rendering predictable.
- Put state close to where it is used unless sharing is required.
- Separate effects from pure rendering.
- Treat accessibility as part of clean structure, not polish.
- Avoid broad snapshots as the only test for behavior.

### Backend APIs

- Validate at request boundaries.
- Keep transport concerns out of domain logic when the codebase supports that separation.
- Return consistent error shapes.
- Test authorization, validation, and persistence boundaries.

### Mobile Apps

- Respect platform lifecycles.
- Keep UI work off blocking paths.
- Make permissions, offline behavior, and cancellation explicit.
- Avoid hidden dependencies on global navigation or current screen state.

### Data And ML

- Make schemas explicit.
- Keep data cleaning steps reproducible.
- Track units, time windows, sampling, and model versions.
- Avoid notebook-only production logic.

### Infrastructure As Code

- Name resources by purpose.
- Use least privilege.
- Avoid wildcard access without a documented reason.
- Keep environment-specific values explicit.
- Verify generated plans before claiming infrastructure changes are safe.

## When Rules Conflict

Specific local project instructions win over this general guide. If a local pattern is unsafe, explain the risk and make the smallest safe change required by the task.
