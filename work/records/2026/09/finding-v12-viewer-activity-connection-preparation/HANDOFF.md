# Preparation complete — owner selection next

baton.claude, W177937 claim 178694, after owner poke 178688 lifted the
queued-preparation stop hold. Dossier-only preparation is complete and returns
to `baton.ops`.

- **`PACKET.md`** SHA256
  `aaa30c9dd529d245f89b1d0645a00c85d5769a94b31b8b8d1411751646a7db28`
  is the concrete connection packet:
  the existing chain named at each hop, the display rule, the exact three-file
  change boundary, focused verification, no-mutation guarantees and the serial
  handoff.
- **`BASELINE-177937.json`** SHA256
  `74549807f5749f955bdcfc60129db7d5f2107c4e076e2c9b277ce2758522f329`
  records nineteen read inputs at their exact bytes and two positive
  revalidations.

## The finding that shapes the whole packet

**The wiring already exists end to end, and exactly one line ignores it.**
`attempts.attempt_activity_of` → `delegation.py:989` → `projection.py:703`
already put the count in the status document at `stage["runtime"]["activity"]`.
`job_viewer.py:323` then discards it and writes the constant `UNKNOWN`.

So this is a read, a format and a predicate — **not a new backend, not a second
reader, not a protocol change**. W167896's first stated rule is that the viewer
has no backend, and this connection does not get to spend it. If the tuner finds
the member missing on some path, that is a producer-side finding to report, not
a licence to add a second read path.

## The rule that matters most

Owner ruling M174788 makes the instant **manager receipt time**, never evidence
of continued provider activity. So:

- non-terminal stage, positive count → count **and relative age**;
- terminal stage (`changes-requested`, `completed`, `exceptional`) → count **and
  the absolute instant, marked historical — never a relative age**;
- everything else → `unknown`.

**A relative age beside `completed` is the exact misreading this Work exists to
prevent**, and it is the case the packet makes a required test.

Two absences stay distinct: no runtime or no activity member is "nobody looked";
a recorded attempt with `bytes_observed` of `None` is "nothing observed yet".
Both render `unknown`, and **neither ever renders `0`** — the producer cannot
emit a zero, and a zero would read as "observed, and empty", which this manager
has no evidence for.

The injected/restored-HOME unknown needs **no viewer special case and must not
acquire one**: an unproved baseline publishes nothing, so the existing `unknown`
branch already covers it, and a "baseline unproved" display would be the viewer
reporting a fact it does not hold.

## Revalidated, not assumed

All three viewer paths match accepted W167896 `candidate-168326.json`. All six
W61599 producer paths match **the accepted correction** `correction-178427`,
independently accepted by `review-2026-09-15T14-06-58Z.md` — not the candidate I
originally submitted. Both comparisons are recorded in BASELINE.

## Serial handoff

1. **baton.tuner implements**, per owner reroute 178690: three files only —
   `tools/job_viewer.py`, `tests/tools/test_job_viewer.py`, `JOB-VIEWER.md`.
   No producer rewrite, rich UI, broad suites, baseline repair or live
   execution. Revalidate the three viewer hashes before editing, since W161234 B
   is editing adjacent files under the same claimant.
2. **Two existing assertions change meaning and must be rewritten, not deleted**
   — the `activity\s+unknown` requirements in `NothingIsInvented` and the
   model-free completion case. Their fixtures carry no activity, so they become
   the "absent stays unknown" cases.
3. **The module docstring and `JOB-VIEWER.md` both say "until it exists,
   activity here is `unknown`"**. That sentence becomes false on the day this
   lands and must be replaced in the same change.
4. **This unblocks W61599** (`add_dependency` 178689). Only after independent
   acceptance may visible counts be claimed delivered.
5. **W177938 follows**, per the owner's stated order.

## Limits

Preparation only. No product or test file edited, no test, probe, provider,
engine, build, installation or version-control operation. **New measured
verification 0 s.** Nothing protected was opened; all writes are inside this
dossier. Preparation acceptance is not implementation or release acceptance.
