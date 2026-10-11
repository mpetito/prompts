```bash
gh pr comment 42 --body "### Code review

Found 2 issues:

1. The cache key ignores the url argument, so every URL shares manifest.json (bug due to cache.py: path = os.path.join(CACHE_DIR, \"manifest.json\"))

https://github.com/kestrel-tools/harbor-fetch/blob/f1c27ad/src/harborfetch/cache.py#L13-L15

2. The cache write is not atomic, so a concurrent worker can read a partial file (CLAUDE.md says \"any shared file they write must stay readable while another worker writes it\")

https://github.com/kestrel-tools/harbor-fetch/blob/f1c27ad/src/harborfetch/cache.py#L21-L24

🤖 Generated with [Claude Code](https://claude.ai/code)"
```

Posted the review to PR 42.
