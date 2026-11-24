# W385695 checkpoint-2 continuation — K (M385897)

Author: baton.prompt (K, model Fable 5.2), owner-selected interactive
continuation, no claim. 2026-11-23.

**Disposition: candidate for independent exact-byte review. Not accepted, not
imported, and not "resume supported".** The four checkpoint-2 obligations
named in M385897 are implemented and exercised through real owners with only
the engine faked. Section 6 lists what is still unproved; two of those items
are ones a reviewer may reasonably hold checkpoint 2 open for.

No host import, protected Git mutation, image build, engine or container
operation, live provider call, credential read or instance change.

## 1. Identity

- Base: 6079ad78345aa87b7148db302d48fb9b1867f940.
- Started from the preserved manifest 531ddac1…53eef in
  `evidence/continuation-385885/`, verified (all 25 file hashes, both
  patches) and left unchanged.
- This candidate: `candidate-manifest.json` sha256 623ac725b8d31368ea5a268b7c719ec979e1d63052737b2ff2bdeb6e46680698.
  - `candidate.patch` (over base) sha256 8c6c1075d6ac5a5bcf7366bb701dc5df663dac8f0bae0beeffa70ca7b5d74d37 — 28 paths.
  - `delta.patch` (over the reconstruction of 531ddac1) sha256 bccd4cc65d417c091e07a407868b73c27ec6b8dd3faede7b7c8a130b493ef764 — 13 paths.
  - `candidate-files/` holds all 28 paths; per-file hashes, base hashes and
    previous-candidate hashes are in the manifest.
- Isolated disposable repository: `work/scratch/w385695-K-385897/repo`,
  built from `git archive 6079ad78` with no alternates; head 671ee3a3. It is
  not the only copy.
- The three historical dossier paths carried in 531ddac1's patch are not
  part of this candidate.

Paths changed since 531ddac1 (13):

| Path | New to the candidate's path set |
| --- | --- |
| `v12/worker/publication_entry.py` | new file |
| `v12/python/tools/publication_worker.py` | |
| `v12/python/tools/single_worker.py` | yes — shared with W385830 |
| `v12/python/tools/stage_execution.py` | yes — shared with W385830 |
| `v12/python/tools/fresh_attempt_ports.py` | |
| `v12/python/tools/publication_decision.py` | (comment only) |
| `v12/python/src/baton_v12/job_manager/publication_execution.py` | |
| `v12/python/src/baton_v12/job_manager/publication_recovery.py` | |
| `v12/python/src/baton_v12/job_manager/manager.py` | yes |
| `v12/python/src/baton_v12/job_manager/delegation.py` | yes |
| `v12/python/src/baton_v12/job_manager/projection.py` | |
| `v12/python/tests/job_manager/test_publication_recovery_execution.py` | |
| `v12/python/tests/tools/test_stage_execution.py` | yes |

## 2. What changed, against the four obligations

### 2.1 Confined deterministic publication with read-only input

- **The in-process host copy is gone.** `PublicationWriter` is removed, not
  kept beside the real path.
- **New worker entry** `v12/worker/publication_entry.py`: a
  `PublicationAgent` run by the unchanged `baton_worker`. It reads one
  pinned request (`publication.json`), copies the staged tree from the
  read-only source mount into its two declared outputs, and lets the ordinary
  worker measure and publish the completion envelope. No provider, no
  credential, no verifier.
- **The publication worker runs on the ordinary worker lifecycle.**
  `tools.publication_worker.PublicationStage` is a stage owner plugged into
  `single_worker.worker_operations(stage=…)`, as the implementation, review
  and managed-apply owners are. Offer, claim, activation, input root, launch
  document, workspace token, journalled runtime start and command are the
  accepted composition, unchanged.
- **Read-only delivery.** The mount commits the launch and delivers the
  staged root as the nominated source at `/input/source` — the one read-only
  bind the engine adapter composes. The original attempt's output is mounted
  nowhere.
- **No credential.** `single_worker` now requires a publication-role
  deployment to declare no credential slot, and composes no credential
  delivery for it. Every other role keeps the at-least-one-slot rule.

### 2.2 Interruptible absolute deadline and host cessation evidence

- **One absolute instant, bound once.** `prepare_launch` commits a durable
  intent carrying the deadline derived from the persisted stage admission.
  The pinned request carries that instant and no remaining number. A missing
  origin, an unplaceable or zone-less instant, or one not still ahead commits
  nothing and starts nothing; there is no default bound.
- **Worker side.** The copy is a child in its own process group. The
  supervisor recomputes the time left against the clock on every wait and at
  the instant ends the whole group (TERM, then KILL) and observes it empty.
  A run the bound ended is a typed fault with no envelope.
- **Host side.** `job_control`'s evaluation journals the expiry at the same
  bound and the ordinary cancellation pass orders the exact runtime to stop
  through the engine owner, whether or not the worker is still there.
