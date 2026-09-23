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
| `no_new_files` | `glob` | no file matching the glob was added |
| `map_finding_absent` | `kind`, optional `path` | `map_structure.py` reports no finding of that kind (mentioning the path) |
| `boundaries_pass` | — | `check_boundaries.py` exits 0 |
| `transcript_reads` | `pattern` | the run's transcript matches, with backslashes read as `/`; skipped when there is none |

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

No model runs are recorded yet.
