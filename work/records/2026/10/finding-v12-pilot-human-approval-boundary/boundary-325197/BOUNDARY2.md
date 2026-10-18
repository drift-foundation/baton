# W325034 — the human approval boundary, corrected and asserted

Driver `boundary2.py`, one run, 1.018s: **49 checks passed, 2 scenarios
observed, 1 failed as it must, 0 unexpected.** Evidence bound by
`MANIFEST.json`. Source base `372281f4a473300efb474d5a6573954c15ade367`; zero
changes under `v12/`.

This supersedes in part `../boundary-325098/`, which is preserved unedited with
`SUPERSESSION.md` naming exactly what is withdrawn. The three faults review
2026-10-18T18-10-11Z found were all mine and all harness faults; the
conclusion they were used to support survives the corrected run.

## The harness now fails

`expect(...)` raises, a failed check fails its scenario, `main` exits non-zero
on any unexpected failure, and `0-harness-self-check` asserts something
deliberately false and **must** be reported failed — if it ever reports
`observed`, the run refuses, because then the checks are not checking.

## Fault 1 — the raw coordination-store read is gone

The line is resolved through the supported pair the review named:
`composed.deployment.line()` for the identity and
`worker_manager.review_cycles.line_of` to read it. The driver then asserts
that the resolved line *is* the named one and that it is bound to this Work,
rather than trusting a row's position. `0000000a-W1`, one published candidate,
all four receipts absent, accepted checkpoint present.

My earlier "no raw SQL" claim was false while `human_boundary.py` was issuing a
`SELECT` against `review_lines`. It is withdrawn there and not repeated here.

## Fault 2 — the judgments now rest on an evaluation

`ordinary_test_evidence` cross-binds observations; it does **not** establish
that the selected required task and command ran and exited zero. So this driver
evaluates the five clauses `_ordinary_tests_passed` names, by name, against the
requirements derived by their own owner (`Integration.required_tests` — derived
from the configured task and its bound input manifest, never from what the
worker reported):

| clause | required | observed |
| --- | --- | --- |
| `task_id` | `w119114-composed-lifecycle` | same |
| `task_digest` | `sha256:5d9f80e2…` | same |
| `argv` | `python3 harness.py` | same |
| `input_manifest_digest` | `sha256:76d530a9…` | same |
| `status` | exactly `0` | `0` |

**Scenario 1 drives the refusals.** Four mutated selections — another task id,
another task digest, another command, another input manifest — each withhold
the judgment, and no receipt exists after any of them. That is the check the
old step 3 skipped by hashing and writing `passed` unconditionally.

**Scenario 2 publishes only because the clauses hold** (`faults: []`), and
then drives the chain end to end:

1. `Session.verify` → `passed` by `baton.verifier-325034`; an identical
   verification **replays its exact receipt**, and a *second, different*
   verification is refused as immutable.
2. `Session.review` → `accepted` by `baton.reviewer-325034`.
3. **The approval is still absent after both judgments** — the question W321690
   raised, answered yes on the native path. The owner holds no `verify` or
   `review` grant; `pending` answers `owner_action: approval-due` with
   `approve`/`integrate`/`close` held.
4. Approval withheld, five refusals with the product's own sentences:
   `… is not approved (None), so there is no approved candidate for a human to
   have integrate`; satisfying closure refused as `approval-due`; a stale
   candidate digest, a wrong review receipt and a wrong principal
   (`'baton.reviewer-325034' does not hold the approve capability`) each
   refused. **No receipt changed across every refusal.**
5. `record bind` (the citation's prerequisite — still the operator trap the
   first 325098 run hit), then the owner's `approve` as `baton.slaw`; an
   identical approval replays and preserves the exact receipt identity.
6. `integrated` and `close --outcome satisfying` accepted; the readback answers
   `closed`, carries the selected acceptance clause, and the cited human record
   is intact.

Final receipts, each by its own actor: verification `baton.verifier-325034`,
review `baton.reviewer-325034`, approval `baton.slaw`, integration
`baton.slaw`.

## Not called, and labelled

`_accepted_receipts`, `admit_accepted`, `continue_accepted` and raw SQL are not
called — that is what makes this the human path rather than the automatic one.
Simulated and labelled in place: the engine (no daemon), the provider (injected
at the adapter's seam), and the verifier's, reviewer's and owner's *judgments*.
The integration record's own bytes say `SIMULATED` and carry forty zeroes for
the commit. No live model, live credential, container, deployment or Git
mutation.

## What still stands from 325098

The deployment guidance is unchanged and is packet material rather than a code
change: do not run automatic integration admission for a Work whose approval is
the human's; grant `verify`/`review` to participants distinct from the owner
while the owner holds `approve`/`integrate`/`close`; and bind the canonical
dossier before the owner records a human integration. No product change is
needed for single-human approval, and none is proposed.
