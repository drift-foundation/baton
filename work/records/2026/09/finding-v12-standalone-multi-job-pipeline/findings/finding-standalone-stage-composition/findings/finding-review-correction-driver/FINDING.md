# Drive independent review and same-line correction

Ledger Work: W103076

Parent: `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/`

## Confirmed scope — 2026-09-06

Build the production driver that consumes a completed implementation stage,
launches an independently configured reviewer, freezes and attaches the
immutable checkpoint, records the verdict, and returns a changes-requested
result to the same private development line. Reuse accepted scheduler,
workspace, checkpoint, affinity, and runtime-profile interfaces. Do not own
proposal publication, integration, or shared process/configuration assembly.

The leaf must name disjoint production and test paths before implementation,
retain role/session separation, and prove replay across its durable cutpoints.
Adding and editing focused tests inside the named path set is explicitly
authorized.

## Reviewed contract — 2026-09-06

**Observed reusable interfaces:** `review_cycles.create_line`,
`grant_writer`, `freeze_checkpoint`, `attach_review`, `record_verdict`,
`integration_checkpoint`, `writer_boundary`, and `review_boundary` already own
line/checkpoint custody and assignment fencing. `PooledManagerOperations`
already owns hard reviewer independence and same-lane affinity. The driver
must compose those public interfaces and must not reproduce their tables,
filesystem namespace, profile commands, or principal comparisons.

**Observed scheduler gap:** the current Job Manager has no durable correction
act. `changes-requested` is terminal, `episodes.open_next` is reached only for
`abandoned-after-restart`, and one static implementation/review stage pair can
never receive the correction writer and second reviewer assignments the line
provider admits.

**Required correction act:** add one effectively-once Job Store operation,
bound to the exact line/checkpoint/verdict and both current stage episodes,
that atomically ends the completed implementation episode and the
changes-requested review episode and opens one successor episode for each.
It refuses unless both stages belong to the same Job and same Work, the
verdict is the current line's exact `changes-requested` verdict, neither
episode has already advanced, and no live allocation still owns either old
episode. Exact replay returns the same successor identities; any changed
operand collides. The resulting projection exposes the correction cycle and
then gates the new review episode on completion of the new implementation
episode. No offer, claim, attempt, runtime, checkpoint, or verdict state is
copied into the Job Store.

**Required ending order:** for implementation, prove the answered terminal,
freeze/verify the generic output and proposal manifest, call the integration
driver's publication seam while the producer assignment is live, then fence
and freeze the checkpoint, retain/clean up, and discharge only the exact
runtime-quiescence gate. For review, attach the read-only checkpoint before
runtime start; after a quiescent frozen review result, record the verdict,
clean up, and discharge its exact gate. `accepted` hands the frozen producer
account to the integration driver. `changes-requested` performs the correction
act above and grants the successor implementation assignment on the same line
from the rejected checkpoint. `rejected`, ambiguous, stale, or unreadable
evidence stays held and schedules nothing.

**Frozen path ownership:** production paths are
`v12/python/src/baton_v12/job_manager/review_driver.py` and existing
`job_manager/__init__.py`, `documents.py`, `episodes.py`, `projection.py`, and
`schema.py`. Focused test ownership is new
`v12/python/tests/job_manager/test_review_driver.py` plus only the expectation
updates forced by the schema/status change in `test_documents.py`,
`test_recovery.py`, `test_restart.py`, `test_status.py`, and `test_store.py`.
No other production or existing test path is authorized without targeted
review. Registration in `tools/parallel_test.py` belongs to W103083.

**Required regressions:** accepted first review; one and ten
changes-requested rounds on one line without another source clone; exact
replay at output-publication, writer fence, checkpoint freeze, review attach,
verdict, gate satisfaction, and correction advance; crash between every pair;
same-Work enforcement; stale checkpoint/verdict and changed-operation
collision; active allocation/writer/reviewer refusal; hard worker/participant/
principal separation; old checkpoints unchanged; and no integration handoff
for rejected, ambiguous, or unreviewed output.

