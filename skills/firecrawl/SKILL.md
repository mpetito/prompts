---
name: firecrawl
description: "Fetch many web pages with Firecrawl without flooding the context: write a docs path's pages to files, and ask each page for its fields instead of its full text. Use when a request needs every page under a site or docs path saved locally, a docs section mirrored for offline search or indexing, or the same facts pulled from many pages into a table or JSON, even when the Firecrawl scrape tool or WebFetch looks enough. Not for one page or a few pages, or a developer-index or library-docs lookup (the Firecrawl MCP tools' own descriptions cover those), testing or driving your own app in a browser (Playwright tools), adding Firecrawl calls to a product's code (Firecrawl SDK docs), or searching the local repository."
---

# Firecrawl: many pages

Role: domain reference, read by whichever session must fetch many pages; detail is in
`references/`.

The Firecrawl MCP server's instructions and tool descriptions cover single pages, search and its
indexes. Each MCP scrape returns its whole page into the conversation, so for many pages choose
by what the user needs from them:

1. **Full text of many pages under one path: write them to files, never into the context.**
   - With a key (a crawl tool such as `firecrawl_crawl`, or the CLI when
     `npx -y firecrawl-cli@latest --status` shows it authenticated): one crawl, seeded at the
     path and written to a file. A crawl follows only child URLs of its seed and stops at
     `--limit` (default 10,000 pages; Firecrawl docs, checked 2026-10-10), so set `--limit` a
     little above the page count you expect and tell the user that count first.

     ```bash
     npx -y firecrawl-cli@latest crawl "https://docs.example.com/guides" --limit 200 --wait -o guides.json
     ```

   - Without a key: take the URL list from one scrape of the index with `formats: ["links"]`,
     state the count, then pass the URLs to one CLI `scrape`, which saves each page to its own
     file under `.firecrawl/` (add it to `.gitignore`). Keyless use is capped per IP per day and
     the docs give no number, so a long list may stop partway; offer a key for one bounded crawl.

     ```bash
     npx -y firecrawl-cli@latest scrape $(cat guide-urls.txt) --only-main-content
     ```

2. **Fields or answers across many pages: ask each page for them, not for its text.** Scrape
   each with `formats: ["json"]` and a `jsonOptions.schema`, or `formats: ["query"]` and a
   `queryOptions.prompt`, and keep the URL with each answer. Either costs 5 credits a page
   against 1 for markdown (Firecrawl scrape docs, checked 2026-10-10), and extraction can miss
   or reword items: when every item or the exact wording matters, ask the schema for verbatim
   items, or write the pages to files (rule 1) and read them there.

## References

- [references/cli-commands.md](references/cli-commands.md): the CLI commands and flags this skill uses, freshness, blocked pages; `--help` for the rest.
- [references/rest-api.md](references/rest-api.md): REST endpoints when neither MCP nor the CLI fits.
