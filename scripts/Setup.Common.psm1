# Shared by the skill and MCP installers. Importing this module changes no files.
#Requires -Version 7.4
$ErrorActionPreference = 'Stop'

function Get-SetupPaths {
    param([string]$HomeDirectory)
    # An explicit home isolates destinations from machine-specific environment overrides.
    $isolated = -not [string]::IsNullOrWhiteSpace($HomeDirectory)
    if (-not $isolated) { $HomeDirectory = [Environment]::GetFolderPath('UserProfile') }
    $userRoot = [IO.Path]::GetFullPath($HomeDirectory)
    $codexRoot = Join-Path $userRoot '.codex'
    $claudeRoot = Join-Path $userRoot '.claude'
    $configRoot = Join-Path $userRoot '.config'
    if (-not $isolated) {
        if ($env:CODEX_HOME) { $codexRoot = [IO.Path]::GetFullPath($env:CODEX_HOME) }
        if ($env:CLAUDE_CONFIG_DIR) { $claudeRoot = [IO.Path]::GetFullPath($env:CLAUDE_CONFIG_DIR) }
        if ($env:XDG_CONFIG_HOME) { $configRoot = [IO.Path]::GetFullPath($env:XDG_CONFIG_HOME) }
    }
    $openCodeRoot = Join-Path $configRoot 'opencode'
    if (-not $isolated -and $env:OPENCODE_CONFIG_DIR) {
        $openCodeRoot = [IO.Path]::GetFullPath($env:OPENCODE_CONFIG_DIR)
    }
    $openCodeConfig = Join-Path $openCodeRoot 'opencode.json'
    if (Test-Path -LiteralPath (Join-Path $openCodeRoot 'opencode.jsonc')) {
        $openCodeConfig = Join-Path $openCodeRoot 'opencode.jsonc'
    }
    if (-not $isolated -and $env:OPENCODE_CONFIG) {
        $openCodeConfig = [IO.Path]::GetFullPath($env:OPENCODE_CONFIG)
    }
    $claudeConfig = Join-Path $userRoot '.claude.json'
    if (-not $isolated -and $env:CLAUDE_CONFIG_DIR) {
        $claudeConfig = Join-Path $claudeRoot '.claude.json'
    }
    @{
        UserRoot = $userRoot; CodexRoot = $codexRoot; ClaudeRoot = $claudeRoot
        ClaudeConfig = $claudeConfig; OpenCodeConfig = $openCodeConfig
        SharedSkills = Join-Path $userRoot '.agents/skills'
        CopilotSkills = Join-Path $userRoot '.copilot/skills'
        BackupRoot = Join-Path $userRoot '.prompts-backups'
    }
}

function Select-SetupTools {
    param([string[]]$Tools, [string[]]$Supported = @('codex', 'claude', 'opencode', 'copilot'))
    if (-not $Tools) {
        foreach ($tool in $Supported) {
            if (Get-Command $tool -ErrorAction SilentlyContinue) { $tool }
            else { Write-Host "[SKIPPED] $tool is not on PATH. Use -Tools $tool to prepare its files before installation." }
        }
        return
    }
    # Also accept comma-separated values from bash or pwsh -File.
    foreach ($tool in ($Tools -split ',' | ForEach-Object { $_.Trim().ToLowerInvariant() } | Select-Object -Unique)) {
        if ($tool -notin $Supported) { throw "Unknown tool '$tool'. Choose: $($Supported -join ', ')." }
        $tool
    }
}

function Test-SamePath {
    param([string]$Left, [string]$Right)
    $comparison = if ($IsWindows) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
    [string]::Equals([IO.Path]::TrimEndingDirectorySeparator([IO.Path]::GetFullPath($Left)),
        [IO.Path]::TrimEndingDirectorySeparator([IO.Path]::GetFullPath($Right)), $comparison)
}