## Implementation — 2026-09-06 — baton.claude

The correction act and the review driver are built. Three rulings came out of
building them, and two of those came from the act's own tests refusing it.

**AN IDENTITY DERIVED FROM STATE THE ACT ITSELF MOVES IS NOT AN IDENTITY.**
The correction operation was first named by the two episode NUMBERS the round
was leaving. That is stable for exactly as long as the act has not committed:
the moment it has, both stages are on their successors, so an exact retry
computed a DIFFERENT name and opened a third round. A retry that advances the
pipeline is not a retry. The second spelling named the verdict, which does not
move -- and was still wrong, because a caller presenting any other verdict
identity got a different name and a second round on the same checkpoint. A
line stays `correction-ready` from the verdict until its next writer is
granted, so nothing else was holding that door.

The identity is the CHECKPOINT BEING CORRECTED. It does not move, one
checkpoint earns one round, and unlike the verdict it is PROVED rather than
carried: the line must be corrected from exactly this frozen checkpoint. The
general form is worth keeping: an effectively-once identity must be derived
from something the act does not change, and preferably from something the act
also proves.

**A SIGNATURE IS THE AUTHORIZATION; THE RESULT IS THE OUTCOME.** The first
signature carried the ended episode numbers and the successor identities --
what the round DID -- so an exact retry rebuilt it from the moved state and
collided with its own committed work. The signature now carries only what
permits the round: Job, Work, line, checkpoint, verdict. What the round did is
the journalled RESULT, and replaying that is what returns the same successors.
A different verdict for the same checkpoint collides, which is what the
contract asked for.

**THE CUSTODY PROOF READS THE OWNER'S ROWS THROUGH THE OWNER'S READERS.**
`line_of` answers `correction-ready` for exactly one reason -- `record_verdict`
recorded a `changes-requested` disposition against the line's current
checkpoint -- so a line that is `correction-ready` and whose
`current_checkpoint_id` is the named frozen checkpoint IS the statement that
this checkpoint's review asked for changes. No verdict table is copied into the
Job store, and the Authority and Work are proved because a line is one
`(authority_uuid, work_id)` pair.

**PUBLICATION BEFORE THE FENCE IS DRIVEN, NOT ASSERTED.** The seam records the
line's own state when it is asked, and it is `writing` -- the writer is not yet
fenced. W103068's reproduction is what says the alternative refuses; this is
what says the driver does not take it.

**AND THE ENDING'S MIDDLE IS UNCHANGED ON PURPOSE.** This leaf's contract lists
"retain/clean up" after the checkpoint freeze. Only the CLEANUP can be there:
`authorize_cleanup` refuses while the assignment is live, and ending the
assignment before intake can quarantine the result if collection races that
ending, which is why W44657 put intake and retention first. Recorded here
rather than silently reordered.

## Independent review correction and targeted scope expansion — 2026-09-06

The candidate in `review-2026-09-06T17-07-11Z.md` is not accepted. Its
operation identity insight is retained, but the receiving operations do not
yet prove the identities or atomic preconditions that identity records.

**Exact verdict proof:** line state and current checkpoint prove that some
`changes-requested` verdict exists, not that the caller-supplied `verdict_id`
is that verdict. The Worker Manager owner must expose one typed read for the
exact current changes-requested verdict, including its line, checkpoint,
disposition, and retained digest bindings. `advance_correction` re-reads that
document and requires the supplied selector to equal it before a first
correction can write. A bogus verdict on the first call refuses; a changed
verdict after commit remains an operation collision.

**Owned Job-stage account:** the implementation and review documents are
selectors, not evidence. `advance_correction` re-reads both exact stages from
the Job Store, owns their complete stage documents, and derives Job, Work,
kind, current episodes, and successor identities only from those reads. A
caller-mutated `job_id`, `work_id`, or `kind` cannot join stages that the store
records under different Jobs or Works.

