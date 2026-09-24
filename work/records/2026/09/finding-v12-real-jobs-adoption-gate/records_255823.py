"""Claim-255823: Correction A implemented; the P1 closes positively."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255823; RETURNED INCOMPLETE

Owner reroute 255814 selected **Correction A** and granted exclusive ownership
of `v12/python/src/baton_v12/worker_manager/intake.py` and the focused tests.
It is implemented, and the P1 closes with a positive outcome rather than a
characterization.

## The correction

`intake.abandon_attempt` now asks whether THIS attempt has its own committed
cancellation, and fences by REPLAYING that Authority operation when it does.

  * **`_committed_cancellation`** is the new reader, in the owned file. It
    derives the cancellation's manager and Authority identities from the
    attempt and its fixed assignment, requires the record to be `committed`
    with the `attempt.cancel` kind, decodes it, recomposes the exact intent
    document those operands produce, and recomposes the canonical signature —
    the same evidence `unstarted_cancellation_of` holds its own copy to. The
    reason is the one member that is not derivable, so it is taken FROM the
    record and then used to recompute both, which is what makes taking it
    safe. Absence answers `None`; a disagreement REFUSES rather than falling
    back, because falling back would fence under a second identity over a
    generation that may already be ended.
  * **The fence** uses the adopted record's identity as before, and when that
    identity is the cancellation's it uses the cancellation's REASON too — the
    Authority signs a cancel over `{expect, reason}`, so replaying with the
    abandonment's own reason would be a different act at the same identity.
  * **The declaration stays separate.** The abandonment's reason is what the
    intent records and what every later reader sees. Only the fence borrows.
  * **Old intents replay untouched.** `_abandon_fence_operation_id`'s
    derivation is unchanged, and `_abandon_intent` signs and validates the
    identity it is given, so an intent committed before this change replays
    against exactly the string it recorded. No journal is rewritten.
  * **The supersession is dated and bounded**, in
    `_abandon_fence_operation_id`'s own docstring: the restriction stands for
    an attempt that was never cancelled, and is narrowed — never erased — for
    one that was. An abandonment still never ISSUES a cancellation and never
    infers a fence from an intent.

**Declared first and cancelled afterwards is closed by the journal's own
rule**, one layer up: the committed declaration names the abandonment's fence,
the next call composes the cancellation's, and the same `attempt.abandon:` id
signed over different operands refuses at §4.2 before anything external is
touched. I wrote a second check for this, measured that it was unreachable, and
removed it rather than leave code asserting what the store guarantees.

## Evidence — 26 focused cases, all passing

`test_abandonment.py` (19) and `test_routed_abandonment.py` (7), clean under
`-W error::ResourceWarning`. New this claim:

  * **positive prior-fence recovery** — cancel, then abandon: the intent
    carries the abandonment's reason AND the cancellation's Authority
    identity, the cleanup settles `retained` with `state: absent`, the
    abandoned gate is discharged, and a repeat replays with no duplicate
    effects;
  * **the preserved run's shape now has exactly one door** — the ordinary
    ending still answers blocked-on-intake and the deadline owner still
    refuses on the null policy, and the abandonment recovers it;
  * **a cancellation after the declaration** refuses at §4.2 with nothing
    external touched;
  * **a tampered cancellation record** refuses fail-closed, world unchanged;
  * **a discharge committed remotely with the local receipt lost** — the
    journal write fails after the Authority acted, and the retry replays the
    remote answer and commits the receipt without removing anything again.
    This is the case the severed-call one deliberately could not model.

Accepted suites over the changed file: `tests.manager.test_abandoned_attempt_engine`,
`test_intake`, `test_attempts`, `test_refused_session_cleanup`,
`test_failed_start_destroy` — **691 tests, OK, 9.308s**.
`tests.manager.test_runtime_deadlines` + `tests.tools.test_single_worker` —
**208 tests, OK, 10.337s**. Ordinary cancellation, ordinary success and the
standalone abandonment are unchanged.

## REMAINING

  1. the routed positive prior-fence case (this claim proved it unpooled);
  2. first-call crash and launch-absent alternate recovery; the unpooled
     altered-context gap, which cannot close the way the routed one did
     because no allocation exists there;
  3. the supervisor's explicit shutdown declaration;
  4. the two operator grants documents with validation and readback;
  5. the executed-image fault diagnosis;
  6. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the pinned snapshot are read-only and were read read-only. Recovery of the
preserved run is PREPARED, not performed.

## Ownership

See `OWNERSHIP-255823.md`. baton.claude holds `tools/single_worker.py`,
`tools/stage_execution.py` and, from owner 255814,
`src/baton_v12/worker_manager/intake.py`. `attempts.py`, `deadlines.py` and
`authority/` were NOT edited.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255823

### Correction A is in, and the P1 closes positively

The abandonment now fences a cancelled attempt by replaying the cancellation's
own Authority operation, with that operation's own reason and this attempt's
exact fixed assignment, acting only on the Authority's validated answer. The
declaration and its reason stay the abandonment's own record; only the fence
borrows an identity, because the Authority signs a cancel over
`{expect, reason}` and anything else collides rather than replays.

The evidence the replay rests on is held to exactly what
`unstarted_cancellation_of` holds its own copy to — derived identity, committed
state, decoded document recomposed from this attempt's operands, canonical
signature recomputed. A record that disagrees refuses; it is not ignored,
because ignoring it would fence under a second identity over a generation that
may already be ended.

I did not touch `attempts.py`, `deadlines.py` or `authority/`, and I added no
new shared reader anywhere. The supersession is dated and bounded in
`_abandon_fence_operation_id`'s own docstring rather than deleted.

### Two things the tests taught me rather than confirmed

**My named refusal for "declared first, cancelled afterwards" was unreachable.**
The journal gets there first: the committed declaration names one fence, the
next call composes another, and §4.2 refuses the same id over different
operands before anything external is touched. I removed my branch — code that
asserts what the store already guarantees is worse than no code — and the case
now asserts the store's own refusal.

**The lost-receipt case is real and it passes.** Failing the local journal write
for the discharge kind leaves the Authority's act committed and no receipt; the
retry replays the remote answer and commits it, removing nothing again. That is
the distinction you drew two reviews ago, now modelled properly rather than
labelled honestly.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 26 cases, all passing,
**1.536s**, clean under `-W error::ResourceWarning`; intermediates this claim
0.904s, 0.937s, 1.118s, 1.424s.
`tests.manager.test_abandoned_attempt_engine`, `test_intake`, `test_attempts`,
`test_refused_session_cleanup`, `test_failed_start_destroy` — **691 tests, OK,
9.308s**. `tests.manager.test_runtime_deadlines` +
`tests.tools.test_single_worker` — **208 tests, OK, 10.337s**.

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
159.910s plus its untimed repeat, 0.966s, 1.170s, 10.041s, 9.966s, 0.348s,
0.130s, the combined 1.090s and 1.334s, the focused
0.632/0.701/0.371/0.772/0.800/0.803/0.917/1.364/1.378/0.480s runs, the earlier
focused and product-suite times, the untimed probes and diagnostic reads, the
unmeasured ~120s command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**.

State: returned INCOMPLETE through baton.bug with Correction A implemented and
proved, and the non-abandonment packet still open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255823" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
