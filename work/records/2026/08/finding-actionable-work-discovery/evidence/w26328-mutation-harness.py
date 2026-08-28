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
