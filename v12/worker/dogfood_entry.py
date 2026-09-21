"""The dogfood image's entrypoint: W6633's worker, this image's agent.

W39357. One line of composition, in a file, rather than a shell incantation in
the recipe -- so the injection is an artefact a reviewer can read and a case
can import, and so `ENTRYPOINT` stays exec-form with no shell in the process
tree.

WHAT IT DOES NOT DO is the whole point. It does not reimplement `main`, does
not wrap it, does not read the launch document, and does not touch the
framing: `baton_worker.main(agent=...)` is the documented seam and this uses
exactly that. A dogfood image that had its own serve loop would be a second
worker-entry implementation nobody reviewed.

W202663 (owner 227095): PID 1 REAPS NOW, AND ONLY PID 1 CHANGED. Job2's
producer killed a background test run and the orphans it left reparented to
PID 1 -- this file, which never called `wait` -- so ~498 zombies sat in the
composed 512-PID cgroup and every later `fork` failed, which broke the
authoritative verification capture. The image's contract with the manager is
unchanged: the manager still stops this container by signalling PID 1, and
PID 1 is still Python. What is new is that PID 1 is a MINIMAL SUPERVISOR --
fork the unchanged worker, forward the stop signals, reap every child the
kernel hands us, exit with the worker's own ending -- and the worker itself
runs exactly the line it always ran, one process down.

AND THE LOG ROOM IS AN EXPLICIT DELIVERY, set here for the same incident's
other half. `claude_agent._log_room` used to open the fixed `/run/baton/logs`
for ANY importer, so nested adapter code run by the provider's own shell
reached the real attempt room and declared failures into the real sidecars.
The room now travels as `BATON_ATTEMPT_LOG_ROOM`, set in the WORKER's process
by this entry -- the one process the manager launched to own that room. The
adapter composes both children's environments member by member and never
forwards this name, so nothing the provider starts, and nothing a nested test
constructs, holds a room at all.
"""

import os
import signal
import sys

from baton_worker import main
from claude_agent import ClaudeAgent, ROOM_VARIABLE

# The same fixed room `attempt_log_format.TARGET` names. Spelled here rather
# than imported so this file needs nothing the accepted images did not carry;
# `claude_agent` refuses to open anything the variable does not name. The
# MOVED spelling (owner 2026-09-21T05:54:40Z): the legacy `/run/baton/logs`
# is a disposable decoy now, so old-byte nested writers cannot reach the
# authoritative room this entry hands its own adapter.
ROOM_TARGET = "/run/baton/attempt-logs"


def supervised(run=None):
    """Run the worker one process down and reap everything else.

    `run` IS THE SAME SEAM `main(agent=...)` IS: the documented injection
    point that lets a case prove the SUPERVISION -- the reaping, the status,
    the forwarding -- without a provider or a container. `None` means the
    production line below, exactly as `agent is None` means the scripted
    default in the worker itself.

    THE WINDOW IS NAMED RATHER THAN HIDDEN: a stop signal arriving between
    the handler installation below and the fork has no worker to forward to
    and is dropped. The engine's stop escalates to SIGKILL after its grace
    period, so the container still ends; what is lost in that microsecond
    window is only the graceful form.
    """
    held = {"worker": None}

    def forward(number, _frame):
        target = held["worker"]
        if target is not None:
            os.kill(target, number)

    for one in (signal.SIGTERM, signal.SIGINT):
        signal.signal(one, forward)
    worker = os.fork()
    if worker == 0:
        # THE WORKER, EXACTLY AS BEFORE. Inherited stdin/stdout carry the
        # worker-entry conversation unchanged; the inherited handlers are put
        # back so a forwarded stop means to this process what it always did.
        for one in (signal.SIGTERM, signal.SIGINT):
            signal.signal(one, signal.SIG_DFL)
        os.environ[ROOM_VARIABLE] = ROOM_TARGET
        os._exit(main(agent=ClaudeAgent()) if run is None else run())
    held["worker"] = worker
    while True:
        try:
            ended, status = os.wait()
        except InterruptedError:
            # A forwarded signal interrupted the wait; the worker it was
            # forwarded to is still ours to collect.
            continue
        except ChildProcessError:
            # No child left at all. The loop below returns on the worker's
            # own ending, so this arrives only if the worker was already
            # collected some way this module did not write; saying "worker
            # gone, ending unknown" honestly is exiting nonzero.
            return 1
        if ended != worker:
            # AN ORPHAN, REAPED. This branch is the whole correction.
            continue
        # THE WORKER HAS ENDED; collect whatever already reparented to us
        # before answering, so the ending this returns is also the moment
        # nothing of ours is left uncollected. As PID 1 the kernel would
        # clean up behind the return anyway; outside one -- which is where
        # the cases prove these semantics -- it would not.
        while True:
            try:
                if os.waitpid(-1, os.WNOHANG) == (0, 0):
                    break
            except ChildProcessError:
                break
        if os.WIFSIGNALED(status):
            # The shell convention the engine already reads: a death by
            # signal N is exit 128+N, not a success and not a bare 1.
            return 128 + os.WTERMSIG(status)
        return os.WEXITSTATUS(status)


if __name__ == "__main__":
    sys.exit(supervised())
