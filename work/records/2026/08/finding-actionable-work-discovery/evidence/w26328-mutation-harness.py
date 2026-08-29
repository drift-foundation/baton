"""Measure W26328's actionable-work derivation by removing its rules."""
import pathlib, shutil, subprocess, sys
HOME = pathlib.Path("/home/sl/src/baton")
SRC = HOME / "src" / "baton_work"
MODULES = ["tests/work/test_w26328_actionable_discovery.py",
           "tests/work/test_w81_personal_bold.py",
           "tests/work/test_w2938_participant_pickup.py",
           "tests/work/test_w6814_active_trails.py",
           "tests/work/test_w155_three_level_tree.py"]

MUTATIONS = [
    # EXPECTED UNSEEN, and stated rather than removed. `phase='queued'`
    # already excludes a claimed Work, because W38 makes `active` hold exactly
    # when a Handler does; and `ready=1` already excludes a terminal one,
    # because closing always clears readiness. Both clauses are the finding's
    # own predicate written literally, and the invariants they lean on are
    # asserted by TestThePredicateRestsOnInvariantsThisSuiteChecks -- so if
    # either stops holding, that fails rather than the count quietly drifting.
    EXPECTED_UNSEEN := "a claimed Work counts as actionable",
]
EXPECTED = {"a claimed Work counts as actionable", "a terminal Work counts"}
MUTATIONS = MUTATIONS[:-1] + [
    ("a claimed Work counts as actionable", "projection.py",
     '"AND handler_team IS NULL AND route_team=?", (viewer_team,)):',
     '"AND route_team=?", (viewer_team,)):'),

    ("a blocked or parked Work counts", "projection.py",
     '''"WHERE status='open' AND ready=1 AND phase='queued' "
            "AND handler_team IS NULL AND route_team=?", (viewer_team,)):''',
     '''"WHERE status='open' AND ready=1 "
            "AND handler_team IS NULL AND route_team=?", (viewer_team,)):'''),

    ("a terminal Work counts", "projection.py",
     '''"SELECT id, route_team, route_kind, route_selected FROM work "
            "WHERE status='open' AND ready=1 AND phase='queued' "''',
     '''"SELECT id, route_team, route_kind, route_selected FROM work "
            "WHERE ready=1 AND phase='queued' "'''),

    ("the route is not resolved to this member", "projection.py",
     "        if viewer_member in resolved[key]:", "        if True:"),

    ("the explicit route selection is ignored", "projection.py",
     "        key = (row[\"route_team\"], row[\"route_kind\"], "
     "row[\"route_selected\"])",
     "        key = (row[\"route_team\"], row[\"route_kind\"], None)"),

    ("the roll-up stops at the first ancestor", "projection.py",
     "            below[current] = below.get(current, 0) + 1\n"
     "            current = parents.get(current)",
     "            below[current] = below.get(current, 0) + 1\n"
     "            current = None"),

    ("a row counts itself as its own descendant", "projection.py",
     "        current = parents.get(work_id)",
     "        current = work_id"),

    ("the total is summed over rows instead of the set", "projection.py",
     '\t        "actionable_for_viewer": len(claimable),',
     '\t        "actionable_for_viewer": sum(\n'
     '\t            1 + one["actionable_descendants"] for one in rows),'),

    ("active-trail rows lose the facts", "projection.py",
     "					viewer_actionable=claim[\"id\"] in claimable,\n"
     "					actionable_descendants=below.get(claim[\"id\"], 0))",
     "					viewer_actionable=False,\n"
     "					actionable_descendants=0)"),

    ("the flattened view drops the breadcrumb", "projection.py",
     '                     "breadcrumb": breadcrumb(store, row["id"])}',
     '                     "breadcrumb": []}'),

    ("the flattened view is not the same predicate", "projection.py",
     "            if row[\"id\"] not in claimable:\n                continue",
     "            pass"),

    ("the endpoint resolution is not memoized", "projection.py",
     "        if key not in resolved:", "        if True:"),

    # --- 2026-08-28, the independent review's [P1]: the continuation ------
    # Each of these breaks ONE rule the corrected paging rests on. They are
    # separate because they fail differently, and a single "paging is wrong"
    # mutation would have said which of the four was actually measured.

    ("the continuation is ignored and every page is page one",
     "projection.py",
     "            if since is not None and _position(row) <= since[\"position\"]:\n"
     "                continue",
     "            if False:\n                continue"),

    ("the page walks a partial order, so a tied position is skipped",
     "projection.py",
     '\treturn (row["order_priority"], row["order_blocking"],\n'
     '\t        row["created_seq"], row["id"])',
     '\treturn (row["order_priority"], row["order_blocking"],\n'
     '\t        row["created_seq"], "")'),

    ("a continuation this authority never minted is answered with page one",
     "projection.py",
     "	if not isinstance(token, str):\n		raise broken",
     "	if not isinstance(token, str):\n		return None"),

    ("a token from a superseded scheme is read as a current one",
     "projection.py",
     "	if len(parts) != _CURSOR_MEMBERS or parts[0] != _CURSOR_SCHEME:\n"
     "		raise broken",
     "	if len(parts) != _CURSOR_MEMBERS:\n		raise broken"),

    ("no page ever offers a continuation",
     "projection.py",
     '            "next_after": _cursor(page[-1], viewer_team, viewer_member)\n'
     '            if remaining else None,',
     '            "next_after": None,'),

    ("the page reads one row past its own limit", "projection.py",
     "            if len(page) == limit:",
     "            if len(page) == limit + 1:"),

    # --- 2026-08-28, the re-review's [P1]: shape is not provenance --------
    ("a well-shaped cursor is never bound to a Work at all", "projection.py",
     "        _cursor_bound(store, since)\n", "        pass\n"),

    ("the cursor's Work is looked up but its position is not compared",
     "projection.py",
     "\tif row is None or _position(row) != wanted:",
     "\tif row is None:"),

    ("a cursor naming no Work at all is followed", "projection.py",
     "\tif row is None or _position(row) != wanted:",
     "\tif row is not None and _position(row) != wanted:"),

    # The binding must NOT be written against the actionable set: a claimed
    # or rerouted row is exactly the ordinary continuation this feature
    # exists for, and binding to claimability would refuse it.
    ("the binding is written against the actionable set", "projection.py",
     '\t\tf"SELECT id, created_seq, {WORK_ORDER_KEY} FROM work WHERE id=?",',
     '\t\tf"SELECT id, created_seq, {WORK_ORDER_KEY} FROM work WHERE id=? "\n'
     '\t\t"AND handler_team IS NULL AND phase=\'queued\'",'),

    # --- 2026-08-28, the third review's [P1]: whose question is this -----
    ("the continuation is not bound to its participant view",
     "projection.py",
     "\tif since[\"viewer\"] != (viewer_team, viewer_member):",
     "\tif False:"),

    ("the view check is skipped for the call that reads the cursor",
     "projection.py",
     "    _cursor_view(since, viewer_team, viewer_member)\n",
     "    pass\n"),

    ("the token carries a viewer it does not read back", "projection.py",
     '\traw = "\\x1f".join((_CURSOR_SCHEME, viewer_team, viewer_member,',
     '\traw = "\\x1f".join((_CURSOR_SCHEME, "any", "one",'),

    # A shape change without a scheme change is the silent-misread case the
    # tag exists to stop, so the tag has to actually move with the shape.
    ("the scheme did not move with the shape", "projection.py",
     '_CURSOR_SCHEME = "w2"', '_CURSOR_SCHEME = "w1"'),
]


