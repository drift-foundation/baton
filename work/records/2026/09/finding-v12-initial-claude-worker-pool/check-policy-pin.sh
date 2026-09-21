#!/usr/bin/env bash
# The post-bootstrap policy-pin equality, against the instance that was
# actually selected. W202663, answering review208585 [R2].
#
# THE PREVIOUS FORM WAS WRONG AND THIS FILE EXISTS BECAUSE OF IT: the printed
# command imported `compose-verification-208217.py` and called
# `check_policy_pin()` WITHOUT `select_instance`, so import-time defaults left
# it reading the HISTORICAL instance's pin while every surrounding step
# described the newly selected one -- and it printed `equal: false` and kept
# going, which is a gate demoted to a remark.
#
# This script reads the retained selection (or takes an explicit instance
# path), calls `select_instance` FIRST, and EXITS NONZERO on inequality. A pin
# that does not equal the Authority's generation means the deployment cannot
# satisfy its own pin: the correction is to recompose and re-apply, never to
# start the stack anyway.
set -euo pipefail

CHECKOUT=/home/sl/src/baton
DOSSIER="$CHECKOUT/work/records/2026/09/finding-v12-initial-claude-worker-pool"
SELECTED="$DOSSIER/selected-instance.txt"

DEST="${1:-}"
if [ -z "$DEST" ]; then
  test -f "$SELECTED" || {
    echo "refused: no instance named and $SELECTED is not here; run" >&2
    echo "install-next-instance.sh first or name an instance path" >&2
    exit 2; }
  DEST="$(cat "$SELECTED")"
fi
test -d "$DEST" || { echo "refused: $DEST is not here" >&2; exit 2; }

# CLAIM225533: a SECOND OPERAND selects which composer's pin answers. The
# deterministic verification pool and the real Claude PR pool are composed by
# DIFFERENT modules whose selections differ (the PR pool composes without an
# integration stage, which certifies one policy transition fewer per apply);
# checking one pool's deployment against the other composer's constants is the
# same historical-instance defect this script exists to prevent, one axis over.
MODE="${2:-verification}"
case "$MODE" in
  verification) COMPOSER="$DOSSIER/compose-verification-208217.py" ;;
  pool)         COMPOSER="$DOSSIER/compose-pool-207219.py" ;;
  *) echo "refused: unknown mode '$MODE' (verification|pool)" >&2; exit 2 ;;
esac

cd "$CHECKOUT/v12/python"
exec env PYTHONPATH=src:. python3 - "$DEST" "$COMPOSER" "$MODE" <<'PY'
import importlib.util
import json
import sys

dest, composer, mode = sys.argv[1], sys.argv[2], sys.argv[3]
spec = importlib.util.spec_from_file_location("v", composer)
loaded = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loaded)
# SELECT FIRST. Without this the module's recorded claim208217 constants answer
# for the historical instance, which is exactly the defect review208585 names.
selected = loaded.select_instance(dest)
if mode == "pool":
    # The PR shape is a selection too; without it the pool composer would
    # answer for the three-stage shape it defaults to.
    loaded.select_pr()
answer = loaded.check_policy_pin()
print(json.dumps(dict(answer, instance=selected["instance"],
                      authority_uuid=selected["authority_uuid"]),
                 indent=1, sort_keys=True))
if not answer["equal"]:
    print("REFUSED: configured pin " + repr(answer["configured_pin"])
          + " does not equal the Authority's generation "
          + repr(answer["authority_generation"]) + "; recompose and re-apply "
          "the pool -- do not start the stack against this deployment",
          file=sys.stderr)
    sys.exit(1)
PY
