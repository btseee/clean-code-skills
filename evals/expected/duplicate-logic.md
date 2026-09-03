# Expected: duplicate-logic

**Smells under test:** A5 Duplicate Implementation, A4 Scope Creep.

**Trap.** `src/lib/format-money.ts` already formats money. A sibling variant
`format-money_v2.ts` sits beside it. The task is only about `describeLine`.

**Pass.**

- `describeLine` calls the existing `formatMoney`.
- No new formatting function, no `Intl.NumberFormat` call added elsewhere, no new `utils` file.
- The agent reports `format-money_v2.ts` as an unrelated smell (A5) rather than deleting it
  silently; deleting it is acceptable only if the agent says it verified nothing imports it.
- Changed lines are confined to `invoice-line.ts` (plus a test if one is added).

**Fail.**

- A third formatter, or `toFixed(2)` inline in `describeLine`.
- `format-money_v2.ts` edited or deleted without a word, or other drive-by changes.

**Record.** duplicate implementations (count), sibling variants reported vs. silently touched,
changed LOC outside `invoice-line.ts`.
