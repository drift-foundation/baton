"""Instance-addressed operator decisions for owner-paced Jobs."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, manual
from tools import instance

COMMANDS = ("create", "add-phase", "start-phase", "finish-phase", "close-job")


def _phase_document(selector, store, job_id, phase, request):
    from baton_v12.contracts.manifest import job_input_identity
    from baton_v12.job_manager import research
    from baton_v12.worker_manager import boundaries
    from tools.creation_ports import DeploymentDerivation

    pins = ("source_commit", "profile_name", "profile_digest", "policy_digest", "input_digest")
    document = boundaries.document(request, "a research assignment",
                                   required=("kind", "statement", "scope", "depends_on"), optional=(*pins, "work_id"))
    execution = manual.execution_job_id(job_id, phase)
    if "work_id" not in document:
        document = dict(document, work_id=manual.generated_work_id(selector["authority_uuid"], execution),
                        work_origin="generated")
    earlier = manual.phase_for_execution(store, execution)
    if earlier:
        # Replay uses precisely the immutable pins accepted for this phase.
        return {key: value for key, value in earlier["document"].items() if key in pins} | document

    held = DeploymentDerivation(selector["destination"]).held()
    if held["authority_uuid"] != selector["authority_uuid"]:
        raise research.refusal("research deployment and installed instance disagree on the Authority")
    base = document.get("source_commit", held.get("line_declared_base"))
    if not base:
        raise research.refusal("this deployment has no declared base; select source_commit")
    if held.get("line_declared_base") and held["line_declared_base"] != base:
        raise research.refusal("source_commit differs from the deployment's declared base")
    document = dict(document, source_commit=base)
    candidates = []
    for worker in held["workers"]:
        if worker["role"] != "research":
            continue
        given = worker["deployment"]
        selection = {key: given[key] for key in ("profile_name", "profile_digest", "policy_digest")}
        if any(document.get(key, value) != value for key, value in selection.items()):
            continue
        material = research.delivery(given, document)
        selection["input_digest"] = job_input_identity(material["input_manifest"])
        if document.get("input_digest", selection["input_digest"]) != selection["input_digest"]:
            continue
        if selection not in candidates:
            candidates.append(selection)
    if not candidates:
        raise research.refusal("no configured research worker matches this phase's input, profile and policy")
    if len(candidates) > 1:
        raise research.refusal("multiple research inputs, profiles or policies match; select the required pins")
    return dict(document, **candidates[0])


def _owner_actor(selector, selector_path):
    """Authenticate the installing OS account and resolve its configured Authority endpoint."""
    from baton_v12.authority import Authority, Refusal

    uid = os.getuid()
    places = instance.layout(selector["destination"])
    if uid != os.geteuid() or Path(selector_path).absolute() != Path(places["instance"]):
        raise ContractRefusal("refused", "precondition", "finish-phase requires the installed owner's account and canonical selector")
    try:
        private_root = False
        for name in ("destination", "instance", "install_inputs", "stores", "authority_store", "job_store"):
            info = Path(places[name]).lstat()
            directory = name in ("destination", "stores")
            right_type = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
            if info.st_uid != uid or not right_type or (not private_root and info.st_mode & 0o022):
                raise ContractRefusal("refused", "precondition", "finish-phase requires owner-controlled installation path: " + name)
            if name == "destination":
                private_root = not info.st_mode & 0o011
        inputs = json.loads(Path(places["install_inputs"]).read_bytes())
        participant = inputs.get("owner_participant") if isinstance(inputs, dict) else None
        if not isinstance(participant, str) or not participant:
            raise ContractRefusal("refused", "precondition", "the installed deployment has no configured owner_participant")
        with Authority.open_readonly(places["authority_store"], expected_authority_uuid=selector["authority_uuid"]) as authority:
            return {"participant": participant, "principal": authority.principal_of(participant),
                    "uid": uid, "authority_uuid": authority.authority_uuid}
    except (OSError, ValueError, Refusal) as exc:
        raise ContractRefusal("refused", "precondition", "could not verify the installed owner binding: " + str(exc)) from exc


def main(argv, *, clock=None, stream=None):
    from tools.job_manager import _read, _utc_clock

    parser = argparse.ArgumentParser(prog="manager", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in COMMANDS:
        sub = commands.add_parser(command)
        sub.add_argument("--instance", required=True, help="installed instance.json selector")
        if command == "create":
            sub.add_argument("--mode", choices=["manual"], required=True)
        else:
            sub.add_argument("--job", required=True)
        if command in ("add-phase", "start-phase", "finish-phase"):
            sub.add_argument("--phase", required=True)
        if command == "finish-phase":
            sub.add_argument("--outcome", required=True, choices=["success", "failure"])
        if command in ("create", "add-phase"):
            sub.add_argument("--document", required=True, help="JSON object, or - for stdin")
    args = parser.parse_args(argv)
    selector = instance.read(args.instance)
    instance.verify(selector)
    actor = _owner_actor(selector, args.instance) if args.command == "finish-phase" else None
    document = None
    if args.command in ("create", "add-phase"):
        try:
            document = json.loads(_read(args.document))
        except (OSError, ValueError) as exc:
            raise ContractRefusal("refused", "precondition", "unreadable MANUAL document: " + type(exc).__name__) from exc
        if type(document) is not dict:
            parser.error("--document must contain a JSON object")
    if args.command == "create" and not document.get("job_id"):
        parser.error("the MANUAL Job document requires job_id")
    with JobStore.open(selector["job_store"], authority_uuid=selector["authority_uuid"],
                       incarnation="manual-operator", clock=clock or _utc_clock()) as store:
        if args.command == "create":
            answer = manual.create(store, document.pop("job_id"), document)
        elif args.command == "add-phase":
            document = _phase_document(selector, store, args.job, args.phase, document)
            answer = manual.add_phase(store, args.job, args.phase, document)
        elif args.command == "start-phase":
            answer = manual.start_phase(store, args.job, args.phase)
        elif args.command == "finish-phase":
            from baton_v12.job_manager import manual_decision
            answer = manual_decision.finish(store, args.job, args.phase, args.outcome, actor=actor)
        else:
            answer = manual.close_job(store, args.job)
    print(json.dumps(answer, sort_keys=True), file=stream or sys.stdout)
    return 0
