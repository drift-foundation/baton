# The corrected-image baseline packet

Claim 244216, baton.claude, W239528. Prepared for independent review; **not
approved for execution by its existence**. Supersedes
`OPERATOR-SUCCESSOR-243284.md`, which is kept: that packet was bound to an
image without the custody correction and said so.

## What is different, and it is the one thing that was missing

Every earlier packet in this campaign bound
`baton-v12-claude-worker:w236087-236349`, whose adapter is `abdf903d…` — the
one **without** `PROVIDER_UMASK`. This packet binds a distinct image built from
the source independent review accepted at 2026-09-23T03:19:21Z:

    reference   baton-v12-claude-worker:w239528-244216
    config      sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2
    adapter     opt/baton/claude_agent.py
                18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d
    umask       0o077, read out of the running image by name
    provider    2.1.247 (Claude Code), unchanged

**Every one of those digests was read out of a container started FROM the
image**, with `--network none --read-only` and the entrypoint overridden — not
from the build context. `IMAGE-ARTIFACT-244216.json` records all of it, plus
the whole `/opt/baton` inventory.

**The limit on that, disclosed.** Review 2026-09-23T03:30:58Z reported that its
own no-network read-only inspection container was denied Docker API access
before it could read content, and took no stronger retry, escalation or
fallback -- correctly. So the inside-image byte and version claims above remain
AUTHOR evidence, independently corroborated at the image-metadata level (both
config digests verified distinct and current, and the four selected worker
hashes agreeing with the artefact record and the accepted source) but not
independently re-read from inside the image.

**The predecessor is preserved.** `w236087-236349` is still tagged, still at
`sha256:2e9e84ff…7456bd`, and still carries `abdf903d…`. It is what W236087's
packet and every earlier W239528 packet are bound to; it was neither retagged,
rebuilt nor removed, and the build verified that before writing anything.

## What this packet can and cannot answer

**Can**: whether the real Claude CLI, under `PROVIDER_UMASK = 0o077`, leaves a
context home the manager can seal. That is the one thing no deterministic test
can establish, and it is the reason this image exists.

**Cannot**: that it will. Review 2026-09-23T03:19:21Z is explicit — the
retained `0o755` modes are consistent with umask creation but do not exclude an
explicit `chmod` or a reset mask. If the CLI does either, the run reaches the
same custody hold, reported now in about six seconds rather than at the bound.
**That would be a new finding, not a failure of this packet.**

## The paths

```sh
PY=/home/sl/.local/state/baton-v12-venv/bin/python
BOUND=/home/sl/baton-runs/single-implementation-242687/manager-source
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
ROOT=/home/sl/baton-runs/single-implementation-244216
RUN="$ROOT/run"
SEL="$ROOT/selections.json"

SOURCE="$ROOT/fixture-source"
BASE="$(git -C "$SOURCE" rev-parse HEAD)"
```

The manager source is unchanged and already verified — the custody correction
is in the **worker image**, not in the host modules:

```sh
"$PY" -B "$DOSSIER/snapshot_242687.py" --verify
```

## Preconditions

1. **A new run identity**, hence a new Job identity.
   `SELECTIONS-SUCCESSOR-244216.json` names `single-implementation-244216`; the
   composer derives `job-single-implementation-244216`.
2. **Genuinely fresh, dedicated stores** under `$ROOT/db/`. Every earlier
   instance holds other work and all of them are preserved evidence.
3. **Step 5a on the NEW instance**, through `prepare_instance.py` below.
   Do NOT follow the block printed in `OPERATOR-SUCCESSOR-243284.md`: it
   hardcodes that packet's selections path and asserts its run name, so
   pointing it at this packet's file raises `AssertionError` before the
   Authority is even opened. Review 2026-09-23T03:30:58Z found exactly that,
   and the remedy is a step that takes the packet as an operand rather than a
   block reprinted per run.
4. **A VALID credential.** This is the packet where that matters: an expired
   token answers the `unable` path, which is already established. A valid one
   is what reaches the custody question.

## Step 5a — prepare this instance's Authority

```sh
PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/prepare_instance.py" \
    --selections "$SEL" \
    --base "$BASE"
```

