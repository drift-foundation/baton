# Finding: manager intake, retention and cleanup

Canonical Baton Work: W6629, a separately scheduled M2 manager prerequisite
from the closed W4 and W5 PLAN item 8. Dossier created 2026-08-24 by
`baton.claude` on claiming, because the assignment requires one before
implementation.

## Confirmed boundary

Python manager intake, retention and cleanup state and operations **over
already-sealed artifacts and already-certified runtime observations**:
effectively-once durable identities, recoverable cancellation material,
retention policy, cleanup authorization, positive absence, and restart/retry
ordering.

**Not here:** collecting OCI files, issuing engine commands, defining
credential or redaction policy, running provider code, or inferring truth from
diagnostics.

## Revalidated against the current tree — and the sharpest finding is an absence

**The cleanup axis is frozen and already pinned.** `cleanup` is `pending,
blocked-on-intake, complete, retained, failed`, and W4's `TRANSITIONS` already
carries the moves: `pending → blocked-on-intake | complete | retained | failed`,
`blocked-on-intake → complete | retained | failed`, and `complete`, `retained`
and `failed` all terminal.

Two things that axis already decides:

1. **`blocked-on-intake` is a first-class cleanup state.** Cleanup explicitly
   waits on intake rather than racing it, and the contract says so — an
   implementation that treated "intake not done" as a retry loop would be
   inventing a mechanism the axis already has.
2. **`retained` is terminal and is not `complete`.** Material kept on purpose
   and material cleaned up are different endings, and a cleanup that reported
   retention as completion would erase the reason the material still exists.

**THE ABSENCE, which is the finding this Job most needs recorded.** The frozen
worker-control schema has **no `$defs` for intake, retention or cleanup at
all** — no `retentionPolicy`, no `intakeRecord`, nothing. `retention` occurs
seven times and `intake` four, and every one of those is a *reference*:
`retention_policy_digest` is a `digest` of a policy document whose **shape the
frozen contract never states**.

So "retention policy" in this assignment names something that does not exist as
a contract. Implementing it means either:

- consuming a retention policy shape that some other Work owns — in which case
  that Work must be named and this one must wait for it; or
- **inventing** the policy document here, which is the trap W6634 was blocked
  on and which this Job's own instruction ("must not reconstruct any of them")
  forbids by implication.

I am not resolving that by choosing. It is a question for the route handler and
it is recorded here so the next implementer meets it before writing code rather
than after.

## Dependencies

**W6629 → W6627, W6628, W6630.** Intake, retention and cleanup consume
certified runtime observations (W6627), sealed-artifact acceptance (W6628) and
§13 policy (W6630), and must not reconstruct any of them. All three are open;
W6627 and W6628 are themselves blocked on W6592.

## Acceptance

- Effectively-once durable identities through W4's existing journal.
- Recoverable cancellation material, distinguishable from material retained by
  policy.
- Cleanup authorization, with `blocked-on-intake` used as the state it is.
- `retained` and `complete` never conflated.
- Positive absence, and restart/retry ordering preserved.
- **Retention policy consumed from a named owner, not invented here.**

The implementer creates and exclusively owns `PROGRESS.md`.

## SUPERSEDED — the retention-policy ownership question, 2026-08-26

The revalidation recorded on 2026-08-24 said:

> So "retention policy" in this assignment names something that does not exist
> as a contract. Implementing it means either consuming a retention policy
> shape that some other Work owns [...] or **inventing** the policy document
> here.

**The premise is right and the conclusion was wrong**, and the correction came
from counting rather than from reasoning. `retention_policy_digest` is one of
**ten** `*_policy_digest` members of the assignment manifest — `policy`,
`toolchain`, `resource`, `network`, `mount`, `tool`, `credential`,
`runtime_profile`, `worker_image` and `retention` — and the frozen schema
states the shape of **not one of them**. A probe over the whole `$defs` set
finds zero policy-document definitions.

