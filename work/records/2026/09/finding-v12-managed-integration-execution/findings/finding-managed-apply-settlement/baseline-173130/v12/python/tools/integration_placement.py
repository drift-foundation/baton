"""W161230 slice1, condition 5: the ONE local interface that may put a managed
integration's collected bytes on a target.

WHY A TRUSTED OWNER EXISTS AT ALL. A managed phase runs somewhere else. What
comes back from it is a report and a content digest -- untrusted input, by
construction, because the thing that produced it is the thing under test. The
node holding the target is a different node with different capabilities, and
publication is ITS act: it resolves the configured target locally, proves the
grant it holds at that moment, proves the execution it is publishing has
stopped, and only then performs the compare-and-swap the existing profile
already owns.

WHAT A WORKER CANNOT DO, stated as the boundary rather than as advice. A worker
output carries no Authority session, no target capability and no authority to
refresh a grant. A worker's own stop report, a stop order somebody sent, a
timeout that elapsed and a runtime belonging to a different coordinator are all
things that can be true while the execution is still writing; none of them
reaches the proof below, which is the manager's own durable observation that
this exact runtime is gone.

THE COMPARE-AND-SWAP IS AGAINST THE ADMITTED OLD REVISION, never against
whatever the reference currently says. Those are the same value in the ordinary
case and different exactly when something moved the target underneath this
integration -- which is the case the swap exists for. Reading the current ref
and passing it as the expected old value would turn the one safety here into a
formality that always succeeds.

WHAT THIS COMPOSES RATHER THAN REPLACES: `queue.live_grant` and
`queue.settle_integrated` own the grant and the settlement; the integration
profile owns the reference advance; `reconciliation.managed_result_of` owns the
managed custody record and proves it against its journal;
`worker_manager.attempts.attempt_runtime_of` owns the runtime axis. This adds
no new store, no second lock, no remote backend and no credential copy.
"""

import json
import os

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts.errors import name_value
from baton_v12.integration.queue import (_settlement, entries_of,
                                         live_grant, settle_integrated)
from baton_v12.integration.reconciliation import (
    managed_result_of, publication_of, record_publication_effect,
    record_publication_intent)
from baton_v12.worker_manager import boundaries
from baton_v12.worker_manager.attempts import attempt_runtime_of

__all__ = ["PLACEMENT_SCHEMA", "PUBLISHED_MEMBERS", "STOPPED",
           "EXCLUSION_SCHEMA", "EXCLUSION_MEMBERS", "AUTHORIZATION_SCHEMA",
           "AUTHORIZATION_MEMBERS", "TARGET_SCHEMA", "TARGET_MEMBERS",
           "TARGET_ANSWERS", "LocalTargetPlacement",
           "publish_collected_integration"]

# WHAT THE EXECUTION OWNER ON THE EXECUTING NODE MUST ANSWER. Gate 4 of the
# accepted design response: a locally composed capability that obtains POSITIVE
# EXCLUSION from the trusted runtime adapter on the node that ran the exact
# phase, binding the assignment, the attempt, the START OPERATION, the RUNTIME
# IDENTITY and the frozen collected phase reference.
#
# THE WORKER'S OWN REPORT IS NOT THIS. Neither is a stop order, an elapsed
# timeout or a runtime belonging to another coordinator. Every one of those can
# be true while the execution is still writing, which is why this answer comes
# from the adapter that owns the runtime rather than from the thing under test.
EXCLUSION_SCHEMA = "baton.v12.managed-exclusion/1"
EXCLUSION_MEMBERS = ("schema", "attempt_id", "assignment",
                     "start_operation_id", "runtime_id", "content_digest",
                     "excluded")

# AND WHAT THE AUTHORIZATION OWNER MUST ANSWER. A measured worker report says
# the harness passed; it does not say anybody approved the derived candidate,
# and publication needs both. These are separate owners because they answer
# separate questions, and one standing in for the other is the substitution
# this gate exists to refuse.
# AND WHAT THE TARGET OWNER ANSWERS, for the act AND for the recovery.
#
# REVIEW 2026-09-14T00:26:30Z [P1]: with an intent recorded, the reference
# cannot prove anything. A target back at the admitted old revision is equally
# consistent with "the advance never ran" and with "it ran and something moved
# the target back", and issuing another compare-and-swap on the strength of the
# current value is exactly the second mutation this interface exists to avoid.
#
# SO THE EFFECT AND ITS RECEIPT ARE ONE BOUNDARY. The owner that applies the
# change is the owner that can say afterwards whether it applied, and it
# answers with a receipt bound to the publication -- not a sidecar written
# after an ordinary advance, which is a second act that can itself be lost.
#
# THREE ANSWERS, AND `unknown` IS ONE OF THEM. An owner that cannot tell says
# so, and this interface keeps the uncertainty rather than choosing the
# reading it prefers.
TARGET_SCHEMA = "baton.v12.managed-target-effect/1"
TARGET_ANSWERS = ("applied", "not-applied", "unknown")
TARGET_MEMBERS = ("schema", "publication_id", "canonical_target_id",
                  "admitted_old_revision", "imported_revision",
                  "content_digest", "derived_proposal_id", "answer",
                  "receipt")

