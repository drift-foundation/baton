# ACP turn teardown can strand a claim beside a live worker

Work: W55705
Observed on: W51487 assignment episode 55530
Prior related correction: retired-authority W4303,
`work/records/2026/08/finding-managed-turn-failure-orphans-claim/`

## 2026-08-31 — observed recurrence on the ACP path

`baton.claude` claimed W51487 and launched retained dogfood attempt
`attempt-w51487-run7`. The provider turn began and the managed agent reported
that it would wait for terminal evidence. The ACP delivery then ended with:

```text
acp process domain torn down after delivering
work:2b077949-W51487:55530:g4
```

Canonical state still records W51487 as `active`, Handler `baton.claude`,
episode 55530. Runtime facts instead report the participant `idle`, with no
Work and no failure cause. No managed-turn incident was filed.

The delegated runtime also survived the ACP process-domain teardown. Host
process evidence shows container shim
`afed4c76aebe339911ab353021227f94cb8c635e9b46ed1e4ba2f642f4d7d334`
and uid-65532 process `python3 /opt/baton/dogfood_entry.py` still alive roughly
29 minutes later, with no provider child. `/tmp/w51487/run7/` contains the
authority, control store, launch record, grants and task, but no terminal
`evidence.json`; `run7.out` stops after `== operator ==`.

This is not ordinary slow Work. The participant's one claim slot is occupied,
the runtime advertises free capacity, the delegated worker has no supervising
agent turn, and neither Baton nor the TUI exposes an incident requiring
recovery.

## Confirmed defect

The v11 managed-turn orphan correction does not cover this ACP completion
path. A normally ended ACP delivery may leave all three facts contradictory:

- canonical Work remains claimed;
- participant runtime is published as idle;
- a delegated container remains live without a supervising turn.

The absence of an incident makes the state less actionable than the Codex
dispatcher failure path already corrected under the prior W4303 record.

## Immediate recovery boundary

Do not release episode 55530 while the delegated container is still live.
First identify and stop that exact runtime, preserving `/tmp/w51487/run7/` for
inspection. Because no clean terminal evidence exists, any partial output is
untrusted and must not be accepted automatically. After runtime absence is
proved, an authorized recovery participant may release exactly W51487,
expected Handler `baton.claude`, episode 55530, with an attributable reason.

This recovery is a stopgap, not the fix.

## Required correction

At every ACP delivery ending, re-read canonical participant state before
publishing idle or accepting another delivery. If the delivered assignment is
still claimed by that participant at the same episode:

1. publish runtime `failed`, never `idle`;
2. file one sticky incident naming Work, participant, action key and episode;
3. retain later readiness instead of spending another turn;
4. report any known delegated-runtime locator without assuming that an ended
   agent process also ended an external container;
5. require explicit fenced recovery unless a separately approved runtime
   policy owns automatic termination and release.

The bridge must not infer that a live container means useful progress, nor
that an ended ACP turn means the container is absent.

### Approved scheduling refinement — 2026-08-31

This ruling supersedes the blanket readiness-retention rule in Required
correction item 3 and the corresponding blanket retention in Required ordering
item 4. A surviving claim does not by itself determine whether the delivered
action may be offered again:

- when the recovery prompt FAILED before returning, its wake is unspent and
  remains eligible for redelivery to the same participant and assignment
  episode;
- when the prompt RETURNED while the exact claim survived, that action was
  presented and is not replayed solely because the claim remains;
- secondary, held, unreadable, and authority-drifted claim-slot states remain
  stranded and retain readiness until canonical recovery.

Every surviving-claim path still withholds `idle`, publishes `failed`, and
owes the one durable actionable incident. Redelivery is recovery of an
unspent wake, never evidence that the surviving claim is healthy and never an
automatic claim release, acceptance, or transfer.

## Acceptance

- An ACP turn ending before claim leaves no Handler and may report idle.
- An ACP turn ending after claim cannot publish idle while the claim survives.
- The exact surviving Work and episode produce one durable actionable
  incident.
