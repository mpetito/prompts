# Readmission candidates

One entry per observed gap: a session where the model, without a skill, did something an
instruction would have prevented, or re-derived a procedure or fact a skill used to carry.
Newest last. An entry is the only way a skill enters review; three evals and the rest of the
[bar](readmission.md) follow.

Format: `YYYY-MM-DD · kind of gap · what went wrong, in "a project" or "this repository" (quote the wrong output) · archived skill that covered it, or "new"`

An entry never names a project and carries no session id, PR or review-comment link, or
project commit; "a project" or a count stands in. Those details go to the private evidence
store (`~/dev/prompts-evidence`), never into this repository.

<!-- Add entries below this line. -->
2025-10-25 · reuse · a project PR review: wrote "an elaborate python script" healthcheck where the container already had curl · code-authoring (reuse existing utilities)
2025-11-14 · dead code · a project PR review: kept the old `createSpec(…)` registry beside the new collocated specs; owner: "We don't need to maintain backwards compatibility." · new
2025-11-25 · least mechanism · a project PR review: a dedicated millisecond-formatting function plus a 6-field date reset where `setHours(0,0,0,0)` sufficed; owner: "Do we even need millisecond formatting?" · new
2025-12-09 · dispatch · a project PR review: `async function executeToolByName(toolName, args) { switch (toolName) { … } }` instead of the registry · code-quality-standards (DRY), partially
2026-02-22 · reuse · a project PR review: hand-rolled envelope validation with hex and base64 regexes instead of zod, already a dependency; owner: "Why not use zod here?" · code-authoring ("identify existing utilities… to reuse before introducing anything new")
2026-09-20 · trust · a project session (Codex): model: "A narrowly scoped project outbox … without giving [the agent] general access to your projects"; owner: "This boundary you're requiring is security theater." · new
2026-09-20 · dispatch · a project session: a Python module selected operations through an if-chain nested 7 deep (`if operation in (…):` … `if operation == '…':` … `if event['status'] != 'pending':`) · code-authoring (guard clauses; loaded in that session), strategy dispatch is new
2026-09-20 · dead code · a project session: model: "Gate or remove them; not applied because it changes coordinator capability." (legacy operations) · code-authoring ("Remove deprecated or dead code outright"; loaded in that session)
2026-09-20 · dead code · this repository: model: "keeping the current block is the safer read — it's correct either way, just verbose"; owner chose removal · new
2026-09-27 · test contract · a project session: the test contract located elements by copy (the 404 page's home-link text and a media toggle's button labels) · code-quality-standards (partial: checklist "data-testid on interactive elements"; loaded)
2026-09-29 · comments · a project session: site, infra and test code shipped without module headers or contract comments ("a lack of high level commenting"); fixed by three follow-up PRs · code-authoring (Comments & Documentation; loaded in that session)
2026-10-02 · least mechanism · a project session: model: "**Fix:** a deletion job sweeps the whole partition again after replication catches up, not just once."; owner: "get rid of the "new writer's sweep" and replicated deletion jobs altogether to keep it even simpler" · new
2026-10-02 · reuse · a Codex session on the owner's machine setup (backups): model: "the custom Python layer I added for application exports, SQLite discovery, validation, retention and monitoring created most of this friction" instead of a stock backup tool · new
2026-10-03 · comments · a project session: Codex exported 31 contract symbols in one contracts module with 3 comment lines and no doc comments (`export interface TextState { readonly text: string; }`); owner: "Codex is pretty bad at deciding level of comments" · code-authoring ("Add public API docs when required by project conventions"), too weak
2026-10-07 · least mechanism · a project session: model: "The simplest fix is one more stored number, a running total … I recommend yes." (a custom stored pending-items ledger beside the queue); owner: "We have a queue. The queue length is itself a signal" · new
2026-10-08 · least mechanism · a project session: model added two stored marker fields to detect a repeated rejection, and a shared stored counter; owner: "you're continuing to add extra guardrails where a monitoring metric added _later_ would suffice" · code-quality-standards (partial: "do not … add abstractions without a concrete need"; loaded in that session), otherwise new
2026-10-10 · trust · this repository (commits 276db18, 1fcc4c6, 9e970ea): hardened trusted orchestration hooks with allowlists and fail-closed branches (`echo "refusing: no /proc or lsof to tell whether a process still runs in $wt; stop it, then pass --force"`), all removed in 682aca7; owner: "The orchestrator is not an adversary we're defending against." · code-authoring ("Fail closed … Add a negative case for each bypass class" pushed the wrong way; needs a trust-model scope)
2025-10-25 · agent files · a project PR review: copilot-instructions.md mixed runtime tool contracts into development review guidance (a tool's output schema); owner: "the instructions here are for development of the project and _not_ for use by the [project's] agents at runtime" · agents-md-authoring (project-setup)
2025-11-24 · lint config · a project PR review: the PR relaxed eslint rules to pass; owner: "this PR cannot be accepted because it modifies eslint rules to relax coding standards." · code-authoring, partly (project-setup: severity and thresholds; code-style: never relax)
2026-02-24 · lint config · a project PR review: complexity rule set to "warn" and a warning left in place; owner: "Need to address linter complexity warning." · new (project-setup)
2026-09-20 · specs layout · a project session: bootstrap scaffolded specs as `mkdir -p … docs/design/001-…`; owner: "specs should be relocated from docs/design to specs/" · spec (not loaded) (project-setup)
2026-09-20 · process docs · this repository: model kept repo process in memory ("Two things I've saved so they don't recur: that this repo commits straight to `main`…"); owner: "a CONTRIBUTING md file is appropriate for this repo … so we don't have to rely on memories" · commit (loaded) (project-setup)
2026-09-27 · agent files · a project session: phase-0 agent files shipped no `.github/copilot-instructions.md` with Copilot review on, and the model resolved its misfires thread by thread; owner: "If you need to tune copilot review behavior, do so via copilot-instructions.md." · agents-md-authoring (loaded) (project-setup)
2026-10-02 · agent files · a project session: model: "Copilot code review stays off, because the cross-family reviewer covers it."; owner: "copilot code reviews can stay on, and you commit copilot instructions to shape its review" · new (project-setup)
2026-10-03 · lint config · a project session: model offered only "the lint rule that enforces doc comments on exports", then held back cognitive complexity ("I'd start with the built-in rules"); owner asked for "eslint complexity rules that will catch overly long modules or high complexity routines" and "I'm fine with adding cognitive complexity rule" · new (project-setup)
2026-10-11 · agent files · this repository, code-style build, owner message: owner accepts the project-setup gap as known: "a skill used during project setup or when bootstrapping an existing project for agentic DX … not just coding guardrails like linters but … AGENTS.md, CLAUDE.md, review and contributing md geared towards agents, a root specs folder, a utils folder for agent helper scripts, and copilot-instructions" · agents-md-authoring (seed) (project-setup)
