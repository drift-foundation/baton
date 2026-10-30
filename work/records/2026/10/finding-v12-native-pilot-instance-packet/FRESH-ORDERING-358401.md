# Fresh-install ordering: what the supported bootstrap will and will not do in one call

Measured at claim358401 in a disposable root with a simulated repository runner
and a stub bundle. No production act, no Git, no live anything. This is the
research the fresh packet's command ordering depends on, recorded before the
packet is authored so the next claim does not have to rediscover it.

## Finding 1 — a fresh install DOES prepare the worker source repositories

The owner asked to *"use supported bootstrap with full worker repository
preparation where possible; do not carry the existing-destination manual clone
workaround into a fresh install without necessity."*

**It is possible.** Driving

    bootstrap.main(["--inputs", doc, "--destination", root,
                    "--distro", distro, "--repository-source", src])

with a document that carries `workers` prepared **all four** repositories:

    repositories  4 prepared under <root>/repo:
      target, workspace, source-implementation-pilot, source-review-pilot

because `bootstrap.repository_plan` derives one `source-<worker_id>` per entry
in `document["workers"]`. Destination 2 got only `target` and `workspace`
because the install input it was given carried **no workers** — that is the
whole origin of the "no supported operation adds a worker source repository to
a prepared destination" gap. **On a fresh destination the gap does not arise**,
and the manual clone step should not be carried forward.

The authority was also minted in the same call (`authority 1c8d7ed1…
generated for this instance`).

## Finding 2 — but it cannot be ONE call, and the reason is an ordering constraint

The same run then refused, **after** the repositories were prepared:

> refused: the deployment this document describes is not one the manager would
> accept, so nothing was prepared: … the document breaks type … Each worker's
> `deployment` member is the single-worker launch document `v12/python/DEPLOYMENT.md`
> specifies; this helper fills in only participant, principal, authority_store,
> authority_uuid and launch_role, and **names the rest as yours to select**.

The failing member is `input_manifest`: the packet's `configure-inputs.json`
carries it as a marker, because `configure.py` composes the real one at run
time. And composing it needs `work_ref = {authority_uuid, work_id}` — where:

- `authority_uuid` is **minted during this very call** (`bootstrap.identity`),
  and
- `work_id` must **carry that authority's prefix**, which
  `contracts/manifest.py` enforces.

So the manifest cannot be composed before the call that creates the authority
it must name. **A single fresh call cannot both mint the authority and carry a
manifest bound to it.**

**Note the ordering hazard this run demonstrated**: the repositories and the
authority were created and then the configuration refused, leaving a
destination holding four repositories and an identity but no deployment. The
product's own `[K3]` comment says admissions are settled before `prepare` has
effects — that holds for the *distro*, but repository preparation and identity
minting happen before the configuration schema is checked. **The packet must
therefore not hand a fresh destination a document it has not already validated
offline.**

## What this means for the packet's command ordering

The supported sequence is two bootstrap calls, and the first must still carry
`workers` so the repositories are prepared:

1. **Install** — `--inputs <install doc> --destination --distro
   --repository-source`, where the install doc carries `workers` **with a
   deployment the schema accepts** and **no `jobs`**, so all four repositories
   are prepared and the authority is minted without creating any Work.
   `PENDING(whether a worker deployment can satisfy the install-time schema
   with a placeholder-free manifest that names no Work — if it cannot, the
   install carries no workers and the worker-source gap returns, which is the
   one thing that would force the clone step back)`.
2. **Read back** the minted `authority_uuid` from
   `<destination>/authority-identity.json`.
3. **Compose** the Work id under that authority's prefix and seal the manifest
   against it — `configure.py`'s existing job, unchanged.
4. **Configure** — `--inputs <configure doc>` with **no** `--destination`,
   which is the in-place operation already proved at claim357725.

**Step 1's pending question is the one thing that decides whether the fresh
path is clean.** It is a focused offline question — compose a candidate install
document and see whether `bootstrap.held` accepts a worker whose
`input_manifest` is absent or minimal — and it must be answered before the
packet's commands are written, not asserted.

## Limits

Disposable root, simulated repository runner, stub bundle satisfying `admit`'s
identity checks. This establishes the **ordering**, not that any real bundle or
real clone behaves this way. Nothing here is evidence about instance 2 or 3,
and no instance 3 was created.
