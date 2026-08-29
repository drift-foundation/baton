# Implementer progress — local OCI lifecycle composition

Created 2026-08-24 by `baton.claude` on claiming W6636, as the record requires.

## The nine dependency edges are installed

The handoff asked the route handler to add them before implementation. All nine
are in, each with its rationale recorded on the edge:

**W5 components** — W6631, W6632, W6633, W6634.
**Manager contracts** — W6592, W6627, W6628, W6629, W6630.

## Not implemented, because the brief's own precondition is unmet

The assignment opens with it: *"After all component and manager prerequisites
close satisfying, compose the approved sequential consent/execution OCI
topology."*

Measured on the current tree rather than assumed — **none of the nine has
closed, and none has a satisfying outcome**:

| Work | status | phase |
|---|---|---|
| W6631 materialize sources | open | queued |
| W6632 adapter core | open | queued |
| W6633 worker image | open | active |
| W6634 sealed output/credentials | open | **block** |
| W6592 manager composition | open | queued |
| W6627 agent-session/runtime | open | queued |
| W6628 output receiver | open | queued |
| W6629 intake/retention/cleanup | open | queued |
| W6630 section 13 security | open | queued |

Four of these I implemented myself in this session and returned for review;
they are in review precisely because nobody has yet confirmed they are right.
Composing on top of them now would build an integration on nine unreviewed
foundations, and the integration's own tests would then encode whatever those
components got wrong — which is the failure that makes an integration review
worthless rather than merely early.

W6634 is a stronger case still: it is itself **blocked**, on contracts that do
not exist. There is nothing there to compose.

## What this Job would need that does not exist yet

Its deliverables name them directly: consent teardown and exact activation need
W6627's agent-session and runtime protocols; **effectively-once**
start/inspect/cancel/**freeze/collect**/destroy needs W6628's output receiver
and W6634's collector; positive absence needs W6632's adapter, which is written
but unreviewed; and the destroy/retain path needs W6629 and W6630.

The mutable Docker restart/race/failure evidence the brief asks for is the one
part I could run today — Docker 29.1.3 is reachable on this host. Running it
against components that may change would produce evidence about a system that
will not exist by the time this Job is reviewed, which is worse than no
evidence because it looks like coverage.

## Recommendation, not a decision

Let the nine settle. This Job is an integration and it is correctly last.

If the intent was for me to begin a *scaffold* — the composition's shape, with
its component seams named and left unimplemented — that is a coherent thing to
ask for and a different Job from the one written here; I would want it stated
before building it, because a scaffold that ages against nine moving components
is the same waste in a smaller package.

## State

**Edges installed, no implementation.** Parked in `block` behind its nine
prerequisites, which is where an integration Job with nothing to integrate
belongs.

## 2026-08-27 — first implementer round: the certified arc, composed and measured

Evidence: `evidence/w6636-2026-08-27-composition.txt`.
Harness: `evidence/w6636-mutation-harness.py`.
Code: `v12/python/tests/manager/test_lifecycle_composition.py` (new, 24 cases).
No Git history or index was mutated; the mutation harness restored every file
it rewrote and the evidence shows the check.

The progress above was written 2026-08-24 and describes nine unclosed
dependencies. All ten are now closed, so it is superseded rather than amended.

### PLAN 1 — the revalidation, and the thing that governs the rest

**W6634 closed NON-SATISFYING**: *"Seven implementation and review cycles
produced no independently accepted deliverable. Closing the overbroad Work; its
code remains provisional and cannot be treated as certified."* No successor Work
exists for its sealed-output/credential half, and W6636 is W5's last open child.

W6636's acceptance requires *"All component and manager dependencies are closed
satisfying before terminal integration signoff."* **That clause cannot be met as
things stand**, and waiving it is not mine to do.

Mapping the provisional reach by CALL rather than by file is what set this
round's scope, and it is wider than the two obvious entries. `seal` and
`collect` land in `sealing.py` and credential delivery lands in
`credentials.py` — but `authorize_cleanup` destroys nothing without an intake
receipt, `request_intake` takes custody only of a `frozen` result, and only
`request_freeze` freezes one. **So for a runtime that ever started, destroy and
positive absence are reachable only through the provisional path.** PLAN item 3
names freeze, collect, destroy and positive absence together; all four sit
behind W6634. A consent runtime is torn down directly by the adapter and never
passes through intake, so consent teardown *is* composed.

With `outputs=()` and `credential_delivery=None` — which the adapter's own
docstring names as the runtime half's supported construction — `start`, `list`,
`stop`, `destroy` and `observe` enter neither provisional module. That is the
ground this composition stands on.

### Two [P0] findings composition produced and no component could

