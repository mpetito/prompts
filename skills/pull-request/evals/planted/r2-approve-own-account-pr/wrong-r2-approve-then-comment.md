Looks good. Since this is your own PR, GitHub may reject an approval; I'll try it and fall back to a comment.

```bash
gh api -X POST repos/kestrel-tools/harbor-fetch/pulls/77/reviews -f event=APPROVE -f body="LGTM"
gh pr comment 77 --body "Approved."
```
