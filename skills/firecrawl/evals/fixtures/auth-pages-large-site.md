# Session snapshot: the authentication pages of a large docs site

## Environment

- Claude Code session in the user's repository `~/dev/support-bot`, 2026-10-10.
- Tools: Read, Write, Bash (with `npx` and network access). No Firecrawl MCP server is
  connected in this session.
- `FIRECRAWL_API_KEY` is set. https://docs.example.com has about 4,000 pages (its sitemap says
  so); the authentication material is spread across several sections with no common path
  (for example `/guides/auth/sso/okta`, `/api/tokens`, `/admin/security/mfa`).
- Earlier in the session the agent ran these commands:

```text
$ npx -y firecrawl-cli@latest --status

  firecrawl cli v1.26.3

  ● Authenticated via FIRECRAWL_API_KEY
  Concurrency: 0/5 jobs (parallel scrape limit)
  Credits: 2,950 remaining
```

```text
$ npx -y firecrawl-cli@latest crawl --help
Usage: firecrawl crawl [options] [url-or-job-id]

Crawl a website using Firecrawl

Arguments:
  url-or-job-id                 URL to crawl or job ID to check status

Options:
  -u, --url <url>               URL to crawl (alternative to positional
                                argument)
  --status                      Check status of existing crawl job (default:
                                false)
  --wait                        Wait for crawl to complete before returning
                                results (default: false)
  --poll-interval <seconds>     Polling interval in seconds when waiting
                                (default: 5)
  --timeout <seconds>           Timeout in seconds when waiting (default: no
                                timeout)
  --progress                    Show progress dots while waiting (default:
                                false)
  --limit <number>              Maximum number of pages to crawl
  --max-depth <number>          Maximum crawl depth
  --exclude-paths <paths>       Comma-separated list of paths to exclude
  --include-paths <paths>       Comma-separated list of paths to include
  --sitemap <mode>              Sitemap handling: skip, include (default:
                                "include")
  --ignore-query-parameters     Ignore query parameters when crawling (default:
                                false)
  --crawl-entire-domain         Crawl entire domain (default: false)
  --allow-external-links        Allow external links (default: false)
  --allow-subdomains            Allow subdomains (default: false)
  --delay <ms>                  Delay between requests in milliseconds
  --max-concurrency <number>    Maximum concurrent requests
  --scrape-options <json>       JSON scrape options passed to each page crawl
  --scrape-options-file <path>  Path to scrape options JSON file
  --webhook <url-or-json>       Webhook URL or webhook configuration
  --cancel                      Cancel active crawl job by job ID (default:
                                false)
  -k, --api-key <key>           Firecrawl API key (overrides global --api-key)
  --api-url <url>               API URL (overrides global --api-url)
  -o, --output <path>           Output file path (default: stdout)
  --pretty                      Pretty print JSON output (default: false)
  -h, --help                    display help for command
```

```text
$ npx -y firecrawl-cli@latest map --help
Usage: firecrawl map [options] [url]

Map URLs on a website using Firecrawl

Arguments:
  url                        URL to map

Options:
  -u, --url <url>            URL to map (alternative to positional argument)
  --wait                     Wait for map to complete (default: false)
  --limit <number>           Maximum URLs to discover
  --search <query>           Search query to filter URLs
  --sitemap <mode>           Sitemap handling: only, include, skip (default:
                             "include")
  --include-subdomains       Include subdomains (default: false)
  --ignore-query-parameters  Ignore query parameters (default: false)
  --timeout <seconds>        Timeout in seconds
  -k, --api-key <key>        Firecrawl API key (overrides global --api-key)
  --api-url <url>            API URL (overrides global --api-url)
  -o, --output <path>        Output file path (default: stdout)
  --json                     Output as JSON format (default: false)
  --pretty                   Pretty print JSON output (default: false)
  -h, --help                 display help for command
```

## The user's request

> Save every page on https://docs.example.com that covers authentication (SSO, API tokens, MFA)
> as markdown under `docs-offline/auth/` so the bot can index them.
