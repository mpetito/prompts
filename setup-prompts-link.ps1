# PowerShell script to create symbolic links from VS Code Insiders user folders
# to the prompts and skills folders in this repository.
# This allows user profile prompts and skills across all projects to redirect to this repository.

# Get the script's directory (repository root)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePrompts = Join-Path $repoRoot "./prompts"
$sourceSkills = Join-Path $repoRoot "./skills"

# Define the VS Code Insiders user prompts folder
$userPromptsFolder = Join-Path $env:APPDATA "Code - Insiders\User\prompts"

# Define the Copilot skills folder (outside VS Code, in user home)
$userSkillsFolder = Join-Path $env:USERPROFILE ".copilot\skills"

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
            Write-Host "Symbolic link already exists at: $TargetPath" -ForegroundColor Cyan
            Write-Host "Current target: $((Get-Item $TargetPath).Target)" -ForegroundColor Cyan
            
            $response = Read-Host "Do you want to replace it? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Host "Skipping $Description." -ForegroundColor Yellow
                return $false
            }
            
            # Remove existing symbolic link
            Remove-Item $TargetPath -Force
            Write-Host "Removed existing symbolic link." -ForegroundColor Green
        }
        else {
            # It's a regular folder, rename it
            $parentDir = Split-Path $TargetPath -Parent
            $folderName = Split-Path $TargetPath -Leaf
            $backupFolder = Join-Path $parentDir "${folderName}_old"
            
            # If backup already exists, create a unique name
            if (Test-Path $backupFolder) {
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $backupFolder = Join-Path $parentDir "${folderName}_old_$timestamp"
            }
            
            Write-Host "Existing $Description folder found. Renaming to: $backupFolder" -ForegroundColor Yellow
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
        Write-Host "`n$Description symbolic link created successfully!" -ForegroundColor Green
        Write-Host "  Link: $TargetPath" -ForegroundColor Cyan
        Write-Host "  Target: $SourcePath" -ForegroundColor Cyan
        return $true
    }
    catch {
        Write-Host "`nFailed to create $Description symbolic link." -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        return $false
    }
}

Write-Host "Setting up VS Code Copilot prompts and skills..." -ForegroundColor Cyan
Write-Host ""

# Create prompts symbolic link
$promptsSuccess = New-SymLink -SourcePath $sourcePrompts -TargetPath $userPromptsFolder -Description "prompts"

# Create skills symbolic link
$skillsSuccess = New-SymLink -SourcePath $sourceSkills -TargetPath $userSkillsFolder -Description "skills"

# Check if either failed
if (-not $promptsSuccess -or -not $skillsSuccess) {
    if (-not $promptsSuccess -and -not $skillsSuccess) {
        Write-Host "`nBoth symbolic links failed or were skipped." -ForegroundColor Yellow
    }
    Write-Host "`nNote: Creating symbolic links on Windows requires either:" -ForegroundColor Yellow
    Write-Host "  1. Run PowerShell as Administrator, or" -ForegroundColor Yellow
    Write-Host "  2. Enable Developer Mode in Windows Settings" -ForegroundColor Yellow
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "  Prompts: $userPromptsFolder -> $sourcePrompts" -ForegroundColor Cyan
Write-Host "  Skills:  $userSkillsFolder -> $sourceSkills" -ForegroundColor Cyan
