First I'd read everything Copilot left, threads and review bodies:

```bash
gh api graphql -f query='query{repository(owner:"kestrel-tools",name:"tidewater"){pullRequest(number:71){reviewThreads(first:100){nodes{id isResolved isOutdated}}}}}'
gh api repos/kestrel-tools/tidewater/pulls/71/reviews --paginate --jq '.[].body'
```

No threads, but the review body has one suppressed finding, and it's correct: `--until` is documented as inclusive and issue #70 asks for the reading at B, yet `r.taken_at >= until` drops it.

```diff
-        if until is not None and r.taken_at >= until:
+        if until is not None and r.taken_at > until:
```

```bash
git commit -am "fix(export): keep the reading taken exactly at --until"
git push
```

Stop after the push. A body-only finding has no thread to answer, so nothing gets posted.

(no review threads)
