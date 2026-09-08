# Prove live-session workspace detach and reattach

## Latest execution feedback — 2026-09-07 — baton.prompt

The owner ran the reviewed offline probe; it failed with exit1 in approximately
0.193 seconds. Exact container ddb4acf072f034acab95cedd729952d6b5294bd743d2fcedbb1a93fbad526f5f
is stopped/PID0, with OOMKilled=false and empty Docker state error. Retained root
is /tmp/baton-w106673-session-preflight-gu8vuv0e. Observations are captured in
evidence/offline-operator-failure-2026-09-07.json; original artifacts remain intact.

Confirmed diagnostic defect in the experiment: real_session_preflight.py discards
the inner exception reason, command stderr and the outer failure reason. Container
logs contain only offline-transport-preflight-failed. Thus the host stage
offline-initialization does not identify whether identity, executable/version,
flags, process startup or control initialization failed. Actual cause is unknown;
this is not evidence against workspace detach or real model/session continuity.

Next bounded correction: preserve fixed non-secret stage/reason codes and child
exit status through both boundaries, with focused additive diagnostic tests. Do
not expose raw provider output, relax assertions, change images/credentials or
repeat the runtime blindly. Revalidate the exact failure path and return corrected
probe bytes/invocation for review before the next operator run. Earlier source
sign-off remains history, not a successful runtime result.

Ledger Work: W106673. Created 2026-09-07 by baton.prompt for Slawomir.
Discovery: `../finding-v12-private-line-custody-locators/`.

## Approved bounded experiment — 2026-09-07

Slawomir approved proving whether a trusted controller can remove the writer's
workspace mount for review and restore it for correction while preserving the
container, live agent process/session and private development line. Measure
turnaround rather than claiming a speedup from container reuse alone. The current
stop-before-consume production behavior remains unchanged until independent proof
review and explicit adoption. Rename and inode-use observations are not revocation.

## Mandatory handoff gate — approved 2026-09-07

Ordinary unmount must succeed in the writer's actual mount namespace, with no
alternate writable access or worker ability to restore the mount. Only a verified
revocation for the exact current assignment permits stable-result consumption.
Agent declarations alone, host-side unmounts, lazy detach and forced-unmount
workarounds are insufficient. Busy after the worker declares completion and
releases its workspace handles is a protocol violation: record a defect and
require confirmed container shutdown before consumption.

Failed, forgotten or uncertain detach blocks review, integration and any new
assignment to that session/workspace. An intent or timeout is not a receipt.
Manager restart must reconcile the actual exact container/mount/assignment state
or take the confirmed-shutdown fallback; it must never infer success. Old or
duplicate handoff acknowledgments cannot authorize a later writer generation.
Keep the gate closed if shutdown itself cannot be confirmed. This is required
correctness for the experiment, not optional cleanup.

## Scope and checkpoints

Tuner owns only this dossier, standalone proof scripts and fixture evidence.
No production code, deployment config, image recipe, existing test or canonical
Git mutation is authorized. Keep IPC, logs and the live process working directory
outside the detached workspace. No copying/recloning or permission switching is
used as the revocation mechanism. Reuse the accepted dev-workspace access policy;
credentials remain separate and must not appear in evidence.

First prove the OS mechanism with a tiny deterministic resident process and a
disposable mounted fixture. Inspect the actual namespace/capability arrangement;
current OCI workers drop all capabilities. Do not add SYS_ADMIN to the agent or
use privileged Docker as an unreviewed workaround. If a trusted host helper or
additional mount authority is needed, publish the exact bounded mechanism and
request that authority before execution. Never unmount host/source/canonical repo
mounts. Resolve fixture identities before any teardown; clean only test-owned
containers and mounts, preserving evidence on uncertain cleanup.

Happy path: write round one, close handles and leave workspace, detach, verify
writer access is absent while consumer reads the same stable data, reattach and
write round two with the same resident process and workspace identity. Include
one real Claude/session two-turn proof after the mechanism works and authorized
runtime/credentials are available; deterministic process survival alone is not
proof of agent-session reuse. No broad provider or scheduler test campaign.

Bounded negatives: open-file and current-directory busy cases; interrupted
controller before/after detach acknowledgment; omitted detach; stale receipt or
attempt to reuse while uncertain. Prove no consumer or new writer proceeds until
verified revocation or confirmed shutdown. Capture mount identity, container and
process/session continuity, state transitions and monotonic timings. Compare one
equivalent stop/start cycle; do not rebuild images in the comparison.

Return evidence as promising, failed or blocked with the exact reason. Even a
successful proof does not authorize changing production custody or dispatch.

Technical references: Linux `umount(2)` and `mount_namespaces(7)` describe busy
refusal, retained references under lazy detach, and namespace-specific mounts:
https://man7.org/linux/man-pages/man2/umount.2.html
https://man7.org/linux/man-pages/man7/mount_namespaces.7.html

## Revalidation and authority boundary — 2026-09-07 — baton.tuner

Under claim event 106686, read this entire dossier and the parent custody
record's later rulings. The accepted development modes are 0664/02775/0775;
the earlier private-group-only proposal and mandatory restrictive-file recovery
matrix are superseded. Detach correctness remains mandatory under this Work.

Observed preflight: this managed context has zero effective/permitted/bounding
capabilities and no-new-privileges; the worker adapter drops all capabilities.
Docker is reachable but no W106673 runtime exists. Tools `nsenter`, `mount` and
`umount` are present, which supplies no namespace/mount privilege. Exact evidence
and a reproducible read-only probe are `evidence/preflight.json` and
`evidence/preflight.py`; separately authorized standalone Docker observations
are in `evidence/direct-docker-preflight.json`.

The Linux manual confirms ordinary unmount and joining the worker's actual
mount namespace require authority unavailable to this context. No privileged
operation was attempted to rediscover that expected boundary. No private
namespace, privileged Docker, lazy detach, forced unmount or host unmount was
used as a substitute. This is an operational prerequisite, not a measured
failure of the proposed detach mechanism.

`AUTHORITY.md` now gives the concrete operator request: exact registered
fixture/controller topology, closed operation surface, namespace/PID/mount/
generation pins, ordinary syscall, durable receipt gate, restart reconciliation,
busy shutdown fallback and subsequent real-session checkpoint. Its controller
implementation must be reviewed and installed by the operator before use.
`evidence/resident.py` is the prepared unprivileged resident, not a controller
and not a successful OS or agent-session proof. It has not run in a container.

Current proof outcome: **blocked on trusted host-controller authority**. No
workspace was mounted/detached, no resident or Claude session launched, and no
turnaround or revocation result is claimed. Stop-before-consume remains the
production behavior. References and exact privilege reasoning are in AUTHORITY.

### Preflight validation clarification

The Python preflight itself exited 0 after recording all observations, but its
Docker subprocess calls each returned exit 1 with socket permission denied.
Standalone direct Docker commands succeeded. The initial artifact check assumed
the Python probe had the same Docker access and failed that assertion; reading
the JSON exposed the distinction. Both evidence accounts are preserved, and
controller Docker execution must be explicitly included in the operator's grant.
This is the managed execution boundary, not a defect in the detach mechanism
and not an excuse to escalate or wrap denied operations differently.

## Owner response to obligation 106736 — 2026-09-07 — baton.prompt for Slawomir

Approved: tuner prepares a small experiment-only host runner in this dossier,
then Codex independently reviews its exact bytes and invocation. Slawomir will
execute the reviewed command with the required host privileges after a separate
execution checkpoint. No privileged operation, helper installation, permanent
privileged service, broad agent capability, or Docker privilege grant is authorized
by this preparation approval. This supersedes any reading of AUTHORITY.md that
requires building/installing a general controller service before testing the idea.

Keep identity registration and receipts minimal fixture machinery sufficient to
prove the required gates, not a production subsystem. First prove ordinary
detach/reattach with the deterministic resident and busy/uncertain shutdown
fallback on explicitly identified disposable resources. No provider, credentials,
network, image rebuild, canonical checkout, or production configuration is needed
for that first proof. Select an existing immutable image and explicit workspace
group as part of the reviewed execution instructions; do not invent deployment
choices or change host groups during preparation.

Return the exact runner, bounded mount/namespace/Docker requirements, disposable
target checks, failure/cleanup behavior, and operator invocation for review. Every
failed or uncertain revocation leaves consumption and reassignment denied. Actual
kernel/session/timing evidence remains pending execution; a real agent session is
a separate later checkpoint only after the OS mechanism succeeds.

## Runner preparation — 2026-09-07 — baton.tuner, claim 106813

Owner response M106756 supersedes the earlier installation prerequisite:
a dossier-local operator-run experiment is now prepared, not installed or
executed. Exact code is evidence/host_runner.py plus evidence/resident.py;
RUNNER.md specifies invocation, source/image identity, authority, gates,
cleanup limits and local validation. evidence/runner-digests.json binds the
candidate scripts. Independent review must bind those bytes before Slawomir's
separate execution checkpoint. No production or runtime adoption is requested.

The runner uses descriptor-based detached bind creation and move_mount for
reattachment, entering only the pinned resident mount namespace; ordinary
umount2(flags=0) remains the sole revocation operation. This refines the earlier
generic descriptor-based mechanism in AUTHORITY.md. No service, helper install,
worker privilege or lazy/forced revocation is needed or authorized.

The existing recipe-pinned Python image resolves locally to
sha256:9351a9a0a697a69e156f8bd067dd5ef3f9fa9b110abbdbbda1f343c622c7adc0.
Proposed fixture gid 65532 matches the fixed runtime; no host group is created
and no production manager group is inferred. These are concrete operator-review
inputs, not authority to execute. Image behavior and mount feasibility remain
unmeasured. Image-list denial and exact-inspect results are preserved.

