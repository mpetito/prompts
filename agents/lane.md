---
name: lane
description: One lane of an orchestrated build, run as a herdr agent in its own worktree by the orchestration thread (lane.sh). Not a subagent; never delegate to it with the Agent tool.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: bash "$HOME/.claude/skills/agent-orchestration/hooks/guard-bash.sh" --lane
          timeout: 10
    - matcher: "Edit|Write|MultiEdit|NotebookEdit"
      hooks:
        - type: command
          command: bash "$HOME/.claude/skills/agent-orchestration/hooks/guard-writes.sh" --lane
          timeout: 10
color: cyan
---
