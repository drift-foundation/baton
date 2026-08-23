"""Generator for cases.json.

The case matrix is data, and this is the one place it is authored.  Keeping it
here rather than in prose is why SPEC 12.2 can require the register and the
matrix to agree in both directions and have a test enforce it.

Run with "python3 -B build_cases.py" from this directory after editing.
"""

from __future__ import annotations

import json
import pathlib

from conformance_model import seal_document

HERE = pathlib.Path(__file__).resolve().parent


def E(category, code):
    return {"category": category, "code": code}


def eq(fact, value):
    return {"fact": fact, "op": "equals", "value": value}


def ne(fact, value):
    return {"fact": fact, "op": "not-equals", "value": value}


def true(fact):
    return {"fact": fact, "op": "is-true"}


def false(fact):
    return {"fact": fact, "op": "is-false"}


def empty(fact):
    return {"fact": fact, "op": "empty"}


def non_empty(fact):
    return {"fact": fact, "op": "non-empty"}


def absent(fact):
    return {"fact": fact, "op": "absent"}


def subset(fact, value):
    return {"fact": fact, "op": "subset-of", "value": value}


def disjoint(fact, value):
    return {"fact": fact, "op": "disjoint-from", "value": value}


def refusal(pair, *requires):
    return {"kind": "control-refusal", "expected_refusal": pair, "requires": list(requires)}


def success(*requires):
    return {"kind": "control-success", "requires": list(requires)}


def invariant(*requires):
    return {"kind": "invariant", "requires": list(requires)}


def stim(kind, control_kinds, faults, detail):
    return {"kind": kind, "control_kinds": list(control_kinds), "faults": list(faults),
            "detail": detail}


CASES = []


BOTH = ["local-oci", "remote"]


def case(case_id, expectation, stimulus, evidence, statement, scope="portable-core",
         applies_to=None):
    CASES.append({
        "case_id": case_id,
        "family": case_id[0],
        "scope": scope,
        "applies_to": list(applies_to or BOTH),
        "required_faults": sorted(stimulus["faults"]),
        "stimulus": stimulus,
        "expectation": expectation,
        "deciding_evidence": evidence,
        "statement": statement,
    })


CTRL = "control-operation"
PROBE = "in-runtime-probe"
AUTH = "authority-read"
AGENT = "agent-script"
RECEIPT = "workflow-receipt"

# ----------------------------------------------------------------- family A --
case("A-git-exact-base",
     success(eq("materialized_object_id", "base-revision-under-test"),
             true("object_id_matches_manifest"), false("ref_was_resolved")),
     stim(CTRL, ["assignment.activate"], [], "Materialize a git source whose manifest binds an exact base revision."),
     ["manifest", "log"],
     "The workspace resolves to the exact base_revision the input manifest bound.")

case("A-git-moved-ref-refused",
     refusal(E("integrity", "digest"), false("object_id_matches_manifest")),
     stim(CTRL, ["assignment.activate"], [], "Move the source ref after binding, then materialize."),
     ["manifest", "log"],
     "A source ref that moved after binding refuses rather than taking the new tip.")

case("A-directory-exact-tree",
     success(true("tree_digest_matches"), true("entry_count_matches"), true("total_bytes_matches")),
     stim(CTRL, ["assignment.activate"], [], "Materialize a directory source and enumerate the tree."),
     ["manifest", "log"],
     "The materialized tree digest, entry count and total bytes equal the declared content manifest.")

case("A-input-readonly",
     invariant(false("input_write_succeeded"), non_empty("input_write_denied_by")),
     stim(PROBE, [], [], "Probe attempts a write into a declared input path."),
     ["log", "trace"],
     "A write into a declared input path does not succeed; inputs are read-only to the worker.")

case("A-output-traversal-refused",
     refusal(E("integrity", "path")),
     stim(CTRL, ["output.freeze"], [], "Declare an output path containing a traversal segment."),
     ["log"],
     "A declared output path containing a traversal segment is refused.")

case("A-output-symlink-refused",
     refusal(E("integrity", "file-type")),
     stim(CTRL, ["output.freeze"], [], "Place a symlink inside a declared output and freeze."),
     ["log"],
     "A symlink or reparse point inside a declared output is refused at freeze.")

case("A-output-overlap-refused",
     refusal(E("integrity", "path")),
     stim(CTRL, ["output.freeze"], [], "Declare two outputs whose destinations overlap."),
     ["log"],
     "Two declared outputs whose destinations overlap are refused.")

case("A-freeze-after-quiescence",
     success(eq("runtime_state_at_freeze", "quiescent"), true("freeze_committed")),
     stim(CTRL, ["runtime.inspect", "output.freeze"], ["process-kill"],
          "Stop the writer, observe quiescence, then freeze."),
     ["manifest", "trace"],
     "Freeze commits only after a quiescent runtime observation.")

case("A-freeze-digest-recomputes",
     success(true("manifest_digest_recomputes")),
     stim(CTRL, ["output.freeze"], [], "Freeze, then recompute the manifest digest over collected bytes."),
     ["manifest", "attestation"],
     "The frozen-result manifest digest recomputes over the collected bytes.")

case("A-freeze-exact-replay",
     success(true("replay_is_byte_identical"), eq("durable_effects", 1)),
     stim(CTRL, ["output.freeze"], ["frame-duplicate"], "Retry the exact freeze operation."),
     ["manifest", "log"],
     "An exact freeze retry replays byte-for-byte and commits nothing a second time.")

