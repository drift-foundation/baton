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

## 2026-08-19 UTC — `baton.claude` (implementer)

W5 slice A: PLAN steps 3 and 4, plus the consumer widening the ruled
rollout puts in the same candidate. Schema 21 → 22; projection 11.0 → 11.1.
No TUI presentation (step 8), and no runner CONSUMES the new kind (step 6).

### Revalidation against the current tree

Every pinned fact re-derived by reading and running the tree, not taken from
`FINDING.md` or from my own `PROPOSAL.md`:

- schema had moved **20 → 21** since the proposal was written; projection was
  still 11.0. The proposal's numbers were stale, its conclusions were not.
- `participant_actions` still had exactly three kinds and is still documented
  as "the facts that may WAKE this exact member", so a fourth kind fits its
  own definition without touching Work.
- `wait_actionable` still creates no authority mutation; a persistent poke
  does not change that, because the `poke` verb writes and `wait` only reads.
- `obligations` is still the closest existing primitive and still ties every
  column to a Work (`work NOT NULL`, `message_seq`, `thread`), which is
  exactly why poke is not built on it.
- **The live-outage fact still held.** Both bridges share ONE validator —
  `acp_baton_bridge` imports `validateEnvelope` from the Codex bridge — whose
  final `else` threw on an unknown kind, rejecting the whole envelope. One
  unreadable entry would have stopped an agent receiving its ordinary Work
  and obligation wakes too.

### Order of work: consumers first, exactly as ruled

1. **Both bridges widened, tested, and green BEFORE the authority could emit
   anything.** The shared validator now removes an unknown-kind entry, keeps
   the rest of the envelope, and returns the removals in
   `result.ignored_actions`; each bridge reports the skew once per unknown
   kind. Once per KIND, not once per entry or once per poll — level-triggered
   delivery would otherwise repeat one diagnostic forever.
2. Only then the authority, projection and CLI.

Nothing relaxed except the kind. An entry still needs a unique non-empty
`action_key` whatever its kind (envelope structure, not kind semantics), and
every known kind is typed exactly as strictly as before. Both are pinned by
new assertions.

### What the authority gained

`pokes`, `poke_answers`, `poke_answer_work` — and the absence of a `work`
column in all three is the design, not an omission.

- **`poke target= [request=] [expires-at=]`** — any configured participant may
  ask any other, including itself. Newest-pending deduplication per (asker,
  target) is done in the committing transaction; the superseded row keeps its
  own text and gains `resolved_seq`, so it stays history rather than being
  rewritten.
- **`poke-answer poke= state= explanation= [work=…] [diagnostics…]`** — the
  one terminal response, from the exact participant asked.
- **`poke-cancel poke= [reason=]`** — the asker, or a `config` holder.
- **`pokes [asker=] [target=] [after=] [limit=]`** — the read.

**Expiry is derived and nothing schedules it.** There is no `timed-out` stored
status: past its deadline the row still says `pending` and every read calls it
`timed-out`. The check lives in `_live_poke`, which the write paths also call,
because a deadline enforced only on the read path would let a late answer
quietly resurrect a poke the operator had already been shown as terminal.

### PLAN step 4 — the response field contract

Two independently observable layers, both capability-based, both closed:

| layer | fields | unknown |
| --- | --- | --- |
| runner/provider | `provider`, `model`, `session_state`, `auth_state`, `limit_state`, `retry_at` | the literal `unknown` member of each vocabulary; `retry_at` null |
| agent status | `state` (`idle`/`working`/`waiting`/`needs-help`), `explanation`, `claimed_work` | — required |
| model telemetry | `context_limit`, `context_used`, `context_remaining` | null, **never** zero |

**Every diagnostic is a closed vocabulary or a bounded scalar. There is no
opaque column.** That is the ruling "diagnostics must not expose credentials,
account secrets, or unrestricted vendor payloads" made structural rather than
enforced by review: a pass-through blob IS an unrestricted vendor payload, so
there is nowhere for one to arrive. It also means nothing needs sanitizing
later, which is the failure mode a blob plus a filter always eventually has.

