# Activate Baton v10

Status: **authorized 2026-08-13**

## Ruling

Slawomir authorized the one-pass switch from the retained legacy 1.1.0
client/mailbox to the deployed 10.2.0 clients and fresh v10 mailbox.

Use only these active paths:

```text
/home/sl/baton/app/baton-cli/v10/v10.2.0/bin/baton
/home/sl/baton/app/baton-tui/v10/v10.2.0/bin/baton-tui
/home/sl/baton/mailbox/v10/baton.json
```

The legacy authority and direct frozen clients remain retained, inactive, for
historical access. No messages, claims, receipts, or history migrate. Pending
legacy work is consciously left on that retained authority and does not block
the cutover.

The bridge changes binary and config together, restarts once, and proves a
directed reviewer/implementer round trip plus scoped notice receipt on v10.

