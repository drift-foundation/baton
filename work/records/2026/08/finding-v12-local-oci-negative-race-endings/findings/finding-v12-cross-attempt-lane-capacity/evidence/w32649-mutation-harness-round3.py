"""W32649 round 3 — the two remaining lane reads, measured by removal."""
import pathlib, re, subprocess, sys

LANES = pathlib.Path("src/baton_v12/worker_manager/lanes.py")
SUITE = "tests.manager.test_runtime_lane"

MUTATIONS = [
    ("the predecessor read owns the whole relation",
     '''    found = connection.execute(
        "SELECT * FROM runtime_lanes "
        "WHERE authority_uuid = ? AND work_id = ? AND holder <> ?",
        (reference["authority_uuid"], reference["work_id"],
         attempt_id)).fetchall()
    if not found:
        return
    holder = _adopted(found[0])''',
     '''    found = connection.execute(
        "SELECT lane_id, holder, reason FROM runtime_lanes "
        "WHERE authority_uuid = ? AND work_id = ? AND holder <> ?",
        (reference["authority_uuid"], reference["work_id"],
         attempt_id)).fetchall()
    if not found:
        return
    holder = found[0]'''),
    ("the race-loser read owns the whole relation",
     '''        held = connection.execute(
            "SELECT * FROM runtime_lanes WHERE lane_id = ?",
            (name,)).fetchone()
        if held is not None:
            held = _adopted(held)''',
     '''        held = connection.execute(
            "SELECT holder, reason FROM runtime_lanes WHERE lane_id = ?",
            (name,)).fetchone()'''),
]


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", SUITE],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin",
             "PYTHONDONTWRITEBYTECODE": "1"})


def failures(output):
    return sorted(set(re.findall(r"^(?:FAIL|ERROR): \S+ \(([^)]+)\)", output,
                                 re.MULTILINE)))


original = LANES.read_text()
base = run()
print("BASELINE:", base.stderr.strip().splitlines()[-1])
if "OK" not in base.stderr:
    raise SystemExit("baseline is not green; the harness measures nothing")
unmeasured = []
try:
    for what, before, after in MUTATIONS:
        if original.count(before) != 1:
            print(f"\n!! NOT APPLICABLE: {what} ({original.count(before)})")
            unmeasured.append(what)
            continue
        LANES.write_text(original.replace(before, after))
        result = run()
        named = failures(result.stderr)
        print(f"\n-- reverted: {what}")
        print(f"   {result.stderr.strip().splitlines()[-1]}")
        for name in named:
            print(f"   FAILS: {name}")
        if not named:
            print("   MEASURED ZERO")
            unmeasured.append(what)
        LANES.write_text(original)
finally:
    LANES.write_text(original)
print(f"\n{len(MUTATIONS) - len(unmeasured)}/{len(MUTATIONS)} named a case")
print("RESTORED:", run().stderr.strip().splitlines()[-1])
