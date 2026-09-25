# Canon

Every named rule this skill draws on: what it means, where the detail lives — find a rule by
name, or cite a finding precisely: "G30, and the arity is polyadic" is checkable; "this function is
messy" is not.

Names are the field's vocabulary; readings here are this project's.

## Code level

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **Boy Scout Rule** | Leave code cleaner than found. **Narrowed here**: clean touched lines, report the rest | `chapter-map.md` Ch1 |
| **LeBlanc's law** | Later equals never: deferred cleanup is cancelled cleanup | `chapter-map.md` Ch1 |
| **Intention-revealing names** | Name answers why it exists, not just its type | `principles.md` |
| **Avoid mental mapping** | Reader shouldn't translate terse name into concept | `principles.md` |
| **One word per concept** | One term per idea, codebase-wide — never two ideas, one term | `principles.md` |
| **Verbs and keywords** | Encode argument order and meaning into the name: `assertExpectedEqualsActual` | `principles.md` |
| **Do One Thing** | Function does one thing at one abstraction level — function-level rule, *not* SRP | `principles.md` |
| **The Stepdown Rule** | File reads top-down: callers above callees, each level more detailed | `principles.md` |
| **Function arity** | Niladic → monadic → dyadic → triadic → polyadic; three arguments need justifying, more need object | `principles.md` |
| **Flag argument** | Boolean parameter means function does two things — split it | `principles.md` |
| **Output argument** | Parameter mutated as return channel — return value instead | `principles.md` |
| **Command Query Separation** | Answer question or change state, never both | `principles.md` |
| **DRY** | One authoritative home per piece of knowledge, only for *true* duplication | `principles.md`, `architecture.md` |
| **Newspaper metaphor** | File opens with high-level intent; detail descends below | `principles.md` |
| **Vertical distance** | Related things stay close: declarations near use, caller near callee | `principles.md` |
| **Conceptual affinity** | Code reading as one idea stays together, even with no call between | `principles.md` |
| **Dummy scope** | Empty body hidden behind a semicolon — make visible, or remove | `principles.md` |
| **Data/object anti-symmetry** | Objects hide data, expose behavior; data structures reverse that — conflating them is defect | `principles.md` |
| **Law of Demeter** | Ask collaborator for decision; don't navigate its internals | `principles.md` |
| **Train wreck** | `a.b().c().d()` — coupling to every link in the chain (smell G36) | `principles.md` |
| **Hybrid** | Type exposing fields while pretending to protect invariants; pick one | `chapter-map.md` Ch6 |
| **DTO** | Structure for transport, no behavior implied | `chapter-map.md` Ch6 |
| **Special Case pattern** | Model expected alternate outcome as value/object, not exception | `principles.md` |
| **Checked vs unchecked exceptions** | Prefer unchecked: checked exceptions force every intermediate signature to change | `principles.md` |
| **Dependency magnet** | Shared error enum/constant forcing recompiles per user; prefer distinct types | `principles.md` |
| **Learning test** | Small test probing unfamiliar library, catches breaking upgrades later | `principles.md` |
| **Three Laws of TDD** | No code before failing test; no more test than fails; no more code than passes | `tests.md` |
| **F.I.R.S.T.** | Fast, Independent, Repeatable, Self-validating, Timely | `tests.md` |
| **BUILD-OPERATE-CHECK** | Three visible parts of a readable test | `tests.md` |
| **Single concept per test** | One idea per test; minimize asserts, not hard one-assert rule | `tests.md` |
| **Domain-specific testing language** | Helpers refactored into existence so tests read as described behavior | `tests.md` |
| **Dual standard** | Tests trade efficiency for clarity, never clarity for cleverness | `tests.md` |
| **Structural test coupling** | Test class per production class — fragile tests, rigid production code | `tests.md` |
| **Four rules of simple design** | In order: tests pass; no duplication; expresses intent; fewest elements | `principles.md` |
| **Successive refinement** | Make it work, then right, in verified steps — not giant rewrite | `chapter-map.md` Ch14 |

## Concurrency

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **Producer-Consumer** | Bounded queue between producers, consumers; failures are lost signals, unbounded blocking | `concurrency.md` |
| **Readers-Writers** | Many readers, few writers; decide deliberately which side may starve | `concurrency.md` |
| **Dining Philosophers** | Competition for shared resources; failure modes: deadlock, livelock, starvation. Fix via resource ordering | `concurrency.md` |
| **The four deadlock conditions** | Mutual exclusion, hold-and-wait, no preemption, circular wait — break any one | `concurrency.md` |
| **Segregation of mutability** | Push work into immutable components; confine mutation to few named places | `concurrency.md`, `architecture.md` |
| **Client-side vs server-side locking** | Where atomic sequence is enforced — choose it, don't stumble into it | `concurrency.md` |

