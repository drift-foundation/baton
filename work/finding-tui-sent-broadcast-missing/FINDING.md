# Sent broadcast missing from the legacy TUI folder

## Observed

On 2026-08-13, after the legacy 1.1.0 relocation and successful directed
ping-pong, `human.slawomir` sent notice
`433d58e6e000c06b8d26ab06c407fa3b` to scope `baton.*`. The authority delivered
it to `baton.reviewer`, which consumed it with `see`. The sender then reported:
"I sent the broadcast but the legacy client doesn't show it in my folder."

The report arrived as directed message
`ecbaad8e69cf62c88a18e251f94e4879`. It was acknowledged without applying a
workaround.

## Confirmed

- The notice exists in the relocated authority and was deliverable to its
  frozen audience.
- The relocated CLI, bridge and human TUI all use
  `/home/sl/baton/mailbox/legacy/baton.json`.
- Baton projections are explicit cache files created by `materialize`/save;
  publication does not automatically write every sent item into the configured
  filesystem projection directory.
- The Baton TUI 1.1.0 contract does include sent notices in its Sent view.

## Open

- "folder" may mean the TUI Sent view or the configured filesystem projection
  directory. Diagnose both meanings; do not silently choose one as the defect.
- If the TUI Sent view is meant, determine whether the notice is absent from
  core sent enumeration, filtered out, stale until refresh, or painted
  incorrectly.
- If the filesystem directory is meant, determine whether this is an unclear
  product affordance/documentation issue rather than missing persistence.

## Acceptance boundary

- A notice sent by the active participant is visible in that participant's TUI
  Sent view without restarting the console.
- Scope, kind, subject and delivery/seen state remain accurate.
- No automatic filesystem projection is introduced without a separate ruling;
  the authority remains canonical and materialization remains explicit.
- Add a focused deployed-artifact/PTY regression if the defect reproduces only
  in the shipped legacy console.

## 2026-08-13 ruling — do not repair legacy if the successor passes

Slawomir ruled that legacy 1.1.0 exists only to reconnect participants through
the new deployment topology. This observation does not authorize or require a
legacy patch. The next-generation TUI must be exercised with the same scenario:
the active human sends a scoped broadcast and sees it in the TUI Sent view
without restarting. If that passes, close this finding as legacy-only and ship
no correction to 1.1.0. If it fails, the defect belongs to the successor release
and must be corrected there before its cutover.

## 2026-08-13 outcome — successor passes; legacy observation closed

The successor passes the ruled scenario in source-level state/render tests and
a real-terminal PTY test without restarting the console. A break sweep that
removed sent notices from `list_sent` made all eight tests fail. This satisfies
the successor acceptance boundary. The legacy observation is closed without a
1.1.0 correction and is not a successor deployment blocker. Candidate-artifact
verification remains part of the ordinary post-build gate, not a reason to
reopen legacy diagnosis.
