# Third owner-run full suite

Selected checkpoint: `c2cb08877495b3124f426dc31e6fa76e37e8e1d9`. Coordinator prepared from the reviewed r2 packet after independent exit-race correction acceptance (M385121). Only checkpoint, output directory and descriptive comment changed; recipe/environment/accounting remain identical. Prior failed runs remain intact.

Run once from any directory:

```sh
bash /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r3/run-final-suite.sh
```

The wrapper checks clean v12 at the exact checkpoint, required images/tools/workspace group and actual sg adoption; refuses existing evidence, builds a fresh bundle, runs all accounted parallel/serial/supervised tests and captures source identities/resource baselines. Optional worker argument is unchanged; default all CPUs. The last two runs took about seven minutes each.

Do not change HEAD or v12 during execution. K/codexpc idle. No tests/builds run during preparation. Independent accounting/source/residue review follows the owner's run; closure and final evidence checkpoint still pending. Existing r2 PREREQUISITES.md describes the unchanged environment and prerequisites.
