# v4.0.0 Packs, Structure Map, Lean Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship clean-code-skills 4.0.0: 19 language and 21 framework packs routed by stack detection, a structure-map scanner that shows what every file and symbol is for and where it belongs, a lean context-first core, an eval harness, and a short README.

**Architecture:** One skill. Packs are on-demand references under `skills/clean-code/references/{languages,frameworks}/`, indexed by a `clean-packs` block in `framework-map.md` that `detect_stack.py` reads. A new scanner (`map_structure.py` plus five focused modules) extracts symbols, assigns roles from `clean-roles` blocks, and writes `.clean/structure.md` and `.clean/structure.json`. `SKILL.md` becomes a 3,000-token router with a context gate.

**Tech Stack:** Python 3.8+ standard library (scanners, tests, grader), Markdown (skill content), Bash (validator, sync), GitHub Actions (CI).

**Spec:** `docs/superpowers/specs/2026-09-23-v4-packs-structure-map-design.md`. Read it before any task.

## Global Constraints

- Skill scripts import only the standard library and sibling modules; the validator rejects anything else.
- Python 3.8 compatible: no `match`, no `str.removeprefix`, no `functools.cache`, no `dict | dict`, no `zip(strict=)`; built-in generics only inside annotations under `from __future__ import annotations`.
- Scanners read files and write only under `<root>/.clean/`, only when `--write` is passed; never touch the network.
- Committed files are LF with a final newline. Run `git ls-files --eol <paths>` before every commit; the index column must read `i/lf`.
- Never commit book text. `books/` stays gitignored. Canon names and smell IDs are allowed; prose is original.
- No absolute machine paths in `skills/` or `templates/` Markdown.
- markdownlint: `MD013` off; every fenced block names a language; headings and lists surrounded by blank lines.
- Budgets, measured as words × 4 / 3: `SKILL.md` at most 3,000 tokens and 500 lines; managed block at most 1,200 tokens; each pack at most 2,000 tokens.
- Never hand-edit the managed block inside an adapter; edit `templates/agent-block.md` and run `bash scripts/sync.sh`.
- Never `git add -A`; stage explicit paths. The working tree holds ignored vendored copies.
- Unit tests: `python -m unittest discover -s tests -v` from the repository root. Validator: `bash scripts/validate.sh` (Git Bash on Windows).
- Nothing is pushed, tagged, or released without the user's explicit approval.

## Execution Notes

- **Deliberate deviation from "complete code in every step".** The same session writes the plan and executes it, and the scanner is roughly 3,000 lines. Writing every body twice would double the cost without adding a decision. This plan therefore pins down every interface, every test case (input and expected output), every command, and every commit, and the code is written once, test-first, during execution.
- Tasks 1–17 and 20–23 run inline. Tasks 18–19 (packs and their eval cases) are dispatched to parallel subagents in batches, each followed by a review before its index lines are added.

## File Structure

| Path | Responsibility | Task |
| --- | --- | --- |
| `skills/clean-code/scripts/project_files.py` | + `glob_match`, `literal_weight` | 1 |
| `skills/clean-code/scripts/project_imports.py` | import extraction (moved) + `ModuleIndex` | 2, 7 |
| `skills/clean-code/scripts/check_boundaries.py` | imports `project_imports`; behavior unchanged | 2 |
| `skills/clean-code/scripts/source_lexer.py` | blank comments and strings, keep offsets | 3 |
| `skills/clean-code/scripts/project_symbols.py` | symbols per language | 3–6 |
| `skills/clean-code/scripts/structure_roles.py` | `clean-roles` parsing, role assignment | 8 |
| `skills/clean-code/scripts/structure_findings.py` | misplaced, mixed, duplicates, name clashes, synonyms | 9 |
| `skills/clean-code/scripts/component_metrics.py` | components, Ca/Ce/I/A/D, cycles | 10 |
| `skills/clean-code/scripts/map_structure.py` | CLI and rendering | 11 |
| `skills/clean-code/scripts/detect_stack.py` | + pack routing, signatures, source signatures | 13 |
| `skills/clean-code/references/framework-map.md` | pack index, generic roles, idioms, fallback | 12, 18, 20 |
| `skills/clean-code/references/languages/*.md` | 19 language packs | 18, 19 |
| `skills/clean-code/references/frameworks/*.md` | 21 framework packs | 18, 19 |
| `skills/clean-code/SKILL.md` | router with context gate | 16 |
| `skills/clean-code/references/init.md` | renamed from `questions.md` | 17 |
| `skills/clean-code/references/review-checklist.md` | + self-check tables | 16 |
| `templates/agent-block.md` + 8 adapters | managed block | 17 |
| `tests/*.py` | unittest suites | 1–15 |
| `evals/` | grader, cases, triggers, results | 15, 18, 19, 21 |
| `docs/install.md`, `docs/configuration.md`, `docs/pack-sources.md` | moved and new docs | 18, 19, 22 |
| `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `CONTEXT.md`, `VERSION`, manifests | release surface | 14, 17, 22 |
| `scripts/validate.sh`, `.github/workflows/ci.yml` | gates | 14, 15, 16, 17 |

(`source_lexer.py` is a sixth scanner module the spec did not name: the brace-matching lexer is shared by symbol extraction and fingerprinting, and it is large enough to deserve its own file.)

---

## Phase 1 — Scanner

### Task 1: Glob matching in the project walker

**Files:**

- Modify: `skills/clean-code/scripts/project_files.py`
- Test: `tests/test_project_files.py`

**Interfaces:**

- Produces: `glob_match(pattern: str, relative_path: str) -> bool` — case-insensitive; `**/` matches zero or more directories, `/**` at the end matches everything below, `*` stays inside one segment, `?` is one non-slash character; backslashes in the pattern count as slashes. `literal_weight(pattern: str) -> int` — the number of characters that are not `*`, `?`, or `/` (specificity for home-role ties).

- [ ] **Step 1: Write the failing tests** — `tests/test_project_files.py` with `sys.path.insert(0, <repo>/skills/clean-code/scripts)` and these cases:

| pattern | path | expected |
| --- | --- | --- |
| `**/middleware/**` | `middleware/auth.ts` | True |
| `**/middleware/**` | `src/middleware/auth.ts` | True |
| `**/middleware/**` | `src/mymiddleware/auth.ts` | False |
| `**/*.middleware.*` | `src/auth.middleware.ts` | True |
| `**/*Controller.*` | `src/Web/UserController.cs` | True |
| `middleware.ts` | `middleware.ts` | True |
| `middleware.ts` | `src/middleware.ts` | False |
| `app/Http/Middleware/**` | `app/http/middleware/Auth.php` | True |
| `src/*.ts` | `src/a/b.ts` | False |
| `src\**` | `src/a/b.ts` | True |

  Plus `literal_weight("**/middleware/**") == 10` and `literal_weight("**/*.middleware.*") == 12`.

- [ ] **Step 2: Run to confirm failure** — `python -m unittest tests.test_project_files -v`; expected: `AttributeError: module 'project_files' has no attribute 'glob_match'`.
- [ ] **Step 3: Implement** — translate the glob to an anchored regex once per pattern (`functools.lru_cache(maxsize=None)`), lowercase both sides.
- [ ] **Step 4: Run to confirm pass** — same command; expected: `OK`.
- [ ] **Step 5: Commit** — `git add skills/clean-code/scripts/project_files.py tests/test_project_files.py && git commit -m "Add glob matching with ** to the project walker"`.

### Task 2: Move import parsing into `project_imports.py`

**Files:**

- Create: `skills/clean-code/scripts/project_imports.py`
- Modify: `skills/clean-code/scripts/check_boundaries.py` (delete `IMPORT_PATTERNS`, `COMPILED_IMPORT_PATTERNS`, `RESOLVABLE_SUFFIXES`, `resolve_relative_import`, `extract_imports`; import them)
- Test: `tests/test_project_imports.py`

**Interfaces:**

- Produces (moved verbatim, same behavior): `IMPORT_PATTERNS`, `COMPILED_IMPORT_PATTERNS`, `RESOLVABLE_SUFFIXES`, `resolve_relative_import(source_path, module, exists) -> str | None`, `extract_imports(path: Path)` yielding `(line_number, module, line_text)`.
- Produces (new): `imports_in_text(suffix: str, text: str) -> list[tuple[int, str]]` — pure; `extract_imports` delegates to it.
- New extraction patterns: `.mts`/`.cts` as `.ts`; `.m`/`.mm` `#import`/`#include` and `@import X;`; `.hh`/`.cxx` includes; `.sh`/`.bash`/`.zsh` `source X` and `. X`; `.ps1`/`.psm1` dot-sourcing, `Import-Module X`, `using module X`; `.r` `source("X")`, `library(X)`, `require(X)`.
- `check_boundaries.py` keeps `parse_layering`, `Layering`, `check_project`, CLI; `Layering.layer_of_import` calls `project_imports.resolve_relative_import`.

- [ ] **Step 1: Failing tests** — `imports_in_text` cases:

| suffix | text | expected |
| --- | --- | --- |
| `.ts` | `import { a } from '../x';` | `[(1, '../x')]` |
| `.py` | `from ..infra.db import Db` | `[(1, '..infra.db')]` |
| `.go` | `import (\n  "fmt"\n  x "example.com/app/internal/auth"\n)` | `[(2, 'fmt'), (3, 'example.com/app/internal/auth')]` |
| `.sh` | `source "$DIR/lib/log.sh"` | `[(1, '$DIR/lib/log.sh')]` |
| `.ps1` | `. $PSScriptRoot\Private\Get-Thing.ps1` | `[(1, '$PSScriptRoot\\Private\\Get-Thing.ps1')]` |
| `.r` | `source("R/clean.R")\nlibrary(dplyr)` | `[(1, 'R/clean.R'), (2, 'dplyr')]` |
| `.m` | `#import "OrderService.h"` | `[(1, 'OrderService.h')]` |

  And the existing CI classification table from `.github/workflows/ci.yml` (step "check_boundaries places imports the same way for paths and module names") copied into `tests/test_check_boundaries.py` unchanged.

- [ ] **Step 2: Confirm failure** — `python -m unittest tests.test_project_imports tests.test_check_boundaries -v`; expected: `ModuleNotFoundError: No module named 'project_imports'`.
- [ ] **Step 3: Implement** — move the code; add `imports_in_text`; add the patterns; point `check_boundaries.py` at the module.
- [ ] **Step 4: Confirm pass** — the unittest command, plus the three existing CI shell steps for `check_boundaries.py` run by hand in Git Bash (violation exits 1, no-match exits 2, pass exits 0).
- [ ] **Step 5: Commit** — `"Move import parsing into project_imports and read Shell, PowerShell, R, Objective-C imports"`.

