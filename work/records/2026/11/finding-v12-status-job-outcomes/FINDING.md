# Installed status: Job outcomes first

## Owner decision — 2026-11-19

Slawomir agreed that just status is not UX friendly and assigned the improvement to codexpc. Current observed behavior: native-labels-4 status showed healthy manager/publisher, one Job and a runtime count while the canonical monitor showed implementation exceptional and review blocked.

Selected behavior: lead with per-Job outcome and stage failures/blockers; service health follows. Example (only when supported by evidence):

```text
Job w29401-labels-3: FAILED
  implementation: agent fault; no proposal
  review: blocked by implementation
Services: manager running, publisher running
```

Example wording is illustrative. Unknown reason/output remains unknown; absent artifact evidence does not automatically prove no proposal. Preserve source freshness and canonicality qualifications. Runtime counts and safety boundary remain available after the useful summary. This is presentation of existing facts, not altered lifecycle semantics.

Owner-approved UX decision: installed just status must lead with useful per-Job outcomes, followed by service health; healthy manager/publisher and runtime counts must not obscure failed work. Queue for baton.codxpc role impl AFTER its current W385222 handoff; do not interrupt that active claim. Coordinator baton.prompt independently reviews; K owns separate labels-fault diagnosis. Read bound FINDING/PLAN before implementation. Use existing canonical published status; no new database reader, execution or status-side mutation. Report failed/exceptional implementation, blocked review and available safe fault reason accurately; do not invent unknown causes, proposals or active coding. Preserve stale/absent/noncanonical qualifications, empty idle behavior, lifecycle exit semantics and detailed runtime boundary. Focused deterministic CLI/output tests; no live runs, instance changes, broad redesign or Git mutations. Hand off exact candidate/evidence to baton.decide and release claim.

Ledger: 2b077949-W385227. Discovery: W321608 native labels pilot. Independent Work, no dependency edge installed; current W385222 continues without interruption.

## 2026-11-19 — E385238 implementation revalidation

W385222 is accepted, committed and closed; its earlier sequencing gate is satisfied. Current retained canonical-fault-status.json confirms an exceptional implementation with exchange terminal fault code `agent`, adapter_failure null, and a closed implementation gate holding review. The snapshot does not supply the layout diagnosis as a typed cause or prove output absence. The presentation therefore says agent fault/cause unknown, not no proposal or a fabricated root cause.

The implementation derives a concise Job heading from published stage states and shows the states beneath it. Completion means published stages completed, not independent owner acceptance. Cancellation request and shutdown disposition remain separate. Freshness/canonicality qualification precedes all outcomes; missing/unreadable data remains unknown and stale/noncanonical empty data does not claim current idleness. Existing JSON observe schema, exit code and runtime safety boundary are unchanged. One validated publication supplies both text and runtime facts.

Ownership notice M385245 in T385227 and M385246 in T321608 names only stack.py/test_stack.py; K pool/single_worker layout pairing is disjoint. The attempted obsolete include=baton.claude was refused before posting, then coordination was posted in the active parent thread. No shared-path edit or change to the accepted recovery candidate.

## 2026-11-19 independent acceptance

Accepted for selective human checkpoint: two-path manifest79b1ae6dd1fcb4faf70c8e129fc63dbe06f1842c0819d1c776a272186557c020 on85e646ba. Both working paths match retained candidate bytes. Independent tests.tools.test_stack:133 tests OK in26.078s, evidence/independent-review.log. Job outcomes and exceptional/blocked details precede services; fresh/stale and canonical qualifications precede outcomes; unknown cause and output remain unknown, completed stages do not claim acceptance. Checked single-snapshot observation, unchanged observe JSON and status exit behavior, retained runtime boundary, malformed optional fields and escaped identifiers. No blocking findings. Changed existing test path tests/tools/test_stack.py only adds eleven cases, no weakened assertions. No build or deployed-runtime verification; installed status remains old until supported deployment of a new bundle. K files excluded; codexpc hold edits, human checkpoint then owner closure. Review review-2026-11-19T17-14-14Z.md.
