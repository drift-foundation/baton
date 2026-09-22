# Isolated canary qualification packet — claim234686

Opus variant under owner234684 / FINDING 2026-09-22T00:44:55Z; isolation design remains owner234513. Pending independent
packet review, then baton.decide for the separate live-run selection. No live
provider, engine operation or production enabling was performed in preparation.

The exact zero-placeholder command is in CANARY-COMMAND-234686.txt. It executes
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
Strict terminal success/session/model requirements are unchanged. Mixed
modelUsage or another reported model refuses, preserving the historical gap.
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
retry. Exclusive /tmp/w177936-canary-234686 and /dev/shm/w177936-canary-234686
reservation consumes the identity, even after partial failure. Do not delete or
reuse these roots to rerun. All five historical consumed identities and prior
candidates remain unchanged.

The parent stops the controller group (including its Docker clients) before
cleanup. Cleanup addresses only the two exact fixture container names and checks
their image/run/attempt labels before stopping/removing them. It never removes
arbitrary host paths. Uncertain cleanup makes the run fail and retains credential
slots when a worker's absence cannot be confirmed. An operator must resolve those
exact named resources before any subsequent experiment. Interrupted execution,
a failed first result or uncertain shutdown cannot admit turn two. Every run,
including failure, remains consumed. No automatic recovery/retry is provided.

Private evidence lives under /tmp/w177936-canary-234686 (0700): binding,
requests, pre/post runtime inspections, intents, raw provider results, selected
session snapshot, transfer hashes, initial HOME inventories, chronology,
observation/failure and final cleanup. Raw contents must not be posted to Baton.
Independent --review emits only session/run/manifest identity, result and an
explicit false production_certification flag. Preserve the evidence until its
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

## Opus selection and evidence limits

This separate package preserves the accepted parent Fable packet unchanged.
Pin --model claude-opus-5 and expected terminal identity claude-opus-5; no
moving alias or extended-context suffix is used for this small canary.
[Official model configuration](https://code.claude.com/docs/en/model-config)
documents the full selector and minimum CLI2.1.219. Retained CLI2.1.247 exceeds
that minimum and its pinned binary contains the exact selector. See
MODEL-SELECTION-234686.json for archive/member/package hashes and source URLs.
No live account/auth/availability/model result is inferred. Any Fable result,
other Opus version or mixed-model usage refuses; there is no fallback acceptance.
The strict contract copy changes only MODEL and ACTUAL_MODEL constants; its
validation logic remains byte-equivalent to the accepted parent.
