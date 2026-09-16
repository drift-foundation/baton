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

- Every Job in the snapshot, with its stages, exact stage/work/offer/attempt
  identities and the current episode.
- `elapsed`, computed **only from recorded source times** — the episode's
  `opened_at` and `ended_at`.
- `activity` — currently always `unknown`; see below.
- Held, failed and operator-action reasons, including which stages a blocked
  stage is waiting on.
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

**It invents nothing.** Every value comes from the snapshot or is spelled
`unknown`. The tempting thing for a viewer is to compute a plausible number
when a real one is missing — elapsed from the wall clock, activity from the
fact that polling returned — and each of those reports the *viewer's* behaviour
as if it were the *Job's*.

**Staleness is about the observation, not about the read.** A snapshot carries
two clocks: when this program received the bytes, and when the manager actually
looked. Re-reading an unchanged document does not make it fresher, and the view
goes `!! STALE` once the *observation* reaches `max(2 s, 2 x --interval)`. The
configured interval is carried into the rendering, so `--interval 5` really
does mean a ten-second window.

**Activity is `unknown` on purpose.** W61599 owns the trusted
provider-safe activity source. Until it lands, this shows `unknown` and never
infers freshness from an empty stream or from local polling. When W61599
supplies a validated source, this is where it plugs in; the viewer does not
edit that provider.

**It does not hide its own age.** A snapshot is exactly as fresh as the moment
it was observed, and the view shows both the manager's `observed_at` and how
long ago this program read it. At `max(2 s, 2 x interval)` it says `!! STALE`; a failed
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
| stale | `max(2 s, 2 x interval)` | derived from the configured interval rather than frozen, and applied **inclusively** so a 2 s-old observation is already flagged |

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
