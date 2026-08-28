<#
.SYNOPSIS
    Merge the per-tranche CSV change logs into one reviewable Markdown change log.

.DESCRIPTION
    Invoke-DocxOps.ps1 writes a CSV per run. When a revision is delivered as a single
    tracked document assembled from several runs, the reviewer needs one log, not five. This
    merges them in run order, numbers every change, and keeps the rationale alongside
    the operation so a reviewer can see why each tracked change was made.

.PARAMETER LogFiles
    The CSVs to merge, in the order the tranches were applied. Accepts wildcards.

.PARAMETER OutFile
    Markdown file to write. Defaults to change-log.md in the current directory.

.PARAMETER Title
    Heading for the generated document.

.EXAMPLE
    .\Merge-ChangeLogs.ps1 ..\work\log-0*.csv -OutFile ..\work\change-log.md
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][string[]]$LogFiles,
    [string]$OutFile = 'change-log.md',
    [string]$Title = 'Tracked Changes — Rationale Log'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$files = @()
foreach ($pattern in $LogFiles) {
    $files += Get-ChildItem -Path $pattern -File | Sort-Object Name
}
if (-not $files) { throw "No change logs matched: $($LogFiles -join ', ')" }

$rows = [System.Collections.Generic.List[object]]::new()
$n = 0
foreach ($f in $files) {
    foreach ($r in (Import-Csv -LiteralPath $f.FullName)) {
        $n++
        $rows.Add([pscustomobject]@{
            Num    = $n
            Batch  = $f.BaseName
            Id     = $r.Id
            Op     = $r.Op
            Status = $r.Status
            Page   = $r.Page
            Detail = $r.Detail
            Note   = $r.Note
        })
    }
}

$md = [System.Collections.Generic.List[string]]::new()
$md.Add("# $Title")
$md.Add('')
$md.Add("$($rows.Count) operations across $($files.Count) batches. Every row is a tracked change in the delivered document; the Why column records the direction it implements.")
$md.Add('')

$summary = $rows | Group-Object Status | Sort-Object Count -Descending
$md.Add('| Outcome | Count |')
$md.Add('| --- | --- |')
foreach ($g in $summary) { $md.Add("| $($g.Name) | $($g.Count) |") }
$md.Add('')

foreach ($batch in ($rows | Group-Object Batch)) {
    $md.Add("## $($batch.Name)")
    $md.Add('')
    $md.Add('| # | Change | Op | Page | What changed | Why |')
    $md.Add('| --- | --- | --- | --- | --- | --- |')
    foreach ($r in $batch.Group) {
        # Pipes inside a cell would break the table; escape them.
        $detail = ($r.Detail -replace '\|', '\|') -replace '\r?\n', ' '
        $note   = ($r.Note   -replace '\|', '\|') -replace '\r?\n', ' '
        $flag   = if ($r.Status -eq 'OK') { '' } else { " **[$($r.Status)]** " }
        $md.Add("| $($r.Num) | ``$($r.Id)`` | $($r.Op) | $($r.Page) |$flag $detail | $note |")
    }
    $md.Add('')
}

$dir = Split-Path -Parent $OutFile
if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$md -join "`n" | Set-Content -LiteralPath $OutFile -Encoding utf8

[pscustomobject]@{
    OutFile    = (Resolve-Path -LiteralPath $OutFile).ProviderPath
    Batches    = $files.Count
    Operations = $rows.Count
    NotOk      = @($rows | Where-Object Status -ne 'OK').Count
}
