"""`baton`: the JSON rendering of the canonical projection — A6/C3.

The launch surface is the CONFIGURATION BOUNDARY (C3): `--config PATH` names
the instance, `--participant team.member` names the acting identity, and both
are validated through the bound-config lifecycle BEFORE any output or curses.
`--authority`/`--viewer` are gone, not aliased — an identity by assertion is
the defect the boundary ended. Topology is written only by accepted
configuration generations: `init` consumes generation 1, `regen` accepts
generation+1 under the config capability, and no registry verb exists.

key=value operands in, JSON out, no terminal formatting; errors are JSON
on stderr with exit 1, because an agent parsing prose refusals is the
defect this surface exists to end.
"""

from __future__ import annotations

import json
import os
import sys

from baton_work.authority import WorkError
from baton_work import jsonapi, lifecycle, projection, transitions


# The public MUTATING verbs — shared with the console's command bar so
# only a successful workflow act (never a refused command or pure read)
# refreshes the cached projection (W5 R2). `bind` joins below as it
# always has.
MUTATIONS = frozenset({
	"activate", "regen", "create", "accept", "respond", "dispose",
	"close", "block", "mark-seen", "classify", "claim", "release",
	"phase", "round",
	"extend", "report", "assess", "abandon", "revise", "start-thread",
	"say", "label", "unlabel", "bind"})


def _participant(value: str) -> tuple[str, str]:
	team, dot, member = value.partition(".")
	if not dot or not team or not member:
		raise WorkError(f"participant {value!r} is not team.member shaped")
	return team, member


# -- W13: the ONE strict order-independent key=value operation grammar -------
#
# Launcher context keeps conventional options BEFORE the verb: --config,
# --participant, --expect-projection (each also in its --name=value
# spelling), plus --help for generated discovery. Every operation operand
# after the verb is a `key=value` token — one dialect shared by the
# standalone CLI and the TUI command bar. Tokens split at the FIRST `=`
# (values may contain `=`); unknown keys, missing required keys, closed-
# vocabulary violations, incompatible forms, malformed tokens, duplicate
# singular keys, and retired flag/positional spellings refuse BEFORE
# authority access. Repeatable keys preserve occurrence order. `op-id=`,
# `ref=` and `answer-ref=` are OPERATION semantics: the parser accepts
# them on every verb and the operation's own ruled refusals decide.
#
# THE SPECIFICATION IS THE AUTHORITATIVE PUBLIC GRAMMAR (W13 R1): it
# carries help text, closed value vocabularies, and alternative/
# conditional forms, so generated help (--help) and the W14 assistance
# surface derive from ONE source. Transition-layer validation remains as
# defense in depth for non-CLI callers.

_ORIGINS = ("external-report", "self-initiated", "decomposition")
_CREATION_CLASSIFICATIONS = ("suspected-defect", "confirmed-defect",
                             "limitation", "duplicate", "design-choice",
                             "rejection")
_CLASSIFICATIONS = ("unknown",) + _CREATION_CLASSIFICATIONS
_PHASES = ("queued", "research", "waiting", "active", "review", "parked")
_CREATION_PHASES = ("queued", "research", "active", "review")
_PASS_PHASES = ("queued", "research", "active", "review")
_OUTCOMES = ("satisfying", "non-satisfying", "rejected", "cancelled")
_ASSESSMENTS = ("accepted", "rejected", "inconclusive")


def _key(name, dest=None, *, required=False, repeat=False, kind="str",
         default=None, values=None, help=""):
	return {"name": name, "dest": dest or name.replace("-", "_"),
	        "required": required, "repeat": repeat, "kind": kind,
	        "default": default, "values": values, "help": help}


# Universal operation operands — part of THE public grammar on every
# verb; their ruled applicability (mutations only / accept only) is
# decided by the operation semantics, exactly as the refusals state.
_UNIVERSAL = (
	_key("op-id", help="client operation identity; an exact retry "
	     "replays the one committed result — mutations only, refused "
	     "by pure reads and filesystem verbs"),
	_key("ref", dest="refs", repeat=True,
	     help="ordered typed asset reference; commits with the act — "
	     "mutations only, refused by pure reads and filesystem verbs"),
	_key("answer-ref", dest="answer_refs", repeat=True,
	     help="reference riding accept's emitted answer message — "
	     "accept only"),
)

