# PHP

> Applies to: PHP 8.3-8.5. Formatter: PHP-CS-Fixer (`@PER-CS` ruleset) or PHP_CodeSniffer (`PSR12`, converging on PER Coding Style). Linter: PHPStan (level `max`) or Psalm. Read with: the framework pack, if any.

## Names

- Use PascalCase for classes, interfaces, traits, and enums; camelCase for methods, properties, and variables; UPPER_SNAKE for class constants (N3).
- Name an interface for the contract it promises, following the ecosystem's convention consistently: the `Interface` suffix in Symfony and PSR code (`LoggerInterface`), the bare noun in Laravel contracts (`Queue`); never a Hungarian `I` prefix (N6).
- Name booleans and their accessors as questions (`isPaid`, `hasItems`); name a method by what it does or returns (G20).
- Never encode type or scope in a name (`$arrItems`, `$strName`, `$_private`) (N6).
- Use one word per concept across the codebase — a `Repository` is not a `Store` is not a `Manager` for the same responsibility (G11).

## Functions And Types

- Start every file with `declare(strict_types=1)`; without it, PHP silently coerces arguments (G26).
- Type every parameter, return, and property; do not rely on a docblock for anything PHP itself can express.
- Prefer `readonly` properties for state fixed at construction, and a `readonly` class when every property is (PHP 8.2+).
- Use constructor promotion for a constructor that only assigns; drop promotion the moment it needs validation logic first.
- Model a closed set of values as a backed `enum`, never as loose class constants (J3).
- Make a class `final` by default; remove `final` only where the design deliberately opens an extension point.
- Never suppress an error with `@`; handle it or let it surface (G4).
- Give a data shape its own class or readonly DTO instead of an untyped array with string keys — an array has no autocomplete and no static check (G26).

## Errors

- Throw a specific exception subclass, never a bare `\Exception`, and build a small hierarchy per failure family.
- Chain the cause: `throw new PaymentFailedException('charge declined', previous: $e);`.
- Model an expected alternate outcome — not found, declined, empty — as a return value or a result-like object, not an exception (Special Case pattern).
- Never catch `\Throwable` only to log and continue; either handle it meaningfully or let it propagate.
- Return `never` from a function that always throws or exits, so callers and static analysis both know control does not return.

## Modules And Visibility

- One class, interface, trait, or enum per file; the filename matches the symbol name exactly (PSR-4).
- Let the namespace mirror the folder path under the configured autoload root (`src/` to `App\`); a namespace that drifts from its path is a convention violation (G24).
- Default to `private`; use `protected` only for a documented extension point, `public` only for the class's real contract (G8).
- Never expose a public, mutable property on a class that also protects an invariant elsewhere — pick object or data structure, not a hybrid.
- Keep `composer.json`'s `autoload`/`autoload-dev` PSR-4 maps in sync with `src/` and `tests/`; a class composer cannot autoload is dead weight (G9).

## Placement

- Source in `src/`, tests in `tests/`, one test tree mirroring the source tree.
- Keep an entry script (`public/index.php`, a console `bin/` command) thin: bootstrap, dispatch, return.
- Never add to a `Utils`/`Helpers` namespace; name the concept the code models (G17).
- Group exceptions with the module that throws them; a single catch-all `Exceptions` namespace spanning unrelated domains hides which module owns which failure (G17).

## Tests

- Use PHPUnit or Pest; one behavior per test, named for the behavior, not the method under test (T1).
- Treat a PHPStan or Psalm error as a failing test, not a warning to defer or a baseline entry to grow (G4).
- Never silence a flaky test with a retry loop or a skip; find the shared state or timing it is exposing (T4).
- Cover boundary values with a data provider (PHPUnit `#[DataProvider]`) or a Pest dataset instead of copy-pasted near-identical tests (T5).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Domain classes never import a framework, ORM, or HTTP namespace; declare the interface the domain needs, and implement it outside (the Dependency Rule).
- Put an interface (`OrderRepository`) beside the domain code that calls it; its implementation (`DoctrineOrderRepository`) lives in the infrastructure layer.
- Wire concrete implementations to interfaces only in the composition root or the container configuration, never as a domain class's constructor default.

```clean-architecture
layer domain         = src/Domain/**
layer application    = src/Application/**
layer infrastructure = src/Infrastructure/**
layer main           = public/index.php, bin/**
```

## Enforce

- PHPStan at a high level (`max` where the codebase allows it) or Psalm, required in CI.
- PHP-CS-Fixer with the `@PER-CS` ruleset, or PHP_CodeSniffer with `PSR12`; auto-fix in a pre-commit hook or CI step, never by hand.
- Deptrac for the declared layers above; commit its ruleset file and fail the build on any outward-pointing dependency.
- phpmd's `codesize` ruleset, at least `CyclomaticComplexity` and `ExcessiveMethodLength`, tuned for the project rather than left at library defaults.

## Smells

- An associative array standing in for a struct (`$order['total']`) instead of a typed class — every key is a magic string no tool checks (G26).
- A static facade or singleton reached into from domain code, making it untestable without booting the framework (G18).
- A global function carrying a business rule instead of a namespaced function or method with a clear owner (G17, G18).
- A `Helpers`/`Utils` class collecting unrelated static methods (G17).
- `@`-suppressed warnings hiding a real failure instead of a handled one (G4).
- A constructor that validates, persists, and dispatches an event before returning — three responsibilities in one call (G30).
