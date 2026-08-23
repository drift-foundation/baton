# Drain managed dispatch before maintenance

## Observed — 2026-08-22

The managed stack keeps the pipeline saturated: when one handler relinquishes
its claim, readiness immediately offers another eligible Work. This is correct
during ordinary operation but leaves no deterministic maintenance boundary.
An operator waiting to restart after "the current item" can repeatedly miss
the gap because another participant has already claimed the next item.

The W4303/W2845 sequence demonstrated the problem. The operator wanted K to
finish her current correction before restarting the quarantined Codex path.
K passed W4303 and immediately claimed W2845, extending the interval during
which stopping the whole stack would interrupt live work.

## Confirmed decision — 2026-08-22

Add a deployment-wide managed-dispatch **drain** control. Drain is lifecycle
state, not a Work phase and not an instruction to an agent.

When drain is requested:

1. The manager snapshots assignments that are already claimed.
2. Those exact handlers may finish, pass, close, or otherwise relinquish their
   current claims.
3. No new Work offer, readiness delivery, or assignment may start. A pass may
   make Work ready for its next Route but must not wake that Route while drain
   remains in effect.
4. Once every snapshot claim is relinquished, managed dispatch becomes
   `paused`. Services may remain alive for status and operator inspection.
5. An explicit `resume` returns the deployment to ordinary dispatch.

An unclaimed or merely queued Work is never part of the finishing round.
Already-offered but unclaimed attempts must be fenced or allowed to expire and
must not become new claims after the drain boundary. A failed or orphaned live
claim prevents `paused`; drain reports that exact blocker rather than claiming
quiescence or silently forcing release. Recovery remains an explicit,
auditable operation.

Dispatch state is deployment-global and appears in the persistent TUI header,
not in any Work row or Work phase. The header distinguishes `Dispatch:
RUNNING`, `Dispatch: DRAINING (N active)`, and `Dispatch: PAUSED`; Teams may
show the identities still preventing pause. Stop/restart tooling exposes the
same state and can require `paused` for a graceful maintenance path while
retaining a separately explicit emergency stop. A bounded wait may return the
still-active blockers but never converts a timeout into cancellation.

## Acceptance boundary

- One operator action suppresses dispatch across every managed participant in
  the deployment.
- Claims active at the boundary can complete normally; later Work is not
  offered or claimed.
- Pass/close races at the boundary cannot leak one new assignment.
- Failed and orphaned claims remain visible blockers with exact identities.
- Status/TUI distinguish `running`, `draining`, and `paused`.
- Resume is explicit and auditable.
- Restart recovery preserves the drain state rather than accidentally
  re-enabling dispatch.
- Focused tests cover simultaneous completion, pass-to-ready, pre-claim offer,
  failed handler, timeout, restart, and resume behavior.

## Authority placement clarification — confirmed 2026-08-22

The deployment-global dispatch state belongs in Baton's SQLite authority, not
in a parallel lifecycle-control file. Calling it lifecycle state distinguishes
it from a Work phase; it does not create a second coordination authority.

The drain transition and claim admission must serialize through the same
authority transaction boundary. The authority records the dispatch mode, a
monotonic control generation, the drain boundary, actor, and time. A claim
whose admission occurs after that boundary is refused while mode is
`draining` or `paused`; claims already live at the boundary may perform only
their ordinary assignment-ending transitions. The last such claim ending can
move the global state to `paused` atomically. `resume` advances the control
generation and re-enables claim admission.

Readiness, ACP bridges, lifecycle commands, status, and the TUI consume this
one canonical projection. They may suppress unnecessary wakeups, but their
files, process memory, or service state never decide whether a claim is
admissible. Restart therefore reconstructs the exact drain state from SQLite.
This requires an authority schema and projection-version change.

The state is protocol-discoverable to every authorized participant. Root/home
and readiness projections distinguish `running`, `draining`, and `paused` and
include the control generation, transition time, requesting actor, and the
bounded identities/count of claims still preventing pause. A readiness client
therefore receives an explicit paused/draining answer rather than mistaking an
empty actionable set for ordinary idleness. The Work event journal records the
assignment-ending acts as usual; a global control journal records drain
requested, pause reached, and resume without manufacturing Work messages.

### Storage shape — confirmed 2026-08-22

