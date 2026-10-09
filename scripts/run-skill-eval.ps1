#Requires -Version 7.4
<#
.SYNOPSIS
Run a skill's eval suite (skills/<name>/evals/shared-benchmark.json) through skill-eval-harness.
.DESCRIPTION
Prepares paired with-skill / without-skill tasks, runs them through a coding agent CLI, grades
deterministic assertions, runs the LLM judge, aggregates a benchmark, measures autonomous skill
triggering, and renders a review page. Requires `uv tool install skill-eval-harness`.

Claude runs are wrapped so they load project settings only: user-level skills, plugins and MCP
servers from this machine are not visible to the agent, while the normal login still works.
.EXAMPLE
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill pr-authoring
.EXAMPLE
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill review,spec -Runs 3 -SkipTrigger
#>
[CmdletBinding()]
param(
    # One or more skill folder names under skills/. Defaults to every skill that has an evals manifest.
    [string[]]$Skill,
    [ValidateSet('claude', 'codex')]
    [string]$Agent = 'claude',
    [string]$Model = 'sonnet',
    [string]$JudgeModel = 'sonnet',
    [ValidateRange(1, 50)]
    [int]$Runs = 1,
    [ValidateRange(1, 50)]
    [int]$TriggerRuns = 1,
    [ValidateSet('tune', 'holdout', 'holdback')]
    [string]$Split = 'tune',
    [string]$OutRoot,
    [int]$TimeoutSeconds = 600,
    [switch]$SkipTrigger,
    [switch]$SkipJudge,
    # Measure autonomous triggering only; no answer runs, grading or judge.
    [switch]$TriggerOnly,
    # Also run the old_skill arm; the manifest must declare old_skill_paths.
    [switch]$IncludeOldSkill
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command skill-benchmark -ErrorAction SilentlyContinue)) {
    throw 'skill-benchmark is not on PATH. Install it with: uv tool install skill-eval-harness'
}
$harnessPython = Join-Path (uv tool dir) 'skill-eval-harness' ($IsWindows ? 'Scripts/python.exe' : 'bin/python')
if (-not (Test-Path -LiteralPath $harnessPython)) { throw "skill-eval-harness python not found at $harnessPython" }
# The harness decodes agent output with the console code page unless Python runs in UTF-8 mode;
# on Windows that silently drops any run whose transcript contains a non-cp1252 byte.
$env:PYTHONUTF8 = '1'
if (-not $OutRoot) { $OutRoot = Join-Path $repo '.eval-runs' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Resolve-SkillList {
    param([string[]]$Requested)
    if ($Requested) { return $Requested -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ } }
    Get-ChildItem -Directory (Join-Path $repo 'skills') |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'evals/shared-benchmark.json') } |
        Select-Object -ExpandProperty Name
}

