# Exact OCI runtime observation during reconciliation

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`

## Finding

**Observed:** `reconcile_runtime` in `v12/python/src/baton_v12/worker_manager/attempts.py` currently treats any matching result from `docker ps --all` as a running worker and does not ask the adapter to observe the matched container's exact runtime state.

**Confirmed:** An exited, dead, or otherwise quiescent container can therefore be misclassified as running. W6636's approver authorized a separate correction Work for exact runtime observation.

**Confirmed boundary:** This Work owns the production observation seam: select by exact assignment identity, require unambiguous multiplicity, invoke `adapter.observe`, and expose running, quiescent, absent, or uncertain state to reconciliation. W6636 retains the broad restart/adoption matrix, shared settlement crossing, and orphan convergence policy.

**Proposed:** Fail closed on duplicate candidates, observation errors, identity mismatch, or unrecognized engine state. Do not infer running state from list membership.

## Acceptance

- Reconciliation lists by exact assignment identity and calls `adapter.observe` on the unique candidate.
- Running, quiescent/exited, absent, and uncertain states remain distinguishable through the manager seam.
- Duplicate containers, observation failures, and identity mismatches fail closed and never report running.
- Unit and real-engine regressions prove an exited container is not classified as running.
- The focused lifecycle diagnostic is converted to a positive production-seam proof.

## Open

- The exact public state type and division between adapter normalization and manager policy must be revalidated before implementation.

## Approved implementation boundary — 2026-08-27

Approve the proposed exact-runtime observation seam. Reconciliation must not
infer `running` from membership in an all-containers listing. It selects the
exact assignment identity, refuses ambiguous or mismatched candidates, asks
the adapter to observe the exact runtime, and preserves `running`,
`quiescent`, `absent`, and `uncertain` as distinct truthful answers.

This Work establishes observation, not policy. It does not automatically
retry, remove a runtime, discard output, release or reassign Work, or reinterpret
uncertainty as absence. W6636 retains those lifecycle consequences and must
act only on the explicit observed state under its pinned policy.

## 2026-08-28 independent review

**Confirmed P0:** Positive absence is unreachable in the ordinary real-engine
shape. `_observed` is called only when the all-containers listing still returns
one candidate. After removal that listing is empty, and `reconcile_runtime`
returns `uncertain` without asking `adapter.observe` about the exact immutable
`runtime_id` already recorded on the attempt. The submitted absence test uses
an artificial race in which listing still returns a candidate while observation
answers absent; it does not cover the normal post-removal path.

**Confirmed P0:** Observation failure does not become `uncertain`. A raised
adapter error, malformed document, missing member, or unknown state propagates
while leaving the durable axis at its previous value, including `running`.
The real-engine test named `test_an_observation_the_adapter_cannot_make_is_never_running`
asserts `not quiescent`, which admits exactly that stale `running` result and
contradicts its own stated invariant.

**Confirmed P1:** The Docker acceptance cases launch through W26291's
superseded `BATON_WORKER_*` environment seam. The live contract is the fixed
read-only `/run/baton/launch.json` document with `schema`, `session`,
`contract`, and `role`, and no environment fallback. W26294's observation seam
is topology-neutral, but its real-engine acceptance evidence must not depend on
the retired transport.

**Confirmed P2:** `runtime.attached` now requires `observed`, but the
same-runtime recovery return in `_attach` still constructs that document
without the required member. The branch appears unreachable under the current
immutable attachment and journal invariants; remove it or make it satisfy the
closed document contract rather than retaining a latent refusal.

## 2026-08-28 — the reviewed findings, corrected

**Confirmed corrected — an exact identity is a question this seam can always
ask.** `_observed` ran only inside the one-candidate branch, so the ordinary
post-removal shape — the container gone, `ps --all` therefore empty, the
attempt still holding the exact immutable runtime id — returned `uncertain`
without asking. Positive absence was unreachable in normal operation, which is
the opposite of what this Work's acceptance says it delivers. Reconciliation
now takes the exact identity from the durable attachment, or from `minted`
when nothing is attached yet, and observes it. Only a reconciliation that
names no runtime at all remains unable to ask.

**Confirmed corrected — every failed or unrecognised observation is a durable
`uncertain`.** `_observed`'s docstring already promised this and the code
raised instead, leaving the durable axis at whatever it said before —
including `running`. An observation that FAILED was therefore
indistinguishable from one that answered liveness, which is the same defect
this Work exists to remove, one level up.

**Confirmed decision — the attachment and the state are two different
answers.** A failed observation still ATTACHES when the listing proved which
runtime this is: `decision` is about the attachment and `observed` is about
the state, which is exactly what `runtime.attached` gaining `observed` was
for. The pair `attached` + `uncertain` is honest, and the durable axis is what
must never still say `running`.

**Confirmed decision — an inconclusive observation carries its reason.**
`runtime.attached` gains an OPTIONAL `why`, supplied only when the observation
was inconclusive. A state recorded with no reason is the confusion this Work
exists to make legible arriving in a different shape; a conclusive observation
has nothing to explain and carries none.

**Confirmed — the two boundary owners whose refusal is now absorbed.**
`adapter.observe.state` and `adapter.observe.why` still run and still decide;
their refusal becomes a durable `uncertain` rather than propagating. They are
registered in the inventory's `NO_PROBE` with that reason, because a probe
asserting the refusal ESCAPES would be asserting the defect the correction
removed. The rule is covered where the behaviour is: `test_attempts` requires
the durable state AND the exact reason.

**Confirmed resolved by W26291 — the retired launch transport.** The real-
engine evidence no longer uses `BATON_WORKER_*`; the only mentions left in the
lifecycle suite are the supersession's own prose and an assertion that no such
value reaches the argv.

## 2026-08-28 — independent re-review

**Confirmed P1:** `_settled` refreshes only `observed` on the document replayed
by effectively-once `_attach`. It does not rebuild the optional `why` from the
current observation. A later `running` to `uncertain` transition therefore
omits the current reason, while an `uncertain` to `running` transition retains
the original failure reason. Exact output and the durable two-pass reproduction
are in `review-2026-08-28T10-09-59Z.md` and
`evidence/w26294-review-replay-reproduction.py`.

## 2026-08-28 — the re-review's [P1], corrected

**Confirmed corrected — the outward answer is REBUILT, never merged.**
`_settled` returned `{**attached, "observed": value}`. `_attach` is
effectively-once, so every reconciliation after the first REPLAYS the first
pass's document — and refreshing one member of a replay leaves the rest as old
as the attachment. Both directions were wrong, in opposite ways: a first
`running` followed by a failed observation answered `observed=uncertain` with
no reason at all, and a first failed observation followed by a `running` one
answered `observed=running` while still carrying the prose of the failure that
could not see it.

A partial refresh is worse than no refresh, because the members that moved and
the members that did not are indistinguishable to a reader. So the document is
now composed from the two things true at the moment it is answered: the STABLE
attachment identity, which is what `_attach` exists to fix and the one thing a
replay is authoritative about, and THIS pass's observation. Nothing is carried
across.

**Confirmed decision — `inconclusive` is decided from the value that is
answered.** The rule "the reason rides exactly when the observation was
inconclusive" was previously spelled `state == "uncertain"` at the one place it
was used. It is now read once from `value`, which is both what the durable axis
records and what the document publishes as `observed` — so the document is
consistent with ITSELF rather than with a variable a reader has to go and
check. `OBSERVED_RUNTIME` maps `uncertain` to itself and nothing else to it, so
the two spellings agree by construction.

**Confirmed boundary — a cancellation passes straight through.** `_attach` can
answer a mismatch instead of an attachment, and that document answers a
different question: there is no observation of this attempt's runtime to state
in it. Rebuilding it as an attachment would have assembled a document its own
contract refuses, so the pass-through is explicit and measured.

**Confirmed gap the correction itself opened, and closed.** Making the answer
independent of the stored attachment also left NOTHING checking the stored
one. It surfaced as a mutation that stopped being caught — dropping `why` from
the `_attach` call changed no answer any case looked at. The journalled
document is what an exact retry replays and what an operator reads out of the
operation log, so a case now asserts it directly. Worth pinning because the
signal was the measurement going quiet, not a test going red.