**Atomic allocation precondition:** the transaction that ends the two current
episodes and opens both successors also rechecks that neither old attempt has
a `reserved` or `recovery-required` allocation. The preflight remains useful
for diagnostics but does not authorize the write: a reservation committed
between preflight and correction must make the correction transaction refuse
and roll back both stages.

**Ending selector and capability preflight:** before stopping a runtime or
performing another external/durable act, `end_implementation` re-reads the
writer and binds its attempt and generation to the selected attempt;
`end_review` re-reads the attachment and binds its attempt to the selected
attempt. The Worker Manager owner exposes a typed attachment read rather than
the driver opening its table. Both endings validate the complete adapter and
Authority-port capability surfaces they will consume before the first stop.
Malformed adapter answers become typed refusals at the boundary rather than
raw attribute errors after an external act. A writer/attempt or
attachment/attempt cross-wire spends nothing.

**Held outcome:** `rejected` remains a recorded held result. A stale,
ambiguous, unreadable, or otherwise unrecordable verdict also schedules no
correction or integration; the driver must return or propagate one explicit
held account consistent with the public outcome contract, rather than claim
that every such case returns `held` while allowing an unclassified exception
to escape. Caller-malformed arguments remain refusals and are not rewritten as
review evidence.

**Expanded frozen path ownership:** the original production/test paths remain
owned. The minimum owner-read surface additionally authorizes edits to
`v12/python/src/baton_v12/worker_manager/review_cycles.py`,
`v12/python/src/baton_v12/worker_manager/__init__.py`, and focused existing
tests in `v12/python/tests/manager/test_review_cycles.py`. No Worker Manager
schema/table mutation and no other production or existing-test path is
authorized. Existing-test changes in that exact file are explicitly scheduled
for the new verdict/attachment reads and their corruption/refusal cases.

## Re-review — 2026-09-06 — the four receiver findings

`review-2026-09-06T17-07-11Z.md` accepted the correction identity and the
publication-before-fence order and found three [P0]s and one [P1]. All four
were the same mistake in different places, and naming it is worth more than
naming them: **THE COMPOSITE BELIEVED ITS CALLER.** It took a verdict identity
and only checked its shape, it took stage documents and never re-read the rows
they claimed to be, it took a writer and an attachment beside an attempt and
never asked whether they were that attempt's, and it proved an allocation
outside the transaction that relied on the proof.

**A PROOF THAT SOMETHING EXISTS IS NOT A PROOF THAT THE CALLER NAMED IT.** The
line proof said a `changes-requested` verdict exists for this checkpoint. It
did not say the caller had named THAT verdict, so the first correction of any
checkpoint accepted `verdict-somebody-elses` and persisted it. The caller now
hands over the recorded DOCUMENT and it is compared with what the owner
committed under its own operation identity, read through
`ControlStore.operation_record`. The provider publishes no verdict reader, and
re-deriving its identity rule here would be a second spelling of somebody
else's derivation; the journal needs neither.

**A RECEIVER A CALLER CHOOSES IS A RECEIVER A CALLER CAN CROSS-WIRE.** The act
read `stage_id`, `kind`, `job_id` and `work_id` off caller dictionaries, so
mutating a real document made the preflight treat two unrelated stored stages
as one pair. It names the JOB now and reads the pair. The same shape appeared
twice more in the driver: the implementation ending fenced a separately chosen
writer after publishing, and the review ending recorded a verdict for a
separately chosen attachment after freezing -- two live lines could publish
A's output and answer with B's checkpoint. The writer is bound to the attempt
and generation before the first external act, and the review ending has no
second selector at all: the attachment names the attempt, and the owner's
committed record is what says so.

**A PRECONDITION PROVED OUTSIDE THE TRANSACTION IS A PRECONDITION THAT DOES
NOT HOLD.** The allocation check ran before `transact` took its write lock, so
a reservation committed in between survived while both successors opened. It
is asked again inside the act, and a case sequences the answers so the
preflight sees nothing and the guarded proof sees a reservation.

