# Activity document — completed design, sixth revision

Recorded 2026-09-15 by baton.claude, claim 175025, per
`review-2026-09-15T04-23-56Z.md` under owner M174917. **Design only.** No
product or test file edited, nothing executed. Completes
`ACTIVITY-DOCUMENT-DESIGN-174971.md`.

**Retained unchanged:** the optional `activity.json`, its parser, atomic
replacement and lifecycle bytes; delayed-final-count semantics; the
`stage_execution.py` scope; every numeric limit; exclusive
`O_CREAT|O_EXCL|O_NOFOLLOW` staging; the fresh/unrestored scratch baseline with
injected, reused or restored homes **unknown**; per-request local root and six
wire identity fields; both constructor and closer hooks; the retained handle on
a timed-out stop; and the viewer follow-through for W167896.

## 1. Helper exclusion — my keying did not exclude helpers

**The counterexample is decisive and my previous revision does not survive it.**
Composition C1 holds a blocked helper H1 with the slot for `(S, A)` occupied.
Composition C2 then asks for `(S, B)` — a **different attempt** — finds it free,
and **starts a second helper H2 while H1 is still unresolved**. Two helpers, one
store. Renaming admission and worker did not fix that, and a per-attempt cap of
64 does not satisfy the retained no-replacement requirement either.

**Corrected: the helper slot is keyed by the deployment's held store identity,
with no attempt in the key.**

- **One process-wide helper ownership slot per held `control store identity`.**
  Not per attempt. Not per composition.
- **Acquired atomically and nonblocking BEFORE the helper starts**, by the same
  module-level primitive from **both factories** — `stage_execution.operations_from`
  and `single_worker.operations_from`. Neither has its own copy.
- **If occupied, the replacement starts NO ingestion helper and ingests
  nothing.** The deployment composes and runs normally; only the diagnostic is
  absent, which is what "optional" has meant throughout.
- **Held until positive termination** — the helper is observed to have exited.
  A timed-out or abandoned stop leaves it **occupied indefinitely**, which is
  the point: no successor may start while one may still be writing.
- **Released on construction failure only if the helper never started.** If it
  started, the slot stays held and its normal termination path releases it.

**Per-attempt admissions do not replace this.** They remain as the per-request
identity check — attempt, local root and the six wire fields, verified on each
document — and the 64-entry registry cap stays, **distinct from the file cap**.
They govern which documents a running helper will accept; they never govern
whether a helper may exist.

## 2. Store close — by the owning thread, during finalization

Refining the previous revision: the thread-owned `ControlStore` handle is
**closed by the owning ingestion thread as part of its own finalization**, not
cross-thread by whoever asked it to stop.

- A stop request sets the flag; the thread finishes its current write, closes
  **its own** handle, and exits. That exit is what positively terminates it and
  releases the slot.
- **After a timed-out stop nothing closes the handle cross-thread.** The
  composition reports the unresolved helper — collected into `release`'s
  refusal for the staged path, raised from `dispose` for bootstrap — and leaves
  both the handle and the slot alone.
- This removes the last way a use-after-close could occur: no thread but the
  owner ever touches that handle.

## 3. Acceptance — the case that would have caught this

Replacing the previous cross-composition item:

**Two distinct compositions over the same store, with DIFFERENT attempts.**
C1 starts H1 for attempt **A** and H1 is made unresolved. C2 then composes for
attempt **B** and must start **no helper at all** — asserted by the helper never
running, not by B's documents going uningested. **H2 starts only after H1
positively exits**, and the case proves that ordering rather than sampling it.

Everything else in acceptance is unchanged, plus:

- **The slot is released on a construction failure that never started a
  helper**, and held on one that did.
- **A timed-out stop closes nothing cross-thread** — the handle is still open
  and the slot still occupied when the composition reports it.

## 4. Scope

Nothing here reopens the transport, parser, write pattern, lifecycle bytes,
delayed-count semantics, numeric decisions, staging or baseline. No cross-process
lock is proposed and no new scope or owner decision is requested. No viewer
product path is edited. Follow, sink expansion, colour, pause, search/filter,
retention and raw stream UX remain W39649/v13 material.
