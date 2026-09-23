# Flutter

> Applies to: Flutter 3.x. Language pack: `languages/dart.md`. Read with: nothing.

## Structure

- `lib/main.dart` — composition root: builds the widget tree and wires top-level dependencies.
- `lib/screens/` or `lib/pages/` — one full-page widget per app destination.
- `lib/widgets/` — small, reusable widgets shared across screens.
- `lib/notifiers/` or `lib/providers/` — `ChangeNotifier`/`Notifier`/`AsyncNotifier` classes holding UI state.
- `lib/blocs/` or `lib/cubits/` — `Bloc`/`Cubit` classes, where the project follows that pattern instead.
- `lib/repositories/` — data-access contracts and their implementations.
- `lib/services/` — a thin wrapper around one external API or platform channel.
- `lib/models/` — immutable data classes and their (de)serialization.
- `test/` mirrors `lib/`; a widget's test sits beside the folder it tests.

## Roles

```clean-roles
role widget = **/widgets/**, **/screens/**, **/pages/**
role notifier = **/notifiers/**, **/providers/**
role bloc = **/blocs/**, **/cubits/**
signal widget = extends\s+(?:StatelessWidget|StatefulWidget|ConsumerWidget|ConsumerStatefulWidget|HookWidget)
signal state = extends\s+State<
signal bloc = extends\s+(?:Bloc|Cubit)<
signal notifier = (?:extends|with)\s+(?:ChangeNotifier|Notifier|AsyncNotifier|StateNotifier)\b
ignore-name = ^(MyApp|App)$
```

## Rules

- Keep a widget small; extract a child widget instead of nesting builders or nested ternaries inside one `build` (G30).
- Mark every constructor `const` where its fields allow it; a widget that cannot be `const` rebuilds when it could have been skipped.
- Never perform I/O, start a timer, or navigate as a side effect of `build`; `build` runs on every frame and must stay pure — start work in `initState`, a lifecycle callback, or an event handler (G17).
- Hold loading, data, and error explicitly (a small sealed result type, or three fields) in a notifier, cubit, or `State`, and let the widget render each — never infer status from nullability alone (G26).
- Check `context.mounted` (or the `State`'s `mounted`) after an `await` before touching `BuildContext` again (`use_build_context_synchronously`).
- Dispose every controller, stream subscription, or listener created in `initState` inside `dispose`.
- Key a widget a parent may reorder or replace, so Flutter matches state to the right element, never the list index, when order can change.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Widgets, `State`, notifiers, and blocs are the delivery layer: they render and dispatch; they never decide a business rule themselves.
- A repository implements an interface the application layer declares; a widget or notifier never constructs an `http.Client` or a database driver itself.
- Compose the dependency graph in `main.dart` and pass collaborators down through constructors; a widget never reaches for a global singleton to find one.

```clean-architecture
layer domain         = lib/domain/**
layer application    = lib/application/**
layer infrastructure = lib/repositories/**, lib/services/**
layer ui             = lib/widgets/**, lib/screens/**, lib/pages/**, lib/notifiers/**, lib/providers/**, lib/blocs/**, lib/cubits/**
layer main           = lib/main.dart
```

## Tests

- Test a widget with `flutter_test`'s `testWidgets` and `WidgetTester`: pump it, then assert on the rendered tree, never on a private field.
- Test a notifier, cubit, or bloc as a plain object — construct it, call its methods, assert what it emits — with no widget tree involved.
- Fake the repository or service interface in every widget and notifier test; a test never makes a real network call.
- Use `bloc_test` for a Bloc/Cubit's state-sequence assertions where the project already depends on the bloc package.

## Enforce

- `flutter analyze`, based on `package:flutter_lints` or the stricter `package:very_good_analysis`, in `analysis_options.yaml`.
- `use_build_context_synchronously`, `prefer_const_constructors`, and `prefer_const_literals_to_create_immutables` enabled and treated as build failures.
- `flutter test --coverage` in CI; golden tests for a pixel-sensitive widget.

## Smells

- `build` calling `http`, a database, or `Future.delayed` directly (G17, G30).
- A widget hundreds of lines long, mixing layout, formatting, and business rules (G30).
- The same validation rule duplicated between a widget and its notifier (G5).
- `setState` or `BuildContext` used after an `await` with no `mounted` check (G3).
- A `StatefulWidget` whose `State` never disposes what it created in `initState` (G31).
- Deeply nested `Consumer`/`BlocBuilder`/ternary widgets where extraction would flatten the tree (G28).
