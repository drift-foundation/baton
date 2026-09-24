"""The settlement gate for the two faulted attempts, through SUPPORTED readers.

Review 2026-09-24T01:25:43Z named the starting points: "Pinned
job_manager/ending.py exposes intent_of, settlement_of, ending_of keyed
stage/episode: supported readonly starting points, no raw SQL."

So this asks those, plus the attempt, intake and runtime readers, over the
preserved instance -- **read-only, through the public API, with no SQL**. It
performs no act, authorizes no cleanup, deletes nothing and starts nothing.

WHAT IT IS FOR: to establish the ACTUAL gate that stopped these two attempts
from settling, and to distinguish a missing RESULT from missing CLEANUP
AUTHORITY. My earlier diagnosis offered a resemblance to W236087 instead of a
read, and the reviewer was right that a resemblance is not a cause.
"""
import json
import os
import sys

SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"
RUN_ROOT = "/home/sl/baton-instances/two-jobs-251156"
JOBS = os.path.join(RUN_ROOT, "db", "jobs.sqlite3")
CONTROL = os.path.join(RUN_ROOT, "db", "control.sqlite3")
AUTHORITY_RECORD = os.path.join(RUN_ROOT, "bootstrap.json")
NOW = "1970-01-01T00:00:00.000Z"
RETENTION = None

if not os.path.isdir(os.path.join(SNAPSHOT, "baton_v12")):
    raise SystemExit(f"REFUSED: the pinned snapshot is not at {SNAPSHOT}")
for one in (SNAPSHOT,):
    while one in sys.path:                                   # pragma: no cover
        sys.path.remove(one)
    sys.path.insert(0, one)


def asked(what, thunk):
    """One read, with its refusal kept rather than turned into a gap."""
    try:
        return {"asked": what, "answer": thunk()}
    except BaseException as failure:                          # noqa: BLE001
        return {"asked": what,
                "refused": f"{type(failure).__name__}: {failure}"}


def main():
    from baton_v12.job_manager import JobStore, ending, episodes, submission
    from baton_v12.worker_manager import ControlStore, attempts, intake
    from baton_v12.worker_manager import output

    with open(AUTHORITY_RECORD, encoding="utf-8") as handle:
        authority_uuid = json.load(handle)["authority_uuid"]
    with open(os.path.join(RUN_ROOT, "run", "outcome.json"),
              encoding="utf-8") as handle:
        outcome = json.load(handle)
    # THE RETENTION POLICY THIS RUN DECIDED EVERY INTAKE UNDER, read from the
    # deployment it actually served rather than named here.
    global RETENTION
    with open(os.path.join(RUN_ROOT, "run", "deployment.json"),
              encoding="utf-8") as handle:
        RETENTION = json.load(handle)["retention_policy_digest"]

    held = {"schema": "baton.v12-two-job-settlement/1", "work": "W247941",
            "claim": 252647, "read_only": True, "run_root": RUN_ROOT,
            "authority_uuid": authority_uuid,
            "admitted_attempts": outcome["admitted_attempts"]}

    jobs = JobStore.open_readonly(JOBS, authority_uuid=authority_uuid,
                                  incarnation="settlement-read",
                                  clock=lambda: NOW)
    control = ControlStore.open_readonly(CONTROL,
                                         incarnation="settlement-read",
                                         clock=lambda: NOW)
    try:
        stages = []
        for stage in submission.stage_rows(jobs):
            one = {"stage_id": stage["stage_id"], "job_id": stage["job_id"],
                   "kind": stage["kind"], "state": stage.get("state")}
            one["episodes"] = asked(
                "the episodes this stage has been through",
                lambda held=stage: [
                    {"episode": row["episode"],
                     "attempt_id": row["attempt_id"],
                     "state": row.get("state")}
                    for row in episodes.episodes_of(jobs, held["stage_id"])])
            stages.append(one)
        held["stages"] = stages

        # THE ENDING, PER STAGE AND EPISODE -- the reviewer's own pointers.
        endings = []
        for one in stages:
            for episode in (one["episodes"].get("answer") or []):
                endings.append({
                    "stage_id": one["stage_id"], "job_id": one["job_id"],
                    "kind": one["kind"], "episode": episode["episode"],
                    "attempt_id": episode["attempt_id"],
                    "intent": asked(
                        "the registered composed-ending obligation",
                        lambda a=one, b=episode: ending.intent_of(
                            jobs, a["stage_id"], b["episode"])),
                    "settlement": asked(
                        "that obligation's paired settlement",
                        lambda a=one, b=episode: ending.settlement_of(
                            jobs, a["stage_id"], b["episode"])),
                    "both": asked(
                        "both halves in one read",
                        lambda a=one, b=episode: ending.ending_of(
                            jobs, a["stage_id"], b["episode"])),
                })
        held["endings"] = endings
        held["pending_endings"] = asked(
            "every ending this store still owes",
            lambda: list(ending.pending_endings(jobs)))

        # AND THE ATTEMPT SIDE: what the control store holds for each admitted
        # attempt. A MISSING RESULT and MISSING CLEANUP AUTHORITY are different
        # facts and this asks them separately.
        per_attempt = {}
        for attempt_id in outcome["admitted_attempts"]:
            per_attempt[attempt_id] = {
                "assignment": asked(
                    "the durable assignment fixed to this attempt",
                    lambda one=attempt_id: attempts.assignment_of(control,
                                                                  one)),
                "runtime": asked(
                    "the runtime axis this manager recorded",
                    lambda one=attempt_id: attempts.attempt_runtime_of(
                        control, one)),
                "start_failure": asked(
                    "a recorded start failure",
                    lambda one=attempt_id: attempts.attempt_start_failure_of(
                        control, one)),
                "preparation_failure": asked(
                    "a recorded preparation failure",
                    lambda one=attempt_id:
                        attempts.attempt_preparation_failure_of(control, one)),
                "intake_receipt": asked(
                    "the intake receipt for this attempt's output",
                    lambda one=attempt_id: intake.intake_receipt_of(control,
                                                                    one)),
                "gate_discharge": asked(
                    "the intake gate's discharge",
                    lambda one=attempt_id: intake.gate_discharge_of(control,
                                                                    one)),
                "abandoned_gate_discharge": asked(
                    "the ABANDONED gate discharge, which is the other door",
                    lambda one=attempt_id:
                        intake.abandoned_gate_discharge_of(control, one)),
                "cleanup": asked(
                    "a committed cleanup under this run's retention policy",
                    lambda one=attempt_id: intake.cleanup_of(
                        control, attempt_id=one,
                        retention_policy_digest=RETENTION)),
                "abandonment_cleanup": asked(
                    "a committed ABANDONMENT cleanup, the faulted-turn door",
                    lambda one=attempt_id: intake.abandonment_cleanup_of(
                        control, attempt_id=one,
                        retention_policy_digest=RETENTION)),
                "frozen_output": asked(
                    "the frozen result this attempt produced",
                    lambda one=attempt_id: output.frozen_output_of(control,
                                                                   one)),
            }
        held["attempts"] = per_attempt
    finally:
        control.close()
        jobs.close()

    print(json.dumps(held, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
