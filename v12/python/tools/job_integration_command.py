"""`manager record-integration` / `manager decline-integration`: the owner's final integration disposition
for an ordinary Job. W385263; W386746.

    manager record-integration --instance <instance.json> --job <job_id>
        --candidate <accepted head commit> --commit <target commit> --repository <target repository>
    manager decline-integration --instance <instance.json> --job <job_id>
        --candidate <accepted head commit> --reason <the owner's reason>

W386746 (owner ruling 2026-11-28): decline-integration records that the Job's
accepted candidate will NOT be integrated. It is final for the Job, bound to the
Job, that candidate and the reason; an identical retry prints the original
receipt (also after a restart), and a different decision -- another reason,
another candidate, or record-integration -- is refused naming the disposition
that exists. The two share one operation identity, so if they race exactly one
succeeds.

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

COMMANDS = ("record-integration", "decline-integration")


def main(argv, *, clock=None, stream=None):
    from tools.job_manager import _utc_clock
    from tools.manual_job import _owner_actor

    parser = argparse.ArgumentParser(prog="manager record-integration", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--instance", required=True, help="the installed instance.json selector")
    parser.add_argument("--job", required=True, help="the ordinary Job's identity")
    parser.add_argument("--candidate", required=True, help="the accepted candidate's head commit, in full")
    parser.add_argument("--commit", help="record-integration: the existing target commit the candidate was integrated as")
    parser.add_argument("--repository", help="record-integration: absolute path of the target repository holding that commit")
    parser.add_argument("--reason", help="decline-integration: the owner's reason, kept exactly")
    args = parser.parse_args(argv)
    if args.command == "record-integration" and (args.commit is None or args.repository is None or args.reason is not None):
        parser.error("record-integration takes --commit and --repository, and no --reason")
    if args.command == "decline-integration" and (args.reason is None or args.commit is not None or args.repository is not None):
        parser.error("decline-integration takes --reason, and no --commit or --repository")
    selector = instance.read(args.instance)
    instance.verify(selector)
    actor = _owner_actor(selector, args.instance)
    target = job_integration.target_commit(args.repository, args.commit) if args.command == "record-integration" else None
    clock = clock or _utc_clock()
    with JobStore.open(selector["job_store"], authority_uuid=selector["authority_uuid"],
                       incarnation="owner-integration", clock=clock) as store, \
            ControlStore.open_readonly(selector["control_store"], incarnation="owner-integration", clock=clock) as control:
        if args.command == "record-integration":
            answer = job_integration.record(store, args.job, candidate=args.candidate, target=target, actor=actor,
                                            operations=_ReadOnly(control), control=control)
        else:
            answer = job_integration.decline(store, args.job, candidate=args.candidate, reason=args.reason, actor=actor,
                                             operations=_ReadOnly(control), control=control)
    print(json.dumps(answer, sort_keys=True), file=stream or sys.stdout)
    return 0
