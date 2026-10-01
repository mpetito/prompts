# Adversarial Probes

How to run the proofs that [Prove the Change Can Fail](../SKILL.md#prove-the-change-can-fail)
requires. Work in a scratch copy or worktree. Keep each probe script and its log, so the author
can re-run them.

## Mutants of the Code Under Test

1. List the clauses the change must satisfy: the spec, contract, brief, and PR body.
2. Re-run the author's mutants. Treat their list as a floor.
3. Add at least one mutant of your own per changed module, and one per clause that no assertion
   touches. A mutant is a small, plausible defect in the product code, not in the test: a removed
   check, a flipped condition, an off-by-one, a reordered step, a swallowed error, a changed
   config value the test reads.
4. Add conforming variants: implementations that meet the contract another way (other timing,
   order, or markup). They must still pass. A failure means the test is coupled to one
   implementation.
5. Prefer mutants the pre-change suite would miss. A mutant the old tests already kill says
   little about the new ones.
6. A survivor is a finding, unless it is behaviorally equivalent to the original; then say why.

| Mutant                 | Where                        | Result       | Killing assertion or probe            |
| ---------------------- | ---------------------------- | ------------ | ------------------------------------- |
| M1 drop expiry check   | `session.ts` `isValid`       | killed       | `session.test.ts` "rejects expired"   |
| M2 accept an empty row | `parse.ts` `readRows`        | **survived** | finding B1; probe `probes/m2.test.ts` |

## Restore the Bug

For each proof, regression test, or negative control added to catch a defect, reinstate that
defect (revert the fix or apply the matching mutant) and run the proof. It must fail, and for the
stated reason. A proof that still passes, or fails for an unrelated reason, is vacuous.

Compare the test list or run count before and after the change. A replaced or dropped proof
shows up as a count that did not move.

## Flaky or Timing-Bound Fixes

1. Reproduce on the unfixed code under CI-like load: limit the run to the CI runner's CPU count
   (for example `taskset -c 0,1 <command>` on Linux) and add competing load on the same CPUs.
   Discard any pairing in which the unfixed code did not fail.
2. Size N so the unfixed code should fail about three times: N ≈ 3 / failure rate. A 5% flake
   needs about 60 runs.
3. Report failure counts before and after at that N, on every project or engine CI runs.
4. Ablate: apply each part of the fix alone. A part that changes nothing is not the fix.
5. Instrument the stated cause (a log line, trace, or counter) and confirm it fires in the
   failing runs and not in the passing ones.
6. Reinstate the defect the test guards, and confirm the fixed test still fails on it.

**Relaxed helpers.** When a fix loosens a shared helper (longer waits, forced actions, retries),
collect real-code mutants the old helper caught and confirm the new helper still catches them.
Scope the relaxation to the engine or platform that flakes.

## Dependent and Stacked Changes

- For a change that enables held-back work (skipped tests, a feature flag), check out the
  dependency, overlay this change, and make the enabling edit mechanically. The run count must
  rise, no skips may remain, and the new tests must pass.
- When parallel lanes touch shared code, merge this change with the other lanes' current heads
  locally and run the full local gate, typecheck included.

## Gates, Validators, and Parsers

- Ask for the protected property in one sentence, and the threat model. A missing one is a finding.
- List the bypass classes (aliasing, duplicates, inlining, deferred or async execution, ordering,
  stale artifacts, encoding). Plant one mutant per class in the thing the gate guards: add the
  forbidden import, remove the check, move the code.
- Feed malformed and unexpected input. The gate must fail closed.

## Secrets and Redaction

1. Prove the scanner first: it must flag a planted leak.
2. Plant a synthetic secret, never a real one, and force the failure paths.
3. Scan every sink: stdout and console, error context, logs, traces, test reports (decode embedded
   base64 and archives), build output, and child-process environments.
4. Disable each protection layer in turn (masking, redaction, argument order) and confirm a test
   fails.

## No-Behavior-Change Claims

For comment-only, rename, formatting, and refactor changes, require a mechanical proof and re-run
it yourself:

- identical build or synth output;
- an identical token stream with comments removed, from a comparator that is shown to detect a
  planted change;
- identical test lists.

For comment and documentation passes, check each statement against the code: IDs, section
references, numbers, and side effects.

## Evidence Audit

- Record the commit CI tested against the head under review. Count fresh runs and re-runs
  separately.
- Re-run the author's reported numbers.
- Mark each causal, numeric, and coverage claim in the PR body, README, and linked issues as
  verified, wrong, or unverified.
