# W72011 managed generation-7 integration

Result: **successful exact one-path import without prompt or custody-mode
propagation**, returned to `baton.ops` at Work event/pass sequence 73150 after
integrator assignment episode 73134.

## Runtime evidence

- Participant/role: `baton.merge` / `integ`
- Configuration generation: 7
- Runtime incarnation: `41a30788-3b21-474e-a0b1-9c3e4137bd54`
- Codex thread/session: `01a064a0-cc5f-7d50-b553-58d2a5622593`
- Context log: `/home/sl/baton-v11.14aecfb/log/context-integrator.log`
- Readiness log:
  `/home/sl/baton-v11.14aecfb/log/codex-integrator-readiness.log`
- Runtime journal: working sequences 73135 and 73145; idle sequence 73151
- Readiness delivery: `work:2b077949-W72011:73134:g7`

The context log identifies the fresh session as `baton.merge`, role `integ`,
configuration generation 7. The readiness log retains the exact assignment
action key above.

## Whole-set preflight

The integrator's thread record at sequence 73149 confirms, before mutation:

- exact W72011 authority for one additive function in
  `tests/work/test_w65212_proposal_integrator_deployment.py`;
- newest independent review `review-2026-09-03T00-54-11Z.md`;
- one-file proposal digest and candidate SHA-256
  `0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`;
- named base `b06c7cbe4f6ef867ea09c735958dc477e6a9e01e` and base/current
  SHA-256
  `e3a0126e55e732b5970faf4aa7d2baf80ff82de868fd82786321af9c0c9abfb4`;
- clean tracked non-symlink regular target, `sl:sl`, owner-writable mode
  `0600`; and
- no canonical overlap or drift.

## Import and verification

Only the reviewed candidate content was imported. Custody mode was not
preserved: candidate mode `0444` remained evidence-only, and the canonical
target remained mode `0600`. Final target SHA-256 equals the candidate digest,
size is 4,988 bytes, and the diff is exactly the reviewed 22 added lines with
zero deletions.

The integrator ran every review-prescribed live-checkout command:

```text
./.venv/bin/python3 -m pytest -q tests/work/test_w65212_proposal_integrator_deployment.py
4 passed

./.venv/bin/python3 -m pytest -q tests/work/test_w71459_integrator_test_change_preapproval.py tests/work/test_w71459_integrator_checkout_modes.py tests/work/test_w65212_proposal_integrator_deployment.py
11 passed

./.venv/bin/python3 -m pytest -q tests/work/test_w101_role_instructions.py tests/work/test_config.py tests/work/test_deploy_v11.py
82 passed

git diff --check
passed
```

No interactive approval request, `chmod`, `install`, staging, Git-history
mutation, or other-path edit occurred. The prepared one-file diff returned to
`baton.ops` for human Git ownership.
