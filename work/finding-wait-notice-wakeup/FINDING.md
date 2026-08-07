# `wait` wakes on a broadcast notice but never delivers it

Folder: `work/finding-wait-notice-wakeup/`
Role: implementer (`baton.implementer`)
Status: **complete — implemented, reviewed, approved and closed.** Shipped as
tool 1.0.1 on protocol 6; the behaviour is unchanged in the current tree, so
the hashes and test counts recorded below are the historical record of this
finding at the time it closed, not current values.
Baseline: 251/251 passing at commit `94299d6`.

## Problem

`send-notice` commits to the WAL, the instance-directory inotify watch fires,
and a blocked `wait` wakes. `wait_for_message` then requeries **only**
claimable directed messages via `Store.claim`, finds nothing pending, and
blocks again. An unseen broadcast notice is therefore invisible to `wait`; the
only way to discover it is to run `see`, which a blocked waiter is by
definition not running.

For an agent whose entire input path is one long-lived `wait`, this makes
broadcast notices undeliverable in practice. Slawomir ruled that broadcasts
must wake **and** be delivered by `wait`.

Full code-path evidence is in `EVIDENCE.md`. The short version: the wake is
correct, the requery is incomplete.

## Contract

`wait` returns one delivery. That delivery is now one of two shapes.

**Directed delivery — byte-for-byte unchanged:**

```json
{"claim": {...}, "message": {...}}
```

**Notice delivery — new:**

```json
{"notice": {"id": ..., "from_participant": ..., "kind": ...,
            "created_ts": ..., "ttl_seconds": ..., "content_sha256": ...,
            "seen_ts": ..., "body": {"base64": ..., "size": ...,
                                     "sha256": ..., "utf8": ...}}}
```

Consumers discriminate on key presence. No key was added to or removed from
the directed shape, so every existing consumer that reads `result["claim"]`
and `result["message"]` is unaffected by this change when a directed message
is what arrives.

### Decisions taken, with reasons

**1. Directed messages take strict precedence over notices.**
When a pending directed message and an unseen live notice are both available,
`wait` returns the directed message. Rationale: claimable work must never be
delayed behind advisory broadcast, and this preserves exact behavioural parity
for every existing consumer — a consumer that only ever receives directed
traffic observes no timing or ordering change whatsoever. Notices drain
whenever the directed queue is empty, which for a loop-and-process consumer is
between every unit of work. Starvation of notices requires a permanently
non-empty directed queue, in which case the consumer has more urgent problems.

**2. One notice per `wait` return, oldest first.**
`wait` has always been "block until exactly one delivery"; returning a batch
would make the return shape depend on arrival timing. Ordering is by
`created_ts`, matching `see`. Draining N notices takes N `wait` calls, exactly
as it takes N `wait` calls to drain N directed messages.

**3. Notice delivery reuses `Store.see`, it does not reimplement it.**
`see` already selects unseen live notices, skips TTL-elapsed ones, and writes
the `notice_seen` receipt in the same transaction. `see` gained one optional
`limit` parameter; `wait` calls it with `limit=1`. There is deliberately no
second notice-reading code path, because a second path is a second place to
get TTL filtering, receipt atomicity, and the trigger contract wrong. It also
makes "what `wait` delivers" and "what `see` returns" the same question by
construction rather than by agreement.

**4. No claim is created, and none can be.**
`claims` rows reference `messages(id)`; a notice has no message row and no
per-recipient state to advance. The audit verb stays `see`, so
`doctor`'s known-verb set, the transition-ledger edge table, and the
`notice_seen` delete guard (`expire`/`gc` only) are all untouched.

**5. Notice delivery is at-most-once per `(participant, actor)` — the same
contract `see` has always had.**
The receipt commits with the read. A process that dies after that commit but
before the operator reads stdout does not get the notice again. This is
inherent to claimless broadcast: at-least-once requires per-recipient
acknowledgement, which is a claim, which the schema cannot express for a
notice. Directed messages remain the durable, at-least-once channel. This is
now stated explicitly in `README.md` and `AGENTS-MAILBOX-PROTO.md` rather than
left as folklore.

**6. Self-authored notices are delivered to the author's own waiter.**
**Ruled by Slawomir (`contract_decision`, outcome `accepted`): option A, keep
parity.** The rule is now explicit — deliver a notice to every
participant+actor that has not seen it, the author included, and `see` and
`wait` must use that same rule. `test_author_receives_own_notice` is the
contract regression and stays.

The reasoning that was escalated: `see` has never excluded self-authored
notices and the receipt key is `(notice_id, participant, actor)`. Excluding in
`wait` only was the one clearly wrong option, since the two commands would
then disagree about what "unseen" means with nothing in the receipt table to
explain the difference; excluding in both was a change to `see` outside the
scope of this bug. Escalated rather than settled between implementer and
reviewer because it is a genuine semantic choice, not a defect.

**7. `EXIT_NONE` on timeout is unchanged**, but its message now reads "no
message or notice for ... arrived within the timeout", because the waiter now
covers both.

