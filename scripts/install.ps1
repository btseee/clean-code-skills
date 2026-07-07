#!/usr/bin/env pwsh
# Installs, updates, or removes clean-code guidance (Windows/PowerShell
# equivalent of install.sh). Shared files (CLAUDE.md, AGENTS.md, GEMINI.md,
# .github/copilot-instructions.md) receive a managed block between
# clean-code-skills markers; your own content in those files is preserved, and
# re-running the installer updates only the block. Dedicated files and skill
# folders are owned by this package and are replaced on every run.
#
# Usage:
#   pwsh scripts/install.ps1 -Target ..\my-project all
#   pwsh scripts/install.ps1 -Target ..\my-project claude cursor copilot
#   pwsh scripts/install.ps1 -Target ..\my-project -Detect          # update what is installed
#   pwsh scripts/install.ps1 -Global claude codex gemini            # once for all projects
#   pwsh scripts/install.ps1 -Target ..\my-project -Uninstall all
#
# Bash-style flags (--detect, --global, --force, --uninstall) are also accepted
# so the same command line works in every shell.
#
# Project profiles: all, claude, agents, codex/opencode/jules (aliases for
# agents), gemini, cursor, copilot, windsurf, cline, skill.
# Global profiles: all, claude (~/.claude), codex (~/.codex), opencode
# (~/.config/opencode), gemini (~/.gemini), agents (codex + opencode).
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$Target = (Get-Location).Path,
    [switch]$Force,
    [switch]$Uninstall,
    [switch]$Global,
    [switch]$Detect,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Profiles = @()
)

$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
$Template = Join-Path $RootDir 'templates/agent-block.md'
$BeginMarker = '<!-- clean-code-skills:begin'
$EndMarker = '<!-- clean-code-skills:end -->'

# Accept bash-style long flags mixed into the profile list.
$normalized = @()
foreach ($p in $Profiles) {
    switch ($p.ToLowerInvariant()) {
        '--detect' { $Detect = $true }
        '--global' { $Global = $true }
        '--force' { $Force = $true }
        '--uninstall' { $Uninstall = $true }
        default { $normalized += $p.ToLowerInvariant() }
    }
}
$Profiles = $normalized

if (-not (Test-Path $Template)) { throw "Missing template: $Template" }
$TemplateText = (Get-Content $Template -Raw).Replace("`r`n", "`n").TrimEnd("`n")
if ($TemplateText -notmatch '^<!-- clean-code-skills:begin v(?<v>[^ ]+) -->') {
    throw 'Could not read version from template begin marker'
}
$Version = $Matches['v']

if ($Global) {
    $Target = if ($env:CLEAN_CODE_HOME) { $env:CLEAN_CODE_HOME } else { $HOME }
}

if (-not $Uninstall) {
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
}
if (-not (Test-Path $Target)) { throw "Target $Target does not exist" }
$TargetDir = (Resolve-Path $Target).Path

