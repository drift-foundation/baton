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
