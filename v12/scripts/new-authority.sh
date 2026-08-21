#!/usr/bin/env bash
# Create a DISPOSABLE prototype Baton authority for the W76 proof.
# Never points at the production coordination home. The deployed v11
# executable is used only as a black-box documented CLI/JSON client.
#
#   new-authority.sh <disposable-authority-dir> <record-base>
#
# Both paths are OPERANDS, and both must be EXACTLY the ones the
# configured placement plan names. Round-2 review: proving each operand
# was *some* strict descendant of the state root was not enough — the
# retained evidence directory and the attempt state are descendants too,
# so a swap or a plausible-looking typo would have recursively removed
# the evidence and built an authority over the attempt tree. The script
# now compares against the plan and then uses the PLAN's values, so the
# operands are a statement of intent that must match, never a path this
# script follows.
#
# Round-1 review is why the plan exists at all: `$1` used to be handed
# straight to `rm -rf` behind a production denylist and a comparison
# against this subtree. `src/placement.mjs` is the single fail-closed
# authority here, and it never creates or deletes anything itself.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="${POC_CONFIG:-$ROOT/poc.json}"
HOME_DIR="${1:?usage: new-authority.sh <disposable-authority-dir> <record-base>}"
RECORD_BASE="${2:?usage: new-authority.sh <disposable-authority-dir> <record-base>}"
BATON="${BATON_BIN:-/home/sl/opt/baton/v11/8835cd5/bin/baton}"

# This one is an independent guard rather than a duplicate: it refuses a
# production coordination home even if some future configuration were to
# declare its state root around one.
case "$HOME_DIR" in
	/home/sl/baton-v11.*|/home/sl/.config/baton/*)
		echo "new-authority: $HOME_DIR looks like production state; refusing" >&2
		exit 2 ;;
esac

# NOTHING above this line has touched the filesystem, and nothing below
# it runs unless the plan validates and the operands ARE the plan.
PLAN="$(node "$ROOT/src/placement.mjs" paths --config "$CONFIG")"
read -r STATE PLANNED_AUTHORITY PLANNED_RECORD_BASE _RECORD_PATH _STATE_DIR \
	<<< "$PLAN"
if [ "$HOME_DIR" != "$PLANNED_AUTHORITY" ] \
		|| [ "$RECORD_BASE" != "$PLANNED_RECORD_BASE" ]; then
	echo "new-authority: the operands are not the configured plan." >&2
	echo "  authority   given $HOME_DIR" >&2
	echo "              plan  $PLANNED_AUTHORITY" >&2
	echo "  record base given $RECORD_BASE" >&2
	echo "              plan  $PLANNED_RECORD_BASE" >&2
	echo "  A descendant of the state root is not automatically a legal" >&2
	echo "  target: the evidence and attempt directories are descendants" >&2
	echo "  too, and this script recursively removes what it is given." >&2
	exit 2
fi

# Ownership BEFORE creation. An existing state root that carries no
# marker is refused here rather than quietly adopted, and a root that
# does not exist yet is established as ours by writing the marker.
OWN="$(node "$ROOT/src/placement.mjs" own --config "$CONFIG")"
read -r MARKER OWNERSHIP <<< "$OWN"
mkdir -p "$STATE"
if [ "$OWNERSHIP" = "fresh" ]; then
	node "$ROOT/src/placement.mjs" marker --config "$CONFIG" > "$MARKER"
fi

# From here on the PLAN's values are the only paths this script touches.
HOME_DIR="$PLANNED_AUTHORITY"
RECORD_BASE="$PLANNED_RECORD_BASE"

mkdir -p "$RECORD_BASE"
rm -rf "$HOME_DIR"
mkdir -p "$HOME_DIR"
UUID="$(python3 -c "import uuid;print(uuid.uuid4().hex)")"
cat > "$HOME_DIR/baton.json" <<JSON
{
  "config_version": 1,
  "generation": 1,
  "instance": {
    "authority_uuid": "$UUID",
    "database": "work.sqlite3",
    "name": "v12-poc-disposable"
  },
  "protocol_version": 11,
  "roots": {
    "poc": {
      "base": "$RECORD_BASE",
      "display": "v12 POC disposable record base"
    }
  },
  "teams": {
    "poc": {
      "display": "V12 POC",
      "kinds": {
        "intake": { "display": "Intake", "route": "approv" },
        "job": { "display": "Job", "route": "impl" },
        "rview": { "display": "Review", "route": "rview" }
      },
      "participants": {
        "ops": { "display": "Operator", "capabilities": ["config"], "roles": ["approv"] },
        "claude": { "display": "Claude worker", "roles": ["impl"] },
        "rev": { "display": "Reviewer", "roles": ["rview"] }
      },
      "roles": {
        "approv": { "display": "Approver", "instructions": "Disposable v12 POC operator." },
        "impl": { "display": "Worker", "instructions": "Disposable v12 POC isolated worker participant. All Baton access is performed by the trusted Worker Manager on this participant's behalf." },
        "rview": { "display": "Reviewer", "instructions": "Disposable v12 POC reviewer." }
      },
      "routes": {
        "approv": { "role": "approv", "handlers": ["ops"] },
        "impl": { "role": "impl", "handlers": ["claude"] },
        "rview": { "role": "rview", "handlers": ["rev"] }
      }
    }
  }
}
JSON
"$BATON" --participant poc.ops activate directory="$HOME_DIR"
echo "disposable authority ready: $HOME_DIR/baton.json"
