#!/usr/bin/env bash
# W384870 exit-race fix: focused verification batch. One log per module per environment, residue counted per run.
set -uo pipefail
E=$(cd "$(dirname "$0")" && pwd)
cd /home/sl/src/baton/v12/python || exit 2
export TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp
MODULES="tests.tools.test_next_run_flow tests.manager.test_authoring_enforcement tests.manager.test_authoring_shutdown_deadline tests.manager.test_authoring_manager_guard tests.tools.test_next_run_managed tests.tools.test_next_run_recovery tests.tools.test_next_run tests.job_manager.test_serving_renewal tests.job_manager.test_native_stop_restart tests.job_manager.test_native_permission"
printf 'env\tmodule\tran\tresult\tseconds\tnew_var_tmp\tnew_containers\tlog\n' >> "$E/summary.tsv"
for ENV in full-run default; do
  if [[ $ENV == full-run ]]; then
    export BATON_W32577_IMAGE_DIGEST=sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8 BATON_V12_INITIAL_ACCESS_ENGINE=1 BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4 BATON_V12_WORKSPACE_GROUP=1001
  else
    unset BATON_W32577_IMAGE_DIGEST BATON_V12_INITIAL_ACCESS_ENGINE BATON_V12_PRIVATE_LINE_IMAGE BATON_V12_WORKSPACE_GROUP
  fi
  for M in $MODULES; do
    LOG="$E/runs/$ENV-$M.log"
    ls -1 /var/tmp | sort > "$E/runs/$ENV-$M.var-tmp-before"; docker ps -aq | sort > "$E/runs/$ENV-$M.containers-before"
    START=$(date +%s)
    { echo "[batch] $(date -u +%FT%TZ) env=$ENV module=$M HEAD=$(git rev-parse --short HEAD) WORKSPACE_GROUP=${BATON_V12_WORKSPACE_GROUP-<unset>} INITIAL_ACCESS_ENGINE=${BATON_V12_INITIAL_ACCESS_ENGINE-<unset>}"; just test-one "$M"; echo "[batch] exit $?"; } > "$LOG" 2>&1
    SECS=$(( $(date +%s) - START ))
    ls -1 /var/tmp | sort > "$E/runs/$ENV-$M.var-tmp-after"; docker ps -aq | sort > "$E/runs/$ENV-$M.containers-after"
    NEWT=$(comm -13 "$E/runs/$ENV-$M.var-tmp-before" "$E/runs/$ENV-$M.var-tmp-after" | wc -l)
    NEWC=$(comm -13 "$E/runs/$ENV-$M.containers-before" "$E/runs/$ENV-$M.containers-after" | wc -l)
    RAN=$(grep -o '^Ran [0-9]* test' "$LOG" | grep -o '[0-9]*'); RES=$(grep -E '^(OK|FAILED)' "$LOG" | tail -1)
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$ENV" "$M" "${RAN:-?}" "${RES:-no verdict}" "$SECS" "$NEWT" "$NEWC" "runs/$ENV-$M.log" >> "$E/summary.tsv"
  done
done
echo "[batch] done $(date -u +%FT%TZ)"
