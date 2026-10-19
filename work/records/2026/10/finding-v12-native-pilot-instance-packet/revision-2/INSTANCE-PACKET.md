# The instance-specific native v12 pilot packet — W325959, revision 2

Revision 1 (`../INSTANCE-PACKET.md`, `../configuration/`, `../verification/`)
is preserved unedited with its own manifest. This revision answers review
2026-10-18T20-17-05Z, whose four corrections were all correct.

**Preparation only, and now actually exercised.**
`prepare.py` composes this packet end to end in a **labelled disposable root**
(`/var/tmp/w325959-preflight`, never the selected destination) through the
*supported* `tools.bootstrap` entry point — the same one
`just -f v12/justfile bootstrap` execs — and retains the readbacks:
**72 checks passed, 4 scenarios observed, the self-check failed for its own
named reason, 0 unexpected, 0.196s**, with
`selected_destination_untouched: true`. Evidence: `evidence/PREPARATION.json`
and four scenario records, bound by `MANIFEST.json`.

## 1. What revision 1 got wrong, and what replaced it

| Review correction | Revision 2 |
| --- | --- |
| Five `just` recipes that do not exist (`stack-distro`, `worker-image ROLE=…`, `pool-policy`, `pool-profile`, `integration-bundle`) | §3's commands are read from the real `v12/justfile` and the real tool CLIs: `setup`, `build`, `bootstrap INPUTS DESTINATION [DISTRO]`, `start`/`stop`/`status`/`monitor DESTINATION`, `test-bootstrap ROOT`, plus `python3 -m tools.worker_image --tag … [--engine --context --dockerfile --platform]` and `python3 -m tools.pool add --deployment … --worker …` |
| Structural validation never composed pass two | `prepare.py` runs both passes, reads back what each made, and proves repetition and binding drift |
| Owner and diagnosis routes declared but never registered (`bootstrap._compose` registers worker stage routes only) | registered with `Authority.add_route_handler` and **proved by claim** — see §4 |
| `network: none` with no credential binds no workload that can do the task | the provider-backed pair is bound **by reference** from a prior validated instance: `network: bridge`, `credential_slots: ["claude"]`, `credential_profile: {"claude": {"provider": "operator-file", "reference": "w202663-development"}}`, `credential_sources: /home/sl/.baton/credential-sources.json` — references only, never content, and the launch gate stays the owner's (§7) |
| `_note` member nothing strips | gone; `configuration/job-inputs.json` carries only real members |
| Cleanup window unquantified | §6 |

## 2. Inputs reused with verified provenance, not invented

`evidence/scenario-4-the-reused-inputs-are-verified.json` recomputes each one
(21 checks). Source: `/home/sl/baton-instances/failed-reporting-w321528-324054/packet/deployment.json`,
a prior prepared instance of this same product.

| Value | Reused | Verified how |
| --- | --- | --- |
| `policy_digest` | `sha256:3a532add…` | **recomputed** as the canonical digest of that packet's `policy.json` |
| `profile_digest` / `profile_name` | `sha256:93fdea4a…` / `claude-fresh-implementation` | **recomputed** from `runtime-profile.json` |
| `adapter_digest` / `adapter_name` | `sha256:5f2ef38f…` / `docker-single-worker` | **recomputed** from `adapter.json` |
| `image_digest` | `sha256:c862c055…` | reused by reference with its provenance. Re-validating it is `python3 -m tools.worker_image --tag <selected tag>`, which is an **engine read this preparation does not perform** |
| `engine` / `network` | `docker` / `bridge` | that instance's own validated selection |
| credential slots, profile, sources | as above | reference only; the sources path exists on this host and its content is never read |
| `workspace_group` / `workspace_capacity` | `1000` / `83886081` | that instance's values; the floor is `MIN_WORKSPACE_BYTES` 83886080 |
| `launch_contract` | `v12-assignment-1` | unchanged |
| `retention_policy_digest` | `sha256:0f4cd2d1…` | **recomputed** as the sha256 of `v12/instance-retention.md` |
| `integration_profile.instructions_digest` | `sha256:fafc3595…` | that instance's value; never compared on this path, because no integration stage is submitted |

**Named, not hidden:** seven identities in the adapted input manifest
(`resource_`, `network_`, `mount_`, `tool_`, `credential_policy_digest`,
`role_instructions_digest`, `toolchain_digest`) are **repeated-hex
placeholders in that prior instance**. They compose and pass the manager's own
structure check, and before any launch the owner's real policy, tool, mount,
network, credential, role-instruction and toolchain documents must be digested
in their place. `configuration/manifest-inputs.json` lists exactly which.

