# Next.js

> Applies to: Next.js 15 and 16, App Router. Language pack: `typescript.md` or `javascript.md`. Read with: `react.md`.

## Structure

- `app/**/page.tsx` — a route's UI; the segment's URL comes from the folder path.
- `app/**/layout.tsx` — the shared shell wrapping a segment and its children.
- `app/**/loading.tsx`, `app/**/error.tsx`, `app/**/not-found.tsx` — the framework's Suspense and error boundaries for a segment.
- `app/**/route.ts` — a Route Handler: HTTP methods for a URL that returns no UI.
- `**/actions/**` or `*.actions.ts` — Server Actions (`'use server'`), called directly from components.
- `lib/` or `src/lib/` — plain business and data modules shared by pages, layouts, and route handlers; no JSX, no route-only exports.
- `middleware.ts` (15) / `proxy.ts` (16), at the project root or under `src/` — the single request boundary, run before routing.
- A module guarded by `import "server-only"` — never reaches the client bundle, even by accident.

## Roles

```clean-roles
role component = app/**/page.*, app/**/layout.*, app/**/template.*, app/**/loading.*, app/**/error.*, app/**/not-found.*
role component = src/app/**/page.*, src/app/**/layout.*, src/app/**/template.*, src/app/**/loading.*, src/app/**/error.*, src/app/**/not-found.*
role endpoint = app/**/route.*, src/app/**/route.*
role middleware = middleware.*, src/middleware.*, proxy.*, src/proxy.*
role server-action = **/actions/**, **/*.actions.*
entry app/**/sitemap.*, app/**/robots.*, app/**/manifest.*, app/**/icon.*, app/**/apple-icon.*, app/**/opengraph-image.*, app/**/twitter-image.*, app/**/global-error.*, app/**/default.*
entry src/app/**/sitemap.*, src/app/**/robots.*, src/app/**/manifest.*, src/app/**/icon.*, src/app/**/apple-icon.*, src/app/**/opengraph-image.*, src/app/**/twitter-image.*, src/app/**/global-error.*, src/app/**/default.*
entry instrumentation.*, **/instrumentation.*
ignore-name = ^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|default|generateMetadata|generateStaticParams|metadata|revalidate|dynamic|runtime|config)$
```

## Rules

- Keep Server Components the default; add `'use client'` only to the leaf that needs state or browser APIs, never to a whole route tree (G17, G8).
- Put the business rule in a plain module under `lib/`, not inside `page.tsx` or `route.ts`; a page and its matching API route both call it, neither redefines it (G5).
- Never read a secret through `NEXT_PUBLIC_*`; that prefix is inlined into the client bundle verbatim. Use a server-only environment variable and guard the module with `import "server-only"`.
- Never assume a `fetch` is cached: since 15 it is not, by default. Opt in around the one function or component that is safe to share — `{ cache: "force-cache" }` or `next: { revalidate }` on 15, `"use cache"` with `cacheComponents` enabled on 16.
- Rename `middleware.ts` to `proxy.ts` and its exported function to `proxy` on 16; `middleware.ts` still works there only for Edge-runtime cases, and is deprecated.
- Keep proxy/middleware a boundary check — auth, redirects, headers — never a business decision; it runs before every matched request (G17).
- A Server Action validates its own input; never trust a client-submitted value as already checked, even one the same team wrote.
- `next lint` is removed in 16 (deprecated since 15.5): run ESLint or Biome directly from the project's own script and CI step.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- `app/**` (pages, layouts, route handlers) and `proxy.ts`/`middleware.ts` are the delivery layer: they adapt, they do not decide.
- Business rules are plain modules with no `next/*` or React import; declare a repository or gateway interface there, implement it in `lib/`.
- Route Handlers and Server Actions call the application layer; they never embed the rule they are exposing.

```clean-architecture
layer domain         = src/domain/**
layer application    = src/application/**
layer infrastructure = src/lib/**, src/server/**
layer ui             = app/**, src/app/**
```

## Tests

- Test a Server Action or a `lib/` business function as a plain async function; it needs no request or render.
- Reserve Testing Library and Playwright for behavior that needs the DOM or a real navigation through `proxy.ts`.
- Mock the network at the boundary (MSW) for Client Components rather than mocking a hook or module.
- Use the project's runner (Vitest or Jest) for units; keep route-handler tests calling the exported `GET`/`POST` function directly where the runner allows it.

## Enforce

- `eslint-config-next` (`next/core-web-vitals`) through the ESLint CLI; on 16 neither `next lint` nor `next build` lints for you.
- `eslint-plugin-react-hooks` and `eslint-plugin-jsx-a11y`, as in `react.md`.
- dependency-cruiser or eslint-plugin-boundaries to stop `app/**` importing a domain module's internals instead of its declared interface.

## Smells

- `'use client'` on a file that does no interactive work, dragging its whole subtree to the client (G8, G17).
- A secret read through `process.env.NEXT_PUBLIC_*` (leaks to the browser).
- The same rule computed inline in both a page and its API route instead of one shared module (G5).
- `middleware.ts`/`proxy.ts` making an authorization decision with business meaning instead of a cheap boundary check (G17).
- A `"use cache"` boundary drawn around a whole page instead of the one function or component that is safe to share (G6).
- Data fetched inside a Client Component effect instead of a Server Component or a query library (G31).
