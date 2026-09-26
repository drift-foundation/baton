# Baton v12 normative design

Canonical Work: W274875. Author: baton.prompt. Created 2026-09-26.

## 2026-09-26 — Owner selects one normative v12 specification

**Confirmed.** Slawomir requests `v12/DESIGN.md` as the specification and map
that development follows, covering the whole v12 system: agents, Docker,
database use, host manager, inside-container manager, exclusive expiring
tokens, recovery, context reuse, artifacts, review and delivery. This is a
target specification, not an inventory of current implementation or an
ARCHITECTURE.md describing existing code. It specifies **v12**, not the v11
deployment currently coordinating development.

The prompt participant authors the document from confirmed decisions and asks
the owner about unresolved requirements rather than guessing. Claude then
reviews the exact document and records signoff or concrete required changes.
No implementation, runtime launch, tests, deployment or Git mutation is selected
by this documentation assignment.

**Confirmed.** The token-baton safety rule is exclusive, expiring permission
acquired atomically under a short database transaction. External I/O happens
after transaction exit. Expiry revokes permission and requires termination of
the exact associated Docker execution, with positive evidence that its writers
are stopped, before reset or reassignment. Expiry alone cannot prove an old
writer has stopped. Database/library-internal I/O is outside the owner's
external-I/O prohibition.

Exact preceding ruling:
[owner token decision](../finding-v12-workspace-removal-outside-locks/OWNER-TOKEN-BATON-20260926.md).

**Confirmed.** The next W270664 review returns that Work to `baton.decide` for
owner alignment with the specification, preserving its candidate and evidence.
It must not automatically begin another implementation correction. This is a
specific sequencing override, not a declaration of acceptance or a takeover of
the current claim. Recorded on T270664 as message 274873; reviewer notified by
poke 274874.

## Ownership and acceptance

`baton.prompt` owns `v12/DESIGN.md` and this record's FINDING/PLAN during drafting.
The W270664 implementation paths and its author-owned progress remain with their
existing owners. Claude's review owns a new append-only review in this record;
the handoff will pin the document digest and exact review scope.

Acceptance requires an internally coherent v12 specification grounded in owner
decisions; explicit treatment of unresolved decisions; clear distinction between
requirements and implementation evidence; and Claude's review of the final exact
bytes. Existing code is evidence of gaps, not authority to weaken requirements.

## 2026-09-26 — Draft and explicit unresolved decisions

Prompt wrote the first consolidated `v12/DESIGN.md`: 20 sections covering v12
responsibilities, identity, database use, token lifecycle and Docker enforcement,
both managers, artifacts, context reuse, scheduling, review, recovery, security,
limits, operator visibility, deployment, conformance and decision provenance.
Older source records were checked for superseding decisions rather than copied
as a retrospective architecture. No product tests were run.

Two actual choices have been asked of the owner and remain unanswered here:

1. Must maintenance mutations of workspace/context/output (including reset and
   deletion) also run in token-bound containers, or may host helpers use a
   separately specified enforceable termination boundary?
2. May the trusted host explicitly renew an unexpired token for the same execution,
   or does each token have a fixed lifetime? Neither permits revival after expiry.

The draft marks these as unresolved and forbids choosing by inference. Claude may
review the settled requirements now; final whole-document signoff must wait for
these decisions and review the final exact bytes.

W270664 reviewer returned the Work to `baton.decide` at event274959, as requested.
The first token slice is NOT accepted: review found old-generation cessation
releasing a newer active token, late binding after revocation/succession, and a
string `false` treated as positive cessation. Real adapter wiring and broader F2
scope remain absent. The spec now explicitly requires generation-bound typed
cessation evidence; no product changes were made by prompt.

Operational read note: the guessed path
`work/records/2026/09/finding-v12-source-boundary/FINDING.md` does not exist.
The actual source/workspace owner record under
`finding-v12-standalone-multi-job-pipeline/findings/finding-source-workspace-mounts/`
was located and read. No required source remains unavailable from that lookup.

## 2026-09-26T11:57Z — Owner resolves placement and renewal; final review selected

**Confirmed.** Slawomir says "i agree with your recommendation", referring to
the prompt recommendation to run governed resource mutations, including deletion
and reset, in token-bound containers; let the trusted host grant tokens, enforce
deadlines and stop containers; and permit explicit renewal only before expiry.
Expired tokens require shutdown and positive cessation before replacement.