## Architecture level

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **The three paradigm disciplines** | Structured disciplines direct control transfer, OO indirect transfer, functional assignment — each removes capability | `architecture.md` |
| **Falsifiability** | Tests show bugs' presence, never absence; correctness: failing to prove incorrectness | `architecture.md`, `tests.md` |
| **The plugin argument** | Plugin depends on host, can't break it — point arrows: business rules host, every detail a plugin | `architecture.md` |
| **The Dependency Rule** | Source dependencies point only inward, toward higher-level policy; inner code never names anything outer | `architecture.md` |
| **The four supports** | Architecture must support use cases plus operation, maintenance, development, deployment | `architecture.md` |
| **Conway's law** | System's structure mirrors its organization's communication structure | `architecture.md` |
| **The two values** | Behavior urgent, structure important; working-but-unchangeable worth less than broken-but-changeable | `architecture.md` |
| **Event sourcing** | Store transactions, not state; recompute by replay — concurrent update disappears | `architecture.md`, `concurrency.md` |
| **Level** | Distance from inputs and outputs — not call order | `architecture.md` |
| **SRP** | Module responsible to one, and only one, **actor** — not "does one thing" | `architecture.md` |
| **OCP** | Open for extension, closed for modification — to protect A from B, make B depend on A | `architecture.md` |
| **LSP** | Subtype usable wherever base is — call site needing to know implementation is violation | `architecture.md` |
| **ISP** | Don't depend on things you don't use; transitive baggage sets recompile and failure radius | `architecture.md` |
| **DIP** | Depend on abstractions; test is **volatility**, not abstractness | `architecture.md` |
| **REP** | Granule of reuse is granule of release | `architecture.md` |
| **CCP** | Gather what changes together, for same reasons — SRP for components | `architecture.md` |
| **CRP** | Don't force users to depend on what they don't need — ISP for components | `architecture.md` |
| **ADP** | No cycles in component dependency graph | `architecture.md` |
| **SDP** | Depend in direction of stability. `I` decreases along dependencies | `architecture.md` |
| **SAP** | Component should be as abstract as stable | `architecture.md` |
| **Instability `I`** | `Fan-out / (Fan-in + Fan-out)`; 0 is maximally stable | `architecture.md` |
| **Abstractness `A`** | Abstract types / total types in component | `architecture.md` |
| **Main Sequence, distance `D`** | `D = \|A + I - 1\|`; investigate components beyond one standard deviation of mean `D` — book's example uses `D = 0.1` as illustration | `architecture.md` |
| **Zone of Pain / Uselessness** | Stable-and-concrete; abstract-with-no-dependents | `architecture.md` |
| **Entity** | Critical business rules and data existing without software | `architecture.md` |
| **Use case** | Application-specific rules orchestrating entities; depends on entities, never reverse | `architecture.md` |
| **Humble Object** | Split hard-to-test from easy-to-test; humble half holds no decisions | `architecture.md` |
| **Screaming architecture** | Top-level structure names domain, not framework | `architecture.md` |
| **Main as the ultimate detail** | All wiring, configuration in dirtiest, lowest-level component | `architecture.md` |
| **Asymmetric marriage** | You commit to framework, it commits nothing back — use it, don't marry it | `architecture.md` |
| **Partial boundary** | Skip-the-last-step, one-dimensional, or facade — each with its own failure mode | `architecture.md` |
| **Decoupling modes** | Source, deployment, service — stay in one address space as long as possible | `architecture.md` |
| **The decoupling fallacy** | Process boundary doesn't decouple what shares a data record | `architecture.md` |
| **True vs accidental duplication** | True: always changes together. Accidental: changes at different rates, different reasons | `architecture.md` |
| **Organization vs encapsulation** | If every type is public, packages are just folders — architecture unenforced | `architecture.md` |
| **Cross-cutting concern** | Policy spanning modules — isolate it rather than scattering it | `architecture.md` |

## Smell IDs

Cite these directly in findings. Full catalogue and cross-reference table: `chapter-map.md`; usual
response for each: `smell-triage.md`.

| Group | Range | Covers |
| --- | --- | --- |
| **A** | A1-A10 | Agent smells: AI-written-code failure patterns, not from the book — see `review-checklist.md` |
| **C** | C1-C5 | Comments |
| **E** | E1-E2 | Environment: multi-step build or test |
| **F** | F1-F4 | Functions: arguments, output args, flags, dead functions |
| **G** | G1-G36 | General — largest group |
| **J** | J2-J3 | Language-specific that generalize (J1 intentionally omitted) |
| **N** | N1-N7 | Naming |
| **T** | T1-T9 | Tests |