So the absence is not about retention. It is how this contract treats policy
documents **uniformly**: a manager binds a policy by IDENTITY and acts on the
operation that cites it. **Interpreting one here would be the boundary
violation, not the fix.** There is no third Work to name and nothing to wait
for, and the dilemma dissolves rather than being resolved by choosing.

The old text is kept because the thing it got right is the instructive part: it
refused to invent a contract. What it missed is that consuming a digest IS
consuming the policy, and that "consume" never meant "read".

## Implementation decision — 2026-08-26: consumed by digest, produced by
construction

**The retention policy is CONSUMED**, so it is bound by digest and never
opened. `decide_retention` records which artifacts, which disposition and
under which policy; `authorize_cleanup` requires the digest the destroy cites
to be the one every decision was made under. Both are identity questions, which
is all a digest allows and all this needs.

**The intake receipt is PRODUCED here**, so its shape is this module's to
write down. The frozen contract names `intake_receipt_digest` in
`runtimeDestroyBody` and states no shape for what it digests — the same
silence, read from the other end. A producer owns the shape of what it
produces, and the receipt is recomputed from its own document on every read so
an edited row cannot authorize a destroy.

## Implementation decision — 2026-08-26: where `sealed` came from

W6628 ends at `frozen` and says so in its own module docstring: "FREEZING IS
NOT ACCEPTING [...] this module ends at `frozen` and never writes `sealed`",
and it lists "retention and cleanup, and the `sealed` transition itself" among
what is not there. **Intake is the act of accepting**, so `frozen -> sealed` is
this slice's, and the receipt is the record of it.

**Quarantined material is sealed too.** W6628 also pinned the reason: its
liveness read "is inside the write and is still only a read", so the window
cannot be zero, and "material from an assignment that ended anyway is
QUARANTINED AT INTAKE rather than trusted here". Refusing would destroy the
evidence of what a worker produced because its assignment ended while it was
being collected; leaving it unsealed would invite a second collection of bytes
already taken.

## Implementation decision — 2026-08-26: the frozen axis says one thing this
slice cannot work around

`uncertain` may never become `destroyed`, on the axis's own stated reasoning.
So an attempt whose `execution_runtime` is `uncertain` **cannot have its
cleanup settled**, even when the engine answers positive absence, until
reconciliation returns the axis to a positive observation. That is refused with
the reason stated rather than reached by writing the terminal value some other
way. It is a consequence of the frozen contract and not a choice made here, and
it is recorded because a later reader will meet it and wonder.

## Independent implementation review — 2026-08-26 (baton.codex)

**Changes requested.** The retained 52-case focused baseline is green, but six
additive review cases expose four P1 contract boundaries.

**STILL LIVE IS NOT OVER was dropped in the Python delivery.** W4 already
decided that runtime destruction waits until the fixed assignment is ended or
fenced. `authorize_cleanup` verifies only that the calling participant matches
the fixed assignment, then destroys while the authority still returns that
exact assignment as live. This tears out a worker that remains authorized to
execute.

**TWO PROTOCOL COMMANDS DO NOT CROSS THE ADAPTER BOUNDARY.**
`decide_retention` requires an adapter `retain` capability but never calls it;
it journals only the manager's local retention row. `_destroyed` calls
`adapter.destroy` with a bare runtime id. The frozen `outputRetainBody` and
`runtimeDestroyBody` carry the assignment, attempt and authorizing material,
and the effectively-once operation must travel beside that body. A capability
checked but unused is not a command, while a bare runtime id omits both digests
that authorize destruction.

**ONE POLICY IS NOT ONE RETENTION ACT.** `retain_operation` derives identity
from the attempt and policy digest alone even though `outputRetainBody` makes
the artifact set and disposition part of the command. Consequently a policy
cannot retain one artifact and discard another: the second valid command
collides with the first instead of committing its own decision.

**A SELF-HASH IS NOT INDEPENDENT EVIDENCE.** `intake_receipt_of` accepts a
receipt row when its recomputed digest matches the digest stored beside it, so
editing both together creates a trusted cleanup receipt. `retentions_of`
authenticates no row against its recorded `output.retain` operation at all, so
editing the policy and disposition creates destroy authorization. This
regresses the predecessor W4 sign-off that every loaded intake decision is
authenticated by the committed operation signature; the same rule necessarily
applies to the retention rows that now authorize destruction.

