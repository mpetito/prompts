# firecrawl

Verdict: **needs-work** · SKILL.md body 203 lines · description 967 chars

The skill is well structured. It starts by detecting the access path, follows with a clear cheapest-first ladder, guards the fragile keyless-CLI case (a crawl that exits 0 with no work), has a strong troubleshooting table, and keeps its references one level deep. The most important gap is that its freshness guidance is backwards: it says to "lower or omit --max-age" for stale content and treats caching as opt-in, but Firecrawl's documented default already serves pages cached up to 2 days old, so a skill built to return "what it says now" quietly returns cached content.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names scrape/crawl/map/search/extract, concrete triggers (pricing, changelogs, JS-rendered pages, PDF/DOCX) and the WebFetch pre-emption. |
| Description includes both what the Skill does and when to use it | pass | 967 of 1,024 chars; what + 'Use whenever…' + 'Not for…' clause per collection convention. |
| SKILL.md body is under 500 lines | pass | 203 body lines. |
| Additional details are in separate files (if needed) | pass | CLI flags, REST endpoints and developer-index detail live in references/. |
| No time-sensitive information (or in an "old patterns" section) | partial | Drifting figures ('70M+ issues', 'roughly 43M paper abstracts', '2 credits per 10 results'). Every command is `@latest` while the flag reference is pinned to v1.23.3. |
| Consistent terminology throughout | partial | The CLI binary appears as both `npx -y firecrawl-cli@latest` and a bare `firecrawl`. The skill prefers MCP but names options only by their CLI flags. 'Surfaces' means access paths in SKILL.md but endpoint-vs-category in developer-index.md. |
| Examples are concrete, not abstract | pass | Runnable commands for each rung; good/weak query table in developer-index.md. |
| File references are one level deep | pass | All three references are linked from SKILL.md. rest-api.md's pointer to developer-index.md goes to a file SKILL.md already links. |
| Progressive disclosure used appropriately | pass |  |
| Workflows have clear steps | pass | Step 1 path, Step 2 ladder, Step 3 run; auth check before CLI crawl/map. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts/ folder. |
| No "voodoo constants" (all values justified) | partial | Most example values are bounded and explained. `--wait-for 3000` in Common Issues has no rationale but is only an illustrative starting value. |
| Required packages listed in instructions and verified as available | partial | npx form is stated, but lines 175 and 203 call a bare `firecrawl` binary that may not be installed. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | partial | `--status` before CLI crawl/map and the 'indexed' check before reporting a negative developer-index result are good. Freshness is the core promise, but the skill gives no step that guarantees a live fetch. |
| Feedback loops included for quality-critical tasks | pass | Common Issues table gives an escalation path for each symptom (wait-for, then interact; proxy auto; 429 backoff). |
| At least three evaluations created | partial | 8 cases, all `kind: trigger`. No behaviour case covers the fragile paths: the keyless CLI crawl, crawl bounding, freshness. |

## Findings

1. **high** · Checklist: Validation/verification steps for critical operations (and Content guidelines: accuracy of a fragile option) · SKILL.md, Discipline (line 169) and Common Issues row 'Content is stale' (line 197)
   > Use `--max-age <ms>` to accept cached content on repeat fetches instead of re-billing.
| Content is stale | A cached response was reused. Lower or omit `--max-age`. |

   Fix: Firecrawl docs (features/fast-scraping, 'Verifying Freshness and Liveness') say an omitted maxAge defaults to a 2-day cache, so omitting it does not give a live fetch. Change the row to 'Pass `--max-age 0` (MCP `maxAge: 0`) for a live fetch'. Reword the Discipline bullet to say that caching up to 2 days is the default and `--max-age 0` is the opt-out when the user needs the current page.

2. **medium** · Structure longer reference files with a table of contents · references/cli-commands.md (252 lines), references/rest-api.md (126 lines), references/developer-index.md (108 lines)
   > # Firecrawl CLI — Command Reference

Flags below were captured from `firecrawl <command> --help` on CLI v1.23.3.

   Fix: Add a one-line contents list under each H1 naming its sections, for example scrape · search · map · crawl · parse · interact · agent · research · monitor · setup. A partial read then still shows that monitor and setup exist.

3. **medium** · Concise is key (repeated content within SKILL.md) · SKILL.md, Keys and the Keyless Tier (lines 54-77), Reading the Output (160-164), Discipline (168), Common Issues (190-203)
   > > Run keyless, the CLI drops into an **interactive login prompt**. In an agent session that
