# Instance 3 — the exact owner commands, in order

Prepared under owner decision358374; corrected at claim358517 for
`review-2026-10-23T05-00-27Z.md`. **Nothing here was executed.** Instance 3 did
not exist at this authoring, and every check is repeated by `fresh.py` at the
eventual operation. Each mutating step is a separate owner selection.

Every block below was checked with `bash -n`; the check is recorded in
`evidence/SHELL-SYNTAX.txt`.

## The operands

```sh
BUILD=/home/sl/baton-builds/w325959-30245386-356981
SRC="$BUILD/src/v12/python"
PY="$BUILD/venv/bin/python"
PKT=/home/sl/src/baton/work/records/2026/10/finding-v12-native-pilot-instance-packet/fresh3-358443
D=/home/sl/baton-instances/native-coordination-pilot-w321608-3
DISTRO="$BUILD/build/out/distro"
RSRC="$BUILD/src"
```

`DISTRO` was **PENDING** at handoff358474 and is now resolved by reading the
build rather than assuming a subdirectory. Confirm it before selection 2 —
these are reads:

```sh
test -x "$DISTRO/baton-v12-stack" || echo "NOT THE BUNDLE: $DISTRO"
"$DISTRO/baton-v12-stack" identity
```

That identity must answer `frozen: true`, both frozen schema assets
(`agent-session-1.0`, `worker-control-1.0`), a `native_rpds` **inside the
bundle's own `_internal`**, and `build_stamp.commit`
`302453869d07eb5579e79a6572586d3c3cf62a5c` with `dirty: false`. At this
authoring it did, with `sha256`
`9cda6dabe328ee800c2eb3cb6997d29dce179c857f9bb2968c33a4adbf043673` — the same
executable digest the accepted instance-2 packet pinned. A bundle that answers
otherwise is not the reviewed one and `admit` is entitled to refuse it.

## Selection 1 — preparation preflight (writes nothing)

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$PKT/fresh.py" \
    --destination "$D" --packet "$PKT" \
    --distro "$DISTRO" --repository-source "$RSRC"
```

This is **read-only** and, corrected at claim358517, now actually checks
everything knowable before anything is minted: all four packet documents parse
and carry the pinned identifiers; the packet, the imported helper
(`post-install-357462/configure.py`) and the four inherited documents all hash
to their pins; no consumed path — packet, helper, bundle, source, inherited
inputs — lies inside instance 1 or 2; the destination is free; the bundle holds
an **executable** `baton-v12-stack`; the source tree carries `v12`; and the
whole manifest/submission cross-binding is **rehearsed against a deliberately
provisional authority** so a sealing fault refuses here rather than after a
destination exists.

## Selection 2 — mint, compose and install in the resolved order

```sh
cd "$SRC" && PYTHONPATH=src:. "$PY" "$PKT/fresh.py" \
    --destination "$D" --packet "$PKT" \
    --distro "$DISTRO" --repository-source "$RSRC" --owner-selected
