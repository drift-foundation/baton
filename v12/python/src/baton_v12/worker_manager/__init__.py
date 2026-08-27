"""The v12 Worker Manager, in Python.

W4. The manager owns worker control: offers, attempts, runtime and agent state,
output and intake. It owns NO authority state -- it consumes an already-minted,
participant-bound session that trusted deployment supplies, and it never opens
the authority's store, shares its connection, or recomputes a signature the
authority owns.

Cuts B and C are present: the separate control store with its schema marker and
operation journal, and the offer/claim boundary against the injected authority
session. Cut D has begun with the runtime attempt -- its frozen axes, its
journalled observations and the activation that fixes an assignment before
anything writable runs.

Cut D now also carries runtime start, reconciliation and cancellation ordering:
the start operation is journalled before the adapter is called, reconciliation
decides by identity AND by the full labels, and cancellation fences at the
authority before it orders the agent and then the runtime.

W6592 cut A adds the first PUBLIC COMPOSITION: one agent-session profile is
certified by composing shape, document seal and policy in that order, its exact
bytes are filed rather than its digest alone, it is read back only when all
three witnesses agree, and §2.2's client-capability rule is enforced where the
document actually arrives.

W6627's confirmed interrogation split adds `probe` and `inquire`: an immediate
control-plane observation that consumes no model turn, and a conversational
request whose acknowledgement and eventual answer are two separate correlated
facts. Both bind the exact assignment generation, the posture session, an
effectively-once operation identity and a manager-observed deadline; a timeout
is an OBSERVATION and never a cancellation; and the manager publishes any
answer into Baton itself, because the worker holds no Baton capability.

W6628 adds THE OUTPUT FREEZE and the sealed artifact receiver: the four
preconditions read from durable state, the liveness read that can only ever be
a read, an immutable record identity fixed per attempt so the same digest
replays and changed bytes refuse, and the retained manifests a declaration is
finally comparable against. Freezing is not accepting: this ends at `frozen`,
because `invalid` is reachable from there.

W6627 adds THE AGENT SESSION: the nine-state frozen axis, the manager-owned
posture slot beside it, what an agent adapter must answer, and the three kinds
of positive absence -- a provider session observed closed, a provider session
observed ABSENT, and a runtime observed absent. The three vocabularies stay
three: the runtime axis says whether a container is up, the session state says
whether an agent inside it can be prompted, and the posture says which of the
two containers this is.

WHAT IS STILL ABSENT RATHER THAN STUBBED: output freeze, intake and cleanup;
then turns and event normalization. And POSITIVE RUNTIME ABSENCE still cannot
be proven here -- it needs certified adapter evidence a later item defines --
so the retry path stays closed and says so. Session absence is a different
fact and IS provable now; it recovers a posture and satisfies no runtime gate.
"""

from .authority_port import (AuthorityPort, SESSION_MEMBERS,
                             SESSION_OPERATIONS)
from .attempts import (AXES, TRANSITIONS, activate_assignment, observe,
                       reconcile_runtime, record_attempt, request_cancellation,
                       request_runtime_start)
from .offers import (OFFER_TTL_SECONDS, SETTLE_SECONDS, accept_offer,
                     certify_profile, claim_operation_id, claimed_offers_for,
                     expire_overdue, issue_offer, recover_on_restart,
                     settle_claim, submit_claim)
from .handshake import (ACP_CLIENT_CAPABILITIES,
                        ACP_CLIENT_CAPABILITY_MEMBERS, SESSION_CAPABILITIES,
                        certified_agent_session_profile,
                        certify_agent_session_profile,
                        check_client_capabilities, negotiate_acp)
from .posture_slots import (RECOVERY_EVIDENCE, posture_slot, release_slot,
                            require_slot_recovery)
from .sessions import (AGENT_ADAPTER, SESSION_OBSERVATIONS, SESSION_STATES,
                       SESSION_SUCCESSORS, TERMINAL_SESSION_STATES,
                       adopt_provider_session, agent_sessions_of,
                       close_agent_session, handle_transport_loss,
                       observe_session_state, open_agent_session,
                       permits_session_transition, reconcile_agent_session,
                       reprompt_after_transport_loss,
                       satisfies_runtime_quiescence_gate,
                       transport_reachability_reidentifies)
from .interrogation import (INTERROGATION_KINDS, inquire,
                            interrogation_of, interrogations_of, probe,
                            publish_inquiry_answer, record_inquiry_answer,
                            settle_interrogation)
from .manifests import load_manifest, retain_manifest
from .output import (freeze_operation, frozen_output_of, record_frozen_result,
                     request_freeze)
from .intake import (KEEPS_MATERIAL, authorize_cleanup, collect_operation,
                     decide_retention, destroy_operation, intake_operation,
                     intake_receipt_of, record_intake, request_intake,
                     retain_operation, retentions_of)
from .schema import (CUSTODY, DISPOSITIONS, OUTPUT_STATUSES, OUTPUT_TYPES,
                     POSTURES, RETENTION_DISPOSITIONS, SCHEMA_VERSION,
                     SLOT_OCCUPANCY, STORE_KIND, TABLES)
from .store import (ControlStore, manager_signature, revive_refusal,
                    seal_refusal)

__all__ = ["CUSTODY", "KEEPS_MATERIAL", "RETENTION_DISPOSITIONS",
           "authorize_cleanup", "collect_operation", "decide_retention",
           "destroy_operation", "intake_operation", "intake_receipt_of",
           "record_intake", "request_intake", "retain_operation",
           "retentions_of",
           "ACP_CLIENT_CAPABILITIES", "ACP_CLIENT_CAPABILITY_MEMBERS",
           "AGENT_ADAPTER", "DISPOSITIONS", "INTERROGATION_KINDS",
           "inquire", "interrogation_of", "interrogations_of", "probe",
           "publish_inquiry_answer", "record_inquiry_answer",
           "settle_interrogation",
           "OUTPUT_STATUSES",
           "OUTPUT_TYPES", "POSTURES", "RECOVERY_EVIDENCE",
           "freeze_operation", "frozen_output_of", "load_manifest",
           "record_frozen_result", "request_freeze", "retain_manifest",
           "SESSION_OBSERVATIONS", "SESSION_STATES", "SESSION_SUCCESSORS",
           "SLOT_OCCUPANCY", "TERMINAL_SESSION_STATES",
           "adopt_provider_session", "agent_sessions_of",
           "close_agent_session", "handle_transport_loss",
           "observe_session_state", "open_agent_session", "posture_slot",
           "permits_session_transition", "reconcile_agent_session",
           "release_slot", "reprompt_after_transport_loss",
           "require_slot_recovery", "satisfies_runtime_quiescence_gate",
           "transport_reachability_reidentifies",
           "AXES", "AuthorityPort", "ControlStore", "OFFER_TTL_SECONDS",
           "SESSION_CAPABILITIES", "certified_agent_session_profile",
           "certify_agent_session_profile", "check_client_capabilities",
           "negotiate_acp",
           "SESSION_MEMBERS", "SESSION_OPERATIONS", "SCHEMA_VERSION",
           "SETTLE_SECONDS", "STORE_KIND", "TABLES", "TRANSITIONS",
           "accept_offer", "activate_assignment", "certify_profile",
           "claim_operation_id", "claimed_offers_for", "expire_overdue",
           "issue_offer", "manager_signature", "observe",
           "reconcile_runtime", "record_attempt", "recover_on_restart",
           "request_cancellation", "request_runtime_start", "revive_refusal",
           "seal_refusal", "settle_claim", "submit_claim"]
