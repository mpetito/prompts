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

## Architecture

```
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

## Instructions

### Step 1: SEO Constants and Metadata Utility

```ts
// lib/seo.ts
import type { Metadata } from "next";

export const SITE_NAME = "Your Site Name";
export const SITE_DESCRIPTION = "Your site description for SEO";
export const SITE_URL =
  process.env.NEXT_PUBLIC_SERVER_URL ?? "https://yoursite.com";
export const SITE_LOCALE = "en_US";
export const TWITTER_HANDLE = "@yourhandle";
export const DEFAULT_OG_IMAGE = `${SITE_URL}/images/og-default.jpg`;

export function generatePageMetadata({
  title,
  description,
  path = "",
  image,
  imageAlt,
  type = "website",
  noIndex = false,
  keywords,
}: {
  title: string;
  description: string;
  path?: string;
  image?: string;
  imageAlt?: string;
  type?: "website" | "article" | "product";
  noIndex?: boolean;
  keywords?: string[];
}): Metadata {
  const url = `${SITE_URL}${path}`;
  const ogImage = image ?? DEFAULT_OG_IMAGE;

  return {
    title: `${title} | ${SITE_NAME}`,
    description,
    keywords: keywords?.join(", "),
    alternates: { canonical: url },
    robots: noIndex
      ? { index: false, follow: false }
      : {
          index: true,
          follow: true,
          "max-image-preview": "large",
          "max-snippet": -1,
          "max-video-preview": -1,
        },
    openGraph: {
      title: `${title} | ${SITE_NAME}`,
      description,
      url,
      siteName: SITE_NAME,
      locale: SITE_LOCALE,
      type: type === "product" ? "website" : type,
      images: [
        { url: ogImage, width: 1200, height: 630, alt: imageAlt ?? title },
      ],
    },
    twitter: {
      card: "summary_large_image",
      site: TWITTER_HANDLE,
      title: `${title} | ${SITE_NAME}`,
      description,
      images: [ogImage],
    },
  };
}
```

**Product-specific metadata (enhanced OG tags):**

```ts
interface ProductMetadataParams {
  name: string;
  description: string;
  slug: string;
  price: number; // cents
  image?: string;
  inStock: boolean;
  category?: string;
}

export function generateProductMetadata({
  name,
  description,
  slug,
  price,
  image,
  inStock,
  category,
}: ProductMetadataParams) {
  const base = generatePageMetadata({
    title: name,
    description,
    path: `/products/${slug}`,
    image,
    type: "product",
    keywords: [name.toLowerCase(), "your", "keywords"],
  });

  return {
    ...base,
    other: {
      "og:type": "product",
      "product:price:amount": (price / 100).toFixed(2),
      "product:price:currency": "USD",
      "product:availability": inStock ? "in stock" : "out of stock",
      "product:condition": "new",
      "product:brand": SITE_NAME,
      ...(category && { "product:category": category }),
    },
  };
}
```

### Step 2: JSON-LD Structured Data

**Generic renderer (works in Server Components):**

```tsx
// components/seo/JsonLd.tsx
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data, null, 0) }}
    />
  );
}
```

**Multiple JSON-LD blocks per page are valid and recommended by Google.** Use separate blocks for different entity types.

### JSON-LD Generator Functions

**Organization:**

```ts
export function organizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": `${SITE_URL}/#organization`,
    name: SITE_NAME,
    url: SITE_URL,
    logo: {
      "@type": "ImageObject",
      url: `${SITE_URL}/images/logo.png`,
      width: 512,
      height: 512,
    },
    sameAs: [
      "https://social.example.com/yourprofile",
      "https://profiles.example.com/yourprofile",
    ],
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "customer service",
      email: "hello@yoursite.com",
    },
  };
}
```

**Product (with offers, shipping, return policy):**

```ts
interface ProductJsonLdParams {
  name: string;
  description: string;
  slug: string;
  price: number; // cents
  image?: string;
  sku?: string;
  inStock: boolean;
  rating?: number;
  reviewCount?: number;
}

