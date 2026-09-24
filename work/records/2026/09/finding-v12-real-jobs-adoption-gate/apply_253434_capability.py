"""Claim-253434: the composed abandonment route, in the two owned product files.

Owner 253388 selected this capability and review 2026-09-24T03:32:55Z answered
the three behaviours I had left unread:

  * `_adopted` is called BEFORE the answered-terminal check, so adoption itself
    is available on the faulted path;
  * `_mounted` ALLOCATES and composes and refuses historical mounts — so an
    abandonment must not call it;
  * a started `_credential` uses live proof or orphan teardown, and only the
    `not-started` branch materializes — so a started attempt cannot be made to
    re-create a credential here;
  * and `ending` skips all recovery after a committed historical cleanup.

So the design follows `cancel_attempt` for the roots -- `assignment_workspace`,
which adopts the ordinary pair rather than composing a stage's -- and `ending`
for the deliveries, and it refuses before touching `_credential` unless the
runtime actually started. Deleted or read-only roots and a removed credential
therefore reach `OrphanTeardown` or `None` rather than forcing a recreation.

WHAT IS NOT INVENTED: the operation. `intake.abandon_attempt` owns the order,
the fence, the removal and the settlement; this composes its three operands and
calls it.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
WORKER = CHECKOUT / "v12" / "python" / "tools" / "single_worker.py"
STAGE = CHECKOUT / "v12" / "python" / "tools" / "stage_execution.py"

WORKER_ANCHOR = '''    def ending(self, stage, job):
        """Drive ONE answered attempt through the already-ruled ending.'''

WORKER_ADDED = '''    def abandon_attempt(self, *, attempt_id, reason, stage=None):
        """W247941: the manager's FOURTH ending, reachable by this worker's owner.

        THE COMPOSITION OWNS THIS AND AN ORCHESTRATOR CANNOT. `abandon_attempt`
        needs the Authority port, a per-attempt adapter carrying the deliveries
        the START created, and the custody capability -- all three this
        composition's. A supervisor that rebuilt them from this module's
        private state would be a second controller over one security boundary,
        which is the same rule `cancel_attempt` records.

        AND IT IS A DECLARATION, NOT AN OBSERVATION. `reason` is the caller's
        own account of why the attempt is over; nothing here reads a clock,
        counts a retry or measures silence. The product is emphatic that
        calling the operation IS the declaration, so a caller that has not
        decided must not call this.

        WHY THE ROOTS COME FROM `assignment_workspace` AND NOT `_mounted`.
        `_mounted` allocates the ordinary pair AND lets a stage composition
        answer a different one, and it refuses a historical mount -- both are
        right for a start and wrong for a removal, which must not allocate
        anything. This adopts the same pair `cancel_attempt` and `reconcile`
        do.

        AND WHY THE RUNTIME IS PROVED FIRST. `_credential`'s `not-started`
        branch MATERIALIZES a credential. Abandonment ends an attempt whose
        runtime started, so proving that here keeps a removal from creating a
        secret on its way to destroying one -- and it is the same precondition
        `intake.abandon_attempt` states, refused earlier and by name.
        """
        boundaries.identity(attempt_id, "a runtime attempt id")
        reason = boundaries.text(reason, "an abandonment reason")
        state = attempt_runtime_of(self.control, attempt_id)
        if state["runtime_id"] is None:
            _refuse(f"attempt {attempt_id!r} has no attached runtime; "
                    f"abandonment ends an attempt whose runtime STARTED and "
                    f"whose worker then never answered, and there is nothing "
                    f"here to end", category="refused", code="precondition")
        roots = workspaces.assignment_workspace(
            self.group, self.given["workspace_storage"], attempt_id)
        # THE LAUNCH DELIVERY IS ADOPTED WHEN THIS CALLER CAN NAME THE STAGE,
        # and its ABSENCE is a fact rather than a failure: `launch.adopt`
        # answers None for a delivery no container ever mounted, and a removal
        # that authored a replacement would turn lost evidence into state that
        # looks valid.
        launched = self._adopted(stage) if stage is not None else None
        delivery, orphan = self._credential(attempt_id, state, roots, launched)
        adapter = self._adapter(roots, delivery, orphan, launched)
        return intake.abandon_attempt(
            self.control, self.port, adapter, attempt_id=attempt_id,
            reason=reason,
            retention_policy_digest=self.given["retention_policy_digest"])

