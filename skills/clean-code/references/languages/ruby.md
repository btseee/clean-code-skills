# Ruby

> Applies to: Ruby 3.4 and 4.0 (3.3 in security maintenance). Formatter: RuboCop (`rubocop -A`) or Standard. Linter: RuboCop or Standard. Read with: nothing.

## Names

- Use `snake_case` for methods, locals, and file names; `PascalCase` for classes and modules; `SCREAMING_SNAKE_CASE` only for true constants (N3).
- Suffix a predicate method with `?` and return only `true`/`false` from it (`valid?`, `empty?`), never a value that merely happens to be truthy (G20).
- Suffix a dangerous or mutating method with `!` only when a safer non-bang sibling exists (`save!` beside `save`); a lone bang with no counterpart just hides risk (N7).
- Name a file after the one constant it defines, on the path Zeitwerk expects (`order_summary.rb` for `OrderSummary`) (G11).
- Never abbreviate a domain word to save keystrokes, or write a vague `data`/`info`/`temp`/`tmp`, or a bare `process`/`handle` with no object; keep a name that short only for a block parameter or loop index (N1, N5).
- Never encode a type into a name (`str_name`, `arr_items`) or carry a Java-style `I` prefix (N6); never leave a rename half-done with `_v2`/`_old`, or a trailing digit like `user2` (N1, N4); never suffix a class `Manager`/`Helper`/`Util(s)`, or name one for a verb like `ProcessOrder` (N1, G17).

## Functions And Types

- Keep methods short and at one level of abstraction; extract a private method instead of commenting a step (G30, G34).
- Take keyword arguments once a method needs more than one or two values, so calls read without counting positions (F1).
- Never add a boolean parameter to select behavior; write two methods, or branch before calling either (F3).
- Model a value with `Data.define` (or a small `Struct`/plain object) instead of a multi-key `Hash` passed between methods.
- Add `# frozen_string_literal: true` to new files and never mutate a literal; `.dup` it first if you must.
- Prefer composition and modules (`include`, `extend`) over deep inheritance into a base class's internals.

## Errors

- Raise a custom class under `StandardError` (never a bare `RuntimeError` or a string) so a caller can `rescue` it precisely; when re-raising, preserve the cause with `raise SomeError, "message", cause: e` or Ruby's automatic `cause` chaining — never swallow `e` silently.
- Rescue the narrowest class the call site can act on; never `rescue Exception`, and never a bare `rescue => e` that does nothing with `e` (G4).
- Model an expected alternate outcome — not found, declined, empty — as a return value or a small result object, and reserve `raise` for genuine failures (Special Case pattern).
- Use `ensure` for cleanup that must run regardless of outcome; never leave a file, connection, or lock unclosed on the error path.

## Modules And Visibility

- Default new methods to `private`; promote what another object calls to `public`, and reserve `protected` for comparisons between instances of the same class (G8).
- Never reopen a class you do not own to patch its behavior; wrap it, subclass it, or scope a `refine` to where it is needed (G18).
- Keep class variables (`@@count`) and globals (`$thing`) out of new code; pass a collaborator through `initialize` instead (G18).
- Namespace a package's public surface under one top-level module so a packwerk boundary can key off it.

## Placement

- Mirror the project's layout (`app/`, `lib/`, or a packwerk package's folder); never invent a new top-level folder for one class.
- Keep `lib/` for code with no framework dependency; keep framework-autoloaded code where the framework expects it.
- Never grow a shared `helpers.rb` or `utils.rb`; name the concept the methods share and give it its own file (G17).
- Keep a class, its test, and its factory discoverable from the class name alone.

## Tests

- Use the project's existing framework, RSpec or Minitest; never introduce the other into a single-framework project (G24).
- Name examples for behavior (`it "rejects an expired card"`) and assert outcomes, never internals.
- Keep specs deterministic: freeze time, stub the network, never depend on run order (F.I.R.S.T.).
- Add a test at every boundary you touch and beside every bug you fix (T5, T6).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Keep domain rules in plain Ruby objects that require no framework, ORM, or HTTP client (the Dependency Rule).
- Declare a port as a small role module or a documented duck type; the domain calls it, an adapter implements it, injected in rather than required directly.
- Enforce the boundary with packwerk: give each layer its own package and `package.yml`, with `enforce_dependencies: true` so a forbidden `require` fails CI.
- Compose the object graph where the process starts (a framework initializer, or a script's entry point), never inside a domain object.

```clean-architecture
layer domain      = lib/domain/**
layer application = lib/application/**
layer adapters    = lib/adapters/**
```

## Enforce

- RuboCop or Standard, with `Metrics/MethodLength`, `Metrics/AbcSize`, `Metrics/CyclomaticComplexity`, and `Metrics/ParameterLists` at the project's limits.
- `rubocop-performance` and any framework extension when the project uses one; Standard has no RuboCop-extension support, so use RuboCop where you need them.
- packwerk (`bin/packwerk check`) in CI once packages are declared, so the boundary stays real.
- RSpec or Minitest in CI, never a manual-only step (E2).

## Smells

- `method_missing` used for routing instead of a small set of real methods; it hides the API from `grep` and from callers (G16).
- A class variable or global standing in for an explicit collaborator (G18).
- A monkey-patched core class (`String`, `Hash`) changing behavior application-wide (G18).
- A bare `rescue => e` (or `rescue Exception`) that discards `e` and returns `nil` (G4).
- A bang method with no non-bang sibling, or a `?` method that returns something other than `true`/`false` (N7, G20).
- A `utils.rb` or a `concerns/` grab-bag with no cohesive theme (G17).
