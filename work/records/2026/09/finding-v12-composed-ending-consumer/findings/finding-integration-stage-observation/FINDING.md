# Integration stages have no observation or owed-conclusion boundary

Work W126558, parent W122060. Created by baton.codex under parent claim126550.

## Confirmed — 2026-09-09, owner M126545

Owner approved the exact seven-path provider allocation in
`../../INTEGRATION-COMPLETION-ALLOCATION-2026-09-09.md`, implementation via
baton.impl returning baton.bug, including its scheduled tests. This record owns
that provider; W122060 retains the separate deployment consumer and final proof.
The exact implementation interface is pinned in `OBSERVATION.md` before handoff.

## Observed baseline

Parent `../../review-2026-09-09T06-15-16Z.md` and
`../../evidence/review-125625-probe.py` / `.json` contain the executable diagnosis.
Reuse it; do not rerun its fixture merely to restate the failure. An actual
corrected and independently accepted proposal runs through the integration
workload, which returns integrated. Ordinary ticks nevertheless project starting
and call generic exchange dispatch; no exchange exists for integration. The
diagnostic-only integration call commits the Authority receipt and coordinator
settlement/release, but the stage still projects starting and the Work remains
held. This provider fixes the scheduler observation boundary, not the missing
terminal Work handoff owned by the parent.

Confirmed paths/symbols, revalidated at allocation:

- `src/baton_v12/job_manager/delegation.py`: `ManagerOperations.observe`,
  `_bound`, `unobserved`, the closed observation members and injected readers.
- `src/baton_v12/job_manager/projection.py`: `_observed_state`, `_conversing`,
  `owed_exchange`, `EXCHANGE_OWED`. Current completion depends on frozen output;
  absent exchange becomes starting and selects dispatch.
- `tools/job_manager.py`: `_Observing` currently extracts only observe_exchange.
  Add only the distinct optional reader, retaining its inability to refresh or
  perform serving acts.
- `worker_manager.attempt_runtime_of` already returns the fixed assignment;
  reuse it to bind the integration observation, without another storage read.

These are paths relative to `v12/python`. The exact allowed test paths and
acceptance are in PLAN. No store schema or stage-status document change is
required: use the existing stage states, with an optional internal observation.
Provider acceptance uses a small concrete manager/projection fixture and honest
reader documents; real integration provenance is the parent's consumer proof.

## Ownership and limits

Do not manufacture an exchange/frozen result, treat integration receipt as a
quiescence discharge, or perform actions from an observation. Existing
implementation/review behavior and negatives remain binding. Unknown or foreign
documents fail closed. Missing capability preserves existing deployments.
Completed means the consumer has read and cross-bound committed integration,
lease release, exclusion and exact terminal handoff, not merely worker success.

Parent's confirmed terminal disposition is existing pass_work on the current
integrator's fixed assignment to its configured outgoing review_route, after
proved worker exclusion and owned committed integration completion. This
provider does not implement that act or weaken its preconditions.

Operational note: a reviewer search also named nonexistent
worker_manager/read_model.py; attempts.py was found and confirms the public
runtime reader. A later optional validator search named nonexistent
authority/contracts.py; the existing worker_manager assignment constructor and
runtime shape were read directly instead. No missing source was treated as
evidence or required file skipped.

## 2026-09-09 — independent review126648

`review-2026-09-09T09-13-35Z.md` records three confirmed contract mismatches:
non-integration stages accept integration completion; mutable uncertainty
overrides committed completion; generic frozen-output logic overrides an
integration hold. The independent public-status probe reproduces all three.
OBSERVATION.md revision1 remains the exact contract; the implementation's
claim that no discrepancy exists is superseded by this evidence. Correct
within the seven allocated paths and scheduled tests. Parent acceptance stays
gated; preserve the already accepted generic ending behavior and current bytes.

## 2026-09-09 — independent acceptance126698

`review-2026-09-09T09-20-55Z.md` resolves all three review126648 findings on the
exact candidates in `evidence/accepted-126698/manifest.json`. Independent public
status probes and43 focused controls pass. This supersedes the outstanding
correction status, preserving its history. OBSERVATION.md revision1 remains the
provider/consumer contract. W122060 now consumes the independently accepted
boundary under its two-path authority; its real terminal handoff and final
ordinary/restart acceptance are not implied by this provider's closure.
