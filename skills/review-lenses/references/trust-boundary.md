# Trust boundary lens

**The question.** Does each guard, check or validation sit where outside input enters, and only
there?

This lens builds on [code-style](../../code-style/SKILL.md) rule 3 (trust your own agents,
scripts and services; validate outside input where it enters) and decides which gates
[review §4](../../review/SKILL.md)'s gate proofs then apply to.

## Where to look

- **Every new or changed guard,** allowlist, refusal, validator or auth check: trace who calls it.
- **Every entry point for outside input:** an HTTP request or webhook body, a user's input or
  upload, a message from a queue others write to, a response from a third party. Follow the input
  from where it enters to where it is used.
- **Who is trusted:** the project's own agents, scripts, services and internal callers, and the
  owner running its tools. Outside input is anything else.

## The evidence a finding carries

- The caller by name, and whether it is trusted.
- For missing validation: the entry point and the path the unvalidated input takes to where it
  is used.
- For a misplaced gate: the gate by location and the trusted caller it stops or slows.

## What the lens does

- Missing validation of outside input is a finding: validate once, where it enters.
- A gate on the project's own callers is a finding: cut it, or turn it into a warning, as
  code-style rule 3 says. Which gates still need review §4's proofs:
  [SKILL.md section 3](../SKILL.md).
- The same input checked again deeper inside trusted code is a finding: keep the check at entry.

## What the lens must not do

- Propose a gate, allowlist or refusal on the project's own callers.

## Tagging

Tag by [review §6](../../review/SKILL.md) or [plan-review step 3](../../plan-review/SKILL.md).
Unvalidated outside input is `blocking` when its path reaches a harmful sink (a query, a shell,
a file path, a redirect, stored data others read) or gives wrong behaviour; otherwise
`follow-up`. A gate on a trusted caller is over-engineering, tagged by its upkeep, and `blocking`
when it refuses work the project's own callers need.
