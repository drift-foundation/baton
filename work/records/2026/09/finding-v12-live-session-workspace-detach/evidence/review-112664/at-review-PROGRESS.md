# Progress

No proof execution yet. Assigned author appends exact checkpoints, results and
limitations; no successful runtime or performance result is claimed at creation.

## 2026-09-07 — baton.tuner, claim event 106686

Completed the authorized proof preparation: added the read-only preflight
script/evidence, deterministic unprivileged resident and concrete controller
authority request. Revalidated the superseding development-workspace modes and
mandatory detach/shutdown gates before preparing the mechanism.

Command:
`python3 work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/preflight.py > work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/preflight.json`
— exit 0. The generated JSON records capability, namespace, tooling and Docker
facts without environment/credential dumps. No experiment container exists.

Validation clarification: the script's three Docker subprocess observations
each failed with socket permission denied, which the script preserved despite
its overall exit 0. Initial artifact validation failed because it assumed those
observations succeeded. Standalone direct `docker version`, `docker info` and
the exact experiment-label `docker ps --all` were independently permitted and
returned exit 0; their results are in `evidence/direct-docker-preflight.json`.
The operator request explicitly includes controller Docker execution authority.

Outcome: blocked before OS execution on the required trusted host-controller
authority. AUTHORITY.md is the reviewable next action; no privileged command or
interactive escalation was attempted. The resident is preparation only. No
mount, detach, busy-refusal, restart, real-session or performance proof has run.
No production code, configuration, recipe, existing test or Git state changed.

Final preparation validation: both Python scripts parse with `ast.parse`; both
JSON evidence accounts agree with their respective observed execution boundary;
all eight dossier/script/evidence files pass trailing-whitespace checks.
`git diff --check` also passed. These checks validate prepared artifacts only,
not execution of the resident, privileged controller, OS gate or real session.

## 2026-09-07 — baton.tuner, claim event 106813

Implemented only the owner-authorized dossier-local runner preparation from
M106756: evidence/host_runner.py, resident security-posture probe, RUNNER.md,
runner input observations and script digests. No privileged execution, install,
Docker creation, image acquisition, provider call or production/test/Git edit.

The runner has fixed image/user/group/mount targets, private disposable state,
identity checks before namespace operations/teardown, ordinary-unmount-only
revocation, denied gates during uncertain detach/reattach, actual helper death
injections, gate reload, busy shutdown fallback and one stop/start comparison.
It deliberately retains containers/files and reports uncertain cleanup. A
failed create/start before full registration remains for exact operator action.

Local command: python3 .../evidence/host_runner.py --self-test — six tests pass.
ast.parse accepts both scripts; libc symbol inspection found all five required
wrappers without invoking them. Exact installed image inspection succeeded;
generic image listing was denied and not escalated. No OS/session/timing proof
has run. RUNNER.md and evidence/runner-digests.json are the concrete handoff to
independent review, followed by owner execution disposition.

## 2026-09-07 — baton.tuner, claim event 107264

Prepared the next concrete prerequisite package after accepted deterministic
evidence and completed W106896 guard handoff: REAL-SESSION-PREPARATION.md,
evidence/real_session_preflight.py, evidence/real_session_contract.py and
non-secret input observations. All edits are in this dossier. The full live
runner remains pending exact-image transport evidence and credential-delivery
clarification; no guessed implementation of credential access was added.

Local validation: four preflight framing/correlation/cleanup-identity cases pass;
four task-verifier/process-session/equivalence/timing cases pass. Logs are
evidence/real-session-preflight-local-tests.txt and
evidence/real-session-contract-local-tests.txt. Both scripts parse. A subsequent
wire-only clarification adds initialize hooks=null to match the inspected SDK;
it does not change the tested parser/identity paths. No redundant suite rerun.

Read-only exact image inspection and model/credential metadata checks succeeded.
The nominated source was never opened for bearer content. Default bridge
network inspection was denied and not escalated. M107310 requests a ruling on
existing volatile materialization versus no-copy wording. The nominal USD3 cap
is reported as unverified. No container, namespace/mount operation, credential
delivery, networked CLI or real model turn was run.

