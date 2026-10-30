# Fresh-destination native adoption proposal — claim357134

## Owner decision and scope

Owner event357131 (2026-10-23T01:47:46Z) selects a fresh destination for native adoption and explicitly preserves the old failed Job and instance unresolved. It says: "Do not implement retained-instance updating now" and "No build, deployment or live execution selected by this command."

This supersedes the undecided fresh-versus-retained choice in review-2026-10-23T01-25-43Z.md and the prior PLAN. Retained update/schema migration/recovery is not a prerequisite for this fresh path and is not implemented. This is not historical recovery acceptance. The retained instance `/home/sl/baton-instances/native-coordination-pilot-w321608-1`, authority `1cdb8d19feda47c0a209bd0669b16871`, Work `1cdb8d19-W1`, Job `quickstart-a`, submission `sub-w321608-quickstart-1` remain unresolved and untouched. No copy, revival, resubmission, deletion or claim of current cessation is made.

## Concrete destination and inputs

Proposed new destination: `/home/sl/baton-instances/native-coordination-pilot-w321608-2`. Availability has not been inspected; refuse any existing entry, including a dangling symlink. Do not reuse a partially populated destination on an unreviewed retry.

`install-inputs.json` beside this proposal is a proposed empty-installation input, derived from the dossier's revision-4/configuration/install-inputs.json. Only state_root, integration_target and integration_workspace are rebound from destination1 to destination2. Other explicit instance selections (receipt participants, retention, integration profile, generations, owner) are preserved for owner selection, not silently replaced by example values. No authority UUID, Job, Work, worker, declared base, canonical target or producer assignment is supplied. The runtime will mint the fresh authority. No historical stores are input.

Expected owned layout: destination2/instance.json, distro/baton-v12-stack, authority-identity.json, db/{authority,jobs,control,integration}.sqlite3, deployment.json, deployment-state, state, logs and repo. All writable deployment and repository targets must resolve inside destination2; source/build and destination1 are not mutable instance roots. Fresh authority is an output, never invented in this packet.

## Selection A — exact human build commands

The following is the accepted build proposal, reproduced without changing its paths or commit. Slawomir alone runs its Git preparation. Selection357131 did not authorize its execution. Downloads and fresh environment mutation are part of this separate build selection. Failure retains partial output; no automatic cleanup or retry is proposed.

```bash
set -euo pipefail
BUILD_ROOT=/home/sl/baton-builds/w325959-30245386-356981
CLEAN="$BUILD_ROOT/src"
export BATON_V12_VENV="$BUILD_ROOT/venv"
OUT="$BUILD_ROOT/build"
SOURCE_COMMIT=302453869d07eb5579e79a6572586d3c3cf62a5c
mkdir -p /home/sl/baton-builds
if [ -e "$BUILD_ROOT" ] || [ -L "$BUILD_ROOT" ]; then
    echo "refuse: build root already exists: $BUILD_ROOT" >&2
    exit 1
fi
mkdir -m 700 "$BUILD_ROOT"
git clone --no-checkout /home/sl/src/baton "$CLEAN"
git -C "$CLEAN" checkout --detach "$SOURCE_COMMIT"
test "$(git -C "$CLEAN" rev-parse HEAD)" = "$SOURCE_COMMIT"
test -z "$(git -C "$CLEAN" status --porcelain --untracked-files=normal)"
for TARGET in "$BATON_V12_VENV" "$OUT"; do
    if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
        echo "refuse: output already exists: $TARGET" >&2
        exit 1
    fi
done
cd "$CLEAN/v12"
just setup
just build "$OUT"
"$OUT/out/distro/baton-v12-stack" identity > "$BUILD_ROOT/identity.json"
```

Expected bundle: `/home/sl/baton-builds/w325959-30245386-356981/build/out/distro`. Before installation selection, retain actual identity showing exact302453869d07eb5579e79a6572586d3c3cf62a5c and clean source, complete bundle manifest/digest, interpreter/platform and lock provenance, build result and any failure. A successful build is not an installed or served instance. Do not build from the dirty shared tree or substitute another commit silently.

## Subsequent selection B — install the empty fresh instance

After build receipts are reviewed, owner may separately select this exact input and bundle for installation. This block is a proposal only; it performs installation, not a read-only check. Runtime repository preparation is part of this selection and remains a human operation. The explicit repository source is the human's clean committed clone. It does not submit a Job or start a provider.

```bash
set -euo pipefail
DEST=/home/sl/baton-instances/native-coordination-pilot-w321608-2
BUILD_ROOT=/home/sl/baton-builds/w325959-30245386-356981
export BATON_V12_VENV="$BUILD_ROOT/venv"
INPUTS=/home/sl/src/baton/work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh-357134/install-inputs.json
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
    echo "refuse: destination already exists: $DEST" >&2
    exit 1
fi
cd "$BUILD_ROOT/src/v12"
just bootstrap "$INPUTS" "$DEST" "$BUILD_ROOT/build/out/distro" "--repository-source $BUILD_ROOT/src"
"$DEST/distro/baton-v12-stack" identity
"$DEST/distro/baton-v12-stack" status --instance "$DEST/instance.json"
```

The installation selection binds the input digest recorded below and the actual reviewed bundle digest, which cannot be known before build. Recheck input bytes before executing; a changed input requires review. If preparation refuses, preserve the refusal and partial artifacts, and report it without installing over them or inventing a store workaround.

Empty-install acceptance: fresh generated authority distinct from destination1; installed selector and bundle identity/digest agree with the accepted build; every instance path is destination2-owned and no old store/Job/worker is imported; empty Job bindings and no configured execution capacity; no provider, engine workload or submission occurred; installed identity/status can be read with truthful absent/unknown states where nothing has started. A stopped/unstarted status is not evidence that the old instance ceased executing. Evidence must come from supported public surfaces and generated artifacts, never raw store reads. Missing public proof is reported as a gap, not guessed.

## Subsequent selection C — native adoption execution

Empty installation alone is not W321608 adoption acceptance. Serving the fresh instance, configuring a bounded new Job, or submitting/executing it requires its own operational selection with fresh authority/Work/submission identities, exact task/source/limits, profiles and receipt actors. Prepare those inputs against the actual fresh instance after B; do not reuse the old failed Job as if it had recovered. Preserve the accepted per-invocation token policy and isolated implementation/review attempts, with actionable failure evidence, cleanup/hold reporting and persisted restart behavior where exercised. Actual output, verification, independent semantic review and human native receipts must establish the chosen development result. Prior deterministic26 proofs remain deterministic evidence, not a substitute for these future receipts. No broader workload or backlog migration is selected.

## Coordination and verification

This is one bounded preparation outcome, so no new implementation child is needed. Existing five children remain closed, W325959 stays open and W321608 stays blocked through adoption acceptance. If B or C later exposes distinct implementation gaps, create bounded Work and actual dependency edges before releasing execution; no retained updater is queued by this decision. Reviewer owns this packet/FINDING/PLAN. Prior author PROGRESS and immutable reviews remain unchanged.

Static validation only: input parses; changes are exactly three destination paths; no old destination string or identity/job/worker members remain; build block matches the accepted addendum. Sources: v12/STACK.md fresh-install contract, tools/instance.py layout, v12/justfile bootstrap recipe. No build, install, live readback, model, engine, tests or Git mutation performed. Prior verification costs/results remain attributed and unchanged. Events read through357131, discussion through356736, claim357134. This packet is decision support, not an independent review of its own future execution.

Proposed install-inputs.json SHA-256: `757e6df36fc704aa74a157bcc0fd25f62a312b6323e5c9591bd068889019cf8e`.
