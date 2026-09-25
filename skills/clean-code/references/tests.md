# Tests

Tests decide whether any rule here applies: no tests, no refactoring; no refactoring, rot. Read
this when writing tests, changing tested behavior, or scoping verification.

## The Three Laws of TDD

1. Write no production code until you have written a failing test.
2. Write no more of that test than is sufficient to fail — including failing to compile.
3. Write no more production code than is sufficient to pass the currently failing test.

The cycle runs in tens of seconds; tests and code grow together.

**No escape hatch.** "When feasible" becomes never under pressure. Where you truly can't go
test-first — an unfamiliar API, a throwaway spike, code with no harness — say so, and what you did
instead. Silence isn't honest.

For an agent: a test you watched fail, then pass, is evidence, not a memory claim. One written
afterwards, against code you already wrote, mostly re-asserts your assumptions.

## Why clean tests matter more than clean production code

Tests keep code flexible, maintainable, reusable — the *-ilities*: the higher their quality, the
less fear changing it, the better the design.

The inverse runs fast: dirty tests rot as code evolves, fail for the wrong reasons, get deleted or
skipped — then production code can't change safely. **A test suite abandoned for being
unmaintainable takes the production code's flexibility with it.** Test code is production code; no
lower standard.

## Readability, and the dual standard

Readability — clarity, simplicity, density of expression — makes a test useful: say the maximum
with the minimum.

Tests get a **dual standard**: less efficient than production code is fine — they run where
memory and cycles rarely matter — but not less *clear*. Trade efficiency for readability; never
readability for cleverness.

## BUILD-OPERATE-CHECK

The default shape of a test, in three visible parts:

1. **Build** the data and world the test needs.
2. **Operate** on it — the single action under test.
3. **Check** that the outcome is what was expected.

Keeping the three parts visually distinct is most of what makes a test readable. When Build grows
too large, extract it into a helper — how a testing language starts.

## A domain-specific testing language

Tests read best in a vocabulary built for themselves — helpers and builders stating the behavior
described, not the mechanics of arranging it. Refactor this language into existence: notice the
same setup three times, name it.

The point isn't brevity — a reader should tell what the test asserts without decoding how it got
there.

## One assert, and single concept per test

The commonly quoted rule is one assert per test. Treat it as direction, not law: asserts should be
**minimized** — the real rule is **one concept per test**.

- Multiple asserts on one concept are fine — an outcome with several fields is one concept.
- Split a test whose name needs "and": it is testing two concepts, exactly as with functions.

Why: a test checking three concepts fails for three reasons, telling you almost nothing — the
second and third go unchecked once the first breaks.

## The F.I.R.S.T. properties

- **Fast.** Slow tests run rarely; rarely-run tests stop catching things, then rot.
- **Independent.** No test sets up the world for another — order dependence hides a cascading
  failure's cause.
- **Repeatable.** Same result anywhere, including offline and on a laptop, or it gets ignored when
  it fails elsewhere.
- **Self-validating.** Pass or fail. Reading a log or eyeballing files makes evaluation subjective,
  and the test optional.
- **Timely.** Written just before the code it covers — written after, that code tends to resist
  testing.

## What to test, matched to risk

| Change | Verification that actually proves it |
| --- | --- |
| Pure function | Focused unit test on behavior and boundaries |
| Bug fix | A test that reproduces the bug first, then goes green |
| Refactor | Existing tests, run before and after; add characterization tests first if none exist |
| API or boundary change | Contract or integration test at the boundary |
| Concurrency change | See `concurrency.md` — a normal unit test proves very little here |
| Legacy code with no tests | Characterization tests capturing current behavior, oddities included |

Boundary conditions, and code near a bug you just found, deserve extra attention: defects cluster.

## Failure modes to avoid

- **Structural coupling to production code** — a test class or method per production one: fragile
  tests, rigid production code, blocked from growing more general as tests grow more specific.
- **Driving business rules through the UI** — the most volatile surface in the system. Test
  through the use case; keep the view humble (see `architecture.md`).
- **Weakening, skipping, or deleting a failing test to get green** buries information, turning a
  known problem into an unknown one — the most damaging thing an agent can do to a codebase: it
  removes the signal everything else depends on.
- **Broad snapshots as the only assertion** — pass until everything changes at once, then explain
  nothing.
- **Sleeps and timing guesses.** Flaky by design; see `concurrency.md`.
- **Excessive mocking of your own code** — mocking three of your own modules asserts your design,
  not your behavior.
- **Tests that duplicate implementation logic** agree with the code by construction, even when
  the code is wrong.
- **Sporadic failures dismissed as noise** — treat them as candidate defects, usually threading.

## Where tests sit architecturally

Tests sit in the system's outermost circle: maximally detailed, depending inward, depended on by
nothing. The first design rule applies to them too — don't depend on volatile things.

When a suite needs privileged access to force states, bypass security, or avoid expensive
resources, that is a **testing API**: a superset of what the UI uses, hiding the application's
structure from tests. Keep it, and its dangerous implementation, in a separately deployable
component. See `architecture.md`.

## Related

- `principles.md` — the summary rules and the rest of the code-level detail.
- `concurrency.md` — why threaded code needs a different testing strategy.
- `architecture.md` — the test boundary, the humble object, and designing for testability.
- `chapter-map.md` — the T1-T9 test smells.
