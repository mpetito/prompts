Type: User Story

## Title
Export the filtered Shipments grid to CSV

## Area Path
Fieldbook (Team: Fieldbook Web)

## Iteration Path
Fieldbook\Sprint 14

## Description
**As a** shipping coordinator on the warehouse team,
**I want** to export the Shipments grid, with my current filters and sort order, to a CSV file,
**so that** I can do the weekly carrier reconciliation without copying rows by hand one page at a time.

**Current behaviour:** The Shipments grid has no export control. "Select all" and copy only copies the visible page of 50 rows. Every Friday, coordinators copy rows page by page into a spreadsheet, which takes about two hours each week.

**Scope:**
- Add an Export button to the Shipments grid toolbar, using the toolbar button style Design has already approved.
- Add a backend endpoint that streams CSV from the existing ShipmentQuery service, using the grid's current filters and sort order.
- Enforce a 50,000-row cap.
- Show error messages in a toast.

**Out of scope:** scheduled or emailed exports, .xlsx output, and exports from any other grid.

**Note on work item type:** The requester asked for this to be logged as a Bug. It is logged as a User Story because the export never existed. Nothing that used to work is broken, so this is new functionality. The product owner's request to land it in the current sprint is reflected in the Iteration Path.

## Acceptance Criteria
1. **Visibility:** Users with the Shipments.Read permission see an Export button on the Shipments grid toolbar. Users without that permission do not see it (the same rule as the grid itself).
2. **Filters and sort:** The file contains exactly the rows that match the current date range, carrier and status filters, across all pages, not just the visible page. Rows are in the grid's current sort order.
3. **Columns:** The file contains the visible grid columns, in their current order.
4. **Format:** The file is CSV, UTF-8, with a header row, and opens correctly in Excel.
5. **Values:** Dates are in ISO 8601. Currency amounts have no currency symbol and exactly two decimal places.
6. **File name:** The file is named `shipments-YYYY-MM-DD.csv`, using the date of the export.
7. **Performance:** A 40,000-row export finishes downloading in under 10 seconds on the office network.
8. **Row cap:** If the filtered result has more than 50,000 rows, no file is produced and the user sees: "Too many rows to export. Narrow your filters to 50,000 rows or fewer." An export of exactly 50,000 rows succeeds.
9. **Server failure:** If the export request fails on the server, the user sees "Export failed. Try again or contact support." and no partial file is downloaded.

## Story Points
Not set; confirm in sprint planning. The dev lead's gut feel is 6 points, or 7 with the row-cap handling.

## Priority
2

## Tags
shipments; export; csv

## Dependencies
- Reuses the existing ShipmentQuery service. No schema changes.
- Uses the toolbar button style Design has already approved.

## Test Notes
QA needs seeded test data with more than 50,000 rows to check the cap: a result just over the limit, exactly 50,000 rows, and a result of about 40,000 rows for the performance target.