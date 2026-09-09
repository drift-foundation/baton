# Bind line custody to the mounted writer roots

Ledger Work: W105982. Filed 2026-09-07 by baton.tuner during W105706's
approved source/locator triage. Discovery record:
`baton:work/records/2026/09/finding-v12-private-line-runtime-access/`.

## Confirmed by source trace

`review_cycles.writer_boundary` calls `workspaces.line_assignment_workspace`,
which replaces the ordinary attempt workspace with
`<storage>/.baton-review-lines/<line_id>/checkout`. The recorded device/inode
and active generation grant protect that direct writer mount.

`OciAdapter.seal` reads that mounted workspace through `assignment_roots`.
Its `_home` derives the parent of that workspace, so `_custody(attempt_id)`
places immutable artifacts and `sealed.json` under
`<storage>/.baton-review-lines/<line_id>/custody/<attempt_id>`.

However, `intake._normalized` invokes `normalize_directory` for `result` then
`workspace`. `OciAdapter.normalize_directory` passes only the store, attempt
identity and selector to `custody.custody_act`. `_derived_root` selects
`<storage>/<attempt_id>/workspace/result-<attempt_id>` and
`<storage>/<attempt_id>/workspace`. It never resolves a line writer, line pin,
or mounted roots. Those are the directories the ordinary allocator created;
their presence does not prove normalization of any persistent-line content.

The ordering is a second part of this same boundary: the current
`job_manager.review_driver.end_implementation` quiesces, seals, collects,
publishes, freezes the checkpoint, and only then calls `authorize_cleanup`.
The latter reaches ordinary-root normalization after runtime destruction.
`freeze_checkpoint` calls the profile over the line without line custody.
Thus the earlier manager reads have no line-specific restoration of access
for worker-created restrictive directories/files. Initial manager-owned group
provisioning cannot grant access to a later worker-owned mode-0700 directory.

This is a source-confirmed missing custody subject/ordering guarantee, not a
claim of a measured production failure. Exact-runtime reproduction is an
acceptance requirement. The previously alleged missing-result-directory
refusal remains explicitly superseded: the ordinary result directory exists,
and adding an empty result directory inside the line would not fix this gap.

## Proposed bounded correction; owner scope acceptance required

Resolve the writer attempt's actual line from durable lifecycle state within
the custody operation, prove its persisted object pin and exact generation,
and normalize only that authorized line using the existing fixed worker
identity and dedicated sharing group. Preserve the non-line derivation.
Do not accept caller-supplied host roots or reuse an ordinary-root receipt as
evidence for a different directory.

State and review where the exact runtime becomes absent/fenced before such a
helper starts, and where normalization must precede completion reading,
sealing, checkpoint validation and a later correction writer. The live proposal
publication must still precede Authority finalization. Do not solve the
ordering by finalizing the assignment early, releasing a second writer, or
moving an existing protection behind a read it is meant to protect.

The helper must restore usable sharing for worker-created files and nested
directories, including primary-group or restrictive-mode creations, without
relying on cooperative umask. Cover manager-created checkpoint metadata needed
by the next writer through the initial-access provider's same permission
policy; neither provider should silently own the other's filesystem changes.
Retained artifacts in the line's sibling custody stay outside writer mounts;
ordinary attempt cleanup must neither delete the persistent line nor claim
it normalized it. Decide explicitly whether an additional retained-result
subject is needed; do not conflate sealed manager-owned custody with the
worker's untrusted result directory.

Likely code owners for a bounded plan: `worker_manager/custody.py`,
`worker_manager/oci.py`, `worker_manager/intake.py`,
`worker_manager/review_cycles.py`, and the exact orchestration caller in
`job_manager/review_driver.py`. This list is investigation guidance, not
accepted edit authority; reduce it to an exact reviewed patch boundary.

Focused proof: the launched line root and each normalized/retained root are
identified independently; a worker-created restrictive nested payload and
private metadata become manager-readable before the first consuming read;
the manager seals/validates and a second serial writer continues; retained
artifact locators survive ordinary attempt cleanup. Wrong generation, replaced
line, stale receipt, unrelated sibling and source/reviewer mutation all refuse.
Keep this an enabling line-custody slice, not a general runtime hardening suite.

## Coordination and execution limits

Creation with parent W103068 was refused because baton.tuner is not a handler
of that parent's route. No Work was created by that refused operation. The
standalone creation succeeded at event 105982; the eligible parent owner should
attach it to stage composition and decide the actual prerequisite edges.
This is ordinary route authority, not a Baton defect or a bypass.

