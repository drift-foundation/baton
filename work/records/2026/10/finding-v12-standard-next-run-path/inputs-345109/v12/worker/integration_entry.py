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

AND EVERY ONE OF THEM NOW SAYS WHY, W198667. The three statuses are unchanged
-- they are this entry's accepted contract with the manager -- but each refusal
also writes ONE bounded, sanitized line to stderr through `baton_worker`'s own
refusal writer. W197661's smoke measured this entry exiting 2 with an EMPTY
stderr under a launch generation it cannot read, and the owner's ruling for
these development deployments is that evidence is captured rather than chased:
output that was never emitted cannot be captured by anything.
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


class ManagedApplyAgent:
    def __init__(self, *, bundle_root=contract.BUNDLE_TARGET, output_root=None, scratch=None):
        self.bundle_root = bundle_root
        self.output_root = output_root or baton_worker.OUTPUT_ROOT
        self.scratch = scratch

    def consider(self, seen, request):
        return {"decision": "accept", "reason": "execute the explicitly managed apply purpose"}

    def work(self, seen, declared):
        import tempfile
        if self.scratch is None:
            with tempfile.TemporaryDirectory(prefix="managed-apply-") as home:
                request, report = workload.managed_apply(self.bundle_root, seen, os.path.join(home, "execution"))
        else:
            request, report = workload.managed_apply(self.bundle_root, seen, self.scratch)
        found = [one for one in declared if one["name"] == request["output_name"] and one["type"] == "directory-result"]
        if len(found) != 1:
            raise workload.WorkloadRefusal("the managed apply report needs its declared directory output")
        place = os.path.join(self.output_root, found[0]["path"])
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "managed-apply.json"), "xb") as stream:
            stream.write(workload.canonical_text(report).encode())
        return {"disposition": "completed", "recap": "managed apply verification retained",
                "outputs": [{"name": one["name"], "status": "present" if one["name"] == request["output_name"] else "missing-optional", "result_metadata": {}} for one in declared]}


def main(*, agent=None, launch_place=baton_worker.LAUNCH_DOCUMENT,
         assignment_root=contract.ASSIGNMENT_TARGET,
         result_root=contract.RESULT_TARGET,
         bundle_root=contract.BUNDLE_TARGET,
         target_root=TARGET_TARGET, scratch=None, revision=None,
         verify=None, command_root=None, event_root=None):
    """Read the delivery, run the workload, publish exactly one result."""
    if os.path.lexists(os.path.join(bundle_root, contract.APPLY_REQUEST_DOCUMENT)):
        options = {name: value for name, value in (("command_root", command_root), ("event_root", event_root)) if value is not None}
        return baton_worker.main(agent=ManagedApplyAgent(bundle_root=bundle_root, scratch=scratch), place=launch_place, **options)
    # W198667, review 2026-09-18T02-31-51Z [2]: THE ORDINARY BRANCH IS CAPTURED
    # TOO. Only the managed-apply branch above reaches `baton_worker.main`, and
    # therefore only that branch reached the wrapper's capture -- so the
    # integration startup diagnostic this Work ADDED to the five `_refused`
    # sites below could still disappear with its container, which is the exact
    # half of the incident that made it expensive. The same capture wraps the
    # whole of this branch; it is a no-op in an image without the format module
    # and it never fails this entry.
    with baton_worker._WorkerCapture():
        return _delivered(
            agent=agent, launch_place=launch_place,
            assignment_root=assignment_root, result_root=result_root,
            bundle_root=bundle_root, target_root=target_root, scratch=scratch,
            revision=revision, verify=verify)


def _delivered(*, agent, launch_place, assignment_root, result_root,
               bundle_root, target_root, scratch, revision, verify):
    """The ordinary one-shot delivery, unchanged but for being captured."""
    try:
        launch = baton_worker.launched(baton_worker.read_launch(launch_place),
                                       launch_place)
    except (baton_worker.Uncorrelated, baton_worker.WorkerFault) as failure:
        # W198667: AND IT SAYS WHY. This branch returned 2 in silence, which
        # W197661's smoke MEASURED at the artefact: the integration candidate
        # given a launch generation it cannot read exits 2 with an EMPTY
        # stderr, while the provider candidate under the identical delivery
        # exits 3 with a bounded sentence. It does not hang -- that defect is
        # absent here -- but an operator gets nothing at all, which is the
        # half of the incident that made it expensive.
        #
        # THE STATUS IS UNCHANGED, DELIBERATELY. `2` is this entry's accepted
        # contract for "nothing correlatable" and the manager settles on it;
        # a diagnostic is not a reason to move a status a manager reads.
        return _refused("the integration runtime cannot read its launch",
                        failure, 2)
    try:
        assignment = contract.read_assignment(assignment_root)
    except contract.BundleRefusal as failure:
        return _refused("the integration runtime cannot read its assignment "
                        f"under {assignment_root}", failure, 2)

    # BEFORE ANYTHING ELSE, AND AGAIN INSIDE THE WORKLOAD. One integration
    # answers once: a terminal result means the provider turn already happened,
    # whatever this incarnation believes about it, and there is no automatic
    # recovery that takes a second one.
    try:
        if workload.existing_result(result_root) is not None:
            return 0
    except (workload.WorkloadRefusal, OSError) as failure:
        # A RESULT NAMESPACE THIS RUNTIME CANNOT READ is not permission to
        # start a turn: whether this attempt has already answered is exactly
        # the question that just went unanswered. W198667: and it is said.
        return _refused("the integration runtime cannot read the result "
                        f"namespace under {result_root}", failure, 1)

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
            result_root=result_root, revision=revision, verify=verify,
            scratch=_scratch(scratch))
    except workload.WorkloadRefusal as failure:
        # NO RESULT CAN BE COMPOSED. `integrate` answers a document for every
        # ordinary refusal and hold; what reaches here is an assignment this
        # build cannot own, which leaves no identities to answer under.
        return _refused("the integration runtime cannot own this assignment",
                        failure, 2)
    try:
        workload.publish_result(result_root, document)
    except (workload.WorkloadRefusal, OSError) as failure:
        return _refused("the integration runtime composed a result and could "
                        f"not publish it under {result_root}", failure, 1)
    return 0


def _refused(what, failure, status):
    """Say why this runtime is stopping, ONCE, on stderr, and keep the status.

    W198667, the owner's durable-development-log decision: "capture evidence so
    we don't chase tails". Capturing output cannot recover a diagnostic that
    was never emitted, and every refusal above emitted none -- W197661's smoke
    measured this entry exiting 2 with an EMPTY stderr under a launch
    generation it cannot read.

    THE SANITIZING RULE HAS ONE OWNER and it is `baton_worker`'s. This calls
    that module's own bounded, single-line, printable-ASCII refusal writer
    rather than growing a second copy here -- two spellings of "what may cross
    onto an operator's terminal" is how they drift. Its return value is its
    own status vocabulary and is DISCARDED: this entry's three statuses are its
    accepted contract with the manager and a diagnostic does not move them.

    A `WorkerFault` IS BUILT FOR THE CARRIER, not invented as a protocol event.
    Nothing here writes a frame, a receipt or a terminal; the fault is a value
    that lives exactly as long as the sentence it becomes.
    """
    message = str(failure) or type(failure).__name__
    baton_worker._startup_refusal(
        sys.stderr, baton_worker.WorkerFault("launch", f"{what}: {message}"))
    return status


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
