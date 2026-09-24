# Scala

> Applies to: Scala 3 LTS (3.3.x, or the newer 3.9.x line). Formatter: scalafmt. Linter: Scalafix, WartRemover. Read with: nothing.

## Names

- Use camelCase for methods and values, PascalCase for classes, traits, and objects; per the Scala style guide, name a constant in UpperCamelCase (`MaxRetries`), never `SCREAMING_SNAKE_CASE` (N3).
- Name a `case class` or `enum` case as a noun in PascalCase; name a `given` for the capability it provides, never `given1` or `theInstance` (N1, N6).
- Name a pure function for the value it produces (`totalPrice`, `isEligible`), not the steps it takes (G20).
- Use one word per domain concept across every subproject; do not let `UserId` in one module and `AccountId` in another name the same thing (G11).
- Never name a value or method `data`, `info`, or `temp`/`tmp` (N1); keep a name that short only for a lambda parameter or a `for`-generator (N5).
- Never encode a type into a name (`strName`, `mCount`) (N6), or leave a rename half-done with `_v2`, `Old`, or `Final` (N1, N4).
- Never suffix a class or object `Manager`, `Helper`, or `Util(s)`, and never name one for a verb like `ProcessOrder` — a class is a noun (N1, G17).

## Functions And Types

- Model a closed set of cases as an `enum` or a `sealed trait` with `case class`/`case object` members, and end every `match` with no catch-all `case _`, so a new case fails to compile until handled (G23).
- Return `Option[A]` for an absent value; never model absence with `null` (Special Case pattern).
- Never call `.get` on an `Option`, `.head` on a `List`, or `apply` on a `Map` you have not proven non-empty in the same expression; pattern-match, `.map`, `.fold`, or `.get(key)` instead (G26).
- Default to `val` and immutable collections (`List`, `Vector`, `Map`); scope a `var` or a mutable collection to one private method, never a class field (G18).
- Declare a `given`/`using` instance only for a capability the type needs (an `Ordering`, a codec, an `ExecutionContext`); do not reach for one to shorten an unrelated signature.
- Avoid an implicit conversion between two unrelated types; write it as a named method so a reader can see it happen at the call site (G16).

## Errors

- Return `Either[DomainError, A]` (or the project's `Result` alias) for an expected alternate outcome like "not found" or "declined"; keep `throw` for a failure no caller can continue past (Special Case pattern).
- Never wrap a whole function body in `Try` to catch a class of errors you have not named; catch the one exception type you can act on (G4).
- Preserve the cause when turning a low-level exception into a domain one, rather than raising a new error with no link to the original.

## Modules And Visibility

- Default every member to `private`; widen to `private[thispackage]` only for code shared inside a package, and to fully public only for the subproject's API (G8).
- Keep a pure domain type and its companion `object` together; keep effectful code (`IO`, `Future`, a database client) in a separate class the domain module never depends on.
- Group a `case class` with the `enum`/ADT siblings it always changes with, in one file named for the concept, not one file per tiny type (G17).

## Placement

- Split an sbt build into subprojects along architectural boundaries (`domain`, `application`, `infra`), and let `dependsOn` express the allowed direction; a subproject never depends on one that would pull outward-facing code into the domain (the Dependency Rule).
- Keep a `given` beside the type it serves, or in a file named for what it provides; never collect unrelated `given`s into one `Implicits.scala` (G17).

## Tests

- Use MUnit or ScalaTest; name a test for the behavior it proves and keep one behavior per test (Single concept per test).
- Test every case of an `enum`/`sealed trait` match, and the `None`/`Left` branch of every `Option`/`Either`-returning function, not only the success path (T5).
- Pass a fixed `Clock`, seed, or `given ExecutionContext` instead of reading real time, randomness, or the global execution context, so tests stay repeatable (F.I.R.S.T.).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- The domain subproject's sources import nothing from `cats.effect`, `akka`, a database driver, or an HTTP client; declare the capability as a trait the domain owns, implemented in an outer subproject (DIP).
- Keep the composition root — wiring `given`s, building the runtime, calling `IOApp.run` or `main` — in one outermost subproject; domain and application code only declare what they need.
- Parse and validate external input into domain types at the boundary; serialize back out before the edge, never inside domain logic.

```clean-architecture
layer domain      = domain/src/main/scala/**
layer application = application/src/main/scala/**
layer infra       = infra/src/main/scala/**
layer main        = main/src/main/scala/**
```

## Enforce

- scalafmt for all formatting, checked in CI with `scalafmt --check`.
- Scalafix with `DisableSyntax` (ban `var`, `null`, `return`, `throw` where the project configures it) and `OrganizeImports`.
- WartRemover with at least `Null`, `Var`, `Return`, and `OptionPartial` enabled as errors.
- `dependsOn` direction between sbt subprojects reviewed like any other dependency graph; no subproject may depend the wrong way (ADP).

## Smells

- A method returning `null`, or a value compared `== null`, instead of `Option` (G26).
- `.get` on an `Option`/`Either` a few lines after a `Some`/`Right` check that could have carried the value through instead (G26).
- A stack of small traits mixed in with `with`, each contributing one method, where one class or a `given` would read clearer (G32).
- An implicit conversion changing a value's type at a call site with nothing to show it happened (G16).
- A `match` with no case for a value that can genuinely arrive, panicking at runtime instead of failing to compile (G3).
- One catch-all `Implicits.scala` or `package.scala` collecting unrelated `given`s (G17).
