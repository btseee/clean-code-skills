# Canon

Every named rule this skill draws on: what it means operationally, and where the detail lives. Use
it to find a rule by name, or to cite a finding precisely — "G30, and the arity is polyadic" is
checkable in a way "this function is messy" is not.

Names are the field's established vocabulary. The operational readings are this project's.

## Code level

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **Boy Scout Rule** | Leave code cleaner than found. **Narrowed here**: clean only the lines your task touches, report the rest | `chapter-map.md` Ch1 |
| **LeBlanc's law** | Later equals never. A deferred cleanup is a cancelled one | `chapter-map.md` Ch1 |
| **Intention-revealing names** | Name answers why the thing exists, not just its type | `principles.md` |
| **Avoid mental mapping** | Reader shouldn't translate a terse name into the concept | `principles.md` |
| **One word per concept** | One term per idea codebase-wide; never one term for two ideas | `principles.md` |
| **Verbs and keywords** | Encode argument order and meaning into the name: `assertExpectedEqualsActual` | `principles.md` |
| **Do One Thing** | A function does one thing at one abstraction level — a function-level rule, *not* the SRP | `principles.md` |
| **The Stepdown Rule** | File reads top-down: callers above callees, each level one step more detailed | `principles.md` |
| **Function arity** | Niladic → monadic → dyadic → triadic → polyadic; three arguments needs justification, more needs an object | `principles.md` |
| **Flag argument** | Boolean parameter means the function does two things — split it | `principles.md` |
| **Output argument** | A parameter mutated as a return channel — return a value instead | `principles.md` |
| **Command Query Separation** | Answer a question or change state, never both | `principles.md` |
| **DRY** | One authoritative home per piece of knowledge — but only for *true* duplication | `principles.md`, `architecture.md` |
| **Newspaper metaphor** | File opens with high-level intent; detail descends below | `principles.md` |
| **Vertical distance** | Related things stay close: declarations near use, caller near callee | `principles.md` |
| **Conceptual affinity** | Code reading as one idea belongs together, even with no call between | `principles.md` |
| **Dummy scope** | Empty body hidden behind a semicolon — make it visible, or remove it | `principles.md` |
| **Data/object anti-symmetry** | Objects hide data, expose behavior; data structures reverse that. Treating one as the other is the defect | `principles.md` |
| **Law of Demeter** | Ask a collaborator for a decision; do not navigate its internals | `principles.md` |
| **Train wreck** | `a.b().c().d()` — coupling to every link in the chain (smell G36) | `principles.md` |
| **Hybrid** | A type exposing fields while pretending to protect invariants. Pick one | `chapter-map.md` Ch6 |
| **DTO** | A structure for transport, with no behavior implied | `chapter-map.md` Ch6 |
| **Special Case pattern** | Model an expected alternate outcome as a value or object, not an exception | `principles.md` |
| **Checked vs unchecked exceptions** | Prefer unchecked: a checked exception forces every intermediate signature to change, breaking encapsulation | `principles.md` |
| **Dependency magnet** | A shared error enum/constant class forcing recompiles on every user. Prefer distinct exception types | `principles.md` |
| **Learning test** | A small test probing an unfamiliar library, which then catches breaking upgrades | `principles.md` |
| **Three Laws of TDD** | No production code before a failing test; no more test than fails; no more code than passes | `tests.md` |
| **F.I.R.S.T.** | Fast, Independent, Repeatable, Self-validating, Timely | `tests.md` |
| **BUILD-OPERATE-CHECK** | The three visible parts of a readable test | `tests.md` |
| **Single concept per test** | One idea per test; minimize asserts, not a hard one-assert rule | `tests.md` |
| **Domain-specific testing language** | Helpers refactored into existence so a test reads as the behavior described | `tests.md` |
| **Dual standard** | Tests may trade efficiency for clarity, never clarity for cleverness | `tests.md` |
| **Structural test coupling** | A test class per production class — fragile tests, rigid production code | `tests.md` |
| **Four rules of simple design** | In order: all tests pass; no duplication; expresses intent; fewest elements | `principles.md` |
| **Successive refinement** | Make it work, then right, in small verified steps — not a giant rewrite | `chapter-map.md` Ch14 |

## Concurrency

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **Producer-Consumer** | Bounded queue between producers and consumers; failures are lost signals, unbounded blocking | `concurrency.md` |
| **Readers-Writers** | Many readers, few writers; decide deliberately which side may starve | `concurrency.md` |
| **Dining Philosophers** | Competition for several shared resources; failures are deadlock, livelock, starvation. Fix via resource ordering | `concurrency.md` |
| **The four deadlock conditions** | Mutual exclusion, hold-and-wait, no preemption, circular wait — break any one | `concurrency.md` |
| **Segregation of mutability** | Push work into immutable components; confine mutation to few named places | `concurrency.md`, `architecture.md` |
| **Client-side vs server-side locking** | Where the atomic sequence is enforced — choose it, don't stumble into it | `concurrency.md` |

