"""W71878: the target-global integration coordinator, and W101490: the generic
integration runtime boundary composed on top of it.

One store, outside every Authority-bound `JobStore`, owning each configured
canonical target's queue order and its single live integration lease. See
`schema` for why it cannot be a Job-store table, and `runtime` for what a
fenced integration is composed from -- documents that name no version control
system, and a writable target access that cannot exist without a live grant.
"""

from .queue import (TARGET_SCHEMA, abandon_lease, activate_target,
                    block_target, enqueue, entries_of, grant_lease,
                    lease_of, live_grant, refuse_entry, release_lease,
                    settle_integrated, target_of)
from .schema import (ENTRY_STATES, LEASE_STATES, SCHEMA_VERSION, STORE_KIND,
                     TARGET_STATES)
from .execution import INTEGRATION_PORT, OUTCOMES, integrate_next
from .driver import (admit_accepted, continue_accepted,
                     publish_candidate, retain_proposal)
from .runtime import (ASSIGNMENT_SCHEMA, HOLD_SCHEMA, PROFILE_SCHEMA,
                      RESULT_SCHEMA, compose_assignment, hold_account,
                      integration_profile, observed_result, target_access)
from .store import IntegrationStore, integration_signature

__all__ = ["ASSIGNMENT_SCHEMA", "ENTRY_STATES", "HOLD_SCHEMA",
           "INTEGRATION_PORT", "OUTCOMES", "integrate_next",
           "IntegrationStore", "LEASE_STATES", "PROFILE_SCHEMA",
           "RESULT_SCHEMA", "SCHEMA_VERSION", "STORE_KIND", "TARGET_SCHEMA",
           "TARGET_STATES", "abandon_lease", "activate_target", "block_target",
           "compose_assignment", "enqueue", "entries_of", "grant_lease",
           "hold_account", "integration_profile", "integration_signature",
           "lease_of", "live_grant", "observed_result", "refuse_entry",
           "release_lease", "settle_integrated", "target_access",
           "target_of", "admit_accepted", "continue_accepted",
           "publish_candidate",
           "retain_proposal"]
