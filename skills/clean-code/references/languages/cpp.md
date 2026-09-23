# C++

> Applies to: C++20 and C++23. Formatter: clang-format. Linter: clang-tidy and cppcheck. Read with: nothing.

## Names

- Match the project's existing casing for types versus functions and variables; never introduce a second convention in the same header (G11).
- Name a RAII wrapper for the resource it owns (`FileHandle`, `ScopedFd`), never `Manager` or `Wrapper` (N1, G12).
- Name a concept for the constraint it guarantees (`Sortable`, `Hashable`), not for its syntax.
- Name a template parameter for its role when there are several (`TKey`, `TValue`); a lone `T` is fine.

## Functions And Types

- Follow the rule of zero: let special members default once every member already manages its own resource; write a destructor only when one is truly needed.
- Never pair a raw `new` with `delete` in application code; use `std::make_unique`/`std::make_shared` or a container, so the destructor is the only release path (RAII).
- Take `std::span` or `std::string_view` for a non-owning view over contiguous data instead of a pointer-and-length pair.
- Mark a function `[[nodiscard]]` when ignoring its result is a likely bug; prefer `enum class` over a plain `enum`; constrain templates with concepts instead of unconstrained `typename`.
- Make every object and member function that does not mutate state `const` (Con.1, Con.2); leave `const` off by-value parameters in declarations, where it tells a caller nothing.

## Errors

- Pick one error model per API boundary — exceptions, or `std::expected<T, E>` for an expected alternate outcome — and keep it consistent across that boundary (Special Case pattern).
- Never let an exception cross an `extern "C"` or plugin boundary; catch and translate to a status there.
- Catch by `const&`, never by value; preserve the cause with `std::throw_with_nested` or as `std::expected`'s error value.
- Never write an empty `catch (...)` that discards the failure (G4).

## Modules And Visibility

- Put translation-unit-internal names in an unnamed namespace instead of relying on `static` (G8).
- Keep public headers under `include/<project>/`; anything without a matching public header is implementation-private under `src/`.
- Prefer `class` (private by default) over `struct` for any type with an invariant to protect.
- Never expose a member that lets a caller bypass an invariant the constructor established.

## Placement

- Mirror `include/<project>/foo.hpp` with `src/foo.cpp`; one primary type, or one small family of related types, per pair.
- Split a header that every translation unit includes and every actor edits for a different reason; a god header is a misplaced-responsibility smell (G17).
- Put tests under `tests/`, mirroring `include/`/`src/` by name.

## Tests

- Use whichever the project already depends on — GoogleTest, Catch2, or doctest — never a second (G11).
- Test through the public header only; reaching into a private member to assert couples the test to implementation.
- Cover ownership edge cases: moved-from state, self-move, self-assignment, an empty span or string_view (T5).
- Run the suite under the sanitizers in CI, not only locally.

## Concurrency

- Prefer `std::jthread` over `std::thread`: it joins automatically and carries a `std::stop_token` for cooperative cancellation.
- Lock more than one mutex at once only with `std::scoped_lock`, never nested individual locks — that breaks circular wait, one of the four deadlock conditions.
- Keep a critical section to the minimum work that must be atomic; copy data out and compute outside the lock.
- Run race-prone code under ThreadSanitizer (`-fsanitize=thread`) before trusting it.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- The core never includes a framework, ORM, socket, or GUI header; declare a pure-virtual interface or a concept there, and implement it in the adapter (the Dependency Rule, DIP).
- Compose the object graph — construct adapters, inject them into the core's interfaces — in `main.cpp` only (Main as the ultimate detail).
- Let CMake enforce the direction: link adapters `PRIVATE` to the core, never the reverse, and never link one adapter target to another (ADP).

```clean-architecture
layer domain      = include/*/domain/**, src/domain/**
layer application = include/*/application/**, src/application/**
layer adapters    = src/adapters/**
layer main        = src/main.cpp
```

## Enforce

- clang-tidy: `cppcoreguidelines-*`, `modernize-*`, and `bugprone-*`, plus `readability-function-size` and `readability-function-cognitive-complexity` for oversized or tangled functions, and `misc-include-cleaner` so headers declare what they use.
- cppcheck for the defects clang-tidy's checks do not model.
- CMake `PRIVATE`/`PUBLIC`/`INTERFACE` link keywords to keep the component graph acyclic and enforce the layer direction above.

## Smells

- Macro cleverness standing in for a `constexpr` value, an inline function, or a template (G27).
- An owning raw pointer with a hand-written `delete` far from its `new` — no RAII wrapper in sight.
- A god header included everywhere and edited for unrelated reasons (G17).
- Mutable global or function-local `static` state shared across calls, making tests order-dependent (G18).
- A `catch (...)` that discards the exception instead of deciding or rethrowing (G4).