Six local tests exercise only fixture gates and namespace identity, and pass.
The planned execution includes actual before/after helper process interruption
plus persisted gate reconstruction, then confirmed shutdown. This is explicitly
not a production-manager restart or real Claude-session result. The bounded
runner preserves every container and temporary resource for operator cleanup;
unregistered or uncertain cleanup cannot create a receipt.

Current outcome: runner preparation complete, awaiting independent byte/invocation
review and the separate privileged operator execution checkpoint. Kernel,
resident/session, cleanup and performance proofs remain pending. Stop-before-
consume remains the production rule.

## Independent runner review — 2026-09-07 — baton.codex

Claim 106911; handoff M106905. Read the full runner/resident, dossier, authority
and invocation documents, input observations, digest manifest and retained local
test output. All nine recorded hashes matched before this review append. Both
scripts independently parse. The six reported local gate tests were audited,
not redundantly rerun. No Docker creation, namespace/mount syscall, privileged
execution, host setup or production change was performed by this review.

**Reviewed for the next operator checkpoint:** the exact prepared runner and
resident have no blocking source-review finding within the deterministic fixture
scope. `review-2026-09-07T03-15-38Z.md` binds their full hashes and the proposed
command. This is not execution approval or evidence of kernel/session success.
Slawomir still decides whether to execute those bytes with the specified host
authority and fixture-only gid/image; no authority is granted to managed agents.

The source keeps ordinary `umount2(flags=0)` as the sole revocation operation,
checks the pinned runtime namespace and source object, keeps the worker
unprivileged, and closes consumption/admission during uncertain detach/attach.
Lost helper acknowledgements and persisted gate reload do not mint revocation
proof. Busy cases require shutdown. Confirmed-stop receipts require stopped Docker
state, original pidfd exit and no observed namespace process survivor. Failed
registration or uncertain cleanup leaves identified resources for the operator.
Those are inspected guards, not measured OS outcomes.

**Next owner decision:** accept the exact RUNNER.md invocation, fixed installed
image, fixture-only numeric gid65532 and bounded host namespace/Docker authority,
or retain shutdown and decline the experiment. The first run remains deterministic
and offline. Capture the printed temporary root, every container identity, result,
timings and any unresolved cleanup before evidence review. Do not interpret a
prepared-runner review as proof of real manager restart, real Claude continuity,
production access setup or a performance benefit. Those remain later checkpoints.

Review annotations deliberately change FINDING/PLAN after the preparation digest
snapshot; runner, resident, RUNNER.md, AUTHORITY.md and PROGRESS remain unchanged.
The preparation snapshot stays historical evidence and is not silently rewritten.

## Operator proof and approved next checkpoint — 2026-09-07 — baton.prompt for Slawomir

Slawomir executed the reviewed host runner and supplied result.json from
`/tmp/baton-w106673-k65r7btj`: deterministic-proof-passed. The exact supplied
result is transcribed with provenance in evidence/operator-result-2026-09-07.json.
Prompt could not independently read the protected retained directory; the result
is operator-supplied evidence, not an independent verification of its artifacts.
The experiment's eight labelled containers were observed exited.

Measured once: detach-to-consumer 66.191 ms, reattach-to-write 79.236 ms,
stop-to-consumer 3095.990 ms, restart-to-write 171.169 ms. This is promising
fixture evidence, not a general performance guarantee. No real agent session was
attempted; helper interruption and fixture reload are not production-manager recovery.

Slawomir approved independent review of this evidence followed by a bounded
real-Claude continuation checkpoint. This supersedes the pending deterministic
operator execution status above, not the production shutdown requirement.
Review the existing results without repeating the privileged experiment; identify
any additional retained artifact needed rather than bypassing its permissions.
After clean evidence review, prepare the exact real-Claude image/session,
credential mounts, invocation and authority scope for the next owner checkpoint.
No new credential access or privileged execution is implied by approval of this
sequence. Production adoption still requires explicit approval after validation.

### Timing interpretation clarification — 2026-09-07 — Slawomir via baton.prompt

The deterministic fixture timings exclude agent/model startup, session restoration
and context reload. Slawomir expects avoiding those costs to provide the larger
benefit of live-session reuse. This is a hypothesis for the real-Claude checkpoint,
not a measured saving: neither the 171 ms replacement-start timing nor the fixture
round-trip represents a restarted agent becoming productive.

For the bounded real-agent comparison, record end-of-work to the first verified
useful correction separately from mount/container timings. Confirm actual session
continuity versus restoration on the restart path, using equivalent instructions
and workspace state. Report observable startup/restoration and response timings;
do not infer provider cache hits or internal context-loading time when unavailable.
Keep this one comparable correction cycle, not a broad benchmark campaign.

## Independent result review and evidence access — 2026-09-07 — baton.codex

Claim 107091 reviewed the operator summary and current runner sources; script
hashes remain those independently reviewed before execution. Direct Docker
inspection confirms eight exact fixture containers on the approved Python image,
all exited with PID 0, exit 137 and no OOM indication. Exact observations are in
evidence/reviewer-container-state-2026-09-07.json. This confirms current stopped
state, not historical namespace revocation or gate ordering.

Observed operational finding: direct reads of retained result.json, runner.json
and happy/events.json under /tmp/baton-w106673-k65r7btj returned permission denied.
No bypass or privileged rerun was attempted. The operator-reported success is
promising and consistent with the reviewed runner, but independent evidence
acceptance is pending the exact 18-file export in EVIDENCE-REQUEST.md. Export
existing evidence with provenance; no new execution or general access is needed.

review-2026-09-07T03-43-35Z.md records this verdict and timing limits. The current
Claude adapter starts a one-shot provider per turn; outer-process continuity is
not real Claude continuity. REAL-SESSION-CHECKPOINT.md records the conditional
next preparation scope, including actual process/session identity, handle/cwd
release, exact image/credential/network choices and end-of-work to first verified
useful correction for one equivalent retained versus restart/restore pair.
No real-session execution or production adoption is implied. The current next
step is evidence export/review, superseding any reading that the supplied summary
already completed independent acceptance of the deterministic experiment.

## Export reviewed; deterministic checkpoint accepted — 2026-09-07 — baton.codex

Claim 107154 consumed owner response M107151. All 18 exported JSON files match
the provenance hashes; runner.json records the reviewed script hashes/image/gid
and result.json matches the earlier supplied summary. The read-only retained-
evidence audit passes all eight scenarios, including complete mount-table checks,
same-resident/workspace reattachment, real EBUSY negatives, before/after helper
loss, closed gates across reload, shutdown-before-consumption and baseline reuse.
Container/image/run identities match the reviewer's prior direct Docker evidence.

**Accepted at bounded deterministic proof maturity.** This explicitly resolves
and supersedes the pending evidence-acceptance status above and in
review-2026-09-07T03-43-35Z.md; that earlier permission-denial history remains true.
The exported observations are operator supplied; protected-original hashes and
exact export UTC were not independently captured. No privileged rerun is needed.
See review-2026-09-07T03-53-47Z.md, evidence/review_export.py and its retained JSON
result for the independent checks, exact bindings and limits.

Next is the bounded real-Claude preparation in REAL-SESSION-CHECKPOINT.md and
the owner's separate exact runtime/credential/network/privilege checkpoint.
Measure first verified useful correction with actual session continuity versus
restoration; deterministic mount times do not measure model startup/context costs.
The Work remains open, real-agent/production-manager proofs remain unperformed,
and production confirmed-stop remains unchanged pending explicit adoption.

## Real-session preparation revalidation — 2026-09-07 — baton.tuner, claim 107264

Owner reroute 107213 authorizes dossier-only real-Claude preparation after the
W106896 guard checkpoint, now passed for review at 107255. Re-read the entire
record, accepted exported-evidence review and REAL-SESSION-CHECKPOINT.md.

Confirmed by exact local image inspection: the selected W85497 dogfood image
sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f
is still installed, with user 65532:65532. That record's selected-image ruling
and retained gate report bind Claude 2.1.247. The host executable resolves to
2.1.250, so running host help would not validate the selected artifact. No
existing container for the selected image was found by the exact ancestor query.

Clarification: the current adapter is one-shot because it sends one text prompt
and starts a subprocess per turn. The --print flag alone does not establish
that limitation: Anthropic documents streaming input as a long-lived process,
and its SDK transport uses input/output stream-json. Those current docs/source
support a transport proposal, not measured 2.1.247 behavior. Before freezing a
credential-bearing supervisor/controller, prepare a no-network/no-credential
probe of exact-image version, flags and initialization while stdin remains open.
Actual model session continuity and restore remain later live evidence.

This is a preparation prerequisite, not a new production decision. The full
execution package cannot yet bind an owner-nominated credential source, exact
model or network/egress boundary. Asynchronous request M107276 names these
missing inputs and concrete proposed time/turn/budget limits. Prepare the
offline probe and independent task/verifier/measurement contract while it is
pending; do not guess a bearer source or inherit another runtime's authority.

Operational observations: guessed v12/worker/README.md and
v12/python/tools/dogfood_retry.py paths do not exist; rg --files located
v12/python/tools/dogfood_operator.py and the canonical image finding instead.
An initial Docker format requested absent Config.Volumes and failed template
evaluation; the corrected exact Id/User/RepoTags inspection succeeded. Neither
observation is a Baton or runtime mechanism defect. No permission bypass occurred.

## Owner runtime-input ruling — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved the proposed response to obligation 107276. This resolves the
missing owner choices for preparation; the exact executable package still returns
for independent review and a separate owner execution checkpoint.

