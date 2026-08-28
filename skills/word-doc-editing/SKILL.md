---
name: word-doc-editing
description: |
  Review and revise Microsoft Word (.docx) documents by driving Word itself through COM
  automation — genuine tracked changes, formatting preserved by construction, every edit
  verified and logged. Use when editing or restructuring a .docx, when applying reviewable
  tracked changes to a Word document, when auditing a document for stale terms or
  cross-references, when accepting/rejecting revisions or refreshing TOC fields, or when
  exporting a .docx to PDF. Requires Windows with Microsoft Word installed.
---

# Word Document Editing (COM Automation)

Scripts and procedure for editing `.docx` files by driving **Microsoft Word itself** through
COM from PowerShell 7. Word does the writing, so formatting fidelity is guaranteed by
construction, and tracked changes are genuine Word revisions the recipient can
Accept/Reject normally. Never hand-edit the OOXML for content changes — raw XML surgery
breaks run formatting, numbering, and revision integrity in ways that are invisible until
someone opens the file.

## When to Use

- Editing, restructuring, or annotating a `.docx` where formatting must be preserved
- Producing a reviewable deliverable: every change tracked, with a rationale log
- Auditing a document: outline/numbering, stale terms, cross-references, revisions
- Post-processing: accept/reject revisions, refresh TOC/fields, export PDF

## Prerequisites

- Windows with Microsoft Word installed (any recent desktop version)
- PowerShell 7 (`pwsh`)
- Scripts live in [`scripts/`](scripts/) beside this file; they share
  [`scripts/WordCom.psm1`](scripts/WordCom.psm1) and can be copied anywhere as a set

## The Toolkit

| Script | Purpose |
| --- | --- |
| `WordCom.psm1` | Shared plumbing — invisible Word app lifecycle, safe open, working copies, orphan cleanup |
| `Get-DocxOutline.ps1` | Every paragraph with its **Word-rendered** list number, style, page, table membership, and text |
| `Find-DocxTerms.ps1` | Search for a checklist of terms; every hit with page and context. `-Terms` takes an array or a file |
| `Invoke-DocxEdits.ps1` | Text edits within paragraphs from a JSON manifest, tracked, with narrowed replacement |
| `Invoke-DocxOps.ps1` | Structural editor — delete paragraphs/tables, insert styled paragraphs/tables, restyle; also does `replace`, so a mixed batch can go through it alone |
| `Get-DocxRevisions.ps1` | List tracked changes — the receipt for an editing pass |
| `New-DocxAccepted.ps1` | Copy with all revisions accepted (or `-Reject`ed), for verifying the *final* text |
| `Update-DocxFields.ps1` | Refresh TOC / PAGEREF / REF fields with tracking temporarily off; reports page count |
| `Export-DocxPdf.ps1` | Render to PDF, with (`-ShowMarkup`) or without visible markup |
| `Merge-ChangeLogs.ps1` | Merge per-batch CSV logs into one Markdown change log with rationale |

Both editors take JSON manifests where every operation carries an `id` and a `note`
(rationale) that flow into the change log. Full manifest schemas and operation reference:
[`references/manifests.md`](references/manifests.md).

## Procedure

1. **Survey the document first.** Get the ground truth — real rendered section numbers,
   styles, what is inside tables:

   ```powershell
   .\scripts\Get-DocxOutline.ps1 '.\doc.docx' -HeadingsOnly -Format Table
   ```

2. **Find what needs to change.** Build the target list before editing:

   ```powershell
   .\scripts\Find-DocxTerms.ps1 '.\doc.docx' -Terms 'stale term','§14' -HitsOnly | Format-Table -AutoSize
   ```

3. **Author a JSON manifest** (see [`references/manifests.md`](references/manifests.md)).
   Split large revisions into small batches by theme; every op gets a `note` saying why.
   Order ops by the three ordering rules below.

4. **Dry-run, then apply.** Never skip the dry run — it surfaces NOT FOUND and AMBIGUOUS
   before anything changes:

   ```powershell
   .\scripts\Invoke-DocxOps.ps1 '.\doc.docx' .\edits\01-batch.json -WhatIf | Format-Table Id,Status,Detail -AutoSize -Wrap
   .\scripts\Invoke-DocxOps.ps1 '.\doc.docx' .\edits\01-batch.json -OutFile .\work\rev1.docx -Author 'YourOrg' -ChangeLog .\work\log-01.csv
   ```

   The source is never modified; both editors always write to a copy. Chain batches
   (`rev1 → rev2 → …`) — revisions accumulate so the final file carries every tracked
   change. Every op reports **OK / NOT FOUND / AMBIGUOUS / SKIPPED / PARTIAL**; treat
   anything but OK as a stop-and-look.

5. **Refresh fields and check the page budget:**

   ```powershell
   .\scripts\Update-DocxFields.ps1 '.\work\rev1.docx'
   ```

