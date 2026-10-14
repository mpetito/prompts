Proposed: Feature: CRM - Contact hub [OPS-5930]
Proposed: User Story: CRM - Show a contact's open support cases on the contact page [OPS-5930]
Proposed: User Story: CRM - Fill in "Last contacted" on contacts from logged calls and meetings [OPS-5930]
Proposed: User Story: CRM - Export an account's contacts to CSV for CS managers [OPS-5930]
Proposed: User Story: CRM - Flag duplicate contacts nightly for CS manager merge [OPS-5930]
Proposed (only if 4936 didn't already cover it): User Story: CRM - Hide inactive contacts from account Contacts lists but keep them searchable [OPS-5930]

I'm making no tool calls yet. I'd wait for Lena first, because two things in the request could put the wrong items on the board, and a third needs her input:

- **Wish-list item 2 may already be done.** Story 4936, "CRM - Inactive contacts drop out of account contact lists [OPS-7214]", is Closed. It's in the current sprint (2026-11-30) under the CRM Spring Change Request (4458). If it already covered this, a new story would duplicate finished work and count its points again.
- **One 21-point story with a blocked part won't report well.** Item 5 depends on the Integration Hub nightly sync, which ships next month. A story holding all five items would stay open until then, even if items 1–4 are finished this sprint. It's also too big to fit in one sprint. A Feature with one child story per item still gives a single line to report on, with points and progress rolled up, and lets the item 5 story be linked to Integration Hub (4555) as its predecessor. I'd only do this with her agreement, since she asked for one story.
- **Where it sits and how the points split.** Should it go under the CRM Modernization Program epic (4106), or inside the existing spring change request (4458)? And Sam's 21 points cover the whole list, so I'd need Sam's split per item rather than make one up. Item 1 may also overlap with 4935 ("Customer Success contact page layout [OPS-7208]"), which is still New.

Note to Lena:

> Hi Lena, before I put OPS-5930 on the board, three quick questions:
>
> 1. **Inactive contacts (item 2):** this looks like it was already delivered in #4936 (OPS-7214, Closed this sprint). Can you confirm it covered "still searchable"? If so, I'll leave it out.
> 2. **One story or a Feature:** item 5 can't start until Integration Hub ships next month, so a single 21-point story would stay open until then even if the rest is done. I suggest a "Contact hub [OPS-5930]" Feature with one story per item. You'd still get one line to report on, with points and progress rolled up, and I'd link the duplicate-flagging story to Integration Hub (#4555) as blocked by it. If you'd still prefer one story, I'll create exactly that.
> 3. **Placement and points:** should it go under CRM Modernization (#4106) or inside the Spring Change Request (#4458)? And could Sam split the 21 points across the items? Also, does item 1 overlap with #4935 (Customer Success contact page layout)?
>
> Once you reply, I'll create the items in the current sprint (except the blocked story) and add the links.