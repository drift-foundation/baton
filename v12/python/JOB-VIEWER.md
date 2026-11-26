# The read-only Job viewer

`tools/job_viewer.py` shows what V12 is running. It is the smallest thing that
fixes "parallel Jobs are invisible", and it is deliberately not more than that.

## Running it

The viewer reads the status document the Job Manager already publishes, so the
ordinary invocation is two commands:

```
python3 tools/job_manager.py --store /path/to/jobs.sqlite \
    --incarnation <incarnation> --authority-uuid <uuid> status > status.json
python3 tools/job_viewer.py --status status.json
```

One Job in detail:

```
python3 tools/job_viewer.py --status status.json --job job-a
```

One published artifact, bounded and read once:

```
python3 tools/job_viewer.py --status status.json \
    --job job-a --stage job-a/implementation --artifact result
```

Refreshing: `--ticks N` performs N bounded reads `--interval` seconds apart
(default 1.0, one tick; the interval must be finite and greater than zero).
Re-run the `status` command on the same cadence and the viewer follows the
file. There is no daemon and no serving process here.

**Publish the status document atomically.** Write to a temporary file beside
it and rename — a plain `>` redirection truncates in place, and the viewer can
catch it mid-write. It survives that (see disconnection below) but it will
report a refusal it did not need to see.

## Seeing live state, not just what was submitted

`job_manager ... status` **without** `--control` reads submitted and recorded
Job state and marks itself `canonical: false` — the viewer renders that as "the
manager was NOT read". That is honest, and it is not the same as observing what
is running. For the canonical read-only observation, pass the manager control
store, and add `--observe` for the durable exchange read:

```
python3 tools/job_manager.py --store /path/to/jobs.sqlite \
    --incarnation <incarnation> --authority-uuid <uuid> \
    status --control /path/to/control.sqlite \
    --observe tools.stage_execution:observing_factory \
    > status.json
```

`observing_factory` reads its deployment document from
`BATON_V12_STAGE_EXECUTION_CONFIG`. It is the **observation** factory — not
`tools.stage_execution:factory`, which is the serving one and would act.

`--observe` reconstructs the attempt's durable launch and exchange files and
therefore requires `--control`; the command refuses the combination rather than
silently downgrading it. Note the runtime axis in a status document is as fresh
as the serving loop that last advanced the store — `status` performs no runtime
refresh, because that would record what it saw, and a read that mutates the
control store is not a read.

## What it shows

- Every Job in the snapshot, with its phases and exact stage/work identities.
  Only admitted attempts expose their attempt, offer and episode identities.
- `duration`, computed **only from recorded source times** — the attributed
  provider invocation's own `started_at` and `ended_at`. It says `running Ns`
  only while no ending is recorded. See below.
- `activity` — the bytes this manager has **observed** of the worker's
  native session stream, and when it received them; `unknown` where it
  has observed nothing. See below.
- Held, failed and operator-action reasons, including which stages a blocked
  stage is waiting on, and — for a failed stage — the ending the **worker
  itself declared**, when the manager sealed one. See below.
- Frozen output artifacts with their sizes and manager-supplied locators, or
  an explicit `unavailable`.

## What it will not do, and why

**It performs no act.** No submit, claim, cancel, serve, reconcile or clean;
no serving factory is constructed. Refresh reads — that is the whole verb list.
An operator surface that could act is a control plane, and this one was asked
not to be. A test walks the module's identifiers (not its prose) to hold this.

**It has no second backend.** `job_manager/projection.py:status` is the read
path. There is no SQL, no projection and no observer here. A viewer with its
own reader would be a second answer to "what is running", and the two would
disagree on the day it mattered.

## Why a failed stage used to say only `cause unknown`

A stage reads `failed: stage ended exceptionally; cause unknown` when nothing
in the snapshot says what happened. That sentence used to cover two different,
*host-known* endings: a provider turn that hit its bound, and a candidate whose
own verification failed. Both were sealed in the frozen result and neither
reached a line.

The diagnostic producer now composes a **worker-declared axis** beside the
cause (`attempt_diagnostics.worker_declaration`), and both views read it:

```text
  implementation: exceptional; worker declared unable: the provider did not
    finish (provider timed out) at a 1h00m provider bound (job-default);
    verification not attempted
```

Three rules hold that line honest, and they are the reason it is a separate
axis rather than a cause:

- **A declaration is not a cessation.** It says what the worker answered and
  what this manager sealed of it. It never says a container stopped, who
  stopped it, or that anything did; `cause`, the explicit `unknown` and the
  absent-record list are unchanged beside it, and a manager cancellation or
  revocation keeps reporting itself.
- **A declaration is not an acceptance.** `verification ended 0` is the
  worker's own command reporting on itself — not a review, not a verdict and
  not a merge.
