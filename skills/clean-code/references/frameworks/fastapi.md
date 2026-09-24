# FastAPI

> Applies to: FastAPI 0.100+ with Pydantic v2 (FastAPI remains pre-1.0). Language pack: languages/python.md. Read with: nothing.

## Structure

- `app/main.py` — creates the `FastAPI()` instance, includes routers, mounts middleware; the composition root.
- `app/routers/` (or `routes/`) — one module per resource; each declares an `APIRouter` and its path operations.
- `app/schemas/` — Pydantic `BaseModel` request and response models.
- `app/models/` — ORM models (SQLAlchemy `DeclarativeBase` subclasses, or SQLModel classes with `table=True`).
- `app/dependencies.py` (or `deps.py`) — shared `Depends()` callables: auth, pagination, database session.
- `app/services.py` (or `app/<feature>/service.py`) — business rules called from routers.
- `app/crud/` — the persistence functions a service or router calls to read and write models.
- `app/config.py` — a `pydantic-settings` `BaseSettings` subclass, loaded once.

## Roles

```clean-roles
role route = **/routers/**, **/routes/**
signal route = @\w+\.(?:get|post|put|patch|delete|api_route)\(
role schema = **/schemas/**
signal schema = \(\s*BaseModel\s*\)
role model = **/models/**
signal model = DeclarativeBase|table=True
role dependency = **/dependencies.py, **/deps.py
role service = **/services.py, **/services/**
role repository = **/crud/**
```

## Rules

- Never perform blocking I/O (sync DB driver, `requests`, file read) inside an `async def` path operation; use an async client, or a sync `def` route, which FastAPI runs in a thread pool.
- Never return an ORM model with no `response_model` or return-type annotation; declare one built from a Pydantic schema so persistence-only fields never leak into the API by accident (G8).
- Validate every request body and query with a Pydantic schema; a path operation never reads raw `Request` JSON past that boundary.
- Push a cross-cutting concern (auth, DB session, pagination) into a `Depends()` callable instead of repeating it in every path operation (G5).
- Load configuration once through a `pydantic-settings` `BaseSettings` subclass; never call `os.environ.get` inside a router or service.
- Keep a router's path operations thin: validate through the schema, call one service or crud function, return.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Routers and schemas are the delivery layer: they adapt HTTP to a call on `services.py`/`crud/` and back.
- `services.py` never imports FastAPI (`Request`, `Depends`, `HTTPException`) or the ORM session type; declare a `typing.Protocol` port and implement it in `crud/`.
- Raise a domain exception from a service; translate it to `HTTPException` in one exception handler or the router, not scattered across services.
- Compose the engine, session factory, and dependency overrides in `main.py`.

```clean-architecture
layer domain      = */domain/**
layer application = */services.py, */services/**
layer persistence = */crud/**, */models/**
layer delivery    = */routers/**, */routes/**, */schemas/**, */dependencies.py, */deps.py
layer main        = app/main.py, app/config.py
```

## Tests

- Use `TestClient` (or `httpx.AsyncClient` with `ASGITransport`) against the app; override dependencies with `app.dependency_overrides`, never by monkeypatching.
- Test services and crud functions directly, without a client, wherever the rule does not need HTTP.
- Build request bodies with the schema (`model_validate`) in the test, not a hand-built dict that drifts from the real shape.
- Fake the database with a test session or an override; never point a test at a shared development database.

## Enforce

- Ruff `FAST` rules: `FAST001` redundant `response_model`, `FAST002` un-annotated `Depends` default, `FAST003` unused path parameter.
- mypy or pyright with Pydantic's plugin for model type-checking.
- import-linter for the layers contract above, and to forbid `services.py` importing `fastapi` or the ORM session.

## Smells

- A path operation returning the ORM model with no schema, leaking an internal column such as a password hash (G8).
- A synchronous database or HTTP call inside `async def`, stalling the event loop for every request (G3).
- The same `Depends()` chain copy-pasted across routers instead of named once and shared (G5).
- A business rule written inline in a path operation instead of a service function (G17).
- Settings read ad hoc with `os.environ` scattered through routers instead of through one settings object (G35).
