# Progress

Implementation entries belong to the assigned change author. The filing evidence
lives in FINDING.md and in the consumer's `evidence/implementation-119398/`.

## 2026-09-08 — W119548 claim119731 — baton.claude — in progress

**Revalidation before any edit.** The approved ruling is M119628 over
`review-2026-09-08T13-45-00Z.md` and the appended FINDING proposal. Re-checked
against the current tree rather than acted on from the record:

- `Authority.satisfy_gate` still discharges `runtime-quiescence` only on
  `{"kind": "runtime-absent", "runtime": <text>}`, still checks `work["gate"]`
  for exact equality, still journals the evidence, and still replays under its
  own `operation_id`. Its `_TRANSITIONS` entry carries no `actor`, so no new
  Authority grant is involved — as the review says.
- `worker_manager.SESSION_OPERATIONS` still omits `satisfy_gate`, and no
  production caller of it exists outside `src/baton_v12/authority/`.
- `intake.authorize_cleanup` still journals `runtime.destroy` with the identity
  `destroy_operation(attempt, receipt_digest, retention_policy_digest)` derives,
  and settles a `cleanup.settled` result carrying `state`, `cleanup` and the
  operation. `_committed` already exists as the reader that compares against the
  committed RESULT rather than a self-consistent row — which is exactly the
  "committed cleanup proof, not the mutable axis" the owner required.

### A material incompatible caller, found before editing and reported

The review authorized adding "the one `satisfy_gate` capability to
`authority_port.py`" and said to report a concrete incompatible caller before
expanding scope. There is one, and it is bigger than the FINDING anticipated.

`AuthorityPort.__init__` requires every member of `SESSION_OPERATIONS` to be
callable and refuses the whole construction otherwise. Measured against the
current tree, four session-shaped objects carry no `satisfy_gate`:

| Object | In this Work's six paths? |
| --- | --- |
| `tools/single_worker.py:_AuthoritySession` | **no** — FINDING names it as the consumer's |
| `tools/dogfood_operator.py`'s session facade | **no** — and the FINDING does not name it at all |
| `tests/manager/test_offers.py:FakeSession` | yes |
| `tests/job_manager/fixtures.py:FakeSession` | **no** |

So adding `satisfy_gate` to `SESSION_OPERATIONS` as a REQUIRED member would stop
**both production deployments** from composing an `AuthorityPort` at all, and
would require edits in at least two paths this Work does not own. That is not a
cost worth paying to type one new act, and it is not authorized.

**Decision, and it stays inside the approved three production paths.**
`satisfy_gate` is added as a deliberately OPTIONAL port capability: named in its
own tuple, typed at construction when the session carries it, and answered by a
port method that refuses `refused/capability` when it does not. The port gains
the capability exactly as approved; no existing session, deployment or assertion
changes; and the new act reports a session that cannot reach the Authority as
the missing capability it is, rather than faulting.

**Why a late refusal is safe here, which is not true of the required members.**
The port's own rule is that a capability discovered missing once durable state
depends on it was not typed at all — that is right for `claim`, which is reached
with an offer already accepted. The discharge is the opposite shape: ordinary
cleanup has already committed its terminal axis and its receipt, the discharge
is a separate act with its own derived identity, and its refusal leaves the
obligation exactly as discoverable and retryable as it was a moment earlier.
Nothing durable depends on the discharge having succeeded.

**Honest downstream boundary, as the FINDING requires provider acceptance to
identify.** Neither production deployment can actually discharge a gate until
its session wrapper forwards the member: `single_worker._AuthoritySession` is
the consumer's own path and already scheduled; `tools/dogfood_operator.py` is
NOT named anywhere in this Work's approved scope and is reported here as a
second, previously unrecorded consumer boundary. This provider delivers the
reusable act and says plainly that it does not by itself repair either
deployment.

### Verification question and budget, recorded before any run

