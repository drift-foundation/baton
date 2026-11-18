#!/usr/bin/env bash
# W384870 M385113 batch: focused verification of the identity/cleanup corrections, sequential, with
# /var/tmp (and for Docker cases: containers/images) listed before and after each run.
set -uo pipefail
N=/home/sl/src/baton/work/scratch/w384870-c/final-fix
cd /home/sl/src/baton/v12/python
PREPARED="$(python3 -m tools.environment interpreter)"
export TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp
FULLRUN_ENV=(BATON_W32577_IMAGE_DIGEST=sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8 BATON_V12_INITIAL_ACCESS_ENGINE=1 BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4 BATON_V12_WORKSPACE_GROUP=1001)
"$PREPARED" -m tools.source_identity --repo /home/sl/src/baton --declared v12 > "$N/source.json"
: > "$N/summary.tsv"
one() {  # LABEL ENVSPEC(full|default) IDS...
  local LABEL=$1 ENVSPEC=$2; shift 2
  ls -1 /var/tmp | LC_ALL=C sort > "$N/$LABEL.var-tmp-before.txt"
  docker ps -a --no-trunc --format '{{.ID}}' | LC_ALL=C sort > "$N/$LABEL.containers-before.txt"
  docker images --no-trunc --format '{{.ID}}' | LC_ALL=C sort -u > "$N/$LABEL.images-before.txt"
  local S=$(date +%s)
  if [[ $ENVSPEC == full ]]; then env "${FULLRUN_ENV[@]}" timeout 3000 just test-one "$@" > "$N/$LABEL.log" 2>&1
  else env -u BATON_V12_WORKSPACE_GROUP -u BATON_V12_INITIAL_ACCESS_ENGINE -u BATON_V12_PRIVATE_LINE_IMAGE timeout 3000 just test-one "$@" > "$N/$LABEL.log" 2>&1; fi
  local CODE=$? E=$(date +%s)
  ls -1 /var/tmp | LC_ALL=C sort > "$N/$LABEL.var-tmp-after.txt"
  docker ps -a --no-trunc --format '{{.ID}}' | LC_ALL=C sort > "$N/$LABEL.containers-after.txt"
  docker images --no-trunc --format '{{.ID}}' | LC_ALL=C sort -u > "$N/$LABEL.images-after.txt"
  printf '%s\t%s\t%s\t%s\t%s\t%ss\tvar-tmp-new=%s\tcontainers-new=%s\timages-new=%s\n' "$LABEL" "$ENVSPEC" "$CODE" "$(grep -E '^Ran ' "$N/$LABEL.log" | tail -1)" "$(grep -E '^(OK|FAILED)' "$N/$LABEL.log" | tail -1)" "$((E-S))" \
    "$(LC_ALL=C comm -13 "$N/$LABEL.var-tmp-before.txt" "$N/$LABEL.var-tmp-after.txt" | wc -l)" \
    "$(LC_ALL=C comm -13 "$N/$LABEL.containers-before.txt" "$N/$LABEL.containers-after.txt" | wc -l)" \
    "$(LC_ALL=C comm -13 "$N/$LABEL.images-before.txt" "$N/$LABEL.images-after.txt" | wc -l)" | tee -a "$N/summary.tsv"
}
ADVERSE=$(python3 -c 'import json; d=json.load(open("/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/test-all.summary.json")); print(" ".join(d["failed"]+d["errors"]))')
one adverse26-fullrun-env full $ADVERSE
one maintenance-fullrun-env full tests.manager.test_maintenance
one attempts-fullrun-env full tests.manager.test_attempts
one maintenance-default-env default tests.manager.test_maintenance
one attempts-default-env default tests.manager.test_attempts
one worker-container-topology-fullrun-env full tests.manager.test_worker_container.RealContainersHoldTheTopology
one dogfood-arc-engine-fullrun-env full tests.tools.test_dogfood_arc_engine
"$PREPARED" -m tools.source_identity --repo /home/sl/src/baton --declared v12 > "$N/source-after.json"
echo "[final-fix] finished $(date -u +%FT%TZ)" >> "$N/summary.tsv"
