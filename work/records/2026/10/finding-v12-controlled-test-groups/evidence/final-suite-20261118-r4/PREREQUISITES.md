# Fourth owner-run full suite

Selected checkpoint: `f896bab03925ff1eb520adc3283da265137d5130`. Coordinator prepared from reviewed r3 packet after independent deferred-signal witness acceptance M385134. Only checkpoint, output directory and descriptive comment changed; recipe/environment/accounting remain identical. Previous failed-run evidence remains intact.

Run once:

```sh
bash /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r4/run-final-suite.sh
```

Preflight checks exact committed HEAD and clean v12, required images/tools/workspace group and actual sg adoption. Wrapper refuses existing run evidence, builds fresh bundle, runs every accounted parallel/serial/supervised test and captures source identities and resource baselines. Default all32 CPUs; prior full runs took about7 minutes. Do not change HEAD or v12 during execution. K/codexpc idle. No suite/build executed in preparation. Final accounting, independent acceptance, child/parent closure and evidence check-in remain pending.