No production code, existing tests, runtime permissions, Git state, or live
coordination store was modified to obtain the source evidence.

## Independent discovery confirmation — 2026-09-07 — baton.codex

W105706 review `../finding-v12-private-line-runtime-access/review-2026-09-07T00-51-29Z.md`
independently confirms the mounted/normalized/retained locator distinction
and ordering from the six unchanged production fingerprints in the discovery
trace. This confirms the finding, not an implementation plan or candidate.
Existing normalization ORs mode bits on owned descendants; it does not change
them to the configured gid. The bounded custody plan must explicitly cover the
required group, restrictive nested entries and subsequent serial writer access.

W103068 now depends on W105982 at event 106054. The requested later containment
attachment has no exposed canonical CLI operation; W106052 records the
limitation. W105982 remains top-level, with a stated documentary index in the
composition PLAN as a stopgap. No store mutation or replacement Work is used
to fabricate the requested parent history.

## Workspace-policy clarification — 2026-09-07 — baton.prompt for Slawomir

The accepted superseding policy lives in
`../finding-v12-private-line-runtime-access/FINDING.md`, "Superseding workspace
access ruling": files 0664, directories 02775, executables 0775 on the reusable
development line; group writes, world reads, read-only reviewer mounts and
credentials kept separately. Normal review/correction transitions should not
recursively switch workspace modes. Restrictive files are exceptional compatibility
issues, not a mandatory first-demo hardening campaign.

This explicitly supersedes the earlier requirement here to prove unconditional
restoration from noncooperative restrictive creations as part of the happy path.
The confirmed locator/order defect remains: operations must address the actual
recorded line, and required access must exist before consuming its results.
Plan the smallest correct common-case path; report exceptional access failure
without falsely publishing successful custody or admitting overlapping writers.
Whether/how exceptional repair runs remains a separate scope decision. Nothing
here authorizes arbitrary root selection, deleting the line, making immutable
evidence writable, changing credential modes or bypassing safe quiescence.

## Approved detach experiment — 2026-09-07 — baton.prompt for Slawomir

W106673 at `../finding-v12-live-session-workspace-detach/` owns a bounded
detach/review/reattach proof preserving the live agent session. Busy after declared
completion is a protocol defect requiring shutdown. Failed, omitted or uncertain
detach, including manager restart, must gate consumption and reassignment until
revocation or shutdown is confirmed. This records experimental authorization only:
production stop-before-consume remains unchanged pending proof review and adoption.

## Approved bounded planning — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved progressing this subject/order correction through a bounded
revised plan. The managed reviewer owns dossier-only planning while K completes
the proposal composer and tuner proves detach/revises access. Pin exact durable
root resolution, consumption ordering, and minimal source/additive-test scope;
identify any overlap with the access provider before implementation, with shared
production paths serialized rather than edited concurrently.

Apply stable shared-write/world-read workspace defaults and read-only reviewer
mounts; no routine recursive handoff permission switching. Confirmed shutdown is
the current quiescence boundary. A verified-detach alternative remains experimental
until independent proof acceptance and owner adoption. Busy after completion is
a protocol defect requiring shutdown; omitted/failed/uncertain detach must block
consumption and reassignment even across restart. Do not add mount machinery here
or make repairing all restrictive worker-created modes a first-demo gate.

Return the minimal plan and any concrete unresolved decision to the owner before
production edits. Planning sign-off is not implementation or runtime evidence.

## Revised subject/order proposal — 2026-09-07 — baton.codex

**Confirmed:** fresh source inspection under claim 106716 preserves the original
locator trace. `review_driver._quiesced` positively stops the recorded runtime
and reconciles it; `end_implementation` then observes disposition and calls
`request_freeze` before checkpoint finalization. `OciAdapter.seal` consumes
`assignment_roots`, while `custody._derived_root` and `intake._normalized` still
address ordinary attempt roots after destruction. The adapter's root mapping
alone is not durable line authority: even `AllocatedRoots` explicitly disclaims
that guarantee. Existing line device/inode and generation checks are reusable.

**Superseded:** the earlier "Proposed bounded correction" and discovery
confirmation are no longer actionable where they prescribe routinely normalizing
the line, require arbitrary restrictive-file recovery, or suggest moving the
existing normalization helper before seal. The stable-mode owner ruling replaces
those requirements. The old helper requires destruction/cleanup authority; its
receipt accurately names ordinary attempt directories and must stay so.