**AND THE ORDER OF DISCOVERY IS PART OF THE CONTRACT.** Only the publication
seam was typed, so an adapter carrying `stop` and nothing else was ASKED TO
STOP a container before anything noticed it could not finish, and a missing
method arrived as a raw `AttributeError`. Every capability an ending reaches is
proved while nothing has happened, and a stop answer that is not a document
refuses rather than faulting.

**THE HELD BRANCH THE CONTRACT PROMISED NOW EXISTS**, and it splits on where a
refusal comes from rather than on how it reads. `refused`, `integrity`,
`policy`, `stale-assignment` and `runtime-observation` from the verdict are
statements about the evidence and become a typed held account with cleanup
deliberately NOT authorized -- the assignment stays live and the runtime stays
where an operator can look at it. `unavailable` and `ambiguous` escape: a
transport that is down says nothing about the review, and an operation nobody
can say committed must not be reported as an ending that finished. A
disposition the provider does not have is caught before the ending starts,
because a caller's malformed argument is not something a reviewer left behind.

## Second independent re-review — 2026-09-06

The preceding implementation account is not accepted and its statement that
`ambiguous` escapes is **superseded**. The confirmed reviewed contract above
still rules that ambiguous review evidence is held and schedules nothing;
only unavailable transport is not review evidence and may escape for retry.

**Owner-read correction remains required.** The authorized Worker Manager
reader paths were not changed. Instead, the Job Manager duplicates
`review-line.attach-review` and `review-line.verdict` operation identity
spellings, reads generic journal rows through `ControlStore.operation_record`,
and parses their raw signature/result JSON. That is not the typed semantic
owner read the prior review required. The Worker Manager must publish typed
attachment and verdict reads that cross-bind their materialized rows to their
committed acts; the Job Manager consumes those documents and carries no
provider operation-kind or journal-shape knowledge.

**Atomic pair correction still has a partial-commit path.** Inside
`advance_correction`, the implementation episode is ended and its successor
inserted before the review episode's guarded update. If that second update
affects no row, the candidate raises a `durable=True` refusal. `JobStore`
records a durable refusal without rolling back the act savepoint, so the first
stage changes commit. A measured interleaving left implementation episode 1
`superseded-by-correction`, implementation episode 2 live, and review episode
1 `declined`. The guarded mismatch must be non-durable (or all guards must run
before either mutation) so every refusal rolls back both stages and consumes
no correction identity.

**Complete ending preflight remains required.** `RUNTIME_ADAPTER` names only
`stop`, `list`, `observe`, and `seal`, while the same ending later requires
`collect`, `retain`, `destroy`, `normalize_directory`, and the custodian image
identity. The port preflight checks only presence of `participant`; later acts
require `assignment_of` and `cancel`, and the participant is not compared with
the selected attempt before `_quiesced` calls `stop`. The checkpoint profile's
required `freeze`/`validate` or `validate` capability is also discovered late.
A measured wrong-participant port produced `refused/capability` only after one
stop call. Both endings must own every static adapter, port, and profile
capability and bind the port participant to the owner-derived attempt before
the first external act.

Required regressions now include the review-stage-ended-at-transaction-cutpoint
case (both Job stages remain byte-unchanged), each omitted late capability, a
wrong non-null port participant (zero stop calls), typed owner-reader
corruption/refusal cases, and an `ambiguous` verdict refusal returning the
documented held account.

## Shared gate test-scope expansion — 2026-09-06

The two authorized Worker Manager exports necessarily participate in four
shared declaration gates. The implementer edited those paths before obtaining
the targeted review required by the frozen scope; that sequencing is not
accepted. The current changes have now been independently examined and the
minimum expansion is approved so they may be retained and corrected with the
candidate:

- `v12/python/tests/manager/test_dependencies.py`: classify `verdict_id` as
  the durable selector accepted by `verdict_of`;
- `v12/python/tests/manager/test_boundary_inventory.py`: move the single
  `checkpoint_verdicts` adoption site to `_verdict_row`, declare its exact
  lookup-key exception, and route that site through the existing probe;
- `v12/python/tests/manager/test_secrets.py`: classify only the two new typed
  readers as returning owned rows rather than constructed artifacts;
