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
