# Questions Protocol

For `/clean-code questions` or "interview me". The agent asks; the user answers; the answers become
durable state in `.clean/` that every later session — and every other agent — reads instead of
guessing. This is the fastest way to bootstrap a project's context without a full audit, and the
right opener when a session keeps having to ask the same things.

Run detection first (`scripts/detect_stack.py --write`, or by inspection) so every question below is
asked **with a proposed answer already on the table**. People correct a concrete guess far more
willingly than they fill a blank form.

## The interview

Ask in this order, one topic at a time, offering the detected candidate as the default. Skip any
question the project's files already answer unambiguously — say what was found instead of asking.

1. **What is this system for, and who are its actors?** The groups of people who can demand a
   change — finance, operations, the end user, another team. Actors decide module boundaries later,
   so vague answers are worth one follow-up.
2. **What are the intended layers, innermost first?** Present the detected layer candidates and a
   proposed ordering; make explicit that the order is the Dependency Rule itself — a layer may
   depend only on itself and the layers named before it. Where the user's mental model differs from
   the folders, the mental model wins and the mismatch goes in the ledger.
3. **Which dependencies are load-bearing?** Show the detected list with versions; ask which are
   deliberate choices worth defending and which are incidental.
4. **What command proves a change?** The real one they trust, not the one the README claims.
5. **No-go zones?** Generated code, vendored trees, another person's in-flight work, anything
   off-limits.
6. **Deliberate exceptions?** Places the rules are knowingly bent, and why — an undocumented
   exception reads as a defect forever.
7. **Decoupling mode?** One address space, separately deployable units, or services — and what
   would justify moving.

## What gets written

| Answers | Land in |
| --- | --- |
| Layers, ordering, allowed exceptions | `.clean/architecture.md` — the fenced `clean-architecture` block plus the prose around it |
| Purpose, actors, verify command, load-bearing dependencies, anything else confirmed by a person | `.clean/context.json` — the reserved top-level `confirmed` object |
| Every choice with a why: layering, exceptions, no-go zones, decoupling mode | `.clean/decisions.md` — one dated entry per decision |

Use `assets/templates/` for any file that does not exist yet. The `confirmed` object is the
interview's home in `context.json` (schema in `memory-protocol.md`):

```json
"confirmed": {
  "purpose": "...", "actors": ["..."], "verify_command": "...",
  "load_bearing_dependencies": ["..."], "notes": "..."
}
```

Read the file, write the answers under `confirmed`, keep every key the detector wrote. The
detector honors the same contract from its side: `detect_stack.py --write` refreshes only its own
keys and preserves `confirmed`, so the interview and a later audit never destroy each other.

## Rules

- One question at a time, each carrying its proposed default. No walls of questions.
- Never re-ask what `.clean/` already records — read it first and confirm only what looks stale.
- An "I don't know" is a valid answer: record it as an open question in `decisions.md`, not as a
  guessed fact.
- Close by echoing exactly what was written and where, so the user can correct it on the spot.
- The interview complements the audit, not replaces it: it captures *intent*; the audit verifies
  the code against that intent. Either can run first.
