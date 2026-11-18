#!/usr/bin/env bash
# W384870 M385050: ONE accounted scans-group run, the test-group recipe's exact runner invocation on the
# prepared interpreter plus the JSON ledger (--summary) and the content-bound source identity before/after.
set -uo pipefail
N=/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/scans-20261118
LOG=$N/scans.log
cd /home/sl/src/baton/v12/python
PREPARED="$(python3 -m tools.environment interpreter)"
TOP="$(git rev-parse --show-toplevel)"
export TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp
{
  echo "[scans] started $(date -u +%FT%TZ) group scans jobs 4 account keep-going (test-group recipe invocation + --summary)"
  "$PREPARED" -m tools.source_identity --repo "$TOP" --declared v12 > "$N/scans.source.json" || echo "[scans] SOURCE IDENTITY REFUSED before the run"
  "$PREPARED" -c 'import json,sys; d=json.load(open(sys.argv[1])); print("[scans] source HEAD", d["head"], "changed-files", d["changed_count"], "consumed-input-files", d["consumed_count"], "content-digest", d["content_digest"])' "$N/scans.source.json"
  echo "[scans] python $("$PREPARED" -c 'import sys; print(sys.version.split()[0])') jsonschema $("$PREPARED" -c 'import importlib.metadata as m; print(m.version("jsonschema"))') uid $(id -u) cpus $(nproc) tmpfs-tmp $(findmnt -no FSTYPE /tmp 2>/dev/null || echo unknown) disk-root $BATON_V12_DISK_ROOT"
} | tee "$LOG"
START=$(date +%s)
timeout --signal=INT --kill-after=60 3300 "$PREPARED" tools/parallel_test.py --group scans --account --keep-going --jobs 4 --summary "$N/scans.summary.json" 2>&1 | tee -a "$LOG"
CODE=${PIPESTATUS[0]}
END=$(date +%s)
{
  echo "[scans] runner exit $CODE elapsed $((END-START))s finished $(date -u +%FT%TZ)"
  "$PREPARED" -m tools.source_identity --repo "$TOP" --declared v12 > "$N/scans.source-after.json" || echo "[scans] SOURCE IDENTITY REFUSED after the run"
  BEFORE=$("$PREPARED" -c 'import json,sys; print(json.load(open(sys.argv[1]))["content_digest"])' "$N/scans.source.json")
  AFTER=$("$PREPARED" -c 'import json,sys; print(json.load(open(sys.argv[1]))["content_digest"])' "$N/scans.source-after.json")
  if [[ "$BEFORE" == "$AFTER" ]]; then echo "[scans] source identity stable $BEFORE"; else echo "[scans] SOURCE DRIFT before $BEFORE after $AFTER"; fi
  ls -1 /var/tmp > "$N/var-tmp-after.txt"
  echo "[scans] /var/tmp entries before $(wc -l < "$N/var-tmp-before.txt") after $(wc -l < "$N/var-tmp-after.txt")"
  diff "$N/var-tmp-before.txt" "$N/var-tmp-after.txt" && echo "[scans] /var/tmp unchanged" || echo "[scans] /var/tmp differs (above)"
} | tee -a "$LOG"
exit $CODE
