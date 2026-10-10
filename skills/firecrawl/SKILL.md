---
name: firecrawl
description: "Fetch many web pages with Firecrawl without flooding the context: crawl a docs path to a file, ask each page for its fields instead of its full text, and map a large site for one topic instead of crawling it. Use when a request needs every page under a site or docs path saved locally, the same facts pulled from many pages into a table or JSON, or the pages of a large site that cover one topic, even when the Firecrawl scrape tool or WebFetch looks enough. Not for one page or a few pages (the Firecrawl MCP tools' own descriptions cover those), testing or driving your own app in a browser (Playwright tools), adding Firecrawl calls to a product's code (Firecrawl SDK docs), or searching the local repository."
---

# Firecrawl: many pages

Role: domain reference, read by whichever session must fetch many pages; detail is in
`references/`.

The Firecrawl MCP server's instructions and tool descriptions cover single pages, search and its
indexes. Each MCP scrape returns its whole page into the conversation, so for many pages choose
by what the user needs from them:

1. **Full text of many pages under one path: crawl to a file.** Use a crawl tool if one is
   connected (`firecrawl_crawl`); otherwise the CLI, which needs an API key for crawl. Check
   with `npx -y firecrawl-cli@latest --status`; `Not authenticated` means ask the user for a key.
   A crawl follows only child URLs of its seed and stops at `--limit` (default 10,000 pages;
   Firecrawl docs, checked 2026-10-10): seed it at the path, set `--limit` a little above the
   page count you expect, and tell the user that count first.

   ```bash
   npx -y firecrawl-cli@latest crawl "https://docs.example.com/guides" \
     --limit 200 --wait -o guides.json
   ```

2. **Fields or answers across many pages: ask each page for them, not for its text.** Scrape
   each with `formats: ["json"]` and a `jsonOptions.schema`, or `formats: ["query"]` and a
   `queryOptions.prompt`, so answers arrive instead of full markdown. Keep the URL with each
   answer for citation.
3. **A topic spread across a large site: map, then scrape the hits.** When the pages share no
   path, a crawl fetches the whole site. Run `map` with `--search` once per facet of the topic
   (a map tool, or the keyed CLI), merge the URLs, state the count, then scrape only those.

   ```bash
   npx -y firecrawl-cli@latest map "https://docs.example.com" --search "single sign-on" --limit 100 --json -o sso.json
   ```

## References

- [references/cli-commands.md](references/cli-commands.md): every CLI command and flag, freshness, blocked pages, setup commands to avoid.
- [references/developer-index.md](references/developer-index.md): developer-index filters, result shape, query technique.
- [references/rest-api.md](references/rest-api.md): REST endpoints when neither MCP nor the CLI fits.
