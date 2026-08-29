# Compose unsupported-version handshake refusal into runtime cleanup

## Discovery and parent

Discovered while implementing W32382 under
`work/records/2026/08/finding-v12-local-oci-negative-race-endings/`.
The parent requires an execution-time `unsupported-version` refusal to reach
the same exact runtime/provider cleanup crossing as every other ending.

## Confirmed gap

`worker_manager/handshake.py:negotiate` correctly emits the closed pair
`refused/unsupported-version` for a non-ACP certified profile or a wire version
different from the pinned profile. That refusal is not and must not become a
member of the frozen worker-disposition axis
`completed|unable|plan-rejected|cancelled`.

No production owner currently carries a refusal raised after the execution
container exists into assignment fencing/ending, exact runtime reconciliation,
output custody as applicable, force-removal, positive absence, credential and
launch teardown, and retryable cleanup settlement. A test cannot invent that
composition by writing a worker disposition.

## Required boundary

- Keep `unsupported-version` as the handshake refusal's typed identity.
- Define one trusted manager/session operation that receives that exact
  refusal for the exact attempt/session/assignment and orders the applicable
  authority ending before runtime destruction.
- Reuse the existing reconciliation, intake/retention, and cleanup owners;
  duplicate no adapter or provider teardown logic.
- Bind effectively-once identity to the attempt, session, assignment,
  handshake profile/pinned version, and refusal. Exact retry replays; changed
  operands collide.
- Preserve the one-container invariant: a created runtime is attached by exact
  identity, no replacement starts while cleanup is pending or uncertain, and
  sibling attempts/runtimes/roots are untouched.

## Acceptance

- A real Docker execution reaches a genuine `unsupported-version` handshake
  refusal after the container exists.
- The refusal remains `refused/unsupported-version` in returned and durable
  evidence and never writes a worker disposition.
- The exact container is force-removed, exact absence is observed, and every
  delivered credential/launch root is positively settled before cleanup and
  lane reuse.
- Restart/retry after the refusal neither duplicates a runtime nor repeats a
  non-idempotent provider act; uncertainty and identity mismatch fail closed.
- Daemon-free unit tests cover malformed/mismatched session and replay
  operands; the real Docker case fails rather than skips.

## 2026-08-28 — correction revalidation

**Confirmed corrected:** the manager now derives the refusal by negotiating
against the persisted session's own certified profile rather than accepting a
caller-built `ContractRefusal`. The four-part session reference fixes the
attempt/profile source. One operation identity is fixed per session act and
changed answered versions ride the signature and collide.

**Confirmed gap — temporal session provenance:** `_require_session` proves the
four-part row identity but does not prove that the row is in the handshake
phase or still owns the active execution posture. The new operation accepts a
historical `closed`, `unknown`, or otherwise post-handshake session row and can
use a newly supplied mismatching version to cancel the attempt. Define and
enforce the exact session state/slot in which an unsupported-version answer is
valid before any refusal journal or authority mutation.

**Confirmed gap — one profile observation:** refusal derivation calls
`negotiate_acp`, which reads the certified profile, and then separately calls
`certified_agent_session_profile` again to obtain the pinned version for the
signature. Concurrent recertification/withdrawal between those reads can make
the second result absent (an untyped subscript fault) or make the signed
evidence differ from the snapshot that produced the refusal. Derive the
refusal and every signed profile/version fact from one owned certified-profile
observation under the operation's concurrency boundary.

## 2026-08-28 — second correction revalidation

**Confirmed regression — public certification bypass:** exported
`negotiate_acp` now accepts an optional caller-supplied `profile`. When present
it skips `certified_agent_session_profile` and does not own, validate, seal, or
bind that document to `profile_digest`. A caller can therefore negotiate an
uncertified digest under arbitrary supplied bytes. The single-snapshot helper
must be private and accept only the owned result returned by the certification
reader; the public operation must always establish certification itself.

**Confirmed gap — active posture ownership:** the correction checks handshake
state twice but never checks that this epoch still occupies the execution
posture slot. Runtime-absence recovery can release a slot independently of the
session observation axis, leaving a `not-started`/`initializing` row that no
longer represents the live session. State is not occupancy; both must agree
inside the refusal transaction.

**Confirmed gap — replay precedes mutable preconditions:** current session
state and current profile certification are checked before the operation
replay. An exact retry after the session advances or after the profile is
withdrawn therefore refuses instead of replaying the already committed
refusal. The new withdrawal test inspects only the first returned document; it
does not retry after withdrawal. A committed act must replay before today's
mutable state is treated as a new-act precondition.

## 2026-08-28 — public-boundary correction accepted

**Confirmed corrected:** exported `negotiate_acp` again accepts no profile
bytes and always reads the certified profile itself. Snapshot sharing is now a
private `_negotiated_against` helper reached only with the owned profile read
by the two trusted module operations. The P0 certification bypass is closed.

**Still open:** active posture-slot ownership, replay before mutable
session/profile preconditions, the exact cleanup/provider/reuse crossing, and
the production Docker/restart/race matrix remain unchanged.

## 2026-08-28 — slot and replay corrections accepted

**Confirmed corrected:** a new refusal is fixed only when the exact execution
epoch owns the occupied posture slot inside the refusal transaction. A
released slot and a newer epoch both refuse.

