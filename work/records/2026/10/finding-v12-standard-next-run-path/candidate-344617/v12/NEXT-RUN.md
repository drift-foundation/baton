# Next-run preparation candidate

This candidate implements reusable task composition, preflight-before-consumption
and retained recovery. It is incomplete and must not be installed as the managed
privileged execution boundary. `next_run install` captures preprovisioned operator
slots; it does not yet provision accounts, credentials, narrow admission or Work
authority through bootstrap. The existing installed managed-entry is unchanged.

The supported development entry is `python3 -m tools.next_run`, with the selected
source's `v12/python` and `v12/python/src` on PYTHONPATH. Commands:

* `install --installation ABSOLUTE-ROOT --inputs INSTALLATION.json` captures one
  configuration containing `schema: baton.next-run-installation/1` and `slots`.
  Each slot names `base` and the existing composer's nonroutine `compose` inputs.
  Runtime/source bytes are inventoried. Slots cannot share Work or Job/control
  stores. Installation performs no provider/engine operation or authority grant.
* `prepare --installation ROOT --slot SLOT --inputs TASK.json` consumes schema
  `baton.next-run-input/1`, `run_id`, `instructions`, `files` (relative selected
  source paths), `base`, `verification` argv and integer `limits` with `provider`,
  `verification`, `total`, `cleanup`. Base must equal the accepted slot base;
  total reserves provider plus verification plus cleanup. Context is fresh,
  one invocation, no automatic retry. Existing limits are never rewritten.
* Generated `commands.json` supplies authoritative `start`, `status`, `recover`
  and environment operands. Start routes through `tools.authoring_enforcement`.
  Preparation alone never starts it. Source, imported packages, controller,
  shutdown helper, task and configuration digests are checked before dispatch.
* `start --installation ROOT --run RUN` revalidates selected bytes, creates and
  validates prerequisite directories, checks image identity, then fsyncs an
  exclusive consumption record before entering the enforcement controller.
  Invalid preflight leaves the run unconsumed so the same start can be repeated
  after its prerequisite is restored. Uncertain dispatch remains consumed.
* `status --installation ROOT --run RUN` is read-only and reports retained
  receipts, never missing evidence as successful work. `recover` leaves consumed
  runs held, without replay. For a never-consumed partial preparation it records
  recovery and releases only its slot reservation, retaining all run bytes and
  permanently reserving the old run identity; prepare a new identity in that slot.

A consumed slot is not automatically recycled. Cessation evidence and a trusted
fresh-run allocation protocol remain required before this can be a complete
install-once service. Public command inputs are not an authorization mechanism;
this draft assumes a trusted operator-owned environment. It cannot replace the
root-protected managed entry or provide isolation against a caller who can mutate
its Python source/configuration. No sudo rule should point to this draft.

Focused deterministic verification:

```
python3 -m unittest tests.tools.test_next_run tests.manager.test_authoring_enforcement
```

The new suite exercises real composition, manifest/configuration validation,
source binding, filesystem preflight and durable admission. Image inspection and
controller dispatch are substituted in launcher tests. Existing enforcement
checks exercise its real guard/store owners with fake engine boundaries. No
engine/provider/Git mutation is executed. Two distinct generated tasks reaching
mocked dispatch do not prove substantive agent work or the <=60-second target.
Complete one-time privileged installation and real-owner deterministic end-to-end
startup/recovery evidence are outstanding; independent candidate acceptance and
human integration remain separate.