- **Cessation is an observation.** `record_adoption` measures only after the
  Worker Manager recorded the runtime quiescent (or destroyed after a settled
  cleanup). `hand_off` now also requires the publishing runtime destroyed or
  its cleanup settled. A reached deadline, an answer or a stop order is
  never read as cessation.

### 2.3 Original held-session ending

- The owner command still holds a read-only Authority and no session. Its
  admission reserves the recovery and stops at the held assignment with a
  typed capability refusal.
- New `publication_recovery.end_prior_assignment` / `advance_endings`: the
  same cut, entered by the serving manager, which ends exactly the failed
  execution's assignment through the producer's own already-held session and
  the Authority's exact-expect transition, under the same operation identity
  and journalled record. It requires an approved decision and an existing
  admission reservation.
- `_ended_prior` now replays its committed record before asking the
  Authority. Without that, a re-entry after the ending committed composed
  disposition `none` and collided with the `ended` record.
- `stage_execution` hands the port a lookup over the producer sessions it
  already minted (`_held_producer_sessions`); it mints nothing.
- **Owner-visible behaviour:** the admission is now two steps when the
  producer still holds the Work — the first attempt reserves and is refused,
  the serving manager ends the assignment on its next tick, and the same
  admission repeated then admits.

### 2.4 Real runtime and token reconciliation

- The start is the Worker Manager's own journalled `runtime.start`, under
  the ordinary workspace governance. A lost start reply is reconciled by
  that owner against the engine's listing of the exact runtime labels.
- `publish` is now the pass's accounting of the one launch and never
  launches. A faulted or lost exchange, a runtime gone without a settled
  cleanup, or an uncertain runtime is journalled UNCERTAIN; nothing is
  recorded as published and `prepare_launch` refuses a second launch.
- `take_custody` no longer asks for a freeze or an intake; it binds the
  ordinary ending's records.
- The publication pass is wired into `manager.sweep` (`_publish`) and
  discovered through `operations.recovery_publication`.

### 2.5 Two defects found on the way

- `projection._RUNNING` had no publication entry: the first publication
  stage with a runtime would have raised `KeyError` out of the projection.
- `fresh_attempt_ports.publication_worker` answered the whole manifest
  digest as the Job identity. The worker lifecycle holds a Job to the
  Job-scoped projection and refuses the whole digest as a legacy identity,
  so no recovery Job could have been served. Invisible while publication
  never went through the lifecycle.

## 3. What the safety delta of 531ddac1 became

M385897 asked that no-repeat intent, staging locks and original custody be
preserved. Stated exactly, because one of them changed form:

| 531ddac1 | Now |
| --- | --- |
| Per-recovery host lock around staging and adoption | Kept. `prepare_launch`, `publish` and `stage_input` take it |
| Interrupted staging preserved | Kept unchanged |
| Intent without result refuses a second writer call | **Changed form.** There is no writer call to repeat. The intent precedes the runtime start; the no-second-start guarantee is the Worker Manager's journalled start plus reconciliation by exact labels. A standing intent with a runtime still running is "in flight", not an uncertainty |
| No default producer-session minting | Kept; the serving lookup answers only sessions already held |
| Real owner admission receipt in the fixture | Kept and extended: no receipt, runtime observation or token state is written by any case |

## 4. Verification

Prepared interpreter via `just`; disk-backed scratch under
`work/scratch/w385695-K-385897/`. Logs in `logs/`. Final source 671ee3a3.

| Run | Result | Time |
| --- | --- | --- |
| Baseline, 531ddac1 reconstruction, four required modules | 307/307 | 16.3 s |
| **Required four modules, final source** (`final-required.log`) | **326/326**, 0 failures, errors, skips | 28.0 s |
| **Whole `tests.tools.test_stage_execution`** (`final-stage-execution.log`) | **514/514** | 357.3 s |
| **`just test-group job_manager`** (`final-group-job_manager.log`) | 2228 collected: 2225 passed, 3 failed, 0 errors, 0 skips, 0 unaccounted | 34.1 s wall |
| Those 3 under a short scratch path (`short-path-three.log`) | 103/103 in their two modules | 1.2 s |
| Wider affected set (`final-affected.log`): test_single_worker, test_dependencies, test_delegation, test_job_control, test_sweep, test_status, test_scheduling, test_managed_apply | 589 run: 568 passed, 21 errors | 101.9 s |

- **The 3 group failures** are the long-path message cases
  (test_store_readonly ×1, test_tool ×2): the refusal text truncates a long
  scratch path. They pass under `/var/tmp/k695`.
- **The 21 errors** are all in `tests.tools.test_managed_apply`
  (`KeyError: 'stage_id'` in `projection.gates_of`). The same module gives
  the same 21 errors of 32 on the base (6079ad78) and on 531ddac1, checked in
  two temporary worktrees. They predate this work and I did not touch them.
