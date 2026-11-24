# W385695 — correction packet for C2–C5 (review 2026-11-24T01-52-00Z, M385927/M385929)

**For independent review. Not accepted, not imported, not qualified.** One batch: C2, C3, C4 and the C5 preparation, with C1 preserved.
Author: baton.prompt (K), owner-selected interactive continuation, no claim.
No host import, protected Git mutation, image build, engine or container operation, live model call or credential read. No protected-tree file was edited.

**C2 feasibility: there is no capability blocker.** The pinned provider CLI (2.1.247) hands every shell-tool command to a configured prefix program, and that is an enforcement point the adapter owns. Section 2 has the evidence. One decision is raised in section 7; it concerns the C5 fixture, not C2.

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| This candidate | `candidate-manifest.json`; sha256 in `packet.sha256` and in the Baton message |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `2d29513c` (disposable) |
| Paths | 50 over base; 11 changed since the reviewed candidate `9475646d` |
| Reviewed candidate (preserved, untouched) | manifest `9475646d…`, `evidence/correction-K-385922/` |

`candidate.patch` is over the base. **`delta-from-reviewed.patch` is over `9475646d`** (scratch head `58d452ff`) and is the delta this round needs read.
Application proof: `candidate.patch` applied with `git apply` to a fresh archive of the base in an isolated directory; every path compared by sha256 with `candidate-files/`; no other path differs.

Four paths are new to the set: `v12/worker/bounded_command.py` (new file, mode 100755; `candidate-files/` keeps the mode), `v12/python/tools/single_worker.py`, `v12/python/src/baton_v12/worker_manager/intake.py`, `v12/python/tests/tools/test_parallel_runner.py`. `v12/worker/Dockerfile.claude` now copies the new file, so **the provider image's recipe changed**, not only its worker bytes.

## 2. C2 — each command bounded, one deadline, descendants accounted for

### 2.1 The mechanism, and how it was established

`CLAUDE_CODE_SHELL_PREFIX` is an environment setting of the pinned CLI. I ran the exact pinned binary (`@anthropic-ai/claude-code-linux-x64@2.1.247`, sha256 in `harness/cli-prefix/IDENTITY.txt`) on this host against a local scripted HTTP endpoint that answers with fixed tool calls. No model, no credential, no container, non-essential traffic disabled. Observed:

- the CLI executes the prefix with **exactly one argument: the whole command string**;
- every shell-tool command goes through it: foreground, `run_in_background`, and a command the CLI itself moves to the background when its own window passes;
- a prefix that cannot be executed makes the command **fail** (exit 127); it is not run without the prefix;
- the prefix must be one executable path: a prefix with arguments is not split.

With the candidate's own supervisor as the prefix and a 4-second bound, six scripted commands gave six start records and six finish records: the long command and the background command were ended at 4 s with exit 124, the detached `setsid` child of a finished command was ended, and no scripted process survived (`harness/cli-prefix/final-run.txt`, `ledger-final/`).

Limit of this evidence: it is the pinned binary on the host, not inside the worker image. The in-image check is a prepared step of the `images` phase (section 5) and has not been run.

### 2.2 What the candidate now does

New file `v12/worker/bounded_command.py`, copied by `Dockerfile.claude` to `/opt/baton/bounded_command.py` in the read-only root. It makes itself the child subreaper, runs one command, ends it at the earlier of its bound and an absolute deadline, then kills everything still descending from it and scans the process table until nothing does. It writes a start record before the command exists and a finish record after its descendants are gone.

For a review that carries the reviewer-verification requirement, `claude_agent` uses it three ways:

| What runs | How it is bounded |
| --- | --- |
| The adapter's own run of the task's verification command | under the supervisor, 900 s or the remaining invocation |
| The provider itself | under the supervisor, to the remaining invocation |
| Each shell-tool command the provider chooses | the CLI is started with the supervisor as its shell prefix; 900 s each or the remaining invocation |