**8. The idle waiter stays read-only — a read probe gates the `see`
transaction.**
This one is a defect I introduced and then caught, and it is the most
important thing in this change after the fix itself. `see` opens a write
transaction (`BEGIN IMMEDIATE`), but a waiter polls indefinitely. Calling
`see` unconditionally on every requery made an *idle* waiter open a write
transaction per poll cycle — measured at 200+ in half a second at a 0.02s
interval, against **zero** before this work, because `Store.claim` raises
`EXIT_NONE` from a plain read before it ever transacts.

Two consequences, the second serious:

- an idle waiter contends for the write lock with every real writer on the
  instance, for no reason;
- `BEGIN IMMEDIATE` on a busy store raises `EXIT_RACE`, and `try_deliver`
  re-raises anything that is not `EXIT_NONE` — so unrelated write traffic
  could **stand a healthy idle waiter down**. `wait` is the long-lived inbound
  path for every agent in the deployment; killing it on someone else's write
  is a much worse bug than the one being fixed.

`Store.has_unseen_notice` is a read-only probe, and the waiter only enters
`see`'s transaction when it returns true — exactly the shape `claim` already
uses (read for a candidate, then transact). The race is harmless: `see`
re-filters under the write lock and returns nothing if the notice expired or
was consumed meanwhile. `test_idle_wait_takes_no_write_transaction` and
`test_expired_notice_never_delivered` both assert zero write transactions, so
this cannot silently return.

**9. Notice ordering gained the `id` tiebreak: `ORDER BY created_ts, id`.**
`_utc_now_iso` truncates to whole seconds, so `created_ts` alone is not a
total order and "oldest first" was undefined for notices published in the same
second. This matches the order `Store.claim` already uses for directed
messages. It only affects same-second ties, which previously resolved
arbitrarily.

**10. `see` now reports `seen_ts` on each returned notice.**
Additive, and it keeps the `see` and `wait` notice shapes identical — which is
the point of decision 3: the two commands answer the same question with the
same bytes.

## Changes

| File | Change |
| --- | --- |
| `baton_v6.py` | `Store.see` gains `limit`, the `id` ordering tiebreak, `seen_ts` in its result, and a `_fault("see:selected")` seam; new read-only `Store.has_unseen_notice`; new `_notice_delivery`; `wait_for_message`'s `try_claim` becomes `try_deliver`, probing then falling through to `see(limit=1)`; timeout message reworded |
| `test_baton_v6.py` | `TestWaitNoticeDelivery` — the regression matrix below |
| `README.md` | `wait` documented as delivering both shapes; at-most-once notice contract stated |
| `AGENTS-MAILBOX-PROTO.md` | notices consumed with `see` **or** `wait`; at-most-once stated |
| `bin/baton`, `DISTRIBUTION.json` | rebuilt — both manifest-pinned inputs (`baton_v6.py`, the protocol doc) changed |

## Regression matrix

Every row is an executable test in `test_baton_v6.py`. Results recorded after
the final build.

All 21 live in `TestWaitNoticeDelivery` in `test_baton_v6.py`. Rows marked ✻
were verified to **fail** against the unfixed tree before the implementation
was written; the three unmarked rows are no-regression pins that correctly
pass in both directions.

| # | Property pinned | Test |
| --- | --- | --- |
| 1 ✻ | A notice published while `wait` is blocked wakes it and is delivered, well inside the rescan interval | `test_notice_wakes_blocked_wait` |
| 2 ✻ | A notice already unseen at call time is delivered immediately, in a shape that is never claim-shaped | `test_existing_unseen_notice_delivered_immediately` |
| 3 ✻ | Notice delivery creates no claim, no message row, no ledger transition; the receipt is the only state written, and `doctor` stays clean | `test_notice_delivery_creates_no_claim` |
| 4 ✻ | The seen receipt is written with the delivery; a second `wait` does not redeliver | `test_notice_not_delivered_twice` |
| 5 ✻ | Receipt and selection are atomic — a fault before commit leaves no receipt and the notice stays deliverable | `test_notice_receipt_atomic_with_selection` |
| 6 ✻ | A notice delivered by `wait` is not returned again by `see`, and one consumed by `see` is not delivered by `wait` | `test_wait_and_see_share_one_receipt` |
| 7 | Directed-message parity: a pending directed message delivers in the byte-identical `{claim, message}` shape while a notice is unseen, and writes no receipt | `test_directed_message_wins_over_notice` |
| 8 ✻ | Once the directed message drains, the notice is delivered | `test_notice_delivered_after_directed_drains` |
| 9 ✻ | Independent delivery to two participants | `test_notice_delivered_to_each_participant` |
| 10 ✻ | Independent delivery to two actors of one participant (two receipt rows) | `test_notice_delivered_to_each_actor` |
| 11 ✻ | Polling fallback (inotify unavailable) delivers notices | `test_notice_delivered_on_degraded_polling` |
| 12 ✻ | Query-to-arm race: a notice published at the arm seam is delivered by the requery, not by the rescan | `test_notice_arm_race_closed_by_requery` |
| 13 ✻ | An idle waiter opens **zero** write transactions across many poll cycles, and exactly one (`see`) once a notice exists | `test_idle_wait_takes_no_write_transaction` |
| 14 | A TTL-expired notice is never delivered, never marked seen, and never makes the waiter take the write lock | `test_expired_notice_never_delivered` |
| 15 | A gated instance stands the notice path down with `EXIT_GATED` | `test_notice_path_respects_gate` |
| 16 ✻ | Timeout stays a clean `EXIT_NONE` when the only notice is already seen, and the diagnostic names both channels | `test_seen_only_notice_times_out_clean` |
| 17 ✻ | Body is lossless (base64 + size + sha256, utf8 when decodable, absent when not), hash-agrees with the envelope, and the delivery is JSON-clean — parametrized over UTF-8 and undecodable bytes | `test_notice_body_lossless` |
| 18 ✻ | A tampered notice body is `EXIT_DAMAGE`, never a delivery | `test_notice_delivery_refuses_corrupt_body` |
| 19 ✻ | CLI end-to-end: `baton wait` prints a notice delivery, exits 0, and CLI `see` then agrees it is consumed | `test_cli_wait_delivers_notice` |
| 20 ✻ | `see(limit=1)` takes the oldest only; an unlimited `see` still full-drains | `test_see_limit_partial_drain` |
| 21 ✻ | `limit` rejects 0, negative, float, str and bool — parametrized | `test_see_rejects_bad_limit` |

