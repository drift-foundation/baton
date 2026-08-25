# Progress: reconcile agent-session close with the observation axis

Implementer-owned. One writer: `baton.claude`.

## Implementation — 2026-08-23

The ruling is this record's own and was confirmed before I claimed the Work,
so there was nothing to decide — only to revalidate and build. I checked all
four premises against the current tree rather than trusting the finding: the
forbidden edges are still taken, the index is still keyed on the observation
state, the stranding is still real, and the two signed-off cases still close a
`not-started` row to get a posture back.

### The separation, and why it removes both halves of the conflict

Occupancy was a projection of the observation axis, so the only value that
freed a posture was `closed` — which asserts terminal turn facts nobody may
have seen. That gave every non-normal ending a choice between stranding the
posture and inventing an observation, and the close path chose to invent.

`posture_slots` makes occupancy a manager-owned fact. Nothing about the
observation axis changed; `unknown` is still terminal and still never becomes
`closed`. What changed is that recovering capacity no longer requires
relabelling evidence.

### Silence is not evidence

The part worth being strict about. `RECOVERY_EVIDENCE` is two members, and a
stop REQUEST, an elapsed deadline and a disconnect are deliberately not among
them — a case names all three so the omission reads as a decision rather than
an oversight. `runtime-absent` requires the exact identity that was observed,
because "the container is gone" without saying which container is a claim
about nothing.

### The two migrations

Both preserve what they proved. The freshness case now recovers its slot
through the path the ruling added for exactly that situation, and I ADDED an
assertion that every epoch's observation is still `not-started` — recovery
rewriting no history is the property the migration turns on, so it should be
asserted rather than implied. The posture-release case still proves an
`unknown` row refuses a second open; it now drives three non-evidence attempts
and asserts the `unknown` survives recovery.

**One thing I left stale on purpose.** The second case is still titled "only
CLOSING frees the posture", which the ruling makes untrue. Renaming a
signed-off case is a bigger edit than the ruling authorized, and its body now
says what it means. Raised on the handoff for the reviewer to decide.

### The gate is not all green, and it is not this Work's failure

`cd v12 && npm test` is **621 passed, 1 failed** of 622. The failure is
`W2929 re-review: an options document is a plain record`, an additive
regression a W4 re-review added to the reconnect suite while I was
implementing this. It drives Date, Map, RegExp, class-instance and
inherited-member option envelopes through `handleTransportLoss`, whose
envelope predicate W771 does not touch.

I did not fix it under this claim. It belongs to W4's open review round, and
correcting another Work's finding inside this one would put the change in the
wrong record. W4 is queued at `baton.impl` and is the next thing I claim.

### Verification

- `cd v12 && npm test` — **621 pass, 1 fail** of 622; the one failure is W4's,
  named above. Zero test-owned roots retained under a TMPDIR bracket.
- Eight mutations, all witnessed; one check measured as unreachable behind the
  column's CHECK constraint.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

### State

**Awaiting independent review.** Plan item 5 — re-reviewing W4's composition
and every adapter consumer against the corrected lifecycle — remains open and
is not discharged by this implementation.

## First correction — 2026-08-23

`review-2026-08-23T18-49-02Z.md`, three P1. Reproduced before any edit — 16
of 21, the five additive regressions the only failures. All three findings are
correct. Evidence: `evidence/correction-2026-08-23.txt`.

### I built a closed vocabulary of labels and called it evidence

The three findings say one thing between them. The ruling required positive
evidence that the old provider session cannot still act. I implemented a
closed set of evidence NAMES and checked membership in it — the spelling of a
caller's assertion — and treated that as the evidence. So
`provider-session-closed` released a slot whose session was still `ready`, and
`runtime-absent` accepted any non-empty string without ever comparing it with
the runtime the attempt is durably attached to.

`proveEvidence` reads the fact now: the same epoch's durable `closed`
observation, or the exact `attempts.runtime_id`. And it runs before the slot
state is read, so a caller whose evidence is not real never learns whether a
retry would have answered.

The epoch binding is the same mistake in a different place — a mutation that
does not say which epoch it is about will act on whichever one is there.

### Two transactions were a crash window

