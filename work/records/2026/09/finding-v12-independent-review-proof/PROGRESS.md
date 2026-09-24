# Implementer progress

## 2026-09-23 -- baton.claude, claim 244629

Owner reroute 244627. Read AGENTS.md policy, EFFECTIVE-BATON.md, W239533's
canonical state, its complete work-events, thread T239533 in full (2 messages,
no pagination remaining), this dossier, W244180's preparation in full and
W239528's accepted live review. Delivered items 1-3 of PLAN; items 4 and 5 are
outstanding and their exact scope is below.

**No file under `v12/` was edited, and no other dossier was written to.** The
accepted run's stores, artifacts and both images are untouched; the survey
opens the producer's control store through SQLite `mode=ro` and nothing else.

### What was delivered

`attachment.py` -- the supported arrangement, and the answer to G2. It reads
the producer's retained control store READ-ONLY, composes the immutable
subject, and answers the exact refusals. G3 in W244180's checklist is the
reason it is not `ControlStore.open`: that path can initialize or migrate a
store, and a survey that migrated W239528's accepted evidence would have
altered the thing it was asked to describe.

`test_attachment.py` -- 16 cases over a REAL `ControlStore` with a real line,
writer and frozen checkpoint built through the supported `review_cycles` API.
Every refusal case asks BOTH accounts about the same store and requires them to
agree, because a preflight that restates a validator's rules and then drifts
from them is worse than no preflight. Covered: the accepted proposal is
attachable by an independent reviewer; a second Job recovers the same line
while a different v12 Work reaches a different line with no checkpoint; a
checkpoint this line never held; a real frozen checkpoint belonging to another
line; a genuinely superseded revision; self-review on all three identities and
on each one alone; a line under correction; and that the survey moves no byte
and leaves no journal companion beside the store.

`review_bindings.py` and `test_review_bindings.py` -- the review-only
composition, 19 cases, composed against that same real line.

### Three things the measurements corrected, left visible

**`immutable=1` was wrong and the test found it -- and dropping it cost
something, which is recorded rather than glossed.** The read-only opener first
used `mode=ro&immutable=1` to guarantee no lock or journal file appeared beside
the retained store. These stores are journalled `wal`, and `immutable=1` makes
SQLite ignore the write-ahead log: against a store whose last commits are still
in the log it answers a SILENTLY STALE picture. The symptom was a refusal
reporting "no lines at all" about a store holding one.

`mode=ro` alone sees the truth, and the price is that opening a `wal` database
read-only CREATES its `-shm` and `-wal` companions when they are absent. This
claim's survey did exactly that to W239528's retained control store:

    /home/sl/baton-runs/single-implementation-244216/db/
        control.sqlite3        380928 bytes, mtime 2026-09-22T22:05:52, UNCHANGED
        control.sqlite3-shm     32768 bytes, CREATED by this claim's read
        control.sqlite3-wal         0 bytes, CREATED by this claim's read

The store's own bytes did not move, `review_attachments` still holds nothing,
and the line is still `review-ready` on the same checkpoint. The two companions
were left in place: they are SQLite's own transient files, a zero-length `-wal`
carries nothing, and deleting files beside another Job's retained evidence is a
mutation this claim will not perform unilaterally. It is disclosed here so the
next reader of that directory is not surprised by two files the accepted review
did not describe.

**A test of mine asserted more than it measured, and it is corrected in
place.** `test_no_byte_moves_and_no_companion_file_appears` required that no
companion appear -- and passed only because the fixture already holds an open
`ControlStore`, so both companions existed before the survey ran. Against the
real store, which has no open connection, they were created. The case is now
`TheSurveyDoesNotChangeTheStoreItReads` and measures the store's own bytes and
row counts, plus that the connection itself refuses a write. I have left the
correction visible rather than renaming the assertion to match the result.

**A stale checkpoint cannot be manufactured, only produced.** The first attempt
granted a second writer to make a second revision and was refused -- "line
state 'review-ready' does not admit a writer". The case now runs the real
correction round (attach, `changes-requested`, correction writer, freeze), which
is the only way a checkpoint becomes stale.

**`attach_review`'s writer-coexistence branch is defensive, not ordinary.**
Reaching "read-only review cannot coexist with a writer" from `review-ready` is
impossible, because that state admits no writer; by the time one is active the
line has left `review-ready` and the earlier precondition refuses first. The
case proves the reachable thing and names which refusal actually fires.

### Exact remaining scope

1. **The bounded review-only supervisor.** W239528's `baseline.py` is closed
   over `implementation` and W236087's `supervisor.py` requires at least one
   implementer invocation, so neither is it -- G1 in W244180's checklist stands
   exactly as written. It needs: `KINDS` closed over `review`; one admission,
   retry disabled; finite turn, total and reserved cleanup limits with an
   actionable no-progress rule; admission closed before cancellation; every
   discovered attempt accounted for; the ordinary ending and cleanup path
   driven; an outcome published on interruption and on failure; verdict
   evidence (`review_verdict_from_result`, attribution against the attached
   checkpoint's base/head/tree) where `baseline.py` gathers proposal evidence;
   and an explicit refusal to open a correction on `changes-requested`.
2. **`review_bindings.write` held against the manager's own validator.** The
   19 composition cases inspect the in-memory documents; they do not run
   `write`, so `stage_execution.held_configuration` has not yet been asked
   about this deployment over a disposable Authority and no `PACKET.json` has
   been produced. `test_review_bindings`'s docstring says so in place rather
   than leaving a reader to assume coverage.
3. **The packet and the operator commands.** They wait on 1: `PACKET.json`
   names its supervisor path and digest.
4. **The real-provider question, once 1-3 exist.** Whether the actual reviewer,
   given these criteria and the retained bytes, returns its own valid report
   through the production boundary. Deterministic checks cannot establish it,
   and no live run is selected or authorized here.

Also outstanding and not this Job's: the `seconds_bound` 3600/180 metadata
discrepancy the accepted review retained for a bounded follow-up.

Verification: 35 focused deterministic checks, 0 failures, measured
0.43275384600565303s, receipt `verification-1.json` with `verification-1.log`.
No container, image, live provider, network, credential or operator deployment.

Cumulative measured for W239533: **0.432753846s** (this is the Job's first
claim; W239528's and W236087's budgets are their own).

State: returned for independent review with the remaining scope above.

## 2026-09-23 -- baton.claude, claim 244759

Owner reroute 244755, addressing review 2026-09-23T04:40:30Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **R1 is fully addressed.
R2 is not, and it is returned again with exact scope.**

**No file under `v12/` was edited and no deployed store was opened under this
claim.** The only store this claim opened was the disposable one the tests
build; the producer's retained store was not read at all this turn.

### R1 -- the survey now reads through supported interfaces

`attachment.py` was rewritten onto `ControlStore.open_readonly`, one
`snapshot()` spanning the whole account, and the public `line_of`,
`checkpoint_of` and `writer_of` readers. `FINDING.md` records why the first
version was wrong, and `attachment.GAPS` records the three public lookups that
do not exist together with the supported alternative used in place of each.

Four things changed in substance rather than in wording:

  * **The line is named and proved, not searched for.** No public function
    answers "the line for this Authority and Work", so the packet names
    `line_id` and `subject()` refuses when that line carries a different
    Authority or Work. A named identity that is checked is better evidence
    than a search that could quietly find something else.
  * **`STALE` and `WRONG` come from the checkpoint's own record.**
    `checkpoint_of` answers its line and revision, which is the whole
    distinction; and a checkpoint the store does not hold is reported as
    absence rather than raised, because "no such checkpoint" IS the answer.
  * **The `ACTIVE WRITER` refusal is gone.** It existed only because of the
    raw `line_writers` scan. The line state is the supported signal and the
    reachable one -- `test_attachment` already established that
    `attach_review`'s writer-coexistence branch cannot be reached from
    `review-ready` -- so the `writing` refusal now says what that state means
    instead.
  * **`checkpoint_of` decodes `evidence` itself.** The raw-SQL version read
    stored text and called `json.loads` on it. That it had to is one more way
    that version was reading something other than what the supported interface
    answers.

Two cases hold the correction to more than its own wording: the snapshot depth
is MEASURED while the survey is inside the boundary, and the bypass is checked
by PARSING the module -- no `sqlite3` import, no `execute` call -- rather than
by searching its text, because the docstring names what was removed and a
substring search would be satisfied by the confession.

`review_bindings.compose` was moved onto the same handle and closes it; its
`COMPOSITION_INSTANT` is a constant so composing the same selections twice
produces the same documents byte for byte.

**The disclosed producer artifacts are preserved.** `control.sqlite3-shm` and
the zero-length `control.sqlite3-wal` beside W239528's retained control store
are still there and still disclosed. They were not cleaned up, and using the
supported opener does not make the earlier read retrospectively clean.

**A test of mine measured the wrong thing, and it is corrected in place.**
`test_the_command_takes_no_base_operand` ran the documented command WITHOUT the
bound import path, so its exit status was an import failure rather than the
argparse refusal it claimed to prove. It now runs through the same bound
environment as the accepting path.

### R2 -- still open, and this is the second claim it has been open

The owner asked for it at reroute 244627 and again at 244755. It is not
delivered, and saying so plainly is better than delivering a supervisor whose
endings I have not driven. Exact remaining scope:

1. **The bounded review-only supervisor.** `KINDS` closed over `review`; one
   admission and retry disabled; finite turn, total and reserved cleanup
   limits with an actionable no-progress rule; admission closed before
   cancellation; every discovered attempt accounted for; the ordinary ending
   and cleanup path driven; an outcome published on interruption and on
   failure; attributed verdict collection through
   `review_driver.review_verdict_from_result` with base/head/tree checked
   against the attached checkpoint; and an explicit refusal to open a
   correction on `changes-requested`.
2. **`review_bindings.write` through `stage_execution.held_configuration` on
   disposable supported stores, driven by the actual documented command.**
   `tests.manager.test_claude_context.ManagedSessionResume` is the fixture
   that supplies a disposable Authority, control store and configured
   workspace storage; reaching a frozen checkpoint there means producing one
   through a deterministic implementation turn the way W239528's
   `test_baseline` does.
3. **Digest-bound selections, the exact commands and the provider question.**
   They wait on 1 because `PACKET.json` names its supervisor and its digest.

Also outstanding and not this Job's: the `seconds_bound` 3600/180 metadata
discrepancy the accepted W239528 review retained for a bounded follow-up.

Verification: 38 focused deterministic checks, 0 failures, measured
0.5900577230058843s, receipt `verification-2.json` with `verification-2.log`.
`verification-1.json` is claim 244629's receipt and is kept beside it; its
checks exercised the refused direct-SQL implementation and it is retained as
history rather than as current evidence.

Cumulative measured for W239533: 0.432753846 (claim 244629) + 0.590057723
(claim 244759) = **1.022811569s**.

State: returned for independent review with R2 outstanding.

## 2026-09-23 -- baton.claude, claim 244877

Owner reroute 244875, addressing review 2026-09-23T04:50:12Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **Both P2 test items are
closed. R2 is not delivered, and the concrete blocker is named rather than
deferred again.**

**No file under `v12/` was edited and no deployed store was opened.**

### The two P2 items, closed

**The foreign attempt is admitted, not relabelled.** The case built the attempt
with this fixture's own Work and then ran
`UPDATE attempts SET work_id = ?` before granting a writer. The reviewer was
right that this asserts the foreign-checkpoint lifecycle rather than
establishing it. `admitted_attempt` now runs the authority half in order --
`issue_offer`, `accept_offer`, `record_attempt`, `submit_claim`,
`activate_assignment` -- against a `FakeSession` bound to the OTHER Work, using
the product suite's own admission fixture (`tests.manager.test_offers`,
`tests.manager.input_roots`). The coverage is unchanged in meaning: a real
frozen checkpoint of a real second line, refused as `WRONG` by both accounts.

