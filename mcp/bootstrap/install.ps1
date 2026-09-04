[CmdletBinding()]
param(
    [string]$AwsRegion = "us-east-1",
    [switch]$SkipCredentialMigration
)

$ErrorActionPreference = "Stop"
$mcpRoot = Split-Path -Parent $PSScriptRoot

function Set-DockerMcpSecret {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string]$Value
    )

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = [System.Diagnostics.ProcessStartInfo]@{
        FileName = "docker"
        Arguments = "mcp secret set $Name"
        UseShellExecute = $false
        RedirectStandardInput = $true
    }
    $null = $process.Start()
    $process.StandardInput.Write($Value)
    $process.StandardInput.Close()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "Failed to store Docker MCP secret '$Name'."
    }
}

function Set-CodexMcpStartupTimeout {
    param(
        [Parameter(Mandatory)] [string]$ServerName,
        [Parameter(Mandatory)] [int]$Seconds
    )

    $configPath = Join-Path $env:USERPROFILE ".codex\config.toml"
    $config = Get-Content -Raw -LiteralPath $configPath
    $sectionPattern = "(?ms)(^\[mcp_servers\.$([regex]::Escape($ServerName))\]\s*\r?\n)(.*?)(?=^\[|\z)"
    $section = [regex]::Match($config, $sectionPattern)
    if (-not $section.Success) {
        throw "Codex MCP server '$ServerName' was not written to '$configPath'."
    }

    $body = $section.Groups[2].Value
    if ($body -match "(?m)^startup_timeout_sec\s*=") {
        $body = [regex]::Replace($body, "(?m)^startup_timeout_sec\s*=.*$", "startup_timeout_sec = $Seconds")
    } else {
        $body += "startup_timeout_sec = $Seconds`r`n"
    }
    $config = $config.Remove($section.Groups[2].Index, $section.Groups[2].Length).Insert($section.Groups[2].Index, $body)
    Set-Content -LiteralPath $configPath -Value $config -NoNewline
}

docker build --tag local/mcp-azure-devops:2.9.0 (Join-Path $mcpRoot "images\azure-devops")
docker build --tag local/mcp-material-ui:0.1.4 (Join-Path $mcpRoot "images\material-ui")
docker build --tag local/mcp-envative-kb:1.6.0 (Join-Path $mcpRoot "images\envative-kb")

docker mcp feature disable dynamic-tools
docker mcp feature enable tool-name-prefix
docker mcp profile import (Join-Path $mcpRoot "profiles\core-dev.yaml")
docker mcp profile import (Join-Path $mcpRoot "profiles\envative.yaml")
docker mcp profile config envative `
    --set "envative-kb.aws_region=$AwsRegion"
docker mcp catalog remove local/core-dev:latest 2>$null
docker mcp catalog remove local/envative:latest 2>$null
docker mcp catalog create local/core-dev:latest --from-profile core-dev --title core-dev
docker mcp catalog create local/envative:latest --from-profile envative --title envative

if (-not $SkipCredentialMigration) {
    $azureDevOpsPat = $env:AZURE_DEVOPS_PAT
    if (-not $azureDevOpsPat) {
        $azureDevOpsPat = [Environment]::GetEnvironmentVariable("AZURE_DEVOPS_PAT", "User")
    }
    if ($azureDevOpsPat) {
        Set-DockerMcpSecret -Name azure-devops.pat -Value $azureDevOpsPat
    } else {
        Write-Warning "AZURE_DEVOPS_PAT is unavailable. Store it with 'docker mcp secret set azure-devops.pat'."
    }

    $claudeConfigPath = Join-Path $env:USERPROFILE ".claude.json"
    if (Test-Path -LiteralPath $claudeConfigPath) {
        $claudeConfig = Get-Content -Raw -LiteralPath $claudeConfigPath | ConvertFrom-Json

        $agentMailUrl = $claudeConfig.mcpServers.'agent-mail'.url
        if ($agentMailUrl) {
            $apiKeyPair = ([uri]$agentMailUrl).Query.TrimStart('?').Split('&') |
                Where-Object { $_.StartsWith('apiKey=') } |
                Select-Object -First 1
            if ($apiKeyPair) {
                $agentMailKey = [uri]::UnescapeDataString($apiKeyPair.Split('=', 2)[1])
                Set-DockerMcpSecret -Name agentmail.api_key -Value $agentMailKey
            }
        }

        $firecrawlAuthorization = $claudeConfig.mcpServers.firecrawl.headers.Authorization
        if ($firecrawlAuthorization) {
            $firecrawlKey = $firecrawlAuthorization -replace '^Bearer\s+', ''
            Set-DockerMcpSecret -Name firecrawl.api_key -Value $firecrawlKey
        }
    }

}

claude mcp remove --scope user MCP_DOCKER_CORE 2>$null
claude mcp remove --scope user MCP_DOCKER_ENVATIVE 2>$null
codex mcp remove MCP_DOCKER_CORE 2>$null
codex mcp remove MCP_DOCKER_ENVATIVE 2>$null
claude mcp add --scope user MCP_DOCKER_CORE -- docker mcp gateway run --profile core-dev
claude mcp add --scope user MCP_DOCKER_ENVATIVE -- docker mcp gateway run --profile envative
codex mcp add MCP_DOCKER_CORE -- docker mcp gateway run --profile core-dev
codex mcp add MCP_DOCKER_ENVATIVE -- docker mcp gateway run --profile envative
Set-CodexMcpStartupTimeout -ServerName MCP_DOCKER_ENVATIVE -Seconds 30

Write-Host "Installed core-dev and envative profiles for Claude Code and Codex."
Write-Host "Authorize hosted services with 'docker mcp oauth authorize <server> --open-browser'."
