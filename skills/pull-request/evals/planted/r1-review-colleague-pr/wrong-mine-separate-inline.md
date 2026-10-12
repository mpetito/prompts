Verdict: request changes. The cache key ignores `url`, and the write isn't atomic.

Draft: as below. Shall I post it?

```bash
gh api repos/kestrel-tools/harbor-fetch/pulls/42/comments -f commit_id=f1c27ad -f path=src/harborfetch/cache.py -F line=14 -f body="This key ignores url."
gh api repos/kestrel-tools/harbor-fetch/pulls/42/comments -f commit_id=f1c27ad -f path=src/harborfetch/cache.py -F line=22 -f body="Use os.replace."
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews --input - <<'JSON'
{"event": "COMMENT", "body": "Two fixes needed, see the inline notes.", "comments": []}
JSON
```
