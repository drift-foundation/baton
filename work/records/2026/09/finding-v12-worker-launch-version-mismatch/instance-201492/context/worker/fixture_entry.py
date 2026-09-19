"""The one fixture image's entrypoint: dispatch on the DELIVERY it was given.

W197661 claim201492. WHY ONE IMAGE AT ALL, and it is a contract rather than a
preference: `tools/single_worker.py:267` refuses a worker whose `image_digest`
differs from its Job input manifest's `worker_image_digest`, and a Job names
exactly ONE input manifest. claim201324 built a second image for the integrator
and three validators refused the composition. So every role of this fixture runs
one artefact, and what differs is which workload the DELIVERY selects.

THE DISCRIMINATOR IS A FACT THE MANAGER PUT ON DISK, not a name and not an
environment variable. An integration attempt is delivered an integration
ASSIGNMENT at `integration_contract.ASSIGNMENT_TARGET`; a producer or reviewer
attempt is not. `integration_entry` already dispatches this way -- it chooses
its managed-apply branch on the presence of the apply-request document -- so
this follows the accepted code's own idiom rather than inventing one.

WHAT THE PROPOSING RECIPE WARNED ABOUT, AND WHY THIS IS NOT IT. That recipe
removed a second agent because "two agents in one image, one selected by a
branch nobody reads" had silently run the WRONG one: `_scripted_default()` was a
FALLBACK, reached by omission, and nothing failed when it was wrong. This is the
opposite shape -- an explicit dispatch on what the manager actually delivered,
with no default: a delivery this entry cannot classify REFUSES rather than
falling back to either workload, because a container that quietly proposes when
it was asked to integrate is exactly the defect that cost this campaign an
episode.

THE THREE ANSWERS, and each is a different fact:

  AN INTEGRATION ASSIGNMENT IS READABLE -- this is an integrator, and the real
  `integration_entry.main` is entered with this fixture's `ImportingAgent`. That
  entry then makes its OWN managed-apply decision, which this one does not
  second-guess: with `integration_preparation` false the ordinary branch runs
  the injected agent, and with it true the entry ignores the agent and runs
  `ManagedApplyAgent`, which is its business and not this file's.

  THE ASSIGNMENT NAMESPACE IS ABSENT -- this is a producer or reviewer turn, and
  `baton_worker.main` is entered with `ProposingAgent`, which decides between
  proposing and reviewing from the manager's own `role`.

  THE NAMESPACE IS THERE AND UNREADABLE -- nothing is classified. This says so
  on stderr and exits 2, the status this campaign's own integration entry uses
  for "nothing correlatable", rather than guessing.
"""

import os
import sys

import integration_contract as contract

__all__ = ["DELIVERY_INTEGRATION", "DELIVERY_WORKER", "delivery", "main"]

DELIVERY_INTEGRATION = "integration"
DELIVERY_WORKER = "worker"


def delivery(assignment_root=None):
    """Which workload this container was delivered, or `None` for neither.

    ABSENT IS AN ANSWER AND UNREADABLE IS NOT. A namespace that is not there is
    an ordinary producer or reviewer attempt; a namespace that is there and
    cannot be read as an assignment is a delivery this build cannot classify,
    and classifying it anyway is how a container proposes when it was asked to
    integrate.
    """
    root = assignment_root or contract.ASSIGNMENT_TARGET
    if not os.path.lexists(root):
        return DELIVERY_WORKER
    try:
        contract.read_assignment(root)
    except contract.BundleRefusal:
        return None
    except OSError:
        return None
    return DELIVERY_INTEGRATION


def main(argv=None, *, assignment_root=None, **options):
    """Enter the workload this delivery names, or refuse to enter either."""
    held = delivery(assignment_root)
    if held == DELIVERY_INTEGRATION:
        import integration_entry
        from importing_agent import ImportingAgent

        return integration_entry.main(agent=ImportingAgent(), **options)
    if held == DELIVERY_WORKER:
        import baton_worker
        from proposing_agent import ProposingAgent

        return baton_worker.main(agent=ProposingAgent(), **options)
    # NO FALLBACK. The one thing a two-workload image must never do.
    print("baton-worker: this container was given an integration assignment "
          "namespace it cannot read, so it can be neither a producer nor an "
          "integrator; nothing was run", file=sys.stderr, flush=True)
    return 2


if __name__ == "__main__":
    sys.exit(main())
