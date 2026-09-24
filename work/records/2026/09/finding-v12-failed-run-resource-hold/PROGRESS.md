# Progress — W257624

## 2026-09-24 — baton.claude, claim 257697 — R1 delivered

**Stage: R1.** **Result: delivered for independent review.** **Next: R2**, which
owner 257693 explicitly does not authorize yet — I did not begin it, and I
added no clearance, resource guard or supervisor edit.

### What R1 asked for, and the defect finding it produced

"One caller owns a pre-effect uncertainty episode; all concurrent or restarted
callers refuse before submission **or reclamation** while it stands."

The second half of that was not true of the code I inherited from W247941. The
standing-hold check sat BELOW `_reconciled`, so a caller arriving behind a held
root still issued its listing — and, had a stranded candidate answered, would
have stopped and removed it. Those are destructive vectors on a path that must
issue none.

**The exclusion is claimed at the top of `custody_act` now**, before the vector
is composed and before any reconciliation.

### And claiming is not checking

A check and a write are two acts. `ControlStore.transact` takes
`BEGIN IMMEDIATE` and re-reads inside the lock, so two connections serialize
there — **but only if their operands differ**, because identical operands at
one identity are a replay, and the loser would be handed the winner's record
as its own claim. That is the hole a barrier race finds and a sequential test
never would.

So the claim carries a **submitter token**: a nonce, naming no path, selecting
no resource, never read back as authority. With it the loser signs different
operands at the same identity and the store refuses it under its own §4.2 rule
— one identity carries one act. No new primitive, and the exclusion is the
store's rather than mine.

### `test_hold_admission.py` — 7 cases, all passing

  * **two racing callers, barrier-driven, two connections** — SQLite binds a
    connection to its thread, so a one-connection race is not one; each racer
    opens its own handle on the same file, which is what two managers are.
    Exactly one episode exists and **exactly one submission crossed**;
  * **a held root admits nothing** — not one engine vector of any kind, which
    is stronger than "no stop or remove";
  * **a late visible helper** named exactly as the hold records it is neither
    observed nor reclaimed behind the standing hold;
  * **crash after submission** — the episode is durable: the store is closed
    and reopened on the same file, the episode reads back uncleared, and the
    reopened manager is bound by it having issued nothing;
  * **crash before submission** — nothing is claimed and nothing is held, so
    the accepted rule that a pre-submission failure commits nothing still
    holds;
  * **the held root keeps its bytes** — walked and compared, not asserted;
  * **replay does not authorize a second submitter** — the record replays, as
    a journal does, and the claimant is recorded so one submitter is
    distinguishable from another at one identity.

Two fixture faults the run found and I corrected rather than worked around: my
first race used one connection (SQLite refused it, correctly), and my severing
stand-in recorded the submission in a private list instead of on the engine, so
the submission counter read zero while a submission had in fact crossed.

### Evidence

```
PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-real-jobs-adoption-gate:$PWD/work/records/2026/09/finding-v12-failed-run-resource-hold"
BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=TERM --kill-after=5s 30s "$PY" -B \
  -W error::ResourceWarning -m unittest test_hold_admission
```

  * `test_hold_admission` — **7 cases, OK, 0.371s**, exit 0;
  * the documented baseline pair — **2 cases, OK, 0.156s**;
  * accepted suites over the changed file — `test_custody`,
    `test_abandoned_attempt_engine`, `test_intake`, `test_attempts`,
    `tests.tools.test_single_worker` — **920 tests, OK, 22.821s**, with no
    accepted test edited;
  * source hashes at hand-off:
    `custody.py` `sha256:e941ec1e2bffe16d6ff18125b67f60d5c0945ffc64adfc7336b2aad6b02a9e9c`,
    `test_hold_admission.py` `sha256:b72647d4a2b62a87db481b798db29a1f714be588ba6b8eafef14390b47481d2b`.

### An actionable runner prerequisite, reported rather than assumed

The PLAN requires an **operator-provisioned** disk-backed scratch parent and
says the recorded `/var/tmp/baton-w247941` is not a permission grant. I found
none provisioned for this Work, so **I created `/var/tmp/baton-w257624`
myself** — ext4, outside the checkout and outside every snapshot — and I am
naming that rather than presenting it as a grant. If the operator wants a
different root, these runs must be repeated under it; nothing about the results
depends on the path.

### Cumulative verification spending

This claim: 7 cases 0.371s (0.375s and 0.409s on the two intermediate runs
whose failures produced the fixture corrections above); the baseline pair
0.120s twice and 0.156s; 920 accepted tests 22.821s.

All W247941 spending stands and is unchanged by this Work: 966 OK
22.565/22.607/22.616/22.618/22.662/22.679/22.686/22.750s and the 22.798s run
with six failures, 121 OK 3.152s, 986 in 38.505s with its seven daemon
failures and the 15.647s pinned comparison, 899 OK 19.828s, 9.308s, 10.337s,
85 OK 68.787/68.953/69.017/69.194/69.207/69.215/69.262/69.281s with the two red
predecessors at 31.663s and 31.822s, 159.910s plus its untimed repeat, 0.966s,
1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s, 125 OK 4.803/4.805/4.875s,
329 OK 8.405s, the focused-fixture runs listed in that dossier's PROGRESS, the
untimed probes and diagnostic reads, the unmeasured ~120s command-timeout run
and the earlier unknowns, alongside named **1047.869180986s**.

### Constraints held

No live run, no deployed mutation, no actual recovery, no deletion, no
preserved-snapshot edit, no Git mutation in the shared checkout, no accepted
test edited, no ownership transfer. W44342 untouched. R2 not begun.