'''

WORKER_EXPOSE_ANCHOR = '''    def cancel_attempt(self, *, attempt_id, reason):
        """W236087: the composed worker's own stop, reachable by its owner."""
        return self._worker.cancel_attempt(attempt_id=attempt_id,
                                           reason=reason)
'''

WORKER_EXPOSE = '''    def cancel_attempt(self, *, attempt_id, reason):
        """W236087: the composed worker's own stop, reachable by its owner."""
        return self._worker.cancel_attempt(attempt_id=attempt_id,
                                           reason=reason)

    def abandon_attempt(self, *, attempt_id, reason, stage=None):
        """W247941: the composed worker's own FOURTH ending, likewise."""
        return self._worker.abandon_attempt(attempt_id=attempt_id,
                                            reason=reason, stage=stage)
'''

STAGE_ANCHOR = '''    # -- the owned observation and the two stage driver operations -----------'''

STAGE_ADDED = '''    def abandon_attempt(self, *, attempt_id, reason, stage=None):
        """Route the FOURTH ending to the worker that STARTED this attempt.

        W247941. A faulted receiptless attempt has none of the three ordinary
        authorizations, so `intake.abandon_attempt` is the only ending it can
        reach -- and an orchestrator cannot perform it, because the adapter it
        needs carries the deliveries that worker's start created. This routes
        it exactly as `cancel_attempt` routes a stop.

        BY THE RECORDED ALLOCATION AND NEVER BY ROLE. An attempt belongs to the
        worker the scheduler reserved for it; picking the first worker of a
        matching role would abandon through a composition that never launched
        this container. Every one of the three ways that can be wrong is a
        refusal here rather than a removal somewhere else.
        """
        recorded = allocation_of(self.pooled.store, attempt_id)
        if recorded is None:
            _refuse(f"attempt {attempt_id!r} has no recorded allocation, so "
                    f"this deployment cannot say which worker started it; an "
                    f"abandonment is declared through the composition that "
                    f"holds that attempt's port and adapter",
                    category="refused", code="precondition")
        owners = {one["worker_id"]: one["operations"] for one in self.workers}
        operations = owners.get(recorded["worker_id"])
        if operations is None:
            _refuse(f"attempt {attempt_id!r} is allocated to worker "
                    f"{recorded['worker_id']!r}, which this deployment does "
                    f"not compose", category="refused", code="precondition")
        abandon = getattr(operations, "abandon_attempt", None)
        if abandon is None:
            _refuse(f"worker {recorded['worker_id']!r} composes no "
                    f"abandonment capability", category="refused",
                    code="capability")
        return abandon(attempt_id=attempt_id, reason=reason, stage=stage)

    # -- the owned observation and the two stage driver operations -----------'''


def swap(place, body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times in {place.name}, "
            f"not once")
    return body.replace(old, new, 1)


def main():
    for place in (WORKER, STAGE):
        if not place.is_file():
            raise SystemExit(f"REFUSED: {place} is not a file to edit")

    body = WORKER.read_text(encoding="utf-8")
    if "def abandon_attempt(" in body:
        raise SystemExit("REFUSED: single_worker already carries it")
    body = swap(WORKER, body, WORKER_ANCHOR, WORKER_ADDED + WORKER_ANCHOR,
                "the ending anchor")
    body = swap(WORKER, body, WORKER_EXPOSE_ANCHOR, WORKER_EXPOSE,
                "the operations wrapper")
    WORKER.write_text(body, encoding="utf-8")
    compile(body, str(WORKER), "exec")

    body = STAGE.read_text(encoding="utf-8")
    if "def abandon_attempt(" in body:
        raise SystemExit("REFUSED: stage_execution already carries it")
    body = swap(STAGE, body, STAGE_ANCHOR, STAGE_ADDED, "the driver anchor")
    STAGE.write_text(body, encoding="utf-8")
    compile(body, str(STAGE), "exec")

    for place in (WORKER, STAGE):
        written = place.read_text(encoding="utf-8")
        if written.count("def abandon_attempt(") < 1:
            raise SystemExit(f"REFUSED: {place.name} does not carry it")
    print("the composed abandonment route is written in both owned files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
