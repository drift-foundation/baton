#!/bin/sh
# W156162 claim156316: the committed-source baseline, RETAINED AND REPRODUCIBLE.
#
# WHY IT EXISTS. Four tests fail in this working tree and I needed to know
# whether W156162 caused them. This builds a copy of the working tree, replaces
# only the Job-manager source files this Work touches with their COMMITTED
# versions, removes this Work's new files, and runs the two affected modules.
# It READS Git history and mutates nothing.
#
# HOW IT WAS ACCOUNTED, AND THE GAP IN THAT. The original run was made inline
# rather than through ledger-156316.json's measured runner, so it has no elapsed
# time, no exit status and no log in that ledger. Review 2026-09-13T01:13:49Z
# asked that the evidence be retained and its spending accounted without
# inventing a duration or repeating a broad suite to repair the record. This
# script is the retained evidence; its cost is recorded in PROGRESS as
# unmeasured, and it is deliberately NOT rerun to patch the ledger.
set -eu
ROOT=${ROOT:-/home/sl/src/baton}
WORK=${WORK:-/tmp/w156162_base}
rm -rf "$WORK" && mkdir -p "$WORK"
cp -a "$ROOT/v12/python" "$WORK/python"
cd "$WORK/python"
rm -f src/baton_v12/job_manager/execution_limits.py \
      tests/job_manager/test_execution_limits.py
for f in documents.py projection.py schema.py store.py submission.py; do
  git -C "$ROOT" show "HEAD:v12/python/src/baton_v12/job_manager/$f" \
      > "src/baton_v12/job_manager/$f"
done
find . -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
env PYTHONPATH=src:tools:. python3 -m unittest \
    tests.job_manager.test_status tests.job_manager.test_exchange