function Get-RelPath([string]$Path) {
    return $Path.Substring($TargetDir.Length).TrimStart('\', '/')
}

function Write-FileLf([string]$Path, [string]$Content) {
    # LF line endings, UTF-8 without BOM, single trailing newline.
    $normalizedContent = $Content.Replace("`r`n", "`n").TrimEnd("`n") + "`n"
    [System.IO.File]::WriteAllText($Path, $normalizedContent, [System.Text.UTF8Encoding]::new($false))
}

function Test-HasBlock([string]$Path) {
    return (Test-Path $Path) -and (Select-String -Path $Path -Pattern 'clean-code-skills:begin' -Quiet)
}

function Get-DetectedProfiles {
    $found = @()
    if ($Global) {
        if ((Test-HasBlock (Join-Path $TargetDir '.claude/CLAUDE.md')) -or (Test-Path (Join-Path $TargetDir '.claude/skills/clean-code'))) { $found += 'claude' }
        if (Test-HasBlock (Join-Path $TargetDir '.codex/AGENTS.md')) { $found += 'codex' }
        if (Test-HasBlock (Join-Path $TargetDir '.config/opencode/AGENTS.md')) { $found += 'opencode' }
        if (Test-HasBlock (Join-Path $TargetDir '.gemini/GEMINI.md')) { $found += 'gemini' }
    } else {
        if ((Test-HasBlock (Join-Path $TargetDir 'CLAUDE.md')) -or (Test-Path (Join-Path $TargetDir '.claude/skills/clean-code'))) { $found += 'claude' }
        if (Test-HasBlock (Join-Path $TargetDir 'AGENTS.md')) { $found += 'agents' }
        if (Test-HasBlock (Join-Path $TargetDir 'GEMINI.md')) { $found += 'gemini' }
        if (Test-Path (Join-Path $TargetDir '.cursor/rules/clean-code.mdc')) { $found += 'cursor' }
        if ((Test-HasBlock (Join-Path $TargetDir '.github/copilot-instructions.md')) -or (Test-Path (Join-Path $TargetDir '.github/skills/clean-code'))) { $found += 'copilot' }
        if (Test-Path (Join-Path $TargetDir '.windsurf/rules/clean-code.md')) { $found += 'windsurf' }
        if (Test-Path (Join-Path $TargetDir '.clinerules/clean-code.md')) { $found += 'cline' }
        if (Test-Path (Join-Path $TargetDir 'skills/clean-code')) { $found += 'skill' }
    }
    return $found
}

if ($Detect) {
    $Profiles += Get-DetectedProfiles
    if ($Profiles.Count -eq 0) {
        Write-Error "Nothing to detect in $TargetDir. Run again with explicit profiles (for example: all)."
        exit 1
    }
    Write-Output "Detected profiles: $($Profiles -join ' ')"
}

if ($Profiles.Count -eq 0) { $Profiles = @('all') }

function Merge-Block([string]$Dest) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null

    if (-not (Test-Path $Dest)) {
        Write-FileLf $Dest $TemplateText
        Write-Output "INSTALLED: $(Get-RelPath $Dest) (new file with managed block v$Version)"
        return
    }

    $text = (Get-Content $Dest -Raw).Replace("`r`n", "`n")
    $beginCount = [regex]::Matches($text, [regex]::Escape($BeginMarker)).Count
    $endCount = [regex]::Matches($text, [regex]::Escape($EndMarker)).Count

    if ($beginCount -eq 0 -and $endCount -eq 0) {
        Write-FileLf $Dest ($text.TrimEnd("`n") + "`n`n" + $TemplateText)
        Write-Output "UPDATED: $(Get-RelPath $Dest) (managed block v$Version appended; existing content preserved)"
        return
    }

    if ($beginCount -ne 1 -or $endCount -ne 1) {
        throw "$(Get-RelPath $Dest) has malformed clean-code-skills markers (begin=$beginCount end=$endCount); fix manually"
    }

    $pattern = [regex]::Escape($BeginMarker) + '.*?' + [regex]::Escape($EndMarker)
    $replaced = [regex]::Replace($text, $pattern, $TemplateText.Replace('$', '$$'), 'Singleline')
    Write-FileLf $Dest $replaced
    Write-Output "UPDATED: $(Get-RelPath $Dest) (managed block replaced with v$Version)"
}

function Remove-Block([string]$Dest) {
    if (-not (Test-Path $Dest)) { return }
    $text = (Get-Content $Dest -Raw).Replace("`r`n", "`n")
    if ($text -notmatch [regex]::Escape($BeginMarker)) { return }

    $pattern = [regex]::Escape($BeginMarker) + '.*?' + [regex]::Escape($EndMarker) + "`n?"
    $stripped = [regex]::Replace($text, $pattern, '', 'Singleline')

    if ([string]::IsNullOrWhiteSpace($stripped)) {
        Remove-Item $Dest -Force
        Write-Output "REMOVED: $(Get-RelPath $Dest) (file contained only the managed block)"
    } else {
        Write-FileLf $Dest $stripped
        Write-Output "UPDATED: $(Get-RelPath $Dest) (managed block removed; your content kept)"
    }
}

function Invoke-BlockTarget([string]$Dest) {
    if ($Uninstall) { Remove-Block $Dest } else { Merge-Block $Dest }
}

function Copy-OwnedFile([string]$SourceFile, [string]$DestFile) {
    if ((Test-Path $DestFile) -and -not (Select-String -Path $DestFile -Pattern 'clean-code' -Quiet) -and -not $Force) {
        Write-Output "SKIP: $(Get-RelPath $DestFile) exists and was not created by this package. Use -Force to overwrite."
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DestFile) | Out-Null
    $verb = if (Test-Path $DestFile) { 'UPDATED' } else { 'INSTALLED' }
    Write-FileLf $DestFile (Get-Content $SourceFile -Raw)
    Write-Output "${verb}: $(Get-RelPath $DestFile) (v$Version)"
}

function Remove-EmptyParents([string]$Dir) {
    while ($Dir -and $Dir -ne $TargetDir -and (Test-Path $Dir) -and -not (Get-ChildItem $Dir -Force)) {
        Remove-Item $Dir -Force
        $Dir = Split-Path -Parent $Dir
    }
}

function Remove-OwnedFile([string]$DestFile) {
    if (-not (Test-Path $DestFile)) { return }
    Remove-Item $DestFile -Force
    Write-Output "REMOVED: $(Get-RelPath $DestFile)"
    Remove-EmptyParents (Split-Path -Parent $DestFile)
}

