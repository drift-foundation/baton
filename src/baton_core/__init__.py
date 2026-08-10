"""Baton core: Baton semantics as an importable library.

BOTH front ends are over this package now: `baton-tui`, the human console, and
`baton`, the agent CLI. Protocol, schema, validation, storage, claim, reply,
notice, attachment and audit behaviour live here, and SQLite is private to
this package: a front end that opens the database directly has become a second
implementation of the protocol.

This is a LIBRARY package, not a runnable artifact: it has no `__main__` and
no command line of its own. `baton_core.cli` is the one door the CLI comes in
through, and it is a door rather than a widened surface — `import baton_core`
gets a library with no `main` on it.

WHAT IS TRUE TODAY, stated exactly because three earlier versions of this
paragraph were not. `bin/baton` is built from this package. Protocol 10 has
landed here: the part label is `part_name`, and this is the implementation,
not a copy of one.

`baton_v6.py` is RETIRED. It was the differential oracle for the whole
scaffolding period; protocol 10 ended that arrangement, because an oracle
pinning protocol-9 behaviour cannot measure an implementation that no longer
claims to implement it. `test_core_parity.py` is deleted.

The file remains in the tree, frozen, unshipped and imported by nothing. Its
job now is EVIDENCE: it is the record of what protocol 9 actually did, and a
record that can be edited is not a record. `test_retired_oracle.py` keeps its
hash pin — the same assertion it always carried, now guarding the evidence
rather than the measurement — and proves, by parsing the tree rather than
grepping it, that nothing imports it.

The coverage did not shrink. `test_core_conformance.py` is the corpus that
used to drive the oracle, moved onto this package whole rather than
hand-picked, so nobody chose which properties survived.

CLIENT API -- what this package offers a front end. `list_roots`,
`list_notice_activity`, `read_claimed_external_part`, and two columns on
`list_messages` are here for the console; `list_received` was removed with the
view it served.

(The "observable parity" list that stood here — a manifest `address` on each
delivered part, and `created_ts` on claimed scan rows — described what the
differential harness tolerated. There is no harness, so there is nothing to
tolerate: those are simply part of this implementation.)
"""

from ._impl import *          # noqa: F401,F403
from . import _impl

# `_impl` carries the CLI adapter (`main`, `_build_parser`). Those are NOT part
# of this package's surface: a library that exports a command line invites
# being run as one, and this core is imported, never executed. They stay
# reachable as `_impl.main` for `baton_core.cli`, which is the one door the
# executable comes in through.
for _cli_only in ("main", "_build_parser"):
	globals().pop(_cli_only, None)
del _cli_only

# The contract a front end compiles against. Bumped when the PUBLIC client API
# changes shape, independently of PROTOCOL_VERSION (the on-disk contract) and
# of any front end's own release version -- which is the whole point of
# splitting them: a TUI can ship faster than the protocol moves, provided it
# declares the core API it was built against.
CORE_API_VERSION = 2

PROTOCOL_VERSION = _impl.PROTOCOL_VERSION
TOOL_VERSION = _impl.TOOL_VERSION


def delivery_for(store, claim: dict) -> dict:
	"""The lossless delivery envelope for a claim the caller already holds.

	Public because every front end needs it: the CLI prints it, the console
	renders it. It was private-by-convention in the single-artifact build only
	because `main()` was the sole caller."""
	return _impl._delivery(store, claim)


def notice_delivery(notice: dict) -> dict:
	"""The broadcast delivery envelope, distinguished from a directed delivery
	by key: `{"notice": ...}` rather than `{"claim": ..., "message": ...}`."""
	return _impl._notice_delivery(notice)


def core_versions() -> dict:
	"""What this core is, for a front end to check at startup."""
	return {
		"core_api_version": CORE_API_VERSION,
		"protocol_version": PROTOCOL_VERSION,
		"tool_version": TOOL_VERSION,
	}
