# Progress

Implementer: `baton.claude`. Canonical Baton Work: W4615.

**State: awaiting review.** Plan items 3-6 are landed and verified; the Work
is passed back rather than closed. Plan item 8 — granting `dispatch` in the
live `baton.json` and advancing the deployment's `infra.json` to version 2 —
is an operator act this Work deliberately does not perform.

## What this Work is

The managed stack keeps the pipeline saturated, so an operator waiting for
"the current item" to finish before a restart can miss the gap repeatedly:
the moment one handler relinquishes a claim, readiness offers the next
eligible Work to somebody else. Drain draws a deterministic boundary instead.

Drain is LIFECYCLE state, not a Work phase and not an instruction to an agent.
Nothing about any Work changes when the deployment drains — the rows keep
their phase, Route and Handler, and the only difference is that no new claim
is admitted. A regression asserts exactly that.

## What landed

### The authority (schema 27 -> 28)

`dispatch_control` is one typed singleton row — mode, monotonic control
generation, boundary sequence, actor, transition instant — seeded `running` at
creation, so no reader invents a default for a missing row. `dispatch_events`
is the typed global journal: `drain_requested`, `pause_reached`, `resumed`,
keyed `(seq, kind)` and never a Work message.

It lives in the authority rather than a lifecycle file because claim admission
and the mode transition must serialize through ONE writer. A file consulted by
the readiness producer could not refuse a claim arriving on another connection
between the read and the write, which is the race the boundary exists to
close.

### The boundary is decided in the write transaction

`claim_work` refuses admission while `draining` or `paused`, before assignment
and inside the transaction — so a direct CLI claim, a retry, or a claim
already in flight when drain committed is refused by the database rather than
by every caller remembering to ask. Proven on two connections in both commit
orders: a claim is either inside the boundary set or refused, never admitted
after it.

The drain mutation records ITS OWN sequence as the boundary, so "after the
boundary" is decided by the same monotonic counter that orders every other
act rather than by a wall clock.

### Pause is settled at the one mutation boundary

`Authority._write` checks after EVERY mutation whether a draining authority
has run out of live assignments, and records `paused` in that same commit.
That is why `set_phase`, a blocking `say`, `_recompute_ready` or any other
Handler-clearing path can end the finishing round; a check copied into
`pass`/`release`/`close` would have stranded a drain after a legitimate final
release. A regression ends the round through `release` specifically, which is
not one of the three verbs the boundary's prose names.

### Authorization

`dispatch` is a third accepted-configuration capability, checked inside the
same transaction that changes the singleton — so a configuration generation
revoking it takes effect against the next act rather than the next process.
Every inferred substitute is refused by a case: a Route, a held role, the
runtime action owner, `recover`, and `config`. Status requires nothing.

### Projection

`dispatch_view` and `dispatch_history` are the one bounded projection, carried
by `home` and by `wait` from the same read snapshot. Blockers are DERIVED from
live assignments — never a stored snapshot that could drift — and bounded with
explicit truncation. Runtime state is deliberately absent from the decision: a
blocker whose runner reports `failed` still prevents pause, or adapter
telemetry would decide the deployment's lifecycle.

`participant_actions` is deliberately UNFILTERED. Drain suppresses model
wakes, not visibility, so the TUI Inbox and the human counters are unchanged;
the filter lives on `wait_actionable`, the one surface a managed bridge polls.
While draining a participant is delivered only the Work it already holds;
while paused, only adapter refresh. A non-running answer returns immediately
with `timed_out: false` and the dispatch object, so a drained deployment never
reads as an idle one.

Projection minor 12.3 -> 12.4: additive, and a client that ignores the new
object reads exactly what it read before.

### Surfaces

`drain`, `resume` and `dispatch` CLI verbs, with `drain`/`resume` recorded as
managed-workflow policy EXCLUSIONS. The TUI paints `Dispatch:DRAINING (N
active)` / `Dispatch:PAUSED` through ONE shared right-edge painter used by
both the top-level and drilled headers — identity still drawn last and
overdrawing. `infra.py` gains manifest version 2 with a NAMED control triple
plus `drain`, `resume`, `dispatch`, and the graceful `stop-drained`.

## Verification

