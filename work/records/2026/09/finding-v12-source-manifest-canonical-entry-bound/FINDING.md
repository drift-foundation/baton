# Make v12 source staging respect canonical entry bounds

Ledger Work: W63214

## Observed — 2026-09-01

W61984 isolated run2 supplied a clean 12 MiB source subset containing more
than 512 entries. `dogfood_operator.stage_source` admitted the tree under its
documented 2,000-entry limit and `workspaces.copied_manifest` copied it into
the attempt input root. Computing the manifest's `tree_digest` then called the
canonical document encoder over the complete entry array, which refuses more
than `canonical.MAX_MEMBERS == 512` entries.

The attempt stopped before an offer, claim, credential delivery, container or
provider turn. Its partial state is preserved under `/tmp/w61984/run2`.

## Confirmed defect

The staging boundary promises and admits a source tree that its own canonical
manifest representation cannot encode. The effective representable bound is
not checked before copying, so an otherwise harmless input-size refusal leaves
a never-launched, one-shot partial attempt.

This is separate from W62535's deployment-prerequisite ordering but has the
same fail-fast requirement: every immutable source-shape property needed to
form the canonical manifest must be proved before the destination is created
or any entry is copied. Stage-once remains correct and must not be weakened.

## Direction

Use one shared bound between source admission and canonical manifest
construction, or replace the oversized entry-array digest input with a
bounded canonical representation. Whichever design is selected, the public
staging boundary must refuse an over-limit source before allocating or copying
the destination, and every later manifest consumer must accept every source
the boundary admits.

Add focused boundary cases at 512 and 513 entries, prove that the latter
leaves no destination, and preserve the existing byte, path, type and
stage-once checks. Do not silently truncate, batch, or hash an unrepresented
suffix.

## Bounded workaround

Preserve run2 and start W61984 run3 with a new identity and a task-specific
source subset below the currently representable 512-entry ceiling. This is
only an operator workaround for the already logged defect; it is not the fix.

## Scope clarification — 2026-09-01

This defect governs the temporary dogfood copier and genuinely generic
file-tree inputs. It does not justify making recursive copy, enumeration or
per-file hashing part of the production Git-backed profile. The superseding
Git input ruling uses an exact repository locator and commit; the worker
clones or fetches and verifies that commit in its private workspace.

## Reviewer revalidation — 2026-09-01

**Confirmed:** the observed limit is not merely a dogfood constant mismatch.
Four currently live limits disagree:

- `contracts.canonical.MAX_MEMBERS` refuses every array or object above 512;
- `dogfood_operator.MAX_SOURCE_ENTRIES` admits 2,000 source entries and also
  declares 2,000 as the proposal-output ceiling;
- `worker_manager.workspaces.MAX_ENTRIES` is 100,000; and
- the frozen `contentManifest.entries` schema and the reference Node worker
  contract admit 100,000 entries.

The Python producer calls `digest(entries)` only after its copy loop, and the
Python consumer owns every nested array before schema validation. A special
tree-digest helper alone therefore cannot make a 513-entry manifest usable:
the same entry array is nested in the input/result document and the whole
manifest digest must canonicalize it too.

**Measured:** a 512-file empty tree passes `copied_manifest`; adding one file
makes the canonicalizer refuse, but only after the public destination exists
and contains all 513 copied files. Retained W61984 run2 has 836 files in both
its source and copied `inputs/source`, with no `input.json` or
`assignment.json`; the failure happened before `stage_source` could return its
manifest.

**Proposed bounded correction:** use 512 as the temporary dogfood/generic-
tree profile ceiling, derived from the canonical owner rather than repeated as
a literal. Apply it to both source staging and declared directory-result
constraints. Before the fixed `inputs/source` target is created, perform a
bounded no-destination manifest pass. Copy through the existing reviewed
no-follow copier into a fresh operator-owned private target, compare the
actual copied manifest with the preflight manifest, and publish the fixed
target atomically only on equality. Any refusal or source race removes only
that owned private target and leaves `inputs/source` absent; an existing fixed
target still refuses stage-once before either pass.

This uses the preflight only as an admission fence. The copier remains the
authority for the bytes it writes, and exact manifest comparison prevents a
source changed between passes from being silently accepted as the preflighted
tree.

**Open approver choice:** 512 is narrower than the frozen schema and the Node
reference, while 100,000 is not representable by the current Python canonical
owner. This Work can safely close the temporary profile at 512 without
claiming the frozen schema was changed. If generic file-tree Work must retain
the 100,000-entry promise, that requires an explicit protocol/conformance
decision and a bounded schema-aware representation or ownership design; it is
not a reason to lift the generic canonical member bound incidentally.

Detailed code paths, reproduction, patch boundary and regression matrix are
in `evidence/research-2026-09-01/README.md`.

## Approved temporary profile — 2026-09-02

Select the canonical-derived 512-entry ceiling for the temporary dogfood and
genuinely generic file-tree profiles. Apply the same bound to source admission
and declared directory results, prove it before creating the fixed destination,
copy into an owned private target, compare the actual copied manifest with the
preflight manifest, and publish atomically only on equality. Preserve the
existing stage-once refusal.

Do not broaden the generic canonical member limit in this Work. A future need
for the frozen 100,000-entry promise requires a separately scheduled versioned,
schema-aware representation. Production Git-backed Work remains outside this
copier and uses repository locator plus immutable commit.

Implementation remains an isolated v12 assignment; this approval does not
route the Work to the legacy v11 implementer.
