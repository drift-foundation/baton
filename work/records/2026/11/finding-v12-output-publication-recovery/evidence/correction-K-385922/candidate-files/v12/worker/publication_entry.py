"""THE DETERMINISTIC PUBLICATION WORKER: one confined adoption of an approved
retained output, supervised to an ABSOLUTE deadline.

W385695 internal checkpoint 2, under DESIGN REC-9 and the owner-selected
contract `work/records/2026/11/finding-v12-output-publication-recovery/
CONTRACT-PROPOSED-385720.md` sections 2 and 5.

WHAT RUNS HERE AND WHAT DOES NOT. This is the entry of the separately selected
no-provider worker a publication recovery is served by. It is run by the
UNCHANGED `baton_worker.main`, so launch validation, the exchange, the replay
fence, the output measurement and the completion envelope are the ordinary
worker's and none of them is restated here. What this file adds is the one
thing that differs: `work` copies the approved original, delivered READ-ONLY
inside `/input`, into this execution's own declared outputs.

  * NO PROVIDER, NO MODEL, NO CREDENTIAL. Nothing here imports a provider
    adapter or reads a credential path, and the answer says so in metadata the
    manager holds to zero.
  * NO PRODUCER VERIFIER. The only command this worker starts is its own copy
    of this file in `--adopt` mode.
  * THE INPUT IS NEVER WRITTEN. The staged original is a read-only mount; the
    copy opens every source entry `O_RDONLY | O_NOFOLLOW` and refuses a link
    or a special file rather than following or reading it.
  * THE BOUND IS AN INSTANT AND THE WORK IS INTERRUPTIBLE. The manager derives
    one absolute deadline from the publication stage's persisted admission and
    delivers it in the pinned request document. This worker never counts down
    from a number: it recomputes the time left against the clock on every
    wait, runs the copy as a CHILD IN ITS OWN PROCESS GROUP, and at the
    instant ends the whole group -- TERM, then KILL -- and OBSERVES that the
    group is empty before it says anything. A worker restarted with forty
    seconds left has forty seconds.
  * A MISSING OR UNREADABLE DEADLINE STARTS NOTHING. There is no default
    bound: a request that names no instant this worker can place is refused
    before the child exists.
  * THE BOUND COVERS THE WHOLE PUBLICATION, NOT ONLY THE COPY (review
    2026-11-23T18-55-03Z R2). The copy is the part this file starts; the
    measurement and the completion envelope are the ordinary worker's, and
    they run AFTER `work` returns. So the one `Bound` made when `work` begins
    is held until this process exits, and it is enforced three ways:
    `supervised` ends the copy at it and compares the completion instant
    against it; `may_complete` is the ordinary worker's own question at each
    commit point -- before the completion envelope and before the `answered`
    state -- and answers no once the instant is reached; and a watch thread
    ENDS THIS PROCESS at the instant when the main thread is still inside a
    measurement or a write that nothing else could interrupt. A process that
    ended itself published no terminal, which the manager reads as a lost
    execution and holds.
  * THE BOUND IS NEVER EXTENDED BY THE CLOCK. The remainder first observed is
    also anchored on the monotonic clock, so a wall clock that is set back
    while this worker runs cannot buy time; one set forward ends it early. A
    restarted worker reads the same instant from the same pinned document and
    finds the replay fence: it starts no second adoption at all.
  * A STOPPED ADOPTION IS NEVER A PUBLICATION. A run the bound ended is a
    typed fault or a process that ended itself; neither publishes an answered
    terminal, and whatever bytes were written stay where they are for the
    owner to inspect. A completion envelope alone, without that terminal, is
    not a publication and the manager records none from it.

WORKER-SIDE SUPERVISION IS HALF THE ENFORCEMENT. If this worker is lost, hung
or lied to about the time, the host's own control evaluation fences the stage
and the engine owner stops the container; see
`job_manager.publication_execution`. Neither half infers cessation from the
deadline having passed.
"""

