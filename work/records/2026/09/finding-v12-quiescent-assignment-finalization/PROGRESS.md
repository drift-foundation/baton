# Progress

Not started until 2026-09-01. The run5b evidence was recorded and
implementation deferred until this Work was explicitly selected for its own
isolated v12 attempt.


## 2026-09-01 — first implementer round (`baton.claude`, W61984 impl claim)

**PLAN item 4 is implemented: one public, journalled already-quiescent
assignment-finalization operation, one explicit dogfood mode over it, and a
focused suite. PLAN item 5 (independent review) is not started, and this is
passed back for it rather than closed.**

Baseline: the exact clean tree at `bb780dccaa736782a16a581dc7d16a0620c8267d`,
which is the working copy this round edited.

### Revalidation before any edit

**The reviewer's current-tree map still holds.** I re-read every symbol the
`evidence/research-2026-09-01/README.md` names and each is where it says:
`attempts.request_cancellation` fences, then orders the agent, then the
runtime; `intake.authorize_cleanup` refuses while the fixed assignment is
live; `dogfood_operator._custody` raises on a nonzero independent status
before retention and the review pass; `_ended_however` goes from there
straight to `authorize_cleanup`; `authority.core.cancel`'s effect reaches this
manager through `AuthorityPort.cancel`, which already refuses an answer whose
assignment is not the exact four-part one or whose `fenced` is not `True`.

**W61599's overlap is preserved rather than overlaid.** Its slice is already
in this tree and untouched by this round: `SCHEMA_VERSION` 14, the
`activity_bytes`/`activity_at` columns, `attempts.observe_activity`,
`attempts.attempt_activity_of`, their exports, their §13 accounting entries,
their text-sweep rows, their `bytes_observed` operand declaration, and
`dogfood_operator._Channel`/`_activity_observer`. My `attempts.py` change is a
new block after `_order_quiescence` and two names in `__all__`; my
`dogfood_operator.py` change is a new function, a new builder, a new flag pair
and a new branch in `main`. Nothing of W61599's was moved, rewritten or
re-derived. No retained proposal was imported or stacked, and no v11 product
code was touched.

**One clarification I re-confirmed rather than assumed:** the reviewer is
right that `observed_after.candidates` recorded the exact runtime as
`quiescent` with its mounts still listed, so "no container remained" is not a
positive-absence fact. Everything below uses the stronger reading — only
`destroyed` is absence.

### What was added

`worker_manager.finalize_quiescent_assignment(store, port, *, attempt_id,
reason)` — the whole public surface, and the signature is the argument. It
takes NO agent and NO runtime adapter, so it cannot contact either; a test
asserts the parameter list rather than trusting the docstring.

The order, and each step is the next one's precondition:

1. own the two operands (`boundaries.identity`, `boundaries.text`, non-blank,
   `MAX_FINALIZATION_REASON = 2000`), then the immutable facts: the attempt
   exists, activation fixed an assignment, the session's binding IS that
   assignment's participant, and a runtime is attached to name;
2. commit or replay `attempt.finalize-quiescent` — attempt id, four-part
   assignment, runtime id, the constant `finalized`, the recorded terminal
   disposition, the authority operation id and the operator's reason — with
   the two MUTABLE facts decided INSIDE that write: the disposition is one of
   `schema.DISPOSITIONS` (so `none` refuses) and `execution_runtime` is
   exactly `quiescent`;
3. adopt the committed record, compare all seven members against this call's
   own operands, and fence with the RECORD's authority operation id and
   reason through the existing `AuthorityPort.cancel`.

Nothing follows the fence. No agent call, no runtime stop, no freeze, no
intake, no retention, no verification, no review pass, no approval, no
integration, no cleanup and no observation. A case reads all ten lifecycle
axes before and after and requires them identical.

`documents.py` gains the two closed shapes (`attempt.finalize-intent`,
`attempt.finalized`) and `FINALIZE_INTENT` for reading the record back.

### The identities, and why there are two more of them

`attempt.finalize-quiescent:<digest of attempt + assignment>` is the manager's
decision; `authority.finalize-quiescent:<same operands>` is the authority's
act. The reason, the runtime and the disposition ride the SIGNATURE rather
than the identity, so a second decision with a different sentence collides
instead of committing a second finalization. Both are distinct from
`attempt.cancel:*`, `authority.attempt.cancel:*`, `attempt.abandon:*` and
`authority.abandon-fence:*` — six identities because they are six acts.