# Each verb: {"help": one-liner, "keys": (...), and optionally
# "exactly-one": (a, b) — exactly one of the named keys present — plus
# "when": {key: {"requires": (...), "forbids": (...)}} applied when that
# key is present. All enforced BEFORE authority access.
GRAMMAR = {
	"init": {"help": "scaffold an editable coordination home",
	         "keys": (_key("directory", required=True,
	                       help="existing empty directory to scaffold"),)},
	"activate": {"help": "validate baton.json and create the authority",
	             "keys": (_key("directory", required=True,
	                           help="the home holding the edited "
	                           "baton.json"),)},
	"regen": {"help": "accept the edited next-generation baton.json",
	          "keys": ()},
	"resolve": {"help": "turn a portable locator into a machine path",
	            "keys": (_key("locator", required=True,
	                          help="ROOT_ID:relative/path, or a WORK id "
	                          "whose binding resolves"),)},
	"bootstrap": {"help": "vendor this release's templates into a root",
	              "keys": (_key("root", required=True,
	                            help="a configured root id from the "
	                            "accepted baton.json"),
	                       _key("template", dest="templates", repeat=True,
	                            help="numbered template to vendor; "
	                            "default every shipped template"))},
	"create": {"help": "create Work and its born thread atomically",
	           "keys": (_key("team", required=True,
	                         help="the owning team"),
	                    _key("kind", required=True,
	                         help="a registered endpoint kind"),
	                    _key("title", required=True,
	                         help="the Work title (born thread subject)"),
	                    _key("origin", required=True, values=_ORIGINS,
	                         help="how this Work arose"),
	                    _key("body", required=True,
	                         help="the first message body"),
	                    _key("parent", help="containing open Work id"),
	                    _key("classification", required=True,
	                         values=_CREATION_CLASSIFICATIONS,
	                         help="the submitter's concrete "
	                         "classification; 'unknown' refuses"),
	                    _key("phase", values=_CREATION_PHASES,
	                         help="initial phase; defaults to queued"),
	                    _key("follow-up-of",
	                         help="CLOSED Work this follows up"),
	                    _key("binding",
	                         help="atomic creation binding ROOT_ID:"
	                         "work/records/YYYY/MM/<record>"))},
	"accept": {"help": "answer an @ obligation by gating on provider "
	           "Work (existing or created atomically)",
	           "exactly-one": ("into", "create"),
	           "when": {"create": {"requires": ("kind", "title",
	                                            "classification")},
	                    "into": {"forbids": ("kind", "title",
	                                         "classification", "phase",
	                                         "parent")}},
	           "keys": (_key("obligation", required=True, kind="int",
	                         help="the pending @ obligation seq"),
	                    _key("body", required=True,
	                         help="the acceptance rationale"),
	                    _key("into", help="existing provider Work id"),
	                    _key("create", kind="bool", default=False,
	                         help="create the provider Work in the same "
	                         "transaction (value: true)"),
	                    _key("kind", help="provider endpoint kind"),
	                    _key("title", help="provider Work title"),
	                    _key("classification",
	                         values=_CREATION_CLASSIFICATIONS,
	                         help="provider classification"),
	                    _key("phase", values=_CREATION_PHASES,
	                         help="provider initial phase"),
	                    _key("parent", help="provider parent Work"))},
	"respond": {"help": "answer an @ obligation with a message",
	            "keys": (_key("obligation", required=True, kind="int",
	                          help="the pending obligation seq"),
	                     _key("body", required=True,
	                          help="the answer body"))},
	"dispose": {"help": "close an @ obligation without an answer",
	            "keys": (_key("obligation", required=True, kind="int",
	                          help="the pending obligation seq"),
	                     _key("disposition", required=True,
	                          help="why no answer is owed"))},
	"close": {"help": "terminally close Work with outcome + rationale",
	          "conditions": (
	              {"if-key": "duplicate-of",
	               "requires-value": ("outcome", "rejected")},),
	          "keys": (_key("work", required=True, help="the Work id"),
	                   _key("rationale", required=True,
	                        help="durable terminal rationale"),
	                   _key("outcome", required=True, values=_OUTCOMES,
	                        help="the terminal outcome"),
	                   _key("duplicate-of",
	                        help="surviving Work id for a duplicate "
	                        "rejection"))},
	"claim": {"help": "atomically claim open ready Work as its one "
	          "active executor (phase untouched)",
	          "keys": (_key("work", required=True,
	                        help="the Work to claim"),)},
	"release": {"help": "release/recover the active claim (self or "
	            "forced) with an exact compare-and-swap",
	            "keys": (_key("work", required=True, help="the Work id"),
	                     _key("expect", required=True,
	                          help="the exact recorded claimant "
	                          "team.member"),
	                     _key("reason", required=True,
	                          help="durable reason the Work became "
	                          "unclaimed"))},
	"block": {"help": "record a dependency edge (work waits on blocker)",
	          "keys": (_key("work", required=True,
	                        help="the consumer Work"),
	                   _key("on", required=True,
	                        help="the blocker Work"))},
	"mark-seen": {"help": "mark a thread page seen up to a message",
	              "keys": (_key("thread", required=True,
	                            help="the thread id"),
	                       _key("up-to", required=True, kind="int",
	                            help="last seen message seq"))},
	"classify": {"help": "reclassify Work (current handler authority)",
	             "keys": (_key("work", required=True,
	                           help="the Work id"),
	                      _key("as", dest="classification",
	                           required=True, values=_CLASSIFICATIONS,
	                           help="the canonical classification"))},
	"phase": {"help": "move Work to another operational phase",
	          "conditions": (
	              {"if-value": ("to", "parked"),
	               "requires": ("reason",)},
	              {"if-value": ("to", "waiting"), "requires": ("wait",)},
	              {"unless-value": ("to", "waiting"),
	               "forbids": ("wait",)}),
	          "keys": (_key("work", required=True, help="the Work id"),
	                   _key("to", dest="phase", required=True,
	                        values=_PHASES, help="the target phase"),
	                   _key("reason", help="required when parking"),
	                   _key("wait", help="waiting condition: gates, or "
	                        "one pending obligation seq (waiting "
	                        "only)"))},
	"round": {"help": "open a verification round with assignments",
	          "keys": (_key("work", required=True, help="the Work id"),
	                   _key("candidate", required=True,
	                        help="the candidate under verification"),
	                   _key("assign", repeat=True, required=True,
	                        help="verifying endpoint (repeatable)"),
	                   _key("review-at",
	                        help="canonical UTC review instant"))},
	"extend": {"help": "extend an open round's review instant",
	           "keys": (_key("work", required=True, help="the Work id"),
	                    _key("round", required=True, kind="int",
	                         help="the round number"),
	                    _key("review-at", required=True,
	                         help="the new canonical UTC instant"))},
	"report": {"help": "file a verification report",
	           "keys": (_key("obligation", required=True, kind="int",
	                         help="the verification assignment seq"),
	                    _key("observation", required=True,
	                         help="what was observed"),
	                    _key("evidence", required=True,
	                         help="where the evidence lives"))},
	"assess": {"help": "assess a verification report",
	           "keys": (_key("obligation", required=True, kind="int",
	                         help="the reported assignment seq"),
	                    _key("as", dest="assessment", required=True,
	                         values=_ASSESSMENTS,
	                         help="the assessment"),
	                    _key("rationale", required=True,
	                         help="why this assessment"))},
	"abandon": {"help": "abandon an open verification round",
	            "keys": (_key("work", required=True,
	                          help="the Work id"),
	                     _key("round", required=True, kind="int",
	                          help="the round number"),
	                     _key("reason", required=True,
	                          help="why the round ends unresolved"))},
	"home": {"help": "the team summary and root Work rows", "keys": ()},
	"tree": {"help": "the canonical bounded tree window (one snapshot)",
	         "keys": (_key("work", help="optional re-root Work id"),)},
	"obligations": {"help": "the team's pending @ obligations",
	                "keys": ()},
	"summary": {"help": "the always-visible team counters", "keys": ()},
	"wait": {"help": "block until actionable state or timeout",
	         "keys": (_key("timeout", required=True, kind="float",
	                       help="seconds to wait"),)},
	"detail": {"help": "everything about one Work",
	           "keys": (_key("work", required=True,
	                         help="the Work id"),)},
	"children": {"help": "a Work's immediate children",
	             "keys": (_key("work", required=True,
	                           help="the Work id"),)},
	"links": {"help": "typed graph edges with far-row summaries",
	          "keys": (_key("work", required=True,
	                        help="the Work id"),)},
	"breadcrumb": {"help": "root-first containment ancestry",
	               "keys": (_key("work", required=True,
	                             help="the Work id"),)},
	"new": {"help": "the viewer's personal New breakdown",
	        "keys": (_key("work", required=True,
	                      help="the Work id"),)},
	"operation-log": {"help": "the effectively-once operation journal",
	                  "keys": (_key("after", kind="int", default=0,
	                                help="page after this seq"),
	                           _key("limit", kind="int", default=100,
	                                help="page size"))},
	"revisions": {"help": "a Work's contract revision history",
	              "keys": (_key("work", required=True,
	                            help="the Work id"),
	                       _key("after", kind="int", default=0,
	                            help="page after this revision"),
	                       _key("limit", kind="int", default=100,
	                            help="page size"))},
	"bind": {"help": "correct or attach the canonical dossier binding "
	         "(compare-and-swap, append-only history)",
	         "keys": (_key("work", required=True, help="the Work id"),
	                  _key("root", required=True,
	                       help="a live configured root id"),
	                  _key("path", required=True,
	                       help="the canonical record path work/records/"
	                       "YYYY/MM/<record>"),
	                  _key("expect", dest="expected_revision",
	                       required=True, kind="int",
	                       help="the expected prior binding revision"),
	                  _key("rationale", required=True,
	                       help="why this correction/attachment is "
	                       "right"),
	                  _key("git", dest="git_provenance",
	                       help="optional immutable Git provenance"))},
	"bindings": {"help": "a Work's append-only binding history",
	             "keys": (_key("work", required=True,
	                           help="the Work id"),
	                      _key("after", kind="int", default=0,
	                           help="page after this revision"),
	                      _key("limit", kind="int", default=100,
	                           help="page size"))},
	"revise": {"help": "promote one durable message as the complete "
	           "Work contract (compare-and-swap)",
	           "keys": (_key("work", required=True, help="the Work id"),
	                    _key("message", dest="message_seq",
	                         required=True, kind="int",
	                         help="the message promoted as the "
	                         "contract"),
	                    _key("expect", dest="expected_revision",
	                         required=True, kind="int",
	                         help="the expected prior revision"),
	                    _key("rationale", required=True,
	                         help="why this promotion is the agreed "
	                         "contract"))},
	"start-thread": {"help": "open a labelled thread with its first "
	                 "message",
	                 "keys": (_key("subject", required=True,
	                               help="the thread subject"),
	                          _key("body", required=True,
	                               help="the first message body"),
	                          _key("label", repeat=True, required=True,
	                               help="Work id to label "
	                               "(repeatable)"))},
	"say": {"help": "post one message, optionally carrying operators",
	        "conditions": (
	            {"exclusive": ("request", "pass-to")},
	            {"if-key": "on",
	             "requires-any": ("request", "pass-to")},
	            {"if-key": "phase", "requires": ("pass-to",)},
	            {"if-key": "set-next", "requires": ("pass-to",)}),
	        "keys": (_key("thread", required=True,
	                      help="the thread id"),
	                 _key("body", required=True,
	                      help="the message body"),
	                 _key("include", help="attention fan-out list/"
	                      "wildcards"),
	                 _key("request", help="ONE endpoint owing a "
	                      "response (acts on on=)"),
	                 _key("pass-to", help="ONE endpoint; moves the "
	                      "baton of on="),
	                 _key("phase", dest="pass_phase",
	                      values=_PASS_PHASES,
	                      help="the destination phase the pass records "
	                      "atomically; derived from the destination "
	                      "stage role when omitted"),
	                 _key("set-next", help="planned return endpoint "
	                      "(with pass-to)"),
	                 _key("on", help="the labelled open Work an @ or "
	                      "=> acts against"))},
	"label": {"help": "label a thread to a Work",
	          "keys": (_key("thread", required=True,
	                        help="the thread id"),
	                   _key("work", required=True,
	                        help="the Work id"))},
	"unlabel": {"help": "remove a thread's Work label",
	            "keys": (_key("thread", required=True,
	                          help="the thread id"),
	                     _key("work", required=True,
	                          help="the Work id"))},
	"thread": {"help": "one thread's paged messages",
	           "keys": (_key("thread", required=True,
	                         help="the thread id"),
	                    _key("after", kind="int", default=0,
	                         help="page after this message seq"),
	                    _key("limit", kind="int", default=500,
	                         help="page size"))},
	"threads": {"help": "the viewer's paged thread listing",
	            "keys": (_key("after", kind="int", default=0,
	                          help="page after this seq"),
	                     _key("limit", kind="int", default=100,
	                          help="page size"))},
	"work-threads": {"help": "a Work's paged thread set",
	                 "keys": (_key("work", required=True,
	                               help="the Work id"),
	                          _key("after", kind="int", default=0,
	                               help="page after this seq"),
	                          _key("limit", kind="int", default=100,
	                               help="page size"))},
	"events": {"help": "the audit trail, ascending by sequence",
	           "keys": (_key("after", kind="int", default=0,
	                         help="page after this seq"),
	                    _key("limit", kind="int", default=1000,
	                         help="page size"))},
	"tui": {"help": "the curses console on this instance",
	        "keys": (_key("refresh", kind="float", default=2.0,
	                      help="auto-refresh seconds (positive)"),)},
}

