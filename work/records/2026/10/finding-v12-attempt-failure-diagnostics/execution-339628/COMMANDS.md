# The exact commands — no placeholders

Six commands. Steps 0 to 3 are authorized preparation and produce no execution.
**Step 4 is not selected and must not be run until an owner selects this run.**
Step 5 is the post-run collection, and it belongs to **you — the operator and
the reviewer — not to the worker inside the run.** `OPERATOR.md` explains what
each one does and what to expect; this file is the copy-paste.

Run id `attempt-diagnostics-w333486-339628`, base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, destination
`/home/sl/baton-instances/attempt-diagnostics-w333486-339628` — **which does
not exist and must be created by step 1, not by hand.**

## 0 — read-only input check (anyone, any time)

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339628/verify-inputs.py
```

## 1 — stage

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339628/prepare.py stage --root /home/sl/baton-instances/attempt-diagnostics-w333486-339628 --acknowledge-unselected-start
```

## 2 — bootstrap this instance's own authority

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-339628/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-339628/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-339628/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/attempt-diagnostics-w333486-339628/bootstrap-inputs.json --destination /home/sl/baton-instances/attempt-diagnostics-w333486-339628/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
```

## 3 — bind

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339628/prepare.py bind --root /home/sl/baton-instances/attempt-diagnostics-w333486-339628
```

## 4 — start: NOT SELECTED

Only after an owner selects this exact run. **This is the enforced invocation;
`packet/commands.json`'s `start` is the unenforced supervisor and must not be
used** — see `ENFORCEMENT.md`.

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-339628/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-339628/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-339628/code/v12/python:/home/sl/baton-instances/attempt-diagnostics-w333486-339628/supervisor BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/attempt-diagnostics-w333486-339628/packet/deployment.json python3 -m tools.authoring_enforcement --packet /home/sl/baton-instances/attempt-diagnostics-w333486-339628/packet/PACKET.json
```

`bind` writes the same invocation machine-readably to
`/home/sl/baton-instances/attempt-diagnostics-w333486-339628/packet/AUTHORING-COMMAND.json`,
with the staged controller's and shutdown helper's paths and digests. Check it
against the command above before starting; if they disagree, stop.

## 5 — after a run: collect the final results. **This is yours, not the worker's.**

**The worker inside the run cannot do this and was not asked to.** All three
final results are published after it is gone: the controller writes its report
after `supervise_process` returns and after child cleanup
(`authoring_enforcement.py:552-591`), and the supervisor publishes
`<outcome_path>` post-stop (`baseline.py:1450-1461`). A worker terminated at the
900-second lease expiry is already dead when both land, and a producer cannot be
the evidence source for its own cessation. `TASK.md` item 6 is the worker's
half: what it observed before termination, plus the retained candidate
checkpoint. **This step is the other half, and the acceptance needs both.**

### 5a — the collection itself

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339628/collect.py --root /home/sl/baton-instances/attempt-diagnostics-w333486-339628
```

Read-only: it opens no store, writes nothing, starts nothing, and reads no
credential, transcript or provider output. It prints one JSON report that, for
each of the four artifacts, gives the state, the paths it found, any `.tmp`
siblings, and the identity correlation:

| artifact | path shape | written by |
| --- | --- | --- |
| workload final report | `packet/outcome.json` | the supervisor, post-stop, inside the `workload-publication` reservation |
| controller final report | `packet/outcome.json.enforcement-<pid>-<ns>.json` | the outer controller, after child cleanup |
| shutdown progress | `packet/outcome.json.manager-<pid>-<ns>.json.progress.json` | each `Shutdown.call`, **before** running its step |
| authoring log | `packet/outcome.json.authoring.log` | the run; reported by **presence, size and digest only** |

### 5b — read the states it reports, and do not collapse them

**An unavailable report names no cause.** Four different facts:

| state | what it means | what it does **not** mean |
| --- | --- | --- |
| **absent** | the directory was listed and the path is not in it | not a timeout, not cessation, not "nothing was written" |
| **inaccessible** | the read itself failed — permission, mount, I/O | **not** absent |
| **pending** | no final path, but a `.tmp` sibling exists, so publication was entered and did not complete | not absent, not failed |
| **unknown cause** | present but unparseable, truncated, or its `run_id` does not correlate | not evidence about this run |