Because the decision commits BEFORE the fence, a crash at the authority leaves
a record naming the one act still owed; the retry reissues that same authority
operation rather than forming a second decision. Cases drive exactly that: a
raising session, then a working one; and a second `ControlStore` incarnation
over the same file.

### `request_cancellation` is untouched

Its fence-agent-stop order is right for a cancellation that INITIATES
quiescence and its own test still pins it; this suite re-pins it too, so a
later edit that "unified" the two would fail here as well.

### The dogfood mode

`dogfood_operator.finalize_quiescent(store, port, given, *, reason)` plus
`--finalize-quiescent --finalize-reason`, built by `_for_finalization`, which
opens the control store, takes the one atomic `attempt_runtime_of` projection,
holds the editable grants against it with the existing `_assignment_disagrees`
and only then opens an authority session. It constructs no engine port, no
adapter, no credential home, no orphan teardown, no launch adoption and no
workspace roots — the same "bounded by what it was handed" argument, one layer
out. The record is the existing closed `RECOVERY_MEMBERS` document with
`branch: "quiescent-finalization"`; `runtime`, `cleanup`, `custody`,
`credentials`, `launch`, `observed_after` and `zombies` stay null because this
command observed none of them.

**Ordinary failed verification still does not finalize.** `_custody` and
`_ended_however` are unchanged, and a case reads the source of the eight arc
and recovery functions and requires that none of them names the operation.
The finding's required supersession therefore does not bite yet:
`test_failed_independent_verification_never_passes_to_review` is unedited and
still true, because the ordinary attempt does remain live until an operator
makes the explicit decision.

### Inventory updates, and why exactly these

- `worker_manager/__init__.py` — the import and the one export.
- `tests/manager/test_secrets.py` — the §13 accounting entry the exported
  surface requires (`RETURNS_NO_CONSTRUCTED_ARTEFACT`).
- `tests/manager/test_text_sweep.py` — the exhaustive exported-callable table,
  with both text operands declared.
- `tests/manager/test_boundary_inventory.py` — `STATED_OWNERS` and `WITNESSES`
  for the two new outbound constructors, and the two caller probes.
- `tools/user_credentials.py` + its test's mirror registry — the new mode is
  added to `ENDING_MODES`, because it opens no registry and no source and an
  operand naming material to deliver is a contradiction in it exactly as it is
  in the other two. This renames one existing assertion
  (`test_the_two_ending_modes_are_the_documented_two` ->
  `..._are_the_documented_ones`) and widens its tuple; it is an additive
  registry member, and the two cases that iterate `ENDING_MODES` now cover
  three modes without editing.

### Verification

I could not execute anything in this container: every `python3` invocation
beyond `--version` was refused by the harness policy, so the supplied focused
command

    python3 v12/python/tests/tools/test_quiescent_assignment_finalization.py -v

was **written but not run by me**. That is stated plainly rather than implied:
the suite is authored against the current fixtures (`tests.manager.
test_attempts.AttemptCase`, `Adapter`, `Agent`, and `tests.manager.
test_offers.FakeSession`) and the real control store, authority port and
journal, and it has not been observed passing. The reviewer's baseline pair
(`EveryPostStartBranchEntersTheEnding.
test_failed_independent_verification_never_passes_to_review` and
`CancellationFencesBeforeItStops.test_the_agent_is_ordered_before_the_runtime`)
is likewise unverified this round, though neither function was modified.

`tests/manager/test_boundary_inventory.py` was already failing on this
baseline for reasons that predate this Work — W44716's `abandon_attempt` and
its documents carry no entries there at all, which is what W61599's own record
counted among its five pre-existing failures. I added this boundary's entries
and did NOT attempt to repair the pre-existing gaps, which are somebody's
separate finding rather than this one's.

### NOT DONE, named rather than left to inference

- running any test, for the reason above;
- PLAN item 5's independent review;
- any automatic finalization policy — the specification still says an `unable`
  result waits for an explicit decision, and changing that is a separate
  ruling;
- anything about cleanup, retention or positive absence: those operations are
  unchanged, and cleanup still refuses until the assignment is over AND every
  custody artifact has an explicit retention decision.

### State

Awaiting independent review of the finalization slice. Passing back rather
than closing.


## 2026-09-01 — bounded repair of the retained attempt-6 proposal (`baton.claude`)

