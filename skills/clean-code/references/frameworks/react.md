# React

> Applies to: React 19, with React Compiler 1.0 where the project enables it. Language pack: `typescript.md` or `javascript.md`. Read with: the meta-framework's pack (`nextjs.md`), if any.

## Structure

- `src/features/<feature>/` — one feature's components, hooks, and API calls, together.
- `src/components/` — shared presentational components used by several features.
- `src/hooks/` — shared custom hooks (`useDebounce`, `useMediaQuery`).
- `src/api/` or `src/services/` — HTTP clients and data access; no JSX.
- `src/main.tsx` or `src/app/` — providers, router, and composition.
- A component's test, styles, and stories sit beside it when the project co-locates.

## Roles

```clean-roles
role component = **/components/**
role hook = **/hooks/**
role context = **/contexts/**, **/context/**
role api = **/api/**
name hook [ts, tsx, js, jsx] = ^use[A-Z]
name component [tsx, jsx] = ^[A-Z][A-Za-z0-9]*$
ignore-name = ^(App|Root|Layout|Page|Providers|Router)$
```

## Rules

- Keep components pure: the same props and state render the same output, with no side effects during render.
- Follow the Rules of Hooks: call hooks only at the top level of components and custom hooks.
- Keep state as close as possible to where it is used; lift it only when two components need it.
- Never store derived data in state; compute it during render (G5).
- Use effects only to synchronize with systems outside React — subscriptions, the DOM, timers. Respond to events in event handlers, not effects.
- Fetch data outside render effects: through the framework's loaders or server components, or a query library (TanStack Query, SWR) that handles caching, races, and cancellation.
- Extract reusable stateful logic into a custom hook named `use<Thing>`, and repeated markup into a component.
- Key list items by stable data identity, never the array index when order can change.
- With React Compiler on, hand-write `useMemo`, `useCallback`, or `memo` only where profiling shows a need.
- Pass `ref` as an ordinary prop; new code does not need `forwardRef`.
- Keep business rules out of components: a component calls a hook or function that owns the rule (G17).
- Build accessible controls: semantic elements first, labels on inputs, keyboard support for custom widgets.
- Never render HTML from strings with `dangerouslySetInnerHTML` unless it is sanitized.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Components and hooks are the delivery layer: they render and adapt; they do not decide.
- Business rules live in plain modules that import nothing from React.
- API clients implement interfaces the application layer declares; components never call `fetch` directly.
- Providers and the router compose everything, in the outermost layer.

```clean-architecture
layer domain         = src/domain/**
layer application    = src/application/**
layer ui             = src/components/**, src/features/**, src/hooks/**
layer infrastructure = src/api/**
layer main           = src/main.tsx, src/app/**
```

## Tests

- Test behavior through the rendered output with Testing Library: query by role and label, interact with `user-event`, assert what the user sees.
- Mock the network at the boundary with MSW rather than mocking modules.
- Test custom hooks through a component or `renderHook`, and business rules as plain functions without rendering.
- Keep snapshots small and deliberate; a large snapshot asserts nothing anyone reads (T1).

## Enforce

- `eslint-plugin-react-hooks` with its `recommended` preset: `rules-of-hooks`, `exhaustive-deps`, and the compiler-powered rules.
- `eslint-plugin-jsx-a11y` for accessibility, and `eslint-plugin-react` for JSX pitfalls.
- eslint-plugin-boundaries or dependency-cruiser to stop features importing each other's internals.

## Smells

- A component of hundreds of lines that fetches, transforms, and renders (G30).
- An effect that fetches without cancellation, or copies derived values into state (G31).
- State duplicated from props (G5).
- Props drilled through many levels where composition or context fits (G14).
- Index keys on lists that reorder (G3).
- Business rules inside JSX event handlers (G6, G17).
- Hand memoization everywhere while the compiler is on (G12).
