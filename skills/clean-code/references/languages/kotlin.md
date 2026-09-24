# Kotlin

> Applies to: Kotlin 2.x. Formatter: ktlint or ktfmt. Linter: detekt. Read with: the framework pack, if any.

## Names

- Use camelCase for functions and properties, PascalCase for types, lowercase-no-underscore for package names, UPPER_SNAKE for `const val`; never prefix an interface with `I` (N3, N6).
- Name booleans as questions (`isEmpty`, `hasErrors`) and functions for what they do or return (G20).
- Never carry Java-era prefixes like `m`, `_`, or Hungarian type tags into a name (N6).
- Name a file for the single top-level type it declares, or for the concept a group of extension functions belongs to — never `Extensions.kt` or `KotlinExt.kt` (G11, G17).
- Give sealed subtypes names that read as domain outcomes (`Declined`, `NotFound`), never `Type1`/`Type2`, a shared prefix repeating the sealed type's own name, or a half-finished `_v2`/`Final` rename (N1, N4).
- Never name a value `data`, `info`, `obj`, `item`, `temp`/`tmp`, or a function `handle`/`process` with no object (N1); keep a name that short only for a loop index or a lambda parameter (N5).
- Never suffix a class `Manager`, `Helper`, `Util(s)`, or `Data`, and never name one for a verb like `ProcessOrder` — a class is a noun (N1, G17).

## Functions And Types

- Default properties and locals to `val`; use `var` only when reassignment is the point.
- Model data-carrying types as `data class`; model a closed outcome set as `sealed interface`/`sealed class`, not a boolean plus a nullable field (Special Case pattern).
- Never use the not-null assertion `!!` — it crashes away from the value's source, not at it (G26); use `require()` for bad arguments and `check()` for broken invariants, both failing at the point of the mistake.
- Take default parameters and named arguments over telescoping overloads (F1); never add a boolean parameter that switches behavior — write two functions or a sealed parameter type (F3).
- Keep extension functions beside the type or file they extend; a scattered one risks duplication (G22).

## Errors

- Model expected alternate outcomes — not found, declined, invalid — as a sealed result type or the stdlib `Result<T>`, never a nullable value the caller must check (Special Case pattern).
- Never wrap a suspending call in `runCatching` without inspecting the failure for `CancellationException` and rethrowing it; swallowing cancellation leaves the parent coroutine unaware and produces zombie work (G4).
- Kotlin has no checked exceptions — do not rebuild one giant exception hierarchy every caller must import (Dependency magnet); give a thrown exception a specific type and `cause = original`, never a bare `catch (e: Exception) {}` that discards both (G4).

## Modules And Visibility

- Default to `internal`; make a class, function, or property `public` only when code outside the module calls it (G8).
- One Gradle module or source set per bounded component; a domain module's public API names no Android, Ktor, Spring, or JDBC type (the Dependency Rule).
- Keep DI wiring (Koin, Dagger/Hilt, Spring `@Configuration`) in the outermost module; inner modules take collaborators as constructor parameters, never a framework annotation.
- Never keep mutable state in a top-level `var`; it is global state wearing a file-scoped disguise (G18).

## Placement

- Mirror the project's module layout: a multi-module Gradle build keeps `domain`, `data`, and `app` (or local names) as separate modules, not folders inside one.
- Put a class's tests under `src/test/kotlin`, mirroring its `src/main/kotlin` package path.
- Never grow a `Utils.kt` or `Helpers.kt`; name the domain concept the functions belong to (G17).
- New top-level code goes where it belongs, not in the file already open in the diff.

## Tests

- Use JUnit 5 or Kotest, and MockK to mock suspend functions, final classes, and objects without reflection workarounds.
- Name tests for the behavior they prove — Kotest's spec styles read as sentences, JUnit 5 reads well with backtick names (`` `rejects a negative quantity`() ``).
- Drive a suspending function under test with `runTest` (kotlinx-coroutines-test); never `runBlocking` in production code.
- Cover every branch of a `sealed` result in its own test; a `when` with a silent `else ->` in test code hides an untested branch (T5).

## Concurrency

- Never launch from `GlobalScope`; every coroutine gets a scope tied to a lifecycle — `viewModelScope`, a request scope, or a structured `coroutineScope { }` (G18).
- Move blocking calls — JDBC, legacy blocking clients, file I/O — onto `Dispatchers.IO` with `withContext`; never block a default or event-loop dispatcher.
- Start independent work with `async`/`awaitAll`, not sequential `await` calls inside a loop.
- Treat cancellation as cooperative: a long CPU-bound loop must check `isActive` or call a suspending function so cancellation lands.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- A domain module imports nothing outward-facing, exposing only plain Kotlin types and interfaces (the Dependency Rule).
- Declare a port as a Kotlin interface in the domain module; outer-module adapters implement it, and the composition root wires it in.
- Keep the DI graph's construction in one composition root per app or service; nothing inward references the DI framework.

```clean-architecture
layer domain      = domain/**, core/**
layer application = application/**, usecase/**
layer adapters    = adapters/**, infrastructure/**
layer main        = app/**, main/**
```

## Enforce

- detekt's complexity rules — `LongMethod`, `LongParameterList`, `CyclomaticComplexMethod`, `TooManyFunctions` — fixed by redesigning, not by raising the threshold.
- Konsist for architectural conventions (layer dependencies, forbidden imports, naming) alongside detekt's style rules.
- ktlint or ktfmt run in CI, not only the IDE formatter, so a change and its formatting agree.

## Smells

- A god object accreting unrelated responsibilities because it was already open (G30).
- A sprawling top-level `Utils.kt` or `Extensions.kt` that nothing else wants to own (G17).
- `!!` scattered through a codebase in place of a null check at the value's source (G26).
- A `when` over a sealed type patched with `else -> {}` instead of handling the new branch (G23).
- Business rules importing `android.*`, `io.ktor.*`, or a persistence annotation directly (G17, the Dependency Rule).
