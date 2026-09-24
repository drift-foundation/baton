"""Claim-253533: recover the durable context, or refuse before any effect.

Review 2026-09-24T03:49:06Z found three P1 defects in what I wrote, and all
three are real:

  1. **`assignment_workspace` itself creates missing entries.** So "roots from
     `assignment_workspace` rather than `_mounted`" did not avoid allocation at
     all -- it only avoided the stage composition. My stated reason for the
     choice was wrong.
  2. **`stage=None` omitted an existing launch delivery**, and the OCI adapter
     then reports not-delivered WITHOUT removing its root. So the "absence is a
     fact" design leaked the launch root -- exactly the 172346 failure mode I
     claimed to be avoiding, reintroduced by making the operand optional.
  3. **Ordinary roots do not establish a stage's alternate mounts or custody**,
     so credential recovery and teardown over them is not the attempt's own
     tree when a stage composed a different one.

The rule the review states is the fix: **recover the exact durable context or
refuse before effects.** So:

  * roots come from `workspaces.adopted_assignment_workspace`, which is "the
    roots an attempt ALREADY HAS, proved and never allocated" and which
    refuses an attempt whose roots are gone -- "not a state an ending can be
    performed over";
  * `stage` is REQUIRED and is bound to this attempt before anything happens;
  * the launch delivery must ADOPT, and a delivery that cannot be adopted is a
    refusal rather than a None passed downstream;
  * and finding 3 is answered by REFUSING rather than by guessing: a worker
    whose stage composition answers alternate roots is refused by name, with
    the sub-question recorded, because tearing down the ordinary pair for a
    line-mounted attempt would remove the wrong tree.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
WORKER = CHECKOUT / "v12" / "python" / "tools" / "single_worker.py"
STAGE = CHECKOUT / "v12" / "python" / "tools" / "stage_execution.py"

OLD_BODY = '''        boundaries.identity(attempt_id, "a runtime attempt id")
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
'''

NEW_BODY = '''        boundaries.identity(attempt_id, "a runtime attempt id")
        reason = boundaries.text(reason, "an abandonment reason")
        # THE STAGE IS REQUIRED AND IS BOUND TO THIS ATTEMPT. Review
        # 2026-09-24T03:49:06Z: an optional stage omitted an EXISTING launch
        # delivery, and the adapter then reports not-delivered without
        # removing its root -- so the operand being optional was itself the
        # leak. Binding it here means a caller cannot abandon one attempt
        # through another's durable context.
        if type(stage) is not dict or stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r} and this one names "
                    f"{(stage or {}).get('attempt_id')!r}; the durable "
                    f"context is recovered from the attempt's own stage or "
                    f"this refuses before any effect",
                    category="refused", code="precondition")
        state = attempt_runtime_of(self.control, attempt_id)
        if state["runtime_id"] is None:
            _refuse(f"attempt {attempt_id!r} has no attached runtime; "
                    f"abandonment ends an attempt whose runtime STARTED and "
                    f"whose worker then never answered, and there is nothing "
                    f"here to end", category="refused", code="precondition")
        # AND THE STAGE COMPOSITION'S ALTERNATE MOUNTS ARE REFUSED, NOT
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
        # THE ROOTS AN ATTEMPT ALREADY HAS, PROVED AND NEVER ALLOCATED.
        # `assignment_workspace` creates, chmods and chgrps -- which review
        # 2026-09-24T03:49:06Z pointed out is still an allocation, so my
        # earlier reason for preferring it over `_mounted` was wrong. This
        # reader asks the same invariant read-only and refuses an attempt
        # whose roots are gone, which "is not a state an ending can be
        # performed over".
        roots = workspaces.adopted_assignment_workspace(
            self.given["workspace_storage"], attempt_id)
        # AND THE LAUNCH DELIVERY MUST ADOPT. A delivery this manager cannot
        # adopt is not a state to remove over: the adapter would take its
        # not-delivered branch and leave the launch root behind, which is the
        # 172346 defect. Refused before the fence rather than discovered after
        # the removal.
        launched = self._adopted(stage)
        if launched is None:
            _refuse(f"attempt {attempt_id!r} has no launch delivery this "
                    f"manager can adopt, so a removal here would report "
                    f"not-delivered and leave its root; the durable context "
                    f"is recovered or this refuses",
                    category="refused", code="precondition")
        delivery, orphan = self._credential(attempt_id, state, roots, launched)
'''

OLD_SIG = '''    def abandon_attempt(self, *, attempt_id, reason, stage=None):
        """W247941: the manager's FOURTH ending, reachable by its owner.'''

