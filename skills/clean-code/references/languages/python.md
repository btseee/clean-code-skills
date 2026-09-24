# Python

> Applies to: Python 3.10+. Formatter: Ruff format. Linter: Ruff, with mypy or pyright for type checking. Read with: the framework pack, if any.

## Names

- Use snake_case for functions, variables, and modules; PascalCase for classes; UPPER_SNAKE for module-level constants (PEP 8; N3).
- Name booleans as predicates (`is_active`, `has_items`) and generators for what they yield, not how they compute it (G20).
- Never encode type or container shape in a name (`str_name`, `lst_items`), or prefix a `Protocol`/ABC with `I` (`IRepository`) — name it for its role (N6).
- Give a module one job and a name for it; a package's `__init__.py` re-exports the public surface and does nothing else (SRP).
- Never write a vague name (`data`, `info`, `obj`, `temp`) or a bare-verb function with no object (`handle`, `process`); a loop or comprehension index, lambda parameter, caught exception, or established short form (`df`, `id`) may stay short, nothing else should (N1, N5).
- Never number or version a name instead of replacing it (`user2`, `_old`); never suffix a class with a noise word (`Manager`, `Helper`, `Util`) or name it after a verb (`ProcessOrder`) (N1, N4, G17).

## Functions And Types

- Keep functions small, at one abstraction level; extract a function instead of nesting another branch (G30, G34).
- Make optional and behavior-selecting parameters keyword-only after `*`; never add a boolean flag that branches behavior — write two functions (F3).
- Never default a mutable value (`def f(items=[])`): default to `None`, build it inside the body (G26).
- Put type hints on every public function, method, and attribute; run mypy or pyright in CI, not only the editor.
- Model plain data with `@dataclass(frozen=True)` or `NamedTuple`; reserve ordinary mutable classes for objects with real identity and behavior.
- Declare a `typing.Protocol` for a structural contract a caller depends on; reach for an ABC only where shared implementation matters.

## Errors

- Raise the most specific built-in or project exception; never raise a bare `Exception` or a string.
- Chain the cause across a re-raise (`raise ServiceError("refund failed") from error`); never write a bare `except:` that discards it (G4).
- Catch only the exception type you can act on; let everything else propagate.
- Model expected alternate outcomes — not found, declined, empty — as a return value or a small result type, not an exception (Special Case pattern).
- Handle an error once, where a decision can be made; never log-and-reraise the same error at every frame up the stack (G17).

## Modules And Visibility

- Prefix a name with `_` for anything outside a module's public surface; declare `__all__` where its star-import surface must be explicit.
- Never use a wildcard import (`from x import *`) outside a `__init__.py` re-export (G16).
- Break a circular import by moving the shared symbol to the module both sides already depend on; never paper over it with a function-local import (G22).
- Keep a class's public methods few and cohesive; unrelated public methods on one class are more than one reason to change (SRP).

## Placement

- Use the `src/` layout: package code under `src/<package>/`, tests under `tests/`, so tests exercise the installed package, not working directory.
- Keep entry point (`__main__.py` or `main.py`) thin: parse arguments, build collaborators, call in.
- Name a module for the domain concept it owns (`pricing.py`, `refunds.py`), never `utils.py` or `helpers.py` (G17).
- Put ORM models, HTTP clients, and file I/O in their own modules; a domain module never imports them directly (G17).

## Tests

- Use pytest; express setup and teardown with fixtures, not repeated per test (F.I.R.S.T.).
- Use `@pytest.mark.parametrize` for boundary and equivalence-class variations instead of copy-pasted test functions (T5).
- Name tests for behavior they prove (`test_cancel_refunds_payment`), and assert outcomes, never internals.
- Keep tests deterministic: injected clock or `freezegun`, no real network or filesystem call (F.I.R.S.T.).

## Concurrency

- Group sibling tasks with `asyncio.TaskGroup` (3.11+) instead of unsupervised `create_task` calls; a group cancels the rest when one member fails.
- Never call blocking I/O or CPU-bound work inside `async def`; use async client, or hand the call to `asyncio.to_thread`.
- Treat every `await` as a point where shared state can change underneath it; re-check invariants after (G31).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- A domain module never imports an ORM, HTTP framework, or `requests`/`httpx` client; declare a `typing.Protocol` port and implement it in an adapter module (the Dependency Rule).
- Compose the object graph in `__main__.py` or `main.py`; nothing else constructs a repository or client and hands it to policy.
- Keep framework base classes and decorators out of the domain layer; a domain object never inherits from one.

```clean-architecture
layer domain      = src/*/domain/**
layer application = src/*/application/**
layer adapters    = src/*/adapters/**
layer main        = src/*/__main__.py, src/*/main.py
```

## Enforce

- Ruff lint: `C901` (complexity), `PLR0913`/`PLR0912`/`PLR0915` (too many arguments, branches, statements), `ARG` (unused arguments), `ERA` (commented-out code), `BLE` (blind except), `S` (bandit security rules).
- mypy or pyright in strict mode for public APIs; import-linter (`.importlinter`) for layer and forbidden-import contracts.
- Ruff format (or Black) owns formatting; never hand-format around it.

## Smells

- A `utils.py` or `helpers.py` absorbing every function nobody else wants to place (G17).
- A bare `except:` or `except Exception:` that discards the cause (G4).
- A circular import papered over with a local `import` inside a function (G22).
- `import *` hiding which names a module actually provides (G16).
- Business logic that only runs correctly inside a notebook's cell execution order (G31).
- A mutable default argument silently shared and mutated across calls (G26).
