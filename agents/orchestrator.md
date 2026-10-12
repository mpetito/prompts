---
name: orchestrator
description: Orchestration thread for one multi-agent build, run as a herdr agent in the build's own workspace by the orchestration-main skill (thread.sh launch). Not a subagent; never delegate to it with the Agent tool, because a spawned subagent cannot schedule its own waits or outlive its caller.
model: opus
effort: high
initialPrompt: /agent-orchestration
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: bash "$HOME/.claude/skills/agent-orchestration/hooks/guard-bash.sh"
          timeout: 10
    - matcher: "Edit|Write|MultiEdit|NotebookEdit"
      hooks:
        - type: command
          command: bash "$HOME/.claude/skills/agent-orchestration/hooks/guard-writes.sh"
          timeout: 10
        - type: command
          command: python3 -I "$HOME/.claude/skills/agent-orchestration/hooks/guard-timestamps.py"
          timeout: 10
color: purple
---
