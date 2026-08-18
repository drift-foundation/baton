# Finding: v12 isolated agent workers and gated integration

## Status

Confirmed operational direction for Baton v12. This record is a roadmap, not
authorization to change the v11 runtime or its current shared-checkout rules.

Authoritative Baton Work: `W193` (`bec445ce-W193`), low priority and parked
until the current v11 cutover and stabilization work is complete.

On 2026-08-18, the project also confirmed the general invariant exposed by
this record's initial omission: every finding dossier must have exactly one
corresponding Baton Work bound to its canonical record path. Roadmap findings
remain visible by being parked; they are not kept off-ledger.

## Motivation

The v11 trial coordinates claims and handoffs authoritatively, but agents still
execute in one writable checkout. A provider can fail after claiming Work, a
replacement can be assigned, and the original process can later recover and
continue writing. Baton can fence late protocol operations, but it cannot fence
direct filesystem writes from an already-running process. Independent agents
can also change the same review target underneath one another.

The live W154/W155 review on 2026-08-18 demonstrated the latter failure mode:
W154 returned for review against the two-level Work tree, while W155 changed
the shared tree to three levels. W154's focused regression then observed a
different implementation boundary from the one it had been written against.

## Confirmed v12 operational model

Each Work assignment executes as a disposable, isolated worker:

- one container or equivalently strong isolation boundary;
- one independent repository checkout, not a writable worktree sharing the
  canonical repository's Git metadata;
- one immutable base revision and one unique assignment generation/claim
  epoch;
- explicit role instructions, policy, toolchain, resource limits, repository
  roots, and scoped credentials;
- no ability to write the canonical checkout, canonical Git refs, or another
  worker's workspace.

The worker does not "finish" by modifying production state. It publishes a
candidate containing:

- a commit range or equivalent immutable patch/bundle;
- the base revision and assignment generation that produced it;
- focused and broad test evidence;
- dossier/progress updates and relevant logs;
- an explicit completion or inability-to-complete disposition.

An integration authority reviews the candidate and explicitly accepts,
rejects, or returns it for revision. Only that authority changes the canonical
repository. Agent-created commits are proposal artifacts in disposable worker
repositories, not canonical history.

## Unified agent boundary

Every model/vendor CLI is wrapped behind one model-neutral worker surface.
ACP is the common interaction boundary for agent sessions and turns; whether
the implementation underneath is Claude, Gemini, Codex, or another CLI is not
a Baton protocol concern.

ACP is not stretched into a container or Git lifecycle protocol. A small Baton
worker-control layer owns:

- create/start/cancel/stop/status;
- assignment and claim-epoch fencing;
- input manifest delivery;
- event, heartbeat, and log collection;
- candidate artifact publication;
- integration disposition and workspace retention.

Thus every agent can behave as an ACP agent while the supervisor, rather than
the model adapter, owns isolation and authoritative job lifecycle.

## Failure, recovery, and late workers

Failover is a fenced takeover, never an ordinary reroute:

1. Cancel/stop the original worker and seek a positive quiescence result.
2. Atomically revoke its exact claim epoch with compare-and-swap recovery.
3. Mint a new assignment generation and start a new isolated worker from the
   selected base revision.
4. Accept candidate publication only from the current generation.

If the original worker later returns, its generation is stale. It cannot
modify the replacement's checkout or submit an acceptable candidate. Its local
work is disposable by default. An operator may retain it briefly and salvage
evidence or a patch manually, but Baton never merges or revives it
automatically.

This deliberately trades some duplicated work for single-writer safety and a
reviewable integration boundary.

## Security and reproducibility boundary

- Credentials are least-privilege, assignment-scoped where possible, and are
  not baked into images or candidate artifacts.
- Repository policy and forbidden operations are enforced outside the model,
  at the container/supervisor boundary.
- Network, CPU, memory, time, and writable mounts are explicit manifest data.
- The worker image, toolchain, adapter, base revision, role instructions, and
  policy digests are recorded with the candidate.
- Logs and candidate artifacts are untrusted worker output until integration
  review accepts them.

## Non-goals for the current v11 release

- No v11 claim, route, ACP, or shared-checkout semantics are silently changed
  by this record.
- No attempt is made to make a writable shared checkout safe for concurrent or
  recovering agents.
- No recovered stale worker is allowed to resume authority merely because its
  provider became available again.

## Open design decisions

- Exact worker-control API and manifest schema.
- OCI/Docker as the required runtime versus an isolation conformance contract.
- Candidate transport: restricted Git namespace, Git bundle, content-addressed
  artifact, or a combination.
- Integration authority implementation and merge/rebase policy.
- Candidate signing/attestation and provenance requirements.
- Workspace/log retention and manual salvage policy.
- Cache sharing without writable cross-worker state.
- Network and credential profiles for different roles and repositories.
