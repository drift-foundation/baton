#!/usr/bin/env bash
# Install the next v12 development instance. W202663, for owner ruling 208460.
#
# REVIEW208507 [R2]: the previous version of this instruction carried
# `/home/sl/baton-v12/instance-<new UTC timestamp>` and `<dest>` for the reader
# to fill in. Those are templates, not the exact commands the owner asked for.
# This script selects the timestamp itself, prints and retains the destination
# it chose, and passes real absolute paths to the supported installer.
#
# REVIEW208585 [R1]: the previous version called `just bootstrap` with no
# DISTRO, and `v12/justfile` REBUILDS in that case -- so what got installed was
# whatever the source and dependencies held at execution time, not the artefact
# that was reviewed. This version names the reviewed distro EXPLICITLY, refuses
# to install unless the bundle on disk still IS that artefact -- executable
# digest against `RUNTIME-BUILD-208531.json`, whole-bundle digest against
# `BUNDLE-MANIFEST-208647.json`, through the same `tools.instance.manifest` the
# installer's own admission uses -- and, after installing, reads the
# destination's `instance.json` back and compares the INSTALLED identity
# against the same two records. Nothing is rebuilt here.
#
# IT INSTALLS AND NOTHING ELSE. No Job is submitted, no pool is configured, no
# provider or model is reached, and no existing instance is touched: owner 208460
# preserves the current destination as evidence and forbids any agent
# replacement or reset of it.
set -euo pipefail

CHECKOUT=/home/sl/src/baton
DOSSIER="$CHECKOUT/work/records/2026/09/finding-v12-initial-claude-worker-pool"
ROOT=/home/sl/baton-v12
INPUTS="$DOSSIER/install-inputs.json"

# THE REVIEWED ARTEFACT, BY NAME. This is the one-folder bundle `just build`
# produced in claim208531 and review208585 identity-checked; passing it as the
# third operand is what stops `just bootstrap` from rebuilding.
DISTRO="$CHECKOUT/v12/python/build/out/distro"
# CLAIM225452: the records name the build carrying the owner's
# generic-reference model (2026-09-20T14:57:48Z): admissible_bases
# admits new bindings at their own OPAQUE declared references (no
# canonical-target comparison), and the integration worker is OPTIONAL
# so the producer-and-reviewer PR deployment composes and serves
# (786af0d5..., fresh snapshot taken before it), with the
# both-causes refresh diagnostic (review225408) and the
# same-line source-refresh recovery (review225331) and the
# bootstrap role-coverage gate now integration-optional too, plus the
# publication gate recording the proposal's OWN base with no offer-time
# canonical-target comparison. Earlier records stay
# in the dossier as history; every installed instance is preserved.
# CLAIM227424 (owner 2026-09-21T05:56:02Z round): the records name the build
# carrying the two round-2 corrections -- the per-attempt disk-backed scratch
# delivery at /scratch (owner "I approve spare mount"; workspaces HOME_ENTRIES,
# single_worker._attempt_scratch, oci._scratch_mount) and the moved attempt-log
# room (/run/baton/attempt-logs) with the disposable legacy-path decoy tmpfs
# (owner "I agree with own/disposable logs") -- atop the accepted 225452
# runtime. Earlier records stay as history; every installed instance is
# preserved.
RUNTIME_RECORD="$DOSSIER/RUNTIME-BUILD-227424.json"
BUNDLE_RECORD="$DOSSIER/BUNDLE-MANIFEST-227424.json"

# ONE TIMESTAMP, CHOSEN ONCE AND RETAINED. Every later command reads it from
# the file rather than recomputing it, so a verification step can never end up
# describing a different instance from the one that was installed.
STAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
DEST="$ROOT/instance-$STAMP"
SELECTED="$DOSSIER/selected-instance.txt"

for NEEDED in "$INPUTS" "$RUNTIME_RECORD" "$BUNDLE_RECORD"; do
  test -f "$NEEDED" || { echo "refused: $NEEDED is not here" >&2; exit 2; }
done
test -d "$ROOT" || { echo "refused: $ROOT is not here" >&2; exit 2; }
test -d "$DISTRO" || {
  echo "refused: the reviewed distro at $DISTRO is not here; this script" >&2
  echo "installs the recorded artefact and never rebuilds one" >&2; exit 2; }
if [ -e "$DEST" ]; then
  echo "refused: $DEST already exists; the installer never replaces a runtime in place" >&2
  exit 2
fi

