The runbook change reads well and matches on-call's request. Verdict: approve.

`gh pr review 77 --approve` would be rejected: the PR was opened from your own account (`rowan-ashby`), and GitHub can't let an author approve their own pull request. So I'd leave the verdict as a comment:

```bash
gh pr comment 77 --body "Approved: restart first, then diagnose, with a clear five-minute skip rule."
```

Stop there.