case("A-freeze-changed-bytes-refused",
     refusal(E("refused", "operation-collision"), eq("durable_effects", 0)),
     stim(CTRL, ["output.freeze"], [], "Freeze different bytes under the same operation id."),
     ["log"],
     "A freeze of different bytes under the same operation id refuses.")

case("A-undeclared-not-collected",
     invariant(true("wrote_undeclared_path"), disjoint("collected_paths", ["undeclared.txt"])),
     stim(PROBE, ["output.collect"], [], "Probe writes outside every declared output, then collect."),
     ["manifest", "diff"],
     "A file written outside every declared output is not collected.")

case("A-missing-required-output",
     success(eq("declared_disposition", "unable"), true("absence_recorded")),
     stim(CTRL, ["result.declare"], ["output-suppress"], "Suppress a required output, then declare."),
     ["manifest", "log"],
     "A missing required output yields 'unable' with the absence recorded, never 'completed'.")

case("A-proposal-is-not-a-push",
     invariant(true("proposal_is_immutable_artifact"),
               eq("canonical_target_revision_before", "target-under-test"),
               eq("canonical_target_revision_after", "target-under-test")),
     stim(CTRL, ["proposal.publish"], [], "Publish a proposal and read the canonical target."),
     ["bundle", "manifest"],
     "The proposal is an immutable artifact and the canonical target revision is unchanged.")

case("A-collection-ambiguous",
     success(true("resolved_by_exact_operation"), false("collected_from_writable_mount"),
             eq("durable_effects", 1)),
     stim(CTRL, ["output.collect"], ["transport-drop"], "Interrupt a collection, then reconcile."),
     ["log", "reproduction"],
     "An interrupted collection reconciles by repeating the exact operation against sealed bytes.")

# ----------------------------------------------------------------- family B --
case("B-no-authority-capability",
     invariant(false("authority_home_reachable"), false("authority_database_reachable")),
     stim(PROBE, [], [], "Probe attempts to resolve and open the authority home and database."),
     ["log", "attestation"],
     "No path resolving into the authority home or its database is reachable from the runtime.")

case("B-no-baton-executable",
     invariant(false("baton_executable_reachable"), false("baton_config_reachable")),
     stim(PROBE, [], [], "Probe attempts to resolve the Baton executable and configuration."),
     ["log", "attestation"],
     "The Baton executable and configuration are not reachable from the runtime.")

case("B-no-canonical-repository",
     invariant(false("canonical_repository_reachable")),
     stim(PROBE, [], [], "Probe attempts to resolve the canonical repository."),
     ["log", "attestation"],
     "The canonical repository is not mounted; only the private copy is.")

case("B-git-metadata-private",
     invariant(eq("object_store_identity", "private-clone"),
               ne("object_store_identity", "canonical")),
     stim(PROBE, [], [], "Probe reads which object store the workspace resolves against."),
     ["log", "diff"],
     "The workspace's Git metadata resolves only against its private object store.")

case("B-cross-worker-isolation",
     invariant(false("peer_workspace_readable"), false("peer_output_writable")),
     stim(PROBE, [], ["concurrent-assignment"],
          "Run two concurrent assignments; each probes for the other's paths."),
     ["log", "trace"],
     "Neither runtime can read or write the other's workspace or declared output.")

case("B-network-policy-enforced",
     invariant(false("egress_beyond_policy_succeeded"), true("egress_within_policy_succeeded")),
     stim(PROBE, [], ["network-deny"], "Probe attempts egress inside and outside the pinned policy."),
     ["log", "trace"],
     "Egress beyond the pinned network policy does not succeed.")

case("B-resource-policy-enforced",
     invariant(false("resource_beyond_policy_succeeded")),
     stim(PROBE, [], [], "Probe attempts to exceed the pinned resource limits."),
     ["log", "trace"],
     "Resource use beyond the pinned limits does not succeed.")

case("B-tool-policy-enforced",
     invariant(false("tool_outside_policy_available"),
               subset("available_tools", ["pinned-tool-a", "pinned-tool-b"])),
     stim(PROBE, [], [], "Probe enumerates the tools available to it."),
     ["log", "trace"],
     "No tool outside the pinned tool policy is available to the worker.")

# ----------------------------------------------------------------- family C --
case("C-preclaim-metadata-only",
     invariant(false("offer_carries_input_bytes"), non_empty("offer_carries_digests")),
     stim(CTRL, ["offer.issue"], [], "Inspect the offer frame before any decision."),
     ["log", "manifest"],
     "The offer frame carries metadata and digests only; no input bytes.")

case("C-preclaim-no-execution",
     invariant(false("consent_runtime_has_workspace"), false("consent_runtime_has_output"),
               empty("consent_runtime_writable_paths")),
     stim(PROBE, ["offer.issue"], [], "Probe the consent runtime for writable paths and input."),
     ["log", "trace"],
     "The consent runtime reaches no input, no output and no writable path.")

case("C-token-expired",
     refusal(E("refused", "precondition"), false("claim_committed"), eq("work_phase", "queued")),
     stim(CTRL, ["offer.decide"], ["clock-advance"], "Advance the clock past expiry, then decide."),
     ["log"],
     "An expired claim token refuses; the Work stays queued, unclaimed and offerable.")

case("C-token-replayed",
     refusal(E("refused", "precondition"), false("claim_committed")),
     stim(CTRL, ["offer.decide"], [], "Replay a token that was already spent."),
     ["log"],
     "A replayed claim token refuses; no second claim commits.")

