# upgrade

Verdict: **needs-work** · SKILL.md body 393 lines · description 277 chars

The skill is organized well. A four-phase overview table leads into clear per-phase steps, and a checkpoint, validate, commit-or-rollback loop handles the fragile implement step. Per-ecosystem commands sit in one reference file, one level deep from SKILL.md. The biggest gap is concision. About a third of the 393-line body is generic upgrade knowledge that Opus and Sonnet already have: classification and breaking-change taxonomies, migration-pattern examples, error-handling tips and CVE response times. On top of that, five overlapping output templates and a description with no "Not for" clause leave the skill both long and imprecise to trigger.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Names npm, .NET, CVEs and major-version upgrades. Missing: framework or runtime retargeting (.NET 6 to 8, React or Next out of support), pnpm and yarn, and npm audit findings, all of which the trigger evals exercise. |
| Description includes both what the Skill does and when to use it | partial | Has a what clause and a "Use when" clause. It lacks the collection's "Not for … (other-skill)" clause, although the evals carry negative cases owned by research, commit and code-authoring. |
| SKILL.md body is under 500 lines | pass | 393 body lines (397 total minus 4 frontmatter lines). |
| Additional details are in separate files (if needed) | partial | Commands are already in references/ecosystem-commands.md. The five output templates and the Error Handling playbook stay inline and would load only when needed if moved out. |
| No time-sensitive information (or in an "old patterns" section) | partial | The reference uses `npx eslint . --ext .ts,.tsx`, which ESLint 9 flat config rejects, and "(npm 7+)" version notes. The inventory example's "Node engine: >=18.0.0" will date. |
| Consistent terminology throughout | partial | "npm" is used both as the ecosystem name and as the package manager. Commit ownership is inconsistent: Phase 3 commits per group, while Output Format says "Suggest `/commit`". Checkpoint offers "git stash or commit". |
| Examples are concrete, not abstract | pass | The templates carry concrete sample rows (lodash CVE, the risk-assessment items). |
| File references are one level deep | pass | SKILL.md links references/ecosystem-commands.md directly. The reference links nothing further. Cross-skill links are skill-relative, per collection convention. |
| Progressive disclosure used appropriately | partial | Commands are disclosed progressively. Templates and the generic troubleshooting are not, although they are needed only at specific phases. |
| Workflows have clear steps | pass | Four phases, an Execution Order loop and checklists per phase. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No "voodoo constants" (all values justified) | not-applicable | No scripts. The CVE response times are policy, not constants. |
| Required packages listed in instructions and verified as available | partial | Assumes npm and the dotnet CLI without detecting the package manager from the lockfile. pnpm and yarn projects get npm commands. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | Phase 3 runs build and unit tests per group with rollback on failure. Phase 4 has a full validation checklist. |
| Feedback loops included for quality-critical tasks | pass | "Commit if passing, rollback if failing" plus Failure Investigation. |
| At least three evaluations created | partial | 8 cases (5 trigger, 3 negative-trigger), but all are kind "trigger" with empty assertions. No case tests the procedure's behaviour against without_skill. |
| Tested with real usage scenarios | partial | The trigger prompts are realistic. No behavioural scenarios exist. |

## Findings

1. **high** · Concise is key ("Default assumption: Claude is already very smart") · SKILL.md: Phase 1 Classification; Phase 2 Breaking Change Categories; Breaking Change Handling > Common Migration Patterns; Error Handling; Security Considerations > CVE Response Priority
   > | Renamed export      | `import { old } from 'pkg'` | `import { new } from 'pkg'`      |
1. Clear node_modules: `rm -rf node_modules && npm install`

   Fix: Delete the Classification table (the Prioritization Strategy already orders by security, patch, minor, major), the Breaking Change Categories and Common Migration Patterns tables, and the generic Error Handling playbook. Fold the one non-obvious peer-conflict rule (upgrade the requiring package first) into Phase 3. Opus and Sonnet already know these taxonomies and troubleshooting steps. (about 1100 tokens saved)

2. **medium** · Template pattern / Progressive disclosure (Pattern 3, conditional details) · SKILL.md: Inventory Output Template, Risk Assessment Template, Validation Report Template, Deferred block, Output Format
   > ### Validation Report Template … ### Status: PASS
## Upgrade Summary … ### Validation - [ ] Tests passing

   Fix: Keep only the final Upgrade Summary inline, and add the Phase 4 checklist to it so the validation items are not listed twice. Move the inventory, risk-assessment and deferred templates to references/templates.md and link them from the phase that produces each. Mark them as flexible defaults. (about 450 tokens saved)

