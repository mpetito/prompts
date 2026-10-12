**Request changes** in substance, but here is a draft for you to check first.

Summary: "Thanks, Juno. The key ignores `url`, and the write can be read half-done by another worker; both need fixing before workers adopt this."

Inline:
- `cache.py:14` "Key this on the URL? Right now every URL shares manifest.json."
- `cache.py:22` "Temp file plus `os.replace`, so readers never see a partial write?"

```bash
gh api -X POST repos/kestrel-tools/harbor-fetch/pulls/42/reviews \
  -f commit_id=f1c27ad -f event=COMMENT \
  -f body="Thanks, Juno. The key ignores url, and the write can be read half-done by another worker; both need fixing before workers adopt this." \
  -F 'comments[][path]=src/harborfetch/cache.py' -F 'comments[][line]=14' -F 'comments[][body]=Key this on the URL? Right now every URL shares manifest.json.' \
  -F 'comments[][path]=src/harborfetch/cache.py' -F 'comments[][line]=22' -F 'comments[][body]=Temp file plus os.replace, so readers never see a partial write?'
```

Want me to post this? I haven't run it; I'm stopping here for your OK on the wording.
