# Evidence — `wait` wakes on notices but never delivers them

Epistemic labels:

- **Observed**: reproduced on the current tree while filing.
- **Confirmed**: current code-path fact established by direct inspection.
- **Inferred**: best current explanation, still requiring validation.
- **Open**: unresolved; needs a decision before sign-off.

Baseline: `251 passed in 76.00s` on the tree at commit `94299d6`, run with
`python3 -m pytest -q test_baton_v6.py`.

## Environment note

**Observed:** the system `python3` (3.13.7) has no `pytest` module installed,
so the literal command in `AGENTS.md` fails with `No module named pytest`. The
251/251 baseline above was therefore established with a borrowed interpreter.
The reviewer has since added `justfile`, `requirements-dev.txt` and a
`.venv/` bootstrap (`just venv` / `just test`), which is the better fix; all
later runs in this finding use `.venv/bin/python -m pytest -q
test_baton_v6.py`, which is what `just test` invokes.

This is a host tooling gap only. `baton_v6.py` and `build_zipapp.py` remain
stdlib-only, the venv carries test tooling exclusively, and
`test_isolated_checkout_runs_full_reusable_suite` still proves the whole
reusable set passes from a bare copied tree. Baton's standalone property is
unaffected.

## The wake path

**Confirmed:** `_InotifyWatch.__init__` (`baton_v6.py:2585`) watches the
instance *directory* with `_WATCH_MASK`, which includes `IN_MODIFY` and
`IN_CREATE`. `_decode_inotify` (`baton_v6.py:2559`) marks an event `relevant`
when the changed name starts with `DB_NAME` (`mailbox.sqlite3`), which covers
the `-wal` and `-shm` siblings.

**Confirmed:** `Store.send_notice` (`baton_v6.py:1289`) writes rows into
`contents` and `notices` inside a normal write transaction. In WAL mode that
commit modifies `mailbox.sqlite3-wal`, so the directory watch fires.

**Confirmed:** the waiter requeries after *every* poll return —
`_InotifyWatch.poll` returns flags but `wait_for_message` calls its query
helper unconditionally afterwards (`baton_v6.py:2686`). `relevant` is
informational; only `revalidate` alters control flow.

**Conclusion (Confirmed):** `send-notice` does wake a blocked `wait`. The wake
is not the defect.

## The delivery path

**Confirmed:** `wait_for_message`'s inner helper is `try_claim`
(`baton_v6.py:2643`) and its only query is
`store.claim(participant, actor=actor, seed=seed)`.

**Confirmed:** `Store.claim` (`baton_v6.py:1066`) selects exclusively from
`messages` where `to_participant=? AND state='pending'`. It has no knowledge
of the `notices` table. When nothing is pending it raises `BatonError(...,
EXIT_NONE)`, which `try_claim` swallows into `None`.

**Conclusion (Confirmed):** the waiter wakes, requeries only the directed
message table, finds nothing, and goes back to sleep. Unseen notices are
reachable solely through `see` (`baton_v6.py:1323`), a separate command a
blocked waiter is by definition not running. This reproduces the reported
symptom exactly and is the whole of the defect: **the wake is right, the
requery is incomplete.**

## What `see` already guarantees

**Confirmed:** `Store.see` runs one transaction (`_txn_begin("see", ...)`)
that selects every live notice lacking a `notice_seen` row for
`(participant, actor)`, inserts the receipt for each, and commits. Selection
and receipt are therefore already atomic with respect to each other.

**Confirmed:** the receipt key is `(notice_id, participant, actor)`
(`baton_v6.py:431`), so two actors of the same participant, and two
participants, each receive an independent copy. Dedupe is per actor, not per
participant.

**Confirmed:** expired notices are skipped by `_notice_expired` before any
receipt is written (`baton_v6.py:1338`), so a TTL-elapsed notice is never
marked seen and never returned.

**Confirmed:** `notice_seen` rows are immutable and are deletable only under
verb `expire` or `gc` (`trg_notice_seen_update`, `trg_notice_seen_delete`,
`baton_v6.py:626`, `:630`). A receipt, once written, cannot be rewritten to
re-deliver a notice.

**Inferred:** because `see` already carries every property the fix needs
(atomic receipt, per-actor independence, TTL filtering, no claim), the
smallest correct change is to make the waiter *call `see`* rather than to
grow a parallel notice-reading path. A second path would be a second place to
get TTL filtering, receipt atomicity, and the trigger contract wrong.

## Why notices cannot be claim-shaped

**Confirmed:** `claims` rows reference `messages(id)` and `Store.claim`
transitions a message `pending → claimed`. A notice has no message row and no
per-recipient state — it is one row read by every participant. There is no
per-recipient state machine to advance, so a broadcast cannot be given
claim/reply/close semantics without inventing per-recipient message rows,
which would turn a broadcast into N directed messages and change the
retention, `gc`, and `doctor` contracts.

