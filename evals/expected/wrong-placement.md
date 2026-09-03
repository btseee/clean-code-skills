# Expected: wrong-placement

**Smells under test:** A6 Wrong-File Gravity, A10 Silent Architecture Drift, A3 Context Loss.

**Trap.** The open file is the controller. The rounding rule is a business rule; the layering in
`.clean/architecture.md` puts business rules in `src/orders/domain`.

**Pass.**

- The rounding rule lives in `src/orders/domain/` (in `order.ts` or a new domain file wired in
  and used by the controller), as a plain function.
- The controller calls it and holds no currency logic.
- No new file at the repository root or in `src/orders/api/` for domain logic.
- `python skills/clean-code/scripts/check_boundaries.py --root <fixture>` still exits 0.
- A test for the rule exists beside the domain code, not through the controller.

**Fail.**

- `if (order.currency === "JPY")` inside `orders-controller.ts`.
- A `utils.ts` or `helpers.ts` created for it.
- The rule tested only by calling the controller.

**Record.** architecture violations (check_boundaries exit code), files created and where,
changed LOC, whether `.clean/architecture.md` was read (the report should mention the layering).
