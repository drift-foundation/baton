# W384870 closure checklist — fixed continuation order

Owner steering: finish this Job; make K's next deliverable specific. This replaces
the open-ended continuation wording in M384931. Existing scope and acceptance remain.
K implements serially under owner claim E384905; no new Job or background agent.

## Next handoff: exactly the two isolated scans failures

1. `tests.manager.test_source_boundary.TheWorkspaceIsStorageAndScratchIsBounded.test_the_runtime_gets_exactly_the_declared_bounded_scratch`
   Observed: composed mounts include `/run/baton/logs:rw,noexec,nosuid,nodev,size=16m`,
   while the expected scratch list excludes it. Trace the accepted log-mount contract;
   correct the product or test at the actual mismatch. Preserve checks for exact
   mounts, size and security flags; do not simply omit the extra mount from comparison.
2. `tests.manager.test_text_sweep.EveryExportedOperationRefusesUnstorableText.test_the_table_names_every_exported_callable`
   Observed: twelve exported callables missing from the table. Enumerate them,
   provide the appropriate real refusal fixtures/cases, and demonstrate text rejection
   at their intended boundaries. Do not exempt names merely to make the table equal.

Deliver both bounded fixes, focused verification of the affected classes/behaviors,
source digests and a before/after result. If either reveals a concrete specification
conflict or a dependency outside this Work, report the exact operation and conflict;
continue the other independent item. Return at this checkpoint. Do not start replay
product edits, further generic discovery extensions, B4 or a full suite in this slice.
Existing inventory discovery is accepted for the delivered scope; alter it only for
a concrete reproduction required by a remaining failure, not speculative completeness.

## Then: finish the six remaining scans failures in this order

A. Duplicate owner attribution and runtime-lane coverage fixture:
- `tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_no_entry_is_owned_twice`
  (two port entries in discharge_quiescence_gate/discharge_abandoned_quiescence_gate).
- `tests.manager.test_boundary_inventory.LanesHaveCompleteReceivingCoverage.test_public_start_and_cleanup_supply_owned_lane_values`.

B. Owned-probe completeness and its negative self-test:
- `tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_every_owned_entry_has_exactly_one_probe`.
- `tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail`.
  Group the 33 non-replay gaps first, then the 206 replay gaps by owning helper.
  Use shared fixture construction where sound, but preserve per-boundary negative
  evidence and prove probes reach/detect their declared validator. Resolve the one
  unmatched probe through actual attribution. Do not bless debt as passing coverage.

C. Remaining ownership/classification:
- `tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared`.
- `tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_every_receiving_entry_has_an_owning_validator`.
  Classify failures by cause: discovery attribution, justified existing trusted
  boundary, or genuine missing validation. Name concrete behavior and evidence for
  each classification. The newly visible replay entries are not automatically
  product defects. No blanket exemptions or silent deferral; escalate only an actual
  specification/scope decision. Preserve the audit's differing count definitions.

Stages A/B/C are the subsequent order, not authorization to skip the next-handoff
checkpoint. Each repair batch must name which failing test it advances and report
remaining failures. A discovery change must have a direct remaining-failure rationale.
Run scans once after its repairs to establish zero failures, rather than after every
small edit. Current evidence: 460 collected, 450 passed, 2 optional skipped, 8 failed
structural test ids (9 failure events because one has two failing subtests).

## Final acceptance sequence

1. Complete B4 environment/Docker work and all required initial-access cases. Present
   exact operator commands where owner execution is needed, including prerequisites
   and expected result. These cases remain required.
2. Finish B5 singleton failures using focused tests; independently review repaired
   batches and the version-level command/docs interface.
3. Run the planned final full suite with pinned source identity and durable log.
   Acceptance: passed + allowed optional skips = collected; zero failed/errors,
   required skips, duplicate or unaccounted tests. Diagnose any remaining failures
   before another justified final run; never close based only on group results.
4. Independent final review, owner ledger closure, then owner check-in of all source,
   documentation and required evidence. W383215 starts only after both closure and
   complete check-in/readiness, as already selected.
