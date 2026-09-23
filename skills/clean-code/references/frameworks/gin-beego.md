# Gin And Beego

> Applies to: Gin 1.12.x and Beego 2.3.x. Language pack: languages/go.md. Read with: nothing.

## Structure

- `internal/handler/` or `internal/handlers/` (Gin) — one file per resource; each function takes `*gin.Context`, does no business logic itself.
- `internal/middleware/` (Gin) — cross-cutting request concerns as `gin.HandlerFunc` factories, registered with `r.Use(...)`.
- `internal/router/` or `internal/routers/` — route tables: method, path, and handler or controller wired together; no logic beyond wiring.
- `controllers/` (Beego) — structs embedding `web.Controller`, one action method per route (`Get`, `Post`, `GetUser`, ...).
- `models/` — domain and persistence types, shared by both stacks.
- `service/`, `repository/` — business rules and data access; framework-agnostic on both stacks.
- `cmd/<app>/main.go` (Gin) or the `routers` package's `init` (Beego) — composition root: builds the engine or route table, starts the server.

## Roles

```clean-roles
role handler = **/handler/**, **/handlers/**
signal controller [go] = (?:web|beego)\.Controller
signal middleware [go] = \)\s*gin\.HandlerFunc
signal handler [go] = \(\s*\w+\s+\*gin\.Context\s*\)
role route = **/routers/**, **/router/**
```

## Rules

- Never pass `*gin.Context` or `*web.Controller` into a service or repository function; extract the data the call needs and pass that instead (G17, DIP).
- Propagate `c.Request.Context()` into every downstream call so cancellation and deadlines carry through; never build a fresh `context.Background()` inside a handler.
- Register middleware with `r.Use(...)` at the engine or group level; a handler never calls another handler's logic directly (G14).
- Make a middleware's decision explicit: `c.Next()` to continue, `c.Abort()` or `c.AbortWithStatusJSON(...)` to stop; let `gin.Recovery()`, not a bare panic, handle the unexpected.
- Bind and validate input with `c.ShouldBindJSON`/`ShouldBind`, and check the error before touching any bound field (G3).
- Beego: keep `Prepare()` for setup shared by every action on the controller; put the action's own decision in the action method (G31).
- Beego: respond through `this.Data["json"]` plus `this.ServeJSON()`, never by writing to the underlying `http.ResponseWriter` directly.
- Never dispatch routes with a hand-written switch on the path; register them on the framework's own router (`r.GET`, `web.Router`).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- `*gin.Context`, `*web.Controller`, and any `net/http` type stop at the handler or controller; none of them appear in a service, repository, or domain signature.
- Declare a repository or external-service port as an interface beside the service that consumes it; the adapter package implements it.
- `cmd/<app>/main.go` (Gin) or the `routers` package (Beego) is the only place that constructs a concrete adapter and wires it in.

```clean-architecture
layer domain      = internal/domain/**, internal/models/**
layer application = internal/service/**
layer adapters    = internal/handler/**, internal/middleware/**, controllers/**, internal/repository/**
layer main        = cmd/**, internal/router/**, routers/**
```

## Tests

- Test handlers and controllers with `net/http/httptest`: build a request against the engine or controller, assert on the recorded response, not on internals.
- Test a middleware by its effect on the response or the request context, not by asserting it was merely called.
- Keep service and repository tests free of `gin`/`beego` imports; they take and return plain types.

## Enforce

- golangci-lint's `contextcheck`: flags a context built fresh instead of taken from the incoming request.
- golangci-lint's `bodyclose`: flags an HTTP client response body a handler or service forgets to close.
- `go vet ./...` for mistagged struct fields on a bound or ORM-mapped type.

## Smells

- A service function taking `*gin.Context` or `*web.Controller` just to reach a query parameter itself (G17, G14).
- Business rules written inline in a handler closure or a Beego action method (G6, G30).
- A middleware that derives a new `context.Context` but never calls `c.Request = c.Request.WithContext(...)`, so downstream code never sees it (G31).
- A failed bind answered with `c.JSON(200, ...)` instead of surfacing the bind error (G4).
- A route table that also validates or transforms the request body (G17).
