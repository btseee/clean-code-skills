# Architecture Map

Routing table: the architectural question you face, and the rule that answers it — the reasoning
lives in `architecture.md`.

## By question

| The question in front of you | The rule that decides it |
| --- | --- |
| Where does this new module belong? | Level = distance from I/O. Business rules highest, delivery mechanisms lowest |
| May this import that? | The Dependency Rule: inward only, never outward |
| Two modules need each other | A cycle. Invert one edge, or extract a component both depend on |
| Where does the interface go? | On the side that *uses* it — owned by its user, not its implementer |
| One module or two? | Which actor can demand a change? Different actors, different modules |
| These two blocks look identical | True duplication — must they always change together? If not, leave them apart |
| Add an abstraction here? | Only for a second implementation or a boundary you must protect now |
| Should this be a service? | Not for decoupling alone — a process boundary is not an architectural one |
| Which database / framework / UI? | A detail. Defer it; design so the answer can change |
| Framework wants to be my base class | Refuse. Derive a proxy in an outer layer instead |
| Where does dependency injection go? | `main` only. Inject there, then pass dependencies onward normally |
| Where does SQL go? | The data-access layer, nowhere else |
| Pass this ORM object inward? | No. Define a structure per crossing and copy the fields |
| This code is hard to test | Split it. The untestable half must be humble: no decisions in it |
| How do I stop layer bypasses? | Access modifiers, one public entry point per component — let the compiler enforce it |
| Build a full boundary? | Only once building it costs less than going without |
| Component too unstable to depend on? | `I = Fan-out / (Fan-in + Fan-out)`. `I` must decrease in the direction of dependency |
| Is this component badly balanced? | `D = \|A + I - 1\|`. Investigate above ~0.1 or beyond one standard deviation |
| A small requirement forced a large diff | An architecture defect. Scope should drive difficulty, never shape |
| Structure's a mess — rewrite it? | No — the team that made the mess rebuilds it. Refactor in verified batches |

## By topic

Named rules live in one place each; this file does not restate them:

- **`canon.md`** — every named rule from both books, one-line meaning. Start here for a name
  without its rule.
- **`architecture.md`** — the reasoning, following its own `## Contents` list.

## Reading order

Coming to this cold, in this order:

1. The Dependency Rule and level (`architecture.md`'s first two sections) — decides most
   placement questions alone.
2. SOLID as dependency rules — most module-shape questions.
3. Boundaries and their costs — when to separate, how far.
4. Packaging and enforcement — whether any of it survives a deadline.
5. Component metrics — only with evidence needed over opinion.
