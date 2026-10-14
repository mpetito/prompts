Type: User Story

## Title
Export filtered Shipments grid to CSV

## Area Path
Fieldbook\Fieldbook Web

## Iteration Path
Fieldbook\Sprint 14

## Story Points
7

## Description
As a shipping coordinator, I want to export the Shipments grid to a CSV file so that I can do the weekly carrier reconciliation without copying rows page by page into a spreadsheet.

Background: The Shipments grid has no export control. Select-all and copy only gets the visible page of 50 rows. Coordinators spend about two hours every Friday copying rows by hand.

Work item type: this was requested as a Bug, but it is new functionality and not a defect, so I've logged it as a User Story. The requester's urgency is reflected in the sprint placement.

Scope:
- Add an Export button to the Shipments grid toolbar, using the already approved toolbar button style.
- Add a backend endpoint that streams CSV from the existing ShipmentQuery service. There are no schema changes.
- Show a toast for the error and blocked cases.

Business rules:
- The export respects the current grid filters (date range, carrier, status) and the current sort order.
- The format is CSV, UTF-8, with a header row. It must open correctly in Excel.
- Columns are the visible grid columns, in their current order.
- Dates are ISO 8601. Currency amounts have no symbol and two decimals.
- The file name is `shipments-YYYY-MM-DD.csv`, using the date of the export.
- Only users with the `Shipments.Read` permission see the button, the same rule as the grid.
- Hard cap of 50,000 rows. Above the cap, the export is blocked.
- If the server request fails, no partial file is downloaded.

Out of scope: scheduled or emailed exports, .xlsx output, and exporting any other grid.

Dependencies and notes:
- Reuses the existing ShipmentQuery service.
- QA needs seeded test data with more than 50,000 rows to verify the cap.
- Sprint 14 ends 2026-10-21, one week from today. The product owner asked for this in the current sprint. The dev lead's estimate is 6 points, or 7 with the row-cap handling. I used 7 because the cap is agreed scope. If it can't be finished and tested by 2026-10-21, move it to Fieldbook\Sprint 15.

## Acceptance Criteria
1. Given a user with `Shipments.Read`, when they open the Shipments grid, then an Export button is visible in the toolbar. Given a user without `Shipments.Read`, the button is not shown.
2. Given filters (date range, carrier, status) and a sort order are applied, when the user clicks Export, then the downloaded CSV contains exactly the rows matching those filters, across all pages, in that sort order.
3. The file is named `shipments-YYYY-MM-DD.csv` with the export date.
4. The file is UTF-8 with a header row. Its columns are the visible grid columns in their current order, and it opens correctly in Excel.
5. Dates in the file are ISO 8601. Currency values have no symbol and two decimals, for example `1234.50`.
6. Given a filtered result of 50,000 rows or fewer, the export succeeds. Given a result of more than 50,000 rows, no file is downloaded and the user sees "Too many rows to export. Narrow your filters to 50,000 rows or fewer."
7. Given a 40,000-row export on the office network, the download finishes in under 10 seconds.
8. Given the server request fails, the user sees "Export failed. Try again or contact support." and no partial file is downloaded.
9. Automated tests cover the permission check, filter and sort fidelity, the cap boundary (50,000 passes, 50,001 is blocked), and the failure path.

## Tags
export; shipments; csv; grid

## Priority
2