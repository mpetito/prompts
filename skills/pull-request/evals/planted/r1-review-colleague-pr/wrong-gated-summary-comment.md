Two blocking problems: the cache key ignores `url`, and the write isn't atomic.

Draft:

> Thanks, Juno. Blocking: (1) the cache key ignores url, so two URLs share manifest.json; (2) the write truncates the file first, so another worker can read a partial file. Please hash the URL into the name and write via a temp file plus os.replace.

```bash
gh pr comment 42 --body-file review.md
```

I'll post it once you approve the text.