- **Only evidence that binds is read.** The typed members come from the
  worker's `result.json` *inside the frozen candidate tree*, read against the
  byte count and content digest this manager measured when it sealed the tree,
  and against an artifact identity that names this exact attempt. Missing,
  changed, foreign or unreadable evidence leaves the members `unknown` with a
  bounded reason — the sealed disposition beside them still answers. The
  worker's prose `recap` is never parsed, and no path, locator or provider
  message reaches a line: every rendered word is a closed vocabulary value, an
  integer in a declared range or a boolean.

Only a sealed `unable` disposition speaks here. `completed`, `plan-rejected`
and `cancelled` render exactly as they did.

`baton-v12-stack attempt-diagnostics <status.json>` reports the same axis
member by member with its provenance, under the same positive allowlist as
every other axis.

**It invents nothing.** Every value comes from the snapshot or is spelled
`unknown`. The tempting thing for a viewer is to compute a plausible number
when a real one is missing — elapsed from the wall clock, activity from the
fact that polling returned — and each of those reports the *viewer's* behaviour
as if it were the *Job's*.

**Staleness is about the observation, not about the read.** A snapshot carries
two clocks: when this program received the bytes, and when the manager actually
looked. Re-reading an unchanged document does not make it fresher, and the view
goes `!! STALE` once the *observation* reaches 15 seconds. The shared status/monitor threshold is inclusive and independent of
refresh
interval. File publication age is checked as well as source observation age.

**Activity is the manager's observation, and its instant is the manager's
receipt time.** W61599 owns the trusted provider-safe source; this view reads
what the status document already carries at `runtime.activity` and adds no
reader of its own.

Three renderings and no fourth:

- nothing observed — no runtime, no activity member, or a recorded attempt with
  no count — is **`unknown`**. A known zero is displayed as `0 B`. Counts
  must name the stage current attempt; a foreign attempt is unknown.
- a **live** stage shows the count, and `observed Ns ago` beneath it.
- a **terminal** stage — `completed`, `changes-requested`, `exceptional` —
  shows the count, and `last at <instant>` beneath it, **never a relative age**.

The count sits in the fixed-width column and the timing goes on its own
continuation line, as `reason` already does:

```text
  implementation   completed        elapsed 0s       activity 1.40 MiB job-a/implementation
      activity last at 2026-09-15T13:22:04.117Z
```

That is a correction rather than a preference. With both on one line the
ordinary 100-column list cut the end of the timestamp **and the entire stage
id**, on ordinary valid counts, in the renderer the plain CLI uses — and the
stage id is the thing an operator opened the list to copy somewhere else.

**A count this view cannot hold is `unknown`.** Accepted counts are bounded by
the producer's own domain (`0 < n ≤ 2**53 - 1`) *before* any conversion, because
the conversion is what fails: a status document carrying `bytes_observed:
10**400` is valid JSON well inside the input bound, and formatting it raised
`OverflowError` past the last-good-snapshot handler. The trusted producer cannot
emit such a value; this is about what a consumer must survive.

That last distinction is the point rather than a detail. Owner ruling M174788
makes the instant the moment *this manager recorded an observation*, and an
update admitted while the operation was live may arrive after it completed. A
relative age beside `completed` invites reading a finished attempt as a running
one, and it gets worse with time: the apparent freshness improves as the clock
moves while nothing is running.

## Why a frozen duration does not say `running`

The worker records the provider **process's** own `ended_at` when that process
exits, and *then* runs its verification command. Between those two facts the
invocation duration has stopped moving while the stage is genuinely still
open — and every shared surface printed `running 15s`: a frozen figure under a
live word, getting more convincing as the clock moved.

The label follows the invocation and nothing else:

```text
  implementation                    running 30s      activity 1.40 MiB job-a/implementation
      provider timeout in 30s

  implementation                    provider ran 15s activity 1.40 MiB job-a/implementation
      provider invocation ended after 15s; this stage has not ended
      stage timeout in 1m00s
```

- an invocation with **no recorded ending** reads `running Ns`, and the figure
  moves with the manager's own observation clock.
- a **recorded ended** invocation reads `provider ran Ns`, past tense and
  naming the provider rather than the stage. Under a stage that has not ended
  it also carries one sentence saying exactly that, on its own continuation
  line so the fixed columns keep the stage id.
- timing that is absent, malformed, in the future, stale or attributed to
  another attempt reads `duration unknown`. A planned phase also has unknown
  duration; absence of execution evidence never means `not started`.

`provider ran Ns` is a claim about a **process**. It does not say the stage or
the Job ended, completed, succeeded or was accepted — the state, timeout,
reason and activity axes beside it report what they always did, and an ended
process stops limiting the stage, so the stage's own admitted deadline is what
remains. `just status`, the viewer list and the viewer detail print the same
words from the same interpretation (`tools/job_observation.py`), because a
surface that composed its own label is one that can disagree with the other
two on the day it matters.

