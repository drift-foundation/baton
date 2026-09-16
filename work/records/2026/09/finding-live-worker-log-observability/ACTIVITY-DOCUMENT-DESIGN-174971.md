# Activity document — completed design, fifth revision

Recorded 2026-09-15 by baton.claude, claim 174971, per review
`review-2026-09-15T04-16-56Z.md` under owner M174917. **Design only.** No
product or test file edited, nothing executed. Completes
`ACTIVITY-DOCUMENT-DESIGN-174920.md`.

**Retained unchanged:** the optional `activity.json`, its parser, atomic
replacement and lifecycle bytes; delayed-final-count receipt semantics; the
`stage_execution.py` scope; the independent store handle; every numeric limit;
exclusive `O_CREAT|O_EXCL|O_NOFOLLOW` staging; the six-wire-field / local-
capability distinction; no diagnostic adoption; and the honest viewer
follow-through for W167896.

## 1. The mtime baseline was wrong — withdrawn

**The counterexample settles it.** A native file holding 1000 bytes, with 10
appended before the first tick, has 1010 bytes *and* a new mtime. My rule
counted **1010** as this invocation's growth when the true answer is **10**.
mtime says a file changed; it cannot say how much of it is new. Withdrawn
entirely — and so is "record the directory identity at launch", because that
stat is not free either, as the review notes.

**Selected instead: a baseline proved by construction, not measured.**

`_scratch` with no injected home calls `tempfile.mkdtemp(...)` — a directory
**this process just created**, which is therefore **provably empty of native
files at that instant, with no scan and no stat**. That is a true pre-launch
baseline of **zero**, admitted without waiting for anything.

| Home | Baseline | Activity |
| --- | --- | --- |
| **Created by this agent** (uninjected `_scratch`) | **zero, by construction** | counted from the first byte |
| **Injected, reused or restored** | not provable | **`unknown` for the whole operation** |

**An unproved home is never estimated.** No scan reconstructs a baseline, and
no restored history is subtracted — the operation simply reports unknown, which
is the answer this design has consistently preferred to a plausible number.

The only thing recorded at launch is a boolean the agent already knows: whether
it created the scratch itself. That is free.

## 2. Admission and the worker — the conflict resolved

The review is right that "one worker per deployment" and "admission per attempt"
were in tension, and that a single delivery root fixed at construction cannot
serve many attempts.

**Two separate things, named separately:**

- **Admission is per `(control store path, attempt_id)`** — the durable identity
  a second writer would collide on. It lives in a **module-owned registry**, not
  in a composition, so it is stable across **both factories** and across
  **distinct compositions** over the same store.
- **The worker is a deployment-scoped helper** that holds whichever admissions
  it has acquired. It is not per attempt, and it does not fix a root at
  construction.

**Acquisition is atomic and nonblocking.** A composition attempts the slot with
a single compare-and-set; **it never waits**. Failure to acquire means this
attempt gets no ingestion — the count is optional and droppable — and the
composition proceeds.

**The slot is retained until positive stop.** Released only when its worker is
observed to have exited. A timed-out or abandoned stop leaves it **occupied**,
so no later composition can start a second writer for that attempt.

**Registration is bounded** at the same 64 identities; exceeding it means no new
admissions, failing toward no diagnostic.

**Each enqueue carries its own operands** — `attempt_id`, the **local** event
root, and the six wire identity fields. The root travels **only in the
in-process queue**, which the review explicitly permits; it is **never supplied
over the wire** and never read from the document. No `launch.adopt` runs on the
diagnostic path.

## 3. Unwind — partial construction and store close

**Pinned, both of them:**

- **Partial construction unwinds what it acquired.** If a composition acquires
  an admission slot and then fails before its worker is running, it **releases
  that slot** as part of the same failure path. A half-built composition never
  leaves a slot occupied by a worker that does not exist.
- **The thread-owned `ControlStore` handle closes only after the worker has
  actually exited.** Never after a timed-out stop. If the stop exceeds its 2 s
  bound the handle is **left open**, the slot stays **occupied**, and the fact
  is reported — through `release`'s collected refusal for the staged path and
  raised from `dispose` for bootstrap. **Leaking a handle is the lesser fault;
  closing one under a live writer is a use-after-close.**

## 4. Everything else

Source and test paths, the numeric table, the write pattern, the parser,
compatibility pairings and the rest of acceptance are as in the fourth revision.

**Acceptance changes and additions:**

1. **No baseline scan and no directory stat on the launch path** — the agent
   records one boolean it already knows.
2. **A created scratch yields counting from the first byte; an injected or
   restored home yields `unknown`** for the whole operation.
3. **Atomic nonblocking acquisition:** a second composition racing the same
   `(store, attempt)` acquires nothing and waits for nothing.
4. **A timed-out stop leaves the slot occupied and the handle open**, and the
   fact is reported — asserted, not inferred from the absence of a crash.
5. **Partial construction releases its slot.**
6. **The enqueue carries a local root and performs no adoption**; no root is
   ever read from the document.

## 5. Scope

Nothing here reopens the transport, parser, write pattern, lifecycle bytes,
delayed-count semantics, numeric decisions or staging. No viewer product path is
edited. Follow, sink expansion, colour, pause, search/filter, retention and raw
stream UX remain W39649/v13 material.
