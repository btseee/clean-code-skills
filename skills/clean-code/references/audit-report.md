# Audit Protocol

For "audit this project", `/clean-code audit`, "how clean is this codebase", or as the mandatory
first half of a cleanup. The audit does two things: it produces a **report**, and it populates
**`.clean/`** so that the cleanup — this session or any later one — starts from durable state
instead of from memory. It changes no production code.

**An audit is complete only when every inventoried file has been reviewed and a full sweep adds
zero new findings.** Anything less is a partial audit, and partial audits are why projects need
auditing three times. The criterion is checkable, so check it before claiming completion.

## Phase A — Inventory: establish the denominator

1. Enumerate every tracked file: `git ls-files` (fall back to a full directory walk excluding
   dependency and build directories when there is no git).
2. Record the total count and the list, grouped by directory, into `.clean/ledger.md` as a
   **coverage checklist** — one tick-box per file (batch trivially small files per directory, but
   list them). Use `assets/templates/ledger.md` as the frame if the file does not exist.
3. Nothing below counts as done until the ticked set equals this inventory. A file never ticked was
   never audited, whatever the summary claims.

## Phase B — Evidence: run the measurements

- `scripts/detect_stack.py --write` — stack, frameworks, test command, layout, **dependencies with
  versions**, saved to `.clean/context.json`. Manual equivalent: derive the same facts by reading
  the manifests, and write them into `context.json` by hand — it is only a cache of what the project
  already says.
- `scripts/scan_repo.py --json` — oversized files, sibling variants, junk drawers, debug output,
  commented-out code, comment blocks, skipped tests. Manual equivalent: targeted searches for each.
- Run the project's own verification and record the result **verbatim** — this is the baseline, and
  a red baseline must be written down, not worked around.
- `scripts/check_boundaries.py` once a layering is declared (Phase D). Manual equivalent: read the
  imports of the innermost modules.

Script output is evidence for judgement, never a verdict.

## Phase C — Read pass: earn the numerator

Work through the inventory directory by directory, ticking files in the ledger as they are read.
For every file, judge at least:

- **Responsibility** — does it pass the one-sentence test; which actor owns it?
- **Placement** — does its directory match its responsibility, per the declared layers and the
  conventions in `framework-map.md`? A file in the wrong folder goes in the ledger as a **move
  candidate** with its intended destination. This is where "the files are not in the right folders"
  gets caught — placement is audited per file, not noticed incidentally.
- **Dependencies** — anything imported against the grain (details in policy, wrong-way layer
  imports, a package used against its documented intent for the installed version in
  `context.json`)?
- **Smells** — anything from `smell-triage.md`, cited by ID.
- **Tests** — is this file's behavior verifiable, and does anything here explain a coverage gap?

Small files are read in batches; generated files are ticked as "generated, skipped" — a decision,
not an omission.

## Phase D — Fill `.clean/` (the audit's second deliverable)

1. `context.json` — already written by Phase B.
2. `architecture.md` — from `assets/templates/architecture.md`: the detected layer candidates as a
   starting point, **ordering confirmed with the user** — innermost-first order is a decision, not
   an inference, and both a strict and a pragmatic reading can be legitimate. Once written, run
   `check_boundaries.py` and add its violations to the ledger.
3. `decisions.md` — initial entries: the verify command, the layering choice and why, declared
   no-go zones, and any deliberate exception discovered during the read pass.
4. `ledger.md` — convert the findings into the prioritized batch plan of
   `project-refactor.md`, with a proposed campaign contract (depth, breadth, behavior policy,
   checkpoint style) at the top, ready for the user to approve when they ask for the cleanup.

## Phase E — Convergence: the loop that replaces "audit it again"

After the first full pass, sweep again: re-run the scripts, re-check the ledger against the
inventory, and re-examine every file the first pass flagged plus every file *adjacent* to a finding
(same directory, same responsibility, callers and callees). New findings go in the ledger.

- **The audit closes only when a complete sweep adds zero new findings.**
- Minimum two full sweeps, always. If sweep N found anything new, sweep N+1 is mandatory.
- Cap at four sweeps; if the fourth still finds new material, close anyway and state plainly what
  was still churning and where — an honest open end beats a false clean bill.
- Record in the ledger: `inventoried N / reviewed N / sweeps M / new findings per sweep: a, b, c`.

## Phase F — Report

Findings first, ordered by consequence. Same structure as before, plus the coverage line at the
top of the verdict.

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
Declared layering; dependency direction with counts; boundaries present and missing; details
leaking inward; testability without infrastructure; cycles.

## Dependencies
Installed versions from context.json; anything used against its documented intent; majors that
look stale (verify currency yourself only where you have web access — never guess).

## Placement
Move candidates from the read pass: file, intended home, what re-wiring the move needs.

## What is already good
<Real strengths — they tell the next agent what to imitate.>

## Recommended sequence
<Ordered by risk reduced per effort; first item independently valuable.>
```

Rules that keep the report worth reading: severity is consequence, not untidiness; no finding
without a location; count instead of listing when instances are many; separate measured from
inferred; formatting belongs to the formatter, not to the report.

## After the audit

The state is on disk, so the follow-up is cheap:

- **"Clean it up" / `/clean-code clean-up`** → `project-refactor.md`, consuming the ledger's batch
  plan — the contract is already drafted, the baseline already recorded. Never begin editing
  straight from the report; the ledger is the working document.
- Re-run the audit after the campaign and compare coverage lines, so improvement is measured
  rather than asserted.
