"""Bounded fake-instance proof of `check-policy-pin.sh`. W202663, review208585 [R2].

WHY A FAKE INSTANCE. The review requires the corrected pin command verified
"with a bounded fake-instance/read-only test so no actual installation is
required". So this builds the three files the pin check reads -- an
`authority-identity.json`, a real (tiny) Authority store made through the
public `Authority.create`, and a `deployment.json` carrying the pin -- under a
temporary directory, and runs the ACTUAL script the owner will run, as a
subprocess, against that path.

WHAT IT PROVES. Three things, each the exact defect or gate review208585
names:

  1. the command answers for the instance IT WAS GIVEN -- the reported
     instance and authority are the fake's, and the historical
     claim208217 instance appears nowhere in the output, so
     `select_instance` really ran before the pin was read;
  2. equality passes: a deployment whose pin equals the Authority's
     generation exits 0;
  3. inequality REFUSES: a moved pin exits nonzero with the refusal on
     stderr, rather than printing `equal: false` and continuing.

WHAT IT TOUCHES. Only its own temporary directory. No real instance is opened,
nothing is installed, and the retained `selected-instance.txt` is neither read
(the instance is passed explicitly) nor written.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")
PYTHON = REPO / "v12/python"
sys.path.insert(0, str(PYTHON))
sys.path.insert(0, str(PYTHON / "src"))

# A fake identity in the same 32-lowercase-hex shape a real install persists.
UUID = "f202663f" + "0" * 20 + "8647"
HISTORICAL = "instance-2026-09-19T02-05-20Z"


def fake_instance(root, *, pin):
    """The minimum a pin check reads, made through public operations."""
    from baton_v12.authority.api import Authority

    place = Path(root) / "fake-instance"
    (place / "db").mkdir(parents=True)
    (place / "authority-identity.json").write_text(json.dumps(
        {"schema": "baton.v12.instance-identity/1",
         "authority_uuid": UUID}, indent=1) + "\n")
    authority = Authority.create(str(place / "db/authority.sqlite3"),
                                 authority_uuid=UUID)
    held = authority.policy_generation()
    dispose = getattr(authority, "dispose", None)
    if dispose is not None:
        dispose()
    (place / "deployment.json").write_text(json.dumps(
        {"policy_generation": held if pin == "equal" else held + 1},
        indent=1) + "\n")
    return place, held


def run(instance):
    return subprocess.run(
        ["bash", str(HERE / "check-policy-pin.sh"), str(instance)],
        capture_output=True, text=True, timeout=120)


def main():
    failures = []

    with tempfile.TemporaryDirectory(prefix="w202663-pin-") as root:
        place, held = fake_instance(root, pin="equal")
        done = run(place)
        answered = json.loads(done.stdout or "{}")
        checks = [
            ("equal pin exits 0", done.returncode == 0),
            ("answer says equal", answered.get("equal") is True),
            ("configured pin is the fake's own",
             answered.get("configured_pin") == held),
            ("generation is the fake authority's",
             answered.get("authority_generation") == held),
            ("the instance answered for is the fake",
             answered.get("instance") == str(place)),
            ("the authority answered for is the fake's",
             answered.get("authority_uuid") == UUID),
            ("the historical instance appears nowhere",
             HISTORICAL not in done.stdout + done.stderr),
        ]
        for name, passed in checks:
            print(("ok   " if passed else "FAIL ") + name)
            if not passed:
                failures.append((name, done))

    with tempfile.TemporaryDirectory(prefix="w202663-pin-") as root:
        place, held = fake_instance(root, pin="moved")
        done = run(place)
        checks = [
            ("moved pin exits nonzero", done.returncode == 1),
            ("the refusal is on stderr, by name",
             "REFUSED" in done.stderr and "recompose" in done.stderr),
        ]
        for name, passed in checks:
            print(("ok   " if passed else "FAIL ") + name)
            if not passed:
                failures.append((name, done))

    if failures:
        for name, done in failures:
            print(f"\n-- {name}: exit {done.returncode}\nstdout: "
                  f"{done.stdout}\nstderr: {done.stderr}", file=sys.stderr)
        return 1
    print("all pin-command checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
