# Plan

1. [done] Reproduce the false-positive readiness state from the `975af64`
   cutover and identify the existing dispatcher status control surface.
2. [done 2026-08-19] Obtain the operator ruling on readiness policy and
   manifest shape: optional request/expect on `unix_socket`, all configured
   targets required, and slow resume holds startup until its existing timeout.
3. [done 2026-08-20] Implement the bounded request/reply readiness
   probe and strict manifest validation without weakening connection-only
   probes; enforce JSON type identity and an absolute exchange deadline.
4. [done 2026-08-20] Cover startup delay, timeout, post-start target
   loss, malformed replies, multiple targets, the healthy path, boolean/number
   mismatch, and slow-drip replies.
5. [done 2026-08-20] Independently review the focused lifecycle and
   dispatcher gates.
