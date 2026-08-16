# WS-3 design/options — atomic provider deduplication

Author: `baton.implementer`
Date: 2026-08-15
Responding to: `58cb118d68f5c4b530a143296dd8294a` (design/ruling only)
No source or test edits made.

## The gap, restated against today's authority

WF-04/WF-05 currently do acceptance in three separate transactions: the
provider creates (or picks) LANG-42; the CONSUMER's handler adds
`PUSH-1 blocked_by LANG-42`; the provider responds to the `@` obligation
naming LANG-42. Any crash/refusal window between them leaves context
without the gate or a gate without its explanation — exactly the observed
defect class WS-2's in-lock discipline eliminated elsewhere.

## D1 — THE central product choice: who may commit the edge

Under the pinned R1 matrix, changing a Work's dependencies belongs to the
handler of THAT Work's Current — the consumer. Acceptance is a provider
act. One of these must bend, and this is not mechanical:

- **Option A (RECOMMENDED) — a request-scoped authority grant.** A pending
  exact `@` response obligation authorizes the live handler of its named
  route to perform ONE atomic acceptance that gates exactly the REQUESTING
  Work — nothing else, nothing twice, and only while the obligation is
  pending. Rationale: by addressing the request, the consumer's handler
  already solicited the provider's decision about this exact report; the
  edge is the answer arriving in executable form. The grant dies with the
  obligation (answered, disposed, withdrawn, or consumer closed), so it is
  narrower than any standing delegation the delegation ruling rejected.
- **Option B — provider proposes, consumer confirms.** No matrix change,
  but the confirm is a second transaction: the WS-3 defect window returns
  by construction. Honest, and inadequate — listed to be rejected
  explicitly.
- **Option C — consumer-side atomic adopt.** The consumer cannot know or
  create the right provider Work; the association decision is provider
  knowledge. Rejected.

Option A requires Slawomir's ruling because it adds the one narrow
exception to "participation never substitutes for ownership": here the
authority flows from the obligation the OWNER created, not from
participation.

## D2 — the honest association without WS-4

WS-4 first-class discussions and `#WORK` labels do not exist, and this
design does not smuggle them. The committed association is the triple that
already lives in today's model:

1. the obligation row (consumer Work ↔ provider route, with its C4
   resolution snapshot), reaching a terminal state that NAMES the provider
   Work;
2. the single `accept` audit act carrying both resolutions, the rationale,
   and both Work ids; and
3. the dependency edge, extended with ONE narrow provenance column —
   `edges.via_obligation INTEGER NULL` — so the projection can answer
   "why does this gate exist" by pointing at the exact request it
   answered.

`via_obligation` is edge provenance, not a reusable relation: it cannot
attach discussions to multiple Works, cannot label, cannot exist without
its edge, and is NULL for plain `block` edges. WS-4 remains whole and
unconstrained. **Sequencing verdict: WS-3 is honestly representable today;
no reorder or scope correction is needed.**

## D3 — the operation

One verb, two forms, one transaction:

    accept OBLIGATION --into PROVIDER_WORK --body RATIONALE
    accept OBLIGATION --create --kind K --title T --body RATIONALE
           [--classification C] [--phase P]

- `--into`: associate with existing provider Work (the N-convergence
  form). `--create`: no provider Work exists yet (the first-report form) —
  the provider Work is created in the SAME transaction.
- Committed effects, all-or-nothing: (a) with `--create`, the provider
  Work + its first message exist (audited via an `_emit`'d `create_work`
  act inside the transaction, the assign/withdraw precedent); (b) the
  obligation reaches terminal status `accepted` with `resolved_seq`
  addressing the `accept` act; (c) the rationale is published as a message
  on the CONSUMER Work (the answer the consumer sees); (d) the edge
  `consumer blocked_by provider` exists with `via_obligation`; (e) the
  consumer's readiness recomputes; (f) the wake sweep runs (an accept
  cannot wake — it only ADDS a gate — but the sweep stays uniform).
- Result: `{kind: "accept", seq, obligation, work (consumer), provider,
  created: bool, edge: {work, blocker, via_obligation}}`.
