# Architecture Map

Routing table: the architectural question you are facing, and the rule that answers it. Use this to
find the right rule fast; the reasoning lives in `architecture.md`.

## By question

| The question in front of you | The rule that decides it |
| --- | --- |
| Where does this new module belong? | Level = distance from I/O. Business rules highest, delivery mechanisms lowest |
| May this file import that one? | The Dependency Rule: inward only, never outward |
| Two modules need each other | You have a cycle. Invert one edge, or extract a component both depend on |
| Where do I put the interface? | On the side that *uses* it. The API is owned by its user, not its implementer |
| Should this be one module or two? | Which actors can demand a change? Different actors, different modules |
| These two blocks look identical | Is it true duplication — must they always change together? If not, leave them apart |
| Should I add an abstraction here? | Only for a second implementation or a boundary you must protect now |
| Should this be a service? | Not for decoupling alone. A process boundary is not an architectural boundary |
| Which database / framework / UI? | A detail. Defer it, and design so the answer can change |
| The framework wants to be my base class | Refuse. Derive a proxy in an outer layer instead |
| Where does dependency injection go? | `main` only. Inject there, then pass dependencies onward normally |
| Where does SQL go? | The data-access layer, nowhere else |
| Can I pass this ORM object inward? | No. Define a structure per crossing and copy the fields |
| This code is hard to test | Split it. The untestable half must be humble: no decisions in it |
| How do I stop people bypassing a layer? | Access modifiers and one public entry point per component. Let the compiler enforce it |
| Should I build a full boundary? | Only at the inflection point where building it costs less than going without |
| Is this component too unstable to depend on? | `I = Fan-out / (Fan-in + Fan-out)`. `I` must decrease in the direction of dependency |
| Is this component badly balanced? | `D = \|A + I - 1\|`. Investigate above ~0.1 or beyond one standard deviation |
| A small requirement forced a large diff | An architecture defect. Scope should drive difficulty, never shape |
| The structure is a mess — rewrite it? | No. The team that made the mess rebuilds it. Refactor in verified batches |

## By topic

Each topic below names the principle or rule, and the specific failure it prevents.

**Design goal.** Architecture minimizes the human effort to build and maintain the system. The
strategy is to leave options open; a good architect maximizes the decisions *not* made. Behavior is
urgent but not always important; structure is important but never urgent — which is why it loses
arguments it should win.

**Paradigms as discipline.** Structured programming disciplines direct transfer of control, giving
falsifiable units. Object orientation disciplines indirect transfer of control, giving absolute
control over source dependencies through polymorphism — that control is the whole architectural
payoff. Functional programming disciplines assignment; every race condition, deadlock, and
concurrent-update defect traces to a mutable variable.

**SOLID.** SRP: one actor per module — the misreading "do one thing" is a function-level rule, not
this one. OCP: extend without modifying; protect A from B by making B depend on A. LSP: a call site
that must know which implementation it has is the violation. ISP: do not depend on things you do not
use, because transitive baggage sets both your recompile and your failure blast radius. DIP: depend
on abstractions, where the test is volatility rather than abstractness.

**Component cohesion.** REP: the granule of reuse is the granule of release. CCP: gather what changes
together for the same reason. CRP: do not force users to depend on what they do not need. REP and CCP
grow components; CRP shrinks them. Favour CCP early, shift toward REP when real consumers appear.

**Component coupling.** ADP: no cycles — a cycle fuses components into one release unit. SDP: depend
in the direction of stability, where stability is the work required to change something. SAP: as
abstract as it is stable. SDP plus SAP is DIP at component scale.

**Boundaries.** Draw them on the axes of change, which is the SRP again. Full, partial (skip the last
step, one-dimensional, facade), or none — each partial form has a specific failure mode, and none
maintains itself without enforcement. Crossing cost rises steeply from function call to network, and
chattiness must match it.

**The circles.** Entities (enterprise critical rules), use cases (application-specific rules),
interface adapters (controllers, presenters, gateways, all SQL), frameworks and drivers (everything
else). Outer circles are mechanisms; inner circles are policies. Control flow crosses outward at the
end of a use case while source dependencies still point inward — resolved by an output port the use
case owns.

**Details.** The database is a detail; the data model is not. The web is a GUI, and a GUI is an I/O
device. Frameworks are an asymmetric commitment: use them, do not marry them. `main` is the ultimate
detail and the only place wiring belongs.

**Testability.** Tests are a system component in the outermost circle. The Humble Object pattern
splits hard-to-test from easy-to-test, and that split usually *is* the boundary. Structural coupling
— a test class per production class — makes tests fragile and production code rigid. Provide a
testing API rather than letting tests know the structure.

**Packaging.** Package by layer, by feature, by ports and adapters, or by component. If every type is
public, all four are syntactically identical and none is enforced: packages become folders. One
public entry point per component lets the compiler do the enforcing.

**Decoupling modes.** Source, deployment, service. Push to the point where a service *could* be
extracted, then stay in one address space as long as possible, and keep the move reversible in both
directions.

## Reading order

Coming to this cold, in this order:

1. The Dependency Rule and level (`architecture.md`, first two sections) — decides most placement
   questions on its own.
2. SOLID as dependency rules — decides most module-shape questions.
3. Boundaries and their costs — decides when to separate and how far.
4. Packaging and enforcement — decides whether any of it survives contact with a deadline.
5. Component metrics — only when you need evidence rather than opinion.
