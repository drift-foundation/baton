# Progress

Implementer-owned.

## Revalidation against the current tree — 2026-08-19

The cause is exactly as recorded. `_ready` for `unix_socket` connects
and returns True, with a comment explaining — correctly — why a
connection beats blessing an inode. What it cannot know is that the
Codex dispatcher starts listening before its targets resume and keeps
listening when one is `notLoaded`.

`EventBridge.statusSnapshot()` is unchanged and already answers the
stronger question: `ready` is true only when every configured target's
server is connected and its thread has loaded, with per-target
`connected`/`loaded`/`status` beside it. `handleRequest` serves it on
`{"control": "status"}` over the same socket. Nothing in the controller
asked.

Two things landed here since the finding was written and neither
changes it: W459 renders the dispatcher's configuration per start, and
W424 makes the bootstrapped thread resumable in the first place. This
Work is what NOTICES when a target is unloadable for any other reason.

## What changed

`readiness.type: unix_socket` gains optional `request` and `expect`.
Both together or neither — a request with nothing to assert about the
reply proves no more than the connection did, and an expectation with
no request has nothing to read.

The probe connects, sends one newline-delimited JSON line, and reads
one back, bounded at 64 KiB. `expect` matches required TOP-LEVEL reply
fields; the reply may carry any number of diagnostic fields beside
them. Values are scalars, and a nested expectation refuses: this
version matches fields and grows no expression language, as ruled.

Every way the answer can fail to arrive or fail to match — malformed,
oversized, truncated, late, closed, absent field, mismatched value —
returns False rather than raising. That is deliberate and it is what
makes the ruling's third clause work without new machinery: "not ready
yet" is a fact about the service, so the existing retry loop and the
service's own `startTimeoutSeconds` decide when it becomes a failure,
exactly as they already do for a socket that is not there. A target
still loading holds startup and then succeeds; one that never loads
fails through the ordinary rollback; one lost after startup makes
later `status` unhealthy while Baton kills and restarts nothing.

`conf/infra.example.json`'s dispatcher now carries the ruled shape, and
`docs/BATON-SETUP.md` documents the form, the all-configured-targets
policy and why an optional target is omitted rather than tolerated.

## Verification

- `tests/work/test_w482_control_readiness.py` — new, **21 passed**,
  driving the real controller as a subprocess against a fake dispatcher
  in the real one's shape: it listens immediately, and when it reports
  itself ready is the test's business.

  The defect is reproduced directly — a listening dispatcher whose
  target never loads fails startup and leaves no state behind — and
  beside it the OLD contract is kept as a live comparison: the same
  service at the same instant, probed connection-only, still reports
  healthy. That is the difference this Work makes, in the suite rather
  than in prose.

  Also covered: the healthy path; a slow target holding startup and
  then succeeding inside its window; a target lost after startup making
  `status` unhealthy while the process stays exactly where it was;
  garbage, an array, a truncated line, an oversized reply, silence and
  an immediate close all failing closed; an expectation naming a field
  the reply does not carry failing closed; extra diagnostic fields
  being welcome; `request`/`expect` refusing when configured apart; an
  empty or nested expectation refusing; connection-only remaining a
  valid form; the shipped example asking for `ready`; stop ownership
  staying process/argv based for a service whose readiness answer has
  gone wrong; and the guide documenting it.
- `test_w20_infrastructure_lifecycle.py` — **46 passed**, unchanged.
- `test_w459_fresh_contexts.py` — **39 passed**, unchanged.
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2527 passed** (parallel), **40 passed** (serial), both bridge
  suites green.

## What this does not do

No `any`-target or named-subset policy, as ruled. No expression
language in `expect`. No automatic kill or restart on an unhealthy
answer — `status` reports and the operator decides, which is the same
boundary every other part of this controller keeps.


## Response to review round 1

Both accepted. Both are the same mistake in different clothes: I wrote
a probe that could be told what it wanted to hear.

**P1 — a slow drip escaped the bounded probe.** I set a 250 ms socket
INACTIVITY timeout and then looped `recv` without a bound. A peer
sending one byte every 200 ms resets that timeout forever, so the probe
outlived the service's own `startTimeoutSeconds` — and `_wait_ready`
could not enforce anything while it was trapped inside a single probe
call. The ruling says late and partial replies fail closed WITHIN the
readiness timeout, and mine failed closed only if the peer stopped
talking.

The whole exchange now lives inside one absolute monotonic deadline,
connect included. Each operation gets what is LEFT of the budget and
nothing gets more; when it is gone the probe is False. The outer loop
retries bounded probes until the service deadline, which is the shape
the review asked for and the one that makes a single probe answer "is
it ready NOW" rather than "will it be".

**P1 — a boolean expectation accepted a number.** The matcher used
Python equality, and Python defines `True == 1`. So a dispatcher reply
of `{"ready": 1}` satisfied `expect: {"ready": true}` and marked the
service healthy — a probe that accepts a value the service never meant
is worse than no probe, because it is believed.

Matching is now in JSON's type system: a boolean matches only a
boolean. Numbers stay one domain — `1` and `1.0` are the same JSON
number — because that distinction is an encoding detail rather than a
fact about the service, which is the latitude the review explicitly
allowed.

Both reviewer regressions pass unedited, and I checked each in the
other direction: restoring Python equality fails
`test_a_boolean_expectation_does_not_accept_a_number` alone, and
removing the per-operation deadline fails
`test_a_slow_drip_cannot_outlive_the_probe_deadline` alone.

- `tests/work/test_w482_control_readiness.py` — **23 passed** (21 mine,
  2 the reviewer's).
- The complete v11 gate, `just test-v11`, exits 0 on this tree:
  **2529 passed** (parallel), **40 passed** (serial), both bridge
  suites green.
