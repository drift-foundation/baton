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

  read-only source mounts and disk-backed workspaces                  W71917
  serialized integration of an approved proposal                      W71878
  the two-Job end-to-end demonstration                                W71879

None of those is stubbed. A stage whose next act belongs to one of them is
projected honestly -- `claimed`, `running`, `reviewing`, `integrating` -- and
this control plane owes nothing further on it. It also performs NO Git
operation, walks or copies no source tree, opens no container, and takes no
review or integration decision.

W71877 adds the durable worker pool beside that existing control plane. It
records immutable pool generations, virtual implementation/review workers,
principal-aware allocation and lane affinity, reserves before an offer, and
releases or quarantines only from canonical lifecycle evidence. It still owns
no provider session: the Worker Manager retains attempts and runtimes, while
W71918 owns provider-neutral cross-assignment session continuity.

AND IT IS HOST-SIDE PYTHON, one process, three stores kept apart: the
authority's, the Worker Manager's control store, and this leaf's Job store.
"""

from .delegation import (CANONICAL_OPERATIONS, INTENT_OPERANDS, OBSERVATION_MEMBERS,
                         OPERATIONS, ManagerOperations,
                         RefreshUnavailable, Unobserved,
                         canonical_operation, check_binding, observation_of,
                         stage_intent)
from .documents import (ACTS, CORRECTION_ENDINGS, EPISODE_ENDINGS,
                        REPLACEABLE_ENDINGS,
                        STAGE_KINDS, STAGE_STATES,
                        STATUS_SCHEMA, SUBMISSION_SCHEMA, TERMINAL_POLICIES,
                        TERMINAL_STAGE_STATES, owned_submission,
                        read_submission, stage_id, submission_signature)
from .creation import (CREATE_KIND, DERIVATION_MEMBERS, INSTALLED_SOURCE,
                       create_template_job, created_job_of,
                       created_job_rows, resolution_of)
from .fresh_attempt import (ADMIT_KIND, INTENT_KIND, admit_fresh_attempt,
                            fresh_attempt_of, fresh_attempt_rows,
                            successor_of, successors_of)
from .episodes import (CORRECT_KIND, advance_correction, attempting,
                       correction_operation_id, episode_by_offer, episode_of,
                       episodes_of, live_of)
from .review_driver import (IMPLEMENTATION_ENDING, PUBLICATION_SEAM,
                            REVIEW_ENDING, VERDICT_OUTCOMES,
                            end_implementation, end_review, open_correction,
                            prepare_implementation, prepare_review)
from .manager import (TICK_SECONDS, apply_offer_state, reconcile, serve,
                      sweep)
from .projection import (ACT_OUTCOMES, owed_acts, receipt_rows, receipts_of,
                         replaceable, status)
from .schema import SCHEMA_VERSION, STORE_KIND, TABLES
from .scheduler import (ALLOCATION_STATES, LANES, POOL_SCHEMA,
                        SEPARATION_CLASSES, PooledManagerOperations,
                        activate_pool, active_generation, allocation_of,
                        allocation_rows, own_pool, pool_workers,
                        reconcile_allocations, release, require_recovery,
                        reserve)
from .store import JobStore, job_signature
from .submission import (job_of, job_rows, jobs_of, stage_rows, stages_of,
                         submission_of, submission_rows, submit)
from .templates import (CONFIGURATION_SCHEMA, DEFAULT_TEMPLATE,
                        IMPLEMENTATION_REVIEW, REQUEST_SCHEMA,
                        RESOLUTION_SCHEMA, TEMPLATES, check_template,
                        owned_resolution, resolution_digest, resolve,
                        submission_for_admission, template_document,
                        template_of)

__all__ = ["ACTS", "ACT_OUTCOMES", "ALLOCATION_STATES", "CANONICAL_OPERATIONS",
           "CORRECTION_ENDINGS", "CORRECT_KIND", "EPISODE_ENDINGS",
           "IMPLEMENTATION_ENDING", "INTENT_OPERANDS",
           "OBSERVATION_MEMBERS", "OPERATIONS", "PUBLICATION_SEAM",
           "REPLACEABLE_ENDINGS", "REVIEW_ENDING", "VERDICT_OUTCOMES",
           "LANES", "POOL_SCHEMA", "PooledManagerOperations", "SCHEMA_VERSION",
           "SEPARATION_CLASSES",
           "STAGE_KINDS", "STAGE_STATES", "STATUS_SCHEMA", "STORE_KIND",
           "SUBMISSION_SCHEMA", "TABLES", "TERMINAL_POLICIES",
           "CONFIGURATION_SCHEMA", "DEFAULT_TEMPLATE",
           "IMPLEMENTATION_REVIEW", "REQUEST_SCHEMA", "RESOLUTION_SCHEMA",
           "TEMPLATES", "check_template", "owned_resolution",
           "resolution_digest", "resolve",
           "submission_for_admission", "template_document", "template_of",
           "TERMINAL_STAGE_STATES", "TICK_SECONDS", "JobStore",
           "ManagerOperations", "RefreshUnavailable", "Unobserved",
           "activate_pool", "active_generation", "advance_correction",
           "allocation_of",
           "allocation_rows", "apply_offer_state",
           "ADMIT_KIND", "INTENT_KIND", "admit_fresh_attempt",
           "CREATE_KIND", "DERIVATION_MEMBERS", "INSTALLED_SOURCE",
           "create_template_job", "created_job_of", "created_job_rows",
           "resolution_of",
           "fresh_attempt_of", "fresh_attempt_rows", "successor_of",
           "successors_of",
           "attempting", "canonical_operation",
           "check_binding", "correction_operation_id", "end_implementation",
           "end_review", "episode_by_offer", "episode_of", "episodes_of",
           "job_of", "job_rows", "job_signature", "jobs_of", "live_of",
           "observation_of", "open_correction", "owed_acts",
           "owned_submission", "prepare_implementation", "prepare_review",
           "own_pool", "pool_workers", "read_submission", "receipt_rows",
           "receipts_of", "reconcile", "reconcile_allocations", "release",
           "replaceable", "require_recovery",
           "serve", "stage_id", "stage_intent", "stage_rows", "stages_of",
           "reserve", "status", "submission_of", "submission_rows",
           "submission_signature", "submit", "sweep"]
