"""Durable Job status reads, independent of a serving manager or publisher."""
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore
from .store import JobStore
from .delegation import ManagerOperations, Unobserved
from .projection import status


def read_status(job_store, *, authority_uuid, incarnation, clock, control_store=None, observation_factory=None):
    """Read existing stores without initialization, migration, or execution.

    The optional factory contributes durable exchange/integration reads only.
    The document observation time is the read time; nested activity timestamps
    remain those recorded by their source. No runtime refresh is performed.
    """
    if observation_factory is not None and control_store is None:
        raise ValueError('an observation factory requires a control store')
    with JobStore.open_readonly(job_store, authority_uuid=authority_uuid, incarnation=incarnation, clock=clock) as jobs:
        if control_store is None:
            return status(jobs, Unobserved(), observed_at=clock())
        with ControlStore.open_readonly(control_store, incarnation=incarnation, clock=clock) as control:
            if observation_factory is None:
                return status(jobs, _ReadOnly(control), observed_at=clock())
            observed = observation_factory(jobs, control)
            try:
                return status(jobs, _Observing(control, observed), observed_at=clock())
            finally:
                close = getattr(observed, 'close', None)
                if close is not None:
                    close()


class _Observing:
    """`_ReadOnly` plus ONE durable-file read, and still no act.

    W85500. THE ONE THING IT ADDS is the exchange observation, which is a read
    of files a worker wrote and this manager's launch delivery named. It
    remains read-only in the sense that matters: it issues no offer, takes no
    claim, applies no canonical ending, and -- the one this Work had to be
    careful about -- performs NO RUNTIME REFRESH.

    WHY THE RUNTIME AXIS IS DELIBERATELY LEFT STALE HERE. Refreshing it means
    `reconcile_runtime`, which RECORDS what it saw; a status command that did
    that would be a read that mutates the control store. So the runtime axis
    in a status document is exactly as fresh as the serving loop that last
    advanced the store, and a store nobody is advancing reports what nobody
    advanced. That is the honest answer, and it is why this class inherits
    `refresh_runtime` answering `None` rather than being given a capability.
    """

    canonical = True

    def __init__(self, control, observed):
        self._operations = ManagerOperations(
            control, None, mint_bearer=_refuses, deliver_bearer=_refuses,
            observe_exchange=_exchange_read(observed),
            # W126558: AND THE OTHER READ, BY NAME AND ONLY IF IT IS THERE.
            # An observation factory composed before this member existed is
            # still a complete one -- an integration read it does not have is
            # a deployment with no integration to observe, which is exactly
            # what `None` says. Taken by name for `_exchange_read`'s reason:
            # passing the object would hand this composition whatever else it
            # happened to carry.
            observe_integration=_integration_read(observed))

    def canonical_operation(self, act, offer_id):
        return self._operations.canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self._operations.receipt_of(operation_id)

    def observe(self, stage):
        return self._operations.observe(stage)

    def refresh_runtime(self, stage):
        """Never. See the class docstring: this one would WRITE."""
        return None


def _exchange_read(observed):
    """The one member an observation factory is allowed to contribute.

    Taken by NAME from the object rather than accepting the object itself as a
    capability: a factory that also carried a dispatch or an ending would hand
    those to `ManagerOperations` if the whole object were passed through, and
    the point of this composition is that it cannot.
    """
    read = getattr(observed, "observe_exchange", None)
    if read is None:
        raise SystemExit(
            "--observe names a factory whose object has no observe_exchange; "
            "an observation surface that cannot read the exchange is the "
            "default this operand exists to replace")
    return read


def _integration_read(observed):
    """The optional second member an observation factory may contribute.

    OPTIONAL WHERE THE EXCHANGE READ IS REQUIRED, and the difference is the
    whole compatibility rule: `--observe` exists to read the exchange, so a
    factory that cannot is the default this operand replaces; an integration
    read is a later capability, and a factory composed without one keeps its
    exact previous behaviour rather than becoming invalid.

    IT GAINS NOTHING ELSE. This surface still performs no refresh and no
    serving act; what it adds is one more read of what a deployment already
    knows.
    """
    return getattr(observed, "observe_integration", None)


class _ReadOnly:
    """The manager's public READS, with every act refused.

    `status` is a read-only surface and this is what makes that a mechanism
    rather than a promise: the object it is handed cannot issue an offer, take
    a claim, or apply a canonical ending, because it has no method that does.

    WHAT THAT COSTS, STATED RATHER THAN HIDDEN. A status run reports the
    pipeline as this store has RECORDED it, plus the canonical observation of
    each stage's current episode. An offer that ended after the last sweep is
    canonically over and not yet recorded here, so the stage still reads
    `offered` until a serving reconciler attaches and applies it. A serving
    deployment is therefore at most one tick behind; a store nobody is
    advancing is exactly as behind as "nobody looked", which is the honest
    answer for a read-only view of it.
    """

    canonical = True

    def __init__(self, control):
        # NO PORT, because none of the three members below reaches one: the
        # authority is spoken to by acts, and this object has none. Handing it
        # a real session would put a capability inside a read-only surface for
        # nothing to use.
        self._operations = ManagerOperations(
            control, None, mint_bearer=_refuses, deliver_bearer=_refuses)

    def canonical_operation(self, act, offer_id):
        return self._operations.canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self._operations.receipt_of(operation_id)

    def observe(self, stage):
        return self._operations.observe(stage)

    # NO `attach` AND NO `drain`, and review [P2, 2026-09-03] is why the
    # earlier draft's were removed rather than wired up. Attaching asks the
    # manager to republish canonical state; APPLYING what comes back ends an
    # episode, which is a durable act. A read-only surface performs none, so a
    # status run that attached would either write -- and stop being read-only
    # -- or drain assertions into a handler that ignored them, which is an
    # operator being told a fact was consumed when it was discarded. This
    # object has exactly the members `status` calls, and the serving
    # reconciler is the one consumer that attaches.


def _refuses(*ignored):
    raise ContractRefusal(
        "refused", "capability",
        "the status surface holds no authority capability; reading a status "
        "never mints, delivers or spends one")