AUTHORIZATION_SCHEMA = "baton.v12.managed-authorization/1"
AUTHORIZATION_MEMBERS = ("schema", "managed_result_id",
                         "canonical_target_id", "derived_proposal_id",
                         "derived_result_id", "derived_result_digest",
                         "content_digest", "approved")

PLACEMENT_SCHEMA = "baton.v12.managed-placement/1"

PUBLISHED_MEMBERS = ("schema", "canonical_target_id", "entry_id", "lease_id",
                     "fence", "managed_result_id", "phase",
                     "admitted_old_revision", "imported_revision",
                     "content_digest", "derived_proposal_id", "settlement",
                     "outcome")

# HOW A PUBLICATION ENDED, as three answers rather than one. `published` did
# the swap and settled; `replayed` found this exact publication already
# settled and performed nothing; `resumed` found its OWN swap committed and no
# settlement, and completed only the part that was missing.
#
# THE THIRD IS NOT AN AUTOMATIC ROLLBACK AND DOES NOT PRETEND TO BE. A
# compare-and-swap that committed cannot be undone by this interface; what it
# can do is refuse to swap twice and finish what it started.
OUTCOMES = ("published", "replayed", "resumed")

# THE ONE RUNTIME ANSWER THAT AUTHORIZES A PUBLICATION. `quiescent` is a
# runtime observed to have stopped executing and STILL EXISTING; `uncertain` is
# the manager saying it does not know. Neither says the thing this act needs to
# be true -- that nothing can still be writing what is about to be published.
STOPPED = "destroyed"


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


class LocalTargetPlacement:
    """The trusted capabilities of the node that holds one target.

    COMPOSED AT THE NODE, NEVER SENT. Each member is something this process
    already has because of where it runs: the coordinator it can open, the
    manager whose runtime rows it holds, the profile wired for this target, the
    configured repository and reference, a materializer that can turn a
    collected content digest into a local revision, an EXECUTION OWNER that can
    ask the executing node's adapter whether the runtime is positively
    excluded, and an AUTHORIZATION owner that can say whether the derived
    candidate was approved.

    THE LAST THREE ARE DIFFERENT RESPONSIBILITIES AND NONE SUBSTITUTES FOR
    ANOTHER. Fetching content is not proving the writer stopped, and proving
    the writer stopped is not approval to publish what it wrote.
    """

    def __init__(self, *, coordinator, manager, profile, materializer,
                 execution_owner, authorization, target_owner, repository,
                 reference):
        self.coordinator = coordinator
        self.manager = manager
        self.profile = profile
        # CAPABILITIES, not paths or documents. "Fetch the collected content",
        # "ask the adapter whether this runtime is gone" and "say whether this
        # candidate was approved" are acts THIS node can perform; an operand
        # describing any of them would be the caller composing its own
        # authorization.
        boundaries.capability(getattr(materializer, "materialize", None),
                              "the collected-content materializer")
        boundaries.capability(getattr(execution_owner, "exclusion_of", None),
                              "the execution owner's exclusion")
        boundaries.capability(getattr(authorization, "authorized", None),
                              "the authorization owner")
        # THE ONE OWNER THAT BOTH APPLIES THE CHANGE AND REMEMBERS IT. Two
        # capabilities here -- one to act, one to report -- would be two acts
        # that can disagree, which is the shape this gate exists to close.
        boundaries.capability(getattr(target_owner, "apply", None),
                              "the target owner's apply")
        boundaries.capability(getattr(target_owner, "recover", None),
                              "the target owner's recovery")
        self.target_owner = target_owner
        self.materializer = materializer
        self.execution_owner = execution_owner
        self.authorization = authorization
        self.repository = boundaries.text(repository,
                                          "the configured target repository")
        self.reference = boundaries.text(reference,
                                         "the configured target reference")

    def configured(self):
        """The target this node actually holds, refusing if it does not."""
        if not os.path.isdir(self.repository):
            _refuse(f"this node has no target repository at "
                    f"{name_value(self.repository)}; a placement publishes "
                    f"into the target it was configured with and creates none")
        return self.profile.revision(self.repository, self.reference)


