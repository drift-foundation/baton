# Proposed next real-session checkpoint — W106673

Decision support by baton.codex, 2026-09-07, claim 107091. Owner messages 107088
and 107099 approve the sequence: clean deterministic evidence review, then a
bounded real-Claude continuation preparation and separate owner execution
checkpoint. The deterministic evidence was accepted in
review-2026-09-07T03-53-47Z.md after export response M107151. This file
records preparation requirements; it is not an executable runner or approval.

## Runtime boundary for the next preparation

Use only a separate dossier-local experiment. Do not change production provider,
manager, image recipe, configuration or existing tests. The current
v12/worker/claude_agent.py PROVIDER_ARGUMENTS uses --print/JSON and _provider
runs one subprocess per turn. Reusing its outer Python process would not prove
that a live Claude process/session survived. Its _provider starts in the candidate
directory, which must also be addressed before ordinary unmount can succeed.

Prepare a small resident supervisor and the exact supported persistent CLI or
session transport for a pinned installed Claude version. Validate that version's
actual transport and restore interface before freezing argv; do not assume
one-shot invocation, a wrapper nonce or an application session label proves
process continuity. A new runner must handle the real supervisor/CLI/tool process
tree; the deterministic runner's requirement that Docker top contain only the
resident cannot simply be removed without replacement identity checks.

Keep supervisor/CLI working directories, IPC and session state outside /output.
Permit fixture tools to edit the private /output line; require completion and
quiescence before detach. Ordinary unmount is still the decisive gate. A retained
cwd/file handle causing EBUSY is a failed protocol handoff requiring confirmed
shutdown, even when the model reports completion. No stronger unmount flags,
worker mount capabilities or alternative writable line alias is acceptable.

Pin full container ID, process start times/pidfds, actual mount namespace,
workspace device/inode and actual Claude session identifier. Retained-session
success requires the same live CLI process and session, not a resumed replacement.
Record process-tree and mount evidence around both turns. All uncertain identity,
detach, restoration or shutdown outcomes keep consumption/reassignment denied.

## Exact owner inputs and execution package

The deterministic Python-only image is not a Claude runtime selection. The
existing v12/worker/Dockerfile.claude recipe is a read-only installation reference,
not an immutable artifact selection. Owner must identify an installed image ID
and accepted CLI/model version; validate them without implicit build/pull.

Owner must nominate the exact read-only credential source and allow its use for
this fixture. Proposed container destination is the existing logical slot
/run/baton/credentials/claude; provider home links to it as the existing adapter
does. Credentials stay separate from the workspace, session export and evidence.
Do not discover/read/hash/copy bearer contents, mount a whole user home, inherit
ambient provider variables or publish raw provider diagnostics/transcripts.
Define the exact approved provider network boundary, time/turn/spend ceiling and
bounded output policy. None is inherited from the offline deterministic grant.

Freeze the full image, mounts, uid/gid, resource limits, CLI/session commands,
supervisor/controller scripts and operator invocation in a reviewed manifest
before asking the owner to execute. Keep cap-drop ALL, no-new-privileges,
read-only root and the reviewed controller-only namespace authority. Any needed
change from deterministic posture must be explicit. Managed agents get no new
credential or privileged execution authority from preparation.

## One comparable correction cycle

Use a tiny disposable task and an independent deterministic check of the first
useful correction. Establish equivalent initial instructions and workspace bytes
for the retained-session and stop/restart/restore arms; record differences that
cannot be held equal. Session state for restoration belongs to this fixture,
outside the detachable workspace and separate from credentials. Prepare a
bounded restoration method that does not export credentials or raw transcripts
into repository evidence. Do not call a fresh unrelated conversation a restore.

For each arm record monotonic first-turn completion, review/consumer readiness,
correction dispatch, observed CLI startup or restoration completion, and first
verified useful correction. Report end-of-work to that verified correction as
the main comparison, separating mount/container intervals and review delay.
Explicitly verify retained process/session continuity versus the restart arm's
new process and restored session. Use equivalent correction instructions and
the same verifier. Limit this to one pair, with no automatic retries or benchmark
campaign. Any inconclusive provider/session result stays inconclusive.

The existing 66.191/79.236/3095.990/171.169 ms values are deterministic fixture
intervals. They exclude real agent startup, restoration and context reload and
do not measure how soon a restarted agent becomes useful. The expected larger
benefit of avoiding those costs remains a hypothesis. Report observable timings;
do not infer cache hits or provider-internal context-loading costs. Real-session
success would still require independent review and explicit production adoption.
