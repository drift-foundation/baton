# Progress

## 2026-09-04 — baton.claude (impl), W81857 claim

Implemented PLAN items 3–6 and the source half of item 7 against the
file-exchange boundary Slawomir ruled on 2026-09-03 and the reviewer
revalidated on 2026-09-04. The pipe-owned proposal in FINDING.md stays
superseded and nothing below reinstates it.

### Revalidation before implementing

Every pinned claim was re-checked against the current tree first:

- `tools.single_worker._SingleWorker._prepared` still ended at
  `request_runtime_start`/`reconcile_runtime` and never called
  `worker_manager.worker_entry.converse`. Confirmed.
- `job_manager.projection._observed_state` still mapped an attached runtime
  identity straight onto the stage-specific running word. Confirmed, and that
  line is what this Work replaces.
- `launch.materialize` created a `0555` attempt-private root holding exactly
  `launch.json`, and `launch.adopt` refused any widened root. Confirmed; both
  are extended rather than relaxed.
- The reviewer's focused baseline is real: 434 cases across
  `tests.manager.test_launch`, `test_oci`, `test_worker_entry`,
  `test_worker_image`, `tests.job_manager.test_launch`, `test_restart`,
  `test_status` and `tests.tools.test_single_worker` passed on the tree as
  found.

### What was built

`v12/worker/baton_worker.py`
: Launch `baton.worker-launch/2` with the fifth member `transport`; the
  schema decides the member set, so no document is valid under both versions.
  `serve` selects the transport from the VALIDATED document only — a latched
  or `/1` container still uses the framing loop whatever its filesystem looks
  like. `serve_exchange` waits for the one command, publishes its receipt
  BEFORE dispatching the provider, publishes one state event per operation
  reached and one terminal document, and reuses `handle`, the input and
  assignment validation, the output measurement and `publish_completion`
  unchanged. A worker that re-enters and finds its own receipt publishes
  nothing and exits non-zero: it cannot know whether the earlier provider is
  still running, and `lost` would be an observation it does not have.

`worker_manager/exchange.py` (new)
: The typed `ExchangeDelivery`, the two fixed container targets, the closed
  command/receipt/state/terminal documents, derived sequence and operation
  identities, atomic publication (exclusive no-follow staging, whole write,
  `fsync`, in-directory rename, directory `fsync`), the untrusted reader, and
  a descriptor-relative no-follow teardown for the dynamic entries the worker
  writes.

`worker_manager/launch.py`, `worker_manager/oci.py`
: The exchange namespaces are created inside the same attempt-private launch
  root before the start and the root is closed `0555` last, so the worker can
  write inside `events/` and cannot move either namespace. `adopt` proves the
  shape, the modes and the configured group; `discard` delegates the dynamic
  walk. `run_vector` composes exactly two more binds at this contract's
  constant targets, refuses either direction reversed, and refuses any
  assignment, credential or launch mount that would contain them.

`job_manager/delegation.py`, `manager.py`, `projection.py`, `documents.py`
: `observe` gains a seventh member, `exchange`, from an injected deployment
  read; `dispatch` and `conclude` are two further optional capabilities. A
  `_converse` pass runs after `_launch` and reacquires canonical state first,
  so one tick can launch a container and command it. No Job-store receipt is
  written for either act. Status moves to `baton.v12.job-status/3` and gains
  `starting`, `waiting` and `answering`; a runtime identity alone no longer
  earns an active word, and an absent exchange read is reported as `null`
  rather than guessed either way.

`tools/single_worker.py`, `DEPLOYMENT.md`
: Configuration schema `/3` adds `review_route`, `retention_policy_digest`
  and `retention_disposition`. The production launch selects the exchange;
  every pass reconstructs the delivery from durable state. The ending runs the
  fixed ruled order — quiesce, disposition, freeze, intake, retention, the
  exact-generation Authority pass to the review Route, then cleanup — and the
  pass capability is added to the deployment's own session wrapper rather than
  widening `AuthorityPort`.