Current state: prerequisite candidate awaiting baton.bug review then baton.ops
disposition. evidence/real-session-preparation-manifest.json binds its exact
artifacts and unchanged deterministic scripts. The accepted deterministic result
stands; real-Claude continuation/restore and the full frozen execution package
remain open. No production/config/recipe/existing-test/Git mutation.

## 2026-09-07 — baton.tuner, claim event 107407

Completed M107404's bounded offline diagnostic correction as a separate candidate:
evidence/real_session_preflight_diagnostic.py. Added
evidence/test_real_session_diagnostics.py and OFFLINE-DIAGNOSTIC-CHECKPOINT.md.
Original probe, six manifest-bound preparation artifacts, accepted deterministic
scripts and operator-retained evidence remain unchanged.

Revalidated readable retained probe/result/registration. Fixed inner stage/reason/
natural-exit/errno projection and host preservation of a structured failure even
when Docker start exits nonzero. Cleanup errors cannot replace the primary inside
diagnostic. Raw exceptions, provider output and stderr remain excluded.
The previous run's root cause is unknown; no blind runtime rerun occurred.

Validation: 11 additive fault-path tests pass in 0.003s; all four original local
tests pass in 0.000s. Both candidate/test files parse, AST preservation checks
pass, and exact old hashes match. Results, input audit, patch and candidate hashes
are retained in evidence/real-session-diagnostic-*.

Current state: diagnostic candidate awaiting baton.bug independent review then
baton.ops disposition of its exact operator command. Full live session work
remains open; this correction changes no production/config/image/credentials/
existing assertions/Git state and claims no transport or model proof.

## 2026-09-07 — baton.tuner, claim event 107495

Revalidated M107492 against retained diagnostic result/registration/probe. Version
and help execution passed; all-help-visible failed before initialization. Missing
names were discarded, so this evidence cannot identify them. No name was guessed.

Prepared separate real_session_preflight_help.py, test_real_session_help.py and
OFFLINE-HELP-CHECKPOINT.md in this dossier. Fixed per-flag observations survive
failed/successful results; explicit pending flags prevent idle initialization
from being presented as full live capability. Proposed only the documented
all-help-visible gate change; actual initializer/runtime checks are unchanged.

Six new mocked tests pass in 0.003s, four original tests pass in 0.000s.
Prior artifacts and selected guard/argv ASTs match. Patch, input audit and
verification are bound by evidence/real-session-help-manifest.json.
Awaiting independent review then baton.ops disposition before execution. No
runtime, credential, production, image, existing-test or Git mutation.

## 2026-09-07 — baton.tuner, claim event 107665

Completed the owner-routed full bounded live preparation after independent
offline transport acceptance in review-2026-09-07T05-07-12Z.md. Revalidated and
pinned the implementation boundary in FINDING.md before adding dossier-only
live_supervisor.py, live_controller.py, test_live_package.py and LIVE-PACKAGE.md.

The candidate composes the accepted streaming handshake and ordinary namespace
helper with actual CLI/process-tree/session pins, exact revocation/shutdown
receipts, safe artifact verification, existing automatic private credentials,
private source snapshots and session restoration. It schedules one four-turn
pair, 180s per turn, 720s work plus 180s ending within a 900s runtime deadline.
Exports are limited to controller-owned evidence with original-byte hashes.

Validation: 19 offline tests pass in 0.137s (recorded final run in
evidence/live-package-tests.txt); three new Python files parse; 23 prior bound
artifacts match. The standalone --audit passes all 80 frozen input hashes.
An actual existing-API test exposed the fixture store's required millisecond-Z
timestamp grammar; the candidate now uses that grammar. No live API/model/
credential/privileged execution occurred. Existing tests and production paths
were not edited; no Git state was mutated.

