# W63214 reviewer research — 2026-09-01

## Result

The immediate dogfood path has a stable effective ceiling of 512 entries, not
its advertised 2,000. The failure is late: the present copier publishes the
destination and copies the whole 513-entry tree before canonicalization
refuses. A 512-entry profile limit is the bounded correction for temporary
file-tree Work; retaining the frozen schema's 100,000-entry capability would
be a separate protocol/conformance design, not a constant increase.

No protocol or application code was changed by this research.

## Exact path

1. `tools/dogfood_operator.py:compose` allocates the attempt workspace and
   calls `stage_source` before offer or claim.
2. `stage_source` accepts up to `MAX_SOURCE_ENTRIES == 2000`, checks only that
   the fixed `inputs/source` target does not already exist, and calls
   `worker_manager.workspaces.copied_manifest`.
3. `copied_manifest` creates the target immediately, walks and copies each
   file through the reviewed descriptor/no-follow path, and accepts the
   caller's 2,000-entry ceiling.
4. After the loop it computes `tree_digest = digest(entries)`.
5. `contracts.canonical.digest` descends into the list and refuses more than
   `MAX_MEMBERS == 512` entries. `stage_source` therefore never returns and
   `input_manifest` is never composed.

The same array has later barriers too. `contracts.pod.own` recursively refuses
every nested list over 512 before schema validation, and `_sealed` digests the
whole input/result manifest containing `content_manifest.entries`. Replacing
only the tree-digest calculation would leave both barriers intact.

## Reproduction

Retained W61984 run2:

- source files: 836;
- copied `storage/attempt-w61984-run2/inputs/source` files: 836;
- other immediate input-root entries: none;
- offer, claim, credential delivery, runtime and provider: not reached.

Focused current-code probe using empty regular files and
`copied_manifest(..., max_entries=2000)`:

```text
512 512 True
513 schema 513 True the array carries more than the frozen limit of 512 entries
```

The four fields are requested size, returned/copied count, destination
existence and refusal. At 513 the fixed destination exists with all 513 files.

## Conflicting owners

| Surface | Current limit | Effect |
| --- | ---: | --- |
| Python `contracts.canonical.MAX_MEMBERS` | 512 | Any nested list/object above this cannot be owned or digested. |
| Dogfood source and output constraint | 2,000 | Stable trees 513–2,000 are admitted, copied, then refused. |
| Python `workspaces.MAX_ENTRIES` | 100,000 | The walker advertises work its manifest constructor cannot finish. |
| Frozen `contentManifest` schema | 100,000 | The wire schema permits documents the Python owner rejects first. |
| Node reference canonicalizer/manifest check | 100,000 schema bound | It has no corresponding 512-member canonical bound. |
| Reference Python worker output measurement | assignment constraint, schema up to 100,000 | It can report a manifest the Python manager cannot own. |

The Python comments call both 512 and 100,000 the frozen contract's own bound.
They cannot both be authoritative. This is why an implementation must not
silently choose 100,000 by raising `MAX_MEMBERS`: that changes every canonical
object and array boundary, not only content manifests.

## Recommended patch boundary

### Temporary dogfood and generic file-tree profile

- Export or reuse one canonical-derived content-entry ceiling of 512. Derive
  `dogfood_operator.MAX_SOURCE_ENTRIES`, the Python workspace manifest ceiling,
  and dogfood output `constraints.max_entries` from it.
- Add a bounded no-destination measurement that takes the same entry and byte
  ceilings. It must run before the fixed `inputs/source` path is created.
- Copy into a fresh private target with the existing `copied_manifest`; do not
  write a second path copier.
- Compare the copied manifest exactly with the preflight manifest. A source
  mutation is a refusal, not a choice of whichever pass is convenient.
- Atomically rename the private tree to the fixed target only after equality.
  On every refusal, clean only the private tree this call created. The fixed
  target remains absent, so stage-once has not been consumed.
- Check an existing fixed target before preflight and preserve the current
  `OperatorRefusal` wording and stage-once semantics.

This two-phase operation does not trust the preflight bytes as the copied
bytes. The no-follow copier still measures and writes from each one descriptor;
the comparison only proves that the admitted source and copied source are the
same content manifest.

### Capability above 512

Do not attempt it inside this bounded correction. A valid design must make all
of these agree: frozen schema copies, Node and Python ownership,
canonicalization, whole-manifest digest, tree digest, manager measurement,
worker measurement, input delivery and output sealing. Candidate directions
include a new schema generation with a chunked/Merkle entry representation or
a schema-aware bounded canonical owner. Merely special-casing
`digest(entries)` or raising the generic 512 bound is incomplete.

## Regression matrix

Positive:

- 0, 1 and exactly 512 regular files stage successfully;
- the preflight, copied and freshly measured destination manifests are equal;
- input-manifest and whole-manifest digests recompute;
- a fresh attempt identity succeeds after an earlier over-limit refusal.

Negative:

- 513 stable files refuse before the fixed destination exists;
- caller bounds 0/bool/text or above the profile ceiling retain current typed
  refusals;
- byte overflow, links at either depth, hard links, FIFOs/devices and invalid
  paths refuse with no fixed destination;
- an existing fixed target refuses before preflight and remains untouched.

Race/retry:

- add, remove, rename or rewrite a source entry between preflight and copy;
  manifest disagreement refuses and leaves no fixed destination;
- a source growing while read remains bounded by allowance plus one;
- two staging calls for one identity cannot both publish;
- a failed private copy cannot be mistaken for a staged fixed target on retry.

Focused verification:

- `tests.manager.test_workspaces`;
- `tests.manager.test_manifest_rules` and `tests.manager.test_canonical`;
- reference worker measurement cases;
- `tests.tools.test_dogfood_operator`;
- dogfood arc/retry engine gates and the existing broader v12 gate.

## Open decision

Approve the 512-entry temporary profile bound, or explicitly schedule the
versioned representation/conformance work needed to preserve 100,000. The
production Git-backed profile remains locator-plus-commit and is outside this
recursive file-tree design.
