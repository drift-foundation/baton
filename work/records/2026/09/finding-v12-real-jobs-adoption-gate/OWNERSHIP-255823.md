# File ownership under W247941, claim 255823

Owner reroute 255814: "Select Correction A with all constraints in
review-2026-09-24T09-46-43Z.md. Coordinate exclusive ownership of
`v12/python/src/baton_v12/worker_manager/intake.py` and focused tests."

**baton.claude holds exclusive ownership of these product files** for the
duration of W247941:

| file | held since |
| --- | --- |
| `v12/python/tools/single_worker.py` | claim 253397 |
| `v12/python/tools/stage_execution.py` | claim 253397 |
| `v12/python/src/baton_v12/worker_manager/intake.py` | **claim 255823** (owner 255814) |
| `v12/python/src/baton_v12/worker_manager/oci.py` | **claim 256145** (owner 256143) |
| `v12/python/src/baton_v12/worker_manager/custody.py` | **claim 256145** (owner 256143) |

And of the focused tests in this dossier: `test_abandonment.py`,
`test_routed_abandonment.py`, and the probe scripts beside them.

Owner reroute 256143 granted the last two on the condition that the required
paths be enumerated first; `PATHS-256145.md` is that enumeration and names
every other file in the chain together with the reason it needs no edit.

## What was NOT taken

`src/baton_v12/worker_manager/attempts.py` is **not** owned and was **not
edited**. The new reader `intake._committed_cancellation` derives the
cancellation's two identities through `attempts._cancel_operation_id` and
`attempts._authority_cancel_operation_id` and recomposes the intent document
through `documents.cancel_intent` — reading those module-level derivations the
way `deadlines.py` already reads `attempts._fixed_assignment` and
`intake._abandoned_fence`. No new shared reader was added to another module, so
the "any new shared reader has one owner" rule is satisfied by there being
none.

`src/baton_v12/worker_manager/deadlines.py` is not owned and was not edited.
The correction mirrors its accepted SHAPE and imports nothing from it.

`src/baton_v12/authority/` is not owned and was not edited. No fence check was
relaxed, removed or worked around.
