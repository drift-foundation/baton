# Progress

## Independent design review — 2026-08-21 (`baton.claude`)

Claimed W151 on the `baton.impl` route. The bound thread asked for an
independent review of a design package authored by `baton.codex`, an
append-only review record, and a return to `baton.ops` for the four
explicit rulings. That is what this round did; no application, protocol,
runtime, schema, or `v12/` change was made.

**Revalidated rather than accepted.** Every claim `SPEC.md` labels
*Confirmed* was re-derived from the tree independently — the `work`
schema, `claim_work` not minting `episode_seq`, the six Handler-clear
sites, `close_work`'s Route-only authorization, and the spike's constant
generation / local selectors / in-process token map. All hold. The
record's Confirmed/Observed/Proposed labelling is accurate throughout; I
found no Confirmed claim that is not.

The stale-parent-statement observation is confirmed twice over:
`finding-v12-isolated-agent-workers/FINDING.md:162` asserts v11 enforces
a claim before terminal close, `close_work` contains no such check, and
the repo's own gate closes unclaimed Work in
`tests/work/test_terminal_outcomes.py`.

`evidence/` re-ran clean: **13/13**.

**Five findings**, in `review-2026-08-21T16-20-35Z.md`:

| | Finding |
| --- | --- |
| P1a | the fenced reservation consumes the participant's ONE global claim slot, so a stranded worker is offline for every Route, not just this Work; offer issue and claim also omit capacity as a precondition |
| P1b | verify/review/approve/integrate bypass operation replay — a plain retry of `integrate` rewrites a committed `integrated` receipt to `stale-target`, and the three upstream receipts are silently overwritable |
| P2a | `fenced` + `phase=active` narrows a pinned `EFFECTIVE-BATON.md` guarantee ("no window where the board shows work in progress that nobody is doing") and needs an explicit dated supersession rather than two live statements |
| P2b | open approval 4 — the only recommendation contradicting current v11 — has no executable scenario; the model has no `close` operation at all |
| P3 | offer uniqueness is per-Work in the spec and store-wide in the model, and two successor tests use a fresh `ControlStore`, reintroducing the per-process amnesia the design supersedes |

P1a, P1b, P3 and P2b were each confirmed by running the model directly,
not by reading it.

Explicitly not raised: the accepted-before-expiry token boundary and
drained activation are both sound and I would approve them; §8's
exact-operation settlement is correct and its successor test is the
sharpest in the set; the model's synchronous shape cannot represent a
genuinely unresolved operation, which is an honest limit rather than a
defect.

**State: passed to `baton.ops` for the four rulings**, not closed —
independent review is preserved by handing the design gate on. P1b and P3
are evidence defects owned by the design's author and do not block
rulings 2 and 3.

## Post-ruling contract revision — 2026-08-21 (`baton.claude`)

Claimed W151 again on the `baton.impl` route after `baton.prompt` rerouted it
there (the four rulings are pinned, so this round is implementation of the
design record, not new product discretion). PLAN item 7 is done. No v11 or
v12 application, protocol, runtime, schema, or dependency change was made;
everything in this round is inside this dossier.

**Revalidated before acting.** `src/` is unchanged since my `0-design`
review, and I re-derived the two facts the rulings turn on rather than
trusting the record: the six Handler-clear sites are still exactly
`_recompute_ready:814`, `close_work:1357`, `release_claim:1549`,
`set_phase:1852`, `post_thread:3508`, `pass_work:3745`, and `claim_work`
still enforces one-live-claim capacity per participant at
`transitions.py:1464-1472`. The stale parent close statement no longer needs
correcting from here: the parent record already carries a dated partial
supersession under "V11 enforcement boundary".

**`SPEC.md` is now version `1-ruled`**, opening with a §0 table that maps each
ruling and each review finding to the sections it moved. The two rejected
`0-design` proposals are marked superseded in §1 rather than deleted, so the
reasoning that was overruled is still readable.

