# Dart

> Applies to: Dart 3.x. Formatter: `dart format`. Linter: `dart analyze` with `package:lints` or `very_good_analysis`. Read with: `frameworks/flutter.md`, if the project uses Flutter.

## Names

- Use lowerCamelCase for variables, functions, and parameters; UpperCamelCase for classes, enums, extensions, and typedefs; lowerCamelCase even for constants (N3).
- Name a boolean as a question (`isValid`, `hasSession`) and a function for what it returns or does (`parseToken`, `totalDue`) (G20).
- Name a file in snake_case after the one thing it exports (`user_repository.dart`), matching the class name it defines (G11).
- Never abbreviate a domain term to save keystrokes, or write a vague `data`/`info`/`item`/`temp` a reader must expand back in their head (N1); keep a name that short only for a loop index or lambda parameter (N5).
- Never encode a type into a name (`stringName`, `listItems`), or prefix an interface-like class with `I` — Dart uses neither (N6); never leave a rename half-done with `_v2`, `_old`, or a `Final` suffix (N1, N4).
- Never suffix a class `Manager`, `Helper`, or `Util(s)`, and never name one for a verb like `ProcessOrder`/`HandleLogin` — a class is a noun (N1, G17).

## Functions And Types

- Use `sealed` (or `enum`) for a closed set of cases and switch over it with patterns; the analyzer flags a missing case at compile time, so skip the `default` that hides one (G23).
- Return a record (`({bool ok, String message})`) for a small, local multi-value result instead of a positional `List`, a `Map`, or a one-off class (G26).
- Choose `final`, `base`, `interface`, or `sealed` on a class deliberately: `final` stops subclassing outside the library, `interface` allows only `implements`, `sealed` enumerates every subtype in one file — do not leave a type extensible without deciding (G32).
- Never use `dynamic` to avoid modeling a type; take `Object?` and narrow it with `is` or a pattern (G26).
- Never silence a nullability the compiler is right about with `!`; prove non-null with an `if`, `??`, or a pattern match instead (G4).

## Errors

- Throw an `Exception` subtype for a condition the caller can handle; reserve `Error` subtypes (`ArgumentError`, `StateError`, `UnimplementedError`) for programmer mistakes that should crash and get fixed.
- Never catch `Error` (or write a bare `catch (e)` that would); an `Error` means the program is wrong, not that the caller has a decision to make (G4).
- Model an expected alternate outcome — not found, declined, empty — as a return value (a nullable type, a record, or a small result type), not as a thrown exception (Special Case pattern).
- Give a custom exception an `Object? cause` field and pass the original error into it when wrapping a lower-level failure.
- Never drop a `Future` silently; `await` it, return it, or mark it `unawaited()` from `dart:async` on purpose.

## Modules And Visibility

- Prefix a library-private declaration with `_`; export only what other packages need from one curated `lib/<package>.dart`, with everything else under `lib/src/` (G8).
- Never import another package's `lib/src/`; only its public library files are its contract.
- Keep a top-level function or constant beside the type it serves; do not collect unrelated declarations into one file for being small.

## Placement

- Keep `main.dart` (or a CLI's entry file) to composition only: read configuration, construct dependencies, start the app; no business rule belongs there (G17).
- Name a file for the concept it holds (`order.dart`, `business_days.dart`), one primary public type per file, mirroring the project's folder-by-feature or folder-by-layer choice.
- Never add a project-wide `utils.dart` or `helpers.dart`; name the concept the functions share (G17).

## Tests

- Use `package:test` (`group`, `test`) or the project's existing runner; name a test for the behavior it proves.
- Inject a `Clock` or a seed instead of reading `DateTime.now()` or `Random()` directly, so tests stay repeatable (F.I.R.S.T.).
- Test every branch of a `sealed` hierarchy's `switch`, and the failure branch of every function returning a result type or nullable value, not only the success path (T5).

## Concurrency

- Move CPU-bound work off the event loop with `Isolate.run`; pass only data an isolate can copy, never a live object reference or open handle.
- Treat every `await` as a point where other code can run; re-read shared mutable state after it instead of assuming nothing changed (G31).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Domain code imports no `package:flutter`, no `dart:io` sockets or file APIs, and no generated client code; declare what it needs as an abstract class the domain owns, implemented outside.
- Compose the object graph in `main.dart` (or the composition root a Flutter app's `main.dart` calls) and pass collaborators down through constructors.

```clean-architecture
layer domain      = lib/domain/**
layer application = lib/application/**
layer adapters    = lib/adapters/**
layer main        = lib/main.dart
```

## Enforce

- `dart analyze --fatal-infos` in CI, with `analysis_options.yaml` including `package:lints/recommended.yaml` or `package:very_good_analysis/analysis_options.yaml`.
- The `unawaited_futures` lint enabled; treat a new warning as a bug, not noise to suppress.
- `dart format --set-exit-if-changed` in CI so formatting never drifts from what `dart format` would write.

## Smells

- `dynamic` where a real type, a generic, or `Object?` would do (G26).
- Business logic living in `main.dart` instead of a constructed, testable class (G17).
- A caught `Error`, or a `catch (e)` with no rethrow, keeping the program running past a bug (G4).
- Nested `if (x != null)` ladders that a record or a pattern match would flatten into one expression (G28).
- A public class or top-level function that nothing outside its own library ever calls (G8, F4).
