# Implementation handoff — wait/broadcast TOOL_BUG

Finding folder: `work/finding-wait-notice-wakeup/` (`FINDING.md`, `EVIDENCE.md`).
Attached separately: the two documents, hash-pinned under root `baton.source`.

## Root cause, confirmed independently

The wake was never broken. `send_notice` commits to the WAL, the
instance-directory inotify watch fires, and the waiter requeries — the decoder
treats every `mailbox.sqlite3*` name change as relevant, and the waiter
requeries after every poll return regardless.

The defect is that the requery was `Store.claim` alone, which reads only
`messages WHERE to_participant=? AND state='pending'`. It has no knowledge of
the `notices` table. So `wait` woke on a notice, found no pending message, and
went back to sleep. **The wake is right; the requery was incomplete.**

I could not find a cleaner or safer contract than the one you were given, and
I did look — see "Decisions taken" in `FINDING.md` for the six semantic
choices with reasons. Two things I want you to push on specifically are marked
below.

## Shape

    {"claim": ..., "message": ...}   directed — byte-for-byte unchanged
    {"notice": ...}                  broadcast — new

No key was added to or removed from the directed shape. Discrimination is by
key presence.

## The one thing I got wrong, and caught

My first working implementation called `store.see(limit=1)` on every requery.
`see` opens a write transaction; `claim` does not when the queue is empty
(it raises `EXIT_NONE` from a plain `SELECT` before `_txn_begin`). So an idle
waiter went from **zero** write transactions to **211 measured in 0.5s** at a
0.05s interval.

Contention is the mild half. The serious half: `_txn_begin` maps a busy
`BEGIN IMMEDIATE` to `EXIT_RACE`, and the waiter re-raises anything that is
not `EXIT_NONE` — so an idle waiter could be **stood down by unrelated write
traffic from any other participant**. That is strictly worse than the bug
being fixed, since `wait` is the sole inbound path for every agent here.

Fix: `Store.has_unseen_notice`, a read-only probe gating entry into `see`'s
transaction — the same read-then-transact shape `claim` already uses. Verified
back to zero. Pinned by `test_idle_wait_takes_no_write_transaction` and by an
added assertion in `test_expired_notice_never_delivered` (an expired,
not-yet-collected notice was the nastier version: the waiter would have
spun on the write lock for the notice's whole remaining lifetime).

Please verify this one adversarially. It is the change I am least able to
review objectively, because I wrote both the bug and the fix.

## Please also push on

1. **Self-authored notices are still delivered to the author's own waiter.**
   `see` has never excluded them and the receipt key is
   `(notice_id, participant, actor)`. Excluding in `wait` only would make
   `wait` and `see` disagree about what "unseen" means; excluding in both is a
   change to `see` nobody asked for. I think parity is right, but this is a
   genuine semantic choice and it may belong with Slawomir rather than us.

2. **A notice whose content row is missing delivers `body: null` rather than
   raising `EXIT_DAMAGE`.** This is unchanged, deliberate parity with `see`,
   which has always used a `LEFT JOIN` on `contents`. A *corrupt* body is
   still `EXIT_DAMAGE` via `_body_repr` (pinned by
   `test_notice_delivery_refuses_corrupt_body`); it is only the missing-row
   case that stays soft, and `doctor` already reports orphan content. I chose
   not to give `wait` damage semantics that `see` lacks, but say so if you
   think both should harden.

## Crash and retry

Notice delivery is **at-most-once per (participant, actor)** — exactly `see`'s
existing contract, not a new weaker one. The receipt commits with the read; a
process that dies after that commit does not get the notice again.

At-least-once is not constructible for a claimless broadcast: it needs
per-recipient acknowledgement, which is a claim, and a `claims` row references
`messages(id)` while a notice has no per-recipient message row. Making one
would turn a broadcast into N directed messages and change the retention, `gc`
and `doctor` contracts. So this is documented in `README.md` and
`AGENTS-MAILBOX-PROTO.md` rather than left as folklore, and directed messages
are stated as the channel for anything that must not be missed.

`test_notice_receipt_atomic_with_selection` pins the other side: a new
`_fault("see:selected")` seam between the receipt insert and the commit
proves a crash there leaves no receipt and the notice still deliverable.

## Verification

- Baseline reproduced independently: **251 passed in 76.00s** at `94299d6`.
- Regression-first: tests written and run before any implementation —
  **22 failed, 3 passed**. The 3 are no-regression pins that correctly pass in
  both directions (directed-wins, TTL, gate).
- Final: **277 passed in 84.77s, 0 failed**, via `just test`. No baseline test
  was modified, deleted or skipped. 21 new methods, 26 items; the full matrix
  with per-row test names is in `FINDING.md`.
- Distribution rebuilt — both pinned inputs changed. Two builds into separate
  roots agree:
  `artifact_sha256 = f45d0e949a03a297337ca103e22b5a2d130981f3435caac1da7eb5fdc2d98fe2`,
  matching `sha256sum bin/baton`.
- Independent end-to-end against the **packed `bin/baton`**, not the source
  module, on a scratch instance from `example-baton.json`: a `wait` blocked
  with `--interval 45` received a notice published 2s later in 0s elapsed — a
  real wake, not a rescan. `scan` showed no claim; a second `wait` for the
  same actor exited 3; a second participant got its own copy; with both
  queued the directed message returned as `{claim, message}` and the notice
  drained on the next call; `doctor` reported `ok: true`.

## Standalone

Nothing Drift-specific and no host coupling. The change touches only the
generic protocol surface; tests stay on the neutral `acme.*` / `hq.*` fixture
shop; `test_isolated_checkout_runs_full_reusable_suite` still passes, so the
whole reusable set runs from a bare copied tree. No protocol bump: the schema
and wire shapes are unchanged, and an old consumer against a new binary sees
an unchanged directed delivery.

Thanks for `just venv` / `just test` — I adopted it and dropped the borrowed
interpreter.
