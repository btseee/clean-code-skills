# Shell

> Applies to: Bash 4+ and POSIX-compliant sh. Formatter: shfmt. Linter: ShellCheck. Read with: nothing.

## Names

- Name functions and locals `snake_case`; reserve `UPPER_SNAKE_CASE` for exported or readonly globals (`CONFIG_PATH`) so scope is visible at a glance (N3).
- Prefix a sourced library's private functions with the library's name (`_mylib_parse_args`); shell has no real module privacy (G8).
- Name a function for the action it performs (`deploy_release`, never `do_stuff` or `run2`); never a bare `data`/`tmp` for a variable holding one thing (N1, G20).
- Never encode a type into a name (`str_path`, `int_count`) (N6); never leave a rename half-done with `_v2`, `_old`, or `_final` (N1, N4).
- Keep a name that short only for a loop index (`for i in`) or a shell idiom (`$#`, `$?`); name anything read later on (N5).

## Functions And Types

- Wrap logic in functions and call them from one `main "$@"` at the bottom; nothing but definitions runs at the top level (G30).
- Declare every function-local with `local` (`local -r` when it never changes); an undeclared variable leaks into the caller's scope (G18).
- Mark a value that must not change `readonly` right after it is set.
- Keep a function to one job; parsing arguments, doing the work, and printing a report is three functions (G30).
- Pass data through arguments and exit status, not through a global a sibling function set earlier (G31).

## Errors

- Start every Bash script with `set -euo pipefail` unless a command's failure needs inspecting; document why when turning a flag off for one line.
- Write user-facing errors to stderr (`echo "error: ..." >&2`) and exit with a distinct, documented code per failure class; never let a script fail silently with exit 0.
- Check every command whose failure matters, including `cd` and `mkdir`; `set -e` does not catch a failure inside `if`, `&&`/`||`, or a non-last pipeline stage without `pipefail`.
- Use `trap 'cleanup' EXIT` (and `INT`/`TERM` when the script holds a lock or a temp file) so cleanup runs on every exit path.
- Never swallow a failure with `2>/dev/null` alone; redirect, then act on the exit status, or let the error surface (G4).

## Modules And Visibility

- Keep reusable functions in `lib/*.sh`, loaded with `source` (G5).
- Guard a sourced library against double-sourcing (`[[ -n "${MYLIB_SOURCED:-}" ]] && return`).
- Never `export` a variable a sourced library does not document as its interface; keep the rest local to the sourcing script.

## Placement

- Keep one script per operational task; when unrelated subcommands accumulate, split the script or add a real subcommand dispatcher.
- Put shared functions in `lib/`, entry points in `bin/` or the project root — whichever the project already uses; never duplicate a helper across scripts (G17).
- Keep generated or vendored scripts out of the directories you hand-edit.

## Tests

- Test with bats-core or ShellSpec; guard `main "$@"` behind `[[ "${BASH_SOURCE[0]}" == "${0}" ]]` so a test can load its functions without running it.
- Assert on exit status and stdout/stderr, not on incidental formatting; use real temp directories, cleaned up in teardown (F.I.R.S.T.).
- Add a test for every argument-parsing edge case and every past incident: a missing argument, an unwritable path, a missing dependency on `PATH` (T5, T6).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Treat the script as a Humble Object: argument parsing, environment setup, and orchestration only; once it needs a real data structure, a retry policy, or a shared business rule, move that logic to the system's main language, called from the script.
- Past a couple hundred lines, or the first time an associative array models more than a lookup table, move that logic out; a shell script is glue, not an application.
- Keep no dependency-injection wiring: shell has none of the tooling to enforce the Dependency Rule, so keep the script small enough that the question does not arise.

## Enforce

- ShellCheck in CI on every script (`git ls-files '*.sh' | xargs shellcheck`) as a build failure, not a suggestion; disable one code only with a comment saying why (`# shellcheck disable=SC2064 # trap must expand now`).
- `shfmt -d` in CI so formatting never bikesheds a review; run `shfmt -w` locally before committing.
- Pin the dialect per file when the project mixes Bash and POSIX sh (`# shellcheck shell=sh`).

## Smells

- An unquoted expansion (`$1`, `$var`, `$@` instead of `"$@"`) that breaks on a space, a glob character, or an empty value (G3).
- Parsing `ls`, or any column-formatted command output, instead of `find`, a glob, or a tool with stable output (G26).
- `eval`, or a command built as a string and piped to `sh -c`, where a plain array or a function call would do (G16).
- Backticks instead of `$(...)` for command substitution (G24).
- An unchecked `cd` — a failed one leaves later commands running against the wrong files (G3).
- A script hundreds of lines long with no functions and no `main`, that nobody wants to touch (G6, G12).
