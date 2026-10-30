# W358969 — manager-owned fresh-attempt admission

## 2026-10-23 — selected scope and decomposition, reviewer claim358954

**Confirmed authority.** Owner's “redirects retry work to the manager now” ruling
in `../finding-v12-native-pilot-instance-packet/FINDING.md` and normative
`v12/DESIGN.md` REC-7 supersede finishing the W325959 retry helper. This Work is
a bounded child of W321608. W325959 consumes its independently accepted delivery
before preparing any selected pilot retry. V11 remains coordination authority.

**Outcome.** One supported deterministic manager operation, exposed through the
existing `baton-v12-stack` command surface, admits a fresh execution from a
retained failed Job/attempt without a model writing a packet. A new Job identity
is permitted. Preserve selected task/specification, resolved limits, installed
configuration and prior failure/evidence linkage. Work identity policy and exact
syntax are implementation choices within existing authorization contracts; the
pilot's proposed quickstart-d/W2 names are not requirements.

**Confirmed baseline (source inspection, not a new runtime proof).**

- `v12/python/src/baton_v12/job_manager/submission.py:37` already journals
  normalized submission intent; `_unclaimed` at line76 checks Job uniqueness
  inside the owning transaction before inserts. Reuse these guarantees rather
  than claim uniqueness is wholly absent or build a CLI-side substitute.
- `v12/python/tools/job_manager.py:749` submits a supplied document; its parser
  at line1112 exposes submit/status/serve. No general fresh-attempt operation is
  exposed here. `tools/stack_command.py:80,255` is the installed manager dispatch.
- `job_manager/episodes.py:1057` restarts explicitly abandoned corrections using
  committed fence, restored-line and excluded-writer evidence. An expired OAuth
  failure is not authority to fabricate those receipts or call it recovery.
- `tools/stage_execution.py:5415,5447` enforces Work/input/policy/role compatibility
  and implementation producer affinity. A new Job name alone cannot make a
  fresh binding selectable. Both implementation and independent review must work;
  preserve the old bindings and evidence.
- The superseded helper checkpoint is
  `../finding-v12-native-pilot-instance-packet/fresh-attempt-358697/CHECKPOINT-358915.md`.
  Reviewer independently confirms current helper SHA256
  `15dd4b084e96bb40dc71b4c9c53b03a7d17da775be58d729b38262079ebdb919`, different from
  reviewed `64d4442c...`. Old proof does not certify these bytes. No helper run is
  part of this Work's baseline.

**Operational inputs, not additional generic projects.** The old helper could
not obtain supported Work-collision and fresh runtime-exclusion facts through
its CLI projections. Address exactly the facts this operation needs through the
owning authority/control APIs. A general-purpose inspection framework is not
required. Do not copy/read live stores directly, invent a snapshot protocol, or
treat a recent status timestamp, dead supervisor PID, failed provider, expired
credential or caller boolean as proof of physical cessation.

## Acceptance boundary

1. Manager owns atomic Job identity reservation/validation, immutable request
   signature, replay and binding consistency. Same operation/same operands
   returns the recorded result without duplicate admissions/effects; changed
   operands refuse. Competing requests for one identity cannot both win.
2. Compose Work authorization and host resource/runtime exclusion through their
   owning APIs. Durable intent and explicit incomplete/held outcomes bridge
   stores; no cross-store atomicity claim, external I/O or other-store access
   inside a DB transaction. Recheck relevant versions/reservations before
   conflicting effects. Unknown prior launch/runtime or stale authorization
   refuses or holds safely; a new Job identity is no bypass.
3. Preserve prior failed Job/attempt/output and readable provenance linkage.
   Reuse installed configuration and selected task/source/constraints and
   resolved per-invocation limits (pilot 3600s provider, 900s verification).
   Bind the actual new attempt/Work/manifests consistently and prove both stage
   selectors and ordinary independent-review behavior. Do not repoint old
   workers/configuration in a way that invalidates retained Jobs.
