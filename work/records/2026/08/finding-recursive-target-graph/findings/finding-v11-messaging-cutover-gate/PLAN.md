# Plan

**Status — 2026-08-17:** W171, W179, W176 and W187 are closed satisfying. W207
independently certifies the standalone Codex readiness bridge for projection 5
and is signed off; closing it releases the final known dependency on W163.
W163's external ACP-generic client is the next implementation-planning item.
Do not revive the superseded generalized Baton multi-protocol bridge design.

The live W148 return exposed and Slawomir approved
`finding-pass-is-work-event`: remove the discussion-thread requirement from
`pass` and retain its comment as authoritative Work-event evidence. Correct
and independently review that operation before completing the W148 return.

The same trial approved `finding-message-pane-header-redundancy`: after the
threadless-pass correction, replace the lower split area's repeated subject
and selected-id heading with stable Messages-list and Message-detail labels.

Before that pane cleanup, `finding-visible-scope-message-counts` corrects the
default Work `Msg`, `My`, and `New` projections to match directly reachable
Threads. Recursive descendant totals remain explicit drill-down data and never
inflate ordinary rows or headers.

After the pane cleanup, `finding-wait-column-label` performs the final small
table-label correction: `Wait` plus `Wn+N` replaces ambiguous `Blk`/arrow
output without changing dependency semantics.

Before the next immutable candidate, `finding-codex-bridge-projection-5`
recertifies the external Codex readiness bridge for W179's projection 5.0.
The old immutable projection-4.3 deployment keeps its matching old bridge; no
cross-major alias is introduced.

1. Finish and independently review the currently queued same-schema usability
   corrections; keep v10 as the reliable channel throughout.
2. Inventory every place the current three-person trial still depends on v10:
   wake-up, message discovery, reading, response, routing, recovery, or trust.
3. Turn each gap into independently tracked v11 Work with a focused workflow
   regression; prioritize messaging over unrelated v11 feature work.
4. Exercise the human TUI and agent JSON/CLI surfaces together. Require both to
   project the same Work, Thread, Message, New, and obligation facts.
5. Run a live three-participant interval using only v11 for coordination while
   v10 remains available as a monitored safety channel.
6. Review missed/late delivery, fallback use, restarts, cursor behavior, and
   operator feedback. Repeat until no v10 fallback is needed.
7. Return the evidence to Slawomir for an explicit v10 retirement ruling; do
   not infer approval from a green automated gate alone.

## Current execution order

1. Finish and independently review the claim-heartbeat and TUI Work-search
   items outside this gate.
2. Resume this parent, implement and review
   `finding-v11-participant-readiness`.
3. Use that canonical action contract to implement the standalone v11 producer
   in `finding-v11-parallel-monitor`. Feed the existing bridge/target while
   leaving the v10 adapter and stack unchanged; prove one consumer per identity
   and no cross-authority effects.
4. Plan, implement and independently review the external ACP readiness client
   in `finding-v11-acp-agent-bridge`. Claude uses JSON-RPC over stdio; prove the
   same client can drive Gemini by configuration rather than a Baton change.
5. Deploy a new immutable v11 candidate and initialize a fresh trial authority.
6. Have Slawomir, Codex and Claude operate through its TUI/CLI and v11 wake
   path, recording every readability, discovery, routing or recovery fallback
   as child Work.
7. Close this gate only after the agreed fallback-free interval and Slawomir's
   explicit retirement ruling.
