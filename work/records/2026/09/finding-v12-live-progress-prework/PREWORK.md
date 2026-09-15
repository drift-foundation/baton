# W61599 minimum live-progress correction — implementation handoff

Advisory Work W174051, claim 174087, baton.claude via baton.impl.
**Read-only pass. Nothing was executed:** no test, probe, provider, model,
engine, build, Git mutation or worker. No product, test or original dossier was
edited. Advice for the future W61599 implementer; **not acceptance**, and it
grants no implementation scope.

Baseline: live tree, 2026-09-15, under claim 174087. Provisional.

**Scope already fixed and not reopened:** the minimum subset is the
2026-09-14 selection (W165782 claim167877) — positive provider-safe native
session growth and a manager-owned last-activity instant, with the outer-stderr
misclassification, synchronous publisher backpressure and zero-byte EOF stamp
corrected, bounded/coalescing publication, and honest absence/partial state
across restart. Items 5b/6/7/9 — follow, colour, pause, search/filter,
retention, native stream expansion, raw transcript — remain deferred v13 scope
and are **not** revived here.

## 1. The current activity source, traced

    tools/dogfood_operator.py:4177  _Channel.__init__(argv, *, seconds, observe)
    tools/dogfood_operator.py:4198  _Channel._drain
    tools/dogfood_operator.py:4229  _Channel._report(final=False)
    tools/dogfood_operator.py:4288  _activity_observer(given)
    src/baton_v12/worker_manager/attempts.py:427  observe_activity(store, *, attempt_id, bytes_observed)

`_drain` reads `self._process.stderr` — **the exec process's stderr**, i.e. the
outer channel — counts every chunk into `self._seen`, and calls `_report()`.
`_report` calls `self._observe(self._seen)` synchronously, swallowing any
exception. `_activity_observer` opens a `ControlStore`, calls
`observe_activity`, and closes, per publication.

`observe_activity` writes under
`AND (activity_bytes IS NULL OR activity_bytes < ?)`, then re-reads and refuses
a regression. That clause is what makes a repeated total not move the instant —
correct and deliberate.

## 2. The four selected corrections, against read test bodies

I read the case bodies before saying anything was missing, and the picture
differs item by item. Distinguishing implementation, test existence, recorded
passing evidence and actual gap:

### 2.1 Outer-stderr misclassification — **defect confirmed, and the current behaviour is PINNED by an existing test**

`_drain` counts the exec process's stderr. Unrelated engine or exec noise is
therefore published as worker activity.

**This is the finding most worth knowing before planning:**
`tests/tools/test_dogfood_operator.py:7094
test_every_byte_is_counted_including_the_ones_discarded` asserts exactly the
present behaviour — every byte of that stream counts, including bytes past
`_KEEP`. The class docstring at `:7073` states the same intent.

**So the correction is not purely additive.** It changes an existing assertion,
and the implementer should name that method and its changed expectation in the
handoff before editing, as the standing test authority expects. A plan that
assumed only new cases would discover this mid-slice.

### 2.2 Synchronous publisher backpressure — **demonstrated gap**

`_report` guards against an observer that **raises**; it does not guard against
one that **blocks**. `self._observe(self._seen)` is a synchronous call on the
drain thread, and `_activity_observer` opens, writes and closes a SQLite handle
inside it. A busy or locked store stalls the drain — which is the hang the
drain exists to prevent.

**Covered:** `:7133 test_an_observer_that_raises_never_wedges_the_session`.
**Not covered:** an observer that is merely slow. I read that case; it raises,
it does not block. This is the bounded/coalescing publication the ruling asks
for, and the gap is demonstrated rather than inferred.

### 2.3 Zero-byte EOF stamp — **demonstrated gap, confirmed at the owner**

`_drain` calls `self._report(final=True)` unconditionally at end of stream, even
when `self._seen == 0`. At the owner, `bytes_observed=0` against a row whose
`activity_bytes IS NULL` satisfies the UPDATE clause, so it **writes
`activity_bytes = 0` and a fresh `activity_at`.**

An operator then reads "0 bytes, updated just now" for a worker that produced
nothing — precisely the "freshness about nothing" the 2026-09-01 implementation
decision says the both-or-neither column pair exists to prevent.