This explicitly supersedes the two unanswered choices above and section19 of
the first DESIGN candidate. Host filesystem helpers are not selected as an
alternative enforcement boundary for governed workspace/context/output/custody
mutations. Maintenance executors, including reset after another execution stops,
are themselves token-bound Docker executions. This is product direction, not
authorization to run containers, change product code or resume W270664.

Claude's first review returned at275003 without whole-document signoff:
`review-2026-09-26T11-52-40Z.md`. It requires clarification of custody-owner
responsibility versus writer placement, token-bound reset, and holder versus
deadline authority. Prompt will resolve all three against the selected model:
the host owns grant/renewal/revocation and trusted time; the container execution
holds the resource permission, usable by its inside manager and descendants,
without minting tokens or using its clock to extend permission. Resource file
mutations are performed by the exact maintenance execution, not by an unfenced
host helper. Host DB/control metadata and Docker supervision remain host duties;
their ownership must not be used to disguise resource mutations as metadata.

Renewal must compare the exact still-live generation/execution and deadline
revision, commit a new bounded deadline, and record the act. Heartbeats and lost
replies cannot imply renewal; replay cannot extend twice; stale expiry observations
cannot revoke a newer renewed deadline. Once expiry or revocation wins, renewal
refuses and the old execution must stop. No numerical duration is selected here.

**Ownership update.** Prompt continues to own DESIGN/FINDING/PLAN and adds only
a narrow `AGENTS.md` v12-spec pointer and `v12/README.md` scope/link clarification
so future work finds the specification. Existing policy and historical proof
instructions are preserved. Claude reviews all three final document paths and
owns only a new append-only review. No source, tests, Git or live execution.

### Response to Claude's first review

1. **TOK-7 versus ART-7/ART-9:** responsibility is now separated from placement.
   The host authorizes and records trusted settlement; a token-bound maintenance
   execution performs governed custody writes/deletion. Storage outside the
   producer's writable mounts does not intrinsically require an unfenced host
   writer. Protected control metadata and engine supervision are explicitly
   distinguished from resource content, with no resource-mutation loophole.
2. **Maintenance/reset scope:** TOK-7 enumerates allocation/staging, normalization,
   freeze/retention, deletion/reset; TOK-12 requires a new scoped maintenance token
   after old-writer cessation, preserving ordinary-use gates until reset settles.
   HOST-1 serializes preparation and task tokens. Section19 states the actual
   implementation consequence, while Docker supervision remains host-controlled.
3. **Holder and clock:** TOK-2 names the container execution as holder and the
   inside manager as a user of that permission; TOK-9 assigns authoritative expiry
   and conditional renewal to the trusted host. RUN-5 does not turn renewal
   requests, local clocks or heartbeat reports into grants. Focused renewal and
   maintenance conformance cases are added to section17.

No unresolved product choice from the first review remains intentionally open.
Concrete timing/schema/profile values still require bounded implementation
selection, not invented numbers in the central specification. Full signoff
remains a new independent review of the revised bytes, not a claim by the author.

## 2026-09-26T12:05Z — Claude signs the exact revised specification

Claude claim275064 returned W274875 to `baton.decide` at275082 with full
specification signoff in `review-2026-09-26T12-04-10Z.md`, SHA256
`31b4cf63702b5143219b8dc9942e842fec74c58c0db8a8355e5e22ffdef671ec`.
The review resolves all three original findings and signs these exact files:

- DESIGN: `baee80a35a9260ac9bd557aad8beb8fcb8ed44908b3f6e01e7f999fb22cfb1a8`, 56163 bytes.
- AGENTS: `e6183efeaf5bf8045affe91bd983eff1e98c874334058bdb9fda0b56e080b2a6`, 36742 bytes.
- v12 README: `87579686ae983818370866669c54f5ef44f45acd1c719208498663c3e09555ae`, 20289 bytes.

Prompt independently re-measured these after return; all match. The three
signed documents remain unchanged. This accepts the specification and discovery
pointers only; no existing code conformance, runtime or deployment is accepted.
W270664 remains unaccepted in owner custody for alignment and bounded selection.

## 2026-09-26 — Owner asks about live-container mount handover; no new selection

Slawomir asks whether the earlier mount-based handover preserving a live Docker
runtime is gone, explicitly saying this is a question rather than a selection
for or against retaining it. No policy or implementation change is inferred.

**Observed:** the current DESIGN requires exact container termination on resource
token expiry. TOK-5 normal return requires exclusion of all effective writable
capabilities but does not specify a live-container detach/reattach protocol.
The document does not explicitly carry that earlier experimental option or its
adoption status. Context reuse and live-process preservation are different facts.