`unknown` leads each vocabulary deliberately. A reader must be able to tell
"the runner reports authentication is fine" apart from "this adapter cannot
see authentication at all", and a default of `ok` would erase that difference
in the direction that reassures.

### Canonical state beside the agent's claim, never instead of it

`answer.claimed_work` is what the agent SAID it is handling, each entry
carrying that Work's canonical status/phase/handler; `canonical.handled_work`
is what the authority says the target actually holds, read fresh. A test
pins the disagreement case directly: grace answers "working on W2" while
canonical says ada holds W2 and grace holds nothing. Collapsing the two would
hide exactly the case somebody poked to find.

### The invariant, tested as a whole-table comparison

`work`, `obligations`, `edges`, `messages`, `threads`, `thread_labels` and
`trials` are captured before and compared after a poke, an answer naming a
Work, and a cancellation — byte-for-byte equal. `work_events` for the named
Work is unchanged (the event-subject map is a whitelist, so a poke can never
manufacture an event on a Work it merely mentions), and the claim on that Work
is exactly where it was. Naming a Work in an answer is a report, never an
acquisition.

### The one decision that deviates from my own proposal — please rule

**Projection 11.1 (minor), not 12.0.** `PROPOSAL.md` §7 concluded "minor", the
disposition adopted it, and that is what I implemented — but §7 reached it
assuming the widening had shipped in a PREVIOUS release, and the ruler
collapsed both into one candidate. So I want the reasoning visible rather than
inherited:

- `jsonapi.py`'s own 11.0 note says a change a consumer would "silently
  misread OR REFUSE" moves the major. Until this candidate, an unknown action
  kind DID refuse — so on that rule alone the major would move.
- Every consumer in this repository is widened in this same candidate, and the
  widening lands before the authority can emit the kind. Under a tolerant
  consumer the addition is genuinely ignorable, which is what "compatible
  within the major" means. Every FUTURE action kind is additive for the same
  reason — that is the lasting value of the widening.
- The exposure that remains is a runner binary built before the widening met
  by an authority that emits a poke: it refuses that envelope by name rather
  than misreading it. Both bridges and the authority ship from one release
  directory, so they move together.

If the reviewer prefers 12.0 the change is small and I will make it: the
constant, three version pins in existing tests, `[7,8,9,10,11]` → `+12` in the
shared validator, and one `role_instructions` test that currently asserts 12.0
refuses. I did not make it unilaterally because it inverts a pinned decision.

### Existing tests I edited, and why each is a pin rather than an assertion

Four files, all forced by version constants, none weakening what its test
proves:

- `test_authority.py` and `test_w92_schema15.py`: schema 21 → 22 (the function
  name carried the number, so it was renamed too).
- `test_w136`, `test_w245`, `test_w47`: `PROJECTION_VERSION == "11.0"` →
  `"11.1"`. Each test's own point — same-major succeeds, stale major refuses —
  is untouched, and W136 now ALSO demands 11.0 beside 11.1, which proves an
  older minor of the live major still succeeds. That is a stronger assertion
  than the one it replaces.
- `codex_baton_bridge.test.mjs`: the `unknown action kind` refusal case was
  removed from the refusal table, because the ruled disposition inverts
  exactly that behaviour. It is replaced in the same file by a tolerance test,
  and two new structural cases keep the table honest — an entry with no
  `action_key`, and one with an empty one, still refuse whatever their kind.

### Regressions

**`tests/work/test_w5_conversational_poke.py`, 41 tests.** Positive, negative,
race-shaped, offline, replay, restart and purity, plus the public CLI grammar
end to end. The ones worth naming: a poke wakes a participant whose every
existing wake rule is silent; the whole-table non-interference comparison;
the canonical-versus-claim disagreement; expiry proven at one second before,
at, and after the deadline WITH the stored row still reading `pending`; an
`op-id` retry that neither mints a second poke nor renews the wait window; and
an offline target answering a year later.

