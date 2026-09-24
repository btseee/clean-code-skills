# JavaScript

> Applies to: ECMAScript 2023+ on current Node.js LTS and evergreen browsers. Formatter: Prettier or Biome. Linter: ESLint 10 (`eslint.config.js` flat config only) or Biome. Read with: the framework pack, if any.

## Names

- Use camelCase for values and functions, PascalCase for classes and components, UPPER_SNAKE only for constants shared across modules (N3).
- Name booleans as questions (`isPaid`, `hasItems`) and functions by what they do or return (`loadOrders`, `totalPrice`) (G20).
- Never encode types or scope in names (`strName`, `arrItems`, `_self`) (N6).
- Name a file after the one thing it exports, in project casing convention — never two conventions in one folder (G11).
- Never write a vague name (`data`, `info`, `obj`, `temp`), a bare-verb function with no object (`handle`, `process`), or a numbered, versioned, or noise-word class (`user2`, `Manager`, `ProcessOrder`); a loop index or callback parameter may stay short (N1, N4, N5, G17).

## Functions And Types

- Keep functions small, one abstraction level; extract a named function instead of commenting a block (G30, G34).
- Take at most two or three positional parameters; beyond that, one destructured options object (F1).
- Never switch behavior with a boolean parameter; write two functions (F3).
- Use `const` by default, `let` only for reassignment, never `var`.
- Never mutate arguments; prefer `map`, `filter`, spread, `toSorted`, `toSpliced`, `with` (F2).
- Use `===`/`!==` only, `??`/`?.` where `0` and `""` are valid values (G26).
- Give magic numbers and strings a name (G25).
- Describe cross-module data shapes with JSDoc `@typedef`, or move the module to TypeScript.

## Errors

- Throw `Error` subclasses, never strings or plain objects; chain the cause: `throw new PaymentError("charge failed", { cause: error })`.
- Never leave a promise floating: await it, return it, or hand it to a handler. Never write an empty `catch` (G4).
- Catch only where a decision can be made; otherwise let it travel up.
- Return expected outcomes as values (`{ ok: false, reason: "card declined" }`); keep exceptions for genuine failures (Special Case pattern).
- Cancel with `AbortController` and pass its `signal` through every call that can wait.

## Modules And Visibility

- Write ES modules (`import`/`export`, `"type": "module"`); never mix `require` into new code (G1).
- Prefer named exports; use a default export only where a framework demands one.
- Export only what another module uses; everything else stays module-private (G8).
- Avoid barrel files re-exporting whole folders — they hide cycles, load unwanted code; import from the owning module (G22).
- Never keep mutable state at module level; pass collaborators in (G18).

## Placement

- Keep sources under project root (`src/`), one module per concept, named for the concept, not its technical type.
- Keep entry points (`server.js`, CLI's `bin/`) thin: read configuration, compose, start.
- Put tests beside their module (`order.test.js`) or under `test/` mirroring `src/` — whichever project already does.
- Never add to `utils.js` or `helpers.js`; name the concept (`money.js`, `business-days.js`) (G17).

## Tests

- Use project's runner — Vitest, Jest, or `node:test`. Keep tests deterministic: fake timers or injected clock, no real network (F.I.R.S.T.).
- Name tests for behavior (`rejects an empty cart`) and assert outcomes, never internals.
- Await every asynchronous assertion; a missing `await` makes a test pass forever.
- Test boundary values, add tests around recent bugs (T5, T6).

## Concurrency

- Never block the event loop with synchronous I/O or long computation; use async API or a worker thread.
- Start independent operations with `Promise.all` or `Promise.allSettled`, not one `await` at a time in a loop.
- Treat every `await` as a point where other code runs: re-check shared state after it (G31).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Business rules are plain modules: no imports of Express, database drivers, `fetch`, or `process.env` (the Dependency Rule).
- Declare a port as an object shape the inner layer documents (JSDoc `@typedef`); adapters implement it.
- Compose the object graph in the entry module, pass it down; policy never imports an adapter.

```clean-architecture
layer domain      = src/domain/**
layer application = src/application/**
layer adapters    = src/adapters/**
layer main        = src/main.js
```

## Enforce

- ESLint core rules: `complexity`, `max-lines-per-function`, `max-params`, `max-depth`, `no-unused-vars`, `eqeqeq`, `no-var`, `prefer-const`.
- `import/no-cycle` (eslint-plugin-import) or dependency-cruiser `no-circular` for cycles; dependency-cruiser `forbidden` rules or eslint-plugin-boundaries for declared layers.
- Biome's matching rules where project lints with Biome.

## Smells

- Callback pyramids and `.then` chains that drop rejections (G16, G4).
- Truthiness bugs with `0`, `""`, and `NaN` (G26).
- Functions that mutate their arguments (F2).
- A `utils.js` collecting unrelated helpers (G17).
- Barrels that re-export everything and hide cycles (G22).
- Built-in prototypes extended by the application (G18).
- `console.log` left on production paths (G12).
