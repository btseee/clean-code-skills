# Changelog

All notable changes to this project. Versions follow semver; the version in `VERSION` is the single
source and the git tag must match it exactly.

## 4.0.0

Stack-aware release. The skill now carries a short, strict pack for each of 19 languages and 21
frameworks, loads only the packs a project needs, and maps every file's functions and classes to
show misplaced, mixed, and duplicated code in one place. The core shrank so the context an agent
must read before its first edit stays small on any model.

### Breaking

- **Layer rules are framework-first.** The skill follows each framework's own idiomatic structure,
  and the strict Clean Architecture layer rules apply only when `.clean/architecture.md` declares
  layers. Projects that relied on layers being assumed should declare them; `/clean-code init`
  asks, and proposes an ordering from the detected layer candidates.
- **`questions` is now `init`.** `references/questions.md` became `references/init.md`; the
  `questions` command still works as an alias. `init` detects the stack, runs the interview, maps
  the structure, and writes `.clean/`.
- **The managed block changed**: placement is role-based and the layer section is framework-first.
  Re-run the installer to update it.

### Added

- **Language and framework packs** under `references/languages/` and `references/frameworks/`:
  TypeScript, JavaScript, Python, Java, C, C++, C#, PHP, Go, Rust, Swift, Objective-C, Kotlin, Ruby,
  Shell, PowerShell, R, Dart, Scala; React, Next.js, Vue and Nuxt, Angular, Svelte and SvelteKit,
  Django, Flask, FastAPI, Express, NestJS, Strapi, Spring, ASP.NET Core with EF Core, Laravel,
  Symfony, Ruby on Rails, Gin and Beego, Ktor, Jetpack Compose, SwiftUI and UIKit, Flutter. Language
  packs cover names, functions and types, errors, modules, placement, tests, layers, enforcement,
  and smells; framework packs cover structure, roles, rules, layers, tests, enforcement, and smells.
  Each stays under 2,000 tokens.
- **Pack routing.** `framework-map.md` holds the pack index; `detect_stack.py` records the selected
  packs in `context.json` as `packs` and prints them under **Read next**. It also detects SvelteKit,
  Strapi, Beego, Spring, the ASP.NET Core SDK, Jetpack Compose, Ktor, SwiftUI, and UIKit.
- **`map_structure.py`**, the structure map: one table of every file with its purpose, symbols,
  and roles, plus findings for misplaced symbols (middleware declared in `auth.ts` is reported with
  a move to `middleware/`), files mixing several roles, duplicated bodies, clashing names, synonym
  verbs, component coupling metrics (Ca, Ce, I, A, D), and folder cycles. `--write` saves
  `.clean/structure.md` and `.clean/structure.json`; the SessionStart hook prints the findings.
  Symbol extraction covers all 19 languages with the standard library only.
- **Role conventions** in fenced `clean-roles` blocks (homes by glob, roles by name or declaration
  signal), overridable per project in `.clean/roles.md`. In a monorepo, a framework pack speaks
  only for the project whose manifest named its framework (`pack_scopes` in `context.json`), and
  `supersede` applies within one manifest, so a Strapi CMS never hides the React app beside it.
- **An eval harness**: `evals/grade.py` grades a run against a case's deterministic expectations
  and exports `evals/evals.json` in skill-creator's layout; 33 cases, one per pack plus four core
  cases, and `evals/triggers.json` for description tuning. `evals/README.md` records the first
  benchmark on ten cases: every expectation passed with the skill, 95.5% without it, at about
  48% more tokens per task.
- **A unit test suite** (`tests/`, standard library `unittest`), run by `validate.sh` and CI.
- `docs/install.md`, `docs/configuration.md`, and `docs/pack-sources.md`, the sources each pack was
  checked against.

### Changed

- **`SKILL.md` is a lean router** of about 1,950 tokens that opens with the context gate: read
  `.clean/`, run the detector, read the named packs, then edit. `validate.sh` enforces the budgets:
  `SKILL.md` at most 3,000 tokens, the managed block 1,200, each pack 2,000.
- **The README is short**; install and configuration details moved to `docs/`.
- The agent failure-mode and anti-loophole tables moved from `SKILL.md` to `review-checklist.md`.
- Import parsing moved into `project_imports.py` and now reads Shell, PowerShell, R, and
  Objective-C imports; `scan_repo.py` shares the generated-file detection of the new map, which
  also recognizes generated files by name (`*.Designer.cs`, `*.g.cs`, `*_pb2.py`, `*.pb.go`), so
  they no longer count as large files.
