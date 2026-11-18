#!/usr/bin/env bash
# W384870 final accounted full suite, fourth selected run after checkpoint f896bab0 — the OWNER runs this (coordinator prepared). It is the canonical
# `just test-all LOG [JOBS]` from v12/ with the environment TESTING.md requires, wrapped ONLY in
# residue accounting (/var/tmp and docker container listings before/after). Nothing else is added
# or removed; the recipe itself writes LOG, LOG.summary.json, LOG.source.json, LOG.source-after.json
# and the supervised run directory beside LOG, and builds a fresh bundle unless BATON_V12_STACK_DISTRO is set.
set -uo pipefail
E=/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r4
LOG=$E/test-all.log
# One selected run owns this evidence location; never overwrite its baseline or log.
for previous in "$LOG" "$E/invocation-environment.txt" "$E/var-tmp-before.txt"; do
  if [[ -e "$previous" ]]; then echo "Refusing existing run evidence: $previous" >&2; exit 2; fi
done
bash "$E/preflight.sh" || exit 2
JOBS=${1:-}                       # optional worker limit, e.g. 16; omitted = every CPU (B0 used all 32)
export TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp
export BATON_W32577_IMAGE_DIGEST=${BATON_W32577_IMAGE_DIGEST:-sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8}
export BATON_V12_INITIAL_ACCESS_ENGINE=1
export BATON_V12_PRIVATE_LINE_IMAGE=${BATON_V12_PRIVATE_LINE_IMAGE:-sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4}
export BATON_V12_WORKSPACE_GROUP=${BATON_V12_WORKSPACE_GROUP:-1001}
# Optional, as in the accepted B4 joined run: select the already-built engine image instead of letting the
# engine modules build their own. Leave unset to build (default). NOTE 2026-11-18: that image is NOT present
# locally any more (`docker image inspect` fails), so selecting it would fail the engine gates; keep unset.
# IMG=sha256:4da24074d73c8bdeb7ad676ca646287f356f84fbccf517f1f6052686b020ef83
# export BATON_V12_INPUT_DELIVERY_IMAGE=$IMG BATON_V12_WORKER_ENTRY_IMAGE=$IMG BATON_V12_CUSTODY_IMAGE=$IMG BATON_V12_LIFECYCLE_IMAGE=$IMG
mkdir -p "$E"
ls -1 /var/tmp | sort > "$E/var-tmp-before.txt"
docker ps -a --no-trunc --format '{{.ID}} {{.Names}} {{.Status}}' | sort > "$E/docker-ps-a-before.txt"
docker images --no-trunc --format '{{.ID}} {{.Repository}}:{{.Tag}}' | sort > "$E/docker-images-before.txt"
{ echo "[final-suite] started $(date -u +%FT%TZ) uid $(id -u) jobs ${JOBS:-all}"; for setting in TMPDIR BATON_V12_DISK_ROOT BATON_W32577_IMAGE_DIGEST BATON_V12_INITIAL_ACCESS_ENGINE BATON_V12_PRIVATE_LINE_IMAGE BATON_V12_WORKSPACE_GROUP BATON_V12_STACK_DISTRO BATON_V12_INPUT_DELIVERY_IMAGE BATON_V12_WORKER_ENTRY_IMAGE BATON_V12_CUSTODY_IMAGE BATON_V12_LIFECYCLE_IMAGE BATON_V12_LARGE_WORKSPACE_PROOF; do printf '%s=%s\n' "$setting" "${!setting-<unset>}"; done; } > "$E/invocation-environment.txt"
START=$(date +%s)
cd /home/sl/src/baton/v12 && just test-all "$LOG" "$JOBS"
CODE=$?
END=$(date +%s)
ls -1 /var/tmp | sort > "$E/var-tmp-after.txt"
docker ps -a --no-trunc --format '{{.ID}} {{.Names}} {{.Status}}' | sort > "$E/docker-ps-a-after.txt"
docker images --no-trunc --format '{{.ID}} {{.Repository}}:{{.Tag}}' | sort > "$E/docker-images-after.txt"
{
  echo "[final-suite] recipe exit $CODE wall $((END-START))s finished $(date -u +%FT%TZ)"
  echo "[final-suite] /var/tmp before $(wc -l < "$E/var-tmp-before.txt") after $(wc -l < "$E/var-tmp-after.txt"); new entries: $(comm -13 "$E/var-tmp-before.txt" "$E/var-tmp-after.txt" | wc -l)"
  comm -13 "$E/var-tmp-before.txt" "$E/var-tmp-after.txt" | sed 's/^/  new: /'
  echo "[final-suite] containers before $(wc -l < "$E/docker-ps-a-before.txt") after $(wc -l < "$E/docker-ps-a-after.txt"); new: $(comm -13 <(cut -d' ' -f1 "$E/docker-ps-a-before.txt") <(cut -d' ' -f1 "$E/docker-ps-a-after.txt") | wc -l)"
  echo "[final-suite] images before $(wc -l < "$E/docker-images-before.txt") after $(wc -l < "$E/docker-images-after.txt"); new: $(comm -13 <(cut -d' ' -f1 "$E/docker-images-before.txt") <(cut -d' ' -f1 "$E/docker-images-after.txt") | wc -l)"
} | tee "$E/residue.txt"
echo "[final-suite] accounting: python3 -I $E/summarize.py $E/test-all.summary.json > $E/ACCOUNTING.md"
exit $CODE