- Credential source: `/home/sl/.claude/.credentials.json`, read-only through the
  existing per-user credential mechanism. No copying, credential-content logging,
  hashing, permission changes or whole-home mount. The old host staging path
  `/run/baton/credentials/claude` is absent and is not the nominated source.
  Verify how the existing mechanism provides container readability without
  changing the host file's restrictive access; do not invent a workaround.
- Model: Slawomir's usual Claude model, identical in both comparison arms.
  Resolve and record its exact ID from current non-secret configuration before
  freezing the package. Do not guess an ID or silently select a different model;
  any ambiguity remains an explicit input for the execution checkpoint.
- Network: ordinary Docker outbound access for Claude, no published ports.
  This is not an enforced provider-only egress allowlist. Record the concrete
  network selection in the execution package; no new firewall project required.
- Bound the experiment to one retained-versus-restart/restore pair, four user
  turns total, 180 seconds per user turn and 15 minutes overall. The proposed
  aggregate USD 3 budget is subject to verification of enforcement under the
  nominated authentication mode; do not claim a hard cap if unavailable. Report
  that limitation before execution rather than substituting credentials or billing.

No credential-bearing, networked or privileged live run is authorized by this
preparation ruling. Production behavior and the accepted shutdown fallback remain
unchanged. This supersedes the earlier missing-owner-input status, not the need
to verify the image transport, exact model, readable credential delivery and limits.

## Prepared offline transport gate and live-package blockers — 2026-09-07 — baton.tuner

M107302 supplied preparation choices. Read-only model lookup resolves the current
configured value exactly to claude-fable-5[1m]. The live package must preserve it
in both arms and separately record actual initialization model identity. Source
credential metadata is 0600 uid1000:gid1000, regular, with no extended ACL; no
bearer contents were accessed. Existing W52821 delivery reads the private source
and writes a distinct volatile slot. M107310 requests clarification of that
mechanism against the owner's no-copy restriction. No direct unreadable bind,
manual staging, host permission change or new UID mapping was substituted.

Exact network inspection of proposed default bridge was denied access to the
Docker API; no escalation, alternate wrapper or state change was attempted.
Owner scope is ordinary outbound access, not provider-only filtering. Record
the exact network identity when authorized. The USD3 proposal is not verified
as a hard cap; official CLI/cost documentation does not establish billing/quota
enforcement for the nominated authentication or resume accounting.

Prepared REAL-SESSION-PREPARATION.md, evidence/real_session_preflight.py and
evidence/real_session_contract.py. The first script is a separate offline
operator-only version/flag/initialize probe against the exact installed image.
It sends no user frame and mounts no credentials/workspace. It checks correlated
success and idle PID/start/pidfd survival, then stops and retains the labelled
container. It has not been executed against Docker. The second script supplies
the exact tiny task, remembered-token correction verifier and observable
comparison checks; it performs no filesystem/provider/controller operations.

Four local preflight tests and four local comparison tests pass; both scripts
parse. Evidence/inputs, exact commands, known limits and next-controller topology
are pinned in the preparation package. The original accepted deterministic runner
and resident hashes remain unchanged. The future credential-bearing supervisor/
controller is intentionally not frozen against an unverified transport or an
unresolved delivery rule. This is a concrete prerequisite package for independent
review and owner disposition, not completion of real-Claude preparation/execution,
and not evidence of model startup, restoration, mount or performance success.

## Credential-delivery clarification approved — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved resolving obligation 107310 by using the existing automatic
manager-owned, attempt-private volatile credential delivery. The earlier blanket
"no copying" restriction is explicitly superseded for that mechanism: the
authorized runtime may read the nominated private source and materialize its
separate short-lived slot for a read-only container mount, with existing cleanup
at the attempt's ending. This is not manual/shared host staging.

The original `/home/sl/.claude/.credentials.json` remains unchanged and private.
No chmod/chown of that source, shared staging directory, whole-home mount,
credential contents in logs/evidence, or alternative UID mapping is authorized.
Preparation may wire existing delivery and cleanup rather than invent a new
mechanism. This resolves the delivery input only: separate reviewed live-execution
approval still applies before credentials are used. The unverified USD3 cap and
pending exact-image transport proof remain separate limitations; this ruling
neither waives them nor authorizes production adoption.

## Independent offline prerequisite review — 2026-09-07 — baton.codex

Claim 107343 reviewed the complete six-artifact M107339 candidate, M107302 inputs
and the later M107362 delivery ruling. All hashes match, both scripts parse, and
accepted deterministic scripts are unchanged. Audited eight retained local test
results without repeating them. No container, credential or privileged operation.

No blocking source finding within the offline transport prerequisite. Recommend
the exact real_session_preflight.py --operator command bound in
review-2026-09-07T04-23-38Z.md for separate owner execution disposition. Review
is not execution approval or proof of real session continuity. The comparison
helper does not itself enforce runtime limits or mint a custody receipt.

M107362 resolves delivery: subsequent preparation may wire existing automatic
attempt-private materialization and cleanup. Do not reopen M107310. The older
hash-bound preparation document's unresolved-delivery passages are superseded
by that ruling; its offline executable is unaffected. Exact-image transport,
live network identity and unverified budget-cap disposition remain pending for
the full live package. The accepted deterministic proof stands and production
confirmed-stop remains unchanged.

## Offline diagnostic correction prepared — 2026-09-07 — baton.tuner, claim 107407

Revalidated M107404 against the retained result/registration and exact probe.py.
All are readable; retained probe bytes equal the original reviewed script.
The observed fast failure's actual cause remains unknown. Confirmed reporting
defect: inner catch-all discarded its cause, and docker() discarded stdout for
nonzero start before the outer boundary could read the inner failure document.

Prepared a separate evidence/real_session_preflight_diagnostic.py, preserving all
original reviewed/manifest-bound artifacts. Fixed stage/reason codes, bounded
numeric natural child status and errno now survive the inner boundary. Host
start preserves bounded stdout and exit status for exact failure projection,
records its own failure separately, and preserves primary evidence if cleanup
fails. No exception prose or provider output/stderr is exported. Existing checks
remain refusal gates, not warnings; no image/runtime input changed.

Eleven new diagnostic tests and four unchanged local tests pass. AST preservation
checks verify original assertions, initialization correlation guards, container
identity/posture checks, fixed inputs and exact Docker create/stop calls. No
Docker or provider runtime was executed. OFFLINE-DIAGNOSTIC-CHECKPOINT.md and
evidence/real-session-diagnostic-manifest.json bind the next candidate/invocation
for independent review then owner disposition. Historical source acceptance is
not runtime success. M107362 remains the resolved credential-delivery rule.

## Independent diagnostic correction acceptance — 2026-09-07 — baton.codex

Claim 107448 reviewed M107443 under the exact M107404 correction scope. All seven
candidate hashes match; all six original preparation artifacts remain unchanged.
Direct retained-file reads/hashes corroborate the original failed run. Independent
AST comparison confirms original local assertions, correlation/identity/posture
guards, fixed inputs and exact create/stop calls are preserved. Captured all
15 mocked checks passing; no Docker or provider runtime ran.

Accepted diagnostic correction for the next separate owner execution checkpoint
in review-2026-09-07T04-40-44Z.md. That append-only review binds the new script,
tests, incremental patch, instructions and manifest. Fixed inner diagnostics now
survive nonzero attached-start exit; host and cleanup failures remain separate
without raw runtime prose. The previous runtime cause remains unknown; neither
this review nor local tests establish transport or real-session success.

The proposed next invocation is real_session_preflight_diagnostic.py --operator,
superseding the original probe as the next operator candidate while preserving
its historical bytes/evidence. Return the new retained result/registration and
exact container identity after owner-approved execution. M107362 remains resolved;
full live preparation and production adoption are not completed by this correction.

## Diagnostic operator result: help-check refusal — 2026-09-07 — baton.prompt

Owner executed the independently reviewed diagnostic probe. Retained result at
/tmp/baton-w106673-session-preflight-2sv7ux6r/result.json was read directly and
agrees with the supplied output; summary/provenance is preserved in
evidence/offline-help-check-failure-2026-09-07.json. Container is reported confirmed
stopped and retained. Inner stage=help-check, reason=required-flag-absent,
child_exit_code=0, os_errno=null. Source ordering establishes that version check
passed and help command succeeded; at least one requested substring is absent
from help. The failing flag names are not retained. Streaming initialization was
not reached. This narrows the earlier unknown cause but proves neither transport
failure nor actual rejection of any flag by the installed CLI parser.

Next bounded investigation: identify the missing fixed flag names and distinguish
help visibility from actual supported invocation on the selected version. Preserve
per-flag booleans/known names in failed as well as successful diagnostic results;
avoid another opaque round. Do not drop required behavior, alter image/posture,
change credentials or claim live transport success to bypass this observation.
Return any proposed probe/acceptance correction with exact evidence for independent
review before another operator run. No further runtime was launched by prompt.

## Help visibility investigation and proposed boundary — 2026-09-07 — baton.tuner

Claim 107495 revalidated M107492, current plan, newest review and readable
retained probe/result/registration. The staged diagnostic script has its exact
reviewed hash. The failure record contains no flag map or help bytes. Thus no
specific missing flag name can be recovered from this evidence; guessing one
would mislabel inference as observation. No runtime was rerun.

Confirmed probe-design mismatch: FLAGS includes options not present in the
offline initialize argv (resume, session-id, model, max-turns, max-budget-usd and
dangerously-skip-permissions). Requiring every option's help substring before
initializing does not measure their actual acceptance or required live behavior.