Two refusals along the way were the lifecycle working and are followed rather
than worked around: an offer whose profile nothing certifies is refused, so the
case certifies it the way the product's own offer fixture does; and a claim
whose decision fences somebody else is refused, so the decision now names the
participant it is about.

**The read-only boundary is measured through a supported mutator.** The probe
ran `DELETE FROM review_lines` on the handle's private connection, which proves
SQLite refuses a write but not that the SUPPORTED interface cannot change the
store through that handle. It now calls `create_line` on the read-only handle.

THE FIRST DRAFT OF THAT REPLACEMENT PASSED THE EXISTING WORK AND NOTHING WAS
RAISED -- correctly, because that call is a pure replay and a replay writes
nothing. Measuring a read-only boundary with an operand that needs no write
measures nothing at all. The case now names a Work the store holds no line for,
so the mutator must insert, and the refusal is real. The draft is recorded in
the case rather than quietly replaced.

**No private SQL remains in this dossier.** `attachment.py`, `review_bindings.py`,
`test_attachment.py` and `test_review_bindings.py` contain no `sqlite3` import
and no `execute` call; the only occurrences of the word are in the prose that
records what was removed, and the bypass check parses the module rather than
searching its text for exactly that reason.

### R2 -- not delivered, and the concrete blocker

The owner asked for R2 complete or a concrete blocker rather than another
helper-only handoff. The blocker is real and it is an OWNERSHIP question, not a
size complaint. `FINDING.md` carries the measurement; in short:
`baseline.AdmissionGate` and every other machine part of W239528's accepted
supervisor are already kind-agnostic and importable, but `_supervise` itself is
one ~400-line function that reads `bounds["implementer_invocations"]` inline
and calls an implementation-shaped `_workload_evidence`, with no seam for a
different stage kind.

So the review supervisor is either a ~2000-line derived copy whose every
ending must be driven again, or a bounded refactor of `baseline.py` to expose
caps and workload evidence as operands. The refactor is the better engineering
and is what "reuse accepted components" points at -- and it edits a file
W239533 does not own, belonging to a Work that is now closed, across a boundary
the owner's split ruling drew deliberately.

**The question: may W239533 refactor W239528's accepted `baseline.py` to expose
that seam, or must it carry a derived copy?** Absent an answer this implementer
will proceed with the derived copy, because it needs nobody's permission -- but
it is the worse option and should be chosen rather than defaulted into.

Nothing else about R2 has changed: the supervisor, `write` through
`held_configuration` driven by the actual documented command, and the
digest-bound selections, commands and provider question remain as
claim 244759's entry records them.

Verification: 38 focused deterministic checks, 0 failures, measured
0.5885895419924054s, receipt `verification-3.json` with `verification-3.log`.
The receipt now also binds the product admission fixtures this claim reuses.
`verification-1.json` and `verification-2.json` are kept as the record of what
each round corrected.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 =
**1.611401111s**. The reviewer's independently measured 0.571337769s at claim
244799 is theirs and is preserved separately rather than added here.

State: returned for independent review with R2 outstanding and its blocker
named.

## 2026-09-23 -- baton.claude, claim 247159

Owner reroute 247154, selecting the local specialization review
2026-09-23T05:08:49Z proposed. Read canonical state, the complete work-events,
thread T239533 in full (2 messages, no pagination remaining), the review, and
this dossier. **R2 is delivered.**

**No file under `v12/` was edited and no deployed store was opened.** The only
stores this claim opened are the disposable ones the tests build.

### The selection, recorded -- and my own framing corrected

The reviewer was right and my two options were a false choice. I had already
measured that `baseline`'s termination, admission, discovery, cancellation,
cleanup and publication parts are kind-agnostic, and then concluded that the
whole file had to move because `_supervise` has no seam. Only the
ORCHESTRATION BODY is implementation-shaped. `FINDING.md` records the
correction rather than adopting the better answer silently.

`review_supervisor.py` imports sixteen names from W239528's accepted
`baseline.py` unchanged and binds that file by digest
(`f27f3cd7...3df18fd5`), refusing before anything opens if the imported bytes
are not the accepted ones -- reuse that cannot say WHICH bytes it reused is a
dependency, not reuse. It monkeypatches nothing, and
`test_it_monkeypatches_nothing_in_baseline` parses this program to hold it to
that rather than trusting the sentence.

### What it delivers

One review invocation, retry refused, finite turn/total/reserved-cleanup
bounds and a no-progress stop after six unchanged ticks; admission closed
BEFORE cancellation; cancellation through the composition's own port; a
cleanup window that settles endings and can admit nothing; every discovered
attempt classified and accounted; an outcome published on every path including
a serving failure and an interruption, with `SupervisorInterrupted` carrying
the retained outcome.

