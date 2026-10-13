---
name: lane
description: One lane of an orchestrated build, run as a herdr agent in its own worktree by the orchestration thread (lane.py). Not a subagent; never delegate to it with the Agent tool.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: python3 "$HOME/.claude/skills/agent-orchestration/hooks/guard_bash.py" --lane
          timeout: 10
    - matcher: "Edit|Write|MultiEdit|NotebookEdit"
      hooks:
        - type: command
          command: python3 "$HOME/.claude/skills/agent-orchestration/hooks/guard_writes.py" --lane
          timeout: 10
color: cyan
---