**The adapter starts no worker that can run.** `run_vector` composes
restrictions, labels, mounts, credential mounts and the image — and no `--env`.
The reference worker reads `BATON_WORKER_POSTURE`, `_SESSION`, `_CONTRACT` and
`_ROLE` from the environment and, finding none, exits at once without a frame.
Measured through the adapter's own vector against a real daemon: **exit 2, empty
stdout, empty stderr.** Every execution container the reviewed adapter starts
from the reviewed image is dead a fraction of a second later.

Neither component's suite could see it and both are right about themselves:
W6632's engine suite runs the pinned *base* image, which requires no
environment; W6633's container suite composes its own `docker run` with `--env`
for every variable and never calls the adapter. The defect exists only in the
join, which is this Job's subject and nobody else's.

**The manager records `running` for a worker that is gone.** `list_vector` is
`ps --all`, and `_attach` observes `running` for anything the label filter
returns — so an *exited* container satisfies reconciliation exactly as a live
one does. Composed with the finding above, every execution attempt records
`execution_runtime = running` for a worker that died before the call returned.
The adapter has the operation that would settle it — `observe` answers
`running`, `quiescent`, `absent` or `uncertain` about one exact identity, and a
case here proves it tells the three apart — and **no manager operation calls
it**. Naming the shape of the fix is this Job's business; making it is not.

**[P2]** The store carries a `consent_runtime` axis and the adapter a `consent`
posture, and nothing joins them. The composition drives the adapter directly and
records the axis alongside; a later slice should replace that with one
operation.

### An operational finding against my own closed Work

The full-tree gate is at **seven** failures. Six are `test_boundary_inventory`'s
accepted baseline, unchanged. The seventh is not:

```
FAIL: test_every_entry_has_exactly_one_stated_owner
      (tests.manager.test_contracts_inventory)
  receiving entries with no owner:
    ('check_input_pair', 'assignment_manifest')
    ('check_input_pair', 'input_manifest')
    ('check_input_pair', 'what')
```

`check_input_pair` is the public function I added to `contracts/manifest.py` in
**W19784, which closed satisfying**. Its three receiving parameters were never
registered in the contracts inventory's `OWNERS` table. Neither my gate nor the
reviewer's caught it, because that inventory is part of the ~14-minute full-tree
run and the round was verified on the manager subset.

**I have not fixed it.** It is a closed Work's deliverable, the remedy is three
entries in `tests/manager/test_contracts_inventory.py`, and editing another
Work's accepted deliverable without review is what passing work back exists to
prevent. It needs an owner.

### PLAN 2, 3, 4 — what is composed

Twenty-four cases over a real daemon, running this repository's own worker image
built from W6633's recipe. Docker is required and **fails rather than skips**;
Podman is absent on this host and its cases skip narrowly, which is the
environment evidence the acceptance asks for rather than a change in vocabulary.

Composed: consent teardown with proved absence and consent proved absent
*before* the execution container is created, read off one trace; decline;
activation gating the first writable call; the ordered arc through offer,
accept, record, claim, activate, compose, start and reconcile, with the engine
asked what the container actually mounts; idempotent reconciliation;
effectively-once start; stale generation; the authorized-root refusals at both
manager boundaries and at the adapter's own seam; fence-then-stop off one
ordering trace; a second incarnation adopting the running runtime; a real
stranger container forcing the multiplicity cancellation; a runtime removed
underneath the manager answering `uncertain` on both of reconciliation's
branches; a start the daemon refuses; and the reachability fact that stops this
arc at destroy.

Not composed, and each is W6634's: the success ending, freeze, collect, destroy,
positive absence, cleanup recovery.

### The measurement, and what it corrected

Every rule this module claims to compose was **removed from the source and the
module re-run**; the harness is kept beside the evidence so the measurement is
repeatable rather than asserted. **The first pass found six unestablished of
twelve**, and five were one mistake — two guards refusing the same obvious case,
so removing either left the other refusing and the case still passed.

- `_plan_agrees` and `authorize_input_root` both refuse a stranger's root.
  Separated into three cases: one whose *plan* is wrong while the authorization
  agrees (asserting nothing was journalled, since that is the earlier check's
  whole value), one whose *root* is wrong while the plan agrees, and one
  reaching the adapter's own seam directly.
- The consent adapter was built with `mounts=()`, making *"a consent container
  mounts nothing"* true by construction; `MOUNTABLE` was never reached. It now
  gets a workspace-only plan — not the full plan, which refuses one step earlier
  on the unauthorized `/input` bind, and accepting *that* refusal would have
  been the same mistake twice.
- Activation could not be separated by wording at all: `authorize_input_root`
  refuses an unactivated attempt with the same category, code and opening words,
  and `issue_offer` requires an input digest so the second guard always runs.
  What the first buys is that the adapter's plan is never read, so the case now
  observes the attribute access.
