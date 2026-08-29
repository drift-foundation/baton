# Finding: compose the local OCI lifecycle

Promoted implementation record for the fifth bounded child of W5. It is W5's
integration Job and remains top-level on disk because the parent dossier is at
maximum nesting depth.
Canonical Work: W6636.

## Confirmed boundary

Compose only reviewed W5 components with completed Python manager receivers.
Exercise the approved two-container consent/execution topology through the
trusted adapter: restricted consent, positive quiescence/destruction, exact
claim and activation, then fresh execution with the private workspace. Compose
effectively-once start/inspect/cancel/freeze/collect/destroy and positive
absence without granting engine observations authority meaning.

This Job owns integration and mutable local-engine evidence, not the component
implementations or W6's independent 109-case conformance certification.

## Acceptance

- Real Docker lifecycle covers consent/decline/activation/execution/success,
  refusal, fault and cancellation with exact durable identities.
- Restart, duplicate start, stale generation, partition/uncertain observation,
  multi-match and cleanup recovery preserve fail-closed ordering.
- No execution workspace exists in consent; consent is absent before execution
  creation; collection follows quiescence; replacement follows positive absence.
- Podman runs the same adapter contract when available; absence is recorded as
  environment evidence rather than changing the vocabulary.
- All component and manager dependencies are closed satisfying before terminal
  integration signoff; W6 remains the separate certification gate.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## 2026-08-27 independent integration review

**Confirmed:** the first-round module is valuable diagnostic evidence, not a
terminal or partial certification result. Its 24 Docker cases expose two
integration-breaking defects and its retained mutation harness reports all 18
targeted rule removals caught. The implementation correctly does not claim the
success/freeze/collect/destroy/positive-absence half or satisfying dependency
closure.

**[P0] Confirmed:** the proposed “certified arc” does not actually avoid
W6634's provisional implementation. W6634 changed the shared
`OciAdapter.start` refusal/settlement path and `OciAdapter.destroy` credential
ending in `v12/python/src/baton_v12/worker_manager/oci.py`; even an adapter
constructed with `outputs=()` and `credential_delivery=None` executes those
paths. `run_vector` also calls W6634's `_credential_mounts` for the empty
delivery. W6634's seventh review requested changes and its terminal outcome
explicitly says the retained code is provisional. The new cases therefore
exercise a provisional combined tree. They may be retained as reproductions,
but no part of their result is independently accepted until replacement
output-custody and credential-delivery Work establishes the shared path.

**[P0] Confirmed:** the accepted OCI adapter and reference worker do not join.
The adapter's `run_vector` supplies no environment, while the worker requires
`BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`, `BATON_WORKER_CONTRACT`, and
`BATON_WORKER_ROLE`. The real-engine evidence records an immediate exit 2 with
no frame. This blocks every successful execution ending.

**[P0] Confirmed:** reconciliation treats membership in `docker ps --all` as a
running runtime. `reconcile_runtime` attaches the sole matching identity
without asking `adapter.observe`; an exited worker is consequently stored as
`execution_runtime=running`. Exact observation must distinguish live,
quiescent, absent, and uncertain before the manager advances lifecycle state.

**[P1] Confirmed:** consent is not composed “through the Python manager” as the
confirmed boundary requires. The test drives a consent-posture adapter and
writes the `consent_runtime` axis directly because no manager operation joins
them. That is a missing production composition seam, not merely later polish.

**[P1] Confirmed:** W6636 consumes W19784's input-root authorization and
assignment-manifest delivery, but the ledger has no dependency edge to W19784.
The same round also found W19784's three `check_input_pair` receiver parameters
missing from the contracts inventory, making the full-tree gate one failure
redder than its six accepted baseline failures. The ownership gap needs a
separate follow-up to the closed Work and W6636 must depend on that correction.

**Open decision:** approve the prior W6634 checkpoint's decomposition into two
independently reviewed successors: output custody and credential delivery. The
shared start/destroy crossing must be assigned explicitly rather than treated
as accepted by either slice. W6636 then needs bounded correction Work for the
worker launch contract, exact runtime observation, and manager-owned consent
composition before this integration can resume.

**Verification limitation:** the reviewer invoked the exact composition module
under the source layout. Import and discovery succeeded, but the managed shell
denied its nested Docker-socket access at `setUpClass`; policy forbids an
escalated retry. A standalone `docker info` independently confirmed Docker
29.1.3 and its daemon are reachable. The implementer's retained real-engine
transcript remains evidence, but it is not an independent reviewer rerun.

## Approver decomposition ruling — 2026-08-27

Do not waive W6634's non-satisfying outcome and do not resume W6636 over its
provisional shared paths. Approve the recorded split into two independently
reviewed provider Works:

1. output custody; and
2. fresh-run credential delivery.

W6636 explicitly owns their shared start/destroy settlement crossing and the
later restart-adoption, reconciliation and orphan-convergence matrix. The two
component successors must not claim that integration acceptance themselves.

Also create four bounded correction Works discovered by composition:

1. deliver the four non-secret `BATON_WORKER_*` launch values through the OCI
   seam and prove the adapter-started reference worker remains runnable;
2. reconcile exact runtime state through `adapter.observe`, preserving
   uncertainty and never recording an exited runtime as running;
