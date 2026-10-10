# Firecrawl CLI — Command Reference

Flags below were captured from `firecrawl <command> --help` on CLI v1.23.3. Run
`npx -y firecrawl-cli@latest <command> --help` to confirm against the version you have.

Every command also accepts the global flags `-k, --api-key <key>`, `--api-url <url>`,
`-o, --output <path>`, and (where output can be JSON) `--json` / `--pretty`.

```bash
npx -y firecrawl-cli@latest --status     # version, auth state, concurrency, credits
npx -y firecrawl-cli@latest --version
npx -y firecrawl-cli@latest doctor <job-id>   # diagnose a specific failed run
```

Set `FIRECRAWL_NO_TELEMETRY=1` to disable the CLI's anonymous telemetry.

---

## `scrape [urls...]`

Scrapes one or more URLs. Multiple URLs run concurrently and are **saved to `.firecrawl/`
rather than stdout**.

| Flag                       | Meaning                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `-u, --url <url>`          | URL, as an alternative to the positional argument                                                                         |
| `-f, --format <formats>`   | Comma-separated: `markdown`, `html`, `rawHtml`, `links`, `images`, `screenshot`, `summary`, `changeTracking`, `json`, `attributes`, `branding`. One format prints raw content; several print JSON |
| `-H, --html`               | Shortcut for `--format html`                                                                                              |
| `-S, --summary`            | Shortcut for `--format summary`                                                                                           |
| `--only-main-content`      | Strip nav, footers, boilerplate (default: false)                                                                          |
| `--wait-for <ms>`          | Wait before capturing — for client-rendered pages                                                                         |
| `--screenshot`             | Capture a screenshot                                                                                                      |
| `--full-page-screenshot`   | Capture a full-page screenshot                                                                                            |
| `--include-tags <tags>`    | Only these HTML tags                                                                                                      |
| `--exclude-tags <tags>`    | Drop these HTML tags                                                                                                      |
| `--max-age <ms>`           | Accept cached content up to this age                                                                                      |
| `--country <code>`         | ISO country code for geo-targeted scraping                                                                                |
| `--languages <codes>`      | Comma-separated language codes                                                                                            |
| `-Q, --query <prompt>`     | Ask a question about the page instead of returning the whole thing                                                        |
| `--schema <json>`          | Inline JSON schema for structured extraction                                                                              |
| `--schema-file <path>`     | JSON schema from a file                                                                                                   |
| `--actions <json>`         | Inline actions array to run during the scrape                                                                             |
| `--actions-file <path>`    | Actions array from a file                                                                                                 |
| `--profile <name>`         | Persistent browser profile, to carry state across scrapes                                                                 |
| `--no-save-changes`        | Load a profile without persisting changes back to it                                                                      |
| `--proxy <proxy>`          | Proxy mode, e.g. `auto`, `basic` — try this on 403 / bot challenges                                                       |
| `--lockdown`               | Lockdown mode                                                                                                             |
| `--redact-pii`             | Redact personally identifiable information from the output                                                                |
| `--timing`                 | Print request timing                                                                                                      |

---

## `search <query>`

| Flag                          | Meaning                                                                                       |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `--limit <n>`                 | Max results (default 5, max 100)                                                                |
| `--sources <sources>`         | `web`, `images`, `news` (default `web`)                                                         |
| `--categories <categories>`   | `github`, `research`, `pdf`, `developer`                                                        |
| `--tbs <value>`               | Recency: `qdr:h`, `qdr:d`, `qdr:w`, `qdr:m`, `qdr:y`                                            |
| `--location <location>`       | Geo-targeting, e.g. `"San Francisco,California,United States"`                                  |
| `--country <code>`            | ISO country code (default `US`)                                                                 |
| `--timeout <ms>`              | Default 60000                                                                                   |
| `--highlights` / `--no-highlights` | Query-relevant highlights vs. the original snippets                                        |
| `--ignore-invalid-urls`       | Drop URLs unusable by other Firecrawl endpoints                                                 |
| `--scrape`                    | Also scrape each result — search and fetch in one call                                          |
| `--scrape-formats <formats>`  | Formats when `--scrape` is on (default `markdown`)                                              |
| `--only-main-content`         | Main content only when scraping (default true here)                                             |

