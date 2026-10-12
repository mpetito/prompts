import { test, expect } from '@playwright/test';
import { invoiceCopy } from './invoice-copy';

test.describe.configure({ mode: 'serial' });

let invoiceNumber: string;

test('creates a draft invoice', async ({ page }) => {
  await page.goto('/invoices/new');
  await page.getByRole('textbox', { name: invoiceCopy.customer }).fill('Northwind Traders');
  await page.getByRole('button', { name: invoiceCopy.create }).click();
  invoiceNumber = (await page.getByTestId('invoice-number').textContent())!;
  await expect(page.getByTestId('invoice-status')).toHaveText(invoiceCopy.status.draft);
});

test('adds a line to the draft', async ({ page }) => {
  await page.goto(`/invoices/${invoiceNumber}`);
  await page.getByRole('button', { name: invoiceCopy.addLine }).click();
  await page.getByRole('textbox', { name: invoiceCopy.lineDescription }).fill('Consulting');
  await page.getByRole('spinbutton', { name: invoiceCopy.lineAmount }).fill('1200');
  await page.getByRole('button', { name: invoiceCopy.saveLine }).click();
  await expect(page.getByTestId('invoice-total')).toHaveText('$1,200.00');
});

test('marks the invoice paid', async ({ page }) => {
  await page.goto(`/invoices/${invoiceNumber}`);
  await page.getByRole('button', { name: invoiceCopy.markPaid }).click();
  await expect(page.getByTestId('invoice-status')).toHaveText(invoiceCopy.status.paid);
});
