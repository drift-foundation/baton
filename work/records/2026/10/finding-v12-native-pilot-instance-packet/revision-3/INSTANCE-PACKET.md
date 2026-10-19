# The instance-specific native v12 pilot packet — W325959, revision 3

Revisions 1 and 2 are preserved unedited with their own manifests (revision 2's
digest as the review published it:
`e6dadbbc2f8009b7ddc5ed49d8fda6755162a27f81d5f34214ca60e4ef99b6c9`).

Review 2026-10-18T20-29-02Z proved four faults in revision 2. All four are
corrected, and the documented sequence and the exercised one are now the same
operations. `prepare.py`, one run in a labelled disposable root: **83 checks
passed, 4 scenarios observed, the self-check failed for its own named reason,
0 unexpected, 0.207s**, `selected_destination_untouched: true`. Evidence:
`evidence/PREPARATION.json` + four scenario records; `MANIFEST.json` binds
everything; `FROZEN-INPUTS.json` binds what this packet consumes.

## R1 — the submitted input identity is the public projection

Revision 2 resolved `input_digest` with a SHA-256 of the whole manifest. The
reviewer proved that unequal to `contracts.job_input_identity`, which projects
out the role-specific members (`worker_image_digest`, `toolchain_digest`,
`runtime_profile_digest`, `credential_policy_digest`,
`role_instructions_digest`, `manifest_id`, `created_at`, `manifest_digest`)
before the canonical digest. The driver now calls the public function and
records both values side by side, and proves the projection's two properties:
changing the worker image digest does **not** move the identity; changing an
included policy identity **does**.

**And the runtime consumer boundary is asked, without launching anything.**
`stage_execution._disagreements` is `single_worker._matches`'s own operand
comparison. For both configured workers against their stages, the Job and the
binding, it answers **empty** — and when the Job names another input it
answers non-empty. `bootstrap.configuration(document, principals)` is now
called with its real signature (two operands, not three), its emission is
validated by `bootstrap.validated`, and both workers' resolved principals are
checked. Revision 2 passed `principals` twice and merely *noted* the
`TypeError`, which proved nothing.

## R2 — one installation, then the in-place configuration pass

Revision 2's step 9 told the operator to run the install recipe again with a
`DESTINATION`; `bootstrap.admit` (1877-1896) refuses an installed destination
that already carries a distro, a justfile and an instance selector. So the
documented command could not have worked while the driver proved something
else. The supported sequence, which is exactly what the driver exercises:

1. `just -f v12/justfile setup`
2. `just -f v12/justfile build` → the distro at `v12/python/build/out/distro`
3. `<distro>/baton-v12-stack identity` — record what was built
4. **The one installation:**
   `just -f v12/justfile bootstrap <this dossier>/revision-3/configuration/install-inputs.json /home/sl/baton-instances/native-coordination-pilot-w321608-1 v12/python/build/out/distro`
   It copies the runtime to the destination, composes the Authority, derives
   the repository and storage layout, and writes the one `instance.json`.
   Configures no worker and binds no Job.
5. **Readbacks:** `authority-identity.json`, the emitted `deployment.json`,
   `Authority.stored_identity` (kind and UUID), `policy_generation()`. Set and
   read back the canonical target; it must equal `14e52d80…`.
6. **Source acquisition and base readback.** The install prepares the
   instance's repositories from the checkout it ran in (or
   `--repository-source <checkout>`), and the git-line checkpoint profile
   clones and detaches at the declared base. **The disposable proof does not
   establish this**: its nominated source is an empty directory, so acquisition
   and base availability are unproven there, and the operator must read the
   prepared `…/repo/source` and confirm its head is the pinned base before
   configuring. Said plainly rather than implied.
7. **Register the two routes `bootstrap` does not** and create the pilot Work;
   bind a flat W39435 dossier locator (`native-pilot-quickstart-<8 hex>`).
8. **Grant the receipts per Work** and read each back.
9. **Compose the input manifest** (§R4) and stage the task document.
10. **The in-place configuration pass** — not a second installation:
    `cd v12/python && PYTHONPATH=src:. python3 -m tools.bootstrap --inputs <this dossier>/revision-3/configuration/configure-inputs.json`
    with the readbacks filled in and `state_root` the installed destination.
    Driven in scenario 3: accepted, repeated without change, the
    install-derived `workspace_storage`, `launch_home`, `credential_home` and
    `nominated_source` all preserved, and a changed `line_declared_base`
    **refused** with the original binding intact.
11. **Submit** `configuration/submission.json`; serve with
    `just -f v12/justfile start <destination>`; watch with `status` /
    `monitor`; read retained output with the installed `logs` subcommand.
12. Judge and dispose exactly as the accepted W321690 packet §9 says.

