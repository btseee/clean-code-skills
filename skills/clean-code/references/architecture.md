# Architecture

Clean code is the lines inside a unit; architecture is the lines *between* — where they run, which
way dependencies cross. Read this for placement, a new dependency, a boundary, or a
framework/database decision.

## Contents

- Why the rule is even possible: the three paradigms
- State and mutability as an architectural choice
- Level, policy, and detail
- The circles
- SOLID, as dependency rules
- Component principles
- Keeping details out
- Systems: construction, growth, and cross-cutting policy
- Testability is an architectural property
- Packaging: four strategies and their weaknesses
- Decoupling modes
- Duplication: resist the reflex
- Architecture serves the developer

**The Dependency Rule: source code dependencies must point only inward, toward higher-level
policies.** Nothing in an inner circle may know anything about an outer circle: no *name*
declared in an outer circle may appear in inner-circle code — no class,
function, variable, annotation, or data format.

**The question to ask before every dependency: which direction does this line cross, and why?**

## Why the rule is even possible: the three paradigms

Each paradigm *removes* a capability; the removal is the discipline:

- **Structured programming restricts direct transfer of control** — sequence, selection, and
  iteration build anything, kept small enough to falsify: **tests show the presence of bugs,
  never their absence.**
- **Object orientation disciplines indirect transfer of control** — polymorphism gives **control
  over the direction of every source-code dependency**, the mechanism behind the Dependency Rule:
  without it the rule is aspiration, with it a choice.
- **Functional programming disciplines assignment** — see State and mutability, below.

**The plugin argument:** a plugin depends on its host and cannot break it; the host drops the
plugin at will — a deliberately **asymmetric** relationship. Point arrows so business rules host
the UI, database, and framework as plugins, so detail changes cannot propagate into policy.

## State and mutability as an architectural choice

Every race condition, deadlock, and concurrent-update defect traces to a mutable variable.
Mutability is a placement decision, not an implementation detail:

- **Segregate mutability** — split the system into mutating and non-mutating components, shifting
  as much work as it can bear onto the immutable side; keep what must mutate small, named, and
  protected (transactions, actors, transactional memory).
- **Event sourcing** goes further: store transactions, not state, recompute by replaying them.
  Applications become create-and-read only; concurrent-update problems disappear because nothing
  updates.

Operational detail — locking discipline, execution models, testing — is in `concurrency.md`.
*Where mutation lives* is a boundary decision, made long before any lock.

## Level, policy, and detail

**Level is distance from input and output** — not call order: a function calling `readChar` and
`writeChar` is *higher* level than they are, even though it is the caller.

- **Policy** is the business rules: the reason the software exists.
- **Detail** is everything that helps policy talk to the world: database, web, UI, framework,
  delivery mechanism, device, protocol.

Group same-reason, same-rate policies into one level; different reasons or rates mean different
levels and components.

Design so **low-level components depend on high-level ones**, never the reverse. The component
dependency graph — compile-time dependencies (`import`, `using`, `require`) — must be acyclic.

### The two kinds of business rule

- **Critical Business Rules** and **Critical Business Data** would exist even on paper, with no
  software. Bind them into an **Entity**: a module holding critical rules and data, needing no
  object-oriented language, just that they share one module.
- A **use case** describes how an automated system is used (input, output, processing steps),
  holding *application-specific* rules and orchestrating Entities.

**Use cases depend on Entities, never the reverse** — use cases sit closer to I/O, so are lower
level. Practical test: still true on paper → an Entity; true only because automated → a use case.
A use case must never reveal whether the delivery mechanism is web, console, desktop, or service.

## The circles

Outermost to innermost. The count is schematic — add circles freely — but the Dependency Rule
always applies.

1. **Frameworks and drivers** — the database, the web framework, the device, the tools, plus glue
   code (both details — see Keeping details out).
2. **Interface adapters** — convert between what use cases need and what an external agency needs:
   controllers, presenters, views, gateways, mappers. **All SQL is confined to this layer**;
   nothing further in knows a database exists.
3. **Use cases** — application-specific rules, orchestrating the flow to and from Entities.
4. **Entities** — enterprise-wide critical business rules. No single application's change should
   force a change here.

