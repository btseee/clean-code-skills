---
name: clean-react
description: Use when writing, reviewing, or refactoring React components, hooks, or state, alongside the clean-code skill. Adds the React-specific checks the universal skill cannot state - effect misuse, derived-state duplication, unclear state ownership, component responsibility, server/client boundary leakage, and business logic inside presentation components.
license: MIT
compatibility: Works with no tooling. Reads package.json to learn the React version and framework (Next.js, Remix, Vite) when present; never writes.
metadata:
  version: "3.3.0"
  extends: clean-code
---

# Clean React

A stack extension of `clean-code`. The universal skill is authoritative for placement, one job per
unit, the Dependency Rule, tests, honesty, and the agent smells A1-A10; this file adds only what is
specific to React and never relaxes a universal rule. Read `clean-code/SKILL.md` first; if the two
disagree, `clean-code` wins. For type-level checks, `clean-typescript` applies as well.

## Before Writing

- Read the installed `react` version and the framework in `package.json`. Hooks and APIs differ
  across 17, 18, and 19 and across frameworks; an API from the wrong one is A1 Hallucinated API.
- Find where this project keeps state (context, a store, server state via a query library, URL) and
  where it keeps components, hooks, and feature folders (`.clean/conventions.json`, or the two or
  three most similar files). Mirror it (A6).
- Find the existing hook or component for the concept before writing one (A5).

## Checks

Cite these as `R1`-`R6` beside the universal IDs.

| ID | Check | Look for | Preferred response |
| --- | --- | --- | --- |
| R1 | Effect misuse | `useEffect` that sets state from props or other state; an effect that fetches without cancellation or a query library the project already uses; an effect standing in for an event handler; a dependency array edited to silence a lint rule | Compute during render; move event logic into the handler; use the project's data-fetching layer; treat a lint-driven dependency edit as a bug report about the effect's design |
| R2 | Derived-state duplication | a `useState` whose value is always computable from props or other state (`filteredItems`, `total`, `isValid`) and kept in sync by an effect | Derive it in render (`useMemo` only when measured); one source of truth per fact |
| R3 | Unclear state ownership | the same fact in two components or in a store and a component; state lifted "just in case"; a global store for one screen's form | Own state at the lowest common ancestor that needs it; server state in the query layer; global only for facts that are global |
| R4 | Component responsibility | a component that fetches, transforms, decides, and renders; hundreds of lines; a prop list that reads like a config object | Split into a container or hook that decides and a presentation component that renders; pass data and callbacks, not flags (one-sentence test) |
| R5 | Server/client boundary leakage | secrets, database or ORM calls, or Node-only modules reachable from a client component; `"use client"` added to a tree to make a hook work; server components importing browser APIs | Keep data access and secrets on the server side of the boundary; pass serializable props across it; push `"use client"` to the leaf that needs it (A10) |
| R6 | Business logic inside presentation | pricing, permission, validation, or workflow rules computed in JSX or in a component body; the same rule repeated in two components | Move the rule to a plain function or hook the domain owns and test it there; components call it. A business rule verified only by rendering is a GUI-driven test |

## Idioms Worth Enforcing

- Components are functions of props; hooks encapsulate one concern and start with `use`.
- Keys are stable identities, never array indices for reorderable lists.
- Lists and conditionals stay readable: early returns, small subcomponents, no nested ternaries
  three deep.
- Accessibility is not optional: semantic elements, labels, keyboard paths, focus management.
- Match the project's styling approach and file layout exactly; do not introduce a second one.

## Verification

- The project's `typecheck` and `test` commands (`.clean/commands.json`) are the LOW-level checks.
- A moved or extracted rule (R6) gets a plain unit test; a component gets a behavior test through
  what the user sees or does, not through implementation details.
- R5 changes are HIGH when secrets or data access are involved
  (`clean-code/references/risk-verification.md`): verify the client bundle does not include the
  server module, and say how you verified it.