Store current dispatch authority in one dedicated typed singleton table, not a
JSON blob, not a per-Work column, and not duplicated lifecycle metadata. The
row carries at least the closed mode (`running`, `draining`, or `paused`), a
monotonic control generation, the authority-sequence drain boundary, the
requesting participant, and the current-state transition time. Existing
operation/journal machinery preserves idempotence and chronological control
events.

Claims still preventing pause are derived from canonical live assignments at
the drain boundary; their identities and count are not copied into a mutable
JSON field. Claim admission and dispatch-mode transitions read and update the
typed row in the same SQLite transaction. JSON is only the external projection
of these constrained columns and derived claims.

## Reviewer revalidation — 2026-08-22

### Observed implementation boundaries

- `src/baton_work/authority.py` is at schema 27. `Authority._write` is the one
  mutation boundary: it starts `BEGIN IMMEDIATE`, allocates the authority
  sequence, runs the transition, records events and the idempotent operation,
  then commits. This is the transaction that must serialize drain/resume with
  claims. The current tree is a fresh-authority product with no schema
  migration path, so this feature advances the schema rather than teaching an
  old store a partial drain representation.
- `claim_work` in `src/baton_work/transitions.py` performs route, readiness,
  claimant, blocker and one-active-slot admission before setting the Handler.
  The dispatch-mode refusal belongs inside that transition, immediately before
  assignment, not in a CLI wrapper or readiness producer.
- Handler removal is not confined to `pass`, `release`, and `close`.
  `_recompute_ready`, `set_phase`, blocking `say`, and other audited paths can
  clear `handler_team`/`handler_member`. A pause-reached check copied into a
  short list of public verbs would therefore strand a drain after a legitimate
  final release. The post-transition portion of `Authority._write` is the one
  complete place to detect that `draining` has no live assignments and record
  `paused` in the same commit.
- The Work row has a current Handler and assignment `episode_seq`, but no
  separate claim-created sequence. Because drain and every later claim
  admission serialize under the same writer transaction and later claims are
  refused, the live Handler set immediately after the drain commit is exactly
  the boundary set. The recorded boundary sequence plus current assignments is
  sufficient; a second mutable blocker snapshot is unnecessary.
- `participant_actions` is shared by managed readiness, the TUI Inbox, and
  human-facing counts. Globally filtering it would hide obligations from the
  operator. `wait_actionable` is the managed delivery boundary and should
  apply dispatch filtering while the unfiltered participant projection
  remains visible to interactive clients.
- Both managed bridges revalidate the exact action key with `wait timeout=0`
  immediately before a turn. Hiding an unclaimed action from `wait` retires an
  already-forwarded pre-drain offer; the transactional claim refusal closes
  the remaining revalidation-to-claim race. Both bridges already delay after a
  successful non-timeout result that forwards nothing, so an explicit paused
  result does not create a hot loop. `runtime_refresh` is adapter-only and does
  not start a model turn.
- `tools/infra.py` currently accepts manifest version 1 and only
  `start|stop|status`. It has no explicit canonical Baton control identity.
  Inferring a drain command from a service argv would repeat the configuration
  ambiguity this lifecycle manager is designed to prevent.
- The TUI header is composed in `_render_header` and `_render_breadcrumb`.
  Both must reserve a compact dispatch label before drawing the participant
  identity last; adding it only to the top-level tab row would make the global
  state disappear during drill-down.

### Proposed patch boundary

1. Advance the authority schema and add a constrained singleton
   `dispatch_control` row containing mode, generation, boundary sequence,
   actor team/member, and transition time. Seed a fresh authority as
   `running`. Add a typed global control-event table keyed by authority
   sequence for `drain_requested`, `pause_reached`, and `resumed`; do not mint
   Work messages or overload the one-Work event row.
2. Add idempotent authority mutations for drain and resume plus pure status
   and paged control-history reads. Drain advances the generation and records
   its own mutation sequence as the boundary. Zero live assignments may enter
   `paused` in that same commit. Repeated drain/resume operations with the same
   operation identity replay; semantically conflicting state requests refuse
   rather than silently resetting the boundary.
3. Refuse every new `claim_work` admission in `draining` or `paused`, including
   direct CLI claims. Existing handlers retain the ordinary assignment-ending
   verbs; drain grants no force-release power. After every successful write,
   the central writer checks whether a draining authority has reached zero
   live handlers and, if so, records `pause_reached` and changes the singleton
   before commit.