_GLOBALS = ("--config", "--participant", "--expect-projection")


class _Args:
	"""The parsed invocation — launcher globals plus one verb's
	key=value operands, every dest present."""


def _verb_spec(verb):
	return {entry["name"]: entry
	        for entry in tuple(GRAMMAR[verb]["keys"]) + _UNIVERSAL}


def render_help(verb=None) -> str:
	"""Generated discovery — derived from THE one specification, so it
	can never drift into a second hand-maintained grammar (W13 R2)."""
	def describe(name):
		info = GRAMMAR[name]
		lines = [f"{name} — {info['help']}"]
		for entry in tuple(info["keys"]) + _UNIVERSAL:
			marks = []
			marks.append("required" if entry["required"] else "optional")
			if entry["repeat"]:
				marks.append("repeatable")
			if entry["kind"] != "str":
				marks.append(entry["kind"])
			line = f"  {entry['name']}=  ({', '.join(marks)})"
			if entry["values"]:
				line += "  one of: " + ", ".join(entry["values"])
			if entry["help"]:
				line += f"  — {entry['help']}"
			lines.append(line)
		exactly = info.get("exactly-one")
		if exactly:
			lines.append("  exactly one of: "
			             + " | ".join(f"{name}=" for name in exactly))
		for key, rule in (info.get("when") or {}).items():
			if rule.get("requires"):
				lines.append(f"  with {key}=: requires "
				             + ", ".join(f"{k}=" for k
				                         in rule["requires"]))
			if rule.get("forbids"):
				lines.append(f"  with {key}=: forbids "
				             + ", ".join(f"{k}=" for k
				                         in rule["forbids"]))
		for rule in info.get("conditions", ()):
			if "exclusive" in rule:
				lines.append("  at most one of: "
				             + " | ".join(f"{k}=" for k
				                          in rule["exclusive"]))
			elif "if-value" in rule:
				key, value = rule["if-value"]
				lines.append(
					f"  with {key}={value}: requires "
					+ ", ".join(f"{k}=" for k in rule["requires"]))
			elif "unless-value" in rule:
				key, value = rule["unless-value"]
				lines.append(
					f"  unless {key}={value}: forbids "
					+ ", ".join(f"{k}=" for k in rule["forbids"]))
			elif "if-key" in rule:
				key = rule["if-key"]
				if rule.get("requires-any"):
					lines.append(
						f"  with {key}=: requires one of "
						+ ", ".join(f"{k}=" for k
						            in rule["requires-any"]))
				elif rule.get("requires"):
					lines.append(
						f"  with {key}=: requires "
						+ ", ".join(f"{k}=" for k
						            in rule["requires"]))
				elif rule.get("requires-value"):
					vkey, vvalue = rule["requires-value"]
					lines.append(
						f"  with {key}=: requires {vkey}={vvalue}")
		return "\n".join(lines)

	header = ("usage: baton [--config PATH] [--participant TEAM.MEMBER] "
	          "[--expect-projection V] [--help [VERB]] VERB key=value …\n"
	          "Operation operands are strict order-independent key=value "
	          "tokens; values containing spaces are quoted; each token "
	          "splits at its first '='.\n")
	if verb is not None:
		if verb not in GRAMMAR:
			raise WorkError(f"unknown command {verb!r}")
		return header + "\n" + describe(verb) + "\n"
	body = "\n\n".join(describe(name) for name in sorted(GRAMMAR))
	return header + "\n" + body + "\n"