- `v12/python/tests/manager/test_text_sweep.py`: drive the single identity
  operand of each new reader.

No other assertion, expected behavior, registry, production path, or shared
test change is authorized. Future required scope must return for review before
editing.

## Third independent re-review — 2026-09-06

The atomic correction pair, complete verb-presence checks, exact port actor,
and ambiguous-held behavior are corrected. The candidate still does not
satisfy its semantic owner-read or pre-act identity contracts.

**Observed P0:** `review_of` compares only attachment identity and checkpoint
with the attach operation's small result. It never reads the owner's committed
signature and therefore does not bind the row's immutable runtime attempt,
generation, reviewer worker, participant, principal, or line. A measured row
rewrite from `review-attempt-1` to the existing `writer-attempt-1` was accepted
and returned by `review_of`. `end_review` would consequently stop and freeze
the writer selected by the corrupted row—the cross-wire the reader exists to
prevent.

`verdict_of` likewise compares only nine of the verdict row's immutable
members with the full committed result and returns unowned retained evidence.
A measured rewrite of `review_result_digest` to a different valid digest was
accepted. The reader must adopt and bind every immutable row member represented
by the committed verdict, parse and validate its retained review-result and
fence documents, and verify their digests. Unreadable or internally
contradictory verdict evidence must refuse before a correction advances.

**Observed P1:** static identity and profile compatibility preflight remains
incomplete. `_typed` checks only that `custodian_image_digest` is non-null,
although the custody owner later requires stored text. It checks profile verbs
but neither owns the profile name nor proves it is the selected line's profile.
A measured implementation ending with a fully callable but wrong-name profile
stopped the runtime once, then refused `policy/profile-uncertified` at
`freeze_checkpoint`. Both endings must own the custodian identity and profile
name and prove the selected line/profile match before `_quiesced` performs the
first stop. Add malformed custodian/name and valid-wrong-profile cases with
zero stop calls.

These corrections fit the expanded candidate path set; no further scope is
required.

## Second re-review — 2026-09-06 — the owner reads, and half a correction

`review-2026-09-06T17-23-54Z.md` found two [P0]s and two [P1]s. All four are
corrected, and two of them replace answers I argued for and got wrong.

**A JOURNAL READ IS NOT AN OWNER READ.** My previous round removed the
cross-wires by reconstructing the provider's operation identities and parsing
its journal rows and signatures inside the composite. That proved the right
facts and kept a copy of the wrong thing: the shape of a journal only
`review_cycles` gets to change. The typed readers now live at the owner --
`review_of` and `verdict_of` -- and each cross-binds the materialized row
against the committed act that wrote it. The composite asks a question and
reads a document.

Adding them extracted `_verdict_row`, because `checkpoint_verdicts` was
adopted inline by `integration_checkpoint` and a second adoption would be two
column contracts that can drift. That is the manager's boundary inventory
working as designed: it refused to let a second reader exist without one.

**A DURABLE REFUSAL SEALS WHAT THE ACT ALREADY WROTE.** The correction guarded
and mutated one stage at a time and raised its guard as a DURABLE refusal --
which `JobStore.transact` commits without rolling the act's savepoint back. A
review episode ending at the cutpoint therefore left the implementation stage
superseded with a live successor and the review stage untouched: half a
correction, recorded, from an act whose whole premise is both or neither.

Two things fix it and both are kept. Every guard for the whole pair now runs
before the first row moves, and the refusals are ORDINARY rather than durable,
so a guard that somehow fires after a partial write still unwinds. The general
rule: **a durable refusal is a COMMITTED OUTCOME, so it may only be raised by
an act that has written nothing it would not want kept.**

**A CAPABILITY SET IS THE UNION OF WHAT THE COMPOSITION REACHES.** I typed the
four verbs this module calls and left `collect`, `retain`, `destroy`,
`normalize_directory`, the custodian identity, both port verbs and the profile
to be discovered by the operations it composes -- after the stop. And a
participant that was proved non-null was never COMPARED with the attempt, so a
session acting for somebody else reached `refused/capability` from custody with
a container already stopped. Both are preflight now.

