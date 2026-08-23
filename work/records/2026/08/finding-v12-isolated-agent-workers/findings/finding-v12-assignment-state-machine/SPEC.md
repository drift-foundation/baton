# V12 assignment state and identity contract

Version: `1-ruled` (supersedes `0-design`, 2026-08-21; revised after the
focused reviews of 2026-08-21T21:06:44Z, 2026-08-21T21:27:27Z,
2026-08-21T21:40:39Z, 2026-08-21T21:48:06Z, and the signed-off review of
2026-08-21T21:52:09Z; §6 and §7 amended 2026-08-22 by the W4487 decline
ruling — see "Superseded by W4487" in §1; §7 clarified 2026-08-22 by the
W4487 re-review with the exact claim-token verifier derivation)

Status: the four open approvals of `0-design` were ruled by `baton.slaw` on
2026-08-21 and are pinned in `FINDING.md`. This revision folds those rulings
into the contract and corrects the evidence defects raised in
`review-2026-08-21T16-20-35Z.md`. It is an executable design record signed off
by focused independent review on 2026-08-21. It is not a wire-compatibility
promise and does not itself authorize changes to v11 or the accepted `v12/`
spike; implementation requires separately assigned Work.

## 0. What this revision changes

| Source | Change |
| --- | --- |
| Ruling 1 (cancellation) | §5, §6, §7, §9, §10, §11 — cancellation now ENDS the assignment, frees the participant slot, and installs a typed `runtime-quiescence` gate. The `fenced`+`phase=active` retained-Handler cross-product is withdrawn. Output retention added. |
| Ruling 2 (token expiry) | §6, §7 — durable `issued -> accepted` before expiry is the boundary; a claim-settlement timeout is separate and never revives the token. |
| Ruling 3 (contract progression) | §4, §5, §7, §9, §10 — one additive superset schema plus a per-Work typed contract selector and a typed `contract-runtime` gate. The global drained activation is withdrawn. |
| Ruling 4 (terminal close) | §7, §10 — authorized unclaimed close is preserved; a close that ends a live v12 assignment must carry the full exact identity. |
| Review P1a | §7 — one-live-claim capacity is now an explicit precondition of BOTH offer issue and claim. |
| Review P1b | §7, §10, §13 — the four workflow receipts are immutable and replay-only; a refused integration is journalled as an attempt and never rewrites a committed receipt. |
| Review P2a | Dissolved by ruling 1: no Work is `active` without an executor, so the pinned `docs/EFFECTIVE-BATON.md` guarantee stands unnarrowed and needs no supersession. |
| Review P2b | §13 — the close rulings now have executable scenarios. |
| Review P3 | §6, §13 — offer uniqueness is scoped per Work over one shared durable control store. |
| Focused review P1 (settlement) | §6, §7, §8, §9 — a claim-settlement timeout settles the FIXED claim operation before it may terminalize an offer. |
| Focused review P1 (effectively-once) | §3, §7, §9, §10 — manager-owned mutations carry their own operation records, runtime observations never regress, frozen output is immutable, a refused act that wrote something durably replays its refusal, and every replay signature carries the durable prose it commits. |
| Focused review P2 (minting) | §1 — the narrowing of the parent generation ruling is now an explicit dated scoped supersession in the parent and child records. |
| Focused review 2 P1 (settlement) | §4, §6, §7, §8, §9, §10 — a fixed operation becomes durably committed or RETIRED before any control row may call it terminal; a point-in-time absence read settles nothing. |
| Focused review 2 P1 (intake/cleanup) | §7, §9, §10 — intake and cleanup carry the operation identities §7 already promised, with intake's disposition in the signature and cleanup's state-writing refusal durable to its own operation. |
| Focused review 3 P1 (deadline) | §6, §7, §10 — the claim-settlement deadline is a distinct durable boundary from the bearer-acceptance deadline, and retirement requires it; reconciling an already committed claim does not. |
| Focused review 3 P1 (operands) | §4, §7, §8, §9, §10 — settlement takes and validates the FIXED claim signature; a committed or durably refused record under the same id with different operands is a collision that fails closed and changes nothing. |
| Focused review 4 P1 (disposition) | §4, §7, §9, §10 — a retirement durably binds the terminal DISPOSITION it caused, and every manager entry path replays that disposition instead of the one its own path would have chosen. |
| W4487 re-review (verifier), 2026-08-22 | §7 — the claim-token VERIFIER is pinned to one exact derivation: SHA-256 over the bearer's own UTF-8 bytes, serialized `sha256:<64 lowercase hex>`. This contract owns the offer record and had left the derivation unstated, so worker-control's new operation-signature payload computed a different value for the same token and called it the same thing. A clarification, not a supersession: nothing previously stated is reversed. |
| W4487 ruling (decline), 2026-08-22 | §1, §6, §7 — DECLINE no longer requires the bearer. It is authorized by the exact integrity-protected `offer.decide` binding and consumes the verifier without echoing the token. Acceptance is unchanged and still requires the exact unspent, unexpired bearer. This amends `1-ruled` AFTER sign-off and is the only post-freeze change to this contract. |

## 1. Supersession boundary

If approved, this contract supersedes three production readings of the
accepted `0-spike` only:

1. `generation: 1` becomes an authority-minted monotonically increasing
   per-Work generation;
2. `W2`-style local selectors in durable envelopes become structured full
   authority and Work identity; and
3. per-process offer/token memory becomes a durable Worker Manager control
   record containing a verifier, never the bearer token.

The spike remains valid evidence for its bounded fresh-authority experiment.

**One confirmed parent ruling is narrowed, explicitly.** The parent
"Assignment-generation identity" ruling (2026-08-20) says the successful
atomic claim generates the assignment generation, without qualification.
Ruling 3's per-Work contract progression narrows that to claims under a v12
assignment contract: a `v11` claim mints none, and a Work's first positive
generation is minted by its first claim after entering the v12 contract. The
old text and its reasoning stand; only the unqualified reading is superseded.
The dated supersession is recorded in the owning parent record
(`work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`,
"Assignment-generation identity") and mirrored in this record's
`FINDING.md`. Nothing else in the parent rulings is superseded.

