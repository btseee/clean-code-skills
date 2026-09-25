# Architecture

Clean code is the lines inside a unit; architecture is the lines *between* — where they run and
which way dependencies cross. Read this for placement across layers, a new dependency, a
boundary, or a framework or database decision.

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

The whole subject reduces to one rule and one question.

**The Dependency Rule: source code dependencies must point only inward, toward higher-level
policies.** Nothing in an inner circle may know anything about an outer circle: no *name*
declared in an outer circle may appear in inner-circle code — no class,
function, variable, annotation, or data format.

**The question to ask before every dependency: which direction does this line cross, and why?**

## Why the rule is even possible: the three paradigms

Each paradigm *removes* a capability; the removal is the discipline:

- **Structured programming restricts direct transfer of control** — sequence, selection, and
  iteration build anything, and keep units small enough to falsify with a test: **tests show the
  presence of bugs, never their absence.**
- **Object orientation disciplines indirect transfer of control.** Its payoff is not encapsulation
  or inheritance but that polymorphism gives **control over the direction of every source-code
  dependency** — the mechanism behind the Dependency Rule: without it the rule is an aspiration,
  with it a choice.
- **Functional programming disciplines assignment** — see State and mutability, below.

**The plugin argument:** a plugin depends on its host and cannot break it, while the host drops the
plugin at will — a deliberately **asymmetric** relationship. Point the arrows so business rules are
the host and the UI, database, and framework are plugins, so detail changes cannot propagate into
policy.

## State and mutability as an architectural choice

Every race condition, deadlock, and concurrent-update defect traces to a mutable variable — no
deadlocks without mutable locks. Mutability is a placement decision, not an implementation detail:

- **Segregate mutability** — split the system into mutating and non-mutating components, moving as
  much processing as you can into the immutable ones; keep what must mutate small, named, and
  protected (transactions, actors, transactional memory).
- **Event sourcing** goes further: store transactions, not state, and recompute by replaying them.
  Applications become create-and-read only, and concurrent-update problems disappear because
  nothing updates — version control works this way.

The operational detail — locking discipline, execution models, how to test any of it — is in
`concurrency.md`. *Where mutation lives* is a boundary-drawing decision, made long before any lock.

## Level, policy, and detail

**Level is distance from input and output** — not call order: a function calling `readChar` and
`writeChar` is *higher* level than they are, even though it is the caller. The further a policy
sits from I/O, the higher its level.

- **Policy** is the business rules: the reason the software exists.
- **Detail** is everything that helps policy talk to the world: database, web, UI, framework,
  delivery mechanism, device, protocol.

Group same-reason, same-rate policies into one level; different reasons or rates mean different
levels and components.

Design so **low-level components depend on high-level ones**, never the reverse. The component
dependency graph — compile-time dependencies (`import`, `using`, `require`) — must be acyclic.

### The two kinds of business rule

- **Critical Business Rules** and **Critical Business Data** would exist even on paper, with no
  software. Bind them into an **Entity**: a module holding critical rules operating on critical
  data — pure business, needing no object-oriented language, only that data and rules share one
  module.
- A **use case** describes how an automated system is used (input, output, processing steps),
  holding *application-specific* rules and orchestrating Entities.

The dependency follows: **use cases depend on Entities, never the reverse** — use cases sit closer
to I/O, so they are lower level.

Practical test: still true on paper → an Entity; true only because the work was automated → a use
case. A use case must never reveal whether the delivery mechanism is a web app, console, desktop
client, or service.

## The circles

Outermost to innermost. The count is schematic — add circles freely — but the Dependency Rule
always applies.

1. **Frameworks and drivers** — the database, the web framework, the device, the tools, plus glue
   code. The web is a detail. The database is a detail.
2. **Interface adapters** — convert between what use cases need and what an external agency needs:
   controllers, presenters, views, gateways, mappers. **All SQL is confined to this layer**;
   nothing further in knows a database exists.
3. **Use cases** — application-specific rules, orchestrating the flow to and from Entities.
4. **Entities** — enterprise-wide critical business rules. No single application's change should
   force a change here.

Outer circles are mechanisms, inner circles policies — the common core of Hexagonal / Ports and
Adapters, DCI, and BCE alike; the names differ, the rule does not.

### Crossing a boundary

A boundary crossing at run time is just a function on one side calling a function on the other and
passing data — the design work is entirely in the *source* dependencies.

