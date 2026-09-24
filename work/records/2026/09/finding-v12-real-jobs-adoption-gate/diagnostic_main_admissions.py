"""The retained `main` admission reproducer. RUNNABLE, and outside the suite.

Review 2026-09-23T18:38:26Z asked for this to be kept as a durable diagnostic
rather than deleted when it does not pass; review 2026-09-23T18:43:15Z found
that what I kept did not even PARSE -- a method body pasted at module scope
under a hyphenated filename nothing can import. This is the runnable one.

    mkdir -p /var/tmp/baton-w247941
    cd <checkout>/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w247941 \\
    PYTHONPATH="src:.:<dossier>" python3 -B -m diagnostic_main_admissions

It prints ONE receipt: the admissions `main` reached, the stage states it
ended with, every deferral the manager recorded, and the outcome's own
`held_because`. It asserts nothing -- it measures, so the next claim starts
from an observation rather than a guess.

WHAT IT HAS MEASURED SO FAR, in the order each cause was found and fixed:

  * `{"implementation": 0, "review": 0}` -- the submission carried a MANIFEST
    DIGEST where `job_input_identity` belongs, so no configured worker could
    serve any stage. Fixed in `two_jobs.submission`.
  * `{"implementation": 2, "review": 0}` -- each Job's two workers carried
    DIFFERENT manifests, and `input_digest` is a JOB fact. Fixed in
    `two_jobs.worker_document`: one manifest per Job, both roles.
  * `{"implementation": 2, "review": 0}` still. The review stage is gated on
    its implementation COMPLETING, and through `main` it does not within the
    bound, while the identical turn through `supervise` completes all four.
    CAUSE NOT ESTABLISHED.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
# PRODUCTION RESOLVES TO THE SELECTED SNAPSHOT. Review 2026-09-23T19:04:38Z:
# what I pinned last claim was cwd independence, and the requirement is
# PROVENANCE -- `baton_v12` and `tools` must be the bytes ASSESSMENT-249338.md
# selected, not the checkout's. Cwd independence is a consequence here, not
# the point.
#
# The snapshot holds `baton_v12` and `tools` and nothing else, so the fixture
# package `tests` must come from the checkout. That is the ONLY thing the
# checkout supplies, and it sits AFTER the snapshot on the path so it can
# never win a production name.
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"
CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(HERE)))))
DISTRIBUTION = os.path.join(CHECKOUT, "v12", "python")
if not os.path.isdir(os.path.join(SNAPSHOT, "baton_v12")):
    raise SystemExit(
        f"REFUSED: the selected manager snapshot is not at {SNAPSHOT}; "
        f"a diagnostic that silently falls back to the checkout measures "
        f"different bytes than the ones this gate pinned")
for one in (DISTRIBUTION, HERE, SNAPSHOT):
    while one in sys.path:                                   # pragma: no cover
        sys.path.remove(one)
    sys.path.insert(0, one)


def provenance():
    """Where each module this run depends on ACTUALLY came from.

    Printed with the receipt, because "it imported" and "it imported the
    selected bytes" are different claims and only one of them is the
    requirement.
    """
    import hashlib
    held = {}
    for name in sorted(sys.modules):
        if name.split(".")[0] not in ("baton_v12", "tools", "tests"):
            continue
        place = getattr(sys.modules[name], "__file__", None)
        if not place:
            continue
        under = ("snapshot" if os.path.realpath(place).startswith(
                     os.path.realpath(SNAPSHOT) + os.sep)
                 else "checkout" if os.path.realpath(place).startswith(
                     os.path.realpath(CHECKOUT) + os.sep)
                 else "elsewhere")
        with open(place, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        held[name] = {"file": place, "from": under, "sha256": digest}
    misplaced = sorted(name for name, one in held.items()
                       if name.split(".")[0] in ("baton_v12", "tools")
                       and one["from"] != "snapshot")
    return {"modules": held, "production_not_from_snapshot": misplaced}

from test_two_jobs import TheSHIPPEDTemplateComposesThroughTheACTUALCLI


class MainAdmissions(TheSHIPPEDTemplateComposesThroughTheACTUALCLI):
    """One measured run of the documented command. NOTHING is asserted."""

    def runTest(self):                                       # noqa: N802
        import two_job_supervisor
        from baton_v12.job_manager import status as projected
        from tests.job_manager import fixtures

        # THE TRACEBACK, CAPTURED BEFORE `_guarded` CONVERTS IT. Review
        # 2026-09-23T18:50:20Z: the guard turns a failed turn into one line of
        # uncertainty, which is right for a run and useless for a diagnosis.
        # This wraps the callback so the frames are printed and retained.
        import traceback
        held_frames = []
        inner = self.answering()

        def answering_with_frames(gate, context):
            try:
                return inner(gate, context)
            except BaseException:                            # noqa: BLE001
                held_frames.append(traceback.format_exc())
                raise

        # THE SUPPORTED STATUS READ, TAKEN WHILE THE COMPOSITION IS OPEN.
        # Every earlier receipt called `status(store, None)` after `main` had
        # closed everything and printed the AttributeError that produces.
        captured = []

        def answering_and_reading(gate, context):
            try:
                return answering_with_frames(gate, context)
            finally:
                try:
                    held_status = projected(context["job"],
                                            context["operations"],
                                            observed_at=fixtures.NOW)
                except Exception as failure:                 # noqa: BLE001
                    captured.append(f"{type(failure).__name__}: {failure}")
                else:
                    captured.append({
                        "canonical": held_status["canonical"],
                        "jobs": {one["job_id"]: {two["kind"]: two["state"]
                                                 for two in one["stages"]}
                                 for one in held_status["jobs"]}})

        self.answering = lambda: answering_and_reading
        argv, outcome, into = self.entrypoint(total=600, cleanup=60)
        moments = iter(range(0, 10_000, 5))
        two_job_supervisor.main(
            argv, turns=self.answering(),
            monotonic=lambda: float(next(moments)),
            sleep=lambda _seconds: None, **self.disposable(into))
        with open(outcome, encoding="utf-8") as handle:
            published = json.load(handle)

        # THE LAST LIVE READ is the stage picture this receipt reports. A read
        # taken after `main` returns has no composition to ask, and an
        # unsupported operand is not a measurement.
        states = captured[-1] if captured else "no tick took a status read"

        # THE COMPARISON REVIEW 2026-09-23T18:54:02Z ASKED FOR. `adopt`
        # answers None when `join(realpath(launch_home), attempt_id)` is
        # MISSING -- a content or identity mismatch REFUSES instead. So the
        # question is whether the delivery directory exists at the home the
        # fixture's `turn` passes, and whether that home is the one the
        # composed deployment actually wrote under.
        with open(os.path.join(into, "deployment.json"),
                  encoding="utf-8") as handle:
            composed_home = json.load(handle)["workers"][0]["deployment"][
                "launch_home"]
        fixture_home = self.config["launch_home"]
        homes = {
            "composed_launch_home": composed_home,
            "fixture_launch_home": fixture_home,
            "same_realpath": os.path.realpath(composed_home)
                             == os.path.realpath(fixture_home),
            "attempt_directories": {},
        }
        for attempt_id in published.get("admitted_attempts", ()):
            place = os.path.join(os.path.realpath(composed_home), attempt_id)
            homes["attempt_directories"][attempt_id] = {
                "path": place,
                "exists": os.path.isdir(place),
                "entries": sorted(os.listdir(place))[:8]
                           if os.path.isdir(place) else None,
            }

        print(json.dumps({
            "provenance": provenance(),
            "launch_homes": homes,
            "admissions": published["admissions"],
            "verdicts": sorted(published.get("verdicts") or {}),
            "stopped": published["stopped"],
            "state": published["state"],
            "held_because": published["held_because"],
            "uncertainty": published.get("uncertainty"),
            "live_status_reads": len(captured),
            "live_status_first": captured[0] if captured else None,
            "stage_states": states,
            "first_turn_traceback": (held_frames[0].splitlines()
                                     if held_frames else None),
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(MainAdmissions())
