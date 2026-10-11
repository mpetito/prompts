# Repository snapshot: tally, spec 011 in progress

A snapshot of a git repository: the path and full contents of every file in the working tree, then the recent history and the output of the last commands run in its terminal.

## Files

### AGENTS.md

````markdown
# Working on tally

- TypeScript run directly by Node (type stripping); no build step and no runtime dependencies.
- Tests use `node:test`; run them with `npm test`.
- New work starts as a numbered spec and plan in `specs/`, reviewed before any code is written.
- Keep amounts in integer cents everywhere; never use floats for money after parsing.
````

### README.md

````markdown
# tally

A small command-line tool that reads an expense CSV export and prints totals by category.

## Usage

    node src/cli.ts expenses.csv          # table
    node src/cli.ts expenses.csv --json   # JSON

## Input format

A header row, then one expense per line:

    date,description,category,amount
    2026-03-01,Coffee,food,3.50
    2026-03-02,Train,travel,12.00

Category aliases (for example `groceries` -> `food`) are applied before totalling.

## Development

    npm test
````

### package.json

````json
{
  "name": "tally",
  "version": "0.4.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test test/*.test.ts"
  }
}
````

### specs/001-csv-import/plan.md

````markdown
# Plan: CSV import

1. Parser for one row and for a whole file, with tests.
2. Per-category totals, with tests.
3. Table output and the CLI entry point.
````

### specs/001-csv-import/spec.md

````markdown
# CSV import

Date: 2026-02-03
Status: done

tally reads one CSV export per run: a header row, then date, description, category and amount per
line. Amounts are held as integer cents. A malformed row stops the run with an error that names its
line number. Totals are printed per category, sorted by category name.
````

### specs/002-category-aliases/plan.md

````markdown
# Plan: category aliases

1. Alias table and lookup, applied in the row parser.
2. Test that an alias resolves and an unknown category is lower-cased.
````

### specs/002-category-aliases/spec.md

````markdown
# Category aliases

Date: 2026-08-19
Status: done

Bank exports use several names for the same category. tally maps known aliases to one canonical
category (case-insensitive) before totalling, so `Groceries` and `restaurant` both count as `food`.
Unknown categories pass through lower-cased.
````

### specs/010-json-output/plan.md

````markdown
# Plan: JSON output

1. JSON formatter beside the table formatter.
2. `--json` flag in the CLI.
````

### specs/010-json-output/spec.md

````markdown
# JSON output

Date: 2026-05-12
Status: done

With `--json`, tally prints the per-category totals as a JSON array instead of a table, each entry
holding the category and the total as a decimal string with two places.
````

### specs/011-multi-currency-totals/plan.md

````markdown
# Plan: multi-currency totals

Spec: [spec.md](spec.md)

## Phase 1: parse currencies

- [x] 1. `src/parser.ts`: add `currency: string` to `Expense`; update the existing
  whole-row test in `test/parser.test.ts`. Check: `npm test` passes.
- [x] 2. `src/parser.ts`: in `parseRow()`, read an optional fifth column as the currency code,
  upper-cased, defaulting to `USD` when the column is missing or empty. Check: `npm test` passes.
- [x] 3. `src/parser.ts`: reject a code that is not three letters with an error naming the line.
  Check: `npm test` passes.
- [x] 4. `test/parser.test.ts`: tests for a present code, a missing column (USD), and an invalid
  code rejected with its line number. Check: `npm test` passes with the three new tests.

## Phase 2: totals and output

- [ ] 5. `src/totals.ts`, `test/totals.test.ts`: `CategoryTotal` gains `currency`;
  `sumByCategory()` groups by category and currency, sorted by category then currency. Check: a
  new test in `test/totals.test.ts` with two currencies in one category passes under `npm test`.
- [ ] 6. `src/format.ts`, `test/format.test.ts`: `formatTable()` adds a `Currency` column;
  `formatJson()` adds a `currency` field to each entry. Check: a new `test/format.test.ts`
  covering both passes under `npm test`.
- [ ] 7. `README.md`: document the optional fifth column and the USD default under "Input format",
  and show the currency in the usage output. Check: the README sample rows parse with
  `parseFile()`, and `npm test` passes.
- [ ] 8. `package.json`: bump the version to 0.5.0. Check: `npm test` prints `tally@0.5.0`.
````

### specs/011-multi-currency-totals/spec.md

````markdown
# Multi-currency totals

Date: 2026-10-09
Status: approved

## Problem

Expenses arrive in more than one currency, and tally adds them together as if they were one.

## Behaviour

- An expense row may carry an ISO 4217 currency code as an optional fifth column. A row without one
  is in USD.
- A code that is not three letters stops the run with an error naming its line.
- Totals are reported per category and currency. Amounts in different currencies are never added
  together and never converted.
- Table output shows the currency of each total; JSON output gives each entry its currency.

## Out of scope

- Exchange rates, and converting totals to a single currency.

## Decisions

- Per-currency subtotals, no conversion (owner, 2026-10-09).
- A missing column means USD, because not every bank export was confirmed to carry a code
  (owner, 2026-10-09).
- The table column is labelled `Currency`.
````

### src/aliases.ts

````ts
const ALIASES: Record<string, string> = {
  groceries: "food",
  restaurant: "food",
  taxi: "travel",
  train: "travel",
};

export function resolveCategory(raw: string): string {
  const key = raw.toLowerCase();
  return ALIASES[key] ?? key;
}
````

### src/cli.ts

