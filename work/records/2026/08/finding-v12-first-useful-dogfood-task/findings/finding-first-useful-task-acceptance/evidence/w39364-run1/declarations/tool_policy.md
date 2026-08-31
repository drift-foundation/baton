# W39364 run 1 — tool policy

The worker's program is the reference `baton_worker.py` with `ClaudeAgent`
injected at the documented seam. Inside the container the provider may read
the staged source, write under `/output`, and run the task's own frozen
verification command against its candidate copy.

No tool grant reaches outside the container: the engine socket is not
mounted, and the task's own prohibitions -- do not read credential bytes, do
not call a real Docker daemon from the test, do not weaken an assertion, do
not change `preflight.py` unless a test exposes a genuine defect -- travel in
the task document the worker is handed.
