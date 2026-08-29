"""The authority's implementation, and NOT a public object.

Nothing outside this package ever holds a `Core`.  The two public faces --
trusted bootstrap now, the participant-bound runtime session in cut 5 -- each
expose the subset their holder is entitled to, and `Core` is what makes them ONE
implementation rather than two that can drift.

THERE IS DELIBERATELY NO ACCESSOR FOR THE STORE, THE CONNECTION OR ANY SQL
RUNNER.  The frozen Node host learned this the hard way: it had a `store`
getter, and through it a consumer of the advertised boundary set
`generation_counter` to 41 and then claimed normally, receiving generation 42.
The consumer had chosen the supposedly authority-minted generation, and could
equally have rewritten Handler, fences, gates and receipts.  "The authority, not
the manager, allocates generations" is not a property a comment can hold; it is
a property of there being no other door.

CUT 3 BRINGS THE OPERATION ID, WITH THE MECHANISM THAT GIVES IT MEANING.  Cut 2
deliberately did not take the operand, because accepting one and doing nothing
with it would be a claim with no mechanism behind it -- an exact retry would
re-perform the act while the caller believed it had been made effectively-once.
Every mutating transition now requires an `operation_id` and runs through
`Store.replay`, so an exact repeat replays the first outcome and a REUSED id
with different operands collides.

The signature is the FULL effective operands INCLUDING THE PROSE.  Reusing one
operation id with different durable text is a refusal rather than a silent
replay of somebody else's result, and that is only true if the text rides the
signature.
"""

import json
from datetime import datetime, timezone

from .errors import Refusal, label_of, name_of
from .labels import MAX_LABELS, canonical_label, canonical_label_set

# THE TRUSTED BOOTSTRAP, named once. Creation is the act that brings into
# existence the Work every later scope resolves against, so there is no prior
# principal to authorize it -- and saying that in a constant is what lets a
# reader tell "the deployment created this" from "nobody recorded who did".
BOOTSTRAP_ENDPOINT = "authority.bootstrap"
BOOTSTRAP_PRINCIPAL = "principal:authority-bootstrap"
from .principals import (DEPLOYMENT_SCOPE, DIRECT, M2_GRANTS,
                         AuthorizationDecision, check_grant_provenance,
                         check_principal, check_scope,
                         principal_for_endpoint)
from .identity import (
    ABSENT, GATE_CONTRACT_RUNTIME, GATE_PLAN_REVISION, GATE_QUIESCENCE,
    MAX_SAFE_INTEGER, V11,
    assignment_key, assignment_ref, check_generation, check_participant,
    check_opaque_id, check_text, check_timestamp, check_work_id,
    claim_signature, gate_token,
    is_v12_contract, normalize_assignment, own, parse_gate, same_assignment,
    signature_of,
)

__all__ = ["Core", "CAPABILITIES", "CLOSED_PHASES", "UNCLAIMED_PHASES",
           "UNCLAIMABLE_PHASES", "GATE_KINDS", "RELEASE_DISPOSITIONS",
           "INTAKE_OUTCOMES"]

# The four scheduler phases, and `None` for a terminal Work.
CLOSED_PHASES = frozenset({"queued", "active", "block", "parked"})
# The phases an UNCLAIMED Work can be in.  `active` is absent on purpose: it
# means exactly "a Handler holds it", and only `claim` reaches it.
UNCLAIMED_PHASES = frozenset({"queued", "block", "parked"})
UNCLAIMABLE_PHASES = frozenset({"block", "parked"})
GATE_KINDS = frozenset({GATE_QUIESCENCE, GATE_CONTRACT_RUNTIME,
                        GATE_PLAN_REVISION})
# What `end` may call itself.  Every other ending has its own transition,
# because every other ending derives a different scheduler outcome.
RELEASE_DISPOSITIONS = frozenset({"release", "recovered"})
# The terminal outcomes a close may record.
INTAKE_OUTCOMES = frozenset({"satisfying", "non-satisfying", "rejected",
                             "cancelled"})
# The configured capabilities §7's actor column names.  Exported so a deployment
# configures them from one list rather than from string literals scattered
# across its setup.
CAPABILITIES = ("verify", "review", "approve", "integrate", "close",
                # W29400: mutating a Work's labels after creation.
                # A SEPARATE grant, resolved in the WORK's effective
                # scope: the contract says Route eligibility, claim
                # ownership, Handler identity and plain membership
                # authorize nothing here, and reusing `close` or any
                # other receipt capability would have made one of
                # them mean two different permissions.
                "manage-work-labels")
_CAPABILITY_SET = frozenset(CAPABILITIES)


def _utc_now():
    """The default clock: aware UTC, in the frozen `timestamp` grammar.

    SQLite time and process-local counters are not authority, so the clock is a
    bootstrap operand and this is only its default.  It returns TEXT, because
    the boundary carries validated UTC text rather than `datetime` objects --
    a `datetime` crossing a boundary is an object with behaviour, and this
    authority does not take those.
    """
    moment = datetime.now(timezone.utc)
    return f"{moment.strftime('%Y-%m-%dT%H:%M:%S')}.{moment.microsecond // 1000:03d}Z"


