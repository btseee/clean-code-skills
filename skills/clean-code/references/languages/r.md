# R

> Applies to: R 4.4+. Formatter: styler. Linter: lintr. Read with: nothing.

## Names

- Use snake_case for functions and variables, per the tidyverse style guide; reserve dots for S3 dispatch (`print.my_class`), never as a plain word separator (G11, N3).
- Name a function for what it returns or does (`clean_scores`, not `f` or `tmp`) (N1, G20).
- Spell out `TRUE` and `FALSE` in full; never rely on `T`/`F`, which are ordinary bindings, not reserved words (N4).

## Functions And Types

- Keep functions small and pure: same input, same output, nothing read from or written to outside the arguments (Do One Thing).
- Never use `<<-` to reach into a parent or global environment; return a value and let the caller assign it (G18).
- Prefer a vectorized expression over a loop that rebuilds a result element by element.
- Use S3 for simple dispatch; reach for S4 or R6 only where the project already relies on one, and never mix a second object system in (G11).
- Name a magic threshold or tuning constant instead of burying it as a bare literal in a pipe (G25).

## Errors

- Signal failures with a classed condition, `rlang::abort("message", class = "pkg_bad_input")`, not a bare `stop("string")` a caller cannot branch on (Special Case pattern).
- Catch narrowly, on the class: `tryCatch(expr, pkg_bad_input = function(e) ...)`, never a catch-all that hides unrelated failures (G4).
- Never swallow a condition with `try()` or `suppressWarnings()` without handling what it caught (G4).
- Chain the cause when wrapping: `rlang::abort(msg, parent = e)`, so the original condition is not lost.

## Modules And Visibility

- Export only what roxygen2's `@export` marks and the generated `NAMESPACE` lists; leave internal helpers unexported (G8).
- Keep one function's `@param`/`@return` roxygen block directly above it; never hand-edit the generated `man/*.Rd` files.
- Declare every dependency in `DESCRIPTION`'s `Imports`; call it with `::` rather than a bare `library()` inside package code.

## Placement

- Package projects: one file per concept under `R/`, never one file per function and never a single catch-all `functions.R` (G17).
- Analysis projects: keep cleaning, modeling, and plotting in functions; let the top-level script or a `{targets}` pipeline (`_targets.R`) only call them in sequence.
- Keep generated output (rendered reports, cached `.Rds` files) out of source folders; route it to an ignored directory or `{targets}`'s own store.

## Tests

- Use testthat 3rd edition (`usethis::use_testthat(3)`); mirror `R/<topic>.R` with `tests/testthat/test-<topic>.R`.
- Assert with `expect_equal`/`expect_identical`, not a hand-written `if (...) stop(...)` inside a test.
- Assert on the condition's class, not its message string: `expect_error(f(bad), class = "pkg_bad_input")` survives a wording edit (G26).
- Restore state automatically with `withr::local_*` helpers instead of a manual teardown a failed test can skip (F.I.R.S.T. — Independent).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- A domain function in `R/` never calls `read_csv`, `dbGetQuery`, or `httr::GET` itself; it takes an already-loaded data frame and returns one (the Dependency Rule).
- Document the data frame a domain function expects — its columns and types — in that function's roxygen `@param`, not as a database or API response shape.
- Compose the pipeline — which adapter feeds which domain function — only in `_targets.R` or the top-level script (Main as the ultimate detail).
- A package cannot nest folders under `R/`, so mark each file's layer with a filename prefix (`domain-`, `io-`), as the block below does.

```clean-architecture
layer domain   = R/domain-*.R
layer adapters = R/io-*.R
layer main     = _targets.R
```

## Enforce

- lintr, including `cyclocomp_linter` (flags a function past a cyclomatic-complexity threshold) and `object_length_linter` (flags an overlong name).
- `R CMD check` (or `devtools::check()`) in CI: it catches a missing `NAMESPACE` export or an undeclared dependency that lintr does not see.
- `covr::package_coverage()` where the project tracks test coverage.

## Smells

- `setwd()` anywhere in package or shared script code — it mutates a global every other piece of code in the session then relies on (G18).
- `library()` inside a function body instead of `DESCRIPTION`'s `Imports` — the dependency stays invisible until the function runs (G22).
- `rm(list = ls())` at the top of a script, masking what the script actually depends on from its environment (G18).
- `attach()`, which puts a data frame's columns on the search path and silently shadows same-named variables (G13).
- `T`/`F` used as boolean literals instead of `TRUE`/`FALSE` (N4).