- Every script prints UTF-8, so non-ASCII text reaches an agent intact through a Windows pipe.

### Fixed

- **`check_boundaries.py` layer globs**: a leading `**/` now also matches a top-level folder, and
  folders that only hold sources (`src/main/java`, `include/`, R's `R/`) no longer become namespace
  tokens, which had classified every `java.*` import into the first declared layer.
- **`check_boundaries.py` sees an import on the first line of a file that starts with a
  byte-order mark**, as Visual Studio writes by default; such a file could pass while breaking the
  declared layers.
- **No script crashes on piped output in Windows** when a path, name, or summary holds a
  character outside the console code page; `detect_stack.py --write` saves its file first.

## 3.2.0

Deepening release, driven by an architecture review of the repository's own hot spots: the
install, validate, and sync scripts and the three bundled Python scanners. One user-visible fix;
the rest removes duplicated knowledge so the next host or the next marker change is one edit.

### Fixed

- **`check_boundaries.py` no longer misses Python relative imports.** `from ..infra.db import Db`
  inside the domain layer passed, because an unresolvable relative import fell through as a fake
  path that `fnmatch` then matched against the source layer. Resolution is now a pure function over
  root-relative paths that understands Python's dotted form and returns unknown, never a guess.
  `allow x -> *` and `deny x -> *`, which parsed but were ignored, are honoured. The report counts
  imports that landed outside every declared layer, and CI drives the classifier with a table.

### Changed

- **Hosts live in one table.** `templates/hosts.tsv` holds every profile, scope, kind, path, and
  detect flag; `install.sh`, `install.ps1`, and `sync.sh` read it, and `validate.sh` asserts it
  agrees with the adapter list. Detection is derived from the same rows the installer applies.
  After `--global agents`, `--detect` now reports `codex opencode agents`, so the shared skill
  folder is updated along with the two blocks.
- **One managed-block implementation in bash.** `merge_block`, `remove_block`, and the version
  parse moved into `scripts/install-lib.sh`, sourced by `install.sh` and `sync.sh`; `sync.sh` lost
  its own awk and its GNU-only `sed -i`, so it runs on macOS, and CI runs it on a synced tree and
  asserts the tree stays clean.
- **`validate.sh` is the validator on Windows too**, run under Git Bash in CI. `validate.ps1`
  shrank to the one thing bash cannot observe: exercising `install.ps1`. Windows contributors run
  `bash scripts/validate.sh` from Git Bash; users are unaffected.
- **The three scanners share one project walker.** `skills/clean-code/scripts/project_files.py`
  owns skip rules, the file cap, capped reads, and test-path detection; the copies had drifted
  (different skip lists, caps of 40000, 20000, and none, different test folder names). Every
  scanner now reports `scan_truncated` when the cap cut a walk short.

## 3.1.1

Hardening release: three read-only deep-scan passes walked the skill the way a user would — a cold
agent following every pointer, the four commands and three scripts against a real project, and the
docs against actual behavior. Everything below fixes something one of those passes found.

### Fixed

- **`detect_stack.py --write` no longer clobbers `context.json`.** It merges: detector-owned keys
  are refreshed; the reserved `confirmed` object (the interview's answers — purpose, actors,
  verify command, load-bearing dependencies, notes) and any unknown keys survive. `questions.md`
  and `memory-protocol.md` define the schema. Previously, running the audit after the interview
  silently destroyed the interview.
- **`check_boundaries.py` fails instead of passing when its globs match no files** — exit 2 with an
  explicit error in both output modes. A fitness function that can silently check nothing is worse
  than none.
- **`scan_repo.py --json` is now always complete**; `--top` caps only the human summary (with an
  explicit "... and N more" line). The audit's convergence loop compares full lists, so a capped
  list no longer turns "entry 16 became visible" into a phantom new finding.
- **`scan_repo.py --changed` says so when git is unavailable** — a `scope_note` in JSON and a
  stderr warning — instead of reporting an empty scan that looks like a clean change.
- **The pre-commit hook finds every install location**: `.grok/skills` and the global roots
  (`~/.claude/skills`, `~/.agents/skills`, `~/.grok/skills`, `~/.gemini/config/skills`) joined the
  candidate list; the phantom `.clean/skill` candidate is gone; a config error (exit 2) now gets
  its own message instead of being reported as a violation. `claude-settings.json` probes the same
  locations and `python3`/`python`/`py` instead of hardcoding both.
- **`assets/templates/ledger.md` gained the `## Audit Coverage` section** the audit protocol has
  been instructed to fill since 3.1.0 — inventory count, reviewed count, sweeps, findings per
  sweep, and the per-file checklist. Section names are now identical across the template,
  `memory-protocol.md`, and `project-refactor.md`.
- **`install.ps1`'s help text and unknown-profile error caught up with its implementation**: both
  now list `grok` and `antigravity`, and global mode's documented roots include `~/.agents/skills`,
  `~/.grok/skills`, and `~/.gemini/config/skills`. (`install.sh` was already right.)
- `assets/templates/architecture.md` replaced its unexplained `<skill>` path placeholder with real
  install-location examples; `examples.md` says three output templates, not two; `host-matrix.md`
  lost a duplicated intro sentence and now marks `scripts/install.sh` and `clean-code.zip`
  explicitly as repository artifacts that do not ship inside the skill folder.

### Changed

- **One rule for who creates `.clean/`, stated once**: reading it is always fine; creating it is
  the `audit` and `questions` workflows' job. `SKILL.md` step 1 no longer suggests `--write` in a
  plain session, and `session-protocol.md` steps 19–20 write to `.clean/` only when it exists,
  offering to persist otherwise.
- **`clean-up` without a ledger asks first**: it proposes the audit, names the project's file
  count, and waits for consent instead of launching hours of unasked work. The campaign contract is
  negotiated once — the audit drafts it, Phase 0 confirms it.
- **The audit protocol scales honestly** (`audit-report.md`): per-file ticks to ~500 files,
  per-directory with flagged-directory detail to ~2,000 (shape agreed with the user), module-scoped
  audits beyond that. The denominator is stated (`git ls-files`; script counts are code-only
  subsets), the report's destination is stated (the conversation — `.clean/` holds the ledger), and
  sweep comparison explicitly uses the full JSON.
- **`new-project <description>` finally says what the description is for**: the draft answer set
  for Phase 0 — extract what it answers, ask only what it leaves open.
- `argument-hint` moved from an HTML comment into SKILL.md frontmatter, where Claude Code actually
  reads it and other hosts ignore it per the spec's unknown-key rule.
- `detect_stack.py` no longer counts a generic `app/` directory as an application-layer hint — the
  boundary checker deliberately discards that guess, and now the two scripts agree.
- README truth pass: the `.clean/` table (dependencies, `confirmed`, real creators), the validator
  paragraph (byte-identical round trip, final-newline check, the `skill-tools` CI job), the
  `detect_stack.py` example output (all nine summary lines plus dependencies and layer candidates),
  the audit example (coverage line, dependencies, placement), the global-install root list, the
  twelve-host shared-root count, and the four manifest descriptions, which still described the
  pre-3.0.0 comment-focused package.

### Not verified

- The zero-match failure mode of `check_boundaries.py` and the new hook messages are covered by
  fixtures on Windows (Git Bash `sh`) and by the CI `skill-tools` job on Linux, but not on macOS.
- Cross-host behavior remains conformance-based, as the README's constraints section states — no
  new smoke tests on other hosts were run for this release.

## 3.1.0

Field-driven release: every change answers a failure observed using v3.0.0 on a real project.

### Added

- **Argument commands.** The skill routes its invocation argument: `/clean-code audit`,
  `/clean-code new-project <description>`, `/clean-code clean-up`, `/clean-code questions` (Codex:
  `$clean-code ...`, Codex App: `@clean-code ...`, Kimi Code: `/skill:clean-code ...`; plain
  language works everywhere).
- **The interview** (`references/questions.md`): `/clean-code questions` asks for purpose, actors,
  layers, verify command, no-go zones and decoupling mode, and writes the answers into `.clean/`.
- **Dependency awareness.** `detect_stack.py` now records every declared dependency **with its
  version** into `context.json` — package.json, requirements.txt, pyproject, go.mod, Cargo.toml,
  csproj (including .NET Central Package Management via Directory.Packages.props), composer.json,
  Gemfile. `framework-map.md` gains the discipline: verify APIs against installed versions, follow
  each package's intended usage, report stale majors, never upgrade silently.
- **Comment-block detection.** `scan_repo.py` flags runs of eight or more consecutive comment
  lines (license headers exempt); `principles.md` states the size discipline — a comment longer
  than about three lines is knowledge in the wrong place.
- Clean Architecture fidelity additions, text-verified against the source: the three paradigm
  discipline statements and falsifiability, the plugin argument, state-and-mutability as an
  architectural choice (segregation of mutability, event sourcing), the four things architecture
  must support, Conway's law, the two values, the third cohesion-tension edge, ISP's
  typing-dependence, the standard-library marriage exception, and the hardware-abstraction layer.
- *(Backfilled in 3.1.1 — shipped in the 3.1.0 tag but missing from this entry.)* **Every named
  host**: `grok` and `antigravity` install profiles in both installers, the host matrix expanded to
  fifteen vendor-verified rows with per-host invocation forms, and the README's prompt-usage
  section.

### Changed

- **The audit is now exhaustive by protocol** (`references/audit-report.md`): a full file inventory
  becomes a coverage checklist in `.clean/ledger.md`; every file is reviewed and ticked; sweeps
  repeat until a complete pass adds zero new findings (minimum two, cap four, honestly reported);
  and the audit **fills `.clean/`** — context.json, architecture.md (ordering confirmed with the
  user), decisions.md, ledger.md with a ready batch plan. `clean-up` consumes that ledger.
- The cleanup campaign gains two mandated batches: **placement** (move misplaced files to their
  intended directories and rewire completely) and **package idioms** (align usage with what the
  installed dependency intends).
- `memory-protocol.md`: the audit and questions workflows are the sanctioned creators of `.clean/`.
- The managed block's comment rule now includes size: a paragraph of comment is a design smell.

### Fixed

- `canon.md` presented `D = 0.1` as the investigation threshold; the book's criterion is
  statistical — one standard deviation from your design's own mean — with 0.1 only as the example
  plot's control limit. Corrected in `canon.md` and `architecture.md`.
- `smell-triage.md` folded volatility into the Zone of Pain definition; it is a separate axis.
- Two dangling cross-references (`canon.md`, `concurrency.md` pointing at architecture.md for
  mutability content it lacked) now resolve.
- *(Backfilled in 3.1.1.)* `scan_repo.py` stopped flagging prose comments as commented-out code —
  a line is code-like only with code punctuation or a short fragment, so `# from sleeping
  processes` no longer counts.
- *(Backfilled in 3.1.1.)* Three defects caught by the field test: `detect_stack.py` reported
  Next.js on a .NET solution (framework signatures now respect word boundaries and skip comments),
  reported "Quality tools: none" despite pyproject `[tool.*]` sections, and `scan_repo.py` raised a
  false "no test files" alarm on projects with a separate top-level test tree.

## 3.0.0

The clean-architecture half, the machinery repairs that let the package build at all, and full
coverage of the clean-code source.

### Added

- **Architecture guidance** (`references/architecture.md`): the dependency rule, level as distance
  from I/O, the four circles and what may cross them, boundary costs and the three partial-boundary
  forms, SOLID stated as dependency rules, component cohesion and coupling with the instability,
  abstractness and distance metrics, policy versus detail, systems and cross-cutting policy,
  testability, the four packaging strategies, and the decoupling modes.
- **Test discipline** (`references/tests.md`): the Three Laws of TDD, the F.I.R.S.T. properties,
  BUILD-OPERATE-CHECK, single concept per test, the domain-specific testing language, the dual
  standard, and the failure modes — structural coupling, GUI-driven business tests, test-blessing.
- **Concurrency** (`references/concurrency.md`): defense principles, the three named execution models
  including Dining Philosophers, locking discipline, the four deadlock conditions, and seven distinct
  tactics for actually catching a race.
- **Canon index** (`references/canon.md`): every named rule from both sources with a one-line
  operational meaning and a pointer to its detail — so a finding can cite a rule by name.
- **Worked examples** (`references/examples.md`): before-and-after cases in Python, TypeScript, Go
  and SQL, plus templates for honest completion reports, campaign contracts, and review findings.
- **Routing and workflow references**: `architecture-map.md`, `smell-triage.md`,
  `session-protocol.md`, `new-project.md`, `audit-report.md`, `memory-protocol.md`, `host-matrix.md`,
  and `principles.md`.
- **Tools** (`skills/clean-code/scripts/`, standard library only, no network): `detect_stack.py`
  (language, frameworks, test command, layout), `scan_repo.py` (oversized files, sibling variants,
  junk drawers, debug output, skipped tests, untested areas), `check_boundaries.py` (dependency
  direction against a declared layering).
- **Durable project context** in a `.clean/` directory — `context.json`, `architecture.md`,
  `decisions.md`, `ledger.md` — so an agent with no memory of the project reconstructs it from disk.
  Templates in `assets/templates/`.
- **Hooks** (`assets/hooks/`): a portable git `pre-commit` hook, which is the only enforcement that
  behaves identically on every host, plus Claude Code session-start and post-edit settings.
- **Four named workflows** — session, onboard, bootstrap, audit — each backed by a reference file and
  each usable with no tooling at all.
- Two adapter files that had never existed: `.windsurf/rules/clean-code.md` and
  `.clinerules/clean-code.md`.
- CI now runs markdownlint and exercises the three scripts, including a fixture that must fail the
  dependency check and then pass.

### Changed

- `SKILL.md` is a router rather than the whole skill: 372 lines and under 5,000 tokens, inside the
  Agent Skills budget, with depth in `references/` that loads on demand. Both validators now enforce
  that ceiling.
- `templates/agent-block.md` is a thin pointer block carrying the non-negotiables, instead of a lossy
  second copy of `SKILL.md` that would drift.
- Permissions are declared in the `compatibility` frontmatter field rather than relying on the
  experimental `allowed-tools`.
- `validate.ps1` reaches parity with `validate.sh`. It had been missing the editor front-matter
  checks, the syntax checks and the line-ending sweep, so the Windows CI job passed content the Linux
  job rejected.
- Both validators additionally check the `SKILL.md` size budget, that bundled Python imports nothing
  outside the standard library, and that no shipped file carries an absolute machine path.

### Fixed

- **The copyright guard had been lost.** `.gitignore` had been replaced with a generic template that
  dropped every project rule, leaving the source PDFs untracked but unignored — one `git add -A` from
  being published from a public repository.
- **Two adapters could never be committed.** The `clean-code.md` ignore pattern was unanchored, so it
  also matched `.windsurf/rules/clean-code.md` and `.clinerules/clean-code.md` — files required by
  `sync.sh`, both validators and the `all` install profile. Both CI jobs had therefore never passed.
  The patterns are now root-anchored.
- **The line-ending check never worked.** `grep -q $'\r'` does not detect CR under the grep shipped
  with Git for Windows, so the sweep reported success on any input. It now forces binary mode and
  verifies its own detector against a known-CRLF fixture before trusting the result.
- **`G7` was miscited.** It is "base classes depending on their derivatives", not a general
  dependency-direction smell, and `chapter-map.md` promises stable citable IDs. Layering violations
  moved to the architectural smells where they belong.
- **`J2` and `J3` were missing** from the smell catalogue; both are portable and now carry their IDs.
  `J1` is documented as intentionally omitted so the numbering stays auditable.
- The Appendix C cross-reference table is now an actual table of root causes, not a statement that
  cross-referencing is a good idea.
- The Ch15 case-study section is grounded in the real lessons — redundant member prefixes, hidden
  temporal coupling through member variables — rather than plausible invention.
- The "write tests first *when feasible*" hedge is gone; the Three Laws are stated as laws, with
  honest deviation required instead of a standing exemption.
- The departure from the Boy Scout Rule is now **documented**. This skill deliberately narrows it to
  "clean the lines your task already touches" because an agent applying it broadly produces
  unreviewable diffs, and silently contradicting the source was worse than explaining the trade.

### Removed

- `FRAMEWORKS.md` — zero unique content against `references/framework-map.md`.
- `EXAMPLES.md` — 15 of 16 sections restated `SKILL.md`, and no installed skill could reach the file.
  Its unique code snippets moved into `references/examples.md`.
- `skills-lock.json` — a lockfile pinning an unrelated third-party tool, referenced nowhere.
- The duplicated "By topic" section of `architecture-map.md`, a third compression of
  `architecture.md`.
- The `curl | bash` self-update instruction from the managed block: it required network plus shell,
  failed on sandboxed hosts, and was a supply-chain surface.
- About 280 lines of unrelated Python and Node boilerplate from `.gitignore`.

### Not verified

No cross-host smoke test was run. Portability rests on conformance to the Agent Skills specification
and on the per-host audit in `references/host-matrix.md`, not on observed behavior in Copilot CLI,
Codex, Cursor or Gemini CLI.

## 2.1.0 and earlier

See the git history. No releases were published before 3.0.0.
