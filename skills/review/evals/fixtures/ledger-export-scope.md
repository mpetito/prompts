# Review request: `ledger export --format csv`

Today is 2026-10-10. Repository `<ledger-cli>` (Go, cobra, shopspring/decimal). Branch
`feature/export-csv`, head `7c41d2e`, base `main` at `e09b3a1`. The branch is pushed; there is no
PR yet.

## Author's description

> Adds `ledger export --format csv` so our clients' accountants can import a period's
> transactions into their bank's reconciliation tool. Columns: Date, Account, Memo, Debit,
> Credit. Tests cover every column.

## Context from the ticket

> Each client's accountant sets up the bank tool's import once, mapping our columns by their
> header names. Twelve clients are waiting for this.

## `REVIEW.md` at the repository root (unchanged by this branch)

```markdown
# Review instructions

Revisited 2026-03-02 at 51c0e7a.

## Expensive to change (blast radius)
- `ledger report --json` output: the finance team's month-end scripts parse it.
- `ledger.toml` keys: every client install has one.

## Risky to get wrong (defect risk)
- `internal/post/`: double-entry posting; every transaction must balance to zero.
- `internal/report/json.go`: the encoder behind `report --json`.

## Always check
- Amounts stay `decimal.Decimal` end to end, never `float64` (from the 2025-11 rounding incident, #212).

## Do not report
- `internal/gen/` (generated); formatting, which `gofmt` in CI enforces.
```

## `git log --oneline -4 main`

```text
e09b3a1 fix(post): reject zero-line transactions (#251)
b77c2d0 feat(report): add --group-by account (#246)
4a1f9e3 refactor: move report encoders from internal/report to internal/render (#240)
91d0c55 chore: bump cobra to v1.9 (#238)
```

## Diff

```diff
--- /dev/null
+++ b/cmd/ledger/export.go
@@ -0,0 +1,33 @@
+package main
+
+import (
+	"fmt"
+	"os"
+
+	"github.com/spf13/cobra"
+	"example.com/ledger/internal/post"
+	"example.com/ledger/internal/render"
+)
+
+var exportFormat, exportFrom, exportTo string
+
+var exportCmd = &cobra.Command{
+	Use:   "export",
+	Short: "Export a period's transactions",
+	RunE: func(cmd *cobra.Command, args []string) error {
+		txs, err := post.Load(exportFrom, exportTo)
+		if err != nil {
+			return err
+		}
+		switch exportFormat {
+		case "csv":
+			return render.WriteCSV(os.Stdout, txs)
+		default:
+			return fmt.Errorf("unknown format %q", exportFormat)
+		}
+	},
+}
+
+func init() {
+	exportCmd.Flags().StringVar(&exportFormat, "format", "csv", "output format")
+	exportCmd.Flags().StringVar(&exportFrom, "from", "", "first day, YYYY-MM-DD")
+	exportCmd.Flags().StringVar(&exportTo, "to", "", "last day, YYYY-MM-DD")
+	rootCmd.AddCommand(exportCmd)
+}
--- /dev/null
+++ b/internal/render/csv.go
@@ -0,0 +1,40 @@
+package render
+
+import (
+	"encoding/csv"
+	"io"
+	"strconv"
+
+	"github.com/shopspring/decimal"
+	"example.com/ledger/internal/post"
+)
+
+var csvHeader = []string{"Date", "Account", "Memo", "Debit", "Credit"}
+
+// WriteCSV writes one row per transaction line.
+func WriteCSV(w io.Writer, txs []post.Transaction) error {
+	cw := csv.NewWriter(w)
+	if err := cw.Write(csvHeader); err != nil {
+		return err
+	}
+	for _, tx := range txs {
+		for _, l := range tx.Lines {
+			debit, credit := "", ""
+			if l.Amount.IsPositive() {
+				debit = money(l.Amount)
+			} else {
+				credit = money(l.Amount.Neg())
+			}
+			row := []string{tx.Date.Format("2006-01-02"), l.Account, tx.Memo, debit, credit}
+			if err := cw.Write(row); err != nil {
+				return err
+			}
+		}
+	}
+	cw.Flush()
+	return cw.Error()
+}
+
+func money(d decimal.Decimal) string {
+	return strconv.FormatFloat(d.InexactFloat64(), 'f', 2, 64)
+}
--- /dev/null
+++ b/internal/render/csv_test.go
@@ -0,0 +1,24 @@
+package render
+
+import (
+	"bytes"
+	"testing"
+
+	"github.com/shopspring/decimal"
+	"example.com/ledger/internal/post"
+)
+
+func TestWriteCSV(t *testing.T) {
+	tx := post.Transaction{Date: day(2026, 9, 30), Memo: "Rent", Lines: []post.Line{
+		{Account: "Expenses:Rent", Amount: decimal.RequireFromString("1250.00")},
+		{Account: "Assets:Bank", Amount: decimal.RequireFromString("-1250.00")},
+	}}
+	var b bytes.Buffer
+	if err := WriteCSV(&b, []post.Transaction{tx}); err != nil {
+		t.Fatal(err)
+	}
+	want := "Date,Account,Memo,Debit,Credit\n2026-09-30,Expenses:Rent,Rent,1250.00,\n2026-09-30,Assets:Bank,Rent,,1250.00\n"
+	if b.String() != want {
+		t.Fatalf("got %q", b.String())
+	}
+}
```

## Validation output the author attached

```text
$ go test ./...
ok  	example.com/ledger/cmd/ledger	0.019s
ok  	example.com/ledger/internal/post	0.031s
ok  	example.com/ledger/internal/render	0.011s
```
