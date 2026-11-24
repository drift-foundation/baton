# W385695 — C5 qualification-preparation corrections (review 2026-11-24T04-42-16Z, M385942/M385944)

**For independent review. Preparation only. Not accepted, not imported, not qualified.**
Author: baton.prompt (K), owner-selected interactive continuation, no claim.
No source change, host import, protected Git mutation, image build, engine or container operation, live model call or credential read. The revision-3 scripts were not executed.

No new decision is raised.

## 1. Source: unchanged, not repackaged

The accepted candidate is manifest `162152b462b8ab0907a43b5dd41f85e8c7c2a6218053b6a93bbf9edc1762a8dd` in `evidence/correction-K-385937/`. This packet carries no candidate.

`source-unchanged.json` records the check made when this packet was sealed: all 50 paths in the scratch repository (head `6d6a4fc8fb1defceeacfaaf97927ffc867fa1ef9`, clean) equal the manifest by sha256 and mode; the path set equals the scratch diff from the base; all 81 entries of the earlier packet still match its `packet.sha256`. No source test was rerun.

## 2. The three scripts

| File | Reviewed (revision 3) | This packet (revision 4) |
| --- | --- | --- |
| `qualify-w385695.sh` | `18d8f260…` | `d8c579d3e9b0122581ce445aeabf02ac5e59a5edcbbaeba0e5911ede1f5da591` |
| `option-a-setup.sh` | `df694163…` | `976476acd42b6328265680d64f4868f9511c086875318bac340c37b4e8f2dc86` |
| `cli-in-image-driver.py` | `b61c12d1…` | `b3a722ef406bb81ed0e84cadf2c0a4983dc3fe92a61532b9992d9a4217a1370d` |

`provenance/*.r3-to-r4.diff` is the change to read. The stack functions (`stack_live`, `op_alive`, `start_stack`, `reconcile_stack`) are byte-identical in the two shell scripts.

## 3. C5.1 — the start effect is reconciled on every exit

**What was wrong.** Ownership lived in a variable set after the start command returned, so a signal in between left a started stack that cleanup never looked at.

**What it does now, in both scripts.**

- **Before the start.** The stack's state is read through the instance's own `status`. A running process is another's and is refused. A state that cannot be told is also refused. Nothing is started or stopped in either case.
- **Intent, then effect.** A start intent holding a token unique to this start is written to disk. The start command then runs as its own process, which records itself (pid and start time) before it asks for anything, and carries the token in its environment.
- **Every exit reconciles from those records**, not from a variable. It first waits for the start command to end, so nothing is reconciled under a start in flight. It then stops the stack through the instance's own `stop` only when every live process is positively this run's, and requires a positive read-back.
- **Anything else is left as it is and reported `UNRESOLVED`**, with the intent retained: state that cannot be told, a live process that is not this run's, a stop that did not positively stop, or a process of this start that no stack record names.
- **A phase with unresolved cleanup does not exit 0.**

**What ownership rests on.** Two things together, neither a pid alone:

1. The product's own answer. `status` says `running` only when the pid and the start time in its record both still match; its `unknown` is passed on as "cannot be told".
2. The token. The reviewed stack hands its caller's environment to the processes it starts (`tools.stack._spawn`, `child_environment`, `instance_settings`). A live recorded process is this run's only if its own environment carries this start's token, checked against the record's pid and start time.

