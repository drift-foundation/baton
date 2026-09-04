"""The one entry point onto the v12 Job manager: submit, status, serve.

W71875. THREE SUBCOMMANDS AND NO FOURTH. `submit` records one bounded
multi-Job submission; `status` prints the read-only projection; `serve` runs
the long-lived control loop. Everything else an operator used to do by hand --
issuing an offer, taking a claim, deciding what is next -- is what `serve`
derives, which is the point of the leaf.

WHAT THIS TOOL WILL NOT CONSTRUCT. It does not mint an authority session and
it does not mint bearers. `baton_v12.worker_manager` states its own rule --
the manager consumes an already-minted, participant-bound session that trusted
deployment supplies -- and a command-line tool that built one would be a way
to obtain authority by running a script in the checkout. So `serve` takes
`--operations module:attribute`, imports exactly that name, and calls it with
the two open stores; supplying the port, the mint and the bearer delivery is
the deployment's business and remains visible in the deployment's own code.

`submit` and `status` need no such capability. A submission is recorded in the
Job store alone, and a status assembled without the manager's control store
says so in its own `canonical` member rather than reporting an empty pipeline
as a quiet one.

JSON ON STDOUT, ONE DOCUMENT PER RUN. The output is the versioned document the
package answers with, so a program consuming this tool and a program calling
the package read the same thing.

THE TWO STORES ARE SEPARATE OPERANDS AND ARE NOT ASSUMED TO BELONG TOGETHER.
Review [P1]: `--store` and `--control` are chosen independently, so pointing a
second Job store at a control store another one is already driving is a typo
away. Nothing here pairs them by configuration; the package proves each
canonical act against the persisted Job/stage intent instead, and a control
store holding somebody else's offer under this store's derived identity refuses
rather than being adopted or projected.
"""

import importlib
import json
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, ManagerOperations, Unobserved,
                                   read_submission, reconcile, serve, status,
                                   submit)
from baton_v12.worker_manager import ControlStore

__all__ = ["main"]


def _utc_clock():
    """The one instant source this tool builds, when a caller supplies none.

    Built once and threaded through, because a tool that called
    `datetime.now()` in three places would have three clocks and a fixture
    pinning one would silently not pin the others.
    """
    from datetime import datetime, timezone

    def now():
        moment = datetime.now(timezone.utc)
        return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
                + f"{moment.microsecond // 1000:03d}Z")

    return now


def _job_store(taken, clock):
    return JobStore.open(taken.store, incarnation=taken.incarnation,
                         clock=clock)


