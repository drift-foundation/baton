# W384944 — first B4 checkpoint, 2026-10-31

Author: baton.codxpc, role impl; claim E384947, episode 384944. This is a
read-only prerequisite/inventory checkpoint, not test or B4 acceptance.
M384943/M384945 select this checkpoint; M384946 confirms creation; M384948
confirms K's current ownership. Parent W384870 remains held by baton.slaw.
No product/test edits, builds, container starts, provider calls, full-suite runs,
Git mutations or removal of existing resources were performed.

## Evidence and exact case inventory

All paths below are relative to this evidence directory. `baseline-cases.tsv`
enumerates exact B0 collected test ids and outcomes for all 17 current engine
modules, the four pure modules named in the original C4/C6 map, and integration
`test_driver` (subsequently reclassified to B4 in parent PROGRESS). It is a
historical inventory, NOT fresh collection or proof that current code passes.
`inventory-summary.json` summarizes the first 21 modules; `test_driver` is an
additional TSV section. `class-absent` marks historical Podman classes absent
from current source, not permission to drop other cases. The 98 removed Podman
ids have owner authority M384888 and parent evidence/PODMAN-REMOVAL-2026-10-30.md.

Sources: parent evidence/b0-2026-10-29/test-all.reconciled.summary.json and
its retained test-all.log; latest engine evidence is
parent evidence/b1-2026-10-30-manager-engine-group.log. The latter accounts for
236 collected/executed, 198 passed, 27 failed, 7 errors, 4 required skips,
zero fixture errors/skips or unaccounted ids. `engine-outstanding-ids.tsv`
enumerates all 38 outstanding ids; its set matches B0 after Podman removal,
as recorded in parent PROGRESS. `latest-engine-report-blocks.txt` preserves
36 failure/error report blocks (subtests explain 36 blocks versus 34 ids),
and `latest-engine-symptoms.txt` makes their final exceptions easy to find.
`baseline-report-blocks.txt` and `baseline-symptoms.txt` preserve relevant B0
blocks including the pure and integration cases. Input SHA256 values are in
`read-inputs.sha256.json`; these are read-time provenance, not a stable tested
candidate. No tests were imported or collected to produce this inventory.

Current registry assigns these 17 modules to manager-engine (all required):

- tests.manager.test_worker_container
- tests.manager.test_failed_start_destroy_engine
- tests.manager.test_oci_engine
- tests.manager.test_lifecycle_composition
- tests.manager.test_negative_race_endings
- tests.manager.test_ended_runtime_adoption
- tests.manager.test_output_custody_engine
- tests.manager.test_credentials_engine
- tests.manager.test_refused_session_engine
- tests.manager.test_custody_engine
- tests.manager.test_input_delivery
- tests.manager.test_worker_entry_engine
- tests.manager.test_dogfood_image
- tests.manager.test_abandoned_attempt_engine
- tests.manager.test_private_line_access_engine
- tests.tools.test_dogfood_arc_engine
- tests.tools.test_dogfood_retry_engine

Additional B4 inventory: manager-pure `tests.manager.test_integration_worker`,
`test_worker_image`, `test_integration_image`, `test_oci_integration`; integration
`tests.integration.test_driver`. The OCI import-order failure is already covered
by accepted B1 C1 correction; do not reopen it as an engine prerequisite.
`test_worker_image`'s bootstrap-generation and `test_integration_image`'s recipe
inventory failures are pure contract/fixture questions despite their original
C6 label. Revalidate those against K's accepted work before any repair.
Packaged C8 was accepted with B1 (24/24); tools-packaged is a prerequisite-status
check here, not another run. Supervised remains a separate later parent gate.

All four required initial-access cases are in class
`tests.manager.test_private_line_access_engine.InitialPrivateLineEngine`:

1. `test_initial_populated_line_is_writable_by_the_fixed_runtime`
2. `test_the_composed_ending_consumes_reviews_and_corrects_one_line`
3. `test_a_reviewer_runtime_cannot_write_the_checkpoint_it_reads`
4. `test_a_correction_runtime_advances_the_same_line`

All four were required skips; none is optional. Preserve writer access,
reviewer EROFS/read-only source, same-line correction and retained checkpoint
history. Test names still describe the historical fixed identity; they do not
supersede the shared-identity ruling.

## Findings from retained evidence and source reads

