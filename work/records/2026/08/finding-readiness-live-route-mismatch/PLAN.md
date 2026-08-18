# Plan

**Status — rejected 2026-08-18.** Ledger review proves the notification was a
delayed delivery of an earlier valid assignment episode. Canonical authority
revalidation correctly refused stale action; no implementation is warranted.

1. [done] Identify the producer that emitted the two external readiness
   events and capture its input envelope/action key.
2. [rejected] Reproduce Route A + Next B: the ledger instead proves each Work
   was previously live-routed to the notified participant.
3. [not needed] Adapter change; canonical revalidation is the intended stale
   delivery boundary and worked correctly.
4. [not needed] Correctness regressions; no correctness defect was reproduced.
5. [done] Record the rejected diagnosis and close without implementation.