**Superseded within this record, 2026-08-21.** Two `0-design` proposals are
withdrawn by the approver rulings and are retained here only as history:
`assignment_publication=fenced` retaining Handler and `phase=active` as a
recovery reservation (§5, §12 of `0-design`), and the globally drained v12
schema activation that minted a generation for every claim (§12 of
`0-design`). Neither is part of this contract.

### Superseded by W4487, 2026-08-22 — the decline token requirement

**The superseded text.** §7's `Decline` row read, in the signed-off
`1-ruled` contract:

> | Decline | agent through manager; **exact unspent token** | offer
> `declined`, verifier consumed | token dead | intent digest | terminal
> offer |

**Why it is superseded.** Worker-control 1.0
(`../finding-v12-worker-contract/findings/finding-worker-control-api-manifests/SPEC.md`
§6.1) carries the token for acceptance only, and its frozen
`worker-control-1.0.schema.json` mechanically REQUIRES `claim_token: null`
when `decision=decline`. Both contracts were frozen, and a Worker Manager
could not satisfy both by any implementation choice: the W151 shape is a
schema-invalid document on the wire. The contradiction is recorded at
`work/records/2026/08/finding-worker-control-decline-token-conflict/` and
was ruled by `baton.slaw` on 2026-08-22.

**What replaces it.** The non-secret decline envelope is kept. A decline is
authorized by the exact integrity-protected `offer.decide` operation bound
to `(offer_id, runtime_attempt_id, work_ref, decision, reason)`; the
manager validates that whole binding and atomically consumes the offer's
durable verifier without minting a claim. §0's precedence rule — "if
worker-control conflicts with W151, W151 wins" — is not weakened in
general; this one conflict is settled in worker-control's favour by an
explicit ruling, and that is the only way it could be settled at all.

**What is NOT superseded.** Every other property the token requirement was
carrying stands, and is carried by the binding instead: the decline is
bound to the exact issued offer and cannot terminate another, it is
effectively once, it consumes the verifier so the bearer is dead
afterwards, and it mints no claim and takes no capacity.
**Acceptance is untouched** and still requires the exact unspent, unexpired
bearer, succeeding only through the canonical claim transaction. The
reasoning behind the old requirement — that a terminal act on an offer must
prove it is that exact offer — is the reason the binding has to be exact,
not a reason to keep transmitting a secret in order to refuse authority.

## 2. Confirmed facts revalidated against the current tree

Re-derived at checkpoint `c529b28`; `src/` is unchanged since the `0-design`
review.

- **Confirmed.** V11 stores `handler_team`, `handler_member`, and
  `episode_seq` on `work`. It has no assignment-generation counter or live
  assignment record (`src/baton_work/authority.py`, `work` table).
- **Confirmed.** V11 `claim_work` deliberately does not mint `episode_seq`;
  it sets Handler and `phase='active'` atomically. Therefore `episode_seq`
  cannot fence consecutive claims (`src/baton_work/transitions.py`,
  `claim_work` and `_mint_episode`).
- **Confirmed.** V11 enforces one-live-claim capacity per participant inside
  the claim write transaction: "a participant holds ONE active claim at a
  time" (`src/baton_work/transitions.py:1464-1472`). Capacity is therefore a
  deployment-wide fact, not a per-Work one, and any v12 reservation that
  retains Handler takes the participant offline for every Route.
- **Confirmed.** The accepted spike writes `generation: 1`, carries local Work
  selectors in durable envelopes, and retains its token issuer key and
  issued/spent map in one manager process (`v12/src/manager.mjs`,
  `envelopes.mjs`, and `claim_token.mjs`). These are explicitly disposable
  `0-spike` choices.
- **Confirmed.** Current v11 Handler-clear paths are exactly six —
  `_recompute_ready:814`, `close_work:1357`, `release_claim:1549`,
  `set_phase:1852`, `post_thread:3508`, `pass_work:3745` — i.e. dependency-gate
  readiness loss, terminal close, release, explicit unclaimed phase, blocking
  request, and pass. A v12 generation fence must be centralized across all of
  them, not added only to `release`.
- **Confirmed.** Current v11 `close_work` is Route-authorized and can close
  unclaimed Work; unlike `pass_work` and `revise_work`, it does not check the
  exact current claimant. The parent record's contrary statement was stale and
  has since been corrected in place with a dated partial supersession
  (`work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`,
  "V11 enforcement boundary" section). Ruling 4 settles the policy question:
  see §7.

## 3. Ownership boundaries

Three stores own different facts:

| Owner | Durable facts | Not authoritative for |
| --- | --- | --- |
| Baton v12 authority | Work route/phase/Handler, per-Work contract selector, per-Work generation counter, live assignment generation, fenced generations, typed gates, assignment-ending events, contract-transition events, gate-satisfaction evidence, proposal and workflow receipts | container/process health, bearer tokens, artifact bytes |
| Worker Manager control store | offer verifier and lifecycle, manager attempt, runtime identity and reconciliation, input/policy digests, output freeze, sealed/quarantined output and its intake disposition, artifact locators, cancellation/quiescence observations | Work phase, Handler, generation allocation, contract selection |
| Immutable artifact store | frozen result/proposal bytes and content digests, sealed cancellation output | permission to publish or integrate |

The control store is shared by active managers in one deployment and uses
compare-and-swap. A process-local map is a cache only. The authority remains
the sole arbiter of who holds the Work, which contract governs it, and which
assignment generation is current.

Sealed cancellation output is control-store and artifact-store material. It
enters the canonical path only by being submitted as a normal proposal by some
later live assignment; intake never publishes on the dead generation's behalf.

## 4. Durable identity shapes

Compact labels are display-only. Durable records use these conceptual shapes:

```json
{
  "work_ref": {
    "authority_uuid": "full authority UUID",
    "work_id": "full canonical Work ID"
  },
  "assignment_ref": {
    "work_ref": { "authority_uuid": "...", "work_id": "..." },
    "participant": "team.member",
    "generation": 7
  }
}
```

- `offer_id`: opaque random identifier for one pre-claim handoff.
- `runtime_attempt_id`: opaque random identifier for one manager-controlled
  attempt. It is bound to the offer and later to the assignment but is not the
  assignment identity.