### Verification

- `tests/manager/test_exchange.py` (new, 56 cases): the launch version and its
  closed member set, the mode and ownership of each namespace, adoption's
  shape/mode/group/byte proofs, the authored command and its derived filename,
  two managers publishing one sequence, a conflicting command refusing, atomic
  publication leaving no staging name, the observation's `not-requested` /
  `waiting` / `working` / `answered` / `faulted` / `unreadable` vocabulary,
  malformed, foreign, oversized, linked, reordered, uncorrelated and
  extra-member worker documents, a §13 live bearer refused out of the command,
  the teardown of dynamic worker entries without following a link, both ends
  agreeing on every mirrored constant, the receipt preceding provider
  dispatch, three worker runs over one receipt producing exactly one provider
  invocation, an agent failure carrying a code and no diagnostic, a
  wrong-session command refused before dispatch, a writable command namespace
  refused, the worker waiting for a command published after it started, and a
  `/1` launch leaving the exchange untouched.
- `tests/job_manager/test_exchange.py` (new, 23 cases): a started container
  nobody commanded is `starting`, the active word is earned by the receipt,
  each kind's own word, `answering` rather than `completed`, faulted/lost/
  unreadable contained as `exceptional`, an unknown exchange state never read
  as the calmest one, the command and the launch in one tick, no second
  command after a restart, a restart after the answer resuming only the ending,
  one stage's refusal leaving another observable, and a read-only status that
  commands nothing.
- Existing suites updated within this Work's scheduled scope: the observation
  member set, the status schema version, and the `running` assertions that
  encoded the defect. `tests/job_manager/fixtures.py` gained opt-in runtime
  attachment on a successful launch and an exchange surface; the default
  behaviour of every pre-existing case is unchanged.
- The reviewer's 434-case focused baseline still passes, plus the 79 new
  cases.

### Not done, and why

- **The real-container gate is not run.** It requires a freshly built image
  candidate whose digest is recorded and selected and a fresh attempt binding
  it. The retained W71917 container carries the old worker bytes, has no
  exchange mounts, and must not be injected into — it stays the defect
  reproduction and the separately permitted manual stopgap.
- **No abandonment, retry, pool, checkpoint or log policy** was added.
  Fault, loss and incompleteness are reported and contained.

### Pre-existing failures observed on the tree, unrelated to this change

All three were observed before this change; the first two reproduce on a
pristine export of the current checkpoint, and the third is host state:

- `tests.manager.test_boundary_inventory` fails five cases, with 323 receiving
  entries that have no declared owner. This change adds 29 entries of exactly
  the shape `launch.py`'s existing unowned entries have; it does not repair
  the backlog, which needs its own record.
- `tests.authority.test_catalog` does not list `test_work_label_exposure.py`,
  and `tools/parallel_test.py` does not register
  `tests.tools.test_quiescent_assignment_finalization`. Both are stale
  registries from earlier Work.
- `tests.manager.test_credentials_engine.ARealDaemonNeverHoldsTheBearer.
  test_nothing_this_module_made_survives_it` fails on HOST STATE: 29
  `baton-runtime.start-*` containers predate this session, the oldest from
  2026-08-30, and the one still running is
  `c4c12927cd8857d1860ac157baf7aee9bb69bb03adc01613fdd4bfbddc08e75b` — the
  retained W71917 reproduction this record names. Nothing was removed: that
  container is deliberately retained evidence and the other 28 are not this
  Work's to dispose of.

Awaiting independent review.

## 2026-09-04 — baton.claude — response to review-2026-09-04T03-32-19Z

Changes requested before byte review, and the finding is correct: the handoff
asked for a digest-bound review and supplied no proposal. A shared, mutable
checkout carrying three different Works' edits is not a candidate, and a
reviewer that bound it would be binding bytes that can move under it.

