# W275774 — bounded inventory of the tree's existing test breakage

Review 2026-09-26T19-53-28Z: "Catalog failures and custody-double failures need bounded
inventory and relevant focused repair before child acceptance, within existing path
ownership", and "two samples cannot classify the other failures as pre-existing".

This is that inventory. It is bounded by CAUSE rather than by count: every family below
was reduced to the one thing that produces it, measured by running the owning module
focused -- no broad discovery was repeated.

## A. The custody double family — ONE cause, REPAIRED

`custody._accountable` requires the normalize act's answer to carry the `submission` it
normalized under. Four test files define a `normalize_directory` double that predates
that requirement, so every ending they drive refuses for want of an accountable act
rather than for the reason its case is about. `tests/manager/test_intake.py`'s custodian
already answers it; the repair is that member, spelled the same way.

| module | before | after |
|---|---|---|
| `tests/manager/test_refused_session_cleanup.py` | 15 errors | **35 tests, all pass** |
| `tests/tools/test_dogfood_operator.py` | 34 | **359 tests, 1 error** (see D) |
| `tests/job_manager/test_recovery.py` | 21 (custody) | 21, NEW cause exposed (see D) |
| `tests/manager/test_boundary_inventory.py` | double present, unused by its failures | see B |

Genuine coverage is retained: no assertion was weakened, no case removed. The only
expectation change is that a happy-path custody double now answers the member the
production boundary requires.

## B. The catalog families — NOT one cause, and mostly NOT this Work's paths

**`tests/manager/test_boundary_inventory.py`: 49 failures, and 48 share ONE cause which
IS MINE.**

    adapter.stop crosses at attempts.py:_order_quiescence and at
    intake.py:reclaim_expired_resource; a capability with two crossings has two owners

`reclaim_expired_resource` is this Work's own code, and the rule it breaks is the
inventory's: one capability, one crossing owner. The reclaim's stop is deliberately NOT
the cancellation's stop -- it fences nothing and carries no receipt, which is why the
receipt-bound destroy was wrong for it -- so the two crossings are two acts sharing one
verb name. THREE SHAPES ARE POSSIBLE and I am not choosing one unreviewed:

  1. the reclaim gets its OWN verb (`stop_expired`), which makes the two acts two
     capabilities and matches why they differ; it changes `oci.py`, the tool's
     `_ReclaimAdapter` and their cases;
  2. the reclaim routes through the existing owner, which would drag the authority fence
     into a sweep -- rejected on its face, recorded so the option is not re-proposed;
  3. the catalog declares a second owner, if the rule admits one.

The remaining 1 is a `4 != 3` count assertion, not yet traced.

**`tests/manager/test_dependencies.py`: 73 failures, a LONG TAIL and no single cause.**
Undeclared public operands, by name and count: `jobs` 5, `authority` 4,
`provider_context` 3, `ordinal` 3, `job_execution` 3, `context_id` 3, `under` 2,
`settlement` 2, `run_id` 2, `launcher` 2, `workspace_storage` 1, and a tail of singles.
Plus the import rule (`uuid` 6, `urllib` 3) and one packaging assertion
(`base_library.zip`).

THIS FAMILY IS LARGELY OUTSIDE THIS WORK'S PATHS: the operand names belong to jobs,
provider context, the launcher and the authority, and this claim's own token operands
(`domain`, `generation`, `which`, `evidence`) are already IN the allowed set. So it is
tree-wide catalog drift rather than this Work's WIP, and repairing it inside Child A
would be editing declarations for paths Child A does not own. Itemization by owning path
is the next step and is not a token-lifecycle change.

## C. What this inventory does NOT claim

It does not claim the 745 totals from the broad run are accounted for. It accounts for the
four modules named above plus the two catalog modules: that is the bounded slice with a
stated cause each. The rest of that run is unclassified and is not called pre-existing
here.

## D. Open, with exact causes

1. `tests/job_manager/test_recovery.py`, 21 errors, cause now visible after A:

       attempt '...'s start submission has not returned to the manager that made it;
       a reservation is not given back on somebody else's observation of the runtime

   The fixture fabricates a running attempt with raw SQL (`UPDATE attempts SET
   runtime_id = ?, execution_runtime = 'running'`) and therefore journals no start, so
   W266336's submission-returned gate in `_settle_recordless_cleanup` refuses. The gate
   is another Work's product rule and the fixture is not this dossier's; the repair is
   either a journalled start in that fixture or that Work's own call.