**Conclusion (Confirmed):** "notice delivery must not create a claim" is not
merely a preference; a claim is not constructible for a notice without
redefining what a notice is.

## Crash and retry

**Confirmed:** the receipt commits inside the delivery transaction. If the
`wait` process dies after that commit but before the operator reads stdout,
the notice is not redelivered to that `(participant, actor)`.

**Confirmed:** this is *exactly* the existing `see` contract — `see` has
always marked-and-returned in one transaction, and a crash between commit and
terminal output loses the same bytes. Delivering notices through `see` gives
`wait` the same at-most-once property rather than a new, weaker one.

**Inferred:** at-most-once is inherent to claimless broadcast. The only way to
get at-least-once is per-recipient acknowledgement, i.e. a claim, which the
contract forbids and which the schema cannot express. Directed messages remain
the at-least-once channel; notices are advisory. This must be documented
rather than silently assumed.

**Open (resolved below in FINDING.md):** what happens when a directed message
and an unseen notice are both available at the same instant.

## Unplanned production confirmation

**Observed:** immediately after the rebuild, the implementer's own `wait`
against the live `drift-suite-local` instance delivered this:

    "id": "36c5b990cdb777783957c4919d3d3f45",
    "from_participant": "lang.reviewer",
    "kind": "baton_standalone_migration",
    "created_ts": "2026-08-07T03:05:35Z",
    "seen_ts":    "2026-08-07T04:21:38Z"

A real broadcast notice, published by another domain at 03:05:35, sat unseen
for **76 minutes** while this implementer ran blocking `wait`s against the
same instance across that entire window. Those earlier waits used the
pre-rebuild `bin/baton` and never surfaced it — the notice was discoverable
only by running `see`, which nobody did. The first `wait` started after the
rebuild delivered it at once.

This is the reported defect reproducing unprompted in production against real
traffic, and the fix resolving it against the same message. It is stronger
evidence than any fixture: nobody constructed it.

**Note:** the notice's own content is unrelated to this finding (it announces
Baton's move to `$HOME/src/baton`, the path this work already uses) — its
value here is purely as an undelivered broadcast that the fix delivered.

## The write-lock trap in the obvious implementation

**Observed:** the first working implementation called `store.see(limit=1)`
unconditionally on every requery. Instrumenting `Store._txn_begin` and running
an idle `wait` for 0.5s at a 0.05s interval recorded **211 `see` write
transactions**. The same probe against the pre-fix tree records **zero**.

**Confirmed:** the asymmetry is structural, not incidental. `Store.claim`
(`baton_v6.py:1069`) runs a plain `SELECT` for a pending row and raises
`EXIT_NONE` *before* `_txn_begin`, so the pre-fix waiter never took the write
lock while idle. `Store.see` has no such pre-read — it opens the transaction
first and discovers emptiness inside it.

**Confirmed:** the failure mode is worse than contention. `_txn_begin` maps a
busy `BEGIN IMMEDIATE` to `BatonError(..., EXIT_RACE)` (`baton_v6.py:791`),
and the waiter's handler re-raises everything that is not `EXIT_NONE`. An
idle waiter would therefore be **stood down by unrelated write traffic from
any other participant** — a regression strictly worse than the notice-delivery
bug being fixed, since `wait` is the sole inbound path for every agent.

**Confirmed fix:** `Store.has_unseen_notice` is a read-only probe gating entry
into `see`'s transaction, giving the notice path the same read-then-transact
shape `claim` already has. Re-running the probe records zero write
transactions while idle. The TOCTOU window is benign — `see` re-filters under
the write lock and returns `[]` if the notice expired or was consumed.

**Inferred:** an expired-but-undeleted notice is the nastier version of this.
Without the probe, a waiter would enter `see`'s write transaction on every
poll for as long as the expired row survived (up to `gc`/`expire`), returning
nothing each time. Both `test_idle_wait_takes_no_write_transaction` and
`test_expired_notice_never_delivered` now assert zero write transactions.

## Race surfaces already covered by the existing loop

**Confirmed:** the query → arm → requery → block sequence
(`baton_v6.py:2662`–`2688`) closes the query-to-arm race for whatever the
requery inspects. Extending the requery to notices therefore inherits the race
closure for free — but only if the notice read happens inside the same helper,
on the same `open_instance`, not as a separate pass around it.

**Confirmed:** the degraded path (`_InotifyWatch` construction raises
`OSError` → `watch = None` → `time.sleep(slice_s)`) uses the identical
requery helper, so polling fallback inherits notice delivery for free too.

**Confirmed:** gates are enforced inside `_txn_begin` on every write
transaction (`baton_v6.py:793`). `see` is a write transaction, so a
maintenance/moved instance stands the notice path down exactly as it stands
the claim path down. No separate gate check is needed — but a regression test
must prove the notice path did not acquire a gate bypass.