- `assignment_ref`: exactly `(authority UUID, full Work ID, participant,
  positive generation)`.
- `assignment_contract`: a typed per-Work selector (`v11`,
  `v12-assignment-1`, …). It is Work state, NOT identity and NOT the
  generation. It decides which rules the next assignment runs under.
- `result_id`: opaque immutable-result identifier plus a required content
  digest and `assignment_ref`.
- `proposal_id`: opaque immutable-proposal identifier plus required result,
  candidate-tree, target, input, policy, and assignment digests.
- `verification_id`, `review_id`, and `approval_id`: immutable receipts bound
  to one `proposal_id`, its candidate digest, and its target revision. They are
  distinct even when configuration permits one participant to hold more than
  one role.
- `quarantine_id`: one sealed cancellation-output record, bound to its
  `work_ref`, ended generation, cancellation reason, and policy provenance.
- `gate token`: a typed, displayed scheduler gate — `runtime-quiescence:<gen>`,
  `contract-runtime:<contract>`, `plan-revision:<plan digest>`. A gate is a
  reason the Work cannot run; it is never a worker or runtime state.
- `operation_id`: stable identity for one requested mutation. Claim uses a
  deterministic value derived from `offer_id`; later assignment-owned acts use
  the full assignment and a caller-stable action identifier; workflow receipts
  use the receipt's own operation identity; intake and cleanup each carry
  their own. An operation identity is durably in exactly one of four states —
  UNSUBMITTED, COMMITTED, REFUSED (only when the refusal itself wrote
  something), or RETIRED. Retirement is a property of the identity rather than
  of any one request's operands: once retired, every later and stale submitter
  is refused, whatever it asks for. The retirement record still BINDS the
  operands it settled, so the journal says which operation died; that binding
  is audit evidence, not a second gate. It also binds the terminal
  DISPOSITION the retirement caused — which state the control row takes
  because of it — and the reason, so a later reader learns why the identity
  died rather than a message invented by whoever noticed.

  An identity is never a substitute for the operands. Reading a committed
  result by id alone proves only that SOMETHING committed under that id — a
  collision, if another submitter reused it — so anything acting on that
  result compares the full expected signature and fails closed on a mismatch
  without adopting or overwriting the other operation's record.

None of `offer_id`, runtime attempt, result, proposal, readiness episode,
runtime incarnation, claim-event sequence, contract selector, or accepted
configuration generation substitutes for `assignment_ref`.

## 5. Authority record

**Proposed.** Every Work row in the additive superset schema has:

- `assignment_contract`: typed selector; existing Work initially retains `v11`;
- `assignment_generation`: non-negative counter, never decremented or reused;
- `live_assignment_generation`: nullable positive integer;
- `fenced_generations`: the ended generations that were fenced, with cause;
- `gate`: the one typed gate holding the Work, as v11 already displays.

Handler continues to hold the participant. The core invariants are:

```text
handler is non-null  implies  phase == active
handler is null      implies  phase != active
                      and     live_assignment_generation is null

contract == v11   and handler non-null  implies live generation is null
contract >= v12   and handler non-null  implies
        live_assignment_generation == assignment_generation

a fenced generation is never the live generation
publication requires a live assignment under a v12 contract
```

There is no live `fenced` publication state and no assignment without an
executor. When an isolated assignment must stop, one authority transaction
fences the exact generation AND ends the assignment (§7, Cancel). Between
those two facts there is no observable window: publication cannot outlive the
fence, and Handler cannot outlive the end.

This single-transaction reading is derived, not assumed. The ruling says the
authority "first fences its exact generation and then ends the live
assignment", AND that the Work is "`block`, never `active`, while no
participant is authorized to execute it". Two separate transactions would
leave exactly the state the second sentence forbids — fenced, so nobody may
execute, yet still `active` with a Handler — so the ordering is internal to
one commit.

**Generation minting is contract-conditional.** A claim mints a generation
only when the Work's contract is a v12 assignment contract; a `v11` claim
mints none and behaves exactly as v11 does today. The consequence is explicit:
under `v11` two consecutive claims by the same participant are
indistinguishable, which is precisely the defect the contract progression in
§7 exists to fix — not an oversight in this model.

This replaces the `0-design` rule that every claim, including legacy claims
during coexistence, mints a generation. The counter is still never decremented
or reused, and a Work's first v12 claim mints its first positive generation.

## 6. Offer and attempt records

The Worker Manager persists at most one nonterminal offer **per Work** in a
control store shared across managers and Works:

```text
issued -> accepted -> claimed
   |         |    \
declined     |     settlement-expired
expired      claim-refused
abandoned-after-restart
```

The issued record stores `offer_id`, full `work_ref` binding, token
verifier/digest, manager-observed issue/expiry times, runtime attempt,
readiness episode as advisory evidence, and pinned input/policy/profile
digests. It never stores the bearer token.

**The verifier is one exact value (clarified 2026-08-22, W4487 re-review).**
This contract owns the offer record, so it owns what the verifier IS, and it
did not say. The derivation is

```text
verifier = "sha256:" + lowercase hex of SHA-256 over the bearer's own UTF-8 bytes
```

The token's OWN BYTES, not a JSON encoding of them. A bearer is a secret
string rather than a JSON document: hashing its encoding brings the quotes and
the escaping rules into the value, so two peers that escape a character
differently derive different verifiers for the same secret. The bytes have one
answer. The `sha256:` prefix is the family's one digest representation
(worker-control §3.2), it is what that frozen schema's `digest` type accepts,
and it names the algorithm — so replacing SHA-256 later is a visible change
rather than a silent reinterpretation of 64 hexadecimal characters.

Every consumer uses THIS value. worker-control's §4.2 operation-signature
payload carries it as `claim_token_verifier`; a golden bearer and its verifier
are pinned as literals in both executable models, and the conformance package
asserts the two derivations agree over bearers neither package pins.

Acceptance records a SECOND, separate deadline: the claim-settlement deadline,
after which an operator may declare the fixed claim over. Ruling 2 makes these
two boundaries independent on purpose — the first is how long the bearer has
to accept, the second is how long the accepted claim stays live — so the
settlement deadline is durable in its own right and is never derived from the
token's expiry. Past the token deadline the fixed claim is still authorized;
that is the whole content of the accepted-before-expiry ruling.