import json
import os
import signal
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

# THE CHILD IS THIS SAME FILE IN `--adopt` MODE, started isolated (`-I`), and
# an isolated interpreter does not put the script's directory on its path. The
# child needs nothing of the ordinary worker -- it copies and exits -- so the
# worker is imported only by the process that IS one.
_ADOPTING = __name__ == "__main__" and sys.argv[1:2] == ["--adopt"]
if not _ADOPTING:
    import baton_worker

__all__ = ["PublicationAgent", "PUBLICATION_DOCUMENT", "REQUEST_SCHEMA",
           "REQUEST_MEMBERS", "METADATA_KEY", "SOURCE_DESTINATION",
           "Bound", "EXPIRED_STATUS", "adopt_tree", "supervised", "main"]

# THE PINNED REQUEST, at one fixed name beside the task in the read-only input
# root. Spelled here a second time because a worker in a container cannot
# import `baton_v12.job_manager.publication_execution`, which owns it; a
# conformance case holds the two spellings equal.
PUBLICATION_DOCUMENT = "publication.json"
REQUEST_SCHEMA = "baton.v12.output-publication-request/1"
REQUEST_MEMBERS = ("schema", "decision_id", "job_id", "attempt_id",
                   "deadline", "staged", "provenance", "outputs")
DEADLINE_MEMBERS = ("deadline_at", "origin", "seconds", "restart_resets")
STAGED_MEMBERS = ("root", "tree_digest", "entry_count", "total_bytes")
PROVENANCE_MEMBERS = ("root", "file", "tree_digest")
OUTPUT_ROLES = ("candidate", "provenance")
# WHERE THE STAGED ROOT IS BOUND inside the read-only input root. The ordinary
# nominated-source destination, because that is the one read-only bind the
# engine adapter composes and proves.
SOURCE_DESTINATION = "source"
# The per-output extension key, in the namespaced grammar the completion
# envelope's metadata keeps.
METADATA_KEY = "baton.v12.output-publication/1"

# HOW LONG THE GROUP IS GIVEN AFTER EACH SIGNAL before the next one, and how
# often the supervisor looks. Short on purpose: these are bounds on ENDING a
# copy that is already over its deadline, not on the copy.
TERM_GRACE_SECONDS = 2.0
KILL_GRACE_SECONDS = 5.0
POLL_SECONDS = 0.05
COPY_CHUNK = 1024 * 1024
MAX_REQUEST_BYTES = 64 * 1024
# HOW LONG THE WATCH LEAVES THE SUPERVISOR TO END AN OVERDUE COPY ITSELF
# before it ends this process instead: both signal graces and a margin. The
# supervisor's ending is the better one -- it observes the group gone and
# reports a typed fault -- so the watch only acts when that did not happen.
SUPERVISOR_GRACE_SECONDS = TERM_GRACE_SECONDS + KILL_GRACE_SECONDS + 1.0
# What this process exits with when the watch ends it at the bound: the
# conventional temporary-failure status, and deliberately not zero. Nothing
# reads it as a protocol fact -- the manager's fact is the missing terminal.
EXPIRED_STATUS = 75


def _fault(code, message):
    """One typed worker fault, in the exchange's own CLOSED code vocabulary.

    `input` is a request this worker cannot act on -- including one that
    names no deadline it can place. `agent` is an adoption that did not
    finish: ended by the bound, by a failed copy, or by a process group that
    could not be ended. The manager's exchange validator refuses any other
    word, and a terminal it cannot read would hide exactly the fault it was
    published to report.
    """
    raise baton_worker.WorkerFault(code, message)


# -- the request --------------------------------------------------------------

def _instant(text):
    """An absolute instant this worker can place, or `None`."""
    if type(text) is not str or not text:
        return None
    try:
        held = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if held.tzinfo is None:
        # A WALL TIME WITH NO ZONE IS NOT AN INSTANT. Guessing one would move
        # the bound by hours on a host whose zone is not the manager's.
        return None
    return held.astimezone(timezone.utc)


