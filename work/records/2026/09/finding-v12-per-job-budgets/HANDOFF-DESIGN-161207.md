# Independent design review of revised managed integration proposal

Prepared under W156162 claim161207; **subsequent independent design review belongs
to W161230**, per owner M161222/M161232. W156162 waits on that mandatory separate
Work. The packet's source evidence remains here; do not move or duplicate it.
Intended design reviewer baton.impl, return baton.feat under W161230.
**DO NOT IMPLEMENT.** Read the bound FINDING/PLAN/PROGRESS, prior independent
DESIGN-REVIEW-161103-2026-09-13.md, DESIGN-RESPONSE-161207.md and current
MANAGED-INTEGRATION-DESIGN-v2-2026-09-13.md. Canonical root is
`baton:work/records/2026/09/finding-v12-per-job-budgets/`.

Review the proposed response to the rejected orchestration gate, independently:

1. Explicit JobStore root/member relationship respects existing stage allocation
   foreign keys/unique effective-principal indexes; actual separate phase claims;
   serial admission including parent apply; all release paths guarded in `_move`.
2. New no-start cancellation reader can prove the exact unstarted parent cannot
   subsequently launch, including cancellation/start race and unknown start.
   It must not claim attached-runtime quiescence or discharge an Authority gate.
3. Slice-one portable result table, schema5→6/read-only compatibility and legacy/
   managed cross-table unique result semantics. No invented paths, lost old target
   lease, reclassified host result or unreviewed automatic migration.
4. Target-owner entrypoint and current grant/old-revision/collected-evidence
   ordering, using existing input/output and node-local trusted capabilities.
5. Exact proposed first-slice source/test scope and preserved host/managed test
   obligations. No blanket authority for all later slices or unrelated changes.

Append a new dated independent design review and return the Work; do not modify
v1, its prior review or v2 to make an objection disappear. If accepted, enumerate
the exact design/path boundary suitable for owner implementation approval. If
not, name the failed invariant and concrete alternative or missing owner contract.
No runtime verification is required merely for review; inspect relevant source
and reuse measured evidence. No live provider, installation, Git mutation or
unbounded scope. Existing29-file candidate unchanged in research-161207.json.

Author246runs2530.5844189850177s plus four disclosed unknown activities;
reviewer147.7342205499972s including current inventory. Preserve all spending,
failed probes and unknowns; no numeric cap/reset/transfer. W103525 is separately
at owner consolidation discussion and does not grant source authority here.