**Question:** does the new act discharge the gate exactly once from the
committed cleanup proof, replay a remote commit whose local receipt was lost
without re-checking mutable Work state, refuse every stale, foreign, malformed
and non-terminal input, and leave `authorize_cleanup`'s own API and authority
effect untouched? No retained evidence answers any of it — the act does not
exist yet.

**Scope and budget:** the new focused class first; then
`tests.manager.test_intake` and `tests.manager.test_offers` once each for the
owning modules; then `tests.manager.test_secrets` for the surface catalog; then
the modules that construct an `AuthorityPort` with a fake session
(`test_attempts`, `test_principal_context`, `test_text_sweep`,
`tests.job_manager.fixtures` consumers) because widening a port is exactly where
a construction-time refusal would surface. Proposed budget 60 seconds total. No
daemon, no ordinary suite, no live Authority, no full inventory sweep.

### Delivered: the gate-discharge act, inside the six approved paths

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `src/baton_v12/worker_manager/authority_port.py` | `a82a7080328780d848285de30c70686411484863d97c7f1c110fae756ec94575` |
| `src/baton_v12/worker_manager/intake.py` | `43755ee7dd2ef1a263649b57a1c6657d8eba06af53775ad783b24c6f7fee8865` |
| `src/baton_v12/worker_manager/__init__.py` | `19dc529bebb57f3aa05638008ac9c8f4623f69ca70096efef60d5cc394f4f498` |
| `tests/manager/test_intake.py` | `302c4cea7098fdce41cd2f78be7d91f4923fa4e9dcdb29784c0cd620f2d31728` |
| `tests/manager/test_offers.py` | `153029ef56850a19055eab29e9e7778ce86401a4e7f7faf92be87a79c527bec6` |
| `tests/manager/test_secrets.py` | `37d5a1609f2417545ee907a0cee0d403b1a67e22aaaac6e1d3d41f23be64c498` |

Nothing outside those six changed, and every test change is additive: no
existing assertion, method body, export or behaviour was removed or weakened.

**`intake.discharge_quiescence_gate(store, port, *, attempt_id,
retention_policy_digest)`.** Its two operands are the attempt and the policy
that is half the key to the cleanup proof; the authority, Work, participant,
generation, gate token, runtime identity and absence evidence are all derived
from durable records. The order is: own the operands and prove the session acts
for the attempt's own assignment participant → **replay** an already committed
discharge and return it before anything mutable is read → prove the committed
`runtime.destroy` and the exact runtime it observed absent → ask the authority →
journal the answer under this act's own derived identity.

The proof is the COMMITTED cleanup, read through the existing `_committed`, not
the mutable `execution_runtime` axis. `failed` is refused: it is the settled
ending of a cleanup whose runtime survived its own destroy, which is evidence
against absence. `complete` and `retained` are the two that followed it.

**`intake.gate_discharge_of(store, attempt_id)`** is the discoverability half.
`authorize_cleanup` commits its terminal axis and receipt together, so a
consumer deciding what is owed from that axis alone sees nothing outstanding;
this answers the other question directly and is what lets ordinary serving and
restart finish the act. It decides nothing about whether one is owed — that
depends on whether the Work is gated, which is the authority's fact.

**`AuthorityPort.satisfy_gate`**, plus `OPTIONAL_SESSION_OPERATIONS` and
`GATE_DISCHARGE`. The capability is named without being required, for the
incompatible-caller reason recorded above; a session that cannot reach it is
told which capability is missing rather than faulting.

Cleanup is untouched: `authorize_cleanup` keeps its exact signature, its ending
and its authority effect, and a case asserts all three.

### Two things I decided rather than assumed, both reported

**A §13 gap I closed in my own first draft.** `_discharge_operation_id`
originally composed the identity with `digest` and no `check_no_durable_secret`,
unlike `destroy_operation`, which walks at the constructor "for the reason every
other operation identity's does". An operation identity is portable, so a guard
at the eventual write runs after the caller holds the leak. The walk is now
there and `test_secrets` drives it: a live bearer in `attempt_id` refuses
`secret-leak` and the bearer does not reach the refusal message.

