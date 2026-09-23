# Java

> Applies to: Java 21 LTS and 25 LTS. Formatter: google-java-format or Spotless. Linter: Checkstyle, PMD, SpotBugs, and Error Prone. Read with: the framework pack, if any.

## Names

- PascalCase for classes, interfaces, records, and enums; camelCase for methods, fields, and locals; `UPPER_SNAKE_CASE` only for `static final` constants (N3).
- Name an interface for the role it promises (`PaymentGateway`), never with an `I` prefix; name the implementation for what it is (`StripePaymentGateway`), never `PaymentGatewayImpl` (N6).
- Name a package for the domain concept it holds, lowercase, no underscores; a package named `util`, `common`, or `misc` means nothing inside it has a real home yet (G17).
- Phrase boolean fields and methods as questions (`isClosed`, `hasPendingCharge`); never give a query and the command that changes its answer the same name (N7).

## Functions And Types

- Keep methods short and at one level of abstraction; extract a private method instead of a comment marking a step (G30, G34).
- Use a record for an immutable data carrier; give it a compact constructor only to validate an invariant, never to add behavior that belongs to another class.
- Model a closed set of alternatives as a `sealed` interface and switch over it with exhaustive pattern matching; the compiler rejects a missing case instead of a reader missing it (G23).
- Return `Optional<T>` only from a method whose caller must handle absence; never accept `Optional` as a parameter, store one in a field, or wrap a collection in it — return an empty collection instead.
- Hand back collections as immutable views (`List.copyOf`, `Collections.unmodifiableList`) once they leave the class that owns them, so no caller can mutate state behind your back (F2).
- Wire dependencies through the constructor onto `final` fields; a class built by its constructor cannot exist half-initialized, and a test can construct it with no container (DIP).

## Errors

- Throw unchecked exceptions from a domain base (`class AccountException extends RuntimeException`); a checked exception forces every intermediate signature to change, so the failure detail leaks into signatures that have nothing to do with it (Checked vs unchecked exceptions).
- Always chain the cause (`throw new PaymentDeclinedException("card declined", cause)`); never leave a `catch` block empty (G4).
- Model an expected alternate outcome — not found, declined, empty — as a return value, not an exception; reserve exceptions for genuine failures (Special Case pattern).
- Open and release a resource with try-with-resources; never call `close()` by hand in a `finally` block.
- Catch the narrowest type a call can actually throw; catching `Exception` or `Throwable` to satisfy the compiler hides the bug it should have surfaced (G4).

## Modules And Visibility

- Default every class, method, and field to package-private; widen to `public` only what another package must call (G8).
- Where the project defines a JPMS module, `exports` only the packages other modules use, and leave implementation packages unexported.
- Never expose a mutable field or a live reference to internal state; return a copy or an immutable view instead.
- Keep one public top-level type per file, named for that type.

## Placement

- In new code, package by feature (`order/`, `payment/`) rather than by technical layer at the root (`controllers/`, `services/`): a feature's classes change for the same reasons and belong together (CCP). An established layer-package layout still wins.
- Keep a package's exported API to the types other packages need; helper classes stay package-private.
- Put a test in the mirrored `src/test/java` tree, same package as the class it tests, named `<Type>Test`.
- Never add a method to a `Utils` or `Helpers` class; name the concept the static methods express, or make it an instance a caller injects (G17).

## Tests

- Use JUnit 5 (`@Test`, `@ParameterizedTest`, `@Nested`) with AssertJ's fluent assertions; assert the outcome, never the internals.
- Name a test for the behavior it proves (`closesWhenBalanceIsZero`), not the method it calls.
- Run an integration test against a real dependency with Testcontainers instead of an in-memory fake standing in for a database, queue, or external service.
- Cover boundary values, and add a regression test beside any bug you fix (T5, T6).

## Concurrency

- Prefer virtual threads (`Executors.newVirtualThreadPerTaskExecutor()`) for blocking, I/O-bound work instead of a hand-sized platform-thread pool; keep CPU-bound work on a platform-thread pool.
- Never pool or reuse a virtual thread, and never cache one in a field; they are meant to be created per task and discarded.
- Confine mutable state to one thread, or guard it explicitly; prefer immutable objects and `java.util.concurrent` collections to synchronizing a collection yourself (Segregation of mutability).
- Never synchronize on `this` or on a class object shared with unrelated code; lock a private, dedicated object.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Business rules import nothing from a web, persistence, or messaging framework's package (the Dependency Rule).
- Declare a port as a plain interface beside the policy that needs it; the adapter package implements it and is named for the technology, never the reverse.
- Wire interfaces to implementations in one composition root — a `Main` class or the framework's own configuration classes — never inside a domain type.

```clean-architecture
layer domain      = src/main/java/**/domain/**
layer application = src/main/java/**/application/**
layer adapters    = src/main/java/**/adapter*/**
layer main        = src/main/java/**/*Main.java, src/main/java/**/config/**
```

## Enforce

- google-java-format or Spotless in CI so formatting is never a review comment.
- Checkstyle `MethodLength`, `ParameterNumber`, and `CyclomaticComplexity` to catch an oversized or overloaded method before a human has to say so.
- PMD and SpotBugs for dead code, unused fields, and known bug patterns; Error Prone at compile time for mistakes `javac` lets through.
- ArchUnit `layeredArchitecture()` for declared layers and `slices().matching("..(*)..").should().beFreeOfCycles()` for package cycles, run as ordinary JUnit 5 tests.

## Smells

- A god service that has accumulated every rule in the module because it was already open; split by responsibility before adding to it (G17, SRP).
- An anemic model: getters and setters with no behavior, while a service reaches in to do the object's own job for it (data/object anti-symmetry).
- A static utility class collecting unrelated helpers under a name like `Utils` (G17, G12).
- A method returning `null` instead of `Optional`, an empty collection, or a Special Case object, pushing a null check onto every caller (Special Case pattern).
- Field injection — a dependency-injection annotation on a field instead of a constructor parameter — hiding what a class actually depends on from its own tests (DIP).
- A checked exception whose `throws` clause has spread across a dozen call sites because nothing wraps it at the boundary (Checked vs unchecked exceptions).
