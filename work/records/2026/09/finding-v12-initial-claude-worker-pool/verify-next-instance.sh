#!/usr/bin/env bash
# The installed verification, parameterized from the instance that was chosen.
# W202663, answering review208507 [R2] and review208585 [R2].
#
# NOTHING HERE IS EDITED BY HAND. `install-next-instance.sh` wrote the
# destination it selected into `selected-instance.txt`, and every command below
# reads it from there -- so no step can describe a different instance from the
# one installed, and no historical composer or evidence file has to be edited
# to run it.
#
# IT RUNS THE READ-ONLY AND COMPOSITION STEPS ONLY. Starting the stack,
# submitting the Job and carrying it to a terminal state are the steps after
# this, and they are listed at the end rather than performed: review208507 says
# not to attempt the installed run before the owner has deployed. The listed
# commands are EXACT -- review208585 [R2]: printing `--help` where a submission
# belongs asks the owner to infer the one command this file exists to state.
set -euo pipefail

CHECKOUT=/home/sl/src/baton
DOSSIER="$CHECKOUT/work/records/2026/09/finding-v12-initial-claude-worker-pool"
SELECTED="$DOSSIER/selected-instance.txt"

test -f "$SELECTED" || {
  echo "refused: $SELECTED is not here; run install-next-instance.sh first" >&2
  exit 2; }
DEST="$(cat "$SELECTED")"
test -d "$DEST" || { echo "refused: $DEST is not here" >&2; exit 2; }
echo "instance: $DEST"

# 1. IDENTITY. What this build IS, beside the digest recorded for the runtime
#    that was installed. This establishes identity, not behaviour -- the
#    owner's own qualification in pass 208215.
echo
echo "== identity =="
just --justfile "$DEST/justfile" identity

# 2. WHAT IT HOLDS BEFORE ANYTHING IS CONFIGURED. A fresh install serves no
#    capacity; this prints the Authority it generated and its empty pool so a
#    later reader can tell a fresh instance from a configured one.
echo
echo "== authority and pool, before configuration =="
python3 - "$DEST" <<'PY'
import json, sys
from pathlib import Path
dest = Path(sys.argv[1])
identity = json.loads((dest / "authority-identity.json").read_text())
deployment = json.loads((dest / "deployment.json").read_text()) \
    if (dest / "deployment.json").is_file() else {}
print("authority_uuid    ", identity["authority_uuid"])
print("workers configured", len(deployment.get("workers") or []))
print("job bindings      ", len(deployment.get("job_bindings") or []))
print("policy_generation ", deployment.get("policy_generation"))
print("pool_generation   ", deployment.get("pool_generation"))
PY

# THE SELECTED INSTANCE'S OWN AUTHORITY, for the exact commands below. It was
# generated at install and persisted at the destination; reading it here is
# what ties every printed command to THIS instance rather than a historical
# one.
UUID="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['authority_uuid'])" \
  "$DEST/authority-identity.json")"

# CLAIM225533: the deterministic-verification listing that stood here is
# SUPERSEDED -- that campaign completed through the A -> owner-acceptance -> B
# demonstration and its instances are preserved evidence. The steps below are
# the REAL CLAUDE PR POOL's, per owner pass 225531 and
# REAL-JOB-PROPOSAL-220329.md; steps a-c are preparation this Work may run,
# steps d-e are the live launch that runs ONLY under the owner's separate
# authorization.
echo
echo "== remaining steps, in order (a-c preparation; d-e OWNER-AUTHORIZED only) =="
cat <<REMAINING
  a. compose the real Claude PR pool for this instance at the owner-accepted
     base (this regenerates $DOSSIER/pool-bootstrap-inputs.json
     and pool-submission.json for it):
       cd $CHECKOUT/v12/python
       PYTHONPATH=src:. python3 $DOSSIER/compose-pool-207219.py \\
         --instance "$DEST" --pr --base <the accepted base current at authorization>
     (--pr composes coder+reviewer only -- no integration worker; --base is
      the opaque accepted reference the owner recorded, e.g. the
      ACCEPTED-BASE-*.json newest at authorization time)
  b. apply it:
       PYTHONPATH=src:. python3 -m tools.bootstrap \\
         --inputs $DOSSIER/pool-bootstrap-inputs.json
  c. check the policy pin in POOL mode -- the PR pool's own composer answers,
     the check is a GATE and exits nonzero on inequality:
       $DOSSIER/check-policy-pin.sh "$DEST" pool
  d. OWNER-AUTHORIZED LIVE LAUNCH ONLY -- start, then submit the composed Job,
     tied to this instance's own Job store and Authority:
       just --justfile "$DEST/justfile" start
       cd $CHECKOUT/v12/python
       PYTHONPATH=src:. python3 -m tools.job_manager \\
         --store "$DEST/db/jobs.sqlite3" \\
         --incarnation w202663-claude-job-submit \\
         --authority-uuid "$UUID" \\
         submit --document $DOSSIER/pool-submission.json
  e. observe to terminal report-and-hold, then the OWNER-PR-FLOW-220329.md
     inspection/acceptance steps over the resulting candidate. Enforced
     limits: one episode per stage by construction, each provider turn
     bounded by the deployment's provider_turn execution limit, verification
     bounded by verification_command_seconds. Nothing merges without the
     owner.
REMAINING