export function productJsonLd({
  name,
  description,
  slug,
  price,
  image,
  sku,
  inStock,
  rating,
  reviewCount,
}: ProductJsonLdParams) {
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name,
    description,
    image: image ?? DEFAULT_OG_IMAGE,
    sku: sku ?? slug,
    brand: { "@type": "Brand", name: SITE_NAME },
    offers: {
      "@type": "Offer",
      url: `${SITE_URL}/products/${slug}`,
      priceCurrency: "USD",
      price: (price / 100).toFixed(2),
      availability: inStock
        ? "https://schema.org/InStock"
        : "https://schema.org/OutOfStock",
      itemCondition: "https://schema.org/NewCondition",
      shippingDetails: {
        "@type": "OfferShippingDetails",
        shippingRate: {
          "@type": "MonetaryAmount",
          value: "5.99",
          currency: "USD",
        },
        shippingDestination: { "@type": "DefinedRegion", addressCountry: "US" },
        deliveryTime: {
          "@type": "ShippingDeliveryTime",
          handlingTime: {
            "@type": "QuantitativeValue",
            minValue: 1,
            maxValue: 3,
            unitCode: "d",
          },
          transitTime: {
            "@type": "QuantitativeValue",
            minValue: 3,
            maxValue: 7,
            unitCode: "d",
          },
        },
      },
      hasMerchantReturnPolicy: {
        "@type": "MerchantReturnPolicy",
        returnPolicyCategory:
          "https://schema.org/MerchantReturnFiniteReturnWindow",
        merchantReturnDays: 30,
        returnMethod: "https://schema.org/ReturnByMail",
        returnFees: "https://schema.org/FreeReturn",
      },
    },
    ...(rating &&
      reviewCount && {
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: rating.toFixed(1),
          reviewCount,
          bestRating: "5",
          worstRating: "1",
        },
      }),
  };
}
```

**FAQPage (critical for AEO):**

```ts
export function faqJsonLd(questions: { question: string; answer: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: questions.map((q) => ({
      "@type": "Question",
      name: q.question,
      acceptedAnswer: { "@type": "Answer", text: q.answer },
    })),
  };
}
```

**BreadcrumbList:**

```ts
export function breadcrumbJsonLd(items: { name: string; url: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: item.url,
    })),
  };
}
```

**HowTo (for configurators/tutorials):**

```ts
interface HowToJsonLdParams {
  name: string;
  description: string;
  steps: { name: string; text: string }[];
  totalTime?: string; // ISO 8601 duration, e.g. "PT5M"
}

export function howToJsonLd({
  name,
  description,
  steps,
  totalTime,
}: HowToJsonLdParams) {
  return {
    "@context": "https://schema.org",
    "@type": "HowTo",
    name,
    description,
    ...(totalTime && { totalTime }), // ISO 8601: "PT5M"
    step: steps.map((step, i) => ({
      "@type": "HowToStep",
      position: i + 1,
      name: step.name,
      text: step.text,
    })),
  };
}
```

**Speakable (voice search / AEO):**

```ts
export function speakableJsonLd({
  url,
  cssSelectors,
}: {
  url: string;
  cssSelectors: string[];
}) {
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    url,
    speakable: { "@type": "SpeakableSpecification", cssSelector: cssSelectors },
  };
}
```

### Step 3: FAQ Component (Dual Rendering)

**Google requires visible HTML to match JSON-LD 1:1.** The FAQ component renders both:

```tsx
import { JsonLd } from "./JsonLd";
import { faqJsonLd } from "@/lib/structured-data";

interface FAQProps {
  questions: { id: string; question: string; answer: string }[];
  heading?: string;
}