Added in review round 1 at the reviewer's request (rows 22–24). These pin
behavior that was already correct — the reviewer's independent adversarial
checks confirmed all three — so they are no-regression tripwires rather than
fix verification.

| # | Property pinned | Test |
| --- | --- | --- |
| 22 | Post-commit crash: the receipt survives, the same actor is not given a second chance, and the loss is scoped to that receipt rather than the notice | `test_receipt_survives_crash_after_commit` |
| 23 | An expired oldest notice does not mask a live newer one — TTL filtering runs in Python, after the ordered SELECT | `test_expired_oldest_does_not_mask_live_notice` |
| 24 | An author's own waiter receives its own broadcast (parity with `see`; see decision 6 and the open escalation) | `test_author_receives_own_notice` |

Row 23 was mutation-checked rather than merely observed to pass: pushing
`LIMIT ?` into the `see` SQL — precisely the future optimization the reviewer
named — makes `wait` block forever behind the dead notice and fails this test
alone. The two pre-existing TTL tests both still pass under that mutation, so
the row covers a real gap.

## Results

- Baseline before this work: **251 passed in 76.00s**.
- Regression-first check: with the tests on the tree and no implementation,
  **22 failed, 3 passed** — the 18 ✻ rows (26 items, 22 of them failing) plus
  the 3 no-regression pins.
- After implementation: **277 passed in 84.84s**, `0 failed`.
- After review round 1: **280 passed in 88.00s**, `0 failed` — 251 baseline
  plus 29 new items (24 test methods, two of them parametrized ×2 and ×5). No
  baseline test was modified, deleted, or skipped.
- `TOOL_VERSION` bumped `1.0.0` → `1.0.1` at the reviewer's request. The
  database protocol stays at 6 — schema and wire shapes are unchanged — but
  `wait`'s observable output and the shipped executable both changed, and two
  behaviorally different artifacts must not both identify as 1.0.0.
  `./bin/baton --version` now reports `baton 1.0.1 (protocol 6)`.
- `build_zipapp.py` rerun; `DISTRIBUTION.json` and `bin/baton` regenerated.
  Builds into separate roots agree, matching `sha256sum bin/baton`:
  `artifact_sha256 = 7b85918348f50bfd606153a380ce14dd4cf154cbbffe992790cb8daed84d7818`,
  `source_sha256 = 86d09104f343a5060f2dec43ee40893b69eab962266486d2724396e4316770f2`.
  Both manifest-pinned inputs changed — `baton_v6.py` and
  `AGENTS-MAILBOX-PROTO.md` — so the rebuild was mandatory, not cosmetic.
- Independent end-to-end verification against the **packed `bin/baton`**, not
  the source module, on a scratch instance built from `example-baton.json`:
  a `wait` blocked with `--interval 45` received a notice published 2s later
  in **0s elapsed** (a real wake, not a rescan); `scan` showed no claim; a
  second `wait` for the same actor exited 3; a different participant received
  its own copy; with both queued, the directed message came back as
  `{claim, message}` and the notice drained on the next call; `doctor`
  reported `ok: true` with no problems.

## Not done, deliberately

- No consumer-side workaround, no polling helper, no "check notices too"
  wrapper — the defect is in `wait` and the fix is in `wait`.
- No Drift-specific or host-project coupling: the change touches only the
  generic protocol surface, and the tests continue to use the neutral
  `acme.*` / `hq.*` fixture shop.
- No new *protocol* version (the tool version did move to 1.0.1). The
  wire/database schema is unchanged; this is a
  delivery-completeness fix within protocol 6, and an old consumer talking to
  a new binary sees an unchanged directed shape.
