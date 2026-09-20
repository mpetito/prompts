#Requires -Version 7.4
# Mock CLI processes; no Docker daemon, network, credentials, or live config is used.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $repo 'scripts/Setup.Common.psm1') -Force
Import-Module (Join-Path $repo 'mcp/bootstrap/Mcp.Common.psm1') -Force
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Expect-Failure([scriptblock]$Action, [string]$Pattern) {
    try { & $Action } catch { if ($_.Exception.Message -notmatch $Pattern) { throw }; return }
    throw "Expected failure matching: $Pattern"
}
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('prompts-mcp-tests-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $testRoot
$prior = @{}
foreach ($name in @('CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'OPENCODE_CONFIG', 'OPENCODE_CONFIG_DIR', 'XDG_CONFIG_HOME')) {
    $prior[$name] = [Environment]::GetEnvironmentVariable($name)
}
$env:CODEX_HOME = Join-Path $testRoot 'codex'
$env:CLAUDE_CONFIG_DIR = Join-Path $testRoot 'claude'
$env:OPENCODE_CONFIG = Join-Path $testRoot 'opencode.jsonc'
$global:mcpTestCalls = [Collections.Generic.List[string]]::new()
$global:mcpTestFailure = ''
function global:docker {
    $call = 'docker ' + ($args -join ' ')
    $global:mcpTestCalls.Add($call)
    $global:LASTEXITCODE = if ($call -eq $global:mcpTestFailure) { 9 } else { 0 }
}
function global:codex {
    $global:mcpTestCalls.Add('codex ' + ($args -join ' '))
    $global:LASTEXITCODE = 0
    if ($args[0] -eq 'mcp' -and $args[1] -eq 'add') {
        $name = $args[2]
        $path = Join-Path $env:CODEX_HOME 'config.toml'
        $text = Get-Content -Raw -LiteralPath $path
        # Model the CLI's upsert, preserving unrelated tables.
        $text = [regex]::Replace($text, ('(?ms)^\[mcp_servers\.' + $name + '\].*?(?=^\[|\z)'), '')
        [IO.File]::WriteAllText($path, $text + "[mcp_servers.$name]`ncommand = `"docker`"`n")
    }
}
function global:claude {
    $global:mcpTestCalls.Add('claude ' + ($args -join ' '))
    $global:LASTEXITCODE = 0
    $path = Join-Path $env:CLAUDE_CONFIG_DIR '.claude.json'
    $config = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json -AsHashtable
    if ($args[1] -eq 'remove') { $config.mcpServers.Remove($args[4]) }
    if ($args[1] -eq 'add') { $config.mcpServers[$args[4]] = @{ command = 'docker' } }
    [IO.File]::WriteAllText($path, (ConvertTo-Json -InputObject $config -Depth 100))
}
function global:opencode { $global:mcpTestCalls.Add('opencode ' + ($args -join ' ')); $global:LASTEXITCODE = 0 }
try {
    $paths = Get-SetupPaths
    Assert (Test-SamePath $paths.CodexRoot $env:CODEX_HOME) 'Must honor CODEX_HOME.'
    Assert (Test-SamePath $paths.ClaudeRoot $env:CLAUDE_CONFIG_DIR) 'Must honor CLAUDE_CONFIG_DIR.'
    Assert (Test-SamePath $paths.OpenCodeConfig $env:OPENCODE_CONFIG) 'Must honor OPENCODE_CONFIG.'
    $isolated = Get-SetupPaths -HomeDirectory (Join-Path $testRoot 'isolated')
    Assert (-not (Test-SamePath $isolated.CodexRoot $env:CODEX_HOME)) 'Explicit home must isolate environment overrides.'
    $env:OPENCODE_CONFIG = $null
    $env:OPENCODE_CONFIG_DIR = $null
    $env:XDG_CONFIG_HOME = Join-Path $testRoot 'xdg'
    Assert (Test-SamePath (Get-SetupPaths).OpenCodeConfig (Join-Path $testRoot 'xdg/opencode/opencode.json')) 'Must honor XDG_CONFIG_HOME.'
    $env:OPENCODE_CONFIG_DIR = Join-Path $testRoot 'custom-config'
    Assert (Test-SamePath (Get-SetupPaths).OpenCodeConfig (Join-Path $testRoot 'custom-config/opencode.json')) 'Must honor OPENCODE_CONFIG_DIR.'
    $env:OPENCODE_CONFIG = $paths.OpenCodeConfig
    foreach ($folder in @($paths.CodexRoot, $paths.ClaudeRoot)) { $null = New-Item -ItemType Directory -Path $folder }
    $codexConfig = Join-Path $paths.CodexRoot 'config.toml'
    Set-Content -LiteralPath $codexConfig -Value "model = `"keep-model`"`n[mcp_servers.personal]`ncommand = `"keep-command`""
    Set-Content -LiteralPath $paths.ClaudeConfig -Value '{"theme":"keep","mcpServers":{"personal":{"command":"keep"},"MCP_DOCKER_CORE":{"command":"old"}}}'
    $jsonc = '{ // keep this comment in the backup' + "`n" + '"model":"keep-model","mcp":{"personal":{"type":"remote","url":"https://example.test"},},}'
    Set-Content -LiteralPath $paths.OpenCodeConfig -Value $jsonc -NoNewline
    $install = Join-Path $repo 'mcp/bootstrap/install.ps1'
    & $install -Tools codex,claude,opencode -WhatIf 6>$null
    Assert ($global:mcpTestCalls.Count -eq 0) 'MCP WhatIf must run no external commands.'
    Assert ((Get-Content -Raw -LiteralPath $paths.OpenCodeConfig) -ceq $jsonc) 'MCP WhatIf must leave config unchanged.'
    Assert (@(Get-ChildItem -LiteralPath $testRoot -Recurse -Filter '*.prompts-backup-*').Count -eq 0) 'MCP WhatIf must not create backups.'

    $global:mcpTestFailure = 'docker mcp version'
    Expect-Failure { & $install -Tools codex -SkipCredentialMigration 6>$null } 'MCP Toolkit is unavailable'
    Assert ($global:mcpTestCalls.Count -eq 1) 'Missing Docker MCP plugin must stop before any builds or writes.'
    $global:mcpTestCalls.Clear()
    $global:mcpTestFailure = 'docker build --tag local/mcp-azure-devops:2.9.0 ' + (Join-Path $repo 'mcp/images/azure-devops')
    Expect-Failure { & $install -Tools codex -SkipCredentialMigration 6>$null } 'Command failed'
    Assert (-not ($global:mcpTestCalls | Where-Object { $_ -like 'codex *' })) 'Build failure must stop before registration.'

    $global:mcpTestFailure = ''
    $global:mcpTestCalls.Clear()
    & $install -Tools codex,claude,opencode -SkipCredentialMigration 6>$null
    foreach ($name in @('core-dev', 'envative')) {
        Assert ("docker mcp catalog create local/${name}:latest --from-profile $name --title $name" -in $global:mcpTestCalls) 'Managed catalogs must be recreated from their profiles.'
    }
    Assert (-not ($global:mcpTestCalls | Where-Object { $_ -like 'docker mcp catalog remove*' })) 'Catalog create upserts, so nothing should be removed first.'
    Assert ('claude mcp remove --scope user MCP_DOCKER_CORE' -in $global:mcpTestCalls) 'Existing Claude entry must be replaced.'
    Assert ('claude mcp remove --scope user MCP_DOCKER_ENVATIVE' -notin $global:mcpTestCalls) 'Missing Claude entries must not be removed blindly.'
    $codexText = Get-Content -Raw -LiteralPath $codexConfig
    Assert ($codexText.Contains('keep-model') -and $codexText.Contains('keep-command')) 'Codex unrelated configuration must survive.'
    Assert (([regex]::Matches($codexText, 'startup_timeout_sec = 30')).Count -eq 2) 'Both Codex gateways need timeouts.'
    $claudeConfig = Read-McpJson $paths.ClaudeConfig
    Assert ($claudeConfig.theme -eq 'keep' -and $claudeConfig.mcpServers.personal.command -eq 'keep') 'Claude unrelated configuration must survive.'
    $openCodeConfig = Read-McpJson $paths.OpenCodeConfig
    Assert ($openCodeConfig.model -eq 'keep-model' -and $openCodeConfig.mcp.personal.url -eq 'https://example.test') 'OpenCode unrelated configuration must survive.'
    Assert ($openCodeConfig.mcp.MCP_DOCKER_CORE.timeout -eq 30000) 'OpenCode timeout must be milliseconds.'
    Assert ($openCodeConfig.mcp.MCP_DOCKER_ENVATIVE.command[-1] -eq 'envative') 'OpenCode command must select the correct profile.'
    $backups = @(Get-ChildItem -LiteralPath $testRoot -Filter 'opencode.jsonc.prompts-backup-*')
    Assert ($backups.Count -eq 1 -and (Get-Content -Raw -LiteralPath $backups[0].FullName) -ceq $jsonc) 'Original JSONC comments must survive in backup.'
    $global:mcpTestCalls.Clear()
    & $install -Tools opencode -SkipGatewaySetup -SkipCredentialMigration 6>$null
    Assert (@(Get-ChildItem -LiteralPath $testRoot -Filter 'opencode.jsonc.prompts-backup-*').Count -eq 1) 'Unchanged OpenCode config must not produce another backup.'
    Assert (-not ($global:mcpTestCalls | Where-Object { $_ -match '^(codex|claude) |^docker build' })) 'Client-only setup must not rebuild or invoke other clients.'

    Set-Content -LiteralPath $paths.OpenCodeConfig -Value '{broken'
    $global:mcpTestCalls.Clear()
    Expect-Failure { & $install -Tools opencode -SkipCredentialMigration 6>$null } 'JSON'
    Assert ($global:mcpTestCalls.Count -eq 0) 'Invalid client configuration must stop before Docker changes.'
    foreach ($newline in @("`n", "`r`n")) {
        [IO.File]::WriteAllText($codexConfig, "[mcp_servers.`"MCP_DOCKER_CORE`"]${newline}command = `"docker`"${newline}[other]${newline}value = 42${newline}")
        Set-CodexMcpStartupTimeout $codexConfig MCP_DOCKER_CORE
        Set-CodexMcpStartupTimeout $codexConfig MCP_DOCKER_CORE
        $text = Get-Content -Raw -LiteralPath $codexConfig
        Assert (([regex]::Matches($text, 'startup_timeout_sec')).Count -eq 1) 'Timeout updates must be idempotent.'
        Assert ($text.Contains("[other]${newline}value = 42")) 'Timeout updates must preserve adjacent tables and line endings.'
    }
    Write-Output 'PASS: MCP previews, prerequisites, native failures, client selection, config backups, JSONC merge, and timeout updates.'
} finally {
    foreach ($name in $prior.Keys) { [Environment]::SetEnvironmentVariable($name, $prior[$name]) }
    foreach ($name in @('docker', 'codex', 'claude', 'opencode')) { Remove-Item "Function:global:$name" -ErrorAction SilentlyContinue }
    Remove-Variable mcpTestCalls, mcpTestFailure -Scope Global
    Remove-Item -LiteralPath $testRoot -Recurse -Force
}