**Confirmed corrected:** operation identity/signature are derived from stable
call operands, committed replay runs before mutable session/profile
preconditions, and exact retry survives state advance, slot release, profile
withdrawal, and a newly opened store handle. Changed answered versions still
collide.

**Still open:** the operation remains a private cancellation-order helper. It
does not yet traverse exact force-removal, positive absence, provider
settlement, lane reuse, or the real-engine/race acceptance.

## 2026-08-29 — the ending, composed

**The remaining half is built.** `authorize_refused_session_cleanup` carries a
recorded `unsupported-version` refusal through exact force-removal, positive
absence, credential and launch settlement, `retained`, and lane release in that
order. It takes the four-part session reference rather than an attempt id,
because the refusal is filed under the session act and an attempt may hold more
than one session.

**A third sibling, on M34998/M34999's own rule.** A handshake refusal has no
intake receipt for the same reason a failed start has none, and it is not a
failed start: the container is RUNNING. Three closed member sets mean a caller
holding one authorization cannot spend it on another ending. The removal core
in the adapter is shared rather than written a third time.

**The record names the runtime it authorizes destroying**, and W32648's [P0] is
why: an authorization and a command built from two independently read facts
combine into one act. `_refused_session_record` verifies kind, decodes through
the journal's own reader, owns the document, and compares six members.

**Known duplication, deliberately not merged.** `_settle_recordless_cleanup`
and `_settle_failed_start_cleanup` are one function with two names; merging
them would edit W32648's code while it is out for independent review.

**The typed refusal is still outside the worker-disposition axis**, and the
engine suite proves the freeze door remains shut rather than only proving the
new one opens.

## 2026-08-29 — independent review: the authorizing record's meaning is not checked

**Observed [P1]: a shape-correct record that no longer says
`unsupported-version` still authorizes destruction.**
`_refused_session_record` verifies the journal kind and six identity members,
then digests the whole result and spends that digest on
`destroy_refused_session`. It never verifies the result's own `decision`,
`category`, or `code`, despite the document contract explicitly retaining
those members so a later reader can know what was decided rather than infer it
from the operation name.

The additive
`test_a_record_that_no_longer_says_unsupported_version_authorizes_nothing`
keeps the exact member set and every compared runtime/session identity, changes
only `decision` to `accepted`, and expects an `integrity/schema` refusal before
the custodian. The submitted code calls the custodian and settles cleanup.

**Confirmed correction boundary:** at the receiving authorization boundary,
prove the committed body still carries the closed
`unsupported-version`/`refused`/`unsupported-version` meaning before reducing
it to a digest. Also own the pinned/answered version relation and the persisted
session profile it claims, because those are the remaining facts that make the
record a genuine unsupported-version verdict rather than merely the right
shape at the right identity. Preserve exact retry after profile withdrawal by
validating retained evidence, not by requiring a fresh certification lookup.

**Observed [P2]: the deliberately duplicated settlement owner is now stale.**
The implementation record says `_settle_recordless_cleanup` was copied because
W32648 was still under review and should be merged once W32648 closed. W32648
closed satisfying at seq 36991, before this implementation round claimed
W32576 at seq 37155. The deferral premise was already false. Consolidate the
two byte-identical settlement bodies now so failed-start and refused-session
cleanup cannot acquire different ordering later.

**Accepted in this pass:** the composed ending otherwise preserves the typed
refusal outside worker disposition, uses a session-derived runtime identity,
fences before destruction, shares the adapter removal/provider core, retains
untrusted output, and releases the lane only after positive absence and
provider settlement. The retained Docker transcript supplies the required
non-skipping real-container path; this managed reviewer could not rerun it
because Docker socket access was denied.

## 2026-08-29 — the authorizing record proves its own meaning

**A record that said `accepted` authorized destruction.** The reader proved the
record named this attempt, runtime and session, then digested `decision`,
`category` and `code` without reading them. The closed verdict is now required
as a triple before the authorization digest is computed, and the recorded wire
versions must still be integers that disagree — a pair that agrees describes a
negotiation that succeeded.

**The profile is compared against the persisted session row, not a
certification lookup.** Reading certification at the authorization boundary
would make an exact retry stop replaying the moment a profile was withdrawn,
which is the effectively-once defect this Work corrected once already on the
recording side.

**The two recordless settlement implementations are one.** The deferral this
record previously stated had already expired when it was written: W32648 closed
satisfying at seq 36991 and this Work was claimed at 37155.

## 2026-08-29 — independent final review

**Confirmed corrected:** the retained authorization now proves the exact
closed verdict, typed unequal wire-version relation and agreement with the
persisted session profile before any custodian call. The reviewer regression
and its category, code, version and profile siblings all refuse corrupted
evidence as `integrity/schema`; withdrawal of the replaceable certification
projection does not invalidate the retained session evidence.

**Confirmed one settlement owner:** failed-start and refused-session cleanup
both call `_settle_recordless_cleanup` with only their lane-release reason as
an operand. The second implementation is gone, and both daemon-free sibling
suites remain green.

**Accepted terminally:** the previously accepted fencing, exact removal,
positive absence, provider settlement, retained-output, replay, lane ordering
and non-skipping Docker evidence remain intact. W32576 satisfies its acceptance
and may close.
