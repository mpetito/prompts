Verdict: request changes. Two defects, plus a scope question.

1. **The cache key ignores `url`** (`cache.py:14`): every URL shares `manifest.json`, so a call for a second URL within 15 minutes returns the first URL's manifest.
2. **The write isn't atomic** (`cache.py:22-23`): `open(path, "w")` truncates and refreshes the mtime first, so a worker reading at that moment gets an empty or partial file it treats as fresh, and every call fails with `JSONDecodeError` for the next 15 minutes. `CLAUDE.md` asks for shared files to stay readable while another worker writes them.
3. **Scope:** the 02:00 load in `docs/operations.md` starts 40 workers on a cache that is a day old, so this doesn't help there. Worth saying so in the description.

Draft review (summary plus inline comments, as one review):

> Thanks, Juno. Two things to fix before the workers switch over, plus a question about the 02:00 start.

- `src/harborfetch/cache.py` line 14: "This key ignores `url`, so two URLs share one cache file. Hash the URL into the filename?"
- `src/harborfetch/cache.py` line 22: "Write to a temp file in `CACHE_DIR` and `os.replace` it, so a concurrent reader never sees a partial file?"
- `tests/test_cache.py` line 18: "Can we cover an expired entry and a corrupt file too?"

```bash
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews --input review.json
```

with `review.json`:

```json
{
  "commit_id": "f1c27ad",
  "event": "COMMENT",
  "body": "Thanks, Juno. Two things to fix before the workers switch over, plus a question about the 02:00 start.",
  "comments": [
    {"path": "src/harborfetch/cache.py", "line": 14, "body": "This key ignores `url`, so two URLs share one cache file. Hash the URL into the filename?"},
    {"path": "src/harborfetch/cache.py", "line": 22, "body": "Write to a temp file in `CACHE_DIR` and `os.replace` it, so a concurrent reader never sees a partial file?"},
    {"path": "tests/test_cache.py", "line": 18, "body": "Can we cover an expired entry and a corrupt file too?"}
  ]
}
```

I stop here: nothing is posted yet. I'll post it once you approve the text. It goes as a COMMENT review unless you pick another event.

Posted text will match the draft above exactly.