case("C-token-wrong-binding",
     refusal(E("refused", "precondition"), false("claim_committed")),
     stim(CTRL, ["offer.decide"], [], "Present a token against a different offer, Work or participant."),
     ["log"],
     "A token presented against a different offer, Work or participant refuses.")

# W4487 (`work/records/2026/08/finding-worker-control-decline-token-conflict/`),
# ruled 2026-08-22. W151 1-ruled §7 required the exact unspent bearer to
# decline; worker-control 1.0 and its frozen schema require `claim_token: null`.
# The approver kept the non-secret envelope and superseded W151, so the
# register has to carry what now authorizes a decline — otherwise the one
# rule the two contracts had to be re-ruled over is the one nothing checks.
case("C-decline-without-bearer",
     success(true("decline_carried_null_token"), eq("offer_state", "declined"),
             true("offer_verifier_spent"), false("claim_committed"),
             eq("work_phase", "queued")),
     stim(CTRL, ["offer.decide"], [], "Decline an issued offer with claim_token null."),
     ["log", "trace"],
     "A decline carrying no bearer terminates its own offer, spends the verifier and commits no claim."),

case("C-decline-carrying-bearer-refused",
     refusal(E("integrity", "schema"), false("claim_committed"),
             ne("offer_state", "declined")),
     stim(CTRL, ["offer.decide"], [], "Decline while carrying the claim bearer."),
     ["log"],
     "A decline that transmits the bearer is refused; the offer is not terminated."),

case("C-decline-wrong-binding-refused",
     refusal(E("refused", "precondition"), false("claim_committed"),
             ne("offer_state", "declined"), ne("other_offer_state", "declined")),
     stim(CTRL, ["offer.decide"], [], "Decline naming one offer while carrying another offer's attempt or Work."),
     ["log"],
     "A differently bound decline refuses and terminates neither the named offer nor the bound one."),

case("C-claim-ambiguous-no-execution",
     invariant(eq("operation_state", "unknown"), false("writable_runtime_started")),
     stim(CTRL, ["offer.decide"], ["process-kill"], "Interrupt the claim mid-flight and inspect."),
     ["trace", "log"],
     "While a claim is unsettled, no writable runtime starts.")

case("C-claim-settled-by-operation",
     success(eq("settled_by", "operation-replay"), ne("settled_by", "handler-identity")),
     stim(CTRL, ["offer.decide"], ["manager-restart"], "Restart the manager, then settle the claim."),
     ["trace", "log"],
     "The claim is settled by exact operation replay, not by reading the current Handler.")

case("C-no-write-before-activate",
     invariant(empty("writable_paths_before_activate"), empty("tools_before_activate"),
               non_empty("writable_paths_after_activate")),
     stim(PROBE, ["assignment.activate"], [], "Probe before and after activation."),
     ["log", "trace"],
     "No writable path or execution tool exists before assignment.activate.")

case("C-assignment-manifest-after-claim",
     invariant(false("manifest_existed_before_claim"), true("manifest_exists_after_claim"),
               true("manifest_generation_is_live")),
     stim(AUTH, ["assignment.activate"], [], "Read the assignment manifest and the authority claim event."),
     ["manifest"],
     "The assignment manifest exists only after the claim committed and binds the live generation.")

case("C-stale-activity",
     refusal(E("stale-assignment", "generation"), eq("durable_effects", 0)),
     stim(CTRL, ["activity.emit"], [], "Emit activity under a superseded generation."),
     ["log"],
     "Activity under a superseded generation refuses.")

case("C-stale-result",
     refusal(E("stale-assignment", "generation"), eq("durable_effects", 0)),
     stim(CTRL, ["result.declare"], [], "Declare a result under a superseded generation."),
     ["log"],
     "A result declared under a superseded generation refuses.")

case("C-stale-proposal",
     refusal(E("stale-assignment", "generation"), eq("durable_effects", 0)),
     stim(CTRL, ["proposal.publish"], [], "Publish a proposal under a superseded generation."),
     ["log"],
     "A proposal published under a superseded generation refuses.")

case("C-activity-changes-no-state",
     invariant(eq("phase_before", "active"), eq("phase_after", "active"),
               true("handler_unchanged"), true("generation_unchanged"),
               true("contract_unchanged")),
     stim(CTRL, ["activity.emit"], [], "Emit a burst of activity and read the projection either side."),
     ["trace", "log"],
     "A burst of activity leaves phase, Handler, contract and generation unchanged.")

# ----------------------------------------------------------------- family D --
case("D-fence-before-stop",
     invariant(true("fence_precedes_agent_cancel"), true("fence_precedes_runtime_stop"),
               true("fence_and_end_same_transaction")),
     stim(CTRL, ["runtime.cancel"], [], "Cancel, then read the ordered event journal."),
     ["trace"],
     "The fence-and-end authority transaction precedes every stop order.")

case("D-cancel-reply-is-not-death",
     invariant(true("cancel_reply_succeeded"), false("gate_cleared_by_reply")),
     stim(CTRL, ["runtime.cancel", "runtime.inspect"], [], "Cancel, then read the gate before inspecting."),
     ["trace", "log"],
     "A successful cancel reply does not by itself satisfy the quiescence gate.")

