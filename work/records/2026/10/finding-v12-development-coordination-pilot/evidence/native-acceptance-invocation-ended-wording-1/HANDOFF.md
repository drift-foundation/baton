# Native Job `invocation-ended-wording-1` — read-only acceptance collection and import recommendation (K)

K (`baton.prompt`, no claim; M385498). Everything here is read from the instance's retained files and supported views, or copied from them byte for byte; no store was opened; nothing on the instance was changed; no import, build, Git or live action. `native-handoffs-2` and `native-handoffs-3` are both left as they are (both still serving).

## 1. The pipeline, narrowly

| Step | Evidence | Fact |
|---|---|---|
| Instance | `instance/instance.json`, `bootstrap.json`, `deployment-binding.json` | `native-handoffs-3`: bundle `601ef8df…` (stamp `ac17a5ad`, dirty 64 dossier entries), runtime manifest `54b8d9ea…` (82 files), both workers on image `sha256:19eb459b…` declaring `proposal, findings, logs, handoff, response`; Job bound to Work `fd3e8b90-W1`, line base and canonical target `ac17a5ad` |
| Create | `checkpoint-ac17a5ad-qualification/create-invocation-ended-wording-1.{json,report.log}` (coordinator) | template `…/3`, profile `native-handoff/1` (3600 s provider turn, 4800 s stage, 9960 s Job, 900 s verification), the command's own report: routing `reviewer baton.reviewer-native, decisions to baton.slaw`; `answer-handoff to baton.reviewer-native in its own scope; no review grant`; created `16:42:56Z` |
| Implementation | `implementation/` | attempt `884fc250…` (`baton.claude-native`, generation 1): provider ended status 0; worker ran the mandatory four-module argv: **Ran 300 tests, OK** (`logs/verification.stderr.log`, 297 verbose `ok` lines + 3 docstring-wrapped, 0 skips); result `candidate`, head `65098f4e9bd6762f44da6b0c7eecb24c6564b25e` on `ac17a5ad`, 7 changed paths; handoff `final-submission` (no clarification request); sealed `completed` at `17:08:54Z` (`sealed.json`: proposal `sha256:61dd6e13…` 64 019 bytes, handoff 69 bytes; findings/logs/response missing-optional) |
| Transition | `views/status-*.json` receipts/episodes; `review/inputs/assignment.json` | review attempt `6132dd1c…` claimed by `baton.reviewer-native`, generation 2, activated `17:09:04Z` — automatic, 10 s after the implementation sealed; no human act |
| Native review | `review/` | provider ended status 0; `findings/report.json` + `findings.txt` (9 109 bytes), `logs/review.json`: `reviewed {base ac17a5ad, head 65098f4e, tree 4ba7382b…}`, **verdict `accepted`**; sealed `completed` at `17:15:36Z` with `result_metadata baton.checkpoint-review/1 {base, head, tree, verdict: accepted}` (`sealed.json`) |
| End state | `views/just-status.txt`, `view-job.txt` | Job `COMPLETED`, both stages `completed`, no cancellation; implementation results `handoff`, `proposal`; review results `findings`, `logs` |

**Binding, candidate → review (verified from retained custody, no store):** `review/logs/review.json` `reviewed.head` == `implementation/proposal/result.json` `head` == `git bundle list-heads objects.bundle` (`65098f4e…`), bases equal (`ac17a5ad`); the review's sealed findings carry the same base/head/tree and the verdict; the review's task document is the same `invocation-ended-wording-1` task with the same four-module verification; the reviewer's own report states it verified `git log` (65098f4e directly on ac17a5ad), the bundle head and the `sha256sum` of the proposal files before judging. The implementation's `sealed.json` proposal content digest `61dd6e13…` is what the review line's checkout carried.

