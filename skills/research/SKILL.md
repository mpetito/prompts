---
name: research
description: "Procedural knowledge for conducting comprehensive technical research using documentation tools, search APIs, and GitHub resources. Use when performing deep technical research, evaluating libraries, comparing options, or investigating APIs."
---

# Research Skill

Procedural knowledge for conducting comprehensive technical research using documentation tools, search APIs, and GitHub resources.

## Core Research Tools

| Capability             | Purpose                            | Use for                                         | Query style               |
| ---------------------- | ---------------------------------- | ----------------------------------------------- | ------------------------- |
| `docs-context7/*`      | Official library documentation     | API reference, usage examples, best practices   | Library ID + topic        |
| `firecrawl/developer`  | Coding-agent index of issues, merged PRs, READMEs, curated docs | Bug reports and their fixes, error messages, API contract changes, library behavior | Natural-language question, error string verbatim |
| `perplexity/search`    | Quick factual lookups              | Version info, simple comparisons, definitions   | Specific, factual         |
| `perplexity/reason`    | Complex analysis and reasoning     | Trade-offs, architecture decisions, debugging   | Comparative, contextual   |
| `perplexity/deep`      | Comprehensive research reports     | Major decisions, unfamiliar domains, deep dives | Broad topic + focus_areas |
| `github/search_issues` | Bug reports and workarounds        | Known issues, community solutions, edge cases   | Error message + repo      |
| `github/search_code`   | Real-world implementation patterns | Usage examples, integration patterns            | Pattern + language        |
| `web`                  | Blogs, tutorials, release notes    | Recent updates, tutorials, opinions             | URL fetch or search terms |

The names above are **capabilities, not literal tool IDs** — actual IDs differ per host (e.g. Context7 is `mcp_docs-context7_*` in Copilot and `mcp__plugin_context7_context7__*` in Claude Code; `web` is `WebSearch`/`WebFetch` in Claude Code; GitHub queries can fall back to `gh api`). Map each capability to whatever is configured in the current session, and skip the ones that are unavailable rather than failing the research.

