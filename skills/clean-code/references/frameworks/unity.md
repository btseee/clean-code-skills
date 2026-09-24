# Unity

> Applies to: Unity 6 (6000.x); Unity 6.3 LTS is current. Language pack: `languages/csharp.md`. Read with: nothing.

## Structure

- `Assets/_Project/` (or the project's root folder) — the team's code, kept apart from `Assets/Plugins/` and imported packages.
- `Assets/_Project/<Module>/Runtime/` — that module's gameplay scripts and its `.asmdef`; the assembly Unity ships inside every player build.
- `Assets/_Project/<Module>/Editor/` — that module's inspectors, windows, and build tooling, in a sibling `Editor/` folder with its editor-only `.asmdef`; stripped from every player build.
- `Assets/_Project/<Module>/Tests/EditMode/` and `Tests/PlayMode/` — the Unity Test Framework's two suites, each with a test `.asmdef`.
- `Assets/_Project/<Module>/Data/` — `ScriptableObject` configuration and shared-data assets, beside the module they configure.
- `Packages/manifest.json` — the project's package dependencies (Addressables, the Input System, and the rest), resolved by the Package Manager.

## Roles

```clean-roles
role editor = **/Editor/**
signal editor [cs] = :\s*(?:Editor|EditorWindow|PropertyDrawer)\b
signal behaviour [cs] = :\s*MonoBehaviour\b
signal data-asset [cs] = :\s*ScriptableObject\b
```

## Rules

- Keep a `MonoBehaviour` a Humble Object: it wires the scene and forwards lifecycle calls; the rule it applies — damage, scoring, an unlock condition — lives in a plain C# class an EditMode test can `new` up with no scene (Humble Object).
- Cache every `Component`/`GameObject` reference once, in `Awake` or `Start`, or wire it through `[SerializeField]`; never call `GetComponent`, `GameObject.Find`, or a `FindObjectOfType` family method inside `Update`, `FixedUpdate`, or `LateUpdate`.
- `FindObjectOfType`/`FindObjectsOfType` are obsolete: reach for `FindFirstObjectByType`, `FindAnyObjectByType`, or `FindObjectsByType` with a sort mode when a lookup is unavoidable.
- Expose Inspector data with `[SerializeField] private`, never a public field — a public field is a write path from every other script in the project (G8).
- Match the project's convention for serialized-field prefixes (`m_camelCase`, or a leading underscore); that prefix is this ecosystem's idiom, not the N6 encoding smell — never add a third style alongside whichever one is there (G11).
- A Unity object's file name must equal its class name or the Inspector cannot attach it; name the class for the responsibility it holds, then match the file to it — never the reverse.
- Give a `ScriptableObject` behaviorless fields for configuration or shared data; put any decision it seems to want in a plain class or the object that reads it (G17).
- Prefer a `UnityEvent`, a C# `event`, or a callback to a flag polled every `Update`; polling reimplements, one frame late, what the platform reports the moment it happens (G6).
- Keep a singleton only where the project already relies on one; give a new subsystem constructor or `[SerializeField]` injection instead of one more static `Instance` (G18).
- Editor code — custom inspectors, `EditorWindow`s, `PropertyDrawer`s, build scripts — stays inside an `Editor/` folder or an editor-only `.asmdef`: a runtime script referencing `UnityEditor.*` cannot compile outside the Editor, and a `MonoBehaviour`/`ScriptableObject` placed inside `Editor/` is silently stripped from the build it was meant to ship in.
- Once the project uses Addressables, load and release every asset of that kind through it; never mix in a `Resources.Load` for the same asset (G11).
- Once the project uses the Input System package, read input through its generated `InputAction`s; never add a legacy `Input.GetKey`/`GetAxis` call beside them (G11).
- Give each `.asmdef` the narrowest `references` list it needs; a module reading data should not reference the one that renders it (CRP).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- No `MonoBehaviour`, `GameObject`, `Transform`, `Component`, or other `UnityEngine.*`/`UnityEditor.*` type crosses into `domain` or `application`; those layers may use math value types (`Vector3`, `Quaternion`, `Color`) but never a scene-graph or lifecycle type (the Dependency Rule).
- Declare an interface in `domain` or `application` for anything the engine supplies — asset loading, input, save data, wall-clock time — and implement it in `infrastructure` against Addressables, the Input System, or `Application.persistentDataPath`.
- A `ScriptableObject` that only carries values is `infrastructure` configuration; one that decides behavior belongs in `domain` (G17).
- Wire every concrete implementation once, in a bootstrap `MonoBehaviour` or installer in `main`, at scene start; `delivery` scripts receive built dependencies and never construct their own (Main as the ultimate detail).

```clean-architecture
layer domain         = Assets/_Project/**/Domain/**
layer application    = Assets/_Project/**/Application/**
layer infrastructure = Assets/_Project/**/Infrastructure/**
layer delivery       = Assets/_Project/**/Runtime/**
layer main           = Assets/_Project/**/Bootstrap/**
layer editor         = Assets/_Project/**/Editor/**
```

## Tests

- Test a plain C# rule class with the project's .NET runner or the Unity Test Framework's EditMode suite; a pure rule needs no scene, prefab, or Play mode.
- Reserve PlayMode tests for what genuinely needs the engine loop: physics, coroutines, animation timing, scene-load order.
- Give each test assembly its `.asmdef` referencing `nunit.framework.dll` and the assembly under test, so it is never bundled into a player build.
- Never verify a business rule only by pressing Play and reading Inspector values by hand; automate it as an EditMode test (F.I.R.S.T.).

## Enforce

- `Microsoft.Unity.Analyzers` — included in every `.csproj` Unity generates once Visual Studio Tools for Unity is installed, or added by hand from the NuGet package of the same name for CI.
- Assembly-definition `references` as the physical boundary: a `Domain.asmdef` listing no `UnityEngine`/`UnityEditor` reference turns a violation into a compiler error, not a review comment.
- The .NET analyzers and `dotnet format` from `languages/csharp.md`, run against the `.sln` Unity generates.
- JetBrains Rider's Unity support plugin, where the team uses Rider, for more Unity-specific inspections.

## Smells

- Gameplay rules — damage, scoring, an unlock condition — written directly in a `MonoBehaviour`'s `Update` or `OnCollisionEnter`, provable only by pressing Play (G17, Humble Object).
- `GetComponent`, `GameObject.Find`, or `FindObjectOfType` resolved fresh every frame instead of cached once in `Awake`.
- A `MonoBehaviour` or `ScriptableObject` class sitting inside `Editor/` — stripped from player builds, so a runtime reference to it cannot compile outside the Editor (G17).
- Public fields carrying Inspector data instead of `[SerializeField] private` (G8).
- A public static `Instance` introduced for a new subsystem instead of an injected dependency (G18).
- A `ScriptableObject` used as mutable shared runtime state with no single writer, drifting out of sync across scenes (G18, G31).
- A `GameManager`/`UIManager`/`Helper` class that has absorbed every unrelated system in the scene (G17, G12).
