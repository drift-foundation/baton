
## 2026-10-22 — baton.claude, claim354357 — STEP 1 ENUMERATED, STEP 2 PINNED; THE CHECKOUT IS THE THIRD BOUNDED OPERATION

Claimed at snapshot354357 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354354`, zero open blockers), the
complete handoff through `work-events` (70 events, no pagination remaining) and
thread T325959 in full (5 messages, `last_seq 329708`, unchanged). Read
`review-2026-10-22T19-12-16Z.md`.

**The mechanism question is closed in my favour and I am not reopening it.**
Review354354 confirms `_reclaiming` and `Governance.overdue` enforce token
expiry, that a bounded initial lifetime is supported, and that the envelope
lacks native `stop_at` enforcement and is not to be pursued.

**Step 1 — the acquisition-to-cessation enumeration — is done**, scoped as the
review set it: only work between acquisition and cessation, using existing
operation bounds, unknowns documented rather than audited.

- **Source checkout**: `claude_agent.py:2429` runs each `plan["steps"]` argv at
  `:2432` with `timeout=CHECKOUT_SECONDS` (`:356`, 900). The production
  `checkout_plan` version-control profile is three steps — clone, detach,
  verify — so up to **2700**.
- **One provider turn**, 3600 for the pilot. The count is the product's own
  invariant, not my assumption: `baton_worker.py:2216 serve_exchange` publishes
  the receipt before dispatch as the durable replay fence, so a manager restart
  or a crash re-entry "all find it and **none of them starts a second provider
  turn**".
- **One verification**, 900 — the single `_verify` call site at `:2153`,
  reached once and only when the provider succeeded with a patch.
- **Engine calls**, individually bounded and short; not summed.

**This confirms the reviewer's warning, and it would have caught me.** Provider
plus verifier is 4500, but the checkout adds up to 2700 more inside the same
token's life — so a 4500s token would expire mid-attempt doing authorized
work. The enumeration settles it, not my earlier instinct.

**Step 2 — the policy — is pinned** in
`evidence/policy-354357/POLICY.json`: bounded initial lifetime via
`tokens.acquire`'s `seconds`; origin at the acquisition instant; persisted in
the token record so a restart re-reads rather than resets it; stop trigger
expiry → `overdue` → `_reclaiming` on the serving interval; a cleanup reserve
owed on top, with **expiry is not release** preserved as the reviewer
restated; **LIM-2**, a token bound derived per attempt from that attempt's own
operation bounds, with nothing accumulating across the two stages.

The figure that follows is **7200 as a floor, not a proved total**, and I am
not committing a number in code while two unknowns stand: whether workspace
preparation, custody and freezing/publication carry their own explicit seconds
between acquisition and cessation, and the engine-call count for one attempt.

**Steps 3–5 are not done**: the `seconds` thread into
`PreparedGovernance.reserve` and `factory` is not implemented, the focused
deterministic two-stage proof is not written, and the owner-produced failure is
not joined. **No product edit and no test run this claim** — the 31-path
composition is untouched and the review demanded no new tests for this
checkpoint. Next executable step: close the two unknowns, commit the lifetime,
implement the thread, write the proof.

No live instance, engine, provider or credential; no deployment, recovery,
migration or shared import; no version-control mutation — reads only. Prior
spending retained: claim354165 joined 14.213s; claim354259 joined 14.254s plus
serving-renewal 0.213s; claim354320 and this claim ran no product test.
