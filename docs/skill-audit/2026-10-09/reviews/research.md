# research

Verdict: **needs-work** · SKILL.md body 300 lines · description 867 chars

The skill has a trigger-precise description, a clear three-phase protocol, a provenance-tagging scheme (DOCS/SOURCE/INFERRED/UNVERIFIED) and turn-cap-aware delegation rules that a model would not produce unprompted. The biggest gap is concision: about a third of the 300-line body is generic research advice an Opus or Sonnet model already follows. The same rules also appear three or four times across Phase 3, the checklist, Delegation and Best Practices.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names the sources (official docs, GitHub issues/PRs, release notes, Firecrawl developer index) and concrete trigger phrasings, including terse 'A vs B vs C'. |
| Description includes both what the Skill does and when to use it | pass | Covers what, when, and disambiguation against firecrawl, upgrade and spec; 867 chars, under the 1,024 limit. |
| SKILL.md body is under 500 lines | pass | 300 body lines excluding frontmatter. |
| Additional details are in separate files (if needed) | partial | No references/ folder. The 60-line output template and the illustrative invocation block could move out, or be cut. The body is under the limit, so this is a concision issue rather than a size issue. |
| No time-sensitive information (or in an 'old patterns' section) | partial | '70M+ issues ... refreshed daily' is a volatile vendor statistic; version-pinned examples (Next.js 14, React 18 vs 19) are only illustrative. |
| Consistent terminology throughout | partial | Mostly consistent ('capability', provenance tags). The Firecrawl index is named three ways: 'Firecrawl's developer index', 'Firecrawl Developer Index' and 'firecrawl/developer'. Workers are also called 'sub-tasks', 'workers' and 'agents'. |
| Examples are concrete, not abstract | pass | Query Formulation gives concrete good/avoid queries; Phase 2 shows concrete invocations. |
| File references are one level deep | pass | All links go directly from SKILL.md to sibling skills or their reference files; no chained references inside this skill. |
| Progressive disclosure used appropriately | partial | Firecrawl detail is correctly delegated to ../firecrawl. The long output template and the duplicated invocation examples stay inline. |
| Workflows have clear steps | pass | Phases 1-3 are numbered, and a copyable quality checklist exists. |
| Validation/verification steps for critical operations | pass | Exact values need a second source; licence, pricing and terms claims need a verbatim quote; cheaper workers' load-bearing claims are re-checked. |
| Feedback loops included for quality-critical tasks | partial | The checklist acts as a final gate, but there is no explicit loop of reviewing against the checklist, filling gaps and re-checking. The UNVERIFIED tag partly covers this. |
| No Windows-style paths (all forward slashes) | pass |  |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 cases, but all are trigger cases with empty assertions. No case checks output behaviour such as provenance tags, cited URLs or an assumptions table. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| Required packages listed in instructions and verified as available | not-applicable | No packages; MCP capabilities are mapped per host and skipped when absent, per collection convention. |

## Findings

1. **high** · Concise is key (Default assumption: Claude is already very smart) · SKILL.md, '## Best Practices' (lines 277-304)
   > - **Prefer official docs** over blog posts for API details
- **Check dates** — technology moves fast, stale info misleads

   Fix: Delete Source quality and Actionable output entirely and most of Efficiency. Keep only the three non-obvious rules (batch independent fetches in one response, Write as you go, Stop at two thirds of a turn cap) and move them into Delegation, where they are already referenced. (about 280 tokens saved)

2. **medium** · Concise is key; Use workflows for complex tasks (no duplicated steps) · SKILL.md, '## Research Quality Checklist' (lines 211-234) vs Phases 1-3
   > - [ ] Check codebase context before external research
- [ ] Cross-reference 2-3 sources for key claims

   Fix: The checklist restates Phase 1 and Phase 3 almost line for line. Keep one copyable checklist: either replace the phase bullet lists with it or drop the generic checklist lines. Keep only the distinctive gates: every assumption has a verdict, every claim has a provenance tag, exact values have a second source, and sources are dated. (about 180 tokens saved)

3. **medium** · Concise is key · SKILL.md, Phase 1 and Phase 3 bullet lists (lines 35-44, 92-95, 104-112)
   > - Verify claims across multiple sources
   - Flag contradictions or outdated information

   Fix: Cut the generic sub-bullets (find existing usage, note the stack, rank options by fit, highlight trade-offs, 'if X then Y'). Keep the non-obvious ones: assumptions listed for confirm/refute/'docs silent', the provenance tags, and second-source confirmation of exact values. (about 220 tokens saved)

