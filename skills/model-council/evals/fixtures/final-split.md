# Model council: state after the last exchange round

Scratch directory: /tmp/council-2b81. Requested by the orchestration thread for lane `billing`:
"Two reviewers disagree on the proration rounding fix. Run the council and tell me what to ship;
the lane is blocked on it."

## Packet (pinned at head 51d0a3c)

Question: `src/billing/prorate.ts:58` rounds each line item to cents before summing, so a 3-line
invoice can be off by up to 1.5 cents against the ledger. What should change? Candidate actions: no
change; round once after summing; switch the ledger to per-line rounding.

## Members

- Claude: subagent, model opus, effort high; focus correctness and contract.
- Codex: `codex_member.py`, model gpt-6-astra, effort high; focus simplicity and maintenance.

## Rounds

- Blind round: Claude `defect`, round once after summing; Codex `defect`, change the ledger.
- Exchange 1: both revised their reasoning, both kept their actions.
- Exchange 2 (the last allowed): both answers below.

## /tmp/council-2b81/round2-claude.md

The other member is right that the ledger's per-line rounding is what finance reconciles against,
but the invoice is the customer-facing document and the tax engine sums unrounded amounts
(tax/compute.ts:33). Rounding once at prorate.ts:58 keeps the invoice equal to the tax base. The
ledger then differs by under a cent per invoice, which the existing nightly reconciliation tolerates
(ledger/reconcile.ts:12, tolerance 0.02).

stance: hold
disposition: defect
action: round once after summing at src/billing/prorate.ts:58
decisive: src/tax/compute.ts:33
crux: whether finance requires invoice totals to equal ledger totals exactly

## /tmp/council-2b81/round2-codex.md

Rounding once after summing fixes the invoice but moves the mismatch to the ledger, which is the
system of record (ledger/README.md: "the ledger is authoritative for revenue"). Changing the ledger
to per-line rounding at the source keeps one rounding rule everywhere and removes the tolerance
special case at reconcile.ts:12.

stance: hold
disposition: defect
action: change the ledger to per-line rounding in src/ledger/post.ts and drop the reconcile tolerance
decisive: src/ledger/README.md
crux: whether finance requires invoice totals to equal ledger totals exactly
