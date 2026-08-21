# Examples

Examples showing how agents should apply clean-code discipline without overreaching. These are illustrative, not language mandates.

## 1. Hidden Scope Assumption

**Request:** Add export for customer records.

**Weak agent behavior:** Immediately exports every customer field to a CSV file in the project root.

**Clean-code behavior:** Clarify scope before implementation because privacy, volume, and format affect the design.

```text
I need one decision before coding: should export include all customers or the current filtered set? Customer fields may include private data, so I will only include the existing list-view fields unless you want a different export contract.

Smallest implementation: add a CSV export for the current filtered list and test that private fields are excluded.
```

## 2. Speculative Abstraction

**Request:** Calculate a 10 percent invoice discount.

**Too much:**

```python
class DiscountStrategy:
    def calculate(self, invoice):
        raise NotImplementedError

class PercentageDiscountStrategy(DiscountStrategy):
    def __init__(self, percent, max_amount=None, min_total=None):
        self.percent = percent
        self.max_amount = max_amount
        self.min_total = min_total

    def calculate(self, invoice):
        # many branches for requirements that do not exist yet
        ...
```

**Clean enough for the request:**

```python
def discount_amount(invoice_total: Decimal) -> Decimal:
    return invoice_total * Decimal("0.10")
```

Add strategies later when there are multiple real discount rules.

## 3. Comments Hiding Bad Names

**Weak:**

```typescript
// Check if the user can access the report
if (u.a && r.s !== 'x') {
  return true
}
```

**Cleaner:**

```typescript
const hasActiveSubscription = user.subscriptionActive
const reportIsNotArchived = report.status !== 'archived'

return hasActiveSubscription && reportIsNotArchived
```

The comment became unnecessary because the names now carry the intent.

## 4. Error Handling That Loses Context

**Weak:**

```go
payload, err := client.Fetch(ctx, id)
if err != nil {
    return nil, err
}
```

**Cleaner:**

```go
payload, err := client.Fetch(ctx, id)
if err != nil {
    return nil, fmt.Errorf("fetch customer %s: %w", id, err)
}
```

The caller can still inspect the original error, and logs identify which customer failed.

## 5. SQL Boundary Risk

**Weak:**

```sql
SELECT *
FROM orders o, customers c
WHERE o.customer_id = c.id
AND c.email = 'user input here';
```

**Cleaner:**

```sql
SELECT
  o.id,
  o.created_at,
  o.total_amount
FROM orders AS o
JOIN customers AS c ON c.id = o.customer_id
WHERE c.email = :email;
```

The query names returned columns, makes the join explicit, and leaves parameter binding to the database client.

## 6. React Component Doing Too Much

**Weak signs:** One component fetches data, manages retries, formats currency, owns modal state, renders a table, and updates the URL.

**Clean-code response:** Do not rewrite the whole component during a small bug fix. If the task is to fix currency formatting, change the formatting path and add a focused test. Mention the broader component split as a follow-up if it slows the fix.

## 7. Refactor With Verification

**Request:** Refactor payment status parsing.

**Clean-code plan:**

```text
1. Run existing parser tests to capture the baseline.
2. Add missing cases for unknown, pending, paid, failed, and provider-specific status values.
3. Replace duplicated parsing branches with one named mapping.
4. Rerun the parser tests and any payment integration tests.
```

The refactor is behavior-preserving and has a verification loop.

## 8. Concurrency Smell

**Weak:** A job retries failed work by reading a shared list, appending retry items, and clearing the list from another thread.

**Cleaner direction:** Put ownership in one place: a queue, channel, actor, transaction, or lock-protected structure that makes ordering and lifecycle explicit. Add a test or stress check for duplicate processing and cancellation.

## 9. Drive-By Formatting

**Request:** Fix an empty-email crash.

**Bad diff shape:** The agent reformats the file, renames unrelated variables, changes validation rules, and then fixes the empty email.

**Clean diff shape:** The agent changes only the empty-email path, adds or updates a focused test, and leaves unrelated validation for a separate task.

