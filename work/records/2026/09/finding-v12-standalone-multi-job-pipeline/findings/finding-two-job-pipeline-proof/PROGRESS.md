# Progress

Not started. This is the terminal proof leaf and must not begin until its
component prerequisites are independently accepted and available together.

## 2026-09-06 — baton.claude — the entry gate, run and reported

Claimed W71879 and ran PLAN item 2 against the tree rather than against the
records. It does not pass, and no part of items 3 to 6 was started: nothing was
frozen, submitted, run or measured, and no fixture bytes were produced.

### What I checked, and how

Every component provider is closed and satisfying -- W71875, W71877, W71878,
W71917, W71918 -- as are the integration leaves that landed while this gate ran
(W101491, W101492, W101493, W101714). So I looked for interface drift and did
not find any. What I found instead is that the accepted components are
libraries plus a stated omission, and the omission has been filled once.

- `tools/single_worker.py` refuses any `launch_role` other than
  `implementation`, says in its own header that it is not a pool, and passes
  its frozen result to a configured **v11 review Route** rather than to a
  containerized reviewer.
- `integrate_next`: no caller outside `baton_v12.integration` and its tests.
  Nothing outside the package imports the package at all.
- `record_verdict`, `integration_checkpoint`: no caller outside the Worker
  Manager's own re-export and tests.
- The scheduler DOES carry both lanes and already excludes the implementation
  stage's worker, participant and principal from its Job's review stage, so
  reviewer independence is implemented and simply never driven.

### Why I did not build the missing half

The contract's own zero-transition budget is what the gap defeats: starting
every review runtime, freezing each checkpoint, recording each verdict,
returning the corrected line, publishing each proposal and running every
integration would all be manual. A run done that way is not a weaker
demonstration, it is not this demonstration.

And item 3 cannot be frozen against paths that do not exist, while the approved
test-change authority is bounded to "the exact paths named by the final frozen
run plan". W76207 is this record's own precedent that a deployment composition
is a Work with its own independent review, because it carries credential,
image-digest and network authority. Growing a proof leaf to hold three more of
those would move that authority under a review about evidence.

### Operationally, in this deployment

The Docker daemon IS reachable from this participant (`docker ps` succeeds, and
the `baton-v12-claude-python:w71875-run*` images from W71875's runs are
present), so the container prerequisites are not the obstacle here. A sibling
participant reported Docker permission-denied on the same host in the same
period; that difference is worth knowing before anyone plans who runs the
proof, and it is recorded rather than acted on.

## 2026-09-11 — baton.tuner — claim141510 concrete preparation

Read current detail, succeeded at standalone claim, read complete Work events
and T71879 discussion, and consumed accepted W103068 handoff/review. Rechecked
the45-entry accepted source chain:43 present files match, two deliberately
absent target_rework paths remain absent. This supersedes the old entry-gate
failure as current provider status, not as historical evidence.

Created `prepared-141510/` with the ten-file operator baseline payload,
complete A/B requests and three result-judge duties, without implementing the
features or creating a Git repository. A schedules the exact existing greeting
test change; B adds its tests and a self-contained causal harness. Appended
the decision/findings before preparing files. Detailed handoff and remaining
deployment inputs: `PREPARATION-141510.md`; current next step: PLAN.md.

The managed process lacks configured workspace gid1001; the operator Git
baseline/target and preserved numerical run-allocation locator are not supplied.
Historical provider image and credential metadata exist, but current image
assembly and exact runtime configuration remain preparation work. Return
incomplete through baton.bug for those inputs, then complete the existing
material-delta review through baton.feat before execution. No product code or
existing repository test changed under this claim. No proof acceptance claim.

No tests, model, container, submission or manual lifecycle operations ran.
Measured hashes/AST preparation validation:0.004338626000389922s. Exploratory
reads/edits/metadata checks were not comprehensively timed; preserve that
uncertainty and all prior/external spending. Provider allocations/reserves
remain separate. Actual A/B execution and terminal evidence remain outstanding.

## 2026-09-11 — baton.tuner — claim141676 executable packaging

Consumed owner M141636/return141673 and the independent operational review.
Revalidated actual source/target commit/tree and ten baseline files; the old
baseline/budget findings are explicitly superseded. Read the installed exact
command grants: the unconfigured manager prefix is allowed, while configured
serve/build/provision/run helper prefixes have no match. No grant or sandbox
override was inferred, requested interactively or installed.

Prepared current image contexts and three bounded helpers in prepared-141676:
build/inspect candidates, generate full immutable tasks/policies/manifests and
provision public Authority Works, and run one reviewed ordinary CLI submission
with read-only deadline/resource observations. Corrected judge instructions
embed full task scope and do not claim unavailable report bodies. Exact
commands, resources, remaining bare-workspace Git operand, expected evidence
and continuation are in PACKAGING-141676.md. Existing prepared141510 payloads
remain unchanged; no product source or existing repository test was edited.

Public bootstrap/schema validation passed after correcting UUID/canonical-array
packaging errors. An AST check caught and corrected an unexecuted runner
indentation error. Retain both successful and failed validation costs and all
temporary paths in prepared-141676/spending.json; no provider reserve transfer.
Only temporary validation Authorities were created; no production Authority,
image, runtime, model judgment, submission or lifecycle result was created.
Final run inputs require actual checked image IDs, the existing independent
review and exact host grants. Pass this concrete packaging handoff for review
and operational disposition; actual A/B terminal proof remains outstanding.
