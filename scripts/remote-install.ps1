#!/usr/bin/env pwsh
# No-clone installer: downloads the latest clean-code-skills release (or main)
# and runs the packaged installer against the current directory.
#
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/btseee/clean-code-skills/main/scripts/remote-install.ps1))) all
#   & ([scriptblock]::Create((irm .../remote-install.ps1))) claude cursor
#   & ([scriptblock]::Create((irm .../remote-install.ps1))) --detect      # update what is already installed
#
# Environment overrides:
#   CLEAN_CODE_REPO  owner/name (default btseee/clean-code-skills)
#   CLEAN_CODE_REF   tag or branch to install (default: latest release, else main)
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$InstallArgs = @()
)

$ErrorActionPreference = 'Stop'

$repo = if ($env:CLEAN_CODE_REPO) { $env:CLEAN_CODE_REPO } else { 'btseee/clean-code-skills' }
$ref = $env:CLEAN_CODE_REF

if (-not $ref) {
    try {
        $latest = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
        $ref = $latest.tag_name
    } catch {
        $ref = 'main'
    }
}
if (-not $ref) { $ref = 'main' }

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("clean-code-remote-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    Write-Output "Downloading clean-code-skills $ref..."
    $zip = Join-Path $tmp 'package.zip'
    Invoke-WebRequest "https://codeload.github.com/$repo/zip/$ref" -OutFile $zip
    Expand-Archive $zip -DestinationPath $tmp
    $extracted = Get-ChildItem $tmp -Directory | Select-Object -First 1

    & (Join-Path $extracted.FullName 'scripts/install.ps1') -Target (Get-Location).Path @InstallArgs
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
