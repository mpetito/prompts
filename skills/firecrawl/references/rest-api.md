# Firecrawl REST API — Reference

Use this when neither an MCP server nor the CLI is available, or when scripting Firecrawl
calls directly.

**Base URL:** `https://api.firecrawl.dev` — every endpoint below is under `/v2`.

**Auth:** `Authorization: Bearer fc-YOUR-API-KEY` on every request.

The authoritative schema is the OpenAPI document, which is worth fetching rather than
guessing at a request body:

```bash
curl -s https://docs.firecrawl.dev/api-reference/v2-openapi.json -o v2-openapi.json
```

`https://docs.firecrawl.dev/llms.txt` is the documentation index.

```bash
curl -X POST "https://api.firecrawl.dev/v2/scrape" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "formats": ["markdown"], "onlyMainContent": true}'
```

## Endpoints

Paths and methods below were read from the v2 OpenAPI document.

### Content

| Endpoint                          | Method        | Notes                                                                    |
| --------------------------------- | ------------- | ------------------------------------------------------------------------ |
| `/v2/scrape`                      | POST          | One URL to clean content. Body: `url` plus scrape options                |
| `/v2/scrape/{jobId}`              | GET           | Retrieve a scrape result by job ID                                       |
| `/v2/batch/scrape`                | POST          | Many URLs in one job                                                     |
| `/v2/batch/scrape/{id}`           | GET, DELETE   | Poll or cancel a batch                                                   |
| `/v2/batch/scrape/{id}/errors`    | GET           | Per-URL failures in a batch                                              |
| `/v2/parse`                       | POST          | `multipart/form-data` upload of a local document (≤50 MB)                |

Scrape options (shared by `/scrape`, and by `scrapeOptions` on `/search`, `/crawl`,
`/extract`): `formats`, `onlyMainContent`, `waitFor`, `includeTags`, `excludeTags`,
`maxAge`, `actions`, `proxy`, `location`, `timeout`, `zeroDataRetention`.

### Discovery

| Endpoint                     | Method      | Body                                                                                                                                            |
| ---------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/v2/search`                 | POST        | `query`* , `limit`, `sources`, `categories`, `includeDomains`, `excludeDomains`, `tbs`, `location`, `country`, `safe`, `timeout`, `highlights`, `scrapeOptions` |
| `/v2/map`                    | POST        | `url`*, `search`, `sitemap`, `includeSubdomains`, `ignoreQueryParameters`, `ignoreCache`, `limit`, `timeout`, `location`                          |
| `/v2/crawl`                  | POST        | `url`*, `prompt`, `includePaths`, `excludePaths`, `maxDiscoveryDepth`, `sitemap`, `limit`, `crawlEntireDomain`, `allowExternalLinks`, `allowSubdomains`, `delay`, `maxConcurrency`, `webhook`, `scrapeOptions` |
| `/v2/crawl/{id}`             | GET, DELETE | Poll status and results, or cancel                                                                                                              |
| `/v2/crawl/{id}/errors`      | GET         | Per-URL failures                                                                                                                                |
| `/v2/crawl/active`           | GET         | Currently running crawls for the team                                                                                                           |
| `/v2/crawl/params-preview`   | POST        | Preview the parameters a natural-language crawl prompt resolves to                                                                              |

`includeDomains` and `excludeDomains` on `/search` are mutually exclusive.

### Extraction and Agents

| Endpoint                                  | Method      | Notes                                                                              |
| ----------------------------------------- | ----------- | ---------------------------------------------------------------------------------- |
| `/v2/extract`                             | POST        | `urls`*, `prompt`, `schema`, `enableWebSearch`, `includeSubdomains`, `showSources` |
| `/v2/extract/{id}`                        | GET         | Poll an extract job                                                                |
| `/v2/agent`                               | POST        | Autonomous gathering — always cap the spend                                        |
| `/v2/agent/{jobId}`                       | GET, DELETE | Poll or cancel                                                                     |
| `/v2/agent/{jobId}/trace`                 | GET         | What the agent actually did                                                        |
| `/v2/agent/{jobId}/snapshots/{id}`        | GET         | Page snapshots the agent captured                                                  |

### Live Browser Sessions

| Endpoint                              | Method      | Notes                                                    |
| ------------------------------------- | ----------- | -------------------------------------------------------- |
| `/v2/interact`                        | POST, GET   | Create a session, or list sessions                       |
| `/v2/interact/{sessionId}/execute`    | POST        | Run a prompt or code against the session                 |
| `/v2/interact/{sessionId}`            | DELETE      | **Close the session** — always do this                   |
| `/v2/scrape/{jobId}/interact`         | POST, DELETE | Attach an interactive session to an existing scrape     |

### Monitoring

| Endpoint                                        | Method      | Notes                                |
| ----------------------------------------------- | ----------- | ------------------------------------ |
| `/v2/monitor`                                   | POST, GET   | Create, or list                      |
| `/v2/monitor/{monitorId}`                       | GET, DELETE | Fetch or delete                      |
| `/v2/monitor/{monitorId}/run`                   | POST        | Trigger a check now                  |
| `/v2/monitor/{monitorId}/checks`                | GET         | Check history                        |
| `/v2/monitor/{monitorId}/checks/{checkId}`      | GET         | One check, page-level results        |

Monitors send outward-facing notifications. Confirm with the user before creating one.

### Specialized Indexes

| Endpoint                                        | Method     | Params                                                                                                          |
| ----------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------- |
| `/v2/search/developer`                          | GET, POST  | `query`*, `k`, `types`, `repos`, `sources`, `skills`, `passages`, `language`, `topic`, `license`, `min_stars`, `max_stars`, `archived`, `fork` |
| `/v2/search/research/papers`                    | GET        | Natural-language search over the paper index                                                                     |
| `/v2/search/research/papers/{id}`               | GET        | Paper metadata; add `query` for the top full-text passages                                                        |
| `/v2/search/research/papers/{id}/similar`       | GET        | Citation-graph expansion                                                                                          |

See `developer-index.md` for what the developer index covers and how to query it well.

### Support and Account

| Endpoint                            | Method   | Notes                                                                     |
| ----------------------------------- | -------- | ------------------------------------------------------------------------- |
| `/v2/support/ask`                   | POST     | `{ question, jobId? }` — diagnoses a failing job; returns `fixParameters` |
| `/v2/support/docs-search`           | POST     | `{ question }` — answers from the docs, with citations                    |
| `/v2/team/credit-usage`             | GET      | Credit balance and spend (`/historical` for a time series)                |
| `/v2/team/token-usage`              | GET      | Token spend (`/historical` for a time series)                             |
| `/v2/team/queue-status`             | GET      | Queue depth and concurrency                                               |
| `/v2/team/activity`                 | GET      | Recent jobs                                                               |
| `/v2/search/{jobId}/feedback`       | POST     | Feedback on a search result; refunds a credit on first submission         |

## Errors

Conventional HTTP codes: `2xx` success, `4xx` client error, `5xx` server error. Failures
return an `error` string.

`429` means a rate or concurrency limit was hit — back off exponentially rather than
retrying immediately. Keyless limits are far tighter than an account's.

Long-running jobs (`crawl`, `batch/scrape`, `extract`, `agent`) return a job ID; poll the
corresponding `GET` endpoint rather than re-submitting. A submit that times out may still
be running — **poll before retrying**, or you will pay for the work twice.

For an inexplicable failure, `POST /v2/support/ask` with the job ID beats guessing.
