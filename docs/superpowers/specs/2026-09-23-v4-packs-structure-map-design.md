# v4.0.0 Design: Language and Framework Packs, Structure Map, Lean Core

Date: 2026-09-23. Status: approved for implementation. Branch: `feature/v4-packs-structure-map`.

## 1. Goals

The seven requests, and where each is answered:

| # | Request | Answered by |
| --- | --- | --- |
| 1 | Clean-code and clean-architecture rules per language and framework | §5 Packs: 19 language packs, 21 framework packs |
| 2 | Simpler usage | §4.6 `init` replaces `questions`; §4.3 load plan; `detect_stack.py` names the packs to read |
| 3 | Shorter README | §8 README of at most 150 lines; detail moves to `docs/` |
| 4 | One place, produced by Python, that shows what every file and symbol is for and whether it sits in the right place | §6 Structure map scanner (`map_structure.py`, `.clean/structure.md`) |
| 5 | Token, context, and performance efficiency for every model | §3 budgets, §4.5 lean `SKILL.md`, §4.3 load plan, §6.9 performance |
| 6 | Load all context first, then apply the books' rules strictly | §4.2 context gate, §4.4 precedence |
| 7 | Suggestions for what else to handle | Adopted: eval harness (§7), Enforce section per pack (§5.4), four extra framework packs (§5.1), component metrics and synonym detection (§6.5, §6.6) |

Declined during brainstorming, so out of scope: pull-request drift checks, monorepo per-package
layering, a single `clean.py` entry point, a printed context receipt, an HTML report.

## 2. Decisions Taken In Brainstorming

1. One spec, built in phases (§10).
2. **Framework-first.** Packs describe each framework's idiomatic structure. Clean Architecture's
   layer rules — the Dependency Rule, frameworks as details, never deriving a business object from a
   framework base class or annotating it — apply only when `.clean/architecture.md` declares layers.
   Clean Code rules (names, functions, comments, errors, tests, one job per unit, role-based
   placement) apply always.
3. Extras adopted: eval harness; an Enforce section in every pack; ASP.NET Core, SwiftUI/UIKit,
   Jetpack Compose, and Ktor packs; component metrics and synonym detection in the scanner.
4. The structure map is one Markdown file, `.clean/structure.md`, with a JSON twin.
5. Usage: `init` replaces `questions`, which stays as an alias. No dispatcher script, no receipt.
6. Approach A: one skill. Packs live under `references/` and are routed by `detect_stack.py`
   through an index in `framework-map.md`. Framework packs carry `clean-roles` blocks that the
   scanner parses, so role-to-folder conventions have exactly one home.

## 3. Loading Model And Budgets

Three tiers of text reach a model:

| Tier | Where | When | Budget (validated) |
| --- | --- | --- | --- |
| Managed block | host instruction files (`CLAUDE.md`, `AGENTS.md`, ...) | every turn | no growth: at most 1,200 tokens |
| `SKILL.md` | skill folder | on activation | at most 3,000 tokens (today 4,998 of a 5,000 ceiling) |
| References and packs | `references/` | on demand, per the load plan | each pack at most 2,000 tokens; any reference over 300 lines opens with a contents list |

Tokens are measured the way the validator already measures them: words × 4 / 3.

A typical edit session loads the block (about 1.2k), `SKILL.md` (about 2.5k), one or two language
packs and up to two framework packs (about 1.5k each), the `.clean/` files, and the structure-map
rows for the area being changed. That is roughly 6k to 9k tokens, all of it relevant to the stack,
where today the fixed cost alone is about 6.2k and carries no stack-specific guidance.

Layout after v4:

```text
skills/clean-code/
  SKILL.md                    router, at most 3,000 tokens
  references/
    framework-map.md          pack index (clean-packs), generic roles (clean-roles),
                              dependency idioms, fallback adaptation questions
    init.md                   renamed from questions.md, extended
    review-checklist.md       + agent failure modes + anti-loopholes, moved from SKILL.md
    languages/*.md            19 language packs
    frameworks/*.md           21 framework packs
  scripts/
    detect_stack.py           + pack routing, + framework signatures
    check_boundaries.py       import parsing moved out; behavior unchanged
    scan_repo.py              unchanged
    project_files.py          + glob matcher
    project_imports.py        NEW: import extraction and module index
    project_symbols.py        NEW: symbol extraction per language
    structure_roles.py        NEW: clean-roles parsing and role assignment
    structure_findings.py     NEW: misplaced, mixed, duplicates, name clashes, synonyms
    component_metrics.py      NEW: component graph, I/A/D, cycles
    map_structure.py          NEW: CLI, structure.md and structure.json rendering
evals/                        NEW, repository only, never installed
tests/                        NEW, repository only: unittest suites for the scanners
docs/install.md               NEW: hosts, profiles, global mode, update, uninstall, env vars
docs/configuration.md         NEW: .clean/ files, declaration formats, hooks
docs/pack-sources.md          NEW: official sources each pack was verified against
```

