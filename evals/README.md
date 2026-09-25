# Evals

Evidence that the skill changes what an agent does: where it puts code, what it reads first, what it
refuses to do. Repository-only; the installer never copies this folder.

## Layout

```text
evals/
  grade.py          grades a finished run; --self-test checks every case; --export-evals
  evals.json        the cases in skill-creator's format (generated: grade.py --export-evals)
  triggers.json     queries that should and should not activate the skill
  cases/<id>/
    case.json       prompt, expected output, machine-checkable expectations
    repo/           the fixture project the agent works on
```

## Expectations

Every expectation has a `type`, a human-readable `text`, and the fields its type needs. Globs use
the skill's own matcher: `**` spans folders, matching ignores case.

| Type | Fields | Passes when |
| --- | --- | --- |
| `file_exists` | `glob` | a file matches |
| `file_contains` | `glob`, `pattern` | a matching file contains the regex |
| `file_not_contains` | `glob`, `pattern` | no matching file contains it |
| `unchanged` | `path` | the file equals the fixture's, line endings aside |
| `no_new_files` | `glob` (one glob or a list) | no file matching the glob was added; lockfiles and `.gitignore`, which installing a dependency writes, do not count |
| `new_file` | `glob` (one glob or a list) | at least one file matching any glob was added; the inverse of `no_new_files`, with the same lockfile exemption |
| `map_finding_absent` | `kind`, optional `path` | `map_structure.py` reports no finding of that kind; `path` is a glob matched against each finding's own `path` or `folder`, so a case can require a clean file while others in the fixture still have theirs. A kind the scanner does not populate yet (an organization finding not built yet) counts as zero findings |
| `boundaries_pass` | — | `check_boundaries.py` exits 0 |
| `transcript_reads` | `pattern` | one of the run's tool calls matches (a plain-text transcript is matched whole), with backslashes read as `/`; skipped when there is none |
| `read_before_edit` | `pattern` | a tool call matching the pattern happens before the run's first file-changing call (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`), or anywhere at all when there is no such call; skipped when there is no transcript |
| `command_passes` | `command` (a non-empty list), optional `timeout` (default 60s) | the command exits 0, run with the workspace as its working directory; fails with the tail of its combined output otherwise; skipped when the executable is not found |

`grade.py --self-test` rejects a case whose expectations all pass on the untouched fixture: such a
case cannot tell a good run from a do-nothing run.

## Running A Model Eval

1. Copy `cases/<id>/repo` to a scratch workspace twice: one run with the skill, one without.
2. Run the agent on each copy with the case's `prompt`. For the with-skill run, make
   `skills/clean-code/` available as an installed skill; save each transcript.
3. Grade each copy:

   ```bash
   python evals/grade.py --case evals/cases/<id> --workspace <copy> \
     --transcript <transcript> --output <copy>/grading.json
   ```

4. Compare pass rates between the two configurations and record them below. skill-creator's
   aggregation reads the `grading.json` files directly.

CI runs `grade.py --self-test` only: model runs cost money and are done at release time.

## Adding A Case

Keep the fixture to a handful of files that look like a real project. Write at least three
deterministic expectations, and make sure at least one fails on the untouched fixture. Prefer
expectations about placement, boundaries, and preserved behavior over exact wording. Then run
`python evals/grade.py --export-evals evals/evals.json` and `python evals/grade.py --self-test`.

## Results

### Iteration 2

2026-09-25: eight cases (hallucinated-api, unverified-success, unsafe-refactor,
frontend-data-fetch, naming-cleanup, comment-cleanup, core-context-gate, core-init), with and
without the skill, two runs per configuration on Claude Sonnet 5 and one on Claude Haiku 4.5: 48
runs. Subagents in Claude Code on Windows, the skill read from a snapshot of commit `f43eb20`,
graded by `grade.py` at commit `cf71bb6`.

| | Sonnet, with | Sonnet, without | Haiku, with | Haiku, without |
| --- | --- | --- | --- | --- |
| Pass rate (judged expectations) | 98.8% (81 of 82) | 92.7% (76 of 82) | 95.1% (39 of 41) | 92.7% (38 of 41) |
| Tokens per run, mean | 76k | 67k | 53k | 48k |
| Time per run, mean | 125 s | 90 s | 67 s | 54 s |
| Feature runs that added a test | 6 of 8 | 4 of 8 | 2 of 4 | 2 of 4 |

- Three expectations told the configurations apart, all about loading context: reading the pack
  that `.clean/context.json` lists (Sonnet 2 of 2 with the skill, 0 of 2 without), reading it
  before the first edit (1 of 2 against 0 of 2), and `init` recording the packs (3 of 3 against
  0 of 3). Haiku with the skill skipped the pack in core-context-gate, like the baseline: the
  smaller model follows the context gate less reliably.
- The planted-flaw cases did not separate the configurations: both avoided the missing money
  helper (reading the module, then adding or composing), kept the pinned refactor tests green,
  and ran the suite before claiming success. The difference lay in how unverified-success ended:
  with the skill, Sonnet left the unrelated failing test unfixed and reported it (surgical scope);
  without it, every run fixed the one-line bug, which the prompt ("make sure the test suite
  passes") arguably asked for. Both satisfy the case, which grades honesty, not the fix.
- The cost is about 13% more tokens and 25-40% more time per task, spent reading `SKILL.md`,
  packs, and references and running the scanners — down from 48% more tokens in iteration 1.
- Confounds: runs without the skill still received this repository's `CLAUDE.md`, whose managed
  block carries the core rules; the Write tool refused the harness's `summary.md` path, so runs
  wrote it with a shell command, which costs a few turns in both configurations.
- Corrected after the first grading pass, because correct work failed them in both
  configurations: hallucinated-api now checks behavior (the exported line-price function returns
  750 for 3 units at 250 cents) instead of a function name and the absence of `money.multiply`
  (commit `255ab98`), and frontend-data-fetch accepts `Revenue: {formatRevenue(...)}` (commit
  `cf71bb6`).

### Iteration 1

2026-09-23: ten cases (the four core cases, Express, Django, Spring, Flutter, Rust,
and ASP.NET Core), one run per configuration, Claude Sonnet 5 subagents in Claude Code on Windows,
graded by `grade.py` at commit `834430f`.

| | With the skill | Without it |
| --- | --- | --- |
| Pass rate, mean per run | 100% (48 of 48) | 95.5% (46 of 48) |
| Tokens per run, mean | 124k | 84k |
| Time per run, mean | 513 s | 284 s |
| Code-changing runs that added tests | 8 of 9 | 2 of 9 |

- Two expectations told the configurations apart: with the skill, the run read the Express pack
  that `.clean/context.json` lists, and `init` recorded the packs. Every other expectation passed
  both ways, so the next iteration needs sharper cases, a frontend case, a tests-added expectation,
  a check that the packs were read before the first edit, and several runs per configuration.
- Runs without the skill still received this repository's `CLAUDE.md`, whose managed block
  carries the core rules. The comparison measures `SKILL.md`, the packs, and the scripts on top of
  that block.
- The cost is real: about 40k more tokens and four more minutes per task, spent reading packs,
  running the scanners, and writing tests.
- Three expectations were corrected after the first grading pass because they failed correct work
  in both configurations (commit `cace411`).