export function FAQ({
  questions,
  heading = "Frequently Asked Questions",
}: FAQProps) {
  return (
    <section
      aria-labelledby="faq-heading"
      itemScope
      itemType="https://schema.org/FAQPage"
    >
      <JsonLd data={faqJsonLd(questions)} />
      <h2 id="faq-heading">{heading}</h2>
      <div className="space-y-6">
        {questions.map((q) => (
          <details
            key={q.id}
            className="group border rounded-lg"
            itemScope
            itemProp="mainEntity"
            itemType="https://schema.org/Question"
            data-testid={`faq-item-${q.id}`}
          >
            <summary
              className="cursor-pointer px-6 py-4 font-medium"
              itemProp="name"
            >
              {q.question}
              <ChevronIcon className="group-open:rotate-180 transition-transform" />
            </summary>
            <div
              className="px-6 pb-4 text-sm"
              itemScope
              itemProp="acceptedAnswer"
              itemType="https://schema.org/Answer"
            >
              <div itemProp="text">{q.answer}</div>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
```

**Why dual rendering:** The JSON-LD tells search engines the FAQ content. The visible HTML with matching microdata (`itemScope`, `itemProp`) proves the content is actually displayed to users. Google can penalize hidden-only structured data.

### Step 4: robots.txt with AI Bot Allowlisting

```ts
// app/robots.ts
import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin/", "/api/", "/account/", "/checkout/", "/cart/"],
      },
      // Explicitly allow AI answer engines
      {
        userAgent: "GPTBot",
        allow: "/",
        disallow: ["/admin/", "/api/", "/account/"],
      },
      {
        userAgent: "PerplexityBot",
        allow: "/",
        disallow: ["/admin/", "/api/", "/account/"],
      },
      {
        userAgent: "ClaudeBot",
        allow: "/",
        disallow: ["/admin/", "/api/", "/account/"],
      },
      {
        userAgent: "Google-Extended",
        allow: "/",
        disallow: ["/admin/", "/api/", "/account/"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
```

**AEO strategy:** Many sites block AI crawlers by default. Explicitly allowing them means your FAQ schema, speakable content, and product data get surfaced in AI-generated answers.

### Step 5: Dynamic XML Sitemap

```ts
// app/sitemap.ts
import type { MetadataRoute } from "next";
import { getCmsClient } from "@/lib/cms";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const cms = await getCmsClient();

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: SITE_URL,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/products`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
  ];

  // Dynamic product pages from CMS
  const products = await cms.find({ collection: "products", limit: 1000 });
  const productPages: MetadataRoute.Sitemap = products.docs.map((p) => ({
    url: `${SITE_URL}/products/${p.slug}`,
    lastModified: new Date(p.updatedAt),
    changeFrequency: "weekly" as const,
    priority: 0.8,
  }));

  return [...staticPages, ...productPages];
}
```

### Step 6: RSS Feed

```ts
// app/feed.xml/route.ts
function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET() {
  const posts = await getCmsClient().then((cms) =>
    cms.find({
      collection: "blog-posts",
      where: { status: { equals: "published" } },
    }),
  );

  const items = posts.docs
    .map(
      (post) => `
    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${SITE_URL}/blog/${post.slug}</link>
      <description>${escapeXml(post.excerpt ?? "")}</description>
      <pubDate>${new Date(post.publishedAt).toUTCString()}</pubDate>
      <guid isPermaLink="true">${SITE_URL}/blog/${post.slug}</guid>
    </item>`,
    )
    .join("");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(SITE_NAME)} Blog</title>
    <link>${SITE_URL}/blog</link>
    <description>${escapeXml(SITE_DESCRIPTION)}</description>
    <language>en-us</language>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    ${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
    },
  });
}
```

**Link in layout:**

```tsx
<link
  rel="alternate"
  type="application/rss+xml"
  title="Blog"
  href="/feed.xml"
/>
```

### Step 7: Analytics + Web Vitals

Keep application code behind a provider-agnostic analytics wrapper. Your analytics provider (e.g. GA4/Plausible) can sit behind this abstraction, but React components should not call vendor globals directly.

```ts
// lib/analytics.ts
export type AnalyticsEvent = {
  name: string;
  properties?: Record<string, unknown>;
};

export function trackAnalyticsEvent(event: AnalyticsEvent) {
  if (typeof window === "undefined") return;

  window.dispatchEvent(new CustomEvent("analytics:event", { detail: event }));
}

export function trackPageView(path: string) {
  trackAnalyticsEvent({ name: "page_view", properties: { path } });
}
```

```tsx
// components/analytics/AnalyticsProvider.tsx
"use client";

import { trackPageView } from "@/lib/analytics";
import { reportWebVitals } from "@/lib/web-vitals";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

export function AnalyticsProvider() {
  const pathname = usePathname();

  useEffect(() => {
    trackPageView(pathname);
  }, [pathname]);

  useEffect(() => {
    // Report Web Vitals once
    reportWebVitals();
  }, []);

  return null;
}
```

## Page-Level Usage

```tsx
// app/(frontend)/page.tsx
import { JsonLd } from "@/components/seo/JsonLd";
import { FAQ } from "@/components/seo/FAQ";
import {
  breadcrumbJsonLd,
  speakableJsonLd,
  organizationJsonLd,
} from "@/lib/structured-data";

export const metadata = generatePageMetadata({
  title: "Your Page Title",
  description: "Your page description",
  path: "/",
  keywords: ["keyword1", "keyword2"],
});

export default function HomePage() {
  return (
    <>
      <JsonLd data={organizationJsonLd()} />
      <JsonLd data={breadcrumbJsonLd([{ name: "Home", url: SITE_URL }])} />
      <JsonLd
        data={speakableJsonLd({
          url: SITE_URL,
          cssSelectors: ['[data-testid="hero"] h1', '[data-testid="hero"] p'],
        })}
      />

      {/* Page content */}

      <FAQ questions={[{ question: "What is this?", answer: "This is..." }]} />
    </>
  );
}
```

## Common Pitfalls

1. **FAQ mismatch**: JSON-LD questions MUST match visible HTML exactly. Google can penalize mismatches.
2. **Missing canonical URLs**: Every page needs `alternates.canonical`. Duplicate content without canonicals hurts ranking.
3. **Price format in JSON-LD**: Use dollars with 2 decimal places (`"24.99"`), not cents. Payment processors often use cents; schema.org uses dollars.
4. **robots.txt blocking AI bots**: Many default configs block GPTBot/PerplexityBot. If you want AEO, explicitly allow them.
5. **Sitemap without dynamic pages**: Static sitemaps miss product pages. Query your CMS for complete coverage.
6. **Missing OG images**: Social sharing without OG images looks unprofessional. Always provide a 1200x630 default.
7. **Speakable selectors**: Point to actual content elements (headings, paragraphs), not containers. Use data-testid selectors for stability.
