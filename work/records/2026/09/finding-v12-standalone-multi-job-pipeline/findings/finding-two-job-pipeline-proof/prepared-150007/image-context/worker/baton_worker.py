"""`baton-worker`: the entry point inside the OCI reference image.

W6633 (`work/records/2026/08/finding-v12-oci-reference-worker-image`), the
third bounded child of W5.

THIS FILE IS THE WHOLE PROGRAM INSIDE THE IMAGE, and that is the design rather
than a convenience. It imports NOTHING from `baton_v12` -- no manager, no
contracts package, no authority client -- because a worker that could import
the manager is a worker one bug away from holding the manager's capabilities.
The image contains this file, the scripted agent beside it, and a Python
runtime. A case asserts the import graph, because "we did not import it" is a
property somebody will break by accident.

THE CHANNEL IS FRAMED AND BOUNDED. Every message is one length-prefixed JSON
document on stdin, answered on stdout:

    <decimal byte length>\\n<exactly that many bytes of UTF-8 JSON>

Length-prefixed rather than newline-delimited because a newline is a byte an
agent's own output legitimately contains, and a protocol whose framing a
payload can forge is a protocol with no framing. Both directions are bounded:
an oversized frame is refused before it is read into memory, not after.

EXCLUSIVE STDIO IS TRANSPORT ISOLATION, NOT MESSAGE IDENTITY -- the approved
`baton.worker-entry/1` ruling, 2026-08-25. Every request is one closed object
carrying `protocol`, `session`, `operation_id` and `operation`, plus only that
operation's own members. `session` is the manager-minted identity of THIS
exact container session and arrives in the launch document;
`operation_id` is consumed once within it. Wrong-session, replayed, missing,
unknown and extra members all refuse before the request reaches the agent.

`session` ARRIVES IN THE LAUNCH DOCUMENT (W26291), not in the environment.
Every container holds its own identity for its own lifetime, and no message
turns one container into another: a fresh container is what a continuation was
replaced by.

THERE IS EXACTLY ONE RESPONSE SHAPE AND IT IS CORRELATED. Every response
echoes the request's own `protocol`, `session` and `operation_id`; a success
adds `ok: true` and `answer`, a fault adds `ok: false`, `code` and a bounded
`message`. A frame this program cannot read an identity envelope out of is
answered with NO FRAME at all and a non-zero exit -- the ruling forbids
inventing an uncorrelated response shape, and the Worker Manager already owns
the launched session and settles that case from the engine.

THIS PROGRAM IS TOLD WHAT IT IS BY ONE VERSIONED DOCUMENT (W26291).
`/run/baton/launch.json` is a manager-authored, read-only, bind-mounted file
carrying exactly `schema`, `session`, `contract` and `role`. The path is a
CONSTANT of the contract, so there is no locator variable to point this program
somewhere else, and the read is bounded, no-follow and descriptor-proved for
the same reason every other worker-visible byte in this campaign is.

THERE IS NO ENVIRONMENT FALLBACK, and that is the ruling rather than an
omission. `BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`,
`BATON_WORKER_CONTRACT` and `BATON_WORKER_ROLE` are not read here at all: a
container started with only those does not start. A compatibility path would be
the second live contract the supersession exists to end.

AND THERE IS NO POSTURE. V12 launches one runtime, consent/execution is not a
runtime axis, and the ruling says there is no constant to transport -- so this
program does not ask what kind of container it is, and `OPERATIONS` is the one
runtime's set rather than a map keyed by an answer nothing supplies. `consider`
is KEPT as a known operation this runtime is not entitled to, which is what
makes refusing it mean something; deleting an operation from a ruled protocol
is a larger decision than the Work that removed the axis.

A BOOTSTRAP FAULT IS LATCHED, NOT RAISED -- the approved startup-correlation
ruling. A container whose launch document is present and
correlatable but not valid still has an operable framing loop, so it reads
exactly one bounded request identity envelope, returns the pending failure
through the ordinary correlated fault, and exits non-zero. A document that
cannot be read AT ALL is the other case: there is no session to answer under,
so nothing is written and the manager settles the start it already owns.

Reading that envelope grants no task, workspace, output, tool or agent
capability: a latched failure can never reach the agent.

STDOUT IS THE CHANNEL, so nothing else may write to it. Diagnostics go to
stderr. A `print` in an agent would otherwise corrupt a frame, which is the
kind of failure that looks like a protocol bug for a week.
"""

import hashlib
import json
import os
import re
import stat
import sys
import time

PROTOCOL = "baton.worker-entry/1"

# The frame ceiling, both directions. Large enough for a human contract and a
# recap, small enough that a hostile or looping agent cannot exhaust the
# container's memory through the channel.
MAX_FRAME = 1 << 20

# The identity members are bounded on their own, well below the frame: an
# identity is a label the manager minted, not a payload.
MAX_IDENTITY = 256

# The bounded prose a fault carries. Bounded here rather than at the frame so
# the worker reports what went wrong instead of the channel reporting that the
# worker said too much.
MAX_MESSAGE = 2000

# W26291: THE FIXED LAUNCH DOCUMENT, and every constant of it.
#
# The path is the contract's, not an operand: a path this program could be told
# is a path a container can be pointed at wrongly, and the whole reason the
# retired environment transport was replaced is that its vocabulary had no
# version and no closed shape. `schema` carries the version IN THE NAME, so a
# document from another generation is refused by an equality test rather than
# by parsing a version member and deciding what to do about it.
LAUNCH_DOCUMENT = "/run/baton/launch.json"
LAUNCH_SCHEMA = "baton.worker-launch/1"
LAUNCH_MEMBERS = ("schema", "session", "contract", "role")

# W81857: THE SECOND LAUNCH VERSION, AND WHAT IT SELECTS.
#
# `/1` describes what this container IS and says nothing about how it is
# spoken to, so a worker reading only `/1` can only ever enter the stdin
# framing loop below. That loop is correct and stays -- it is the diagnostic
# and test transport -- but it makes the manager process that holds the pipe
# the only reader of a provider's answer, and a manager restart then destroys
# protocol state a healthy container is still producing.
#
# `/2` adds exactly one member, `transport`, and the value below is the only
# one this program knows. THE VERSION IS CHECKED BY EQUALITY and the member
# set is decided by the version: there is no document that is valid under both
# and no discovery path that turns a mounted directory into a contract. A
# container that finds `/run/baton/exchange/command` present and is launched
# under `/1` uses stdin, because a worker that picked its own transport from
# the filesystem would be a worker with two live contracts and no version --
# which is what the retired environment channel was.
EXCHANGE_LAUNCH_SCHEMA = "baton.worker-launch/2"
EXCHANGE_LAUNCH_MEMBERS = LAUNCH_MEMBERS + ("transport",)
EXCHANGE_TRANSPORT = "baton.worker-exchange/1"

# THE TWO FIXED EXCHANGE ROOTS, constants of the contract at both ends and
# never operands. The manager writes the command namespace and mounts it
# READ-ONLY here; this program writes the event namespace and the manager
# reads it as untrusted input. A path this program could be told is a path a
# container can be pointed at wrongly, which is the same rule the launch
# document's own fixed path states.
COMMAND_ROOT = "/run/baton/exchange/command"
EVENT_ROOT = "/run/baton/exchange/events"

COMMAND_SCHEMA = "baton.worker-exchange.command/1"
RECEIPT_SCHEMA = "baton.worker-exchange.receipt/1"
STATE_SCHEMA = "baton.worker-exchange.state/1"
TERMINAL_SCHEMA = "baton.worker-exchange.terminal/1"

COMMAND_MEMBERS = ("schema", "session", "attempt_id", "sequence_id",
                   "operations")
COMMAND_OPERATION_MEMBERS = ("operation", "operation_id")
RECEIPT_DOCUMENT = "receipt.json"
TERMINAL_DOCUMENT = "terminal.json"

# The worker's own closed ending vocabulary, the same three words the framed
# transport answers with. `lost` is accepted by the manager's reader and is
# deliberately NOT published by this program: a process that finds its own
# receipt with no terminal cannot know whether the provider it started is
# still running, and claiming loss would be exactly the observation it lacks.
# The manager derives loss by combining the durable receipt with its own exact
# runtime observation, which is evidence this side does not have.
EXCHANGE_ENDINGS = ("answered", "faulted", "lost")
EXCHANGE_STATES = ("dispatched", "answered", "faulted")

# The bytes any one exchange document may be. Bounded before it is read, for
# the reason the launch reader is: a reader with no bound is bounded by
# whoever writes the file.
MAX_EXCHANGE_BYTES = 65536                     # 64 KiB
MAX_EXCHANGE_VALUE = 4096

# How long this program waits between scans of the command namespace, and how
# many entries it will look at. The command is published AFTER the container
# starts -- that is what makes it a level-triggered manager act rather than a
# launch-time one -- so PID 1 waits for it here instead of on a pipe nobody
# may be holding.
SCAN_SECONDS = 2

# GROUP-READABLE, OWNER-WRITABLE-BY-NOBODY. The manager runs as another uid and
# reaches this namespace through the deployment's configured workspace group,
# which the container holds as a supplementary group; a document published at
# the process default 0600 would be one only this container could read. The
# document is finished when it is written and nothing writes it again, and the
# mode says so on disk.
EVENT_FILE = 0o440

# The manager writes these same four names, the same schema string and the same
# ceilings. THE TWO COPIES ARE NECESSARY -- this program cannot import the
# manager, which is the isolation rule the image is built on -- and a case in
# `test_oci` reads this literal and holds the manager's against it, because two
# copies of one contract agree until they don't.
MAX_LAUNCH_BYTES = 65536                       # 64 KiB
MAX_LAUNCH_VALUE = 4096

# WHAT THIS RUNTIME MAY BE ASKED. One tuple rather than a map keyed by posture:
# V12 launches one runtime, so there is no second set and nothing to key on.
# `consider` stays in the vocabulary below as an operation this runtime is NOT
# entitled to -- that refusal is the entitlement proof, and it needs `consider`
# to be a real operation rather than an unknown word.
OPERATIONS = ("describe", "work")

