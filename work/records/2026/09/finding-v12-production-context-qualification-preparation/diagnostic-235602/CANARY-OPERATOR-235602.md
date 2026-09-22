# Isolated canary qualification packet — claim235602

Failure-diagnostic correction under owner M235599/reroute235600 and the final
authentication-restored/resume FINDING entry. Recall-only acceptance remains
owner235310/235311 and isolation design remains owner234513. Pending independent
packet review, then baton.decide for the separate live-run selection. No live
provider, engine operation or production enabling was performed in preparation.

The exact zero-placeholder command is in CANARY-COMMAND-235602.txt. It executes
the new isolated_canary.py, with the reviewed manifest SHA256 as an operand.
Use the same invocation with --audit instead of --run for an offline file audit;
use --review after the run from the independently assigned reviewer context.
The run reports only protected evidence location and outcome, never the canary,
credentials, provider prose or session content. The output is **observed awaiting
review**, never production qualified. An independent reviewer reads the evidence,
runs --review with the same approved digest, and appends a review to this dossier.

The question requiring the real provider is narrow: does Claude Code 2.1.247,
model argument claude-opus-5, resume the exact session and recall a random
first-prompt canary from only the designated session file? Deterministic tests
exercise the fixture and refusal paths, but cannot answer that provider question.
Exact terminal success/session/answer requirements remain. This experiment requires
modelUsage with exactly claude-opus-5 and claude-haiku-4-5-20251001 keys. Missing
usage, missing either key, unknown additional keys, and non-object usage refuse,
even with a direct Opus model field. A direct model field may be absent or exactly
claude-opus-5; any other value or type refuses. Usage values are not interpreted
as attribution. Every accepted result is explicitly labeled recall-only mixed
usage with model attribution unestablished; no exclusive/primary Opus claim or
auxiliary Haiku claim follows. The unchanged strict projection is retained inside
the experimental terminal envelope with actual_model null.
Recall establishes neither token/cache savings nor general production readiness.

## Selected execution

The fixture controls Docker directly through /usr/bin/docker, with explicit
unix:///var/run/docker.sock, no inherited Docker configuration and --pull=never.
It uses the independently verified existing image e84a033c…; the exact digest is
in the manifest. It mounts only the pinned fixture and its unchanged strict
terminal contract as read-only code. No image rebuild, installation or production
worker alteration is required. The fixture is **not** the ordinary dogfood entry.

It runs non-root with the current owner's exact uid:gid (the standing shared
manager/runtime identity), bridge network, read-only image root, dropped
capabilities, no-new-privileges, 64 PIDs, 2 GiB memory and one CPU. Each worker has
its own /tmp tmpfs (256 MiB), destroyed when that stopped container is removed.
Each /input, /source and /output is a freshly created empty read-only bind.
The provider HOME is the only writable persistent bind. The credential source
is /home/sl/.claude/.credentials.json, independently copied into one private
/dev/shm slot per turn; slot cleanup follows confirmed container removal.
Credentials never enter the session snapshot or public result.

Turn one chooses a fresh UUID session and 128-bit random canary. Its only user
prompt says to remember the canary conversationally and answer READY. Turn two
has a fresh process/container/HOME/task roots and resumes that exact UUID; its
prompt asks for RECALL: followed by the canary, without supplying it. Provider
argv uses --print --dangerously-skip-permissions --output-format json --model,
then --session-id or --resume, UUID and prompt. The worker passes only HOME,
PATH, TMPDIR, XDG_CACHE_HOME and PYTHONDONTWRITEBYTECODE to the CLI. It checks the
pinned CLI version before the one provider invocation per worker.

Only .claude/projects/-output/<session UUID>.jsonl is copied to the fresh second
HOME. This is the explicit allowlist; a missing, linked, aliased, empty, oversized
or unreadable session file refuses. No adaptive wider copy is attempted. The
session file remains writable so the provider can append the resumed turn.
Other first-HOME files are retained privately for diagnosis but are never mounted
in turn two. The first request, raw result and evidence roots are likewise absent
from the second worker. Exact initial HOME inventories, mounts, Docker identities,
stopped states and controller ordering are retained for independent evaluation.
This construction excludes first-turn non-session filesystem persistence. It is
not a proof against a malicious provider or external network service persistence.

## Bounds, identity, cleanup and evidence

Two provider invocations maximum, 180 seconds each, 420-second active controller
and 600 seconds total including a reserved cleanup interval. No third turn or
retry. Exclusive /tmp/w177936-diagnostic-235602 and /dev/shm/w177936-diagnostic-235602
reservation consumes the identity, even after partial failure. Do not delete or
reuse these roots to rerun. The failed opus-234686 identity, its packet, all earlier consumed identities
and prior candidates remain unchanged. No failed result is reclassified.

The parent stops the controller group (including its Docker clients) before
cleanup. Cleanup addresses only the two exact fixture container names and checks
their image/run/attempt labels before stopping/removing them. It never removes
arbitrary host paths. Uncertain cleanup makes the run fail and retains credential
slots when a worker's absence cannot be confirmed. An operator must resolve those
exact named resources before any subsequent experiment. Interrupted execution,
a failed first result or uncertain shutdown cannot admit turn two. Every run,
including failure, remains consumed. No automatic recovery/retry is provided.

