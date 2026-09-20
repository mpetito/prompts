#Requires -Version 7.4
<#
.SYNOPSIS
Link this checkout into selected clients on Windows, Linux, or macOS.
.DESCRIPTION
Defaults to clients found on PATH. -Tools also prepares clients not yet installed.
Conflicts are preserved unless -ReplaceConflicts is given. -WhatIf previews changes.
An explicit -HomeDirectory isolates all destinations and ignores client environment overrides.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string[]]$Tools,
    [string]$HomeDirectory,
    [switch]$ReplaceConflicts
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'scripts/Setup.Common.psm1') -Force
$paths = Get-SetupPaths -HomeDirectory $HomeDirectory
$selected = @(Select-SetupTools -Tools $Tools)
if (-not $selected) { Write-Host 'No supported clients detected. Use -Tools to select clients explicitly.'; return }

$incomplete = $false
foreach ($target in Get-SkillTargets -RepoRoot $PSScriptRoot -Paths $paths -Tools $selected) {
    $options = @{
        Source = $target.Source; Path = $target.Path; BackupRoot = $paths.BackupRoot
        ReplaceConflicts = $ReplaceConflicts; WhatIf = $WhatIfPreference
    }
    $linked = if ($target.Children) { Install-SkillChildren @options } else { Install-RepoLink @options }
    if (-not $linked) { $incomplete = $true }
}
if ('codex' -in $selected) {
    Remove-LegacyCodexLinks -RepoRoot $PSScriptRoot -Paths $paths -WhatIf:$WhatIfPreference
}
if ($WhatIfPreference) { Write-Host 'Preview complete. No files were changed.' }
elseif ($incomplete) { throw 'Setup is incomplete; conflicting entries were preserved. Review warnings or run verify-setup.ps1.' }
else { Write-Host "Skills configured for: $($selected -join ', '). Restart clients to refresh skill discovery." }
