# The read-only worker visibility view

`tools/worker_visibility.py` answers one question about a status document the
Job Manager has already published: **which worker is each current stage on,
and what has anybody actually observed of it.**

It is a bounded projection, not a collector. It reads one file, publishes
`baton.v12.worker-visibility/1`, and performs no act. `baton.v12.job-status/6`
is unchanged by this Work — this surface adds a reading of it, not a member to
it.

## Running it

You already have the input. The status document the viewer reads
(`JOB-VIEWER.md`) is the same one this reads:

```
python3 tools/job_manager.py --store /path/to/jobs.sqlite \
    --incarnation <incarnation> --authority-uuid <uuid> \
    status --control /path/to/control.sqlite > status.json

python3 -m tools.worker_visibility --snapshot status.json
```

The answer is JSON on stdout, exit `0`. A document this view will not read is
a JSON refusal on the same stream and exit `2`:

```json
{
  "refused": "this view reads baton.v12.job-status/6 and this document declares another schema (str); an unsupported version is refused rather than partly read",
  "schema": "baton.v12.worker-visibility/1"
}
```

**Pass `--control`.** Without it, `job_manager ... status` reports submitted
and recorded state and marks itself `canonical: false`. This view carries that
through as `snapshot.canonical`, and a consumer **must** branch on it: an empty
`stages` under `canonical: false` is *nobody looked*, which is not *nothing is
running*. `--observe` additionally reconstructs the durable exchange read, and
the `exchange` block below is `not-read` without it.

## Consuming it from a file an operator already has

The projection is importable, so a consumer does not shell out:

```python
import json

from tools.worker_visibility import VisibilityRefusal, rows_of

with open("status.json", "rb") as handle:           # bounded by the caller
    body = handle.read()

try:
    rows = rows_of(body)                            # bytes, text or a mapping
except VisibilityRefusal as refusal:
    raise SystemExit(f"this status document was not read: {refusal}")

for row in rows:
    stage = row["stage"]["stage_id"]["value"]
    worker = row["allocation"]["facts"]["worker_id"]
    count = row["activity"]["facts"]["bytes_observed"]

    where = worker["value"] if worker["known"] else \
        f"no worker ({row['allocation']['presence']}: {row['allocation']['reason']})"

    # THE THREE ANSWERS ARE KEPT APART. `known` false is not a zero, and the
    # reason says which kind of absence it is.
    if count["known"]:
        seen = f"{count['value']} bytes observed at " \
               f"{count['observed_at']['value'] or 'an unrecorded instant'}"
    else:
        seen = f"nothing observed ({count['unknown_reason']})"

    print(stage, "->", where, "|", seen)
```

`visibility(document, read_at=None)` is the whole view — envelope plus rows.
`rows_of(document)` is the rows alone. Both validate before they report
anything, and neither opens a store, constructs a serving factory, spawns a
command or asks what time it is.

## The shape

Every reported member is the same three-part fact: the value, **where it came
from**, and — when the source records one — **when it was observed**.

```json
"bytes_observed": {
  "known": true,
  "value": 4096,
  "source": "jobs[0].stages[0].runtime.activity.bytes_observed",
  "unknown_reason": null,
  "observed_at": {
    "known": true,
    "value": "2026-09-02T00:00:00.000Z",
    "source": "jobs[0].stages[0].runtime.activity.observed_at",
    "unknown_reason": null
  }
}
```

Unknown carries the same shape and a reason instead of a value:

```json
"last_contact": {
  "known": false,
  "value": null,
  "source": null,
  "unknown_reason": "unsupported by this status contract",
  "observed_at": {"known": false, "value": null, "source": null,
                  "unknown_reason": "unsupported by this status contract"}
}
```

The shape does not change with the answer. A consumer that had to handle a
missing key *as well as* an unknown fact would have two ways to read an
absence, and one of them is `0`.

`source` is checked rather than decorative: a test walks every published path
back into the source document and compares the value. A fact labelled with a
path it did not come from would be worse than one with no provenance at all.

## One row per current stage

```
jobs[].stages[]  ->  stages[]
```

Including a stage nobody has assigned to a worker. A queued stage with no
reservation, no runtime and no activity is exactly the row an operator asking
"why is nothing moving" needs to see.

Each row carries:

| block | what it is |
|---|---|
| `job` | `job_id`, `submission_id` |
| `stage` | exact `stage_id`, `job_id`, `kind`, `state`, `work_id`, `episode`, `attempt_id`, `offer_id`, and the current episode's own `episode_opened_at` |
| `configured_profile` | the profile identity this stage was **submitted with** — not evidence a worker ever ran under it |
| `allocation` | the scheduler's reservation: `worker_id`, `participant`, `lane`, `generation`, `allocation_state`, `selection_outcome`, the reserved worker's own configured profile, and its instants |
| `runtime` | `runtime_id`, the producer's `execution_runtime` axis word, and the fixed `assignment` |
| `exchange` | `transport`, `sequence_id`, `state`, the command digest, the receipt's `accepted_at`, the terminal ending and a contained unreadability's *kind* |
| `activity` | bytes observed, with its own instant and its `bytes` unit |
| `contact` | `last_contact` — always unknown, see below |
| `context` | `context_used`, `context_limit` — always unknown, see below |
| `freshness` | always `unknown`, see below |

**The configured profile and the observed runtime are separate blocks.** What
was asked for and what is running are different facts, and a stage can be
reserved on a worker before any runtime exists at all — so `allocation` sits
*beside* `runtime` rather than inside it.

## Presence, which is the member to branch on

Each block says which kind of answer it is before any fact is read.

| block | values |
|---|---|
| `allocation` | `allocated`, `unallocated`, `unknown` |
| `runtime` | `reported`, `not-reported`, `unknown` |
| `exchange` | `reported`, `not-read`, `unknown` |
| `activity` | `observed`, `not-observed`, `unknown` |
| `contact`, `context` | `unsupported` |

**`unallocated` is not `unknown`.** A stage with no reservation is a real and
ordinary state — queued, or claimed before the scheduler acted. A document
whose `allocation` member is unreadable is a different answer, and a
reservation belonging to another attempt is a third. Folding any of them into
one `unknown` is what makes an operator guess.

## No observation is attached to an attempt that did not earn it

Each row carries `attempt_association`, and it is proved before any member of
the block is reported:

- **activity** names its own `attempt_id`; it is compared against the stage's
  *current* attempt. A count from the episode that ended is `unknown` with
  `the reported activity names another attempt`, never re-attached.
- **allocation** carries `assignment_id` and `episode`; both must equal the
  stage's current attempt and episode.
- **runtime** carries no attempt id at all in this contract, so
  `verified: false` with the reason — this view says it cannot tell rather
  than claiming it can.
- **`episode_opened_at`** comes from the live episode record matched on *both*
  identities, and only while it is live. The episode history is append-only
  and an abandoned episode keeps its record, so matching on the episode number
  alone would hand a restarted stage the instant of the attempt that is over.
  **There is no history fallback:** a stage whose current episode has no live
  record answers `unknown`.

## The snapshot's instant is the query time, and nothing else

`observed_at` in the status document is when the **manager queried its own
stores**. It is published as `snapshot.query_time`, with the note saying so,
and it is never reported as a worker contact time or an activity observation
time. A test asserts that no fact in any row carries it.

`visibility(document, read_at=...)` accepts the **caller's own** read time. It
is reported separately under `read.local_read_time`, it must itself be a
durable instant, and no fact is derived from it — passing a different one
answers byte-identical rows.

## What is always unknown, and why that is the honest answer

**`last_contact`** — `unsupported by this status contract`. There is no worker
contact instant in `baton.v12.job-status/6`. The snapshot query time is not
one, and presenting it as one would report the *reader's* behaviour as the
*worker's*.

**`context_used` / `context_limit`** — `unsupported by this status contract`.
This view reads no transcript, provider session or private context path, so
there is nothing to report and nothing to estimate.

**`freshness`** — `no freshness policy selected`. No threshold has been chosen
for this Work. A view that invented a window would be publishing a policy
nobody chose. The projection is a pure function of the document, so re-reading
an unchanged source answers the same facts with the same instants, every time:
**an old timestamp cannot acquire `fresh` or `healthy` by being read again.**

A quiet runtime is neither `healthy` nor `offline`. The producer's own axis
word (`running`, `quiescent`, `uncertain`, `not-started`, …) is forwarded
unmapped. A consumer that wants a verdict has to say whose policy it is
applying.

