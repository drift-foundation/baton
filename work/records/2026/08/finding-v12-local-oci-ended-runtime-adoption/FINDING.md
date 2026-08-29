# Finding: adopt exact ended OCI runtime before lane reuse

Later-pass M2 restart hardening split from W6636 by the 2026-08-28 approver
scheduling ruling. Canonical predecessor evidence:
`work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`.

## Confirmed boundary

W6636 already proves a second manager incarnation adopts one exact running
runtime and refuses mismatch or multiplicity. This Work owns the missing ended
case: after restart, an exact container that is exited but still present is
not absence and cannot release the lane.

The manager must identify the exact attempt/runtime, force-remove it, observe
positive absence through the adapter, settle applicable credential and launch
roots, and only then permit lane reuse or replacement. Uncertain observation,
identity mismatch, and more than one candidate fail closed without deleting a
sibling attempt's runtime or roots.

## Acceptance

- A real Docker restart opens a second manager incarnation over the same
  durable store and discovers the exact ended container.
- Exited-but-present does not satisfy cleanup or reuse.
- Exact force-removal, provider teardown and observed absence precede reuse.
- Mismatch, multiplicity and observation uncertainty preserve the retry
  obligation and unrelated attempts.
- Independent review signs off this restart slice without claiming Podman or
  the separate negative/race matrix.

## Independent review — 2026-08-28

**Confirmed partial:** the new real-engine module composes an ordinary exited
container, reopens the same durable store under a second manager incarnation,
and asks reconciliation for the exact runtime. It also retains explicit engine
and delivery-root assertions around cleanup.

**Changes requested:** the module never attempts lane reuse after cleanup,
asserts only final state rather than the required removal/absence/provider
ordering, and constructs no unrelated sibling attempt in the ended-restart
negative. The implementer may cite earlier unit/running-runtime cases as
supporting evidence, but those do not satisfy this follow-up's exact restart
acceptance. See `review-2026-08-28T16-04-24Z.md` and
`evidence/w32385-acceptance-shape.py`.

## Correction re-review — 2026-08-28

**Accepted:** the revised positive case traces exact force-removal, post-remove
observation, credential teardown and launch teardown in order, retains a
sibling credential root, and starts a real successor manager attempt only
after cleanup. These close the prior ordering, provider-root bound, and bounded
manager-attempt reuse findings.

**Still open:** the case creates no sibling runtime or attempt row and has no
ended-restart mismatch or multiple-candidate method. This is an explicit
acceptance member, not optional context. See
`review-2026-08-28T16-16-50Z.md` and
`evidence/w32385-re-review-shape.py`.

## 2026-08-28 — supersession: the unreachable mismatch, and what replaces it

The acceptance's "identity mismatch" was written as a reconciliation answer.
At THIS seam that is unreachable, and the reason is a property of the design
rather than a gap: `_attach` is effectively-once on
`attempt.attach:{attempt}:{runtime}`, so an ended-restart reconciliation of an
attempt that already attached replays the first incarnation's document and the
compare-and-swap never runs. A state where the attempt row names one runtime
and the engine holds another is one no sequence of manager operations produces
— constructing it means editing the row behind the manager, which tests the
edit.

**What replaces it, exactly.** The reachable identity disagreement at this
crossing is the ADAPTER answering the destroy about a different runtime, which
`intake._destroyed` compares and refuses `runtime-observation/identity-
mismatch`. That is proved by
`test_a_destroy_answer_about_another_runtime_is_refused` on a real ended
runtime, and the attempt's cleanup stays `pending`. The attach-time mismatch
rule keeps its own evidence at `_attach`'s boundary in `test_attempts`.

Multiplicity is NOT superseded and is proved here directly:
`test_two_ended_restart_candidates_cancel_without_removing_either` starts a
second real container carrying the assignment's labels, restarts the manager,
and requires the reconciliation to cancel and remove NEITHER.

## Final independent signoff — 2026-08-28

The exact ended-runtime restart slice satisfies its bounded acceptance. The
positive crossing now proves adoption, non-reuse while present, ordered exact
removal/absence/provider settlement, sibling root/runtime preservation and a
post-cleanup successor. Multiplicity and uncertainty fail closed, and the
explicit mismatch supersession is backed by a reachable destroy-answer
identity disagreement. See `review-2026-08-28T16-29-52Z.md`.

This signoff retains the environment boundary: required Docker execution is
implementer evidence because the managed reviewer cannot access the daemon;
Podman and W32382's separate negative/race matrix are not claimed.
