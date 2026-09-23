# ASP.NET Core

> Applies to: ASP.NET Core and EF Core 8, 9, and 10, each matching its .NET major (.NET 8 and .NET 9 both end support 2026-11-10; target .NET 10). Language pack: `csharp.md`. Read with: nothing.

## Structure

- `Controllers/` — the `controller` role: one MVC controller per resource, thin, delegating to a service or handler.
- `Endpoints/` — the `endpoint` role: minimal-API endpoint groups, where the project prefers `MapGet`/`MapPost` over controllers.
- `Middleware/` — the `middleware` role: custom pipeline components.
- `Filters/` — cross-cutting action or endpoint filters, the `filter` role.
- `Services/` — the `service` role: application and business logic behind an interface.
- `Data/` — the `data` role: the `DbContext` and its `IEntityTypeConfiguration<T>` classes, often in a `Data/Configurations/` subfolder.
- `Options/` — the `options` role: one class per bound configuration section.
- `Validators/` — the `validator` role: one FluentValidation class per command or request DTO.
- `Handlers/`, or beside the command it handles — the `request-handler` role, where the project uses a mediator pattern.
- `Program.cs` — composes the host, the middleware pipeline, and the DI container; holds no business rule.

## Roles

```clean-roles
role controller = **/Controllers/**
signal controller = \[ApiController\]|:\s*(?:ControllerBase|Controller)\b
role endpoint = **/Endpoints/**
role middleware = **/Middleware/**
signal middleware = RequestDelegate|:\s*IMiddleware\b
role filter = **/Filters/**
signal filter = IAsyncActionFilter|IActionFilter|ActionFilterAttribute
role data = **/Data/**
signal data = :\s*DbContext\b|IEntityTypeConfiguration<
role options = **/Options/**
signal validator = AbstractValidator<
signal request-handler = IRequestHandler<
```

## Rules

- Keep a controller or endpoint action thin: parse the request, call one service or handler, map the result — no query or business rule inline (Humble Object).
- Return errors as `ProblemDetails`: register `AddProblemDetails()` with a central `IExceptionHandler`, never a hand-rolled error shape per controller (G11).
- Bind configuration with the options pattern (`IOptions<T>`, `IOptionsSnapshot<T>`, `IOptionsMonitor<T>`); never read `IConfiguration` by string key inside a service (G35).
- Register `DbContext` with `AddDbContext`/`AddDbContextPool` and keep it scoped; never inject it into a singleton or cache an instance across requests — that is a captive dependency (G18).
- Use `AsNoTracking()` for read-only queries; keep change tracking only for entities you intend to update.
- Never use the EF Core InMemory provider to verify behavior: it skips constraints, transactions, and real query translation, so it can pass a test the real database would fail (G3). Use SQLite's in-memory mode, or a real instance, instead.
- Put a validation rule in the `validator` or a filter, not inside the action body (G30).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Controllers, endpoints, middleware, and filters are the delivery mechanism: they depend inward on application services or handlers, never the reverse, and hold no business rule (Humble Object, the Dependency Rule).
- `DbContext`, repositories, and `IEntityTypeConfiguration<T>` classes are infrastructure; declare the repository or gateway interface in the application layer and implement it in infrastructure (DIP).
- A filter or middleware invokes a rule; it never contains one — the rule lives in application or domain, where it can be tested without the HTTP pipeline (G17).
- Compose DI registrations, the middleware pipeline, and `DbContext` options in `Program.cs`, the outermost layer (Main as the ultimate detail).

```clean-architecture
layer domain         = src/Domain/**
layer application    = src/Application/**
layer infrastructure = src/Infrastructure/**
layer api            = src/Api/Controllers/**, src/Api/Endpoints/**, src/Api/Middleware/**, src/Api/Filters/**
layer main           = src/Api/Program.cs
```

## Tests

- Test controllers and endpoints through `WebApplicationFactory<TEntryPoint>` and an HTTP client; assert status code, the `ProblemDetails` shape, and the response body, not internal calls.
- Test services and handlers as plain classes with faked dependencies; a business-rule test needs no ASP.NET Core host.
- Replace the database with SQLite's in-memory mode (or a real instance via Testcontainers) for data-access tests, never the EF Core InMemory provider, so query-translation and constraint bugs surface (G3).
- Test the options pattern's bound values against a boundary case (`IValidateOptions<T>` or data annotations), not only the happy path (T5).

## Enforce

- NetArchTest.Rules or `TngTech.ArchUnitNET.*` asserting that `Api` and `Infrastructure` reference `Application`, never the reverse, and that `Domain` references neither.
- Project references as the physical enforcement: add only the `<ProjectReference>` the layering allows.
- `dotnet test` with `WebApplicationFactory` in CI for the delivery layer; `check_boundaries.py` for the declared layering.
- `dotnet format --verify-no-changes` and the C# pack's analyzer settings apply here too; do not relax them for controllers.

## Smells

- A captive dependency: a singleton or `IServiceScopeFactory` misuse that lets one `DbContext` leak across requests (G18, G31).
- Sync-over-async: `.Result`, `.Wait()`, or a synchronous wrapper around an async EF Core call (G4).
- A controller or endpoint calling `DbContext` or `SaveChanges` directly, skipping the service or handler that owns the rule (G17, G14).
- The EF Core InMemory provider used to "prove" behavior a real database would reject (G3, T1).
- One options class bound to all of `appsettings.json` instead of one class per section (G8, G35).
- A filter or validator re-implementing a rule the application layer already owns, instead of calling it (G5).
