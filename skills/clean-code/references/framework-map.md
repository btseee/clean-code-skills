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
- In a monorepo, a framework pack speaks only for the project whose manifest named the framework:
  `context.json` records those folders as `pack_scopes`.
- No pack for your stack? Use the adaptation questions at the end of this file.

The index, read by `detect_stack.py`. Labels are spelled exactly as it reports them; `supersede`
drops the packs of a label that a detected framework already covers in the same manifest.

```clean-packs
# language <Label> = <pack>[, <pack>...]
# framework <Label> = <pack>[, <pack>...]
# supersede <Label> > <Label>[, <Label>...]
language JavaScript = languages/javascript.md
language TypeScript = languages/typescript.md, languages/javascript.md
language Python = languages/python.md
language Java = languages/java.md
language C = languages/c.md
language C++ = languages/cpp.md
language C++ header = languages/cpp.md
language C# = languages/csharp.md
language PHP = languages/php.md
language Go = languages/go.md
language Rust = languages/rust.md
language Swift = languages/swift.md
language Objective-C = languages/objective-c.md
language Objective-C++ = languages/objective-c.md, languages/cpp.md
language Kotlin = languages/kotlin.md
language Ruby = languages/ruby.md
language Shell = languages/shell.md
language PowerShell = languages/powershell.md
language R = languages/r.md
language Dart = languages/dart.md
language Scala = languages/scala.md
language CSS = languages/css.md
language SCSS = languages/sass.md
language Sass = languages/sass.md
language Vue = frameworks/vue-nuxt.md
language Svelte = frameworks/svelte.md
framework React = frameworks/react.md
framework Next.js = frameworks/nextjs.md
framework Vue = frameworks/vue-nuxt.md
framework Nuxt = frameworks/vue-nuxt.md
framework Angular = frameworks/angular.md
framework Svelte = frameworks/svelte.md
framework SvelteKit = frameworks/svelte.md
framework Tailwind CSS = frameworks/tailwind.md
framework Django = frameworks/django.md
framework Flask = frameworks/flask.md
framework FastAPI = frameworks/fastapi.md
framework Express = frameworks/express.md
framework NestJS = frameworks/nestjs.md
framework Strapi = frameworks/strapi.md
framework Spring = frameworks/spring.md
framework Spring Boot = frameworks/spring.md
framework ASP.NET Core = frameworks/aspnet-core.md
framework EF Core = frameworks/aspnet-core.md
framework Laravel = frameworks/laravel.md
framework Symfony = frameworks/symfony.md
framework Drupal = frameworks/drupal.md
framework WordPress = frameworks/wordpress.md
framework Ruby on Rails = frameworks/rails.md
framework Gin = frameworks/gin-beego.md
framework Beego = frameworks/gin-beego.md
framework Ktor = frameworks/ktor.md
framework Jetpack Compose = frameworks/jetpack-compose.md
framework SwiftUI = frameworks/swiftui-uikit.md
framework UIKit = frameworks/swiftui-uikit.md
framework Flutter = frameworks/flutter.md
framework Unity = frameworks/unity.md
framework TensorFlow = frameworks/tensorflow.md
framework PyTorch = frameworks/pytorch.md
supersede NestJS > Express
supersede Strapi > React
supersede Drupal > Symfony
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
allow <home> = <role>[, <role>...]     a <home> file may also hold symbols of these roles
accept <glob>[ = <symbol>, ...]        a recorded exception: no misplaced or mixed finding
ignore-name = <regex>                  names left out of name-clash and synonym findings
```

The project's `.clean/roles.md` is read first, then the framework packs in the order
`detect_stack.py` lists them, then the conventions below. Signals beat names. Among homes, the most
specific glob wins, so record a deliberate exception with `accept`, not a competing rule.
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