4. **medium** · Concise is key; Examples pattern (one good example, not two) · SKILL.md, Phase 2 invocation block (lines 56-86) and '## Query Formulation' (lines 116-126)
   > firecrawl/developer(query: "why is my retry backoff not firing on 429", limit: 10)
...| `firecrawl/developer`  | "why is my retry backoff not firing on 429" —

   Fix: The same example queries appear twice, once as host-specific call syntax and once in the good/avoid table. Delete the 30-line invocation block and keep the Query Formulation table. Call syntax is host-specific anyway, and line 23 already says to map capabilities. (about 300 tokens saved)

5. **medium** · Avoid offering too many options (provide a default with an escape hatch) · SKILL.md, '## Core Research Tools' table and '## Common Research Patterns' (lines 12-21, 130-138)
   > | `perplexity/search`    | Quick factual lookups ...
| `perplexity/reason`    | Complex analysis ...
| `perplexity/deep`      | Comprehensive research ...

   Fix: Replace eight parallel capabilities and five tool sequences with one default source order: official docs (Context7 or web) first, then firecrawl/developer for bug- or error-shaped questions, then github/search_issues when the repo is known. Name Perplexity only as an optional synthesis aid. This also matches the docs-first, then issue tracker, then probe order the owner's global rules require. (about 200 tokens saved)

6. **low** · Template pattern (match strictness to need); Conditional workflow pattern · SKILL.md, '## Output Format Template' (lines 144-207)
   > ## Options Analysis

### Option 1: [Name]

   Fix: State whether the template is strict or a sensible default. Add one line making Options Analysis and Code Examples conditional on a choice-between-options question, so the template fits the description's 'is this a known upstream bug and which release fixed it' case, which needs a findings-plus-fix-version answer.

7. **low** · Avoid time-sensitive information; Use consistent terminology · SKILL.md, line 25 (firecrawl/developer paragraph)
   > `firecrawl/developer` is the [Firecrawl Developer Index] — 70M+ issues, merged pull requests, READMEs, and curated documentation sites, refreshed daily

   Fix: Drop the '70M+ ... refreshed daily' statistic and the explanation of what the index is, because ../firecrawl owns it. Keep the routing rule: prefer it over github/search_issues when the repo is unknown, and over web for error- or bug-shaped queries. Use the single name `firecrawl/developer` throughout. (about 60 tokens saved)

8. **low** · Build evaluations first; Testing checklist (at least three evaluations, real usage scenarios) · evals/shared-benchmark.json
   > "kind": "trigger", ... "assertions": []

   Fix: All 8 cases test triggering only, so nothing checks that the skill's distinctive rules change behaviour. Add about three behaviour cases with assertions: provenance tags on claims, URLs cited, an assumptions table, and a version-fixed answer for a known-bug question. Then a with/without delta can show whether the trimmed body still earns its tokens.

## Strengths

- A provenance tag on every claim (DOCS / SOURCE / INFERRED / UNVERIFIED), plus second-source confirmation of exact values and verbatim quotes for licence and pricing claims. This is a concrete verification scheme that other analysis skills could reuse.
- Turn-cap-aware delegation: at most about five prioritised questions per worker, stop at two thirds of the cap, and write findings as you go. This guidance is specific and a model does not apply it unprompted.
- The description carries a 'Not for … (firecrawl / upgrade / spec)' clause, and the eval suite includes matching negative trigger cases for each excluded sibling.

## Cut candidates

- ## Best Practices: Source quality and Actionable output subsections in full; Efficiency except Batch, Write as you go, and Stop at two thirds
- ## Research Quality Checklist: generic items that restate Phases 1-3
- ### Phase 1: Contextualization: sub-bullets under 'Search existing usage' and 'Capture constraints'
- ### Phase 3: Synthesis: 'Verify claims across multiple sources', 'Flag contradictions', 'Note consensus', and all of 'Prioritize recommendations'
- ### Phase 2: Information Gathering: the illustrative invocation code block, which duplicates Query Formulation
- # Research Skill: the opening sentence 'Procedural knowledge for conducting comprehensive technical research...'
- ## Core Research Tools: the '70M+ issues ... refreshed daily' description of the Firecrawl index