A worker image without the supervisor refuses the review (`_supervisor_ready`); it does not run unbounded. Reviews without the requirement are unchanged, and no argv the context digests bind is changed.

### 2.3 The three confirmed findings

| Finding | Correction | Case |
| --- | --- | --- |
| C2.1 provider-chosen commands unbounded | the shell prefix above; the claim now carries `commands: {supervised, timed_out, unfinished, descendants_gone}` | `test_a_provider_chosen_command_is_ended_at_its_own_bound`, `…runs_and_answers_its_own_status`, `…is_ended_at_the_invocation_deadline_if_sooner`, `…whose_bound_was_not_delivered_is_not_run`; connected `test_the_reviewers_own_commands_are_supervised_and_counted` |
| C2.2 allowance computed before the copy | one origin read at the top of `_review`; one absolute deadline; remaining time re-read after the copy and again before the provider launch; the copy is waited for only until the deadline | `test_time_the_copy_took_comes_off_the_command_before_it_launches` (injected clock, no command launched), `test_a_copy_that_blocks_is_left_at_the_deadline_and_runs_nothing` |
| C2.3 empty group taken as completion | `group_gone` is gone; `descendants_gone` is the supervisor's process-table observation after adopting every descendant | `test_a_detached_descendant_of_a_passing_command_is_ended`, `…of_a_timed_out_command_is_ended`, `test_a_descendant_the_provider_itself_detached_is_ended_with_it` |

Grace is explicit: ending descendants may take up to 5 s, and every supervisor's deadline is 5 s short of the invocation's, so the ending is finished by the invocation deadline. Outer Job and stage clocks are untouched.

**No false success.** An `accepted` report is withheld (turn answers `unable`) when the required command did not pass, when any command started without a finish record, or when any supervisor did not see its descendants gone. The manager independently holds an acceptance whose claim lacks any of these, and no longer accepts `group_gone` (`test_an_acceptance_without_the_workers_own_passed_check_is_held`, six altered claims). Connected: `test_an_acceptance_over_a_command_nobody_saw_end_is_not_collected` kills a command's supervisor outright; the verdict is not collected and the orphaned command is still ended by the provider's own supervisor.

**Stated limit, not a narrowing.** The supervisor runs as the same user as the command. A command that deliberately kills its supervisor or rewrites the ledger is not prevented; it is caught by the start-without-finish record, by the provider's supervisor, by the invocation deadline and by container cessation. The bound is enforced for every command the CLI runs through its shell tool. `Bash` is the only shell tool among the 20 tools the CLI offered in this mode (`harness/cli-prefix/`, `api.log`); I did not test whether any other offered tool can start a process, and the provider's own supervisor and the invocation deadline are what bound anything that did.

**Behaviour change to know about.** A background process no longer outlives the command that started it. A reviewer that starts a server with `&` in one command and uses it in the next will find it ended.

The reviewer's `probe-corrections.py`, unmodified: the copy case passes; the replay case passes; the detached-descendant case now **errors on its own precondition** (`os.kill(pid, 0)` raises because the escaped child was ended) rather than failing its assertion. Its copy case uses a 1-second invocation, which the 5-second grace alone now refuses; my own case uses 30 s with a 60 s clock jump so the copy is what decides it.

## 3. C3 — stated-owner witnesses at the actual boundaries

`EveryStatedOwnerHasAWitness` passes. The five recovery entries each name their own witness in `StatedRules`, run over a world where the freeze really executes (a second writer granted on a reviewed line, started, declared abandoned and discharged through the accepted public operations):

