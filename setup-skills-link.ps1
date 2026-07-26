# PowerShell script to create symbolic links from each agent tool's user-level
# skills folder to the skills folder in this repository.
# This allows user profile skills across all projects to redirect to this repository.
#
# Targets:
#   ~/.copilot/skills  - GitHub Copilot (VS Code + Copilot CLI)
#   ~/.claude/skills   - Claude Code (CLI, desktop, IDE extensions)
#   ~/.agents/skills   - cross-tool convention (opencode and others that scan it)

# Get the script's directory (repository root)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceSkills = Join-Path $repoRoot "skills"

# User-level skills folders, keyed by the tool that reads them
$targets = @(
    @{ Description = "Copilot skills"; Path = Join-Path $env:USERPROFILE ".copilot\skills" }
    @{ Description = "Claude Code skills"; Path = Join-Path $env:USERPROFILE ".claude\skills" }
    @{ Description = "Cross-tool agent skills"; Path = Join-Path $env:USERPROFILE ".agents\skills" }
)

# Function to create a symbolic link
function New-SymLink {
    param (
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$Description
    )

    # Ensure the source folder exists
    if (-not (Test-Path $SourcePath)) {
        Write-Host "Creating source folder: $SourcePath" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $SourcePath -Force | Out-Null
    }

    # Check if the target folder already exists
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
            # It's a real folder — it may be managed by another tool, so confirm before displacing it
            $parentDir = Split-Path $TargetPath -Parent
            $folderName = Split-Path $TargetPath -Leaf
            $backupFolder = Join-Path $parentDir "${folderName}_old"

            # If backup already exists, create a unique name
            if (Test-Path $backupFolder) {
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $backupFolder = Join-Path $parentDir "${folderName}_old_$timestamp"
            }

            $contents = @(Get-ChildItem $TargetPath -Force -ErrorAction SilentlyContinue)
            Write-Host "Existing $Description folder found (not a symbolic link): $TargetPath" -ForegroundColor Yellow
            Write-Host "  Contains $($contents.Count) item(s)$(if ($contents) { ': ' + (($contents | Select-Object -First 5).Name -join ', ') })" -ForegroundColor Yellow
            Write-Host "  It would be renamed to: $backupFolder" -ForegroundColor Yellow
            Write-Host "  If another tool manages this folder, replacing it will break that tool's state." -ForegroundColor Yellow

            $response = Read-Host "Rename it and link this repository instead? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Skipping $Description." -ForegroundColor Yellow
                return "Skipped"
            }

            Rename-Item -Path $TargetPath -NewName (Split-Path $backupFolder -Leaf)
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

Write-Host "Setting up agent skills..." -ForegroundColor Cyan
Write-Host ""

$results = @()
foreach ($target in $targets) {
    $status = New-SymLink -SourcePath $sourceSkills -TargetPath $target.Path -Description $target.Description
    $results += @{ Description = $target.Description; Path = $target.Path; Status = $status }
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
    Write-Host "  [$label] $($result.Path) -> $sourceSkills" -ForegroundColor Cyan
}
