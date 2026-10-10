#Requires -Version 7.4
<#
.SYNOPSIS
Run a skill's eval suite (skills/<name>/evals/shared-benchmark.json) through skill-eval-harness.
.DESCRIPTION
Prepares paired with-skill / without-skill tasks, runs them through a coding agent CLI, grades
deterministic assertions, runs the LLM judge, aggregates a benchmark, measures autonomous skill
triggering, and renders a review page. Requires `uv tool install skill-eval-harness`.

The harness runs one task at a time, so this script splits answer runs across -Parallel
processes, judges each arm in its own process, and measures triggering while the answer runs
are in flight. docs/evaluating-skills.md says which switches fit which kind of edit.

Claude runs are wrapped so they load project settings only: user-level skills, plugins and MCP
servers from this machine are not visible to the agent, while the normal login still works.
.EXAMPLE
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill pr-authoring
.EXAMPLE
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill review,spec -Runs 3 -SkipTrigger
.EXAMPLE
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill skill-authoring -Runs 3 -SkipTrigger -Baseline ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator
.EXAMPLE
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Regrade .eval-runs/skill-authoring/20261009-223826
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
    # Concurrent answer-run processes; judging uses one process per arm.
    [ValidateRange(1, 16)]
    [int]$Parallel = 4,
    [switch]$SkipTrigger,
    [switch]$SkipJudge,
    # Measure autonomous triggering only; no answer runs, grading or judge.
    [switch]$TriggerOnly,
    # Also run the old_skill arm; the manifest must declare old_skill_paths.
    [switch]$IncludeOldSkill,
    # A skill folder (or its SKILL.md) to run as the old_skill arm instead of old_skill_paths:
    # an earlier revision, or a competing skill such as an official plugin's.
    [string]$Baseline,
    # An existing run directory to grade again against the current manifest. No model calls
    # unless -Rejudge is given.
    [string]$Regrade,
    # With -Regrade, judge the saved outputs again, for a changed judge rubric.
    [switch]$Rejudge
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
    # Live skills first; archived skills (archive/skills) are measured on their way back in.
    @('skills', 'archive/skills') | ForEach-Object { Join-Path $repo $_ } | Where-Object { Test-Path -LiteralPath $_ } |
        ForEach-Object { Get-ChildItem -Directory $_ } |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'evals/shared-benchmark.json') } |
        Select-Object -ExpandProperty Name -Unique
}

function Get-ManifestPath {
    param([string]$Name)
    foreach ($root in 'skills', 'archive/skills') {
        $path = Join-Path $repo "$root/$Name/evals/shared-benchmark.json"
        if (Test-Path -LiteralPath $path) { return $path }
    }
    throw "No manifest for $Name under skills/ or archive/skills/"
}

function New-BaselineManifest {
    param([string]$Manifest, [string]$BaselinePath, [string]$Directory)
    $skillMd = (Test-Path -LiteralPath $BaselinePath -PathType Container) ? (Join-Path $BaselinePath 'SKILL.md') : $BaselinePath
    if (-not (Test-Path -LiteralPath $skillMd -PathType Leaf)) { throw "Baseline has no SKILL.md: $BaselinePath" }
    # The harness resolves skill paths against the skill folder and fixtures against the manifest's
    # folder, so this copy, written beside the run, carries every path absolute.
    $evalsDir = Split-Path -Parent $Manifest
    $skillRoot = Split-Path -Parent $evalsDir
    $m = Get-Content -Raw -LiteralPath $Manifest | ConvertFrom-Json -AsHashtable -Depth 100
    $m.skill_paths = @($m.skill_paths | ForEach-Object { [IO.Path]::GetFullPath($_, $skillRoot) })
    foreach ($case in $m.cases) {
        if ($case.files) { $case.files = @($case.files | ForEach-Object { [IO.Path]::GetFullPath($_, $evalsDir) }) }
        if ($case.prompt_ref) { $case.prompt_ref = [IO.Path]::GetFullPath($case.prompt_ref, $evalsDir) }
    }
    # The harness mounts the whole folder that holds this SKILL.md, minus evals/ and dotfiles.
    $m.old_skill_paths = @((Resolve-Path -LiteralPath $skillMd).Path)
    $path = Join-Path $Directory 'manifest.json'
    $m | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $path -Encoding utf8
    Set-Content -LiteralPath (Join-Path $Directory 'baseline.txt') -Value $m.old_skill_paths[0] -Encoding utf8
    $path
}

