# Changelog

All notable changes to this project. Versions follow semver; the version in `VERSION` is the single
source and the git tag must match it exactly.

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
