"""THE HOST SIDE OF ONE RETAINED VERIFICATION: the command runner and the
seam a deployment composes it into.

W385625 Stage 1-C, under DESIGN REC-8 and the accepted Stage 1 contract.

WHY IT IS HERE AND NOT IN THE PRODUCT PACKAGE. `baton_v12` never imports
`subprocess` -- running a process is a host act, and every one of them in this
tree lives behind an adapter in `tools/` (`worker_manager.custody` and
`worker_manager.oci` document the same split for the engine client). So
`job_manager.retained_verification` owns every RULE about what may run, in
which context, against which bytes and what the account of it must contain,
and takes the execution itself as an injected port. This module is that port
and the five configuration facts around it, and it decides nothing:

    CommandRunner        runs ONE bounded command and reports what happened
    VerificationSeam     the five members `check_verification_seam` proves
    verification_seam()  composes them over one instance's own layout

WHAT THE RUNNER WILL NOT DO, and each is a refusal rather than a convention:

  * NO SHELL AND NO SEARCH. The argv is executed as the exact words the owner
    approved, with `shell=False` and no `PATH` fallback this module supplies;
    the executable is whatever the approved argv's first word resolves to in
    the environment the approved CONTEXT declares.
  * NO INHERITED ENVIRONMENT. The child gets exactly the declared environment
    and nothing else, because the environment is part of what the owner's
    `context_digest` covers -- a run that inherited this manager's variables
    would be a run in a context nobody approved.
  * NO UNBOUNDED WAIT. The approved per-command ceiling is passed to
    `subprocess.run(timeout=)`, which terminates and reaps the local child;
    the ceiling having stopped the command is reported as its own fact, so a
    timeout can never read as a passed verification.
  * NO SECOND TURN. It is called once per successor by a journalled
    operation; it holds no retry of its own and no correction, which is what
    the approved profile's zero retries and zero corrections mean on this
    side of the boundary.
"""

import json
import os
import subprocess
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import retained_verification

__all__ = ["CommandRunner", "VerificationSeam", "DEFAULT_WORKSPACES",
           "SIGNAL_BASE", "TIMEOUT_SIGNAL", "declared_context",
           "verification_seam", "workspaces_root", "main"]

# WHERE A DEPLOYMENT ALLOCATES PRIVATE VERIFICATION WORKSPACES, under its own
# state root. A sibling of the stores rather than a child of custody: the
# contract's "materialize ... into a new private verification workspace", and
# a workspace inside custody would put a writable tree inside the immutable
# evidence it is a copy of.
DEFAULT_WORKSPACES = "recovery-verification"

# The private mode of that root and of every workspace under it. 0o700
# because this manager is the only reader: the verifier runs as this process,
# and a group-readable scratch tree beside a candidate is a wider boundary
# than the one the contract declares.
PRIVATE = 0o700


# WHICH SIGNAL THE APPROVED PER-COMMAND CEILING SENDS. `subprocess.run`'s
# timeout path calls `Popen.kill`, which is SIGKILL on this platform; the
# number is named here so the retained account says what actually happened
# rather than "it stopped".
TIMEOUT_SIGNAL = 9

# The shell convention for "terminated by signal N". A durable record may not
# carry a negative integer -- `contracts.canonical` refuses one, because a
# signature that could is a signature two runtimes can disagree about -- and
# `Popen.returncode` reports a signal as `-N`. So the status travels as
# `128 + N` with the signal BESIDE it, which is the encoding every operator
# already reads out of a shell and which loses nothing: the two members
# together say exactly what the child did.
SIGNAL_BASE = 128


def _coded(returncode):
    """`(exit_status, signal)` from one `Popen.returncode`."""
    if returncode < 0:
        return SIGNAL_BASE + (-returncode), -returncode
    return returncode, None


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


