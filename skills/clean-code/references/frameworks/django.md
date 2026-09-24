# Django

> Applies to: Django 5.2 LTS and 6.1. Language pack: languages/python.md. Read with: nothing.

## Structure

- `models.py` — ORM models: fields, model-level validation, `Meta`.
- `views.py` — request/response glue: parse input, call one service or selector, render or serialize the result.
- `urls.py` — URL patterns for the app, included from the project's root URLconf.
- `admin.py` — `ModelAdmin` registrations; no business rules.
- `forms.py` — Django forms: field definitions and form-level validation.
- `serializers.py` — DRF serializers: field definitions and (de)serialization only.
- `services.py` — the app's business rules and side-effecting operations, called from views, commands, and signal handlers.
- `selectors.py` — read-only queries: the `select_related`/`prefetch_related` shapes other code calls instead of repeating.
- `tests/` — one test module per unit under test, mirroring the app's structure.
- `management/commands/` — one file per command; a command parses arguments and calls a service.

## Roles

```clean-roles
role model = **/models.py, **/models/**
signal model = \((?:models\.)?Model\)
role view = **/views.py, **/views/**
signal view = \(\s*(?:\w+\.)?\w*(?:View|APIView|ViewSet)\s*[,)]
role serializer = **/serializers.py, **/serializers/**
role form = **/forms.py
role admin = **/admin.py
role url = **/urls.py
role service = **/services.py, **/services/**
role selector = **/selectors.py
role middleware = **/middleware.py
role command = **/management/commands/**
ignore-name = ^(Meta|get_queryset|get|post|put|patch|delete|dispatch|get_context_data|save|clean|handle|ready)$
```

## Rules

- Name a model singular PascalCase (`Order`, not `Orders` or `order`) and an app lowercase (`orders`, not `OrdersApp`) (N3).
- Put a rule on the model when only that model's own invariants govern it; put it in `services.py` when it spans models, calls out, or has steps to sequence (framework-first; SRP by actor).
- Keep `views.py` thin: parse the request, call one service or selector, shape the response; never branch a business decision inside a view (G17).
- Never put business flow in a signal handler; a receiver calls a service function and does nothing else (G17, G31).
- Call `select_related`/`prefetch_related` wherever a view, serializer, or selector walks a relation in a loop; a query per iteration is a defect, not a scaling detail for later (G3).
- Wrap a multi-write operation in `transaction.atomic()` explicitly; never rely on autocommit accidentally covering it (G27).
- Keep `admin.py` to `ModelAdmin` configuration; a computed or side-effecting admin action calls a service.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Business rules live in plain Python under `domain/`; `services.py` orchestrates them and reaches the database only through repository `typing.Protocol` ports declared in the domain (the Dependency Rule).
- `models.py`, `selectors.py`, and `repositories.py` are the persistence adapter: ORM types stay there and never travel into services or the domain.
- `views.py`, `serializers.py`, `forms.py`, `admin.py`, and `urls.py` are the delivery layer: they adapt HTTP to calls on services and selectors and back.
- Compose real implementations in `apps.py`'s `ready()` or a dedicated container module; never inside a view or model.

```clean-architecture
layer domain      = */domain/**
layer application = */services.py, */services/**
layer persistence = */models.py, */selectors.py, */repositories.py, */migrations/**
layer delivery    = */views.py, */serializers.py, */forms.py, */admin.py, */urls.py
layer main        = manage.py, */settings/**, */apps.py
```

## Tests

- Use `django.test.TestCase` for database-backed tests, each wrapped in a transaction; use plain pytest functions for pure logic in `services.py`/`selectors.py`.
- Build fixtures with a factory (factory_boy) or plain helper functions, not fixture files that hide what a test depends on.
- Use the Django test client or DRF's `APIClient` for view tests; assert status code and body shape, not query count, unless the test is about query count (`assertNumQueries`).
- Never point a test at a real external service; fake the gateway behind its port.

## Enforce

- django-stubs with mypy for model and queryset typing.
- Ruff `DJ` rules (for example `DJ001` no `null=True` on string fields, `DJ008` models define `__str__`).
- import-linter for the layers contract above, and to forbid `models.py` importing `services.py`.

## Smells

- A "fat view" doing validation, business rules, and response shaping in one function (G30, G17).
- The same rule reimplemented in a signal handler and in a service, drifting apart over time (G5).
- A view or serializer that triggers a database query per loop iteration (G3).
- A model importing another app's `services.py`, coupling persistence to unrelated business flow (G17).
- A multi-step write with no `transaction.atomic()`, leaving partial state on failure (G27).
