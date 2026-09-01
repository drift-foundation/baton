# Plan: make live worker progress observable

1. [done 2026-09-01] Record the observed W52821 visibility gap and the ruling
   that native JSONL with jq-style presentation is sufficient for the first
   useful operator view.
2. [done 2026-09-01; W61599] Bind this record to one follow-up Baton Work and
   link it from the v12 roadmap.
3. [done 2026-09-01; reviewer revalidation] Trace both current agents, the
   worker-entry transport, the dogfood channel, allocation, OCI custody and
   existing credential-exclusion decisions. The exact seams and conflict are
   recorded in `FINDING.md`.
4. [done 2026-09-01; approver ruling] Preserve W43972, W39357 and section 13.
   Authorize only a closed provider-safe durable progress surface and defer raw
   native content until credential isolation or enforceable sanitization
   exists. Live container-private operator inspection remains diagnostic, not
   a Baton result artifact.
5. [projection mechanics implemented; changes requested; see below] First
   expose the credential-free default liveness projection: monotonic
   native-session bytes observed and manager receipt time of latest activity.
   Then add a manager-minted attempt-result/log capability,
   manager-owned incremental safe-progress capture and a stable relative
   locator under the attempt's `result/logs/`. Establish incomplete state
   before start; only clean EOF/exit marks complete; restart preserves partial
   evidence without claiming the prior exec stream can be reattached.
6. [pending after item 5] Add an unbuffered CLI follow operation that
   pretty-prints bounded JSON records and preserves non-JSON lines without
   accepting an arbitrary host path.
7. [pending; after item 6 and after the first v12 viewer exists] Render the
   same live stream in attempt details with follow/pause and jq-style syntax
   coloring.
8. [pending] Add focused incremental-write, success, failure, forced-stop,
   restart, access-boundary, and no-container-inspection verification.
9. [parked hardening] Decide bounded retention, search/filter UX and whether a
   separately credential-isolated or enforceably sanitized native transcript
   is valuable from evidence gathered in real use. The closed safe progress
   stream is the MVP contract, not a temporary exception.

## 2026-09-01 first implementer round (`baton.claude`)

5a. [implemented but changes requested in review-2026-09-01T14-24-19Z.md]
    The control-store projection and outer-stderr counter. Schema 14 carries
    `activity_bytes` and `activity_at` on the attempt under a both-or-neither
    CHECK; `attempts.observe_activity` writes a monotonic cumulative total with
    the manager's own instant, deciding monotonicity inside the write; and
    `attempts.attempt_activity_of` reads it, distinguishing an id naming no
    attempt from a recorded attempt nobody has observed. The dogfood
    deployment's `_Channel` counts every drained byte -- including the ones
    past its bounded window -- and publishes the running total through an
    injected observer that opens, writes and closes its own store handle.
    Nothing the worker produced reaches a durable surface: what crosses is a
    length. Independent review found that outer stderr is not the Claude
    adapter's native session stream, synchronous publication can backpressure
    the required drain, and a zero-byte EOF stamps an instant despite no
    activity. This slice is not yet end to end.
5b. [not started] The rest of item 5: the manager-minted attempt-result/log
    capability, the sink created and marked incomplete BEFORE runtime start,
    the clean-EOF-only complete mark, restart preserving partial evidence, and
    the stable relative locator under `result/logs/`.
10. [done; changes requested] Independent review of 5a before 5b is built on
    it. `review-2026-09-01T14-24-19Z.md` records two P1 findings and one P2;
    do not build 5b on the current observation wiring.
11. [next correction] Wire an actual provider-safe native-session growth
    source, decouple publication from the mandatory stream drain with a
    bounded/coalescing handoff, and preserve absence until positive activity
    unless a separate observation instant is explicitly ruled.
12. [next verification/review] Prove real provider growth reaches the manager
    before completion, unrelated stderr is not mislabeled, and a blocked
    publisher cannot backpressure a stream larger than pipe capacity. Re-run
    the focused manager/deployment suite and review again before item 5b.