## 4. Core

### 4.1 Managed Block

`templates/agent-block.md` changes, then `bash scripts/sync.sh` mirrors it into all eight adapters:

- "Dependency Direction" becomes "Layers", scoped to projects whose `.clean/architecture.md`
  declares them, plus one bullet: without declared layers, follow the framework pack's idiomatic
  structure; the Clean Code rules still apply.
- "Read the skill" adds: read the language and framework packs that `detect_stack.py` names, or
  look them up in `references/framework-map.md`.
- Placement adds: a unit's role decides its folder, per the pack's roles.
- `questions` becomes `init` wherever it is named.
- The block must not grow past 1,200 tokens, so the additions are paid for by trimming.

### 4.2 Context Gate

`SKILL.md` opens with the gate. Before the first edit, in order, each step naming its manual
equivalent:

1. **Stack.** `.clean/context.json`; else `scripts/detect_stack.py` without `--write`. By hand:
   manifests and file extensions.
2. **Packs.** Read every pack listed under `packs` or printed as "Read next". By hand: look up the
   language and framework in the `clean-packs` index in `references/framework-map.md`.
3. **Layers.** `.clean/architecture.md`. Declared: layer rules apply strictly and
   `check_boundaries.py` enforces them. Absent: framework-first, per the pack.
4. **Decisions and ledger.** `.clean/decisions.md`, `.clean/ledger.md`.
5. **Structure.** The rows of `.clean/structure.md` for the area being changed (grep the path), or
   `scripts/map_structure.py --path <area>`. By hand: list the folder and open the two or three most
   similar files.
6. **Project instructions.** `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`,
   `README.md`.

### 4.3 Load Plan

A table in `SKILL.md`:

| Task | Read, beyond `SKILL.md` and its packs |
| --- | --- |
| Any edit | the `.clean/` files present; structure rows for the area |
| Review or diff review | `review-checklist.md` |
| New dependency, boundary, layer, framework, or database | `architecture.md`, via its contents list |
| Writing or fixing tests | `tests.md` |
| Concurrency | `concurrency.md` |
| Naming or triaging a smell | `smell-triage.md`, `chapter-map.md` |
| `init`, `audit`, `clean-up`, `new-project` | `init.md`, `audit-report.md`, `project-refactor.md`, `new-project.md` |
| Editing a language whose pack is not loaded | that pack, via the index |

### 4.4 Precedence

Stated once in `SKILL.md`: project instructions, then recorded decisions, then declared layers, then
existing local conventions, then the framework pack, then the language pack, then the skill's
defaults. The block keeps its existing sentence that project instructions outrank it.

### 4.5 `SKILL.md` Outline

Frontmatter (`name`, `description`, `license`, `compatibility`,
`argument-hint: "[init | audit | clean-up | new-project <description>]"`, `metadata.version`), then:
purpose in two or three sentences; context gate; precedence; the operating loop in six short steps;
always-on Clean Code rules (placement by role, including the sibling-variant, junk-drawer, and
repository-root rules; one job per unit; names; functions; comments; errors; tests; verified APIs;
true duplication only); layer rules when declared; commands; load plan; tools (four scripts); scope
modes in two lines; a compressed completion checklist.

Moved out: the Agent Failure Modes and Anti-Loopholes tables go to `review-checklist.md` under a
"Self-check before completion" heading. Smell triage becomes a pointer.

### 4.6 The `init` Command

`references/questions.md` becomes `references/init.md`:

1. **Detect**: `scripts/detect_stack.py --write`.
2. **Interview**: the existing seven topics, one question at a time with detected defaults. The
   layers question now defaults to "no declaration, framework-first" and writes
   `.clean/architecture.md` only when the user opts in.
