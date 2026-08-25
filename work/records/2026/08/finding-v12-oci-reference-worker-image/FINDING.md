# Finding: build the OCI reference worker image and entry point

Promoted implementation record for the third bounded child of W5. Its Work is
contained by W5; the top-level dossier is the permanent record required by the
maximum-depth promotion rule.
Canonical Work: W6633.

## Confirmed boundary

Build a digest-pinned OCI image and `baton-worker` entry point using the
deterministic scripted M2 agent. Provider-native code remains opaque inside a
worker image; live provider certification belongs to M4. The worker has no
authority client, host runtime socket, nested runtime, host repository/config/
database access or hidden control channel.

Consent and execution are fresh posture-specific containers under one logical
runtime attempt. Consent receives no assignment, workspace, output or
execution tools. It is positively quiesced/destroyed before the execution
container is created after activation. The consent session is never promoted.

## Acceptance

- Reproducible image recipe with an immutable base/image digest and explicit
  runtime user/entrypoint.
- Protected framed control channel with bounded input/output and no ambient
  authority or engine access.
- Scripted consent, decline, execution, cancellation and fault fixtures.
- Image inspection proves filesystem/user/capability and entrypoint posture;
  secrets and assignment material do not enter image layers.
- Container-level negative tests prove consent cannot reach execution state.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## Confirmed `baton.worker-entry/1` contract — 2026-08-25

Exclusive framed stdio attachment is transport isolation, not sufficient
message identity. Every request is one closed object with exactly the common
members `protocol`, `session`, `operation_id`, and `operation`, plus only the
operation-specific members below. `protocol` is exactly
`baton.worker-entry/1`; `session` is the manager-minted identity of this exact
posture-specific container session; and `operation_id` is unique and consumed
once within that session. Wrong-session, duplicate/replayed, missing, unknown
or extra members refuse before the request reaches the agent.

- `describe` has no operation-specific members.
- `consider` has no operation-specific members and exists only in consent.
- `work` has exactly the bounded text member `task` and exists only in
  execution.

Consent and execution use different session identities; an execution session
is never a continuation or promotion of consent. Responses echo `protocol`,
`session`, and `operation_id`. A success has exactly `ok: true` and `answer`;
a fault has exactly `ok: false`, `code`, and bounded `message`. Answer objects
retain their current closed sets: describe reports `protocol`, `posture`,
`operations`, and `environment`; consider reports `contract_digest`,
`decision`, and `reason`; work reports `disposition`, `workspace`, and `recap`.
The whole response remains frame-bounded.

`cancel` is not a worker-entry operation. Cancellation is the manager's
explicit runtime stop/termination path and must be exercised against the real
container; clean EOF from an input stream is not proof of intentional
cancellation.

## Confirmed startup-fault correlation — 2026-08-25

An entrypoint/bootstrap failure that still leaves the framing loop operable is
latched before any agent dispatch. The entrypoint then reads exactly one
bounded request identity envelope and returns the pending failure through the
normal closed fault response, echoing its `protocol`, `session`, and
`operation_id`, before exiting non-zero. Reading the envelope grants no task,
workspace, output, tool, or agent capability; a latched startup failure can
never reach the agent.

A failure that prevents the entrypoint or framing loop from starting cannot
truthfully produce a worker response. The Worker Manager already owns the
launched session and operation identity and settles that case as its own
correlated `worker_start_failed` runtime result from the container-engine
failure. The protocol never invents an uncorrelated startup-response shape.