4. Project one bounded `dispatch` object from the same read snapshot through
   home/root, summary/status, and `wait`: mode, generation, boundary, actor,
   transitioned time, total blocker count, a bounded ordered blocker list, and
   truncation/continuation disclosure. Blockers name Work, Handler, assignment
   episode, and useful runtime state, but runtime failure never changes whether
   the canonical assignment blocks pause.
5. Keep `participant_actions` unfiltered. In `wait_actionable`, `running`
   returns the ordinary set; `draining` returns only Work already claimed by
   that exact participant plus adapter-only `runtime_refresh`; `paused` returns
   only `runtime_refresh`. Obligations, trials, pokes, and unclaimed Work remain
   visible to humans but do not wake a managed model. A non-running empty result
   returns immediately with `timed_out=false` and the dispatch object, allowing
   existing bridge backoff and delivery-memory retirement to fence old offers.
6. Make lifecycle manifest version 2 name one explicit control triple
   (canonical binary, config, participant). Add distinct drain/status/resume
   operations. Graceful stop reads canonical status and refuses unless paused
   before signalling any service; a separately named emergency stop preserves
   its exceptional meaning. Start never resumes implicitly, and status reports
   the authority state even when services are stopped.
7. Advance the additive JSON projection minor from 12.3, teach both shared
   readiness-envelope tests the typed dispatch object, render
   `Dispatch:RUNNING`, `Dispatch:DRAINING (N active)`, or `Dispatch:PAUSED` in
   both TUI header paths, and update the operating guide and setup/lifecycle
   documentation.

The global journal can use the same authority sequence as the transition that
caused it. In particular, the last assignment-ending act and
`pause_reached` are one atomic authority instant, recorded in their separate
typed journals; allocating a synthetic second write would create a false race
window and is not required for chronological projection.

### Focused regression matrix

- Drain with zero, one, and simultaneous multiple live claims; exactly one
  pause-reached event and one monotonic generation change.
- Claim racing drain on separate connections in both commit orders: the claim
  is either in the boundary set or refused, never admitted after it.
- Every Handler-clearing path can release the last blocker and atomically reach
  paused; a pass may make destination Work ready without waking or claiming it.
- A pre-drain unclaimed action already held by each bridge disappears on its
  exact `timeout=0` revalidation; a direct stale claim also refuses.
- Failed/unknown/orphaned runtime state leaves the canonical claim as an exact
  visible blocker. Drain timeout reports it and performs no cancellation or
  release.
- Obligations, trials, pokes, and unclaimed Work remain visible in Inbox/home
  while managed `wait` suppresses their model wakes; a claimed participant can
  still receive its one finishing Work. Adapter runtime refresh remains live.
- Restart in draining and paused reconstructs the same mode/generation/boundary
  from SQLite. Start does not resume. Graceful stop refuses before any signal
  unless paused; emergency stop is explicit.
- Resume is authorized, idempotent by operation identity, audited, wakes the
  ordinary level-triggered projection again, and cannot resurrect a stale
  assignment episode.
- Home/readiness/status snapshots agree on mode and blockers; blocker
  truncation is explicit; top-level and drilled TUI headers retain both the
  dispatch label and participant identity at narrow widths.

### Open authority decision

The confirmed record defines what drain and resume do but not who may perform
them. The current accepted configuration has only the narrow `recover`
capability and the much broader `config` capability. Route membership is not
global lifecycle authority, a runtime `actionOwner` is transient adapter state,
and reusing `config` would unnecessarily couple roster mutation with
maintenance control. The reviewer recommends a new narrow `dispatch`
participant capability, checked transactionally by drain and resume. This
requires an explicit authority ruling before implementation.

## Dispatch authorization — confirmed 2026-08-22

The authority approves the recommended narrow accepted-configuration
`dispatch` capability. Both drain and resume require that capability, checked
inside the same authority transaction that changes the dispatch singleton.
Status remains readable by every participant in the accepted configuration;
reading mode, generation and bounded blockers does not require `dispatch`.

The initial deployment grants `dispatch` only to `baton.slaw`. The authority
explicitly rejects every inferred substitute:

- a Work Route or held role is local scheduling responsibility, not
  deployment-global maintenance authority;
- runtime `actionOwner` is transient adapter state, not accepted authority;
- `recover` authorizes one narrow orphan-claim correction and does not grant
  global drain/resume;
- broad `config` authority does not implicitly include `dispatch`.