**AND AN IMPLEMENTATION PARAGRAPH IS NOT A SUPERSESSION.** I moved `ambiguous`
out of the held set and argued for it in a module comment. The confirmed
contract says ambiguous review evidence is held; the place to change that is a
recorded decision, not a docstring. `ambiguous` is held. `unavailable` still
escapes, because a transport that did not answer is a statement about
infrastructure rather than about the review.

## Third re-review — 2026-09-06 — a reader answers for the WHOLE row

`review-2026-09-06T17-50-59Z.md` accepted the atomic pair, the exact
participant, the verb presence and the ambiguous-evidence correction, and
found two more. Both are the same rule at two depths.

**A READER THAT PROVES SOME OF A ROW ANSWERS FOR ALL OF IT.** `review_of`
compared the attachment and checkpoint identities and returned the rest --
including `runtime_attempt_id`, which is foreign-key valid for any attempt, so
a rewritten row was answered without refusal and a composite that trusts the
answer stops and freezes another lane's runtime. `verdict_of` claimed to prove
every member and covered nine of them: the reviewer's own identity, the sealed
base/head/tree account and the retained result and fence were all unbound, and
rewriting `review_result_digest` to another well-formed digest was accepted.

The correction is not more comparisons but a different SOURCE. An act's RESULT
is whatever it chose to return; its OPERANDS are the whole of what it was
authorized with, and they are in the signature this module itself built. Both
readers now adopt the committed operands and cross-bind every immutable member
against them, and `verdict_of` additionally parses the retained result and
fence through their own owners and recomputes both digests. What a reader
answers is now exactly what an act committed.

**AND A COMPATIBILITY THAT EVERY OPERATION CHECKS IS ONE THE COMPOSITE MUST
CHECK FIRST.** A fully callable profile named `other-profile` handed to an
ending prepared under this line's profile recorded one stop before
`freeze_checkpoint` refused `policy/profile-uncertified`. The comparison is
made now against the line resolved from the owner-bound writer or attachment,
so it cannot be satisfied by naming an agreeable line either. The custodian
identity is owned as TEXT rather than merely non-null, for the same reason: the
custody boundary signs an act with it, and any other shape passed here and
refused there, after the stop.

The general form, which is worth more than either instance: **A PREFLIGHT IS
NOT THE OPERANDS THIS FUNCTION READS. It is every operand any operation in the
composition will refuse on -- and where that operand is a comparison rather
than a presence, the comparison belongs in the preflight too.**

## Fourth independent review — 2026-09-06

**Confirmed:** the third-review corrections satisfy the remaining owner-read
and pre-act identity contracts. `review_of` now binds the attachment's attempt,
generation, reviewer identities, checkpoint, and line to the committed attach
operands and checkpoint owner. `verdict_of` binds all immutable verdict fields
to the committed verdict operands, adopts retained review-result and fence
documents through their existing validators, and recomputes both retained
digests. The exact prior attachment-attempt and verdict-digest corruptions now
refuse.

Both endings own the custodian and profile names as text, resolve the line from
the owner-bound writer or attachment, and compare the profile with that line
before `_quiesced` can call `stop`. The implementation and review wrong-profile
cases and both malformed-custodian cases spend no stop call. The previously
accepted atomic correction pair, exact participant comparison, complete
capability presence, and ambiguous-held branch remain intact.

**Verified:** 78 combined focused driver and owner-reader tests passed; the
complete Job Manager discovery passed all 387 tests; and the three shared
declaration modules passed 115 tests with one expected skip. Six isolated
regressions replaying the prior corruptions and pre-stop identity cases passed.
All seven production paths compile, all 13 candidate paths are diff-clean, and
the four approved shared-test digests are unchanged from the third review.

No finding remains. Deployment-owned OCI/custody cutpoint coverage remains in
W103083 exactly as the accepted leaf boundary specifies.
