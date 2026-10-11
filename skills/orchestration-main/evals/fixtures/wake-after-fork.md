# Snapshot: main session, woken by the owner after a restart

`ListAgents` says: "This session is shopfront-main-2". Time now: 2026-10-11T14:05Z. The owner
wrote: "I had to restart my terminal. Anything from the build?"

## Output of `thread.sh list`

    shopfront 5c1d2e3f build=shopfront status=busy main=shopfront-main worktree=/home/dev/shopfront-orch-shopfront launched=2026-10-11T08:00Z

## Output of `thread.sh check`

    MOVED shopfront main=shopfront-main recorded=uds:/run/user/1000/cc-socks/41022.sock this=uds:/run/user/1000/cc-socks/58810.sock: if you are its main session now, run thread.sh adopt shopfront --main <your name>
    INBOX shopfront 2026-10-11T13:20Z to shopfront-main
      STATUS: need-decision - D5 order confirmation email provider
      Question: send order confirmations through SES or Postmark?
      Options: SES (already set up, plain template) | Postmark (better deliverability, new account, USD 15/month)
      Default: none, owner-before
      Blocks: lane order-email only; checkout continues
    INBOX shopfront 2026-10-11T13:40Z to shopfront-main
      STATUS: working - checkout-web landed; try https://dev.shopfront.example/checkout