class CommandRunner:
    """ONE bounded command, run as the exact approved argv, and reported.

    IT ANSWERS FACTS AND NEVER A JUDGEMENT. `exit_status` is what the process
    exited with, `timed_out` is whether the approved ceiling stopped it, and
    both streams and both instants are what actually happened. Whether that
    is a passed required verification is `retained_verification`'s reading of
    the approved profile, which is why this returns no verdict word at all:
    an adapter that decided "passed" would be the script-side precheck REC-7
    forbids, wearing the product's name.
    """

    def __init__(self, identity, *, clock, run=None):
        self._identity = identity
        self._clock = clock
        # THE CHILD-PROCESS CALL IS AN OPERAND so a case can drive this
        # adapter's own accounting -- the truncation, the instants, the
        # timeout mapping -- without starting a process, exactly as the
        # engine adapters take theirs. The DEFAULT is the real one, and the
        # acceptance uses it.
        self._run = run if run is not None else subprocess.run

    def instance(self):
        return self._identity

    def run(self, argv, *, cwd, environment, timeout_seconds):
        if type(argv) is not list or not argv \
                or any(type(one) is not str for one in argv):
            _refuse("an approved verification argv is a non-empty list of "
                    "words", category="integrity", code="schema")
        if not os.path.isabs(str(cwd)) or not os.path.isdir(str(cwd)):
            _refuse(f"the approved working directory {str(cwd)!r} is not a "
                    f"directory this runner can start a command in",
                    category="integrity", code="path")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            _refuse("an approved per-command ceiling is a positive whole "
                    "number of seconds", category="integrity", code="schema")
        started = self._clock()
        timed_out = False
        try:
            # THE EXACT WORDS, NO SHELL, NO INHERITED ENVIRONMENT, AND THE
            # STREAMS CAPTURED RATHER THAN LET OUT. A verifier that wrote to
            # this manager's own stdout would put a worker's bytes into an
            # operator's terminal and into whatever is reading it.
            answer = self._run(argv, cwd=str(cwd), env=dict(environment),
                               stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=timeout_seconds, shell=False,
                               check=False)
            status, signalled = _coded(answer.returncode)
            out, err = answer.stdout or b"", answer.stderr or b""
        except subprocess.TimeoutExpired as expired:
            # THE CEILING STOPPED IT, and what it had written is kept: a
            # retained account that dropped the output of the run the ceiling
            # ended would be evidence about less than what happened.
            #
            # AND THE STATUS IS THE SIGNAL THE CEILING ACTUALLY SENT.
            # `subprocess.run(timeout=)` kills the child and reaps it, so the
            # honest account is "terminated by SIGKILL", reported in the shell
            # convention below rather than as a negative number no durable
            # record may carry.
            timed_out = True
            status, signalled = _coded(-TIMEOUT_SIGNAL)
            out = expired.stdout or b""
            err = expired.stderr or b""
        except OSError as failure:
            # A COMMAND THAT COULD NOT START IS NOT A FAILED VERIFICATION, and
            # it is certainly not a passed one. It is a typed refusal, so the
            # pass reports it as the condition it is and journals no account
            # of a run nobody performed.
            _refuse(f"the approved verification command could not be started: "
                    f"{type(failure).__name__}", category="unavailable",
                    code="transport")
        return {"exit_status": status, "signal": signalled,
                "stdout": out, "stderr": err,
                "started_at": started, "ended_at": self._clock(),
                "timed_out": timed_out}


class VerificationSeam:
    """The five members `check_verification_seam` proves, as one object.

    IT CARRIES CONFIGURATION AND ONE CAPABILITY, exactly as
    `stage_execution.RecoveryAnalysis` does for the analysis pass: the control
    store the evidence lives in, the declared execution context whose digest
    the owner approved, the root private workspaces are allocated under, the
    host command runner, the declared analysis worker a RENEWED failure's one
    analysis is admitted under, and the owner address an item is delivered to.

    IT DECIDES NOTHING. Whether a candidate materializes, whether the context
    is the approved one, whether a verification passed, whether a review may
    be released and which owner item is delivered are all the Job manager's,
    derived from durable state.
    """

    def __init__(self, *, control, context, workspaces, runner, declaration,
                 destination):
        self.control = control
        self.context = context
        self.workspaces = workspaces
        self.runner = runner
        self.declaration = declaration
        self.destination = destination


def declared_context(configured, *, what="a declared execution context"):
    """PRODUCE one `baton.v12.recovery-verification-context/1`.

    THE PRODUCER THE DEPLOYMENT CALLS, and `owned_context` is the validator --
    `failure_analysis.declared_analysis_worker`'s split, for its reason: a
    deployment states the four facts that are its own and this composes the
    document, filling the schema from the one place that holds it. And the
    product of this function is validated before it is returned, by the same
    validator a hand-written context goes through, so there is no path into a
    decision with no context check on it.
    """
    if type(configured) is not dict:
        _refuse(f"{what} is one closed object", category="integrity",
                code="schema")
    return retained_verification.owned_context(
        dict(configured, schema=retained_verification.CONTEXT_SCHEMA),
        what=what)


def workspaces_root(instance_root):
    """The private workspace root of one instance, created if absent."""
    place = os.path.join(os.path.realpath(str(instance_root)),
                         DEFAULT_WORKSPACES)
    os.makedirs(place, mode=PRIVATE, exist_ok=True)
    os.chmod(place, PRIVATE)
    return place


def verification_seam(request):
    """Compose this deployment's verification seam over its own instance.

    THE DEFAULT FACTORY, in the shape `recovery_decision.owners` already
    takes: which owners a pass acts through is a DEPLOYMENT fact, and the
    instance's own layout says which stores it owns. Nothing is searched for
    and nothing is guessed -- the context is the deployment's declared one,
    the workspace root is this instance's own, and the runner is bound to the
    identity that instance published.
    """
    from tools.fresh_attempt_ports import instance_identity

    identity = instance_identity(request["instance"])
    return VerificationSeam(
        control=request["control_handle"],
        context=declared_context(request["context"]),
        workspaces=workspaces_root(identity["root"]),
        runner=CommandRunner(identity, clock=request["clock"]),
        declaration=request["declaration"],
        destination=request["destination"])


def main(argv=None):                                      # pragma: no cover
    """Print the declared execution context's digest, for an owner to approve.

    THE ONE READ THIS MODULE OFFERS AN OPERATOR, and it is a read: the owner's
    decision binds a `context_digest` beside the corrected argv, and an owner
    asked to approve a digest they cannot compute is an owner approving a
    number. So this takes the deployment's declared context document and
    prints the canonical document and the digest `recovery-decide
    --context-digest` compares against. It records nothing and runs nothing.
    """
    taken = list(sys.argv[1:] if argv is None else argv)
    if len(taken) != 1:
        raise SystemExit("usage: recovery_execution <declared-context.json>")
    with open(taken[0], "rb") as reading:
        configured = json.loads(reading.read().decode("utf-8"))
    context = declared_context(configured)
    json.dump({"context": context,
               "context_digest": retained_verification.context_digest(context)},
              sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
