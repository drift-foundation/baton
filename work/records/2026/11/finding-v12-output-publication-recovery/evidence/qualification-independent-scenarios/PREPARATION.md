# Independent installed qualification scenarios

The original two-Job setup reused one derived Work. Each scenario now gets its own instance, Authority, one Job and evidence directory. The three setup loops (create, observe, settle) select only the first Job; duplicate-Job assertion is removed. Recovery and deadline acceptance in qualify-w385695.sh remain unchanged.

A second preparation defect was found by reading the emitted deployment: the qualification stores reader looked for workspace_storage at the top of a pooled configuration. It now requires exactly one common worker deployment workspace_storage, matching the installed pooled document. No fallback path is guessed.

Old scripts and evidence are unchanged. Image identities are reused with a provenance pointer; do not run image cleanup while either scenario uses these shared tags. Both destination/runtime checks passed. Shell syntax checks passed; source checks confirm exactly three single-Job loops and no second-Job output access. Python wrappers parse. No engine operation, install or scenario execution performed by the coordinator.

Operator: python3 /tmp/baton-w385695-independent.py recovery. This installs/configures, runs and settles only the scripted producer, then runs recovery preflight. It does not yet execute the recovery gate. Prepare deadline separately after the recovery path proves usable; its actual gate retains the selected 900-second bound.
