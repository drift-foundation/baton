#!/usr/bin/env bash
# W384870 final accounted full suite — READ-ONLY preflight for the owner. Checks every prerequisite
# TESTING.md names and prints what the run will consume. Changes nothing; starts nothing.
set -uo pipefail
TOP=/home/sl/src/baton
IMAGE=${BATON_W32577_IMAGE_DIGEST:-sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8}
LINE=${BATON_V12_PRIVATE_LINE_IMAGE:-sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4}
ok=0; bad=0
check() { if "$@" >/dev/null 2>&1; then echo "ok    $*"; ok=$((ok+1)); else echo "FAIL  $*"; bad=$((bad+1)); fi; }
cd "$TOP/v12/python" || exit 2
echo "== source"; git -C "$TOP" log --oneline -1; echo "status lines under v12: $(git -C "$TOP" status --short v12 | wc -l) (0 expected for a committed candidate)"
if [[ "$(git -C "$TOP" rev-parse HEAD)" != "$(git -C "$TOP" rev-parse e80f2c8e)" || -n "$(git -C "$TOP" status --porcelain -- v12)" ]]; then echo "FAIL selected checkpoint e80f2c8e with clean v12 required"; bad=$((bad+1)); fi
for setting in BATON_V12_STACK_DISTRO BATON_V12_INPUT_DELIVERY_IMAGE BATON_V12_WORKER_ENTRY_IMAGE BATON_V12_CUSTODY_IMAGE BATON_V12_LIFECYCLE_IMAGE BATON_V12_LARGE_WORKSPACE_PROOF; do
  if [[ -n "${!setting-}" ]]; then echo "FAIL $setting must be unset for this selected run"; bad=$((bad+1)); fi
done
if [[ " $(id -G) " != *" ${BATON_V12_WORKSPACE_GROUP:-1001} "* ]]; then echo "FAIL caller lacks selected workspace group"; bad=$((bad+1)); fi
PREPARED="$(python3 -m tools.environment interpreter 2>/dev/null)"; echo "prepared interpreter: ${PREPARED:-MISSING}"
check test -x "${PREPARED:-/nonexistent}"
"$PREPARED" -m tools.source_identity --repo "$TOP" --declared v12 > /dev/null 2>&1 && echo "ok    source identity composes (declared inputs present)" || { echo "FAIL  source identity refuses (a declared consumed input is absent)"; bad=$((bad+1)); }
echo "== tools"; check command -v just; check command -v git; check command -v docker
echo "== docker"; check docker version
check docker image inspect "$IMAGE"; echo "      reference worker image (BATON_W32577_IMAGE_DIGEST) $IMAGE"
check docker image inspect "$LINE";  echo "      private line image (BATON_V12_PRIVATE_LINE_IMAGE) $LINE"
echo "      containers now: $(docker ps -aq | wc -l) total, $(docker ps -q | wc -l) running (pre-existing; recorded as baseline by run-final-suite.sh)"
echo "== workspace group"; check getent group "${BATON_V12_WORKSPACE_GROUP:-1001}"; echo "      $(getent group "${BATON_V12_WORKSPACE_GROUP:-1001}") ; caller in it: $(id -nG | tr ' ' '\n' | grep -c -x "$(getent group "${BATON_V12_WORKSPACE_GROUP:-1001}" | cut -d: -f1)")"
echo "== storage"; echo "      /tmp fstype $(findmnt -no FSTYPE /tmp) ; /var/tmp fstype $(findmnt -no FSTYPE /var/tmp 2>/dev/null || findmnt -no FSTYPE / ) ; free $(df -h /var/tmp | awk 'NR==2{print $4}')"
echo "      /var/tmp entries now: $(ls -1 /var/tmp | wc -l) (baseline 376 on 2026-11-18)"
echo "== bundle"; if [[ -n "${BATON_V12_STACK_DISTRO:-}" ]]; then echo "      BATON_V12_STACK_DISTRO=$BATON_V12_STACK_DISTRO (test-all will NOT build)"; else echo "      BATON_V12_STACK_DISTRO unset: test-all builds a fresh bundle (default; build/out/distro currently from $(./build/out/distro/baton-v12-stack identity 2>/dev/null | grep -o '"commit": "[0-9a-f]*"' | head -1), will be replaced)"; fi
echo "== host"; echo "      cpus $(nproc) ; mem $(free -g | awk 'NR==2{print $7}')G available ; userns $(unshare -rm true 2>/dev/null && echo yes || echo no) ; python $("$PREPARED" -c 'import sys; print(sys.version.split()[0])')"
echo "== result: $ok ok, $bad failing"; [[ $bad -eq 0 ]]
