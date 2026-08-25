# Plan: manager output freeze and artifact receiver

1. [done 2026-08-24] Create this dossier and revalidate the frozen
   worker-control output contracts and the closed W4 record. Recorded in
   `FINDING.md`: `missing-optional` is a reported status rather than an
   absence; `frozen` and `sealed` are distinct with `invalid` reachable from
   `frozen`; and W4 already owns the output axis, its transitions and the
   journalled effectively-once observations this receiver hangs off.
2. [blocked on W6592] The freeze handoff: prove quiescence, then move
   `open -> freeze-requested -> frozen` through W4's journal, on W6592's public
   boundary rather than beside it.
3. [blocked on item 2] The artifact receiver: the manager RECOMPUTES the
   declared regular-file manifest, count, bytes and digest rather than adopting
   the collector's account, and records `missing-optional` as the answer it is.
4. [blocked on item 3] Immutable staging identity, so a retry names the same
   material, and effectively-once acceptance through the existing journal.
5. [blocked on item 4] Caller-local refusals, with engine and adapter status
   carrying no authority meaning at any point.
6. [blocked on item 5] Tests, evidence and independent review.

## Implementation — 2026-08-25

Status: **implemented and verified; awaiting independent review.** W6592 closed
satisfying, so items 2–6 were unblocked and are done.

2. [done] The freeze handoff. Four preconditions read from durable state, the
   liveness read inside the write and still only a read, and
   `open -> freeze-requested -> frozen` through W4's journal. Only a positive
   `quiescent` observation permits it: `uncertain` is a failure to look and
   `destroyed` is a writer never observed to have finished.
3. [done] The artifact receiver. The contracts composite recomputes the
   manifest's aggregates and tree digest, the manager stores the RECOMPUTED
   identity rather than the declared one, and `missing-optional` is recorded
   as the answer it is. `manifests.py` retains the documents a declaration is
   finally comparable against — a digest is not a record.
4. [done] The record operation is fixed per attempt and per assignment, so the
   same result replays and changed bytes under that identity refuse. Replay
   asks nothing about today, which a case drives by moving the axis and
   deleting the declaration before retrying.
5. [done] Caller-local refusals throughout. What an adapter ASSERTS about its
   own success decides nothing: its answer is validated as a sealed result
   where it arrives, and a witness case drives a confidently-wrong adapter.
6. [done] Tests and evidence: `tests/manager/test_output.py`, 55 cases; the
   boundary inventory, text sweep and declared-operand gates extended;
   `evidence/gate-after-2026-08-25.txt` bounds what this slice changed.
7. [done 2026-08-25] Independent review recorded in
   `review-2026-08-25T06-08-36Z.md`: changes requested on one P1 atomicity
   defect. A newer non-quiescent runtime observation can land after the
   optimistic row read and before the freeze write, yet the stale row still
   authorizes `freeze-requested`.
8. [done 2026-08-25] Re-read and decide positive quiescence inside the
   `output.freeze` journal transaction before moving the output axis. The
   deterministic regression proves the newer observation wins, the adapter is
   not called, and output remains `open`.
9. [done 2026-08-25] Final independent review signed off in
   `review-2026-08-25T06-41-52Z.md`. Focused output suite: 58/58; combined
   output/attempt/store suite: 158/158.

## Boundaries this slice did not cross

The `sealed` transition is NOT written here. `invalid` is reachable from
`frozen`, so material can be frozen and then found invalid; sealing is W6634's,
and collapsing the two would have removed the state that expresses it.

## Review correction — 2026-08-25

Status: **corrected, verified, and signed off.**

1. [done] [P1]: the decisive quiescence check is a row re-read INSIDE the
   `output.freeze` transaction, before the output transition. The outside
   check is retained as an optimistic early refusal and no longer authorizes
   the write; both call one helper, so the two answers cannot drift.
2. [done] The reviewer's regression is green, with two more beside it: that a
   plainly unready attempt never reaches the journal, and the terminal-once
   property of `worker_disposition` that makes the inner disposition half
   inert — pinned so the gate speaks if it ever stops holding.
3. [done] `test_output` is 58/58; the full suite carries only the twelve
   pre-existing failures plus W6630's in-flight review cases.
