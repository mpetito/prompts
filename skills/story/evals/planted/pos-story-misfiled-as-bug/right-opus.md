Type: User Story

## Title

Export the Shipments grid to CSV

## Area Path

Fieldbook\Fieldbook Web

## Iteration Path

Fieldbook\Sprint 14

## Story Points

8

## Parent

The open Feature that covers the Shipments grid. The input file names no Feature, so check the board for one before filing, and link this story to it as a child.

## Description

As a shipping coordinator, I want to export the Shipments grid to a CSV file using my current filters and sort order so that I can do the weekly carrier reconciliation without copying rows by hand, one page at a time.

#### Additional Context

The operations lead for the warehouse team asked for this. Every Friday the shipping coordinators copy the Shipments grid into a spreadsheet for the carrier reconciliation, one page at a time. It takes them about two hours each week. The grid has no export control anywhere. Selecting all and copying only copies the visible page of 50 rows. The product owner wants this to land in the current sprint (Sprint 14, ends 2026-10-21).

The requester asked for this as a bug. It is filed as a User Story because export has never existed, so no existing behaviour is broken.

Agreed in refinement on 2026-10-06:

- The export uses the grid's current filters (date range, carrier, status) and its current sort order.
- Format: CSV, UTF-8, with a header row. Excel opens it without trouble. No .xlsx for now.
- Columns: the visible grid columns, in their current order.
- Largest realistic export: one quarter of shipments for one warehouse, about 40,000 rows.
- Hard cap: 50,000 rows. Above that the export is blocked and the user sees "Too many rows to export. Narrow your filters to 50,000 rows or fewer."
- Target: a 40,000-row export finishes downloading in under 10 seconds on the office network.
- File name: `shipments-YYYY-MM-DD.csv`, using the date of the export.
- Only users with the Shipments.Read permission see the button. This is the same rule that controls access to the grid.
- Dates are in ISO 8601. Currency amounts have no symbol and two decimals.
- If the export fails on the server, the user sees "Export failed. Try again or contact support." and no partial file is downloaded.

Source: the work item request "getting data out of the Shipments grid" (the input file has no ticket link).

#### Out of Scope

- Scheduled or emailed exports
- .xlsx output
- Exports from any grid other than Shipments

#### Technical Notes

- Backend: an endpoint that streams the CSV from the existing grid query through the ShipmentQuery service. It takes the grid's filters, sort order and visible columns. No schema changes.
- Count the rows before streaming starts. Reject anything over 50,000 rows with the cap message so no file is started.
- Authorize the endpoint with Shipments.Read, the same check the grid uses.
- Frontend: one button in the grid toolbar, using the toolbar button style Design has already approved, plus a toast for the cap and failure messages.
- Make sure a failure partway through the stream cannot leave a partial file. For example, buffer the file or check the response before saving the blob.
- Write UTF-8 so non-ASCII text survives. Check whether Excel needs a BOM to detect UTF-8.
- QA needs seeded test data with more than 50,000 rows to test the cap, and about 40,000 rows to test the timing.
- Estimate: the dev lead's gut feel was 6 points, "maybe 7 with the row-cap handling". 7 rounds to 8 on the Fibonacci scale, and the seeded large-data testing supports the higher value.

#### Dependencies

None blocking. It reuses the existing ShipmentQuery service and the approved grid-toolbar button style.

## Acceptance Criteria

### 1. Access

- [ ] A user with the Shipments.Read permission sees an Export button on the Shipments grid toolbar.
- [ ] A user without the Shipments.Read permission does not see the Export button.

### 2. What the file contains

- [ ] Clicking Export downloads a file named `shipments-YYYY-MM-DD.csv`, where the date is the day of the export (for example, `shipments-2026-10-16.csv`).
- [ ] The file contains every shipment that matches the grid's current date range, carrier and status filters, across all pages, not just the 50 rows on screen.
- [ ] Rows in the file are in the same order as the grid's current sort.
- [ ] The first row of the file is a header row with the visible grid columns, in the order they currently appear in the grid. Columns hidden in the grid are not in the file.
- [ ] Dates in the file are in ISO 8601 format (for example, `2026-10-16`).
- [ ] Currency amounts have no currency symbol and exactly two decimals (for example, `1234.50`).
- [ ] The file opens in Excel with names that contain accented or non-English characters displayed correctly.

### 3. Size limit and speed

- [ ] An export of 40,000 rows finishes downloading in under 10 seconds on the office network.
- [ ] An export of exactly 50,000 rows downloads.
- [ ] When the filters match more than 50,000 rows, no file downloads and the user sees "Too many rows to export. Narrow your filters to 50,000 rows or fewer."

### 4. Failure

- [ ] When the export fails on the server, the user sees "Export failed. Try again or contact support." and no file, not even a partial one, is downloaded.

---

A few notes on how I drafted this:

- **User Story, not Bug.** The grid has never had an export, so nothing existing is broken. It's new capability, and the description explains this to the requester.
- **One item.** The request asks for one thing the client can accept on its own, so I didn't split it. I left the backend and the button together on purpose; splitting by technical layer would give two items that can't ship alone.
- **8 points.** The dev lead said 6 or 7 points. 7 rounds to 8 on the Fibonacci scale.
- **Vague wording turned into checks.** "Fast", "intuitive" and "handle errors gracefully" became the specific limits and messages agreed in refinement.
- **Placement needs confirming.** The input file gives no area path or parent Feature. I guessed `Fieldbook\Fieldbook Web` as the team's area path; check both against similar stories on the board before creating the item.