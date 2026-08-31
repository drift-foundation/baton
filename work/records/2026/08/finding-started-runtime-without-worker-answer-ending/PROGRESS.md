# Progress

Owned by the participant making the implementation change under the W44716
claim.

## 2026-08-30 — first round (`baton.claude`, W44716 impl claim)

Revalidated the contract's named symbols against the tree rather than trusting
them: the sibling `abandon_attempt` mirrors exists in full, nothing in
`worker_manager` was named `abandon` so the new document kinds overload no
existing vocabulary, and the additive red case failed only for the operation's
absence.

## 2026-08-30 — second round (`baton.claude`, W44716 impl claim)

**Implemented, to the pinned contract.** The approver's ruling and the
reviewer's specification were exact enough that this round is the contract
carried out rather than designed.

### What was built, by the record's own patch boundary

`documents.py` — `attempt.abandon-intent`, `attempt.abandonment` and
`destroy.abandoned-command`, each a CLOSED member set and none a union with
the receipt, failed-start or refused-session bodies. Four closed sets mean a
caller holding one authorization cannot spend it on another ending, which is
the rule the second and third siblings were made under.

`oci.py` — `destroy_abandoned`, reusing `_removed`. Force-removal is the
combined stop and remove, so a RUNNING container and a stopped one are one
teardown rather than two, and the result directory is not touched.

`intake.py` — the public `abandon_attempt`, plus three private identities and
the record reader. The declaration identity derives from the attempt and its
fixed assignment ONLY; the reason and the runtime ride the signature, so a
changed reason or a re-attached runtime COLLIDES rather than committing a
second abandonment of one attempt. The authority fence identity is distinct
from both that and `attempt.cancel:*`, because three acts are three
identities.

`__init__.py` — `abandon_attempt` and nothing else. The identity builders and
the record reader stay internal: an ending authorized by a record a caller
could compose is not authorized by anything.

`tools/dogfood_operator.py` — the W44716 unresolved branch is now the real
ending. The deployment calls the public operation and reads no manager
storage and no OCI destroy capability.

### Two decisions worth a reviewer's eye

**The fence is not conditional on the assignment looking dead.** Both siblings
refuse a still-live assignment, because somebody else ended it and they are
settling afterwards. Abandonment IS the act that ends it, so this fences
rather than asking whether somebody already did — which is the ruling's own
order and the one place this operation legitimately differs from the two it
otherwise mirrors.

**`uncertain` is fenced and not cleaned up.** Stopping further authorized
execution is the whole point, so the fence stands; but the manager cannot say
what exists, so there is nothing to prove absent, the lane is not released,
and the refusal says so.

### A defect the reviewer's additive case caught in my operator wiring

`test_an_empty_intake_receipt_still_authorizes_cleanup`: I set the
receipt-exists flag AFTER checking whether the receipt held any artifacts, so
an attempt with a perfectly good but empty receipt fell to the abandonment
ending. **The receipt is the authorization; its contents are not.** That would
have declared a human decision over an attempt the manager could already end
by itself. Recorded the moment intake commits now.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_attempts
    -> 229 tests, OK -- including the additive red case, which now passes for
       the operation's presence rather than failing for its absence.

    PYTHONPATH=src python3 -m unittest tests.manager.test_attempts
      tests.manager.test_intake tests.manager.test_secrets
      tests.manager.test_dependencies tests.manager.test_oci
      tests.manager.test_frozen tests.manager.test_workspaces
      tests.tools.test_dogfood_operator tests.tools.test_parallel_runner
      tests.manager.test_lifecycle_composition tests.manager.test_oci_engine
    -> 753 tests, OK (7 skipped) -- including the real Docker gates.

    The working tree's whitespace check: passed.

`test_secrets` required a §13 accounting entry for the new export, as it does
for every sibling; the statement added is what the operation actually answers.

### What this round did NOT do

The regression matrix the record specifies — replay before and after
settlement, restart between each step, race against reconciliation, a positive
survivor, a mismatched runtime, and the real-engine ending — is not written.
The reviewer's one additive case and the surrounding suites are what stands
behind this round, and that is less than the matrix the contract asks for.