case("D-quiescent-is-not-destroyed",
     invariant(eq("runtime_observation", "quiescent"), false("gate_cleared"),
               non_empty("gate_token")),
     stim(CTRL, ["runtime.inspect"], [], "Observe quiescence and read the gate."),
     ["trace"],
     "A quiescent observation does not clear runtime-quiescence.")

case("D-destroyed-clears-gate",
     success(eq("runtime_observation", "destroyed"), true("gate_cleared"),
             eq("successor_generation", 2)),
     stim(CTRL, ["runtime.destroy"], [], "Destroy the runtime, satisfy the gate, claim a successor."),
     ["trace", "attestation"],
     "A positive destroyed observation clears the gate and the successor mints the next generation.")

case("D-uncertain-quiescence",
     success(eq("runtime_observation", "uncertain"), ne("runtime_observation", "destroyed")),
     stim(CTRL, ["runtime.inspect"], ["transport-partition"], "Partition the runtime, then inspect."),
     ["trace", "log"],
     "An unreachable runtime records 'uncertain', never 'destroyed'.")

case("D-replacement-gated",
     refusal(E("refused", "precondition"), true("gate_held"), false("claim_committed")),
     stim(CTRL, ["offer.decide"], ["transport-partition"], "Attempt a replacement claim while gated."),
     ["trace"],
     "A replacement claim refuses while the quiescence gate is visibly held.")

case("D-late-publication-refused",
     refusal(E("stale-assignment", "ended"), eq("durable_effects", 0)),
     stim(CTRL, ["proposal.publish"], [], "Publish after the fence."),
     ["log"],
     "Publication attempted after the fence refuses.")

case("D-cancelled-output-sealed",
     success(true("material_sealed"), non_empty("sealed_binds"), false("material_discarded")),
     stim(CTRL, ["output.collect"], [], "Cancel with partial output present, then collect."),
     ["manifest", "log"],
     "Partial output at cancellation is sealed with its Work, generation, reason and policy provenance.")

case("D-discard-requires-policy",
     refusal(E("policy", "retention"), false("material_discarded")),
     stim(CTRL, ["output.retain"], [], "Attempt discard with no pinned disposable-attempt policy."),
     ["log"],
     "Discarding recoverable output without a pinned disposable-attempt policy refuses.")

case("D-slot-freed-immediately",
     success(true("unrelated_claim_committed"), true("cancelled_work_still_gated")),
     stim(CTRL, ["offer.decide"], ["concurrent-assignment"],
          "After cancellation, claim an unrelated Work as the same participant."),
     ["trace"],
     "The participant may claim an unrelated Work while the cancelled Work stays gated.")

case("D-agent-quiescence-not-runtime",
     invariant(eq("agent_session_state", "agent-quiescent"), false("gate_cleared"),
               disjoint("gate_clearance_evidence_sources", ["agent-session"])),
     stim(AUTH, [], [], "Reach agent quiescence, then read the gate and its clearance evidence."),
     ["trace"],
     "No gate clearance cites an agent-session observation.")

case("D-retention-policy",
     refusal(E("policy", "retention"), false("retained_past_policy")),
     stim(CTRL, ["output.retain"], [], "Attempt retention beyond the pinned policy."),
     ["log", "manifest"],
     "Retention beyond the pinned policy refuses; retention is not acceptance.")

# ----------------------------------------------------------------- family E --
case("E-manager-restart-reconciles",
     success(true("authority_record_read"), true("control_store_record_read"),
             false("outcome_inferred_from_handler")),
     stim(CTRL, ["operation.reply"], ["manager-restart"],
          "Restart the manager mid-operation, then reconcile."),
     ["trace", "log"],
     "After restart the ambiguous operation is reconciled against both durable records.")

case("E-adapter-restart-reconciles",
     success(true("adapter_reattached_to_same_runtime"), eq("durable_effects", 1),
             false("second_runtime_started")),
     stim(CTRL, ["runtime.inspect"], ["adapter-restart"],
          "Restart the adapter mid-attempt, then reconcile its runtime observations."),
     ["trace", "log"],
     "After an adapter restart the same runtime is re-identified and no second runtime starts.")

# The only profile-scoped case in the matrix.  A local runtime's host IS the
# manager's host, so restarting it is `manager-restart` — which is in the
# common core as E-manager-restart-reconciles.  There is no separate host to
# restart, so this is a fault that cannot exist locally rather than one a local
# profile is being let off.
case("E-remote-host-restart",
     success(eq("runtime_observation", "uncertain"), false("gate_cleared"),
             false("replacement_claim_committed")),
     stim(CTRL, ["runtime.inspect"], ["host-restart"],
          "Restart the remote runtime host, then inspect and attempt a replacement."),
     ["trace", "log"],
     "A restarted remote host leaves the runtime uncertain and the replacement gated.",
     applies_to=["remote"])

case("E-exact-replay",
     success(true("replay_is_byte_identical"), eq("durable_effects", 1)),
     stim(CTRL, ["operation.reply"], ["frame-duplicate"], "Retry the exact operation."),
     ["log"],
     "An exact operation retry replays byte-for-byte.")

case("E-operation-collision",
     refusal(E("refused", "operation-collision"), eq("durable_effects", 0)),
     stim(CTRL, ["operation.reply"], [], "Reuse an operation id with a different signature."),
     ["log"],
     "The same operation id with a different signature refuses and changes nothing.")