Proposed bounded correction for independent review: preserve the complete fixed
flag-to-boolean help map and derived missing-name list on success and failure.
Treat help visibility as an observation, then exercise the unchanged offline
initialize argv. Actual version, command exit, correlation, live-process and
container checks remain mandatory. A pass describes idle initialization only;
it cannot satisfy the six omitted options' live requirements or establish budget,
resume, session continuity, model selection or tool-policy enforcement. Pin an
explicit pending-behavior list in the result. This proposes superseding only the
all-help-visible prerequisite to the next idle probe, not dropping any required
live capability. No new image/runtime argv, posture or credential choice.

## Help-observation candidate prepared — 2026-09-07 — baton.tuner, claim 107495

Prepared evidence/real_session_preflight_help.py and additive
evidence/test_real_session_help.py. Every fixed help flag boolean and derived
missing-name list now survives failure as well as success; unobserved help is
explicitly null. Strict projection rejects unknown names, non-booleans and
inconsistent lists. The six flags absent from the actual initialize argv remain
explicit unexercised live requirements.

The proposed all-help-visible acceptance change above is implemented only in
this unexecuted candidate: record help omissions, then require the unchanged
actual initializer. No actual requirement for later session/restore/model/limits
is discharged. Six new mocked checks and four original local checks pass.
Preservation audit confirms prior manifest-bound artifacts, original assertions/
correlation/container guards, constants and actual argv/create/stop calls remain
unchanged. OFFLINE-HELP-CHECKPOINT.md and evidence/real-session-help-manifest.json
bind exact proposal and invocation for independent review then owner disposition.
No runtime was rerun. Exact installed missing flag names remain unobserved.

## Independent help-boundary review — 2026-09-07 — baton.codex

Claim 107527 reviewed M107522 under M107492. Eight candidate hashes and both
prior manifests match; direct retained-run reads/hashes confirm help-check refusal
after successful version/help execution. Exact absent names remain unknowable
from that run. Independently captured ten mocked/original tests passing and
verified unchanged core guards, operator, inputs and actual initializer argv.

Recommend owner acceptance of the explicit bounded change in
review-2026-09-07T04-51-47Z.md: record help visibility, then require the unchanged
actual idle initializer. This recommendation does not adopt the change or grant
execution. The six unexercised options remain explicit pending live behavior;
no resume/session/model/tool-policy/limit capability is accepted by help visibility
or idle initialization. Synthetic missing flags in tests are not installed-image
observations. No blocking source issue was found within this proposal.

The exact new script/invocation is bound by OFFLINE-HELP-CHECKPOINT.md and the
help manifest. Return to baton.ops for acceptance/execution disposition, then
review retained per-flag and initializer results. Earlier invocations remain
historical evidence, M107362 stays resolved, and no real-session/production
adoption is claimed.

## Operator accepted help-inventory change; offline pass — 2026-09-07 — baton.prompt

Slawomir executed the reviewed real_session_preflight_help.py command, accepting
the bounded help-inventory/actual-initialization change for this operator run.
Retained result and registration under /tmp/baton-w106673-session-preflight-u6nurmlz
were independently read by prompt; recorded in evidence/offline-transport-pass-2026-09-07.json.
The recorded script digest matches the reviewed candidate. Exact container
444a9cd51de60cec40a6809e27b91ebb4a33764bf56b9f89575c6dc5b4e1ae24
was independently observed exited, PID0, exit0, OOMKilled=false.

Outcome offline-transport-preflight-passed on Claude 2.1.247. The sole missing
help flag is --max-turns. Unchanged actual streaming argv initialized successfully
in 204277488 ns and its idle process survived. This resolves the missing help-name
question and supplies actual offline transport evidence; it does not verify
--max-turns parser/behavior because that option was not in the initializer argv.
No real model turns, session continuation, restore or model/limit enforcement
were exercised. The older failed invocations remain valid historical observations.

Next: independent acceptance of this retained evidence, without an OS rerun,
then complete the already-approved bounded live supervisor/controller preparation
using existing automatic private credential delivery. Explicitly verify the live
invocation's remaining options and limits before claiming them supported; do not
restart the resolved credential discussion or infer an enforced billing cap.
Exact live package still requires review and separate owner execution approval.

## Independent offline transport acceptance — 2026-09-07 — baton.codex

Claim 107622 reviewed M107571. Direct retained result/registration/script hashes
and owner-export equality pass; all eight reviewed help-candidate hashes remain
unchanged. Independent standalone Docker inspection confirms the exact pinned
container/image, exited/PID0/exit0/no OOM and the offline restricted posture.
The reviewed initializer actually succeeded in 204277488 ns and survived idle;
--max-turns is the sole missing help entry. No real turn or restored session ran.

**Accepted at this bounded maturity:** offline streaming initialization, in
`review-2026-09-07T05-07-12Z.md`. This explicitly supersedes the pending owner
help-change disposition and unknown missing-name/idle-transport questions above.
It does not supersede any remaining live option, session, turn/time/cost or
production-adoption boundary. M107362's existing automatic private credential
delivery stays resolved. Next is the complete dossier-local live runner package
for independent review and separate execution approval.

The review retains direct file audit and independent container observations.
An additional shell-redirection inspection capture was denied docker.sock access;
the earlier standalone inspection had succeeded and is explicitly transcribed.
No escalation, runtime rerun or protocol workaround followed. This is an invocation
capture limitation, not a measured failure of the experiment or Baton authority.

## Complete live-package preparation boundary — 2026-09-07 — baton.tuner, claim 107665

Revalidated owner reroute 107658, accepted offline review and current plan.
Prepare separate dossier-local live_supervisor.py and live_controller.py, reusing
the accepted deterministic Gate/namespace machinery without changing its bytes.
The supervisor holds one streaming CLI between turns; the comparison restarts
a different container/CLI and resumes its original session storage. Root controller
pins init/CLI/process tree, workspace and namespace before ordinary detach;
consumption requires exact revocation or confirmed shutdown.

M107362 authorizes wiring existing UserCredentialSources and CredentialHome
materialize/tear_down. Those APIs need the original user's effective identity for
source reads and a configured held delivery group. Proposed operator composition:
root controller creates a private tmpfs credential home and non-secret registry;
the existing source reader temporarily executes with effective uid1000, then
existing materialization runs as manager root with fixture supplementary gid65532.
Only operator-process credentials/groups and fixture-owned objects change;
no persistent user/group configuration or source credential mode changes.
This explicitly supersedes the earlier preparation document's blanket “no
production manager imported” proposal only for the existing credential/group/store
APIs needed by the approved delivery. No live coordination store is used.

The exact runtime source dependencies will be hash-bound and checked before
execution; drift refuses. Session state remains fixture-private outside /output
and outside exported repository evidence. Ordinary built-in Docker bridge is the
selected outbound boundary with no published ports; runtime resolution pins its
ID before creating the three exact labelled containers. Unknown network state
refuses. No new egress-filter project or implicit model/image choice.

All implementation here is preparation for independent review and separate
operator execution. Four user turns,180s per turn,900s overall are explicit
deadlines; startup/cleanup uncertainty stays failed or blocked. The nominal
max-turns/max-budget/model/session options are included in actual prepared argv,
with observed result checks; their live behavior and USD3 hard cap are unproved
until execution and must not be inferred from the accepted idle initializer.

## Complete candidate prepared — 2026-09-07 — baton.tuner, claim 107665

Confirmed in preparation: LIVE-PACKAGE.md and evidence/live_controller.py,
live_supervisor.py, test_live_package.py implement the bounded package above.
Existing credential/source/group/store APIs are exercised offline with an
artificial private source. Nineteen tests pass, including bounded partial frames,
actual init/result identity requirements, failed-result/cost checks, process-tree
refusal, custody-before-read, descriptor/file checks, credential retention after
unconfirmed shutdown or lost create response, source identity restoration,
source-snapshot drift, closed export and the exact four-turn pair ordering.

All 23 prior preparation/diagnostic/help/deterministic manifest-bound artifacts
remain byte-identical. evidence/live-package-preservation.json records the audit.
evidence/live-package-manifest.json freezes 80 inputs; SHA256
eea4e949548c2301e4c45f815a60380b8edda1adbbc4c4f75dd6420ac496402b.
The standalone offline audit passes. These are source and offline observations,
not evidence of credential-bearing runtime or retained/restored Claude success.

Clarified bounded ending: work stops at 720 seconds to reserve 180 seconds for
ending within the 900-second runtime deadline. Result/export flushing follows;
an exhausted ending deadline leaves cleanup unconfirmed. Actual stream model
claude-fable-5 is a required unverified observation for configured argument
claude-fable-5[1m]; no alias substitution is inferred. The fixed export excludes
session, workspace, source registry, delivery, runtime snapshot and fixture DB.

Current disposition: independent candidate review by baton.bug, then baton.ops
separate execution checkpoint. Existing M107362 delivery approval is unchanged.
Live flags, billing limits, model/session restore, latency and production adoption
remain open; no production/config/recipe/existing-test/Git change was made.

## Independent live-package preparation sign-off — 2026-09-07 — baton.codex

Claim 107845 inspected the full supervisor/controller, fixed verifier/comparison,
reused namespace/gate lifecycle, credential interfaces and offline test evidence.
No blocking source finding was identified within the bounded package. All 80
manifest inputs and 23 prior artifacts independently match; the standalone audit
passes. The nineteen passing offline tests were audited, not repeated as a live
composition claim.

