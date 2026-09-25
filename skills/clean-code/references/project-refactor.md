# Project Refactor Protocol (Campaign Mode)

For cleanup as the task: "clean up this project", "refactor this module to clean code", "apply
clean code everywhere". Surgical-mode scope is suspended, not discipline: a structure-less campaign
becomes an unreviewable rewrite of behavior nobody asked for.

Large refactors fail predictably — context overflow, early session end, batches forgetting each
other, quality drift file 3 to 30 — and each step below counters one.

## Contents

- Phase 0: contract
- Phase 1: inventory and baseline
- Phase 2: plan in batches
- Phase 3: execute batch by batch
- Phase 4: consistency sweep and close
- The ledger; stop conditions; what this protocol is not
- Leaving it better than a checklist would

## Phase 0: Contract

Agree with the user before touching code:

- **Depth**: naming-and-dead-code pass? structural extraction? architectural re-layering? Each level multiplies risk.
- **Breadth**: whole project, selected modules, or one vertical slice as a pilot.
- **Behavior policy**: batches stay behavior-preserving; bugs found are logged, not fixed (invisible to review inside a rename batch) — confirm the user agrees, or carve a bug-fix lane.
- **Checkpoint style**: one commit per batch (preferred), or staged diffs for review.
- **No-go zones**: generated/vendored code, files with others' pending changes, anything the user marks off-limits.

"Clean it up" alone: propose a contract at your recommended depth/breadth; let the user confirm or
adjust — no editing while open. Negotiated once: an audit already drafted it atop
`.clean/ledger.md`, so this phase only confirms, taking amendments.

## Phase 1: Inventory And Baseline

**Audit already ran** (`.clean/ledger.md` holds a coverage checklist and batch plan): verify the
baseline, confirm the contract, go straight to Phase 3.

**No ledger**: propose the audit first, naming the file count as its cost — two typed words must
not launch unasked hours of work; wait for consent. Leaner fallback: the same measurements as
`audit-report.md` Phases A-B (`scripts/detect_stack.py --write`, full verification recorded
verbatim as the **baseline** — not a blocker if red, but must be written down — and a smell sweep
via `smell-triage.md`, `chapter-map.md`, `scripts/scan_repo.py`, `scripts/map_structure.py --write`),
minus the coverage checklist and convergence sweeps. Record findings as a file-path list — this
becomes the ledger.

1. Risky code with no tests: add characterization tests first, capturing current behavior (oddities included). Impractical: mark the area high-risk, reduce depth there.
2. Architectural inventory decides what later batches can safely do:
   - Layering declared? `.clean/architecture.md` is the contract if present, else the framework pack's idiomatic structure; re-layering in scope: infer it, show the user, confirm.
   - Dependencies pointing the wrong way? `scripts/check_boundaries.py` once layers are declared; otherwise check imports of modules you believe innermost.
   - Cycles between components (which edge to invert), and details reaching inward — ORM types, framework annotations, HTTP objects, raw rows in business rules?
   - Business rules testable with no infrastructure running? If not, that finding gates everything else.

## Phase 2: Plan In Batches

Batches sized to fit one session and review. Two strategies; pick per campaign:

- **By module**: all smells within one module/directory — best for independent modules, visible completion.
- **By smell family**: one mechanical change across many files (rename a concept everywhere, normalize error wrapping, delete dead code, fix import order) — best when codebase-wide consistency matters more than local completeness. Keep mechanical sweeps separate from structural batches: a rename sweep plus extractions is unreviewable.

Order batches by risk and value:

