---
name: seo-aeo-structured-data
description: |
  Use when optimizing for search engines or AI answer engines (ChatGPT, Perplexity, Google AI Overviews), or adding structured data / JSON-LD to a React/Next.js site.
---

# SEO, AEO, and Structured Data

## When to Use This Skill

Use when:

- Setting up SEO metadata for a Next.js application
- Implementing JSON-LD structured data for rich results
- Optimizing for AI answer engines (AEO): ChatGPT, Perplexity, Google AI Overviews
- Creating sitemaps, robots.txt, or RSS feeds
- Adding Open Graph and Twitter Card metadata
- Monitoring Core Web Vitals

Implementations live in reference files; this file carries the architecture, the decisions, and
the ways it goes wrong.

| Reference                                                                    | Contains                                                                        |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| [`references/json-ld-generators.md`](references/json-ld-generators.md)       | `JsonLd` renderer, Organization/Product/FAQ/Breadcrumb/HowTo/Speakable generators, FAQ component, page-level usage |
| [`references/metadata-sitemap-rss.md`](references/metadata-sitemap-rss.md)   | `generatePageMetadata`, product metadata, `robots.ts`, `sitemap.ts`, `feed.xml`, analytics wiring |

## Architecture

```text
lib/
├── seo.ts              # Site constants, generatePageMetadata(), generateProductMetadata()
├── structured-data.ts  # JSON-LD generator functions
├── analytics.ts        # Provider-agnostic event tracking
└── web-vitals.ts       # CLS, INP, LCP, FCP, TTFB reporting

components/
├── seo/
│   ├── JsonLd.tsx      # Generic JSON-LD renderer
│   └── FAQ.tsx         # FAQ with visible HTML + JSON-LD
└── analytics/
    └── AnalyticsProvider.tsx  # Client-side analytics scripts

app/
├── sitemap.ts          # Dynamic XML sitemap
├── robots.ts           # robots.txt with AI bot rules
├── feed.xml/route.ts   # RSS feed
└── layout.tsx          # Global metadata
```

The shape matters more than the file names: **one source of site constants**, **one metadata
factory**, **one JSON-LD renderer**, and generators that are pure functions returning plain
objects. That keeps structured data testable and prevents per-page drift.

## Build Order

1. **Site constants + `generatePageMetadata`** — everything else depends on `SITE_URL`.
2. **`JsonLd` renderer**, then generators as pages need them.
3. **`robots.ts` and `sitemap.ts`** — cheap, and they gate discovery of everything else.
4. **FAQ component** where AEO matters most.
5. **RSS + analytics/Web Vitals** last.

## Key Decisions

**Multiple JSON-LD blocks per page are valid** and recommended by Google. Use a separate block
per entity type rather than trying to merge Organization, Breadcrumb, and Product into one graph.

**FAQ content must be dual-rendered.** Google requires visible HTML matching the JSON-LD 1:1, so
the FAQ component emits both the JSON-LD and visible markup carrying the same content via
microdata (`itemScope`, `itemProp`). Hidden-only structured data can be penalized.

**Explicitly allow AI crawlers if you want AEO.** Many default `robots.txt` configs block GPTBot
and PerplexityBot. Allowing them is what makes your FAQ schema, speakable content, and product
data eligible to appear in AI-generated answers. This is a deliberate trade-off — decide it,
don't inherit it.

**Prices are cents internally, dollars in schema.org.** Storage and arithmetic use integer
cents (see [`ecommerce-patterns`](../ecommerce-patterns/SKILL.md)); JSON-LD `price` and
`product:price:amount` need `"24.99"` with two decimals.

**Speakable selectors point at content, not containers** — headings and paragraphs, ideally via
stable `data-testid` selectors.

**One analytics pipeline.** Web Vitals and commerce events go through the same provider-agnostic
wrapper. `reportWebVitals` and `trackEcommerceEvent` are defined once in
[`ecommerce-patterns`](../ecommerce-patterns/SKILL.md); this skill only wires them into the
client provider component.

## Common Pitfalls

1. **FAQ mismatch**: JSON-LD questions MUST match visible HTML exactly. Google can penalize mismatches.
2. **Missing canonical URLs**: every page needs `alternates.canonical`. Duplicate content without canonicals hurts ranking.
3. **Price format in JSON-LD**: use dollars with 2 decimal places (`"24.99"`), not cents.
4. **robots.txt blocking AI bots**: many default configs block GPTBot/PerplexityBot. If you want AEO, explicitly allow them.
5. **Sitemap without dynamic pages**: static sitemaps miss product pages. Query your CMS for complete coverage.
6. **Missing OG images**: social sharing without OG images looks unprofessional. Always provide a 1200x630 default.
7. **Speakable selectors on containers**: point at actual content elements, not wrappers.
8. **Unescaped XML in RSS**: user-authored titles and excerpts must go through `escapeXml` or the feed becomes invalid.
