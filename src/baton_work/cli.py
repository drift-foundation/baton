"""`baton-work`: the JSON rendering of the canonical projection — A6/C3.

The launch surface is the CONFIGURATION BOUNDARY (C3): `--config PATH` names
the instance, `--participant team.member` names the acting identity, and both
are validated through the bound-config lifecycle BEFORE any output or curses.
`--authority`/`--viewer` are gone, not aliased — an identity by assertion is
the defect the boundary ended. Topology is written only by accepted
configuration generations: `init` consumes generation 1, `regen` accepts
generation+1 under the config capability, and no registry verb exists.

JSON in flags, JSON out, no terminal formatting; errors are JSON on stderr
with exit 1, because an agent parsing prose refusals is the defect this
surface exists to end.
"""

from __future__ import annotations

import argparse
import json
import sys

from baton_work.authority import WorkError
from baton_work import jsonapi, lifecycle, projection, transitions


def _participant(value: str) -> tuple[str, str]:
	team, dot, member = value.partition(".")
	if not dot or not team or not member:
		raise WorkError(f"participant {value!r} is not team.member shaped")
	return team, member


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(prog="baton-work")
	parser.add_argument("--config", required=True,
	                    help="the instance configuration (baton.json)")
	parser.add_argument("--participant",
	                    help="team.member; the acting identity, validated "
	                         "against the accepted configuration before any "
	                         "output")
	parser.add_argument("--expect-projection",
	                    help="fail unless the projection version is "
	                         "compatible with this")
	sub = parser.add_subparsers(dest="command", required=True)

	sub.add_parser("init")
	sub.add_parser("regen")

	cmd = sub.add_parser("create")
	cmd.add_argument("--team", required=True)
	cmd.add_argument("--kind", required=True)
	cmd.add_argument("--title", required=True)
	cmd.add_argument("--origin", required=True)
	cmd.add_argument("--body", required=True)
	cmd.add_argument("--parent")
	cmd.add_argument("--classification", help="canonical value; defaults to "
	                 "'unknown'")
	cmd.add_argument("--phase", help="initial operational phase; defaults "
	                 "to 'queued'")
	cmd.add_argument("--follow-up-of", dest="follow_up_of",
	                 help="id of the CLOSED work this follows up (WS-2)")

	cmd = sub.add_parser("post")
	cmd.add_argument("work")
	cmd.add_argument("--body", required=True)
	cmd.add_argument("--include", help="comma list / wildcards; the fan-out")
	cmd.add_argument("--request", help="ONE endpoint owing a response")
	cmd.add_argument("--pass-to", dest="pass_to", help="ONE endpoint; moves "
	                 "the baton")
	cmd.add_argument("--set-next", dest="set_next",
	                 help="planned return endpoint; requires --pass-to")

	cmd = sub.add_parser("accept")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--body", required=True,
	                 help="the acceptance rationale, answered into the "
	                 "consumer's discussion")
	cmd.add_argument("--into", help="existing provider work id")
	cmd.add_argument("--create", action="store_true",
	                 help="create the provider work in the same "
	                 "transaction")
	cmd.add_argument("--kind")
	cmd.add_argument("--title")
	cmd.add_argument("--classification")
	cmd.add_argument("--phase")
	cmd.add_argument("--parent")

	cmd = sub.add_parser("respond")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--body", required=True)
	cmd = sub.add_parser("dispose")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--disposition", required=True)

	cmd = sub.add_parser("close")
	cmd.add_argument("work")
	cmd.add_argument("--disposition", required=True)
	cmd.add_argument("--outcome", required=True,
	                 help="exactly satisfying or non-satisfying (WS-2)")
	cmd = sub.add_parser("block")
	cmd.add_argument("work")
	cmd.add_argument("--on", required=True, help="the blocker work id")
	cmd = sub.add_parser("mark-seen")
	cmd.add_argument("work")
	cmd.add_argument("--up-to", dest="up_to", type=int, required=True)
	cmd = sub.add_parser("classify")
	cmd.add_argument("work")
	cmd.add_argument("--as", dest="classification", required=True,
	                 help="canonical classification value")
	cmd = sub.add_parser("phase")
	cmd.add_argument("work")
	cmd.add_argument("--to", dest="phase", required=True,
	                 help="canonical phase value")
	cmd.add_argument("--reason", help="required when parking")
	cmd.add_argument("--wait-on-gates", dest="wait_gates",
	                 action="store_true",
	                 help="waiting: wake when every required child and "
	                 "blocker is closed")
	cmd.add_argument("--wait-on-obligation", dest="wait_obligation",
	                 type=int, help="waiting: wake when this one pending @ "
	                 "obligation completes")

	cmd = sub.add_parser("round")
	cmd.add_argument("work")
	cmd.add_argument("--candidate", required=True,
	                 help="exact candidate/artifact identity; immutable")
	cmd.add_argument("--assign", action="append", required=True,
	                 help="one exact verifier endpoint; repeatable")
	cmd.add_argument("--review-at", dest="review_at",
	                 help="optional UTC ISO instant when the round becomes "
	                 "due for review")
	cmd = sub.add_parser("extend")
	cmd.add_argument("work")
	cmd.add_argument("--round", type=int, required=True)
	cmd.add_argument("--review-at", dest="review_at", required=True)
	cmd = sub.add_parser("report")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--observation", required=True,
	                 help="exactly passed, failed, or unable")
	cmd.add_argument("--evidence", required=True)
	cmd = sub.add_parser("assess")
	cmd.add_argument("obligation", type=int)
	cmd.add_argument("--as", dest="assessment", required=True,
	                 help="exactly accepted, rejected, or inconclusive")
	cmd.add_argument("--rationale", required=True)
	cmd = sub.add_parser("abandon")
	cmd.add_argument("work")
	cmd.add_argument("--round", type=int, required=True)
	cmd.add_argument("--reason", required=True)

	sub.add_parser("home")
	sub.add_parser("obligations")
	sub.add_parser("summary")
	cmd = sub.add_parser("wait")
	cmd.add_argument("--timeout", type=float, required=True,
	                 help="seconds to block for actionable work; the wait "
	                 "is read-only and mutates nothing")
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

	sub.add_parser("tui")

	args = parser.parse_args(argv)
	try:
		jsonapi.require_version(args.expect_projection)
		if args.command == "init":
			# The one command with no authority to open: it creates one from
			# the generation-1 configuration.
			result = lifecycle.init_from_config(args.config)
			print(json.dumps({"projection_version":
			                  jsonapi.PROJECTION_VERSION,
			                  "result": result}, indent=2, sort_keys=True))
			return 0
		if args.command == "regen":
			team, member = _need_participant(args)
			result = lifecycle.accept_config(args.config,
			                                 actor=f"{team}.{member}")
			print(json.dumps({"projection_version":
			                  jsonapi.PROJECTION_VERSION,
			                  "result": result}, indent=2, sort_keys=True))
			return 0
		# EVERY ordinary command opens through the bound lifecycle and
		# validates the participant BEFORE producing anything — including
		# before curses claims the screen. R1: uniformly, not only when one
		# happens to be supplied — an anonymous read was the identity-by-
		# assertion defect wearing a read-only disguise.
		_need_participant(args)
		store = lifecycle.open_bound(args.config)
		try:
			_validate_participant(store, args.participant)
			if args.command == "tui":
				if not args.participant:
					raise WorkError("tui needs --participant team.member")
				from baton_work.tui import run as tui_run
				import curses
				curses.wrapper(tui_run, store,
				               *_participant(args.participant))
				return 0
			result = _dispatch(store, args)
			snapshot_seq = (result.pop("snapshot_seq", None)
			                if isinstance(result, dict) else None)
			if snapshot_seq is None and \
					isinstance(result, projection.Snapshotted):
				snapshot_seq = result.snapshot_seq
			print(json.dumps(jsonapi.envelope(store,
			                                  participant=args.participant,
			                                  result=result,
			                                  snapshot_seq=snapshot_seq),
			                 indent=2, sort_keys=True))
		finally:
			store.close()
		return 0
	except WorkError as refusal:
		print(json.dumps({"error": str(refusal)}), file=sys.stderr)
		return 1