## Zero, absence and malformed are three different answers

- `bytes_observed: 0` with an instant is a **known zero**. The producer really
  records one, and "nobody has observed anything" and "this manager observed
  zero bytes at 12:04" are different facts.
- A recorded attempt nobody has observed is `not-observed` with
  `this attempt is recorded and this manager has observed none of its session
  stream yet`.
- A count that is not an integer in the producer's domain is `unknown` and is
  never evidence.

A missing count is never rendered as `0`, and a missing runtime is never
rendered as a verdict.

> This surface deliberately disagrees with the terminal viewer on one point,
> and says so out loud. `job_viewer` renders an observed `0` as `unknown`,
> which is a **display** rule about a count an operator reads as "running and
> idle". This is a **fact** projection for a consumer, so an observed zero is
> a known zero with its instant and its unit. Neither surface renders an
> absence as a count.

**Activity is bytes.** Not tokens, not a percentage, not model progress. The
unit is published beside the number and the `what` member says what it is not.
Repeated noise grows the count, a long quiet model call leaves it unchanged,
and a provider may expose no measurable stream at all.

## What it will not do

**It is not telemetry collection.** No provider call, no engine call, no CPU
or network sampling, no terminal scraping, no transcript, no context
restoration. It reads a file.

**It has no store, no clock and no second reader.** No database is opened, no
serving factory is constructed, no command is spawned. `tools/job_viewer.py`'s
`read_snapshot` owns the schema and structural validation and this module
calls it rather than growing a second answer to "is this document readable".
Those boundaries are **trapped** in the tests — `JobStore.open`,
`ControlStore.open`, `scheduler.reserve`, `scheduler.activate_pool`,
`subprocess.run`, `subprocess.Popen` and `sqlite3.connect` all raise while the
view runs — and a separate test walks the module's identifiers rather than its
prose.

**It forwards no nested object.** Every block is an explicit allowlist of named
members with a declared type. A view that forwarded whole nested documents
would publish whatever a future producer adds to them — credentials, raw logs,
a command argv, a private-context path — and would do it silently. The
worker-authored entry names an exchange reports as `foreign` are deliberately
not among the members: they are bytes a container chose, and naming them here
would make this view their publisher.

**It follows no locator.** A status document carries the manager's own artifact
locators. A visibility view that opened one would be reporting whatever that
names rather than what this document says.

**Its refusals carry no input.** Every message is a literal plus, at most, a
Python type name. An error string assembled out of an untrusted document is a
way for that document to choose what lands in a log.

## Bounds

| bound | value | why |
|---|---|---|
| snapshot input | 4 MiB (`job_viewer.MAX_SNAPSHOT_BYTES`) | **refuses** rather than truncating — a dropped tail would silently omit stages, which is the failure this view exists to fix |
| reported text member | 256 bytes | an identity, participant, lane or digest is far inside this; a longer one is a document this view does not recognise rather than a value to republish |
| instant text | 32 bytes, then the producer's frozen `0000-00-00T00:00:00.000Z` grammar **and** a real calendar date | a near-instant — a bare date, a naive time in no zone — is a value whose meaning this view would be choosing |
| count domain | `0 ≤ n ≤ 2**53 - 1` | zero is inside the domain because the producer can observe one; a value outside it is `unknown`, checked before any conversion |

These bound what this program holds and publishes. They are not protocol
limits and change nothing about the manager's own input rules.

### Refusal, not a shorter answer

A malformed envelope, an unsupported schema, or a Job whose `stages` member is
not a list refuses the **whole** document. Publishing the readable Jobs' rows
would answer a consumer's "every current stage" with a subset it has no way to
know was a subset.

This is deliberately stricter than the terminal viewer, which treats a Job
with no readable stages as a Job with nothing to draw. That is right for a
list a person is looking at; here the entire output *is* the row set, and
`stages: []` is a confident, machine-readable "no stage is in any state".

By contrast a malformed **optional observation** — a count, an instant, one
member of a block — becomes `unknown` with a bounded reason. It is never valid
evidence, and it never costs a consumer the rest of the document.

## Not in scope here

A worker contact instant, context accounting and a freshness policy are things
this contract does not carry. If one of them is needed, that is a finding for
the producer's existing owner — not a reason to grow a collector here.