# BEFORE: the bundle on disk must BE the reviewed artefact. A distro whose
# executable or whole-folder digest moved since the record was taken is a
# DIFFERENT artefact, and installing it while citing the reviewed digests would
# be presenting new bytes as the old build -- the exact thing review208585
# forbids. Refusal here costs nothing; the correction is to review the new
# artefact, not to install it unreviewed.
echo "verifying the reviewed artefact before installation:"
cd "$CHECKOUT/v12/python"
env PYTHONPATH=src:. python3 - "$DISTRO" "$RUNTIME_RECORD" "$BUNDLE_RECORD" <<'PY'
import hashlib, json, sys
from pathlib import Path
from tools import instance

distro, runtime_record, bundle_record = (Path(one) for one in sys.argv[1:4])
recorded_runtime = json.loads(runtime_record.read_text())
recorded_bundle = json.loads(bundle_record.read_text())
expected_exe = recorded_runtime["built"]["sha256"]
held_exe = "sha256:" + hashlib.sha256(
    (distro / "baton-v12-stack").read_bytes()).hexdigest()
if held_exe != expected_exe:
    sys.exit(f"refused: the executable hashes {held_exe}, not the recorded "
             f"{expected_exe}; this is not the reviewed artefact")
held = instance.manifest(str(distro))
expected = recorded_bundle["runtime"]
if (held["digest"], held["files"]) != (expected["digest"], expected["files"]):
    sys.exit(f"refused: the bundle digests {held['digest']} over "
             f"{held['files']} files, not the recorded {expected['digest']} "
             f"over {expected['files']}; the one-folder bundle is not the "
             f"reviewed artefact even though its executable is")
print(f"  executable {held_exe}")
print(f"  bundle     sha256:{held['digest']} ({held['files']} files)")
PY

echo "destination: $DEST"
printf '%s\n' "$DEST" > "$SELECTED"
echo "retained at: $SELECTED"

# THE SUPPORTED INSTALLER, with real absolute operands -- INCLUDING the distro,
# so nothing is rebuilt and the bytes verified above are the bytes copied.
#
# `state_root` INSIDE THE INPUT DOCUMENT IS NOT THE DESTINATION HERE, and that
# is an installer convention rather than a defect: `tools.bootstrap.main`
# overrides `state_root` from `--destination` BEFORE the document is validated,
# which review208507 verified in source. So the placeholder in
# `install-inputs.json` is never read on this path. Validating that document on
# its own would refuse it, and such a refusal is NOT an installation defect --
# do not report one.
cd "$CHECKOUT/v12"
just bootstrap "$INPUTS" "$DEST" "$DISTRO"

# AFTER: what was installed must still be the reviewed artefact. The installer
# already refuses a copy that does not digest as what it admitted; this
# compares the INSTALLED identity against the dossier's own records, so the
# binding is reviewed-record -> installed-instance with no step inferred.
echo
echo "verifying the INSTALLED identity against the recorded artefact:"
cd "$CHECKOUT/v12/python"
env PYTHONPATH=src:. python3 - "$DEST" "$RUNTIME_RECORD" "$BUNDLE_RECORD" <<'PY'
import hashlib, json, sys
from pathlib import Path

dest, runtime_record, bundle_record = (Path(one) for one in sys.argv[1:4])
recorded_exe = json.loads(runtime_record.read_text())["built"]["sha256"]
recorded = json.loads(bundle_record.read_text())["runtime"]
held = json.loads((dest / "instance.json").read_text())["runtime"]
if (held["digest"], held["files"]) != (recorded["digest"], recorded["files"]):
    sys.exit(f"refused: the installed instance records runtime digest "
             f"{held['digest']} over {held['files']} files, not the reviewed "
             f"{recorded['digest']} over {recorded['files']}")
installed_exe = "sha256:" + hashlib.sha256(
    (dest / "distro" / "baton-v12-stack").read_bytes()).hexdigest()
if installed_exe != recorded_exe:
    sys.exit(f"refused: the installed executable hashes {installed_exe}, not "
             f"the recorded {recorded_exe}")
print(f"  installed executable {installed_exe}")
print(f"  installed bundle     sha256:{held['digest']} ({held['files']} files)")
print("  both equal the reviewed records; identity established, behaviour not")
PY

echo
echo "installed. Its identity:"
just --justfile "$DEST/justfile" identity
echo
echo "next, from $DOSSIER:"
echo "  ./verify-next-instance.sh        # every following step reads $SELECTED"
