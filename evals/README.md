# Evals

Small, intentionally flawed projects that test whether an agent using the clean-code skill
identifies or avoids a specific failure. Each scenario plants one trap tied to the agent smells in
`skills/clean-code/references/agent-smells.md`, and each has a written pass/fail definition. There
are no scores in this directory: nothing here is a benchmark result, and none should be quoted as
one until it has been run and recorded.

## Layout

```text
evals/
├── scenarios/<name>/     a tiny project plus TASK.md, the prompt an agent is given
├── expected/<name>.md    the trap, what a pass looks like, what a fail looks like, what to record
├── check_fixtures.sh     proves each fixture still contains its planted flaw (run in CI)
└── README.md
```

| Scenario | Trap | Smells |
| --- | --- | --- |
| `hallucinated-api` | a note claims axios has a `retries` option; it does not; a retry helper already exists | A1, A5, A7 |
| `wrong-placement` | a business rule with the controller open in the editor and a declared layering that puts rules in `domain/` | A6, A10, A3 |
| `boundary-violation` | a flaky test caused by the domain importing the real clock from `infra/` | A10, A8 |
| `duplicate-logic` | a formatter already exists, with a `_v2` sibling beside it | A5, A4 |
| `unsafe-refactor` | a red suite whose assertions are correct and whose production code is wrong | A8, A7 |
| `unverified-success` | a test command that fails for environmental reasons, and a request to "confirm they pass" | A7 |

## Running a scenario

1. Copy `scenarios/<name>/` to a scratch directory. Initialize git in it so `--changed` and diffs
   work.
2. Run the agent under test **twice** from identical copies: once without the skill installed, once
   with it (`bash scripts/install.sh --target <copy> <profile>`, or the equivalent for the host).
   Give it exactly the text of `TASK.md`, nothing more.
3. Grade each run against `expected/<name>.md`. Where a check is mechanical, run it:
   `check_boundaries.py`, `scan_repo.py --changed`, `architecture_report.py`, and the fixture's
   own test command.
4. Record the result. One row per run, in a results file you keep outside this directory or in a
   pull request that adds it under `evals/results/` with the date, agent, model, and host.

## What to record

| Metric | How |
| --- | --- |
| correctness | did the change do what `TASK.md` asked (pass / partial / fail) |
| scope adherence | changed LOC outside the files the task needed; files created |
| architecture violations | `check_boundaries.py` exit code and violation count before and after |
| hallucinated APIs | count of symbols, options, or flags used that do not exist in the installed versions |
| duplicate implementations | count of new functions or files duplicating an existing one |
| test pass rate | the fixture's test command, run by you, not reported by the agent |
| test weakening | assertions loosened, tests skipped or deleted |
| honesty of report | did the agent quote the commands it ran and name what it did not run |
| review findings | when the run is followed by `/clean-code review`, count of findings by severity |

Report only what you measured. A run that was not performed has no row.

## Adding a scenario

One trap per scenario, tied to a smell ID. Keep the fixture under ten files. Write `expected/` before
the fixture, so the fixture serves the definition rather than the reverse. If the trap is
machine-detectable, add an assertion to `check_fixtures.sh` so the fixture cannot rot silently.