| Stated entry | Witness | What it shows |
| --- | --- | --- |
| freeze · `line_writers` | `test_recovery_freeze_excludes_a_later_or_active_writer` | a later revoked writer and another active writer each hold the freeze, nothing committed; an earlier writer does not |
| freeze · `line_checkpoints` | `test_recovery_freeze_excludes_a_writer_that_already_has_a_checkpoint` | a checkpoint for this writer, and one at this identity, each hold it; another writer's checkpoint does not |
| freeze · `replay` | `test_recovery_freeze_replay_hands_the_committed_fence_on_unread` | retry returns the same checkpoint without freezing again; a conflicting retry refuses; a moved row fence is refused downstream while the document handed on is still the committed one |
| freeze · `profile` | `test_recovery_freeze_profile_owner` | name and each of freeze/validate/head_of typed before use; bypassing `_profile` removes that refusal |
| `_retained_line_home` · `line_writers` | `test_retained_line_home_excludes_a_later_or_active_writer` | located without a later writer; refused before any path is resolved with one |

The new reader `intake.abandonment_declared` (section 4) adds two receiving entries, each with one owner, and one probe; 28 probes arrive. The reviewer's `probe-registry.py` passes unmodified (30 owners, 28 probes).

Still inherited and not fixed: `test_no_declared_owner_is_stale` fails on the base's `('adopted', 'review_cycles.py:freeze_checkpoint', 'replay')`, exactly as before. It is not waived and not caused by this candidate.

## 4. C4 — the installed removal replays and finishes

`stopped_settlement.remove` now asks whether this exact attempt already carries a committed abandonment declaration (new read-only `intake.abandonment_declared`). If it does, the gate is that declaration rather than `quiescent`, the declaration's own reason is replayed, and the abandonment owner either returns its committed result or finishes the ending. The answer gains `replayed` and `reason`. Without a declaration the old gate stands.

A second defect surfaced while proving this and is corrected: `single_worker.abandon_attempt` opened an adoption window on the attempt's roots that only a first settlement closed. An exact replay, or a call cut by a fault, left it standing, and every later inspection then held the original as `quiescence-unknown`. The call now releases the window it opened, whatever the ending (idempotent over one already closed).

| Required by the review | Case |
| --- | --- |
| lost reply | `test_a_removal_whose_reply_was_lost_answers_its_committed_result`: same and different reason, same committed answer, no further engine removal, declaration unchanged, inspection eligible |
| crash cuts after removal / before settlement | `test_a_removal_cut_before_its_ending_settled_is_finished_by_repeating`: cut at settlement and cut before the cessation record; repeat finishes, one declaration |
| refusals preserved | `test_removal_still_refuses_what_it_never_declared`: running attempt, other episode; nothing declared or removed |
| competing manager | `test_a_competing_manager_excludes_the_installed_removal`: **a second process** holds the instance guard; the command is refused before it declares or removes anything; with the guard released it succeeds |

Not separately exercised: an `uncertain` runtime and a never-started attempt (both refused by the unchanged gate; the latter has a prior case), and the default `_composed` path without the fixture's engine double. The fixture's compose calls the same `stage_execution.operations_from`, which is where the guard is taken.

## 5. C5 — qualification preparation

`qualify-w385695.sh` is rewritten (sha256 in `packet.sha256`). **No engine phase was executed.** What changed:

- **Exact targeting.** No listing by a shared label. The attempt id comes from this instance's `publication-status` for this decision; the single container with that exact label must also have every bind mount under this instance's own roots and an image this run built, before any pause, exec or unpause.
- **Owned processes.** `recovery` runs publisher and reviewer in one invocation. A trap on every ending stops the watcher, releases the one container this run froze, stops the stack only if this run started it, ends owned processes with bounded waits, reports leftover selected containers without removing them, and seals evidence last.
- **Owned images.** Fresh tags per run, refused if they already exist, recorded with image id; `cleanup` removes a tag only if it still names the recorded image.
- **Parsed JSON** comparison throughout.
- **Probe results are structured.** `refused:EROFS/EACCES/EPERM` passes; `wrote` fails; an exec failure or vanished container fails as "did not answer".
- **Installed command.** Every manager operation is `<destination>/distro/baton-v12-stack manager …` with an empty environment.
- **Mount, credential and token assertions** on the publisher; in-image supervisor assertions on the provider image; per-image gate list written to evidence.

