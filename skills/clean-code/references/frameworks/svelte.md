# Svelte

> Applies to: Svelte 5 runes, SvelteKit 2. Language pack: `typescript.md` or `javascript.md`. Read with: nothing.

## Structure

- `src/routes/` — SvelteKit's file-based router: `+page.svelte`, `+page.ts`/`+page.server.ts`, `+layout.svelte`, `+layout.ts`/`+layout.server.ts`, `+error.svelte`.
- `src/lib/components/` — shared presentational components (also reachable as `**/components/**`).
- `src/lib/server/` — server-only modules: database clients, secrets; importable only from server-side code.
- `src/hooks.server.ts`, `src/hooks.client.ts` — the app's single request and navigation hook, run before every matched request.
- A `.svelte.ts` file — shared reactive state built from runes, outside any one component.

## Roles

```clean-roles
role page = **/+page.svelte
role load = **/+page.ts, **/+page.js, **/+page.server.ts, **/+page.server.js, **/+layout.ts, **/+layout.js, **/+layout.server.ts, **/+layout.server.js
role endpoint = **/+server.ts, **/+server.js
role app-hook = src/hooks.*
role store = **/stores/**, **/*.svelte.ts, **/*.svelte.js
ignore-name = ^(load|actions|GET|POST|PUT|PATCH|DELETE|handle|handleError|handleFetch|prerender|ssr|csr|trailingSlash|entries)$
```

## Rules

- Use runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`) as the default reactivity model; do not mix in Svelte 4's `$:` reactive statements in the same component (G11).
- Fetch and load data in a `load` function (`+page.ts`, `+page.server.ts`, `+layout.ts`, `+layout.server.ts`), not in a component's script block; the component receives `data` as a prop.
- Keep secrets and server-only calls behind `src/lib/server`, importable only from `+page.server.ts`, `+server.ts`, or another server module; `$env/static/private` is restricted the same way.
- Use `+server.ts` for a non-page HTTP endpoint (`GET`, `POST`, and so on as named exports); keep each handler thin, delegating the rule to a plain module.
- Keep `hooks.server.ts`'s `handle` a boundary check — auth, headers, `event.locals` — never a place to compute a business rule (G17).
- Derive values with `$derived`; reach for `$effect` only to synchronize with something outside Svelte — the DOM, a subscription, a timer (G31).
- Share reactive state across modules through a `.svelte.ts` file exporting runes-based state, never a plain exported `let` (G18).
- Make a two-way binding explicit with `$bindable()`; never mutate a prop silently and hope the parent notices (F2).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Components, `load` functions, and `+server.ts` endpoints are the delivery layer: they call the application layer, they do not decide.
- Business rules are plain modules, commonly under `src/lib/domain/`, with no `$app`, `$env`, or `svelte` import.
- `src/lib/server/` holds the adapters: they implement interfaces the domain or application layer declares, beside the code that calls the database or external API.

```clean-architecture
layer domain         = src/lib/domain/**
layer application    = src/lib/application/**
layer infrastructure = src/lib/server/**
layer ui             = src/routes/**, src/lib/components/**
```

## Tests

- Test components with `@testing-library/svelte`, asserting on rendered output, not internal rune state.
- Unit-test a `load` function by calling it directly with a fabricated event object; it is a plain (often async) function.
- Run `svelte-check` as a test step: a type or template error is a failing test, the same as a failing unit test.
- Mock network calls at the boundary (MSW) rather than stubbing `fetch` ad hoc in each test.

## Enforce

- `eslint-plugin-svelte` with its flat-config recommended preset.
- `svelte-check` in CI, for the `.svelte` template checking `tsc` alone does not cover.
- dependency-cruiser or eslint-plugin-boundaries for declared layers.

## Smells

- A component's script block calling `fetch` directly instead of a `load` function (G17) — the case this pack exists to prevent.
- A database client or `$env/static/private` import reachable from a file the client bundle also imports (secret leak).
- `hooks.server.ts` making a business decision instead of an auth or boundary check (G17).
- Svelte 4 `$:` statements mixed into an otherwise runes-mode component (G11).
- A `.svelte.ts` store exporting a mutable `let` instead of encapsulated runes state (G18).
- A `+server.ts` handler holding the rule itself instead of calling the shared module that owns it (G5).