def _convert(verb, name, kind, value):
	if kind == "int":
		try:
			return int(value)
		except ValueError:
			raise WorkError(f"{verb}: {name}= takes an integer; "
			                f"got {value!r}") from None
	if kind == "float":
		try:
			return float(value)
		except ValueError:
			raise WorkError(f"{verb}: {name}= takes a number; "
			                f"got {value!r}") from None
	if kind == "bool":
		if value != "true":
			raise WorkError(f"{verb}: {name}= is a boolean key and "
			                f"takes exactly the value true; got "
			                f"{value!r}")
		return True
	return value


def _parse_invocation(argv):
	"""The W13 grammar, applied BEFORE any authority access: launcher
	globals (conventional, both `--name VALUE` and `--name=VALUE`
	spellings, duplicates refused), one verb, strict key=value operands
	validated against the one declarative specification. Refusals are
	the JSON exit-one contract."""
	argv = list(argv)
	args = _Args()
	args.config = None
	args.participant = None
	args.expect_projection = None
	args.help_requested = False
	index = 0
	seen_globals = set()
	while index < len(argv) and argv[index].startswith("--"):
		token = argv[index]
		name, equals, inline = token.partition("=")
		if name == "--help":
			args.help_requested = True
			index += 1
			continue
		if name not in _GLOBALS:
			raise WorkError(
				f"{name} is not part of the launcher context; the "
				f"launcher takes only --config, --participant, "
				f"--expect-projection and --help before the verb — "
				f"operation input is key=value after it (W13)")
		if name in seen_globals:
			raise WorkError(f"duplicate {name}; launcher globals are "
			                f"singular and never silently overwritten")
		seen_globals.add(name)
		if equals:
			value = inline
			index += 1
		else:
			if index + 1 >= len(argv):
				raise WorkError(f"{name} needs a value")
			value = argv[index + 1]
			index += 2
		setattr(args, name[2:].replace("-", "_"), value)
	if args.help_requested:
		verb = argv[index] if index < len(argv) else None
		args.command = "--help"
		args.help_verb = verb
		return args
	if index >= len(argv):
		raise WorkError(
			"no command; the grammar is [--config …] [--participant …] "
			"VERB key=value … (--help lists every verb)")
	verb = argv[index]
	if verb not in GRAMMAR:
		raise WorkError(f"unknown command {verb!r} (--help lists every "
		                f"verb)")
	spec = _verb_spec(verb)
	for entry in spec.values():
		setattr(args, entry["dest"],
		        [] if entry["repeat"] else entry["default"])
	seen = set()
	for token in argv[index + 1:]:
		key, equals, value = token.partition("=")
		if token.startswith("--"):
			raise WorkError(
				f"{verb}: {key!r} is retired flag spelling; the "
				f"operation grammar is key=value (W13)")
		if not equals or not key:
			raise WorkError(
				f"{verb}: {token!r} is not a key=value token; "
				f"positional operands are retired (W13)")
		if key not in spec:
			raise WorkError(
				f"{verb}: unknown key {key!r}; accepted keys: "
				f"{', '.join(sorted(spec))}")
		entry = spec[key]
		if entry["values"] is not None and value not in entry["values"]:
			raise WorkError(
				f"{verb}: {key}= takes one of "
				f"{', '.join(entry['values'])}; got {value!r}")
		converted = _convert(verb, key, entry["kind"], value)
		if entry["repeat"]:
			getattr(args, entry["dest"]).append(converted)
		else:
			if key in seen:
				raise WorkError(
					f"{verb}: duplicate {key}=; the key is singular")
			seen.add(key)
			setattr(args, entry["dest"], converted)
	info = GRAMMAR[verb]
	exactly = info.get("exactly-one")
	conditional = set()
	if exactly:
		for rule in (info.get("when") or {}).values():
			conditional.update(rule.get("requires", ()))
		present = [name for name in exactly if name in seen]
		if len(present) != 1:
			raise WorkError(
				f"{verb}: exactly one of "
				f"{' | '.join(name + '=' for name in exactly)} is "
				f"required; got {len(present)}")
		chosen = present[0]
		rule = (info.get("when") or {}).get(chosen, {})
		missing_form = [name for name in rule.get("requires", ())
		                if name not in seen]
		if missing_form:
			raise WorkError(
				f"{verb}: {chosen}= requires "
				f"{', '.join(name + '=' for name in missing_form)}")
		stray_form = [name for name in rule.get("forbids", ())
		              if name in seen]
		if stray_form:
			raise WorkError(
				f"{verb}: {chosen}= forbids "
				f"{', '.join(name + '=' for name in stray_form)}")
	for rule in info.get("conditions", ()):
		if "exclusive" in rule:
			named = [key for key in rule["exclusive"] if key in seen]
			if len(named) > 1:
				raise WorkError(
					f"{verb}: at most one of "
					f"{' | '.join(k + '=' for k in rule['exclusive'])}"
					f"; got {', '.join(k + '=' for k in named)}")
		elif "if-value" in rule:
			key, value = rule["if-value"]
			if getattr(args, spec[key]["dest"], None) == value:
				lacking = [k for k in rule["requires"]
				           if k not in seen]
				if lacking:
					raise WorkError(
						f"{verb}: {key}={value} requires "
						f"{', '.join(k + '=' for k in lacking)}")
		elif "unless-value" in rule:
			key, value = rule["unless-value"]
			if getattr(args, spec[key]["dest"], None) != value:
				stray = [k for k in rule["forbids"] if k in seen]
				if stray:
					raise WorkError(
						f"{verb}: "
						f"{', '.join(k + '=' for k in stray)} "
						f"applies only with {key}={value}")
		elif "if-key" in rule:
			key = rule["if-key"]
			if key in seen:
				if rule.get("requires-any") and not any(
						k in seen for k in rule["requires-any"]):
					raise WorkError(
						f"{verb}: {key}= requires one of "
						f"{', '.join(k + '=' for k in rule['requires-any'])}")
				lacking = [k for k in rule.get("requires", ())
				           if k not in seen]
				if lacking:
					raise WorkError(
						f"{verb}: {key}= requires "
						f"{', '.join(k + '=' for k in lacking)}")
				if rule.get("requires-value"):
					vkey, vvalue = rule["requires-value"]
					if getattr(args, spec[vkey]["dest"],
					           None) != vvalue:
						raise WorkError(
							f"{verb}: {key}= requires "
							f"{vkey}={vvalue}")
	missing = sorted(
		entry["name"] for entry in spec.values()
		if entry["required"] and entry["name"] not in exactly_names(info)
		and entry["name"] not in conditional
		and (entry["name"] not in seen if not entry["repeat"]
		     else not getattr(args, entry["dest"])))
	if missing:
		raise WorkError(
			f"{verb}: missing required "
			f"{', '.join(name + '=' for name in missing)}")
	# `phase wait=` folds the former two flags into the transition's own
	# condition parameter: gates, or one obligation seq.
	if verb == "phase":
		wait = getattr(args, "wait", None)
		args.wait_gates = wait == "gates"
		args.wait_obligation = None
		if wait is not None and wait != "gates":
			args.wait_obligation = _convert(verb, "wait", "int", wait)
	# bootstrap's optional template list: None means "every shipped
	# template" (the established contract).
	if verb == "bootstrap" and not args.templates:
		args.templates = None
	args.command = verb
	return args