**No `pool add` step.** `tools/pool.py` takes `--worker <a worker document
filename>`, not an id, and `bootstrap` already supplies both workers in the
emitted configuration — so revision 2's step 10 was both wrong in its operand
and unnecessary. Omitted.

## R3 — `worker_image` builds; it is not a read-only check

`worker_image._main` (384-440) builds, saves, normalizes, loads and cleans an
image. Revision 2 called `python3 -m tools.worker_image --tag …` a
"re-validation engine read"; that was wrong and is corrected here and in the
driver's own provenance note. A **build** is a separately selected act. A
read-only presence check of the recorded digest is an engine *inspect*, and
this preparation performs neither.

## R4 — frozen inputs, and the concrete missing documents

**Frozen.** The documents this packet consumes are copied into `inputs/` and
digested in `FROZEN-INPUTS.json`: the prior instance's `deployment.json`,
`policy.json`, `runtime-profile.json`, `adapter.json`, and this tree's
`instance-retention.md`. Preparation reads the frozen copies, not a mutable
path. Recomputed from them this claim: `policy_digest` is the canonical digest
of `policy.json`, `profile_digest` of `runtime-profile.json`, `adapter_digest`
of `adapter.json`, `retention_policy_digest` the sha256 of
`instance-retention.md` (21 checks in scenario 4).

**The seven that remain are missing documents, not owner homework.**
`resource_`, `network_`, `mount_`, `tool_`, `credential_policy_digest`,
`role_instructions_digest` and `toolchain_digest` are repeated-hex placeholders
in the frozen prior deployment. No document for any of them exists in this tree
or in the frozen inputs, and **no product operation composes one** — and
`dogfood_operator.input_manifest` says why in its own words: *"EVERY POLICY
IDENTITY IS AN OPERAND … each names something the deployment is accountable
for. A tool that filled one in would be making a grant on an operator's
behalf, which is the one thing"* it may not do. So this packet names the gap
precisely instead of hashing a grant on the owner's behalf:

| In the Job input identity (must be real before launch) | Excluded from it |
| --- | --- |
| `resource_policy_digest`, `network_policy_digest`, `mount_policy_digest`, `tool_policy_digest` | `credential_policy_digest`, `role_instructions_digest`, `toolchain_digest` |

The four on the left change what the Job is admitted under; the three on the
right do not (`contracts.manifest.JOB_INPUT_EXCLUDED`).
`configuration/manifest-inputs.json` records this split and the reason.

**The manifest itself** is adapted from the frozen `deployment.json` — its
nominated-mount source descriptor (which declares `baton.source-boundary/1`),
outputs and policy identities — with the Work reference, human contract and
manifest id replaced, sealed **last** with the canonical digest the manager
recomputes, and held to `check_manifest_structure`. There is no composer in the
tree for the nominated-mount shape; `dogfood_operator.input_manifest` composes
the staged shape, which the stage deployment refuses.

## Limits, stated as limits

| Window | Value | Status |
| --- | --- | --- |
| one provider turn + its verification | ≤ 4500 s | the two per-invocation ceilings |
| one attempt pair, at one invocation each | ≤ 9000 s | **conditional on that invocation count**, not a proven worst case |
| per-runtime stop | 30 s | `oci.stop_vector` default |
| cleanup settle, two runtimes | ≤ 120 s | **proposed observation allowance** — no engine cleanup was observed in any run here, and an unknown runtime **retains its hold** rather than expiring; this is not an upper bound on cessation |

There is no product total or cleanup setting and none is invented.
Supervision: `status` for process health and the runtime boundary, `monitor` to
watch, `stop <destination>` for the processes this stack owns — non-zero when
an owned process cannot be resolved, because stopping a supervisor is not
evidence that what it started has finished. `record recovery-check` reports and
refuses; it never admits. Admit one writable instance.

## What remains

* **The engine-side facts**: whether the reused `image_digest` is present on
  the host (an inspect), and any rebuild (a separately selected build).
* **The four in-identity accountability documents** above.
* **Source acquisition and base readback** at install time (§R2 step 6),
  unproven by the disposable run.
* **The owner's launch selection.** This packet binds a provider-backed
  configuration by reference — `network: bridge`, `credential_slots:
  ["claude"]`, profile `{"claude": {"provider": "operator-file", "reference":
  "w202663-development"}}`, sources `/home/sl/.baton/credential-sources.json`
  whose existence is checked and whose content is never read — and calls
  nothing.
* The structural task check establishes four headings, a length floor and the
  absence of markers; it is **not** a usefulness judgment, and the filler prose
  used to exercise it is not a quickstart.

## Boundaries of this revision

No install into the selected destination (it still does not exist), no engine
call, no provider call, no credential content read, no image build or inspect,
no submission to a manager, no `start`, no product source change, no raw SQL,
and nothing that mutates this repository's history, index or working tree. The
disposable root is labelled `w325959-preflight`; `prepare.py` refuses any root
without that label and refuses the selected destination outright.