Frozen manifest: evidence/live-package-manifest.json, SHA256
eea4e949548c2301e4c45f815a60380b8edda1adbbc4c4f75dd6420ac496402b.
Controller SHA256 f9500d4a3537a7b10201f6399cb901c899cd728ad397d1d9258a16632abd555d;
supervisor SHA256 6a9d4fb65bd95757b9d0b4133ccc7f9a2945c9e9ba612ae7c0403c51507767db.
Awaiting baton.bug independent package review, then baton.ops separate owner
execution approval. Six live options, actual model/session/restore behavior,
runtime-resolved bridge ID and hard billing cap remain explicitly unverified.

## 2026-09-07 — baton.tuner, claim event 107956

Read the failed-run export and newest owner/reviewer handoffs. All three exported
projection hashes match PROVENANCE.json. Reproduced the exact reviewed snapshot
in an ordinary-user clean-environment import: FileNotFoundError/ENOENT for the
fixed worker-control JSON schema. The snapshot omitted package data required by
frozen.py. This is a confirmed source defect and inferred historical cause;
the original flattened exception and protected-root resource state were not read.

Pinned that finding and bounded correction before implementation. Preserved the
failed package; added separate live_controller_setup.py, test_live_setup.py and
LIVE-SETUP-CORRECTION.md. The candidate includes two hash-bound schema assets,
closed setup diagnostics, durable allocation intent and partial-constructor
ownership/accounting. It adds no cleanup deletion or credential authority.

Validation: 28 checks pass in 0.347s, including fresh system-Python snapshot
imports, actual prepare failure at fixture-store open, constructor/close failure
accounting and safe exports. All 19 prior assertions run unchanged against the
candidate. All 80 original inputs remain byte-identical; key runtime/gate/pair/
credential-method ASTs are preserved. The 90-file standalone --audit passes.
No real credential read, Docker/network/provider operation, privileged execution,
production/config/recipe/existing-test edit or Git mutation occurred.

Frozen evidence/live-setup-manifest.json SHA256
c0ec6a1d820894f9a6064b6289824f20fdf296e6e2ea7599df9f22108cbb1b30;
candidate controller SHA256
ade171ca071c78ce992aab76462b6fa7e906be90dfedbd22cba019ceff54e485.
Awaiting baton.bug independent correction review, then baton.ops disposition of
any separate operator execution. The consumed original live approval is not
carried forward as replacement execution authority.

## 2026-09-07 — baton.tuner, claim event 110238

Revalidated owner reroute 110236, current dossier decisions and independent
partial-live review-2026-09-07T06-25-36Z.md. Preserved accepted retained-session
correction evidence; restored-first cause remains unknown. Pinned the bounded
diagnostic implementation boundary before adding separate controller/supervisor
sources, focused tests and LIVE-DIAGNOSTICS.md.

Prepared closed arm/operation/stage/refusal reporting and distinct host/provider
write/result observations before post-turn checks. Unknown text/fields refuse
or map to fixed labels; ordered diagnostic frames and independent supervisor/
host timestamps preserve chronology. Runtime summaries retain actual partial
milestones without stale preparation-only or blanket historical-denial claims.
The public live entry is disabled; future continuation/pair scope is not chosen.

Validation: 16 offline fault/redaction checks pass. All 90 earlier candidate
inputs and nine accepted exported-data hashes match. AST checks preserve core
credential/setup/pair/verifier helpers, gated method bodies and supervisor
argv/framing/result checks. A full diagnostic-frame test caught and resolved a
timestamp-field collision before freezing. No live/provider/real-credential
operation, production/config/existing-test edit, cleanup expansion or Git
mutation occurred.

Frozen 108-file manifest evidence/live-diagnostic-manifest.json SHA256
2ef942b1f58f95ff3ff59d4815e01688ee45d3dd8b10713331c6e0844335b5b3;
controller SHA256 bfe220010a6a07e72dd80c0745c8213ebf9fa581fbb5422b008fce7561ee35e3;
supervisor SHA256 e2f909cd74008ba155be39aa93bca4757cf5e600296f4ec9ff938ee0b097d621.
Awaiting baton.bug independent diagnostic review, then baton.ops separate
execution-scope disposition. The accepted retained observation remains separate
from the unproved restoration comparison and any production adoption decision.

