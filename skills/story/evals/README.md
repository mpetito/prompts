# story evals

Behaviour cases for the rules in `../SKILL.md`, plus trigger cases. The general suite rules are in
the repository's `docs/evaluating-skills.md`; `skills/pull-request/evals/` is the reference suite.

## Fixtures

Answer runs have no MCP tools, so the s-cases carry what a live session sees:

- `ado-mcp-tools.md` (and `ado-mcp-tools-gateway-only.md`, its gateway half, for s4): the tool
  descriptions and parameter schemas of both Azure DevOps connections, captured read-only on
  2026-10-14. Neither connection presented server-level instructions. The descriptions are
  verbatim; the edits (tool-name prefix, removed schema keys, omitted parameters) are listed at
  the top of each file.
- `kestrel-ledger-snapshot.md` (and `kestrel-ledger-snapshot-gateway.md`, the same results under
  the gateway's tool names): the results of the read-only lookups the skill's step 1 makes, from a
  real project with every project, team, client, person, ticket number, title and id replaced.
  The shape is kept: the team's default area path is the project root, the stories sit four
  levels down, most recent stories have no parent though an open Feature fits them, iterations
  are monthly and named by end date, titles end with the client's ticket key, and the existing
  descriptions are HTML.
- `contact-cases-cold-request.md` (s5): the s1 request with the project and team named and no
  lookups made.
- `runtime-upgrade-request.md` states the process the way the owner's projects run it: Issue sits
  on the Stories backlog with Story Points and has no Acceptance Criteria field.

## Cases

| Case | Rule | Trap in the fixture | Overlap probe and fixes |
| --- | --- | --- | --- |
| s1-contact-cases-on-the-board | none (regression) | Team default area is the root; siblings' area is four levels down; most siblings unparented | Passed unaided on Opus and Sonnet: the tool descriptions and the snapshot were enough. Placement rules dropped from the skill |
| s2-case-routing-ac-user-facing | step 5 | The developer's request is all field API names, a flow, a test class and a change set | Failed unaided on both: tests, coverage and deployment written as acceptance criteria (the archived skill did the same) |
| s3-contact-hub-split | steps 3, 6 | The PM asks for the five-item wish list "as one story"; item 2 already shipped (4936); item 5 waits on another team | Failed unaided on both. Fix 1: the ask was "tracked as one item", which Sonnet split 1 time in 3 unaided. Owner decision D6: propose the split as sibling stories under the existing parent, no new Feature unless asked, and write nothing until the PM confirms; the prompt asks for `Proposed: <type>: <title>` lines |
| s4-refresh-story-markdown-update | step 6 | Only the gateway connection is attached; the story's Description is stored as HTML | Fix 1: with both connections, Opus failed (sent `format: Html` to match the field) but Sonnet passed 2 of 3; with the gateway only, both send an unflagged single-item update, even with the fixture header naming `additionalProperties: false` |
| s5-cold-start-looks-first | step 1 (regression) | Nothing looked up yet: only the tools and the request | Passed unaided in every scorable run on both models: they read team settings or iterations and query the work in flight before writing. Kept so a skill edit can't lose step 1 |
| pos-story-misfiled-as-bug | steps 2, 3, templates | Requester insists on a Bug for a feature that never existed; a 6-7 point estimate | Failed unaided on both (type, points, AC format, headings) |
| pos-tech-debt-oversized-issue | steps 2, 3, templates | A tech lead asks for a story for a runtime upgrade estimated at 20 points | Failed unaided on both (type, `We need` opening, split) |

Decision runs, 3 per arm, objective assertions, all graded with the head manifest; a run fails if
any objective assertion fails. Each cell names the run behind it (`.eval-runs/<run>/story/`, local
and gitignored). With-skill cells are all on the head fixtures and on SKILL.md as of 8e287bf,
whose only later edit (owner decision D7: propose a refine or link of an existing item and write
nothing until it is confirmed) no case exercises; the without-skill cells from `final` are on
older fixtures (next paragraph but one). Two runs were API safeguard
errors ("safeguards flagged this message"), which are unscorable and left out.

| Case | Opus without | Opus with | Sonnet without | Sonnet with |
| --- | --- | --- | --- | --- |
| s1 (regression) | 0/3 (final) | 0/3 (r2b) | 0/3 (final) | 0/3 (r2b 2, r2b2 1) |
| s2 | 3/3 (final) | 0/3 (r2b) | 3/3 (final) | 0/3 (r2b) |
| s3 | 3/3 (r2a) | 0/3 (r2a) | 3/3 (r2a) | 0/3 (r2a) |
| s4 | 3/3 (r2c) | 0/3 (r2b) | 3/3 (r2c) | 0/3 (r2b) |
| s5 (regression) | 0/2 (r2a) | 0/3 (r2a) | 0/3 (r2a) | 0/3 (r2a) |
| pos-story-misfiled-as-bug | 3/3 (final) | 0/3 (r2b) | 3/3 (final) | 0/3 (r2b) |
| pos-tech-debt-oversized-issue | 3/3 (r2a) | 0/3 (r2a) | 3/3 (r2a) | 0/3 (r2a) |

`no-vague-criteria` reads only criteria lines, by the owner's ruling: checkbox items, numbered
items, and any line under an Acceptance Criteria heading. Before the ruling it scanned every
list line and failed one Opus with-skill run (r2a) on an Additional Context bullet ("The tech
lead expects it to be faster, but nobody has committed to a specific improvement"). Regraded
under the scoped guard, that run passes. Of 70 saved outputs, the only other verdict that
changed was a Sonnet without-skill run, whose hit was a "Related Work" note; that run still
fails its case on other assertions.

The without-skill cells from `final` (s1, s2 and pos-story-misfiled, on both models) ran on the
pre-renumber fixtures, before the round-2 edits: the renumbered ticket keys, the rewritten
titles, the "verbatim except" header and the renamed sandbox. Those edits change labels only.
The cells were regraded against the head manifest, and no verdict moved.

Connection choice was probed too: with both connections attached, unaided Opus and Sonnet sent
every write through the connector, whose single-item update has a format field. The skill
therefore only says what to do when a write call has no format field (s4).

Assertion notes:

- `no-vague-criteria` skips balanced quoted spans, so a chat note that quotes the request's "fast
  and intuitive" passes, while `- [ ] The "Export CSV" button works correctly` still fails.
- `ac-no-implementation-terms` also fails test-run and promotion criteria ("All automated tests
  pass", "promoted to production").
- The rich-text checks read a JSON object whose string values may hold braces.
- Call-anchored checks accept `**Call:**`, `Call 1:` and a short tool name. Opus labelled calls
  `**Call 1:**` in one s5 run that looked first. s3's `no-write-before-confirmation` also fails any
  write action (`create`, `add_child`, `update`, `update_batch`, `link`), whatever the label.
- pos-tech-debt-oversized-issue fails a proposed Feature or Epic (`no-new-feature`). It also
  requires the Issue's criteria under a `###` or `####` Acceptance Criteria heading
  (`ac-under-heading`), because the owner's Issue type has no Acceptance Criteria field; in r2a
  this holds in 6 of 6 with-skill outputs and 0 of 6 without.

## Output contract

s-case prompts ask for every tool call as a `Call: <full tool name>` line followed by a fenced
json block. Assertions read the JSON objects: a field object (`{"name": …, "value": …,
"format": …}` or an update `{"path": …}`) is matched as one `{…}` span, so a format flag counts
only on the field it sits on.

## Checks

```sh
"$(uv tool dir)/skill-eval-harness/bin/python" skills/story/evals/check_assertions.py
skill-benchmark validate skills/story/evals/shared-benchmark.json --strict-leakage
```

`check_assertions.py` grades `planted/<case id>/` with the harness's own grader: each `right*.md`
must pass every objective assertion and each `wrong*.md` must fail at least one. The planted
answers are real eval outputs, except four wrong ones that are a passing output with one planted
defect each: s1's root area path and unflagged Description, and s5's reads removed and write
moved first. Ticket keys and titles in planted outputs were renumbered with the fixtures.

## Known gaps

- **Truncated answers.** In one batch run with four eval processes at once, 3 of 9 Opus
  with-skill answers ended "My last answer was stopped partway through" and scored as failures.
  The rerun with `--parallel 2` and nothing else running finished 6 of 6. Read a with-skill
  failure's `output.md` before counting it.
- **API safeguard errors.** Two answer runs returned "safeguards flagged this message" instead of
  an answer. They count as unscorable, not as failures.
- **No Bug-path case.** No case files a real Bug, so the Repro Steps and System Info mapping and the
  Severity value format are unmeasured.