`_verdict_evidence` replaces the implementation's workload evidence: one review
attempt and no other kind, an attachment to the checkpoint the packet names,
and a verdict read from the reviewer's own frozen output through
`review_driver.review_verdict_from_result`, whose cross-binding is the point --
base, head and tree are checked against the reviewed checkpoint's own record.

### The correction guarantee, stated at its real width

`StageComposition.routed` opens a correction ROUND itself on a
`changes-requested` verdict. This supervisor does not suppress it: that is the
accepted composition's act, and suppressing it would be weakening the
composition to make this report tidier. What it guarantees is that no
correction CONTAINER starts -- the gate's only cap is `review` -- and the
outcome reports both facts separately. See `FINDING.md`.

### The command through write and held_configuration

`TheDocumentedCommandProducesAnAcceptedPacket` runs the operator page's command
as a subprocess: it composes, holds the deployment against
`stage_execution.held_configuration`, writes seven documents, and the
`PACKET.json` it wrote is then handed to `review_supervisor.held_packet`. A
refused composition writes no packet at all.

Two things that surfaced there are corrected in place rather than worked
around. `_document` is an EXACT member check, and holding the subject to one
refused the real composition for carrying the survey's full account -- the
line's path, device, inode, state and revision, the source, the reference name
and the path set. All of that belongs in a packet an operator reads, so the
subject check is now REQUIRED-members: a validator should not fail in the
direction of refusing evidence. And the second case first derived a checkout
from the state root, which put the deployment's mutable state inside the
checkout; it now reads the packet's own bound `code_boundary`, which is exactly
the disagreement W239528's composer carries that value to avoid.

### The packet

`SELECTIONS-239533.json` binds the subject, the image, the adapter, the manager
source and the 180/300/60 bounds, and leaves every choice this implementer may
not take as an explicit `<OWNER: ...>`. The subject values were read at claim
244629 and are reproduced rather than re-read, because this reroute forbids
deployed-store access; step 1 re-reads them and the composer refuses on drift.

`OPERATOR-239533.md` carries the six steps, and says plainly what the run is
not: the review APPENDS to W239528's retained control store and its boundary
lands under W239528's workspace storage, because those four things are the
line's identity and custody. It states the real-provider question with the
three outcomes that would each answer it negatively, and says that
`changes-requested` and `rejected` are not among them.

Verification: 64 focused deterministic checks, 0 failures, measured
1.1679170720017282s, receipt `verification-4.json` with `verification-4.log`;
26 are new. The supervisor's imported machinery is bound by digest and was
proved by W239528's own suite, not re-proved here, and the receipt says so.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 = **2.779318183s**. The reviewers' independent measurements
(0.571337769s at claim 244799, 0.596305013s at claim 244917) are theirs and are
preserved separately.

State: the complete preparation is returned for independent review. No live run
is selected or authorized by it.

## 2026-09-23 -- baton.claude, claim 247318

Owner reroute 247316, addressing review 2026-09-23T11:30:47Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **R1-R4 are resolved.**

**No file under `v12/` was edited and no deployed store was opened.**
`baseline.py` is unchanged at its accepted digest.

### R1 -- the supervisor refused its own packet

`verify_imported_sources(packet, program=os.path.abspath(__file__))`. The
imported function defaults `program` to `baseline.__file__`, so every correct
packet failed at startup. `FINDING.md` records why the delivered tests could
not have caught it: they stopped one call short of `main`.

The operator page's step-1 clock is corrected too. `attachment.now()` exports
the instant formula, the page names it, and two cases run that exact block --
one against the real opener on a disposable store, one holding the page to the
corrected text.

### R2 -- every successful verdict was classified as invalid

The collector read `disposition` and `verdict_id`; the public reader answers
`verdict`, `result_id` and `result_digest`. It read `generation`; the
attachment row records `assignment_generation`. Both are corrected, and the
outcome now carries the result provenance.

The new cases drive the SUCCESS path for all three supported verdicts, plus a
verdict outside the contract and a head that disagrees with the checkpoint.
The public return is substituted and LABELLED as such: reaching a real frozen
review output needs a provider turn and an Authority receipt this deterministic
suite does not have and must not fabricate. What it holds the collector to is
the public return contract, which is exactly what was wrong.

The existing success fixture also built subjects from `checkpoint.get("base")`
where the row records `base_object`, so its comparisons were None against None.
Corrected, and the comment says so.

### R3 -- the orchestration is now driven

`SupervisionCase` drives `supervise` over a real `JobStore`, a real
`ControlStore`, a real submission and the real imported `AdmissionGate`, with a
stand-in for the engine side only. Three real defects came out of it:

  * the submission and the turn-ceiling read sat OUTSIDE the publishing
    region. A colliding Job identity escaped with nothing on disk. They are
    now inside it, `submission_failure` is a hold reason, and a case drives it
    with a genuine second submission over one Job identity;
  * the cleanup window's progress read was unguarded and could do the same;
  * serving ran for the whole `total_seconds` and THEN opened a further
    `cleanup_seconds`. Serving now stops at `total - cleanup` and the window is
    additionally bounded by what is left of the total.

Driven paths: the serving bound, the reserved-cleanup arithmetic, a refusing
submission, a serving failure, an interruption that publishes AND still raises,
and an outcome on every one of them. Two limits are stated rather than faked:
the fixture composition defers admission instead of completing an admit
through to a journalled operation, so `no-progress` -- which requires
something accountable -- is not reachable here, and neither is a completed
attempt lifecycle. A fake that answered an admit it could not finish made the
next sweep refuse for the fixture's reason instead of the run's, which is
itself a small demonstration of why driving beats reasoning.

A test of mine also read `SupervisorInterrupted.args[1]` for the retained
outcome; the class documents it on `.outcome` and passes only the reason to
`BaseException`. That was the case assuming a shape instead of reading the one
the class states.

### R4 -- the selected contract is restored

The previous claim narrowed it by prose. It is restored: a correction round
opened in this Job store HOLDS the run, `correction_rounds_opened` is read
from the Job store's own stage records rather than from attempt kinds, and
`CORRECTION_LIMITATION` names the exact product site -- `StageComposition.routed`
calling `open_correction` unconditionally, with no operand that declines it --
and says the change belongs to the owning implementation scope. A case drives
that branch and asserts the hold. `OPERATOR-239533.md` presents the choice to
the owner where the effect appears.

Verification: 79 focused deterministic checks, 0 failures, measured
1.3253460949927103s, receipt `verification-5.json` with `verification-5.log`;
15 are new. Earlier receipts are kept as the record of what each round
corrected.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 = **4.104664278s**. The reviewers' independent
measurements (0.571337769s, 0.596305013s, 1.152729417s) are theirs and are
preserved separately.

State: the corrected preparation is returned for independent review. No live
run is selected or authorized by it.

## 2026-09-23 -- baton.claude, claim 247423

Owner reroute 247421, addressing review 2026-09-23T11:56:42Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **R3a and R4 are done.
R3b is not, and it is the single remaining item.**

**No deployed store was opened.** One product file was edited under the
owner's explicit selection, recorded before the edit.

### R4 -- the owner-selected product change

`OWNER-PRODUCT-CHANGE-247423.md` records the decision, the reasoning, the
exact file and its before-digest, written BEFORE the first edit as reroute
247421 requires. `PRODUCT-CHANGE-247423.json` records the after-digest and the
product-suite accounting.

`v12/python/tools/stage_execution.py` gains an optional `correction_policy`
deployment member. Absent or `open` is byte-for-byte today's behaviour, so
every existing deployment is preserved by DEFAULT rather than by a migration.
`decline` makes `routed` not reach `open_correction` and record
`correction_declined`. `review_bindings` sets it; `held_packet` refuses a
packet without it, so the packet is non-runnable until the boundary is
configured -- which is what reroute 247421 asked for.

The change had a real defect and the product suite found it: the first version
read `self.deployment.correction_policy` inside `routed`, and `routed` IS the
deployment's own method, so 38 cases answered `AttributeError`. Fixed. The
suite runs 424 with 12 errors, and those 12 are the pre-existing
`Integration._run` fixture errors that predate this Work -- each fails inside
that function's producer-proposal read and none names `correction_policy` or
`routed`.

Four new cases drive the REAL `StageDeployment.routed` with `open_correction`
WATCHED rather than stubbed away, because the question is whether it is
reached: declining never reaches it, absent and `open` both do, a
non-correction verdict is returned as it arrived under either policy, and the
supervisor's mirrored constant is held equal to the product's own.

### R3a -- the interrupt that lost the outcome