## 2026-08-30 — third round (`baton.claude`, W44716 impl claim)

Correcting review `review-2026-08-30T11-44-55Z.md`. All five findings are
addressed; one of them exposes a contradiction between two of the reviewer's
own cases, which I have NOT resolved by editing theirs.

### [P0] A terminal exact retry changed the public answer's type

`abandon_attempt` now commits the complete `attempt.abandonment` composite as
the journalled result of `runtime.destroy-abandoned`, rather than committing
the inner `cleanup.settled` document and composing the wrapper only for the
first caller. `_settle_recordless_cleanup` is invoked INSIDE the transact
callback and its answer becomes the `cleanup` member of the document that is
committed, so an exact terminal retry replays the identical
`{intent, fenced, cleanup}` object without rereading the removed runtime or
any mutable terminal axis.

### [P0] Ineligibility was declared and fenced before it was checked

Eligibility is now proved atomically with the declaration. `_declared` runs
inside the write transaction and refuses unless `worker_disposition` is
`none`, `output` is `open`, and cleanup is not already terminal -- so nothing
is recorded and nothing is fenced for an attempt whose worker already
answered. The post-fence cleanup check was REMOVED, deliberately: once the
intent is committed, a replayed call must be able to finish what it started,
and re-checking a mutable axis after the fence would strand exactly the
interrupted caller the intent exists to resume.

### [P1] The operation envelope now binds its own id

`_abandoned_destroy_operation` composes `operation_id` once and derives
`signature_digest` over the kind plus operands INCLUDING that id, matching
`destroy_operation`, `failed_start_destroy_operation` and
`refused_session_destroy_operation` rather than merely claiming to.

### [P1] The committed record is adopted whole

`_abandon_intent` now compares all six closed members, including
`authority_operation_id` and `reason`, and the fence is called with the values
read back from the committed record instead of the caller's parallel
spelling. The record is the authorization, so the fence uses the record.

### [P0] No runtime control before the manager fences -- and what it collides with

`dogfood_operator._ended_however` no longer stops the runtime on the
receiptless path. The stop is now gated on `evidence["intake_receipt"]`: the
ordinary receipt-authorized cleanup keeps its established quiescence path, and
abandonment's composite owns its own fence/removal order. The reviewer's new
witness `test_receiptless_abandonment_does_not_stop_before_the_fence` passes.

**This contradicts the reviewer's earlier case.**
`EveryPostStartBranchEntersTheEnding.test_transport_and_disposition_failures_do_not_return_around_ending`
(added by review `2026-08-30T06:44:13Z` [P0]) asserts `len(adapter.stops) == 1`
on the lost-conversation and answered-without-disposition paths. Both are
receiptless, so they are precisely the paths the new [P0] forbids stopping.
The two cases cannot both hold. I have left the earlier case exactly as the
reviewer wrote it, and it is RED -- 2 subcase failures.

What I did instead was hold its *property* under the measure W44716 leaves
available, in an additive case of my own:
`test_conversation_failures_still_reach_the_abandonment_ending`. It drives the
same two conversation failures and proves the started runtime does not return
around its ending -- `abandon_attempt` is entered exactly once, naming the
attempt, with `adapter.stops` empty and `observed_after` recorded. It passes.

The one-line change their case needs is to retire the stop count for the same
entry assertion. **That edit is theirs to make or to authorize; I have not
made it.** Question posted with the pass-back.

### Also corrected

`evidence["observed_after"] = _observed_after(adapter, runtime_id)` is back at
the END of `_ended_however`. An edit had displaced it below the unconditional
return in `_abandonment_reason`, where it was unreachable and referred to
names that function does not have.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_attempts
    -> 231 tests, OK -- including all three of the reviewer's additive
       witnesses for the two manager P0s and the composite replay.

    PYTHONPATH=src python3 -m unittest tests.manager.test_attempts
      tests.manager.test_secrets tests.manager.test_dependencies
      tests.tools.test_dogfood_operator tests.tools.test_parallel_runner
    -> 448 tests, FAILED (failures=2, skipped=1).

       The two failures are the two subcases of the superseded case named
       above, and nothing else. Every other case in the sweep passes.

