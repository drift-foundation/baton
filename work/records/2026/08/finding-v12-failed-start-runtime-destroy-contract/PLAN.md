# Plan

1. [done] Revalidated the existing intake-receipt destroy body, document owner,
   adapter boundary and provider behavior against the current tree.
2. [done] Pinned the distinct five-member manager/provider command, separate
   adapter callable, frozen-1.0 non-change, exact-build binding, shared removal
   core, custody semantics and non-overlap with W32648.
3. [ready for implementation] Add the closed constructor and separate adapter
   capability. Factor only the shared exact removal/observation/provider-ending
   core; preserve the existing `destroy` signature and behavior.
4. [ready for implementation] Add positive, missing/extra/null, cross-body,
   no-fallback, exact removal/absence, uncertain/surviving runtime, provider
   retry, process reconstruction and retained-result sentinel cases. Extend
   boundary/contracts/operand/secret inventories without editing frozen 1.0.
5. Run the prepared v12 focused provider and inventory gates plus the applicable
   real-engine removal case. Return for independent review; only satisfying
   closure unblocks W32648's composition.

## 2026-08-29 — implemented

3. [done] `documents.failed_start_destroy_command` and the closed
   `destroy.failed-start-command` contract; `OciAdapter.destroy_failed_start`.
   The shared removal/observation/provider-ending core is factored as
   `_removed`; `destroy`'s signature and behaviour are unchanged and its
   member set is untouched.
4. [done] `tests/manager/test_failed_start_destroy.py` -- positive, missing,
   extra, null runtime, cross-body, no-fallback, exact removal and absence,
   surviving and uncertain runtimes, provider retry, process reconstruction and
   the retained-result sentinel; plus the frozen-schema measurements. The
   boundary, contracts, operand and secret inventories name the new digest and
   callable.
5. [done] Focused and full daemon-free gates, and
   `tests/manager/test_failed_start_destroy_engine.py` -- the applicable
   real-engine removal, registered serial beside the other engine-owning
   suites. Every guard measured by removal.

## 2026-08-29 — independent review

6. [done] Preserve a successful transcript of the exact
   `tests.manager.test_failed_start_destroy_engine` gate from an
   engine-capable runner. The existing gate transcript never entered the
   serial phase, and the managed reviewer is denied access to the Docker
   socket. `evidence/w34998-engine-gate-2026-08-29.txt` now records the exact
   four-case module and the 83-test engine-owning serial registry passing.
