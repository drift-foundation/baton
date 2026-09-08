"""The integration image's entrypoint: one shot, from durable files.

W110935. The composition, in a file, rather than a shell incantation in the
recipe -- so the injection is an artefact a reviewer can read and a case can
import, and so `ENTRYPOINT` stays exec-form with no shell in the process tree.
`dogfood_entry.py` is the same shape for the same reasons.

WHAT IT IS NOT. This is not `baton_worker.main`. It reads no `describe`/`work`
command frames, writes no worker terminal, and treats stdout as nothing at all:
an integration runtime is launched to do ONE thing from files that are already
on disk, and the framing loop's whole purpose -- a manager holding a pipe and
asking questions -- is a channel this runtime does not have and does not need.
What it DOES reuse is that module's launch readers, because the launch document
is one contract with one owner and a second reader of it would be a second
answer to "what is this container".

THE FIVE FIXED NAMES ARE THE CONTRACT'S, not operands. A path this program
could be told is a path a container can be pointed at wrongly, which is the
whole reason the environment transport was retired. They are keyword arguments
here for one reason: a test drives this entry over disposable directories, and
the alternative -- a case that could only run against absolute container paths
-- is a case that never runs.

THE THREE EXIT STATUSES, and each says something different to the manager:

  0  a terminal result is at the fixed name: this run published one, or found
     one already there and deliberately did not take a second provider turn.
  1  the delivery could not be completed: a result namespace this runtime
     cannot read, or a composed result it could not publish. The manager
     observes `waiting` and the operator has an unfinished delivery to look at.
  2  nothing correlatable: no readable launch document or no readable
     assignment, so there is no attempt to compose a result ABOUT. This is the
     same ruling the ordinary worker follows for a missing launch -- write no
     frame, exit 2, and let the Worker Manager settle it from the engine.
"""

import os
import sys

import baton_worker
import integration_contract as contract
import integration_workload as workload

# THE FOURTH FIXED CONTAINER PATH, spelled a second time because a worker in a
# container cannot import `baton_v12.integration.oci_delivery`, which owns it.
# A conformance case holds the two spellings equal, exactly as the assignment
# and result namespaces are held.
TARGET_TARGET = "/target"


def main(*, agent=None, launch_place=baton_worker.LAUNCH_DOCUMENT,
         assignment_root=contract.ASSIGNMENT_TARGET,
         result_root=contract.RESULT_TARGET,
         bundle_root=contract.BUNDLE_TARGET,
         target_root=TARGET_TARGET, scratch=None, revision=None):
    """Read the delivery, run the workload, publish exactly one result."""
    try:
        launch = baton_worker.launched(baton_worker.read_launch(launch_place),
                                       launch_place)
    except (baton_worker.Uncorrelated, baton_worker.WorkerFault):
        return 2
    try:
        assignment = contract.read_assignment(assignment_root)
    except contract.BundleRefusal:
        return 2

    # BEFORE ANYTHING ELSE, AND AGAIN INSIDE THE WORKLOAD. One integration
    # answers once: a terminal result means the provider turn already happened,
    # whatever this incarnation believes about it, and there is no automatic
    # recovery that takes a second one.
    try:
        if workload.existing_result(result_root) is not None:
            return 0
    except (workload.WorkloadRefusal, OSError):
        # A RESULT NAMESPACE THIS RUNTIME CANNOT READ is not permission to
        # start a turn: whether this attempt has already answered is exactly
        # the question that just went unanswered.
        return 1

    if agent is None:
        # THE REAL ADAPTER, constructed exactly the way `dogfood_entry` does.
        # The import is here rather than at module scope so a case can drive
        # this entry with its own agent without the provider adapter's own
        # imports having to resolve.
        from claude_agent import ClaudeAgent

        agent = ClaudeAgent()
    try:
        document = workload.integrate(
            agent=agent, assignment=assignment, launch=launch,
            bundle_root=bundle_root, target_root=target_root,
            result_root=result_root, revision=revision,
            scratch=_scratch(scratch))
    except workload.WorkloadRefusal:
        # NO RESULT CAN BE COMPOSED. `integrate` answers a document for every
        # ordinary refusal and hold; what reaches here is an assignment this
        # build cannot own, which leaves no identities to answer under.
        return 2
    try:
        workload.publish_result(result_root, document)
    except (workload.WorkloadRefusal, OSError):
        return 1
    return 0


def _scratch(place):
    """One bounded private directory for this turn's report, mode 0700."""
    if place is not None:
        return place
    import tempfile

    made = tempfile.mkdtemp(prefix="integration-")
    os.chmod(made, 0o700)
    return made


if __name__ == "__main__":
    sys.exit(main())