**Bridges.** Codex 45 (tolerance, `ignored_actions`, unchanged strictness for
known kinds, duplicate keys across kinds, empty `ignored_actions` on a clean
envelope). ACP 42 — the whole loop: the entry BESIDE the unreadable one still
reaches the agent, nothing about the unknown entry does, and the diagnostic
appears exactly once across two polls.

### Break-sweeps

Each defect reintroduced alone against the 41-test suite.

| Reintroduced defect | Result |
| --- | --- |
| A poke never enters the action projection | 13 red |
| Expiry not derived in delivery | 3 red |
| A timed-out poke is still answerable | 1 red |
| No supersession — pending pokes accumulate | 1 red |
| Supersession also sweeps already-timed-out rows | 1 red |
| Anyone may answer a poke addressed to somebody else | 1 red |
| Answering touches the Work it names | 1 red |

### Gate

`just test-v11`: **1797 passed**, serial **40 passed**, ACP **42/42**.
`tools/codex-event-bridge`: **45 passed**. The whitespace check is clean.

### Not in this slice, deliberately

- **No runner consumes the `poke` kind.** PLAN step 5 is the review gate
  "before any runner consumes the new action kind", and step 6 owns the
  integration. Today both bridges tolerate and ignore it, which is exactly
  what the ruled order asks for and is why slice A can ship without slice B.
- **No TUI presentation** — step 8, explicitly after the JSON contract and
  live runner behaviour are stable.
- **No deployment.** The running set at `/home/sl/baton-v11` is release
  `7bea055` and is untouched; nothing here was deployed or activated.

## 2026-08-19 UTC — `baton.claude` (implementer), second pass

W5 came back to `baton.impl`. Recording what the repository records actually
show, because the answer to "what should I do now" is entirely in them.

### What the return contained

The pass at seq 62 carries an implementation instruction — "Implement
self-poke diagnostics, optional explicit timeout, newest-pending
deduplication with renewed expiry, terminal answer/cancel/timeout history,
normalized diagnostics, and unknown-action-tolerant Codex/ACP consumers plus
poke emission in one rollout" — and asks me to follow the `PLAN.md` review
gates.

Against that:

- **There is no `review-YYYY-MM-DDTHH-MM-SSZ.md` in this record.** Repository
  policy makes the review journal the durable artifact of a review pass; this
  record has none, so nothing states a disposition on the delivered slice A.
- **`PLAN.md` is byte-identical to before the first pass** — step 3 still
  reads `[ready: slice A]`, step 4 `[pending: slice A]`, step 5
  `[pending: slice A review gate]`.
- **`FINDING.md` is unchanged**, so the two questions the first pass raised
  for a ruling are still open.
- The thread carries no new message (`new: 0`).

I am not treating that as a request to build slice A a second time. Policy is
to resume from the repository records, and those records — this file — say
slice A is implemented and gated. Re-implementing would duplicate work that is
already in the tree and would destroy the evidence trail that says so.

### Revalidation of the tree, done rather than assumed

Every claim from the first pass re-derived against the working tree today:

- `transitions.py` carries `poke`, `answer_poke`, `cancel_poke`;
- `authority.py` is schema **22** with `pokes`, `poke_answers`,
  `poke_answer_work`;
- `jsonapi.py` is projection **11.2** (11.1 was W5's; W7 has since moved the
  minor again — the poke contract itself is unchanged);
- `projection.py` carries the `poke` action kind and the `pokes` read;
- both bridges carry `ignored_actions`;
- `tests/work/test_w5_conversational_poke.py` is present.

Full gate re-run on the current tree, not quoted from the first pass:
`just test-v11` **1844 passed**, serial **40**, ACP **42/42**,
`codex-event-bridge` **45**.

### The one thing the return surfaced that was genuinely missing

The phrase "newest-pending deduplication **with renewed expiry**" pointed at a
real coverage gap, and it is worth saying plainly that the return earned its
round trip on this one point.

The behaviour was correct — a superseding poke inserts its own `expires_at`,
so the new wait window is the one the asker just set — but only the NEGATIVE
half was pinned: `test_an_exact_retry_replays_and_does_not_renew_the_wait_window`
proved an `op-id` retry does not renew. A deliberate re-ask and a retry are
different acts, and only one of them had a test.

