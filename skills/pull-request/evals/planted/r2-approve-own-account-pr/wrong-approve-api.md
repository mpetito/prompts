The runbook change is good, so approve it.

```bash
gh api repos/kestrel-tools/harbor-fetch/pulls/77/reviews -f event=APPROVE -f body="LGTM: restart first, then diagnose."
```

That approves PR 77.
