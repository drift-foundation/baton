"""Public host reproduction: a frozen assignment home is replaceable.

Run from v12/python:
  PYTHONPATH=src:. python3 ../../work/records/2026/08/finding-v12-worker-input-documents-readable/evidence/w33935-assignment-home-replacement-repro.py
"""

import os
import tempfile

from baton_v12.worker_manager import workspaces
from tests.manager import test_lifecycle_composition as composition

with tempfile.TemporaryDirectory(prefix="w33935-home-replace-") as temporary:
    storage = os.path.join(temporary, "storage")
    os.makedirs(storage)
    roots = workspaces.assignment_workspace(storage, "assignment-1")
    given, assignment = composition.input_roots.documents(
        work_ref=dict(composition.WORK_REF), participant=composition.WHO,
        generation=1, runtime_attempt_id="attempt-1", given=None,
        policy_digest=composition.POLICY,
        profile_digest=composition.PROFILE)
    workspaces.compose_input_root(
        roots["inputs"], given, assignment,
        assignment=dict(assignment["assignment_ref"]),
        runtime_attempt_id="attempt-1")

    home = os.path.dirname(roots["inputs"])
    displaced = home + ".displaced"
    os.rename(home, displaced)
    os.makedirs(roots["inputs"])
    with open(os.path.join(roots["inputs"], workspaces.INPUT_MANIFEST), "w",
              encoding="utf-8") as handle:
        handle.write("replacement")

    print("displaced-home-mode", oct(os.stat(displaced).st_mode & 0o777))
    print("replacement-home-mode", oct(os.stat(home).st_mode & 0o777))
    with open(os.path.join(roots["inputs"], workspaces.INPUT_MANIFEST),
              encoding="utf-8") as handle:
        print("replacement-bytes", handle.read())
    raise AssertionError("the delivered assignment home was replaceable by name")