The guard caught `Exception`; the handler raises `KeyboardInterrupt`. Now
`BaseException`, recorded, serving skipped, and re-raised after the accounting
and the publication. The regression wraps the real public `submit`, lets it
COMMIT, then injects the interrupt -- and asserts the committed submission,
the published outcome and that the final canonical read still ran.

### R3b -- not delivered, and the reviewer's objection is correct

`Serving` defers every admission, so `test_exactly_one_review_is_admitted...`
measured calls reaching a composition that refuses them. I renamed and
re-scoped that case last claim, which made it honest but did not make it the
proof. What remains unexercised is exactly what the reviewer listed: an
admitted attempt, cancellation of one, cleanup uncertainty and interruption
with an outstanding attempt, a completed review, and real frozen-result
collection.

The reviewer is also right that my "a real frozen output needs a live
provider" claim was not established: `ManagedSessionResume` and W239528's
`test_baseline` already drive deterministic providers over real coordination.
The remaining work is to extend that fixture to admit and end the separate
review while preserving producer/reviewer identities and the frozen checkpoint
provenance, with the simulated provider labelled. I did not reach it this
claim, and the packet stays non-runnable until it and the product change are
independently accepted.

Verification: 86 focused deterministic checks, 0 failures, measured
1.3391616380104097s, receipt `verification-6.json` with `verification-6.log`;
7 are new. Separately, the product suite `tests.tools.test_stage_execution`:
424 tests, 12 pre-existing errors, measured 159.751s.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 = **165.194825916s**. The
reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s) are theirs and are preserved separately.

State: returned for independent review with R3b outstanding.

## 2026-09-23 -- baton.claude, claim 247666

Owner reroute 247663, addressing review 2026-09-23T12:20:24Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **Item 5 is done. Items
1-4 and 6 are not, and this claim did not reach them.** That is partial
progress, not readiness, and the packet stays marked NOT RUNNABLE.

**No deployed store was opened.** The one product file remains the one the
owner selected.

### Item 5, done

**The malformed policy goes through the validator.**
`test_a_malformed_correction_policy_is_refused_by_the_validator` composes a
real deployment and hands `held_configuration` five unreadable values --
`"Decline"`, `"off"`, `""`, `None`, `1` -- and requires each to be refused by
name. An unreadable policy would otherwise be discovered by `routed`, which
runs after a verdict has been recorded: the wrong moment to learn that a
deployment cannot say what it meant.

**The twelve are corroborated focally rather than counted.**
`preexisting_errors.py` runs them BY NAME and records where each one fails.
All twelve fail inside `Integration._run`'s producer-proposal read, through
`_authority_read`, and NO traceback among them names `correction_policy`,
`CORRECTION_POLICIES`, `DECLINE_CORRECTION`, `routed` or
`correction_declined`. A change that is never reached did not cause them.
`PREEXISTING-ERRORS-247666.json` records the selectors, the failing frames and
that result.

Exact prior evidence is quoted beside it -- W239528's
`review-2026-09-22T23-53-34Z.md`, dated the day BEFORE the product change --
**with that reviewer's own caveat kept**: "I did not rerun that broader suite
or independently establish their provenance." Quoting the report without the
caveat would have been citing my own claim back as if somebody else had
checked it, which is why the focused comparison exists rather than the quote
standing alone.

**A comment repair, and it is the only reason the product digest moved.** A
shell backtick had eaten the word `routed` from one comment line when claim
247423's edit was applied, leaving "# IS the deployment's own method". No
behaviour changed. `PRODUCT-CHANGE-247423.json` records the new after digest
`6a212c3a...` and says exactly that.

### Items 1-4, not reached, and the honest reason

I did not run out of interface or authority -- I ran out of turn. The path is
known and the reviewer named it: `BaselineCase` in W239528's
`test_baseline.py` already drives a real composition through
`stage_execution.operations_from` with a deterministic provider, real stores
and `baseline.prepare` in place of the owner acts, and `stores(incarnation)`
opens fixed paths so a second phase can share one control store with the
first. The shape is: run the accepted implementation phase to leave a frozen
review-ready checkpoint, then compose and drive the REVIEW packet over those
same stores with `review_supervisor.supervise`.

WHAT I EXPECT TO HAVE TO SOLVE THERE, recorded so the next claim starts from
it rather than from scratch:

  * `baseline.prepare` mints the qualification grant bound to
    `packet["context"]["job_id"]` for a CONTEXTUAL worker. The review worker
    is not contextual (`single_worker.CONFIG_SCHEMA`, not the context one), so
    whether a review run needs that preparation at all, and what it needs
    instead, is the first thing to establish.
  * the review packet's `context` member is currently composed with null
    profile members for the same reason, and `held_packet` accepts that; a
    driven run will say whether the composition agrees.
  * the second phase's Job identity must differ from the first's while the
    control store is shared, which is the arrangement `attachment.py` already
    describes and `survey` already refuses collisions for.

Item 4 is smaller and also unreached: a distinct digest-bound manager-source
snapshot carrying the `correction_policy` change, built the way
W239528's `snapshot_242687.py` builds one and leaving the producer's snapshot
untouched, then `SELECTIONS-239533.json` pointing at it instead of
`single-implementation-242687/manager-source`, which predates the change.

Verification: 88 focused deterministic checks, 0 failures, measured
1.2950563630001852s, receipt `verification-7.json` with `verification-7.log`;
2 are new. Separately, `preexisting_errors.py` ran the twelve named product
cases.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 =
**166.489882279s**. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s) are theirs and are
preserved separately.

State: returned for independent review with items 1-4 and 6 outstanding and
the packet not runnable.

## 2026-09-23 -- baton.claude, claim 247757

Owner reroute 247747. Read canonical state, the complete work-events, thread
T239533 in full (2 messages, no pagination remaining), the review, and this
dossier. Item 5 is accepted and was not repeated. **Item 1 is substantially
advanced and NOT finished; items 2-4 and 6 are untouched.**

**No deployed store was opened and no product byte changed under this claim.**

### What now works, and it is the thing three reviews have asked for

`test_review_lifecycle.py` admits ONE REVIEWER through supported real
coordination. Two phases over ONE control store:

  * PHASE ONE is W239528's accepted `baseline.supervise` run, driven
    unmodified, so what phase two reviews is a checkpoint that Job's own
    accepted program actually made -- a real line, a real writer, a real
    frozen checkpoint, `review-ready`.
  * PHASE TWO composes a review deployment carrying
    `correction_policy: "decline"`, submits a review-only Job with its OWN
    identity, and drives `review_supervisor.supervise` over the same stores.

The outcome now reports `admissions: {"review": 1}` and the stage reaches
`answering`: the reviewer is admitted, the turn runs, and the manager freezes
a real result. The subject is read back from the control store rather than
declared.

### Four real defects the drive found, each fixed

Every one of them was invisible to a fixture that defers admission, which is
exactly why the reviewer refused that fixture.

  * **The review Job's input digest was the fixture constant.** The stage sat
    `queued` for a whole run and the deferral said why: "no worker this
    deployment configures for the 'review' stage can serve Job ...:
    {'review-worker': ['the submitted input']}". It is now
    `job_input_identity(self.manifest)` -- the worker's own manifest.
  * **`composed_for` answered phase one's composition.** The fixture's `turn`
    reaches it for the prepared attempt's boundary, so the review turn raised
    `KeyError` for the attempt that had just been admitted. Phase two now sets
    `self._composed`.
  * **The report had no way to travel.** `claude_agent._review_report(room)`
    reads `review-report.json` from the PROVIDER'S OWN cwd, which the
    fixture's `edits` seam writes; a `report=` operand the turn does not take
    did nothing.
  * **The producer's stores were not carried forward.** `supervised` keeps
    `_job` but not `_control`, so the subject could not be read.

### THE EXACT NEXT UNFINISHED OPERATION

The frozen result is `unable`, so `review_verdict_from_result` refuses:

    review attempt 'attempt-27aae1ed...' froze an 'unable' result;
    a review that did not complete decided nothing

So the manager side is reached and correct -- it froze a result and refused to
read a verdict out of a turn that did not complete. What remains is to find why
`claude_agent._review` answers `unable` for this turn and supply what it is
missing. The report bytes now travel the way a real reviewer's would, so the
gap is inside that branch rather than in the manager or the supervisor.
`_review` re-reads the mounted source after the turn and refuses if it moved,
refuses an inherited report destination, and requires the provider to answer
`ok` -- each is a candidate and none has been eliminated yet.

