# Memory Protocol

You forget everything between sessions; the project doesn't. These files carry its design intent,
letting a memoryless agent rebuild what it needs from the repo alone.

Everything lives in `.clean/` at the project root; templates in `assets/templates/`.

| File | Holds | Written by | Read when |
| --- | --- | --- | --- |
| `context.json` | detected stack, frameworks, packs needed, test command, layout, dependencies with versions; the interview's `confirmed` object | `scripts/detect_stack.py --write` (refreshes, keeps rest), `init`'s interview, or hand-written | every session, first |
| `architecture.md` | declared layers and allowed dependencies; its absence means framework-first | `init`/`audit` if opted in, ordering user-confirmed, or a human | every session; enforced by `check_boundaries.py` |
| `decisions.md` | decisions made and why, append-only | any session that made a real choice | before proposing a design change |
| `ledger.md` | audit coverage checklist and findings, then cleanup-campaign state | `audit` workflow first; campaign sessions keep it current | before starting or resuming audit/campaign |
| `structure.md`, `structure.json` | every file's symbols, role, purpose; placement, duplication, naming, cycle findings; component metrics | `scripts/map_structure.py --write`, run by `init`, `audit`, sessions adding/moving files; never hand-edited | before changing an area: grep its rows |
| `roles.md` | the project's `clean-roles` conventions and confirmed placement exceptions | `init`, `audit`, or a human; grammar in `framework-map.md` | read by `map_structure.py`; overrides the packs |

## Rules

**Read before deciding.** Context, architecture, decisions, ledger, area structure rows — before
touching code (order: `session-protocol.md`). A recorded decision is settled: report a wrong-looking
one, don't reopen it.

**`architecture.md` outranks your instincts** — the project's stated intent. Disagreeing code is a
finding to report, not licence to follow.

**Write only what the next session cannot re-derive.** Skip what the code shows; record the
*reasoning* it can't: why this boundary, not that one; what was rejected; what forced an unusual
choice.

**Never invent history.** Don't know why something is the way it is? Write it as an open question,
not a plausible reason — a confident wrong entry is worse than none: the next session will trust
it.

**Append; do not rewrite.** `decisions.md` is a log — supersede an entry with a new one referencing
it, not by editing the past.

**Who creates `.clean/`.** `init`, `audit`, and `new-project` create and populate it — invoking them
is the consent. A plain coding session never introduces it silently: it offers at the end.

**The structure map is a cache, not a record.** Never hand-edit `structure.md` or `structure.json`;
regenerate them. The header names the commit it was generated at; if that differs from
`git rev-parse --short HEAD`, regenerate before trusting a row.

**Default to untracked.** Add `.clean/` to `.gitignore` unless design intent should be committed.
`architecture.md` is the one file usually worth committing: a shared decision driving a CI check.

## What to record, and what not to

Record:

- a choice between real alternatives, and why the loser lost
- a deliberate deferral, and what should trigger revisiting it
- a constraint discovered the hard way (an API limit, a migration hazard, a load-bearing quirk)
- a deviation from this skill or the project's conventions, and its justification
- a boundary decision: where the line is and which side owns the interface
- an open question the user needs to answer

Do not record:

- what the code plainly shows
- a summary of what you changed — the commit message's job
- restatements of this skill's rules
- anything you are guessing about

## Formats

### `context.json`

Two key kinds share the file. **Detector-owned** (`primary_language`, `frameworks`, `dependencies`,
`suggested_verify_commands`, plus `detect_stack.py`'s output) cache the project's own data;
`--write` refreshes them, keeping the rest. **`confirmed`** is a reserved object for humans and the
`init` interview — facts detection can't infer:

```json
"confirmed": {
  "purpose": "what the system is for, one sentence",
  "actors": ["who demands changes"],
  "verify_command": "the command the user actually trusts",
  "load_bearing_dependencies": ["packages the design leans on"],
  "notes": "anything else the next session must not rediscover"
}
```

`confirmed` outranks detected keys on disagreement — a person said so.

### `decisions.md`

Append-only. Newest last. One entry per decision:

```markdown
## <date> - <short title>
**Decision**: <what was decided, in one sentence>
**Context**: <what forced the choice>
**Alternatives**: <what else was considered, and why it lost>
**Consequences**: <what this makes easy, and what it makes hard>
**Revisit if**: <the condition that would change the answer, or "n/a">
```

### `ledger.md`

Audit and campaign state — the file that makes multi-session cleanup survivable; see
`audit-report.md`, `project-refactor.md`. Keep it current *during* work: an accurate ledger with an
interrupted campaign beats a finished one with a stale ledger.

Sections, in template order: Audit Coverage (the per-file checklist and convergence line), Contract,
Baseline, Batches (a checklist with commit references), Found But Not Fixed, Deferred, Close-out.

### `architecture.md`

Prose for humans plus a fenced `clean-architecture` block; layers declare innermost first, each
depending only on itself and layers before it. Format: `assets/templates/architecture.md`; reasoning:
`references/architecture.md`. (Three files share this name: template, reference, `.clean/architecture.md`.)

## If the host has session hooks

Some hosts run a command at session start: printing `.clean/context.json`, packs, layer declaration,
and structure findings is the highest-value hook — it removes the chance an agent forgets to look.
See `host-matrix.md`, `assets/hooks/`.

Absent that, step 1 of `session-protocol.md` substitutes — hence step 1.
