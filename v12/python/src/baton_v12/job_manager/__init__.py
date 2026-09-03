"""The v12 persistent Job manager, in Python.

W71875, the first leaf of W71830's standalone multi-Job milestone. This
package is the host-side CONTROL PLANE: it accepts a bounded multi-Job
submission, persists it atomically and idempotently, derives which stage act
is owed next from dependencies and canonical state, delegates that act to the
already-public v12 operation that owns it, records the receipt, and answers a
read-only status projection. A long-lived process ticks that derivation; a
restarted one resumes from the two stores rather than from an operator.

WHAT IT COMPOSES. `baton_v12.worker_manager` already owns restart-safe offers,
claims, attempts, agent sessions, runtime start and reconciliation, output
freeze, custody, intake, retention and cleanup, and `baton_v12.authority` owns
Work, claim, proposal and review/integration receipts. Those are the
operations this package calls. It adds no second account of any of them: a
stage's state is DERIVED at read time from this store's receipts plus the
manager's own public reads, and there is no column here that says an offer was
claimed or a runtime is up.

WHAT IS DELIBERATELY ABSENT, so a reader can tell a boundary from a gap:

  worker-pool selection and runtime profiles instantiated per worker  W71877
  read-only source mounts and disk-backed workspaces                  W71917
  immutable review checkpoints and same-line correction cycles        W71918
  serialized integration of an approved proposal                      W71878
  the two-Job end-to-end demonstration                                W71879

None of those is stubbed. A stage whose next act belongs to one of them is
projected honestly -- `claimed`, `running`, `reviewing`, `integrating` -- and
this control plane owes nothing further on it. It also performs NO Git
operation, walks or copies no source tree, opens no container, and takes no
review or integration decision.

AND IT IS HOST-SIDE PYTHON, one process, three stores kept apart: the
authority's, the Worker Manager's control store, and this leaf's Job store.
"""

from .delegation import (CANONICAL_OPERATIONS, INTENT_OPERANDS, OBSERVATION_MEMBERS,
                         OPERATIONS, ManagerOperations, Unobserved,
                         canonical_operation, check_binding, observation_of,
                         stage_intent)
from .documents import (ACTS, STAGE_KINDS, STAGE_STATES, STATUS_SCHEMA,
                        SUBMISSION_SCHEMA, TERMINAL_POLICIES,
                        TERMINAL_STAGE_STATES, owned_submission,
                        read_submission, stage_id, submission_signature)
from .manager import TICK_SECONDS, reconcile, serve, sweep
from .projection import (ACT_OUTCOMES, owed_acts, receipt_rows,
                         receipts_of, status)
from .schema import SCHEMA_VERSION, STORE_KIND, TABLES
from .store import JobStore, job_signature
from .submission import (job_of, job_rows, jobs_of, stage_rows, stages_of,
                         submission_of, submission_rows, submit)

__all__ = ["ACTS", "ACT_OUTCOMES", "CANONICAL_OPERATIONS", "INTENT_OPERANDS",
           "OBSERVATION_MEMBERS", "OPERATIONS", "SCHEMA_VERSION",
           "STAGE_KINDS", "STAGE_STATES", "STATUS_SCHEMA", "STORE_KIND",
           "SUBMISSION_SCHEMA", "TABLES", "TERMINAL_POLICIES",
           "TERMINAL_STAGE_STATES", "TICK_SECONDS", "JobStore",
           "ManagerOperations", "Unobserved", "canonical_operation",
           "check_binding", "job_of", "job_rows", "job_signature", "jobs_of",
           "observation_of", "owed_acts", "owned_submission",
           "read_submission", "receipt_rows",
           "receipts_of", "reconcile",
           "serve", "stage_id", "stage_intent", "stage_rows", "stages_of",
           "status", "submission_of", "submission_rows",
           "submission_signature", "submit", "sweep"]
