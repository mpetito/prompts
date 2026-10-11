# Code-style build: proposed diffs (from the overlap analysis; owner-only ones not applied)

A. Author brief line (skill lane owns this file per plan.md Phase D). Skill name is pending D1.

```diff
--- a/skills/agent-orchestration/references/briefs.md
+++ b/skills/agent-orchestration/references/briefs.md
@@ -32,6 +32,7 @@
 
 ```markdown
 # <lane>: <one-line goal>
+Load the code-style skill before you write code.
 Why: <the owner's or the spec's words, verbatim, with the source>
 Worktree: `git worktree add -b <branch> ../<repo>-wt-<lane> <LANE-BASE from state.sh thread>`; base `<sha>` when sent.
 Owns: <paths>. Never touch: <paths> (owned by <lane>; message the thread with evidence instead).
```

B. CLAUDE.md style line becomes a pointer (owner-only).

```diff
--- a/instructions/CLAUDE.md
+++ b/instructions/CLAUDE.md
@@ -21,8 +21,8 @@
 and the archived skill (if any) that covered it. That ledger is the only way a skill earns
 its way back.
 
-- Follow the target project's conventions first. Keep comments concise; explain only what
-  names, types, and code cannot. These rules also apply to delegated implementation.
+- Before writing or changing code, load the `code-style` skill; a brief that delegates
+  implementation names it too.
 - Before reporting implementation complete, review the final diff yourself: prove every new
   guard or fix can fail (revert it or plant a mutant), run the project's checks, and report
   findings by severity.
```

C. Optional, owner-only: the stale "archived … Nothing auto-loads" sentence that works against B.

```diff
--- a/instructions/CLAUDE.md
+++ b/instructions/CLAUDE.md
@@ -12,7 +12,8 @@
 ## Skills
 
-The skill collection is archived (`archive/skills/` in the configuration repository that this
-file links from; `readlink -f ~/.claude/CLAUDE.md` finds it). Nothing auto-loads. A skill
-returns only through the readmission bar in `docs/skill-audit/readmission.md` there.
+Most of the skill collection is archived (`archive/skills/` in the configuration repository
+that this file links from; `readlink -f ~/.claude/CLAUDE.md` finds it); `skills/` there holds
+the readmitted ones. A skill returns only through the readmission bar in
+`docs/skill-audit/readmission.md` there.
 
 When a task goes wrong in a way an instruction would have prevented, or you find yourself
```

D. Root README coding path.

```diff
--- a/README.md
+++ b/README.md
@@ -65,6 +65,6 @@
-The coding path is `code-authoring` → applicable `code-quality-standards` → `review`, including
-bug fixes and refactors without a spec. Project conventions take precedence over personal
-style; concise comments and reuse are checked during implementation and review. `pr-feedback`
+The coding path is `code-style` → `review`, including bug fixes and refactors without a spec.
+`code-style` holds the personal style rules (project conventions win); `review` judges the
+diff. Worker briefs name the skill because Codex does not load this file. `pr-feedback`
 collects full review bodies as well as threads and verifies visible and suppressed Copilot
 claims before accepting changes. These routes are explicit in skill bodies for other hosts,
 which do not load this Claude-only global file.
```
(`pr-feedback` is archived too; that sentence is stale but outside this brief.)

E. Recommendation, owner-only, `~/.claude/settings.json` (not versioned):

```diff
--- a/.claude/settings.json
+++ b/.claude/settings.json
@@ -1,4 +1,5 @@
 {
   "permissions": {
-    "defaultMode": "auto"
+    "defaultMode": "auto",
+    "deny": ["Agent(pr-review-toolkit:code-simplifier)"]
   },
@@ -37,4 +38,4 @@
     "frontend-design@claude-plugins-official": true,
     "code-review@claude-plugins-official": true,
-    "code-simplifier@claude-plugins-official": true,
+    "code-simplifier@claude-plugins-official": false,
     "playwright@claude-plugins-official": true,
```
Unverified: the docs show `Agent(<name>)` deny rules but no plugin-scoped example. After the change, confirm
that `pr-review-toolkit:code-simplifier` is absent from a new session's agent roster.

F. Not a diff: after the skill lands on main in `/home/mpetito/dev/prompts`, run `setup-skills-link.ps1` so
`~/.agents/skills/code-style` and `~/.claude/skills/code-style` exist. Then check with `ls -la`.
