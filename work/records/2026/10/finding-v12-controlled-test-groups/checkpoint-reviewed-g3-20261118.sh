#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
if ! git diff --cached --quiet; then
    echo "Index already has staged changes; review them before selective checkpoint." >&2
    exit 1
fi
python3 - <<'CHECK'
from pathlib import Path
import hashlib
expected = {'v12/DESIGN.md': 'd9fa46a6aa10472a145d6a6a9aa08a7b8ec814fdb9f88f559ab41eb1952f5114', 'v12/python/src/baton_v12/worker_manager/attempts.py': 'c3f665482758c0f67fcb82f6dc377333e5bc5f6dd7c182c54aaedf10288ada72', 'v12/python/tools/stage_execution.py': '36ce6ca6d43ab95aaebd3b200a3a99a25e59fd9bba39d5b312df98fb2adabc92', 'v12/python/tests/tools/test_quiescent_assignment_finalization.py': '0d51609644dce8d17f2be7a753582672b27350f32d0d6d64aae9e680faf15643', 'v12/python/tests/tools/test_single_worker.py': '6ef4d0582e5c7a594c654b8f097ffa51998713b952764d4c933d036150b7bb98', 'v12/python/tests/manager/test_launch.py': 'e7adfbddf24a10aa9990cd89fa45bf2ac8b177dd75a1c7f5f43e6f010777614e', 'v12/python/tests/manager/test_execution_limits.py': '9e87de494438333766e44ee9619412074550a6b77027491a33210b31a5c67316', 'v12/python/tests/tools/test_execution_limits.py': '02ef815d5a9e9a35127f2f000291f85facadb7885fa7126817d9741182adc2c4', 'v12/python/src/baton_v12/worker_manager/tokens.py': 'd2cd3ecd1c8c81782352363edac37ed2a646fe82ef1fa39cfc2ddb29fbff79a9', 'v12/python/src/baton_v12/worker_manager/maintenance.py': 'f5f848bba1cbf2b9608df5080c689560a35f9766445c986fc9fba2ae5765875d', 'v12/python/tests/manager/test_stopped_settlement.py': 'eb9f7a7267190db03b994f1ceaf7ab51c062b15c9c34adef3ab06925f0d75d4a', 'v12/python/tests/manager/test_maintenance.py': '24b268af3722440a477eaa92b7603a2aedc93c19ee2b3486ae05f49f49d9addc'}
for path,digest in expected.items():
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
        raise SystemExit('Reviewed source changed; stop before staging: '+path)
CHECK
git add -- v12/DESIGN.md v12/python/src/baton_v12/worker_manager/attempts.py v12/python/tools/stage_execution.py v12/python/tests/tools/test_quiescent_assignment_finalization.py v12/python/tests/tools/test_single_worker.py v12/python/tests/manager/test_launch.py v12/python/tests/manager/test_execution_limits.py v12/python/tests/tools/test_execution_limits.py v12/python/src/baton_v12/worker_manager/tokens.py v12/python/src/baton_v12/worker_manager/maintenance.py v12/python/tests/manager/test_stopped_settlement.py v12/python/tests/manager/test_maintenance.py work/records/2026/10/finding-v12-controlled-test-groups
git diff --cached --stat
git commit -m "fix(v12): preserve revoked replay boundaries and repair launch fixtures"
