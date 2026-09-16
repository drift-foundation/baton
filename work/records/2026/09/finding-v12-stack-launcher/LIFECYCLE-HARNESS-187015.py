"""W183883 — the retained, reproducible installed-lifecycle harness.

Review 2026-09-16T14-06-35Z asked for the harness itself, with exact argv, cwd,
environment, timeouts and cleanup, and the fixture digest mapping, kept beside
its outputs. This is that harness: every command it runs is recorded as the
argv it ran, from the cwd it ran in, under the environment it was given.

WHAT IT NEEDS, and what it does NOT do:

  * a built bundle (`just build` from v12/) and two installed destinations,
    prepared by `just bootstrap <inputs> <destination> <distro>`. It installs
    nothing itself.
  * it submits no Job, contacts no provider, runs no engine, reads no owner
    credential registry and performs no version-control operation.
  * the fixture inputs it maps are the ones this claim composed under LIVE;
    their digests are recorded so a later reader can tell whether the
    deployment described here is the one they are holding.

    python3 LIFECYCLE-HARNESS-187015.py > LIFECYCLE-187015.json
"""
import hashlib
import json
import os
import pathlib
import subprocess
import time

LIVE = pathlib.Path(os.environ.get("W183883_LIVE",
                                   "/var/tmp/w183883-live-186890"))
A = LIVE / "deployment"
B = LIVE / "deployment-b"
DISTRO = os.environ.get("W183883_DISTRO",
                        "/home/sl/src/baton/v12/python/build/out/distro")

# THE ENVIRONMENT IS THE CLAIM. An installed deployment reads nothing from the
# development checkout: no PYTHONPATH, no BATON_V12_* operand, no virtual
# environment on PATH. HOME is given because a process is entitled to one.
ENVIRONMENT = {"HOME": "/root", "PATH": "/usr/bin:/bin"}
CWD = "/"
TIMEOUT = 300           # seconds, per command
MONITOR_TICKS = ("--interval", "0.2", "--ticks", "2")

ran = []


def digest(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def run(argv, *, timeout=TIMEOUT):
    started = time.monotonic()
    done = subprocess.run([str(one) for one in argv], capture_output=True,
                          text=True, timeout=timeout, cwd=CWD,
                          env=dict(ENVIRONMENT))
    answer = {"argv": [str(one) for one in argv], "cwd": CWD,
              "env": dict(ENVIRONMENT), "timeout_seconds": timeout,
              "exit": done.returncode, "seconds": round(time.monotonic() - started, 3),
              "stdout": done.stdout.strip().splitlines(),
              "stderr": done.stderr.strip().splitlines()[-3:]}
    ran.append(answer)
    return answer


def stack(root, verb, *operands):
    return run([root / "distro" / "baton-v12-stack", verb, "--instance",
                root / "instance.json", *operands])


def main():
    started = time.monotonic()
    record = {"how": "every command below was run from " + CWD + " with an "
              "environment of exactly " + json.dumps(ENVIRONMENT) + ": no "
              "PYTHONPATH, no BATON_V12_* operand, no virtual environment, "
              "nothing from the checkout"}
    told = run([A / "distro" / "baton-v12-stack", "identity"])
    record["identity"] = json.loads("\n".join(told["stdout"]))
    record["start_a"] = stack(A, "start")
    record["start_b"] = stack(B, "start")
    record["a_status"] = stack(A, "status")
    record["b_status"] = stack(B, "status")
    record["isolation"] = {
        "a_stores": sorted(os.listdir(A / "db")),
        "b_stores": sorted(os.listdir(B / "db")),
        "distinct_state_roots": [str(A / "state"), str(B / "state")],
        "distinct_stores": [str(A / "db"), str(B / "db")]}
    record["monitor_a"] = stack(A, "monitor", *MONITOR_TICKS)
    record["repository_a"] = stack(A, "repository")
    record["repository_b"] = stack(B, "repository")
    record["cross_instance_is_refused"] = run(
        [A / "distro" / "baton-v12-stack", "status", "--instance",
         B / "instance.json"])

    before = (A / "instance.json").read_bytes()
    record["repeat_is_refused"] = run(
        [A / "distro" / "baton-v12-stack", "bootstrap", "--inputs",
         LIVE / "inputs.json", "--destination", A, "--distro", DISTRO])
    record["repeat_is_refused"]["selector_unchanged"] = (
        (A / "instance.json").read_bytes() == before)

    kept = (B / "instance.json").read_bytes()
    (B / "instance.json").write_bytes(b"{ not a document")
    record["corrupt_selector_is_refused"] = stack(B, "status")
    (B / "instance.json").write_bytes(kept)
    record["restored_selector_works"] = stack(B, "status")

    record["stop_a"] = stack(A, "stop")
    record["stop_b"] = stack(B, "stop")
    time.sleep(0.5)
    record["after_stop"] = {"a": stack(A, "status"), "b": stack(B, "status")}

    # THE MISMATCH IS DONE STOPPED, DELIBERATELY. An earlier attempt rewrote a
    # library the RUNNING manager had mapped and killed it: the refusal was
    # real and so was the crash, and reporting them together would report the
    # harness's own doing as a product property.
    library = B / "distro" / "_internal" / "libpython3.13.so.1.0"
    held = library.read_bytes()
    library.write_bytes(held[:-1] + bytes([held[-1] ^ 0xFF]))
    record["changed_runtime_is_refused"] = {"status": stack(B, "status"),
                                            "start": stack(B, "start")}
    library.write_bytes(held)
    record["restored_runtime_is_accepted"] = stack(B, "status")

    # CLEANUP: everything this harness started, it stopped. Nothing is removed
    # -- the destinations are the evidence -- and nothing owned is left alive.
    alive = subprocess.run(
        ["bash", "-lc", "pgrep -f 'baton-v12-stack (manager|publish)' || true"],
        capture_output=True, text=True, timeout=60)
    record["cleanup"] = {
        "both_instances_stopped": (record["stop_a"]["exit"] == 0
                                   and record["stop_b"]["exit"] == 0),
        "no_owned_child_left_running": alive.stdout.strip() == "",
        "nothing_removed": "the destinations and the fixture roots are retained",
        "tampered_library_restored": library.read_bytes() == held}

    fixtures = {}
    for name in ("inputs.json", "inputs-b.json", "credential-sources.json",
                 "fixture-credential.txt"):
        place = LIVE / name
        if place.exists():
            fixtures[str(place)] = {"sha256": digest(place),
                                    "bytes": place.stat().st_size,
                                    "mode": oct(place.stat().st_mode & 0o777)}
    record["fixtures"] = {
        "digests": fixtures,
        "what_they_are": "an inputs document per instance, composed from the "
                         "accepted stage fixtures; a FIXTURE credential "
                         "registry naming a fixture bearer file. No owner "
                         "registry was read and no provider was contacted.",
        "retained_fixture_material": (LIVE / "fixture-root.txt").read_text().split()
        if (LIVE / "fixture-root.txt").exists() else []}

    print(json.dumps({"record": record, "commands": ran,
                      "seconds": round(time.monotonic() - started, 3),
                      "harness": __file__},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
