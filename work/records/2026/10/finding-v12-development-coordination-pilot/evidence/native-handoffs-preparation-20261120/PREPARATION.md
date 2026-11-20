# W385331 — smallest native executable slice: gap assessment, focused tests, ordinary kickoff (K, M385333)

Prepared by baton.prompt (K) under the owner-held W321608 interactive arrangement; K holds no claim on W385331 (queued, route rview → baton.rvpc, handler null), so this packet lives in the pilot dossier and only references `work/records/2026/11/finding-v12-native-agent-handoffs-discovery/`. Inputs read: T321608 M385333, T385331 M385331, W385331 FINDING/PLAN, DESIGN SCH-2a (uncommitted edit in the working tree), current source at HEAD `45141ac6` (labels checkpoint), the native-labels-5 kickoff record (`evidence/native-labels-5-failure/DIAGNOSIS.md`) and the reusable-kickoff packet. Nothing was executed, built, installed, launched or edited in product source.

## 1. Current runtime coherence (what "a coherent current runtime" requires)

| fact | value |
|---|---|
| HEAD | `45141ac6` (labels checkpoint); `v12/` tree clean |
| uncommitted | `v12/DESIGN.md` (SCH-2a), pilot FINDING/PLAN entries, untracked W385331 dossier |
| host bundle `v12/python/build/out/distro` | exe sha256 `1265b1ff…`, stamp `86c1c22b dirty` (built from the imported tree, i.e. 45141ac6 bytes, before the commit; `changed_entries` counts dossier files) |
| retained instance `/home/sl/baton-instances/native-labels-5` | pinned to the d8f77700 bundle `0f75ae9a…`, runtime digest `59df90fa…`; workers impl-a (`baton.claude-native`) / review-a (`baton.reviewer-native`); untouched |

A coherent current runtime for this slice is: (1) Slawomir checkpoints SCH-2a + the W385331 dossier (+ this packet) so the stamp is clean; (2) `just build` from `v12/` → bundle stamped at that checkpoint, `dirty: false`; (3) a NEW instance (`native-handoffs-1`) installed from that bundle with the instance-only document (same shape as `config/native-instance-e670e624.json`, new `state_root`, `line_declared_base`/`canonical_target_id` = the checkpoint), two workers composed with the installed `pool compose-worker --like` the d8f77700 worker documents and the owner-built worker image (`sha256:f2b86df0…`, qualification per the labels lessons: verifier layout, disk-backed `/scratch` root, image/layout match). The retained instances are not updated. Slice 1 source is implemented through v12 on that instance; its candidate is then reviewed, imported and checkpointed exactly as the labels slice was.

## 2. What exists and is reused (no second identity/routing system)

- **Identities, routes, capabilities**: `tools/bootstrap.py` `ROUTES = {implementation: impl, review: rview, integration: integration}`, `add_route_handler(route, participant)` per worker, receipt participants (verification/review/approval/integration) and capabilities `verify`, `review`, `approve`, `integrate`, `close`, `manage-work-labels`; `Session` is participant-bound and whitelists exactly `claim, end, pass_work, route_fenced, cancel, reject_plan, install_gate, satisfy_gate, advance_contract, activity, publish, verify, review, approve, integrate, close, settle_operation, label_work, unlabel_work`. Phases `queued/active/block/parked`; gates `runtime-quiescence`, `contract-runtime`, `plan-revision` (closed `GATE_KINDS`).
- **Worker/host protocol** (`worker-control-1.0`, frozen asset): result disposition `{completed, unable, plan-rejected, cancelled}` (closed), result `summary` ≤16000 + `evidence[]` + declared outputs; activity kinds `{step-started, step-completed, action, evidence, retry, blocker, handoff-preparation}` with `summary` ≤16000. The reviewer worker emits a `findings` artifact `baton.review-report/1 {verdict, findings}` (`v12/worker/claude_agent.py`).
- **Review → correction handoff (already courier-free inside one Job)**: `review_driver.review_verdict_from_result` reads the verdict from the frozen output; `end_review_from_result` maps `accepted → accepted`, `changes-requested → correction`, anything else `held`; `stage_execution._finished/_handed_off/_next_route` route-fence the Work to the worker's `review_route` or, for a correction, back to the producer's committed claim route; `deployment.routed` → `review_driver.open_correction`; the correction round restores the retained `findings` text to the implementer (`provider_context`, `MAX_FEEDBACK_BYTES`). Proven by `tests/job_manager/test_review_driver.py`, `tests/tools/test_joined_workflow.py` (real `serve_exchange` turns, fake agent), `tests/tools/test_correction_restart.py`.
- **Projection/status**: `tools/job_observation.py` states `blocked/queued/…/changes-requested/completed/exceptional`; `held` renders `exceptional`.
- **Dossier/disposition CLI**: `record bind/read/cite/verify`, `disposition pending/approve/deny/integrated/close`, `work labels…` — the conventions a new verb follows.