## Architecture level

| Named rule | Operationally | Detail |
| --- | --- | --- |
| **The three paradigm disciplines** | Structured programming disciplines direct control transfer; OO disciplines indirect transfer; functional disciplines assignment — each removes a capability | `architecture.md` |
| **Falsifiability** | Tests show the presence of bugs, never their absence; correctness is failing to prove incorrectness | `architecture.md`, `tests.md` |
| **The plugin argument** | A plugin depends on its host, so it can't break the host — point arrows so business rules are the host, every detail a plugin | `architecture.md` |
| **The Dependency Rule** | Source dependencies point only inward, toward higher-level policy. Inner code never names anything outer | `architecture.md` |
| **The four supports** | Architecture must support use cases plus operation, maintenance, development, deployment | `architecture.md` |
| **Conway's law** | A system's structure mirrors the communication structure of its organization | `architecture.md` |
| **The two values** | Behavior is urgent, structure is important; working-but-unchangeable is worth less than broken-but-changeable | `architecture.md` |
| **Event sourcing** | Store transactions, not state; recompute by replay — concurrent update disappears | `architecture.md`, `concurrency.md` |
| **Level** | Distance from the inputs and outputs — not call order | `architecture.md` |
| **SRP** | A module is responsible to one, and only one, **actor**. Not "does one thing" | `architecture.md` |
| **OCP** | Open for extension, closed for modification — to protect A from B, make B depend on A | `architecture.md` |
| **LSP** | Subtype usable wherever the base is — a call site needing to know the implementation is the violation | `architecture.md` |
| **ISP** | Don't depend on things you don't use; transitive baggage sets your recompile and failure radius | `architecture.md` |
| **DIP** | Depend on abstractions. The test is **volatility**, not abstractness | `architecture.md` |
| **REP** | The granule of reuse is the granule of release | `architecture.md` |
| **CCP** | Gather what changes for the same reasons at the same time. SRP for components | `architecture.md` |
| **CRP** | Don't force users to depend on what they don't need — ISP for components | `architecture.md` |
| **ADP** | No cycles in the component dependency graph | `architecture.md` |
| **SDP** | Depend in the direction of stability. `I` decreases along dependencies | `architecture.md` |
| **SAP** | A component should be as abstract as it is stable | `architecture.md` |
| **Instability `I`** | `Fan-out / (Fan-in + Fan-out)`; 0 is maximally stable | `architecture.md` |
| **Abstractness `A`** | Abstract types / total types in a component | `architecture.md` |
| **Main Sequence, distance `D`** | `D = \|A + I - 1\|`; investigate components beyond one standard deviation of the design's mean `D` — the book's example plot uses `D = 0.1` as its control limit | `architecture.md` |
| **Zone of Pain / Uselessness** | Stable-and-concrete; abstract-with-no-dependents | `architecture.md` |
| **Entity** | Critical business rules and data that would exist without any software | `architecture.md` |
| **Use case** | Application-specific rules orchestrating entities; depends on entities, never the reverse | `architecture.md` |
| **Humble Object** | Split hard-to-test from easy-to-test; the humble half holds no decisions | `architecture.md` |
| **Screaming architecture** | The top-level structure names the domain, not the framework | `architecture.md` |
| **Main as the ultimate detail** | All wiring and configuration in the dirtiest, lowest-level component | `architecture.md` |
| **Asymmetric marriage** | You commit to a framework; it commits nothing to you — use it, don't marry it | `architecture.md` |
| **Partial boundary** | Skip-the-last-step, one-dimensional, or facade — each with its own failure mode | `architecture.md` |
| **Decoupling modes** | Source, deployment, service — stay in one address space as long as possible, reversibly | `architecture.md` |
| **The decoupling fallacy** | A process boundary does not decouple what shares a data record | `architecture.md` |
| **True vs accidental duplication** | True: must always change together. Accidental: changes at different rates, different reasons | `architecture.md` |
| **Organization vs encapsulation** | If every type is public, packages are just folders — no architecture enforced | `architecture.md` |
| **Cross-cutting concern** | A policy spanning modules — isolate it rather than scattering it | `architecture.md` |

## Smell IDs

Cite these directly in findings. Full catalogue and the cross-reference table: `chapter-map.md`;
usual response for each: `smell-triage.md`.

| Group | Range | Covers |
| --- | --- | --- |
| **A** | A1-A10 | Agent smells: failure patterns of AI-written code, not from the book. Signal and response in `review-checklist.md` |
| **C** | C1-C5 | Comments |
| **E** | E1-E2 | Environment: multi-step build or test |
| **F** | F1-F4 | Functions: arguments, output args, flags, dead functions |
| **G** | G1-G36 | General — the largest group |
| **J** | J2-J3 | Language-specific that generalize (J1 intentionally omitted) |
| **N** | N1-N7 | Naming |
| **T** | T1-T9 | Tests |