3. **Map**: `scripts/map_structure.py --write`. By hand: list each source folder, its role, and any
   file whose symbols do not match that role.
4. **Close**: echo what was written and where; summarize packs, layers, and the top structure
   findings; suggest `audit` when the findings are more than a handful.

`SKILL.md`, the README, the manifests, and the block say `init`. `questions` and "interview me"
remain accepted aliases.

### 4.7 Other Core Edits

- `session-protocol.md`: its context steps mirror §4.2; the inspection step reads structure rows;
  the after-work steps refresh the map with `--write` when `.clean/` exists and files were added or
  moved.
- `memory-protocol.md`: adds `structure.md` and `structure.json` (a generated cache, never
  hand-edited; the header records the git commit, and a differing HEAD means regenerate) and the
  optional `roles.md` (project role overrides).
- `audit-report.md`: the inventory comes from `structure.json`; misplaced, mixed, duplicate,
  synonym, and cycle findings feed the ledger; the metrics feed the architecture assessment.
- `project-refactor.md`: placement batches consume map findings and re-run
  `map_structure.py --path` after each move.
- `new-project.md`: layer declaration stays, framed as opting into strict layer rules; the initial
  layout comes from the framework pack's Structure section.
- `architecture.md` and `chapter-map.md` gain a contents list (both exceed 300 lines).
- `assets/hooks/claude-settings.json`: the SessionStart hook also prints the header and finding
  counts of `.clean/structure.md`.
- `CONTEXT.md`: adds Pack, Pack index, Role, Home role, Structure map, Finding, and Component; a
  Scanner becomes one of four optional Python scripts.
- Version 4.0.0, because the rules contract changes: layer rules become conditional.

## 5. Packs

### 5.1 Inventory

Languages (19), in `references/languages/`: `typescript`, `javascript`, `python`, `java`, `cpp`,
`csharp`, `php`, `go`, `rust`, `swift`, `kotlin`, `ruby`, `shell`, `c`, `r`, `dart`, `scala`,
`objective-c`, `powershell`.

Frameworks (21), in `references/frameworks/`: `react`, `nextjs`, `vue-nuxt`, `angular`, `svelte`
(Svelte and SvelteKit), `django`, `flask`, `fastapi`, `express`, `nestjs`, `spring` (Spring
Framework and Spring Boot), `laravel`, `symfony`, `rails`, `gin-beego`, `strapi`, `flutter`,
`aspnet-core` (with EF Core), `swiftui-uikit`, `jetpack-compose`, `ktor`.

Packs layer rather than repeat: a TypeScript project also loads `javascript.md`, a Next.js project
also loads `react.md`. Every framework pack names its language pack.

### 5.2 Language Pack Template

```markdown
# <Language>

> Applies to: <versions>. Formatter: <tool>. Linter: <tool>. Read with: <packs, or nothing>.

## Names
## Functions And Types
## Errors
## Modules And Visibility
## Placement
## Tests
## Concurrency
## Layers
## Enforce
## Smells
```

`Concurrency` is optional; every other heading is required, in this order.

### 5.3 Framework Pack Template

```markdown
# <Framework>

> Applies to: <versions>. Language pack: <file>. Read with: <packs, or nothing>.

## Structure
## Roles
## Rules
## Layers
## Tests
## Enforce
## Smells
```

### 5.4 Authoring Rules

Rules marked (validated) are checked by `validate.sh`.

- Required headings present and in order (validated); at most 2,000 tokens (validated), aiming for
  about 1,500.
- Imperative one-line bullets: "Never ...", "Always ...", "Prefer ...". Where a book rule applies,
  cite it by canon name or smell ID in parentheses — (G5), (F.I.R.S.T.), (DIP), (N1) — so every
  rule traces back to `canon.md` and `chapter-map.md`.
- **Structure** (framework packs): the idiomatic layout, one line per folder, and which role lives
  where. This is the framework-first default.
- **Layers**: opens with "Applies only when `.clean/architecture.md` declares layers." Then: which
  framework types must not cross inward, where interfaces for details are declared, where the
  composition root and dependency-injection wiring live, and a suggested `clean-architecture` block
  of at most six lines.