- `tests/work/test_w4615_dispatch_drain.py` — **27 focused cases**: the
  capability and its transactional check, the empty and non-empty finishing
  rounds, the two-connection claim/drain race in both orders, every
  Handler-clearing path, second-drain refusal, operation replay and conflict,
  resume, the managed/human split, immediate non-running answers, explicit
  truncation, restart in both modes, a failed runtime not retiring a blocker,
  the public grammar, and the lifecycle manager including its refusal when the
  named participant may not.
- `pytest -n auto -m "not serial" tests/work` — **2880 passed**.
- `pytest -m serial tests/work` — **52 passed**.
- `tools/acp-baton-bridge npm test` — 55. `v12 npm test` — 161.
- `tools/codex-event-bridge npm test` — 283 tests, 282 pass, **1 fail**: the
  W4303 reviewer regression "a reconnect settlement racing late turn/completed
  files one incident". It is that Work's, not this one's — an untracked test
  file that imports no `baton_work` module at all, so nothing in this change
  can reach it.

Thirteen existing cases moved with the change and each was inspected rather
than bulk-edited: two schema-version pins, five projection-version pins, the
W220 policy registry (a deliberate exclusion, recorded), three `wait`-shape
assertions that gained the additive `dispatch` object, and one W245 vocabulary
guard that caught a comment of mine pairing "current" with an eligibility
noun — a real repository rule, and the scan was right.

## Not done, on purpose

- **No live configuration edit.** The deployment grants `dispatch` to nobody
  and its `infra.json` is version 1, so it reads `running` and correctly
  refuses drain and resume. Both are operator acts with their own accepted
  generation (plan item 8).
- **No automatic anything.** Drain cancels nothing, releases nothing, and
  never converts a wait into a cancellation. A failed or orphaned claim stays
  a visible blocker with its exact identity.
- **Plain `stop` is unchanged.** See the divergence recorded in `FINDING.md`.

## Review notes

Six decisions beyond the pinned boundary are in `FINDING.md` under
"Implementation revalidation — 2026-08-22" with their reasoning. The first is
the one most worth a second opinion: the graceful stop is named `stop-drained`
and the plain `stop` keeps its meaning, which is a deliberate divergence from
the reviewer's proposed boundary and is argued there.

## Round 2 — three read and audit edges (2026-08-22)

`review-2026-08-22T16-25-29Z.md`, three P2s. All reproduced before any edit;
all correct. Evidence:
`evidence/correction-projection-edges-2026-08-22.txt`.

### What I had wrong

- **The history cursor could not traverse its own journal.** I designed
  `dispatch_events` so two kinds could share one authority sequence — and
  documented why — then wrote a reader that ordered by `seq` alone, limited
  ROWS and resumed with `seq < next_before`. A page size that bisected the
  empty-drain pair made the second event unreachable. `limit` counts INSTANTS
  now, sibling order is written out, and the cursor names the last instant.
- **Two snapshots described a state that never existed.** `dispatch_view`
  read the singleton and the live Handler rows independently, so a final pass
  committing between them returned `draining` with zero blocking claims. It is
  self-snapshotting now and `wait` derives both under one outer reentrant
  snapshot — which is what the pinned contract asked for and what my own
  implementation note claimed I had done.
- **The settlement used the wrong clock.** `_settle_dispatch` called the
  private wall clock while the act it completes used the authority's, so under
  an injected instant the two same-sequence events disagreed and the singleton
  inherited the host's time.

### Tests — 4 new cases (31 total)

Instant-complete traversal at `limit=1`; the interposed two-connection read;
`wait` deriving both from one instant; and the authority clock for both the
immediate empty drain and a later final release.

**Two of my three first-attempt mutations left the suite green** — they were
too weak to reproduce the defects — so they were redone against the exact
original code paths. A mutation that does not fail is not evidence about the
test, and I would rather record that than quietly keep the weak version.

### One existing test's fixture moved, and it is recorded

`test_w321_readiness_cadence`'s "meanwhile" commit ran on the SAME connection
from inside a patched `participant_actions`. A connection holding a read
snapshot cannot also write, so that fixture raised once `wait` took one
snapshot. The commit moved to a second connection; the assertion is unchanged,
and a second writer is the more faithful "meanwhile". The alternative was
dropping the one-snapshot boundary the review requires, which is not a trade
worth making for a fixture mechanism.

