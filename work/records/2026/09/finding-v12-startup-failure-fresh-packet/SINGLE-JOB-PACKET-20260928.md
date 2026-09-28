# W257627 — one useful Job draft, not launchable

Owner291710; author baton.tuner claim291715. This is packet preparation in parallel
with active W285465, not a candidate freeze. D1 and the declaration correction are
accepted historical inputs (reviews 2026-09-24T15-06-15Z and 16-25-54Z). No new
engine/provider execution, build, deployment or product change occurred here.

## Selected intermediate result

One fresh implementation Job proposes docs/v12-first-job-inspection.md from the
immutable task and excerpts named in INPUTS-20260928.json. It performs useful
operator-documentation work without modifying shared source. The host collects
correlated, measured output and a separate reviewer evaluates the exact retained
proposal. One provider invocation, no automatic retry, no context reuse, no
integration, no second Job. This does not prove independent parallel adoption.
The proposed Git profile requires a prepared isolated source revision; no Git
repository was created or changed here. Do not substitute an existing consumed run.

CANDIDATE-20260928.json pins observed files, not an accepted transitive runtime.
The historical c862c055 image and adapter hash are exact provenance, not a current
image selection. The current adapter still declares PROVIDER_UMASK=0o077; that
alone neither proves nor disproves required host access under the final UID/GID
arrangement. Verify actual produced modes/access on the selected path; never repair
them with a helper or host chmod/chown. Image/source changes, if necessary, need
an owned candidate and separately selected build. No new image is presumed needed
merely for the accepted declaration correction.

## Isolation and immutable inputs

Reserve absent paths `/home/sl/baton-instances/single-job-257627-291715` (stores,
workspace and launch evidence) and `/home/sl/baton-runs/single-job-257627-291715`
(packet, immutable runtime, nominated source and evidence). They have not been
created or admitted. Before effects, prove absence and canonical parent ownership,
no symlink/alias overlap with each other, the checkout, credentials, v11, or any
consumed instance. An occupied path requires a new identity and regenerated packet;
never clear it or reuse a grant. Preserve two-jobs-251156 and both W257624 residue
inventories unchanged. Keep credentials outside worker writable roots; only the
configured credential reference crosses into preparation, never its bytes.

Hash TASK-SINGLE-JOB-20260928.md and SOURCE-EXCERPTS-20260928.md against INPUTS.
At freeze, bind exact source revision and file hashes, policy/profile/adapter/image,
input identity, task JSON, independent principals, generation, roots and limits.
Derive Authority UUID and Work from supported preparation; do not invent them.
A `/2` Job submission carries explicit provider_turn_seconds=180 and
verification_command_seconds=30. Reserve 60 seconds inside a proposed 300-second
supervisor bound; stop new admission by 240 seconds. This is a proposed bound to
validate through the actual supervisor, not a proved external-I/O hard ceiling.
Workspace capacity 83886081 bytes is a free-space admission requirement, not a quota.

## Literal command surfaces — draft operands, not an execution sequence

The following are existing supported entrypoints. `$PY` is the known interpreter;
`$BOUND` and document paths are future reviewed artifacts, currently absent. These
commands are not authorized for live execution by this draft. They must be rehearsed
with the final generated documents and isolated fake boundaries after selection.

```sh
PY=/home/sl/.local/state/baton-v12-venv/bin/python
ROOT=/home/sl/baton-instances/single-job-257627-291715
PACK=/home/sl/baton-runs/single-job-257627-291715
BOUND="$PACK/manager-source"
export PYTHONPATH="$BOUND/src:$BOUND"
export PYTHONDONTWRITEBYTECODE=1

# Preparation only: bootstrap.prepare's supported command; no Job submission.
"$PY" -B -m tools.stack_command bootstrap --inputs "$PACK/bootstrap-empty.json"
# After supported Work/principal resolution, repeat bootstrap with the sealed Job.
"$PY" -B -m tools.stack_command bootstrap --inputs "$PACK/bootstrap-job.json"

# This is the supported submission surface, not permission to submit before B1–B5.
"$PY" -B -m tools.stack_command manager --store "$ROOT/jobs.sqlite3" --incarnation single-job-257627-291715-submit --authority-uuid "$AUTHORITY_UUID" submit --document "$PACK/submission.json"

# Observation against those exact stores; obtains no execution capability.
BATON_V12_STAGE_EXECUTION_CONFIG="$PACK/deployment.json" "$PY" -B -m tools.stack_command manager --store "$ROOT/jobs.sqlite3" --incarnation single-job-257627-291715-read --authority-uuid "$AUTHORITY_UUID" status --control "$ROOT/control.sqlite3" --observe tools.stage_execution:observing_factory

# File-only failure readback; derive ATTEMPT and LOG_ROOT from correlated status/delivery.
"$PY" -B -m tools.stack_command logs --logs "$LOG_ROOT" --attempt "$ATTEMPT" locators
"$PY" -B -m tools.stack_command logs --logs "$LOG_ROOT" --attempt "$ATTEMPT" read --stream provider.stderr
"$PY" -B -m tools.stack_command logs --logs "$LOG_ROOT" --attempt "$ATTEMPT" read --stream worker.stderr
```