| Ruling | How the contract changed |
| --- | --- |
| 1 cancellation | One transaction fences the exact generation AND ends the assignment: Handler clears, the participant's claim slot frees, and the Work sits `block` behind typed `runtime-quiescence:<gen>`. Sealed/quarantined output with intake dispositions; discard needs a pinned disposable-attempt policy; cleanup blocks on intake |
| 2 token expiry | Durable `issued -> accepted` before expiry is the boundary and reserves nothing — the claim still rechecks route, capacity, gates and state. A separate visible `settlement-expired` state ends an unsettled accepted offer without reviving its token |
| 3 contract progression | Typed per-Work `assignment_contract`; the current Handler advances it atomically with its own assignment end; no certified profile means a typed `contract-runtime:<contract>` gate. Generation minting became contract-conditional, which supersedes `0-design`'s "every claim mints one" |
| 4 terminal close | Unclaimed authorized close preserved; a close ending a live assignment requires the full exact identity, and omitted / participant-only / stale / fenced identities all refuse |

**Review findings.** P1a: capacity is now an explicit precondition of both
offer issue and claim, and ruling 1 removes the strand it warned about — a
cancelled worker's participant is free immediately, and only the replacement
waits. P1b: the four workflow receipts are immutable and replay-only, and a
refused integration is journalled as an attempt instead of rewriting a
committed `integrated` receipt. P2b: every ruled close case now has a
scenario. P3: offer uniqueness is scoped per Work and demonstrated with two
Works over one shared control store; the successor tests share the durable
store instead of constructing a fresh one. **P2a is dissolved rather than
accepted** — it warned about `fenced` + `phase=active` narrowing the pinned
`docs/EFFECTIVE-BATON.md` guarantee, and ruling 1 removed that state
entirely, so the guarantee stands unnarrowed and nothing in
`docs/EFFECTIVE-BATON.md` was superseded or touched.

**Evidence: 13 -> 27 scenarios, all passing** (`python3 -m unittest -v
test_assignment_state_model.py` from `evidence/`). The model gained a
`Deployment` holding deployment-wide claim capacity, certified contracts, the
contract-transition policy, and the isolation/retention clauses, so scenarios
that need two Works now build two authorities over one deployment and one
control store.

One residual is recorded in `FINDING.md` and `SPEC.md` §12 rather than
silently resolved: ruling 3 gives contract advancement to the current Handler,
so unclaimed Work advances by being claimed first — ordinary for `queued`
Work, unavailable for Work already gated or parked. I did not invent an
unclaimed transition path for it.

**State: awaiting focused independent review** by `baton.codex` (PLAN item 9).
Passing W151 back to `baton.feat` rather than closing it; the reviser does not
certify her own corrections.

## Focused-review response — 2026-08-21 (`baton.claude`)

Claimed before executing (seq 1201). All seven additive scenarios reproduced
red first — 27 passed, 6 failed, 1 error of 34, exactly the reviewer's
numbers — and every correction is mutation-checked below. PLAN item 10. No
v11 or v12 application, protocol, runtime, schema, or dependency change; the
round is confined to this dossier and the parent record's decision history.

### P1 — a settlement timeout could hide a committed claim

Confirmed, and the trace is worse than an inconsistency: the authority mints
generation 1, records Handler and consumes the participant's ONE deployment
-wide claim slot; the manager loses the result before writing `claimed`; the
timeout reads only the offer row and expires it; every later claim then
refuses "offer was not accepted". The Work is live and unrecoverable, holding
a slot that takes the participant offline everywhere — the same stranding
ruling 1 was written to prevent, arriving through the offer row instead.

My own §8 says an ambiguous claim is settled by its fixed operation, and the
timeout was the one path that settled by current state instead. It now
resolves that operation first: a committed claim WINS and is recorded
`claimed` with its assignment bound late, and only a claim the authority
positively reports as uncommitted becomes `settlement-expired`.

