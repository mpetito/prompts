#Requires -Version 7.4
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '../../scripts/Setup.Common.psm1')

function Assert-McpPrerequisites {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker is not on PATH. Install Docker and its MCP Toolkit before running MCP setup.' }
    try { Invoke-SetupCommand docker @('mcp', 'version') | Out-Null }
    catch { throw 'Docker MCP Toolkit is unavailable. Install a compatible docker mcp plugin; Docker Engine alone is insufficient. Skill setup does not require Docker.' }
    Invoke-SetupCommand docker @('info', '--format', '{{.ServerVersion}}') | Out-Null
    # The checked-in profiles use docker-desktop-store; validate its availability before builds.
    Invoke-SetupCommand docker @('mcp', 'secret', 'ls') | Out-Null
}

function Backup-McpConfig {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        $backup = "$Path.prompts-backup-$([guid]::NewGuid().ToString('N'))"
        Copy-Item -LiteralPath $Path -Destination $backup
        if (-not $IsWindows) { [IO.File]::SetUnixFileMode($backup, [IO.UnixFileMode]::UserRead -bor [IO.UnixFileMode]::UserWrite) }
        Write-Host "[BACKUP] $backup"
    }
}

function Read-McpJson {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return @{} }
    $config = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json -AsHashtable -Depth 100
    if ($config -isnot [System.Collections.IDictionary]) { throw "Expected a JSON object in $Path" }
    return $config
}

function Set-OpenCodeMcpConfig {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Path, [switch]$ValidateOnly)
    $config = Read-McpJson $Path
    if ($config.Contains('mcp') -and $config.mcp -isnot [System.Collections.IDictionary]) {
        throw "Expected an mcp object in $Path"
    }
    if (-not $config.Contains('mcp')) { $config.mcp = @{} }
    $changed = $false
    foreach ($entry in @(@('MCP_DOCKER_CORE', 'core-dev'), @('MCP_DOCKER_ENVATIVE', 'envative'))) {
        $expected = @{
            type = 'local'; command = @('docker', 'mcp', 'gateway', 'run', '--profile', $entry[1])
            enabled = $true; timeout = 30000
        }
        $current = $config.mcp[$entry[0]]
        if ($current -and $current.type -ceq 'local' -and $current.enabled -eq $true -and
            $current.timeout -eq 30000 -and
            (ConvertTo-Json -InputObject $current.command -Compress) -ceq (ConvertTo-Json -InputObject $expected.command -Compress)) { continue }
        # These two names are managed by this installer; other MCP entries remain intact.
        $config.mcp[$entry[0]] = $expected
        $changed = $true
    }
    if ($ValidateOnly) { return }
    if (-not $changed) { Write-Host "[UNCHANGED] OpenCode MCP configuration: $Path"; return }
    if ($PSCmdlet.ShouldProcess($Path, 'Back up and merge Docker MCP registrations (JSONC comments are retained in the backup)')) {
        $json = ConvertTo-Json -InputObject $config -Depth 100
        Backup-McpConfig $Path
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force
        [IO.File]::WriteAllText($Path, $json + [Environment]::NewLine)
    }
}

function Set-CodexMcpStartupTimeout {
    param([string]$ConfigPath, [string]$ServerName, [int]$Seconds = 30)
    $config = Get-Content -Raw -LiteralPath $ConfigPath
    $name = [regex]::Escape($ServerName)
    $pattern = '(?ms)(^\[mcp_servers\.(?:' + $name + '|"' + $name + '")\][ \t]*\r?\n)(.*?)(?=^\[|\z)'
    $section = [regex]::Match($config, $pattern)
    if (-not $section.Success) { throw "Codex MCP server '$ServerName' was not written to '$ConfigPath'." }
    $body = $section.Groups[2].Value
    $newline = if ($config.Contains("`r`n")) { "`r`n" } else { "`n" }
    if ($body -match '(?m)^startup_timeout_sec\s*=') {
        $body = [regex]::Replace($body, '(?m)^startup_timeout_sec[^\r\n]*', "startup_timeout_sec = $Seconds")
    } else {
        if ($body.Length -gt 0 -and -not $body.EndsWith("`n")) { $body += $newline }
        $body = "startup_timeout_sec = $Seconds$newline" + $body
    }
    $updated = $config.Remove($section.Groups[2].Index, $section.Groups[2].Length).Insert($section.Groups[2].Index, $body)
    [IO.File]::WriteAllText($ConfigPath, $updated)
}

function Set-DockerMcpSecret {
    param([string]$Name, [string]$Value)
    # Keep values off command lines and out of error output.
    $process = [Diagnostics.Process]::new()
    # Docker Desktop ships both docker.exe and an extension-less docker shim, so this resolves
    # to more than one command; an array here would silently become a space-joined FileName.
    $process.StartInfo.FileName = @(Get-Command docker -CommandType Application)[0].Source
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.RedirectStandardInput = $true
    foreach ($argument in @('mcp', 'secret', 'set', $Name)) { $process.StartInfo.ArgumentList.Add($argument) }
    try {
        $null = $process.Start()
        $process.StandardInput.Write($Value)
        $process.StandardInput.Close()
        $process.WaitForExit()
        if ($process.ExitCode -ne 0) { throw "Failed to store Docker MCP secret '$Name'." }
    } finally { $process.Dispose() }
}

function Copy-McpCredentials {
    param([string]$ClaudeConfigPath)
    $pat = $env:AZURE_DEVOPS_PAT
    if (-not $pat -and $IsWindows) { $pat = [Environment]::GetEnvironmentVariable('AZURE_DEVOPS_PAT', 'User') }
    if ($pat) { Set-DockerMcpSecret 'azure-devops.pat' $pat }
    else { Write-Warning "AZURE_DEVOPS_PAT is unavailable. Use 'docker mcp secret set azure-devops.pat'." }
    $config = Read-McpJson $ClaudeConfigPath
    $url = $config.mcpServers.'agent-mail'.url
    $agentMailKey = $env:AGENTMAIL_API_KEY
    if (-not $agentMailKey -and $url) {
        $pair = ([uri]$url).Query.TrimStart('?').Split('&') | Where-Object { $_.StartsWith('apiKey=') } | Select-Object -First 1
        if ($pair) { $agentMailKey = [uri]::UnescapeDataString($pair.Split('=', 2)[1]) }
    }
    if (-not $agentMailKey) { $agentMailKey = $config.mcpServers.'agent-mail'.headers.'x-api-key' }
    if ($agentMailKey) { Set-DockerMcpSecret 'agentmail.api_key' $agentMailKey }
    $firecrawlKey = $env:FIRECRAWL_API_KEY
    if (-not $firecrawlKey) { $firecrawlKey = $config.mcpServers.firecrawl.headers.Authorization -replace '^Bearer\s+', '' }
    if ($firecrawlKey) { Set-DockerMcpSecret 'firecrawl.api_key' $firecrawlKey }
}

Export-ModuleMember -Function Assert-McpPrerequisites, Backup-McpConfig, Read-McpJson, Set-OpenCodeMcpConfig, Set-CodexMcpStartupTimeout, Copy-McpCredentials
