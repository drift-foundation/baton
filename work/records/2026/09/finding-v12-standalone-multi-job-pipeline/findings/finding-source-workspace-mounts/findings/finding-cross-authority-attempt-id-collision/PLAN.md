# Plan

1. Extend `JobStore.open` with one required Authority UUID, validated before
   filesystem access and persisted as the store's immutable Authority binding.
   Bump the schema; initialize new stores with the binding, and migrate both
   prior schemas atomically without rewriting existing episodes, receipts, or
   operation records. A later open under another UUID refuses untouched.
2. Derive every newly opened offer/attempt pair from the canonical
   `authority_uuid`, `stage_id`, and episode number. Route both first-episode
   and replacement-episode creation through `store.authority_uuid`; preserve
   every identity already stored and preserve the common digest shared by the
   `offer-` and `attempt-` spellings.
3. Require `--authority-uuid` on the Job Manager tool and thread it through
   `submit`, `status`, and `serve`. Update the deployment documentation. Keep
   `status` read-only and capability-free: it compares a stable identity but
   opens no Authority.
4. Make the production single-worker factory compare the Job store's bound
   UUID with its validated configuration UUID before any control-store
   configuration, profile certification, allocation, or Authority open.
5. Add and update the bounded tests in
   `v12/python/tests/job_manager/fixtures.py`, `test_store.py`,
   `test_submission.py`, `test_recovery.py`, `test_sweep.py`, `test_status.py`,
   `test_restart.py`, `test_launch.py`, and `test_tool.py`, plus
   `v12/python/tests/tools/test_single_worker.py` and the focused cases in
   `v12/python/tests/manager/test_oci.py`. This is the explicit scheduled
   authority to adjust existing UUID/identity expectations and CLI operands in
   those files; do not weaken unrelated assertions.
6. Prove same-authority replay, cross-authority separation, process-restart
   stability, first/replacement parity, schema-1/schema-2 identity
   preservation, wrong-UUID untouched refusal, production preflight ordering,
   foreign-label refusal, and one fresh independent OCI start.
7. Run the focused Job Manager, production single-worker, and OCI slices, then
   the full v12 Python suite. Package the exact source, documentation, dossier,
   and scheduled test path set for independent review. Rollout with fresh Job
   and control stores; do not describe legacy episode rows as repaired.
