# W197 protocol proposal — the conversational poke

PLAN step 2, by `baton.claude`. This is the explicit proposal the plan asks
for, covering authorization, timeout, retry/redelivery, cancellation,
idempotency and rate limiting. Nothing here is implemented: the plan says not
to bury unresolved policy in code, so each question is answered in the open
with its reasoning, and the ones that are genuinely the ruler's are marked.

## Revalidation against the current authority

Confirmed by reading and running the current tree, not from the finding's
description of it:

- **The action projection has exactly three kinds today** — `obligation`,
  `due_trial`, `work` — each with a stable `action_key` (`obligation:<seq>`,
  `trial:<work>:<trial>:<generation>`, `work:<id>:<episode>:g<generation>`).
  `participant_actions` is documented as "the facts that may WAKE this exact
  member", which is exactly what a poke is; a fourth kind fits the definition
  without touching Work.
- **`wait_actionable` is strictly read-only** — "creates no claim, timer row,
  audit act, or any other authority mutation". A persistent poke does not
  change that: the row is written by the `poke` verb, and `wait` only reads it.
- **Schema is 20; projection is 11.0.** Both moved this week (W78's typed gate,
  W155's three-level window).
- **The obligations table is the closest existing primitive**, and is the
  reason poke should NOT be built on it: every column ties it to a Work
  (`work NOT NULL`, `message_seq`, `thread`). A poke has no Work, which is the
  whole point.

### The decisive fact the plan did not anticipate

**A new action kind refuses the entire envelope in both runner bridges, not
just the unknown entry.** Their validator ends with:

    } else {
      throw new Error(`unknown action kind ${JSON.stringify(action?.kind)}`);
    }

Run against the current code with a real envelope:

    obligation alone     ACCEPTED
    poke alone           REFUSED: unknown action kind "poke" (poke:7)
    obligation + poke    REFUSED: unknown action kind "poke" (poke:7)

So the moment the authority emits a poke, a running agent stops receiving its
ordinary Work and obligation wakes as well. This is not a cosmetic
compatibility note — it is a live-outage shape, and it is why §7 below proposes
the rollout order as part of the protocol rather than as a deployment detail.

## 1. Authorization — who may poke whom

**Proposed:** any configured participant may poke any other configured
participant in the same instance. The target is exactly one `team.member`,
never a route, never a wildcard, as the approved contract already pins.

Reasoning: poke carries no workflow authority — it cannot claim, pass, close,
re-phase or make Work actionable — so the Route-eligibility gate that protects
mutations has nothing to protect here. Requiring a capability would make the
friendly status question harder to ask than the acts that actually change
state, which inverts the risk.

The audited record names the asker, so a misuse pattern is visible rather than
prevented by refusal.

**Open for the ruler:** whether a participant may poke *itself*. I propose
allowing it — it is harmless, and it gives a runner a way to prove its own
answer path end to end — but it is a judgement about noise, not correctness.

## 2. Timeout — when an unanswered poke stops waiting

**Proposed:** a poke carries no authority-enforced deadline. It has three
terminal states — `answered`, `cancelled`, and *nothing else* — plus a derived
presentation age.

Reasoning: this instance's precedent is that the authority times nothing on its
own. `PICKUP_OVERDUE_SECONDS` is a projection-side reading of an instant, not a
scheduled transition; trial `review_at` deadlines are explicit operator inputs.
Introducing the first background expiry in the authority for a conversational
primitive would be the largest change in this Work and the least justified.

A poke that is never answered is a fact about the deployment. The operator sees
its age and can cancel it (§4). Automatic expiry would also destroy the
approved property that "an offline participant may answer after reconnecting".

**Alternative if the ruler prefers a deadline:** an explicit optional
`expires_at` operand on `poke`, defaulting to none, evaluated in the projection
exactly as `due_trial` evaluates `review_at`. That keeps the authority free of
schedulers while giving the operator the option per poke.

## 3. Retry and redelivery

**Proposed:** redelivery is level-triggered and needs no new mechanism. A
pending poke appears in `participant_actions` on every `wait` until it is
answered or cancelled — the same way an obligation does. A runner that restarts,
reconnects, or simply polls again sees it again.

