#Requires -Version 7.4
[CmdletBinding()]
param([string[]]$Tools)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '../../scripts/Setup.Common.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'Mcp.Common.psm1') -Force
$selected = @(Select-SetupTools -Tools $Tools -Supported @('codex', 'claude', 'opencode'))
Assert-McpPrerequisites
Invoke-SetupCommand docker @('mcp', 'feature', 'list')
foreach ($profileName in @('core-dev', 'envative')) {
    Invoke-SetupCommand docker @('mcp', 'profile', 'show', $profileName, '--format', 'yaml')
    Invoke-SetupCommand docker @('mcp', 'gateway', 'run', '--profile', $profileName, '--dry-run')
}
foreach ($tool in $selected) {
    if (Get-Command $tool -ErrorAction SilentlyContinue) { Invoke-SetupCommand $tool @('mcp', 'list') }
    else { Write-Warning "Skipping $tool MCP verification: CLI is not installed." }
}