## 2026-09-07 — baton.tuner, claim event 110487

Revalidated owner M110484 and independent diagnostic sign-off
review-2026-09-07T13-08-30Z.md, then pinned the restored-only implementation
boundary before editing. Added separate runnable controller/supervisor sources,
RESTORED-ONLY.md, five restoration tests and exclusive claim-specific evidence.
All previous bound candidate and accepted export bytes remain unchanged.

The new path creates a fresh initial session/workspace, confirms shutdown and
verifies initial bytes before constructing its one replacement. It restores the
same actual session/workspace in a different process and requires the unchanged
remembered-token correction through ordinary revocation. Both host/supervisor
limit each container to one user turn. A durable initial verified checkpoint
survives later failure. Success reports standalone restoration timings, without
executing the retained arm or claiming a matched comparison.

Validation: 21 offline checks pass, including 16 unchanged diagnostic assertions
against the new candidate and real fixture-gate/fixed-byte verification with
simulated processes. All 116 hashes pass the standalone audit, including all
108 prior inputs and nine accepted exports. Input/AST audit, review patch and
raw test output are bound in the new manifest. No live/provider/real-credential
operation, production/config/existing-test edit, cleanup expansion or Git mutation
occurred. The disclosed older unbound reviewer-test-output loss remains historical.

Frozen evidence/restore-only-manifest.json SHA256
a3f5f845c344ee9418327123cbc32de37be35701dfee5b0ba342a19005681c5a;
controller SHA256 f3fa2435ab3a90643fa2fdf4e9cd58d9ca5bc6f114c0ad032fa8dcca0310ed51;
supervisor SHA256 3322a0494f8dd51be1f8188e626e522ad676dfee4c380d6c939b9827e4f3082f.
Awaiting baton.bug independent runnable candidate review, then baton.ops separate
exact execution approval. The proposal is limited to two containers/two turns,
180s per turn and 420s work plus 180s ending within 600s runtime. Owner scope
selection authorizes preparation only; no operator invocation was executed.

## 2026-09-07 — baton.tuner, claim event 110596

Responded to review-2026-09-07T13-42-14Z.md. Reproduced the real fresh-constructor
arm-name overwrite with the reviewer probe and pinned the correction boundary
before implementation. Prepared a separate controller changing only the private
subdirectory loop variable and new manifest basename; reused the unchanged
restored supervisor. No earlier frozen input or assertion was edited.

Added actual fresh/replacement constructor checks for exact arm labels, private
directories/modes, shared session/workspace, preserved private content and
unsupported-arm refusal. Only chown is mocked for successful construction;
external/credential operations are forbidden and receive no calls. The new
regression fails against the old source with the expected diagnostic-arm-invalid
error. All 23 candidate checks pass, including the prior 21 assertions unchanged.
Baseline and passing logs, narrow source patch and preservation audit use exclusive
claim-110596 paths. All 125 manifest hashes pass; all 116 preceding bound inputs
and nine accepted exported-data hashes remain unchanged.

Frozen evidence/restore-constructor-manifest.json SHA256
b6058f4774775c63113f0f9721e264dd317a4f57692b2ebfdf3264511c032c4b;
controller SHA256 fd551c9684b2caa4577482bd5305b5f2a8e5ed22032d821b801f1ca33305f247;
unchanged supervisor SHA256 3322a0494f8dd51be1f8188e626e522ad676dfee4c380d6c939b9827e4f3082f.
RESTORED-CONSTRUCTOR-CORRECTION.md names the exact proposed invocation. Awaiting
baton.bug independent correction review, then baton.ops separate exact owner
execution approval. Existing two-container/two-turn/600s limits, credential
delivery, custody, diagnostics and teardown are unchanged. No live/provider/
real-credential operation, production/config/existing-test edit or Git mutation
occurred. Accepted retained proof and the unknown historical failure cause remain
separate; the older unbound reviewer-log loss is not claimed recovered.

## 2026-09-07 — baton.tuner, claim event111078