````ts
import { readFileSync } from "node:fs";
import { parseFile } from "./parser.ts";
import { sumByCategory } from "./totals.ts";
import { formatJson, formatTable } from "./format.ts";

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith("--"));
if (!file) {
  console.error("usage: tally <expenses.csv> [--json]");
  process.exit(2);
}
const totals = sumByCategory(parseFile(readFileSync(file, "utf8")));
console.log(args.includes("--json") ? formatJson(totals) : formatTable(totals));
````

### src/format.ts

````ts
import type { CategoryTotal } from "./totals.ts";

function money(cents: number): string {
  return (cents / 100).toFixed(2);
}

export function formatTable(totals: CategoryTotal[]): string {
  const rows = totals.map((t) => `${t.category.padEnd(12)} ${money(t.totalCents).padStart(10)}`);
  return [`${"Category".padEnd(12)} ${"Total".padStart(10)}`, ...rows].join("\n");
}

export function formatJson(totals: CategoryTotal[]): string {
  return JSON.stringify(
    totals.map((t) => ({ category: t.category, total: money(t.totalCents) })),
    null,
    2,
  );
}
````

### src/parser.ts

````ts
import { resolveCategory } from "./aliases.ts";

export interface Expense {
  date: string;
  description: string;
  category: string;
  amountCents: number;
  currency: string;
}

const DEFAULT_CURRENCY = "USD";

export function parseRow(line: string, lineNo: number): Expense {
  const cols = line.split(",").map((c) => c.trim());
  if (cols.length < 4) {
    throw new Error(`line ${lineNo}: expected 4 columns, got ${cols.length}`);
  }
  const [date, description, category, amount, currency] = cols;
  return {
    date,
    description,
    category: resolveCategory(category),
    amountCents: toCents(amount, lineNo),
    currency: toCurrency(currency, lineNo),
  };
}

function toCents(raw: string, lineNo: number): number {
  const value = Number(raw);
  if (!Number.isFinite(value)) {
    throw new Error(`line ${lineNo}: bad amount "${raw}"`);
  }
  return Math.round(value * 100);
}

function toCurrency(raw: string | undefined, lineNo: number): string {
  if (raw === undefined || raw === "") return DEFAULT_CURRENCY;
  const code = raw.toUpperCase();
  if (!/^[A-Z]{3}$/.test(code)) {
    throw new Error(`line ${lineNo}: bad currency "${raw}"`);
  }
  return code;
}

export function parseFile(text: string): Expense[] {
  return text
    .split(/\r?\n/)
    .slice(1) // header row
    .map((line, i) => ({ line, lineNo: i + 2 }))
    .filter(({ line }) => line.trim() !== "")
    .map(({ line, lineNo }) => parseRow(line, lineNo));
}
````

### src/totals.ts

````ts
import type { Expense } from "./parser.ts";

export interface CategoryTotal {
  category: string;
  totalCents: number;
}

export function sumByCategory(expenses: Expense[]): CategoryTotal[] {
  const totals = new Map<string, number>();
  for (const e of expenses) {
    totals.set(e.category, (totals.get(e.category) ?? 0) + e.amountCents);
  }
  return [...totals]
    .map(([category, totalCents]) => ({ category, totalCents }))
    .sort((a, b) => a.category.localeCompare(b.category));
}
````

### test/parser.test.ts

````ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseFile, parseRow } from "../src/parser.ts";

test("parses a row into integer cents", () => {
  assert.deepEqual(parseRow("2026-03-01,Coffee,food,3.50", 2), {
    date: "2026-03-01",
    description: "Coffee",
    category: "food",
    amountCents: 350,
    currency: "USD",
  });
});

test("applies category aliases", () => {
  assert.equal(parseRow("2026-03-01,Milk,Groceries,2.00", 2).category, "food");
});

test("rejects a short row with its line number", () => {
  assert.throws(() => parseRow("2026-03-01,Coffee,food", 7), /line 7/);
});

test("skips the header and blank lines", () => {
  const rows = parseFile("date,description,category,amount\n\n2026-03-01,Coffee,food,3.50\n");
  assert.equal(rows.length, 1);
});

test("reads a currency code from the fifth column, upper-cased", () => {
  assert.equal(parseRow("2026-03-01,Coffee,food,3.50,eur", 2).currency, "EUR");
});

test("defaults to USD when the currency column is missing", () => {
  assert.equal(parseRow("2026-03-01,Coffee,food,3.50", 2).currency, "USD");
});

test("rejects an invalid currency code with its line number", () => {
  assert.throws(() => parseRow("2026-03-01,Coffee,food,3.50,EURO", 9), /line 9/);
});
````

### test/totals.test.ts

````ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { sumByCategory } from "../src/totals.ts";

test("sums by category, sorted by name", () => {
  const e = (category: string, amountCents: number) => ({ date: "d", description: "x", category, amountCents });
  assert.deepEqual(sumByCategory([e("travel", 100), e("food", 50), e("food", 25)]), [
    { category: "food", totalCents: 75 },
    { category: "travel", totalCents: 100 },
  ]);
});
````

## Terminal

```text
$ git log --oneline
490ac43 011 step 4: parser tests for the currency column
c5eaec3 011 steps 1-3: parse the currency column
5ee826a spec 011: multi-currency totals
4910287 tally 0.4.0

$ git status --short
(clean)

$ npm test

> tally@0.4.0 test
> node --test test/*.test.ts

✔ parses a row into integer cents
✔ applies category aliases
✔ rejects a short row with its line number
✔ skips the header and blank lines
✔ reads a currency code from the fifth column, upper-cased
✔ defaults to USD when the currency column is missing
✔ rejects an invalid currency code with its line number
✔ sums by category, sorted by name
ℹ tests 8
ℹ suites 0
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```