**Signals to the whole process group** (a terminal's Ctrl-C, a group TERM) are covered: the recorded start process handles them and stays until the start command, which `timeout` runs in its own group, has ended.

The setup script's own deliberate stop before settlement now goes through the same reconciliation, and nothing is settled unless that stop is positively confirmed.

## 4. C5.2 — a failed observation is not absence

`pause_state` answers one of four words. Three are positive answers of the engine; the fourth is not an answer.

| Answer | Meaning | Cleanup |
| --- | --- | --- |
| `true` | inspected, paused | unpause, then read back |
| `false` | inspected, not paused | left alone |
| `absent` | inspection failed **and** the engine answered a listing by that exact id with nothing | nothing to release |
| `unknown` | anything else, after three tries | `UNRESOLVED`; **not unpaused blind**; intent retained |

- **The release is always read back**, whatever the unpause answered. A lost unpause reply with a not-paused read-back is released. A read-back that says still paused, or fails, is `UNRESOLVED`.
- **The main path uses the same function.** The deadline phase no longer reads a failed inspection as "already ended".
- **A pause request in flight is settled first.** The watcher's engine call is now its own recorded process. After the watcher has ended, cleanup waits for that request to end before it looks at the container, so a request that outlives a killed watcher cannot pause after the reconciliation.
- **Two more places had the same fault and are corrected:** the leftover-container listing at the end of a phase, and the `cleanup` phase's "tag already gone". An engine that does not answer is now `UNRESOLVED` in both.

My earlier adapted probe equated a generic failure with "gone", as the review said. It still passes only because its double happens to answer the listing with nothing; the new probe separates the cases.

## 5. C5.3 — the driver ends only what its own turn started

I chose invocation ownership and kept the one program for host and container.

- Each run makes a random token and puts it in the environment of the one CLI process it starts.
- The survival check and the final cleanup select **only** processes whose own environment carries that token. No program name, argument or parent is consulted.
- A driver that started no turn owns nothing. Before each signal the token is read again for that pid.
- The check is now "nothing this turn started survived it", which is wider than the old name match.

The command, ledger, bound and version assertions are unchanged, and the in-image CLI obligation stays separate and unexecuted.

## 6. Evidence

All doubles. No engine, container, manager or model. Prepared interpreter, disk-backed scratch.

| Run | Result |
| --- | --- |
| Reviewer's `probe-cleanup-cuts.py`, packet path changed only | 3/3 (was 0/3) |
| Reviewer's `probe-driver-ownership.py`, packet path changed only | 1/1 (was 0/1) |
| Reviewer's copy of `probe-qualification-r3.py`, byte-identical | 4/4 |
| `probes/probe-cleanup-r4.py` (new) | 10/10 |
| `harness/qualify/run-all.sh`, 40 scenarios | 40/40 as required |
| `option-a-setup.sh` argv through the real `pool`, `bootstrap` and `job_manager` | 1/1 |
| Revised driver on the host, pinned CLI 2.1.247, final supervisor bytes | pass, 10 checks |
| Revised driver, unbounded pass-through prefix (abort path) | fails as intended: the turn is aborted at 240 s, two of its processes are found by token and ended, none is left |

**The scenario matrix** (`harness/qualify/dry-run.log`; each scenario states what it must show and is marked):

- *Stack, both scripts:* TERM while the start is in flight; after its effect and before its answer; after acknowledgment; the same to the whole process group; a pre-existing stack (refused, left running); live processes that are not this run's; an unreadable record (the product's real `unknown`); a status that does not answer; a process started but never recorded; a stop that does not stop; clean and partial start failures.
- *Pause:* TERM mid-freeze; pause reply lost; engine stops answering after the pause; unpause reply lost; unpause fails; unpause fails and the read-back fails; TERM while the pause request is in flight; the watcher killed while the request is in flight.
- *Retained from revision 3:* the selection, refusal and ordinary-ending scenarios, unchanged in outcome.

**The stack double is the product's own code where it matters.** Records are written by the reviewed `tools.stack._spawn`, and `status` and `stop` are the reviewed `tools.stack.status` and `tools.stack.stop`. Only what a manager and a publisher are is doubled (a `sleep`).

**The new probe** asks the exact `reconcile_pause`, `pause_state` and `finish` text every combination of first inspection, unpause and read-back, checks the exit status of a phase with unresolved cleanup, and shows the driver ending a token-bearing `sleep 303` while a same-named one beside it stays alive.

## 7. Limits

- **Token ownership is not proved against an installed bundle.** It is read from the reviewed stack source and exercised through the real `_spawn`. If an installed command did not pass the environment on, the result is "ownership is not established": `UNRESOLVED`, nothing stopped. It cannot become a wrong stop.
- **The installed command has no machine-readable status verb.** The scripts read the product's `status` text for its four process states; output they do not recognise is "cannot be told".
- **A process of this start outside the stack's records is reported, never signalled.**
- **A script killed with SIGKILL runs no cleanup.** Its intent stays on disk, and a rerun of the phase refuses to start over it and reconciles it. That rerun path was not exercised.
- **A request still in flight after its own bound** is reported `UNRESOLVED`; it is not killed.
- Everything in section 6 is doubles. Every engine phase, the fixture image build and the in-image CLI check remain unexecuted.

## 8. Disclosures

- Two earlier runs of the scenario matrix were discarded. The first stalled on a 600-second default wait in a refusal scenario, and I edited its runner while it was executing; I ended it and its own processes (selected by the run's token) and set the wait to 20 seconds in the harness. The second completed with two scenarios marked not as required. In both the script behaved correctly and my stated expectation was wrong: the setup script asks for the stop twice when it does not stop (once deliberately, once at exit), and an unpause that fails with the engine then down is reported by the first inspection, not the read-back. I corrected the two expectations and ran the whole matrix again from an empty directory. The retained log is that third run; the second is kept as `harness/qualify/dry-run.discarded-expectations.log`.
- `evidence/correction-K-385937/` now holds a `__pycache__` directory that is not in its `packet.sha256`. It is not mine and I did not touch it; importing the driver from that directory creates it. I ran every probe with bytecode writing off.
- No reviewer probe that writes into its own evidence directory was run. `evidence/review-385941/` was only read.