3. add the production manager operation that owns consent-runtime creation,
   teardown and ordering; and
4. follow up closed W19784 by registering the three `check_input_pair`
   receiving parameters and restoring the aggregate contracts inventory.

Record W19784 itself as a historical W6636 dependency and make all six new
Works live W6636 blockers. Retain the 24-case module and mutation harness as
diagnostic starting evidence. W6636 resumes integration only after all six
providers close satisfying; then it must replace the current expected-failure
observations with positive real-engine regressions and obtain independent
Docker review.

## Decomposition coordination result — 2026-08-27

**Confirmed:** the approver-authorized decomposition is now durable and
ledger-bound. W26283 owns output custody; W26284 owns fresh-run credential
delivery; W26291 owns the four-value reference-worker launch environment;
W26294 owns exact observation-backed reconciliation; W26295 owns the
manager-composed consent runtime; and W26296 follows W19784 for the missing
`check_input_pair` receiver inventory.

**Confirmed:** W19784 is the historical assignment-identity dependency. Its
closed satisfying result does not substitute for W26296's bounded inventory
correction.

**Operational finding:** the canonical v11 CLI refused the approver-requested
W6636 dependency edge to closed W19784: “a dependency on finished work gates
nothing — depend on follow-up Work instead (WS-2 ruling: new blockers target
only open Work).” No workaround was attempted. W19784 is therefore preserved
as dossier provenance and as W26296's atomic `follow-up-of` relation, while
W26296 is the permitted live gate.

**Confirmed:** all six new Works are required live W6636 blockers. W6636 keeps
ownership of the providers' shared quiescence/output-read/container-removal/
credential-removal/clean-settlement crossing plus restart adoption, recovery,
reconciliation policy, and orphan convergence. No provisional W6634 code is
accepted by creating these successors.

## Consent topology superseded — 2026-08-27

The confirmed boundary, acceptance text, diagnostic tests, and decomposition
above are superseded wherever they require two consent/execution containers, a
`consent_runtime` axis, or positive absence of that consent runtime. They remain
useful evidence of why W26295 was created, but are not production requirements.

W6636 now composes one direct crossing: the trusted adapter reserves an
eligible slot without launching a runtime, the Worker Manager atomically
claims, and only a successful claim launches the single execution container.
Offer expiry or a lost claim race launches nothing. Post-claim launch failure,
agent `plan-rejected`/`unsupported`, cancellation, quiescence, output custody,
credential removal, restart adoption, reconciliation and orphan convergence
remain typed lifecycle cases.

The execution container may see the exact assignment source through read-only
`/input`; it may not see the Baton authority store, integration credentials,
unrelated host paths, or a writable canonical checkout. Credentials retain
their separate read-only provider. W26295 closes cancelled as superseded and
is not a satisfying implementation prerequisite.

## Attempt-domain invariant carried in from W28681 — 2026-08-28

Recorded here by `baton.claude` while implementing W28681
(`work/records/2026/08/finding-managed-acp-tool-process-lifetime/`), which is
a live prerequisite of this Work on the ledger. W28681 owns the v11 half; this
entry is the v12 half it hands over, and W6636 owns it because the destroy and
settlement crossing is already W6636's.

**Confirmed, from W28681's incident:** a managed agent that owns no process
domain accumulates tool processes it cannot enumerate or destroy. Five tool
process groups survived 34-36 hours and several later turns below one ACP
agent; four had called `setsid`, so they were in neither the supervisor's
process group nor its session, and one held a full core. The supervisor's
readiness probe proved only that the bridge was alive — not that the current
turn was progressing, and not that earlier turns' children had been reaped.

**Confirmed:** v12 has the stronger native boundary and must not restate the
v11 mechanism. An execution container IS the attempt's process domain, so the
invariant reads:

- Success, failure, cancellation, deadline, restart reconciliation and orphan
  recovery each FORCE-REMOVE the exact execution container and OBSERVE
  POSITIVE ABSENCE before the attempt settles cleanly, before credentials are
  removed, and before any replacement is started.
- A container reported `exited` is not sufficient. A runtime object that still
  exists is a domain that still exists; manager state stays
  `uncertain`/cleanup-required until adapter observation proves absence.
- Inability to prove absence FAILS CLOSED exactly as W28681's teardown does:
  the attempt is not settled clean, the lane is not reused, and nothing is
  inferred from the absence of evidence.
- The container must not be able to launch host or sibling-container processes
  outside its runtime boundary, which is the container-level equivalent of the
  PID namespace v11 now requires of its agent launcher.

**Not implemented by W28681, and deliberately so.** W28681 changed the v11 ACP
bridge, its configuration contract, the shipped Claude launcher and that
deployment's verifier. It did not touch the v12 manager: this crossing is
W6636's, and implementing it from another Work would be the second owner of
one rule that this campaign keeps correcting for.

## Unblocked implementation revalidation — 2026-08-28

**Confirmed:** W6636 has no open ledger blocker. The replacement providers
W26283 (output custody), W26284 (fresh-run credentials), W26291 (launch
document), W26294 (exact runtime observation), W26296 (input receiver
inventory), and the carried W28681 prerequisite all closed satisfying. W26295
closed cancelled under the direct claim-to-execution supersession. W6634's
non-satisfying result remains historical evidence, but its output and
credential surfaces now have the two reviewed replacements the decomposition
required. Implementation can resume; it may not treat W6634 itself as
accepted.