**Confirmed historical evidence:**
`../finding-v12-live-session-workspace-detach/FINDING.md`, approved experiment and
mandatory handoff gate of September7, selects verified workspace revocation in
the writer's namespace while preserving the process/session, with confirmed
shutdown on busy/failed/uncertain detach. The 06:25:36Z independent review accepted
actual Claude process/session/workspace continuity across detach, consumption,
reattach and useful correction. It explicitly did not claim production adoption.
The later production custody plan and context-reuse design continue to record
confirmed shutdown as the production path and detach as unadopted. Separate
restoration evidence proves a new process using the prior session/workspace.

**Clarification:** mandatory termination on expiry does not logically require
termination on every cooperative normal handover. A verified detach path could
be selected for normal return while expiry still terminates the execution. The
current central specification does not spell out that path; the owner has not
selected its adoption or removal by asking this question. Keep the accepted
experiment/evidence intact and distinguish the omission from technical failure.

## 2026-09-26 — Owner selects shutdown on normal handoff for v12

**Confirmed.** After asking whether shutdown would simplify v12, Slawomir
accepts the recommendation with "I agree, proceed". V12 MUST positively confirm
termination of the exact outgoing container before resource ownership is handed
to another execution, including normal implementation/review/correction and
maintenance handoffs. A naturally exited container may satisfy the same exact
termination proof; a completion message, detached mount or sent stop request
cannot. Expiry/revocation retains its mandatory shutdown behavior.

This explicitly supersedes the preceding inquiry-only/no-selection status and
the open interpretation of normal return in DESIGN TOK-5 at digest baee80a3.
It narrows the allowed v12 handoff mechanism to confirmed container termination.
Claude's review-2026-09-26T12-04-10Z.md remains valid historical signoff for its
exact bytes; the changed specification requires a new review/signoff.

Preserve the workspace, retained result and qualified provider conversation
outside the disposable container so a new execution can restore context.
Context reuse remains a v12 requirement; shutdown is not a reason to erase the
context, start fresh silently or relabel failed restoration as reuse. Normal
completion saves required durable state before graceful shutdown; incomplete or
uncertain state remains held/quarantined through existing recovery rules.

This is an ownership-handoff boundary, not a shutdown after every tool call,
database transaction or heartbeat. Explicit renewal can keep the same valid
execution running within its current assignment. Independent Jobs still run in
parallel; all stopping and confirmation I/O remains outside DB transactions.

Live-runtime mount detach/reattach is deferred from the v12 delivery path as a
later optimization. Preserve the successful experiment and its independent
review; it is not disproved or deleted. Reconsider only through a separately
selected change justified by measured handoff benefit and full safety evidence.
The old separately timed retained/restored experiments are not a matched speed
comparison. No new implementation, test, live runtime or Git action is selected.

Prompt owns this bounded specification amendment and its FINDING/PLAN checkpoint.
Claude reviews the changed DESIGN and returns to owner. Existing README/AGENTS
pointers remain applicable. W270664 remains unaccepted at the owner for alignment.

## 2026-09-26T12:19:56Z — Claude signs shutdown-on-handoff amendment

Claude claim275172 returned W274875 to `baton.decide` at275184 with no required
correction. New immutable review: `review-2026-09-26T12-14-30Z.md`, 6750 bytes,
SHA256 `265274512a0ee02d4980a98dee871eb05400aed044fb1513305a843ffb28d6d2`.
It explicitly signs the amendment and whole current specification at DESIGN
`7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0`, 59518 bytes.
AGENTS and v12/README retain the digests from the preceding full signoff. Prompt
re-measured all three documents and the new review after return; all match.

The review checks normal and maintenance handoff cessation, save-before-shutdown
and new-execution restoration, same-assignment renewal, unchanged expiry rules,
and preservation of deferred live-mount experimental evidence. It reads the
amendment and affected surrounding sections, relying on its prior review for
unchanged material; it does not claim to re-derive every unchanged requirement.

The design blocker is cleared. W270664 remains unaccepted and unclaimed at
`baton.decide` for a dedicated alignment selection. Required implementation work
still includes the three independently reproduced token defects, actual controlled
runtime admission/enforcement, governed filesystem effects inside maintenance
containers, confirmed shutdown before normal return, and the outstanding F2
proofs in its latest review. Any wider required change must be identified rather
than silently expanding F2. Specification signoff does not execute or accept that
work. No test, provider, engine, deployment or Git mutation occurred here.