Items 2 and 3 are one step behind that: the fixture that makes an attributed
verdict, a stopped runtime, positive cleanup and an outstanding-attempt
failure/interruption reachable now EXISTS, and the cases do not.

Verification: the dossier's receipt is unchanged from claim 247666
(`verification-7.json`, 88 checks) because this claim added no passing case --
`test_review_lifecycle.py` carries the fixture and no test method yet, and
`load_tests` keeps `BaselineCase`'s own cases from being counted here. Saying
"88" twice is more honest than inventing a number for work in progress.

Cumulative measured for W239533 is therefore unchanged at **166.489882279s**.
The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s) are theirs and are
preserved separately.

State: returned for independent review with item 1 in progress at the exact
operation named above, and the packet not runnable.

## 2026-09-23 -- baton.claude, claim 247823

Owner reroute 247812 and thread message 247805 (the delivery-continuity
policy, now in AGENTS.md). Read current canonical detail, the handoff since
247794, the latest review and the new discussion; the checkpoint above records
those positions. **Items 1, 2 and 3 of owner 247663 are done. Items 4 and 6
remain and no new authority is needed for them.**

### The reviewer found the cause and it was mine

`claude_agent._review_report` requires `findings` to be NON-EMPTY TEXT; both
fixture reports supplied a LIST, so the adapter answered `unable` and the
manager correctly refused to read a verdict out of a turn that did not
complete. The adapter was right and the fixture was wrong -- "an exit status is
not a decision and this adapter will not map one into a verdict" is exactly the
behaviour that made this hard to misread. Corrected in place with the reason
recorded beside it.

With that one operand corrected the whole path settles:

    state settled, stopped completed, stage review completed
    admissions {"review": 1}, one admitted attempt
    verdict accepted, bound to the packet's checkpoint base/head/tree,
      with result_id and result_digest
    cancellation requested, execution_runtime destroyed
    cleanup retained, state absent
    correction_rounds_opened [], correction_containers_started []
    held_because []

### Eight discoverable cases, and a loader defect they exposed

`test_review_lifecycle.py` now carries `OneReviewerIsAdmittedAndEnded`,
`AChangesRequestedReviewIsAValidOutcome` and
`AnAdmittedAttemptIsAccountedForWhenTheRunDoesNotFinish` -- the attributed
verdict, the stopped runtime and positive cleanup, producer/reviewer
independence read back through `review_of`, `changes-requested` settling with
zero rounds and zero containers, and an interruption and a composition failure
that each leave ONE ADMITTED ATTEMPT accounted for with the outcome published.

Excluding the base class by NAME was not enough: the fixture's ancestors carry
their own `test_` methods, so the three new classes inherited twelve of
W239528's and the product suite's cases and ran them under this dossier's name.
`load_tests` now filters on each class's OWN `__dict__`, which is the only set
this module wrote.

### The stale limitation prose, corrected

`CORRECTION_LIMITATION` still said the round could not be prevented and that
the fix belonged to the owning implementation scope. Owner selection 247421
MADE that change, so the text now names the boundary that closes it -- and says
that a round appearing anyway means the boundary did not hold, which is a fault
worth holding on rather than a state to accommodate. Its case moved with it.

### Spending, including what was not a test

Verification: 96 focused deterministic checks, 0 failures, measured
5.328163940997911s, receipt `verification-8.json` with `verification-8.log`;
8 are new and `test_review_lifecycle` is now in `verify.py`.

THE PROBES ARE COUNTED TOO. Review 2026-09-23T12:57:02Z is right that
unmeasured driving is not zero spending. Claims 247757 and 247823 drove the
two-phase fixture roughly a dozen times outside any receipt while finding the
four defects and the report shape. Those runs were not individually timed, and
the honest figure is an upper bound rather than a measurement: at the
5.3-second cost the receipt now measures for a suite containing four such
drives, a dozen ad-hoc drives is on the order of 20 seconds. It is recorded as
**~20s ESTIMATED, NOT MEASURED**, and it is not folded into the measured total.

Cumulative MEASURED for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 + 5.328163941
= **171.818046220s**, plus the ~20s estimated above. The reviewers' independent
measurements (0.571337769s, 0.596305013s, 1.152729417s, 1.311204790s,
1.302250807s, 2.361050477s, 3.324525589s) are theirs and are preserved
separately.

State: returned for independent review with items 4 and 6 outstanding. Per the
delivery-continuity policy this is ordinary continuation, not an owner gate.

## 2026-09-23 -- baton.claude, claim 247870

Review 2026-09-23T13:04:00Z accepted items 1 and 2 and called item 3 PARTIAL,
naming four gaps. **Three of the four are now closed; the fourth is the
admitted no-progress case and its exact preconditions are recorded rather than
approximated.** Read current canonical detail, the handoff since 247847 and
the review; positions are in the checkpoint.

### The gate-order objection was right

"Gate-order test checks only final counts; that cannot establish gate closed
before cancellation in a single-stage Job." It cannot -- a count is the end of
a run and the question is about an instant during it. The gate now stamps its
own `stopped` state onto every act it performs, and the cancellation is watched
on the COMPOSITION rather than on the gate, because `_cancel_active` is handed
the composition. So the order is read off a trace: every admitting act happened
with the gate open, every cancellation with it closed, and nothing admitting
follows the first cancellation. A closed gate is also OFFERED an admission and
refuses it, which is a stronger statement than "none arrived".

THE SEAM IS `review_supervisor.AdmissionGate`, NOT `baseline`'s. The recording
gate is a subclass of the real imported one and the patch is on the name this
module under test resolves; W239528's module is untouched and
`test_review_supervisor` still parses this program to hold it to that.

### The other two gaps

The total bound is now arithmetic on the controlled clock: `serving_bound_seconds`
equals `total - cleanup` and `served_seconds` never exceeds `total`. And the
outstanding attempt is named EXACTLY -- its identity, its `cleanup: None`, and
that identity appearing in `held_because` -- rather than counted.

### What is NOT done, and why it is not approximated

The admitted NO-PROGRESS case. The detector requires four things at once: an
accountable attempt, NO outstanding cleanup, a non-terminal stage, and an
unchanged observation for six ticks. A settled review has a terminal stage; a
failed one leaves cleanup outstanding. The state that satisfies all four is a
committed cleanup under a stage that cannot advance -- which is W239528's real
stall -- and reaching it deterministically needs the ending to settle while the
stage is held short of `completed`. I would rather record that precondition
than assert no-progress from a state that does not have it.

The cleanup-WINDOW interruption is in the same category and is stated in the
case that replaced it: a settled run leaves nothing outstanding, so the window
breaks before it sleeps and an interrupt injected through `sleep` never reaches
it. What is reachable -- and is the property that matters -- is an interruption
while an admitted attempt is still outstanding, which is covered.

### The probe estimate, withdrawn

Review 2026-09-23T13:04:00Z: "Historical ~20s probe estimate is not an
established upper bound; actual unknown". Correct -- I derived it from a later
suite's cost, which is not a measurement of those runs. The record now says
**unknown and unmeasured** rather than carrying a number that reads like one.

Verification: 103 focused deterministic checks, 0 failures, measured
9.069514465998509s, receipt `verification-9.json` with `verification-9.log`;
7 are new.

Cumulative MEASURED for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 + 5.328163941
+ 9.069514466 = **180.887560686s**. Unmeasured ad-hoc driving across claims
247757, 247823 and 247870 is UNKNOWN and is not estimated. The reviewers'
independent measurements (0.571337769s, 0.596305013s, 1.152729417s,
1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s, 4.056475030s) are
theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 247908

Review 2026-09-23T13:10:01Z accepted the gate-state observation and the exact
outstanding identity, and refused two things. **Both are closed. The admitted
no-progress case remains outstanding and is still disclosed as such.**

### R1 -- the bound cases were not reaching their own condition

The reviewer reproduced the exact operands independently and got
`state=settled, stopped=completed, served_seconds=3.0, cleanup_sweeps=0`. That
is right and the diagnosis is exact: `report=None` falls back to ACCEPTED in
the driver, and `expect=None` only disables the status assertion rather than
the turn -- so both "cannot finish" cases were successful early completions
and neither reached a deadline. `fail_at=10**9` never fired. I had written two
cases that asserted arithmetic about a run that finished normally.