**Observed:** the retained real-engine module is still the first-round
diagnostic, not the resumed composition. Its module contract says output and
credential paths are provisional; its adapter fixture supplies neither an
output declaration nor a credential delivery; and three cases still create or
require the superseded consent runtime:

- `test_the_consent_runtime_is_torn_down_before_execution_exists`;
- `test_consent_is_absent_before_the_execution_container_is_created`; and
- `test_a_credential_never_delivered_is_not_reported_torn_down`.

`test_destroy_is_unreachable_without_the_provisional_path` is now the inverse
of the required result. These cases are useful evidence of the old boundary,
but they must be replaced by direct one-container lifecycle evidence. The
remaining input-root, activation, effectively-once start, cancellation
ordering, restart, multiplicity, launch, and exact-observation assertions stay
valuable and are not superseded.

**Confirmed existing crossing:** `intake.authorize_cleanup` calls
`OciAdapter.destroy` before journalling settlement. `destroy_vector` uses
`rm --force --volumes`, `OciAdapter.destroy` observes the exact runtime after
that command, and `intake._settle` advances `execution_runtime=destroyed` and
the cleanup ending only for observed `absent`. An `uncertain` observation
leaves cleanup retryable and a positively present runtime fails cleanup. This
is the correct runtime half of the W28681 attempt-domain invariant and should
be composed, not reimplemented.

**[P0] Observed integration gap:** the same destroy answer carries separate
`credentials` and `launch` endings, but `intake._destroyed` requires only
`runtime_id`, `state`, and `why`, and `intake._settle` never evaluates the two
provider endings. Credential teardown raises when it cannot prove removal, but
`OciAdapter._launch_ended` can return `lifecycle_state=unresolved`; the manager
can therefore record cleanup `complete` or `retained` after positive container
absence while the launch root is still present. W6636 owns this shared
settlement crossing. A clean attempt, credential release, lane reuse, or
replacement must require the applicable provider endings to be positively
terminal, with uncertainty/failure preserved as cleanup-required rather than
discarded as an extra adapter field.

**[P0] Observed integration gap:** `attempts.request_runtime_start` journals
`execution_runtime=start-requested` and then calls `adapter.start`. A refused
or post-create start exits through `OciAdapter._refused_start`, which reduces
credential and launch endings to refusal prose and raises. The manager neither
records a typed launch-failure ending nor immediately reconciles the exact
runtime identity, so a successful atomic claim can strand an attempt at
`start-requested`. The resumed composition must define and exercise the
manager-owned settlement: observe by exact labels/identity, force-remove any
runtime the failed start may have created, prove absence, settle both delivery
roots, and preserve uncertainty without launching a replacement.

**Confirmed vocabulary clarification:** `plan-rejected` is a terminal worker
disposition. `unsupported` in the supersession means the typed
`unsupported-version` handshake refusal; it is not a fifth worker disposition
and must not be silently added to or aliased into the frozen disposition axis.
Both paths still need one-container integration evidence and the same cleanup
invariant.

**Proposed patch boundary:** change only production composition needed to join
the reviewed manager and adapter operations, then replace the stale parts of
`v12/python/tests/manager/test_lifecycle_composition.py`. Do not duplicate
provider internals in W6636. The complete real-engine arc is offer reservation
without a runtime, accept, atomic authority claim, activation, exact input and
private-root composition, one execution start, agent outcome, positive
quiescence, freeze, intake, retention decision, force-removal, exact absence,
provider teardown, and only then clean settlement and slot reuse.

**Required negative/race evidence:** decline, offer expiry, and lost claim
create no container or delivery; post-claim start refusal and a post-create
failure converge without a duplicate; `plan-rejected`, unsupported-version,
unable/fault, cancellation, and deadline take the same cleanup crossing;
exited-but-present is not absence; observation uncertainty preserves the
runtime, roots, lane, and retry obligation; restart adopts one exact live
runtime, removes an exact ended runtime before reuse, and rejects mismatches or
multiple candidates; orphan recovery is bounded to the attempt and cannot
delete a sibling attempt's roots.

**Verification boundary:** required Docker evidence fails rather than skips.
Podman remains additive and records a narrow availability skip. Independent
review must inspect the engine after each terminal case for positive absence,
not infer cleanup from the store row or a zero exit status.

## 2026-08-28 — the two shared-crossing [P0]s, corrected

**Confirmed, and WORSE than this dossier pinned it — the destroy contract did
not name the provider endings at all.** The pinned observation says
`intake._settle` "never evaluates the two provider endings", so the manager
could record cleanup `complete` while a launch root survived. Revalidated
against the tree, that is one layer below what actually happened:
`_destroyed` owns the adapter's answer with
`boundaries.document(..., required=("runtime_id", "state", "why"))` and no
`optional`, and `_members` REFUSES an unrecognised member rather than ignoring
it. So the real `OciAdapter.destroy` answer — which always carries
`credentials` and `launch` — was refused outright, and `authorize_cleanup`
could not complete against the real adapter at all.

