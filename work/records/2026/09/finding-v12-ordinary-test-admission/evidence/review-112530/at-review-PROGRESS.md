# Progress

## 2026-09-07 — baton.claude — ordinary-test evidence at admission

Claimed under owner112006's split. The four owned paths are delivered; the
conditional fifth needed no change. State: **awaiting independent review**.

### Revalidation

All five paths `baseline-112022.json` binds are byte-identical in the current
tree, and every confirmed claim was re-checked against the source: the worker
does already run the frozen task's verification argv and publish its answer,
`admit_accepted` had no `required_tests` operand, and `_accepted_receipts`
published `observation="passed"` unconditionally.

### The defect, in one word

The Authority's verification receipt said `passed` for **every** accepted
checkpoint, whatever any test had done. An accepted technical review is a
judgement about a change; it is not a statement that the required commands ran
and exited zero. Publishing one as the other made the strongest receipt in the
protocol the least evidenced.

### The worker half executes nothing new

`ClaudeAgent` already runs the task's own verification argv and records the
answer. What was missing was a way for admission to resolve that same fact, so
the existing observation is exposed on the proposal output's metadata under
`baton.git-ordinary-tests/1` — six closed members, beside the existing
four-field proposal claim rather than widening it.

**There is no `passed` in it and no boolean.** A status is what this adapter
read from a child's exit; deciding whether that satisfies a requirement belongs
to the consumer that holds the requirement. A case asks that by TYPE rather
than by value, because `0 == False` in Python and zero is exactly the value
this observation most often carries.

**Unrun is explicitly null rather than absent or zero.** The command is skipped
when the provider failed or produced no patch, and a timeout or a failed start
answers `None` too. All three are "no status", and a consumer that must refuse
on anything but an actual zero needs to tell that apart from a status it can
compare. A missing member would say the same thing by omission, which a closed
reader cannot distinguish from a producer that forgot.

`task_digest` names the exact bytes this turn read, answered from the SAME read
that produced the document — a second open would be a second file. `_task`
keeps exactly the contract it had; `_read_task` is the new pair.

### The consumer half decides, and says what it decided on

`ordinary_test_evidence` is public and read-only. It resolves the accepted
checkpoint's producer, re-reads that attempt's frozen result and retained
manifest through their accepted owners, and cross-binds every identity: the
retained manifest names the result and the assignment, the published proposal
names the same result, candidate, input and policy digests, and the
observation's own base and head are the ones the proposal claim recorded. All
of it comes from retained manifests and durable rows, so it survives ordinary
cleanup — which is the property that makes it usable at admission at all.

`_ordinary_tests_passed` is the only route to a `passed` receipt. **A non-zero
status and an unrun command are both refusals and deliberately not the same
one**: the first is evidence the required tests failed, the second is the
absence of evidence, and reporting one as the other sends an operator to the
wrong place.

`required_tests` is a closed SELECTION and there is no `status` in it — a
caller that could supply the observation would be certifying its own candidate,
which is the exact defect the unconditional receipt was. A case asserts that
member is absent and that supplying one refuses.

**The evidence is proved before any receipt side effect**, so a refusal writes
no verification, review or approval receipt and admits nothing. The receipt and
operation identities carry the observation digest, the requirement digest, the
producer attempt and an `ordinary-tests/1` marker — deliberately not a word
like `certified` or `verified`, because what happened is that the author's own
container ran the required command. **This is author-container testing plus
independent review; it is not clean candidate-merge certification**, and a case
asserts the marker does not claim to be.

### Verification

    PYTHONPATH=src python3 -m unittest tests.integration.test_driver -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_dependencies -q
    PYTHONPATH=src python3 -m unittest discover -s tests -t .

`tests.integration.test_driver` is 52 passing — 38 before, plus fourteen.
`tests.manager.test_claude_agent` is 170 passing — 164 before, plus six.
`tests.manager.test_dependencies` passes unchanged: no new PUBLIC function
parameter reaches its inventory, because `required_tests` is a keyword of
`admit_accepted`, which that walk already covers through its existing operand
`required`. **The conditional tenth path therefore needed no edit**, and it is
byte-identical to the baseline.

