"""Read-only source audit and inert parser checks; no runtime or store operations.

Exports committed v12 files into a fresh retained /tmp directory. This is
development evidence, not a launcher, installer or routine Job preparation tool.
"""
import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

START = time.monotonic()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
COMMIT = "8876bf950ff1f8ab8767ce9786df268cc9d767c6"
OLD = ROOT / "work/records/2026/10/finding-v12-shared-output-template-preparation/successor-371277"
IMAGE = ROOT / "work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-376414"

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], timeout=30)

def sha(data):
    return hashlib.sha256(data).hexdigest()

export = Path(tempfile.mkdtemp(prefix="w376804-8876bf95-"))
pins = {}
for entry in git("ls-tree", "-r", "-z", COMMIT, "--", "v12").split(b"\0"):
    if not entry:
        continue
    metadata, raw_path = entry.split(b"\t", 1)
    mode, kind, oid = metadata.decode().split()
    if kind != "blob" or mode not in ("100644", "100755"):
        raise ValueError("unsupported source entry: " + raw_path.decode())
    name = raw_path.decode()
    data = git("cat-file", "blob", oid)
    assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == oid
    destination = export / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    destination.chmod(int(mode[-3:], 8))
    pins[name] = sha(data)

image_check = {}
for name, expected in json.loads((IMAGE / "BUILD-INPUTS.json").read_text()).items():
    actual = pins["v12/" + name]
    image_check[name] = {"expected": expected, "actual": actual, "equal": actual == expected}
assert all(item["equal"] for item in image_check.values())

capacity = ROOT / "work/records/2026/10/finding-v12-useful-template-job-monitor/findings/finding-one-time-capacity-composition/capacity.py"
values = {}
for node in ast.parse(capacity.read_text()).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("STATEMENT", "ACCEPTANCE"):
        values[node.targets[0].id] = ast.literal_eval(node.value)
task = json.loads((OLD / "candidate/task.json").read_text())
task["declared_base"] = COMMIT
task["task_id"] = "template-job-guide-w376804"
assert task["instructions"] == values["STATEMENT"]
task_path = HERE / "TASK-377930.json"
task_path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n")

dest = "/home/sl/baton-instances/useful-template-job-w376804"
argv = ["manager", "--store", dest + "/db/jobs.sqlite3", "--incarnation", "w376804-create-1", "--authority-uuid", "0" * 32,
        "create", "--instance", dest, "--control", dest + "/db/control.sqlite3", "--authority", dest + "/db/authority.sqlite3",
        "--task", task["task_id"], "--statement", values["STATEMENT"], "--template", "baton.v12.job-template.implementation-review/1",
        "--source", "installed", "--work-scope", "v12/TEMPLATE-JOBS.md", "--job-id", "template-guide-w376804",
        "--submission-id", "template-guide-w376804-1", "--provider-turn-seconds", "3600", "--verification-command-seconds", "900"]
for criterion in values["ACCEPTANCE"]:
    argv += ["--acceptance", criterion]
vectors = [argv, ["status", "--instance", dest + "/instance.json"],
           ["monitor", "--instance", dest + "/instance.json", "--interval", "3", "--ticks", "1"],
           ["view", "--status", dest + "/state/status.json", "--job", "template-guide-w376804"],
           ["stop", "--instance", dest + "/instance.json"],
           ["manager", "settlement-preview", "--instance", dest + "/instance.json", "--job", "template-guide-w376804", "--stage", "template-guide-w376804/implementation", "--episode", "1", "--operation-id", "w376804-settle-1"],
           ["manager", "settle-stopped", "--instance", dest + "/instance.json", "--document", "request.json"],
           ["manager", "settlement-status", "--instance", dest + "/instance.json", "--document", "request.json"]]
sys.dont_write_bytecode = True
sys.path[:0] = [str(export / "v12/python/src"), str(export / "v12/python")]
from tools import stack_command

class Parsed(Exception):
    pass

original = argparse.ArgumentParser.parse_args
def inert(parser, args=None, namespace=None):
    original(parser, args, namespace)
    raise Parsed()
argparse.ArgumentParser.parse_args = inert
results = []
try:
    for vector in vectors:
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                stack_command.main(vector)
        except Parsed:
            results.append({"argv": vector, "syntax": "accepted; stopped immediately after parsing"})
        else:
            raise RuntimeError("expected parser boundary")
finally:
    argparse.ArgumentParser.parse_args = original

report = {"commit": COMMIT, "source_export": str(export), "source_files": len(pins),
          "source_sha256": pins, "image_build_inputs": image_check, "parser_checks": results,
          "task_sha256": sha(task_path.read_bytes()), "task_delta": ["declared_base", "task_id"],
          "statement": values["STATEMENT"], "acceptance": values["ACCEPTANCE"],
          "template_guide_exists": "v12/TEMPLATE-JOBS.md" in pins,
          "elapsed_seconds": time.monotonic() - START,
          "limitations": "No store, engine, build, install or provider call. Zero UUID and episode1 are parser-only placeholders, never minted identity. Export is not a Git transport repository. Parser acceptance is not admission, runtime or package qualification."}
(HERE / "CHECK-377930.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({key: report[key] for key in ("source_export", "source_files", "task_sha256", "elapsed_seconds")}))
print("Image inputs equal: " + str(len(image_check)) + "; inert parser checks: " + str(len(results)))
