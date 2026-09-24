# Patterns

Architecture styles, design patterns, and data-access approaches: what each is for, when it earns
its place, when it is over-engineering, where the books stand, and which packs' frameworks embody
it. Read this when choosing or reviewing one.

## Contents

- Before reaching for a pattern
- Architecture styles: DI, IoC, MVC, MVVM, CQRS, Clean, Hexagonal, Microservices, Event-Driven
- Design patterns: Repository, Unit of Work, Factory, Singleton, Strategy, Adapter, Decorator,
  Observer, Command
- Data access: ORM, Micro ORM, Query Builder, Data Mapper, Active Record

## Before reaching for a pattern

A pattern is a cost paid for a force you can name today. First climb the minimal-code ladder in
`SKILL.md`; only then build the smallest version. Each "Over-engineered" line applies the ladder:
delete the pattern, write the direct code (A9). Book terms: `canon.md`; arguments: `architecture.md`.

## Architecture styles

### Dependency Injection

- **Intent:** a unit receives its collaborators instead of building or finding them.
- **Earns its place:** a collaborator varies by environment or test, or policy needs a detail it
  must not name.
- **Over-engineered:** one-implementation interfaces nobody fakes; a container for a small
  script; classes pulling services from the container (a service locator); eight constructor
  parameters (F1: several jobs).
- **Books:** DIP; construction apart from use; Main as the ultimate detail: wire in `main`, keep
  container annotations out of inner code.
- **Packs:** Spring `@Configuration`, ASP.NET Core `Program.cs`, NestJS providers, Symfony
  autowiring, FastAPI `Depends()`, Hilt or Koin (Jetpack Compose), Flutter constructors from
  `main.dart`.

### Inversion of Control

- **Intent:** the framework owns the flow and calls your code; DI is one kind.
- **Earns its place:** framework handlers, hooks, and middleware; in your code, a plugin point whose
  host must not know its plugins.
- **Over-engineered:** a home-made hook registry or plugin loader with one caller; business
  flow spread across lifecycle hooks in an order nobody sees (G31).
- **Books:** the plugin argument; DIP: control flow and source dependency point opposite ways;
  frameworks are details, so no business object derives from a framework class.
- **Packs:** the Spring and ASP.NET Core containers, Express and Gin middleware, React effects,
  Flutter's `initState` and `dispose`.

### MVC

- **Intent:** split input handling (controller), presentation (view), and state (model).
- **Earns its place:** request-response and server-rendered apps; frameworks that impose it.
- **Over-engineered:** hand-rolled atop a framework that has it; a CLI or one-page script gets
  `models/`, `views/`, and `controllers/`.
- **Books:** the web is a detail: MVC organizes delivery, not the application; views are Humble
  Objects; rules in a controller are G17; `models/` is not the domain (screaming architecture).
- **Packs:** Rails, Laravel, Symfony, Spring, ASP.NET Core, Express; Django says model, template,
  view.

### MVVM

- **Intent:** a view binds to a view model that holds presentation state and logic and names no
  view type.
- **Earns its place:** reactive UI toolkits; presentation logic worth testing without rendering.
- **Over-engineered:** a view model per static screen, or one that only forwards repository
  calls; state held in both the view and the view model (G5).
- **Books:** Humble Object: the view is humble, the view model testable; the Dependency Rule: no
  `Context`, view, or navigation controller inside it.
- **Packs:** Jetpack Compose `ViewModel` with `StateFlow`, SwiftUI view models, Flutter
  `ChangeNotifier`, Vue composables.

### CQRS

- **Intent:** separate the model that changes state (commands) from the one that answers questions
  (queries).
- **Earns its place:** reads and writes differ sharply in shape, load, or owner; reports fight the
  write model.
- **Over-engineered:** CRUD screens whose read and write shapes match; separate stores and
  eventual consistency with no load demanding them; a mediator hop before every call.
- **Books:** Command Query Separation at module scale; SRP: reads and writes often answer to
  different actors; the decoupling fallacy when both sides share one record.
- **Packs:** Django `selectors.py` beside `services.py`, ASP.NET Core mediator handlers
  (`IRequestHandler<`), Symfony Messenger with separate command and query buses.