**A count is not proof of useful work** (approver ruling M61707). Repeated noise
grows it, a long quiet model call leaves it unchanged, and nothing in this
program — refresh, refusal, ordering or selection — branches on it. The viewer
does not edit the provider.

**It does not hide its own age.** A snapshot is exactly as fresh as the moment
it was observed, and the view shows both the manager's `observed_at` and how
long ago this program read it. At 15 seconds it says `!! STALE`; a failed
read says `!! DISCONNECTED` and keeps the last good reading *under* the warning
rather than replacing it with an empty screen. `canonical: false` is reported
as "the manager was NOT read", because that is the difference between "nothing
is running" and "nobody looked".

## Bounds

| bound | value | why |
|---|---|---|
| snapshot input | 4 MiB | **refuses** rather than truncating — a dropped tail would silently omit Jobs, which is the failure this viewer exists to fix |
| locator read | 64 KiB | bounded, on explicit detail only, and **visibly** truncated; there is no idle log tail |
| poll | 1 s default, finite and > 0 | the loop sleeps between reads; a failed read does not become a hot retry, and a zero or non-finite interval is refused rather than spun on |
| stale | 15 seconds | shared with status, independent of polling, applied **inclusively** at 15 seconds |

These bound what this program holds and shows. They are not protocol limits and
change nothing about the manager's own input rules.

Drill-down selects an artifact **by identity out of the snapshot** — Job, stage
and `output_name` — and reads the locator the manager published there. There is
no path operand, `file:///...` is understood as a locator rather than as a
filename, a relative reference is never resolved against wherever the viewer
happens to be running, and only a regular file opened without following a link
is read. No raw transcripts are exposed.

A read that fails, or a document that is truncated, oversize or not a status
document at all, leaves the last good view on screen under a conspicuous
`!! DISCONNECTED` warning and retries on the ordinary tick. The nested shape is
validated before a document is allowed to replace a good one, so a
schema-tagged but malformed body cannot throw the view away and then fail to
render. In detail mode, "no readable observation yet" is reported as exactly
that — a Job genuinely missing from a *readable* snapshot still refuses. The command does
not exit because it caught its source mid-write.

## Measured cost

`cost-168118.py` / `cost-168118.json` in the Work dossier, 20 deterministic
Jobs, 1 s polling, 60 s idle, driving the **selected refresh adapter**
(`_source_from`, re-reading the status file each tick) through parse, staleness
and render:

- **0.025 CPU-seconds including children** over 60.0 s wall — **0.0409 % of one
  core** against a 1 % target
- child CPU 0.0 s; 60 refreshes, 0 failures; slowest single source read 0.4 ms
- 39129-byte input document; host `slryzen`, Linux 6.17.0, CPython 3.13.7

**What this does not measure:** periodic canonical status *production*. Writing
that document is `job_manager ... status`, a separate command with its own
cost, and calling this a whole-pipeline figure would be a claim the harness
cannot support. The earlier `cost-167908.json` remains in the dossier; the
numbers above are this run's, and the figures quoted in the first handoff
(0.023 / 0.039 %) did not match the file that was retained with them.

Refresh latency is held by a test rather than a stopwatch: a changed
observation is visible after exactly one tick, so at 1 s polling one interval
is the worst case for *noticing* — which is a statement about the loop, not a
measured wall-clock bound.

## Not in scope here

Rich telemetry (W39649) and labels (W29408) are separate v13 work. Managed
execution evidence is W161230. If an observation this viewer needs does not
exist, that is a finding for the provider's existing owner — not a reason to
grow a second backend here.

Status and monitor share `tools/job_observation.py` for outcomes, gates, failures,
reported operations, attempt-bound native-byte activity and freshness. Operation
state is reported evidence, not a current provider tool; exchange attempt binding
is explicitly unverified where the snapshot cannot establish it. No reader adds
collectors or interprets raw logs. JSON schemas and service-health checks remain
unchanged (W385263).

### Planned phases and admitted attempts

Both `just status` and the monitor use the pure `tools/job_observation.py`
interpretation of `baton.v12.job-status/9`. Plan position and admission are
independent. Admission has three answers:

- **admitted**: an allocation bound by episode and assignment id to the row's
  attempt id; or, for the live episode, an `admit` receipt in `performed` or
  `adopted` state whose detail says `canonical_state: committed`; or a `claim`
  receipt whose result state is `claimed`.
- **not admitted**: a cancellation target for the exact stage, episode and
  attempt in state `retired-before-admission`.
- **unknown**: everything else. A row, its opening or ending, a stage state,
  a refused offer, a gate, and missing evidence prove neither admission nor
  non-admission.

