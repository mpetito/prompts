# Branch context: users/dev/csv-import-refresh

Base: main. Spec: specs/041-csv-import-refresh/spec.md ("Nightly CSV refresh of product values").

## git log main..HEAD --oneline

9c1d7f0 docs(ops): describe the nightly refresh and its failure modes
2ab44e1 test(import): cover bad rows, empty folder and bulk replace
7e30b92 feat(import): schedule RefreshValues nightly via Hangfire
c4f1a08 feat(import): bulk-replace Values table from combined CSV files
15d9e6b feat(import): add CsvDataset reader with per-row validation
a0b3c77 refactor(domain): extract ValueRow record from Product
e8f2d10 chore(deps): add CsvHelper 33.0.1

## git diff main...HEAD --stat

 Directory.Packages.props                                  |   1 +
 docs/ops/nightly-refresh.md                               |  48 ++++++
 libs/domain/Products/Product.cs                           |  22 +--
 libs/domain/Products/ValueRow.cs                          |  18 +++
 libs/import/CsvDataset.cs                                 | 121 +++++++++++++
 libs/import/ICsvDataset.cs                                |   9 +
 libs/import/RefreshValues.cs                              | 143 ++++++++++++++++
 libs/import/ValuesBulkWriter.cs                           |  77 +++++++++
 apps/api/Jobs/NightlyRefreshJob.cs                        |  31 ++++
 apps/api/Program.cs                                       |   6 +
 apps/api/appsettings.json                                 |   4 +
 tests/import.tests/CsvDatasetTests.cs                     |  88 ++++++++++
 tests/import.tests/RefreshValuesTests.cs                  | 134 ++++++++++++++
 tests/domain.tests/ValueRowTests.cs                       |  26 +++
 14 files changed, 712 insertions(+), 16 deletions(-)

## Key diff excerpts

CsvDataset.cs reads every column as text, so a malformed cell rejects only its own
row and the rest of the file still loads. Rejected rows are counted and logged.

RefreshValues.cs combines every .csv file in the inbound folder sorted by path.
When there are no files or no valid rows it leaves the Values table untouched;
otherwise it replaces the table in a single bulk import inside one transaction.

NightlyRefreshJob.cs registers the refresh with Hangfire at 02:00 server time.
Program.cs binds the `Import:InboundFolder` setting and registers the job.

Product.cs no longer carries value columns; they moved to ValueRow. DocumentBuilder
is unchanged and still reads values through the Product navigation.

Not in the spec: the ops runbook in docs/ops/nightly-refresh.md was added because
the on-call rotation asked for it.

## Validation run on the branch

$ dotnet test libs/import.tests
Passed!  - Failed:     0, Passed:    31, Skipped:     0, Total:    31, Duration: 2.9 s

$ dotnet test libs/domain.tests
Passed!  - Failed:     0, Passed:   296, Skipped:     0, Total:   296, Duration: 4.1 s

$ dotnet build -warnaserror
Build succeeded. 0 Warning(s) 0 Error(s)

Not run: the job has not been executed against the real inbound folder, and
nothing has been deployed. After merge an operator must set Import:InboundFolder
on staging and trigger the job once from the Hangfire dashboard.
