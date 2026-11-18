#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
if ! git diff --cached --quiet; then
    echo "Index contains staged changes; review them before this selective checkpoint." >&2
    exit 1
fi
git add -- \
    v12/python/src/baton_v12/worker_manager/intake.py \
    v12/python/src/baton_v12/worker_manager/tokens.py \
    v12/python/src/baton_v12/worker_manager/workspaces.py \
    v12/python/tests/manager/test_boundary_inventory.py \
    v12/python/tests/manager/test_stopped_settlement.py \
    v12/python/tests/manager/test_workspaces.py \
    v12/python/tests/manager/test_integration_image.py \
    v12/python/tests/manager/test_worker_image.py \
    v12/python/tests/integration/test_driver.py \
    work/records/2026/09/finding-v12-token-renewal/FINDING.md \
    work/records/2026/10/finding-v12-controlled-test-groups
git diff --cached --stat
git commit -m "fix(v12): bind renewal decisions and verify boundary provenance"