- **Enforce**: real tools that check the rules mechanically, with the rule or configuration key that
  matters — lint rules for function size, complexity, and unused code, and architecture checkers
  such as dependency-cruiser or eslint-plugin-boundaries, import-linter and Ruff, ArchUnit or
  Konsist, NetArchTest, Deptrac, go-arch-lint, Clippy, ShellCheck, PSScriptAnalyzer, lintr,
  SwiftLint, detekt, RuboCop, PHPStan, `dart analyze`, Scalafix, clang-tidy. Only tools that exist.
- **Smells**: language- or framework-specific failure patterns, each with its nearest smell ID.
- At most two code examples, each at most eight lines.
- **Accuracy**: every API, file convention, and configuration key is verified against official
  documentation for the stated versions. Sources are recorded in `docs/pack-sources.md`, which is
  neither shipped nor loaded.
- **Originality**: no book text. Checked before commit by comparing word n-grams against the local,
  gitignored books.
- Framework packs contain a `clean-roles` block that parses and uses lowercase role names
  (validated).

### 5.5 Pack Index

`framework-map.md` gains a fenced block the scripts read:

````markdown
```clean-packs
language TypeScript = languages/typescript.md, languages/javascript.md
framework Next.js = frameworks/nextjs.md, frameworks/react.md
supersede NestJS > Express
```
````

Two statements. `language|framework <Label> = <path>[, <path>...]` maps a label, spelled exactly as
`detect_stack.py` reports it, to pack paths relative to `references/`.
`supersede <Label> > <Label>[, <Label>...]` drops the right-hand labels' packs when the left label is
detected (a NestJS project also depends on Express). Validated: every path exists, every pack file is
indexed, and every label is one `detect_stack.py` can emit.

The rest of `framework-map.md` keeps the universal rule, the dependency and package idioms, and the
adaptation questions (the fallback for stacks without a pack), and gains the generic `clean-roles`
block described in §6.3.

### 5.6 `detect_stack.py` Changes

- New signatures: `@sveltejs/kit` → SvelteKit, `@strapi/strapi` → Strapi, `beego` → Beego,
  `org.springframework` → Spring, `microsoft.net.sdk.web` → ASP.NET Core, `androidx.compose` →
  Jetpack Compose, `io.ktor`, `ktor-server`, and `ktor.server` → Ktor.
- New manifest: `libs.versions.toml`, the Gradle version catalog.
- New source signatures, bounded to 200 files and their first 60 lines: `import SwiftUI` →
  SwiftUI; `import UIKit`, `#import <UIKit/...>`, and `@import UIKit` → UIKit. Neither framework
  appears in a manifest.
- Pack routing reads the index from the skill's own `references/framework-map.md`. Language packs:
  the most common indexed language, plus any indexed language with at least 10% of the indexed
  languages' files. Framework packs: every detected label, minus superseded ones. Order: languages,
  then frameworks, deduplicated. Output: a `packs` key (paths prefixed `references/`) and a summary
  line `Read next : ...`. A missing index yields `packs: []` and a note, never an error.

## 6. Structure Map Scanner

### 6.1 Purpose

One file answers, for every source file, what it contains, what role it plays, what it is for, and
whether it sits in the right place. Duplication, mixed responsibility, and misplaced code become
visible, and a cold session reads one file instead of crawling the tree. Like the other scanners, its
output is evidence for judgement, never a verdict.

### 6.2 Modules

| Module | One job |
| --- | --- |
| `project_imports.py` | Which modules a file imports, and which project files an import resolves to. `IMPORT_PATTERNS`, `extract_imports`, and `resolve_relative_import` move here unchanged from `check_boundaries.py`; adds PowerShell, Shell, R, Objective-C `#import`, and more C-family and PowerShell extensions; adds `ModuleIndex` |
| `project_symbols.py` | Which symbols a file declares: name, kind, lines, visibility, doc summary, declaration context, body fingerprints |
| `structure_roles.py` | Parse `clean-roles` blocks; give each file a home role and each symbol an intrinsic role |
| `structure_findings.py` | Misplaced, mixed, duplicates, name clashes, synonyms |
| `component_metrics.py` | Component graph, afferent and efferent coupling, instability, abstractness, distance, cycles |
| `map_structure.py` | The CLI: orchestrates the modules above and renders `structure.md`, `structure.json`, and the terminal summary |
| `project_files.py` | Gains `glob_match(pattern, path)`: `**` spans directories, matching ignores case |