### Clean Architecture

- **Intent:** concentric layers (entities, use cases, interface adapters, frameworks and drivers),
  every source dependency pointing inward.
- **Earns its place:** long-lived business rules; several delivery or storage options; rules worth
  testing with no database or server.
- **Over-engineered:** a CRUD app with no business rules gets four layers of pass-through mappers;
  boundaries built before any need, where a partial boundary would do.
- **Books:** the Dependency Rule; SOLID; component principles; Humble Object at each boundary; the
  database and the web as details; Main as the ultimate detail.
- **Packs:** every pack's `## Layers` section and `clean-architecture` block, enforced by
  `scripts/check_boundaries.py`.

### Hexagonal (Ports and Adapters)

- **Intent:** the application declares ports (interfaces it needs or offers); adapters implement
  them for HTTP, databases, queues, and tests.
- **Earns its place:** several drivers (HTTP, CLI, jobs) or swappable infrastructure; a core that
  must run with fakes.
- **Over-engineered:** a port per table with one adapter forever; a driving port for a single
  HTTP entry; adapters that only rename framework calls.
- **Books:** the Dependency Rule by another name; DIP: the port belongs to its user; one shared
  infrastructure tree lets a controller bypass the core.
- **Packs:** Spring adapters named for their technology, NestJS tokens bound with `useClass`,
  FastAPI `typing.Protocol` ports implemented in `crud/`, Gin and Ktor interfaces beside the
  service.

### Microservices

- **Intent:** independently deployable services, each owning its data.
- **Earns its place:** teams that deploy on their own cadence; parts with different scaling,
  runtime, or fault-isolation needs; module boundaries already proven in one process.
- **Over-engineered:** boundaries still move; services share a database or one record's
  fields; one team runs many services; a function call became a distributed transaction.
- **Books:** decoupling modes: one address space as long as possible, reversibly; architectural
  boundaries run through services, not between them; REP, CCP, CRP; Conway's law.
- **Packs:** each Spring, ASP.NET Core, NestJS, Gin, or Ktor service keeps its own layers;
  premature split: `smell-triage.md`.

### Event-Driven

- **Intent:** components announce facts; others react without the announcer knowing them.
- **Earns its place:** several independent reactions to one fact; work that runs later or
  elsewhere; integration across services.
- **Over-engineered:** one listener the emitter could call directly; a business process
  scattered across handlers, its order invisible (G31, G22); a broker for in-process work that
  needs an answer.
- **Books:** OCP: add a reaction without editing the emitter; event sourcing: store facts, replay
  state; a shared payload couples like a shared record.
- **Packs:** Laravel events, listeners, and queued jobs; Symfony subscribers and Messenger; Django
  signals (a receiver only calls a service); Rails Active Job; Flutter Bloc.

## Design patterns

### Repository

- **Intent:** a collection-like interface for loading and saving domain objects, hiding storage.
- **Earns its place:** business rules need persistence without naming the database; tests need an
  in-memory fake; queries recur.
- **Over-engineered:** a generic `IRepository<T>` over an ORM that already is one (EF Core
  `DbSet<T>`, Spring Data); returned query objects leaking the ORM (`IQueryable`, `QuerySet`); one
  per table, CRUD-named, with no domain vocabulary.
- **Books:** DIP: the interface sits beside the policy that uses it; the database is a detail; SQL
  stays in data access (G17).
- **Packs:** Spring Data, Symfony Doctrine repositories behind a domain interface, Laravel
  repositories bound in a provider, Django `repositories.py`, Jetpack Compose repositories over
  Room or Retrofit.

### Unit of Work

- **Intent:** track one business operation's changes and commit them together, atomically.
- **Earns its place:** one operation changes several objects that must succeed or fail together.
- **Over-engineered:** hand-written around an ORM session that already is one; wrapped around
  single-row writes; kept alive across requests (a captive `DbContext`).
- **Books:** the use case, not the controller, owns the transaction and sees a narrow commit port,
  never the session (the Dependency Rule); G31 when a forgotten flush loses writes.
- **Packs:** EF Core `DbContext.SaveChanges()`, the SQLAlchemy `Session`, Doctrine
  `EntityManager::flush()`, JPA's persistence context under Spring's `@Transactional`.