Both readings required the same correction and the second is the one that
matters, so the endings are named on the contract AND read: a clean settlement
now requires every present provider ending to be terminal
(`not-delivered` or `torn-down`), and `unresolved` keeps cleanup open with the
reason. Positive container absence is what makes it SAFE to settle the mounted
roots; it is not evidence that they were settled.

**Confirmed by our own regression — an unsettled cleanup could never be
retried.** `_settle` returned `cleanup_unsettled` from inside the journalled
transaction, so the destroy operation committed with "it did not settle" as
its result. A retry of that cleanup is the same receipt under the same policy,
which is an exact retry, and it replayed the non-ending forever. "The offer to
try again is the axis staying where it is" was true of the AXIS and false of
the OPERATION, and it was true of the pre-existing `uncertain` branch too.

Nothing that fails to settle is journalled now. That puts a non-ending in
exactly the state this module's own ordering note already describes as safe —
the one a crash between the engine call and the journal leaves — and the next
authorization runs the destroy again, which is `rm --force` followed by an
inspection of the exact identity. This was not in the pinned list; it was
surfaced by writing the retry the required correction implies, and the required
correction is not satisfiable without it.

**Confirmed corrected — a refused post-claim start is settled, not stranded.**
`request_runtime_start` journals the start operation, moves
`execution_runtime` to `start-requested`, and only then calls the adapter. A
refusal from that call propagated untouched, leaving the attempt claimed,
activated and stranded with no runtime identity — and `authorize_cleanup`
refuses exactly that shape, so nothing could clean it up either. A successful
atomic claim could end in an attempt no operation in this manager could move.

The manager now reconciles through the operation that owns the answer: a
runtime carrying this attempt's labels is ATTACHED, which is what makes it
nameable by the ordinary destroy crossing, and a state the manager cannot
establish is recorded `uncertain`. No replacement is started on either path.
What the ADAPTER did about its own refusal is not what the manager knows —
`_refused_start` settles both roots and says so in refusal prose, and prose is
not a durable manager fact.

**Confirmed decision — the refusal keeps its own closed pair.** A first
version retyped every settled start failure as `refused/start-failed`, and the
boundary inventory caught it: a malformed start ANSWER is `integrity/schema`
at `_started`, and relabelling it made the manager's account disagree with the
boundary that found it. Category and code cross unchanged and only the message
grows, because settling is not a different thing going wrong. The typed ending
that a caller acts on is the DURABLE one — the attached identity or the
`uncertain` axis — which survives the process the refusal is raised in.

## 2026-08-28 — independent review of the resumed P0 round

**Confirmed P0 — provider teardown can be bypassed on cleanup retry.** A first
destroy may prove the runtime absent, advance `execution_runtime` to
`destroyed`, and leave cleanup pending because a provider ending is
`unresolved`. The exact retry then takes `_destroyed`'s already-destroyed
shortcut, does not call the adapter, receives no provider endings, and records
cleanup complete because those members are optional. The last known
unresolved provider is therefore erased by omission. Provider applicability
and outstanding teardown must remain durable independently of the runtime
axis; see `evidence/w6636-review-p0-retry.py`.

**Confirmed P0 — failed refused-start reconciliation is still stranded.** If
the start refuses and the immediate exact-state reconciliation also refuses,
`_start_failed` augments the error prose but leaves the durable attempt at
`execution_runtime=start-requested` with no runtime identity. Every
refused-start settlement exit must leave an attached identity or a durable
`uncertain` ending; reporting both failures is necessary but is not itself
settlement.

## 2026-08-28 — the re-reviewed [P0]s, corrected

**Confirmed — the shape this round introduced defeated itself one call
later.** `_destroyed` short-circuited on `execution_runtime == "destroyed"`
and answered a synthetic `absent` WITHOUT CALLING THE ADAPTER. The first
destroy truthfully moves that axis while a provider reports `unresolved`, so
the retry that was supposed to finish the teardown skipped the adapter
entirely — and because the provider endings are optional, an answer carrying
none of them recorded cleanup `complete` with no provider retried at all. The
correction that made an unsettled cleanup retryable and the short-circuit that
made the retry vacuous were added in the same round.

The runtime axis is a fact about the CONTAINER and says nothing about the
roots it mounted, so an attached identity is now always asked about. Removing
an identity the engine no longer has is safe — `destroy` is `rm --force`
followed by an inspection of the exact identity, and a gone identity answers
`absent` — so the short-circuit bought nothing and cost the second half of the
ending.

**Confirmed decision — the outstanding ending survives by being RE-ASKED
rather than remembered.** The provider's state is the provider's fact, so a
manager restart that re-runs the destroy gets the adapter's current answer
instead of replaying a note about it. This is what makes the ending survive
the runtime-axis transition and a process restart without a schema change.

**Confirmed — an ending recorded only on the happy path is not an
invariant.** `_start_failed` caught a failed reconciliation to EXTEND THE
MESSAGE and nothing else, so an adapter whose listing was unavailable left the
attempt at `start-requested` with no identity — the exact stranded state the
settlement was written to remove, reached through the one path where the
manager knows least. Every exit now leaves an ending: `_settle_unknown_start`
records `uncertain` before the refusal is raised, and it is written ONLY from
`start-requested`, so a reconciliation that recorded something truer before it
failed is never overwritten.