## 10. Completion Claim

**Weak:** "This should work now."

**Clean:** "I ran `npm test -- email-validator` and the empty-email regression test passes. I did not run the full suite."

## 11. File Created In The Wrong Place

**Request:** Add a currency formatting helper for the invoice page.

**Weak agent behavior:** Creates `formatCurrency.ts` in the repository root, or in whatever directory the last edit touched, and never imports it anywhere.

**Clean-code behavior:** Look at where formatting helpers already live. If the project has `src/lib/format/date.ts` used by other pages, the new helper belongs at `src/lib/format/currency.ts`, named and exported the same way, imported by the invoice page, and covered by a test in the same pattern as `date.test.ts`. If a currency formatter already exists, extend it instead of adding a second one.

## 12. Sibling-Variant File

**Request:** Improve the retry logic in `http_client.py`.

**Weak agent behavior:** Creates `http_client_v2.py` (or `http_client_new.py`) with the improved logic, leaving both files in the tree and callers split between them.

**Clean-code behavior:** Edit `http_client.py` in place. Version control preserves the old implementation; the project keeps exactly one HTTP client.

## 13. Mixed Responsibilities In One Function

**Weak:**

```python
def register_user(raw):
    data = json.loads(raw)
    if "@" not in data["email"]:
        return {"error": "bad email"}
    user = db.insert("users", data)
    smtp.send(data["email"], WELCOME_TEMPLATE)
    log.info("registered %s", data["email"])
    return {"id": user.id, "html": render("welcome.html", user)}
```

One function parses transport data, validates, persists, sends email, logs, and renders. Testing it needs a database, an SMTP server, and a template engine.

**Cleaner shape:** `register_user` becomes an orchestrator that sequences `parse_registration(raw)`, `validate_registration(data)`, `create_user(data)`, and `send_welcome(user)` — each unit testable alone, each living in the layer the project uses for that concern (API parsing, domain, persistence, notifications). Rendering stays in the view layer that called it.

Do not perform this split as a drive-by during an unrelated fix; do it when the task touches this function, or record it as a finding.

## 14. Reinvented Helper

**Request:** Truncate product descriptions to 140 characters in the search results.

**Weak agent behavior:** Writes a new `truncateString` function from memory — the third one in the codebase.

**Clean-code behavior:** Search first (`truncate`, `ellipsis`, `shorten`). Finding `text/truncate.ts` already used by two components, reuse it. If it lacks the needed option, extend it with a test, keeping its existing callers green.

## 15. Whole-Project Cleanup Request

**Request:** "Clean up this whole project with clean code."

**Weak agent behavior:** Starts rewriting files alphabetically, mixing renames, logic changes, and formatting in giant diffs until context runs out, leaving the project half-migrated.

**Clean-code behavior:** Switch to campaign mode (`references/project-refactor.md`):

```text
Proposed contract: structural depth, src/ only, behavior-preserving, one commit per batch.
Baseline: 214/214 tests pass; lint clean; build green (recorded verbatim).
Plan: 1) delete dead exports  2) rename ambiguous managers to domain names
      3) split mixed-responsibility services  4) normalize error wrapping.
Ledger: cleanup-ledger.md tracks batches, findings, and deferred bugs.
```

Each batch is verified against the baseline and committed separately. A rounding bug found in batch 3 goes into the ledger for the user, not silently fixed inside a rename commit.

## 16. Full-Map Review

**Request:** Review this service for clean code.

**Too shallow:** Only comments on naming and function length.

**Clean-code behavior:** Scan the chapter map and report grouped findings:

```text
Findings:
- Boundary: vendor errors are passed through without a local contract.
- Tests: retry and timeout paths are untested near a recent production bug.
- Concurrency: job cancellation can race with queue acknowledgement.
- Functions: `processBatch` validates, transforms, persists, retries, and emits metrics.

No findings in comments/formatting after formatter output.
```

The review uses the full map without inventing unrelated rewrites.
