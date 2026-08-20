# Dispatcher readiness proves a socket, not a loadable target

## Observed — 2026-08-19

During the `975af64` cutover the lifecycle controller reported the Codex
dispatcher healthy while its configured tuner target could not resume:

    thread/resume failed (-32600): no rollout found for thread id ...

The readiness producer continued forwarding W321, but the dispatcher queued
the events behind an unloadable target. W321 stayed queued and overdue. The
failure was visible in `codex-dispatcher.log`, not in `just status`.

## Confirmed cause

`tools/infra.py` treats `readiness.type=unix_socket` as successful when a
client can connect. This correctly avoids blessing a stale socket inode, but
the dispatcher begins listening before its configured targets resume and keeps
listening when a target remains `notLoaded`.

The dispatcher already exposes the stronger fact through the same socket:

    {"control":"status"}

`EventBridge.statusSnapshot()` returns `ready: true` only when every configured
target's server is connected and its Thread is loaded. It also returns each
target's `connected`, `loaded`, and status fields. The lifecycle controller
does not query this control surface.

## Proposed ruling

Extend Unix-socket readiness with an optional JSON request/reply assertion.
The dispatcher service sends `{"control":"status"}` and requires top-level
`ready: true`. A plain Unix-socket probe remains available for services whose
connectability is the complete health contract.

For the first version, the dispatcher's own `ready` value is authoritative and
means ALL configured targets are loadable. Do not add any/selected-target
policy to the generic lifecycle controller. A target not required by a
deployment should not be configured in that dispatcher.

Startup remains pending while any configured target is still loading and
fails after the existing service startup timeout. Later `just status` repeats
the control query, so a target that becomes unloadable makes the service and
stack unhealthy without killing or restarting anything automatically.

## Acceptance boundary

- The existing connection-only Unix-socket readiness form remains valid.
- A request/reply form sends one bounded newline-delimited JSON request and
  validates the reply rather than merely connecting.
- Dispatcher lifecycle configuration requires its control response to report
  `ready: true`.
- A listening dispatcher with any `notLoaded` target is unready at startup and
  unhealthy in later status output.
- All configured targets loaded makes the existing managed stack healthy.
- Malformed, oversized, missing, partial, or mismatched replies fail closed
  within the readiness timeout.
- Stop ownership remains process/argv based and does not depend on readiness.

## Open decision

Approve or revise the proposed all-configured-targets policy and the optional
request/reply extension of Unix-socket readiness before implementation.

## Approved ruling — 2026-08-19

Slawomir approved the proposed policy with the following exact boundaries:

1. Keep `unix_socket` connection-only readiness unchanged when no control
   assertion is configured. Extend that readiness form with optional bounded
   newline-delimited JSON `request` and `expect` fields rather than adding a
   dispatcher-specific probe. Both fields are required together. `expect`
   matches required top-level reply fields; this first version does not grow
   an expression language.
2. The dispatcher is ready only when **all configured targets** are connected
   and loadable. Do not add `any` or named-subset policy. A target configured
   in one managed dispatcher is required by that deployment; an optional
   target must be omitted or represented by a later, separate topology.
3. A target that is slow to resume holds startup unready for the existing
   service startup timeout. Loading within that window succeeds; exceeding it
   fails startup through the controller's existing rollback path. A target
   that becomes unloadable after successful startup makes later `status`
   unhealthy, but Baton does not automatically kill or restart the service.

For the dispatcher manifest, the intended shape is equivalent to:

```json
{
  "type": "unix_socket",
  "path": "...",
  "request": {"control": "status"},
  "expect": {"ready": true}
}
```

Replies may carry additional diagnostic fields. Malformed, oversized,
partial, missing, timed-out, or top-level-mismatched replies fail closed.