`check_boundaries.py` imports from `project_imports.py`; its behavior and CLI do not change. The
classification table in CI is the regression gate.

### 6.3 The `clean-roles` Grammar

Blocks live in `framework-map.md` (generic conventions), in each framework pack, and optionally in
the project's `.clean/roles.md`.

```text
role <name>              = <glob>[, <glob>...]   files matching a glob are homes for <name>
name <name> [<suffixes>] = <regex>               symbols whose name matches get intrinsic role <name>
signal <name> [<suffixes>] = <regex>             symbols whose declaration context matches get intrinsic role <name>
ignore-name              = <regex>               names excluded from name-clash and synonym findings
```

- Role names match `[a-z][a-z0-9-]*`. Globs are root-relative posix paths, `**` spans directories,
  and matching ignores case. Regexes use Python `re` syntax.
- The optional bracketed suffix list (`name component [tsx, jsx] = ^[A-Z]\w*$`) limits a `name` or
  `signal` statement to files with those extensions, so a React pack's PascalCase rule never
  touches a Go backend in the same repository.
- Precedence: `.clean/roles.md`, then framework packs in `packs` order, then the generic block. A
  symbol's intrinsic role is the first matching `signal`, else the first matching `name`, scanning
  sources in precedence order and each block top to bottom. A file's home role comes from the
  matching `role` glob with the most literal characters; ties go to the higher-precedence source.
- Declaration context: up to three decorator, annotation, or attribute lines directly above the
  symbol, plus its declaration up to the body opener (at most three lines).
- A malformed line or regex makes `map_structure.py` exit 2, naming the file and line. The validator
  parses every shipped block.

### 6.4 Symbol Extraction

- **Python**: `ast` — classes, functions, async functions, methods, decorators, docstrings,
  `__all__`, underscore privacy.
- **Brace languages** (JavaScript, TypeScript, Java, Kotlin, C#, Scala, Dart, Swift, PHP, Go, Rust,
  C, C++, Objective-C, Shell, PowerShell, R): per-language declaration patterns; body extent by
  brace matching over a light lexer that skips strings and comments; methods found inside type
  bodies.
- **Ruby**: `class`, `module`, and `def`, with extent from indentation and the matching `end`.
- **Vue and Svelte single-file components**: the file is a component symbol; the `<script>` block
  is parsed as JavaScript or TypeScript.
- **Visibility**: `export` or an export list (JavaScript, TypeScript); no leading underscore and
  `__all__` (Python); capitalized (Go); `pub` (Rust); the language's default and explicit modifiers
  (JVM languages, C#, Swift, Dart, PHP); everything top-level (Ruby, Shell, PowerShell, R, C).
- **Doc summary**: the first sentence, at most 100 characters, of the docstring or of the comment
  block directly above. File purpose: the module docstring or header comment, skipping license and
  copyright headers.
- **Fingerprints** for functions and methods with at least six normalized lines: exact (comments and
  whitespace stripped) and shape (identifiers and literals abstracted, keywords kept).

### 6.5 Findings

Test files (per `project_files.is_test_path`) are counted but never produce findings. A
*role-bearing* symbol is a top-level symbol with an intrinsic role whose kind is not interface,
type, enum, protocol, or trait: abstractions legitimately live beside their consumers.

- **Misplaced**: a role-bearing symbol whose intrinsic role differs from its file's home role; or a
  file without a home role whose role-bearing symbols all share one role that has a home elsewhere
  in the project. The finding suggests a destination: the folder holding most files with that home
  role (same source root first); else the folder implied by the role's first `**/<dir>/**` glob
  under the file's source root; else "a file matching `<glob>`".
- **Mixed**: a file without a home role whose role-bearing symbols carry two or more intrinsic roles.
- **Duplicate**: functions or methods sharing an exact fingerprint ("identical") or a shape
  fingerprint ("same shape") across locations.
- **Name clash**: one top-level symbol name, at least four characters and not ignored, declared in
  two or more non-test files of the same language.
- **Synonyms** (one word per concept): one noun used with two or more verbs from the same group
  across function and method names. Groups: retrieve {get, fetch, load, retrieve}; create {create,
  add, insert, make}; update {update, modify, edit, change}; delete {delete, remove, destroy,
  erase}. Nouns are singularized; trivial nouns (all, by, data, item, items, list, value) are
  skipped.
- **Cycle**: a strongly connected set of two or more components.

### 6.6 Component Metrics

A component is the first `--depth` directory segments of a file's path (default 2; shallower files
use their own directory). Edges are imports resolved by `ModuleIndex` between non-test files in
different components.

