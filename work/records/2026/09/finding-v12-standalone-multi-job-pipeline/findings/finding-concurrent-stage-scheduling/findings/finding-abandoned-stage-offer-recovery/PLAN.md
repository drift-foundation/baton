# Plan

1. [done, reviewer reproduction 2026-09-02] Prove that restart abandonment
   leaves the Job stage projected `offered` with only a permanently deferred
   claim owed.
2. [pending] Expose the canonical offer identity and terminal settlement
   needed by the Job manager through a public Worker Manager read.
3. [pending] Persist append-only stage execution episodes and derive a fresh
   offer/attempt identity after canonical abandonment.
4. [pending] Cover undelivered abandonment, accepted recovery, repeated
   restart, concurrent replacement, and status history.
5. [pending independent review] Bind the verdict to the immutable proposal and
   enumerate every changed production and test path.