Revalidated owner reroute111076 and review-2026-09-07T14-50-28Z.md; pinned the
authorized diagnostic boundary in FINDING/PLAN before edits. Added separate
result diagnostic controller/supervisor, offline tests, recorded closed transport
label contract, RESULT-DIAGNOSTICS.md and a fresh manifest/invocation. Historical
candidate/export bytes and existing assertions remain unchanged.

The supervisor records subtype and is_error independently before result
validation; the host validates exact closed shapes and arm/operation/turn/stage
correlation before logging. Known labels are documented contract labels only;
unknown strings, messages, result/errors text and private data are excluded.
The existing result predicate, session/model/cost/turn checks, restoration,
credential/setup, mount/receipt and ending bodies are unchanged. No historical
provider root cause is inferred from new synthetic diagnostics.

Focused command: python3 -B .../evidence/test_result_diagnostics.py — eight
tests pass in0.008s. Broader command: same path with --broad —32 tests pass
in0.232s, including the prior23 assertions, eight existing stream/result cases
and actual fresh-snapshot imports. Source reader, model and runtime construction
are not invoked by the import check; review_driver is not imported on that path.
The focused log is explicitly transcribed from tool output; the broad log
preserves the full returned command output. Neither suite was redundantly rerun.

audit_result_diagnostics_111078.py verifies167 historical dossier files unchanged
outside the decision/progress records,124 unchanged prior inputs, the one exact
current dependency rebind, contract labels, runtime file-set equality and
unchanged guarded method ASTs/text. Prior manifests remain frozen; current
review_driver.py is rebound from78ddccdf... to62db37ee... without editing it.
This is current dependency revalidation, not historical execution-drift evidence.

Frozen143-input manifest evidence/result-diagnostics-manifest.json SHA256
bb2f29412486a2ed3846e9c7235f1481e5cb62e16b7a6889ca3fbbc8b9d1c0fd;
controller d19221fd610320c8bb2d87ff225eedd609694b9a46133a2402b5c903d21e9251;
supervisor 94c6dd20122131f2a67bcd00c50d55e94ac5b65f14d648f036d8532fcf0cca41.
Awaiting baton.bug independent candidate review, then baton.ops exact execution
disposition. No live/provider/real-credential operation, private-session read,
production/config/existing-test edit or Git mutation occurred. Accepted retained
proof stays separate; restoration and matched comparison remain unproved.

## 2026-09-07 — baton.tuner, claim112609

Revalidated owner111303, independent review111259 and closed satisfying
W110772/W112039/W110934 provider evidence. Pinned the bounded rebind in
FINDING/PLAN before edits. Prepared a separate controller changing only its
manifest filename, an additive test copy changing only controller imports,
DEPENDENCY-REBIND-112609.md and a fresh manifest. Old candidate/evidence bytes
remain unchanged; production sources were only read and hash-bound.

Six changed and one added runtime dependency match accepted candidate maps.
All143 prior inputs remain in the152-input package; the complete71-module
Python file set, two schema assets and source-reader tool remain bound.
The unchanged source snapshot copier includes that closure at execution.

Validation: eight diagnostics checks pass in0.008s;32 broader checks pass
in0.239s, including all prior assertions and fresh imports from the actual new
snapshot without credential/source-reader/runtime construction. Standalone
--audit passes152 inputs. Exact equality verifies only the controller manifest
filename changes, supervisor equality and unchanged existing assertions.
All191 protected historical files match. Unique evidence/rebind-112609/ retains
baseline, dependency provenance, source/test diffs, commands/raw output and audit.

Manifest SHA256 2d829e03d3337c9eabf05d4e0d0ce01097bc185be24b991d0b3012b0ea3a78e5;
controller SHA256 2ce81534d65f8f82d4797e4f4b0ce9afd903aca2df154d567db3fd6eaeeea92d.
Awaiting independent exact-binding review then separate owner execution decision.
No live/provider/credential operation, private-session read, production/config/
existing-test edit or Git mutation. No restoration or matched comparison claim;
accepted retained proof remains separate and historical broad failures unwaived.
