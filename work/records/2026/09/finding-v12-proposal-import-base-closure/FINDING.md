# Make retained v12 proposals complete against their import base

Ledger Work: W62098

## Finding

W52821 run5b started from a source tree that already overlaid the retained run4
candidate. Its durable `changed_paths` and independent review therefore named
only the six paths changed between run4 and run5b. They did not name inherited
run4 changes that were still absent from the canonical repository.

After run5b review signed off, the operator imported the six reported paths.
The repository gate failed immediately because `tools/dogfood_operator.py`
still exposed the retired `--credential-file` boundary while the imported
tests required `--credential-sources`. The complete retained candidate does
contain the required operator change. It also lacks concurrent W61599 edits to
the same file, so replacing the repository with the whole candidate would
silently overwrite unrelated live work.

This is an import-lineage defect, not a candidate-code verdict. A delta against
the immediate staged source is insufficient when that source is itself a
retained proposal. The importer needs a complete immutable relationship among
the canonical import base, every inherited candidate layer, the signed final
candidate and the current target tree.

## Confirmed stopgap — 2026-09-01

The W52821 operator may perform one bounded manual integration after recording
this defect: retain the signed candidate's W52821 changes, retain the current
W61599 changes, touch no other differing path, and rerun the exact W52821 gate
plus overlap-focused tests. This stopgap does not satisfy this finding and does
not authorize automatic conflict resolution.

The durable correction is deferred to its own isolated v12 attempt. Until it
lands, an importer must stop whenever the current target differs from both the
declared canonical base and the signed candidate on an intended path. It never
replaces a whole candidate tree merely because that tree passed review.

## Acceptance

- Every attempt records the immutable canonical import-base identity and any
  inherited proposal lineage separately from its immediate staged source.
- The retained result exposes the complete intended path closure relative to
  that import base, including changes inherited from prior candidate layers.
- Independent review signs the final candidate digest and the complete import
  closure, not only the newest worker delta.
- Import compares the current target, canonical base and signed candidate and
  refuses overlapping divergence without overwriting either side.
- Disjoint current work remains byte-for-byte intact; a conflict becomes a
  typed operator decision rather than an automatic merge.
- A focused multi-run reproduction proves that run2 changes inherited by run3
  are not omitted and that concurrent edits to one inherited path stop safely.
- The correction is produced in its own isolated v12 attempt and independently
  reviewed before import.

## Reviewer revalidation — 2026-09-01

The retained run2, run4 and run5b artifacts reproduce the defect. Run5b's
immediate source already contains the run2 `tools/dogfood_operator.py` change,
so the newest six-path delta is internally correct but is not the import
closure. Direct canonical-base-to-final-candidate comparison yields seven
paths. The omitted inherited path now differs from both sides in the working
repository because the authorized manual stopgap preserves concurrent W61599
work; automatic replacement would be data loss.

The current v12 layers each hold only part of the needed relationship:

- dogfood proposal/evidence v1 records the immediate source digest, final
  retained candidate digest and immediate byte delta;
- authority publication records the input, result, policy, candidate and
  canonical-target digests, and authority integration fences a moved target;
  but
- neither surface retains canonical-base bytes, inherited candidate lineage,
  a complete path-state closure, or a path-level three-way import result.

The measured digests, complete W52821 seven-path closure, exact code paths and
proposed contract are preserved in
`evidence/research-2026-09-01/README.md`.

### Proposed decision boundary

Keep three facts distinct and bind all three to the final proposal:

1. the immediate source-to-candidate delta, which remains worker accountability;
2. ordered digest-linked inherited proposal lineage, which is provenance; and
3. the independently derived canonical-base-to-final-candidate closure, which
   is the review and import boundary.

Use a retained immutable base artifact, not only a mutable checkout, Git name,
or unresolvable digest. Represent every closure side as explicit `absent` or
`file` state with byte count and content digest. Derive the closure directly
from base and final candidate; do not union intermediate deltas. Review and
downstream receipts bind base, closure and final-candidate digests.

Import preflights the whole closure before writing. A current state equal to
the candidate is already applied; one equal to the base may apply; one equal
to neither is overlap and refuses the entire import. Disjoint paths remain
untouched and the first slice performs no automatic merge. Authority's
canonical-target fence remains necessary but does not substitute for this
byte-level three-way comparison.

W61981's approved `baton.dogfood-task/2` remains the verification-context
owner. W62098 may reuse bounded manager-copied source machinery, but import
base/lineage are separately named and digest-bound; verification input is not
implicitly an import base.

### Open decisions before implementation

1. Approve a separate closed import-context/result version while preserving
   task/2 and proposal-v1 `changed_paths` semantics.
2. Approve the retained-base, digest-linked-lineage and explicit path-state
   closure representation recorded in the evidence.
3. Approve all-path preflight, whole-import overlap refusal, no automatic
   merge and no integration receipt without a no-partial-write boundary.
4. Choose the exact repository-integrator write/fence mechanism. The current
   dogfood operator has no filesystem importer and v12 authority integration
   advances only the canonical target digest.
