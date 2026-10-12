The thread list is empty, so I read the reviews too:

```bash
gh api graphql -f query='query{repository(owner:"kestrel-tools",name:"tidewater"){pullRequest(number:71){reviews(first:20){nodes{author{login} body}}}}}'
```

Copilot's review has one finding tucked into its collapsed low-confidence section, and it holds: `--until` is documented as inclusive, but `>=` drops the reading taken exactly at `until`.

```diff
-        if until is not None and r.taken_at >= until:
+        if until is not None and r.taken_at > until:
```

```bash
git commit -am "fix(export): keep the reading taken exactly at --until"
git push
```

Stop there; there's no thread to reply to.

(no review threads)
