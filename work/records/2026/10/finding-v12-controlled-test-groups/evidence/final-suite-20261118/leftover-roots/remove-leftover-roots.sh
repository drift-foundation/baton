#!/usr/bin/env bash
# W384870 (review 2026-11-18T07-13-25Z): remove the SEVEN roots the owner's full run left under /var/tmp,
# inventoried in inventory-before-removal.txt. Check mode by default; `--remove` acts. Touches only the
# seven names below. The five v12-worker-roots-* hold `output/out` written by the worker container as uid
# 65532 (modes the host user cannot change), so that content is removed by a container running as the
# same uid over the same bind mount (alpine:3.20, present locally, no network); the host then removes
# its own roots with tests.manager.disk_roots.remove_owned_root (frozen dirs restored, links not followed).
set -euo pipefail
MODE=${1:-check}
[[ $MODE == check || $MODE == --remove ]] || { echo "expected check or --remove" >&2; exit 2; }
WORKER_ROOTS=(v12-worker-roots-78ca8ao8 v12-worker-roots-hhy37lad v12-worker-roots-nz4ckmfp v12-worker-roots-pbqsu9nz v12-worker-roots-xjbhv9_v)
ARC_ROOTS=(v12-w39358-arc-p1ma63lu v12-w39358-arc-qdt5r4ho)
for r in "${WORKER_ROOTS[@]}" "${ARC_ROOTS[@]}"; do
  if [[ ! -d /var/tmp/$r || -L /var/tmp/$r || ! -O /var/tmp/$r ]]; then echo "refusing absent, linked or unowned root: /var/tmp/$r" >&2; exit 2; fi
  echo "$MODE: /var/tmp/$r ($(find /var/tmp/$r -mindepth 1 | wc -l) entries, foreign-uid entries: $(find /var/tmp/$r -mindepth 1 ! -user "$(id -un)" | wc -l))"
done
for r in "${WORKER_ROOTS[@]}"; do
  [[ -d /var/tmp/$r/output && ! -L /var/tmp/$r/output && -O /var/tmp/$r/output ]] || { echo "refusing substituted output: $r" >&2; exit 2; }
done
[[ $MODE == --remove ]] || { echo "(check mode; pass --remove to act). /var/tmp entries now: $(ls -1 /var/tmp | wc -l), baseline 376"; exit 0; }
for r in "${WORKER_ROOTS[@]}"; do
  [[ -d /var/tmp/$r/output && -O /var/tmp/$r ]] || continue
  docker run --pull=never --rm --user 65532:65532 --network none --mount "type=bind,source=/var/tmp/$r/output,target=/output,readonly=false" alpine:3.20 rm -rf /output/out
  echo "container-written /output/out removed: $r"
done
cd /home/sl/src/baton/v12/python
PYTHONPATH=src:. "$(python3 -m tools.environment interpreter)" - "${WORKER_ROOTS[@]}" "${ARC_ROOTS[@]}" <<'PY'
import os, sys
from tests.manager import disk_roots
for name in sys.argv[1:]:
    place = "/var/tmp/" + name
    if os.path.isdir(place) and not os.path.islink(place):
        disk_roots.remove_owned_root(place); print("removed", place, "exists:", os.path.lexists(place))
PY
echo "/var/tmp entries now: $(ls -1 /var/tmp | wc -l) (baseline 376)"