function Get-LinkDestination {
    param($Item)
    if (-not $Item -or -not ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return }
    if ($Item.LinkTarget) {
        [IO.Path]::GetFullPath($Item.LinkTarget, (Split-Path -Parent $Item.FullName))
    }
}

function Test-RepoLink {
    param([string]$Path, [string]$Source)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    $destination = Get-LinkDestination $item
    $destination -and (Test-SamePath $destination $Source)
}

function Get-SkillTargets {
    param([string]$RepoRoot, [hashtable]$Paths, [string[]]$Tools)
    $skills = Join-Path $RepoRoot 'skills'
    if ('codex' -in $Tools -or 'opencode' -in $Tools) {
        @{ Source = $skills; Path = $Paths.SharedSkills; Children = $true }
    }
    if ('copilot' -in $Tools) {
        @{ Source = $skills; Path = $Paths.CopilotSkills; Children = $true }
    }
    if ('claude' -in $Tools) {
        @{ Source = $skills; Path = Join-Path $Paths.ClaudeRoot 'skills'; Children = $true }
        @{ Source = Join-Path $RepoRoot 'agents'; Path = Join-Path $Paths.ClaudeRoot 'agents'; Children = $false }
        @{ Source = Join-Path $RepoRoot 'instructions/CLAUDE.md'; Path = Join-Path $Paths.ClaudeRoot 'CLAUDE.md'; Children = $false }
        @{ Source = Join-Path $RepoRoot 'statusline/statusline.js'; Path = Join-Path $Paths.ClaudeRoot 'statusline.js'; Children = $false }
    }
}

function Move-SetupConflict {
    param([string]$Path, [string]$BackupRoot)
    # Backups live outside skill discovery folders to avoid publishing duplicate skills.
    $backupDir = Join-Path $BackupRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $backupDir -Force
    $backup = Join-Path $backupDir (Split-Path -Leaf $Path)
    Move-Item -LiteralPath $Path -Destination $backup
    Write-Host "[BACKUP] $Path -> $backup"
    $backup
}

function Install-RepoLink {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Source, [string]$Path, [string]$BackupRoot, [switch]$ReplaceConflicts)
    if (-not (Test-Path -LiteralPath $Source)) { throw "Repository source is missing: $Source" }
    if (Test-RepoLink $Path $Source) { Write-Host "[LINKED] $Path"; return $true }
    $existing = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($existing -and -not $ReplaceConflicts) {
        Write-Warning "Conflict preserved: $Path. Use -ReplaceConflicts to back it up and replace it."
        return $false
    }
    $action = if ($existing) { "Back up existing entry and link to $Source" } else { "Link to $Source" }
    if ($PSCmdlet.ShouldProcess($Path, $action)) {
        $backup = $null
        if ($existing) { $backup = Move-SetupConflict $Path $BackupRoot }
        try {
            $null = New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force
            $null = New-Item -ItemType SymbolicLink -Path $Path -Target $Source -ErrorAction Stop
        } catch {
            if ($backup) { Move-Item -LiteralPath $backup -Destination $Path }
            if ($IsWindows) { Write-Warning 'Windows symlinks require Developer Mode or an elevated PowerShell session.' }
            throw
        }
        Write-Host "[LINKED] $Path -> $Source"
        return $true
    }
    return $false
}

