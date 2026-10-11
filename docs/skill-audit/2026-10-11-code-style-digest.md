# Code-style digest (2026-10-11)

**Skill name:** `code-style` (already used by the harness scaffold, overlap diffs A-F and the
README diff). Alternatives: `pragmatic-code`, `lean-code`.
**Role (worker):** loaded once per lane by Claude subagents and Codex; write or change code the
owner's way: least mechanism, reuse what exists, trust internal callers, comment at contract level.

Sources: `.orchestration/results/` ev-claude (C), ev-codex-gh (G), ev-written (W), overlap (homes),
probe-guards (P). Quotes de-duplicated by session tag + timestamp: S1-S8 are opaque tags local
to this file, one per session, and "PR review" marks an owner comment on a pull request. One
owner message, S3 @ 2026-09-20T15:02:46Z, lists numbered items that back rules 5, 8 and 12. It
counts once. Memories that repeat a typed quote are not counted again.

**Read column 5 as a hypothesis.** It quotes Copilot, Codex or older Claude output, often with
the archived code skills loaded (marked [skill]). Current unaided Opus is unverified until each
rule's without-skill run. Rules 5, 7, 8, 10, 12 and 13 were all drawn with code-authoring loaded,
so the archived wording did not prevent them.

**Probe result (P, 2026-10-11).** Unaided Opus 5.5 added no speculative guards in 0 of 3 clean
runs: no guard, try/except or logging on a helper behind a validated caller, even with
zero-division bait. "Trust internal code" at the line level is therefore **not a gap on Opus**.
The owner's complaints are architecture-level: stored counters and ledgers instead of queue
depth, hardening against a trusted caller, and extra policies, jobs and fallback paths. The traps
below target that level.

**Claude baseline carries CLAUDE.md.** `run-skill-eval.ps1` flags still load `~/.claude/CLAUDE.md`
(probe-verified; `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` turns it off). Its "Follow the target
project's conventions first" and "explain only what names, types, and code cannot" are therefore
in the Claude without-skill arm. For Claude, rule 7's no-narration half is probably already
covered and only the contract-doc and module-header half can discriminate. Codex arms never see
CLAUDE.md.

## Proposed rules (strongest first)

