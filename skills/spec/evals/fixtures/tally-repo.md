# Repository snapshot: tally

A snapshot of a git repository: the path and full contents of every file, as of its only commit (`tally 0.4.0`). The working tree is clean.

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
}

export function parseRow(line: string, lineNo: number): Expense {
  const cols = line.split(",").map((c) => c.trim());
  if (cols.length < 4) {
    throw new Error(`line ${lineNo}: expected 4 columns, got ${cols.length}`);
  }
  const [date, description, category, amount] = cols;
  return {
    date,
    description,
    category: resolveCategory(category),
    amountCents: toCents(amount, lineNo),
  };
}

function toCents(raw: string, lineNo: number): number {
  const value = Number(raw);
  if (!Number.isFinite(value)) {
    throw new Error(`line ${lineNo}: bad amount "${raw}"`);
  }
  return Math.round(value * 100);
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