1. Safety first: dead code removal, single-caller duplication, formatter-only formatting. Low risk, shrinks the problem. Before deleting an `unreferenced` file, search its path, module, and stem in manifests (pyproject scripts and entry points, package.json `bin`/`main`/`exports`), Procfile, Dockerfile, CI files, HTML, and string imports; a runtime-loaded file gets an `entry` line in `.clean/roles.md` instead.
2. Naming/readability: renames, explanatory variables, comment cleanup per `comments.md`, starting with files the map reports `comment_heavy`. Low risk, tooling-supported.
3. **Placement**: start from `.clean/structure.md`'s `## Proposed moves` (`from -> to (why)`: misplaced symbols, file families, junk-drawer splits) — confirm each against the code (evidence, not verdict), drop or amend any the audit rejected. Move every confirmed file and symbol to its intended home; rewire completely: imports, exports, registrations, build config. One behavior-preserving batch (or per module), verified before and after — `scripts/map_structure.py --path <folder>` should no longer report it. A half-moved file is worse than unmoved.
4. **Package idioms**: align usage with each installed dependency's intent, per `.clean/context.json` and `framework-map.md` — replace hand-rolled code with what the library provides, fix misused APIs. Version *upgrades* are a `decisions.md` entry, not this batch.
5. Structure: extractions, responsibility splits. Medium risk; needs tests.
6. Boundaries/error handling: wrapping third-party APIs, normalizing failure paths. Higher risk; needs contract awareness.
7. Architecture: re-layering, dependency direction fixes. Highest risk; only within the agreed depth.

Write the plan into the ledger before batch 1.

## Phase 3: Execute Batch By Batch

For each batch:

1. Re-read target files fresh — earlier batches may have changed them; stale context reintroduces deleted code.
2. Make the changes, applying the full skill: placement, one job per unit, naming, error handling.
3. Run verification relevant to the batch, the broader suite every few batches. Compare against baseline: no new failures.
4. Update the ledger: done, found, deferred, anything that changes the plan.
5. Checkpoint: commit with a message describing the batch, or present the diff, per the contract.
6. A batch went sideways: report it honestly; revert to the checkpoint rather than patch forward.

Batch hygiene: one batch, one intent — commit message passes the one-sentence test. Balloons past
intent: stop, checkpoint what is coherent, re-plan the remainder. Never carry uncommitted work
forward.

## Phase 4: Consistency Sweep And Close

After the planned batches:

1. Sweep for consistency debts the batches created: old/new naming coexisting, half-migrated patterns, imports of moved code. Half-done renames are worse than none.
2. Run the full verification suite; compare to baseline; record the final state.
3. Close the ledger: done, deferred (with reasons), bugs found (for the user to prioritize), recommended next campaigns.
4. Summarize for the user: batches completed, verification evidence, behavior risks taken (ideally none), deferred list.

## The Ledger

A plain markdown file surviving context loss and session ends. Default home `.clean/ledger.md`,
started from `assets/templates/ledger.md` (full structure there); keep it wherever preferred,
uncommitted unless asked. See `memory-protocol.md` for its fit with other durable state. Skeleton:

```markdown
# Cleanup Ledger: <project> — <date>

## Audit Coverage
## Contract
## Baseline
## Batches
## Found But Not Fixed
## Deferred
```

Re-read the ledger at every session start and before every batch — the recovery point after lost
context.

## Stop Conditions

Pause and report instead of pushing through when:

- baseline cannot be established (build broken, tests cannot run) — fixing it needs the user's go-ahead
- a batch requires a behavior change to proceed
- a risky area has no tests and characterization is impractical
- the same conflict recurs between local style and clean-code rules — surface it once, get a ruling, apply consistently
- remaining context is too small to finish the batch safely — checkpoint, continue in a fresh session from the ledger

## What This Protocol Is Not

- Not a license to rewrite: preserve public behavior and contracts unless contracted otherwise.
- Not a style crusade: the project's formatter, linter, and idioms define style; the campaign enforces, not replaces, them.
- Not all-at-once: thirty files in one pass make thirty unreviewable diffs.
- Not an architecture redesign in disguise: re-layering is the highest-risk depth, only inside the agreed contract — architecture as the real problem: say so, let the user decide.

## Leaving it better than a checklist would

Removing smells alone yields a tidier version of the same design. What lowers the cost of change,
usually in this order:

1. **Declare the architecture** in `.clean/architecture.md` — cheapest batch, turns every later argument into an automated check.
2. **Add tests that make risky areas verifiable.**
3. **Fix dependency direction** on the worst offenders — inner modules naming outer ones.
4. **Remove the cycles** — components build and release independently again.
5. **Pull details out of policy**: ORM types, framework annotations, HTTP objects — out of business rules, behind interfaces the rules own.
6. **Then** code-level work: naming, function size, duplication, dead code.

Record decisions and why in `.clean/decisions.md` as you go — the next agent inherits the reasoning,
not just the result.
