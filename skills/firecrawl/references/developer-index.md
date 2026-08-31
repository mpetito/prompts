# Firecrawl Developer Index

An index built for coding agents: **70M+ issues, merged pull requests, and READMEs from
public repositories, plus curated documentation sites**, most sources refreshed daily.
It answers a question about code behavior, a library, an API contract, an error message,
or a known bug **from primary sources** rather than from whatever blog post ranks well.

Overview: <https://www.firecrawl.dev/developer-index> · Docs:
<https://docs.firecrawl.dev/features/developer>

## When It Beats the Alternatives

| Question                                                       | Reach for                             |
| -------------------------------------------------------------- | ------------------------------------- |
| "Was this bug reported, and where was it fixed?"               | **Developer index**                   |
| "Why does this error message happen?"                          | **Developer index**                   |
| "Which PR changed this API contract?"                          | **Developer index**                   |
| "What is the current, versioned API of library X?"             | Context7 docs tools                   |
| "How do I do X in Azure / .NET?"                               | `microsoft-docs` tools                |
| "What's the general landscape / what do people recommend?"     | Ordinary web search                   |

The index reaches the *discussion* behind the code — issues, review threads, merged fixes.
That is exactly the material a general web search is worst at surfacing.

**No API key is needed to start.** Add one for higher rate limits. A developer search costs
2 credits per 10 results, rounded up.

## Two Surfaces — Pick Deliberately

### 1. Dedicated endpoint — ranked results with matched passages

This is the one you usually want: it returns the passages that matched, in markdown, so
tables and code blocks survive.

```bash
npx -y firecrawl-cli@latest developer "why is my retry backoff not firing on 429" --limit 10
```

```bash
curl -s "https://api.firecrawl.dev/v2/search/developer?query=how%20do%20I%20configure%20retries&k=10"
```

`POST` on the same path is easier when passing array filters:

```bash
curl -X POST https://api.firecrawl.dev/v2/search/developer \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I configure retries", "k": 10, "types": ["issue", "pull_request"]}'
```

Via MCP: `firecrawl_developer_search`.

### 2. `developer` category on ordinary web search — blended results

```bash
npx -y firecrawl-cli@latest search "how do I configure retries" --categories developer --limit 10
```

This returns the **web result shape** — `url`, `title`, `description`, `position`, tagged
`category: "developer"` — with **no matched passages and no index filters**. Use it when you
want developer hits alongside normal web results. `developer` cannot be combined with other
categories.

## Filters

| Filter                                                        | Effect                                                        |
| ------------------------------------------------------------- | ------------------------------------------------------------- |
| `k`                                                           | Number of results (default 10)                                |
| `passages`                                                    | Matched passages carried per result                           |
| `types`                                                       | Any of `doc`, `issue`, `pull_request`, `readme`               |
| `repos`                                                       | Scopes the **repository** half of the index                   |
| `sources`                                                     | Scopes the **documentation** half                             |
| `skills: "only"`                                              | Restrict to indexed agent-skill files                         |
| `language`, `topic`, `license`, `min_stars`, `max_stars`, `archived`, `fork` | Repository attributes                          |

> Those last seven describe a **code repository**. Sending one without a `sources` scope
> returns **no `doc` results** — a silent way to lose half the index.

## Reading Results

- Each result has a stable `id` encoding its kind: `doc:`, `issue:`, `pull_request:`, or
  `readme:` — e.g. `issue:sidekiq/sidekiq#1471`.
- **`title` is frequently absent on `doc` results.** Fall back to `url`; do not assume the
  field is present.
- When you scope with `repos` or `sources`, the response echoes them back with an `indexed`
  flag per entry — that is how you tell "this repo isn't in the index" apart from "this
  query found nothing". Check it before reporting a negative result.

## Querying It Well

Express scoping intent **in the query text** — semantic retrieval handles it, so you rarely
need to reach for structured filters first.

| Good                                                          | Weak                             |
| ------------------------------------------------------------- | -------------------------------- |
| "why is my retry backoff not firing on 429"                   | "retries"                        |
| "ECONNRESET during long-running requests in undici"           | "connection errors"              |
| "which PR added Retry-After handling to the aws-sdk-js retry" | "aws sdk retry"                  |

Paste the **actual error string**. Ask the question the way you'd ask a maintainer. Run two
or three distinct framings rather than one — each surfaces different issues and PRs.

## Note on the Vendor Skill

The docs recommend `npx -y firecrawl-cli@latest setup developer-index`, which installs
Firecrawl's own `firecrawl-developer-index` skill into the user-level skills directory.
Where that directory is a symlink to a managed repository, this writes vendor files straight
into version control — ask before running it. This reference covers the same ground.
