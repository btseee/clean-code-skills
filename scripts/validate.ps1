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
    'README.md', 'CLAUDE.md', 'GEMINI.md', 'AGENTS.md',
    'CONTRIBUTING.md', 'LICENSE', 'VERSION',
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
    'skills/clean-code/references/architecture.md',
    'skills/clean-code/references/architecture-map.md',
    'skills/clean-code/references/principles.md',
    'skills/clean-code/references/smell-triage.md',
    'skills/clean-code/references/canon.md',
    'skills/clean-code/references/tests.md',
    'skills/clean-code/references/concurrency.md',
    'skills/clean-code/references/examples.md',
    'skills/clean-code/references/session-protocol.md',
    'skills/clean-code/references/new-project.md',
    'skills/clean-code/references/audit-report.md',
    'skills/clean-code/references/memory-protocol.md',
    'skills/clean-code/references/host-matrix.md',
    'skills/clean-code/scripts/detect_stack.py',
    'skills/clean-code/scripts/scan_repo.py',
    'skills/clean-code/scripts/check_boundaries.py',
    'skills/clean-code/assets/templates/architecture.md',
    'skills/clean-code/assets/templates/decisions.md',
    'skills/clean-code/assets/templates/ledger.md',
    'skills/clean-code/assets/hooks/pre-commit',
    'skills/clean-code/assets/hooks/claude-settings.json',
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
    Pass 'uninstall removes managed content and keeps user content'

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

# --- editor rule front matter -----------------------------------------------
# Cursor and Copilot both refuse to apply a rule file whose front matter is wrong,
# and the failure is silent, so it has to be checked rather than assumed.

$cursorRule = Join-Path $RootDir '.cursor/rules/clean-code.mdc'
$cursorLines = Get-Content $cursorRule
if ($cursorLines[0] -ne '---') { Fail 'Cursor rule must start with front matter' }
if (-not ($cursorLines | Select-String -Pattern '^alwaysApply: true$' -Quiet)) {
    Fail 'Cursor rule must set alwaysApply: true'
}
Pass 'Cursor rule front matter is valid'

$copilotInstructions = Join-Path $RootDir '.github/instructions/clean-code.instructions.md'
$copilotLines = Get-Content $copilotInstructions
if ($copilotLines[0] -ne '---') { Fail 'Copilot instructions must start with front matter' }
if (-not ($copilotLines | Select-String -Pattern '^applyTo: "\*\*/\*"$' -Quiet)) {
    Fail 'Copilot instructions must set applyTo: "**/*"'
}
Pass 'Copilot instruction front matter is valid'

# --- skill budget -----------------------------------------------------------
# The Agent Skills spec recommends keeping SKILL.md under 500 lines and roughly
# 5,000 tokens, because hosts load the whole body on activation.

$skillFile = Join-Path $RootDir 'skills/clean-code/SKILL.md'
$skillLines = (Get-Content $skillFile).Count
# Split on whitespace runs so this counts words the same way `wc -w` does. Measure-Object
# -Word disagrees with wc by a fraction of a percent, which is enough to make one
# validator fail while the other passes.
$skillWords = (((Get-Content $skillFile -Raw) -split '\s+') | Where-Object { $_ }).Count
$skillTokens = [int]($skillWords * 4 / 3)
if ($skillLines -gt 500) {
    Fail "SKILL.md is $skillLines lines; keep it under 500 and move depth into references/"
}
if ($skillTokens -gt 5000) {
    Fail "SKILL.md is ~$skillTokens tokens; keep it under 5000 and move depth into references/"
}
Pass "SKILL.md is within budget ($skillLines lines, ~$skillTokens tokens)"

# --- skill scripts ----------------------------------------------------------
# The scripts must run on a clean machine, so they may only use the standard library.

$python = @('python3', 'python', 'py') |
    ForEach-Object { Get-Command $_ -ErrorAction SilentlyContinue } |
    Select-Object -First 1