Control flow and source dependency point the same way inbound, opposite ways outbound. A
controller calls into a use case, which must deliver a result outward to a presenter it may not
name. Resolve with dynamic polymorphism: the use case calls an interface it owns (an **output
port**), and the presenter in the outer circle implements it — the dependency now opposes the flow
of control, Dependency Inversion.

**What may cross:** simple, isolated structures — a struct, a plain DTO, function arguments, a
basic map — shaped for the *inner* circle's convenience.

**What may never cross inward:** an Entity object, a database row, an ORM row type, a result set, a
framework request or response object. When fields overlap, define a separate structure per crossing
and copy the fields anyway; sharing the type is a Single Responsibility violation returning later
as tramp data and special-case conditionals.

### The cost of each boundary

Chattiness must match the boundary's cost — a conversation shaped for one boundary becomes a
performance failure when that boundary becomes another kind.

| Boundary | Mechanism | Crossing cost | Chattiness |
| --- | --- | --- | --- |
| Same address space (monolith) | function call | very cheap | can be very chatty |
| Deployment component (jar, DLL, shared library, gem) | function call plus one load-time cost | very cheap | can still be chatty |
| Local process | OS calls, marshaling, context switches | moderately expensive | limit it carefully |
| Service | network | very slow: tens of milliseconds to seconds | avoid chatting |

Threads are not boundaries, not deployment units — they are scheduling.

### Full, partial, and no boundary

A full boundary costs reciprocal interfaces, input/output structures, and the dependency
management to keep them apart, buying independent compilability and deployability. When the case
is "not yet, but I might," use a partial boundary and know its weakness:

- **Skip the last step** — build the separated components but deploy as one. Cheapest to reverse;
  separation quietly erodes as dependencies creep back across.
- **One-dimensional boundary** (a Strategy interface, no reciprocal interface) — nothing but
  discipline stops a backchannel.
- **Facade** — sacrifices dependency inversion entirely: the client gains a transitive dependency
  on everything behind it and recompiles when any of it changes.

Prefer Strategy over Facade when the client must not recompile, and either way add compile-time or
automated enforcement — a partial boundary does not maintain itself.

Build a boundary once it is cheaper than living without it. Declare each boundary interface in the
component that *uses* it: the API belongs to its user, not its implementer.

## SOLID, as dependency rules

Not style advice — each prevents a specific structural failure.

**SRP — Single Responsibility Principle.** *A module should be responsible to one, and only one,
actor* — the people who can demand a change. Not "one thing per module" (a real function-level
rule, but not the SRP). Ask which actor can demand a change before placing a function; never
co-locate code for different actors or deduplicate across an actor boundary. Repeated merge
conflicts in one file signal an SRP violation, not a process problem.

**OCP — Open-Closed Principle.** *A software artifact should be open for extension but closed for
modification* — extend by adding code, not editing it. **If A must be protected from changes in B,
then B depends on A.** Never let business rules reference a presenter, view, database, or UI type;
invert with an interface the policy side owns. Cross each boundary in one direction, with a narrow
interface — a wide one leaks internals as transitive dependencies.

**LSP — Liskov Substitution Principle.** A subtype must be usable anywhere the base type is,
without changing caller behavior. Proof of violation: a call site that must know which
implementation it holds (a type check or vendor-name special case), in any substitutable
boundary — REST contracts, plugin interfaces, duck-typed objects, services behind one interface.
The workaround conditional multiplies into extra mechanisms, often a security hole.

**ISP — Interface Segregation Principle.** Avoid depending on things you do not use — "keep
interfaces small" is a symptom; depending on a module containing more than you need is harmful by
itself. Define the narrow interface the caller needs, and check what a new dependency itself
depends on: transitive baggage sets both the recompile and failure blast radius. Static typing
shows it at compile time; dynamic typing only hides the coupling — ISP applies in Python and
JavaScript as much as in Java.

**DIP — Dependency Inversion Principle.** The most flexible systems have source dependencies
referring only to abstractions, never concretions. The test is **volatility, not abstractness**:
the standard library's string type is fine, being stable; a volatile concrete class of your own is
not. Do not refer to, derive from, or override one — inheritance is the strongest, most rigid
source relationship, and overriding still inherits its dependencies. Creating an object is itself a
concrete dependency, so policy code must not `new` a volatile class; use an abstract factory.
Violations cannot be removed entirely; gather them into a small number of concrete components,
usually `main`.

## Component principles

