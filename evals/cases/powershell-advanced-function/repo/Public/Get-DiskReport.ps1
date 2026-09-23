function Get-DiskReport {
    [CmdletBinding()]
    param(
        [Parameter()]
        [string]$Path = $PWD
    )

    Get-PSDrive -PSProvider FileSystem |
        Where-Object { $_.Root -like "$Path*" } |
        Select-Object Name, Used, Free
}