Issue preconditions are checked when they are knowable, not discovered after a
single-use token has been spent: the Work is open, unclaimed and not gated or
parked; its contract has a certified runtime profile; no other nonterminal
offer exists **for that Work**; and the intended participant has free
one-live-claim capacity.

The atomic `issued -> accepted` compare-and-swap validates exact binding,
single use, and manager-clock expiry; stores the accepted intent digest and
time; consumes the verifier; and fixes the claim `operation_id`. Once this
commits before expiry, later submission of that already-authorized claim is
reconciliation, not revival of an expired token — the authority transaction
still rechecks route, capacity, gates, and Work state, and refuses normally if
any has changed.

**Refusing authority is authorized differently from taking it (W4487,
2026-08-22).** The `issued -> declined` compare-and-swap takes NO bearer. It
validates the exact `offer.decide` binding — `offer_id`,
`runtime_attempt_id`, `work_ref`, `decision`, and `reason` — against the
issued record, and only then consumes the verifier. So the two decisions
consume the same single-use fact and prove themselves differently: an
acceptance proves possession of the secret because it is about to gain
authority, and a decline proves the exact identity of the offer it is
ending because that is all a terminal act on an offer needs. Sending a
secret in order to reject authority is a leak with nothing bought by it,
and worker-control's frozen schema refuses to carry it at all.

The verifier is single-use across BOTH paths and across expiry. Once
consumed, no bearer can be validated against that offer again, whichever
transition consumed it, so a declined offer's token is exactly as dead as
an accepted one's. The reason is a durable operand and rides the operation
signature: reusing one decline operation id with different prose is an
operand collision, not a replay.

A separate, visible **claim-settlement timeout** may end an accepted offer
that never settles. It does not un-consume the verifier, does not permit a
second acceptance, and does not reinterpret the token. Recovery is a fresh
offer with a fresh bearer.

**The offer row is not the settlement.** An accepted offer that has not
reached `claimed` is exactly the §8 ambiguity — the authority may have
committed the fixed claim while the manager lost the result — so the timeout
resolves that operation before it may terminalize anything. A committed claim
WINS: the offer becomes `claimed` and its assignment is recorded, late, by
whichever process is running. If the authority cannot answer, the offer stays
visibly `accepted` and unsettled; "the lookup was unavailable" is never read
as "it did not commit". A timeout that terminalizes on the row alone strands a
live assignment holding the participant's one claim slot while every later
claim refuses because the offer is no longer accepted.

**And a read is not a settlement either.** A lookup answering "not committed"
proves only its own instant: a submitter may already have passed its
preconditions and commit immediately after the read. So the fixed operation
must become durably terminal in ONE authority act — committed, or RETIRED
against that identity — before any control row calls the offer terminal.
Retirement closes the identity to every later and stale submitter, and the act
finds any claim that committed while the lookup was in flight.

**The retirement decides the outcome; the caller only proposes one.** The
authority record and the control row are separate durability boundaries, so a
manager can commit the retirement and die before writing the row. Whoever
arrives next arrives through whatever entry path it happens to be on — a
retrying claim, another timeout — and if the retirement said only "this
identity is dead", that caller would supply the outcome from its own path: a
settlement timeout silently relabelled as a refused claim. So the disposition
is bound with the retirement, and every manager path that meets one replays
it. A timeout retirement stays `settlement-expired`; a
submitted-and-refused retirement stays `claim-refused`.

Two further things bound that act. It takes the FIXED claim signature and compares it:
a committed or durably refused record under the same id with different
operands is an identity collision, and a collision fails closed rather than
binding another participant's assignment to this offer or overwriting its
record. And retirement — unlike reconciliation — requires settlement
authority: before the claim-settlement deadline the timeout may observe and
record a claim that already committed, but it may not kill one that has not.
Making an operator wait for the deadline to LEARN that the claim committed
would strand the assignment for exactly as long as the deadline.

The same rule governs a refused claim. An ordinary authority refusal writes
nothing and stays retryable, which is right for the operation and wrong for
the offer: a `claim-refused` row beside a live operation lets a stale
submitter retry the same fixed claim once the competing Handler releases, and
mint an assignment for an offer the control store already retired. **No
`settlement-expired` or `claim-refused` row may coexist with a claim operation
that can still commit later.**

A manager that crashes before the accept CAS abandons the unrecoverable bearer
and issues a fresh offer. A manager that crashes after it resumes from
`accepted` with the same claim operation identity.

The runtime attempt has orthogonal fields, not one overloaded status:

- consent runtime: `not-started|running|quiescent|uncertain|destroyed`;
- execution runtime: `not-started|start-requested|running|cancel-requested|`
  `stopping|quiescent|uncertain|destroyed`;
- output: `open|freeze-requested|frozen|invalid|sealed|discarded`;
- worker disposition: `none|completed|unable|plan-rejected|cancelled`;
- proposal: `none|publish-requested|published|superseded`;
- verification: `none|passed|failed|unable` plus reviewer assessment;
- technical review: `none|accepted|changes-requested|rejected`;
- approval: `none|approved|denied`;
- integration: `none|integrated|failed`;
- cleanup: `pending|blocked-on-intake|complete|retained|failed`.

`quiescent` and `destroyed` are different observations and only the second is
positive proof of absence: a quiescent runtime still exists and could resume.

Sealed cancellation output is a separate control record with its own intake
disposition `pending|preserved|revised|submitted|discarded`. Recording an
intake disposition judges the material; it never makes it canonical.

Work remains on its own scheduler axis. A cancelled, uncertain runtime leaves
the Work `block` behind a typed gate with no Handler, while its attempt record
independently reports `uncertain`, `sealed`, and `blocked-on-intake`.

## 7. Transition table

Every authority mutation below is effectively-once. `expect assignment` means
the full four-part identity, never participant alone.

