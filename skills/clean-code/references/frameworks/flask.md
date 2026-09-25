# Flask

> Applies to: Flask 3.x (current 3.1). Language pack: languages/python.md. Read with: nothing.

## Structure

- `app/__init__.py` — the application factory (`create_app`): builds the app, loads config, initializes extensions, registers blueprints.
- `app/extensions.py` — extension instances created unbound (`db = SQLAlchemy()`), bound in the factory with `init_app`.
- `app/config.py` — config classes (`DevelopmentConfig`, `ProductionConfig`) read from the environment.
- `app/<feature>/routes.py` (or `views.py`) — the feature's blueprint and its route functions.
- `app/<feature>/services.py` — the feature's business rules, called from its routes.
- `app/<feature>/models.py` — ORM models for the feature.
- `app/<feature>/schemas.py` — request and response (de)serialization and validation.
- `tests/` — mirrors `app/`, one test module per feature.

## Roles

```clean-roles
role route = **/routes.py, **/views.py, **/blueprints/**
signal route = @\w+\.(?:route|get|post|put|patch|delete)\(
role service = **/services.py, **/services/**
role model = **/models.py, **/models/**
role schema = **/schemas.py, **/schemas/**
role extension = **/extensions.py
entry **/*blueprint.py
```

## Rules

- Name a Blueprint for its feature, matching the package (`Blueprint("orders", __name__)` in `app/orders/routes.py`), so its endpoint prefix and `url_for` target stay obvious (N3).
- Build the app with an application factory (`create_app`); never construct a module-level `Flask(__name__)` that many other modules import (G18).
- Give every feature its own `Blueprint`, registered in the factory; never route directly on the app object outside the factory (G17).
- Create extension instances unbound in `extensions.py` and bind them with `init_app(app)` inside the factory, so no module needs `from app import db` to reach one (G22).
- Keep `services.py` free of `request`, `g`, and `current_app`; a route function reads the request and passes plain values in.
- Validate input and shape output with a schema in `schemas.py`; a route function never hand-parses `request.json` past that boundary.
- Read configuration through config classes selected once in the factory; never call `os.environ` deep inside a service (G35).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Routes are the delivery layer: they adapt HTTP to a call on `services.py` and back; they never decide.
- `services.py` never imports `flask` — no `request`, `g`, `current_app`, or `session` — and reaches the database through repository `typing.Protocol` ports; `repositories.py` implements them with the ORM.
- Models and `extensions.py` are the persistence adapter: models import `db` from `extensions.py`, and nothing inner imports either.
- Compose blueprints and adapter implementations in the application factory; nothing outside it constructs a client and hands it to a service.

```clean-architecture
layer domain      = */domain/**
layer application = */services.py, */services/**
layer persistence = */models.py, */repositories.py, */extensions.py
layer delivery    = */routes.py, */views.py, */schemas.py
layer main        = app/__init__.py, app/config.py
```

## Tests

- Build the app with the factory in a fixture (`create_app("testing")`) and use its `test_client()`; never share one mutated app instance across tests.
- Test `services.py` functions directly, with no client and no request context, wherever the rule does not need one.
- Push an application context (`app.app_context()`) only where a test needs `current_app` or the database; keep the rest context-free.
- Fake an external call behind the port a service depends on, not by monkeypatching a library deep in the call stack.

## Enforce

- Ruff for style; mypy or pyright against Flask's typed `Blueprint`/`Flask` signatures.
- import-linter to forbid `services.py` importing `flask`, and to forbid feature packages importing each other's internals.
- Flask's own `flask routes` command to check every blueprint is registered.

## Smells

- A god `app.py` holding routes, models, and configuration together (G30, G17).
- `from app import db` cycles between the factory module and feature modules (G22).
- A service function reading `request.args` or `current_app.config` directly (G17).
- A business rule duplicated between a route's inline logic and a service function (G5).
- An extension bound to a module-level app instead of through `init_app` (G18).