Private evidence lives under /tmp/w177936-diagnostic-235602 (0700): binding,
requests, pre/post runtime inspections, intents, raw provider results, selected
session snapshot, transfer hashes, initial HOME inventories, chronology,
observation/failure and final cleanup. Raw contents must not be posted to Baton.
Independent --review emits only session/run/manifest identity, result and an
explicit false production_certification flag plus the exact experimental acceptance
scope, usage-model pair and unestablished attribution. Review recomputes acceptance
from both raw provider results, rather than trusting the controller summary. Preserve the evidence until its
independent disposition; no host evidence deletion is automated.

## Relationship to preserved production work

The run and two attempt identities are **qualification fixture** identities bound
to v11 W177936; they are not invented v12 Job assignments, admission commits,
serving receipts or certification evidence. The owner-selected isolated test
supersedes the new private reviewer-delivery/image requirement. Accordingly this
packet does not invoke authorize_qualification_run or certify_production_profile,
modify a live deployment or claim that direct Docker is the full manager route.
A successful independently evaluated recall test supplies the selected provider
fact; any subsequent production certification must still satisfy the accepted
R1–R3 manager contract with real serving receipts and independent review.

The earlier four capsule and 275 guard/serving tests, accepted review234346,
IMAGE-VERIFICATION-234131.json, MANAGER-ARTIFACT-234277.json and its independent
81-file inventory remain supporting evidence. That manager artifact is unchanged
and is not executed by this isolated fixture. The new manifest binds this
qualification-specific runtime/argv/state/deployment profile and exact fixture
files; it does not relabel a candidate as a certified production profile.

## Model evidence and acceptance scope

MODEL-SELECTION-234686.json retains the earlier static CLI/selector provenance.
REVIEW-EVIDENCE-235117.json records the independently observed exact mixed usage
pair in the failed first turn. Neither is a successful recall result. This packet
uses that exact pair by explicit owner selection; it does not reinterpret the
failed opus-234686 run as success. The previous packet and consumed roots are
unchanged. No image rebuild or new selector discovery is needed for this amendment.

CANARY-MANIFEST-235602.json binds model_acceptance as well as the fixture files,
profile, bounds, image and deployment. The requested model remains claude-opus-5.
There is no claimed reported answer model: the strict contract is copied byte for
byte and continues to yield actual_model null for mixed usage. This fixture's
separate experimental envelope carries the accepted pair and unestablished model
attribution. Production strict-model validation/certification remains unchanged.

Preparation is authorized; the new --run invocation requires independent packet
review followed by the owner's separate exact live selection. The live question
is still clean-worker recall from only the allowlisted session state. Passing
focused deterministic tests does not answer it or justify production enabling.

## Private failure diagnostics — owner235599/reroute235600

The operator reports restored authentication and an explicit Opus pong. This
packet does not repeat that probe, change credentials/settings or assume future
authentication. It preserves the failed recall-235340 and opus-234686 packets,
consumed roots and evidence; their outcomes remain failures.

Each version/provider invocation drains stdout and stderr together under the
existing deadline. Each stream is capped at2MiB; overflow terminates execution
and records truncation. Private records include exact observed exit code (null
if process creation failed), closed reason, elapsed time and base64 stream bytes.
Timeout records include retained bytes and the observed post-termination status.
These are bounded prefixes on overflow/timeout, never claims of complete output.
Raw exception strings and raw diagnostics never enter the outward outcome.

A run/attempt/turn/session-bound worker envelope carries both version and provider
records through Docker stdout even when the worker exits nonzero. The outer
start/attach transport has a12MiB per-stream cap for encoding overhead; provider
streams retain their2MiB caps. This is not a larger provider-output allowance.
The controller records start-failure status and both outer streams, retains the
worker wire, validates its closed envelope and base64/bounds/status, writes
private version/provider .stdout/.stderr and provider JSON before interpreting
failure status or terminal JSON, and then saves obtainable runtime-after facts
before cleanup. Invalid/empty wire remains retained even when no envelope can
be parsed. Nonzero provider/engine exit, timeout, overflow, malformed output or
unavailable inspection still fails; no second turn or session transfer follows.

Other failed engine calls retain engine-failure-<pid>-<sequence>.json in private
custody. Cleanup retains obtainable cleanup-before and cleanup-stopped inspections
before removing exactly the owned named container. An unavailable runtime-after
inspection is explicitly recorded; missing observations are not successes.
Cleanup uncertainty keeps the run failed and preserves the credential slot per
the original policy. Independent success review also rechecks the bound worker
envelopes, process statuses and their byte equality with retained provider JSON.
A successful-looking provider JSON cannot override a failed process status.

All new stream/wire/engine/worker records are private0700-root/0600-file evidence.
Do not publish their contents or arbitrary provider error prose. Review can
publish closed failure classifications, status/bounds and protected locators.
Exact provider causes may remain unknown; retained bytes are evidence for a
bounded independent diagnosis, not authority to refresh credentials or retry.
The run/cleanup limits and accepted exact mixed-model predicate are unchanged.