Outer circles are mechanisms, inner circles policies — the shared core of Hexagonal, DCI, and BCE;
names differ, the rule doesn't.

### Crossing a boundary

A boundary crossing at run time is a function on one side calling a function on the other and
passing data — the design work is entirely in the *source* dependencies.

Control flow and source dependency point the same way inbound, opposite ways outbound. A
controller calls a use case, which must deliver a result outward to a presenter it may not name.
Resolve with dynamic polymorphism: the use case calls an interface it owns (an **output port**)
that the outer-circle presenter implements — the dependency now opposes the flow of control,
Dependency Inversion.

**What may cross:** simple, isolated structures — a struct, a plain DTO, function arguments, a
basic map — shaped for the *inner* circle's convenience.

**What may never cross inward:** an Entity object, a database row, an ORM row type, a result set,
a framework request or response object. When fields overlap, define a separate structure per
crossing and copy the fields anyway; sharing the type is an SRP violation, returning later as
tramp data and special-case conditionals.

### The cost of each boundary

Chattiness must match the boundary's cost — a conversation shaped for one kind becomes a
performance failure as another.

| Boundary | Mechanism | Crossing cost | Chattiness |
| --- | --- | --- | --- |
| Same address space (monolith) | function call | very cheap | can be very chatty |
| Deployment component (jar, DLL, shared library, gem) | function call plus one load-time cost | very cheap | can still be chatty |
| Local process | OS calls, marshaling, context switches | moderately expensive | limit it carefully |
| Service | network | very slow: tens of milliseconds to seconds | avoid chatting |

Threads are not boundaries or deployment units — scheduling only.

### Full, partial, and no boundary

A full boundary costs reciprocal interfaces, input/output structures, and dependency management,
buying independent compilability and deployability. For "not yet, but I might," use a partial
boundary and know its weakness:

- **Skip the last step** — build the separated components but deploy as one: cheapest to reverse,
  though separation quietly erodes as dependencies creep back.
- **One-dimensional boundary** (a Strategy interface, no reciprocal interface) — discipline alone
  stops a backchannel.
- **Facade** — sacrifices dependency inversion entirely: the client gains a transitive dependency
  on everything behind it, recompiling whenever any of it changes.

Prefer Strategy over Facade when the client must not recompile; either way, add compile-time or
automated enforcement — a partial boundary does not maintain itself.

Build a boundary once it is cheaper than living without it. Declare each boundary interface in the
component that *uses* it: the API belongs to its user, not its implementer.

## SOLID, as dependency rules

Not style advice — each prevents a specific structural failure.

**SRP — Single Responsibility Principle.** *A module should be responsible to one, and only one,
**actor*** — the people who can demand a change. Not "one thing per module" (a function-level
rule, not the SRP). Never co-locate code for different actors or deduplicate across an actor
boundary. Repeated merge conflicts in one file signal an SRP violation, not a process problem.

**OCP — Open-Closed Principle.** *Open for extension, closed for modification* — add code, don't
edit it. **If A must be protected from changes in B, then B depends on A.** Never let
business rules reference a presenter, view, database, or UI type; invert with an interface the
policy side owns, crossing each boundary in one direction with a narrow interface — a wide one
leaks internals as transitive dependencies.

**LSP — Liskov Substitution Principle.** A subtype must be usable anywhere the base type is,
without changing caller behavior. Violation: a call site that must know which implementation it
holds (a type check or vendor-name special case), in any substitutable boundary — REST contracts,
plugins, duck typing, services behind one interface. The workaround conditional multiplies into
extra mechanisms, often a security hole.

**ISP — Interface Segregation Principle.** Avoid depending on things you do not use — depending on
a module containing more than you need is harmful by itself, not merely a symptom of large
interfaces. Check what a new dependency depends on: transitive baggage sets the recompile and
failure blast radius. Applies in dynamically typed languages too, which only hide the coupling,
not remove it.

