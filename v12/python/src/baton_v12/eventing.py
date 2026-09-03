"""The transient event transport, and the run-to-completion pump that drains it.

W73629. THIS IS NOT AN AUTHORITY AND MUST NEVER BECOME ONE. Both v12 products
keep their own SQLite file, and each one's store is the only thing that says
what is true. What travels through here is a LEVEL-TRIGGERED assertion about
state those stores already hold -- "offer X is currently abandoned" -- so
losing the whole queue is safe: the producer regenerates the same assertions
from its rows at the next startup or consumer attachment, and the consumer's
effect of applying one is idempotent. A durable queue would be a third account
of state two stores already own, and the first time it disagreed with them
somebody would have to decide which to believe.

WHY A PUMP RATHER THAN A CALLBACK. In-process does not mean inline. A producer
that invoked its consumer from inside `publish` would run the consumer's store
writes inside the producer's transaction -- two owners in one transaction, the
exact boundary this distribution keeps -- and a consumer that published a
follow-up would re-enter the dispatcher underneath itself, so the "one handler
at a time" rule would hold only until the first interesting case. So
`publish` appends an owned copy and RETURNS, and one top-level `pump` call
dispatches what has accumulated.

WHAT A HANDLER MAY DO, written down because the shape is the contract. It
processes ONE message, records its durable effect or the act it now owes,
enqueues any follow-up, and returns. It never waits for another event, and it
never calls the pump. Worker-directed or otherwise blocking activity is
outside this loop entirely: its request is represented durably, its completion
arrives later as another event, and the pump stays free to serve unrelated
state meanwhile.

The whole thing is a list and a loop on purpose. A single-process deployment
needs no `asyncio`, no third-party signal package and no broker, and adopting
one would import a scheduler whose re-entrancy rules are not these.
"""

from .contracts import ContractRefusal, own
from .contracts.errors import name_value
from .worker_manager import boundaries

__all__ = ["MAX_PENDING", "EventQueue", "pump"]

# One drain's worth of events. A bound rather than a policy: a producer that
# enumerated an unbounded number of rows into memory would be a producer that
# can end the process, and discovering that at the bound names the producer
# instead of the allocator.
MAX_PENDING = 4096

_KIND = "kind"


class EventQueue:
    """A transient, ordered, non-reentrant hand-off between two products.

    Ordered because a consumer applying a stale assertion after a fresh one
    would regress its own state; the consumer ALSO compares revisions, because
    order within one queue says nothing about two producers or two drains.
    """

    __slots__ = ("_pending", "_dispatching")

    def __init__(self):
        self._pending = []
        self._dispatching = False

    def publish(self, event):
        """Append ONE owned event and return. Nothing is dispatched here.

        The document is owned on the way in, so the producer cannot mutate an
        event a consumer has not read yet, and a value carrying behaviour
        cannot reach a handler at all. Publishing DURING a dispatch is
        ordinary and is what a follow-up looks like: it joins the same queue
        and is dispatched after the current handler returns.
        """
        taken = boundaries.document(own(event, what="a published event"),
                                    "a published event")
        if _KIND not in taken:
            raise ContractRefusal(
                "integrity", "schema",
                f"a published event names its kind; this carries "
                f"{name_value(sorted(taken))}")
        boundaries.text(taken[_KIND], "a published event's kind")
        if len(self._pending) >= MAX_PENDING:
            raise ContractRefusal(
                "refused", "precondition",
                f"this transport holds {MAX_PENDING} undispatched events; a "
                f"producer enumerating more than one drain can carry is a "
                f"producer that would end the process, and the bound names it")
        self._pending.append(taken)
        return None

    def pending(self):
        """A copy of what is queued, for a caller reporting rather than acting."""
        return [dict(event) for event in self._pending]

    def _take(self):
        held = self._pending
        self._pending = []
        return held


def pump(queue, handlers, *, quiescent=()):
    """Dispatch everything queued, to completion, exactly once each.

    RUN TO COMPLETION AND NEVER RECURSIVELY. One handler runs at a time; a
    follow-up it publishes is appended to the queue and dispatched by a LATER
    turn of this same loop, after the handler that produced it has returned.
    Re-entering the pump refuses rather than nesting, because a nested drain
    would dispatch a handler underneath another handler and the one-at-a-time
    rule would be true only of the outermost call.

    NOTHING IS DISPATCHED WHILE A STORE TRANSACTION IS HELD. Each `quiescent`
    entry answers whether one store is mid-transaction, and every one of them
    is asked before the first handler runs. A producer that published from
    inside its own write would otherwise have a consumer writing a second
    store inside it -- one transaction with two owners, which is the boundary
    this distribution exists to keep. This is checked rather than promised,
    because "the caller will only pump at the top level" is exactly the kind
    of rule that holds until somebody adds a convenient call site.

    Answers how many events were dispatched, so a caller can report a drain
    that did nothing without inspecting the queue.
    """
    if type(queue) is not EventQueue:
        raise ContractRefusal(
            "integrity", "schema",
            f"the pump drains this build's own transport; this is "
            f"{name_value(queue)}")
    if type(handlers) is not dict:
        raise ContractRefusal(
            "integrity", "schema",
            f"the pump takes a kind-to-handler table; this is "
            f"{name_value(handlers)}")
    for kind, handler in sorted(handlers.items()):
        boundaries.text(kind, "a handled event kind")
        boundaries.capability(handler, f"the {kind} handler")
    if queue._dispatching:
        raise ContractRefusal(
            "refused", "precondition",
            "this transport is already dispatching; a follow-up event is "
            "queued and drained by the running pump, and a second pump "
            "underneath the first would run one handler inside another")
    for probe in quiescent:
        boundaries.capability(probe, "a store's transaction probe")
        if probe():
            raise ContractRefusal(
                "refused", "precondition",
                "a store transaction is open; events are dispatched at the "
                "top level after every producer has committed and released "
                "its locks, never underneath one of them")
    dispatched = 0
    queue._dispatching = True
    try:
        while True:
            taken = queue._take()
            if not taken:
                return dispatched
            for event in taken:
                handler = handlers.get(event[_KIND])
                # AN UNHANDLED KIND IS ORDINARY, not an error. A producer
                # publishes what its own state says; a consumer that has no
                # effect for one kind has nothing to do with it, and refusing
                # here would make adding a kind break every existing consumer.
                if handler is None:
                    continue
                handler(event)
                dispatched += 1
    finally:
        queue._dispatching = False
