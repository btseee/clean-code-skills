# Init Protocol

For `/clean-code init`, alias `/clean-code questions` ("set up clean-code" / "interview me"). One
command detects the stack, interviews the user, maps the structure into durable `.clean/` state,
read instead of guessed — fastest path to context, the opener when sessions repeat themselves.

Invoking it consents to creating `.clean/`. Add it to `.gitignore` unless design intent should be
committed (`memory-protocol.md`).

## 1. Detect

Run `scripts/detect_stack.py --write`, or by inspection write the same into `.clean/context.json`:
languages, frameworks, packs needed, test command, source/test layout, dependencies with versions.
Detection first means every question carries **a proposed answer** — a guess is corrected more
willingly than a blank form. Then read the packs listed.

## 2. Interview

Ask in order, one topic at a time, offering the detected candidate as default. Skip what the
project's files already answer; say what was found.

1. **What is this system for, and who are its actors?** Groups who can demand a change — finance,
   operations, end user, another team. Actors decide module boundaries later: a vague answer is
   worth one follow-up.
2. **Should layers be enforced?** Default is no — follows the framework pack's structure. For strict
   clean-architecture layers, present detected candidates and an ordering, innermost first — that's
   the Dependency Rule, defined in `memory-protocol.md`. Mental model differs from the folders? It
   wins; log the mismatch in the ledger.
3. **Which dependencies are load-bearing?** Show the detected list with versions; ask which are
   deliberate, which incidental.
4. **What command proves a change?** The one they trust, not the one README claims.
5. **No-go zones?** Generated code, vendored trees, another person's in-flight work.
6. **Deliberate exceptions?** Where rules are knowingly bent, and why — undocumented, it reads as a
   permanent defect. A placement exception is an `accept` line in `.clean/roles.md` (`accept <glob>`,
   or `accept <glob> = <symbol>` for one symbol), clearing that structure-map flag.
7. **Decoupling mode?** One address space, separately deployable units, or services — what would
   justify moving.

## 3. Map

Run `scripts/map_structure.py --write`: `.clean/structure.md` and `.clean/structure.json` record
every file's symbols, role, purpose, flagging misplaced, mixed, duplicated, clashing, synonymous
code, and component cycles. By hand: list each folder's role; note files that don't match.

## What Gets Written

| Answers | Land in |
| --- | --- |
| Layers, ordering, allowed exceptions (if opted in) | `.clean/architecture.md` — its fenced `clean-architecture` block, plus surrounding prose |
| Purpose, actors, verify command, load-bearing dependencies, anything else a person confirmed | `.clean/context.json` — the reserved top-level `confirmed` object |
| Every choice with a why: layering or its absence, exceptions, no-go zones, decoupling mode | `.clean/decisions.md` — one dated entry per decision |
| Placement exceptions the user confirmed | `.clean/roles.md` — a fenced `clean-roles` block (grammar in `framework-map.md`) |

Use `assets/templates/` for files that don't exist. `confirmed` is the interview's home in
`context.json` (schema: `memory-protocol.md`) — read, write under it, keep every detector key.
Symmetric: `detect_stack.py --write` refreshes only its keys, preserving `confirmed`; interview and
audit never destroy each other.

## 4. Close

Echo what was written and where, so the user can correct it. Summarize packs, whether layers are
enforced, and top structure findings. More than a handful of problems? Suggest `/clean-code audit`
— init records intent, audit verifies code.

## Rules

- One question at a time, each with its proposed default. No walls of questions.
- Never re-ask what `.clean/` already records — read it first, confirm only what looks stale.
- An "I don't know" is valid: record it as an open question in `decisions.md`, not a guessed fact.
- Init changes no production code.