**DIP — Dependency Inversion Principle.** The most flexible systems have source dependencies
referring only to abstractions, never concretions. The test is **volatility, not abstractness**: a
stable standard-library type is fine; a volatile concrete class of your own is not. Do not derive
from or override one — inheritance is the strongest, most rigid source relationship. Creating an
object is itself a concrete dependency, so policy code must not `new` a
volatile class; use an abstract factory. Violations cannot be removed entirely; gather them into
few concrete components, usually `main`.

## Component principles

A component is a unit of deployment — the smallest independently deployable thing. Keep that
independence even in a single executable, or a partitioned system becomes an unsplittable
monolith.

### Cohesion: which classes belong together

- **REP — Reuse/Release Equivalence Principle.** *The granule of reuse is the granule of release.*
  Anything reused elsewhere must be tracked and released as a unit.
- **CCP — Common Closure Principle.** *Gather into components those classes that change for the
  same reasons and at the same times; separate those that change at different times and for
  different reasons.* The SRP restated for components.
- **CRP — Common Reuse Principle.** *Don't force users of a component to depend on things they
  don't need.* ISP restated for components.

These pull against each other: REP and CCP enlarge components, CRP shrinks them. Too much REP/CRP:
a simple change touches too many components. Too much CCP/REP: releases multiply needlessly. Too
much CCP/CRP: REP is abandoned, components become impractical to reuse. Favor CCP early
(develop-ability over reuse), shift toward REP once real external consumers exist.

### Coupling: which components may depend on which

- **ADP — Acyclic Dependencies Principle.** *Allow no cycles in the component dependency graph.* A
  cycle fuses components into one release unit and can leave no valid build order. Break it with
  DIP, or by extracting a component both depend on.
- **SDP — Stable Dependencies Principle.** *Depend in the direction of stability.* Stability here
  is not frequency of change but the work required to change something — a heavily depended-on
  component is hard to move.
- **SAP — Stable Abstractions Principle.** *A component should be as abstract as it is stable.* A
  stable component must be abstract enough to extend without modifying it — OCP again.

SDP and SAP together are the DIP for components: depend toward stability, stability implies
abstraction. DIP is binary per class; these two allow degrees.

### The metrics

Useful for evidence, not opinion, about a component graph.

- **Fan-in** = classes outside the component that depend on classes inside it.
- **Fan-out** = classes inside the component that depend on classes outside it.
- **Instability `I = Fan-out / (Fan-in + Fan-out)`**, ranging 0 to 1. `I = 0` is maximally stable
  (depended upon, depending on nothing): responsible, independent. `I = 1` is maximally unstable:
  irresponsible, dependent.
- **SDP in metric form:** `I` should *decrease* in the direction of dependency — check
  `I(A) > I(B)` before adding a dependency from A to B.
- **Abstractness `A = Na / Nc`** — `Nc` is the component's class count, `Na` its abstract classes
  and interfaces. `A = 0` is nothing abstract; `A = 1` is nothing but abstractions.
- **The Main Sequence** runs from `(I=1, A=0)` to `(I=0, A=1)` — stable and abstract, or unstable
  and concrete: the two desirable positions.
- **Distance `D = |A + I - 1|`**, ranging 0 to 1. `D = 0` sits exactly on the Main Sequence.
  Compute the mean and variance of `D` across your components; investigate anything beyond one
  standard deviation from the mean. The book's example plot sets `D = 0.1` as its control limit,
  illustration only, not a universal threshold.

**Zone of Pain**, near `(I=0, A=0)`: stable, concrete, rigid — a database schema is the archetype,
highly depended upon and volatile despite being concrete (volatility is a separate axis from `I`
and `A`). **Zone of Uselessness**, near `(I=1, A=1)`: abstractions nobody implements or depends
on.

Component structure evolves with the system rather than being designed top-down; draw unstable
components at a diagram's top so every upward arrow is a visible violation.

## Keeping details out

**Screaming architecture.** The top-level structure should announce the domain, not the
framework — "Rails" or "ASP.NET" instead of "billing" or "patient records" means the framework
became the architecture. Name top-level packages after the domain and its use cases.