- Audit: primary event `accept` with payload naming obligation, both
  Works, `created`, rationale bytes, and BOTH in-lock resolution
  snapshots (the obligation route's and, for --into, the provider
  Current's). Dense: `create_work` (if any) then `accept` in one
  transaction.

Authorization, all in-lock with snapshots recorded:
- always: the live handler of the obligation's named route
  (`_obligation_gate`, as respond/dispose today);
- `--into` additionally: the actor is a live Current handler of the
  provider Work (`_handler_gate`) and the provider Work belongs to the
  obligation endpoint's team — accepting into another team's Work, or
  into provider Work whose baton has moved to a route the actor does not
  hold, refuses (D6 offers the weaker alternative for ruling);
- `--create`: root-creation rules apply; the kind must be a live kind of
  the obligation endpoint's team.

## D4 — the stories

**PushCoin→Drift, first report:** push.sl reports PUSH-1, asks
`@drift.bug`. Drift's handler runs `accept <obl> --create --kind rsrch
--title "parser recovery" --body "ours; tracking"`. One commit: DRIFT-1
exists, PUSH-1 is gated with provenance, the obligation reads `accepted →
DRIFT-1`, push's discussion shows the rationale. PUSH-1 may then enter
gates-waiting; default views stay noise-scoped (DRIFT-1 in drift's home
only); drill-through: PUSH-1 → blocked_by(via obligation N) → DRIFT-1.

**N-consumer convergence:** web and mdb report independently, each asking
`@drift.bug`; the handler accepts each `--into DRIFT-1`. DEP rises 1→3
live; each edge carries its own provenance; each consumer's discussion
carries its own rationale. Closing DRIFT-1 (universal outcome) ends all
three gates, wakes the waiting consumers atomically, DEP drops to 0, and
history explains every edge through its obligation.

## D5 — refusals, races, crash, retry (all in-lock where stateful)

- Obligation not pending (responded/disposed/withdrawn/accepted),
  verification flavor, or nonexistent → refuse; nothing commits.
- Consumer Work closed → its obligations are already withdrawn (WS-2), so
  the pending recheck covers it; raced close-vs-accept serializes to
  exactly one (close first: accept refuses "already withdrawn"; accept
  first: the close is still legal and the edge remains history).
- Provider Work closed (`--into`) → the open-only blocker rule refuses;
  raced provider-close-vs-accept: in-lock blocker status recheck.
- Wrong handler on either gate, or provider Work of another team →
  refuse.
- Self-edge (consumer == provider Work), duplicate edge, union cycle →
  the existing in-lock refusals, now inside the accept transaction; a
  refused cycle rolls back the `--create` Work too.
- Concurrent accepts of the SAME obligation (two providers, two sessions)
  → the pending recheck serializes to exactly one winner; the loser gets
  a structured refusal and creates nothing (including no orphan
  `--create` Work).
- Concurrent accepts of two DIFFERENT obligations into one provider Work
  → both commit; DEP=2; no interference.
- Config-generation change mid-accept → live in-lock gates decide;
  recorded snapshots keep history unambiguous (C4 discipline).
- Crash at every write boundary → single `_write` transaction:
  whole-or-nothing, proven by the established fault-injection harness.
- Retry without operation ids → the stated WS-2 boundary: a retried
  completed accept refuses ("already accepted → DRIFT-1") with zero
  duplicate effects; callers read before retrying.

## D6 — product choices for Slawomir (beyond D1)

1. D1 itself: the request-scoped edge authority (Option A) — the slice is
   blocked without it.
2. `--into` double gate: obligation-route handler AND provider Current
   handler (recommended), or obligation-route handler alone (weaker:
   permits gating on provider Work whose baton moved elsewhere).
3. The obligation's terminal status: distinct `accepted` (recommended —
   projections can say "accepted → DRIFT-1" without parsing prose) versus
   reusing `responded`.
4. Edge provenance `via_obligation` (recommended) versus no recorded
   association beyond the audit act.
5. Whether `--create` may also set `--parent` (a provider accepting into
   a NEW CHILD of an existing epic — recommended yes, with the existing
   parent-handler gate applying to the actor).

## D7 — test matrix for the implementation slice

Focused (`test_ws3_accept.py`): both authorization gates ± reassignment;
every D5 refusal; races accept-vs-accept, accept-vs-consumer-close,
accept-vs-provider-close, accept-vs-dispose, accept-vs-regen (both orders
where both are legal); fault injection at every write boundary of both
forms; retry; restart reconstruction (obligation terminal state, edge
provenance, DEP). Stories (`workflows/test_ws3_wf01/02.py`, source AND
packaged): the two D4 stories with default-view/drill/DEP/fanout
checkpoints. Break-sweeps proving neither half commits alone: (a) edge
insertion removed → association-without-gate detected; (b) obligation
terminalization removed → gate-without-answer detected; (c) the two
halves split into separate transactions → the fault-injection test
catches the partial commit. Projection additions (blocked_by/blocks
entries exposing `via_obligation`; obligations entries exposing
`accepted → id`; `accept` in the declared transitions for the eligible
handler) covered by parity and one-snapshot regressions.

Smallest implementation slice, once D1/D6 are ruled: schema v6
(`edges.via_obligation`, obligation status `accepted`), `accept` engine
transition + CLI verb, the projection provenance fields, the focused
suite, the two stories, and the sweeps — nothing else.

## Post-review corrections (6f3d6776, accepted for the implementation slice)

- **R47 — accept and the waiting consumer.** My D3(f) claim that "an
  accept cannot wake" was wrong for one case: a consumer
  obligation-waiting on THAT exact obligation wakes when the accept
  completes it (its named condition is satisfied), while the newly added
  gate keeps `ready` false; a gates-waiter does NOT wake (the accept only
  adds a gate); no automatic wait-type conversion happens.
- **R48 — compound event layout.** The outer `_write` allocates its
  sequence before mutate runs, so a nested `_emit`'d `create_work`
  followed by the primary `accept` would commit in backward order. The
  accepted layout: the primary `accept` event doubles as the provider
  Work's creation record when `created: true` (full creation payload
  embedded), with the consumer response message row written later in the
  same transaction — one honest compound act, dense and ordered.