class LocalGitTargetOwner:
    """The local target effect and its receipt share one Git transaction.

    Configuration and all receipt operands come from the node's owners. The
    worker supplies neither a repository/ref nor an effect receipt. Recovery
    reads the receipt without retrying a target transaction.
    """

    def __init__(self, *, coordinator, manager, profile, execution_owner,
                 authorization, repository, reference, managed_result_id):
        self.coordinator = coordinator
        self.manager = manager
        self.profile = profile
        self.execution_owner = execution_owner
        self.authorization = authorization
        self.repository = repository
        self.reference = reference
        self.managed_result_id = managed_result_id

    def _binding(self, operands):
        request = boundaries.document(operands, "the local target publication", required=(
            "publication_id", "canonical_target_id", "admitted_old_revision",
            "imported_revision", "content_digest", "derived_proposal_id"))
        published = publication_of(self.coordinator, self.managed_result_id, "apply")
        if published is None or any(published[name] != value for name, value in request.items()):
            _denied("the target request does not match its journalled publication")
        result = managed_result_of(self.coordinator, self.managed_result_id)
        account = result["phases"].get("apply")
        if account is None or account["result"]["collected"] is None:
            _denied("the target publication has no collected apply")
        collected = account["result"]["collected"]
        excluded = _excluded(self, account, collected)
        authorized = _authorized(self, self.managed_result_id, request["canonical_target_id"], collected)
        if authorized["derived_proposal_id"] != request["derived_proposal_id"]:
            _denied("the publication and authorization name different derived proposals")
        return {"schema": "baton.v12.local-target-receipt/1", "publication": request,
                "repository": self.profile.storage(self.repository), "reference": self.reference,
                "managed_result_id": self.managed_result_id,
                "entry_id": published["entry_id"], "lease_id": published["lease_id"], "fence": published["fence"],
                "authorization": authorized, "exclusion": excluded,
                "preparation": result["phases"].get("prepare"), "apply": account}

    @staticmethod
    def _answer(binding, receipt):
        return {"schema": TARGET_SCHEMA, **binding["publication"],
                "answer": "unknown" if receipt is None else "applied",
                "receipt": None if receipt is None else receipt["object"]}

    def recover(self, operands):
        binding = self._binding(operands)
        receipt = self.profile.publication_receipt(self.repository, publication_id=operands["publication_id"])
        if receipt is not None and receipt["document"] != binding:
            _denied("the target publication receipt has different bound operands")
        return self._answer(binding, receipt)

    def apply(self, operands):
        binding = self._binding(operands)
        receipt = self.profile.publication_receipt(self.repository, publication_id=operands["publication_id"])
        if receipt is not None:
            if receipt["document"] != binding:
                _denied("the target publication receipt has different bound operands")
            return self._answer(binding, receipt)

        def current_grant():
            live_grant(self.coordinator, canonical_target_id=operands["canonical_target_id"],
                       entry_id=binding["entry_id"], lease_id=binding["lease_id"], fence=binding["fence"])

        receipt = self.profile.publish_with_receipt(
            self.repository, reference=self.reference, imported=operands["imported_revision"],
            reviewed=operands["admitted_old_revision"], publication_id=operands["publication_id"],
            receipt=binding, before_commit=current_grant)
        return self._answer(binding, receipt)


def _target_answer(placement, act, operands):
    """The target owner's own closed answer, for an act or for a recovery."""
    answer = act(dict(operands))
    if answer is None:
        _refuse(f"the target owner answered nothing for publication "
                f"{name_value(operands['publication_id'])}; an unavailable "
                f"owner leaves this uncertain rather than deciding it")
    held = boundaries.document(answer, "the target owner's answer",
                               required=TARGET_MEMBERS)
    if held["schema"] != TARGET_SCHEMA:
        _refuse(f"a target effect is {name_value(TARGET_SCHEMA)}; this is "
                f"{name_value(held['schema'])}", category="integrity",
                code="schema")
    if held["answer"] not in TARGET_ANSWERS:
        _refuse(f"a target effect is one of {', '.join(TARGET_ANSWERS)}; this "
                f"is {name_value(held['answer'])}", category="integrity",
                code="schema")
    for member in ("publication_id", "canonical_target_id",
                   "admitted_old_revision", "imported_revision",
                   "content_digest", "derived_proposal_id"):
        if held[member] != operands[member]:
            _denied(f"the target owner answered about {member} "
                    f"{name_value(held[member])} and this publication is "
                    f"{name_value(operands[member])}; an owner's answer about "
                    f"something else is not an answer about this")
    if held["answer"] == "applied":
        # A RECEIPT IS REQUIRED FOR THE ONLY ANSWER THAT CLAIMS AN EFFECT, and
        # it is the owner's -- this interface does not compose one.
        boundaries.text(held["receipt"], "the target owner's receipt")
    elif held["receipt"] is not None:
        _refuse(f"the target owner answered {name_value(held['answer'])} and "
                f"carries a receipt; a receipt accounts for an effect that "
                f"happened", category="integrity", code="schema")
    return held


