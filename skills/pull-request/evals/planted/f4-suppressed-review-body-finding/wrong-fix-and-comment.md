Copilot's review body hides one low-confidence finding: `>=` drops the reading at `until`, although `--until` is documented as inclusive. Fix it:

```diff
-        if until is not None and r.taken_at >= until:
+        if until is not None and r.taken_at > until:
```

```bash
git commit -am "fix(export): keep the reading taken exactly at --until"
git push
gh pr comment 71 --body "Addressed Copilot's suppressed comment about the --until boundary in the latest commit: readings at exactly --until are now kept."
```

(no review threads)
