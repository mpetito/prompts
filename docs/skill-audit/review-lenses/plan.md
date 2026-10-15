# Plan: review lenses

Spec: [spec.md](spec.md). This plan follows the spec's decisions and its open-question defaults:
no `/simplify` baseline (it has no folder to stage), Opus or a cross-family model per lens
reviewer, and at most four lens reviewers, one per picked lens.

Paths are from the repository root. Per [CONTRIBUTING.md](../../../CONTRIBUTING.md) the work lands
on `main` with Conventional Commits and no AI attribution; an orchestrated build lands each lane's
approved commit there.

## Lanes and file ownership

| Lane | Owns | Must not touch |
| --- | --- | --- |
| `skill` | `skills/review-lenses/SKILL.md`, `skills/review-lenses/references/` | `skills/review-lenses/evals/` |
| `evals` | `skills/review-lenses/evals/` | the skill text (it writes its traps from spec.md alone, so the fixtures do not mirror the wording) |
| `wiring` | `skills/plan-review/SKILL.md`, `skills/review/SKILL.md`, `skills/agent-orchestration/SKILL.md`, `docs/skill-audit/candidates.md`, `README.md` | everything under `skills/review-lenses/` |
| `eval-runner` | steps 8–10: the paid runs, their reading, and `docs/skill-audit/2026-10-15-review-lenses-retrospective.md` | the skill text (fixes go back to `skill`) and the evals (fixes go back to `evals`, only when they trace to spec.md) |

All three lanes start together. The spec fixes the skill's name, the lens names, the `Lenses:`
line and the finding prefix, so `wiring` and `evals` need nothing from `skill` to start. Links
across lanes are checked in step 7, after all three land. `eval-runner` starts once `skill`,
`evals` and `wiring` have landed.

## Amendments from the plan review (2026-10-15)

These override the steps below where they differ.

