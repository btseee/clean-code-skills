#!/usr/bin/env pwsh
# Windows/PowerShell validator for clean-code-skills. Mirrors the checks in
# validate.sh: required files, skill front matter, version sync, managed-block
# sync, JSON parse, and install.ps1 behavior (merge, idempotency, uninstall).
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

# --- required files ---------------------------------------------------------

$requiredFiles = @(
    'README.md', 'CLAUDE.md', 'GEMINI.md', 'AGENTS.md', 'EXAMPLES.md',
    'FRAMEWORKS.md', 'CONTRIBUTING.md', 'LICENSE', 'VERSION',
    'gemini-extension.json', '.markdownlint.json',
    '.claude-plugin/plugin.json', '.claude-plugin/marketplace.json',
    '.codex-plugin/plugin.json', '.cursor/rules/clean-code.mdc',
    '.windsurf/rules/clean-code.md', '.clinerules/clean-code.md',
    '.github/copilot-instructions.md', '.github/instructions/clean-code.instructions.md',
    '.github/workflows/ci.yml', '.github/workflows/release.yml',
    'templates/agent-block.md',
    'skills/clean-code/SKILL.md',
    'skills/clean-code/references/chapter-map.md',
    'skills/clean-code/references/framework-map.md',
    'skills/clean-code/references/review-checklist.md',
    'skills/clean-code/references/project-refactor.md',
    'scripts/install.sh', 'scripts/install.ps1',
    'scripts/remote-install.sh', 'scripts/remote-install.ps1',
    'scripts/sync.sh',
    'scripts/validate.sh', 'scripts/validate.ps1'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path (Join-Path $RootDir $file))) { Fail "missing $file" }
}
Pass 'required files exist'

# --- skill front matter -------------------------------------------------------

$skillFile = Join-Path $RootDir 'skills/clean-code/SKILL.md'
$skillLines = Get-Content $skillFile
if ($skillLines[0] -ne '---') { Fail 'SKILL.md must start with front matter' }
if (-not ($skillLines -match '^name: clean-code$')) { Fail 'SKILL.md name must be clean-code' }
if (-not ($skillLines -match '^description: ')) { Fail 'SKILL.md needs description' }
if (-not ($skillLines -match '^license: MIT$')) { Fail 'SKILL.md needs MIT license field' }
if (-not ($skillLines[1..11] -contains '---')) { Fail 'SKILL.md front matter must close near the top' }
Pass 'skill front matter is valid'

# --- versions stay in sync -------------------------------------------------------

$template = Join-Path $RootDir 'templates/agent-block.md'
$templateText = (Get-Content $template -Raw).Replace("`r`n", "`n")
if ($templateText -notmatch '(?m)^<!-- clean-code-skills:begin v(?<v>[^ ]+) -->') {
    Fail 'template begin marker must carry a version'
}
$version = $Matches['v']

$fileVersion = (Get-Content (Join-Path $RootDir 'VERSION') -Raw).Trim()
if ($fileVersion -ne $version) { Fail "VERSION file ($fileVersion) != template version ($version)" }

$skillVersionLine = $skillLines | Where-Object { $_ -match '^\s+version: "(?<v>.+)"$' } | Select-Object -First 1
if (-not $skillVersionLine -or $Matches['v'] -ne $version) {
    Fail "SKILL.md metadata version does not match template version ($version)"
}

foreach ($manifest in @('.claude-plugin/plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/marketplace.json', 'gemini-extension.json')) {
    $raw = Get-Content (Join-Path $RootDir $manifest) -Raw
    if ($raw -notmatch [regex]::Escape("`"version`": `"$version`"")) { Fail "$manifest version != $version" }
}
Pass "versions are in sync ($version)"

# --- managed block stays identical across adapters --------------------------------

function Get-ManagedBlock([string]$Path) {
    $text = (Get-Content $Path -Raw).Replace("`r`n", "`n")
    $match = [regex]::Match($text, '(?ms)^<!-- clean-code-skills:begin.*?^<!-- clean-code-skills:end -->')
    if (-not $match.Success) { return $null }
    return $match.Value
}

$templateBlock = Get-ManagedBlock $template
if (-not $templateBlock) { Fail 'template has no managed block' }

$blockFiles = @(
    'CLAUDE.md', 'AGENTS.md', 'GEMINI.md',
    '.github/copilot-instructions.md',
    '.github/instructions/clean-code.instructions.md',
    '.cursor/rules/clean-code.mdc',
    '.windsurf/rules/clean-code.md',
    '.clinerules/clean-code.md'
)

foreach ($file in $blockFiles) {
    $block = Get-ManagedBlock (Join-Path $RootDir $file)
    if ($block -ne $templateBlock) { Fail "$file managed block drifted from templates/agent-block.md" }
}
Pass 'managed block is identical in all adapter files'

# --- JSON parses --------------------------------------------------------------------

foreach ($json in @('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.codex-plugin/plugin.json', 'gemini-extension.json', '.markdownlint.json')) {
    Get-Content (Join-Path $RootDir $json) -Raw | ConvertFrom-Json | Out-Null
}
Pass 'JSON files parse'

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
            '.claude/skills/clean-code/SKILL.md', '.github/skills/clean-code/SKILL.md')) {
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
    Pass 'uninstall removes managed content and keeps user content'

    $fakeHome = Join-Path $tmpDir 'fake-home'
    New-Item -ItemType Directory -Path $fakeHome | Out-Null
    $env:CLEAN_CODE_HOME = $fakeHome
    try {
        & (Join-Path $RootDir 'scripts/install.ps1') -Global all | Out-Null
        foreach ($file in @('.claude/CLAUDE.md', '.claude/skills/clean-code/SKILL.md', '.codex/AGENTS.md', '.config/opencode/AGENTS.md', '.gemini/GEMINI.md')) {
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

Pass 'clean-code-skills repository is valid'
