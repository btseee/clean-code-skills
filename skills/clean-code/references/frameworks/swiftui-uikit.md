# SwiftUI And UIKit

> Applies to: SwiftUI with the Observation framework (iOS 17 / macOS 14 / watchOS 10 / tvOS 17 and later) alongside UIKit. Language pack: `languages/swift.md`. Read with: nothing.

## Structure

- `Sources/<App>/<Feature>/` — a SwiftUI feature's view and view model together; or `Views/` plus `ViewModels/` when the project splits by kind. A view model is recognized by name, not by folder.
- `Sources/<App>/Controllers/` — UIKit `UIViewController` subclasses, one screen per file.
- `Sources/<App>/Coordinators/` — navigation flow: the only types constructing and presenting screens.
- `Sources/<App>/Services/` — networking and persistence, behind protocols the domain declares.
- `Sources/<App>/Models/` — plain domain types shared by views, view models, and services.
- `<App>App.swift` — the `@main` `App` entry: composition only, no business rules.

## Roles

```clean-roles
role view = **/Views/**
signal view [swift] = struct\s+\w+\s*:\s*(?:[\w, ]*\b)?View\b
role view-model = **/ViewModels/**
name view-model [swift] = ViewModel$
role view-controller = **/Controllers/**
signal view-controller [swift] = :\s*UI\w*ViewController\b
name view-controller [swift] = ViewController$
role coordinator = **/Coordinators/**
name coordinator [swift] = Coordinator$
```

## Rules

- Keep a view a pure function of its state: read from its view model or `@State`, and never call a service or hit the network directly from a `View`'s `body` (G17).
- Name a `ViewModel`, `ViewController`, and `Coordinator` with those exact suffixes; suffix a `View` only where the project's other views already do.
- Make every `@Observable` view model `@MainActor`, explicitly or through the module's default actor isolation, so its state only changes on the main actor.
- Inject a view model's dependencies through its initializer; share a value across many views through the SwiftUI environment, never through a singleton.
- Own navigation in one coordinator or the platform's state (`NavigationStack` path, `UIViewController` push/present); a view never instantiates the next screen (G17).
- Bridge the two UI kits at the edge only, through `UIViewControllerRepresentable` or `UIHostingController`; never let a view's logic import UIKit types.
- Keep a `UIViewController` thin: delegate decisions to a view model or service it owns, so it has one reason to change (G30).
- Start a view model's work from `.task`/`.refreshable` in SwiftUI or a lifecycle method's action in UIKit; never start async work inside an initializer.

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Views, view models, view controllers, and coordinators are the delivery layer: render, adapt, and route, and hold no business rules (the Dependency Rule).
- Business rules live in plain Swift types importing neither SwiftUI nor UIKit; a view model reaches them through a protocol the domain declares.
- A service implements the protocol the domain or application layer declares; a view or view model never imports `URLSession` or a persistence framework.
- Compose services into view models in one place — the `App` entry or a coordinator's initializer — never scattered across views.
- The block below keeps every layer in one app target; files in one Swift module never import each other, so `check_boundaries.py` cannot check it: split the layers into SwiftPM targets (see the Swift pack) to get the check, or rely on the SwiftLint rules under Enforce.

```clean-architecture
layer domain      = Sources/*/Models/**
layer application = Sources/*/ViewModels/**
layer services    = Sources/*/Services/**
layer ui          = Sources/*/Views/**, Sources/*/Controllers/**, Sources/*/Coordinators/**
layer main        = Sources/*/*App.swift
```

## Tests

- Test a view model's behavior without instantiating a SwiftUI view or the view hierarchy.
- Host or snapshot a `View` only for rendering regressions; assert business behavior through its view model.
- Give a `UIViewController` a way to test its logic without the lifecycle: extract decisions into an injectable collaborator the test calls.
- Fake the network and persistence behind the same protocol the view model or controller depends on; never let a test reach a real server.

## Enforce

- SwiftLint `custom_rules` scoped to `Views/`, matching `import` lines for networking or persistence frameworks, to keep I/O out of views.
- Xcode's "Treat Warnings as Errors" plus the module's Swift 6 strict-concurrency setting.
- A `#Preview` on every view as a compile-time check that it constructs from sample data.

## Smells

- A view's `body` doing I/O or heavy computation on every render instead of delegating to a view model (G17, G30).
- `ObservableObject`/`@Published` reintroduced beside `@Observable` view models in the same feature, running two observation models (G11).
- A `UIViewControllerRepresentable`/`UIViewRepresentable` wrapper carrying business logic instead of bridging (G17).
- A closure or delegate held strongly for a `UIViewController`'s lifetime, keeping it alive after dismissal.
- A coordinator or view model reaching back into a view's internals instead of exposing state and intents (G36).
