# Framework And Language Map

How the skill adapts to a stack: which packs to read, which role conventions decide where code
lives, and how to use a dependency the way it was meant to be used.

## Packs

A pack is a short, strict reference for one language or framework: names, functions, errors,
placement, tests, layers, the tools that enforce it, and its characteristic smells. Read the packs
your stack needs before the first edit.

- `scripts/detect_stack.py` prints them under **Read next** and records them in
  `.clean/context.json` as `packs`.
- By hand: look up each language and framework in the index below and read every file it names.
  Paths are relative to this folder.
- A language pack applies when that language is the project's most common indexed language or covers
  at least a tenth of its files. Editing a file in another language? Read that language's pack too.
- A framework pack describes the framework's own idiomatic structure: this skill is
  framework-first. Its **Layers** section applies only when `.clean/architecture.md` declares layers.
- No pack for your stack? Use the adaptation questions at the end of this file.

The index, read by `detect_stack.py`. Labels are spelled exactly as it reports them; `supersede`
drops the packs of a label that a detected framework already covers.

```clean-packs
# language <Label> = <pack>[, <pack>...]
# framework <Label> = <pack>[, <pack>...]
# supersede <Label> > <Label>[, <Label>...]
language JavaScript = languages/javascript.md
language TypeScript = languages/typescript.md, languages/javascript.md
framework React = frameworks/react.md
```

## Roles

A role is a kind of responsibility with a conventional home: middleware lives with middleware,
controllers with controllers. `scripts/map_structure.py` reads role conventions from fenced
`clean-roles` blocks — this one, one per framework pack, and optionally the project's own
`.clean/roles.md` — and reports symbols whose role differs from where they live.

```text
role <name> = <glob>[, <glob>...]      files matching are homes for <name>
name <name> [<exts>] = <regex>         symbol names matching have role <name>
signal <name> [<exts>] = <regex>       declarations matching (decorators, base types) have role <name>
ignore-name = <regex>                  names left out of name-clash and synonym findings
```

The project's `.clean/roles.md` wins, then the framework packs in the order `detect_stack.py` lists
them, then the conventions below. Signals beat names. Among homes, the most specific glob wins.
Interfaces, protocols, traits, enums, and type aliases never have a role: abstractions live beside
the code that consumes them.

```clean-roles
# Conventional homes shared by most stacks.
role controller = **/controllers/**, **/controller/**, **/*.controller.*, **/*_controller.*, **/*Controller.*
name controller = Controller$
role middleware = **/middleware/**, **/middlewares/**, **/*.middleware.*, **/*_middleware.*, **/*Middleware.*
name middleware = Middleware$
role service = **/services/**, **/service/**, **/*.service.*, **/*_service.*, **/*Service.*
name service = Service$
role repository = **/repositories/**, **/repository/**, **/repos/**, **/*.repository.*, **/*_repository.*, **/*Repository.*
name repository = (Repository|Repo|Dao|DAO)$
role model = **/models/**, **/model/**, **/entities/**, **/entity/**
role view = **/views/**
role component = **/components/**
role hook = **/hooks/**
role validator = **/validators/**, **/validation/**, **/*.validator.*, **/*_validator.*, **/*Validator.*
name validator = Validator$
role mapper = **/mappers/**, **/*.mapper.*, **/*_mapper.*, **/*Mapper.*
name mapper = Mapper$
role route = **/routes/**, **/routers/**, **/*.routes.*, **/*.router.*, **/*_routes.*
name route = (Router|Routes)$
role config = **/config/**, **/configuration/**
role dto = **/dto/**, **/dtos/**
ignore-name = ^(main|index|init|setup|run|handler|default|app|App|Program|Startup|Main|Meta|Config|Settings|Configuration|Module|create_app)$
```

## Universal Rule

Clean code should look idiomatic to a senior maintainer of that stack, and the project's existing
layout always overrides the ecosystem default. In a monorepo, respect each package's own conventions
and never import across packages except through their public entry points.

## Dependencies And Package Idioms

`.clean/context.json` carries the project's declared dependencies **with their versions**
(`detect_stack.py` collects them; by hand, read the manifests). Those versions are load-bearing:

- **Verify every API you call against the installed version, never memory.** The commonest invented-
  API failure is writing for the version you remember instead of the one in the lockfile.
- **Follow the package's intention.** A library ships with an intended usage shape — its
  configuration style, its extension points, its error model. Using it against that grain (hand-
  rolling what it provides, bypassing its lifecycle, reaching into its internals) is a finding, the
  same class as G24 ignoring conventions.
- **Check currency, but only where you genuinely can.** If you have web access, compare the
  installed major against the current one and *report* stale majors. Never guess at "latest" from
  memory, and never upgrade silently — an upgrade changes behavior and is a `decisions.md` entry
  for the user, not a drive-by.
- **A new dependency is a cost**: it brings transitive baggage (ISP at package scale) and an
  asymmetric commitment (see `architecture.md` on frameworks). Adding one is a decision worth
  recording; duplicating three lines is often cheaper than importing three thousand.

## Adaptation Questions

For a stack without a pack, answer these before changing code:

1. What does this ecosystem consider idiomatic error handling?
2. Where should domain logic live in this framework?
3. Where do new files go, and what registration makes them reachable?
4. What formatter or linter owns style?
5. How are tests normally structured?
6. What boundaries are risky here: network, database, UI lifecycle, concurrency, generated code, or permissions?
7. Which local pattern is established, and is it safe enough to follow?