### Factory

- **Intent:** move the decision of what to construct away from the code that uses it.
- **Earns its place:** the concrete type depends on configuration or input; construction is
  complex; policy must create objects whose class lives outward (an abstract factory).
- **Over-engineered:** it wraps one constructor with no choice to make; factories build
  factories; a plain data class gets one.
- **Books:** construction apart from use; DIP: policy never instantiates a volatile class, so it
  names a factory interface implemented outward; Main as the ultimate detail.
- **Packs:** Flask `create_app`, the FastAPI session factory in `main.py`, ASP.NET Core
  `WebApplicationFactory` in tests, factory_boy in Django.

### Singleton

- **Intent:** one instance per process, reachable from anywhere.
- **Earns its place:** a truly single resource (a connection pool, a process-wide cache), created
  once in `main` and injected with a singleton lifetime.
- **Over-engineered:** a static accessor replaces passing a dependency; tests share its mutable
  state (G18); it captures a shorter-lived dependency.
- **Books:** G18; global mutable state (`smell-triage.md`); lifetime is a wiring decision in
  `main`, not a class property.
- **Packs:** ASP.NET Core `AddSingleton`, Angular `core/` services provided at the root, Spring's
  default bean scope; the Flask, Ktor, Flutter, and SwiftUI packs forbid global ones.

### Strategy

- **Intent:** interchangeable algorithms behind one interface, chosen at run time.
- **Earns its place:** two or more real variants today; the same type switch repeated in several
  places (G23).
- **Over-engineered:** one implementation kept "for later"; a class hierarchy where a function
  argument or a map of functions would do.
- **Books:** G23; OCP; LSP: a caller never checks which strategy it holds; a one-dimensional
  partial boundary (`architecture.md`).
- **Packs:** Spring injecting every bean of an interface as a `List` or `Map`, ASP.NET Core keyed
  services, Angular's `LocationStrategy` (`PathLocationStrategy`, `HashLocationStrategy`), Passport
  strategies in Express.

### Adapter

- **Intent:** convert an interface you have into the one your code expects, usually around a
  third-party API.
- **Earns its place:** a vendor SDK, framework, or protocol would otherwise spread through your
  code; providers must be swappable, or testable without the vendor.
- **Over-engineered:** it wraps your own code, or the standard library, behind an identical
  interface; adapters stack on adapters.
- **Books:** Clean Code's boundaries: own the interface, confine the vendor, pin its behavior with
  learning tests; the interface-adapters ring; Humble Object.
- **Packs:** Spring adapters named for their technology, Strapi outbound interfaces implemented in
  a provider, SvelteKit's `src/lib/server/`, a Laravel Eloquent implementation bound to a domain
  interface.

### Decorator

- **Intent:** wrap an object or function in one with the same interface, adding behavior around it.
- **Earns its place:** a cross-cutting concern (caching, retries, logging, metrics, authorization)
  added to some implementations without editing them.
- **Over-engineered:** a chain for a one-line concern; nesting so deep that order becomes a
  hidden dependency (G31); a wrapper that silently changes results (N7).
