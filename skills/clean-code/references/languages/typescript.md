# TypeScript

> Applies to: TypeScript 5.x through 7.x. Formatter: Prettier or Biome. Linter: typescript-eslint on ESLint 10, or Biome. Read with: `javascript.md` — every JavaScript rule applies; this pack adds the type system's.

## Names

- Name types for what they are, in PascalCase (`Order`, `PaymentGateway`); no `I` prefix or `Type` suffix unless the project already uses one (N6).
- Name type parameters for their role when there are several (`TItem`, `TKey`); a lone `T` is fine.
- Use one discriminant field name — `kind` or `type` — across the codebase (G11).

## Functions And Types

- Enable `strict`, `noUncheckedIndexedAccess`, and `noImplicitOverride`; never relax a flag to silence an error (G4).
- Never use `any`. Take `unknown` and narrow it; confine an unavoidable `any` to one adapter, reason beside it.
- Model alternatives as discriminated unions and end every `switch` over them with a `never` check (G23).
- Mark fields `readonly` and inputs `readonly T[]` when you do not mutate them.
- Use `satisfies` to check a literal against a type without widening it.
- Brand identifiers that must not mix: `type OrderId = string & { readonly __brand: "OrderId" }` (G26).
- Avoid `as` assertions; when one is unavoidable, assert once, at the boundary, after validation.
- Prefer literal unions or `as const` objects to `enum`. With `erasableSyntaxOnly` or Node's type stripping, write no `enum`, `namespace`, or parameter properties at all.
- Use classes when state and behavior belong together; plain types and functions otherwise.

## Errors

- Treat `catch (error)` as `unknown`: narrow with `instanceof` before reading anything from it.
- Return expected outcomes as a discriminated union — `{ ok: true; value: T } | { ok: false; reason: Reason }` — and keep `throw` for genuine failures.
- Validate external data at the boundary with a schema (Zod, Valibot, or project's choice) and derive the type from the schema; a cast validates nothing.

## Modules And Visibility

- Use `import type` for type-only imports and enable `verbatimModuleSyntax`, so erased imports never turn into runtime dependencies.
- Export only the types consumers need; implementation types stay module-private (G8).
- Use `paths` aliases only where project defines them. TypeScript 6 deprecates `baseUrl` and 7 removes it: write `paths` relative to the tsconfig.
- Keep `.d.ts` files for ambient declarations; types for your own code live beside that code.

## Placement

- Put a type next to the code that owns it; a shared `types.ts` junk drawer is misplaced responsibility (G17).
- Keep boundary schemas with the adapter that parses the input, and domain types in the domain.

## Tests

- Run `tsc --noEmit` (or the build's type check) as a test step: a type error is a failing test.
- Pin important type-level contracts with `expectTypeOf` (Vitest) or `@ts-expect-error` lines.
- Never loosen a production type to make a test compile; fix the test's data.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Domain types never import framework, ORM, or HTTP types; map DTOs to domain types in the adapter (the Dependency Rule).
- Declare ports as interfaces in the inner layer (`interface OrderRepository`); adapters implement them, the composition root wires them.
- Keep schema libraries at the boundary; the domain receives validated plain types.

## Enforce

- `tsc --noEmit` in CI with `strict` and `noUncheckedIndexedAccess`.
- typescript-eslint `strict-type-checked`, including `no-explicit-any`, `no-floating-promises`, `no-misused-promises`, `consistent-type-imports`, `switch-exhaustiveness-check`.
- dependency-cruiser or eslint-plugin-boundaries for dependency direction.

## Smells

- `any` leaking from one untyped boundary across the codebase (G26).
- `as` casts silencing errors instead of narrowing them (G4).
- Unions without exhaustive handling: a new variant compiles and is silently ignored (G23).
- Floating promises the linter would have caught (G4).
- One global `types.ts` holding unrelated types (G17).
- Hand-written types drifting from the schema they describe (G5).
