"""Claim-253661: rebuild single_worker.py from the pinned bytes, then re-add.

I BROKE THE FILE. An edit under this claim sliced from a marker to the SECOND
occurrence of `delivery, orphan = self._credential(` -- `str.index` found a
later one -- and deleted the region between, splicing my method's tail into
another method's body. `IndentationError` at line 2477.

Rather than patch the wreckage, this rebuilds: the PINNED SNAPSHOT's copy of
`tools/single_worker.py` is the unmodified product, so the file is restored from
it and this claim's additions are re-applied in their final reviewed form. That
loses nothing and leaves a file whose whole diff against the pinned bytes is
exactly the capability.

THE PINNED SNAPSHOT IS READ, NEVER WRITTEN.
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
WORKER = CHECKOUT / "v12" / "python" / "tools" / "single_worker.py"
PINNED = pathlib.Path("/home/sl/baton-runs/independent-review-247947"
                      "/manager-source/tools/single_worker.py")

OLD_IMPORT = """from baton_v12.worker_manager import (ControlStore, attempts, boundaries,
                                      credentials, exchange, launch,
                                      source_boundary, workspaces)"""

NEW_IMPORT = """from baton_v12.worker_manager import (ControlStore, attempts, boundaries,
                                      credentials, exchange, intake, launch,
                                      source_boundary, workspaces)"""

ANCHOR = '''    def ending(self, stage, job):
        """Drive ONE answered attempt through the already-ruled ending.'''

CAPABILITY = '''    def abandon_attempt(self, *, attempt_id, reason, stage):
        """W247941: the manager's FOURTH ending, reachable by its owner.

        THE COMPOSITION OWNS THIS AND AN ORCHESTRATOR CANNOT.
        `intake.abandon_attempt` needs the Authority port, a per-attempt
        adapter carrying the deliveries the START created, and the custody
        capability -- all three this composition's. A supervisor that rebuilt
        them from this module's private state would be a second controller over
        one security boundary, which is the rule `cancel_attempt` records.

        AND IT IS A DECLARATION, NOT AN OBSERVATION. `reason` is the caller's
        own account of why the attempt is over; nothing here reads a clock,
        counts a retry or measures silence. Calling the operation IS the
        declaration, so a caller that has not decided must not call this.

        REPLAY IS THE CORE'S. `intake.abandon_attempt` commits or replays its
        own intent before any external call and owns every eligibility check.
        This composes operands and nothing else -- it does not read a discharge
        or a cleanup to decide what to do, and it never synthesises an
        operation result.
        """
        boundaries.identity(attempt_id, "a runtime attempt id")
        reason = boundaries.text(reason, "an abandonment reason")
        # THE TYPE ANSWERS FIRST, AND THE REFUSAL TOUCHES NOTHING. A refusal
        # that formats with `(stage or {}).get(...)` raises `AttributeError`
        # on a string, a list or an int -- a refusal that crashes is not one.
        if type(stage) is not dict:
            # `integrity`/`schema` is the closed pair for a malformed
            # document; `refused`/`schema` is not one, and this build asserts
            # on an unclosed pairing rather than raising the refusal.
            _refuse(f"an abandonment takes the attempt's own stage document; "
                    f"this is a {type(stage).__name__}",
                    category="integrity", code="schema")
        if stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r} and this one names "
                    f"{stage.get('attempt_id')!r}; the durable context is "
                    f"recovered from the attempt's own stage or this refuses "
                    f"before any effect",
                    category="refused", code="precondition")
        state = attempt_runtime_of(self.control, attempt_id)
        if state["runtime_id"] is None:
            _refuse(f"attempt {attempt_id!r} has no attached runtime; "
                    f"abandonment ends an attempt whose runtime STARTED and "
                    f"whose worker then never answered, and there is nothing "
                    f"here to end", category="refused", code="precondition")
        # ADOPTION DECIDES WHICH ROOT RECOVERY IS EVEN LEGAL, so it happens
        # first. `launch.adopt` answers None ONLY when the launch root does not
        # exist -- every other condition refuses -- so None means there is no
        # launch material, and a stage composition has nothing to answer about.
        launched = self._adopted(stage)
        if launched is not None and self.stage is not None:
            # THE STAGE'S OWN MOUNTS, recovered the way `ending` recovers them
            # for an attempt this process did not start: a private line is the
            # writable root for an implementation attempt, and a teardown over
            # the ordinary pair would remove the wrong tree.
            roots = self._mounted(stage, attempt_id, checkpoint=False)[0]
        else:
            # PROVED, NEVER ALLOCATED. Allocating a root in order to remove it
            # would be this call creating what it came to destroy, and a
            # refusal here is the core's own precondition failing early rather
            # than a state this call may work around.
            roots = workspaces.adopted_assignment_workspace(
                self.given["workspace_storage"], attempt_id)
        # A RETRY AFTER AN INTERRUPTED SETTLEMENT FINDS THE RUNTIME GONE, and
        # `_credential`'s live recovery cannot serve it: `recover_credentials`
        # adopts exactly ONE identified container and refuses every other
        # count, so a removal that journalled nothing left a retry that this
        # composition refused before the core was ever entered -- the one the
        # core explicitly supports, because "force-removal of an already
        # absent exact identity answers absent".
        #
        # SO THE ENGINE IS ASKED, AND ONLY A POSITIVE ABSENCE BRANCHES.
        # `observe` answers `absent` only when the engine says THIS EXACT
        # identity does not exist; anything it cannot read is `uncertain`, and
        # uncertainty takes the ordinary path. Nothing here catches a refusal
        # to decide this -- that was the fabrication this Work removed.
        #
        # AND THE ORPHAN IS `_credential`'S OWN ANSWER for a delivery this
        # process cannot hold, not a substitute invented here: the credential
        # lifecycle is then settled by cleanup discarding the orphaned root,
        # which is what the recovery refusal itself describes.
        if self._adapter(roots, None, None, launched).observe(
                state["runtime_id"])["state"] == "absent":
            delivery = None
            orphan = (credentials.OrphanTeardown(
                attempt_id, homes=[self.credential_home])
                if self.given["credential_resolution"] else None)
        else:
            delivery, orphan = self._credential(attempt_id, state, roots,
                                                launched)
        adapter = self._adapter(roots, delivery, orphan, launched)
        answered = intake.abandon_attempt(
            self.control, self.port, adapter, attempt_id=attempt_id,
            reason=reason,
            retention_policy_digest=self.given["retention_policy_digest"])
        # AND THE GATE THIS ACT INSTALLED IS CARRIED, because nothing else
        # will. The fence and the authority's `runtime-quiescence:<generation>`
        # commit in one transaction, and an abandonment has no ordinary ending
        # anywhere in its future to discharge it -- so an operator declaration
        # would leave the Work gated forever. A REFUSAL HERE PROPAGATES: the
        # cleanup is committed and durable, and a retry replays it and then
        # discharges, which is better than an answer that hides an obligation
        # nobody holds a receipt for.
        self._discharged_abandonment(attempt_id, answered)
        return answered

    def _discharged_abandonment(self, attempt_id, answered):
        """W247941: the abandoned gate's discharge, on the accepted shape.

        `StageExecution._discharged` is the pattern and this is deliberately
        the same three steps in the same order: REPLAY a committed discharge
        before anything mutable is read, decide owedness from what THIS act
        FENCED rather than from today's projection -- a lost receipt leaves
        the gate already cleared, so the projection would say nothing is owed
        -- and only then perform the act.

        AND THE COMMITTED CLEANUP IS THE PRECONDITION, read from the durable
        record rather than inferred from the answer in hand. An interrupted
        settlement journals nothing, and this gate "is discharged on the
        abandonment this manager committed and never on the absence of one";
        asking the reader is how this composition knows which it is holding.
        """
        held = intake.abandoned_gate_discharge_of(self.control, attempt_id)
        if held is not None:
            return held
        if not (answered.get("fenced") or {}).get("gate"):
            return None
        digest = self.given["retention_policy_digest"]
        if intake.abandonment_cleanup_of(
                self.control, attempt_id=attempt_id,
                retention_policy_digest=digest) is None:
            return None
        return intake.discharge_abandoned_quiescence_gate(
            self.control, self.port, attempt_id=attempt_id,
            retention_policy_digest=digest)