def exactly_names(info):
	return set(info.get("exactly-one") or ())


def _partial_tokens(text):
	"""Tokens of a PARTIAL command line under the bar's own execution
	tokenizer (`shlex.split`): the completed tokens exactly as execution
	would receive them, plus the live final token still being typed —
	selected by POSITION (unquoted trailing whitespace ends a token),
	never by object identity. An open quote is tolerated: the live
	token is the honestly-joined quoted text so far, so nothing inside
	it can be mistaken for a key. Returns (completed, live, open_quote),
	or None for a line even the quote rules cannot carry yet (a
	trailing escape)."""
	import shlex
	try:
		tokens = shlex.split(text)
	except ValueError:
		for closer in ('"', "'"):
			try:
				tokens = shlex.split(text + closer)
			except ValueError:
				continue
			return tokens[:-1], tokens[-1], True
		return None
	if not tokens:
		return [], None, False
	if text[-1].isspace():
		return tokens, None, False
	return tokens[:-1], tokens[-1], False


def analyze_partial(buffer: str) -> dict:
	"""W14: pure analysis of a PARTIAL command line against THE one
	declarative specification `_parse_invocation` executes — owned
	here, beside the grammar, so every assistance surface consumes the
	parser's own interpretation instead of approximating it. Reads no
	authority state; converts nothing into effects.

	Returns {"state": ...}:
	- "commands"   {matches}: empty line — every verb;
	- "verbs"      {matches}: a verb prefix — the matching verbs;
	- "values"     {key, values}: live `key=` on a closed vocabulary —
	  the accepted values, narrowed by the typed prefix;
	- "diagnostic" {diagnostic}: malformed, unknown, duplicate, or
	  conflicting input, parser-shaped — from COMPLETED tokens, or from
	  a live token once typing more cannot repair it;
	- "operands"   {verb, heading, required, optional, notes,
	  key_matches}: the EFFECTIVE remaining form — the same
	  exactly-one/when/conditions model the parser enforces, applied
	  to what is already typed (a live `key=value` in progress counts
	  as supplied for display; repeatable keys stay available).
	"""
	text = buffer.lstrip()
	if not text:
		return {"state": "commands", "matches": sorted(GRAMMAR)}
	parts = _partial_tokens(text)
	if parts is None:
		return {"state": "diagnostic",
		        "diagnostic": "open escape; finish the token"}
	completed, live, open_quote = parts
	if not completed:
		if live is None:
			return {"state": "commands", "matches": sorted(GRAMMAR)}
		matches = sorted(name for name in GRAMMAR
		                 if name.startswith(live))
		if matches == [live]:
			completed, live = [live], None
		elif matches:
			return {"state": "verbs", "matches": matches}
		else:
			return {"state": "diagnostic",
			        "diagnostic": "no matching command"}
	verb = completed[0]
	if verb not in GRAMMAR:
		return {"state": "diagnostic",
		        "diagnostic": "no matching command"}
	spec = _verb_spec(verb)
	info = GRAMMAR[verb]
	supplied = {}
	repeated = set()
	for token in completed[1:]:
		key, equals, value = token.partition("=")
		if token.startswith("--"):
			return {"state": "diagnostic", "diagnostic":
			        f"{key!r} is retired flag spelling; operands are "
			        f"key=value"}
		if not equals or not key:
			return {"state": "diagnostic", "diagnostic":
			        f"{token!r} is not a key=value token"}
		if key not in spec:
			return {"state": "diagnostic",
			        "diagnostic": f"unknown key {key!r}"}
		entry = spec[key]
		if entry["values"] is not None and 				value not in entry["values"]:
			return {"state": "diagnostic", "diagnostic":
			        f"{key}= takes one of "
			        f"{', '.join(entry['values'])}"}
		try:
			_convert(verb, key, entry["kind"], value)
		except WorkError as refusal:
			return {"state": "diagnostic",
			        "diagnostic": str(refusal)}
		if entry["repeat"]:
			repeated.add(key)
		elif key in supplied:
			return {"state": "diagnostic", "diagnostic":
			        f"duplicate {key}=; the key is singular"}
		else:
			supplied[key] = value
	exactly = exactly_names(info)
	chosen = [name for name in info.get("exactly-one", ())
	          if name in supplied]
	if len(chosen) > 1:
		return {"state": "diagnostic", "diagnostic":
		        "exactly one of " + " | ".join(
		            name + "=" for name in info["exactly-one"])}
	for rule in info.get("conditions", ()):
		if "exclusive" in rule:
			named = [key for key in rule["exclusive"]
			         if key in supplied]
			if len(named) > 1:
				return {"state": "diagnostic", "diagnostic":
				        "at most one of " + " | ".join(
				            key + "=" for key in rule["exclusive"])}
	# The live token: a key still being typed narrows the display; a
	# `key=value` in progress is diagnosed only once more typing
	# cannot repair it (its KEY is already fixed).
	key_matches = None
	display_supplied = set(supplied)
	if live is not None:
		key, equals, prefix = live.partition("=")
		if equals and key:
			if key not in spec:
				return {"state": "diagnostic",
				        "diagnostic": f"unknown key {key!r}"}
			entry = spec[key]
			if not entry["repeat"] and key in supplied:
				return {"state": "diagnostic", "diagnostic":
				        f"duplicate {key}=; the key is singular"}
			if entry["values"] is not None and not open_quote:
				values = [value for value in entry["values"]
				          if value.startswith(prefix)]
				if not values:
					return {"state": "diagnostic", "diagnostic":
					        f"{key}= takes one of "
					        f"{', '.join(entry['values'])}"}
				return {"state": "values", "key": key,
				        "values": values}
			display_supplied.add(key)
		elif live.startswith("--"):
			return {"state": "diagnostic", "diagnostic":
			        f"{live!r} is retired flag spelling; operands "
			        f"are key=value"}
		else:
			key_matches = sorted(name + "=" for name in spec
			                     if name.startswith(live))
			if not key_matches:
				return {"state": "diagnostic", "diagnostic":
				        f"no {verb} key starts with {live!r}"}
	# The EFFECTIVE form: the parser's own condition model applied to
	# the already-typed keys.
	required = {entry["name"] for entry in spec.values()
	            if entry["required"]}
	required -= exactly
	forbidden = set()
	notes = []
	heading = None
	if exactly:
		if chosen:
			rule = (info.get("when") or {}).get(chosen[0], {})
			required |= set(rule.get("requires", ()))
			forbidden |= set(rule.get("forbids", ()))
			forbidden |= exactly - {chosen[0]}
		else:
			heading = "one of: " + " | ".join(
				name + "=" for name in info["exactly-one"])
	for rule in info.get("conditions", ()):
		if "exclusive" in rule:
			named = [key for key in rule["exclusive"]
			         if key in supplied]
			if named:
				forbidden |= set(rule["exclusive"]) - set(named)
		elif "if-value" in rule:
			key, value = rule["if-value"]
			if supplied.get(key) == value:
				required |= set(rule["requires"])
		elif "unless-value" in rule:
			key, value = rule["unless-value"]
			if supplied.get(key) != value:
				forbidden |= set(rule["forbids"])
		elif "if-key" in rule:
			key = rule["if-key"]
			if key in supplied or key in repeated:
				required |= set(rule.get("requires", ()))
				group = rule.get("requires-any")
				if group and not any(name in supplied
				                     for name in group):
					notes.append(f"{key}= needs " + " or ".join(
						name + "=" for name in group))
				if rule.get("requires-value"):
					vkey, vvalue = rule["requires-value"]
					if supplied.get(vkey) != vvalue:
						notes.append(
							f"{key}= needs {vkey}={vvalue}")
	# A key whose own requirement is already excluded can never be
	# satisfied on this form — the parser would refuse the
	# combination, so the assist stops offering it.
	for rule in info.get("conditions", ()):
		if "if-key" in rule and \
				set(rule.get("requires", ())) & forbidden:
			forbidden.add(rule["if-key"])
	remaining = sorted(
		name + "=" for name in required - forbidden
		if name not in display_supplied and name not in repeated)
	optional = sorted(
		entry["name"] + "=" for entry in spec.values()
		if not entry["required"]
		and entry["name"] not in required
		and entry["name"] not in forbidden
		and entry["name"] not in exactly
		and entry["name"] not in display_supplied)
	return {"state": "operands", "verb": verb, "heading": heading,
	        "required": remaining, "optional": optional,
	        "notes": notes, "key_matches": key_matches}


