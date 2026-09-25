# Audit Protocol

For "audit this project", `/clean-code audit`, "how clean is this codebase", or the first half of a
cleanup. Two deliverables: a **report** in the conversation, and **`.clean/`** populated on disk —
the ledger, not the report, lets the cleanup, this session or later, start from durable state, not
memory. No production code changes.

**Complete only when every inventoried file has been reviewed and a full sweep adds zero new
findings** — anything less is partial, why projects need auditing three times. Checkable: check
before claiming completion.

## Phase A — Inventory: establish the denominator

1. Enumerate every tracked file: `git ls-files` (no git: a directory walk excluding dependency/build
   directories). **This count is the audit's one denominator** — script totals (`files_scanned`,
   code-file counts) are code-only subsets, never the denominator.
2. Record the total and list, grouped by directory, into `.clean/ledger.md` as a **coverage
   checklist** — one tick-box per file (batch trivially small files, but list them);
   `assets/templates/ledger.md` is the frame if `.clean/ledger.md` does not exist.
3. Nothing counts as done until ticked equals inventoried. A file never ticked was never audited.

**Scale.** Up to ~500 files: tick per file. ~500-2,000: checklist per directory, ticking only where
findings turn up — agree the shape first. Beyond ~2,000: propose module-scoped audits, each with its
own inventory/convergence. Scope is always agreed out loud, never silently sampled.

## Phase B — Evidence: run the measurements

- `scripts/detect_stack.py --write` — stack, frameworks, test command, layout, **dependencies with
  versions**, into `.clean/context.json`. Merges: detector-owned keys refresh, an existing
  `confirmed` object survives untouched.
- `scripts/scan_repo.py --json` — oversized files, sibling variants, junk drawers, debug output,
  commented-out code, comment blocks, skipped tests; the JSON is always complete, `--top` caps only
  the summary.
- `scripts/map_structure.py --write` — every file's symbols, role, purpose, with misplaced, mixed,
  duplicated, clashing, synonymous, and badly named code flagged, file families, junk drawers,
  flat folders, unreferenced and comment-heavy files, `## Proposed moves`, plus component metrics
  and cycles, into `.clean/structure.md` and `.clean/structure.json` — a ready-made start for the
  Phase C read pass.
- Run the project's own verification; record the result **verbatim** — the baseline. A red baseline
  must be written down, not worked around.
- `scripts/check_boundaries.py` — a Phase D step (needs declared layering), listed here for
  completeness.

No script access: read the manifests into `context.json` by hand, search by hand for what
`scripts/scan_repo.py` flags, compare each folder's files to its role, read imports directly.

Script output is evidence for judgement, never a verdict.

## Phase C — Read pass: earn the numerator

Directory by directory, ticking files in the ledger as read. For every file, judge at least:

- **Responsibility** — passes the one-sentence test; which actor owns it?
- **Placement** — directory matches responsibility, per declared layers, the framework pack's
  roles, and `framework-map.md`? Confirm or reject each move in `.clean/structure.md`'s
  `## Proposed moves` (from `map_structure.py`) against the code — evidence, not verdict — before
  the clean-up campaign's placement batch acts on them. Record each confirmed move in the ledger as
  a **move candidate** with its destination; a deliberate exception becomes an `accept` line in
  `.clean/roles.md` and a `decisions.md` entry.
- **Duplication** — each group the map reports: true duplication (must change together) or
  accidental (different actors, different rates)? Only the first is a finding.
- **Dependencies** — anything against the grain (details in policy, wrong-way layer imports, a
  package used against its documented intent for the version in `context.json`)?
- **Smells** — anything from `smell-triage.md`, cited by ID.
- **Tests** — is behavior verifiable; does anything explain a coverage gap?

Small files read in batches; generated files ticked "generated, skipped" — a decision, not an
omission.

## Phase D — Fill `.clean/` (the audit's second deliverable)

1. `context.json` — already written by Phase B.
2. `architecture.md` — only if the user wants layers enforced. No declaration: framework pack's
   idiomatic structure; declared: layer rules strict. On yes, start from
   `assets/templates/architecture.md` with detected layer candidates, **ordering confirmed with the
   user** — innermost-first is a decision, not an inference. Once written, run
   `check_boundaries.py`, add violations to the ledger.
3. `decisions.md` — initial entries: verify command, layering choice and why, no-go zones, any
   deliberate exception found during the read pass.
4. `ledger.md` — findings become the prioritized batch plan of `project-refactor.md`, with a
   proposed campaign contract (depth, breadth, behavior policy, checkpoint style) atop, ready to
   approve at cleanup.

## Phase E — Convergence: the loop that replaces "audit it again"

After the first full pass, sweep again: re-run the scripts, re-check the ledger against the
inventory, re-examine every flagged file plus every file *adjacent* to a finding (same directory,
same responsibility, callers/callees). New findings go in the ledger. Compare sweeps on the full
JSON (`scan_repo.py --json`, `.clean/structure.json`), never capped summaries — a capped list turns
"entry 16 became visible" into a phantom finding.

- **The audit closes only when a complete sweep adds zero new findings.**
- Minimum two full sweeps always; sweep N found anything new, sweep N+1 is mandatory.
- Cap at four; the fourth still finds new material: close anyway, state plainly what was still
  churning and where.
- Record in the ledger: `inventoried N / reviewed N / sweeps M / new findings per sweep: a, b, c`.

## Phase F — Report

Findings first, ordered by consequence; delivered in the conversation, written to a file only if
asked. Structure:

```markdown
# Clean Code And Architecture Audit: <project>

**Date**: <date>   **Commit**: <sha>   **Scope**: <what was and was not examined>
**Coverage**: <N> files inventoried / <N> reviewed / <M> sweeps to convergence

## Verdict
<Three to five sentences. The most important structural fact, the biggest risk, and whether the
codebase is currently safe to change quickly. No hedging.>

## Baseline
- Verify command and verbatim result; untested areas; what could not be run.

## Findings
### Critical - wrong behavior or security risk
### High - blocks safe change
### Medium - raises the cost of every change
### Low - readability and consistency

<Per finding:>
**<Title>** - `path/file.ext:line`
- What: <observable fact>   Why it matters: <the failure it causes>
- Fix: <specific change>   Effort: <estimate>   Risk: <low/med/high>

## Architecture assessment
Declared layering, or "framework-first, no declaration"; dependency direction with counts;
boundaries present/missing; details leaking inward; testability without infrastructure; cycles and
the components furthest from the main sequence (D), from the structure map.

## Dependencies
Installed versions from context.json; anything used against documented intent; majors that look
stale (verify currency only where you have web access — never guess).

## Placement and duplication
Move candidates from the map and read pass: file or symbol, intended home, re-wiring needed. True
duplicates and their single intended home. Concepts named several ways, with the term to keep.

## What is already good
<Real strengths — they tell the next agent what to imitate.>

## Recommended sequence
<Ordered by risk reduced per effort; first item independently valuable.>
```

Severity is consequence, not untidiness; no finding without a location; count instead of listing
when instances are many; separate measured from inferred; formatting belongs to the formatter, not
the report.

## After the audit

State is on disk, so the follow-up is cheap:

- **"Clean it up" / `/clean-code clean-up`** → `project-refactor.md`, consuming the ledger's batch
  plan — contract already drafted, baseline already recorded. Never start editing straight from the
  report; the ledger is the working document.
- Re-run the audit after the campaign and compare coverage lines, so improvement is measured, not
  asserted.