def _validate_participant(store, value: str) -> None:
	team, member = _participant(value)
	row = store.conn.execute(
		"SELECT 1 FROM members WHERE team=? AND handle=? AND removed=0",
		(team, member)).fetchone()
	if row is None:
		raise WorkError(
			f"{value} is not a participant of the accepted configuration "
			f"generation {store.meta().get('accepted_generation')}")


def _need_participant(args) -> tuple[str, str]:
	if not args.participant:
		raise WorkError(f"{args.command} needs --participant team.member")
	return _participant(args.participant)


def _dispatch(store: Authority, args):
	command = args.command
	if command == "create":
		team, member = _need_participant(args)
		if team != args.team:
			raise WorkError(f"participant {team}.{member} cannot author "
			                f"for {args.team}")
		return transitions.create_work(
			store, team=args.team, kind=args.kind, title=args.title,
			origin=args.origin, author=member, body=args.body,
			parent=args.parent, classification=args.classification,
			phase=args.phase, follow_up_of=args.follow_up_of)
	if command == "post":
		team, member = _need_participant(args)
		return transitions.post_message(
			store, args.work, author_team=team, author=member,
			body=args.body, include=args.include or (),
			request=args.request, pass_to=args.pass_to,
			set_next=args.set_next)
	if command == "accept":
		team, member = _need_participant(args)
		create_only = {"--kind": args.kind, "--title": args.title,
		               "--classification": args.classification,
		               "--phase": args.phase, "--parent": args.parent}
		if not args.create:
			# R50: the forms fail CLOSED — an --into acceptance must not
			# silently ignore creation options a typo supplied.
			stray = [flag for flag, value in create_only.items()
			         if value is not None]
			if stray:
				raise WorkError(
					f"accept --into takes no creation option; remove "
					f"{', '.join(stray)} or use --create")
		create = None
		if args.create:
			if args.kind is None or args.title is None:
				raise WorkError("accept --create requires --kind and "
				                "--title")
			create = {"kind": args.kind, "title": args.title,
			          "classification": args.classification,
			          "phase": args.phase, "parent": args.parent}
		return transitions.accept_obligation(
			store, args.obligation, actor_team=team, actor=member,
			body=args.body, into=args.into, create=create)
	if command == "respond":
		team, member = _need_participant(args)
		return transitions.respond_obligation(
			store, args.obligation, team=team, member=member, body=args.body)
	if command == "dispose":
		team, member = _need_participant(args)
		return transitions.dispose_obligation(
			store, args.obligation, team=team, member=member,
			disposition=args.disposition)
	if command == "close":
		team, member = _need_participant(args)
		return transitions.close_work(store, args.work, actor_team=team,
		                              actor=member,
		                              disposition=args.disposition,
		                              outcome=args.outcome)
	if command == "block":
		team, member = _need_participant(args)
		return transitions.add_dependency(store, args.work, args.on,
		                                  actor_team=team, actor=member)
	if command == "mark-seen":
		team, member = _need_participant(args)
		return transitions.mark_seen(store, args.work, team=team,
		                             member=member, up_to_seq=args.up_to)
	if command == "round":
		team, member = _need_participant(args)
		return transitions.create_round(
			store, args.work, actor_team=team, actor=member,
			candidate=args.candidate, assign=args.assign,
			review_at=args.review_at)
	if command == "extend":
		team, member = _need_participant(args)
		return transitions.extend_round(
			store, args.work, args.round, actor_team=team, actor=member,
			review_at=args.review_at)
	if command == "report":
		team, member = _need_participant(args)
		return transitions.report(
			store, args.obligation, team=team, member=member,
			observation=args.observation, evidence=args.evidence)
	if command == "assess":
		team, member = _need_participant(args)
		return transitions.assess(
			store, args.obligation, actor_team=team, actor=member,
			assessment=args.assessment, rationale=args.rationale)
	if command == "abandon":
		team, member = _need_participant(args)
		return transitions.abandon_round(
			store, args.work, args.round, actor_team=team, actor=member,
			reason=args.reason)
	if command == "classify":
		team, member = _need_participant(args)
		return transitions.classify(store, args.work, actor_team=team,
		                            actor=member,
		                            classification=args.classification)
	if command == "phase":
		team, member = _need_participant(args)
		if args.wait_gates and args.wait_obligation is not None:
			raise WorkError("waiting records exactly ONE typed condition: "
			                "gates or one obligation, not both")
		wait = "gates" if args.wait_gates else args.wait_obligation
		return transitions.set_phase(store, args.work, actor_team=team,
		                             actor=member, phase=args.phase,
		                             reason=args.reason, wait=wait)

	if command == "home":
		team, member = _need_participant(args)
		return projection.home(store, viewer_team=team, viewer_member=member)
	if command == "obligations":
		team, _member = _need_participant(args)
		return projection.obligations(store, viewer_team=team)
	if command == "summary":
		team, _member = _need_participant(args)
		return projection.team_summary(store, viewer_team=team)
	if command == "wait":
		team, _member = _need_participant(args)
		return projection.wait_actionable(store, viewer_team=team,
		                                  timeout_seconds=args.timeout)
	if command == "detail":
		team, member = _need_participant(args)
		return projection.detail(store, args.work, viewer_team=team,
		                         viewer_member=member)
	if command == "children":
		team, member = _need_participant(args)
		return projection.children(store, args.work, viewer_team=team,
		                           viewer_member=member)
	if command == "new":
		team, member = _need_participant(args)
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


def entry() -> None:
	"""The PROCESS entry point — the one that owns the exit status.

	`main` returns its code so tests can call it in-process; a packaged
	archive must target THIS instead, because zipapp's generated __main__
	calls the target and discards its return value — which turned every
	structured refusal into exit 0 (found by WF-06's cycle-refusal
	checkpoint; regression:
	`test_packaged.test_a_refusal_exits_nonzero_through_the_archive`)."""
	sys.exit(main())


if __name__ == "__main__":
	entry()
