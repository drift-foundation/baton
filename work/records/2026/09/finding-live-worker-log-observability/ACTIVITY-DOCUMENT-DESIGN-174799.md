# Activity document — completed design, third revision

Recorded 2026-09-15 by baton.claude, claim 174799, per owner reroute M174788.
**Design only.** No product or test file edited, nothing executed. Completes
`ACTIVITY-DOCUMENT-DESIGN-174645.md` against
`review-2026-09-15T03-50-47Z.md`. The selected `activity.json`, its parser,
atomic replacement and unchanged lifecycle bytes are **retained, not reopened**,
as are the accepted corrections: scratch deduction, work-only baseline,
monotonic freeze counting, numeric publisher cadence/stop, and the 64-entry
accounting.

Routine numeric values below are **chosen here** as the reroute directs; none
needs another approval.

## 1. Delayed final counts — the owner's selected semantics, pinned

The review is right that a terminal precheck cannot reject a **greater-total**
write that stalls in the store until after the terminal, and that binding alone
does not decide this. **M174788 selects the honest semantics rather than a
revocation boundary:**

> An update admitted while the operation was live **may arrive after
> completion**. Its timestamp is **manager receipt time** — the instant this
> manager recorded the observation — and is **never** evidence of continued
> provider activity, and **never** authority to change terminal state.

What follows, and what the implementation must hold:

- `observe_activity` keeps its existing rule: a greater total advances both
  columns, an equal one advances neither, a smaller one refuses. **Unchanged.**
- The terminal precheck of the previous revision is kept as a **cheap early
  skip**, not as a correctness boundary. It avoids most late work; it is not
  claimed to eliminate it.
- **The projection's own words carry the meaning.** `activity_at` is the
  manager's receipt time for the latest observed activity. Where a stage is
  terminal, a reader must not render that instant as liveness. **The viewer
  therefore reports activity as historical once the stage is terminal**, which
  is the display rule this semantics requires and the only user-visible change
  it implies.
- **No terminal state is ever changed by an activity update.** Nothing in this
  path writes an ending, a disposition, an output axis or a cleanup axis.

## 2. Ingestion ownership — the selected `stage_execution.py` boundary

**Confirmed composition facts.** `single_worker.worker_operations` is **per
pooled worker**, so it cannot own a per-deployment worker.
`stage_execution.operations_from` (`:5430`) composes the deployment, and
`StageExecution.release` (`:4309`) drives `_closers` (`:4321`), which already
yields named closers and collects their failures into one refusal. That is the
deployment-owned lifecycle the ingestion worker needs, and **M174788 selects
adding this boundary to `v12/python/tools/stage_execution.py`.**

**The design:**

- **One ingestion worker per deployment**, constructed in `operations_from`
  beside the other deployment-owned handles, and yielded from `_closers` as
  `"the activity ingestion worker"` so its shutdown is reported through the same
  failure list as any other handle.
- **Its own `ControlStore` handle, opened on its own thread**, for the reason
  `_activity_observer` already records: a `sqlite3` connection belongs to the
  thread that opened it. It never shares the serving handle.
- **Pooled and bootstrap both covered by construction**, because ownership is at
  the deployment rather than the worker: a pooled deployment gets one worker for
  all its pooled workers, and a bootstrap deployment gets one for its single
  worker. Neither composes its own.
- **The enqueue hook is `single_worker.refresh_runtime`** — the serving loop's
  one runtime read, which already runs per tick on the serving path and is
  serving-only. It enqueues; it does not read the file and does not write.

**Trusted enqueue binding.** The hook enqueues a tuple the worker can trust
without re-deriving it: `(attempt_id, event_root, session, sequence_id,
command_digest, operation, operation_id)`, taken from the delivery the manager
itself composed. The worker **re-reads** the document and accepts it only if all
seven match. A document naming anything else is discarded unread.

**Exclusion across repeated composition.** A deployment closed and recomposed
gets a **new** worker; the old one is stopped by `_closers` first. If a previous
worker has not resolved, the new composition **starts none** — the deployment
runs with no activity ingestion, which is acceptable because these counts are
optional — and `_closers` reports the unresolved handle rather than hiding it.

## 3. Numeric limits — chosen here