| Transition | Actor and preconditions | Atomic durable write | Capability change | Retry / settlement | Failure state |
| --- | --- | --- | --- | --- | --- |
| Observe | manager; Work is visible | none | none | read again | no offer |
| Issue offer | manager CAS; Work open, unclaimed, ungated, contract certified, no nonterminal offer FOR THIS WORK, participant capacity free | `issued` offer with verifier, binding, expiry, attempt and digests | bearer may request acceptance only | `offer_id` | issued or no change |
| Decline | agent through manager; exact `offer.decide` binding `(offer_id, runtime_attempt_id, work_ref, decision, reason)` over an ISSUED offer with an unspent verifier; **no bearer** (W4487, superseding "exact unspent token") | offer `declined`, verifier consumed, decline reason bound | token dead; no claim minted and no capacity taken | manager operation id whose signature binds the whole binding INCLUDING the reason; an exact replay returns the one committed decline | terminal offer; a stale, foreign, differently bound or operand-colliding decline refuses and changes nothing |
| Expire | manager clock; issued and deadline reached | offer `expired`, verifier consumed | token dead | offer CAS | terminal offer |
| Accept | agent through manager; exact issued binding before expiry | offer `accepted`, verifier consumed, intent digest/time and claim op fixed, and the separate claim-settlement deadline recorded | authorizes one canonical claim attempt; no write/publication capability | offer CAS; replayed token refuses | accepted or no change |
| Settlement timeout | manager policy; offer `accepted`; retirement additionally requires the recorded claim-settlement deadline to have passed | ONE authority act, taking the fixed claim signature, retires that identity and binds the operands, reason and terminal disposition it settled; then the offer takes the BOUND disposition | none; token is not revived, and nothing can commit under the retired identity | operation settlement, then offer CAS; a caller meeting an existing retirement replays its disposition rather than its own | before the deadline it refuses and the fixed claim stays live; a claim found committed is recorded `claimed` whatever the deadline says; an operand mismatch is a collision and changes nothing; an unanswerable lookup leaves the offer accepted |
| Claim | manager; accepted offer, route still permits participant, capacity free, Work still claimable | authority sets Handler/active/live generation, mints a generation when the contract is v12, writes claim event and replayable result | full assignment minted | deterministic claim op with its participant operands; exact replay or operation-result lookup only | ambiguous never activates; a refusal the manager records as terminal must retire the claim identity in the same breath — with positive evidence the claim was submitted and refused, so no deadline applies — while an identity collision leaves the offer untouched |
| Record assignment | manager; exact claim result | control record binds assignment to offer/attempt/digests | none | assignment CAS | recover from claim op |
| Activate runtime | manager; authority projects the exact live assignment and no other execution runtime | start-requested with adapter op, then opaque runtime identity after positive inspect | writable workspace/tools granted only to exact runtime | adapter idempotency plus exact labels | cancel the assignment if identity is ambiguous or duplicated |
| Activity | manager; exact live assignment | authority Event with assignment and idempotency key | none | action id | stale/fenced refusal |
| Cancel assignment | manager/operator; expect assignment | ONE transaction: fence the exact generation, end the assignment, clear Handler, derive `phase=block` with gate `runtime-quiescence:<gen>`, record cause and reason | every worker capability of that generation dies; the participant's one claim slot is freed; no successor can claim while the gate holds | action op; projection of the ended assignment and its gate | wrong or stale generation refuses |
| Force stop / destroy | manager; assignment already ended and fenced | runtime cancellation/stop observations against the exact runtime identity | runtime loses execution | adapter op and inspect | `uncertain` is explicit |
| Quiescence observation | manager/adapter | exact runtime becomes `quiescent`, `uncertain`, or `destroyed`, never regressing to an earlier stage | none by itself | runtime identity proof | no guessed death; a `destroyed` observation is terminal and refuses any later weaker one |
| Collect output | manager; assignment ended, declared outputs only | sealed/quarantined record with `work_ref`, ended generation, cancellation reason, policy provenance, digest | material becomes inspectable, never canonical | freeze/collect op and content digest | `invalid`; discard ONLY where a pinned policy marks the attempt disposable |
| Intake decision | configured trusted intake; sealed record `pending` | disposition `preserved|revised|submitted|discarded` | permits later reuse as INPUT to a future assignment | disposition operation id with the disposition in its signature: an exact retry replays the committed decision, a different one refuses | pending remains a visible loose end |
| Satisfy quiescence gate | manager/operator; gate is the one holding the Work | gate cleared, `phase=queued`, evidence journalled | a successor may now claim and mint the next generation | gate op and evidence digest | refuses without positive absence or a pinned certified-isolation clause |
| Cleanup | manager; no sealed record for that generation is still `pending`, or policy permits discard | attempt cleanup `complete` | none | cleanup op; because the refusal WRITES `blocked-on-intake` it is durable to that operation, while a NEW cleanup operation may re-evaluate the boundary | `blocked-on-intake`; cleanup never changes authority state |
| Freeze output | manager; exact live assignment, runtime quiescent, declared outputs only, output not already frozen | immutable manifest/digest and artifact locator | output becomes immutable | content digest and freeze op; the same digest replays, a different one refuses | invalid/quarantined |
| Record inability | manager; exact assignment, worker stopped/quiescent, rationale and available evidence sealed | immutable `unable` disposition bound to assignment and evidence digests | no successful result or proposal implied | disposition op/id | Work remains for an explicit pass/release/close decision |
| Publish proposal | manager; exact live assignment under a v12 contract, frozen valid output | authority proposal receipt binds assignment and all digests | immutable candidate enters review; worker gains no integration authority | proposal op/id and receipt lookup | stale/fenced/target mismatch refuses |
| Verify candidate | verifier; immutable proposal, exact target/candidate construction, NO verification receipt yet | immutable raw verification receipt and separate assessment | no workflow or integration authority | verification op id; a second write is refused, an exact replay returns the receipt | failed/unable/inconclusive remains evidence |
| Technical review | `rview`; exact proposal, accepted verification assessment, no review receipt yet | immutable review disposition | no canonical write authority | review op id; replay-only | changes requested or rejected; revision is a new proposal |
| Approve | `approv`; exact technically accepted proposal, no approval receipt yet | immutable approval disposition and policy generation | permits only the trusted integrator to attempt CAS | approval op id; replay-only | denial is terminal for this proposal only |
| Integrate | trusted integrator; exact approved proposal, no integration receipt yet, canonical target equals reviewed target | compare-and-swap target update plus immutable integration receipt | canonical target advances; no automatic Work close | integration op id; replay-only, and a refusal that journalled an attempt replays that refusal | refused attempt is journalled ONCE beside the proposal and never rewrites a committed receipt |
| Advance contract | current Handler; expect assignment AND expect current contract; transition permitted by configured policy | ONE transaction: record new contract and rationale, end the old assignment, derive unclaimed scheduler state — `queued` if a certified profile exists, else `block` with gate `contract-runtime:<contract>` | the next claim runs under the new contract; no running worker's constraints change | action op; contract CAS | stale contract or stale assignment refuses; unpermitted target refuses |
| Satisfy contract-runtime gate | operator; a certified profile now executes the Work's contract | gate cleared, `phase=queued`, certification evidence journalled | Work becomes claimable under the already-selected contract | gate op | refuses while no certified profile exists |
| Pass | manager for worker; expect assignment and published result when required | existing Route move plus centralized assignment end | assignment invalid; Handler/live fields clear | action op and exact result | stale generation refuses |
| Release | authorized manager/operator; expect assignment | unclaimed phase derived, Handler/live fields clear, counter retained | assignment invalid | action op and exact result | stale generation refuses |
| Close, unclaimed | authorized actor holding the close capability; no Handler | terminal Work with outcome and rationale | none; no execution claim is manufactured to reach a terminal state | action op | already-closed refuses |
| Close, ending a live assignment | authorized actor; `expect assignment` is MANDATORY and exact | terminal Work outcome plus centralized assignment end, publication invalidation, and an event naming the ended assignment | assignment invalid | action op and exact result | omitted identity, participant-only identity, or a stale generation all refuse |
| Gate arrival / blocking request / unclaimed phase | authority transition; if Handler exists it captures exact assignment | scheduler change plus centralized assignment end in same transaction | assignment invalid | causing action op/event | racing stale acts refuse |
| Plan reject | manager; exact assignment and immutable plan digest | one transaction records disposition, installs `plan-revision` gate, clears Handler/live assignment | assignment invalid; no proposal implied | action op and detail/gate read | stale generation refuses |

