# Session snapshot: an offline copy of a docs section

## Environment

- Claude Code session in the user's repository `~/dev/support-bot`, 2026-10-10.
- Tools available besides the ones below: Read, Write, Bash (with `npx`). `FIRECRAWL_API_KEY`
  is not set and `~/.config/firecrawl` does not exist.
- The guides index at https://docs.example.com/guides links about 140 guide pages, some nested
  two levels deep (for example `/guides/auth/sso/okta`).

## The user's request

> Download every page under https://docs.example.com/guides and save the text locally so I can
> grep it offline.

## The session's tools (copied from the live session on 2026-10-10)

The session can call the tools listed here and nothing else from the web. Tool names are shown
bare; the host prefixes them (for example `mcp__claude_ai_Firecrawl__firecrawl_scrape`).

### Firecrawl MCP server: its instructions, word for word

> Authenticated search combines web results, semantic tool summaries and domain matches. Use sources: ["alexandria"] for semantic tools only. A search with sources: ["web"] omits semantic provider discovery; domainTools: true can still return website-matched tools. Web-only results use domainTools: false. Tool matches describe available structured-data capabilities, not executed data. toolDetail: "compact" (default) returns only provider, capability and description; "summary" adds metadata; "full" includes their input and output contracts. firecrawl_scrape with an alexandria body executes a selected capability; firecrawl_find_tools provides catalogue browsing and full contracts. Firecrawl provides web, developer, government, and research search, and executes catalogued Alexandria data providers. Use firecrawl_search to find relevant results across the web and specialized indexes; authenticated searches also return matching Alexandria providers in data.tools. firecrawl_find_tools provides catalogue browsing and provider contracts; firecrawl_scrape with an alexandria body executes a selected capability; firecrawl_scrape with a url retrieves one supplied page. For a programming question, firecrawl_developer_search searches indexed public repositories, GitHub issues, merged pull requests, READMEs, and code documentation and returns the matched passages, and skills: "only" narrows it to agent-skill files; firecrawl_search with categories: ["developer"] reaches the same index beside ordinary web results, returning the hits in the web group rather than as passages and offering no skills filter. For a legal or regulatory question, firecrawl_gov_search searches primary law and regulatory material from US federal, state, and local government sources: statutes, regulations, codes, court opinions, and other government publications; firecrawl_search with categories: ["gov"] reaches the same sources in the web group and cannot be combined with other categories. For a biomedical, life-science, clinical, or arXiv literature question, the firecrawl_research_* tools search the paper index, while categories: ["research"] on firecrawl_search filters ordinary web results to research-affiliated websites. Use the firecrawl_research_* tools to search academic and research literature, expand from anchor papers via the citation graph, and read full-text passages from a specific paper. Search and discovery tools are read-only and return ranked results. Billing: web, developer, and research search are billed per request; government search is free; Alexandria discovery (firecrawl_search with sources ["alexandria"] alone, and firecrawl_find_tools) is free; firecrawl_scrape is billed, as a page retrieval in url mode or at each executed capability's listed price in alexandria mode.

### Firecrawl tool descriptions, word for word except where marked as an excerpt

**firecrawl_search**

> Search web and specialized indexes, returning ranked results with query-relevant highlights. Each web result is a title, URL, and description. Operators include quoted phrases, `-term`, `site:host`, `inurl:term`, `intitle:term`, and `related:host`; the set is non-exhaustive. `includeDomains` and `excludeDomains` are mutually exclusive hostname filters; categories limit result types to `research`, `pdf`, `developer`, or `gov`.
>
> For a programming question, add `categories: ["developer"]`. It searches an index of public repositories, GitHub issues, merged pull requests, repository READMEs, and code documentation, and returns the results in `data.web` with `category: "developer"`.
>
> For a legal or regulatory question, `categories: ["gov"]` returns results in `data.web` with `category: "gov"` and cannot be combined with other categories; `firecrawl_gov_search` is the dedicated tool. Verify gov results' issuer, jurisdiction, status, and version before citing current law.
>
> Authenticated search combines web results, semantic tool summaries and domain matches. Use sources: ["alexandria"] for semantic tools only. A search with sources: ["web"] omits semantic provider discovery; domainTools: true can still return website-matched tools. Web-only results use domainTools: false. Tool matches describe available structured-data capabilities, not executed data. toolDetail: "compact" (default) returns only provider, capability and description; "summary" adds metadata; "full" includes their input and output contracts. firecrawl_scrape with an alexandria body executes a selected capability; firecrawl_find_tools provides catalogue browsing and full contracts.
>
> Returns result groups in `data` and an operation `id`.

