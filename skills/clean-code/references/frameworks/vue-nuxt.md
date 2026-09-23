# Vue And Nuxt

> Applies to: Vue 3.5+ Composition API, Nuxt 3 and 4. Language pack: `typescript.md` or `javascript.md`. Read with: nothing.

## Structure

- `components/` — presentational `.vue` files, `<script setup>` by default.
- `composables/` — shared reactive logic: a `useThing()` function returning refs and computed values.
- `stores/` — Pinia stores, one per domain concept, named `useThingStore`.
- `pages/` — file-based routes (Vue Router, or Nuxt's own router).
- `layouts/`, `middleware/`, `plugins/` — Nuxt's shared page shells, navigation guards, and app-wide setup.
- `server/api/**`, `server/routes/**` — Nuxt (Nitro) server endpoints; `server/middleware/**` — server request hooks.
- Nuxt 4 moves everything above except `server/`, `public/`, and `nuxt.config.ts` under `app/`; `~` resolves to `app/`.

## Roles

```clean-roles
role store = **/stores/**
name store [ts, js, vue] = ^use\w+Store$
role composable = **/composables/**
name composable [ts, js, vue] = ^use[A-Z]
role page = **/pages/**
role layout = **/layouts/**
role middleware = **/middleware/**
role server-route = server/api/**, server/routes/**
role server-middleware = server/middleware/**
role plugin = **/plugins/**
```

## Rules

- Write `<script setup>` with `defineProps`, `defineEmits`, and `defineModel`; do not add Options API code to a new component.
- Never mutate a prop; treat it as read-only and emit an event, or use `defineModel` for two-way binding (F2).
- Compute derived values with `computed`; reach for `watch` or `watchEffect` only to synchronize with something outside Vue's reactivity — a subscription, the DOM, a timer (G31).
- Extract logic two components both need into a composable named `use<Thing>` that returns refs or computed values, never a plain mutable object (G5, G17).
- Keep templates free of business logic: a template calls a computed property or a method, it does not compute one inline (G6).
- Fetch through Nuxt's `useFetch`/`useAsyncData`, or a query library in plain Vue; never call `fetch` directly inside `<script setup>`.
- Key `v-for` by a stable id, never the array index, when the list can reorder (G3).
- Give each Pinia store one domain concept and the name `use<Thing>Store`; do not grow one store into a global bucket (G17).
- Keep route middleware and plugins thin: redirect or inject, never decide a business rule (G17).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Components, pages, and layouts are the delivery layer; composables adapt reactivity to the domain, they do not decide it.
- Business rules are plain TypeScript modules with no `vue`, `#app`, or `nuxt` import; composables and stores call them.
- `server/api/**` implements interfaces the application layer declares; Nitro/H3 request and response types never cross into domain modules.

```clean-architecture
layer domain         = **/domain/**
layer application    = **/application/**
layer infrastructure = server/**
layer ui             = **/components/**, **/pages/**, **/layouts/**, **/composables/**
```

## Tests

- Test components with Vue Testing Library or `@vue/test-utils`, asserting on rendered output, not internal refs.
- Call a composable inside a minimal host component (or a `withSetup` test helper); test the business rule it delegates to as a plain function, unrendered.
- Mock network calls at the boundary (MSW) rather than mocking `useFetch` internals.
- Reserve `@nuxt/test-utils` for tests that truly need the Nuxt runtime; keep ordinary unit tests plain and fast.

## Enforce

- `eslint-plugin-vue` (`vue/recommended` or its flat-config equivalent).
- `@nuxt/eslint`, Nuxt's own flat-config module, for Nuxt-specific rules and generated import globals.
- dependency-cruiser or eslint-plugin-boundaries for declared layers.

## Smells

- A prop reassigned inside the child instead of emitted or bound with `defineModel` (F2, G17).
- A `watch` recomputing a value that `computed` should own (G5, G31).
- Business logic written directly inside a `<template>` expression (G6).
- A composable returning a plain mutable object instead of refs or computed, so callers lose reactivity (G26).
- `server/api/**` importing a Vue component or a `#app` runtime symbol (wrong-direction dependency, G17).
- Two components each holding their own copy of the same computation instead of one shared composable (G5) — the duplication this pack exists to prevent.
