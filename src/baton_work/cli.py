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
from baton_work import config, jsonapi, lifecycle, projection, transitions


# The public MUTATING verbs — shared with the console's command bar so
# only a successful workflow act (never a refused command or pure read)
# refreshes the cached projection (W5 R2). `bind` joins below as it
# always has.
MUTATIONS = frozenset({
	"activate", "regen", "create", "accept", "respond", "dispose",
	"close", "block", "unblock", "mark-seen", "classify", "claim", "release",
	"prioritize", "pass", "heartbeat",
	"phase", "try",
	"extend", "report", "assess", "abandon", "revise", "start-thread",
	"say", "label", "unlabel", "bind",
	# W5: conversational, carrying no workflow authority — but they DO
	# write, so the console must refresh after them like any mutation.
	"poke", "poke-answer", "poke-cancel", "reroute",
	# W93: runtime reports WRITE, so a console refreshes after them —
	# but they carry no workflow authority whatsoever.
	"runtime-start", "runtime-state", "runtime-end",
	"runtime-facts", "runtime-refresh",
	# W415: a durable managed-turn incident and its authoritative
	# dismissal. Both WRITE; neither carries workflow authority.
	"incident", "dismiss",
	# W4615: deployment-global maintenance control. These WRITE the
	# dispatch singleton and carry no Work authority at all — no Work
	# row changes when the deployment drains.
	"drain", "resume"})

# W5: the closed answer vocabularies, shared by the generated help and
# the transition layer. `unknown` leads each diagnostic vocabulary
# because it is the honest default for an adapter that cannot observe
# the fact, not a fallback for one that did not try.
_POKE_STATES = ("idle", "working", "waiting", "needs-help")
# W93: the runner vocabularies, shared with the transition layer so the
# generated help and the refusals can never drift apart.
from baton_work.transitions import (INCIDENT_CATEGORIES
                                        as _INCIDENT_CATEGORIES,
                                    RUNTIME_CAUSES as _RUNTIME_CAUSES,
                                    RUNTIME_SOURCES as _RUNTIME_SOURCES,
                                    RUNTIME_STATES as _RUNTIME_STATES)
_POKE_SESSION_STATES = ("unknown", "live", "starting", "stopped", "failed")
_POKE_AUTH_STATES = ("unknown", "ok", "expired", "failed")
_POKE_LIMIT_STATES = ("unknown", "ok", "rate-limited", "overloaded")


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
# W38: the closed scheduler axis. All four are FILTERABLE — asking to
# see what is running is an ordinary question — but only three are
# SETTABLE, because `active` is established by claiming, not by asking.
_PHASES = ("queued", "active", "block", "parked")
_SETTABLE_PHASES = ("queued", "block", "parked")
_OUTCOMES = ("satisfying", "non-satisfying", "rejected", "cancelled")
_PRIORITIES = ("high", "normal", "low")
# W24755: JSON stays the default so existing automation keeps reading the
# ordinary envelope; DOT is the ONE deliberate raw-stdout exception and has to
# be asked for by name.
_GRAPH_FORMATS = ("json", "dot")


def _filter_keys():
	"""W5: the ONE shared filter vocabulary — identical operands on
	home, tree, tui, and the console-local filter command."""
	return (_key("team", help="owning team handle"),
	        _key("status", values=("open", "closed"),
	             help="work lifecycle status"),
	        _key("phase", values=_PHASES,
	             help="operational phase (closed selects through "
	             "status=closed)"),
	        _key("route", help="canonical TEAM.KIND endpoint whose "
	             "handlers may claim, or me (the viewer resolves as a "
	             "handler)"),
	        _key("handler", help="the exact TEAM.MEMBER holding the "
	             "claim, or me (the viewer holds it); unclaimed work "
	             "matches neither"),
	        _key("category", values=_CLASSIFICATIONS,
	             help="canonical classification (compact display "
	             "labels are refused)"),
	        _key("ready", values=("true", "false"),
	             help="dependency readiness"),
	        _key("new", values=("true", "false"),
	             help="the viewer's personal New count is nonzero"),
	        _key("priority", values=_PRIORITIES,
	             help="the owning team's priority"))


def _filter_operands(args):
	active = {}
	for name in ("team", "status", "phase", "route", "handler", "category",
	             "ready", "new", "priority"):
		value = getattr(args, name, None)
		if value is not None:
			active[name] = value
	return active or None
_ASSESSMENTS = ("accepted", "rejected", "inconclusive")


