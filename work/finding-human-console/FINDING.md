# Baton needs a human-oriented console

Folder: `work/finding-human-console/`
Status: queued next; not started.

> Refreshed 2026-08-07 for the shipped protocol. The seed-based identity model
> and the protocol-7 sequencing this finding originally assumed are both
> obsolete: a participant address is now the whole identity, and the typed
> content envelope has landed. Product acceptance criteria are unchanged.
Priority: **#1 immediately after the post-cutover cleanup review closes.**
Raised by: Slawomir during `work/finding-wait-notice-wakeup/`.

## Problem

Raw Baton JSON is an appropriate machine protocol but a poor human interface.
Reading and responding from a terminal exposes transport details -- base64
payloads, manifest digests, part trees -- and makes claim lifecycle actions
easy to get wrong.

## Required direction

Provide a console or UI that:

- presents readable message parts;
- hides base64 payloads and integrity metadata by default;
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

Next after the post-cutover cleanup review closes, including
`work/finding-attachment-part-convergence/`.

**The multipart dependency is gone.** The typed content envelope shipped in
`work/finding-typed-content-envelope/`, so the console is built against the
real content model rather than against a placeholder to be replaced later.
That removes the part/view isolation this finding previously called for as a
hedge: there is nothing left to swap in.

What the console can now rely on:

- every body is an ordered `parts` tree with a declared `content_type`,
  `disposition` and optional advisory `filename`;
- each leaf carries exactly ONE representation, named by `encoding` -- `text`
  or `base64` -- so rendering dispatches on one stable key instead of probing;
- `filename` is advisory and must NEVER be used to open, create or name a
  file, which is a console-side hazard as much as a protocol one;
- Baton itself renders nothing. A console that renders HTML or Markdown owns
  that injection surface entirely and must treat every part as hostile input.

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
- Content is rendered according to its declared `content_type`, with safe
  fallbacks for unsupported media and no execution of untrusted markup.
- Encoded binary payloads and integrity metadata are not displayed unless
  explicitly requested.
- Multipart messages are navigable: a human can see that several parts exist,
  choose among `multipart/alternative` variants, and materialize a specific
  part.
- Claim state and the next required lifecycle action are always visible.
- Every state-changing action goes through the Baton executable/API and
  preserves its transactional and audit guarantees.
- The console remains standalone and contains no host-project or
  Drift-specific assumptions.

## Not done yet

No implementation or UI technology has been selected. This finding records
the product and safety contract only.