def _excluded(placement, account, collected):
    """POSITIVE EXCLUSION from the node that ran the phase, bound to it.

    The manager's own axis is asked as well, and the two must agree: the
    adapter says the runtime is gone, the manager's durable row says the same,
    and both name the SAME runtime. One of those alone is a single owner's
    word about its own work.
    """
    attempt_id = account["task"]["execution_attempt_id"]
    answer = placement.execution_owner.exclusion_of(
        {"attempt_id": attempt_id, "assignment": account["task"]["assignment"],
         "content_digest": collected["manifest_digest"]})
    if answer is None:
        _denied(f"the execution owner for attempt {name_value(attempt_id)} "
                f"answered nothing; an unavailable owner refuses a "
                f"publication rather than authorizing one")
    held = boundaries.document(answer, "the execution owner's exclusion",
                               required=EXCLUSION_MEMBERS)
    if held["schema"] != EXCLUSION_SCHEMA:
        _refuse(f"an exclusion is {name_value(EXCLUSION_SCHEMA)}; this is "
                f"{name_value(held['schema'])}", category="integrity",
                code="schema")
    if held["excluded"] is not True:
        _denied(f"the execution owner reports exclusion "
                f"{name_value(held['excluded'])} for attempt "
                f"{name_value(attempt_id)}; only a positive exclusion "
                f"publishes")
    for member, expected in (
            ("attempt_id", attempt_id),
            ("assignment", account["task"]["assignment"]),
            ("content_digest", collected["manifest_digest"])):
        if held[member] != expected:
            _denied(f"the exclusion names {member} "
                    f"{name_value(held[member])} and this phase is "
                    f"{name_value(expected)}; an owner's answer about "
                    f"something else is not an answer about this")
    boundaries.identity(held["runtime_id"], "the excluded runtime")
    boundaries.identity(held["start_operation_id"], "the start operation")
    # AND THE START IT NAMES IS A COMMITTED START IN THIS MANAGER'S JOURNAL.
    # A runtime identity with no start behind it is a runtime nobody in this
    # deployment is recorded as having launched.
    started = placement.manager.operation_record(held["start_operation_id"])
    if started is None or started["state"] != "committed" \
            or started["kind"] != "runtime.start":
        _denied(f"the exclusion names start operation "
                f"{name_value(held['start_operation_id'])} and this manager "
                f"holds no committed runtime start there; a publication "
                f"follows an execution this deployment actually launched")
    # AND IT IS THIS ATTEMPT'S START. Review 2026-09-14T00:04:25Z: any
    # committed act of that kind satisfied the check, so a start belonging to
    # another attempt would have done -- "a runtime.start exists" is not "this
    # runtime was started".
    try:
        launched = json.loads(started["signature"])["operands"]
    except (TypeError, ValueError, KeyError):
        launched = None
    if type(launched) is not dict \
            or launched.get("attempt_id") != attempt_id:
        _denied(f"the start operation "
                f"{name_value(held['start_operation_id'])} was signed over "
                f"attempt {name_value((launched or {}).get('attempt_id'))} "
                f"and this phase is {name_value(attempt_id)}")
    # AND THE MANAGER'S OWN ROW AGREES, about the same runtime.
    runtime = attempt_runtime_of(placement.manager, attempt_id)
    if runtime is None:
        _denied(f"this manager holds no attempt {name_value(attempt_id)}; "
                f"absence of a record is not absence of a runtime, and "
                f"nothing publishes behind an execution nobody can account "
                f"for")
    if runtime["execution_runtime"] != STOPPED:
        _denied(f"attempt {name_value(attempt_id)} execution is "
                f"{name_value(runtime['execution_runtime'])}; a publication "
                f"needs the runtime positively observed "
                f"{name_value(STOPPED)}, and a worker's own stop report, a "
                f"stop order or an elapsed timeout is not that observation")
    if runtime["runtime_id"] is None:
        _denied(f"attempt {name_value(attempt_id)} has no attached runtime; "
                f"an execution that never attached one has no runtime to be "
                f"excluded from, and this is not the shape a publication "
                f"follows")
    if runtime["runtime_id"] != held["runtime_id"]:
        _denied(f"the execution owner excluded runtime "
                f"{name_value(held['runtime_id'])} and this manager records "
                f"{name_value(runtime['runtime_id'])} for attempt "
                f"{name_value(attempt_id)}")
    if runtime["assignment"] != account["task"]["assignment"]:
        _denied(f"attempt {name_value(attempt_id)} is fixed to "
                f"{name_value(runtime['assignment'])} and this phase was "
                f"composed for {name_value(account['task']['assignment'])}")
    return held