This resolves the open question above without rewriting its history. Add
`dispatch` to the strict accepted capability vocabulary, update the repository
configuration/example and lifecycle control identity to name the intended
holder explicitly, and document the required accepted-generation rollout.
The source implementation does not silently edit a live deployment config or
infer the holder from service argv. A deployment whose accepted configuration
grants nobody `dispatch` remains readable but correctly refuses drain/resume
until an authorized configuration generation grants it.

The transaction checks the actor's current accepted capability at the same
writer boundary as the mode transition. An operation replay still resolves by
its committed operation identity, while a new drain or resume from an actor
who no longer holds `dispatch` refuses; stale process memory never preserves
authority across a configuration change.

## Implementation revalidation — 2026-08-22 (baton.claude)

Every anchor in the reviewer's proposed boundary was re-checked against the
tree before it was used. The four that held exactly as recorded: schema 27 and
`Authority._write` as the one mutation boundary; `claim_work` performing
admission before assignment; Handler removal reaching well past `pass`,
`release` and `close`; and `participant_actions` being shared by managed
readiness, the TUI Inbox and the human counters. The implementation follows
them.

Six decisions had to be made beyond what the boundary pins. They are here
rather than in the diff, because each could defensibly have gone the other
way.

### 1. The graceful stop is `stop-drained`; plain `stop` is unchanged

**This diverges from the proposed boundary**, which had graceful take the
plain name and the immediate stop take a new one. Revalidating that against
this tree:

- `stop` is an established operator verb with its own regression suite, and
  27 existing cases mean it;
- every version-1 manifest can still be stopped and CANNOT ask the authority
  anything, so making the plain word require a control triple would strand
  them;
- the immediate stop must keep working when the authority is unreachable,
  which is exactly when an operator needs it.

Silently making the familiar word require a healthy authority would turn an
emergency tool into one more thing that can refuse. So the NEW capability got
the new name, and `stop-drained` reads the canonical state and refuses before
signalling anything. Flagged for the reviewer: this is the one place the
implementation deliberately did not do what the boundary proposed.

### 2. The control journal is keyed `(seq, kind)`, not `seq`

Two control acts DO share one authority instant, legitimately: draining a
deployment with nothing live is `drain_requested` and `pause_reached` at the
same sequence, because the finishing round was empty at the moment it was
drawn. The boundary already says the last assignment-ending act and
`pause_reached` are one instant; this is the same rule one case over. Two
events of the same KIND at one instant remain impossible, which is what the
composite key says.

### 3. `dispatch_events.seq` references `events(seq)` DEFERRABLE

The writer allocates the sequence, runs the mutation, and inserts the `events`
row last. An immediate foreign key fires while that row is still pending and
would force the journal to be written outside the act it describes. Deferring
keeps the reference real and leaves the ordering the writer's business.

### 4. A non-running `wait` returns immediately, `timed_out: false`

The boundary asks for an explicit paused/draining answer rather than an empty
set. It could have blocked out the caller's timeout and answered at the end;
it does not, because a managed client that waited its full timeout would learn
"nothing for you" and could not tell a paused deployment from an idle one.
Both bridges already back off after a non-timeout result that forwards
nothing, so this does not spin.

### 5. Blockers are bounded with EXPLICIT truncation

`blocking_claims` is the total, `blockers` is the bounded list, and
`blockers_truncated` says when they differ. A silently cut list reads as
"these are all of them", which for an operator waiting to restart is the one
wrong answer.

### 6. `drain` and `resume` are managed-workflow policy EXCLUSIONS

The W220 registry demands every public mutation be authorized by the
managed-workflow profile or recorded as deliberately excluded. These are
excluded: a managed turn that could drain would suspend the stack it is
running in, and one that could resume would undo the operator's maintenance
boundary while the operator is acting on it. The ruling grants `dispatch` to
`baton.slaw` alone; an execution rule authorizing the command would be a
second, contradicting answer to who may.

### Found while implementing, not in the boundary

- **The TUI label needed one shared painter.** The right edge of row 0 is
  drawn twice — top-level and drilled — and adding the label to one would have
  made the deployment-global state vanish exactly when an operator drilled
  into a Work. Both paths now call one `_render_right_edge`, with identity
  still drawn last and overdrawing, and the dispatch label furthest left of
  the three so a narrow terminal loses it before it loses who is signed in.
- **The label is empty while `running`.** A label always present trains the
  eye to ignore it, and RUNNING is the state an operator already assumes.
- **The fixture grants `dispatch` directly.** The shared test document
  predates the capability; the regressions write the grant into
  `member_capabilities` rather than rewriting a fixture every other suite
  shares. The authority's own transactional check is still what every case
  exercises.

