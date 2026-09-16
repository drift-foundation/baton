# W183883 — the deployment inputs, corrected against the code

Written under claim185653, **corrected under claim185774** after review
2026-09-16T10-39-48Z [B1] showed three of its claims were wrong. The corrections
are stated first, because the superseded text was used to argue that the
bootstrap could not be written yet — and that argument was itself wrong.

Nothing here was obtained by running a deployment, submitting a Job, calling a
provider or starting an engine. No credential file was read.

## What this record got wrong, and what the code actually says

**1. `/2` is not "pool-only".** The first version repeated a module comment
saying the multi-worker variant "changes the POOL and nothing else".
`stage_execution._held_bindings` is the rule that matters:
`baton.v12.stage-execution-deployment/2` requires a **nonempty `job_bindings`
list**, one entry per Job, each carrying that Job's own Work, declared base,
canonical target and producing worker. A `/1` document **derives** its single
binding from members it already has, and is refused outright if it also names
`job_bindings` — two places for one fact is how they drift.

**2. There are not two Works per Job.** `_held_bindings` requires the
implementation and review Work IDs to be **equal within a binding**, and says
why: the accepted review-cycle provider keys one line by one
`(authority, work)` pair, and `attach_review` binds the reviewer to the writer's
own Work. A deployment that created distinct Works for those roles could never
attach its review. The first version's "job_work_id, review_work_id" phrasing
invited exactly that mistake.

**3. There is no fixed count of nine endpoints.** `_RECEIPT_MEMBERS` names
**three** receipt participants — verification, review, approval. `_minted`
**derives** the integrator from `integration_profile.integrator_participant`,
and the publisher from the producing worker's own participant, because
`Authority.publish` takes the producer's live assignment as its operand and a
session refuses to act on an assignment naming somebody else. The actual
selected set for a one-Job deployment sharing its integrator with its
integration worker is **six participants**, and `tools/bootstrap.py` derives it
rather than gating on a count. What *is* a rule is `INDEPENDENT`:
implementation and review may share neither participant nor principal.

**4. Capacity is per-Job affinity, not a producer count.** Each Job binds one
producer, one Work, one declared base and one canonical target. Jobs sharing a
canonical target are serialized at integration by the accepted composition. So
`bootstrap.capacity()` reports what is *configured* — workers by role, Jobs,
each Job's producer, and the distinct targets — and says in the record itself
that this is configured capacity rather than a concurrency guarantee.

The accepted composition reference is
`work/records/2026/09/finding-v12-multi-job-deployment/DEPLOYMENT-HANDOFF-2026-09-11.md`,
which selects `/2` plus `job_bindings` with each Job's held Work, source, base,
line and target. It is a composition reference, not reusable proof paths.

## What the bootstrap derives, with no owner secret

`tools/bootstrap.py` owns all of this. None of it is an operator input:

| Derived | How |
| --- | --- |
| the Authority store | `Authority.create` when absent, `Authority.open` when present, bound to the named uuid |
| every `principal` | `Authority.principal_of(participant)` — never configured, never spelled twice |
| each Job's Work | `Authority.create_work(work_id, "impl", operation_id=..., contract=...)`, left alone when it already exists |
| the three route handlers | `Authority.add_route_handler` for `impl`, `rview`, `integration` |
| the four grants per Work | `verify`, `review`, `approve` to the three receipt participants and `integrate` to the integrator, each in that Work's own scope |
| the external layout | one `state_root`: `authority.sqlite3`, `jobs.sqlite3`, `control.sqlite3`, `integration.sqlite3`, `state/`, `deployment.json` |
| the stage-execution document | `/1` or `/2` as the Jobs require, with `job_bindings` when there are several, and one Work written to both axes |
| the four exports `just start` needs | printed as copy-paste commands |

## What only the owner can supply

These are production selections. `bootstrap` refuses by name and does not
invent one — and a fixture digest, proof task or disposable credential is not a
production selection.

1. **`image_digest`, per worker.** `docker` is present here (server 29.1.3) with
   several `baton-w*` images, but every one is a proof or candidate tag from
   other Work. `tools/worker_image.py` is the accepted builder; the digest is
   the image config's content digest, not a tag.
2. **`adapter_name`, `adapter_digest`** — the deployment's fixed OCI adapter.
3. **`profile_name`, `profile_digest`, `policy_digest`.**
4. **`credential_sources`, `credential_slots`, `credential_profile`.** A private
   `baton.user-credential-sources/1` registry exists at
   `/home/sl/.baton/credential-sources.json`, mode `0600`. **Its contents were
   not read and must not enter source or any report.**
5. **`nominated_source`, `task_document`, `input_manifest`,
   `workspace_capacity`** — the per-Job workload.
6. **`canonical_target_id`, `line_declared_base`**, and the integration target
   and reference — the repository this deployment integrates into. v11 is not
   it, and this Work may not choose one.
7. **`workspace_group`** — a provisioned non-authority gid. Creating an OS group
   is outside this managed authority, so it returns as an exact operator
   command.
8. **`retention_policy_digest`** and `retention_disposition`.
9. **The participant endpoints** for the three stage roles and the three
   receipt roles, subject to `INDEPENDENT`.

Items 1–5 and 7 live inside each worker's `deployment` member, which
`single_worker._held` validates; the bootstrap carries that member through
verbatim and adds only what it derives.

## What was verified, and what was not

Verified read-only: `single_worker._MEMBERS`; `stage_execution._MEMBERS`,
`_WORKER_MEMBERS`, `_RECEIPT_MEMBERS`, `_BINDING_MEMBERS`, `INDEPENDENT`,
`_held_bindings` and `_minted`; the Authority API in
`src/baton_v12/authority/api.py`; `DEPLOYMENT.md`'s operand table; the presence
and mode of the credential registry; the presence of a container engine.

Verified by running: `tools/bootstrap.py` composes a real Authority, derives six
principals, creates the Work, adds the three routes and the four grants, emits
a `/1` document for one Job and a `/2` document with `job_bindings` for two, and
is repeatable — 28 focused checks.

NOT verified, and not claimed: that any existing image, adapter, profile or
credential on this machine is fit to be this deployment's production selection.
That remains the owner decision, and it is now the *only* thing standing between
this helper and a running deployment.
