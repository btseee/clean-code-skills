# Swift

> Applies to: Swift 6.0+ in the Swift 6 language mode (strict concurrency checking on by default; Swift 6.2's approachable concurrency where a project opts in). Formatter: swift-format or SwiftFormat. Linter: SwiftLint. Read with: the framework pack, if any.

## Names

- Name types and protocols as nouns in UpperCamelCase; name methods and functions as verb phrases that read as a sentence at the call site (`employees.remove(at: x)`, not an ambiguous `remove(x)`) (G20).
- Favor clarity at the call site over brevity; omit an argument label only when the call reads unambiguously without it.
- Name a `Bool` property or method as an assertion (`isEmpty`, `canEdit(_:)`); use one word per concept across a module instead of mixing synonyms (G11).
- Never abbreviate a type into a variable name (`vc`, `mgr`, `tmp`); spell out `viewController`, `manager` (N1).
- Never name a type `Manager`, `Helper`, or `Util`; name the actual responsibility (G17).

## Functions And Types

- Default to `struct` and `enum`; reach for `class` only for reference identity, inheritance, or Objective-C interop.
- Mark every class `final` unless it is deliberately designed as a base class.
- Keep a function to one screen and one level of abstraction; extract a named function instead of nesting closures three deep (G34).
- Replace a `Bool` parameter that switches behavior with two named functions or an `enum` (F3); use default parameter values instead of overloads that only vary a flag.
- Model alternatives as `enum` cases with associated values and `switch` over them exhaustively; a `default:` that silences a new case is a bug waiting to ship (G23).
- Use `guard` for preconditions and early exits, so the happy path stays unindented at the end of the function.
- Prefer value semantics; confine the mutable reference types you do need to one clear owner.

## Errors

- Throw a typed `Error` enum per domain; never throw a bare string or a generic `NSError` from new Swift code.
- Reserve `throws` for genuine failures; model expected absence or alternatives with `Optional` or a domain `enum`, not a thrown error (Special Case pattern).
- Adopt typed throws (`func load() throws(FeedError)`) where every call site handles one concrete error type; keep untyped `throws` where callers genuinely need `any Error`.
- Never use `try!`, and never force-unwrap (`!`) or force-cast (`as!`) outside a precondition you just proved true; prefer `guard let`, `if let`, or `??` (G3).
- Never catch an error only to print it and swallow it; propagate with `throw` or handle it with a specific `catch let error as SpecificError` (G4).
- Preserve the original failure: wrap it as an associated value or through `CustomNSError`, never rethrow a new error with the cause discarded.

## Modules And Visibility

- Default to `internal`; mark a declaration `public` or `package` only when another module genuinely uses it, and `private`/`fileprivate` for implementation detail (G8).
- Give a SwiftPM target one clear public surface; keep helper types `internal` even when the target is small.
- Publish a read-only property with `private(set)` instead of a getter method plus a separately mutable backing field.
- Put an extension where its purpose lives (`Feed+Formatting.swift`), not scattered unrelated `extension` blocks across the codebase (G13).

## Placement

- Mirror the SwiftPM layout: `Sources/<Target>/...`, `Tests/<Target>Tests/...`; production code never lives under `Tests/`.
- Name a file after the type it declares; split a file that declares more than one unrelated top-level type (G17).
- Keep `Package.swift` and the `@main` entry thin: wire dependencies and start, with no business rules of their own.
- Never add to a catch-all `Utilities.swift` or `Extensions.swift`; name the concept the new code actually adds (G17).

## Tests

- Default new tests to Swift Testing (`@Test`, `#expect`, `#require`); keep XCTest for UI automation (`XCUIApplication`) and suites not yet migrated.
- Name each `@Test` for the behavior it proves, and use `@Test(arguments:)` for boundary values instead of copy-pasted near-duplicate tests (T5).
- Keep tests deterministic: inject a fake clock or a stubbed `URLProtocol` instead of hitting the network, and `await` async work instead of sleeping for it.
- Test domain types without importing SwiftUI or UIKit; view and view-model tests are a separate, smaller layer.

## Concurrency

- Build in the Swift 6 language mode with strict concurrency checking; never silence a data-race diagnostic with `@unchecked Sendable` unless the reason is documented beside it.
- Give shared mutable state a single `actor` owner; mark UI-facing types `@MainActor` explicitly, or rely on a module's default main-actor isolation (Swift 6.2 approachable concurrency) and opt heavy work out with `@concurrent`.
- Make cross-boundary types `Sendable`: value types earn it for free; a reference type needs an actor or real synchronization, never a cast that just quiets the compiler.
- Never block a thread with a semaphore or `.wait()` inside `async` code; `await` the work instead (G31).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- A domain target imports neither `UIKit` nor `SwiftUI`; it depends only on Foundation and its own types (the Dependency Rule).
- Declare a capability the domain needs as a `protocol` inside the domain target; an adapter target implements it and is injected through an initializer.
- Wire concrete adapters together only in the app target's composition root (the `@main` entry point), never inside a domain or feature type.

```clean-architecture
layer domain      = Sources/Domain/**
layer application = Sources/Application/**
layer adapters    = Sources/Adapters/**, Sources/Infrastructure/**
layer main        = Sources/App/**
```

## Enforce

- SwiftLint: `function_body_length`, `cyclomatic_complexity`, `function_parameter_count`, `force_unwrapping`, `force_try`.
- `swift build`/`swift test` with warnings treated as errors, and `-strict-concurrency=complete` where the module hasn't fully adopted Swift 6 mode yet.
- `swift-format lint` or `swiftformat --lint` in CI so an unformatted diff fails the build.

## Smells

- A "massive view controller" or view absorbing networking, parsing, and layout at once (G30).
- A singleton (`.shared`) standing in for dependency injection, hiding a type's real collaborators (G18).
- A force unwrap or `try!` guarding a path that is not actually guaranteed (G3).
- A closure capturing `self` strongly across an async gap while assuming the main thread without `@MainActor` (G31).
- A protocol with exactly one implementation and no second caller in sight — speculative abstraction, not flexibility (G32).
