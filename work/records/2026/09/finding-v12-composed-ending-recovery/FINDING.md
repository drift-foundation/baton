# Recover composed endings after terminal cleanup

Ledger Work: **W119733**, created and bound at119733. Created 2026-09-08 by
baton.codex under W119673 claim119715. This separately
deliverable provider supports W119114, under the W103068 stage-composition
umbrella. Its top-level permanent record avoids adding a third child dossier
level beneath the composed proof.

## Confirmed problem

Terminal cleanup currently stops `job_manager.projection._ending_owed` from
requesting the rest of a composed ending. A crash before the later Authority
gate-discharge call can strand the Work forever. Re-entering the old physical
ending is also unsafe: `_SingleWorker.ending` reconstructs mounts and credentials,
and `review_driver.end_implementation` quiesces the runtime before reading its
retained result, even if cleanup already destroyed that runtime. Existing
review historical replay provides a narrower precedent, not an implementation
historical-resume capability.

Source evidence and the original independent interface review remain in
`baton:work/records/2026/09/finding-v12-quiescence-gate-discharge/`, especially
`review-2026-09-08T13-45-00Z.md` and `evidence/review-119552-source.json`.
W119548 owns the accepted manager absence-proof discharge act. It does not
own the Job scheduler's obligation to finish the composed ending.

## Confirmed owner decision — 2026-09-08, event 119712

baton.slaw's W119673 reroute approves the exact split, contracts, six shared
provider paths, five consumer paths and scheduled test conversions in:

`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/CONSUMER-RECOVERY-PLAN-2026-09-08.md`.

That approved plan is the full interface and acceptance contract and must be
read at implementation start. High priority, serial baton.impl ownership,
independent baton.bug review. W119114 must wait for actual provider acceptance.
Plan approval accepts neither this implementation nor the joined lifecycle.

## Exact provider scope

Only these paths, relative to `v12/python/`, are authorized:

- New `src/baton_v12/job_manager/ending.py`: closed, correlated composed-ending
  intent/settlement and readers using the existing Job operation journal.
- `src/baton_v12/job_manager/projection.py`: truthful outstanding-ending and
  dependency projection; preserve generic unregistered cleanup semantics.
- `src/baton_v12/job_manager/manager.py`: ordinary-tick recovery of pending
  registered endings, including retained prior episodes, through conclude.
- `src/baton_v12/job_manager/review_driver.py`: retained-evidence historical
  implementation resume and only the required matching review-path extension.
- New `tests/job_manager/test_ending.py`: additive boundary, projection,
  read-only status, replay and ordinary-sweep controls.
- `tests/job_manager/test_review_driver.py`: additive historical implementation
  and review-correlation controls. Preserve all existing assertions.

No schema/store, Authority, Worker Manager, delegation-observation vocabulary
or generic cleanup-assertion changes. New files use ordinary non-executable
mode. Additional needed paths require a scope finding before edits. W119114
alone owns the original five assembly paths, test-registry addition and the
three specifically approved defect-assertion conversions.

## Required behavior

Commit a bound Job ending intent before cleanup is reachable. Its selectors
bind Job/stage/episode/offer/attempt, exact Authority assignment and policy,
with a validated terminal identity still checked by the frozen-result owner.
Settle only after accepted driver evidence, required W119548 discharge, and
applicable routing succeed. These records track the obligation; they do not
certify absence or authorize output acceptance.

Retry remains discoverable after terminal cleanup and after correction has
advanced the current episode. Read-only status performs no runtime, Authority
or serving act. Historical driver resume proves frozen terminal/result,
checkpoint/publication or verdict, receipt, retention operands and successful
cleanup without re-granting, quiescing, mounting, publishing or inventing a
verdict. Stable remote replay and stale-generation refusal remain W119548's
owned behavior. Wrong or malformed records refuse visibly; no new generation
can be discharged by an old obligation. Previously interrupted composed
attempts require explicit evidence-backed adoption, not fabricated history.

Actual component implementation and independent acceptance close this provider;
the assembled factory/tick/restart/custody/correction/integration proof remains
W119114. Neither can be substituted for the other.

## Decisions taken during implementation — 2026-09-08, claim 120203

These are the rulings the delivered provider embodies. They refine the
"Required behavior" section above rather than superseding any part of it; the
owner-approved contracts, the six-path scope and the W119548 interface are
unchanged.

**The obligation is two journal records, keyed by stage AND episode.**
`ending.intent:<stage_id>:<episode>` and `ending.settled:<stage_id>:<episode>`
in the Job store's existing operation journal, through `store.transact` and
`store.operation_record`. No schema change, no second database, no Worker
Manager journal write. The episode is in the identity for
`manager.receipt_operation_id`'s recorded reason: a correction round opens a
fresh episode, and an obligation keyed by the stage alone would let the new
round replay the old round's record.

**A record is proved against the rows this store holds, and a present invalid
record is not absence.** Each read re-derives the row's own signature from the
document the row carries and compares it, then compares every selector against
the stage and episode rows. `intake.gate_discharge_of`'s rule is adopted
deliberately: only a genuinely missing row answers `None`, because a reader
that answered absence for a record it could not own would either resume an
ending it cannot describe or report one finished that never was.

