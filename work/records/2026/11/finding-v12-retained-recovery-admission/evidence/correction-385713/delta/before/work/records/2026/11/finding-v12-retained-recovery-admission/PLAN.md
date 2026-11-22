# Plan

1. Revalidate accepted contract and concrete source before assignment.
2. Establish native execution inputs and independent review; preserve serial shared-file ownership.
3. Implement only the named outcome with focused deterministic evidence.
4. Independently review exact candidate and retain evidence; owner performs Git checkpoint.
5. Read canonical dependencies before downstream admission.

Stage 1-B: supported owner read/decision surface binds exact failure, report, candidate, original/corrected verifier and context, approved profile identity/digest and selected stages. New linked manager-owned verification/review-only successor, never implementation redispatch. Prove authorization, replay/collision, cancellation, cessation, candidate integrity and exact stage/profile agreement. Post-verification expiry holds owner item; owner-authorized review-only successor requires valid exact evidence and unchanged approved limits. Depends on accepted Stage 1-A.

## Current state — 2026-11-22

**Delivered and awaiting independent review.** Implementation is complete
against the accepted contract; see FINDING "Stage 1-B delivered — 2026-11-22"
for the decisions it pins and the one defect it found. Evidence, digests and
measured durations: `evidence/native-stage-1b-385624/`.

### Next executable milestone

Independent native review of the exact candidate bytes at the paths below,
checking actual command/admission connectivity and the preserved Stage 1-A
guarantees. Nothing downstream is released by this record: W385625 (Stage 1-C)
owns the verifier execution and the final loop and is NOT delivered here.

### Pending owner Git checkpoint

This is a major accepted slice, so a human-owned Git checkpoint is due once
independent review accepts it (AGENTS "every major milestone requires a human
Git checkpoint"). Carried here until Slawomir fulfils it; no agent stages,
commits or publishes anything.

### Changed paths and file ownership

Product:

- `v12/python/src/baton_v12/job_manager/retained_recovery.py` (new) — the
  owner decision, the successor admission, the review-only evidence rules and
  the owner-facing read.
- `v12/python/tools/recovery_decision.py` (new) — the two installed verbs.
- `v12/python/tools/job_manager.py` — two dispatch lines and the help text.
- `v12/python/src/baton_v12/job_manager/job_control.py` — the approved
  `stage1-verification-review/1` control entry, its zero continuation
  allowance, and the atomic `advance_watermark` correction.
- `v12/python/src/baton_v12/job_manager/documents.py` — the
  `recovery.successor` answer contract and its emitter.
- `v12/python/src/baton_v12/job_manager/fresh_attempt.py` — three PUBLIC
  aliases (`CEASED_RUNTIME`, `SETTLED_CLEANUP`, `one_instance`) so the sibling
  admission reads that module's rules instead of copying them. No behaviour
  change.
- `v12/python/src/baton_v12/job_manager/__init__.py` — package exports.
- `v12/python/src/baton_v12/authority/api.py` — `authorize_capability`, the
  existing W16821 seam exposed as the document it answers with.
- `v12/python/tools/parallel_test.py` — the new test module's registry entry
  and the consumed profile-definition input.

### Test paths changed, and why (standing authority 2026-09-13)

- `v12/python/tests/job_manager/test_retained_recovery_admission.py` (new) —
  the focused acceptance entry this Work's criterion names. 57 cases.
- `v12/python/tests/job_manager/test_retained_failure_analysis.py` — ONE
  expectation moved: `test_the_implementation_jobs_own_control_profile_is_untouched`
  enumerated `job_control.PROFILES` exactly, and this slice adds a fourth
  owner-approved entry. The case's own subject is preserved and still checked
  — the ANALYSIS profile is absent from that table and no existing entry's
  numbers moved — and the new entry's five bounds are now asserted too, so the
  defect coverage (no silent widening of an admitted profile) is unchanged.
- `v12/python/tests/authority/test_boundary.py` — one ADDITIVE entry in the
  exhaustive public-face enumeration for `authorize_capability`, which is what
  that enumeration exists to force.

### Known environment limitation in this container

This container has no non-tmpfs storage outside the checkout (`/var/tmp` is
read-only, `/tmp` is a 32 MiB tmpfs, only `/output` is writable and it IS the
checkout), and `just`/the prepared interpreter are not installed. Every
`tests/tools/test_stack.py::_disk_root_outside_the_checkout` consumer therefore
fails in setUp before any product code runs. Measured identically at the base
commit; see `evidence/native-stage-1b-385624/REPORT.md` and `COUNTS.md` for
the exact pre-existing failure set and its proof. One consequence is recorded
rather than worked around: the `tools-pure` group cannot produce a meaningful
accounted verdict in this container, so it is reported INCOMPLETE and the
module its change bears on (`tests.tools.test_parallel_runner`, the execution
registry and declared consumed inputs) is verified completely instead. A
reviewer or integrator on a host with real storage outside the checkout should
run `just test-group tools-pure` and `just test-group job_manager` there.