**Confirmed scope — a fault is a failed start too.** An adapter that raises
something other than a `ContractRefusal` says even less about what it created
than one that refuses, and it left the same stranded attempt. It is settled
and then re-raised UNCHANGED: this manager has no account of what the fault
was, and inventing one would be worse than the fault.

## 2026-08-28 — independent re-review of the second P0 round

**Confirmed P0 — provider omission still erases outstanding teardown.** The
retry now calls the adapter, but provider endings remain optional and the
manager persists neither applicability nor the prior unresolved ending. After
an `unresolved` launch answer and a manager restart, an otherwise valid
runtime-absent answer that omits `launch` records cleanup `complete`. Re-asking
preserves the ending only when the adapter repeats the member; omission is
still treated as evidence that no provider exists. See
`evidence/w6636-review-provider-omission.py`.

**Confirmed P0 — a fault-created runtime is not reconciled.** The
non-`ContractRefusal` start catch records `uncertain` directly and re-raises,
without calling `reconcile_runtime`. A runtime created before the adapter
fault is therefore left unnamed even when list and exact observation can
identify it. Reconciliation must precede the uncertain fallback on this path
just as it does for a typed refusal; see
`evidence/w6636-review-fault-created-runtime.py`.

## 2026-08-28 — the third-round [P0]s, corrected

**Confirmed — the destroy-answer contract is CLOSED, and the two provider
endings are required.** Optional was exactly the hole. A first answer of
runtime `absent` with launch `unresolved` correctly left cleanup pending; a
later answer that simply OMITTED `launch` then settled it `complete`, because
an absent member reads as "no such provider" and the manager remembers
nothing. The adapter was called — what was lost was the knowledge that a
launch teardown was owed.

The review offered two resolutions and this takes the second: the manager
cannot remember applicability without inventing durable state for it, so the
CONTRACT says it. Every provider answers on every destroy, and an attempt with
no such provider says `not-delivered` out loud. `OciAdapter` always answering
both was a habit of one implementation, and `authorize_cleanup` is a generic
public boundary — a durable invariant that rests on a habit is not one.

**Confirmed — the fault path takes the same settlement boundary as the
refusal path.** The first correction caught a non-`ContractRefusal` fault and
called `_settle_unknown_start` directly, which asks the adapter nothing. So a
driver that created a runtime and then raised left that runtime unnamed and
outside the ordinary destroy crossing, even though `list` and exact `observe`
would have found and identified it immediately. A fault says LESS about the
start result than a typed refusal; that makes exact reconciliation more
necessary rather than less. `_settle_failed_start` is now the one boundary for
both, the `uncertain` fallback is retained for a reconciliation that cannot
answer, and the fault itself is re-raised unchanged.

**Confirmed — a test double that completes what a case named hides contract
violations.** The first attempt at closing the contract gave the shared
`Custodian` a `not-delivered` default for both endings, and the reviewer's own
omission reproduction promptly stopped reproducing: the omission never reached
the manager. The double now returns exactly what a case names, and the cases
that want the defaults say so. This is the same class of defect as the one
being corrected — a missing thing silently read as a benign one — and it was
found by running the reviewer's file rather than by reading the diff.

## 2026-08-28 — independent third re-review

**Confirmed corrected.** Required provider endings make omission a schema
refusal across restart, and the shared failed-start settlement attaches a
runtime created before either a refusal or an ordinary fault while preserving
the original failure and the `uncertain` fallback.

**Confirmed P2 — the new shared-boundary regression leaks its fixture.**
`test_both_kinds_of_failed_start_take_one_settlement_boundary` calls
`tearDown()` on a manually constructed test case whose directory and store are
registered with `addCleanup`; the registered cleanups never run. The focused
gate emits implicit-directory and unclosed-SQLite `ResourceWarning`s. See
`review-2026-08-28T14-14-18Z.md`.

## 2026-08-28 — independent review of the P2 cleanup correction

**Confirmed corrected.** The manual `TestCase` regression and the four
implementer-owned corrected evidence scripts now execute their registered
cleanups. The 207-test focused manager gate and all four scripts pass with
`ResourceWarning` promoted to an error. This accepts only the P2 cleanup; the
integration remainder remains open. See `review-2026-08-28T14-22-39Z.md`.

## 2026-08-28 — the arc composes, and it found two more missing seams

**Confirmed — the one-container arc reaches a clean settlement on a real
engine.** Offer reservation, accept, atomic claim, activation, exact input and
private-root composition, one execution start, positive quiescence, freeze,
intake, retention, force-removal, exact absence, both provider teardowns and a
clean settlement, through the PRODUCTION providers: W26283 declares the
output, W26284 materializes the credential, W26291 delivers the launch
document. The previous rounds composed this with `outputs=()` and
`credential_delivery=None` and could not reach an ending at all.

**[P0] Confirmed and corrected — `OciAdapter` had no `retain` at all.**
`intake.decide_retention` types `adapter.retain` as a capability and delivers
`outputRetainBody` to it. The accepted adapter simply did not implement the
method, so a composed lifecycle refused at retention and could never reach the
destroy crossing. This is the same class as the first round's missing `--env`
and missing `observe`: two accepted components, each right about its own half,
with nothing between them.

