---
name: owner-acceptance
description: "Gate 'complete' on the owner's own path, not on green checks: one real browser pass through sign-in, setup and the first action on the deployed environment, a friction checklist for owner-facing screens, and a sample-before-pipeline rule for owner-facing content such as copy, taxonomies and labels. Use whenever a lane, slice or milestone that the owner will see is about to be reported done, deployed or demoed, even in plain words: is the onboarding ready to show, call the milestone complete, deploy the settings page to dev, check the first-run experience, draft the tag list or the onboarding copy, or decide whether the owner needs to look before the pipeline runs. Load it before writing the status that says done. Not for the adversarial code review of the diff (review), or for the deploy mechanics (autonomous-loops)."
---

# Owner Acceptance

In one build, every owner-facing slice was declared complete on CI, reviewer approval and a live
health probe, and the owner then found the gaps on first use: an empty first screen, a setup flow
that asked for things it did not need, a 70-item taxonomy nobody had sampled. Machine evidence
proves the code does what the tests say. This gate proves the owner can use it.

## When to Use

- Before reporting any owner-visible slice as complete, deployed or ready to demo
- Before running a pipeline over owner-facing content (copy, labels, categories, templates)
- When the owner's steer is "show me", "simplest", or "visible progress first"

## Procedure

### 1. Walk the owner's path, in a browser, on the deployed environment

Not a unit test, not a curl. One pass from the entry point the owner uses, by the orchestrator
or a browser-capable agent, with a screenshot or a short transcript per screen:

1. Sign in (or the equivalent entry), including the cold-start case with no data.
2. First-run setup, end to end, with the fewest inputs the product allows.
3. The slice's first real action, then reload: the result is still there.
4. The failure the owner is most likely to hit (a wrong code, an expired link, a slow network),
   and what the screen says then.

Record each step as `path step · observed · screenshot or quote`. A step that cannot be walked
yet is listed as not walked, never as passed.

### 2. Friction check, per screen

Apply each line; a "no" is a finding to fix before "complete", not a note for later:

| Check | Pass when |
| --- | --- |
| One primary action | The screen has one obvious next thing to do, and it is first |
| Short copy | Every sentence earns its place; no explanation the owner did not ask for |
| Never an empty page | A new account sees something useful or a call to action, never a blank list |
| Ends on a call to action | The last screen of a flow says what happens next, with the button to do it |
| Nothing asked twice | No input the product already has or could default |
| Usable one-handed at 375 px | Tap targets and order work on a phone, where the owner will try it |

### 3. Sample before pipeline, for owner-facing content

Before a model, a script or an agent produces a set of content the owner will see (a taxonomy,
interface copy, templates, a label set):

1. Produce 8 to 10 representative samples and show them to the owner in one message, with the
   rule that generated them in one line each.
2. Ask one question with a default: "proceed with this shape unless you object by <time>".
3. Only then run the full set. Anything the owner changes in the sample changes the rule first.

### 4. Report

"Complete" carries the walk and the check, in this shape:

```text
OWNER PATH: walked <date -u> on <environment> at <sha>; steps 1-4 <passed|not walked: reason>
FRICTION: <n> findings <fixed|open: list>
CONTENT: <sampled with owner on <date> | not owner-facing>
```

Anything less is "built and reviewed", which is a different status.

## Common Issues

| Problem | Solution |
| --- | --- |
| The environment is not deployed yet | The slice is not complete; report "built and reviewed, deploy pending" and schedule the walk |
| The walk needs credentials only the owner has | Ask once, with the default of walking with a test account, and keep the status at "built and reviewed" meanwhile |
| The sample review stalls because the owner is away | Default applies at the stated time for content with no safety or legal exposure; everything else waits |
| Reviewers approved and CI is green, so the lane wants to close | Approval is a precondition of this gate, not a substitute; the walk still runs |