Transport loss recorded `unknown` and moved no slot. Composing them through
two transactions would have left a state where the observation had landed and
the slot had not — a session recorded `unknown` whose posture still looked
live. The `...In` variants let the observation and the slot movement be one
transaction; the store-level functions are thin wrappers, so there is one
implementation of each rule rather than two.

### The reviewer's case taught me something the review text did not say

`a delayed close cannot release a newer epoch` expects epoch 1 to end up
observed `closed` while epoch 2's slot is untouched. My first correction
refused the whole act, which rolled the observation back with it.

The case is right and I was wrong: epoch 1's provider session really did
close, and that observation is true whatever the posture has done since. The
close records the observation always and releases only its own slot, reporting
`releasedSlot: false` otherwise — "the close landed and the posture did not
move" is a result a caller has to be able to see.

### A zero that was a missing case, not a broken instrument

One mutation — letting an unattached attempt be declared absent — reported no
witnesses. The instrument was fine; with the identity comparison still in
place such an attempt refuses anyway, just with a pair that says the caller
named the wrong runtime when the truth is that this attempt names none. The
added case drives that distinction.

### I damaged one of the reviewer's cases

A blanket textual rename of `epoch:` to `sessionEpoch:` across the file also
rewrote `session_epoch:` inside one of their expected rows. The failure it
caused is what found it; repaired, and the file re-audited for other instances
— there were none. A mechanical edit across a file somebody else also writes
in is worth doing narrowly.

### Verification

- W771's suites: posture slots **22/22**, sessions **18/18**, axis **16/16**.
  All five review regressions pass.
- `cd v12 && npm test` — 639/643; zero test-owned roots under a TMPDIR
  bracket. The four remaining failures are other Works' open rounds — two
  W543 and two W4 — and were not touched here.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

### State

**Awaiting re-review.** Plan item 5 remains open: this round composed the two
product entry points W771's own rule reaches, and the sweep of every adapter
consumer is still that item's.

## Second correction — 2026-08-23

`review-2026-08-23T19-28-58Z.md`, one P1. Reproduced before any edit — 22 of
24, the two additive regressions the only failures. The finding is correct.
Evidence: `evidence/correction-round2-2026-08-23.txt`.

### The reviewer taught me this asymmetry last round and I applied it once

Round 1's delayed-close case established that the OBSERVATION is about the
epoch and always lands, while the SLOT movement is about the posture and only
applies to its own occupant. I implemented that in `closeAgentSession` and did
not carry it one function over.

So `handleTransportLoss` still required both, and a delayed epoch-1 report
refused on epoch 2 and rolled back with it — leaving epoch 1 falsely `ready`
when the transport really had died for it. The composition matches the close
now, and the answer reports the occupancy that ACTUALLY holds: a caller told
`recovery-required` while a later epoch occupies the posture has been told
something false about the posture.

The strict slot API is unchanged, as the review requires. What changed is that
the composition stopped asking it a question that does not apply.

### I wrote the added case as a property, not a third instance

Because the finding was that I had treated a ruling as a precedent about one
function. `the two endings share one asymmetry` drives BOTH transport loss and
normal close through the same scenario and asserts the same three things of
each. The next ending has a property to satisfy rather than a precedent to
notice.

### A mutation whose witnesses were not mine

One mutation initially reported two witnesses — and both were W4 fifth-review
cases that had just landed in the reconnect file and fail on the current code
for their own reasons. My own case did not assert the reported occupancy at
all. I added the assertion, and the mutation now fails the case that should
own it.

That is a new failure mode for me: I have been checking whether a zero is real
and had not been checking whose the non-zeros are.

### Verification

- W771's suites: posture slots **25/25**, sessions **18/18**, axis **16/16**.
  Both review regressions pass.
- `cd v12 && npm test` — 646/652; zero test-owned roots under a TMPDIR
  bracket. None of the six remaining failures is W771's — two W543, two W641
  and two W4 fifth-review cases, none touched here.
- whitespace clean.

### State

**Awaiting re-review.** Plan item 5 remains: the review's own consumer sweep
found no additional `v12/src` posture-slot consumers, so what is left is the
W4 integration review rather than a search.
