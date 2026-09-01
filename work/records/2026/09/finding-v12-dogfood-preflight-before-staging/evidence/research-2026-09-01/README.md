# Research evidence — 2026-09-01

## Retained live attempt

`/tmp/w62098/run1` still contains the failed dogfood attempt. Public files and
filesystem state show:

- `storage/attempt-w62098-run1/` was allocated with all five manager-owned
  child roots;
- `inputs/source/` contains the complete staged source subset;
- the separately provisioned `launch/` and `credential-home/` remain empty;
- no attempt evidence record was written.

The Work thread records the first refusal as
`policy/profile-uncertified`. After public profile certification, the same
attempt identity stopped at the existing-source stage-once refusal. The
current `setup.py` was amended after the failure and now includes the missing
certification, so it is not evidence of the original setup ordering.

## Focused reproduction

Run from `v12/python`:

```text
PYTHONPATH=src:. python3 \
  ../../work/records/2026/09/finding-v12-dogfood-preflight-before-staging/evidence/research-2026-09-01/reproduce_uncertified_profile.py
```

The reproduction uses the real `ControlStore`, workspace allocation,
`stage_source`, and offer implementation from the existing effectively-once
arc fixture. It varies only profile certification. Baseline output on
2026-09-01:

```json
{
  "first_run": {
    "attempt_root_exists": true,
    "authority_calls": ["project_work"],
    "category": "policy",
    "code": "profile-uncertified",
    "provider_turns": 0,
    "runtime_starts": 0,
    "source_root_exists": true
  },
  "same_attempt_after_certification": "... already exists; an attempt stages its source once ..."
}
```

This distinguishes three facts: the manager committed no offer, claim, or
runtime; it nevertheless allocated and staged durable input; and the correct
stage-once guard then made that attempt identity non-retryable.

## Code-path closure

The current order in `tools/dogfood_operator.py::run_dogfood_task` is:

1. pure grant/task `preflight`;
2. `configured_workspace_group`;
3. `workspaces.assignment_workspace` (allocates the attempt root);
4. `stage_source` (copies the source once);
5. `input_manifest`;
6. `issue_offer`.

`worker_manager/offers.py::issue_offer` first reads the authority Work and
then calls private `_certified(store, "runtime", profile_name)`. Missing or
mismatched certification raises `policy/profile-uncertified` before the offer
transaction and before bearer minting. There is no public read/require
operation for deployment code to apply the same certification rule earlier;
only mutating `certify_profile` is exported.

Two adjacent immutable deployment checks are also late or absent:

- `_launched` reads the configured workspace group, but the granted
  `storage` is never compared with
  `workspaces.configured_workspace_storage(store).place` before allocation.
  Custody later reads the configured storage, so a different granted root can
  stage and run before that contradiction surfaces.
- `credentials.resolved_delivery(credential_slots,
  profile=credential_profile)` is pure but is called lazily inside
  `adapter_of`, after offer acceptance, attempt recording, claim, activation,
  task delivery, and launch-document materialization. An invalid slot or an
  unmapped provider therefore consumes durable attempt state before refusing.

The group, storage, certification and credential resolution are all facts of
the already-open control-store/deployment configuration. None needs source
bytes, a bearer, authority mutation, workspace allocation, or an engine.

## Recommended boundary

Add one shared deployment-readiness operation, called by both the documented
launcher and direct `run_dogfood_task` callers before
`assignment_workspace`. It should return the held values that later acts
consume rather than validate and discard them:

- the configured `WorkspaceGroup`;
- the configured `WorkspaceStorage`, required to name exactly the granted
  `storage` path;
- the resolved credential mapping tuple;
- a generic, public Worker Manager certification requirement for
  `(kind, name, digest)`, with `issue_offer` retaining the same authoritative
  check.

The public certification reader/requirement should own the existing
`_certified` adoption and refusal semantics; the dogfood deployment must not
query manager tables or copy those rules. `issue_offer` must recheck because
offer issuance is its own receiving boundary, not because deployment
certification is expected to change underneath an attempt.

The early check is a fail-fast deployment guarantee, not a reservation.
Mutable Work eligibility (open/queued/unclaimed/ungated), participant
capacity, offer expiry, and the offer CAS stay solely authoritative in
`issue_offer`. Moving or duplicating those reads would add a race without
making source staging atomic with authority state.

## Regression boundary

The negative arc regression should start with a configured group/storage but
no `dogfood` profile certification, and assert:

- no attempt root at all (not merely an empty `inputs/source`);
- no offer, bearer mint, claim, attempt record, activation, launch root,
  credential provider call, runtime, or worker conversation;
- after certification, the *same* attempt identity succeeds because the
  failed preflight left no attempt state;
- after actual staging/success, an exact rerun still stops at the existing
  source and starts no second runtime/provider turn.

Add parallel negative cases for configured-storage absence/mismatch and an
unmapped credential slot. Each must leave the same zero-allocation footprint.

## Configuration stability

The legacy offer-profile certification is immutable within one control store:
`certify_profile` journals under the fixed operation identity
`profile.certify:<kind>:<name>`, with the digest in its signature. Repeating the
same digest replays; naming another digest is an operation collision. There is
no withdrawal operation for this certification. Workspace group and storage
configuration have the same one-store immutability rule, and a different
storage is expressly refused because it would orphan existing attempts.

Consequently a successful early read cannot be invalidated through the public
manager API before `issue_offer`. A concurrent first certification may make an
early absent read conservatively refuse, but it leaves no attempt state and
the same identity can retry. No configuration generation or reservation is
needed for this Work.

## Verification run

On 2026-09-01, the reproduction produced the baseline above. The three
existing `TheArcIsEffectivelyOnceAndAFreshAttemptIsFresh` cases passed, as did
the offer suite's focused absent- and mismatched-certification cases. These
are baseline checks only. A focused public-API probe also confirmed that an
exact certification replays and a changed digest answers
`refused/operation-collision`. No product implementation or new regression
has been added by this reviewer Work.
