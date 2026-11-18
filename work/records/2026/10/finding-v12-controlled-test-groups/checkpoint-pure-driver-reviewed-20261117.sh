#!/usr/bin/env bash
set -euo pipefail
cd /home/sl/src/baton
if ! git diff --cached --quiet; then
    echo "Index already contains staged changes; review before selective checkpoint." >&2
    exit 1
fi
git add -- v12/python/tests/manager/test_integration_image.py v12/python/tests/manager/test_worker_image.py v12/python/tests/integration/test_driver.py work/records/2026/10/finding-v12-controlled-test-groups/findings/finding-b4-docker-readiness
git diff --cached --stat
git commit -m "test(v12): repair image contracts and retained admission history"
