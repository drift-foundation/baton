# Fresh-runner Baton connection handoff

Status: **confirmed cross-team operational defect, transferred to Baton on
2026-08-11; contract and implementation owner remain open. This is not
implicit config discovery and is not yet scheduled into 1.1.0.**

## Transfer and minimal reproduction

`workflows.reviewer` transferred this finding in message
`9d64b6b920d5b47fceaa4b68cefd8121`:

> fresh sessions are not supplied the deployed Baton executable/config paths
> and must infer among retired installs

Minimal reproduction:

1. Start a fresh agent session for a repository whose policy binds a role to a
   participant and says the local deployment supplies Baton's executable and
   config paths.
2. Supply neither absolute path to the session.
3. Leave current, candidate, and retired Baton trees/authorities present on the
   host.
4. Ask the role to receive work.

The agent has no conformant next step. Searching the host, choosing a checkout
binary, following a plausible `current`, pairing a retired executable with a
live config, or deriving a config from the working directory are all
inference. Refusing to start is correct but leaves coordination unavailable.

## Confirmed current contract

- `AGENTS.md`, `docs/AGENTS-MAILBOX-PROTO.md`,
  `docs/EFFECTIVE-BATON.md`, and `docs/RELEASE-1.0.0.md` all say the local
  deployment supplies the absolute executable and explicit absolute config
  paths. They explicitly forbid inference from a product repository.
- The participant identity is separately bound by participating-project
  policy. A path does not choose or authenticate a participant.
- `tools/deploy.py` publishes/verifies versioned product bytes and explicitly
  creates, copies, discovers, and activates no config or SQLite authority. A
  deployed tree is inert until a caller supplies `--config`.
- The authority config lives outside product and deployment trees. Baton's
  trust boundary is filesystem access plus the explicitly named participant;
  implicit nearest-file discovery would change that boundary.
- Retired authorities require their era's executable for deliberate historical
  inspection. Their continued presence is required evidence, not a pool from
  which a fresh active session may guess.

The written product contract is therefore right but incomplete: it assigns an
obligation to “the local deployment” without defining a carrier, lifetime,
validation, or failure behavior for a fresh runner session.

## Confirmed defect boundary

This is a deployment/runner integration seam, not a reason to teach the Baton
CLI implicit config discovery. A compliant agent must receive one explicit
active executable/config pair before its first mailbox operation. If that pair
is missing or internally incompatible, the runner must fail visibly and ask
the operator; it must not search, score, or select among host paths.

Supplying only one half is insufficient. A current executable can reject a
retired protocol authority, while a retired executable can misrepresent or
refuse a current authority. Candidate and production tools may speak the same
protocol yet still represent different release choices. The pair and its
intended channel are one launch decision even though deployment owns only the
executable half.

## Proposed handoff contract

**Proposed, not yet ruled:** every fresh/resumed runner context receives a
small structured connection handoff with at least:

- the exact absolute Baton executable path;
- the exact absolute authority config path;
- the intended deployment class or provenance (for example production,
  candidate soak, or explicit retired inspection); and
- optional expected release/protocol/authority identity values that read-only
  startup validation can compare.

`BATON_BIN` and `BATON_CONFIG` are the established documentation vocabulary,
but the carrier could be typed runner metadata, environment injection, or a
runner-owned launch record. Selecting the carrier is an open integration
decision. A repository file containing host-local paths is not acceptable:
that would be non-portable, stale branch state and would collapse deployment
data into product policy.

Startup validation should be read-only and should distinguish:

1. missing handoff fields;
2. missing/unexecutable binary or unreadable config;
3. executable/config protocol mismatch or refused authority;
4. a valid connection whose `doctor` reports an operational problem; and
5. a valid, healthy connection.

Those are different operator actions. In particular, an attachment warning or
other non-OK `doctor` result must not cause the runner to hunt for a different
mailbox.

## Exact repository surfaces

- `tools/deploy.py` and `just deploy`/`deploy-activate`/`verify-deployment` own
  immutable executable publication and stable-pointer mechanics, not config
  selection.
- `docs/EFFECTIVE-BATON.md` owns onboarding and runner guidance.
- `docs/AGENTS-MAILBOX-PROTO.md` owns the portable explicit-instance rule.
- `docs/RELEASE-1.0.0.md` owns the current public onboarding promise.
- `work/finding-deployment-recipe/` owns release publication/destination work.
- `work/records/2026/08/finding-reviewer-polling-reliability/` owns post-connection readiness
  lifecycle. A polling loop cannot repair a missing connection handoff.
- `work/finding-live-first-mailbox-upgrade/` owns deliberate active/retired
  authority transitions and must provide the switch event/provenance consumed
  by any eventual handoff mechanism.

## Interactions and risks

- **Upgrade atomicity:** a runner must never observe a new executable with the
  old active-config choice or vice versa merely because two independent launch
  fields updated at different times.
- **Candidate opt-in:** a human-run 1.1 RC soak may explicitly inject the
  candidate executable with the live protocol-10 config. That must not silently
  change every team's production launch choice.
- **Restarts and compaction:** the handoff must be supplied again to a fresh
  context; transcript memory is not a deployment mechanism.
- **Several mailboxes:** a host may legitimately expose more than one active
  authority. The task/session must name which connection applies; path search
  cannot settle scope.
- **Retired evidence:** preserving retired executables/authorities must not make
  them candidates for ordinary startup.
- **No raw-store fallback:** if the config or matching executable cannot be
  supplied, opening SQLite directly is forbidden and is not a workaround.

## Open decisions

1. Which component owns the handoff carrier: the model runner, a host launcher,
   a deployment supervisor, or a small Baton integration adapter?
2. Is the active executable/config pair global to a host, scoped to a mailbox,
   scoped to a repository/team, or supplied per task?
3. Which immutable identity should startup validate in addition to
   release/protocol: authority UUID, accepted generation, deployment manifest
   digest, or some subset?
4. How does an audited live-first cutover atomically replace the active pair
   for future sessions while existing sessions stand down safely?
5. Does the deployer emit a machine-readable executable handoff fragment for a
   human/supervisor to combine with an external config, or must deployment stay
   entirely unaware of launch records?
6. Which external runner environments can receive structured session metadata,
   and what is the honest fallback when one cannot?

## Acceptance boundary

- A fresh session can begin with no repository-local Baton path and receive the
  exact active executable/config pair without filesystem search.
- Missing either field produces one explicit setup failure before `wait`,
  `claim`, `see`, or any authority write; no alternative install is tried.
- Current, candidate, and multiple retired installations can coexist without
  ambiguity. Candidate and retired use require explicit provenance/opt-in.
- Read-only validation detects an incompatible or wrongly paired executable and
  config without selecting another pair.
- A valid but unhealthy authority remains the selected authority and surfaces
  its real diagnosis; the runner does not relabel it as path-discovery failure.
- Fresh/restarted/compacted sessions receive the handoff again rather than
  depending on transcript memory.
- An active-authority transition changes the future-session pair atomically and
  leaves the retired pair available only for explicitly requested inspection.
- Participating repositories keep only role-to-participant policy and portable
  placeholders; no host-local executable/config paths are committed there.
- The complete flow is exercised from a non-Baton product repository with the
  Baton source checkout absent and several misleading retired paths present.
