# Generation 6 configuration candidate

This `baton.json` is derived from the accepted generation 5 candidate retained
in `work/records/2026/09/finding-dedicated-proposal-integrator/evidence/generation-5/`.
Its complete delta is:

- `generation` advances from 5 to 6; and
- `teams.baton.roles.integ.instructions` gains W71459's whole-path-set
  existing-test authority preflight, candidate-bounded approval, refusal, and
  never-prompt boundaries.

No participant, kind, route, root, capability, runtime, dispatcher, execution
policy, or infrastructure input changes. Generation 5 remains immutable
evidence.

Verified candidate digest:

```text
4869e1a9271c0119ec8d3074ba54d9195994e9dea7c0a2aa5490d23abc7c9114  baton.json
```

## Approver rollout and live acceptance gate

After independent review confirms the digest, exact two-field delta, and
repository guard:

1. place in W33937's handoff the case-specific approval of the independently
   signed run2c proposal digest
   `sha256:6501754bd04c3fb846776919eb4e854d1ffd6b9bf71c4d1ba43dcab06c908c44`,
   enumerating all four existing test paths and expressly approving their
   reviewed assertion or expected-behaviour changes:
   `v12/python/tests/manager/test_boundary_inventory.py`,
   `v12/python/tests/manager/test_lifecycle_composition.py`,
   `v12/python/tests/manager/test_offers.py`, and
   `v12/python/tests/manager/test_secrets.py`;
2. let W71459 leave its live claims and begin the deployment drain, establishing
   the fence that prevents released Work from being reclaimed by the old
   runtime;
3. while that drain fence is active, inspect canonical W33937 detail and dispatch
   state, then release the exact `baton.merge` assignment through its explicit
   operational gate using the freshly read claimant and episode;
4. verify that ending the final live claim moves dispatch to `paused`;
5. stop through the drained lifecycle gate, install this `baton.json` as the
   deployment configuration at mode 0600, and accept generation 6 with the
   canonical v11 `regen` invocation as `baton.slaw`;
6. start the managed stack, require lifecycle status to report every target
   healthy, and require a fresh `integrator` context whose thread id matches the
   `baton.merge` runtime publication; and
7. allow queued W33937 to be claimed by that fresh integrator, which must
   preflight the whole six-path proposal before mutation, import only the
   reviewed bytes, run W33937's bounded verification, and hand the result to
   `baton.ops` without an interactive approval request.

Do not install only the role text without accepting generation 6 and starting a
fresh managed context. Do not treat W33937's prior generic sign-off or a
cross-reference to W71459 as the explicit handoff authority required above.