**Confirmed scope — the new `retain` owns its command and acts on nothing, and
that is a REPORTED GAP rather than a design.** What a local adapter should do
to the custody tree on each disposition — whether `discard-after-intake`
removes those bytes, and when relative to the runtime's destruction — is
stated by no accepted finding this Work can read. Inventing a deletion here
would be this seam deciding a retention semantics for the Work that owns
custody, over material a later cleanup still reports on. Named rather than
guessed.

**[P0] Confirmed and corrected — the destroy contract refused the manager's
own delivery.** `authorize_cleanup` delivers `{**destroy_command(...),
"operation": ...}`, which `OciAdapter.destroy`'s own docstring describes, while
its member list named only the body — and an unrecognised member is refused
rather than ignored. The composed lifecycle therefore refused at the destroy
crossing, one step past the retention seam that was missing entirely. Both
were invisible to either side's own suite.

## 2026-08-28 — independent review of the first one-container slice

**Confirmed P0 — `discard-after-intake` is a no-op that permits a false clean
ending.** `OciAdapter.retain` accepts the command and returns
`{"delivered": True}` without changing its custody tree. The composed arc then
records `cleanup=complete` and proves the credential and launch roots are gone,
but never checks the custodied artifact. The daemon-independent reproduction
prints `discarded artifact still exists: True`; see
`evidence/w6636-review-retention-noop.py` and
`review-2026-08-28T14-38-40Z.md`.

This is not an open retention-policy-document decision. W6629 already pinned
the command boundary: `output.retain` crosses to the side holding the material
because the disposition decides what happens to it, and `complete` is distinct
from material retained. W6636 owns that cross-provider integration. The local
adapter must enact the frozen disposition and establish the named discard
before the arc can claim a clean settlement.

## 2026-08-28 — the retention no-op, corrected

**Confirmed — and my own account of it was wrong.** I recorded
`OciAdapter.retain` acting on nothing as an unspecified retention semantics
this seam should not invent. It is not unspecified. The manager's own
settlement rule says `complete` means nothing was kept, so an arc that selected
`discard-after-intake` and then accepted `cleanup=complete` over surviving
custody bytes was reporting a FALSE CLEAN ENDING. W6629 had already decided the
boundary: `output.retain` is delivered to the side holding the material
BECAUSE retention decides what happens to that material. Deferring it to a
ruling was deferring a defect.

**Confirmed corrected — the disposition is enacted, and the path is derived.**
`discard-after-intake` removes only the named, adapter-owned custody trees and
establishes their absence before returning; `retain` and `quarantine` leave the
bytes untouched. An artifact identity is `attempt:name` and the tree is derived
from it, so a caller cannot name a path, cannot reach another attempt's
material, and cannot discard an output this assignment never declared — each is
refused rather than resolved. An exact retry discards an already-absent tree,
which is the state it asked for: the manager delivers this before its own
journal, so a crash between the two makes the next authorization repeat it.

## 2026-08-28 — independent re-review of the retention correction

**Confirmed P0 — a keep disposition does not establish that anything is
kept.** `retain` and `quarantine` return success without observing the named
custody trees. If custody is absent after intake, the manager can journal the
keep decision and later report cleanup `retained` over no retained material.

**Confirmed P1 — every unknown disposition means delete.** The implementation
branches on the two keep values and sends every other string through the
`discard-after-intake` path. A malformed or future value therefore destroys
custody instead of failing closed. See
`evidence/w6636-review-retention-fail-closed.py` and
`review-2026-08-28T14-49-59Z.md`.

## 2026-08-28 — the two fail-open retention endings, corrected

**Confirmed — a keep disposition succeeded over material that was already
gone.** The `retain`/`quarantine` branch returned without observing anything,
so custody that vanished between intake and retention was journalled as kept
and cleanup then derived `retained` — an ending whose whole meaning is that
the material is still there. That is the keep-side twin of the false `complete`
the previous review found, and it fails the same way: an ending reported over
bytes nobody looked at. Every named tree must now be positively present, and
the refusal lands BEFORE the manager journals the decision.

**Confirmed — an unknown disposition fell through to the destructive
branch.** The code asked only whether the value was one of the keeping pair;
everything else discarded and reported success. A typo or a value from a later
vocabulary therefore removed the material. An adapter boundary that owns a
destructive command may not make unknown mean delete, so the disposition is
now checked against exactly the frozen three before the artifact names are
resolved, let alone before anything is removed.

**Confirmed pattern, three reviews running.** All three retention findings are
one shape: an ending reported without the observation that would justify it.
The no-op reported `complete` over surviving bytes; the keep branch reported
`retained` over absent ones; the unknown disposition reported success over a
removal nobody asked for. Each was fail-open in the direction that looked
harmless from inside the branch that wrote it.

## 2026-08-28 — independent re-review of the fail-closed corrections

**Confirmed corrected.** The destructive command validates the frozen three
before resolving names or touching custody, and both keep dispositions require
every named custody directory to be positively present before success. The
selective, derived, positively absent, idempotent discard behavior remains
intact. The focused 231-test gate and corrected evidence pass warning-clean;
see `review-2026-08-28T15-00-01Z.md`.

