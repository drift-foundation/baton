"""The versioned JSON surface — Gate A step A6.

Every response is an ENVELOPE: projection version, protocol version, viewer,
authority uuid and snapshot sequence (the consistency token), then the
result. Stable ids, enums, numbers, booleans and structured relations — no
preformatted display strings, ever (parity ruling: the TUI renders, this
states).

Version discipline: a client may demand a projection version; the same MAJOR
is compatible (unknown fields are ignorable within it), a different major
fails clearly rather than degrading into plausible but false output.
"""

from __future__ import annotations

from baton_work.authority import Authority, WorkError

# 4.1 (schema 15): rows additively gain canonical `priority`,
# `last_changed_at`, and `last_change_seq`. Same major: nothing moved
# or changed meaning.
# 4.2 (W47): rows and details additively gain `heartbeat_at` — the
# latest qualifying claim/heartbeat timestamp of the CURRENT claim
# epoch (null while unclaimed and on terminal rows) — the first
# projection carrying claimant liveness evidence. Same major.
# 4.3 (W136): `wait` becomes PARTICIPANT-relative — its actionable
# entries are typed actions (originally kind: obligation | due_round |
# work; due_round became due_trial at 6.0) with
# stable `action_key` identities, filtered to the exact requesting
# member by live route resolution; routed Work enters the wake set for
# the first time. Same major: envelope shape and every other
# projection unchanged.
# 4.4 (W171, finding-pass-is-work-event): `pass` is a THREADLESS Work
# event — the public grammar drops thread= (refused as unknown), the
# pass/return event payload carries the exact comment plus complete
# transition metadata and no thread, and a pass moves no message,
# cursor, or Message/My/New/obligation count. Same major: the envelope
# and every other projection unchanged.
# 5.0 (W179, finding-visible-scope-message-counts): default Work
# counters describe the DIRECT visible scope — Msg/My/New in home
# rows and detail cover exactly the threads labelled directly to the
# Work (thread-less verification obligations stay with their own
# Work); descendants never inflate a parent. The recursive union
# survives only in the explicitly named breakdown, whose field is now
# `subtree_total` (was `total`). This CHANGES the meaning of existing
# fields, so the major moves: 5.0, honest and breaking — the human
# ruled no v11 client-compat limit during the trial, so no alias, no
# migration, and a 4.x demand refuses cleanly.
# 6.0 (W202, finding-try-trial-vocabulary): the candidate-verification
# object is a TRIAL created by `try` — the `round` verb, the rounds
# projection fields, the round: action keys, and the due_round wake
# kind are GONE without alias (fresh-authority evolution, ruled
# no-migration). Same honest-breaking policy as 5.0: an old-major
# demand refuses cleanly.
# 6.1 (W226, finding-tui-held-duration): rows/detail gain the
# committed `handoff_at` instant (newest pass/return; null for
# never-passed Work) and the structured `pickup` state
# (claimed | pending | overdue | null). Additive; glyphs stay TUI-only.
# 6.2 (W7, finding-local-thread-selectors): thread, threads, and
# work-threads expose `local_id` — the authority-local `T<sequence>`
# spelling every Thread-valued command accepts — alongside canonical
# identity. Additive.
# 8.0 (W245, finding-current-is-claimant): ROUTE and CURRENT are
# separate published facts. The endpoint formerly published as
# `current` is now `route`; `current` is the EXACT claiming
# participant (team/member/participant) or null, replacing `active`
# with no alias. Far-row link summaries carry both. The `current=`
# filter selects the claimant and `route=` selects eligibility.
# This REUSES an existing field name for a different meaning, which is
# the most dangerous kind of change a pinned consumer can meet — a 7.x
# client reading `current` would silently take an endpoint struct for a
# claimant. So the major moves and a 7.x demand refuses cleanly, which
# is exactly the stale-consumer refusal this finding asks for.
# 9.0 (W38, finding-phase-is-scheduler-state): PHASE is a closed
# scheduler axis — queued | active | waiting | parked, terminal null
# (`waiting` is renamed `block` at 10.0). The
# role-shaped `research` and `review` values are gone, and a handoff no
# longer derives its phase from the destination role. `active` now means
# exactly "a participant holds the claim". The claimant published as
# `current` at 8.0 is renamed `handler`, and the `current=` filter
# becomes `handler=`; `route` and `next` are unchanged.
# Participant-action envelopes carry `phase`, so their VALUE SET changed
# and every readiness consumer must be updated in the same candidate —
# the major moves and an 8.x demand refuses cleanly rather than reading
# a vocabulary that no longer exists.
# 9.1 (W29, finding-message-total-unseen-heading): the thread read
# carries `total` — the whole-thread Message count at the snapshot,
# beside the whole-thread personal `new`. Additive: a page-length
# reading of the old shape stays valid, it was just never the thread.
# 9.2 (W47, finding-event-index-phase-duration): `work-events` entries
# carry a typed `phase_interval` on the event that ENTERED each
# scheduler episode — phase, start/end sequence and timestamps, elapsed
# whole seconds, and whether it is still open. Replayed from the
# ledger's `phase_now` records, which every phase-changing transition
# now writes. Additive.
# 10.0 (W78, finding-unclaimed-work-cue): the `waiting` phase is renamed
# `block` and `waiting_on` is REPLACED by a structured `gate` — kind
# (`work` or `message`), the canonical locator and its `W…`/`M…`
# selector, the episode's `started_at`, and for a Message gate the
# pending obligation's identity, state and endpoint. The summary
# counter `waiting` becomes `blocked`.
# Both halves are breaking. The phase VALUE SET changed, so every
# consumer that matched `waiting` must be updated in the same candidate;
# and `waiting_on` named the wake CONDITION while `gate` names the one
# thing actually holding the Work and since when. A 9.x client would
# have had to combine `waiting_on`, `first_open_blocker` and journal
# timestamps to answer what `gate` answers directly — and could not
# answer it at all when the displayed gate changed inside `block`, which
# the authority previously committed silently. So the major moves and a
# 9.x demand refuses cleanly rather than reading a shape that cannot
# express the question.
# 11.0 (W155, finding-tui-three-level-work-tree): the `tree` window spans
# THREE containment levels instead of two, and every row carries an
# additive `deeper` — this row contains Work the window does not show.
#
# I first published this as a MINOR, reasoning that nothing was renamed
# and that a client written as "0 is a root, anything else is a child"
# would merely draw a grandchild at the wrong indent — a mis-render, not
# a misread. Review overturned that with a counterexample from this very
# repository: `test_parity.py::_parse_rows` matched a leading `↳ ` and
# mapped everything else to depth 0, so a depth-2 row decoded as a ROOT.
# That is a consumer silently reading the wrong containment, and this
# file's own rule is that every response inside one major is compatible.
# Adding a value to a consumed domain breaks that rule whatever the
# failure is called, so the major moves and the readiness and
# role-instruction consumers are widened in the same candidate.
# 11.1 (W5, finding-conversational-agent-poke): a FOURTH participant
# action kind, `poke` — a conversational "what's up?" addressed to one
# exact configured participant — plus the `pokes` projection carrying
# each poke, its one terminal answer, and canonical Work state beside
# every claim the agent made. Nothing existing moved or changed meaning.
#
# This is published as a MINOR, and the reasoning deserves stating
# because this file's own 11.0 note says a change a consumer would
# "silently misread OR REFUSE" moves the major. Until this candidate an
# unknown action kind DID refuse — the whole envelope, not the entry —
# so on that rule alone the major would move. The same candidate widens
# both readiness bridges to ignore an unreadable entry, keep the rest of
# the envelope, and report the skew; the widening lands before the
# authority can emit the kind, and every consumer in this repository
# moves with it. Under a tolerant consumer this addition is genuinely
# ignorable, which is what "compatible within the major" means, and
# every FUTURE action kind is additive for the same reason.
#
# The exposure this leaves is real and bounded: a runner binary built
# before the widening, met by an authority that emits a poke, refuses
# that envelope by name rather than reading it wrongly. Both bridges and
# the authority ship from one release directory, so they move together —
# and a refusal that names the unknown kind is the failure the
# tolerance permanently removes, not one it hides.
# 11.2 (W7, finding-blocker-effective-priority): rows and details gain
# the canonical boolean `blocking` — this Work is open, ready, unclaimed,
# neither gated nor parked, and at least one OPEN Work waits on it
# through a live dependency edge. The same predicate orders every Work
# list (home, tree, children) and the participant-action wake set:
# WITHIN one explicit-priority pool, a blocker sorts ahead of
# free-standing Work, with stable creation order the final tie-break.
#
# Explicit `high | normal | low` is untouched and is never rewritten or
# inherited; there is no cross-pool promotion, no fan-out weight, and no
# second user-managed priority axis. Nothing became claimable that was
# not already, and no field changed meaning.
#
# Additive, and deliberately so: the ORDER of a list is not a field a
# client reads a value out of, and no consumer can misread `blocking` as
# something it already had. A client that took row 0 as "what next" now
# gets a better answer to the same question, which is the point. Compare
# 11.1, where an unwidened consumer would have REFUSED an envelope — the
# rule discriminates, and here it says minor.
# 12.0 (W5 review 2026-08-19): the accumulated candidate — the `poke`
# participant action and its `pokes` projection (W5), and the `blocking`
# boolean with the blocker-first Work ordering (W7) — is published as a
# MAJOR.
#
# I published the poke half as 11.1 and argued the case for a major in
# the same breath; review ruled the major, and the reasoning is worth
# keeping because it is the rule in this file finally being applied to
# its own hardest case.
#
# A new ACTION KIND is not a new field. A consumer built before the
# tolerance widening REFUSES an envelope containing `poke` — the whole
# envelope, not the entry — so it stops receiving its ordinary Work and
# obligation wakes too. Widening every consumer in the SAME candidate
# does not repair that: it repairs the candidate, while the mixed
# interval between a deployed old runner and a new authority is exactly
# where the refusal lives. This file's rule says a change a consumer
# would misread OR REFUSE moves the major, and refusing is the case.
#
# What the tolerance widening buys is the NEXT one: inside major 12
# every consumer ignores an unreadable entry and keeps the rest, so a
# fifth action kind really will be an additive minor. That is the
# difference between this bump and a permanent tax.
#
# W7's `blocking` and ordering are genuinely additive and rode 11.2
# briefly; they are aggregated here rather than published separately,
# because nothing has been released between them and two majors for one
# unreleased candidate would describe a history that never happened.
# 12.1 (W25, finding-tui-jobs-teams-inbox): two NEW read projections,
# `teams` and `inbox`. Teams is the operational roster — configured
# members, their route coverage including W230 alternates, the Work each
# one canonically holds, and the runner status each last reported through
# a poke answer. Inbox is the participant-relative owed-action and
# attention surface, with `total`, `unseen`, `owed` and the `owed_action`
# boolean the console bolds its tab on.
#
# A MINOR by this file's own discriminator, and the case is easy for
# once. No existing response gains, loses or redefines a field; no new
# participant action kind exists, so no readiness consumer meets an entry
# it cannot read. Inbox does not derive owed-ness a second time — it
# reads `participant_actions`, the same derivation `wait` consumes — so
# there is no second opinion to drift. A consumer built before this
# simply never calls the two new verbs, which is exactly what
# "ignorable" means and is the property 12.0 bought.
#
# `inbox` deliberately omits actionable WORK, which `participant_actions`
# does return: Jobs is the Work surface and repeating its rows here would
# put one queue in two places. The wake set is unchanged and still
# carries both, because a runner has one attention span and no tabs.
# 12.2 (W93 slice 6, finding-agent-runtime-state): a FIFTH participant
# action kind, `runtime_refresh` — an operator's request that this
# participant's ADAPTER republish its safe operational inventory. It
# carries `wakes_model: false` because the adapter answers it from facts
# it already holds; `poke` remains the path for what only the agent can
# say.
#
# A MINOR, and this is the case 12.0's own note anticipated: that bump
# went major because an unwidened consumer REFUSED a whole envelope
# containing an unknown kind, and the same candidate taught every
# consumer to ignore an unreadable entry and keep the rest. That
# tolerance is what makes this one additive — a build that predates it
# drops the entry and still receives its Work, its obligations and its
# pokes.
# 12.3 (W93 slice 6 review R25, finding-agent-runtime-state): a
# `runtime_refresh` entry carries the request's `generation` — the
# authority sequence that minted it — and its `action_key` is built
# from that rather than from the request instant. Canonical instants
# are whole seconds, so two asks inside one second produced the SAME
# key and a level-triggered consumer suppressed the second as already
# delivered. `requested_at` stays beside it as what an operator reads.
#
# A MINOR: the key is opaque to every consumer, which delivers on it
# changing and never parses it, and the new field is additive.
PROJECTION_VERSION = "12.3"


def require_version(requested: str | None) -> None:
	if requested is None:
		return
	wanted_major = str(requested).split(".")[0]
	have_major = PROJECTION_VERSION.split(".")[0]
	if wanted_major != have_major:
		raise WorkError(
			f"projection version {requested} is not compatible with "
			f"{PROJECTION_VERSION}; refusing to answer in a shape the "
			f"client will misread")


def envelope(store: Authority, *, participant: str | None, result,
             snapshot_seq: int | None = None) -> dict:
	"""`snapshot_seq` may be supplied by a projection that read everything
	inside ONE database snapshot (home does); the envelope then describes
	that snapshot, never a later commit (WS-1 R3)."""
	meta = store.meta()
	return {
		"projection_version": PROJECTION_VERSION,
		"protocol_version": int(meta["protocol_version"]),
		"authority_uuid": meta["authority_uuid"],
		"snapshot_seq": store.last_seq() if snapshot_seq is None
		else snapshot_seq,
		"participant": participant,
		"result": result,
	}