Parameters: `query` (required), `limit` (1-100), `sources`, `categories`, `includeDomains`, `excludeDomains`, `tbs`, `location`, `filter`, `highlights`, `objective`, `clientModel`, `domainTools`, `toolDetail`, `enterprise`.

**firecrawl_scrape**

> Scrape one URL and return its content, or execute catalogued Alexandria capabilities. URL mode returns markdown by default, or HTML, links, screenshots, branding data, a targeted answer, or JSON matching a supplied schema, plus page metadata. Firecrawl may serve recently indexed content; set `maxAge: 0` for a live fetch. A successful response does not by itself confirm the page is still current. A named browser profile loads saved session data without saving changes to it.
>
> `firecrawl_search` with `sources` unset and `firecrawl_find_tools` can discover providers for the same fields across several pages; a matching Alexandria provider returns typed records in one call.
>
> Alexandria mode: `alexandria` selects catalogued capability execution and is mutually exclusive with `url`. Alexandria execution is billed at the capability's listed price and needs a team with Alexandria enabled.

Parameters: `url`, `formats` (any of `markdown`, `html`, `rawHtml`, `screenshot`, `links`, `images`, `summary`, `changeTracking`, `branding`, `json`, `query`, `audio`), `onlyMainContent`, `maxAge`, `waitFor`, `includeTags`, `excludeTags`, `jsonOptions` (`prompt`, `schema`), `queryOptions` (`prompt`, `mode`), `proxy` (`basic`, `stealth`, `enhanced`, `auto`), `location`, `mobile`, `parsers`, `pdfOptions`, `profile`, `lockdown`, `redactPII`, `removeBase64Images`, `skipTlsVerification`, `storeInCache`, `timeout`, `zeroDataRetention`, `alexandria`, `domainTools`, `toolDetail`, `requestId`.

**firecrawl_developer_search**

> Search an index of public repositories, GitHub issues, merged pull requests, repository READMEs, and code documentation for programming questions that need external documentation or upstream evidence.
>
> Returns ranked results with an ID, source type, URL, title, and the matched passages in markdown.

Parameters: `query` (required), `k` (1-100, default 10), `skills` (`"only"`).

**firecrawl_gov_search** (excerpt: first paragraph)

> Search US federal, state, and local statutes, regulations, codes, court opinions, and other government publications for legal or regulatory questions that need primary text. Clarify a missing jurisdiction or ambiguous as-of date before identifying the governing rule.

(excerpt, summarised) **firecrawl_research_search_papers**, **firecrawl_research_read_paper**, **firecrawl_research_inspect_paper**, **firecrawl_research_related_papers**: the research paper index (search, read passages, metadata, citation graph).

**firecrawl_find_tools** (excerpt)

> Browse Alexandria data providers and workflows or read a selected contract. [...] Discovery is free.

There is no `firecrawl_crawl`, `firecrawl_map`, `firecrawl_extract` or `firecrawl_parse` tool in this session.

### WebFetch (built in), word for word except one omitted bullet about claude.ai artifact links

> Fetches a URL, converts the page to markdown, and answers `prompt` against it using a small fast model.
>
> - Fails on authenticated/private URLs — use an authenticated MCP tool or `gh` for those instead.
> - Fails on localhost and other hostnames without a dot; for a local server, use curl via Bash.
> - HTTP is upgraded to HTTPS. Cross-host redirects are returned to you rather than followed; call again with the redirect URL.
> - Responses are cached for 15 minutes per URL.
