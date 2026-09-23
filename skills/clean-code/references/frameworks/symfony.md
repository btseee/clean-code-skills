# Symfony

> Applies to: Symfony 7.4 LTS and 8.x (PHP 8.2+ on 7.4; PHP 8.4+ on 8.x). Language pack: `languages/php.md`. Read with: nothing.

## Structure

- `src/Controller/**` — one route group's actions; extends `AbstractController` for its helpers, or stays a plain invokable service.
- `src/Entity/**` — Doctrine entities: mapped fields and relations, `#[ORM\Entity]`.
- `src/Repository/**` — one query-building home per entity; extends `ServiceEntityRepository`.
- `src/Form/**` — form types; extends `AbstractType`.
- `src/EventSubscriber/**` — a cross-cutting reaction to a kernel or domain event; implements `EventSubscriberInterface`.
- `src/Command/**` — a console command; `#[AsCommand]`.
- `src/MessageHandler/**` — one handler per Messenger message; `#[AsMessageHandler]`.
- `src/Security/Voter/**` — one authorization decision per subject; extends `Voter`.
- `src/Service/**` (or a domain-named namespace) — business rules with no HTTP or console concern.
- `config/services.yaml` — autowiring and autoconfiguration defaults; an explicit binding only where autowiring cannot decide.
- `config/routes/attributes.php` — imports the routes declared as attributes on controllers.
- `templates/**` — Twig views; no business decisions.
- `tests/**` — mirrors `src/`.

## Roles

```clean-roles
role entity             = src/Entity/**
role form               = src/Form/**
role subscriber         = src/EventSubscriber/**
role command            = src/Command/**
role message-handler    = src/MessageHandler/**
role voter              = src/Security/Voter/**
signal controller       = extends\s+AbstractController
signal entity           = #\[ORM\\Entity
signal repository       = extends\s+ServiceEntityRepository
signal form             = extends\s+AbstractType
signal subscriber       = implements\s+EventSubscriberInterface
signal command          = #\[AsCommand
signal message-handler  = #\[AsMessageHandler
signal voter            = extends\s+Voter\b
```

## Rules

- Inject collaborators through the constructor; autowiring resolves them from type-hints. Never fetch a service from the container inside a class (DIP).
- Keep a controller a thin adapter: resolve the request, call a service or the message bus, return a response; put validation and business rules in a Form type, a Voter, or a service (G17).
- Authorize with a Voter and `denyAccessUnlessGranted()` or `#[IsGranted]`; never compare roles or ownership inline in a controller (G23).
- Dispatch a Messenger message and let an `#[AsMessageHandler]` service do the work; a controller or command never contains the handling logic itself.
- Map an entity to a plain DTO at the boundary when the layer rule is active; a serializer group is not a substitute for a real boundary (G26).
- Give a subscriber's `getSubscribedEvents()` exactly one job, wiring; put the reaction in a small method or a collaborator it calls (G30).
- Keep a console command's `execute()` as thin as a controller: parse input, call a service, format output (G17).
- Fetch related entities with a `JOIN` in a dedicated repository method; never trigger a lazy load inside a loop (the N+1 query).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Controllers, forms, subscribers, commands, and voters are the delivery layer: they adapt Symfony's request, console, or security lifecycle; they do not decide.
- Business rules live in services with no `Doctrine\ORM`, `Symfony\Component\HttpFoundation`, or `Symfony\Component\Console` import; declare the interface they need there, and implement it in infrastructure.
- Doctrine entities and repositories are infrastructure; when the domain needs persistence, it depends on an interface it declares, implemented by a Doctrine-backed repository.
- Wire concrete services to interfaces in `config/services.yaml` or a compiler pass, never inside a domain class's constructor default.

```clean-architecture
layer domain         = src/Domain/**
layer application    = src/Application/**
layer infrastructure = src/Entity/**, src/Repository/**
layer delivery       = src/Controller/**, src/Command/**, src/EventSubscriber/**
layer main           = src/Kernel.php, config/**, public/index.php
```

## Tests

- Use PHPUnit (Symfony's default) or Pest; `KernelTestCase`/`WebTestCase` for integration, plain PHPUnit for a service with no framework dependency.
- Test a Voter by calling `vote()` directly with a fake token and subject; never drive it through a full HTTP request to check one permission rule.
- Test a message handler as a plain class: construct it with fakes or stubs and call it directly, without dispatching through the real bus.
- Roll back each test's transaction (for example `dama/doctrine-test-bundle`) or use an in-memory/test database so tests stay independent (F.I.R.S.T.).

## Enforce

- Deptrac for the layer rules above; commit `deptrac.yaml` and fail CI on a violation.
- `phpstan/phpstan-symfony` alongside PHPStan at a high level, for container- and Doctrine-aware type checking.
- `bin/console lint:container` and `lint:yaml` in CI to catch a misconfigured service or file before deploy.

## Smells

- A controller building a Doctrine query or a business rule inline instead of delegating to a repository method or a service (G17).
- An entity returned directly as an API response, leaking ORM proxies and lazy-load traps into serialization (G26).
- A subscriber whose listener method holds the real business logic instead of delegating it (G30, G14).
- A service constructed with `new` inside another class instead of injected, duplicating what the container already resolves (G18).
- A Voter that queries the database directly instead of asking an injected service for the decision it needs (G14).
- A message handler validating, applying a side effect, and formatting a response all inside one `__invoke()` (G30).
