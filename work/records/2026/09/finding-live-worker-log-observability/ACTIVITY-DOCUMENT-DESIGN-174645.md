# Activity document — completed design, second revision

Recorded 2026-09-15 by baton.claude, claim 174645, per owner reroute M174641.
**Design only.** No product or test file edited, nothing executed. Completes
`ACTIVITY-DOCUMENT-DESIGN-174572.md` against
`review-2026-09-15T03-30-15Z.md`. The already-selected optional `activity.json`,
its temp-to-published atomic replacement, its separate parser and count limits,
and the unchanged lifecycle bytes are **retained and not reopened**.

## 0. My source error, corrected first

I wrote that `_scratch` caches the generated scratch and concluded that
`describe` and `work` share it. **That is wrong.** `claude_agent.py:1508-1513`
returns `self._home` **only when the constructor supplied one** — a test seam —
and otherwise calls `tempfile.mkdtemp(...)` and returns it **without storing
it**. Each uninjected call makes a fresh directory.

The per-operation-baseline conclusion happened to be right, but I reached it
from a false premise, and the premise is what a later reader would have trusted.
Two further corrections I accept:

- **`describe` invokes no provider**, so there is no provider state to account
  for there. The publisher is therefore **`work`-only** (§3).
- **A reused `_prepared_home` is not proved empty.** When a home *is* injected,
  prior content can exist, so "the private `.claude` starts empty" is not a
  general fact and must not be the basis of the binding.

## 1. Baseline and monotonic accounting — corrected

**Bind the baseline after preparation and any restoration, immediately before
the actual provider launch.** That is correct whether the home is fresh or
reused, and it replaces the emptiness argument entirely.

**The formula in the previous packet could go backwards.**
`sum(max(0, current - baseline))` drops from 100 to 80 when a file that had
grown is replaced by a smaller one while its baseline stays 0. A count that can
fall is exactly the lie this projection must not tell.

**Corrected accounting:**

- Keep, per observed file, its **identity** (device and inode) and its **last
  observed size** — not just the baseline.
- The operation's reported figure is a **monotonic running total**: on each
  scan, add `max(0, current_size - last_size)` per surviving file of unchanged
  identity, then update `last_size`. A file first seen after the baseline
  contributes its full current size once, then grows incrementally.
- **Freeze on shrink, disappearance or identity change.** Any of the three makes
  the source ambiguous: the running total **stops advancing and is never
  reduced**, and the operation reports *unknown from here* rather than a
  smaller number. It does not resume if the file reappears.
- **The reported figure is this operation's cumulative growth**, and the manager
  owner it feeds is `observe_activity`, whose column is the attempt's cumulative
  total. With one `work` operation per attempt these coincide; if that ever
  stops being true, the publisher must carry the attempt cumulative rather than
  a per-operation figure, because the owner refuses a regression.

**The bounded metadata scan is a proposed observation, not a proof.** I am not
claiming every `*.jsonl` beneath the private home is provider session state;
I am proposing to observe those files' metadata and saying so.

## 2. Compatibility headroom — pinned from source, not left to an experiment

`exchange.py:197` `MAX_EVENT_ENTRIES = 64`, and `:1128` makes an event namespace
holding more than that **unreadable as a whole** — not merely truncated. An old
reader also reports foreign names.

**Pinned accounting:** four lifecycle documents (receipt, `state-describe`,
`state-work`, terminal) **+ `activity.json` + `.activity.json.tmp` = 6**. This
design therefore consumes **2 of 64**, leaving **58** for other staging files
and leftovers.

**The rule that follows:** the publisher may never create more than one
temporary file, because the budget is shared with everything else in that
namespace and overrunning it does not degrade one document — **it makes the
whole observation unreadable**. §3's single-writer exclusion is what keeps this
true, and the implementation must assert the count, not assume it.

## 3. Publisher lifetime, exclusion, and late writes

**One `work`-only publisher.** `describe` runs none.

**Positive exclusion, replacing the previous packet's binding-only argument.**
The review is right that an immutable binding neither stops an abandoned writer
nor expires the *same* completed operation, and that `observe_activity` has no
live-state predicate. So:

- **A single writer slot per attempt, with an explicit owner token.** A new
  publisher may start only when the previous one has **positively resolved** —
  finished, or observed stopped. **No replacement is started while a prior
  publisher is unresolved**; the operation proceeds with **no activity
  publication at all**, which is an acceptable loss because these counts are
  optional.
- **Numeric bounds, stated rather than implied:** at most **one** outstanding
  temporary file; at most **one** publisher per attempt; cadence **1 write per
  second**; stop wait **2 seconds**; after that the writer is abandoned and the
  slot stays **unresolved** — which is what forbids a replacement rather than
  permitting one.
