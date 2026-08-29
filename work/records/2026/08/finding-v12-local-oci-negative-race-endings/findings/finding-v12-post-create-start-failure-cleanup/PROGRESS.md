# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — PLAN 1 and 2 done; PLAN 3–5 not started

Claimed W32648 at seq 32853. **No production code was edited.** No Git history
or index was mutated.

### PLAN 1: revalidated, and one fact reshapes the composition

Measured on the tree rather than transcribed:

- **`output.py` gates the freeze on a terminal `worker_disposition` already
  recorded**, and says a proof the caller can write is not proof. So a
  post-create failure cannot reach `request_freeze` at all without a
  disposition — and inventing one is the defect this Work exists to remove.
- **therefore the custody path for this ending is NOT freeze → intake.**
  That is worth stating before anything is written: the obvious composition
  (reuse the completed arc) is unavailable by construction, and a round that
  discovered it half-way would have manufactured a disposition again.
- **`intake.py` already owns the exact rule this ending needs, and already has
  the word.** Material collected for a generation that has ended is
  `quarantined`, and the code says why: "Refusing would destroy the evidence
  of what a worker produced… accepting would present it as the live
  generation's result. Quarantine is the third answer, and it is the reason
  the disposition vocabulary has that word in it."
- `schema.py` confirms the closed pair: `custody IN ('accepted',
  'quarantined')`, and `authorize_cleanup` already ends `retained` rather than
  `complete` when custody is quarantined.

### PLAN 2: the two things pinned, and neither is invented

**The failed-start record is manager-owned and is NOT a worker disposition.**
It records that THIS manager's start call faulted after the engine created a
container: the attempt, the fixed assignment, the start operation identity,
the attached runtime identity and the original typed fault, preserved rather
than reworded. It moves the runtime axis and never the
`worker_disposition` axis, whose terminal-once vocabulary
(`completed|unable|plan-rejected|cancelled`) answers what a WORKER did — and a
transport fault says nothing about that. A container that was created may also
have run code, which is exactly why the manager may not say `unable`.

**The custody rule is QUARANTINE, not refusal and not acceptance.** Chosen
from the two the finding permits, and it is the one the tree already means:

- accepting would synthesize a successful result from material no envelope
  vouches for — the thing `output.py` forbids;
- refusing would destroy the evidence of whatever the container did write
  before the fault, which is the reason quarantine exists at all;
- and the ending follows from it without new vocabulary: quarantined custody
  already makes `authorize_cleanup` settle `retained` rather than `complete`,
  which is the honest ending for an attempt whose result nobody can trust.

### PLAN 3–5 not started, and why not part-way

Implementing the record, the custody path that bypasses the disposition-gated
freeze, the authority ordering and the removal/absence/provider crossing, plus
the real Docker fault and the restart/mismatch/multiplicity/uncertainty/
custody-failure/sibling matrix, is one coupled round.

The immediately preceding Work, W32576, is the precedent: I part-did a seam
there and the review found it checked a refusal's spelling and called that its
identity. The same shape here would be a failed-start record whose custody
path was not actually reachable. I would rather hand over a pinned rule than a
seam that looks composed.

## State

**PLAN 1 and 2 done and evidenced; PLAN 3–5 open.** The pinned rule is above
and needs no ruling from elsewhere — the finding permits fail-closed or
quarantine and this chooses quarantine with the tree's own reasons. W32648
continues to gate W32382.

## 2026-08-28 — PLAN 3's first unit: the manager-owned failure record

Claimed W32648 at seq 34479. **No Git history or index was mutated.**

### The ruling, revalidated before acting

Approver M33800 is pinned in `FINDING.md` and **supersedes my own earlier
pinned rule**. My previous round chose QUARANTINE and wrote that into
`PROGRESS.md`; the ruling rejects the explicit copied no-envelope quarantine
record and names the existing unique per-generation, per-attempt result
directory as the custody boundary — untrusted, retained, never copied and
never admitted to the proposal pipeline. I revalidated that against the tree
rather than acting on my own superseded text.

### The record, and why the journal is it

**The start operation has already committed by the time the failure happens.**
`request_runtime_start` journals its intent and moves `execution_runtime` to
`start-requested`, and only then calls the adapter — so the failure cannot be
carried as that operation's refusal, and my first instinct (mark it durable)
was wrong for that reason.

So the failure is **its own journalled act**, `runtime.start-failed`. The
journal is the record and no new table is: `store.transact` stores the sealed
document as the operation's result, so it is durable, replayable and readable
back through the operation row.

**Its identity is exactly the facts the acceptance names** — the attempt, the
fixed assignment, the start operation it followed, the runtime reconciliation
attached, and the typed failure. An exact retry replays the one record; any of
those differing is an operation collision rather than a second account of one
act. That is the effectively-once guarantee the journal already owns, reused
rather than reinvented.