# Review 2026-08-22T14:39:32Z [P1] on W4487. §4.2 always said the operation
# signature is the canonical digest of the operation KIND and every effective
# durable operand, and §12 rule 9 requires every signature to include all of
# them — but nothing in the family certified that a receiver RECOMPUTES it.
# The defect that surfaced this was a decline document whose durable reason
# changed, whose body digest was recomputed, and whose operation signature
# still named the previous decline: schema-valid, semantically valid, and
# replayable as the first decline. E-02 does not catch it, because E-02 starts
# from two signatures that already differ.
case("E-operation-signature-mismatch-refused",
     refusal(E("integrity", "digest"), eq("durable_effects", 0)),
     stim(CTRL, ["offer.decide"], [],
          "Change a durable operand, recompute ONLY the body digest, and retain the previous operation signature."),
     ["log"],
     "A command whose operation signature does not recompute over its own kind and operands refuses and writes nothing.")

# The kind is IN the signature, and this is the case that can tell. An
# implementation that signed the body alone would compute one signature for
# both, so the second frame would look like an exact retry and replay the
# first kind's committed result instead of colliding. `output.freeze` and
# `output.collect` are the natural probe: §6 gives them the same body.
case("E-operation-signature-covers-kind",
     refusal(E("refused", "operation-collision"), eq("durable_effects", 1),
             false("second_kind_replayed_first_result")),
     stim(CTRL, ["output.freeze", "output.collect"], [],
          "Reuse one operation id for output.freeze and output.collect, whose bodies are byte-identical."),
     ["log"],
     "Two kinds carrying identical operands are different operations, so the second under one id collides rather than replaying.")

case("E-duplicate-observation",
     success(eq("durable_effects", 1), true("replay_is_byte_identical")),
     stim(CTRL, ["runtime.inspect"], ["frame-duplicate"], "Deliver a duplicate runtime observation."),
     ["trace"],
     "A duplicate runtime observation replays without a second effect.")

case("E-observation-regression",
     refusal(E("runtime-observation", "state-regression"), eq("durable_effects", 0)),
     stim(CTRL, ["runtime.inspect"], [], "Report an observation earlier than the recorded one."),
     ["trace"],
     "A regressive runtime observation refuses; the axis never walks backwards.")

case("E-duplicate-frame",
     success(eq("durable_effects", 1)),
     stim(CTRL, ["activity.emit"], ["frame-duplicate", "frame-delay"],
          "Duplicate and delay a frame carrying the same message id."),
     ["log"],
     "A duplicated or delayed frame produces no second durable effect.")

case("E-partition-reattach-proof",
     success(true("runtime_identity_proved"), true("assignment_compared_in_full"),
             false("reachability_treated_as_identity")),
     stim(CTRL, ["runtime.inspect"], ["transport-partition"], "Partition, heal, then reattach."),
     ["trace", "attestation"],
     "Reattachment cites an exact runtime identity and the full assignment.")

case("E-reachability-is-not-identity",
     refusal(E("runtime-observation", "identity-mismatch"), false("reattached")),
     stim(CTRL, ["runtime.inspect"], ["transport-partition"],
          "Heal the partition onto a different runtime and attempt reattachment."),
     ["trace"],
     "Transport reachability alone is refused as evidence of runtime identity.")

case("E-duplicate-runtime-start",
     refusal(E("runtime-observation", "duplicate-runtime"), true("assignment_cancelled"),
             false("second_runtime_adopted")),
     stim(CTRL, ["runtime.start"], ["duplicate-runtime-start"], "Produce two runtimes for one attempt."),
     ["trace"],
     "A duplicated runtime start cancels the assignment rather than adopting one.")

case("E-agent-transport-lost",
     success(eq("agent_session_state", "unknown"), eq("turn_outcome", "transport-lost"),
             false("reprompted"), false("session_resumed")),
     stim(AGENT, [], ["transport-drop"], "Drop the agent transport mid-turn."),
     ["log", "trace"],
     "A dropped agent transport ends the epoch 'unknown' with no resume and no re-prompt.")

case("E-cleanup-blocked-on-intake",
     invariant(eq("cleanup_result", "blocked-on-intake"), true("authority_state_unchanged"),
               false("pending_material_deleted")),
     stim(CTRL, ["runtime.destroy"], [], "Run cleanup while a sealed record is pending intake."),
     ["log"],
     "Cleanup reports blocked-on-intake and changes no authority state.")

# ----------------------------------------------------------------- family F --
case("F-no-credential-in-manifests",
     invariant(disjoint("canaries_found_in_manifests", ["credential-canary"]),
               true("manifest_surfaces_scanned")),
     stim(AUTH, [], ["canary-plant"], "Plant a credential canary and scan every durable manifest."),
     ["manifest", "attestation"],
     "No credential appears in any durable manifest or artifact locator.")

case("F-no-credential-in-events",
     invariant(disjoint("canaries_found_in_events", ["credential-canary"]),
               true("event_surfaces_scanned")),
     stim(AUTH, [], ["canary-plant"], "Plant a credential canary and scan events, errors and logs."),
     ["log", "attestation"],
     "No credential appears in any event, error or retained log.")

case("F-canary-each-surface",
     invariant(eq("surfaces_scanned",
                  ["caches", "declared-output", "events", "evidence", "git-objects", "manifests",
                   "proposal", "retained-logs", "retained-runtime-layers", "workspace"]),
               eq("planted_canaries_found", 10)),
     stim(AUTH, [], ["canary-plant"], "Plant one canary per named surface and scan all ten."),
     ["attestation", "reproduction"],
     "Every surface worker-control 9 names is scanned, evidenced by a planted canary found in each.")