- **Books:** OCP; SRP: one concern per wrapper; cross-cutting policy at the edge. Language
  decorators (`@Injectable()`, Python's `@`) are syntax, not this pattern, and stay off business
  objects.
- **Packs:** Express, Gin, and ASP.NET Core middleware; Angular `HttpInterceptorFn`; Spring proxies
  behind `@Transactional` and `@Cacheable`.

### Observer

- **Intent:** a subject notifies subscribers of changes without knowing who they are.
- **Earns its place:** UI state that many views display; several independent reactions to one
  change.
- **Over-engineered:** one subscriber forever; an event bus between two objects that could
  call each other; a business sequence hidden in callbacks (G31).
- **Books:** OCP; the source dependency runs from observer to subject, against the notifications, as
  in DIP; ordering and idempotency are concurrency questions (`concurrency.md`).
- **Packs:** Angular signals, Jetpack Compose `StateFlow`, Flutter `ChangeNotifier` (listeners
  disposed in `dispose`), Django signals, Laravel and Symfony events.

### Command

- **Intent:** package a request as an object that can be queued, logged, retried, or undone.
- **Earns its place:** work must run later, retry, be audited, or be undone; each business action
  wants one entry point.
- **Over-engineered:** command, handler, and bus replace a synchronous call with one caller;
  the bus becomes a service locator.
- **Books:** SRP: one action, one class; use cases as request models and interactors; Command Query
  Separation: a command changes state and answers nothing.
- **Packs:** Laravel Actions and queued jobs (`ShouldQueue`), Symfony Messenger handlers
  (`#[AsMessageHandler]`), Rails Active Job, ASP.NET Core request handlers. Console commands share
  only the name.

## Data access

### ORM

- **Intent:** map tables to objects; code handles objects and the library writes the SQL.
- **Earns its place:** many related entities, CRUD-heavy flows, migrations, a team fluent in the
  ORM.
- **Over-engineered:** a full ORM serves three queries; reports contort through it where SQL
  reads clearer.
- **Books:** the database is a detail: ORM types stay in data access and never travel inward; rows
  are data structures, not objects (data/object anti-symmetry); the ORM is a Humble Object
  boundary. Watch lazy loading for N+1 queries.
- **Packs:** EF Core, Hibernate and JPA (Spring), Doctrine (Symfony), SQLAlchemy (FastAPI, Flask),
  TypeORM or Prisma (NestJS), and the Active Record ORMs below.

### Micro ORM

- **Intent:** you write the SQL; the library binds parameters and maps rows onto objects.
- **Earns its place:** SQL-heavy or performance-sensitive reads, reporting, a team fluent in SQL, no
  need for change tracking.
- **Over-engineered:** change tracking, identity maps, or lazy loading rebuilt on top; use an ORM
  instead.
- **Books:** SQL stays in the data-access layer (G17); parameterize every query and never
  concatenate input; the gateway is humble, so test it against a real database.
- **Packs:** Dapper (ASP.NET Core), Go's `sqlx` (Gin), Spring's `JdbcTemplate`.

### Query Builder

- **Intent:** compose SQL through a fluent API that parameterizes values, instead of building
  strings.
- **Earns its place:** filters, sorting, and joins assembled at run time; typed columns;
  portability across databases.
- **Over-engineered:** wrapped in a home-made generic builder; used for a fixed query that
  reads better as plain SQL.
- **Books:** SQL stays in data access, so a builder chain in a controller or service is misplaced
  SQL (G17); values are parameterized by construction.
- **Packs:** Knex or Kysely (Express, NestJS), Laravel's query builder, Django `QuerySet`,
  SQLAlchemy Core `select()`, Exposed's DSL (Ktor), Rails `where` chains.

### Data Mapper

- **Intent:** a separate layer moves data between domain objects and the database, so the objects
  know nothing of persistence.
- **Earns its place:** a rich domain model shaped unlike the tables; business rules tested without
  a database.
- **Over-engineered:** objects mirror the tables and carry no behavior, where Active Record is
  simpler; mapping annotations on domain objects undo the separation.
- **Books:** the Dependency Rule; the database is a detail; data/object anti-symmetry; mappers
  belong to the interface adapters.
- **Packs:** Doctrine (Symfony) and SQLAlchemy's ORM (FastAPI, Flask), each with a Unit of Work;
  Hibernate and JPA (Spring); EF Core mapped by `IEntityTypeConfiguration<T>` classes, not entity
  attributes.

### Active Record

- **Intent:** each object wraps a row and carries its own persistence (`save`, `find`).
- **Earns its place:** domains shaped like their tables; the framework's convention; speed over
  layering.
- **Over-engineered:** repositories and mappers wrap models whose domain still mirrors the
  tables. Outgrown when business rules pile onto models (SRP, G17) or callbacks hide side effects
  (G31, N7).
- **Books:** data/object anti-symmetry: a record is a data structure with persistence methods, so
  keep domain rules off it; with declared layers, models stay in the adapter layer, out of use
  cases (the Dependency Rule).
- **Packs:** Rails `ApplicationRecord`, Laravel Eloquent, Django models, TypeORM's `BaseEntity`,
  Exposed's DAO (Ktor).
