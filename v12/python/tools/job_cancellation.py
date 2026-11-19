"""Instance-addressed Job cancellation request and status; no serving composition.

W383215 / DESIGN LIM-5. `cancel-job` journals the request and the admission
fence in the installed instance's Job store and reports what the stores say
about its targets; `cancel-status` is the same report, read-only. Neither
composes a deployment, opens an Authority, mints a session, takes the serving
manager's instance guard or touches a container: the serving sweep carries the
request out through the existing owners on its own ticks, and a manager that is
not running is reported as targets that are still pending, never as ceased.

WHY NO MANAGER GUARD. The guard says "one manager acts on this instance", and a
request that took it could not be made while the manager serves -- which is
exactly when an operator needs it. The Job store's own journal serialises the
request: the same Job and reason replay one committed record, another reason
collides, and the serving ticks interleave with it by the database's lock.
"""
import argparse
import hashlib
from contextlib import ExitStack
import json
from pathlib import Path
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, cancellation, job_control,
                                   submission)
from baton_v12.worker_manager import ControlStore, boundaries
from tools import instance

# W383217 moved this to /2: the answer carries `control`, the Job's admitted
# finite control and derived deadlines, and the cancellation report names its
# trigger (an operator request or a deadline expiry).
SCHEMA = "baton.v12.installed-cancellation/2"
COMMANDS = ("cancel-job", "cancel-status")


def _refuse(message):
    raise ContractRefusal("refused", "precondition", message)


def _document(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as fault:
        _refuse("deployment document is unreadable: " + type(fault).__name__)


def _binding(selector, configuration):
    """The same installed binding the settlement commands recognise."""
    return {"instance": selector["destination"],
            "authority_uuid": selector["authority_uuid"],
            "runtime_digest": selector["runtime"]["digest"],
            "deployment_digest": "sha256:" + hashlib.sha256(json.dumps(
                configuration, sort_keys=True, separators=(",", ":"),
                ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest(),
            "job_store": selector["job_store"],
            "control_store": selector["control_store"]}


def execute(command, selector_path, *, job_id, reason=None, clock=None):
    """Compose the public owners over the stores the installed selector names."""
    from tools.job_manager import _utc_clock
    clock = clock or _utc_clock()
    if command not in COMMANDS:
        _refuse("unknown installed cancellation command")
    boundaries.identity(job_id, "a Job id")
    selector = instance.read(selector_path)
    instance.verify(selector)
    configuration = _document(selector["deployment"])
    places = instance.layout(selector["destination"])
    if configuration.get("authority_uuid") != selector["authority_uuid"] \
            or Path(configuration.get("authority_store", "")).resolve() \
            != Path(places["authority_store"]).resolve():
        _refuse("cancellation deployment and instance Authority do not agree")
    binding = _binding(selector, configuration)
    with ExitStack() as opened:
        # RECOGNITION FIRST, READ-ONLY. An existing store at this build's
        # version holding this Job is what a writable open may follow.
        reader = opened.enter_context(JobStore.open_readonly(
            selector["job_store"], authority_uuid=selector["authority_uuid"],
            incarnation="cancellation-reader", clock=clock))
        if submission.job_of(reader, job_id) is None:
            _refuse("cancellation Job does not exist in this instance")
        control = opened.enter_context(ControlStore.open_readonly(
            selector["control_store"], incarnation="cancellation-reader",
            clock=clock))
        jobs = reader
        request = None
        if command == "cancel-job":
            if reason is None or not str(reason).strip():
                _refuse("cancel-job carries the operator's own --reason")
            jobs = opened.enter_context(JobStore.open(
                selector["job_store"],
                authority_uuid=selector["authority_uuid"],
                incarnation="cancellation", clock=clock))
            request = cancellation.request(jobs, job_id=job_id, reason=reason)
        # THE AXES ARE READ AFTER THE JOB STORE'S VIEW IS RELEASED; `report`
        # materializes under one read boundary and asks `axes_of` outside it.
        report = cancellation.report(
            jobs, job_id, now=clock(),
            observed_of=lambda entry: cancellation.observed_from(
                control, entry["attempt"]["attempt_id"]))
        return {"schema": SCHEMA, "command": command, "binding": binding,
                "job_id": job_id,
                "request": (request if request is not None
                            else cancellation.fence_of(jobs, job_id)),
                "cancellation": report,
                "control": job_control.report(jobs, job_id, now=clock())}


def main(argv, *, clock=None, stream=None):
    parser = argparse.ArgumentParser(prog="manager cancellation")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--instance", required=True,
                        help="installed instance.json selector")
    parser.add_argument("--job", required=True, help="the Job to cancel")
    parser.add_argument("--reason", default=None,
                        help="the operator's own reason; required by "
                             "cancel-job and refused by cancel-status")
    args = parser.parse_args(argv)
    if args.command == "cancel-job" and args.reason is None:
        parser.error("cancel-job needs --reason")
    if args.command == "cancel-status" and args.reason is not None:
        parser.error("cancel-status takes no --reason")
    answer = execute(args.command, args.instance, job_id=args.job,
                     reason=args.reason, clock=clock)
    print(json.dumps(answer, sort_keys=True), file=stream or sys.stdout)
    return 0
