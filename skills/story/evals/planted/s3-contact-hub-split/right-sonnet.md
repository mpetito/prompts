Proposed: User Story: CRM - Show open support cases on the contact page for Customer Success [OPS-5930]
Proposed: User Story: CRM - Add an automatic "Last contacted" date to contacts [OPS-5930]
Proposed: User Story: CRM - Export an account's contacts to CSV for CS managers [OPS-5930]
Proposed: User Story: CRM - Flag duplicate contacts nightly for CS manager review [OPS-5930]

I would wait for you to confirm the split before writing anything, so I have made no tool calls.

**Note to Lena**

Hi Lena, I haven't put anything on the board yet. I need your OK on the split first.

Why not one story: the wish list has five separate outcomes. Each can be accepted and shipped on its own, and one 21-point story would be too big to ship in a sprint. For reporting, all the stories will carry OPS-5930 in the title and link back to the ticket, so one search on OPS-5930 pulls them together.

What I'd create: the four stories above, all under the "CRM Spring Change Request" Feature (4458), the parent of the other CRM stories in this sprint. They would use area path `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering` and the current iteration, `Kestrel Ledger\2026-11-30`. Each would have acceptance criteria written from the client's wording, with the full wish-list text copied in.

- **Inactive contacts (wish 2):** I would not file this one. Story 4936, "Inactive contacts drop out of account contact lists [OPS-7214]", is closed and looks like it covers it. Can you confirm that story also kept inactive contacts searchable? If it didn't, I'll file only that gap.
- **Open cases (wish 1):** Story 4935, "Customer Success contact page layout [OPS-7208]", is open and touches the same contact page. I'd file this as its own story and link it to 4935 as related. Tell me if you'd rather fold it into 4935.
- **Duplicate flagging (wish 5):** This one waits on the Integration Hub's nightly sync, which ships next month. I'd schedule it in a later iteration, with a predecessor link to the Integration Hub work. There is no Integration Hub story for the nightly sync yet, only the Integration Hub Feature (4555). Do you know of a story I should link to? I also need the next iteration's name, because I only looked up the current one.
- **Points:** I can't split Sam's 21 points across stories without guessing. Could Sam give an estimate for each of the four (1, 2, 3, 5, 8 or 13)?

Once you confirm, I'll create the stories, link them, and send you the ids and where each one sits.