def _closed(document, members, what):
    if type(document) is not dict or sorted(document) != sorted(members):
        _fault("input", f"{what} is exactly {', '.join(members)}")
    return document


def request_document(input_root=None):
    """The manager's pinned publication request, proved before anything runs.

    READ ONCE, BOUNDED, AND HELD TO ITS CLOSED MEMBER SET. It is the manager's
    document and it is still checked, because this worker decides with it: a
    missing member discovered after the copy would be a published proposal
    nobody could describe.
    """
    place = os.path.join(input_root or baton_worker.INPUT_ROOT,
                         PUBLICATION_DOCUMENT)
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        _fault("input", "this publication worker was delivered no "
                        "publication request")
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode) \
                or found.st_size > MAX_REQUEST_BYTES:
            _fault("input", "the publication request is one bounded regular "
                            "file")
        payload = os.read(handle, MAX_REQUEST_BYTES + 1)
    finally:
        os.close(handle)
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        _fault("input", "the publication request is not one JSON document")
    _closed(document, REQUEST_MEMBERS, "a publication request")
    if document["schema"] != REQUEST_SCHEMA:
        _fault("input", f"this worker adopts under {REQUEST_SCHEMA} and the "
                        f"request names another revision")
    _closed(document["deadline"], DEADLINE_MEMBERS,
            "a publication request's deadline")
    _closed(document["staged"], STAGED_MEMBERS,
            "a publication request's staged input")
    _closed(document["provenance"], PROVENANCE_MEMBERS,
            "a publication request's provenance")
    _closed(document["outputs"], OUTPUT_ROLES,
            "a publication request's outputs")
    for member in ("decision_id", "job_id", "attempt_id"):
        if type(document[member]) is not str or not document[member]:
            _fault("input", f"a publication request names its {member}")
    for held, member in ((document["staged"], "root"),
                         (document["provenance"], "root"),
                         (document["provenance"], "file")):
        name = held[member]
        if type(name) is not str or not name or "/" in name \
                or name in (".", ".."):
            _fault("input", "a publication request names its staged roots "
                            "as single path components")
    # THE BOUND, AND THERE IS NO DEFAULT. `restart_resets` is carried so the
    # document says in its own words what kind of bound this is; a request
    # stating the opposite describes a worker-local timer and is refused.
    deadline = document["deadline"]
    if _instant(deadline["deadline_at"]) is None:
        _fault("input", "the publication request names no absolute "
                           "deadline this worker can place; a publication "
                           "without its bound is not started")
    if deadline["restart_resets"] is not False:
        _fault("input", "a publication bound is absolute; a request whose "
                           "bound resets on restart is refused")
    return document


# -- the copy, which is the child ---------------------------------------------