The authority implementation must use one assignment-ending helper from every
Handler-clear path. Each event records the ended `assignment_ref`, cause,
whether the generation was fenced, and the gate the transition derived.

**Effectively-once has two boundaries, not one.** The authority's operation
journal protects authority state and says nothing about the control store, so
every manager-owned mutation — cancellation, collection, freeze, intake,
cleanup — carries its own durable operation record too, and that list is
exhaustive rather than illustrative. Without it an exact
retry replays the authority result and then re-runs the manager's own write on
top of newer observations: retrying a cancellation after the runtime was
positively destroyed would walk that observation back to `cancel-requested`,
losing the strongest evidence there is and un-satisfying the gate it settles.

Two further rules make replay honest:

- **Every durable operand rides the replay signature**, including the prose.
  A reason or rationale is written into the authoritative event, the contract
  history, or the terminal outcome; if it were outside the signature, reusing
  one operation id with different prose would silently return the first
  result instead of refusing conflicting operands.
- **A refusal that wrote something durable is itself a committed outcome.**
  The stale-target integration journals its attempt before refusing, so its
  operation record binds that refusal: the retry replays the same refusal
  rather than appending a second attempt, or — if the canonical target moved
  back in the meantime — taking a different outcome under one identity.

## 8. Claim and mutation ambiguity

Participant equality is insufficient to settle an ambiguous claim or mutation:
the same participant may release generation 7 and immediately claim generation
8. The current Handler would match while the stale operation must not.

Settlement order is:

1. exact operation replay or a read-only operation-result lookup;
2. exact full assignment projection when the requested effect has a unique
   current representation;
3. otherwise remain ambiguous and grant no capability.

Reading by identity alone settles nothing twice over: it proves only its own
instant, and it proves only that SOMETHING committed under that id. Every
settlement therefore compares the full expected operands and fails closed on a
mismatch. Reading is how a submitter LEARNS an outcome; it is not how an
outcome is DECIDED. Any actor that wants to declare an unsettled operation over —
a settlement timeout, a terminal offer row, an operator abandoning a stuck
handoff — must retire that operation identity in the authority first. The
read tells you what happened up to an instant; the retirement is what makes
the next instant knowable.

No manager turns `handler == participant` into a recovered claim result. Every
assignment-owned mutation supplies `expect assignment`; this includes
activity, revise, blocking request, plan rejection, result/proposal
publication, contract advancement, cancellation, pass, release, and a close
that ends a live assignment.

## 9. Restart and recovery table

