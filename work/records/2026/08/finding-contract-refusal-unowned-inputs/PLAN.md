# Plan: own ContractRefusal's remaining public inputs

1. Revalidate every construction, serialization, replay and transaction branch
   that consumes `ContractRefusal.message` or `.durable`.
2. Establish message and exact-Boolean durability at construction without
   running rejected caller objects.
3. Add direct and transaction-level hostile regressions.
4. Update W6782's inventory owners/probes and remove both `UNOWNED` entries.
5. Run focused and full source/locked verification; return both dependent Works
   for independent review.
6. [done 2026-08-25; changes requested] Independently verified exact-Boolean
   durability and unencodable-message ownership, plus contracts inventory
   13/13 and store 48/48. Review found that a 100,000-character message remains
   accepted, the shared boundary inventory still carries an unreachable
   `seal_refusal` probe, and this implementation has no `PROGRESS.md`.
7. [done — ruling 2026-08-25] Bound `ContractRefusal.message` at 4,096 Unicode
   scalar values after establishing encodable text; accept exactly 4,096 and
   refuse 4,097 at the constructor boundary.
8. [changes required; implementer] Enforce the ruled message bound without
   running caller behavior, turn the additive exact-edge regression green,
   retire or replace the now-unreachable shared `seal_refusal` probe, create
   and maintain `PROGRESS.md`, and run the focused plus source/locked gates.
   Review: `review-2026-08-25T00-33-39Z.md`.
9. [done 2026-08-25; changes requested] The exact edge, stale message probe and
   missing progress record are corrected. Re-review found the enclosing public
   `seal_refusal.refusal` entry wholly unowned: a hostile attribute lookup runs
   before any boundary. Own the exact refusal before reading members, add its
   inventory declaration/probe, reconcile the `MESSAGE_LIMIT` export claim,
   then rerun focused and source/locked gates. Review:
   `review-2026-08-25T00-44-40Z.md`.
10. [done 2026-08-25; changes requested] Exact-type public sealing and the
    package export are corrected; the hostile case plus contracts/store focused
    suites pass. Add `seal_refusal.refusal` to the manager inventory's stated
    owners and checked witnesses, add permanent coverage of the exported
    4,096 rule, append this round and actual gate state to `PROGRESS.md`, then
    rerun focused and source/locked gates. Review:
    `review-2026-08-25T00-51-03Z.md`.
11. [done 2026-08-25; signed off] Verified the stated owner and non-vacuous
    hostile witness, added permanent public-`MESSAGE_LIMIT` edge coverage, and
    passed contracts inventory 15/15 plus store 49/49. The remaining aggregate
    owner-sweep failures are 16 separately owned OCI entries and no longer
    include W7079. Review: `review-2026-08-25T00-55-28Z.md`.