def _key(name, dest=None, *, required=False, repeat=False, kind="str",
         default=None, values=None, prose=False, help=""):
	"""One operand of the ONE declarative grammar.

	W36 adds `prose`: this operand carries durable human prose an
	operator may want to author in a real editor rather than quote into
	a single terminal row. It is GRAMMAR METADATA and nothing else —
	the CLI's parsing, refusals and help are untouched by it, and no
	caller is obliged to do anything with it. The TUI reads it to decide
	when Enter opens an editor instead of returning a bare
	missing-operand refusal; a separate hard-coded verb list would have
	drifted from the grammar the parser actually executes, which is the
	failure this flag exists to prevent."""
	return {"name": name, "dest": dest or name.replace("-", "_"),
	        "required": required, "repeat": repeat, "kind": kind,
	        "default": default, "values": values, "prose": prose,
	        "help": help}


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
	"instructions": {"help": "resolve this participant's durable role instructions for an agent launcher",
	                 "keys": (_key("role", required=True,
	                               help="the held role to launch in; always explicit, so a later second role cannot silently change the session's persona"),)},
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
	                    _key("body", prose=True, required=True,
	                         help="the first message body"),
	                    _key("parent", help="containing open Work id"),
	                    _key("classification", required=True,
	                         values=_CREATION_CLASSIFICATIONS,
	                         help="the submitter's concrete "
	                         "classification; 'unknown' refuses"),
	                    _key("priority", values=_PRIORITIES,
	                         help="the owning team's ordering signal; "
	                         "defaults to normal"),
	                    _key("follow-up-of",
	                         help="CLOSED Work this follows up"),
	                    _key("binding",
	                         help="atomic creation binding ROOT_ID:"
	                         "work/records/YYYY/MM/<record>"
	                         "[/findings/<child>"
	                         "[/findings/<grandchild>]]"))},
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
	                    _key("body", prose=True, required=True,
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
	                    _key("parent", help="provider parent Work"))},
	"respond": {"help": "answer an @ obligation with a message",
	            "keys": (_key("obligation", required=True, kind="int",
	                          help="the pending obligation seq"),
	                     _key("body", prose=True, required=True,
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
	                   _key("rationale", prose=True, required=True,
	                        help="durable terminal rationale"),
	                   _key("outcome", required=True, values=_OUTCOMES,
	                        help="the terminal outcome"),
	                   _key("duplicate-of",
	                        help="surviving Work id for a duplicate "
	                        "rejection"))},
	"claim": {"help": "atomically claim open ready Work as its one "
	          "active executor — the claim IS the phase: it records the "
	          "Handler and moves the Work to `active` in the same "
	          "transaction, and only claiming reaches that phase (W38)",
	          "keys": (_key("work", required=True,
	                        help="the Work to claim"),)},
	"release": {"help": "release/recover the active claim (a Route "
	            "handler, or an owning-team `recover` operator) with an "
	            "exact claimant + assignment-episode compare-and-swap "
	            "(W4303)",
	            "keys": (_key("work", required=True, help="the Work id"),
	                     _key("expect", required=True,
	                          help="the exact recorded claimant "
	                          "team.member"),
	                     _key("episode", required=True, kind="int",
	                          help="the exact assignment episode that "
	                          "claim was offered under; a stale request "
	                          "never releases a later claim by the same "
	                          "participant"),
	                     _key("reason", prose=True, required=True,
	                          help="durable reason the Work became "
	                          "unclaimed"))},
	"block": {"help": "record a dependency edge (work waits on blocker)",
	          "keys": (_key("work", required=True,
	                        help="the consumer Work"),
	                   _key("on", required=True,
	                        help="the blocker Work"),
	                   _key("rationale", prose=True, required=True,
	                        help="durable reason this gate is required"))},
	"unblock": {"help": "correct one live dependency edge without "
	            "closing either Work",
	            "keys": (_key("work", required=True,
	                          help="the consumer Work"),
	                     _key("on", required=True,
	                          help="the blocker Work"),
	                     _key("rationale", prose=True, required=True,
	                          help="durable reason the edge was wrong"))},
	"mark-seen": {"help": "mark a thread page seen up to a message",
	              "keys": (_key("thread", required=True,
	                            help="the thread id"),
	                       _key("up-to", required=True, kind="int",
	                            help="last seen message seq"))},
	"heartbeat": {"help": "the current claimant's deliberate liveness "
	              "beat (informational; never releases or transfers)",
	              "keys": (_key("work", required=True,
	                            help="the claimed Work"),)},
	"poke": {"help": "ask exactly one participant what is going on "
	         "(conversational; carries no workflow authority)",
	         "keys": (_key("target", required=True,
	                       help="the exact TEAM.MEMBER to ask; never a "
	                       "route or a wildcard, and may be yourself"),
	                  _key("request",
	                       help="the friendly question (default: "
	                       "\"what's up?\")"),
	                  _key("expires-at",
	                       help="optional canonical UTC instant after "
	                       "which the poke is terminally timed-out; "
	                       "omit to leave it pending until answered "
	                       "or cancelled"))},
	"poke-answer": {"help": "answer a poke addressed to you — the one "
	                "terminal response",
	                "keys": (_key("poke", required=True, kind="int",
	                              help="the poke sequence"),
	                         _key("state", required=True,
	                              values=_POKE_STATES,
	                              help="your own status"),
	                         _key("explanation", required=True,
	                              help="a short human explanation"),
	                         _key("work", repeat=True,
	                              help="a Work you believe you are "
	                              "handling (repeatable); canonical "
	                              "state is reported beside your "
	                              "claim, never instead of it"),
	                         _key("provider",
	                              help="runner/provider name, or omit "
	                              "for unknown"),
	                         _key("model",
	                              help="model name, or omit for "
	                              "unknown"),
	                         _key("session-state",
	                              values=_POKE_SESSION_STATES,
	                              help="runner session state"),
	                         _key("auth-state",
	                              values=_POKE_AUTH_STATES,
	                              help="provider authentication state"),
	                         _key("limit-state",
	                              values=_POKE_LIMIT_STATES,
	                              help="provider rate-limit/overload "
	                              "state"),
	                         _key("retry-at",
	                              help="canonical UTC instant the "
	                              "provider says to retry or reset"),
	                         _key("context-limit", kind="int",
	                              help="advisory context/token limit; "
	                              "omit to report it unknown"),
	                         _key("context-used", kind="int",
	                              help="advisory context/token usage; "
	                              "omit to report it unknown"),
	                         _key("context-remaining", kind="int",
	                              help="advisory context/token "
	                              "remaining; omit to report it "
	                              "unknown"))},
	"poke-cancel": {"help": "withdraw an unanswered poke (the asker, or "
	                "a config-capability holder)",
	                "keys": (_key("poke", required=True, kind="int",
	                              help="the poke sequence"),
	                         _key("reason", prose=True,
	                              help="durable reason it was "
	                              "withdrawn"))},
	"pokes": {"help": "conversational pokes and their answers, with "
	          "canonical state beside every agent claim",
	          "keys": (_key("asker", help="narrow to one asking "
	                        "TEAM.MEMBER"),
	                   _key("target", help="narrow to one asked "
	                        "TEAM.MEMBER"),
	                   _key("after", kind="int", default=0,
	                        help="page after this poke sequence"),
	                   _key("limit", kind="int", default=100,
	                        help="page size"))},
	"prioritize": {"help": "revise the owning team's Work priority "
	               "(ordering signal only)",
	               "keys": (_key("work", required=True,
	                             help="the Work id"),
	                        _key("as", dest="priority", required=True,
	                             values=_PRIORITIES,
	                             help="the canonical priority"))},
	"classify": {"help": "reclassify Work (Route handler authority)",
	             "keys": (_key("work", required=True,
	                           help="the Work id"),
	                      _key("as", dest="classification",
	                           required=True, values=_CLASSIFICATIONS,
	                           help="the canonical classification"))},
	"phase": {"help": "move Work to another operational phase",
	          "conditions": (
	              {"if-value": ("to", "parked"),
	               "requires": ("reason",)},
	              {"if-value": ("to", "block"), "requires": ("wait",)},
	              {"unless-value": ("to", "block"),
	               "forbids": ("wait",)}),
	          "keys": (_key("work", required=True, help="the Work id"),
	                   _key("to", dest="phase", required=True,
	                        values=_SETTABLE_PHASES,
	                        help="the target phase; `active` is not "
	                             "settable — claim the Work instead"),
	                   _key("reason", prose=True, help="required when parking"),
	                   _key("wait", help="the gate: gates, or "
	                        "one pending obligation seq (block "
	                        "only)"))},
	"try": {"help": "ask the assigned endpoints to TRY one exact candidate — opens a trial",
	          "keys": (_key("work", required=True, help="the Work id"),
	                   _key("candidate", required=True,
	                        help="the candidate under verification"),
	                   _key("assign", repeat=True, required=True,
	                        help="verifying endpoint (repeatable)"),
	                   _key("review-at",
	                        help="canonical UTC review instant"))},
	"extend": {"help": "extend an open trial's review instant",
	           "keys": (_key("work", required=True, help="the Work id"),
	                    _key("trial", required=True, kind="int",
	                         help="the trial number"),
	                    _key("review-at", required=True,
	                         help="the new canonical UTC instant"))},
	"report": {"help": "file a verification report",
	           "keys": (_key("obligation", required=True, kind="int",
	                         help="the verification assignment seq"),
	                    _key("observation", prose=True, required=True,
	                         help="what was observed"),
	                    _key("evidence", required=True,
	                         help="where the evidence lives"))},
	"assess": {"help": "assess a verification report",
	           "keys": (_key("obligation", required=True, kind="int",
	                         help="the reported assignment seq"),
	                    _key("as", dest="assessment", required=True,
	                         values=_ASSESSMENTS,
	                         help="the assessment"),
	                    _key("rationale", prose=True, required=True,
	                         help="why this assessment"))},
	"abandon": {"help": "abandon an open verification trial",
	            "keys": (_key("work", required=True,
	                          help="the Work id"),
	                     _key("trial", required=True, kind="int",
	                          help="the trial number"),
	                     _key("reason", prose=True, required=True,
	                          help="why the trial ends unresolved"))},
	"home": {"help": "the team summary and root Work rows",
	         "keys": _filter_keys()},
	# W29146: the help already said team-scoped; the RESULT now says it
	# too, so a client does not have to have read this line to know what an
	# empty answer means.
	"search": {"help": "read-only Work search scoped to your own team, "
	           "which the result names as `team` (title substring; id "
	           "exact/prefix)",
	           "keys": (_key("query", required=True,
	                         help="case-folded title substring, or a "
	                         "canonical/local Work id prefix"),
	                    _key("after", kind="int", default=0,
	                         help="page after this continuation "
	                         "cursor"),
	                    _key("limit", kind="int", default=100,
	                         help="page size (1..500)"))
	                   + _filter_keys()},
	"tree": {"help": "the canonical bounded tree window (one snapshot)",
	         "keys": (_key("work", help="optional re-root Work id"),)
	                 + _filter_keys()},
	"filter": {"help": "the console-local view filter (TUI command "
	           "mode; bare filter clears)",
	           "keys": _filter_keys()},
	"obligations": {"help": "the team's pending @ obligations",
	                "keys": ()},
	# W25: the two participant-relative surfaces the console's Teams and
	# Inbox tabs render. They are verbs rather than console-only reads
	# because the TUI is ONE projection of the model and not its only
	# interface — an agent derives the same counts, owed-action state and
	# navigation targets from these, in typed fields rather than glyphs.
	"teams": {"help": "the operational roster: configured members, their "
	          "route coverage, the Work they hold, and the runner status "
	          "each last reported",
	          "keys": ()},
	"inbox": {"help": "this participant's owed actions and unseen "
	          "attention, with total/unseen/owed counters",
	          "keys": ()},
	# W415: what FAILED and still needs an operator, which is a
	# different question from what a runner is doing now. An incident
	# survives the runner returning to idle, a restart, and a refresh.
	"drain": {"help": "suspend managed dispatch deployment-wide: claims "
	          "live at this boundary finish normally, no new claim is "
	          "admitted, and the deployment reaches `paused` when the "
	          "last one ends (requires the accepted `dispatch` "
	          "capability)",
	          "keys": (_key("reason", prose=True,
	                        help="durable note recorded in the global "
	                             "control journal"),)},
	"resume": {"help": "return the deployment to ordinary dispatch "
	           "(requires the accepted `dispatch` capability)",
	           "keys": (_key("reason", prose=True,
	                         help="durable note recorded in the global "
	                              "control journal"),)},
	"dispatch": {"help": "the deployment-global dispatch state: mode, "
	             "control generation, boundary, actor, and the exact "
	             "claims still preventing `paused` — readable by every "
	             "accepted participant",
	             "keys": (_key("history", kind="bool", default=False,
	                           help="the global control journal instead "
	                                "of the current state"),
	                      _key("limit", kind="int",
	                           help="control-journal page size"),
	                      _key("before", kind="int",
	                           help="page before this control sequence"))},
	"incidents": {"help": "durable managed-turn incidents awaiting an "
	              "action owner; open by default",
	              "keys": (_key("include-dismissed", kind="bool", default=False,
	                            help="also show dismissed history, so a "
	                                 "recurrence after a dismissal is "
	                                 "visible as one"),)},
	"incident": {"help": "file (or coalesce into) one durable incident "
	             "for a managed turn that could not complete; owed to "
	             "the runner's CONFIGURED action owner, and carrying no "
	             "workflow authority",
	             "keys": (_key("incarnation", required=True,
	                           help="the lease this runner holds"),
	                      _key("cause", required=True,
	                           values=_RUNTIME_CAUSES,
	                           help="closed machine category, shared "
	                           "with the runtime vocabulary"),
	                      _key("category", required=True,
	                           values=_INCIDENT_CATEGORIES,
	                           help="the SAFE command category; the "
	                           "command body is never stored"),
	                      _key("detail",
	                           help="a short safe explanation, with no "
	                           "command body, credential or environment "
	                           "value in it"),
	                      _key("work",
	                           help="the Work this failure interrupted; "
	                           "correlation only, never a claim"),
	                      _key("episode", kind="int",
	                           help="the assignment episode"),
	                      _key("action-key",
	                           help="the exact readiness episode key"),
	                      _key("session",
	                           help="the live session locator"))},
	"dismiss": {"help": "the action owner's authoritative, journaled "
	            "dismissal of one incident; it closes the incident and "
	            "mutates no Work",
	            "keys": (_key("incident", required=True, kind="int",
	                          help="the incident id"),
	                     _key("note",
	                          help="what was done about it, for the "
	                          "next reader"))},
	# W93: the participant RUNTIME lease. A runner publishes about
	# itself; the acting participant is always the subject, so no
	# capability question arises and no participant can narrate
	# another's runtime.
	# W128: the owning team's correction for work nobody has taken.
	"reroute": {"help": "move OPEN, UNCLAIMED Work to another endpoint "
	            "or configured alternate route, on the owning team's "
	            "authority rather than the resolved route handler's — "
	            "the one operation for work nobody holds, since W2571 "
	            "requires a pass to release the actor's own claim; it "
	            "corrects WHERE and never whether the Work may run, so "
	            "a gated Work stays blocked and a parked one stays "
	            "parked (W2645)",
	            "keys": (_key("work", required=True,
	                          help="the unclaimed Work"),
	                     _key("to", required=True,
	                          help="ONE destination endpoint team.kind"),
	                     _key("route",
	                          help="explicitly select one of the "
	                          "destination endpoint's configured "
	                          "routes; omitted resolves to the "
	                          "endpoint's default"),
	                     _key("reason", prose=True, required=True,
	                          help="durable reason the Work is being "
	                          "moved"))},
	"runtime-start": {"help": "open this participant's runtime lease, "
	                  "superseding any previous incarnation",
	                  "keys": (_key("incarnation", required=True,
	                                help="the runner's opaque identity "
	                                "for THIS launch"),
	                           _key("adapter", required=True,
	                                help="the runner family (codex, "
	                                "acp, ...); never inferred from the "
	                                "participant name"),
	                           _key("provider", help="provider name"),
	                           _key("model", help="model name"),
	                           _key("session",
	                                help="the exact session locator, in "
	                                "full"),
	                           _key("expires-at",
	                                help="the lease deadline past which "
	                                "reads derive `unknown`; omitted "
	                                "takes the configured duration, "
	                                "because a lease is always "
	                                "bounded"),
	                           _key("action-owner",
	                                help="TEAM.MEMBER who owes this "
	                                "runner's interactive answers"),
	                           _key("rationale", prose=True,
	                                help="why this launch replaces the "
	                                "previous lease; required when one "
	                                "exists, and read back through "
	                                "runtime-history"))},
	"runtime-state": {"help": "publish one explicit runtime transition "
	                  "on this participant's live lease",
	                  "keys": (_key("incarnation", required=True,
	                                help="the lease this runner holds"),
	                           _key("state", required=True,
	                                values=_RUNTIME_STATES,
	                                help="the semantic runner state; "
	                                "`offline`/`unknown` are DERIVED "
	                                "and never published"),
	                           _key("cause", values=_RUNTIME_CAUSES,
	                                help="closed machine category, "
	                                "required for waiting-input; it is "
	                                "not `reason=`, which is durable "
	                                "human prose everywhere else"),
	                           _key("detail",
	                                help="a short safe explanation; "
	                                "published by the adapter, so it is "
	                                "not editor-authored prose"),
	                           _key("work",
	                                help="the Work this runner believes "
	                                "it is serving; correlation only, "
	                                "never a claim"),
	                           _key("episode", kind="int",
	                                help="the assignment episode"),
	                           _key("session",
	                                help="a new session locator, for a "
	                                "reconnect"),
	                           _key("expires-at",
	                                help="a new lease deadline"))},
	"runtime-end": {"help": "close this participant's runtime lease "
	                "explicitly; reads then report offline as reported",
	                "keys": (_key("incarnation", required=True,
	                              help="the lease this runner holds"),
	                         _key("cause", values=_RUNTIME_CAUSES,
	                              help="closed machine category"),
	                         _key("detail",
	                              help="a short safe explanation; "
	                              "published by the adapter, so it is "
	                              "not editor-authored prose"))},
	# W93 slice 6: the safe operational inventory, and the cheap ask for
	# a fresh one. The key set is CLOSED — that is the redaction
	# boundary made structural, not a convenience.
	"runtime-facts": {"help": "publish this runner's safe operational "
	                  "inventory; every fact carries its source and the "
	                  "instant it was observed",
	                  "keys": (_key("incarnation", required=True,
	                                help="the lease this runner holds"),
	                           _key("source", values=_RUNTIME_SOURCES,
	                                default="reported",
	                                help="configured, reported or "
	                                "derived — a reader never guesses"),
	                           _key("observed-at",
	                                help="the ADAPTER's instant for "
	                                "these facts; omitted means now, "
	                                "and commit time is never used "
	                                "because these writes queue"),
	                           _key("answers", kind="int",
	                                help="the refresh generation this "
	                                "publication responds to; omitted "
	                                "means it answers no request and "
	                                "clears none"),
	                           _key("service",
	                                help="the process or service "
	                                "identity running this runner"),
	                           _key("dispatcher",
	                                help="the dispatcher target this "
	                                "runner is driven through"),
	                           _key("readiness",
	                                help="the readiness path it polls"),
	                           _key("workdir",
	                                help="the working directory or root "
	                                "it operates in"),
	                           _key("log",
	                                help="the configured log locator"),
	                           _key("version",
	                                help="the adapter or runner "
	                                "version"),
	                           _key("retry-at",
	                                help="the instant the provider says "
	                                "to retry or reset"))},
	"runtime-refresh": {"help": "ask one participant's ADAPTER for "
	                    "fresh machine facts; runs nothing and never "
	                    "wakes a model",
	                    "keys": (_key("target", required=True,
	                                  help="the exact TEAM.MEMBER whose "
	                                  "adapter is asked"),)},
	"runtime": {"help": "every configured participant's runtime state "
	            "beside the Work the authority says they hold",
	            "keys": ()},
	"runtime-history": {"help": "one participant's append-only runtime "
	                    "journal",
	                    "keys": (_key("participant", required=True,
	                                  help="the TEAM.MEMBER"),
	                             _key("after", kind="int", default=0,
	                                  help="page after this seq"),
	                             _key("limit", kind="int", default=100,
	                                  help="page size"))},
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
	# W26328: the flattened view the bounded tree cannot answer. `tree` stops
	# at three containment levels and `search` needs a query and only reaches
	# the viewer's own team, so a queued Work this participant may claim --
	# nested deeper, or owned by another team -- had no locator anywhere.
	"actionable-work": {"help": "every Work awaiting this participant, "
	                            "flattened, with complete breadcrumbs",
	                    # W26328 [P1]: the continuation is a STRING and the
	                    # CLI is a pass-through. It used to be declared an
	                    # integer, which both invited `after=25` arithmetic
	                    # and made the grammar itself a place the opaque
	                    # contract could be contradicted.
	                    "keys": (_key("after",
	                                  help="opaque continuation token from "
	                                       "a previous page's next_after; "
	                                       "pass it back unchanged, and only "
	                                       "to the same participant view "
	                                       "that produced it"),
	                             _key("limit", kind="int", default=100,
	                                  help="page size, 1..500"))},
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
	                       "YYYY/MM/<record>[/findings/<child>"
	                       "[/findings/<grandchild>]]"),
	                  _key("expect", dest="expected_revision",
	                       required=True, kind="int",
	                       help="the expected prior binding revision"),
	                  _key("rationale", prose=True, required=True,
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
	# W288: the precondition an operator cannot otherwise discover —
	# eligibility through the route is NOT enough, because a peer would
	# then rewrite scope underneath whoever is executing the Work.
	"revise": {"help": "promote one durable message as the complete "
	           "Work contract (compare-and-swap); only the exact "
	           "current claimant, still eligible through the Work's "
	           "route, may promote it — claim first, and unclaimed "
	           "Work refuses",
	           "keys": (_key("work", required=True,
	                         help="the Work id; you must hold its "
	                              "current claim"),
	                    _key("message", dest="message_seq",
	                         required=True, kind="int",
	                         help="the message promoted as the "
	                         "contract"),
	                    _key("expect", dest="expected_revision",
	                         required=True, kind="int",
	                         help="the expected prior revision"),
	                    _key("rationale", prose=True, required=True,
	                         help="why this promotion is the agreed "
	                         "contract"))},
	"start-thread": {"help": "open a labelled thread with its first "
	                 "message",
	                 "keys": (_key("subject", required=True,
	                               help="the thread subject"),
	                          _key("body", prose=True, required=True,
	                               help="the first message body"),
	                          _key("label", repeat=True, required=True,
	                               help="Work id to label "
	                               "(repeatable)"))},
	"say": {"help": "post one discussion message, optionally with an "
	        "@ request",
	        "conditions": (
	            {"if-key": "on", "requires": ("request",)},
	            # W159: `wait=` says whether a directed request blocks
	            # the Work it acts on, so it is meaningless without one.
	            {"if-key": "wait", "requires": ("request",)},),
	        "keys": (_key("thread", required=True,
	                      help="the thread id"),
	                 _key("body", prose=True, required=True,
	                      help="the message body"),
	                 _key("include", help="attention fan-out list/"
	                      "wildcards"),
	                 _key("request", help="ONE endpoint owing a "
	                      "response (acts on on=)"),
	                 _key("on", help="the labelled open Work an @ "
	                      "acts against"),
	                 _key("wait", dest="say_wait", kind="boolean",
	                      values=("true", "false"),
	                      help="whether the directed request BLOCKS the "
	                      "selected Work (default true with request=; "
	                      "wait=false is the explicit asynchronous "
	                      "override)"))},
	"pass": {"help": "hand on the Work baton YOU HOLD: handoff "
	         "evidence, Route, and the ROUTE-DERIVED destination phase "
	         "in ONE atomic THREADLESS Work event (W2571: the actor "
	         "must be the current claimant — claim it first, or use "
	         "reroute to move unclaimed Work on the owning team's "
	         "authority; W171: no thread, no message, no count moves; "
	         "W73: the destination route decides the phase, so phase= "
	         "is refused as unknown)",
	         "keys": (_key("work", required=True,
	                       help="the Work whose baton moves; you must "
	                       "be its current claimant"),
	                  _key("to", required=True,
	                       help="ONE destination endpoint team.kind"),
	                  _key("comment", prose=True, required=True,
	                       help="durable handoff evidence stored with "
	                       "the authoritative pass event — never a "
	                       "discussion message"),
	                  _key("route", help="W230: explicitly select one of "
	                       "the destination endpoint's configured routes; "
	                       "omitted always resolves to the endpoint's "
	                       "deterministic default, and Baton never "
	                       "selects an alternate on your behalf"),
	                  _key("set-next", help="planned return "
	                       "endpoint"))},
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
	"work-events": {"help": "one Work's append-only operational "
	                "journal — the play-by-play of what happened to it "
	                "and why, with typed roles, related Work, and claim "
	                "intervals",
	                "keys": (_key("work", required=True,
	                              help="the Work id"),
	                         _key("after", kind="int", default=0,
	                              help="page after this event seq"),
	                         _key("before", kind="int",
	                              help="page immediately OLDER than "
	                              "this event seq"),
	                         _key("newest", kind="bool",
	                              help="open the newest page (value: "
	                              "true)"),
	                         _key("limit", kind="int", default=200,
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
	# W24755: the portable Work-graph export. `team=` and `status=` here are
	# GRAPH SCOPE, not the participant-relative `home`/`tree` filter grammar --
	# they are deliberately not `_filter_keys()`, because this verb answers a
	# question about the authority's graph rather than about one viewer's
	# view, and reusing that grammar would import `route=me` and the rest of a
	# vocabulary that has no meaning for an export.
	"work-graph": {"help": "the complete current Work graph, one snapshot, "
	                       "as JSON or portable Graphviz DOT",
	               "keys": (_key("format", default="json",
	                             values=_GRAPH_FORMATS,
	                             help="json (the ordinary envelope) or dot "
	                                  "(raw DOT on stdout, for `> work.dot`)"),
	                        _key("status", default="open",
	                             values=projection.GRAPH_STATUSES,
	                             help="graph scope by Work status; the "
	                                  "default is the current operational "
	                                  "graph"),
	                        _key("team",
	                             help="graph scope by owning team; the "
	                                  "default is every team"),
	                        _key("changed-from",
	                             help="inclusive RFC 3339 lower bound on "
	                                  "last_changed_at; required with "
	                                  "status=all"),
	                        _key("changed-until",
	                             help="exclusive RFC 3339 upper bound on "
	                                  "last_changed_at; required with "
	                                  "status=all"))},
	"tui": {"help": "the curses console on this instance",
	        "keys": (_key("refresh", kind="float", default=2.0,
	                      help="auto-refresh seconds (positive)"),)
	                + _filter_keys()},
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
	if kind == "boolean":
		# W159: a genuine two-valued operand, distinct from the
		# true-only FLAG above. `wait=false` has to be sayable, while
		# `create=false` on accept must stay meaningless — so the two
		# kinds are deliberately separate rather than one loosened one.
		if value not in ("true", "false"):
			raise WorkError(f"{verb}: {name}= takes exactly true or "
			                f"false; got {value!r}")
		return value == "true"
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
		if "if-key" not in rule:
			continue
		needs = set(rule.get("requires", ()))
		if needs & forbidden:
			forbidden.add(rule["if-key"])
		elif needs and not needs <= display_supplied:
			# W159 R4: a conditional key is not OFFERED until what it
			# depends on is actually present. The documented promise is
			# the effective remaining keys "with form conditions applied
			# exactly as the parser enforces them", and suggesting a key
			# the parser would refuse is worse than silence. This is the
			# same declarative rule for `say`'s `on=` and `wait=`, so
			# both now appear only in the request-bearing form.
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


def missing_prose_operand(buffer: str) -> str | None:
	"""W36: the REQUIRED editor-capable prose operand this line is still
	missing, or None.

	Asked of the GRAMMAR, through the same analyzer the assistance line
	and Tab completion already consume — so form conditions apply
	exactly as the parser enforces them. `phase work=W1 to=parked` needs
	`reason=` only because it is parking, and this answers that
	correctly without knowing anything about `phase`.

	Pure: reads no authority state and converts nothing into effects. A
	malformed or unknown line returns None, so the ordinary parser
	refusal still speaks first — an editor is never opened for a command
	that could not run anyway.

	The trailing space is not a detail. `analyze_partial` is written for
	a line still being TYPED, so its last token is live: `close work=W1
	outcome=satisfying` reads as "the operator is part-way through
	`outcome=`" and reports the accepted values, not the remaining
	operands. On Enter that token is finished, and saying so is what
	turns the same analyzer into an answer about a COMPLETE line."""
	state = analyze_partial(buffer + " ")
	if state["state"] != "operands":
		return None
	# The prose operand must be the ONLY thing left. The approved
	# contract promises that saving "supplies that one missing value and
	# resumes the same canonical command execution path" — a promise
	# that cannot be kept when something else is missing too. Asking an
	# operator to write a paragraph and THEN telling them the command
	# also needs `outcome=` spends their prose on a line that was never
	# going to run; the ordinary missing-operand refusal names
	# everything at once and is the better answer.
	#
	# An unresolved form choice (`heading`) or an unmet conditional
	# (`notes`) is the same situation wearing a different name.
	if state["heading"] or state["notes"] or len(state["required"]) != 1:
		return None
	entry = _verb_spec(state["verb"]).get(state["required"][0][:-1])
	return entry["name"] if entry is not None and entry.get("prose") \
		else None


def _common_prefix(candidates) -> str:
	shared = os.path.commonprefix(list(candidates)) if candidates else ""
	return shared


def complete_partial(buffer: str) -> dict:
	"""W27: conservative Tab completion over the SAME analysis the
	assistance line and the parser use.

	Returns `{"buffer", "progressed", "candidates"}`. It edits only the
	live final token, preserves everything before it byte-for-byte, and
	reads no authority, config or filesystem. Shorthand is an input
	GESTURE: nothing here becomes accepted grammar, and execution still
	demands full canonical spellings.

	The rules, all deterministic and none of them cycling:

	- a unique candidate completes and appends its ruled delimiter — a
	  space for verbs and closed values, `=` for operand names;
	- several candidates extend only their common prefix, so a repeated
	  Tab that can make no further progress changes nothing and the
	  existing assist line remains the candidate display;
	- a diagnostic, an open quote, or no candidate leaves the buffer
	  exactly as it was.

	The candidate set for operand names is the EFFECTIVE one, not every
	name that shares a prefix: a key already supplied, or forbidden by
	the form conditions the parser enforces, is not offered — completing
	to something the parser would then refuse is worse than not
	completing at all."""
	analysis = analyze_partial(buffer)
	unchanged = {"buffer": buffer, "progressed": False, "candidates": []}
	state = analysis["state"]
	if state == "diagnostic":
		return unchanged
	parts = _partial_tokens(buffer.lstrip())
	if parts is None:
		return unchanged
	_completed, live, open_quote = parts
	if open_quote:
		# Rewriting the inside of an open quoted value would change its
		# quoting, which this never does.
		return unchanged
	live = live or ""

	if state in ("commands", "verbs"):
		candidates = [name for name in analysis["matches"]
		              if name.startswith(live)]
		delimiter = " "
	elif state == "values":
		candidates = [value for value in analysis["values"]]
		key = analysis["key"]
		typed = live.partition("=")[2]
		candidates = [value for value in candidates
		              if value.startswith(typed)]
		live, delimiter = typed, " "
	elif state == "operands":
		offered = set(analysis["required"]) | set(analysis["optional"])
		if analysis["heading"]:
			# an exactly-one choice is selectable until one is chosen
			offered |= {name for name in analysis["heading"]
			            .removeprefix("one of: ").split(" | ") if name}
		candidates = [name for name in (analysis["key_matches"] or [])
		              if name in offered]
		delimiter = ""
	else:
		return unchanged
	if not candidates:
		return unchanged

	if len(candidates) == 1:
		completion = candidates[0] + delimiter
	else:
		completion = _common_prefix(candidates)
		if len(completion) <= len(live):
			return {"buffer": buffer, "progressed": False,
			        "candidates": sorted(candidates)}
	if completion == live:
		return {"buffer": buffer, "progressed": False,
		        "candidates": sorted(candidates)}
	head = buffer[:len(buffer) - len(live)] if live else buffer
	return {"buffer": head + completion, "progressed": True,
	        "candidates": sorted(candidates)}


# W4: every Work-valued operand, by KEY NAME across the one grammar —
# each routes through THE strict selector resolver before dispatch, so
# the short and canonical spellings are interchangeable everywhere and
# a malformed or foreign value refuses before any transition runs.
# W7 (finding-local-thread-selectors): Thread-valued operands get the
# SAME pre-dispatch pass — resolution happens before the transitions
# fingerprint the operation, so `T2` and the canonical spelling are
# ONE operation identity, including effectively-once retries.
_WORK_VALUED = frozenset({"work", "on", "parent", "into",
                          "duplicate-of", "follow-up-of", "label"})
_THREAD_VALUED = frozenset({"thread"})


def _resolve_selector_operands(store, args) -> None:
	spec = _verb_spec(args.command)
	for name, entry in spec.items():
		if name in _WORK_VALUED:
			resolver = transitions.resolve_work_selector
		elif name in _THREAD_VALUED:
			resolver = transitions.resolve_thread_selector
		else:
			continue
		value = getattr(args, entry["dest"], None)
		if entry["repeat"]:
			if value:
				setattr(args, entry["dest"],
				        [resolver(store, one) for one in value])
		elif value is not None:
			setattr(args, entry["dest"], resolver(store, value))


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
			_resolve_selector_operands(store, args)
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
				# W5: launch filters use the ONE shared grammar and
				# validate BEFORE curses claims the screen — a bad
				# filter refuses instead of opening a partial view.
				launch_filter = _filter_operands(args)
				launch_filter = projection.normalize_filter(
					store, launch_filter,
					_participant(args.participant)[0])
				from baton_work.tui import run as tui_run
				import curses
				curses.wrapper(tui_run, store,
				               *_participant(args.participant),
				               config_path=args.config,
				               refresh=args.refresh,
				               work_filter=launch_filter)
				return 0
			result = _dispatch(store, args)
			snapshot_seq = (result.pop("snapshot_seq", None)
			                if isinstance(result, dict) else None)
			if snapshot_seq is None and \
					isinstance(result, projection.Snapshotted):
				snapshot_seq = result.snapshot_seq
			envelope = jsonapi.envelope(store,
			                            participant=args.participant,
			                            result=result,
			                            snapshot_seq=snapshot_seq)
			# W24755: THE ONE RAW-OUTPUT BRANCH, and it is reached only
			# here -- after the projection-version check, the --config
			# requirement, the participant validation and the dispatch
			# that every other command passes through. A portable export
			# is not a way around identity; it is a different rendering
			# of the same authorized answer.
			#
			# THE WHOLE DOCUMENT IS COMPOSED BEFORE ANYTHING IS WRITTEN.
			# `render_work_graph_dot` returns a complete string or
			# raises, so a refusal leaves stdout untouched and the
			# operator's `> work.dot` is empty rather than holding a
			# half-graph that happens to parse.
			if args.command == "work-graph" and args.format == "dot":
				from baton_work import dot as dot_render
				document = dot_render.render_work_graph_dot(envelope)
				sys.stdout.write(document)
				return 0
			print(json.dumps(envelope, indent=2, sort_keys=True))
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
			follow_up_of=args.follow_up_of,
			priority=args.priority, op_id=args.op_id,
			refs=args.refs or ())
	if command == "instructions":
		_need_participant(args)
		return config.participant_instructions(store.accepted_config,
		                                       args.participant, args.role)
	if command == "accept":
		team, member = _need_participant(args)
		create_only = {"kind=": args.kind, "title=": args.title,
		               "classification=": args.classification,
		               "parent=": args.parent}
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
			          "parent": args.parent}
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
		                                  actor_team=team, actor=member,
		                                  rationale=args.rationale, op_id=args.op_id,
		                                  refs=args.refs or ())
	if command == "unblock":
		team, member = _need_participant(args)
		return transitions.remove_dependency(
			store, args.work, args.on, actor_team=team, actor=member,
			rationale=args.rationale, op_id=args.op_id,
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
		if _re.match(r"^W[1-9][0-9]*$", left):
			# W4: the locator's Work form takes the short selector too
			left = transitions.resolve_work_selector(store, left)
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
		# W80: say is DISCUSSION (plus the @ request operator). The
		# baton moves only through the explicit pass verb below.
		team, member = _need_participant(args)
		return transitions.post_thread(
			store, args.thread, author_team=team, author=member,
			body=args.body, include=args.include or (),
			request=args.request, on=args.on, wait=args.say_wait,
			op_id=args.op_id, refs=args.refs or ())
	if command == "pass":
		# W171 (finding-pass-is-work-event): pass is an authoritative
		# THREADLESS Work transition — comment as durable evidence in
		# the pass event, Route + destination phase + planned Next +
		# claim release in one atomic act; no message, no thread, no
		# cursor or count movement. A refusal leaves everything
		# unchanged.
		team, member = _need_participant(args)
		return transitions.pass_work(
			store, args.work, actor_team=team, actor=member,
			to=args.to, route=args.route,
			comment=args.comment, set_next=args.set_next,
			op_id=args.op_id, refs=args.refs or ())
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
	if command == "work-events":
		_need_participant(args)
		return projection.work_events(store, args.work,
		                              after=args.after,
		                              before=args.before,
		                              newest=bool(args.newest),
		                              limit=args.limit)
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
	if command == "try":
		team, member = _need_participant(args)
		return transitions.create_trial(
			store, args.work, actor_team=team, actor=member,
			candidate=args.candidate, assign=args.assign,
			review_at=args.review_at, op_id=args.op_id,
			refs=args.refs or ())
	if command == "extend":
		team, member = _need_participant(args)
		return transitions.extend_trial(
			store, args.work, args.trial, actor_team=team, actor=member,
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
		return transitions.abandon_trial(
			store, args.work, args.trial, actor_team=team, actor=member,
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
			expect=args.expect, episode=args.episode,
			reason=args.reason, op_id=args.op_id,
			refs=args.refs or ())
	if command == "heartbeat":
		team, member = _need_participant(args)
		return transitions.heartbeat(
			store, args.work, actor_team=team, actor=member,
			op_id=args.op_id, refs=args.refs or ())
	if command == "poke":
		team, member = _need_participant(args)
		return transitions.poke(
			store, actor_team=team, actor=member, target=args.target,
			request=args.request, expires_at=args.expires_at,
			op_id=args.op_id, refs=args.refs or ())
	if command == "poke-answer":
		team, member = _need_participant(args)
		return transitions.answer_poke(
			store, args.poke, actor_team=team, actor=member,
			state=args.state, explanation=args.explanation,
			work=args.work or (), provider=args.provider,
			model=args.model, session_state=args.session_state,
			auth_state=args.auth_state, limit_state=args.limit_state,
			retry_at=args.retry_at, context_limit=args.context_limit,
			context_used=args.context_used,
			context_remaining=args.context_remaining,
			op_id=args.op_id, refs=args.refs or ())
	if command == "poke-cancel":
		team, member = _need_participant(args)
		return transitions.cancel_poke(
			store, args.poke, actor_team=team, actor=member,
			reason=args.reason, op_id=args.op_id,
			refs=args.refs or ())
	if command == "prioritize":
		team, member = _need_participant(args)
		return transitions.prioritize(
			store, args.work, actor_team=team, actor=member,
			priority=args.priority, op_id=args.op_id,
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
			raise WorkError("block records exactly ONE typed gate: "
			                "gates or one obligation, not both")
		wait = "gates" if args.wait_gates else args.wait_obligation
		return transitions.set_phase(store, args.work, actor_team=team,
		                             actor=member, phase=args.phase,
		                             reason=args.reason, wait=wait, op_id=args.op_id,
			refs=args.refs or ())

	if command == "search":
		team, member = _need_participant(args)
		return projection.search(
			store, args.query, viewer_team=team, viewer_member=member,
			work_filter=_filter_operands(args), after=args.after,
			limit=args.limit)
	if command == "home":
		team, member = _need_participant(args)
		return projection.home(store, viewer_team=team,
		                       viewer_member=member,
		                       work_filter=_filter_operands(args))
	if command == "tree":
		team, member = _need_participant(args)
		return projection.tree(store, args.work, viewer_team=team,
		                       viewer_member=member,
		                       work_filter=_filter_operands(args))
	if command == "filter":
		raise WorkError(
			"filter is client-local console view state — use it in "
			"the TUI command mode (:filter ...), or pass the same "
			"operands to home, tree, or tui")
	if command == "obligations":
		team, _member = _need_participant(args)
		return projection.obligations(store, viewer_team=team)
	if command == "pokes":
		team, member = _need_participant(args)
		return projection.pokes(store, viewer_team=team,
		                        viewer_member=member, asker=args.asker,
		                        target=args.target, after=args.after,
		                        limit=args.limit)
	if command == "reroute":
		team, member = _need_participant(args)
		return transitions.reroute_work(
			store, args.work, actor_team=team, actor=member,
			to=args.to, route=args.route, reason=args.reason,
			op_id=args.op_id, refs=args.refs)
	if command == "runtime-start":
		team, member = _need_participant(args)
		return transitions.runtime_start(
			store, actor_team=team, actor=member,
			incarnation=args.incarnation, adapter=args.adapter,
			provider=args.provider, model=args.model,
			session=args.session, expires_at=args.expires_at,
			action_owner=args.action_owner, rationale=args.rationale,
			op_id=args.op_id, refs=args.refs)
	if command == "incident":
		team, member = _need_participant(args)
		return transitions.incident_report(
			store, actor_team=team, actor=member,
			incarnation=args.incarnation, cause=args.cause,
			category=args.category, detail=args.detail, work=args.work,
			episode=args.episode, action_key=args.action_key,
			session=args.session, op_id=args.op_id, refs=args.refs)
	if command == "dismiss":
		team, member = _need_participant(args)
		return transitions.incident_dismiss(
			store, actor_team=team, actor=member,
			incident=args.incident, note=args.note,
			op_id=args.op_id, refs=args.refs)
	if command == "runtime-state":
		team, member = _need_participant(args)
		return transitions.runtime_state(
			store, actor_team=team, actor=member,
			incarnation=args.incarnation, state=args.state,
			cause=args.cause, detail=args.detail, work=args.work,
			episode=args.episode, session=args.session,
			expires_at=args.expires_at, op_id=args.op_id,
			refs=args.refs)
	if command == "runtime-end":
		team, member = _need_participant(args)
		return transitions.runtime_end(
			store, actor_team=team, actor=member,
			incarnation=args.incarnation, cause=args.cause,
			detail=args.detail, op_id=args.op_id, refs=args.refs)
	if command == "runtime-facts":
		team, member = _need_participant(args)
		return transitions.runtime_facts(
			store, actor_team=team, actor=member,
			incarnation=args.incarnation, source=args.source,
			observed_at=args.observed_at, answers=args.answers,
			facts={"service": args.service,
			       "dispatcher": args.dispatcher,
			       "readiness": args.readiness,
			       "workdir": args.workdir, "log": args.log,
			       "version": args.version,
			       "retry-at": args.retry_at},
			op_id=args.op_id, refs=args.refs)
	if command == "runtime-refresh":
		team, member = _need_participant(args)
		return transitions.runtime_refresh(
			store, actor_team=team, actor=member, target=args.target,
			op_id=args.op_id, refs=args.refs)
	if command == "runtime":
		team, member = _need_participant(args)
		return projection.runtime(store, viewer_team=team,
		                          viewer_member=member)
	if command == "runtime-history":
		_need_participant(args)
		return projection.runtime_history(
			store, participant=args.participant, after=args.after,
			limit=args.limit)
	if command == "teams":
		team, member = _need_participant(args)
		return projection.teams(store, viewer_team=team,
		                        viewer_member=member)
	if command == "drain":
		team, member = _need_participant(args)
		return transitions.drain_dispatch(
			store, actor_team=team, actor=member, reason=args.reason,
			op_id=args.op_id, refs=args.refs or ())
	if command == "resume":
		team, member = _need_participant(args)
		return transitions.resume_dispatch(
			store, actor_team=team, actor=member, reason=args.reason,
			op_id=args.op_id, refs=args.refs or ())
	if command == "dispatch":
		if args.history:
			return projection.dispatch_history(
				store, limit=args.limit if args.limit else 50,
				before=args.before)
		return projection.dispatch_view(store)
	if command == "incidents":
		team, member = _need_participant(args)
		return projection.incidents(
			store, viewer_team=team, viewer_member=member,
			include_dismissed=bool(args.include_dismissed))
	if command == "inbox":
		team, member = _need_participant(args)
		return projection.inbox(store, viewer_team=team,
		                        viewer_member=member)
	if command == "summary":
		team, _member = _need_participant(args)
		return projection.team_summary(store, viewer_team=team)
	if command == "wait":
		# W136: the wake is PARTICIPANT-relative — both halves of the
		# validated identity reach the projection.
		team, member = _need_participant(args)
		return projection.wait_actionable(store, viewer_team=team,
		                                  viewer_member=member,
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
	if command == "work-graph":
		return projection.work_graph(store, team=args.team,
		                             status=args.status,
		                             changed_from=args.changed_from,
		                             changed_until=args.changed_until)
	if command == "links":
		return projection.links(store, args.work)
	if command == "actionable-work":
		team, member = _need_participant(args)
		return projection.actionable_work(store, viewer_team=team,
		                                  viewer_member=member,
		                                  after=args.after, limit=args.limit)
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
