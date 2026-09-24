# Rust

> Applies to: editions 2021 and 2024 (rustc 1.85+). Formatter: rustfmt. Linter: Clippy. Read with: nothing.

## Names

- Use `snake_case` for functions, variables, and modules; `UpperCamelCase` for types, traits, and enum variants; `SCREAMING_SNAKE_CASE` for constants and statics (N3).
- Wrap a primitive in a newtype to name the invariant it carries (`struct OrderId(String)`), instead of passing a bare `String` or `u64` everywhere (G26).
- Name a trait for the capability it grants (`Cache`, `Clock`); never with an `I`- prefix or `Trait` suffix (N6).
- Give every enum variant a name that reads as a state (`Shipped { at: Timestamp }`), not a flag hiding inside a struct (F3).
- Never write a vague name (`data`, `info`, `item`, `temp`) or a bare-verb function with no object (`handle`, `process`); a loop index, closure parameter, or `_` for a discarded value may stay short, nothing else should (N1, N5).
- Never number or version a name instead of replacing it (`user2`, `_old`); never suffix a type with a noise word (`Manager`, `Helper`, `Util`) or name it after a verb (`ProcessOrder`) (N1, N4, G17).

## Functions And Types

- Model a closed set of states as an `enum`, not a struct with a `status: String` field and scattered booleans (G26, J3).
- Borrow (`&T`, `&mut T`) by default; clone only where ownership must move, or the type is `Copy` and cheap.
- Return `Result<T, E>` for a recoverable failure and propagate it with `?`; reserve `panic!` for a broken invariant the type system should prevent.
- Keep a function's parameter count small; past three related values, group them into a struct (F1).
- Implement `From`/`TryFrom` for a conversion instead of a same-named `to_x`/`from_x` free function per type pair (G11).

## Errors

- Define a library's errors as an enum with `#[derive(thiserror::Error)]`, one variant per distinguishable cause, implementing `std::error::Error`.
- In a binary, collect errors with `anyhow::Result` and `.context("...")`; do not invent a parallel enum the binary never matches on.
- Never call `.unwrap()` or `.expect()` on a path reachable from library code; return the `Result`/`Option` to the caller instead (G4).
- Preserve the source error with `#[source]` or `.context(...)`; never format it away into a plain `String` (G26).
- Model an expected absence as `Option<T>` or a dedicated variant, not a sentinel value (Special Case pattern).

## Modules And Visibility

- Default every item to private; use `pub(crate)` for cross-module use inside the crate, `pub` only for the crate's real public surface (G8).
- Give each concept its own module under `src/`, re-exported from `lib.rs`; do not mirror folders into a `mod` tree nobody reads.
- Keep a trait beside the module that owns its concept; put a second implementation (a test double, an alternate backend) in its own module.

## Placement

- Split a multi-purpose binary into workspace crates along actor lines — a domain crate, an application crate, adapter crates — never one crate that several teams edit for unrelated reasons (SRP).
- Keep `src/main.rs` or `src/bin/*.rs` thin: parse arguments, build the dependency graph, run.
- Never add a catch-all `utils.rs` or `helpers.rs`; name the module for the concept it implements (G17).

## Tests

- Put unit tests beside their code in `#[cfg(test)] mod tests`; put tests of the public API under `tests/`.
- Name a test for behavior it proves (`rejects_empty_input`), and assert on `Result`/`Option` values with a pattern match, not `.unwrap()` on the tested path.
- Reserve `#[should_panic]` for a genuine panic contract; never use it to paper over an untested `Result` path.

## Concurrency

- Prefer message passing (`std::sync::mpsc`, `tokio::sync::mpsc`) over a shared `Mutex<T>` when ownership can move instead.
- Push blocking or CPU-heavy work into `tokio::task::spawn_blocking`; never call blocking I/O from an async task on the runtime's worker threads.
- Scope a `Mutex`/`RwLock` guard as narrowly as possible; never hold one across an `.await`.
- Treat an `Rc<RefCell<T>>` or `Arc<Mutex<T>>` reachable from many owners as a design smell to resolve, not a default to reach for (G13).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- The domain crate names no I/O dependency in its `Cargo.toml`: no HTTP client, database driver, or async runtime (the Dependency Rule).
- Declare ports as traits in the domain or application crate; adapter crates implement them, path dependencies point outward-to-inward only.
- The binary crate is the composition root: the only place that names a concrete adapter type.

```clean-architecture
layer domain      = crates/domain/**
layer application = crates/application/**
layer adapters    = crates/adapters/**
layer main        = crates/cli/**, src/main.rs
```

## Enforce

- Clippy's `too_many_arguments` runs by default; `cognitive_complexity` (nursery group) and `unwrap_used` and `expect_used` (restriction group) run only once enabled, for example via `[workspace.lints.clippy]` in the workspace `Cargo.toml`.
- Allow them in test code with `clippy.toml`'s `allow-unwrap-in-tests = true` and `allow-expect-in-tests = true`, rather than disabling the lints crate-wide.
- `cargo deny check` (`deny.toml`) for license, advisory, banned-crate, and source policy.
- `cargo fmt --check` and `cargo clippy --all-targets -- -D warnings` in CI.

## Smells

- `.clone()` reached for to silence a borrow-checker error instead of restructuring ownership (G21).
- An error carried as a `String` instead of a typed enum, leaving callers only a text match (G26, N1).
- An `Rc<RefCell<_>>` (or `Arc<Mutex<_>>`) web threaded through modules that do not otherwise share state (G13).
- `unsafe` with no `// SAFETY:` comment naming the invariant that makes it sound (G4).
- A trait with every method `pub` and only one implementation, built "just in case" (G8).