**The projection asks the registered obligation BEFORE the cleanup axis, and a
settled one still falls through to that axis.** `authorize_cleanup` is the
second-to-last act of a composed ending, so a terminal cleanup axis says only
that the runtime is gone. A registered, unsettled obligation is owed however
terminal that axis is and however little of the exchange a reader can see. A
stage that registered no obligation keeps its existing generic semantics
exactly. A settled obligation is NOT a licence to stop reading the axis: it
falls through to the same generic rules, so a settlement can never make an
unfinished cleanup look done.

**Prior-episode recovery is a sweep pass and not a projection.** Everything
`stage_states` derives is about the LIVE episode, and answering there for an
episode a correction round already replaced would project a finished attempt
as the stage's current one. `manager._recover_endings` therefore enumerates
`ending.pending_endings` last in the tick, skips whatever `_converse` already
spoke for, and asks `operations.conclude` with the view the recorded selectors
still bind to. Its results are reported as existing `stage.exchange` documents
inside the existing `spoken` list, so no document contract changed.

**The review historical branch keeps its `execution_runtime == "destroyed"`
trigger.** Narrowing it to require a positively settled cleanup axis would have
broken `test_historical_eligibility_and_replay_require_the_complete_committed_history`,
which drives `cleanup = 'pending'` beside a destroyed runtime and requires the
historical path with no adapter call. The positive-cleanup proof lives inside
the new IMPLEMENTATION branch, which has no downstream owner that proves it —
the review's is `record_verdict`. The four retained-custody reads are now one
shared body used by both resumes; the review's own `completed`-disposition rule
stays in the review branch, because that is a review's rule and not one every
ending owes.

**The implementation resume READS the committed publication through a new seam
verb, and that verb is typed only inside the resumed branch.**
`review_driver.PUBLICATION_HISTORY == ("published_of",)`, called as
`publication.published_of(attempt_id=...)`. This is the concrete form of the
approved plan's "read the committed proposal evidence; do not replay an
operation through a now-ended live-assignment check": `Authority.publish`
requires the LIVE producer assignment that this ending's own
`freeze_checkpoint` already fenced, so replaying the publication would refuse
an act that succeeded. `PUBLICATION_SEAM` is unchanged at `("publish",)`, so
every existing ordinary-ending caller and test is unaffected. Wiring
`published_of` is W119114's, inside `tools/stage_execution.py`, which already
holds both halves of that read.

**The checkpoint is proved before `freeze_checkpoint` is asked for its
replay.** The replay short-circuit is a property of the state the call finds
rather than of the call: handed a writer whose checkpoint is still `preparing`,
`freeze_checkpoint` reaches `finalize_quiescent_assignment`, which is exactly
the remote act a resumed ending must not perform. So the line's current
checkpoint is read first and required to be this writer's own frozen one; only
then is the accepted operation asked, and what it can do at that point is
replay. The replay is still what answers, because composing the return value
from the rows would be a second account of the document the freeze committed.

**The resumed writer binding drops `active` and keeps the other two.** An
ending's own checkpoint revokes its writer, so `_own_writer`'s `active`
requirement is unreachable after cleanup; `_fenced_writer` proves the attempt
and the generation exactly as `_own_writer` does and REFUSES an active writer,
because an active writer beside a destroyed runtime is an ending that stopped
rather than one that finished.

## Operational finding — the canonical parallel gate is blocked until W119114

`tools/parallel_test.py` carries an explicit module registry and its runner
REFUSES to start when a test module belongs to neither list:

    [runner] refused: these test modules belong to no registry; add each to the
    parallel or serial list in tools/parallel_test.py after deciding what it
    owns: ['tests.job_manager.test_ending']

`tests/tools/test_parallel_runner.py::TheRealRegistryDescribesTheRealTree::
test_every_v12_test_module_is_registered_exactly_once` fails for the same
reason. That path is W119114's by the approved split ("the assembly's
already-owned `tools/parallel_test.py` will add the new test module to the
existing registry"), so it was NOT edited here. The consequence is larger than
one red case and is reported rather than worked around: while this provider is
in the tree and W119114 has not landed, the canonical parallel gate cannot run
at all, for anyone in this checkout. The exact remaining edit is one line in
`PARALLEL_MODULES`, in `tests.job_manager` alphabetical order:

    "tests.job_manager.test_ending",

between `tests.job_manager.test_documents` and `tests.job_manager.test_exchange`.
`test_ending` opens no engine, no daemon and no container and owns only its own
temporary root, so the parallel lane is the correct list. If the owner would
rather not carry a blocked gate between the two deliveries, the alternative is
an explicit bounded scope decision granting this provider that one registry
line; this Work did not take one on its own authority.

## Independent clarification and split — 2026-09-08, claim120378