3. **medium** · Writing effective descriptions (be specific, include key terms and triggers); collection convention of a "Not for … (other-skill)" clause · SKILL.md frontmatter description
   > "Upgrade dependencies across npm and .NET … or planning a major-version upgrade."

   Fix: Add triggers that the evals exercise but the description lacks: moving a framework or runtime off an out-of-support version (React, Next, .NET 6 to 8), clearing npm audit findings, and pnpm and yarn. End with "Not for choosing a library for a new project (research), adding a new dependency in feature work (code-authoring), or committing finished lockfile changes (commit)."

4. **medium** · Set appropriate degrees of freedom (low freedom for fragile operations) / Avoid offering too many options · SKILL.md: Error Handling > "Peer dependency conflict"; Security Considerations > CVE Response Priority; references/ecosystem-commands.md: Peer Dependency Conflicts, Security Audit, Migration Automation
   > 3. Use `--legacy-peer-deps` as a temporary workaround
| Critical | Immediate | Hotfix, bypass normal process if needed |

   Fix: Treat `--legacy-peer-deps`, `--force`, `npm audit fix --force` and the blind `xargs sed -i` replace as ask-first escape hatches, not ordinary options, and say that in Boundaries. Remove "bypass normal process", which contradicts "Never: Skip validation".

5. **medium** · Use consistent terminology · SKILL.md: Phase 3 Principles and Execution Order vs Output Format
   > 1. Create checkpoint (git stash or commit) … 6. Commit if passing, rollback if failing
Suggest `/commit` to commit changes and create/update a pull request.

   Fix: Pick one model: either commit per upgrade group in Phase 3 (the checkpoint is a commit), or leave all committing to the commit skill at the end. State it once, and drop the duplicate Commit Message Format if commit owns messages. (about 80 tokens saved)

6. **low** · Avoid assuming tools are installed / Package dependencies · SKILL.md: Constraint Checklist, Execution Order step 3; references/ecosystem-commands.md header
   > - [ ] Lockfile state (`package-lock.json`, `packages.lock.json`)
3. Update lockfile (npm install / dotnet restore)

   Fix: Add one line saying to detect the package manager from the lockfile (package-lock.json, pnpm-lock.yaml, yarn.lock, packages.lock.json) and use that manager's equivalent commands. Avoid hard-coding npm in SKILL.md, since the reference is meant to hold commands.

7. **low** · Structure longer reference files with a table of contents; Avoid time-sensitive information · references/ecosystem-commands.md (208 lines)
   > Commands are shown for PowerShell but work in any shell unless noted.
npx eslint . --ext .ts,.tsx

   Fix: Add a short contents list of its six sections at the top. Delete the Security Audit section and the overlapping per-phase lines that repeat the Quick Reference table. Drop the inaccurate PowerShell claim: grep, xargs and sed are POSIX. Replace `--ext`, which ESLint 9 flat config rejects, with `npx eslint .`.

8. **low** · Build evaluations first (evaluation structure with expected_behavior) / Checklist: At least three evaluations · evals/shared-benchmark.json
   > "kind": "trigger" … "assertions": []

   Fix: The suite tests only triggering, so the with-versus-without delta that CONTRIBUTING.md uses to judge removal cannot be measured for the body. Add two or three behavioural cases with assertions, for example: researches the changelog before a major bump, keeps the lockfile in sync, and asks before a major upgrade.

## Strengths

- A four-row phase overview table up front gives the whole workflow at a glance before any detail.
- The fragile implement step is a pseudocode loop with a built-in feedback loop: checkpoint, update the manifest, update the lockfile, run quick validation, then commit or roll back.
- Per-ecosystem commands sit in one reference file linked from each phase by section name ("see **Phase 2** in references/ecosystem-commands.md"), with an explicit instruction to consult it rather than recall flags.

## Cut candidates

- Phase 1: Inventory & Plan > Classification (duplicates Prioritization Strategy)
- Phase 2: Research & Risk > Breaking Change Categories
- Phase 3: Implement > Principles (restates the Execution Order)
- Phase 4: Validation > Failure Investigation (overlaps Error Handling "Tests fail after upgrade")
- Security Considerations > CVE Response Priority
- Breaking Change Handling > Common Migration Patterns
- Breaking Change Handling > When to Defer Major Upgrades
- Error Handling (all four generic playbooks)
- Phase 4: Validation > Validation Report Template (duplicates Output Format)
- references/ecosystem-commands.md > Security Audit (duplicates Phase 1 and Phase 4 commands)