- Ca: files outside the component that import into it. Ce: files outside the component that it
  imports.
- Instability I = Ce / (Ca + Ce).
- Abstractness A = abstract types / all types. Abstract means an interface, protocol, trait (PHP
  traits excepted), abstract class, or Python `ABC`/`Protocol` subclass.
- Distance D = |A + I − 1|.
- Undefined values render as `-`, never as zero.

### 6.7 Import Resolution

`ModuleIndex` resolves relative paths (JavaScript and TypeScript including index files, Python
dots, Dart, Ruby `require_relative`, Shell `source`, PowerShell dot-sourcing, R `source`, quoted
C-family includes with a unique-basename fallback); `baseUrl` and `paths` aliases from `tsconfig.json`
and `jsconfig.json`; Python dotted modules; JVM `package` plus type name; C# namespaces, file-scoped
or block; PHP namespace plus class; Go import paths under the `go.mod` module; Rust `crate::`,
`self::`, and `super::`; Dart `package:<own name>/`. An import it cannot resolve is skipped, never
guessed.

Some languages reference other files without importing them: Swift (one module, no file imports),
Ruby under Rails autoloading, and same-namespace or same-package code in C#, Java, Kotlin, Scala, and
PHP. For those languages `ModuleIndex` also resolves capitalized identifiers in comment- and
string-free code against the project's type names, counting only names declared exactly once and at
least three characters long, never the file's own names.

### 6.8 Outputs

`.clean/structure.md`, ordered so that a partial read still gets the most important part first:

1. **Header**: generator, date, git commit, packs used, counts, truncation note.
2. **Findings**: a counts table, then one bullet list per kind, capped at `--top` (default 25) with
   "... and N more in structure.json".
3. **Tree**: a table of folders (path, role, files, symbols, findings), sorted by path, at most 200
   rows.
4. **Components**: the metrics table sorted by D, the cycles, and a Mermaid graph of at most 25
   components chosen by degree.
5. **Files**: one row per non-test source file — path, role, up to eight symbols with flagged ones
   marked `!`, purpose — sorted by path so a grep for a path returns its row.

`.clean/structure.json` holds the same data, uncapped: `schema_version`, `generated`, `commit`,
`root`, `packs`, `truncated`, `files` (each with `symbols`), `findings`, `components`, `edges`.

CLI: `map_structure.py [--root DIR] [--write] [--json] [--path SUBDIR] [--depth N] [--top N]
[--packs LIST]`. By default it prints a terminal summary of about 40 lines. `--path` prints that
subtree's file rows and findings. `--write` writes both files under `<root>/.clean/`. Exit 0 on
success, 2 on a usage or roles error. Packs come from `--packs`, else `.clean/context.json`, else
live detection through `detect_stack`.

### 6.9 Performance

One walk through `project_files.walk`, with its skip rules and 40,000-file cap; each file read once;
patterns compiled at import; every finding linear except duplicate grouping, which uses hash maps.
Target: under 10 seconds for 5,000 files on a laptop, measured on this repository and on a real .NET
solution before release.

## 7. Eval Harness

Repository only; the installer never copies it.

```text
evals/
  README.md        how to run with skill-creator, how to grade, how to record results
  evals.json       skill-creator format: id, prompt, expected_output, files, expectations
  triggers.json    should-trigger and should-not-trigger queries for description tuning
  grade.py         standard-library grader; --self-test validates every case
  cases/<id>/      case.json (machine-checkable expectations) and repo/ (a tiny fixture project)
```

Expectation types, checked against the finished workspace: `file_exists`, `file_contains`,
`file_not_contains`, `unchanged`, `no_new_files`, `map_finding_absent` (runs `map_structure.py`),
and `transcript_reads` (needs a transcript, otherwise reported as skipped). Output follows
skill-creator's `grading.json` shape: `expectations` entries of text, passed, and evidence, plus a
summary.

Cases (33): one per framework pack (21); one per language without a framework pack — C, C++, Rust,
Shell, PowerShell, R, Scala, Objective-C (8); four core cases — the context gate reads the packs
before the first edit, declared layers keep the domain free of framework imports, `init` writes
context and the structure map, and no sibling-variant file appears.