2. `tests/tools/test_dogfood_operator.py`, 1 error: `KeyError: 'store'` in
   `TheCredentialIsMaterializedAfterActivationAndNotBefore.test_the_factory_materializes_exactly_once_through_the_owned_home`.
   Not traced; not in any path this claim edits.
3. B above, both modules.

## E. Update, 2026-09-26 claim 278601 — inventory B's own cause, repaired

Review 20:07:17Z authorized the first of the three shapes: the receipt-free expiry stop
gets its OWN narrow capability with one crossing owner, preserving the cancellation
stop's semantics. Implemented as `stop_expired` across the pinned paths:

* `src/baton_v12/worker_manager/oci.py` — `stop` and `stop_expired` are two named
  capabilities over ONE core (`_stopped`), so the exact identity, the operation riding
  with it, the engine vector and the timeout are the same BY CONSTRUCTION rather than by
  a second implementation that agrees until one is edited.
* `src/baton_v12/worker_manager/intake.py` — `reclaim_expired_resource` owns
  `stop_expired` at its capability boundary and crosses it. No authority fence was
  dragged into the sweep; nothing about the cancellation path changed.
* `v12/python/tools/job_manager.py` — `_ReclaimAdapter.stop_expired`, and `_Reclaiming`
  forwards that name.
* Dossier selector `test_expiry_reclaim.py` — the reclaim doubles offer the new verb;
  the negative cases (refused stop, no-transaction-during-engine, the in-flight
  observations) are unchanged and still pass.

**Measured: `tests/manager/test_boundary_inventory.py` 49 failures -> 28, and the
two-owner cause is gone.** The new capability is discovered by the inventory as its own
receiving entry rather than needing a waiver.

### What the remaining 28 are, attributed rather than waived

| cases | what | attribution |
|---|---|---|
| 15 `test_no_declared_owner_is_stale` | declared owners naming entries the tree no longer presents | **13 are `review_cycles.py:attach_review`** (answer.authority_uuid/participant/generation …) — another Work's path; **2 are `oci.py:OciAdapter.start` (`labels.runtime_attempt_id`) and `OciAdapter.observe` (`document.Running`)** — THIS Work's two-act launch and observation changes, so these two are mine |
| 5 `test_every_declared_probe_reaches_its_named_boundary` | probes whose refusal now arrives at a different boundary; three refuse at "no configured workspace store" before reaching their named operand | workspace-storage configuration order; `workspaces.py` declarations |
| 3 `test_no_entry_is_owned_twice` | "2 not less than or equal to 1: owned more than once" | not yet traced to a pair; NOT `adapter.stop`, which this claim removed |
| 1 each: `test_the_missing_probe_check_can_actually_fail`, `test_private_lane_writer_provenance`, `test_every_receiving_entry_has_an_owning_validator`, `test_every_owned_entry_has_exactly_one_probe`, `test_every_boundary_call_belongs_to_an_entry_or_is_declared`, plus the `4 != 3` count | list diffs over `attempts.py:_attempts`, `attempts.py:_decide`, `attempts.py:_committed_record` | mixed; needs itemization |

`tests/manager/test_dependencies.py` is unchanged at 73 and still the long tail of section
B: `stop_expired` appears in that suite's universe rather than among its missing entries,
so this claim added no drift there.

NOTHING HERE IS CALLED WAIVED. The two `oci.py` stale owners are this Work's to repair and
are listed as such; `review_cycles.py`'s thirteen belong to the Work that owns that path
and need coordinating rather than an opportunistic edit from inside Child A.

## F. Update, 2026-09-26 claim 278715 — the two owned OCI declarations

### F1. `OciAdapter.start` / `labels.runtime_attempt_id` — WITHDRAWN, and re-pointing it was the wrong repair

The two-act launch gave `start` a named `request` document, so the member is discovered as
`request.labels.runtime_attempt_id`. I first RE-POINTED the exception to that path, and
measured the result: stale owners fell 15 -> 14 and owned-twice ROSE 3 -> 4, because that
path is already owned by the envelope's own `request.labels` validation against
`documents.RUNTIME_LABELS`. An exception for a member the tree already owns is the opposite
defect, so the exception is withdrawn instead.

THAT IS NOT DELETION TO SILENCE A PROBE. What the exception stated -- that the comparison
against the delivery's attempt is a semantic rule over two already-owned values -- is still
true, and its witness `test_one_delivery_belongs_to_one_attempt` stays where it is and
passes (measured, 1 test). The member's own validation is now discovered rather than
declared, which is what the inventory prefers.