### What this round still did NOT do

The dossier matrix remains unwritten: interruption before/after intent, fence,
removal and terminal commit; uncertain, surviving and mismatched runtime;
provider endings; changed reason, runtime and policy; record corruption; and
the real OCI ending. This round spent itself on the five review findings.

## 2026-08-30 — fourth round (`baton.claude`, W44716 impl claim)

Correcting review `review-2026-08-30T11-56-53Z.md`, and finally writing the
matrix the record has required since the Work was filed.

### [P0] A newly derived cleanup could revisit a finished ending

The reviewer is right and my previous round's reasoning was too broad. Skipping
the mutable eligibility for a REPLAYED INTENT is correct; I extended that to
every destroy operation later derived from that intent, and those are not the
same thing. The retention policy rides the destroy identity but not the
declaration, so a second policy over an already-settled attempt missed the
outer replay and went on to fence and remove again, refusing only afterwards
inside `_settle_recordless_cleanup`.

The distinction the intent replay protects is narrower than I had it. An
INTERRUPTED same-policy call has no terminal cleanup result — its axis is
still pending or blocked-on-intake, and it is exactly the caller that must be
allowed to finish. A COMPLETED same-policy call is caught by the exact replay.
So a terminal axis after the replay miss can only mean a newly derived cleanup
arriving after some ending already happened. That refuses now, before the
authority is touched and before the engine is called, reading the axis fresh
rather than trusting the read taken at entry.

### The matrix, written

`TheAbandonmentEndingSurvivesInterruptionAndDrift` in
`tests/manager/test_attempts.py` — 13 cases, one per row the record names.

Interruption, each with a real manager restart over the same control store:

- interrupted AT the fence — the resumed call reuses the committed
  declaration, and the two authority calls carry the SAME operation, so the
  authority sees one operation retried rather than two cancels;
- interrupted AT the removal — the resumed call fences with the adopted
  record's own values and removes once;
- interrupted BEFORE the terminal commit — nothing is journalled, so the
  removal is redone rather than assumed, and the terminal result is replayable
  thereafter;
- interrupted AFTER the terminal commit — replay answers from the journal,
  re-fencing nothing, re-removing nothing, rereading no removed runtime.

The runtime the engine actually reports:

- an `uncertain` axis is fenced and deliberately NOT cleaned up — the fence is
  the point, and claiming absence would be a lie;
- an `uncertain` removal answer is not an ending: `cleanup.unsettled` carries
  no cleanup member at all, and the axis does not move;
- a `running` answer after force-removal settles `failed`, not `retained` —
  `retained` means material kept on purpose, and a surviving container is not
  that, so the lane does not go back into circulation on it;
- an answer about another runtime is refused as `identity-mismatch`.

Deliveries: an `unresolved` provider ending holds the ending open —
`execution_runtime` moves to `destroyed` because that is true, `cleanup` stays
pending because that is not, and a retry finishes it.

Operands that changed between calls:

- a changed REASON collides rather than declaring twice: the reason rides the
  declaration's signature, so a differently-worded second declaration of one
  attempt is `operation-collision` and the operator is told rather than the
  journal quietly acquiring a second account;
- a changed POLICY before settlement is a retry, not a re-fence — a new
  destroy identity, one authority operation, and the removal carries the
  policy it was actually called with;
- a runtime RE-ATTACHED after the declaration also collides, one step earlier
  than the member comparison, because the runtime rides that same signature.

Record corruption: a declaration edited underneath the manager — corruption, a
restore, a hand at the sqlite prompt — fails the six-member adoption and
authorizes nothing.

### The real engine

`tests/manager/test_abandoned_attempt_engine.py`, registered SERIAL, 4 cases
against a real daemon, inheriting the lifecycle gate that FAILS rather than
skips without one.

