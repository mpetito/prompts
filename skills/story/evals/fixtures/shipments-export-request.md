# Work item request: getting data out of the Shipments grid

Project: Fieldbook (internal logistics portal). Team: Fieldbook Web.
Current sprint: Fieldbook\Sprint 14 (ends 2026-10-21). Next sprint: Fieldbook\Sprint 15.
The product owner has asked for this to land in the current sprint.

## Message from the requester (operations lead, warehouse team)

> Hi team, please log this as a BUG so it gets picked up this sprint. It has
> been bugging us for months.
> The Shipments grid has no way to get the data out. Every Friday my shipping
> coordinators copy rows page by page into a spreadsheet for the carrier
> reconciliation, and it takes them about two hours each week.
> We need an export button. It should be fast and intuitive and handle errors
> gracefully. Ideally it just works with whatever filters they have set.

## Current behaviour

There is no export control anywhere on the Shipments grid. Selecting all and
copying only copies the visible page (50 rows).

## Notes from refinement (2026-10-06)

- The export respects the current grid filters (date range, carrier, status)
  and the current sort order.
- Format: CSV, UTF-8 with a header row. Excel opens it fine; no .xlsx for now.
- Columns: the visible grid columns, in their current order.
- Largest realistic export: one quarter of shipments for one warehouse,
  about 40,000 rows.
- Hard cap agreed: 50,000 rows. Above that the export is blocked and the user
  sees "Too many rows to export. Narrow your filters to 50,000 rows or fewer."
- Target: a 40,000-row export finishes downloading in under 10 seconds on the
  office network.
- File name pattern: shipments-YYYY-MM-DD.csv (the date of the export).
- Only users with the Shipments.Read permission see the button (same rule as
  the grid itself).
- Dates are written in ISO 8601; currency amounts without symbols, two decimals.
- If the export request fails on the server, the user sees "Export failed.
  Try again or contact support." and no partial file is downloaded.
- Out of scope: scheduled or emailed exports, .xlsx output, exporting any
  other grid.

## Estimate notes

- Dev lead: "Backend endpoint streams CSV from the existing grid query, the
  frontend is one button plus a toast. Gut feel is 6 points, maybe 7 with the
  row-cap handling."
- QA: needs seeded test data with more than 50,000 rows to check the cap.

## Dependencies

- Reuses the existing ShipmentQuery service; no schema changes.
- Design has a button style already approved for grid toolbars.
