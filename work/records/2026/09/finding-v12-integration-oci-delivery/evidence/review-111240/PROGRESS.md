# Progress

## 2026-09-07 — baton.claude — the boundary revalidated and adopted

PLAN item 2, complete. State: **awaiting independent review of the adoption**.
No source file has been edited; item 3 is not started, and the last section
says why plainly rather than by implication.

### What the revalidation actually checked

All nine files `evidence/research-111047/baseline.json` binds are
byte-identical in the current tree, so the research inspected exactly this
tree. Each "Confirmed" claim was then re-read against the source rather than
against the summary of it — the delivery's two namespaces and their fixed
container constants, `adopt_delivery`'s parent-first descriptor proof,
`run_vector`'s and `OciAdapter`'s parameter lists, the `ROOT_NAMES` /
`MOUNTABLE` / `WRITABLE` confinement that produces the baseline's three
`policy/denied` refusals, and `start`'s attempt binding for the launch document
and the authenticated input root. All hold.

### Three things the revalidation established that the research did not state

**The container target is free, and now demonstrably so.** I enumerated every
fixed container target this build composes — ten of them, listed in FINDING.md
— and `/target` is equal to none and is neither an ancestor nor a descendant of
any. That matters because the plan requires a both-directions collision check,
and a check whose answer is vacuously empty proves nothing.

**The public assignment reader is genuinely absent.** `observed_delivery`
compares published bytes against an assignment the caller already holds and
answers a state; `_read_bounded` is private. Nothing answers the published
document. So the plan's new reader is an addition rather than a rename, which
is worth knowing before somebody goes looking for the function it was thought
to be.

**The import constraint is a cycle rather than a risk.** `worker_manager`
imports nothing from `integration`, and `integration.runtime` imports
`worker_manager.attempts` and `workspaces`. A module-scope import of
`integration.oci_delivery` inside `worker_manager/oci.py` therefore cannot
work at all, rather than merely pulling in an eager graph. The resolution point
has to be inside the use.

### What was pinned, because the plan asked for it explicitly

The private immutable binding companion is `mount-binding.json` at
`<delivery.root>/mount-binding.json` — beside the two mounted namespaces and
never inside them — under the existing 0o700 delivery root, published through
`runtime`'s existing no-clobber atomic write. Schema
`baton.v12.integration-mount-binding/1` with closed members `schema`,
`attempt_id`, `assignment_digest`, `canonical_target_id` and `sources`. No
runtime id and no lifecycle state: the runtime journal is `oci.py`'s, and a
companion carrying one would be a second account of the same lifecycle.

Public names are pinned in FINDING.md. Semantics are the proposal's; only the
spelling was open and only the spelling is settled.

### What is NOT delivered, and the reason rather than an excuse

**PLAN item 3 — the typed three-mount family, the public assignment reader,
the final pre-engine proof and the observed-mount adoption — is not started.**
No file under `v12/python/src` or `v12/python/tests` was edited by this turn,
and no candidate hashes are offered, because there is no candidate.

The reason is a judgement about where a partial change does harm. Item 3 is a
multi-file change across the OCI start boundary carrying the enumerated refusal
matrix: no grant, blocked or ended grant, wrong attempt, participant, profile,
version or instruction digest, publication mismatch, target swap, symlink,
foreign root, overlap and shadowing in both directions, group and mode
incompatibility, duplicate start, unknown run result, exact reconstruction, and
foreign or missing observed mounts. `worker_manager/oci.py` is shared by every
worker suite in this tree; a mount family half-composed there is worse than an
absent one, because the absent one refuses and the half-composed one starts
something.

So it is left whole for its own scheduled turn. Whether that is this
implementer next, or somebody with the room to carry the whole matrix in one
pass, is the reviewer's and Slawomir's call rather than mine to decide by
starting it.

### Verification

None is claimed and none was run: this turn changed no source. The evidence
for what it does claim is the hash revalidation, the target enumeration and the
two structural facts above, all reproducible by reading the tree.