function New-ClaudeWrapper {
    param([string]$Directory)
    # A nested `claude -p` refuses to start while CLAUDECODE marks the parent session, so clear it.
    # Eval cases only read fixtures and write text, so every tool that can act on the machine is
    # denied outright: managed settings can grant Bash to a headless run, and a sandboxed run that
    # inherits the Herdr variables will otherwise treat the user's real terminal panes as its own.
    $wrapper = Join-Path $Directory 'claude-eval.cmd'
    $denied = 'Bash,PowerShell,Write,Edit,MultiEdit,NotebookEdit,Agent,WebFetch,WebSearch'
    $lines = @('@echo off', 'set CLAUDECODE=', 'set HERDR_PANE_ID=', 'set HERDR_TAB_ID=', 'set HERDR_WORKSPACE_ID=',
        'set HERDR_SOCKET_PATH=', 'set HERDR_BIN_PATH=', 'set HERDR_ENV=', 'set TERM_PROGRAM=',
        "claude --setting-sources project --strict-mcp-config --disallowedTools `"$denied`" %*")
    Set-Content -LiteralPath $wrapper -Value ($lines -join "`r`n") -Encoding ascii
    $wrapper
}

function Invoke-Harness {
    param([string[]]$Arguments)
    Write-Host "> skill-benchmark $($Arguments -join ' ')"
    & skill-benchmark @Arguments
    if ($LASTEXITCODE -ne 0) { throw "skill-benchmark $($Arguments[0]) failed with exit code $LASTEXITCODE" }
}

function Format-Rate {
    param($Value)
    if ($null -eq $Value) { return 'n/a' }
    '{0:n2}' -f [double]$Value
}

function Write-Summary {
    param([string]$Name, [string]$BenchmarkPath, [string]$TriggerPath)
    Write-Host ''
    Write-Host "== $Name =="
    if ($BenchmarkPath) {
        $b = Get-Content -Raw -LiteralPath $BenchmarkPath | ConvertFrom-Json
        $with = $b.summary.with_skill
        $without = $b.summary.without_skill
        $paired = $b.paired_summary
        Write-Host ("  objective pass rate   with {0}  without {1}  delta {2}" -f (Format-Rate $with.mean_objective_pass_rate), (Format-Rate $without.mean_objective_pass_rate), (Format-Rate $paired.absolute_delta))
        Write-Host ("  combined (with judge) with {0}  without {1}" -f (Format-Rate $with.mean_combined_pass_rate), (Format-Rate $without.mean_combined_pass_rate))
        Write-Host ("  cost USD              with {0}  without {1}" -f (Format-Rate $with.cost_usd_total), (Format-Rate $without.cost_usd_total))
        foreach ($r in $b.results) {
            $failed = @($r.assertions | Where-Object { $_.passed -eq $false } | ForEach-Object { $_.name })
            if ($failed) { Write-Host ("  {0}/{1} failed: {2}" -f $r.case_id, $r.variant, ($failed -join ', ')) }
    }
    }
    if ($TriggerPath -and (Test-Path -LiteralPath $TriggerPath)) {
        $t = Get-Content -Raw -LiteralPath $TriggerPath | ConvertFrom-Json
        foreach ($cell in $t.matrix) {
            $fire = $cell.summary.should_trigger
            $quiet = $cell.summary.should_not_trigger
            Write-Host ("  trigger {0}/{1}: should-fire {2}/{3}  should-not-fire {4}/{5}" -f $cell.agent, $cell.model, $fire.passed, $fire.total, $quiet.passed, $quiet.total)
            foreach ($q in $cell.queries | Where-Object { $_.passed_runs -lt $_.runs }) {
                Write-Host ("    missed ({0} of {1} runs): {2}" -f ($q.runs - $q.passed_runs), $q.runs, $q.query)
            }
        }
    }
}

$names = @(Resolve-SkillList -Requested $Skill)
if (-not $names) { throw 'No skill has an evals/shared-benchmark.json manifest.' }
$failed = @()
foreach ($name in $names) {
  try {
    $manifest = Join-Path $repo "skills/$name/evals/shared-benchmark.json"
    if (-not (Test-Path -LiteralPath $manifest)) { throw "No manifest at $manifest" }
    $out = Join-Path $OutRoot "$name/$stamp"
    $runsDir = Join-Path $out 'runs'
    $null = New-Item -ItemType Directory -Path $out -Force
    # One wrapper per run directory: concurrent invocations rewriting a shared .cmd made launches
    # fail with WinError 193, and every failed launch was scored as a miss.
    $claudeBin = New-ClaudeWrapper -Directory $out

    Invoke-Harness @('validate', $manifest, '--strict-leakage')
    if (-not $TriggerOnly) {
        $prepare = @('prepare', $manifest, '--split', $Split, '--runs-per-variant', $Runs, '--out', (Join-Path $out 'tasks.jsonl'))
        if ($IncludeOldSkill) { $prepare += '--include-old-skill' }
        Invoke-Harness $prepare

        $run = @('run-agent', '--agent', $Agent, '--model', $Model, '--timeout', $TimeoutSeconds, '--tasks', (Join-Path $out 'tasks.jsonl'), '--runs', $runsDir)
        if ($Agent -eq 'claude') { $run += @('--claude-bin', $claudeBin) }
        Invoke-Harness $run

        $benchmark = @('benchmark', $manifest, '--runs', $runsDir, '--split', $Split, '--out', (Join-Path $out 'benchmark.json'))
        if (-not $SkipJudge) {
            $judgeResults = Join-Path $out 'judge-results.jsonl'
            $judge = @('judge', $manifest, '--runs', $runsDir, '--split', $Split, '--judge-backend', $Agent, '--judge-model', $JudgeModel, '--out', $judgeResults)
            if ($Agent -eq 'claude') { $judge += @('--claude-bin', $claudeBin) }
            Invoke-Harness $judge
            $benchmark += @('--judge-results', $judgeResults)
    }
    Invoke-Harness $benchmark
    }

    $triggerReport = $null
    if (-not $SkipTrigger) {
        $triggerReport = Join-Path $out 'trigger-matrix.json'
        $trigger = @('--agent', $Agent, '--model', $Model, '--runs-per-query', $TriggerRuns, '--timeout', $TimeoutSeconds, '--trace-runs', (Join-Path $out 'trigger-traces'), '--out', $triggerReport, $manifest)
        if ($Agent -eq 'claude') { $trigger += @('--claude-bin', $claudeBin) }
        # The shim names the mounted skill folder after the skill (see scripts/trigger-matrix-shim.py).
        $shim = Join-Path $PSScriptRoot 'trigger-matrix-shim.py'
        Write-Host "> trigger-matrix-shim.py $($trigger -join ' ')"
        & $harnessPython -X utf8 $shim @trigger
        if ($LASTEXITCODE -ne 0) { throw "skill-trigger-matrix failed with exit code $LASTEXITCODE" }
    }

    if ($TriggerOnly) {
        Write-Summary -Name $name -TriggerPath $triggerReport
    }
    else {
        Invoke-Harness @('render-viewer', '--benchmark', (Join-Path $out 'benchmark.json'), '--runs', $runsDir, '--out', (Join-Path $out 'review.html'))
        Write-Summary -Name $name -BenchmarkPath (Join-Path $out 'benchmark.json') -TriggerPath $triggerReport
    }
    Write-Host "  artifacts: $out"
  }
  catch {
    # One broken suite must not hide the results of the others; the exit code reports it at the end.
    Write-Warning "$name failed: $($_.Exception.Message)"
    $failed += $name
  }
}
if ($failed) { throw "Eval failed for: $($failed -join ', ')" }
