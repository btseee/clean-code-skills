$public = Join-Path $PSScriptRoot 'Public'
Get-ChildItem -Path $public -Filter '*.ps1' | ForEach-Object {
    . $_.FullName
}
