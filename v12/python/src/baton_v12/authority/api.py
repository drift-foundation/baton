"""The two public faces of the authority.

`Authority` is TRUSTED BOOTSTRAP.  It creates, opens and disposes of the store,
and in later cuts it certifies contracts, permits transitions, configures
policy, routes and capabilities, creates Work, reads projections and MINTS
SESSIONS.  It performs no runtime transition itself: a bootstrap that could also
claim would be one object holding both the configuration authority and the
authority it configures.

The minted `AuthoritySession` is the RUNTIME face and arrives in cut 5.  It is
participant-bound: the actor and claimant identity come from the binding and not
from an operand, it accepts only owned exact operand documents, it exposes an
enumerated transition and read surface, and it returns fresh built-ins.  This
module holds its place deliberately rather than leaving the shape to be
discovered later.

CUT 1 IMPLEMENTS CREATION, OPENING AND DISPOSAL ONLY.  Every other method
belongs to a later reviewed cut and is absent rather than stubbed, because a
stub that raises `NotImplementedError` is a method the exported surface claims
to have.
"""

from .core import CAPABILITIES, Core
from .errors import Refusal
from .identity import check_authority_uuid
from .session import _mint_session
from .store import Store

__all__ = ["Authority"]


class Authority:
    """The trusted bootstrap face.

    Construct it through `create` or `open`.  Direct construction takes an
    already-owned `Store`, which is why it is not the documented entry point:
    the two named operations are what carry the non-adoption rules, and a
    constructor that also accepted a path would be a third way in that skipped
    them.
    """

    def __init__(self, store, *, clock=None, new_uuid=None):
        if not isinstance(store, Store):
            raise Refusal(
                "an Authority is constructed from an owned store; use "
                "Authority.create or Authority.open")
        self._core = Core(store, clock=clock, new_uuid=new_uuid)

    @classmethod
    def create(cls, path, *, authority_uuid, clock=None, new_uuid=None):
        """Create a NEW authority at an absent path.

        `clock` and `new_uuid` are injected at trusted bootstrap so tests are
        deterministic.  They are BOOTSTRAP operands and never runtime ones: a
        session that could supply its own clock could date its own evidence, and
        SQLite time and process-local counters are not authority.  Production
        defaults arrive with the transitions that need them, in later cuts.
        """
        check_authority_uuid(authority_uuid)
        return cls(Store.create(path, authority_uuid=authority_uuid),
                   clock=clock, new_uuid=new_uuid)

    @classmethod
    def open(cls, path, *, expected_authority_uuid=None, clock=None, new_uuid=None):
        """Open an EXISTING recognized authority store.

        `expected_authority_uuid` is a compare-and-swap on identity, not a
        default.  Supplying it and being wrong is a refusal; omitting it means
        "whichever authority this is", which is a legitimate thing for an
        operator tool to mean and is never a legitimate thing for a deployment
        that already knows the answer to mean.
        """
        return cls(Store.open(path,
                              expected_authority_uuid=expected_authority_uuid),
                   clock=clock, new_uuid=new_uuid)

    @classmethod
    def open_readonly(cls, path, *, expected_authority_uuid=None, clock=None,
                      new_uuid=None):
        """Open an EXISTING recognized authority store WITHOUT writing to it.

        W126880. The same public face and the same readers, over a store this
        process cannot write: `open` takes a write lock, applies the schema and
        sets a persistent journal mode, which is right for a serving
        deployment and wrong for a separate process that only wants to read
        committed evidence.

        `expected_authority_uuid` KEEPS ITS MEANING exactly. It is a
        compare-and-swap on identity rather than a default, and a deployment
        that already knows which authority it is reading supplies it; omitting
        it means "whichever authority this is", which stays a legitimate thing
        for an operator tool to mean.

        WHAT THE HANDLE CANNOT DO. Every transition on it refuses at this
        store's own boundary before a statement is issued, so a caller holding
        one reads the committed record and performs nothing.
        """
        return cls(
            Store.open_readonly(
                path, expected_authority_uuid=expected_authority_uuid),
            clock=clock, new_uuid=new_uuid)

    @property
    def authority_uuid(self):
        """The durable UUID this store answers to.

        Readable because every assignment identity names it and a consumer
        assembling one needs it.  It is the only fact about the store this face
        exposes: not the path, not the connection, not the schema.
        """
        return self._core.authority_uuid

    # -- configuration -------------------------------------------------------
    #
    # This face CONFIGURES and it does not act.  A bootstrap that could also
    # claim would be one object holding both the configuration authority and
    # the authority it configures -- which is the defect the frozen Node host
    # was corrected for: through one advertised boundary a consumer granted
    # itself the close capability, closed the live Work as that actor, and
    # moved the canonical target with zero proposals and zero receipts.
    #
    # The runtime transitions therefore live on `Core` and reach the outside
    # world only through the participant-bound session, which arrives in cut 5.

    def certify_contract(self, contract, profile="reference"):
        return self._core.certify_contract(contract, profile)

    def withdraw_certification(self, contract):
        return self._core.withdraw_certification(contract)

    def is_certified(self, contract):
        return self._core.is_certified(contract)

    def permit_contract_transition(self, from_contract, to_contract):
        return self._core.permit_contract_transition(from_contract, to_contract)

    def permits_contract_transition(self, from_contract, to_contract):
        return self._core.permits_contract_transition(from_contract, to_contract)

    def set_policy(self, key, value):
        return self._core.set_policy(key, value)

    def policy(self, key, fallback=None):
        return self._core.policy(key, fallback)

    def canonical_target(self):
        return self._core.canonical_target()

    def accept_base(self, acceptance, *, operation_id):
        return self._core.accept_base(acceptance, operation_id=operation_id)

    def grant_capability(self, participant, capability, *, scope=None):
        return self._core.grant_capability(participant, capability,
                                           scope=scope)

    def revoke_capability(self, participant, capability, *, scope=None):
        return self._core.revoke_capability(participant, capability,
                                            scope=scope)

    def holds_capability(self, participant, capability, *, scope=None):
        return self._core.holds_capability(participant, capability,
                                           scope=scope)

    # -- the principal mapping (W16821) --------------------------------------
    #
    # ON THIS FACE AND NOT ON THE SESSION, for the reason the two faces exist
    # at all: a session that could rebind its own endpoint could move its claim
    # slot, its grants and everything it is attributed for onto another
    # identity.  Binding an address to a principal is a deployment act.

    def bind_endpoint(self, participant, principal):
        return self._core.bind_endpoint(participant, principal)

    def principal_of(self, participant):
        return self._core.principal_of(participant)

    def endpoints_of(self, principal):
        return self._core.endpoints_of(principal)

    def slot_holder_of_principal(self, principal):
        return self._core.slot_holder_of_principal(principal)

    def policy_generation(self):
        return self._core.policy_generation()

    def capabilities_of(self, participant):
        return self._core.capabilities_of(participant)

    def labels_of(self, work_id):
        return self._core.labels_of(work_id)

    def work_creation(self, work_id):
        """W29400: the act that made this Work, from the Work alone."""
        return self._core.work_creation(work_id)

    def work_label_events(self, work_id):
        return self._core.work_label_events(work_id)

    def works_with_labels(self, *, all_of=(), none_of=()):
        return self._core.works_with_labels(all_of=all_of, none_of=none_of)

    def grants_of(self, participant):
        return self._core.grants_of(participant)

    def decision_of(self, act, act_id):
        return self._core.decision_of(act, act_id)

    def create_work(self, work_id, route, *, operation_id, contract=None,
                    phase="queued", gate=None, scope=None, labels=()):
        """W29400: the public creation face, with an identity and labels.

        `operation_id` is REQUIRED, which is what makes a creation replayable
        and what gives its create-time labels an act to be attributed to. The
        internal `Core.create_work` used to be the only door and took neither.
        """
        if contract is None:
            return self._core.create_work(work_id, route,
                                          operation_id=operation_id,
                                          phase=phase, gate=gate, scope=scope,
                                          labels=labels)
        return self._core.create_work(work_id, route,
                                      operation_id=operation_id,
                                      contract=contract, phase=phase,
                                      gate=gate, scope=scope, labels=labels)

    def add_route_handler(self, route, participant):
        return self._core.add_route_handler(route, participant)

    # -- W321688: the canonical dossier binding ------------------------------
    #
    # ON THE TRUSTED BOOTSTRAP FACE, not the session's, and that is the
    # deliberate part. A dossier address is deployment configuration of the same
    # kind as creating the Work it belongs to: it is allocated once by whoever
    # stands the Work up, and it is not a runtime transition a participant
    # performs against Work it holds. Putting `bind_dossier` on the session
    # would have made a claimant able to rename its own record.
    #
    # THE READS ARE HERE TOO rather than only on the session, because the
    # question "where does this Work's record live" is asked by operators,
    # materializers and reviewers who hold no claim and should need none.

    def bind_dossier(self, work_id, locator, *, operation_id):
        return self._core.bind_dossier(work_id, locator,
                                       operation_id=operation_id)

    def dossier_of(self, work_id):
        return self._core.dossier_of(work_id)

    def dossier_work(self, locator):
        return self._core.dossier_work(locator)

    def record_dossier_evidence(self, work_id, reference, digest, *,
                                operation_id):
        return self._core.record_dossier_evidence(
            work_id, reference, digest, operation_id=operation_id)

    def dossier_evidence(self, work_id):
        return self._core.dossier_evidence(work_id)

    # -- W321689: one command request, one durable meaning -------------------
    #
    # ON THE OPERATOR FACE, beside `accept_base` and for the same reason: it is
    # a composite COMMAND's own act, performed by whoever holds the deployment,
    # and it journals a request rather than performing a transition. A session
    # that could bind requests about Work it does not hold would be keeping a
    # record about somebody else's act.

    def bind_request(self, work_id, request, *, operation_id):
        return self._core.bind_request(work_id, request,
                                       operation_id=operation_id)

    @staticmethod
    def stored_identity(path):
        """What a store says it IS, read-only, without opening it for use.

        W321688 review 2026-10-18T08-48-00Z. THE SUPPORTED OBSERVATION THIS
        BOUNDARY WAS MISSING. `open` REFUSES a store this build does not speak,
        which is correct and is exactly why it cannot answer "which version is
        that file" -- so a recovery check asking the compatibility question had
        no public surface and reached for raw SQL instead. This is that surface:
        the authority's OWN read-only probe, the one `open` itself uses before
        it decides anything, exposed rather than reimplemented.

        It answers a fresh mapping of the recorded metadata, or `None` when the
        file is not a database this build can read at all -- which is an answer
        and not an error. It opens nothing for use, writes no row, creates no
        journal and performs no migration.

        WHAT IT STILL DOES NOT PROMISE, said plainly: `mode=ro` is SQLite's
        guarantee about the DATABASE, and owner M128249 accepted that reading a
        WAL database may create or maintain its `-shm`/`-wal` coordination
        files. A caller that must leave a byte-identical set behind reads a COPY
        and verifies the original afterwards; this method does not pretend that
        guarantee is SQLite's to give.
        """
        from .store import _probe

        return _probe(path)

    # -- projections ---------------------------------------------------------

    def project_work(self, work_id):
        return self._core.project_work(work_id)

    def assignment_of(self, work_id):
        return self._core.assignment_of(work_id)

    def fenced_generations(self, work_id):
        return self._core.fenced_generations(work_id)

    def assignment_events(self, work_id):
        return self._core.assignment_events(work_id)

    def gate_evidence(self, work_id):
        return self._core.gate_evidence(work_id)

    def slot_holder(self, participant):
        return self._core.slot_holder(participant)

    def assert_invariants(self, work_id):
        return self._core.assert_invariants(work_id)

    # -- journal READS ------------------------------------------------------
    #
    # Reads only.  `settle_operation` RETIRES an identity, which is a
    # transition, so it stays on `Core` and reaches the outside world through
    # the participant-bound session in cut 5 -- not through the face that
    # configures the deployment.

    def operation_result(self, operation_id):
        return self._core.operation_result(operation_id)

    def operation_record(self, operation_id):
        return self._core.operation_record(operation_id)

    # -- workflow READS ------------------------------------------------------

    def contract_events(self, work_id):
        return self._core.contract_events(work_id)

    def activities(self, work_id):
        return self._core.activities(work_id)

    def proposal(self, proposal_id):
        return self._core.proposal(proposal_id)

    def proposals_of(self, work_id):
        """W321689: which candidates one Work has published.

        ON THIS FACE and not the session's, for the reason `works_with_labels`
        is here: it answers an INVENTORY question rather than a fact about the
        asker's own assignment, and the asker is an operator -- the human whose
        disposition is due -- who holds no claim and should need none.  A
        session reading it would be reading the publication history of Work it
        may have no part in.
        """
        return self._core.proposals_of(work_id)

    def receipts(self, proposal_id):
        return self._core.receipts(proposal_id)

    def receipt(self, proposal_id, kind):
        return self._core.receipt(proposal_id, kind)

    def integration_attempts(self, proposal_id):
        return self._core.integration_attempts(proposal_id)

    # -- minting the runtime face --------------------------------------------

    def session(self, participant):
        """Mint the narrow runtime handle for ONE participant.

        This is the only route to a transition at all.  The bootstrap face
        performs none of them, which is the whole point of there being two
        faces: a deployment holds this object at start-up and hands out
        sessions, and a session holds no path, no store and no way back to
        here.
        """
        return _mint_session(self._core, participant)

    # -- disposal -------------------------------------------------------------

    def dispose(self):
        """Release the store handle.

        `dispose`, not `close`: `close` is the Baton verb that TERMINALIZES a
        Work, and cut 4 put exactly that verb on the session.  One name meaning
        both "release the file handle" and "end this Work with an outcome" is an
        API that invites the wrong one -- so the collision is removed rather
        than documented.
        """
        self._core.dispose()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        self.dispose()
        return False
