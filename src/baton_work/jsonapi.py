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
PROJECTION_VERSION = "11.0"


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