Only admitted rows are called attempts. Detail shows other reserved rows as
“reserved identity — admission unknown”. Earlier admitted attempts retain their
allocation, ending and exactly bound cancellation evidence; other facts are
unknown. The list counts admitted attempts. Runtime summaries count admitted
attempts in nonterminal phases, separately from recorded runtimes.

Every fact must name or be published under its exact attempt. Allocations match
both episode and assignment id; receipts match the live episode; cancellation
targets match stage, episode and attempt id; diagnostics and activity match
attempt id. Provider invocation evidence additionally passes the existing scope,
operation, command digest, sequence and chronology checks. Earlier-attempt stops
never label a later attempt.

**Command accepted (reported)** means the exchange receipt records acceptance,
with its instant. **Execution started** and **provider started** require a valid
attributable provider invocation record. Runtime identity, reported operation
states, activity and **result recorded** do not prove start or that a model ran.
Non-provider phases have no attributable execution-start fact in this snapshot;
their duration is unknown. No provider wording is shown without an invocation.
Valid invocation durations remain `running Ns` or `provider ran Ns`.

The position words are **planned**, **ready**, **admitted**, **in progress**,
**waiting for an answer**, **answered — held**, **changes requested**, and
**done**. Execution states without admission read **unknown (reported state:
state)**. **Failed** denotes an exceptional ending; **stopping (state)** denotes
a stop request or order with cessation unconfirmed; **stopped** requires recorded
cessation; **cancelled before start** requires the exact attempt's
`fenced-unstarted` target. Cancellation of the Job remains a separate line.

Job headlines summarize the same observation in status, monitor list and monitor
detail. A failed phase takes precedence over an owner decision. An owner hold
shows its reason immediately below the headline. Next in order are CANCELLATION
REQUESTED, IN PROGRESS, ADMITTED, then QUEUED. ADMITTED means admission
is confirmed and no phase has progressed to active execution. A cancellation
request alone does not establish cessation. BLOCKED includes a chain of closed
gates when an external dependency holds up all remaining work. After ADMITTED,
a review whose attempt froze its result without a usable report makes the Job
BLOCKED, with that review's `Review held: …` sentence below the headline, and
the phase row reads `held`. That hold outlasts its runtime: once the attempt
stops, the row reads `stopped` and the Job stays BLOCKED with the same sentence.
A review still answering with no frozen result is
in progress, because its verification may still be running.
Phase rows still show the stopped attempt, active worker or named dependency.
A closed gate on an unidentified dependency leaves the Job headline unknown.
Completion of every phase does not establish the final Job outcome.
The current status publisher has no Job finalization or final outcome field.

A review held because its worker had no usable report shows one of
`Review held: review report missing`, `Review held: review report empty`,
`Review held: review report malformed`, or `Review held: no usable report` on
its phase row in status, list and detail. The held conclusion carries the same
reason. These words come only from the current attempt's sealed, re-measured
review log; qualifying older logs use the last sentence. Missing or changed
retained evidence is unknown and supplies no sentence. Attribution holds appear
first when both facts are evidenced, and stale snapshots keep their stale marker.
This diagnostic does not change the Job headline or authorize further execution.

## The read-only TUI (W386308)

`tui` is the same snapshot and the same words as `monitor`, kept on screen and
navigable. It is read-only: it opens the published status file and nothing
else, and quitting it leaves every Job as it was.

```sh
"$DEST/distro/baton-v12-stack" tui --instance "$DEST/instance.json"
python3 -m tools.job_tui --status "$DEST/state/status.json"      # the same program over a named document
```

- **List**: one row per Job in the snapshot's own order, with its headline and,
  beneath it, the reason when there is one. The header counts Jobs and how many
  need a decision.
- **Detail**: the selected Job's headline, reason and summary, then one row per
  phase with its position and reason. The selected phase also shows its attempt
  identity, recorded facts, timing and requested model.
  The detail shows a phase's name before its role when it has one.
- **Keys**: `↑`/`k` and `↓`/`j` move; `PgUp`, `PgDn`, `Home`, `End` jump;
  `Enter` opens the selected Job; `Esc` goes back; `n` moves to the next Job
  needing a decision; `r` reads the snapshot now; `q` or `Ctrl-C` quits.
- **Selection** is the Job's or phase's identity and survives refresh. One that
  is no longer in the snapshot is shown as `… — not in the current snapshot`
  until you move.
- **Freshness**: `!! STALE` when the observation is at least 15 seconds old,
  `!! DISCONNECTED` with the cause when a read fails (the last good content
  stays), and `not read yet` before the first good read.
- It refuses, with exit 2, when standard input or output is not a terminal;
  `monitor` is the plain-text view. `--interval` sets the seconds between
  reads (default 5).