### Acceptance not established here

The live deployment still grants `dispatch` to nobody and its `infra.json` is
version 1, so it reads `running` and correctly refuses drain and resume. Both
are operator acts with their own accepted generation — plan item 8 — and this
Work deliberately does not edit a live configuration.

## Independent review findings — 2026-08-22 (baton.codex)

**Confirmed:** the transactional claim/drain ordering and write-boundary
settlement satisfy the pinned exclusion boundary. A claim is either captured
in the finishing round or refused after the drain commit, and a held Work
remains actionable until it relinquishes. The implementation's deliberate
`stop-drained` name is accepted: keeping plain `stop` independent of authority
health preserves both version-1 compatibility and the emergency stop path.

**Observed — changes requested:** three projection/audit boundaries remain:

1. `dispatch_history` pages rows by `seq`, but two event kinds legitimately
   share one sequence. A one-row page returns one empty-drain event and its
   `WHERE seq < ?` continuation permanently skips the sibling event.
2. `dispatch_view` reads the singleton and live Handler set without
   `_read_snapshot`, and `wait_actionable` reads its action and dispatch
   projections separately. A final pass interposed between the singleton and
   Handler reads produces the non-canonical answer `draining` with zero
   blockers, even though that commit made the authority `paused`.
3. `_settle_dispatch` timestamps `pause_reached` with private wall time rather
   than `store.clock()`. Under an injected clock, the two events belonging to
   one empty-drain authority instant receive different time origins and the
   singleton exposes the wall-clock value.

The deterministic reproductions are retained in
`evidence/repro_projection_edges.py`; the complete analysis and correction
boundaries are in `review-2026-08-22T16-25-29Z.md`.

## Correction after independent review — 2026-08-22 (baton.claude)

Three P2s, all reproduced before any edit. Evidence:
`evidence/correction-projection-edges-2026-08-22.txt`.

### The history cursor could not traverse its own journal

`dispatch_events` permits two kinds at one authority sequence — the design
says so, and an empty drain is the case. The reader then ordered by `seq`
alone, limited ROWS and resumed with `seq < next_before`, so a page size that
bisected the pair made the second event unreachable. The journal was complete
only for callers who happened to pick a page size that did not cut through an
instant.

`limit` counts INSTANTS now: the sequences are chosen first, every event at
them is returned together, and the cursor names the last instant. Sibling
order is written out rather than left to storage order, which is not an order.
An instant is indivisible for the reader for the same reason it is indivisible
in the writer.

### Two snapshots described a state that never existed

`dispatch_view` read the singleton and the live Handler rows independently, so
a final pass committing between them returned `draining` with zero blocking
claims — while that same commit had made the mode `paused`. It is
self-snapshotting now, and `wait` derives its action set and the dispatch
state under one outer reentrant snapshot, which is what the pinned contract
asked for and what my own implementation note claimed.

### The settlement used the wrong clock

`_settle_dispatch` called the private wall clock while the act it completes
used the authority's, so under an injected instant the two same-sequence
events disagreed and the singleton inherited the host's time. A settlement
completing an act is timestamped by that act's clock.

### Recorded because it changed an existing test's fixture

`test_w321_readiness_cadence`'s "meanwhile" commit ran on the SAME connection
from inside a patched `participant_actions`. A connection holding a read
snapshot cannot also write, so that fixture raised once `wait` took one
snapshot. The commit moved to a second connection; the assertion is unchanged,
and a second writer is the more faithful "meanwhile" anyway. The alternative
was dropping the one-snapshot boundary, which is not a trade worth making for
a fixture mechanism.

### Worth recording about the mutation checks

Two of the three first-attempt mutations left the suite green — they were too
weak to reproduce the defects — so they were redone against the exact original
code paths. A mutation that does not fail is not evidence about the test.

## Independent correction re-review — 2026-08-22 (baton.codex)

**Confirmed corrected:** history pages whole authority instants with a
deterministic sibling order and no cursor loss. `dispatch_view` is
self-snapshotting, and `wait_actionable` derives its action set and dispatch
mode under one outer reentrant snapshot. Automatic pause no longer calls the
private wall clock.

**Observed — changes requested:** the clock correction passes a fresh
`self.clock()` sample from `_write`, not the drain mutation's already-sampled
instant. An empty drain therefore calls the injected clock twice. With a
ticking clock, its same-sequence `drain_requested` and `pause_reached` events
carry different timestamps and the singleton ends at the second, although the
design makes those events one indivisible authority instant. The constant
`BATON_WORK_NOW` regression cannot expose the second sample.

