# Progress

## Step 1 — the ledger states the phase (2026-08-18)

The projection needed the scheduler history, and the ledger already had
it — spread across five differently-named payload keys (`to`,
`destination_phase`, `phase`, `from_phase`, and the wake's own pair).
Reading all five would have meant the projection re-deriving the
authority's decision from circumstantial evidence.

So every phase-changing transition now records one uniform
`phase_now`: the phase the Work is in AFTER the event commits.
Seven sites — creation, claim, release, the phase verb, pass/return,
the condition wake, and the readiness gate — plus terminal close, which
records `None`, the one transition that ends an episode without opening
another.

It is a LIST whose entries name their Work, because one event can move
more than one: creating a child gates its parent, so the child's
`create_work` event is where the PARENT enters `waiting`. A bare phase
string would have attributed that to the wrong Work.

## Step 2 — the intervals

`_phase_intervals()` replays those records, keyed by the event that
ENTERED each episode, in the shape `_claim_intervals()` already
established. An open episode measures from the read's own instant; a
completed one is fixed.

Heartbeats cannot split an episode BY CONSTRUCTION rather than by
exclusion: an event that changes no phase writes no `phase_now`, so
there is nothing for the replay to see. That is stronger than listing
heartbeat as an exception, because the next non-phase event is also
covered without anybody remembering to add it.

The interval rides its entry event ONLY. Claim intervals deliberately
ride both boundaries so the facts are reachable from either end; doing
that here would print the same episode twice in an index that shows one
row per episode.

## Step 3 — the fixed columns

`EVENT | KIND | ACTOR | TIME | PHASE | FOR`, fixed widths, one header,
and an entire lower-priority column dropped whole when the pane is too
narrow. Truncating one would move every column after it — the same
defect in a subtler form.

The Events index needed its own width. It carries six columns where the
Messages index carries prose, and sharing the Messages budget of 34
would have dropped PHASE and FOR at every terminal size — the two
columns this Work exists to add.

`duration_cell()` sits beside `held_cell()` and shares its scale and
overflow, so the two read identically; the difference is only that this
one formats seconds the PROJECTION computed rather than arithmetic
against a terminal clock.

`PROJECTION_VERSION` 9.1 -> 9.2, additive.

## Step 4 — acceptance

`tests/work/test_w47_event_phase_intervals.py`, 25 checks: the full
boundary matrix (creation, claim, release, pass, park/resume, gate,
wake, terminal close), heartbeat non-reset, once-per-episode, completed
stability, open elapsed, JSON carrying no glyph and exactly the ruled
field set, the shared scale at 0/59/60/5999/6000 and its negative
clamp, column alignment across a deliberately long event kind, the
phase and duration cells riding only the entry row, whole-column
omission preserving the surviving offsets, and the highest-priority
columns surviving the narrowest pane.

Break-sweeps: concatenating the row again reds 2; attaching the
interval to both boundaries reds the once-only check.

That second sweep is worth recording, because the first time I ran it
it did NOT red. For phase intervals the ending event is usually also
the next episode's start, so a both-boundary attachment is only
reachable at terminal closure — and my once-only test had not closed
anything. The test now closes the Work, which is the single case that
distinguishes the two implementations. Without it the check passed
against exactly the behaviour it forbids.

## Evidence

- Gate: **1213 passed** + 14 serial + acp 38/38 on 32 cores.
- Whitespace check clean.
- No persisted schema change: the intervals are derived from the
  append-only ledger.

## Round 2 — the two compound transitions (2026-08-18)

Both review findings are correct and are fixed. I hit them independently while
running the v11 gate under W30 and traced each on a fresh authority before
reading the review; the traces agree with R1 and R2 exactly.

**R2 — `accept create=`.** The provider is inserted directly rather than
through `create_work`, so nothing recorded its birth phase. The accept event
carried `phase_now` for the CONSUMER only (`[{phase: waiting, work: W2}]`) and
the created provider had no entry at all — no `phase_interval` on any event,
an empty scheduler history from birth. `_phase_now(payload, provider_id,
create["phase"])` now sits immediately before the readiness recomputation, not
after it: `_recompute_ready` may append a second entry for the same Work in the
same event when a gate is present at birth, and the replay takes the last entry
per event, which is that later truth.

**R1 — a blocking `request`.** The request transaction moves the Work to
`waiting` and releases the claim in its own statement, reaching neither
`set_phase` nor `release_claim`. Trace: `create_work(queued)`, `claim(active)`,
`request(nothing)`, while the row read `phase=waiting, handler=NULL`. The
payload's `from_phase` was already there but is evidence about the released
claim, not the scheduler axis — so the replay kept the `active` episode open
while the Work was in fact waiting, the false actionability signal W38 ruled
against.

### The class, not the two instances

Both defects are one shape: a transition that moves the phase in its own
statement and therefore never passes the place where the recording lives. Since
the replay reconstructs nothing by design, an unrecorded move is not
recoverable later — it is absent forever. Fixing two named sites does not stop
a third.

So the sweep was run over every phase write in `transitions.py` — eight
`UPDATE`/`INSERT` sites plus the two creation paths. All are now paired with a
record; the condition wake was already correct in a way the grep does not show,
because it emits its own event with `phase_now` inline.

And the invariant is now enforced rather than eyeballed:
`test_the_ledger_and_the_row_agree_across_every_transition` drives one scenario
through creation, claim, blocking request, `accept create=`, provider close,
park, resume, a child gating its parent, the child's close, and terminal
closure — asserting after every step that the phase replayed from the ledger
equals the phase the authority reports. Two more tests cover the paths that
scenario cannot reach in sequence: a dependency edge gating from outside the
thread, and `pass`. A future transition that moves the phase without recording
it fails here whether or not anyone remembers to write a test for it.

One note for the reader of that guard: it compares against the PROJECTED phase,
not the raw `work.phase` column. The column is `NOT NULL`, so a closed Work's
row keeps whatever phase it last held; the projection derives the terminal null
from the status, and that is what every reader sees. Comparing the column would
fail on every close for a reason no operator can observe. That is recorded in
the helper's docstring so nobody "fixes" it later.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| `accept create=` records no `phase_now` | 2 red (R2's test + the invariant) |
| blocking `request` records no `phase_now` | 2 red (R1's test + the invariant) |

The invariant catches each independently of its named test, which is the point
of having it.

### Gate

`just test-v11`: **1218 passed, 1 failed.** The one failure is
`test_w26_command_history.py::test_an_overwidth_reverse_query_keeps_its_live_tail_visible`
— W26's own round-2 review defect, queued and unclaimed on `baton.impl`, and
unrelated to this Work. Taking it next.
