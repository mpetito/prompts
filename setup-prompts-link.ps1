# PowerShell script to create a symbolic link from VS Code Insiders user prompts folder
# to the .github/prompts folder in this repository.
# This allows user profile prompts across all projects to redirect to this repository's prompts.

# Get the script's directory (repository root)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePrompts = Join-Path $repoRoot ".github\prompts"

# Define the VS Code Insiders user prompts folder
$userPromptsFolder = Join-Path $env:APPDATA "Code - Insiders\User\prompts"

# Ensure the source .github/prompts folder exists
if (-not (Test-Path $sourcePrompts)) {
    Write-Host "Creating source folder: $sourcePrompts" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $sourcePrompts -Force | Out-Null
}

# Check if the user prompts folder already exists
if (Test-Path $userPromptsFolder) {
    # Check if it's already a symbolic link
    $item = Get-Item $userPromptsFolder -Force
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        Write-Host "Symbolic link already exists at: $userPromptsFolder" -ForegroundColor Cyan
        Write-Host "Current target: $((Get-Item $userPromptsFolder).Target)" -ForegroundColor Cyan
        
        $response = Read-Host "Do you want to replace it? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Host "Operation cancelled." -ForegroundColor Yellow
            exit 0
        }
        
        # Remove existing symbolic link
        Remove-Item $userPromptsFolder -Force
        Write-Host "Removed existing symbolic link." -ForegroundColor Green
    }
    else {
        # It's a regular folder, rename it to prompts_old
        $backupFolder = Join-Path (Split-Path $userPromptsFolder -Parent) "prompts_old"
        
        # If prompts_old already exists, remove it or create a unique name
        if (Test-Path $backupFolder) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupFolder = Join-Path (Split-Path $userPromptsFolder -Parent) "prompts_old_$timestamp"
        }
        
        Write-Host "Existing prompts folder found. Renaming to: $backupFolder" -ForegroundColor Yellow
        Rename-Item -Path $userPromptsFolder -NewName (Split-Path $backupFolder -Leaf)
        Write-Host "Backup created successfully." -ForegroundColor Green
    }
}

# Ensure the parent directory exists
$parentDir = Split-Path $userPromptsFolder -Parent
if (-not (Test-Path $parentDir)) {
    Write-Host "Creating parent directory: $parentDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
}

# Create the symbolic link
try {
    New-Item -ItemType SymbolicLink -Path $userPromptsFolder -Target $sourcePrompts -Force | Out-Null
    Write-Host "`nSymbolic link created successfully!" -ForegroundColor Green
    Write-Host "  Link: $userPromptsFolder" -ForegroundColor Cyan
    Write-Host "  Target: $sourcePrompts" -ForegroundColor Cyan
}
catch {
    Write-Host "`nFailed to create symbolic link." -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`nNote: Creating symbolic links on Windows requires either:" -ForegroundColor Yellow
    Write-Host "  1. Run PowerShell as Administrator, or" -ForegroundColor Yellow
    Write-Host "  2. Enable Developer Mode in Windows Settings" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nSetup complete! Your VS Code Insiders prompts now point to this repository." -ForegroundColor Green
