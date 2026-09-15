"""Independent memo isolation/materialization probe, with no live child.

The missing harness on a shared base is supplied through the production
`adding` operand, exactly the causal observer's base case. Git materialization
is simulated at its boundary; the production failure key/run code is unchanged.
"""
import json
import pathlib
import subprocess
import tempfile
from unittest.mock import patch
from tools import stage_execution as stage

calls = []
archives = []
retained = {}

def archive(runner, repository, revision, where):
    archives.append({"repository": repository, "revision": revision, "where": where})

def run(argv, **options):
    body = (pathlib.Path(options["cwd"]) / "harness.py").read_text()
    calls.append({"body": body, "seconds": options["timeout"]})
    raise subprocess.TimeoutExpired(argv, options["timeout"])

with tempfile.TemporaryDirectory(prefix="w156162-review-157602-") as root:
    with patch.object(stage, "_materialize", archive), patch.object(subprocess, "run", run):
        observed = []
        for label, body in [("first-harness", "# first\n"), ("repeat", "# first\n"), ("different-harness", "# corrected\n")]:
            owner = stage._ConfiguredExecution("baton.observer", ["python3", "harness.py"], None, root, seconds=77, retention=retained)
            before = len(calls)
            try:
                owner._run("/same-source-line", "a" * 40, adding=body)
            except Exception as failed:
                observed.append({"case": label, "new_child_calls": len(calls)-before, "refusal": str(failed)})
        print(json.dumps({"case": "memo-harness-collision", "observed": observed, "calls": calls,
                          "materializations": len(archives), "retained_scratch_directories": len(list(pathlib.Path(root).iterdir())),
                          "keys": list(retained)}, indent=2))
