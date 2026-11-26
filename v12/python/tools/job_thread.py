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
    parser.add_argument("action", nargs="?", default="read", choices=("read", "note", "answer"))
    parser.add_argument("--instance", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--thread", default="main", choices=("main",))
    parser.add_argument("--body")
    parser.add_argument("--operation")
    parser.add_argument("--request")
    parser.add_argument("--phase")
    parser.add_argument("--checkpoint")
    args = parser.parse_args(argv)
    if args.action != "read" and not args.body:
        parser.error("note and answer require --body")
    if args.action == "note" and not args.operation:
        parser.error("note requires a stable --operation for safe retries")
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
            elif args.action == "answer":
                main_thread.answer(jobs, authority, args.job, args.request, args.body, phase=args.phase, checkpoint_id=args.checkpoint, actor=actor, thread=args.thread)
            result = main_thread.read(jobs, authority, args.job, thread=args.thread)
    print(json.dumps(result, sort_keys=True), file=stream or sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