## 2026-08-28 — the superseded cases, replaced

**Confirmed — the four cases the supersession invalidated are gone, and what
was true in them is kept.** Three drove a consent container and the fourth
reported that destroy sat behind provisional code. The topology has one
container and destroy is reachable, so all four asserted a boundary that no
longer exists; deleting them without replacements would have cost real
coverage, which is why they were left standing until the arc landed.

What replaced them, rule for rule:

- the consent teardown case proved a container mounted nothing and was
  destroyed before execution. The ordering claim survives as
  `test_a_reservation_launches_no_runtime` and
  `test_only_a_successful_claim_launches_one_container` — nothing runs before
  the atomic claim, exactly one container after it.
- the consent-absent-before-execution case compared two containers' positions
  in one trace. With one container the ordering that matters is between the
  claim and the launch, which the pair above reads off the same trace.
- the `not-delivered` versus `absent` distinction was asserted on a consent
  adapter and is not about consent at all. It is asserted on the live
  one-container topology now, where it has its other half beside it: the full
  arc proves a delivery that WAS made ends `torn-down` with its root gone.
- the destroy-unreachable case said it would fail and say so when a later
  slice made destroy reachable on certified code. It has. The rule underneath
  it — cleanup destroys nothing it has no receipt for — is kept as
  `test_cleanup_without_an_intake_receipt_is_blocked_rather_than_run`.

**Confirmed added — the lost claim.** `test_a_lost_claim_launches_nothing`:
an authority that refuses the claim is an authority saying somebody else holds
it, and the loser must reach no engine.

## 2026-08-28 — independent review of the superseded-case replacements

**Confirmed partial replacement.** Reservation-before-claim, exactly one
post-claim execution container, provider `not-delivered` versus `torn-down`,
and cleanup blocked before destroy without an intake receipt preserve the live
rules beneath the four retired cases.

**Confirmed P1 — the lost-claim case is not a lost claim.** It supplies `None`
as the authority answer, which the port refuses as a malformed claim document
with `integrity/schema` while leaving the offer `accepted`. `submit_claim`
never launches on any path, and the test attempts no later manager step, so its
empty engine trace does not prove a competing-claim loser cannot cross into
execution. See `evidence/w6636-review-lost-claim-shape.py` and
`review-2026-08-28T15-10-16Z.md`.

## 2026-08-28 — the lost-claim case, corrected

**Confirmed — a malformed document is not a competing claim.** The first
version set `claim_answer = None` and described that as the authority saying
somebody else holds the claim. The port owns a claim answer as one exact
assignment document, so `None` is refused `integrity/schema`, the offer stays
`accepted`, and nothing is settled. Its closing assertion was then
non-probative: `submit_claim` launches no runtime on ANY path, and the case
never attempted the step after it.

**Confirmed corrected — the race is the claim capability's typed refusal, and
the crossing is what is asserted.** The refusal crosses from the capability,
the offer reaches its durable `claim-refused` ending through the settlement
path the port already has, and then the next two lifecycle steps are refused
with their reasons pinned: activation because the attempt has no committed
claim, and start because it is not activated. No `run` reaches the engine and
no container carries the labels. That is the supersession's actual
requirement — a loser cannot cross from reservation into execution.

## 2026-08-28 — independent re-review of the lost-claim correction

**Confirmed corrected.** The typed refusal, durable `claim-refused` settlement,
activation refusal, start refusal, empty run trace, and direct no-container
query establish the losing reservation cannot cross into execution. The
focused 269-test gate passes warning-clean; see
`review-2026-08-28T15-18-37Z.md`.

## 2026-08-28 — the security inspection and the orphan bound

**Confirmed — the container's boundary is asked of the ENGINE, not of the
argv.** An adapter that composed the right flags and an engine that applied
them are two facts, and only the second protects anything. The live container
is inspected: exactly four mounts (`/input` read-only at the proved source,
the one writable workspace, and the credential and launch deliveries each
read-only at its own fixed path) and no others; `NetworkMode` none; no
privileges, `CapDrop: ALL` with nothing added, `no-new-privileges`, a bounded
pid count, a read-only rootfs and a non-root user.

**Confirmed — what is ABSENT is asserted by name.** The authority store, this
repository's checkout and the engine's own socket are each named, because "the
mount list is short" is a different statement from "these exact things are not
in it". With no socket mounted and no network at all there is nothing to ask
for a sibling container, which is the container-level form of the PID-namespace
invariant W28681 carried in.

**Confirmed — orphan recovery is bounded to the attempt that proved it
stale.** A `CredentialHome` is assignment-scoped and holds several attempts'
roots, so "no record for THIS attempt" is not evidence about any other. Two
real deliveries are materialized through the manager's own seam and exactly
one is recovered; the sibling's root and its live bearer both survive.

## 2026-08-28 — independent security and orphan review

**Confirmed partial.** Daemon inspection establishes the exact mount targets
and sources plus the applied no-network, unprivileged, capability-drop,
no-new-privileges, bounded-PID, read-only-root and non-root configuration.