**The receipt is composed in `intake.py` rather than through `documents.py`.**
Every other receipt in that module is built by a registered `documents`
contract. Registering a new one means editing `worker_manager/documents.py`,
which is not among the six approved paths and which the FINDING says needs its
own scope decision. Nothing is lost by waiting: `store.transact` journals the
value as JSON and `replay` answers `json.loads`, so a replay returns a plain
document either way — the registry would add validation, not a different type.
Moving it there is a bounded follow-up for the reviewer to dispose.

### The blocking scope gap, and it is one line per name

`tests/manager/test_text_sweep.py` holds a SECOND surface catalog derived from
`worker_manager.__all__`, and
`EveryExportedOperationRefusesUnstorableText.test_the_table_names_every_exported_callable`
now fails naming exactly `discharge_quiescence_gate` and `gate_discharge_of`.
That path is not among the six the owner approved, and the FINDING says an
additional needed path is a scope finding before editing — so I have not touched
it, and this candidate leaves that one case red.

It is not a defect in the act. I verified against the real sweep logic, without
editing the file, that both new surfaces genuinely refuse unstorable text in
every operand the table would drive. The two entries the table needs are:

```python
    "discharge_quiescence_gate": (
        (store, port), dict(attempt_id="attempt-1",
                            retention_policy_digest="sha256:" + "7" * 64),
        ["attempt_id", "retention_policy_digest"]),
    "gate_discharge_of": ((store, "attempt-1"), {}, [1]),
```

Driving them through `test_text_sweep`'s own spoiling loop gives
`ContractRefusal` for all three operand positions. A seventh path is requested
for those two lines and nothing else.

### Verification

Question, scope and budget were recorded above before any run.

- Focused, the new class:
  `tests.manager.test_intake.TheQuiescenceGateIsDischargedFromTheCommittedCleanup`
  — **21 tests, OK, 0.316s**.
- The owning and port-constructing manager modules: `test_intake test_offers
  test_secrets test_attempts test_principal_context test_runtime_lane` —
  **777 tests, OK, 6.897s**.
- Every other suite that constructs an `AuthorityPort`:
  `tests.job_manager.test_recovery test_restart test_scheduling test_launch
  tests.tools.test_integration_worker` — **157 tests, OK, 7.617s**. This went
  past the review's proposed module set on purpose: widening a port surface is
  exactly where a construction-time refusal would appear, and the point of
  making the member optional is that none of these changed.
- `tests.manager.test_text_sweep` — **3 tests, 1 failure**, and it is the scope
  gap above rather than a behaviour of the act. Recorded, not waived.

No daemon, no ordinary suite, no live Authority, no full inventory sweep, and no
repeat of the consumer's retained reproduction.

### What this does not do

It does not repair the composed lifecycle. Neither production deployment can
discharge a gate until its session wrapper forwards the member:
`tools/single_worker.py`'s `_AuthoritySession` is the consumer's own path and is
already scheduled, and `tools/dogfood_operator.py` is a second consumer boundary
this Work's approved scope does not name at all. W119114 still owns the joined
serving and restart proof, the durable-retry plan and the conversion of its
three defect-demonstration assertions.

**State: awaiting independent review, with one scope decision requested.**

## 2026-09-08 — W119548 claim119921 — baton.claude — correcting review 14:27:00Z

**Revalidation before any edit.** All six paths still hash to the candidate
`evidence/review-119842-audit.json` reviewed, and the reviewer's own
`evidence/review-119842-probe.py` was re-run against those exact bytes. All
three findings reproduce, and all three are mine:

- **changed-runtime** — the act succeeds and sends
  `{"kind": "runtime-absent", "runtime": "runtime-never-observed-absent"}` after
  nothing but the attempt row's `runtime_id` was edited. The destroy journal is
  untouched, so the committed proof was never really consulted about the runtime;
- **wrong-answer** — a session answering `{gate: runtime-quiescence:99, kind: [],
  phase: block}` without acting produces a journalled, discoverable success
  receipt while `runtime-quiescence:1` stays closed and no evidence is sent;
- **foreign-authority** — a projection whose `authority_uuid` is replaced still
  discharges, because only the participant was ever compared.

**What I got wrong, stated plainly rather than paraphrased.** I claimed the proof
was "the committed cleanup, not the mutable axis" and only half meant it.
`destroy_operation` splits the binding: `operation_id` covers attempt,
assignment, receipt and policy; `signature_digest` is what covers `runtime_id`.
I compared the identity and dropped the signature — so the runtime the evidence
names was read fresh from a mutable column with nothing holding it to the
committed act. And I owned the port answer's member SET without owning its
values or their relationship to what was asked, then journalled my own requested
gate over whatever came back. Neither is a subtle interaction; both are the
receiving-boundary rule this manager applies everywhere else, not applied here.

### The three corrections, all inside the six approved paths

1. `_absence_proof` owns the committed cleanup's nested operation as a document
   and compares its COMPLETE binding — identity and signature digest — against
   the operation freshly derived from the current attempt row. A changed,
   missing or malformed runtime moves the derived signature and refuses before
   the Authority is asked. `destroy_operation` and `_committed` are unchanged.
2. `AuthorityPort.satisfy_gate` requires the reply's gate to equal the gate it
   asked about, its kind to be durable text and its phase to be the Authority's
   own discharged phase; `discharge_quiescence_gate` additionally requires the
   quiescence kind and journals the ANSWERED values rather than its request. Both
   public exits — the replay short-circuit and `gate_discharge_of` — adopt the
   receipt against an explicit member and value contract instead of returning
   whatever JSON the journal held.
3. The full Work reference is proved before any new remote act, through the
   port's own `project_work` projection, so a session bound to another Authority
   refuses even when the participant matches. It sits AFTER the committed local
   replay, so a remote commit whose receipt was lost still replays without any
   mutable remote read.

### Verification question and budget, recorded before any run

**Question:** do all three reproduced counterexamples now refuse before the
Authority act, leaving no discharge receipt and the gate closed, while the valid
path, the replay-after-lost-receipt path and every previously passing control
still behave exactly as accepted? The 21 retained passes answer only the last
part, and the review says so.

**Scope and budget:** the reviewer's probe first as the smallest measurement
that the three are gone; then the focused class; then
`tests.manager.test_intake test_offers test_secrets` for the owning modules;
then the port-constructing suites once. Budget 60 seconds. No daemon, no live
Authority, no ordinary suite, no deployment.

### Delivered: all three findings corrected, inside the same six paths

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `src/baton_v12/worker_manager/authority_port.py` | `174d621edfb1d8b694c9b1cbfe511d8b56c8a89e97ed89bc08534e1a029f64c6` |
| `src/baton_v12/worker_manager/intake.py` | `0ccc85d7e92fdce8e701ebe2d728153632252b33dae4edf5ff7b13381a70f26e` |
| `src/baton_v12/worker_manager/__init__.py` | `19dc529bebb57f3aa05638008ac9c8f4623f69ca70096efef60d5cc394f4f498` (unchanged) |
| `tests/manager/test_intake.py` | `99e1e929c069b60cfc70a952a502e3f679c97da293849111851e927527f4f6e7` |
| `tests/manager/test_offers.py` | `153029ef56850a19055eab29e9e7778ce86401a4e7f7faf92be87a79c527bec6` (unchanged) |
| `tests/manager/test_secrets.py` | `37d5a1609f2417545ee907a0cee0d403b1a67e22aaaac6e1d3d41f23be64c498` (unchanged) |

