# Failed managed cleanup attempt — operator review

baton.prompt, 2026-09-08. Discussion/operational assessment, not independent
acceptance or execution under the held tuner claim. Read-only investigation.

## Confirmed chain

- M118940 authorizes the exact physical disposal; tuner pinned it before acting.
- Tuner claimed W116016 at118969, offered under assignment episode118941.
- Its first command, ordinary docker rm of full ID
  395d0a8f58dd436d76bf2c7c26ea4eaace084b394a3f48938a51e1c51d168baf,
  failed with Docker socket permission denied. The retained result is
  evidence/disposal-118969/01-removal.json. No successful removal is recorded.
- The local tuner transcript at12:27:14.570Z records the same docker rm
  retried with sandbox_permissions=require_escalated and a request referring
  to the existing M118940 approval. The bridge denied that interactive request
  at12:27:14.577Z and quarantined the context (incident42).
- At12:27:29.582Z the bridge reported that the interrupted turn still held
  W116016 (incident43). The turn originally delivered W116014; tuner had
  already handed that Work away and claimed W116016 in the same turn. This
  explains the different Work IDs in the two incidents; the orphan is W116016.

Canonical snapshot119020 confirms failed tuner runtime, cause approval,
incarnation ed6f611e-4132-4c3b-af52-a86aae2aa9df, and W116016 still active
under baton.tuner, episode118941. No replacement claim or completion exists.

## Fresh resource check

Direct read-only Docker inspection found the first exact container still
exited, finished2026-09-05T05:31:21.082645165Z. The runtime name listing still
contains all31 exact selected runtime IDs, each exited. The old test tag still
resolves to db9f397171153338ce068b46a7c9ab48c79b80d9f1ad1db4c149541a5eb8199b
with both baton-w81857-exchange aliases intact. All32 selected containers and
the selected tag therefore remain. This presence check is not a replacement
for the full before-each-removal identity comparison required by M118940.

## Diagnosis

This is an execution-authority/assignment mismatch followed by a prohibited
interactive request on a managed turn. Existing user approval did not install
Docker socket execution permission. The managed Docker inspection profile in
tools/codex-event-bridge/src/exec_policy.mjs explicitly excludes arbitrary
mutable Docker operations; its read-only access cannot execute this disposal.
Restarting and handing back the unchanged operation would reproduce the gap.
The bridge's denial/quarantine is its configured behavior, not evidence of a
new integration/runtime cleanup defect. Prompt's earlier handoff should have
checked the execution boundary before assigning raw Docker removal to tuner.

## Recommended recovery, not executed here

Drain new dispatch, release exactly the orphaned tuner claim with episode118941,
and route W116016 to ops for the existing approved physical disposition through
an eligible interactive/operator execution boundary. Let other live claims
finish, require paused/zero blockers, then use stop-drained/start and explicitly
resume to replace the quarantined managed context. Do not reset a healthy live
claim or merely retry the failed Docker request. No new broad Docker allow rule
is proposed. An automated mutable boundary would need its own bounded design.

M118940 remains the sufficient disposal decision; no repeated user selection
is required. Physical cleanup and independent absence/alias verification still
need execution. Keep W116016 and W115981 open; dismiss incidents only after the
orphan and quarantined-context conditions have actually been resolved.
