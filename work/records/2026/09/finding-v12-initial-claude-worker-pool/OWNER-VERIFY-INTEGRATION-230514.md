# Complete Job5 integration verification in the owner/interactive context

The two reviewed files are already imported. Do not reimport or edit them.
This command is for the ordinary host context with writable disk-backed
/var/tmp; the managed context cannot supply that fixture storage. The test
fixtures own their temporary directories and cleanup. No provider or deployment
operation is involved.

```sh
set -euo pipefail
cd /home/sl/src/baton/v12/python
env PYTHONPATH=src:. BATON_V12_STACK_TEST_ROOT=/var/tmp \
  timeout --kill-after=10s 180s \
  /home/sl/.local/state/baton-v12-venv/bin/python -m unittest -v \
  tests.tools.test_pool tests.tools.test_bootstrap
```

Retain the actual result. A green result completes the remaining focused
integration verification; a failure is evidence to diagnose, not permission
to change the reviewed bytes. Slawomir retains all Git operations. W177936
session reuse remains the selected next priority, not automatically launched.
