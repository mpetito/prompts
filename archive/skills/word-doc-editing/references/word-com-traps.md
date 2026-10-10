# Word COM Traps — Full Explanations

Every one of these was hit in production and cost real debugging time. The scripts in
`../scripts/` defend against them; ad-hoc COM code must defend against them too.

## 1. `Find.Execute` mis-scopes ranges that start inside a table cell

Word's `Find.Execute` on a `Range` beginning inside a table cell will happily return a
hit that starts *before* the range start. The classic "find, advance range start, repeat"
loop therefore never terminates — observed as `range[35269,51590] -> hit at [35264,35269]`
repeating forever. Form-style documents are often one large table, so nearly every target
sits inside a cell.

**Defense:** never loop `Find.Execute`. Index `$doc.Paragraphs` once (text + Range), find
matches with exact .NET `String.IndexOf`, and edit each paragraph's own Range. Side
benefit: exact match counts instead of approximations.

## 2. `Paragraph.Range` includes the trailing paragraph mark

The obvious `$para.Range.Text = 'new text'` deletes the paragraph mark and merges the
paragraph into the one after it. Chain several insert-then-fill operations and each block
silently swallows the next — content appears to insert OK but is missing from the saved
file, with tell-tale merged text like `"Heading TitleFirst body sentence"`.

**Defense:**

```powershell
$r = $Paragraph.Range
$Document.Range($r.Start, [Math]::Max($r.Start, $r.End - 1)).Text = $Text
```

## 3. Word refuses to delete a table cell's final paragraph mark

Deleting a range that ends at a cell boundary throws **"Cannot edit Range."** — every
cell must keep its final ¶. Deletions of blocks that end at a cell edge hit this
routinely.

**Defense:** detect (`$rng.Cells` end position vs range end), shrink the range by one
character, and report that an empty paragraph was left behind.

## 4. Cross-document paste carries the source's section break

Copying a range that includes a `sectPr` (section properties) — common when the copied
content is or abuts its own section, e.g. a landscape appendix — pastes that section
break into the target. The result: the target document's page size, orientation, and
margins are silently replaced for everything *before* the pasted break. Observed as a
24-page A4 portrait body reflowing to 34 landscape-Letter pages after appending an
appendix, with zero content changes.

**Defense:** after any cross-document paste, compare section count and geometry:

```powershell
# quick check from the OOXML (no Word needed)
# unzip word/document.xml and inspect <w:sectPr> / <w:pgSz> elements
```

If the pasted content needs different geometry (e.g., landscape tables), give it its own
section deliberately: delete the imported stray `sectPr` paragraph, insert a next-page
section break (`Range.InsertBreak(2)`) at the content's first paragraph, then set that
section's `PageSetup` (orientation, `PageWidth`/`PageHeight` in points, margins). Note
**Word does not track page-setup changes** — record them in the change log by hand.

Related: `Range.Copy()` + `Range.PasteAndFormat(16)` (wdFormatOriginalFormatting)
preserves visual formatting; styles that do not exist in the target map to Normal with
direct formatting and outline levels intact. A paste into a tracked document records as
one contiguous insertion — good for reviewability.

## 5. Tracked deletions are still searchable text

While revisions are tracked, deleted text remains physically in the document. Two
consequences:

- A term search on the tracked file keeps "finding" text that is already struck through.
  **Verify against a copy with revisions accepted** (`New-DocxAccepted.ps1`).
- Anchor matching can land on a struck-through paragraph. When several paragraphs start
  with the same words (e.g., a live heading and a deleted table cell), the first match in
  document order wins — and that may be the deleted one. Prefer long, full-sentence
  anchors, and remember a pasted block's first paragraph may begin with an invisible
  page-break character (`Chr(12)`), which defeats `StartsWith` matching.

## 6. Relative paths resolve against the process CWD

`[IO.Path]::GetFullPath()` and Word's own file APIs resolve relative paths against the
**process** working directory, which `Set-Location` does not move. Symptom: a script that
worked all session suddenly throws **"The directory name isn't valid."** from
`ExportAsFixedFormat`.

**Defense:** root relative paths against `(Get-Location).ProviderPath` before handing
them to .NET or COM, or always pass absolute paths.

## 7. Highlight (and other property) changes under tracking

With revision tracking on, Word records a highlight change as a property revision that
does not take visible effect until acceptance — so "clear the highlighting" appears to
no-op. Clearing highlights is a deliberate final pass to run *after* revisions are
accepted. Corollary: replacement text inherits the formatting of the text it replaces, so
edits inside reviewer-highlighted passages come out highlighted — usually desirable
during review.

## 8. Dialogs, orphans, and hygiene

- A modal dialog blocks COM entirely; the script hangs until timeout. `WordCom.psm1` sets
  `DisplayAlerts = 0` and `AutomationSecurity = 3` (macros force-disabled) at startup.
  Never call anything that can raise UI.
- A failed run leaves an orphaned `WINWORD.exe` holding file locks. `Stop-OrphanWord`
  kills only instances with no visible window, so a document the user has open by hand is
  safe. Always `Remove-WordApp` in a `finally` block.
- `$host` is a reserved PowerShell automatic variable — never use it as a loop variable
  in scripts that drive COM (or anywhere).

## 9. Structural verification catches what reports miss

After a large pass, compare before/after: paragraph count, table count, field count,
bookmark count, and bold/italic **character coverage**. An unexplained drop in italic
coverage once exposed a materially important sentence that lived only inside a deleted
table row — the op reports were all OK. Cheap to run, catches content loss nothing else
reports.
