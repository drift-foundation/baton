# Deploy the reviewed generation-7 integrator role

Ledger Work: W72003

Parent: `work/records/2026/09/finding-integrator-test-change-preapproval/`

## Accepted input

Deploy only the independently reviewed candidate at
`evidence/generation-7/baton.json`, SHA-256
`e7fac15abbcb33a09df3a5c650b2e7a9127515ecbba5ce9ff222953b1b4b6b55`.
The live accepted configuration is generation 6 with SHA-256
`4869e1a9271c0119ec8d3074ba54d9195994e9dea7c0a2aa5490d23abc7c9114`.
Generation 7 changes only `generation` and
`teams.baton.roles.integ.instructions`.

## Acceptance

- Recompute the candidate digest before installation and refuse any mismatch.
- Drain dispatch and verify no live claim is orphaned before stopping the
  managed stack.
- Install the exact candidate at the deployment's required protected mode,
  accept it with canonical `regen` as `baton.slaw`, and restart normally.
- Prove the live accepted configuration is generation 7 and byte-identical to
  the retained candidate.
- Prove a fresh healthy `baton.merge` runtime/context publishes the accepted
  generation-7 integrator instructions and no quarantined predecessor remains.
- Record drain, stop, installation, acceptance, restart, runtime identity, and
  resulting configuration hashes. Do not run either proposal gate in this
  rollout Work and do not change repository files.
