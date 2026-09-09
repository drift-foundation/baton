# Progress

## 2026-09-08 — baton.claude, claim 120461

### Revalidation before editing (PLAN step 1)

Read this dossier, the parent FINDING/PLAN, the append-only
`../../review-2026-09-08T15-46-16Z.md`, the reviewer's
`../../evidence/review-120378-probe.{py,json}` and `review-120378-audit.json`,
and the linked approved CONSUMER-RECOVERY-PLAN-2026-09-08.md.

**The four owned paths are byte-identical to the reviewed candidate**, so the
review's source anchors still hold and nothing about it needed re-deriving:

    8da734ac757126ad70cc64556c8568384fa4a6283f0304cc0eaf17a92a1bae16  ending.py
    8a15446c04ceec1e43bcafc41e22e87cf0419a4fff78daf03b06ffa47cea8796  projection.py
    f77a12f80c66e8dfb9ed700177b90fa4bda841788396304189f00230dfbd9c83  manager.py
    a0ca21e92fb5ddf4721dff987ed68e459c874102440fbff1b0cf4e92399f63c7  test_ending.py

**All three [P1] Job-journal reproductions confirmed against that baseline**
before any edit, from the reviewer's own probe output: a foreign-Authority
registration returned a committed intent; an ordinary settlement with all three
required references null projected `completed` and left the dependent `queued`;
and a genuine review settlement copied to the implementation stage's selected
settlement identity was read as that stage's own, emptied pending discovery,
projected `completed` and opened the dependent.

**The review's diagnosis is accepted without qualification.** My own handback
claimed "every selector is compared back against the stage and episode rows
before a record is used". That was true of the three functions that WRITE and
of `attempt_of`; it was false of `intent_of` and `settlement_of`, which are the
two the projection and the sweep actually call. What those two proved -- member
set, kind, committed state, self-signature -- is satisfied by any legitimate
record of this build, including one belonging to another stage. Signature
integrity is a statement about how a record was made, not about whose it is.

### What was corrected, in the two owned source paths

**`ending.py` — one derivation for the identity, used to store and to prove.**
`_operation_id(kind, stage_id, episode)` is now the single spelling behind
`intent_operation_id` and `settlement_operation_id`, because a check that a
document belongs at the identity it was selected by is only a check if it
derives that identity exactly as the write did.

**`ending.py` — `_committed` asks three questions it was not asking.** After
the existing kind/state/member/self-signature proofs it now requires that (1)
the document's own `stage_id` and `episode` DERIVE the identity it was selected
by, (2) its selectors still bind to this store's stage and episode rows through
the same `_bound` proof a write makes, and (3) its assignment is this store's
Authority and its stage's Work. None is deferred to a caller: the callers are a
projection and a sweep, and neither can know.

**`ending.py` — `_assignment` binds the Authority as well as the Work.**
`authority_uuid` and `work_id` are a pair and this store is bound to exactly
one Authority -- the namespace W83781 makes every episode identity derive in --
so the pair is compared against `store.authority_uuid` rather than merely
parsed. This closes the write defect and the read defect with one rule.

**`ending.py` — `settlement_of` is paired with its obligation.** It requires
the settlement to name the intent identity at its own position, requires that
intent to exist, and requires every selector AND the assignment to agree with
it. A caller that already holds the intent passes it, so the pair is decided
from one moment's state; `_UNREAD` distinguishes "nobody has read it" from a
proven absence, which is what lets an orphan be recognised.

**`ending.py` — `ending_of` seeks the settlement even when the obligation is
absent.** A settlement standing alone is a store this build cannot explain --
an obligation lost, or an ending recorded as finished that nobody registered --
and answering `None` would hand the stage back to the generic cleanup rules,
which is precisely the state the obligation exists to stop being mistaken for a
finished one.

**`ending.py` — `_evidence` requires its three references to be present.** A
member that may be null is a member that is not required. Optional references
are OMITTED when there is nothing to name, which is what a pass with no gate to
discharge does, rather than present and empty.

**`ending.py` — `pending_endings` reads both halves through `ending_of`.** What
it skips is now an obligation whose own settlement it has proved, not merely a
record standing at the settlement's identity.

**`projection.py` — the stage row is handed down.** `stage_states` already
holds the row the reader must prove the record against, so it passes it rather
than making the reader look it up again; a second lookup would be a second
moment, and it would make the pass quadratic in stages.

**`manager.py` is unchanged.** Its `_recover_endings` calls `pending_endings`
and `attempt_of`, both of which now refuse what they used to accept, so no edit
there was needed to close any part of the finding. Owning a path is not a
reason to change it.

