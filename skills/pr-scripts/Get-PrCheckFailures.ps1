<#
.SYNOPSIS
Lists failing PR checks with trimmed failure-log excerpts as JSON.

.EXAMPLE
./Get-PrCheckFailures.ps1 -Pr 123
./Get-PrCheckFailures.ps1 -Pr 123 -LogTailLines 80
#>
[CmdletBinding()]
param(
    [int]$Pr,
    [string]$Repo,
    [int]$LogTailLines = 50
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$ctx = Resolve-PrContext -Repo $Repo -Pr $Pr

$checksRaw = gh pr checks $ctx.Pr -R $ctx.Repo --json name,state,bucket,link,workflow 2>&1
# gh pr checks exits non-zero when checks are failing/pending; only fail on unparseable output
if ("$checksRaw" -match 'no checks reported') { $checks = @() }
else {
    try { $checks = $checksRaw | ConvertFrom-Json } catch { throw "gh pr checks failed: $checksRaw" }
}

$failures = @($checks | Where-Object { $_.bucket -eq 'fail' })

$results = @($failures | ForEach-Object {
    $logExcerpt = $null
    if ($_.link -match '/actions/runs/(\d+)') {
        $runId = $Matches[1]
        $log = gh run view $runId -R $ctx.Repo --log-failed 2>$null
        if ($LASTEXITCODE -eq 0 -and $log) {
            $lines = @($log -split "`n")
            $logExcerpt = ($lines | Select-Object -Last $LogTailLines) -join "`n"
        }
    }
    [pscustomobject]@{
        name       = $_.name
        workflow   = $_.workflow
        state      = $_.state
        link       = $_.link
        logExcerpt = $logExcerpt
    }
})

ConvertTo-Json @($results) -Depth 4
