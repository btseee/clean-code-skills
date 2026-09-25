# Worked Examples

Before-and-after cases, plus three output templates — illustrative, not language mandates; the
lesson transfers, not the syntax.

## Do not abstract for requirements that do not exist

**Request: apply a 10 percent invoice discount.**

Too much: a strategy hierarchy for rules nobody asked for.

```python
class DiscountStrategy:
    def calculate(self, invoice): raise NotImplementedError

class PercentageDiscountStrategy(DiscountStrategy):
    def __init__(self, percent, max_amount=None, min_total=None):
        self.percent, self.max_amount, self.min_total = percent, max_amount, min_total

    def calculate(self, invoice):
        ...  # branches for requirements that do not exist yet
```

Enough for the request:

```python
def discount_amount(invoice_total: Decimal) -> Decimal:
    return invoice_total * Decimal("0.10")
```

Add the strategy once a second real discount rule exists. Money is `Decimal`, never a float.

## Let names carry the intent, then delete the comment

Weak — the comment exists because the code is unreadable:

```typescript
// Check if the user can access the report
if (u.a && r.s !== 'x') return true
```

Cleaner:

```typescript
const hasActiveSubscription = user.subscriptionActive
const reportIsNotArchived = report.status !== 'archived'

return hasActiveSubscription && reportIsNotArchived
```

Named variables now carry what the comment compensated for — it is gone.

## Preserve the cause when wrapping an error

Weak — the error propagates with no indication of what failed:

```go
payload, err := client.Fetch(ctx, id)
if err != nil {
    return nil, err
}
```

Cleaner:

```go
payload, err := client.Fetch(ctx, id)
if err != nil {
    return nil, fmt.Errorf("fetch customer %s: %w", id, err)
}
```

`%w` keeps the original error inspectable, and the message says which customer failed — context
added, nothing hidden.

## Make the boundary explicit in SQL

Weak — implicit join, `SELECT *`, and a value pasted into the statement:

```sql
SELECT *
FROM orders o, customers c
WHERE o.customer_id = c.id
AND c.email = 'user input here';
```

Cleaner:

```sql
SELECT
  o.id,
  o.created_at,
  o.total_amount
FROM orders AS o
JOIN customers AS c ON c.id = o.customer_id
WHERE c.email = :email;
```

Named columns survive a schema change, the join is explicit, and client-owned parameter binding
closes the injection hole too.

## Split mixed responsibilities — when the task touches them

Weak — one function parses transport data, validates, persists, sends mail, logs, and renders:

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

Testing it needs a database, an SMTP server, and a template engine — the test-pain check signaling
mixed concerns.

Cleaner: `register_user` orchestrates `parse_registration(raw)`, `validate_registration(data)`,
`create_user(data)`, and `send_welcome(user)` — each testable alone, each in the project's layer
for that concern; the orchestrator holds no business rules of its own.

**Do not split this as a drive-by during an unrelated fix** — only when the task touches this
function; otherwise record it as a finding.

## Template: reporting completion honestly

Weak:

> This should work now.

Clean:

> I ran `npm test -- email-validator` and the empty-email regression test passes. I did not run the
> full suite.

The difference is evidence and a stated gap.

## Template: a campaign contract

When cleanup itself is the task, agree this before editing anything (see `project-refactor.md`):

```text
Proposed contract: structural depth, src/ only, behavior-preserving, one commit per batch.
Baseline: 214/214 tests pass; lint clean; build green (recorded verbatim).
Plan: 1) delete dead exports  2) rename ambiguous managers to domain names
      3) split mixed-responsibility services  4) normalize error wrapping.
Ledger: .clean/ledger.md tracks batches, findings, and deferred bugs.
```

Verify and commit each batch against the baseline separately; a bug found during batch 3 goes into
the ledger — never silently fixed inside a rename commit.

## Template: review findings

Naming and function length alone is too shallow a review. Scan the map, group by concern, and cite
smell IDs (see `chapter-map.md`):

```text
Findings:
- Boundary: vendor errors are passed through without a local contract.
- Tests (T6): retry and timeout paths are untested near a recent production bug.
- Concurrency: job cancellation can race with queue acknowledgement.
- Functions (G30): `processBatch` validates, transforms, persists, retries, and emits metrics.

No findings in comments or formatting after formatter output.
```

Findings first, each with a location and a consequence. No invented rewrites.
