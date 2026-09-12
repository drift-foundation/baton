# W71879 observation and command-error correction — claim149854

This is a correction candidate derived from prepared-149488. Its run8 identities
are historical fixture metadata. Do not run provision, prepare, build, render or
run.py against run8: its one-attempt authorization was consumed and no retry is
authorized. Copied operator recipes and image context are preserved dependencies
for offline checks, not new host instructions. No actual inputs or review markers
are copied. Future packaging must bind accepted source and fresh authorized state.

Owner149847 explicitly assigns the read-only observation binding correction in
v12/python/tools/stage_execution.py, plus runner command-error retention. The
observer shares only pure binding/Work/target/allocation readers; local read-only
Authority/coordinator handles remain unchanged. No serving deployment or sessions.
The successor runner retains the final2000 command-stderr characters and reports
truncation/exit status. This is manager/engine error text already captured by the
runner; it does not read provider streams or credentials. Very long exception
messages can still exceed the bound, with that omission explicit. Structured safe
provider diagnostics and first-failure priority remain unchanged.

Only run.py, runner-helpers.json and copied test_run8_preparation.py behavior
expectation change here; README clarifies scope, test_command_errors.py adds five
focused cases. All other copied files remain byte-identical, including the three
other execution helpers, deployment, tasks, policies and integration instructions.
W71830 standing test-change authority applies; existing assertions preserve every
guard while accounting for the exact scheduled runner delta.

From /home/sl/src/baton, offline verification:

```sh
python3 -B work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149854/verify_offline.py
```

63 tests pass. Five focused product observation checks also pass, including the
new two-producer real-account regression, unknown/foreign Job refusal, both bound
producer selections, existing fresh-process read-only handle/disposal/nonmutation
coverage and observation-only exchange behavior. Initial red regression retained.
Full evidence, exact source delta/custody and spending are in
../evidence/observation-correction-149854 and ../OBSERVATION-CORRECTION-149854.md.
Run8 outcome remains failed/unconfirmed; no corrected read was run over its stores.
Direct independent review; no retry, repair, broader hardening or new planning gate.