# The common envelope every request carries, and then EXACTLY the members each
# operation adds.
#
# Review [P1]: this used to be keyed by POSTURE, so an execution `describe`
# carrying `task` succeeded -- a member `describe` has no use for, accepted
# because some other operation of that posture does. Closure that is one level
# coarser than the contract is closure over the wrong thing.
COMMON_MEMBERS = ("protocol", "session", "operation_id", "operation")

REQUEST_MEMBERS = {
    "describe": COMMON_MEMBERS,
    "consider": COMMON_MEMBERS,
    # W14251, closed: A WORK REQUEST CARRIES NO TASK. The assignment is read
    # from `/input/input.json`, which is the manager-authored document at a
    # path that is a CONSTANT of the contract rather than an operand. An
    # inline task was the superseded shape and is not kept as an alias: two
    # live contracts for one operation is what a supersession exists to end.
    "work": COMMON_MEMBERS,
}

# What each answer is, exactly. Validated before it is framed, because an
# answer is what crosses the worker boundary and an agent is the least trusted
# thing inside this container -- a missing, unknown, extra or wrong-typed
# member must not become a frame the manager then has to interpret.
ANSWER_MEMBERS = {
    # W26291: `posture` and `environment` are GONE and `launch` replaced them.
    # `posture` reported an axis that no longer exists, and `environment`
    # reported the transport this Work retired; `launch` is the exact analogue
    # of what `environment` said -- the sorted member names of the document
    # this container was actually launched with.
    "describe": ("protocol", "operations", "launch"),
    "consider": ("contract_digest", "decision", "reason"),
    # `workspace` IS GONE ENTIRELY rather than renamed. A workspace path is a
    # HOST fact and the Worker Manager is artifact-neutral: what it needs from
    # a worker is which declared outputs were produced, and it learns where
    # they are from the declarations it wrote.
    "work": ("disposition", "outputs", "recap"),
}

# `ENVIRONMENT` IS GONE ENTIRELY rather than emptied (W26291). It named the
# four `BATON_WORKER_*` values a container was allowed to see, and the
# supersession retired that transport with no fallback -- so a set describing
# which of them are legal would be describing a channel this program no longer
# reads. What replaced it is `LAUNCH_MEMBERS` above: the closed set of one
# versioned document, checked as a closed set rather than as an allowlist over
# whatever the image happened to be started with.

# THE TWO FILESYSTEM ROLES, as constants of the contract. W14251 §7.0: a path
# a manifest could vary is a path a runtime can be pointed at wrongly, so the
# worker is told where to look by the contract rather than by a payload.
INPUT_ROOT = "/input"
OUTPUT_ROOT = "/output"
INPUT_MANIFEST = "input.json"
# W19784, approved 2026-08-26: THE SECOND MANAGER-AUTHORED INPUT DOCUMENT.
#
# The frozen `completionManifest` requires the exact full `assignment_ref` --
# Work reference, participant AND authority generation. `input.json` is minted
# before any claim exists and carries no generation, the `work` frame carries
# only the common worker-entry identity, and the execution environment
# deliberately carries no assignment value. So until this path existed there
# was NOWHERE inside the container to learn who this assignment is, and the
# only way to publish a valid envelope was to put `assignment_ref` into a
# document whose schema forbids it -- which is what this file used to do.
#
# The manager materializes this after the claim commits and before the input
# root is mounted. It is the ONE source of the identity below.
ASSIGNMENT_MANIFEST = "assignment.json"
OUTPUT_MANIFEST = "output.json"
COMPLETION_SCHEMA = "baton.worker-manifest/completion"

# THE FROZEN CONTRACT ITSELF, shipped beside this program as DATA.
#
# W19784 review [P0]: this worker read the two manager-authored documents by
# picking out the members it wanted. So a document with a false
# `manifest_digest`, or one carrying an extra top-level member -- a second
# identity alias, exactly what the ruling rejected -- passed straight through
# to agent dispatch. Shallow extraction is not validation.
#
# The fix could not be a hand-written member list. A list typed here is a
# SECOND COPY of the contract, and a second copy is a second thing to keep
# true; the campaign has been corrected for that before. So the schema travels
# with the image and the closed member sets are DERIVED from it at startup.
# `test_frozen` proves this copy is byte-identical to the other four, so there
# is one contract with five identical copies rather than five contracts.
#
# WHAT THIS DELIBERATELY IS NOT: a JSON Schema implementation. The image
# carries no validator library and must not grow one -- "no build toolchain, no
# package manager state" is a decision of the recipe, and a schema interpreter
# inside the worker would be a second validator to keep true anyway. What is
# proved here is the part a mis-composed or edited delivery breaks and that
# this program can prove ALONE: the document is the manager's closed document,
# it carries every member that definition requires, and its bytes are the ones
# its own digest describes. The manager proves the whole schema before it
# mounts the root (`workspaces.compose_input_root`, which calls the shipped
# `check_input_pair`), and `test_worker_image` pins that the two agree about
# what "closed" means.
CONTRACT_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "worker-control-1.0.schema.json")

# How much of the manager's input manifest this worker will read. It is a
# document from outside the container and its size is not this program's
# decision, so the bound has to be.
MAX_INPUT_BYTES = 4 * 1024 * 1024

# W6633 eleventh review [P1]: the declared-output shape and the path grammar
# are DERIVED from the shipped contract, exactly as the manifest member sets
# are. A list typed here would be a paraphrase, and W19784's third review is
# the standing lesson about paraphrased rules: they agree with the original
# until they don't, and they stop agreeing where it costs most.
#
# `DECLARATION_MEMBERS` used to be four names with `constraints` missing, so
# the ceilings a declaration states were not merely unenforced -- they were not
# even required to be present.
DECLARATION_DEFINITION = "outputDescriptor"
CONSTRAINT_DEFINITION = "outputConstraints"
RELATIVE_PATH = "relativePath"

# What an `assignment_ref` is, exactly. The worker COPIES this value into the
# envelope rather than rebuilding it, so what it checks is that the delivered
# document carries the whole thing and nothing else -- an envelope carrying a
# reconstructed or widened identity would be this worker's invention.
ASSIGNMENT_REF_MEMBERS = ("work_ref", "participant", "generation")

# `ASSIGNMENT_MEMBERS` and the two manifest-schema constants are GONE with the
# W19784 review's correction rather than kept beside it. They were this
# program's own list of what a delivered document must carry and be, and the
# closed set is now derived from the frozen contract -- so keeping them would
# be exactly the second copy the derivation exists to avoid, differing from the
# real definition the first time either moves.

# What an agent says about ONE declared output. The bytes are deliberately not
# in it: the worker MEASURES them, because the agent is the least trusted thing
# in this container and a content manifest is a claim about a tree.
AGENT_OUTPUT_MEMBERS = ("name", "status", "result_metadata")
OUTPUT_STATUSES = ("present", "missing-optional")

# What a worker may say it did. The frozen `completionManifest`'s own set, and
# a worker's disposition is a CLAIM about its work rather than a settlement --
# the manager records it and settles the attempt itself.
DISPOSITIONS = ("completed", "unable", "plan-rejected", "cancelled")