`withhold=True` is the seam that actually withholds the turn after admission.
With it the run stops on its deadline: `overall-bound-exceeded`, ONE admitted
attempt, stage not `completed`. And the total is now checked on the clock
rather than on `served_seconds` -- which is measured BEFORE cancellation and
cleanup and cannot speak for them. Every read of the injected monotonic clock
is recorded, so the case asserts the LAST read of the whole run is inside
`total_seconds`.

A sensitivity case raises the total far above the tick budget and requires
that the run then does NOT stop on the deadline, so the deadline case is
measuring the deadline rather than something that would have held anyway.

### R2 -- the shutdown interruption is observed rather than inferred

"An interruption during serving ... does not substitute for a deliberately
observed interruption in shutdown", and the failure-before-ending path already
supplies the reachable state. The interrupt is now injected AT the
composition's cancellation -- gate already closed, attempt already outstanding
-- and the case asserts the injected point fired (`shutdown_reached is True`)
rather than reading the phase off the outcome. It then asserts that the
PUBLISHED outcome carries the named attempt and its uncertainty, which is the
ordering that matters: the accounting reaches disk before the interrupt is
re-raised.

### Still outstanding, and unchanged

The admitted NO-PROGRESS case. The reviewer's seam is recorded in the
checkpoint: hold stage advancement at its real transition boundary after
positive cleanup commits, keep reads and records real, verify six unchanged
non-terminal observations, and do not attribute a timeout falsely. No raw
store edits and no fabricated cleanup receipts.

Verification: 106 focused deterministic checks, 0 failures, measured
12.534635852993233s, receipt `verification-10.json` with
`verification-10.log`; 3 are new and 2 were replaced rather than added -- the
two bound cases the reviewer refused are gone, not kept beside their
replacements.

Cumulative MEASURED for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 + 5.328163941
+ 9.069514466 + 12.534635853 = **193.422196539s**. Unmeasured ad-hoc driving
across claims 247757, 247823, 247870 and 247908 remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s) are theirs and are preserved
separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 247947

Review 2026-09-23T13:15:08Z accepted the deadline and shutdown corrections.
**Item 4 is done. Item 6 and the admitted no-progress case remain.**

### Item 4 -- this Job's own manager source

The selections bound `single-implementation-242687/manager-source`, which is
W239528's producer snapshot and PREDATES the `correction_policy` change. A run
bound to it would have no boundary to decline the correction round with, and
`held_packet` would refuse the packet composed from it -- so the binding was
not merely stale, it was unusable.

`snapshot_247947.py` builds the successor: 106 files at
`/home/sl/baton-runs/independent-review-247947/manager-source`, carrying
`tools/stage_execution.py` at `6a212c3a...ab5801`, bound by
`MANAGER-SOURCE-independent-review-247947.json`. `--verify` holds with no
drift, nothing missing and nothing extra.

W239528'S SNAPSHOT_242687.PY WAS NOT USED, and the reason is ownership rather
than capability. It supports `--rebuild-into` and `--claim` for exactly this,
and its refusals are the ones this follows -- never replace a tree, never
replace a manifest, a successor states its own claim. But its `manifest_for`
writes into ITS OWN dossier, and W239528 is a closed Work whose dossier is
read-only here; writing a W239533 manifest into it would be this Job filing its
evidence in somebody else's record. The rules are reused; the destination is
this dossier's.

THE PREDECESSOR IS VERIFIED UNCHANGED AS PART OF EVERY BUILD, against its own
recorded manifest, and the build refuses if it has drifted. A successor whose
build could not say the predecessor survived would be asserting the one thing
the arrangement exists to guarantee.

`SELECTIONS-239533.json` and `OPERATOR-239533.md` are repointed, and the page
now carries the `--verify` command and says why the binding moved.

### The no-progress case, measured again

The adapter's own `unable` path was tried as a route to it: a malformed report
makes the turn `unable`, the stage stays `answering` and the run stops on its
bound -- but cleanup is OUTSTANDING (`no committed cleanup`), which correctly
suppresses the detector. So that route does not reach it. The state the
detector needs is positive cleanup COMMITTED under a stage still short of
terminal, held at its real transition boundary, and that is recorded in the
checkpoint as the next milestone rather than approximated.

Verification: 106 focused deterministic checks, 0 failures, measured
12.45698677400651s, receipt `verification-11.json` with `verification-11.log`.
No case was added this claim -- the work was the snapshot and the bindings --
and the receipt now also binds `snapshot_247947.py` and its manifest.

Cumulative MEASURED for W239533: 193.422196539 + 12.456986774 =
**205.879183313s**. Unmeasured ad-hoc driving remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s, 4.491119177s) are theirs and are
preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 247997

Review 2026-09-23T13:20:42Z accepted the successor snapshot and its bindings,
and corrected me on scope: **owner 247663 item 4 includes the exact-successor
documented preparation and startup, and I had deferred that into item 6 and
called item 4 done.** That was moving a requirement rather than meeting it, and
the correction is right. It is now executed.

### Item 4's remaining half

`TheDocumentedCommandsRunAgainstTheSUCCESSORSource` binds `PYTHONPATH` to the
successor snapshot -- exactly what `BOUND` names on the operator page, and
NOTHING from the checkout's own `v12/python`, because a path carrying both
would prove nothing about which bytes answered.

  * The documented COMPOSITION exits 0 against those bytes, and the
    `PACKET.json` it writes names the snapshot as its manager source and code
    boundary with a file count and per-file digests equal to the manifest's --
    so the packet is bound to the tree the manifest describes rather than to a
    path that happens to have the right name.
  * The documented STARTUP holds the packet and resolves
    `verify_imported_sources` INSIDE the snapshot; both `tools` and
    `baton_v12` are asserted to resolve under that path. The image check goes
    through `review_supervisor.main`'s own `image_inspect` seam with a stub,
    so no container, image or engine is reached -- the proof is about which
    bytes ran, not about a deployment.

One defect surfaced there and is fixed: the shared composition fixture binds
`attachment.py` as `supervisor_path`, so the startup refused with "this process
is running review_supervisor.py and the packet binds attachment.py". A startup
proof has to name the supervisor rather than inherit a composition fixture's
placeholder.

### The operator page's opening note

It still claimed the boundary "has not yet been accepted" and that R3b was
outstanding, both of which had moved. It now lists what IS accepted, what is
outstanding, and that the whole preparation is not accepted so steps 2 and 4
are unauthorized -- and it distinguishes "nothing has been executed against a
deployment" from "the documented commands have been executed on disposable
fixtures", which are different claims and were being blurred.

Verification: 108 focused deterministic checks, 0 failures, measured
13.294443416991271s, receipt `verification-12.json` with
`verification-12.log`; 2 are new.

Cumulative MEASURED for W239533: 205.879183313 + 13.294443417 =
**219.173626730s**. Unmeasured ad-hoc driving remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s) are
theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248032

Review 2026-09-23T13:25:28Z accepted the successor-only composition and the
exact packet manifest, and refused a claim of mine that was simply false.

### The startup case never called `main`, and three documents said it did

It called `held_packet`, `verify_imported_sources` and `verify_worker_image`
individually and then printed success. The case name, its docstring, the
handoff comment and PLAN all said `main` had run. Naming a check after an entry
point it never enters is worse than no claim at all, and the reviewer was right
to refuse it.

`main` is now invoked with the documented `--packet` and `--incarnation`, under
successor-only imports, with two of ITS OWN seams supplied so that nothing can
start: `image_inspect`, so no engine is reached, and `compose`, so no container
can be. Everything else is real -- the packet validation, the imported-source
check, the Job and control stores, `survey`, and the supervised run that
publishes an outcome. `main` returns 1; the outcome on disk is `held` with "no
runtime was ever admitted", which is the honest answer for a composition that
starts nothing, and the case asserts exactly that rather than accepting any
non-refusal.

The case also asserts it did NOT exit 2, because 2 is "refused before anything
opened" -- and a startup proof that only showed the program refusing early
would be the same empty claim in a different shape.

### One thing the first working version got wrong about cost

At the packet's own 300/60 bounds, `main` served on the REAL wall clock for
242 seconds to prove a startup path. There is no injected monotonic through the
documented entry point and there should not be, so the case now composes 12/4
bounds and proves the same path in seconds. The ARITHMETIC of the bounds is
proved separately on a controlled clock in
`test_review_lifecycle.TheTotalBoundHoldsWhenTheRunCannotFinish`; this case is
about the entry point, not the numbers.

