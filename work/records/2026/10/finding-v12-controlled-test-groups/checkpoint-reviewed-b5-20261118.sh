#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
if ! git diff --cached --quiet; then
    echo "Index already has staged changes; review them before this selective checkpoint." >&2
    exit 1
fi
python3 - <<'CHECK'
import hashlib
expected = {'v12/python/src/baton_v12/authority/store.py': 'd67f1052ce06030f59ccb63411a6ae2257c6d6465721b88a15a5e495fbf4ea75', 'v12/python/src/baton_v12/contracts/errors.py': 'def3854f5fc852a7a695169fb2493aa6d5c94eeab77368fe12db199646c60660', 'v12/python/src/baton_v12/worker_manager/workspaces.py': '6e8748820ab4ebb18dc69fd0cb8aa3be979637bb9aa5b586868fa37e0fa67d4f', 'v12/python/tests/authority/test_boundary.py': '2d25cc18e803702dc54338b4efa0f3141924fa1431040c9c8dc1f08c4663ceae', 'v12/python/tests/manager/test_secrets.py': '95608dbad02d38e7e27c939c7fe6012f68d092e34c7aa617be20b1269918a907', 'v12/python/tests/manager/test_workspaces.py': '3e51b10f67e6193cf03ea5c3dbb8db7fd8410b13494815b75fe614c173d0c06e'}
from pathlib import Path
for path,digest in expected.items():
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
        raise SystemExit('Reviewed source changed; stop before staging: '+path)
CHECK
git add -- v12/python/src/baton_v12/authority/store.py v12/python/src/baton_v12/contracts/errors.py v12/python/src/baton_v12/worker_manager/workspaces.py v12/python/tests/authority/test_boundary.py v12/python/tests/manager/test_secrets.py v12/python/tests/manager/test_workspaces.py work/records/2026/10/finding-v12-controlled-test-groups
git diff --cached --stat
git commit -m "fix(v12): repair bounded diagnostics and secrets coverage"
