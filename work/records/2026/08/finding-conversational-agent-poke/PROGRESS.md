# Progress

**PLAN step 2 complete: the protocol proposal is in `PROPOSAL.md`, and W197 is
returned for review by `baton.claude` on 2026-08-18.** No implementation: the
plan says not to bury unresolved policy in code, so this step produced
decisions-in-the-open rather than a slice.

## Revalidation against the current authority

Read and run, not taken from the finding's description:

- the action projection has exactly three kinds today (`obligation`,
  `due_trial`, `work`), each with a stable `action_key`;
- `participant_actions` is defined as "the facts that may WAKE this exact
  member" — which is what a poke is, so a fourth kind fits without touching
  Work;
- `wait_actionable` creates no authority mutation of any kind, and a persistent
  poke does not change that: the `poke` verb writes, `wait` only reads;
- schema 20, projection 11.0 — both moved this week;
- the obligations table is the closest existing primitive and is exactly why
  poke must not be built on it: every column ties it to a Work.

## The finding the revalidation turned up

**A new action kind refuses the ENTIRE envelope in both runner bridges.** Their
validator throws on an unknown kind, so the whole `wait` result is rejected —
an agent would stop receiving its ordinary Work and obligation wakes, not
merely miss the poke. Proven by running the real validator:

    obligation alone     ACCEPTED
    poke alone           REFUSED: unknown action kind "poke" (poke:7)
    obligation + poke    REFUSED: unknown action kind "poke" (poke:7)

That is a live-outage shape rather than a compatibility footnote, and it is why
the proposal treats rollout order as protocol: widen both bridges to TOLERATE an
unknown kind first, ship that alone, and only then emit the new kind. That step
also decides the version question — with it, adding the kind is additive; without
it, W155's review standard applies and the major must move with every consumer
widened in the same candidate.

## The shape of the proposal

Each area answered with its reasoning, and the genuinely-ruler questions marked
rather than decided:

- **authorization** — any configured participant may poke any other; poke
  carries no workflow authority, so requiring a capability would make the
  friendly question harder to ask than the acts that change state;
- **timeout** — none in the authority. This instance times nothing on its own
  (`PICKUP_OVERDUE_SECONDS` is a projection reading; trial deadlines are
  operator inputs), and expiry would destroy the approved property that an
  offline participant may answer after reconnecting. An explicit optional
  `expires_at` is offered as the alternative;
- **retry/redelivery** — level-triggered, no new mechanism: a pending poke
  reappears on every `wait` until answered or cancelled, and consumers already
  dedupe on `action_key`;
- **cancellation** — an explicit verb for the asker and `config` holders;
  cancelling an answered poke refuses rather than rewriting history;
- **idempotency** — the existing `op-id=` protection, unchanged. The
  duplicate-poke question is deliberately separated from it;
- **rate limiting** — none, and a structural property instead: at most one
  pending poke per (asker, target). A rate limit is a timer; this achieves what
  the limit is for without measuring time.

Four questions are left explicitly for the ruler: self-poke, timeout,
pending-uniqueness, and the rollout order.

## Not done, deliberately

No schema, no verb, no projection change. PLAN steps 3–4 own slice A and its
telemetry shape; step 5 is its review gate; step 8 owns presentation. Producing
a slice now would have answered the four open questions by implementing one
arbitrary reading of each, which is precisely what step 2 forbids.

## Gate

Nothing to gate: no source changed. `just test-v11` remains green from the
preceding Work — **1609 passed**, serial **37**, ACP **41/41**.
