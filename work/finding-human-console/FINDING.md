# Baton needs a human-oriented console

Folder: `work/finding-human-console/`
Status: queued next; not started.
Priority: **#1 immediately after the current protocol-7 work lands.**
Raised by: Slawomir during `work/finding-wait-notice-wakeup/`.

## Problem

Raw Baton JSON is an appropriate machine protocol but a poor human interface.
Reading and responding from a terminal currently exposes transport details,
including base64 bodies and seeds, and makes claim lifecycle actions easy to
get wrong.

## Required direction

Provide a console or UI that:

- presents readable message parts;
- hides base64 and actor seeds by default;
- shows pending and claimed state clearly;
- provides explicit wait/inbox, reply, close, notice, and attachment actions;
- makes it clear when a consumed directed message still requires `reply` or
  `close`.

## Authority and safety constraint

The console must use Baton's transactional API. It must never read or mutate
the SQLite authority as an alternative protocol path. Direct database writes
can violate claim and receipt invariants and are treated as corruption by
`doctor`.

## Sequencing

This is the next finding after the immediate protocol-7 work lands. It does
not wait for `work/finding-multipart-content/`: the current human workflow is
already too rough for safe routine use.

The first console increment must make today's text-message protocol usable,
while isolating content rendering behind a part/view boundary so multipart
can replace the current body envelope without rewriting claim lifecycle and
inbox interaction. Multipart remains separate versioned protocol work and is
integrated when available.

## Acceptance criteria

- A human can wait for, inspect, reply to, and close directed messages without
  manually parsing raw JSON.
- A human can remain in an inbox/wait loop after handling a delivery instead
  of manually reconstructing the wait command each time.
- Short ACKs, status updates such as “still working; give me more time,” and
  simple decisions can be sent inline without creating temporary body files.
- The workflows previously covered by the local `wait_for_msg.sh`,
  `reply_with_claim.sh`, and `close_with_claim.sh` helpers are first-class
  console actions rather than machine-specific scripts.
- A human can inspect and publish notices and work with attachments.
- Content is rendered according to its declared part metadata, with safe
  fallbacks for unsupported media.
- Seeds and encoded binary bodies are not displayed unless explicitly
  requested.
- Claim state and the next required lifecycle action are always visible.
- Every state-changing action goes through the Baton executable/API and
  preserves its transactional and audit guarantees.
- The console remains standalone and contains no host-project or
  Drift-specific assumptions.

## Not done yet

No implementation or UI technology has been selected. This finding records
the product and safety contract only.