The first five additive cases run against the retained baseline as 52 passes,
four failures and one error. A sixth case pins the same-policy/multiple-artifact
identity boundary. Before it could be collected, a concurrent edit to the
Python schema snapshot made the unchanged published input vector fail during
shared fixture setup; that separate interference is recorded in the review
evidence rather than attributed to W6629. Exact correction boundaries and
verification are in `review-2026-08-26T07-35-43Z.md` and
`evidence/review-2026-08-26T07-35-43Z.txt`.

### Review verification addendum — 2026-08-26

The last paragraph above is superseded as a verification status, not as an
operational observation. The concurrent schema snapshot became coherent again
during this review. All six additive cases then collected in the complete
focused module: 52 retained passes, four failures and two errors, 58 total.
The second error is the predicted same-policy/multiple-artifact operation
collision. The stable final count is recorded in the same review and evidence
files as an append-only addendum.

## Independent correction re-review — 2026-08-26

**Confirmed corrected.** The correction delivers the complete retain and
destroy commands through the adapter, keeps exact replay above the live
assignment gate, includes the artifact set and disposition in retention
operation identity, and authenticates receipt and retention rows against the
committed journal. The two review assertions changed from checking refusal
`code` to checking refusal `category` are explicitly approved: the closed
pairing puts `integrity` in the category field, so the original assertions
were unsatisfiable review mistakes rather than product requirements.

**Confirmed P1.** The new retention authentication rejects a legitimate
partial policy replacement. `_retain` intentionally keeps one current row per
artifact and lets a later policy replace one member of a previously grouped
decision. `retentions_of` instead groups only the rows that remain current by
their original operation id and reconstructs the original whole command from
that now-incomplete group. Replacing artifact B leaves artifact A naming the
original A+B act, but the reader derives an A-only act and reports an
integrity failure. This can strand otherwise authorized retention and cleanup
after ordinary policy evolution.

Authenticate each surviving current row as a member of the committed
`output.retain` result named by its stored operation id. The committed result
must still name that artifact and carry the row's disposition and policy; the
reader must not require every artifact from the historical command to remain
current forever. The additive regression and full correction boundary are in
`review-2026-08-26T09-13-46Z.md` and
`evidence/review-round-3-2026-08-26.txt`.

## Independent correction re-review, round 4 — 2026-08-26

**Confirmed corrected.** Per-row authentication now permits a legitimate
partial policy replacement and continues to reject an edited disposition or
policy. The focused module is 59/59 before this round's additive case.

**Confirmed P1.** The committed membership comparison omits the attempt
identity. Artifact ids, retention policy digests and dispositions are not
globally unique, so a retention row for attempt A can be edited to name an
authentic `output.retain` operation committed for attempt B. If that act also
includes the same artifact under the same policy and disposition,
`retentions_of` accepts it as authorization for A. The committed result already
carries `attempt_id`; the reader must require it to equal the attempt whose row
is being authenticated.

The additive cross-attempt regression and correction boundary are recorded in
`review-2026-08-26T10-04-44Z.md` and
`evidence/review-round-4-2026-08-26.txt`.

## Independent final re-review — 2026-08-26

**Confirmed corrected:** each surviving retention row is authenticated against
the committed `output.retain` result it names, and that result must name the
same attempt before artifact, disposition and policy membership can authorize
the row. A row can no longer borrow another attempt's authentic act, while a
later policy may still replace one member of a historical grouped decision.
Forged disposition/policy rows continue to fail closed.

**Confirmed:** the complete focused module passes 60/60. The manager
secret/dependency/text-sweep slice passes 114 tests with one expected skip,
and `git diff --check` is clean. Independent source review found no remaining
intake, retention or cleanup contract issue.

Final review and evidence are recorded in
`review-2026-08-26T12-28-42Z.md` and
`evidence/review-final-2026-08-26T12-28-42Z.txt`.
