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
import os
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
	parser.add_argument("--config",
	                    help="the instance configuration (baton.json); "
	                         "every command except init/activate/"
	                         "bootstrap requires it")
	parser.add_argument("--participant",
	                    help="team.member; the acting identity, validated "
	                         "against the accepted configuration before any "
	                         "output")
	parser.add_argument("--op-id", dest="op_id",
	                    help="optional client operation identity (WS-5): "
	                         "with it a mutation is effectively-once — "
	                         "an exact retry replays the one committed "
	                         "result; without it the weaker "
	                         "read-before-retry tier applies. Pure reads "
	                         "take none.")
	parser.add_argument("--ref", dest="refs", action="append",
	                    help="ordered typed asset reference "
	                         "(ROOT_ID:relative/path independent, or "
	                         "WORK-ID:relative/path dossier-relative); "
	                         "repeatable; commits with the act. Pure "
	                         "reads take none.")
	parser.add_argument("--answer-ref", dest="answer_refs",
	                    action="append",
	                    help="accept only: references riding the emitted "
	                         "ANSWER message (explicit compound "
	                         "placement)")
	parser.add_argument("--expect-projection",
	                    help="fail unless the projection version is "
	                         "compatible with this")
	sub = parser.add_subparsers(dest="command", required=True)

	cmd = sub.add_parser("init")
	cmd.add_argument("directory",
	                 help="the coordination home to scaffold; must "
	                 "exist and hold no managed Baton files (one-shot)")
	cmd = sub.add_parser("activate")
	cmd.add_argument("directory",
	                 help="the coordination home holding the edited "
	                 "baton.json")
	sub.add_parser("regen")
	cmd = sub.add_parser("resolve")
	cmd.add_argument("locator",
	                 help="ROOT_ID:relative/path, or a WORK id whose "
	                 "effective binding resolves")
	cmd.add_argument("--roots-file", dest="roots_file", required=True,
	                 help="the explicit machine-local resolver JSON")
	cmd = sub.add_parser("bootstrap")
	cmd.add_argument("--root", required=True,
	                 help="the configured project root id to vendor "
	                 "into")
	cmd.add_argument("--roots-file", dest="roots_file", required=True,
	                 help="the explicit machine-local resolver JSON")
	cmd.add_argument("--template", action="append", dest="templates",
	                 help="numbered template file to vendor; default: "
	                 "every shipped template")

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
	cmd.add_argument("--binding",
	                 help="atomic creation binding "
	                 "ROOT_ID:work/records/YYYY/MM/<stable-record>")

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
	# R73: omitting --rationale or --outcome refuses through the JSON
	# stderr/exit-one agent contract, never argparse prose — the checks
	# live in the transition.
	cmd.add_argument("--rationale",
	                 help="the non-empty terminal rationale; durable "
	                 "review evidence for every outcome")
	cmd.add_argument("--outcome",
	                 help="exactly satisfying, non-satisfying, rejected, "
	                 "or cancelled")
	cmd.add_argument("--duplicate-of", dest="duplicate_of",
	                 help="the surviving canonical work id; a duplicate "
	                 "is a rejected close carrying this explicit "
	                 "non-gating link")
	cmd = sub.add_parser("block")
	cmd.add_argument("work")
	cmd.add_argument("--on", required=True, help="the blocker work id")
	cmd = sub.add_parser("mark-seen")
	cmd.add_argument("discussion")
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
	cmd = sub.add_parser("operation-log")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=100)
	cmd = sub.add_parser("revisions")
	cmd.add_argument("work")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=100)
	cmd = sub.add_parser("bind")
	cmd.add_argument("work")
	cmd.add_argument("--root", help="a live configured root id")
	cmd.add_argument("--path", help="the canonical permanent record "
	                 "path: work/records/YYYY/MM/<stable-record>")
	cmd.add_argument("--expect", dest="expected_revision", type=int,
	                 help="the expected prior binding revision")
	cmd.add_argument("--rationale",
	                 help="why this correction/attachment is right")
	cmd.add_argument("--git", dest="git_provenance",
	                 help="optional immutable Git provenance")
	cmd = sub.add_parser("bindings")
	cmd.add_argument("work")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=100)
	cmd = sub.add_parser("revise")
	cmd.add_argument("work")
	# R73 discipline: omission refuses through the JSON exit-one
	# contract in the transition, never argparse prose.
	cmd.add_argument("--message", dest="message_seq", type=int,
	                 help="the ONE durable discussion message promoted "
	                 "as the complete contract")
	cmd.add_argument("--expect", dest="expected_revision", type=int,
	                 help="the expected prior revision; stale or "
	                 "concurrent edits refuse, never overwrite")
	cmd.add_argument("--rationale",
	                 help="why this promotion is the agreed contract")
	cmd = sub.add_parser("discuss")
	cmd.add_argument("--body", required=True)
	cmd.add_argument("--label", action="append", required=True,
	                 help="a #WORK label; repeatable; at least one open "
	                 "work of your own team")
	cmd = sub.add_parser("say")
	cmd.add_argument("discussion")
	cmd.add_argument("--body", required=True)
	cmd.add_argument("--include", help="comma list / wildcards; the ONLY "
	                 "fan-out — attention wiring, changes nothing else")
	cmd.add_argument("--request", help="ONE endpoint owing a response; "
	                 "acts on the --on work")
	cmd.add_argument("--pass-to", dest="pass_to", help="ONE endpoint; "
	                 "moves the --on work's baton")
	cmd.add_argument("--set-next", dest="set_next",
	                 help="planned return endpoint; requires --pass-to")
	cmd.add_argument("--on", help="the ONE labelled open work an @ or => "
	                 "acts against; may be omitted only when exactly one "
	                 "label is eligible")
	cmd = sub.add_parser("label")
	cmd.add_argument("discussion")
	cmd.add_argument("--work", required=True)
	cmd = sub.add_parser("unlabel")
	cmd.add_argument("discussion")
	cmd.add_argument("--work", required=True)
	cmd = sub.add_parser("thread")
	cmd.add_argument("discussion")
	cmd.add_argument("--after", type=int, default=0)
	# R68: the default is a LEGAL value; every supplied limit reaches the
	# contract unchanged — an over-max request refuses, never clamps.
	cmd.add_argument("--limit", type=int, default=500)
	cmd = sub.add_parser("discussions")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=100)
	cmd = sub.add_parser("work-discussions")
	cmd.add_argument("work")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=100)
	cmd = sub.add_parser("events")
	cmd.add_argument("--after", type=int, default=0)
	cmd.add_argument("--limit", type=int, default=1000)

	sub.add_parser("tui")

	args = parser.parse_args(argv)
	try:
		jsonapi.require_version(args.expect_projection)
		mutations = {"activate", "regen", "create", "accept",
		             "respond", "dispose", "close", "block",
		             "mark-seen", "classify", "phase", "round",
		             "extend", "report", "assess", "abandon", "revise",
		             "discuss", "say", "label", "unlabel"}
		filesystem = {"init", "bootstrap", "resolve"}
		if args.command not in {"init", "activate", "bootstrap"} and \
				not args.config:
			raise WorkError(f"{args.command} needs --config naming the "
			                f"instance configuration")
		if args.command in filesystem and (args.op_id or args.refs or
		                                   args.answer_refs):
			raise WorkError(
				f"{args.command} is a filesystem operation outside the "
				f"authority; it carries no operation identity and no "
				f"asset references")
		mutations.add("bind")
		if args.op_id is not None and args.command not in mutations:
			raise WorkError(
				f"{args.command} is a pure read and takes no operation "
				f"identity; --op-id protects mutations only (WS-5)")
		if args.refs and args.command not in mutations:
			raise WorkError(
				f"{args.command} is a pure read and carries no asset "
				f"references; --ref commits with a mutation (WS-6)")
		if args.answer_refs and args.command != "accept":
			raise WorkError(
				"--answer-ref is accept's explicit compound placement; "
				"no other act emits an answer message")
		if args.command == "init":
			# The coordination-home SCAFFOLD (WS-6): editable strict
			# JSON plus instructions, no database, deliberately
			# one-shot.
			from baton_work import project
			result = project.scaffold_home(args.directory)
			print(json.dumps({"projection_version":
			                  jsonapi.PROJECTION_VERSION,
			                  "result": result}, indent=2,
			                 sort_keys=True))
			return 0
		if args.command == "activate":
			# The ONE authoritative generation-one validation and
			# creation — committed by a NAMED participant of the
			# proposed document (WS-5 P9a); on an existing authority
			# the current-generation identity gate and the
			# exact/conflicting operation lookup run first. A refusal
			# leaves no database and no accepted state.
			if not args.participant:
				raise WorkError("activate needs --participant naming "
				                "a member of the proposed "
				                "generation-1 document")
			result = lifecycle.init_from_config(
				os.path.join(args.directory, "baton.json"),
				participant=args.participant,
				op_id=args.op_id, refs=args.refs or ())
			print(json.dumps({"projection_version":
			                  jsonapi.PROJECTION_VERSION,
			                  "result": result}, indent=2, sort_keys=True))
			return 0
		if args.command == "bootstrap":
			from baton_work import project
			result = project.bootstrap_project(
				args.root, args.roots_file,
				templates=args.templates)
			print(json.dumps({"projection_version":
			                  jsonapi.PROJECTION_VERSION,
			                  "result": result}, indent=2,
			                 sort_keys=True))
			return 0
		if args.command == "regen":
			team, member = _need_participant(args)
			result = lifecycle.accept_config(args.config,
			                                 actor=f"{team}.{member}",
			                                 op_id=args.op_id,
			                                 refs=args.refs or ())
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
			store, binding=args.binding,
			team=args.team, kind=args.kind, title=args.title,
			origin=args.origin, author=member, body=args.body,
			parent=args.parent, classification=args.classification,
			phase=args.phase, follow_up_of=args.follow_up_of, op_id=args.op_id,
			refs=args.refs or ())
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
			answer_refs=args.answer_refs or (),
			body=args.body, into=args.into, create=create, op_id=args.op_id,
			refs=args.refs or ())
	if command == "respond":
		team, member = _need_participant(args)
		return transitions.respond_obligation(
			store, args.obligation, team=team, member=member, body=args.body, op_id=args.op_id,
			refs=args.refs or ())
	if command == "dispose":
		team, member = _need_participant(args)
		return transitions.dispose_obligation(
			store, args.obligation, team=team, member=member,
			disposition=args.disposition, op_id=args.op_id,
			refs=args.refs or ())
	if command == "close":
		team, member = _need_participant(args)
		return transitions.close_work(store, args.work, actor_team=team,
		                              actor=member,
		                              rationale=args.rationale,
		                              outcome=args.outcome,
		                              duplicate_of=args.duplicate_of, op_id=args.op_id,
			refs=args.refs or ())
	if command == "block":
		team, member = _need_participant(args)
		return transitions.add_dependency(store, args.work, args.on,
		                                  actor_team=team, actor=member, op_id=args.op_id,
			refs=args.refs or ())
	if command == "operation-log":
		team, member = _need_participant(args)
		return projection.operation_log(store, f"{team}.{member}",
		                                after=args.after,
		                                limit=args.limit)
	if command == "revisions":
		_need_participant(args)
		return projection.revisions(store, args.work, after=args.after,
		                            limit=args.limit)
	if command == "resolve":
		team, member = _need_participant(args)
		from baton_work import project
		mapping = project.load_resolver(args.roots_file)
		left, _colon, rest = args.locator.partition(":")
		# R92: the ONE shared locator grammar — every suffix is a
		# contained relative POSIX path, root and dossier forms alike;
		# the machine-local resolver never authorizes locators the
		# accepted grammar refuses.
		if rest:
			transitions._validate_ref_path(
				rest, "resolve: the locator suffix must stay a "
				"contained relative path")
		import re as _re
		if _re.match(r"^[0-9a-f]{8}-W[0-9]+$", left):
			view = projection.detail(store, left, viewer_team=team,
			                         viewer_member=member)
			binding = view["binding"]
			if binding is None:
				raise WorkError(f"{left} has no dossier binding to "
				                f"resolve")
			base = project.resolve_base(mapping, binding["root"])
			absolute = os.path.join(base, binding["path"])
			if rest:
				absolute = os.path.join(absolute, rest)
			return {"root": binding["root"], "path": binding["path"],
			        "relative": rest or None, "absolute": absolute}
		# R95: the independent form IS `ROOT_ID:relative/path` — a bare
		# root or an empty suffix is not a canonical locator; only a
		# bare WORK id resolves a dossier root.
		if not _colon or not rest:
			raise WorkError(
				f"{args.locator!r} is not a canonical independent "
				f"locator: the form is ROOT_ID:<contained relative "
				f"path> with a non-empty contained suffix; a bare "
				f"WORK id resolves its dossier root")
		# R92: an independent root must be live in the ACCEPTED
		# authority — the resolver maps accepted root ids, it is never
		# a second root catalog.
		live = store.conn.execute(
			"SELECT removed FROM roots WHERE root=?",
			(left,)).fetchone()
		if live is None or live["removed"]:
			raise WorkError(
				f"root {left!r} is not a live configured root; the "
				f"machine-local resolver never authorizes roots "
				f"outside the accepted catalog")
		base = project.resolve_base(mapping, left)
		return {"root": left, "path": rest,
		        "absolute": os.path.join(base, rest)}
	if command == "bind":
		team, member = _need_participant(args)
		return transitions.bind_work(
			store, args.work, actor_team=team, actor=member,
			root=args.root, path=args.path,
			expected_revision=args.expected_revision,
			rationale=args.rationale,
			git_provenance=args.git_provenance, op_id=args.op_id,
			refs=args.refs or ())
	if command == "bindings":
		_need_participant(args)
		return projection.bindings(store, args.work, after=args.after,
		                           limit=args.limit)
	if command == "revise":
		team, member = _need_participant(args)
		return transitions.revise_work(
			store, args.work, actor_team=team, actor=member,
			message_seq=args.message_seq,
			expected_revision=args.expected_revision,
			rationale=args.rationale, op_id=args.op_id,
			refs=args.refs or ())
	if command == "discuss":
		team, member = _need_participant(args)
		return transitions.create_discussion(
			store, actor_team=team, actor=member, body=args.body,
			labels=args.label, op_id=args.op_id,
			refs=args.refs or ())
	if command == "say":
		team, member = _need_participant(args)
		return transitions.post_discussion(
			store, args.discussion, author_team=team, author=member,
			body=args.body, include=args.include or (),
			request=args.request, pass_to=args.pass_to,
			set_next=args.set_next, on=args.on, op_id=args.op_id,
			refs=args.refs or ())
	if command == "label":
		team, member = _need_participant(args)
		return transitions.label_discussion(
			store, args.discussion, args.work, actor_team=team,
			actor=member, op_id=args.op_id,
			refs=args.refs or ())
	if command == "unlabel":
		team, member = _need_participant(args)
		return transitions.unlabel_discussion(
			store, args.discussion, args.work, actor_team=team,
			actor=member, op_id=args.op_id,
			refs=args.refs or ())
	if command == "thread":
		team, member = _need_participant(args)
		return projection.thread(store, args.discussion,
		                         viewer_team=team, viewer_member=member,
		                         after=args.after, limit=args.limit)
	if command == "discussions":
		team, member = _need_participant(args)
		return projection.discussions_for(store, viewer_team=team,
		                                  viewer_member=member,
		                                  after=args.after,
		                                  limit=args.limit)
	if command == "work-discussions":
		team, member = _need_participant(args)
		return projection.work_discussions(store, args.work,
		                                   viewer_team=team,
		                                   viewer_member=member,
		                                   after=args.after,
		                                   limit=args.limit)
	if command == "mark-seen":
		# R61: the ONE explicit public seen mutation, discussion-scoped.
		# Reads (thread/detail/list) are byte-pure; nothing named like a
		# read may write.
		team, member = _need_participant(args)
		return transitions.seen_discussion(
			store, args.discussion, team=team, member=member,
			up_to_seq=args.up_to, op_id=args.op_id,
			refs=args.refs or ())
	if command == "round":
		team, member = _need_participant(args)
		return transitions.create_round(
			store, args.work, actor_team=team, actor=member,
			candidate=args.candidate, assign=args.assign,
			review_at=args.review_at, op_id=args.op_id,
			refs=args.refs or ())
	if command == "extend":
		team, member = _need_participant(args)
		return transitions.extend_round(
			store, args.work, args.round, actor_team=team, actor=member,
			review_at=args.review_at, op_id=args.op_id,
			refs=args.refs or ())
	if command == "report":
		team, member = _need_participant(args)
		return transitions.report(
			store, args.obligation, team=team, member=member,
			observation=args.observation, evidence=args.evidence, op_id=args.op_id,
			refs=args.refs or ())
	if command == "assess":
		team, member = _need_participant(args)
		return transitions.assess(
			store, args.obligation, actor_team=team, actor=member,
			assessment=args.assessment, rationale=args.rationale, op_id=args.op_id,
			refs=args.refs or ())
	if command == "abandon":
		team, member = _need_participant(args)
		return transitions.abandon_round(
			store, args.work, args.round, actor_team=team, actor=member,
			reason=args.reason, op_id=args.op_id,
			refs=args.refs or ())
	if command == "classify":
		team, member = _need_participant(args)
		return transitions.classify(store, args.work, actor_team=team,
		                            actor=member,
		                            classification=args.classification, op_id=args.op_id,
			refs=args.refs or ())
	if command == "phase":
		team, member = _need_participant(args)
		if args.wait_gates and args.wait_obligation is not None:
			raise WorkError("waiting records exactly ONE typed condition: "
			                "gates or one obligation, not both")
		wait = "gates" if args.wait_gates else args.wait_obligation
		return transitions.set_phase(store, args.work, actor_team=team,
		                             actor=member, phase=args.phase,
		                             reason=args.reason, wait=wait, op_id=args.op_id,
			refs=args.refs or ())

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