6. **Review what changed:**

   ```powershell
   .\scripts\Get-DocxRevisions.ps1 '.\work\rev1.docx' | Format-Table -AutoSize
   .\scripts\Export-DocxPdf.ps1 '.\work\rev1.docx' -ShowMarkup -OutFile .\work\review.pdf
   ```

7. **Verify against the FINAL text, not the marked-up text.** While revisions are
   tracked, deleted text is still physically present — a term search keeps finding
   deleted text long after it is struck through:

   ```powershell
   $final = .\scripts\New-DocxAccepted.ps1 '.\work\rev1.docx'
   .\scripts\Find-DocxTerms.ps1 $final.Output -Terms 'stale term','§14' -HitsOnly
   ```

   For high-stakes deliverables, also verify at the XML level: unzip
   `word/document.xml` from the accepted copy and scan its `<w:t>` text independently —
   the accepted copy is the ground truth for what the recipient will read.

8. **Merge the logs** when delivering one document assembled from several batches:

   ```powershell
   .\scripts\Merge-ChangeLogs.ps1 .\work\log-0*.csv -OutFile .\work\change-log.md
   ```

## Ordering Rules (violations cause silent damage)

1. **Delete before you insert.** If a batch removes an old block and adds a new one in
   the same region, put the deletion first, or the delete range and the fresh paragraphs
   can overlap and content you just wrote disappears.
2. **Insert tables last.** No operation can anchor inside a table cell it is about to
   create, and `InsertParagraphAfter` fails on a row end. Add prose first, then the table.
3. **When anchoring by index, work bottom-up.** Indices shift on every insert; ordering
   `anchorIndex` ops from the end of the document backwards keeps the rest valid.

## Word COM Traps

These cost real debugging time; the scripts already defend against them, but any ad-hoc
COM you write must too. Full explanations: [`references/word-com-traps.md`](references/word-com-traps.md).

| Trap | Consequence | Defense |
| --- | --- | --- |
| `Find.Execute` mis-scopes ranges starting inside a table cell | Hits *before* the range start → infinite loop / hang | Index paragraphs once; search text with .NET `IndexOf`; edit each paragraph's own Range |
| `Paragraph.Range` includes the trailing ¶ | Assigning `.Text` merges the paragraph into the next; chained inserts silently swallow each other | Write to `Range(Start, End-1)` |
| Word refuses to delete a cell's final ¶ ("Cannot edit Range.") | Deletions ending at a cell boundary fail | Shrink the range by one character; leave the mark |
| Cross-document paste carries the source's **section break** | Target's page size/orientation/margins silently replaced; whole document reflows | After any paste, diff `sectPr` count and geometry; give pasted content its own section deliberately |
| Tracked text search sees deleted text; anchors can match struck-through content | Ops land on the wrong paragraph | Verify against the accepted copy; prefer full unique anchor strings |
| Relative output paths resolve against the **process** CWD, not `Set-Location` | "Directory name isn't valid" from `ExportAsFixedFormat` | Pass absolute paths, or resolve against `(Get-Location)` first |
| Highlight changes under tracking are property revisions that apply only on acceptance | "Clear highlight" appears to no-op | Clear highlights in a separate pass *after* acceptance |
| Modal dialogs block COM entirely | Script hangs until timeout | `DisplayAlerts=0`, `AutomationSecurity=3` (WordCom.psm1 does this); never trigger UI |

## Working Style That Holds Up

- **Batch + manifest + log, not ad-hoc edits.** The manifest is reviewable before it
  runs, the CSV log is the receipt after, and `-WhatIf` is free.
- **Replacement text inherits the formatting of what it replaces** (including reviewer
  highlighting). Narrowed replacement — trimming the shared prefix/suffix so only changed
  characters are rewritten — keeps formatting intact on the flanks.
- **Verify structurally after big passes:** compare paragraph/table/field counts and
  bold/italic character coverage before vs after; unexplained drops mean content loss.
- **Refresh the TOC once more after the recipient accepts** — page numbers reflect
  marked-up pagination until then.

## Common Issues

| Problem | Fix |
| --- | --- |
| Script hangs, file stays locked | `Import-Module .\scripts\WordCom.psm1 -Force; Stop-OrphanWord` (only kills windowless instances) |
| `AMBIGUOUS` result | Lengthen the `find`/`anchor` string, or set `scope` deliberately |
| `NOT FOUND` for text you can see | The text spans paragraphs or contains a field result; target within a single paragraph, or check for fields |
| "range check failed … paragraph likely contains a field" | Paragraph text offsets diverge from Range offsets when fields are present; edit around the field |
| Accepted page count differs wildly after a paste | You imported a section break — check `sectPr` geometry (see traps) |
| Word dialog appeared, everything frozen | Kill the orphan, re-run; find and remove whatever triggered UI |