class Core:

    def __init__(self, store, *, clock=None, new_uuid=None):
        self._store = store
        self._uuid = store.authority_uuid
        self._clock = clock if clock is not None else _utc_now
        self._new_uuid = new_uuid

    @property
    def authority_uuid(self):
        return self._uuid

    def _now(self):
        """The configured clock's answer, VALIDATED.

        The clock is a TRUSTED bootstrap collaborator, so a clock that RAISES is
        a fault and is left to propagate -- the transaction rolls back and
        nothing is recorded, because an act whose failure we cannot describe is
        not one we may record an outcome for.  What is checked is the ANSWER: a
        clock that returns the wrong shape is not faulting, it is lying, and
        every row it touches would carry the lie.
        """
        return check_timestamp(self._clock(), what="the configured clock answered")

    # -- deployment policy ---------------------------------------------------

    def certify_contract(self, contract, profile="reference"):
        _text(contract, "a contract")
        _text(profile, "a profile")
        def body():
            self._store.run(
                "INSERT INTO certified_contract (contract, profile, "
                "certified_at) VALUES (?, ?, ?) ON CONFLICT (contract) DO "
                "UPDATE SET profile = excluded.profile",
                contract, profile, self._now())
            self._bump_policy_generation()

        self._store.transact(body)

    def withdraw_certification(self, contract):
        _text(contract, "a contract")
        def body():
            self._store.run(
                "DELETE FROM certified_contract WHERE contract = ?", contract)
            self._bump_policy_generation()

        self._store.transact(body)

    def is_certified(self, contract):
        _text(contract, "a contract")
        return self._store.get(
            "SELECT 1 AS ok FROM certified_contract WHERE contract = ?",
            contract) is not None

    def permit_contract_transition(self, from_contract, to_contract):
        _text(from_contract, "a contract")
        _text(to_contract, "a contract")
        def body():
            self._store.run(
                "INSERT INTO contract_transition (from_contract, to_contract) "
                "VALUES (?, ?) ON CONFLICT DO NOTHING",
                from_contract, to_contract)
            self._bump_policy_generation()

        self._store.transact(body)

    def permits_contract_transition(self, from_contract, to_contract):
        _text(from_contract, "a contract")
        _text(to_contract, "a contract")
        return self._store.get(
            "SELECT 1 AS ok FROM contract_transition WHERE from_contract = ? "
            "AND to_contract = ?", from_contract, to_contract) is not None

    def set_policy(self, key, value):
        _text(key, "a policy key")
        # The VALUE is owned data: a policy is durable and is read back as JSON.
        owned = json.dumps(own(value, what="a policy value"))

        def body():
            self._store.run(
                "INSERT INTO policy (key, value) VALUES (?, ?) ON CONFLICT "
                "(key) DO UPDATE SET value = excluded.value", key, owned)
            self._bump_policy_generation()

        self._store.transact(body)

    def policy(self, key, fallback=None):
        _text(key, "a policy key")
        row = self._store.get("SELECT value FROM policy WHERE key = ?", key)
        if row is None:
            return fallback
        return json.loads(row["value"])

    def canonical_target(self):
        """The one policy value this authority reads SEMANTICALLY.

        Review [P1]: `policy` is deliberately generic -- a policy value is any
        owned JSON document -- and this accessor handed whatever it found
        straight into a durable column.  A dict reached parameter binding as a
        raw `ProgrammingError`, and an EMPTY STRING published successfully as a
        target, which is worse: a proposal bound to no target at all.
        Generic storage plus a specific meaning is exactly where a type has to
        be asserted, and this is the only place that knows the meaning.
        """
        return check_text(self.policy("canonical_target", "base-1"),
                          "the configured canonical_target")

    # -- the principal mapping (W16821) --------------------------------------
    #
    # The endpoint address is the OPERATIONAL name: it routes, it is the
    # Handler, it fences an assignment and it is the actor on a receipt.  The
    # principal is WHO acted.  Before this correction one string was both, so
    # two spellings of one person held two claim slots and one spelling could
    # not say which scope and which grant authorized an act.

    def principal_of(self, participant):
        """WHICH principal this endpoint resolves to.  A READ, and it writes
        nothing.

        A deployment that has bound the endpoint gets the binding; one that has
        not gets the authority's own default, which is one principal per
        endpoint -- exactly the behaviour that existed before this correction.
        The mapping is the AUTHORITY's either way: no operand anywhere names a
        principal for the endpoint it is acting as, so no caller can choose or
        widen the identity its acts are attributed to.
        """
        check_participant(participant)
        row = self._store.get(
            "SELECT principal_id FROM endpoint WHERE participant = ?",
            participant)
        return (row["principal_id"] if row is not None
                else principal_for_endpoint(participant))

    def bind_endpoint(self, participant, principal):
        """Bind one endpoint address to a canonical principal.

        THE CONFIGURATION ACT THAT MAKES TWO ADDRESSES ONE PERSON.  It lives on
        the trusted bootstrap face and nowhere else: a session that could
        rebind its own endpoint could move its claim slot, its grants and its
        attribution to somebody else's identity.

        Rebinding an endpoint that already HOLDS a slot is refused rather than
        followed.  Moving the binding under a live claim would move the
        capacity that claim is occupying, and the deployment would have two
        principals each believing they hold it.
        """
        check_participant(participant)
        check_principal(principal)

        def body():
            held = self._store.get(
                "SELECT work_id FROM claim_slot WHERE participant = ?",
                participant)
            if held is not None:
                raise Refusal(
                    f"{name_of(participant)} holds a live claim on "
                    f"{name_of(held['work_id'])}; an endpoint is rebound when "
                    f"it is holding nothing, or the capacity it occupies would "
                    f"move to another principal underneath it")
            self._register_principal(principal)
            self._store.run(
                "INSERT INTO endpoint (participant, principal_id, bound_at) "
                "VALUES (?, ?, ?) ON CONFLICT (participant) DO UPDATE SET "
                "principal_id = excluded.principal_id, "
                "bound_at = excluded.bound_at",
                participant, principal, self._now())
            self._bump_policy_generation()
            return self.principal_of(participant)

        return self._store.transact(body)

    def endpoints_of(self, principal):
        """Every endpoint address bound to one principal, ordered."""
        check_principal(principal)
        return [row["participant"] for row in self._store.all(
            "SELECT participant FROM endpoint WHERE principal_id = ? "
            "ORDER BY participant", principal)]

    def _register_principal(self, principal):
        """Record the principal so a foreign key can name it.

        Called from inside a write transaction only.  Registration is not a
        grant of anything: it says this identity exists, which is what a
        durable reference to it requires.
        """
        self._store.run(
            "INSERT INTO principal (principal_id, registered_at) "
            "VALUES (?, ?) ON CONFLICT DO NOTHING", principal, self._now())
        return principal

    def _principal_for_write(self, participant):
        """The principal to write a durable row against, registered.

        The read path does not register, because a read that wrote rows would
        make `principal_of` a mutation with a projection's name.
        """
        return self._register_principal(self.principal_of(participant))

    # -- the configuration generation ---------------------------------------

    def policy_generation(self):
        """WHICH configuration every decision below is being taken under.

        An absent row is generation 1 rather than an error: a store that has
        never been reconfigured is at its first configuration, and inventing a
        seed row at open would have had to date it with a clock this authority
        does not inject.
        """
        row = self._store.get("SELECT generation FROM policy_generation")
        return 1 if row is None else row["generation"]

    def _bump_policy_generation(self):
        """One configuration act, one generation.  Inside the caller's
        transaction, so a refused configuration bumps nothing."""
        self._store.run(
            "INSERT INTO policy_generation (one, generation, bumped_at) "
            "VALUES (1, 2, ?) ON CONFLICT (one) DO UPDATE SET "
            "generation = policy_generation.generation + 1, "
            "bumped_at = excluded.bumped_at", self._now())

    # -- the decision, recorded and read back --------------------------------

    def _record_decision(self, act, act_id, decision):
        """Retain the exact decision one authorized act was taken under.

        Review [P0]: the first cut spread four nullable columns across
        `assignment_event` and three more across `receipt`, so an authorized
        CLOSE -- which writes neither row when the Work was never claimed --
        persisted no decision at all, and every future door would have needed
        its own copy of the same shape.

        IMMUTABLE, and refused rather than overwritten.  A second decision for
        one act is a second answer to a question that was already decided, and
        a journal that let the later one win could not say which one the act
        was actually performed under.
        """
        _text(act, "an authorized act")
        _text(act_id, "an authorized act identity")
        if self._decision(act, act_id) is not None:
            # THE ACT KIND IS NOT INTERPOLATED.  It is one of this module's
            # own constants, but the diagnostic walker cannot prove a parameter
            # bounded and buying an exception-registry entry for a word is the
            # wrong trade; the act identity IS caller-derived and goes through
            # `name_of`, which bounds it.
            raise Refusal(
                f"the authorized act {name_of(act_id)} already retains its "
                f"authorization decision; a decision is what was answered at "
                f"the instant of the act and is never rewritten")
        self._register_principal(decision.principal)
        self._store.run(
            "INSERT INTO authorization_decision (act, act_id, endpoint, "
            "principal_id, effective_scope, role, grant_provenance, "
            "policy_generation, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            act, act_id, decision.endpoint, decision.principal,
            decision.effective_scope, decision.role, decision.grant,
            decision.policy_generation, self._now())
        return decision

    def _act_kind_of(self, act_id):
        """Which of the three acts wrote this label event, from the journal."""
        for act in ("work-label", "work-unlabel", "work-create"):
            if self._decision(act, act_id) is not None:
                return act
        return None

    def _decision(self, act, act_id):
        """The retained decision as a fresh owned document, or `None`.

        READ FROM THE ROW, never rebuilt.  Rebuilding it would consult today's
        endpoint mapping and today's policy generation, and answer what the act
        WOULD be authorized under now rather than what it was performed under
        -- which is the one thing a history is for.
        """
        row = self._store.get(
            "SELECT * FROM authorization_decision WHERE act = ? AND act_id = ?",
            act, str(act_id))
        if row is None:
            return None
        return {"endpoint": row["endpoint"], "principal": row["principal_id"],
                "effective_scope": row["effective_scope"], "role": row["role"],
                "grant": row["grant_provenance"],
                "policy_generation": row["policy_generation"]}

    def decision_of(self, act, act_id):
        """PUBLIC: the decision one authorized act was taken under."""
        _text(act, "an authorized act")
        _text(act_id, "an authorized act identity")
        return self._decision(act, act_id)

    def _scope_of(self, proposal):
        """The scope of the Work a proposal belongs to.

        Taken from the proposal's own EXACT ASSIGNMENT identity rather than
        from a loose column, because that identity is what the proposal is
        bound to and is the thing a scope may not drift from.
        """
        return self._work(
            proposal["assignment_ref"]["work_ref"]["work_id"])["scope"]

    def _live_claim_seq(self, expect):
        """The EXACT claim event this act is being carried out under.

        Resolved AT THE ACT and then stored, which is what makes it exact:
        right now there is one live assignment and one newest claim event for
        it, and a reference captured here cannot be re-pointed by anything that
        happens afterwards.

        Re-review [P0]: the first cut searched for this at READ time instead,
        by `(work_id, participant, generation)`, newest first.  A v11
        assignment mints no generation, so a release and a reclaim through the
        same endpoint gave two claim acts with identical join fields -- and the
        later claim silently became the apparent authorization of the earlier
        act's history.
        """
        found = self._store.get(
            "SELECT seq FROM assignment_event WHERE work_id = ? AND "
            "participant = ? AND IFNULL(generation, -1) = IFNULL(?, -1) AND "
            "cause = 'claimed' ORDER BY seq DESC",
            expect["work_ref"]["work_id"], expect["participant"],
            expect["generation"])
        if found is None:
            raise Refusal(
                "this act is carried out under an assignment whose claim this "
                "authority never journalled; an act that cannot name the "
                "exact claim that authorized it is not attributable")
        return found["seq"]

    def _claim_decision_for(self, row):
        """The decision the assignment an act was carried out under was claimed
        with, read through the row's OWN exact reference.

        Assignment-derived acts -- activity, contract events, proposals -- are
        performed under an assignment somebody else already authorized, so the
        decision they carry is that claim's.  They durably name the claim event
        rather than carrying a copy of its decision, because two copies of one
        fact are two things that can disagree -- and rather than searching for
        it afterwards, because a search over a nullable tuple is not an
        identity.
        """
        return self._decision("claim", str(row["claim_seq"]))

    # -- the ONE authorization decision seam ---------------------------------

    def authorize(self, participant, *, capability=None, route=None,
                  scope=None):
        """Decide ONE act, and answer with the decision rather than a boolean.

        W16821 item 3.  Route membership and capability membership used to be
        two ad-hoc `SELECT 1` existence checks reading a participant column,
        answering yes or no.  A boolean cannot be recorded beside the act it
        authorized: it does not say who acted, in which scope, or by which
        grant, and the acts therefore recorded the endpoint spelling and
        nothing else.

        EXACTLY ONE OF `capability` OR `route`.  A call that named both would
        be two decisions with one answer, and a caller could not tell which one
        the provenance describes.

        The scope is the WORK's or the deployment's, never the caller's: it is
        passed in by the transition from the row it read, and there is no
        operand on any exported surface through which a caller could supply
        one.
        """
        check_participant(participant)
        named = [one for one in (capability, route) if one is not None]
        if len(named) != 1:
            raise Refusal(
                "an authorization decides one route membership or one "
                "capability, and names exactly one of them")
        effective = DEPLOYMENT_SCOPE if scope is None else check_scope(scope)
        principal = self.principal_of(participant)
        if capability is not None:
            self._require_known_capability(capability)
            row = self._store.get(
                "SELECT provenance FROM capability WHERE principal_id = ? AND "
                "capability = ? AND scope = ?",
                principal, capability, effective)
            if row is None:
                return None
            role, provenance = capability, row["provenance"]
        else:
            _text(route, "a route")
            if self._store.get(
                    "SELECT 1 AS ok FROM route_handler WHERE route = ? AND "
                    "participant = ?", route, participant) is None:
                return None
            # A configured route handler is a DIRECT grant of that route to
            # the principal the endpoint resolves to.  When the M6 resolver
            # arrives it answers here, and the shape it must fill is already
            # the shape this returns.
            role, provenance = route, DIRECT
        return AuthorizationDecision(
            endpoint=participant, principal=principal,
            effective_scope=effective, role=role,
            # READ WIDE, WRITE NARROW.  The column admits inherited and masked
            # provenance so a resolver can land without a migration; a decision
            # this cut hands out may only be direct, and that is checked here
            # rather than trusted from the row.
            grant=check_grant_provenance(provenance, producible=M2_GRANTS),
            policy_generation=self.policy_generation())

    # -- capabilities --------------------------------------------------------
    #
    # THE GRANTEE IS THE PRINCIPAL.  The exported surface still takes an
    # endpoint address, because that is what a deployment configures and what
    # every existing caller has; the authority resolves it, and two addresses
    # bound to one principal therefore share one grant instead of needing two.

    def grant_capability(self, participant, capability, *, scope=None):
        check_participant(participant)
        self._require_known_capability(capability)
        effective = DEPLOYMENT_SCOPE if scope is None else check_scope(scope)

        def body():
            principal = self._principal_for_write(participant)
            self._store.run(
                "INSERT INTO capability (principal_id, capability, scope, "
                "provenance, granted_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT DO NOTHING",
                principal, capability, effective, DIRECT, self._now())
            self._bump_policy_generation()

        self._store.transact(body)

    def revoke_capability(self, participant, capability, *, scope=None):
        check_participant(participant)
        self._require_known_capability(capability)
        effective = DEPLOYMENT_SCOPE if scope is None else check_scope(scope)

        def body():
            self._store.run(
                "DELETE FROM capability WHERE principal_id = ? AND "
                "capability = ? AND scope = ?",
                self.principal_of(participant), capability, effective)
            self._bump_policy_generation()

        self._store.transact(body)

    def holds_capability(self, participant, capability, *, scope=None):
        if type(participant) is not str or type(capability) is not str:
            return False
        try:
            return self.authorize(participant, capability=capability,
                                  scope=scope) is not None
        except Refusal:
            # A malformed participant or an unknown capability is not a holder.
            # This read answered False for those before the seam existed and
            # callers depend on it being a question rather than a refusal.
            return False

    def grants_of(self, participant):
        """EVERY grant this endpoint's principal holds, with its scope and its
        provenance.

        Review [P1]: `capabilities_of` answered names alone, so a principal
        granted `verify` in two scopes projected `['verify', 'verify']` -- a
        list that neither said where either grant was effective nor told a
        duplicate from a second scope.  This is the projection; the one below
        is a deliberately narrower helper.
        """
        check_participant(participant)
        return [{"capability": row["capability"], "scope": row["scope"],
                 "provenance": row["provenance"]}
                for row in self._store.all(
                    "SELECT capability, scope, provenance FROM capability "
                    "WHERE principal_id = ? ORDER BY capability, scope",
                    self.principal_of(participant))]

    def capabilities_of(self, participant):
        """WHICH capabilities this endpoint's principal holds anywhere, and
        deliberately not where.

        A COMPATIBILITY PROJECTION with explicit semantics: the DISTINCT
        capability names held in any scope, sorted.  It answers "may this
        principal ever verify" and nothing else -- a deployment asking whether
        a grant is effective for a particular act must read `grants_of`, or
        better, let the authorization seam decide, because a name held in some
        scope authorizes nothing by itself.

        Distinct rather than one row per grant: the duplicate the first cut
        projected was not information, it was the scope column missing.
        """
        check_participant(participant)
        return [row["capability"] for row in self._store.all(
            "SELECT DISTINCT capability FROM capability WHERE "
            "principal_id = ? ORDER BY capability",
            self.principal_of(participant))]

    def _require_known_capability(self, capability):
        if type(capability) is not str or capability not in _CAPABILITY_SET:
            raise Refusal(
                f"{name_of(capability)} is not one of the configured "
                f"capabilities ({', '.join(CAPABILITIES)}); a deployment "
                f"grants what §7 names and not a word of its own")

    # -- Work and route ------------------------------------------------------

    def create_work(self, work_id, route, *, operation_id, contract=V11,
                    phase="queued", gate=None, scope=None, labels=()):
        """Mint an UNCLAIMED Work.

        The frozen host accepted `phase="active"` and committed a
        Handler-null/active row, which its invariant check then reported after
        the corruption was already durable.  Invariants are a BACKSTOP; the
        transition is where an impossible state is refused.  `active` means
        exactly "a Handler holds it", and only `claim` reaches it.
        """
        check_work_id(work_id)
        _text(route, "a route")
        _text(contract, "a contract")
        if type(phase) is not str or phase not in UNCLAIMED_PHASES:
            raise Refusal(
                f"a Work is created unclaimed, so its phase is one of "
                f"{', '.join(sorted(UNCLAIMED_PHASES))}; {name_of(phase)} is "
                f"not reachable without a Handler")
        self._assert_phase_gate(phase, gate)
        # W16821 item 2.  The effective scope is AUTHORITY-OWNED and supplied
        # here, at the trusted bootstrap that creates the Work.  It is NOT
        # derived from the route, the repository or the participant spelling --
        # the correction boundary forbids exactly that, and it is why an
        # omitted scope falls back to the deployment's one named constant
        # rather than to anything computed from the operands beside it.
        effective = DEPLOYMENT_SCOPE if scope is None else check_scope(scope)
        # W29400: VALIDATED BEFORE THE TRANSACTION, because a malformed label
        # is a refusal about the operands and not about the Work -- and a Work
        # half-created with some of its labels would be a set nobody asked for.
        wanted = canonical_label_set(labels, what="the Work's labels")
        if len(wanted) > MAX_LABELS:
            raise Refusal(
                f"a Work holds at most {MAX_LABELS} labels and this creation "
                f"names {len(wanted)}")

        def body():
            if self._store.get("SELECT 1 AS ok FROM work WHERE work_id = ?",
                               work_id) is not None:
                raise Refusal(f"Work {name_of(work_id)} already exists")
            self._store.run(
                "INSERT INTO work (work_id, route, status, phase, gate, "
                "contract, scope, created_at) "
                "VALUES (?, ?, 'open', ?, ?, ?, ?, ?)",
                work_id, route, phase, gate, contract, effective, self._now())
            # THE CREATION IS ATTRIBUTED, and to a decision rather than to a
            # string. Review [P0]: create-time labels were filed under
            # `"create:" + work_id` -- an act id nothing decided and nothing
            # could join -- so `work_label_events` answered `decision: None`
            # and the addition was unattributable by the approved contract.
            #
            # THE PROVENANCE IS THE TRUSTED BOOTSTRAP, named as such. There is
            # no actor here by construction: creation is the act that brings
            # the Work the scope resolves in into existence, so there is
            # nothing yet to resolve a capability against. What the record has
            # to say is exactly that, in a shape a reader can join -- not a
            # null standing for "somebody, somehow".
            self._record_decision("work-create", operation_id,
                                  self._bootstrap_decision(effective))
            # CREATE-TIME LABELS ARE ADDITIONS ATTRIBUTED TO THAT ACT, in the
            # same transaction: a Work that existed for an instant without the
            # labels it was created with is a Work a reader could have seen
            # unlabelled.
            for one in wanted:
                self._add_label(work_id, one, act_id=operation_id)
            return self.project_work(work_id)

        return self._replay(
            operation_id,
            signature_of("work-create", {
                "work_id": work_id, "route": route, "contract": contract,
                "phase": phase, "gate": gate, "scope": scope,
                "labels": list(wanted)}),
            body)

    def _bootstrap_decision(self, effective):
        """The provenance a Work creation is taken under.

        NAMED RATHER THAN NULL. A trusted bootstrap is a real answer to "under
        what authority did this happen" -- it says the deployment itself, at
        the act that has no prior Work to resolve against -- and a reader can
        tell it apart from a capability-authorized act by its role and its
        grant. A `None` could not be told apart from a missing row.
        """
        return AuthorizationDecision(
            endpoint=BOOTSTRAP_ENDPOINT, principal=BOOTSTRAP_PRINCIPAL,
            effective_scope=effective, role="create-work",
            grant=DIRECT, policy_generation=self.policy_generation())

    def add_route_handler(self, route, participant):
        _text(route, "a route")
        check_participant(participant)

        def body():
            # The endpoint's principal is registered HERE, at the configuration
            # act that first names the address, so the mapping exists durably
            # before any claim can be decided against it.
            self._principal_for_write(participant)
            self._store.run(
                "INSERT INTO route_handler (route, participant) VALUES (?, ?) "
                "ON CONFLICT DO NOTHING", route, participant)
            self._bump_policy_generation()

        self._store.transact(body)

    # -- Work labels (W29400) ------------------------------------------------
    #
    # CROSS-CUTTING METADATA AND NOTHING ELSE.  Adding, removing or spelling a
    # label changes the label set, its journal and nothing whatever about
    # contract, phase, gate, readiness, Route, Handler, claim, dependency,
    # outcome or capacity.  No spelling is reserved and no behaviour is
    # inferred from one, which is why nothing in this section reads a label to
    # decide anything.

    def labels_of(self, work_id):
        """One Work's live set, sorted, as a fresh owned list.

        `[]` for a Work with none: absence is an answer, and a caller that had
        to distinguish "no labels" from "no such member" would be reading the
        projection's shape instead of the Work's facts.
        """
        return [row["label"] for row in self._store.all(
            "SELECT label FROM work_label WHERE work_id = ? ORDER BY label",
            self._work(work_id)["work_id"])]

    def _add_label(self, work_id, label, *, act_id):
        """Add one canonical label inside the caller's transaction.

        Answers whether it CHANGED anything.  Adding a label the Work already
        holds is a successful no-op that writes no event -- the contract's
        `changed:false` -- because an event recording that nothing happened
        makes the journal unable to say what did, and two callers converging on
        the same set is agreement rather than a conflict.

        THE CARDINALITY IS CHECKED HERE, inside the write, and only when the
        label is genuinely new.  Checked before the transaction it would be a
        limit two racing final-slot additions could both pass; charged against
        a no-op it would refuse a caller asking for a state the Work is already
        in.
        """
        if self._store.get(
                "SELECT 1 AS ok FROM work_label WHERE work_id = ? AND "
                "label = ?", work_id, label) is not None:
            return False
        held = self._store.get(
            "SELECT COUNT(*) AS n FROM work_label WHERE work_id = ?",
            work_id)["n"]
        if held >= MAX_LABELS:
            # THE COUNT IS NOT RENDERED.  At this line it IS `MAX_LABELS` --
            # that is the branch's own condition -- so interpolating it would
            # add an unproven value to a diagnostic to say something the
            # constant beside it already says.
            raise Refusal(
                f"Work {name_of(work_id)} already holds the maximum "
                f"{MAX_LABELS} labels; a label is removed before another is "
                f"added")
        at = self._now()
        self._store.run(
            "INSERT INTO work_label (work_id, label, added_at) "
            "VALUES (?, ?, ?)", work_id, label, at)
        self._store.run(
            "INSERT INTO work_label_event (work_id, label, action, act_id, at) "
            "VALUES (?, ?, 'added', ?, ?)", work_id, label, act_id, at)
        return True

    def _remove_label(self, work_id, label, *, act_id):
        """Remove one canonical label inside the caller's transaction.

        Removing a label the Work does not hold is the same convergent no-op in
        the other direction, and for the same reason.
        """
        # ASKED BEFORE THE DELETE.  `Store.run` answers the cursor rather than
        # a rowcount, and a cursor is always truthy -- so branching on it made
        # every removal look like a change, including the convergent no-op the
        # contract is specifically about.
        if self._store.get(
                "SELECT 1 AS ok FROM work_label WHERE work_id = ? AND "
                "label = ?", work_id, label) is None:
            return False
        self._store.run(
            "DELETE FROM work_label WHERE work_id = ? AND label = ?",
            work_id, label)
        self._store.run(
            "INSERT INTO work_label_event (work_id, label, action, act_id, at) "
            "VALUES (?, ?, 'removed', ?, ?)",
            work_id, label, act_id, self._now())
        return True

    def label_work(self, work_id, label, *, actor, operation_id):
        """Add one label to one Work, as an authorized attributable act."""
        return self._label_transition(work_id, label, actor=actor,
                                      operation_id=operation_id, adding=True)

    def unlabel_work(self, work_id, label, *, actor, operation_id):
        """Remove one label from one Work, as an authorized attributable act."""
        return self._label_transition(work_id, label, actor=actor,
                                      operation_id=operation_id, adding=False)

    def _label_transition(self, work_id, label, *, actor, operation_id,
                          adding):
        """The one boundary both label mutations cross.

        AUTHORIZED IN THE WORK'S OWN EFFECTIVE SCOPE, through W16821's seam:
        the Work is loaded first so there is a target to derive the scope from,
        which is the correction that Work's review required after a default
        scope let a receipt resolve in the deployment's.

        PERMITTED WHATEVER THE PHASE, AND AFTER CLOSURE.  The contract says so
        and gives the reason: a label change is archive metadata, and it
        reopens, reschedules and re-authorizes nothing.  There is deliberately
        no status or phase check here, because adding one would be this module
        inventing a rule the contract explicitly settled the other way.
        """
        check_work_id(work_id)
        canonical = canonical_label(label)
        act = "work-label" if adding else "work-unlabel"
        # THE SIGNATURE IS MADE OF CALLER OPERANDS ONLY, which is what lets an
        # exact retry reach the journal BEFORE today's policy is consulted.
        #
        # Review [P0]: it carried `work["scope"]`, read from state, so the Work
        # had to be loaded and authorized before the signature existed -- and
        # an operation that already committed was therefore re-authorized
        # against current policy. A retry after the recorded grant was revoked
        # got a denial instead of its own committed outcome, which is the
        # opposite of what effectively-once means. Replay is a fact about an
        # act that already happened.
        signature = signature_of(act, {
            "work_id": work_id, "label": canonical, "actor": actor})

        def body():
            # AND THE LOOKUP AND THE DECISION ARE INSIDE THE WRITE, which is
            # the other half of the same finding. Authorization read outside
            # the transaction let a competing connection revoke the grant
            # between the decision and the mutation; resolved here, the
            # decision, the mutation, the event and the decision row serialize
            # together. This is the ordering `end` and `pass_work` already use.
            work = self._work(work_id)
            decision = self._require_capability(
                actor, "manage-work-labels",
                "Work label addition" if adding else "Work label removal",
                scope=work["scope"])
            changed = (self._add_label(work["work_id"], canonical,
                                       act_id=operation_id)
                       if adding else
                       self._remove_label(work["work_id"], canonical,
                                          act_id=operation_id))
            if changed:
                # THE DECISION IS RETAINED ONLY FOR AN ACT THAT HAPPENED.
                # A no-op authorized nothing, so a decision row for it would
                # be evidence of a change the journal correctly does not have.
                self._record_decision(act, operation_id, decision)
            return {"work_id": work["work_id"], "label": canonical,
                    "action": "added" if adding else "removed",
                    "changed": changed,
                    "labels": self.labels_of(work["work_id"]),
                    "decision": decision.as_document()}

        return self._replay(operation_id, signature, body)

    def work_label_events(self, work_id):
        """The append-only mutation history, with its authorization evidence.

        The decision is JOINED from `authorization_decision` rather than copied
        onto the event: one shape, one owner, and a history that cannot drift
        from the decision it names.  `None` for the additions a Work creation
        made, which are attributed to the creation act rather than to a
        `manage-work-labels` grant.
        """
        return [{"seq": row["seq"], "work_id": row["work_id"],
                 "label": row["label"], "action": row["action"],
                 # THE ACT KIND IS PROJECTED, never inferred from an id
                 # prefix: the three acts that can write a label event each
                 # have a decision under their own kind, and a create-time
                 # addition names `work-create` rather than answering `None`.
                 "act": self._act_kind_of(row["act_id"]),
                 "decision": (self._decision("work-label", row["act_id"])
                              or self._decision("work-unlabel", row["act_id"])
                              or self._decision("work-create", row["act_id"])),
                 "at": row["at"]}
                for row in self._store.all(
                    "SELECT * FROM work_label_event WHERE work_id = ? "
                    "ORDER BY seq", self._work(work_id)["work_id"])]

    def works_with_labels(self, *, all_of=(), none_of=()):
        """Every Work id carrying ALL of one set and NONE of another, sorted.

        REPEATED POSITIVES INTERSECT and repeated negatives exclude, which is
        the contract's rule and deliberately not an implicit OR: a future
        disjunction gets its own named operand rather than silently changing
        what a repeated filter has always meant.

        MATCHING IS EXACT MEMBERSHIP over normalized keys -- never a substring,
        never `LIKE`, never a separator interpretation.  A label is one opaque
        key, so a filter that matched part of one would be reading structure
        the grammar refuses to have.

        ONE SNAPSHOT.  Both halves are decided in a single read, so a Work
        cannot satisfy the positives from before a change and the negatives
        from after it.
        """
        wanted = canonical_label_set(list(all_of), what="the label filter")
        unwanted = canonical_label_set(list(none_of),
                                       what="the excluded label filter")
        both = sorted(set(wanted) & set(unwanted))
        if both:
            raise Refusal(
                f"the filter requires and excludes {name_of(both[0])}; a "
                f"Work cannot both carry and not carry one label")
        return self._store.read_snapshot(
            lambda: self._matching(set(wanted), set(unwanted)))

    def _matching(self, wanted, unwanted):
        """Both halves decided from ONE read view -- see `read_snapshot`."""
        held = {}
        for row in self._store.all("SELECT work_id, label FROM work_label"):
            held.setdefault(row["work_id"], set()).add(row["label"])
        return sorted(
            row["work_id"] for row in self._store.all(
                "SELECT work_id FROM work")
            if set(wanted) <= held.get(row["work_id"], set())
            and not (set(unwanted) & held.get(row["work_id"], set())))

    def _assert_phase_gate(self, phase, gate):
        """The ONE place the scheduler cross-product is checked.

        Called by every transition that writes a phase or a gate.  A gate is a
        REASON the Work cannot run, so a gate without `block` and a `block`
        without a gate are both states nobody can act on or explain.  The token
        must also be a typed one with a non-empty detail: an unparseable gate
        can never be satisfied, because gate satisfaction has no kind to check
        evidence against.
        """
        if phase is not None:
            if type(phase) is not str or phase not in CLOSED_PHASES:
                raise Refusal(f"unknown phase {name_of(phase)}")
        if gate is None:
            if phase == "block":
                raise Refusal(
                    "a blocked Work must name the one gate holding it")
            return
        if type(gate) is not str:
            raise Refusal(f"a gate token is text; this is {name_of(gate)}")
        if phase != "block":
            raise Refusal(
                f"a gate is what holds a Work in block; it cannot be installed "
                f"with phase {name_of(phase)}")
        parsed = parse_gate(gate)
        if parsed is None or parsed["kind"] not in GATE_KINDS \
                or parsed["detail"] == "":
            raise Refusal(
                f"{name_of(gate)} is not a typed gate token; a gate names one "
                f"of {', '.join(sorted(GATE_KINDS))} and a nonempty detail")

    def _work(self, work_id):
        check_work_id(work_id)
        row = self._store.get("SELECT * FROM work WHERE work_id = ?", work_id)
        if row is None:
            raise Refusal(f"no such Work {name_of(work_id)}")
        return row

    # -- projections ---------------------------------------------------------

    def project_work(self, work_id):
        """The read side.

        A projection is what an operator, a Worker Manager or a reviewer reads
        BEFORE acting, and reading is not deciding: every value here is advisory
        the moment it is returned, and the atomic compare-and-swap in the write
        transaction is the arbiter.

        Two things are spelled out rather than inferred, because inferring them
        is how the contract gets misread.  `assignment` is the FULL four-part
        identity or `None`, never a bare participant, so a caller cannot
        accidentally compare three quarters of an identity and think it compared
        one.  And `ready` is false whenever a gate holds the Work, with the gate
        displayed beside it -- offer, runtime, output, proposal, cancellation,
        quiescence, intake and cleanup stay OFF the phase axis and become at
        most this one displayed gate.

        Returned as fresh owned built-ins, never a live row.

        ONE READ VIEW. Review [P0]: the Work row and its labels were read in
        separate autocommit statements, so a projection could return an open
        Work carrying a label added only after that Work closed -- a state
        that never existed. Every read below is answered from one snapshot.
        """
        return self._store.read_snapshot(lambda: self._projected(work_id))

    def _projected(self, work_id):
        work = self._work(work_id)
        fenced = self._store.all(
            "SELECT generation, cause, reason FROM fenced_generation WHERE "
            "work_id = ? ORDER BY generation", work_id)
        gate = None
        if work["gate"] is not None:
            parsed = parse_gate(work["gate"])
            gate = {"token": work["gate"], "kind": parsed["kind"],
                    "detail": parsed["detail"]}
        return {
            "authority_uuid": self._uuid,
            "work_id": work["work_id"],
            "route": work["route"],
            "status": work["status"],
            "phase": work["phase"],
            "outcome": work["outcome"],
            "rationale": work["rationale"],
            "handler": work["handler"],
            "contract": work["contract"],
            # W16821: the scope is READ beside the route, never derived from
            # it.  A consumer that wants the effective scope of this Work's
            # authorizations reads this; there is nothing to compute.
            "scope": work["scope"],
            # W29400: the complete sorted set, always present and `[]` when
            # empty.  A projection that omitted the member for an unlabelled
            # Work would make every consumer branch on absence.
            "labels": self.labels_of(work["work_id"]),
            # And the decision the close was authorized under, or `None` while
            # the Work is open.  Review [P0]: an authorized close persisted
            # nothing at all, so a closed Work could not say who was permitted
            # to close it -- including the unclaimed close, which writes no
            # assignment event to carry it.
            "close_decision": self._decision("close", work["work_id"]),
            "generation_counter": work["generation_counter"],
            "live_generation": work["live_generation"],
            "assignment": self._assignment_of(work),
            "gate": gate,
            "fenced_generations": [
                {"generation": row["generation"], "cause": row["cause"],
                 "reason": row["reason"]} for row in fenced],
            # Readiness is a derived READ.  It says the Work could be claimed at
            # the instant it was projected and nothing more; the claim
            # transaction rechecks every one of these.
            "ready": (work["status"] == "open" and work["phase"] == "queued"
                      and work["handler"] is None and work["gate"] is None),
        }

    def _assignment_ref_of(self, row, *, work_id=None):
        """The full four-part identity, from any row that carries its parts.

        Review [P1]: `assignment_events` was corrected in cut 2 to answer with a
        nested `assignment_ref`, and then cut 4 added four more projections that
        answered in BARE COLUMNS again -- activity, contract events, proposals,
        and a publish result that omitted the assignment entirely.  Correcting
        one projection and writing the next four the old way is the same defect
        as before, one cut later.

        So there is ONE projector, and every answer that carries an assignment
        goes through it.  §4 says an identity is never a participant alone or a
        local selector, and a projection that answers in parts invites exactly
        the comparison §4 forbids.
        """
        return {
            "work_ref": {"authority_uuid": self._uuid,
                         "work_id": row["work_id"] if work_id is None else work_id},
            "participant": row["participant"],
            "generation": row["generation"],
        }

    def _assignment_of(self, work):
        if work["handler"] is None:
            return None
        return {
            "work_ref": {"authority_uuid": self._uuid,
                         "work_id": work["work_id"]},
            "participant": work["handler"],
            "generation": work["live_generation"],
        }

    def assignment_of(self, work_id):
        """The Work's live assignment, or `None`.

        A PROJECTION of durable columns and never a cache: `handler` and
        `live_generation` move in one transaction, so they cannot disagree here.
        """
        return self._assignment_of(self._work(work_id))

    def fenced_generations(self, work_id):
        return [row["generation"] for row in self._store.all(
            "SELECT generation FROM fenced_generation WHERE work_id = ? "
            "ORDER BY generation", self._work(work_id)["work_id"])]

    def assignment_events(self, work_id):
        """Every assignment event, each carrying the FULL four-part identity.

        Review [P1]: these were returned as the raw scalar row -- work id,
        participant and generation as separate columns -- which is three
        quarters of an identity in the one place a reader reconstructs history
        from.  §4 says an identity is never a participant alone or a local
        selector, and a journal that answers in parts invites exactly the
        comparison §4 forbids.  The columns stay (they are what is indexed);
        the ANSWER is an `assignment_ref`.
        """
        owned = self._work(work_id)["work_id"]
        events = []
        for row in self._store.all(
                "SELECT * FROM assignment_event WHERE work_id = ? ORDER BY seq",
                owned):
            events.append({
                "seq": row["seq"],
                # Review [P1]: the row persisted the decision and the
                # projection discarded it, so the acceptance's public evidence
                # boundary was only reachable through raw SQL.  `None` for the
                # authority's own acts -- a fence, a release and an expiry are
                # not authorized by anybody, and inventing a principal for them
                # is the inference this correction forbids.
                "decision": self._decision("claim", str(row["seq"])),
                "assignment_ref": self._assignment_ref_of(row),
                "cause": row["cause"],
                "fenced": row["fenced"] == 1,
                "reason": row["reason"],
                "gate": row["gate"],
                "phase": row["phase"],
                "at": row["at"],
            })
        return events

    def gate_evidence(self, work_id):
        return [{**dict(row), "evidence": json.loads(row["evidence"])}
                for row in self._store.all(
                    "SELECT * FROM gate_evidence WHERE work_id = ? ORDER BY seq",
                    self._work(work_id)["work_id"])]

    def slot_holder_of_principal(self, principal):
        """Which Work this PRINCIPAL holds, across every address it acts
        through."""
        check_principal(principal)
        row = self._store.get(
            "SELECT work_id FROM claim_slot WHERE principal_id = ?", principal)
        return None if row is None else row["work_id"]

    def slot_holder(self, participant):
        check_participant(participant)
        row = self._store.get(
            # RESOLVED TO THE PRINCIPAL, not read by address.  Asking by
            # address would answer "nothing" for a person who is holding a
            # Work through their other endpoint -- which is the capacity leak
            # this correction closes, reappearing as a read.
            "SELECT work_id FROM claim_slot WHERE principal_id = ?",
            self.principal_of(participant))
        return None if row is None else row["work_id"]

    # -- the compare-and-swap ------------------------------------------------

    def _expect(self, expected, *, what="assignment"):
        """The compare-and-swap every assignment-owned act performs.

        The FENCED case gets its own refusal on purpose.  "Stale assignment" and
        "your generation was ended and fenced" are different facts, and a late
        worker deserves to be told which one applies to it -- the second means
        the assignment is gone for good, not that it lost a race it might win on
        retry.
        """
        # The LABEL is caller text at every exported helper, so it is
        # bound by the rule here, once, where it is accepted.
        what = label_of(what)
        if expected is None:
            raise Refusal(
                f"this act is assignment-owned and needs an exact {what} identity")
        assignment_key(expected, what=what)
        if expected["work_ref"]["authority_uuid"] != self._uuid:
            raise Refusal(
                f"assignment names authority "
                f"{name_of(expected['work_ref']['authority_uuid'])}, not "
                f"{name_of(self._uuid)}")
        work_id = expected["work_ref"]["work_id"]
        current = self.assignment_of(work_id)
        if same_assignment(current, expected):
            return self._work(work_id)
        if self._is_fenced(work_id, expected["generation"]):
            raise Refusal("assignment generation was fenced and ended")
        raise Refusal("stale assignment")

    def _is_fenced(self, work_id, generation):
        if generation is None:
            return False
        return self._store.get(
            "SELECT 1 AS ok FROM fenced_generation WHERE work_id = ? AND "
            "generation = ?", work_id, generation) is not None

    # -- claim capacity ------------------------------------------------------

    def _take_slot(self, decision, work_id, generation):
        """Deployment-wide capacity, keyed by PRINCIPAL.

        W16821 item 4.  The capacity invariant is unchanged -- one live claim
        across the whole deployment -- and WHOSE it is has been corrected.  Two
        endpoint addresses bound to one principal now share one slot; before
        this they had one each, so the limit could be escaped by being
        addressed differently.

        The endpoint is stored beside the key rather than dropped: the Handler
        column, the fence and the assignment identity are all endpoint-
        addressed, and a release has to name the address that took it.
        """
        principal = self._register_principal(decision.principal)
        held = self.slot_holder_of_principal(principal)
        if held is not None and held != work_id:
            raise Refusal(
                f"{name_of(decision.principal)} already holds "
                f"{name_of(held)}; a principal holds ONE active claim at a "
                f"time, across every endpoint address it acts through")
        self._store.run(
            "INSERT INTO claim_slot (principal_id, participant, work_id, "
            "generation, taken_at) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT (principal_id) DO UPDATE SET "
            "participant = excluded.participant, "
            "work_id = excluded.work_id, generation = excluded.generation",
            principal, decision.endpoint, work_id, generation, self._now())

    def _release_slot(self, participant, work_id):
        """Released by PRINCIPAL and Work.

        Deleting by address would leave a slot behind when the endpoint that
        took it was not the one the Work ended under, and the principal would
        be permanently at capacity.
        """
        if participant is None:
            return
        self._store.run(
            "DELETE FROM claim_slot WHERE principal_id = ? AND work_id = ?",
            self.principal_of(participant), work_id)

    # -- claim ---------------------------------------------------------------

    def claim(self, work_id, participant, *, operation_id):
        """Take an unclaimed Work, minting the generation if the contract has one.

        CAPACITY IS CHECKED HERE, inside the write transaction, and not only
        wherever an offer was issued.  Checking it at issue alone would make it
        advisory (§10.2), and an advisory limit on how many live claims one
        participant may hold is not a limit.

        W16823, approver rulings M34905 and M35002.  THE ANSWER IS A CLOSED
        RESULT rather than the bare assignment:

            {assignment, claim_event, decision}

        `assignment` is the UNCHANGED four-part execution fence and nothing
        about it moves -- §4 fencing is what W16793 found working and said must
        not be weakened.  `claim_event` is the exact `assignment_event.seq`
        this claim wrote.  `decision` is W16821's authorization vocabulary byte
        for byte: endpoint, principal, effective scope, role, grant provenance
        and policy generation.

        WHY THE CONSUMER CANNOT ASSEMBLE THIS ITSELF.  The decision was already
        retained here, and a Worker Manager wanting it had only one route: pick
        a claim event out of `assignment_events` by the four-part identity,
        newest first.  This module's own re-review refused that join as "not an
        exact identity" on the authority's side, and it is no more exact on the
        consumer's.  A caller that must guess which of its own acts it just
        performed has not been answered.

        ALL THREE MEMBERS ARE WRITTEN AND READ IN THIS TRANSACTION, so the
        operation journal retains the whole document and an exact retry or a
        lost-result settlement replays the original bytes rather than
        recomposing them against today's endpoint mapping and today's policy
        generation.
        """
        check_work_id(work_id)
        check_participant(participant)

        def body():
            work = self._work(work_id)
            if work["status"] != "open":
                raise Refusal("Work is not claimable")
            if work["phase"] in UNCLAIMABLE_PHASES:
                raise Refusal(
                    f"Work is blocked by {name_of(work['gate'])}; blocked work "
                    f"cannot be claimed" if work["gate"] is not None
                    else f"Work is {name_of(work['phase'])}; blocked and parked work "
                         f"cannot be claimed")
            if work["handler"] is not None:
                raise Refusal("Work is already claimed")
            # W16821 item 3: THROUGH THE SEAM, which answers with the decision
            # rather than with a boolean.  The scope comes off the Work's own
            # row -- the authority-owned value written at creation -- and never
            # from the caller, so no operand can select the scope an act is
            # authorized in.
            decision = self.authorize(participant, route=work["route"],
                                      scope=work["scope"])
            if decision is None:
                raise Refusal(
                    f"route {name_of(work['route'])} does not resolve to "
                    f"{name_of(participant)}")
            generation = None
            if is_v12_contract(work["contract"]):
                generation = work["generation_counter"] + 1
                # Review [P1]: the counter was incremented and returned as an
                # assignment identity without ever being held to the frozen
                # range, so a Work at the boundary minted 9007199254740992 --
                # a generation no consumer of these documents can read back.
                # §10.1 says the counter is never decremented or reused, which
                # means the space is finite and running out is an ORDINARY
                # refusal rather than a number nobody can use.
                if generation > MAX_SAFE_INTEGER:
                    raise Refusal(
                        f"this Work has minted every generation the frozen "
                        f"range allows (up to {MAX_SAFE_INTEGER}); the counter "
                        f"is never reused, so there is no next assignment")
            self._take_slot(decision, work_id, generation)
            self._store.run(
                "UPDATE work SET handler = ?, phase = 'active', "
                "generation_counter = ?, live_generation = ? WHERE work_id = ?",
                participant,
                work["generation_counter"] if generation is None else generation,
                generation, work_id)
            # Review [P1]: W151's transition table requires a CLAIM event, and
            # cut 2 wrote none -- so the history said who lost the Work and
            # never who took it, and a reader could not reconstruct the
            # assignment's life from the journal.  Written in the SAME
            # transaction as the Handler, because an event that can exist
            # without its state (or the reverse) is not a record of anything.
            #
            # The frozen Node host omits it.  It is executable-reference
            # evidence, not the contract.
            # W16821: THE DECISION IS RETAINED FOR THE ACT IT AUTHORIZED.
            # The participant column is unchanged and still names the endpoint
            # -- relabelling it as the principal is exactly the conflation
            # being corrected -- and the decision is keyed by the event this
            # claim wrote, so a Work claimed, released and claimed again keeps
            # both decisions rather than colliding on its own identity.
            self._store.run(
                "INSERT INTO assignment_event (work_id, participant, "
                "generation, cause, fenced, reason, gate, phase, at) "
                "VALUES (?, ?, ?, 'claimed', 0, NULL, NULL, 'active', ?)",
                work_id, participant, generation, self._now())
            # W16823: THE CLAIM EVENT IS NAMED, and then answered with.
            #
            # The seq is read back rather than remembered because SQLite mints
            # it, and it is the ONE exact immutable identity of this act.  A
            # v11 assignment mints no generation, so two claims through one
            # endpoint are two acts whose four-part identities are IDENTICAL --
            # measured, not supposed -- and a consumer matching on the
            # assignment alone cannot say which claim it just made.
            claim_event = self._store.get(
                "SELECT MAX(seq) AS seq FROM assignment_event")["seq"]
            self._record_decision("claim", str(claim_event), decision)
            # THE CLOSED RESULT, and every member is READ BACK FROM THE ROW it
            # was just written to rather than composed from what is in hand.
            # `_decision` is the same reader `decision_of` answers history
            # with, so what a claimant receives and what the journal retains
            # cannot drift into two spellings of one fact.
            return {"assignment": self.assignment_of(work_id),
                    "claim_event": claim_event,
                    "decision": self._decision("claim", str(claim_event))}

        # The operands a fixed claim commits under.  The Work is part of it:
        # this authority holds many Works, and an operation id meaning "claim by
        # this participant" without saying WHICH Work would collide across them.
        return self._replay(operation_id,
                            claim_signature(work_id, participant), body)

    # -- the ONE assignment-ending helper -----------------------------------

    def _end_assignment(self, expected, *, phase, gate=None, cause,
                        fence=False, reason=None):
        """Every Handler-clear path calls this, and nothing else clears Handler.

        The event it appends names the ended assignment, the cause, whether the
        generation was fenced, and the gate the transition derived -- so the
        journal answers "who lost the Work and why" without inference.

        The phase/gate cross-product is checked BEFORE the compare-and-swap, so
        an impossible outcome refuses without touching state.
        """
        self._assert_phase_gate(phase, gate)
        work = self._expect(expected)
        if fence and expected["generation"] is not None:
            self._store.run(
                "INSERT INTO fenced_generation (work_id, generation, cause, "
                "reason, fenced_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                work["work_id"], expected["generation"], cause, reason,
                self._now())
        self._release_slot(work["handler"], work["work_id"])
        self._store.run(
            "UPDATE work SET handler = NULL, live_generation = NULL, phase = ?, "
            "gate = ? WHERE work_id = ?", phase, gate, work["work_id"])
        self._store.run(
            "INSERT INTO assignment_event (work_id, participant, generation, "
            "cause, fenced, reason, gate, phase, at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            work["work_id"], expected["participant"], expected["generation"],
            cause, 1 if fence else 0, reason, gate, phase, self._now())
        return {"cause": cause, "assignment": expected, "phase": phase,
                "gate": gate, "fenced": fence}

    # -- assignment-ending transitions --------------------------------------

    def end(self, expect, *, operation_id, disposition="release", reason=None):
        """Release: the assignment ends and the Work returns to the queue.

        The frozen host took caller-supplied `phase` and `gate` here, so
        `end(..., phase="active")` committed a Handler-null active row through
        the public boundary.  Every transition has a DERIVED scheduler outcome:
        a release derives `queued` and no gate, and a caller that wants a gate
        uses the transition that installs one.
        """
        expect = normalize_assignment(expect)
        _text(disposition, "a disposition")
        if disposition not in RELEASE_DISPOSITIONS:
            raise Refusal(
                f"{name_of(disposition)} is not a release disposition; use the "
                f"transition that owns it -- cancel, reject_plan, install_gate "
                f"or pass_work")
        reason = _optional_text(reason, "a reason")
        return self._replay(
            operation_id,
            signature_of("end", {"expect": expect, "disposition": disposition,
                                 "reason": reason}),
            lambda: self._end_assignment(
                expect, phase="queued", gate=None, cause=disposition,
                fence=False, reason=reason))

    def pass_work(self, expect, *, operation_id, to_route, comment=None):
        """A pass moves the Route and ends the assignment in the same act."""
        expect = normalize_assignment(expect)
        _text(to_route, "a route")
        comment = _optional_text(comment, "a comment")

        def body():
            work = self._expect(expect)
            self._store.run("UPDATE work SET route = ? WHERE work_id = ?",
                            to_route, work["work_id"])
            ended = self._end_assignment(
                expect, phase="queued", cause="pass", fence=False,
                reason=comment)
            return {**ended, "route": to_route}

        return self._replay(
            operation_id,
            signature_of("pass", {"expect": expect, "to_route": to_route,
                                  "comment": comment}), body)

    def cancel(self, expect, *, operation_id, reason=None):
        """Fence the exact generation AND end the assignment in ONE transaction.

        The participant's one global claim slot is freed immediately; only the
        REPLACEMENT waits, behind the typed gate this installs.

        Under `v11` there is no generation, so "fence the exact generation AND
        end the assignment" would fence nothing and install a
        `runtime-quiescence:None` gate naming no generation.  HALF A GUARANTEE
        SPELLED LIKE A WHOLE ONE IS WORSE THAN A REFUSAL: advance the contract
        first.
        """
        expect = normalize_assignment(expect)
        reason = _optional_text(reason, "a reason")

        def body():
            # Review [P2]: the v11 refusal subscripted the normalized ABSENCE,
            # so `cancel(None)` raised `TypeError` instead of the ordinary
            # missing-assignment refusal every other transition gives.  The
            # COMMON precondition comes before the transition-specific one:
            # "you gave me no assignment" is true of every act and is answered
            # the same way by all of them.
            if expect is None:
                raise Refusal(
                    "this act is assignment-owned and needs an exact "
                    "assignment identity")
            if expect["generation"] is None:
                raise Refusal(
                    "cancellation fences an exact generation and this "
                    "assignment has none; only a v12 assignment contract can "
                    "be cancelled")
            return self._end_assignment(
                expect, phase="block",
                gate=gate_token(GATE_QUIESCENCE, str(expect["generation"])),
                cause="cancelled", fence=True, reason=reason)

        return self._replay(
            operation_id,
            signature_of("cancel", {"expect": expect, "reason": reason}), body)

    def reject_plan(self, expect, *, operation_id, plan_digest, reason=None):
        """A plan rejection cannot reoffer the unchanged plan, because the gate
        is installed atomically with the assignment end (§11)."""
        expect = normalize_assignment(expect)
        _text(plan_digest, "a plan digest")
        reason = _optional_text(reason, "a reason")
        return self._replay(
            operation_id,
            signature_of("reject-plan", {"expect": expect,
                                         "plan_digest": plan_digest,
                                         "reason": reason}),
            lambda: self._end_assignment(
                expect, phase="block",
                gate=gate_token(GATE_PLAN_REVISION, plan_digest),
                cause="plan-rejected", fence=False, reason=reason))

    def install_gate(self, work_id, *, operation_id, gate, reason=None,
                     expect=ABSENT):
        """Gate arrival, and the explicit unclaimed phase change.

        If a Handler exists the caller must name its exact assignment: a
        scheduler event that silently discarded a live assignment is precisely
        the uncentralized ending this contract exists to prevent.

        `expect=ABSENT` is the MISSING operand and is not the same as `None`.
        `None` means "I assert there is no assignment"; absent means "I did not
        say".  Conflating them is how a gate arrival ends an assignment nobody
        mentioned.

        AND A SUPPLIED `expect` IS ALWAYS COMPARED, even when the Work turns out
        to be unclaimed.  Found by probing my own cut: the frozen host takes the
        unclaimed branch first and never looks at `expect`, so a caller passing
        a STALE identity to a Work that had since been released got success and
        believed it had performed a compare-and-swap.  An operand supplied and
        ignored is the defect this contract keeps naming; if the caller says
        which assignment it expects, that is the question being asked.
        """
        check_work_id(work_id)
        reason = _optional_text(reason, "a reason")
        if expect is not ABSENT:
            expect = normalize_assignment(expect)
            # Review [P1]: THE IDENTITY MUST BE THIS WORK'S.  An assignment for
            # Y satisfied the compare-and-swap and then X was gated -- or, on
            # the live path, Y WAS ENDED while X stayed untouched.  A
            # compare-and-swap that compares one object and mutates another is
            # not a compare-and-swap; it is two acts wearing one operand.
            if expect is not None \
                    and expect["work_ref"]["work_id"] != work_id:
                raise Refusal(
                    f"the supplied assignment names "
                    f"{name_of(expect['work_ref']['work_id'])} and this gate "
                    f"arrival is for {name_of(work_id)}; an identity is "
                    f"compared against the Work "
                    f"it belongs to or not at all")

        def body():
            self._assert_phase_gate("block", gate)
            work = self._work(work_id)
            if work["handler"] is None:
                if expect is not ABSENT and expect is not None:
                    # The CAS the caller asked for, which cannot hold: there is
                    # no live assignment to be the one they named.
                    self._expect(expect)
                self._store.run(
                    "UPDATE work SET phase = 'block', gate = ? WHERE work_id = ?",
                    gate, work_id)
                return {"gate": gate, "phase": "block", "assignment": None}
            if expect is ABSENT:
                raise Refusal(
                    "this Work has a live assignment; a gate arrival that ends "
                    "it must supply the exact assignment identity")
            return self._end_assignment(
                expect, phase="block", gate=gate, cause="gate-arrival",
                fence=False, reason=reason)

        return self._replay(
            operation_id,
            signature_of("install-gate", {"work_id": work_id, "gate": gate,
                                          "reason": reason, "expect": expect}),
            body)

    # -- gates ---------------------------------------------------------------

    def satisfy_gate(self, work_id, *, operation_id, gate, evidence):
        """Discharge the one gate holding this Work, on evidence of its KIND.

        The evidence is journalled AND checked, so it is owned for the same
        reason an assignment is.
        """
        check_work_id(work_id)
        evidence = own(evidence, what="gate evidence")

        def body():
            work = self._work(work_id)
            if work["gate"] is None or work["gate"] != gate:
                raise Refusal("that gate is not the one holding this Work")
            parsed = parse_gate(gate)
            kind = evidence.get("kind") if type(evidence) is dict else None
            # Review [P1]: every one of these used TRUTHINESS, so a list stood
            # for an exact runtime identity, a dict stood for a pinned clause,
            # and a list satisfied a plan-revision gate.  A gate is discharged
            # by PROOF, and `[1]` is not a proof of anything -- it is a value
            # that happens not to be empty.  Each kind now names the shape it
            # requires, through the one durable-text rule.
            if parsed["kind"] == GATE_QUIESCENCE:
                # §10.8: AN UNREACHABLE RUNTIME IS NOT A DEAD ONE.  Only
                # positive absence, or an explicitly pinned certified-isolation
                # clause, releases the replacement.
                if kind == "runtime-absent":
                    _evidence_text(evidence, "runtime",
                                   "positive absence must name the exact "
                                   "runtime it observed")
                elif kind == "certified-isolation-policy":
                    # AND THE CLAIM IS BOUND TO THE CONFIGURED FACT.  A boolean
                    # `isolation_certified` made "pinned" mean "somebody once
                    # said yes"; the deployment pins a CLAUSE, and the evidence
                    # has to name that clause.  Raised in the record as the one
                    # representation decision this correction takes: the policy
                    # holds the clause identity, and `True` is no longer a
                    # pinned clause.
                    pinned = self.policy("isolation_certified", None)
                    if type(pinned) is not str or pinned == "":
                        raise Refusal(
                            "replacement is not permitted: no isolation clause "
                            "is pinned, and a pinned clause is an identity "
                            "rather than a yes")
                    named = _evidence_text(
                        evidence, "policy",
                        "a certified-isolation claim names the clause it relies "
                        "on")
                    if named != pinned:
                        raise Refusal(
                            "replacement is not permitted: this evidence names "
                            "an isolation clause the deployment has not pinned")
                else:
                    raise Refusal("replacement is not permitted")
            elif parsed["kind"] == GATE_CONTRACT_RUNTIME:
                if kind != "certified-profile":
                    raise Refusal(
                        "no certified runtime profile executes this contract")
                # AND THE JOURNALLED PROOF NAMES THE PROFILE.  Recording only
                # "a certified profile exists" leaves the evidence unable to say
                # WHICH one was relied on, which is the whole point of keeping it.
                certified = self._store.get(
                    "SELECT profile FROM certified_contract WHERE contract = ?",
                    work["contract"])
                if certified is None:
                    raise Refusal(
                        "no certified runtime profile executes this contract")
                named = _evidence_text(
                    evidence, "profile",
                    "certified-profile evidence names the profile it relies on")
                if named != certified["profile"]:
                    raise Refusal(
                        f"the certified profile for {name_of(work['contract'])} "
                        f"is not "
                        f"the one this evidence names")
            elif parsed["kind"] == GATE_PLAN_REVISION:
                if kind != "revised-plan":
                    raise Refusal(
                        "a plan-revision gate needs a revised plan digest")
                digest = _evidence_text(
                    evidence, "plan_digest",
                    "a plan-revision gate needs a revised plan digest")
                if digest == parsed["detail"]:
                    raise Refusal(
                        "the plan digest is unchanged; a plan-revision gate "
                        "cannot be satisfied by reoffering the rejected plan")
            else:
                raise Refusal("unknown gate kind")
            self._store.run(
                "INSERT INTO gate_evidence (work_id, gate, evidence, at) "
                "VALUES (?, ?, ?, ?)",
                work_id, gate, json.dumps(evidence), self._now())
            self._store.run(
                "UPDATE work SET gate = NULL, phase = 'queued' WHERE work_id = ?",
                work_id)
            return {"gate": gate, "kind": kind, "phase": "queued"}

        return self._replay(
            operation_id,
            signature_of("satisfy-gate", {"work_id": work_id, "gate": gate,
                                          "evidence": evidence}), body)

    # -- contract progression -------------------------------------------------

    def advance_contract(self, expect, *, operation_id, expect_contract,
                         target_contract, rationale):
        """Move one Work to another assignment contract, ending the assignment.

        A Work MAY intentionally advance to a contract whose runtime is not
        deployed yet.  It stays the same Work and waits visibly on a typed gate
        rather than being recreated or misclaimed (§11) -- which is the whole
        reason the gate exists.
        """
        expect = normalize_assignment(expect)
        _text(expect_contract, "a contract")
        _text(target_contract, "a contract")
        _text(rationale, "a rationale")

        def body():
            work = self._expect(expect)
            if work["contract"] != expect_contract:
                raise Refusal("contract compare-and-swap is stale")
            if not self.permits_contract_transition(expect_contract,
                                                    target_contract):
                raise Refusal("contract transition is not permitted by policy")
            certified = self.is_certified(target_contract)
            gate = None if certified else gate_token(GATE_CONTRACT_RUNTIME,
                                                     target_contract)
            phase = "queued" if certified else "block"
            self._store.run("UPDATE work SET contract = ? WHERE work_id = ?",
                            target_contract, work["work_id"])
            self._store.run(
                "INSERT INTO contract_event (work_id, from_contract, "
                "to_contract, participant, generation, claim_seq, rationale, "
                "at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                work["work_id"], expect_contract, target_contract,
                expect["participant"], expect["generation"],
                self._live_claim_seq(expect), rationale, self._now())
            self._end_assignment(expect, phase=phase, gate=gate,
                                 cause="contract-advanced", fence=False,
                                 reason=rationale)
            return {"contract": target_contract, "phase": phase, "gate": gate}

        return self._replay(
            operation_id,
            signature_of("advance-contract",
                         {"expect": expect, "expect_contract": expect_contract,
                          "target_contract": target_contract,
                          "rationale": rationale}), body)

    def contract_events(self, work_id):
        # `decision` is the CLAIM's, joined through the full exact assignment
        # identity: a contract transition is carried out under an assignment
        # somebody already authorized, and copying the decision onto this row
        # would be a second copy of one fact.
        return [{"seq": row["seq"],
                 "assignment_ref": self._assignment_ref_of(row),
                 "decision": self._claim_decision_for(row),
                 "from_contract": row["from_contract"],
                 "to_contract": row["to_contract"],
                 "rationale": row["rationale"],
                 "at": row["at"]}
                for row in self._store.all(
                    "SELECT * FROM contract_event WHERE work_id = ? ORDER BY seq",
                    self._work(work_id)["work_id"])]

    # -- canonical activity ---------------------------------------------------

    def activity(self, expect, *, key):
        """One canonical act carried out UNDER an exact assignment.

        Idempotent by the store's own unique index rather than by the journal,
        because the caller's `key` IS the idempotency: a retry of the same act
        under the same assignment is the same row.  Named here rather than left
        between cuts -- neither cut 2's nor cut 4's list mentions it, and an
        assignment-owned durable act with an idempotency key belongs with the
        assignment-owned transitions.
        """
        expect = normalize_assignment(expect)
        _text(key, "an activity key")

        def body():
            work = self._expect(expect)
            self._store.run(
                "INSERT INTO activity (work_id, participant, generation, "
                "claim_seq, action_key, at) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT DO NOTHING",
                work["work_id"], expect["participant"], expect["generation"],
                self._live_claim_seq(expect), key, self._now())
            row = self._store.get(
                "SELECT * FROM activity WHERE work_id = ? AND participant = ? "
                "AND generation IS ? AND action_key = ?",
                work["work_id"], expect["participant"], expect["generation"],
                key)
            return {"seq": row["seq"],
                    "assignment_ref": self._assignment_ref_of(row),
                    "action_key": row["action_key"], "at": row["at"]}

        return self._store.transact(body)

    def activities(self, work_id):
        return [{"seq": row["seq"],
                 "assignment_ref": self._assignment_ref_of(row),
                 "decision": self._claim_decision_for(row),
                 "action_key": row["action_key"],
                 "at": row["at"]}
                for row in self._store.all(
                    "SELECT * FROM activity WHERE work_id = ? ORDER BY seq",
                    self._work(work_id)["work_id"])]

    # -- proposal and the four workflow receipts ------------------------------

    def publish(self, expect, *, operation_id, proposal_id, result_id,
                result_digest, candidate_digest, input_digest, policy_digest,
                target=None):
        """The immutable candidate.

        §10.11 requires the receipt to bind the exact assignment AND the input,
        policy, output, candidate-tree and target digests; §4 adds the frozen
        result identity and its content digest.  The frozen host took ONE
        undifferentiated digest, so a published candidate could not say what it
        had been built FROM -- the input it consumed, the policy it ran under,
        or the frozen output it came from.

        Every one is required and every one rides the operation signature: later
        bytes are a NEW proposal, and an id reused for different bytes refuses
        rather than replaying somebody else's candidate.
        """
        expect = normalize_assignment(expect)
        check_opaque_id(proposal_id, "a proposal id")
        # Review [P1]: `result_id` had only the text rule, so an identifier with
        # a space was accepted -- and §4 types the frozen RESULT IDENTITY as an
        # opaque id like every other durable identity.  Checked BEFORE the
        # signature and the journal, so a malformed one never consumes an
        # operation identity.
        check_opaque_id(result_id, "a result id")
        if target is not None:
            _text(target, "a target")
        digests = {"result_id": result_id, "result_digest": result_digest,
                   "candidate_digest": candidate_digest,
                   "input_digest": input_digest, "policy_digest": policy_digest}

        def body():
            # ONE mechanism.  A separate "is it missing" check in front of
            # `check_text` was measured to change neither the verdict nor the
            # message -- `check_text` already names the member -- so it is gone
            # rather than kept as a guard nothing can observe.  What the loop
            # still carries is that ALL FIVE are required, one at a time, so the
            # refusal says which.
            for name, value in digests.items():
                check_text(value,
                           f"a proposal binds the exact assignment and the "
                           f"result, candidate, input and policy digests, and "
                           f"{name}")
            work = self._expect(expect)
            if not is_v12_contract(work["contract"]):
                raise Refusal("publication requires a v12 assignment contract")
            wanted = target if target is not None else self.canonical_target()
            # A RESULT IDENTITY IS BOUND TO ITS BYTES AND ITS ASSIGNMENT.
            # Review [P1]: the same `result_id` could be published twice with
            # CONTRADICTORY digests, so the frozen result identity named two
            # different things and nothing downstream could tell which.
            # Consistent reuse stays permitted -- one result may back several
            # proposals -- but a contradiction refuses.
            bound = self._store.get(
                "SELECT * FROM proposal WHERE result_id = ? LIMIT 1", result_id)
            if bound is not None:
                if bound["result_digest"] != result_digest:
                    raise Refusal(
                        f"result identity {name_of(result_id)} is already bound "
                        f"to {name_of(bound['result_digest'])}; a frozen result "
                        f"names one "
                        f"set of bytes")
                if (bound["work_id"] != expect["work_ref"]["work_id"]
                        or bound["participant"] != expect["participant"]
                        or bound["generation"] != expect["generation"]):
                    raise Refusal(
                        f"result identity {name_of(result_id)} was produced "
                        f"under a "
                        f"different assignment; a frozen result names the one "
                        f"that made it")
            prior = self._store.get(
                "SELECT * FROM proposal WHERE proposal_id = ?", proposal_id)
            if prior is not None:
                same = (prior["work_id"] == work["work_id"]
                        and prior["participant"] == expect["participant"]
                        and prior["generation"] == expect["generation"]
                        and all(prior[name] == value
                                for name, value in digests.items())
                        and prior["target"] == wanted)
                if not same:
                    raise Refusal(
                        "proposal identity was reused for different bytes")
                return {"proposal_id": proposal_id,
                        "assignment_ref": dict(expect), **digests,
                        "target": wanted}
            self._store.run(
                "INSERT INTO proposal (proposal_id, work_id, participant, "
                "generation, claim_seq, result_id, result_digest, "
                "candidate_digest, input_digest, policy_digest, target, "
                "published_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                proposal_id, work["work_id"], expect["participant"],
                expect["generation"], self._live_claim_seq(expect), result_id,
                result_digest, candidate_digest, input_digest, policy_digest,
                wanted, self._now())
            return {"proposal_id": proposal_id,
                    "assignment_ref": dict(expect), **digests,
                    "target": wanted}

        return self._replay(
            operation_id,
            signature_of("publish", {"expect": expect,
                                     "proposal_id": proposal_id, **digests,
                                     "target": target}), body)

    def proposal(self, proposal_id):
        check_opaque_id(proposal_id, "a proposal id")
        row = self._store.get(
            "SELECT * FROM proposal WHERE proposal_id = ?", proposal_id)
        if row is None:
            raise Refusal("no such proposal")
        return {"proposal_id": row["proposal_id"],
                "assignment_ref": self._assignment_ref_of(row),
                # The CLAIM's decision: publishing is carried out under an
                # assignment somebody already authorized.
                "decision": self._claim_decision_for(row),
                "result_id": row["result_id"],
                "result_digest": row["result_digest"],
                "candidate_digest": row["candidate_digest"],
                "input_digest": row["input_digest"],
                "policy_digest": row["policy_digest"],
                "target": row["target"],
                "published_at": row["published_at"]}

    def _receipt_document(self, row):
        """One receipt, with the decision it was written under beside it.

        `actor` and `decision["endpoint"]` are the same address and are both
        present on purpose: a consumer comparing receipts by attributable actor
        reads `actor`, and one asking who that resolved to reads the decision.
        Collapsing them is the conflation this Work corrects.
        """
        answer = dict(row)
        answer["decision"] = self._decision(row["kind"], row["receipt_id"])
        return answer

    def receipts(self, proposal_id):
        check_opaque_id(proposal_id, "a proposal id")
        return [self._receipt_document(row) for row in self._store.all(
            "SELECT * FROM receipt WHERE proposal_id = ? "
            "ORDER BY recorded_at, kind", proposal_id)]

    def receipt(self, proposal_id, kind):
        check_opaque_id(proposal_id, "a proposal id")
        _text(kind, "a receipt kind")
        row = self._store.get(
            "SELECT * FROM receipt WHERE proposal_id = ? AND kind = ?",
            proposal_id, kind)
        return None if row is None else self._receipt_document(row)

    def _require_capability(self, actor, capability, what, *, scope):
        """Authorize one attributable act IN A NAMED SCOPE, and ANSWER WITH THE
        DECISION.

        `scope` IS REQUIRED AND HAS NO DEFAULT.  Review [P0]: it defaulted to
        the deployment scope, so a receipt on a `scope:platform` Work resolved
        in `scope:deployment` -- an actor granted the capability only in the
        Work's own scope was refused, an actor granted it deployment-wide
        succeeded, and the receipt then recorded `scope:deployment` as the
        scope it had been authorized in.  That is the scope widening this seam
        exists to prevent, arriving through a default argument.

        Every caller derives it from the exact target row -- the Work being
        closed, or the Work the proposal belongs to -- and never from an
        operand.  `test_principal_scope` walks this module's own AST and
        requires every call site to pass one.

        An ORDINARY refusal: it writes nothing, so an actor granted the
        capability afterwards may simply retry with a NEW operation id.

        W16821 item 3: this used to answer nothing at all and its callers
        recorded the endpoint spelling as the whole of the attribution.  It now
        returns the authority's decision, so the principal, the effective scope
        and the grant that carried it can ride the receipt the caller is about
        to write.
        """
        # The LABEL is caller text at every exported helper, so it is
        # bound by the rule here, once, where it is accepted.
        what = label_of(what)
        if type(actor) is not str or actor == "":
            raise Refusal(
                f"a {what} is separately attributable and needs the participant "
                f"writing it")
        decision = None
        try:
            decision = self.authorize(actor, capability=capability,
                                      scope=scope)
        except Refusal:
            # A malformed actor is not a holder.  The refusal below is the one
            # this boundary owes its caller, and it says the same thing it said
            # before the seam existed.
            decision = None
        if decision is None:
            raise Refusal(
                f"{name_of(actor)} does not hold the {capability} capability; "
                f"a {what} "
                f"is written by the configured actor, not by whoever holds the "
                f"object")
        return decision

    def _write_receipt(self, *, kind, capability, valid, proposal_id,
                       receipt_id, actor, disposition, operation_id,
                       precondition=None, policy_generation=None):
        """The four receipts are separately attributable and IMMUTABLE (§10.12).

        The frozen host once stored them as disposition STRINGS on the proposal
        with no actor and no authorization, so one consumer could publish a
        candidate, self-verify, self-review, self-approve, integrate it into the
        canonical target and close the Work.  Each receipt now carries its own
        identity, the actor who wrote it, and the candidate digest and target
        revision that actor was LOOKING AT -- and the actor must hold the
        configured capability for that step.

        A deployment MAY grant one participant several capabilities; §10.12 says
        the receipts stay distinct even then.  What it cannot do is leave the
        question unasked.
        """

        def body():
            check_opaque_id(receipt_id, f"a {kind} receipt needs its own identity, and one")
            # THE PROPOSAL FIRST, because the scope this act is authorized in
            # is the scope of the Work the proposal belongs to.  Review [P0]:
            # the capability check ran BEFORE this load and therefore had no
            # target to derive a scope from, so it used the deployment's.
            proposal = self.proposal(proposal_id)
            decision = self._require_capability(
                actor, capability, kind,
                scope=self._scope_of(proposal))
            if type(disposition) is not str or disposition not in valid:
                raise Refusal(f"invalid {kind} disposition")
            if self.receipt(proposal_id, kind) is not None:
                raise Refusal(f"{kind} receipt is immutable")
            self._require_free_receipt_id(receipt_id, kind)
            if precondition is not None:
                precondition(proposal)
            # `actor` is the ENDPOINT that wrote this receipt and stays
            # exactly what it was: §10.12's four separately attributable
            # receipts are about addresses a deployment configures.  Which
            # principal that address resolved to, in which scope and by which
            # grant is the DECISION, retained under this receipt's own identity.
            self._store.run(
                "INSERT INTO receipt (receipt_id, kind, proposal_id, actor, "
                "disposition, candidate_digest, target, policy_generation, "
                "recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                receipt_id, kind, proposal_id, actor, disposition,
                proposal["candidate_digest"], proposal["target"],
                policy_generation, self._now())
            self._record_decision(kind, receipt_id, decision)
            return {"kind": kind, "receipt_id": receipt_id,
                    "proposal_id": proposal_id, "actor": actor,
                    "disposition": disposition,
                    "policy_generation": policy_generation,
                    "candidate_digest": proposal["candidate_digest"],
                    "target": proposal["target"]}

        return self._replay(
            operation_id,
            # EVERY durable operand, including the policy generation an
            # approval binds.
            signature_of(kind, {"proposal_id": proposal_id,
                                "receipt_id": receipt_id, "actor": actor,
                                "disposition": disposition,
                                "policy_generation": policy_generation}), body)

    def _require_free_receipt_id(self, receipt_id, kind):
        """A receipt identity is claimed once, and reusing one is an ORDINARY
        collision.

        Found by probing my own cut: a `receipt_id` reused across kinds on one
        proposal, or across two proposals, hit the table's uniqueness and left
        as `IntegrityError` -- a FAULT, which takes the whole transaction down
        and journals nothing, so the caller got an unexplained crash instead of
        "that identity is taken".

        `publish` already had this rule for proposal identities.  The receipts
        did not, which is the same omission in the neighbouring transition.
        """
        held = self._store.get(
            "SELECT kind, proposal_id FROM receipt WHERE receipt_id = ?",
            receipt_id)
        if held is not None:
            raise Refusal(
                f"receipt identity {name_of(receipt_id)} is already the "
                f"{name_of(held['kind'])} receipt of "
                f"{name_of(held['proposal_id'])}; a "
                f"{kind} "
                f"receipt needs its own")

    def _disposition_of(self, proposal_id, kind):
        found = self.receipt(proposal_id, kind)
        return None if found is None else found["disposition"]

    def verify(self, *, proposal_id, verification_id, actor, observation,
               operation_id):
        return self._write_receipt(
            kind="verification", capability="verify",
            valid=frozenset({"passed", "failed", "unable"}),
            proposal_id=proposal_id, receipt_id=verification_id, actor=actor,
            disposition=observation, operation_id=operation_id)

    def review(self, *, proposal_id, review_id, actor, disposition,
               operation_id):
        def precondition(_proposal):
            if self._disposition_of(proposal_id, "verification") != "passed":
                raise Refusal("technical review requires passed verification")

        return self._write_receipt(
            kind="review", capability="review",
            valid=frozenset({"accepted", "changes-requested", "rejected"}),
            proposal_id=proposal_id, receipt_id=review_id, actor=actor,
            disposition=disposition, operation_id=operation_id,
            precondition=precondition)

    def approve(self, *, proposal_id, approval_id, actor, disposition,
                operation_id, policy_generation):
        """The policy generation an approval was granted UNDER is a durable
        operand of the receipt, so §10.13 puts it in the operation identity.

        The frozen host had it optional and OUTSIDE the signature, so committing
        one operation under generation 7 and resubmitting the same id under 8
        REPLAYED success instead of colliding -- one identity taking two
        different durable meanings -- and omitting it entirely committed NULL
        while the record claimed approval binds it.
        """
        # Checked BEFORE the journal, so a malformed generation refuses without
        # consuming the identity.
        if type(policy_generation) is bool or type(policy_generation) is not int \
                or policy_generation < 1 \
                or policy_generation > MAX_SAFE_INTEGER:
            raise Refusal(
                "an approval binds the configured policy generation it was "
                "granted under; supply a positive integer")

        def precondition(_proposal):
            if self._disposition_of(proposal_id, "review") != "accepted":
                raise Refusal("approval requires accepted technical review")

        return self._write_receipt(
            kind="approval", capability="approve",
            valid=frozenset({"approved", "denied"}),
            proposal_id=proposal_id, receipt_id=approval_id, actor=actor,
            disposition=disposition, operation_id=operation_id,
            policy_generation=policy_generation, precondition=precondition)

    def integrate(self, *, proposal_id, integration_id, actor, operation_id):
        """The one transition whose REFUSAL can write something.

        The stale-target attempt is journalled beside the proposal BEFORE it
        refuses, so the retry replays that refusal instead of appending a second
        attempt or taking a different outcome under one identity.

        The frozen host had the durable flag on the CALL, so every integration
        refusal -- including a pre-approval one that wrote nothing -- was
        recorded REFUSED and permanently closed.  Only the refusal that actually
        journalled its attempt is marked durable.
        """

        def body():
            check_opaque_id(integration_id,
                            "an integration receipt needs its own identity, and one")
            proposal = self.proposal(proposal_id)
            decision = self._require_capability(
                actor, "integrate", "integration",
                scope=self._scope_of(proposal))
            if self.receipt(proposal_id, "integration") is not None:
                raise Refusal("integration receipt is immutable")
            self._require_free_receipt_id(integration_id, "integration")
            # ORDINARY refusals: they write nothing and stay retryable.
            if self._disposition_of(proposal_id, "verification") != "passed":
                raise Refusal("integration requires passed verification")
            if self._disposition_of(proposal_id, "review") != "accepted":
                raise Refusal("integration requires accepted technical review")
            if self._disposition_of(proposal_id, "approval") != "approved":
                raise Refusal("integration requires explicit approval")
            target = self.canonical_target()
            if target != proposal["target"]:
                # A DURABLE, SEPARATELY ATTRIBUTABLE ACT.  Review [P0]: this
                # journalled an authorized actor and no decision, so the one
                # act in this door that survives its own refusal was the one
                # act that could not say what authorized it.  Its identity is
                # the integration identity this operation was submitted under,
                # which is exactly what a retry would collide on.
                self._store.run(
                    "INSERT INTO integration_attempt (attempt_id, proposal_id, "
                    "actor, reason, target, at) "
                    "VALUES (?, ?, ?, 'stale-target', ?, ?)",
                    integration_id, proposal_id, actor, target, self._now())
                self._record_decision("integration-attempt", integration_id,
                                      decision)
                # DURABLE: this one journalled its attempt, so the refusal is
                # itself a committed outcome of this operation identity.
                raise Refusal("canonical target moved", durable=True)
            self.set_policy("canonical_target", proposal["candidate_digest"])
            self._store.run(
                "INSERT INTO receipt (receipt_id, kind, proposal_id, actor, "
                "disposition, candidate_digest, target, policy_generation, "
                "recorded_at) VALUES (?, 'integration', ?, ?, 'integrated', "
                "?, ?, NULL, ?)",
                integration_id, proposal_id, actor,
                proposal["candidate_digest"], proposal["target"], self._now())
            self._record_decision("integration", integration_id, decision)
            return {"kind": "integration", "receipt_id": integration_id,
                    "proposal_id": proposal_id, "actor": actor,
                    "disposition": "integrated"}

        return self._replay(
            operation_id,
            signature_of("integrate", {"proposal_id": proposal_id,
                                       "integration_id": integration_id,
                                       "actor": actor}), body)

    def integration_attempts(self, proposal_id):
        check_opaque_id(proposal_id, "a proposal id")
        return [dict(row, decision=self._decision("integration-attempt",
                                                  row["attempt_id"]))
                for row in self._store.all(
                    "SELECT * FROM integration_attempt WHERE proposal_id = ? "
                    "ORDER BY seq", proposal_id)]

    # -- close ----------------------------------------------------------------

    def close(self, work_id, *, operation_id, outcome, rationale, actor,
              expect=ABSENT):
        """Authorized UNCLAIMED closure is preserved -- no execution claim is
        manufactured merely to reach a terminal state -- while a close that ends
        a live v12 assignment must supply and compare its full exact identity.

        §7 says an AUTHORIZED actor holding the configured close capability, and
        the frozen host had neither an actor nor a check.  Both close forms name
        their actor: the exact-assignment form still compare-and-swaps the
        identity, and HOLDING THE ASSIGNMENT IS NOT BY ITSELF AUTHORITY to
        terminalize the Work.
        """
        check_work_id(work_id)
        _text(outcome, "an outcome")
        _text(rationale, "a rationale")
        if expect is not ABSENT:
            expect = normalize_assignment(expect)
            # The cut-2 lesson: an identity is compared against the Work it
            # belongs to or not at all.
            if expect is not None \
                    and expect["work_ref"]["work_id"] != work_id:
                raise Refusal(
                    f"the supplied assignment names "
                    f"{name_of(expect['work_ref']['work_id'])} and this close "
                    f"is for {name_of(work_id)}")

        def body():
            # THE WORK FIRST.  Review [P0]: the capability check ran before
            # this load, so a close was authorized in the deployment scope
            # whatever scope the Work belonged to -- an actor granted `close`
            # only in the Work's own scope was refused, and a
            # deployment-scoped grant closed a Work in another scope.
            work = self._work(work_id)
            decision = self._require_capability(actor, "close", "close",
                                                scope=work["scope"])
            if work["status"] != "open":
                raise Refusal("Work is already closed")
            if outcome not in INTAKE_OUTCOMES:
                raise Refusal(f"unknown outcome {name_of(outcome)}")
            live = self.assignment_of(work_id)
            if live is not None and expect is ABSENT:
                raise Refusal(
                    "a close that ends a live assignment must supply its exact "
                    "assignment identity")
            if expect is not ABSENT and expect is not None:
                self._expect(expect)
            if live is not None:
                # `phase: None` is TERMINAL, not a scheduler state: a closed
                # Work has no phase at all.
                self._end_assignment(expect, phase=None, gate=None,
                                     cause=f"close:{outcome}", fence=True,
                                     reason=rationale)
            self._store.run(
                "UPDATE work SET status = 'closed', phase = NULL, gate = NULL, "
                "outcome = ?, rationale = ? WHERE work_id = ?",
                outcome, rationale, work_id)
            # RETAINED FOR THE CLOSE ITSELF, whether or not there was ever an
            # assignment: an unclaimed close is still a directly authorized
            # act, and it used to leave nothing behind that said who was
            # allowed to perform it.  Keyed by the Work, which closes once.
            self._record_decision("close", work_id, decision)
            return {"outcome": outcome, "actor": actor, "assignment": live,
                    "decision": decision.as_document()}

        return self._replay(
            operation_id,
            signature_of("close", {"work_id": work_id, "outcome": outcome,
                                   "rationale": rationale, "actor": actor,
                                   "expect": expect}), body)

    # -- the operation journal -----------------------------------------------

    def _replay(self, operation_id, signature, action):
        return self._store.replay(operation_id, signature, action, at=self._now())

    def set_lookup_available(self, available):
        """THE ONE FAULT-INJECTION SEAM in this module.

        It is here because §8 turns on the difference between "it did not
        commit" and "I could not ask".  A store or transport fault has to be
        reachable in a test or the rule that an unanswerable lookup settles
        NOTHING is unprovable.  It affects only `operation_result`.
        """
        self._lookup_available = bool(available)

    def operation_result(self, operation_id):
        """§8's read-only operation-result lookup, or `None` when nothing has
        committed.

        It RAISES when the authority cannot answer, because "I could not ask"
        must never be read as "it did not commit".  Those are different facts
        and a caller that conflated them would settle a live operation.
        """
        check_opaque_id(operation_id, "an operation id")
        if not getattr(self, "_lookup_available", True):
            raise Refusal("the operation-result lookup is unavailable")
        row = self._store.operation_row(operation_id)
        if row is None or row["state"] != "committed":
            return None
        return json.loads(row["result"])

    def operation_record(self, operation_id):
        check_opaque_id(operation_id, "an operation id")
        return self._store.operation_record(operation_id)

    def settle_operation(self, operation_id, *, signature, reason=None,
                         disposition=None, may_retire=False):
        """Make one FIXED operation durably terminal, in ONE authority act.

        A read that says "not committed" proves only its own instant: a
        submitter may already have passed its preconditions and commit right
        after the read.  So this is NOT lookup-then-write.  It is one
        transaction that either finds the committed result or RETIRES the
        identity so nothing can ever commit under it again.

        `signature` is the FIXED operation the caller believes it is settling.
        An id alone proves only that SOMETHING committed under it, so a record
        with different operands is a COLLISION: it fails closed, adopts nothing
        and overwrites nothing (§10.16).

        `may_retire` is the caller's settlement authority and it defaults to
        FALSE.  Retirement kills a live authorization, so a caller with no
        positive evidence that the operation is over -- a timeout before its
        deadline -- may only OBSERVE (§10.15).  The frozen host defaulted this
        to true, so omitting the operand retired an unsubmitted claim on the
        spot; settlement authority is something a caller asserts, never
        something it inherits by saying nothing.

        `disposition` is the terminal outcome this retirement CAUSES and it is
        bound with it.  The authority record and a manager's control row are
        separate durability boundaries; binding the disposition is what stops
        the next caller, arriving on whatever entry path it happens to be on,
        from relabelling a settlement timeout as a refused claim (§10.17).
        """
        # Review [P1]: settlement used the weaker text check and wrote the
        # retirement directly, so it could MINT an invalid durable identity --
        # and a later claim under that id refused its shape before ever seeing
        # the retirement, leaving two authority paths disagreeing about whether
        # the identity existed.  One validator, four paths.
        check_opaque_id(operation_id, "an operation id")
        # The SIGNATURE is deliberately not bounded.  Settlement must compare
        # the exact canonical signature the authority itself produced, including
        # every durable operand, and the ruled contract has no system-wide text
        # bound -- so a settlement-only cap could reject a legitimate signature.
        # Accepted as a decision on review; revisit only through a broader
        # operand/signature ruling.
        #
        # MEASURED at cut 5, where a participant first supplies this operand
        # through a session: a legitimate activity key of 100,000 characters is
        # accepted and journalled, and the signature derived from it is 100,185
        # characters.  A cap below that refuses the settlement of an operation
        # THIS AUTHORITY COMMITTED, so the bound belongs on durable text
        # system-wide rather than here.  Pinned by
        # `test_the_authority_settles_the_largest_signature_it_can_produce`.
        check_text(signature, "a settled operation's signature")
        reason = _optional_text(reason, "a settlement reason")
        disposition = _optional_text(disposition, "a terminal disposition")
        if may_retire is not True and may_retire is not False:
            raise Refusal(
                f"settlement authority is asserted or it is not held; "
                f"may_retire is {name_of(may_retire)}")
        if may_retire and (reason is None or disposition is None):
            raise Refusal(
                "a retirement records why the identity died and what terminal "
                "outcome it causes; both are durable and neither is inferred")
        # RAISES when the authority cannot answer at all, before anything is
        # decided.  An unanswerable lookup settles nothing.
        self.operation_result(operation_id)
        at = self._now()

        def body():
            # RE-READ INSIDE THE SETTLEMENT.  Anything that committed while the
            # lookup was in flight is found here, and after this act the
            # identity is closed to every later and stale submitter alike.
            prior = self._store.operation_row(operation_id)
            if prior is not None:
                if prior["state"] == "retired":
                    return {"kind": "retired",
                            "record": json.loads(prior["detail"])}
                if prior["signature"] != signature:
                    raise Refusal(
                        "operation id was reused for different operands")
                if prior["state"] == "committed":
                    return {"kind": "committed",
                            "result": json.loads(prior["result"])}
                return {"kind": "refused", "detail": prior["detail"]}
            if not may_retire:
                return {"kind": "live", "record": None}
            record = {"reason": reason, "disposition": disposition}
            self._store.record_retirement(operation_id, signature, record, at)
            return {"kind": "retired", "record": record}

        return self._store.transact(body)

    # -- invariants ----------------------------------------------------------

    def assert_invariants(self, work_id):
        """The BACKSTOP, and deliberately not the enforcement.

        Every impossible state below is refused by the transition that would
        have written it.  This exists to catch the one nobody thought of, and it
        raises rather than refusing: an invariant violation is not an ordinary
        outcome a caller may retry, it is a fault.
        """
        work = self._work(work_id)
        failures = []

        def check(ok, message):
            if not ok:
                failures.append(message)

        held = work["handler"] is not None
        fenced = set(self.fenced_generations(work_id))
        if held:
            check(work["phase"] == "active",
                  "a Work with a Handler must be active")
            check(work["status"] == "open",
                  "a closed Work cannot have a Handler")
            if work["contract"] == V11:
                check(work["live_generation"] is None,
                      "a v11 claim mints no generation")
            else:
                check(work["live_generation"] == work["generation_counter"],
                      "the live generation must be the current counter")
                check(work["live_generation"] not in fenced,
                      "a fenced generation is never the live generation")
            check(self.slot_holder(work["handler"]) == work_id,
                  "the Handler must hold this Work's claim slot")
        else:
            check(work["phase"] != "active",
                  "no Work is active without an executor")
            check(work["live_generation"] is None,
                  "an unclaimed Work has no live assignment")
            check(self._store.get(
                "SELECT 1 AS ok FROM claim_slot WHERE work_id = ?",
                work_id) is None,
                "an unclaimed Work holds no participant's claim slot")
        for generation in sorted(fenced):
            check(1 <= generation <= work["generation_counter"],
                  f"fenced generation {generation} is outside the minted range")
        # Review [P2]: this checked gate-implies-block and nothing else, so an
        # open Work in `block` with NO gate, and one in an INVENTED phase, both
        # returned True.  A backstop that only checks one direction of a
        # cross-product is a backstop for one of its two failures.
        if work["status"] == "open":
            check(work["phase"] in CLOSED_PHASES,
                  f"{work['phase']!r} is not one of the closed scheduler phases")
            check((work["phase"] == "block") == (work["gate"] is not None),
                  "block and a gate hold each other: neither occurs alone")
        if work["gate"] is not None:
            parsed = parse_gate(work["gate"])
            check(parsed is not None and parsed["kind"] in GATE_KINDS
                  and parsed["detail"] != "",
                  "a gate is a typed token with a nonempty detail")
        if work["status"] != "open":
            check(work["phase"] is None and not held,
                  "terminal Work has no phase and no Handler")
        if failures:
            raise AssertionError(
                f"v12 authority invariant violated for {work_id}: "
                + "; ".join(failures))
        return True

    def dispose(self):
        self._store.close()


# Review [P1]: these were a second, weaker text rule beside `own`'s -- exact and
# nonempty but not ENCODABLE -- so a lone surrogate reached SQLite from a route,
# a reason, a comment and a plan digest.  They are thin aliases now, over the one
# rule in `identity`, kept only so the call sites read as they did.
def _evidence_text(evidence, member, complaint):
    """One member of gate evidence, as exact durable text.

    The evidence has already been through `own`, so it is built of exact
    built-ins; what is checked here is that the member the gate KIND needs is
    present and is text, rather than merely being something truthy.
    """
    value = evidence.get(member) if type(evidence) is dict else None
    if type(value) is not str or value == "":
        raise Refusal(complaint)
    return value


def _text(value, what):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    return check_text(value, what)


def _optional_text(value, what):
    # The LABEL is caller text at every exported helper, so it is
    # bound by the rule here, once, where it is accepted.
    what = label_of(what)
    return check_text(value, what, optional=True)
