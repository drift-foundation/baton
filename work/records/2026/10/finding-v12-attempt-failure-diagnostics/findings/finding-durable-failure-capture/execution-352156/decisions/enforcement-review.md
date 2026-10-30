# Independent review — accepted bounded prerequisite candidate

Reviewer baton.rvpc, claim334000. Accept `candidate-333964-final/` only, manifest SHA256 `60bcecee17f0ff96827f16203e9eedcde01b02634c441c3d646881c1bb29bfab`, base `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`. This supersedes the changes-requested disposition of review-2026-10-19T17-18-01Z.md for this corrected candidate; historical candidate333743 and its counterexamples remain valid history. The packaging draft candidate333964 is not the approved artifact.

## R1 resolution and acceptance

Reviewed the correction against the previous code and four counterexamples. `attempts._order_quiescence` now resolves this execution/start-operation's token-bound container after `request_cancellation` obtains the Authority fence. It refuses conflicting identities, does not invent attachment, and retains unresolved-launch uncertainty. `Lane.tick` requests cancellation even without a known identity, then revisits a subsequently bound or still-running effect under the same cancellation identity. Positive observed quiescence suppresses needless repeats; acknowledgement alone does not. No premature token revoke, return or renewal is added.

The expanded tests exercise actual StageExecution/_SingleWorker/request_cancellation composition with controlled allocation/workspace/external boundaries and real control/token contracts. They cover deadline/operator/recovery pre-attachment cancellation, late binding and later activation, refused Authority fence, failed stop, unavailable engine, identity disagreement and acknowledgement-only retry. Each stop checks prior Authority cancellation and absence of a control transaction. Together with the prior outer-process blocked-sweep, expiry, restart, once-only admission and retained-output evidence, this establishes the bounded prerequisite under the stated local process/engine scheduling assumptions.

Independent verification reconstructed a fresh source at `/tmp/w333735-review-334000-fzlyv0qc`, verified all18 manifest members, all456 source-manifest members, all six proposed candidate bytes and the four existing paths' base hashes against read-only Git history. Re-ran the submitted focused selection:72 tests PASS,2.992978504 seconds measured wall time,45-second timeout (unittest reports2.641 seconds). Exact command, result and output: `evidence/review-334000/verification.json` and `focused.log`. Previous reviewer verification3.246114866 seconds remains separately recorded; total measured review subprocess verification for these two passes6.239093370 seconds. Implementation reports28.000166608 seconds in its retained SPENDING.json; these are not CPU totals or bounds on review/edit time.

## Exact path and test scope

Approval binds CANDIDATE.json's complete base/candidate SHA256 inventory and ordinary0644 import modes for these six paths under `v12/python/`:

- `src/baton_v12/worker_manager/intake.py`
- `src/baton_v12/worker_manager/attempts.py`
- `tools/authoring_enforcement.py` (new)
- `tests/manager/test_authoring_enforcement.py` (new)
- `tests/manager/test_attempts.py` (existing test changed)
- `tests/job_manager/test_tool.py` (existing test changed)

The existing test_attempts change replaces the inaccurate “nothing to stop” explanation with unresolved-launch uncertainty while preserving no-effect assertions. The existing test_tool change requires one stop/removal on positive exact-absence replay while retaining exactly-one-return and no-new-start assertions. Both match accepted behavior; standing test authority applies. The new authoring suite now requires correlated retry when acknowledgement leaves the runtime running. No genuine cessation or unknown-hold obligation is weakened. Custody read-only modes are not import modes.

## Delivery boundary

This is independent acceptance of the isolated candidate and deterministic enforcement prerequisite, not shared-tree import, owner Git acceptance, deployment, live engine/provider proof, pilot execution or acceptance of production renewal/diagnostics. No actual engine/provider operation or Git mutation occurred. Physical cessation cannot be guaranteed when engine control is unavailable; held outcomes, unsettled activation and retained evidence remain required. README accurately states these limits and the replacement invocation/source pins. Fresh execution packets must bind all accepted production bytes and retain the historical supervisor pins; old execution333532 remains forbidden.

Owner M333721's temporary direct isolated implementation/verification exception expires at this independent acceptance. Production renewal and diagnostics must return to the separately reviewed/selected v12 execution workflow. Pass accepted delivery to baton.decide for human-plus-agent integration and owner disposition; do not silently close dependency gates or import files. The six-path proposal needs current target/base/overlap checks before integration, especially intake.py shared with later diagnostics. Human Git checkpoint is due after accepted import; suggested message: `fix(v12): enforce isolated authoring deadlines and expiry`. Agents do not stage or commit. W325959 remains the integrated acceptance consumer; one coupled prerequisite outcome is complete and no further decomposition is needed here.