### Task 3: Lexer and symbols for Python, JavaScript, TypeScript, Vue, Svelte

**Files:**

- Create: `skills/clean-code/scripts/source_lexer.py`, `skills/clean-code/scripts/project_symbols.py`
- Test: `tests/test_source_lexer.py`, `tests/test_project_symbols.py`

**Interfaces:**

- `source_lexer.strip(text: str, family: str) -> Stripped` with `Stripped = NamedTuple(code: str, no_comments: str)`: `code` has comments and string contents replaced by spaces, `no_comments` has only comments replaced; newlines and offsets preserved in both. Families: `c` (`//`, `/* */`, `"`, `'` char literals, JS backticks, triple quotes, C# `@"…"`, Rust raw strings and lifetimes, Go backticks), `hash` (`#` comments, `'` and `"` strings, heredocs for Shell, `<# #>` and here-strings for PowerShell, `#[` kept as code for PHP attributes), `python`.
- `source_lexer.match_braces(code: str) -> dict[int, int]` — open-brace offset to close-brace offset.
- `project_symbols.Symbol` NamedTuple: `name, kind, line, end_line, exported, parent, doc, context, exact, shape` (`kind` ∈ class, interface, enum, struct, trait, protocol, record, type, object, module, function, method, component, constant; `parent` is the enclosing type or `None`; `exact` and `shape` are 16-hex fingerprints or `None`).
- `project_symbols.FileSymbols` NamedTuple: `path, language, purpose, lines, symbols, types, abstract_types`.
- `project_symbols.SUPPORTED_SUFFIXES: frozenset[str]`; `project_symbols.language_of(path) -> str | None`; `project_symbols.extract(path: str, text: str) -> FileSymbols | None`.
- `project_symbols.TYPE_KINDS = {"class", "interface", "enum", "struct", "trait", "protocol", "record", "object"}` and `ABSTRACT_KINDS = {"interface", "trait", "protocol"}` (abstract classes are flagged by kind `class` plus an `abstract` marker inside `context`, counted in `abstract_types`).

- [ ] **Step 1: Failing tests** — lexer: a `//` comment containing `{` does not count in `match_braces`; a string `"}"` does not either; a JS template literal with `${}` is blanked; offsets equal in `code` and input. Symbols:

| file | source | expected symbols (name, kind, exported, parent) |
| --- | --- | --- |
| `a.py` | `class Repo(ABC):\n    @abstractmethod\n    def get(self): ...\ndef _helper(): pass\ndef load_user(): pass` | `Repo` class exported; `get` method parent `Repo`; `_helper` function not exported; `load_user` function exported; `abstract_types == 1` |
| `auth.ts` | `export class AuthService {\n  verify(t: string) { return t; }\n}\nexport const authMiddleware = (req, res, next) => { next(); };\nfunction local() {}` | `AuthService` class exported; `verify` method parent `AuthService`; `authMiddleware` function exported, `context` contains `(req, res, next)`; `local` function not exported |
| `types.ts` | `export interface User { id: string }\nexport type Id = string;\nexport enum Role { A }` | interface, type, enum, all exported |
| `legacy.js` | `module.exports.requireAdmin = function (req, res, next) { next(); };` | `requireAdmin` function exported |
| `Button.vue` | `<template><b/></template>\n<script setup lang="ts">\nconst x = 1\n</script>` | `Button` component exported, `language == "vue"` |
| `svc.py` | a six-line function body duplicated verbatim in another function with a different name | both get the same `exact`; both get the same `shape` |

  Docs: `"""Loads users."""` becomes `doc == "Loads users."`; a JSDoc `/** Verifies tokens. More text. */` above a function becomes `doc == "Verifies tokens."`; a module docstring becomes `purpose`; a license header (`// Copyright ...`) is skipped for `purpose`.

- [ ] **Step 2: Confirm failure** — `python -m unittest tests.test_source_lexer tests.test_project_symbols -v`; expected: `ModuleNotFoundError`.
- [ ] **Step 3: Implement** — Python via `ast` (`end_lineno`, `get_docstring`, decorators, `__all__`); JS/TS via declaration regexes over `code` with `match_braces` extents; methods detected inside class bodies with a keyword exclusion list; Vue/Svelte extract `<script>` blocks, re-offset lines, add the component symbol named from the file stem in PascalCase.
- [ ] **Step 4: Confirm pass.**
- [ ] **Step 5: Commit** — `"Extract symbols from Python, JavaScript, TypeScript, Vue, and Svelte"`.

### Task 4: Symbols for Java, Kotlin, Scala, C#, PHP, Dart

**Files:** Modify `project_symbols.py`; extend `tests/test_project_symbols.py`.

**Interfaces:** same `extract`; namespace and package blocks are transparent (their braces do not make contents non-top-level).

- [ ] **Step 1: Failing tests:**

| file | source (abridged) | expected |
| --- | --- | --- |
| `UserController.java` | `@RestController\npublic class UserController {\n  public List<User> all() { return List.of(); }\n}` | `UserController` class, `context` contains `@RestController`; `all` method |
| `Port.java` | `public interface OrderPort { void save(Order o); }` | interface; `save` method without fingerprint |
| `Svc.kt` | `@Service\nclass OrderService(private val repo: Repo) {\n  suspend fun place(o: Order) { repo.save(o) }\n}\nfun String.slug() = lowercase()\ninternal object Cache` | `OrderService` class; `place` method; `slug` function exported; `Cache` object exported |
| `Model.scala` | `sealed trait Shape\ncase class Circle(r: Double) extends Shape\nobject Shape { def unit: Shape = Circle(1) }` | `Shape` trait (abstract); `Circle` class; `Shape` object; `unit` method |
| `Orders.cs` | `namespace App.Web {\n  [ApiController]\n  public sealed class OrdersController : ControllerBase {\n    public async Task<IActionResult> Get(CancellationToken ct) { return Ok(); }\n  }\n}` | `OrdersController` class top-level despite the namespace block, `context` contains `[ApiController]` and `ControllerBase`; `Get` method |
| `File.cs` | `namespace App.Domain;\npublic record Money(decimal Amount);\npublic interface IClock { DateTime Now { get; } }` | `Money` record; `IClock` interface |
| `Auth.php` | `<?php\nnamespace App\Http\Middleware;\n#[Attr]\nfinal class Authenticate {\n  public function handle($request, Closure $next) { return $next($request); }\n}` | `Authenticate` class, `context` contains `#[Attr]`; `handle` method |
| `widget.dart` | `class LoginPage extends StatelessWidget {\n  const LoginPage({super.key});\n  @override\n  Widget build(BuildContext context) { return Text(''); }\n}\nabstract interface class AuthRepo { Future<User> login(); }\nString _hidden() => '';` | `LoginPage` class, `context` contains `StatelessWidget`; `build` method; `AuthRepo` counted abstract; `_hidden` not exported |

- [ ] **Step 2: Confirm failure.** - [ ] **Step 3: Implement.** - [ ] **Step 4: Confirm pass.**
- [ ] **Step 5: Commit** — `"Extract symbols from Java, Kotlin, Scala, C#, PHP, and Dart"`.

### Task 5: Symbols for Go, Rust, Swift, C, C++, Objective-C

**Files:** Modify `project_symbols.py`; extend tests.

- [ ] **Step 1: Failing tests:**

| file | source (abridged) | expected |
| --- | --- | --- |
| `auth.go` | `// AuthMiddleware checks tokens.\nfunc AuthMiddleware(next http.Handler) http.Handler { return next }\ntype Store interface { Get(id string) (User, error) }\nfunc (s *userStore) Get(id string) (User, error) { return User{}, nil }\nfunc helper() {}` | `AuthMiddleware` function exported, `doc == "AuthMiddleware checks tokens."`; `Store` interface; `Get` method parent `userStore`; `helper` not exported |
| `lib.rs` | `pub trait Repo { fn get(&self) -> u8; }\npub struct Pg;\nimpl Repo for Pg { fn get(&self) -> u8 { 1 } }\nfn private() {}\n#[cfg(test)]\nmod tests { #[test] fn t() {} }` | `Repo` trait; `Pg` struct; `get` method parent `Pg`; `private` not exported; nothing from `mod tests` |
| `View.swift` | `struct ContentView: View {\n  var body: some View { Text("") }\n}\nprotocol Clock { func now() -> Date }\nextension ContentView { func refresh() {} }\nprivate func hidden() {}` | `ContentView` struct, `context` contains `: View`; `Clock` protocol; `refresh` method parent `ContentView`; no symbol named by the extension; `hidden` not exported |
| `list.c` | `static int grow(list *l) {\n  return 0;\n}\nint list_push(list *l, int v) {\n  return grow(l);\n}` | `grow` not exported; `list_push` exported |
| `list.h` | `typedef struct list list;\nint list_push(list *l, int v);` | no symbols (declarations only) |
| `shape.cpp` | `namespace geo {\nclass Shape {\npublic:\n  virtual double area() const = 0;\n};\ndouble Circle::area() const { return 1; }\n}` | `Shape` class counted abstract; `area` method parent `Circle` |
| `Svc.m` | `@interface OrderService : NSObject\n- (void)place:(Order *)o;\n@end\n@implementation OrderService\n- (void)place:(Order *)o { }\n@end` | `OrderService` class; `place` method parent `OrderService` |

- [ ] **Steps 2–4** as before. - [ ] **Step 5: Commit** — `"Extract symbols from Go, Rust, Swift, C, C++, and Objective-C"`.

### Task 6: Symbols for Ruby, Shell, PowerShell, R

**Files:** Modify `project_symbols.py`; extend tests.

- [ ] **Step 1: Failing tests:**

| file | source (abridged) | expected |
| --- | --- | --- |
| `order.rb` | `# Places orders.\nclass OrderService < BaseService\n  def call(order)\n    save(order)\n  end\nend\nmodule Billing\n  def self.charge; end\nend` | `OrderService` class, `context` contains `< BaseService`, `doc == "Places orders."`; `call` method parent `OrderService`; `Billing` module; `charge` method |
| `deploy.sh` | `#!/usr/bin/env bash\n# Deploys the app.\nlog() {\n  echo "$1" >&2\n}\nfunction main {\n  cat <<EOF\n}\nEOF\n  log hi\n}` | `log` and `main` functions; the heredoc brace does not end `main` early (`end_line` is the last line) |
| `Tools.psm1` | `function Get-Thing {\n  <#\n  .SYNOPSIS\n  Returns things.\n  #>\n  [CmdletBinding()] param()\n}\nclass Cache { [string] Get([string]$k) { return $k } }` | `Get-Thing` function, `doc == "Returns things."`; `Cache` class; `Get` method parent `Cache` |
| `clean.R` | `#' Clean the data.\n#' @param df a frame\nclean_data <- function(df) {\n  df\n}\nsetClass("Person", representation(name = "character"))` | `clean_data` function, `doc == "Clean the data."`; `Person` class |

- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Extract symbols from Ruby, Shell, PowerShell, and R"`.

### Task 7: Module index and import resolution

**Files:** Modify `project_imports.py`; extend `tests/test_project_imports.py`.

**Interfaces:**

- `ModuleIndex(root: Path)`; `add(path: str, text: str, symbols: FileSymbols | None) -> None` during the single walk; `finish() -> None` once; `resolve(source_path: str, module: str) -> list[str]` (project files, sorted, `[]` for external or unknown); `resolve_type_references(source_path: str) -> list[str]` (files declaring capitalized names used in this file's comment- and string-free code; only for C#, Java, Kotlin, Scala, Swift, Ruby, PHP; only names declared once and at least three characters; never the file itself).
- Reads `tsconfig.json`/`jsconfig.json` (JSON with comments and trailing commas tolerated), `go.mod`, `pubspec.yaml` from `root`.

- [ ] **Step 1: Failing tests** — each builds an index over an in-memory file set:

| language | files | source, import | expected |
| --- | --- | --- | --- |
| TS relative | `src/a.ts`, `src/lib/index.ts` | `src/a.ts`, `./lib` | `['src/lib/index.ts']` |
| TS alias | `tsconfig.json` with `"paths": {"@/*": ["src/*"]}` (a comment and a trailing comma inside), `src/util/date.ts` | `src/a.ts`, `@/util/date` | `['src/util/date.ts']` |
| Python dotted | `app/services/auth.py`, `app/api/routes.py` | `app/api/routes.py`, `app.services.auth` | `['app/services/auth.py']` |
| Python package | `app/services/__init__.py` | `app/api/routes.py`, `app.services` | `['app/services/__init__.py']` |
| Java | `src/main/java/com/acme/order/OrderService.java` (`package com.acme.order;`) | any, `com.acme.order.OrderService` | that file |
| C# | `Core/Orders/Order.cs` (`namespace Acme.Core.Orders;`) | `Web/Api.cs`, `Acme.Core.Orders` | `['Core/Orders/Order.cs']` |
| PHP | `app/Services/Billing.php` (`namespace App\Services; class Billing`) | any, `App\Services\Billing` | that file |
| Go | `go.mod` (`module example.com/app`), `internal/auth/auth.go`, `internal/auth/auth_test.go` | `cmd/api/main.go`, `example.com/app/internal/auth` | `['internal/auth/auth.go']` |
| Rust | `src/lib.rs`, `src/domain/order.rs` | `src/lib.rs`, `crate::domain::order::Order` | `['src/domain/order.rs']` |
| Dart | `pubspec.yaml` (`name: shop`), `lib/src/cart.dart` | `lib/main.dart`, `package:shop/src/cart.dart` | `['lib/src/cart.dart']` |
| C include | `include/geo/shape.h`, `src/shape.c` | `src/shape.c`, `geo/shape.h` | `['include/geo/shape.h']` |
| Shell | `scripts/lib/log.sh`, `scripts/deploy.sh` | `scripts/deploy.sh`, `"$(dirname "$0")/lib/log.sh"` | `['scripts/lib/log.sh']` |
| External | — | `src/a.ts`, `react` | `[]` |
| Type refs | Swift `Sources/App/Cart.swift` declares `Cart`, `Sources/App/CheckoutView.swift` uses `Cart()` in code and `Cart` in a comment | `resolve_type_references('Sources/App/CheckoutView.swift')` | `['Sources/App/Cart.swift']` |
| Ambiguous | two files declare `User` | a third file uses `User` | `[]` |

- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Resolve imports and type references to project files"`.

### Task 8: Roles grammar and assignment

**Files:** Create `skills/clean-code/scripts/structure_roles.py`; test `tests/test_structure_roles.py`.

**Interfaces:**

- `class RolesError(Exception)`.
- `Statement` NamedTuple: `kind` (`role`, `name`, `signal`, `ignore-name`), `role`, `suffixes` (tuple of lowercase extensions without dots; empty means all), `value` (list of globs, or compiled regex), `source` (`"<file>:<line>"`).
- `parse_roles(text: str, source: str) -> list[Statement]` reads the first ```` ```clean-roles ```` block; raises `RolesError("<source>:<line>: <reason>")`.
- `Roles(statements_in_precedence_order)`: `home_role(path) -> str | None`; `intrinsic_role(name, context, suffix) -> str | None` (all signals in precedence order first, then all names); `is_ignored_name(name) -> bool`; `home_globs(role) -> list[str]`.
- `load_roles(skill_root: Path, packs: list[str], project_root: Path) -> Roles`: `.clean/roles.md` (optional), then framework packs in `packs` order, then `references/framework-map.md`.
- `RoledSymbol(symbol, role)`, `RoledFile(path, language, suffix, home_role, is_test, symbols, purpose, lines, types, abstract_types)`; `assign(file_symbols: FileSymbols, roles: Roles, is_test: bool) -> RoledFile`.

- [ ] **Step 1: Failing tests:**
  - Parses `role middleware = **/middleware/**, **/*.middleware.*`, `name hook = ^use[A-Z]`, `signal controller = @Controller\(`, `name component [tsx, jsx] = ^[A-Z]\w*$`, `ignore-name = ^(GET|POST)$`, blank lines and `#` comments.
  - `RolesError` naming the line for: unknown statement, bad role name `Middleware`, invalid regex `(`, suffix list on a `role` statement.
  - Precedence: a project statement `signal service = @Injectable` beats a pack statement `signal guard = @Injectable`; a pack beats the generic block.
  - Signals beat names: a symbol named `AuthService` whose context contains `implements CanActivate` gets `guard` when a pack says `signal guard = implements\s+CanActivate`.
  - Suffix filter: `name component [tsx] = ^[A-Z]` gives `component` for `Button` in `a.tsx` and `None` for `Button` in `a.go`.
  - Home role specificity: with `role service = **/services/**` and `role middleware = **/*.middleware.*`, `src/services/auth.middleware.ts` is `middleware`.

- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Parse clean-roles blocks and assign roles to files and symbols"`.

### Task 9: Findings

**Files:** Create `skills/clean-code/scripts/structure_findings.py`; test `tests/test_structure_findings.py`.

**Interfaces:**

- `ROLE_EXEMPT_KINDS = {"interface", "type", "enum", "protocol", "trait"}`.
- `EXPORT_AWARE_LANGUAGES = {"javascript", "typescript", "python", "go", "rust", "dart"}`: in these, only exported symbols are role-bearing.
- `find_misplaced(files: list[RoledFile], roles: Roles) -> list[dict]` → `{"path", "line", "symbol", "role", "home_role", "suggestion"}` (`symbol` is `None` for a whole-file move).
- `find_mixed(files) -> list[dict]` → `{"path", "roles": {role: [names]}}`.
- `find_duplicates(files) -> list[dict]` → `{"kind": "identical" | "same shape", "lines", "members": [{"path", "line", "symbol"}]}`.
- `find_name_clashes(files, roles) -> list[dict]` → `{"name", "language", "members": [{"path", "line", "kind"}]}`.
- `find_synonyms(files, roles) -> list[dict]` → `{"noun", "group", "verbs": {verb: [{"path", "line", "symbol"}]}}`.
- `SOURCE_ROOTS = {"src", "lib", "app", "source", "sources", "pkg", "internal"}`.

- [ ] **Step 1: Failing tests** (build `RoledFile` values directly):
  - `src/services/auth.ts` (home `service`) exporting `AuthService` (`service`) and `authMiddleware` (`middleware`), with `src/middleware/cors.ts` present (home `middleware`) → one misplaced finding for `authMiddleware` with suggestion `src/middleware/`.
  - Same without any middleware file, and the generic glob `**/middleware/**` → suggestion `src/middleware/`.
  - `src/auth.ts` (no home role) exporting `AuthService` and `authMiddleware` → one mixed finding with both roles.
  - `src/guards.ts` (no home role) exporting only a `guard` when `src/guards/` holds guards → whole-file misplaced, suggestion `src/guards/`.
  - A non-exported `validate` middleware in a TypeScript route file → no finding; an interface named `UserRepository` inside `models/` → no finding.
  - Two methods with equal `exact` → one `identical` group; equal `shape` only → one `same shape` group; a test file never appears.
  - `formatDate` declared in `src/a.ts` and `src/b.ts` → one name clash; `main` in two Go files → none (ignored by the generic block).
  - `getUser` ×2, `fetchUser` ×1, `loadUsers` ×1 → one synonym finding for noun `user` in group `retrieve` with verbs get, fetch, load; `getAll` and `fetchAll` → none (trivial noun).

- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Find misplaced, mixed, duplicated, clashing, and synonymous code"`.

### Task 10: Component metrics and cycles

**Files:** Create `skills/clean-code/scripts/component_metrics.py`; test `tests/test_component_metrics.py`.

**Interfaces:**

- `component_of(path: str, depth: int) -> str` (directory prefix of at most `depth` segments; `"."` for root files).
- `analyze(file_imports: dict[str, list[str]], type_counts: dict[str, tuple[int, int]], depth: int) -> dict` → `{"components": [{"name", "files", "types", "abstract_types", "ca", "ce", "instability", "abstractness", "distance"}], "edges": [{"from", "to", "count"}], "cycles": [{"components": [...], "edges": [...]}]}`; undefined metrics are `None`.

- [ ] **Step 1: Failing tests:**
  - `component_of("src/services/auth.ts", 2) == "src/services"`, `component_of("src/index.ts", 2) == "src"`, `component_of("main.go", 2) == "."`.
  - Files `a/x/1.ts → b/y/1.ts`, `b/y/1.ts → c/z/1.ts`: component `b/y` has `ca == 1`, `ce == 1`, `instability == 0.5`.
  - Types `(2, 1)` in `b/y` → `abstractness == 0.5`, `distance == 0.0`; a component with no types → `abstractness is None` and `distance is None`.
  - `a → b`, `b → a`, `c → a` → exactly one cycle, members `a` and `b` sorted.
  - An import inside one component creates no edge.

- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Compute component coupling, instability, abstractness, distance, and cycles"`.

### Task 11: `map_structure.py`

**Files:** Create `skills/clean-code/scripts/map_structure.py`; test `tests/test_map_structure.py`.

**Interfaces:**

- `build_map(root: Path, packs: list[str] | None, depth: int) -> dict` — the JSON document from spec §6.8 (`schema_version: 1`).
- `render_markdown(data: dict, top: int) -> str`; `render_summary(data: dict, path_filter: str | None) -> str`.
- `main(argv=None) -> int`; flags `--root`, `--write`, `--json`, `--path`, `--depth` (default 2), `--top` (default 25), `--packs` (comma-separated; `references/` prefix optional).
- Packs source order: `--packs`, `.clean/context.json` `packs`, `detect_stack.build_context(root)["packs"]` (Task 13 adds that key; until then treat a missing key as `[]`).

- [ ] **Step 1: Failing tests** — temporary fixture:

```text
package.json                  {"dependencies": {"express": "4.19.2"}}
src/app.js                    requires ./routes/users and ./middleware/requestId
src/routes/users.js           requires ../services/auth
src/middleware/requestId.js   module.exports = function requestId(req, res, next) { next(); }
src/services/auth.js          class AuthService {...}; function authMiddleware(req, res, next) {...}; module.exports = { AuthService, authMiddleware }
src/services/fetch.js         getUser(), fetchUser()  (synonyms)
```

  Assertions: `findings.misplaced` contains `authMiddleware` with suggestion `src/middleware/`; `findings.synonyms` has noun `user`; `render_markdown` output contains, in order, `## Findings`, `## Tree`, `## Components`, `## Files`, and a row starting `` | `src/services/auth.js` ``; `main(["--root", fixture, "--write"])` returns 0 and creates `.clean/structure.md` and `.clean/structure.json`; a malformed `.clean/roles.md` makes `main` return 2; `--path src/services` output lists `src/services/auth.js` and not `src/app.js`.

- [ ] **Step 2: Confirm failure.** - [ ] **Step 3: Implement.** - [ ] **Step 4: Confirm pass**, then run for real:
  - `python skills/clean-code/scripts/map_structure.py --root .` on this repository;
  - `time python skills/clean-code/scripts/map_structure.py --root "d:/Development/Inklusit/Inklusit.Core"` (read-only; never `--write` there); record file count and seconds (target under 10 s for 5,000 files).
- [ ] **Step 5: Commit** — `"Add map_structure: one map of every file, symbol, role, and misplacement"`.

## Phase 2 — Pack Infrastructure

### Task 12: Pack index and generic roles in `framework-map.md`

**Files:** Modify `skills/clean-code/references/framework-map.md`.

- [ ] **Step 1:** Keep "Universal Rule", "Dependencies And Package Idioms", "Adaptation Questions" (now framed as the fallback for stacks without a pack). Replace the language and framework tables with: a short "Packs" section explaining the index and the load rule; the `clean-packs` block (at this point only lines for packs that exist — none yet, so the block holds a comment line); a "Roles" section with the generic `clean-roles` block:

```text
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
role handler = **/handlers/**
name handler = Handler$
role config = **/config/**, **/configuration/**
ignore-name = ^(main|index|init|setup|run|handler|default|app|App|Program|Startup|Main|Meta|Config|Settings|create_app)$
```

- [ ] **Step 2:** `python -c` parse check: `structure_roles.parse_roles(open(...).read(), "framework-map.md")` returns statements; `map_structure.py --root <Task 11 fixture>` still reports the misplaced `authMiddleware` using only the generic block.
- [ ] **Step 3: Commit** — `"Turn framework-map into the pack index and the generic role conventions"`.

### Task 13: Pack routing and new signatures in `detect_stack.py`

**Files:** Modify `skills/clean-code/scripts/detect_stack.py`; test `tests/test_detect_stack.py`.

**Interfaces:**

- `PackIndex` NamedTuple: `languages: dict[str, list[str]]`, `frameworks: dict[str, list[str]]`, `supersedes: dict[str, set[str]]`.
- `parse_pack_index(text: str) -> PackIndex` (raises `ValueError` naming the line); `load_pack_index(path=PACK_INDEX_PATH) -> PackIndex | None`.
- `select_packs(languages: dict[str, int], frameworks: list[str], index: PackIndex) -> list[str]` — paths prefixed `references/`.
- `scan_source_signatures(root: Path, files) -> list[str]`.
- `EMITTABLE_LANGUAGES: frozenset[str]`, `EMITTABLE_FRAMEWORKS: frozenset[str]`.
- `build_context` adds `packs` (and `packs_note` when the index is missing); `render_summary` adds `Read next        : ...`.
- New `FRAMEWORK_SIGNATURES`: `("@sveltejs/kit", "SvelteKit")`, `("@strapi/strapi", "Strapi")`, `("beego", "Beego")`, `("org.springframework", "Spring")`, `("microsoft.net.sdk.web", "ASP.NET Core")`, `("androidx.compose", "Jetpack Compose")`, `("io.ktor", "Ktor")`, `("ktor-server", "Ktor")`, `("ktor.server", "Ktor")`. New manifest: `"libs.versions.toml": ("Gradle version catalog", "gradle test")`.

- [ ] **Step 1: Failing tests:**
  - `parse_pack_index` on a block with a language line, a framework line with two paths, a supersede line; a malformed line raises `ValueError` mentioning it.
  - `select_packs({"TypeScript": 90, "JavaScript": 8, "Shell": 2}, ["Express", "NestJS"], idx)` with `supersede NestJS > Express` → TypeScript packs, then NestJS pack; no Shell pack (2%), no Express pack.
  - `select_packs({"SQL": 50, "C#": 40}, [], idx)` → the C# pack (SQL is not indexed, C# is the most common indexed language).
  - Signatures: a `package.json` with `"@sveltejs/kit"` → SvelteKit; `.csproj` with `Sdk="Microsoft.NET.Sdk.Web"` → ASP.NET Core; `build.gradle.kts` with `implementation(libs.ktor.server.core)` → Ktor; `go.mod` with `github.com/beego/beego/v2 v2.3.0` → Beego.
  - `scan_source_signatures` finds SwiftUI from `import SwiftUI` in a `.swift` file and UIKit from `#import <UIKit/UIKit.h>` in a `.m` file.
  - `build_context` on a fixture with the real index returns a `packs` list; with a missing index returns `packs == []` and a `packs_note`.
  - The existing CI step "detect_stack --write merges instead of clobbering" copied into this file.

- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Route detected stacks to packs and detect SvelteKit, Strapi, Beego, Spring, ASP.NET Core SDK, Compose, Ktor, SwiftUI, UIKit"`.

### Task 14: Pack and content checks, validator wiring, pack templates

**Files:**

- Create: `tests/test_skill_content.py`
- Modify: `scripts/validate.sh`, `CONTRIBUTING.md`

**Interfaces:** `tests/test_skill_content.py` asserts, for every file in `references/languages/` and `references/frameworks/`:

- the required headings of spec §5.2 or §5.3 appear in order (`Concurrency` optional);
- the line after the title is a blockquote starting `> Applies to:`;
- words × 4 / 3 ≤ 2,000;
- framework packs contain exactly one `clean-roles` block that `structure_roles.parse_roles` accepts;
- every pack is indexed, every indexed path exists, every index label is in `detect_stack.EMITTABLE_LANGUAGES | EMITTABLE_FRAMEWORKS`;
- every top-level reference over 300 lines has a `## Contents` heading within its first 30 lines.

- [ ] **Step 1:** Write the tests (the TOC test fails for `architecture.md` and `chapter-map.md` until Task 16; mark nothing as skipped — Task 16 runs before the next commit of this file's dependents).
- [ ] **Step 2:** `validate.sh`: derive the allowed sibling modules from the scripts folder (`{p.stem for p in root.glob("*.py")}`); add the Python 3.8 grammar check (`ast.parse(src, feature_version=(3, 8))`, skipping with a warning if the running Python rejects the parameter); add `evals` must not exist under `skills/clean-code/`; add `python -m unittest discover -s tests` after the script checks.
- [ ] **Step 3:** `CONTRIBUTING.md`: add "Writing a pack" — the two templates (spec §5.2, §5.3), the authoring rules (spec §5.4), how to add the index line, how to verify facts and record sources in `docs/pack-sources.md`, how to run the originality check.
- [ ] **Step 4:** Run `python -m unittest discover -s tests -v`; only the TOC test may fail at this point. Do not commit until Task 16 makes it pass; Tasks 14–16 land as one commit: `"Check packs and references in the validator; lean SKILL.md with a context gate"`.

## Phase 3 — Eval Harness Infrastructure

### Task 15: Grader, case schema, core cases

**Files:**

- Create: `evals/grade.py`, `evals/README.md`, `evals/cases/core-*/case.json` and `evals/cases/core-*/repo/**`
- Modify: `.github/workflows/ci.yml` (skill-tools job: unit tests, `map_structure.py --root .`, `python evals/grade.py --self-test`)
- Test: `tests/test_grade.py`

**Interfaces:**

- `python evals/grade.py --case DIR --workspace DIR [--transcript FILE] [--output FILE]` → writes skill-creator-shaped JSON: `{"expectations": [{"text", "passed", "evidence"}], "summary": {"passed", "failed", "skipped", "total", "pass_rate"}}`; skipped expectations carry `"passed": null`.
- `python evals/grade.py --self-test` → validates every `evals/cases/*/case.json`, then grades each untouched fixture and requires at least one non-transcript expectation to fail (a case that passes on its own fixture tests nothing); exits 1 listing problems.
- `python evals/grade.py --export-evals FILE` → skill-creator `evals.json` (`skill_name`, `evals[]` of `id`, `prompt`, `expected_output`, `files`, `expectations` as text).
- `case.json`: `id`, `pack` (or `"core"`), `prompt`, `expected_output`, `expectations[]`. Expectation types and fields: `file_exists {glob}`, `file_contains {glob, pattern}`, `file_not_contains {glob, pattern}`, `unchanged {path}`, `no_new_files {glob}`, `map_finding_absent {kind, path?}`, `boundaries_pass {}`, `transcript_reads {pattern}`; every expectation has `text`. Globs use `project_files.glob_match`.
- Core cases: `core-context-gate`, `core-layers-declared`, `core-init`, `core-no-sibling` (spec §7).

- [ ] **Step 1: Failing tests** — `tests/test_grade.py` builds a temporary case and workspace: `file_exists` passes and fails correctly; `unchanged` detects an edit and ignores CRLF-only differences; `no_new_files` flags a new `src/pay_v2.js`; `transcript_reads` is skipped without a transcript and passes with one containing the path; `--self-test` rejects a case whose expectations all pass on the fixture.
- [ ] **Steps 2–4.** - [ ] **Step 5: Commit** — `"Add the eval grader, case schema, and four core cases"`.

## Phase 4 — Core

### Task 16: Lean `SKILL.md`, self-check tables, contents lists

**Files:** Modify `skills/clean-code/SKILL.md`, `skills/clean-code/references/review-checklist.md`, `skills/clean-code/references/architecture.md`, `skills/clean-code/references/chapter-map.md`, `scripts/validate.sh`.

- [ ] **Step 1:** Rewrite `SKILL.md` to the spec §4.5 outline: gate (§4.2), precedence (§4.4), loop, always-on rules, layer rules when declared, commands (`init` with alias `questions`), load plan (§4.3), tools (four scripts, each with its manual equivalent), scope modes, completion checklist. Keep every named rule the canon check needs (grep list below).
- [ ] **Step 2:** Move "Agent Failure Modes" and "Anti-Loopholes" into `review-checklist.md` under `## Self-Check Before Completion`, unchanged in content.
- [ ] **Step 3:** Add `## Contents` lists to `architecture.md` and `chapter-map.md`.
- [ ] **Step 4:** `validate.sh`: SKILL.md token ceiling 3000; managed-block ceiling 1200 (words of `templates/agent-block.md` × 4 / 3).
- [ ] **Step 5:** Verify: `python -c "import re;t=open('skills/clean-code/SKILL.md',encoding='utf-8').read();w=len([x for x in re.split(r'\s+',t) if x]);print(w*4//3)"` prints at most 3000; `git grep -c -E "DRY|F\.I\.R\.S\.T\.|Three Laws of TDD|Dependency Rule" -- skills/clean-code` still finds each name; `python -m unittest discover -s tests` green.
- [ ] **Step 6: Commit** (together with Task 14).

### Task 17: Managed block, `init`, protocol files, hooks, vocabulary

**Files:** Modify `templates/agent-block.md`, the 8 adapters via `bash scripts/sync.sh`; `git mv skills/clean-code/references/questions.md skills/clean-code/references/init.md` then edit; modify `session-protocol.md`, `memory-protocol.md`, `audit-report.md`, `project-refactor.md`, `new-project.md`, `assets/hooks/claude-settings.json`, `CONTEXT.md`, `scripts/validate.sh` (required files: `init.md` replaces `questions.md`; add the new scripts).

- [ ] **Step 1:** Rewrite the block per spec §4.1 within 1,200 tokens; `bash scripts/sync.sh`; confirm `git diff --stat` shows the 8 adapters changed identically.
- [ ] **Step 2:** `init.md` per spec §4.6.
- [ ] **Step 3:** Protocol edits per spec §4.7; hook prints the structure header: `sed -n '1,/^### /p' .clean/structure.md`.
- [ ] **Step 4:** `CONTEXT.md` terms: Pack, Pack index, Role, Home role, Structure map, Finding, Component; Scanner updated.
- [ ] **Step 5:** `bash scripts/validate.sh` green; `bash scripts/sync.sh && git status --short` shows nothing new.
- [ ] **Step 6: Commit** — `"Framework-first managed block, init command, and structure-aware protocols"`.

## Phase 5 — Packs

### Task 18: Pilot packs — JavaScript, TypeScript, React

**Files:** Create `references/languages/javascript.md`, `references/languages/typescript.md`, `references/frameworks/react.md`, `evals/cases/react-*/`, `docs/pack-sources.md`; modify the `clean-packs` block.

- [ ] **Step 1:** Write the three packs from the briefs in Appendix A, verifying version-specific facts against official documentation (record URLs in `docs/pack-sources.md`).
- [ ] **Step 2:** Add index lines: `language JavaScript = languages/javascript.md`, `language TypeScript = languages/typescript.md, languages/javascript.md`, `framework React = frameworks/react.md`.
- [ ] **Step 3:** Write the React eval case per Appendix B.
- [ ] **Step 4:** `python -m unittest discover -s tests`, `python evals/grade.py --self-test`, originality check (Task 20 script) on the three packs.
- [ ] **Step 5:** Read the three packs against the template and amend the template in `CONTRIBUTING.md` if the pilot exposed a gap.
- [ ] **Step 6: Commit** — `"Add JavaScript, TypeScript, and React packs"`.

### Task 19: Remaining 37 packs, in parallel batches

**Dispatch:** Subagents (general-purpose), at most six at once, each owning two to four packs plus their eval cases. Each subagent prompt contains: the pack template and authoring rules (spec §5.2–§5.4 verbatim), the `clean-roles` grammar (spec §6.3 verbatim), the pilot packs as style reference (paths), its briefs from Appendix A and B, the budget command, the constraints (no book text, LF, no absolute paths, no `git` commands, write only the listed files), and the report format: files written, token counts, sources consulted, any fact it could not verify.

**Batches:**

1. Languages: python, java, csharp, go, rust, php.
2. Languages: kotlin, swift, ruby, cpp, c, dart, scala, objective-c, shell, powershell, r.
3. Frameworks: nextjs, vue-nuxt, angular, svelte, express, nestjs, strapi.
4. Frameworks: django, flask, fastapi, spring, aspnet-core, ktor.
5. Frameworks: laravel, symfony, rails, gin-beego, flutter, swiftui-uikit, jetpack-compose.

- [ ] **Per batch:** dispatch → review every pack (template, budget, accuracy spot-checks of the claims most likely to be version-sensitive, roles block sanity against a one-file sample) → fix → add index lines and `supersede` lines (`supersede NestJS > Express`, `supersede Strapi > React`) → append sources → `python -m unittest discover -s tests` and `python evals/grade.py --self-test` → commit `"Add <names> packs"`.

### Task 20: Originality check and pack review pass

**Files:** scratchpad script only (never committed): `originality.py`.

- [ ] **Step 1:** Script: normalize both books and each new Markdown file to lowercase words; report every shared run of 8 or more consecutive words, excluding runs made only of canon names or code.
- [ ] **Step 2:** Run over `skills/clean-code/references/languages/*.md`, `frameworks/*.md`, `SKILL.md`, `init.md`, `framework-map.md`, `docs/*.md`, `README.md`. Expected: no shared run beyond canon phrases (for example "the dependency rule"). Rewrite any hit.
- [ ] **Step 3:** Whole-set review: consistent voice, no contradictions between a framework pack and its language pack, every Layers section opens with the applicability sentence.
- [ ] **Step 4: Commit** fixes, if any — `"Tighten packs after review"`.

## Phase 6 — Eval Runs

### Task 21: Eval exports and a with/without-skill run

**Files:** `evals/evals.json` (exported), `evals/triggers.json`, `evals/README.md` (results section).

- [ ] **Step 1:** Load the `anthropic-skills:skill-creator` skill; align `evals.json` and grading output with its schemas.
- [ ] **Step 2:** `python evals/grade.py --export-evals evals/evals.json`; write `triggers.json` (about ten should-trigger and ten near-miss should-not-trigger queries).
- [ ] **Step 3:** For the subset (four core cases plus express, django, spring, flutter, rust, aspnet-core): copy each fixture to a scratch workspace twice; run one subagent with the skill (pointed at `skills/clean-code/SKILL.md`) and one without; save transcripts; grade both.
- [ ] **Step 4:** Record pass rates per case and configuration in `evals/README.md`, with honest notes on skipped expectations.
- [ ] **Step 5: Commit** — `"Record eval results for 4.0.0"`.

## Phase 7 — Docs And Release Preparation

### Task 22: README, docs, changelog, version

**Files:** `README.md`, `docs/install.md`, `docs/configuration.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `VERSION`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`.

- [ ] **Step 1:** README per spec §8, at most 150 lines (`wc -l README.md`).
- [ ] **Step 2:** Move host table, profiles, global mode, env vars, update and uninstall detail into `docs/install.md`; `.clean/` formats, architecture and roles declarations, hooks into `docs/configuration.md`.
- [ ] **Step 3:** Manifest descriptions: name `init`, the packs, and the structure map; drop `questions`.
- [ ] **Step 4:** `CHANGELOG.md` 4.0.0 entry (Added, Changed, Fixed); `VERSION` → `4.0.0`; `bash scripts/sync.sh`; update the `CLEAN_CODE_REF=v4.0.0` example by hand (sync does not stamp it).
- [ ] **Step 5:** `bash scripts/validate.sh` green.
- [ ] **Step 6: Commit** — `"4.0.0: short README, install and configuration docs, changelog"`.

## Phase 8 — Verification

### Task 23: Full verification and handoff

- [ ] `bash scripts/validate.sh` — quote the final `pass` line.
- [ ] `python -m unittest discover -s tests -v` — quote the summary.
- [ ] The CI skill-tools steps by hand in Git Bash.
- [ ] `npx --yes markdownlint-cli2 "**/*.md" "#node_modules" "#books"` (PowerShell tool if `npx` is missing from Git Bash).
- [ ] `detect_stack.py`, `scan_repo.py`, `map_structure.py` on this repository and read-only on `d:/Development/Inklusit/Inklusit.Core`; spot-check five findings by hand.
- [ ] `git ls-files --eol | grep -v "i/lf" | grep -v "i/-text"` prints nothing.
- [ ] Review the full branch diff (`git diff main...HEAD --stat`, then per area).
- [ ] Update memory files (`clean-code-skills-v3-structure.md` → v4 facts: budgets, packs, scanner modules, framework-first).
- [ ] Handoff report: what changed, what ran with which command and result, what did not run, residual risks; ask about push, PR, and release.

---

## Appendix A — Pack Briefs

Every brief lists what the pack must cover beyond the template's generic expectations. "Verify" marks facts that changed recently and must be checked against official documentation before they are written.

### Languages

- **javascript** — ES2023+ on current Node LTS. Prettier or Biome format; ESLint 9 flat config lints. `const`/`let`, strict equality, ESM, named exports; async/await, no floating promises; `Error` subclasses with `cause`; `AbortController` for cancellation; never block the event loop. Ports as duck-typed objects documented with JSDoc; composition root in the entry module. Enforce: ESLint `complexity`, `max-lines-per-function`, `max-params`, `max-depth`, `no-unused-vars`; `import/no-cycle`; dependency-cruiser. Smells: callback pyramids, `==`, mutated arguments, barrels that create cycles, `utils.js`.
- **typescript** — delta over javascript; TypeScript 5.x. `strict`, `noUncheckedIndexedAccess`; `unknown` over `any` with narrowing; `satisfies`; discriminated unions for expected outcomes; `readonly`; branded IDs; `import type`; literal unions over `enum` where the project allows (verify `erasableSyntaxOnly`). typescript-eslint `strict-type-checked`, `no-floating-promises`, `consistent-type-imports`; `tsc --noEmit` in CI. Layers: domain types never import framework types; map DTOs at the edge.
- **python** — 3.10+. Ruff format and lint; mypy or pyright. PEP 8 names; keyword-only flags; no mutable defaults; type hints on public API; frozen dataclasses; specific exceptions, `raise ... from`; `__all__`; src layout; pytest fixtures and parametrize; `asyncio.TaskGroup`, never block the loop. Layers: `typing.Protocol` ports; ORM models stay outside the domain; composition in `__main__.py` or `main.py`. Enforce: Ruff `C901`, `PLR0913`, `PLR0912`, `PLR0915`, `ARG`, `ERA`, `BLE`, `S`; import-linter layers and forbidden contracts. Smells: `utils.py`, circular imports, `import *`, bare `except`, notebook-only logic.
- **java** — Java 21 LTS and 25 LTS (verify). google-java-format or Spotless; Checkstyle, PMD, SpotBugs, Error Prone. Records, sealed interfaces with pattern matching, `Optional` only as a return type, immutable collections, constructor injection, unchecked exceptions with causes, try-with-resources, package-private by default, JPMS `exports` where modules exist, package by feature, JUnit 5 and AssertJ, Testcontainers, virtual threads. Enforce: ArchUnit `layeredArchitecture()`, `slices().should().beFreeOfCycles()`; Checkstyle `MethodLength`, `ParameterNumber`, `CyclomaticComplexity`. Smells: god services, setter-only anemic models, static utility classes, null returns.
- **cpp** — C++20/23. clang-format; clang-tidy (`cppcoreguidelines-*`, `modernize-*`, `bugprone-*`), cppcheck. RAII, no naked `new`/`delete`, rule of zero, `const`, `std::span`/`std::string_view`, `[[nodiscard]]`, `enum class`, concepts; one error model per boundary (exceptions or `std::expected`); anonymous namespaces for internal linkage; `include/<project>/` public headers; GoogleTest, Catch2, or doctest; `std::jthread`, `std::scoped_lock`, TSan. Layers: pure-virtual interfaces or concepts in the core; CMake `PRIVATE`/`PUBLIC` link visibility enforces direction. Enforce: `readability-function-size`, `readability-function-cognitive-complexity`, `misc-include-cleaner`. Smells: macro cleverness, owning raw pointers, god headers, mutable globals.
- **csharp** — C# 12–14 on .NET 8–10 (verify current LTS). `dotnet format` with `.editorconfig`; .NET analyzers (`AnalysisLevel`), StyleCop.Analyzers. Naming (PascalCase, `_camelCase` fields, `I` interfaces, `Async` suffix); nullable reference types; records; file-scoped namespaces; `sealed` by default; `throw;` not `throw ex;`; `ArgumentNullException.ThrowIfNull`; async all the way, `CancellationToken`, no `async void`, no `.Result`; `internal` by default, projects as components; namespace mirrors folder; xUnit, NUnit, or MSTest. Layers: Domain project references no EF Core or ASP.NET Core; composition in `Program.cs`. Enforce: NetArchTest.Rules or ArchUnitNET, project-reference direction, `TreatWarningsAsErrors`, CA1502 (verify configuration). Smells: service locator, static helpers, `DateTime.Now` in domain, EF entities as API contracts.
- **php** — PHP 8.3/8.4. PHP-CS-Fixer or PHP_CodeSniffer (PER Coding Style); PHPStan at a high level or Psalm. `declare(strict_types=1)`; typed properties and returns; readonly; enums; constructor promotion; `final` by default; exception hierarchies; never `@` suppression; PSR-4 autoloading; `src/` and `tests/`; PHPUnit or Pest. Layers: interfaces in the domain, container configuration at the edge. Enforce: Deptrac; PHPStan rules; phpmd `CyclomaticComplexity`, `ExcessiveMethodLength`. Smells: arrays as structs, static facades in the domain, global functions.
- **go** — Go 1.22+ (verify current). gofmt/goimports; golangci-lint v2 configuration (verify). MixedCaps, no stutter, short package names; early returns; `fmt.Errorf("...: %w", err)`, `errors.Is`/`As`, no panics in libraries; accept interfaces, return structs, declare interfaces at the consumer; `internal/`; `cmd/<app>/main.go` as composition root; table-driven tests with `t.Run`; `context.Context` first; errgroup; sender closes channels; `-race`. Enforce: `gocyclo`/`gocognit`, `funlen`, `errcheck`, `revive`, `depguard`, go-arch-lint. Smells: `util`/`common` packages, package-level mutable state, `init()` side effects, contexts stored in structs.
- **rust** — editions 2021/2024. rustfmt; Clippy. Newtypes for invariants, enums for states, borrowing over cloning, `Result` with `?`, thiserror in libraries, anyhow in binaries, no `unwrap` in library paths; `pub(crate)` by default; workspace crates as components; unit tests in `#[cfg(test)] mod tests`, integration tests in `tests/`; tokio: `spawn_blocking` for blocking work. Layers: a domain crate with no I/O dependencies; traits as ports; Cargo dependencies enforce direction. Enforce: Clippy `too_many_arguments`, `cognitive_complexity`, `unwrap_used`, `expect_used`; cargo-deny. Smells: clone-to-compile, stringly-typed errors, `Rc<RefCell<_>>` webs, `unsafe` without a `SAFETY:` comment.
- **swift** — Swift 6 with strict concurrency (verify). swift-format or SwiftFormat; SwiftLint. API Design Guidelines names; value types by default; `final` classes; protocols; access control; `throws` (typed throws where helpful); no `try!` or force unwraps in production paths; async/await, actors, `@MainActor`, `Sendable`; SwiftPM targets as components; Swift Testing or XCTest. Layers: a domain target that imports neither UIKit nor SwiftUI. Enforce: SwiftLint `function_body_length`, `cyclomatic_complexity`, `function_parameter_count`, `force_unwrapping`, `force_try`. Smells: massive view controllers, singletons, implicit main-thread assumptions.
- **kotlin** — Kotlin 2.x. ktlint or ktfmt; detekt. `val` over `var`, data classes, sealed interfaces for outcomes, no `!!`, `internal`, `require`/`check`; `runCatching` swallows `CancellationException` — never use it around suspending calls without rethrowing (verify wording); structured concurrency, no `GlobalScope`, `Dispatchers.IO` for blocking; Gradle modules as components; JUnit 5 or Kotest, MockK. Layers: a domain module with no Android, Ktor, or Spring dependencies. Enforce: detekt `LongMethod`, `LongParameterList`, `CyclomaticComplexMethod`, `TooManyFunctions`; Konsist. Smells: god objects, sprawling top-level utility files.
- **ruby** — Ruby 3.3/3.4. RuboCop or Standard. Predicates `?`, bang `!`, small methods, keyword arguments, `Data.define` value objects, `frozen_string_literal`; custom errors under `StandardError`, specific `rescue`, never `rescue => e; nil`; Zeitwerk naming; RSpec or Minitest. Layers: plain Ruby objects for domain rules; packwerk for boundaries. Enforce: `Metrics/MethodLength`, `Metrics/AbcSize`, `Metrics/CyclomaticComplexity`, `Metrics/ParameterLists`. Smells: monkey patching, `method_missing` magic, class variables.
- **shell** — Bash 4+ and POSIX sh. shfmt; ShellCheck. `set -euo pipefail` where safe; quote every expansion; `local`; `readonly`; a `main "$@"` entry; errors to stderr with meaningful exit codes; `trap` cleanup; sourced libraries in `lib/`; bats-core or ShellSpec. Layers: a script is a humble object — logic lives in functions; past a couple of hundred lines or any real data structure, move to a real language. Enforce: ShellCheck in CI, `shfmt -d`. Smells: unquoted variables, parsing `ls`, `eval`, backticks, unchecked `cd`.
- **c** — C11/C17/C23. clang-format; clang-tidy, cppcheck; `-Wall -Wextra -Werror`. Module prefixes (`list_push`); `static` for internal linkage; opaque structs; fixed-width integers; error enums checked at every call; `goto cleanup` for release paths; documented ownership; one public header per module; Unity, CMocka, or Check. Layers: ports as structs of function pointers; `main` composes. Enforce: `readability-function-size`, cppcheck, `-fanalyzer`, ASan/UBSan. Smells: function-like macros, globals, `strcpy`, unchecked `malloc`.
- **r** — R 4.4+. styler; lintr. tidyverse-style snake_case; small pure functions, no `<<-`; conditions with classes (`rlang::abort`), specific `tryCatch`; package layout (`R/`, `tests/testthat/`, `DESCRIPTION`, roxygen2 `@export`); analysis projects keep logic in functions called by thin scripts or a `{targets}` pipeline; testthat 3rd edition. Enforce: lintr `cyclocomp_linter`, `object_length_linter`; `R CMD check`. Smells: `setwd()`, `library()` inside functions, `rm(list = ls())`, `attach()`, `T`/`F`.
- **dart** — Dart 3.x. `dart format`; `dart analyze` with `package:lints` or `very_good_analysis`. Class modifiers, sealed classes with patterns, records, null safety without casual `!`; `Exception` versus `Error`, never catch `Error`; `unawaited_futures`; `Isolate.run`; `lib/src/` private with a public library file; package:test. Layers: domain code never imports `package:flutter`. Smells: `dynamic`, logic in `main.dart`.
- **scala** — Scala 3 (3.3 LTS). scalafmt; Scalafix, WartRemover. Immutability, case classes, enums/sealed traits, `Option`/`Either` over `null`/exceptions, no `.get`/`.head` on possibly empty values; given/using; sbt subprojects as components; MUnit or ScalaTest. Layers: a pure domain module; effects at the edges. Enforce: WartRemover `Null`, `Var`, `Return`, `OptionPartial`; sbt `dependsOn` direction. Smells: implicit conversions, deep trait stacks, partial functions.
- **objective-c** — modern Objective-C with ARC. clang-format; Clang Static Analyzer; warnings as errors. Cocoa naming and class prefixes; `nonatomic`, `copy` for strings and blocks, `weak` delegates; nullability annotations (`NS_ASSUME_NONNULL_BEGIN`); lightweight generics; `NSError **` out-parameters, exceptions only for programmer errors; class extensions for private API; XCTest; GCD with UI on the main queue. Layers: model classes never import UIKit. Smells: massive view controllers, retain cycles in blocks, missing nullability, unprefixed categories.
- **powershell** — PowerShell 7.4+ (and 5.1 where required). PSScriptAnalyzer (`Invoke-Formatter` for layout). Approved verbs, singular nouns; `[CmdletBinding()]`; typed and validated parameters; emit objects, `Write-Host` only for display; pipeline input with a `process` block; `SupportsShouldProcess` for changes; `$ErrorActionPreference = 'Stop'`, specific `catch`, `$PSCmdlet.ThrowTerminatingError`; `.psm1` plus `.psd1` with explicit `FunctionsToExport`, `Public/` and `Private/` folders; Pester 5. Enforce: `PSAvoidUsingWriteHost`, `PSUseApprovedVerbs`, `PSAvoidUsingCmdletAliases`, `PSUseShouldProcessForStateChangingFunctions`, `PSAvoidGlobalVars`. Smells: aliases in scripts, parsing command text output, `Invoke-Expression`.

### Frameworks

Each framework brief lists roles the `clean-roles` block must express. Signals match declaration context (decorators, annotations, base types, signatures).

- **react** — React 19 (verify React Compiler status). Pure components, hooks rules, state colocation, custom hooks for shared logic, data fetching outside render effects (framework loaders, server components, or a query library), effects only to sync with external systems, stable keys, accessibility. Structure: `features/<name>/` with components, hooks, api; shared `components/`, `hooks/`. Roles: `component` (`**/components/**`; `name component [tsx, jsx] = ^[A-Z][A-Za-z0-9]*$`), `hook` (`**/hooks/**`; `name hook [ts, tsx, js, jsx] = ^use[A-Z]`), `context` (`**/contexts/**`, `**/context/**`), `api` (`**/api/**`). Tests: Testing Library with Vitest or Jest, MSW. Enforce: `eslint-plugin-react-hooks` (`rules-of-hooks`, `exhaustive-deps`), `eslint-plugin-jsx-a11y`. Smells: god components, fetch-in-effect races, derived state in `useState`, index keys, `dangerouslySetInnerHTML`.
- **nextjs** — Next.js 15/16 App Router (verify: `middleware.ts` renamed to `proxy.ts` in 16; caching defaults; `next lint` deprecation). Read with react. Structure: `app/` route files (`page`, `layout`, `loading`, `error`, `not-found`, `route`), server actions, `server-only` modules. Roles: `page` (`app/**/page.*`, `src/app/**/page.*`), `layout`, `route-handler` (`app/**/route.*`), `middleware` (`middleware.*`, `src/middleware.*`, `proxy.*`, `src/proxy.*`), `server-action` (`**/actions/**`, `**/*.actions.*`). `ignore-name` for `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, `default`, `generateMetadata`, `generateStaticParams`, `metadata`, `revalidate`, `dynamic`, `runtime`, `config`. Smells: `'use client'` everywhere, secrets in `NEXT_PUBLIC_*`, business rules in route handlers.
- **vue-nuxt** — Vue 3.5+ Composition API with `<script setup>`; Nuxt 3/4 (verify `app/` source directory default in 4). Roles: `component` (`**/components/**`), `composable` (`**/composables/**`; `name composable [ts, js, vue] = ^use[A-Z]`), `store` (`**/stores/**`; `name store = ^use\w+Store$`), `page` (`**/pages/**`), `layout` (`**/layouts/**`), `middleware` (`**/middleware/**`), `server-route` (`server/api/**`, `server/routes/**`), `server-middleware` (`server/middleware/**`), `plugin` (`**/plugins/**`). Enforce: `eslint-plugin-vue`, `@nuxt/eslint`. Smells: mutated props, watchers for derived state, logic in templates.
- **angular** — Angular 19/20 (verify: standalone default, signals APIs, the v20 style guide dropping `.component`/`.service` suffixes, zoneless status, default test runner). Roles by signal: `component` (`@Component\(`), `directive` (`@Directive\(`), `pipe` (`@Pipe\(`), `guard` (`CanActivateFn|implements\s+CanActivate`), `interceptor` (`HttpInterceptorFn|implements\s+HttpInterceptor`), `resolver` (`ResolveFn`), `service` (`@Injectable\(`, listed last); by path also the suffixed file names. Enforce: angular-eslint, `strictTemplates`, Nx `@nx/enforce-module-boundaries` where Nx is used. Smells: nested subscriptions, logic in templates, shared-module dumping grounds.
- **svelte** — Svelte 5 runes, SvelteKit 2. Roles: `page` (`**/+page.svelte`), `load` (`**/+page.ts`, `**/+page.server.ts`, `**/+layout.ts`, `**/+layout.server.ts`), `endpoint` (`**/+server.ts`, `**/+server.js`), `server-hook` (`src/hooks.server.*`, `src/hooks.client.*`, `src/hooks.*`), `component` (`**/lib/components/**`, `**/components/**`), `store` (`**/stores/**`, `**/*.svelte.ts`, `**/*.svelte.js`). `ignore-name` for `load`, `actions`, `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `handle`, `handleError`, `handleFetch`, `prerender`, `ssr`, `csr`, `trailingSlash`, `entries`. Rules: secrets only in `$lib/server` and `$env/static/private`. Enforce: `eslint-plugin-svelte`, `svelte-check`.
- **express** — Express 5 (verify async error forwarding). Structure: `app` setup, `server` listen, `routes/`, `controllers/`, `services/`, `middleware/`, `models/` or `repositories/`, `config/`; error middleware last. Roles: `route`, `controller`, `middleware` (`signal middleware [js, ts, mjs, cjs] = \(\s*(?:req|request)\b[^)]*,\s*(?:res|response)\b[^)]*,\s*next\b`), `service`, `model`. Rules: never pass `req`/`res` into services; validation middleware; central error handler; no stack traces in responses. Enforce: dependency-cruiser rules forbidding services → controllers and `express` imports in services. Smells: fat route callbacks.
- **nestjs** — NestJS 10/11 (verify). Roles by signal, specific first: `module` (`@Module\(`), `controller` (`@Controller\(`), `guard` (`implements\s+CanActivate`), `interceptor` (`implements\s+NestInterceptor`), `pipe` (`implements\s+PipeTransform`), `filter` (`@Catch\(|implements\s+ExceptionFilter`), `middleware` (`implements\s+NestMiddleware`), `resolver` (`@Resolver\(`), `gateway` (`@WebSocketGateway`), `entity` (`@Entity\(`), `service` (`@Injectable\(`); by path `**/*.module.ts`, `**/*.guard.ts`, `**/dto/**`. Smells: `forwardRef` cycles, business rules in guards or controllers, entities as DTOs.
- **strapi** — Strapi 5 (verify Document Service API, lifecycle guidance). Structure `src/api/<name>/{content-types,controllers,services,routes,policies,middlewares}`. Roles: `controller` (`src/api/*/controllers/**`; signal `createCoreController`), `service` (`createCoreService`), `route` (`createCoreRouter`), `policy`, `middleware`, `content-type`. Smells: business rules in lifecycles, raw queries in controllers.
- **django** — Django 5.x (verify current). Structure per app: `models.py`, `views.py`, `urls.py`, `admin.py`, `forms.py`, `serializers.py`, `services.py`, `selectors.py`, `tests/`, `management/commands/`. Roles: `model` (signal `\((?:models\.)?Model\)`), `view` (signal `\(\s*(?:\w+\.)?\w*(?:View|APIView|ViewSet)\s*[,)]`), `serializer`, `form`, `admin`, `url`, `service`, `selector`, `middleware`, `command`. `ignore-name` for `Meta`, `get_queryset`, `get`, `post`, `put`, `patch`, `delete`, `dispatch`, `get_context_data`, `save`, `clean`, `handle`, `ready`. Rules: fat models or service modules (framework-first), thin views, no business flow in signals, `select_related`/`prefetch_related`, explicit `transaction.atomic`. Enforce: import-linter, Ruff `DJ` rules, django-stubs.
- **flask** — Flask 3.x. App factory, blueprints per feature, `extensions.py`, config classes. Roles: `route` (signal `@\w+\.(?:route|get|post|put|patch|delete)\(`; paths `**/routes.py`, `**/views.py`, `**/blueprints/**`), `service`, `model`, `schema` (`**/schemas.py`, `**/schemas/**`), `extension` (`**/extensions.py`). Rules: services never touch `request`, `g`, or `current_app`. Smells: god `app.py`, `from app import db` cycles.
- **fastapi** — FastAPI current (verify), Pydantic v2. Roles: `router` (signal `@\w+\.(?:get|post|put|patch|delete|api_route)\(`; paths `**/routers/**`, `**/routes/**`), `schema` (signal `\(\s*BaseModel\s*\)`; `**/schemas/**`), `model` (signal `DeclarativeBase|table=True`), `dependency` (`**/dependencies.py`, `**/deps.py`), `service`, `repository` (`**/crud/**`). Rules: no blocking I/O in `async def`; never return ORM objects without a response model; pydantic-settings. Enforce: import-linter, Ruff `FAST` rules (verify).
- **spring** — Spring Framework 6/7, Spring Boot 3/4 (verify). Roles by signal: `controller` (`@(?:Rest)?Controller\b`), `advice` (`@(?:Rest)?ControllerAdvice\b`), `service` (`@Service\b`), `repository` (`@Repository\b|extends\s+\w*Repository<`), `entity` (`@Entity\b|@Document\b`), `config` (`@Configuration\b|@ConfigurationProperties\b`), `component` (`@Component\b`). Rules: constructor injection, transactions on services, no entities in API contracts. Enforce: ArchUnit, Spring Modulith `ApplicationModules.of(...).verify()` (verify API). Smells: field injection, `@Transactional` on private methods, circular beans.
- **aspnet-core** — ASP.NET Core 8–10 with EF Core (verify). Roles: `controller` (signal `\[ApiController\]|:\s*(?:ControllerBase|Controller)\b`; `**/Controllers/**`), `endpoint` (`**/Endpoints/**`), `middleware` (`**/Middleware/**`; signal `RequestDelegate|:\s*IMiddleware\b`), `filter` (signal `IAsyncActionFilter|IActionFilter|ActionFilterAttribute`), `data` (signal `:\s*DbContext\b`), `entity-configuration` (signal `IEntityTypeConfiguration<`), `options` (`**/Options/**`; name `Options$`), `validator` (signal `AbstractValidator<`), `request-handler` (signal `IRequestHandler<`), `service`, `repository`. Rules: ProblemDetails, options pattern, scoped `DbContext`, `AsNoTracking` reads, no EF InMemory provider for behavior tests (verify guidance). Enforce: NetArchTest, project references. Smells: captive dependencies, sync over async.
- **ktor** — Ktor 3.x (verify DI plugin status). Roles: `route` (signal `fun\s+Route\.\w+\(`; `**/routes/**`, `**/routing/**`), `plugin-config` (signal `fun\s+Application\.configure\w*\(`; `**/plugins/**`), `application` (signal `fun\s+Application\.module\(`), `service`, `repository`, `model`. Rules: StatusPages for errors, RequestValidation, `withContext(Dispatchers.IO)` for blocking JDBC. Tests: `testApplication`.
- **laravel** — Laravel 11/12 (verify slim skeleton, middleware registration in `bootstrap/app.php`, Pest arch testing). Roles: `controller` (`app/Http/Controllers/**`), `middleware` (`app/Http/Middleware/**`), `request` (`app/Http/Requests/**`; signal `extends\s+FormRequest`), `resource` (`app/Http/Resources/**`), `model` (`app/Models/**`; signal `extends\s+Model\b`), `action` (`app/Actions/**`), `service` (`app/Services/**`), `job` (`app/Jobs/**`; signal `implements\s+ShouldQueue`), `policy` (`app/Policies/**`), `event`, `listener`, `provider` (`app/Providers/**`). Enforce: Larastan, Deptrac, Pint, Pest `arch()`. Smells: logic in Blade, `$guarded = []`, N+1.
- **symfony** — Symfony 7.x (verify). Roles: `controller` (`src/Controller/**`; signal `extends\s+AbstractController`), `entity` (`src/Entity/**`; signal `#\[ORM\\Entity`), `repository` (`src/Repository/**`; signal `extends\s+ServiceEntityRepository`), `form` (`src/Form/**`; signal `extends\s+AbstractType`), `subscriber` (signal `implements\s+EventSubscriberInterface`), `command` (signal `#\[AsCommand`), `message-handler` (signal `#\[AsMessageHandler`), `voter` (signal `extends\s+Voter\b`), `service`. Rules: autowired constructor injection, never inject the container. Enforce: Deptrac, PHPStan Symfony extension.
- **rails** — Rails 7.2/8.x (verify). Roles: `model` (`app/models/**`; signal `<\s*(?:ApplicationRecord|ActiveRecord::Base)`), `controller` (`app/controllers/**`; signal `<\s*(?:ApplicationController|ActionController::\w+)`), `job` (`app/jobs/**`), `mailer` (`app/mailers/**`), `helper` (`app/helpers/**`), `service` (`app/services/**`), `concern` (`**/concerns/**`), `policy` (`app/policies/**`), `channel` (`app/channels/**`). Rules: skinny controllers; fat models or service objects (framework-first); side effects out of callbacks; strong parameters; `includes` against N+1. Enforce: RuboCop Rails, packwerk, Brakeman.
- **gin-beego** — Gin 1.x and Beego 2.x (verify). Roles: `handler` (signal `\(\s*\w+\s+\*gin\.Context\s*\)`; `**/handler/**`, `**/handlers/**`), `middleware` (signal `\)\s*gin\.HandlerFunc`; `**/middleware/**`), `controller` (signal `(?:web|beego)\.Controller`; `**/controllers/**`), `router` (`**/routers/**`, `**/router/**`), `service`, `repository`, `model`. Rules: never pass `*gin.Context` into services; use `c.Request.Context()`.
- **flutter** — Flutter 3.x (verify). Roles: `widget` (signal `extends\s+(?:StatelessWidget|StatefulWidget|ConsumerWidget|ConsumerStatefulWidget|HookWidget)`; `**/widgets/**`, `**/screens/**`, `**/pages/**`), `state` (signal `extends\s+State<`), `bloc` (signal `extends\s+(?:Bloc|Cubit)<`), `notifier` (signal `extends\s+(?:ChangeNotifier|Notifier|AsyncNotifier|StateNotifier)`), `repository`, `service`, `model`. Rules: small widgets, const constructors, no I/O in `build`, `use_build_context_synchronously`. Enforce: `flutter_lints` or `very_good_analysis`.
- **swiftui-uikit** — SwiftUI with Observation (iOS 17+) and UIKit (verify). Roles: `view` (signal `struct\s+\w+\s*:\s*(?:[\w, ]*\b)?View\b`; `**/Views/**`), `view-model` (name `ViewModel$`), `view-controller` (signal `:\s*UI\w*ViewController\b`; name `ViewController$`), `coordinator` (name `Coordinator$`), `service`, `repository`, `model`. Rules: no networking or persistence in views; `@MainActor` view models; injection through initializers or the environment.
- **jetpack-compose** — Compose with the Android architecture guidance (verify). Roles: `composable` (signal `@Composable`), `view-model` (name `ViewModel$`; signal `:\s*ViewModel\(\)`), `repository` (name `Repository$`), `use-case` (name `UseCase$`; `**/usecase/**`, `**/usecases/**`), `data-source` (name `DataSource$`), `di-module` (signal `@Module\b`). `ignore-name` for `Preview`-suffixed functions. Rules: state hoisting, `collectAsStateWithLifecycle`, ViewModels never hold `Context` or views. Enforce: detekt with Compose rules, Konsist, Android Lint.

## Appendix B — Eval Case Briefs

Each case: a fixture of three to ten files under `repo/`, a realistic prompt, and at least three deterministic expectations, at least one of which fails on the untouched fixture.

| Case | Prompt | Key expectations |
| --- | --- | --- |
| `react-hook-extraction` | "UserList fetches users inside a component effect. Add loading and error states and make the fetching reusable for the profile page." | a `src/hooks/use*.ts(x)` file exists containing `fetch`; `src/components/UserList.tsx` no longer contains `fetch(`; no new file at the root |
| `nextjs-shared-rule` | "Apply a 10% discount to orders over 100 EUR on the orders page and in the orders API route." | a non-`app/` module contains the rule; `app/orders/page.tsx` and `app/api/orders/route.ts` import it |
| `vue-composable` | "Two components duplicate cart-total logic. Make it shared." | `composables/use*.ts` exists; both components import it |
| `angular-service` | "OrdersComponent calls HttpClient directly. Add retry and keep the component thin." | an injectable service contains `HttpClient`; the component file no longer does |
| `svelte-load` | "The page component fetches products in the script block. Move loading to the right place." | `+page.ts` or `+page.server.ts` exports `load`; `+page.svelte` no longer contains `fetch(` |
| `express-rate-limit` | "Limit POST /login to five attempts per minute per client IP." | a `src/middleware/*` file contains `(req, res, next)`; `src/services/userService.js` unchanged; map reports no misplaced finding |
| `nestjs-admin-guard` | "Only admins may call DELETE /users/:id." | a `*.guard.ts` file contains `CanActivate`; the controller contains `UseGuards`; the service does not contain `role` |
| `strapi-service-logic` | "When an article is published, compute its reading time." | the article service contains the computation; the controller does not |
| `django-service` | "Cancelling an order must refund the payment and restock items." | the rule lives in `services.py` or a model method; `views.py` contains no `refund` logic |
| `flask-blueprint` | "Add GET /reports/monthly returning totals per month." | a blueprint route exists; a service module holds the aggregation; `app.py` unchanged apart from registration |
| `fastapi-schema` | "Add PATCH /items/{id} to update the price." | a Pydantic schema exists for the update; the route function does not return the ORM model directly; a service or crud module holds the update |
| `spring-layering` | "Add an endpoint that closes an account when its balance is zero." | the rule is in a `@Service` class; the controller does not inject a repository |
| `aspnet-core-service` | "Add an endpoint that archives completed projects older than a year." | the logic sits in a service; the controller does not reference `DbContext` |
| `ktor-route` | "Add POST /orders with validation." | a `Route.` extension function exists; a service class holds the logic |
| `laravel-form-request` | "Validate that a new invoice has a positive amount and a due date in the future, and only let accountants create invoices." | a `FormRequest` class exists; a middleware or policy exists in its conventional folder; the controller stays thin |
| `symfony-service` | "Send a welcome email after a user registers." | a service or message handler holds the mailing; the controller does not construct the mailer |
| `rails-service-object` | "Charging a subscription must create an invoice and send a receipt." | the logic sits in a model method or `app/services/`; no new callback is added to the model |
| `gin-middleware` | "Add request-ID middleware and use the ID in the order service logs." | a `middleware` package file returns `gin.HandlerFunc`; the service has no `*gin.Context` parameter |
| `flutter-notifier` | "The login screen calls the API inside `build`. Fix it and show a spinner while loading." | a notifier, cubit, or state class holds the call; the widget's `build` no longer contains the HTTP call |
| `swiftui-view-model` | "ContentView downloads the feed with URLSession. Add pull-to-refresh." | a view model contains `URLSession`; `ContentView.swift` does not |
| `compose-view-model` | "The screen reads the repository directly. Add a loading state." | a ViewModel exposes state; the composable does not reference the repository |
| `c-error-codes` | "Add `list_remove` that reports when the index is out of range." | the function returns an error code declared in the header; the header declares it |
| `cpp-raii` | "Wrap the file handle so it always closes." | a class manages the handle; no `delete` expression or `fclose(` call remains in the caller |
| `rust-errors` | "Parse config values and report bad input to the caller." | an error enum exists; library code contains no `.unwrap()` |
| `shell-functions` | "Make deploy.sh safe to rerun and easier to read." | `set -euo pipefail` present; logic moved into functions; no unquoted `$1` |
| `powershell-advanced-function` | "Add a command that removes stale temp files older than N days." | a `Verb-Noun` function with `[CmdletBinding(SupportsShouldProcess` exists; no `Write-Host` |
| `r-function` | "The analysis script repeats the same cleaning steps twice." | a function in `R/` holds the steps; a testthat test exists |
| `scala-option` | "Lookup returns null when the user is missing; fix it." | the signature returns `Option`; no `null` remains in the lookup |
| `objc-nserror` | "Report save failures to the caller." | the method takes `NSError **`; nullability annotations present |
| `core-context-gate` | an Express task on a fixture with `.clean/context.json` listing packs | transcript reads `.clean/context.json` and `frameworks/express.md` |
| `core-layers-declared` | the Express task with `.clean/architecture.md` declaring layers | `boundaries_pass`; no `express` import under `src/domain/` |
| `core-init` | "/clean-code init" with the interview answers in the prompt | `.clean/context.json` and `.clean/structure.md` exist |
| `core-no-sibling` | "Improve error handling in src/services/payment.js." | no file matching `*_v2*`, `*_new*`, `*final*`, `*copy*`; `payment.js` changed |
