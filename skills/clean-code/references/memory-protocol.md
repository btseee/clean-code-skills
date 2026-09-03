# Memory Protocol

You forget everything between sessions. The project does not. This file defines the small set of
files that carry a project's design intent forward, so an agent with no memory and no conversation
history can reconstruct what it needs from the repository alone.

Everything lives in a `.clean/` directory at the project root. Templates are in
`assets/templates/`.

| File | Holds | Written by | Read when |
| --- | --- | --- | --- |
| `context.json` | detected stack, frameworks, test command, layout, dependencies with versions; plus the interview's `confirmed` object | `scripts/detect_stack.py --write` (merges: detector keys refreshed, everything else preserved) and the `questions` interview; or hand-written | every session, first |
| `architecture.md` | declared layers and allowed dependencies | the `audit` or `questions` workflow — ordering confirmed with the user — or a human | every session; enforced by `check_boundaries.py` |
| `decisions.md` | decisions made and why, append-only | any session that made a real choice | before proposing a design change |
| `ledger.md` | the audit's coverage checklist and findings, then cleanup-campaign state | the `audit` workflow first; campaign sessions keep it current | before starting or resuming an audit or campaign |
| `commands.json` *(optional)* | the trusted install, test, lint, typecheck, and build commands | the `questions` interview, or a human | before running any check |
| `dependencies.json` *(optional)* | the few package versions an agent must verify APIs against | the `questions` interview or the audit, from the lockfile; or a human | before using any API of those packages |
| `conventions.json` *(optional)* | source root, test convention, module style, naming, placement | the `questions` interview or the audit; or a human | before creating or placing a file |

The three optional files exist because `context.json` is mostly *detected* and therefore mostly
*guessed*. They hold the small set of facts a person has confirmed and an agent would otherwise
re-derive wrongly: which command to trust, which versions matter, where files go. A `.clean/`
directory without them is still complete; nothing requires them, and every reader falls back to
`context.json` when they are absent.

## Rules

**Read before deciding.** All of `.clean/` that exists, at the start of the session, before touching code. A
recorded decision is settled: do not re-open it because you would have chosen differently. If it now
looks wrong, say so and let the user decide.

**`architecture.md` outranks your instincts.** It is the project's stated intent. If the code
disagrees with it, that is a finding to report, not a licence to follow the code.

**Write only what the next session cannot re-derive.** Do not record what the code already shows.
Record the *reasoning* that the code cannot: why this boundary and not that one, what was rejected,
what constraint forced an unusual choice.

**Never invent history.** If you do not know why something is the way it is, write that down as an
open question rather than a plausible-sounding reason. A confident wrong entry is worse than no
entry, because the next session will trust it.

**Append; do not rewrite.** `decisions.md` is a log. Supersede an entry with a new one that
references it, rather than editing the past.

**Who creates `.clean/`.** The `audit` and `questions` workflows create and populate it as part of
their job — that is what they are for, and the user invoking them is the consent. A plain coding
session still does not silently introduce the convention: it offers at the end.

**Default to untracked.** Add `.clean/` to the project's `.gitignore` unless the user wants the
design intent committed. `architecture.md` is the one file usually worth committing, because it is a
shared decision and it drives a check in CI.

## What to record, and what not to

Record:

- a choice between real alternatives, and why the loser lost
- a deliberate deferral, and the condition that should trigger revisiting it
- a constraint discovered the hard way (an API limit, a migration hazard, a load-bearing quirk)
- a deviation from this skill or from the project's own conventions, and its justification
- a boundary decision: where the line is and which side owns the interface
- an open question the user needs to answer

Do not record:

- what the code plainly shows
- a summary of what you changed — that is the commit message's job
- restatements of this skill's rules
- anything you are guessing about

## Formats

### `context.json`

Two kinds of keys share the file. **Detector-owned keys** (`primary_language`, `frameworks`,
`dependencies`, `suggested_verify_commands`, and the rest of what `detect_stack.py` emits) are a
cache of what the project already says; `--write` refreshes them and preserves everything else.
**`confirmed`** is a reserved top-level object owned by humans and the `questions` interview —
facts detection cannot infer:

```json
"confirmed": {
  "purpose": "what the system is for, one sentence",
  "actors": ["who demands changes"],
  "verify_command": "the command the user actually trusts",
  "load_bearing_dependencies": ["packages the design leans on"],
  "notes": "anything else the next session must not rediscover"
}
```

`confirmed` outranks the detected keys when they disagree, because a person said so.

### `commands.json`, `dependencies.json`, `conventions.json`

Flat JSON, one fact per key, templates in `assets/templates/`. Precedence when files disagree:

| Question | Answer from | Falls back to |
| --- | --- | --- |
| Which command proves a change? | `commands.json` | `context.json` `confirmed.verify_command`, then `suggested_verify_commands` |
| Which version of X is installed? | `dependencies.json` | `context.json` `dependencies`, then the lockfile itself |
| Where does a new file go; how is it named? | `conventions.json` | `context.json` `source_roots` and `tests`, then the two or three most similar existing files |

Rules: the file that a person confirmed wins; a detected value never overwrites a confirmed one;
an absent file is not an error. `dependencies.json` lists only packages whose API an agent has to
verify (frameworks, SDKs, anything with breaking majors), never the whole lockfile. Every key in
`conventions.json` is optional; delete what the project does not settle rather than guessing.

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

Audit and campaign state. The one file that makes a multi-session cleanup survivable — see
`audit-report.md` and `project-refactor.md`. Keep it current *during* the work, not at the end: an
accurate ledger and an interrupted campaign is a good outcome, while a finished campaign with a
stale ledger is not.

Sections, in template order: Audit Coverage (the per-file checklist and convergence line),
Contract, Baseline, Batches (a checklist with commit references), Found But Not Fixed, Deferred,
Close-out.

### `architecture.md`

Prose for humans, plus one fenced `clean-architecture` block that tools can read. Layers are
declared innermost first; the default rule is that a layer may depend only on itself and on layers
declared before it. See `assets/templates/architecture.md` for the full format and
`references/architecture.md` for the reasoning behind it. (Three files share the name: the
template, the reference, and the project's own `.clean/architecture.md` that the template becomes.)

## If the host has session hooks

Some hosts can run a command when a session starts. Where that exists, printing `.clean/context.json`
and the layer declaration at session start is the single highest-value hook available, because it
removes the chance that an agent simply forgets to look. See `host-matrix.md` and
`assets/hooks/`.

Where it does not exist, step 1 of `session-protocol.md` is the substitute — which is why it is step
1.
