# Go

> Applies to: Go 1.22 and later (current stable 1.27). Formatter: gofmt, goimports. Linter: golangci-lint v2. Read with: the framework pack, if any.

## Names

- Case marks visibility: MixedCaps (exported) or mixedCaps (unexported); never underscores (N3, G24).
- Keep package names short, lowercase, and single-word; never `util`, `common`, or `base` (G17).
- Never stutter the package name inside an exported identifier: `user.New`, not `user.NewUser` (N6).
- Name a single-method interface for the behavior it grants, with an `-er` suffix (`Reader`, `Notifier`), never an `I` prefix (`IReader`) (N1, N6).
- Keep a method's receiver name short (one or two letters) and identical across every method of that type (N5).
- Never prefix a getter with `Get`: name it for the value it returns (`Owner`, not `GetOwner`) (N1).
- Never suffix a struct or type with a noise word (`Manager`, `Helper`, `Util`) or name it after a verb (`ProcessOrder`) (N1, G17).
- Never write a vague name (`data`, `info`, `obj`, `ret`) or a bare-verb function with no object (`handle`, `process`); never number or version one instead of replacing it (`user2`, `dataV2`) (N1, N4).

## Functions And Types

- Return early on error or an unmet precondition; keep the success path unindented and last (G6).
- Accept an interface as a parameter, return a concrete struct; declare the interface at the consumer that needs it, never beside the implementation (DIP).
- Keep exported functions to a handful of parameters; past three related values, group them into a struct (F1).
- Never switch behavior on a `bool` parameter; write two functions or a small typed enum instead (F3).
- Use named returns only to document a short function's intent, never to smuggle a late, hidden mutation (G16).
- Guard a type whose zero value is unsafe to use behind a constructor (`NewX`), document the zero value when it is safe.

## Errors

- Wrap with context and keep the cause: `fmt.Errorf("loading order %s: %w", id, err)`.
- Compare with `errors.Is` and extract with `errors.As`; never compare an error's `.Error()` string (G26).
- Return `(T, error)` rather than a sentinel zero value standing in for failure (Special Case pattern).
- Never panic for an expected failure in library code; reserve `panic` for a programmer error the caller cannot act on.
- Check every returned error where it is returned; assigning one to `_` outside a test is a defect, not a shortcut (G4).

## Modules And Visibility

- Default to unexported; export only the names another package must call (G8).
- Put package-private internals under `internal/`, never behind a naming convention alone (G24).
- One directory holds one package; never split a single package's files across unrelated directories.
- State a package's purpose once, in its doc comment; do not restate it per file (C1).

## Placement

- `cmd/<app>/main.go` is the composition root: read configuration, construct dependencies, start — no business rules (G17).
- Keep `<name>_test.go` beside the file it tests; a test belongs to the unit it exercises.
- Never add to a `utils` or `common` package; name the concept the code implements (G17).
- Mirror the module's existing layout (`internal/`, `pkg/`, or flat) instead of introducing a second convention (G11).

## Tests

- Write table-driven tests with `t.Run(tt.name, func(t *testing.T) {...})`; name each case for behavior, not the input shape.
- Call `t.Helper()` in every test helper so a failure reports the caller's line.
- Run with `-race` whenever a test touches a goroutine or shared state; a flake there is a bug to fix, not noise to rerun (G3).
- Reach for `t.Parallel()` only once a test's fixtures are verified independent of its siblings'.

## Concurrency

- Give every goroutine an owner for its shutdown; never start one with `go func() { ... }()` and no way to wait for or cancel it.
- Take `context.Context` as the first parameter and check `ctx.Done()`/`ctx.Err()` on any path that can block.
- Use `errgroup.Group` for goroutines that share a lifetime and must fail together, rather than a `sync.WaitGroup` plus a hand-rolled error slice.
- The sender closes a channel, never the receiver; closing one with a live sender still writing to it panics.
- Since Go 1.22 each `for` iteration owns its own loop variables; add a `v := v` capture only when the module still targets an older Go version.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Domain packages import nothing from `net/http`, a database driver, or a web framework (the Dependency Rule).
- Declare a port as a small interface in the package that consumes it; the adapter package implements it, never the reverse.
- `cmd/<app>/main.go` is the only place that constructs an adapter, injects it into the domain or application layer.

```clean-architecture
layer domain      = internal/domain/**
layer application = internal/service/**
layer adapters    = internal/adapters/**, internal/repository/**
layer main        = cmd/**
```

## Enforce

- golangci-lint v2 (`.golangci.yml`, `version: "2"`): enable `gocyclo`/`gocognit` for complexity, `funlen` for size, `errcheck` for ignored errors, `revive` for naming and style, `depguard` to forbid disallowed imports.
- `go-arch-lint` (`.go-arch-lint.yml`) to enforce declared component boundaries by import path.
- `gofmt -l` and `goimports -l` in CI; a file either would change is a failing check, not a style nit.
- `go vet ./...` and `go test -race ./...` on every change that touches concurrency.

## Smells

- A `util` or `common` package that keeps absorbing unrelated helpers (G17).
- Package-level mutable state read or written from more than one goroutine (G18).
- An `init()` that reaches out to a database, file, or network instead of only registering something (G18).
- A `context.Context` stored on a struct field instead of threaded through as a parameter (G31).
- An error compared by its formatted string instead of `errors.Is`/`errors.As` (G26).
- A wide interface declared next to its one implementation, instead of the small one its consumer needs (G8, ISP).
