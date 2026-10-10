---
name: firecrawl
model: sonnet
effort: high
description: "Copy many web pages with Firecrawl without pulling them one by one into the context: crawl to a file, bounded, with the API key a crawl needs. Use when a request needs every page under a site or docs path saved locally, a docs section mirrored for offline search or indexing, or more than a handful of whole pages fetched at once, even when the Firecrawl scrape tool or WebFetch looks enough. Not for one page or a few pages (the Firecrawl MCP tools' own descriptions cover those), testing or driving your own app in a browser (Playwright tools), adding Firecrawl calls to a product's code (Firecrawl SDK docs), or searching the local repository."
---

# Firecrawl: many pages

Role: domain reference, read by whichever session must fetch many whole pages; detail is in
`references/`.

The Firecrawl MCP server's instructions and tool descriptions cover single pages, search and
its indexes. This file covers the one choice they leave out.

1. **Full text of more than about ten pages goes through a crawl written to a file, never
   through scrapes into the context.** Each MCP scrape returns its whole page into the
   conversation, so a hundred of them fill it.
2. **Find the crawl.** Use a crawl tool if one is connected (`firecrawl_crawl`; if two Firecrawl
   servers are connected, use the one that has it). Otherwise use the CLI, which needs an API
   key for crawl: keyless Firecrawl covers search, scrape, parse and the indexes only. Check
   with `npx -y firecrawl-cli@latest --status`; `Not authenticated` means ask the user for a
   key, and offer a bounded alternative meanwhile.
3. **Bound it.** A crawl follows only child URLs of its seed and stops at `--limit` (default
   10,000 pages; Firecrawl docs, checked 2026-10-10). Seed it at the path, set `--limit` a
   little above the page count you expect, and tell the user that count first:

   ```bash
   npx -y firecrawl-cli@latest crawl "https://docs.example.com/guides" \
     --limit 200 --wait -o guides.json
   ```

## References

- [references/cli-commands.md](references/cli-commands.md): every CLI command and flag, freshness, blocked pages, setup commands to avoid.
- [references/developer-index.md](references/developer-index.md): developer-index filters, result shape, query technique.
- [references/rest-api.md](references/rest-api.md): REST endpoints when neither MCP nor the CLI fits.