**Measured: boundary inventory 28 -> 27, stale owners 15 -> 14, owned-twice back to 3.**

### F2. `OciAdapter.observe` / `document.Running` — diagnosed, NOT repairable by re-pointing

The declaration says this read cannot refuse (`is True` / `is False`, anything else
`uncertain`), and the code comment at the read says the same. The read still exists at that
crossing. What no longer exists is the PATH: the member now lives under the engine's nested
`State` record, and the discovery does not chain nested member reads. TWO EXPERIMENTS,
both reverted:

1. `state["Running"] if "Running" in state else None` instead of `state.get("Running")`:
   the entry does NOT appear -- `('caller','oci.py:OciAdapter.observe','document.Running')`
   still absent, and no entry anywhere mentions `Running`.
2. Also reading the nested record literally, `document["State"] if "State" in document
   else None` instead of `_one_of(document, ("State",), ...)`: still absent.

So there is no live key to re-point the declaration to, and deleting it would remove the
record that this read is deliberately unrefusable -- the thing the review forbids. The
repair belongs to whichever of the two rules is wrong: either the discovery chains nested
member reads (the inventory suite's own rule, and the same "invisible to the catalog"
failure class its own comments name), or the read is restructured so the member is
discovered at the crossing that owns it -- which would mean giving up `_one_of`'s
alternative-spelling tolerance for the engine's `State` record, a product behaviour change
made to satisfy a catalog key. I am not making that trade unreviewed.

### F3. Newly measured: `tests/manager/test_oci.py`, 4 failures

Not previously in this inventory; measured this claim while verifying the witness case.

1. `OneAttemptsEndingNeverRemovesAnothersCredential.test_the_matching_attempt_still_ends`:
   `TypeError: <lambda>() got an unexpected keyword argument 'seconds'`. A double for the
   observe seam that predates its `seconds` operand -- the port-budget wrapper. Fixture
   drift against a product operand, and the operand is this campaign's.
2. Three failures in that module's `setUp` (line 156) asserting over a provider lifecycle
   answer of `'not-asked'`. Not traced further this claim.

NONE of the four mentions `stop` or `stop_expired`: the expiry-capability split added a
method and a delegation and changed no behaviour, and this module's failures are unrelated
to it.

## G. Update, 2026-09-26 claim 278807 — F2's provenance, traced to the bottom

Review 20:35:57Z authorized a bounded nested-member provenance correction in the owned
`test_boundary_inventory.py`, naming `_member_origins`/`_source`/helper-return propagation
as starting points. Tracing them shows the declaration is stale in its ROLE as well as its
path, which changes what the correction has to be:

1. `_helper_returns()` DOES resolve the pass-through: `oci.py:_one_of` is recorded as
   `('caller:document', ('document', 'names', 'what'), ())`. So helper-return propagation
   is not the missing link.
2. `_origins` for `oci.py:OciAdapter.observe` binds ONLY its two parameters --
   `runtime_id` and `seconds`. Neither `document` nor `state` is tracked.
3. And the reason is what `observe` actually reads: `answer = self.run(inspect_vector(...))`
   -- the engine's answer is an INJECTED capability answer, and the engine's own members
   are owned at `oci.py:EnginePort.__call__` as `run.status`, `run.stdout`, `run.stderr`.
   The inspection `document` is parsed out of that stdout stream, so `Running` is a member
   of a JSON document decoded from an injected stream.

THE INVENTORY HAS NO ENTRY CLASS FOR THAT TODAY. No `injected` entry anywhere mentions
`Running`, and there is no `caller:` origin to hang it on, so the declared
`("caller", "oci.py:OciAdapter.observe", "document.Running")` names a role the value no
longer has. Nested-member chaining alone would not produce it either: the chain has to
start from a provenance the discovery does not yet assign.

So the bounded correction is: give a document decoded from an injected stream its own
provenance -- an `injected` origin carried from the stream member it was parsed out of --
and then declare the member at the path that discovery reports. That is a discovery-rule
addition rather than a re-pointed key, it is bigger than the two experiments in F2, and it
is what the next claim should do with a positive and a negative regression beside it.

UNTIL THEN THE DECLARATION STAYS. It records that this read deliberately cannot refuse,
its witness `test_an_unrecognised_running_member_is_uncertain_and_never_absent` passes, and
the product observation behaviour is unchanged -- which is the review's own instruction.

## H. Update, 2026-09-27 claim 280339 — the abandoned-correction families, and one newly seen file

