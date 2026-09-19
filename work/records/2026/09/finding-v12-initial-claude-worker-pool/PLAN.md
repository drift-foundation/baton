# Current action — owner destination selection for D3

Read review-2026-09-18T23-44-44Z.md. Recommend a fresh development destination
/home/sl/baton-v12-instance-w202663-corrected through supported installation;
preserve the old selected instance and all evidence. Proposal only.
The earlier no-new-selection statement covers isolated verification only and
is superseded for a change of selected development destination. Remaining
implementation/verification scope is unchanged; Work is incomplete.

# Current action — step 8 on a separate destination (D3)

Review207292's R1 is ANSWERED and it found a real blocker, now pinned in
FINDING.md as **D3**: the owner's selected instance carries a runtime packaged
from a different source state (77 changed entries against this tree's 92), and
the supported installer REFUSES to replace it -- measured, exit 2, before any
effect: "nothing here upgrades a deployment in place".

So step 8 cannot honestly run on that instance. The next implementation step,
which needs no decision, is **resolution 3 in D3**: run the deterministic
terminal heterogeneous verification on a SEPARATE disposable destination
prepared with the corrected runtime, leaving the owner's instance exactly as it
is. Resolutions 1 and 2 touch the owner's named instance and are reported, not
taken.

ALSO OPEN: recovery/historical attribution, 3a's prospective build snapshot,
and re-verifying the final pool, pin and commands after the fixture pool has
been used.

Read review-2026-09-18T23-38-01Z.md, FINDING.md D3, and the claim207307 entry in
PROGRESS.md. No new owner selection; no combined image; no live submission.

# Plan — initial Claude worker pool for v12 development (W202663)

What is currently actionable. The chronological decision history is in
`FINDING.md`; this file names the one step that is live.

**Superseded 2026-09-18T22:01:51Z by the owner ruling** pinned in `FINDING.md`.
The three-option decision package this file previously carried is gone, not
merely reordered: the owner ruled that D2 is a gap in realizing the existing
provider-diverse architecture, refused the combined-image recommendation, and
authorized the bounded contract change that lets workers select their own
images. The old options are preserved in `FINDING.md`'s history as the
reasoning that led to the ruling.

## Ordered steps

| # | Step | State |
| --- | --- | --- |
| 1 | Pin the owner's original decision in this bound dossier before implementation | done (claim202665) |
| 2 | Build the provider image from `v12/worker/Dockerfile.claude`; record exact source and image provenance | done (claim202665) |
| 3 | Build the integration image on the step-2 digest as `PROVIDER_BASE`; record its provenance | done (claim202665) |
| 3a | Complete the provenance record: enumerate every copied input path including the `source_profiles` directory, with a pre-build input snapshot and retained image-side comparison | enumeration + image-side comparison done (claim207111, `COPIED-INPUTS-207111.json`, 7 and 9 paths, all equal); **the pre-build snapshot remains** and can only be taken before the next build |
| 4 | Pin the owner's D2 ruling and revalidate the existing contracts against the tree | done (claim206704) |
| 5 | Correct the coupling: a Job's `input_digest` names the shared Job input identity; workers keep their own runtime manifests and select their own images | done (claim206923) |
| 6 | Prove heterogeneous-image execution deterministically, including mismatch refusal | **partly done** — contract (claim206923/207111), preflight, and the accepted one-Job lifecycle re-run over three images with real attempt-row runtime attribution and real admission refusals (claim207111/207219). NOT done: TERMINAL heterogeneous integration, and recovery/historical attribution. The lifecycle re-run uses a simulated engine and an in-process workload, which review207195 accepted as deterministic evidence and not as proof the selected images ran |
| 7 | Compose and apply the Claude pool on the selected instance with distinct coder and reviewer identities | **done (claim207219)** — composed by `compose-pool-207219.py`, every accepted validator holding, and applied through `tools.bootstrap`; three workers, TWO images, one Job input identity; policy pin measured and equal at 16 |
| 8 | One deterministic Job to report-and-hold, with usable logs | **open** — and the pool from step 7 cannot serve it: its implementation and review workers run the provider image, so a Job reaching them makes a live model turn. Needs a deterministic fixture-image pool on the same instance |
| 9 | Replace the `COMMANDS-202663.md` part-2 template with generated concrete files and exact commands naming immutable digests | **written, not ready** — the template is gone and every value is read out of an artefact that exists (claim207219), but D3 means the documented installed path cannot yet be called launch-ready, and the final configuration after step 8 has still to be verified |

## Step 5 — the correction, and its exact boundary

`FINDING.md`'s revalidation establishes the shape: `launch.py:137` already
carries `job_input_digest` and `runtime_input_digest` as two facts and rules
that they are not to be compared. Two sites compare them anyway.

**Changed:**

1. `contracts/manifest.py` — one closed tuple naming the worker-runtime members
   and one function deriving the shared Job input identity from a manifest.
   The tuple is the contract; a second list of those names anywhere else would
   be a second thing to keep true.
2. `tools/single_worker.py` `_matches` — compare the Job's `input_digest`
   against the derived identity instead of the full `manifest_digest`.
3. `integration/admission.py` — the same correction at import time, by loading
   the proposal's own input manifest from the control store it already holds
   and deriving from it.

**Deliberately unchanged**, because each is the per-attempt validation or
attribution the ruling requires preserved:

- `single_worker.py:267`, a worker's image against its own manifest;
- `record_attempt`'s `input_digest`/`image_digest`/`toolchain_digest`;
- `output.py`, `provider_context.py`, `review_cycles.py`, which load an
  attempt's own runtime manifest;
- the frozen `worker-control-1.0` schema asset, so no built image is
  invalidated and no worker changes.

**Out of scope by the ruling:** worker-add UI, per-stage manifest schema
redesign, live models, Git mutation, unrelated redesign.

## Step 6 — what the proof must show

Deterministic, at the provider boundary, with no live model:

- **positive** — one Job whose implementation, review and integration workers
  name three different image digests is admitted, each worker carrying its own
  runtime manifest;
- **refusal** — a worker whose shared Job input identity differs from the Job's
  is still refused, so the correction did not weaken the check into absence;
- **refusal** — a worker whose configured image disagrees with its own
  manifest is still refused (`single_worker.py:267` intact);
- **reversal probe** — restoring the old comparison reproduces the D2 refusal.

## Coordination, not duplication

`W115981` and `W117026` keep their own scope. The first development task —
user-managed addition of workers to an existing pool — remains recorded only;
step 5 is the contract correction that makes it expressible, not the interface
itself.
