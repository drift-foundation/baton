"""Reviewer reproductions on disposable synthetic trees only; no live roots."""
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "evidence"))
import qualification_contract as c
import qualification_worker as worker

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

evidence = json.loads((HERE / "EVIDENCE-182264.json").read_bytes())
checks = []
for row in evidence["files"]:
    for path, expected in ((HERE / row["path"], row["candidate_sha256"]), (HERE / row["retained_copy"], row["candidate_sha256"]), (HERE / "candidate-180078" / Path(row["path"]).name, row["base_sha256"])):
        actual = sha(path)
        checks.append({"path": str(path.relative_to(HERE)), "sha256": actual, "matches": actual == expected})
assert all(row["matches"] for row in checks)
before = {row["path"]: sha(HERE / row["path"]) for row in evidence["files"]}
session = "6887cfd5-e201-44ed-94eb-21d6302e13bf"
results = []
started = time.monotonic()

def mode(path):
    return oct(stat.S_IMODE(path.stat().st_mode))

for case in ("symlinked-projects-parent", "project-swapped-after-descriptor-check", "foreign-session", "nested-session", "credential-shaped-entry", "hardlinked-session"):
    with tempfile.TemporaryDirectory(prefix="w177936-review-182326-") as temporary:
        root = Path(temporary)
        home = root / "home"
        projects = home / ".claude/projects"
        project = projects / "observed"
        project.mkdir(parents=True)
        selected = project / (session + ".jsonl")
        selected.write_bytes(b"synthetic session")
        project.chmod(0o700)
        selected.chmod(0o600)
        observed = selected
        owner_open = worker._owned
        swapped = []
        if case == "symlinked-projects-parent":
            other = root / "outside-home"
            projects.rename(other)
            projects.symlink_to(other, target_is_directory=True)
            observed = other / "observed" / selected.name
        elif case == "project-swapped-after-descriptor-check":
            decoy = root / "decoy"
            decoy.mkdir()
            observed = decoy / selected.name
            observed.write_bytes(b"unselected synthetic object")
            observed.chmod(0o600)
            def owner_open(path, directory):
                answer = original_open(path, directory)
                if directory and not swapped:
                    project.rename(projects / "moved")
                    project.symlink_to(decoy, target_is_directory=True)
                    swapped.append(True)
                return answer
        elif case == "foreign-session":
            (project / "00000000-0000-4000-8000-000000000001.jsonl").write_bytes(b"foreign")
        elif case == "nested-session":
            (project / "nested").mkdir()
            (project / "nested/foreign.jsonl").write_bytes(b"foreign")
        elif case == "credential-shaped-entry":
            (project / "oauth-token").write_bytes(b"synthetic secret")
        elif case == "hardlinked-session":
            observed = root / "outside-alias"
            os.link(selected, observed)
        original_open = worker._owned
        initial = mode(observed)
        with mock.patch.object(c, "HOME", str(home)), mock.patch.object(c, "GROUP", os.getgid()), mock.patch.object(worker, "_owned", owner_open):
            try:
                published = worker.publish(session, 1)
                outcome = "published"
            except BaseException as error:
                published = None
                outcome = c.failure_code(error)
        results.append({"case": case, "outcome": outcome, "published": published, "observed_before": initial, "observed_after": mode(observed), "observed_mode_changed": initial != mode(observed), "same_uid_synthetic_fixture": True})

with tempfile.TemporaryDirectory(prefix="w177936-review-diagnostic-182326-") as temporary:
    with mock.patch.object(c.os, "scandir", side_effect=PermissionError(errno.EACCES, "PRIVATE-CANARY")):
        try:
            c.inventory(Path(temporary))
        except BaseException as error:
            detail = {"step": "source-inventory", **c.failure_detail(error)}
            results.append({"case": "coverage-EACCES-projection", "failure_code": c.failure_code(error), "failure_detail": detail, "input_errno": "EACCES", "canary_leaked": "PRIVATE-CANARY" in json.dumps(detail)})

seconds = time.monotonic() - started
after = {row["path"]: sha(HERE / row["path"]) for row in evidence["files"]}
assert before == after
record = {"claim": 182326, "checks": checks, "all_hashes_match": True, "results": results, "seconds": seconds, "source_unchanged": True, "method": "same-UID synthetic temporary trees; only HOME/GROUP and the exact race/error seam patched; no credentials/live roots/models/engine", "python": sys.version}
with (HERE / "review-probes-182326.json").open("x") as output:
    output.write(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