def main(argv=None) -> int:
	if argv is None:
		import sys as _sys
		argv = _sys.argv[1:]
	try:
		args = _parse_invocation(argv)
	except WorkError as refusal:
		print(json.dumps({"error": str(refusal)}), file=sys.stderr)
		return 1
	if args.command == "--help":
		try:
			print(render_help(args.help_verb), end="")
		except WorkError as refusal:
			print(json.dumps({"error": str(refusal)}), file=sys.stderr)
			return 1
		return 0
	try:
		jsonapi.require_version(args.expect_projection)
		mutations = set(MUTATIONS)
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
		if args.op_id is not None and args.command not in mutations:
			raise WorkError(
				f"{args.command} is a pure read and takes no operation "
				f"identity; op-id= protects mutations only (WS-5)")
		if args.refs and args.command not in mutations:
			raise WorkError(
				f"{args.command} is a pure read and carries no asset "
				f"references; ref= commits with a mutation (WS-6)")
		if args.answer_refs and args.command != "accept":
			raise WorkError(
				"answer-ref= is accept's explicit compound placement; "
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
			# W4: the root base comes from the ACCEPTED configuration —
			# bootstrap binds to the instance like every other command.
			from baton_work import project
			if not args.config:
				raise WorkError("bootstrap resolves its root through "
				                "the accepted baton.json; --config is "
				                "required")
			boot_store = lifecycle.open_bound(args.config)
			try:
				base = project.store_root_base(boot_store, args.root)
			finally:
				boot_store.close()
			result = project.bootstrap_project(
				args.root, base,
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
				import math
				if not (math.isfinite(args.refresh) and
				        0 < args.refresh <= 86400):
					raise WorkError(
						"tui refresh= takes a finite positive "
						"number of seconds (at most 86400); "
						"automatic refresh cannot be disabled, "
						"negative, or unrepresentable")
				from baton_work.tui import run as tui_run
				import curses
				curses.wrapper(tui_run, store,
				               *_participant(args.participant),
				               config_path=args.config,
				               refresh=args.refresh)
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
		create_only = {"kind=": args.kind, "title=": args.title,
		               "classification=": args.classification,
		               "phase=": args.phase, "parent=": args.parent}
		if not args.create:
			# R50: the forms fail CLOSED — an into= acceptance must not
			# silently ignore creation keys a typo supplied.
			stray = [flag for flag, value in create_only.items()
			         if value is not None]
			if stray:
				raise WorkError(
					f"accept into= takes no creation key; remove "
					f"{', '.join(stray)} or use create=true")
		create = None
		if args.create:
			if args.kind is None or args.title is None:
				raise WorkError("accept create=true requires kind= and "
				                "title=")
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
			base = project.store_root_base(store, binding["root"])
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
		# W4: the accepted authority IS the one root catalog — the
		# base rides the same live row.
		base = project.store_root_base(store, left)
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
	if command == "start-thread":
		team, member = _need_participant(args)
		return transitions.create_thread(
			store, actor_team=team, actor=member, body=args.body,
			labels=args.label, subject=args.subject, op_id=args.op_id,
			refs=args.refs or ())
	if command == "say":
		team, member = _need_participant(args)
		return transitions.post_thread(
			store, args.thread, author_team=team, author=member,
			body=args.body, include=args.include or (),
			request=args.request, pass_to=args.pass_to,
			pass_phase=args.pass_phase,
			set_next=args.set_next, on=args.on, op_id=args.op_id,
			refs=args.refs or ())
	if command == "label":
		team, member = _need_participant(args)
		return transitions.label_thread(
			store, args.thread, args.work, actor_team=team,
			actor=member, op_id=args.op_id,
			refs=args.refs or ())
	if command == "unlabel":
		team, member = _need_participant(args)
		return transitions.unlabel_thread(
			store, args.thread, args.work, actor_team=team,
			actor=member, op_id=args.op_id,
			refs=args.refs or ())
	if command == "thread":
		team, member = _need_participant(args)
		return projection.thread(store, args.thread,
		                         viewer_team=team, viewer_member=member,
		                         after=args.after, limit=args.limit)
	if command == "threads":
		team, member = _need_participant(args)
		return projection.threads_for(store, viewer_team=team,
		                                  viewer_member=member,
		                                  after=args.after,
		                                  limit=args.limit)
	if command == "work-threads":
		team, member = _need_participant(args)
		return projection.work_threads(store, args.work,
		                                   viewer_team=team,
		                                   viewer_member=member,
		                                   after=args.after,
		                                   limit=args.limit)
	if command == "mark-seen":
		# R61: the ONE explicit public seen mutation, thread-scoped.
		# Reads (thread/detail/list) are byte-pure; nothing named like a
		# read may write.
		team, member = _need_participant(args)
		return transitions.seen_thread(
			store, args.thread, team=team, member=member,
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
	if command == "claim":
		team, member = _need_participant(args)
		return transitions.claim_work(store, args.work, actor_team=team,
		                              actor=member, op_id=args.op_id,
		                              refs=args.refs or ())
	if command == "release":
		team, member = _need_participant(args)
		return transitions.release_claim(
			store, args.work, actor_team=team, actor=member,
			expect=args.expect, reason=args.reason, op_id=args.op_id,
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
	if command == "tree":
		team, member = _need_participant(args)
		return projection.tree(store, args.work, viewer_team=team,
		                       viewer_member=member)
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
