"""Mutate production `_observed_readable`; report which cases catch each one.

Runs against a WRITABLE COPY of the retained candidate. The retained custody
tree and the canonical checkout are never opened for writing here.

Usage: python3 mutation_check.py CANDIDATE_ROOT WORK_ROOT
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

PREFLIGHT = "v12/spike/ping-pong/preflight.py"
HARNESS = "v12/spike/ping-pong/test_harness.py"

MUTATIONS = [
    ("the nominated engine is replaced by the literal current value",
     '[engine, "run", "--rm", "--user",',
     '["docker", "run", "--rm", "--user",'),
    ("network isolation is dropped",
     '"--network", "none",\n', ''),
    ("the bind stops being read-only",
     ',target=/probe,readonly=true"', ',target=/probe"'),
    ("the container identity becomes root",
     '"--rm", "--user", f"{CONTAINER_UID}:{CONTAINER_GID}",',
     '"--rm", "--user", "0:0",'),
    ("the answer is no longer read from stdout",
     'found.stdout.strip() == "readable"', 'True'),
    ("a probe that did not run is reported as an unreadable verdict",
     '''return {"probed": False,
                "why": "the probe container did not run",
                "status": found.returncode}''',
     '''return {"probed": True, "readable": False,
                "status": found.returncode}'''),
    ("the absent-path short circuit is removed",
     '''    if not os.path.exists(place):
        return {"probed": False, "why": "the path is not there to probe"}
''', ''),
]

CASE = re.compile(r"^(FAIL|ERROR): (\w+) \(([\w.]+)\)")


def failures(root):
    done = subprocess.run(["python3", HARNESS], cwd=root,
                          capture_output=True, text=True, timeout=600)
    caught = sorted({found.group(2)
                     for found in (CASE.match(line)
                                   for line in done.stderr.splitlines())
                     if found})
    return done.returncode, caught


def main(argv):
    candidate, work = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(candidate, work)
    for member in work.rglob("*"):
        member.chmod(0o755 if member.is_dir() else 0o644)
    original = (work / PREFLIGHT).read_text(encoding="utf-8")

    baseline_status, baseline_caught = failures(work)
    report = {"baseline": {"status": baseline_status,
                           "failing": baseline_caught},
              "mutations": []}
    for why, before, after in MUTATIONS:
        if original.count(before) != 1:
            report["mutations"].append(
                {"mutation": why, "applied": False,
                 "why": f"the anchor appears {original.count(before)} times"})
            continue
        (work / PREFLIGHT).write_text(original.replace(before, after),
                                      encoding="utf-8")
        try:
            status, caught = failures(work)
        finally:
            (work / PREFLIGHT).write_text(original, encoding="utf-8")
        report["mutations"].append(
            {"mutation": why, "applied": True, "status": status,
             "caught_by": [name for name in caught
                           if name not in baseline_caught],
             "already_failing": baseline_caught})
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