**Added beyond the ask:** an unanswerable lookup is not an answer. If the
authority cannot be asked, the offer stays visibly `accepted` and unsettled
rather than expiring on a default — "I could not ask" must never be read as
"it did not commit", which is the same failure in a smaller window.

### P1 — effectively-once stopped at the authority boundary

Confirmed on all four counts, and the framing is the correction: the
authority's operation journal protects AUTHORITY state and says nothing about
the control store, so an exact retry replayed the authority result and then
re-ran the manager's own write on top of newer observations.

- Manager-owned mutations (cancel, collect, freeze) now carry their own
  durable operation records in the control store.
- Runtime observations are monotonic and `destroyed` is terminal. This is a
  second, independent protection: positive proof of absence is the strongest
  evidence the model has, it is what satisfies a `runtime-quiescence` gate,
  and no replay or later call may walk it back.
- `freeze` is immutable: the same digest replays — the honest answer to a lost
  response — and a different one refuses, because a published proposal is
  bound to the digest of bytes that were declared frozen.
- A refusal that wrote something durable is itself a committed outcome. The
  stale-target integration journals its attempt before refusing, so its
  operation record binds that refusal and the retry replays it instead of
  appending a second attempt or, if the target moved back meanwhile, taking a
  different outcome under one identity.
- `end`, `advance_contract` and `close` now bind their reason/rationale in the
  replay signature. That prose is written into the authoritative event, the
  contract history, or the terminal outcome, so it is a durable operand, and a
  signature that omits it returns the first result for a materially different
  request.

### P2 — competing live text about generation minting

Confirmed, and it is exactly the failure mode `AGENTS.md` names: two live
rules that both look authoritative. The parent "Assignment-generation
identity" ruling now carries a dated **Narrowed 2026-08-21** clause scoping
minting to the v12 assignment contract, with everything else in that ruling
explicitly left standing; this record's "Confirmed parent decisions" bullet
mirrors it; and `SPEC.md` §1 no longer claims the contract supersedes no
parent ruling — it names this one narrow supersession and its location.

### Regressions

The reviewer's seven, plus four of mine for the edges these open:

- `settlement timeout leaves an unanswerable claim accepted`;
- `a destroyed runtime observation never walks backwards` (stop, uncertain and
  quiescent all refuse after `destroyed`);
- `an identical freeze replays and a second digest refuses`;
- `an exact collection retry seals exactly one record` and does not resurrect
  a record whose intake already decided.

Mutation-checked, each independently:

| mutation | fails |
| --- | --- |
| settlement timeout ignores the fixed claim operation | the reviewer's settlement scenario and my unanswerable-lookup one |
| an unanswerable lookup reads as uncommitted | only my unanswerable-lookup scenario |
| manager `cancel` has no replay journal | only the reviewer's cancel-retry scenario |
| runtime observations may walk backwards | only my monotonic-observation scenario |
| a refused integration is not durably journalled | only the reviewer's one-attempt scenario |
| `freeze` is not immutable | the reviewer's frozen-output scenario and mine |
| collection has no replay journal | only my one-record scenario |
| `end` replay ignores the durable reason | only the reviewer's end-replay scenario |
| contract replay ignores the durable rationale | only the reviewer's contract-replay scenario |
| `close` replay ignores the durable rationale | only the reviewer's close-replay scenario |

### Verification

- `python3 -m unittest test_assignment_state_model.py` from `evidence/`:
  **38 tests, all passing** (34 with the reviewer's additions and the
  corrections; 27 before this review round).
- No application, protocol, runtime or schema code was touched, so no v11
  gate applies to this round; `src/` is unchanged.

**State: awaiting focused review round 2.** Passed back to `baton.feat`
rather than closed.

## Focused-review round-2 response — 2026-08-21 (`baton.claude`)

Claimed before executing (seq 1267). Both P1s reproduced red first — 38
passed, 3 failed, 1 error of 42, the reviewer's numbers — and every correction
is mutation-checked below. PLAN item 11. No v11 or v12 application, protocol,
runtime, schema, or dependency change.

