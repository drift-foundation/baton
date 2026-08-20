# Codex bootstrap thread durability

## Observed — 2026-08-19

During the `975af64` coordination-home cutover, `codex-event-bridge
--start-thread` returned a new tuner Thread id and exited successfully. After
the app-server restarted, the dispatcher could not resume that id:

    thread/resume failed (-32600): no rollout found for thread id ...

Creating another Thread and attempting to resume it immediately, without an
app-server restart, failed identically. The command disconnects after
`thread/start` without creating a first turn, so the returned empty Thread has
no durable rollout that another client can resume.

The lifecycle controller nevertheless reported the dispatcher healthy because
its socket was live; target-level resume failure was visible only in the
dispatcher log. W321 remained queued and overdue.

## Expected (as first recorded — narrowed 2026-08-19, see below)

A successful role-bootstrap command must return a Thread locator that remains
resumable after the bootstrap client disconnects and after an app-server
restart. It must not report success for an ephemeral locator.

## Immediate workaround

Keep one app-server connection open across `thread/start` and the Thread's
first no-tool bootstrap turn. Only after that turn completes may deployment
configuration record the locator and restart the dispatcher.

This workaround is deployment recovery, not the product fix.

## Clarification — 2026-08-19, approved by Slawomir

W424 is narrowed to the SAME-START handoff: from the bootstrap client's
disconnect to the dispatcher's resume, within one app-server lifetime. It must
NOT establish that the Thread is reused on later stack restarts.

The original expectation above is preserved rather than rewritten, because the
reasoning still holds for the defect it names — a locator nobody but its
creator can resolve is not a locator — and only the SPAN it must hold over has
changed. Managed stack starts will deliberately create fresh agent contexts
every time, so cross-restart reuse is not a property this Work should promise
or test. That lifecycle requirement is
`work/records/2026/08/finding-fresh-agent-context-per-start/` (W459).

Promoted as this Work's contract through `revise` (thread message 456), so the
narrowing lives in the authority and not only in discussion.

## Acceptance boundary (as narrowed 2026-08-19)

- The supported bootstrap path creates a durable first turn before returning.
- Its returned Thread resumes on a SECOND CONNECTION within the same
  app-server lifetime — the bootstrap-client-to-dispatcher handoff.
- Failure to persist the Thread fails the bootstrap command rather than
  printing a usable-looking locator.
- Lifecycle status eventually exposes a configured target that cannot resume;
  a live dispatcher socket alone is not sufficient evidence for target health.

The lifecycle-status bullet is separately accountable follow-up W482, not a
W424 closure condition. W424 owns producing a same-start locator the next
connection can resume; W482 owns detecting any configured target that still
cannot load.

Superseded by the clarification above: "and after an app-server restart".
Reuse across a managed restart belongs to W459 and is neither promised nor
tested here.
