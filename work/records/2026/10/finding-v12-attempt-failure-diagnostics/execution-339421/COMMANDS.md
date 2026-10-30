# The exact commands — no placeholders

Five commands. Steps 0 to 3 are authorized preparation and produce no
execution. **Step 4 is not selected and must not be run until an owner selects
this run.** `OPERATOR.md` explains what each one does and what to expect;
this file is the copy-paste.

Run id `attempt-diagnostics-w333486-339421`, base
`bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, destination
`/home/sl/baton-instances/attempt-diagnostics-w333486-339421` — **which does
not exist and must be created by step 1, not by hand.**

## 0 — read-only input check (anyone, any time)

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339421/verify-inputs.py
```

## 1 — stage

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339421/prepare.py stage --root /home/sl/baton-instances/attempt-diagnostics-w333486-339421 --acknowledge-unselected-start
```

## 2 — bootstrap this instance's own authority

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-339421/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-339421/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-339421/code/v12/python python3 -B -m tools.bootstrap --inputs /home/sl/baton-instances/attempt-diagnostics-w333486-339421/bootstrap-inputs.json --destination /home/sl/baton-instances/attempt-diagnostics-w333486-339421/instance --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro --no-repositories
```

## 3 — bind

```
python3 -B /home/sl/src/baton/work/records/2026/10/finding-v12-attempt-failure-diagnostics/execution-339421/prepare.py bind --root /home/sl/baton-instances/attempt-diagnostics-w333486-339421
```

## 4 — start: NOT SELECTED

Only after an owner selects this exact run. **This is the enforced invocation;
`packet/commands.json`'s `start` is the unenforced supervisor and must not be
used** — see `ENFORCEMENT.md`.

```
cd /home/sl/baton-instances/attempt-diagnostics-w333486-339421/code/v12/python
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/sl/baton-instances/attempt-diagnostics-w333486-339421/code/v12/python/src:/home/sl/baton-instances/attempt-diagnostics-w333486-339421/code/v12/python:/home/sl/baton-instances/attempt-diagnostics-w333486-339421/supervisor BATON_V12_STAGE_EXECUTION_CONFIG=/home/sl/baton-instances/attempt-diagnostics-w333486-339421/packet/deployment.json python3 -m tools.authoring_enforcement --packet /home/sl/baton-instances/attempt-diagnostics-w333486-339421/packet/PACKET.json
```

`bind` writes the same invocation machine-readably to
`/home/sl/baton-instances/attempt-diagnostics-w333486-339421/packet/AUTHORING-COMMAND.json`,
with the staged controller's and shutdown helper's paths and digests. Check it
against the command above before starting; if they disagree, stop.

## 5 — after a run, read the three final results

```
ls -la /home/sl/baton-instances/attempt-diagnostics-w333486-339421/packet/outcome.json*
```

| file | what it is |
| --- | --- |
| `packet/outcome.json` | the workload final report |
| `packet/outcome.json.enforcement-<pid>-<ns>.json` | the controller final report, with `shutdown_deadline` and `shutdown_progress` |
| `packet/outcome.json.manager-<pid>-<ns>.json.progress.json` | the last shutdown step entered |
| `packet/outcome.json.authoring.log` | the retained authoring log |

**A missing or partial final report is INCOMPLETE — never success, never
acceptance, never proof of cessation.** See `SHUTDOWN.md`.

## Operands this run proposes

| operand | value |
| --- | --- |
| run id | `attempt-diagnostics-w333486-339421` |
| root | `/home/sl/baton-instances/attempt-diagnostics-w333486-339421` (absent; created by step 1) |
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
  failed run, preserved as evidence: no rerun, no recovery, no reuse.
- A second `bind` over a root that already holds a composed packet; it is
  refused by design.
- Any step at all against the four earlier packets. They are sealed history.