def _authorized(placement, managed_result_id, canonical_target_id, collected):
    """The APPROVED derived candidate for this result, from its own owner.

    A measured worker report says the harness passed. It does not say anybody
    approved publishing the bytes, and the accepted request carries both.
    """
    answer = placement.authorization.authorized(
        {"managed_result_id": managed_result_id,
         "canonical_target_id": canonical_target_id,
         "content_digest": collected["manifest_digest"]})
    if answer is None:
        _denied(f"no authorization owner answered for managed result "
                f"{name_value(managed_result_id)}; an unavailable owner "
                f"refuses a publication rather than authorizing one")
    held = boundaries.document(answer, "the candidate authorization",
                               required=AUTHORIZATION_MEMBERS)
    if held["schema"] != AUTHORIZATION_SCHEMA:
        _refuse(f"an authorization is {name_value(AUTHORIZATION_SCHEMA)}; "
                f"this is {name_value(held['schema'])}",
                category="integrity", code="schema")
    if held["approved"] is not True:
        _denied(f"the derived candidate for "
                f"{name_value(managed_result_id)} is not approved; a "
                f"publication carries content somebody independently "
                f"authorized")
    for member, expected in (
            ("managed_result_id", managed_result_id),
            ("canonical_target_id", canonical_target_id),
            ("content_digest", collected["manifest_digest"])):
        if held[member] != expected:
            _denied(f"the authorization names {member} "
                    f"{name_value(held[member])} and this publication is "
                    f"{name_value(expected)}")
    for member in ("derived_proposal_id", "derived_result_id"):
        boundaries.identity(held[member], f"the authorized {member}")
    boundaries.text(held["derived_result_digest"],
                    "the authorized derived result digest")
    return held


def _eligible(entry, held, authorized, collected):
    """The entry this publication settles is THIS submission's own.

    REVIEW 2026-09-14T00:04:25Z [P1]: nothing related the selected entry to
    the managed result at all, so content prepared for one submission
    published and SETTLED an unrelated entry that happened to have a valid
    lease. A grant says this caller may write the target; it does not say
    which queued work the bytes answer.

    THE ENTRY'S OWN ELIGIBILITY IS THE OWNER OF THAT QUESTION. It carries the
    submission's identities as the queue admitted them, and the managed result
    carries the same identities as reconciliation recorded them. They are
    compared by NAME, member for member -- not by hoping a digest family
    matches, and not by relating a source identity to a derived one, which are
    different objects with different lifetimes.
    """
    account = entry.get("eligibility")
    if type(account) is not dict:
        _refuse(f"entry {name_value(entry['entry_id'])} carries no "
                f"eligibility account; the queue's own record of which "
                f"submission this entry is for is what a publication answers")
    for mine, theirs in (("authority_uuid", "authority_uuid"),
                         ("work_id", "work_id"),
                         ("line_id", "line_id"),
                         ("source_checkpoint_id", "checkpoint_id"),
                         ("source_verdict_id", "verdict_id"),
                         ("source_proposal_id", "proposal_id"),
                         ("source_result_id", "result_id"),
                         ("source_result_digest", "result_digest"),
                         ("source_checkpoint_digest", "checkpoint_digest")):
        if held[mine] != account.get(theirs):
            _denied(f"entry {name_value(entry['entry_id'])} is queued for "
                    f"{theirs} {name_value(account.get(theirs))} and this "
                    f"managed result is for {name_value(held[mine])}; a live "
                    f"grant says this node may write the target, not which "
                    f"queued work these bytes answer")
    # AND THE ENTRY WAS ADMITTED AGAINST THE SAME TARGET SNAPSHOT.
    if account.get("expected_target_revision") != held["target_revision"]:
        _denied(f"entry {name_value(entry['entry_id'])} expects target "
                f"revision {name_value(account.get('expected_target_revision'))} "
                f"and this result was reconciled against "
                f"{name_value(held['target_revision'])}")