**Frameworks are details.** Using one is asymmetric: you commit enormously, the author commits
nothing. Never derive an Entity or use case from a framework base class — derive a proxy in an
outer circle instead — and keep framework annotations off business objects; confine dependency
injection to `main` (see Systems, below). Some marriages — the standard library, the base
platform — are unavoidable, but still a decision made once, on record, not a default.

**Hardware and the OS are details too.** Put a hardware-abstraction layer between code and a
device or OS facility, named for what the *application* needs (`indicate_low_battery`), never
what the device offers (`led_on(5)`) — keeps business rules testable off-target.

**The database is a detail.** The *data model* is architecturally significant; the database
system is not. Never let rows, tables, result sets, or ORM row types travel beyond the
data-access layer — confine SQL and tabular structure to the outermost utilities, handling
storage performance there, not by reshaping business rules.

**The web is a detail.** The web is one more GUI, and a GUI is an I/O device. Moment-to-moment UI
interaction resists abstraction, but the *use case* boundary does not: gather complete input,
process it, return output data, all in plain structures. Keep HTTP, session, and widget concepts
out of business rules.

**`main` is the ultimate detail** — the policy at the lowest level, the dirtiest component, the
only one nothing else depends on. All wiring, configuration, and framework binding belong there.
Treat `main` as a plugin: prefer a separate `main` per environment, jurisdiction, or customer over
configuration branches inside policy code.

## Systems: construction, growth, and cross-cutting policy

**Separate constructing the system from using it.** Startup builds the object graph, reads
configuration, chooses implementations; code doing real work receives what it needs and never
builds it, or it takes on a second job and becomes untestable alone.

- A factory, when an object is created *during* execution: the calling policy names the factory
  interface, the concrete factory lives outward.
- Dependency injection moves construction to `main`; inject there, pass dependencies on as
  ordinary arguments, not framework annotations.
- **Lazy initialization is a construction decision leaking into use** — it hardcodes a concrete
  type at the point of use, making null-checks part of the business logic.

**Systems grow; they are not built whole.** A clean system starts simple and grows because its
concerns stayed separated: new use cases arrive as new components, not edits across old ones.
Decide at the **last responsible moment**.

**Isolate cross-cutting concerns.** Persistence, transactions, security, logging, caching, and
metrics cut across clean separation, duplicating into every handler if naive. Concentrate each at
one boundary — middleware, decorator, proxy, interceptor, aspect: **one home per policy, applied
at the edge, invisible to the business rules it protects.**

**Test-drive the architecture.** A use case's tests need no database, web server, or framework
running when the architecture is truly decoupled — the suite is the proof, not the diagram.

**Adopt a standard only when it demonstrably buys interoperability or reuse**, never for its own
sake. A recurring domain concept earns a small domain-specific language or helper vocabulary stating
intent directly — the same instinct as `tests.md`'s testing language.

## Testability is an architectural property

**The Humble Object pattern.** When behavior is hard to test, split it into two modules rather
than build a harness around it: a *humble* module holding the hard-to-test behavior stripped to
its essence, no decisions in it, and another holding everything testable stripped out. Boundaries
often fall where hard-to-test meets easy-to-test; separating the two finds the boundary.

- A **view** is the humble object: it moves data onto the screen, no decisions. The **presenter**
  does all the work — formatting dates and currency, greyed-out or highlighted state, labels.
- A **database gateway** is an interface with one intention-named method per operation; the
  implementation is the humble object.
- An **ORM belongs in the database layer**, another humble-object boundary: objects expose
  behavior and hide data, data structures expose data and imply none.

**Tests are a system component**, part of the architecture like any other — the outermost circle:
maximally detailed, depending inward, depended on by nothing.

- GUIs are volatile; a suite driving business rules through one is fragile by construction.
- **Structural coupling** — a test class per production class, a test method per production
  method — the most insidious test coupling: fragile tests, rigid production code, neither free to
  grow independently.
- Provide a **testing API** hiding application structure from tests, able to bypass security or
  expensive resources to force testable states; keep its dangerous implementation in a separately
  deployable component.

## Packaging: four strategies and their weaknesses

Grouping code decides whether the compiler enforces the architecture, or only discipline does.

