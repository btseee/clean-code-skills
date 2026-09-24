# Init Protocol

For `/clean-code init`, its alias `/clean-code questions`, or "set up clean-code" and "interview
me". One command does the whole first-time setup: detect the stack, interview the user, map the
structure. The answers become durable state in `.clean/` that every later session — and every
other agent — reads instead of guessing. It is the fastest way to give a project its context
without a full audit, and the right opener when sessions keep asking the same things.

Invoking it is the user's consent to create `.clean/`. Add `.clean/` to the project's `.gitignore`
unless the user wants the design intent committed (`memory-protocol.md`).

## 1. Detect

Run `scripts/detect_stack.py --write`, or by inspection write the same facts into
`.clean/context.json`: languages, frameworks, the packs they need, test command, source and test
layout, dependencies with versions. Detection comes first so that every question below is asked
**with a proposed answer on the table** — people correct a concrete guess far more willingly than
they fill a blank form. Then read the packs it lists.

## 2. Interview

Ask in this order, one topic at a time, offering the detected candidate as the default. Skip any
question the project's files already answer unambiguously — say what was found instead of asking.

1. **What is this system for, and who are its actors?** The groups of people who can demand a
   change — finance, operations, the end user, another team. Actors decide module boundaries later,
   so a vague answer is worth one follow-up.
2. **Should layers be enforced?** The default is no: the skill follows the framework pack's
   idiomatic structure. If the user wants strict clean-architecture layers, present the detected
   layer candidates and a proposed ordering, innermost first, and make explicit that the order is
   the Dependency Rule itself — a layer may depend only on itself and the layers named before it.
   Where the user's mental model differs from the folders, the mental model wins and the mismatch
   goes in the ledger.
3. **Which dependencies are load-bearing?** Show the detected list with versions; ask which are
   deliberate choices worth defending and which are incidental.
4. **What command proves a change?** The real one they trust, not the one the README claims.
5. **No-go zones?** Generated code, vendored trees, another person's in-flight work, anything
   off-limits.
6. **Deliberate exceptions?** Places the rules are knowingly bent, and why — an undocumented
   exception reads as a defect forever. A placement exception becomes an `accept` line in
   `.clean/roles.md` (`accept <glob>`, or `accept <glob> = <symbol>` for one symbol) so the
   structure map stops flagging it.
7. **Decoupling mode?** One address space, separately deployable units, or services — and what
   would justify moving.

## 3. Map

Run `scripts/map_structure.py --write`: `.clean/structure.md` and `.clean/structure.json` record
every source file's symbols, role, and purpose, and flag misplaced, mixed, duplicated, clashing,
and synonymous code plus component cycles. By hand: list each source folder with its role, and note
any file whose contents do not match that role.

## What Gets Written

| Answers | Land in |
| --- | --- |
| Layers, ordering, allowed exceptions (only if the user opted in) | `.clean/architecture.md` — the fenced `clean-architecture` block plus the prose around it |
| Purpose, actors, verify command, load-bearing dependencies, anything else confirmed by a person | `.clean/context.json` — the reserved top-level `confirmed` object |
| Every choice with a why: layering or its absence, exceptions, no-go zones, decoupling mode | `.clean/decisions.md` — one dated entry per decision |
| Placement exceptions the user confirmed | `.clean/roles.md` — a fenced `clean-roles` block (grammar in `framework-map.md`) |

Use `assets/templates/` for any file that does not exist yet. The `confirmed` object is the
interview's home in `context.json` (schema in `memory-protocol.md`):

```json
"confirmed": {
  "purpose": "...", "actors": ["..."], "verify_command": "...",
  "load_bearing_dependencies": ["..."], "notes": "..."
}
```

Read the file, write the answers under `confirmed`, keep every key the detector wrote. The detector
honors the same contract from its side: `detect_stack.py --write` refreshes only its own keys and
preserves `confirmed`, so the interview and a later audit never destroy each other.

## 4. Close

Echo exactly what was written and where, so the user can correct it on the spot. Summarize the
packs, whether layers are enforced, and the top structure findings. If the map found more than a
handful of problems, suggest `/clean-code audit` next — init records intent; the audit verifies the
code against it.

## Rules

- One question at a time, each carrying its proposed default. No walls of questions.
- Never re-ask what `.clean/` already records — read it first and confirm only what looks stale.
- An "I don't know" is a valid answer: record it as an open question in `decisions.md`, not as a
  guessed fact.
- Init changes no production code.
