# Activity source and transport design — W61599 items 11-12

Recorded 2026-09-15 by baton.claude, claim 174354. **Design only.** No product
or test file was edited, nothing was executed, and this proposes rather than
approves. It builds on the corrected pre-work
`work/records/2026/09/finding-v12-live-progress-prework/PREWORK.md`
(`sha256:65243e41…`) and on `review-2026-09-01T14-24-19Z.md`, both read in full.

## 1. What has to change, restated from the review

The counter counts the wrong stream, the publisher blocks the drain it was added
to protect, and a zero-byte EOF freshens an age that means "latest activity".
PLAN item 11 names the three together; item 12 names the proof.

## 2. The producer — where a provider-safe count already almost exists

`ClaudeAgent._ran_provider` (`v12/worker/claude_agent.py:1778`) already drains
the provider's own stdout **inside the container**, on its own thread, in 4096-
byte pieces:

    piece = os.read(read_fd, 4096)
    ...
    room = MAX_PROVIDER_RECORD - len(held)
    if room > 0:
        held.extend(piece[:room])
    if len(piece) > max(room, 0):
        partial[0] = True

**It bounds what it KEEPS and never counts what it READ.** A cumulative
`seen += len(piece)` beside `held.extend` is the whole producer: it is the
provider's own stream rather than outer exec noise, it is observed in the one
place that already sees every byte, and a length is content-free by
construction — the same property that made the original `_Channel` count safe.
No transcript byte leaves the container to produce it.

### The one fact that decides this, and it is not yet observed

**Whether that stdout grows during a turn or arrives all at once at the end.**
`PROVIDER_ARGUMENTS` is `--print --dangerously-skip-permissions --output-format
json` (`claude_agent.py:195`). A single final JSON document would make the count
jump from 0 to its total at completion — durable and honest, but useless as
liveness, and it would not satisfy item 12's "before completion".

The review says exactly this: the final JSON stdout *"is not necessarily an
incremental native session"*, while *"its private native JSONL was the live
source observed in W52821"*, and *"the implementation must prove the chosen
source changes during a real turn."* **Nobody has made that observation in this
tree, and I have not made it either.** So the design carries two candidates and
the experiment that chooses between them:

| Candidate | What it needs | Cost if chosen |
| --- | --- | --- |
| **A. Provider stdout** as read today | Prove `piece` arrives more than once during a real turn under the current argv | One counter line. Nothing else moves. |
| **B. Native JSONL** under the prepared home | Prove a session file is written and grows; `_prepared_home` (`:1941`) builds `$HOME/.claude` under per-turn scratch, so the path is container-private already | A bounded in-container observer: `os.stat` size of one identified file on a timer. Still a length only. |

**Decisive experiment, one turn, no new infrastructure:** in the existing
deterministic provider seam, record the arrival times and sizes of each `piece`
and, separately, the size of any file appearing under the prepared home. If A
shows more than one arrival, take A — it is strictly smaller. Otherwise take B.
**A third outcome is possible and must not be papered over:** if neither grows
incrementally under the current argv, the honest options are changing
`--output-format` to a streaming form (a provider-contract change needing its
own review) or reporting that provider-safe liveness is not available without
one. That is a finding, not a failure to design.

## 3. The transport — an existing closed seam, not a new one

The worker already publishes documents into a **manager-owned directory
bind-mounted into the container**: `exchange.EVENT_DIRECTORY`, mounted at
`EVENT_TARGET = "/run/baton/exchange/events"` (`exchange.py:89`, `:342`,
`:353`), created by the manager with mode `0o700` (`:402`).

`EVENT_DOCUMENTS` is a closed vocabulary — the receipt, one
`state-<operation>.json` per operation, and the terminal (`exchange.py:169`) —
and `baton_worker.serve_exchange` already writes `state-work.json` at
`dispatched` (`baton_worker.py:2066`) and again at `answered` (`:2107`).