**Covered:** `tests/manager/test_attempts.py` has first-observation, growing,
repeated, backwards, negative and no-attempt cases — I read them.
**Not covered:** a **zero** first observation.
`test_the_first_observation_publishes_the_count_and_the_instant` uses 4096, and
`:7117 test_the_end_of_the_stream_is_always_published` uses a producing
program. No body exercises the zero path.

**A design question the implementer must answer rather than assume:** whether
the fix belongs in the caller (do not publish a final zero) or at the owner
(refuse or ignore a zero first observation). I recommend the caller, because
`observe_activity` accepting 0 is coherent for a stream that genuinely produced
nothing after having produced something — but this is a recommendation, not a
ruling, and the owner's `both-or-neither` invariant deserves the decision.

### 2.4 Honest restart / unknown and partial state — **partly covered; the rest uncertain**

**Covered:** `tests/manager/test_attempts.py:2647
test_an_unobserved_attempt_is_not_an_empty_one` distinguishes never-observed
from zero. `tests/tools/test_job_viewer.py:123
test_activity_is_unknown_until_a_trusted_source_exists` and `:986` hold the
viewer to `activity unknown`, with `:662` exercising an explicit `None`.
`tests/job_manager/test_status.py:226` projects a running stage's activity.

**Uncertain, and labelled so:** I did not find a case that carries activity
state across a manager restart — i.e. that the durable columns survive and are
still read as partial rather than as fresh. I did not exhaustively search every
module, so I am recording this as **uncertain rather than commissioning work**.
The implementer should confirm before adding a duplicate.

## 3. Smallest correction paths

**Source (1 file, 2 regions):** `tools/dogfood_operator.py`
- `_Channel._drain` / `_report` — the activity source, the bounded/coalescing
  publication, and the end-of-stream condition.
- `_activity_observer` — if publication moves off the drain thread, this is
  where the handoff to it belongs.

**No manager change is required** for 2.1, 2.2 or 2.4. `observe_activity`
already refuses regressions, ignores repeats and keeps the column pair
consistent. Item 2.3 *may* touch it, depending on the design decision above.

**Tests (2 files):** `tests/tools/test_dogfood_operator.py` — the existing
`TheChannelReportsHowMuchItSawAndNeverWhatItSaw` and
`TheDeploymentPublishesTheCountAndClosesWhatItOpened` classes, where 2.1's
changed expectation and 2.2/2.3's new cases belong; and
`tests/manager/test_attempts.py` only if 2.3 is solved at the owner.

**Preserve unchanged:** the length-only crossing (a count cannot carry a
credential), the `_KEEP` bounded window and W39357's disposal of those bytes,
the repeated-total rule, the regression refusal, and the viewer's `unknown`.

## 4. Proposed focused validation — not executed

Using the existing deterministic seams — the `_Channel` fixture at `:7087`
which runs `sys.executable -c <program>`, and the fake-observer pattern at
`:7211`. **No live model or engine**, as the ruling states.

1. **Unrelated stderr is not activity.** A program writing to the outer stderr
   without provider progress publishes no growth. This is the case that
   replaces the pinned assertion in 2.1.
2. **Genuine growth is positive and monotonic before completion** — retaining
   the existing monotonic and final-total assertions.
3. **A slow observer never stalls the drain.** Observer sleeps; assert the
   drain keeps reading and the session ends within its bound. Pair it with the
   existing raises case rather than replacing it.
4. **A stream that produced nothing leaves no stamp.** Assert `activity` stays
   the never-observed shape — not `0` with a fresh instant.
5. **Restart keeps partial facts honest**: reopen the store and assert the
   durable pair reads as last observed, with the viewer still able to say
   unknown when there is nothing.

For 3 and 4 especially, pair each positive with the reversal that would catch a
vacuous case — "it did not stall" and "nothing was stamped" are both easy to
assert in ways that would pass against the current defect. Supervise
experiments as well as final runs and record failures too.

## 5. Reconciled rulings — no new decisions requested

- The **minimum-outcome gate clarification** already supersedes the earlier PLAN
  assumption that every rich-stream item must finish before W61599 can close.
  Closing the narrowed outcome must **name** the deferred items without
  asserting their implementation.
