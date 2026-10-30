# Progress

## claim371131 — the routine-startup proposal

Owner W370747 E370866 selects **planning only**. No product source, test or
specification byte changed; nothing installed, started, retried or cleaned up;
no engine, provider or deployment touched; no Git mutation.

### Revalidated at claim, read-only

    HEAD                f36bcd75ed22430355efe1b274b8f236cb591f6b
    v12 porcelain       two paths modified, both W370555's accepted candidate
                        (single_worker.py, test_job_task_delivery.py) — not mine
                        this claim and not touched by it

Every source statement in `PROPOSAL.md` was re-read at this base rather than
carried from the parent assessment, and the seven anchor hashes are recorded
in the proposal's own table.

### What I could state as *observed* rather than inferred

I was the operator in W370268, so the four failures are first-hand and their
exact refusal text is already retained in that dossier's
`evidence/claim-370272`. That is why this plan needed **no new probe**: the
only way to re-reach them would have been starting the retained instance,
which this claim forbids. Stated in the proposal rather than left implicit.

### The finding the plan turns on

The FINDING asks for code gaps to be separated from new semantics, and the
four do not divide evenly:

**Three are code gaps under existing DESIGN**, and OBS-0a says so in its own
words — *"The launcher MUST create and validate required output directories
and other launch prerequisites"* and *"Further manual reprovisioning
requirements are product defects, not normal operator steps."*
`instance.layout` has no `workspaces`/`launch`/`credentials` member, and
`bootstrap` creates only four of the paths the configuration it writes will
require; the control store exists only once something has served, because the
single writable `ControlStore.open` in `job_manager` is inside `_serve`; and
`observing_factory` requires an operator-authored env export.

**The fourth is a decision, and neither side of it is wrong.** `HOST-8`
mandates one active manager behind an exclusive non-blocking file lock, and
`creation.create_template_job` takes that same guard *on purpose* so the
derivation cannot go stale — DB-3 and DB-5 being satisfied, with the reason
written in its own comment. `borrow_manager_instance` already serves "one
user among any number of them", but its count and cache are **process-global**,
so borrowing composes only in-process. A separate `create` process must take
the `flock` the serving process holds.

So no lock can be relaxed without losing the atomicity the derivation
depends on, and cross-process borrowing of an exclusivity guard is the
standby/takeover HOST-8 forbids. **The question is where the admission runs,
not which lock to weaken** — and that reframing is the substance of this
plan.

### What the proposal recommends

**Option A**: `create` records a durable creation intent bound to the Job's
existing operation id, and the **serving manager** performs the same
`create_template_job` inside the guard it already holds. DB-4 prescribes that
shape in terms — *"durable intents, idempotent operations and explicit
incomplete states"* — and DB-7's operation identity already makes a repeated
request replay and a changed one refuse. One manager, no standby, no
takeover, derivation still atomic, and the admission code does not move.

Options B (a second configuration guard — new semantics, deadlock risk),
C (yielding the lifetime guard — reopens the window HOST-8 exists to close)
and D (keep the stop/create/start cycle — what the FINDING rules out) are
each recorded with the reason they are not recommended.

**Four finite slices.** S1 installer paths, S2 control-store initialisation,
S3 `status --observe --instance` are each independently acceptable, need no
new semantics, and **should land before S4** — together they get a fresh
install to its first `start` with no operator-authored step, which is most of
what OBS-0a asks, and they do not depend on the decision. S4 is Option A and
waits on the owner.

### Overlap recorded rather than assumed

S3 would touch `tools/single_worker.py`, which **W370555's accepted candidate
is currently modifying** — so S3 sequences after that checkpoint.
W325695 holds `claude_agent` and this plan touches none of it. S1/S2 touch
`bootstrap.py` and `instance.py`, which no current claim holds. S4's surface
is the largest, which is a second reason it is last.

### Labelled, as the PLAN requires

**Observed:** the four refusals and every source anchor, re-read at this base.
**Inferred:** that S1–S3 suffice to reach a first `start` with no operator
step — I did not build or run them. **Proposed:** every contract in the
proposal's §2–§6. **Open:** the §4 decision, whether `create` waits by
default, the OBS-0a endpoints, and whether the intent relation belongs to the
Job store or the control store.

### The OBS-0a interval cannot be measured as things stand

W370268 established that the status projection's `observed_at` is *query
time*, that worker visibility separates bytes observed from progress, and that
nothing records when an operator's command was received. So the acceptance
matrix asks for the endpoints and clock source to be **named**, and for the
interval to be reported unknown where no output records an endpoint, rather
than approximated. That is an owner decision the proposal surfaces instead of
inferring.