Reuse one sampled transition time for every control transition belonging to
one write. The exact finding and correction boundary are in
`review-2026-08-22T17-57-11Z.md`; deterministic evidence is retained in
`evidence/re-review-single-instant-clock-2026-08-22.txt`.

## Round-3 correction — 2026-08-22

The re-review is correct and was reproduced before any edit. It corrects my
own round-2 correction: I fixed the clock SOURCE and left the number of
SAMPLES at two.

**One act, one instant — and the sample is taken once.** `Authority.instant()`
is the sampled instant of the write in progress. `_write` takes it once,
inside the transaction and after the operation-replay check, and clears it in
a `finally` however the write ends. `drain_dispatch`, `resume_dispatch` and
`_settle_dispatch` all read it back. Two readings of one clock are still two
instants whenever it advances between them, and an empty drain writes
`drain_requested` and `pause_reached` at ONE sequence precisely because they
are one indivisible committed act.

**`instant()` refuses outside a write** rather than falling back to `clock()`.
A caller with no open transaction is asking for wall time, not for this act's
instant, and answering quietly with a fresh reading is exactly how the two
drifted apart. Both the refusal and the `finally` are witnessed by a
regression — a leaked instant would be read by the NEXT act as its own, which
is the same defect with a longer window.

**Why my round-2 regression could not see this.** It pinned `BATON_WORK_NOW`
to one constant, so every sample was identical and it could not distinguish
"same clock source" from "same act instant". It is retained anyway: it is the
one that pins the source, and it exercises the subprocess path.

### One call site outside this Work changed, deliberately and recorded

`create_trial`'s in-lock deadline recheck read `store.clock()`, and `_write`
taking a sample of its own consumed a moment that
`test_ws2_due.py::test_a_round_rechecks_deadline_after_entering_the_write`
had budgeted. The recheck now reads `store.instant()` — which is what R42's
own comment above it already asked for in words, "ONE transaction-local
instant" — and since the sample is taken after BEGIN IMMEDIATE the recheck
still happens strictly inside the lock. The WS-2 property is unchanged and the
test's assertion was not touched.

The other in-mutation `store.clock()` call sites in `transitions.py` were
deliberately NOT converted. Each is one act sampling once for its own fields,
which is not the reported defect, and they are other Works' code. `instant()`
is available to them and refuses outside a write, so adopting it later is
safe. Named here rather than done quietly in a Work that was not asked for it.

## Round-4 independent review — 2026-08-22

**Confirmed corrected:** `_write` samples the authority clock once after the
write transaction and operation-replay check, and clears the sample in a
`finally` on every exit. Drain, resume, and automatic pause settlement reuse
that exact value through `instant()`, which refuses outside a live write.

The ticking empty-drain case, later final-release case, and refused-write leak
case establish the stronger one-act/one-instant property rather than merely a
shared clock source. The adjacent `create_trial` deadline recheck correctly
uses the same transaction-local sample and its WS-2 regression remains green.

**Signed off for operator rollout.** Focused W4615 plus WS-2 deadline tests
pass 67/67 and `git diff --check` is clean. Live accepted-configuration and
lifecycle-manifest changes remain the operator gate. Review:
`review-2026-08-22T18-38-04Z.md`.

## Operator rollout ruling — 2026-08-22

**Approved:** grant the accepted-configuration `dispatch` capability only to
`baton.slaw`. No Route handler, managed agent, runtime owner, `recover`
holder, or general configuration capability inherits drain/resume authority.

**Approved:** the next deployment uses lifecycle manifest version 2 with one
explicit control triple naming its canonical Baton binary, accepted config,
and `baton.slaw`. The global dispatch state remains in the SQLite authority;
the manifest identifies how the lifecycle controller reads and mutates it.

**Approved:** retain ordinary `stop` as the emergency/unconditional path,
including when the authority is unhealthy or unreachable. Planned maintenance
uses the separately named `stop-drained`, which reads canonical state and
refuses before signalling any service unless dispatch is `paused`.

Roll out through a fresh schema-28 / projection-12.4 authority; deployed
`c529b28` is schema 27 / projection 12.3 and is not upgraded in place. Before
closing W4615, verify a live `running -> draining -> paused -> running` cycle,
including refusal of a new claim after the drain boundary and successful
`stop-drained` only while paused.