**Canonical subtree gate: 4799 tests in 239.4s, 11 failures, 1 error, 21
skipped**, retained at `evidence/implementation-112071/subtree-gate.txt`.
Handed over red, with the failures the standing baseline: six
boundary-inventory, four live-daemon cleanup, one authority-catalog, and the
registry error naming the two untracked baseline modules. **The two
`TheWorkerCompletionTraversesPublicCustody` failures present in earlier runs
are gone**, which is W110772's lifecycle correction landing rather than
anything this Work did — I claim no credit for it and note it only so the count
is comparable.

The daemon-free statement is about this Work's own fixtures: no provider,
container, image or canonical target was involved in any case here. The broad
discover command does run live-engine suites, which is where four of those
failures come from.

### Candidate

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/integration/driver.py` | `d05c59ede048826b125396ab3b7256b701b4726b5ef9124329d4d192d8037ed7` |
| `v12/worker/claude_agent.py` | `65a9d8b7dda16f76665c0a620740653b43692ac315e246fd4e822fe222101817` |
| `v12/python/tests/integration/test_driver.py` | `d496f499c2d0ba9ea489996471af0acedced15ccab3a3cfc75c565638b074586` |
| `v12/python/tests/manager/test_claude_agent.py` | `e6e26f42348d67c82a80d7cf8ceada6ca701a312da8eb65a7d60fcea7c0ac5f1` |
| `v12/python/tests/manager/test_dependencies.py` | `89b00e126443f1e49227cffb57de956abaf3303dff84bbd4da0edc75abe74130` (unchanged) |

Exactly the assigned paths. No W110772 lifecycle source, test or document was
touched; no schema, Authority, intake, attempts or OCI change; no assembly file.

### Enumerated assertion changes

`tests/integration/test_driver.py`, all in this Work's own scope:

- the two light fixtures (`AcceptedReceiptCase`, `DriverCase`) supply the
  evidence resolution and a matching requirement, because neither holds a
  producer to read one from; each says so in place, and the resolution itself
  is driven for real against the retained result in the new class;
- the producer fixture's retained result now carries the observation beside the
  existing claim, and its proposal document is completed with the members
  `admission._proposal` requires;
- the terminal-replay case names its own requirement, because it drives the
  restart tail rather than the evidence gate.

No existing assertion was weakened or removed. Fourteen cases were added.

### Not claimed

No live provider, container, image or canonical target. W103083 still has to
derive `required_tests` from the task bytes it already holds and pass it —
until it does, an assembled admission will refuse for want of the operand,
which is the correct direction of failure. W110935 waits on the shared worker
bytes through this gate. W112039 joins this slice with W110772's before
W103083/W110935/W106673 open.


## 2026-09-07 — baton.claude — the three findings, corrected

Reclaimed after `review-2026-09-07T17-47-09Z.md`. All three reproduced and all
three were real. **Two are fully corrected and the third is partly delivered**;
the last section says exactly which part is missing and does not claim it. The
adoption entry the review asked for is now in `FINDING.md` and `PLAN.md` carries
the true current status.

### P1 — three receipts were written for a proposal nobody had checked

The reviewer's probe is exactly right, and the shape of the defect is worth
stating plainly: I compared the RESULT's assignment to the producer's and never
the PROPOSAL's, and I never compared the proposal's target with the base its
producer built on. So a published proposal naming another generation, another
participant, another Work, or offered against another revision reached
`_accepted_receipts` and had verification, review and approval written for it.

`resolved_account` does make several of those comparisons — three steps later,
after immutable receipts exist. **A later admission refusal cannot retract a
receipt**, which is what makes "the check exists elsewhere" the wrong answer
here. The comparisons are now in this Work's own reader, ahead of the side
effect: the proposal's whole `assignment_ref` against the resolved producer,
its target against the claimed base, and the accepted checkpoint's base against
the same.

Nine cases drive the ACTUAL `_accepted_receipts` with recorded external
sessions: the unchanged control writes exactly three receipts, and foreign
generation, participant, Work, target, checkpoint base, failing command, unrun
command and mismatched requirement each **assert zero calls to all three
sessions**.

### P2 — the marker was hashed and therefore invisible

The workflow word went into the hashed basis while the emitted identities
stayed the generic `verification-receipt` and `verification-operation` whatever
the evidence was — so the one thing an operator actually reads said nothing.
The verification receipt and operation identities now carry
`ordinary-tests-verification`, and a case inspects the operands the production
composition actually emitted rather than the constant.

Review and approval identities are unchanged: what this Work altered is which
evidence a VERIFICATION receipt rests on, and relabelling the other two would
claim something about acts it did not touch. A case asserts that too.

### P1 — the real command, and the part that is still missing

**Corrected:** the worker cases inherited a runner that returned a
`CompletedProcess` for every non-Git argv, so the status in the metadata was
one the fixture injected — the cases proved carriage and their names claimed
execution. `really()` now runs the task's own verification argv with
`subprocess.run` in the candidate. Two cases use it: one where the command
genuinely exits zero, and one where the provider's own edit makes a real
process exit 3. I confirmed the second drives the status rather than passing
vacuously. The injected-status case stays and now says in its docstring that it
checks carriage, not execution.

**NOT delivered:** the end-to-end proof that carries a real completion through
public freeze, intake, retention and cleanup into a real Authority admission,
with retained evidence reopened after cleanup and conflicting-receipt and
replay behaviour exercised at that boundary. That is a substantial fixture —
the nearest existing one is W110772's `TheWorkerCompletionTraversesPublicCustody`,
in a file this Work does not own — and I have not built it. The receipt-boundary
negatives above run against the real `_accepted_receipts` with a really retained
result manifest, which is stronger than what I submitted last round and is still
not the scheduled joined proof. **I am not claiming it and the plan now says so.**

### Verification

    PYTHONPATH=src python3 -m unittest tests.integration.test_driver -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent -q
    PYTHONPATH=src python3 -m unittest discover -s tests -t .

`tests.integration.test_driver` is 64 passing — 52 before, plus twelve.
`tests.manager.test_claude_agent` is 172 passing — 170 before, plus two.

**Canonical subtree gate: 4813 tests in 240.6s, 11 failures, 1 error, 21
skipped**, retained at
`evidence/implementation-112071/subtree-gate-corrected.txt`. Handed over red,
distribution unchanged: six boundary-inventory, four live-daemon cleanup, one
authority-catalog, and the registry error. No new failure.

### Candidate

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/integration/driver.py` | `4e4db51abf56a0774588c9bfc31e99f2bf44fc13c291e243c84eb9eb45174c65` |
| `v12/worker/claude_agent.py` | `65a9d8b7dda16f76665c0a620740653b43692ac315e246fd4e822fe222101817` (unchanged) |
| `v12/python/tests/integration/test_driver.py` | `054bbb355c3ad8726fc53c83d78490fac375160245dfae21c8cf3173ef4f3f39` |
| `v12/python/tests/manager/test_claude_agent.py` | `a6c6e57ad38dd9c24c6ad864080ed02f0106ce27a509631b52436c1f9bbf5dd7` |
| `v12/python/tests/manager/test_dependencies.py` | `89b00e126443f1e49227cffb57de956abaf3303dff84bbd4da0edc75abe74130` (unchanged) |