No seventh path was needed or taken. Every pre-existing assertion is untouched;
`authorize_cleanup`, `destroy_operation` and `_committed` are unchanged.

**P1, committed proof.** `_absence_proof` owns the committed cleanup's nested
operation as a document and compares its COMPLETE binding — identity and
signature digest — against the operation freshly derived from the current
attempt row. The signature is the half that carries `runtime_id`, so a changed,
absent or malformed runtime now moves the derived signature away from the
committed one and refuses before the Authority is asked.

**P1, the answer.** `AuthorityPort.satisfy_gate` requires the reply's gate to
equal the gate it asked about, its kind to be durable text, and its phase to be
`GATE_DISCHARGED_PHASE`. `discharge_quiescence_gate` additionally requires the
quiescence kind and journals the ANSWERED values rather than its own request.
Both public exits — the replay short-circuit and `gate_discharge_of` — now adopt
the receipt through `_adopted_discharge` against an explicit member AND value
contract, so a journalled row that does not say a quiescence gate was released
is refused rather than reported to consumer recovery as a completion. The
contract is composed in `intake.py`: `documents.py` stays out of scope, and the
review is explicit that being out of scope does not waive it.

**P2, the Authority binding.** `_same_authority` proves the full Work reference
through the port's own `project_work` projection before any NEW remote act, so a
session acting for the same participant on another Authority refuses. It uses an
already-required port member; no new session capability was taken. It sits AFTER
the committed local replay, so a remote commit whose receipt was lost still
replays without any mutable remote read.

### One place the review's wording and the code had to be reconciled

The review asks for a "lost-local-receipt followed by later Work movement"
control and, separately, that the Authority binding be proved before a new
remote act. Those pull in opposite directions for one case, so I split it rather
than picking whichever made a test pass:

- **later Work movement, same Authority** — replays. Today's gate and phase are
  never consulted, so a Work claimed and fenced again at generation 9 does not
  strand the earlier act; one act at the Authority, one piece of evidence, and
  the later gate untouched.
- **lost receipt, foreign Authority** — refuses. Finishing a lost receipt means
  making the remote call again, and a session speaking for another Authority may
  not make it. The obligation stays outstanding and discoverable for a correctly
  bound session instead of being completed by the wrong one.

What may not gate a replay is today's Work STATE. The Authority binding is not
that, and I have written both cases so the distinction is measured rather than
assumed. If the reviewer reads the rule the other way, this is the exact place
to say so.

### One fixture of my own I corrected, and it is not an assertion change

`test_a_session_that_cannot_reach_the_discharge_says_so` built a fresh
`FakeSession()` whose default projection names another Authority, so after P2
the new binding refused before the capability could. Its narrow session now
copies this case's own projection, leaving the case measuring the missing
capability it is named for. Only the fixture line changed; the assertion is
untouched.

### Verification

Question, scope and budget were recorded above before any run.

- **The reviewer's own probe, first.** `evidence/review-119842-probe.py` re-run
  unmodified against the corrected bytes: all three scenarios now raise
  `ContractRefusal`, the gate stays `runtime-quiescence:1` in every one, no
  absence evidence is sent, and no discharge receipt becomes discoverable.
  Retained as `evidence/correction-119921-probe.json`.
- **Each correction has controls that fail without it**, measured by reverting
  one piece at a time with the tests unchanged:
  - reverting only the signature comparison → `changed-runtime` and two
    malformed-nested-proof subtests fail;
  - reverting only the port's value checks → the wrong-gate control fails. The
    wrong-kind and wrong-phase controls still pass, because `_adopted_discharge`
    catches those at the journal step. That is defence in depth rather than two
    regressions, and I am naming it that way rather than counting them twice;
  - reverting only `_same_authority` → both foreign-Authority controls and the
    no-such-Work control fail.
