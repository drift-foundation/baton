# Plan

**Status — 2026-08-16:** waiting on child Work `W148`, queued to `baton.impl`,
after independent sign-off and satisfying closure of participant-readiness
Work `W136`. The deliberately minimal one-bridge/standalone-v11-producer
topology is pinned; do not revive the superseded generalized multi-protocol
bridge design.

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
4. Deploy a new immutable v11 candidate and initialize a fresh trial authority.
5. Have Slawomir, Codex and Claude operate through its TUI/CLI and v11 wake
   path, recording every readability, discovery, routing or recovery fallback
   as child Work.
6. Close this gate only after the agreed fallback-free interval and Slawomir's
   explicit retirement ruling.
