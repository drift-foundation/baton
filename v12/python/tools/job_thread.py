"""Read main, post a note, or answer one escalated request with services stopped."""
import argparse
import json
import sys

from baton_v12.authority import Authority
from baton_v12.job_manager import JobStore, main_thread
from tools import instance


def main(argv=None, *, clock=None, stream=None):
    from tools.job_manager import _utc_clock
    from tools.manual_job import _owner_actor

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="read", choices=("read", "note", "ruling", "answer"))
    parser.add_argument("--instance", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--thread", default="main", choices=("main",))
    parser.add_argument("--body")
    parser.add_argument("--operation")
    parser.add_argument("--request")
    parser.add_argument("--phase")
    parser.add_argument("--checkpoint")
    parser.add_argument("--standing", action="store_true", help="designate a targeted answer as a standing ruling")
    parser.add_argument("--supersedes", action="append", default=[], metavar="MESSAGE_ID", help="replace an earlier same-Job ruling (repeatable)")
    args = parser.parse_args(argv)
    if args.standing and args.action != "answer":
        parser.error("--standing applies to a targeted answer")
    if args.supersedes and args.action != "ruling" and not args.standing:
        parser.error("--supersedes requires a ruling or standing answer")
    if args.action != "read" and not args.body:
        parser.error("note, ruling and answer require --body")
    if args.action in ("note", "ruling") and not args.operation:
        parser.error("note and ruling require a stable --operation for safe retries")
    if args.action == "answer" and not all((args.request, args.phase, args.checkpoint)):
        parser.error("answer requires --request, --phase and --checkpoint")
    selector = instance.read(args.instance)
    instance.verify(selector)
    actor = None if args.action == "read" else _owner_actor(selector, args.instance)
    places = instance.layout(selector["destination"])
    opening = JobStore.open_readonly if args.action == "read" else JobStore.open
    with opening(selector["job_store"], authority_uuid=selector["authority_uuid"], incarnation="main-client", clock=clock or _utc_clock()) as jobs:
        with Authority.open_readonly(places["authority_store"], expected_authority_uuid=selector["authority_uuid"]) as authority:
            if args.action == "note":
                main_thread.note(jobs, authority, args.job, args.body, actor=actor, operation_id=args.operation, thread=args.thread)
            elif args.action == "ruling":
                main_thread.ruling(jobs, authority, args.job, args.body, actor=actor, operation_id=args.operation,
                                   supersedes=args.supersedes, thread=args.thread)
            elif args.action == "answer":
                main_thread.answer(jobs, authority, args.job, args.request, args.body, phase=args.phase, checkpoint_id=args.checkpoint, actor=actor, thread=args.thread, standing=args.standing, supersedes=args.supersedes)
            result = main_thread.read(jobs, authority, args.job, thread=args.thread)
    print(json.dumps(result, sort_keys=True), file=stream or sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
