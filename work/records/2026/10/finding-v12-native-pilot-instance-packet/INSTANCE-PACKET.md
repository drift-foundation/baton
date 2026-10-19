# The instance-specific native v12 pilot packet — W325959

**Preparation only.** Nothing in this dossier has been installed, submitted,
served or executed. Every routine value is **resolved** here, as the FINDING
instructs — this is not a questionnaire. What remains unresolved is exactly two
classes, both named with their evidence: `BUILD:` values that are digests of
build outputs this preparation may not silently produce, and `READBACK:` values
that supported preparation generates in an earlier step.

What keeps it non-executable is therefore **not** a validator, and this packet
says so because the verification run proved it: with the routine values
resolved, `bootstrap.validated` ACCEPTS the configuration pass one would emit.
The gates are `bootstrap.admit`, which refuses an install with no built runtime
("needs a built runtime; name it with `--distro`") and one whose distro is not
there; the two worker images, which do not exist; and the owner's launch
selection, which is not this Work's. Evidence:
`verification/scenario-2-install-inputs-closed-and-refusing.json`.

Owner selection: `baton:work/records/2026/10/finding-v12-development-coordination-pilot/SELECTION-325909.md`
(M325952 / E325954). Structural verification: **70 checks passed, 5 scenarios
observed, the self-check failed for its own named reason, 0 unexpected,
0.165s** — `verification/validate.py`, bound by `MANIFEST.json`.

## 1. The instance

| Fact | Value |
| --- | --- |
| Destination (fresh, retained) | `/home/sl/baton-instances/native-coordination-pilot-w321608-1` |
| Preflight, checked read-only this claim | the destination does not exist; its parent `/home/sl/baton-instances` does |
| Refuses to replace | `…/distro`, `…/justfile`, `…/instance.json` — a destination is prepared once |
| Retention | `retain`; Slawomir owns backup/restore |

The seventeen derived places are in
`verification/scenario-5-destination-fresh-and-pins-hold.json` under `layout`;
they are `tools.instance.layout`'s own answer for this destination, not a list
this packet composed.

## 2. Provenance — and one pin that MOVED since the W321690 packet

| Fact | Value |
| --- | --- |
| Selected source | `14e52d80679de5e844f72324df632da5e01cf393` |
| Difference from the W321690 packet's base | **not record-only.** `2aa8ca56` added `v12/python/tools/worker_visibility.py` (1004 lines) and `tests/tools/test_worker_visibility.py` (1426) between `372281f4` and this source |
| Installed surface | thirteen `baton-v12-stack` subcommands, unchanged: `bootstrap`, `disposition`, `identity`, `logs`, `manager`, `monitor`, `publish`, `record`, `repository`, `start`, `status`, `stop`, `view`. `worker_visibility` is a tool in the tree and **not** one of them |
| Packaged stack identity | `BUILD:` **built and read back** with `baton-v12-stack identity`; a commit is not a package identity and this packet does not infer one |
| Worker images | `BUILD:` validated immutable digests per role, recorded in their owning record as `tools/worker_image.py` requires. A fresh build result is a candidate, not a selection |

## 3. The Job shape, and why it is the control

Two stages: `implementation` and `review`. **No integration stage.** The
serving manager reaches `admit_accepted` / `continue_accepted` only through a
composed integration stage, so a Job that declares none cannot have the owner's
approval taken by configuration. W321690 drove this
(`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/composition-325757/`,
32 checks), and `bootstrap`'s own validator says the same thing in its own
words: the integration role is **optional** — "owner 2026-09-20T14:57:48Z
(W202663, the PR model): integration is a human act or an explicitly submitted
ordinary Job, never an obligatory worker".

Two consequences this packet does not hide:

* the `integration_profile` **document** is still a REQUIRED bootstrap input,
  so its four members — including `integrator_participant` — must be named
  even though no integration stage is submitted;
* integration is therefore the **human's** act, recorded by
  `disposition integrated` against a human integration record.

## 4. Participants, routes and grants