`--categories research` filters **web results to research-affiliated sites**. It is not the
paper index — use `research search-papers` for papers. `--categories developer` searches the
indexed GitHub issues, merged PRs, READMEs, and curated docs.

---

## `map [url]`

**Requires an API key.** Discovers a site's URLs without fetching page content — the cheap
way to decide what is worth scraping.

| Flag                        | Meaning                                     |
| --------------------------- | ------------------------------------------- |
| `--limit <n>`               | Max URLs to discover                        |
| `--search <query>`          | Filter discovered URLs by query             |
| `--sitemap <mode>`          | `only`, `include` (default), `skip`         |
| `--include-subdomains`      | Include subdomains                          |
| `--ignore-query-parameters` | Collapse URLs differing only by query string |
| `--timeout <seconds>`       | Request timeout                             |
| `--wait`                    | Wait for the map to complete                |

---

## `crawl [url-or-job-id]`

**Requires an API key.** Also the status/cancel surface for an existing crawl job.

| Flag                           | Meaning                                          |
| ------------------------------ | ------------------------------------------------ |
| `--limit <n>`                  | Max pages — always set this                      |
| `--max-depth <n>`              | Max depth from the seed URL                      |
| `--include-paths <paths>`      | Comma-separated paths to restrict to             |
| `--exclude-paths <paths>`      | Comma-separated paths to skip                    |
| `--sitemap <mode>`             | `skip`, `include` (default)                      |
| `--crawl-entire-domain`        | Whole domain rather than the seed subtree        |
| `--allow-subdomains`           | Follow subdomains                                |
| `--allow-external-links`       | Follow off-site links                            |
| `--ignore-query-parameters`    | Treat URLs differing only by query as one        |
| `--delay <ms>`                 | Delay between requests — politeness              |
| `--max-concurrency <n>`        | Cap concurrent requests                          |
| `--scrape-options <json>`      | Scrape options applied to every page             |
| `--scrape-options-file <path>` | The same, from a file                            |
| `--webhook <url-or-json>`      | Webhook URL or config                            |
| `--wait`                       | Block until the crawl finishes                   |
| `--progress`                   | Progress dots while waiting                      |
| `--poll-interval <seconds>`    | Status poll interval when waiting (default 5)    |
| `--timeout <seconds>`          | Timeout while waiting (default: none)            |
| `--status`                     | Check an existing job by ID                      |
| `--cancel`                     | Cancel an active job by ID                       |

---

## `parse <file>`

Converts a **local** file to markdown. Public document URLs go through `scrape` instead.

Supported: `.html`, `.htm`, `.pdf`, `.docx`, `.doc`, `.odt`, `.rtf`, `.xlsx`, `.xls`.
Max upload 50 MB.

Formats: `markdown`, `html`, `rawHtml`, `links`, `images`, `summary`, `json`, `attributes`.
Shares `--only-main-content`, `--include-tags`, `--exclude-tags`, `-S`, `-H`, `-Q`,
`--timeout`, `--timing` with `scrape`.

```bash
npx -y firecrawl-cli@latest parse ./report.pdf -f markdown,links
npx -y firecrawl-cli@latest parse ./report.pdf -Q "What is the total revenue?"
```

---

## `interact [args...]`

Opens a live browser session **against a previous scrape**. The scrape ID is remembered
automatically, so the usual flow is scrape then interact:

```bash
npx -y firecrawl-cli@latest scrape https://example.com
npx -y firecrawl-cli@latest interact "Click the pricing tab"
npx -y firecrawl-cli@latest interact "What is the price of the Pro plan?"
npx -y firecrawl-cli@latest interact stop
```

| Flag                   | Meaning                                                     |
| ---------------------- | ----------------------------------------------------------- |
| `-p, --prompt <text>`  | AI prompt, as an alternative to the positional argument      |
| `-c, --code <code>`    | Execute code in the browser sandbox                          |
| `-s, --scrape-id <id>` | Target a specific scrape (default: the last one)             |
| `--node`               | Run `--code` as Node/Playwright (default)                    |
| `--python`             | Run `--code` as Python/Playwright                            |
| `--bash`               | Run `--code` as Bash                                         |
| `--timeout <seconds>`  | 1–300, default 30                                            |