4. CLI delegates to that operation and reports exact outcome, identities and
   actionable refusal/hold. It must not become a second admission implementation.
   No per-retry installation, hand-built script or live database inspection.
   Current credential resolution occurs at the existing launch boundary; no
   credentials in retry operands, saved documents, logs or evidence.
5. Deterministic tests use real disposable owner stores/APIs and controlled
   engine/provider boundaries. Cover successful failed-attempt replacement,
   direct manager invocation (bypassing CLI), concurrency, exact replay after
   restart/lost reply, changed operands, collisions, partial cross-store cuts,
   active/unknown/stale runtime and authorization, wrong Work/input/configuration,
   unchanged prior history and both stage bindings. Record actual exercised cuts
   and limitations; fake engine/provider evidence is not live authentication.

## Decomposition and ownership

The manager operation, owner-API composition and thin CLI stay together: only
their connected behavior establishes the selected retry outcome. Splitting them
into another speculative interface handoff would not independently unblock the
pilot. General new-Job creation and reusable versioned templates are separately
selected follow-on outcomes under W321608, not prerequisites for this slice or
new W325959 pilot gates. Align their approved requirements in DESIGN before
dependent implementation; no general framework is selected here.

Implementation goes to `baton.impl` after scope and the W325959 dependency are
recorded. That handler owns its candidate, tests and this record's PROGRESS;
reviewer owns FINDING, PLAN and append-only reviews. Use an isolated candidate
root under this dossier for product edits and record exact base/digests, avoiding
existing working-tree changes. These code locations are evidence, not a files-to-
edit restriction. The implementer selects necessary files, records actual paths
and coordinates any overlap before serial integration. No other candidate may
be overwritten. Do not modify the superseded helper or its historical manifests.

W325959 reviewer is the joined pilot consumer; W321608 retains native-workflow
acceptance. Independent exact-byte review precedes human integration and any
separately selected deployment/live execution. Ordinary direct deterministic
development is authorized by AGENTS; no live provider, engine operation against
retained instances, install, credential read or Git mutation is selected here.

**Open implementation questions.** Choose the minimum supported request/result
contract, durable retry intent and compatible binding composition using existing
owner APIs. Show recovery at each actual effect cut. Report a concrete missing
product decision rather than silently changing REC-7; routine implementation
choices do not require another planning approval.

## 2026-10-23T21:38:33Z — candidate358995 changes requested

Independent review claim359263 confirms manifest88a1ef8c and all11 member pins,
with all8 existing base paths matching current canonical bytes. Four concrete
defects prevent acceptance: real bootstrap binding rejects job_work_id; racing
requests admit two successors of one failure; serving checks fabricated worker-
derived Job inputs; changed partial operands create Work before collision refusal.
Probe and exact limitations: `evidence/review-359263/PROBE.json` and
`review-2026-10-23T21-38-33Z.md`. Connected authority/host exclusion and binding
publication recovery remain required; no live verification selected.

This supersedes any interpretation of handoff359260 as accepted connected REC-7
delivery. Preserve its useful manager/CLI split, immutable prior-spec copying and
attributed author evidence. Review does not require a new Work or owner decision:
these defects are coupled corrections within the existing bounded outcome.
Return directly to implementation with exact candidate/evidence, then independent
review. W325959 gate and pending human checkpoint remain unchanged.

## 2026-10-23T22:00:41Z — bounded corrections pass, ownership still incomplete

Review claim359420 independently verifies candidate359299 manifest7ee13790 and
all12 member hashes;55 focused tests pass. Previous binding-field, actual-input,
Work-before-reservation defects are corrected, as is the distinct-successor race.
This qualifies the earlier all-four-blockers status without accepting delivery.

New independent two-connection probes show identical retry requests both perform
the binding effect, and ordinary submission can occupy an already-reserved retry
identity. The host exclusion requirement remains unimplemented: coherent read
and warning are not an owned exclusion. Existing instance/lifecycle ownership
APIs are concrete research leads; read-only control access is not a requirement
of this mutating command. Full findings R5–R7, exact evidence and accepted limits:
`review-2026-10-23T22-00-41Z.md`, `evidence/review-359420/PROBE.json`.