- A detached or escaped delegated runtime is reported independently from the
  agent turn and cannot disappear from the recovery account.
- Later wakes remain retained until the exact claim is reconciled.
- Exact runtime stop plus exact claim release restores capacity without
  accepting partial output or releasing a newer episode.
- Tests cover normal completion, provider failure, transport loss, detached
  runtime survival and duplicate terminal notification.

## 2026-08-31 — reviewer research

### Confirmed code path

`tools/acp-baton-bridge/src/acp_baton_bridge.mjs::runBridge` has no
post-turn canonical settlement. Its successful-delivery path currently does,
in order:

1. `live.promptText(...)` returns;
2. `settleDomain(...)` proves the ACP agent process exited;
3. `runtime.state("idle")` advertises free capacity; and
4. `memory.markPresented(...)` suppresses the just-spent offer until its
   retry deadline.

Neither `settleDomain` nor `ReadinessOffers` reads the participant's canonical
claim slot. The ordinary exception path also tears the process domain down and
publishes `failed`, but it neither persists a claim fence nor files a durable
incident. `DomainTeardownError` fences the in-process delivery lane and exits,
but that fence is not restart-durable and also does not account for a surviving
canonical claim.

The distinction is important: an ACP prompt returning is a transport fact, not
a Baton terminal result. Unlike the Codex event bridge, this adapter receives
no semantic `turn/completed` status that proves the model passed or closed its
Work. Therefore the canonical claim reconciliation is required after every ACP
turn outcome, including a normally returned prompt, not only after caught
provider or transport errors.

`tools/acp-baton-bridge/src/baton_readiness.mjs::episodeStillLive` is only the
pre-turn stale-offer check. It narrows a race before delivery and cannot answer
what the model did after the turn began. It must not be treated as settlement.

### Confirmed precedent and reusable boundary

The sibling implementation under
`work/records/2026/08/finding-managed-turn-failure-orphans-claim/` already
defines the safety contract. In
`tools/codex-event-bridge/src/event_bridge.mjs`, the W4303 settlement:

- performs a canonical participant-relative `wait timeout=0` read;
- distinguishes the exact delivered claim, a different secondary claim, an
  occupied but weakly correlated claim, a released slot, and an unreadable
  answer;
- treats unreadable as fenced rather than as released;
- commits a durable `.settlement.json` marker before asynchronous incident
  publication;
- joins concurrent publication, retries a refused or thrown publication, and
  durably acknowledges only the exact fence whose publication succeeded;
- restores the marker before admitting new delivery; and
- clears it only after a later canonical read proves the participant has no
  claim.

`tools/codex-event-bridge/src/quarantine_store.mjs::QuarantineStore` was made
generic for this use and can back an ACP-specific settlement marker. Reusing
that store is lower risk than adding another persistence format. The Codex
`EventBridge` settlement itself is coupled to per-target thread state, so a
small ACP settlement owner should reuse the store and the proven state machine
rather than copying private methods or forcing a broad dispatcher refactor.

**Proposed key:** the ACP fence belongs to the canonical participant claim
slot, not to the short-lived agent process or its replaceable ACP session.
Persist it below the configured `stateDir`, keyed by the accepted participant,
and record the authority UUID returned by the canonical read. A restart must
restore it before the first `idle` publication or delivery. An authority UUID
mismatch is configuration drift and must fail closed; it is not evidence that
the old claim was released.

### Required ordering and state behavior

For a delivered action whose ACP domain can be proved gone, the safe order is:

1. destroy and prove the per-turn ACP process domain gone, preserving W28681;
2. read the participant's canonical claim slot with `wait timeout=0`;
3. if no claim is held, publish `idle` and then mark the offer presented;
4. if the exact claim, a secondary claim, or an unreadable result remains,
   synchronously persist the fence, publish `failed`, file/retry one sticky
   incident, retain the offer and all later readiness, and reconcile on a
   bounded cadence until a canonical read proves the slot released.

