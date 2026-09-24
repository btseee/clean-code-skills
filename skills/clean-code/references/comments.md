# Comment Cleanup

For comment work: the comment batch of `/clean-code clean-up`, review findings C1-C5 or G12, or code,
often agent-written, that narrates itself line by line. Goal: fewer comments, each true and
necessary, and code that says the rest.

## Pick the files

- **Campaign or audit:** start with the files the map reports as `comment_heavy` in
  `.clean/structure.md` (full list in `.clean/structure.json`); refresh a stale map with
  `scripts/map_structure.py --write`. By hand: count comment lines per file and start where comments
  rival code.
- **Surgical mode:** only comments in lines your change touches; report the rest.

## Comments tools read are code

Never delete or reword a comment a tool reads: shebangs, encoding lines, license and SPDX headers,
build and compiler directives (`//go:build`, `#pragma`, `// @ts-check`), suppressions (`# noqa`,
`# type: ignore`, `// eslint-disable-next-line`, `// @ts-expect-error`), doctests, and JSDoc types a
type checker enforces. A generated-file header means: leave the whole file alone. An unexplained
suppression is a finding, not a comment to delete.

## Classify each comment

Keep these, tersely:

| Kind | Keep when | Example |
| --- | --- | --- |
| Legal | the project or its license requires the header | `# SPDX-License-Identifier: MIT` |
| Informative | it states a fact code cannot: a format, a unit, a source | `# timestamps: epoch milliseconds, UTC` |
| Intent | it says why this approach beats the obvious one | `# linear scan: lists stay under 20 items` |
| Clarification | it translates an obscure value you cannot rename | `if code == 0x2A:  # vendor status "queued"` |
| Warning | changing or calling the code has a consequence nobody would guess | `# not reentrant: hold jobs_lock` |
| TODO with owner | it names who, what, and ideally a ticket | `# TODO(billing, #412): remove after v2 migration` |
| Amplification | a line looks removable and is not | `.rstrip("\n")  # a trailing newline breaks the signature` |
| Public API docs | exported units, in an ecosystem that publishes docs from them | docstrings, JSDoc, XML docs |

Delete these:

| Kind | Looks like | Cite |
| --- | --- | --- |
| Mumbling | a half-thought only its author could decode | C4 |
| Redundant | the next line, restated | C3 |
| Misleading | a claim the code does not honor | C2 |
| Mandated | a docblock on every function, repeating its signature | C3, G12 |
| Journal | a change log at the top of the file | C1 |
| Noise | `// constructor`, `# getters`, `# imports` | C3, G12 |
| Position markers | `// ====== HELPERS ======` banners | G12 |
| Closing-brace | `} // end for` | G12; the function is too long (G30) |
| Attributions | `# added by Dana` | C1 |
| Commented-out code | disabled statements kept "just in case" | C5, G9 |
| Nonlocal | a description of code or configuration elsewhere | C1 |
| Too much information | history, meeting notes, pasted specifications | C1 |

Version control keeps history, authors, and removed code; the ticket keeps the debate.

## Order of work

1. **Delete the bad kinds.** Cheapest step, biggest win.
2. **Turn "what" comments into code.** A comment explaining what a block does is a name not yet
   written: an explanatory variable (G19), a function extracted and named after the comment (G20,
   G30), a named constant (G25), or a type. Then delete the comment.
3. **Rewrite surviving "why" comments tersely.** One line where possible: the constraint and its
   source, not the story. Cut articles, filler, and hedging; keep IDs, numbers, links, and warnings
   whole.

Narration agents often leave:

```javascript
// Function to calculate the total
// Takes an array of items and returns the total price
function calc(items) {
  // Initialize the total to zero
  let t = 0;
  // Loop through each item
  for (const i of items) {
    // Add the price multiplied by the quantity
    t += i.price * i.qty;
  }
  // Return the total
  return t;
}
```

After: every comment gone, the name carries the intent, the platform runs the loop.

```javascript
function orderTotal(items) {
  return items.reduce((total, item) => total + item.price * item.qty, 0);
}
```

A "why" comment, before and after:

```python
# We have to wait a little here because the payment provider rate-limits us
# and starts answering HTTP 429 if we go faster. Found in production, see PAY-231.
time.sleep(0.2)
```

```python
time.sleep(0.2)  # provider rate limit: HTTP 429 when faster; PAY-231
```

## Over-built code the comments narrate

Heavy narration often covers code that should not exist. Before polishing its comments, climb the
minimal-code ladder (credited to the ponytail plugin) and stop at the first yes:

1. Does it need to exist? A speculative option, a branch nothing reaches, or a wrapper nobody calls
   goes (G9, F4).
2. Does the codebase already have it? Call that (G5).
3. Does the standard library, the platform, or an installed dependency do it? Use that, at the
   installed version.
4. Is it one line? Write the line.
5. Only then write the minimum.

Never cut validation, error handling, security checks, or accessibility to get shorter. Replacing
code is not a comment edit: in a campaign it belongs to a structure batch, with tests; in surgical
mode, report it unless the task covers it.

## Done when

- No comment of a deleted kind remains in scope; each survivor is a kept kind, stated tersely.
- Comments tools read are untouched.
- Formatter, linter, and tests ran after the edit, since doctests, directives, and generated docs
  live in comments; results reported.
- Report per file: comments deleted, turned into names, and rewritten, plus any code the ladder
  removed.