### Verification and cumulative spending

Planning only: eighteen read-only source and specification reads
(`job_manager`, `bootstrap`, `instance`, `fresh_attempt_ports`, `creation`,
`workspaces`, `single_worker`, and DESIGN HOST-8 / DB-3–DB-7 / OBS-0a read
verbatim), seven hash computations, one read-only `instance.layout` call to
enumerate its members, and the parent assessment. **No probe was run and none
was needed.** No test suite executed, because nothing was changed.

### Boundaries

Written: `PROPOSAL.md`, this file and `evidence/claim-371131/`. Nothing else.
The reviewer's `FINDING.md` and `PLAN.md` are unmodified; sibling dossiers,
accepted candidates, product source, tests and DESIGN were read-only. No
version-control mutation — the only calls were `rev-parse` and `status`, both
reads.

---

## claim371264 — revision 2, answering R1–R4

Answers `review-2026-10-28T03-22-00Z.md`. The bytes reviewed as revision 1 are
preserved **unchanged** at `evidence/claim-371264/as-delivered-371131/`, both
hashes verified against the reviewed binding before anything was rewritten:

| | sha256 |
| --- | --- |
| `PROPOSAL.md` as delivered | `3ec301169674f12839d10d65738ffa20db1643d5d1fd1939cafa0af8cbc0f425` |
| `PROGRESS.md` as delivered | `54e12c96f431f5b22d6d6fa328a19af29f7bcc62882cc9bc16d96dc4046257c4` |

Still **planning only**. No product source, test or specification byte changed;
nothing installed or started; no engine, provider or deployment touched; no Git
mutation.

### R4 — the baseline statements above are wrong, and here is the correction

The two statements at lines 11–12 and in *Overlap recorded rather than assumed*
contradict each other and both mis-state the base. Corrected here rather than
by editing them, so the reviewed text stays attributable:

* **`f36bcd75` already contains W370555.** Its checkpoint is **not** a future
  gate, and S3 does not sequence after it. *"W370555's accepted candidate is
  currently modifying `single_worker.py`"* was wrong — that correction is in
  the commit this claim is based on.
* **The current working-tree modifications under `v12` are W325695's** —
  `v12/worker/claude_agent.py` and
  `v12/python/tests/manager/test_claude_agent.py` — not W370555's. Neither is
  mine this claim and neither is touched by it.
* **Withdrawn:** *"deterministic reproduction would require starting the
  retained instance."* Unsupported. Isolated temporary stores and fake owner
  boundaries make the §6 acceptance reachable without starting it, and §6 now
  says so. The honest reason no probe was run is that the four refusals are
  already retained with their exact text.

### R1 — sections 2 answers the admission contract concretely

Owning store (the Job store, because the Job's creation is already its fact
under DB-4); the `creation_intents` relation with its canonical operands,
operation id and request digest; five states with who may make each
transition; **DB-5's safe held states mapped onto the existing CUT A/B/C in
`creation._owned`** rather than revision 1's false claim that no partial
reservation survives; direct-versus-queued arbitration through the per-Job
`invocation` flock that contends across threads of one process as well as
processes, with `store.replay` kept **before** derivation so a completed
request still replays; per-crash-point recovery; DB-7 retirement as a
conditional transition a retired row cannot make; `--wait/--no-wait` and the
timeout that leaves the intent pending.

Revision 1's *"the OS guard serialises admissions"* is corrected:
`borrow_manager_instance` is **counted**, so N in-process borrowers coexist.
Different Jobs are serialised by performing at most one queued admission per
reconcile step, and a recorded `configuration_revision` is the generation
fence against serving and dispatch.

**Reconciled with sibling W371072** by name: its PROPOSAL states that if
startup ownership changes here, *"its admitted configuration revision/fence
must replace the current OS-guard assumption explicitly"*. §2.6 supplies that
revision.

### `DESIGN.md` changed during this claim, and it changes the answer

Re-hashing the anchors rather than carrying them found `v12/DESIGN.md`
**modified in the working tree** — `571738130e7cfedd…` now against the
`500fa602…` revision 1 recorded at `f36bcd75`. The +16 lines are a new owner
clause, **Development role-contract admission (owner 2026-10-28)**, which
**selects sibling W371072's admission plan as normative** and cites that
sibling's `FINDING.md` as the decision.

