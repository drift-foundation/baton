# Progress

Allocated by owner; no implementation started. Assigned implementer appends attributable progress after successful claim/authorized native admission.

## 2026-11-22 — Stage 1-B implemented (baton.claude, impl)

Awaiting independent review. Stage 1-B is complete: the installed
`manager recovery-item` / `manager recovery-decide` verbs, the owner decision
and the manager-owned linked verification/review-only successor admission, the
review-only evidence rules, and 57 focused acceptance cases driving the REAL
command over disposable stores through production Authority authorization and
manager admission/readback.

- Outcome this turn: product, command, contract and acceptance delivered at
  source `ce6e1b2b`; `tests.job_manager.test_retained_recovery_admission`
  passes 57/57; `authority` group 511/511 OK; `job_manager` group 1836/1925
  with every remaining failure measured as pre-existing/environmental.
- One defect found and corrected rather than worked around:
  `job_control.advance_watermark`'s read-then-write of `control.watermark`
  faulted under two concurrent decisions. Recorded in FINDING with its
  observation, cause and correction.
- One additive Authority read added: `authorize_capability`, because REC-8
  requires binding owner identity/provenance and `holds_capability`'s boolean
  cannot be recorded beside an act.
- Not delivered and not claimed: Stage 1-C (W385625) verifier execution, the
  retained-review handoff and the joined loop. The admission answer's
  `readiness` member names those acts as owed.
- Test paths changed and their reasons are in PLAN; two existing expectations
  moved, both additive to exhaustive registries.
- Pending: owner Git checkpoint for this slice, carried in PLAN.

## 2026-11-22 — baton.codxpc E385713 review correction

Corrected isolated exact5bc260b6 under M385710: F1 actual projection/sweep hold plus scheduler admission defense, with decision/candidate/lineage visible; F2 recovery profile limited to exact successor submission, ordinary submit/create/fresh-attempt refused; F3 shipped default owners factory over bootstrapped disposable instance. Only existing test_retained_recovery_admission.py changed:11 additive tests and two owed-to-blocked expectation corrections, preserving earlier identity/authorization/replay/cancellation/lineage guarantees. Final149/149 in7.468s and615/615 in21.430s, zero failures/errors/skips; source-identity archive limitation resolved using isolated Git metadata. Intermediate test-only errors/expectations fixed, logs retained in author evidence. Stage1-C handoff remains unavailable and non-runnable; no implementation/verifier/provider or native Job rerun. Candidate returned for independent review, not accepted.
