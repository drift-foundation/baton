# Plan: constrained OCI adapter core

1. [implementation-ready] Freeze the adapter's closed operation/observation
   types from worker-control 1.0 and the approved posture topology.
2. [pending] Implement policy, argv and inspection normalization for Docker and
   compatible Podman without shell composition.
3. [pending] Implement exact reconciliation, quiescence, destruction and
   positive-absence evidence.
4. [pending] Add vector, hostile-output, retry, race and isolated engine tests.
5. [pending] Record focused evidence and return for independent review.

## Review correction — 2026-08-24

Status: **changes requested** in
`review-2026-08-24T23-49-38Z.md`.

1. [required] Derive an engine-valid deterministic container name from the
   manager's real `runtime.start:<digest>` operation identity; never weaken or
   rewrite the manager operation identity itself.
2. [required] Require inspection to name the exact requested runtime before
   reporting running/quiescent, and replace broad stderr substring matching
   with a pinned engine-specific exact-identity positive-absence contract.
3. [required] Own every reconciliation-label member by its semantic rule,
   reject unknown `baton.v12.*` labels and bind resolved
   image/profile/policy/adapter identity to both argv and labels.
4. [required] Canonicalize mount spellings and replace the host-path denylist
   with proof against assignment-owned, posture-specific allowed roots so
   authority/config/database/repository and other-worker state cannot mount.
5. [required] Make the six additive reviewer cases green, finish the receiving
   inventory and probes without exemptions, and add the isolated Docker smoke
   with positive cleanup plus compatible Podman coverage when available.
6. [verification] Run focused adapter, boundary inventory, dependency/text,
   isolated-engine, full source and locked installed-layout gates, then return
   the corrected cut for independent review.

## Correction re-review — 2026-08-25

Status: **changes requested**.

1. [confirmed corrected] The six prior focused regressions pass 39/39.
2. [still required] Replace `_FORBIDDEN` with proof that every host source is
   within this assignment's posture-specific allowed roots. The new repository
   mount regression is the focused negative acceptance case.
3. [still required] Bind the resolved image/profile/policy/adapter identity to
   both emitted argv and reconciliation labels rather than accepting those
   accounts independently.
4. [still required] Complete W6632's receiving inventory and probes, and add
   the isolated Docker positive-cleanup smoke plus compatible Podman coverage
   required by this dossier. The test module's claim that smoke belongs to a
   separate cut does not supersede this record's acceptance.
5. [verification] Make the 40-case OCI module green, then run the inventory,
   dependency/text, engine, full source and locked installed-layout gates.

## Assignment-root API decision — 2026-08-25

1. [done — ruling 2026-08-25] Make both `assignment_roots` and closed `posture`
   required inputs to `run_vector` and `OciAdapter`. Roots alone cannot choose
   the posture-specific topology.
2. [confirmed topology] Require the exact `inputs`/`workspace`/`git` root record.
   Consent mounts none. Execution may mount the `inputs` root or a descendant
   read-only and the `workspace` root or a descendant under the requested
   read/write mode. Never mount the private `git` root; refuse writable inputs,
   foreign/other-assignment roots, and overlapping/nested source or target
   spellings.
3. [required] Remove `_FORBIDDEN`; update every public call site and golden
   vector; make ownership/posture positive and negative cases green. Then
   continue the still-open resolved-identity, inventory and engine-smoke items
   from the correction plan.

## Assignment-root implementation re-review — 2026-08-25

Status: **changes requested; positive-root implementation is partial**.

1. [confirmed corrected] Required `assignment_roots`/`posture`, consent-no-
   mounts, inputs-read-only, workspace-mode, private-Git refusal, and removal
   of `_FORBIDDEN` pass the original 45 focused cases.
2. [required P1] Resolve real host identity before containment so a symlink
   below an owned lexical root cannot mount foreign state.
3. [required] Reject pairwise equal/nested assignment roots and equal/nested
   mount sources or targets; make all three additive methods (four assertions)
   green.
4. [still required] Bind one closed resolved image/profile/policy/adapter
   identity to argv plus reconciliation labels and prove mismatch/restart.
5. [still required] Complete the 20 unowned and 17 unprobed OCI inventory
   entries, including the new public inputs.
6. [still required] Add isolated Docker positive-cleanup and compatible Podman
   coverage; append actual state to `PROGRESS.md` and run all specified gates.
   Review: `review-2026-08-25T03-01-06Z.md`.

## Assignment-root re-review correction — 2026-08-25

All six required corrections from `review-2026-08-25T03-01-06Z.md` are done.

1. [done] Canonical filesystem identity before containment. `_canonical`
   resolves a host path as the kernel would; both roots and mount sources go
   through it, and the RESOLVED source is what reaches argv.
2. [done] Pairwise equal/nested assignment roots refused, and pairwise
   equal/nested mount sources and targets refused. All four of the reviewer's
   assertions are green, plus three of mine covering resolution on both sides
   and the degenerate equal-roots case.
3. [done] One closed `RESOLVED_IDENTITY` — image, profile and adapter digests
   — owned at construction, naming the argv's image and required to agree with
   the reconciliation labels. Mismatch, no-side-effect and restart probes
   added.
4. [done] Every OCI receiving entry owned and probed: twenty owners (fifteen
   delegated, five stated with witnesses) and twenty-nine probes. Measured
   rather than asserted — the probe gate reports zero `oci.py` mentions and the
   ownership gate's unowned list contains none. `assignment_roots` is a
   declared operand; `identity` deliberately is not, because this gate reads
   public FUNCTIONS and it is a constructor operand.
5. [done] `tests/manager/test_oci_engine.py`: the real-engine cycle for Docker
   and Podman, skipped per engine when the binary or daemon is absent, with a
   case requiring the covered engines and `ENGINES` to be the same list.
6. [done] `PROGRESS.md` and
   `evidence/gate-after-correction-2026-08-25.txt`.

The pre-existing twelve this campaign has carried are now seven, and the five
that went are this Work's. Nothing was added.