function Install-SkillChildren {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Source, [string]$Path, [string]$BackupRoot, [switch]$ReplaceConflicts)
    $existing = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    $isLink = $existing -and ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if ($existing -and ($isLink -or -not $existing.PSIsContainer)) {
        $owned = Test-RepoLink $Path $Source
        if (-not $owned -and -not $ReplaceConflicts) {
            Write-Warning "Skills root conflict preserved: $Path. Use -ReplaceConflicts to back it up and replace it."
            return $false
        }
        if ($PSCmdlet.ShouldProcess($Path, 'Replace whole-folder link or conflicting file with a real skills directory')) {
            if ($owned) {
                Remove-Item -LiteralPath $Path -Force
                Write-Warning "Converted whole-folder link: $Path. Tool-managed entries previously written into $Source must be moved out manually."
            } else { $null = Move-SetupConflict $Path $BackupRoot }
            $null = New-Item -ItemType Directory -Path $Path -Force
        } elseif (-not $WhatIfPreference) { return $false }
    }
    if (-not (Test-Path -LiteralPath $Path) -and $PSCmdlet.ShouldProcess($Path, 'Create skills directory')) {
        $null = New-Item -ItemType Directory -Path $Path -Force
    }
    $complete = $true
    foreach ($child in Get-ChildItem -LiteralPath $Source -Directory) {
        $linked = Install-RepoLink -Source $child.FullName -Path (Join-Path $Path $child.Name) `
            -BackupRoot $BackupRoot -ReplaceConflicts:$ReplaceConflicts -WhatIf:$WhatIfPreference
        if (-not $linked) { $complete = $false }
    }
    # Only prune direct child links with precisely the source/name mapping we create.
    if (Test-Path -LiteralPath $Path) {
        foreach ($child in Get-ChildItem -LiteralPath $Path -Force) {
            $expected = Join-Path $Source $child.Name
            if (-not (Test-Path -LiteralPath $expected) -and (Test-RepoLink $child.FullName $expected)) {
                if ($PSCmdlet.ShouldProcess($child.FullName, 'Remove stale repository skill link')) {
                    Remove-Item -LiteralPath $child.FullName -Force
                }
            }
        }
    }
    return $complete
}

function Remove-LegacyCodexLinks {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$RepoRoot, [hashtable]$Paths)
    $source = Join-Path $RepoRoot 'skills'
    $legacy = Join-Path $Paths.CodexRoot 'skills'
    if (Test-SamePath $legacy $Paths.SharedSkills) { return }
    if (Test-RepoLink $legacy $source) {
        # Migrate only after every replacement really exists. WhatIf removes nothing.
        $missing = @(Get-ChildItem -LiteralPath $source -Directory | Where-Object {
            -not (Test-RepoLink (Join-Path $Paths.SharedSkills $_.Name) $_.FullName)
        })
        if ($missing.Count -eq 0 -and $PSCmdlet.ShouldProcess($legacy, 'Remove legacy whole-folder link and retain a real Codex skills directory')) {
            Remove-Item -LiteralPath $legacy -Force
            $null = New-Item -ItemType Directory -Path $legacy
            Write-Warning "Removed legacy whole-folder link. Tool-managed entries in $source must be moved into $legacy manually."
        }
        return
    }
    $root = Get-Item -LiteralPath $legacy -Force -ErrorAction SilentlyContinue
    if (-not $root -or -not $root.PSIsContainer -or ($root.Attributes -band [IO.FileAttributes]::ReparsePoint)) { return }
    foreach ($child in Get-ChildItem -LiteralPath $legacy -Force) {
        $expected = Join-Path $source $child.Name
        if (-not (Test-RepoLink $child.FullName $expected)) { continue }
        if ((Test-Path -LiteralPath $expected) -and -not (Test-RepoLink (Join-Path $Paths.SharedSkills $child.Name) $expected)) { continue }
        if ($PSCmdlet.ShouldProcess($child.FullName, 'Remove migrated legacy Codex skill link')) {
            Remove-Item -LiteralPath $child.FullName -Force
        }
    }
}

function Invoke-SetupCommand {
    param([string]$Command, [string[]]$Arguments)
    # ErrorActionPreference alone does not turn native nonzero exits into exceptions.
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE): $Command $($Arguments -join ' ')" }
}

Export-ModuleMember -Function Get-SetupPaths, Select-SetupTools, Test-SamePath, Get-LinkDestination, Test-RepoLink, Get-SkillTargets, Install-RepoLink, Install-SkillChildren, Remove-LegacyCodexLinks, Invoke-SetupCommand
