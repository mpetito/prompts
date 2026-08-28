# Manifest Reference

Both editors take a JSON array of operations. Every operation should carry an `id` (label
used in reports and logs) and a `note` (the rationale — it flows into the CSV change log
and the merged Markdown log, so a reviewer can see *why* each tracked change was made).

## Invoke-DocxEdits.ps1 — text edits within a paragraph

```json
[
  {
    "id": "xref-13.4",
    "find": "cost scoring under §13.4",
    "replace": "cost scoring under the Sealed Cost/Fee Proposal",
    "scope": "unique",
    "matchCase": true,
    "note": "Descriptive reference replaces stale numeric one"
  }
]
```

| Field | Meaning |
| --- | --- |
| `find` | Literal text to locate. Must sit within a single paragraph. |
| `replace` | Replacement text. `""` deletes. No paragraph breaks — split multi-paragraph changes into ops. |
| `scope` | `unique` (default — refuse if more than one match), `first`, or `all` |
| `matchCase` | Default `true`. Set `false` for case-insensitive. |

Statuses: **OK / NOT FOUND / AMBIGUOUS / SKIPPED / PARTIAL** — nothing changes silently.
`AMBIGUOUS` is the default outcome for a phrase appearing more than once; lengthen `find`
or set `scope` deliberately.

Replacement is *narrowed*: the shared prefix and suffix of `find`/`replace` are trimmed so
only genuinely changed characters are rewritten, preserving formatting on the untouched
flanks. Before writing, the target range's actual text is compared to the expectation; a
mismatch (usually a field code in the paragraph) is reported as SKIPPED, never guessed at.

## Invoke-DocxOps.ps1 — structural operations

Also supports `replace` (same fields as above), so a mixed batch can go through this
script alone. Operations address paragraphs by `anchor` — a text fragment that must match
exactly one paragraph — or by `anchorIndex` when a paragraph has no unique text (verify
the index with `Get-DocxOutline.ps1` against the same file immediately before using it,
and order such ops bottom-up).

| op | Fields | Effect |
| --- | --- | --- |
| `replace` | `find`, `replace` [, `scope`] | Text rewrite inside one paragraph |
| `restyle` | `anchor`, `style` | Change a paragraph's style |
| `deleteParas` | `anchor` [, `through`] [, `count`] [, `maxParas`] | Delete from anchor through a second anchor (inclusive), or `count` paragraphs |
| `deleteTable` | `anchor` | Delete the table containing the anchor text |
| `insertAfter` | `anchor`, `blocks[]` | Insert paragraphs after the anchor paragraph |
| `insertBefore` | `anchor`, `blocks[]` | Insert paragraphs before the anchor paragraph |
| `insertTable` | `anchor`, `rows[][]` [, `style`] | Insert a table after the anchor paragraph |

A block is `{ "text": "...", "style": "Body Text" }` (optionally `"noList": true` to
strip inherited list numbering). **Style names must already exist in the document** — the
script validates every style up front and refuses unknown ones, so run `Get-DocxOutline`
first to see what the document actually uses.

### Safety guards built into deleteParas

- The live text of the first and last paragraph of the computed range is re-checked to
  contain the anchor/through strings; a mismatch refuses the delete.
- A range spanning more than `maxParas` paragraphs (default 60) refuses; raise it
  explicitly when a big delete is intended.

### Example structural batch

```json
[
  {
    "id": "S1-delete-old-section",
    "op": "deleteParas",
    "anchor": "4. Legacy Disqualification Criteria",
    "through": "shall be rejected without scoring",
    "note": "Construct removed per review direction; capabilities re-homed as scored criteria"
  },
  {
    "id": "S2-new-intro",
    "op": "insertAfter",
    "anchor": "Selection Process and Criteria",
    "blocks": [
      { "text": "Evaluation Categories and Weights", "style": "Heading 2" },
      { "text": "Proposals are scored on a 100-point scale...", "style": "Body Text" }
    ],
    "note": "Replaces the deleted construct with the scoring model"
  },
  {
    "id": "S3-weights-table",
    "op": "insertTable",
    "anchor": "Evaluation Categories and Weights",
    "rows": [
      ["Category", "Weight", "What is evaluated"],
      ["Solution Fit", "35", "..."],
      ["Total", "100", ""]
    ],
    "note": "Inserted last — nothing can anchor inside a table about to be created"
  }
]
```

## Batching and chaining

Author one manifest per theme (structure, references, new content, …). Chain them:

```powershell
.\scripts\Invoke-DocxOps.ps1 '.\doc.docx'      .\edits\01-structure.json -OutFile .\work\rev1.docx -Author 'YourOrg' -ChangeLog .\work\log-01.csv
.\scripts\Invoke-DocxOps.ps1 .\work\rev1.docx  .\edits\02-references.json -OutFile .\work\rev2.docx -Author 'YourOrg' -ChangeLog .\work\log-02.csv
.\scripts\Update-DocxFields.ps1 .\work\rev2.docx
.\scripts\Merge-ChangeLogs.ps1 .\work\log-0*.csv -OutFile .\work\change-log.md
```

Revisions accumulate across the chain; the final file carries every tracked change from
every batch, and the merged log is the single rationale document to deliver alongside it.

## Change log CSV columns

`Invoke-DocxOps.ps1 -ChangeLog` writes: `Id, Op, Status, Page, Detail, Note`. Rows for
work done outside the manifests (e.g., a scripted paste) can be appended by hand with the
same columns so `Merge-ChangeLogs.ps1` tells the whole story.
