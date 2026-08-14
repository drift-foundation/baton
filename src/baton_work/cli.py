"""`baton-work`: the JSON rendering of the canonical projection — A6.

JSON in flags, JSON out, no terminal formatting. Every read is an enveloped
projection call; every mutation returns the committed record inside the same
envelope. Errors are JSON on stderr with exit 1, because an agent parsing
prose refusals is the defect this surface exists to end.
"""

from __future__ import annotations

import argparse
import json
import sys

from baton_work.authority import Authority, WorkError
from baton_work import jsonapi, projection, transitions


def _viewer(value: str) -> tuple[str, str]:
	team, dot, member = value.partition(".")
	if not dot or not team or not member:
		raise WorkError(f"viewer {value!r} is not team.member shaped")
	return team, member


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(prog="baton-work")
	parser.add_argument("--authority", required=True)
	parser.add_argument("--viewer", help="team.member; required for "
	                    "per-viewer reads and every mutation")
	parser.add_argument("--expect-projection",
	                    help="fail unless the projection version is "
	                         "compatible with this")
	sub = parser.add_subparsers(dest="command", required=True)

	sub.add_parser("init")
	for name in ("register-team", "register-kind"):
		cmd = sub.add_parser(name)
		cmd.add_argument("--team", required=True)
		if name == "register-kind":
			cmd.add_argument("--kind", required=True)
		cmd.add_argument("--display", required=True)
	cmd = sub.add_parser("register-member")
	cmd.add_argument("--team", required=True)
	cmd.add_argument("--member", required=True)
	cmd.add_argument("--display", required=True)
	cmd = sub.add_parser("retire-kind")
	cmd.add_argument("--team", required=True)
	cmd.add_argument("--kind", required=True)

	cmd = sub.add_parser("create")
	cmd.add_argument("--team", required=True)
	cmd.add_argument("--kind", required=True)
	cmd.add_argument("--title", required=True)
	cmd.add_argument("--origin", required=True)
	cmd.add_argument("--body", required=True)
	cmd.add_argument("--parent")

	cmd = sub.add_parser("post")
	cmd.add_argument("work")
	cmd.add_argument("--body", required=True)
	cmd.add_argument("--include", help="comma list / wildcards; the fan-out")
	cmd.add_argument("--request", help="ONE endpoint owing a response")
	cmd.add_argument("--pass-to", dest="pass_to", help="ONE endpoint; moves "
	                 "the baton")
	cmd.add_argument("--set-next", dest="set_next",
	                 help="planned return endpoint; requires --pass-to")

	cmd = sub.add_parser("respond")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--body", required=True)
	cmd = sub.add_parser("dispose")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--disposition", required=True)

	cmd = sub.add_parser("close")
	cmd.add_argument("work")
	cmd.add_argument("--disposition", required=True)
	cmd = sub.add_parser("reopen")
	cmd.add_argument("work")
	cmd.add_argument("--reason", required=True)
	cmd = sub.add_parser("block")
	cmd.add_argument("work")
	cmd.add_argument("--on", required=True, help="the blocker work id")
	cmd = sub.add_parser("mark-seen")
	cmd.add_argument("work")
	cmd.add_argument("--up-to", dest="up_to", type=int, required=True)

	sub.add_parser("home")
	sub.add_parser("obligations")
	for name in ("detail", "children", "links", "breadcrumb", "new"):
		cmd = sub.add_parser(name)
		cmd.add_argument("work")
	cmd = sub.add_parser("discussion")
	cmd.add_argument("work")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=1000)
	cmd = sub.add_parser("events")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=1000)

	args = parser.parse_args(argv)
	try:
		jsonapi.require_version(args.expect_projection)
		if args.command == "init":
			store = Authority.init(args.authority)
		else:
			store = Authority(args.authority)
		with store:
			result = _dispatch(store, args)
			viewer = args.viewer
			print(json.dumps(jsonapi.envelope(store, viewer=viewer,
			                                  result=result),
			                 indent=2, sort_keys=True))
		return 0
	except WorkError as refusal:
		print(json.dumps({"error": str(refusal)}), file=sys.stderr)
		return 1


def _need_viewer(args) -> tuple[str, str]:
	if not args.viewer:
		raise WorkError(f"{args.command} needs --viewer team.member")
	return _viewer(args.viewer)


def _dispatch(store: Authority, args):
	command = args.command
	if command == "init":
		return {"initialized": True}
	if command == "register-team":
		return store.register_team(args.team, args.display)
	if command == "register-member":
		return store.register_member(args.team, args.member, args.display)
	if command == "register-kind":
		return store.register_kind(args.team, args.kind, args.display)
	if command == "retire-kind":
		return store.retire_kind(args.team, args.kind)

	if command == "create":
		team, member = _need_viewer(args)
		if team != args.team:
			raise WorkError(f"viewer {team}.{member} cannot author for "
			                f"{args.team}")
		return transitions.create_work(
			store, team=args.team, kind=args.kind, title=args.title,
			origin=args.origin, author=member, body=args.body,
			parent=args.parent)
	if command == "post":
		team, member = _need_viewer(args)
		return transitions.post_message(
			store, args.work, author_team=team, author=member,
			body=args.body, include=args.include or (),
			request=args.request, pass_to=args.pass_to,
			set_next=args.set_next)
	if command == "respond":
		team, member = _need_viewer(args)
		return transitions.respond_obligation(
			store, args.obligation, team=team, member=member, body=args.body)
	if command == "dispose":
		team, member = _need_viewer(args)
		return transitions.dispose_obligation(
			store, args.obligation, team=team, member=member,
			disposition=args.disposition)
	if command == "close":
		team, member = _need_viewer(args)
		return transitions.close_work(store, args.work, actor_team=team,
		                              actor=member,
		                              disposition=args.disposition)
	if command == "reopen":
		team, member = _need_viewer(args)
		return transitions.reopen_work(store, args.work, actor_team=team,
		                               actor=member, reason=args.reason)
	if command == "block":
		team, member = _need_viewer(args)
		return transitions.add_dependency(store, args.work, args.on,
		                                  actor_team=team, actor=member)
	if command == "mark-seen":
		team, member = _need_viewer(args)
		return transitions.mark_seen(store, args.work, team=team,
		                             member=member, up_to_seq=args.up_to)

	if command == "home":
		team, member = _need_viewer(args)
		return projection.home(store, viewer_team=team, viewer_member=member)
	if command == "obligations":
		team, _member = _need_viewer(args)
		return projection.obligations(store, viewer_team=team)
	if command == "detail":
		team, member = _need_viewer(args)
		return projection.detail(store, args.work, viewer_team=team,
		                         viewer_member=member)
	if command == "children":
		team, member = _need_viewer(args)
		return projection.children(store, args.work, viewer_team=team,
		                           viewer_member=member)
	if command == "new":
		team, member = _need_viewer(args)
		return projection.new_count(store, args.work, viewer_team=team,
		                            viewer_member=member)
	if command == "links":
		return projection.links(store, args.work)
	if command == "breadcrumb":
		return projection.breadcrumb(store, args.work)
	if command == "discussion":
		return projection.discussion(store, args.work, after=args.after,
		                             limit=args.limit)
	if command == "events":
		return store.events(after=args.after, limit=args.limit)
	raise WorkError(f"unknown command {command!r}")


if __name__ == "__main__":
	sys.exit(main())