| Strategy | Structure | Specific weakness |
| --- | --- | --- |
| **Package by layer** | horizontal: web / business logic / persistence | Stops scaling past three buckets, says nothing about the domain; a controller can wire straight to a repository while looking clean |
| **Package by feature** | vertical slice per feature or aggregate | Announces the domain, but one entry point per feature may restrict more or less than wanted |
| **Ports and adapters** | domain "inside", infrastructure "outside", outside depends on inside | One shared infrastructure tree lets a controller reach a repository directly, bypassing the domain |
| **Package by component** | business logic *and* persistence behind one interface per component; UI separate | Needs real discipline about what's public, plus one module per component in some ecosystems |

**Organization versus encapsulation is the decisive point.** If every type is public, packages are
just folders and all four strategies are *syntactically identical* however different on a
diagram — nothing stops code from instantiating an implementation class directly.

Never mark a type public by default: use package-private, `internal`, or the equivalent, unless
another package needs an inbound dependency. Give each component one public entry point so the
compiler, not a code review, blocks a controller calling a repository directly.

Enforcement, weakest to strongest: code review (fails under deadlines), static analysis (crude,
slow), the compiler (immediate, unarguable) — prefer the compiler.

## Decoupling modes

Three ways to separate components, increasing in cost:

1. **Source level** — dependencies controlled between source modules so a change doesn't force
   recompiling; one address space, function calls: a monolith.
2. **Deployment level** — dependencies controlled between independently deployable units (jars,
   DLLs, shared libraries); many still share an address space.
3. **Service level** — dependencies reduced to data structures over the network, each unit
   independent of the others' source and binaries.

The best mode is hard to know early and changes as the system matures: **decouple far enough that
a component could become a service, then stay in one address space as long as you can** —
reversibly. Never write code that assumes the current mode.

Service boundaries alone are not architectural — services separated only by behavior are expensive
function calls, still coupled through shared data: one changed field forces every touching service
to agree again. **Architectural boundaries run *through* services, dividing them into
components**, not between them: "all of them" changed by one cross-cutting feature means the
boundary is functional, not architectural.

Micro-services aren't automatically finer-grained decoupling either, and cost development time —
unlike memory and cycles, not cheap.

## Duplication: resist the reflex

Eliminating duplication is right only when it is real.

- **True duplication**: every change to one instance requires the same change to every copy.
- **False (accidental) duplication**: the copies change at different rates, for different reasons.

Two shapes identical today and diverging tomorrow are not duplicates — a database record shaped
like a screen view is almost certainly accidental; build the separate view model. Unifying
accidental duplication is harder to undo than leaving it, and a common way an agent damages a
codebase while believing it is cleaning it.

## Architecture serves the developer

The goal of architecture is to **minimize the human effort required to build and maintain the
system** — leave options open as long as possible. A good architect maximizes the number of
decisions *not* made.

A good architecture supports four things: **use cases and operation**, **maintenance**,
**development**, and **deployment**. Operation is the one agents forget — throughput and scale
shape the component structure too. Development is where **Conway's law** bites: a system's
structure mirrors its organization's — the SRP again, so give each team components it can own
separately.

**The two values.** Software has behavior (urgent, visible) and structure (important, invisible).
Working-but-unchangeable is worth less than broken-but-easy-to-change — one can be shaped into
anything, the other dies at its first new requirement. Features never outrank structure on the
urgent/important grid, yet win every undefended argument — asserting structure's importance is
part of the job. A structural defect shows as a mismatch between *scope* and *shape*: a small
requirement forcing a large diff is an architecture defect — name it.

- Never justify a shortcut with "clean it up later"; the pressure that created it never abates.
- Never propose a rewrite as the remedy for a mess — the team that made the mess rebuilds it.
- Treat rising cost per comparable change as the primary signal of decay.
- Never treat "it satisfies the requirements" as done.

## Related files

- `architecture-map.md` — per-chapter map from architectural topics to the decisions they govern.
- `principles.md` — the code-level principles: naming, functions, errors, tests, concurrency.
- `chapter-map.md` — code-level chapter map and the full code-smell catalogue with IDs.
- `new-project.md` — designing a structure from scratch.
- `project-refactor.md` — changing an existing structure safely.
