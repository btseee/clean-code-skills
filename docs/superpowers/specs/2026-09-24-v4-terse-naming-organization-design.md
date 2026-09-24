# v4 Completion: Terse Content, Naming, Organization, Patterns, New Packs, PR #6 Ideas

Status: approved 2026-09-24 ("put it all inside v4"). Extends the unreleased 4.0.0 on
`feature/v4-packs-structure-map`; the version stays 4.0.0 and the CHANGELOG entry grows.

## 1. Goals

The user's asks, in their words and as requirements:

1. **Comments.** When cleaning code, especially AI-generated code with heavy comments, fix comments
   with caveman's terseness and ponytail's minimalism.
2. **LLM instruction files** (AGENTS.md, CLAUDE.md, DESIGN.md, ARCHITECTURE.md, ...) are too heavy:
   compress what the skill installs, give users a command to compress their own, and compress the
   skill's own content and comments.
3. **Folder organization per the books**, decided by Python: the map says what to organize; then
   reorganize this repository with it.
4. **Naming** of functions, classes, and variables is poor: detect it and teach it.
5. **PR #6** (kyuna0312's 3.3.0 proposal): adopt agent smells A1-A10, the `plan` and `review`
   commands, risk-based verification, and planted-flaw evals.
6. **Suggest improvement ideas** (in the handoff, not in this spec's scope).
7. **New packs**: Drupal, WordPress, Tailwind, CSS, Sass, TensorFlow, PyTorch, Unity. Laravel
   already has a pack; re-check it against current documentation.
8. **Update `evals/README.md`** with a second benchmark iteration.
9. **Cover the concepts**: architecture styles (DI, IoC, MVC, MVVM, CQRS, Clean, Hexagonal,
   Microservices, Event-Driven), design patterns (Repository, Unit of Work, Factory, Singleton,
   Strategy, Adapter, Decorator, Observer, Command), data access (ORM, Micro ORM, Query Builder,
   Data Mapper, Active Record).

## 2. Approach

Rules in the skill, verification in Python. Caveman and ponytail concepts become skill rules and
workflows; the agent does the rewriting. Python measures and guards: naming findings, organization
findings, comment density, and a checker that proves a compressed file lost nothing technical.
Rejected: Python rewriting prose itself (silent meaning loss), and depending on the caveman or
ponytail plugins (breaks "works in every host with no tooling"; both are credited as inspiration).

Constraints unchanged: scripts are standard-library only and parse under Python 3.8; no book text
(`scripts/check_originality.py` reports 0); `bash scripts/validate.sh` passes; the managed block is
edited only in `templates/agent-block.md` and synced.

## 3. Reorganize The Scripts First

`skills/clean-code/scripts/` holds 18 flat modules, and names such as `symbols_braces.py` versus
`brace_grammars.py` or `project_*` versus `structure_*` hide what each does. Before new features,
group the library modules into packages named for their concept (CCP: what changes together lives
together); CLI entry points stay at the top level, so every documented command keeps working.

| Package | Modules (old -> new) |
| --- | --- |
| `source/` | `project_files` -> `files`, `source_lexer` -> `lexer`, `project_imports` -> `imports`, `import_resolution` -> `resolution` |
| `symbols/` | `project_symbols` -> `__init__` (exposes `extract`, `language_of`, `SUPPORTED_SUFFIXES`), `symbol_model` -> `model`, `symbols_braces` -> `braces`, `brace_grammars` -> `grammars`, `symbols_python` -> `python_source`, `symbols_ruby` -> `ruby_source` |
| `structure/` | `structure_roles` -> `roles`, `structure_findings` -> `findings`, `structure_report` -> `report`, `component_metrics` -> `metrics`; new `naming`, `organization` |

Top level: `detect_stack.py`, `scan_repo.py`, `check_boundaries.py`, `map_structure.py`, and the new
`check_compression.py`. Tests keep passing unchanged except for imports (behavior-preserving move,
verified before and after); `validate.sh`'s parse, Python 3.8, and standard-library checks cover the
packages; installers already copy recursively; `evals/grade.py` and the hooks keep working. No
package may shadow a standard-library module (`source`, `symbols`, and `structure` do not).

## 4. Naming Findings

New `structure/naming.py`; `map_structure.py` reports a `names` finding kind. Scope: classes,
functions, methods (all languages the map extracts), and variables and parameters where extraction
is reliable: Python via `ast`, JavaScript and TypeScript via declarations (`const`, `let`, `var`,
function parameters) on the lexer's code view. Rules, each citing Clean Code:

| Rule | Flags | Cites |
| --- | --- | --- |
| vague | `data`, `info`, `obj`, `item`, `thing`, `stuff`, `temp`, `tmp`, `val`, `res`, `ret`, `foo`, `bar`, and functions named `handle`, `process`, `doIt`, `manage` with no object | N1 |
| encoded | Hungarian prefixes (`strName`, `iCount`, `szX`, `m_x`, `lpX`), an `I` interface prefix outside C#/.NET conventions, a type in the name where the language has types | N6 |
| numbered | `data2`, `user1`, `_v2`, `_new`, `_old`, `_copy`, `final` suffixes | N1, N4 |
| noise-word | class names ending `Manager`, `Processor`, `Data`, `Info`, `Helper`, `Util`, `Utils`, `Stuff` | N1, G17 |
| verb-class | a class named like an action (`ProcessOrder`, `HandleLogin`) | N1 |
| too-short | a name under three characters outside loop indices, lambdas, catch variables, and math-idiom names (`x`, `y`, `i`, `j`, `k`, `e`, `id`) | N5 |
| convention | casing that breaks the language's convention (Python functions `snake_case`, classes `PascalCase`; JS/TS functions `camelCase`; Go exported `MixedCaps`; C# methods `PascalCase`; Java/Kotlin methods `camelCase`; Rust functions `snake_case`; Ruby methods `snake_case`; PHP methods `camelCase`) | N3, G24 |
| file-mismatch | a file whose only public type has an unrelated name (`user_service.py` holding `AccountRepository`) in languages with one-type-per-file conventions (Java, C#, Kotlin, Swift, PHP, Dart) | N4, G17 |

Noise controls: tests, generated files, `ignore-name` patterns, and `accept`ed files are exempt;
`clean-roles` blocks may add `ignore-name` for framework idioms (`MainActivity`, `urlpatterns`).
Findings group by rule with counts and the top examples, like the other finding kinds. The skill
and packs get sharper naming rules (Names sections name the concrete anti-patterns above).

## 5. Organization Findings And The Move Plan

New `structure/organization.py`; `map_structure.py` reports:

- **family**: three or more files in one folder that share a leading name token and import each
  other -> propose a folder named for the token (CCP; Screaming Architecture).
- **junk-drawer**: a folder named `utils`, `util`, `helpers`, `helper`, `common`, `misc`,
  `shared`, `general`, or `stuff` with files of several roles or families -> propose splitting by
  concept (G17).
- **flat-folder**: a folder holding more than 15 production source files -> propose grouping by
  its families (CCP, CRP).
- **unreferenced**: a production file nothing imports, that is not a test, entry point, or holder
  of a role (framework-discovered code), in a language whose imports the map resolves -> "possibly
  unused" (dead code, G9).
- **comment-heavy**: a file whose comment lines are at least 40% of its non-blank lines and at
  least 20 lines -> candidate for the comment workflow (C1-C5, G12).

`structure.md` gains a **Proposed moves** section: misplaced symbols, families, and junk-drawer
splits as concrete moves (`source -> destination`), for an audit to confirm; the clean-up
campaign's placement batch consumes it. `map_structure.py --changed` limits findings to files git
reports as changed (for the `review` command). Thresholds are constants with one test each.

Then reorganize this repository with the output: after section 3, run the map on the repository,
act on its organization findings, and record anything deliberately left as an `accept` line.

## 6. Terse Content

Always-loaded text is paid on every turn; on-demand text is paid when read. Rewrite both in a
caveman-derived style: drop articles, filler, hedging, and repeated framing; keep full words (no
invented abbreviations), imperative verbs, code, paths, commands, rule IDs, numbers, and every
security line. Style targets: managed block and `SKILL.md` "full" (fragments allowed where meaning
holds); references and packs "lite" (tight complete sentences).

| Text | Now | Budget |
| --- | --- | --- |
| Managed block (`templates/agent-block.md`) | ~1,160 tokens | 750 |
| `SKILL.md` | ~2,080 tokens | 1,500 |
| Top-level `references/*.md` (total words) | measured before | at least 20% smaller |
| Each pack | at most 2,000 | at most 2,000, lite pass |

`validate.sh` enforces the new budgets. Every rewrite passes `check_compression.py` (section 7) and
the content tests; the benchmark (section 11) confirms no quality loss.

## 7. Workflows: Compress, Comments, Minimal Code

- **`/clean-code compress [files]`** (`references/compress.md`): rewrite a project's instruction
  files (default: AGENTS.md, CLAUDE.md, GEMINI.md, DESIGN.md, ARCHITECTURE.md, CONTRIBUTING.md, and
  `.cursor`/`.github` rule files) tersely; keep a `<name>.original.md` backup until the user deletes
  it; never touch the clean-code managed block (the installer owns it); run `check_compression.py`
  and report the reduction.
- **`scripts/check_compression.py ORIGINAL COMPRESSED`**: exits 1 when the compressed file lost a
  heading, a fenced code block, an inline code span, a URL, a rule ID (`G17`, `N7`, `A3`), or a
  number; prints word and token counts and the reduction. Standard library only; used by the
  command and by this release's own rewrites.
- **Comment cleanup** (`references/comments.md`, routed from the Load Plan and from `clean-up`):
  classify each comment by Clean Code's good and bad kinds; delete the bad (redundant, noise,
  journal, attribution, closing-brace, position markers, mandated doc that restates the signature,
  commented-out code); turn "what" comments into names (explanatory variable or extracted
  function); rewrite surviving "why" comments caveman-terse; keep legal headers, warnings, and
  public API docs, tersely. The `comment-heavy` finding picks the files.
- **Minimal code** (ponytail's ladder, an always-on rule in `SKILL.md`): before writing code, ask
  in order: does it need to exist (YAGNI), does the codebase already have it, does the standard
  library, the platform, or an installed dependency do it, is it one line; only then write the
  minimum. Safety (validation, error handling, security, accessibility) is never cut.

## 8. PR #6 Ideas

Credit kyuna0312 in the CHANGELOG.

- **Agent smells A1-A10** replace the untagged Agent Failure Modes table in `review-checklist.md`:
  hallucinated API, unverified dependency, context loss, scope creep, duplicate implementation,
  wrong-file gravity, phantom success, test weakening, speculative abstraction, silent architecture
  drift; one line each for signal and response. `chapter-map.md` and `smell-triage.md` cite the A
  group beside G, N, and T.
- **`/clean-code plan <task>`** (`references/plan.md`): read context, find existing
  implementations, verify installed APIs, place the change, and write a plan under fixed headings;
  edit nothing.
- **`/clean-code review`**: review the current change (working tree, then staged, then named
  files) with `map_structure.py --changed`, `check_boundaries.py`, and the checklist; findings first,
  ranked P0-P3, each with a smell ID.
- **Risk-based verification**: LOW, MEDIUM, HIGH from scope, blast radius, uncertainty, and
  reversibility, each with the checks it owes before completion; the operating loop's verify step
  points to it.

## 9. Patterns Reference

New `references/patterns.md` (at most about 3,500 tokens), routed from the Load Plan ("choosing or
reviewing an architecture style, design pattern, or data-access approach"). One entry per concept
in goal 9: intent in one line; when it earns its place; when it is over-engineering (ponytail's
ladder); its link to the books (the Dependency Rule, SOLID, component principles, Humble Object,
Main as the ultimate detail, the database and web as details, G-codes); and which packs' frameworks
embody it (for example Rails and Django models as Active Record, Doctrine and SQLAlchemy as Data
Mapper with Unit of Work, EF Core's `DbContext` as Unit of Work, Dapper as a micro ORM, Knex and
Kysely as query builders, Spring and ASP.NET Core containers as IoC). Original synthesis only.

## 10. New Packs

| Pack | Kind | Detection |
| --- | --- | --- |
| `languages/css.md` | language | existing `CSS` label |
| `languages/sass.md` | language | existing `SCSS` and `Sass` labels |
| `frameworks/tailwind.md` | framework | `tailwindcss` in `package.json` |
| `frameworks/drupal.md` | framework | `drupal/core` or `drupal/core-recommended` in `composer.json` |
| `frameworks/wordpress.md` | framework | `wp-config.php`, a `wp-content/` folder, or WordPress core in `composer.json` |
| `frameworks/tensorflow.md` | framework | existing `TensorFlow` label |
| `frameworks/pytorch.md` | framework | existing `PyTorch` label |
| `frameworks/unity.md` | framework | `ProjectSettings/ProjectVersion.txt` or `com.unity.` packages in `Packages/manifest.json` |

Each follows the pack template and budget, carries a `clean-roles` block where the framework has
conventional homes (Drupal modules, WordPress plugins, Unity `Editor/` folders and asmdefs, PyTorch
`nn.Module` and `Dataset`, Keras `Model` and `Layer`), a coherent layer block, sources in
`docs/pack-sources.md`, an index line, and an eval case. Laravel: re-verify against current docs.

## 11. Evals Iteration 2

- New cases: PR #6's planted flaws ported to graded expectations (hallucinated API, unverified
  success, unsafe refactor), a frontend case, a naming case, and a comment-cleanup case, plus the
  eight new pack cases.
- `grade.py` gains `command_passes` (runs a command in the workspace with a timeout; passes on exit
  0) so "tests still pass" is checkable, with a test.
- Sharper expectations: tests added, packs read before the first edit (ordering in the transcript),
  naming and comment findings absent in changed files.
- Run: with and without the skill, two runs each on Sonnet over the new planted-flaw, frontend,
  naming, and comment cases plus iteration 1's two discriminating cases (`core-context-gate`,
  `core-init`), and one run each on Haiku over the same set as a small-model probe; record pass rates, tokens, and time in
  `evals/README.md`, with the same honesty about confounds as iteration 1.

## 12. Verification And Done

Unit tests (new tests for every rule, threshold, and command), `validate.sh`, the CI steps by hand,
markdownlint, the originality check, sync no-op, line endings, the map on this repository and
read-only on Inklusit.Core, the benchmark, and a final whole-branch review. Then the handoff with
improvement ideas and the merge, PR, and release question.

## 13. Risks

- **Terseness hurting small models**: mitigated by keeping full words and imperatives and by the
  Haiku probe; revert a file's rewrite if the probe regresses.
- **Naming noise**: every rule has exemptions and a test with idiomatic code that must stay silent;
  conventions come from each language, never one global style.
- **Unreferenced false positives** (framework discovery, reflection, DI): excluded when a file holds
  a role or sits at an entry point; labelled "possibly unused", never a verdict.
- **Reorganization breakage**: done first, as one behavior-preserving batch, with the suite green
  before and after and every documented command re-run.
