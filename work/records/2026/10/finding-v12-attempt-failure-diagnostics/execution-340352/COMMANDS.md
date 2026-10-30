# The exact commands — no placeholders

Six commands, and one thing to know before any of them: **this is a
CONTINUATION.** The previous run completed, returned a candidate, and that
candidate was rejected with three static blockers. `CONTINUATION.md` is the
account; the turn's first act is to apply the pinned candidate patch.

Six commands. **Step 5's subsections exist because this packet's collector has
twice made claims its artifacts did not support — four defects found by
`decisions/review-339861.md` and three more by `decisions/review-340012.md`.
`SHUTDOWN.md` has the account; both reviewers' fixtures are pinned in
`decisions/` so you can check the corrections yourself.** Steps 0 to 3 are authorized preparation and produce no execution.
**Step 4 is not selected and must not be run until an owner selects this run.**
Step 5 is the post-run collection, and it belongs to **you — the operator and
the reviewer — not to the worker inside the run.** `OPERATOR.md` explains what
each one does and what to expect; this file is the copy-paste.

Run id `attempt-diagnostics-w333486-340352`, base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, destination
`/home/sl/baton-instances/attempt-diagnostics-w333486-340352` — **which does
not exist and must be created by step 1, not by hand.**

## 0 — read-only input check (anyone, any time)

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-340352/verify-inputs.py
```

## 1 — stage

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-340352/prepare.py stage --root /home/sl/baton-instances/attempt-diagnostics-w333486-340352 --acknowledge-unselected-start
```

## 2 — bootstrap this instance's own authority

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-340352/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-340352/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-340352/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/attempt-diagnostics-w333486-340352/bootstrap-inputs.json --destination /home/sl/baton-instances/attempt-diagnostics-w333486-340352/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
```

## 3 — bind

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-340352/prepare.py bind --root /home/sl/baton-instances/attempt-diagnostics-w333486-340352
```

## 4 — start: NOT SELECTED

