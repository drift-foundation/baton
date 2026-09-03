# Prove scheduled reviewed test import under generation 7

Ledger Work: W72011

Parent: `work/records/2026/09/finding-integrator-test-change-preapproval/`

Dependency: W72003.

## Explicit scheduled test authority

This Work authorizes one additive test-function change, and no deletion or
weakening, in exactly:

`tests/work/test_w65212_proposal_integrator_deployment.py`

The function should add a bounded generation-7 deployment assertion without
changing existing test bodies or expectations. No other production, test,
dossier, or configuration path is authorized in the proposal.

At planning time the target is a tracked, non-symlink regular file owned by
`sl:sl`, mode `0600`, with SHA-256
`e3a0126e55e732b5970faf4aa7d2baf80ff82de868fd82786321af9c0c9abfb4`.
The proposal base is commit
`b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`. The operator must revalidate all
of these facts immediately before proposal creation and again during
integration; drift requires a newly reviewed gate, not substitution.

## Acceptance

- W72003 has closed satisfying and the live integrator is a fresh healthy
  generation-7 context.
- A separately retained immutable proposal changes only the exact test path
  above, names the exact base, and is independently reviewed. The review binds
  its digest, enumerates the test path, and confirms the change is additive
  and within this scheduled scope.
- Before mutation, `baton.merge` records whole-set authority, type, base-byte,
  and owner-write preflight for the existing target.
- The managed integrator imports the reviewed candidate bytes without an
  interactive approval request and without `install`, `chmod`, or another
  privileged replacement.
- Final target bytes equal the reviewed candidate, its preflight mode remains
  exactly unchanged, and custody `0444` does not reach the checkout.
- The focused test module and parent W71459/W65212 guards pass from the live
  checkout; the Work retains runtime identity, proposal/review digest, hashes,
  modes, commands, and handoff evidence.

## Candidate preparation — 2026-09-03

**Observed:** the canonical target remains byte-identical to the recorded base
and planning-time hash, with the recorded tracked regular-file type, `sl:sl`
ownership, and mode `0600`.

**Confirmed:** the separately retained proposal changes only the authorized
test path and adds one assertion-only function over the retained generation-7
integrator role. No existing body or expectation changes. Its exact locator,
candidate digest, delta, focused preparation check, and unchanged-target proof
are retained in `evidence/preparation.md`. Independent review and managed
integration remain pending.

## Live positive-gate result — 2026-09-03

**Confirmed:** fresh generation-7 `baton.merge` assignment episode 73134
accepted the exact scheduled test authority and independently reviewed
one-path candidate. Whole-set scope/review/digest/path, base/type/owner-write,
and overlap preflight passed before mutation. The managed integrator imported
only the reviewed content without a prompt or privileged replacement.

The final target is byte-identical to candidate SHA-256
`0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`,
while its preflight mode remains `0600`; custody mode `0444` did not propagate.
The exact reviewed diff contains 22 added lines and no deletion. All focused
and broader review-prescribed gates passed (4, 11, and 82 tests respectively),
as did `git diff --check`. Runtime and final evidence are retained in
`evidence/managed-integration.md` and `evidence/final-assessment.md`.

## Independent review — 2026-09-03

**Confirmed:** `review-2026-09-03T00-54-11Z.md` approves the one-path proposal
at candidate digest
`0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`
for the bounded managed integration attempt. The canonical target remains
byte-identical to base, a non-symlink regular file owned by `sl:sl`, and
owner-writable mode `0600`. The frozen candidate is mode `0444`, which is
custody evidence and must not propagate.

The proposal adds 22 lines and deletes none. Its only change is the expressly
scheduled `test_generation_seven_candidate_authorizes_scheduled_test_imports`;
no existing assertion, fixture, or expected behaviour changes. All four test
functions in the candidate module pass against the current repository sources.

Managed integration and its retained preflight, final byte/mode, runtime, test,
and diff evidence remain pending. Approval is limited to the exact reviewed
bytes at the exact named path.
