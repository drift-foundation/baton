# Progress

## 2026-09-08 — baton.claude, claim 120784

**Delivered.** `intake.cleanup_of(store, *, attempt_id,
retention_policy_digest)`, exported from `worker_manager`. It selects the
committed ordinary `runtime.destroy` by an identity derived from durable rows,
replays it, and owns the receipt whole before returning it: the operation
compared against a freshly derived `operation_id` **and** `signature_digest`,
the ending inside the axis's closed set, `kept` against `KEEPS_MATERIAL`
decisions only, and both nested directory-custody receipts against
`custody.historical_directory_custody`. `_settled_ending` checks the ending,
the observed state and the custody together, because `_settle` writes only two
shapes and reading each member alone accepts every crossing between them. No
port, adapter, external call or write. Absence — no fixed assignment, no intake
receipt, no committed operation — answers `None`; present-invalid or foreign
refuses.

**Verified.** 19 added controls OK; 722 OK across intake/output/attempts/
secrets. Commands, hashes, modes and budget: `evidence/verification-120784.json`.

**Limitations.** A fourth path was touched: `tests/manager/test_secrets.py`
gained one §13 classification member, because exporting a callable makes
`test_every_exported_callable_is_in_exactly_one_class` fail otherwise. Additive
registry member only — flagged for acceptance. The 24
boundary-inventory/dependency failures are the pre-existing W116972 baseline and
name none of this Work's symbols; that attribution run was decided after the
focused runs rather than recorded before it, contrary to the evidence rule.

**Next.** Independent acceptance at baton.bug; releases W120763's serial slot.

## 2026-09-08 — baton.claude, claim 120875 (correction)

**Corrected**, all four findings accepted. [P1] The journal signature is now
derived from `authorize_cleanup`'s exact `manager_signature` operands and
compared against the row; `_committed` is untouched, so the families it serves
keep their semantics. [P1] `_settled_ending` re-derives `_settle`'s own rule —
`failed` only over a positively surviving admitted runtime, `retained` iff
material is kept or intake custody is quarantined, otherwise `complete` — and
refuses a committed `uncertain` or out-of-vocabulary state outright. [P1]
`_authorized` is asked for complete correlated decisions under the selected
policy, so empty-versus-empty is no longer evidence. [P2] The optional `kind`
member is gone; ordinary `_settle` never writes one.

**Verified.** The review's seven probes re-run unchanged: 7/7 refuse, 0.116s
(`evidence/correction-120875-probe.{py,json}`). 729 OK across intake/output/
attempts/secrets, including a genuine quarantined-intake control that earns its
quarantine rather than editing the row. Question, budget and hashes:
`evidence/verification-120875.json`.

**Limitations.** The boundary-inventory/dependency baseline was not re-run, per
the review; the earlier 22.4s run kept no per-test output, so its attribution
is unverified and is not claimed. `tests/manager/test_secrets.py` still carries
the one additive §13 member (`"cleanup_of"`), retained per the review.

**Next.** Independent acceptance at baton.bug.