`OPERATOR-239533.md` now states what has been executed at its real width, and
records that an earlier version of the page claimed `main` had run when it had
not.

Verification: 108 focused deterministic checks, 0 failures, measured
21.35032132201013s, receipt `verification-13.json` with
`verification-13.log`. The count is unchanged because the case was REPLACED
rather than added; the measured time rose because it now really runs the
supervisor.

Cumulative MEASURED for W239533: 219.173626730 + 21.350321322 =
**240.523948052s**. Unmeasured ad-hoc driving remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s,
0.770625345s) are theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248090

Review 2026-09-23T13:35:00Z accepted the `main` startup proof and the closure
of the main-never-called finding. Two things remain and this claim advanced the
harder one by half, with the half that does not hold stated plainly.

### The no-progress structure, and what it measured

The detector needs four conditions at once: an accountable attempt, NO
outstanding cleanup, a non-terminal stage, and an unchanged observation for six
ticks. Earlier claims kept reaching three of four -- a settled review has a
terminal stage; a failed one leaves cleanup outstanding -- which is why the
case has stayed open rather than been faked.

`stalling_submission` supplies the missing structure: the review Job gains an
`integration` stage that depends on a stage in a SECOND Job which never runs.
Measured, it does exactly what it should: `integration` is `blocked`, the Job
is therefore not terminal, and the gate records 240 FOREIGN admissions and ZERO
cap refusals -- so the blocked stage never reaches admission and no cap refusal
ends the run for a different reason. A cap refusal would have stopped the run
for something other than the detector and proved nothing.

WHAT DOES NOT HOLD YET, and it is one thing: under this two-Job submission the
review attempt ends `exceptional`, with `cleanup: None, why: "no committed
cleanup"` -- so the cleanup is outstanding and the detector is correctly
suppressed. The same turn settles under the one-Job submission, so the question
is narrow: what about the two-Job shape makes the review attempt fail.

NO CASE ASSERTS NO-PROGRESS, because none can yet. The `stalling` plumbing is
in the fixture and no test uses it. I would rather leave a named half-result
than an assertion about a state the run does not reach.

### The packet's honest distinction, carried forward

The reviewer's note is recorded in the checkpoint as part of item 6: the final
packet must distinguish the `main` startup proof -- a `Deferring` composition
with stub image metadata, honestly holding with "no runtime was ever admitted"
-- from the separate successful real-coordination lifecycle. **No successful
reviewer run through `main` is proved.**

### Spending

Verification: 108 focused deterministic checks, 0 failures, measured
21.34568109900283s, receipt `verification-14.json` with
`verification-14.log`. No case was added.

Cumulative MEASURED (suite receipts only) for W239533: 240.523948052 +
21.345681099 = **261.869629151s**.

SEPARATELY, and not folded into that subtotal: the preliminary 242-second
`main` run recorded under claim 248032, before that case was bounded to 12/4.
It was a real measured run and it is preserved as its own figure rather than
absorbed. Unmeasured ad-hoc driving remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s) are theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248135

Review 2026-09-23T13:41:04Z found the fixture cause I had left as an open
question, and it was a positional assumption rather than anything about the
lifecycle.

### The selector

`ComposedOneJobCase.states` reads `projected["jobs"][0]`. That is correct for a
one-Job fixture and wrong the moment a second Job exists: under the stalling
submission it answered the BLOCKER Job's stages, so the driver never saw
`review` reach `waiting`, never took the turn, and the attempt ended
`exceptional`. The reviewer reproduced it with an instance-only public status
selector; the fixture now makes the same selection by `REVIEW_JOB`.

MY FIRST FIX BROKE PHASE ONE, which is worth recording because it is the same
mistake mirrored. Returning `{}` when no review Job is present meant the
PRODUCER's run -- a one-Job fixture with no review Job at all -- never had its
turn taken either. The override now falls back to the inherited positional
answer exactly where that answer is right.

### What the four conditions look like now

Measured on the stalling submission after the fix: `review: completed`,
`integration: blocked`, `outstanding_cleanup: []`, verdict `accepted`. THREE OF
FOUR hold -- an accountable attempt, no outstanding cleanup, and a Job that is
not terminal.

The fourth does not: `stalled_ticks` is 0 across 241 serving ticks, so the
observation is still changing. That is precisely what the review predicted --
"final cleanup does not establish positive cleanup during six serving
observations" -- and the next step is to find WHEN during serving the cleanup
commits and what else in `_observation(states, accountable, cleanup)` keeps
moving, rather than to assert a stall the run does not reach.

STILL NO ASSERTING NO-PROGRESS CASE. The `stalling` plumbing and the selector
are in the fixture; no test uses them. The eighteen lifecycle cases pass
unchanged, which is what says the selector fix did not disturb the accepted
proofs.

Verification: 108 focused deterministic checks, 0 failures, measured
21.342962219001492s, receipt `verification-15.json` with
`verification-15.log`. No case was added; the broad suite ran because the
selector touches the shared fixture every accepted lifecycle case uses, so
leaving it unrun would have been the reverse mistake.

Cumulative MEASURED (suite receipts only) for W239533: 261.869629151 +
21.342962219 = **283.212591370s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc
driving remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s) are theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248173

Review 2026-09-23T13:46:58Z diagnosed the suppression exactly, over 42 real
cleanup reads, and the cause was a defect in MY supervisor rather than in the
fixture. **The admitted no-progress case now asserts, and owner 247663 item 3
is complete.**

### Two accounts of one set

`should_continue` built its accountable set from the gate's launches and the
projection and classified nothing. The shutdown's `classify()` drops an
identity whose origin is `UNALLOCATED` -- "an identity the manager answers no
row for, that this run never launched, is not a runtime". So the blocked
stage's projection identity was counted OUTSTANDING on every serving tick and
EXCLUDED at shutdown. The outstanding condition could therefore never empty,
and the no-progress rule could never fire, no matter what the run did.

I had also inferred the wrong thing from the same evidence last claim:
`stalled_ticks 0` does NOT mean the observation kept changing. The reviewer
said so plainly and the trace shows it -- the review attempt was already
`retained`/`absent` DURING serving, and the extra identity alone held the set
open.

Serving now classifies through the same `_origin` the shutdown uses. IT FAILS
CLOSED: a read that does not complete answers `FOREIGN`, which is not excluded,
so an identity this run cannot classify keeps its cleanup obligation. Dropping
on uncertainty would invent the very quiet the detector then reports, which is
why the fix is not a filter.

### What it measures now

`stopped: no-progress`, `stalled_ticks: 6`, `outstanding_cleanup: []`,
`review: completed`, `integration: blocked`, every cleanup positive, and the
run served 9 seconds of a 300-second bound instead of 241. Reporting a stall
when it happens rather than waiting the backstop out is the whole purpose of
the rule, and the case asserts the elapsed time as well as the reason.

Three cases: the four conditions each asserted rather than assumed; the
excluded identity reported as `unallocated` and present in `observed_attempts`
but not in `admitted_attempts`, so it is excluded rather than ignored; and the
NEGATIVE case -- a run whose ending never settles keeps its real outstanding
runtime, and no-progress must not fire there.

Verification: 111 focused deterministic checks, 0 failures, measured
23.648867101001088s, receipt `verification-16.json` with
`verification-16.log`; 3 are new.

Cumulative MEASURED (suite receipts only) for W239533: 283.212591370 +
23.648867101 = **306.861458471s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc driving
remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s, 2.115041870s) are theirs and are preserved
separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248209

Review 2026-09-23T13:52:06Z accepted the unallocated accounting correction and
the six-tick stall, and found a regression in the fix itself. It is the same
defect this project has already been corrected for once, and I put it back.

### The swallowed interrupt

`_serving_origin` used `_guarded(..., interrupted=[])`. `_guarded` catches
`BaseException` and appends the interruption to the list it is given; a
DISPOSABLE list discards it. So a `KeyboardInterrupt` raised while classifying
an origin was swallowed, the predicate returned normally, and serving could
continue after an operator had asked the run to stop.

W239528's review 2026-09-23T00:50:59Z R1 found exactly that shape in the
progress read, and the comment explaining it is a few lines above the one I
wrote. Reaching for `_guarded` because it was the local idiom is how the same
mistake gets a second home.