CI runs `grade.py --self-test` only. Model runs happen at release time through skill-creator, and
their results are recorded in `evals/README.md`. v4.0.0 ships after a with-skill versus
without-skill run over a representative subset: the four core cases and at least six packs spanning
frontend, backend, mobile, and systems work.

## 8. README And Docs

README of at most 150 lines: banner and badges, a one-paragraph pitch, why (three bullets), install
(two one-liners plus the plugin and skills-CLI lines), use (a commands table — `init`, `audit`,
`clean-up`, `new-project` — and three example prompts), what you get (rules, packs by name,
structure map, boundary check, `.clean/` memory), optional enforcement (four lines),
update and uninstall (two lines), documentation links, license.

The host table, profiles, global mode, and environment variables move to `docs/install.md`. The
`.clean/` formats, the roles override, and hooks move to `docs/configuration.md`. Validation and
releases stay in `CONTRIBUTING.md`, which also gains "Writing a pack" with the templates from §5.2
and §5.3. Manifest descriptions name `init`, the packs, and the structure map. `CHANGELOG.md` gains
4.0.0.

## 9. Validation, Tests, CI

`validate.sh` adds:

- pack headings, order, and budget;
- index, pack files, and detectable labels agree;
- every `clean-roles` block parses;
- `SKILL.md` at most 3,000 tokens; the managed block at most 1,200 tokens;
- reference files over 300 lines open with a contents list;
- scripts parse under the Python 3.8 grammar (`ast.parse(..., feature_version=(3, 8))`);
- the allowed sibling modules are derived from the scripts folder instead of a fixed list;
- `evals/` never appears inside the skill folder;
- `init.md` replaces `questions.md` among the required files;
- `python -m unittest discover -s tests` when Python is available.

`tests/` (unittest, standard library): symbols per language; imports and `ModuleIndex` per
language; the roles grammar and its precedence; each finding kind; metrics and cycles; the map end
to end on a temporary Express-like fixture, where the `authMiddleware` case must surface as
Misplaced; `detect_stack` routing and signatures.

`ci.yml` gains, in the skill-tools job: the unit tests, `map_structure.py` on this repository, and
`grade.py --self-test`.

## 10. Phases And Acceptance

| Phase | Delivers | Done when |
| --- | --- | --- |
| 1 Scanner | §6 modules and tests | unit tests green; the `check_boundaries` CI table unchanged; the map runs on this repository and a .NET solution |
| 2 Pack infrastructure | index, generic roles, routing, validator checks, templates in `CONTRIBUTING.md` | tests green; `detect_stack.py` prints "Read next" |
| 3 Core | §4 | `SKILL.md` at most 3,000 tokens; `sync.sh` leaves the tree clean; `validate.sh` green |
| 4 Pilot packs | `typescript`, `javascript`, `react` | template confirmed or amended |
| 5 Packs | the remaining 37 packs and their sources | validator green; originality check clean |
| 6 Evals | §7 and the subset run | self-test green; results recorded |
| 7 Docs and release preparation | §8, VERSION 4.0.0, sync | README at most 150 lines; `validate.sh` green |
| 8 Verification | validator, tests, markdownlint, scanners on real repositories | evidence quoted in the handoff |

Nothing is pushed, tagged, or released without the user's explicit go-ahead.

## 11. Risks

| Risk | Mitigation |
| --- | --- |
| Framework facts drift or are wrong | versions stated per pack; verified against official docs; sources recorded; agents still verify against `context.json` versions |
| Regex extraction misses constructs | evidence-not-verdict framing; per-language unit tests; anything unrecognised is skipped, never guessed |
| Misplaced and mixed findings are noisy in flat projects | only role-bearing symbols count; interfaces and types are exempt; home roles; `ignore-name`; suggestions, never automatic moves |
| Forty packs inflate the install | packs load on demand; about 60k tokens on disk, about 3k to 6k per session |
| Framework-first weakens architectural guarantees | layer rules stay strict when declared; `init` and `new-project` offer the declaration; the boundary hook is unchanged |
| Book text leaks into packs | n-gram comparison against the gitignored books before each commit |
| CRLF from Windows tooling | `git ls-files --eol` before each commit; the validator gate |
