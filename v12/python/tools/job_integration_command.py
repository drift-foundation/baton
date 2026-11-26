"""`manager record-integration`: the owner records an existing target commit for a Job. W385263.

    manager record-integration --instance <instance.json> --job <job_id>
        --candidate <accepted head commit> --commit <target commit> --repository <target repository>

Owner decision M386422 (2026-11-26). Works with every service stopped: it opens
the Job store to append one journalled receipt and reads the control store and
the target repository read-only. It starts nothing, changes no stage, attempt,
line, custody or verdict, and prints the receipt as one JSON line. An identical
retry prints the same receipt; a different commit or candidate for a Job that
already has one is refused, as is a candidate that is not the Job's accepted,
retained and importable candidate, or a commit whose tree is not that candidate's.
"""
import argparse
import json
import sys

from baton_v12.job_manager import JobStore, job_integration
from baton_v12.job_manager.reading import _ReadOnly
from baton_v12.worker_manager import ControlStore
from tools import instance

COMMANDS = ("record-integration",)


def main(argv, *, clock=None, stream=None):
    from tools.job_manager import _utc_clock
    from tools.manual_job import _owner_actor

    parser = argparse.ArgumentParser(prog="manager record-integration", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--instance", required=True, help="the installed instance.json selector")
    parser.add_argument("--job", required=True, help="the ordinary Job's identity")
    parser.add_argument("--candidate", required=True, help="the accepted candidate's head commit, in full")
    parser.add_argument("--commit", required=True, help="the existing target commit the candidate was integrated as")
    parser.add_argument("--repository", required=True, help="absolute path of the target repository holding that commit")
    args = parser.parse_args(argv)
    selector = instance.read(args.instance)
    instance.verify(selector)
    actor = _owner_actor(selector, args.instance)
    target = job_integration.target_commit(args.repository, args.commit)
    clock = clock or _utc_clock()
    with JobStore.open(selector["job_store"], authority_uuid=selector["authority_uuid"],
                       incarnation="owner-integration", clock=clock) as store, \
            ControlStore.open_readonly(selector["control_store"], incarnation="owner-integration", clock=clock) as control:
        answer = job_integration.record(store, args.job, candidate=args.candidate, target=target, actor=actor,
                                        operations=_ReadOnly(control), control=control)
    print(json.dumps(answer, sort_keys=True), file=stream or sys.stdout)
    return 0
