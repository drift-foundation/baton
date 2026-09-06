"""W71878: the target-global integration coordinator.

One store, outside every Authority-bound `JobStore`, owning each configured
canonical target's queue order and its single live integration lease. See
`schema` for why it cannot be a Job-store table.
"""

from .queue import (TARGET_SCHEMA, abandon_lease, activate_target,
                    block_target, enqueue, entries_of, grant_lease,
                    lease_of, live_grant, refuse_entry, release_lease,
                    settle_integrated, target_of)
from .schema import (ENTRY_STATES, LEASE_STATES, SCHEMA_VERSION, STORE_KIND,
                     TARGET_STATES)
from .store import IntegrationStore, integration_signature

__all__ = ["ENTRY_STATES", "IntegrationStore", "LEASE_STATES",
           "SCHEMA_VERSION", "STORE_KIND", "TARGET_SCHEMA", "TARGET_STATES",
           "abandon_lease", "activate_target", "block_target", "enqueue",
           "entries_of", "grant_lease", "integration_signature", "lease_of",
           "live_grant", "refuse_entry", "release_lease", "settle_integrated",
           "target_of"]
