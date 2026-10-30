# The exact commands — no placeholders

Six commands. **Step 5 grew subsections (5a to 5e) because revision 6's
collector made four claims its artifacts did not support; `SHUTDOWN.md` and
`decisions/review-339861.md` have the account.** Steps 0 to 3 are authorized preparation and produce no execution.
**Step 4 is not selected and must not be run until an owner selects this run.**
Step 5 is the post-run collection, and it belongs to **you — the operator and
the reviewer — not to the worker inside the run.** `OPERATOR.md` explains what
each one does and what to expect; this file is the copy-paste.

Run id `attempt-diagnostics-w333486-339868`, base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, destination
`/home/sl/baton-instances/attempt-diagnostics-w333486-339868` — **which does
not exist and must be created by step 1, not by hand.**

## 0 — read-only input check (anyone, any time)

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339868/verify-inputs.py
```

## 1 — stage

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339868/prepare.py stage --root /home/sl/baton-instances/attempt-diagnostics-w333486-339868 --acknowledge-unselected-start
```

## 2 — bootstrap this instance's own authority

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-339868/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-339868/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-339868/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/attempt-diagnostics-w333486-339868/bootstrap-inputs.json --destination /home/sl/baton-instances/attempt-diagnostics-w333486-339868/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
```

## 3 — bind

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339868/prepare.py bind --root /home/sl/baton-instances/attempt-diagnostics-w333486-339868
```

## 4 — start: NOT SELECTED

Only after an owner selects this exact run. **This is the enforced invocation;
`packet/commands.json`'s `start` is the unenforced supervisor and must not be
used** — see `ENFORCEMENT.md`.

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-339868/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-339868/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-339868/code/v12/python:/home/sl/baton-instances/attempt-diagnostics-w333486-339868/supervisor BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/attempt-diagnostics-w333486-339868/packet/deployment.json python3 -m tools.authoring_enforcement --packet /home/sl/baton-instances/attempt-diagnostics-w333486-339868/packet/PACKET.json
```

`bind` writes the same invocation machine-readably to
`/home/sl/baton-instances/attempt-diagnostics-w333486-339868/packet/AUTHORING-COMMAND.json`,
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
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339868/collect.py --root /home/sl/baton-instances/attempt-diagnostics-w333486-339868
```

Read-only: it opens no store, writes nothing, starts nothing, and reads no
credential, transcript or provider output. It prints one JSON report covering
five artifacts, each with its state, the paths it found, any `.tmp` siblings and
its identity correlation:

| artifact | path shape | written by |
| --- | --- | --- |
| workload final report | `packet/outcome.json` | the supervisor, post-stop, inside the `workload-publication` reservation |
| controller final report | `packet/outcome.json.enforcement-<pid>-<ns>.json` | the outer controller, after child cleanup |
| shutdown progress | `packet/outcome.json.manager-<pid>-<ns>.json.progress.json` | each `Shutdown.call`, **before** running its step |
| manager status snapshot | `packet/outcome.json.manager-<pid>-<ns>.json` | `publish_guard`, each observation |
| authoring log | `packet/outcome.json.authoring.log` | the run; reported by **presence, size and digest only** |

