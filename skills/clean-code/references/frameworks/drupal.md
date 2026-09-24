# Drupal

> Applies to: Drupal 10.x (PHP 8.1+; security fixes only, EOL 2026-12-09) and 11.x (PHP 8.3+; current). Language pack: `languages/php.md`. Read with: nothing.

## Structure

- `web/modules/custom/<module>/<module>.info.yml` — machine name, `core_version_requirement`, package; one module per bounded capability.
- `web/modules/custom/<module>/<module>.services.yml` — service definitions; `_defaults: autowire: true` resolves most constructor arguments from their type-hints.
- `web/modules/custom/<module>/<module>.module` — procedural hooks only where no OOP form exists yet; thin, delegates to a service.
- `web/modules/custom/<module>/src/Controller/**` — one route action per method; returns a render array or a `Response`.
- `web/modules/custom/<module>/src/Form/**` — `FormBase`/`ConfigFormBase` subclasses: build, validate, submit.
- `web/modules/custom/<module>/src/Plugin/<PluginType>/**` (for example `src/Plugin/Block/**`) — one plugin per class, declared with a PHP attribute.
- `web/modules/custom/<module>/src/EventSubscriber/**` — one core-dispatched event, one reaction, via `getSubscribedEvents()`.
- `web/modules/custom/<module>/src/Hook/**` — OOP hook implementations (Drupal 11.1+): plain classes whose methods carry `#[Hook('hook_name')]`, autowired as services.
- `config/install/**`, `config/sync/**` — exported configuration, owned by `drush config:export`/`config:import`.
- `tests/src/{Unit,Kernel,Functional,FunctionalJavascript}/**` — the four PHPUnit test types Drupal core defines.

## Roles

```clean-roles
role form = **/src/Form/**
role block = **/src/Plugin/Block/**
role event-subscriber = **/src/EventSubscriber/**
role hook = **/src/Hook/**
signal controller = extends\s+ControllerBase
signal form = extends\s+(?:Config)?FormBase
signal block = extends\s+BlockBase
signal event-subscriber = implements\s+EventSubscriberInterface
```

## Rules

- Inject services through the constructor, declared in `<module>.services.yml`; core's `_defaults: autowire: true` resolves most of them from the type-hint alone, with no `arguments:` line at all.
- Never call `\Drupal::service()`, `\Drupal::entityTypeManager()`, or another static `\Drupal::` accessor from inside a class; a static call belongs only in procedural `.module` code (DIP, G18).
- Give a controller or form a `create(ContainerInterface $container)` factory returning `new static(...)` with its injected services; never resolve a dependency any other way inside one.
- Implement a new hook as a method tagged `#[Hook('hook_name')]` on a plain class under `src/Hook/**` (Drupal 11.1+); reserve procedural `hook_*()` in `.module` for Drupal 10.x or a hook with no OOP form yet.
- Declare a plugin with a PHP attribute (`#[Block(id: '...', admin_label: ...)]`), not a docblock annotation — attributes replace annotations since Drupal 10.2, and every core plugin type accepts them from 11.2 (G24).
- Keep exported configuration under `config/sync/` and move it one way per change: edit the site, then `drush config:export`; or edit the YAML, then `drush config:import` — never both, or the next export silently drops the hand edit (G31).
- Model content through the Entity API — bundles, fields, `hook_entity_presave` reactions — instead of hand-written SQL for data Drupal already models as entities.
- Extend `ConfigFormBase` for a settings form that maps fields straight to configuration keys; use plain `FormBase` for anything that does not persist to config.
- Register a reaction to a core-dispatched event through `EventSubscriberInterface`/`getSubscribedEvents()` rather than the nearest hook, when both exist for it.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Controllers, Forms, EventSubscribers, and plugin classes are delivery: they translate a request, a submission, or an event into a call on a service.
- Business rules live in plain services that take scalars or value objects, never an `EntityInterface`, a `Request`, or a `FormStateInterface` in their signature.
- Declare a repository interface on the domain side to swap persistence; implement it against the Entity API or `Database::getConnection()` in an infrastructure service, bound in `<module>.services.yml`.
- Wire concrete bindings only in `.services.yml` and provider classes; a domain service never constructs its own infrastructure dependency.

```clean-architecture
layer domain         = **/src/Domain/**
layer infrastructure = **/src/Repository/**, **/src/Entity/**
layer delivery       = **/src/Controller/**, **/src/Form/**, **/src/Plugin/**, **/src/EventSubscriber/**, **/src/Hook/**
layer main           = **/*.services.yml, **/*.routing.yml
```

## Tests

- Use PHPUnit's four Drupal test types: Unit for plain classes, Kernel for anything touching the Entity API, config, or one real service, Functional/FunctionalJavascript for full request or route behavior.
- Prefer Kernel over Functional wherever a bootstrapped container is enough; a Functional test installs the whole site and runs far slower (T9).
- Build fixtures with the Entity API (`Node::create([...])->save()`) or an install profile's config, never a hand-inserted database row.
- Test a hook or event subscriber by dispatching the event or invoking the hook and asserting the resulting state, not that the callback ran.

## Enforce

- `phpcs` with the `Drupal` and `DrupalPractice` standards (`drupal/coder`) in CI, not only an editor integration.
- `mglaman/phpstan-drupal`, a PHPStan extension that resolves Drupal's runtime autoloading and core stubs.
- Deptrac for the layers declared above, once `.clean/architecture.md` exists.

## Smells

- `\Drupal::service('x')` or another static `\Drupal::` call inside a class instead of an injected dependency (G18, DIP).
- A plugin still declared with a docblock `@Block`/`@EntityType` annotation in a codebase already requiring Drupal 10.2+ (G24).
- Business logic living in a `.module` file's procedural hook instead of the service it should delegate to (G17).
- A form's `submitForm()` querying the database directly instead of calling a service (G30).
- Hand-edited YAML under `config/sync/` that the next `drush config:export` silently overwrites (G31).
- A hook implementation and an event subscriber both reacting to the same change, drifting apart over time (G5).