Continue one coupled admission/ownership correction through deterministic focused
proof. Reassessed decomposition: shared manager/port execution boundary and
existing ownership mechanisms make another supplier handoff unnecessary now.
No template/framework expansion, new owner gate, deployment or live run selected.
Independent exact-byte acceptance and human checkpoint remain owed.

## 2026-10-23T22:22:03Z — ownership correction remains incomplete

Review claim359576 verifies candidate359459 manifestb99ba986, all13 members
and all10 existing bases. All66 focused cases pass independently. Added guards
and reservation checks improve distinct-holder contention but leave name-based
bypasses: same-incarnation requests both bind, and same-submission-name changed
content takes the reserved Job. A real guard probe proves admission closes an
already-held process guard, allowing a competing process in before its actual
owner releases it. Missing resource-token evidence also still permits admission.
Exact R8–R11 findings, provenance, durations and limits:
`review-2026-10-23T22-22-03Z.md`, `evidence/review-359576/`.

This supersedes the claim359459 handoff's assertion that R5–R7 are fully
corrected. The accepted REC-7 target is unchanged. Continue serial correction
of this single shared admission boundary; the review records the renewed
decomposition assessment and actual ownership. No live run or owner scope gate
is needed. W325959 remains gated and no candidate is accepted for integration.

## 2026-10-23T22:41:20Z — separate submission ownership from host exclusion

Claim359705 verifies candidate359603 manifestad9a63db, all14 members and all11
existing bases. All78 focused tests pass independently. New probes still show
reserved submission ID theft by a different Job, overlapping guard lifetime loss,
and self-validating CLI host identity accepting an unrelated empty store.
Exact R12–R14 findings, evidence and limits are in
`review-2026-10-23T22-41-20Z.md` and `evidence/review-359705/`.
The ordinary non-durable signature-conflict refusal is acceptable because it
avoids poisoning the reserved operation; no extra product decision is needed.

**Decomposition decision within accepted scope:** repeated combined correction
passes now justify two independently reviewable outcomes. This explicitly
supersedes the earlier keep-together decisions. W359718 owns complete submission
identity/intended-document reservation. W359719 owns host identity and guard
lifetime, waiting on W359718. Both are canonical child dossiers under findings/.
W358969 waits on both and consumes the cumulative candidate for joined acceptance;
W325959 still waits on W358969. No partial slice releases the pilot.

Execution stays serial to protect shared candidate/admission/test paths. The
first child derives from preserved candidate359603; the second from the exact
independently accepted first candidate. Claimed implementer owns each child's
new candidate/tests/PROGRESS. Reviewer owns records/reviews/evidence. Neither
child edits parent candidate or canonical product bytes. Human checkpoint and
any separate live/deployment selection remain after joined independent acceptance.

## 2026-10-24 — joined technical acceptance, claim360999

**Confirmed:** both selected child outcomes are closed satisfying. Exact cumulative
candidate360912 manifest164546f94cc88854271d623a149835e1283e76a4f8d9049bdc68a402656ab13f
passes joined CLI/real-owner admission, prior-history/configuration preservation,
both stage selection, reopened completed replay and binding-publication recovery
checks. Review `review-2026-10-24T01-46-13Z.md` records scope, evidence and limits;
the latest159-case independent suite on the same bytes is reused.

**Recovery qualification:** incomplete intent remains owned by its recorded
incarnation and resumes under that identity after acquiring the real execution
lock; a different incarnation refuses safely. Completed admission replays under
a reopened handle with another incarnation. No generic takeover is claimed.

Pass this accepted proposal to owner delivery. Human integration and required
Git checkpoint remain pending; neither candidate acceptance nor this note runs
the pilot, imports bytes, deploys or closes W325959's gate. Suggested checkpoint
message is pinned in PLAN, and the actual human commit must be recorded later.