case("F-leak-refuses-publication",
     refusal(E("integrity", "secret-leak"), false("proposal_published")),
     stim(CTRL, ["proposal.publish"], ["canary-plant"], "Plant a canary in the output, then publish."),
     ["log", "attestation"],
     "A detected leak refuses publication.")

case("F-credential-lifetime",
     refusal(E("policy", "credential-lifetime"), false("execution_started")),
     stim(CTRL, ["assignment.activate"], ["credential-expire"],
          "Activate with a credential below the pinned remaining-lifetime floor."),
     ["log"],
     "A credential below the pinned remaining-lifetime floor refuses before execution.")

case("F-credential-scoped-to-assignment",
     success(true("credential_delivered_to_assignment"), true("credential_out_of_band"),
             eq("credential_scope", "assignment"), false("credential_persisted")),
     stim(PROBE, ["assignment.activate"], [], "Deliver the credential and probe its scope and persistence."),
     ["log", "attestation"],
     "The credential is delivered out of band, scoped to the exact assignment, and not persisted.")

case("F-credential-not-reusable-cross-assignment",
     # A credential presented from inside another runtime is an INVARIANT, not
     # a control refusal: nothing in an upstream contract requires the runtime
     # to synthesize a control frame for it.
     invariant(false("cross_assignment_access_succeeded"),
               non_empty("cross_assignment_denied_by")),
     stim(PROBE, [], ["concurrent-assignment", "credential-reuse"],
          "Present one assignment's credential from another assignment's runtime."),
     ["log", "trace"],
     "One assignment's credential grants nothing in another assignment's runtime.")

case("F-credential-expiry-mid-run",
     invariant(true("credential_expired_during_run"), false("expired_credential_accepted"),
               true("expiry_reported")),
     stim(PROBE, [], ["credential-expire"], "Expire the credential mid-run and probe its use."),
     ["log", "trace"],
     "A credential that expires during a run stops working and the expiry is reported.")

case("F-residual-risk-reported",
     invariant(non_empty("residual_risk_unproven"), true("scanned_surfaces_listed"),
               false("absence_claimed_unqualified")),
     stim(AUTH, [], [], "Read the assessor's residual-risk statement."),
     ["dossier"],
     "The run reports which surfaces were scanned and what remains unproven.")

# ----------------------------------------------------------------- family G --
case("G-mode-unavailable",
     refusal(E("policy", "denied"), false("turn_started"), false("fell_back_to_other_mode")),
     stim(AGENT, [], [], "Withhold the pinned mode from the scripted agent."),
     ["log"],
     "An unavailable pinned mode fails visibly rather than falling back.")

case("G-policy-drift",
     refusal(E("policy", "denied"), eq("turn_outcome", "policy-failed")),
     stim(AGENT, [], [], "Report provider operands differing from the pinned ones."),
     ["log", "trace"],
     "Provider operands differing from the pinned ones fail the turn.")

case("G-approval-refused",
     refusal(E("policy", "denied"), false("anything_granted"), eq("turn_outcome", "policy-failed")),
     stim(AGENT, [], [], "Script an unexpected approval request."),
     ["log", "trace"],
     "An unexpected approval request grants nothing.")

case("G-approval-race",
     refusal(E("policy", "denied"), false("anything_granted"), true("answer_identical_to_unraced")),
     stim(AGENT, [], [], "Script an approval arriving after cancellation was ordered."),
     ["log", "trace"],
     "An approval arriving after cancellation takes the identical non-granting answer.")

case("G-approval-payload-valid",
     success(true("payload_valid_against_provider_schema"), false("anything_granted"),
             eq("families_answered", 4)),
     stim(AGENT, [], [], "Script one approval request per family and capture each reply."),
     ["log", "attestation"],
     "Each denial payload validates against its family's provider response schema.")

case("G-untrusted-output",
     invariant(true("output_schema_valid"), false("output_trusted_without_verification")),
     stim(PROBE, ["result.declare"], [], "Declare schema-valid but hostile worker output."),
     ["log", "reproduction"],
     "Schema-valid worker output is still treated as untrusted.")

case("G-prose-decides-nothing",
     invariant(empty("portable_state_derived_from_prose"),
               empty("portable_state_derived_from_tool_status")),
     stim(AGENT, [], [], "Script a transcript claiming success, failure and completion."),
     ["log", "trace"],
     "No portable state is derived from agent prose, tool status or diagnostics.")

case("G-proposal-integrity",
     invariant(true("assignment_digest_matches"), true("input_digest_matches"),
               true("policy_digest_matches"), true("output_digest_matches"),
               true("candidate_digest_matches"), true("target_digest_matches")),
     stim(RECEIPT, ["proposal.publish"], [], "Recompute every digest the proposal binds."),
     ["manifest", "candidate-tree"],
     "Every digest the proposal binds matches what the run actually used.")

case("G-receipt-immutability",
     refusal(E("refused", "already-terminal"), true("committed_receipt_unchanged"),
             eq("receipt_families_tested", 5)),
     stim(RECEIPT, [], [], "Write each workflow receipt twice with different content."),
     ["manifest", "log"],
     "A second differing write to any workflow receipt refuses.")

case("G-version-refused",
     refusal(E("refused", "unsupported-version"), eq("durable_effects", 0)),
     stim(CTRL, ["control.hello", "control.welcome"], [], "Offer an unsupported protocol version."),
     ["log"],
     "An unsupported protocol version refuses before any side effect.")

