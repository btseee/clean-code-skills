# Sass

> Applies to: Dart Sass 1.105+, SCSS and the indented syntax. Formatter: Prettier. Linter: Stylelint (`stylelint-config-standard-scss`). Read with: `languages/css.md` — the compiled output is CSS, so its cascade, naming, and layer rules apply; this pack adds the preprocessor's own rules.

## Names

- Name a variable, mixin, or function for the role it plays, not the value it currently holds: `$color-brand`, never `$blue-1` (N2).
- Use kebab-case for every Sass identifier — variables, mixins, functions, placeholders — matching CSS's own convention; never mix in camelCase or snake_case — Sass treats `-` and `_` as the same character, so `$font_size` silently aliases `$font-size` (G11).
- Never hedge a name with a version or a fix marker: `$spacing-v2`, `%card-old`, `_helpers-new.scss` all mean the real rename never happened (N1, N4).
- Name a mixin or function for what it produces (`button-reset`), not the bug it patches (`fix-button-again`) (N1).

## Functions And Types

- Model a related set of values as one Sass map, not a spray of separate variables: `$spacing: (sm: 0.5rem, md: 1rem, lg: 2rem)`, read with `map.get($spacing, md)` (G25).
- Reach for a built-in module before hand-rolling: `sass:math` for arithmetic and `math.clamp`, `sass:color` for `color.adjust`, `sass:list` and `sass:map` for collections — load with `@use "sass:math"` (G24).
- Use `math.div()` for division; plain `/` still divides outside `calc()` but is deprecated and warns on every build (G24).
- Write a `@function` to compute a value and a `@mixin` to emit declarations; never a mixin that hands back a result through a `!global` variable (G18).

## Errors

- Validate a map's shape or an argument's type at the top of a mixin or function (`@if not map.has-key($tokens, $key) { @error "..." }`) before using it, so a caller learns immediately, not three nesting levels into generated CSS (G3).
- Write an `@error` message that names the bad value and the shape expected; a silently wrong computed value is harder to find than a build that stops.
- Never silence a failing `@extend` with `!optional` or an empty placeholder; a missing target is a real defect (G4).

## Modules And Visibility

- Load every partial with `@use`, never `@import`: Dart Sass deprecated `@import` in 1.80 (October 2024) and targets removal in Dart Sass 3.0, no earlier than October 2026 — new and touched files use the module system now (G24).
- Prefix a member with `-` or `_` (`$-internal-ratio`) to make it private: the module system hides prefixed members from every `@use` and `@forward` (G8).
- Re-export a partial's public pieces with `@forward`, restricted with `show`/`hide` or a prefix, never a wildcard re-export of internals a consumer should not reach (G8).
- Give each `@use` a clear namespace; reserve `as *` for one project-wide, deliberately unnamespaced tokens file, never as a habit (G22).

## Placement

- One partial (`_name.scss`) per concept — one component, one set of tokens, one set of mixins; never a `_helpers.scss` collecting unrelated mixins (G17).
- Keep partials under the project's style root, mirroring how components are organized; a component's own partial sits beside the component when the project co-locates styles.
- Keep the compiled entry point (`main.scss`/`app.scss`) to `@use`/`@forward` statements and the `@layer` order; it declares the build, it does not itself hold rules (G6).

## Tests

- Lint every `.scss` file with Stylelint and `stylelint-config-standard-scss` in CI; a `@warn` left behind after debugging is clutter that earns no keep (G12).
- Run `sass --fatal-deprecation=import` (repeat the flag per deprecation ID, for example also `slash-div`) in CI once the project is ready to stop tolerating those warnings.
- Cover a nontrivial function or mixin — a responsive-map generator, a color-contrast helper — with `sass-true` unit tests or a snapshot of its compiled CSS (T1).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Sass compiles to CSS and carries the same outermost-UI-detail position `languages/css.md` describes; a mixin or function never encodes a business rule — a price break, a permission — that an inner layer should own.
- Token maps are the interface a stylesheet exposes inward: name entries for the design system's vocabulary so an inner layer can request a token by name without knowing the Sass that produced it.

## Enforce

- Stylelint with `stylelint-config-standard-scss` (extends `stylelint-config-standard`, bundles the `stylelint-scss` plugin); add `at-rule-disallowed-list: ["import"]` once migration is done.
- `sass --fatal-deprecation=<id>` in CI to stop a chosen deprecation warning (`import`, `slash-div`, ...) from creeping back in.
- Prettier for `.scss` formatting; the indented syntax has thinner tooling support, so format it by convention (two-space indent, no braces) instead.

## Smells

- A committed `.scss` file still written against `@import` for project code (G24).
- The same map or variable declared in two partials that must always agree (G5).
- Nesting several levels deep, producing a long compiled selector chain nobody intended (G6).
- `@extend` reaching across unrelated components for a shared look, coupling their compiled output (G13).
- A mixin used at exactly one call site, adding indirection with no reuse to justify it (G32).
- Plain `/` used for division outside `calc()`, relying on a deprecation warning nobody reads (G4).