**Current disposition:** source/invocation preparation is signed off in
review-2026-09-07T05-45-19Z.md, binding manifest SHA256
eea4e949548c2301e4c45f815a60380b8edda1adbbc4c4f75dd6420ac496402b.
This supersedes pending independent preparation review above; it does not
supersede the separate owner execution checkpoint or any live-capability limit.
M107362 delivery remains resolved, and M107809's disjoint W105706 ownership remains
unchanged. Return to baton.ops for the exact one-pair invocation decision.

No live credential/runtime/provider operation was performed by the reviewer.
Real CLI/session continuation and restoration, combined options/model behavior,
useful-correction timing and billing bounds are unproved. Independent runtime
proof and explicit owner adoption still precede any production detach decision.

## Owner approves one real-session pair — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved the exact operator execution in LIVE-PACKAGE.md, independently
reviewed in review-2026-09-07T05-45-19Z.md. Manifest SHA256
eea4e949548c2301e4c45f815a60380b8edda1adbbc4c4f75dd6420ac496402b
is unchanged; prompt's immediate offline audit passes all 80 bound inputs.
This supersedes the pending owner execution decision above, not the requirement
for subsequent independent live-evidence review or separate production adoption.

Approval covers one retained-versus-restored Claude pair, up to three exact-image
containers/four user turns, the reviewed 900-second runtime budget and ending
limits, ordinary Docker bridge outbound connectivity, and existing private
credential delivery. The reviewed root controller's fixture-local groups and
temporary effective-UID handling are explicit parts of this experiment only;
they do not change the non-root dedicated-group access proof's requirements.
The nominal USD3 is not a verified hard billing cap. All model/CLI identity,
mount/process checks, bounded export and exact cleanup/uncertainty rules remain.
No automatic retry, input drift repair, image build/pull, model fallback,
production change or stronger unmount is approved. Operator executes the reviewed
command; managed agents do not invoke the privileged live run.

## First live invocation refused during setup — 2026-09-07 — baton.prompt

Operator executed the approved command once. Original retained root:
/tmp/baton-w106673-live-0hswl4m1; exported projections:
/tmp/baton-w106673-live-export-dzna6j98. The export reports failed-or-inconclusive,
failure_code execution-refused, consumption_and_admission denied, empty cleanup
list and cleanup_confirmed true, after 0.017681615019682795 seconds. No arms.json
or per-arm evidence is exported. Image/package and bridge projections exist;
there is no evidence of a real model turn or successful comparison.

Export hashes match PROVENANCE.json: result.json
a279113a71c7abf05b943c863b080c189716eabcb629f2bf32cc91dffeeb8279;
network.json 09ed852e06371c451ad39bf1f0964af6f262d001631d0481d5bc7f29cf1ce2a5;
package.json a31ce2377810e4614641baef94917d9e979d96aca50eb9c3b4a8b30ea4cb9063.
This verifies exported bytes against their supplied provenance, not independent
access to the protected originals or full cleanup of partially constructed setup.

Confirmed diagnostic gap: the controller reduces every non-wire.Refusal exception
to execution-refused without a stage/type. After network.json it sets groups,
snapshots runtime sources, constructs Credentials, then enters the pair. Current
evidence does not isolate the exception. In particular, Credentials construction
can fail before assignment to the outer variable, so an empty cleanup list is
not proof that every partial setup resource was removed. Do not read credential
contents or expose arbitrary exception text to diagnose this. Investigate safe
stage/type diagnostics and setup-only reproductions first; no automatic live
rerun, stronger invocation, cleanup expansion or production change is authorized.

## Setup import omission reproduced — 2026-09-07 — baton.tuner, claim 107956

**Observed:** an ordinary-user, clean-environment subprocess importing the exact
80-file reviewed snapshot fails with FileNotFoundError/ENOENT for the fixed
worker-control schema asset at contracts/schema/worker-control-1.0.schema.json.
evidence/live-setup-reproduction.json binds the original manifest and retained
reproduction. No credential construction, real source read, Docker or provider
operation occurred. frozen.py imports two JSON schema assets; the manifest and
snapshot included Python files only. Existing tests imported the checkout with
its data and did not exercise imports from the actual snapshot.

**Confirmed source defect:** the reviewed snapshot cannot import its credential
APIs. **Inferred historical cause:** this matches the operator failure immediately
after network projection and before any credential allocation. The old export
flattened the exception, so its actual traceback and partial resources remain
unobserved; do not claim an independently inspected protected-root exception.

**Bounded correction prepared next:** preserve all old package bytes; prepare a
separate controller candidate and manifest that add the two exact hash-bound
schema assets, export closed setup stage/type/errno diagnostics, and retain
constructor progress before failure. A partial constructor must not let an empty
fixture list imply cleanup success. Add offline snapshot-import and injected
partial-setup regressions. No new teardown authority, arbitrary exception text,
real bearer access, live rerun, production edit or existing-test mutation.
The old live approval does not authorize executing the replacement candidate.

## Setup correction candidate complete — 2026-09-07 — baton.tuner, claim 107956

**Confirmed offline:** adding both existing schema assets to the private snapshot
permits credential/store/group API imports in a fresh system-Python subprocess
with user site packages disabled. No source reader is constructed in that import
check. This fixes the reproduced snapshot packaging defect; it does not establish
the protected historical traceback or prove the next live stage will succeed.

Separate evidence/live_controller_setup.py preserves the original controller and
all 80 original manifest inputs. Its lifecycle owner is assigned before fallible
preparation. setup.json records closed stage/resource intent; setup-private.json
holds generated paths privately and is excluded from export. Partial attempted
construction now prevents cleanup_confirmed even with an empty fixture list.
Received store objects are closed; close failure remains a separate bounded
diagnostic. No additional resource removal or credential authority is introduced.

Twenty-eight checks pass: all 19 prior assertions unchanged against the candidate
plus nine setup/import/diagnostic/export/partial-lifecycle regressions. The full
Fixture, execute_pair, snapshot copier, Docker/mount/process/verifier helpers and
credential provider/materialize/release methods preserve their original ASTs.
The three original export hashes match their supplied provenance; protected
originals remain uninspected. evidence/live-setup-input-audit.json and
live-setup-tests.txt retain those checks.

LIVE-SETUP-CORRECTION.md and evidence/live-setup-manifest.json bind the 90-file
candidate and exact proposed invocation. Manifest SHA256
c0ec6a1d820894f9a6064b6289824f20fdf296e6e2ea7599df9f22108cbb1b30;
controller SHA256 ade171ca071c78ce992aab76462b6fa7e906be90dfedbd22cba019ceff54e485.
Current action is independent correction review, then baton.ops separate operator
disposition. The earlier preparation task is complete; live behavior, latency,
billing limits and adoption remain unproved. No automatic rerun occurred.

## Independent setup correction sign-off — 2026-09-07 — baton.codex

Claim 108038 independently reproduced the missing-schema import failure using
the actual original manifest and a clean system-Python child, and proved imports
succeed from the corrected 90-file snapshot. No credential construction/source
read occurred. The earlier preparation review missed this packaging omission;
its unchanged-input audit and checkout-based tests were insufficient to prove
private-snapshot import completeness. That earlier review remains historical.

All ninety candidate hashes and eighty unchanged original inputs match. Nine
focused setup/diagnostic/partial-lifecycle regressions pass independently. The
full fixture/pair, namespace/process/verifier helpers and credential delivery
methods preserve their ASTs. Exported original projections match supplied
provenance, but the protected original exception/resources remain unobserved.
The historical cleanup_confirmed field is not independently accepted as proof
that partial setup left nothing behind.

**Supersedes pending independent correction review:** the bounded replacement
is signed off in review-2026-09-07T06-10-40Z.md, manifest
c0ec6a1d820894f9a6064b6289824f20fdf296e6e2ea7599df9f22108cbb1b30.
Return to baton.ops for a new exact invocation decision; the consumed original
approval is not reused. No live run, bearer access, cleanup expansion, timing
result, session success or production adoption is claimed by this sign-off.

## Owner approves corrected-controller run — 2026-09-07 — baton.prompt

Slawomir approved one operator execution of live_controller_setup.py --run using
the exact sudo/env invocation in LIVE-SETUP-CORRECTION.md and independent review
review-2026-09-07T06-10-40Z.md. Immediate offline audit passes all 90 inputs;
manifest c0ec6a1d820894f9a6064b6289824f20fdf296e6e2ea7599df9f22108cbb1b30
and controller ade171ca071c78ce992aab76462b6fa7e906be90dfedbd22cba019ceff54e485
match the reviewed values. This explicitly supersedes the pending owner decision
above; it is a new bounded approval, not reuse of the earlier failed run's grant.
Same one-pair/four-turn experiment, exact original experiment image/model,
existing private credential delivery, ordinary bridge egress, reviewed root
fixture behavior and 900-second runtime budget remain. Nominal billing bounds
are still not verified hard caps. No automatic retry, production adoption,
stronger unmount, image substitution or broader cleanup. Retain the result/export
and return it for independent evidence review, whether successful or failed.

## Corrected live run: retained arm completes, comparison incomplete — 2026-09-07 — baton.prompt

Operator executed the approved setup controller. Protected original:
/tmp/baton-w106673-live-csh8co4v; readable export:
/tmp/baton-w106673-live-export-bnhjq5rq. All nine exported data-file hashes
match supplied PROVENANCE.json. Original protected bytes were not inspected.
Setup reports construction_complete and cleanup_accounted true, no unresolved
partial setup and confirmed store close. Overall result remains
failed-or-inconclusive after 20.26228991500102s, fixture-refusal at pair stage,
execution-refused, consumption_and_admission denied. No speed comparison exists.

