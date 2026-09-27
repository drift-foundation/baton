# Implementer progress — W275776 (Child C)

Kept by baton.claude. Each entry records what was measured, not what was intended.

## 2026-09-27 claim 284804 — the uncertain half of restart recovery, measured then closed

Dossier created and bound at revision 1 (bind 284880) before any edit, per owner brief 275776.
Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     41f151e03e1b   PRODUCT, exclusive custody
    v12/python/tests/manager/test_boundary_inventory.py   2457b3142a9d   entry declaration only
    work/.../test_restart_recovery.py                     99450de75f41   NEW selector

### What I measured before writing anything

The FINDING recorded a question rather than a claim: `tools/job_manager.py:_governed_candidates`
selects candidates by `governance.overdue(...) is not None`, so is an outstanding token with an
unresolved LAUNCH reconciled after a restart? I answered it on the connected path, at two REC-3
cuts, with a fresh `ControlStore` handle standing in for the restart:

| cut | attempt row after | token record after | `overdue` |
|---|---|---|---|
| adapter's reply lost (`OSError`) | `running`, `runtime-1` attached | outstanding, container bound, **activation admitted and never settled** | `None` |
| manager KILLED (`KeyboardInterrupt`, no settlement ran) | **`start-requested`, nothing attached** | outstanding, container bound, **activation admitted and never settled** | `None` |

Both cuts leave exactly one engine crossing, and in both the TOKEN remembers the container the
attempt row does not. And in both, `overdue` answers `None` -- the deadline has not passed --
so the reclaim pass does not select them, and `grep -rn "outstanding\b"` over `src/` and
`tools/` finds no other consumer of the outstanding set. **So the uncertain half of TOK-10's
"restart recovery processes overdue and uncertain tokens before admitting conflicts" had no
reader at all**: until the lifetime ran out, a container that may have been writing the
resource was nobody's candidate. That is the gap this claim closes, and it was measured rather
than assumed.

### What I added, and deliberately what I did not

`tokens.unresolved(control, domain)` answers the uncertain set: every outstanding, unrevoked
generation whose ACTIVATION was admitted and never settled, with the exact attribution a
caller needs -- execution, operation, launch, container, deadline, expiry and revision.

"Admitted and never settled" is the right fact because of Child A's accepted rule: a refusal or
a fault can follow a REAL activation, so those outcomes are deliberately left unsettled to keep
the resource held. That makes it precisely "this manager does not know whether its container
started" -- an actionable unknown with exact references, which is REC-4's requirement.

**It decides nothing.** No engine is asked, no record written, nothing returned or revoked. The
ACTION stays with the accepted owners (`reconcile_runtime`, `intake`), which are read-only for
this Work, so the selector drives them rather than reimplementing them.

### Measured

`test_restart_recovery.py`: **49 PASS 1.024s** standalone. Seven cases are mine; the rest are
Child A's connected cases inherited through its fixture, which is the cheapest regression
evidence available -- an ending that stopped working under this change would fail there
without any case of mine. My seven:

* a lost reply leaves a findable unresolved generation naming the exact container;
* a KILLED manager leaves the same, with the attempt row still at `start-requested`;
* nothing is unresolved before a launch is attempted (REC-3's first cut);
* a settled activation is NOT unresolved -- the reader must not sweep healthy executions;
* reconciling from that set attaches the exact container, with the engine crossing count
  UNCHANGED (no duplicate container dispatch) and the resource still held;
* an unreachable engine keeps the hold and still names the execution (TOK-10);
* the hold still excludes a conflicting acquisition ("before admitting conflicts").

Predecessors' accepted evidence re-run: Child A's `test_token_lifecycle`,
`test_connected_lifecycle`, `test_expiry_reclaim`, `test_governed_endings` all PASS; Child B's
`test_renewal_arbitration` (46) and its reviewer probes `review_final_arbitration` and
`review_expiry_clock_gap` all PASS. `test_intake`, `test_single_worker`, `test_tool` PASS.
`test_boundary_inventory` 26 failures with the failure **name-set byte-identical** to the
accepted baseline and `tokens.py` at **0 unowned**; `test_dependencies` 73, unchanged.

### The gap that remains open, and why I did not close it here

**No production caller reads `unresolved` yet.** The pass that should consume it is
`tools/job_manager.py:pass_over_attempts`, whose candidate scan is the `_governed_candidates`
function measured above -- and `tools/job_manager.py` is NOT in this Work's pinned paths. The
brief excludes consumer migration, so I have not edited it. The shape it would need is one
call beside the existing overdue scan: reconcile each `unresolved` generation through
`reconcile_runtime` before the expiry sweep, which is exactly what my selector drives by hand.
I am reporting this as the next decision rather than taking it: if the reviewer pins
`tools/job_manager.py` for this Work, the wiring and its proof are small and the selector
already demonstrates the behaviour end to end.

### Remaining for this child

1. The wiring decision above.
2. The rest of REC-3's cut list within this child's scope: during freeze, during retention,
   after verdict, during handoff, during cleanup -- restart behaviour at each, on the connected
   path.
3. Engine failure/recovery beyond "unreachable at reconciliation": the supported retry path
   and its exact unresolved report.
4. The integrated G1 acceptance statement across Child A, Child B and this child.

## CORRECTION to the heading above

The previous entry is titled "the uncertain half of restart recovery, measured then closed".
**"Closed" was wrong and the review is right to say so.** What that claim delivered was the
reader plus a selector that drove the observation and the reconciliation BY HAND; the
production pass still made zero engine calls and reported nothing for an unexpired unsettled
launch, which the reviewer's `review_restart_tick_20260927.py` demonstrated independently.
The measurement in that entry stands; the word "closed" is withdrawn. R1 below is what closes
it.

## 2026-09-27 claim 284944 — R1: the production pass now visits the uncertain tokens

Paths newly pinned by the review and edited here: `v12/python/tools/job_manager.py` and
`v12/python/tests/job_manager/test_tool.py`. Digests:

    v12/python/tools/job_manager.py              6bf1f7e0450b   PRODUCT, newly pinned
    v12/python/tests/job_manager/test_tool.py    edbd89bce265   focused recovery proof
    v12/python/src/baton_v12/worker_manager/tokens.py   41f151e03e1b   unchanged this claim

Reproduced `review_restart_tick_20260927.py` first: **1 FAIL** — zero engine calls, empty
report, no cursor.

### The wiring

`_observing_unresolved` runs FIRST in `pass_over_attempts`, before the overdue reclaim and
separately from it, with **its own rotation cursor** (sharing one would let a run of overdue
candidates starve the unresolved ones, and the two sets barely overlap — an unresolved launch
is usually not overdue). The row discovery is now `_governed_rows`, split out of
`_governed_candidates` so both halves ask their own eligibility question over the same query,
unchanged and still ordered by identity so both rotations stay stable.

For each unresolved generation it asks the engine ONE bounded question through the `observe`
verb the reclaim already has, outside every transaction, and reports the exact
domain/generation/execution/operation/launch/container/deadline with the observation. Per
attempt fault isolation is preserved.

### What it deliberately does NOT do, and why — the part worth stating

**It does not attach.** `attempts.reconcile_runtime` is the accepted act that attaches, and
its `list` compares the engine's reported image against the exact image THAT DELIVERY
resolved — a fact the lean reclaim adapter cannot know. Handing it an adapter that skipped
that comparison would be a second, weaker spelling of a boundary that exists precisely to
stop a stale image being adopted on matching labels alone. So the observation lives in the
pass and the attachment stays with the worker path that holds the delivery
(`tools/single_worker.py`'s restart branch, which already reconciles from `start-requested`).
This pass makes that work discoverable and keeps the resource held until then.

**And attachment would not be a settlement anyway.** Finding the container alive says nothing
about whether the launch this manager never saw return completed, and it is not permission to
dispatch again; the activation stays unsettled, which is what keeps the resource held. An
`absent` answer is likewise not an ending — the accepted ending for a proved non-launch needs
the failed-start record this cut may never have written. Both are reported, neither is acted
on. That is the reviewer's "do not mistake attachment for cessation or settlement of a
still-pending launch", followed rather than paraphrased.

### Five focused cases in the pinned suite

Driving the REAL composed pass (`job_manager._reclaiming`, the one `serve` is handed) over
real rows and a controlled runner, with a new `_unsettled_governed_attempt` fixture built
from the same intake fixture and the same accepted acts as the overdue one beside it,
differing in exactly two deliberate ways: the activation is admitted and never settled, and
the clock is NOT moved past the lifetime.

* the pass observes the exact container the TOKEN bound, and reports every exact reference;
  nothing is reclaimed, and the resource is still held with its activation unsettled;
* an unreachable engine holds and says so per attempt;
* a LATER TICK RETRIES once the engine is back — the hold is not terminal;
* the pass never starts or dispatches anything: no vector it composes is `run`, `create`,
  `start` or `exec`, and an `absent` container is reported rather than treated as an ending;
* a settled activation is never visited.

### One correction the cases forced

My first version invented `"unknown"` for an observation it could not establish. Measured:
`_ReclaimAdapter.observe` never raises for an unreachable engine — it answers
`uncertain`, which is this module's existing word for exactly that, deliberately so ("everything
unrecognised answers `uncertain`, which the reclaim treats as a hold"). Reporting a second
word for one state would have described it two ways, so the report uses `uncertain` and the
fault branches do too.

### Measured

* `review_restart_tick_20260927.py`: **OK** (was 1 FAIL).
* `tests/job_manager/test_tool.py`: **48 PASS 0.381s** (43 existing, 5 added).
* `test_restart_recovery.py` **49 PASS**; Child A's `test_connected_lifecycle`,
  `test_expiry_reclaim`, `test_governed_endings`, `test_token_lifecycle` and Child B's
  `test_renewal_arbitration` **all PASS**; `test_intake`, `test_single_worker` **PASS**.
* `test_boundary_inventory`: **26 failures, name-set byte-identical** to the accepted
  baseline.

### Remaining

R2 (delayed launch and exact permission, including the restart-after-journal/bind-but-before-
admission cut, which `unresolved` does not currently select and which needs its own explicit
safe-resume-or-hold treatment), R3 (the REC-3 cut matrix), R4 (the integrated G1 audit).

## 2026-09-27 claim 285013 — R2: every unsettled-launch cut, and the evidence a restart may act on

Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     c59c5d92352c   the reader widened
    v12/python/tools/job_manager.py                       5adda0452a85   the report widened
    v12/python/tests/job_manager/test_tool.py             fc2e2289e75c   +2 cases (50 total)
    work/.../test_restart_recovery.py                     3c2425e10fa0   +9 cases (99 total)

### The cut the reader was missing, measured before it was widened

The review said the pre-admission cut needed its own explicit treatment. Measured it on the
connected path first: a manager killed after `journal_launch` and `bind_container` committed
but BEFORE the admission was asked leaves `launch` journalled, `container` = `runtime-1`
bound, `activating` False -- and `tokens.unresolved` answered **`[]`**. The engine had already
created that container and the resource was held, with nothing visiting it.

So the reader's rule is no longer "an admitted, unsettled activation" but **an unsettled
LAUNCH**: journalled launch, activation not settled, generation outstanding/unreturned/
unrevoked. Each entry now NAMES its cut, because they are not the same unknown:

* `launched-unbound` — launch journalled, no container identity ever bound: the engine may
  have created something whose identity this manager never learned, so there is nothing to
  observe by id and that is the report;
* `bound-not-admitted` — a container was bound and the activation never asked for: it may
  exist and be INERT, created and never started;
* `admitted-unsettled` — admitted and never resolved: it may be running right now.

The production report carries the cut through, so an operator is told which unknown it is.

### A premise of mine that measurement corrected

I wrote a case expecting `reconcile_runtime` to REFUSE a runtime whose id differs from the one
the token bound. It **attaches** it. **CORRECTION, per review 2026-09-27T11-52-29Z:** I then
called that "the accepted design because measurement found it", and that reasoning is wrong
and is withdrawn. Measuring current behaviour is not authority to substitute a container bound
to another token identity, and neither predecessor's acceptance covers a cross-identity
recovery path nobody reviewed. The case is kept as a recorded OBSERVATION, asserting the two
facts that hold either way -- the token's binding is not rewritten, and the resource stays
held -- and whether that attachment is correct is an open question for the worker proof, not
something the selector settles.

But the disagreement that remains is real and matters: the resource's stop/expiry path acts on
the BOUND container while the attempt's ending acts on the attached one. So the pass now
reports `contradicts_binding` and holds — the review's "contradictory observation is held,
never resolved by picking one", followed rather than paraphrased.

### Nine new connected cases

Every unsettled-launch cut is selected and named; the unbound cut has nothing to observe by
id; the admitted cut is still named as itself; a settled activation is still never selected;
**no cut releases the resource or permits a replacement** (all three, driven); a different
container under these labels is a contradiction to hold; a RENEWED deadline is what a restart
reads (Child B's arbitration from a fresh handle, revision 1 and the moved deadline); and an
expired unsettled launch is reported expired and **still held**, with revocation available in
the supported order — after which it is no longer a recovery candidate, because a revoked
generation's entitlement is withdrawn and the reclaim path owns it.

### Measured

* `test_restart_recovery.py`: **99 PASS 2.082s** (16 mine, the rest Child A's inherited).
* `tests/job_manager/test_tool.py`: **50 PASS 0.412s** (43 prior, 7 added across R1 and R2).
* Reviewer's `review_restart_tick_20260927.py` **OK**.
* Child A's `test_connected_lifecycle`, `test_expiry_reclaim`, `test_token_lifecycle`,
  `test_governed_endings` and Child B's `test_renewal_arbitration` **all PASS**;
  `test_intake`, `test_single_worker` **PASS**; `test_boundary_inventory` name-set
  **byte-identical** to the accepted baseline.

### What R2 still owes, stated rather than implied

The review asks R2 to demonstrate the **actual worker safe resume OR actionable held result**
for these persisted states -- not merely that `single_worker` has a reconcile branch. My
evidence so far is the actionable HELD result (the pass's report plus the holds above) and the
accepted `reconcile_runtime` attachment driven directly. Driving `single_worker.Worker.start`
over a store left at each cut is the remaining half; that is read-only use of an unpinned
module from my own selector, which is allowed, and it is the next thing I will do rather than
something I am claiming now.

R3 (the REC-3 matrix) and R4 (the integrated audit) remain untouched.

## 2026-09-27 claim 285064 — the attribution defect, and R2's worker half on the real path

Files changed, with digests:

    v12/python/tools/job_manager.py               9afc38ae5b8b   the attribution corrected
    v12/python/tests/job_manager/test_tool.py     ad226d6f6d3e   +2 cases (52 total)
    work/.../test_restart_recovery.py             96550cea6a38   wording corrected
    work/.../test_worker_resume.py                c01fc8798ec4   NEW, the worker proof

### P2 — a false actionable contradiction, reproduced then fixed

`review_report_attribution_20260927.py` reproduced first: **1 FAIL**. `_observing_unresolved`
compared the token's bound container against `row["runtime_id"]` — and a row is only how the
DOMAIN was discovered. Serial attempts over one retained resource share a domain, so a
historical attempt's old runtime was reported as the current token's contradiction: the report
named the right execution and the right binding while claiming a mismatch taken from somebody
else's row. A false actionable contradiction is worse than none.

Corrected two ways: the attachment is now read from the attempt the TOKEN names
(`held["execution"]`), and each domain is reported **once** — the discovery can reach the same
generation through several rows, and one unknown said several times is noise. An unreadable
owner is itself reported (`attachment: unreadable`) rather than silently skipped. Two cases:
a historical row attributes nothing, and a GENUINE owner mismatch is still reported — the
correlation must not silence a real disagreement.

### The "accepted design" framing is withdrawn

The review rejects my reasoning that measuring `reconcile_runtime`'s attachment of a
differently-identified container made it accepted design, and it is right: measurement shows
what the code does, not that cross-identity substitution is authorized, and neither
predecessor's acceptance covers that path. Withdrawn here and in the selector's docstring. The
case is kept as a recorded OBSERVATION asserting the two facts that hold either way — the
token's binding is not rewritten, and the resource stays held.

### R2's worker half, on the actual composed worker

`test_worker_resume.py` drives `single_worker.operations_from` over real stores with the worker
suite's own engine boundary and the job manager's own tick, kills the engine INSIDE the two-act
launch, and then resumes with fresh stores and the same engine memory. Four cases:

* the restarted worker **reconciles and never composes a second container**: one launch vector
  in total, zero activations, and the resource still held by its generation;
* the resume reaches an **actionable** state — the stage is `exceptional` and repeated ticks
  compose nothing further — rather than spinning;
* the production pass **reports that hold every tick**, naming the exact execution and cut;
* the hold **is not permanent**: past the deadline the accepted expiry path still owns the
  resource and revokes it in the supported order, which is also why the recovery visit never
  needed to release anything itself.

**One measurement corrected my assertion again.** I expected the interrupted launch to land on
`bound-not-admitted` or `admitted-unsettled`; the real worker lands on **`launched-unbound`**,
because the adapter binds the container id that `create` RETURNS and the engine died as it
answered. That is precisely the cut the reader was widened to select last claim, so the two
halves of this Work meet on the real path rather than in theory.

### Measured

* `test_worker_resume.py` **4 PASS 0.431s**; `test_restart_recovery.py` **99 PASS**;
  `tests/job_manager/test_tool.py` **52 PASS**.
* Both reviewer probes -- attribution and restart-tick -- **OK**.
* `tests.tools.test_single_worker` **PASS** (the suite whose fixture the worker proof borrows),
  `tests.manager.test_intake` **PASS**, Child A's `test_connected_lifecycle` **PASS**,
  `test_boundary_inventory` name-set **byte-identical** to the accepted baseline.

### Remaining

R3, the finite REC-3 cut matrix, reusing this Work's and both predecessors' exact evidence and
adding only the missing focused cuts; R4, the integrated G1 audit. No Child C, parent or G2
acceptance is claimed here.

## 2026-09-27 claim 285134 — R2's remaining cuts, the evidence precision, and R3's matrix

Files changed, with digests:

    v12/python/tools/job_manager.py     d272bd9242c2   one comment aligned
    work/.../test_worker_resume.py      edc8a5c7ae4c   7 cases, four cut points
    work/.../MATRIX.md                  f654ae98e815   NEW, the R3 matrix

### Four evidence-precision corrections, each exactly as the review named it

1. **The expiry case did not prove its title.** It was called "the hold is not permanent
   because expiry still reclaims it", accepted ANY nonempty refused list, never asserted
   revocation, cessation, return or discharge, and its engine answer named a made-up object.
   Measured the real outcome and renamed it to that: at expiry the reclaim REVOKES the
   entitlement, attempts the stop **against the runtime the attempt row names**, cannot
   confirm it, and the outcome is `held` / `uncertain` / `awaits-normalizing-ending` with the
   resource **still outstanding and not returned**. The assertions now name every one of those
   and the stop vector's exact target. Nothing was forced to release to make a nicer claim.
2. **PROGRESS's "non-permanent/reclaims" claim** is corrected by that rename, and the module
   prose claiming "ONE activation" and "a resolved generation" is corrected to what the cases
   assert: **ZERO** activations and a generation still held and unresolved.
3. **The reports-every-tick case never reopened stores.** Renamed to "on every pass" and
   labelled as repetition over the same handle, explicitly not counted as a restart cut.
4. **The `_observing_unresolved` comment** calling label attachment "the accepted exactness" is
   aligned with the withdrawal: observed behaviour, with both reviews cited, and the code takes
   no position on whether the attachment is right.

### R2's remaining cuts, on the same composed fixture

* `admitted-unsettled` — a new engine that answers `create` (so the bind and the admission
  commit) and faults on the ACTIVATION vector. Restart: no second container, resource still
  held, not returned, not revoked.
* `bound-not-admitted` — the one cut **no engine vector can produce**, because `Reservation.bind`
  journals the launch and binds the container and only then asks the admission. Reached by
  faulting `tokens.admit_activation` once, which is a fault injected at that exact real seam
  and is stated as such in the case. The case asserts the seam was reached, the cut is named,
  and the restart composes no second container.
* the **attached/bound mismatch**: after the interrupted launch the engine names a different
  container for the same labels. Whatever the resumed worker concludes about attachment -- and
  this Work still takes no position -- the asserted facts are that no second container is
  composed, the token's binding is **not rewritten**, the resource stays held, and the pass
  reports the disagreement rather than resolving it.

### R3 — the matrix

`MATRIX.md` enumerates thirteen proved rows, each naming the exact case that proves it, the
resume-or-hold result and the custody/no-repeated-effect fact; and then, separately, the rows
with **no restart proof in this Work**, each with its next bounded correction: dispatch and
unknown provider receipt, freeze, retention, verdict, handoff, cleanup, the discharge of a hold
whose cessation cannot be established (separable gap B), and clearing a timing-ambiguity hold
(separable gap C, inherited from Child B).

It states the counting rule the review requires and applies it: **only distinct cases of this
Work are counted** -- 16 in `test_restart_recovery.py`, 7 in `test_worker_resume.py`, 9 in
`tests/job_manager/test_tool.py` -- and inherited Child A executions are regression evidence,
not cut coverage.

### Measured

* `test_worker_resume.py` **7 PASS 0.862s** (four cut points); `test_restart_recovery.py`
  **99 PASS** (16 distinct mine); `tests/job_manager/test_tool.py` **52 PASS**.
* Both reviewer probes **OK**. `tests.tools.test_single_worker`, `tests.manager.test_intake`,
  Child A's `test_connected_lifecycle` **PASS**; `test_boundary_inventory` name-set
  **byte-identical** to the accepted baseline.

### Remaining

R4, the integrated G1 candidate/path/digest/evidence audit, plus the umbrella checkpoint
refresh at delivery. The matrix's "no restart proof" rows are the honest boundary of what this
child proves; two of them are the separable gaps already reported, and none of them hides a
defect -- each is a hold that keeps the resource excluded.

## 2026-09-27 claim 285184 — the mismatch premise repaired, and the matrix made exact

Files changed, with digests:

    work/.../test_worker_resume.py   463f9a0b7e71   8 cases; the mismatch scenario repaired
    work/.../MATRIX.md               3c5cf95bea24   rewritten with exact selectors

### The mismatch premise: the review was right twice, and the real behaviour is better

My previous case switched the engine double's `runtime_id` and asserted only one create, an
unchanged binding and `held=True`. It never established that the resumed worker REACHED the
conflicting evidence, and the reviewer's wrapper showed the recovery report naming the BOUND
runtime as absent with no contradiction at all. **MATRIX row 9's claim about that scenario was
false**, and it is withdrawn.

Measured what the composed worker actually does, and it is stronger than my framing suggested:

* the resume DOES ask the engine -- the `ps`/`inspect` vectors are now asserted as the premise
  rather than assumed;
* when the listing carries a runtime that is NOT the one this attempt recorded, the production
  identification **CANCELS rather than adopting it**: axis `cancel-requested`, recorded runtime
  unchanged, stage `exceptional`, no container composed, ZERO activations, binding intact,
  resource still held. That is the exact actionable pre-use refusal the review asked to see,
  and nothing was forced to attach.

**And it NARROWS my earlier observation rather than contradicting it.** The helper-level case
saw a labelled container adopted -- but there the attempt had NO recorded runtime, so there was
nothing for the engine's answer to contradict. With a recorded runtime, a different identity is
refused. Both facts are now in the matrix as separate rows (9 and 11) with that relationship
stated.

The same case now also asserts what the recovery pass reports for this scenario: deliberately
**no** contradiction, because the worker refused instead of adopting, so the attempt and the
token still agree. The contradiction report is a different scenario and is proved by the tool
case, which the matrix now names exactly.

### The reviewer's probe: it executes, and its remaining assertion is the premise I disproved

`review_mismatch_premise_20260927.py` wraps my case BY NAME, and the repair renamed it. I kept
the old name as an **alias** so the immutable artifact executes the repaired scenario rather
than erroring on a missing attribute. Its first assertion now passes (reports are captured).
Its second assertion -- that this scenario reports `contradicts_binding == another-runtime` --
fails, and that is the correct outcome: the premise is exactly what the repair disproves,
because the connected worker refuses the conflicting identity instead of adopting it. The
failing line is `self.assertTrue(any(r.get('contradicts_binding') == 'another-runtime' ...))`.

### The matrix, made exact

Rewritten per the review: exact `file::class::test` selectors instead of ellipsized names;
fifteen proved rows; and every unproved row CLASSIFIED against a named authority instead of
being called a harmless hold --

* dispatch and unknown provider receipt: **selected G1 obligation** (REC-3 plus the owner
  brief's "lost adapter replies" and "engine failure/recovery"), acts proved by Child A, no
  restart cut here, next step named;
* freeze, retention, verdict, handoff, cleanup: **not established as this child's obligation**
  on the owner brief's own selection, with their accepted acts named; if a restart obligation
  is intended it needs naming before being added;
* the two former "separable gaps B and C" are relabelled **limitations / open proposals with
  provenance**, explicitly NOT assigned Work and NOT release gates, recording that prior
  reviews expressly retained unknown-cessation holds and selected no hold-clearing API.

Counts are distinct-cases-only, as required: R 16, W 8, T 9.

### Measured

`test_worker_resume.py` **8 PASS**; `test_restart_recovery.py` **99 PASS** (16 distinct);
`tests/job_manager/test_tool.py` **52 PASS** (9 distinct); the attribution and restart-tick
probes **OK**; `tests.tools.test_single_worker` and `tests.manager.test_intake` **PASS**;
`test_boundary_inventory` name-set **byte-identical** to the accepted baseline.

### Remaining

R4, the integrated G1 candidate/path/digest/evidence audit and the umbrella checkpoint refresh
at delivery; and, if the reviewer or owner selects it, the dispatch-boundary restart cut named
in the matrix's first unproved row.

## 2026-09-27 claim 285232 — the dispatch boundary, and the two matrix corrections

Files changed, with digests:

    work/.../test_dispatch_cuts.py   63788ef16d0d   NEW, the authorised dispatch milestone
    work/.../MATRIX.md               88ba22cabe4b   two corrections plus the new rows

### The dispatch boundary, both cuts, on the composed worker

The durable intent here is `exchange.publish_command`: the command document is authored from
the attempt alone, so two managers compose identical bytes under an identical derived name, an
identical existing command is ADOPTED and a different one refuses. These two cases are what
that property is worth across a restart, driven through the real composed worker with fresh
stores on the resume.

* **Before dispatch** — the runtime is live and nothing durable was written. The resumed
  manager publishes **exactly one** command; one container, one activation, resource held.
* **After dispatch with the reply lost** — the command IS a durable file and this manager never
  learned it landed. **MEASURED, and stronger than what I first asserted:** I expected the
  resume to reach the publisher and adopt the identical command. It never reaches the publisher
  at all — the durable command plus the canonical state already say this stage is dispatched
  and waiting, so nothing is re-asked. **WORDING CORRECTED per review 2026-09-27T12-20-22Z:**
  I called zero further publications "the strongest form of no duplicated provider turn", and
  that overstated it -- it proves the command INTENT is not rewritten or re-published, and says
  nothing by itself about a consumer repeating one published intent. The consumer half is the
  next entry's proof. The case asserts zero publications, one container, one activation, the stage
  `waiting`, and the written command's digest **re-read from its own file** rather than from a
  second publication.

I also dropped a third case I had written: it asserted stage states that these two already
establish, and its stacked fixture patches made it measure the wrong engine. Two exact cases
rather than three with one unreliable.

### The two matrix corrections, exactly as named

* `W`'s shorthand now names its class, and the count says **7 distinct cases, 8 executions** --
  the eighth is the old-name alias of the repaired mismatch method, kept so an immutable
  artifact still runs it, and counted as an execution rather than a case.
* Row 15's class is corrected to `ReconcilingFromThatSetAttachesWithoutASecondCrossing`.
* The dispatch row moved out of "no restart proof here" and into rows **16 and 17**, with a
  note saying the review authorised it; the remaining unproved rows keep their classification
  and their named authority, and the two limitations keep their provenance.

### Measured

`test_dispatch_cuts.py` **2 PASS**; `test_worker_resume.py` **8 executions / 7 distinct
PASS**; `test_restart_recovery.py` **99 PASS (16 distinct)**; `tests/job_manager/test_tool.py`
**52 PASS (9 distinct)**; the attribution and restart-tick probes **OK**;
`tests.tools.test_single_worker` **PASS**; `test_boundary_inventory` name-set
**byte-identical** to the accepted baseline.

### Remaining

R4 only: the integrated G1 candidate/path/digest/evidence audit across Child A, Child B and
this child, plus the umbrella checkpoint refresh at delivery. The matrix's remaining unproved
rows are classified rather than claimed, and the two limitations remain recorded proposals
rather than gates.

## 2026-09-27 claim 285284 — the provider effect and its receipt, cut and restarted

Files changed, with digests:

    work/.../test_provider_effect_cut.py   49d59ce72616   NEW, the last selected R3 proof
    work/.../MATRIX.md                     69bed28115bf   rows 18-19, scope note, new open row

### The proof the review said remained

A deterministic executor now CONSUMES the published command the way the in-container worker
does -- reading the command file at its fixed name, deriving the digest from the same bytes the
manager digested, and asserting they agree -- performs ONE counted effect, and writes the
worker-side RECEIPT document into the exchange's event root. Then the manager is interrupted
having never observed that receipt, the stores are reopened, and the actual resume is driven.

* **The effect happens once and the receipt survives** -- **CORRECTED, see the next entry.**
  As first written this case called the consumer by hand on both sides of the restart and then
  asserted TWO effects, which proves the fixture can repeat a command and says nothing about
  whether the production resume asks again. Review 2026-09-27T12-28-08Z rejected that claim and
  it is withdrawn; the replacement wires the recorder to the production invitation.
* **A receipt with no terminal is an actionable unknown**: the observation answers `working`,
  which is the module's own word for "the provider may still be running" and deliberately not
  rounded to lost. No false success -- the stage is not integrating/accepted/complete -- and
  the resource stays held.

Four measurements corrected this file while I built it, each recorded at the code: the launch
document cannot be re-authored by a fixture (two attempts were correctly refused as "not the
one this manager would have written"), so the exchange is adopted through `exchange.adopt`, the
reader the launch path itself calls; `observation` deliberately does not surface the session to
a manager-side reader, so the executor reads it from the command file as a worker does; the
receipt view exposes `accepted_at` alone, and the digest is therefore asserted through the
observation's own acceptance of the receipt (`_event` compares the digests); and `incomplete`
is not a member of the view -- `state: working` is the vocabulary.

### The overstated wording, corrected

My previous entry called zero further publications "the strongest form of no duplicated
provider turn". That overstated it, exactly as the review said: it proves the command INTENT is
not rewritten or re-published and says nothing by itself about a consumer repeating one
published intent. Corrected in PROGRESS, and MATRIX row 17 now carries that scope note
explicitly, with the consumer half as rows 18 and 19.

### One new open row, named rather than implied

A worker TERMINAL written while the manager was gone is the other half of row 19, and this Work
does not prove it. It is recorded in the matrix as a **selected G1 obligation not proved here**,
with the one further cut that would prove it, rather than being folded into row 19.

### Measured

`test_provider_effect_cut.py` **2 PASS**; `test_dispatch_cuts.py` **2 PASS**;
`test_worker_resume.py` **8 executions / 7 distinct PASS**; `test_restart_recovery.py`
**99 PASS (16 distinct)**; `tests/job_manager/test_tool.py` **52 PASS (9 distinct)**; both
reviewer probes **OK**; `tests.tools.test_single_worker` **PASS**; `test_boundary_inventory`
name-set **byte-identical** to the accepted baseline.

### Remaining

R4: the integrated G1 candidate/path/digest/evidence audit across all three children and the
umbrella checkpoint refresh at delivery -- plus the one new open row above if the reviewer
selects it.

## 2026-09-27 claim 285346 — the effect count is the product's now, not the fixture's

Files changed, with digests:

    work/.../test_provider_effect_cut.py   fb67e9627343   3 cases, recorder rewired
    work/.../MATRIX.md                     f17f07f5e52b   rows 18, 18b, 19 corrected

### The rejected claim, and why the rejection was right

My "one effect" case called the consumer by hand before the restart, created a second consumer
after it, called that by hand too, and then asserted the total was TWO. That demonstrates the
FIXTURE can repeat a command; it says nothing about whether the production resume asks again.
The once-only claim is **withdrawn** from PROGRESS and from the matrix.

### The replacement, wired where the review said

The effect recorder is attached to `exchange.publish_command` -- the manager's own invitation --
and it **stays attached across the interruption and the reopen**. Every invitation that actually
WRITES a command invites the consumer exactly once; an adoption invites nobody, because no new
turn was asked for. So the count is produced by production invitations, and if the resumed
manager asked again the recorder would fire again.

* **Acceptance**: `test_ONE_effect_in_total_and_the_resume_never_invites_another` -- one
  invitation, one publication, one effect, one activation, after eight resumed ticks with the
  recorder attached throughout; the receipt is still readable by the production observation,
  which is what makes asking again unnecessary rather than merely skipped.
* **Negative control**, explicitly not acceptance:
  `test_the_recorder_DOES_catch_a_duplicate_control_case` -- a deliberate second consume reaches
  two, so the acceptance result of one is a measurement rather than a silence. The review asked
  for exactly this distinction.
* **Unknown outcome**, tightened: renamed from the stale `INCOMPLETE` spelling to
  `..._is_WORKING_held_and_asks_nothing_further`, asserting the exact observation state
  `working`, the exact stage state **`running`** (measured -- the honest projection for a
  receipted turn whose outcome nobody has established), and that nothing further was asked:
  one effect, one invitation, one publication, one activation, all counted by instruments
  attached throughout.

### The proposed extra gate is dropped, as instructed

The terminal-while-the-manager-was-gone row is no longer listed as a selected obligation. The
review is explicit that it must not become another acceptance gate and that row 19's unknown
hold suffices; the matrix now records it as **not selected**, with that reference, so the
boundary stays visible without becoming work.

### Measured

`test_provider_effect_cut.py` **3 PASS**; `test_dispatch_cuts.py` **2 PASS**;
`test_worker_resume.py` **8 executions / 7 distinct PASS**; `test_restart_recovery.py`
**99 PASS (16 distinct)**; `tests/job_manager/test_tool.py` **52 PASS (9 distinct)**; both
reviewer probes **OK**; `tests.tools.test_single_worker` **PASS**; `test_boundary_inventory`
name-set **byte-identical** to the accepted baseline.

### Remaining

R4 alone: the integrated G1 candidate/path/digest/evidence audit across Child A, Child B and
this child, plus the umbrella checkpoint refresh at delivery.