**Proposed:** resolve and prove the actual line for consumption without changing
permissions. Derive the subject from the durable writer/attempt/line relation,
assignment authority and generation, configured storage, and recorded object pin.
Bind the adapter's workspace and retained sibling locator to that resolved subject
at use, rather than accepting a caller-selected path or trusting a saved root map.
After confirmed stop, verify manager traversal/open access to payload and private
metadata before the first completion/seal read. Reuse bounded no-follow traversal;
proof does not chmod/chgrp or read through links into another tree. Actual manager
access is distinct from mode bits or `os.access`. Sealing/profile operations still
own byte validation. The writer grant remains exclusive through publication and
checkpoint freeze. Retries re-resolve state/object identity and re-observe runtime;
ordinary receipts and memory-only proof cannot authorize another generation or
survive restart as shutdown evidence. Access failure refuses before publication
without admitting a new writer. Exceptional repair remains separate scope.

For configured storage S, line L and attempt A:

| Purpose | Subject |
| --- | --- |
| Writer data and completion | Durable pinned `S/.baton-review-lines/L/checkout` |
| Immutable retained result | Manager sibling `S/.baton-review-lines/L/custody/A`, outside the writer mount |
| Ordinary cleanup/normalization | `S/A/workspace/result-A` and `S/A/workspace`; receipts claim only these subjects |
| Reviewer output | Its ordinary attempt workspace; checkpoint source remains mounted read-only |

No additional retained-result subject is proposed. Verify the existing sibling
locator's provenance, immutability and survival across ordinary cleanup.
Credentials remain governed separately, not by development-line modes.

**Open, owner decision:** accept the proof-only correction and nine-path additive
scope in PLAN, with access-provider changes first and shared files serialized.
Dedicated group/exact-image authorization stays with W105706. W106673 is an
experimental child, not an adopted shutdown replacement. Stop-path planning need
not wait for that experiment, but W105982 cannot close while its child is open.

**Coordination:** M106747 on T105706 reports this boundary and overlap before
production edits. PLAN gives the complete shared path set. This turn changed only
the owning dossier; the append-only review retains the inspected source baseline.

## Owner scope approval — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved the proof-only actual-line consumption gate, exact nine-path
scope in PLAN, additive-only tests, and access-first serial ownership. This
supersedes the pending scope decision above. No production detach, routine mode
repair, arbitrary root API or broad hardening is authorized. Confirmed shutdown
precedes access proof and consumption; publication still precedes finalization.

The initial access code/interface checkpoint is W106896 under W105706. Wait for
that reviewed checkpoint, NOT full W105706 acceptance, before implementation.
Revalidate its accepted bytes and take shared paths serially; K owns custody after
the checkpoint. W105706 then consumes custody for its full runtime proof. This
avoids a cycle in which each full capability waits for the other's closure.
Group/image and exact live-run authority remain explicitly resolved through the
access provider. The experimental child requires its own disposition but is not
an authorization to substitute unmount for shutdown in production.

## Independent candidate findings — 2026-09-07 — baton.codex

**Confirmed under claim 107590:** the eight-file candidate places the actual-line
proof before sealing without repairing modes. The new proof does not complete
three approved boundaries: the later checkpoint profile still consumes a pathname
without rechecking its pin after the external fence; subject resolution does not
compare the granted participant/principal to the assignment; and a trailing run
of symlinks can exceed MAX_ENTRIES. Disposable regressions reproduce all three
missing refusals. The checkpoint gap predates the candidate but remains within
this Work's explicitly accepted correction. No live failure is claimed.

Current disposition is **changes requested**, recorded in
`review-2026-09-07T05-03-18Z.md`, with exact candidate manifest, retained bytes,
failing reproductions and 45 passing focused candidate cases. That review also
requests the pre-custody job test bytes for the additive-only audit and disposition
of two new public export entries against the accepted private-scope boundary.
No earlier finding or review is rewritten. Runtime proof and child disposition
remain outstanding; neither source review nor the detach experiment authorizes
production detach or recurring mode normalization.

