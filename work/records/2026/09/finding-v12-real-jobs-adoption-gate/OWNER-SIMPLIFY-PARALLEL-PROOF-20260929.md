# Owner direction — simplify the parallel proof

Confirmed by Slawomir in the interactive context on 2026-09-29 after discussion of repeated preparation validators and partial handoffs. Recorded by baton.prompt while the managed reviewer holds W247941; this file avoids concurrent changes to reviewer-owned FINDING/PLAN.

Reuse the accepted single-Job preparation machinery and evidence wherever applicable. Supply two task descriptions and isolated workspaces under one Host manager. The additional proof is actual execution overlap, isolation, attribution and completion, with independent review of both useful proposals.

Do not grow a bespoke validation framework as the objective of this Work. Each additional check or abstraction must address a concrete failure relevant to the selected run. Prefer existing mechanisms and a bounded connected deliverable. Fix the known writes-before-refusal defect; do not waive reached DB-I/O, isolation, false-success, work-loss or identity defects, weaken genuine coverage, or discard historical evidence.

This supersedes any interpretation of earlier implementation suggestions as mandatory additional layers of contracts, packet validators or checkers. It does not require a broad refactor, rollback of accepted changes, two independent Host managers, or removal of useful existing checks. Implementer chooses the smallest adequate reuse/adaptation and explains any unavoidable parallel-specific addition.

Reviewer: incorporate this direction into FINDING/current PLAN and the next complete handoff before continued implementation. Review the complete selected path; avoid per-edit approval loops. Claude remains implementer. Existing independent acceptance and operational execution boundaries remain unchanged; no new live run, deployment or Git mutation is authorized here.
