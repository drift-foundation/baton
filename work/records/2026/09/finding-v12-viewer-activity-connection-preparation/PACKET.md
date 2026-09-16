# Viewer activity connection — preparation packet

Prepared by baton.claude, W177937 claim 178694, after owner poke 178688 lifted
the queued-preparation stop hold. **Preparation only.** No product or test file
edited, no test run, no engine or live call, no shared producer edit. All writes
are inside this dossier.

W61599 is **blocked on this Work** (`add_dependency` 178689) and the owner has
assigned the implementation to `baton.tuner` (reroute 178690). This packet is
that tuner's input.

## 1. Headline

**The wiring already exists end to end, and exactly one line ignores it.**

The producer writes a count; `attempts.attempt_activity_of` reads it;
`delegation.py` puts it in the observation; `projection.py` puts it in the
status document under `stage.runtime.activity`. The viewer then throws it away
and prints a constant.

```
job_viewer.py:323        "activity": UNKNOWN,
```

That is the whole defect. **The implementation is a read, a format and a
predicate — not a new backend, not a new reader, not a protocol change.** The
viewer's own first rule stays intact: it still has no second read path.

## 2. Revalidated state

All bytes below were re-read and hashed during this preparation.

| What | Hash | Status |
| --- | --- | --- |
| `v12/python/tools/job_viewer.py` | `093ec72480e2c921ea657b0e63e7235d7dd5e27933762724132310b42447d356` | matches accepted W167896 `candidate-168326.json` |
| `v12/python/tests/tools/test_job_viewer.py` | `bbbc6be5ffc35774654336a41f9d0c36182f013ae53feb3b14203ce0245b476b` | matches |
| `v12/python/JOB-VIEWER.md` | `d319f7813c826970eca6f49a5970f894805288754f31f30999d28d3cfbbb5976` | matches |

**The producer is the ACCEPTED correction, not my original candidate.** All six
W61599 source paths in the tree match `correction-178427/candidate.json`,
independently accepted by `review-2026-09-15T14-06-58Z.md`
(`sha256:975d4ea565eb3eae50e5f053b7677fdeae00a5109f518502331d06ad27a42e90`):

```
v12/worker/claude_agent.py                           bbca3ad5eac9c734…  (corrected)
v12/worker/baton_worker.py                           75ff8ab7d336ce1b…  (corrected)
v12/python/tools/single_worker.py                    0327cc49571f2cb2…  (corrected)
v12/python/src/baton_v12/worker_manager/exchange.py  50cfc38b13221966…  (unchanged)
v12/python/tools/stage_execution.py                  30c4d4fe347697f1…  (unchanged)
v12/python/tools/dogfood_operator.py                 e68dbe4030f95454…  (unchanged)
```

**None of those six is touched by this connection**, and the tuner holds them
under W161234 B. The viewer consumes their output; it does not reach into them.

## 3. The existing chain, named at each hop

| Hop | Where | What it carries |
| --- | --- | --- |
| store | `attempts` columns `activity_bytes`, `activity_at`, both-or-neither | the manager's count and **its own receipt instant** |
| reader | `attempts.attempt_activity_of(store, attempt_id)` | `{attempt_id, bytes_observed, observed_at}`, or `None` for an unknown attempt; **members are `None` for a recorded attempt nobody has observed** |
| observation | `job_manager/delegation.py:989`, member `"activity"` | the same dict, per stage |
| status document | `job_manager/projection.py:703` | `stage["runtime"]["activity"]` — **and `stage["runtime"]` itself is `None` when there is no runtime** |
| viewer | `job_viewer.py:_stage_line` | **discards it and writes `UNKNOWN`** |

**Two absences that are not the same, and the viewer must keep them apart:**

- `runtime` is `None`, or `runtime["activity"]` is `None` → **nobody has looked
  at this attempt.** `unknown`.
- `activity` is a dict whose `bytes_observed` is `None` → **the attempt is
  recorded and has shown nothing yet.** Also `unknown` — `attempt_activity_of`'s
  own docstring is explicit that a zero here "would read as observed, and
  empty", which is a claim this manager does not have.

The producer never writes a zero, so `bytes_observed` is either `None` or a
positive integer. A zero arriving would be a producer defect, and the viewer
should render it `unknown` rather than `0` — it invents nothing either way.

## 4. The display rule, and the one it must not break

`ACTIVITY-DOCUMENT-DESIGN-175025.md` and the accepted
`review-2026-09-15T04-29-53Z.md` pin owner ruling **M174788**: an update
admitted while the operation was live **may arrive after completion**, and its
instant is **manager receipt time** — never evidence of continued provider
activity.

**So the age is only meaningful while the stage is live.** The viewer already
holds the discriminator it needs:

```
documents.TERMINAL_STAGE_STATES = ("changes-requested", "completed", "exceptional")
```

**Proposed rendering, three cases and no fourth:**

| Stage state | `bytes_observed` | Render |
| --- | --- | --- |
| any | `None`, or no runtime, or no activity member | `unknown` |
| **not** in `TERMINAL_STAGE_STATES` | positive | the count **and** the age of `observed_at`, e.g. `1.40 MiB · 4s ago` |
| **in** `TERMINAL_STAGE_STATES` | positive | the count **and the instant, marked historical** — e.g. `1.40 MiB · last at 2026-09-15T13:22:04.117Z` — **never a relative age** |

**A relative age on a terminal stage is the exact misreading this whole Work
exists to prevent.** "4s ago" next to `completed` invites an operator to read a
finished attempt as a live one, and the count keeps ticking up in appearance as
the clock moves while nothing is running. The terminal case therefore shows an
absolute instant, and the word `last`.

