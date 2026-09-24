"""This claim's two measured runs, with their receipts written beside them.

The dossier's receipt shape is one document per COMMAND, so this runs each of
the two and writes `verification-22` and `verification-23`. It measures; it
asserts nothing about the result beyond recording the exit status, which is
what every earlier receipt here does.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
DISTRIBUTION = CHECKOUT / "v12" / "python"
SNAPSHOT = "/home/sl/baton-runs/independent-review-247947/manager-source"

RUNS = (
    # THE EXISTING SUITE, on the environment its own receipts name, so a green
    # result here is comparable with verification-18 and -20 rather than a
    # different measurement wearing their name.
    (22, {"cwd": str(DISTRIBUTION),
          "pythonpath": os.pathsep.join(["src", ".", str(HERE)]),
          "argv": ["-m", "unittest", "-v", "test_supervisor",
                   "test_packet_bindings", "test_generated_packet"]}),
    # THIS CLAIM'S CHECKS, bound to the PINNED SNAPSHOT: they read a store the
    # snapshot's own manager wrote, and reading it with the checkout would be
    # reporting a different product's answer about it.
    (23, {"cwd": str(HERE),
          "pythonpath": os.pathsep.join([SNAPSHOT, str(HERE)]),
          "argv": ["-m", "unittest", "-v", "test_resume_state"]}),
)


def main():
    held = []
    for number, one in RUNS:
        argv = [sys.executable, "-B", *one["argv"]]
        started = time.perf_counter()
        answer = subprocess.run(
            argv, cwd=one["cwd"], capture_output=True, text=True, timeout=1800,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=one["pythonpath"]))
        elapsed = time.perf_counter() - started
        (HERE / f"verification-{number}.log").write_text(
            answer.stdout + answer.stderr, encoding="utf-8")
        receipt = {"argv": argv, "cwd": one["cwd"],
                   "pythonpath": one["pythonpath"],
                   "seconds": elapsed, "status": answer.returncode,
                   "timeout": False, "claim": 250376, "work": "W236087",
                   "participant": "baton.claude",
                   "log": f"verification-{number}.log"}
        (HERE / f"verification-{number}.json").write_text(
            json.dumps(receipt, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
        held.append({"receipt": number, "seconds": elapsed,
                     "status": answer.returncode})
    print(json.dumps(held, indent=2))
    return 0 if all(one["status"] == 0 for one in held) else 1


if __name__ == "__main__":
    raise SystemExit(main())
