# Plan Protocol

For `/clean-code plan <task>` or "plan this change using the clean-code skill before editing
anything". The output is a change plan in the conversation; **no production code, test, or
configuration changes**. Reading, searching, and running read-only scripts are allowed. If the
plan needs a file written, that is the next task, not this one.

The plan exists to catch the agent smells that are cheapest to catch before the first edit:
hallucinated APIs (A1), duplicate implementations (A5), wrong-file gravity (A6), speculative
abstractions (A9), and silent drift (A10). Spend the effort there, not on prose.

## Inspect before writing

1. Load context (`session-protocol.md`, step 1): `.clean/` if it exists, then the project's own
   instruction files. Note the declared layers and any decision that touches the task.
2. Find the existing implementation. Search for the behavior, the concept's name, and its obvious
   synonyms. Most tasks extend something; say what.
3. Read the units the change will touch, their callers, and their tests.
4. Confirm the APIs the plan relies on exist in the installed versions (`.clean/context.json`,
   `.clean/dependencies.json`, or the manifests and the packages themselves).
5. Classify the risk (`risk-verification.md`) so the verification plan matches it.

## Output

Use these headings in this order. Keep each section to what a reviewer needs; a line is fine.

```markdown
## Goal
<One sentence: what will be true when the change is done.>

## Existing implementation
<What already does part of this, where, and whether the plan extends or replaces it.>

## Likely affected files
<Paths, each with one phrase on what changes. New files marked as new, with their wiring.>

## Ownership / responsibility
<Which unit owns the new behavior and why; what stays out of it.>

## Architecture boundaries crossed
<Layers or seams the change touches, and the direction of every new dependency.>

## Dependencies involved
<Packages and versions relied on; anything to add, and the reason. "None" is a valid answer.>

## Risks
<What could go wrong: correctness, data, security, concurrency, compatibility, blast radius.>

## Proposed smallest change
<The steps, in order, sized to one reviewable diff. Name what is deliberately left out.>

## Verification plan
<Risk level and the checks that match it: exact commands where known.>

## Open assumptions
<What was assumed because it could not be verified, and what would settle each one.>
```

## Example

`/clean-code plan Add Stripe refund support`

```markdown
## Goal
Refunds can be issued for a paid order without Stripe SDK types entering the domain layer.

## Existing implementation
`PaymentGateway` (src/application/ports/payment-gateway.ts) already abstracts charges; there is no
refund method. `StripePaymentGateway` implements it. No refund logic exists anywhere.

## Likely affected files
- src/application/ports/payment-gateway.ts: add `refund(paymentId, amount)` to the port
- src/application/refund-service.ts (new): orchestrates refund, wired in main.ts
- src/infrastructure/stripe-payment-gateway.ts: implement `refund` via `stripe.refunds.create`
- src/application/refund-service.test.ts (new), stripe-payment-gateway.contract.test.ts

## Ownership / responsibility
RefundService owns the rule (only paid, not already refunded, amount <= captured). The gateway
owns the Stripe call and nothing else.

## Architecture boundaries crossed
HTTP -> Application -> PaymentGateway port -> Stripe adapter. All new dependencies point inward.

## Dependencies involved
stripe 14.x (installed; `refunds.create` confirmed in node_modules/stripe/types). Nothing to add.

## Risks
Duplicate refund on retry; partial-refund arithmetic; SDK version drift; who is authorized.

## Proposed smallest change
1. Port method. 2. Service with the three rules and an idempotency key. 3. Adapter method.
4. Wire in main. Deliberately out: refund UI, webhooks for async refund status.

## Verification plan
MEDIUM. Service unit tests; gateway contract test against Stripe's test mode or a recorded
fixture; `yarn tsc --noEmit`; `yarn test src/application`.

## Open assumptions
Refund authorization reuses the order-owner check (confirm with the user). Idempotency key format
follows the existing charge key (confirm in charge-service.ts).
```

## Rules

- Never edit while planning. If you notice a bug, it goes under Risks, not into the code.
- Every "likely affected file" you name must exist or be marked new. Guessing paths is A6 in
  advance.
- Every API named must have been checked (A1). Say where it was checked.
- If the task is trivial (a rename, a typo), say so in two lines and stop; a plan is not a ritual.
- Close by offering to execute the plan. When the user agrees, the plan's Verification section is
  the acceptance test for the handoff.
