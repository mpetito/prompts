Verdict: request changes. The cache key ignores `url`, and the write isn't atomic.

```bash
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews -f event=COMMENT -f body="Key issue" -F 'comments[][path]=src/harborfetch/cache.py' -F 'comments[][line]=14' -F 'comments[][body]=This key ignores url.'
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews -f event=COMMENT -f body="Write issue" -F 'comments[][path]=src/harborfetch/cache.py' -F 'comments[][line]=22' -F 'comments[][body]=Use os.replace.'
gh api repos/kestrel-tools/harbor-fetch/pulls/42/reviews -f event=COMMENT -f body="Overall: two fixes needed."
```

I stop here; want me to post these three?