## 3. The ordered operator commands — all real

Run from the repository root unless stated. `just -f v12/justfile <recipe>`.

1. `just -f v12/justfile setup` — prepare the pinned interpreter.
2. `just -f v12/justfile build` — the one-folder runtime; it lands at
   `v12/python/build/out/distro`. Host-specific by construction.
3. `<distro>/baton-v12-stack identity` — record what was built. A commit is
   not a package identity.
4. **Pass one, install:**
   `just -f v12/justfile bootstrap <this dossier>/revision-2/configuration/install-inputs.json /home/sl/baton-instances/native-coordination-pilot-w321608-1 v12/python/build/out/distro`
   (the recipe builds the distro itself if the third operand is omitted).
   It composes the Authority, the record and the stage configuration, copies
   the runtime to the destination and writes the one `instance.json` that
   selects every later lifecycle command. It configures no worker and binds no
   Job — `bootstrap` defers both, because a worker's `deployment` carries a
   digest-sealed input manifest naming the Authority and the Work.
5. **Read back:** the identity at `…/authority-identity.json`, the emitted
   `…/deployment.json`, `Authority.stored_identity` (kind and UUID), and
   `policy_generation()`. Set the canonical target and read it back; it must
   equal `14e52d80679de5e844f72324df632da5e01cf393`.
6. **Register the two routes `bootstrap` does not** (§4) and create the pilot
   Work on `impl`; bind its dossier with a **flat** W39435 locator —
   `native-pilot-quickstart-<8 hex>`; a path and a 12-character suffix are both
   refused by name.
7. **Grant the receipts per Work** in that Work's own scope: `verify` to
   `baton.verifier-pilot`, `review` to `baton.reviewer-receipt-pilot`,
   `approve`/`integrate`/`close` to `baton.slaw` — and never `verify` or
   `review` to the owner. Read each one back with `holds_capability`.
8. **Compose the input manifest** for the created Work (§5) and stage the task
   document.
9. **Pass two, configure:**
   `just -f v12/justfile bootstrap <this dossier>/revision-2/configuration/job-inputs.json /home/sl/baton-instances/native-coordination-pilot-w321608-1`
   with the readback values filled in. Repeating it preserves what is there;
   a changed Job binding is refused rather than moved.
10. `python3 -m tools.pool add --deployment <the emitted deployment.json>
    --worker implementation-pilot` (and `review-pilot`) if the pool is managed
    separately from the emitted configuration.
11. **Submit** `configuration/submission.json` and serve with
    `just -f v12/justfile start /home/sl/baton-instances/native-coordination-pilot-w321608-1`;
    watch with `status` / `monitor`; read one attempt's retained output with
    the installed `logs` subcommand.
12. **Judge and dispose** exactly as the accepted W321690 packet §9 says:
    independent `Session.verify` then `Session.review` (the approval stays
    absent), then the owner's `disposition pending` → `approve` →
    `integrated` → `close --outcome satisfying`, then read it back.
13. `just -f v12/justfile test-bootstrap <a disk-backed root outside the
    checkout>` is the deployment setup's own check suite, available at any
    point.

## 4. Owner and diagnosis ownership — registered and proved

`bootstrap._compose` adds the worker stage routes only (`tools/bootstrap.py`
730-732), and the owner grants at 768-772 register no route handler. Revision 1
declared the routes and left that gap; `prepare.py` scenario 2 closes it with
16 checks:

* **the gap, measured first** — before registration, `baton.slaw` claiming its
  own Work is refused: the route resolves to nobody;
* `add_route_handler` for `impl` → `baton.claude-pilot`, `rview` →
  `baton.reviewer-pilot`, `owner` → `baton.slaw`, `diagnosis` →
  `baton.diagnostician-pilot`;
* the real readback: the implementation participant claims on `impl`, hands
  off to `rview`, the reviewer claims, hands off to `owner`, and **`baton.slaw`
  claims the Work its review ending handed on**, with the decision naming
  `principal:baton.slaw`;
* a participant that does not handle the route is refused;
* a dedicated diagnostic Work on `diagnosis` is created and claimed by
  `baton.diagnostician-pilot`, and an identical claim replays;
* the five grants are made and read back, and the owner is proved to hold
  **neither** `verify` nor `review`;
* the canonical dossier binds, which the human integration citation requires.