function Invoke-OwnedFileTarget([string]$SourceFile, [string]$DestFile) {
    if ($Uninstall) { Remove-OwnedFile $DestFile } else { Copy-OwnedFile $SourceFile $DestFile }
}

function Copy-SkillDir([string]$DestDir) {
    $verb = if (Test-Path $DestDir) { 'UPDATED' } else { 'INSTALLED' }
    if (Test-Path $DestDir) { Remove-Item $DestDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DestDir) | Out-Null
    Copy-Item -Recurse (Join-Path $RootDir 'skills/clean-code') $DestDir
    Write-Output "${verb}: $(Get-RelPath $DestDir)/ (v$Version)"
}

function Remove-SkillDir([string]$DestDir) {
    if (-not (Test-Path $DestDir)) { return }
    Remove-Item $DestDir -Recurse -Force
    Write-Output "REMOVED: $(Get-RelPath $DestDir)/"
    Remove-EmptyParents (Split-Path -Parent $DestDir)
}

function Invoke-SkillTarget([string]$DestDir) {
    if ($Uninstall) { Remove-SkillDir $DestDir } else { Copy-SkillDir $DestDir }
}

function Invoke-GlobalProfile([string]$Name) {
    switch ($Name) {
        'all' {
            foreach ($p in @('claude', 'agents', 'gemini')) { Invoke-GlobalProfile $p }
        }
        'claude' {
            Invoke-BlockTarget (Join-Path $TargetDir '.claude/CLAUDE.md')
            Invoke-SkillTarget (Join-Path $TargetDir '.claude/skills/clean-code')
        }
        'agents' {
            Invoke-GlobalProfile 'codex'
            Invoke-GlobalProfile 'opencode'
        }
        'codex' { Invoke-BlockTarget (Join-Path $TargetDir '.codex/AGENTS.md') }
        'opencode' { Invoke-BlockTarget (Join-Path $TargetDir '.config/opencode/AGENTS.md') }
        'jules' { Invoke-GlobalProfile 'agents' }
        'gemini' { Invoke-BlockTarget (Join-Path $TargetDir '.gemini/GEMINI.md') }
        { $_ -in 'cursor', 'copilot', 'windsurf', 'cline', 'skill' } {
            Write-Output "SKIP: $Name is project-scoped; run without -Global for a specific project."
        }
        default {
            throw "Unknown profile: $Name"
        }
    }
}

function Invoke-ProjectProfile([string]$Name) {
    switch ($Name) {
        'all' {
            foreach ($p in @('claude', 'agents', 'gemini', 'cursor', 'copilot', 'windsurf', 'cline', 'skill')) {
                Invoke-ProjectProfile $p
            }
        }
        'claude' {
            Invoke-BlockTarget (Join-Path $TargetDir 'CLAUDE.md')
            Invoke-SkillTarget (Join-Path $TargetDir '.claude/skills/clean-code')
        }
        { $_ -in 'agents', 'codex', 'opencode', 'jules' } {
            Invoke-BlockTarget (Join-Path $TargetDir 'AGENTS.md')
        }
        'gemini' { Invoke-BlockTarget (Join-Path $TargetDir 'GEMINI.md') }
        'cursor' { Invoke-OwnedFileTarget (Join-Path $RootDir '.cursor/rules/clean-code.mdc') (Join-Path $TargetDir '.cursor/rules/clean-code.mdc') }
        'copilot' {
            Invoke-BlockTarget (Join-Path $TargetDir '.github/copilot-instructions.md')
            Invoke-OwnedFileTarget (Join-Path $RootDir '.github/instructions/clean-code.instructions.md') (Join-Path $TargetDir '.github/instructions/clean-code.instructions.md')
            Invoke-SkillTarget (Join-Path $TargetDir '.github/skills/clean-code')
        }
        'windsurf' { Invoke-OwnedFileTarget (Join-Path $RootDir '.windsurf/rules/clean-code.md') (Join-Path $TargetDir '.windsurf/rules/clean-code.md') }
        'cline' { Invoke-OwnedFileTarget (Join-Path $RootDir '.clinerules/clean-code.md') (Join-Path $TargetDir '.clinerules/clean-code.md') }
        'skill' { Invoke-SkillTarget (Join-Path $TargetDir 'skills/clean-code') }
        default {
            throw "Unknown profile: $Name (expected all, claude, agents, codex, opencode, jules, gemini, cursor, copilot, windsurf, cline, skill)"
        }
    }
}

foreach ($p in $Profiles) {
    if ($Global) { Invoke-GlobalProfile $p } else { Invoke-ProjectProfile $p }
}

if ($Uninstall) {
    Write-Output "Clean-code uninstall complete for $TargetDir"
} else {
    Write-Output "Clean-code v$Version install complete for $TargetDir"
    Write-Output 'To update later: re-run with -Detect (or use scripts/remote-install.ps1 with --detect).'
}