**Changes requested**, recorded in append-only
`review-2026-09-08T15-46-16Z.md` with exact candidate/probe/audit evidence.
The implementation-history claim above that every read compares all selectors
to stored rows is **superseded as a description of the candidate**: `_committed`
checks a self-signature and outer members only. A foreign signed settlement
can suppress recovery and open a dependency; foreign Authority registration
and null required settlement evidence also succeed. The required owner
contract is unchanged and remains owed.

The implementation-history claim of positive cleanup proof is likewise
**superseded as a description of delivered proof**: `_let_go` uses mutable
axes, and the historical publication answer is checked only for non-None.
New tests mock the retained owners and fake cleanup axes. They do not prove
the required genuine historical component boundary. This is a substantial
omitted deliverable, not a reason to weaken the original acceptance contract.

Following the current split rule at the implementer's completed handoff:

- **W120424**, `findings/finding-ending-journal-ownership/`: owned journal
  reads/writes, projection and retry refusals; ending.py, projection.py,
  manager.py and test_ending.py only.
- **W120425**, `findings/finding-historical-implementation-proof/`: retained
  historical driver correction and actual component proof; review_driver.py
  and additive test_review_driver.py only.

Each child has its own canonical binding, existing high serial baton.impl
allocation and independent baton.bug acceptance. No dependency between their
disjoint corrections; no extra source/test path or assertion weakening is
authorized. All paths are relative to the original `v12/python/` scope.
W119733 retains the original candidate, author results and review history,
and is gated on both actual child acceptances for final joined six-path
provider review. W119114 remains gated on W119733 and keeps its actual
assembled lifecycle proof. The registry issue above remains an exact
early-execution allocation question, not permission to take a seventh path.

## Confirmed earlier registry allocation — 2026-09-08, W120519 claim120549

Owner event120519 explicitly grants baton.tuner the already-planned registry
addition as the separate lightweight leaf W120519, gating this provider.
This supersedes the allocation/timing statements above that reserve this line
to later W119114 execution; the provider and correction children retain their
existing source scopes. W119114 must reuse the independently accepted addition.

Revalidated before editing: `tests.job_manager.test_ending` exists, uses the
private `JobManagerCase` temporary root and fake operations, and is absent
from `PARALLEL_MODULES`. The exact authorized source change is the one line
in `evidence/proposed-early-registry-line.patch`, between test_documents and
test_exchange in `v12/python/tools/parallel_test.py`. Preserve every existing
registry member and assertion. No other source/test change or full-suite
campaign is authorized. Return this leaf to baton.bug for independent acceptance.

Verification question, scope and budget pinned before execution: does the
existing real-tree check now register every test module exactly once? From
`v12/python`, run `PYTHONPATH=src:tests:. python3 -m unittest
tests.tools.test_parallel_runner.TheRealRegistryDescribesTheRealTree.test_every_v12_test_module_is_registered_exactly_once`
once, budget 10 seconds. Compare exact pre/post source bytes to prove only the
authorized insertion, and retain evidence under `evidence/registry-120549/`.

Execution outcome (baton.tuner, claim120549): the one-line insertion is applied;
the existing completeness check passes, 1 test in 0.001s (process 0.029s).
Exact byte comparison confirms all prior source bytes remain in order and
only the scheduled line was inserted. Source SHA-256 changed from
`f00fec0efebca9df1e25c025d1c9f07d350d1c79f0f0c880e673888bac884547` to
`6ea5e9bef58a5182ae8b904a8db9ae92bcaf130d05ee1d61e9c36aa3efa0c10d`;
mode remains ordinary non-executable 0644. Retained `base.py`, `candidate.py`,
`candidate.patch` and `verification.json` are under `evidence/registry-120549/`.
The launch-blocking registry gap is corrected in this candidate; independent
leaf acceptance and the provider's substantive corrections remain owed.

## Independent registry acceptance — 2026-09-08, W120519 claim120577

`review-2026-09-08T16-08-40Z.md` accepts only the registry leaf at hash6ea5e9be.
This supersedes the preceding pending-registry-acceptance state and the earlier
claim that the missing registration still blocks runner startup. Independent
exact-byte audit proves the single authorized insertion and unchanged mode;
the retained existing completeness test passes on the identical candidate.
W120519 closes satisfying, and W119114 must reuse the accepted addition.
This is no full-suite or substantive recovery acceptance: W120424, W120425
and W119733's joined provider proof retain their own gates.

## Independent joined acceptance — 2026-09-08, claim121965

Both correction children and the joined six-path provider are now accepted;
`review-2026-09-08T19-39-44Z.md` supersedes the pending provider verdict above.
Its exact-byte audit and linked child evidence are the canonical technical
account. The historical implementation descriptions of mutable cleanup axes,
current checkpoint selection and process-retained publication evidence are
explicitly superseded: committed cleanup, writer-owned frozen checkpoint and
public attempt-only publication history now supply the proof, preserving the
ordinary ending's complete answer. Owner121773's exact test exceptions remain
bounded to the child disposition. W119114 still owes the actual assembled
factory/tick/restart/custody/correction/integration proof; this acceptance
releases the provider gate and does not accept that consumer.