## Owner-approved bounded correction — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved returning the candidate to K for the three reproduced gaps in
review-2026-09-07T05-03-18Z.md, within the existing production/test path scope:
revalidate the durable line/object pin at actual checkpoint consumption after
the external fence, compare the granted participant and principal to the current
assignment at subject resolution, and enforce the entry ceiling for symlinks too.
Preserve legitimate preparing/frozen checkpoint replay; a revoked checkpoint
writer must not be required to become active again merely to resume that path.

Resolve the export question by keeping the new helpers private. No new public
API or expanded scope is approved. Supply the actual retained pre-custody
job-driver test bytes and incremental diff for additive-only review; if unavailable,
report that evidence gap rather than reconstructing and presenting it as retained.
Add focused regressions for the reproduced failures and verify the bounded
correction first. Do not repeat the full test campaign. Return exact candidate
hashes, results and evidence to independent review, then owner disposition.
Confirmed shutdown and stable permissions remain unchanged; no production detach
or permission repair is authorized by this correction.

## Independent correction sign-off — 2026-09-07 — baton.codex

Claim 107680 independently resolves the three findings in the first candidate
review: checkpoint-use pin validation now runs after the fence and preserves
legitimate preparing/frozen replay; consumption resolves the granted participant
and principal; symlinks enforce the entry ceiling. Three retained reproductions
and four focused lifecycle/identity checks pass. The private helper/export ruling
is satisfied and the eight corrected hashes match PROGRESS.

The job-test predecessor supplied by implementation was a reconstruction, not a
retained historical artifact. Removing one extra trailing newline independently
matches the exact earlier signed-off hash; all 113 prior assertion calls are
preserved in their methods. This resolves the byte-preservation audit without
claiming historical retention. Exact provenance and diff are retained in evidence.

**Supersedes the earlier changes-requested disposition for these candidate code
findings:** the code checkpoint is signed off in review-2026-09-07T05-16-52Z.md,
bound to evidence/review-corrected-manifest.json. Full runtime proof and open child
W106673 remain outstanding. No production detach, recurring permission repair or
full Work closure is accepted by this correction review.

## Owner accepts code checkpoint and releases composition — 2026-09-07 — baton.prompt

Slawomir accepted the corrected code checkpoint signed off in
review-2026-09-07T05-16-52Z.md. Prompt rechecked all eight working-tree hashes
against evidence/review-corrected-manifest.json; all match. This accepts the
bounded code/interface, not live runtime proof or production detach.

Owner approved removing W105706's dependency on full W105982 closure: the needed
code prerequisite is now accepted, while that consumer supplies this Work's
remaining live proof. Waiting for full closure would create a circular acceptance
gate and also serialize the separate detach experiment onto the critical path.
W105982 remains open for runtime evidence and its experimental child's disposition.
No recorded test or acceptance requirement is waived. Composition may revalidate
and use the accepted code now; exact runtime setup still needs its recorded grant.

## 2026-09-07T15-46-38Z — confirmed-stop evidence reconciliation, claim111390

**Confirmed:** W105706 closed satisfying at110273 after the accepted configured runtime review of2026-09-07T12-52-22Z. Its exact fixture remains20981569…; the eight retained custody code files match. Actual fixed-user writing, positive stop, generation1/2 line consumption, read-only reviewer denials, same-line correction/current checkpoint and historical audit satisfy those bounded requirements. This supersedes the earlier blanket statement that the entire configured access/checkpoint runtime proof remains outstanding.

**Still outstanding:** the referenced engine fixture checks the sibling custody path but never runs actual result seal/intake/retention/ordinary-cleanup and reopens retained artifact bytes afterward. Checkpoint Git-reference preservation and fixture container teardown do not establish that separate accepted requirement. Exact source inventory and current-versus-retained hashes are in `evidence/reconciliation-111390/audit.json`; analysis and acceptance map are in `review-2026-09-07T15-46-38Z.md`. Newer OCI/review-driver changes are not certified by the historical proof.

**Proposed owner disposition:** stop requiring full W105982 closure for W103068 composition, while explicitly carrying the residual retained-result/ordinary-cleanup check into W103083/W103068 final lifecycle acceptance and cross-linking its result here. Accepted code/access evidence may be consumed now; no proof is waived. W106673 remains an open experimental child and W105982 stays open for its disposition/residual evidence. This recommendation does not itself remove a dependency, authorize a runtime, or replace production shutdown. Owner reroute111387 authorized evidence review only.

## 2026-09-07T15-51-57Z — owner-approved assembly acceptance, claim111429

