"""Claim-253632: adoption decides first, and `adopt`'s own None is the contract.

Review 2026-09-24T04:02:45Z, two P1 findings, both right:

  * **`_mounted` ran before the replay determination**, so allocation and the
    historical-mount refusal happened before anything had decided whether this
    was a first call or a repeat.
  * **`abandoned_gate_discharge_of` reads a separate committed gate discharge,
    not the abandonment intent or cleanup** — so "a crash after removal or
    cleanup before discharge still has no record there", and my replay gate
    was reading the wrong fact.

THE CONTRACT I SHOULD HAVE USED IS `launch.adopt`'S OWN. Reading it:

    root = os.path.join(os.path.realpath(home), attempt)
    if not os.path.lexists(root):
        return None

`None` means the launch root **does not exist** — every other condition
refuses. So `launched is None` is not ambiguous at all: there is no launch
material on disk, so `not-delivered` is the CORRECT adapter branch rather than
the leak I worried about two claims ago. No discharge read, no cleanup read and
no intent reader is needed to know that.

So adoption happens FIRST and decides which root recovery is even legal, and
`_mounted` is reached only when there IS launch material — which is exactly the
case it was written for.

One residual limit is reported rather than papered over: when the launch root
is gone AND the workspace roots are gone, `adopted_assignment_workspace` refuses
(correctly — it will not allocate), so a repeat after a completed removal cannot
compose an adapter. Rather than refuse an attempt that is already finished, that
case READS the outcome — a committed abandonment cleanup under this deployment's
own retention policy digest — and answers it. That is reading a result, not
using cleanup presence as a replay contract.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
WORKER = CHECKOUT / "v12" / "python" / "tools" / "single_worker.py"

OLD = '''        if self.stage is not None:
            # THE STAGE'S OWN MOUNTS, recovered the way `ending` recovers them
            # for an attempt this process did not start. A private line is the
            # writable root for an implementation attempt, and a teardown over
            # the ordinary pair would remove the wrong tree.
            roots = self._mounted(stage, attempt_id, checkpoint=False)[0]
        else:
            roots = workspaces.adopted_assignment_workspace(
                self.given["workspace_storage"], attempt_id)
'''

NEW = '''        # ADOPTION DECIDES FIRST, because it decides which root recovery is
        # even legal. Review 2026-09-24T04:02:45Z: `_mounted` ran before this
        # and so reintroduced allocation and the historical-mount refusal
        # before anything had established whether there was launch material at
        # all.
        #
        # AND `adopt`'S OWN None IS THE CONTRACT. It answers None only when
        # `os.path.lexists(root)` is false -- every other condition refuses --
        # so None means there is no launch root on disk, and the adapter's
        # not-delivered branch is then correct rather than a leak. My previous
        # gate read `abandoned_gate_discharge_of`, which is a SEPARATE
        # committed discharge and says nothing about this.
        launched = self._adopted(stage)
        if launched is not None and self.stage is not None:
            # THE STAGE'S OWN MOUNTS, recovered the way `ending` recovers them
            # for an attempt this process did not start. A private line is the
            # writable root for an implementation attempt, and a teardown over
            # the ordinary pair would remove the wrong tree.
            roots = self._mounted(stage, attempt_id, checkpoint=False)[0]
        else:
            # PROVED, NEVER ALLOCATED. With no launch material there is nothing
            # for a stage composition to answer about, and allocating a root in
            # order to remove it would be this call creating what it came to
            # destroy.
            try:
                roots = workspaces.adopted_assignment_workspace(
                    self.given["workspace_storage"], attempt_id)
            except ContractRefusal:
                # THE ROOTS ARE GONE TOO. If this attempt already has a
                # committed abandonment cleanup under THIS deployment's own
                # retention policy, the removal is finished and the honest
                # answer is that record rather than a refusal. This reads an
                # OUTCOME; it is not a replay contract, and it is qualified by
                # the policy digest rather than by cleanup existing at all.
                settled = intake.abandonment_cleanup_of(
                    self.control, attempt_id=attempt_id,
                    retention_policy_digest=self.given[
                        "retention_policy_digest"])
                if settled is None:
                    raise
                return {"fenced": {"fenced": True, "replayed": True},
                        "cleanup": settled}
'''

OLD_LATER = '''        launched = self._adopted(stage)
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
                        category="refused", code="precondition")
'''

NEW_LATER = ''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = WORKER.read_text(encoding="utf-8")
    if "ADOPTION DECIDES FIRST" in body:
        raise SystemExit("REFUSED: the ordering correction is already applied")
    body = swap(body, OLD, NEW, "the roots recovery")
    body = swap(body, OLD_LATER, NEW_LATER, "the old replay gate")
    WORKER.write_text(body, encoding="utf-8")
    compile(body, str(WORKER), "exec")

    written = WORKER.read_text(encoding="utf-8")
    if "abandoned_gate_discharge_of(self.control" in written:
        raise SystemExit("REFUSED: the wrong replay read survives as a call")
    for present in ("ADOPTION DECIDES FIRST", "abandonment_cleanup_of(",
                    "launched is not None and self.stage is not None"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    print("adoption decides first; adopt's own None is the contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