**It is not a worker disposition, and that is the whole point.** The record
moves no `worker_disposition` and no `output` axis; a case pins both still at
`none` and `open` after a failed start. A container created before a fault may
also have run code, so `unable` would be this manager inventing a worker's
account of itself, which `output.py` forbids in terms.

**A fault is recorded as a fault.** The closed pairing has no
`refused/start-failed`, and this module's own history says why — a wrapper that
retyped every failed start as one was measured against the boundary inventory
and broke three probes. So the record carries `kind: refusal` with the original
category, code and message, or `kind: fault` with the exception's own class and
text. My first cut manufactured `refused/start-failed` and the closed-pairing
assertion refused it immediately, which is the guard working.

**Reconcile first, then record.** The record names the runtime the
reconciliation attached, so recording first would durably say `None` about a
runtime that exists and leave the destroy crossing with a record disagreeing
with the attempt row it is meant to authorize.

### Seven cases, and two of them I had to correct

`TheFailedStartIsDurablyRecorded` covers the typed pair, the fault preserved as
a fault, no disposition written, exact retry replaying one record, a different
failure being its own act, the `uncertain` path recording `runtime_id: None`,
and the operator-visible refusal naming the record.

**The collision case first drove a second `request_runtime_start`, and that
measured the wrong guard**: after the first failure the runtime is attached and
the axis is `running`, so the second call is refused before the adapter is
reached. It would have passed while establishing an earlier rule. It now drives
the recording seam directly.

### A regression from the PREVIOUS Work that the full gate caught

W33936 left `run_vector(workspace_gid=None)` in place as an inert operand. The
operand inventory in `test_dependencies` refuses a public parameter that is not
declared, and **I did not run the full gate that round** — I ran the manager
subset and reported it as such, which is exactly the gap that let this through.
Declared with its reason. The three `test_oci` shards still fail from the
damage I reported under W33936 and are unchanged by this round.

### Gates

- `tests.manager.test_attempts` — 177 tests, OK
- the engine-owning modules together — 76 tests, OK, 4 narrow skips
- `tests.manager.test_dependencies` — 21 tests, OK
- full v12 parallel source — **9 failing shards**, and every one is accounted
  for: the accepted `test_boundary_inventory` baseline of six, checked by NAME,
  plus the three `test_oci` shards damaged under W33936 and reported there.
  Nothing this round added. Transcript:
  `evidence/w32648-gate-2026-08-28.txt`

A note on how the engine suites were run: my first attempt ran them in the
foreground while the full gate ran in the background, and
`test_a_second_incarnation_adopts_the_running_runtime` failed on a container
count. It passes alone and passed again once the gate finished — the two runs
were competing for the same daemon, which is exactly what the serial registry
exists to prevent and which I caused by ignoring it. Recorded because a
container-count failure that "goes away" is worth an explanation rather than a
retry.

## State

**PLAN 3's first unit is done. The cleanup crossing is not, and it is the next
coupled unit.** What remains is the ruled ending itself: an authorization that
does not require an intake receipt — because there is no frozen result and the
ruling forbids manufacturing one — which fences the exact attempt, removes the
exact attached container, positively observes absence, settles the delivery
roots, ends `cleanup = retained`, and leaves the result directory in place for
later explicit retention cleanup. Plus the real Docker post-create fault and
the restart/mismatch/multiplicity/uncertainty/custody-failure/sibling matrix.

I stopped here rather than part-building that crossing: it changes
`authorize_cleanup`'s neighbourhood, and the record above is its prerequisite
and stands on its own.

## 2026-08-28 — the identity [P0], and a structural blocker on the ending

Reclaimed W32648 at seq 34683. **No Git history or index was mutated.**

### [P0] The identity was inverted, and my own case asserted the inversion

The review is exactly right. `_start_failure_operation_id` hashed the attached
runtime and the typed failure INTO the operation id — and `store.transact` can
compare a changed signature only after the caller selects the SAME id. So a
changed fact chose a different row and never reached the collision guard at
all. Worse, the case I wrote required the two rows: durable evidence for the
opposite of the contract this Work records.

**Corrected.** The id is now stable for the one start act — attempt, fixed
assignment, start operation, and nothing that can change. The changeable facts
live in the SIGNATURE, where a difference is what the journal is built to
refuse. An exact repetition replays; any changed fact arrives at the same id
with another signature and fails closed with the first record intact.

The recorder is split so the rule can be driven and seen:
`_record_and_raise_start_failure` raises, and the reporting wrapper appends the
collision to whatever failure is already on its way out — a recorder that threw
would substitute its own problem for the one that actually happened. Two cases
now: the collision leaves one row and it is the first one, and the wrapper
reports rather than raises.

### The ruled ending is BLOCKED on a frozen contract, and this is new