A process-domain teardown failure is a separate, stronger fence. Claim
settlement must not clear it or imply that the process is gone. Conversely,
proving the ACP process domain gone does not settle the Baton claim.

The fence must be committed before awaiting incident publication. Duplicate
observations, a restart, and a late publication acknowledgement must retain the
W4303 guarantees: one incident per exact fence, no acknowledgement transferred
to a successor fence, and retry after `incident()` returns false or throws.

### Incident ownership prerequisite

**Observed:** the W51487 runtime projection inspected during recovery carried
`action_owner: null`. ACP configuration currently treats
`runtime.actionOwner` as optional, while
`RuntimePublisher.incident()` deliberately refuses an ownerless incident and
returns false. The required sticky incident therefore cannot be satisfied by
the affected deployment as configured.

**Proposed:** for a managed ACP bridge governed by this settlement contract,
make `runtime.actionOwner` mandatory and refuse startup before the runtime
lease or first wait when it is absent. Do not infer an owner from the runner
participant. If optional ownership must remain a supported product mode, an
explicit alternative durable incident owner and its authority contract are an
open decision; silently running without either is not compatible with this
finding's acceptance boundary.

**Approved 2026-08-31:** `runtime.actionOwner` is mandatory for every managed
ACP bridge governed by this settlement contract. The bridge must refuse
startup before publishing a runtime lease or arming its first wait when the
owner is absent or unresolved. The owner is an explicitly configured,
authorized recovery/operations participant and is never inferred from the
runner participant, session, Route, or runtime telemetry. An ownerless bridge
is outside this managed contract, not a supported degraded mode.

### External delegated runtime boundary

The W28681 domain owns the ACP agent subprocess and descendants contained by
the configured PID namespace. A container created through the Docker daemon is
not in that process domain. Run7 is direct evidence: the ACP domain ended while
`python3 /opt/baton/dogfood_entry.py` remained alive in the delegated
container.

The bridge has no current structured source for a delegated container ID and
must not scrape model prose, tool arguments, logs, or environment values for
one. An incident may include a locator only when a trusted deployment
integration supplies it. Otherwise it must state that delegated-runtime
absence is unproved and external cleanup may still be required. This Work does
not authorize automatic container termination, credential revocation, partial
output acceptance, or claim release.

Queued Work W55758, *An interrupted dogfood attempt strands a runtime and a
live credential*, owns the broader interrupted-attempt runtime/credential
recovery problem. W55705 owns the ACP participant's post-turn claim settlement
and the truthful runtime/incident projection; the two must cross-reference
without duplicating automatic recovery policy.

### Regression boundary

Add focused cases that drive the canonical reconciliation rather than merely
asserting runtime state calls:

- prompt returns with no claim: domain gone, then `idle`, then presented;
- prompt returns with the exact Work/episode still claimed: durable fence,
  one `failed` plus one incident, no `idle`, no presented acknowledgement;
- provider failure and transport loss with a surviving claim take the same
  settlement path;
- a different secondary claim occupies the slot, including a newer episode of
  the same Work, and cannot be mistaken for release;
- malformed output, execution failure, and authority UUID mismatch fail
  closed;
- later readiness is retained while fenced and drains only after a canonical
  released answer, except that an exact claimed-Work recovery prompt that
  failed before returning remains eligible for redelivery under the approved
  scheduling refinement above;
- restart restores a well-formed marker before wait/idle, a damaged marker
  remains fenced with preserved evidence, and exact release clears it;
- duplicate/overlapping terminal observations file once, publication false or
  throw remains retryable, and a late acknowledgement cannot mark a successor
  fence filed;
- an external sentinel representing a daemon-owned runtime survives ACP-domain
  teardown; the bridge neither kills it nor reports it absent and the incident
  names the locator only when the fixture supplies one; and
- process-domain teardown failure composes with claim settlement without
  either fence clearing the other.