Important partial evidence: arms.json retains a completed retained arm, actual
Claude 2.1.247/model claude-fable-5, identical process/session/workspace identities,
pidfd continuously live, both verified consumption receipts and corrected output.
Events show successful ordinary detach with denied access, verified first output,
reattach, same-session correction, second detach and verified corrected files.
First detach duration 67872486ns; reattach 30631873ns; final detach 68312975ns.
First-turn completion 410107005825906ns to verified useful correction
410118942151044ns is 11.936325138s, including the fixed five-second review delay.
These are exported observations pending independent acceptance, not production
adoption or a comparison against restored execution.

The restored-first container initializes but has no completed-turn event, and
no restored-second arm is exported. The safe failure code does not identify the
specific refused invariant. Do not infer provider outage, expired credentials
or session restore failure: an actual restore was not reached in the evidence.

Direct Docker inspect independently confirms both exact containers stopped,
PID0, no OOM, with image979f11d5:
df456ca2f698778e9ad0b0d223cdfdbda123cb205e33534a7dea43ee507f689b and
3d86c49dafeca849a138f4cd40e416722fe844d57039228669317fbc96656700.
Both container exit codes are 1; distinguish this controlled experiment ending
from successful CLI turn observations. Gates record shutdown/no survivors and
controller reports both cleanups confirmed; source credentials were not read by
prompt and their teardown is not independently verified here. The result's static
'Preparation only' limitation is stale for this actual live run and must not
erase the actual runtime evidence. Preserve the approved artifacts and route to
independent evidence review before deciding any further invocation.

## Independent retained live proof accepted; comparison diagnostic gap — 2026-09-07 — baton.codex

Claim 108110, review-2026-09-07T06-25-36Z.md: all nine export hashes and ninety
candidate inputs match. Exact readable projections are retained permanently in
evidence/live-partial-export-2026-09-07/ alongside the offline audit and independent
Docker inspection. Both exact containers are exited/PID0/no OOM; historical gate
survivor and credential teardown observations remain controller attestations.

**Supersedes pending partial-evidence acceptance and preparation-only live-session
claims:** the bounded retained actual-Claude process/session/workspace continuity
and useful correction are independently accepted. Both ordinary detaches precede
identity-bound consumption with denied access; reattach preserves the live CLI;
known solution bytes reproduce both hashes. Reviewed fixed verifier attests the
private continuity token. Verified correction takes 11.936325138s including the
five-second review delay. This is one retained observation, not comparative speed
or production adoption. Protected original bytes and raw token were not read.

**Observed diagnostic defect:** restored-first initializes and records pre-turn
quiescence, then only shutdown; no completed-turn/consumption or restored-second
exists. Fixture.turn publishes completion after response and post-turn checks,
while controller and supervisor flatten the refusal. Missing completion therefore
does not prove no dispatch or response occurred. Exact refused invariant/provider
cause remains unknown; do not infer restore or credential failure. Copied static
preparation-only limitations are stale, but historical export bytes stay intact.

**Proposed, awaiting owner decision:** prepare a separately bound dossier-only
closed diagnostic correction with safe arm/stage/refusal and intent/write/response
milestones, truthful result limitations, and offline fault/redaction regressions.
No raw diagnostic text or new runtime authority. After review, owner chooses
whether a restored-only continuation suffices or a new matched pair is necessary;
never silently label separate runs as the original pair. Preserve accepted
retained proof. PLAN now names this disposition as the only current action;
existing credential decision, confirmed-stop production behavior and W105706
parallel scope remain unchanged.

## Owner approves bounded diagnostic preparation — 2026-09-07 — baton.prompt

Slawomir accepted the next preparation recommendation from
review-2026-09-07T06-25-36Z.md: tuner prepares a separate dossier-only candidate
with closed arm/stage/refusal and intent/write/response observations, truthful
runtime milestone reporting, and focused offline fault/redaction regressions.
This explicitly supersedes the pending preparation decision above. Preserve the
independently accepted retained-process/session/workspace correction proof and
all earlier candidate/export bytes. No live rerun, new credential policy,
production adoption, raw diagnostic export or broader cleanup is authorized.
Independent candidate review precedes a separate operator execution decision;
restored-only continuation must never be presented as the original matched pair.

## Diagnostic implementation boundary — 2026-09-07 — baton.tuner, claim 110238

Revalidated owner reroute 110236 and review-2026-09-07T06-25-36Z.md. All 90
prior candidate inputs still match. The accepted retained proof and all earlier
artifacts remain unchanged. No specific cause of restored-first failure is
inferred from absence of turn-complete.

Prepare separate live_controller_diagnostic.py and live_supervisor_diagnostic.py
plus offline tests. Closed arm/operation/stage/refusal labels distinguish host
command intent/write/response, supervisor provider-write intent/completion, actual
provider result observation and post-response validation. Intent never asserts
a successful write; a missing observation never proves no side effect occurred.
Refusals project only explicit allowlisted codes and bounded numeric metadata;
unknown messages/types/fields cannot reach evidence. Runtime summaries derive
observed milestones rather than copying preparation-only text. Preserve all
receipt, identity, model, time/budget and shutdown gates.

This is diagnostic preparation only. The candidate --run path will refuse before
runtime activity while restored-only versus a new matched pair remains an owner
decision. No new operator invocation is proposed by this claim. Independent
review comes next; execution scope, timing comparability and authorization remain
a separate checkpoint. Existing credential delivery and K access paths stay intact.

## Closed runtime diagnostics prepared — 2026-09-07 — baton.tuner, claim 110238

Separate live_controller_diagnostic.py and live_supervisor_diagnostic.py now
record host intent/full-write/parsed-response boundaries, provider user-frame
intent/full-write/result-observed boundaries, and post-response validation.
Closed arm/outer-operation/command/turn/stage/refusal labels preserve failure
context. Short writes refuse without claiming full dispatch. Provider milestones
must arrive once in order, and supervisor timestamps remain separate from host
receipt timestamps. Exact response-field checks prevent extra untrusted values
from reaching logs. Unknown refusal text/types become fixed unclassified/other
labels; no arbitrary exception stringification occurs.

Future result summaries derive observed completions, consumptions, model and
retained/restored milestones rather than copying preparation-only claims. An
accepted earlier correction survives a later-arm failure without becoming a
completed matched comparison. Missing observations explicitly do not establish
absence of dispatch or effects. Historical source and result bytes are untouched.

Sixteen offline checks pass, including before/partial/after-write faults,
post-response identity and quiescence faults, provider failed-result observation,
ordered correlation/redaction, and unchanged receipt-before-read and failed-stop
credential retention. The complete diagnostic-frame path exposed a timestamp
key collision during preparation; separating supervisor_monotonic_ns from the
host timestamp fixes it, and the correlated completion test now passes.

All 90 prior candidate inputs and nine accepted export hashes still match.
Credential/setup/export/pair/verifier helpers preserve their ASTs; original
detach/consume/shutdown method bodies remain unchanged beneath observational
wrappers. Supervisor argv, framing and result-verification helpers are unchanged.
No live run or historical provider/credential/restore cause is claimed.

LIVE-DIAGNOSTICS.md and evidence/live-diagnostic-manifest.json bind 108 inputs.
Manifest SHA256 2ef942b1f58f95ff3ff59d4815e01688ee45d3dd8b10713331c6e0844335b5b3;
controller bfe220010a6a07e72dd80c0745c8213ebf9fa581fbb5422b008fce7561ee35e3;
supervisor e2f909cd74008ba155be39aa93bca4757cf5e600296f4ec9ff938ee0b097d621.
The public --run entry is disabled pending owner scope and invocation decisions.
Current action: independent diagnostic review, then baton.ops disposition;
restored-only versus a new pair remains open and no retained-arm rerun is implied.

## Independent diagnostic sign-off — 2026-09-07 — baton.codex

Claim110341 reviewed owner event110236 and tuner handoff110337. All108 candidate
hashes,90 prior bound inputs and nine accepted runtime exports match. Sixteen
offline diagnostic checks pass independently in0.005s; core credential/setup/
pair/verifier and gated bodies preserve their ASTs. Closed diagnostics distinguish
intent, full writes, parsed responses and validated completion while refusing
unknown fields/codes and preserving receipt/ending checks. Public --run remains
disabled. Evidence: review-live-diagnostic-audit-110341.json and
review-live-diagnostic-tests-2026-09-07T13-08-00Z.txt under evidence/.

**Supersedes pending independent diagnostic review:** preparation manifest
2ef942b1f58f95ff3ff59d4815e01688ee45d3dd8b10713331c6e0844335b5b3 is signed off
in review-2026-09-07T13-08-30Z.md with no blocking candidate finding. Owner next
selects restored-only continuation versus a new matched pair, then separately
binds runnable bytes/invocation for review. Restored-only is the smaller proposal
for missing restoration proof, not the original matched comparison. No live
rerun, historical-cause inference, credential-policy reopening or adoption.

**Reviewer operational finding:** while recording this review, baton.codex reused
evidence/review-diagnostic-tests-2026-09-07.txt, overwriting older prerequisite
raw test output referenced by review-2026-09-07T04-40-44Z.md. The original raw
output is no longer available at that path. New output is retained under the
unique path above; the old path now explicitly records the loss and forwarding.
The earlier review and separate hash/AST evidence remain intact. None of108
candidate inputs,90 prior bound inputs or nine accepted runtime exports changed.
This incident qualifies any blanket all-history-preserved claim; it does not
silently revise the earlier verdict or claim recovery of missing bytes. Use
unique claim/time filenames and exclusive creation for subsequent evidence.

## Owner selects restored-only continuation — 2026-09-07 — baton.prompt

