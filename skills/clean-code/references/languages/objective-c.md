# Objective-C

> Applies to: modern Objective-C with ARC, on current Xcode/Clang. Formatter: clang-format. Linter: Clang Static Analyzer (`scan-build` or Xcode's Analyze). Read with: nothing.

## Names

- Follow Cocoa naming: verb phrases for methods (`loadFeedWithCompletion:`), nouns for classes, and a two- or three-letter prefix on every class, protocol, category, and free C function your project owns (N3).
- Prefix category and extension method names too; an unprefixed category on a class you do not own can silently override another library's method (G13).
- Name a `BOOL` property as an assertion (`isLoading`, `hasError`); name a delegate method with the sender first (`tableView:didSelectRowAtIndexPath:`).
- Keep a private class extension's ivars and methods named clearly enough that no reader mistakes them for public API.

## Functions And Types

- Declare every property's memory semantics explicitly: `nonatomic` unless the class is deliberately thread-safe by atomicity, `copy` for `NSString`, `NSArray`, and block-typed properties, `weak` for delegates and other back-references (G26).
- Declare Foundation collection properties and parameters with lightweight generics (`NSArray<Item *> *`, not bare `NSArray *`), so the compiler and any Swift caller both see the element type.
- Put private methods and ivars in a class extension (`@interface Foo ()`) in the `.m` file; never expose them in the public header (G8).
- Keep a method to one task; split a `configure` method that also fetches and formats into named steps (G30).
- Prefer immutable value classes for simple data; expose a mutable copy only where mutation is genuinely the point.

## Errors

- Report a recoverable failure through an `NSError **` out parameter and a `BOOL`/`nil` return; never mix a thrown exception into a normal failure path.
- Reserve `@throw`/`NSException` for programmer errors — an out-of-bounds index, a violated precondition — that should crash in development, never for network or disk failures (Special Case pattern).
- Populate the `NSError` with a domain, a code, and `NSLocalizedDescriptionKey`; never return failure with a `nil` error and no explanation (G3).
- Treat a non-nil `NSError *` alongside a reported success as untrustworthy; check the error only after the method's return value says it failed.

## Modules And Visibility

- Wrap every public header in `NS_ASSUME_NONNULL_BEGIN`/`NS_ASSUME_NONNULL_END`; annotate each exception explicitly with `nullable`, and leave the trailing `NSError **` alone — the convention already treats it as nullable.
- Expose in the `.h` only what other classes call; keep everything else in a class extension in the `.m` (G8).
- Give every class, protocol, category, and free function your project's prefix; an unprefixed category on a Foundation class is a standing collision risk (G13).
- Use `NS_SWIFT_NAME`/`NS_REFINED_FOR_SWIFT` to keep the Swift-facing API idiomatic instead of a literal transliteration.

## Placement

- Mirror Xcode's group structure to the filesystem; one class per `.h`/`.m` pair, named after the class.
- Keep model classes free of `UIKit`/`AppKit` imports; a model that formats itself for display has taken on the view's job (G17).
- Put a category in its own `<Class>+<Purpose>.m` file, never folded into an unrelated file.
- Never add to a shared `Helpers.m`/`Utilities.m`; name the concept the new code actually adds (G17).

## Tests

- Use XCTest; name a test method `test<Behavior>` and assert outcomes, never internal ivars.
- Give asynchronous work a real `XCTestExpectation` with a timeout; never poll or sleep for completion.
- Test a model or service in isolation from `UIKit`; drive a view controller's logic through an injected collaborator, not through `viewDidLoad`.

## Concurrency

- Dispatch UI updates on the main queue (`dispatch_async(dispatch_get_main_queue(), ...)`) or the main `NSOperationQueue`; never touch a view from a background queue.
- Capture `self` weakly in a block stored beyond the current scope (`__weak typeof(self) weakSelf = self;`), and re-strengthen it inside the block before use, to avoid a retain cycle (G31).
- Give one serial `dispatch_queue_t` ownership of a piece of mutable state instead of guarding it with ad hoc locks.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Model classes never import `UIKit`/`AppKit`; a view controller maps a model to what the view needs, not the other way round (the Dependency Rule).
- Declare a service's contract as a `@protocol` beside the model that needs it; the concrete class doing network or disk access lives outside that model layer.
- Wire concrete services into their consumers in one composition point (the app or scene delegate, or a small factory), never inside a view controller.

```clean-architecture
layer model   = **/Model/**, **/Models/**
layer service = **/Services/**
layer ui      = **/Controllers/**, **/Views/**
layer main    = **/AppDelegate.m, **/SceneDelegate.m
```

## Enforce

- clang-format with the project's `.clang-format`, run in CI rather than by hand.
- Clang Static Analyzer (`scan-build`, or Xcode's Analyze) as a build gate: fix or explicitly suppress a finding, never leave it silently unresolved (G4).
- `-Wall -Werror` (or the project's warning set) so a new warning fails the build, not just the log (G4).
- `-Wnullable-to-nonnull-conversion` enabled and treated as an error.

## Smells

- A massive view controller doing networking, parsing, and layout at once (G30).
- A block property or delegate reference declared `strong` where `copy` (blocks) or `weak` (delegates) is the convention, risking a retain cycle (G26).
- A category on a Foundation or UIKit class without your project's prefix (G13).
- A public header missing `NS_ASSUME_NONNULL_BEGIN`, so every pointer reads as implicitly unwrapped from Swift.
- An `NSError **` out parameter left unpopulated on a reported failure (G3).
