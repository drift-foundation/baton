# Plan

1. Revalidate the reference-image entrypoint contract and current manager/adapter launch request.
2. Pin the superseding versioned launch-document contract at the fixed
   read-only `/run/baton/launch.json` path; retain no multi-variable or
   environment fallback.
3. Implement manager authorship, strict document validation, read-only OCI
   mounting, and worker ingestion while keeping credentials and assignment
   input on their separate mounts.
4. Replace the diagnostic expected failure with positive unit and real-Docker
   regressions, including missing, malformed, unknown-field, wrong-version,
   mutable/non-regular, secret-bearing, and legacy-environment-only refusals.
5. Run focused and full v12 verification, then request independent review.

## 2026-08-27 — implementation

- [done] 1. Both ends revalidated: the worker's four values for both postures,
  and the frozen `runtimeStartBody` confirmed to carry no environment member,
  so this is a manager/adapter seam rather than protocol state.
- [done] 2. A typed three-value seam, with `BATON_WORKER_POSTURE` derived from
  the adapter that already owns `posture` — one fact, one owner.
- [done] 3. Manager carries, adapter validates and translates. No arbitrary
  pass-through.
- [done] 4. The expected-failure case replaced by a positive real-Docker
  regression proving exit 0, plus negative secret and malformed-value cases and
  a case holding the adapter's set against the worker's own literal.
- [done] 5. Focused and full v12 verification; returned for independent review.

### For review

- [flagged] Where the three caller-supplied values come from in manager state is
  not decided here — the finding's boundary keeps the sourcing outside this
  Work, and `request_runtime_start` carries them as an operand.

## 2026-08-27 — independent review changes requested

The implementation status above describes the superseded environment design
and is not completion of live plan items 2–5.

- [required] Remove the new arbitrary `environment` operand and all
  `BATON_WORKER_*` `--env` transport and fallback tests; the superseding
  decision explicitly retains no compatibility path.
- [required] Pin the exact launch-document schema/version constant and bounds,
  then implement manager authorship of a complete UTF-8 JSON document carrying
  only `schema`, `posture`, `session`, `contract`, and `role`.
- [required] Materialize the document as a manager-owned regular read-only file
  and have the OCI adapter mount exactly that file read-only at the fixed
  `/run/baton/launch.json` target, with no caller-selected locator or arbitrary
  mount/environment channel.
- [required] Change the reference worker to open the fixed path without
  following links, bound the read, prove the opened descriptor regular and
  immutable for its view, and strictly validate version, complete field set,
  types, and unknown fields before agent execution. Legacy environment-only
  launch must refuse.
- [required] Replace unit, mutation, and real-engine evidence with coverage of
  the live document contract, including missing, malformed, unknown-field,
  wrong-version, mutable/non-regular, secret-bearing, and environment-only
  refusals plus a positive reference-worker launch.
- [evidence] Keep the retired environment evidence as historical, but append a
  clearly labelled supersession rather than presenting its nine mutations or
  1578-test run as the current gate. W26296 now owns the stale
  `check_input_pair` inventory failure named there.
- [cleanup] Remove the duplicate scratch mutation harness
  `w26291_mutation.py` from the record root after preserving any unique
  evidence under `evidence/`; the two current scripts are byte-for-byte the
  same retired measurement.

## 2026-08-27 — required consent-posture supersession

- [required] Remove the consent `posture` axis from the fixed launch document.
  The exact members are `schema`, `session`, `contract`, and `role`.
- [required] Preserve the fixed read-only `/run/baton/launch.json` transport,
  strict validation, and refusal of all legacy environment fallbacks.
- [required] Keep credentials and read-only `/input` outside this control
  document; the latter may expose the exact operator-dispatched Work source.
- [required] Re-run focused and real-Docker evidence before review. Neither the
  first environment implementation nor a five-member launch document satisfies
  the current ruling.

## 2026-08-28 — the live contract, implemented