- `observe` was read everywhere absence happened to be the honest answer, so an
  adapter answering `absent` to everything satisfied every case — measured, and
  it did. That is the one answer that releases an assignment whose worker may be
  running, so a live container is now put in front of it.
- Reconciliation's two uncertainty branches are different questions and only one
  is reached per call. Both now are.

**All eighteen mutations are caught.** I will state the pattern rather than
resolve it: for the fifth Work running I wrote the case that confirms the
behaviour instead of the case that could distinguish it, and removing the guard
and looking is the only thing that has ever caught it.

## State

The certified arc is composed, measured and clean. **This is not terminal
integration signoff and must not be read as one.** W6634 closed non-satisfying,
the acceptance clause on satisfying dependencies is unmet, and freeze, collect,
destroy and positive absence are unreachable without provisional code. Two [P0]
findings say the composed execution path cannot presently run a worker at all
and that the manager does not notice.

Passed back for independent review rather than closed, with four things owned by
someone other than this round: whether composition may proceed across a
non-satisfying dependency, who owns the missing `--env`, who owns the missing
`adapter.observe` call, and who owns the `check_input_pair` inventory
registration left behind by W19784.

## 2026-08-28 — resumed; the two shared-crossing [P0]s

Claimed W6636 at seq 31075. Evidence:
`evidence/w6636-settlement-crossing-probe.py`. Docker 29.1.3 reachable and
used. No Git history or index was mutated.

### Revalidating the pinned [P0]s, and one of them was understated

The dossier pins that `intake._settle` "never evaluates the two provider
endings", so cleanup could record `complete` while a launch root survived.
That is one layer below what the tree actually did. `_destroyed` owned the
adapter's answer with `required=("runtime_id", "state", "why")` and no
`optional`, and `boundaries._members` REFUSES an unrecognised member rather
than ignoring it — so the real `OciAdapter.destroy` answer, which always
carries `credentials` and `launch`, was refused outright. `authorize_cleanup`
could not complete against the real adapter at all.

Measured rather than reasoned: the same document through the same owner
refuses with "a destroy observation also carries credentials, launch, which
this build's contract for it does not name". Both readings needed the same
correction, so this is a correction to the RECORD rather than to the plan.

### A defect my own regression created the conditions to find

Writing the retry the required correction implies — "uncertainty/failure
preserved as cleanup-required" — showed that cleanup-required was permanently
stuck. `_settle` returned `cleanup_unsettled` from INSIDE the journalled
transaction, so the destroy operation committed with "it did not settle" as
its result; and a retry of that cleanup is the same receipt under the same
policy, which is an exact retry, so it replayed the non-ending forever.

The module's own sentence — "the offer to try again is the axis staying where
it is" — was true of the axis and false of the operation, and it had been
false for the pre-existing `uncertain` branch all along. Nothing that fails to
settle is journalled now, which puts a non-ending in exactly the state this
module already documents as safe: the one a crash between the engine call and
the journal leaves.

### The refused start

`request_runtime_start` journalled `start-requested` and then let the
adapter's refusal propagate, leaving the attempt claimed, activated and
stranded with no runtime identity — and `authorize_cleanup` refuses exactly
that shape, so nothing could clean it up either. It now reconciles through the
operation that owns the answer, attaches a runtime the failed start created
(which is what makes it nameable by the destroy crossing), records `uncertain`
when nothing can be established, and starts no replacement.

**The first version retyped every settled failure as `refused/start-failed`,
and the boundary inventory caught it** — three probes stopped reaching their
named boundary, because a malformed start ANSWER is `integrity/schema` at
`_started` and relabelling it made the manager's account disagree with the
boundary that found it. The closed pair crosses unchanged now and only the
message grows. The typed ending a caller acts on is the durable one.

### Measured, not read

- `evidence/w6636-settlement-crossing-probe.py` drives a REAL `OciAdapter`
  against a real daemon and passes the answer through the manager's own
  contract. Against the pre-fix tree it prints the refusal; against the
  corrected tree both endings are owned, an unresolved root is reported as
  waiting, and the launch root is confirmed gone from disk. The probe reads
  the contract FROM the manager rather than restating it — the first version
  spelled the members out and so proved only that it could spell them.
- against the pre-fix source, the four new intake cases and the six new
  attempts cases fail; the two "must still settle" cases pass either way by
  design and are named rather than counted.

### Gates

- `tests.manager.test_intake` 70, `tests.manager.test_attempts` 126 — green
- full v12 parallel source — **1612 tests, 6 failures**, every one in
  `test_boundary_inventory` and none of them this Work's. Verified by CONTENT
  rather than by count: the unowned-entry list and the intake sites in the
  boundary-call list are identical before and after this round.
- serial registry — **105 tests, 0 failed, 6 skipped**