## 3. Gaps (concrete, by file) — the missing agent-facing transitions

| # | missing transition | where it is absent today |
|---|---|---|
| G1 | **Yield**: an implementer ends a turn with a retained candidate + continuation + a finding needing disposition, distinct from completion/failure | worker-control disposition enum is closed; `end_review_from_result` knows accepted/correction/held only; `job_observation` has no `yielded` state |
| G2 | **Reviewer discovery disposition** (continue / nonblocking / blocking / decision) as a durable, attributable receipt | `authority/schema.py` `receipt.kind CHECK IN ('verification','review','approval','integration')`; `core._write_receipt` valid sets; no `dispose-discovery` capability; no `discovery_disposition_from_result` reader; reviewer worker has only `baton.review-report/1` |
| G3 | **Prerequisite hold**: block the yielding Work on another Work's ACCEPTED outcome; rejected/cancelled never satisfies; containment is not a dependency | `GATE_KINDS` closed (3 kinds); `satisfy_gate` evidence kinds `quiescence/contract-runtime/revised-plan` only; no Work→Work edge (Job `depends_on` is stage-internal; SCH-5 accepted base is a human act via `tools/accepted_base.py`) |
| G4 | **Filing Work from a disposition** (nonblocking or blocking) without a worker Work-creation service | `create_work` exists only on the trusted `Authority` face (`core.create_work`, used by bootstrap and `creation.py`); nothing creates/links a Work from a reviewer's recorded disposition; linkage (`follow_up_of`/`blocking`) has no v12 column |
| G5 | **Resume with continuation**: on satisfied gate, re-open the producer's round carrying the retained candidate + disposition text | `open_correction` is bound to a `changes-requested` verdict (`provider_context` 816-824, 1135-1193 compare `verdict["disposition"] == "changes-requested"` and read the `findings` artifact) |
| G6 | **Durable Work/Job messages and receipts** (clarification request/answer, notes, candidate/evidence refs) readable by agents and humans | no message table in the Authority; only `pass_work(comment)`, `install_gate(reason)`, `reject_plan(reason)` carry one text; `activity` rows carry an `action_key` only; the host ingests worker activity as **bytes** (`attempts.observe_activity(bytes_observed)`, `single_worker._ingest`) and discards the `blocker`/`handoff-preparation` summaries; v11 `say` is the only messaging and is transitional |
| G7 | **Clarification vs review vs correction as distinct transitions** | only "end the attempt" exists; a question cannot be asked without ending as `unable`/`plan-rejected` |

Answer to the PLAN's research question: the current worker return protocol CAN carry a yielded finding **without a wire change** — a `completed` result whose declared outputs include a `discovery` artifact (`baton.discovery-report/1 {schema, finding, continuation, candidate_ref}`) beside the frozen checkpoint; the host, not the worker, turns that into the yield (Option A). An explicit `yielded` disposition (Option B) needs worker-control 1.1: frozen asset bytes, `contracts/frozen.REQUIRED_ASSETS`, `v12/worker/baton_worker.DISPOSITIONS`, `tests/manager/test_contracts_inventory`, the bundle gate. Recommend A for slice 1 and record B as an owner vocabulary decision, not a prerequisite. Host disposition/messaging belongs in the Authority (receipts, gates, messages) with the Job manager composing the acts (`review_driver`/`stage_execution`), exactly where review/correction live today.