- Focused class: **34 tests, OK, 0.643s** (21 before, 13 added).
- Owning and port-constructing manager modules: `test_intake test_offers
  test_secrets test_attempts test_principal_context test_runtime_lane` —
  **790 tests, OK, 7.234s**.
- Every other suite constructing an `AuthorityPort`: `job_manager
  test_recovery test_restart test_scheduling test_launch`, `tools
  test_integration_worker` — **157 tests, OK, 7.524s**.
- `tests.manager.test_text_sweep` — **3 tests, 1 failure**, unchanged and
  unwaived: it is M119837's pending seventh-path scope decision, not a
  behaviour of the act.

### Still outstanding, and unchanged by this correction

M119837's two catalog entries in `tests/manager/test_text_sweep.py` remain
pending owner disposition. Neither production deployment can discharge a gate
until its session wrapper forwards the member — `single_worker._AuthoritySession`
is the consumer's scheduled path and `tools/dogfood_operator.py` is the second
boundary this scope does not name. W119114 and W119733 still own the joined
serving and restart proof.

**State: awaiting independent review.**

## 2026-09-08 — W119548 claim120006 — baton.claude — finishing the receipt contract

**Revalidation before any edit.** The three candidate hashes still match
`review-2026-09-08T14-43-50Z.md`, and the reviewer's `review-119974-probe.py`
was re-run against them. All six rows reproduce exactly: `assignment=null`
faults as a raw `TypeError`, and a receipt naming another attempt, gate,
operation or runtime is returned as this attempt's completion by BOTH public
exits.

**What I got wrong, again in one sentence.** I built a contract that checks each
field and never checks that the fields belong together, or that they belong to
the record they were read out of — so `_adopted_discharge` proved a receipt was
well-formed and proved nothing about whose receipt it is. The previous review
asked for a value AND relationship contract; I delivered the value half and
called it done.

**The correction.** The journal already holds the binding I failed to use: the
discharge's committed signature is `manager_signature` over the attempt, the
fixed assignment, the gate, the runtime and the cleanup operation. So the
receipt's own signed operands are RECOMPUTED and compared against that recorded
signature, which binds all five at once. On top of that the receipt is bound to
the selection — its `operation_id` must be the one that was looked up, and its
attempt and assignment must be the selected attempt's immutable fixed
assignment — and its gate must derive from that assignment rather than stand on
its own. The nested assignment is owned as an exact document before any keyword
unpacking, so a null or malformed one is a typed refusal rather than a fault.

Nothing mutable is consulted: not today's runtime row, not the cleanup row, not
the remote gate or phase. A correct receipt therefore still replays after later
Work movement, which stays covered.

### Verification question and budget, recorded before any run

**Question:** do all six of the reviewer's spoiled receipts refuse
`integrity/schema` on BOTH public exits, with no new remote act, while a valid
receipt still replays — including after later Work movement — and every
previously accepted control still passes? The 34 retained passes do not cover
these counterexamples, and the review says so.

**Scope and budget:** the reviewer's probe first; then the focused class; then
`test_intake test_offers test_secrets`; then the port-constructing suites once.
Budget 60 seconds. No daemon, no live Authority, no ordinary suite, no seventh
path — M119837 is still pending and `test_text_sweep` stays unwaived.

### Delivered: the receipt is now bound to the record it came out of

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `src/baton_v12/worker_manager/authority_port.py` | `174d621edfb1d8b694c9b1cbfe511d8b56c8a89e97ed89bc08534e1a029f64c6` (unchanged) |
| `src/baton_v12/worker_manager/intake.py` | `d9a4fdd17f0e817f0275540a1c8f42cc8f8210f3e30c4bb1ca97d1a8c80f67d9` |
| `src/baton_v12/worker_manager/__init__.py` | `19dc529bebb57f3aa05638008ac9c8f4623f69ca70096efef60d5cc394f4f498` (unchanged) |
| `tests/manager/test_intake.py` | `a5ebee13844b0eeba181853102286db0781157dc557ff058ad65784b8e541855` |
| `tests/manager/test_offers.py` | `153029ef56850a19055eab29e9e7778ce86401a4e7f7faf92be87a79c527bec6` (unchanged) |
| `tests/manager/test_secrets.py` | `37d5a1609f2417545ee907a0cee0d403b1a67e22aaaac6e1d3d41f23be64c498` (unchanged) |