The `action_key` is `poke:<seq>`. The sequence is the poke's identity and never
changes, so repeated delivery is inherently idempotent for the consumer, which
already dedupes on `action_key`.

Deliberately NOT proposed: a delivery counter, a redelivery timer, or an
acknowledgement distinct from the answer. The approved contract's "repeated
delivery is idempotent" is satisfied by level-triggering alone, and each of
those additions would be a piece of scheduler state the authority does not
otherwise keep.

## 4. Cancellation

**Proposed:** `poke-cancel poke=<seq>` terminally closes an unanswered poke,
permitted to the asker and to any participant holding the `config` capability.
A cancelled poke leaves the action projection immediately. Cancelling an
already-answered poke refuses by name rather than rewriting history.

Reasoning: the asker owns the question and may withdraw it; the operator needs
a way to clear a poke aimed at a participant that will never return. Both are
recorded, so "why did this poke vanish" is answerable.

## 5. Idempotency

**Proposed:** `poke` accepts the existing `op-id=` protection unchanged, with
the fingerprint over the effective operands (target participant, request text).
An exact retry replays the one committed poke rather than creating a second.

This is the established mechanism for every mutation in this authority
(`_operation`), and poke should not invent a second idempotency story.

**Separately — the duplicate-poke question, which is not idempotency.** Two
*deliberate* pokes to the same participant, minutes apart, are two questions and
should both exist. I propose no uniqueness constraint. §6 covers the volume
concern, which is the real one.

## 6. Rate limiting

**Proposed:** no authority-enforced rate limit, and one structural property
instead: **at most one poke per (asker, target) may be pending at a time.** A
second poke from the same asker to a target that already has one pending from
them refuses by name and points at the pending seq.

Reasoning: a rate limit is a timer, and §2 argues against putting the first
timer in the authority for this feature. The pending-uniqueness rule achieves
what rate limiting is actually for here — it makes "poke storms" structurally
impossible from any one asker — without measuring time at all. It also matches
the conversational intent: you do not ask the same person "what's up?" three
times before they answer.

Different askers may each have one pending poke to the same target, because
they are different people asking.

**Open for the ruler:** whether that is too strict when a poke is genuinely
stale (the target has been offline for hours and the asker wants to re-ask with
new text). My answer is that cancelling and re-poking is the honest sequence and
leaves a truthful record, but the ruler may prefer plain allowance.

## 7. Rollout order — required by the compatibility fact above

**Proposed, and I believe this is protocol rather than deployment:**

1. Widen both runner bridges to *tolerate* an unknown action kind — ignore the
   entry, keep the envelope, and report the unknown kind as a diagnostic. Ship
   and deploy that first, as its own change, with no authority change beside it.
2. Only then add the `poke` kind to the projection.

Reasoning: today an unknown kind is a hard refusal, so the authority and every
runner must move in lockstep or agents go dark. Step 1 removes the lockstep
permanently — it is the difference between "old consumers ignore what they do
not understand" and "old consumers break". Every future action kind benefits.

This also decides the version question. With step 1 shipped first, adding the
kind is **additive** and the projection minor moves. Without it, adding the kind
is breaking and the major must move — and W155's review established the
standard clearly: if a consumer would silently misread or refuse, the major
moves and every consumer is widened in the same candidate.

## What I am NOT proposing, and why

- **No `poke` fields on Work, Messages, or Events.** The contract says poke
  state stays outside both, and the invariant is easier to keep if the poke
  table simply has no Work column to fill in.
- **No provider/telemetry schema yet.** PLAN step 4 owns it, and the shape
  should follow the two runner adapters' real capabilities rather than lead
  them.
- **No TUI presentation.** PLAN step 8, explicitly after the JSON contract and
  live runner behaviour are stable.

## Decisions I need before slice A

1. Self-poke: allowed or refused? (§1)
2. Timeout: none, or optional explicit `expires_at`? (§2)
3. Pending-uniqueness per (asker, target): accept, or allow duplicates? (§6)
4. Rollout order: accept step-1-first, which makes this additive? (§7)

Everything else above I am prepared to implement as proposed, under the
ordinary review gate at PLAN step 5.
