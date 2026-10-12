Request changes in substance: the cache key ignores `url`, and the write isn't atomic, so a concurrent worker can read a partial file.

This goes as one review with inline comments, not `gh pr comment` and not separate `pulls/42/comments` posts:

```bash
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews --input review.json
```

```json
{
  "event": "COMMENT",
  "body": "Thanks, Juno. Two things before workers adopt this.",
  "comments": [
    {"path": "src/harborfetch/cache.py", "line": 14, "body": "Key the cache file on the URL?"},
    {"path": "src/harborfetch/cache.py", "line": 22, "body": "Temp file plus os.replace?"}
  ]
}
```

Nothing is posted yet; I'll post it once you approve the text.