function New-ClaudeWrapper {
    param([string]$Directory)
    # A nested `claude -p` refuses to start while CLAUDECODE marks the parent session, so clear it.
    # Eval cases only read fixtures and write text, so every tool that can act on the machine is
    # denied outright: managed settings can grant Bash to a headless run, and a sandboxed run that
    # inherits the Herdr variables will otherwise treat the user's real terminal panes as its own.
    $denied = 'Bash,PowerShell,Write,Edit,MultiEdit,NotebookEdit,Agent,WebFetch,WebSearch'
    $cleared = @('CLAUDECODE', 'HERDR_PANE_ID', 'HERDR_TAB_ID', 'HERDR_WORKSPACE_ID', 'HERDR_SOCKET_PATH',
        'HERDR_BIN_PATH', 'HERDR_ENV', 'TERM_PROGRAM')
    $claude = "claude --setting-sources project --strict-mcp-config --disallowedTools `"$denied`""
    if ($IsWindows) {
        $wrapper = Join-Path $Directory 'claude-eval.cmd'
        $lines = @('@echo off') + @($cleared | ForEach-Object { "set $_=" }) + "$claude %*"
        Set-Content -LiteralPath $wrapper -Value ($lines -join "`r`n") -Encoding ascii
    }
    else {
        $wrapper = Join-Path $Directory 'claude-eval.sh'
        $lines = @('#!/bin/sh', "unset $($cleared -join ' ')", "exec $claude `"`$@`"")
        Set-Content -LiteralPath $wrapper -Value (($lines -join "`n") + "`n") -Encoding ascii
        & chmod +x -- $wrapper
        if ($LASTEXITCODE -ne 0) { throw "chmod failed for $wrapper" }
    }
    $wrapper
}

function Invoke-Harness {
    param([string[]]$Arguments)
    Write-Host "> skill-benchmark $($Arguments -join ' ')"
    & skill-benchmark @Arguments
    if ($LASTEXITCODE -ne 0) { throw "skill-benchmark $($Arguments[0]) failed with exit code $LASTEXITCODE" }
}

function Invoke-HarnessParallel {
    # Each job is a {Label, Arguments} pair run as its own skill-benchmark process, logged to LogDir.
    param([object[]]$Jobs, [string]$LogDir)
    $null = New-Item -ItemType Directory -Path $LogDir -Force
    $results = $Jobs | ForEach-Object -ThrottleLimit $Jobs.Count -Parallel {
        $log = Join-Path $using:LogDir "$($_.Label).log"
        $argList = $_.Arguments
        & skill-benchmark @argList *> $log
        [pscustomobject]@{ Label = $_.Label; ExitCode = $LASTEXITCODE; Log = $log }
    }
    $bad = @($results | Where-Object ExitCode -ne 0)
    if ($bad) { throw "skill-benchmark failed: $(($bad | ForEach-Object { "$($_.Label) (log: $($_.Log))" }) -join ', ')" }
}

function Invoke-ArmJudges {
    # One judge process per arm; their results are concatenated into $ResultsPath.
    param([string]$Manifest, [string]$RunsDir, [string[]]$Variants, [string]$ResultsPath, [string]$ClaudeBin, [string]$LogDir)
    $dir = Split-Path -Parent $ResultsPath
    $stem = [IO.Path]::GetFileNameWithoutExtension($ResultsPath)
    $jobs = foreach ($v in $Variants) {
        $judge = @('judge', $Manifest, '--runs', $RunsDir, '--split', $Split, '--judge-backend', $Agent, '--judge-model', $JudgeModel, '--variant', $v, '--out', (Join-Path $dir "$stem-$v.jsonl"))
        if ($Agent -eq 'claude') { $judge += @('--claude-bin', $ClaudeBin) }
        [pscustomobject]@{ Label = "$stem-$v"; Arguments = $judge }
    }
    Write-Host "> skill-benchmark judge: one process per arm ($($Variants -join ', '))"
    Invoke-HarnessParallel -Jobs $jobs -LogDir $LogDir
    Set-Content -LiteralPath $ResultsPath -Encoding utf8 -Value @($Variants | ForEach-Object { Get-Content -LiteralPath (Join-Path $dir "$stem-$_.jsonl") })
}

function Get-RunVariants {
    param([string]$RunsDir)
    @(Get-ChildItem -Directory -LiteralPath $RunsDir | ForEach-Object { Get-ChildItem -Directory -LiteralPath $_.FullName } |
        Select-Object -ExpandProperty Name -Unique)
}

function Format-Rate {
    param($Value)
    if ($null -eq $Value) { return 'n/a' }
    '{0:n2}' -f [double]$Value
}

