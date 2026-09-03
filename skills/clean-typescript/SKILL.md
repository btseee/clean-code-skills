---
name: clean-typescript
description: Use when writing, reviewing, or refactoring TypeScript, alongside the clean-code skill. Adds the TypeScript-specific checks the universal skill cannot state - unsafe any propagation, an oversized public surface, domain types coupled to transport or persistence types, unchecked narrowing, and duplicate DTO or domain models with no clear owner.
license: MIT
compatibility: Works with no tooling. Reads tsconfig.json and package.json when present; never writes.
metadata:
  version: "3.3.0"
  extends: clean-code
---

# Clean TypeScript

A stack extension of `clean-code`. The universal skill is authoritative for everything
cross-language: placement, one job per unit, the Dependency Rule, tests, honesty, and the agent
smells A1-A10. This file adds only what is specific to TypeScript, and it never relaxes a universal
rule. Read `clean-code/SKILL.md` first; if the two disagree, `clean-code` wins.

## Before Writing

- Read `tsconfig.json`: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, path
  aliases, and `moduleResolution` decide what is idiomatic here. Match them; do not loosen them.
- Read the installed `typescript` version and the types of any package you are about to call
  (`node_modules/<pkg>/**/*.d.ts`). A method that exists in your memory but not in those files is
  A1 Hallucinated API.
- Find the existing types for the concept you are touching before declaring a new one (A5).

## Checks

Cite these as `TS1`-`TS5` beside the universal IDs.

| ID | Check | Look for | Preferred response |
| --- | --- | --- | --- |
| TS1 | Unsafe `any` propagation | `any` (explicit, from `JSON.parse`, `as any`, untyped catch, an untyped third-party call) flowing into a typed function; `@ts-ignore` / `@ts-expect-error` without a reason | Narrow at the boundary where the value enters: parse or validate into a declared type once, then stay typed. `unknown` plus a type guard beats `any` |
| TS2 | Oversized public surface | `export` on every declaration; barrel files re-exporting internals; types exported only because a test wanted them | Export what a consumer needs and nothing else. A test that needs an internal is a test of the wrong shape; test through the public interface |
| TS3 | Domain types coupled to transport or persistence | a domain entity that is also the API response shape, the Prisma/TypeORM model, or the form state; `Date` from a serializer inside a business rule; ORM decorators on a domain class | One type per side of the seam, converted explicitly at the seam. The domain type never imports from `api/`, `db/`, or the framework (A10) |
| TS4 | Unchecked narrowing | `as SomeType` on external data; non-null assertions (`!`) to silence the compiler; `in` or `typeof` checks that do not cover the union; a `switch` on a discriminant without an exhaustive `never` default | Assert only what you have checked. Prefer a runtime guard or schema at the boundary and exhaustive switches inside; treat every `!` as a claim that needs a comment saying why it holds |
| TS5 | Duplicate DTO / domain models with no owner | `User`, `UserDto`, `UserResponse`, `UserRecord`, `IUser` scattered across folders with overlapping fields and no rule about which is canonical | Name one owner per side (domain, transport, persistence); delete or derive the rest (`Pick`, `Omit`, `satisfies`). Two types that must always change together are true duplication |

## Idioms Worth Enforcing

- `unknown` at inputs, precise types inside, `never` at the end of exhaustive switches.
- Discriminated unions over boolean flags and optional-field soups.
- `readonly` and `as const` where mutation is not intended; narrow return types over wide ones.
- Errors as values (`Result`-style unions) for expected alternate outcomes; `throw` for genuine
  failures, with the cause preserved (`new Error(msg, { cause })`).
- Import paths follow the project's aliases; relative `../../..` climbs usually mean a file is in
  the wrong place (A6).

## Verification

- `tsc --noEmit` (or the project's `typecheck` command in `.clean/commands.json`) is the LOW-level
  check for any TypeScript change; it is never sufficient on its own for MEDIUM or HIGH
  (`clean-code/references/risk-verification.md`).
- A new type guard or parser gets a test with a malformed input, not only a happy one.
- Report `any`, `as`, and `!` counts you added, if any, in the handoff; each is a claim.
