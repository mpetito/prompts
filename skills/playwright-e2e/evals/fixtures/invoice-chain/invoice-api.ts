import type { APIRequestContext } from '@playwright/test';

// Test-only endpoints, enabled when the server runs with TEST_API=1.
export type InvoiceSeed = {
  customer: string;
  lines?: { description: string; amount: number }[];
  status?: 'draft' | 'sent' | 'paid';
};

/** Creates an invoice directly in the database and returns its number. */
export async function createInvoice(request: APIRequestContext, seed: InvoiceSeed): Promise<string> {
  const response = await request.post('/test-api/invoices', { data: seed });
  if (!response.ok()) throw new Error(`createInvoice failed: ${response.status()}`);
  return (await response.json()).number;
}