> either hangs or — with stdin closed — prints the prompt, does no work, and still exits `0`.

   Fix: Each of these is stated two or three times: the keyless login-prompt failure (blockquote plus two Common Issues rows), the `.firecrawl/` gitignore (lines 162 and 202), `--only-main-content` (lines 106, 168 and 195) and 429 backoff. State each once: keep the auth check in Step 1, move each symptom and fix into Common Issues only, and cut the first Keys paragraph to one sentence ('MCP carries its own credentials; this section is CLI/REST only'). (about 250 tokens saved)

4. **medium** · Avoid assuming tools are installed; Use consistent terminology · SKILL.md lines 175 and 203
   > `firecrawl doctor <job-id>` diagnoses it.
| Scientific paper search returns web pages | … For papers use `firecrawl research search-papers`. |

   Fix: Every other command uses `npx -y firecrawl-cli@latest`, and line 52 says this form needs no global install. Write these two commands the same way (or define the npx prefix once and use it everywhere), so Claude does not run a `firecrawl` binary that may not exist.

5. **low** · Use consistent terminology (one name per concept across access paths) · SKILL.md, Step 3 intro (lines 96-97) and Common Issues table
   > Commands below are the CLI form; the MCP tools take the same concepts as parameters

   Fix: Step 1 says to prefer MCP, but every later fix names only a CLI flag. Add the MCP parameter beside each flag in the Common Issues fixes, for example `--only-main-content`/`onlyMainContent`, `--wait-for`/`waitFor`, `--max-age`/`maxAge`, `--proxy`/`proxy`, `--schema`/`jsonOptions.schema`. An MCP-path agent then does not have to translate.

6. **low** · Concise is key (Default assumption: Claude is already very smart) · SKILL.md intro (line 10), Scope 'In scope' (15-19), Developer Index paragraph (130-133), Structured Extraction (155), Discipline (173)
   > Firecrawl turns live web pages into clean, LLM-ready markdown.
…Where `schema.json` is an ordinary JSON Schema object.

   Fix: Cut the product blurb, the 'In scope' list (it restates the description), the developer-index coverage claim ('70M+ … No API key required', already in developer-index.md), the JSON Schema gloss and 'One page that answers the question beats forty'. Keep the routing table and the one-line 'own web work, not product code' scope. (about 150 tokens saved)

7. **low** · Avoid time-sensitive information · references/cli-commands.md line 3 and line 187; references/developer-index.md lines 3 and 25-26
   > A dedicated index of roughly 43M paper abstracts — about 90% biomedical
A developer search costs 2 credits per 10 results, rounded up.

   Fix: Drop the corpus sizes and the credit price, or move them under a dated 'as of' note. The examples use `@latest`, but the flag tables come from v1.23.3, so either pin the examples to `firecrawl-cli@1.23.3` or keep the existing 'run --help to confirm' line as the only version statement. (about 40 tokens saved)

8. **low** · Build evaluations first (scenarios that test the gaps); Checklist: At least three evaluations · evals/shared-benchmark.json
   > "kind": "trigger",  (all 8 cases)

   Fix: Add 2-3 behaviour cases with assertions for the gaps this skill exists to close: a keyless CLI crawl must check `--status` and not report an empty result; a 'download every page under /guides' request must bound the crawl (`--limit` plus `--include-paths`); a 'what does it say right now' scrape must request a live fetch (`maxAge 0`).

## Strengths

- Starts by detecting which access path is available (full MCP, search-only MCP, CLI or REST) and says what each one cannot do. This includes the case where two Firecrawl servers are connected at once and the agent must choose by capability, not by name.
- Calls out a fragile failure that a model cannot infer: a keyless CLI crawl prints a login prompt and still exits 0, so it must never be read as an empty result. A `--status` check comes first.
- A Common Issues table maps each symptom to a cause and a next action, giving a compact feedback loop. The developer-index reference also tells the agent to check the 'indexed' echo before reporting a negative result.

## Cut candidates

- Intro paragraph line 10 ('Firecrawl turns live web pages into clean, LLM-ready markdown')
- Scope > In scope list (restates the description)
- Keys and the Keyless Tier: first paragraph and the blockquote that repeats the Common Issues rows
- The Developer Index — Don't Scrape What's Already Indexed: '70M+ issues … No API key required' coverage sentence
- Structured Extraction: 'Where schema.json is an ordinary JSON Schema object' gloss
- Reading the Output: .firecrawl/ gitignore bullet (repeated in Common Issues)
- Discipline: 'One page that answers the question beats forty that mention it' and the --only-main-content bullet (repeated in Step 3 and Common Issues)
- references/developer-index.md 'Note on the Vendor Skill' (duplicates cli-commands.md 'Setup Commands — Use With Care')
