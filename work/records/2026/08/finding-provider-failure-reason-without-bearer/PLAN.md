# Plan

1. [done] Revalidate both W51487 occurrences against the current Claude
   adapter, its accepted W39357 stream boundary, and the measured structured
   provider output.
2. [done] Separate the evidence-backed result (`api-error`) from the unproven
   credential-expiry/account-limit causes and record the bounded publication
   design plus adversarial regressions.
3. [done, approved in W55360 event 55479] Default supervised execution may
   read one bounded structured provider stdout document and publish only an
   adapter-owned closed category. `api_error` maps to `api-error`; every
   malformed, unknown, duplicate, trailing, invalid-UTF8 or overflow case maps
   to `unclassified`. The result is descriptive, not a causal diagnosis.
4. [done] The dated supersession is pinned here and in
   W39357's owning finding. Add the structured argv and bounded drain/parser,
   publish the closed `failure_reason`, and update focused tests. Provider
   stderr and all verification streams stay on `DEVNULL`.
5. [done] Run the complete Claude-adapter suite plus relevant worker
   image/entry regressions. Exercise the fd boundary with real chunked child
   output, overflow, malformed/hostile documents, success output, stderr, and
   verification attacks; no live credential is required or authorized.
6. [done; signed off in review-2026-09-01T03-53-13Z.md]
   Verify both directions: the mapped reason is useful and
   present when earned, while every unrecognized/raw provider byte remains
   absent from all durable and returned sinks.

## Expected implementation files

- `v12/worker/claude_agent.py`
- `v12/python/tests/manager/test_claude_agent.py`
- the dated supersession in
  `work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/finding-real-claude-adapter-image/FINDING.md`

No Docker build, provider call, credential read, or supervised attempt is part
of the implementation proof unless separately authorized.

## 2026-08-31 implementer round

7. [done] `--output-format json`, an anonymous-pipe stdout drained beside the
   child with a 64 KiB retention bound, a strict parser refusing duplicates,
   the one-entry equality map, and `provider.failure_reason` published as the
   only member derived from anything a child wrote. Stderr and both
   verification streams unchanged on `DEVNULL`.
8. [done] Twelve regressions driven through a real chunk-writing child, then
   nine mutations of the module: all nine caught. Two started as misses and
   the TESTS were corrected — the overflow guard and the duplicate-key guard
   were both unprovable as first written. Two further mutations are recorded
   as equivalent mutants rather than gaps.
9. [done] 81 adapter tests OK; 403 with the adjacent worker-entry,
   worker-image and dogfood-operator gates. No Docker build, provider call or
   credential read, as this plan's boundary requires.

## 2026-09-01 implementer round (response to review 2026-09-01T03-35-56Z)

10. [done] The drain now ends on its own clock rather than on EOF.
    `PROVIDER_DRAIN_SECONDS` (2s) starts when the provider process ends, and
    a stream that never reached EOF inside it is PARTIAL — the same word an
    over-ceiling record earns, so a descendant holding the inherited write
    end can no longer outlive `PROVIDER_SECONDS`. The reader owns and closes
    the read descriptor itself. The bound is armed in the `finally`, so the
    timeout path is covered too.
11. [done] The parser is made strict AND total. `parse_constant` refuses
    Python's `NaN`/`Infinity`/`-Infinity` extensions, and `RecursionError` is
    caught beside `ValueError`, so a bounded but deeply nested record answers
    `unclassified` instead of faulting the worker. No exception detail is
    interpolated.
12. [done] Five new regressions (three real-child descendant cases, two
    parser cases) plus two more end-to-end unusable-record cases. Seven
    mutations of the two corrected guards: all seven caught. 86 adapter tests
    OK; 409 with the adjacent worker-entry, worker-image and dogfood-operator
    gates. Still no Docker build, provider call or credential read.

The published flag is renamed `overflowed` -> `partial` throughout, because
it now means one thing with two causes: bytes dropped at the ceiling, and a
stream never proved finished. Both say the record is a prefix rather than a
record, and both are `unclassified`.