Plan items 2–5 were not completed by the superseded environment
implementation; the review said so and was right. This is the live boundary,
end to end.

- [done] 2. The contract PINNED FIRST, in `FINDING.md` under "Pinned
  launch-document contract — 2026-08-28": the fixed path, the
  `baton.worker-launch/1` schema constant, the exactly-four member set, the
  per-value and whole-document bounds, and the closed list of what is refused.
  A clarification the two supersessions force is recorded there as a decision
  rather than made silently — see below.
- [done] 2. Manager authorship. `worker_manager/launch.py` owns the constants,
  authors the complete four-member document over `LAUNCH_MEMBERS` rather than
  copying a caller's mapping, bounds every value and the encoded bytes, walks
  the result under §13, and materializes it.
- [done] 3. One manager-owned regular read-only file, 0444 under a 0555
  attempt-private root this module creates outright. The mode is deliberate at
  both ends: the container runs as a fixed non-root uid and a bind carries the
  host mode through, so an owner-only document would be one no worker could
  read — which is only acceptable because §13 keeps this document non-secret,
  and that is driven rather than asserted.
- [done] 3. The OCI adapter mounts exactly that file READ-ONLY at the fixed
  `/run/baton/launch.json`. The typed capability is held at construction, like
  the credential delivery and for the same reasons; the PAIR it answers with
  reaches `run_vector`, exactly as a credential delivery's pairs do. The
  `environment` operand, `WORKER_ENVIRONMENT`, `LAUNCH_VALUES`,
  `_launch_environment` and every `--env` are GONE rather than deprecated.
- [done] 4. The worker opens the fixed path no-follow and nonblocking, proves
  the descriptor regular, bounds the read at the ceiling plus one byte, proves
  the file is not writable for its own view, and validates the closed member
  set, the schema by equality, and every value's type and bound before any
  agent execution. `serve` has no environment operand at all, so there is
  nothing a fallback could be threaded back through.
- [done] 5. Coverage of the live contract: `tests/manager/test_launch.py`
  (25 cases), `TheLaunchDocumentIsAMountAndNotAChannel` in `test_oci`,
  `TheLaunchReadIsBoundedNoFollowAndProved` and the rewritten latch/entitlement
  classes in `test_worker_image`, and eleven real-container cases in
  `test_worker_container` covering missing, malformed, unknown-field,
  wrong-version, non-regular, writable, oversize, no-session and
  ENVIRONMENT-ONLY refusals plus a positive launch.
- [done] 5. `evidence/w26291-launch-document-mutations.py` replaces the retired
  harness, which is KEPT beside it as history. Nineteen mutations across both
  trees, measured against the real-engine suite as well as the in-process ones.
- [done] Registries. `test_dependencies`'s operand table gains
  `session`/`contract`/`role`/`launch_delivered` and LOSES `environment`;
  `test_boundary_inventory` gains the launch module's owners, delegates and
  probes, so this Work adds nothing to the accepted failure set.

### The clarification, and it is a decision rather than an omission

- [decided, recorded in FINDING.md] Removing `posture` from the document
  removes the reference worker's only source for it, so the worker-entry
  program no longer asks what kind of container it is: `POSTURES`,
  `posture_of`, the posture-keyed environment set and the posture-keyed
  operation set are gone. `describe`'s answer loses `posture` and
  `environment` and gains `launch`. `consider` is KEPT as a known operation
  this runtime is not entitled to, because deleting an operation from a ruled
  protocol is a larger decision than this Work holds — and keeping it is what
  makes the entitlement refusal mean anything.
- [open, needs an owner] Whether the rest of the consent vocabulary should
  leave `baton.worker-entry/1` now that no consent runtime exists.

### Existing expectations replaced, and why each one had to be

The review required replacing the retired evidence, and these are the cases
whose SUBJECT no longer exists rather than whose assertion was inconvenient:

- `test_a_consent_container_answers_describe_and_consider`,
  `test_a_real_consent_container_is_not_asked_to_work`,
  `test_a_real_consent_container_mounts_neither_input_document`,
  `test_a_real_container_refuses_the_other_postures_session`,
  `test_a_container_built_with_the_wrong_posture_latches_and_exits`,
  `test_a_consent_container_carrying_assignment_material_latches`
  (`test_worker_container`);
- `ConsentCannotReachExecution` entire, `test_consent_reads_neither_input_
  document`, `test_an_invalid_posture_is_one_correlated_fault_and_a_non_zero_
  exit`, `test_a_container_built_with_the_wrong_material_latches_too`,
  `test_consent_accepts_and_declines_deterministically`,
  `test_a_consent_answer_names_nothing_it_cannot_see`,
  `test_the_two_postures_are_the_whole_set`
  (`test_worker_image`);
- `TheLaunchEnvironmentIsFourValuesAndNoChannel` entire (`test_oci`).

Each replacement asserts the property the original was protecting, on the
subject the ruling left in place. The mapping is in `PROGRESS.md`.

## 2026-08-28 — independent re-review changes requested

- [required] Establish exact worker-readable `0444` launch-file mode
  independently of ambient process umask and add a restrictive-umask
  regression plus positive composition coverage.
- [required] Make a materialized launch delivery mandatory at the canonical
  reference-worker OCI construction/start seam; missing-document worker
  refusal remains defense, not a legal manager launch configuration.
- [required] End the manager-owned launch root after a refused start or proved
  runtime absence, while preserving uncertainty when absence is not proved.
- [required] Reconcile `describe.launch` with the pinned four-member document
  wording, either in code/tests or through an explicit approved supersession.
- [cleanup] Correct the stale `0400`/`0500` module text and duplicate test
  method definitions identified in the newest review journal.
- [pending] Re-run focused, mutation, full-tree, serial, and real-engine gates,
  then return for independent review.

## 2026-08-28 — re-review corrections applied

- [done] [P0] The mode is established rather than requested. The file is
  created at 0000 and `fchmod`ed to `READ_ONLY_FILE` on the descriptor that
  wrote it, after the last byte — exact under any umask, with no writable
  interval and no readable partial document. Two regressions: one sets and
  restores umasks 077/027/022/000, one proves the file is mode 0000 at every
  write.
- [done] [P1] The canonical start REQUIRES a materialized launch document and
  refuses before the engine is asked anything. Optional at construction,
  because the adapter's runtime half is constructible without one.
- [done] [P1] The launch root has one ending, taken only on the evidence that
  no runtime can hold its mount, reported beside the credential ending rather
  than folded into it. Regressions cover a refused start, an engine that
  cannot answer, a destroyed runtime, and a runtime not proved gone.
- [done] [P1] `describe.launch` reports all four pinned member names. The
  implementation's three-member preference lost to the recorded decision.
- [done] [P2] The module contract says 0444/0555; the duplicated block of five
  test definitions in `test_lifecycle_composition` is removed, and the file
  now has no duplicate method name in any class.
- [done] Fixtures. Every canonical start in `test_oci`, `test_credentials`,
  `test_oci_engine`, `test_credentials_engine`, `test_lifecycle_composition`
  and the boundary-inventory witness now carries a materialized delivery; the
  lifecycle and engine fixtures mint one PER ADAPTER, because a settled
  delivery is discarded and a second adapter must not be handed a document the
  first tore down.
- [done] Gates: `test_oci` 99, `test_launch` 22, `test_credentials` 80,
  `test_worker_image` 103, parallel 1555 with the accepted six
  `test_boundary_inventory` failures, serial 105/0 including
  `test_lifecycle_composition` 26 and `test_worker_container` 50 on a real
  daemon.

## 2026-08-28 — second re-review changes requested