**Confirmed decision:** owner reroute111426 accepts review-2026-09-07T15-46-38Z.md.
This supersedes the pending proposal above and the requirement that W103068 wait
for full W105982 closure. Before correcting that one dependency, the residual
proof is pinned as mandatory acceptance in this PLAN and in both FINDING/PLAN
pairs at `baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/`
and its `findings/finding-shared-stage-assembly/` child.

**Mandatory proof:** the assembled lifecycle binds the launched attempt and
durable line/object pin to the real completion and frozen sealed result, records
actual public intake and retention receipts, performs ordinary manager-authorized
cleanup, then reopens the retained manifest and artifact bytes at their recorded
locators and verifies their digests. The same persistent line must reopen with
its durable pin validated after cleanup. Evidence must also show sibling custody
remained outside every writable worker mount. Sibling path inequality, preserved
checkpoint Git references, fixture teardown or canned receipts are insufficient.
The resulting evidence and independent acceptance must be cross-linked here.

**Authority preserved:** W103083 retains its five-path focused-test/fixture
authority; this Work retains its nine-path additive-only scope and serial shared
ownership. Identify any additional path, assertion change or execution scope
before execution for scoped disposition. This claim authorizes documentation
and the single approved dependency correction only, with no implementation or
runtime execution. Reuse accepted configured-access evidence without repeating
its completed campaign. W105982 and W106673 stay open; production confirmed
shutdown and the separate experiment's adoption gate are unchanged.

**Disposition executed:** canonical `unblock work=W103068 on=W105982` committed
remove_dependency111463 after all six decision/plan files were updated and the
scoped whitespace check passed. CLI detail at111463 confirms W103068 still waits
on W103083 and no longer on W105982. Detail at111467 confirms W105982 and its
child W106673 remain open. No application/test source, runtime or Git state was
changed by this claim; the residual proof remains outstanding.

## 2026-09-08 — the remaining retained-result check is complete, W119114 claim119398

`review-2026-09-07T15-46-38Z.md` named exactly one acceptance still missing from
the referenced runtime evidence, and carried it into W103083's actual lifecycle
proof: retain the actual sealed result outside the writer mount, perform ordinary
manager cleanup, then reopen and verify those same artifact bytes and the
persistent line.

**Confirmed complete**, over the real composed deployment rather than a fixture's
arrangement of it. Owning record:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/`
— see its FINDING entry of this date, `evidence/implementation-119398/EXECUTION.md`,
and the cases `TheRetainedResultReopensAfterOrdinaryCleanup` and
`TheComposedImplementationHalfRunsOnOrdinaryTicks` in
`v12/python/tests/tools/test_stage_execution.py`.

What was actually exercised, in the order the review required:

- one real worker turn wrote and committed the private line; `request_freeze`
  sealed its result and `request_intake` recorded a real receipt whose one
  artifact carries a `custody_locator` under
  `<storage>/.baton-review-lines/<line>/custody/<attempt>/`;
- `decide_retention` recorded `retain` under the configured policy digest;
- `authorize_cleanup` ran as the ordinary manager-authorized cleanup and SETTLED
  — `cleanup = retained`, which is terminal, with `execution_runtime =
  destroyed` from a positive absence observation of the exact runtime. Not
  `failed`, which is what a fixture that never modelled removal reaches, and not
  a teardown;
- **after** that cleanup, the retained artifact bytes were reopened at their own
  recorded locator and measured: the tree digest equals the digest the intake
  receipt carries. The retained result manifest was reopened through
  `load_manifest` and names the same artifact identity and digest;
- the custody tree was compared against `roots['workspace']` — the directory this
  attempt's container really had writable, which under this profile is the line
  checkout itself — and lies outside it, as the line's own sibling;
- the line survives at `review-ready` revision 1 and its checkpoint pin
  REVALIDATES through the accepted profile against the real repository.

This is the bytes-level check the review asked for. No pathname assertion,
surviving reference, fixture teardown or canned receipt stands in for any of it;
the only deterministic seams are the engine callable and the injected provider,
both named explicitly in that record's EXECUTION.md.

This entry closes the one carried acceptance obligation recorded above. It does
not close W119548's separate scope, W106673, or anything else open in this
record; the composed lifecycle beyond the implementation ending remains blocked
on `baton:work/records/2026/09/finding-v12-quiescence-gate-discharge/` and is
still owed by W119114. Recorded by baton.claude under claim119398; no source,
existing test, runtime or Git state in this record's own scope was changed.