| # | Rule | Evidence | Provenance | What the model did instead | Home | Scope |
|---|---|---|---|---|---|---|
| 1 | Add no stored field, counter, job, option or policy until a real need shows; a later metric will do. | "you're continuing to add extra guardrails where a monitoring metric added _later_ would suffice" (S1, 2026-10-08T18:11:15Z); "Do we even need millisecond formatting?" (PR review, 2025-11-25) | typed | two stored marker fields added to detect a repeated rejection [skill]; a dedicated millisecond-formatting function | skill (review:79-80 judges) | general |
| 2 | Use what exists first: a platform signal (queue depth, existence check), the dependency's API, a stock tool, a shared helper. | "Why do we need a running total at all? We have a queue." (S1, 2026-10-07T11:18:29Z); "Why not use zod here?" (PR review, 2026-02-22) | typed; typed-likely | "The simplest fix is one more stored number, a running total … I recommend yes." [skill]; Codex: "You're right—I overengineered this… the custom Python layer I added" (S5) | skill + pointer to repo REVIEW.md "Primitives to prefer" | general |
| 3 | Treat your own agents, scripts and services as trusted: no allowlists or fail-closed refusals; warn rather than block. | "The orchestrator is not an adversary we're defending against." (this repository, S7, 2026-10-10T19:51:08Z); "This boundary you're requiring is security theater." (Codex, S6, 2026-09-20T02:35:47Z) | typed (memory repeats it) | 9e970ea: `echo "refusing: no /proc or lsof to tell whether a process still runs in $wt; stop it, then pass --force"`; five commits reverted in 682aca7 | skill (review keeps the gate check) | general; untrusted input still validated |
| 4 | Don't wrap an abstraction you already have in an interface, facade, executor map or memo hook. | "do we even need this interface? It seems redundant given the [client library] abstraction." (PR review, 2025-11-14); "This memo hook seems overkill" (PR review, 2025-12-07) | typed; typed-likely | an `I…` interface over the library client, "Enables unit testing with mocks"; `const toolExecutors = { … }` | skill | general |
| 5 | Select behaviour through a registry or handler table and derive lists from it; never switch on names. | "There should be no need for switch statements based on tool name. That's the purpose of a registry." (PR review, 2025-12-09); "restructure to use strategy pattern for operation selection, and avoid deeply nested conditionals" (S3, 2026-09-20T15:02:46Z) | typed-likely; typed | `switch (toolName) { … }` in `executeToolByName`; a Python `if operation in (…):` chain nested 7 deep [skill] | skill | general |
| 6 | No fallback paths or mock data for components you control; use the right path up front and show "unavailable". | "Remove all of these fallbacks - we control the tools." (PR review, 2025-12-07); "If we have a way to do this as a fallback, why wouldn't we just use it upfront in the first place?" (PR review, 2025-11-17) | typed-likely; typed | `if (message.includes("unknown tool") \|\| message.includes("not found")) { …fallback… }`; an exported mock-data array. **Micro-level guards: unaided Opus already complies (probe 0/3, CLAUDE.md off).** It added no guard to a helper behind a validated caller. Fallback paths and mock data remain unverified | skill, only if the fallback trap fails unaided | general |
| 7 | Doc-comment every public contract and open each module with a purpose header; comment the why of algorithms; never narrate internals. | "Public contracts should have doc comments … and algorithms should have comments explaining why." (S1, 2026-10-03T00:13:10Z); "a lack of high level commenting" (S2, 2026-09-29T09:17:45Z) | typed; owner-approved files (one project's AGENTS.md, another's decision log) | Too few: a Codex PR's contracts module, 31 exports and 3 comment lines; too many: one-line doc comments restating internal function names [skill] | skill (CLAUDE.md:24-25 becomes a pointer) | general |
| 8 | Split modules by responsibility: one file per pluggable unit with its spec; split test modules the same way. | "could we separate out all the [units] into their own files … so that this file isn't so long and it's easy to add new [ones]?" (PR review, 2025-11-12); "module scopes are huge … which also applies to the test modules" (S3) | typed | one module with a switch over every unit; a 569-line Python module [skill] | skill | general |
| 9 | Never relax a lint rule or threshold to pass; decompose the code. Leave mechanical checks to the linter. | "this PR cannot be accepted because it modifies eslint rules to relax coding standards." (PR review, 2025-11-24); "No - this is a linter or compiler warning." (S4, 2026-09-20T23:50:17Z) | typed; owner-approved file (a project's eslint.config.mjs) | a PR relaxed eslint rules; kept a naming-case rule as an AI-judged check [skill] | skill; review ("Do not report: what CI enforces") | general |
| 10 | Delete what a change replaces: legacy ops, compatibility shims, redundant calls. No "correct either way" leftovers. | "coordinator reachable legacy ops: remove." (S3, 2026-09-20T15:05:29Z); "We don't need to maintain backwards compatibility." (PR review, 2025-11-14) | typed | "Gate or remove them; not applied because it changes coordinator capability." [skill]; "it's correct either way, just verbose" (this repository, S8) | skill | pre-release, internal |
| 11 | Let the compiler hold invariants (literal key types); no `any`, casts or runtime sync checks. | "casting types to `any` is lazy." (PR review, 2025-11-12); "Couldn't you have used typescript compiler validation … so its key type is the [unit] literals" (PR review, 2025-12-10) | typed; typed-likely | `const resp = response as any;`; a runtime check that the registry matches a list of name constants | skill only if a trap fails unaided ("no `any`" is generic) | TS |
| 12 | Docs and comments describe the code as it is: no history, baselines, "not verified" notes, review files or FIXMEs. | "a lot of documentation states what is not verified, or still has reference to baselines" (S3); "i also caught a few fixmes left in test suites" (S2, 2026-09-29T09:17:45Z) | typed | committed `docs/findings-2026-09-20.md` and review snapshots [skill; CA:141 already said so] | skill | general |
| 13 | Tests locate elements by role or test id and read expected text from the content source; never match copy. | "I'd rather not rely on content text matching for test contract." (S2, 2026-09-27T16:46:04Z) | typed; owner-approved file (a project's decision log) | the 404 page's home-link text and a media toggle's labels as locators [skill] | skill | UI and e2e tests |
| 14 | Log raw internal ids; keep personal data out of logs instead of hashing identifiers. | "It would be absurd to obfuscate them in logs and make any use of the logs that much more difficult." (S1, 2026-10-02T23:29:33Z) | typed (queued mid-turn) | "logs carry no raw internal ids, only a daily-keyed hash." | skill | general |
| 15 | Keep analytics out of entities: record events and derive milestones; no `firstXAt` marker attributes. | "How can we make this so the analytics aren't baked into the model itself?" (S1, 2026-10-02T20:07:14Z) | typed | two milestone marker attributes already on the entity | skill | data modelling |

Size check: 15 rules at 2-4 lines each, plus the description and the trust-boundary exception,
fit a ≤120-line worker body. Rules 14 and 15 rest on single episodes and are the first to cut.

## Considered, not proposed

- Get the feature working end to end first, with stand-ins (C-R11, W-R18): **process**. Home: orchestration briefs and plan-review.
- Choose CDK over SST, an SPA over SSR, minimal dependencies (C-R13, W-R16): **architecture**. The evidence is weak, and the "taste" essay is pasted text with an uncertain author.
- Spend design effort where change is expensive (blast radius) (W-R14): **belongs in review** (review:18-30).
- Never test against possibly stale build output (G-12): typed, in 2 repos, but test infrastructure and rare. Second wave.
- Don't expose config for implementation details; inject the logger and model; no import side effects (G-9): one PR. Second wave.
- Put an interface at a raw external service (repository, classifier) (G-19): one design-doc comment. It is the exception to rule 4, and the skill can state it in one clause.
- Collocate `{module}.test.ts` (G-11): one comment, typed-likely. Usually the repo's own convention.
- LLM apps: pass tools to the agent, keep prompts lean, don't truncate output, keep prompts in their own modules (G-13–15): strong, but **domain-specific**. Candidate `references/llm-apps.md`.
- Magic numbers to named constants (G-16): **generic**.
- Timestamps in UTC (G-17): one comment, and the owner's point about `Date.now` is technically off. Inline `import()` types (G-18): one comment, and a lint rule is its home.
- Debug affordances may ship to prod (C-R14): one case, project-specific. Node scripts over bash (W-R17): pasted brief, uncertain author; repo AGENTS.md.
- **Inferred** from 2019-2023 hand-written code: braceless early returns, argument checks only at public entry points, almost no try/catch (G-20, supports rule 6); table-driven tests (G-22); flat one-off scripts (G-23); sparse internal comments (G-21, supports rule 7). No correction shows a model getting these wrong.
- Dec-2025 preference list (options object past 3 params, no boolean flags, result objects, `interface` vs `type`): inferred; no correction found.
- Archived generic items (naming, map/filter, async, input validation, regex anchors, localStorage, a11y, `use client`): **generic**. Homes: the security-guidance plugin and review, or drop.

## Contradictions

Archived rules the owner's evidence contradicts:
- CA:159-161 "Fail closed … Add a negative case for each bypass class" pushed the hardening that 682aca7 reverted (rule 3). Scope it to untrusted external input, or drop it.
- CQS:315-341 and checklist "Expensive computations memoized (useMemo)", "Callbacks stable (useCallback)" vs "This memo hook seems overkill" (rule 4).
- CQS fetch try/catch (:281-301), the localStorage triple (:94-119) and boundary clamps (:256-279) default to defensive code. That is right at real boundaries and wrong for internal code (rule 6).
- CA:130 "Add public API docs when required by project conventions" is weaker than rule 7.
- CA:201-202 "state-by-event table … One test per cell" runs against rule 1 and "You're spending a ton of time on evals that can all slot in later." (S1, 2026-10-06T10:13:16Z).

Enabled plugins that push the opposite way (all Claude-only; none invoked in the 1,084 retained transcripts):
- silent-failure-hunter: "Silent failures are unacceptable" (:14), "Always log errors" (:92), and it flags optional chaining as error-hiding (:32). That runs against rules 3 and 6.
- comment-analyzer: "Critical assumptions or preconditions are documented" (:31), "least experienced future maintainer" (:41). It wants more comments on internals than rule 7 allows.
- code-simplifier (two identical copies): applies a fixed JS rule set "from CLAUDE.md" (:49-56) against project conventions, prefers "explicit … over overly compact" (:66), and runs on its own after proofs (:88). Overlap diff E (owner-only) disables or denies it.
- type-design-analyzer, mildly: it flags "Anemic domain models" and asks for encapsulation, which leans against rule 4.

Tensions inside the owner's own evidence: rule 4 vs "Interaction with [the third-party classifier] should always be through a Classifier interface" (a project design doc, 2026-10-02). They reconcile: an interface for a raw external service is fine; one over a library that already abstracts the service is not. Global CLAUDE.md:24-25 ("explain only what names, types, and code cannot") is silent on contract docs. Overlap diff B turns it into a pointer.

## Trap ideas (one fixture each; regex pairs are drafts)

1. A notification "on the second rejection", with an event log present. Fail: `not_regex` `(Count|Total|counter)\w*\s*[:=+]|ADD\s+\w+`. Pass: `regex` for the notify call.
2. "Cap waiting items at 1000 per region" on an SQS-backed store. Fail: a new counter field. Pass: `regex` `ApproximateNumberOfMessages|getQueueAttributes`. Variant: zod in package.json and the task is "validate the envelope". Fail: `not_regex` `\[0-9a-f\]|new RegExp`. Pass: `regex` `z\.object\(`.
3. A warn-only hook for a trusted agent plus a "security review" listing bypasses. Fail: `not_regex` `exit 1|realpath|readlink|command -v jq|allowlist`. Pass: `regex` `warn|advis|trust`. A counter-case keeps validation at an untrusted HTTP boundary, so the skill can't pass by deleting needed checks.
4. A third-party SDK client that already abstracts the service, and "add fetchBalance with unit tests". Fail: `not_regex` `interface I[A-Z]\w+|class \w+(Adapter|Facade)|useMemo\(`. Pass: `regex` `\.fetchBalance\(`.
5. A `TOOLS` registry and the task "add a get_news tool". Fail: `not_regex` `switch\s*\(\s*\w*[Nn]ame|case\s+["']get_news`. Pass: `regex` `name:\s*["']get_news`. Python variant: `not_regex` `elif\s+op\w*\s*==`.
6. Not the micro-guard fixture: probe-guards' version passed unaided 3 of 3, so keep it only as a non-discriminating regression case. Instead: a dashboard card fed by an in-repo tool, where the task says "the holdings call can return nothing on a fresh account". Fail: `not_regex` `mock\w*\s*[:=]|fallback|includes\(["'](unknown|not found)`. Pass: `regex` `[Uu]navailable`.
7. New exported contract types plus a jittered backoff. Pass: `regex` `/\*\*` before each `export` and a `//` near the jitter line. Fail: `not_regex` `@param\s+\{|@returns\s+\{`.
8. "Add an indicator" to a 300-line indicator module. Fail: `not_regex` for a new `case "…":` in that file. Pass: `regex` `indicators/\w+\.ts`.
9. An eslint config with `complexity: ["error", 10]` and a function at the limit; the task adds branches. Fail: `not_regex` `eslint-disable|complexity["']?\s*:\s*\[\s*["']\w+["']\s*,\s*(1[1-9]|[2-9]\d)`. Pass: `regex` for an extracted function.
10. Old `createSpec` next to the new collocated specs; the task is "finish the migration". Fail: `not_regex` `createSpec\(|@deprecated|legacy|compat`. Pass: `regex` for the new spec shape.
11. A typed SDK response and a registry keyed by string. Fail: `not_regex` `as any|:\s*any\b|as unknown as|validate\w*Matches`. Pass: `regex` `Record<\w+Name|keyof typeof|satisfies`.
12. "Write the README for this extracted project", with extraction notes in the fixture. Fail: `not_regex` `(?i)not (yet )?verified|baseline|findings-20|FIXME|TODO`. Pass: `regex` `^## `.
13. "Write a Playwright test for the 404 link home". Fail: `not_regex` `getByText\(|text=|toHaveText\(\s*["']`. Pass: `regex` `getByRole\(|getByTestId\(`.
14. "Log the order id when processing fails; ids are internal". Fail: `not_regex` `(?i)hash|sha256|createHmac|redact|mask`. Pass: `regex` `orderId` inside a logger call.
15. "Track when a profile gets its first and third approval". Fail: `not_regex` `(first|third)\w*At\b`. Pass: `regex` for an event item `type:\s*["']\w*[Aa]pprov`.