Baseline before implementation: `npm test` in
`tools/acp-baton-bridge/` passed all 89 tests. The focused sibling command
`node --test test/failed_turn_settlement.test.mjs` in
`tools/codex-event-bridge/` also passed.

## 2026-09-01 — the regression boundary is superseded to match the refinement

The approved scheduling refinement above supersedes *Required correction* item
3 and *Required ordering* item 4 by name. It also contradicts the second
bullet of **Regression boundary**, which still reads:

> prompt returns with the exact Work/episode still claimed: durable fence,
> one `failed` plus one incident, no `idle`, **no presented acknowledgement**

**Superseded.** A returned prompt whose exact claim survives IS marked
presented: the wake was spent, the action was presented, and the refinement
says such an action is not replayed solely because the claim remains. The
durable fence, the single `failed`, the one incident and the withheld `idle`
all stand unchanged; only the acknowledgement clause moves.

The unspent case keeps the original behaviour and is now the *failed*-prompt
bullet: a recovery prompt that failed before returning is not acknowledged and
is delivered again.

Recorded rather than silently implemented, because two live rules that
contradict each other are worse than either alone.

## 2026-09-01 — implementation note on the ledger record

The approver ruling for the scheduling refinement is pinned above and dated
2026-08-31. On the Baton ledger the corresponding obligation (message seq
58475, owed by `baton.decide`) is still **pending**, and `PLAN.md` item 8 cites
M58475 as the approval when M58475 is the message that *requested* it. The
repository record is what implementation followed, per this repository's
pinned-decision rule; the ledger obligation still needs an explicit
`respond`/`dispose` so the two accounts agree. Reported rather than corrected:
discharging another participant's obligation is not the implementer's act.

## 2026-09-01 — reviewer correction to the ledger note

**Superseded:** the implementation note immediately above says obligation
M58475 is still pending. Canonical W55705 detail at snapshot 58706 reports
that obligation as `responded`, with `resolved_seq: 58545`; message M58545 is
the approver response that confirms the scheduling split. The repository
ruling and the ledger now agree, and no obligation disposal remains for this
decision.

## 2026-09-01 — the recoverable exception is exactly one action wide

The approved scheduling refinement above says an exact claimed-Work recovery
prompt that FAILED remains eligible for redelivery. The return review
(`review-2026-09-01T05-03-30Z.md` [P1]) establishes how narrow that is, and it
is recorded here because the implementation first read it as an envelope-wide
permission:

- **the exception is one ACTION wide**, not one authority wide. The same
  ledger answering is not proof that the next action is the exact unspent
  recovery wake for the same participant and assignment episode;
- **a same-authority successor claim and a neighbouring wake stay retained**
  until the exact claim is reconciled, which is what this record's own
  acceptance already said;
- **a successor is recorded through reconciliation BEFORE a turn is spent**,
  never discovered by spending one.

**Consequential supersession, flagged for acceptance.** W11910's accepted case
`non-Work actions beside a deferred Work keep their own delivery rule`
asserted that a poke is delivered beside a claimed Work. Its underlying
property is untouched — the one-claim Work slot governs Work offers and
nothing else — but delivering a claimed recovery wake mints a settlement fence,
and the rule above then retains the poke through that SECOND gate. The case's
prompt count therefore moves from two to one, with the poke retained rather
than withdrawn and delivered again once a canonical read says the slot is
free. The implementer changed the expectation rather than the rule, recorded
it in the test itself, and it is the reviewer's to accept or overrule.

## 2026-09-01 — exact neighboring-wake assertion supersession approved

Baton response M59062 approves the consequential supersession above. In the
existing test `non-Work actions beside a deferred Work keep their own delivery
rule`, the current expected prompt count is one after the claimed recovery
wake strands post-turn settlement, not two.

This **supersedes** only the old same-envelope prompt-count expectation. The
claim-slot rule is unchanged: a claimed Work does not itself defer non-Work
actions. The later settlement fence is the distinct gate that retains the
poke beside a known orphaned claim. The poke remains unspent and is delivered
after a canonical read proves claim release.