The fact only a daemon supplies is the one that separates this ending from its
three siblings: THE CONTAINER IS RUNNING. A failed start has no container, a
refused handshake has one that was refused, an intake receipt has one whose
worker answered. So the gate starts a real container, confirms with the daemon
that it is up, and abandons it: the acceptance, the fence taken while the
container is still running, replay across a manager restart, and the new
policy refusal — each verified by asking the daemon separately, because the
adapter's own answer is the thing under test and cannot also be the evidence
for it.

I checked it is not vacuous rather than assuming it: with `destroy_abandoned`
swapped for one that answers `absent` without removing anything, the
acceptance case FAILS on the daemon question. Removed the throwaway after.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest
      tests.manager.test_attempts tests.manager.test_intake
      tests.manager.test_secrets tests.manager.test_dependencies
      tests.manager.test_oci tests.manager.test_frozen
      tests.manager.test_workspaces tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_lifecycle_composition
      tests.manager.test_abandoned_attempt_engine
      tests.manager.test_refused_session_engine tests.manager.test_oci_engine
    -> 783 tests, OK (8 skipped), including the real Docker gates.

    py_compile passed on every changed module; the whitespace check passed.

Registering the new gate also required its mirror in
`tests/tools/test_parallel_runner.py`, which pins the serial tuple exactly. It
is APPENDED, so no existing member moves.

### What remains

The race against reconciliation is covered only through its observable
consequences — the `uncertain` axis case and the interrupted-removal case —
rather than by driving `reconcile_runtime` concurrently. I did not write a
threaded race case, and say so rather than letting the row look closed.

## 2026-08-30 — fifth round (`baton.claude`, W44716 impl claim)

Correcting `review-2026-08-30T12-10-41Z.md`. The reviewer wrote the race case
I had reported as not done, and it was red — the row I left open was open
because the code was wrong, not only because the case was missing.

### [P0] The gates were applied to a row read before the fence

I moved the cleanup precondition to a fresh read and left the uncertainty gate
reading `attempt`, the snapshot taken at ENTRY — before the declaration,
before the destroy replay, and before `AuthorityPort.cancel`. Reconciliation
is an independent manager operation. If it revokes the positive runtime
observation while the fence is in flight, the abandonment crossed the
destructive boundary on a `running` row that had already been withdrawn, and
the conflict surfaced only during settlement as a refused state regression.

**A refusal after the removal is not a refusal.** The authority call is the
one place this operation waits on somebody else, so the world is now read
again immediately after it and immediately before any runtime control, and
that read is the last thing between the fence and the engine.

Three gates apply to that current row:

- `uncertain` — the reviewer's specified case. The fence stands, because
  stopping further authorized execution is the whole point; nothing is
  removed, nothing is proved absent, the lane is not released.
- terminal cleanup — the other half of the same window. The pre-fence check
  cannot see an ending that lands DURING the authority call, and an ending is
  not revisited however narrow the window was.
- the runtime the declaration names. The adopted record authorizes destroying
  ONE container; a row that names another by the time the fence returns is not
  the world that record was written about.

The destroy and the unsettled-ending reading both take the current row now,
rather than the entry snapshot.

Only the first of those three was covered by the reviewer's witness, so I
added the other two: `test_an_ending_that_settles_while_fencing_is_not_revisited`
and `test_a_runtime_reattached_while_fencing_is_not_the_one_declared`. Both
drive the change inside the fence callback, as the reviewer's does.

### What I got wrong in the fourth round's report

I wrote that the reconciliation row was "covered through its observable
consequences" by the static already-uncertain case. It was not. A static
starting state and a state that changes mid-operation are different facts, and
the second one is the whole reason the row is in the matrix. Reporting the gap
was right; reasoning that the existing cases stood in for it was not.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest
      tests.manager.test_attempts.ExplicitAbandonmentFencesBeforeItRemoves
      tests.manager.test_attempts.TheAbandonmentEndingSurvivesInterruptionAndDrift
      tests.tools.test_dogfood_operator.EveryPostStartBranchEntersTheEnding
    -> 22 tests, OK, including the reviewer's race witness.

    The thirteen-module sweep, including the real Docker gates
    -> 786 tests, OK (8 skipped).

    py_compile passed on every changed module; the whitespace check passed.
