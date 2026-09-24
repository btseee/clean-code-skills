# CSS

> Applies to: current Baseline CSS (native nesting, cascade layers, container queries, `:has()`, custom properties, logical properties). Formatter: Prettier. Linter: Stylelint (`stylelint-config-standard`). Read with: nothing.

## Names

- Name a class for what it is or does in the domain, never how it looks: `.alert`, not `.red-text`; `.is-collapsed`, not `.hidden-block` (N2).
- Pick one casing convention and one naming system — kebab-case, and BEM (`.card__title--compact`) where the project uses it — never two conventions in one stylesheet (G11).
- Never hedge a name with a version or a fix marker: `.tmp-fix`, `.wrapper2`, `.box-final` all mean the real rename never happened (N1, N4).
- Never stack noise words onto a class: `.header-wrapper-inner-box` says nothing `.header` didn't already say (N1).
- Give a custom property the same intention-revealing name as any other identifier: `--color-brand-500`, never `--c1` or `--tmp` (N1, N5).
- Never name a class `.data`, `.info`, `.item`, or `.thing` alone; a class names the concept, not a placeholder for one (N1).
- Reserve an ID for a unique document landmark (a skip-link target); never select on it for styling — its specificity (1,0,0) outranks any number of classes (G24).

## Functions And Types

- Give every value repeated more than once — a color, a spacing step, a duration — one custom property; a hex code or a magic `14px` used twice is undeclared knowledge (G25).
- Declare a token's type and default with `@property` (`syntax`, `inherits`, `initial-value`) when animation or type safety depends on it; without it, a custom property is an untyped string.
- Compute a related value instead of hand-picking a second one: `color-mix(in oklab, var(--color-brand) 80%, white)` for a tint, `clamp(1rem, 2vw + 0.5rem, 1.5rem)` for fluid sizing — the tint follows the brand color (G5).
- Scope a custom property to where it is overridden — a component root, a media query — not only `:root`; a property only one component reads belongs on that component (G22).

```css
:root { --color-brand: #3457d5; --space-md: 1rem; }
.card {
  --card-gap: var(--space-md);
  padding: var(--card-gap);
}
```

## Errors

- The cascade drops an invalid declaration; nothing throws. Lint (`property-no-unknown`, `unit-no-unknown`, `color-no-invalid-hex`) or a typo ships unnoticed (G4).
- Give a `var()` read a fallback wherever the token is not always set — `color: var(--surface, #fff)` — so a missing token degrades instead of invalidating the declaration (Special Case pattern).
- Guard a feature the project's targets cannot all render with `@supports (...)`; keep the declaration outside the guard so every target gets a working rule (G3).
- Never win an override with a specificity fight — a deeper selector chain or `!important` — that hides which rule the author expected to apply (G16).

## Modules And Visibility

- Declare cascade layers once, in one file, in the order the project loads them (`@layer reset, tokens, base, components, utilities;`); every other stylesheet adds to a named layer instead of fighting specificity across files (G22).
- Scope a component's selectors with `@scope`, CSS Modules, or one component-root class prefix so they cannot leak onto unrelated markup; do not lean on deep descendant selectors for isolation (G8).
- Keep specificity low and let layer order decide overrides: a later layer beats an earlier one whatever the selectors' specificity, so utilities need no `!important`. `!important` reverses layer order — an important reset beats an important utility (G24).
- Export design tokens from one file; a component file may read them but never redeclare a project-wide token under a different value (G5).

## Placement

- Keep a component's stylesheet beside the component it styles; a cross-cutting stylesheet (reset, tokens, layout) lives at the project's style root.
- Keep the `@layer` order declaration in one file, loaded before every other stylesheet.
- Never add a rule to a catch-all `misc.css` or `extra.css`; name the concept the rule belongs to instead (G17).

## Tests

- Run Stylelint in CI on every stylesheet; treat a warning on the main branch as a failing test (G4).
- Add visual-regression coverage (Playwright, Chromatic, or the project's tool) for components whose layout or theme correctness matters — a snapshot catches what a linter cannot (T1).
- Test a dark-mode or container-query breakpoint by asserting the rendered state, not by reading the source rule back (T5).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Stylesheets are the outermost UI detail: they decide appearance, never business rules — a discount, a permission, or a status is never expressed as a CSS class an inner layer cannot name.
- A component chooses which class or token to apply from data the application layer computed; the stylesheet makes no decision.
- Design tokens are the one interface a stylesheet exposes inward: name them for the design system's terms, not the implementation, so an inner layer can reference a token name without knowing its value.

## Enforce

- Stylelint with `stylelint-config-standard`; add `declaration-no-important` and `custom-property-pattern` to enforce token naming.
- `stylelint-order` (`order/properties-order`) when the project fixes a property order; `stylelint-config-standard` sets none.
- Prettier for formatting; never hand-align values or fight the formatter's line breaks.

## Smells

- A hex code, pixel value, or duration repeated across selectors instead of named once (G25).
- A dark theme or breakpoint built by duplicating every rule instead of overriding tokens (G5).
- An ID selector, or a selector chain reaching several levels into a component's markup, used to win a specificity fight (G13).
- `!important` used to win a specificity fight instead of a layer (G24).
- A `misc.css` or `global.css` catch-all that keeps absorbing unrelated rules (G17).
- A `var()` read with no fallback, that invalidates the declaration once the token is unset (G3).