## 4. Slice 1 — "reviewer-dispositioned discovery with prerequisite hold" (the smallest executable slice)

Scope (one Job pair, existing participants/routes/claims): G1(A) + G2 + G3 + G4 + G5. `decision` maps onto the existing `reject_plan`/`plan-revision` gate (owner satisfies with a revised task digest) — no new code beyond the mapping. Messages (G6/G7) are slice 2.

Executable changes (bounded, by owner module):
1. Authority (`authority/schema.py`, `core.py`, `identity.py`, `session.py`, `__init__.py`): receipt kind `discovery` with dispositions `{continue, nonblocking, blocking, decision}`, capability `dispose-discovery` (granted to the review participant at bootstrap beside `review`), one per proposal, replay/collision as other receipts; gate kind `work-prerequisite` (detail = prerequisite `work_id`) with satisfy evidence kind `accepted-prerequisite {work_id, proposal_id, approval_id}` checked against that Work's committed `approval: approved` receipt in the same Authority; `work.follow_up_of`/`blocking` link columns written with the filed Work. Schema migration under the existing versioning.
2. Worker contract (`v12/worker/claude_agent.py`): implementation outputs may include `discovery` (`baton.discovery-report/1`); review outputs may include `disposition` (`baton.discovery-disposition/1 {disposition, rationale, filed_work: {work_id, title, labels}?}`); the prompt text names the four dispositions. No worker-control schema change.
3. Job manager (`job_manager/review_driver.py`, `stage_execution.py`, `projection.py`, `tools/job_observation.py`): detect the `discovery` artifact at the implementation ending → attach the reviewer with the discovery contract (same attachment mechanism); `discovery_disposition_from_result` sibling reader; ending outcome `disposed:<kind>`; acts in order and replayable: `continue` → open round with rationale as feedback; `nonblocking` → trusted `create_work(filed, impl route, labels, follow_up_of)` then round; `blocking` → `create_work(prereq, …, blocking=yielder)` + `install_gate(yielder, work-prerequisite:<prereq>, expect=live assignment)` → phase `block`, line/checkpoint retained; scheduler tick: prerequisite approved → `satisfy_gate` → Work queued on the producer's claim route → round carrying candidate + rationale; rejected/cancelled prerequisite → hold stays, status says why. `decision` → `reject_plan(task digest, rationale)`. Projection states `yielded`, `blocked (prerequisite W…)`.
4. CLI (`tools/stack_command.py` + one new `tools/discovery_command.py` following `disposition_command` conventions): `discovery pending|read` (read-only) and, for a human reviewer, `discovery dispose --participant … --proposal … --disposition … --rationale … [--file-work …]` through a participant-bound Session; `satisfy` is NOT a verb (the manager derives it from the approval receipt).

Focused verification (groups `authority`, `job_manager`, `tools-pure`; `tools-packaged` only at the host gate; `scans` untouched because no frozen asset changes):
- `tests/authority/test_operations.py` (+ `test_store` migration): discovery receipt kind/capability/one-per-proposal/replay/collision; `work-prerequisite` gate install (claimed and unclaimed, stale `expect` compared), satisfy only by the named Work's `approved` receipt, `rejected`/`denied`/cancelled never satisfies, containment/label never satisfies, unknown-kind refusal unchanged.
- `tests/job_manager/test_review_driver.py` (`DriverCase`): discovery ending → each of the four dispositions performs exactly its acts in recorded order; re-entry from every cut point (after receipt, after create_work, after install_gate) writes nothing twice; exact replay returns the same successors; a disposition about another checkpoint is refused.
- `tests/tools/test_joined_workflow.py` (`JoinedWorkflowCase`, real `serve_exchange` turns with the scripted agent): one created Job yields a discovery → reviewer `blocking` → Work `block` with the prerequisite linked and the candidate/continuation retained → owner approves the prerequisite's proposal → Work resumes on the producer's route, the round is served the retained candidate + rationale → completes; `nonblocking` and `continue` variants; `rejected` prerequisite keeps the hold; status/viewer render `yielded` and `blocked (prerequisite …)`.
- `tests/tools/test_correction_restart.py`-style restart proof: manager restart between the receipt and the gate installs no second Work and no second gate.
- `tests/tools/test_discovery_command.py` (new module, registered once in `tools-pure`): verbs, read-only reads, participant binding, refusals.
Declared in the handoff per TESTING.md; `just test-one`/`test-group` from `v12/`; disk-backed roots outside the checkout (`/var/tmp/...`), never under `work/scratch`.

