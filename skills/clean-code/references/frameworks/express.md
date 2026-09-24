# Express

> Applies to: Express 5. Language pack: `javascript.md` or `typescript.md`. Read with: nothing.

## Structure

- `app.js` (or `src/app.js`) — builds the Express app, mounts middleware and routers; never calls `listen()`.
- `server.js` (or `bin/www`) — imports the app and calls `listen()`; the process's only entry point.
- `src/routes/` — one router per resource; wires paths and HTTP verbs to controllers, nothing else.
- `src/controllers/` — reads `req`, calls a service, shapes the response; no business rules.
- `src/services/` — business rules and orchestration; never imports `express` or reads `req`/`res`.
- `src/middleware/` — cross-cutting request handling: authentication, validation, rate limiting, logging.
- `src/models/` or `src/repositories/` — the only layer that queries the database.
- `src/config/` — environment values and third-party client setup, read once at startup.
- Error-handling middleware (four parameters) is registered last, after every route and router.

## Roles

```clean-roles
signal middleware [js, ts, mjs, cjs] = \(\s*(?:err|error)\b[^)]*,\s*(?:req|request)\b[^)]*,\s*(?:res|response)\b[^)]*,\s*next\b
signal middleware [js, ts, mjs, cjs] = \(\s*(?:req|request)\b[^)]*,\s*(?:res|response)\b[^)]*,\s*next\b
# Express 4 controllers and route handlers take `next` too; there it is not misplaced.
allow controller = middleware
allow route = middleware
```

## Rules

- Never pass `req` or `res` into a service; pull out the plain values a service needs before calling it (the Dependency Rule).
- Validate and sanitize input in middleware or at the top of the controller; a service trusts the shape of what it receives.
- Register exactly one central error-handling middleware, mounted last with all four parameters `(err, req, res, next)`, and let thrown errors and `next(err)` calls reach it.
- Never put a stack trace or a raw error message in a response body; log the error and answer with a safe message and status code.
- Async route handlers and middleware that throw or return a rejected promise reach `next(err)` on their own in Express 5; do not wrap every handler in `try/catch` or a helper like `express-async-handler` just to forward errors.
- Give each resource its own router file instead of one flat file of `app.get`/`app.post` calls.
- Write new wildcard and optional-segment routes in Express 5's path-to-regexp v8 syntax (`/*splat`, `/:file{.:ext}`); the Express 4 forms no longer match the same thing (G3).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- `express`, `req`, `res`, and any ORM or driver type stop at the controller; services and models never import them (the Dependency Rule).
- Declare a repository interface beside the service that needs it; the module under `models/` or `repositories/` implements it, chosen in `app.js`.
- Compose the app, its routers, and every dependency in `app.js`/`server.js`; no other module builds the object graph.

```clean-architecture
layer domain      = src/domain/**
layer application = src/services/**
layer adapters    = src/models/**, src/repositories/**
layer delivery    = src/controllers/**, src/routes/**, src/middleware/**
layer main        = src/app.*, src/server.*, src/config/**
```

## Tests

- Test services as plain functions with no HTTP layer involved.
- Test routes with `supertest` against the exported `app`, without a real listening socket.
- Mock outbound HTTP calls and the database at the boundary the service depends on, not inside the service itself.
- Cover the error middleware directly: a thrown error from a route must produce the documented status and body (T5).

## Enforce

- dependency-cruiser `forbidden` rules: `src/services/** -> express` and `src/services/** -> src/controllers/**`, both disallowed.
- `helmet` for HTTP security headers, configured once in `app.js`, not reimplemented per route.
- `express.json()`/`express.urlencoded()` size limits set explicitly; Express 5 now defaults `extended` to `false`.

## Smells

- A route callback that parses input, applies a business rule, and queries the database inline (G30).
- A service that imports `express` or reads `req.body` directly (G17, the Dependency Rule).
- An empty `catch` inside a route that swallows an error instead of forwarding it to the central handler (G4).
- A route still written with Express 4's bare wildcard or bracket syntax after an upgrade, silently matching the wrong paths (G3).