### Verification

- `tests/work/test_w4615_dispatch_drain.py` — **31 passed** (27 before).
- `pytest -n auto -m "not serial" tests/work` — 2909 passed, 2 failed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/codex-event-bridge npm test` — 295 tests, 294 pass, 1 failed.
- `tools/acp-baton-bridge npm test` — 55 passed. Whitespace check clean.

### The three failures are not this Work's

Two are W4996's reviewer cases against `src/baton_work/tui/graph.py`; one is
W2845's round-9 reviewer case against `exec_policy.mjs` ("astral text in a
comment does not shift the policy mask" — a real defect in the masking I
landed there last round). Both Works are queued on `baton.impl` awaiting their
own turns and neither was touched from here.

### State

**Awaiting re-review.** No live configuration was edited; plan item 8 remains
the operator act.

## Round 3 — one sample per write (2026-08-22)

`review-2026-08-22T17-57-11Z.md`, one P2. Reproduced before any edit; the
review is right, and it corrects my own round-2 correction. Evidence:
`evidence/correction-single-instant-2026-08-22.txt`.

### What I had wrong

Round 2 fixed the clock SOURCE and left the number of SAMPLES at two.
`drain_dispatch` read `store.clock()` for its own two rows and `_write` read
`self.clock()` again for the settlement, so an empty drain's two events —
written at ONE sequence, deliberately, because they are one indivisible
committed act — carried two timestamps the moment the clock advanced between
the calls.

My round-2 regression could not see it: `BATON_WORK_NOW` pinned to one
constant makes every sample identical, so it proved "same clock source" and
not "same act instant". Those are different properties and I asserted the
weaker one.

### Changed

`Authority.instant()` is the write's one sampled instant. `_write` takes it
once, inside the transaction and after the replay check, and clears it in a
`finally` however the write ends. `drain_dispatch`, `resume_dispatch` and
`_settle_dispatch` read it back.

`instant()` refuses outside a write rather than falling back to `clock()` — a
caller with no open transaction wants wall time, and quietly answering with a
fresh reading is how the two drifted apart to begin with.

### Tests — 34 (32 before, the reviewer's retained)

The reported case covers the immediate empty drain, so two were added: a
later final release carrying ITS act's instant (the two events correctly
DIFFER there, because they are two authority instants), and the sampled
instant not outliving its write — a refused mutation samples and then raises,
and `instant()` afterwards must refuse rather than answer with the leak.

Four mutations, each independently: settlement re-reading the clock, drain
re-reading it, the `finally` removed, and `instant()` falling back instead of
refusing. Each fails exactly the case that names it. The last two are
witnessed only by the leak case, which is why that case exists.

### One call site outside this Work changed, and it is recorded

`create_trial`'s R42 in-lock deadline recheck read `store.clock()`, and
`_write`'s new sample consumed a moment that
`test_ws2_due.py::test_a_round_rechecks_deadline_after_entering_the_write`
had budgeted. The recheck reads `store.instant()` now — literally what R42's
own comment above it asks for, "ONE transaction-local instant" — and since
the sample is taken after BEGIN IMMEDIATE the recheck is still strictly
inside the lock. The WS-2 property is unchanged and its assertion untouched.

The other in-mutation `store.clock()` call sites were deliberately NOT
converted: each is one act sampling once for its own fields, which is not the
reported defect, and they are other Works' code.

### Verification

- `tests/work/test_w4615_dispatch_drain.py` — **34 passed** (32 before).
- `pytest -n auto -m "not serial" tests/work` — 2919 passed, 4 failed.
- `pytest -m serial tests/work` — 52 passed.
- `tools/codex-event-bridge npm test` — 297/297. `acp-baton-bridge` — 55/55.
- `v12 npm test` — 200/202. Whitespace check clean.

### The six failures are not this Work's

Four are W4996's reviewer cases against the dependency graph; two are
W2929's in `v12/src/worker_manager/`. Both are queued on `baton.impl` for
their own turns and neither was touched from here. W4303 and W2845 are clean.

No projection version change: `instant()` is internal and no response shape
moved.

### State

**Awaiting re-review.** No live configuration was edited; plan item 8 remains
the operator act.
