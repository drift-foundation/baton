# Progress

Implementer: `baton.claude`. Canonical Baton Work: W4303.

**State: awaiting review.** Plan items 4 and 5 are landed and verified;
the Work is passed back rather than closed.

## What landed

### Authority — the release contract (`src/baton_work/`)

- `config.py`: `CAPABILITIES` gains `recover`, deliberately beside
  `config` rather than inside it.
- `transitions.py`: new `_release_authority` returns the branch that
  authorized the release — `handler` (a resolved handler of the Work's
  own Route, self-release included) or `recover` (a member of the
  Work's OWNING team holding the capability). The refusal names both.
  `release_claim` takes a mandatory `episode` and compare-and-swaps
  `(work, assignment episode, claimant)` inside the write transaction,
  in that message order: unclaimed, then wrong claimant, then wrong
  episode. `_mint_episode` on success is what makes the fence
  single-use. The branch and the episode are journaled on the event
  payload and returned in the result.
- `cli.py`: `episode=` is a required int operand on `release`, and the
  verb help says what it fences.
- `projection.py`: `detail` publishes `episode_seq`, and
  `available_transitions` offers `release` to an owning-team `recover`
  holder as well as to a route handler — discovery, not
  discovery-by-attempt.

### Dispatcher — failed-turn settlement (`tools/codex-event-bridge/`)

- `event_bridge.mjs`: one `#settleTurn` used by BOTH completion
  orderings. A non-`completed` terminal status on a turn bound to an
  immutable delivery attempt re-reads the exact delivered
  `(participant, work, episode)` through the participant's own
  `wait timeout=0`. A surviving claim fences the target, publishes
  `failed(internal)` instead of `idle`, files one durable
  Work-correlated incident, and retains every queued wake. An
  unreadable or malformed read fails closed the same way.
  `#turnCompleted` no longer publishes `idle` before knowing, and holds
  the publication entirely while a `turn/start` is in flight.
- The fence is durable (`.settlement.json` beside the quarantine
  marker, same context key, same fail-closed `damaged` rule), restored
  before anything opens, re-published and re-filed on restart unless
  the marker durably says the incident already reached the authority,
  and cleared ONLY by a canonical read proving the claim is gone.
- `quarantine_store.mjs` grew a `suffix`/`label` option and a `clear`,
  so the two fences share one implementation. Only the settlement path
  calls `clear`; the approval quarantine still has no clearing path.
- Claimed-first delivery, both halves: `claimedFirst` in
  `codex_baton_bridge.mjs` promotes claimed Work in the forwarded set,
  and `EventBridge#admit` promotes a claimed action past unclaimed
  events already queued. `#dequeue` now removes by identity so a late
  promotion cannot make a settling caller drop the wrong event, and the
  in-flight or ambiguous head is never displaced.
- `claimed` rides structurally through `actionEvent` and
  `normalizeAction` as a boolean; a non-boolean refuses rather than
  coercing.
- `statusSnapshot` reports `orphan` beside `blocked` and `tainted`, and
  an orphaned target is not `deliverable` and not `ready`.

### v12 prototype (`v12/`)

`v12` drives the deployed v11 executable as a black box and calls
`release`, so it had to move with the contract: `BatonClient.release`
takes the episode and refuses without one, the manager carries
`attempt.episode` from the readiness action, and the local readiness
validator refuses a Work action with no `episode_seq` — that field is
now load-bearing for its compensation path.

### Docs

`docs/EFFECTIVE-BATON.md` (recovery section rewritten, including the
route-cannot-serve case), `docs/BATON-WORK.md`, and
`docs/AGENTS-MAILBOX-PROTO.md`. Every refusal and result quoted in the
guide was executed against a throwaway authority built from this tree.

## Verification

- `.venv/bin/python3 -m pytest -n $(nproc) -m "not serial" tests/work`
  → 2844 passed. `-m serial` → 52 passed.
- `tools/codex-event-bridge`: `node --test` → 263 passed.
- `tools/acp-baton-bridge`: `npm test` → 55 passed.
- `v12`: `npm test` → 159 passed.

New suites: `tests/work/test_w4303_release_recovery.py` (20 cases:
capability separation, both authorization branches and the negative,
cross-team ownership, journaling, the episode fence including the
same-participant re-claim successor, malformed operands committing
nothing, unclaimed/terminal, op-id replay and conflicting reuse,
discovery). `tools/codex-event-bridge/test/failed_turn_settlement.test.mjs`
(18 cases: fail-after-claim, fail-before-claim, success never
reconciled, unreadable/malformed reads, retention, the
completion-before-start ordering, interactive turns, structured
correlation, a later episode not being this orphan, the uncorrelated
`held` case, fence lifting only on canonical evidence, durability and
restart, unacknowledged and damaged markers, duplicate completion,
claimed-first partitioning, late promotion, and in-flight head
protection). Three W4303 cases appended to
`test/runtime_publisher.test.mjs`.

Existing suites touched only where the ruled contract changed: every
`release` call site gained its episode (via a new `fx.episode_of` test
helper), and two exhaustive expectations were EXTENDED additively — the
producer action block now carries `claimed`, and the status row now
carries `orphan`.

## Not done, on purpose

- **No automatic release.** The ruling permits one only under an
  explicit configured rule; none is ruled, so none was invented. Plan
  item 7 carries the open decision.
- **No `recover` grant in any live configuration.** That is an operator
  act on `baton.json` plus a generation acceptance. Plan item 8.
- **I5 / the managed socket-bearing test gate** is a reviewer
  prerequisite (plan item 3a), untouched here. No `node` execution
  policy was broadened.

## Review notes

The four decisions this implementation had to make beyond the pinned
ruling — ownership bounding `recover`, publishing `episode_seq` on
`detail`, holding rather than correcting the `idle`, and the
four-valued reconciliation answer — are written into `FINDING.md` under
"Implementation revalidation — 2026-08-22" with their reasoning, and
are the parts most worth a second opinion.

## Round 2 — the reconnect settlement gap (2026-08-22)

`review-2026-08-22T14-46-33Z.md`, one P1. Reproduced against the tree before
any edit; the review is right. Evidence:
`evidence/correction-reconnect-2026-08-22.txt`.

### What I had wrong

Round 1's own note says the correction is "one shared `#settleTurn` used by
both completion orderings" and lists them as the complete set. They are the
two orderings in which a completion NOTIFICATION arrives — not the two ways a
terminal managed turn is first OBSERVED. Reconnect reconciliation exists
precisely because notifications can be missed, so the resume snapshot is an
ordinary third observation point. I got the routine right and then called it
from an incomplete set of sites, which is not a defect a better routine fixes.

### Changed

`#settleTurn` now runs at four more places, all in
`tools/codex-event-bridge/src/event_bridge.mjs`:

- `#reconcileTarget`, persisted turn terminal — the reported P1;
- `#reconcileTarget`, an ambiguous `turn/start` resolved against the resume
  snapshot as already ended;
- `#reconcileAmbiguous` from `#drain`, the same resolution reached through a
  later `readThread` when resume did not carry the delivery;
- `#reconcileTarget`, an accepted turn ABSENT from an idle thread.

Settlement runs before `activeTurn` is cleared, so a throw inside it leaves
the attempt in flight rather than clearing it unreconciled. `#drain` already
refuses to deliver on a fenced target, so nothing else needed to move.

### Found while correcting, not in the review

The last three sites above. Each bound the delivery and then dropped it —
same terminal turn, same surviving claim, same orphan, different route — so
correcting only the reported one would have left the fence depending on which
reconciliation happened to look first.

The absent-turn case deserves its own sentence because the review asked to
preserve that boundary, and it is preserved: the turn is not replayed, and a
regression asserts the delivery is not re-sent. What the boundary is about is
whether to re-run a turn whose fate is unknown. The claim is a different
question with a canonical answer — the branch only fires on an idle thread, so
nothing is executing the delivery — and settlement returns without fencing in
the ordinary case where the claim is already gone.

### Tests — 7 new cases (41 in the file, 279 in the suite)

The reviewer's regression, plus: a successful turn found on reconnect is not
fenced AND costs no canonical read; a failed turn on reconnect whose claim is
gone is not fenced; a late `turn/completed` after resume settlement files
nothing twice; the resume-ambiguous path; the drain-ambiguous path; the absent
turn with a surviving claim; the absent turn with the claim gone.

Each of the four new call sites was removed independently and fails exactly
the case that names it, and no other. Restored: 41/41.

### Verification

- `tools/codex-event-bridge npm test` — 279 tests, 0 failures (272 before).
- `pytest -n auto -m "not serial" tests/work` — 2850 passed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/acp-baton-bridge npm test` — 55. `v12 npm test` — 161.
- Whitespace-damage check clean.

### Not changed

`v12` consumes the release contract (mandatory `episode=` fencing in
`v12/src/baton_cli.mjs`, the offer episode in `v12/src/manager.mjs`) and has
no dispatcher resume path of its own, so it does not move with this
correction. Checked rather than assumed.

Plan items 3a, 7 and 8 are untouched: the socket-bearing managed gate is
still a reviewer prerequisite, no automatic release was invented, and no
`recover` grant was made in any live configuration.

### State

**Awaiting re-review.**

## Round 3 — the concurrent publication race (2026-08-22)

`review-2026-08-22T15-23-14Z.md`, one P2. Reproduced before any edit; the
review is right. Evidence: `evidence/correction-concurrent-2026-08-22.txt`.

### What I had wrong, and where it came from

`incidentFiled` is the durable acknowledgement and becomes true only after the
awaited publication returns. Two observers of one fence can both read it false
and both publish, and the authority counts one failed turn twice.

**The window is round 2's own consequence.** Routing the resume path through
the shared settlement is what made reconnect and a late `turn/completed`
overlap naturally; before that they could not observe one fence concurrently.
The sequential late-notification case I added in the same round runs only
after the first settlement has acknowledged, so it could never have witnessed
this. A correction that merges two paths inherits the concurrency of both —
that is the lesson, not "races are hard".

### Changed

- A second observer JOINS the in-flight publication: the promise is held on
  the orphan and awaited by anyone else who arrives.
- The handle is dropped unless the acknowledgement made it durable, so a
  refused or failed publication stays retryable. Without this half the fix
  would have replaced double-filing with never-filing.

### Found while correcting, not in the report

A rejecting runner took the whole settlement path down with it — out of
`#settleTurn`, out of `#turnCompleted`, into an unhandled rejection — so the
incident was neither filed nor retried and, in the notification path, the rest
of the handler never ran. A throw is now a failed publication rather than a
failed settlement: logged, answered `false`, retried. The fence is already
durable when this happens, so nothing is lost.

### Tests — 2 new cases (44 in the file, 288 in the suite)

The reviewer's concurrent regression is retained beside the sequential
late-replay case, as the review requires. The two new ones cover the
retryable half: a publication the runner REFUSES, and one that THROWS.

Mutation-checked in both directions: removing the join fails exactly the
concurrent case; removing the handle-clearing fails exactly the two
retryability cases. Neither half is unwitnessed.

### Verification

- `tools/codex-event-bridge npm test` — **288 pass, 0 fail**. The suite is
  fully green for the first time since this Work opened; the failure other
  Works have been reporting as "W4303's reviewer regression" was this defect.
- `pytest -n auto -m "not serial" tests/work` — 2883 passed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/acp-baton-bridge npm test` — 55. `v12 npm test` — 186.
- Whitespace-damage check clean.

### Unchanged

No automatic release was invented; the socket-bearing managed gate and the
live `recover` grant remain operator actions (plan items 3a and 8).

### State

**Awaiting re-review.**

## Round 4 — the successor acknowledgement (2026-08-22)

`review-2026-08-22T16-54-56Z.md`, one P1. Reproduced before any edit; the
review is right. Evidence:
`evidence/correction-successor-ack-2026-08-22.txt`.

### What I had wrong

Round 3 bound the JOIN to the orphan object and left the ACKNOWLEDGEMENT
reading `state.orphan` — the same identity mistake, in the same routine, one
line apart. A publication belongs to the fence it captured; after an await the
live state need not still name that fence.

My round-3 regressions could not see it: they hold one fence and race two
observers of it, never a fence REPLACED while a publication is in flight.

### Changed

- `#acknowledgeOrphanIncident(state, orphan)` takes the exact orphan whose
  publication returned, and sets the in-memory flag on that captured object.
- The durable marker is written only while `state.orphan` is still that
  object, so a late publication cannot overwrite a successor's marker.

### The durable half needed a regression of its own

Mutation-checking showed the reviewer's case witnesses only the in-memory
flag — removing the durable guard left the suite green. The new case reads the
settlement marker off disk and asserts it still describes the successor with
`incidentFiled` false, which is the state a restart actually trusts. An
unwitnessed guard is one the next correction deletes.

Both halves now fail exactly the case that names them.

### Verification

- `tools/codex-event-bridge npm test` — **290 pass, 0 fail**.
- `pytest -m serial tests/work` — 52 passed.
- `pytest -n auto -m "not serial" tests/work` — 2902 passed, **2 failed**, and
  both are W4996's: reviewer-added cases in
  `test_w4996_dependency_graph.py` against `src/baton_work/tui/graph.py`,
  which is Python and shares nothing with `event_bridge.mjs`. W4996 is queued
  on `baton.impl` awaiting its own turn and was deliberately not touched from
  here.

### State

**Awaiting re-review.**

## Round 5 — signed off, revalidated, handed to the approver (2026-08-22)

`review-2026-08-22T17-16-24Z.md` **signed off** the round-4 correction and
returned the Work to `baton.impl`. Nothing was implemented this turn. What I
did was revalidate the signed-off state against the tree as it now stands and
hand the two remaining items to the participant who owns them.

### Revalidated against the current tree

The tree has moved since the sign-off — W2845, W4615, W4996 and W2929 all
landed changes in the interval — so the sign-off was re-measured rather than
assumed:

- `tools/codex-event-bridge npm test` — **297 pass, 0 fail** (290 at sign-off;
  the seven additional cases are W2845's, in `policy_syntax.test.mjs`).
- `tests/work/test_w4303_release_recovery.py` — **20 passed**, unchanged.

### One cross-Work interaction, checked deliberately

W4615 landed managed-dispatch drain in the same `transitions.py` this Work's
`release_claim` lives in, so the two were read together rather than assumed
independent. They compose correctly, and in the direction that matters:

- drain refuses **claim admission** only; `release_claim` is untouched by
  dispatch mode, so an orphaned claim can still be recovered while the
  deployment is draining or paused.
- W4615 derives its drain blockers from **live assignments**, and an orphaned
  claim from a failed managed turn is exactly such an assignment. It will
  never clear on its own, so a drain would wait on it forever.

That makes this Work's `recover` release the thing that unblocks a drain
stuck on an orphan. Recorded because it is an argument for plan item 8 that
did not exist when item 8 was written: the grant is no longer only about
recovering one claim, it is what lets a maintenance drain finish.

### What remains, and why it is not mine

- **Plan item 7** — whether a configured automatic release/retry rule should
  exist beside the incident path. The ruling PERMITS one and does not require
  it; the shipped default is fence + durable incident + operator recovery.
  Deliberately not invented: no configuration surface for automatic release
  was created, because inventing one would put claim destruction behind an
  unreviewed key.
- **Plan item 8** — granting `recover` in the live `baton.json` and accepting
  the generation. Verified still undone: the deployment's configuration grants
  `recover` to nobody, so the ordinary Route-handler branch is what is live
  and forced recovery is currently unavailable to any participant.
- **Plan item 3a's remainder** — dismissing incident I5 is the configured
  action owner's separate incident act.

All three are approver/operator acts. Implementation and independent review
are both complete.

### State

**Passed to `baton.ops` for the approver.** Not closed: closing is not the
implementer's act, and two of the three remaining items are decisions rather
than work.