- **Worker supervisor probe** (`probe_worker.py`, real processes): ordinary
  copy; symlink refused; existing destination refused; a hung child with a
  TERM-ignoring grandchild ended at the instant with the group observed
  empty (3.0 s for a 1 s bound); past and unplaceable deadlines refused.
- One intermediate run is worth knowing about: the first full
  stage-execution run failed 7 of 514 because I had added the publication
  role to `ROLES`, a name other preflights and tests mean "the three a Job
  needs" by. Corrected (publication is a separate optional configured role);
  the rerun above is on the corrected source.

### What the execution suite now exercises (109 cases)

Real Authority, real stores, real `manager.sweep`, real offer / claim /
activation, real input root, launch document and workspace-governed start,
real exchange, the real worker entry with a real supervised child, the
ordinary freeze / intake / retention / cleanup. Faked: the engine callable
and its custody helper, the host's record of the original attempt, the
deployment binding, the instance guard, the Git consumer's engine. Where a
case needs an engine that will not stop, loses a reply or cannot be reached,
it interposes at the engine.

Named behaviours: read-only `/input/source` and the original mounted
nowhere; zero provider and verifier counts from the worker's envelope;
worker lying about a count denied with nothing frozen; output changed after
the answer refused on the manager's own measurement; tampered staged tree
not published by the worker; oversized provenance refused on measurement;
runtime that will not stop → nothing measured or frozen; hung adoption
ended at the instant, no surviving process; worker past its deadline
publishes nothing; request without a placeable deadline refused (worker and
host); manager death after the engine started the container → reattached,
one start; death between intent and start → same intent, one start; runtime
removed underneath the manager → uncertain, no relaunch; engine unreachable
→ not read as ended; cancellation before launch and in flight; host stop at
the absolute bound; reached bound not read as cessation; serving-side
ending then replayed admission; and one ticks-only case that goes from the
held assignment to exactly one review offer with no act called by hand.

### Existing tests changed

All in `test_publication_recovery_execution.py`, because they were written
against the removed writer:

- Removed doubles: `PublicationCustodian`, `LostWriter`, and the fixture
  methods that wrote runtime observations (`quiescent`, `settle_ending`)
  or hand-issued the claim (`claim_publication`, `admit_stage`).
- 25 cases rewritten to assert the same rule through the real runtime; the
  reviewer should read each against the rule it previously asserted. Renamed
  where the old name described the writer.
- Expectation changes of substance: a standing intent is no longer an
  uncertainty by itself; custody no longer freezes; the recovery Job's input
  identity is the Job-scoped projection; the pass performs
  stage / account / custody / hand-off and never launches.
- The suite takes the pass off the sweep by default so a case can stand
  between two acts; cases about the sweep doing it all call `serving()`.

## 5. Decisions of mine a reviewer should check

- Worker faults use the exchange's closed code vocabulary (`input`,
  `agent`); I did not widen it. A deadline-ended run and a failed copy are
  both `agent` and are told apart only by message.
- The pass's acts are not added to the sweep report, following the standing
  rule the verification pass states.
- `end_prior_assignment` requires the admission's reservation, so nothing
  is ended for a decision nobody tried to admit.
- The publication role is configured through `WORKER_ROLES`; `ROLES` is
  unchanged.
- The worker compares its own clock with the delivered instant. In a
  container on the same host that is the host's clock; nothing here proves
  it for another arrangement.

## 6. Not done, or not proved

1. **No worker image and no container run.** There is no image recipe that
   carries `publication_entry.py`, and nothing was built or run under an
   engine. Read-only enforcement is shown as the composed mount vector and
   host permissions, not as a kernel-enforced mount.
2. **The pooled composition is configuration-tested only.**
   `stage_execution.operations_from`'s new publication branch (instance
   identity, host ports, session lookup, seam on the pooled object) is not
   executed by any test. It needs a bootstrapped instance that carries a
   publication worker, and no installer produces one: `pool compose-worker`
   has no publication role. What is proved end to end is
   `publication_operations` over real owners.
3. **Per-Job binding of a pooled publication worker** (one installed worker
   serving recoveries of different Works) was not examined.
4. **After an uncertain hold** the stopped container's removal and token
   return are left to the existing reclaim and operator paths; not exercised
   here. Whether an owner item is delivered for a held recovery was not
   examined.
5. **Token return** on the successful path happens inside the ordinary
   `authorize_cleanup`; no case asserts the token record itself.
6. **Installed owner commands** (`publication-resume`, `publication-status`)
   and the review binding are checkpoint 3 and untouched.

Items 1 and 2 are the ones I would not want read as delivered.

## 7. Continuation

If review returns corrections: the repository above, head 671ee3a3; rerun
the four required modules and the whole stage-execution module. Shared-file
note for W385830: `single_worker.py` and `stage_execution.py` are changed
here and its N1/N2 work builds on these bytes once they are accepted.