`PYTHONPATH` is bound for the same reason every other command on this page
binds it: this step imports `baton_v12.authority`, and without the bound source
a fresh shell answers `ModuleNotFoundError`. Review 2026-09-23T03:42:19Z ran
the command as printed and got exactly that.

It reads the selections you filled in, DERIVES the freshness marker from their
own `run_id` -- so the check moves with the packet instead of naming a run --
and refuses before opening anything if a store does not name this run, if one
names a consumed instance, if any `<OWNER>` member is still unresolved, or if
`--base` is not a full object name. Then it performs the same acts the earlier
block did: `create_work`, the `impl` and `integration` route handlers, the four
capability grants, and `set_policy("canonical_target", $BASE)`. It prints what
it did.

It opens no Job or control store, starts no container, reads no credential and
runs no provider.

**Running it twice is safe, and that was measured rather than assumed.**
`create_work` is journalled under an operation identity this step derives from
the run, so a repeat replays the same act and answers the same Work and scope.
An earlier draft of this page said the opposite; driving it twice showed
otherwise and the claim is corrected here.

Then check what is left with `baseline_bindings.preflight`, reading its stated
limits in `OPERATOR-239528.md`.

## Steps 1–4

Step 2 (the fixture) is `OPERATOR-239528.md` step 2 unchanged: `harness.py`
printing `before` and `TASK.md`, committed, at `$SOURCE`, and `$BASE` is also
the Authority's canonical target.

```sh
mkdir -p "$ROOT"
cp "$DOSSIER/SELECTIONS-SUCCESSOR-244216.json" "$SEL"
# fill the <OWNER> members, then:

PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline_bindings.py" \
    --selections "$SEL" --base "$BASE" --run-root "$RUN"

PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/baseline.py" \
    --packet "$RUN/PACKET.json" \
    --incarnation single-implementation-244216
```

Before running step 4, read `PACKET.json`:

- `worker_image.config_digest` must be
  `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`.
  **If it is `sha256:2e9e84ff…7456bd` you are bound to the uncorrected image**
  and the run cannot answer the custody question.
- `worker_image.worker_files["opt/baton/claude_agent.py"]` must be
  `18c34ff5…f9d8d`, not `abdf903d…bb4d`.
- `bounds` 180 / 300 / 60.
- `submission.job_id` `job-single-implementation-244216`.

`baseline.verify_worker_image` asks the engine for the image's own config
digest and refuses before any store opens if it is not the bound one.

## What each outcome means, and what it does not

Each entry below names a STATE and what to read. None of them names a cause:
the run reports what happened, and the cause is established from the evidence
afterwards. An earlier draft of this page asserted a mechanism for the
`no-progress` case that no run had shown, which is the habit review
2026-09-23T03:30:58Z asked to drop.

**Settled.** A proposal attributed to `Baton worker <worker@baton.invalid>` on
the declared base, the context generation sealed, execution stopped, cleanup
positive. That is the end-to-end implementation baseline this Job exists for,
and it would be the first time it has been reached.

**`stopped: no-progress`, `stage_states: implementation answering`.** The stage
could not advance and the run said so instead of spending its bound. What to
read, in this order: `context_use` for the hold and its reason; the context
home's own directory modes; and the attempt's provider log. `custody-invalid`
with non-private directories would say the mask did not govern what created
them — an explicit `chmod` and a reset umask are both consistent with that and
the modes alone do not separate them. A different hold reason is a different
question. Record what the evidence shows; do not re-run.

**`stopped: exceptional`, `disposition: unable`.** The turn ended without a
proposal. The attempt's retained provider log carries what the provider
reported; an expired credential is the already-established shape of this, and
is not the only one.

**`overall-bound-exceeded`, or a traceback out of the command.** Neither is
expected under the current corrections. Retain the outcome and the logs and
report it; whether it is a regression is a question for the evidence rather
than an assumption here.

Record whichever happened. A second run needs a new run identity and a new
selection.

## What this command does NOT authorize

Retagging, rebuilding or removing the preserved image. Reuse of, recovery on or
cleanup of any earlier run's stores, runtimes or evidence. Any reviewer stage,
session resume or Work closure. Anything in W244180's dossier or in W239533.
