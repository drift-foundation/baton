# Progress: make live worker progress observable

No implementation claim has started. The confirmed MVP boundary is recorded
and bound to canonical Baton Work W61599.


## 2026-09-01 — first implementer round (`baton.claude`, W61599 impl claim)

**The default liveness projection is implemented end to end. The `result/logs/`
capability, the safe-progress stream, the locator and the CLI follow view are
NOT, and PLAN item 5 is therefore half done rather than done.**

I took PLAN item 5 in the order it is written -- the projection first --
because it is the part that answers the W52821 question ("is this worker
moving?") on its own, and because it needs no new durable content surface.

### What an operator can now be told, and what it costs

Two numbers, per attempt, in this manager's own control store: how many bytes
of the worker's native session stream this manager has OBSERVED, and the
MANAGER's receipt instant for the latest of them. That is the whole of it.
No provider timestamp, no native log path, no sample of what was read.

M61707's credential-free durable surface is preserved BY CONSTRUCTION rather
than by a redactor: what crosses from the observing loop is a length. A count
cannot carry a credential, which is the property W39357's `DEVNULL` correction
was protecting and the reason this slice could be built before the sanitization
boundary exists.

### The seams, and why each is where it is

`schema.py` -- SCHEMA_VERSION 14, and two nullable `attempts` columns,
`activity_bytes` and `activity_at`, under a both-or-neither CHECK. A schema-13
store has nowhere to put either, so a manager reading one could only answer
"unknown" for every attempt. The columns are diagnostic: nothing that was
authorized under 13 is authorized differently under 14.

`attempts.observe_activity` -- the writer. The operand is a CUMULATIVE TOTAL
rather than a delta, which is what makes a lost, duplicated or reordered report
harmless. Monotonicity is decided INSIDE the write against the exact value the
update compares, for the reason `observe` decides its transition there.

`attempts.attempt_activity_of` -- the reader. An id naming no attempt answers
`None`; a recorded attempt nobody has observed answers a projection whose
members are `None`. Those are different facts and a zero would conflate them.

`tools/dogfood_operator._Channel` -- the one place in this manager that sees a
live worker producing anything. It already drained the exec process's stderr so
a full pipe could not wedge the session, and it was throwing the FACT away
along with the bytes. It now counts every byte, including the ones past the
bounded window it deliberately forgets, and publishes the running total through
an injected observer.

`tools/dogfood_operator._activity_observer` -- the deployment's publisher. It
opens, writes and closes its own handle per publication, because `_Channel`
drains from a thread of its own and a `sqlite3` connection belongs to the
thread that opened it. A handle it forgot to close would be a lock the next
incarnation waits on, which this deployment has been bitten by before.

### Three decisions this record did not contain, now recorded in FINDING.md

1. A REPEATED TOTAL DOES NOT MOVE THE INSTANT. An observer polling a quiet
   stream is behaving correctly and its report is accepted, but the instant is
   the age of the latest observed ACTIVITY -- advancing it would make a wedged
   worker read as freshly alive to the one operator relying on this to notice.
2. A DECREASE REFUSES rather than being absorbed, so a stale observer cannot
   make a progressing worker look stalled.
3. PUBLISHING FAILURES ARE DROPPED AT THE DRAIN. The loop exists to stop a full
   pipe from hanging the session; a diagnostic projection that could raise out
   of it would wedge the very thing it was added to observe.

### Mutation check

Six mutations, all caught:

    CAUGHT  a repeated total freshens the instant
    CAUGHT  a decrease is silently accepted
    CAUGHT  the end of the stream is never published
    CAUGHT  an observer fault escapes the drain      [wedges the session]
    CAUGHT  bytes past the bounded window are not counted
    CAUGHT  the observer leaks the handle it opened

### Verification

    tests.manager.test_attempts + test_store + test_workspaces
      + test_credentials + test_oci + test_secrets + test_text_sweep
      + tests.tools.test_dogfood_operator            1083 tests, OK
    the whole v12 python suite                       2986 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity:
      five in `test_boundary_inventory`, one in `tests.authority.test_catalog`
      and `test_credentials_engine`'s host check

The schema bump made two boundary-inventory attempt-document fixtures
incomplete -- a persisted attempt document carries every column -- and the two
new exports needed their entries in the §13 accounting, the text sweep's table
and the public-operand declaration. All four are additive registry members.

The working-tree diff check is clean and no added line exceeds 79 characters.

### NOT DONE, and named rather than left to inference

- the manager-minted attempt-result/log capability, the sink created before
  runtime start, the incomplete/complete marking and the stable relative
  locator under `result/logs/` (the second half of PLAN item 5);
- the closed provider-safe progress stream itself and its worker-side emitter
  (PLAN item 5, and the reason item 8's matrix is not started);
- the CLI follow view (item 6) and the TUI rendering (item 7);
- rendering `Log 1.40 MiB · updated 4s ago` anywhere. The projection is
  exposed as a manager read; nothing displays it yet, and the display belongs
  with the follow surface rather than ahead of it.

### State

Awaiting review of the projection slice before the sink and the safe stream are
built on top of it. Passing back rather than closing.
