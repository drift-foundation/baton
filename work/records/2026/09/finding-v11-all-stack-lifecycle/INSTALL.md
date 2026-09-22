# Current deployment installation

After independent review, place this dossier's `infra-stacks.json` at
`/home/sl/baton-v11.14aecfb/infra-stacks.json`. It declares only the existing
main, rview-pc and codx-pc sets. Before writing, confirm the destination is absent
(otherwise inspect and reconcile; do not overwrite unknown registration), and
confirm all three registered infra.json files remain the intended deployment.

The source checkout's justfile and tools/infra_deployment.py take effect directly;
this does not require a Baton binary deployment, schema change, config generation
change, service stop/start or dispatch resume. Run `just status /home/sl/baton-v11`
from the checkout on the host to report all three stacks. A stopped coder or
reviewer should make overall status unsuccessful, not be silently omitted.
An isolated process-namespace sandbox cannot assess host PIDs correctly; use the
host execution context for operational status.

At the next owner-selected restart:

```sh
just stop /home/sl/baton-v11
```

Only after successful stop:

```sh
just start /home/sl/baton-v11
just status /home/sl/baton-v11
```

These are immediate lifecycle commands, not drain requests. Drain and inspect
global dispatch first if active Work must finish. Start does not resume dispatch.

For bounded maintenance or fallback use the unchanged controller directly:

```sh
python3 tools/infra.py status /home/sl/baton-v11.14aecfb/rview-pc
```

Changing this to stop/start affects only that stack. Retain registration and
state if an aggregate command fails; inspect the per-stack report and apply the
existing explicit recovery. No automatic rollback kills previously healthy
stacks, and no raw lifecycle-state deletion is part of recovery.
