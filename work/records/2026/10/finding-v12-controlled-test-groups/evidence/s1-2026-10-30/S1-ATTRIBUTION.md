# S1 — attribution of demonstrated existing validation (owner M384898)

Author: K (interactive copilot under the owner-held claim E384883), 2026-10-30.
Edits: `v12/python/tests/manager/test_boundary_inventory.py` only (the
`DELEGATED` block marked "W384870 S1", two `STATED_OWNERS` entries, the
`w384870_probes` table and its registration in `all_probes`). No product edit.

## Method

1. The inventory's own delegation walk (`_delegations`) was run over every
   "caller" entry it reported unowned, and a candidate was kept only when the
   receiving private helper calls the `boundaries` layer on EXACTLY that
   operand with a literal label (`_owned_here(helper, "caller:<param>")`
   non-empty). Inline checks (`_hash`, `_component`, `type(x) is`) and
   forwarding do not qualify and were not credited. `documents._emit` was
   not credited (it owns member names, not values; review M384897).
   Candidates: `delegation-candidates.json`, reviewed with each public
   function's signature and first statements in
   `delegation-candidates-reviewed.txt` (126 candidates).
2. Every kept delegation has a probe in `w384870_probes` that drives the
   PUBLIC entry with that one operand spoiled (`SURROGATE`, a missing member,
   a non-text value) and requires the delegate's own label in the refusal
   (`refusing`). A probe that met an earlier precondition instead was not
   worked around by weakening: the delegation was withdrawn (listed below) or
   the probe composed the deployment fact the entry legitimately demands
   (configured workspace store, as the existing custody probes do).

## Delegations added (118 entries) and their probes

| public entry | operand(s) | delegate, label | probe |
|---|---|---|---|
| attempts.py: assignment_of, attempt_activity_of, attempt_runtime_of, attempt_start_failure_of, authorize_input_root, label_context, observe_activity, recorded_input_of, unstarted_cancellation_of | attempt_id | `_attempt_row`, "a runtime attempt id" | attempt_id=SURROGATE |
| exchange.py:command_document | session | `_value`, "an exchange document value" | session=SURROGATE |
| review_cycles.py: abandoned_correction_of, restore_abandoned_correction, review_for_attempt, settle_restoration_execution, writer_for_attempt | attempt_id, generation | `_requested_pair`, "a runtime attempt id" / "an assignment generation" | one of the pair spoiled |
| provider_context.py: admit_context_use (attempt_id, writer_id), authorize_qualification_run (job_id, storage_path), bind_context_invocation, context_of, correction_feedback_of, hold_context_use, prove_context_execution (attempt_id/context_id), qualification_deployment (authority_uuid) | identities | `_text`, "provider context identity" | the identity = SURROGATE, stores None (the owner runs first) |
| provider_context.py: certify_context_profile, certify_production_profile | profile and its 17 members | `_document`, "provider context metadata" | profile=SURROGATE; a profile lacking the member |
| launch.py:launch_document | job_execution and 8 members; execution_limits.{compatibility_generation, requested} | `_job_execution`, "a launch document's job execution"; `_configuration`, "a launch document's execution limits" | job_execution=SURROGATE; a document lacking the member |
| oci.py: activation_vector, exec_vector, run_vector | engine | `_engine`, "an engine name" | engine=SURROGATE |
| sessions.py: close_agent_session, handle_transport_loss (posture, session_epoch); observe_session_state (posture, provider_session_id, runtime_attempt_id, session_epoch) | session_ref members | `_session_ref`, "an agent session reference" | the member = SURROGATE in an otherwise valid reference |
| workspaces.py: adopted_assignment_workspace, assignment_workspace, discard_execution_roots, discard_workspace | assignment_id | `_assignment_identity`, "an assignment identity" | assignment_id=SURROGATE |
| workspaces.py: copied_manifest (root), read_input_root (inputs), refuse_if_held (storage; store configured first), restoration_lock_path (storage) | paths | `_real`, "a filesystem root" | the path = SURROGATE |

Stated (not delegated, following the file's existing rule for profile
aggregates whose capability label is an f-string): review_cycles.py
restore_abandoned_correction / settle_restoration_execution `profile`.

## Candidates reviewed and NOT added (remain per-case, S2/S3)

- oci.py OciAdapter.stop / stop_expired `request` (+2 members): `_stopped`'s label is the f-string `{what}`.
- oci.py OciAdapter.__init__ `network` (`_network`): not reachable with one spoiled operand (identity, roots, posture are typed first).
- oci.py run_vector `logs_delivered` (`_log_mounts`): deep inside the composed vector.
- provider_context.py finalize_context_use `checkpoint_reader` / `receipt_reader`, context_invocation_of / context_use_of / revalidate_context_start `attempt_id`: the store is read before `_text`; a probe reaches an absence or a store precondition first.
- provider_context.py certify_production_profile `evidence` (+6 members): `_profile` must pass with a production profile before the evidence is read.
- workspaces.py discard_execution_roots / discard_workspace `control` → `_token_terms` (the walker bound a store to an execution operand; not a demonstrable claim).
- workspaces.py borrow_manager_instance / borrowers_of / held_manager_instance / holders_of `place` (`check_workspace_storage` refuses first with another label); line_assignment_workspace `place` (deep).
- review_cycles.py settle_restoration_execution `profile` as a DELEGATED entry (cessation/launcher typed first) — stated instead.

## Measured effect (EveryReceivingEntryHasOneOwner / EveryProbeProvesItArrived)

| list | before S1 | after S1 |
|---|---|---|
| receiving entries with no owning validator | 696 | 597 |
| boundary calls attributed to no entry | 190 | 182 |
| owned entries with no probe | 266 | 266 (S4) |
| declared probes not reaching their owner | 0 (after B2 fixtures) | 0 |

Every S1 probe reaches its owner's label; the stale-owner and double-owner
tests are unchanged except the two intake `port` entries (per-case, S5).