case("G-capability-refused",
     refusal(E("refused", "capability"), eq("durable_effects", 0)),
     stim(CTRL, ["control.hello"], [], "Send a message requiring an unselected capability."),
     ["log"],
     "A message requiring an unselected capability refuses before any side effect.")

case("G-extension-refused",
     refusal(E("refused", "extension"), eq("durable_effects", 0)),
     stim(CTRL, ["control.hello"], [], "Send an unnegotiated extension."),
     ["log"],
     "An unnegotiated extension refuses before any side effect.")

case("G-uncertified-profile",
     refusal(E("policy", "profile-uncertified"), eq("gate_token", "contract-runtime"),
             false("execution_started")),
     stim(CTRL, ["assignment.activate"], ["profile-decertify"],
          "Withdraw profile certification, then attempt execution."),
     ["log", "trace"],
     "An uncertified runtime profile cannot execute the contract.")

case("G-plan-rejected",
     refusal(E("refused", "precondition"), eq("gate_token", "plan-revision"),
             false("identical_plan_reoffered")),
     stim(CTRL, ["result.declare"], ["plan-reject"], "Reject a plan, then reoffer the identical one."),
     ["trace"],
     "The plan-revision gate blocks reoffering the identical plan.")

case("G-verdict-is-not-policy",
     invariant(false("suite_mutated_route_policy"), false("suite_mutated_certification"),
               true("verdict_reported")),
     stim(AUTH, [], [], "Read route policy and profile certification either side of a run."),
     ["dossier"],
     "The suite reports a verdict and mutates no route policy or profile certification.")

case("G-profile-failure-signal",
     invariant(eq("signal", "probation"), non_empty("signal_failed_cases"),
               eq("signal_consumer", "route-policy"), true("signal_binds_profile_digest")),
     stim(AUTH, [], ["profile-decertify"],
          "Produce a run with a failed core case and read the emitted profile signal."),
     ["dossier", "attestation"],
     "A run with a failed portable core case emits a probation signal bound to the profile and adapter digests.")

case("G-error-frames-typed",
     invariant(true("every_refusal_was_a_control_error"), true("every_pair_in_taxonomy"),
               non_empty("retry_classes_seen"), non_empty("operation_states_seen")),
     stim(CTRL, ["control.error"], [],
          "Collect the error frame from every control-refusal case in the run."),
     ["log"],
     "Every refused control operation yields a control.error with its pair, retry class and operation_state.")

case("G-authority-unavailable",
     refusal(E("unavailable", "authority"), eq("operation_state", "unknown")),
     stim(CTRL, ["control.error"], ["authority-unavailable"], "Make the authority unreachable."),
     ["log"],
     "An unreachable authority is reported unavailable with operation_state unknown.")

case("G-artifact-store-unavailable",
     refusal(E("unavailable", "artifact-store"), eq("operation_state", "unknown")),
     stim(CTRL, ["control.error"], ["artifact-store-unavailable"], "Make the artifact store unreachable."),
     ["log"],
     "An unreachable artifact store is reported unavailable, never as a refusal.")

case("G-source-provider-unavailable",
     refusal(E("unavailable", "source-provider"), eq("operation_state", "unknown")),
     stim(CTRL, ["control.error"], ["source-provider-unavailable"], "Make the source provider unreachable."),
     ["log"],
     "An unreachable source provider is reported unavailable, never as a refusal.")

case("G-stale-contract",
     refusal(E("stale-assignment", "contract"), eq("durable_effects", 0)),
     stim(CTRL, ["activity.emit"], [], "Act under a superseded contract selector."),
     ["log", "trace"],
     "An act under a superseded contract selector refuses.")

case("G-stale-target",
     refusal(E("stale-assignment", "target"), eq("journalled_attempts", 1),
             false("integration_committed")),
     stim(RECEIPT, [], ["canonical-target-move"], "Move the canonical target, then integrate."),
     ["log", "manifest"],
     "A moved canonical target refuses integration and journals exactly one attempt.")

# ----------------------------------------------------------------- family H --
case("H-capability-withheld",
     invariant(empty("advertised_client_capabilities"), false("fs_advertised"),
               false("terminal_advertised")),
     stim(AGENT, [], [], "Capture the client capabilities the relay advertised."),
     ["log"],
     "The relay advertises no filesystem, terminal or other client capability.")

case("H-unadvertised-method-refused",
     refusal(E("policy", "denied"), false("method_served"), eq("turn_outcome", "policy-failed")),
     stim(AGENT, [], [], "Script an agent call to an unadvertised client method."),
     ["log"],
     "An agent call to an unadvertised client method is refused, and the turn fails.")

case("H-fresh-session",
     invariant(eq("distinct_provider_sessions", 2), false("session_reused")),
     stim(AGENT, [], [], "Open two epochs and compare provider session identities."),
     ["log", "trace"],
     "Each epoch opens a new provider session; none is reused.")

case("H-history-methods-refused",
     refusal(E("refused", "capability"), empty("history_methods_sent")),
     stim(AGENT, [], [], "Attempt session load, resume and fork."),
     ["log"],
     "Load, resume and fork are never sent and are refused if attempted.")

case("H-consent-then-execution",
     invariant(eq("consent_assignment_ref", None), true("execution_assignment_present"),
               true("same_runtime_attempt"), eq("consent_epoch", 1), eq("execution_epoch", 1)),
     stim(AGENT, [], [], "Run a consent posture, settle the claim, then run an execution posture."),
     ["trace", "manifest"],
     "One attempt hosts a consent session with no assignment and a separate execution session with the exact one.")