Slawomir approved the recommendation following independent diagnostic sign-off
review-2026-09-07T13-08-30Z.md. This explicitly supersedes the unresolved
restored-only-versus-new-matched-pair choice above: prepare the restored-session
path only. Do not repeat the accepted retained/live-session correction arm.
Its independently accepted evidence remains valid; separately timed restoration
evidence must not be presented as the original matched pair or a controlled
speedup comparison.

Tuner owns the bounded dossier-only preparation: compose the necessary initial
session/workspace, confirmed shutdown and restoration/correction path using the
reviewed closed diagnostics; bind exact runnable bytes, invocation, resource
and time limits, expected evidence and teardown instructions for independent
review. Preserve existing image/model/credential delivery, custody and shutdown
rules, and all earlier bound candidate/export bytes. No production/config edits,
broader cleanup, new credential policy or rerun of completed proof.

This approval selects the experiment and authorizes candidate preparation, not
immediate live execution. Return the reviewed runnable candidate to baton.ops
for the exact operator invocation decision. No new live run starts here.

## Restored-only implementation boundary — 2026-09-07 — baton.tuner, claim 110487

Revalidated owner M110484 and diagnostic sign-off review-2026-09-07T13-08-30Z.md.
Prepare separate runnable controller/supervisor sources; preserve all prior bound
bytes. Compose a fresh private initial session/workspace, verify its initial
artifact only after confirmed stop, then restore that same actual session and
workspace in one replacement container and verify the remembered-token correction
after ordinary revocation. Do not reopen the protected failed-run session or
execute the retained arm. Separate timings prove restoration only, not a matched
comparison with the prior retained observation.

Narrow execution ceilings to two containers, one user turn per container, two
turns total, 180s per turn, 420s work plus 180s ending within 600s runtime.
Preserve image/model, existing private credential delivery, process/session/mount
checks, verifier, closed diagnostics and cleanup. Nominal USD1 per CLI means
USD2 for this scope, with no verified hard billing cap. Bind the exact proposed
operator invocation for independent review before separate owner execution
approval. Evidence writes use exclusive new paths; the prior reviewer loss
incident is historical and is not repaired or concealed by this preparation.

## Restored-only candidate prepared — 2026-09-07 — baton.tuner, claim 110487

The separate runnable candidate implements the boundary above. The host and
supervisor each enforce one user turn per container. A replacement is constructed
only after successful initial work, confirmed old-container shutdown and fixed
initial-byte verification. The same actual session UUID and workspace must survive
restoration in a different process; ordinary revocation and fixed correction/token
verification precede acceptance. Initial verified evidence survives a later failure.
Acceptance reports restored-only-passed and separate restoration timings, with no
retained row, pair evaluator or matched comparison.

RESTORED-ONLY.md binds the exact proposed operator invocation and unchanged
image/model, credential delivery, custody, diagnostics and teardown boundaries.
The narrowed two-container/two-turn scope has a 600s runtime ceiling and nominal
USD2 CLI budget settings, not a verified hard billing cap. Preparation does not
exercise restoration or establish future provider behavior.

Validation: 21 offline checks pass, including all 16 diagnostic assertions
unchanged against the new sources and five restoration checks with real fixture
gates/fixed-byte verification and simulated processes. Negative cases prevent
premature replacement, extra turns and acceptance without identity/custody/clock
proof. All 116 manifest hashes pass; all 108 prior bound inputs, including the
nine accepted exported-data files, remain unchanged. Claim-specific evidence is
exclusively created; the older unbound reviewer-log loss remains disclosed.

Frozen evidence/restore-only-manifest.json SHA256:
a3f5f845c344ee9418327123cbc32de37be35701dfee5b0ba342a19005681c5a.
Controller SHA256 f3fa2435ab3a90643fa2fdf4e9cd58d9ca5bc6f114c0ad032fa8dcca0310ed51;
supervisor SHA256 3322a0494f8dd51be1f8188e626e522ad676dfee4c380d6c939b9827e4f3082f.
Independent candidate review precedes separate owner execution approval through
baton.ops. No live/provider/real-credential operation or production/config edit
occurred; accepted retained proof and the unknown historical failure cause remain
separate from this unexecuted restoration candidate.

## Restored-only constructor refusal — 2026-09-07 — baton.codex

**Confirmed; changes requested:** independent review under claim 110564
reproduces a blocking constructor defect in the restored-only candidate. The
fresh private-session subdirectory loop reuses the requested `name` parameter;
`self.arm` becomes `cache`, then raises `diagnostic-arm-invalid` before the
first container is created. The same defect is present in the diagnostic
candidate and was missed by the previous independent review. All 21 offline
tests pass because their fixture paths replace or bypass the real constructor.

Exact reproduction, evidence and correction boundary: `review-2026-09-07T13-42-14Z.md`
and `evidence/review-110564/`. All 116 hashes, 108 prior bound inputs and nine
accepted exports match. Preserve earlier bytes and prepare a separately bound
constructor correction plus real-constructor regression within this dossier.
No additional runtime, credential or production authority is needed.

This explicitly supersedes pending runnable sign-off and the preceding diagnostic
review's no-blocking-candidate conclusion for the fresh constructor. Prior
reviews remain historical; diagnostic checks and accepted retained live proof
remain valid. The newly reproduced pre-container refusal does not explain the
earlier live restored-first failure, whose cause remains unknown. Do not run
the proposed privileged candidate; return corrected bytes through review, then
baton.ops for the separate exact execution decision.

## Constructor correction boundary — 2026-09-07 — baton.tuner, claim 110596

Revalidated review-2026-09-07T13-42-14Z.md and ran its actual-constructor probe:
both frozen restored-only and diagnostic controllers assign cache as the fresh
arm and refuse diagnostic-arm-invalid, with zero Docker/credential calls.
Prepare a separate controller that renames only the private-subdirectory loop
variable and points to its new manifest. Reuse the unchanged restored supervisor.
Add real fresh/replacement constructor regressions with only chown mocked and
external/credential operations forbidden; preserve all 21 existing assertions.
Bind a new exact invocation and all prior hashes for independent review, then
separate ops execution approval. No live run or change to restoration, credential,
custody, diagnostics, limits, teardown or accepted retained proof is authorized.

## Constructor correction prepared — 2026-09-07 — baton.tuner, claim 110596

The new live_controller_restore_constructor.py differs from the frozen restored
controller only in its manifest basename and the private-subdirectory loop
variable. The actual fresh constructor now preserves restored-first; replacement
preserves restored-second and reuses the same private session/workspace. The
restored supervisor and all earlier bound sources/evidence remain unchanged.

Twenty-three offline checks pass: the previous 21 assertions unchanged against
the corrected controller, plus real fresh/replacement and unsupported-arm tests.
Successful construction mocks only chown; real temporary directories, modes,
UUIDs and identity checks are exercised. Forbidden external/credential spies
receive no calls. Running the new constructor tests against the frozen old
controller reproduces the expected diagnostic-arm-invalid error. Both baseline
and passing output are preserved in exclusive claim-110596 evidence files.

All 125 hashes pass the standalone audit, including all 116 prior bound inputs
and the nine accepted exports. The source patch and input-preservation audit
are bound in evidence/restore-constructor-manifest.json, SHA256
b6058f4774775c63113f0f9721e264dd317a4f57692b2ebfdf3264511c032c4b.
Corrected controller SHA256:
fd551c9684b2caa4577482bd5305b5f2a8e5ed22032d821b801f1ca33305f247.
Unchanged supervisor SHA256:
3322a0494f8dd51be1f8188e626e522ad676dfee4c380d6c939b9827e4f3082f.

RESTORED-CONSTRUCTOR-CORRECTION.md supersedes the future controller/manifest/
invocation selection while retaining the earlier restored-only runtime limits,
authority, custody and ending requirements. Independent review and separate exact
owner execution approval remain pending; no live run or production change occurred.
This correction neither explains the historical live failure nor establishes
restoration, a matched comparison or production adoption. Earlier reviews and
the disclosed unbound reviewer-log loss remain unchanged history.

## Independent constructor correction sign-off — 2026-09-07 — baton.codex

Claim 110810 reviewed tuner handoff 110624. Exact text comparison confirms only
the manifest basename and private-subdirectory loop variable differ from the
frozen restored controller; supervisor bytes are unchanged. All 125 input
hashes, 116 prior bound inputs and nine accepted export hashes match. The
standalone --audit passes. Audited 23 passing offline checks and the expected
old-source constructor regression failure without repeating the same suites.

**Supersedes pending independent constructor review:** no blocking finding
remains for the corrected candidate, signed off in `review-2026-09-07T14-19-04Z.md`. Manifest
`b6058f4774775c63113f0f9721e264dd317a4f57692b2ebfdf3264511c032c4b`
binds the exact candidate/invocation. Earlier controllers remain frozen with
their defect; prior reviews and the disclosed unbound-log loss remain history.

Next is the separate baton.ops owner execution decision for the single command
in RESTORED-CONSTRUCTOR-CORRECTION.md. No live run, runtime authority, restored
session success, matched comparison or production adoption follows from source
sign-off. Preserve the two-container/two-turn/600-second limits, existing
credential/custody/teardown rules and accepted retained live proof. The earlier
live restored-first failure cause remains unknown. Exclusive independent
evidence is in `evidence/review-110810/`; PROGRESS was not edited.

## Independent restored-only failed-run review — 2026-09-07 — baton.codex

Claim 111006 reviewed owner execution handoff 110864. Six exported data hashes
match supplied provenance and are preserved with PROVENANCE.json under
evidence/review-111006/export/. Exact package manifest matches the signed-off
constructor candidate. Protected originals and private session bytes remain
uninspected; provenance supports exported projections, not an independent
original-byte audit.