'''

WRAP_ANCHOR = '''    def cancel_attempt(self, *, attempt_id, reason):
        """W236087: the composed worker's own stop, reachable by its owner."""
        return self._worker.cancel_attempt(attempt_id=attempt_id,
                                           reason=reason)
'''

WRAP = WRAP_ANCHOR + '''
    def abandon_attempt(self, *, attempt_id, reason, stage):
        """W247941: the composed worker's own FOURTH ending, likewise."""
        return self._worker.abandon_attempt(attempt_id=attempt_id,
                                            reason=reason, stage=stage)
'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    if not PINNED.is_file():
        raise SystemExit(f"REFUSED: the pinned copy is not at {PINNED}")
    pristine = PINNED.read_text(encoding="utf-8")
    if "def abandon_attempt(" in pristine:
        raise SystemExit("REFUSED: the pinned copy already carries the "
                         "capability, so it is not the unmodified product")
    shutil.copyfile(PINNED, WORKER)

    body = WORKER.read_text(encoding="utf-8")
    body = swap(body, OLD_IMPORT, NEW_IMPORT, "the import block")
    body = swap(body, ANCHOR, CAPABILITY + ANCHOR, "the ending anchor")
    body = swap(body, WRAP_ANCHOR, WRAP, "the operations wrapper")
    WORKER.write_text(body, encoding="utf-8")
    compile(body, str(WORKER), "exec")

    written = WORKER.read_text(encoding="utf-8")
    if written.count("def abandon_attempt(") != 2:
        raise SystemExit("REFUSED: the capability and its wrapper are not both "
                         "present exactly once")
    for absent in ("fenced\": {\"fenced\": True", "except ContractRefusal:\n"
                   "                settled = intake.abandonment_cleanup_of"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives")
    over = [number for number, line in enumerate(written.splitlines(), 1)
            if len(line) > 79]
    print(f"rebuilt from the pinned bytes; {len(over)} line(s) over 79 "
          f"columns, all predating this claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