Two tests added:

- `test_a_superseding_poke_starts_its_own_wait_window` — the first poke's
  deadline passes and the live question is still live; the superseded row
  keeps the deadline it was created with, because it is history; the new
  window ends when the new deadline says it does.
- `test_a_superseding_poke_may_drop_the_deadline_entirely` — re-asking with no
  `expires_at` replaces a bounded question with an unbounded one, which is
  what "optional" has to mean in both directions.

Break-sweep: making the superseding poke INHERIT the superseded deadline reds
both, and nothing else. Suite is now 43 tests.

Everything else the return names — self-poke, optional explicit timeout,
terminal answer/cancel/timeout history, normalized diagnostics, tolerant
consumers plus emission in one rollout — was delivered in the first pass and
is covered; the section above this one lists each with its test.

### Still open, and still not mine to decide

Restated because they are what the review gate at PLAN step 5 exists to
settle, and neither has been answered:

1. **Projection minor vs major.** Implemented as a minor (11.1 at the time),
   per `PROPOSAL.md` §7 and the disposition — but §7 reached "minor" assuming
   the consumer widening had shipped in a PREVIOUS release, and the ruling
   collapsed both into one candidate. `jsonapi.py`'s own rule says a change a
   consumer would "silently misread OR REFUSE" moves the major, and an
   unwidened bridge would refuse. Cost of switching, if ruled: the constant,
   the version pins in `test_w136`/`test_w245`/`test_w47`/`test_w5`, the
   `[7,8,9,10,11]` list in the shared validator, and one `role_instructions`
   test that currently asserts 12.0 refuses.
2. **One existing assertion I removed.** The `unknown action kind` refusal
   case in `codex_baton_bridge.test.mjs`, because the ruled disposition
   inverts exactly that behaviour. It is replaced in the same file by a
   tolerance test plus two structural cases (an entry with no `action_key`,
   and one with an empty one, still refuse whatever their kind).

### State

Slice A implemented, gated, and **awaiting review** at PLAN step 5. Slice B
(PLAN step 6 — a runner actually CONSUMING the poke kind) stays behind that
gate, as the plan and the return both ask. Nothing deployed: the running set
at `/home/sl/baton-v11` is release `7bea055` and was not restarted.

## 2026-08-19 UTC — `baton.claude` (implementer), third pass

`review-2026-08-19T03-12-50Z.md`: slice A accepted, two release-gate
corrections required. Both made.

## 1. The projection major — the question I raised, ruled against my publication

Published as **12.0**. I shipped the poke half as 11.1 while arguing in the
same handoff that the rule pointed at a major; review ruled the major, and the
reasoning belongs in the record because it is this repository's own rule
finally applied to its hardest case.

A new ACTION KIND is not a new field. A consumer built before the tolerance
widening REFUSES an envelope containing `poke` — the whole envelope, not the
entry — so it stops receiving its ordinary Work and obligation wakes too.
Widening every consumer in the same candidate repairs the CANDIDATE; the mixed
interval between a deployed old runner and a new authority is where the
refusal actually lives, and no same-candidate widening reaches into it. That
is exactly the documented condition.

What the widening does buy is the NEXT one: inside major 12 every consumer
ignores an unreadable entry and keeps the rest, so a fifth action kind will be
a genuine additive minor. That is the difference between this bump and a
permanent tax.

W7's `blocking` field and blocker-first ordering rode 11.2 briefly and are
**aggregated** into this baseline rather than published separately. Nothing
was released between them, and two majors for one unreleased candidate would
describe a history that never happened. The review authorises exactly this.

Consumers widened in the same candidate: the shared participant-action
validator (`[7,8,9,10,11]` → `+12`) and `role_instructions.mjs`
(`[9,10,11]` → `+12`), whose own result shape did not change.

## 2. Slice B — the runners consume and deliver the poke

