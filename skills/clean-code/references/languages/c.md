# C

> Applies to: C11, C17, and C23. Formatter: clang-format. Linter: clang-tidy and cppcheck. Read with: nothing.

## Names

- Prefix every public symbol with its module name (`list_push`, `list_free`): C has no namespaces, so the prefix is the namespace (N3, G11).
- Use snake_case for functions and variables, `UPPER_SNAKE_CASE` for macros and constants; follow the project's typedef convention (`_t` suffix or none) — never invent a second one (N3).
- Name booleans as questions (`is_empty`) using `<stdbool.h>`'s `bool`, never a plain `int` flag (N7).
- Never abbreviate past what a reader can expand from context alone, or add a Hungarian type prefix (`iCount`, `pFoo`) — the type is already in the declaration (N1, N6).
- Never write a vague name (`data`, `tmp`, `ret`, `val`) or a bare-verb function with no object (`handle_it`, `process`); never number or suffix one instead of replacing it (`buffer2`, `_final`); a loop index may stay one letter, nothing wider in scope should (N1, N4, N5).

## Functions And Types

- Keep each function to one thing, one abstraction level; extract instead of nesting past two levels (Do One Thing).
- Use fixed-width types from `<stdint.h>` (`int32_t`, `size_t` for sizes/counts) instead of plain `int`/`long` where the width matters (G26).
- Hide a type's layout behind an opaque struct: declare `typedef struct list list_t;` in the public header, define `struct list` only in the `.c` file (data/object anti-symmetry, G8).
- Prefer a `static inline` function over a function-like macro: it is type-checked, scoped, and evaluates its arguments once (G27).

## Errors

- Return a project-wide error enum from every fallible function, check it at every call site; never let a caller discover failure by crashing later (G4).
- Free every resource on every exit path through one `goto cleanup` label per function that owns more than one resource, instead of duplicating release calls (G31):

```c
char *line = NULL;
FILE *file = fopen(path, "w");
if (file == NULL) { status = REPORT_IO_ERROR; goto cleanup; }
if ((line = malloc(REPORT_LINE_MAX)) == NULL) { status = REPORT_NO_MEMORY; goto cleanup; }
status = report_format(report, line, file);
cleanup:
free(line);
if (file != NULL) fclose(file);
```

- Document ownership at allocation — who frees this, and when — instead of leaving it implied (N7).
- Mark a function whose result must not be ignored with C23's `[[nodiscard]]`, or `__attribute__((warn_unused_result))` on older standards where project already uses compiler attributes.

## Modules And Visibility

- Mark every function and file-scope variable `static` unless the public header declares it (G8).
- Treat one `.c`/`.h` pair as one module; the header is that module's entire contract; nothing outside it reaches past that.
- Guard every header with `#pragma once` or a unique include guard, consistently.
- Avoid a mutable file-scope global; where one is unavoidable, make it `static` and name why it exists (G18).

## Placement

- Place each module's `.c` and `.h` beside each other under project's existing source root; never invent a second layout.
- Keep a public header self-contained: it includes what its own declarations need and nothing else.
- Put tests under project's existing test folder, one test file per module.

## Tests

- Use whichever project already depends on — Unity, CMocka, or Check — and never introduce a second (G11).
- Test boundary values for every buffer and width: zero, one, exact capacity, and `SIZE_MAX`/`INT_MAX` (T5).
- Assert on the returned error enum, not only on "did it crash" (F.I.R.S.T. — Self-validating).
- Keep tests independent of run order; never rely on another test's leftover global state (G18).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- The core never `#include`s a framework, database client, or driver header; declare a port as a struct of function pointers in the core, let the detail fill it in (the Dependency Rule).
- `main.c` is the only place that allocates concrete adapters, wires them into the port structs, calls into the core — no business rule lives there (Main as the ultimate detail).

```clean-architecture
layer domain   = src/domain/**
layer adapters = src/adapters/**
layer main     = src/main.c
```

## Enforce

- clang-tidy's `readability-function-size` for oversized functions; cppcheck for the defects clang-tidy does not model.
- Compiler flags `-Wall -Wextra -Werror` always, plus `-fanalyzer` (GCC) for interprocedural bug detection.
- Build the test binary with `-fsanitize=address,undefined` (ASan/UBSan), run it in CI, not only locally.

## Smells

- A function-like macro standing in for a `static inline` function (G27).
- Mutable global or `extern` state written from more than one translation unit (G18).
- `strcpy`, `strcat`, or an unbounded `sprintf` — a boundary defect waiting for a long input (G3).
- `malloc`/`calloc` used without checking for `NULL` before the pointer is dereferenced (G2).
- A returned error enum that the caller never checks (G4).