## State

The two production [P0] crossings are corrected and measured. **This is not
integration signoff and must not be read as one.** Passed back for independent
review rather than closed.

### Explicitly not done, and why

The real-engine module replacement is untouched. The three consent-runtime
cases and `test_destroy_is_unreachable_without_the_provisional_path` still
pass and still assert the superseded two-container boundary; the full arc
through the production output and credential providers, the negative/race and
orphan matrices, the security inspection and Podman are all still ahead. I
left the stale cases in place rather than half-migrating them: deleting them
without the replacement arc removes coverage and buys nothing, and the
replacement arc is the substantial remainder of this Work rather than a tidy-up
after it.

### For review

- **`_start_failed` cannot force-remove anything, and the plan asks for it.**
  Removal goes through `adapter.destroy`, whose command requires the intake
  receipt and retention policy digests — neither exists at start time. So a
  refused start ATTACHES the runtime it finds, which is what makes the
  ordinary destroy crossing able to name it, and removal happens there. If the
  intent is that a failed start removes its own container immediately, that
  needs an adapter operation that does not exist and is a contract change
  rather than a composition one.
- **An attempt that reaches `uncertain` from a refused start cannot be cleaned
  up.** `authorize_cleanup` refuses `uncertain` by the frozen asymmetry, and
  reconciliation cannot leave `uncertain` without an identity to ask about.
  That is fail-closed and correct as far as it goes, and it is also a real
  hole in the recovery matrix this Work owns; it belongs to the orphan-
  convergence work that is still ahead rather than to this round.

## 2026-08-28 — the re-reviewed [P0]s, corrected

Claimed W6636 at seq 31418; passed back at seq 31469. Evidence:
`evidence/w6636-corrected-p0-retry.py`. The reviewer's
`evidence/w6636-review-p0-retry.py` is kept byte-for-byte. Docker 29.1.3
reachable and used. No Git history or index was mutated.

**Recording note.** This entry was written immediately AFTER the pass rather
than before it: the append and the pass were issued together, a failed `cd`
short-circuited the append, and the pass ran anyway. Nothing about the round
changed in between and the pass comment carries the same account; this is the
record catching up with it, said here rather than left to look like the
ordinary order.

### Reproduced first, and both findings are exact

The reviewer's file runs and prints both:

    provider retry adapter calls: 0
    provider retry cleanup: complete
    failed-reconciliation runtime axis: start-requested

### The first one is my own correction defeating itself one call later

`_destroyed` short-circuited on `execution_runtime == "destroyed"` and
answered a synthetic `absent` without calling the adapter. The destroy I made
retryable last round moves that axis truthfully on its first pass — so the
retry that existed to finish the provider teardown skipped the adapter, and
because the endings are optional an answer carrying none of them recorded
`complete`.

Both halves landed in the same round, which is the part worth pinning: the
retry path and the bypass that made it vacuous are in the same file, and
neither the review nor my own measurement caught the interaction because my
retry case supplied a second positive answer and never asserted that anything
was ASKED. The call count is now the assertion, across three rounds.

The correction is to stop short-circuiting. The runtime axis is a fact about
the container and says nothing about the roots it mounted, and asking about an
identity the engine no longer has is safe. The outstanding ending survives by
being RE-ASKED rather than remembered, which is what makes it survive a
process restart without a schema change.

### The second is an invariant that only held on the happy path

`_start_failed` caught a failed reconciliation to extend the exception message
and nothing else, so an unavailable listing left the attempt exactly where the
settlement was written to stop it being left. `_settle_unknown_start` records
`uncertain` before the refusal is raised, from `start-requested` ONLY — a
reconciliation that recorded something truer before it failed is not
overwritten, because closing one hole must not open the opposite one. An
adapter that faults rather than refuses takes the same path and its fault is
re-raised unchanged.

### Measured, not read

- against the PRE-FIX source, **5 of the 6 new cases fail**. The sixth is
  `test_a_settlement_never_overwrites_a_truer_observation`, which guards the
  opposite defect and passes either way BY DESIGN; it is named rather than
  counted.
- `evidence/w6636-corrected-p0-retry.py` walks the adapter call count across
  three cleanup rounds and all three refused-start endings, and exits 0.

### The reviewer's verification boundary, addressed as far as I can

The review reports the Docker probe exiting before the crossing because the
managed nested process could not reach the daemon, while a standalone
`docker info` could. The probe now prints the engine's own argv, status and
stderr when it cannot connect, and says in as many words that a standalone
`docker info` working while this does not makes the boundary the invocation's
rather than the host's. It still FAILS rather than skips. I cannot remove a
managed-shell restriction from inside a managed shell, so this makes the
condition legible rather than fixing it.

### Gates

