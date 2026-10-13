---
name: orchestrator
description: Orchestration thread for one multi-agent build, run as a herdr agent in the build's own workspace by the orchestration-main skill (thread.py launch). Not a subagent; never delegate to it with the Agent tool, because a spawned subagent cannot schedule its own waits or outlive its caller.
model: opus
effort: high
initialPrompt: /agent-orchestration
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: python3
          args: ["-c", "import os,runpy,sys; p=os.path.expanduser('~/.claude/skills/agent-orchestration/hooks/guard_bash.py'); sys.argv=[p]; runpy.run_path(p, run_name='__main__')"]
          timeout: 10
    - matcher: "Edit|Write|MultiEdit|NotebookEdit"
      hooks:
        - type: command
          command: python3
          args: ["-c", "import os,runpy,sys; p=os.path.expanduser('~/.claude/skills/agent-orchestration/hooks/guard_writes.py'); sys.argv=[p]; runpy.run_path(p, run_name='__main__')"]
          timeout: 10
        - type: command
          command: python3
          args: ["-c", "import os,runpy,sys; p=os.path.expanduser('~/.claude/skills/agent-orchestration/hooks/guard_timestamps.py'); sys.argv=[p]; runpy.run_path(p, run_name='__main__')"]
          timeout: 10
color: purple
---
