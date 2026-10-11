The runbook change is good: restart first, a clear five-minute skip rule, diagnosis afterwards. My verdict is approve.

The PR was opened from `rowan-ashby`, the account `gh` is logged in as, and GitHub doesn't let an author approve their own pull request. So I won't run any approve command (`gh pr review 77 --approve` or `"event": "APPROVE"`). The verdict goes on as a COMMENT review instead:

```bash
gh pr review 77 --comment --body "Approved: restart-first matches on-call's ask, and the skip rule covers a server that just restarted."
```

I stop here: say "post" and I'll run it as written.
