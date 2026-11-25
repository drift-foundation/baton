# Shortest path to Codex implementation → Claude review

## Route

Use the supported operator stack in a fresh qualification instance, not another bespoke launcher.

- The Q4 question asks for "normal composition/entrypoint" (`../native-readiness-386143/PLAN.md:63`). A review stage needs the composed deployment: line, frozen checkpoint, review attachment, receipts, routes and grants. The stack's bootstrap provisions all of that; a launcher would have to re-implement it.
- The composed path with selected providers is covered deterministically at `b5abf798`: `tests/tools/test_provider_selection.py` (implementation and review bind their own evidence; simulated Codex and Claude lanes admit in one Job; separation class computed) and `tests/tools/test_stage_execution.py::OrdinaryReviewUncertainty`.
- Reused unchanged: source `b5abf798`; Codex image `sha256:2c982530412d6811cfa6aa2e28181f859cc2a9fb2e4372f29d88784763dbe693` with bundle `55d58a10…`; Codex selection gpt-6-astra / `codex-pushcoin-subscription`; the Q2 task shape (one file, one fixed verification).
- New: one Claude image (current `claude_agent.py` bytes are in no existing image) and one instance.

Status of the commands below: operand names are taken from `v12/STACK.md` and from `--help` run on the frozen source (`pool compose-worker`, `manager create`, `worker_image`, `manager review-uncertainty-items`). I have not executed them; every one needs a build. Selection A exercises all of them offline. Values in capitals are filled from the step that produces them.

## Selection A — offline: image, inventory, instance (no credential, no provider)

Prerequisites: decisions D1–D3; clean export of `b5abf798` at `$SRC` (for example `git archive` into a fresh directory outside the checkout); fresh destination `$DEST` outside the checkout; Docker available; uid:gid 1000:1000.

1. Build the Claude image with the product's own tool.
   ```sh
   cd $SRC/v12/python && PYTHONPATH=src /home/sl/.local/state/baton-v12-venv/bin/python -m tools.worker_image --context $SRC/v12 --dockerfile $SRC/v12/worker/Dockerfile.claude --tag baton-v12-claude-worker:b5abf798
   docker image inspect baton-v12-claude-worker:b5abf798 --format '{{.Id}}'      # -> CLAUDE_IMAGE
   ```
   Accept: one build, exit 0, one image id. No fallback build.
2. Offline inventory of that image (network none, read-only, no mounts, no credential).
   ```sh
   docker run --rm --network none --read-only --user 1000:1000 --entrypoint claude CLAUDE_IMAGE --version
   docker run --rm --network none --read-only --user 1000:1000 --entrypoint claude CLAUDE_IMAGE --help
   docker run --rm --network none --read-only --user 1000:1000 --entrypoint sh CLAUDE_IMAGE -c 'cd /opt/baton && find . -type f | sort | xargs sha256sum'
   docker image inspect CLAUDE_IMAGE --format '{{json .Config.Entrypoint}} {{.Config.User}}'
   ```
   Accept: version is exactly 2.1.247 (C1); help lists `--print`, `--output-format`, `--model` and `--dangerously-skip-permissions` (C2 surface); every `/opt/baton` file hash equals the same file in `$SRC` (including `claude_agent.py`, `provider_policy/` and `verifier-layout-marker.json` = `3355c11a…`); entrypoint is `python3 /opt/baton/dogfood_entry.py`. If `--version` cannot run on a read-only root, record that and rerun that one command with `--tmpfs /tmp`; it is not a pass by itself.
