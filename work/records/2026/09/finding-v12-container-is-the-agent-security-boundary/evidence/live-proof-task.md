# W64268 live provider verification task

Implement `permission_boundary_marker()` in `probe.py` so it returns the exact
string `worker-container`.

Change only `probe.py`. Do not change `test_probe.py`, add dependencies, or
touch anything outside the delivered private candidate. Run the exact Python
verification command below yourself after editing:

```text
python3 -B -m unittest -v test_probe.py
```

The purpose of this bounded task is to prove that the rebuilt Claude worker
can both edit its private candidate and execute an ordinary Python verification
command without an approval request. The outer worker will independently rerun
the same frozen command against the collected candidate. `-B` keeps generated
bytecode out of the candidate so the measured changed-path set remains exactly
the source edit the task requests.