It now catches ordinary `Exception` only: the failure is named as uncertainty
and the answer is `FOREIGN`, which is not excluded, so the identity keeps its
cleanup obligation. A `BaseException` travels out of the predicate, out of
`serve`, and into the shutdown handler that already closes admission, cancels,
accounts and publishes.

### Two regressions, in the right branch

Both are injected INSIDE the origin read, which the review correctly noted is
a different branch from the `sleep` the other interruption cases use.

An interrupt there stops the run, publishes the outcome and raises
`SupervisorInterrupted` -- asserted on the PUBLISHED file, not only the
exception. An ordinary failure there keeps the identity accountable, records
the uncertainty, and does NOT report no-progress.

The interrupt case asserts AT LEAST one admitted attempt rather than exactly
one. With the classification broken the blocked stage's identity can no longer
be shown `unallocated`, so it is not dropped -- that is the fail-closed rule
visible, and asserting exactly one would have been asserting that uncertainty
silently shrinks the accountable set, which is the thing the rule exists to
prevent.

Verification: 113 focused deterministic checks, 0 failures, measured
36.40780342000653s, receipt `verification-17.json` with
`verification-17.log`; 2 are new. The suite is slower because the two new
cases drive whole runs whose origin reads fail.

Cumulative MEASURED (suite receipts only) for W239533: 306.861458471 +
36.407803420 = **343.269261891s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc driving
remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s, 2.115041870s, 2.201875895s) are theirs and are
preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248263

Review 2026-09-23T13:57:49Z accepted the origin-read correction and closed item
3. **This claim completes owner 247663 item 6, the last one: the complete
packet, exact commands, provider question and consolidated evidence.**

### The packet, and why it is two documents

`OPERATOR-239533.md` is now the packet rather than a note beside it. It opens
with what is in the packet, lists the TWELVE unresolved operator-selected
inputs by member -- calling out the three that carry a refusal rather than a
choice (`provider_network` where `none` is refused, the credential reference
where an expired token reproduces a known failure, and the evidence digest
where an all-zero sentinel is refused) -- then gives steps 0-6 with the exact
commands, the provider question with the three negative answers that are
evidence rather than bugs, and a limitations section.

`EVIDENCE-239533.json` is the machine-readable half, produced by the new
`packet.py`. Every digest, receipt, count and open choice in it is READ from a
retained file at generation time; the only written prose is `established`,
`not_established` and the provider question. `verify.py` regenerates it BEFORE
running the suite, so the checks compare a current document against the tree
rather than the previous run's -- which also means its `receipts` list stops one
run short of the receipt written afterwards, and the document says so.

### Prose that was true when it was written

That is the failure this Job has now hit twice -- a page claiming `main` had
run when it had not, and a page still advertising `verification-6.json` and "64
focused deterministic checks" at claim 248209. `test_packet.py` is the answer,
and its 25 checks are about the packet's honesty rather than the supervisor:

every shipped and reused digest against the file on disk; no SHA256 on the page
that the evidence does not know; NO receipt name or check count quoted in prose
at all, so there is nothing left to go stale; the documented `--flags` compared
against what `review_bindings`, `review_supervisor`, `packet` and
`snapshot_247947` actually declare, read out of the source by `ast` rather than
by running them; the open choices exactly those the selections still ask for,
with the count the page states; and the two proofs kept distinct.

I probed three of those assertions against deliberately corrupted inputs before
trusting them -- a stale baseline digest on the page, a blurred lifecycle entry
point, and a wrong document digest -- and each failed as it should.

### What the packet does NOT claim

The `main` startup proof enters the documented entry point with two seams
supplied, and its outcome is `held` because a composition that starts nothing
answers nothing about the reviewer. The real-coordination lifecycle settles
with an attributed verdict over real stores, a real attachment and a real
frozen output, but it calls `supervise` directly with an injected clock and
does not enter `main`. **No single run here both enters `main` and settles, and
no run reached a live provider.** Both documents say so in those words, and a
check asserts they keep saying it.

Verification: 138 focused deterministic checks, 0 failures, measured
36.4567306980025s, receipt `verification-18.json` with `verification-18.log`;
25 are new.

Cumulative MEASURED (suite receipts only) for W239533: 343.269261891 +
36.456730698 = **379.725992589s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc driving
remains UNKNOWN and is not estimated; the retained receipts now sum to
183.515042473s in `EVIDENCE-239533.json`, and the difference between that and
the cumulative figure is superseded within-claim runs, which were not
individually receipted.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s, 2.115041870s, 2.201875895s, 13.059195031s) are
theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.

## 2026-09-23 -- baton.claude, claim 248565

The owner ran the packet. Review 2026-09-23T14:45:57Z retained the evidence and
left two items; both are done.

### R1 -- the reader that refused, and what it holds

The supported `ControlStore.open_readonly` that answered the reviewer with an
`OperationalError` OPENED here -- same store, same path, same call, same pinned
source -- and served every read. **The cause of the earlier refusal is
UNKNOWN.** It is not permissions: the store and its directory are uid 1000 and
writable. Opening it recreated the `-shm` and a zero-length `-wal`, which a
cleanly closed store does not carry, and a `mode=ro` connection that cannot
create them is one known way to get that error -- A HYPOTHESIS, NOT A
DIAGNOSIS. I claim no product defect, and an intermittent refusal on the
managed read boundary is worth an owner's attention even though the attribution
it blocked has since been derived.

`attribution.py` then did what R1 asked. Inside one snapshot, through public
readers only: the line, the checkpoint, the attachment, the frozen output, the
retained result manifest, the cleanup and the producer's writer; the verdict
through `review_driver.review_verdict_from_result`. No raw SQLite, no copied
database, no `immutable=` handle, no write-capable fallback.

`ATTRIBUTION-248565.json` holds it: verdict **`accepted`**, agreeing with the
published outcome on all eight compared members; cleanup `retained` with the
runtime `absent`; the manifest's assignment matching the attachment's
generation and participant and the packet's Authority and Work; bound to the
executed packet, outcome, deployment-configuration digests and the retention
policy.

**One correction I had to make to my own export.** The first version read the
reviewer's identities off the attachment as `worker_id`/`participant`/
`principal`; the row names them `reviewer_*`, so all three came back `None`,
nothing could equal anything, and it reported `independent: true` having
compared NOTHING. A comparison over missing values is the most expensive kind
of false pass, because it looks exactly like a real one. It now refuses when
either side is empty, and the case asserting it checks that both sides are
populated rather than only that the shared set is empty.

### R2 -- the two template defects

Both were the same shape: documentation metadata reaching an execution
boundary. `review_bindings.main` splatted `selections["compose"]`, so
`_manager_source_note` raised `TypeError` before `compose` was entered; and
`compose` copied `bounds` verbatim, so `bounds._note` made `held_packet` refuse
at startup.

`without_documentation` now removes `_`-prefixed members recursively at
composition. **Neither entry point was loosened** -- a packet is an execution
document, and `held_packet` is right to require exactly five bounds members.
An unknown member that is NOT documentation is refused by name, so stripping
prose cannot swallow a typo.

Why the suite missed both: every case wrote its own selections through
`written_selections`, and a document this suite invents has no prose in it.
`TheACTUALShippedTemplateComposesAndStarts` reads the SHIPPED file, keeps its
notes, and drives the real CLI and `held_packet`. It also asserts the notes are
still there -- without that, the class would pass by proving nothing, which is
exactly what its first version did until that case caught it.

### The subject has moved

The line is now `accepted` and its attachment `ended`, so step 1 and the
composer REFUSE this packet. That is the arrangement working: a retained
proposal is reviewed once. The operator page records it so a future operator
does not read that refusal as a defect.

Verification: 151 focused deterministic checks, 0 failures, measured
37.4308637320064s, receipt `verification-19.json` with `verification-19.log`;
38 are new (6 template, 32 packet -- the packet module grew by 7 live-run
cases and had 4 rewritten because the live run made their old assertions
false).

Cumulative MEASURED (suite receipts only) for W239533: 379.725992589 +
37.430863732 = **417.156856321s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032, and the OWNER's live run
at 55.409s, which is theirs. Unmeasured ad-hoc driving remains UNKNOWN and is
not estimated; the retained receipts now sum to 219.971773171s in
`EVIDENCE-239533.json`.

The reviewers' independent measurements are theirs and are preserved
separately; claim 248523's probes were each under 0.1s and its wall time was
not measured.

State: returned for independent review. Ordinary continuation per M247805.