Proposed addresses (reviewable; the owner's to confirm):

| Role | Address | Grants | Route |
| --- | --- | --- | --- |
| implementation worker | `baton.claude-pilot` | none; acts by claim | served on `impl`; its ending hands the Work to `rview` |
| review worker | `baton.reviewer-pilot` | none; acts by claim | served on `rview`; its ending hands the Work to the **owner route** `owner` |
| verification receipt actor | `baton.verifier-pilot` | `verify` | — |
| review receipt actor | `baton.reviewer-receipt-pilot` | `review` | — |
| human owner | `baton.slaw` | `approve`, `integrate`, `close` — and **never** `verify` or `review` | the owner route |
| integrator (profile member only) | `baton.integrator-pilot` | `integrate` | unused on this path |
| diagnostic handler | `baton.diagnostician-pilot` | `manage-work-labels` if labels are used | the dedicated `diagnosis` route; nothing routes an exceptional stage automatically |

`bootstrap` enforces the independence rule itself: implementation and review
may share no participant. The producer and the reviewer above are distinct, and
the review **receipt** actor is distinct from both the owner and the verifier.

Grants are written in each bound Work's own scope, and the **policy generation
must be read back after the install and compared before any dependent
operation** — a fixture generation is not a production pin.

## 5. The ordered operator commands

`bootstrap` **defers** `jobs` and `workers` from a fresh install: a worker's
`deployment` carries a digest-sealed input manifest naming the Authority and
the Work, which cannot be written before the instance exists. Preparation is
therefore two bootstrap passes, and this packet says so rather than pretending
one command composes everything.

1. **Build the distro** from `packaging/stack.spec` at the selected source, and
   record its identity: `baton-v12-stack identity`. Host-specific by
   construction.
2. **Preflight** the destination: it must not exist, and its `distro`,
   `justfile` and `instance.json` names must be free.
3. **Pass one — install the instance.**
   `bootstrap --inputs configuration/install-inputs.json --destination
   /home/sl/baton-instances/native-coordination-pilot-w321608-1 --distro
   <built distro>`
   Configures no worker and no Job. Generates the Authority identity once and
   persists it at `…/authority-identity.json`.
4. **Read back** the authority UUID, the policy generation, and the instance
   selector. Set and read back the canonical target; it must equal
   `14e52d80679de5e844f72324df632da5e01cf393`, which is the base the task
   document pins. If it differs, the task document is wrong and must be
   re-pinned rather than worked around.
5. **Create the pilot Work** in the Authority on the implementation route, and
   bind its canonical dossier with `record bind` — the human integration
   citation refuses without a bound dossier (W325034's recorded operator trap).
   Allocate the dossier locator under the W39435 grammar.
6. **Compose the input manifest** for each role from the created Work: its
   `work_ref` carries the authority UUID and the Work id, and its
   `runtime_profile_digest`, `policy_digest` and `worker_image_digest` must
   equal the worker document's own three. Stage the task document at
   `…/state/task/w321608-native-operator-quickstart.json`.
7. **Pass two — configure the pool and the binding.**
   `bootstrap --inputs configuration/job-inputs.json --destination …`
   A repeated bootstrap preserves what is there and refuses a changed
   selection, so every pass-one member is repeated verbatim.
8. **Submit** `configuration/submission.json` and **serve**: `manager`, with
   `status` for state and `logs` for one attempt's retained raw output.
9. **Judge independently**: the verification actor's `Session.verify` after
   evaluating the evidence itself — the five clauses are `task_id`,
   `task_digest`, `argv`, `input_manifest_digest` and a status of exactly `0`,
   against `Integration.required_tests` — then the review actor's
   `Session.review`. The approval stays absent.
10. **The owner, once**: `disposition pending` (expect `approval-due`) →
    `disposition approve` → `disposition integrated` citing the human
    integration record → `disposition close --outcome satisfying`, then read it
    back. An honest unhappy ending is `close --outcome non-satisfying` with the
    operator's own rationale.
11. **Diagnosis, if a stage goes exceptional**: notice it in `status`, read
    `logs`, then either add the diagnostic handler to the Work's route and let
    that participant claim it, or create a dedicated diagnostic Work on its own
    route. Nothing routes it automatically. An unknown runtime keeps its hold.

## 6. Limits — and what the product does NOT express

The Job carries exactly two settable members, and this submission sets both:

| Member | Value |
| --- | --- |
| `provider_turn_seconds` | 3600 |
| `verification_command_seconds` | 900 |

Deployment defaults at generation `1`: `provider_turn` 3600,
`ordinary_verification` 900, `integration_verification` 1800,
`host_verification` 300; bounds 1 and 86400.

**There is no total and no cleanup reserve to configure.**
`execution_limits` says so in its own words: each value is a per-invocation
ceiling, and "none of them is a cumulative allowance, a remaining balance, a
budget the Job spends down, or a limit on how long an agent may work in total";
cumulative accounting and per-role pools are deferred. So the total and the
cleanup allowance the selection asks for are an **operator-side wall-clock
envelope**, not settings:

* one implementation turn ≤ 3600 s + its verification ≤ 900 s;
* one review turn ≤ 3600 s + its verification ≤ 900 s;
* teardown: the engine stop timeout is 30 s per runtime
  (`oci.stop_vector`'s default), and cleanup is settled on positive absence of
  the exact runtime identity — so reserve wall-clock for it rather than
  assuming it is instant;
* a sensible envelope for one attempt of each stage is therefore ≈ 2.6 h of
  provider and verification ceilings plus the operator's own cleanup window.
  **This envelope is advisory arithmetic, not a configured limit**, and nothing
  in the product enforces it.

## 7. The task and the check (fully pinned)

`configuration/task.json`, schema `baton.dogfood-task/2`, task id
`w321608-native-operator-quickstart`, declared base
`14e52d80679de5e844f72324df632da5e01cf393`, source profile `git-line`. It
validates through the workload's own owner (`dogfood_operator.held_task`), and
its sealed canonical bytes — the form `_copied_task` writes — digest to
`5ec48d4baf2020a8ef972237444c5989cf8490dea23cc285dbfd3bc0508dc1bb` (1853
bytes).

The Work authors `v12/QUICKSTART.md` with four required headings. The
verification argv is closed and deterministic — `python3 -c <structural
check>` — and it was **run against five candidates** in a temporary directory
during preparation: it accepts a complete quickstart, and refuses a missing
section, a document below its length floor, an unresolved `TODO`/`TBD`/`FIXME`
marker, and an absent file. Evidence:
`verification/scenario-1-task-document-immutable-and-owned.json`.

`test_scope` is `["v12/QUICKSTART.md"]` and `terminal_policy` is
`report-and-hold`, which is this build's only terminal policy.

## 8. Resolved here, and what genuinely remains

The owner delegated resolution of routine values, so these are **resolved** in
the authored documents rather than asked about:

| Value | Resolved to | On what basis |
| --- | --- | --- |
| `checkpoint_profile` | `git` | `checkpoint_profiles.GIT_PROFILE` |
| `integration_profile.profile_kind` / `.profile_version` | `git` / `1` | the shipped `v12/instance-inputs.json` shape and the git profile |
| `integration_profile.integrator_participant` | `baton.integrator-pilot` | bootstrap requires the member; no integration stage is submitted |
| `retention_policy_digest` | `sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a` | **recomputed this claim** as the sha256 of `v12/instance-retention.md`, which is what the shipped instance inputs also name |
| `retention_disposition` | `retain` | the selected retained destination |
| `pool_generation` / `policy_generation` | `1` / `1` | positive integers; the policy generation is re-read in step 4 and compared before any dependent grant |
| receipt actors | `baton.verifier-pilot`, `baton.reviewer-receipt-pilot`, approval `baton.slaw` | verify/review separated from the owner |
| owner | `baton.slaw` with `approve`, `integrate`, `close` and never `verify`/`review` | the selection |
| worker participants | `baton.claude-pilot` (implementation), `baton.reviewer-pilot` (review) | distinct participants and new native addresses — not an impersonation of the v11 identities |
| owner route | `owner`, handled by `baton.slaw` | the review worker's `review_route` |
| diagnostic route / handler | `diagnosis`, handled by `baton.diagnostician-pilot` | a dedicated diagnostic Work on its own route per W325035; nothing routes automatically |
| `engine` | `docker` | `/usr/bin/docker` is present on this host and `podman` is not; `ENGINES` admits exactly these two |
| `network` | `none` | no provider execution is selected |
| `credential_sources` / `_slots` / `_profile` | `null` / `[]` / `{}` | "no provider call is selected", said in the document rather than only in prose |
| `workspace_group` | `1000` | this host's own group id (`id -g`) |
| `workspace_capacity.max_bytes` | `167772160` | twice `source_boundary.MIN_WORKSPACE_BYTES` (83886080), the floor the boundary enforces |
| `profile_name` | `pilot-implementation` / `pilot-review` | named per role |
| `adapter_name` | `agent-session-1.0` | `bootstrap.EXPECTED_ASSETS` names it |
| `launch_contract` / `launch_role` | `v12-assignment-1` / the role | the assignment contract this build serves |
| paths | under the destination | `tools.instance.layout`'s own answer |
| task, check argv, `test_scope`, `terminal_policy`, limits | §6 and §7 | pinned, and the check is run |

**What genuinely remains — five build outputs and six readbacks.**

`BUILD:` — each carries its concrete separately-selectable command in the
document itself, and none is performed here:

1. the packaged stack distro and its identity — `just build` from `v12/`, then
   `baton-v12-stack identity`;
2. the implementation worker image digest — `worker-image ROLE=implementation`;
3. the review worker image digest — `worker-image ROLE=review`;
4. the runtime profile digests and the policy digest the pool admits —
   `pool-profile` / `pool-policy`, read back from `pool`;
5. the integrator instructions digest — the integration bundle's own recorded
   value. Never compared on this path, because no integration stage is
   submitted; bootstrap requires the member.

`READBACK:` — generated by supported preparation, and deliberately not
invented here: the authority UUID, each participant's principal, the policy
generation, the Work id, each role's input manifest, and the Job's
`input_digest` (`job_input_identity` of that manifest).

**The owner still selects one thing that is not a value in a document:**
whether provider-backed execution is selected at all. Everything here is
deterministic; the documents say `network: none` and no credential, and a
provider-backed attempt would need its own stated provider question plus
credential and network references — bound by reference, never by content.

Two protections that are **not** where one might assume, established by the
verification run rather than asserted:

1. `bootstrap.held` validates presence and relationships, not value formats.
2. The Job manager's submission validator takes `input_digest` and
   `policy_digest` through `boundaries.text` — opaque at that layer by design;
   they are proved where the manifest is cross-bound (`single_worker._held`)
   and by `stage_execution`'s `sha256:<64 hex>` rule.

## 9. Result, recovery and rollback

Result reading: `status` for stage state, `logs` for one attempt's retained raw
output, and the Authority's own `proposals_of` / `receipt` reads for the
authoritative candidate and receipt inventory. A completed stage is not an
accepted candidate.

Recovery is W321688's contract, cited and not re-proved:
`baton:work/records/2026/10/finding-v12-pilot-dossier-binding/RECOVERY.md`.
`record recovery-manifest` emits the closed set; **`record recovery-check`
reports and refuses — it never admits anything**, and a clean report is the
precondition for an operator's admission, not the admission. Three obligations
stay the operator's: stop admissions (not merely the supervisor), positively
account for every runtime and launch, and admit **one** writable instance.
A manager restarted over the same instance retains exact ownership
(W325035 `matrix-325259` scenario 3); that is **not** backup restoration, not
failover, and not fencing of a second writable copy.

Rollback before any admission leaves nothing behind but this dossier. After
admission: stop new pickup, cancel or fence the exact assignment through the
supported owners, account for every runtime, and close the Work
non-satisfying with the operator's own rationale. A cancelled assignment is
not a cancelled Work, and the runtime-quiescence gate survives a cancellation —
a re-claim is refused until it is discharged. Withdrawal preserves the native
history; no reverse migration to v11.

## 10. Boundaries of this preparation

No install, no submission, no serving, no container, no provider call, no
credential read, no store write, no deployment, no product source change, and
nothing that mutates this repository's history, index or working tree. The
verification run reads the authored documents, calls the validators that own
them, and runs the pinned check argv in a temporary directory. No fixture value
is presented as a production pin, and no accepted fixture receipt is presented
as a production receipt.