## 5. The input manifest, and the composer that does not compose it

`dogfood_operator.input_manifest` hardcodes
`consumption: {"baton.directory/1": …}` — the *staged* delivery shape — and the
stage deployment refuses it: *"this source descriptor does not declare
'baton.source-boundary/1'; a descriptor with no boundary declaration is a
staged source whose content this manager measured, and a nominated mount would
deliver material its manifest does not describe."* My first cut used that
composer and the manager said exactly that.

There is **no composer in the tree for the nominated-mount shape**. So the
manifest is **adapted** from the prior validated instance's own manifest — its
source descriptor, outputs and policy identities — with the Work reference, the
human contract and the manifest id replaced, re-sealed through the same
canonical digest the manager recomputes, and then held to
`check_manifest_structure` (the manager's own validator) rather than to this
driver's opinion. Scenario 3 proves the boundary declaration, the Work binding,
the task bytes and that the digest moved because the Work did.

## 6. Supervision and cleanup — concrete, and honest about the gap

Per-invocation ceilings carried by the Job: `provider_turn_seconds` 3600,
`verification_command_seconds` 900. There is **no product total and no cleanup
reserve** to configure; `execution_limits` says each value is a per-invocation
ceiling and that none of them is a cumulative allowance. The operator-side
envelope, quantified:

| Window | Value | Basis |
| --- | --- | --- |
| implementation turn + its verification | ≤ 4500 s | the two ceilings |
| review turn + its verification | ≤ 4500 s | the two ceilings |
| one attempt pair, worst case | ≤ 9000 s (2 h 30 m) | sum of the above |
| per-runtime stop | 30 s | `oci.stop_vector(seconds=30)` default |
| cleanup settle, two runtimes | ≤ 120 s observed window | two stops plus the positive-absence observation each needs |
| **operator window to reserve** | **≈ 2 h 45 m** per attempt pair | the above; advisory arithmetic, **not** a configured limit |

Supervision procedure: `status` for process health, snapshot freshness, the
observed Jobs and the runtime boundary; `monitor` to watch it; `stop
DESTINATION` to stop **only the processes this stack owns** — it is non-zero
when an owned process cannot be resolved, because *stopping a supervisor is not
evidence that what it started has finished*. Positively account for every
runtime by identity before concluding cessation: the cleanup settles on the
engine's own absence sentence naming the exact runtime, and an unknown runtime
keeps its hold. `record recovery-check` **reports and refuses — it never
admits**, and a clean report is the precondition for an operator's admission,
not the admission. Admit one writable instance.

## 7. What remains, and the launch gate

* **The engine-side facts** this preparation may not read: whether the reused
  `image_digest` is present on the host, and its re-validation
  (`python3 -m tools.worker_image --tag …`).
* **The seven placeholder policy identities** named in §2.
* **The owner's launch selection.** Binding a provider-backed configuration is
  not permission to run it: this packet describes an executable selection and
  calls nothing. The useful outcome it can produce is the one in §8 — a
  reviewed `v12/QUICKSTART.md` authored by the implementation worker, judged
  by an independent reviewer, approved by the human owner.
* The structural task check establishes four headings, a length floor and the
  absence of markers; **it is not a usefulness judgment**, and the fixture
  filler prose the driver used to exercise it is not a quickstart. Substantive
  review of the authored document is the reviewer's, at review time.

## 8. The task (unchanged from revision 1, still fully pinned)

`configuration/task.json`, schema `baton.dogfood-task/2`, task id
`w321608-native-operator-quickstart`, declared base `14e52d80…`, source
profile `git-line`; sealed canonical digest
`5ec48d4baf2020a8ef972237444c5989cf8490dea23cc285dbfd3bc0508dc1bb`. The
verification argv is closed and was run against five candidates in revision 1's
verification (accepts a complete document; refuses a missing section, a short
one, a marker, and an absent file). `test_scope` is `["v12/QUICKSTART.md"]`;
`terminal_policy` is `report-and-hold`; the submission schema is
`baton.v12.job-submission/2`, which is the only one carrying
`execution_limits`.

## 9. Boundaries of this revision

No install into the selected destination (it still does not exist), no engine
call, no provider call, no credential content read, no image build, no
submission to a manager, no `start`, no product source change, no raw SQL, and
nothing that mutates this repository's history, index or working tree. The
disposable root is labelled `w325959-preflight`, every identity it generated is
labelled PREFLIGHT, and `prepare.py` refuses to run against the selected
destination or against a root that does not carry that label.
