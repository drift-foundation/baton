# What you are given: the exact retained candidate, and it is not accepted

Recorded by `baton.claude`, claim345388, read-only against the preserved run and
the reviewer's published digests.

## The input

`recovery-345039/candidate.patch` — the **exact candidate** run
`durable-capture-w341357-345039` returned, copied **verbatim** from that run's
retained evidence. No hunk was edited, reordered or regenerated. The copy was
verified against its source and against the digest the reviewer published
independently, and the patch's sections were checked to name exactly the
changed paths the candidate's own result document names.

| fact | value |
| --- | --- |
| patch | `f9e68939c17871a475daa133cf6f9a6dc53ad11e9405b95d2644e83254a000a9`, 168606 bytes, 5 sections |
| head | `370a0aebd6a491cca49a1e2c84587c802b1afc54` |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| content digest | `sha256:1599471c21d9427e83883a6346d9e846295c3f222296c320b68933f178b0b096` |
| transport | `candidate-objects.bundle`, `9dfce290142ec0e4e8b62871dd315d08d7f6780509de0cd502567369ac4c2c89` |
| attempt | `attempt-3161b3636a90e93369568ede26d259ff607bd976a63c02e59a40fa16af310f78` |

Changed paths:

```
v12/python/src/baton_v12/worker_manager/attempts.py
v12/python/src/baton_v12/worker_manager/documents.py
v12/python/src/baton_v12/worker_manager/failure_cause.py
v12/python/src/baton_v12/worker_manager/intake.py
v12/python/tests/manager/test_attempt_failure_cause.py
```

**The patch is the whole delivery.** The transport bundle is recorded by digest
and locator for provenance and is deliberately **not** a task input: this
campaign creates no version-control object on this host and restores nothing
into the private checkout, `PROVENANCE.checkpoint.paths` stays empty, and
`prepare.py` still refuses a declared restored buffer — so that refusal keeps
its meaning. `prepare.py` and `verify-inputs.py` both **refuse** if the bundle
ever appears among the task inputs.

## What is different about this input, and why it matters

Every earlier recovery set in this campaign was a **producer split out of an
unfrozen working tree** — bytes a run was in the middle of writing when the
lease killed it, which had never been executed at all. `recovery-341360` was
that, and it stays in place as history.

**This one is different: a completed run returned it, and its gate actually
ran.** That is the first time in this campaign. What the run established:

- **864 tests in 12.817s**, exit 1, **9 failures and 7 errors**;
- **all 16 in `tests.manager.test_maintenance`.** `test_intake`,
  `test_attempts`, `test_contracts_inventory` and the candidate's own
  `test_attempt_failure_cause` — 63 cases — reported no failure;
- **the 30-second verification ceiling fits**, with room.

## What it is NOT

**It is retained and UNACCEPTED.** Its adapter disposition is
`verification-failed`, its worker disposition is `unable`, it published no
proposal, and its `acceptance` reads `unobserved`.
`review-2026-10-21T10-42-55Z.md` verified the evidence and **withheld
acceptance**.

Three things that look like evidence and are not:

- **63 producer cases reporting no failure is useful evidence, not independent
  signoff.** The reviewer says so in those words. Full producer byte review
  comes after the gate is usable.
- **The absence of this candidate's changed paths from every traceback does not
  exonerate it.** It is a real and mechanical fact — 21 frames in
  `test_maintenance.py`, 15 in `workspaces.py`, zero in any changed path — and
  it is still not a general proof of innocence.
- **"Pre-existing" is a hypothesis.** No base measurement of this argv exists in
  any run. `TASK.md` step 1 asks you to produce that comparison rather than
  assume its answer.

## Do not discard it and start again

`review-2026-10-21T10-42-55Z.md` is explicit: *"do not discard this retained
candidate and repeat open-ended authoring."* Static inspection confirmed that
the producer now distinguishes exact replay from conflicting intent in
`failure_cause._authorizes` / `ensure_cessation_intent` — the defect the
original `FINDING.md` named. That work exists. The gate around it does not yet
run.

`FIXTURE.md` is where the gate problem is described, with the file and line
citations. Read it before you change anything.