### P1 — an absent result is not a settlement

Confirmed, and the finding names the real boundary: a linearizable read proves
only its own instant. My round-1 correction moved settlement from "the offer
row says accepted" to "the lookup says nothing committed", which is better and
still not a settlement — a submitter can pass its preconditions and commit
immediately after the read, leaving a live assignment holding the
participant's deployment-wide slot behind a terminal control row. The reviewer
committed at exactly that boundary.

The second half is the one I would have missed on my own: `Manager.claim`
writes `claim-refused` on an ordinary authority refusal, and an ordinary
refusal is deliberately NOT durably bound — correct for the operation, which
stays retryable, and wrong for the offer, which the control store has just
called terminal. After the competing Handler releases, a stale retry of that
same fixed operation mints an assignment for a retired offer. No timing hook
needed.

The correction is that an operation identity now has a fourth durable state.
`Authority.settle_operation` is ONE act that either finds the committed result
or RETIRES the identity, and retirement is answered before the operand
signature — it belongs to the identity, not to what any particular submitter
asks with it. `Manager` uses one `_terminalize` path for both the settlement
timeout and the `claim-refused` row, so the rule holds in one place: no
terminal control row may coexist with a claim operation that can still commit.
A claim the settlement finds committed still wins and is recorded, however
late, and an unanswerable lookup still leaves the offer accepted.

### P1 — intake and cleanup lacked the identities §7 promised

Confirmed, and this one is a plain gap between my own spec text and my own
model: §7 said every manager-owned mutation carries a durable operation
record; I gave records to cancellation, collection and freeze and stopped.

Intake now carries a disposition operation identity with the disposition in
its signature — an exact retry replays the committed decision instead of
answering "already recorded", a conflicting retry under the same identity
refuses as reused operands, and a genuinely second decision under its own
identity still refuses as the second decision it is. Cleanup writes
`blocked-on-intake` before refusing, so that refusal is a committed outcome of
its operation and the SAME operation replays it; a distinct cleanup operation
is free to re-evaluate a boundary that has since moved. `ControlStore.replay`
gained the same `durable_refusal` mechanism the authority already had, rather
than a second one.

### My own scenario asserted the overturned behaviour

`test_cancelled_output_is_sealed_until_an_intake_disposition` called
`cleanup(offer_id)` twice under the default identity and expected the second
to succeed once intake moved. Under the ruled contract that is the same
operation taking a different outcome. I corrected my own scenario — the
post-intake call now passes its own operation id — rather than touching the
reviewer's regression, and flag it here because it is an assertion changing,
not just an addition.

### Regressions

The reviewer's four, plus three of mine:

- `a retired claim operation stays dead for every submitter` — a second
  timeout is refused, the retired identity refuses even after the Work is free
  again, and a fresh offer with its own identity still claims;
- `a conflicting intake decision is refused either way` — same identity with a
  different disposition, and a distinct identity after the fact;
- `a new cleanup operation may re-evaluate the intake boundary` — the old
  identity keeps replaying its refusal while the new one completes and then
  replays its success.

Mutation-checked, each independently:

| mutation | fails |
| --- | --- |
| settlement reads instead of retiring the operation | both reviewer settlement scenarios and my retirement one |
| settlement decides from the point-in-time read alone | only the reviewer's later-commit race |
| a refused claim leaves its operation live | only the reviewer's terminal-refusal scenario |
| retirement is answered after the operand signature | only my retirement scenario |
| intake has no operation identity | the reviewer's intake replay and my conflicting-decision scenario |
| cleanup's state-writing refusal is not durable | the reviewer's cleanup scenario and my re-evaluation one |

### Verification

- `python3 -m unittest test_assignment_state_model.py` from `evidence/`:
  **45 tests, all passing** (42 with the reviewer's additions and the
  corrections; 38 before this review round).