**Subject:** retained W61984 attempt-6 proposal
`sha256:5157bae48ef063ecf8b063e4dee399067b4570d3027cfddaaac7e329caacf2ac`.

**Scope, and it was not exceeded.** One test file was edited —
`v12/python/tests/tools/test_quiescent_assignment_finalization.py` — plus this
entry. No production code was touched: not `worker_manager/attempts.py`, not
`documents.py`, not `tools/dogfood_operator.py`, not any inventory or
accounting file. No other case in the suite was edited.

### The one defect repaired

`TheQuiescentAssignmentIsEndedAndNothingElseIs.
test_no_runtime_is_stopped_and_no_agent_is_asked` asserted
`self.adapter.observed == []`. That is a false claim about the FIXTURE rather
than about the operation under test: `quiescent()` calls
`request_runtime_start`, which legitimately records a setup observation on the
adapter before finalization is ever reached. The empty-history assertion could
therefore only ever have failed, and it would have failed for a reason that
says nothing about `finalize_quiescent_assignment`.

The repair keeps the case's actual subject — that finalization contacts
neither boundary — by making it a DIFFERENCE rather than an absolute:
`before = list(self.adapter.observed)` is snapshotted immediately after
`self.quiescent()`, and the post-condition is
`self.assertEqual(self.adapter.observed, before)`. Finalization must add
nothing to the history the setup already wrote. The sibling assertions
(`stopped == []`, `agent.cancelled == []`, and the `execution_runtime` axis
still reading `quiescent`) are unchanged, because those ARE absolutes: the
setup orders no stop and asks no agent, so an empty list is the honest claim
there.

Deliberately NOT done: the assertion was not deleted, and it was not weakened
to a length or membership check. A snapshot comparison is strictly stronger
than either — it would catch a finalization that appended, replaced or
reordered an observation.

### Verification — NOT RUN, and this is the same wall as the first round

The supplied focused command

    python3 v12/python/tests/tools/test_quiescent_assignment_finalization.py -v

was **not executed**. Every `python3` invocation carrying arguments beyond
`--version` is refused by this container's harness policy; `python3 --version`
answers (3.11.2), `python3 -m py_compile <the edited file>` is refused, and the
focused command itself is refused. The edit is therefore reviewed rather than
observed: it is a two-line change in one method, using only `list()` over an
attribute the fixture (`tests.manager.test_attempts.Adapter.observed`) already
initialises to a list, so it introduces no new import, name or fixture
dependency. It has not been seen passing, and no claim is made here that it
does.

Because nothing ran, this round also could not distinguish the repaired
assertion from any OTHER failure the suite may still hold. If the focused
command is run by a reviewer with execution rights and fails somewhere other
than this case, that failure is not addressed here and was not looked for.

**No production failure was exposed by this round**, because no test was
executed to expose one. The stop-and-report instruction did not trigger; it
was also never given a chance to.

### State

The single named defect is repaired and this remains awaiting PLAN item 5's
independent review, now with execution of the focused suite as an explicit
outstanding item rather than an assumed one.


## 2026-09-02 — bounded repair of the reviewed run8 proposal (`baton.claude`, impl)

**Subject:** retained W61984 run8 proposal
`sha256:3b85e275fc58451c0b9ee95af8649039a0f2dc25e3ff0ae0fb7cc3039cac01d3`.
**Response to:** the append-only review named as
`review-2026-09-01T22-53-21Z.md` in this record root, and its ONE P1.

### The review file is NOT in this working copy, and that is stated first

`work/records/2026/09/finding-v12-quiescent-assignment-finalization/` in this
private copy holds `FINDING.md`, `PLAN.md`, `PROGRESS.md` and
`evidence/research-2026-09-01/README.md` and no `review-*.md` at all. The only
review pass anywhere in the tree is
`work/records/2026/09/finding-live-worker-log-observability/review-2026-09-01T14-24-19Z.md`,
which is another record's. The search was confined to the working tree because
this container refuses any path outside it.

So this round could not read the review's own words. It worked from the P1 as
the handoff stated it — represent `attempts.py:_finalization_record`'s adopted
committed finalization record as a receiving trust-domain entry, assign its
validator exactly once, add a probe that substitutes or corrupts the replayed
`attempt.finalize-intent` and proves validation refuses before any authority
`port.cancel`/fence, and add no new orphan validator call against the recorded
baseline of 34. **A reviewer should confirm that this is the whole of the P1**;
if the review carries qualifications this entry does not answer, they were not
seen rather than declined.

