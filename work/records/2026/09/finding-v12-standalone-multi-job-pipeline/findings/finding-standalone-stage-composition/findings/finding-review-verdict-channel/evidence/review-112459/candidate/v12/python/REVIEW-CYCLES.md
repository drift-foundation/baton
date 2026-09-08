# Persistent review cycles

W71918 adds a Worker Manager custody object above disposable implementation and
review attempts. One development line is keyed by `(authority_uuid, work_id)`
and stored under the workspace store's reserved `.baton-review-lines/`
namespace. An assignment ID cannot select that namespace, and ordinary attempt
cleanup cannot remove it.

The line lifecycle is:

```text
idle -> writing -> freezing -> review-ready -> reviewing
                                                | accepted
                                                | rejected
                                                ` correction-ready -> writing
```

Every writer and reviewer attachment names an activated runtime attempt and its
exact assignment generation. A line has at most one writer. Checkpoint
preparation first requires the writer attempt's exact attached runtime to be
positively quiescent with a terminal disposition, atomically revokes the
database grant, and fences that assignment generation through its Authority
session. The frozen checkpoint binds the committed fence evidence. Previously
minted writer boundaries recheck the live grant at adoption and mount
composition, so revocation also invalidates capabilities already in memory.
Only then may the profile retain immutable evidence; no writable mount can
coexist with read-only review. Review admission also
compares worker, participant, and principal identities with the checkpoint's
producer and refuses if any identity is shared.

`changes-requested` preserves the same checkout and grants a fresh writer based
on the current checkpoint. The next freeze increments the revision; all older
checkpoint evidence remains resolvable. Only an `accepted` verdict creates an
integration-eligibility row. A verdict requires the reviewer's exact runtime
to be positively quiescent, its disposition to be `completed`, its output to
be frozen or sealed, and its result to retain separate `findings` and `logs`
outputs. Sealed output additionally requires accepted intake for the exact
result and manifest, matching artifact identities and measurements, and a
retained decision for every review artifact. The manager fences the review assignment
and binds that fence and the frozen-result summary—including the manifest
digest locating the retained result—to the verdict. Eligibility is revalidated
against that exact checkpoint, completed review attempt, result, fence, and
verdict rather than the mutable line path.

For the current W71830 milestone, ordinary implementer tests and independent
technical review replace the prerequisite for a separate clean verifier. The
reviewer's verification axis is preserved as recorded, including `none`,
`failed` or `unable`; recording a technical verdict does not certify required
tests or set that axis to `passed`. Integration admission separately checks
the exact retained ordinary-test evidence against the trusted test requirements.
An accepted technical review alone does not establish passed tests or authorize
integration. The separate ordinary-test admission implementation is owned by
W112029, and W112039 gates joined acceptance of both capabilities.

## Deployment wiring

The generic manager receives a checkpoint profile capability. The included
`GitCheckpointProfile` owns all Git argument vectors and retains checkpoints
under `refs/baton/checkpoints/<line-id>/<revision>`. Its injected runner accepts
one tuple argument vector and returns exactly:

```python
{"returncode": 0, "stdout": "...", "stderr": "..."}
```

The runner must execute without shell interpolation. A nonzero result becomes
a profile refusal; extra or missing result members are refused. The profile
freezes only a clean committed worktree and records exact base, head, tree,
sorted path set, path-set digest, and retained reference. A deployment without
an equivalent immutable-checkpoint profile must refuse this workflow rather
than copy the candidate between roles.

Every line creation and writer/reviewer custody act derives its root from the
Worker Manager's committed `workspace_storage` configuration; none accepts a
caller-supplied storage path. The manager proves that line storage is
disk-backed but performs no predictive free-space preflight, reservation, or
live quota check. Concrete
allocation, mount, write, and `ENOSPC` failures belong to the affected attempt
and do not delete the durable line or retained checkpoints. `line_status`
accepts an operator-supplied storage-meter capability and reports accumulated
bytes and entries separately from lifecycle state. Live byte and entry
ceilings remain W91072's hardening boundary.

For an implementation runtime, `writer_boundary` composes the nominated source
read-only at `/input/source` and the persistent line directly writable at
`/output`; there is no whole-tree copy. For review, `review_boundary` mounts the
current line read-only at `/input/source` and retains the review attempt's own
separate writable `/output`. It repeats the checkpoint profile's current-line
validation immediately before composing that mount, after confirming that no
writer grant exists.

## Recovery

All externally visible mutations use the manager operation journal. A freeze
has an additional durable `preparing` state because writer revocation must
commit before the external Authority fence and profile work. The fence has its
own effectively-once manager and Authority operation identities. If the
process, Authority call, or profile fails in that window, retrying the same
writer resumes the same checkpoint revision, fence, and retained reference; it
never restores the writer or allocates a later revision. Review completion uses
the same resumable exact-generation fence before its verdict transaction. Line
creation similarly records its immutable source, base, profile,
and custody path in `materializing` state before the one profile checkout; a
restart resumes that checkout and changed recovery operands refuse. Exact
operation retries replay, while reuse with changed operands refuses as an
operation collision.

After successful ordinary cleanup, eligibility and exact review-ending replay
read retained history instead of asking the destroyed runtime to become
quiescent. This requires the exact ended attachment, committed verdict and fence,
matching frozen result, accepted intake and retained artifacts, and the matching
committed `runtime.destroy` operation under that receipt and retention policy.
The operation must prove positive runtime absence and retained cleanup. Its
result and workspace custody receipts must exactly match the committed
normalization receipts, including their attempt, root, operation and account.
The custody owner reads and validates those records against the recorded
workspace store without requiring an adapter or running another helper. A bare
`destroyed` axis, missing history or unresolved provider teardown is insufficient.
Destruction cannot create a first verdict.

The ending compares the original completion and retention operands on replay
and returns the same verdict account without another worker, fence, freeze,
intake or destroy call. An unsettled cleanup remains held. Retained custody
bytes remain outside the disposable execution roots and can be reopened after
cleanup. This covers immediate completion replay; it does not introduce an
automatic restart or recovery service.

The Worker Manager schema is version 18. It has the repository's standing
fresh-store rollout boundary: older control stores are refused, not migrated or
guessed across.
