The thread list is empty, but Copilot's review body has one finding in its collapsed "Comments suppressed due to low confidence" section, and it's right: the help text, the docstring and issue #70 all say `--until` is inclusive, while `r.taken_at >= until` skips a reading taken exactly at `until`.

```diff
-        if until is not None and r.taken_at >= until:
+        if until is not None and r.taken_at > until:
             continue
```

And a test that a reading at exactly `until` is written:

```diff
+def test_until_keeps_the_boundary_reading():
+    out = io.StringIO()
+    assert export_readings([r(1), r(2), r(3)], out, until=r(2).taken_at) == 2
```

```bash
pytest
git commit -am "fix(export): keep the reading taken exactly at --until"
git push
```

That's where I stop. The finding came from the review body, not a thread, so there's nothing to reply to or resolve, and it doesn't need a new comment on the PR; the commit speaks for it.

(no review threads)
