#!/usr/bin/env bash
# W384870 M385106 batch: focused module/id runs after the two test repairs and nine leak-site repairs,
# each with /var/tmp before/after; then four concurrent runs of the operator-view module.
set -uo pipefail
N=/home/sl/src/baton/work/scratch/w384870-c/batch
cd /home/sl/src/baton/v12/python
PREPARED="$(python3 -m tools.environment interpreter)"
export TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp
"$PREPARED" -m tools.source_identity --repo /home/sl/src/baton --declared v12 > "$N/source.json"
: > "$N/summary.tsv"
one() {
  local LABEL=$1; shift
  ls -1 /var/tmp > "$N/$LABEL.var-tmp-before.txt"
  local S=$(date +%s)
  timeout 1500 just test-one "$@" > "$N/$LABEL.log" 2>&1
  local CODE=$? E=$(date +%s)
  ls -1 /var/tmp > "$N/$LABEL.var-tmp-after.txt"
  local RAN=$(grep -E '^Ran [0-9]+ tests?' "$N/$LABEL.log" | tail -1)
  local VERDICT=$(grep -E '^(OK|FAILED)' "$N/$LABEL.log" | tail -1)
  local RESIDUE=$(diff "$N/$LABEL.var-tmp-before.txt" "$N/$LABEL.var-tmp-after.txt" | grep -c '^>')
  printf '%s\t%s\t%s\t%s\t%ss\tresidue=%s\n' "$LABEL" "$CODE" "$RAN" "$VERDICT" "$((E-S))" "$RESIDUE" | tee -a "$N/summary.tsv"
}
one sealing tests.manager.test_sealing
one credentials tests.manager.test_credentials
one attempt_logs tests.manager.test_attempt_logs
one maintenance tests.manager.test_maintenance
one integration_worker tests.tools.test_integration_worker
one managed_preparation tests.tools.test_managed_preparation
one single_worker tests.tools.test_single_worker
one dogfood_operator tests.tools.test_dogfood_operator
one operator_view tests.tools.test_operator_verification_view
one diagnostic_rendering tests.manager.test_diagnostic_rendering
one inventory_probe_check tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.test_the_missing_probe_check_can_actually_fail
# concurrency: four simultaneous runs of the operator-view module over the shared host /tmp
ls -1 /var/tmp > "$N/concurrent.var-tmp-before.txt"; ls -1d /tmp/dogfood-view-* 2>/dev/null > "$N/concurrent.tmp-views-before.txt"
S=$(date +%s)
for i in 1 2 3 4; do ( timeout 1500 just test-one tests.tools.test_operator_verification_view > "$N/concurrent-$i.log" 2>&1; echo "$i $?" >> "$N/concurrent.exit.txt" ) & done
wait
E=$(date +%s)
ls -1 /var/tmp > "$N/concurrent.var-tmp-after.txt"; ls -1d /tmp/dogfood-view-* 2>/dev/null > "$N/concurrent.tmp-views-after.txt"
printf 'concurrent-x4\t%s\t%s\t%ss\tresidue=%s\ttmp-views-after=%s\n' "$(sort "$N/concurrent.exit.txt" | tr '\n' ' ')" "$(grep -h -E '^(OK|FAILED)' "$N"/concurrent-?.log | sort | uniq -c | tr '\n' ' ')" "$((E-S))" "$(diff "$N/concurrent.var-tmp-before.txt" "$N/concurrent.var-tmp-after.txt" | grep -c '^>')" "$(wc -l < "$N/concurrent.tmp-views-after.txt")" | tee -a "$N/summary.tsv"
"$PREPARED" -m tools.source_identity --repo /home/sl/src/baton --declared v12 > "$N/source-after.json"
echo "[batch] finished $(date -u +%FT%TZ)" >> "$N/summary.tsv"