A component is a unit of deployment — the smallest thing you can deploy independently. Keep that
independence even inside a single executable, or a partitioned system turns into a monolith that
cannot be split.

### Cohesion: which classes belong together

- **REP — Reuse/Release Equivalence Principle.** *The granule of reuse is the granule of release.*
  Anything you expect others to reuse must be tracked and released as a unit.
- **CCP — Common Closure Principle.** *Gather into components those classes that change for the
  same reasons and at the same times; separate those that change at different times and for
  different reasons.* The SRP restated for components.
- **CRP — Common Reuse Principle.** *Don't force users of a component to depend on things they
  don't need.* ISP restated for components.

These three pull against each other: REP and CCP enlarge components, CRP shrinks them. Over-weight
REP and CRP, and one simple change touches too many components; over-weight CCP and REP, and
releases multiply needlessly; over-weight CCP and CRP, and REP is abandoned — components become
impractical to reuse. Favor CCP early (develop-ability over reuse), and shift toward REP once real
external consumers exist.

### Coupling: which components may depend on which

- **ADP — Acyclic Dependencies Principle.** *Allow no cycles in the component dependency graph.* A
  cycle fuses components into one release unit, makes build problems grow geometrically, and can
  leave no valid build order at all. Break it with DIP, or by extracting a component both existing
  ones depend on.
- **SDP — Stable Dependencies Principle.** *Depend in the direction of stability.* Stability here
  is not frequency of change but the work required to change something — a component many others
  depend on is hard to move.
- **SAP — Stable Abstractions Principle.** *A component should be as abstract as it is stable.* A
  stable component must be abstract enough to extend without modifying it — OCP again.

SDP and SAP together are the DIP for components: depend toward stability, stability implies
abstraction, so dependencies run toward abstraction. DIP is binary per class; these two allow
degrees.

### The metrics

Useful when you need evidence rather than opinion about a component graph.

- **Fan-in** = classes outside the component that depend on classes inside it.
- **Fan-out** = classes inside the component that depend on classes outside it.
- **Instability `I = Fan-out / (Fan-in + Fan-out)`**, ranging 0 to 1. `I = 0` is maximally stable
  (depended upon, depending on nothing): responsible and independent. `I = 1` is maximally
  unstable: irresponsible and dependent.
- **SDP in metric form:** `I` should *decrease* in the direction of dependency — before adding a
  dependency from A to B, check `I(A) > I(B)`. A stable component depending on a deliberately
  flexible one destroys the flexible one's changeability without editing a line of it.
- **Abstractness `A = Na / Nc`**, where `Nc` is the component's class count and `Na` its abstract
  classes and interfaces. `A = 0` is nothing abstract; `A = 1` is nothing but abstractions.
- **The Main Sequence** runs from `(I=1, A=0)` to `(I=0, A=1)` — stable and abstract, or unstable
  and concrete: the two most desirable positions.
- **Distance `D = |A + I - 1|`**, ranging 0 to 1. `D = 0` sits exactly on the Main Sequence.
  Compute the mean and variance of `D` across your own components — a conforming design keeps both
  near zero — and investigate anything beyond one standard deviation from that mean. The book's
  example plot sets its control limit at `D = 0.1` as illustration, not a universal threshold: a
  metric measures against an arbitrary standard, not a verdict.

**Zone of Pain** is near `(I=0, A=0)`: stable, concrete, and rigid — a database schema is the
archetype: highly depended upon, extremely concrete, and volatile (volatility is a third axis, why
a stable concrete thing like a standard string type is harmless there). **Zone of Uselessness** is
near `(I=1, A=1)`: abstractions nobody implements or depends on.

Component structure cannot be designed top-down before code exists — it maps buildability and
maintainability, not function, and evolves with the system. Draw unstable components at a
diagram's top so every upward arrow is a visible violation.

## Keeping details out

**Screaming architecture.** The top-level structure should announce the domain, not the
framework — "Rails" or "ASP.NET" instead of "billing" or "patient records" means the framework
became the architecture. Name top-level packages after the domain and its use cases.

**Frameworks are details.** Using one is asymmetric: you commit enormously, the author commits
nothing. Use it without coupling to it — never derive an Entity or use case from a framework base
class (derive a proxy in an outer circle instead), and keep framework annotations off business
objects. Confine dependency-injection usage to `main`; inject there, pass dependencies onward
normally. Ask both how to use a framework and how to protect yourself from it before adopting one.
Some marriages — the standard library, the base platform — are unavoidable, but even those are a
decision made once, on record, not a default.

