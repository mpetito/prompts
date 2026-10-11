// Shipping quotes for checkout. CI runs eslint with complexity: ["error", 10].
export type Address = {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
};

export type Parcel = { weightKg: number; longestSideCm: number; hazmat: boolean };

export type ShippingRequest = {
  address: Address;
  parcels: Parcel[];
  subtotalUsd: number;
  speed: "standard" | "express";
};

export type Quote = { carrier: "usps" | "ups" | "freight"; amountUsd: number; days: number };

const PO_BOX = /\bp\.?\s*o\.?\s*box\b/i;

// eslint-disable-next-line complexity -- a flat checklist of independent address problems
export function addressProblems(address: Address): string[] {
  const problems: string[] = [];
  if (!address.line1.trim()) problems.push("street address is required");
  if (!address.city.trim()) problems.push("city is required");
  if (address.country !== "US") problems.push("we only ship within the US");
  if (address.state.length !== 2) problems.push("state must be a two-letter code");
  if (!/^\d{5}(-\d{4})?$/.test(address.postalCode)) problems.push("ZIP code is not valid");
  if (address.line2 && address.line2.length > 60) problems.push("address line 2 is too long");
  if (PO_BOX.test(address.line1) && address.line2) problems.push("PO boxes take one address line");
  if (address.city.length > 40) problems.push("city name is too long");
  if (address.line1.length > 60) problems.push("street address is too long");
  return problems;
}

export function quoteShipping(request: ShippingRequest): Quote {
  const weight = request.parcels.reduce((sum, p) => sum + p.weightKg, 0);
  const oversized = request.parcels.some((p) => p.longestSideCm > 150);
  const hazmat = request.parcels.some((p) => p.hazmat);
  const poBox = PO_BOX.test(request.address.line1);

  if (oversized || weight > 70) {
    return { carrier: "freight", amountUsd: 95 + weight * 1.1, days: 7 };
  }
  let quote: Quote;
  if (poBox) {
    quote = { carrier: "usps", amountUsd: 6 + weight * 0.9, days: 5 };
  } else if (request.speed === "express") {
    quote = { carrier: "ups", amountUsd: 18 + weight * 1.6, days: 2 };
  } else if (weight < 1) {
    quote = { carrier: "usps", amountUsd: 5.5, days: 4 };
  } else {
    quote = { carrier: "ups", amountUsd: 8 + weight * 0.8, days: 4 };
  }
  if (hazmat && quote.carrier === "usps") {
    quote = { carrier: "ups", amountUsd: quote.amountUsd + 12, days: quote.days + 1 };
  } else if (hazmat) {
    quote = { ...quote, amountUsd: quote.amountUsd + 12 };
  }
  if (request.parcels.length > 3) {
    quote = { ...quote, amountUsd: quote.amountUsd + 4 * (request.parcels.length - 3) };
  }
  return { ...quote, amountUsd: Math.round(quote.amountUsd * 100) / 100 };
}
