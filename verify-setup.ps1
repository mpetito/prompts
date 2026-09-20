#Requires -Version 7.4
[CmdletBinding()]
param([string[]]$Tools, [string]$HomeDirectory)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'scripts/Setup.Common.psm1') -Force
$paths = Get-SetupPaths -HomeDirectory $HomeDirectory
$selected = @(Select-SetupTools -Tools $Tools)
if (-not $selected) { throw 'No clients detected. Use -Tools to verify prepared client files.' }
$missing = 0
foreach ($target in Get-SkillTargets -RepoRoot $PSScriptRoot -Paths $paths -Tools $selected) {
    if ($target.Children) {
        $root = Get-Item -LiteralPath $target.Path -Force -ErrorAction SilentlyContinue
        if (-not $root -or -not $root.PSIsContainer -or ($root.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Write-Warning "Skills root must be a real directory: $($target.Path)"
            $missing++
        }
        $links = @(Get-ChildItem -LiteralPath $target.Source -Directory | ForEach-Object {
            @{ Source = $_.FullName; Path = Join-Path $target.Path $_.Name }
        })
    } else { $links = @($target) }
    foreach ($link in $links) {
        if ((Test-Path -LiteralPath $link.Source) -and (Test-RepoLink $link.Path $link.Source)) { Write-Host "[OK] $($link.Path)" }
        else { Write-Warning "Missing or conflicting link: $($link.Path)"; $missing++ }
    }
}
foreach ($command in @($selected) + @('gh', 'node')) {
    $found = Get-Command $command -ErrorAction SilentlyContinue
    if ($found) { Write-Host "[AVAILABLE] $command" }
    else { Write-Warning "Optional dependency not on PATH: $command" }
}
if (-not $IsWindows) { Write-Host '[UNSUPPORTED] Word COM helpers require Windows and desktop Microsoft Word.' }
if ($missing) { throw "$missing skill setup check(s) failed." }
Write-Host 'Skill links verified. MCP registration is checked separately by mcp/bootstrap/verify.ps1.'