`firecrawl/developer` is the [Firecrawl Developer Index](https://www.firecrawl.dev/developer-index) — 70M+ issues, merged pull requests, READMEs, and curated documentation sites, refreshed daily, returning the **matched passages** rather than a link. It reaches the discussion behind the code, which is precisely what general web search surfaces worst. Prefer it over `github/search_issues` when you don't already know the repository, and over `web` for anything error-message- or bug-shaped. It needs no API key. The [`firecrawl`](../firecrawl/SKILL.md) skill owns the full surface — including scrape, crawl, map, and the scientific paper index — and [`../firecrawl/references/developer-index.md`](../firecrawl/references/developer-index.md) covers filters, result shape, and query technique.

---

## Research Protocol

### Phase 1: Contextualization

**Goal**: Understand how the research topic relates to the current codebase.

1. **Search existing usage**
   - Find current implementations of the topic in codebase
   - Identify patterns, conventions, and constraints
   - Note technology stack (languages, frameworks, versions)

2. **Capture constraints**
   - Architecture patterns that must be followed
   - Dependencies that affect compatibility
   - Team conventions or standards

3. **Define scope**
   - What specific questions need answering?
   - What decisions will this research inform?
   - What are the acceptance criteria for "good enough" research?

### Phase 2: Information Gathering

**Goal**: Collect authoritative information from multiple sources.

Call each capability with the arguments its host exposes. Illustrative invocations:

```text
# Official docs — resolve the library, then pull a topic
resolve-library-id(libraryName: "react")
get-library-docs(id: "/facebook/react", topic: "hooks", mode: "code")

# Quick fact, version, or comparison
perplexity/search(query: "React 18 vs React 19 concurrent features comparison")

# Trade-off analysis with context
perplexity/reason(query: "Compare Redux Toolkit vs Zustand vs Jotai for a large-scale
  React app with complex state dependencies, considering bundle size, learning curve,
  and TypeScript support")

# Comprehensive investigation of unfamiliar territory
perplexity/deep(
  query: "WebSocket vs Server-Sent Events vs HTTP/2 push for real-time data streaming",
  focus_areas: ["latency", "reconnection handling", "browser support", "scalability"])

# Primary sources for a bug, error string, or API change — passages, not links
firecrawl/developer(query: "why is my retry backoff not firing on 429", limit: 10)
firecrawl/developer(query: "ECONNRESET during long-running requests in undici",
  types: ["issue", "pull_request"])

# Known issues and workarounds in a repo you can already name
github/search_issues(query: "memory leak useEffect cleanup", repo: "facebook/react")

# Real-world usage patterns
github/search_code(query: "useReducer middleware pattern", language: "typescript")
```

### Phase 3: Synthesis

**Goal**: Transform raw findings into actionable guidance.

1. **Cross-reference sources**
   - Verify claims across multiple sources
   - Flag contradictions or outdated information
   - Note consensus vs contested findings

2. **Contextualize findings**
   - How do findings apply to our specific codebase?
   - What patterns from our stack align with recommendations?
   - What constraints eliminate certain options?

3. **Prioritize recommendations**
   - Rank options by fit for the specific use case
   - Highlight trade-offs relevant to project constraints
   - Provide clear "if X then Y" guidance

---

## Query Formulation

Query quality determines result quality more than tool choice does.

| Capability             | Good                                                                                                             | Avoid                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `perplexity/search`    | "What is the minimum Node.js version required for Next.js 14?"                                                   | "What's the best state management library?"       |
| `perplexity/reason`    | "Compare Prisma vs Drizzle for a TypeScript project with PostgreSQL, considering type safety and migrations"     | "What is Prisma?" (simple factual question)       |
| `perplexity/deep`      | "Authentication strategies for a multi-tenant SaaS with SSO, considering OAuth 2.0, SAML, and JWT" + focus_areas | Narrow questions a single search would answer     |
| `github/search_issues` | "ECONNRESET during long-running requests" + `repo:`                                                              | Generic topics without an error string or repo    |
| `firecrawl/developer`  | "why is my retry backoff not firing on 429" — the question as you'd ask a maintainer, error string verbatim      | Bare keywords ("retries"); repo filters without a `sources` scope, which drop all doc results |

---

## Common Research Patterns

| Pattern                  | Scenario                              | Sequence                                                                                                                                    |
| ------------------------ | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Library evaluation**   | Choosing between competing libraries  | Define criteria → `perplexity/search` for recent comparisons → `docs-context7` per candidate → `github/search_issues` → `perplexity/reason` |
| **Bug investigation**    | Debugging an issue with a dependency  | Search codebase for workarounds → `firecrawl/developer` with the error string verbatim → `github/search_issues` in the library repo → check newer versions |
| **API integration**      | Integrating a new external API        | `docs-context7` or `web` for official docs → `github/search_code` for examples → `github/search_issues` for rate limits → auth patterns      |
| **Architecture decision**| Making a significant technical choice | Define criteria → `perplexity/deep` for best practices → `github/search_code` for prior art → `perplexity/reason` for trade-offs             |
| **Version compatibility**| Upgrading or checking compatibility   | Check current version → `docs-context7` changelog → `perplexity/search` breaking changes → identify affected code paths                     |

For version compatibility specifically, the [`upgrade`](../upgrade/SKILL.md) skill owns the full protocol — use this pattern only for the research portion.

---

## Output Format Template

```markdown
## Research Summary

**Topic**: [What was researched]
**Relevance**: [How this applies to the current project]

## Key Findings

- [Finding 1 — most important discovery]
- [Finding 2 — second most important]
- [Finding 3 — third most important]

## Current Codebase Context

[How the topic relates to existing code, patterns, or dependencies]

## Options Analysis

### Option 1: [Name]

**Description**: [What this approach entails]

| Pros          | Cons             |
| ------------- | ---------------- |
| [Advantage 1] | [Disadvantage 1] |

**Best For**: [When to choose this option]

### Option 2: [Name]

(Same shape as Option 1.)

## Recommendation

**Recommended Approach**: [Which option and why]

**Implementation Notes**:

- [Specific guidance for implementing in this codebase]
- [Gotchas or pitfalls to avoid]
- [Migration steps if applicable]

## Code Examples

[Relevant code snippets adapted to the current project's style]

## References

| Source                 | Type         | Date       | Notes               |
| ---------------------- | ------------ | ---------- | ------------------- |
| [URL or doc reference] | Official     | YYYY-MM-DD | [Why it's relevant] |

## Open Questions

- [Anything that couldn't be definitively answered]
- [Areas needing further investigation or user decision]
```

---

## Research Quality Checklist

**Before starting**

- [ ] Understand the specific question or decision to inform
- [ ] Check codebase context before external research
- [ ] Identify what "good enough" research looks like

**During research**

- [ ] Use official documentation as primary source
- [ ] Verify information is current (check dates, versions)
- [ ] Cross-reference 2-3 sources for key claims
- [ ] Check GitHub issues for known problems
- [ ] Note version compatibility requirements

**Before finalizing**

- [ ] Findings are adapted to codebase context
- [ ] Recommendations are actionable, not just informational
- [ ] Uncertainties and open questions are clearly stated
- [ ] All sources are cited with dates
- [ ] Trade-offs are explicit for each option

---

## Delegation for Complex Research

For large research topics, break into focused sub-tasks and run them in parallel:

| Sub-Task                  | Focus Area                             |
| ------------------------- | -------------------------------------- |
| Codebase Context Analysis | Existing usage, patterns, constraints  |
| Documentation Research    | Official docs, API reference, examples |
| GitHub Investigation      | Bugs, workarounds, community solutions |
| Version Compatibility     | Compatibility matrix, migration needs  |
| Research Synthesis        | Cross-reference, recommendations       |

Subagents are stateless and do not auto-load skills — embed the relevant portion of this skill in each subagent prompt.

**Handoff Pattern**: Write findings to `specs/{topic}/research-findings.md` for complex research that will inform implementation planning (see the [`spec`](../spec/SKILL.md) skill's Supporting Documents convention).

---

## Best Practices

**Source quality**

- **Prefer official docs** over blog posts for API details
- **Check dates** — technology moves fast, stale info misleads
- **Verify with code** — if possible, test claims in actual code
- **Note uncertainty** — if sources conflict, say so explicitly

**Efficiency**

- **Start narrow, then expand** — specific questions first
- **Don't over-research** — know when "good enough" is reached
- **Batch related queries** — group similar questions together
- **Cache findings** — write to files for reuse across sessions

**Actionable output**

- **Always contextualize** — generic advice is less useful
- **Include code examples** — adapted to the current codebase style
- **Specify next steps** — what should happen after reading the research
- **Flag blockers** — what decisions or clarifications are needed
