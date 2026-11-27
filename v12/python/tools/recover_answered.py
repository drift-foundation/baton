"""Select a particular completed implementation for host recovery by its manager."""
from contextlib import ExitStack
import argparse
import json
import sys
from pathlib import Path

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, ending, submission
from baton_v12.worker_manager import ControlStore, answered_recovery
from tools import instance, runtime_upgrade, stack, stopped_settlement
from tools.manual_job import _owner_actor


def main(argv, *, clock=None, stream=None):
    from tools.job_manager import _utc_clock
    parser = argparse.ArgumentParser(prog="manager recover-answered", description=__doc__)
    for name in ("instance", "job", "attempt", "manifest", "head"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--episode", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        result = recover(args, clock=clock or _utc_clock())
    except (ContractRefusal, runtime_upgrade.UpgradeRefusal, instance.InstanceRefusal, stack.StackRefusal) as error:
        print("Recovery held: " + str(error), file=stream or sys.stderr)
        return 1
    print(json.dumps(result), file=stream or sys.stdout)
    return 0


def recover(args, *, clock):
    selected = instance.read(args.instance)
    options = dict(incarnation="answered-recovery", clock=clock)
    with stack.admission(Path(selected["state"])), ExitStack() as opened:
        runtime_upgrade._stopped(Path(selected["state"]))
        instance.verify(selected)
        actor = _owner_actor(selected, args.instance)
        configuration = stopped_settlement._document(selected["deployment"])
        places = instance.layout(selected["destination"])
        if (configuration.get("authority_uuid") != selected["authority_uuid"]
                or Path(configuration["authority_store"]).resolve() != Path(places["authority_store"]).resolve()):
            answered_recovery.refuse("deployment and instance Authority disagree")
        jobs = opened.enter_context(JobStore.open(selected["job_store"], authority_uuid=selected["authority_uuid"], **options))
        control = opened.enter_context(ControlStore.open(selected["control_store"], **options))
        receipt = answered_recovery.request_for(jobs, control, attempt=args.attempt, job=args.job, episode=args.episode,
            manifest=args.manifest, head=args.head, actor=actor)
        stage_id = args.job + "/implementation"
        settled = ending.settlement_of(jobs, stage_id, args.episode)
        if settled is None:
            stage, _ = stopped_settlement._stage(jobs, {"job_id": args.job, "stage_id": stage_id, "episode": args.episode,
                                                       "request": {"attempt_id": args.attempt}})
            operations = stopped_settlement._composed(configuration, jobs, control)
            opened.callback(operations.close)
            with answered_recovery.nominated(control, receipt):
                answer = operations.conclude(stage, submission.job_of(jobs, args.job))
            settled = ending.settlement_of(jobs, stage_id, args.episode)
            if settled is None:
                reason = (answer or {}).get("reason") or (answer or {}).get("held_reason") or "implementation ending remains held"
                answered_recovery.refuse(reason)
        if settled["attempt_id"] != args.attempt or not settled["evidence"].get("checkpoint_id"):
            answered_recovery.refuse("no settled checkpoint for the selected attempt")
    return {"selection": receipt, "settlement": settled}
