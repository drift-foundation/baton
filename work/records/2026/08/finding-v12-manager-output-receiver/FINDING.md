# Finding: the manager's output freeze and sealed artifact receiver

Canonical Baton Work: W6628, a separately scheduled M2 manager prerequisite
from the closed W4 and W5 PLAN item 8. Dossier created 2026-08-24 by
`baton.claude` on claiming, because the assignment requires one before
implementation.

## Confirmed boundary

The Python manager-owned output-freeze/collector handoff and the sealed
artifact observation receiver: quiescence before freeze, declared regular-file
manifest with count, bytes and digest, immutable staging identity,
effectively-once acceptance and retry, and caller-local refusals. **The manager
decides acceptance and settlement; adapter and engine status carry no authority
meaning.**

**Not here:** OCI filesystem collection (W6634), credentials (W6634/W6630),
retention and cleanup (W6629), provider code, and lifecycle composition (W6636).

## Revalidated against the current tree

**The frozen contracts exist and are more specific than the brief.**

- `artifactOutput` requires `name, type, status, content_manifest, artifact`
  with `type` closed to `git-change-proposal, directory-result, record-output`
  and `status` closed to **`present, missing-optional`**. Both the manifest and
  the artifact are explicitly nullable.
- `outputDescriptor` — what the *input* manifest declared — carries `name,
  type, path, required, constraints`.
- The **output axis** is `open, freeze-requested, frozen, invalid, sealed,
  discarded`, and W4's `TRANSITIONS` already pins the moves:
  `open → freeze-requested | invalid | discarded`,
  `freeze-requested → frozen | invalid`,
  `frozen → sealed | invalid | discarded`,
  `invalid → discarded`, `sealed → discarded`, `discarded` terminal.

**Two facts the contract already decides, which this Job must consume rather
than re-decide:**

1. **`missing-optional` is a status, not an absence.** An output the assignment
   declared as not required and which did not appear is *reported*, with a null
   manifest and a null artifact. It is not silence, and it is not an error. A
   receiver that treated a missing optional output as nothing to record would
   lose the fact that the worker was asked and answered.
2. **`frozen` and `sealed` are different states with a transition between
   them**, and `invalid` is reachable from `open`, `freeze-requested` *and*
   `frozen`. So freezing is not accepting: material can be frozen and then
   found invalid, which is exactly the case a receiver that conflated the two
   could not express.

**What W4 already ships:** the output axis, its transitions, `observe` with
journalled effectively-once identities, and the sealed-refusal machinery in the
control store. The receiver hangs off that journal; it does not add a second.

**What does not exist:** any Python operation that accepts an artifact
observation, freezes, or records a sealed result. `ARTIFACT_REF_MEMBERS` is a
member list in the contracts layer and `seal_refusal` is the control store's
refusal sealing — a different thing wearing a similar word. This is the gap
**W6634 is blocked on**.

## Dependency

**W6628 → W6592.** The receiver must consume the completed contracts inventory
and public composition rather than creating an unindexed receiver — the manager
package's boundary inventory would otherwise carry a public operation nobody
declared. W6592 is open with changes requested, so this Job cannot start.

## Acceptance

- Quiescence proved before freeze; `freeze-requested` and `frozen` distinct.
- Declared regular-file manifest with count, bytes and digest recomputed by the
  manager, never adopted from the collector's account.
- Immutable staging identity, so a retry names the same material.
- Effectively-once acceptance through W4's journal.
- Caller-local refusals; engine or adapter status never decides acceptance.
- `missing-optional` recorded as the answer it is.

The implementer creates and exclusively owns `PROGRESS.md`.

## Implementation decisions — 2026-08-25

Recorded by the implementer under the claim that built this slice.

**Retention is part of this Job, and it had to be.** The receiver's whole
declared-output comparison is against a document the store did not hold. The
frozen host was corrected for exactly this: "the store held only
`input_digest`, so a schema-valid result could substitute an undeclared output
or drop a required one while echoing the expected digest." Making the
declaration a caller operand instead would be a proof the caller writes, which
is not a proof. So `manifests.py` is here, keyed by digest, serving both the
input declaration and the frozen result.

**This slice ends at `frozen` and never writes `sealed`.** The brief says
"sealed artifact observation receiver", and `sealed` there is the adapter's
sealed OBSERVATION document, not the output axis's `sealed` value. `invalid` is
reachable from `frozen`, so material can be frozen and then found invalid; the
axis value belongs to W6634, and writing it here would remove the state that
expresses the distinction this finding already pinned.

**`freeze_operation` takes an attempt ROW rather than an id.** The identity is
derived from the row's own assignment members, and a caller that already holds
the row should not have to re-fetch it — the row crosses back in as a caller
operand and is owned as one. Its members are each their own inventory entry
and each is probed.

**The record identity is fixed per attempt and assignment, not per digest.**
If it varied with the bytes, two different results would be two different
operations and BOTH would commit, which is the opposite of what an immutable
record means. The identity is the act; the signature carries the bytes.

**Not here, and named so the absence is deliberate:** filesystem and OCI
collection, credentials, retention and cleanup, provider code, lifecycle
composition, and the `sealed` transition.

## Operational finding — the boundary inventory resolves private helpers by name

**Observed 2026-08-25.** `tests/manager/test_boundary_inventory.py` keys
functions by LEXICAL SITE and its header explains why, but
`_returned_origins` — the fixpoint resolving what a private helper hands back —
is keyed by the helper's NAME across the whole package. Two modules with a
private helper of one name therefore collapse, and one becomes invisible to the
inventory.

Hit directly: naming this module's attempt reader `_attempt`, as `sessions.py`
already does, made two of W6627's adopted column entries stop being wanted — a
green-looking narrowing of the universe caused by a name. Avoided here by
naming this module's reader `_attempt_of`, with the reason at the site. NOT
fixed here: correcting it changes how every module's entries are derived, which
is a change to a shared gate and deserves its own Work.

## Independent review finding — 2026-08-25

**Observed, P1.** The mutable positive-quiescence precondition is checked from
an attempt row before `store.transact`, but the journalled `_request` action
does not re-read it under the write lock. A newer `execution_runtime=uncertain`
observation can therefore land between check and write and the stale row still
authorizes `output=freeze-requested`.

The deterministic regression and full analysis are in
`review-2026-08-25T06-08-36Z.md`. The decisive quiescence check must occur
inside the freeze transaction before the output transition; the optimistic
outside check cannot authorize the write.

**Resolved 2026-08-25.** The decisive `_provable` check now re-reads the
attempt on the transaction connection before the output transition. The
review regression and the surrounding output/attempt/store suites pass; final
sign-off is recorded in `review-2026-08-25T06-41-52Z.md`.
