"""CLOSED CANONICAL CONSTRUCTORS for every document this manager emits.

PLAN 4bz, the outbound half. `boundaries.py` owns what arrives; this owns what
leaves. The ruling's sentence is that an outbound contract document is produced
through a closed constructor and OWNED BY THE NEXT RECEIVER at its own boundary
-- so nothing here revalidates a member's value. What it establishes is the
SHAPE: exactly these members, in one deterministic order, written down once.

WHY A CONSTRUCTOR AND NOT AN INLINE DICT. Every one of these documents was
assembled at its return statement, which meant the shape of an answer lived
wherever the answer happened to be built -- and three of them are built in more
than one place. `_settle_terminal` returns one document when its compare-and-swap
wins and a different one when it loses; `_record_claim` is reached from four
callers each contributing its own members. The shape was therefore a property of
the PATH rather than of the operation, and a caller reading one return statement
had no way to learn what the other paths answer with.

It is also what makes the next receiver's job possible. A document whose members
depend on which branch produced it cannot be owned at the far end against
anything, because there is nothing to own it against.

WHAT THIS IS NOT. It is not validation. A constructor here refuses a member set
that does not match the contract -- a defect in this build, raised as one -- and
says nothing about the members' values. Owning our own outbound values would be
the blanket revalidation the same ruling forbids, one direction over.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value

__all__ = ["CONTRACTS", "ASSIGNMENT", "profile_certified",
           "agent_session_certified", "acp_negotiated", "offer_issued",
           "offer_bearer", "offer_settled", "offer_settled_by_another",
           "offer_accepted", "claim_recorded", "settlement_observed",
           "recoverable_offer", "recovery_report", "assignment", "work_ref",
           "WORK_REF", "RUNTIME_LABELS",
           "attempt_recorded", "assignment_activated", "observation",
           "runtime_labels", "runtime_start_requested", "runtime_attached",
           "runtime_uncertain", "runtime_cancel", "cancel_intent",
           "quiescence_ordered", "quiescence_not_ordered",
           "attempt_cancelled", "SESSION_REF", "session_ref", "posture_slot",
           "slot_moved", "session_opened", "provider_session_adopted",
           "session_observed", "session_closed", "transport_lost",
           "session_reconciled", "session_quiescence_requested",
           "operation", "manifest_retained", "freeze_requested",
           "result_frozen", "output_answer", "frozen_output",
           "output_artifact", "interrogation", "interrogation_requested",
           "collect_requested", "destroy_command", "intake_artifact",
           "intake_receipt", "retain_command",
           "retention", "retention_decided", "cleanup_blocked",
           "cleanup_settled", "cleanup_unsettled"]

# name -> (required, optional). ONE table, so "what does this manager answer
# with" is a question with a written answer rather than a survey of return
# statements.
CONTRACTS = {
    "profile.certified": (("kind", "name", "digest"), ()),
    "offer.issued": (("offer_id", "work_id", "participant",
                      "runtime_attempt_id", "verifier", "issued_at",
                      "expires_at"), ()),
    # The bearer rides back with the RESULT and never through the store, so the
    # document that carries it is a different document from the one that was
    # committed -- and naming them apart is what keeps the stored shape honest.
    "offer.issued-with-bearer": (("offer_id", "work_id", "participant",
                                  "runtime_attempt_id", "verifier",
                                  "issued_at", "expires_at", "bearer"), ()),
    "offer.settled": (("offer_id", "state", "reason"), ()),
    # LOSING the compare-and-swap is its own answer. It reports the winner's
    # state without rewriting it, and it is not the same document as a
    # settlement this call performed.
    "offer.settled-by-another": (("offer_id", "state", "settled_by_another"),
                                 ()),
    "offer.accepted": (("offer_id", "state", "intent_digest",
                        "claim_operation_id", "claim_signature", "accepted_at",
                        "settle_by"), ()),
    # FOUR CALLERS, one shape. A claim is recorded on submission, late on
    # settlement of a commit this manager never saw, and on adopting another
    # settler's bound disposition -- each contributing different members.
    "claim.recorded": (("offer_id", "state"),
                       ("assignment", "reason", "late", "adopted")),
    # `live`: the identity is still open and nothing changed. Saying so is the
    # honest answer, and it is a document like any other.
    "settlement.observed": (("offer_id", "state", "settled", "why"), ()),
    "offer.recoverable": (("offer_id", "claim_operation_id", "settle_by"), ()),
    "recovery.report": (("abandoned", "recoverable"), ()),
    # -- cut D ---------------------------------------------------------------
    #
    # THE FOUR-PART ASSIGNMENT, built in one place and in the AUTHORITY'S OWN
    # SHAPE. §4: an identity is never a participant alone and never three
    # quarters of one -- and it is never two shapes either. The authority
    # answers with a nested Work reference, so this manager compares and stores
    # the same document rather than a flattened cousin that would have to be
    # translated at every boundary between them.
    "work_ref": (("authority_uuid", "work_id"), ()),
    "assignment": (("work_ref", "participant", "generation"), ()),
    "attempt.recorded": (("attempt_id", "adapter_name", "profile_digest"), ()),
    "assignment.activated": (("attempt_id", "assignment", "already_fixed"),
                             ()),
    # `changed` and `replayed` are different facts and both are answers: an
    # observation that moved nothing is not the same as one that had already
    # been recorded under its source identity.
    "observation": (("attempt_id", "axis", "value", "changed"),
                    ("replayed", "manager_seq")),
    # -- cut D, second slice -------------------------------------------------
    #
    # THE LABELS EVERY RUNTIME THIS MANAGER STARTS MUST CARRY, and all four
    # parts of the assignment are among them: the frozen host omitted the
    # participant, so two participants' runtimes on one Work and generation were
    # indistinguishable by label.
    #
    # W6632 review [P1]: `policy_digest` joins them, and this is the second
    # time this build has extended these labels past the frozen host's set for
    # the same reason. Reconciliation after a restart finds a runtime by these
    # labels and then reasons about WHAT WAS DELIVERED from them, so every
    # member of the resolved identity that the engine cannot report itself has
    # to be here or it does not survive the restart. The engine knows the
    # image it is running and reports it; it has never heard of a policy
    # digest, so a label is the only carrier there is.
    "runtime.labels": (("runtime_attempt_id", "authority_uuid", "work_id",
                        "participant", "generation", "profile_digest",
                        "policy_digest", "adapter_digest"), ()),
    "runtime.start-requested": (("attempt_id", "operation_id"), ()),
    # THREE DECISIONS, THREE DOCUMENTS. A reconciliation answers "attached",
    # "uncertain" or "cancel", and each carries different facts -- one shape
    # covering all three would be a document whose members depend on the branch
    # that built it, which the far end cannot own against anything.
    "runtime.attached": (("attempt_id", "decision", "runtime_id"), ()),
    "runtime.uncertain": (("attempt_id", "decision", "why"), ()),
    "runtime.cancel": (("attempt_id", "decision", "why"), ("runtimes",)),
    "attempt.cancel-intent": (("attempt_id", "assignment",
                               "authority_operation_id", "reason"), ()),
    # ORDERED, NOT DONE. Reaching a boundary is not evidence of its effect, so
    # the two settlements ride back UNINTERPRETED and the manager reports only
    # what it did: it ordered the acts.
    "quiescence.ordered": (("ordered", "runtime_id", "agent_settlement",
                            "runtime_settlement"), ()),
    "quiescence.not-ordered": (("ordered", "why"), ()),
    # NESTED RATHER THAN MERGED. The frozen host spread the intent, the fence
    # and the quiescence answer into one object, so its member set depended on
    # which branch ran. Three named members always present is a document a
    # receiver can own.
    # W6627 adds the SESSION half. Three named members were the three axes a
    # cancellation touches; there are four, and the agent session's own
    # announcement was the one a reader had to infer from its absence.
    "attempt.cancelled": (("intent", "fenced", "session_quiescence",
                           "quiescence"), ()),
    # -- W6592 cut A: composition ---------------------------------------------
    #
    # Certification answers with the profile's own id AND the seal it was
    # certified under. The id is what a reader recognises; the digest is what
    # everything else names, because "the profile we agreed on" is a byte
    # identity rather than a name.
    "profile.agent-session-certified": (("profile_id", "digest"), ()),
    # The NEGOTIATED handshake, in three members the far end can own. The
    # capability document rides as ACP's own wire shape -- W641 keeps one
    # representation and this is it.
    "acp.negotiated": (("wire_version", "client_capabilities",
                        "session_capabilities"), ()),
    # -- W6627: the agent session -------------------------------------------
    #
    # THE §3.1 REFERENCE, in one place. It labels evidence, it is never an
    # assignment identity and it authorizes nothing -- and all FOUR components
    # are always present, because a boundary that binds three quarters of one
    # moves the row held for provider session A on a report about B. The
    # provider id is `null` before the provider names one; absent and null are
    # different documents and only one of them is this.
    "session.ref": (("runtime_attempt_id", "posture", "session_epoch",
                     "provider_session_id"), ()),
    # THE SLOT, read and moved. `moved` says whether THIS act changed it: a
    # retried recovery answers rather than refusing, and "already released" is
    # a different fact from "released by this call".
    "posture.slot": (("attempt_id", "posture", "occupancy", "session_epoch",
                      "reason", "changed_at"), ()),
    "slot.moved": (("attempt_id", "posture", "occupancy", "session_epoch",
                    "moved"), ()),
    # WHAT A SESSION IS WHEN IT IS OPENED. `assignment` is exactly null for a
    # consent session and exactly the four-part identity for an execution one,
    # which is the posture binding the frozen schema states and this document
    # carries rather than implies. Nothing here is the manager's authority
    # handle: rule 3 is that no Baton capability reaches the provider.
    "session.opened": (("agent_session_ref", "profile_digest",
                        "pinned_policy", "work_ref", "assignment",
                        "workspace", "declared_output", "state"), ()),
    "session.provider-adopted": (("agent_session_ref", "adopted"), ()),
    # `moved` rather than a bare state: re-observing the current state is
    # ordinary and answers, and a caller has to be able to tell that from a
    # transition it caused.
    "session.observed": (("agent_session_ref", "state", "moved"), ()),
    # THE CLOSE REPORTS BOTH HALVES SEPARATELY, because "the close landed and
    # the posture did not move" is a real result: a delayed close of epoch 1
    # is a true observation about epoch 1 and is not epoch 2's slot to free.
    "session.closed": (("agent_session_ref", "state", "closed",
                        "slot_occupancy", "released_slot"), ()),
    # §8.4's two refusals are REPORTED as facts rather than left to a caller's
    # memory of the section, and the turn outcome rides back without being
    # recorded -- this boundary never saw the turn.
    "session.transport-lost": (("agent_session_ref", "session_state",
                                "slot_occupancy", "resume", "reprompt",
                                "next_epoch_allowed_without_runtime_"
                                "reidentification", "turn_outcome"), ()),
    # `found` is the adapter's answer and `state` is the axis: an ABSENT
    # session leaves the axis exactly where it was, because absence is not one
    # of the nine and inventing a tenth is how a failed look becomes a claim.
    "session.reconciled": (("agent_session_ref", "found", "state", "moved",
                            "slot"), ()),
    # ORDERED, NOT OBSERVED -- the same rule the runtime quiescence document
    # carries. The manager announced `cancel-requested` on the axis where the
    # table permits it; `agent-quiescent` arrives as an observation or not at
    # all.
    "session.quiescence-requested": (("agent_session_ref", "requested",
                                      "state", "why"), ()),
    # -- W6628: the output freeze and the sealed receiver --------------------
    #
    # THE WHOLE OPERATION IDENTITY, in the frozen §4.2 shape. The id is the
    # retry key and the signature is the BINDING over the kind and every
    # effective operand; an adapter handed only the key cannot echo the
    # binding, and a manager that asks for an echo it never supplied is asking
    # the adapter to guess.
    "operation": (("operation_id", "signature_digest"), ()),
    # `retained` says whether THIS call wrote the bytes. Retention is
    # idempotent by construction -- the key is the digest -- so "already held"
    # and "held by this call" are different facts and both are answers.
    "manifest.retained": (("digest", "schema", "retained"), ()),
    "output.freeze-requested": (("attempt_id", "operation", "disposition"),
                                ()),
    # EVERY OUTPUT IS REPORTED, present or missing. `missing-optional` is a
    # status and not an absence: an output the assignment declared as not
    # required and which did not appear is the worker having been asked and
    # having answered, and a result document that dropped it would lose that.
    "output.answer": (("name", "type", "status"), ()),
    "output.result-frozen": (("attempt_id", "result_id", "manifest_digest",
                              "disposition", "outputs"), ()),
    "output.artifact": (("output_name", "artifact_id", "media_type", "bytes",
                         "content_digest", "locator"), ()),
    # THE INDEXED HALF, and it says so by carrying the digest of the retained
    # document rather than pretending to be it. The content trees, the
    # explicitly missing outputs and the evidence are in the manifest that
    # digest names.
    "output.frozen": (("attempt_id", "result_id", "disposition",
                       "manifest_digest", "freeze_operation_id", "frozen_at",
                       "artifacts"), ()),
    # -- W6629: intake, retention and cleanup --------------------------------
    #
    # THE ASK, journalled before the adapter is called, so a restart can tell
    # "we never asked" from "we asked and do not know what came back".
    "collect.requested": (("attempt_id", "result_id", "operation"), ()),
    # W6629 review [P1]: THE TWO FROZEN COMMANDS THIS MANAGER ISSUES, in the
    # schema's own member order. `outputRetainBody` and `runtimeDestroyBody`
    # each have five required operands; the manager used to type the adapter's
    # capability and then send one of them nothing and the other a bare
    # runtime id, so the side holding the material was told neither what
    # authorized the act nor which protocol operation it was executing.
    "retain.command": (("assignment_ref", "runtime_attempt_id",
                        "artifact_ids", "disposition",
                        "retention_policy_digest"), ()),
    "destroy.command": (("assignment_ref", "runtime_attempt_id", "runtime_id",
                         "intake_receipt_digest",
                         "retention_policy_digest"), ()),
    "intake.artifact": (("artifact_id", "content_digest", "bytes",
                         "custody_locator"), ()),
    # THE RECEIPT, and it is THIS MANAGER'S DOCUMENT.
    #
    # `runtimeDestroyBody.intake_receipt_digest` is a digest of a shape the
    # frozen contract never states -- exactly like the ten `*_policy_digest`
    # members whose documents it also never shapes. The difference is
    # direction: a policy is CONSUMED, so it is bound by identity and never
    # interpreted; a receipt is PRODUCED here, so the producer owns its shape
    # and writes it down.
    #
    # `custody` and `recoverable` are two different reasons material is still
    # on disk and are deliberately not one member: `quarantined` is doubt
    # keeping it, and `recoverable` is a CANCELLED attempt's work being kept so
    # it can be recovered. Merging them would answer "why is this still here?"
    # with "it is still here".
    "intake.receipt": (("attempt_id", "assignment", "result_id",
                        "manifest_digest", "custody", "why", "recoverable",
                        "artifacts", "operation"), ()),
    "retention.decision": (("artifact_id", "disposition",
                            "retention_policy_digest", "decided_at"), ()),
    "retention.decided": (("attempt_id", "artifact_ids", "disposition",
                           "retention_policy_digest", "operation"), ()),
    # BLOCKED IS AN ANSWER, not an error and not a retry: the frozen cleanup
    # axis has `blocked-on-intake`, so cleanup WAITS on intake, and a caller
    # that looped would be inventing a mechanism the axis already has.
    "cleanup.blocked": (("attempt_id", "why"), ()),
    # AND UNSETTLED IS A THIRD ANSWER. An engine account that did not settle
    # what became of the runtime moves nothing, because a cleanup axis that
    # advanced on it would record an ending nobody observed.
    "cleanup.unsettled": (("attempt_id", "state", "why", "operation"), ()),
    "cleanup.settled": (("attempt_id", "cleanup", "state", "why", "kept",
                         "operation"), ()),
    # -- W6627: the operator interrogation split -----------------------------
    #
    # THE REQUEST, journalled before the adapter is asked. Its four bindings
    # are all present because an interrogation that could not name one of them
    # is one nobody can correlate afterwards.
    "interrogation.requested": (("operation_id", "kind", "agent_session_ref",
                                 "assignment", "requested_at", "deadline_at",
                                 "outcome"), ()),
    # THE WHOLE LIFECYCLE, in one shape. `answered` is a fact about whether an
    # answer exists and `published_at` a fact about whether Baton has it --
    # two members because they are two acts, and a committed Baton request is
    # never proof that a model said anything. `observation` carries a probe's
    # control-plane reading and is absent for everything else.
    "interrogation": (("operation_id", "kind", "agent_session_ref",
                       "assignment", "requested_at", "deadline_at", "outcome",
                       "settled_at", "answered", "published_at"),
                      ("observation",)),
}

# The member names of one assignment identity, for the boundaries that own an
# incoming one against the same contract the constructor emits.
ASSIGNMENT = CONTRACTS["assignment"][0]
WORK_REF = CONTRACTS["work_ref"][0]
RUNTIME_LABELS = CONTRACTS["runtime.labels"][0]


def _emit(name, members):
    """Build the named document, in the contract's own member order.

    A missing or unexpected member is a DEFECT in this build rather than
    somebody's bad input, and it is refused rather than assembled: a document
    that does not match its contract is one the far end cannot own.
    """
    required, optional = CONTRACTS[name]
    missing = [member for member in required if member not in members]
    if missing:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build assembled a {name} document without "
            f"{', '.join(missing)}; an answer that does not match its contract "
            f"is one no receiver can own")
    allowed = frozenset(required) | frozenset(optional)
    extra = sorted(member for member in members if member not in allowed)
    if extra:
        raise ContractRefusal(
            "integrity", "schema",
            f"this build assembled a {name} document carrying "
            f"{', '.join(extra)}, which its contract does not name "
            f"({name_value(name)})")
    # THE CONTRACT'S ORDER, not the caller's. Two paths that build the same
    # document must build the same bytes, because these answers are journalled
    # and an exact retry reproduces the stored ones.
    ordered = tuple(required) + tuple(member for member in optional
                                      if member in members)
    return {member: members[member] for member in ordered}


SESSION_REF = CONTRACTS["session.ref"][0]
OPERATION = CONTRACTS["operation"][0]


def profile_certified(**members):
    return _emit("profile.certified", members)


def session_ref(**members):
    return _emit("session.ref", members)


def posture_slot(**members):
    return _emit("posture.slot", members)


def slot_moved(**members):
    return _emit("slot.moved", members)


def session_opened(**members):
    return _emit("session.opened", members)


def provider_session_adopted(**members):
    return _emit("session.provider-adopted", members)


def session_observed(**members):
    return _emit("session.observed", members)


def session_closed(**members):
    return _emit("session.closed", members)


def transport_lost(**members):
    return _emit("session.transport-lost", members)


def session_reconciled(**members):
    return _emit("session.reconciled", members)


def session_quiescence_requested(**members):
    return _emit("session.quiescence-requested", members)


def operation(**members):
    return _emit("operation", members)


def manifest_retained(**members):
    return _emit("manifest.retained", members)


def freeze_requested(**members):
    return _emit("output.freeze-requested", members)


def output_answer(**members):
    return _emit("output.answer", members)


def result_frozen(**members):
    return _emit("output.result-frozen", members)


def output_artifact(**members):
    return _emit("output.artifact", members)


def frozen_output(**members):
    return _emit("output.frozen", members)


def collect_requested(**members):
    return _emit("collect.requested", members)


def retain_command(**members):
    return _emit("retain.command", members)


def destroy_command(**members):
    return _emit("destroy.command", members)


def intake_artifact(**members):
    return _emit("intake.artifact", members)


def intake_receipt(**members):
    return _emit("intake.receipt", members)


def retention(**members):
    return _emit("retention.decision", members)


def retention_decided(**members):
    return _emit("retention.decided", members)


def cleanup_blocked(**members):
    return _emit("cleanup.blocked", members)


def cleanup_unsettled(**members):
    return _emit("cleanup.unsettled", members)


def cleanup_settled(**members):
    return _emit("cleanup.settled", members)


def interrogation_requested(**members):
    return _emit("interrogation.requested", members)


def interrogation(**members):
    # THE OPTIONAL MEMBER IS OMITTED RATHER THAN NULLED when there is no
    # observation: absent and null are different documents, and only one of
    # them says "this operation has no control-plane reading to give".
    if members.get("observation") is None:
        members = {name: value for name, value in members.items()
                   if name != "observation"}
    return _emit("interrogation", members)


def agent_session_certified(**members):
    return _emit("profile.agent-session-certified", members)


def acp_negotiated(**members):
    return _emit("acp.negotiated", members)


def offer_issued(**members):
    return _emit("offer.issued", members)


def offer_bearer(issued, bearer):
    return _emit("offer.issued-with-bearer", dict(issued, bearer=bearer))


def offer_settled(**members):
    return _emit("offer.settled", members)


def offer_settled_by_another(**members):
    return _emit("offer.settled-by-another", members)


def offer_accepted(**members):
    return _emit("offer.accepted", members)


def claim_recorded(**members):
    return _emit("claim.recorded", members)


def settlement_observed(**members):
    return _emit("settlement.observed", members)


def recoverable_offer(**members):
    return _emit("offer.recoverable", members)


def recovery_report(**members):
    return _emit("recovery.report", members)


def work_ref(**members):
    return _emit("work_ref", members)


def assignment(**members):
    return _emit("assignment", members)


def attempt_recorded(**members):
    return _emit("attempt.recorded", members)


def assignment_activated(**members):
    return _emit("assignment.activated", members)


def observation(**members):
    return _emit("observation", members)


def runtime_labels(**members):
    return _emit("runtime.labels", members)


def runtime_start_requested(**members):
    return _emit("runtime.start-requested", members)


def runtime_attached(**members):
    return _emit("runtime.attached", members)


def runtime_uncertain(**members):
    return _emit("runtime.uncertain", members)


def runtime_cancel(**members):
    return _emit("runtime.cancel", members)


def cancel_intent(**members):
    return _emit("attempt.cancel-intent", members)


def quiescence_ordered(**members):
    return _emit("quiescence.ordered", members)


def quiescence_not_ordered(**members):
    return _emit("quiescence.not-ordered", members)


def attempt_cancelled(**members):
    return _emit("attempt.cancelled", members)
