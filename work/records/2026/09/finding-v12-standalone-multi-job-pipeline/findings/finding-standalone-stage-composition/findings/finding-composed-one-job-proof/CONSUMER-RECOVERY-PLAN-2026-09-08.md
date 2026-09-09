# Composed-ending recovery plan

**Recovery semantics superseded 2026-09-09T04:13Z.** Slawomir permits abandoning
unfinished work and repeated execution from the last committed handoff/checkpoint.
The campaign FINDING's "Restart from committed handoffs; repeated work is allowed"
entry replaces this plan's mandatory same-attempt intermediate continuation,
pre-intent adoption and no-repeat-start guarantees. Preserve committed-effect
safety and history below; W122060/W119114 PLANs carry the current re-scoping action.

**Current disposition — approved 2026-09-08, owner event119712.** baton.slaw
approved this exact split, contracts, six shared-provider paths, five consumer
paths and explicitly scheduled test conversions. The original proposal below
is preserved as history; its pending-approval language is superseded by this
decision. Shared provider **W119733** binds
`baton:work/records/2026/09/finding-v12-composed-ending-recovery/` and waits for
actual W119548 acceptance. W119114 now also waits for W119733 acceptance
(edges119734/119735). Both implementations and the joined proof remain open.
The earlier route-authority refusal was resolved when owner event119711
returned W119114 to baton.bug for this placement.

Prepared by baton.codex following M119628. This is a proposal for owner
disposition, not source/test authority. W119548's accepted six-path provider
is already routed separately. W119114 remains blocked on that provider and
owns the actual joined lifecycle proof.

Owner disposition is tracked by lightweight **W119673**, routed to baton.ops.
The attempted child attachment to W119114 refused ordinary route authority
(`baton.codex` is not a handler of `baton.impl`); no child attachment or
dependency was made by the reviewer. W119673 asks the authorized actor to
install the scheduling gate or return the consumer for reviewer scheduling.

## Observed boundary and recommended split

`projection._ending_owed` stops driving an ending once cleanup is terminal.
`_SingleWorker.ending` reconstructs mounts/credentials before it reaches the
composed driver. `end_implementation` then quiesces before reading retained
results; unlike the review driver's historical branch, it has no destroyed-
runtime resume branch. Appending the provider call to the existing ending is
therefore insufficient both to schedule recovery and to execute it safely.
The standalone `_AuthoritySession` also lacks the new forwarding member.

Propose two serial deliveries after W119548: a separately accountable shared
recovery provider, then W119114's existing assembly glue and joined proof.
The former owns six exact paths; the latter keeps its original five. This
keeps shared scheduler/driver changes out of an incidental assembly edit.
Create and bind the shared provider Work after disposition, before source
changes, and gate W119114 on its actual independent acceptance as well as
W119548. Neither the plan approval nor component tests finish W119114.

## Shared recovery provider: exact proposed paths

Paths are relative to `v12/python/`:

1. **New** `src/baton_v12/job_manager/ending.py`: own a narrow durable
   composed-ending obligation and its readers in the existing Job operation
   journal. No schema change, second database or Worker Manager journal write.
2. `src/baton_v12/job_manager/projection.py`: include that owned pending
   obligation when deriving completion and downstream eligibility. Preserve
   the current cleanup rule when no composed-ending obligation exists.
3. `src/baton_v12/job_manager/manager.py`: resume pending registered endings
   through the existing `operations.conclude` serving act on ordinary ticks,
   including retained prior episodes. Read-only status performs no resume.
4. `src/baton_v12/job_manager/review_driver.py`: provide the bounded historical
   resume of a positively cleaned implementation ending, and preserve/extend
   the review historical path only as required for the same owned evidence
   contract. No engine, agent, credential, mount or new publication operation
   may run in the historical path. Use actual retained owner records.
5. **New** `tests/job_manager/test_ending.py`: additive public-operation,
   projection/status and ordinary-sweep tests for the obligation contract.
6. `tests/job_manager/test_review_driver.py`: additive historical implementation
   and review-correlation controls; preserve every existing assertion.

No edits to Job schema/store, delegation observation vocabulary, Authority,
Worker Manager or existing generic cleanup assertions are scheduled. An
additional required path is a scope finding before editing. New modules use
ordinary non-executable repository mode. The assembly's already-owned
`tools/parallel_test.py` will add the new test module to the existing registry,
preserving its current serial declarations.

## Durable ordering and ownership

The Job manager owns the obligation to finish a composed stage, not the truth
of runtime absence. Use its existing public `transact`, `replay` and
`operation_record` operations. One immutable intent and one correlated settled
record use deterministic identities bound to Job, stage, episode, offer,
attempt, Authority assignment and configured retention-policy identity. Own
closed documents before persistence/readback; validate each identity against
the existing stage/episode/claim binding. No boolean in a configuration or
caller-supplied gate evidence stands in for an owner receipt.

