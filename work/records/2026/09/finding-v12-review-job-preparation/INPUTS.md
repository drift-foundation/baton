# Inputs and interface gaps for W239533

W244180 preparation, claim244188, 2026-09-23 UTC. This checklist records pending
values rather than inventing a packet. Owning decisions:
[W239533 FINDING](../finding-v12-independent-review-proof/FINDING.md),
[PLAN](../finding-v12-independent-review-proof/PLAN.md), and
[owner split](../finding-v12-managed-session-resume/OWNER-SPLIT-20260922.md).

## Acceptance checklist

| Input | Required evidence | State at preparation |
| --- | --- | --- |
| W239528 prerequisite | Independent acceptance of actual retained proposal, stopped execution and positive cleanup | Pending; custody source acceptance is narrower |
| Corrected worker artifact | Image reference/digest and build provenance binding accepted adapter bytes | Pending; prior selections bind old adapter |
| Immutable subject | Proposal ID/manifest digest; result ID/digest; artifact locators/content digests; base/head/tree; producer assignment/generation, worker, participant, principal; line/checkpoint identity | Pending accepted W239528 output; do not substitute historical held output |
| Review criteria | Independent task bytes/digest, explicit requirements and meaningful verification argv | Not selected; no fabricated expected verdict |
| Execution identity | Fresh run/submission/Job identity, reviewer worker/participant/principal and assignment, distinct from producer | Pending selection; v11 Work selector is not automatically a v12 Work or Job ID |
| Checkpoint/store arrangement | Exact v12 Authority/Work/line mapping and reviewed attachment procedure, paired stores and provenance/retention access | Pending; see G2 |
| Isolated resources | Bound source snapshot/bundle, configured private launch/output/log roots, credentials reference, image, network and resource policy | Pending; no credential contents in packet evidence |
| Manifest/deployment | Review-role task/input digest; required findings/logs outputs; profile/policy/adapter digests; independent allocation and route bindings | Pending separate-review composer |
| Bounded command | Digest-bound composer/supervisor, exact argv/import path, finite turn/overall/cleanup/no-progress limits, one review/no retry | Pending; see G1 |
| Inspection and stop | Published status/log/outcome locations, exact attempts, tested interruption and positive cleanup accounting | Reusable readers exist; reviewer-specific outcome/stop contract pending |
| Verification and selection | Deterministic real-boundary proof, independent packet acceptance, exact live-provider question and owner execution selection if needed | Not granted by W244180 |

Keep W239528, W239533 and W236087 as distinct executions and evidence records.
Do not reuse failed/consumed run identities, grants or stores by merely changing
a label. Preserve prior runtime uncertainty separately. Any proposal to continue
against an accepted producer's retained control records needs an explicit tested
arrangement; it is not authority to reopen its old execution packet.

## Recorded gaps — no workaround or implementation in this preparation

### G1 — separate reviewer composer and bounded supervisor are not delivered

**Observed:** W239533's dossier currently contains FINDING and PLAN only.
W239528's `baseline.py:KINDS` is implementation-only; its composer emits an
implementation-only submission and refuses review invocation bounds.
W236087's `supervisor.held_packet` requires implementer and review counts of
`corrections + 1`, with at least one implementer. `job_manager.main` exposes
submit/status/serve, with no review-only one-run/stop subcommand.

**Consequence:** none is the selected one-review/no-implementation command.
Do not relabel or run them as W239533. The W239533 execution owner must supply
the missing composer/admission/accounting path and independently reviewed
bounded command. Reuse accepted mechanisms, not consumed packets. This is an
unfulfilled composition deliverable, not evidence that review itself is absent.

### G2 — retained proposal to separate Job binding needs an explicit procedure

**Confirmed in source:** `StageDeployment.line_for(job_id)` calls `create_line`
using the binding's v12 Authority/Work; `StageComposition._prepare` selects that
line's current checkpoint. `review_cycles.attach_review` requires a frozen
checkpoint, matching profile, same Authority/Work assignment, and a different
worker, participant and principal from its producer. The stage deployment also
requires `job_work_id == review_work_id` within one binding.

**Open:** the reviewed procedure mapping the separate W239533 execution to
W239528's retained checkpoint and exact proposal bytes. A brand-new unrelated
line has no accepted producer checkpoint; copying the proposal file or supplying
a new Work ID does not create that provenance. Distinct v11 Work and execution
identity must not be confused with permission to bypass the v12 same-line rule.
The relevant composer/attachment proof has not been delivered in W239533.

**Required:** select and test the exact continuation/transfer arrangement with
supported interfaces. Prove wrong/stale/foreign checkpoints fail before launch
and independence survives across Jobs. Do not copy database rows, manufacture
a writer/checkpoint or weaken the validators. Whether additional product
support is necessary is not established by this static inspection.

### G3 — CLI status is not guaranteed to open stores read-only

**Observed:** `tools.job_manager._status` goes through `_job_store`, which calls
`JobStore.open`, and uses `ControlStore.open`. `JobStore.open` can initialize or
migrate a store; the separate `open_readonly` API is not used by this CLI path.

**Consequence:** calling that command with arbitrary paths is not a safe way to
discover a deployment under this preparation's no-store-mutation constraint.
No store was opened here. `stack_command view` and `logs` read published files
without stores and are immediately reusable. A future packet must select its
status publisher against verified existing paired stores, or provide a reviewed
strictly read-only interface if that is required. No status implementation change
is proposed or authorized by this document.

## Existing support that should be reused

- `claude_agent._review`, `_review_prompt`, `_review_report`: independent
  criteria from the frozen task, read-only source, validated provider-authored
  report and adapter-attributed findings/logs. No context restore is needed.
- `review_driver.prepare_review`, `end_review_from_result`,
  `review_verdict_from_result`: checkpoint attachment, retained result-derived
  verdict and strict assignment/base/head/tree attribution. The old unused
  `_no_verdict` helper in stage_execution is not the current call path.
- `review_cycles.review_boundary` and `attach_review`: read-only checkpoint
  plus separate writable reviewer output and producer/reviewer independence.
- `stack_command` manager/status, view and logs: exact command forms and limits
  in [OPERATOR.md](OPERATOR.md); no invented reviewer launch verb.
- W239528 `baseline.py` interruption, admission and cleanup accounting are
  reference mechanisms only. Any reuse in a reviewer supervisor needs its own
  scope, actual CLI proof, provenance checks and independently accepted packet.
