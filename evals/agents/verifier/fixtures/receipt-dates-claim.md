# Claim to verify

From the author of PR #412, after merging it:

> Fixed the receipt date bug. `formatReceiptDate` now passes `timeZone: 'UTC'`, so every
> receipt date we render is in UTC. The new test proves it.

The caller pasted the files below from the repository at the merge commit, with line numbers.
The servers run with `TZ=America/New_York`.

## src/dates/format.ts

```ts
1  export function formatReceiptDate(d: Date): string {
2    return d.toLocaleDateString('en-US', {
3      timeZone: 'UTC', year: 'numeric', month: 'short', day: 'numeric',
4    });
5  }
```

## src/dates/format.test.ts

```ts
1  import { formatReceiptDate } from './format';
2
3  test('formats receipt dates in UTC', () => {
4    const d = new Date('2026-03-01T02:00:00Z');
5    expect(formatReceiptDate(d)).toBe('Mar 1, 2026');
6  });
```

## src/receipts/pdf.ts (excerpt)

```ts
12 export function renderReceiptPdf(receipt: Receipt): Pdf {
13   const doc = new Pdf();
14   const issued = formatReceiptDate(receipt.issuedAt);
15   doc.text(`Issued ${issued}`);
```

## src/receipts/email.ts (excerpt)

```ts
18 export function receiptEmailBody(receipt: Receipt): string {
19   const lines = [`Thanks for your order, ${receipt.customerName}.`];
20   lines.push(`Order ${receipt.number}`);
21   lines.push(`Total ${formatMoney(receipt.total)}`);
22   const issued = receipt.issuedAt.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
23   lines.push(`Issued ${issued}`);
24   return lines.join('\n');
25 }
```

## src/receipts/csv.ts (excerpt)

```ts
7  export function receiptCsvRow(receipt: Receipt): string[] {
8    const row = [receipt.number];
9    row.push(receipt.issuedAt.toISOString().slice(0, 10));
10   return row;
11 }
```

## Output of `git grep -n "issuedAt" src/`

```text
src/receipts/csv.ts:9:    row.push(receipt.issuedAt.toISOString().slice(0, 10));
src/receipts/email.ts:22:  const issued = receipt.issuedAt.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
src/receipts/pdf.ts:14:  const issued = formatReceiptDate(receipt.issuedAt);
```
