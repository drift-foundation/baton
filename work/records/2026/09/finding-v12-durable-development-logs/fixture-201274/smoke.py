"""W198667 claim201274 — the capture, proved in a REAL container.

WHAT THIS ESTABLISHES that a unit case cannot: that the room the manager makes
is the room the container writes into, through an actual bind at the actual
target, with the actual fixed non-root uid -- and that a worker refused at
startup leaves its diagnostic BEHIND rather than only on a terminal nobody kept.

WHAT IT IS NOT. No live model, no provider, no network. The image is this Work's
labelled fixture; the accepted production images are neither used nor rebuilt.

The composition comes from the manager's own functions: the room from
`attempt_logs.materialize`, the bind from `AttemptLogs.mounts`, the restrictions
from `oci.RESTRICTIONS` -- so what is proved is this deployment's rules rather
than this script's idea of them.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

IMAGE = (HERE / "build/fixture.iid").read_text().strip()

from baton_v12.worker_manager import (ControlStore, attempt_logs,  # noqa: E402
                                      configure_workspace_group,
                                      configured_workspace_group, oci)


def ran(argv, **kwargs):
    return subprocess.run(argv, capture_output=True, text=True, timeout=120,
                          **kwargs)


def main():
    home = tempfile.mkdtemp(prefix="w198667-smoke-201274-")
    found = {"schema": "baton.w198667.capture-smoke/1", "claim": 201274,
             "image": IMAGE, "checks": []}

    def check(what, answer, detail=None):
        found["checks"].append({"check": what, "held": bool(answer),
                                "detail": detail})

    try:
        root = os.path.join(home, "logs")
        os.makedirs(root)
        control = ControlStore.open(os.path.join(home, "control.sqlite3"),
                                    incarnation="i-1",
                                    clock=lambda: "2026-09-18T00:00:00.000Z")
        try:
            configure_workspace_group(control, os.getgid())
            group = configured_workspace_group(control)
        finally:
            control.close()
        delivery = attempt_logs.materialize(root, attempt_id="attempt-smoke",
                                            workspace_group=group)

        # THE BIND IS THE DELIVERY'S OWN, held by the adapter's own boundary.
        bind = oci._log_mounts(list(delivery.mounts()))
        check("the adapter's boundary accepts the delivery's own bind",
              bind == ((delivery.log_root, attempt_logs.LOG_TARGET, True),),
              list(bind))

        source, target, writable = bind[0]
        # THE DEPLOYMENT'S OWN TABLE, flattened the way the adapter does: each
        # entry is a flag and its value, and `None` means the flag stands
        # alone. A smoke that confined itself with this record's idea of the
        # rules would prove nothing about the deployment's.
        confined = []
        for flag, value in oci.RESTRICTIONS:
            confined.append(flag)
            if value is not None:
                confined.append(value)

        # A LAUNCH THE WORKER CANNOT READ, which is the reported incident's own
        # shape: a document naming a generation this worker does not speak.
        launch = os.path.join(home, "launch")
        os.makedirs(launch)
        with open(os.path.join(launch, "launch.json"), "w") as handle:
            json.dump({"schema": "baton.worker-launch/9",
                       "session": "session-smoke",
                       "contract": "v12-assignment-1",
                       "role": "implementation",
                       "transport": "baton.worker-exchange/1"}, handle)

        # THE SHARE IN THE ROOM'S GROUP, which is how the adapter grants it:
        # `run_vector` composes `--group-add` from the deployment's configured
        # workspace group, because the container's fixed uid is not this
        # manager's and a room it cannot write is a room it cannot log to. A
        # first run of this smoke omitted it and captured nothing -- which is
        # the delivery behaving correctly over a bind the container had no
        # share in, rather than a capture defect.
        argv = ["docker", "run", "--rm", "--name", "baton-w198667-smoke",
                "--group-add", str(group.gid),
                *confined,
                "-v", f"{source}:{target}:rw",
                "-v", f"{launch}/launch.json:/run/baton/launch.json:ro",
                IMAGE]
        answer = ran(argv)
        check("the container refused the launch and exited 3",
              answer.returncode == 3,
              {"returncode": answer.returncode,
               "stderr": (answer.stderr or "")[:400]})
        check("its diagnostic reached the terminal, as it already did",
              "baton-worker:" in (answer.stderr or ""),
              (answer.stderr or "")[:200])

        # THE FINDING THIS WORK EXISTS FOR: the same sentence is now ON DISK,
        # in the manager's own room, readable after the container is gone.
        retained = attempt_logs.read(delivery, "worker.stderr")
        check("the wrapper's earliest output was RETAINED in the room",
              "baton-worker:" in retained["text"], retained["text"][:300])
        check("and it is reported as a whole capture rather than a guess",
              retained["state"] in ("captured", "live"), retained["state"])
        check("its writer's own word was recorded",
              retained["declaration"] == "declared", retained["declaration"])

        # AND THE STREAMS NOBODY WROTE ARE ABSENT, never empty.
        picture = attempt_logs.locators(delivery)
        states = {one["stream"]: one["state"] for one in picture["streams"]}
        check("a stream nobody wrote is ABSENT and not an empty success",
              states.get("provider.stdout") == "absent", states)
        check("the container is gone and the evidence is not",
              ran(["docker", "ps", "-a", "--filter",
                   "name=baton-w198667-smoke", "--format",
                   "{{.ID}}"]).stdout.strip() == ""
              and os.path.exists(delivery.place("worker.stderr")))

        found["all_true"] = all(one["held"] for one in found["checks"])
        found["locators"] = picture
        (HERE / "build/smoke.json").write_text(
            json.dumps(found, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"image": IMAGE, "all_true": found["all_true"],
                          "failed": [one["check"] for one in found["checks"]
                                     if not one["held"]]}, indent=1))
        return 0 if found["all_true"] else 1
    finally:
        shutil.rmtree(home, True)


if __name__ == "__main__":
    sys.exit(main())
