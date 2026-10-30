# What you are given: the second retained candidate, and it is not accepted

Recorded by `baton.claude`, claim345822, read-only against the preserved run and
the reviewer's published digests.

## The input

`recovery-345388/candidate.patch` — the **exact candidate** run
`durable-capture-w341357-345388` returned, copied **verbatim** from that run's
retained evidence. No hunk was edited, reordered or regenerated. The copy was
verified against its source **and** against the digest the reviewer published
independently, and the patch's sections were checked to name exactly the changed
paths the candidate's own result document names.

| fact | value |
| --- | --- |
| patch | `5030be0867af2c7989638ca2cf369891672b876b80f6245e6344d0db793d3458`, 9 sections |
| head | `5a7d5976ab48c2e66ad5ae610e526362a0990871` |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| content digest | `sha256:5c0fca78e650ad9ff75b07e86a3d9b1c80e094d93087ab13c1c7566e0c3ca391` |
| transport | `candidate-objects.bundle`, `c6d1706d40fb0792b15b18a8606c156825e88fdc8ee23d50aef7285d6fb58eb9` |
| attempt | `attempt-5b3a73432204dc215833b3bf2c6b22d9dc47ddf733e9f66eafc445aea6d15083` |

Changed paths:

```
v12/python/src/baton_v12/worker_manager/attempts.py
v12/python/src/baton_v12/worker_manager/documents.py
v12/python/src/baton_v12/worker_manager/failure_cause.py
v12/python/src/baton_v12/worker_manager/intake.py
v12/python/tests/manager/disk_roots.py
v12/python/tests/manager/input_roots.py
v12/python/tests/manager/test_attempt_failure_cause.py
v12/python/tests/manager/test_maintenance.py
v12/python/tests/manager/test_output.py
```

The four producer sections and `test_attempt_failure_cause.py` are
**byte-identical** to the first retained candidate from run345039 — the reviewer
compared them section by section. The four other sections canonicalise fixture
paths and surface missing child stdout.

**The patch is the whole delivery.** The transport bundle is recorded by digest
and locator for provenance and is deliberately **not** a task input: this
campaign creates no version-control object on this host and restores nothing
into the private checkout, `PROVENANCE.checkpoint.paths` stays empty, and
`prepare.py` still refuses a declared restored buffer. Both programs **refuse**
if the bundle ever appears among the task inputs.

## What these bytes have already shown

- the gate runs to completion and the 30-second ceiling fits:
  **864 tests in 12.515s**;
- **zero assertion failures** — every path-comparison and line-layout refusal
  that failed the run before now passes;
- **16 failing subtest outcomes in FOUR methods**, every chain ending in
  `sqlite3.OperationalError: database or disk is full`.

## What they are NOT

**Retained and UNACCEPTED.** Adapter disposition `verification-failed`, worker
disposition `unable`, no published proposal, `acceptance: unobserved`.
`review-2026-10-21T11-37-58Z.md` verified the evidence and **withheld
acceptance**. Full independent producer byte acceptance remains owed **after**
an assessable passing gate.

Three things that look like evidence and are not — see `FIXTURE.md` for the
detail:

- **the equal test count.** 864 both runs proves nothing about assertion
  coverage: a test that fails during setup never proved its later assertions.
- **the disappearance of the old error class.** Progress, not proof that every
  earlier affected assertion reached and passed.
- **the configured capacities.** `tmp_bytes 67108864` and friends are
  configured limits, **not observed free space**, and no observation of the
  exhausted filesystem exists.

## Do not discard it and start again

`review-2026-10-21T11-37-58Z.md` requires a **minimal** continuation reusing
unchanged machinery, and the producer work inside these bytes is not the subject
of this turn. Static inspection has already confirmed the producer distinguishes
exact replay from conflicting intent in `failure_cause._authorizes` /
`ensure_cessation_intent`, and its 63 focused cases report no failure — **useful
evidence, not signoff.**

`FIXTURE.md` is where the remaining problem is described, with citations. Read
it before you change anything, and **measure before you conclude.**