- **Publication cadence** (`_ACTIVITY_SECONDS = 1.0`, always one at end of
  stream) is the drain loop's own recorded resource decision. Bounded/coalescing
  publication should preserve that meaning rather than re-decide it.
- The only genuinely open question I found is 2.3's caller-versus-owner
  placement, and I have given a recommendation rather than asking for a ruling.

## 6. Assumptions and limits

- I ran nothing. Behavioural claims come from reading source, test bodies and
  recorded decisions; structural claims are file/symbol citations.
- §2.4's second half is labelled uncertain on purpose.
- I read `FINDING.md` through the 2026-09-14 selection and the implementation
  decisions of 2026-09-01. I did **not** read
  `review-2026-09-01T14-24-19Z.md` in full or `PLAN.md`'s item list; the
  implementer should, and my item numbering follows the FINDING's own summary.
- Nothing here changes the original Work, its route, its parked state or any
  gate, and none of it is a new release prerequisite.


---

# CORRECTION — claim 174145, after owner reroute 174118

**Two claims in the report above were wrong and one scope statement was
unsupported.** I wrote §6 saying I had not read
`review-2026-09-01T14-24-19Z.md` in full or `PLAN.md`'s item list — and then
made scope and coverage claims that reading them would have prevented. Having
now read both, the corrections follow. The original text is left intact above
as history; this supersedes it.

## A. The one-source-file scope claim was unsupported — it is wrong

§3 said "**Source (1 file, 2 regions):** `tools/dogfood_operator.py`" and "no
manager change is required". That cannot be right, because the correction the
review requires is not a change to *how* the existing stream is counted — it is
**wiring a different stream, which is produced inside the container**.

`review-2026-09-01T14-24-19Z.md` [P1] traces it exactly:

- `ClaudeAgent._ran_provider` (`v12/worker/claude_agent.py:1778`) owns a private
  pipe for provider **stdout** and reads it **inside the container**, bounded,
  drained on its own thread with `PROVIDER_DRAIN_SECONDS`.
- Provider **stderr is `subprocess.DEVNULL`** and was never opened
  (`claude_agent.py:1770`, `:1786`).
- **Neither `baton_worker.py` nor `dogfood_entry.py` writes progress to stderr.**

So the outer `docker exec` stderr that `_Channel` counts is not, and cannot
become, the native session stream. **A provider-safe count has to originate
inside the container and cross a closed worker/deployment seam to the manager.**

### Exact required paths, and what is genuinely unresolved

**Required, worker side (inside the container):**
- `v12/worker/claude_agent.py` — wherever the chosen native source is observed.
  `_ran_provider` already drains provider stdout and already counts what it
  reads, so a cumulative length exists there today; what does not exist is a way
  to emit it incrementally.
- `v12/worker/baton_worker.py` — the worker entry that would carry a periodic
  count out, if the seam is the worker protocol rather than a file.

**Required, deployment side:**
- `v12/python/tools/dogfood_operator.py` — `_Channel`/`_report` stop being the
  activity source and become (at most) the transport for one; `_activity_observer`
  keeps the manager crossing.

**Not required:** `worker_manager/attempts.py`. `observe_activity` already
refuses regressions, ignores repeats and keeps the column pair consistent. That
part of §3 stands.

**Explicitly unresolved producer facts — the review says these must be proved,
not assumed:**
1. **Which native source.** The review states the current final JSON stdout *"is
   not necessarily an incremental native session"*, while *"its private native
   JSONL was the live source observed in W52821"*. The provider home is prepared
   at `claude_agent.py:1941 _prepared_home` with
   `PROVIDER_HOME_STATE = ".claude"` under the per-turn scratch — that is where
   a native JSONL would live, but **I did not confirm that any such file is
   written during a turn**, and neither did the review. It says the
   implementation *"must prove the chosen source changes during a real turn"*.
2. **Which seam carries it out.** `dogfood_entry.py` is the documented injection
   seam (`dogfood_operator.py:960`, `WORKER_PROGRAM` at `:964`), but whether the
   count travels over the worker protocol, a bounded stderr line, or a
   container-private file read by the manager is undecided in every document I
   read.
3. **Whether reading it stays content-free.** A length crosses safely by
   construction; a file offset or line count derived from native JSONL must be
   derived **inside** the container so no transcript byte leaves it. This is the
   raw-content exclusion, and it constrains option (1) rather than being a
   separate task.