AUTHORITY_UUID must be read from the supported bootstrap result, not typed from an
old instance; ATTEMPT/LOG_ROOT likewise come from this run's published evidence.
No raw store read. Match configured store layout to these paths in bootstrap inputs.
A source runtime must have a complete reviewed transitive manifest and controlled
import/cache origin before effects; `-B` alone does not prevent stale pyc loading.
A packaged runtime may instead supply these subcommands once its exact build is
accepted. Do not run the old distro simply because its path is known.

**B1 — missing matching bounded start/preparation packet.** There is no verified
one-job, fresh-context end-to-end command in the inspected accepted recipes:
`baseline_bindings.py` unconditionally emits required context, and `baseline.py`
requires its context profile. `two_job_supervisor.TwoJobGate` explicitly rejects
anything but two distinct Jobs; `prepare_two_jobs.py` pins the historical manager
snapshot. `stack_command start` is a persistent supervisor, not a bounded Job run;
`stop` stops its supervisors, not proof of stopped task writers. The low-level
`manager serve --once` is one sweep, not end-to-end completion. Therefore this
packet deliberately has no fabricated bounded-start command. This concrete command
gap is recorded in FINDING, to be fixed at the existing owned composer/supervisor
boundary and independently tested; do not copy a helper here or use shell timeout
as a substitute for cancellation/cessation/settlement.

The bootstrap command can consume one Job and workers using the supported schema;
that is not evidence that the old baseline composer generates this new packet.
Keep generated bootstrap/submission files absent until the resolved identities and
accepted composer exist, rather than publishing syntactically plausible placeholders.
The future bounded command should own submission once; the illustrative submit
surface above must not also run if the supervisor itself submits.

## Expected evidence and failure behavior

Positive: exactly one admitted task execution, correlated answered terminal and
completion-envelope digest; stopped exact producer/all writers; host-readable
proposal; frozen measured result, accepted intake/retention with authoritative
bindings and independent review of the same bytes/base. A provider answer, exit0,
empty status, or proposed artifact alone is not success. Record each preparation,
claim, token, launch, cessation, result and review identity and its evidence path.
Preserve result/attempt log locators and capture state. Missing is not empty.

Negative: stale claim or changed root refuses before launch; interrupted host
writer keeps admission/reuse held; engine ambiguity, permission error, incomplete
result or missing required artifact reports the exact operation and preserves
workspace/evidence. No automatic normalization, repair, reset, deletion or retry.
Status must distinguish stale observations, held resources and unfinished cleanup;
status/readback cannot clear a hold. An access error is not successful collection.

Future deterministic packet acceptance must drive the literal generated argv with
fake engine/provider at their normal boundaries and real isolated coordination.
Preflight named selectors by AST/source inspection first; exclude live *_engine
selectors and imports with live effects. Prove positive completion plus missing
proposal, partial preparation/late writer, access failure, interrupted reply,
changed identity, duplicate submission and one-run admission cap. Assert each cut
fires and count effects. Use inherited accepted tests for unchanged boundaries;
no broad-suite rerun merely to certify this draft. No runtime tests ran here.

## Finite readiness and next handoff

B1 bounded fresh-context single-job composer/supervisor: unresolved command gap.
B2 W285465 current no-helper completion/recovery: active, not accepted; includes
remaining cleanup/failed-start/refused-session/abandon/deadline wiring and honest
permission errors. No parallel product edits by tuner.
B3 reached consumer/cross-store/DB and hold coverage: disposition in
BLOCKERS-20260928.md; old residual labels do not prove current defects fixed or live.
B4 complete frozen runtime/image/profile, immutable source and generated documents:
not available, values remain null in candidate manifest instead of fabricated hashes.
B5 final literal deterministic rehearsal and independent packet acceptance: pending
B1–B4. Draft review can proceed now; no dependency was changed.

Remaining live question after those facts are accepted: does the chosen real OCI
image/provider, under the selected shared UID/GID and network/credential reference,
produce a useful host-readable result that this exact manager can cease, collect
and retain without normalization/helper launch? Deterministic simulation cannot
establish real provider behavior, authentication or actual OCI mount/access behavior.
Select one exact frozen start argv, artifact/image hashes, credential reference,
network, limits and preservation-on-failure disposition before launch. No live suite,
image build or preserved-run recovery is implicitly selected. Parallel proof follows
a successful, independently assessed single Job; reuse remains a later v12 delivery
obligation and is not smuggled into this fresh-context packet.