Acceptance for slice 1 (from the FINDING, bounded): the implementation yields without claiming completion; the reviewer's disposition durably decides continue/file/hold; blocking creates and links the prerequisite and installs the gate coherently in one replayable sequence; only the prerequisite's accepted outcome releases the hold; restart/replay preserves messages-in-receipts, exact candidate, ownership and gates with no duplicate Work/effects. Not in slice 1: clarification transition, Work message table, worker-control 1.1 vocabulary, any backlog migration, automatic host integration, privileged containers, worker store access.

## 5. Slice 2 — durable Work messages and clarification (after slice 1 is reviewed)

Authority `work_message(seq, work_id, author participant, kind {clarification-request, clarification-answer, note, handoff}, body ≤16000, refs[], operation_id, at)` + read receipts; Session transition `say_work`; host persists the worker's `blocker`/`handoff-preparation` activity summaries as messages (host-mediated, no store access); CLI `message say|read`; clarification = yield with disposition `decision` answered by a message that revises the task digest. Owner decision needed first: whether a clarification answer may change the task digest without a new Job identity (SCH-2a says it does not approve code or revise the specification).

## 6. Ordinary kickoff commands for slice 1 (prepared; NOT executed; live run requires the coordinator's run selection)

Same supported path as the labels run (`evidence/native-labels-5-failure/DIAGNOSIS.md` §exact owner commands), on the new instance:

```sh
DEST=/home/sl/baton-instances/native-handoffs-1          # installed from the clean checkpoint bundle (section 1)
BIN="$DEST/distro/baton-v12-stack"; UUID=$(python3 -c 'import json;print(json.load(open("'$DEST'/authority-identity.json"))["authority_uuid"])')
STMT=/home/sl/src/baton/work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-preparation-20261120/task-statement.txt
"$BIN" stop --instance "$DEST/instance.json"             # instance guard: no create while serving
"$BIN" manager --store "$DEST/db/jobs.sqlite3" --incarnation slaw-create-handoffs-1 --authority-uuid "$UUID" \
  create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" \
  --task w385331-discovery-1 --job-id w385331-discovery-1 --statement "$(cat "$STMT")" --label w385331 --label discovery \
  --acceptance "An implementation yields a retained candidate with a discovery needing disposition without claiming completion." \
  --acceptance "Reviewer dispositions continue/nonblocking/blocking/decision are durable receipts; blocking links the prerequisite and installs the work-prerequisite gate atomically; only the prerequisite's approved outcome releases it." \
  --acceptance "Restart and exact replay preserve candidate, continuation, ownership and gates with no duplicate Work or effects; focused tests pass with no required skips; independent review and human integration remain required." \
  --work-scope v12/python --work-scope v12/STACK.md --work-scope v12/worker \
  --test-scope v12/python/tests --test-scope v12/python/tools/parallel_test.py \
  --control-profile documentation/1 \
  --verification env --verification BATON_V12_STACK_TEST_ROOT=/scratch --verification BATON_V12_DISK_ROOT=/scratch \
  --verification PYTHONPATH=v12/python/src:v12/python --verification python3 --verification=-m --verification unittest --verification=-v \
  --verification tests.authority.test_operations --verification tests.job_manager.test_review_driver \
  --verification tests.tools.test_joined_workflow --verification tests.tools.test_correction_restart --verification tests.tools.test_discovery_command
"$BIN" start --instance "$DEST/instance.json"; "$BIN" status --instance "$DEST/instance.json"
```
Preconditions: clean-stamp bundle; new instance installed and `status` healthy with zero Jobs; worker image/layout verified as for labels; `--label` and `work` verbs exist only on the 45141ac6-or-later bundle. `task-statement.txt` (beside this file) is the slice-1 statement. Per the labels lesson: the verification names the disk-backed container root; no create-while-serving.

