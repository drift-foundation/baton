#!/usr/bin/env bash
set -euo pipefail
cd /home/sl/src/baton
if ! git diff --cached --quiet; then
    echo "Index already contains staged changes; review those before using this selective checkpoint." >&2
    exit 1
fi
git add -- v12/python/tests/manager/test_credentials_engine.py v12/python/tests/manager/test_lifecycle_composition.py v12/python/tests/manager/test_ended_runtime_adoption.py v12/python/tests/manager/test_negative_race_endings.py work/records/2026/10/finding-v12-controlled-test-groups/findings/finding-b4-docker-readiness
git diff --cached --stat
git commit -m "test(v12): clear remaining historical Docker engine failures"
