# PowerShell script to create symbolic links from each agent tool's user-level
# skills and agents folders to the matching folders in this repository.
# This allows user profile skills and subagents across all projects to redirect here.
#
# Targets:
#   ~/.copilot/skills  - GitHub Copilot (VS Code + Copilot CLI)
#   ~/.claude/skills   - Claude Code (CLI, desktop, IDE extensions)
#   ~/.codex/skills/*  - Codex CLI (per-child links preserve Codex-managed .system skills)
#   ~/.agents/skills   - cross-tool convention (opencode and others that scan it)
#   ~/.claude/agents   - Claude Code subagent definitions (Claude Code format only)
#   ~/.claude/CLAUDE.md - Claude Code user-level global instructions (a file, not a folder)
#   ~/.claude/statusline.js - Claude Code custom status line script (a file, not a folder)

# Get the script's directory (repository root)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceSkills = Join-Path $repoRoot "skills"
$sourceAgents = Join-Path $repoRoot "agents"
$sourceGlobalMd = Join-Path $repoRoot "instructions\CLAUDE.md"
$sourceStatusLine = Join-Path $repoRoot "statusline\statusline.js"

# User-level targets, keyed by the tool that reads them. Skills are an open format every
# tool reads; subagent definitions, global instructions, and the status line script are
# Claude Code's own formats, so only it gets those links.
$targets = @(
    @{ Description = "Copilot skills"; Source = $sourceSkills; Path = Join-Path $env:USERPROFILE ".copilot\skills"; Kind = "Directory" }
    @{ Description = "Claude Code skills"; Source = $sourceSkills; Path = Join-Path $env:USERPROFILE ".claude\skills"; Kind = "Directory" }
    @{ Description = "Codex skills"; Source = $sourceSkills; Path = Join-Path $env:USERPROFILE ".codex\skills"; Kind = "DirectoryChildren" }
    @{ Description = "Cross-tool agent skills"; Source = $sourceSkills; Path = Join-Path $env:USERPROFILE ".agents\skills"; Kind = "Directory" }
    @{ Description = "Claude Code subagents"; Source = $sourceAgents; Path = Join-Path $env:USERPROFILE ".claude\agents"; Kind = "Directory" }
    @{ Description = "Claude Code global instructions"; Source = $sourceGlobalMd; Path = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"; Kind = "File" }
    @{ Description = "Claude Code status line"; Source = $sourceStatusLine; Path = Join-Path $env:USERPROFILE ".claude\statusline.js"; Kind = "File" }
)

# Function to create a symbolic link
function New-SymLink {
    param (
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$Description,
        [ValidateSet('Directory', 'File')]
        [string]$Kind = 'Directory'
    )

    # Ensure the source exists. A missing source folder is routine on a fresh clone and can
    # be created; a missing source file means the repository is incomplete, so stop instead
    # of silently linking to nothing.
    if (-not (Test-Path $SourcePath)) {
        if ($Kind -eq 'File') {
            Write-Host "Source file not found: $SourcePath" -ForegroundColor Red
            Write-Host "Skipping $Description." -ForegroundColor Yellow
            return "Failed"
        }
        Write-Host "Creating source folder: $SourcePath" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $SourcePath -Force | Out-Null
    }

    # Check if the target already exists
    if (Test-Path $TargetPath) {
        # Check if it's already a symbolic link
        $item = Get-Item $TargetPath -Force
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            $currentTarget = $item.Target

            # Already pointing at this repository - nothing to do
            if ($currentTarget -and ((Resolve-Path $currentTarget).Path -eq (Resolve-Path $SourcePath).Path)) {
                Write-Host "$Description symbolic link already points to this repository." -ForegroundColor Cyan
                Write-Host "  Link: $TargetPath" -ForegroundColor Cyan
                return "Linked"
            }

            Write-Host "Symbolic link already exists at: $TargetPath" -ForegroundColor Cyan
            Write-Host "Current target: $currentTarget" -ForegroundColor Cyan

            $response = Read-Host "Do you want to replace it? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Skipping $Description." -ForegroundColor Yellow
                return "Skipped"
            }

            # Remove existing symbolic link
            Remove-Item $TargetPath -Force
            Write-Host "Removed existing symbolic link." -ForegroundColor Green
        }
        else {
            # A real file or folder — it may be managed by another tool, so confirm before displacing it
            $isContainer = Test-Path $TargetPath -PathType Container
            $itemKind = if ($isContainer) { "folder" } else { "file" }
            $parentDir = Split-Path $TargetPath -Parent
            $leafName = Split-Path $TargetPath -Leaf
            $backupPath = Join-Path $parentDir "${leafName}_old"

            # If backup already exists, create a unique name
            if (Test-Path $backupPath) {
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $backupPath = Join-Path $parentDir "${leafName}_old_$timestamp"
            }

            Write-Host "Existing $Description $itemKind found (not a symbolic link): $TargetPath" -ForegroundColor Yellow
            if ($isContainer) {
                $contents = @(Get-ChildItem $TargetPath -Force -ErrorAction SilentlyContinue)
                Write-Host "  Contains $($contents.Count) item(s)$(if ($contents) { ': ' + (($contents | Select-Object -First 5).Name -join ', ') })" -ForegroundColor Yellow
            }
            else {
                $lineCount = @(Get-Content $TargetPath -ErrorAction SilentlyContinue).Count
                Write-Host "  $lineCount line(s). Its contents are NOT merged into the repository copy — check that nothing in it is lost first." -ForegroundColor Yellow
            }
            Write-Host "  It would be renamed to: $backupPath" -ForegroundColor Yellow
            Write-Host "  If another tool manages this $itemKind, replacing it will break that tool's state." -ForegroundColor Yellow

            $response = Read-Host "Rename it and link this repository instead? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Skipping $Description." -ForegroundColor Yellow
                return "Skipped"
            }

            Rename-Item -Path $TargetPath -NewName (Split-Path $backupPath -Leaf)
            Write-Host "Backup created successfully." -ForegroundColor Green
        }
    }

    # Ensure the parent directory exists
    $parentDir = Split-Path $TargetPath -Parent
    if (-not (Test-Path $parentDir)) {
        Write-Host "Creating parent directory: $parentDir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    # Create the symbolic link
    try {
        New-Item -ItemType SymbolicLink -Path $TargetPath -Target $SourcePath -Force | Out-Null
        Write-Host "$Description symbolic link created successfully!" -ForegroundColor Green
        Write-Host "  Link:   $TargetPath" -ForegroundColor Cyan
        Write-Host "  Target: $SourcePath" -ForegroundColor Cyan
        return "Linked"
    }
    catch {
        Write-Host "Failed to create $Description symbolic link." -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        return "Failed"
    }
}

