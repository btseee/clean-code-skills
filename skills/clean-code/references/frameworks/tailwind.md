# Tailwind CSS

> Applies to: Tailwind CSS v4 (CSS-first configuration, `@theme`, `@import "tailwindcss"`, automatic content detection, Lightning CSS under the hood); v3 notes in Structure. Language pack: `languages/css.md`. Read with: the project's UI framework pack (`react.md`, `vue-nuxt.md`, `svelte.md`), if any.

## Structure

- `src/styles/app.css` (or the project's existing entry point) — one CSS entry: `@import "tailwindcss";`, then the `@theme` token block, then any hand-written base styles.
- No `tailwind.config.js` by default — v4 configures through CSS; add one only behind `@config` for a plugin that still requires it.
- `src/components/` — components that wrap a repeated utility string once, instead of repeating the string or reaching for `@apply`.
- A theme or token stylesheet (`theme.css`, `tokens.css`) — the `@theme` block, or `@import`ed before component styles, when the project splits it out.
- v3 project: keep `tailwind.config.js` (`content`, `theme.extend`, `darkMode`) and the three `@tailwind` directives; every Rule applies except those naming v4-only features (`@theme`, `@custom-variant`, `@source`).

## Roles

```clean-roles
role theme = **/theme.css, **/tokens.css, **/*.theme.css
ignore-name = ^cn$
```

## Rules

- Never build a class name by concatenating or interpolating a partial utility prefix, as in `` `bg-${color}-500` ``; Tailwind's build scans source text for complete tokens, so a class assembled at runtime never ships (G16).
- Map a variant to its full, literal class list with an object or `switch`; only the lookup's result is dynamic, never the class string itself:

```ts
const SIZE = { sm: "px-2 py-1 text-xs", lg: "px-4 py-2 text-base" };
```

- Extract a class string repeated across more than a couple of call sites into a real framework component, not `@apply`; `@apply` works but re-adds the specificity and build-order problem utilities exist to avoid (G5).
- Put every design token — color, spacing, radius, font — in `@theme`; reserve an arbitrary value (`top-[117px]`) for a one-off that will never recur (G25).
- Merge conditional classes with `clsx` (or the project's equivalent) for readability, and `tailwind-merge` wherever two conditional utilities can target the same CSS property, so the last one wins deliberately instead of by accidental cascade order (G3).
- Sort classes with `prettier-plugin-tailwindcss`; never hand-order a long `className` string.
- Let automatic content detection find templates; reach for an explicit `@source` only for a path it cannot see — outside the project root, or `.gitignore`d.
- Configure class-based dark mode with `@custom-variant dark (&:where(.dark, .dark *));` in the CSS entry point rather than reaching for a removed `darkMode` config key; v4's default with no configuration is `prefers-color-scheme`.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Utility classes and `@theme` tokens are the delivery layer's detail; a component decides which classes to render from state the application layer already computed, never the reverse.
- Keep no business rule inside a `class`/`className` conditional beyond selecting an already-decided variant; a discount threshold or a permission check belongs in the layer that owns it, exposed to the component as a plain prop.
- Layer globs come from the UI framework's pack; Tailwind adds none.

## Tests

- Snapshot or visual-regression test a component's rendered output when a design token changes, the same as any other UI pack; Tailwind adds no test primitive.
- Add a lint step that fails on a template-literal-built class name — a Tailwind-aware ESLint plugin's unknown-classname rule, or a project regex check — so the smell is caught before review.

## Enforce

- A Tailwind-aware ESLint plugin for class validity and consistent ordering, as a backstop to `prettier-plugin-tailwindcss`; confirm its Tailwind v4 support before adopting one.
- `languages/css.md`'s Stylelint config still applies to any hand-written CSS beside the generated utilities.
- `prettier-plugin-tailwindcss` in the Prettier config so class order never bikesheds a review.

## Smells

- A class name built from a template literal or string concatenation that only a browser's runtime, never Tailwind's scanner, would see (G16).
- The same long utility string copy-pasted across several components instead of extracted into one (G5).
- `@apply` used for nearly every rule in a stylesheet, rebuilding the component-class system utilities exist to replace (G24).
- Arbitrary values (`top-[13px]`, `text-[#3457d5]`) standing in for what should be a `@theme` token (G25).
- A conditional `className` string built by hand where two utilities can collide, instead of resolved with `tailwind-merge` (G3).