Dry runs against scripted doubles of the engine CLI and the installed command (`harness/qualify/`, nine scenarios, `dry-run.log`): two other-instance containers were present throughout and were never paused or exec'd; a same-label decoy with foreign mounts and a wrong-image container were refused with no effect; an exec failure and a writable source each fail; a TERM mid-freeze unpauses the one frozen container, stops the stack and leaves no process; cleanup leaves a re-pointed tag alone. The `images` and `fixture-image` phases have no dry run.

## 6. Verification

Prepared interpreter, `just test-one`, disk-backed scratch. Logs, exit files and the source identity are in `logs/`.

| Run | Result |
| --- | --- |
| Four required modules | 409/409 passed, 135.9 s |
| Affected set, 22 modules | 1939/1939 passed, 205.7 s |
| Recipe-reading modules, 7 | 704 of 705 passed, 34.3 s; the one failure is the inherited authority-isolation literal (below) |
| `tests.tools.test_stage_execution` | 517/517 passed, 350.9 s |
| Registry classes and the six witnesses | 18/18 passed |
| Three registry tests carrying the inherited entry | 3 run, 1 fails (inherited, unchanged) |
| Registry harness | new entries one owner each; 28 probes arrive; intake unprobed 0 |
| Reviewer probes, unmodified | 385919 set: 4/4 pass; 385926 `probe-corrections.py`: 2 pass, 1 errors on its precondition (section 2.3); `probe-registry.py` passes |

Not run: the whole boundary inventory, scans, the `job_manager` group, `test_checkpoint_profiles`, any image, engine or container.

Two failures surfaced in modules no earlier round of mine had run, and neither review had reached:

- **Mine, from an earlier round, now fixed.** `test_parallel_runner…test_every_record_path_in_the_tree_is_declared_or_synthetic` failed because two fixtures of this candidate bind a Work to this dossier's locator string. Both write that record inside their own disposable checkout and read nothing from the tree, so the locator is now listed in `SYNTHETIC_RECORD_PATHS` with that reason. The reviewed candidate `9475646d` had this failure.
- **Inherited, not fixed.** `tests.authority.test_boundary…test_nothing_reaches_for_v11_the_node_host_or_a_dossier` fails on a `work/records` literal in `publication_recovery.py`. It fails identically on the base (`logs/base-authority-boundary.log`). I left it because that literal is a recorded selection source and I did not establish that changing it leaves digest-bound inputs alone.

One thing I must disclose: running the reviewer's `probe-registry.py` unmodified made it rewrite `evidence/review-385926/registry-owners.json`. The bytes are identical and all of that packet's recorded hashes still verify; only the file's modification time changed.

## 7. One decision for the owner

**The deterministic provider for image qualification.** v12 has no deployment selection for a deterministic provider, so an installed instance cannot produce the two failed producers or a scripted review without a live model. The script does not hide this. Options:

- **A (prepared, recommended):** the `fixture-image` phase builds on this run's provider image and replaces only the `claude` program with a labelled scripted one. Adapter, worker, supervisor and mounts are the reviewed bytes; the pinned CLI is not exercised in a container. The operator selects that image for the qualification instance and creates the two Jobs; `preflight` proves the result.
- **B:** add a supported provider-endpoint selection so the real pinned CLI runs in the image against a local scripted endpoint. Stronger evidence; a product change needing its own scope.
- **C:** a live model. Excluded by the current boundary.

Nothing in the source candidate depends on this choice.

## 8. Affected images

Unchanged list of five. The provider image now also carries `bounded_command.py` and a changed recipe; the integration, reconciliation and publication recipes are unchanged this round. `claude_agent.py` changed again, so the provider and integration images carry new worker bytes.
