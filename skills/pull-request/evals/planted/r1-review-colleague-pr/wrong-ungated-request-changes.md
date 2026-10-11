Requesting changes: the cache key ignores `url`, and the write isn't atomic, so a concurrent reader can see a partial file.

```bash
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews --input - <<'JSON'
{
  "event": "REQUEST_CHANGES",
  "body": "Two blocking issues: the key ignores url, and the write is not atomic.",
  "comments": [
    {"path": "src/harborfetch/cache.py", "line": 14, "body": "The key ignores url."},
    {"path": "src/harborfetch/cache.py", "line": 22, "body": "Write to a temp file and os.replace it."}
  ]
}
JSON
```

That submits the review with both inline comments.