### The defect, re-derived against the current tree

`attempts._finalization_record` adopted the journalled decision with

    held = boundaries.document(committed, "a committed finalization record",
                               required=documents.FINALIZE_INTENT)

and `committed` is bound from `store.transact(...)`. `test_boundary_inventory`
discovers each domain from a structure no validator defines — public
parameters, capability calls, SQL reads — and a control-store return is none of
the three:

- `_source` resolves `<name>.<method>(...)` only for `PORTS` (`port`),
  `boundaries.*`, `fetchone`/`fetchall`, and helpers listed in
  `_helper_returns()`. `ControlStore.transact` returns `own(result, ...)` and
  `own` is imported from `boundaries.py`, which `_sources()` EXCLUDES, so
  `transact` never enters `_helper_returns()` and `committed` gets no origin.
- `_subject` therefore reported the bare local name `committed`, and `_claims`
  only ever produces `caller:*`, `read:*` or `session:*` stems. No entry could
  answer for it.
- `_finalization_record` is private, so its parameters are not receiving
  entries either (PLAN 4bz), and `_calls_in` propagates only `session:`/`read:`
  subjects to the public caller.

The call was consequently a boundary call attributed to no entry — the 35th
orphan against the recorded 34. The four sibling `store.transact` adoptions in
this package (`intake._abandon_intent`, intake's refusal and cleanup records,
and the two workspace configurations) are unmodelled in exactly the same way
and are part of that pre-existing 34; **this round did not touch them.** They
are somebody's separate finding, and widening the inventory's discovery to see
journal replays would have added an unowned, unprobed entry at all seven sites
that bind a `transact` result — a blast radius a bounded repair does not get to
take.

### What was changed, and it is three files

**1. `v12/python/src/baton_v12/worker_manager/attempts.py`** — the crossing is
given a site of its own:

    def adopt_finalization_record(record):
        held = boundaries.document(record, "a committed finalization record",
                                   required=documents.FINALIZE_INTENT)
        return dict(held)

and `_finalization_record` now calls it instead of owning inline. The operand
name is `record`, which is already a declared operand in
`tests/manager/test_dependencies.py`'s `OPERANDS` table (under "the boundary
layer"), so the public-parameter gate needs no edit. The function is
DELIBERATELY NOT added to `attempts.__all__` or to
`worker_manager/__init__.py`: the package's exported surface is unchanged, so
`test_secrets`'s §13 accounting and `test_text_sweep`'s exported-callable table
— both driven from `worker_manager.__all__` — are untouched.

Why public at all, said plainly rather than left to inference: the inventory
excludes a private function's parameters on purpose, so a receiving site that
stays private cannot be held to having an owner and a probe. The docstring
states that reason in the code, because a later reader who "tidies" the
underscore back on would silently reopen the orphan.

`return dict(held)` is load-bearing twice over and both are recorded here: it
hands the caller a mapping this operation owns rather than an alias of the
journal's answer, AND it stops `_returned_origins` propagating a `caller:record`
origin out through `_finalization_record` into
`finalize_quiescent_assignment`, which would have made
`record.authority_operation_id` and `record.reason` two further unowned
entries. If that line is ever removed, those two entries appear and the
inventory says so — which is the right failure, not a silent one.

**2. `v12/python/tests/manager/test_boundary_inventory.py`** — the entry's one
probe, in `probes()` beside the two W61984 caller operands, plus `attempts`
added to the existing module import. The probe drives
`attempts.adopt_finalization_record(7)` directly, the same way the workspace
and OCI probes drive their exported rules, and requires the refusal to name the
label.

**3. `v12/python/tests/tools/test_quiescent_assignment_finalization.py`** — the
new `AReplayedDecisionIsProvedBeforeTheAuthorityIsAsked` class, which is the
probe the P1 asked for. It reaches the state a crash between the two boundaries
leaves (`session.fence_answer` set to a `RuntimeError`, so the decision commits
and the fence faults), rewrites `operations.result` for the
`attempt.finalize-quiescent` row through a SECOND sqlite handle — same identity,
same kind, same signature, different bytes — and then resumes:

- a member dropped from the replayed record → refused at
  `a committed finalization record`;
- an unnamed member added → refused at the same owner;
- a well-formed record naming another `runtime_id` → refused at the member
  comparison;
- another `reason`, and another `authority_operation_id` → the same;
- and a CONTROL that rewrites the record with the bytes it already held and
  requires the resume to fence exactly once more, so the five refusals are not
  passing because the resumed path refuses everything.

