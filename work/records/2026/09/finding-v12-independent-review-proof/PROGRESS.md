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