def run():
    return subprocess.run(
        [str(HOME / ".venv" / "bin" / "python3"), "-m", "pytest", "-q", *MODULES],
        cwd=HOME, capture_output=True, timeout=900)


def drop_cache():
    for c in (HOME / "src").rglob("__pycache__"): shutil.rmtree(c, ignore_errors=True)
    for c in (HOME / "tests").rglob("__pycache__"): shutil.rmtree(c, ignore_errors=True)


def main():
    drop_cache(); base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stdout.decode()[-2500:]); return 1
    missed = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where; original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x"); missed.append(name); continue
        place.write_text(original.replace(before, after)); drop_cache()
        try: found = run()
        finally: place.write_text(original); drop_cache()
        if found.returncode == 0:
            if name in EXPECTED:
                print(f"[expected-unseen] {name}")
                continue
            print(f"[UNSEEN] {name}"); missed.append(name)
        else:
            out = found.stdout.decode()
            f = [l.split("::")[-1].split()[0] for l in out.splitlines() if l.startswith("FAILED")]
            print(f"[caught] {name}\n         {', '.join(f)[:120]}")
    print()
    if missed:
        print(f"{len(missed)} UNESTABLISHED:"); [print(" -", o) for o in missed]; return 1
    caught = len(MUTATIONS) - len(EXPECTED)
    print(f"{caught} of {len(MUTATIONS)} mutations caught; "
          f"{len(EXPECTED)} expected-unseen and named above")
    return 0


if __name__ == "__main__":
    sys.exit(main())
