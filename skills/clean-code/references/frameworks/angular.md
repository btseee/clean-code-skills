# Angular

> Applies to: Angular 20, 21, and 22. Language pack: `typescript.md`. Read with: nothing.

## Structure

- `src/app/<feature>/` — a feature's components, services, guards, and routes, colocated (Angular's flat layout, not a type-based tree).
- `src/app/core/` — singleton services, guards, and interceptors provided once, at the root.
- `src/app/shared/` — presentational components, directives, and pipes reused by several features — not a dumping ground for unrelated helpers (G17).
- `src/main.ts` — the composition root: `bootstrapApplication`, providers, and nothing else.
- `src/app/app.routes.ts` — the root `Routes` array; features lazy-load with `loadComponent`/`loadChildren`.

## Roles

```clean-roles
role component = **/*.component.ts
role directive = **/*.directive.ts
role pipe = **/*.pipe.ts
role guard = **/*.guard.ts
role interceptor = **/*.interceptor.ts
role resolver = **/*.resolver.ts
signal component [ts] = @Component\(
signal directive [ts] = @Directive\(
signal pipe [ts] = @Pipe\(
signal guard [ts] = CanActivateFn|implements\s+CanActivate
signal interceptor [ts] = HttpInterceptorFn|implements\s+HttpInterceptor
signal resolver [ts] = ResolveFn
signal service [ts] = @Injectable\(|@Service\(
```

## Rules

- Write standalone components, directives, and pipes; `standalone: true` is the default since v19, and a new `NgModule`-based one needs `standalone: false` stated explicitly.
- Since v20, `ng generate` no longer appends `Component`/`Service`/`Directive`/`Pipe` to new names by default; name for the concept (`Orders`, not `OrdersService`) unless the project's `angular.json` still requests suffixes — match whichever this project already does (G11).
- Prefer functional guards, interceptors, and resolvers (`CanActivateFn`, `HttpInterceptorFn`, `ResolveFn`) over class-based ones; they need no `@Injectable()` ceremony for a single decision.
- Hold state in `signal()`, derive it with `computed()`, and accept it through `input()`/`model()`; never derive a value into a second signal that `computed()` should own (G5).
- Write every component to work without Zone.js and under `OnPush` — new apps are zoneless since v21, and `OnPush` is the default strategy since v22: change state through signals and inputs, never by mutating an object in place and waiting for the view to notice.
- Use `effect()` only to synchronize with something outside Angular's reactivity; a template or a computed signal answers most other needs (G31).
- Never subscribe inside a `subscribe` callback; compose with `switchMap`, `mergeMap`, or `toSignal` instead (G30, G31).
- Keep templates free of method calls that carry business logic; bind to a signal or a getter that calls the one function that owns the rule (G6).
- Inject collaborators with `inject()` or the constructor, never `new` a service directly (DIP).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Components, directives, and pipes are the delivery layer: they render and adapt, they do not decide.
- Business rules are plain TypeScript classes or functions with no `@angular/*` import; declare a repository interface there and implement it in a service that injects `HttpClient`.
- Guards, interceptors, and resolvers depend on the application layer's interfaces, never the reverse.

```clean-architecture
layer domain         = src/app/domain/**
layer application    = src/app/application/**
layer infrastructure = src/app/infrastructure/**, src/app/**/*.service.ts, src/app/**/*.interceptor.ts
layer ui             = src/app/**
layer main           = src/main.ts
```

## Tests

- New projects get Vitest (`@angular/build:unit-test`) since v21, while older ones may still run Karma; check which one this project runs before assuming either.
- Test a component through `TestBed` and its rendered template or public API, never a private method.
- Test an injected service by providing a fake for its own dependencies (`HttpClient`, a repository), not the real network.
- Test a business rule as a plain function or class, with no `TestBed` needed.

## Enforce

- angular-eslint with its recommended config.
- `angularCompilerOptions.strictTemplates: true` in `tsconfig.json` (the default since v22); never turn it off to silence a template error.
- Nx `@nx/enforce-module-boundaries` where the project is an Nx monorepo.

## Smells

- A `.subscribe()` call nested inside another `.subscribe()` callback instead of a piped operator (G30, G31).
- A computed value copied into a `signal` and kept in sync by hand instead of `computed()` (G5).
- A template expression calling a method that fetches or mutates instead of reading a signal (G6, N7).
- A `shared/` folder accumulating components, pipes, and services with nothing in common (G17).
- A class-based guard or interceptor added for a single, stateless check that a functional one would express in three lines (G32).
- A component injecting `HttpClient` directly instead of an injectable service the component only calls (G17).
