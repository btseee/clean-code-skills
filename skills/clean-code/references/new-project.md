# New Project Protocol

Starting a project, or a major new module. Not the grandest structure — the cheapest correct first
decisions, keeping later ones open.

Governing idea: **a good architect maximizes the number of decisions not made.** Defer what can be
deferred; keep the domain independent of what is deferred.

**Invoked as `new-project <description>`**: the description is the draft answer set for Phase 0.
Extract what it already answers — purpose, actors, scope, vocabulary — read it back, ask only what
it leaves open. Never re-ask what it plainly states.

## Phase 0 — Understand before designing

**1. Clarify the requirements and scope.** What must the system do, for whom, what makes it
valuable — the two or three requirements most likely to change decide where the boundaries go. What
is explicitly *not* in version one, written down: the main defence against speculative structure.

**2. Identify the actors.** Which groups can demand a change — finance, operations, compliance, the
end user, another team? Different actors, different modules: this one question prevents the most
expensive later rework.

**3. Name the domain vocabulary.** Terms for core concepts, agreed now, used everywhere — types,
files, directories, tests. One word per concept, one concept per word.

Ask the user for anything above you cannot infer. Guessing the domain costs more than asking.

## Phase 1 — Design the shape

**4. Design the architecture before the code.** Policy vs. detail: business rules highest;
database, web, UI, framework, delivery mechanism are details.

**5. Define the domain model and module boundaries.** Critical Business Rules and Data — what
would exist on paper — form the innermost layer, depending on nothing; draw one boundary per axis
of change, one public entry point per component.

**6. Decide whether to enforce layers, then write the rules down.** No declaration: framework
pack's idiomatic structure applies; declared: layer rules become strict. Real business rules: write
`.clean/architecture.md` from `assets/templates/architecture.md`, innermost first (pack's
**Layers** section) — the project's constitution, read by later sessions, enforced by
`scripts/check_boundaries.py`.

**7. Choose the decoupling mode deliberately.** Source level first — one address space, function
calls — shaped so a service *could* be extracted later, not extracted until forced. Reversible both
ways.

**8. Create the project structure.** The framework pack's **Structure** section gives each role its
home; name top-level directories for the domain and its use cases, not the framework or technical
layers — the listing should teach a newcomer what the system is *for*.

## Phase 2 — Set the standards

**9. Establish coding standards by choosing tools, not writing prose.** A formatter, a linter, an
`.editorconfig`; tools own formatting so nobody argues about it.

**10. Design for testability from the first commit.** Business rules testable with no database, web
server, UI, or external service — not true day one, never true. The untestable half stays humble,
no decisions in it.

**11. Automate the quality checks.** Test command, linter, and — once layers are declared — a
dependency-direction check, one command, wired into CI. Team wants local enforcement: add the
pre-commit hook from `assets/hooks/`.

**12. Set up the memory files.** `.clean/` from `assets/templates/`: `decisions.md`, optional
`architecture.md`, `context.json` (`scripts/detect_stack.py --write`), `structure.md`
(`scripts/map_structure.py --write`) — or hand-write the same facts, since you just chose them.
Record the Phase 0 and Phase 1 decisions in `decisions.md` while fresh.

## Phase 3 — Build

**13. Implement vertical slices.** One complete use case end to end, through every layer, before
the next — a slice proves the architecture, a finished layer proves nothing.

**14. Keep abstractions minimal.** An interface for a second implementation or a real boundary,
never in anticipation. One implementation, no boundary: cost, no benefit.

**15. Prefer simplicity; resist the three temptations.** No premature optimization: measure first.
No premature generalization: build for the requirement in front of you. No premature distribution:
a network boundary is not a design.

**16. Keep the domain pure; confine wiring to `main`.** No framework annotations, ORM base classes,
or HTTP types in the domain — wrap a framework at the edge in a proxy instead. Configuration
reading, dependency injection, framework binding: one dirty low-level component nothing else
depends on; prefer a separate `main` per environment over configuration branches inside policy
code.

**17. Review architectural consistency, then scale only when needed.** Each milestone: dependencies
still point inward, no new cycle, structure still screams the domain. Add a boundary, service, or
cache on measured need — not before.

## What "done" means for version one

- A newcomer can tell from the directory names what the system does.
- The business rules can be tested with no infrastructure running.
- Every source dependency points inward, and the dependency check passes.
- One command runs the tests; one command runs the linter.
- `.clean/architecture.md` and `.clean/decisions.md` exist and are accurate.
- Nothing has been built for a requirement that does not exist yet.

## Anti-patterns specific to greenfield work

| Temptation | Why it costs |
| --- | --- |
| Scaffolding every layer before any feature works | You have proven nothing and now must maintain it all |
| Choosing the database and ORM first | The most deferrable decision, made at the moment you know least |
| Micro-services from day one | Expensive, coarse-grained, and hard to reverse; development time is the scarce resource, not CPU |
| A `utils` or `common` module in the first commit | It becomes the place where design goes to die |
| Generic `BaseEntity` / `BaseService` / `AbstractManager` classes | Inheritance is the most rigid dependency; you are committing before you know the shape |
| Copying a reference architecture wholesale | Structure without the reasoning behind it cannot be maintained or adapted |
| Configuration systems, plugin points, and feature flags before the second case exists | Speculative flexibility that ossifies into required complexity |
