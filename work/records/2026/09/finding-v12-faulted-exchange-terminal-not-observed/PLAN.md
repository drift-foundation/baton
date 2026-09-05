# Plan

1. Extend the closed Job Manager operations seam with one serving-only
   runtime-refresh operation. Run it for every live episode before the first
   projection of each sweep, contain a typed refusal to that stage, and do not
   call it from the read-only `status()` function. Cover ordering, refusal
   isolation, and repeated sweeps in
   `v12/python/tests/job_manager/test_delegation.py` and
   `v12/python/tests/job_manager/test_sweep.py`.
2. Compose the production refresh in `v12/python/tools/single_worker.py` from
   the attempt's naming-only OCI adapter and
   `worker_manager.reconcile_runtime`. Re-prove that this path has no
   credential-provider, command-publish, provider-turn, output, ending,
   Authority-pass, cleanup, or replacement capability.
3. Preserve exchange observation as an independent durable-file read. In
   `v12/python/tests/tools/test_single_worker.py`, deterministically publish a
   valid receipt, reachable state prefix, and correlated `faulted` terminal;
   make the fake engine report the exact container stopped before the next
   sweep; then require `exceptional`, typed `fault_code`, and canonical
   `quiescent` runtime truth from that sweep.
4. Add the restart/replay controls to the same production-seam test: reopen
   both stores and operations under a fresh incarnation and require the same
   exceptional observation, one original command, no second provider call,
   no successful-ending owner records, no new episode/runtime, and no removal
   of the retained exchange evidence. Add a second live stage whose projection
   and owed work continue when the first stage's refresh or exchange read
   refuses.
5. Add an optional observation-only factory operand to
   `v12/python/tools/job_manager.py` status and a single-worker factory that
   reconstructs launch/exchange files without opening Authority or carrying
   any mutating operation. Keep the no-factory default at `exchange: null` and
   prove both branches, factory release, and refusal handling in
   `v12/python/tests/job_manager/test_tool.py`.
6. Update `v12/python/DEPLOYMENT.md` with the distinction between serving
   reconciliation, observation-enabled status, and deliberately blind
   read-only status. Run the four authorized test modules, the existing
   exchange projection suite, and the full v12 Python suite; record exact
   counts and any environment-bound exclusions.
7. Package the bounded candidate for independent review. Do not use it for a
   new ordinary workload until review signs off on the exact digest and the
   fault/exit race passes against the production composition.