| Last durable boundary | Recovery rule |
| --- | --- |
| Before offer CAS | Nothing exists; observe again. |
| `issued`, bearer may have escaped | Bearer is unrecoverable. Mark the offer `abandoned-after-restart` or let it expire, consume its verifier, and issue a distinct offer. |
| Intent received but accept CAS absent | Treat as not accepted; never infer consent from logs. |
| `accepted`, claim not known | Submit/retry only the fixed claim operation. The accepted-before-expiry record is the authorization; wall-clock expiry does not invalidate it, and a settlement timeout does not revive it. |
| `accepted` and past the settlement deadline | Settle the fixed claim operation FIRST, in one authority act carrying the expected claim operands. Committed: record `claimed` and bind the assignment late. Retired by that act: `settlement-expired`. Operand mismatch: a collision — change nothing. Unanswerable: leave it accepted and unsettled. Never decide from a bare read. |
| `accepted` and BEFORE the settlement deadline | Reconcile only. A committed claim is recorded; an unsubmitted one stays live, because the authorization has not expired and nothing proves it never will settle. |
| A claim refused and the offer called terminal | The refusal alone is retryable, so retire the claim identity in the same act that writes `claim-refused`. A stale submitter then replays the retirement instead of minting after the competitor releases. |
| Claim may have committed | Replay/query the exact claim operation. Current participant alone cannot settle it. No writable runtime starts while ambiguous. |
| Assignment recorded, runtime not requested | Re-read the exact live assignment, then start once. |
| Runtime start ambiguous | Inspect by opaque adapter id plus full assignment labels. Reattach only to one positively identified exact runtime; zero permits a new start only when the prior start is proven absent; mismatch/multiplicity cancels the assignment. |
| Runtime running | Reattach only with positive proof of the same runtime and assignment. Transport reachability alone is insufficient. |
| Retired identity found on any entry path | Replay the retirement's BOUND disposition into the offer row. The path that found it does not get to choose the outcome; the act that retired the identity already did. |
| Manager mutation ambiguous | Replay/query the manager's own operation record, not just the authority's. Observations only move forward, so a replay never downgrades a later one. |
| Intake or cleanup ambiguous | Replay by that decision's operation id. Intake replays its committed disposition; cleanup replays a `blocked-on-intake` refusal it already wrote. Re-evaluating a moved boundary is a NEW operation, deliberately. |
| Cancel ambiguous | Replay/query the exact cancel operation. Because fence and assignment end commit together, either the generation is fenced and the gate is installed, or neither is; do not send cancellation to a runtime while publication might still be live. |
| Runtime unreachable after cancel | Record `uncertain`. The Work is already unclaimed and gated, so nothing is stranded except the replacement. Satisfy the gate only with positive absence or the pinned certified-isolation clause; otherwise leave the gate visibly held. |
| Collection ambiguous | Recompute the sealed manifest from the sealed store or repeat the same collect op; never collect from a still-writable mount, and never delete before the intake boundary is satisfied. |
| Freeze ambiguous | Recompute manifest from the sealed store or repeat the same freeze op with the SAME digest; a different digest refuses because the output is already immutable. |
| Proposal publication ambiguous | Replay/query proposal receipt by proposal op/id and exact digests. Never mint a second proposal over mutable bytes. |
| Workflow receipt ambiguous | Replay/query by the receipt's own operation id. A second differing write refuses; it never overwrites a committed receipt, and a refused integration is a journalled attempt. |
| Contract transition ambiguous | Replay/query the exact contract operation. Read the Work's current contract and gate: the transition either committed with its assignment end and derived gate, or not at all. |
| Pass/release/close ambiguous | Replay/query the exact operation. A successor assignment proves the old capability stale but does not prove which requested disposition committed. |
| Cleanup ambiguous | Preserve/retain and report failed cleanup; cleanup never changes authority state. |

## 10. Safety invariants

1. `generation` is positive, monotonically increasing per Work, and allocated
   only by a successful authority claim transaction under a v12 contract.
2. At most one live assignment and at most one execution runtime exist for a
   Work, and one participant holds at most one live claim across the whole
   deployment. Capacity is checked at offer issue AND inside the claim
   transaction.
3. No writable workspace, execution tool, canonical activity, result, or
   proposal capability exists before the claim result is settled exactly.
4. Every assignment-owned act compare-and-swaps the full identity. A stale
   generation can never act on a successor held by the same participant.
5. Cancellation fences the exact generation and ends the assignment in one
   transaction. No Work is `active` without an executor, and no ended
   generation can publish, act, or be closed against.
6. Every Handler-clear path clears the live assignment in the same authority
   transaction and leaves the counter unchanged.
7. Work phase carries only scheduler meaning. Offer, runtime, output,
   proposal, cancellation, quiescence, intake, and cleanup never become
   phases; they become at most ONE displayed typed gate, which is the v11
   `block` mechanism and not a new axis.
8. An unreachable runtime is not dead. A replacement claim requires the
   `runtime-quiescence` gate to be satisfied by positive proof that the exact
   runtime is absent, or by an explicit pinned certified-isolation clause
   journalled with its evidence.
9. Cancellation never silently deletes recoverable declared output. Sealing or
   quarantining is the default; discard requires a pinned disposable-attempt
   policy; cleanup waits for the intake boundary. Inspecting or retaining
   sealed material neither accepts it nor makes it canonical.
10. A Work keeps its identity, dossier, history, containment, and
    relationships across a contract transition. A transition never changes
    constraints under a running worker: it ends the assignment in the same
    transaction, and prior assignments and artifacts keep the contract they
    were produced under.
11. Immutable proposal receipt binds the exact assignment, input, policy,
    output, candidate tree, and target digests. Later bytes are a new proposal.
12. Verification, technical review, approval, and integration are four
    separately attributable IMMUTABLE receipts. A second write refuses; only a
    byte-identical replay of the same operation id returns the committed
    result; a refused attempt is journalled separately. Integration requires
    all three prior gates for the exact proposal and target; it never closes
    Work implicitly.
13. Retry can repeat an operation result but cannot repeat a generation mint,
    token acceptance, runtime start, output mutation, proposal identity, or a
    workflow receipt. This holds at BOTH boundaries: a manager-owned mutation
    is effectively-once in the control store as well, an exact replay never
    regresses a terminal runtime observation or rewrites frozen output, a
    refusal that wrote something durable replays that refusal instead of
    repeating it, and every durable operand — including the reason,
    rationale, or outcome prose — is part of the operation's identity.
14. An accepted offer is settled by its fixed claim operation, never by the
    control-store row alone, and never by a point-in-time read. Terminalizing
    an offer requires that operation identity to be durably committed or
    retired in one authority act: no `settlement-expired` or `claim-refused`
    row may coexist with a claim operation that can still commit later.
15. Retirement requires authority to retire. A timeout may retire only after
    the recorded claim-settlement deadline — distinct from and never derived
    from the bearer-acceptance deadline — while a claim proven submitted and
    refused may be retired at once. Reconciling an already committed claim is
    not a retirement and no deadline gates it.
16. A settlement compares the full expected operands, not the operation id.
    A committed or durably refused record under that id with different
    operands is a collision: it fails closed, adopts nothing, and overwrites
    nothing. A retirement binds the operands it settled so the journal says
    which operation died.
17. A retirement binds the terminal disposition and reason it caused. Because
    the authority record and the control row commit separately, every manager
    entry path that meets an existing retirement replays its bound
    disposition; no retry path may relabel an outcome the retirement already
    decided, and no replayed refusal invents its own reason.

## 11. Liveness properties

- An issued offer eventually becomes accepted, declined, expired, or
  abandoned; it cannot block reoffer forever without a visible control-store
  fault, and it never blocks an offer for a different Work.