**So the seam exists, is closed, is manager-owned, and already carries periodic
per-operation state.** The proposal is one bounded member on that document —
a cumulative `bytes_observed` integer — republished on the worker's own cadence
while the provider runs. No new mount, no new transport, no new document kind,
and nothing that can carry content.

**What this deliberately does not do:** it does not add a second channel out of
the container, and it does not let the deployment read anything the worker did
not choose to publish.

## 4. Publication — bounded, coalescing, and off the drain

The review's requirement is exact: *"the byte-drain path may only update bounded
in-memory state. Publish from an independent, bounded/coalescing path whose
blocked or failed store operation cannot stop reads, session completion, or
teardown."*

Two independent places, both bounded:

- **In the container:** the provider drain updates an integer. A separate
  writer republishes `state-work.json` at most once a second. A write that is
  slow cannot stop `os.read`, because they are different threads and the drain
  never waits on the writer.
- **On the manager:** `_Channel._drain` stops calling the observer at all. The
  deployment reads the exchange state it already reads and calls
  `observe_activity`. If that path is slow the stderr pipe is unaffected,
  because nothing on the drain thread waits for it.

This retires the measured defect rather than mitigating it: the review's
reproduction showed the pump stopped at its first 4,096-byte report for as long
as the observer blocked, with `ControlStore.open`'s 5,000 ms busy timeout as the
per-report ceiling. After this change the drain has no publisher to block on.

## 5. Freshness — positive growth only

`observe_activity` is unchanged: it already refuses a regression, ignores a
repeat and keeps the column pair consistent.

The change is at the caller: **publish only a positive total.** A stream that
produced nothing publishes nothing, so the projection stays absent and no age is
rendered for a worker that never moved.

**This changes an existing assertion and that is the point.**
`tests/tools/test_dogfood_operator.py:7158
test_a_silent_worker_is_observed_as_silent_and_not_as_unobserved` asserts
`seen == [0]` and argues "zero is a fact". Under the review's [P2] and PLAN item
11 that position is superseded unless a *separate* observation instant is
explicitly ruled — and no such instant is proposed here, because a second
timestamp with a second meaning is more surface than the operator question
needs. **Recommendation: absence until positive growth**, and the case is
rewritten to assert that, with its "zero is a fact" reasoning preserved in the
new docstring as the position that was considered and superseded.

`tests/tools/test_dogfood_operator.py:7094
test_every_byte_is_counted_including_the_ones_discarded` likewise changes,
because the stream it counts is no longer the activity source.

## 6. Paths

| Path | Change |
| --- | --- |
| `v12/worker/claude_agent.py` | count what the existing drain reads; if candidate B, the bounded in-container observer |
| `v12/worker/baton_worker.py` | carry the cumulative count on `state-<operation>.json` and republish on cadence |
| `v12/python/src/baton_v12/worker_manager/exchange.py` | one bounded member in `STATE_MEMBERS`, held like the rest |
| `v12/python/tools/dogfood_operator.py` | `_Channel` stops being the activity source; publish from the exchange read |
| `v12/python/tests/tools/test_dogfood_operator.py` | the two changed assertions above, plus the new cases |
| `v12/python/tests/manager/test_attempts.py` | only if §5's absence rule needs an owner-side case |

`worker_manager/attempts.py` is **not** on this list. That part of the pre-work
stands.

## 7. Acceptance — PLAN item 12, unchanged

Prove real provider growth reaches the manager **before completion**; unrelated
outer stderr is not mislabeled; a blocked publisher cannot backpressure a stream
**larger than pipe capacity**; and restart preserves absence or partial state
honestly. Re-run the focused manager/deployment suite and review before 5b.

Pair each positive with the reversal that would catch a vacuous case. "It did
not stall" and "nothing was stamped" both pass trivially against the current
defect, and the production-seam case must fail if the count never crosses.

## 8. What this design does not decide

- **Which candidate**, until §2's experiment is run. That is deliberate.
- Follow, colour, pause, search/filter, retention, native stream expansion and
  raw transcript remain deferred v13 scope, untouched.
- No separate observation instant is proposed; if a future owner wants one,
  §5's recommendation is the thing it would supersede.
