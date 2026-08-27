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

## Independent correction re-review — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T15-07-37Z.md`.

1. [confirmed corrected] The preceding 56 OCI unit methods remain green;
   filesystem-canonical roots/sources, overlap refusal, mismatch-before-start,
   and the OCI inventory additions are present.
2. [required P0] Make positive absence require one supported engine's complete
   absence form naming the requested runtime; do not combine an absence phrase
   for one identity with the requested identity elsewhere in stderr.
3. [required P1] Restore the confirmed four-digest
   image/profile/policy/adapter identity.  Bind the running image and policy to
   restart reconciliation, including a stale-image negative case; same-image
   positive restart is insufficient.
4. [required P1] Make the engine cleanup proof query the manager-owned labels
   the smoke runtimes actually carry, require successful cleanup/query
   commands, and prove the resulting set empty.
5. [verification] Make all five additive methods green, rerun focused and OCI
   inventory gates, and rerun reachable Docker plus compatible Podman evidence
   with non-vacuous final cleanup.

## Fifth review correction — 2026-08-25

All three items from `review-2026-08-25T15-07-37Z.md` are done and the five
additive review methods are green.

1. [done] **[P0] Absence names the runtime in the sentence that states it.**
   Each engine's own complete form is pinned as a pattern that CAPTURES the
   identity, per engine rather than pooled, and only a captured identity equal
   to the one asked about is absence. Two fragments of one diagnostic are no
   longer an association.
2. [done] **[P1] The confirmed four-digest identity is restored**, and the case
   that counts the members asserts the tuple instead of naming a number.
3. [done] **[P1] The image survives the restart as the ENGINE'S fact**, read
   from the listing rather than from a label and measured against a real
   daemon. A listing naming no image, or naming a tag, is refused.
4. [done] **[P1] The policy survives the restart as a LABEL**, because no
   engine reports one. `runtime.labels` gains `policy_digest`; pinned in
   `FINDING.md` with the lifecycle consequence it reaches, which is flagged
   for the reviewer rather than absorbed silently.
5. [done] **[P1] The cleanup proof queries the label namespace the runtimes
   actually carry**, requires the query to have succeeded before reading its
   result as absence, and surfaces a removal the daemon refused.
6. [done] **The OCI inventory is complete again, measured.** One probe added:
   the identity envelope was probed and the digests inside it were not, and
   `_image_identity` is a new receiving boundary with a literal label.
7. [done] Focused `test_oci` 64, `test_oci_engine` 14 with Docker green,
   `test_attempts` 52; adjacent 522; boundary inventory back to the same seven
   pre-existing failures; full source suite and locked installed-layout build
   both 1189 with nine failures, none of them this correction's.
8. [next] Independent review — including of the lifecycle rule in item 4,
   which this Job reached rather than owns.

## Sixth review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T00-03-30Z.md`.

1. [done] Confirm the fifth correction's absence association, four-digest
   identity, engine-image/policy-label restart comparison, cleanup selector,
   original 64 OCI cases, 52 attempt cases, and source/build mirrors.
2. [next P0] Enumerate runtime candidates by stable attempt/assignment
   identity before comparing resolved profile/policy/adapter labels. A stale
   candidate must be returned and refused before `run`; an engine-side filter
   must not hide the mismatch as an empty set. Preserve ambiguity refusal and
   engine-reported image comparison.
3. [next] Revise the older every-label-filter assertion to the stable
   candidate-selector plus complete post-read comparison contract. This is
   case-specific confirmation to change that now-unsafe assertion.
4. [next P1] Check a mount target's raw inert spelling for `..` before
   `normpath`, keep the additive traversal regression, and emit only the
   canonical target.
5. [next] Rerun focused, inventory, reachable-engine, adjacent, source and
   installed-layout gates; append exact evidence and return for review.


## Sixth review correction — 2026-08-26

Both findings in `review-2026-08-26T00-03-30Z.md` are corrected and both
additive methods are green.

1. [done] **[P0] The candidate query is broader than the identity
   comparison.** `list_vector` filters on the attempt and the four parts of
   the assignment; the three resolved digests and the engine-reported image
   are compared in process, and a stale candidate is refused rather than
   hidden by the engine. `_CANDIDATE_LABELS` is derived from the frozen set
   minus the resolved identity.
2. [done] The whole label set is still owned before the engine is asked, so an
   invented or malformed label refuses before a query is composed.
3. [done] **[P1] The raw target spelling is checked for `..` before
   normalization**, and only the canonical spelling reaches the engine.
4. [done] **The pinned assertion is revised under the review's explicit
   confirmation.** `test_the_listing_filters_on_every_label` required a filter
   for every label — the defect as an expectation — and is now
   `test_the_listing_selects_candidates_and_never_pre_compares_identity`.
5. [done] `test_oci` 66 -> 70, with four added cases; both corrections
   measured to fail without them. `test_oci_engine` 14 green against docker
   29.1.3, which is what a fake could not establish. Adjacent 564 OK.
6. [done] Source suite and locked build both 1228 with eleven failures, and
   `test_oci` is not among them. Nothing added by this correction.
7. [next] Independent review.

## Seventh review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T02-14-24Z.md`.

1. [next P0] Narrow engine-side candidate selection to the minimal stable
   ownership key needed to enumerate this attempt. Do not pre-compare
   authority/work/participant/generation facts whose contradiction must be
   observed and refused rather than hidden as absence.
2. [next P0] After parsing a returned candidate's complete label record,
   compare every returned label with the request in process. Engine filters
   select rows; they do not prove the contents of a row. Preserve the separate
   engine-image and resolved-digest comparisons.
3. [next] Keep both additive regressions and revise the five-label selector
   assertion to the corrected minimal-selector contract. This is explicit,
   case-specific confirmation to change that unsafe expectation.
4. [next] Rerun focused OCI, reachable-engine, adjacent, source, and
   installed-layout gates; append exact evidence and return for review.


## Seventh review correction — 2026-08-26

`review-2026-08-26T02-14-24Z.md`'s one [P0] is corrected.

1. [done] **The selector is the minimal ownership key**, `runtime_attempt_id`
   alone. Any assignment fact used as a filter hides a runtime that
   contradicts it.
2. [done] **The complete returned record is compared in process** against the
   requested record, across the whole frozen label set, before adoption.
3. [done] The resolved-identity and engine-image comparisons and the ambiguity
   behaviour are preserved, as the review required.
4. [done] The selector assertion is revised a second time under the review's
   explicit confirmation: exactly one filter, and every other member of the
   frozen set asserted absent.
5. [done] `test_oci` 70 -> 74; both halves measured to fail without them.
   `test_oci_engine` 14 green against docker 29.1.3; adjacent 486 OK.
6. [done] Source suite and locked build RE-TAKEN so both describe one tree —
   the first pair straddled a reviewer's edit — and both now report 1244 with
   fifteen failures, none of them this Work's.
7. [done 2026-08-26] Independent review signed off the minimal selector,
   complete returned-record comparison, and preserved resolved-identity
   checks. No W6632 finding remains; see
   `review-2026-08-26T03-38-48Z.md`.