Only after an owner selects this exact run. **This is the enforced invocation;
`packet/commands.json`'s `start` is the unenforced supervisor and must not be
used** — see `ENFORCEMENT.md`.

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-340352/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-340352/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-340352/code/v12/python:/home/sl/baton-instances/attempt-diagnostics-w333486-340352/supervisor BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/attempt-diagnostics-w333486-340352/packet/deployment.json python3 -m tools.authoring_enforcement --packet /home/sl/baton-instances/attempt-diagnostics-w333486-340352/packet/PACKET.json
```

`bind` writes the same invocation machine-readably to
`/home/sl/baton-instances/attempt-diagnostics-w333486-340352/packet/AUTHORING-COMMAND.json`,
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
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-340352/collect.py --root /home/sl/baton-instances/attempt-diagnostics-w333486-340352
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
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-340352/collect.py --packet-dir /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/evidence/execution-334663-failure --expect-run attempt-diagnostics-w333486-334663
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
| **pending** | a temporary belonging to **this** artifact exists, so **its** publication was entered and did not complete | not absent, not failed, and **nothing about any other artifact** |
| **unknown cause** | present but unparseable, **not a JSON object**, or its identity does not correlate | not evidence about this run |

A malformed artifact — **or a malformed link inside a readable one** — is
reported as an observation and **does not stop the rest of the collection**;
anything that went wrong internally is listed under `isolated_failures`.
`available` names the artifacts actually read.

Each artifact is classified **only from files matching its own name**, which is
not guessable and was twice got wrong here. The real names, read from the
producers: the workload's temporary is `outcome.json.partial`
(`baseline.py:1006`), while `with_suffix('.tmp')` *replaces* `.json`, so the
controller's is `outcome.json.enforcement-<pid>-<ns>.tmp`. And
`outcome.json.manager-*.json` matches `...json.progress.json`, so a glob would
report a manager snapshot that does not exist. `directory_entries` gives you the
whole listing and `unclassified_entries` anything unaccounted for — neither is
used to infer any artifact's state.

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
`<manager_report_path>.progress.json` — and says whether each was `found`,
`named but not present`, `inaccessible`, `malformed` (the report carried
something that is not a path string) or `not named by the report`. A malformed
link is reported and **not followed**, and it costs you nothing else. If the run
root was moved or copied, those absolute paths will not resolve; that is a fact
about your filesystem, not about the run, and the output says so.

The worker's report carries `run_id`, `work`, `claim`, its own pid where it knew
it, and the `outcome_path`/`status_path` it was given. Join the two on `run_id`.

When you write up the run, state for each artifact **which state it was in**, and
for each unavailable one **that its cause is unknown unless you have specific
correlated evidence**. An unavailable final report retracts nothing already
recorded.

### 5d — the timeout verdict, and why it is usually unknown

**This vehicle persists no publication fault reliably.** Read that before you
read the verdict, because it means absence is the *expected* state even when a
publication really did time out. From the producer's statement order in
`Shutdown.call` (`authoring_shutdown.py:72-86`): it enters
`bounded(deadline, step)` **first** — an exhausted deadline raises there, before
any write — then writes its snapshot carrying the faults of **earlier** calls,
then runs the step, then on failure appends that step's fault to **memory only**
and re-raises.

| step | recordable? | why |
| --- | --- | --- |
| `outer outcome publication` (`authoring_enforcement.py:588`) | **no** | not a `Shutdown.call`; the handler at `:592-595` returns 1 and records nothing |
| `final enforcement publication` (`:493`) | **no** | the **last** `Shutdown.call` in the controller's `finally`; nothing follows to flush its fault |
| `workload publication` (`baseline.py:1461`) | **not reliably** | later calls exist in `main` but are reached only if control gets there, and each re-enters `bounded()` against the same exhausted deadline |

So `collect.py` reports:

- `publication_timeout.established: false` with
  `producer_persistence` spelling the above out. **That is not "no timeout
  happened"** — it is "nothing on disk could tell you either way".
- `parsed_publication_faults` when a fault naming a publication step **is**
  literally on disk in a correlated artifact, each entry labelled
  `PARSED FROM A FAULT ALREADY ON DISK`. Parsing, not producer proof.
- `other_timeouts_observed` — real `TimeoutError`s naming **non-publication**
  steps (`manager startup snapshot`, `manager shutdown observation`, a cleanup
  step). Genuine observations, **not** publication evidence.
- `uncorrelated_timeouts` — faults in artifacts that do not correlate to this
  run. Evidence about something else.

This Work's one real execution is the standing example of why absence licenses
nothing: it died at startup in 0.506s and left **no workload outcome** —
`FAILURE.md` and `../evidence/execution-334663-failure/`.

And the converse: a present report is **not** proof that publication completed
cleanly. The bound at `authoring_enforcement.py:586-594` wraps `write_text`,
`os.replace` **and** `print` in one block, so a `TimeoutError` during the `print`
follows an already-completed `os.replace`. Check that artifact's
`own_temporaries`.

**A missing or partial final report is INCOMPLETE — never success, never
acceptance, never proof of cessation.** No startup success and no producer exit
substitutes for final-result acceptance. See `SHUTDOWN.md`.

### 5e — the retained candidate and the retained evidence

```
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-340352/packet/outcome.json*
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-340352/packet/workspaces
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
| run id | `attempt-diagnostics-w333486-340352` |
| root | `/home/sl/baton-instances/attempt-diagnostics-w333486-340352` (absent; created by step 1) |
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
  `/home/sl/baton-instances/attempt-diagnostics-w333486-334663` (the startup
  failure) or `/home/sl/baton-instances/attempt-diagnostics-w333486-340016`
  (**the completed run, whose retained candidate this packet continues from**).
  Both are preserved as evidence: no rerun, no recovery, no reuse. Read-only
  copies are in `../evidence/execution-334663-failure/` and
  `../evidence/run-340016/`, and `collect.py --packet-dir` over those copies is
  how this packet exercised the collection against real evidence without
  touching either instance.
- **The host-side gate rerun that `candidate-verification.txt` suggests.**
  `decisions/review-340349.md` is explicit that a generated line in a proposal
  is not authority: AGENTS applies, there is no product-test exception for
  W333486, and the previous invocation is consumed. The classification happens
  inside the next isolated run — `TASK.md` item 7.
- A second `bind` over a root that already holds a composed packet; it is
  refused by design.
- Any step at all against the eight earlier packets. They are sealed history.
