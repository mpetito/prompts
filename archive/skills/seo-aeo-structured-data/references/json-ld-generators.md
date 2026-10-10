# JSON-LD Generators and Components

Generator functions for `lib/structured-data.ts` and the components that render them.
Multiple JSON-LD blocks per page are valid and recommended by Google — use a separate block
per entity type.

## Generic Renderer

Works in Server Components:

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

---

## Organization

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

## Product (with offers, shipping, return policy)

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

**Note the units**: prices are stored in cents but schema.org expects dollars with two decimal
places (`"24.99"`).

## FAQPage (critical for AEO)

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

## BreadcrumbList

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

## HowTo (for configurators/tutorials)

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
    ...(totalTime && { totalTime }),
    step: steps.map((step, i) => ({
      "@type": "HowToStep",
      position: i + 1,
      name: step.name,
      text: step.text,
    })),
  };
}
```

## Speakable (voice search / AEO)

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

Point selectors at actual content elements (headings, paragraphs), not containers, and prefer
`data-testid` selectors for stability.

---

## FAQ Component (Dual Rendering)

Google requires visible HTML to match JSON-LD 1:1, so the component renders both.

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

**Why dual rendering:** the JSON-LD tells search engines the FAQ content; the visible HTML with
matching microdata (`itemScope`, `itemProp`) proves the content is actually displayed to users.
Google can penalize hidden-only structured data.

---

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
