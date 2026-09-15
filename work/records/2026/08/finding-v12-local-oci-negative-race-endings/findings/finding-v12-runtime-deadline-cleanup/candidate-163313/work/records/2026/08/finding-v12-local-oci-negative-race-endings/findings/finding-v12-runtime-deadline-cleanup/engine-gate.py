"""W32577 gate supervisor. Prepared only; real execution requires a later assignment.

The child owns test assertions; this surviving parent owns container cleanup.
Run directories, logs, fixture roots and unresolved inventories remain evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

LABEL = "org.baton.w32577.gate"
SELECTOR = "tests.manager.test_runtime_deadline_engine.DeadlineDocker.test_reached_fence_exact_removal_providers_custody_and_discharge"


def durable(path, value, *, exclusive=False):
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    parent = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


class Budget:
    def __init__(self, start=None, clock=time.monotonic):
        self.clock = clock
        self.start = clock() if start is None else start
        self.total_end = self.start + 180
        self.body_end = self.start + 120

    def phase_end(self, phase):
        limits = {"reap": (5, 125), "cleanup": (50, 175), "account": (5, 180)}
        if phase == "body":
            return self.body_end
        length, absolute = limits[phase]
        return min(self.clock() + length, self.start + absolute, self.total_end)

    def allowance(self, end, *, expected=1, margin=1, maximum=30):
        remaining = min(end, self.total_end) - self.clock()
        if remaining <= expected + margin:
            raise TimeoutError("expected time plus margin cannot fit phase and total")
        return min(maximum, remaining - margin)


class Inventory:
    def __init__(self, root, run_id):
        self.root = Path(root)
        self.run_id = run_id

    def register(self, name):
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", name):
            raise ValueError("invalid exact owned container name")
        path = self.root / (hashlib.sha256(name.encode()).hexdigest() + ".json")
        value = {"name": name, "run_id": self.run_id}
        try:
            durable(path, value, exclusive=True)
        except FileExistsError:
            if path.is_symlink() or json.loads(path.read_text()) != value:
                raise ValueError("owned-name inventory collision")

    def names(self):
        names = []
        for path in sorted(self.root.iterdir()):
            if path.is_symlink() or not path.is_file():
                raise ValueError("invalid inventory entry type")
            value = json.loads(path.read_text())
            if set(value) != {"name", "run_id"} or value["run_id"] != self.run_id:
                raise ValueError("invalid inventory ownership")
            name = value["name"]
            if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", name):
                raise ValueError("invalid inventory name")
            if path.name != hashlib.sha256(name.encode()).hexdigest() + ".json":
                raise ValueError("invalid inventory identity")
            names.append(name)
        return names


class Calls:
    def __init__(self, root, budget, runner=subprocess.run, channel="parent"):
        self.root, self.budget, self.runner, self.channel = Path(root), budget, runner, channel
        self.sequence = 0

    def run(self, command, end):
        timeout = self.budget.allowance(end)
        self.sequence += 1
        path = self.root / f"{self.channel}-call-{self.sequence}.json"
        record = {"command": command, "expected": 1, "margin": 1, "timeout": timeout,
                  "phase_end": end, "total_end": self.budget.total_end, "state": "running"}
        durable(path, record, exclusive=True)
        start = self.budget.clock()
        try:
            # Durable guard I/O consumes the same allowance; never use stale time.
            timeout = min(timeout, self.budget.allowance(end))
            record["actual_timeout"] = timeout
            result = self.runner(command, capture_output=True, timeout=timeout)
            record.update(returncode=result.returncode,
                          stdout=result.stdout.decode("utf-8", "replace"),
                          stderr=result.stderr.decode("utf-8", "replace"), state="completed")
            return result
        except BaseException as error:
            record.update(state="failed", error=type(error).__name__ + ": " + str(error))
            raise
        finally:
            record["elapsed"] = self.budget.clock() - start
            durable(path, record)


class ChildControl:
    def __init__(self, root, *, clock=time.monotonic, runner=subprocess.run):
        self.root = Path(root)
        config = json.loads((self.root / "config.json").read_text())
        self.inventory = Inventory(self.root / "names", config["run_id"])
        self.budget = Budget(config["start"], clock)
        self.calls = Calls(self.root, self.budget, runner, "child")

    def docker(self, words):
        words = list(words)
        # Both EnginePort (runtime/custodian) and direct sibling paths cross here.
        if words and words[0] in ("create", "run"):
            if words.count("--name") != 1:
                raise ValueError("creation requires one exact registered name")
            self.inventory.register(words[words.index("--name") + 1])
            words[1:1] = ["--label", LABEL + "=" + self.inventory.run_id]
        return self.calls.run(["docker", *words], self.budget.body_end)


class OwnedProcess:
    def __init__(self, command, **kwargs):
        self.process = subprocess.Popen(command, start_new_session=True, **kwargs)

    def wait(self, timeout):
        return self.process.wait(timeout=timeout)

    def terminate(self):
        os.killpg(self.process.pid, signal.SIGTERM)

    def kill(self):
        os.killpg(self.process.pid, signal.SIGKILL)


def reap(process, budget, end):
    """Stop/reap the one session this supervisor created, within its shared slot."""
    failures = []
    for action in (process.terminate, process.kill):
        try:
            action()
        except ProcessLookupError:
            pass
        except OSError as error:
            failures.append(str(error))
        timeout = budget.allowance(end, expected=0.1, margin=0.1, maximum=2)
        try:
            process.wait(timeout=timeout)
            return failures
        except subprocess.TimeoutExpired:
            continue
    raise TimeoutError("owned child could not be reaped within reserved slot")


def inspect_owned(calls, inventory, name, end):
    result = calls.run(["docker", "container", "inspect", name], end)
    missing = "Error: No such container: " + name
    if result.returncode and result.stdout.strip() in (b"", b"[]") and result.stderr.decode().strip() == missing:
        return None
    if result.returncode:
        raise RuntimeError("cannot establish exact container identity/absence: " + name)
    rows = json.loads(result.stdout)
    if len(rows) != 1 or rows[0]["Name"] != "/" + name or rows[0]["Config"].get("Labels", {}).get(LABEL) != inventory.run_id:
        raise RuntimeError("foreign or ambiguous container: " + name)
    identity = rows[0]["Id"]
    if not re.fullmatch(r"[0-9a-f]{64}", identity):
        raise RuntimeError("invalid immutable container ID")
    return identity


def uncertain_creations(root):
    """A lost create reply cannot turn one absent observation into settlement."""
    uncertain = set()
    for path in Path(root).glob("child-call-*.json"):
        record = json.loads(path.read_text())
        command = record["command"]
        if len(command) > 1 and command[1] in ("create", "run") and "--name" in command:
            if record["state"] != "completed" or record["returncode"] != 0:
                uncertain.add(command[command.index("--name") + 1])
    return uncertain


def cleanup(inventory, calls, end, uncertain=()):
    resolved, unresolved, errors = [], [], []
    for name in inventory.names():
        try:
            identity = inspect_owned(calls, inventory, name, end)
            if identity is None and name in uncertain:
                raise RuntimeError("creation outcome unresolved despite current absence: " + name)
            if identity is not None:
                removed = calls.run(["docker", "rm", "--force", identity], end)
                if removed.returncode:
                    raise RuntimeError("exact owned container removal failed: " + name)
                if inspect_owned(calls, inventory, name, end) is not None:
                    raise RuntimeError("container remains after removal: " + name)
            resolved.append(name)
        except Exception as error:
            unresolved.append(name)
            errors.append(type(error).__name__ + ": " + str(error))
    return {"resolved": resolved, "unresolved": unresolved, "errors": errors}


def supervise(root, command, *, clock=time.monotonic, runner=subprocess.run, process_factory=OwnedProcess, env=None, cwd=None):
    root = Path(root)
    budget = Budget(clock=clock)
    root.mkdir()  # A new, exact run directory; never adopt somebody else's inventory.
    (root / "names").mkdir()
    (root / "fixtures").mkdir()
    run_id = uuid.uuid4().hex
    durable(root / "config.json", {"run_id": run_id, "start": budget.start}, exclusive=True)
    inventory = Inventory(root / "names", run_id)
    calls = Calls(root, budget, runner)
    result = {"body_returncode": None, "body_error": None, "reap_errors": [], "cleanup": None, "phases": {}}
    process = None
    reaped = False
    try:
        timeout = budget.allowance(budget.body_end, maximum=120)
        durable(root / "body-guard.json", {"expected": 1, "margin": 1, "timeout": timeout,
                "body_end": budget.body_end, "total_end": budget.total_end}, exclusive=True)
        with (root / "body.log").open("wb") as output:
            budget.allowance(budget.body_end)
            process = process_factory(command, stdout=output, stderr=subprocess.STDOUT, cwd=cwd,
                env={**(os.environ if env is None else env), "BATON_W32577_GATE_DIR": str(root.resolve()),
                     "TMPDIR": str((root / "fixtures").resolve()), "PYTHONDONTWRITEBYTECODE": "1"})
            result["body_returncode"] = process.wait(timeout=budget.allowance(budget.body_end, maximum=120))
            reaped = True
    except BaseException as error:
        result["body_error"] = type(error).__name__ + ": " + str(error)
    finally:
        result["phases"]["body"] = {"start": budget.start, "elapsed": clock() - budget.start, "end": budget.body_end}
        phase_start, phase_end = clock(), budget.phase_end("reap")
        if process is not None and not reaped:
            try:
                durable(root / "reap-guard.json", {"expected": 0.1, "margin": 0.1,
                        "phase_end": phase_end, "total_end": budget.total_end}, exclusive=True)
                result["reap_errors"] = reap(process, budget, phase_end)
                reaped = True
            except Exception as error:
                result["reap_errors"].append(type(error).__name__ + ": " + str(error))
        result["phases"]["reap"] = {"start": phase_start, "elapsed": clock() - phase_start, "end": phase_end}
        phase_start, phase_end = clock(), budget.phase_end("cleanup")
        try:
            # No uncertain child may create resources concurrently with this sweep.
            if process is not None and not reaped:
                result["cleanup"] = {"resolved": [], "unresolved": inventory.names(),
                                     "errors": ["owned child not reaped; inventory retained"]}
            else:
                result["cleanup"] = cleanup(inventory, calls, phase_end, uncertain_creations(root))
        except Exception as error:
            result["cleanup"] = {"resolved": [], "unresolved": None,
                                 "errors": [type(error).__name__ + ": " + str(error)]}
        result["phases"]["cleanup"] = {"start": phase_start, "elapsed": clock() - phase_start, "end": phase_end}
        phase_start, phase_end = clock(), budget.phase_end("account")
        result["elapsed"] = clock() - budget.start
        result["accounting_end"] = phase_end
        result["ok"] = (result["body_returncode"] == 0 and result["body_error"] is None
                        and not result["reap_errors"] and not result["cleanup"]["errors"]
                        and not result["cleanup"]["unresolved"] and result["elapsed"] < 180
                        and all(row["start"] + row["elapsed"] <= row["end"] for row in result["phases"].values()))
        durable(root / "result.json", result, exclusive=True)
        result["phases"]["account"] = {"start": phase_start, "elapsed": clock() - phase_start, "end": phase_end}
        result["elapsed"] = clock() - budget.start
        if clock() >= phase_end:
            result["ok"] = False
            result["accounting_error"] = "final accounting exhausted reserved phase/total"
        durable(root / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    if not args.python.is_absolute() or not args.run_dir.is_absolute():
        parser.error("interpreter and fresh run directory must be absolute")
    repo = Path(__file__).resolve().parents[7]
    result = supervise(args.run_dir, [str(args.python), "-W", "error", "-m", "unittest", SELECTOR],
                       cwd=repo / "v12/python", env={**os.environ, "PYTHONPATH": str(repo / "v12/python/src")})
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