- `tests.manager.test_intake` 72, `tests.manager.test_attempts` 130 — green
- full v12 parallel source — **1618 tests, 6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **105 tests, 0 failed, 6 skipped**

## State

The re-reviewed [P0]s are corrected and measured. **Still not integration
signoff.** Passed back for independent review rather than closed.

### For review

- **"Survives a process restart" means re-asked, not remembered.** There is no
  durable manager note of which provider was unresolved; the adapter is called
  on every retry and reports its own current endings. An adapter that reports
  a provider once and OMITS it later would therefore read as "no such
  provider". `OciAdapter` always answers both, so nothing in this tree does
  that — but it is a real gap in the CONTRACT rather than in the
  implementation, and closing it needs either a durable record or a rule that
  a provider may not disappear from an answer.
- **The remainder is unchanged.** The one-container real-engine module
  replacement, the negative/race and orphan matrices, the security inspection
  and Podman are all still ahead, exactly as the first resumed round reported.

## 2026-08-28 — the third-round [P0]s, corrected

Claimed W6636 at seq 31755. Evidence:
`evidence/w6636-corrected-omission-and-fault.py`. The reviewer's two files are
kept byte-for-byte. No Git history or index was mutated.

### Reproduced first

Both reviewer files run and print the unsafe durable rows: `cleanup after
restart: complete` with the provider member omitted, and `durable runtime id:
None` / `exact observations: 0` after a fault that created a runtime.

### The contract is closed rather than the manager given a memory

The review offered two resolutions. Preserving applicability durably means
inventing manager state for a fact the provider already owns; closing the
contract says it once and needs nothing stored. Every provider answers on
every destroy, `not-delivered` is the explicit no-provider ending, and an
omission is a schema refusal. `OciAdapter` always answering both was a habit
of one implementation, and `authorize_cleanup` is a generic public boundary.

### One boundary for both kinds of failed start

The fault path called `_settle_unknown_start` directly, which asks the adapter
nothing — so a driver that created a runtime and then raised left it unnamed.
`_settle_failed_start` reconciles first for both, falls back to `uncertain`
only when reconciliation cannot answer, and re-raises the fault unchanged. A
case now drives a refusal and a fault against the same adapter shape and
requires the same durable row, because splitting them is how the reconciliation
was lost in the first place.

### The mistake inside the fix, found by running the reviewer's file

Closing the contract broke every existing case that named a bare destroy
answer, so my first move was to give the shared `Custodian` a `not-delivered`
default for both endings. That made the reviewer's omission reproduction pass
while measuring something else entirely: the omission never reached the
manager. A double that quietly completes what a case named is a double that
hides contract violations — the same class of defect as the one being
corrected, a missing thing read as a benign one.

The double now returns exactly what a case names. Six cases that constructed
bare answers, two inline adapter classes and the boundary-inventory destroy
probes all name both endings now; every one of those is a FIXTURE change, and
no assertion was weakened.

### Measured, not read

- against the PRE-FIX source, **4 of the 5 new cases fail**. The fifth is
  `test_a_fault_the_reconciliation_cannot_answer_is_still_uncertain`, which
  guards the retained fallback and passes either way BY DESIGN; it is named
  rather than counted.
- `evidence/w6636-corrected-omission-and-fault.py` exits 0, and the real-engine
  probe still exercises the crossing against a real daemon.

### Gates

- `tests.manager.test_intake` 74, `tests.manager.test_attempts` 133 — green
- full v12 parallel source — **1623 tests, 6 failures**, every one in
  `test_boundary_inventory` and none this Work's. The three destroy probes
  that briefly joined them were probes rendered vacuous by the closed
  contract, and they are fixed rather than accepted.
- serial registry — **105 tests, 0 failed, 6 skipped**

## State

Corrected and measured. **Still not integration signoff.** Passed back for
independent review rather than closed.

### For review

- **An adapter that answers `not-delivered` after `unresolved` is still
  believed.** The closed contract stops an OMISSION erasing a teardown; it
  cannot stop an adapter contradicting itself, because the manager holds no
  prior ending to compare against. The review's required regression is
  "unresolved first, omitted second must refuse or remain pending, and only an
  explicit terminal ending may settle", which this satisfies exactly — but the
  self-contradiction case is left open deliberately rather than silently.
- **The remainder is unchanged.** The one-container real-engine module
  replacement, the negative/race and orphan matrices, the security inspection
  and Podman are all still ahead.

## 2026-08-28 — the reviewed [P2], corrected

Claimed W6636 at seq 31901. No Git history or index was mutated.

### The leak, and everywhere it was

