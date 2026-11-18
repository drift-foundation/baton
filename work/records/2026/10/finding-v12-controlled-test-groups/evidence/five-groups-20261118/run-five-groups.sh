#!/usr/bin/env bash
# W384870 M385102: ONE accounted run each of authority, job_manager, manager-pure, tools-pure, integration,
# in that order, the test-group recipe's exact runner invocation on the prepared interpreter plus the JSON
# ledger (--summary) and the content-bound source identity before/after each group. Verification only.
set -uo pipefail
N=/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/five-groups-20261118
cd /home/sl/src/baton/v12/python
PREPARED="$(python3 -m tools.environment interpreter)"
TOP="$(git rev-parse --show-toplevel)"
export TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp
JOBS=8
digest() { "$PREPARED" -c 'import json,sys; print(json.load(open(sys.argv[1]))["content_digest"])' "$1"; }
run_group() {
  local G=$1 LIMIT=$2
  local LOG=$N/$G.log
  ls -1 /var/tmp > "$N/$G.var-tmp-before.txt"
  {
    echo "[$G] started $(date -u +%FT%TZ) group $G jobs $JOBS account keep-going timeout ${LIMIT}s (test-group recipe invocation + --summary)"
    echo "[$G] git HEAD $(git rev-parse HEAD) status-lines $(git status --short | wc -l)"
    "$PREPARED" -m tools.source_identity --repo "$TOP" --declared v12 > "$N/$G.source.json" || echo "[$G] SOURCE IDENTITY REFUSED before the run"
    "$PREPARED" -c 'import json,sys; d=json.load(open(sys.argv[1])); print("['"$G"'] source HEAD", d["head"], "changed-files", d["changed_count"], "consumed-input-files", d["consumed_count"], "content-digest", d["content_digest"])' "$N/$G.source.json"
    echo "[$G] python $("$PREPARED" -c 'import sys; print(sys.version.split()[0])') jsonschema $("$PREPARED" -c 'import importlib.metadata as m; print(m.version("jsonschema"))') uid $(id -u) cpus $(nproc) tmpfs-tmp $(findmnt -no FSTYPE /tmp 2>/dev/null || echo unknown) disk-root $BATON_V12_DISK_ROOT"
  } | tee "$LOG"
  local START=$(date +%s)
  timeout --signal=INT --kill-after=120 "$LIMIT" "$PREPARED" tools/parallel_test.py --group "$G" --account --keep-going --jobs "$JOBS" --summary "$N/$G.summary.json" 2>&1 | tee -a "$LOG"
  local CODE=${PIPESTATUS[0]}
  local END=$(date +%s)
  {
    echo "[$G] runner exit $CODE elapsed $((END-START))s finished $(date -u +%FT%TZ)"
    "$PREPARED" -m tools.source_identity --repo "$TOP" --declared v12 > "$N/$G.source-after.json" || echo "[$G] SOURCE IDENTITY REFUSED after the run"
    local BEFORE AFTER; BEFORE=$(digest "$N/$G.source.json"); AFTER=$(digest "$N/$G.source-after.json")
    if [[ "$BEFORE" == "$AFTER" ]]; then echo "[$G] source identity stable $BEFORE"; else echo "[$G] SOURCE DRIFT before $BEFORE after $AFTER"; fi
    ls -1 /var/tmp > "$N/$G.var-tmp-after.txt"
    echo "[$G] /var/tmp entries before $(wc -l < "$N/$G.var-tmp-before.txt") after $(wc -l < "$N/$G.var-tmp-after.txt")"
    diff "$N/$G.var-tmp-before.txt" "$N/$G.var-tmp-after.txt" && echo "[$G] /var/tmp unchanged" || echo "[$G] /var/tmp differs (above)"
  } | tee -a "$LOG"
  echo "$G $CODE $((END-START))" >> "$N/exit-codes.txt"
}
: > "$N/exit-codes.txt"
echo "[five-groups] started $(date -u +%FT%TZ)" > "$N/driver.log"
run_group authority 2400
run_group job_manager 3600
run_group manager-pure 5400
run_group tools-pure 5400
run_group integration 3600
echo "[five-groups] finished $(date -u +%FT%TZ)" >> "$N/driver.log"
cat "$N/exit-codes.txt" >> "$N/driver.log"