- No application, protocol, runtime or schema code was touched, so no v11
  gate applies to this round; `src/` is unchanged.

**State: awaiting focused review round 3.** Passed back to `baton.feat`
rather than closed.

## Focused-review round-3 response — 2026-08-21 (`baton.claude`)

Claimed before executing (seq 1305). Both P1s reproduced red first — 45
passed, 2 failed of 47, the reviewer's numbers — and every correction is
mutation-checked below. PLAN item 12. No v11 or v12 application, protocol,
runtime, schema, or dependency change.

### P1 — the settlement deadline was specified and never modeled

Confirmed. §6, §7 and §9 all say an accepted offer must be past a visible
settlement deadline before its fixed claim may be retired, and the model had
no such deadline at all: `Offer` carried only the bearer-acceptance expiry and
`settlement_timeout` consulted no clock. It could retire an authorization in
the same instant that authorized it.

Acceptance now records a claim-settlement deadline of its own, from a
deployment `settlement_window`, and it is emphatically not the token's:
ruling 2 made those two boundaries independent, and past the token deadline
the fixed claim is still authorized — that is the entire content of the
accepted-before-expiry ruling. A regression asserts they cannot be conflated.

**Where the deadline does NOT apply, deliberately.** It gates RETIREMENT, not
reconciliation. A claim that already committed is recorded `claimed` whatever
the clock says, because making an operator wait for a deadline to LEARN that
the claim committed would strand the assignment for exactly as long as the
deadline — the stranding this whole settlement contract exists to prevent. The
same goes for a claim proven submitted and refused: there is nothing left to
wait for, so the `claim-refused` path retires at once. Both are pinned by
regressions and by a mutation that moves the deadline check earlier and fails
three scenarios, including two of the reviewer's own from earlier rounds.

### P1 — settlement accepted a committed result with the wrong operands

Confirmed, and this is the sharper of the two. `_replay` bound a committed
operation to its signature; `operation_result` and `settle_operation` looked
only at the id. So a committed claim for `baton.claude` under the same
operation id satisfied a settlement for `baton.codex`'s offer, and the
manager bound another participant's assignment to it.

`settle_operation` now takes the fixed claim signature and compares it. A
committed or durably refused record with different operands is an
operation-id collision: it fails closed, adopts nothing, overwrites nothing,
and leaves the offer row exactly as it was — an identity this manager cannot
prove is its own is not one it may declare over. Retirement of an unsubmitted
identity binds the operands it settled, so the journal says which operation
died, and `Authority.operation_record` makes that binding readable; without a
read for it, "bound" would have been an unobservable claim. Retirement is
still answered before any operand comparison, so a stale submitter learns the
identity is dead rather than that its operands disagree — the two properties
coexist exactly as the review said they could.

### Three of my own scenarios needed the new precondition

`test_settlement_timeout_never_revives_the_consumed_token`,
`test_settlement_timeout_leaves_an_unanswerable_claim_accepted` and
`test_a_retired_claim_operation_stays_dead_for_every_submitter` all called the
timeout in the same instant as acceptance, which the ruled contract now
forbids. Each advances the clock to the offer's own recorded `settle_by`
first. What they assert is unchanged; only the precondition is now stated.
Flagged here because assertions moving is different from assertions being
added.

### Regressions

The reviewer's two, plus four of mine:

- `the settlement deadline is not the token deadline` — they differ, the
  timeout still refuses past the token deadline, and the fixed claim still
  claims successfully there;
- `a committed claim reconciles before its settlement deadline`;
- `a colliding operation identity changes no record` — after the deadline,
  where the manager would otherwise have authority to retire;
- `a retirement names the operation it killed`, while every submitter still
  meets the retirement first.

Mutation-checked, each independently:

| mutation | fails |
| --- | --- |
| the settlement timeout ignores its deadline | the reviewer's immediate-timeout scenario and my two-deadlines one |
| the settlement deadline reuses the token expiry | only my two-deadlines scenario |
| a live claim is retired instead of observed | the reviewer's immediate-timeout scenario and my two-deadlines one |
| the deadline is checked BEFORE reconciling a committed claim | my reconciliation scenario and the reviewer's round-1 and round-2 settlement scenarios |
| settlement ignores the fixed claim signature | the reviewer's wrong-operands scenario and my collision one |
| retirement is recorded without binding its operands | only my retirement-record scenario |

### Verification

- `python3 -m unittest test_assignment_state_model.py` from `evidence/`:
  **51 tests, all passing** (47 with the reviewer's additions and the
  corrections; 45 before this review round).
- No application, protocol, runtime or schema code was touched, so no v11
  gate applies to this round; `src/` is unchanged.

**State: awaiting focused review round 4.** Passed back to `baton.feat`
rather than closed.

## Focused-review round-4 response — 2026-08-21 (`baton.claude`)

Claimed before executing (seq 1340). The single P1 is corrected. Reproduced
red first — 51 passed, 1 failed of 52, the reviewer's numbers — and the
correction is mutation-checked below. PLAN item 13. No v11 or v12 application,
protocol, runtime, schema, or dependency change.

### P1 — retirement did not preserve its terminal disposition across a crash

Confirmed, and it is the same ambiguity the authority-side settlement was
introduced to remove, one layer further out. Rounds 2 and 3 moved the decision
from "the control row says accepted" to "the authority says the identity is
dead" — but the authority only said DEAD. Which terminal state the offer took
was still supplied by whichever manager path noticed: `settlement-expired`
from the timeout, `claim-refused` from the claim. Since the authority record
and the control row are separate durability boundaries, a manager crashing
between them hands that choice to whatever arrives next, and the reviewer's
trace crashes at exactly that point: a settlement timeout retires the
identity, a later claim finds the retirement, and the offer terminalizes as
`claim-refused` — an outcome nobody decided.

The retirement now binds its disposition alongside the operands and reason,
and `_terminalize` treats its caller's state as a PROPOSAL: any retirement it
finds already carries the answer, and that one wins. The reason is bound for
the same reason and to the same effect — a stale submitter meeting the
retirement is told what the identity died of, not a message invented by the
path it happened to take.

**Both directions, deliberately.** The reviewer's regression covers a timeout
retirement met by a later claim path. I added the mirror: a claim positively
submitted and refused retires as `claim-refused`, and a later settlement
timeout on that identity replays `claim-refused` rather than overwriting it
with `settlement-expired`. A rule that only held in the direction it was
reported in would be an accident, not a contract.

### One of my own scenarios reads the richer record

`test_a_retirement_names_the_operation_it_killed` asserted on the
retirement's free-form reason string. The record is now structured, so it
asserts on the reason AND the bound disposition. Flagged because the assertion
changed rather than merely being added — though in this case it strengthened.

### Regressions

The reviewer's one, plus two of mine:

- `a refused claim retirement keeps its own disposition` — the mirror
  direction, with the row reopened as a crash would leave it;
- `a replayed retirement reports the reason it died of` — to the original
  participant and to a stale one with different operands alike.

Mutation-checked, each independently:

| mutation | fails |
| --- | --- |
| the caller's entry path chooses the outcome of an existing retirement | the reviewer's crash scenario and my mirror one |
| retirement records no disposition (hard-codes one) | my mirror scenario and three earlier claim-refusal scenarios |
| an existing retirement reports a different disposition than it bound | only the reviewer's crash scenario |
| a replayed retirement invents its own message | my reason-replay scenario and two earlier retirement scenarios |

### Verification

- `python3 -m unittest test_assignment_state_model.py` from `evidence/`:
  **54 tests, all passing** (52 with the reviewer's addition and the
  correction; 51 before this review round).
- No application, protocol, runtime or schema code was touched, so no v11
  gate applies to this round; `src/` is unchanged.

**State: awaiting focused review round 5.** Passed back to `baton.feat`
rather than closed.
