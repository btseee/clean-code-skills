# Framework And Language Map

How the skill adapts to a stack: packs, role conventions, dependencies used as intended.

## Packs

A pack is a short, strict reference for one language or framework: names, functions, errors,
placement, tests, layers, enforcement tools, smells. Read the packs your stack needs before the
first edit.

- `scripts/detect_stack.py` prints them under **Read next** (`.clean/context.json`, `packs`); by
  hand, look up each language/framework (paths relative here).
- A language pack applies when it's the project's most common, or covers a tenth of its files;
  editing another, read its pack too.
- A framework pack describes its own idiomatic structure — this skill is framework-first. Its
  **Layers** section applies only when `.clean/architecture.md` declares layers; in a monorepo,
  only for the project whose manifest named it (`pack_scopes`, `context.json`).
- No pack for your stack? Use the adaptation questions at file's end.

Index read by `detect_stack.py`, labels matching its output; `supersede` drops packs a detected
framework already covers in the same manifest.

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

A role: a responsibility with a conventional home. `scripts/map_structure.py` reads role
conventions from fenced `clean-roles` blocks (this one, per framework pack, optionally
`.clean/roles.md`), flagging symbols whose role differs from where they live.

```text
role <name> = <glob>[, <glob>...]      matches are homes for <name>
name <name> [<exts>] = <regex>         matching symbol names have role <name>
signal <name> [<exts>] = <regex>       matching declarations (decorators, base types) have role <name>
allow <home> = <role>[, <role>...]     a <home> file may hold these roles too
accept <glob>[ = <symbol>, ...]        a recorded exception: no misplaced, mixed, naming, or organization finding
entry <glob>[, <glob>...]              files a framework loads without an import: never unreferenced; an all-entry folder is no junk drawer
ignore-name = <regex>                  names left out of name-clash, synonym, and naming findings
```

Read order: `.clean/roles.md`, framework packs as `detect_stack.py` lists them, then the conventions
below. Signals beat names; the most specific glob wins — record exceptions with `accept`, not a
competing rule. Interfaces, protocols, traits, enums, type aliases never have a role: abstractions
live beside the code using them. `entry` lists files the framework finds by name or place (Next.js
`sitemap.ts`, Django `apps.py`, Laravel seeders); manifest targets (pyproject scripts and entry
points, package.json `bin`, `main`, `module`, `exports`) are entries automatically.

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

Clean code looks idiomatic to a senior maintainer of that stack; layout always overrides ecosystem
default. In a monorepo, respect each package's conventions; cross-package imports only through
public entry points.

## Dependencies And Package Idioms

`.clean/context.json` carries declared dependencies **with versions** (`detect_stack.py` collects
them; by hand, read the manifests) — load-bearing:

- **Verify every API against the installed version, never memory.** Commonest failure: coding to the
  version you remember, not the lockfile's.
- **Follow the package's intention** — configuration style, extension points, error model. Working
  against that grain (hand-rolled, bypassed lifecycle, reached-into internals) is a finding, same
  class as G24.
- **Check currency where you can.** With web access, compare installed majors against current,
  *report* stale ones — never guess "latest" or upgrade silently; a `decisions.md` entry, not a
  drive-by.
- **A new dependency is a cost**: transitive baggage (ISP at package scale), an asymmetric commitment
  (`architecture.md`, on frameworks). Record the decision — duplicating three lines often beats
  importing three thousand.

## Adaptation Questions

Without a pack, answer these before changing code:

1. What's idiomatic error handling in this ecosystem?
2. Where should domain logic live here?
3. Where do new files go, and what makes them reachable?
4. What formatter or linter owns style?
5. How are tests normally structured?
6. What boundaries are risky: network, database, UI lifecycle, concurrency, generated code, permissions?
7. Which local pattern is established, and is it safe to follow?