Every one of the five takes `len(self.fences())` before the resumed call and
requires it UNCHANGED after — `fences()` reads the fake authority session's own
call log, and `FakeSession.cancel` appends before it answers or raises, so an
unchanged count is a positive statement that the authority was never asked.
Each also requires the journal to still hold exactly one row.

Nothing else in the suite was edited. The run8 test repair is preserved
verbatim: `test_no_runtime_is_stopped_and_no_agent_is_asked` still snapshots
`self.adapter.observed` into `before` and compares against it.

### What was NOT changed

- No accepted finalization semantics. The order is still own the operands, then
  commit or replay the decision with the two mutable facts decided inside the
  write, then adopt the record and fence with ITS values; the operation still
  takes no agent and no runtime capability; `request_cancellation` is untouched;
  no output, custody, retention, review or cleanup decision was added or moved.
- No dossier file other than this `PROGRESS.md`. `FINDING.md` and `PLAN.md` are
  unedited — this round records no new ruling, only a response.
- No unrelated production file. `documents.py`, `store.py`, `intake.py`,
  `dogfood_operator.py`, `user_credentials.py` and every inventory/accounting
  registry other than the one probe entry above are as run8 left them.
- No import of a retained proposal and no Git mutation of any kind.

### Verification — the commands, and what each of them actually did

**None of them ran.** This container authorizes `python3 --version` and refuses
`python3` with any other argument. Reported exactly:

    $ python3 --version
    Python 3.11.2

    $ python3 v12/python/tests/tools/test_quiescent_assignment_finalization.py -v
    This command requires approval

    $ python3 /tmp/dogfood-a2rek0ch/candidate/v12/python/tests/tools/\
      test_quiescent_assignment_finalization.py -v
    This command requires approval

    $ python3 -m py_compile v12/python/src/baton_v12/worker_manager/attempts.py
    This command requires approval

    $ python3 -m pytest --version
    This command requires approval

The same refusal was returned with the harness's sandbox override set, so it is
a permission decision rather than a sandbox one. Per the non-interactive-turn
rule this was not retried as a stronger command and no approval request was
manufactured; the blocker is reported here instead. Note also that this
interpreter is 3.11.2 while the distribution declares
`requires-python = ">=3.13"` and `just version` refuses below 3.13, so even an
authorized run in THIS container would not be the gate's own interpreter.

**The narrow checks a reviewer with execution rights should run**, and exactly
these — the focused suite plus the two boundary-inventory assertions that carry
the candidate-specific delta:

    cd v12/python
    python3 tests/tools/test_quiescent_assignment_finalization.py -v
    PYTHONPATH=src python3 -m unittest -v \
      tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner
    PYTHONPATH=src python3 -m unittest -v \
      tests.manager.test_boundary_inventory.EveryProbeProvesItArrived.\
test_every_owned_entry_has_exactly_one_probe
    PYTHONPATH=src python3 -m unittest -v \
      tests.manager.test_dependencies

`EveryReceivingEntryHasOneOwner` is where the delta shows:
`test_every_boundary_call_belongs_to_an_entry_or_is_declared` should report
**34** orphans and not 35, and none of the 34 should name
`attempts.py:_finalization_record` or `attempts.py:adopt_finalization_record`.
`test_every_receiving_entry_has_an_owning_validator` and
`test_no_entry_is_owned_twice` should be no worse than the recorded baseline.
That class is ALREADY RED on the baseline for reasons that predate this Work —
W44716's `abandon_attempt` documents carry no entries there — and this round did
not attempt those.

**So the claim made here is exactly this and no more:** the delta is reasoned
statically against the inventory's own rules, which were read in full for this
purpose (`receiving_entries`, `_source`, `_origins`, `_returned_origins`,
`_subject`, `_claims`, `_owned_here`, `owning_validators`, `_calls_in`,
`_delegations`, `expected`, and the four gates above). It has NOT been observed.
If the focused suite fails anywhere, this entry is what says the failure was not
excluded by a run.

### State

**Awaiting independent review** (PLAN item 5), passing back rather than closing.
Two outstanding items are named rather than implied: execution of the focused
suite and the narrow inventory checks above, and confirmation that the P1 as
restated in the handoff is the whole of what
`review-2026-09-01T22-53-21Z.md` asked for, since that file is absent from this
working copy.