def publish_collected_integration(placement, *, canonical_target_id, entry_id,
                                  lease_id, fence, admitted_old_revision,
                                  managed_result_id, phase="apply",
                                  settlement):
    """Publish ONE managed phase's collected content, or refuse before writing.

    THE ORDER IS THE WHOLE DESIGN, and everything before the swap is a refusal
    that leaves the target exactly as it was:

      1. the WHOLE IMMUTABLE REQUEST, owned before any effect -- including the
         settlement, through the settlement owner's own rule. Review
         2026-09-13T23:50:10Z [P1]: it was passed to `settle_integrated` AFTER
         the swap, so a malformed one moved the reference and then refused;
      2. the managed result, through its own owner, which proves it against
         the journal that made it;
      3. the phase's report -- a MEASURED success with nothing left unrun;
      4. POSITIVE EXCLUSION from the executing node's own owner, bound to the
         assignment, attempt, start operation, runtime identity and collected
         content, and agreeing with this manager's durable row;
      5. the APPROVED derived candidate, from its own owner;
      6. where this publication already stands -- settled, or swapped and not
         settled, or not begun;
      7. the content, materialized locally from its digest;
      8. the LIVE GRANT, at the canonical mutation boundary. Review [P1]: it
         was proved before materialization, and a grant released while content
         resolved let the target advance under a lease already ended;
      9. the compare-and-swap, against the ADMITTED old revision;
     10. the settlement, which is the second of the two grant cutpoints.
    """
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(entry_id, "an entry id")
    boundaries.identity(lease_id, "a lease id")
    boundaries.identity(managed_result_id, "a managed result identity")
    boundaries.text(admitted_old_revision, "the admitted old revision")
    if type(fence) is not int or type(fence) is bool or fence < 1:
        _refuse(f"a grant fence is a whole number from one; this is "
                f"{name_value(fence)}", category="integrity", code="schema")
    # 1. THE SETTLEMENT, THROUGH ITS OWN OWNER, BEFORE ANY EFFECT. The rule is
    #    `queue`'s, not a duplicate spelled here: one lock, and both doors use
    #    it.
    settled_request = _settlement(settlement, "integrated",
                                  "this publication's settlement")

    # 2. THE CUSTODY RECORD, THROUGH ITS OWNER.
    held = managed_result_of(placement.coordinator, managed_result_id)
    if held["canonical_target_id"] != canonical_target_id:
        _denied(f"managed result {name_value(managed_result_id)} is for "
                f"target {name_value(held['canonical_target_id'])} and this "
                f"placement holds {name_value(canonical_target_id)}")
    if held["target_revision"] != admitted_old_revision:
        _denied(f"managed result {name_value(managed_result_id)} was "
                f"reconciled against {name_value(held['target_revision'])} "
                f"and this publication names "
                f"{name_value(admitted_old_revision)}")
    account = held["phases"].get(phase)
    if account is None:
        _refuse(f"managed result {name_value(managed_result_id)} retains no "
                f"{name_value(phase)} phase; there is nothing to publish")

    # 3. THE REPORT, WHICH MUST SAY THE HARNESS ACTUALLY PASSED.
    report = account["result"]["report"]
    if report["kind"] != "measured":
        _denied(f"the {phase} phase reports {name_value(report['kind'])}; a "
                f"report collected without a status, and the absence of a "
                f"report, are answers about what was OBSERVED and neither "
                f"authorizes a publication")
    if report["status"] != 0:
        _denied(f"the {phase} phase measured status "
                f"{name_value(report['status'])}; a publication carries "
                f"content whose own harness succeeded")
    if report["not_run"]:
        _denied(f"the {phase} phase did not run "
                f"{name_value(report['not_run'])}; a sequence that stopped "
                f"partway is not a shorter sequence that passed")
    collected = account["result"]["collected"]
    if collected is None:
        _refuse(f"the {phase} phase collected no content; there is nothing to "
                f"publish and absence is not an empty result")

    # 4 and 5. THE TWO TRUSTED OWNERS. Neither substitutes for the other, and
    #          a measured worker report substitutes for neither.
    exclusion = _excluded(placement, account, collected)
    authorized = _authorized(placement, managed_result_id,
                             canonical_target_id, collected)

    # 6. THE ENTRY THIS SETTLES, and that it is this submission's own.
    standing = placement.configured()
    entries = entries_of(placement.coordinator, canonical_target_id)
    entry = next((one for one in entries if one["entry_id"] == entry_id), None)
    if entry is None:
        _refuse(f"target {name_value(canonical_target_id)} holds no entry "
                f"{name_value(entry_id)}")
    _eligible(entry, held, authorized, collected)

    def answer(outcome, imported, settled):
        return {"schema": PLACEMENT_SCHEMA,
                "canonical_target_id": canonical_target_id,
                "entry_id": entry_id, "lease_id": lease_id, "fence": fence,
                "managed_result_id": managed_result_id, "phase": phase,
                "admitted_old_revision": admitted_old_revision,
                "imported_revision": imported,
                "content_digest": collected["manifest_digest"],
                "derived_proposal_id": authorized["derived_proposal_id"],
                "settlement": settled, "outcome": outcome}

    # 7. WHERE THIS PUBLICATION ALREADY STANDS, from its OWN durable record.
    #    Review 2026-09-14T00:04:25Z: this was inferred from the target's
    #    current revision, so a foreign move onto the same revision was
    #    adopted as an owned swap, a completed retry accepted an unrelated
    #    lease and fence, and a retry after later movement reported a foreign
    #    revision as its own imported outcome. A materializer mapping proves
    #    what content IS; only a record written before the mutation says who
    #    moved a reference.
    recorded = publication_of(placement.coordinator, managed_result_id, phase)
    if recorded is not None:
        for member, given in (("canonical_target_id", canonical_target_id),
                              ("entry_id", entry_id),
                              ("lease_id", lease_id), ("fence", fence),
                              ("admitted_old_revision", admitted_old_revision),
                              ("content_digest", collected["manifest_digest"]),
                              ("derived_proposal_id",
                               authorized["derived_proposal_id"]),
                              ("settlement", settled_request)):
            if recorded[member] != given:
                _denied(f"this publication of "
                        f"{name_value(managed_result_id)} is already recorded "
                        f"with {member} {name_value(recorded[member])} and "
                        f"this request names {name_value(given)}; a retry of "
                        f"one publication is not a second account of it")
        if recorded["state"] == "settled":
            # NOTHING IS RESOLVED, NOTHING IS SWAPPED, AND THE ANSWER IS THE
            # RECORDED ONE -- including the revision this publication actually
            # imported, rather than whatever the target says now.
            return answer("replayed", recorded["imported_revision"],
                          recorded["settlement"])

    imported = placement.materializer.materialize(
        {"canonical_target_id": canonical_target_id,
         "managed_result_id": managed_result_id, "phase": phase,
         "content_digest": collected["manifest_digest"],
         "result_id": collected["result_id"]})
    if imported is None:
        _refuse(f"this node holds no collected content for "
                f"{name_value(collected['manifest_digest'])}; a publication "
                f"imports bytes this node actually has")
    boundaries.text(imported, "the materialized revision")

    if recorded is not None and recorded["imported_revision"] != imported:
        _denied(f"this publication recorded that it would import "
                f"{name_value(recorded['imported_revision'])} and now "
                f"resolves {name_value(imported)}; the content a publication "
                f"is about does not change between its attempts")
    # AND WHERE THIS PUBLICATION STANDS IS ITS RECORDED STATE, not a reading
    # of the target. INTENT IS NOT PROOF OF EFFECT, and neither is the
    # reference: a target back at the admitted old revision is equally
    # consistent with "the advance never ran" and with "it ran and something
    # moved the target back". Only the owner that applies the change can say.
    swapped = recorded is not None and recorded["state"] in ("swapped",
                                                             "settled")
    if swapped and standing != recorded["imported_revision"]:
        _denied(f"this publication's swap to "
                f"{name_value(recorded['imported_revision'])} is recorded and "
                f"the target now stands at {name_value(standing)}; something "
                f"moved it afterwards, and a recorded swap is never performed "
                f"a second time")
    # WHAT WE ARRIVED TO, kept separate from what we then did. Measured, step
    # 144: reusing one flag for "already swapped when we got here" and "the
    # swap has now happened" made a fresh publication answer `resumed`.
    # THE OUTCOME IS ABOUT THIS CALL: `published` means this call performed
    # the effect, `resumed` means it found one already done and completed what
    # was missing -- which a recovery answering `applied` is, exactly as an
    # already-recorded swap is.
    performed = False
    placed_already = recorded["imported_revision"] if swapped else None
    if recorded is None and standing != admitted_old_revision:
        _denied(f"the configured target is at {name_value(standing)} and "
                f"this publication was admitted against "
                f"{name_value(admitted_old_revision)}; something else "
                f"moved the target, and the swap is not retried against "
                f"whatever is there now")

    # 9. THE INTENT, COMMITTED BEFORE THE SWAP, and then the swap ONCE. A
    #    publication resuming after its own committed CAS does not swap again:
    #    that swap is not undoable, and re-running it against a new old
    #    revision is how a resume becomes a second mutation.
    resuming = recorded is not None and recorded["state"] == "intended"
    if recorded is None:
        recorded = record_publication_intent(
            placement.coordinator,
            {"managed_result_id": managed_result_id, "phase": phase,
             "canonical_target_id": canonical_target_id, "entry_id": entry_id,
             "lease_id": lease_id, "fence": fence,
             "admitted_old_revision": admitted_old_revision,
             "imported_revision": imported,
             "content_digest": collected["manifest_digest"],
             "derived_proposal_id": authorized["derived_proposal_id"],
             "settlement": settled_request})
    request = {"publication_id": recorded["publication_id"],
               "canonical_target_id": canonical_target_id,
               "admitted_old_revision": admitted_old_revision,
               "imported_revision": imported,
               "content_digest": collected["manifest_digest"],
               "derived_proposal_id": authorized["derived_proposal_id"]}
    if swapped:
        placed = placed_already
    else:
        if resuming:
            # AN INTENT THAT DID NOT REACH ITS MARKER. The owner that applies
            # the change is asked whether it did -- not the reference, which
            # cannot tell a delayed effect from an absent one.
            found = _target_answer(placement, placement.target_owner.recover,
                                   request)
            if found["answer"] == "unknown":
                # NO "NOTHING WAS CHANGED" HERE. The recovery has already been
                # called, and an effect-capable owner may have done something
                # this interface did not observe -- claiming otherwise would
                # be exactly the unfounded certainty this branch exists to
                # avoid.
                _refuse(f"the target owner cannot say whether publication "
                        f"{name_value(recorded['publication_id'])} was "
                        f"applied; this interface keeps that uncertainty "
                        f"rather than issuing a second compare-and-swap on "
                        f"the strength of the current reference")
            if found["answer"] == "applied":
                # THE RECEIPT PROVES A PAST EFFECT, NOT CURRENT CONTENT.
                # Review 2026-09-14T00:35:44Z [P1]: the target was read before
                # the recovery, so a reference moved back to the admitted
                # revision in between was settled as integrated while holding
                # none of this publication's content. It is re-read HERE.
                current = placement.configured()
                if current != found["imported_revision"]:
                    _denied(f"the target owner's receipt accounts for "
                            f"{name_value(found['imported_revision'])} and "
                            f"the target now stands at "
                            f"{name_value(current)}; a receipt proves what "
                            f"once happened, not what the target holds, and "
                            f"this publication neither settles that drift nor "
                            f"repeats its own effect")
                placed = found["imported_revision"]
                recorded = record_publication_effect(
                    placement.coordinator, recorded["publication_id"],
                    "swapped")
                swapped = True
        if not swapped:
            # THE TARGET FIRST, THEN THE GRANT, THEN THE APPLY -- in that
            # order and with nothing between the last two. Review
            # 2026-09-14T00:41:55Z [P1]: reading the reference is itself a
            # call that takes time, and the reviewer's probe released this
            # lease from inside it, so a grant proved BEFORE that read was
            # already stale when the apply ran. Whatever is checked last is
            # the only thing that is true at the moment of mutation.
            current = placement.configured()
            if current != admitted_old_revision:
                _denied(f"the target moved to {name_value(current)} while "
                        f"this publication was being resolved and it was "
                        f"admitted against "
                        f"{name_value(admitted_old_revision)}; the swap is "
                        f"not retried against whatever is there now")
            live_grant(placement.coordinator, lease_id=lease_id,
                       canonical_target_id=canonical_target_id,
                       entry_id=entry_id, fence=fence)
            # THE OWNER APPLIES IT, and its receipt is what makes the effect
            # answerable afterwards. `not-applied` from a recovery is a
            # POSITIVE exclusion of a delayed effect, which is the only thing
            # that makes a second attempt safe.
            done = _target_answer(placement, placement.target_owner.apply,
                                  request)
            if done["answer"] != "applied":
                _refuse(f"the target owner answered "
                        f"{name_value(done['answer'])} to applying "
                        f"publication "
                        f"{name_value(recorded['publication_id'])}; this "
                        f"publication did not complete, and what its apply "
                        f"did before answering is that owner's account to "
                        f"give")
            placed = done["imported_revision"]
            recorded = record_publication_effect(placement.coordinator,
                                                 recorded["publication_id"],
                                                 "swapped")
            swapped = True
            performed = True

    # 10. THE SETTLEMENT, the second cutpoint. A failure here leaves the swap
    #     committed and unsettled; that is the interrupted state the branch
    #     above resumes, and it is reported rather than pretended away.
    # AND BEFORE THE SETTLEMENT, ON EVERY PATH, THE TARGET ACTUALLY HOLDS
    # WHAT THIS PUBLICATION PUBLISHED. Review 2026-09-14T00:41:55Z [P1]: a
    # fresh apply can TRUTHFULLY answer `applied` with a receipt after
    # somebody moved the target between the effect and the reply, and the
    # fresh path settled `integrated` over the old revision. The owner's
    # answer accounts for what it did; it cannot account for what happened
    # afterwards, and that is the same distinction the recovery path already
    # makes. One check, after every owner call and all effect bookkeeping,
    # shared by the fresh, recovered and previously-recorded paths.
    #
    # THE EFFECT IS RETAINED AND NEVER REAPPLIED. Drift refuses; it does not
    # roll back, and it does not try again.
    settled_target = placement.configured()
    if settled_target != placed:
        _denied(f"this publication's effect accounts for "
                f"{name_value(placed)} and the target now stands at "
                f"{name_value(settled_target)}; the effect is recorded and is "
                f"never repeated, and an entry is not settled over content "
                f"the target does not hold")
    settle_integrated(placement.coordinator, lease_id=lease_id,
                      canonical_target_id=canonical_target_id,
                      fence=fence, entry_id=entry_id,
                      settlement=settled_request)
    record_publication_effect(placement.coordinator,
                              recorded["publication_id"], "settled")
    # AND THE SETTLEMENT THIS ANSWERS WITH IS THE RECORDED ONE, read back
    # through the same owner a replay reads. Returning the act's own richer
    # answer here and the stored document on replay would make one member mean
    # two things depending on which path produced it.
    written = next(one for one in
                   entries_of(placement.coordinator, canonical_target_id)
                   if one["entry_id"] == entry_id)
    return answer("published" if performed else "resumed", placed,
                  _settlement(written["settlement"], written["state"],
                              "the recorded settlement"))