**Always `interact stop` when done** — the session is a live browser holding resources.

---

## `agent <prompt-or-job-id>`

**Requires an API key.** Autonomous multi-page gathering when you cannot name the pages up
front. Expensive — bound it.

| Flag                      | Meaning                                                     |
| ------------------------- | ----------------------------------------------------------- |
| `--urls <urls>`           | Comma-separated URLs to focus on                            |
| `--model <model>`         | `spark-1-mini` (default, cheaper) or `spark-1-pro`          |
| `--schema` / `--schema-file` | JSON schema for structured output                        |
| `--max-credits <n>`       | Hard spend cap — the job fails rather than overruns          |
| `--webhook <url-or-json>` | Webhook URL or config                                       |
| `--wait`, `--poll-interval`, `--timeout` | Blocking behavior                             |
| `--status`, `--cancel`    | Inspect or cancel an existing job by ID                     |

Set `--max-credits` on every agent run.

---

## `research <subcommand>`

A dedicated index of roughly 43M paper abstracts — about 90% biomedical (PubMed, bioRxiv,
medRxiv) plus arXiv. Use it instead of scraping PubMed or Google Scholar by hand.

| Subcommand                        | Purpose                                                                                  |
| --------------------------------- | ---------------------------------------------------------------------------------------- |
| `search-papers <query>`           | Entry point. Semantic search over abstracts; returns ranked papers with a source ID       |
| `inspect-paper <paperId>`         | Canonical metadata for one paper                                                          |
| `read-paper <paperId>`            | Best-matching in-body passages for a `--question` — use it to verify a candidate          |
| `related-papers <seedIds...>`     | Citation-graph expansion from your strongest hits; `--mode similar\|citers\|references`   |
| `search-github <query>`           | GitHub issue/PR history and READMEs                                                       |

IDs take the forms `pmid:`, `pmcid:`, `doi:`, `arxiv:`, or a canonical paper ID.

```bash
npx -y firecrawl-cli@latest research search-papers "CRISPR base editing off-target effects" --limit 20
npx -y firecrawl-cli@latest research related-papers pmcid:PMC12530322 --intent "in vivo delivery"
npx -y firecrawl-cli@latest research read-paper arxiv:1706.03762 --question "What is the attention mechanism?"
```

Run several distinct framings of the same question — each surfaces different papers.

---

## `monitor <subcommand>`

**Requires an API key.** Recurring checks that diff a page against the last snapshot, judge
the change against a plain-language `--goal`, and notify by webhook, email, or Slack.

Prefer a monitor over repeated one-off scrapes whenever the same URL must be checked more
than once, or when the request is "tell me when X changes" rather than "what does X say".

| Subcommand                        | Purpose                              |
| --------------------------------- | ------------------------------------ |
| `create [file]`                    | Create from flags, a JSON file, or stdin |
| `list`                             | List monitors                        |
| `get <monitorId>`                  | Fetch one monitor                    |
| `update <monitorId> [file]`        | Update, e.g. `--state paused`        |
| `delete <monitorId>`               | Delete                               |
| `run <monitorId>`                  | Trigger a check immediately          |
| `checks <monitorId>`               | List that monitor's checks           |
| `check <monitorId> <checkId>`      | One check, with page-level results   |

```bash
npx -y firecrawl-cli@latest monitor create --name "Blog" \
  --goal "Notify me when a new post is published" \
  --schedule "every 30 minutes" \
  --page https://example.com/blog \
  --email alerts@example.com
```

Monitors are recurring, outward-facing, and can send mail — **confirm with the user before
creating, updating, or deleting one.**

---

## Setup Commands — Use With Care

`init`, `setup`, `make`, `launch`, and `config`/`login` modify the user's machine: they
install skill packs into the skills root, register MCP servers, rewrite tool defaults, and
open browser auth.

Do not run them unprompted. In particular, `init --all` writes a large set of vendor skills
into the user-level skills directory — which, in a setup where that directory is a symlink
to a managed repository, drops them straight into version control. Ask first.

`env` pulls `FIRECRAWL_API_KEY` into a local `.env`; make sure `.env` is gitignored.
