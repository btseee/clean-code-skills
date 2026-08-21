# Changelog

All notable changes to this project. Versions follow semver; the version in `VERSION` is the single
source and the git tag must match it exactly.

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
