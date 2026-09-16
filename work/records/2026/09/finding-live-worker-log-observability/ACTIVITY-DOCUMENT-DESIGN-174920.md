# Activity document — completed design, fourth revision

Recorded 2026-09-15 by baton.claude, claim 174920, per owner reroute M174917.
**Design only.** No product or test file edited, nothing executed. Completes
`ACTIVITY-DOCUMENT-DESIGN-174799.md` against
`review-2026-09-15T04-06-59Z.md`.

**Retained, not reopened:** the optional `activity.json`, its parser, atomic
replacement and lifecycle bytes; the delayed-final-count receipt semantics; the
selected `stage_execution.py` scope; the independent store handle; the numeric
limits; and exclusive `O_CREAT|O_EXCL|O_NOFOLLOW` staging. No further permission
or revocation decision is needed.

## 1. Nonblocking baseline — actually off the launch path

The previous revision said the baseline scan runs "before the provider process
is started". **That still puts it on the launch path**, which is what the review
objects to: a bounded scan is still work the provider waits behind, and a slow
filesystem would delay the turn for a diagnostic.

**Corrected mechanism — the baseline is *admitted*, not *taken*, before launch:**

- At launch time the agent records only **the instant** and the identity of the
  private `.claude` directory. That is two cheap facts, no directory walk.
- **The first scan happens on the publisher's own thread**, at its first cadence
  tick after launch. Files whose `st_mtime` is **at or before** the recorded
  launch instant contribute their size as **baseline**, not as growth; files
  newer than it are this invocation's from their first byte.
- So no scan ever runs on the launch path, and the baseline is still correct:
  the discriminator is the recorded instant, which is free to capture.
- **If the first scan fails or overflows, activity stays `unknown`** for the
  operation, exactly as before — and, now, without having cost the launch
  anything.

This also removes the last reason the agent would touch the filesystem
synchronously for a diagnostic.

## 2. Pooled and bootstrap — two owners, named separately

The review is right that these are different compositions with different unwind
shapes, and my previous revision named only one.

| Composition | Owner | Unwind |
| --- | --- | --- |
| **Pooled / staged** | `stage_execution.operations_from` (`:5430`) constructs the ingestion worker beside the other deployment-owned handles | `StageExecution.release` (`:4309`) → `_closers` (`:4321`) yields `"the activity ingestion worker"`, and a failed stop appears in `release`'s collected refusal |
| **Bootstrap / single worker** | `single_worker.operations_from` (`:2319`) constructs it | `_Operations.close` (`:2312`) already owns a single `dispose` hand-back; the worker's stop is chained **into that same `dispose`**, so the one existing teardown point stays the one teardown point |

**Neither composes the other's.** A bootstrap deployment never reaches
`_closers`, and a staged deployment never relies on `_Operations.close` for
this. Each constructs exactly one worker and unwinds it through the hook it
already has.

**Unwind order is the same in both:** stop the ingestion worker **before**
closing the `ControlStore` handle it owns, so it can never write through a
closed handle. A stop that exceeds its 2 s bound leaves the worker
**unresolved** and that fact is reported — collected into `release`'s refusal
for the staged path, raised from `dispose` for the bootstrap path.

## 3. Shared admission across distinct compositions

The previous revision made exclusion a property of *one* composition being
recomposed. **That is not enough:** the review is right that two *distinct*
compositions over the same stores can overlap, and an unresolved helper from
either must block a new one.

**Mechanism — admission is keyed on the durable identity, not on an object:**

- A single **admission slot per `(control store path, attempt_id)`**, held in a
  process-wide registry owned by the worker module rather than by either
  composition.
- A composition may start an ingestion worker for an attempt **only if that slot
  is free**. A slot is freed **only** when its worker positively resolves —
  finished or observed stopped. An abandoned or timed-out worker leaves it
  **held**.
- **A held slot means the new composition starts no worker** and ingests
  nothing for that attempt. Optional counts are droppable; a second writer
  against the same store is not acceptable.
- The registry is bounded by the same **64 tracked identities** limit; exceeding
  it means no new admissions, which fails toward *no diagnostic* rather than
  toward unbounded growth.

## 4. Trusted enqueue operands — six wire fields, plus a capability

The review is right to separate these. My previous list of seven conflated a
**wire identity** with a **local capability**.

**Six wire identity fields**, all read from the document and all compared:
`session`, `attempt_id`, `sequence_id`, `command_digest`, `operation`,
`operation_id`.

**The event root is a local capability**, not a wire field: it is the path the
manager itself composed for this delivery, handed to the ingestion worker
directly. It is never read from the document and never compared against it.

**No synchronous `launch.adopt` for diagnostics.** The enqueue hook must not
adopt a launch delivery merely to learn the root. If the serving loop does not
already hold it at that point, the worker is given the root **once at
construction** from the composition that created the delivery, and the enqueue
carries only `(attempt_id, the six fields)`. **Adoption is never performed on
the diagnostic path.**

## 5. Viewer follow-through — recorded, not implemented

The delayed-final-count semantics imply a display rule: **activity is historical
once the stage is terminal.** The current viewer displays `unknown`
(`tests/tools/test_job_viewer.py:123`, `:986`), and **W167896 owns those three
files.**

**This design edits no viewer path and proposes no change to W167896's scope.**
It records the follow-through so that owner can decide: while W61599's activity
source is unimplemented the viewer's `unknown` remains correct, and when a count
exists the viewer must distinguish *live* activity from a historical instant on
a terminal stage. **Until W167896 takes that up, the honest display is the one
it already has.**

## 6. Everything else, unchanged

Source paths, test paths, the numeric table, the write pattern, the parser,
compatibility pairings and acceptance are as in the previous revision, with
these additions to acceptance:

1. **The launch path performs no directory scan** — asserted against the
   recorded instant, not inferred from timing.
2. **Bootstrap unwind:** the worker is stopped through `_Operations.close`'s
   `dispose`, before its store handle closes, and an over-bound stop is
   reported.
3. **Cross-composition admission:** a second composition over the same store
   with an unresolved helper starts none and ingests nothing.
4. **The enqueue carries no root** and performs no adoption.

## 7. Scope

Nothing here reopens the transport, parser, write pattern, lifecycle bytes,
delayed-count semantics or numeric decisions. No viewer product path is edited.
Follow, sink expansion, colour, pause, search/filter, retention and raw stream
UX remain W39649/v13 material.