That is not bookkeeping. Revision 1 and the review both discuss W371072 as a
peer proposal to reconcile with; it is now a settled requirement. So:

* §7 is corrected: pre-reservation validation and the retained-contract
  dispatch check are **not negotiable between the two plans**, and S4 cannot
  be accepted in a form contradicting them.
* A new **§2.6a** states conformance with each sentence of the clause: the
  validation ordering (replay → closed-data contract validation → record the
  intent → flock → CUT A, because recording an intent **is** a Job-store
  effect); the fence comparing the retained contract and capability digests
  **together with** `configuration_revision`; no template/deployment callback
  inside the intent transition or any cut and no second store opened under
  one; a queued intent whose contract no longer validates **refusing** rather
  than re-deriving, which is why the intent stores canonical operands and not
  a reference to mutable configuration; and the clause's
  shared-optional-declarations sentence recorded as the reason
  `SHARED_DECLARED` cannot satisfy a role's required outputs — the exact fault
  W370268 observed.

I did not author, request or touch that clause; it is the owner's and it is
read-only to me. **`DESIGN.md` must be re-read at the next claim** rather than
carried from this base, and both hashes are recorded in the proposal's table
so the drift is visible rather than smoothed over.

### R2 — the OBS-0 interval is restored with its bound

Install-to-first-start is OBS-0a and separate. §3 now states the normative
interval — **≤60 seconds** from receipt of the task description and selected
inputs to the assigned agent starting substantive work, across input handling,
configuration, validation and launch — names both proposed clock endpoints
(`received_at` on the intent; the worker's existing `state-work.json`), and
states the simulated-provider limit instead of implying a live measurement.

The OBS-1 assertion is corrected from *"mutates no durable byte"* to **no
application-data or schema mutation, no initialisation or migration, no
reconciliation, no writable fallback**, per the owner clarification of
2026-10-18 and `ControlStore.open_readonly`'s own docstring — SQLite sidecars
and locking are the accepted boundary. That also identifies the `-shm/-wal`
test failure I reported in W370555 as asserting the superseded absolute.

### R3 — installer, reopen and observation, against the real APIs

* `bootstrap.install` **refuses an occupied installed destination and upgrades
  nothing**, so revision 1's "create-and-validate-if-absent" implied a
  reinstall path that does not exist. Split: prerequisites are created in the
  **fresh install** path; an existing instance gets a separate **read-only
  validate** verb that reports and refuses, repairing nothing.
* `ControlStore.open(path, *, incarnation, clock)` already initialises an
  empty store, adopts a supported existing schema, requests WAL and closes its
  handle on every failure — so the installer calls **that** opener once with
  its own incarnation and injected clock. One creator, one migrator, no second
  compatibility check.
* The proposed `instance.json` prerequisite inventory is **withdrawn**:
  `instance.settings` already derives the four operands and
  `stack.instance_settings` already validates the installed selector, so an
  inventory would be a second account of a fact they own.
* `stack status`/`monitor` are already instance-addressed; the gap is the
  lower-level `manager status --observe`, which gains `--instance` deriving
  `BATON_V12_STAGE_EXECUTION_CONFIG` through `instance.settings`. Exact argv
  is in §4.5, with precedence stated and **a disagreement between `--instance`
  and the env var refusing**.

### Verification this claim

Read-only: `v12/DESIGN.md` OBS-0 and OBS-1 verbatim; `creation.py`'s cut
markers and `_owned`; `ControlStore.open`/`open_readonly`;
`bootstrap.install`'s occupied-destination refusal; `instance.settings`;
`stack.instance_settings`; sibling W371072's `PROPOSAL.md` and
`review-2026-10-28T03-16-17Z.md`; and the new owner clause, reached by
re-hashing rather than by being told about it. Two hash computations to
confirm the as-delivered snapshot MATCHES the reviewed binding, seven anchor
re-hashes, and one working-tree diff of `DESIGN.md` to establish exactly what
the owner added. **No test suite executed, because no product byte changed.
No probe run.**

### Cumulative

claim-371131 (revision 1: the four refusals re-read, seven anchor hashes, one
read-only `instance.layout` enumeration) **plus** this claim's reads above.
All claim-371131 evidence is retained, not deleted.

### Boundaries this claim

Written: `PROPOSAL.md`, this file and `evidence/claim-371264/`. Nothing else.
`FINDING.md`, `PLAN.md` and both reviews are the reviewer's and unmodified.
Sibling dossiers, product source, tests and DESIGN were read-only. No
version-control mutation — only `rev-parse`-class reads.