if ($python) {
    $checker = @'
import ast
import pathlib
import sys

ALLOWED = {
    "argparse", "ast", "collections", "dataclasses", "difflib", "fnmatch",
    "functools", "hashlib", "io", "itertools", "json", "os", "pathlib", "re",
    "shutil", "subprocess", "sys", "tempfile", "textwrap", "time", "typing",
    "unicodedata", "__future__",
}

root = pathlib.Path(sys.argv[1]) / "skills" / "clean-code" / "scripts"
bad = []
for path in sorted(root.glob("*.py")):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        print(f"{path.name} is not valid Python: {error}")
        sys.exit(1)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            if name.split(".")[0] not in ALLOWED:
                bad.append(f"{path.name}: {name}")

if bad:
    print("third-party imports found: " + ", ".join(bad))
    sys.exit(1)
'@
    $checkerPath = Join-Path ([System.IO.Path]::GetTempPath()) 'clean-code-import-check.py'
    Set-Content -Path $checkerPath -Value $checker -Encoding utf8
    try {
        $output = & $python.Source $checkerPath $RootDir 2>&1
        if ($LASTEXITCODE -ne 0) { Fail "skill scripts: $output" }
        Pass 'skill scripts parse and use only the standard library'
    }
    finally {
        Remove-Item $checkerPath -Force -ErrorAction SilentlyContinue
    }
}
else {
    Write-Output 'WARN: python not found; skipping skill script checks'
}

# --- portability of shipped skill content ------------------------------------
# Skill content is read by many agents. An absolute path from the author's machine
# breaks it everywhere else.

$shipped = Get-ChildItem -Path (Join-Path $RootDir 'skills'), (Join-Path $RootDir 'templates') `
    -Recurse -File -Filter '*.md'
foreach ($file in $shipped) {
    if (Select-String -Path $file.FullName -Pattern '(/Users/|/home/[a-z]|[A-Za-z]:\\\\)' -Quiet) {
        $relative = $file.FullName.Substring($RootDir.Length + 1)
        Fail "$relative contains an absolute machine path; use paths relative to the skill or project root"
    }
}
Pass 'shipped skill content has no absolute machine paths'

# --- line endings -----------------------------------------------------------
# Check the files this repository ships, not everything under the checkout: a working
# tree can also hold ignored caches, study material, and vendored third-party skills.

# Assert on what git has *committed*, not on the working tree. A Windows checkout with
# core.autocrlf=true legitimately holds CRLF on disk while the blob is LF, so scanning
# the worktree fails on every correct file there -- which is exactly how this check
# broke CI. `git ls-files --eol` reports the index encoding, which is the real
# requirement.
$eolReport = & git -C $RootDir ls-files --eol 2>$null
if ($LASTEXITCODE -eq 0 -and $eolReport) {
    # Format is "i/lf<spaces>w/lf<spaces>attr/<spaces>" then a TAB then the path.
    $committedCrlf = foreach ($line in $eolReport) {
        $fields = $line -split "`t", 2
        $indexEol = ($fields[0] -split '\s+')[0]
        if ($indexEol -in @('i/crlf', 'i/mixed')) { $fields[1] }
    }
    if ($committedCrlf) { Fail "CRLF committed in: $($committedCrlf -join ', ')" }

    foreach ($line in $eolReport) {
        $fields = $line -split "`t", 2
        $indexEol = ($fields[0] -split '\s+')[0]
        if ($indexEol -eq 'i/-text') { continue }  # binary
        $relative = $fields[1]
        $path = Join-Path $RootDir $relative
        if (-not (Test-Path $path -PathType Leaf)) { continue }
        $bytes = [System.IO.File]::ReadAllBytes($path)
        if ($bytes.Length -eq 0) { continue }
        if ($bytes[-1] -ne 10) { Fail "missing final newline in $relative" }
    }
    Pass 'line endings are LF in the index'
}
else {
    Write-Output 'WARN: not a git checkout; skipping line-ending check'
}

Pass 'clean-code-skills repository is valid'