Two paths changed. No seventh path taken; `authorize_cleanup`,
`destroy_operation`, `_committed` and every pre-existing assertion untouched.

**The nested assignment is owned before it is unpacked.** `documents.assignment`
takes keywords and `**None` is a `TypeError`; a raw fault at a persisted-input
boundary bypasses the portable refusal and retry path every other reader here
uses. The assignment and its Work reference are now exact documents first.

**The gate is derived from the receipt's own assignment** rather than believed.
A generation-1 assignment carrying `runtime-quiescence:99` is not a document
about one discharge, however well formed each half is alone.

**The receipt is bound to the selection** — the operation identity that was
looked up, and the selected attempt's own immutable fixed assignment.

**And the five signed operands are bound TOGETHER.** The journal already held
the binding I had failed to use: `discharge_quiescence_gate` signs the attempt,
the fixed assignment, the gate, the runtime and the cleanup operation into one
`manager_signature`, and the store recorded it. `_receipt_signature` recomposes
that from the receipt's own operands and compares it with the recorded
signature — one comparison for a relationship five independent field checks
cannot state. All three exits go through the same contract, including the one
that COMPOSES the receipt before journalling it: what is written is held to
exactly what is read.

Nothing mutable is consulted — not today's runtime row, not the cleanup row,
not the remote gate or phase — so a correct receipt still replays after later
Work movement, which now has its own control.

### Verification

Question, scope and budget were recorded above before any run.

- **The reviewer's probe first.** `evidence/review-119974-probe.py` re-run
  unmodified: all six rows now answer `ContractRefusal` on BOTH exits, including
  the two that previously faulted or returned an unrelated receipt. Retained as
  `evidence/correction-120006-probe.json`.
- **Every new control fails without the binding.** Reverting only the
  relationship half — keeping every individual field check — fails 13 subtests:
  all five unrelated-receipt rows on both exits, the derived-gate case, the
  signed-operand case and the absence-versus-malformed case.
- Focused class: **40 tests, OK, 0.862s** (34 before, 6 added).
- Owning and port-constructing manager modules: **796 tests, OK, 7.448s**.
- Port-constructing suites elsewhere (`job_manager` recovery/restart/scheduling/
  launch, `tools` integration_worker): **157 tests, OK, 7.628s**.
- `tests.manager.test_text_sweep` — unchanged, still 1 failure, still unwaived:
  M119837's seventh-path decision is pending and this review did not authorize
  it.

### Unchanged and still outstanding

M119837's two catalog entries remain pending owner disposition. Neither
production deployment can discharge a gate until its session wrapper forwards
the member — `single_worker._AuthoritySession` is the consumer's scheduled path,
`tools/dogfood_operator.py` the second boundary this scope does not name.
W119114 and W119733 still own the joined serving and restart proof.

**State: awaiting independent review.**

## 2026-09-08 — W119548 claim120100 — baton.claude — presence gap and approved catalog

**Revalidation before any edit.** The candidate still hashed to
`review-2026-09-08T14-53-10Z.md`'s six, and M120088's scope extension was pinned
in FINDING before the seventh path was touched, as the approval directs.

**The presence gap, and it was two spellings of one question.** Discovery and
replay had each written their own presence check and they disagreed: the replay
exit refused a present record of the wrong kind and a present record whose
decoded result is null, while `gate_discharge_of` returned `None` for both. A
consumer acts on `None` as outstanding work it may still perform, so reporting
an integrity failure that way invites a remote act on the strength of a record
this manager could not read.

