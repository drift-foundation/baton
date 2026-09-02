# Generation 5 deployment candidate

These files are derived from the live generation-4 deployment inputs on
2026-09-02 and contain only W65212's additive proposal-integrator changes:

- `baton.json` adds `baton.merge`, the `integ` role and route, the `merge` kind,
  and the exact role instructions; its proposed generation is 5.
- `infra.json` adds one fresh `integrator` context and one
  `codex-integrator-readiness` service.
- `codex-event-bridge.template.json` adds the `baton-integrator` target and
  includes `baton.merge` in the exact-policy provisioning recipe.
- `baton.rules` adds only the generator-emitted managed workflow rules for
  `baton.merge`; it adds no Git, shell, configuration, dispatch, runtime, or
  incident authority.

The tuner verified this candidate but did not install it. The live mailbox and
execution-policy paths are outside the managed repository writer boundary, and
accepted configuration, dispatch, and restart are `baton.slaw` operations.

Verified candidate digests:

```text
1741f88d9c80d7af559fd916d86cb049cf2affd1737728aa149dbf2de2d58f47  baton.json
7086f2ba5e432f7aa2bd08f25d9d618f5e9a36e6d771a24b4f5dadd481c3f83b  infra.json
8cfe7749fe8fe64c63c3918b5f8b152aca1013ab476436ac6d8425d81e2d4e09  codex-event-bridge.template.json
351c8b6a4f0d439e38d2f6441ff660792f00ee81c8f112208dd29b4f7dd5120f  baton.rules
```

## Approver gate

After reviewing the candidate and the repository diff:

1. let W65212's tuner claim end, drain the managed deployment, and confirm it
   reaches `paused`;
2. stop it through the drained lifecycle gate;
3. install these four files at mode 0600 over the corresponding deployment
   files (`baton.json`, `infra.json`, `codex-event-bridge.template.json`, and
   `/home/sl/.codex/rules/baton.rules`);
4. accept generation 5 with the canonical v11 `regen` invocation as
   `baton.slaw`;
5. start the managed stack and require lifecycle status to report every target
   healthy, including `baton-integrator`;
6. compare the `integrator` thread id in `run/infra-state.json` with the
   `baton.merge` runtime publication; and
7. only then route W61984 to `baton.integ` for the signed run10 proposal.

Do not start against a partial install: the dispatcher target, readiness
consumer, accepted identity, role instructions, and execution policy are one
deployment unit.