**Hardware and the operating system are details too.** Put a hardware-abstraction layer between
code and a device or OS facility, named for what the *application* needs
(`indicate_low_battery`), never what the device offers (`led_on(5)`) — the same inversion as every
boundary, making business rules testable off-target.

**The database is a detail.** The *data model* is architecturally significant; the database system
is not. Never let rows, tables, result sets, or ORM row types travel beyond the data-access layer,
or circulate as objects — confine SQL and tabular structure to the outermost utilities, and handle
storage performance inside the access mechanism, not by reshaping business rules.

**The web is a detail.** The web is one more GUI, and a GUI is an I/O device. Moment-to-moment UI
interaction is genuinely hard to abstract, but the *use case* boundary is not: gather complete
input, process it, return output data, all in plain structures. Keep HTTP, session, and widget
concepts out of business rules.

**`main` is the ultimate detail** — the policy at the lowest level, the dirtiest component, the
only one nothing else depends on. All wiring, configuration loading, and framework binding belong
there. Treat `main` as a plugin: prefer a separate `main` per environment, jurisdiction, or
customer over configuration branches inside policy code.

## Systems: construction, growth, and cross-cutting policy

**Separate constructing the system from using it.** Startup builds the object graph, reads
configuration, chooses implementations; code doing real work receives what it needs and never
builds it, or it takes on a second job and becomes untestable alone.

- A factory, when an object is created *during* execution: the calling policy names the factory
  interface, the concrete factory lives outward.
- Dependency injection moves construction to `main`; inject there, then pass dependencies on as
  ordinary arguments, not scattered framework annotations.
- **Lazy initialization is a construction decision leaking into use** — it hardcodes a concrete
  type at the point of use, making the null-check path part of the business logic.

**Systems grow; they are not built whole.** You cannot pour a software foundation once. A clean
system starts simple and grows because its concerns stayed separated: new use cases arrive as new
components, not edits across old ones. Decide at the **last responsible moment**.

**Isolate cross-cutting concerns.** Persistence, transactions, security, logging, caching, and
metrics cut across clean separation and duplicate into every handler if naive. Concentrate each in
one place, at a boundary — middleware, decorator, proxy, interceptor, aspect, whatever the
ecosystem provides: **one home per policy, applied at the edge, invisible to the business rules it
protects.**

**Test-drive the architecture.** A use case's tests need no database, web server, or framework
running when the architecture is truly decoupled — the suite is the proof, not the diagram.

**Adopt a standard only when it demonstrably buys interoperability or reuse**, never for its own
sake. A recurring domain concept earns a small domain-specific language or named vocabulary of
helpers, stating intent directly instead of restating mechanism — the same instinct as the testing
language in `tests.md`.

## Testability is an architectural property

**The Humble Object pattern.** When behavior is hard to test, split it into two modules rather than
build a harness around it: one *humble* module holds the hard-to-test behavior stripped to its
barest essence, no decisions in it; the other holds everything testable that was stripped out.

This pattern sits near every architectural boundary: boundaries tend to fall where hard-to-test
meets easy-to-test, and separating the two often *is* how you find the boundary.

- A **view** is the humble object: it moves data onto the screen, no decisions. The **presenter**
  does all the work — formatting dates and currency, greyed-out or highlighted state, labels.
  Anything on screen the application controls appears in the view model as a string, boolean, or
  enum.
- A **database gateway** is an interface with one intention-named method per operation; the
  implementation is the humble object. Never put SQL in a use case.
- An **ORM belongs in the database layer**, another humble-object boundary: objects expose behavior
  and hide data, data structures expose data and imply none — not the same thing.

**Tests are a system component**, part of the architecture like any other — the outermost circle:
maximally detailed, depending inward, depended on by nothing.

- Do not depend on volatile things: GUIs are volatile, so a suite driving business rules through
  one is fragile by construction.
- **Structural coupling** — a test class per production class, a test method per production
  method — is the most insidious form of test coupling: it makes tests fragile and production code
  rigid, and blocks tests from growing more specific as production code grows more general.
- A fragile suite that makes developers refuse a correct change is that rigidity's cost.
- Provide a **testing API** that hides application structure from tests and can bypass security or
  expensive resources to force testable states, kept with its dangerous implementation in a
  separately deployable component.

## Packaging: four strategies and their weaknesses

How you group code decides whether the compiler enforces the architecture, or only discipline
does.