```

**What this does, in the order independently resolved at
`review-2026-10-23T04-52-43Z.md`:**

1. `bootstrap --inputs install-inputs.json` **with no `--destination`** — mints
   and persists the authority and an empty configuration. No repositories, no
   runtime, no selector.
2. Reads the minted `authority_uuid` back from `$D/authority-identity.json`.
3. Composes the Work as `<uuid[:8]>-W1` — `contracts/manifest.py` refuses a
   Work reference without its authority's prefix — and seals the manifest and
   task against it. The packet pins are **re-checked after the mint**, so a
   packet edited mid-run cannot be installed.
4. `bootstrap --inputs <composed> --destination "$D" --distro "$DISTRO"
   --repository-source "$RSRC"` — reuses that uuid and creates **all four
   repositories**, the Work, the configuration and the selector.

**No manual clone step.** The instance-2 workaround is not carried forward:
`repository_plan` derives one source per worker, so a fresh install with
`workers` prepares `target.git`, `workspace`, `source-implementation-pilot` and
`source-review-pilot` itself.

Then reads the installed `deployment.json` back through
`stage_execution.held_configuration`, verifies every installed worker names the
**minted** authority, and emits `configure-inputs.json`, `submission.json` and
`preparation-readback.json` under `$D/generated/`.

**This selection is where simulation stops.** Everything proved in
`evidence/PROVE.json` used a *simulated* repository runner and a *stub* bundle.
This command runs the real thing: it executes real `git clone` operations
through the product's own boundary and really admits the bundle. Treat its
first run as the first unproven step.

**Restart checkpoint**: if interrupted after step 1, the destination holds an
authority and an empty configuration. Re-running refuses on the existing
destination by design — **do not delete it**; report its state and continue
from a bounded correction, because the authority is already minted and is this
instance's identity.

## Selection 2b — the workspace storage prerequisite (measured, required)

```sh
mkdir -p "$D/state/workspaces"
test -d "$D/state/workspaces" && test ! -L "$D/state/workspaces"
```

**This is required and was measured, not assumed.**
`bootstrap.storage_bound` (`bootstrap.py:1673`) derives `workspace_storage`
when absent and refuses a path outside the destination, but **creates no
directory**; the consumer `workspaces.check_workspace_storage`
(`workspaces.py:869`) `lstat`s the place and refuses with *"is not a directory
this manager can see"*. The disposable proof measured the installed destination
after a successful supported preparation and found
`state/workspaces` **absent** (`PROVE.json` →
`workspace_storage_present: false`). So preparation does not create it and a
stage would refuse without this step.

That same consumer also refuses **a link at that name** and **a directory owned
by another uid**, which is why the check above asserts a real directory rather
than just a successful `mkdir`.

## Selection 3 — submission (separate decision)

```sh
C="$D/distro/baton-v12-stack"
A="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["authority_uuid"])' "$D/authority-identity.json")"
test -n "$A" || echo "NO AUTHORITY READ BACK -- do not proceed"

"$C" manager \
    --store "$D/db/jobs.sqlite3" \
    --incarnation w325959-owner-submit-3 \
    --authority-uuid "$A" \
    submit --document "$D/generated/submission.json"
```

The authority is **read out of the instance's own record into a quoted shell
variable** rather than left as a placeholder for someone to paste. Operand
spelling is the one read off the installed bundle's own help at claim357834:
`--store`, `--incarnation`, `--authority-uuid`, then `submit --document`. There
is **no** `--instance` and **no** `--submission`.

## Selection 4 — serving and reading (separate decision)

```sh
I="$D/instance.json"
S="$D/state/status.json"

"$C" identity
"$C" status      --instance "$I"
"$C" start       --instance "$I"        # live serving
"$C" monitor     --instance "$I" --interval 5
"$C" repository  --instance "$I"
"$C" stop        --instance "$I"
"$C" view --status "$S"                 # needs a PUBLISHED snapshot
"$C" attempt-diagnostics "$S"
```

## Identities and limits

| Operand | Value |
|---|---|
| Destination | `…-w321608-3` |
| Job | `quickstart-c` |
| Submission | `sub-w321608-quickstart-3` |
| Task | `w321608-native-operator-quickstart-3` |
| Incarnation | `w325959-owner-submit-3` |
| Distro | `$BUILD/build/out/distro` (resolved and verified) |
| Authority | minted at step 1, read back at selection 3 |
| Work | `<minted uuid[:8]>-W1` — never `673355e1-W1` |

Task scope, the required downstream proposal/review/human acceptance, and the
**3600s provider / 900s verification per-invocation** limits are unchanged. No
integration worker or stage. Instances 1 and 2, their custody and the failed
`quickstart-b` review are untouched.

**What remains unproven**, stated plainly: `evidence/PROVE.json` establishes the
composition, the ordering, both role declaration contracts, the workspace
measurement and every pre-mint refusal — using a simulated repository runner
and a stub bundle. It does **not** establish that real clones, the real bundle's
admission, or a real provider turn succeed. Selections 2, 3 and 4 are each the
first execution of their own step.
