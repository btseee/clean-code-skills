# Laravel

> Applies to: Laravel 11.x-13.x (PHP 8.2+, 8.3+ on 13.x; the slim skeleton introduced in 11 continues through 13). Language pack: `languages/php.md`. Read with: nothing.

## Structure

- `app/Http/Controllers/**` — translates one HTTP request into a call on a service, action, or the message it delegates to; returns a response.
- `app/Http/Middleware/**` — one pipeline step per class; registered in `bootstrap/app.php`'s `withMiddleware()`.
- `app/Http/Requests/**` — Form Requests: `authorize()` and `rules()` for one request shape.
- `app/Http/Resources/**` — shapes a model or collection into a response; no queries.
- `app/Models/**` — Eloquent models: relationships, casts, scopes, query concerns; not business rules.
- `app/Actions/**` — one task, one public entry point, callable from a controller, job, or command.
- `app/Services/**` — orchestration and business rules that span more than one model.
- `app/Jobs/**` — queued work; implements `ShouldQueue`.
- `app/Policies/**` — one authorization decision set per model.
- `app/Events/**`, `app/Listeners/**` — a domain event and its side effects, kept apart.
- `app/Providers/**` — boot/register wiring only; listed in `bootstrap/providers.php`.
- `bootstrap/app.php` — the composition root: middleware, exception handling, routing files.
- `routes/*.php` — path, controller, middleware, and name; no inline logic in a closure.
- `tests/Feature/**`, `tests/Unit/**` — HTTP-level tests and plain-PHP tests.

## Roles

```clean-roles
role request      = app/Http/Requests/**
role resource     = app/Http/Resources/**
role action       = app/Actions/**
role job          = app/Jobs/**
role policy       = app/Policies/**
role event        = app/Events/**
role listener     = app/Listeners/**
role provider     = app/Providers/**
signal request    = extends\s+FormRequest
signal model      = extends\s+Model\b
signal job        = implements\s+ShouldQueue
signal resource   = extends\s+JsonResource
signal provider   = extends\s+ServiceProvider
```

## Rules

- Validate through a Form Request; a controller that reads `$request->all()` straight into `Model::create()` has skipped the one place validation rules should live (G5).
- Keep a controller thin: resolve input via a Form Request, hand off to a service or action, return a response — no query building or business rule inside it (G17).
- Guard mass assignment with `$fillable`; treat `$guarded = []` as no decision at all, not a safe default (G4).
- Authorize with a Policy (or the `#[Authorize]` attribute available since 13.x) — never an inline role string comparison scattered through controllers (G23).
- Register global and route middleware in `bootstrap/app.php`; never wire the framework from inside a controller or model.
- Eager-load a relationship a view or Resource will touch (`with()`, `load()`); never let a template or Resource trigger a lazy load inside a loop.
- Keep a queued job's payload small — plain values or a single model; `SerializesModels` re-fetches by key, so a bloated constructor means a bloated queue.
- Keep Blade free of query calls and authorization decisions; a view renders data a controller or Resource already shaped.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Controllers, Form Requests, Resources, and Middleware are the delivery layer: they translate HTTP; they do not decide.
- Business rules live in services or actions that take plain arguments and return plain results — no `Illuminate\Http\Request` and no Eloquent model in their signatures.
- Eloquent models and query builders are infrastructure; declare a repository interface on the domain side when the project wants to swap persistence, and bind the Eloquent implementation in a provider.
- Wire concrete bindings only in a service provider's `register()`/`boot()`, never inside a domain class.

```clean-architecture
layer domain         = app/Domain/**
layer application    = app/Actions/**, app/Services/**
layer infrastructure = app/Models/**
layer delivery       = app/Http/**
layer main           = app/Providers/**, bootstrap/**
```

## Tests

- Use Pest (with `pestphp/pest-plugin-laravel`) or PHPUnit; feature tests drive routes through the HTTP test client, unit tests exercise services and actions as plain PHP.
- Add a Pest `arch()` test that pins the boundaries this pack states, for example controllers never depending on models directly.
- Build fixtures with model factories, never hand-inserted rows; keep a fresh or transactional database per test so tests stay independent (F.I.R.S.T.).
- Fake queues, mail, events, and the clock (`Queue::fake()`, `Mail::fake()`, `Event::fake()`, `Carbon::setTestNow()`) instead of asserting on real side effects.

## Enforce

- Larastan (`larastan/larastan`, a PHPStan extension) at a high level in CI.
- Pint for style — Laravel's wrapper around PHP-CS-Fixer; `pint --test` in CI, `pint` locally.
- Pest `arch()` (`pestphp/pest-plugin-arch`) for the boundary rules above; add Deptrac when the project also declares `.clean/architecture.md` layers.

## Smells

- Business logic inside a Blade template — an `@if` chain deciding a business rule, or a query call in the view (G17).
- `protected $guarded = [];` on a model, making every column mass-assignable (G4).
- An N+1 query hiding in a loop over a relationship the query never eager-loaded.
- A "Service" class that is a bag of static methods with no cohesive state — a facade wearing a service's name (G18, G11).
- A Form Request whose `rules()` duplicates a check already enforced by a Policy or a database constraint, drifting out of sync over time (G5).
- A fat controller method validating, querying, and formatting the response all at once (G30).
