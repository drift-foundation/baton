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