- **Same-operation late writes.** Binding cannot distinguish a late write from a
  live one for the *same* operation, so the **consumer** adds the predicate the
  owner lacks: it ingests a document only while the exchange shows that
  operation **not yet terminal**. Once the terminal document exists, activity
  documents for that operation are **ignored**. That closes the window binding
  alone cannot.
- **Stale temporary files.** A `.activity.json.tmp` older than the stop bound,
  belonging to a resolved-or-abandoned publisher, is **left in place, not
  cleaned up by a reader**, and is removed with the event root at delivery
  teardown. A reader never deletes; §2's budget makes one stale file safe.

**No publisher gates anything.** Not mandatory reads, not provider completion,
not the terminal document, not runtime cleanup.

## 4. Off-loop ingestion — the actual hook and its bounds

The review is right that a synchronous file-and-store read inside the serial
sweep blocks the passes, stages and cleanup that follow it. Resolving this as a
routine engineering choice within scope, as the reroute authorises:

- **The sweep does not read the file and does not write the store.** The
  read-only projection `single_worker.observed_exchange` is unchanged in
  character: it reports what is already known and gains no I/O of its own.
- **A single bounded ingestion worker owned by the composition** — one per
  deployment, not per attempt and not per tick. It holds a **single-slot**
  queue of `(attempt_id, path)` overwritten by the newest request, does the
  file read and the `observe_activity` write off the sweep thread, and is
  started and stopped with the composition that owns it.
- **Bounds:** one worker, one slot, at most one store write in flight, and a
  **finite stop** at composition close. If it is stalled at close it is
  abandoned, and §3's terminal predicate plus `observe_activity`'s own
  repeat/regression rules make any late write harmless.
- **What the sweep does** is enqueue an attempt id when the exchange shows a
  non-terminal `work` operation. Enqueueing is a slot assignment and cannot
  block.

**If implementation finds no composition-owned lifecycle to hang that worker
on**, that is a genuinely different required source boundary and must be
reported with the exact missing hook rather than solved by putting the write
back on the sweep.

## 5. Unchanged from the selected design

The optional `activity.json`; schema `baton.worker-exchange.activity/1`; the
temp-then-rename-**over** pattern with the published file never renamed away;
the separate parser validating `bytes_observed` as an integer in
`[0, 2**53 - 1]` with no existing parser relaxed; lifecycle documents
byte-unchanged; binding on session, attempt, sequence, command and operation;
missing or mismatched activity preserving **unknown or last-observed**;
publishing only a positive total; and `observe_activity` unchanged.

## 6. Path ownership

`v12/worker/claude_agent.py` (baseline binding and monotonic file accounting),
`v12/worker/baton_worker.py` (work-only publisher, slot, exclusion, bounds),
`v12/python/src/baton_v12/worker_manager/exchange.py` (document, parser,
vocabulary entry, entry-count assertion),
`v12/python/tools/single_worker.py` (read-only projection; enqueue hook; the
ingestion worker's ownership), `v12/python/tools/dogfood_operator.py`
(`_Channel` stops being the source). `worker_manager/attempts.py` unchanged.

Tests: `tests/manager/test_claude_agent.py`, `tests/manager/test_exchange.py`,
`tests/tools/test_single_worker.py`, `tests/tools/test_dogfood_operator.py`;
`tests/job_manager/test_exchange.py` or `tests/manager/test_attempts.py` only
where composition or owner behaviour actually changes.

## 7. Acceptance

Carrying forward the previous list, plus the review's new controls:

1. Growth before completion at the normal adapter boundary — **labelled
   simulated-provider coverage**.
2. Unrelated stderr and zero EOF create no activity; repeats do not move the
   receipt time; never-observed stays unknown; reopen preserves last-observed.
3. Exact binding and hostile counts, refused by the new parser.
4. **Same-operation late write after the terminal is ignored** — the case
   binding alone could not cover.
5. **A blocked publisher does not delay another stage's pass or cleanup**, with
   output larger than pipe capacity.
6. **No replacement publisher while a prior one is unresolved**, and the
   attempt simply publishes nothing.
7. **Stale temporary file**: one may exist, no reader deletes it, and the
   namespace stays within `MAX_EVENT_ENTRIES` — asserted, not assumed.
8. **Truncation, replacement, disappearance and identity change freeze the
   total**; it never falls and never resumes.
9. Both compatibility pairings, including the pinned headroom of §2.

**A counter is not proof of useful work.**

## 8. Scope

Follow, sink expansion, colour, pause, search/filter, retention and raw stream
UX remain W39649/v13 material. Nothing here reopens the selected document,
write pattern, parser or lifecycle bytes.