| Area | Confirmed observation | Required next investigation |
| --- | --- | --- |
| C4 integration worker | B0 has 60 errors at the per-attempt delivery ancestor (0775 versus required 0700), plus two failures. Current test_integration_worker.py:434–438 constructs IntegrationDelivery and manually creates assignment/result roots; place() creates parents with ambient umask. | Repair fixture setup through the actual delivery owner or exact fixture modes, preserving the product's refusal of an existing altered ancestor. Do not change the host umask or chmod existing operational storage to conceal it. |
| Input delivery | Latest engine evidence: 19 failures and 3 errors. Four race cases pass a connection across threads; three cleanup cases lack configured workspace storage; the remaining failures compare shared identity against 65532. | Give each racing caller its own valid store capability and configured storage. Preserve refusal for invalid connections, race safety and isolation. Trace identity-sensitive assertions individually. |
| Shared runtime identity | oci.py:1440–1463 and 1509–1519 deliberately compose execution identity from workspaces.identity_for. Initial-access launched() still asserts 65532 at line 156; input_delivery has corresponding fixed-pair assertions. | Align tests with the accepted trusted shared identity while preserving actual mount/access evidence. Do not simply swap every numeric assertion; consent, raw fixed-user negative tests and image defaults have different contracts. |
| Custody | Four errored ids include PermissionError for nested/outer, followed by unresolved removal holds. Raw fixture docker runs explicitly select 65532. | Trace fixture-created foreign-owner material versus the supported identity; preserve actionable permission failures and genuine hold/recovery coverage. No blanket recursive repair. |
| Endings | Five failed ids across lifecycle_composition (one), negative_race_endings (two), ended_runtime_adoption (two) expect complete but observe retained. | Compare exact retained-ending contract with accepted K changes; retain cessation, evidence and cleanup assertions. A textual expected-value replacement is insufficient. |
| Worker entry | One failed id asserts worker UID differs from manager UID. | Preserve real container boundary proof using execution/mount evidence under the shared-identity contract. |
| Broad cleanup checks | Two failed ids inspect namespace-wide leftovers. Read-only current inventory finds one old lifecycle-sibling container and 44 baton-runtime.start containers, all exited; zero initial-access-labelled containers. | Use unique run provenance for new resources and prove their cleanup; never delete or silently adopt historical containers. If old-resource removal is selected, it is a separately identified operator action after provenance inspection. |
| Integration driver | Parent PROGRESS reclassifies its retained-root expectation to C4/B4: three failed ids, four report events. | Trace retained-history semantics against the selected ending; do not erase retained output to make absence true. |

Identity authority: v12/DESIGN.md HOST-5 and
work/records/2026/09/finding-v12-workspace-shared-identity/OWNER-TRUSTED-IDENTITY-20260917.md.
No specification change is proposed. Current source gaps above are observations
or bounded hypotheses; no new failing run is claimed.

## Read-only prerequisite results

`environment.json`, `images.json`, `resource-overlap.json` retain argv, return
codes, safe output and measured durations. First image template inspection
failed because Config.Volumes is absent; corrected optional-key inspection
succeeded, and both records are retained. This was a query error, not an image
failure. Queries were bounded at 30 seconds; no test duration is claimed.

- Prepared environment ready: /home/sl/.local/state/baton-v12-venv/bin/python,
  Python 3.13.7, jsonschema 4.26.0. No install needed.
- Docker server 29.1.3 reachable as sl, uid/gid 1000:1000; this actual process
  holds supplementary gid 1001, baton-workspace. No group creation, sudo,
  chmod of existing roots or runner restart is needed on this host.
- /var/tmp and work/scratch are writable/searchable ext4, about 622 GB free at
  observation. /tmp is not selected. Existing distro directory is present;
  presence alone does not certify freshness against current Stage C changes.
- All inspected BATON test-selection variables are unset, including the three
  initial-access variables, disk root and supervised image. This explains why
  an unconfigured initial-access run would skip; it is not a missing daemon.
- Installed initial-access candidate:
  `sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4`,
  tag baton-w71917-provider-gate:20260905, linux/amd64, Config.User 65532:65532,
  no declared volumes. Historical owner selection is in private-line-runtime-
  access/FINDING.md, “Owner selects Git-capable candidate — 2026-09-07”; that
  dossier retains actual Git/initial-access evidence. This is an explicit
  reuse proposal for B4, not automatic selection of an arbitrary local image.
  Image default user does not override the adapter's execution --user.
- Installed supervised reference candidate:
  `sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8`,
  baton-w32577-reference:20260913, linux/amd64, default 65532:65532, no volumes.
  B0 retained its supervised use. No supervised execution selected here.
- Image metadata and historical provenance do not prove compatibility with
  current source. No current build or runtime capability claim is made.

## Exact operator setup proposed for the allocated next slice

Coordinator first selects reuse of the exact initial-access image above and
allocates a stable candidate plus the resource namespace. No image build is
needed for this proposed initial-access batch: the historical selected image
is installed. Other engine modules build their own reference/dogfood images;
those builds remain part of a separately released engine batch, not these steps.
No host privilege repair is presently missing. Do not run setup or groupadd again.

From the repository root, after that allocation, these independently pasteable
commands establish only the selected environment (they have NOT been executed):

```sh
export BATON_V12_INITIAL_ACCESS_ENGINE=1
export BATON_V12_PRIVATE_LINE_IMAGE=sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4
export BATON_V12_WORKSPACE_GROUP=1001
export BATON_TEST_ENGINE=docker
mkdir -m 2770 /var/tmp/baton-w384944-b4-20261031-a
chgrp 1001 /var/tmp/baton-w384944-b4-20261031-a
export BATON_V12_DISK_ROOT=/var/tmp/baton-w384944-b4-20261031-a
export TMPDIR=/var/tmp/baton-w384944-b4-20261031-a
```