The worker source needed no further change: its correction was to the cases
that exercise it. No lifecycle file, assembly file, schema, Authority, intake,
attempts or OCI path was touched, and no existing assertion was weakened —
one docstring was made accurate about what its case measures.


## 2026-09-07 — baton.claude — the KeyError, and how my own fixture hid it

Reclaimed after `review-2026-09-07T18-00-22Z.md`. The reader defect is
corrected and proved against the real owner. The end-to-end component proof is
still not delivered and I say so plainly at the end.

### The defect, and the reason it survived my tests

`integration_checkpoint` answers `line_id`, `checkpoint_id`, `verdict_id`,
`checkpoint_digest` and `evidence` — with the objects **inside** `evidence`.
My reader read a top-level `head` and an optional top-level `base`, so it
raised `KeyError` the moment it met the real owner.

**My own fixture is why that shipped.** I hand-built the mocked eligibility
document with a top-level `head`, so the case proved the reader agreed with a
shape nothing in this build produces. That is the failure mode this campaign
keeps naming — a test that agrees with itself — and I wrote it.

The consumer now reads `evidence`, requires `base` and `head` in it, and
compares both. **The public eligibility schema is untouched.**

### Proved against the owner rather than against another mock

A mock is what let the defect through, so a mock cannot be what proves it
fixed. `TheReaderConsumesTheOwnersActualAnswer` builds a real line, writer,
checkpoint, reviewer and accepted verdict through the accepted
`tests/manager/test_review_cycles` fixture — **imported and driven, never
edited** — and asserts two things about the document
`integration_checkpoint` actually answers: its exact member set, and that
`base` and `head` are inside `evidence` and NOT at the top level, which is the
defect restated as an assertion. A second case runs the exact call that raised
`KeyError` over that real document and gets an ordinary refusal instead.

