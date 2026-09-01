# Reviewer revalidation — 2026-09-01

## Retained observation

`/tmp/w52821/run5/evidence.json` records one exact post-worker state:

- attempt `attempt-w52821-run5b`;
- assignment `baton.claude`, generation 1;
- worker disposition `unable`;
- runtime `94753a3a1c5a93c17609ab6b4654a61346dead63d1d258ad5bf9cbcf7dd2f4de`;
- execution positively observed `quiescent`;
- frozen output and an intake receipt with proposal custody;
- no retention decision, review pass or cleanup result; and
- cleanup refused because the exact assignment remained live.

Docker's answer is intentionally not upgraded to absence. The assignment
state-machine specification says a quiescent runtime still exists and could
resume; only `destroyed` is positive absence. Accordingly, the dossier's
opening phrase “No container remained” is retained history but not a confirmed
absence fact. The evidence proves “not running,” and still names the quiescent
runtime and its mounts.

## Current public boundaries

The current tree was revalidated at these symbols:

- `worker_manager.attempts.request_cancellation` journals a cancellation,
  fences and ends the exact authority assignment, then orders the agent and
  runtime to stop. It deliberately does not satisfy the authority's
  runtime-quiescence gate.
- `worker_manager.intake.authorize_cleanup` replays an exact completed cleanup,
  but a new cleanup refuses while the fixed assignment is still live. It also
  refuses custody for which no retention decision exists.
- `dogfood_operator._custody` records quiescence, terminal worker disposition,
  frozen output and intake before its independent verification. A nonzero
  independent status raises before retention and review pass.
- `dogfood_operator._ended_however` then calls cleanup directly. It has no act
  between “do not pass an unverified candidate” and “cleanup requires the
  assignment to be over,” producing the retained run5b refusal.
- `authority.core.cancel` already provides the authoritative atomic effect:
  fence the exact generation, clear the Handler/live assignment, free the
  participant's claim slot, and install
  `runtime-quiescence:<generation>` for any replacement.

The existing general cancellation operation is not a complete substitute for
the missing boundary. Its post-fence agent and runtime stop calls are correct
when cancellation initiates quiescence. Run5b is already past that point: the
manager has a terminal disposition and a durable exact `quiescent` runtime
observation. Requiring fresh agent/runtime capabilities to restate that fact
adds new fallible external acts after the fence and can turn an already-ended
conversation into an exception.

## Baseline check

From `v12/python` with `PYTHONPATH=src` and bytecode writes disabled:

```text
tests.tools.test_dogfood_operator.EveryPostStartBranchEntersTheEnding.
  test_failed_independent_verification_never_passes_to_review ... ok
tests.manager.test_attempts.CancellationFencesBeforeItStops.
  test_the_agent_is_ordered_before_the_runtime ... ok
Ran 2 tests in 0.007s — OK
```

The first case pins the current gap: verification failure causes no review
pass and cleanup is attempted while the assignment remains live. The second
pins why the existing cancellation operation must not be weakened: for a
running attempt, fence-agent-stop ordering remains its contract.

## Recommended state sequence

1. The worker disposition is already one terminal alternative and the exact
   execution runtime is already durably `quiescent`.
2. An explicit operator decision invokes a new manager finalization operation
   for the attempt, with a bounded reason.
3. The manager re-reads those preconditions, derives the fixed four-part
   assignment and exact runtime identity from its own row, journals one
   operation identity, and asks the authority to cancel/fence that assignment.
4. The authority atomically ends the assignment and frees participant
   capacity, leaving the Work blocked behind
   `runtime-quiescence:<generation>`. The manager performs no agent call,
   runtime stop, retention decision, proposal pass, acceptance or discard.
5. The retained custody remains pending for an explicit operator retention
   decision. Only after that decision may existing exact cleanup destroy the
   runtime and prove absence. Positive absence may then satisfy the authority
   gate; quiescence alone never does.

This sequence reuses the ruled authority cancellation effect without changing
the existing running-cancellation operation.

## Proposed patch boundary

- `src/baton_v12/worker_manager/attempts.py`: add the public already-quiescent
  finalization operation and deterministic manager/authority operation IDs;
  share only the exact fence validation with cancellation.
- `src/baton_v12/worker_manager/documents.py` and `__init__.py`: closed result
  shape and public export.
- `tools/dogfood_operator.py`: expose an explicit recovery/finalization mode
  over existing evidence and grants; do not make ordinary verification failure
  silently cancel by itself.
- `tests/manager/test_attempts.py`: preconditions, exact identity, wrong
  generation/participant, crash and restart replay, and no injected agent or
  runtime act.
- `tests/tools/test_dogfood_operator.py`: explicit mode, durable account,
  contradictory operands, no credential read, no pass/retention/cleanup, and
  the corrected failed-verification expectation.
- `tests/manager/test_boundary_inventory.py` plus the public inventory/text
  sweeps required by the new boundary.

No schema column is proposed. The manager operation journal records the
reason, terminal disposition, runtime identity, exact assignment and authority
operation identity; the authority journal remains the source of truth for the
fence and assignment end.

Implementation must start from the then-current tree. W52821's signed-off
six-path candidate changes `tools/dogfood_operator.py` and its tests, while
W61599 currently changes `attempts.py`, schema and the operator activity path.
Neither participant's retained patch may be overwritten or silently treated
as the baseline.

## Regression matrix

- terminal `unable`, `completed`, `plan-rejected` and `cancelled` dispositions
  with exact `quiescent` runtime can be finalized;
- disposition `none`, running, uncertain or merely agent-quiescent state
  refuses before the authority is called;
- wrong participant, authority, Work, generation or fence answer refuses and
  performs no output/retention act;
- crash before fence, after fence and before returning, and manager restart
  reuse the same manager and authority operation identities;
- exact replay returns the first durable reason/disposition/fence answer;
  changed operands collide;
- finalization does not alter output, custody, retention, verification,
  review, approval or integration axes;
- cleanup before finalization still refuses; cleanup after finalization still
  refuses until every custody artifact has an explicit retention decision;
- after that decision, existing cleanup proves exact absence, releases the
  runtime lane and preserves retained custody when the decision says keep;
- positive exact absence, never quiescence or agent settlement, is what may
  satisfy the authority gate; and
- a successor generation or another participant/runtime is never fenced,
  stopped, cleaned or otherwise affected.