**What the native reviewer ran itself (`review/runs/`, its scratch logs, retained as its evidence, not K's):** required four modules 300/300 OK (`req.log`); `tests.manager.test_exchange` 182 OK (`exch.log`); four neighbouring renderer-importing modules 184 OK (`reg1.log`); `tests.tools.test_stack` 133 with **6 failures** (`reg2.log`, `reg2b.log`) — the reviewer reproduced the identical six on a pristine `ac17a5ad` extract (`snapshot … written -1.0s ago` read as stale, a sandbox mtime/clock artefact) and attributes none to the change; the new tests against base production code 8 F + 27 E (`mut.log`: the defect reproduced verbatim). Its limitations as stated: simulated/real-publisher evidence, no live-provider evidence claimed; the candidate's `verification.txt` carries command + exit only; a terminal stage with no recorded ending still reads `running unknown` (unchanged, outside the named defect); the 19-column duration field.

**Clarification branch:** none occurred (`handoff.json` = final-submission, no `request.json`); no handoff-branch claim.

## 2. The candidate, frozen (`candidate-packet/`)

Reconstructed by applying the retained `change.patch` (sha256 `10045d72…`) to a pristine `git archive ac17a5ad` under `/var/tmp` (dry run and apply clean, `patch-apply.log`); `objects.bundle` (`e67e5b5b…`) lists head `65098f4e… HEAD`. Seven paths, all modified over `ac17a5ad` (`manifest.json` sha256 `aa7161aa…`, `candidate.sha256`; **tree `57dfac01727026e6a3093b5fcff286b1c3535bef060854a68642f8a84db9a247`**):

| path | base `ac17a5ad` | candidate |
|---|---|---|
| `v12/python/JOB-VIEWER.md` | `7b0ac7c8…` | `9177a140…` |
| `v12/python/tests/manager/test_exchange.py` | `eadcd4a8…` | `cc4041ec…` |
| `v12/python/tests/tools/test_job_observation.py` | `6d13d60c…` | `2818e39e…` |
| `v12/python/tests/tools/test_job_viewer.py` | `876aa5ef…` | `5dbca278…` |
| `v12/python/tools/job_observation.py` | `aae42fbc…` | `a78bf165…` |
| `v12/python/tools/job_viewer.py` | `8aaec44c…` | `c6021572…` |
| `v12/python/tools/stack.py` | `3afd8d45…` | `d74753a9…` |

`base/` and `candidate/` hold the bytes; nothing under `src/` changed.

## 3. Import recommendation (drift-checkable; not executed)

`candidate-packet/import/integrate.py` is the independently accepted corrected import helper (M385491, sha256 `bad0b3cf…`) with ONLY its three pins changed (`helper-pins.diff`, 6 changed lines): `MANIFEST_SHA = aa7161aa…`, `TREE = sha256:57dfac01…`, `BASE = ac17a5ad…`; new helper sha256 `135d0163…`. Closed mode/arity, inert `--help`, typo refused (checked: `prefight` → usage, exit 2). Run read-only on the host now: **`PREFLIGHT OK 7 paths; 0 faults`** (`import/PREFLIGHT.json`: `HEAD ac17a5ad`, `v12/` clean, every target a regular owner-writable file at the base bytes with blob == `HEAD`).

Recommended next operator command, after the owner accepts this collection (the native review is the independent review of these bytes; no duplicate model review is requested):
```sh
cd /home/sl/src/baton
/home/sl/src/baton/.venv/bin/python -I -B work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/candidate-packet/import/integrate.py preflight work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/candidate-packet work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/candidate-packet/import
/home/sl/src/baton/.venv/bin/python -I -B work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/candidate-packet/import/integrate.py import   work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/candidate-packet work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-acceptance-invocation-ended-wording-1/candidate-packet/import
```
then `git status --porcelain -- v12` (exactly the 7 ` M` lines in `import/imported-paths.txt`), `sha256sum -c …/import/post-import.sha256`, stage those 7 paths and commit (owner's Git). Separate boundaries after that: bundle/image rebuild for the next qualification, nothing else.

## 4. Observations recorded, not repaired

- **Terminal stages read `running unknown`, `started unknown`** on `just status` and the viewer for both completed stages: the status projection carries `exchange: null` once the runtime is destroyed, so the attributed invocation fact is no longer in the snapshot and the shared interpretation answers unknown (its own honest rule). The provider-process start/end were observed only while the exchange was live. Whether a completed stage should retain its invocation duration in the projection is a product question, not changed here.
- The coordinator's "Job/stage timing unknown" observation during the run is kept as stated; in the final snapshot `control.timing` is `trusted` and the stages say `timeout not applicable (stage ended)`.
- `worker.stderr.log` of both attempts carries the worker's launch-fixture refusals (`spoiled-attempt-…`): those are the tests' own spoiled launch documents under `/scratch` during verification, logged by the worker as refused — expected noise from the mandatory suite, not a fault of this Job.

## 5. Retained files

`implementation/` (proposal: result.json `827b803c…`, change.patch `10045d72…`, objects.bundle `e67e5b5b…`, verification.txt; sealed.json `55e4f802…`; handoff/handoff.json; inputs assignment/task/handoff; logs provider/worker/verification + statuses), `review/` (findings/report.json + findings.txt, logs/review.json, sealed.json, inputs assignment/task, runs/ the reviewer's six scratch logs, launch-logs/), `views/` (status snapshot, just status, viewer detail, log locators ×2, attempt-diagnostics), `instance/`, `candidate-packet/` (base, candidate, manifest, listing, patch-apply log, import/). Logs scanned for credential-like strings: none. Digests in `evidence.sha256`.