I set out to implement it and stopped at a wall neither the finding nor
approver ruling M33800 anticipated. Measured:

- the only manager-to-adapter destroy seam is `documents.destroy_command`, and
  the frozen `worker-control-1.0` `runtimeDestroyBody` **requires**
  `intake_receipt_digest`:

      required: ['assignment_ref', 'runtime_attempt_id', 'runtime_id',
                 'intake_receipt_digest', 'retention_policy_digest']

- `OciAdapter.destroy` requires the same member at its own boundary.

**The ruled ending has no intake receipt and is forbidden to manufacture one.**
M33800 says exactly that: no second result, no copy, no invented disposition.
So the ending it orders — fence, remove the exact container, prove absence,
settle the delivery roots, retain the untrusted result directory, reach
`cleanup = retained` — cannot reach the adapter through the one seam that
performs it.

Three ways out, and choosing between them is not an implementation choice:

1. **Widen the frozen body** so the digest member admits a manager-owned
   failure-record digest, or add a sibling destroy body. That is a frozen 1.0
   contract change and the compatibility policy makes it explicit negotiated
   Work.
2. **Supply the failed-start record's digest in `intake_receipt_digest`.**
   Cheap, and I will not do it: a field named for an intake receipt carrying
   something that is not one is a lie in a durable command, and the next reader
   has no way to know.
3. **Rule that this ending settles without an adapter destroy** — recording the
   attached runtime and leaving removal to a later owner. That contradicts
   "remove the exact attached container", so it would supersede part of M33800.

### What I did NOT do

I did not build the crossing against any of the three. Picking one silently is
choosing a frozen-contract disposition on my own authority, which is the
failure this campaign has corrected in my work before — and the cheapest of
the three is the dishonest one.

### Gates

- `tests.manager.test_attempts` — 178 tests, OK
- `tests.manager.test_dependencies` — 20 tests, OK, 1 skip

No package gate is claimed: `tests/manager/test_oci.py` remains destroyed under
W33936 and its restoration is blocked on owner authority there.

## State

**The [P0] is corrected. The ending is blocked on a ruling** and W32648
continues to gate W32382 and W32576.

## 2026-08-29 — 3a revalidated, and the ruled ending landed

Claimed W32648 at seq 36555. **No Git history or index was mutated.**

### The provider gate cleared

W34998 is **closed satisfying**, so the sibling failed-start destroy command
and adapter capability exist. This Work CONSUMES them: it composes the body,
types the capability and reads the observation, and redefines none of it.

### 3a, revalidated rather than assumed

`start_failure_operation_id` is already the one stable identity the [P0]
required -- attempt, fixed assignment, start operation -- with the runtime,
the settled axis and the typed failure in the signature, and
`test_a_changed_failure_fact_collides_and_the_first_record_stands` asserts the
collision. What I found stale was the PROSE: `_record_start_failure`'s
docstring still described the superseded identity, naming the runtime and the
failure as part of it. A comment that contradicts the code is a second,
unmaintained specification, and this one described exactly the contract the
review rejected. Corrected.

The derivation also became public -- `start_failure_operation_id` -- because
the cleanup crossing has to name the identity the record was written under.
Recomputing it at the reader would be two spellings of one identity, and the
first time they disagreed only one would be the row that exists.

### 3b, the ruled ending

`authorize_failed_start_cleanup` is the sibling of `authorize_cleanup`, and a
sibling for the same reason W34998's command is one: what authorizes it is the
manager's own durable `runtime.start-failed` record, read back from the journal
rather than recomposed, and never an intake receipt.

The order is the ruling's: fence at the AUTHORITY -- asked of it rather than
inferred from an axis, because whether an assignment is still authorized is not
something this manager stores -- then remove the exact attached runtime through
W34998's capability, positively observe absence, settle the delivery roots on
that absence and nothing else, and end at `retained`.

**`retained` unconditionally, and that is a decision rather than a default.**
`_settle` chooses between `complete` and `retained` by counting what retention
kept. There is nothing to count here: no intake happened and no artifact was
decided. M33800 makes the untrusted result directory itself the material that
stays, so `retained` is the frozen axis's own word for it, and `complete` would
erase the reason the directory still exists.

**Nothing is fabricated**, which is the whole finding. No worker disposition,
no frozen output, no second result, no proposal admission, and the result
directory left exactly where it is -- each proved by a case rather than
asserted by the code.

### What I got wrong inside this round

Four probes I added to the boundary inventory did not REACH their named
boundary. `output_world` leaves its attempt `quiescent`, and the frozen axis
has no transition from there back to a live runtime -- so my driver's
`observe(... running)` was refused before the adapter was ever called, and all
four proved that refusal instead of the crossing they name. Caught by
`test_every_declared_probe_reaches_its_named_boundary`, which is the check that
exists for exactly this. The driver now writes the STATE a failed start leaves
-- an attached identity on a runtime not yet destroyed -- behind the build's
back, and `test_attempts` drives the real sequence through
`request_runtime_start`.