- An accepted offer eventually settles its one claim operation, or ends
  visibly as `settlement-expired`; it never starts execution speculatively and
  never revives its token.
- A cancelled assignment is always already ended: the participant regains
  capacity immediately, and only the REPLACEMENT waits, behind a displayed
  `runtime-quiescence` gate with its reason.
- Sealed cancellation output eventually receives an intake disposition or
  remains a visible pending loose end; cleanup that is waiting on it reports
  `blocked-on-intake` rather than deleting.
- A Work advanced to a contract with no certified runtime waits visibly on
  `contract-runtime:<contract>` and becomes claimable when a matching
  environment is deployed and certified — the same Work, never recreated,
  never misclaimed under the old contract.
- A plan rejection cannot reoffer the unchanged plan because the
  `plan-revision` gate is installed atomically with assignment end.

## 12. Ruled decisions

The four `0-design` open approvals were ruled on 2026-08-21 and are pinned in
`FINDING.md`; the corresponding `0-design` proposals are superseded (§1).

1. **Cancellation.** Fence the exact generation and END the assignment in one
   transaction; clear Handler, free the participant's slot, and hold the
   replacement behind a typed `runtime-quiescence` gate. Recoverable output is
   sealed or quarantined for policy-controlled trusted intake rather than
   automatically discarded.
2. **Token expiry.** Durable `issued -> accepted` before expiry is the
   deadline boundary; it fixes one exact later claim reconciliation and
   reserves nothing. A separate claim-settlement timeout may end an unsettled
   accepted offer without reinterpreting or reviving the token.
3. **Contract progression.** One additive superset schema plus an
   authoritative per-Work typed contract selector. The current Handler
   advances it atomically while ending its own assignment; an unavailable
   target runtime creates a typed `contract-runtime` gate.
4. **Terminal close.** Authorized unclaimed closure is preserved. A close that
   ends a live v12 assignment must supply and compare its full exact
   assignment identity.

**Residual question, non-blocking.** Ruling 3 gives contract advancement to
the current Handler. Unclaimed Work therefore advances by being claimed under
its current contract first, which is ordinary for `queued` Work but not
available for Work that is already gated or parked. No such case exists today,
and this contract deliberately proposes no unclaimed contract-transition path;
if one is later wanted it is a separate ruling, not an implementation detail.

## 13. Executable design evidence

`evidence/assignment_state_model.py` is a deliberately small executable model
of the authority/control-store split. `evidence/test_assignment_state_model.py`
runs 54 scenarios covering every ruling above. It is not application code and
imports no Baton implementation.

Scenarios added or changed in this revision:

- cancellation ends the assignment, fences generation 1, installs
  `runtime-quiescence:1`, and refuses late publication, late activity, and a
  successor claim (ruling 1);
- cancellation frees the participant's one global claim slot, evidenced by the
  same participant immediately claiming an unrelated Work in the same
  deployment while the cancelled Work stays gated (review P1a);
- an uncertain runtime satisfies the gate only with a pinned certified
  isolation clause, and a destroyed runtime satisfies it by absence, after
  which the successor mints generation 2 (ruling 1);
- cancelled output is sealed with its Work, generation, reason and policy, and
  cleanup refuses until intake decides; discard requires a pinned
  disposable-attempt policy (ruling 1, retention clarification);
- a settlement timeout leaves the consumed token dead and requires a fresh
  offer (ruling 2);
- contract progression keeps the same Work, mints its first generation on the
  first v12 claim, and refuses publication under `v11`; an uncertified target
  contract blocks on `contract-runtime:` until a profile is certified; stale
  contract, stale assignment, and unpermitted targets refuse (ruling 3);
- close scenarios: authorized unclaimed close, refusal when a live assignment
  is present and identity is omitted, refusal for participant-only identity,
  refusal for a stale generation, refusal for a fenced generation, and success
  with the exact identity (ruling 4, review P2b);
- the four workflow receipts refuse a second write, replay byte-identically on
  the same operation id, and journal a refused integration without rewriting a
  committed receipt (review P1b);
- offer uniqueness is per Work, demonstrated by two Works over one shared
  durable control store, which the successor scenarios now also share
  (review P3).

Added after the focused review of 2026-08-21T21:06:44Z:

- a settlement timeout cannot hide an already committed claim, and an
  unanswerable operation lookup leaves the offer accepted rather than expired;
- an exact cancellation retry does not regress a `destroyed` runtime, and no
  observation walks backwards from it;
- a refused integration journals exactly one attempt and replays its refusal;
- frozen output is immutable: the same digest replays, a different one
  refuses;
- an exact collection retry seals exactly one quarantine record and does not
  resurrect a record whose intake already decided;
- `end`, `advance_contract`, and `close` refuse a replay that reuses one
  operation id with different durable prose.

Added after the focused review of 2026-08-21T21:27:27Z:

- a settlement timeout cannot race a claim that commits after its lookup, and
  a retired claim identity stays dead for every later submitter — including
  after the Work becomes free again;
- a claim the manager records as `claim-refused` is terminal for that
  operation, so a stale retry cannot mint once the competitor releases;
- intake carries its own disposition operation identity: an exact retry
  replays the committed decision, a conflicting one refuses either way;
- cleanup's `blocked-on-intake` refusal is durable to its own operation while
  a distinct cleanup operation may re-evaluate the moved boundary.

Added after the focused review of 2026-08-21T21:40:39Z:

- a settlement timeout cannot fire in the instant acceptance commits, and the
  claim-settlement deadline is neither the token deadline nor derived from it
  — past the token deadline the fixed claim is still authorized;
- a claim that already committed reconciles before the settlement deadline,
  because learning an outcome is not declaring one;
- a committed result under the same operation id with different claim operands
  is a collision: it refuses, leaves both records untouched, and never binds
  another participant's assignment to this offer;
- a retirement binds and reports the operands it settled, while every
  submitter still meets the retirement before any operand comparison.

Added after the focused review of 2026-08-21T21:48:06Z:

- a manager crash between the authority retirement and the offer row cannot
  let a later claim path relabel a timeout retirement, and the same holds in
  the other direction for a refusal-driven retirement met by a later timeout;
- a replayed retirement reports the reason its identity died of, to every
  submitter, rather than a message supplied by the path that found it.
