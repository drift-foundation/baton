# Public contract — provider B, owner128669

Current test authority: AGENTS.md#w71830-standing-test-change-authority and the
campaign2026-09-09T16:36Z ruling supersede all additive-only, per-method and
other-test preservation restrictions below for accepted campaign scope. Record
test deltas and independently review required behavior; no per-test approval
gate applies. Public acceptance behavior and the four-path source allocation
remain. B's25s cumulative cap remains; accepted candidate accounting is24.028s
used,0.972s remaining (review-2026-09-09T16-52-52Z.md). Earlier budget/test
amendments below are decision history.

Owner129177 amendment (2026-09-09): the public behavior below is unchanged.
For verification/test scope only, OWNER-DECISION-129125.md's four exact
conversions and mandatory original-admission-test restoration are approved.
The B-only cumulative cap is25s, carrying19.534s used and5.466s remaining;
this supersedes the original20s/additive-only text below only within that
explicit amendment. Every other assertion/setup and path boundary remains.

Pinned by baton.codex under W119114 claim128673, before implementation. Only
W128692's four allocated paths may change. Revalidate A's accepted contract
before editing; do not import a private provider helper or parse its tables.

`restore_abandoned_correction(store, *, attempt_id, generation, retention_policy_digest, profile)`
`abandoned_correction_of(store, *, attempt_id, generation)`

Both are public operations of worker_manager.review_cycles. They select the
attempt's historical writer via the existing owner reader, never by the line's
current pointer alone. The act re-reads A's abandonment_cleanup_of and
abandoned_gate_discharge_of and cross-binds complete attempt/assignment/runtime,
cleanup identity/signature and original generation before any profile write.
Require a declared unfinished correction with a based frozen checkpoint; no
first-writer/base-only recovery is included in this bounded allocation.

Validate the unique old writer, exact line identity/device/inode/profile, its
based checkpoint, the committed changes-requested verdict/handoff provenance
available through existing owners, and absence of another active attachment.
Refuse stale/foreign/uncertain/incomplete evidence before writable exposure.
Preserve the historical abandoned writer as revoked and return the SAME durable
line to correction-ready at its retained checkpoint, not a new checkpoint.

Add `GitCheckpointProfile.restore_checkpoint(repository, evidence)` to the
existing concrete checkpoint profile class. The
profile verifies the retained checkpoint reference/tree before any write;
restores only this nominated private mutable checkout's tracked/untracked
scratch to that exact checkpoint; and returns the same evidence only after
validate(current=True) succeeds. It must preserve Git objects/checkpoint refs,
immutable sibling custody and paths outside the nominated line. Refuse wrong
object/path/profile or unsafe path substitution. It grants no permission to
operate on the shared source checkout or a production target.

Record fixed recovery intent before a profile act and a completed outcome after
validated restoration, with exact replay identities. Retry a partial restore
only under the same owned exclusion and checkpoint; a recorded completed replay
returns history without resetting a later writer's checkout. Failed restoration
must not admit another writer. Concurrent attempts must not create two writers
or restore a checkout after another writer is admitted. Keep existing ordinary
freeze/grant behavior and historical writer readers unchanged.

The completed act/read returns a plain closed document:
- schema: `baton.v12.abandoned-correction/1`;
- operation_id, attempt_id, assignment, runtime_id, retention_policy_digest;
- writer_id, line_id, checkpoint_id, checkpoint_evidence;
- cleanup_operation (A's original identity/signature pair);
- discharge_operation_id (A's committed discharge identity);
- state: `correction-ready`.

The reader returns None when no completed recovery exists; malformed or foreign
records refuse. It verifies the owning journal identity/signature/result and
exact historical records, performs no profile/Authority/runtime act, and remains
readable after later line/writer advancement. It does not claim the CURRENT
line is correction-ready simply because that historical operation completed.
The next consumer must check its own live episode and admissibility.

Add focused proof for dirty scratch -> exact retained checkpoint, pin/custody
preservation, positive exclusion before first write, wrong-generation/runtime/
checkpoint/line refusal, failed/interrupted restore, completed replay after a
later writer, and concurrent duplicate recovery. Use real disposable profile
fixtures; preserve all existing test assertions. Enforce20s cumulative per
provider with exact commands/logs/wall times. Hand accepted bytes and schema to C.
