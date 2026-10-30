# The supported configuration path, and what `configure.py` must become

Recorded at claim357676 answering `review-2026-10-23T03-04-01Z.md`. These are
**verified source facts**, not a plan I am asserting. The rewrite they imply is
**not done** — see PROGRESS for what remains.

## 1. The supported in-place configuration operation exists, and I had not used it

`bootstrap.main(["--inputs", <document>])` **without** `--destination` runs
`prepare(document, installing=False)`, composing the deployment from
`document["state_root"]`. The `v12/justfile` says this in its own words:
*"Without those two operands this composes the deployment in place and installs
nothing, which is the older form and still works."*

`prepare` (`bootstrap.py:1248`) proves everything before composing, and
critically **reuses this root's existing Authority**:

> *"A root that already has a record keeps the Authority that record names; a
> fresh one is given a new identity here"* — `bootstrap.py:1270-1274`

So configuring the already-installed destination 2 against authority
`673355e1…` is the supported operation, and it refuses conflicts
(`record_of` / `conflicts`) **before opening any store**.

## 2. The supported operation ALSO performs the registration

This is the structural finding, and it makes my `configure.py` wrong rather
than merely incomplete. `bootstrap` itself does:

| Line | Operation |
|---|---|
| `bootstrap.py:731` | `authority.add_route_handler(route, worker["participant"])` |
| `:746` | `authority.create_work(job["work_id"], ROUTES["implementation"], …)` |
| `:758` | `authority.grant_capability(receipt_participants[name], …)` |
| `:760` | `authority.grant_capability(integrator, INTEGRATOR_GRANT, scope=scope)` |
| `:771` | `authority.grant_capability(owner, capability, scope=scope)` |

**So `configure.py` must not register anything itself.** My own `register()`
duplicated the supported operation *and* was the direct cause of the
review's finding 3: it wrote routes, the Work and grants **before**
`sealed_task` or `configuration` could reject a conflict. Removing it removes
the ordering defect at its root rather than reordering around it.

The corrected shape is: **preflight → compose the whole document → one
supported call → read back → validate.**

## 3. The Work identity claim was misleading, and here is the accurate statement

**Withdrawn**: that the Work id is "resolved from readback, never presumed."
`configure.register` defaulted to `uuid[:8] + "-W1"` and then read that same
chosen string back. Reading back a value you chose is not evidence that you did
not choose it. The review is right, and `prove.py`'s check that "the resolved
Work came from the authority, not a guess" was asserting something it did not
establish.

**Accurate**: the Work id is a **selection in the configuration input**.
`bootstrap.py:746` calls `create_work(job["work_id"], …)` with the identifier
the document names, and `create_work` **refuses a collision** — which is the
real safety property. There is no allocator that hands one back, and inventing
one is out of scope. So the honest description is:

> `jobs[0].work_id` is chosen by the packet, created by the supported
> `bootstrap` operation, and **collision-checked by the authority**. It is not
> allocated by the authority and must not be described as a readback. What
> *is* a readback is the Work's projection — its scope, route and status —
> after creation.

The packet's `READBACK:` marker on `work_id` is therefore also wrong as
written. It should say `SELECTED(…)` with the collision refusal named.

## 4. The manifest cross-binding, with the exact values

Confirmed by direct comparison, the inherited manifest in
`revision-4/inputs/deployment.json` carries values that **disagree with the
workers that would consume it**:

| Member | Inherited manifest | What the new workers name |
|---|---|---|
| `policy_digest` | `sha256:3a532add…` | `sha256:837d7a03…` |
| `retention_policy_digest` | `sha256:cccccccc…` (a placeholder) | `sha256:0f4cd2d1…` |

`revision-4/configuration/manifest-inputs.json` supplies the replacements:

- `content_derived_and_recomputed_from_the_frozen_copies` — four members:
  `adapter_digest`, `policy_digest`, `retention_policy_digest`,
  `runtime_profile_digest`.
- `proposed_accountability_documents` — seven members:
  `credential_policy_digest`, `mount_policy_digest`, `network_policy_digest`,
  `resource_policy_digest`, `role_instructions_digest`, `tool_policy_digest`,
  `toolchain_digest`.

`revision-4/prepare.py:314-320` is the loop that applies all eleven, and the
seal comes **after** them. My `sealed_manifest` omitted every one of them, so
it produced **a valid seal over stale and placeholder content** — which, as the
review says, is not correct evidence. A `cccc…` retention digest surviving into
a sealed manifest is the clearest symptom.

## 5. What the proof must then validate

Not `check_manifest_structure` and `owned_submission` alone — those are
structural. The real consumer is **`tools/stage_execution.held_configuration`**
(`:516`), which *"proves one closed deployment document before anything is
opened"*, sweeps for secrets first, and replaces each worker's deployment with
the owned form `single_worker._held` derives. The proof must read back the
**installed `deployment.json`** that the supported operation wrote and put it
through that function, plus cross-bind worker ↔ manifest ↔ submission
policy/profile/source/task identities.

And it must demonstrate a **conflict discovered after the supported call would
have begun** — leaving no unintended registration and no overwritten output —
rather than relying on a duplicate check that only covers a successful previous
run.
