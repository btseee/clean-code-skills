# PowerShell

> Applies to: PowerShell 7.4+ (7.6 LTS current); Windows PowerShell 5.1 where a host requires it. Formatter: PSScriptAnalyzer's `Invoke-Formatter`. Linter: PSScriptAnalyzer. Read with: nothing.

## Names

- Name every function `Verb-Noun` with an approved verb (`Get-Verb` lists them) and a singular noun (`Get-User`, never `Get-Users` or `List-Users`) (N3, G24).
- Add a vendor or module prefix to the noun to avoid colliding with a built-in or another module's command (`Get-MyAppUser`) (N4).
- Name parameters in PascalCase for their meaning, matching cmdlet convention (`-Path`, `-Force`), never an abbreviation only the author understands (N1, N6).

## Functions And Types

- Start every function with `[CmdletBinding()]` (add `SupportsShouldProcess` when it changes state) so common parameters, `-Verbose`, and `-WhatIf` come for free.
- Type every parameter and validate it declaratively (`[ValidateNotNullOrEmpty()]`, `[ValidateRange()]`, `[ValidateSet()]`) instead of an early `if` that throws by hand.
- Accept pipeline input with `[Parameter(ValueFromPipeline)]` and a `process` block; never require a caller to assign a variable first just to loop over it.
- Emit objects (`[PSCustomObject]`, a typed class, or a domain type) from a function that returns data; never format it as a string for a caller to re-parse (G26).
- Use `Write-Host` only for output meant purely for a human on the console; use the pipeline (or `Write-Output`), `Write-Verbose`, and `Write-Warning` for everything else.
- Split a function that both decides whether to act and performs the action; gate the action with `$PSCmdlet.ShouldProcess(...)` rather than a boolean parameter (F3).

## Errors

- Set `$ErrorActionPreference = 'Stop'` at script scope so a cmdlet's non-terminating error becomes catchable; pass `-ErrorAction Stop` to individual calls inside a shared module.
- Catch specific exception types (`catch [System.IO.IOException]`) before a general `catch`; never catch everything only to swallow it (G4).
- Re-raise from a function with `$PSCmdlet.ThrowTerminatingError($_)` so the original `ErrorRecord`, category, and target survive for the caller.
- Model an expected alternate outcome (not found, already exists) as a return value or a `-PassThru` result; reserve a thrown error for what the caller did not ask for (Special Case pattern).

## Modules And Visibility

- Ship a module as a `.psm1` plus a `.psd1` manifest that lists `FunctionsToExport` explicitly; never export with a wildcard (G8).
- Split `Public/` (one file per exported function) from `Private/` (internal helpers); export only the public folder.
- Keep a function private unless another script or module is meant to call it.
- Never rely on a `$global:` variable to pass state between functions; pass parameters and return values instead (G18).

## Placement

- Mirror the module layout the project already uses (`Public/`, `Private/`, `Classes/`, `Tests/`); never add a loose top-level `.ps1` that duplicates a module function.
- Keep one function per file under `Public/`/`Private/` when the project follows that convention, named identically to the function.
- Keep build and packaging scripts (`build.ps1`) at the repository root, thin, and free of business logic.

## Tests

- Use Pester (5 or 6); existing `Should -Be` assertions keep working on either, so match whichever the project already has installed.
- Structure specs `Describe`/`Context`/`It` around behavior, and mock the filesystem, network, or registry a function calls rather than hitting them for real (F.I.R.S.T.).
- Test parameter validation and the `ShouldProcess` branch explicitly; `-WhatIf` must produce no side effect (T5).

## Layers

Applies only when `.clean/architecture.md` declares layers.

- Keep a public function a Humble Object: parameter binding, `ShouldProcess`, and formatting only; call into a `Classes/` type or a private function for any rule with real branching.
- Keep cmdlet-shaped types (`[PSCustomObject]`, a .NET type from a module you call) out of a domain class's public surface; convert at the boundary.
- Keep module import and dependency wiring (`Import-Module`, `using module`) at the script or manifest level, never inside a function that also does the work.

## Enforce

- PSScriptAnalyzer in CI (`Invoke-ScriptAnalyzer -Recurse`) with at least `PSUseApprovedVerbs`, `PSAvoidUsingCmdletAliases`, `PSAvoidUsingWriteHost`, `PSUseShouldProcessForStateChangingFunctions`, and `PSAvoidGlobalVars` enabled.
- `Invoke-Formatter` in CI or a pre-commit hook so layout never bikesheds a review.
- Pester in CI, with coverage on `Public/` and `Private/` functions, not just a manual run before release.

## Smells

- An alias (`gci`, `%`, `?`, `echo`) left in a script instead of the full cmdlet name (G24).
- A function that writes formatted text and expects a caller to regex-parse it back into data instead of returning an object (G26).
- `Invoke-Expression` building a command from string concatenation, where a script block or splatted parameters would do (G16).
- A state-changing function with no `SupportsShouldProcess`, so `-WhatIf` and `-Confirm` silently do nothing (G2).
- A verb outside the approved list (`Create-`, `Delete-`, `Update-`) forcing an import warning (G24, N3).
- A `$global:` variable standing in for a parameter or a module-scoped value (G18).
