#Requires -Version 7.4
<#
.SYNOPSIS
Stage the commit-commands, code-review and pr-review-toolkit plugins as one skill folder, the
plugin arm (-Baseline) of the pull-request suite.
.DESCRIPTION
The folder is generated from the installed plugins on each run and lives outside the
repository, so the plugins' third-party text is never committed. It holds:
- SKILL.md: the four command descriptions joined as its description, one paragraph of harness
  glue labelled as such, then each command body verbatim under `## /<plugin>:<command>`.
  Each host-expanded context line (!`cmd`) becomes a pointer to the fixture section headed
  `## cmd`, and review-pr's "$ARGUMENTS" becomes "" (its default: every review aspect).
- agents/: the pr-review-toolkit agents, verbatim.
The suite's cases tagged plugin-arm (A1, R1) are the ones this arm is compared on; the
runner runs the arm on every case, so read only those.
.PARAMETER Destination
The folder to write. Defaults to $CLAUDE_JOB_DIR/tmp/plugin-baseline/pr-plugins. Its SKILL.md
and agents/ are replaced.
.PARAMETER Marketplace
The installed claude-plugins-official marketplace.
.EXAMPLE
pwsh -NoProfile -File skills/pull-request/evals/stage-plugin-baseline.ps1
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill pull-request -Runs 3 -SkipTrigger -Baseline "$env:CLAUDE_JOB_DIR/tmp/plugin-baseline/pr-plugins"
#>
[CmdletBinding()]
param(
    [string]$Destination = ($env:CLAUDE_JOB_DIR ? (Join-Path $env:CLAUDE_JOB_DIR 'tmp/plugin-baseline/pr-plugins') : $null),
    [string]$Marketplace = (Join-Path $HOME '.claude/plugins/marketplaces/claude-plugins-official')
)
$ErrorActionPreference = 'Stop'
if (-not $Destination) { throw 'Pass -Destination, or set CLAUDE_JOB_DIR for the default.' }
$plugins = Join-Path $Marketplace 'plugins'
$commands = @(
    @{ Plugin = 'commit-commands'; Command = 'commit' }
    @{ Plugin = 'commit-commands'; Command = 'commit-push-pr' }
    @{ Plugin = 'code-review'; Command = 'code-review' }
    @{ Plugin = 'pr-review-toolkit'; Command = 'review-pr' }
)
$build = (Get-Content -LiteralPath (Join-Path $Marketplace '.gcs-sha') -TotalCount 1).Substring(0, 12)

$descriptions = [Collections.Generic.List[string]]::new()
$sections = foreach ($c in $commands) {
    $text = Get-Content -Raw -LiteralPath (Join-Path $plugins "$($c.Plugin)/commands/$($c.Command).md")
    if ($text -notmatch '(?s)\A---\r?\n(.*?)\r?\n---\r?\n(.*)\z') { throw "No frontmatter in $($c.Plugin)/$($c.Command)" }
    $frontmatter, $body = $Matches[1], $Matches[2]
    if ($frontmatter -notmatch '(?m)^description:\s*"?(.*?)"?\s*$') { throw "No description in $($c.Plugin)/$($c.Command)" }
    $descriptions.Add($Matches[1].TrimEnd('.') + '.')
    $body = $body -replace '!`([^`]+)`', '(expanded: see `## $1` in the input file)' -replace '"\$ARGUMENTS"', '""'
    "## /$($c.Plugin):$($c.Command)`n`n$($body.Trim())`n"
}
$glue = "**Harness glue (not plugin text).** These are the enabled commit-commands, code-review and " +
    "pr-review-toolkit commands (marketplace build $build), verbatim below. Use the one the request " +
    "calls for. A context line marked as expanded was run by the host before you saw it; its output " +
    "is in the input file under a heading with the same command. You cannot launch subagents here: " +
    "where a command says to use an agent, apply that agent's instructions (agents/) yourself. You " +
    "cannot call tools either: where a command says to make tool calls and send no other text, write " +
    "the commands you would run as text, in the format the request asks for."
$skill = @('---', 'name: pr-plugins', "description: `"$($descriptions -join ' ')`"", '---', '', '# PR plugins', '', $glue, '') + $sections

$null = New-Item -ItemType Directory -Path $Destination -Force
$agents = Join-Path $Destination 'agents'
if (Test-Path -LiteralPath $agents) { Remove-Item -LiteralPath $agents -Recurse -Force }
$null = New-Item -ItemType Directory -Path $agents
Set-Content -LiteralPath (Join-Path $Destination 'SKILL.md') -Value ($skill -join "`n") -Encoding utf8NoBOM
Copy-Item -Path (Join-Path $plugins 'pr-review-toolkit/agents/*.md') -Destination $agents
Write-Host "Staged $Destination (build $build): SKILL.md and $(@(Get-ChildItem -LiteralPath $agents).Count) agents"