`test_both_kinds_of_failed_start_take_one_settlement_boundary` constructed a
fresh `TestCase`, called `setUp()`, and called `case.tearDown()` in `finally`.
The fixture owns its temporary directory and its `ControlStore` through
`addCleanup`, and NO class in these suites defines `tearDown` at all — so that
call ran the base no-op and released neither. The focused run emitted implicit
`TemporaryDirectory` and unclosed-SQLite `ResourceWarning`s at process exit.

**It was not only the named case.** The same `setUp()`/`tearDown()` shape is
what I wrote in four of my own evidence files — `w6636-corrected-p0-retry.py`,
`w6636-corrected-omission-and-fault.py`, `w26294-corrected-replay.py` and
`w26294-corrected-reproductions.py`, fourteen call sites in total. All of them
now call `doCleanups()`. Fixing only the case the review named would have left
the durable evidence leaking for the same reason.

The reviewer's own `w26294-review-*.py` files use the same shape and are kept
byte-for-byte as produced; they are theirs, and both now fail at their own
assertions by design. Named here rather than edited.

### Measured

- `tests.manager.test_intake` and `tests.manager.test_attempts` under
  `-W error::ResourceWarning` — **207 tests, OK, warning-clean**
- all four corrected evidence files under `-W error::ResourceWarning` — exit 0
- full v12 parallel source — **1623 tests, 6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **105 tests, 0 failed, 6 skipped**

## State

The reviewed [P2] is corrected. **Still not integration signoff.** Passed back
for independent review rather than closed; the one-container real-engine
replacement, the negative/race and orphan matrices, the security inspection and
Podman remain exactly as reported.

## 2026-08-28 — the one-container arc, composed

Claimed W6636 at seq 31948. The reviewed [P2] was accepted; this round is the
integration remainder's first real slice. No Git history or index was mutated.

### What now runs against a real daemon

`test_the_whole_one_container_arc_reaches_a_clean_settlement` walks offer →
accept → atomic claim → activation → input and private-root composition → one
execution start → quiescence → freeze → intake → retention → force-removal →
exact absence → provider teardown → clean settlement, through the production
providers. It asserts the credential and launch documents land as separate
read-only mounts, that the engine really ran (a real `run` argv carrying the
resolved image DIGEST), that the container is gone from the daemon rather than
from a row, and that both delivered roots are gone from disk.

The fixture gained `declarations` (taken FROM the retained input manifest
rather than written out, because §12 rule 15 holds the envelope against the
declarations and a suite that composed its own list would be testing whether
it can copy what it just read), `produced`, `published` and `credential`.

### Two more missing seams, and they are the round-one shape again

- **`OciAdapter` had no `retain` method at all**, so `decide_retention`
  refused and the destroy crossing was unreachable.
- **`OciAdapter.destroy` refused the manager's own `operation` member**, which
  its own docstring says rides beside the body.

Both are seams BETWEEN two accepted components, each of which is right about
its own half — exactly the class the first round found as the missing `--env`
and the missing `observe` call. Neither is visible to either side's suite; only
composing the arc shows them.

### A wrong assertion of mine, and what it proved

The arc completes in under a second on a warm daemon, which reads like a suite
that mocked the engine. I added an assertion that the built IMAGE TAG appears
in the run argv and it failed — printing the whole real `docker run`: the
security flags, the eight labels, and four mounts including the credential at
`/run/baton/credentials/registry` and the launch document at
`/run/baton/launch.json`. The adapter runs by resolved DIGEST rather than by
tag, which is the correct behaviour and what my assertion had wrong. The
corrected assertion is kept, because the next reader will have the same doubt.

### Gates

- `tests.manager.test_lifecycle_composition` — 27 tests, 1 skipped (Podman
  absent, narrowly), green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **106 tests, 0 failed, 6 skipped**

## State

The keystone arc is composed and green. **Still not integration signoff.**
Passed back for independent review rather than closed.

### For review

- **`OciAdapter.retain` acts on nothing, deliberately.** The disposition's
  effect on the custody tree is unspecified by every accepted finding this
  Work can read, and nothing else in the tree removes custody material either.
  That needs a ruling or a bounded Work; this seam should not invent it.
- **Still ahead, unchanged:** replacing the three superseded consent cases and
  the `destroy-is-unreachable` expectation, the negative/race and orphan
  matrices, the security inspection, and the Podman contract. The arc landing
  is what makes those writable; they are not written yet.

## 2026-08-28 — the retention no-op, corrected

Claimed W6636 at seq 32040. Evidence:
`evidence/w6636-corrected-retention.py`. The reviewer's file is kept
byte-for-byte. No Git history or index was mutated.

### I deferred a defect, and the review was right to refuse that

I wrote that what a local adapter should do to the custody tree per
disposition was "stated by no accepted finding this Work can read" and named
it a reported gap. The review answered it exactly: the manager's own
settlement rule already says `complete` means nothing was kept, so the arc I
landed was reporting a false clean ending — not raising an open question. That
is the difference between a boundary I should not cross and a defect I did not
want to fix, and I had them the wrong way round.

