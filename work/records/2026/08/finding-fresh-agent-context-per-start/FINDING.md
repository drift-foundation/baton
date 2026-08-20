# Fresh agent context on every managed start

## Decision — 2026-08-19

Every managed Baton stack start creates fresh execution contexts for its
configured agents. Codex reviewer/tuner Threads and ACP agent sessions are
replaceable runtime state, not deployment configuration and not authority.

Stable identity remains the Baton participant (`baton.codex`, `baton.tuner`,
and the configured ACP participants). After startup, each fresh agent rebuilds
its position from canonical Baton state, accepted role instructions, and the
bound Work dossier. Old sessions remain history but are never selected as the
current worker by a later start.

The launcher records newly created session locators under the coordination
home's private `run/` state. Operators do not edit persistent deployment JSON
to rotate Thread ids. A planned restart therefore cannot carry obsolete
binary/config paths, accumulated conversational assumptions, or an old active
writer into the new runtime.

This decision does not supersede W424's bootstrap-handoff correction. A fresh
Codex Thread must survive the creating client's disconnect long enough for the
dispatcher to resume it during the SAME managed startup. It is simply not
reused by a later startup.

## Rationale

Operational restarts are expected roughly weekly or less. The bounded cost of
rereading policy and active dossiers is preferable to stale deployment
instructions, context growth, writer conflicts, and manual Thread migration.

## Acceptance boundary

- `just start` creates fresh contexts for every configured agent.
- The dispatcher and readiness producers use the locators minted by that same
  start.
- Session locators live in private runtime state, not durable deployment
  configuration.
- Restarting with unchanged configuration still creates fresh contexts.
- Claimed Work remains discoverable and resumable through canonical Baton
  readiness by the new context holding the same participant identity.
- Old contexts are retained as history and never silently reselected.

## Supersession clarification — 2026-08-19

This later decision governs the boundary between MANAGED stack starts for
every configured agent, including ACP agents. W27's protection against
silently overwriting an existing ACP session selection remains valid within
one managed run, during agent-process recovery, and for an operator who
explicitly chooses a persistent manual `load` deployment. It does not
authorize `just start` to reuse the preceding managed run's ACP session.

Therefore a managed restart must give each ACP participant fresh selection
state (or an equivalent fresh-session boundary) without weakening W27 into an
overwrite. The old selection remains history; it is not the state against
which the new managed run bootstraps.
