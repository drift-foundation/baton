"""Deterministic W4615 review reproductions.

Run from the repository root with::

	./.venv/bin/python3 work/records/2026/08/finding-managed-stack-drain/evidence/repro_projection_edges.py

The authority is a temporary test instance.  The first reproduction shows
that an authority instant containing two typed dispatch events cannot be
fully traversed through the current sequence-only cursor.  The second
interposes a committed final pass between dispatch_view's two reads to show
that the returned mode and blocker count need not describe one snapshot. The
third shows that automatic pause bypasses the authority's injected clock.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "tests" / "work"))
sys.path.insert(0, str(REPO / "src"))

import fixtures  # noqa: E402
import baton_work as bw  # noqa: E402
from baton_work import projection as pj  # noqa: E402
from baton_work import transitions as tr  # noqa: E402


def authority(root: Path):
	root.mkdir(parents=True)
	database = root / "work.sqlite3"
	cast = fixtures.build(str(database))
	store = bw.Authority(str(database))
	store.conn.execute(
		"INSERT INTO member_capabilities (team, member, capability) "
		"VALUES ('lang', 'ada', 'dispatch')")
	store.conn.commit()
	return store, cast


def reproduce_sequence_cursor(root: Path) -> None:
	store, _cast = authority(root)
	try:
		tr.drain_dispatch(store, actor_team="lang", actor="ada")
		first = pj.dispatch_history(store, limit=1)
		second = pj.dispatch_history(store, limit=1,
		                             before=first["next_before"])
		all_kinds = [event["kind"] for event in
		             pj.dispatch_history(store)["events"]]
		paged_kinds = [event["kind"] for event in first["events"]]
		paged_kinds += [event["kind"] for event in second["events"]]
		print("sequence cursor:")
		print(f"  complete={all_kinds}")
		print(f"  traversed={paged_kinds}")
		assert set(all_kinds) == {"drain_requested", "pause_reached"}
		assert len(paged_kinds) == 1
	finally:
		store.close()


def reproduce_split_snapshot(root: Path) -> None:
	reader, cast = authority(root)
	writer = bw.Authority(str(root / "work.sqlite3"))
	work = cast["step_fix"]
	try:
		tr.claim_work(reader, work, actor_team="lang", actor="ada")
		tr.drain_dispatch(reader, actor_team="lang", actor="ada")
		original_dispatch_row = pj.dispatch_row

		def finish_after_control_read(conn):
			row = original_dispatch_row(conn)
			tr.pass_work(writer, work, to="lang.rev", actor_team="lang",
			             actor="ada", comment="finish during status read")
			return row

		pj.dispatch_row = finish_after_control_read
		try:
			view = pj.dispatch_view(reader)
		finally:
			pj.dispatch_row = original_dispatch_row
		actual = pj.dispatch_view(reader)
		print("split snapshot:")
		print(f"  returned={(view['mode'], view['blocking_claims'])}")
		print(f"  committed={(actual['mode'], actual['blocking_claims'])}")
		assert (view["mode"], view["blocking_claims"]) == ("draining", 0)
		assert (actual["mode"], actual["blocking_claims"]) == ("paused", 0)
	finally:
		writer.close()
		reader.close()


def reproduce_split_clock(root: Path) -> None:
	store, _cast = authority(root)
	fixed = "2099-01-02T03:04:05Z"
	try:
		store.clock = lambda: fixed
		tr.drain_dispatch(store, actor_team="lang", actor="ada")
		events = pj.dispatch_history(store)["events"]
		stamps = {event["kind"]: event["ts"] for event in events}
		print("split clock:")
		print(f"  drain_requested={stamps['drain_requested']}")
		print(f"  pause_reached={stamps['pause_reached']}")
		assert stamps["drain_requested"] == fixed
		assert stamps["pause_reached"] != fixed
	finally:
		store.close()


def main() -> None:
	with tempfile.TemporaryDirectory(prefix="w4615-review-") as directory:
		root = Path(directory)
		reproduce_sequence_cursor(root / "cursor")
		reproduce_split_snapshot(root / "snapshot")
		reproduce_split_clock(root / "clock")


if __name__ == "__main__":
	main()
