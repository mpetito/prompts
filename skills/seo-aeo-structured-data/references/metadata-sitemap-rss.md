# Metadata, robots.txt, Sitemap, and RSS

Implementations for `lib/seo.ts` and the Next.js App Router metadata files.

## SEO Constants and Metadata Utility

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

## Product Metadata (enhanced OG tags)

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

---

## robots.txt with AI Bot Allowlisting

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

---

## Dynamic XML Sitemap

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

---

## RSS Feed

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

**Link it in the layout:**

```tsx
<link
  rel="alternate"
  type="application/rss+xml"
  title="Blog"
  href="/feed.xml"
/>
```

---

## Analytics Provider Wiring

Keep application code behind a provider-agnostic wrapper — React components should never call
vendor globals directly.

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

`reportWebVitals` itself is defined in the `ecommerce-patterns` skill —
[`references/orders-giftcards-analytics.md`](../../ecommerce-patterns/references/orders-giftcards-analytics.md).
For commerce events specifically, use `trackEcommerceEvent` from that same file rather than
adding a second event pipeline.
