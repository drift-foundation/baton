# Finding: remove the retired v10 runtime

## Context

Child of W99 (`Retire v10 code and data without fallback`). After the v11 messaging gate closes, remove repository runtime code and tests whose only purpose is to implement or operate protocol 10. Preserve historical evidence and release records that cannot execute as a fallback.

## Boundary

- Inventory exact modules, commands, build inputs, tests, and compatibility paths before removal.
- Refuse removal while any active build, deployment, monitor, or documented launch path imports them.
- Keep v11 behavior and its complete gate green after the v10-only surface disappears.

