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

WHAT IS TRUE TODAY, stated exactly because two earlier versions of this
paragraph were not. Stage 1A landed: `bin/baton` is built from this package
and no longer contains `baton_v6.py`. Protocol 9 and the CLI's behaviour are
unchanged by that adoption; only the artifact bytes moved.

`baton_v6.py` remains in the tree, frozen, and is NOT shipped. Its only job is
to be the differential ORACLE:

- it stays byte-identical, because it is the instrument parity is measured
  with;
- fixes land HERE only. A fix applied to both copies would make them agree
  with each other about the wrong answer, and the oracle would have quietly
  stopped being an oracle;
- `test_core_parity.py` drives both through the same operations and records
  every deliberate divergence rather than reconciling it silently.

Two records, and they are NOT the same record. Conflating them once produced
the sentence "the divergences are additive ... and the removal of
`list_received`", which contradicts itself.

OBSERVABLE PARITY -- what the differential harness sees when both
implementations are driven through the same operations. Exactly two, and both
are ADDITIONS:

- a manifest `address` on each delivered part, making the envelope
  self-addressing;
- `created_ts` on claimed scan rows.

Anything else differing is an unrecorded divergence and fails the harness.

CLIENT API -- what this package offers a front end, which the oracle never
had a reason to. Additions: `list_roots`, `list_notice_activity`,
`read_claimed_external_part`, and two columns on `list_messages`. One removal:
`list_received`, which served a view that no longer exists.

A removal here is not a parity divergence. It is a method the oracle's callers
never had, because the oracle has no front end.
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