| Limit | Value | Why this one |
| --- | --- | --- |
| scan depth beneath the private `.claude` | **4** | deep enough for a vendor `projects/<slug>/<file>` shape with room to spare, shallow enough to bound cost |
| entries examined per scan | **256** | far above any plausible session count; exceeding it yields **unknown**, not a sample |
| tracked file identities | **64** | one turn does not write dozens of session files; exceeding it yields **unknown** |
| `bytes_observed` ceiling | **2**53 − 1** | the integer range the parser already validates |
| publisher cadence | **1 s** | unchanged |
| publisher stop wait | **2 s** | unchanged |
| outstanding temporary files | **1** | unchanged; §2 of the prior revision pins the 64-entry budget |
| ingestion worker stop wait at composition close | **2 s** | matches the publisher, so neither side waits on the other |
| enqueue slot depth | **1** | newest request overwrites; enqueue cannot block |

**Overflow is always `unknown`, never a partial answer.** A scan that exceeds
depth, entries or identities stops and reports unknown for the rest of the
operation. It never samples, never estimates and never reports a smaller total.

## 4. Nonblocking baseline

Binding the baseline must not delay the provider launch. So:

- The baseline scan runs **before** the provider process is started, and is
  bounded by §3's limits, so its cost is fixed rather than proportional to
  whatever is on disk.
- **If the baseline scan fails or exceeds a limit, the operation proceeds with
  no activity publication at all** — activity stays `unknown`. It is never a
  provider failure, never a refusal, and never a reason to delay the launch.
- The provider launch does not wait on the publisher's first write.

## 5. Safe staging

- The temporary file is created **exclusively** — `O_CREAT | O_EXCL` — and
  **`O_NOFOLLOW`**, so an existing entry or a symlink is never written through.
- **If the exclusive create fails, the publisher suppresses this write** and
  tries again at the next cadence tick. It does not unlink, truncate or
  overwrite a file it did not create.
- A stale temporary file from an abandoned writer therefore **suppresses
  publication rather than being cleaned up by anyone**, which is the safe
  direction: at most one exists, the 64-entry budget tolerates it, and the
  delivery teardown removes the event root wholesale.
- The published file is still replaced by rename **over** it, never renamed
  away.

## 6. Path ownership

`v12/worker/claude_agent.py`, `v12/worker/baton_worker.py`,
`v12/python/src/baton_v12/worker_manager/exchange.py`,
**`v12/python/tools/stage_execution.py`** (newly selected: the ingestion
worker's construction and its `_closers` entry),
`v12/python/tools/single_worker.py` (read-only projection; the
`refresh_runtime` enqueue hook), `v12/python/tools/dogfood_operator.py`.
`worker_manager/attempts.py` unchanged.

Tests: `tests/manager/test_claude_agent.py`, `tests/manager/test_exchange.py`,
`tests/tools/test_single_worker.py`, `tests/tools/test_dogfood_operator.py`, and
**`tests/tools/test_stage_execution.py`** for the composition boundary —
construction, the `_closers` entry, no-replacement across recomposition, and
bounded shutdown.

## 7. Acceptance

Carrying the prior list, plus:

1. **A delayed greater-total update after the terminal is recorded**, and the
   viewer renders it as historical rather than as liveness — the owner's
   selected semantics, asserted rather than assumed away.
2. **The ingestion worker is constructed once per deployment and released by
   `_closers`**, with its failure surfacing in `release`'s refusal list.
3. **No replacement worker across recomposition while a prior one is
   unresolved**, and the deployment simply ingests nothing.
4. **Overflow of depth, entries or identities yields unknown**, never a partial
   or smaller total.
5. **A failed baseline leaves activity unknown and does not delay the launch.**
6. **Exclusive staging:** an existing or symlinked temporary path suppresses the
   write and nothing is unlinked or overwritten.
7. Everything already listed: growth before completion at the normal adapter
   boundary (**simulated-provider coverage**), no false activity from stderr or
   zero EOF, repeats not moving receipt time, unknown preserved, both
   compatibility pairings within the 64-entry budget, hostile counts refused,
   blocked publisher not delaying another stage, and truncation/replacement
   freezing the total.

**A counter is not proof of useful work.**

## 8. Scope

Nothing here reopens the transport selection, the parser, the write pattern or
the lifecycle bytes. Follow, sink expansion, colour, pause, search/filter,
retention and raw stream UX remain W39649/v13 material.
