#!/usr/bin/env pwsh
# Exercises install.ps1 the way validate.sh exercises install.sh: fresh install,
# content-preserving merge, idempotent re-install, --detect, uninstall, a
# byte-identical round trip, and global mode. Everything else about the
# repository is checked once, by validate.sh, which CI also runs on Windows
# through Git Bash; nothing here duplicates it.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RootDir = Split-Path -Parent $PSScriptRoot

function Fail([string]$Message) {
    Write-Error "FAIL: $Message"
    exit 1
}

function Pass([string]$Message) {
    Write-Output "PASS: $Message"
}

# --- installer behavior ----------------------------------------------------------------

$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("clean-code-validate-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmpDir | Out-Null
try {
    [System.IO.File]::WriteAllText((Join-Path $tmpDir 'AGENTS.md'), "# My Project`n`nLocal agent notes that must survive.`n")

    & (Join-Path $RootDir 'scripts/install.ps1') -Target $tmpDir all | Out-Null

    foreach ($file in @('CLAUDE.md', 'GEMINI.md', 'AGENTS.md', '.cursor/rules/clean-code.mdc',
            '.windsurf/rules/clean-code.md', '.clinerules/clean-code.md',
            '.github/copilot-instructions.md', '.github/instructions/clean-code.instructions.md',
            'skills/clean-code/SKILL.md', 'skills/clean-code/references/project-refactor.md',
            '.claude/skills/clean-code/SKILL.md', '.agents/skills/clean-code/SKILL.md', '.grok/skills/clean-code/SKILL.md', '.github/skills/clean-code/SKILL.md')) {
        if (-not (Test-Path (Join-Path $tmpDir $file))) { Fail "installer did not create $file" }
    }
    Pass 'installer all profile works'

    $agentsText = Get-Content (Join-Path $tmpDir 'AGENTS.md') -Raw
    if ($agentsText -notmatch 'Local agent notes that must survive\.') { Fail 'installer clobbered existing AGENTS.md content' }
    if (([regex]::Matches($agentsText, 'clean-code-skills:begin')).Count -ne 1) { Fail 'AGENTS.md should contain exactly one managed block' }
    Pass 'merge preserves existing content'

    & (Join-Path $RootDir 'scripts/install.ps1') -Target $tmpDir all | Out-Null
    $agentsText = Get-Content (Join-Path $tmpDir 'AGENTS.md') -Raw
    if (([regex]::Matches($agentsText, 'clean-code-skills:begin')).Count -ne 1) { Fail 're-install duplicated the managed block' }
    Pass 're-install is idempotent'

    $detectOutput = & (Join-Path $RootDir 'scripts/install.ps1') -Target $tmpDir --detect
    if (-not ($detectOutput -match 'Detected profiles: .*claude')) { Fail '--detect did not find the claude profile' }
    $agentsText = Get-Content (Join-Path $tmpDir 'AGENTS.md') -Raw
    if (([regex]::Matches($agentsText, 'clean-code-skills:begin')).Count -ne 1) { Fail '--detect update duplicated the managed block' }
    Pass 'detect updates exactly what is installed'

    & (Join-Path $RootDir 'scripts/install.ps1') -Target $tmpDir -Uninstall all | Out-Null
    $agentsText = Get-Content (Join-Path $tmpDir 'AGENTS.md') -Raw
    if ($agentsText -notmatch 'Local agent notes that must survive\.') { Fail 'uninstall removed user content from AGENTS.md' }
    $leftover = Get-ChildItem $tmpDir -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { Select-String -Path $_.FullName -Pattern 'clean-code-skills:begin' -Quiet }
    if ($leftover) { Fail 'uninstall left managed markers behind' }
    if (Test-Path (Join-Path $tmpDir 'skills/clean-code')) { Fail 'uninstall left skills/clean-code behind' }
    if (Test-Path (Join-Path $tmpDir '.cursor/rules/clean-code.mdc')) { Fail 'uninstall left cursor rule behind' }
    Pass 'uninstall removes managed content and keeps user content'

    # Install then uninstall must restore a shared file byte for byte.
    $roundtripDir = Join-Path ([System.IO.Path]::GetTempPath()) ("ccs-roundtrip-" + [System.Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $roundtripDir | Out-Null
    try {
        $roundtripFile = Join-Path $roundtripDir 'CLAUDE.md'
        [System.IO.File]::WriteAllText($roundtripFile, "# My Project`n`nLocal notes.`n")
        $before = [System.IO.File]::ReadAllBytes($roundtripFile)
        & (Join-Path $RootDir 'scripts/install.ps1') -Target $roundtripDir claude | Out-Null
        & (Join-Path $RootDir 'scripts/install.ps1') -Target $roundtripDir -Uninstall claude | Out-Null
        $after = [System.IO.File]::ReadAllBytes($roundtripFile)
        if (-not ([System.Linq.Enumerable]::SequenceEqual($before, $after))) {
            Fail 'install then uninstall did not restore CLAUDE.md byte for byte'
        }
        Pass 'install/uninstall round trip is byte-identical'
    }
    finally {
        Remove-Item $roundtripDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    $fakeHome = Join-Path $tmpDir 'fake-home'
    New-Item -ItemType Directory -Path $fakeHome | Out-Null
    $env:CLEAN_CODE_HOME = $fakeHome
    try {
        & (Join-Path $RootDir 'scripts/install.ps1') -Global all | Out-Null
        foreach ($file in @('.claude/CLAUDE.md', '.claude/skills/clean-code/SKILL.md', '.codex/AGENTS.md', '.config/opencode/AGENTS.md', '.gemini/GEMINI.md', '.agents/skills/clean-code/SKILL.md', '.grok/skills/clean-code/SKILL.md', '.gemini/config/skills/clean-code/SKILL.md')) {
            if (-not (Test-Path (Join-Path $fakeHome $file))) { Fail "global install did not create $file" }
        }
        if (Test-Path (Join-Path $fakeHome '.cursor')) { Fail 'global install must skip project-scoped cursor profile' }
        & (Join-Path $RootDir 'scripts/install.ps1') --global --detect | Out-Null
        $claudeText = Get-Content (Join-Path $fakeHome '.claude/CLAUDE.md') -Raw
        if (([regex]::Matches($claudeText, 'clean-code-skills:begin')).Count -ne 1) { Fail 'global detect update duplicated the block' }
        & (Join-Path $RootDir 'scripts/install.ps1') -Global -Uninstall all | Out-Null
        $globalLeftover = Get-ChildItem $fakeHome -Recurse -File -Force -ErrorAction SilentlyContinue |
            Where-Object { Select-String -Path $_.FullName -Pattern 'clean-code-skills:begin' -Quiet }
        if ($globalLeftover) { Fail 'global uninstall left managed markers behind' }
        Pass 'global install, detect, and uninstall work'
    }
    finally {
        Remove-Item Env:CLEAN_CODE_HOME -ErrorAction SilentlyContinue
    }
}
finally {
    Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

Pass 'install.ps1 behaves like install.sh'