- [required] Settle a same-attempt credential delivery when canonical start
  refuses because the launch document is missing; preserve uncertainty rather
  than inferring absence if the engine cannot answer, and do not settle a
  mismatched attempt.
- [required] Add combined missing-launch/credential regressions for proved
  absence and uncertain listing. The current missing-launch case carries no
  credential and therefore cannot observe this lifecycle regression.
- [verified] Focused four-suite reviewer gate: 304 green; targeted diff check:
  clean. The durable reproduction reports `engine_calls=0`,
  `credential_root_present=True`, and `bearer_live=True`; see
  `review-2026-08-28T08-33-46Z.md`.

## 2026-08-28 — second re-review correction applied

- [done] [P1] The missing-launch refusal goes through `_refused_start` rather
  than calling `_denied` directly, so a canonical adapter already holding a
  credential delivery has it settled instead of stranded. My comment beside
  that check said "nothing has been created yet"; that was true only when no
  other provider had materialized anything, which is the assumption the
  reproduction broke.
- [done] It sits AFTER both attempt checks. `_refused_start` settles by asking
  which runtimes carry THESE labels, so a mismatched attempt must refuse above
  it — an empty answer about attempt 2 says nothing about attempt 1's runtime.
- [done] Three combined regressions, each measured against the pre-fix
  placement before being trusted: same-attempt credential torn down and bearer
  forgotten; a surviving runtime leaving both unresolved with the root intact;
  and a mismatched attempt refused with no engine call at all and the
  credential untouched. All three fail against the old placement.
- [done] The harness gained the settlement-bypass mutation AND
  `tests.manager.test_credentials` in its module list — the first run reported
  that mutation UNSEEN because the cases covering it were in a suite the
  harness did not run, and a mutation nothing runs is not measured. It also
  re-anchored the older missing-document mutation, which the harness reported
  as a stale 0x anchor rather than mutating something else. **25 of 25.**
- [done] Gates: focused 307, parallel 1563 with the accepted six
  `test_boundary_inventory` failures, serial 105/0 on a real daemon.

## 2026-08-28 — third independent review changes requested

- [verified] The production correction settles the same-attempt credential on
  proved absence; the durable reproduction now reports one inventory query,
  no credential root, and no live bearer. Focused four-suite gate: 307 green.
- [required] Add the requested combined missing-launch/credential regression
  for an inventory listing that itself cannot answer. The added surviving-
  runtime case covers a successful listing with a row, which is a distinct
  uncertainty path. Assert that failed/untrustworthy listing leaves both
  present providers unresolved and preserves the credential root and live
  registration. Keep the surviving-runtime and mismatch cases.
- [review] See `review-2026-08-28T09-16-54Z.md`.

## 2026-08-28 — third review [P2] applied

- [done] The combined missing-launch case where the LISTING ITSELF is
  unusable, in three spellings: the engine refuses it, it is not readable
  JSON, and it names no runtime this manager can own. Each asserts the start
  refuses, the credential ending is `unresolved`, the root remains and the
  bearer stays live — an inventory this manager could not read is never
  proved absence.
- [done] The surviving-runtime case is KEPT beside it. It covers a successful
  listing with a row, which is the adapter inferring possible use; this is the
  adapter knowing nothing at all. Two branches, two cases.
- [done] Measured: with `why = refusal.message` changed to `why = None`, so an
  unusable listing becomes proved absence, the new case fails in all three
  spellings. The harness gained that exact mutation, which the existing
  `if not proved_absent` one does not reach.

## 2026-08-28 — final independent review

- [signed off] The failed/untrustworthy inventory branch now has the direct
  combined missing-launch/credential regression requested by the prior pass,
  in three spellings, and the exact mutation that would turn uncertainty into
  false absence is caught.
- [verified] Durable lifecycle reproduction passes; focused four-suite gate is
  308 green; targeted diff hygiene is clean. See
  `review-2026-08-28T09-41-31Z.md`.