No implementation byte was changed in response. What was missing was the
packaging, and it now exists.

### The immutable proposal

    /home/sl/baton-proposals/baton/W81857/2026-09-04T07-30-00Z/

That directory and everything under it are mode `0555`/`0444` and are outside
this checkout, so nothing in the working tree can move them. It holds:

- `manifest.json` — the declared base, the exact sorted candidate path set,
  a per-path record of status, mode, byte count, candidate digest and base
  digest, the record path set beside it, and the recomputation instructions;
- `proposal.patch` — the whole reproduction diff against the declared base,
  restricted to exactly the candidate path set;
- `candidate/` — the exact candidate bytes at their repository-relative paths;
  and
- `DIGESTS` — the proposal digest and the patch digest, in one line each.

The proposal digest is the SHA-256 of `manifest.json`'s canonical bytes with
its own `proposal_digest` member removed; `manifest.json` states the exact
recomputation in terms a reader can run without this note.

### Separation from the unrelated dossier edits

The checkout also carries modifications under
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-source-workspace-mounts/`.
They are **not** in this candidate and never were: they were already present in
the working tree when this Work was claimed, they are a different record's
evidence, and no act of this implementation touched either file. The manifest
names them explicitly as excluded so the exclusion is a stated fact rather than
an omission a reader has to notice.

### The proposal was reproduced from its own declared base

Packaging that nobody has replayed is a claim. The published `proposal.patch`
was applied to a clean export of the declared base at
`65851899efed44b9926658cdbd3ba5bb485288da`, in `/tmp/w81857-repro`, which is
left in place for the operator rather than removed. Every candidate and record
path came out byte-identical to its manifest digest, and the focused suite —
`tests.manager.{test_launch,test_oci,test_worker_entry,test_worker_image,test_exchange}`,
`tests.job_manager.{test_launch,test_restart,test_status,test_exchange}` and
`tests.tools.test_single_worker` — ran 513 cases green in that reproduction,
with no dependency on this shared checkout.

The manifest's own recomputation prose was replayed the same way: the proposal
digest was recomputed by following the text rather than by re-running the
packager, so a manifest whose instructions did not describe what was actually
done would have failed there. Every dirty path in the checkout is either a
candidate path, a record path, or a named exclusion; nothing is unaccounted
for.

### The real-container gate is still open

Nothing in this packaging runs it or claims it ran. The acceptance bullet
requiring a manager-owned real-container observation remains unmet and is
recorded as such in `PLAN.md` item 7.


## 2026-09-04 — baton.claude — response to review-2026-09-04T03-43-45Z

Five P1 findings, all five reproduced on the reviewed digest, all five
corrected in the same candidate line. The reviewer's four reproductions are
left where they were named — `/tmp/repro-w81857-ending-window.py`,
`/tmp/repro-w81857-stale-staging.py`, `/tmp/repro-w81857-event-secret.py`,
`/tmp/repro-w81857-dead-worker-status.py` — and every one of them now shows the
corrected behaviour.

### What changed, and where

**The ending is owed until its last step settles.** `projection` gained
`_ending_owed`, which reads the manager's own cleanup axis: an answered
exchange projects `answering` and keeps owing `conclude` until that axis is
`complete`, `retained` or `failed`, whatever committed before it. A frozen
output no longer outranks an owed ending. `single_worker.ending` was already
composed of replayable owners; the docstring now states that property at each
boundary instead of leaving it implied.

**Publication converges.** `exchange._publish_once` stages under a unique name
and takes the final name with `link`, which fails closed instead of clobbering;
`baton_worker._publish` stages under a unique name and keeps `replace`, because
a state event is legitimately published twice. A crash-stranded staging file no
longer wedges either end, and a genuine race produces one command.

**No worker value crosses without its own shape.** Every scalar member of a
worker-written document now has a closed vocabulary or a canonical grammar,
the ending decides which members apply, and §13's durable-secret walk runs over
the whole projection. One refused document makes the exchange `unreadable`
rather than projecting the members that happened to parse.

**The active word needs a receipt and a running runtime.** `_conversing`
crosses the two axes. A receipted turn whose runtime is not running is
`exceptional` — reported, contained, authorizing no replay. `answering` is
exempt, because the ending quiesces the runtime deliberately.

**The terminal's digest is enforced, against the right document.** See the
supersession appended to `FINDING.md`: the comparison is against the sealed
result's `completion_manifest_digest`, which is this manager's own
independently recomputed digest of `/output/output.json`, not the frozen
result's `manifest_digest`. The first correction compared the wrong pair and
the real-composition regression caught it before this handoff.

### Regressions, and that they fail on the reviewed digest

`tests/manager/test_exchange.py` grows to 79 cases and
`tests/job_manager/test_exchange.py` to 39; `tests/tools/test_single_worker.py`
gains a class that drives the **real** ending. The whole tree runs 3667 cases
against 3552 at the declared base, with the same eight pre-existing failures
and no others. The unsafe
`test_a_frozen_output_ends_the_asking` is replaced by five crash-boundary cases
covering each unsettled cleanup state, a restart mid-ending, and the settled
states that finally end the asking.

`TheAnsweredEndingRunsThroughTheRealOwners` runs the real `baton_worker` over
the real exchange this deployment composed and then drives
`_SingleWorker.ending` through the Worker Manager's own quiescence,
disposition, freeze, intake, retention, exact-generation Authority pass and
cleanup, with only the engine boundary faked. It carries the matching control,
the mismatch control (which stops before intake and leaves the stage
`answering`), and the missing/malformed controls that never reach the ending
because the exchange refuses them first.

The new and changed cases were replayed against the **reviewed** candidate at
`/tmp/w81857-repro` with only the test files substituted: 49 failures and 5
errors, covering every one of the five findings. A regression that passes on
the digest it was written for is not a regression, so this is checked rather
than asserted.

### One defect this pass introduced and corrected before handoff

`exchange.py` first named a private helper `_one_of`, and `oci.py` already had
one. `test_boundary_inventory` resolves private helper returns by BARE FUNCTION
NAME across the whole package, first module in sorted order winning -- so the
new helper silently retargeted `oci.py:OciAdapter.observe`'s `document.Running`
entry to this module's parameter name, and a declared owner for a module this
Work never touched went stale. The helper is renamed `_vocabulary` and the
reason is written at the site, because the next person adding a module here
will not expect a private name to be package-global to a test.

The whole discovered entry universe is now compared against the pristine
checkpoint: nothing is removed or retargeted, and every added entry is a
parameter this Work genuinely introduces in `exchange.py`, `launch.py` or
`oci.py`.

### Still open

The real-container gate. Unchanged by this pass and unclaimed.


## 2026-09-04 — baton.claude — response to review-2026-09-04T04-17-15Z

Three findings, all three reproduced on the reviewed digest, all three
corrected in the same candidate line. The five prior corrections are preserved
and their regressions still pass. The reviewer's seven reproductions are left
where they were named and all seven now show the safe outcome.

### What changed, and where

**The schema member is compared.** `exchange._event` now takes the pinned
schema for the kind it is reading and holds the document to it by equality,
before the correlation. A receipt, a state event or a terminal that says it is
another protocol -- or one of this exchange's OWN other kinds -- refuses.

**A terminal requires the sequence that produced it.** `exchange._caused`
requires the receipt, and derives the expected state evidence from the
terminal's own claim: each answered operation carries an `answered` state, a
faulted ending carries a `faulted` state for the operation it stopped on, and
an operation the terminal does not claim may not be sitting there answered.
A `lost` ending is held to its answered prefix and no further, because nobody
observed what became of the operation it stopped on.

This changed the worker's publication ORDER. `_published_manifest_digest` is
now read before `work`'s `answered` state is published rather than after the
loop: publishing `answered` and then faulting over a missing envelope would
emit the exact contradiction the manager now refuses. `serve_exchange` also
binds `manifest` before the loop and reports a sequence that never reached
`work` as a fault, so no path can reach the terminal with it unbound.

**One cleanup boundary per publication.** `exchange._publish_once` and
`baton_worker._publish` now put creation, write, mode, file sync, link or
replace, directory sync and close under one boundary, so an ordinary transient
failure at any step leaves no staging residue. Durability and the no-clobber
`link` are unchanged.

### Regressions, and that they fail on the reviewed digest

`tests/manager/test_exchange.py` grows to 96 cases with two new classes --
`EveryWorkerDocumentIsHeldToItsOwnKind` and
`ATerminalNeedsTheSequenceThatProducedIt` -- plus injected write- and
sync-failure staging cases at both ends. The existing positive controls now
build the whole correlated chain through a `chain()` helper, because a fixture
that wrote a terminal alone was writing something no worker produces, which is
precisely the forgery the correction refuses.

Replayed against the reviewed candidate at `/tmp/w81857-reviewed` with only the
test files substituted: **13 failures**, four on the schema discriminator, seven
on the causal chain and two on staging residue. Whole tree 3684 against 3552 at
the declared base, with the same eight pre-existing failures and no others.

The discovered boundary-inventory entry universe is diffed against the pristine
checkpoint again after this pass: nothing removed or retargeted.

### Still open

The real-container gate, and the operational integration blocker: this review
binds a proposal digest, and restoring the shared checkout's target set to the
declared base or absence is the authorized operator's act, not the
implementer's.


## 2026-09-04 — baton.claude — response to review-2026-09-04T04-31-34Z

One P1, reproduced and corrected; the accepted schema, publication-boundary and
worker-ordering corrections are preserved unchanged.

### The causal validator now checks a history, not its parts

`exchange._caused` required the answered prefix and then rejected only a
remaining `answered` state, which left every other impossible tail acceptable.
The ending now decides the WHOLE state map and the map is compared member for
member: an `answered` terminal has the full answered vector and nothing else; a
`faulted` terminal has its answered prefix, the next operation `faulted`, and no
state after it; a `lost` terminal has its answered prefix, at most the next
operation `dispatched`, no fault anywhere, and is not a completed sequence.

`lost` keeps one optional slot because that is its honest shape: a process that
died between publishing `dispatched` and receiving an answer leaves exactly
that event, and one that died before publishing it leaves none. A rule strict
enough to refuse the four reproduced contradictions has to accept both of those
or it refuses the states this transport exists to survive.

`FINDING.md` marks the superseded clause in place and states the exact-vector
rule in a new dated section, so the weak rule and its replacement do not sit
live beside each other.

### The accounting claim is now true

The preceding manifest said injected write- and sync-failure staging cases
existed "at both ends" while the worker half injected `fsync` only. The
implementation was already correct, so what was wrong was the accounting: the
worker case now injects both, with a partial write first so the staging file
exists and is non-empty when the failure lands.

### Regressions, and that they fail on the reviewed digest

`tests/manager/test_exchange.py` reaches 100 cases. `no_impossible_state_tail`
carries all four reproduced contradictions plus two the prior rule already
caught; `every_legitimate_crash_boundary_is_a_readable_loss` and its fault
sibling are the positive controls at each real boundary, which is the half a
stricter rule can break.

Replayed against the reviewed candidate at `/tmp/w81857-reviewed` with only the
test file substituted: **4 failures**, exactly the four contradictions the
review reproduced. The other two tail cases and the worker write-failure
control pass there, because the prior rule already covered them — a control is
not a regression and is not reported as one.

Whole tree 3688 against 3552 at the declared base, same eight pre-existing
failures. The boundary-inventory entry universe still removes and retargets
nothing.

### Still open

The real-container gate, and the operational integration blocker.


## 2026-09-04 — baton.claude — the real-container gate, and the verification note

`review-2026-09-04T04-41-52Z.md` signed off the source and left two things
owed: the real-container gate, and a verification note that had been carried
forward from an earlier pass and no longer described what it claimed.

### The gate ran

A fresh immutable reference image was built from this candidate's worker:

    sha256:db9f397171153338ce068b46a7c9ab48c79b80d9f1ad1db4c149541a5eb8199b

`evidence/gate-real-container.py` composes a complete production deployment
around that digest -- Authority, Work, staged source, frozen task, input
manifest, credential registry, schema `/3` configuration -- submits one Job,
and then runs every manager tick as `job_manager serve --once` in its OWN
process. Between two ticks there is no manager of this deployment anywhere on
the host. The evidence document is
`evidence/gate-real-container-2026-09-04.json`.

What it establishes:

- the production composition started a real container from the fresh digest
  and published one command into its mounted exchange;
- the commanding tick's process was reaped at a recorded instant, and the
  worker's receipt -- which it publishes BEFORE dispatching its provider --
  landed after it, with no manager of this deployment alive at any point in
  the gap;
- exactly one command file and exactly one receipt exist, with no staging
  residue in either namespace;
- the container published `output.json` and a correlated terminal naming that
  envelope's digest, and then PID 1 exited 0 of its own accord rather than
  idling, which is the defect this Work opened on;
- a fresh incarnation picked all of that up by rescanning alone and drove the
  whole ending, ending at `completed` with the runtime absent and the exchange
  removed by cleanup; and
- three further incarnations changed nothing.

**The claim that does not depend on a clock.** The measured margin between the
commanding tick's exit and the receipt is small -- 13 ms -- because the
reference provider answers instantly, and a margin that size is thin evidence
on its own. What settles it structurally is the engine's own record: the
runtime's `ExecIDs` is `null`. `worker_entry.converse` would have run
`docker exec`; the production composition opened no channel into that container
at any point in its life. That is the supersession's actual requirement, and it
is a fact about the engine rather than about timing.

**What the gate does not prove, stated so nobody reads it as more.** The
reference image's provider is `ScriptedAgent`. This gate proves the transport,
the restart boundary, the exactly-once fence and the durable result -- not that
a commercial provider was reached. The dogfood image injects a real provider at
the same documented `main(agent=...)` seam and needs a credential this gate
deliberately does not require; running it there is a separately authorized
operator act. `PLAN.md` says the same thing.

### The verification note is now about this pass

The preceding manifest's `verification.note` described the pass-2 replay
against the `04-05-00Z` candidate. It is replaced by this pass's own numbers
and names the locator and digest it was actually replayed against.

### Two things observed while running the gate

- `job_manager status` is given no deployment factory, so it holds no exchange
  read and answers `exchange: null`. For a stage whose output is frozen and
  whose ending is still owed, that reader therefore says `completed` where a
  serving manager says `answering`. It is not wrong about anything it can see
  and the null says so, but an operator reading only that surface cannot tell
  the two apart. Reported rather than changed: the reviewed source is signed
  off and a CLI widening is not this Work's.
- The separately retained W71917 deployment still has a live serving manager on
  this host against its own stores. The gate's liveness claim is scoped to its
  own Job store for exactly that reason, and the evidence records the other
  process rather than hiding it.

### The declared base moved while this package was being assembled

`f684bd1 docs(v12): define worker base-image selection policy` landed on top of
`6585189`, which every preceding proposal in this line declared as its base. It
touches two files of the separately owned `finding-v12-isolated-agent-workers`
dossier and nothing this proposal names, so no candidate or record byte is
affected — but a declared base is a fact about the repository, not about the
candidate, so this package declares `f684bd1` and recomputes every base digest
against it.

The packager's own coverage check is what caught it: it requires every dirty
path in the checkout to be a candidate, a record path or a named exclusion, and
those two files were suddenly neither. A reviewer who verified an earlier
package against the old base is told here rather than left to find out.

### Still open

Independent review of this package, and then the authorized operator's
restoration of the target path set for `baton.merge`'s preflight.


## 2026-09-04 — baton.claude — response to review-2026-09-04T07-00-54Z

Three P1s, all three reproduced, all three corrected. One of them is a defect I
had found myself, written into this file, and set aside as somebody else's
scope. That judgement was wrong and the review is right: it is inside this
Work's accepted status boundary and it is the read-only form of the very defect
this Work exists to remove.

### The status correction

`projection._ending_owed` asked for an exchange whose state was `answered`, and
the read-only `job_manager status` surface has no exchange reader at all. So
one durable state gave two answers — `answering` from a serving manager and
`completed` from the read-only surface — and the reassuring one belonged to the
reader that could see less.

The rule now reads canonical Worker Manager state alone: the cleanup axis is
asked first, so a settled ending is settled for every reader; otherwise the
ending is owed if either the exchange says `answered` or this manager holds a
frozen output, because nothing but the ending freezes one. `exchange: null`
stays the availability fact and no longer decides whether a stage is finished.

`fixtures.frozen()` now defaults `cleanup="complete"`, which is what every case
written before the ending existed meant by "this stage is frozen". Cases about
the window name an unsettled value explicitly. An unsettled default would have
made every pre-existing terminal expectation mean something its author never
wrote.

Four new cases: an unsettled cleanup is not `completed` — asserted both with
and without an exchange reader — a settled cleanup still projects the frozen
disposition, no exchange read before any answer is still `starting`, and an
unfinished ending opens no dependent gate. Replayed against the source-approved
candidate: four failures, exactly those.

### The gate correction

`evidence/gate-real-container.py` computed every acceptance member and exited
zero whatever they said. It now fails closed on all sixteen, and its verdict is
both a member of the evidence and the exit code, so the JSON and `$?` cannot
disagree. Each predicate was driven against a spoiled copy of the passing run to
prove it can actually fail.

It also bound nothing to the reviewed source. It now requires the proposal's own
candidate digest for `v12/worker/baton_worker.py` and measures the worker file
inside the selected image by copying it out — `create` plus `cp` runs nothing
from the artefact — and refuses before composing anything on a mismatch, which
was checked by passing a wrong digest and getting exit 1. The rebuilt image is
byte-identical to the one already selected, and the measured worker digest is
`sha256:da34aa2c…`, this candidate's own.

The gate was rerun after the status correction, because that correction changes
the manager source the gate exercises. It passed with an empty
`unmet_acceptance`.

### The packaging correction

The immutable manifest carried a note saying the gate "was NOT run" beside a
member saying it was, because the note was moved between packages by string
edits and one edit silently failed to match. The note is now COMPOSED from the
measured members every time. That is the cause rather than the symptom: prose
transcribed between packages is prose nothing checks.

### Verification

Focused suite 574; whole tree 3692 with the same eight pre-existing failures.
The boundary-inventory entry universe still removes and retargets nothing.

### The declared base moved while this package was being assembled

`f684bd1 docs(v12): define worker base-image selection policy` landed on top of
`6585189`, which every preceding proposal in this line declared as its base. It
touches two files of the separately owned `finding-v12-isolated-agent-workers`
dossier and nothing this proposal names, so no candidate or record byte is
affected — but a declared base is a fact about the repository, not about the
candidate, so this package declares `f684bd1` and recomputes every base digest
against it.

The packager's own coverage check is what caught it: it requires every dirty
path in the checkout to be a candidate, a record path or a named exclusion, and
those two files were suddenly neither. A reviewer who verified an earlier
package against the old base is told here rather than left to find out.

### Still open

Independent review of this package, and then the authorized operator's
restoration of the target path set for `baton.merge`'s preflight.