**[P1] Confirmed — the orphan case does not cross production recovery.** It
calls `CredentialHome.discard_orphan` directly and still passes with
`OciAdapter.recover_credentials` disabled. It therefore cannot catch the
adapter applying one attempt's recovery evidence to assignment-wide cleanup.
See `evidence/w6636-review-orphan-seam.py`.

**[P1] Confirmed — excluding only host PID mode admits a sibling process
domain.** The applied-boundary case passes with
`PidMode=container:sibling-runtime`, even though that is not the attempt's own
namespace. Pin the private/default engine answer; see
`evidence/w6636-review-security-shape.py` and
`review-2026-08-28T15-29-25Z.md`.

## Approver scheduling ruling — 2026-08-28

W6636 became an integration campaign disguised as one leaf Job. Its message
and review history now mixes the positive one-container Docker arc with
provider corrections, negative races, restart adoption, orphan recovery,
security inspection and an unavailable alternate engine. That prevents the
ledger from showing what is complete, what is being corrected and what has not
started.

The critical-path acceptance is now the smallest honest happy path: one real
Docker runtime traverses claim through launch, execution, output custody,
settlement, cleanup and positive absence. Corrections and security/orphan
evidence already implemented or submitted in the current assignment remain in
this review; no scope is changed underneath the live claimant. A defect that
would let this path report false success still blocks acceptance.

Passing this boundary says the composed design is promising; it does not call
the platform production-ready. Reaching the finish line first validates that
the major seams work together before exhaustive tests and resilience machinery
are built around choices a later phase may change. The hardening requirements
remain visible below and are completed after or alongside that validation,
never silently discarded.

For this composition, W6636 is the current capability pass. Its separately
scheduled negative/race, restart-adoption and Podman outcomes are later-pass
requirements with preserved acceptance boundaries, not optional omissions.
They become critical only after the Docker arc has demonstrated the design is
promising, or earlier when one exposes a defect that would make that very
demonstration false.

At the next handoff, any materially unstarted remainder becomes separate M2
Work with its own claim, evidence, review and outcome. The expected cuts are:

- negative and race endings, including offer expiry, non-duplicating
  post-create failure, and the shared cleanup crossing for `plan-rejected`,
  unsupported version and deadline;
- exact-ended runtime adoption across manager restart before lane reuse; and
- Podman certification, parked until a real engine is available rather than
  simulated as Docker.

These are robustness Jobs, not an excuse to lose their existing recorded
requirements. They may advance concurrently through non-overlapping ownership,
but they do not hold the next proof stage unless an explicit dependency states
why that stage cannot produce an honest result without one of them.

## 2026-08-28 — the two [P1]s on the security and orphan slice

**Confirmed — excluding one unsafe value is not requiring the safe one.** The
process-domain assertion said only that `PidMode` is not the literal `host`,
and Docker also admits `container:<runtime>`, which JOINS a sibling's PID
namespace and is precisely not the attempt-owned process domain W28681 carried
in. The engine's own private-namespace answer is pinned now — Docker spells it
as the empty string, Podman as `private` — so anything naming somebody else's
domain fails. The pid bound is asserted exactly rather than as "greater than
zero", since the case claims to be about the boundary the launcher composed.

**Confirmed — a composition case that bypasses the production seam composes
nothing.** The orphan case called `CredentialHome.discard_orphan` directly, so
an adapter reaching for the assignment-wide `discard_orphans`, or applying
evidence about one attempt to its sibling, would not have been caught. It
drives `OciAdapter.recover_credentials` now, over the ADAPTER'S OWN credential
home — building a separate home and then calling the adapter recovered an
empty directory and proved nothing, which is what it did until this was
corrected. Measured: with `recover_credentials` replaced by a no-op the case
fails.

## 2026-08-28 — independent correction re-review and bounded acceptance

**Confirmed corrected.** The applied PID namespace is pinned to the target
engines' private/default answer and the limit to 512. Orphan recovery now
crosses `OciAdapter.recover_credentials` over its own home; a successful no-op
mutation is called and fails the case. See
`evidence/w6636-review-orphan-seam-correction.py` and
`review-2026-08-28T15-39-21Z.md`.

**Confirmed bounded outcome.** Under the approver's scheduling ruling, W6636
may close satisfying as the positive one-container Docker capability pass.
That outcome means the composed design is promising, not production-ready.
The negative/race endings, exact-ended restart adoption and Podman
certification remain mandatory separate M2 follow-up Work rather than waived
acceptance.

## 2026-08-28 — terminal follow-up ledger cuts

W6636 closed satisfying in the bounded meaning above. Its mandatory later-pass
requirements now have atomic `follow-up-of=W6636` ledger Work and canonical
dossiers:

- W32382 — local OCI negative and race endings,
  `work/records/2026/08/finding-v12-local-oci-negative-race-endings/`;
- W32385 — exact ended-runtime adoption before lane reuse,
  `work/records/2026/08/finding-v12-local-oci-ended-runtime-adoption/`; and
- W32391 — Podman lifecycle certification,
  `work/records/2026/08/finding-v12-podman-lifecycle-certification/`.

W32391 requires a real Podman engine. The reviewer creator is not a handler of
its implementer Route and therefore could not park it; the Route was notified
to set the recorded deferral before pickup.
