I'd request changes, but as a draft for you first:

- The cache key ignores `url`: two URLs share `manifest.json` (`cache.py:14`).
- The write isn't atomic (`cache.py:22`): a concurrent worker can read a truncated file and treat it as fresh.

```bash
cat > review.json <<'JSON'
{
  "event": "COMMENT",
  "body": "Thanks, Juno. Two things before the workers switch over: the cache key and the write.",
  "comments": [
    {"path": "src/harborfetch/cache.py", "line": 14, "body": "Key the cache file on the URL?"},
    {"path": "src/harborfetch/cache.py", "line": 22, "body": "Write to a temp file and os.replace it?"}
  ]
}
JSON
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews --input review.json
```

Once you're happy with the wording, I'll submit it as one COMMENT review; nothing is sent until then. Shall I post it, or make it a request for changes?