`poke` is now a KNOWN kind in the shared validator, typed exactly as strictly
as the other three. Being liberal about what a build cannot read is not a
reason to be liberal about what it does read, so the entry must carry a
positive `poke` sequence, an `action_key` that AGREES with it, a non-empty
asker and request, an `expires_at` that is a string or null — and **no `work`
field at all**. That last check is not pedantry: an envelope attaching a Work
to a poke would be describing a different primitive from the one the contract
approved.

`actionLocator` carries `poke`, `asker`, `request` and `expires_at`, which is
precisely what `poke-answer` needs — an agent should not have to re-read the
projection to answer a one-line question it was already handed.

Both prompt builders say the same thing, word for word:

> `baton.slaw asks baton.claude: still on W12? Answer through the canonical
> v11 CLI (poke-answer poke=7 state=idle|working|waiting|needs-help
> explanation=…), reading your canonical Baton state first.`

Deliberately ordinary. The approved contract calls a poke a lightweight
request for status between collaborators and says its wording must not imply
an alarm, escalation, accusation or health verdict — so the prompt names who
asked, repeats their actual question, and points at the one verb that answers
it. Tests assert the absence of alarming words rather than trusting the
sentence to stay calm.

Delivery is unchanged machinery: `poke:<seq>` is stable, so the existing
whole-set delivery memory makes repeat delivery idempotent, and the projection
already orders pokes last so they cannot displace Work or obligation wakes.
The bridges deliver; the AGENT answers through `poke-answer`. No adapter
answers on a model's behalf, which keeps "exactly one response terminally
answers the poke" true and matches "runner adapters only translate the common
action and response".

## The test that mattered most

Both bridge suites tested `poke` against fixtures they wrote themselves. That
is precisely how a producer and a consumer drift apart while both suites stay
green, so
`test_the_real_envelope_satisfies_both_runner_bridges` drives a REAL `wait`
envelope out of the CLI, writes it to disk, and runs it through the actual
shared validator, the compact locator and the ACP prompt builder under `node`.
The fields the authority emits and the fields a runner requires are now the
same fields or that test fails.

Its companion `test_the_emitted_action_carries_exactly_the_consumed_contract`
pins the producer half as an exact field set, so a change here fails beside
the bridge suites rather than silently ahead of them.

Break-sweep: making the validator tolerate `poke` again instead of consuming
it — the exact pre-slice-B behaviour — reds the cross-surface test alone,
which is the difference the review asked for stated as a diff.

## Existing tests updated

- The tolerance tests in both bridge suites used `poke` as their example of an
  unreadable kind. It is readable now, so they use a genuinely unknown one.
  That is what they always meant: the point is the entry BESIDE the
  unreadable one, not which word is unreadable this week.
- Every `12.0 refuses` assertion became `13.0 refuses`, in the two bridge
  suites and the role-instruction suite.
- Python version pins (`test_w136`, `test_w245`, `test_w47`, `test_w5`,
  `test_w7`, `test_jsonapi`) move to 12.0, and the ones that demonstrated a
  compatible older minor now demonstrate an 11.x demand REFUSING — which is
  the point of the bump and a stronger assertion than the one it replaces.

## Regressions

`tests/work/test_w5_conversational_poke.py`: **45**. Codex bridge: **46**
(strict poke typing across six malformed shapes, the forwarded event's summary
and locator, tolerance now on a truly unknown kind). ACP bridge: **44** (a
poke waking the agent with the question and the answer verb, and a poke
sharing an envelope with a Work action delivering both without displacing
either, across four polls including a level-triggered redelivery).

## Gate

`just test-v11`: **1912 passed**, serial **40 passed**, ACP **44/44**.
`tools/codex-event-bridge`: **46 passed**. The whitespace check is clean.

## State

Slice A accepted; the two required corrections are made. Awaiting re-review at
PLAN steps 5 and 7. TUI presentation (step 8) remains outside this gate.
Nothing deployed: the running set at `/home/sl/baton-v11` is release
`7bea055` and was not restarted — and it is a PRE-widening runner, so the
restart this candidate is heading for is the one the major bump exists to make
honest.