### The correction

`discard-after-intake` removes only the named custody trees and PROVES their
absence before returning; `retain` and `quarantine` leave the bytes. The tree
is DERIVED from the `attempt:name` identity rather than taken, so a path, a
cross-attempt identity and an undeclared output are three refusals rather than
three resolutions. The retry is idempotent because the manager delivers this
before its own journal.

### Measured

- eight focused cases in `tests/manager/test_sealing.py`, including the
  vacuous-removal case: `discard_tree` is patched to answer True and change
  nothing, and the refusal has to come from the filesystem rather than from
  the call returning.
- the real arc now asserts the custody trees EXIST before the decision and are
  gone after it, so the absence is a removal rather than a tree that never was.
- `evidence/w6636-corrected-retention.py` exits 0 under
  `-W error::ResourceWarning`; the reviewer's file now refuses, because it
  discards an artifact its adapter never declared — one of the three
  identities the review required be refused.

### Gates

- `tests.manager.test_sealing` — 53 tests, green
- `tests.manager.test_lifecycle_composition` — 27 tests, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **106 tests, 0 failed, 6 skipped**

## State

Corrected and measured. **Still not integration signoff.** Passed back for
independent review rather than closed; the superseded consent cases, the
negative/race and orphan matrices, the security inspection and Podman remain.

## 2026-08-28 — the two fail-open endings, corrected

Claimed W6636 at seq 32107. Evidence:
`evidence/w6636-corrected-retention.py`, extended with both. The reviewer's
file is kept byte-for-byte. No Git history or index was mutated.

### Both reproduced, both the same shape as the last one

    unknown disposition answer: {'delivered': True, 'discarded': ['proposal']}
    unknown disposition destroyed custody: True
    retain over absent custody answer: {'delivered': True, 'discarded': []}
    retained custody exists: False

The disposition is now validated against exactly the frozen three before the
artifact names are resolved, and a keep requires every named tree to be
positively present before it returns.

### A vacuous case of my own, caught by the split

`test_a_keep_over_absent_custody_refuses` looped over both keep dispositions
in one fixture. The first pass removes the custody tree — and
`collected_result` SKIPS a name whose tree is absent, so the second pass
collected nothing, checked an empty artifact list, and passed vacuously. It
was the loop, not the guard, that was being measured on the second half.

Measured: with the loop in place the second disposition reported
`{'delivered': True, 'discarded': []}` over absent custody and the case still
went green. It is two named cases now, one fixture each, and the corrected
evidence uses a fresh tree per disposition for the same reason.

### Measured

- `tests.manager.test_sealing` — **58 tests**, green under
  `-W error::ResourceWarning`
- `evidence/w6636-corrected-retention.py` — exits 0 under the same policy, and
  prints the refusal for each unknown disposition and each keep over absent
  custody
- the reviewer's `w6636-review-retention-fail-closed.py` now refuses where it
  asserted the fall-through
- `tests.manager.test_lifecycle_composition` — 27 tests, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **106 tests, 0 failed, 6 skipped**

## State

Corrected and measured. **Still not integration signoff.** Passed back for
independent review rather than closed; the superseded consent cases, the
negative/race and orphan matrices, the security inspection and Podman remain.

## 2026-08-28 — the superseded cases, replaced

Claimed W6636 at seq 32161. The retention P0/P1 were accepted with no new
finding. No Git history or index was mutated.

### Replaced rather than deleted, and that is why they waited

The three consent cases and `test_destroy_is_unreachable_without_the
_provisional_path` all asserted a boundary the supersession removed. I left
them standing for three rounds and said so each time, because deleting them
before the arc existed would have removed coverage and bought nothing. The arc
landed, so the replacements are writable and they are written.

Each replacement keeps what was TRUE in the case it replaces rather than
matching it one for one — the ordering claim, the `not-delivered` versus
`absent` distinction, and the no-receipt rule are all still held. The four new
cases are named in `FINDING.md` against the four they replace.

`test_a_lost_claim_launches_nothing` is new rather than a replacement: the
supersession names the lost claim explicitly and nothing covered it.

### Gates

- `tests.manager.test_lifecycle_composition` — **28 tests**, 1 narrow Podman
  skip, green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **107 tests, 0 failed, 6 skipped**

## State

**Still not integration signoff.** Passed back for independent review.

### Still ahead, and now the whole of what is left

- the rest of the negative/race matrix: offer expiry, a post-create failure
  that cannot duplicate, `plan-rejected` and unsupported-version taking the
  same cleanup crossing, deadline;
- restart adoption of an exact ended runtime before reuse, and per-attempt
  orphan recovery that cannot delete a sibling attempt's roots;
