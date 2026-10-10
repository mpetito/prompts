# Hooks

Claude Code `PreToolUse` hooks from this skill. Paths assume the skill is linked at
`~/.claude/skills/orchestration-ops`; adjust `$HOME` if it lives elsewhere. Hooks read the tool
call as JSON on stdin and answer with `hookSpecificOutput` (a deny with its reason, or extra
context); a silent exit 0 lets the call continue through the normal permission flow
([Claude Code hooks](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)).

## Settings snippet

Merge into `.claude/settings.json` (project) or `~/.claude/settings.json` (user):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash \"$HOME/.claude/skills/orchestration-ops/hooks/guard-bash.sh\"", "timeout": 10 }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "python3 -I \"$HOME/.claude/skills/orchestration-ops/hooks/guard-timestamps.py\"", "timeout": 10 }
        ]
      }
    ]
  }
}
```

## What each hook does

| Hook | Refuses | Why |
| --- | --- | --- |
| `guard-bash.sh` | `pkill …` and `killall …` in command position (a quoted string, a backtick span or a comment that mentions them passes) | Pattern kills have taken out the caller's own shell and another lane's preview server; one stray listener then cost about 30 hours. Kill by PID after reading the command line |
| `guard-bash.sh` | `git worktree remove …` (with or without `-C`) | Removal before the archive step lost lane evidence under `.orchestration/tmp`. `finish-lane.sh` archives, checks for a live agent, then removes |
| `guard-bash.sh` | `rm … .orchestration/lanes/…` and `rm … .orchestration/tmp/…` | Same evidence; archive or move aside instead |
| `guard-bash.sh` (warning only) | nothing; adds context when `/tmp` or `$TMPDIR` is at 70% of its inodes | Full tmpfs produced false test failures across every lane at once |
| `guard-timestamps.py` | A clock time such as `14:30Z`, `07:3xZ` or `T18:16Z` that is new to an `.orchestration/` file, through Edit or Write | Hand-typed times were estimates for hours at a stretch. `state.sh log` stamps the line itself; times already in the file may be moved or quoted |

`guard-timestamps.py` matches paths containing `/.orchestration/`; set `ORCHESTRATION_DIRS` to
colon-separated fragments to watch other directories.

`guard-bash.sh` reads the command text line by line, so a heredoc or script body that starts a
line with one of the refused commands is refused too. Write such a script through the host's
file tools (Write or Edit), which this hook does not see, then run it.

## Checking a hook by hand

```bash
printf '%s' 'git worktree remove ../wt' | jq -Rs '{tool_input:{command:.}}' | bash hooks/guard-bash.sh
jq -n '{tool_input:{file_path:"/repo/.orchestration/state.md",new_string:"done 14:30Z"}}' | python3 -I hooks/guard-timestamps.py
```

Both print a deny object. `tests/run.sh` runs these and the script checks offline.