### Gates

- `tests/manager/test_attempts.py` -- **226 tests, OK**, including eleven new
  cases for the ending;
- every serial engine-owning suite together -- **180 tests, OK**, 10 Podman
  skips;
- every guard measured BY REMOVAL --
  `evidence/w32648-mutations-2026-08-29.txt`: six mutations, six named
  failures. One was STALE on the first run, from an over-escaped anchor in the
  harness itself, and is fixed rather than reported as a skip.
- full v12 parallel source -- `evidence/w32648-gate-2026-08-29.txt`.

### Probe coverage, and the two I am reporting

Sixteen of the eighteen boundary entries this cut opened are probed. The two
left are
`intake.py:_destroyed_failed_start adapter.destroy_failed_start` and its
`.lifecycle_state`, both under the label `a  teardown ending` -- and they are
the exact pair `intake.py:_destroyed` already carries unprobed, because
`_provider_ending` builds its label by interpolating the provider name and the
literal part is the same for both providers. Mine mirror a pre-existing family
rather than starting one; the family is worth its own correction and is not
this Work's.

## State

**PLAN 3–5 done. Passed back for independent review.** W32382 and W32576 wait
on this closing satisfying.

## 2026-08-29 — the [P0] and [P1] corrected

Reclaimed W32648 at seq 36909. **No Git history or index was mutated.**

### [P0] The record is bound to the runtime it authorizes destroying

The defect exactly: `_failed_start_record` read a committed row under a derived
identity and asked nothing else about it, while the command was built from the
CURRENT `attempt["runtime_id"]`. Two independently read facts, combined into
one authorization — so a record written when the failed start attached
`runtime-1` authorized destroying whatever the row named later.

Corrected on the pattern `_committed` already establishes for intake and
retention: the row's KIND is verified, the committed answer is decoded through
the journal's own reader rather than adopted as stored bytes, and four members
of the retained record are compared against the attempt — attempt id, fixed
assignment, start operation and runtime identity. A disagreement is
`integrity/schema`, not a reason to recompose: the journal stays the source of
the failure identity and digest, and if the row it authorizes has moved, this
manager cannot say which of the two describes the world.

**One member of the review's list is deliberately NOT compared, and I would
rather argue it than drop it silently.** `execution_runtime` is the one member
of the record that is allowed to move: it captures the axis at the instant the
failure settled, and a later reconciliation may legitimately observe the
runtime again — so requiring agreement would refuse a cleanup for having
looked. What the axis must be NOW is checked directly by the caller (an
`uncertain` axis refuses, an unattached runtime refuses), which is a stronger
statement than agreeing with a stale value.

### [P1] The real-engine path no longer fabricates anything

`test_a_post_create_failure_leaves_no_duplicate_and_no_container` used to
observe `worker_disposition="unable"`, freeze an output, take intake, decide
retention and reach the receipt-authorized `authorize_cleanup` — the whole set
of preconditions this finding exists to remove, and its own comment said so.

It now goes through `authorize_failed_start_cleanup`, against a real Docker
daemon, authorized by the record `request_runtime_start` wrote when the start
above really failed. Measured rather than assumed: one real `run` vector is
issued and the container really exists before the ending removes it. The case
asserts `retained`, `execution_runtime = destroyed`, an empty daemon, a torn
down launch root, `worker_disposition` still `none`, `output` still `open`, no
intake row at all, and a sentinel surviving in the untrusted result directory.

### The harness caught a gap in my own correction

"the record's kind is verified" measured **zero** on the first run: I added the
check and no case drove it. A committed row of another kind sitting at the
derived identity is exactly the thing the check exists for, and it now has a
case that corrupts the journal's `kind` behind the build's back and requires
the refusal before the adapter. Eight mutations, eight named failures.

### Gates

- `tests/manager/test_attempts.py` — **228 tests, OK**;
- `tests.manager.test_negative_race_endings` verbose — **4 tests, OK**, one
  Podman skip, with the post-create-fault case passing through the new
  crossing;
- every other engine-owning and lifecycle serial suite — **177 tests, OK**,
  9 Podman skips;
- full v12 parallel source — `evidence/w32648-gate-2026-08-29.txt`. The
  `test_attempts` shard this Work owned is green; what remains is the accepted
  baseline plus three shards belonging to other Works out for review.

### Reported rather than fixed

`tests.manager.test_runtime_lane` (two shards) is W32649's open second round,
and `tests.manager.test_workspaces.TheConfiguredWorkspaceGroupRecord` is a
regression W33936's reviewer added after I passed that Work back. Neither is
this Work's to correct.

## State

**Passed back for independent review.** W32382 and W32576 wait on this closing
satisfying.
