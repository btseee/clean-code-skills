# C\#

> Applies to: C# 12–14 on .NET 8, 9, and 10 (.NET 8 and .NET 10 are LTS; all three are supported today, but .NET 8 and .NET 9 both end support 2026-11-10 — target .NET 10 for new work). Formatter: `dotnet format` with `.editorconfig`. Linter: .NET analyzers (`AnalysisLevel`) and StyleCop.Analyzers. Read with: the framework pack, if any.

## Names

- PascalCase for types, methods, and properties; camelCase for locals and parameters; `_camelCase` for private fields (N3).
- Prefix interfaces with `I` (`IOrderRepository`) — idiomatic C# convention, not the N6 encoding smell to avoid here.
- Suffix an async method with `Async`; name booleans as predicates (`IsArchived`, `HasExpired`); name every method for what it returns or does (G20).
- Make the namespace mirror the folder path below the project root, so a reader can find a type from its name alone.

## Functions And Types

- Enable `<Nullable>enable</Nullable>` and treat a `?` as a contract you checked, not a warning to silence; never use `!` to dismiss one you have not verified (G4).
- Prefer `record`/`record struct` for immutable data carriers; keep `class` for identity and behavior (data/object anti-symmetry).
- Leave a class `sealed` unless the project deliberately designs it for inheritance.
- Use file-scoped namespaces (`namespace Orders;`) — one file, one namespace, one less indent level.
- Guard arguments with `ArgumentNullException.ThrowIfNull(order)` instead of a hand-written `if`/`throw` block (G24).
- Keep parameters niladic to triadic; group related ones into a record before adding a fourth (F1).
- Never select behavior with a `bool` parameter; write two methods, or a small enum for more than two cases (F3).

## Errors

- `throw;` to rethrow — never `throw ex;`, which resets the stack trace and hides where the failure began.
- Never write `async void` outside an event handler: the caller cannot catch what it throws, so a failure crashes the process instead of failing one request.
- Never block on async code with `.Result`, `.Wait()`, or `GetAwaiter().GetResult()` in library or request code; it can deadlock under a synchronization context and hides the real call graph.
- Accept a `CancellationToken` on every async method that can wait, and pass it to every call that accepts one (CA2016); never swap in `CancellationToken.None` partway down the chain.
- Throw for genuine failures; model an expected alternate outcome — not found, declined, already archived — as a nullable return or a small result type (Special Case pattern).
- Chain the cause across a boundary (`throw new OrderException("archive failed", innerException)`); never leave a `catch` block empty (G4).

## Modules And Visibility

- Default every type and member to `internal`; make something `public` only when another project must call it (G8).
- Give each project one reason to change (CCP); keep the project-reference graph acyclic (ADP).
- Register dependencies (`AddScoped`, `AddSingleton`) in the composition root, never inside the class being registered (Main as the ultimate detail).
- Never reach for a static service locator or an ambient `Current`/`Instance` property in place of a constructor-injected dependency (G18).
- Expose an `internal` member to a test project through `[InternalsVisibleTo]`, named explicitly — never make a type `public` only so a test can reach it.

## Placement

- New code goes in the project that already owns the responsibility; a new project is a new component boundary, not a folder shortcut (SRP).
- Mirror the source project's folder structure in its test project, one for one.
- Never add to a catch-all `Common`, `Shared`, or `Utils` project; name the concept it actually holds (G17).
- Keep configuration and options classes beside the feature they configure, not in one shared configuration project.

## Tests

- Use the project's existing runner — xUnit, NUnit, or MSTest — and do not add a second one; xUnit's current major (v3) runs on Microsoft Testing Platform, so check which the project already targets.
- Name a test for the behavior it proves (`Archive_ProjectCompletedOverAYearAgo_MarksItArchived`) and assert the outcome through the public surface, not internals.
- Inject the clock; a test that reads `DateTime.Now`/`UtcNow` through production code is not repeatable (F.I.R.S.T.).
- Cover the boundary explicitly: exactly one year old, one day short, one day over (T5).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- The domain project references no `Microsoft.EntityFrameworkCore` and no `Microsoft.AspNetCore.*` package; when a domain type needs a capability from one, declare an interface in the domain and implement it outside (the Dependency Rule).
- Never let an EF Core entity or an ASP.NET Core request/response type cross into the domain or application project; map between them at the boundary.
- Wire every concrete dependency in `Program.cs` or a dedicated composition module; the domain and application projects never call `AddScoped` on themselves (Main as the ultimate detail).

```clean-architecture
layer domain         = src/Domain/**
layer application    = src/Application/**
layer infrastructure = src/Infrastructure/**
layer main           = src/Api/**, src/Worker/**
```

## Enforce

- NetArchTest.Rules, or ArchUnitNET (`TngTech.ArchUnitNET.*`), as a test project asserting the project-reference direction above.
- Project references as the physical enforcement: add only the `<ProjectReference>` the Dependency Rule allows; a build failure beats a review comment.
- `TreatWarningsAsErrors`, `<AnalysisLevel>latest</AnalysisLevel>`, and `EnforceCodeStyleInBuild` in `Directory.Build.props`; `dotnet format --verify-no-changes` in CI.
- CA1502 (excessive cyclomatic complexity) is off by default: enable it in `.editorconfig`, and tune its threshold (default 25) with a `CodeMetricsConfig.txt` line such as `CA1502: 15`, included as an `AdditionalFiles` item, not by suppressing the warning.
- StyleCop.Analyzers for the naming and layout rules above; suppress one rule at a time in `.editorconfig`, never with a blanket file-level pragma.

## Smells

- A static service locator or ambient `Current`/`Instance` property standing in for constructor injection (G18).
- Business logic reading `DateTime.Now`/`UtcNow` directly instead of an injected clock — untestable, and a dependency the signature hides (G18, T1).
- A static "helper" or "utility" class accumulating unrelated methods (G17).
- An EF Core entity accepted or returned directly as an API's request or response contract (G8).
- `catch (Exception) { }` swallowing a failure instead of handling or propagating it (G4).
- `partial class` used to avoid deciding where a member belongs, rather than for a generator (G17).
