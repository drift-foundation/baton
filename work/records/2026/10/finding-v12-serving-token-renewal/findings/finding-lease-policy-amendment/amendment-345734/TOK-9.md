**TOK-9.** Heartbeats report liveness; they do not implicitly extend a token.
The trusted host's clock/deadline owner decides expiry for every holder, including
an inside-container manager using the container's token. Local runner timers may
stop work earlier; they cannot delay host revocation. Persist enough timing and
execution identity to reconcile restart; never reuse a monotonic timestamp across
boots or reset a timer merely because the manager restarted. Ambiguous timing
means hold/reconcile.

The host MAY explicitly renew a still-unexpired, unrevoked token for the same
resource, generation, operation and execution under the selected bounded policy.
Renewal is an atomic conditional control-store decision with a durable operation
ID, expected deadline revision and recorded new deadline. It does not create a
new writer or reset Job execution limits. Same-operation replay returns the
recorded renewal without extending again. A lost renewal reply grants nothing
beyond the committed authority state.

Renewal and expiry compete against that same current state. A stale expiry
observation cannot revoke a later successfully renewed deadline. Once expiry or
revocation wins, renewal MUST refuse; no heartbeat, late renewal request or
clock adjustment revives the token. Follow TOK-6 before admitting replacement.

**Owner clarification 2026-10-21 — lease policy must support the selected execution.**
A fixed 900-second lease is not a v12 requirement and MUST NOT be an incidental
ceiling that repeatedly interrupts an otherwise authorized longer Job. Select and
record bounded permission durations compatible with the Job's execution limits
and required cleanup reserve. A shorter renewable lease is valid only when the
actual execution path supplies timely eligible renewal; an unused renewal API
does not establish that support. Correct the deployed execution path or its
bounded initial-duration policy rather than repeatedly truncating development
at an arbitrary profile constant. Do not reset or exceed selected Job limits,
disable cancellation/expiry enforcement, revive expired permission, or silently
reinterpret existing tokens. Historical 900-second/four-renewal profile bounds
may be revised through the owned correction and independent verification; they
are not immutable product requirements. Decision: W333485 FINDING, owner
lease-policy correction, 2026-10-21.