### H1. `tests/job_manager/test_recovery.py` (21 errors) — REPAIRED, two causes

Cause 1, the scheduled one: two synthetic `execution_runtime = 'running'` updates could not
satisfy W266336's `start_submission_returned`, which only `request_runtime_start` writes.
Cause 2, found by measuring cause 1 alone: W257624's `restore_abandoned_correction` refuses
without a launcher and a cessation observer. 21 errors to 0; 56 PASS 1.904s.

### H2. `tests/manager/test_review_cycles.py` (36 errors) — the same two causes, plus a third

Same two causes, same repairs: 36 errors to 26 errors plus 3 failures after cause 1, then to
7 failures plus 1 error after cause 2. The residual 8 are a THIRD class -- assertions that
encode the pre-W257624 serialization shape (effect inside the transaction, writer revoked only
on success, overlapping caller replays rather than holds) which that Work explicitly withdrew.
Reported unchanged: repairing them means re-specifying another Work's accepted behaviour.

### H3. `tests/tools/test_stage_execution.py` (8 errors) — REPAIRED

`TheIntegrationStageConsumesTheAcceptedPort.deployment()` held `authority=object()` where the
branch decision reads `.proposal` and `.canonical_target`, and `reconciles` behind it. Both
answers agree and `reconciles` is the production rule over this held configuration, so the
DIRECT branch this fixture configures is the one selected. 8 errors to 0; 26 failures unchanged.

### H4. NEW, pre-existing, not previously inventoried: `tests/integration/test_driver.py`, 2 errors

`TheOrdinaryCommandTraversesPublicAdmission.test_actual_failed_and_unrun_completion_cannot_publish_policy_receipts_or_admit`,
both subTests. On the `unable` branch `_OrdinaryAdmissionWorld` authorizes cleanup while the
line writer is still active, so `discard_execution_roots` refuses. Unrelated to claim 280339's
edits by construction: that world is composed from tests.job_manager.test_review_driver and
tests.manager.test_claude_agent, and neither edited module is reachable on that path.
Not this Work's path; recorded, not touched.

### H5. A false product comment, recorded for its owner

src/baton_v12/worker_manager/review_cycles.py around 3210-3231 claims the runner "OPERAND IS
PASSED ONLY WHEN THERE IS ONE" and that no accepted fixture has to grow a parameter, directly
above `if True:` and an unconditional `runner=`. Both sentences are false and the second is
the exact reason the fixtures above raised `TypeError`. W257624's, not edited here.

## I. Update, 2026-09-27 claim 280572 — the ungoverned ending, and what it was really breaking

### I1. `tests/tools/test_stage_execution.py`, 26 failures — REPAIRED, and the cause was this Work's

One symptom (implementation stage `exceptional`, never `waiting`), one root cause: my governed
start acquires a workspace token and `review_driver`'s two endings called `authorize_cleanup`
with no governance, so nothing ever returned it and the correction round was refused by its
own predecessor's generation. Threaded `govern` through the driver's endings and wired it in
`tools/stage_execution.end`. Two masked layers behind it: the stage suite's own restore calls
needed W257624's accountable pair, and `declare_abandoned` composed an ungoverned operator
declaration. 424 PASS, zero failures, zero errors.

### I2. `tests/manager/test_claude_context.py`, 28 failures — REPAIRED, same cause plus one of mine

A/B against the pre-turn baseline: 28 failures without the governance repair, 1 error with it.
That last error was the two-act launch: the case selected launching vectors by `run`, and a
governed launch composes `create` then `start`. Now derived from `oci.ACTIVATIONS`. 81 PASS.
This suite was never inventoried; it is not a new break, it is an old one now attributed.

### I3. `tests/manager/test_review_cycles.py`, 8 residuals — ALIGNED under H2's superseded reading

H2 said repairing these necessarily re-specifies another Work. The reviewer superseded that
with W257624's own accepted reviews as the authority, and the alignment is now done: three
revocation-timing expectations, two retries through the supported settlement, two overlap
refusals asserted exactly, one negative asserted as refusal-plus-state, and one stale
injection point moved to `_admitted_execution` with its no-effect assertion kept. 162 PASS.

### I4. Still pre-existing, A/B-confirmed in BOTH arms and untouched

`test_execution_limits` 4 failures, `test_parallel_runner` 1 error, `test_boundary_inventory`
26 failures (B/D family), `tests/integration/test_driver.py` 2 errors (H4). The first two are
newly attributed as pre-existing and not yet diagnosed.
