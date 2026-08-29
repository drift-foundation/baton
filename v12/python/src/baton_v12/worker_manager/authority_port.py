"""The injected authority capability, TYPED and nothing more.

W4 cut C (PLAN item 4bd). This module implements no authority and grants no
capability. It names the narrow surface the Worker Manager uses on an
already-minted, participant-bound session that trusted deployment supplies, and
it refuses an object that does not carry it.

WHY THE PORT NAMES ONLY WHAT W4 USES. The delivered session carries sixteen
transitions and sixteen reads. A port that named all thirty-two would be a
capability nobody granted: the manager would type -- and a fake would have to
implement -- authority the manager never exercises. Six members is what cut C
needs, and a later cut widens the port deliberately rather than inheriting the
width.

WHY THE CLAIM SIGNATURE ARRIVES BY INJECTION RATHER THAN BY IMPORT. The
authority owns the answer to "are these two claims the same claim", and a
manager that recomputed it would be a second authority on that question -- the
first time the two spellings disagreed, only one would be authoritative and it
would not be the one doing the comparing. So the manager CONSUMES the
authority's own derivation.

It does not IMPORT it. `baton_v12.authority` is a sibling package in one
distribution, and importing it would make the manager depend on the authority's
module graph to do arithmetic on a string -- while the deployment that mints the
session already holds the authority and can hand the derivation over with it.
One injected capability, one trusted supplier, and the manager's import boundary
stays exactly where its own cases say it is.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value, type_name_of
from . import boundaries

__all__ = ["AuthorityPort", "SESSION_MEMBERS", "SESSION_OPERATIONS",
           "PROJECTION_READ", "PROJECTION_UNREAD", "SETTLEMENT", "FENCE",
           "CLAIM_RESULT", "DECISION", "GRANT_PROVENANCE"]

# The session surface cut C uses, written out -- and split, because a bound
# value and an operation are different things to check.
# WIDENED DELIBERATELY FOR CUT D, which is the rule this port was written
# under: a later cut names what it needs rather than inheriting the session's
# full width. Activation asks the authority for the LIVE assignment, because the
# session's binding and this attempt's own claim agreeing is not enough -- any
# two of the three agreeing is exactly how a replayed activation gets in.
SESSION_OPERATIONS = ("project_work", "slot_holder", "claim",
                      "settle_operation", "assignment_of", "cancel",
                      # W6627: the manager is the ONE Baton client, so a
                      # conversational answer reaches Baton through this port
                      # and never through the worker. The worker holds no
                      # Baton and no SQLite capability at any point, and this
                      # member is where that stops being an assertion.
                      "publish_answer")

# WHAT A FENCE ANSWERS WITH. The authority ends the assignment, fences the exact
# generation and installs the typed quiescence gate in ONE transaction, and says
# so in one document.
FENCE = ("cause", "assignment", "phase", "gate", "fenced")
SESSION_MEMBERS = ("participant",) + SESSION_OPERATIONS

# THE PROJECTION, split into what this manager READS and what it merely knows
# the authority emits.
#
# Review [P1]: the contract named the five read members and accepted every
# other, so "exactly these members" was false of the check that said it -- a
# projection carrying an unexpected member was accepted and reached offer
# issuance. Closing it needs both halves: refusing an unnamed member is only
# safe if the members the authority DOES send are written down.
#
# Naming the unread ten rather than ignoring them is the point. An authority
# that stops sending one of them, or starts sending an eleventh, is a build this
# one was not written against -- and the five we read may not mean what they did.
#
# W16823 is the separate later Work W16821 named, and `scope` and `route` MOVE
# HERE because it consumes them.  They are what an offer freezes about the Work
# it is issued against, and what the claim decision is later held to: a claim
# authorized in another scope, or for another route, is not the claim this
# offer promised however well-formed it is.  Reading them is what makes
# "relationally inconsistent context" a thing this manager can actually refuse
# rather than a phrase.
PROJECTION_READ = ("authority_uuid", "status", "phase", "handler", "gate",
                   "scope", "route")
PROJECTION_UNREAD = ("work_id", "outcome", "rationale", "contract",
                     "generation_counter", "live_generation", "assignment",
                     "fenced_generations", "ready",
                     # ...and the decision a closed Work's close was
                     # authorized under.  UNREAD for the same reason `scope`
                     # is: the manager consuming the new projection is separate
                     # later Work, and naming a member is not consuming it.
                     "close_decision",
                     # ...and W29400's Work labels.  UNREAD for the same reason
                     # and with the same boundary: user metadata carries no
                     # runtime meaning, the Worker Manager's own `labels` are
                     # OCI execution identity and are a different thing
                     # entirely, and naming a member is not consuming it.
                     "labels")

# EACH VARIANT'S OWN SHAPE, because knowing WHICH answer arrived tells you
# nothing about what it carries.
#
# Review [P1]: only the vocabulary was closed, so `{"kind": "committed"}` was a
# complete settlement -- and the offer durably advanced to `claimed` carrying a
# null assignment, which is the exact outcome the `committed` branch exists to
# record faithfully.
SETTLEMENT = {
    # `live` carries `record: None`. It is REQUIRED rather than omitted: the
    # authority sends the member, and a `live` answer without it is not the
    # authority's `live`.
    "live": (("record",), ()),
    "committed": (("result",), ()),
    "retired": (("record",), ()),
    "refused": (("detail",), ()),
}

# WHAT AN ASSIGNMENT IDENTITY IS, and it is not "a dict with three members".
#
# Review [P1]: exact POD and an exact member set are the SAFE REPRESENTATION of
# a document; they are not its field contract. A projection whose
# `authority_uuid` was the integer 7 was issued and put in an operation
# signature; a claim answer naming another participant was durably recorded; and
# a `generation` of "not-a-generation" reached SQLite's INTEGER column and
# escaped as a raw IntegrityError AFTER the authority had answered the claim.
#
# §4: an identity is the FULL four parts, never a participant alone and never
# three quarters of one. So each part is owned, and the two parts that are
# RELATIONSHIPS -- whose participant, which Work -- are compared rather than
# shaped, because a well-formed identity for somebody else is still not ours.
CLAIM_ANSWER = ("work_ref", "participant", "generation")
CLAIM_WORK_REF = ("authority_uuid", "work_id")

# W16823: THE CLOSED CLAIM RESULT, and it is three facts rather than one.
#
# The `assignment` is the unchanged four-part fence and its rules above are
# untouched. `claim_event` is the authority's exact immutable identity for the
# act -- the thing that lets this manager say WHICH of its own claims the
# context belongs to, which a v11 assignment tuple cannot because it mints no
# generation. `decision` is the authority's own authorization vocabulary,
# consumed rather than respelled.
CLAIM_RESULT = ("assignment", "claim_event", "decision")
DECISION = ("endpoint", "principal", "effective_scope", "role", "grant",
            "policy_generation")

# WHERE A GRANT CAN HAVE COME FROM, spelled here for the same reason
# `SETTLEMENT`'s kinds are: this manager persists the value into a durable
# column and a later reader reasons from it, so a provenance this build cannot
# place is not one it can store as evidence of anything.
#
# NOT the authority's grammar for principals and scopes, and the difference is
# the whole trust boundary. A closed vocabulary is a fact about the WIRE. The
# mapping from an endpoint to a principal is the authority's private
# configuration, and a manager that reconstructed enough of it to second-guess
# an internally consistent answer would be a second authority on the question
# -- which is the correction this Work exists to make, applied backwards.
GRANT_PROVENANCE = ("direct", "inherited", "masked")


class AuthorityPort:
    """One participant-bound session, plus the authority's own signature rule.

    Holding one grants exactly what the deployment put in it. The manager never
    receives an authority bootstrap, a configuration surface, a store path or a
    way to mint another session -- those are the trusted side of a boundary this
    object is the narrow end of.
    """

    def __init__(self, session, claim_signature):
        """Refuse an object that does not carry what this port names.

        Checked at construction rather than at first use: a manager that
        discovers halfway through an offer that its session cannot claim has
        already spent entropy and taken a durable slot. The members are only
        LOOKED UP here -- `getattr` on an ordinary object runs no more than
        attribute lookup, and nothing is called.
        """
        # Review [P1]: this checked only that the members EXIST, so a session
        # whose `claim` was `None` constructed happily -- and the manager found
        # out as a raw `TypeError` AFTER the offer had been accepted and its
        # claim identity frozen. A capability that is discovered to be missing
        # once durable state depends on it was not typed at all.
        #
        # `participant` is the bound VALUE and the four operations are
        # OPERATIONS, so they are checked differently and both are checked.
        for member in SESSION_OPERATIONS:
            found = getattr(session, member, None)
            if not callable(found):
                raise ContractRefusal(
                    "integrity", "schema",
                    f"the injected session's {member} is "
                    f"{name_value(found)}; a {type_name_of(session)} is not "
                    f"the participant-bound session this manager was given")
        # Injected with the session, and typed with it.
        boundaries.capability(claim_signature,
                              "the authority's claim-signature derivation")
        # THE BOUND VALUE, owned like any other injected one. Review [P1]: the
        # inventory saw the session's CALLS and not the value it is bound to, so
        # an unencodable participant constructed happily -- and nothing binds an
        # authorization this manager records to the identity that will spend it
        # if that identity cannot be stored.
        # THE LABEL CARRIES THE REASON. A refusal here should say what is
        # actually lost -- nothing binds an authorization this manager records
        # to the identity that will spend it -- and the label is the part of a
        # layer refusal that belongs to the caller's domain rather than to the
        # rule.
        participant = boundaries.text(
            session.participant,
            "the identity this session binds an authorization to")
        self._session = session
        self._claim_signature = claim_signature
        self.participant = participant

    # -- reads ---------------------------------------------------------------

    # EVERY ANSWER IS OWNED AT THE PORT, which is where the injected trust
    # domain is crossed. Review [P1]: the port typed the CALL and not the
    # ANSWER, so an integer projection faulted at `.get`, an integer claim was
    # persisted as the assignment, and an integer settlement was silently read
    # as `live` -- the branch that writes nothing, which is a claim about the
    # authority nobody made.
    #
    # One owner per entry, here, so no caller downstream has to wonder.

    def project_work(self, work_id):
        answer = self._session.project_work(work_id)
        if answer is None:
            return None
        projection = boundaries.document(
            answer, "the session's Work projection", required=PROJECTION_READ,
            optional=PROJECTION_UNREAD)
        # THE MEMBER THIS MANAGER CARRIES ONWARD, owned at the same crossing.
        # `authority_uuid` becomes part of an offer's operation signature and a
        # NOT NULL TEXT column, so what it must BE is a durable identity rather
        # than whatever POD happened to arrive in that slot.
        boundaries.identity(projection["authority_uuid"],
                            "the projection's authority")
        # W16823: AND THE TWO AN OFFER FREEZES. They become NOT NULL TEXT
        # columns on the offer and the operands of the relational check the
        # claim decision is later held to, so what they must BE is durable
        # text rather than whatever POD arrived in the slot -- the same rule
        # `authority_uuid` is under and for the same reason.
        boundaries.text(projection["scope"], "the projection's effective scope")
        boundaries.text(projection["route"], "the projection's route")
        return projection

    def assignment_of(self, work_id, authority_uuid):
        """The Work's LIVE assignment, or absence.

        Absence is its own answer: "this Work holds no live assignment" and
        "the live assignment is somebody else's" are different facts, and
        nothing writable may run against either.
        """
        answer = self._session.assignment_of(work_id)
        if answer is None:
            return None
        return self._assignment(answer, work_id, authority_uuid,
                                "the live assignment")

    def cancel(self, expect, operation_id, reason, work_id, authority_uuid):
        """Fence the exact generation and end the assignment, at the authority.

        FIRST in the cancellation order, and this port is where its answer is
        owned. Until the generation is fenced the assignment is still live, so a
        runtime stopped before this returned would be a worker torn out from
        under an assignment the authority still believes is executing.
        """
        answer = boundaries.document(
            self._session.cancel({"expect": expect,
                                  "operation_id": operation_id,
                                  "reason": reason}),
            "the session's fence answer", required=FENCE)
        # THE ASSIGNMENT IT ENDED, owned at the same crossing and related to the
        # attempt this manager is cancelling: a fence that ended somebody else's
        # assignment is not this cancellation however well-formed it is.
        self._assignment(answer["assignment"], work_id, authority_uuid,
                         "the fenced assignment")
        # ALL FOUR MEMBERS, against the EXACT assignment this cancellation
        # named.
        #
        # Review [P1]: relating the authority, the Work and the participant left
        # the GENERATION only shape-checked, so a fence of generation 2 was
        # accepted for an attempt expecting generation 1 -- and the agent and
        # the runtime were then ordered with no evidence that THIS attempt's
        # generation had been fenced. A fence is an act about one generation;
        # three quarters of a match is not that act.
        if answer["assignment"] != expect:
            raise ContractRefusal(
                "integrity", "schema",
                f"the authority fenced {name_value(answer['assignment'])} and "
                f"this cancellation named {name_value(expect)}; nothing below "
                f"may run without evidence that this attempt's generation was "
                f"the one fenced")
        boundaries.text(answer["cause"], "the fence's cause")
        if answer["fenced"] is not True:
            raise ContractRefusal(
                "integrity", "schema",
                f"the authority answered fenced "
                f"{name_value(answer['fenced'])}; a cancellation that did not "
                f"fence the generation leaves the assignment live, and nothing "
                f"below this line may run against one that is")
        return answer

    def slot_holder(self, participant):
        answer = self._session.slot_holder(participant)
        if answer is None:
            return None
        return boundaries.text(answer, "the session's slot holder")

    # -- the two transitions cut C performs ----------------------------------

    def claim(self, work_id, operation_id, authority_uuid, scope, role):
        """Take the claim, as the identity this session is bound to.

        The manager supplies no participant. It could not: the session takes its
        claimant from its binding and REFUSES a supplied one, which is the whole
        reason an offer's participant is checked against the binding rather than
        carried beside it.

        W16823: AND THE ANSWER IS THE CLOSED RESULT, owned whole. `scope` and
        `role` are what THIS offer froze from the Work projection at issuance,
        and they are what the returned decision is held to -- see
        `_claim_result`.
        """
        answer = self._session.claim({"work_id": work_id,
                                      "operation_id": operation_id})
        # THE THREE OWNERS ARE CALLED FROM HERE, one level down each, and that
        # is not a style choice. The boundary inventory attributes a crossing
        # to the public door through ONE private helper; a chain two deep is a
        # crossing it can no longer name, and a rule that is applied and cannot
        # be SEEN to be applied is one the next reviewer takes on trust.
        taken = boundaries.document(answer, "the claim answer's result",
                                    required=CLAIM_RESULT)
        self._assignment(taken["assignment"], work_id, authority_uuid,
                         "the claim answer")
        return self._decided(taken, scope, role, "the claim answer")

    def _decided(self, taken, scope, role, what):
        """The closed claim result, owned at the crossing that receives it.

        W16823. The result is three facts and each is owned by the rule that
        fits what this manager DOES with it. THE ASSIGNMENT keeps every rule it
        had and is owned by the caller, one level from the public door, for the
        inventory reason recorded there. The other two are owned here.

        THE CLAIM EVENT is an act identity this manager persists and compares,
        so it is a whole number counting from one. Zero and negatives are not
        acts; `bool` is excluded because `True == 1` would compare equal to the
        first event ever written.

        THE DECISION is checked for its closed shape, for the durable
        provenance vocabulary, and for THREE RELATIONS this manager can
        establish without acquiring any new authority:

          * the endpoint IS this assignment's participant.  Two spellings of
            one fact are two places for it to be wrong, so the manager stores
            one and proves the other equals it;
          * the effective scope IS the scope this offer froze from the Work;
          * the role IS the route it froze.

        AND ONE THING IT DELIBERATELY DOES NOT CHECK, which is the acceptance
        clarification approver ruling M34905 made. The principal is the only
        principal fact that crosses this boundary. Deciding that a well-formed,
        internally consistent principal from the trusted authority is the
        WRONG one would take a second, independent endpoint-to-principal
        mapping -- and a manager holding that is a second authority, which is
        the conflation this correction exists to end rather than to relocate.
        """
        assignment = taken["assignment"]
        event = taken["claim_event"]
        if type(event) is bool or type(event) is not int or event < 1:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s claim event is {name_value(event)}; it is the "
                f"authority's exact identity for the act, counting from one, "
                f"and it is the only thing that says which of this "
                f"participant's claims the context beside it belongs to")
        decision = boundaries.document(taken["decision"],
                                       f"{what}'s decision", required=DECISION)
        boundaries.text(decision["endpoint"], f"{what}'s decision endpoint")
        boundaries.text(decision["principal"], f"{what}'s principal")
        boundaries.text(decision["effective_scope"],
                        f"{what}'s effective scope")
        boundaries.text(decision["role"], f"{what}'s decided role")
        if decision["grant"] not in GRANT_PROVENANCE:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s grant provenance is "
                f"{name_value(decision['grant'])}; this manager retains it as "
                f"durable evidence of how the claim was authorized, and a "
                f"provenance it cannot place is evidence of nothing")
        policy = decision["policy_generation"]
        if type(policy) is bool or type(policy) is not int or policy < 1:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s policy generation is {name_value(policy)}; it is "
                f"the configuration generation the decision was taken under, "
                f"counting from one")
        if decision["endpoint"] != assignment["participant"]:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} was decided for endpoint "
                f"{name_value(decision['endpoint'])} and fences "
                f"{name_value(assignment['participant'])}; the endpoint is "
                f"the assignment's participant, and a decision about somebody "
                f"else does not authorize this claim")
        if decision["effective_scope"] != scope:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} was decided in scope "
                f"{name_value(decision['effective_scope'])} and this offer "
                f"was issued against {name_value(scope)}; an authorization in "
                f"another scope is not the one this offer promised")
        if decision["role"] != role:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} was decided for role {name_value(decision['role'])} "
                f"and this offer was issued against route {name_value(role)}; "
                f"a claim authorized as another route is not this offer's")
        return taken

    def _assignment(self, answer, work_id, authority_uuid, what):
        """One assignment identity, owned part by part.

        NESTED, AT THE SAME CROSSING: the members of an injected document cross
        the boundary with it, so owning them here is one entry's ownership
        rather than a second validation of the first.

        THREE OF THE FOUR PARTS ARE RELATIONSHIPS. A perfectly well-formed
        identity naming another authority, another Work or another participant
        is not this manager's assignment, and recording one would durably
        attribute somebody else's claim to this offer. Those are compared, not
        shaped.

        Review [P1]: the authority was owned as durable text and never compared,
        so an assignment from a different authority entirely was accepted for an
        offer this one issued -- advancing it to `claimed` and recording the
        foreign generation. A four-part identity is not owned if one of its
        relationships is only shaped, and `authority_uuid` was the part I had
        typed and left unrelated.

        Shared by the claim answer and by a committed settlement's result,
        because they are the same document arriving by two paths -- and writing
        the rule twice is how it ends up applied at one of the two. The whole
        document is owned here too, for the same reason: a commit recorded late
        goes to the same columns the claim answer does.
        """
        # A LITERAL IN EVERY LABEL, even a derived one. `what` alone would be a
        # label the inventory cannot attribute and a probe cannot assert -- the
        # machinery caught this the moment the shared owner was written.
        boundaries.document(answer, f"{what}'s identity", required=CLAIM_ANSWER)
        boundaries.document(answer["work_ref"], f"{what}'s Work reference",
                            required=CLAIM_WORK_REF)
        boundaries.identity(answer["work_ref"]["authority_uuid"],
                            f"{what}'s authority")
        boundaries.identity(answer["work_ref"]["work_id"], f"{what}'s Work id")
        boundaries.text(answer["participant"], f"{what}'s participant")
        boundaries.generation(answer["generation"], f"{what}'s generation")
        if answer["work_ref"]["authority_uuid"] != authority_uuid:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} comes from authority "
                f"{name_value(answer['work_ref']['authority_uuid'])} and this "
                f"offer was issued from {name_value(authority_uuid)}; an "
                f"assignment another authority made is not this one's to record")
        if answer["work_ref"]["work_id"] != work_id:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} names Work "
                f"{name_value(answer['work_ref']['work_id'])} and this manager "
                f"asked about {name_value(work_id)}; an assignment recorded "
                f"against another Work is not this offer's claim")
        if answer["participant"] != self.participant:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} names {name_value(answer['participant'])} and this "
                f"session is bound to {name_value(self.participant)}; a claim "
                f"is taken as the binding, so an answer naming anybody else is "
                f"not this session's")
        return answer

    def publish_answer(self, work_ref, operation_id, body):
        """Publish one model answer into Baton, with this manager's own
        provenance.

        FORWARDED, and the authority owns its own operands -- the same shape
        every other member of this port has. What is added here is that the
        manager is the party doing it: an answer published by the WORKER would
        need the worker to hold a Baton capability, and the whole isolation
        topology exists so that it does not.

        The answer's reference comes back as durable text, owned as the
        injected value it is: a port that types the call and not the answer
        lets `None` become a durable identity, which is the defect the claim
        path was corrected for.
        """
        return boundaries.injected(
            self._session.publish_answer({"work_ref": work_ref,
                                          "operation_id": operation_id,
                                          "body": body}),
            "a published answer reference")

    def settle_operation(self, operation_id, signature, reason, disposition,
                         may_retire, work_id, authority_uuid, scope, role):
        answer = boundaries.alternative(
            self._session.settle_operation(
                {"operation_id": operation_id, "signature": signature,
                 "reason": reason, "disposition": disposition,
                 "may_retire": may_retire}),
            "the session's settlement answer", SETTLEMENT)
        if answer["kind"] == "committed":
            # THE SAME CLOSED RESULT, arriving by the other path. A commit
            # this manager never saw is recorded LATE from this answer, so an
            # unowned result reaches exactly the columns the claim answer's
            # would -- W16823 included, which is why this is the whole result
            # owner rather than the assignment's.
            result = boundaries.document(answer["result"],
                                         "the committed claim's result",
                                         required=CLAIM_RESULT)
            self._assignment(result["assignment"], work_id, authority_uuid,
                             "the committed claim")
            self._decided(result, scope, role, "the committed claim")
        if answer["kind"] == "refused" and answer["detail"] is not None:
            # Becomes the recorded decision reason, so it is storable text or it
            # is nothing.
            boundaries.text(answer["detail"],
                            "the refused settlement's detail")
        if answer["kind"] == "live" and answer["record"] is not None:
            raise ContractRefusal(
                "integrity", "schema",
                f"a live settlement carries no record and this one carries "
                f"{name_value(answer['record'])}; `live` is the answer that "
                f"says nothing is decided, and a record beside it would be a "
                f"decision nobody made")
        if answer["kind"] == "retired":
            # THE RETIREMENT'S BOUND RECORD, owned at the same crossing.
            # Whoever retired the identity first decided what it means, and the
            # manager reads BOTH members to choose the control state it writes
            # -- so a retirement that carries neither would have chosen that
            # state by default rather than by the authority's answer.
            record = boundaries.document(answer["record"],
                                         "the retirement's bound record",
                                         required=("reason", "disposition"))
            # AND WHAT THE TWO MEMBERS ARE. Review [P1]: their presence was
            # checked and their contents were not, so an integer reason was
            # adopted as the terminal decision and the offer settled. The
            # manager RECORDS the reason and BRANCHES on the disposition -- one
            # reaches a TEXT column, the other decides which control state is
            # written -- so both are text or this settlement is not one this
            # build can adopt.
            boundaries.text(record["reason"], "the retirement's reason")
            boundaries.text(record["disposition"],
                            "the retirement's disposition")
        return answer

    # -- the authority's own derivation, consumed rather than reimplemented ---

    def claim_signature(self, work_id, participant):
        return boundaries.injected(
            self._claim_signature(work_id, participant),
            "the authority's claim signature")