Over a **retained evidence copy** rather than a live root, use `--packet-dir`,
and add `--expect-run` because such a directory holds the published artifacts
but not the composed `PACKET.json`:

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339868/collect.py --packet-dir /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/evidence/execution-334663-failure --expect-run attempt-diagnostics-w333486-334663
```

`--expect-run` is an **operator assertion** and is labelled as one in the output
(`expected_identity.identity_source`). It is refused outright if it contradicts
a `PACKET.json` that *is* readable, rather than quietly correlating against one
of two different runs.

### 5b — read the states it reports, and do not collapse them

**An unavailable report names no cause.** Four different facts:

| state | what it means | what it does **not** mean |
| --- | --- | --- |
| **absent** | the directory was listed and the path is not in it | not a timeout, not cessation, not "nothing was written" |
| **inaccessible** | the read itself failed — permission, mount, I/O | **not** absent |
| **pending** | a `.tmp` sibling exists, so publication was entered and did not complete | not absent, not failed |
| **unknown cause** | present but unparseable, **not a JSON object**, or its identity does not correlate | not evidence about this run |

A malformed artifact is reported as that artifact's state and **does not stop the
rest of the collection**; anything that did go wrong inside one artifact is
listed under `isolated_failures`. `available` names the artifacts actually read.

### 5c — correlate, and name what is missing

Each artifact is correlated through **the fields it actually publishes**, and the
output names the field used in `identity_detail.correlated_on`:

| artifact | identity fields | note |
| --- | --- | --- |
| controller report | `original_envelope.run`, `.job`, `.authority` | **no top-level `run_id`**; built at `authoring_enforcement.py:40-52`, stored at `:580`. A controller incarnation that never established an envelope carries no identity — reported `unresolved`, not guessed |
| workload outcome | `run_id`, `job_id`, `work`, `claim` | `baseline.py:1453-1458` |
| shutdown progress | `run_id`, `job_id` | `authoring_shutdown.py:76-78` |
| manager snapshot | `envelope.run` | `publish_guard` |

The verdict is `matched`, `mismatch` (a carried field disagrees — evidence about
another run, and the artifact is downgraded to `unknown-cause`) or `unresolved`
(the artifact carries no identity, or nothing was available to compare against).

`linked_artifacts` resolves the paths the controller report names **for itself** —
`enforcement_path`, `authoring_log`, `manager_report_path` and
`<manager_report_path>.progress.json` — and says whether each was found. If the
run root was moved or copied, those absolute paths will not resolve; that is a
fact about your filesystem, not about the run, and the output says so.

The worker's report carries `run_id`, `work`, `claim`, its own pid where it knew
it, and the `outcome_path`/`status_path` it was given. Join the two on `run_id`.

When you write up the run, state for each artifact **which state it was in**, and
for each unavailable one **that its cause is unknown unless you have specific
correlated evidence**. An unavailable final report retracts nothing already
recorded.

### 5d — the timeout verdict, and what it can and cannot establish

`collect.py` reports `publication_timeout.established: true` **only** when it
read a fault naming a publication step, in an artifact that correlates to this
run. Everything else is reported as what it is:

- `other_timeouts_observed` — real `TimeoutError`s naming **non-publication**
  steps (`manager startup snapshot`, `manager shutdown observation`, a cleanup
  step). These are genuine observations and are **not** publication evidence.
- `uncorrelated_timeouts` — faults in artifacts that do not correlate to this
  run. Evidence about something else.
- `outer_publication_limit` — the one that matters most:
  **an outer-publication timeout is not establishable from these files at all.**
  `authoring_enforcement.py:592-595` catches its own `TimeoutError` and returns
  1 *without* adding the fault to the report it was writing, so nothing records
  it. Its absence is **expected** and is not evidence either way. A child
  publication timeout *is* recordable and reaches the progress file.

So when the controller report is simply not there, the honest reading is
**unavailable, cause unknown** — with a partial `.enforcement-*.tmp` as the only
positive sign that publication was entered at all. This Work's one real
execution is the standing example: it died at startup in 0.506s and left **no
workload outcome** — `FAILURE.md` and `../evidence/execution-334663-failure/`.
A reader that turned that absence into a publication timeout would have reported
a timeout that never happened.

And the converse: a present report is **not** proof that publication completed
cleanly. The bound at `authoring_enforcement.py:586-594` wraps `write_text`,
`os.replace` **and** `print` in one block, so a `TimeoutError` during the `print`
follows an already-completed `os.replace`. Check `temporary_siblings`.

**A missing or partial final report is INCOMPLETE — never success, never
acceptance, never proof of cessation.** No startup success and no producer exit
substitutes for final-result acceptance. See `SHUTDOWN.md`.

### 5e — the retained candidate and the retained evidence

```
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-339868/packet/outcome.json*
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-339868/packet/workspaces
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
| run id | `attempt-diagnostics-w333486-339868` |
| root | `/home/sl/baton-instances/attempt-diagnostics-w333486-339868` (absent; created by step 1) |
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
- Any step at all against the six earlier packets. They are sealed history.