**A refusal propagates out of the projection, and that is the chosen answer.**
`episodes.live_of` already refuses a stage with two live episodes rather than
choosing between them; a control plane that cannot describe the store it holds
must say so. The two alternatives here are both worse than a visible refusal:
answering absence hides an unfinished ending, and answering "settled" opens a
dependent stage on a stranger's record. This is stated so a reviewer can
disagree with it deliberately rather than discover it.

### Verification

**Question, commands and budget recorded before execution.** The question: do
the three confirmed reproductions now refuse without becoming absence, skipping
recovery or opening a dependent, and does the added ownership validation change
the meaning of any existing Job-manager assertion? Retained parent evidence
cannot answer it -- it was taken against the defective bytes.

Scope, and why no broad sweep: the two changed sources are `ending.py` and one
call site in `projection.py`, so what can be affected is the ending module plus
every module that drives `stage_states`/`status`. The canonical parallel gate
is still not runnable (the registry line remains W119114's), and repeating the
5099-test sweep would answer no question this correction raises. Budget: the
reviewer's three reproductions re-run, then those modules once, about 30
seconds.

    python3 <this record>/evidence/correction-120461-probe.py
    PYTHONPATH=src:tests:. python3 -m unittest tests.job_manager.test_ending
    PYTHONPATH=src:tests:. python3 -m unittest \
        tests.job_manager.test_sweep tests.job_manager.test_exchange \
        tests.job_manager.test_status tests.job_manager.test_scheduling \
        tests.job_manager.test_recovery tests.job_manager.test_restart \
        tests.job_manager.test_launch tests.job_manager.test_delegation \
        tests.job_manager.test_tool tests.job_manager.test_review_driver

Results follow as each run completes.

#### Results

**The three reproductions, re-run unchanged.** `evidence/correction-120461-probe.py`
is the reviewer's own script with the same fixtures, the same public journal
technique and the same three scenarios; only the expectation changed, so what
it measures is the correction rather than a new fixture. Output is retained at
`evidence/correction-120461-probe.json`, 0.010s.

- `foreign_authority_registration` — was: a committed intent. Now:
  `refused/operation-collision`, "names Authority '999…' and this Job store is
  bound to '000…a'".
- `null_required_evidence` — was: settlement committed, implementation
  `completed`, dependent `queued`. Now: `integrity/schema` on the reference,
  implementation `answering`, dependent `blocked`, and the stage is still
  enumerated as pending. The obligation survives the refused settlement, which
  is what the refusal is for.
- `foreign_settlement_under_selected_identity` — was: the copied review
  settlement read as the implementation's, discovery empty, implementation
  `completed`, dependent `queued`. Now all four of the reader, the discovery,
  the implementation projection and the dependent projection raise
  `refused/operation-collision` naming both identities. The review stage's own
  settlement still reads back as its own, so the correction refuses the
  stranger without damaging the record it was copied from.

**Focused suites.**

    tests.job_manager.test_ending                     38 tests, OK
    10 modules driving stage_states/status/advance    363 tests, OK, 3.6s

`test_ending` is 38 where the reviewed candidate had 29. Nine cases were added
and no existing case was edited, renamed, removed or weakened:
`ASignatureIsNotOwnership` (6) drives the copied foreign settlement, a record
filed under another episode's identity, an orphan settlement, a settlement
naming another obligation, a settlement disagreeing with its own obligation's
assignment, and a recorded foreign Authority — each asserting that the reader,
`pending_endings` and `status` all refuse rather than any of them answering.
`WhatAWriteWillNotAcceptEither` (3) drives the two accepted write operands the
review found, and pins that an optional reference is omitted rather than
emptied.

The 363 include `test_review_driver`, which drives `status` and
`advance_correction`: it is W120425's path and was NOT edited here, but the
`projection.py` call-site change can reach it, so it was run rather than
assumed. No broad sweep: the two changed sources are `ending.py` and one line
in `projection.py`, the canonical parallel gate is still not runnable, and
repeating the 5099-test sweep would answer no question this correction raises.

#### Candidate bytes and modes

    545c63801b87cb2db4e02d19ddfac022c99ebd8a51ee6d09e0cc36b817126192  664  v12/python/src/baton_v12/job_manager/ending.py
    4fd1a92a59c9bc0295016c345660db8f502502ee75a8b2804d528952c62609ed  664  v12/python/src/baton_v12/job_manager/projection.py
    f77a12f80c66e8dfb9ed700177b90fa4bda841788396304189f00230dfbd9c83  664  v12/python/src/baton_v12/job_manager/manager.py
    d7617628b7d6675bd2bf2f37615a88444ec051907cb02e49ef3ed8a893a27abc  664  v12/python/tests/job_manager/test_ending.py

`manager.py` is byte-identical to the reviewed baseline. The only other files
this claim wrote are this record's own `PROGRESS.md`, `PLAN.md` and
`evidence/correction-120461-probe.{py,json}`. `review_driver.py` and
`test_review_driver.py` are untouched and remain W120425's. No Git operation of
any kind was performed.

#### Interface, unchanged for the consumer

The public surface W119114 was handed is the same: `register_ending`,
`settle_ending`, `intent_of`, `settlement_of`, `ending_of`, `pending_endings`,
`attempt_of`. The readers grew an optional `stage=` operand for callers that
already hold the row, and `settlement_of` an optional `intent=`; both default to
reading for themselves, so no existing call site changed. What DID change for a
consumer is what a settlement must carry: `result_id`, `manifest_digest` and
`receipt_digest` must now be present and non-null, and the assignment must name
this store's Authority. Both are requirements the consumer already satisfies —
it holds all three references from the driver's own answer, and its assignment
comes from `assignment_of` on the same Authority.

#### State

Awaiting independent review at `baton.bug`. This claim corrects the journal
ownership finding only. The historical implementation resume and its real
component proof are W120425's and are not touched or claimed here; W119733
retains the joined six-path acceptance, and the `tools/parallel_test.py`
registry line remains allocated elsewhere and still blocks the canonical gate.

## 2026-09-08 — baton.claude, claim 120627 (second correction pass)

### Revalidation

Read `review-2026-09-08T16-00-28Z.md` and its retained
`evidence/review-120507-probe.{py,json}`. The four owned paths were
byte-identical to the hashes that review audited, so its source anchors held
without re-deriving.

**Both findings are accepted.** [P1] is exact: `_committed` owned the member
SET and then reached past the rest of the document, so every value outside the
selectors and the assignment was unowned on readback — and `_evidence` was
reached only by the writer. Validating on the way in does not discharge a
readback contract, because the process that wrote a durable value is not the
process that reads it; that is the reason this package owns its own store's
rows everywhere else.

[P2] is exact too, and the reasoning I gave for the operands was wrong in both
halves. Matching members are not ownership: a public reader cannot tell a
document a caller read from one a caller invented. And the "one moment's
state" the `intent=` operand was supposed to buy never existed — two ordinary
reads on one connection are two reads, not a transactional snapshot. I should
not have claimed it.

### What was corrected

**One validator per record kind, used by both sides.** `_intent_document` and
`_settlement_document` own the WHOLE payload — every selector, the assignment's
shape, the disposition, the terminal digest, both retention operands, the
obligation identity and the nested `evidence` — and a `_PAYLOAD` table names
which one owns which kind. `_committed` runs it before anything else looks at
the record; `register_ending` and `settle_ending` compose through the same
function, so there are not two contracts that agree today.

**`_assignment` split.** `_shaped_assignment` is the pure document contract
both sides hold a record to; the store-ownership comparison (this Authority,
this stage's Work) stays where the store is and composes onto it.

**Every optional operand is gone from the public readers.** `intent_of`,
`settlement_of` and `ending_of` are `(store, stage_id, episode)` and
`attempt_of` is `(store, intent)`. The private `_intent_of`, `_settlement_of`
and `_ending_of` carry a `rows` argument that no caller can reach: it is the
one stage-row read `pending_endings` performs for a pass that asks about many
stages, built inside that call from this store's own rows. The public entries
take nothing and read for themselves, which is [P2]'s requirement that a
public reader establish the same owned result with and without it.

**`projection.py` hands nothing down.** The `stage=stage` I added last pass is
removed. It saved one row lookup per stage and made the ownership proof depend
on who was asking.

**`manager.py` is again unchanged**, and `attempt_of`'s signature change is the
only thing its `_recover_endings` sees — it never passed the operand.

### Verification

**Question, commands and budget recorded before execution.** The question: do
the review's six reproductions now refuse where required, does an honest
record still read back unchanged through the same validator, and does the
readback ownership change the meaning of any existing Job-manager assertion?
The retained evidence cannot answer it — it was taken against the previous
bytes. Budget: the six reproductions re-run, then the ending module and the
modules that drive `stage_states`/`status`, about 30 seconds. No broad sweep:
the two changed sources are `ending.py` and one line of `projection.py`, and
the review asks for the smallest affected set.

    python3 <this record>/evidence/correction-120627-probe.py
    PYTHONPATH=src:tests:. python3 -m unittest tests.job_manager.test_ending
    PYTHONPATH=src:tests:. python3 -m unittest \
        tests.job_manager.test_sweep tests.job_manager.test_exchange \
        tests.job_manager.test_status tests.job_manager.test_scheduling \
        tests.job_manager.test_recovery tests.job_manager.test_restart \
        tests.job_manager.test_launch tests.job_manager.test_delegation \
        tests.job_manager.test_tool tests.job_manager.test_review_driver

Results follow.

#### Results

**The six reproductions, re-run unchanged** as
`evidence/correction-120627-probe.py` — the reviewer's script with the same
fixtures, the same public journal writes and the same six scenarios. Output at
`evidence/correction-120627-probe.json`, 0.014s.

- `null_references_on_read`, `non_document_evidence`,
  `unknown_evidence_member` — were: read clean, discovery empty,
  implementation `completed`, dependent `queued`. Now: the reader, the
  discovery and the projection all raise `integrity/schema` naming the exact
  member ("settled manifest_digest is durable text; this is none"; "settled
  evidence is one exact document; this is a list"; "also carries unowned").
- `malformed_intent_payload` — now `integrity/schema` on the first bad member
  ("worker disposition is durable text; this is a list"), from all three
  decisions.
- `caller_intent_bypasses_orphan_refusal` — the ordinary reader refuses
  `refused/precondition` ("settles an obligation this store never registered")
  and the bypass has no surface at all: `settlement_of() got an unexpected
  keyword argument 'intent'`, public parameters `(store, stage_id, episode)`.
- `caller_stage_bypasses_stored_work_binding` — the ordinary reader refuses
  `refused/operation-collision` naming both Works, and `intent_of() got an
  unexpected keyword argument 'stage'`.

Two of the six are now argument errors rather than refusals, deliberately: the
correction removed the operand rather than adding a check to it, so there is
nothing left to refuse. A control asserts the public signatures directly, so
the absence is measured rather than inferred from a `TypeError`.

**Focused suites.**

    tests.job_manager.test_ending                     47 tests, OK
    10 modules driving stage_states/status/advance   374 tests, OK, 4.5s

`test_ending` is 47 where the last handback had 38. Nine cases were added and
no existing case was edited, renamed, removed or weakened:
`TheWholePayloadIsOwnedOnTheWayOutToo` (5) drives stored evidence that is null,
not a document, unknown-membered, short a member or wrong-typed; a stored
intent payload with four wrong types; each intent payload member on its own; a
stored obligation identity that is null; and — the positive half, which is what
stops this from being a wall — an honest record reading back unchanged through
the same validator, still projecting `answering`, still enumerated pending, and
still settling into `completed` with the dependent `queued`.
`NoCallerDocumentStandsInForAStoredRecord` (4) pins the public signatures,
drives the orphan and wrong-Work records through the ordinary readers, and
measures that the many-stage pass answers exactly what the single reads answer.

The 374 include `test_review_driver`, which is W120425's path and was not
edited here but which drives `status`.

No broad sweep. The registry line landed under W120519 so the canonical gate is
runnable again, but repeating it would answer no question this correction
raises, and the review asked for the smallest affected set.

#### Candidate bytes and modes

    3d9c4f1914806e2b38543642c483d74628da9e1cbd36a24fa4cc04bf75ea2b99  664  v12/python/src/baton_v12/job_manager/ending.py
    b47c469641df61b6516f590602c6930968a71d5b7f24cf7e8856b6e95197ae9e  664  v12/python/src/baton_v12/job_manager/projection.py
    f77a12f80c66e8dfb9ed700177b90fa4bda841788396304189f00230dfbd9c83  664  v12/python/src/baton_v12/job_manager/manager.py
    30a0b759754bb78fd27e99ab6e9ea1a76949d4b644bda5f3b42fea0e72a796d9  664  v12/python/tests/job_manager/test_ending.py

`manager.py` is still byte-identical to the original reviewed baseline. The
only other files this claim wrote are this record's `PROGRESS.md`, `PLAN.md`
and `evidence/correction-120627-probe.{py,json}`. No Git operation was
performed.

#### Interface note for W119114

The public reader signatures are now `intent_of(store, stage_id, episode)`,
`settlement_of(store, stage_id, episode)`, `ending_of(store, stage_id,
episode)` and `attempt_of(store, intent)`. The optional operands introduced in
the previous pass are withdrawn; no consumer call site used them. The writers'
signatures and the settlement evidence contract are unchanged from the last
handback.

#### State

Awaiting independent review at `baton.bug`. Sibling W120425 is unaffected;
W119733 retains the joined six-path acceptance.