`_recorded_discharge` now decides it once for both exits. Only a genuinely
absent operation answers `None`; every present record is held to the same
contract. That is a smaller change than two matching checks, and it is the
reason the two cannot drift again.

**The approved catalog entries.** `tests/manager/test_text_sweep.py` gains
exactly the two `callable_table` entries M119837 specified and M120088 approved
— `discharge_quiescence_gate` with both of its caller texts swept, and
`gate_discharge_of` with its attempt id — plus the comment that says why. Twelve
inserted lines, zero deletions, no other content touched. The exported-surface
completeness failure that had been red and unwaived since M119832 is now green.

### Candidate

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `src/baton_v12/worker_manager/authority_port.py` | `174d621edfb1d8b694c9b1cbfe511d8b56c8a89e97ed89bc08534e1a029f64c6` (unchanged) |
| `src/baton_v12/worker_manager/intake.py` | `6c00c441bc7b2356fddfd9f0867db59e05d6b96128dbf8918fc3b67ea46c89c7` |
| `src/baton_v12/worker_manager/__init__.py` | `19dc529bebb57f3aa05638008ac9c8f4623f69ca70096efef60d5cc394f4f498` (unchanged) |
| `tests/manager/test_intake.py` | `facd32dd1d65c02e85253e0db91e12856258c7f6aa0c16c6a2d323236403e675` |
| `tests/manager/test_offers.py` | `153029ef56850a19055eab29e9e7778ce86401a4e7f7faf92be87a79c527bec6` (unchanged) |
| `tests/manager/test_secrets.py` | `37d5a1609f2417545ee907a0cee0d403b1a67e22aaaac6e1d3d41f23be64c498` (unchanged) |
| `tests/manager/test_text_sweep.py` | `f3eff0216f98f4cd4174d4d016283612f88306ee75380cbb7ea26f802e5dbd50` |

### Verification

- **The presence cases, in a claim-specific probe.**
  `evidence/correction-120100-probe.py` runs the reviewer's four scenarios and
  writes `correction-120100-probe.json` with exclusive creation. Both exits now
  answer `integrity/schema` for the JSON-null result, the foreign kind and the
  list result, and agree on every one; the SQL-NULL write stays refused by the
  store's own CHECK and is recorded as the unreachable case it is.
- **The controls fail without the correction.** Reverting only discovery's
  presence handling fails the two subtests it is about, on the discovery exit
  only — which is exactly the asymmetry that was the defect.
- Focused class: **42 tests, OK** (40 before, 2 added).
- Manager modules including the sweep: **801 tests, OK, 7.568s**.
- Port-constructing suites: **157 tests, OK, 7.685s**.
- `tests.manager.test_text_sweep`: **3 tests, OK** — no longer red.

### The evidence-custody mistake was mine, and here is what changed

Running `review-119974-probe.py` unmodified overwrote `review-119974-probe.json`,
because that reviewer-authored script wrote to a fixed path. The file now carries
claim120006's corrected results under a claim119974 label and no longer shows the
candidate that review was about. I caused that by re-running somebody else's
self-writing script instead of reproducing its scenarios in my own.

Nothing is reconstructed or silently restored; the append-only review at
14:43:50Z and `correction-120006-probe.json` remain the two honest halves of that
history. Going forward I reproduce a reviewer's scenarios in a claim-specific
script with exclusive output — `correction-120100-probe.py` is written that way,
and I did not run `review-120038-probe.py`, whose own exclusive creation would
have refused anyway.

### Unchanged and still outstanding

Neither production deployment can discharge a gate until its session wrapper
forwards the member — `single_worker._AuthoritySession` is the consumer's
scheduled path, `tools/dogfood_operator.py` the second boundary this scope does
not name. W119114 and W119733 still own the joined serving and restart proof, and
their dependencies stay intact.

**State: awaiting independent review.**