function Write-Summary {
    param([string]$Name, [string]$BenchmarkPath, [string]$TriggerPath, [string]$BaselineFile)
    Write-Host ''
    Write-Host "== $Name =="
    if ($BenchmarkPath) {
        $b = Get-Content -Raw -LiteralPath $BenchmarkPath | ConvertFrom-Json
        $baselineName = ($BaselineFile -and (Test-Path -LiteralPath $BaselineFile)) ?
            (Split-Path -Leaf (Split-Path -Parent (Get-Content -LiteralPath $BaselineFile -TotalCount 1))) : $null
        # Judge rubrics are soft by default, so they never move the pass rates; report them apart.
        $judge = @{}
        foreach ($r in $b.results) {
            foreach ($q in @($r.qualitative_assertions | Where-Object { $null -ne $_.score })) {
                if (-not $judge[$r.variant]) { $judge[$r.variant] = [Collections.Generic.List[double]]::new() }
                $judge[$r.variant].Add([double]$q.score)
            }
        }
        foreach ($v in 'with_skill', 'without_skill', 'old_skill') {
            $s = $b.summary.$v
            if (-not $s) { continue }
            $label = ($v -eq 'old_skill' -and $baselineName) ? "old_skill ($baselineName)" : $v
            $judgeMean = $judge.ContainsKey($v) ? ($judge[$v] | Measure-Object -Average).Average : $null
            Write-Host ("  {0,-30} objective {1}  judge {2}  cost USD {3}" -f $label, (Format-Rate $s.mean_objective_pass_rate), (Format-Rate $judgeMean), (Format-Rate $s.cost_usd_total))
        }
        Write-Host ("  paired delta, with minus without: {0}" -f (Format-Rate $b.paired_summary.absolute_delta))
        $failures = foreach ($r in $b.results) {
            foreach ($a in @($r.assertions | Where-Object { $_.passed -eq $false })) { "$($r.case_id)/$($r.variant): $($a.name)" }
        }
        foreach ($g in $failures | Group-Object | Sort-Object Name) { Write-Host ("  failed {0}x  {1}" -f $g.Count, $g.Name) }
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

if ($Regrade) {
    $out = (Resolve-Path -LiteralPath $Regrade).Path
    $runsDir = Join-Path $out 'runs'
    if (-not (Test-Path -LiteralPath $runsDir)) { throw "No runs/ directory under $out" }
    $name = Split-Path -Leaf (Split-Path -Parent $out)
    $manifest = Get-ManifestPath $name
    $benchmarkPath = Join-Path $out 'benchmark-regraded.json'
    $runVariants = Get-RunVariants $runsDir
    $grade = @('benchmark', $manifest, '--runs', $runsDir, '--split', $Split, '--out', $benchmarkPath) +
        ($runVariants | ForEach-Object { '--variant', $_ })
    $judgeResults = Join-Path $out 'judge-results.jsonl'
    if ($Rejudge) {
        # A changed rubric needs new verdicts, not new answers; the first run's verdicts stay as they were.
        $judgeResults = Join-Path $out 'judge-results-regraded.jsonl'
        Invoke-ArmJudges -Manifest $manifest -RunsDir $runsDir -Variants $runVariants -ResultsPath $judgeResults -ClaudeBin (New-ClaudeWrapper -Directory $out) -LogDir (Join-Path $out 'logs')
    }
    if (Test-Path -LiteralPath $judgeResults) { $grade += @('--judge-results', $judgeResults) }
    Invoke-Harness $grade
    Invoke-Harness @('render-viewer', '--benchmark', $benchmarkPath, '--runs', $runsDir, '--out', (Join-Path $out 'review-regraded.html'))
    Write-Summary -Name $name -BenchmarkPath $benchmarkPath -TriggerPath (Join-Path $out 'trigger-matrix.json') -BaselineFile (Join-Path $out 'baseline.txt')
    Write-Host "  artifacts: $out"
    return
}

$names = @(Resolve-SkillList -Requested $Skill)
if (-not $names) { throw 'No skill has an evals/shared-benchmark.json manifest.' }
if ($Baseline -and $names.Count -ne 1) { throw '-Baseline compares one skill; name it with -Skill.' }
$failed = @()
foreach ($name in $names) {
  $triggerJob = $null
  try {
    $manifest = Get-ManifestPath $name
    $out = Join-Path $OutRoot "$name/$stamp"
    $runsDir = Join-Path $out 'runs'
    $logDir = Join-Path $out 'logs'
    $null = New-Item -ItemType Directory -Path $out -Force
    # One wrapper per run directory: concurrent invocations rewriting a shared .cmd made launches
    # fail with WinError 193, and every failed launch was scored as a miss.
    $claudeBin = New-ClaudeWrapper -Directory $out

    $answerManifest = $Baseline ? (New-BaselineManifest -Manifest $manifest -BaselinePath $Baseline -Directory $out) : $manifest
    $variants = @('with_skill', 'without_skill') + (($IncludeOldSkill -or $Baseline) ? @('old_skill') : @())
    Invoke-Harness @('validate', $answerManifest, '--strict-leakage')

    $triggerReport = $null
    if (-not $SkipTrigger) {
        # Triggering reads only the description, so it runs alongside the answer runs.
        $triggerReport = Join-Path $out 'trigger-matrix.json'
        $trigger = @('--agent', $Agent, '--model', $Model, '--runs-per-query', $TriggerRuns, '--timeout', $TimeoutSeconds, '--trace-runs', (Join-Path $out 'trigger-traces'), '--out', $triggerReport, $manifest)
        if ($Agent -eq 'claude') { $trigger += @('--claude-bin', $claudeBin) }
        # The shim names the mounted skill folder after the skill (see scripts/trigger-matrix-shim.py).
        $shim = Join-Path $PSScriptRoot 'trigger-matrix-shim.py'
        $null = New-Item -ItemType Directory -Path $logDir -Force
        $triggerLog = Join-Path $logDir 'trigger.log'
        Write-Host "> trigger-matrix-shim.py $($trigger -join ' ') (log: $triggerLog)"
        $triggerJob = Start-ThreadJob -ArgumentList $harnessPython, $shim, $trigger, $triggerLog -ScriptBlock {
            param($python, $shim, $argList, $log)
            & $python -X utf8 $shim @argList *> $log
            $LASTEXITCODE
        }
    }

    if (-not $TriggerOnly) {
        $tasks = Join-Path $out 'tasks.jsonl'
        $prepare = @('prepare', $answerManifest, '--split', $Split, '--runs-per-variant', $Runs, '--out', $tasks)
        if ($variants -contains 'old_skill') { $prepare += '--include-old-skill' }
        Invoke-Harness $prepare

        # Every task writes only its own runs/<case>/<variant>/run-N, so shards cannot collide.
        # Round-robin keeps each shard's mix of slow and fast cases even.
        $rows = @(Get-Content -LiteralPath $tasks | Where-Object { $_.Trim() })
        $shardCount = [Math]::Max(1, [Math]::Min($Parallel, $rows.Count))
        $jobs = for ($i = 0; $i -lt $shardCount; $i++) {
            $shard = Join-Path $out "tasks-$i.jsonl"
            Set-Content -LiteralPath $shard -Encoding utf8 -Value @(for ($j = $i; $j -lt $rows.Count; $j += $shardCount) { $rows[$j] })
            $run = @('run-agent', '--agent', $Agent, '--model', $Model, '--timeout', $TimeoutSeconds, '--tasks', $shard, '--runs', $runsDir)
            if ($Agent -eq 'claude') { $run += @('--claude-bin', $claudeBin) }
            [pscustomobject]@{ Label = "answers-$i"; Arguments = $run }
        }
        Write-Host "> skill-benchmark run-agent: $($rows.Count) tasks in $shardCount parallel shards (logs: $logDir)"
        Invoke-HarnessParallel -Jobs $jobs -LogDir $logDir

        # Without --variant, judge and benchmark score only the manifest's default arms, so the
        # old_skill runs would be paid for and never graded.
        $variantArgs = $variants | ForEach-Object { '--variant', $_ }
        $benchmark = @('benchmark', $answerManifest, '--runs', $runsDir, '--split', $Split, '--out', (Join-Path $out 'benchmark.json')) + $variantArgs
        if (-not $SkipJudge) {
            $judgeResults = Join-Path $out 'judge-results.jsonl'
            Invoke-ArmJudges -Manifest $answerManifest -RunsDir $runsDir -Variants $variants -ResultsPath $judgeResults -ClaudeBin $claudeBin -LogDir $logDir
            $benchmark += @('--judge-results', $judgeResults)
        }
        Invoke-Harness $benchmark
        Invoke-Harness @('render-viewer', '--benchmark', (Join-Path $out 'benchmark.json'), '--runs', $runsDir, '--out', (Join-Path $out 'review.html'))
    }

    if ($triggerJob) {
        $code = Receive-Job -Job $triggerJob -Wait -AutoRemoveJob
        $triggerJob = $null
        if ($code -ne 0) { throw "skill-trigger-matrix failed with exit code $code (log: $triggerLog)" }
    }

    $benchmarkPath = $TriggerOnly ? $null : (Join-Path $out 'benchmark.json')
    Write-Summary -Name $name -BenchmarkPath $benchmarkPath -TriggerPath $triggerReport -BaselineFile (Join-Path $out 'baseline.txt')
    Write-Host "  artifacts: $out"
  }
  catch {
    # One broken suite must not hide the results of the others; the exit code reports it at the end.
    Write-Warning "$name failed: $($_.Exception.Message)"
    $failed += $name
  }
  finally {
    if ($triggerJob) { Stop-Job -Job $triggerJob; Remove-Job -Job $triggerJob -Force }
  }
}
if ($failed) { throw "Eval failed for: $($failed -join ', ')" }
