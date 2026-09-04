# Prove the standalone two-Job v12 pipeline

Ledger Work: W71879

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/`

## Confirmed scope

Run one integrated, evidence-producing acceptance demonstration after the
bounded control-plane, source/workspace, concurrent-stage, review-correction,
and integration leaves are available. This leaf owns fixtures, one submission,
measurement, retained evidence, and the independent assessment of the whole
vertical slice. It does not repair a component defect inline; a defect returns
to its owning Work and this proof is rerun from a clean submission.

## Review-ahead scheduling ruling — 2026-09-04

The open component dependencies constrain FREEZING AND RUNNING the integrated
proof, not independent review of its demonstration contract. The scenario
shape, required evidence, operator-intervention budget, test-change authority,
resource measurements, and pass/fail boundary can be reviewed before those
components finish. That review may require a targeted delta review if a
component's accepted interface later differs materially from the assumptions
recorded here; it cannot claim that the demonstration itself passed.

Protocol 11 cannot represent those stage-scoped edges. For review-ahead, the
eligible reviewer temporarily removes the open component edges, claims and
reviews this plan, restores every still-open component edge before leaving
review, and reroutes the Work to implementation. Restoring the first edge
atomically releases the review claim, so this is deliberately a
`block`-then-`reroute` ceremony rather than a `pass`. The live proof therefore
stays blocked until all providers are accepted, then becomes runnable without
an operator watching the queue.

## Demonstration shape

- Submit at least two independent Git-backed Jobs from the same immutable base
  commit in one documented CLI/JSON operation.
- Run both implementation containers concurrently in separate disk-backed
  manager-custodied workspaces with immutable read-only source mounts,
  separate durable output/log locations, and bounded scratch.
- Send each immutable candidate checkpoint to an independent containerized
  reviewer. Force one bounded changes-requested result, return that Work to the
  same private development line, and accept a later checkpoint without another
  source clone or candidate-tree copy.
- Include one explicitly planned existing-test modification within its Work
  scope. Also inject one distinct out-of-scope test mutation and prove the
  integration preflight refuses it before any canonical path changes.
- Queue accepted proposals to the one-target integrator and import them
  serially. Slawomir retains final Git ownership.
- Inject one worker/runtime failure and prove the other Job and available
  slots continue without a full manager or v11 restart.

## Acceptance evidence

- The submitted document, immutable source/base identity, Job/offer/claim/
  attempt/session identities, workspace/source mounts, checkpoints, review
  verdicts, integration queue/lease records, and final handoffs are retained.
- The status projection is sampled at queued, offered, claimed, running,
  reviewing, changes-requested, integrating, completed, and exceptional states
  and includes runtime identities plus safe relative log/activity locators.
- Process/container timing proves at least two implementation runtimes overlap.
  Review and integration timing proves reviews may overlap unrelated coding
  while one target's integrations do not overlap.
- Filesystem evidence proves source mounts stay unchanged, writable workspaces
  are distinct and disk-backed, the correction reuses one private line, and
  canonical paths are untouched by the refused candidate.
- Operator intervention is enumerated. Ordinary transition count is zero;
  allowed human acts are initial submission, the deliberately forced review
  verdict or policy decision, exceptional observation, and final Git action.
- Record wall latency, per-stage latency, CPU utilization, peak workspace and
  scratch use, retained artifact sizes, failures/refusals, and every operator
  intervention.
- Independent review either calls this narrow design promising or records the
  exact false-success/blocking defect and links the owning follow-up Work.

## Test-change authority

This Work authorizes creating demonstration fixtures and adding or editing
tests within the exact paths named by the final frozen run plan. It explicitly
requires one planned existing-test modification and one out-of-scope mutation
fixture. The accepted candidate/review must enumerate those paths; any deletion
or weakened production expectation must be separately explicit. No other test
mutation is authorized.