**The count is not proof of useful work**, and no rendering may suggest it is.
It is bytes this manager observed; a provider can emit noise and a thoughtful
one can be quiet. M61707 bounds it as diagnostic, and nothing in the viewer may
branch on it.

**Staleness stays the snapshot's, not the activity's.** The viewer's existing
`stale_after`/banner machinery describes how old the *observation document* is.
Activity age is a different clock and must not be folded into it: a fresh
snapshot can carry an old activity instant, and that is a true and useful thing
to show.

## 5. The injected/restored-HOME unknown, preserved

The accepted producer makes activity **`unknown` for the whole operation**
whenever the provider HOME was injected, reused or restored — only a
`tempfile.mkdtemp` this process created has a baseline proved by construction.

For the viewer this needs **no special case and must not acquire one**: an
unknown operation simply publishes nothing, so `bytes_observed` stays `None` and
the existing `unknown` branch renders it. **The tuner must not add a "probably
restored" or "baseline unproved" display**, because the viewer cannot tell that
apart from a provider that has produced nothing yet, and inventing the
distinction would be the viewer reporting a fact it does not hold.

## 6. Exact proposed change boundary

**Three files, all W167896's own, none shared with W61599 or W161234 B.**

| Path | Concrete change |
| --- | --- |
| `v12/python/tools/job_viewer.py` | `_stage_line` reads `stage["runtime"]["activity"]` defensively (runtime may be `None`); one new private formatter turning `{bytes_observed, observed_at}` plus the stage state into the three renderings of §4; the list line and the detail row consume it. Reuse the existing `_duration`/elapsed helper for the live age rather than a second clock. |
| `v12/python/tests/tools/test_job_viewer.py` | `NothingIsInvented.test_activity_is_unknown_until_a_trusted_source_exists` and the model-free completion assertion at the two places that currently require `activity\s+unknown` **change meaning and must be rewritten, not deleted** — their fixtures carry no activity, so they become the "absent stays unknown" cases. Add the cases in §7. |
| `v12/python/JOB-VIEWER.md` | The header and doc currently say "W61599 owns the trusted activity source; until it exists, activity here is `unknown`". That sentence becomes false on the day this lands and must be replaced in the same change — including the module docstring at `job_viewer.py:24-25`. |

**No other file.** Not `projection.py`, not `delegation.py`, not `attempts.py`,
not the six producer paths, not `DEPLOYMENT.md`, no new reader, no schema.

**If the tuner finds the status document does not actually carry the member on
some path, that is a producer-side finding to report — not a reason to add a
second read path in the viewer.** The viewer having no backend is W167896's
first stated rule and this connection does not get to spend it.

## 7. Focused verification, proposed and not run

Deterministic, no engine, no provider, no live execution, using the viewer
suite's existing snapshot fixtures. Selector: `tests.tools.test_job_viewer`.

1. **Absent stays unknown** — no runtime, runtime without an activity member,
   and an activity member whose `bytes_observed` is `None`: all three render
   `unknown`, in both list and detail. (The two existing assertions, rewritten.)
2. **A live stage shows count and age** — a non-terminal state with a positive
   count renders the byte figure and a relative age derived from the snapshot's
   observed instant.
3. **A terminal stage shows count and instant, never an age** — for each of
   `changes-requested`, `completed`, `exceptional`: the absolute instant appears
   and **no relative-age token does**. This is the case that would have caught a
   finished attempt rendered as live, and it is the reason the packet exists.
4. **A zero renders unknown, not `0`** — the producer cannot emit one, so this
   pins the viewer's own honesty if it ever sees one.
5. **No mutation** — the existing no-mutation case is extended to cover the new
   path: rendering activity opens no store, performs no write, and constructs no
   serving factory. The viewer's read verb list stays `refresh`.
6. **Snapshot staleness and activity age stay separate** — a fresh snapshot
   carrying an old activity instant shows the stale banner off and the activity
   instant old, and vice versa.

**Proposed ceiling 60 s under an owning supervisor in its own process group,
TERM 5 s / KILL 5 s, with positive group-absence proof.** No broad suite, no
baseline repair, no historical reconstruction.

## 8. No-mutation guarantees, restated as checkable properties

- The viewer gains **no** store handle, connection, or writer.
- It gains **no** new read path: `stage["runtime"]["activity"]` is already in
  the snapshot it already reads.
- It **branches on nothing**: activity affects rendering only. No refresh
  interval, no refusal, no ordering, no selection depends on it.
- It **derives no liveness**: the only clock it may use for activity is the
  snapshot's own `observed_at` against the activity instant, and only while the
  stage is non-terminal.
- It **invents no count**: absent is `unknown`, and unknown is never `0`.

## 9. Serial handoff

1. **The tuner implements**, per owner reroute 178690: record exact consumer
   paths, implement the bounded packet, then focused independent review at
   `baton.feat`. No producer rewrite, rich UI, broad suites, baseline repair or
   live execution.
2. **The producer bytes are already accepted and released** — correction 178427,
   accepted at 178630, shared files released at 178644. There is nothing left to
   wait for on that side. Revalidate the three viewer hashes in §2 before
   editing, since W161234 B is editing adjacent files under the same tuner.
3. **This unblocks W61599** (`add_dependency` 178689). Only after the viewer
   change is independently accepted may visible counts be claimed delivered;
   until then W61599's own handoff language — "visible counts are not claimed
   delivered" — remains correct.
4. **W177938 follows**, per the owner's stated order.

## 10. What this preparation did not do

No product or test file edited. No test, probe, provider, engine, build,
installation or version-control operation. **New measured verification: 0 s.**
Source reads and hash comparisons are preparation evidence, not executed
acceptance. Nothing protected was opened. All writes are inside this dossier.

Rich follow, sink expansion, colour, pause, search/filter, retention and raw
stream UX remain W39649/v13 material and are not touched here.