mkdir must succeed as a NEW root; if it exists, stop and allocate another suffix,
never reuse/chmod/chown it blindly. gid 1001 is verified on this host only; a
new host must explicitly resolve/provision its dedicated group and approve its
image. The proposed exports do not start anything. A future prepared runner
lacking gid 1001 can use an operator-created group-aware shell (`sg
baton-workspace`) after checking membership; this current process needs none.

After fixture correction, stable-source selection and engine release, the exact
focused four-case command from v12/ is:

```sh
just test-one tests.manager.test_private_line_access_engine.InitialPrivateLineEngine
```

This invokes exactly the class's four methods via the prepared interpreter.
It starts real Docker containers with scripted payloads, not live providers.
It is a future verification command, not authorized execution at this checkpoint.
For the later parent's supervised gate only, select the retained exact reference
image with:

```sh
export BATON_W32577_IMAGE_DIGEST=sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8
```

That export does not select a supervised or full run. No full-run command is
included because B5/final acceptance stays with the parent coordinator.

## Proposed ownership, first repair batch and runtime allocation

First repair batch proposed: the C4 integration-worker delivery fixture only,
followed by its focused module, before initial-access/engine repairs. Proposed
codxpc edit ownership is v12/python/tests/manager/test_integration_worker.py plus
this child record/evidence. Existing source points to fixture construction; if
investigation instead requires product changes, report the actual overlapping
path and coordinate ownership, rather than weaken the product mode check.
Suggested command from v12/: `just test-one tests.manager.test_integration_worker`.
Acceptance preserves existing refusal tests and proves positive cases reach their
intended stage; 83 is the historical collected count, not a guaranteed current
count. Suggested per-run ceiling: 300 seconds plus 30 seconds process cleanup;
measured duration and actual ids/outcomes must be retained.

Next proposed fixture allocation, after that bounded result: test_input_delivery.py,
test_private_line_access_engine.py, test_custody_engine.py,
test_worker_entry_engine.py, test_lifecycle_composition.py,
test_negative_race_endings.py, test_ended_runtime_adoption.py,
test_credentials_engine.py, and tests/integration/test_driver.py. These are
proposed ownership, not permission to edit them now or an exclusive permanent
files-to-edit restriction. Shared input_roots.py, disk_roots.py,
test_review_cycles.py, worker image recipes and runner/registry/docs stay read-only
unless coordinator allocates a concrete required change. Pure image/bootstrap
cases need revalidation against current accepted K work before expansion.

M384948 reserves K's test_boundary_inventory.py and product attempt_logs.py,
attempts.py, custody.py, exchange.py, intake.py, oci.py, workspaces.py, tokens.py,
store.py and stopped_settlement.py. B4 fixtures depend on those bytes. No engine
test against moving K source: coordinator supplies an accepted stable snapshot
or a source-stable window. A snapshot must include v12 and declared consumed
inputs, use the prepared interpreter and preserve source digests before/after;
no Git operations are needed to construct it. Refuse source drift, including
shared helpers, instead of attributing a run to one candidate after bytes move.
K owns parent PROGRESS; coordinator owns parent FINDING/PLAN/checklist.

Resources proposed: external root /var/tmp/baton-w384944-b4-20261031-a for
engine fixtures requiring an out-of-checkout root; work/scratch/w384944-b4-*
for disposable stable snapshots; this child's evidence/<unique-run>/ for durable
logs, per-id ledger and source manifests. Initial-access already uses UUID nonce
labels baton.initial-access and exact container IDs for cleanup. Other fixtures
use UUID-suffixed tags/names but some final sweeps are broad: allocate a run-specific
namespace or exact owned-ID set before execution and preserve genuine leak checks.
Serialize every engine module and all image builds; share Docker build cache only
as a cache, never as provenance. Do not prune images/caches or remove preexisting
containers. Capture before/after identities and cleanup results for newly owned
objects only. Keep the two preloaded image IDs unchanged.

Suggested initial-access ceiling: 600 seconds with 120 seconds reserved for
exact-container termination/cleanup; other selected engine-module ceilings 900
seconds plus 120 seconds cleanup, revised for the known build before release.
A timeout never proves container cessation: retain unknown state and exact IDs.
These are planning estimates, not measured costs or cumulative approval gates.
The existing fixture commands have internal timeouts up to 300 seconds; outer
supervision must preserve cleanup and cannot merely kill the host and declare done.
Later focused group verification declares manager-pure, manager-engine and
integration only as affected; tools-packaged/supervised remain parent checkpoints.
Use test-one during correction, then selected test-group with actual-started
accounting. Retain log, collected/executed outcome ledger, source identity before
and after, image IDs, environment and measured durations together. Required skips,
fixture errors and unaccounted ids fail acceptance. Never infer current passes
from this preflight inventory.

## Handoff condition

Return to baton.decide for coordinator review of the inventory, exact image
reuse and path/resource allocation. B4 remains open. No additional action is
needed from Slawomir merely to install a group or interpreter on this host.
The next release should name the stable source and first fixture batch; preserve
all four initial-access cases and the parent's Stage C/B5/final acceptance and
owner Git checkpoint gates. No implementation approval is being inferred from
this completed planning checkpoint.
