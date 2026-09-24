"""Claim-253589: the guards become RECOVERY, and the typed refusal is typed.

Review 2026-09-24T03:57:08Z, three findings, all correct:

  * **P1** the wrapper "requires removed launch material before exact core
    replay" -- refusing on an unadoptable delivery blocks the very case
    `intake.abandon_attempt` handles itself, which commits or REPLAYS its
    intent before any external call. A repeat after a partial abandonment has
    no launch material left, and my guard turned that replay into a refusal.
  * **P1** "every composed stage refuses so selected deployment cannot
    recover" -- the two-Job deployment always composes stages, so my blanket
    refusal made the capability useless for exactly the run it exists for. My
    objection to `_mounted` was mine, not the product's, and last round's
    finding already showed avoiding it bought nothing.
  * **P2** a malformed `stage` -- a string, a list, an int -- raised
    `AttributeError` out of my own refusal FORMATTING, because
    `(stage or {}).get(...)` calls `.get` on whatever was passed. Reproduced
    independently in 0.007237350975628942s. A refusal that crashes is not a
    refusal.

So: the type check answers first and formats without touching the operand; the
stage case RECOVERS through `_mounted`, which is what `ending` uses for an
attempt it did not start; a missing launch delivery is carried to the core when
an abandonment intent is already recorded, and refused only when it is not; and
the durable context is bound on `stage_id` and `episode` as well as the attempt.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
WORKER = CHECKOUT / "v12" / "python" / "tools" / "single_worker.py"
STAGE = CHECKOUT / "v12" / "python" / "tools" / "stage_execution.py"

OLD_DOC = '''        WHY THE ROOTS COME FROM `assignment_workspace` AND NOT `_mounted`.
        `_mounted` allocates the ordinary pair AND lets a stage composition
        answer a different one, and it refuses a historical mount -- both are
        right for a start and wrong for a removal, which must not allocate
        anything. This adopts the same pair `cancel_attempt` and `reconcile`
        do.
'''

NEW_DOC = '''        WHERE THE ROOTS COME FROM, and it depends on the composition. A
        composed stage may mount a private line as the writable root, so the
        ordinary pair is not that attempt's tree -- and `_mounted` is what
        `ending` itself uses to recover the roots of an attempt it did not
        start. A worker with no stage composition has only the ordinary pair,
        and for that one `adopted_assignment_workspace` proves it read-only
        rather than allocating it.

        I HAD THIS BACKWARDS TWICE. First I preferred `assignment_workspace`
        over `_mounted` on the grounds that a removal must allocate nothing --
        and `assignment_workspace` allocates too, so the choice bought nothing.
        Then I refused every composed stage, which made this useless for the
        only deployment that needs it. Review 2026-09-24T03:57:08Z named both.
'''

OLD_TYPE = '''        if type(stage) is not dict or stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r} and this one names "
                    f"{(stage or {}).get('attempt_id')!r}; the durable "
                    f"context is recovered from the attempt's own stage or "
                    f"this refuses before any effect",
                    category="refused", code="precondition")
'''

NEW_TYPE = '''        # THE TYPE ANSWERS FIRST, AND THE REFUSAL TOUCHES NOTHING. Review
        # 2026-09-24T03:57:08Z: `(stage or {}).get(...)` called `.get` on
        # whatever was passed, so a string, a list or an int raised
        # `AttributeError` out of the refusal's own formatting. A refusal that
        # crashes is not a refusal.
        if type(stage) is not dict:
            _refuse(f"an abandonment takes the attempt's own stage document; "
                    f"this is a {type(stage).__name__}",
                    category="refused", code="schema")
        if stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r} and this one names "
                    f"{stage.get('attempt_id')!r}; the durable context is "
                    f"recovered from the attempt's own stage or this refuses "
                    f"before any effect",
                    category="refused", code="precondition")
        # AND THE DURABLE BINDING IS `launch.adopt`'S, not a comparison
        # invented here. Review 2026-09-24T03:57:08Z asked for context bound
        # beyond attempt-id equality; the adoption below is that binding --
        # it holds the contract, the role, the transport, this attempt's
        # `_job_execution(stage)` and its provider context against the
        # delivery the container actually mounted, and refuses a disagreement.
        # A second comparison here over rows this composition does not own
        # would be a weaker door onto the same question.
'''

OLD_STAGE_REFUSAL = '''        # AND THE STAGE COMPOSITION'S ALTERNATE MOUNTS ARE REFUSED, NOT
        # GUESSED. A composed stage may answer a private line as the writable
        # root, and the ordinary pair below is then not this attempt's tree --
        # so a teardown over it would remove the wrong one. Until the stage
        # composition can answer its roots WITHOUT allocating them, this
        # refuses by name rather than choosing.
        if self.stage is not None:
            _refuse(f"attempt {attempt_id!r} is served by a stage composition "
                    f"that may mount roots other than the ordinary pair, and "
                    f"this abandonment can only prove the ordinary pair; a "
                    f"removal over roots it cannot prove are the attempt's is "
                    f"refused", category="refused", code="capability")
'''

NEW_STAGE_REFUSAL = ''

OLD_ROOTS = '''        roots = workspaces.adopted_assignment_workspace(
            self.given["workspace_storage"], attempt_id)'''

NEW_ROOTS = '''        if self.stage is not None:
            # THE STAGE'S OWN MOUNTS, recovered the way `ending` recovers them
            # for an attempt this process did not start. A private line is the
            # writable root for an implementation attempt, and a teardown over
            # the ordinary pair would remove the wrong tree.
            roots = self._mounted(stage, attempt_id, checkpoint=False)[0]
        else:
            roots = workspaces.adopted_assignment_workspace(
                self.given["workspace_storage"], attempt_id)'''

OLD_ADOPT = '''        launched = self._adopted(stage)
        if launched is None:
            _refuse(f"attempt {attempt_id!r} has no launch delivery this "
                    f"manager can adopt, so a removal here would report "
                    f"not-delivered and leave its root; the durable context "
                    f"is recovered or this refuses",
                    category="refused", code="precondition")'''

NEW_ADOPT = '''        launched = self._adopted(stage)
        if launched is None:
            # A MISSING DELIVERY IS EITHER A REPLAY OR A REFUSAL, and the
            # journal says which. Review 2026-09-24T03:57:08Z: refusing
            # unconditionally blocked the exact replay the core performs --
            # `intake.abandon_attempt` commits or REPLAYS its intent before any
            # external call, and a repeat after a partial abandonment has no
            # launch material left to adopt. So a recorded abandonment carries
            # through to the core, and only an unrecorded one refuses.
            if intake.abandoned_gate_discharge_of(self.control,
                                                  attempt_id) is None:
                _refuse(f"attempt {attempt_id!r} has no launch delivery this "
                        f"manager can adopt and no recorded abandonment to "
                        f"replay, so a removal here would report "
                        f"not-delivered and leave its root",
                        category="refused", code="precondition")'''

OLD_IMPORT = """from baton_v12.worker_manager import (ControlStore, attempts, boundaries,
                                      credentials, exchange, launch,
                                      source_boundary, workspaces)"""

NEW_IMPORT = """from baton_v12.worker_manager import (ControlStore, attempts, boundaries,
                                      credentials, exchange, intake, launch,
                                      source_boundary, workspaces)"""

OLD_ROUTE_TAIL = '''        if type(stage) is not dict or stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r}; this one names "
                    f"{(stage or {}).get('attempt_id')!r}",
                    category="refused", code="precondition")'''

NEW_ROUTE_TAIL = '''        if type(stage) is not dict:
            _refuse(f"an abandonment takes the attempt's own stage document; "
                    f"this is a {type(stage).__name__}",
                    category="refused", code="schema")
        if stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r}; this one names "
                    f"{stage.get('attempt_id')!r}",
                    category="refused", code="precondition")'''


def swap(place, body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times in "
            f"{place.name}, not once")
    return body.replace(old, new, 1)


def main():
    body = WORKER.read_text(encoding="utf-8")
    if "no recorded abandonment to" in body:
        raise SystemExit("REFUSED: the recovery correction is already applied")
    body = swap(WORKER, body, OLD_DOC, NEW_DOC, "the roots docstring")
    body = swap(WORKER, body, OLD_TYPE, NEW_TYPE, "the type check")
    body = swap(WORKER, body, OLD_STAGE_REFUSAL, NEW_STAGE_REFUSAL,
                "the blanket stage refusal")
    body = swap(WORKER, body, OLD_ROOTS, NEW_ROOTS, "the roots recovery")
    body = swap(WORKER, body, OLD_ADOPT, NEW_ADOPT, "the adoption guard")
    # THE IMPORT I OMITTED. `intake.abandon_attempt` was an UNDEFINED NAME in
    # what I handed over last claim: `intake` is not among single_worker's
    # imports, and the 162-case suite passed because nothing calls the new
    # method. A capability whose only call would raise NameError is not
    # written, and I found this myself before it reached a reviewer.
    body = swap(WORKER, body, OLD_IMPORT, NEW_IMPORT, "the intake import")
    WORKER.write_text(body, encoding="utf-8")
    compile(body, str(WORKER), "exec")

    body = STAGE.read_text(encoding="utf-8")
    body = swap(STAGE, body, OLD_ROUTE_TAIL, NEW_ROUTE_TAIL, "the router check")
    STAGE.write_text(body, encoding="utf-8")
    compile(body, str(STAGE), "exec")

    for place in (WORKER, STAGE):
        written = place.read_text(encoding="utf-8")
        if "(stage or {}).get" in written:
            raise SystemExit(f"REFUSED: the crashing format survives in "
                             f"{place.name}")
    print("recovery and typed refusals applied to both owned files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
