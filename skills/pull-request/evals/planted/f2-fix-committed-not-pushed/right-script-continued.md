`4be91c2` is local only (`git status`: ahead of origin by 1), so push it first. Then the skill's script replies on each thread and resolves it.

```bash
git push
python3 "$HOME/.claude/skills/pull-request/scripts/resolve_pr_thread.py" \
  --thread-id=PRRT_kwDOQx7a1M5Tr1Ka \
  --body "Fixed in 4be91c2: fetch_manifest passes timeout to client.get."
python3 "$HOME/.claude/skills/pull-request/scripts/resolve_pr_thread.py" \
  --thread-id "PRRT_kwDOQx7a1M5Tr1Kb" \
  --body "Fixed in 4be91c2: the default is 5.0 seconds now."
```

I stop after the second thread.

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
