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
