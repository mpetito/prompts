#Requires -Version 7.4
# Offline integration checks. All writes are confined to a disposable directory.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $repo 'scripts/Setup.Common.psm1') -Force
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Expect-Failure([scriptblock]$Action, [string]$Pattern) {
    try { & $Action } catch { if ($_.Exception.Message -notmatch $Pattern) { throw }; return }
    throw "Expected failure matching: $Pattern"
}
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('prompts-tests-' + [guid]::NewGuid().ToString('N'))
$fixture = Join-Path $testRoot 'repo with spaces [test]'
$destination = Join-Path $testRoot 'user with spaces'
$null = New-Item -ItemType Directory -Path $fixture -Force
try {
    foreach ($folder in @('scripts', 'skills', 'agents', 'instructions', 'statusline')) {
        $null = New-Item -ItemType Directory -Path (Join-Path $fixture $folder) -Force
    }
    Copy-Item -LiteralPath (Join-Path $repo 'scripts/Setup.Common.psm1') -Destination (Join-Path $fixture 'scripts')
    foreach ($name in @('setup-skills-link.ps1', 'verify-setup.ps1')) {
        Copy-Item -LiteralPath (Join-Path $repo $name) -Destination $fixture
    }
    foreach ($name in @('example', 'pr-scripts')) {
        $null = New-Item -ItemType Directory -Path (Join-Path $fixture "skills/$name")
        Set-Content -LiteralPath (Join-Path $fixture "skills/$name/data.txt") -Value 'source'
    }
    Set-Content -LiteralPath (Join-Path $fixture 'instructions/CLAUDE.md') -Value 'instructions'
    Set-Content -LiteralPath (Join-Path $fixture 'statusline/statusline.js') -Value '// script'
    $setup = Join-Path $fixture 'setup-skills-link.ps1'
    $verify = Join-Path $fixture 'verify-setup.ps1'
    $paths = Get-SetupPaths -HomeDirectory $destination
    & $setup -Tools codex,claude,opencode,copilot -HomeDirectory $destination -WhatIf 6>$null
    Assert (-not (Test-Path -LiteralPath $destination)) 'WhatIf must not create even the home directory.'
    & $setup -Tools codex -HomeDirectory $destination 6>$null
    Assert (Test-RepoLink (Join-Path $paths.SharedSkills 'example') (Join-Path $fixture 'skills/example')) 'Codex must use shared skills.'
    Assert (-not (Test-Path -LiteralPath $paths.ClaudeRoot)) 'Codex selection must not create Claude files.'
    & $setup -Tools 'codex,claude,opencode,copilot' -HomeDirectory $destination 6>$null
    & $verify -Tools codex,claude,opencode,copilot -HomeDirectory $destination 3>$null 6>$null
    $initialCount = @(Get-ChildItem -LiteralPath $destination -Recurse -Force).Count
    & $setup -Tools codex,claude,opencode,copilot -HomeDirectory $destination 6>$null
    Assert (@(Get-ChildItem -LiteralPath $destination -Recurse -Force).Count -eq $initialCount) 'Reruns must not add files or backups.'
    Assert (Test-RepoLink (Join-Path $paths.SharedSkills 'pr-scripts') (Join-Path $fixture 'skills/pr-scripts')) 'Sibling helper directories must be linked.'

    $source = Join-Path $fixture 'skills/example'
    $link = Join-Path $paths.SharedSkills 'example'
    Remove-Item -LiteralPath $link -Force
    $relative = [IO.Path]::GetRelativePath($paths.SharedSkills, $source)
    $null = New-Item -ItemType SymbolicLink -Path $link -Target $relative
    & $setup -Tools codex -HomeDirectory $destination 6>$null
    Assert ((Get-Item -LiteralPath $link).LinkTarget -ceq $relative) 'A valid relative link must remain unchanged.'

    $foreign = Join-Path $paths.SharedSkills 'foreign'
    $stale = Join-Path $paths.SharedSkills 'removed-skill'
    $null = New-Item -ItemType SymbolicLink -Path $foreign -Target (Join-Path $testRoot 'missing-foreign')
    $null = New-Item -ItemType SymbolicLink -Path $stale -Target ([IO.Path]::GetRelativePath($paths.SharedSkills, (Join-Path $fixture 'skills/removed-skill')))
    & $setup -Tools codex -HomeDirectory $destination 6>$null
    Assert ($null -eq (Get-Item -LiteralPath $stale -Force -ErrorAction SilentlyContinue)) 'Owned dangling links must be removed.'
    Assert ($null -ne (Get-Item -LiteralPath $foreign -Force)) 'Unrelated dangling links must remain.'

    Remove-Item -LiteralPath $link -Force
    $null = New-Item -ItemType Directory -Path $link
    Set-Content -LiteralPath (Join-Path $link 'personal.txt') -Value 'keep me'
    Expect-Failure { & $setup -Tools codex -HomeDirectory $destination 3>$null 6>$null } 'incomplete'
    Assert ((Get-Content -LiteralPath (Join-Path $link 'personal.txt')) -eq 'keep me') 'Conflicts must be preserved by default.'
    & $setup -Tools codex -HomeDirectory $destination -ReplaceConflicts -WhatIf 6>$null
    Assert (-not (Test-Path -LiteralPath $paths.BackupRoot)) 'WhatIf must not create backups.'
    & $setup -Tools codex -HomeDirectory $destination -ReplaceConflicts 6>$null
    $backup = @(Get-ChildItem -LiteralPath $paths.BackupRoot -Recurse -File)
    Assert ($backup.Count -eq 1 -and (Get-Content -LiteralPath $backup[0].FullName) -eq 'keep me') 'Conflict backups must preserve data outside scanned roots.'

    Remove-Item -LiteralPath $link -Force
    $null = New-Item -ItemType SymbolicLink -Path $link -Target (Join-Path $testRoot 'missing-other')
    Expect-Failure { & $setup -Tools codex -HomeDirectory $destination 3>$null 6>$null } 'incomplete'
    & $setup -Tools codex -HomeDirectory $destination -ReplaceConflicts 6>$null
    Assert (Test-RepoLink $link $source) 'Explicit replacement must repair a broken conflicting link.'

    $legacy = Join-Path $paths.CodexRoot 'skills'
    $null = New-Item -ItemType Directory -Path (Join-Path $legacy '.system') -Force
    Set-Content -LiteralPath (Join-Path $legacy '.system/keep.txt') -Value 'system'
    $null = New-Item -ItemType SymbolicLink -Path (Join-Path $legacy 'example') -Target $source
    $null = New-Item -ItemType SymbolicLink -Path (Join-Path $legacy 'other') -Target (Join-Path $testRoot 'missing-other')
    & $setup -Tools codex -HomeDirectory $destination 6>$null
    Assert (-not (Test-Path -LiteralPath (Join-Path $legacy 'example'))) 'Migrated duplicate links must be removed.'
    Assert (Test-Path -LiteralPath (Join-Path $legacy '.system/keep.txt')) 'Codex system skills must survive migration.'
    Assert ($null -ne (Get-Item -LiteralPath (Join-Path $legacy 'other') -Force)) 'Unrelated legacy links must survive migration.'

    # A failed destination must never cause deletion of its legacy source link.
    Remove-Item -LiteralPath $link -Force
    $null = New-Item -ItemType Directory -Path $link
    $null = New-Item -ItemType SymbolicLink -Path (Join-Path $legacy 'example') -Target $source
    Expect-Failure { & $setup -Tools codex -HomeDirectory $destination 3>$null 6>$null } 'incomplete'
    Assert (Test-RepoLink (Join-Path $legacy 'example') $source) 'Migration must retain the old link when its replacement failed.'

    $wholeHome = Join-Path $testRoot 'whole-folder-user'
    $wholePaths = Get-SetupPaths -HomeDirectory $wholeHome
    $null = New-Item -ItemType Directory -Path $wholePaths.CodexRoot -Force
    $null = New-Item -ItemType Directory -Path (Split-Path -Parent $wholePaths.SharedSkills) -Force
    $null = New-Item -ItemType SymbolicLink -Path (Join-Path $wholePaths.CodexRoot 'skills') -Target (Join-Path $fixture 'skills')
    $null = New-Item -ItemType SymbolicLink -Path $wholePaths.SharedSkills -Target (Join-Path $fixture 'skills')
    & $setup -Tools codex -HomeDirectory $wholeHome 3>$null 6>$null
    Assert (-not (Get-Item -LiteralPath $wholePaths.SharedSkills).LinkType) 'Whole-folder shared link must become a real folder.'
    Assert (-not (Get-Item -LiteralPath (Join-Path $wholePaths.CodexRoot 'skills')).LinkType) 'Whole-folder legacy link must become a real folder.'
    Assert (Test-Path -LiteralPath (Join-Path $source 'data.txt')) 'Migration must not delete repository content.'
    if (-not $IsWindows) {
        Assert (-not (Test-SamePath (Join-Path $testRoot 'Case') (Join-Path $testRoot 'case'))) 'Unix comparisons must be case sensitive.'
    }
    Expect-Failure { & $setup -Tools unknown -HomeDirectory $destination } 'Unknown tool'
    Write-Output 'PASS: selections, previews, reruns, relative and broken links, conflicts, backups, migration, and verification.'
} finally { Remove-Item -LiteralPath $testRoot -Recurse -Force }
