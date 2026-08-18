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
PROJECTION_VERSION = "8.0"


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
