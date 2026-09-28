# B1 correction checkpoint — partial implementation, connected proof blocked

Author baton.tuner, claim291848, owner291841 selecting B1-SCOPE-PROPOSAL-20260928.
Only the four selected baseline/composer/test paths changed outside this dossier.
Pre-edit diff was empty. No G2/product/prepare_instance/two-job helper edit.
Owner291841 supersedes the older PLAN/proposal awaiting-path-selection status;
reviewer should refresh its current PLAN on pickup from this checkpoint.

## Implemented contract

Historical default context_mode=contextual and packet/1 remain. Explicit
context_mode=fresh requires nonempty task_instructions and verification argv,
emits packet/2 with context={mode:fresh}, plain worker /4, proposal-only output,
no emitted context profile or receipt declaration, and no context-storage,
certification or qualification grant. Task and policy hashes are derived normally;
fresh verification ceiling is 30 seconds in both policy and submission. Existing
one-implementation/no-retry bound and all proposal/attribution/cleanup checks remain.

Reader rejects mode/deployment/submission confusion before any store/engine effect.
Fresh workload evidence independently checks absence of context invocation;
unreadable or unexpected context is a shortfall. It still requires measured retained
proposal and attribution; fresh mode does not make those checks optional.
Fresh write refuses an existing destination without replacing any packet bytes.
Historical write behavior is unchanged. No runtime lifecycle code was modified.

Fresh write emits commands.json with literal start/status argv, selected environment,
outcome path and submission ownership. Existing baseline.main owns submission once;
do not also execute manager submit. Existing termination handling remains and does
not turn unresolved cleanup into success. No new supervisor was copied or forked.

## Operator shape, pending final candidate acceptance

In the already selected selections.json compose object add:

```json
{
  "context_mode": "fresh",
  "task_instructions": "the exact reviewed task text",
  "verification": ["python3", "harness.py"]
}
```

Those are literal key names; the instruction text/verification must be bound to
the actual useful task and immutable source at packet freeze, not this example.
Other existing selections stay required, including exact image/runtime/source,
Work/principals, profile evidence and full source revision. prepare_instance.py
remains the supported, unchanged preparation step after bootstrap identity exists.

```sh
PY=/home/sl/.local/state/baton-v12-venv/bin/python
PACK=/home/sl/baton-runs/single-job-257627-291715
BOUND="$PACK/manager-source"
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-single-implementation-proof
export PYTHONPATH="$BOUND/src:$BOUND"
export PYTHONDONTWRITEBYTECODE=1
"$PY" -B "$DOSSIER/prepare_instance.py" --selections "$PACK/selections.json" --base "$BASE"
"$PY" -B "$DOSSIER/baseline_bindings.py" --selections "$PACK/selections.json" --base "$BASE" --run-root "$PACK/run"
"$PY" -B "$DOSSIER/baseline.py" --packet "$PACK/run/PACKET.json" --incarnation single-job-257627-291715
```

BASE is the exact resolved source object, never a placeholder at execution.
Generated commands.json carries final paths/UUID rather than shell placeholders.
Status/log surfaces remain those in SINGLE-JOB-PACKET-20260928.md. This supersedes
its *source-level absence* of a bounded fresh entrypoint, not its NOT-LAUNCHABLE
status: B1 connected acceptance and B2–B5 remain pending. Final command must pin
these helper bytes too; do not execute mutable checkout helpers in a frozen run.
No preserved instance was prepared, submitted or run here.

## Verification actually performed

AST selector preflight covered the four changed modules and the explicit methods;
reviewed fixture engine/provider seams and disk_roots selection. Existing inherited
fixtures use disposable local Git repositories, fake engine/provider and public
Authority/manager APIs; no repository Git index/history was changed. Existing
worker test imports clean their own worker bytecode cache; no new cleanup added.
Disk scratch is this dossier's scratch directory, with test-owned child cleanup.
No live engine/provider, production credential or deployment accessed.

Exact passing command is B1-FOCUSED-291848.sh: 14 explicit selectors, 29 tests
PASS in0.335s. Includes generated composer main, generated start argv's mixed-mode
refusal before store/image access, actual stack logs command missing-room readback,
context grant/certification exclusion, packet/submission guards, admission/cap
regressions, and historical contextual config/reader checks. The command-entrypoint
refusal test is not a successful runtime run. Status argv was generated/source-checked,
not a connected status acceptance. New tests are not evidence of final B1 success.

Earlier measured runs: 5 tests0.428s (4pass/1connected fail); fresh connected retries
0.313s,0.347s,0.343s (each1fail, added public diagnostic readback); historical connected
positive0.289s (1fail); first focused set28 tests0.267s (27pass/1new log expectation
failure); corrected focused28 tests0.271s PASS; final29 tests0.335s PASS.
Known unittest time this claim2.593s. No campaign-total reconstruction. The new log
case initially expected absent; actual reader correctly reports inaccessible with
FileNotFoundError for an unopenable room. Corrected to assert that exact result and
all stream states, preserving the no-empty-success requirement.

## Exact connected blocker — do not bypass

`test_baseline_bindings.TheFreshPacket.test_fresh_positive_one_proposal_without_context`
remains an ordinary failing test in the module; no skip/xfail or weakened success
expectation. It reaches real composed host preparation, one admission, then
exceptional/not-started and held with no frozen result/proposal and outstanding
cleanup. Public attempt_preparation_failure_of reports:

> adopting this attempt's workspace roots is refused: host preparation 1 ... was
> admitted and has recorded no completion, so a preparation writer may still be
> creating, staging, publishing or freezing ...

Observed caller boundary: tools.single_worker._prepared calls _mounted after
preparation admission; composed stage mount reaches workspaces' adopted-root
boundary (workspaces.py symbol with message “adopting this attempt's workspace
roots”). Active G2 owns these shared paths. This is a connected reached-consumer
finding, not proof the guard itself should be relaxed. The historical contextual
positive also returns exceptional/held before a provider context or result, so
fresh context removal alone does not explain the blocked positive composition.

Next independent reviewer action: inspect the four-path candidate and this evidence,
coordinate this exact preparation/adoption gap with W285465 or its explicitly
selected consumer owner. No tuner fifth-path authority, no active-claim takeover,
no fake preparation completion or mock around the guard. Once corrected/accepted,
resume the retained fresh positive test and literal generated start/status/outcome
with fake engine/provider, then interruption/deadline/access preservation checks
on that connected path. Finish B1 acceptance before claiming its blocker cleared;
finish exact provider/candidate freeze/rehearsal before any live selection. Existing
packet/graph residuals remain; no new owner gate on ordinary continuation.