- the security inspection — exact read-only `/input`, the one writable
  workspace, absence of the authority store and unrelated host paths, and the
  runtime boundary's inability to create host or sibling-container processes;
- Podman as the additive contract, which currently skips narrowly because the
  daemon is absent on this host.

## 2026-08-28 — the lost-claim case, corrected

Claimed W6636 at seq 32219. The other four replacements were accepted. No Git
history or index was mutated.

### The case tested the fixture rather than the rule

`claim_answer = None` is a malformed document, and the boundary refuses it as
`integrity/schema` before any authority answer is involved. So the case proved
that an unusable injected document does not itself call the engine — which
another suite already covers — and its no-engine assertion could not fail,
because `submit_claim` never launches anything on any path.

It now injects the capability's TYPED REFUSAL, settles the offer to
`claim-refused` through the existing path, and then attempts activation and
start. Each refusal's REASON is pinned rather than only its type: "has no
committed claim" and "is not activated". A case that passed for some unrelated
precondition would say so.

Verified by printing all five outcomes before pinning them, because the defect
being corrected is precisely a case that passed for the wrong reason:

    1 claim   -> refused precondition | already claimed by another participant
    2 offer   -> claim-refused
    3 activate-> refused precondition | has no committed claim
    4 start   -> refused precondition | is not activated
    5 runs    -> []

### Gates

- `tests.manager.test_lifecycle_composition` — 28 tests, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **107 tests, 0 failed, 6 skipped**

## State

**Still not integration signoff.** Passed back. The remainder is unchanged
from the previous round: the rest of the negative/race matrix, restart/orphan,
the security inspection, and Podman.

## 2026-08-28 — the security inspection and the orphan bound

Claimed W6636 at seq 32267. The lost-claim P1 was accepted. No Git history or
index was mutated.

### Asked of the engine, and printed before it was pinned

Four cases: the exact four-mount set with each source proved, the named
absences, the applied runtime boundary, and the orphan bound.

I printed the real applied configuration before asserting it, for the reason
the lost-claim correction taught — a case that passes for the wrong reason
looks exactly like one that passes:

    mount targets : ['/input', '/run/baton/launch.json', '/workspace']
    network       : none | privileged: False
    capdrop       : ['ALL'] | capadd: None
    securityopt   : ['no-new-privileges', 'label=disable'] | pids: 512
    readonly root : True | user: 65532:65532

Every one of those is the ENGINE's answer about a live container rather than
the argv this suite watched the manager compose.

### Gates

- `tests.manager.test_lifecycle_composition` — **32 tests**, 1 narrow Podman
  skip, green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **111 tests, 0 failed, 6 skipped**

## State

**Still not integration signoff.** Passed back for independent review.

### What is left, and it is now short

- the rest of the negative/race matrix: offer expiry, a post-create failure
  that cannot duplicate, and `plan-rejected` / unsupported-version / deadline
  taking the same cleanup crossing the completed arc takes;
- restart adoption of an exact ENDED runtime before lane reuse — adoption of a
  RUNNING one, mismatch and multiplicity are already covered;
- Podman, which skips narrowly because no daemon is present on this host. That
  is an environment fact rather than a coverage decision, and it is the one
  item here I cannot close by writing anything.

## 2026-08-28 — the two [P1]s, corrected

Claimed W6636 at seq 32326. No Git history or index was mutated.

Both findings are the same class as the lost-claim one, and the second is the
same mistake twice: a case that names the production seam in its docstring and
does not call it.

- `PidMode` is pinned to the engine's private-namespace answer (`""` on
  Docker, `private` on Podman) rather than merely not `host`, and `PidsLimit`
  is asserted exactly at 512.
- the orphan case drives `OciAdapter.recover_credentials`. My first correction
  still failed, and the reason is worth recording: I built the two deliveries
  in a `CredentialHome` of my own and then called the adapter, whose recovery
  acts on ITS OWN home — so the recovery ran over an empty directory and the
  sibling assertion passed for no reason at all. Both deliveries are now
  materialized in `adapter._credential_home()`.

**Measured, because the finding was that the case measured nothing:** with
`OciAdapter.recover_credentials` replaced by a no-op the case FAILS. The
reviewer's `w6636-review-security-shape.py` now fails on the sibling
namespace; their `w6636-review-orphan-seam.py` can no longer run the case at
all, because disabling the seam leaves the Docker class fixture unbuilt —
a weaker signal than the no-op patch above, which is why that one was run.

### Gates

- `tests.manager.test_lifecycle_composition` — 32 tests, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **111 tests, 0 failed, 6 skipped**

## State

**Still not integration signoff.** Passed back. The remainder is unchanged:
the rest of the negative/race matrix, ended-runtime restart adoption, and
Podman.
