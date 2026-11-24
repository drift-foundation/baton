# W385695 — correction packet for C2 and C5 (review 2026-11-24T03-03-48Z, M385935/M385937)

**For independent review. Not accepted, not imported, not qualified.** One batch: the C2 late-completion defect and the five C5 preparation items. C1, C3 and C4 are unchanged.
Author: baton.prompt (K), owner-selected interactive continuation, no claim.
No host import, protected Git mutation, image build, engine or container operation, live model call or credential read. No protected-tree file was edited.

No new decision is raised. One limit of the Option A setup is stated in section 3.4.

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| This candidate | `candidate-manifest.json`; sha256 in `packet.sha256` and in the Baton message |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `6d6a4fc8` (disposable) |
| Paths | 50 over base; 4 changed since the reviewed candidate `0a9bc8a9` |
| Reviewed candidate (preserved, untouched) | manifest `0a9bc8a9…`, `evidence/correction-K-385929/` |

`delta-from-reviewed.patch` is over `0a9bc8a9` (scratch head `2d29513c`) and is the delta to read. The source delta is four files: `v12/worker/bounded_command.py`, `v12/worker/claude_agent.py`, `v12/python/DEPLOYMENT.md` and the test module. The rest of this round is qualification preparation, which is in the packet and not in the candidate.
Application proof as before: `candidate.patch` applied to a fresh archive of the base; every path compared by sha256 and mode.

## 2. C2 — the bound dominates a late completion

**The defect.** `supervise` believed a child's exit status before it looked at the clock, so a command that was still running when its bound passed and then exited 0 was recorded `exited`, status 0.

**The correction** (`bounded_command.py`):

- When the child is seen ended, the clock is read first. If the bound has passed, the outcome is `timed-out`, no status is published and the supervisor answers 124. Only an ending observed inside the bound is `exited`.
- The allowance is read again immediately before the launch. A bound that ran out while the supervisor adopted descendants and left its start record starts no child.

**The adapter applies its own clock too** (`claude_agent.py`), so it does not rest on the supervisor's word alone: a required check whose supervisor answered after the invocation deadline is `timed-out`; a provider whose supervisor answered after it is a timed-out turn.

| Required by the review | Case (class `TheReviewersRequiredVerificationIsSupervisedAndBounded`) |
| --- | --- |
| completion after the bound | `test_a_command_that_ends_after_its_bound_is_a_timeout_not_a_success`: real child released only after a controlled clock crosses the bound, at exactly the bound and past it |
| completion before the bound | `test_a_command_that_ends_inside_its_bound_is_its_own_status` |
| launch and setup transition | `test_a_bound_that_expires_while_the_supervisor_sets_up_runs_nothing` (no fork) |
| required-check interpretation | `test_a_supervisor_that_answers_after_the_deadline_is_not_a_pass` |
| provider interpretation | `test_a_provider_whose_supervisor_answers_late_is_a_timeout` |

The reviewer's `probe-late-exit.py` and all four cases of `probe-delta.py` pass unmodified. The 900-second per-command and 3600-second invocation contract, the invocation origin, the ending grace and descendant cleanup are unchanged.

**Documentation corrected.** `DEPLOYMENT.md` and the supervisor's own header no longer suggest that ledger tampering is detected. They now say: not a security boundary against the reviewer; a killed supervisor is counted as unfinished; a command that rewrites the records is not detected; the provider's supervisor, the invocation deadline and container cessation are what still bound it.

Unchanged qualifications: same-user isolation is not claimed, and tools other than the shell tool were not tested for process creation.

## 3. C5 — qualification preparation

Three files in the packet: `qualify-w385695.sh` (revision 3), `option-a-setup.sh` (new) and `cli-in-image-driver.py` (new). **No engine phase was executed.**

### 3.1 Installed layout (item 1)

The authority store is now `<destination>/db/authority.sqlite3`. The script also checks every path it derives against the reviewed tree's own `tools.instance.layout` and refuses on a mismatch. My dry-run doubles had invented the same wrong directory; they now use the real layout and run the script's check against the real `layout()`.

### 3.2 Pause cleanup and stack ownership (item 2)

- The watcher writes a pause **intent** before asking the engine and an **acknowledgment** after. On any ending the script first stops and waits for the watcher, then reconciles from both records: a container found paused is unpaused, one not paused or gone is left alone.
- The stack is stopped only on proof. A live process in the stack's own records before the start means it is someone else's: the phase refuses and stops nothing. After the start, the run owns the stack only if a live record names a process that was not there before, whether the start command succeeded or failed.

### 3.3 Fixture image recipe (item 3)

The derivative now switches to root, removes and replaces only `/usr/local/bin/claude`, sets its mode, and restores the exact user the provider image declares. After the build the script asserts: same user, the label, `/opt/baton` byte-identical to the provider image, the scripted program is what the adapter's `PATH` resolves, and the runtime user cannot write it. This was not built; the earlier failure and this fix are both read from the recipe.

### 3.4 Executable Option A setup (item 4)

`option-a-setup.sh` uses only the instance's supported verbs:

| Phase | What it runs |
| --- | --- |
| `workers` | `pool compose-worker` three times (implementation and review on the labelled fixture image, publication on this run's publication image), then the one-operand `bootstrap` repeat over the instance's own `install-inputs.json` with exactly those workers; reads the deployment back |
| `jobs` | `manager … create` twice under `baton.v12.job-template.implementation-review/1` |
| `failures` | starts the stack under the same ownership proof; waits until `settlement-preview` answers `eligible` for both producers; stops; `settle-stopped`, `settlement-remove`, `publication-inspect` for each; writes the environment file for `qualify-w385695.sh` |

**The argv were executed against the real commands.** `harness/setup/validate-option-a.py` takes the script's own argv for all six composing and creating steps and enters the real `pool.main`, `bootstrap.main` and `job_manager.main` with them, on an instance the accepted connected-creation fixture installs. Three workers compose, the repeat admits exactly them, and two servable Jobs are created. This found and fixed one real error: the publication role refuses `--verifier-layout`.

**The output ceiling is pinned.** An ordinary proposal is admitted under `role_contract.MAX_OUTPUT_BYTES`, 1048576 bytes; the recovery requires an original over that and inside the 100 MiB corrective declaration. The fixture writes 1048576 + 4096. The scripts hold that number to the reviewed tree, name the `/1` template explicitly, and `preflight` requires `output.exceeded` and `output.fits_corrective` from the product's own inspection.

**No live fallback.** `preflight` refuses, by worker id, any implementation or review worker that is not on the labelled fixture image, including this run's real provider image.

What remains the operator's, stated rather than filled in:

- **Installing the instance.** `just bootstrap INPUTS DESTINATION` with the operator's own instance selections (profiles, participants, digests, repositories). I did not author that document: its members are the instance's, and I could not execute an install here because it needs the bundle build.
- **Host facts** the setup takes as required environment with no defaults: workspace group, network name, a qualification-only credential registry and slot, task document, record and checkout, verifier-layout marker.
- The `failures` phase is proved only against scripted doubles (three scenarios, including producers that never stop and a refused removal). It needs containers to run for real.

### 3.5 The real CLI in the image, kept separate (item 5)

New phase `cli-in-image`. It runs the provider image's own pinned `claude` inside one container with **no network**, against the scripted endpoint on that container's loopback, with the image's `/opt/baton/bounded_command.py` as shell prefix. It requires the recipe's pinned version, the reviewed supervisor's hash, and a pass on ten checks (six commands answered, six start and finish records, bound timeouts, detached child ended, no survivor). Neither the supervisor self-check nor the fixture image covers this, and this phase does not use the fixture.

The driver is the same program inside or outside a container. I ran it **on the host** with the exact pinned binary and the final supervisor bytes: verdict pass (`harness/cli-prefix/driver-host-run.json`). A first run with a relative prefix path failed every command closed, which is retained. The in-container run is not executed and remains the open obligation.

### 3.6 Dry runs

| Harness | Result |
| --- | --- |
| `harness/qualify/scenario.sh`, 14 scenarios | as intended: other-instance containers never touched; decoy and wrong-image refused with no effect; lost pause reply and TERM mid-freeze both unpause the one container; pre-existing stack refused and left running; clean start failure stops nothing; partial start failure stops the run's own; live-provider selection refused |
| `harness/qualify/setup-scenario.sh`, 3 scenarios | as intended |
| `probe-qualification-r3.py` (the reviewer's probe adapted to the new script) | 4/4: layout equals `tools.instance.layout`; exact `finish` at the acknowledged-before-assigned cut unpauses; intent-only (lost reply) unpauses; not-paused or gone is left alone |

The reviewer's own `probe-qualification.py` asserts the old wrong path is present in the reviewed packet, so it cannot be rerun against a corrected script; the adapted probe asks the same questions.

## 4. Verification

Prepared interpreter, `just test-one`, disk-backed scratch, at the final head.

| Run | Result |
| --- | --- |
| Four required modules | 414/414 passed, 135.2 s |
| Eight modules affected by the worker change | 1083/1083 passed, 51.7 s |
| Reviewer probes, unmodified | `probe-late-exit.py` 1/1; `probe-delta.py` 4/4 |
| Adapted qualification probe | 4/4 |
| Setup argv through the real commands | 1/1 |
| Pinned CLI driver on the host | pass |

Not run: the 22-module affected set and `test_stage_execution` from the last round (no file they cover changed except `claude_agent.py`, whose module is in the eight), the registry classes (no registry file changed), the whole boundary inventory, scans, the `job_manager` group, `test_checkpoint_profiles`, any image, engine or container. The two inherited failures reported last round are unchanged and not rerun.

This round I did not rerun any reviewer probe that writes into its own evidence directory; `evidence/review-385934/` verifies against its recorded hashes.

One incident to disclose: a shell edit command of mine was cut short by a nested here-document, and the remaining lines ran as shell. They failed immediately (undefined functions, unwritable paths); no engine command ran and no file was written. I redid the edit from a file.

## 5. Affected images

Unchanged list. The provider image carries the changed `bounded_command.py` and `claude_agent.py`; the integration image carries the changed `claude_agent.py`.
