# Project-agnostic build retrospective (2026-10-11)

The repository is public and its skills are used in professional work, so the owner asked that
no file and no commit name a personal project, and that project-specific evidence live elsewhere.

## What changed

- **Current files:** 18 files generalized by hand in one reviewed lane (three fix rounds, two reviews):
  evidence now says what happened, with "a project" or a count in place of a name; session ids,
  pull request numbers and product details went to a private evidence store outside the
  repository, each entry pointing back to the generalized text. One file was renamed.
- **Employer detail:** client names, the employer's own product examples and an IAM policy file
  with infrastructure ids were removed or replaced with fictional examples, on the owner's calls.
- **Rules going forward:** `readmission.md`, the `candidates.md` format and `instructions/CLAUDE.md`
  now say entries describe the kind of gap with "a project", and that names, session ids and
  pull request links go to the private store. No in-repo guard lists the names; the search
  lists live only in the store.
- **History:** every commit's content, paths and messages rewritten with `git filter-repo`
  (replacements, whole-file replacement for the four docs dense with project detail, one path
  rename, one path removal). Commit counts and dates unchanged, and authors too apart from the five re-authored commits below; signatures dropped;
  every hash changed; SHAs cited in current docs updated from the commit map. Fully merged
  branches were deleted instead of rewritten. A bundle of the original history is the rollback,
  kept only in the private store.

## What the reviews caught

- The inventory missed files a plain name search later found, and the scrub found more names in
  the inventory's own files: one pass is never complete; the search lists grew in four rounds.
- The plan review moved the push to the very end (a miss after a force push costs a second
  force push, which publishes another old SHA) and gave the apply a freeze and tip checks.
- The dry-run review found that a names-only rewrite leaves product detail in the history of
  docs the hand scrub had cleaned on the tip. Fixed as a class: whole-file replacement for the
  dense docs, and a check that no line the scrub removed survives anywhere in history.
- A review caught a `set -e` gap: `test A && test B` does not abort when `A` fails.
- Nobody caught, until the final post-apply look: a reviewer's `cp -a` scratch copy of a linked
  worktree kept its `.git` pointer, so the reviewer's test identity went into the live repo's
  config and five commits carried it. Re-authored locally before the push (same trees), and
  recorded in `candidates.md` as a fix for the orchestration brief guidance.

## Cost

Nine Opus workers plus one owner-approved re-author pass (inventory, research, plan review, scrub author and reviewer, dry-run author and
reviewer, final verify), about 1.5M worker tokens, no eval spend. Four review rounds landed fixes;
the rewrite itself takes under two seconds.

## Left as is

- The owner's kept evidence branch cites one commit by its old hash; it gets no commits.
- Whole-file replacement makes those four docs anachronistic in old commits (a later version
  appears from the first commit that had the file).
- Four commits became empty once their edits were folded into history; they stay, so commit
  counts are unchanged.
- The orchestration `state.sh set` treats a lane row whose agent cell is `-` as a separator and
  refuses to update it; use a placeholder such as `tbd` until the script is fixed.

## Reuse

- Scrub the tip by hand first, then rewrite history; gate the apply on "tip tree unchanged".
- Keep search lists, replacement rules and the scripts in the private store; a check whose own
  text lists the names would republish them.
- Check removed lines, not only names: product detail rarely contains the project's name.
- Before force-pushing a public repo, read GitHub's sensitive-data guide: old commits stay
  reachable by SHA, through pull request refs and the activity view, and Support won't remove
  non-sensitive data.