def _read(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _emit(document, stream):
    json.dump(document, stream, indent=2, sort_keys=False, ensure_ascii=False)
    stream.write("\n")
    return 0


def _submit(taken, clock, stream):
    with _job_store(taken, clock) as store:
        return _emit(submit(store, read_submission(_read(taken.document))),
                     stream)


def _status(taken, clock, stream):
    with _job_store(taken, clock) as store:
        if taken.control is None:
            # NO CONTROL STORE IS A LEGITIMATE ANSWER, and the projection
            # marks itself as unobserved rather than reporting a pipeline
            # nobody looked at.
            return _emit(status(store, Unobserved(), observed_at=clock()),
                         stream)
        with ControlStore.open(taken.control, incarnation=taken.incarnation,
                               clock=clock) as control:
            return _emit(status(store, _ReadOnly(control),
                                observed_at=clock()), stream)


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


def _operations_from(name, store, control):
    """Import exactly the deployment factory the operator named.

    `module:attribute`, and nothing is searched for. A tool that guessed at a
    factory would be choosing which authority the manager acts under.
    """
    if ":" not in name:
        raise SystemExit(
            f"--operations names a deployment factory as module:attribute; "
            f"this is {name!r}")
    where, _, attribute = name.partition(":")
    factory = getattr(importlib.import_module(where), attribute)
    return factory(store, control)


def _release(operations, stream):
    """Give a factory-owned object back whatever it opened, exactly once.

    W76207: a production factory opens an Authority, a credential home and a
    launch home that the two stores' context managers know nothing about, so
    a serve that returned or failed simply leaked them. The factory owns those
    handles, so the factory's object is asked to close them -- this tool does
    not go looking for what they were.

    OPTIONAL BY DESIGN AND SILENT WHEN ABSENT. Most operations objects hold
    nothing to release; requiring the member would make every deployment
    declare a teardown it does not need. A failure while releasing is reported
    and not raised: it must not replace the outcome the run already reached,
    and it must not stop the remaining handles from being released.
    """
    close = getattr(operations, "close", None)
    if close is None:
        return None
    try:
        close()
    except BaseException as failure:
        print(f"the deployment's operations did not release cleanly: "
              f"{type(failure).__name__}: {failure}", file=stream)
    return None


def _serve(taken, clock, stream):
    import signal
    import time

    with _job_store(taken, clock) as store:
        with ControlStore.open(taken.control, incarnation=taken.incarnation,
                               clock=clock) as control:
            # CONSTRUCTION IS INSIDE THE RELEASE, and review [P1] is why the
            # earlier version's comment was a claim the code did not keep: the
            # call sat in FRONT of the `try`, so a factory that opened an
            # Authority and then failed on its next operand returned nothing
            # for `_release` to close.
            #
            # WHAT THIS CAN AND CANNOT DO, stated because the difference
            # matters. It guarantees that an object the factory RETURNED is
            # always released, however this block leaves. It cannot release
            # handles a factory took and then abandoned by raising -- nothing
            # here ever saw them -- so a factory that acquires more than one
            # resource owns cleaning up its own partial construction, and this
            # tool holds it to that rather than pretending to do it for it.
            operations = None
            try:
                operations = _operations_from(taken.operations, store,
                                              control)
                running = [True]

                def stop(number, frame):
                    # POLITE, AND ONCE. The tick in flight finishes and its
                    # receipts are written; a loop that died mid-act would
                    # leave exactly the performed-but-unrecorded window
                    # reconciliation exists to close, for no reason.
                    running[0] = False

                signal.signal(signal.SIGINT, stop)
                signal.signal(signal.SIGTERM, stop)
                if taken.once:
                    return _emit(reconcile(store, operations, now=clock()),
                                 stream)
                return _emit(serve(store, operations, clock=clock,
                                   sleep=time.sleep,
                                   should_continue=lambda: running[0],
                                   interval=taken.interval), stream)
            finally:
                if operations is not None:
                    _release(operations, stream)


def main(argv, *, clock=None, stream=None):
    import argparse

    parser = argparse.ArgumentParser(
        prog="job_manager",
        description="Submit Jobs to the v12 Job manager, read its status, or "
                    "run its control loop.")
    parser.add_argument("--store", required=True,
                        help="the Job store's path; there is no default, and "
                             "one inside the checkout is what the external "
                             "state root exists to prevent")
    parser.add_argument("--incarnation", required=True,
                        help="this process's incarnation, which is what "
                             "restart recovery distinguishes managers by")
    commands = parser.add_subparsers(dest="command", required=True)

    submitting = commands.add_parser(
        "submit", help="record one versioned multi-Job submission")
    submitting.add_argument("--document", required=True,
                            help="the submission JSON, or - for stdin")
    submitting.set_defaults(run=_submit)

    reading = commands.add_parser(
        "status", help="print the read-only status projection")
    reading.add_argument("--control", default=None,
                         help="the Worker Manager control store; without it "
                              "the projection reports canonical=false rather "
                              "than an empty pipeline, and with one that is "
                              "driving another Job store it refuses rather "
                              "than projecting that store's offers as these "
                              "Jobs'")
    reading.set_defaults(run=_status)

    serving = commands.add_parser(
        "serve", help="run the persistent control loop")
    serving.add_argument("--control", required=True,
                         help="the Worker Manager control store; each act is "
                              "proved against this Job store's own intent, so "
                              "one already driving another Job store refuses "
                              "instead of being adopted")
    serving.add_argument("--operations", required=True,
                         help="module:attribute of the deployment factory "
                              "called with (job_store, control_store)")
    serving.add_argument("--interval", type=int, default=5,
                         help="seconds between ticks")
    serving.add_argument("--once", action="store_true",
                         help="recover and sweep exactly once, then stop")
    serving.set_defaults(run=_serve)

    taken = parser.parse_args(argv)
    return taken.run(taken, clock or _utc_clock(),
                     stream if stream is not None else sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
