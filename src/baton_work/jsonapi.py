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

PROJECTION_VERSION = "2.1"


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