## 7. Limits

No build, install, instance, Job, container, provider, Git mutation or product edit was performed. Counts/durations are not estimated. W385331 remains queued on `rview` for the reviewer's first research; this packet is input to it, not a claim.

## 8. Addendum — owner-interruption boundary (T321608 seq 385335; pinned in W385331 FINDING "2026-11-20 — owner-interruption boundary", PLAN "Acceptance clarification — human interruption", DESIGN SCH-2a continuation)

The clarification changes slice 1 in four places and adds two acceptance demonstrations; it adds no new mechanism.

1. **`decision` is a role transition before it is an owner gate.** A discovery the reviewer cannot classify from accepted design is NOT sent to the human first. The reviewer records `decision` with the exact ambiguity, evidence, options and a recommendation (in the `baton.discovery-disposition/1` rationale) and the Work is routed to the configured decision role (`rview` today — the reviewer participant holds `dispose-discovery`; a separate `decide` route is only configuration, `bootstrap.ROUTES` + `add_route_handler`). Only when that role records that accepted authority does not determine the answer does the host install the owner gate (existing `reject_plan` → `plan-revision`, satisfied by the owner's revised task digest). Projection: `awaiting decision (role)` vs `blocked (owner decision)`. Nothing invents a policy answer: a `decision` disposition without options/recommendation is refused by the reader.
2. **No acknowledgment gates.** `continue`, `nonblocking` and the gate release are performed by the manager on the recorded receipt alone; no `mark-seen`, no human relay, no renewed confirmation. Retries within the control profile's correction allowance (`correction_policy`, `documentation/1` limits) stay governed by that profile, not by a question. Progress is observable through `status`/the viewer states (`yielded`, `awaiting disposition`, `awaiting decision`, `blocked (prerequisite W…)`, `blocked (owner decision)`) and the Authority receipts/gate evidence.
3. **Owner actions are consolidated into one prepared list**, asked once, not per step: (a) checkpoint SCH-2a + W385331 dossier + this packet (commit message below); (b) `just build` from `v12/` on that checkpoint; (c) install `native-handoffs-1` from the instance-only document and admit the two composed workers (commands in §6 preamble and the reusable-kickoff packet); (d) select the live run with the §6 `manager create`. Git, instance installation and live-run selection are the three explicitly reserved owner acts; everything else in slice 1 is agent/system work.
4. **Slice 2 clarification routing follows the same rule**: a worker's routine question travels (host-mediated message) to the reviewer/decision role first; the human is reached only when that role records it cannot resolve the question from accepted authority.

Added acceptance demonstrations for slice 1 (PLAN clarification), both deterministic in `tests/tools/test_joined_workflow.py`: one design-resolvable discovery (e.g. a test-scope path question answered by the accepted scope) is classified `continue`/`nonblocking` and the Job completes with zero human acts; one genuinely ambiguous design discovery is recorded `decision` with evidence/options/recommendation, routed to the decision role, and only then blocks on the owner gate — the test asserts the Work never reached the owner gate before the role's record, and that no policy answer was invented.

Proposed owner commit message for (a):
```
Pin W385331 native handoffs/discovery scope and owner-interruption boundary

DESIGN SCH-2a: native messaging, explicit handoffs, reviewer-dispositioned
discovery with dependency-gated resumption; routine transitions proceed
without human relay. Create the owning dossier and record K's slice-1
preparation (gap assessment, focused tests, ordinary kickoff) under the pilot.
```
