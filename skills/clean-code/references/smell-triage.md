# Smell Triage

What to do about a smell you found. The scope gate in `SKILL.md` decides *whether* to act; this
file says *what* the usual action is.

**Scope gate, restated:** fix now only if it blocks the requested change, creates immediate risk,
or your own work introduced it — otherwise report it, untouched. In campaign mode, log it in the
ledger and handle it in its batch.

Cite smell IDs from `chapter-map.md` (G17, N7, T5...) and agent smells A1-A10 from
`review-checklist.md` — findings stay unambiguous and cross-referenceable.

## Code-level smells

| Smell | Look For | Usual Response |
| --- | --- | --- |
| Long function | mixed abstraction levels, many branches | extract named steps if touching the area |
| Mixed responsibility | unit fails the one-sentence test | split by responsibility when your task touches it |
| Misplaced code | logic living in the wrong layer or module | move it to its owner, or report the mismatch |
| Junk-drawer module | growing `utils`/`helpers`/`common` | name the domain concept; relocate what you touch |
| Duplicate knowledge | same rule or constant in multiple places | centralize when behavior changes and the duplication is true |
| Duplicate implementation | parallel versions of the same helper or file | consolidate to one; delete the orphan if unused |
| Primitive obsession | loose strings, numbers, maps standing in for concepts | introduce a type only when it protects a real invariant |
| Boolean flag argument | one function doing two jobs | split functions or name modes clearly |
| Repeated type-switch | same if/else or switch chain in several places | one dispatch point when idiomatic |
| Feature envy | code reaching into another module's internals | move behavior or expose a clearer API |
| Hidden temporal coupling | calls that must happen in a secret order | make state transitions explicit |
| Global mutable state | order-dependent tests, hidden inputs | inject dependencies or isolate state |
| Broad catch | failures disappear | handle, wrap, or propagate with context |
| Magic values | unexplained numbers or strings | name constants expressing domain meaning |
| Buried configuration | tunable values hardcoded deep in call stacks | lift to the top level, pass down |
| Dead code | unreachable branches, unused exports, orphan files | delete what your change orphaned; report the rest |

## Structural and architectural smells

These cost more to fix and more to leave. Report them even out of scope — they shape every later
change.

| Smell | Look For | Usual Response |
| --- | --- | --- |
| Wrong-way dependency | an inner layer naming an outer one; an ORM type/annotation in a business rule | invert it: declare the interface inward, implement it outside |
| Skipped layer | a controller wired straight to a repository or data access | route through the owning layer; check first whether it holds the only authorization |
| Dependency cycle | components that cannot be built or released independently | invert one edge, or extract a component both depend on |
| Detail leak | rows, result sets, or request/response objects travelling inward | define a structure per crossing; copy the fields |
| Framework as architecture | top-level structure named after the stack; business objects derived from framework classes | name packages for the domain; wrap the framework at the edge |
| Shotgun surgery | one concept forces edits across many files | find the missing boundary |
| Unstable dependency | a widely depended-on component depending on a volatile one | extract an abstract component between them |
| Zone of pain | something stable and concrete, widely depended on — pain scales with its volatility | put an abstraction in front of it |
| Structural test coupling | one test class per production class, mirroring methods | test behavior, not structure |
| GUI-driven business tests | business rules verified by driving the UI | test through the use case; keep the UI humble |
| Premature service split | a process or network boundary that separates behavior but shares a data record | draw the boundary inside the service, or collapse it |
| Accidental deduplication | one helper serving two actors, or two change rates | split back apart; owners differ, so the code should too |

## Agent smells

A1-A10 carry signal and response in `review-checklist.md`. In your own diff, an agent smell always
passes the scope gate — your work introduced it; fix before completion. Reviewing someone else's
change, report its ID, ranked below: A1/A8 as wrong behavior, A7 as blocked verification, A10 as a
wrong-way dependency, A5 as duplicated knowledge.

## Priority when several apply

Order work by risk, not by how easy the fix looks:

1. Wrong behavior or a security hole — skipped authorization, a broad catch hiding failures, a
   substitutability violation papered over with a type check.
2. Blocked verification — untestable by design, structural test coupling, missing tests for the
   area you're changing.
3. Wrong-way dependencies and cycles: every later change gets more expensive.
4. Duplicated knowledge that is genuinely true duplication.
5. Readability: naming, function size, comments, magic values.

Formatting is last, and usually belongs to the formatter, not to you.