3. Install the instance (this builds the one-folder runtime from `$SRC`; it is a build, not a provider or engine operation) and compose two workers: implementation = Codex, review = Claude. No integration worker: the deployment document requires only those two roles (`tools/stage_execution.py:1052`), so an integration stage, if the template submits one, has nobody to run it and stays blocked.
   ```sh
   cd $SRC/v12 && just bootstrap $PREP/instance.json $DEST
   $DEST/distro/baton-v12-stack pool compose-worker --deployment $DEST/deployment.json --worker-id impl-codex --role implementation --participant qualification.codex \
     --image-reference sha256:2c982530412d6811cfa6aa2e28181f859cc2a9fb2e4372f29d88784763dbe693 --image-digest sha256:2c982530412d6811cfa6aa2e28181f859cc2a9fb2e4372f29d88784763dbe693 \
     --cli-build 0.169.0 --provider codex --requested-model gpt-6-astra --reported-identity gpt-6-astra --network bridge \
     --credential-sources REGISTRY --credential codex=operator-file:codex-pushcoin-subscription --workspace-group 1000 \
     --task-document $DEST/state/task/installed-task.json --record RECORD --checkout /home/sl/src/baton --verifier-layout $SRC/v12/worker/verifier-layout-marker.json --into $PREP/workers/impl-codex.json
   $DEST/distro/baton-v12-stack pool compose-worker --deployment $DEST/deployment.json --worker-id review-claude --role review --participant qualification.claude \
     --image-reference CLAUDE_IMAGE --image-digest CLAUDE_IMAGE --cli-build 2.1.247 --provider claude --requested-model D1_SELECTOR --reported-identity D1_IDENTITY --network bridge \
     --credential-sources REGISTRY --credential claude=D2_REFERENCE --workspace-group 1000 \
     --task-document $DEST/state/task/installed-task.json --record RECORD --checkout /home/sl/src/baton --verifier-layout $SRC/v12/worker/verifier-layout-marker.json --into $PREP/workers/review-claude.json
   just --justfile $SRC/v12/justfile bootstrap $PREP/updated-inputs.json      # instance.json + state_root=$DEST + copied derived paths + workers + native_handoff_routing
   just --justfile $DEST/justfile start && just --justfile $DEST/justfile status && just --justfile $DEST/justfile stop
   ```
   `updated-inputs.json` carries `"native_handoff_routing": {"reviewer": "qualification.claude", "decision_recipient": "baton.slaw"}`.
   `REGISTRY` is the private credential registry path; composition records the path and reference names, and I do not open the file. `RECORD` is the repository-relative record the Job is bound to; a small dedicated qualification record is prepared with `instance.json` before this step.
   Accept: every composition exits 0 and writes a fresh worker document; the review worker document carries the D1 selection, credential mode `delivered`, and the marker; the repeated bootstrap exits 0; `start` comes up and `status` shows zero Jobs and two configured workers; `stop` leaves no container (`docker ps -a` shows none with this instance's labels). No provider process, no credential read.
4. Reviewer confirms the retained outputs of steps 1–3 and writes the exact selection B commands with the real `CLAUDE_IMAGE`, worker documents and Job id.

Anything that refuses in step 3 is a finding to correct before B. It costs no provider call. This is where the unexercised commands are proved.

## Selection B — live: one Job, two provider turns

Prerequisites: selection A accepted; D4 answered.

1. Create the Job (task as in Q2: change `message.txt` from `before` + newline to `after` + newline; verification `python3 -I -c "from pathlib import Path; assert Path('message.txt').read_bytes()==b'after'+bytes([10])"`), with the D3 limits. The provider-turn ceiling is one value per Job, so it is the reviewer's 600 s for both turns.
   ```sh
   $DEST/distro/baton-v12-stack manager create --instance $DEST --control $DEST/db/control.sqlite3 --authority $DEST/db/authority.sqlite3 --task q4-codex-claude --statement "…" --acceptance "only message.txt changes to after plus newline" --work-scope message.txt \
     --provider-turn-seconds 600 --verification-command-seconds 15 --verification python3 --verification=-I --verification=-c --verification "from pathlib import Path; assert Path('message.txt').read_bytes()==b'after'+bytes([10])"
   just --justfile $DEST/justfile start
   ```
   Store file names under `$DEST/db/` are read from `$DEST/deployment.json` in selection A; the names above are placeholders.
2. Watch until the review stage settles or the wall bound passes, then stop. Completion is read the same two ways as in part 1: a transient exchange terminal, or a durably completed stage whose custody binds to its attempt. Never from elapsed time.
   ```sh
   just --justfile $DEST/justfile status
   $DEST/distro/baton-v12-stack manager review-uncertainty-items --jobs JOB_STORE --authority-uuid AUTHORITY_UUID
   just --justfile $DEST/justfile stop
   ```
3. Stop as soon as the review stage is `completed` or held. No integration worker is configured, so no integration provider call can happen.

Acceptance for B (judged by a separately authorized review of retained evidence, not by exit status):

| Check | Evidence |
| --- | --- |
| Codex stage completed; exact candidate in custody; only `message.txt` changed to `after` + newline | Stage status, frozen result, checkpoint. |
| Codex configured-model record and launched image `2c982530` bound | Model attribution on the stage; image receipt. |
| The reviewer received that exact checkpoint, read-only | Review attachment checkpoint id equals the implementation checkpoint. |
| Claude ran on 2.1.247 from `CLAUDE_IMAGE` with the D1 selector, no refusal or substitution (C2, C3) | Review stage attribution; image receipt. |
| `modelUsage` present and contains the D1 identity (C4, C5) | Attribution outcome `matched`; all contributors retained. |
| Reviewer role label and worker-instruction digest reported | Stage runtime line. |
| Outcome is exactly one of: a verdict recorded by the manager from the reviewer's own report, or an uncertainty owner item addressed to `baton.slaw` with no verdict | Verdict record, or `review-uncertainty-items`. |
| No retry, no correction round, no integration turn; one container per role | Engine start count; stage episodes. |
| Both containers ceased and removed; delivered Claude credential withdrawn; Codex home retained; no source writeback | Cleanup receipts; `docker ps -a`. |

If the review is uncertain: the Job stays held, the owner item is the handback, and the instance is stopped. There is no owner continuation command yet; that is product follow-up, not part of this qualification. If attribution is missing or conflicting, the manager holds and records no verdict; that is a failed C-requirement, not a retry.

If D4 is yes: after the first Job's review settles, create a second Job in the same instance whose acceptance criterion cannot be decided from the candidate, start, and read the queue. One more Codex turn and one more Claude turn.

## What stays unqualified after B

Conversation resume, same-provider login sharing, more than one Job at a time, integration and publication roles, owner continuation after uncertainty, and independent attestation of the in-container mounts.
