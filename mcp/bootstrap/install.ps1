#Requires -Version 7.4
[CmdletBinding(SupportsShouldProcess)]
param(
    [string[]]$Tools,
    [string]$AwsRegion = 'us-east-1',
    [switch]$SkipCredentialMigration,
    [switch]$SkipGatewaySetup
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '../../scripts/Setup.Common.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'Mcp.Common.psm1') -Force
$paths = Get-SetupPaths
$mcpRoot = Split-Path -Parent $PSScriptRoot
$selected = @(Select-SetupTools -Tools $Tools -Supported @('codex', 'claude', 'opencode') | Where-Object {
    if ((Get-Command $_ -ErrorAction SilentlyContinue) -or $WhatIfPreference) { $true }
    else { Write-Warning "Skipping $_ MCP registration: CLI is not installed."; $false }
})
if (-not $selected) { Write-Host 'No installed MCP clients selected. Install a client and rerun setup.'; return }

# Validate selected JSON configs before Docker changes, without displaying their contents.
if ('claude' -in $selected -or -not $SkipCredentialMigration) { $null = Read-McpJson $paths.ClaudeConfig }
if ('opencode' -in $selected) { Set-OpenCodeMcpConfig -Path $paths.OpenCodeConfig -ValidateOnly }
if (-not $WhatIfPreference) { Assert-McpPrerequisites }
if ($SkipGatewaySetup -and -not $WhatIfPreference) {
    foreach ($profileName in @('core-dev', 'envative')) {
        Invoke-SetupCommand docker @('mcp', 'profile', 'show', $profileName, '--format', 'yaml') | Out-Null
    }
}

if (-not $SkipGatewaySetup -and $PSCmdlet.ShouldProcess('Docker MCP', 'Build images and import core-dev and envative profiles')) {
    foreach ($image in @(@('azure-devops', '2.9.0'), @('material-ui', '0.1.4'), @('envative-kb', '1.6.0'))) {
        Invoke-SetupCommand docker @('build', '--tag', "local/mcp-$($image[0]):$($image[1])", (Join-Path $mcpRoot "images/$($image[0])"))
    }
    Invoke-SetupCommand docker @('mcp', 'feature', 'disable', 'dynamic-tools')
    Invoke-SetupCommand docker @('mcp', 'feature', 'enable', 'tool-name-prefix')
    foreach ($profileName in @('core-dev', 'envative')) {
        Invoke-SetupCommand docker @('mcp', 'profile', 'import', (Join-Path $mcpRoot "profiles/$profileName.yaml"))
    }
    Invoke-SetupCommand docker @('mcp', 'profile', 'config', 'envative', '--set', "envative-kb.aws_region=$AwsRegion")
    # 'catalog create' upserts an existing ref in place (Docker MCP Toolkit v0.43.3), so no
    # remove step is needed. The CLI documents no schema for 'catalog ls'; do not gate on it.
    foreach ($profileName in @('core-dev', 'envative')) {
        Invoke-SetupCommand docker @('mcp', 'catalog', 'create', "local/${profileName}:latest", '--from-profile', $profileName, '--title', $profileName)
    }
}
if (-not $SkipCredentialMigration -and $PSCmdlet.ShouldProcess('Docker MCP secret store', 'Migrate available PAT, SonarQube, AgentMail, and Firecrawl credentials')) {
    Copy-McpCredentials -ClaudeConfigPath $paths.ClaudeConfig
}
foreach ($tool in $selected) {
    if ($tool -eq 'opencode') {
        Set-OpenCodeMcpConfig -Path $paths.OpenCodeConfig -WhatIf:$WhatIfPreference
        continue
    }
    if (-not $PSCmdlet.ShouldProcess($tool, 'Back up configuration and register both Docker MCP gateways')) { continue }
    $configPath = if ($tool -eq 'codex') { Join-Path $paths.CodexRoot 'config.toml' } else { $paths.ClaudeConfig }
    Backup-McpConfig $configPath
    $claudeConfig = if ($tool -eq 'claude') { Read-McpJson $configPath } else { @{} }
    foreach ($entry in @(@('MCP_DOCKER_CORE', 'core-dev'), @('MCP_DOCKER_ENVATIVE', 'envative'))) {
        $name, $profileName = $entry
        if ($tool -eq 'claude') {
            if ($claudeConfig.mcpServers -and $claudeConfig.mcpServers.Contains($name)) {
                Invoke-SetupCommand claude @('mcp', 'remove', '--scope', 'user', $name)
            }
            Invoke-SetupCommand claude @('mcp', 'add', '--scope', 'user', $name, '--', 'docker', 'mcp', 'gateway', 'run', '--profile', $profileName)
        } else {
            Invoke-SetupCommand codex @('mcp', 'add', $name, '--', 'docker', 'mcp', 'gateway', 'run', '--profile', $profileName)
            Set-CodexMcpStartupTimeout -ConfigPath $configPath -ServerName $name
        }
    }
}
if ($WhatIfPreference) { Write-Host 'MCP preview complete. No commands were run and no files were changed.' }
else {
    Write-Host "Registered Docker MCP gateways for: $($selected -join ', ')."
    Write-Host "Authorize hosted services with 'docker mcp oauth authorize <server> --open-browser'."
}
