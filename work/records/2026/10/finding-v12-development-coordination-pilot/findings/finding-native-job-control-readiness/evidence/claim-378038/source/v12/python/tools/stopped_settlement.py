"""Instance-addressed retained failure settlement; no serving composition."""
import argparse
import hashlib
from contextlib import ExitStack
import json
from pathlib import Path
import sys

from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import JobStore, episodes, scheduler, submission
from baton_v12.worker_manager import ControlStore, attempts, boundaries, tokens
from baton_v12.worker_manager import stopped_settlement as owner
from tools import instance, single_worker, stage_execution
from tools.fresh_attempt_ports import InstanceOwnership

SCHEMA = "baton.v12.installed-settlement/1"
COMMANDS = ("settlement-preview", "settle-stopped", "settlement-status")


def _refuse(message):
    raise ContractRefusal("refused", "precondition", message)


def _document(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as fault:
        _refuse("settlement document is unreadable: " + type(fault).__name__)


def _binding(selector, configuration):
    return {"instance": selector["destination"], "authority_uuid": selector["authority_uuid"],
            "runtime_digest": selector["runtime"]["digest"], "deployment_digest": "sha256:" + hashlib.sha256(json.dumps(configuration, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest(),
            "job_store": selector["job_store"], "control_store": selector["control_store"]}


def _request(document, binding):
    held = boundaries.document(document, "an installed settlement request", required=("schema", "binding", "job_id", "stage_id", "episode", "operation_id", "request"))
    if held["schema"] != SCHEMA or held["binding"] != binding:
        _refuse("settlement request names another instance, package or deployment")
    for key in ("job_id", "stage_id", "operation_id"):
        boundaries.identity(held[key], "an installed settlement identity")
    if type(held["episode"]) is not int or held["episode"] < 1:
        _refuse("settlement episode counts from one")
    expected = _operation(held)
    if type(held["request"]) is not dict or held["request"].get("operation_id") != expected:
        _refuse("settlement core operation does not bind this installed selection")
    return held


def _operation(held):
    return "installed-settlement:" + digest({key: held[key] for key in ("binding", "job_id", "stage_id", "episode", "operation_id")})[7:]


def _stage(jobs, held):
    with jobs.read_snapshot():
        if submission.job_of(jobs, held["job_id"]) is None:
            _refuse("settlement Job does not exist in this instance")
        rows = [row for row in submission.stages_of(jobs, held["job_id"]) if row["stage_id"] == held["stage_id"]]
        episode = episodes.episode_of(jobs, held["stage_id"], held["episode"])
        if len(rows) != 1 or episode is None:
            _refuse("settlement stage or episode does not belong to this Job")
        stage = episodes.attempting(rows[0], episode)
        allocation = scheduler.allocation_of(jobs, stage["attempt_id"])
    if allocation is None or allocation["stage_id"] != stage["stage_id"] or allocation["episode"] != stage["episode"]:
        _refuse("settlement episode has no exact recorded worker allocation")
    if held.get("request") is not None and held["request"].get("attempt_id") != stage["attempt_id"]:
        _refuse("settlement request names another attempt")
    return stage, allocation


def _worker(configuration, allocation):
    # Validate the whole deployment with its existing owner, without starting it.
    given = stage_execution.held_configuration(configuration)
    if allocation["generation"] != given["pool_generation"]:
        _refuse("settlement allocation belongs to another deployment generation")
    workers = [one for one in configuration["workers"] if one["worker_id"] == allocation["worker_id"]]
    if len(workers) != 1:
        _refuse("settlement worker is no longer configured")
    return workers[0]["deployment"]


class _AssignmentReader:
    def __init__(self, authority):
        self.authority = authority

    def assignment_of(self, work_id, authority_uuid):
        if authority_uuid != self.authority.authority_uuid:
            _refuse("settlement assignment belongs to another Authority")
        return self.authority.assignment_of(work_id)


def _runtime(deployment):
    # Only read capabilities escape this composition. No stop/remove/normalize.
    from tools.job_manager import _ReclaimAdapter
    source = _ReclaimAdapter(deployment["engine"], single_worker.effective_engine_run(),
                             deployment.get("custodian_image_digest"))
    class Observation:
        observe = staticmethod(source.observe)
    if deployment.get("custodian_image_digest") is not None:
        Observation.surviving_helpers = staticmethod(source.surviving_helpers)
    return Observation()


def _core_request(control, stage, held, delivery):
    with control.snapshot():
        records = [one for one in attempts.runtime_recovery_inventory(control) if one["attempt_id"] == stage["attempt_id"]]
    if len(records) != 1 or records[0]["token"] is None:
        _refuse("settlement attempt has no exact retained runtime and token")
    runtime, token = records[0]["runtime"], records[0]["token"]
    return {"schema": owner.SCHEMA, "operation_id": _operation(held),
            "attempt_id": stage["attempt_id"], "runtime_id": runtime["runtime_id"],
            "assignment": runtime["assignment"], "start_operation_id": token["operation"],
            "token": {key: token[key] for key in ("domain", "generation", "owner", "launch")},
            "failure_digest": owner.failure_digest(delivery)}


def execute(command, selector_path, *, document=None, job_id=None, stage_id=None,
            episode=None, operation_id=None, clock=None):
    """Compose public owners over the stores derived by the installed selector."""
    from tools.job_manager import _utc_clock
    clock = clock or _utc_clock()
    if command not in COMMANDS:
        _refuse("unknown installed settlement command")
    selector = instance.read(selector_path)
    instance.verify(selector)
    configuration = _document(selector["deployment"])
    places = instance.layout(selector["destination"])
    if configuration.get("authority_uuid") != selector["authority_uuid"] or Path(configuration.get("authority_store", "")).resolve() != Path(places["authority_store"]).resolve():
        _refuse("settlement deployment and instance Authority do not agree")
    binding = _binding(selector, configuration)
    if command == "settlement-preview":
        held = {"schema": SCHEMA, "binding": binding, "job_id": job_id, "stage_id": stage_id,
                "episode": episode, "operation_id": operation_id}
        for key in ("job_id", "stage_id", "operation_id"):
            boundaries.identity(held[key], "an installed settlement identity")
        if type(episode) is not int or episode < 1:
            _refuse("settlement episode counts from one")
    else:
        held = _request(document, binding)
    with ExitStack() as opened:
        jobs = opened.enter_context(JobStore.open_readonly(selector["job_store"], authority_uuid=selector["authority_uuid"], incarnation="settlement-reader", clock=clock))
        control = opened.enter_context(ControlStore.open_readonly(selector["control_store"], incarnation="settlement-reader", clock=clock))
        report = owner.status(control, held["request"]) if command != "settlement-preview" else {"state": "not-selected"}
        # A writable opener is reached only after the existing database has
        # passed read-only recognition and the instance guard has been acquired.
        if command == "settle-stopped":
            ownership = InstanceOwnership.of(control, configuration)
            opened.enter_context(ownership.held())
            opened.enter_context(ownership.invocation("settlement:" + held["request"]["attempt_id"]))
            if _binding(instance.read(selector_path), _document(selector["deployment"])) != binding:
                _refuse("settlement instance or deployment changed before exclusion was acquired")
        stage, allocation = _stage(jobs, held)
        deployment = _worker(configuration, allocation)
        if command == "settlement-status":
            return {"schema": "baton.v12.installed-settlement-status/1", "selection": held, "settlement": owner.status(control, held["request"])}
        # Replay must not reopen Authority or depend on launch files.
        delivery = None
        port = None
        if report["state"] == "not-selected":
            delivery = single_worker.settlement_delivery(deployment, jobs, control, stage)
            if delivery is None:
                _refuse("settlement has no validated retained exchange delivery")
            authority = opened.enter_context(Authority.open_readonly(places["authority_store"], expected_authority_uuid=selector["authority_uuid"]))
            port = _AssignmentReader(authority)
        if command == "settlement-preview":
            held["request"] = _core_request(control, stage, held, delivery)
            answer = owner.preview(control, port, _runtime(deployment), tokens.Governance("workspace", tokens.workspace_identity), request=held["request"], delivery=delivery)
            return {"schema": "baton.v12.installed-settlement-preview/1", "request": held, "eligibility": answer}
        writable = opened.enter_context(ControlStore.open(selector["control_store"], incarnation="settlement", clock=clock))
        answer = owner.settle_stopped(writable, port, _runtime(deployment), tokens.Governance("workspace", tokens.workspace_identity), request=held["request"], delivery=delivery)
        return {"schema": "baton.v12.installed-settlement-status/1", "selection": held, "settlement": answer}


def main(argv, *, clock=None, stream=None):
    parser = argparse.ArgumentParser(prog="manager settlement")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--instance", required=True, help="installed instance.json selector")
    parser.add_argument("--document", help="exact request emitted by preview")
    parser.add_argument("--job")
    parser.add_argument("--stage")
    parser.add_argument("--episode", type=int)
    parser.add_argument("--operation-id")
    args = parser.parse_args(argv)
    if args.command == "settlement-preview":
        if args.document is not None or any(value is None for value in (args.job, args.stage, args.episode, args.operation_id)):
            parser.error("preview needs --job, --stage, --episode and --operation-id, without --document")
    elif args.document is None or any(value is not None for value in (args.job, args.stage, args.episode, args.operation_id)):
        parser.error("settlement and status need --document, without selection overrides")
    answer = execute(args.command, args.instance, document=_document(args.document) if args.document else None,
                     job_id=args.job, stage_id=args.stage, episode=args.episode, operation_id=args.operation_id, clock=clock)
    print(json.dumps(answer, sort_keys=True), file=stream or sys.stdout)
    return 0