| Strategy | Structure | Specific weakness |
| --- | --- | --- |
| **Package by layer** | horizontal: web / business logic / persistence | Stops scaling past three buckets, says nothing about the domain; a controller can wire straight to a repository while the graph still looks clean |
| **Package by feature** | vertical slice per feature or aggregate | Announces the domain, but one entry point per feature may restrict more or less than you want |
| **Ports and adapters** | domain "inside", infrastructure "outside", outside depends on inside | One shared infrastructure tree lets a controller reach a repository directly, bypassing the domain |
| **Package by component** | business logic *and* persistence behind one interface per component; UI separate | Needs real discipline about what is public, plus one module per component in some ecosystems |

**Organization versus encapsulation is the decisive point.** If every type is public, packages are
just folders, and all four strategies are *syntactically identical* however different on a
diagram — nothing stops code from instantiating an implementation class directly.

Never mark a type public by default: use package-private, `internal`, or the equivalent, unless
another package needs an inbound dependency. Give each component one public entry point, so the
compiler — not a code review — blocks a controller from calling a repository directly.

Enforcement, weakest to strongest: discipline and code review (fails under deadlines), post-compile
static analysis (crude, slow feedback), the compiler (immediate, unarguable). Prefer the compiler.

## Decoupling modes

Three ways to separate components, increasing in cost:

1. **Source level** — dependencies controlled between source modules so a change does not force
   others to recompile; one address space, function calls: a monolith.
2. **Deployment level** — dependencies controlled between independently deployable units (jars,
   DLLs, shared libraries); many still share an address space.
3. **Service level** — dependencies reduced to data structures over the network, so each unit is
   independent of the others' source and binaries.

The best mode is hard to know early and changes as a system matures: **decouple far enough that a
component could become a service, then stay in one address space for as long as you can** —
reversibly. Never write code that assumes the current mode.

Service boundaries are not architectural boundaries by themselves — services separated only by
behavior are expensive function calls, still coupled through shared data: a field added to a
shared record forces every service touching it to change and agree on its meaning.
**Architectural boundaries run *through* services, dividing them into components**, not between
them. Count how many units a cross-cutting feature forces you to change; "all of them" means it is
functional, not architectural.

Micro-services are not automatically finer-grained decoupling either, and cost development time —
unlike memory and cycles, not cheap.

## Duplication: resist the reflex

Eliminating duplication is right only when it is real.

- **True duplication**: every change to one instance requires the same change to every copy.
- **False (accidental) duplication**: the copies change at different rates, for different reasons.

Two shapes identical today and diverging tomorrow are not duplicates — a database record shaped
like a screen view is almost certainly accidental; build the separate view model. Unifying
accidental duplication is harder to undo than leaving it alone, and is a common way an agent
damages a codebase while believing it is cleaning it.

## Architecture serves the developer

The goal of architecture is to **minimize the human effort required to build and maintain the
system** — so the strategy is to leave as many options open as possible, for as long as possible. A
good architect maximizes the number of decisions *not* made.

A good architecture must support four things: **the use cases and operation** of the system, its
**maintenance**, its **development**, and its **deployment**. Operation is the one agents forget —
throughput and scale shape the component structure too. Development is where **Conway's law**
bites: a system's structure mirrors its organization's, and its corollary is the SRP again — give
each team components it can own separately.

**The two values.** Software has behavior (urgent, visible) and structure (important, invisible).
Working-but-unchangeable is worth less than broken-but-easy-to-change — the one can be shaped into
anything, the other dies at its first new requirement. Architecture occupies the top two cells of
the urgent/important grid; features never rise above the third, yet win every undefended argument —
asserting structure's importance is part of the job. A structural defect shows as a mismatch
between *scope* and *shape*: difficulty should track scope, never shape. A small requirement
forcing a large diff is an architecture defect — name it.

- Never justify a shortcut with "we will clean it up later"; the pressure that created it never
  abates.
- Never propose a rewrite as the remedy for a mess — the team that made the mess rebuilds it.
- Treat rising cost per comparable change as the primary signal of decay.
- Never treat "it satisfies the requirements" as done.

## Related files

- `architecture-map.md` — per-chapter map from architectural topics to the decisions they govern.
- `principles.md` — the code-level principles: naming, functions, errors, tests, concurrency.
- `chapter-map.md` — code-level chapter map and the full code-smell catalogue with IDs.
- `new-project.md` — designing a structure from scratch.
- `project-refactor.md` — changing an existing structure safely.
