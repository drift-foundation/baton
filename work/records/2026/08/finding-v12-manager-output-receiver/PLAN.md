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
