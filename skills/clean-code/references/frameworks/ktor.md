# Ktor

> Applies to: Ktor 3.x. Language pack: languages/kotlin.md. Read with: nothing.

## Structure

- `Application.kt` — the composition root: `fun main()` starts the engine, `fun Application.module()` installs plugins and routing.
- `plugins/` — one file per installed plugin or plugin group, each a `fun Application.configure<Thing>()`.
- `routes/` (or `routing/`) — one file per resource, each a `fun Route.<thing>Routes()` mounted from the routing plugin.
- `services/` — business logic routes call into; no `ApplicationCall`, `Route`, or other Ktor type appears here.
- `repositories/` — database or external-API access behind an interface the services depend on.
- `models/` (or `dto/`) — `@Serializable` data classes for requests, responses, and persistence.

## Roles

```clean-roles
role route = **/routes/**, **/routing/**
signal route [kt] = fun\s+Route\.\w+\(
role plugin-config = **/plugins/**
signal plugin-config [kt] = fun\s+Application\.configure\w*\(
signal application [kt] = fun\s+Application\.module\(
```

## Rules

- Install `StatusPages` once, and translate exceptions or status codes to responses there — not with scattered `try/catch` inside routes (G4, Special Case pattern).
- Install `RequestValidation` with one `validate<T> { }` block per request type, and let `StatusPages` catch the `RequestValidationException`; a route handler should never see an invalid body (G3).
- Keep a route function thin: parse the request, call one service method, respond; persistence and business rules belong in the service, not the route lambda (G17, G30).
- Name each route function an extension on `Route` for its feature (`fun Route.orderRoutes()`).
- Wrap blocking JDBC or file calls in `withContext(Dispatchers.IO) { }`; the engine's dispatcher is for suspending, non-blocking work only.
- Give routes their services through Ktor's DI plugin (`io.ktor:ktor-server-di`) or another DI library, instead of a file-scoped singleton tests cannot replace.
- Read configuration through `Application.environment.config`; never read `System.getenv` from business code (G35).
- Serialize with `@Serializable` data classes registered through `ContentNegotiation`; never hand-build a JSON string.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Business rules — services, domain types — never import `io.ktor.server.*` or `ApplicationCall`; a route maps a request to a plain call, the plain result back to a response.
- Declare repository interfaces beside the services using them; implement them in an adapter module or package depending inward, never the reverse.
- Compose plugins, routing, and DI wiring in `Application.module()` and `plugins/`; that pairing is this framework's composition root.

```clean-architecture
layer domain   = **/services/**, **/models/**
layer adapters = **/routes/**, **/routing/**, **/repositories/**
layer main     = **/plugins/**, **/Application.kt
```

## Tests

- Use `testApplication { }` from `ktor-server-test-host`; it runs the plugin pipeline without opening a socket.
- Test a route through its HTTP contract — status code, body — with the test client; test a service's business rules as plain unit tests with no Ktor type involved.
- Override a dependency for a test through the DI plugin's test support or constructor injection, never by mutating global state.

## Enforce

- detekt (see the Kotlin pack) plus Konsist rules asserting routes never import a repository and services never import `ApplicationCall`.
- `RequestValidation` and `StatusPages` each installed exactly once, in `plugins/`, never per route.

## Smells

- A route lambda that queries a database or reaches into another service's internals (G17, G14).
- `try/catch` wrapping business logic inside a route instead of one `StatusPages` mapping (G4, G13).
- A service constructed inside a route file instead of provided from outside (G13).
- A blocking call left on the default dispatcher, stalling every other request sharing it (G6).