case("H-turn-outcomes",
     invariant(eq("outcomes_exercised", 8), true("every_outcome_named_its_terminal_fact"),
               empty("outcomes_derived_from_prose")),
     stim(AGENT, [], ["transport-drop", "clock-advance"],
          "Script one ending per closed turn outcome."),
     ["trace", "log"],
     "Each scripted ending produces its mapped closed turn outcome and names its terminal fact.")

case("H-disposition-gating",
     refusal(E("refused", "precondition"), false("disposition_accepted")),
     stim(CTRL, ["result.declare"], [],
          "Declare a disposition outside the set the observed turn outcome permits."),
     ["log"],
     "A disposition outside the set permitted by the turn outcome refuses.")

case("H-event-normalization",
     invariant(eq("event_kinds_exercised", 10), eq("unmapped_kind_normalized_to", "other"),
               empty("events_dropped_silently")),
     stim(AGENT, [], [], "Script one provider update per normalized kind, plus an unmapped one."),
     ["trace"],
     "Every scripted provider update maps into the closed event set; unmapped kinds become 'other'.")

case("H-event-integrity",
     refusal(E("integrity", "digest"), true("identical_duplicate_replayed"),
             false("conflict_merged")),
     stim(AGENT, [], ["frame-duplicate"], "Deliver an identical duplicate, then a conflicting one."),
     ["trace", "attestation"],
     "Events are sealed and bounded; a conflicting duplicate refuses rather than merging.")

case("H-event-overflow-counted",
     invariant(non_empty("dropped_event_count"), true("drops_recorded_durably"),
               false("drops_silent")),
     stim(AGENT, [], [], "Overflow the relay queue."),
     ["trace"],
     "Queue overflow drops are counted durably, never silent.")

case("H-cancel-observed",
     invariant(true("cancel_order_recorded"), non_empty("cancel_observation"),
               false("order_treated_as_observation")),
     stim(AGENT, ["runtime.cancel"], [], "Order cancellation and observe the terminal fact."),
     ["trace"],
     "Cancellation records the order, then whichever terminal fact actually occurred.")

case("H-cancel-drain-unknown",
     invariant(eq("cancel_observation", "agent-quiescence-unknown"),
               eq("turn_outcome", "timeout"), false("gate_cleared")),
     stim(AGENT, [], ["transport-drop"], "Order cancellation and let the drain deadline elapse."),
     ["trace"],
     "No terminal fact within the drain deadline records agent-quiescence-unknown.")

case("H-axis-monotonic",
     refusal(E("runtime-observation", "state-regression"), false("axis_regressed")),
     stim(AGENT, [], [], "Report an agent-session state earlier than the recorded one."),
     ["trace"],
     "A regressive agent-session state refuses.")

case("H-provider-id-is-not-identity",
     invariant(empty("participants_derived_from_provider_id"),
               empty("assignments_derived_from_provider_id")),
     stim(AUTH, [], [], "Search durable records for identities derived from a provider session id."),
     ["log"],
     "No Baton participant, Handler or assignment is derived from a provider session id.")

case("H-agent-holds-no-capability",
     invariant(empty("baton_capabilities_reaching_agent"), false("agent_received_token"),
               false("agent_received_authority_path")),
     stim(AGENT, [], [], "Enumerate everything the agent endpoint received."),
     ["log", "attestation"],
     "Nothing the agent endpoint received carries a Baton capability.")


def required_facts(entry):
    names = {p["fact"] for p in entry["expectation"]["requires"]}
    if entry["expectation"]["kind"] == "control-refusal":
        names.add("refusal")
    return sorted(names)


def main():
    obligations = json.loads((HERE / "obligations.json").read_text())
    by_case = {}
    for o in obligations["obligations"]:
        for cid in o["cases"]:
            by_case.setdefault(cid, []).append(o["id"])

    defined = {c["case_id"] for c in CASES}
    missing = set(by_case) - defined
    extra = defined - set(by_case)
    if missing:
        raise SystemExit("cases in the register with no definition: " + repr(sorted(missing)))
    if extra:
        raise SystemExit("definitions with no register entry: " + repr(sorted(extra)))

    sealed = []
    for entry in sorted(CASES, key=lambda c: c["case_id"]):
        document = {
            "suite_family": "baton.worker-conformance",
            "version": {"major": 1, "minor": 0},
            "document": "case",
            "case_id": entry["case_id"],
            "family": entry["family"],
            "scope": entry["scope"],
            "applies_to": entry["applies_to"],
            "obligations": sorted(by_case[entry["case_id"]]),
            "supplemental_source": None,
            "required_faults": entry["required_faults"],
            "stimulus": entry["stimulus"],
            "expectation": entry["expectation"],
            "required_facts": required_facts(entry),
            "deciding_evidence": entry["deciding_evidence"],
            "statement": entry["statement"],
        }
        sealed.append(seal_document(document))

    (HERE / "cases.json").write_text(
        json.dumps({"format": "baton.worker-conformance/cases-2", "cases": sealed},
                   indent=1, ensure_ascii=False) + "\n")
    kinds = {}
    for c in sealed:
        kinds[c["expectation"]["kind"]] = kinds.get(c["expectation"]["kind"], 0) + 1
    print("cases:", len(sealed), kinds)


if __name__ == "__main__":
    main()