`collect.py` reports `publication_timeout.established: false` unless it actually
read a `TimeoutError` fault in a correlated controller report. **Honour that.** A
run that never started, an import or startup failure, process death, a failed
read and non-timeout publication errors all leave no final report. This Work's
one real execution is the standing example: it died at startup in 0.506s and
left **no workload outcome at all** — `FAILURE.md` and
`../evidence/execution-334663-failure/`. A reader that turned that absence into
a publication timeout would have reported a timeout that never happened.

And note the converse: a present report is **not** proof that publication
completed cleanly. The bound at `authoring_enforcement.py:586-594` wraps
`write_text`, `os.replace` **and** `print` in one block, so a `TimeoutError`
during the `print` follows an already-completed `os.replace`. Check
`temporary_siblings` before concluding.

**A missing or partial final report is INCOMPLETE — never success, never
acceptance, never proof of cessation.** No startup success and no producer exit
substitutes for final-result acceptance. See `SHUTDOWN.md`.

### 5c — correlate, and name what is missing

The worker's report carries `run_id`, `work`, `claim`, its own pid where it knew
it, and the `outcome_path`/`status_path` it was given. `collect.py` reports the
composed identity from `packet/PACKET.json` and checks every report's `run_id`
against it — `matched`, `mismatch` or `unresolved`. Join the two on `run_id`.

When you write up the run, state for each of the four artifacts **which state it
was in**, and for each one that was unavailable, **that its cause is unknown
unless you have correlated positive evidence**. An unavailable final report
retracts nothing already recorded: the authoring log, the manager snapshots and
the progress file remain exactly as good as they were.

### 5d — the retained candidate and the retained evidence

```
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-339628/packet/outcome.json*
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-339628/packet/workspaces
```

For retained attempt evidence, the supported reader is the deployed `logs`
subcommand over `worker_manager.attempt_logs`; it needs the launch home's logs
root and the attempt id, both of which come out of the run rather than out of
this packet:

```
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> locators
```

`TASK.md`'s locator obligation is that the candidate's own report emits the
attempt identity and the manager-recorded locator fields and names this one
operand you must supply. This packet does not resolve a deployment root, and a
report that did would be a reader that can be pointed at a store.

## Operands this run proposes

| operand | value |
| --- | --- |
| run id | `attempt-diagnostics-w333486-339628` |
| root | `/home/sl/baton-instances/attempt-diagnostics-w333486-339628` (absent; created by step 1) |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| image reference | `baton-v12-claude-worker:w239528-244216`, config digest `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`, from `IMAGE-ARTIFACT-244216.json` pinned at `8cf90edc…` |
| worker profile | `claude-fresh-implementation`, engine `docker`, model `opus`, cli build `2.1.247`, runtime uid 1000 |
| runtime profile | `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, binary `04aa459a…`, build commit `1e576ff2` |
| provider network | `bridge` |
| credential reference | registry `/home/sl/.baton/credential-sources.json`, slot `claude`, provider `operator-file`, reference `w202663-development` — **named, never read by this packet** |
| limits | provider 3600s, verification 30s, total 4800s, cleanup 60s, one invocation, no retry, `report-and-hold` |
| lease | **900s, enforced and not extended** |

Before step 4, confirm the credential reference resolves in your own registry
and that the image reference is available. This packet contacted neither.

## What must not be run

- `packet/commands.json`'s `start` — the unenforced supervisor.
- Anything against
  `/home/sl/baton-instances/attempt-diagnostics-w333486-334663`. That is the
  failed run, preserved as evidence: no rerun, no recovery, no reuse. Read-only
  copies of its evidence are in `../evidence/execution-334663-failure/`, and
  `collect.py --packet-dir` over those copies is how this packet exercised the
  collection against real evidence without touching the instance.
- A second `bind` over a root that already holds a composed packet; it is
  refused by design.
- Any step at all against the five earlier packets. They are sealed history.