def adopt_tree(source, into):
    """Copy one tree of directories and regular files, following nothing.

    THE CHILD'S WHOLE JOB. Every source entry is `lstat`ed and anything that
    is not a directory or a regular file ends the copy with a nonzero status;
    every file is opened `O_NOFOLLOW` on both sides and created `O_EXCL`, so
    an existing name is a failure rather than an overwrite. Nothing is
    measured or judged here: the ordinary worker measures the result against
    the declared constraints, and the manager measures it again.
    """
    os.mkdir(into, 0o755)
    pending = [("", source)]
    while pending:
        relative, place = pending.pop()
        with os.scandir(place) as listed:
            names = sorted(one.name for one in listed)
        for name in names:
            here = os.path.join(place, name)
            there = os.path.join(into, relative, name)
            found = os.lstat(here)
            if stat.S_ISDIR(found.st_mode):
                os.mkdir(there, 0o755)
                pending.append((os.path.join(relative, name), here))
                continue
            if not stat.S_ISREG(found.st_mode):
                raise OSError(f"{here} is neither a directory nor a regular "
                              f"file")
            reading = os.open(here, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                writing = os.open(
                    there,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644)
                try:
                    while True:
                        piece = os.read(reading, COPY_CHUNK)
                        if not piece:
                            break
                        while piece:
                            piece = piece[os.write(writing, piece):]
                finally:
                    os.close(writing)
            finally:
                os.close(reading)


def _adopt_main(arguments):                               # pragma: no cover
    """`--adopt SOURCE INTO [SOURCE INTO ...]`, run only as the child."""
    if not arguments or len(arguments) % 2:
        return 2
    try:
        for index in range(0, len(arguments), 2):
            adopt_tree(arguments[index], arguments[index + 1])
    except OSError as failure:
        sys.stderr.write(f"adoption failed: {failure}\n")
        return 1
    return 0


# -- the supervisor ------------------------------------------------------------

def _group_is_gone(group):
    """Is the GROUP empty -- not, is the leader reaped."""
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _excluded(child, group):
    """End the whole group and OBSERVE that it is gone. True when it is.

    `reconciliation_task._exclude`'s rule and its reason: the leader having
    exited says nothing about what it left behind, and a signal that was sent
    is not a process that ended. TERM, then KILL, and the group is re-observed
    after each.
    """
    for signalled, patience in ((signal.SIGTERM, TERM_GRACE_SECONDS),
                                (signal.SIGKILL, KILL_GRACE_SECONDS)):
        try:
            os.killpg(group, signalled)
        except ProcessLookupError:
            pass
        except PermissionError:
            break
        until = time.monotonic() + patience
        while time.monotonic() < until:
            child.poll()
            if _group_is_gone(group):
                return True
            time.sleep(0.01)
    child.poll()
    return _group_is_gone(group)


class Bound:
    """THE ONE ABSOLUTE INSTANT, held against two clocks and never extended.

    `ends` is the instant the manager delivered, on the wall clock. The
    remainder observed when this object is made is ALSO laid along the
    monotonic clock, and the bound is reached when EITHER says so:

      * a wall clock that jumps forward reaches it early, which is the
        delivered instant doing its job;
      * a wall clock set BACK cannot reach it late, because the monotonic
        anchor still arrives when the first-observed remainder has elapsed.

    Nothing here counts down from a number the worker chose, and nothing
    resets: a second `Bound` made later from the same document can only be
    the same instant or -- after a rollback -- an earlier anchor than the wall
    clock alone would give.
    """

    def __init__(self, deadline_at, *, clock=time.time,
                 monotonic=time.monotonic):
        placed = _instant(deadline_at)
        if placed is None:
            _fault("input", "a supervised adoption needs its absolute "
                            "deadline")
        self.deadline_at = deadline_at
        self.ends = placed.timestamp()
        self._clock = clock
        self._monotonic = monotonic
        self.first_seen = clock()
        self._anchor = monotonic() + (self.ends - self.first_seen)

    def reached(self):
        return self._clock() >= self.ends \
            or self._monotonic() >= self._anchor

    def remaining(self):
        return max(0.0, min(self.ends - self._clock(),
                            self._anchor - self._monotonic()))


def supervised(argv, deadline_at, *, clock=time.time, sleep=time.sleep,
               bound=None, started=None):
    """Run one child to completion OR TO THE ABSOLUTE INSTANT, whichever first.

    ANSWERS FACTS: the child's status when it finished, `timed_out` when the
    instant was reached, and whether the process group was observed empty
    afterwards. The remainder is recomputed against the clocks on every pass,
    so a clock that jumps forward ends the run and nothing here ever holds a
    countdown of its own.

    `timed_out` IS ABOUT THE INSTANT AND NOT ABOUT WHO NOTICED (review
    2026-11-23T18-55-03Z R2). A child that finished is still compared against
    the bound at the moment its ending was observed: a copy that completed
    after the instant did not complete in time, whichever pass of this loop
    would have been the one to see the clock.

    `bound` is the caller's own `Bound` when it already holds one -- the
    agent's, which goes on governing the measurement after this returns -- and
    `started(group)` is told the child's process group once it exists.
    """
    if bound is None:
        bound = Bound(deadline_at, clock=clock)
    began = bound.first_seen
    if bound.reached():
        return {"status": None, "timed_out": True, "started": False,
                "group_gone": True, "started_at": began,
                "ended_at": began}
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
    except OSError as failure:
        _fault("agent", "this worker could not start its adoption child: "
                           + type(failure).__name__)
    # THE GROUP IDENTITY IS TAKEN AT LAUNCH, while the leader is certainly
    # alive, so the ending never depends on looking it up again.
    group = child.pid
    if started is not None:
        started(group)
    try:
        while child.poll() is None:
            if bound.reached():
                gone = _excluded(child, group)
                return {"status": None, "timed_out": True, "started": True,
                        "group_gone": gone, "started_at": began,
                        "ended_at": clock()}
            sleep(POLL_SECONDS)
    except BaseException:
        # THIS WORKER IS BEING STOPPED. The copy does not outlive it.
        _excluded(child, group)
        raise
    # ORDINARY COMPLETION IS STILL AN ENDING: nothing the child started may
    # go on writing into an output this worker is about to measure.
    gone = _excluded(child, group)
    ended = clock()
    # AND IT IS HELD TO THE INSTANT. `ended` is read once and both the answer
    # and the comparison use it, so the report cannot say an on-time ending at
    # an instant that is past the bound.
    late = ended >= bound.ends or bound.reached()
    return {"status": None if late else child.returncode, "timed_out": late,
            "started": True, "group_gone": gone, "started_at": began,
            "ended_at": ended}


# -- the agent -----------------------------------------------------------------

class PublicationAgent:
    """The deterministic publication worker's `work`, and its bound.

    ONE `Bound` PER EXECUTION, made when `work` begins and held until this
    process exits. `work` returning is NOT the end of what the bound governs:
    the ordinary worker measures and publishes afterwards, and asks
    `may_complete` at each commit point.
    """

    def __init__(self, *, input_root=None, output_root=None, source_root=None,
                 clock=time.time, sleep=time.sleep, executable=None,
                 monotonic=time.monotonic, abort=None, watch=True):
        self._input_root = input_root
        self._output_root = output_root
        # WHERE THE READ-ONLY STAGED ROOT IS BOUND. In a container that is
        # always `<input>/source`; it is an operand only so a case can hand
        # this agent the exact directory its fake engine was told to bind
        # there, which a host without a container cannot overlay.
        self._source_root = source_root
        self._clock = clock
        self._sleep = sleep
        self._monotonic = monotonic
        self._executable = executable or sys.executable
        # HOW THIS PROCESS ENDS ITSELF AT THE BOUND. `os._exit` and not an
        # exception: the main thread may be inside a read or a hash that no
        # exception raised from another thread can interrupt, and an exit
        # that ran handlers could finish a publication on its way out. It is
        # an operand only so a case run in the test process can observe the
        # decision instead of being ended by it.
        self._abort = abort if abort is not None else os._exit
        self._watching = watch
        self._bound = None
        self._group = None
        # WHAT THE MAIN THREAD IS DOING, for the watch: `copy` while the
        # supervisor owns the ending, `completing` from the moment the copy is
        # over until this process exits.
        self._phase = None
        self._overdue = None
        # LATCHED ONCE: the bound was reached and a FAULT is being reported.
        # After it nothing successful is reachable -- every commit point asks
        # `may_complete`, which now answers no for good -- so the watch stands
        # down and lets the typed fault be published rather than cutting it
        # off into a lost execution.
        self._refused = threading.Event()
        self._expired = threading.Event()
        self._stopped = threading.Event()
        self._thread = None

    def consider(self, seen, request):                    # pragma: no cover
        return {"decision": "accept",
                "reason": "adopt the approved retained output"}

    # -- the bound, after `work` has returned --------------------------------

    def may_complete(self):
        """The ordinary worker's question at each commit point.

        NO BOUND YET IS NOT PERMISSION TO COMPLETE WITHOUT ONE: this agent's
        `work` makes the bound before it starts anything, so a commit point
        reached with none means `work` did not run, and there is nothing of
        this agent's to complete.
        """
        if self._bound is None:
            return False
        if self._refused.is_set() or self._expired.is_set() \
                or self._bound.reached():
            self._refused.set()
            return False
        return True

    def stand_down(self):
        """Stop the watch. For a case that runs this agent in its own process;
        a real worker's watch ends with the process it guards."""
        self._stopped.set()
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(2.0)

    def _due(self):
        """Does the watch end this process NOW? One decision, no waiting.

        NOT WHILE A FAULT IS BEING REPORTED, and not before the instant. In
        the copy phase the supervisor is given its window first, because its
        ending observes the process group and reports a typed fault; past
        that window the supervisor itself is what is stuck.
        """
        if self._bound is None or self._refused.is_set():
            return False
        if not self._bound.reached():
            return False
        if self._phase == "copy":
            return self._monotonic() - self._overdue_since() \
                >= SUPERVISOR_GRACE_SECONDS
        return True

    def _overdue_since(self):
        if self._overdue is None:
            self._overdue = self._monotonic()
        return self._overdue

    def _expire(self):
        """End this process at the bound. Never returns in a real worker."""
        self._expired.set()
        group = self._group
        if group is not None:
            # A COPY THIS PROCESS STARTED DOES NOT OUTLIVE IT.
            try:
                os.killpg(group, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self._abort(EXPIRED_STATUS)

    def _watch(self):
        while not (self._stopped.is_set() or self._refused.is_set()):
            if self._due():
                self._expire()
                return
            # A REAL WAIT ON A REAL CLOCK, whatever clock the bound reads:
            # this thread exists for the case where nothing else is running.
            self._stopped.wait(POLL_SECONDS)

    def _enter(self, phase):
        self._phase = phase

    def _held(self, what):
        """One in-`work` gate: the bound is checked, and a reached bound is
        this agent's typed fault."""
        if not self.may_complete():
            _fault("agent",
                   "the absolute publication bound "
                   f"{self._bound.deadline_at} was reached {what}; nothing "
                   "is published")

    # -- the work --------------------------------------------------------------

    def work(self, seen, declared):
        input_root = self._input_root or baton_worker.INPUT_ROOT
        output_root = self._output_root or baton_worker.OUTPUT_ROOT
        request = request_document(input_root)
        # THE BOUND, BEFORE ANYTHING ELSE THIS EXECUTION DOES, and the watch
        # with it. From here until this process exits every path is governed.
        self._bound = Bound(request["deadline"]["deadline_at"],
                            clock=self._clock, monotonic=self._monotonic)
        self._enter("copy")
        if self._watching and self._thread is None:
            self._thread = threading.Thread(target=self._watch, daemon=True)
            self._thread.start()
        try:
            return self._adopted(request, declared, input_root, output_root)
        except BaseException:
            # A FAULT IS BEING REPORTED, by the ordinary worker, as a typed
            # ending. The watch must not cut that report off.
            self._refused.set()
            raise

    def _adopted(self, request, declared, input_root, output_root):
        delivered = baton_worker.assignment_manifest()
        if delivered.get("runtime_attempt_id") != request["attempt_id"]:
            _fault("input", "the publication request was composed for "
                            "another execution than the one this worker was "
                            "assigned")
        by_name = {one["name"]: one for one in declared}
        wanted = {role: request["outputs"][role] for role in OUTPUT_ROLES}
        if sorted(wanted.values()) != sorted(by_name) \
                or wanted["candidate"] == wanted["provenance"]:
            _fault("input", "the publication request and this execution's "
                            "declared outputs do not name the same two "
                            "outputs")
        mounted = self._source_root or os.path.join(input_root,
                                                    SOURCE_DESTINATION)
        copies = []
        for role, root in (("candidate", request["staged"]["root"]),
                           ("provenance", request["provenance"]["root"])):
            source = os.path.join(mounted, root)
            into = os.path.join(output_root, by_name[wanted[role]]["path"])
            found = os.lstat(source) if os.path.lexists(source) else None
            if found is None or not stat.S_ISDIR(found.st_mode):
                _fault("input", f"the staged {role} is not a directory in "
                                f"the read-only input this worker was "
                                f"delivered")
            if os.path.lexists(into):
                # WRITTEN ONCE. An output an interrupted pass already began is
                # not completed by a second pass over it.
                _fault("agent", f"this execution's {role} output already "
                                   f"exists; an adoption writes its declared "
                                   f"outputs once")
            copies += [source, into]
        argv = [self._executable, "-I", os.path.abspath(__file__), "--adopt"] \
            + copies

        def started(group):
            self._group = group

        ran = supervised(argv, request["deadline"]["deadline_at"],
                         clock=self._clock, sleep=self._sleep,
                         bound=self._bound, started=started)
        if ran["group_gone"]:
            self._group = None
        if ran["timed_out"]:
            _fault("agent",
                   "the absolute publication bound "
                   f"{request['deadline']['deadline_at']} ended this adoption"
                   + ("" if ran["group_gone"] else
                      "; its process group could NOT be observed gone")
                   + "; nothing is published")
        if not ran["group_gone"]:
            _fault("agent", "the adoption child left a process group this "
                               "worker could not end; nothing is published")
        if ran["status"] != 0:
            _fault("agent", f"the adoption child ended with status "
                               f"{ran['status']}; nothing is published")
        # FROM HERE THE WATCH OWNS THE INSTANT. The copy is over and what
        # remains -- this measurement, then the ordinary worker's own
        # measurement and envelope -- runs on the main thread, where a slow
        # or blocked read cannot be ended by anything but the process ending.
        self._enter("completing")
        self._held("before the adopted proposal was measured")
        # THE WORKER'S OWN MEASUREMENT, HELD TO THE STAGED DIGEST BEFORE AN
        # ENVELOPE EXISTS. The manager measures again and decides; this is the
        # worker declining to publish bytes it can already see are not the
        # ones it was delivered.
        candidate = by_name[wanted["candidate"]]
        measured = baton_worker.measured(
            os.path.join(output_root, candidate["path"]),
            candidate["constraints"])
        self._held("while the adopted proposal was measured")
        if measured["tree_digest"] != request["staged"]["tree_digest"]:
            _fault("agent", "the adopted proposal does not measure as the "
                               "staged original; nothing is published")
        account = {"published_by": "deterministic publication worker",
                   "provider_invocations": 0, "verifier_invocations": 0,
                   "adopted_from": "the approved retained original, "
                                   "delivered read-only",
                   "deadline_at": request["deadline"]["deadline_at"],
                   "supervised": True}
        return {"disposition": "completed",
                "recap": "the approved retained output was adopted "
                         "byte-for-byte under this execution's own "
                         "assignment",
                "outputs": [{"name": one["name"], "status": "present",
                             "result_metadata": {METADATA_KEY: dict(account)}}
                            for one in declared]}


def main(*, agent=None, launch_place=None, command_root=None,
         event_root=None):
    """Serve this execution's one command through the ordinary worker."""
    launch_place = launch_place or baton_worker.LAUNCH_DOCUMENT
    options = {name: value for name, value in
               (("command_root", command_root), ("event_root", event_root))
               if value is not None}
    return baton_worker.main(agent=agent or PublicationAgent(),
                             place=launch_place, **options)


if __name__ == "__main__":                                # pragma: no cover
    if _ADOPTING:
        raise SystemExit(_adopt_main(sys.argv[2:]))
    raise SystemExit(main())
