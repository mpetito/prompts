Proposed: User Story: CRM - Customer Success reps see a contact's open support cases on the contact page [OPS-5930]
Proposed: User Story: CRM - "Last contacted" date filled in automatically from logged calls and meetings [OPS-5930]
Proposed: User Story: CRM - CS managers export an account's contacts to CSV [OPS-5930]
Proposed: User Story: CRM - Duplicate contacts flagged nightly for a CS manager to merge [OPS-5930]

These calls only read. Item 4936 already covers the inactive-contacts item (wish 2) and is Closed. Item 4730, "Contact management tweaks", is also Closed and may cover part of the list. I need both in full before the split is final:

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{"action": "get", "id": 4936, "project": "Kestrel Ledger", "expand": "All"}
```

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{"action": "get", "id": 4730, "project": "Kestrel Ledger", "expand": "All"}
```

I'm stopping here and won't write anything until Lena confirms the split.

---

**Note to Lena**

Hi Lena, I haven't put anything on the board yet. I'd like your OK on how I've split the wish list first.

**Why not one story:** The list has five things the client can accept separately, and they don't ship together. The duplicate-flagging item can't start until the Integration Hub's nightly sync ships next month. At about 21 points, one story would also be bigger than we can estimate as a single item. If it went in as one story, it would stay open until next month even after the rest is done. For reporting, all the stories would sit under **4458 CRM Spring Change Request**, and each title would carry **[OPS-5930]**. You can then pull them all up together with one query.

**Inactive contacts (wish 2):** This looks like it was already delivered in **4936 "CRM - Inactive contacts drop out of account contact lists [OPS-7214]"**, which is Closed. I'm checking whether that story also kept inactive contacts searchable:
- If it did, I'll link 4936 to OPS-5930 and won't file anything new.
- If it didn't, I'll add a small story just for the search part.

**Where the stories go:**
- **Parent:** 4458 CRM Spring Change Request
- **Area:** `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering`
- **Type:** User Story
- **Iteration:** `Kestrel Ledger\2026-11-30` for the first three
- **Duplicate flagging:** a later sprint. It gets a predecessor link to the Integration Hub nightly-sync work. That's under Feature 4555 unless you can point me to a more specific item.

The open-cases story would also get a "related" link to 4935, the Customer Success contact page layout.

**Points:** These are my split of Sam's estimate, for Sam to confirm. They add up to his 21.

| Story | Points |
|---|---|
| Open support cases | 3 |
| Inactive contacts (only if search is missing) | 2 |
| Last contacted | 5 |
| CSV export | 3 |
| Duplicate flagging | 8 |

**What each story will check:**
- **Open support cases:**
  - Reps see the contact's open cases, newest first.
  - At most 10 are shown.
  - A "View all" link opens the full list.
- **Last contacted:**
  - The date updates when a call or meeting with the contact is logged.
  - The field stays empty if nothing has been logged.
- **CSV export:**
  - Only CS managers see the export button.
  - The file has these columns in this order: name, email, phone, role, last contacted.
- **Duplicate flagging:**
  - Each night, contacts on the same account with the same email are flagged for a CS manager to merge.
  - Nothing is merged automatically.

Reply "go ahead" (or send changes) and I'll create the stories, link them and read each one back to check.