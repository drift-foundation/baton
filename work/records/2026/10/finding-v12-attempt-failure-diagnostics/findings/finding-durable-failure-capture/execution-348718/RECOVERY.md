# What you are given: the first candidate whose gate passes — still unaccepted

Recorded by `baton.claude`, claim347396, read-only against the preserved run and
the reviewer's published digests.

## The input

`recovery-345822/candidate.patch` — the **exact candidate** run
`durable-capture-w341357-345822` returned, copied **verbatim**. No hunk was
edited, reordered or regenerated. The copy was verified against its source
**and** against the digest the reviewer published independently, and the patch's
sections were checked to name exactly the changed paths the candidate's own
result document names.

| fact | value |
| --- | --- |
| patch | `294368c55fd468a95a4375c250e560def0f4cbc0a0c8a2a3a6f2658732e83856`, 11 sections |
| head | `e9d292ede76ac4f93d4761e32779f0ea9f207648` |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| content digest | `sha256:59d666d9131eb3de7aec669eafc9be1a2dbb7c8c6a0ff8d60770b7d32109f854` |
| transport | `candidate-objects.bundle`, `806ef4006de0591755cf502bbdc2d2e743c79155a4ab115ffd5128abbcd41ec2` |
| report inside it | `W341357-VERIFICATION.json`, `a5b69ad30c2fc0be5c4c6dcb81daebba878a51d02e452ddf62d1dd3c179bc703` |
| attempt | `attempt-784e7bd67b43ccab28b62f242281f716fc068ec30a87f4490fd910eca51086c4` |

Changed paths:

```
W341357-VERIFICATION.json
v12/python/src/baton_v12/worker_manager/attempts.py
v12/python/src/baton_v12/worker_manager/documents.py
v12/python/src/baton_v12/worker_manager/failure_cause.py
v12/python/src/baton_v12/worker_manager/intake.py
v12/python/tests/manager/disk_roots.py
v12/python/tests/manager/input_roots.py
v12/python/tests/manager/test_attempt_failure_cause.py
v12/python/tests/manager/test_intake.py
v12/python/tests/manager/test_maintenance.py
v12/python/tests/manager/test_output.py
```

**The patch is the whole delivery.** The transport bundle is recorded by digest
and locator for provenance and is deliberately **not** a task input: this
campaign creates no version-control object on this host, and `prepare.py` still
refuses a declared restored buffer. Both programs **refuse** if the bundle ever
appears among the task inputs.

## What these bytes have established — and it is a lot

- **the sealed adapter gate PASSES**: `Ran 864 tests in 12.631s / OK`, exit 0,
  **no skips**, independently confirmed by the reviewer hashing the raw stream in
  place;
- the worker's own in-turn run reported 864/0/0/0 in 11.398s unittest / 11.604s
  wall — **a separate measurement of the same argv**, not an independent
  repetition;
- the **same-environment base comparison** ran: 801 tests with **2 failures at
  the pinned base** across the four shared modules, and the candidate adds 63
  tests and changes no other outcome;
- those two base failures were an **umask-dependent fixture precondition** — the
  product read was correct in both arms — and are fixed;
- `/tmp` high-water fell **13303808 → 2437120 bytes** and inodes **326 → 63**.
  A measured pressure reduction, **not** a retrospective proof of which mount
  filled run345388; that cause did not reproduce and remains unknown.

**Preserve all of it.** `FIXTURE.md` lists the specific fixture corrections the
green gate rests on. They are the floor you build from.

## What it is NOT

**Retained and STILL UNACCEPTED.** `review-2026-10-21T15-30-10Z.md` confirmed
the passing gate, retained the fixture work, and **withheld product acceptance
on two producer defects** — R1, a fresh observation conflated with a replay of
an old one; R2, recording failures discarded on the acting paths. Both are
written up in `FIXTURE.md` with citations.

Three things that look like evidence and are not:

- **the passing gate.** It is necessary and it is not acceptance. The review
  says so in the same breath as confirming it: *"a passing gate lacking these
  injections does not establish it."*
- **the 63 producer cases reporting no failure.** Useful evidence, not signoff.
  One of them — the replay test at `test_attempt_failure_cause.py:167` — proves
  value deduplication and **not** the separation of replay from a fresh
  observation.
- **the two static traces themselves.** They are code-derived, not executed.
  `TASK.md` step 2 asks you to make each a deterministic reproduction first.

## Do not restart, and do not discard

The review is explicit: **reuse this candidate and the existing preparation; do
not restart packet engineering.** The producer work inside these bytes already
answers the original `FINDING.md` defect — `failure_cause._authorizes` /
`ensure_cessation_intent` distinguish exact replay from conflicting intent — and
the gate around it now runs clean. What remains is two bounded corrections to
the same outcome/read contract, kept together because they share their call
sites.
