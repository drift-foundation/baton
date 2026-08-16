# Plan

**Status — 2026-08-16:** round-two changes requested on v11 Work `W148` in
`review-2026-08-16T18-15-02Z.md`; returning to `baton.impl`. Parent `W24`
remains waiting on this gate. The earlier generalized multi-source adapter and
two-complete-stack plans are superseded by the one-bridge/standalone-v11-
producer decisions in `FINDING.md`.

1. Add the external `codex-baton-bridge` entry point and protocol-11 action-set
   parser under the Codex event-bridge integration; leave Baton core, the v10
   monitor and stack configuration unchanged. Do not ship the superseded
   `baton-v11-monitor` name.
2. Render v11 action readiness through the trusted compact Baton event path,
   carrying only stable action locators and the standing-policy cue.
3. Implement whole-set level-triggered suppression, removal/reappearance,
   restart discovery, forwarding retry and bounded backoff.
4. Add focused Node tests for every acceptance case named in `FINDING.md`, and
   rerun the unchanged v10 adapter and complete bridge suites.
5. Independently review the implementation before any live process is changed.
6. Launch the v11 producer beside the existing v10 stack, targeting this same
   Codex thread; prove one consumer per identity and no cross-authority effects.
7. Return the live evidence to the parent gate. Stack integration and removal
   of the v10 source wait for the explicit v10-retirement ruling.