function New-ChildSymLinks {
    param (
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    }

    $target = Get-Item -LiteralPath $TargetPath -Force
    if (-not $target.PSIsContainer -or ($target.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        Write-Host "$Description target must be a real directory so Codex-managed entries remain available: $TargetPath" -ForegroundColor Red
        return "Failed"
    }

    $statuses = foreach ($sourceChild in Get-ChildItem -LiteralPath $SourcePath -Directory) {
        New-SymLink `
            -SourcePath $sourceChild.FullName `
            -TargetPath (Join-Path $TargetPath $sourceChild.Name) `
            -Description "$Description ($($sourceChild.Name))"
    }

    if ($statuses -contains "Failed") { return "Failed" }
    if ($statuses -contains "Skipped") { return "Skipped" }
    return "Linked"
}

Write-Host "Setting up agent skills and subagents..." -ForegroundColor Cyan
Write-Host ""

$results = @()
foreach ($target in $targets) {
    $status = if ($target.Kind -eq "DirectoryChildren") {
        New-ChildSymLinks -SourcePath $target.Source -TargetPath $target.Path -Description $target.Description
    } else {
        New-SymLink -SourcePath $target.Source -TargetPath $target.Path -Description $target.Description -Kind $target.Kind
    }
    $summarySource = if ($target.Kind -eq "DirectoryChildren") { Join-Path $target.Source "*" } else { $target.Source }
    $summaryPath = if ($target.Kind -eq "DirectoryChildren") { Join-Path $target.Path "*" } else { $target.Path }
    $results += @{ Description = $target.Description; Source = $summarySource; Path = $summaryPath; Status = $status }
    Write-Host ""
}

# Only surface the privilege hint when a link genuinely failed — a declined
# target is a deliberate choice, not an error.
if ($results.Where({ $_.Status -eq "Failed" })) {
    Write-Host "One or more symbolic links failed." -ForegroundColor Yellow
    Write-Host "`nNote: Creating symbolic links on Windows requires either:" -ForegroundColor Yellow
    Write-Host "  1. Run PowerShell as Administrator, or" -ForegroundColor Yellow
    Write-Host "  2. Enable Developer Mode in Windows Settings" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Setup complete!" -ForegroundColor Green
foreach ($result in $results) {
    $label = $result.Status.ToUpper().PadRight(7)
    Write-Host "  [$label] $($result.Path) -> $($result.Source)" -ForegroundColor Cyan
}
