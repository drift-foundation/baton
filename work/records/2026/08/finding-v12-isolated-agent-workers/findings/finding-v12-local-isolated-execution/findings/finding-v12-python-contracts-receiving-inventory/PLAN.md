# Plan: inventory the Python contracts receiving boundaries

1. Revalidate the actual `baton_v12.contracts` public export set, signatures,
   existing boundary primitives and current manager inventory conventions.
2. Derive the receiving-entry universe from that actual surface rather than
   from the owner table being checked.
3. Declare exactly one owner or checked non-entry rationale for every entry.
4. Add exactly one non-vacuous probe per owned entry, including structural
   proof where a public composite delegates to a private-body rule.
5. Run focused inventory tests, the full Python source suite and the locked
   distribution gate; record evidence in this dossier.
6. Hand the completed inventory to independent review under this Work. Do not
   fold it back into W6592.

## Review correction — 2026-08-25

1. [confirmed] Derived 18-callable/40-entry universe and private composite
   structure are sound; strengthened label witnesses pass.
2. [required; W7079] Own `ContractRefusal.message` as safe durable text and
   `.durable` as an exact Boolean without running caller behavior.
3. [required here after W7079] Remove both `UNOWNED` values, name their actual
   owner rules, add non-vacuous direct/transaction probes, and keep
   `test_no_receiving_entry_is_marked_unowned` green permanently.
4. [blocked] W6782 waits on W7079 before full source/locked verification and
   final review.

## Unblocked re-review — 2026-08-25

1. [confirmed] W7079 closed satisfying; both former `UNOWNED` entries now name
   real asserted owners with direct non-vacuous witnesses.
2. [confirmed] The derived contracts inventory passes 15/15, including public
   `MESSAGE_LIMIT` coverage added during review.
3. [record-only correction] Append the current completion and gate attribution
   to implementer-owned `PROGRESS.md`, which still describes the superseded
   11-test/unowned state.
4. [next] Return for final record verification. No implementation change is
   requested. Review: `review-2026-08-25T00-57-12Z.md`.

## Final-record re-review — 2026-08-25

1. [confirmed] The implementation and focused 15-test inventory are accepted.
2. [record-only correction] Append that the current derived universe is 18
   exported callables and 39 receiving entries, superseding the stale 40 count
   in `PROGRESS.md`.
3. [next] Return for final closure. Review:
   `review-2026-08-25T01-02-30Z.md`.

## Final review — 2026-08-25

1. [done; signed off] The progress record now carries the recomputed 18/39
   universe and the inventory passes 15/15. W6782 is complete. Review:
   `review-2026-08-25T01-04-54Z.md`.
