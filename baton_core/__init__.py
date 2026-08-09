"""Baton core: Baton semantics as an importable library.

`baton-tui` (the human console) is the current front end over this package.
Protocol, schema, validation, storage, claim, reply, notice, attachment and
audit behaviour live here, and SQLite is private to this package: a front end
that opens the database directly has become a second implementation of the
protocol.

This is a LIBRARY package, not a runnable artifact: it has no `__main__` and
no command line.

WHAT IS TRUE TODAY, stated exactly because an earlier version of this
paragraph was not. The released `baton` CLI does NOT use this package: it is
still built from the top-level `baton_v6.py`, and `_impl.py` is a
byte-for-byte copy of that file plus a small set of recorded read-only
additions. So the same behaviour deliberately exists in two places right now.
That duplication is the FROZEN PARITY INTERVAL, not an accident and not a
steady state:

- `baton_v6.py` is frozen and hash-pinned for the whole interval, and serves
  as the oracle.
- Fixes land HERE only. A fix applied to both copies would make them agree
  with each other about the wrong answer, and the oracle would have quietly
  stopped being an oracle.
- `test_core_parity.py` drives both through the same operations and records
  every deliberate divergence rather than reconciling it silently.

CLI adoption of this package is approved as a SEPARATE, later stage, on its
own branch and with its own review; it is not scheduled here and nothing in
this package assumes it. Until it lands, the CLI source, artifact, builder and
distribution stay untouched.
"""

from ._impl import *          # noqa: F401,F403  -- surface parity with the oracle
from . import _impl

# `_impl` is a byte-copy of the single-artifact build, so it still carries the
# CLI adapter (`main`, `_build_parser`). Those are NOT part of this package's
# surface: a library that exports a command line invites being run as one, and
# this core is imported, never executed. They stay reachable as `_impl.main`
# for the differential harness, which needs to compare the oracle's behaviour.
for _cli_only in ("main", "_build_parser"):
	globals().pop(_cli_only, None)
del _cli_only

# The contract a front end compiles against. Bumped when the PUBLIC client API
# changes shape, independently of PROTOCOL_VERSION (the on-disk contract) and
# of any front end's own release version -- which is the whole point of
# splitting them: a TUI can ship faster than the protocol moves, provided it
# declares the core API it was built against.
CORE_API_VERSION = 1

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
