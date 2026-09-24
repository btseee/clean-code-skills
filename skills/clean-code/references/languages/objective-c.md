# Objective-C

> Applies to: modern Objective-C with ARC, on current Xcode/Clang. Formatter: clang-format. Linter: Clang Static Analyzer (`scan-build` or Xcode's Analyze). Read with: nothing.

## Names

- Follow Cocoa naming: lowerCamelCase verb phrases with labeled parameters for methods (`loadFeedWithCompletion:`), PascalCase nouns for classes, and your project's two- or three-letter prefix on every class, protocol, category, and free C function — platform convention, not an N6 encoding (N3).
- Prefix category and extension method names too; an unprefixed category on a class you do not own can silently override another library's method (G13).
- Name a `BOOL` property as an assertion (`isLoading`, `hasError`); name a delegate method with the sender first (`tableView:didSelectRowAtIndexPath:`); name a class extension's private members as clearly as public ones.
- Never name a variable or property `data`, `info`, `obj`, or `temp`/`tmp`, or a method with no object like `handle:`/`doStuff` (N1); keep a name that short only for a loop index or block argument (N5).
- Never carry a Hungarian-style tag into a name (`strName`, `pFoo`, `bEnabled`) (N6), or leave a rename half-done with `_v2`, `_new`, `Old`, `Copy`, or `Final` (N1, N4).
- Never suffix a class `Manager`, `Helper`, `Util(s)`, `Info`, or `Data` when it does one job, and never name a class for a verb like `ProcessOrder`/`HandleLogin` — a class is a noun (N1, G17).

## Functions And Types

- Declare property memory semantics: `nonatomic` unless the class is thread-safe by atomicity, `copy` for `NSString`/`NSArray`/blocks, `weak` for delegates and back-references (G26); type collections with lightweight generics (`NSArray<Item *> *`, not bare `NSArray *`) so the compiler and Swift callers see the element type.
- Keep a method to one task; split a `configure` method that also fetches and formats into named steps (G30).
- Prefer immutable value classes for simple data; expose a mutable copy only where mutation is the point.

## Errors

- Report a recoverable failure through an `NSError **` out parameter and `BOOL`/`nil` return, never a thrown exception.
- Reserve `@throw`/`NSException` for programmer errors — an out-of-bounds index, a violated precondition — that should crash in development, never network or disk failures (Special Case pattern).
- Populate `NSError` with a domain, code, and `NSLocalizedDescriptionKey`; never return failure with a `nil` error and no explanation (G3).
- Treat a non-nil `NSError *` beside reported success as untrustworthy; check it only after the return value says failure.

## Modules And Visibility

- Wrap public headers in `NS_ASSUME_NONNULL_BEGIN`/`NS_ASSUME_NONNULL_END`; annotate exceptions with `nullable`, and leave the trailing `NSError **` alone — convention treats it as nullable.
- Expose in the `.h` only what other classes call; keep the rest — `@interface Foo ()` extensions — in the `.m` (G8).
- Give every class, protocol, category, and free function your project's prefix (G13).
- Use `NS_SWIFT_NAME`/`NS_REFINED_FOR_SWIFT` to keep the Swift-facing API idiomatic, not a literal transliteration.

## Placement

- Mirror Xcode's group structure on disk; one class per `.h`/`.m` pair, named after the class.
- Keep model classes free of `UIKit`/`AppKit` imports; a model that formats itself for display has taken the view's job (G17).
- Put a category in its own `<Class>+<Purpose>.m` file, never folded into an unrelated file.
- Never add to a shared `Helpers.m`/`Utilities.m`; name the concept the new code adds (G17).

## Tests

- Use XCTest; name a test method `test<Behavior>` and assert outcomes, never internal ivars.
- Give asynchronous work an `XCTestExpectation` with a timeout; never poll or sleep for completion.
- Test a model or service in isolation from `UIKit`; drive a view controller through an injected collaborator, not `viewDidLoad`.

## Concurrency

- Dispatch UI updates on the main queue (`dispatch_async(dispatch_get_main_queue(), ...)`) or the main `NSOperationQueue`; never touch a view off it.
- Capture `self` weakly in a block outliving the current scope (`__weak typeof(self) weakSelf = self;`), and re-strengthen it inside before use, to avoid a retain cycle (G31).
- Give one serial `dispatch_queue_t` ownership of mutable state instead of ad hoc locks.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Model classes never import `UIKit`/`AppKit`; a view controller maps a model to the view's needs, not the reverse (the Dependency Rule).
- Declare a service's contract as a `@protocol` beside the model that needs it; keep the concrete network/disk class outside that model layer.
- Wire concrete services into consumers at one composition point (app/scene delegate, or a small factory), never inside a view controller.

```clean-architecture
layer model   = **/Model/**, **/Models/**
layer service = **/Services/**
layer ui      = **/Controllers/**, **/Views/**
layer main    = **/AppDelegate.m, **/SceneDelegate.m
```

## Enforce

- clang-format with the project's `.clang-format`, run in CI rather than by hand.
- Clang Static Analyzer (`scan-build`, or Xcode's Analyze) as a build gate: fix or suppress a finding, never leave it unresolved (G4).
- `-Wall -Werror` (or the project's warning set) plus `-Wnullable-to-nonnull-conversion`, all treated as errors, so a new warning fails the build, not just the log (G4).

## Smells

- A massive view controller doing networking, parsing, and layout at once (G30).
- A block or delegate property declared `strong` where `copy` (blocks) or `weak` (delegates) is the convention, risking a retain cycle (G26).
- A category on a Foundation or UIKit class without your project's prefix (G13).
- A public header missing `NS_ASSUME_NONNULL_BEGIN`, so every pointer reads as implicitly unwrapped from Swift.
- An `NSError **` out parameter left unpopulated on a reported failure (G3).