These three are the "explicitly unresolved producer facts" the reroute asks for.
I am naming them rather than proposing a design, because the review makes
proving the source a precondition and I ran nothing.

## B. The zero-byte case IS pinned by an existing test — I said it was not

§2.3 said "**No body exercises the zero path.**" That is wrong.

`tests/tools/test_dogfood_operator.py:7158
test_a_silent_worker_is_observed_as_silent_and_not_as_unobserved` runs
`import sys` as the child and asserts `seen == [0]`. Its docstring argues the
position deliberately: *"Zero is a fact: this manager watched the stream and it
produced nothing."*

The review had already said so — [P2]: *"The added test explicitly expects a
silent worker to publish `[0]`."* I missed it because I read the manager-side
cases and two of the channel cases rather than the whole class.

**This changes the character of item 2.3.** It is not an uncovered path; it is a
**recorded disagreement between two positions**, both argued:

- the test's: zero-is-a-fact, distinguishable from never-observed;
- the review's [P2]: `activity_at` is defined as the instant of latest
  *activity*, the writer says a repeat is not activity, so a zero-byte EOF must
  not freshen the age.

The review's required correction — *"either leave the projection absent until
positive growth, or record a separate ruled observation instant distinct from
latest activity"* — resolves it, and PLAN item 11 pins the same: *"preserve
absence until positive activity unless a separate observation instant is
explicitly ruled."*

So **both** items 2.1 and 2.3 change existing assertions. That is the scope fact
to carry into planning, and my report had it for only one of them.

## C. Over-escalated decisions — withdrawn

§2.3 asked the owner to decide caller-versus-owner placement, and §5 framed it
as "the only genuinely open question". The reroute is explicit: **caller-versus-
owner placement and scoped test changes do not require another owner gate.**
Withdrawn. PLAN item 11's "unless a separate observation instant is explicitly
ruled" is the only place a ruling is contemplated, and only if the implementer
chooses that branch over absence-until-growth.

## D. Corroboration the report lacked, now recorded

The review's [P1] backpressure finding has a **measured independent
reproduction** I did not have:

```text
poll_while_observer_blocked None first_total 4096
ending 0 final_total 2000000 calls 2
```

A blocking observer and a child writing 2,000,000 stderr bytes left the child
running with the pump stopped at its first 4,096-byte report. The review also
names the mechanism precisely: `ControlStore.open` configures a **5,000 ms busy
timeout**, so a busy store can stop the pump for five seconds per attempted
report, and *"a collaborator that hangs rather than raises can stop it
indefinitely."* My §2.2 reasoning was right; this is the evidence for it.

The review's required correction is sharper than mine: *"the byte-drain path may
only update bounded in-memory state. Publish from an independent,
bounded/coalescing path whose blocked or failed store operation cannot stop
reads, session completion, or teardown."*

## E. What stands from the original report

- §1's source trace of `_drain`/`_report`/`_activity_observer`/`observe_activity`
  and the `activity_bytes IS NULL` mechanism.
- §2.1's finding that the outer-stderr behaviour is pinned by
  `test_every_byte_is_counted_including_the_ones_discarded` — now joined by B.
- §2.2's backpressure gap, corroborated by D.
- §2.4's coverage reading, and its uncertain label.
- The preserved invariants: raw content never crosses, the `_KEEP` window and
  W39357's disposal, the repeated-total rule, the regression refusal, the
  viewer's `unknown`.
- §4's validation cases, with case 4 re-aimed: it must assert the **ruled**
  outcome (absence until positive growth, or a separate instant), replacing the
  existing `[0]` assertion rather than adding beside it.

## F. Corrected acceptance, per PLAN item 12

Item 12 states it directly, and it is the right list:

> Prove real provider growth reaches the manager **before completion**,
> unrelated stderr is not mislabeled, and a blocked publisher cannot
> backpressure a stream **larger than pipe capacity**. Re-run the focused
> manager/deployment suite and review again before item 5b.

The production-seam case the review requires — driving a real adapter through
the worker entry until a native observation reaches `attempt_activity_of` before
the turn ends — is the one my §4 did not have, because I had not read the review.

Read-only throughout this correction: no test, probe, engine, model, Git
mutation or worker. Zero measured verification seconds.
