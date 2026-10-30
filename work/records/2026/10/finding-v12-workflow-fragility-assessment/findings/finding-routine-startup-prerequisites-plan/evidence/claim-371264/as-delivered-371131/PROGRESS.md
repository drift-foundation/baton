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