**Supersedes pending owner execution/returned-evidence review:** the owner ran
the corrected restored-only command; the result is failed-or-inconclusive.
Fresh restored-first CLI initialization, local full user-frame write and an
actual result-frame observation precede provider-result-failed at result
validation. Zero validated completions/consumptions, no replacement or restoration
initialization. No validated actual model or restored proof; no useful timing or
matched comparison. Accepted prior retained proof remains separate and valid.

Independent Docker inspection confirms the exact exported container exited,
PID0, no OOM, matching image and labels. Gate shutdown/identity and controller
cleanup attestations agree; historical namespace absence and credential teardown
were not independently inspected. Details and limits are in
review-2026-09-07T14-50-28Z.md and evidence/review-111006/.

**Confirmed diagnostic limitation:** result_projection combines subtype success
and is_error false, then discards those fields on refusal. Four synthetic cases
reproduce the same code. CLI-declared error versus malformed/missing success
fields cannot be distinguished, and authentication/provider/network/restore
causes are unknown. This does not retroactively explain the earlier paired-run
failure. Proposed next action is owner disposition of separate dossier-only
closed result-field diagnostics and offline redaction/correlation regressions,
then independent review before a separate execution decision. No live rerun.

**Observed current input drift:** 124 of125 current manifest inputs match.
job_manager/review_driver.py has changed; exact expected/observed hashes are in
the review/audit. Constructor/supervisor and earlier dossier/accepted-export bytes
match. This does not establish historical runtime drift. A new candidate must
revalidate and bind current dependencies; preserve old manifests and unrelated
work. The old exact invocation now fails its audit and is not a runnable retry.

## Owner-approved result diagnostics — 2026-09-07 — baton.tuner, claim 111078

Owner reroute 111076 approves the bounded preparation proposed in
review-2026-09-07T14-50-28Z.md. This explicitly supersedes the pending diagnostic
preparation decision above. Revalidation confirms the current restored supervisor
observes a result but combines subtype and is_error into provider-result-failed,
discarding their individual shapes before export. No historical provider root
cause can be recovered from the closed exported evidence.

Prepare separate dossier-only controller/supervisor sources and an exact new
manifest/invocation. Before the unchanged result acceptance checks, emit only
closed subtype and error-flag classifications, correlated to arm/operation/turn.
Known nonsuccess labels require a verified transport-contract source; arbitrary
or unsupported labels remain unknown. No provider messages, result/errors text,
arbitrary keys, stderr or private session data may enter evidence. Preserve all
acceptance, receipt, session/model/cost, admission and ending gates. Add offline
success/failure/field-shape/redaction/correlation checks without changing earlier
assertions. Revalidate current runtime dependencies and record changed bindings
explicitly while preserving all historical dossier bytes and unrelated edits.

Return the completed candidate to baton.bug for independent review, then
baton.ops. Preparation grants no live invocation, private-session inspection,
raw provider export, production change or retained-arm repetition. Existing
two-container/two-turn/600-second restored-only scope and credential/custody/
teardown rules remain. Earlier retained proof stays separate; no matched timing
comparison or restoration success follows from this diagnostic preparation.

## Result diagnostics prepared — 2026-09-07 — baton.tuner, claim 111078

Separate live_controller_result_diagnostics.py and
live_supervisor_result_diagnostics.py now retain closed subtype/is_error shapes
before the unchanged compound success predicate. Known nonsuccess labels come
from the official transport documentation recorded locally in
evidence/result-subtype-contract-111078.json; this is an allowlist, not proof of
every label's emission by the pinned image. Unknown strings and provider prose
are never exported. The exact host schema, arm/operation/turn and ordered-stage
checks validate the nested summary before logging. Legacy frames with no summary
stay explicitly unobserved. No acceptance gate depends on diagnostic presence.

Eight focused offline tests pass in0.008s, including actual supervisor/host
methods on synthetic results and independent field-shape/redaction/correlation
cases. Failed results retain their fields and still produce zero validated
completions or consumptions. The broader32-check gate passes in0.232s: all23
preceding diagnostic/restoration/real-constructor assertions unchanged, eight
earlier stream/result tests against the new supervisor, and fresh imports from
the actual new dependency snapshot. The credential/group/store/source APIs
import successfully without constructing a source reader or runtime; the changed
review_driver module is not imported on that path.

All167 historical dossier files audited outside FINDING/PLAN/PROGRESS remain
unchanged, including accepted and failed exported evidence. Of125 prior manifest
inputs,124 match; the one previously observed review_driver.py dependency is
explicitly rebound to current bytes. Its top-level body contains imports,
constants and function definitions only. No unrelated edit was reverted and no
historical runtime drift is inferred. AST/text checks preserve result acceptance,
CLI argv, restoration/verifier, credentials, setup, custody and ending behavior.

RESULT-DIAGNOSTICS.md and evidence/result-diagnostics-manifest.json bind143 inputs.
Manifest SHA256 bb2f29412486a2ed3846e9c7235f1481e5cb62e16b7a6889ca3fbbc8b9d1c0fd;
controller d19221fd610320c8bb2d87ff225eedd609694b9a46133a2402b5c903d21e9251;
supervisor 94c6dd20122131f2a67bcd00c50d55e94ac5b65f14d648f036d8532fcf0cca41.
Exclusive claim111078 evidence retains the baseline, patch, focused result,
broader raw output and reproducible source/preservation audit.

This supersedes preparation-in-progress, not the separate independent review
and owner execution gates. Current action is independent candidate review through
baton.bug, then baton.ops. No live/provider/credential operation, private-session
inspection, production edit or Git mutation occurred. Restoration and historical
provider cause remain unknown; accepted retained proof remains separate.

## 2026-09-07T15-25-45Z — independent closed result-diagnostic review, claim 111259

**Supersedes pending diagnostic-source review:** no blocking finding remains in the separate controller/supervisor change bound by manifest bb2f29412486a2ed3846e9c7235f1481e5cb62e16b7a6889ca3fbbc8b9d1c0fd. Full sign-off and limits: `review-2026-09-07T15-25-45Z.md`. Closed field projection and host validation preserve prior acceptance, custody and ending behavior. Recorded eight focused and32 broader checks were audited, not redundantly rerun. All167 historical protected files match.

**Current invocation blocked:** independent verification finds142 of143 manifest inputs match. review_driver.py changed again from62db37ee... tofcac6d17..., recorded exactly in `evidence/review-111259/audit.json`; the standalone offline --audit exits1 before setup. This is current dependency drift, not historical-run evidence or a diagnostic-source regression. Preserve the manifest and unrelated source changes. Recommend one tuner revalidation/rebind after the active W110772 correction settles, then independent exact-binding review and separate ops execution disposition. No live invocation, restored proof or comparative timing is authorized or claimed.

## Dependency rebind boundary — 2026-09-07 — baton.tuner, claim112609

Owner reroute111303 authorizes bounded dependency revalidation and a separately
bound manifest/invocation, preserving the diagnostic semantics signed off in
review-2026-09-07T15-25-45Z.md. This supersedes the pending ops preparation
disposition, not independent exact-binding review or separate execution approval.
Canonical revalidation finds W110772 and joined acceptance W112039 closed
satisfying; W112039 closed112601 after both accepted providers completed.
W110934 also closed satisfying112242. Their bounded acceptance does not waive
historical broad failures or authorize this experiment's live invocation.

Current manifest comparison finds six changed production dependencies and one
added runtime module, integration/oci_delivery.py. Rebind the complete current
Python package and existing schema/source-reader assets; delete no dependency.
Preserve every old manifest, source, invocation document and exported observation.
Prepare a separate controller changing only its manifest filename and an additive
copy of the offline checks selecting it. Audit exact source equality, current
closure and fresh-snapshot imports before returning to baton.bug, then baton.ops.
The accepted credential, custody, diagnostics, restoration and ending semantics,
two-container/two-turn/600-second limits and separate retained proof remain.
No live run, private-session inspection, production edit or stronger cleanup.
Claim-specific before hashes and evidence use exclusive evidence/rebind-112609/.

## Dependency rebind prepared — 2026-09-07 — baton.tuner, claim112609

The separate controller differs from the independently signed-off diagnostic
controller only in its manifest filename. Supervisor bytes and all prior test
assertions are unchanged. The current package retains every one of143 prior
inputs, explicitly rebinds six dependencies, adds the accepted OCI module and
binds152 inputs in total. All six changed hashes and the added hash match
accepted joined/OCI candidate maps. Production bytes were not edited.

Eight focused checks pass in0.008s and32 broader checks pass in0.239s, including
actual fresh-snapshot imports without source-reader/runtime construction. The
standalone audit passes all152 inputs. All191 protected historical dossier
files match the claim baseline; earlier accepted and failed evidence is preserved.
Exact commands/output, source/test patches, accepted dependency map and the
reproducible preservation audit are in evidence/rebind-112609/. No live run,
private-session inspection, credential read, production or Git mutation occurred.

DEPENDENCY-REBIND-112609.md supplies the exact proposed invocation. Manifest
SHA256 2d829e03d3337c9eabf05d4e0d0ce01097bc185be24b991d0b3012b0ea3a78e5;
controller 2ce81534d65f8f82d4797e4f4b0ce9afd903aca2df154d567db3fd6eaeeea92d.
This supersedes preparation-in-progress and the old candidate as the proposed
future invocation. Independent exact-binding review through baton.bug precedes
baton.ops separate execution disposition. Existing restored-only limits and
accepted retained proof remain; restoration and comparative timing are unproved.
Historical broad red gates remain unwaived and were not rerun for this binding.
