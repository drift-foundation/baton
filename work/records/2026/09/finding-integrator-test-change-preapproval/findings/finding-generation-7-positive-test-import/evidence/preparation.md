# W72011 proposal preparation

Prepared by `baton.tuner` at `2026-09-03T00:51:43Z`.

- Proposal: `file:///tmp/w72011/proposal`
- Base commit: `b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`
- Exact path: `tests/work/test_w65212_proposal_integrator_deployment.py`
- Base and pre/post-preparation canonical SHA-256:
  `e3a0126e55e732b5970faf4aa7d2baf80ff82de868fd82786321af9c0c9abfb4`
- Candidate SHA-256 / one-file proposal digest:
  `0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`
- Canonical target: clean tracked non-symlink regular file, `sl:sl`, mode
  `0600`, 4,063 bytes
- Frozen candidate: regular file, `sl:sl`, custody mode `0444`, 4,988 bytes

The candidate adds exactly one function,
`test_generation_seven_candidate_authorizes_scheduled_test_imports`. It loads
the retained generation-7 configuration, asserts generation 7, and checks that
the integrator instructions preserve the accepted Work scope, explicitly
scheduled-test authority, pre-mutation owner-write requirement, non-preserving
custody transfer, final byte/mode verification, and non-interactive no-prompt
rule. It changes, removes, or weakens no existing assertion, fixture, or
expected behaviour.

Focused preparation check:

```text
env PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python3 -c "load the candidate module; set REPO to the canonical checkout; run test_generation_seven_candidate_authorizes_scheduled_test_imports()"
status: 0
```

The target was rechecked after candidate creation and remained scoped-Git-clean
at the base hash and mode `0600`. No canonical file was changed. Independent
review must recompute and bind these exact candidate bytes and the one-path set
before managed integration.
