# Proposed kernel proof — corrected runner, not executed or selected

Question unchanged: does the selected engine/image topology prevent same-UID mount
root rename/removal/link substitution while ordinary descendants/nested adapter
paths work, and does exact-container teardown stop detached descendants? Simulated
composition is not kernel evidence. No provider/model or credentials needed.

After independent implementation review and image construction, copy
ENGINE-SELECTION.template.json to a new selection file. Fill the exact reviewed
image digest and trusted execution UID/GID from that reviewed deployment, not host
getuid/getgid. Keep the pinned layout/payload/runner SHA256 and new proof_id. Review
and select the complete resulting document and its SHA256 before executing:

    python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-325908/engine-proof.py --selection <reviewed-selection.json> --selection-sha256 <reviewed-document-sha256> --execute-reviewed

Template is deliberately invalid (no image/UID/GID selected). Digest and closed
shape validation occurs before engine operations; root/bool/invalid identities and
mismatched layout/payload/runner refuse. Nothing infers identity from ambient host
UID/GID. Image digest must bind the new image scaffold and worker bytes through the
reviewed image workflow; the authoring image is not accepted correction proof.

Runner creates ENGINE-RECEIPT exclusively before its first engine call. state.json
is written through fsync plus atomic replacement and directory fsync. Creation
intent/name are durable before create; acquired exact ID is durable before the next
engine operation. Each operation records its phase, timeout, status or exception.
No raw Docker diagnostics or provider output are copied to the receipt. A lost
create reply reconciles only the reserved name and exact image/proof-label/UID:GID;
ambiguous inspection never authorizes deletion. An absent observation after a lost
create response is still creation uncertainty, since creation may complete later.

Removal exceptions cannot skip the final inspection and failure record. Invalid/
unknown inspection responses remain uncertain, never absence. Only an exact-scoped
No-such response supplies absence. Failure retains exact ID or creation name and
uncertainty. A filesystem failure can prevent a new receipt update; the already
fsynced reservation/intent/identity remains the recovery checkpoint. Never claim
this mechanism survives unavailable storage or arbitrary host process termination.

Any existing ENGINE-RECEIPT prevents a rerun, even if its state is incomplete or the
object was removed. Recover that exact object separately under recorded authority;
do not delete the receipt or choose a new proof_id to replay a spent selection.
No recovery operation is automatically launched by this packet.

Internal total deadline120s, with40s reserved for cleanup and80s work admission.
Every call is bounded by min(per-call cap, phase deadline remaining). Receipt has
its own20s monotonic window, not40 potentially slow polls. Cleanup reconciliation
uses at most5s, removal at most25s while retaining10s for exact absence inspection.
Record elapsed, timeout phase and exhausted phase; no sleeps beyond remaining
receipt time. An optional external guard should exceed the internal120s plus small
receipt-write allowance (e.g.150s), never interrupt the intended cleanup reserve.
Subprocess timeout kills/reaps the local CLI; a timed-out create may still have
side effects, which is why its intent remains durable and uncertainty is explicit.

One object, no pull, network none, read-only root, cap-drop ALL, no-new-privileges,
explicit reviewed nonroot UID/GID,64 process cap,1CPU,2GiB memory. Payload runs through
python entrypoint, never provider entrypoint. No host/credential/authority/socket
mounts. Actual mount sizes/modes are from LAYOUT.json. Unrelated16MiB legacy-log
decoy is omitted in this no-log diagnostic; product still accounts it separately.

kernel-payload.py tests mount-root refusal/identity, ordinary child/grandchild,
exact image nested validator and a detached sleeper. Successful payload leaves the
container alive so exact teardown/absence, not leader wait, establishes cessation.
This is mechanism evidence only: product missing/false mount/identity/start/timeout
refusal, capacity fit, candidate/input preservation and safe-output tests remain.
Existing W321528186 evidence is preserved and must later be joined on accepted
source in the corrected worker environment, not relabeled by this standalone proof.

RUNNER-CHECK.json and test_engine_proof.py cover deterministic no-engine faults:
create reply loss/unobserved creation, start/log errors, rm timeout/OSError,
unknown/invalid inspection, invalid JSON, identity mismatch, malformed receipt,
slow/non-returning logs, success, no-retry reservation and selection mismatches.
All tests replace the engine and clock; no real sleeps or Docker invocation.