**The fixture is composed, not subclassed.** My first attempt inherited the
accepted `TestCase` and the suite jumped from 64 to 102, because every one of
its own cases re-ran under a second name — the same inflation I introduced once
before in this campaign. Moving to composition left 84, because a `TestCase`
subclass bound at module level is collected by the loader too; the import is
therefore inside the method. 66 is the honest number: 64 plus these two.

### Still not delivered

The end-to-end component proof — a real completion carried through public
freeze, intake, retention and cleanup into a real Authority admission, with
retained evidence reopened after cleanup and conflicting-receipt and replay
behaviour exercised there — **is still not built.** The review is right that
fixture size is not a scheduling excuse and that existing helpers may be
imported without editing them; this turn spent its room on the reader defect
and its owner-level proof instead, and I am not going to describe that as the
scheduled evidence.

What exists today: the receipt-boundary negatives run against the real
`_accepted_receipts` with a really retained result manifest and recorded
sessions, the worker's command really executes, and the eligibility reader is
now proved against its real owner. What is missing is the single joined path
through custody into admission.

### Verification

`tests.integration.test_driver` is 66 passing — 64 before, plus two.
`tests.manager.test_claude_agent` is 172, unchanged.

**Canonical subtree gate: 4815 tests in 262.1s, 11 failures, 1 error, 21
skipped**, retained at
`evidence/implementation-112071/subtree-gate-keyerror.txt`. Handed over red,
distribution unchanged: six boundary-inventory, four live-daemon cleanup, one
authority-catalog, one registry error. No new failure.

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/integration/driver.py` | `d6b3be4f99e0776d6ec402db6bfb05b4db8fd376a36b8d1c4225eb17dec83bd6` |
| `v12/worker/claude_agent.py` | `65a9d8b7dda16f76665c0a620740653b43692ac315e246fd4e822fe222101817` (unchanged) |
| `v12/python/tests/integration/test_driver.py` | `28cf1e1cf3d234728b33a6d1174ec222e621e3d09eca9cf0a57e6c5e5f62f6d7` |
| `v12/python/tests/manager/test_claude_agent.py` | `a6c6e57ad38dd9c24c6ad864080ed02f0106ce27a509631b52436c1f9bbf5dd7` (unchanged) |
| `v12/python/tests/manager/test_dependencies.py` | `89b00e126443f1e49227cffb57de956abaf3303dff84bbd4da0edc75abe74130` (unchanged) |

No lifecycle file, assembly file, public schema, Authority, intake, attempts or
OCI path was touched. `tests/manager/test_review_cycles.py` is read and
imported and is byte-identical.

## 2026-09-07 — baton.tuner claim112441, proof-only delivery

Owner112439 adopted before editing. The only edited product/test path is
tests/integration/test_driver.py. All production, worker-test, dependency and
reused lifecycle files remain byte-identical to this claim's incoming hashes.
This supersedes the preceding implementation episodes' undelivered component
proof status: the admission component proof below is now delivered for review.
It does not claim independent provider or joined acceptance.

The new _OrdinaryAdmissionWorld composes locally imported existing fixtures;
no imported TestCase is collected or subclassed. The existing worker runner
executes the task's actual python3 harness.py subprocess and records its real
return code. The proof hashes the exact consumed task bytes independently and
compares every observation field with them and the candidate's actual objects.
The same generated proposal directory/metadata is measured by baton_worker,
written into its completion envelope, and carried through public runtime
reconciliation, freeze, intake, retention, proposal retention/publication,
checkpoint, review completion/verdict and cleanup owners. The review runs the
existing actual review worker over the candidate's real Git objects.

After cleanup the proof reopens actual retained result/artifact files, recomputes
artifact tree digests, reads result.json and its real command observation, and
compares completion/result/assignment/intake/retention identities. It asserts
both runtime cleanups, removed execution roots and one worker/review/destroy.
The actual ordinary_test_evidence reader resolves this retained producer.

Publication and verification/review/approval use real minted Authority sessions
and their actual journals. Public admit_accepted runs its real evidence checks,
receipt operations, resolved_account and admit_candidate. A named exception
stops at execution.integrate_next only AFTER the real coordinator entry is
durably queued; the test reads that entry back and asserts its admitted account.
No admission/evidence/custody reader is patched. The execution cut is explicit:
this proves admission, not an integration runtime or canonical target mutation.

Other explicit fixture seams remain the existing model process and engine,
manager-assignment transport, and checkpoint profile fixture holding object
names observed from the real worker repository. This is a deterministic
component proof, not a live deployment or full source-profile acceptance.

Seven additive tests cover positive admission; retained evidence/exact replay;
actual failed and unrun completions; each of the four mismatched trusted
requirements; real conflicting Authority receipt; real foreign producer; and
a real later assignment generation. Actual failed/unrun turns remain unable,
are publicly frozen/retained and explicitly finalized/cleaned, and cannot gain
an accepted checkpoint or any policy receipt/admission. They are never relabeled
completed. The existing observation-level nonzero/null negatives are preserved.
Mismatch cases assert zero verify/review/approve calls, no receipts, no queue
entry and no execution. The conflict case retains the original real passed
receipt unchanged across two refused attempts; review/approval/admission never
follow. Exact successful retry uses the same Authority operation identities,
returns the same complete receipts and queue rank/account, adds no manager or
coordinator writes, and invokes no worker or custody action.

The explicitly authorized ineffective regression now uses the actual retained
producer and asserts the positive observation with head/base from the owner's
evidence. The old early-refusal expectation is removed only in that named test.
Its composed fixture setUp now registers the imported owner's tearDown, which
closes its store and temporary root; no other existing assertions change.
The retained broken reader was compiled in an isolated namespace and injected
only for the sensitivity check: the corrected test now fails at KeyError head.
All other existing test/helper source bodies remain unchanged.

Verification:

- Full tests.integration.test_driver: **73 tests pass, 1.679s** (66 incoming
  plus seven additive cases; one named regression corrected).
- Sensitivity proof: the retained broken reader fails the corrected regression
  with exactly KeyError head. Current reader passes it in the full suite.
- Retained component probe: actual command status0, three real Authority receipt
  kinds, durable queued admission and exact retry; full operands and owner
  documents are in component_probe.json.
- git diff --check passes. No production/worker-test/inventory bytes changed.
- Per owner112439, no broad rerun. The historical 4815-test log remains
  11 failures/1 error/21 skips, retained and hash-bound in
  historical-broad-evidence.json. It is not re-certified for current shared-tree
  bytes, and no red gate is waived.

New-fixture corrections during development: mounted the reviewed repository
under the existing worker helper's actual input/source path; finalized unable
assignments through finalize_quiescent_assignment before cleanup; used the
coordinator's actual empty-list answer; and gave a foreign Authority producer
its own result identity because Authority correctly refuses reusing another
assignment's result. These were new fixture errors, not production defects.

Evidence, baseline/candidate bytes, exact delta, source-preservation audit and
all unchanged hashes: evidence/tuner-112441/. Test candidate SHA-256:
3aeb9fad7e75d958070c7086cbfeeccf9098ff4f9714f1bff1be69a6a5988907.
Handoff manifest SHA-256:
85fef2a72bb68080fd988c7c343c4d2295b1d2cc1a91eeef0def427086117a4a.

Return to baton.bug for independent review. W110772 has its separate candidate
and review; W112039 and all downstream gates remain intact.
