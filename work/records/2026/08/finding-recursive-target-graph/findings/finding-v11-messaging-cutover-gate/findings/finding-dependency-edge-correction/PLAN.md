# Plan

Tracked as v11 Work W122, a contained child of W2. W123 independently owns the
Events-tab presentation and is not a W2 prerequisite.

1. [done] Revalidate the current model: no schema change is needed. `edges` is
   the live graph projection; immutable `add_dependency` and
   `remove_dependency` events preserve history.
2. [done] Require `rationale=` on both `block` and `unblock`; add the
   authorized correction operation with transaction-local existence,
   lifecycle, authorization, retry, and readiness checks.
3. [done] Pin the separate Events-view contract in W123 at
   `work/records/2026/08/finding-work-events-tab/`. W122 records complete typed
   payloads for that projection but does not wait for the independent UI Work.
4. [done — independently re-reviewed 2026-08-17] Cover positive removal, wrong
   actor, absent/already-removed edge, stale race, retry conflict/replay,
   last-gate wake, remaining-gate behavior, required add/remove rationales, and
   action discovery. Independent review found that correction recomputed
   readiness but omitted the same-transaction wake sweep, stranding a Work
   explicitly waiting on its last gate. Correct that path and prove both final
   and non-final removal while waiting. Human-visible journal projection
   remains the independent W123 UI contract.
5. [done — source acceptance] The pre-review focused gate and all 888 parallel
   plus serial v11 tests passed. After the wake correction, the implementer
   reported 931 parallel plus 4 serial and ACP 35/35; final independent review
   ran the 52-test dependency/phase/episode/closure gate clean. Deploy the next
   immutable CLI, then use it to correct W2's remaining live W81 and W90 edges.
   W76 closed satisfying before deployment, so no live W76 edge remains to
   correct.
6. [pending] Claim and close W2 satisfying; verify its dependents wake without
   performing any retirement deletion implicitly.