class WorkerFault(Exception):
    """A refusal this program can report as a frame rather than a crash."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message[:MAX_MESSAGE]


class Uncorrelated(Exception):
    """A failure this program cannot answer, because it has no identity to
    answer under.

    Deliberately NOT a `WorkerFault`. The approved ruling forbids inventing an
    uncorrelated response shape, so a frame whose identity envelope cannot be
    read produces no frame at all -- the Worker Manager already owns the
    launched session and settles that case from the engine rather than from a
    worker message nobody can match to a request.
    """


def read_frame(stream):
    """One length-prefixed frame, or None at a clean end of input.

    The length is read BYTE BY BYTE up to the digits a ceiling can have, so a
    peer that sends no newline cannot make this read forever -- the bound is on
    the header as well as on the body, because a header is caller input too.
    """
    header = b""
    while True:
        piece = stream.read(1)
        if not piece:
            if not header:
                return None
            raise Uncorrelated("the frame header ended early")
        if piece == b"\n":
            break
        header += piece
        if len(header) > 12:
            raise Uncorrelated("the frame header is not a length")
    if not header.isdigit():
        raise Uncorrelated("the frame header is not a length")
    length = int(header)
    if length > MAX_FRAME:
        raise Uncorrelated(f"a frame of {length} bytes is larger than the "
                           f"{MAX_FRAME} this channel carries")
    body = stream.read(length)
    if len(body) != length:
        raise Uncorrelated("the frame body ended early")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise Uncorrelated("a frame is not UTF-8 JSON") from None
    if type(document) is not dict:
        raise Uncorrelated("a frame is one JSON object")
    return document


def write_frame(stream, document):
    body = json.dumps(document, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_FRAME:
        # OUR OWN OUTPUT IS BOUNDED TOO, and the replacement KEEPS THE
        # IDENTITY. A bounds fault that dropped the correlation would be the
        # uncorrelated shape arriving by the back door.
        body = json.dumps(
            {"protocol": document.get("protocol"),
             "session": document.get("session"),
             "operation_id": document.get("operation_id"),
             "ok": False, "code": "bounds",
             "message": "the answer exceeded the frame ceiling"},
            sort_keys=True, separators=(",", ":")).encode("utf-8")
    stream.write(str(len(body)).encode("ascii") + b"\n" + body)
    stream.flush()


def _bounded(value, what):
    if type(value) is not str or not value or len(value) > MAX_IDENTITY:
        raise Uncorrelated(f"{what} is bounded non-empty text")
    return value


def identity_of(request):
    """The request's own identity envelope, or nothing this program can answer.

    Read BEFORE anything else and read the same way whatever the request turns
    out to be, because a response correlates to a REQUEST: the three members
    echoed back are the ones the sender put on the frame, so even a refusal is
    matchable to the frame that caused it.

    A request that does not carry a readable envelope is `Uncorrelated`. There
    is no fault frame for it, and that is the ruling rather than an omission.
    """
    if "protocol" not in request or "session" not in request \
            or "operation_id" not in request:
        raise Uncorrelated("a request carries protocol, session and "
                           "operation_id")
    return {"protocol": _bounded(request["protocol"], "a protocol"),
            "session": _bounded(request["session"], "a session"),
            "operation_id": _bounded(request["operation_id"],
                                     "an operation id")}


def success(identity, answer):
    return {**identity, "ok": True, "answer": answer}


def failure(identity, fault):
    return {**identity, "ok": False, "code": fault.code,
            "message": fault.message}


def read_launch(place=LAUNCH_DOCUMENT):
    """The manager's launch document, from a descriptor that proves what it is.

    W26291. THE FOUR PROPERTIES HERE ARE NOT DECORATION, and each is a way a
    container can be handed something other than the document it was promised:

      NO-FOLLOW, so a link at the fixed path is refused rather than resolved.
      A link is how a path this contract fixed becomes a path something else
      chose, which is the exact defect `_read_without_following` was added to
      the manager for.
      NON-BLOCKING, so a FIFO at that name cannot stop this program inside
      `open` before the descriptor check below can run. W26283's re-review is
      the standing lesson: a guard placed after an operation that may not
      return is a guard that never runs.
      REGULAR, PROVED ON THE DESCRIPTOR rather than on the path, because the
      descriptor is the one thing a racing replacement cannot have changed.
      BOUNDED, at one byte past the ceiling. The document is written by the
      manager, but this program is what a mis-composed delivery lands on, and a
      reader with no bound is bounded by whoever writes the file.

    AND READ-ONLY FOR THIS CONTAINER'S OWN VIEW. The manager mounts the file
    read-only; this proves it rather than trusting it, because a launch
    document this worker could rewrite is one it could change between reading
    it and being asked what it is. The proof is an attempted write-open, which
    is the only thing that actually answers the question -- the mode bits
    describe the host file and say nothing about how it was mounted.

    That proof depends on this process not being root, and it is not: the
    recipe fixes the image user at 65532 and the adapter's `--user` restriction
    names the same id, which is one decision written in two places with a case
    holding them together. Root would satisfy a write-open on a read-only MODE
    and still be refused by a read-only MOUNT, so the check is conservative in
    the direction that matters either way.

    Every failure here is `Uncorrelated`: without this document there is no
    session, nothing this program said could be matched to a request, and the
    ruling hands that case to the Worker Manager, which already owns the
    launched operation.
    """
    try:
        descriptor = os.open(place,
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        raise Uncorrelated(f"this container has no readable {place}; the "
                           f"launch document is how a worker is told what it "
                           f"is") from None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise Uncorrelated(f"{place} is not a regular file")
        raw = os.read(descriptor, MAX_LAUNCH_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_LAUNCH_BYTES:
        raise Uncorrelated(f"{place} is wider than {MAX_LAUNCH_BYTES} bytes")
    try:
        writable = os.open(place, os.O_WRONLY | os.O_NOFOLLOW)
    except OSError:
        pass
    else:
        os.close(writable)
        raise Uncorrelated(f"{place} is writable from inside this container; "
                           f"a launch document this worker could rewrite is "
                           f"not one the manager can hold it to")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise Uncorrelated(f"{place} is not UTF-8 JSON") from None
    if type(document) is not dict:
        raise Uncorrelated(f"{place} is one JSON object")
    return document


def session_of(document):
    """The identity the manager minted for THIS container session.

    Read BEFORE the rest of the document is validated, and deliberately: it is
    what every answer correlates to, so a document that carries a usable
    session and is wrong in some OTHER way can still be reported through the
    ordinary fault frame. Without it nothing this program says can be
    correlated to anything, so its absence is not a fault frame -- it is the
    case the ruling hands to the Worker Manager, which already owns the
    launched session and settles it as `worker_start_failed` from the
    container-engine result.
    """
    given = document.get("session")
    if type(given) is not str or not given or len(given) > MAX_IDENTITY:
        raise Uncorrelated("a worker session identity is bounded non-empty "
                           "text and arrives in the launch document")
    return given


def launched(document, place=LAUNCH_DOCUMENT):
    """The launch document held to its own closed contract.

    A CLOSED SET, not an allowlist. Every required member present, NOTHING
    else, the pinned schema, and every value bounded non-empty text -- an extra
    top-level member is how a second contract alias would arrive, and this
    campaign has rejected those explicitly before.

    THE SCHEMA IS CHECKED BY EQUALITY. A version this program does not know is
    not a document to read the parts it recognises out of: a manager and a
    worker from two generations disagreeing silently is precisely what the
    versioned document replaced.

    Answers the VALIDATED DOCUMENT, all four members of it.

    Re-review [P1]: this stripped `schema` and answered three, on the argument
    that the version is this program's business. That is a plausible proposal
    and it is not the recorded decision: the pinned finding says `describe`'s
    `launch` is "the sorted member names of the validated launch document", and
    that document has exactly four. Reporting three made the implementation
    disagree with the ruling it was implementing, so the ruling wins — an
    operator reading `describe` now sees which generation the container was
    launched under, which is a fact worth having anyway.
    """
    # W81857: THE SCHEMA DECIDES THE MEMBER SET, which is what makes the two
    # versions two contracts rather than one contract with an optional member.
    # A reader that accepted the union would accept a `/1` document carrying a
    # transport and a `/2` document carrying none, and each of those is a
    # manager and a worker disagreeing silently about which channel is
    # authoritative. An unknown schema is held to `/1`'s set so the refusal
    # names the version rather than the members.
    given = document.get("schema")
    members = (EXCHANGE_LAUNCH_MEMBERS if given == EXCHANGE_LAUNCH_SCHEMA
               else LAUNCH_MEMBERS)
    missing = sorted(name for name in members if name not in document)
    extra = sorted(name for name in document if name not in members)
    if missing or extra:
        raise WorkerFault(
            "launch",
            f"{place} is exactly {', '.join(members)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if given not in (LAUNCH_SCHEMA, EXCHANGE_LAUNCH_SCHEMA):
        raise WorkerFault(
            "launch",
            f"{place} says it is {document['schema']!r} and this worker reads "
            f"{LAUNCH_SCHEMA!r} and {EXCHANGE_LAUNCH_SCHEMA!r}; a launch "
            f"document from another generation is not one to read the "
            f"recognised parts out of")
    if given == EXCHANGE_LAUNCH_SCHEMA \
            and document.get("transport") != EXCHANGE_TRANSPORT:
        raise WorkerFault(
            "launch",
            f"{place} selects transport {document.get('transport')!r} and "
            f"this worker speaks {EXCHANGE_TRANSPORT!r}; a transport this "
            f"program cannot name is a channel nothing is listening to")
    for name in members:
        value = document[name]
        if type(value) is not str or not value:
            raise WorkerFault(
                "launch",
                f"{place} carries a {name} that is not bounded non-empty text")
        if len(value) > MAX_LAUNCH_VALUE:
            raise WorkerFault(
                "launch",
                f"{place} carries a {name} wider than {MAX_LAUNCH_VALUE} "
                f"characters")
    return {name: document[name] for name in members}


def canonical(value):
    """RFC 8785-equivalent bytes for the documents this worker writes.

    Member names here are ASCII, so sorting them lexically is the UTF-16 order
    the frozen contract requires; `ensure_ascii=False` and no whitespace are
    the other two halves. A digest two readers compute differently is not an
    identity, and the manager recomputes this one.
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def _frozen_contract():
    """The shipped `worker-control-1.0` document, read once per call.

    A schema this program cannot read is an operational fault rather than a
    reason to validate less: without it there is no closed set and no path
    grammar, and a worker that carried on would be back to the shallow
    extraction W19784's review replaced.
    """
    try:
        with open(CONTRACT_SCHEMA, "rb") as reading:
            return json.loads(reading.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise WorkerFault(
            "input",
            f"this image carries no readable {CONTRACT_SCHEMA}; without the "
            f"frozen contract there is no closed member set to hold a "
            f"manager document to")


def _plain(frozen, named):
    """The closed member set and required set of a NON-composed definition.

    `outputDescriptor` and `outputConstraints` are plain objects with
    `additionalProperties: false` rather than the `allOf` composition the
    manifests use, so they are read directly.
    """
    definition = frozen["$defs"][named]
    return set(definition.get("properties", ())), set(
        definition.get("required", ()))


def _resolved(frozen, rule):
    """One property rule with its `$ref` followed, if it has one."""
    while "$ref" in rule:
        rule = frozen["$defs"][rule["$ref"].rsplit("/", 1)[-1]]
    return rule


def _held(frozen, rule, value, what):
    """One value, against the frozen rule that describes it.

    W6633 twelfth review [P1]: deriving the member NAMES and then checking two
    integers was mistaken for validation. `name` and `type` are used for
    lookup and for authoring the completion envelope, `required` decides
    control flow, and a ceiling above the frozen maximum weakens the resource
    bound the schema pins -- so every one of them was consumed unvalidated.

    THIS IS NOT A JSON SCHEMA ENGINE AND MUST NOT BECOME ONE. It is the closed,
    bounded keyword set that `outputDescriptor` and `outputConstraints`
    actually use, and nothing else: an unrecognised keyword is a FAULT rather
    than a value this function passes over, because silently skipping one is
    how a derived check becomes a paraphrase again. If a later version of those
    two definitions uses a keyword this does not implement, the worker refuses
    and says so instead of validating less than it claims.
    """
    rule = _resolved(frozen, rule)
    if "oneOf" in rule:
        for branch in rule["oneOf"]:
            try:
                return _held(frozen, branch, value, what)
            except WorkerFault:
                continue
        raise WorkerFault("input", f"{what} matches none of its frozen forms")
    for keyword, expected in rule.items():
        if keyword in ("description", "title"):
            continue
        if keyword == "const":
            if value != expected:
                raise WorkerFault(
                    "input", f"{what} is {value!r} and the contract pins "
                             f"{expected!r}")
        elif keyword == "type":
            if not _is_type(value, expected):
                raise WorkerFault(
                    "input", f"{what} is not the frozen {expected}")
        elif keyword == "pattern":
            if not re.match(expected, value):
                raise WorkerFault(
                    "input", f"{what} does not match its frozen grammar")
        elif keyword == "minLength":
            if len(value) < expected:
                raise WorkerFault("input", f"{what} is shorter than {expected}")
        elif keyword == "maxLength":
            if len(value) > expected:
                raise WorkerFault("input", f"{what} is longer than {expected}")
        elif keyword == "minimum":
            if value < expected:
                raise WorkerFault("input", f"{what} is below {expected}")
        elif keyword == "maximum":
            if value > expected:
                raise WorkerFault("input", f"{what} is above {expected}")
        elif keyword == "uniqueItems":
            if expected and len(set(map(repr, value))) != len(value):
                raise WorkerFault("input", f"{what} repeats an entry")
        elif keyword == "items":
            for entry in value:
                _held(frozen, expected, entry, f"an entry of {what}")
        else:
            raise WorkerFault(
                "input",
                f"the frozen rule for {what} uses {keyword!r}, which this "
                f"worker does not implement; it refuses rather than validate "
                f"less than it says it does")
    return value


def _is_type(value, expected):
    """JSON's own types, and BOOLEANS ARE NOT INTEGERS.

    `isinstance(True, int)` is true in Python and false in JSON, and a
    `required` flag arriving where a ceiling belongs would otherwise pass a
    `minimum: 0` check as the number one.
    """
    if expected == "string":
        return type(value) is str
    if expected == "integer":
        return type(value) is int
    if expected == "boolean":
        return type(value) is bool
    if expected == "array":
        return type(value) is list
    if expected == "object":
        return type(value) is dict
    if expected == "null":
        return value is None
    raise WorkerFault(
        "input", f"the frozen rule names the type {expected!r}, which this "
                 f"worker does not implement")


def _definition(named):
    """The closed member set and the required set of one frozen definition.

    DERIVED FROM THE SHIPPED SCHEMA, never typed here. A definition in this
    contract is `allOf: [manifestHeader, {...}]` with
    `unevaluatedProperties: false`, so its closed set is the union of the two
    property maps and nothing else may appear beside them.

    A schema this program cannot read is an operational fault rather than a
    reason to validate less: without it there is no closed set, and a worker
    that carried on would be back to the shallow extraction this replaced.
    """
    frozen = _frozen_contract()
    definition = frozen["$defs"][named]
    closed, required, names = set(), set(), None
    for part in definition["allOf"]:
        if "$ref" in part:
            part = frozen["$defs"][part["$ref"].rsplit("/", 1)[-1]]
        properties = part.get("properties", {})
        closed |= set(properties)
        required |= set(part.get("required", ()))
        # WHICH DOCUMENT THIS IS, taken from the contract rather than from a
        # constant. Without it the closed set alone would accept the two
        # `/input/` documents SWAPPED: they share the header, and a delivery
        # that put the assignment manifest at `input.json` would fail later,
        # somewhere less clear, or not at all.
        if "schema" in properties and "const" in properties["schema"]:
            names = properties["schema"]["const"]
    return closed, required, names


def _closed_manifest(place, document, named):
    """One manager-authored document, held to its own frozen definition.

    THREE QUESTIONS, and each is a different way a delivery is wrong:

      EVERY REQUIRED MEMBER IS PRESENT -- a document short a member is one
      this worker would have to guess the rest of;
      NOTHING ELSE IS -- `unevaluatedProperties: false` is the contract's own
      word, and an extra top-level member is how a second identity alias would
      arrive. W19784's ruling rejected compatibility aliases explicitly, so
      one appearing in a delivered document is refused rather than ignored;
      THE BYTES ARE THE ONES THE DIGEST DESCRIBES -- recomputed over this
      document's own canonical form with the digest member removed, which is
      how the frozen contract defines it. Comparing the two documents' digest
      STRINGS with each other, as this used to, proves they were minted
      together and says nothing about whether either still is what it was.
    """
    closed, required, names = _definition(named)
    missing = sorted(required - set(document))
    extra = sorted(set(document) - closed)
    if missing or extra:
        raise WorkerFault(
            "input",
            f"{place} is not a closed {named}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if document["schema"] != names:
        raise WorkerFault(
            "input",
            f"{place} says it is {document['schema']} and this delivery reads "
            f"it as {names}; the two documents in this root are not "
            f"interchangeable")
    body = {name: value for name, value in document.items()
            if name != "manifest_digest"}
    if document["manifest_digest"] != digest(body):
        raise WorkerFault(
            "input",
            f"{place} does not identify itself; its manifest_digest describes "
            f"other bytes than the ones this worker read")
    return document


def _document(name, named):
    """One manager-authored document out of `/input/`, read once and bounded.

    W19784 review [P0]: this used to say the worker does not validate the
    manager's documents, and that was the defect. The manager DOES own the
    full boundary, and a worker that took a document on that basis had no way
    to tell a correctly delivered one from an edited or mis-composed one --
    which is precisely what a two-root delivery can get wrong.
    """
    place = os.path.join(INPUT_ROOT, name)
    try:
        with open(place, "rb") as reading:
            raw = reading.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise WorkerFault(
            "input",
            f"this assignment has no readable {place}; it is one of the two "
            f"documents a worker is told what it was asked for by")
    if len(raw) > MAX_INPUT_BYTES:
        raise WorkerFault(
            "input",
            f"{place} is wider than {MAX_INPUT_BYTES} bytes")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise WorkerFault("input", f"{place} is not a readable document")
    if type(document) is not dict:
        raise WorkerFault("input", f"{place} is one JSON object")
    return place, _closed_manifest(place, document, named)


def input_manifest():
    """The manager's `/input/input.json`: what this assignment declared.

    IT NO LONGER NAMES THE ASSIGNMENT, and it never legitimately could.
    W19784: this used to read `assignment_ref` from here, which made the whole
    worker depend on a member the frozen `inputManifest` schema forbids -- the
    document is minted before any claim exists. The identity now comes from
    `assignment_manifest()` and the schema and this reader finally agree.
    """
    place, document = _document(INPUT_MANIFEST, "inputManifest")
    declared = document["outputs"]
    if type(declared) is not list or not declared:
        raise WorkerFault(
            "input", f"{place} declares at least one output")
    return document, _declarations(place, declared)


def _declarations(place, declared):
    """Every declared output, proved BEFORE an agent is dispatched.

    W6633 eleventh review [P1], and the order is the whole content. This used
    to check that four member names were present and then hand the
    declarations straight to the agent, which wrote under
    `os.path.join(OUTPUT_ROOT, path)`. A declaration spelling `../tmp/escaped`
    therefore had the agent writing OUTSIDE the output root -- into the
    writable private ephemeral space, where the read-only input mount does not
    contain it -- and this worker then measured that escaped tree, published a
    completion envelope describing it, and answered success.

    Everything below runs before `agent.work`, so a declaration this worker
    cannot honour never becomes bytes anywhere.

    THE RULES ARE THE CONTRACT'S OWN, not a paraphrase of them: the closed
    descriptor and constraint member sets and the `relativePath` grammar are
    read out of the shipped schema.
    """
    frozen = _frozen_contract()
    descriptor = frozen["$defs"][DECLARATION_DEFINITION]
    constraint = frozen["$defs"][CONSTRAINT_DEFINITION]
    closed, required = _plain(frozen, DECLARATION_DEFINITION)
    limits, limited = _plain(frozen, CONSTRAINT_DEFINITION)
    root = os.path.realpath(OUTPUT_ROOT)
    seen, taken = set(), []
    for one in declared:
        if type(one) is not dict or set(one) != closed | required:
            raise WorkerFault(
                "input",
                f"a declared output in {place} is exactly "
                f"{', '.join(sorted(closed | required))}")
        constraints = one["constraints"]
        if type(constraints) is not dict \
                or set(constraints) != limits | limited:
            raise WorkerFault(
                "input",
                f"a declared output in {place} declares constraints that are "
                f"exactly {', '.join(sorted(limits | limited))}")
        # EVERY VALUE, against the frozen rule that describes it. The member
        # set alone said only that the right NAMES were present -- W6633's
        # twelfth review, and the same shape of mistake as proving two
        # documents agree with each other and calling it authorization.
        for member, rule in descriptor["properties"].items():
            if member == "constraints":
                continue
            _held(frozen, rule, one[member],
                  f"a declared output's {member}")
        for member, rule in constraint["properties"].items():
            _held(frozen, rule, constraints[member],
                  f"output {one['name']!r}'s {member}")
        _limits(one["name"], constraints)
        path = one["path"]
        # AND THEN CONTAINMENT, resolved. The grammar refuses the spellings;
        # this refuses a path that resolves out of the root anyway, which is
        # what a symlinked component would do.
        landing = os.path.realpath(os.path.join(root, path))
        if landing != root and not landing.startswith(root + os.sep):
            raise WorkerFault(
                "input",
                f"output {one['name']!r} resolves outside {OUTPUT_ROOT}")
        if path == OUTPUT_MANIFEST or path.startswith(OUTPUT_MANIFEST + "/"):
            raise WorkerFault(
                "input",
                f"output {one['name']!r} is declared at "
                f"{OUTPUT_MANIFEST!r}, which is this root's protocol manifest")
        if one["name"] in seen:
            raise WorkerFault(
                "input", f"output {one['name']!r} is declared twice")
        seen.add(one["name"])
        for before in taken:
            if landing == before[1] \
                    or landing.startswith(before[1] + os.sep) \
                    or before[1].startswith(landing + os.sep):
                # §7.2: the same bytes under two names are two artifacts with
                # two identities, and retention would decide twice about
                # material that is once.
                raise WorkerFault(
                    "input",
                    f"outputs {before[0]!r} and {one['name']!r} name the same "
                    f"tree or one inside the other")
        taken.append((one["name"], landing))
    return declared


def _limits(name, constraints):
    """What the frozen VALUE rules cannot say, plus the account of each member.

    `_held` above proves every member against the contract -- types, patterns,
    lengths, the `link_policy` const and the schema's own maxima on both
    ceilings. What is left here is the one decision the schema does not make.

    ENFORCED WHILE MEASURING: `max_bytes` and `max_entries`.

    `link_policy` is `const: "forbid"` in 1.0 and is enforced BY CONSTRUCTION
    rather than by comparison -- `measured` admits regular files only, so a
    link is refused whatever the policy said. A comparison against a one-value
    const could never fail, and writing one would be a guard no removal can
    measure.

    `allowed_media_types` is CARRIED AND NOT ENFORCED HERE, deliberately. A
    frozen `contentManifest` entry is a path, a byte count and a digest -- this
    worker has no media type for anything it measures. The value is enforced
    where a media type exists, on the collected artifact in the manager's
    `output.py`. Saying so is the difference between a split boundary and a
    dropped rule.

    `validator_digest` REFUSES the assignment when it is not null, and that is
    fail-closed rather than unimplemented. §7.2 makes `type` opaque and says
    the manager never branches on it; a worker that ran a type-specific
    validator would be branching on exactly that. Nothing else in 1.0 runs it
    either, so accepting a declaration that states one would be publishing a
    result while ignoring a constraint the manager wrote down.
    """
    if constraints["validator_digest"] is not None:
        raise WorkerFault(
            "input",
            f"output {name!r} declares a type-specific validator digest and "
            f"this worker runs none; a result published while ignoring a "
            f"stated constraint would be a result nobody checked")


def assignment_manifest():
    """The manager's `/input/assignment.json`: WHO this assignment is.

    W19784, approved 2026-08-26. This is the only source of the participant and
    authority generation inside the container, and the value it returns is
    copied into the completion envelope unchanged. So what it refuses is a
    document that could not be copied from: an `assignment_ref` that is not
    exactly the frozen three members is either short of the generation the
    envelope requires or carrying something this worker would be inventing.
    """
    place, document = _document(ASSIGNMENT_MANIFEST, "assignmentManifest")
    assignment = document["assignment_ref"]
    if type(assignment) is not dict \
            or sorted(assignment) != sorted(ASSIGNMENT_REF_MEMBERS):
        raise WorkerFault(
            "input",
            f"{place} names an assignment by exactly "
            f"{', '.join(ASSIGNMENT_REF_MEMBERS)}; the completion envelope "
            f"carries this value unchanged")
    return document


def one_delivery(given, delivered):
    """The two `/input/` documents, held against each other before dispatch.

    §12 rule 16. Each document is separately readable and separately
    plausible, and that says nothing about whether they are ABOUT ONE THING. A
    container composed from one delivery's input and another's assignment
    would run the agent against the wrong material and then publish an
    envelope naming the wrong Work -- and every single-document check above
    would have passed.

    The manager performs the same comparison before it mounts the root. This is
    not redundancy: the worker is the party that COPIES the identity into a
    durable document, and a party that copies an identity proves the identity
    belongs to the material it is describing. It also runs before the agent, so
    a mis-composed container writes nothing at all.

    THE GENERATION IS NOT COMPARED and cannot be: `input.json` has none. That
    asymmetry is the whole reason this Work exists, and the assignment side is
    the sole source.
    """
    assignment = delivered["assignment_ref"]
    if assignment["work_ref"] != given.get("work_ref"):
        raise WorkerFault(
            "input",
            f"{INPUT_ROOT}/{ASSIGNMENT_MANIFEST} names another Work than "
            f"{INPUT_ROOT}/{INPUT_MANIFEST} declares")
    if delivered["input_manifest_digest"] != given.get("manifest_digest"):
        raise WorkerFault(
            "input",
            f"{INPUT_ROOT}/{ASSIGNMENT_MANIFEST} was minted against another "
            f"input manifest than the one beside it; the pair in one root is "
            f"one pair or it is two halves of two deliveries")
    for name in ("policy_digest", "runtime_profile_digest"):
        if delivered[name] != given.get(name):
            raise WorkerFault(
                "input",
                f"the two documents in {INPUT_ROOT}/ declare different "
                f"{name} values; one delivery carries one identity")
    return assignment


def measured(place, constraints):
    """One declared output tree, as the frozen `contentManifest`.

    THE WORKER MEASURES AND THE AGENT DOES NOT. A content manifest is a claim
    about bytes, and the agent is the least trusted thing inside this
    container -- so it says WHICH outputs it produced and this says what is in
    them. Sorted bytewise, aggregates computed rather than declared, and the
    tree digest over the canonical ordered entry array, which is §3.3's own
    rule and what makes two manifests over one tree the same manifest.
    """
    # W6633 eleventh review [P1]: THE CEILINGS ARE ENFORCED WHILE MEASURING,
    # not afterwards. A declaration's limits are the manager's statement about
    # what this assignment may produce, and a worker that measured a whole
    # oversized tree and then compared totals would already have read it all
    # into this process -- so the refusal arrives as the bound is crossed,
    # before the next file is accumulated and long before anything is
    # published.
    ceiling_entries = constraints["max_entries"]
    ceiling_bytes = constraints["max_bytes"]
    entries, total = [], 0
    for base, directories, files in os.walk(place):
        # EVERY ENTRY THE TRAVERSAL MEETS, not only the ones in `files`.
        #
        # W6633 twelfth review [P1]: this walked `files` alone, and
        # `os.walk(..., followlinks=False)` puts a symlink TO A DIRECTORY in
        # `directories` -- where it was then skipped in silence. So a declared
        # tree containing `linked-directory -> /output` measured as empty, the
        # worker answered success, and the completion manifest claimed a tree
        # with nothing in it while the link was still there.
        #
        # I had written that `link_policy: forbid` is enforced BY
        # CONSTRUCTION. That claim is only true when every entry the traversal
        # encounters takes part in the construction, and one whole list of
        # them did not. The claim is now true.
        for one in directories:
            full = os.path.join(base, one)
            if os.path.islink(full):
                raise WorkerFault(
                    "output",
                    f"{full} is a link; a declared output carries regular "
                    f"files in 1.0 and `link_policy` is `forbid`")
        for one in files:
            full = os.path.join(base, one)
            if not os.path.isfile(full) or os.path.islink(full):
                # REGULAR FILES ONLY, like the manager's own measurement. A
                # link is not material this worker can describe by content;
                # a socket, a device or a fifo is not either.
                raise WorkerFault(
                    "output",
                    f"{full} is not a regular file; a declared output carries "
                    f"regular files in 1.0")
            if len(entries) + 1 > ceiling_entries:
                raise WorkerFault(
                    "output",
                    f"this output declares at most {ceiling_entries} "
                    f"entries and carries more")
            size = os.path.getsize(full)
            if total + size > ceiling_bytes:
                raise WorkerFault(
                    "output",
                    f"this output declares at most {ceiling_bytes} bytes and "
                    f"carries more")
            with open(full, "rb") as reading:
                content = reading.read()
            total += len(content)
            entries.append({
                "path": os.path.relpath(full, place).replace(os.sep, "/"),
                "bytes": len(content),
                "content_digest": "sha256:" + hashlib.sha256(
                    content).hexdigest()})
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    return {"entries": entries, "entry_count": len(entries),
            "total_bytes": sum(one["bytes"] for one in entries),
            "tree_digest": digest(entries)}


def answered(declared, reported):
    """The agent's per-output answers, held against the declarations.

    The agent names outputs and says whether it produced them; everything else
    in the published answer comes from the DECLARATION or from this worker's
    own measurement. So an agent cannot rename an output, move it, invent one,
    or describe bytes it did not write.
    """
    if type(reported) is not list:
        raise WorkerFault("answer", "a work answer's outputs are a list")
    said = {}
    for one in reported:
        if type(one) is not dict \
                or sorted(one) != sorted(AGENT_OUTPUT_MEMBERS):
            raise WorkerFault(
                "answer",
                f"an output answer is exactly "
                f"{', '.join(AGENT_OUTPUT_MEMBERS)}")
        if one["status"] not in OUTPUT_STATUSES:
            raise WorkerFault(
                "answer",
                f"an output status is one of {', '.join(OUTPUT_STATUSES)}")
        if type(one["result_metadata"]) is not dict:
            raise WorkerFault("answer",
                              "an output's result metadata is one object")
        if one["name"] in said:
            raise WorkerFault(
                "answer", f"output {one['name']!r} is answered twice")
        said[one["name"]] = one
    names = sorted(one["name"] for one in declared)
    if sorted(said) != names:
        raise WorkerFault(
            "answer",
            f"a work answer answers exactly {', '.join(names)}")
    published = []
    for declaration in declared:
        one = said[declaration["name"]]
        place = os.path.join(OUTPUT_ROOT, declaration["path"])
        status = one["status"]
        if status == "present" and not os.path.isdir(place):
            raise WorkerFault(
                "answer",
                f"output {declaration['name']!r} is answered present and "
                f"{place} is not there")
        if declaration["required"] and status != "present":
            # WHETHER AN OUTPUT WAS REQUIRED IS THE MANAGER'S DECLARATION. An
            # agent that could answer a required output away would be settling
            # its own attempt, and the manager refuses this too -- refusing it
            # here as well is the worker declining to publish a document it
            # knows is wrong.
            raise WorkerFault(
                "answer",
                f"output {declaration['name']!r} is required and is answered "
                f"{status}")
        published.append({
            "name": declaration["name"], "type": declaration["type"],
            "path": declaration["path"], "status": status,
            "content_manifest": (measured(place, declaration["constraints"])
                                 if status == "present" else None),
            "result_metadata": one["result_metadata"]})
    return published


def publish_completion(assignment, disposition, outputs):
    """`/output/output.json`, published LAST and ATOMICALLY.

    LAST, because its presence under its final name is the completion signal:
    it exists only if everything it describes was already written, so no
    separate signal is needed and none is invented.

    ATOMICALLY, because writing bytes into the final name is not publication.
    A process stopped inside that write leaves the name existing and empty,
    and a manager cannot tell that from a settled answer -- so the bytes
    become visible under the final name only once they are complete.
    """
    body = {"version": {"major": 1, "minor": 0},
            "manifest_id": f"completion-{disposition}",
            "created_at": _instant(),
            "extensions": {},
            "schema": COMPLETION_SCHEMA,
            "assignment_ref": assignment,
            "disposition": disposition,
            "outputs": outputs}
    body["manifest_digest"] = digest(body)
    place = os.path.join(OUTPUT_ROOT, OUTPUT_MANIFEST)
    staged = place + ".publishing"
    with open(staged, "wb") as writing:
        writing.write(canonical(body))
        writing.flush()
        os.fsync(writing.fileno())
    os.replace(staged, place)
    return body


def _instant():
    """This worker's own clock, in the frozen grammar.

    The manager does not take its ordering from this -- it has its own clock
    and its own observation -- so what this needs to be is well formed rather
    than authoritative.
    """
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + ".000Z"


def check_answer(operation, answer):
    """The agent's answer, against the closed set the contract pins.

    THE LAST BOUNDARY BEFORE THE FRAME. The agent is the least trusted thing
    inside this container, and an answer is what crosses out of it -- so a
    missing, unknown, extra or wrong-typed member is refused here rather than
    handed to a manager that would then have to decide what it meant.
    """
    if type(answer) is not dict:
        raise WorkerFault("answer",
                          f"a {operation} answer is one JSON object")
    wanted = ANSWER_MEMBERS[operation]
    missing = sorted(name for name in wanted if name not in answer)
    extra = sorted(name for name in answer if name not in wanted)
    if missing or extra:
        raise WorkerFault(
            "answer",
            f"a {operation} answer is exactly {', '.join(wanted)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    for name, value in answer.items():
        # ONE RULE, AND NO EXEMPTION. W6633 eleventh review [P1]: `outputs`
        # used to be skipped here, on the reasoning that `answered` had
        # already built it -- and that reasoning was about the wrong document.
        # `answered` builds the records the COMPLETION ENVELOPE carries, which
        # is where they belong; the framed answer is a different surface and
        # is pinned to the bounded names of the outputs produced. Skipping the
        # member meant the whole record set crossed the channel, and the rule
        # that was supposed to stop a shape the manager would have to
        # interpret was not applied to the one member most able to carry one.
        #
        # `MAX_FRAME` bounds the entries too. A list of unbounded strings is
        # unbounded text with extra steps.
        if type(value) is str and len(value) <= MAX_FRAME:
            continue
        if type(value) is list \
                and all(type(entry) is str and len(entry) <= MAX_FRAME
                        for entry in value):
            continue
        raise WorkerFault(
            "answer",
            f"a {operation} answer's {name} is bounded text or a list of it")
    return answer


def bind(identity, expected):
    """THE COMMON CONTRACT, and it holds on every path this program has.

    The order is the content. A frame that is not for this session is not a
    request to this container at all, so it is refused before any question
    about entitlement: answering "you are not asked to work" would be
    answering a question somebody else was asked.

    Re-review [P1]: this used to live inside `handle`, which the latched
    bootstrap path never reaches -- so a container with a pending launch fault
    echoed an arbitrary peer's session and disclosed its own failure to
    whoever asked. Startup correlation supplies an operation identity; it does
    not suspend the binding. Lifted out so the one caller that decides what to
    answer establishes the correlation FIRST, whatever it goes on to say.
    """
    if identity["protocol"] != PROTOCOL:
        raise WorkerFault(
            "protocol",
            f"this channel speaks {PROTOCOL}; the frame says "
            f"{identity['protocol']!r}")
    if identity["session"] != expected:
        raise WorkerFault(
            "session",
            "this frame names another container session; a worker answers "
            "only the session the manager minted for it, and no message turns "
            "one container into another")


def handle(request, identity, seen, agent, spent):
    """One operation, with ENTITLEMENT CHECKED EVERY TIME.

    The protocol and the session are `bind`'s and are established before this
    is reached; what remains here is entitlement, shape and the replay fence.

    W26291: the entitlement was a POSTURE check and the posture axis is gone.
    What it protected did not go with it -- this runtime answers `describe` and
    `work`, and an operation outside that set is refused on every message
    rather than once at start, because a check that ran once at start is a
    check a later message can walk past.
    """
    operation = request.get("operation")
    if type(operation) is not str or operation not in REQUEST_MEMBERS:
        raise WorkerFault("protocol", "a request names one known operation")
    if operation not in OPERATIONS:
        # NOT "unknown operation". The distinction is the whole point of
        # keeping `consider` in the vocabulary: it is a REAL operation that
        # this runtime is not entitled to, and saying so is what makes the
        # negative case mean something.
        raise WorkerFault(
            "entitlement",
            f"this worker is not asked to {operation!r}; it answers "
            f"{', '.join(OPERATIONS)}")
    wanted = REQUEST_MEMBERS[operation]
    missing = sorted(name for name in wanted if name not in request)
    extra = sorted(name for name in request if name not in wanted)
    if missing or extra:
        raise WorkerFault(
            "protocol",
            f"a {operation} request is exactly {', '.join(wanted)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    # NO PER-OPERATION MEMBER CHECK REMAINS. `work` used to name an inline
    # task and this typed it; W14251 closed replaced that with
    # `/input/input.json`, so the closed member set above is the whole of what
    # a request carries and there is nothing left here to type.
    # ONE USE PER SESSION, CONSUMED BEFORE DISPATCH. An id that reached the
    # agent is spent whatever the outcome, because this program cannot know
    # whether the first attempt's side effects happened -- and "it failed, so
    # you may send it again" is exactly the reasoning a replay fence exists to
    # refuse.
    if identity["operation_id"] in spent:
        raise WorkerFault(
            "replay",
            f"operation {identity['operation_id']!r} was already used in this "
            f"session; an operation id is consumed once")
    spent.add(identity["operation_id"])
    if operation == "describe":
        return check_answer(operation,
                            {"protocol": PROTOCOL,
                             "operations": list(OPERATIONS),
                             "launch": sorted(seen)})
    if operation == "consider":
        return check_answer(operation, agent.consider(seen, request))
    # W14251, closed: THE WORK OF AN EXECUTION WORKER, IN ORDER.
    #
    #   read `/input/input.json`  -- the manager's declaration of what was
    #                                asked for, at a path this contract fixes;
    #   read `/input/assignment.json`
    #                             -- WHO this assignment is, at the other fixed
    #                                path (W19784);
    #   hold the pair             -- one Work, one input digest, one policy and
    #                                profile: two documents that are not one
    #                                delivery are refused BEFORE the agent runs
    #                                and therefore before anything is written;
    #   run the agent             -- which writes its material under the
    #                                declared output paths and says which of
    #                                them it produced;
    #   hold its answer           -- against those declarations, and measure
    #                                the bytes rather than believe them;
    #   publish `output.json`     -- LAST and atomically, which is what makes
    #                                its presence the completion signal.
    #
    # The manager then validates that envelope, holds it against the same
    # input manifest and its own assignment, and freezes. Nothing here decides
    # settlement: a worker reports what it produced and the manager settles.
    given, declared = input_manifest()
    delivered = assignment_manifest()
    assignment = one_delivery(given, delivered)
    reported = agent.work(seen, declared)
    if type(reported) is not dict:
        raise WorkerFault("answer", "a work answer is one JSON object")
    published = answered(declared, reported.get("outputs"))
    disposition = reported.get("disposition")
    if disposition not in DISPOSITIONS:
        raise WorkerFault(
            "answer",
            f"a work disposition is one of {', '.join(DISPOSITIONS)}")
    publish_completion(assignment, disposition, published)
    # TWO SURFACES, AND THEY CARRY DIFFERENT THINGS. The completion envelope
    # above is the durable document and holds the whole record for each output
    # -- name, type, path, status, the measured content manifest and the
    # opaque metadata. The framed answer is the correlated reply on the
    # worker-entry channel and carries the bounded NAMES of what was produced.
    #
    # W6633 eleventh review [P1]: it used to carry the records themselves, so
    # the manager received one document twice by two routes, one of them the
    # transport it is supposed to be able to read without interpreting.
    return check_answer(operation, {
        "disposition": disposition,
        "outputs": [one["name"] for one in published
                    if one["status"] == "present"],
        "recap": reported.get("recap")})


# -- W81857: the durable file exchange ---------------------------------------
#
# THE SAME OPERATION HANDLER, THE OTHER TRANSPORT. Everything below composes
# requests and publishes documents; not one rule about what an operation IS
# lives here. `handle` still validates the closed request member set, checks
# entitlement on every message, consumes the operation id once, reads
# `/input/input.json` and `/input/assignment.json`, runs the agent, measures
# the declared outputs and publishes `/output/output.json` atomically. A second
# serve loop that reimplemented any of that would be a second worker-entry
# protocol nobody reviewed, which is the thing this file exists not to be.


def _publish(root, name, document):
    """One event document, published ATOMICALLY under a fixed name.

    FIVE STEPS AND ALL FIVE MATTER: exclusive no-follow staging so nothing
    already at the staging name is written through; the complete write; `fsync`
    on the file so the bytes survive the machine; `rename` WITHIN the directory
    so the final name never exists half written; and `fsync` on the directory
    so the rename itself survives. A manager scanning mid-publication sees the
    staging name, which is not one of the four names its contract describes and
    is therefore not protocol state.

    THE MODE IS ESTABLISHED, NOT REQUESTED, and it is the same correction the
    launch document's writer records. A creation mode is filtered by the
    umask, and the manager reaches this namespace as another uid through the
    deployment's configured group -- so a document left at the process default
    is one only this container can read, which is a lost turn on somebody
    else's machine and nothing in the mount table would show why.

    AND THE STAGING NAME IS UNIQUE PER PUBLICATION. W81857 review
    2026-09-04T03-43-45Z [P1]: a fixed `.publishing` name plus `O_EXCL` means a
    process that died between creation and rename left a file that made every
    later incarnation of this program fail `FileExistsError` forever -- a
    permanent wedge created by a crash, inside the transport whose entire
    purpose is surviving one. A unique name cannot collide with a stale one,
    and a stale one is invisible: the manager reads the four fixed names this
    contract describes and reports anything else as a foreign entry rather than
    reading it.

    THE FINAL NAME IS REPLACED RATHER THAN LINKED, and that is the difference
    from the manager's own publisher. A state event is published TWICE for one
    operation -- `dispatched` before the provider and then its outcome -- so
    the second publication must land on the first. The receipt and the terminal
    are each written once, behind the fence that reads them first.
    """
    payload = canonical(document)
    if len(payload) > MAX_EXCHANGE_BYTES:
        raise WorkerFault("answer",
                          f"a {name} of {len(payload)} bytes is wider than "
                          f"the {MAX_EXCHANGE_BYTES} this exchange carries")
    place = os.path.join(root, name)
    staged = os.path.join(root, f".{name}.{os.getpid()}."
                                f"{os.urandom(8).hex()}.publishing")
    handle = os.open(staged,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o000)
    # ONE CLEANUP BOUNDARY OVER EVERYTHING AFTER THE CREATE, the same shape the
    # manager's publisher was corrected to. W81857 review
    # 2026-09-04T04-17-15Z [P2] found the leak on the manager side and asked
    # for the same audit here: several small unwinds that each cover one step
    # are several places for a step to be added outside one, and a transient
    # write or sync failure leaving a staging file behind is a leak whether or
    # not unique names keep it from being a wedge.
    #
    # A SUCCESSFUL `replace` CONSUMES THE STAGED NAME, so the unlink below is
    # an ordinary no-op on the happy path rather than a second act with an
    # effect.
    try:
        try:
            written = 0
            while written < len(payload):
                step = os.write(handle, payload[written:])
                if type(step) is not int or step <= 0:
                    raise WorkerFault("answer",
                                      f"publishing {name} made no progress "
                                      f"after {written} of {len(payload)} "
                                      f"bytes")
                written += step
            os.fchmod(handle, EVENT_FILE)
            os.fsync(handle)
        finally:
            os.close(handle)
        os.replace(staged, place)
        opened = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(opened)
        finally:
            os.close(opened)
        return place
    finally:
        try:
            os.unlink(staged)
        except OSError:
            pass


def _exchange_read(root, name):
    """One named regular file's whole bytes, or absence. NO-FOLLOW, BOUNDED.

    The four properties are `read_launch`'s and each one is a way this program
    can be handed something other than a document: NO-FOLLOW so a link at a
    fixed name is refused rather than resolved, NON-BLOCKING so a FIFO cannot
    stop this program inside `open`, REGULAR proved on the DESCRIPTOR rather
    than on the path, and BOUNDED at one byte past the ceiling.
    """
    try:
        descriptor = os.open(os.path.join(root, name),
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError:
        raise WorkerFault("exchange",
                          f"{name} could not be opened as an ordinary file; a "
                          f"link or a device at a name this contract fixes is "
                          f"not a document") from None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise WorkerFault("exchange", f"{name} is not a regular file")
        raw = os.read(descriptor, MAX_EXCHANGE_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_EXCHANGE_BYTES:
        raise WorkerFault("exchange",
                          f"{name} is wider than {MAX_EXCHANGE_BYTES} bytes")
    return raw


def _commanded(root, session):
    """The one manager-authored command in this namespace, or absence.

    EXACTLY ONE, AND ITS NAME IS ITS OWN SEQUENCE IDENTITY. The manager derives
    the filename from the sequence rather than being given a path, so a
    namespace holding two commands is one this program did not receive from a
    manager it recognises -- choosing between them by directory order would be
    inventing which turn was asked for.

    STAGING NAMES ARE INVISIBLE, which is the other half of atomic
    publication: a scan that raced a rename sees a dot-prefixed name and must
    read nothing, because the document under it is not finished.

    AND THE NAMESPACE IS PROVED READ-ONLY. A command this worker could rewrite
    is one the manager cannot hold it to -- it could change what it was asked
    to do between reading the command and publishing the receipt that fences
    it. The proof is an attempted write-open, which is the only thing that
    answers the question: the mode bits describe the host file and say nothing
    about how it was mounted.
    """
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return None
    named = [one for one in entries
             if one.endswith(".json") and not one.startswith(".")]
    if not named:
        return None
    if len(named) > 1:
        raise WorkerFault("exchange",
                          f"this exchange carries {len(named)} commands and "
                          f"one attempt has one sequence")
    name = named[0]
    raw = _exchange_read(root, name)
    if raw is None:
        return None
    try:
        writable = os.open(os.path.join(root, name),
                           os.O_WRONLY | os.O_NOFOLLOW)
    except OSError:
        pass
    else:
        os.close(writable)
        raise WorkerFault("exchange",
                          f"{name} is writable from inside this container; a "
                          f"command this worker could rewrite is not one the "
                          f"manager can hold it to")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise WorkerFault("exchange", f"{name} is not UTF-8 JSON") from None
    _closed(document, COMMAND_MEMBERS, name)
    if document["schema"] != COMMAND_SCHEMA:
        raise WorkerFault("exchange",
                          f"{name} says it is {document['schema']!r} and this "
                          f"worker reads {COMMAND_SCHEMA!r}")
    if document["session"] != session:
        # NOT THIS CONTAINER'S COMMAND. A frame that is not for this session is
        # not a request to this container at all, and the file transport
        # answers that question exactly as `bind` does for the framed one.
        raise WorkerFault("session",
                          f"{name} names another container session; a worker "
                          f"answers only the session the manager minted for "
                          f"it")
    if name != document["sequence_id"] + ".json":
        raise WorkerFault("exchange",
                          f"{name} carries sequence "
                          f"{document['sequence_id']!r}; the published name "
                          f"is derived from the sequence identity")
    ordered = document["operations"]
    if type(ordered) is not list or not ordered \
            or len(ordered) > len(OPERATIONS):
        raise WorkerFault("exchange",
                          f"{name} carries a bounded ordered operation list")
    for one in ordered:
        _closed(one, COMMAND_OPERATION_MEMBERS, name)
        if one["operation"] not in OPERATIONS:
            raise WorkerFault(
                "entitlement",
                f"this worker is not asked to {one['operation']!r}; it "
                f"answers {', '.join(OPERATIONS)}")
        _exchange_value(one["operation_id"], "an operation id", name)
    _exchange_value(document["attempt_id"], "an attempt id", name)
    return document, digest_of(raw)


def _closed(document, members, name):
    if type(document) is not dict:
        raise WorkerFault("exchange", f"{name} is JSON objects")
    missing = sorted(one for one in members if one not in document)
    extra = sorted(one for one in document if one not in members)
    if missing or extra:
        raise WorkerFault(
            "exchange",
            f"{name} is exactly {', '.join(members)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return document


def _exchange_value(value, what, name):
    if type(value) is not str or not value \
            or len(value) > MAX_EXCHANGE_VALUE:
        raise WorkerFault("exchange",
                          f"{name} carries {what} that is not bounded "
                          f"non-empty text")
    return value


def digest_of(payload):
    """The digest every event document is correlated by.

    Over the EXACT BYTES the manager published rather than over a
    recanonicalization of them: the manager holds its own bytes and this holds
    the file, so two readers that canonicalize differently cannot disagree
    about what was commanded.
    """
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _bound(command, digested, **members):
    """Every event document, bound to the exact command it answers.

    THE DIGEST IS THE BINDING and the identities are the readable half of it.
    A manager that found a document naming another sequence would have no way
    to tell a stale delivery from a foreign one, so all four travel on every
    document this program publishes.
    """
    return {"session": command["session"],
            "attempt_id": command["attempt_id"],
            "sequence_id": command["sequence_id"],
            "command_digest": digested, **members}


def _published_manifest_digest():
    """The completion envelope's own digest, read back from what was published.

    READ BACK RATHER THAN CARRIED. `publish_completion` is the atomic writer
    and its output is the durable record; naming its digest here from a value
    passed alongside would be a second account of a document that already
    exists. The manager validates that same file independently before it
    freezes anything, so this is a correlation label rather than evidence.
    """
    try:
        raw = _exchange_read(OUTPUT_ROOT, OUTPUT_MANIFEST)
    except WorkerFault:
        return None
    if raw is None:
        return None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    found = document.get("manifest_digest") if type(document) is dict else None
    # THE SHAPE, NOT THE LENGTH. The manager holds this member to a canonical
    # sha256 grammar, so a value that would be refused there is not one this
    # program publishes -- a worker that wrote something the manager cannot
    # read would be moving its own mistake into a container the manager can no
    # longer ask about.
    if type(found) is not str or not re.match(r"\Asha256:[0-9a-f]{64}\Z",
                                              found):
        return None
    return found


def serve_exchange(agent, seen, expected, command_root, event_root,
                   sleep=None):
    """The durable transport. NOTHING HERE DEPENDS ON A LIVE MANAGER.

    THE ORDER IS THE WHOLE CONTRACT:

      1. wait for the one command, which the manager publishes AFTER this
         container is up -- so this program is running before there is
         anything to do, which is exactly the state the defect this Work
         corrects reported as `running`;
      2. publish the RECEIPT before the provider is dispatched. That receipt is
         the durable replay fence: rescanning this namespace, a manager
         restart during the turn, and a re-entry of this program after a crash
         all find it and none of them starts a second provider turn;
      3. publish one state event per operation actually reached, so an operator
         can tell "the turn is running" from "the turn is over" without
         interpreting silence; and
      4. publish ONE terminal document carrying only bounded protocol facts.

    A RECEIPT WITH NO TERMINAL IS NOT AN ENDING THIS PROGRAM MAY WRITE. Re-
    entering here after a receipt means a previous incarnation reached the
    provider and this one cannot know whether that provider is still running,
    already finished, or gone. Publishing `lost` would be claiming an
    observation this side does not have; the manager combines the durable
    receipt with its own exact runtime observation and decides.

    WHAT NEVER CROSSES: the provider's recap, its stdout or stderr, the prompt,
    a source excerpt, tool input or output, or any diagnostic prose. The
    terminal document carries the completed operation names, a bounded fault
    CODE from this program's own closed set, the worker disposition when there
    is one, and the digest of the completion envelope already published under
    the existing `/output` contract.
    """
    waiting = time.sleep if sleep is None else sleep
    try:
        found = _commanded(command_root, expected)
        while found is None:
            waiting(SCAN_SECONDS)
            found = _commanded(command_root, expected)
        command, digested = found
    except WorkerFault:
        # NOTHING CORRELATES A REFUSAL ABOUT THE COMMAND ITSELF. Without a
        # command there is no sequence, no digest and no session this program
        # may publish under -- writing an uncorrelated document into a
        # namespace the manager reads by identity would be inventing state
        # rather than reporting one. The manager already owns the launched
        # runtime and reads this exchange as `waiting`.
        return 2
    if _exchange_read(event_root, RECEIPT_DOCUMENT) is not None:
        # THE FENCE, AND IT IS READ BEFORE ANYTHING IS DISPATCHED. A receipt
        # under this command means a provider turn was already begun for it.
        # Whether it finished is not this program's question and not one it can
        # answer, so it reports the sequence as already accepted and stops.
        return 0 if _exchange_read(event_root,
                                   TERMINAL_DOCUMENT) is not None else 4
    _publish(event_root, RECEIPT_DOCUMENT,
             _bound(command, digested, schema=RECEIPT_SCHEMA,
                    accepted_at=_instant()))
    spent = set()
    answered = []
    disposition = None
    # BOUND BEFORE THE LOOP, because a command carries a BOUNDED ordered list
    # rather than necessarily the whole pair, and the terminal below needs
    # this value on every path. A sequence that never reached `work` has no
    # completion envelope to name and therefore no answer to publish.
    manifest = None
    for one in command["operations"]:
        operation = one["operation"]
        identity = {"protocol": PROTOCOL, "session": command["session"],
                    "operation_id": one["operation_id"]}
        request = {**identity, "operation": operation}
        _publish(event_root, f"state-{operation}.json",
                 _bound(command, digested, schema=STATE_SCHEMA,
                        operation=operation,
                        operation_id=one["operation_id"],
                        state="dispatched"))
        try:
            answer = handle(request, identity, seen, agent, spent)
        except WorkerFault as fault:
            return _faulted(event_root, command, digested, operation,
                            one["operation_id"], answered, fault.code)
        except Exception:                                  # noqa: BLE001
            # THE AGENT'S FAILURE IS NOT THIS PROGRAM'S CRASH, and it is not
            # this program's diagnostic either. The framed transport answers a
            # bounded description with no traceback; here even the exception's
            # type name stays out of the durable document, because a durable
            # file is a different surface from a frame the manager reads once.
            return _faulted(event_root, command, digested, operation,
                            one["operation_id"], answered, "agent")
        # AN ANSWER NAMES THE ENVELOPE IT PUBLISHED, or it is not an answer.
        # W81857 review [P1] made this member load-bearing: the manager
        # compares it with the digest its own independent validation of
        # `/output/output.json` produced, and refuses the whole success ending
        # on a mismatch. So a `work` that ran and cannot read back its own
        # completion envelope is reported as a FAULT rather than as an answer
        # with a null digest -- publishing the latter would be asking the
        # manager to accept a correlation this program could not make.
        #
        # IT IS CHECKED BEFORE THE `answered` STATE IS PUBLISHED, and re-review
        # 2026-09-04T04-17-15Z [P1] is why the order matters now. The manager
        # holds a terminal against its own state evidence: an operation the
        # terminal does not answer must not be sitting there answered, and a
        # faulted ending must name the operation it stopped on. Publishing
        # `answered` for `work` and then faulting over the envelope would emit
        # exactly that contradiction, and the manager would refuse the whole
        # exchange rather than read the fault.
        if operation == "work":
            disposition = answer.get("disposition")
            manifest = _published_manifest_digest()
            if manifest is None:
                return _faulted(event_root, command, digested, operation,
                                one["operation_id"], answered, "output")
        _publish(event_root, f"state-{operation}.json",
                 _bound(command, digested, schema=STATE_SCHEMA,
                        operation=operation,
                        operation_id=one["operation_id"],
                        state="answered"))
        answered.append(operation)
    if manifest is None:
        # EVERY COMMANDED OPERATION SUCCEEDED AND NONE OF THEM WAS `work`, so
        # there is nothing this sequence could correlate an answer to. The
        # manager holds an answered terminal to a canonical completion digest,
        # so publishing one here would be publishing a document it refuses;
        # the honest report is that this exchange asked for no work.
        return _faulted(event_root, command, digested,
                        command["operations"][-1]["operation"],
                        command["operations"][-1]["operation_id"],
                        answered[:-1], "exchange")
    _publish(event_root, TERMINAL_DOCUMENT,
             _bound(command, digested, schema=TERMINAL_SCHEMA,
                    ending="answered", answered=answered,
                    disposition=disposition, fault_code=None,
                    manifest_digest=manifest))
    return 0


def _faulted(event_root, command, digested, operation, operation_id, answered,
             code):
    """One refused operation, ended once and correlated.

    THE FAULT CODE AND NOTHING ELSE. This program's codes are a closed set of
    short literals it authored; a message is composed from values it read,
    including the assignment, the agent's answer and the container's own paths,
    and none of those is material the finding permits in a durable exchange
    document.
    """
    _publish(event_root, f"state-{operation}.json",
             _bound(command, digested, schema=STATE_SCHEMA,
                    operation=operation, operation_id=operation_id,
                    state="faulted"))
    _publish(event_root, TERMINAL_DOCUMENT,
             _bound(command, digested, schema=TERMINAL_SCHEMA,
                    ending="faulted", answered=answered, disposition=None,
                    fault_code=code, manifest_digest=None))
    return 1


def serve(stdin, stdout, agent, place=LAUNCH_DOCUMENT,
          command_root=COMMAND_ROOT, event_root=EVENT_ROOT, sleep=None):
    """The loop. Every answerable fault becomes a correlated frame; nothing
    becomes a traceback.

    A worker that died on a malformed frame would leave the manager waiting for
    a runtime that is gone, and reconciliation would have to infer what
    happened from engine state -- which is exactly what the manager is built
    not to do.

    W26291: THE LAUNCH DOCUMENT IS READ HERE, and the two failure kinds it has
    are the two this loop already had. A document that cannot be read at all,
    or that carries no usable session, is `Uncorrelated`: there is nothing to
    answer under, so nothing is written and the manager settles the start it
    already owns. A document that IS correlatable and is wrong in some other
    way -- an unknown member, another generation's schema, an over-long role --
    is LATCHED, answered once through the ordinary correlated fault, and exits
    non-zero. Nothing on either path reaches the agent.
    """
    try:
        document = read_launch(place)
        expected = session_of(document)
    except Uncorrelated:
        # NOTHING THIS PROGRAM SAYS COULD BE MATCHED TO A REQUEST. The ruling
        # hands this to the manager, which already owns the launched session.
        return 2
    # THE BOOTSTRAP FAULT IS LATCHED, NOT RAISED. The framing loop is still
    # operable, so the failure is answered through the ordinary correlated
    # shape after exactly one identity envelope -- and it never reaches the
    # agent, because the dispatch below is not on this path at all.
    latched = None
    seen = {}
    try:
        seen = launched(document, place)
    except WorkerFault as fault:
        latched = fault
    # W81857: THE LAUNCH DOCUMENT SELECTS THE TRANSPORT, and it is the only
    # thing that does. `seen` is the VALIDATED document, so a `/1` container
    # cannot reach the branch below however its filesystem happens to look, and
    # a latched container -- one whose document is correlatable and wrong in
    # some other way -- has no validated transport at all and answers its one
    # correlated fault through the framing loop exactly as it did before.
    if seen.get("transport") == EXCHANGE_TRANSPORT:
        return serve_exchange(agent, seen, expected, command_root, event_root,
                              sleep=sleep)
    spent = set()
    while True:
        try:
            request = read_frame(stdin)
        except Uncorrelated:
            return 1
        if request is None:
            # A clean end of input is the manager closing the channel. It is
            # NOT cancellation -- cancellation is the manager's runtime stop
            # path and this program never sees it as a message.
            return 1 if latched is not None else 0
        try:
            identity = identity_of(request)
        except Uncorrelated:
            return 1
        # THE BINDING FIRST, ON BOTH PATHS. Re-review [P1]: the latched return
        # below used to come before any correlation check, so a container that
        # had failed to start answered a frame minted for somebody else's
        # session and told them what had gone wrong inside it.
        try:
            bind(identity, expected)
        except WorkerFault as fault:
            write_frame(stdout, failure(identity, fault))
            # A LATCHED CONTAINER STILL ANSWERS EXACTLY ONCE AND EXITS
            # NON-ZERO. Which fault it names changed; how many frames it
            # writes, and that it dispatches nothing, did not.
            if latched is not None:
                return 1
            continue
        if latched is not None:
            write_frame(stdout, failure(identity, latched))
            return 1
        try:
            write_frame(stdout, success(
                identity,
                handle(request, identity, seen, agent, spent)))
        except WorkerFault as fault:
            write_frame(stdout, failure(identity, fault))
        except Exception as failed:                        # noqa: BLE001
            # THE AGENT'S FAILURE IS NOT THIS PROGRAM'S CRASH. It is reported
            # as a fault frame with a bounded description and no traceback: a
            # traceback would carry paths from inside the image out through the
            # channel.
            write_frame(stdout, failure(
                identity,
                WorkerFault("agent",
                            f"the agent failed: {type(failed).__name__}")))


def _scripted_default():
    """The M2 fixture agent, loaded ONLY when nobody injected one.

    W39770. The import lives here rather than at the top of `main` because
    where it lives decides what an image has to carry. `main` opened with an
    unconditional `from scripted_agent import ScriptedAgent`, before it looked
    at whether an agent was supplied -- so the DOCUMENTED INJECTION SEAM could
    not be used by any image that did not also ship the default it was
    overriding. W39357's provider image injects a real Claude adapter and
    carries no scripted agent; its entrypoint died `ModuleNotFoundError`
    before this program started, which its build gate caught and recipe
    inspection could not.

    THE REFERENCE IMAGE IS UNCHANGED. Its recipe ships `scripted_agent.py` and
    its entrypoint supplies no agent, so this is exactly the branch it takes
    and exactly the object it got before.
    """
    from scripted_agent import ScriptedAgent

    return ScriptedAgent()


def main(argv=None, stdin=None, stdout=None, agent=None,
         place=LAUNCH_DOCUMENT, command_root=COMMAND_ROOT,
         event_root=EVENT_ROOT):
    # NO ENVIRONMENT OPERAND AT ALL, W26291. It is not defaulted to `os.environ`
    # and then ignored: a parameter that still exists is a parameter something
    # can be threaded back through, and the supersession retains no fallback.
    #
    # `agent is None`, NOT `agent or`. W39770's review found the second half of
    # the same line: truthiness discarded an explicitly injected FALSEY adapter
    # and substituted the fixture, and only `None` means "nobody injected one".
    # An agent that defines `__bool__` or `__len__` is an ordinary object; a
    # seam that silently replaced it would run somebody else's agent under the
    # caller's assignment.
    return serve(stdin or sys.stdin.buffer, stdout or sys.stdout.buffer,
                 _scripted_default() if agent is None else agent, place,
                 command_root, event_root)


if __name__ == "__main__":
    sys.exit(main())