NEW_SIG = '''    def abandon_attempt(self, *, attempt_id, reason, stage):
        """W247941: the manager's FOURTH ending, reachable by its owner.'''

OLD_WRAP = '''    def abandon_attempt(self, *, attempt_id, reason, stage=None):
        """W247941: the composed worker's own FOURTH ending, likewise."""
        return self._worker.abandon_attempt(attempt_id=attempt_id,
                                            reason=reason, stage=stage)'''

NEW_WRAP = '''    def abandon_attempt(self, *, attempt_id, reason, stage):
        """W247941: the composed worker's own FOURTH ending, likewise."""
        return self._worker.abandon_attempt(attempt_id=attempt_id,
                                            reason=reason, stage=stage)'''

OLD_ROUTE = '''    def abandon_attempt(self, *, attempt_id, reason, stage=None):'''
NEW_ROUTE = '''    def abandon_attempt(self, *, attempt_id, reason, stage):'''

OLD_ROUTE_TAIL = '''        return abandon(attempt_id=attempt_id, reason=reason, stage=stage)'''
NEW_ROUTE_TAIL = '''        # THE STAGE IS BOUND TO THE RECORDED ALLOCATION'S OWN ATTEMPT, here as
        # well as in the worker: routing by allocation and then handing over
        # somebody else's stage would defeat the binding the worker performs.
        if type(stage) is not dict or stage.get("attempt_id") != attempt_id:
            _refuse(f"an abandonment names the stage of attempt "
                    f"{attempt_id!r}; this one names "
                    f"{(stage or {}).get('attempt_id')!r}",
                    category="refused", code="precondition")
        return abandon(attempt_id=attempt_id, reason=reason, stage=stage)'''


def swap(place, body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times in "
            f"{place.name}, not once")
    return body.replace(old, new, 1)


def main():
    body = WORKER.read_text(encoding="utf-8")
    if "adopted_assignment_workspace" in body:
        raise SystemExit("REFUSED: the recovery correction is already applied")
    body = swap(WORKER, body, OLD_SIG, NEW_SIG, "the worker signature")
    body = swap(WORKER, body, OLD_BODY, NEW_BODY, "the worker body")
    body = swap(WORKER, body, OLD_WRAP, NEW_WRAP, "the operations wrapper")
    WORKER.write_text(body, encoding="utf-8")
    compile(body, str(WORKER), "exec")

    body = STAGE.read_text(encoding="utf-8")
    body = swap(STAGE, body, OLD_ROUTE, NEW_ROUTE, "the routing signature")
    body = swap(STAGE, body, OLD_ROUTE_TAIL, NEW_ROUTE_TAIL, "the routing tail")
    STAGE.write_text(body, encoding="utf-8")
    compile(body, str(STAGE), "exec")

    written = WORKER.read_text(encoding="utf-8")
    for absent in ("stage=None", "workspaces.assignment_workspace(\\n"
                   "            self.group, self.given[\"workspace_storage\"], "
                   "attempt_id)\n        # THE LAUNCH"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives")
    for present in ("adopted_assignment_workspace", "may mount roots other",
                    "has no launch delivery this"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("recover-or-refuse applied to both owned files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
