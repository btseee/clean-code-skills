# Jetpack Compose

> Applies to: Jetpack Compose on Kotlin 2.x, with the Compose Compiler Gradle plugin (`org.jetbrains.kotlin.plugin.compose`, versioned with Kotlin). Language pack: languages/kotlin.md. Read with: nothing.

## Structure

- `ui/<feature>/` — a feature's composables and its `ViewModel`, together.
- `ui/theme/` — `Color.kt`, `Type.kt`, `Theme.kt`: the design system, no business logic.
- `data/` — repositories and data sources; the single source of truth for each kind of data.
- `domain/usecase/` (optional) — one use case per file, once business rules are shared across ViewModels.
- `di/` — Hilt or Koin modules wiring repositories and use cases into ViewModels.
- `MainActivity.kt` / `<Name>App.kt` — the composition root: sets the theme, hosts navigation.

## Roles

```clean-roles
signal view-model [kt] = :\s*ViewModel\(\)
name view-model = ViewModel$
role use-case = **/usecase/**, **/usecases/**
name use-case = UseCase$
name data-source = DataSource$
signal di-module [kt] = @Module\b
signal component [kt] = @Composable\b
ignore-name = Preview$
```

## Rules

- Hold UI state in the `ViewModel` and expose it as one observable stream (`StateFlow<UiState>` or Compose `State`); the composable reads and renders it (Unidirectional Data Flow).
- Collect that state with `collectAsStateWithLifecycle()`, never plain `collectAsState()`, on a screen that can be backgrounded.
- Never give a `ViewModel` a `Context`, a `View`, or a composable/`Activity` reference; pass what it needs through its constructor or a `SavedStateHandle` (the Dependency Rule).
- Keep composables pure functions of their parameters: no reading a repository, data source, or singleton inside `@Composable` code (G14, G17).
- Name a composable a PascalCase noun for what it renders (`UserAvatar`), a state holder `remember<Thing>()`.
- Hoist state to the lowest common caller that needs it; a composable that owns state its caller needs is the wrong owner for it (G17).
- Use `remember`/`rememberSaveable` for UI-only state (scroll offset, a draft field); anything the app's logic depends on belongs in the ViewModel.
- Use `LaunchedEffect`/`DisposableEffect` only to synchronize with something outside Compose; never to run business rules on every recomposition.
- Model loading, success, and error as a sealed UI-state hierarchy or explicit fields, never a "`null` means loading" convention (G26, Special Case pattern).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Composables and ViewModels are the delivery layer: render and hold UI state; never decide a business rule.
- Repositories implement interfaces the domain or ViewModel layer declares; a ViewModel depends on the interface, never a Room, Retrofit, or DataStore type.
- Confine DI modules and navigation graphs to `di/` and the app's composition root; nothing inward imports Hilt, Koin, or Dagger annotations.

```clean-architecture
layer domain = **/domain/**
layer data   = **/data/**
layer ui     = **/ui/**
layer di     = **/di/**, **/MainActivity.kt
```

## Tests

- Test a `ViewModel` with `runTest` (kotlinx-coroutines-test) and a fake or MockK repository; assert on the UI states, not on the composable.
- Test composable behavior with the Compose UI testing APIs (`createComposeRule`, semantics matchers); never verify a business rule only by driving the UI (F.I.R.S.T.).
- Keep `@Preview` functions out of test scope — documenting a screen, asserting nothing.

## Enforce

- detekt with compose-rules (`mrmans0n/compose-rules`) for Compose-specific checks: unstable parameters, missing `remember`, modifier ordering and reuse.
- Konsist rules asserting ViewModels hold no Android `Context`/`View` type, and `ui/**` composables never import a `data/**` repository.
- Android Lint (`lintDebug` or the project's variant) for platform issues the rules above miss.

## Smells

- A composable injecting or default-constructing a repository or data source (G14, G17).
- `collectAsState()` on a screen-level flow instead of the lifecycle-aware collector, doing work after the screen is backgrounded (G3).
- Business branching — pricing, eligibility, validation — written inside a composable's body (G17, G30).
- A `ViewModel` holding an `Activity`, `Context`, or `NavController` (the Dependency Rule).
- State duplicated between a `remember` block and the ViewModel, drifting out of sync (G5).