Commit the intent before the first composed ending can reach cleanup. An
intent with no exact settlement remains pending after terminal cleanup. A
settlement is written only after the accepted driver evidence, W119548 gate
act when required by the recorded fence, and the applicable routing act have
all succeeded. It records their correlated owner references/results; it does
not authorize them. Keep the intent selectors sufficient to reconstruct the
same ending without a process cache or a live exchange. Retain a validated
terminal identity needed by the driver; the driver's frozen result must still
prove that terminal, so persistence never promotes the worker's claim to proof.

Pending enumeration must include recorded prior episodes, not only the current
stage episode. This covers a crash after `open_correction` creates the next
round but before the old ending records settlement. Enumerate owned stage/
episode identities and read their deterministic journal records; do not infer
unfinished work by reading raw journal SQL from a deployment. The serving
resume uses the recorded old identities, finishes only their historical
operation and cannot reopen/restart an old runtime. Avoid two executions of
the same pending ending within a tick; owner operation replay remains required
regardless. A malformed/foreign record refuses visibly and never opens a
dependent stage. An old obligation cannot change a newer generation's gate.

The projection reports an unsettled registered ending as still owed even with
`exchange: null` and terminal cleanup. Status reads the Job journal and existing
canonical observations; it must open no Authority, session, engine or serving
factory. A settled old ending does not keep the next episode pending. Existing
unregistered generic stages retain their current cleanup semantics. For a
previously interrupted composed attempt predating this intent, the serving
consumer must explicitly adopt the obligation from the existing bound stage,
checkpoint/verdict and cleanup evidence before it can report completion; no
unconditional migration or fabricated absence is permitted.

Historical driver resume validates the exact attempt/generation, frozen
terminal/result, intake receipt, retention operands and successful cleanup
proof before returning its retained checkpoint/publication or verdict result.
For publication, read the committed proposal evidence; do not replay an
operation through a now-ended live-assignment check. No re-granting a writer,
re-quiescing a destroyed runtime or silently inventing a review verdict.
W119548 alone derives and submits absence evidence using the original attempt
participant's port. Retry the same provider operation after a lost remote
answer, and accept its exact replay after later Work movement. A no-gate
ordinary pass is not a reason to fabricate a quiescence obligation.

## W119114: original five paths, precise additions

- `tools/stage_execution.py`: register and settle the composed-ending
  obligation; resume terminal-cleanup cases through the accepted historical
  driver before runtime/mount reconstruction; invoke W119548's act through
  the correct worker port. Reconstruct the original writer/attachment from
  owned records and wire `end_review_from_result`. Preserve correction routing
  and the integration continuation/uncertainty contract.
- `tools/single_worker.py`: forward `satisfy_gate` through `_AuthoritySession`;
  permit the composed historical resume before mount/credential work, while
  preserving the ordinary single-worker ending.
- `tests/tools/test_stage_execution.py`: **explicitly schedule modification
  of the three existing methods in
  `TheComposedHandoffStopsAtTheUndischargedQuiescenceGate`**. Replace the absent-
  capability assertion with available exact forwarding; replace the gated
  completed-implementation assertion with exact discharge/queued Work evidence;
  replace the refused-review-offer assertion with an ordinary tick issuing the
  next independent review offer. Rename the class/docstring to describe the
  corrected behavior. Preserve the prior file/digest and reproduction in the
  record. Add reconstructed-manager and ordinary-tick recovery controls below;
  do not remove unrelated negative assertions.
- `tests/tools/test_single_worker.py`: additive exact forwarding and unchanged
  ordinary-ending compatibility controls only.
- `tools/parallel_test.py`: add the new shared test module; preserve all
  existing serial-lane declarations and test registrations.

## Focused acceptance, then joined proof

Shared controls cover closed record shape/correlation, missing/foreign/stale
settlement, generic stages without an intent, read-only status with no exchange,
and recovery after correction advances the episode. Driver tests prove real
retained evidence is required and assert zero physical/runtime calls in the
historical path. Reuse W119548's absence and remote replay controls.

The actual composed fixture must stop and reconstruct all managers at: (a)
cleanup commit before discharge starts, (b) remote discharge commit before its
local answer/settlement, and (c) correction routing commit before the old ending
settles. Ordinary ticks must finish with no operator transition, duplicate
start, publication, checkpoint, verdict or correction. A deferred cleanup
before positive absence keeps the original ending owed. Preserve uncertain
runtime/integration holds and custody digests. The same submitted Job must
still traverse real review, correction, acceptance, integration and terminal
handoff; three converted assertions alone do not prove that lifecycle.

Before execution, each actual author records the new evidence question,
commands and cumulative budget. Proposed component budget: focused new tests
then the affected Job manager modules once, about 60 seconds. Proposed joined
budget: the composed fixture then one relevant existing assembled sweep, about
30 seconds before reassessment. No daemon, new live-model authority, Git
mutation or broad baseline rerun follows from this plan. Missing ability to
verify under installed authority is reported, not worked around. Reviewer
will inspect source bytes and reuse sufficient retained component evidence.