- A1 (step 3, step 8). Every behaviour case names its discriminating assertions `trap-*`; the
  lens names, `Lenses:` line and prefix alone never discriminate, since the baseline has never
  seen them. Each case also has a `control-*` assertion both arms must pass (plan-review's
  `VERDICT` first line, or review's `Depth:` line). Step 8 passes when a `trap-*` assertion fails
  in every `without_skill` run and every assertion passes in every `with_skill` run. Lens-prefix
  regexes are unanchored (`Reuse · ` anywhere on the line), so they match after a review's own
  finding id. Each pattern is tested on planted replies, one in the trap and one doing the work.
- A2 (step 3). The sibling goes in both arms as its body without frontmatter,
  `fixtures/plan-review-procedure.md` or `fixtures/review-procedure.md`, called "the team's review
  procedure" in the prompt: the harness tells the `without_skill` arm that no skill files are
  present, and any read of a path containing `SKILL.md` counts as a skill invocation.
- A3 (step 3, `pos-pick-lenses`). The change has hand-rolled date or retry logic inside an
  existing function (no new helper), an outbound public event schema (blast radius high), and a
  fixture that states nothing reads outside input. The prompt casts the model as a coordinator
  and asks for the reviewer briefs as text (eval runs deny the Agent tool). The explicit-model
  assertion is not a discriminator.
- A4 (step 3). Before step 8, the `evals` lane runs one `without_skill`-only smoke of its cases
  (at most USD 3) and tightens any trap the sibling alone already avoids.
- A5 (step 2). Reuse deletes obsolete internal code in the same change, per
  [code-style rule 6](../../../skills/code-style/SKILL.md); a published API keeps its deprecation
  path. Reversibility's decide-now list is the blast-radius list in plan-review step 2 and review
  §2, by link; the lens adds the defer half and each deferral's signal. Reuse and Adopt link
  code-style rules 2 and 6. Links from `references/` use `../../<skill>/SKILL.md`.
- A6 (step 1). The check also asserts the first body line is `Role: worker.`
- A7 (step 4). The numstat check runs against the base: `git diff --numstat e646294 --`.
- A8 (steps 5, 6). The unittest suites never read these files; the checks are greps for the new
  lines and the link check on `README.md`. Step 6 drops the lens-mapping ledger entry; the
  Reversibility gap entry stays.
- A9 (step 7). The skill link waits until steps 8 and 9 pass and MAIN has merged the build;
  MAIN runs `setup_skills_link.py` from the owner's checkout, which it links from.
- A10 (steps 8, 9). Pin `--effort high` in every arm. Before step 8, refresh the sibling copies in
  the fixtures from the wired siblings. The Codex run passes `--skip-judge` or a Codex
  `--judge-model`. Step 9 covers plan-review and review only (the spec asks for no
  agent-orchestration regression), on `--model opus --skip-trigger`, baseline `e646294`, the
  pre-wiring revision. Spend for steps 8 and 9: cap USD 60, check in with the thread at USD 40.

## Steps

- [ ] 1. `skills/review-lenses/SKILL.md`: frontmatter and body. Description under about 900
  characters: what it does; "Use when" a review request or brief asks for a lens, asks whether
  something in the repository or a library already does what a plan or change under review
  builds, asks what in a plan or change to decide now versus defer, or asks whether a change's
  guards sit at the right boundary; "Not for" a general plan review (plan-review), a general code
  review or merge verdict (review), writing or changing the code (code-style), and researching a
  library on its own (researcher agent). Body line one: `Role: worker.`, under 120 lines.
  Sections: picking lenses (signals table, named-lens override, the `Lenses:` line in the spec's
  exact form), running them by depth (inline; one reviewer per lens on explicit Opus or a
  cross-family model, at most four; a delegated reviewer never starts reviewers), settling
  conflicts (including the spec's rule on review's gate proofs), finding format (the spec's
  `<Lens> · <tag> · <location>: <issue>` prefix, the review's tags, the lens's evidence rule), and
  one link per lens. No `model` key (it is read inside another task). Check: `python3 -c "import
  yaml; t=open('skills/review-lenses/SKILL.md').read().split('---')[1]; d=yaml.safe_load(t);
  assert d['name']=='review-lenses' and len(d['description'])<=900"` passes (PyYAML 6.0.3 is
  installed), and `wc -l skills/review-lenses/SKILL.md` is under 120.
- [ ] 2. `skills/review-lenses/references/{reuse,adopt,reversibility,trust-boundary}.md`: one
  file per lens, each with: the question, where to look (for Reuse, search the repository beyond
  the changed files for the same responsibility by name and by behaviour; for Adopt, the
  manifest's dependencies first), the evidence a finding must carry, what the lens must not do
  (Reversibility: no guard, counter, option or abstraction for anything reversible; Adopt: no
  library fact from memory, marked unverified when it could not be checked; Trust: no gate on the
  project's own callers), and tagging guidance. Reuse says the obsolete path is deleted in the
  same change, not deprecated or left for later. Each links to, rather than restates, the
  existing guidance it builds on: Reversibility to review's interface design review and
  plan-review's blast radius step; Reuse and Adopt to plan-review's mechanisms step and review's
  over-engineering rule; Trust to code-style's trust rule. Check: the link check below passes on
  `skills/review-lenses/`, and each file is under 100 lines or opens with a table of contents.
- [ ] 3. `skills/review-lenses/evals/fixtures/`, `skills/review-lenses/evals/shared-benchmark.json`
  (format: `skills/plan-review/evals/shared-benchmark.json`). **The sibling is in both arms:** each
  plan case's fixtures include a verbatim copy of `skills/plan-review/SKILL.md`, and each diff
  case's a copy of `skills/review/SKILL.md`, and the prompt says to follow it. `without_skill`
  then means the sibling alone, and a pass measures what the lenses add (readmission item 4).
  Each case has a trap that a model following the sibling alone plausibly falls into, regex
  assertions that use the spec's literal lens names, `Lenses:` line and `<Lens> · ` prefix, and a
  judge rubric. Prompts read: "Read the input files; a read-only command such as cat is fine for
  that, but do not change any file or run anything else."
  - `pos-reuse-plan`: a plan plus a repository excerpt with an existing helper the plan
    duplicates under a different name, and an old path the change makes obsolete. Discriminating
    assertion: the obsolete path is deleted in the same change, never deprecated or left for
    later. Secondary: names the existing file and proposes extending it for both callers.
  - `pos-adopt-diff`: a diff hand-rolling envelope validation, date arithmetic and retry with
    backoff, with a manifest listing a schema validator and a date library but nothing for
    retry. Pass: the two existing dependencies are named for the first two pieces; any library
    proposed for retry has its version or maintenance marked unverified (the run has no network).
  - `pos-reversibility-plan`: a plan that leaves a public event payload "to implementation" and
    adds a stored retry counter "for future needs". Pass: the payload is decide-now, naming its
    dependents; the counter is deferred, naming the signal that would bring it back; no new guard
    is proposed for it. This is the over-correction trap.
  - `pos-trust-boundary-diff`: a diff that adds an allowlist refusing the project's own
    orchestration script while passing an inbound webhook body through unvalidated. Pass: the
    allowlist is cut rather than given bypass-class mutants, and validation is added at the
    webhook's entry.
  - `pos-pick-lenses`: a coordinator prompt with a change whose signals call for exactly
    Reversibility and Adopt (a new public schema and a hand-rolled parser, no new helper beside
    an existing one, no outside input). Pass: the `Lenses:` line picks those two and skips Reuse
    and Trust boundary, each with a reason, and the briefs give one reviewer per picked lens on
    an explicit model.
  - Trigger cases. Should-fire, review-scoped and in people's words: "review this plan for
    anything we already have in the repo or could get from a library", "run the adopt lens on
    this diff", "in this plan, what should we decide now and what can wait?". Should-not-fire
    from the Not-for clause: "review my staged changes", "review this plan before we start",
    "research which CSV library to use", and the code-style near-miss "add a date helper to
    utils".
  Check: `python3 -c "import json,re,os; d=json.load(open('skills/review-lenses/evals/shared-benchmark.json')); [os.stat('skills/review-lenses/evals/'+f) for c in d['cases'] for f in c.get('files',[])]; [re.compile(a['pattern']) for c in d['cases'] for a in c.get('assertions',[]) if a['type']=='regex']"`
  passes.
- [ ] 4. `skills/plan-review/SKILL.md`, `skills/review/SKILL.md`: one short pointer each, in the
  sizing step (review §2) and before the checks (plan-review step 2): pick lenses from
  `../review-lenses/SKILL.md` and put the spec's `Lenses:` line in the report; each report
  template gains that line. In review §4, the gate row's proofs apply to gates the Trust boundary
  lens keeps (one clause). No existing guidance moves or is removed. Check: `git diff --numstat`
  on both files shows 0 deleted lines except the one §4 row it amends; plan-review stays under
  120 lines; review grows by at most 4 lines.
- [ ] 5. `skills/agent-orchestration/SKILL.md`: one line in "5. Reviews, merges and releases":
  a reviewer's brief names its lenses from review-lenses. Check: the line is present, and
  `python3 -m unittest discover -s skills/agent-orchestration/tests -t skills/agent-orchestration`
  passes.
- [ ] 6. `docs/skill-audit/candidates.md`: an entry dated 2026-10-15 recording the owner's
  acceptance of the Reversibility gap as known, and mapping the existing entries to the lenses as
  the spec does (`reuse` to Adopt; `dead code` and `dispatch` to Reuse; `least mechanism` to both;
  `trust` to Trust boundary). `README.md`: a row for review-lenses in the skills table, and the
  "how the pieces fit" paragraph routes plan-review and review to it. Check:
  `python3 -m unittest discover -s tests -t .` passes.
- [ ] 7. After all lanes land: the link check below passes on `skills/review-lenses/`,
  `skills/plan-review/`, `skills/review/` and `skills/agent-orchestration/SKILL.md`. Then MAIN,
  with the owner's approval of the link change, runs `python3 setup_skills_link.py` and
  `python3 verify_setup.py`. Check: both pass and `verify_setup.py` reports review-lenses linked.
- [ ] 8. Eval run: `python3 scripts/run_skill_eval.py --skill review-lenses --runs 3
  --trigger-runs 3 --model opus`, then one `--agent codex --runs 1 --skip-trigger` run with a
  Codex model and `--effort` per `docs/evaluating-skills.md`, "Running on Codex". Read the
  outputs before trusting a failure. Iterate on the skill text (lane `skill`), never by widening
  an assertion after the fact unless it traces to a stated rule and an existing trap. Check:
  every behaviour case fails at least one assertion in every `without_skill` run and passes in
  `with_skill`; trigger rates recorded.
- [ ] 9. Regression: run plan-review's, review's and agent-orchestration's suites with the
  pre-wiring revision as `--baseline` (`docs/evaluating-skills.md`, "Compare against an earlier
  revision"; agent-orchestration on `--model opus --effort high`). Check: no `with_skill`
  objective rate drops below its baseline arm's, after reading every failed output (three runs
  are noisy; a drop that the outputs show is noise is recorded as such, not called a regression).
- [ ] 10. `docs/skill-audit/2026-10-15-review-lenses-retrospective.md`: the eval numbers, the
  baseline comparisons, the `/simplify` comparison recorded as not runnable, what changed during
  iteration, and the 30-day load check date (2026-11-14, `python3 scripts/skill_usage.py`).
  Check: the file cites the run directories' timestamps and every number matches
  `benchmark.json`.

## Link check

Every relative Markdown link target resolves from the file that holds it:

```sh
python3 - <paths> <<'EOF'
import os, re, sys
bad = []
for root in sys.argv[1:]:
    files = [root] if root.endswith('.md') else [os.path.join(d, f) for d, _, fs in os.walk(root) if 'evals' not in d for f in fs if f.endswith('.md')]
    for f in files:
        for t in re.findall(r'\]\(([^)#\s]+)', open(f).read()):
            if '://' not in t and not os.path.exists(os.path.join(os.path.dirname(f), t)):
                bad.append(f'{f}: {t}')
print('\n'.join(bad) or 'LINKS OK'); sys.exit(bool(bad))
EOF
```
