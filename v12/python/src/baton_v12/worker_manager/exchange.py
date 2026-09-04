"""THE DURABLE FILE EXCHANGE: one attempt's whole production control path.

W81857, `work/records/2026/09/finding-v12-production-runtime-conversation/`.
The mechanism is not chosen here. Slawomir's supersession of 2026-09-03 and the
reviewer revalidation of 2026-09-04 decide it, and this module implements that
pin rather than re-deciding it.

WHAT THIS REPLACED, and why the replacement is not an equivalent transport.
`worker_entry.converse` is a blocking stdin/stdout conversation held open by
one manager process. It works, it is proved against a real container, and it is
still the diagnostic and test transport -- but a manager that owns the only
reader of a provider's answer has coupled the container's lifetime to its own.
A restart there destroys the reader, makes a healthy container unknowable, and
leaves an uncertain pipe write nobody may safely replay. THE OUTER MANAGER'S
LIFETIME MUST NOT BE THE CONTAINER'S, so production commands and receipts are
DURABLE FILES that outlive every process that wrote them.

THE TWO NAMESPACES, and the direction of each is the whole safety argument:

  `command/`  the manager writes, the container mounts READ-ONLY. One closed
              sequence document per attempt, published atomically under a name
              derived from the sequence identity.
  `events/`   the container writes, the manager reads as UNTRUSTED INPUT. The
              worker's receipt, its per-operation state, and one terminal
              document.

NEITHER DIRECTION IS REACHABLE THROUGH THE OTHER, and that is why this is a
THIRD delivery rather than a corner of an existing root. `inputs` is frozen
before the runtime starts, so a later command cannot be published there at all;
anything under `workspace` is also reachable through the worker's writable
`/output` mount, so a command placed there could be renamed or replaced by the
very program it is addressed to. A read-only alias elsewhere would not help --
the host entry would still be writable through `/output`.

THE PARENT IS NOT WRITABLE BY THE WORKER. This delivery is created inside the
launch root, which `launch.py` establishes at `READ_ONLY_DIR` before the
runtime starts. The worker may write files INSIDE `events/`; it may not rename,
replace or remove `events/` or `command/` themselves, because those are
permissions of the parent.

WHAT THE WORKER WRITES IS NEVER AUTHORITY. The provider runs under the same
container identity and can reach the same mounts, so every document read back
here is bounded, no-follow opened, closed-member checked, and held to the
session, attempt, sequence and command digest THIS MANAGER authored. A terminal
document claiming `answered` is a claim; `/output/output.json`, the exact
runtime observation and the existing freeze/intake gates are what settle it.

WHAT NEVER CROSSES: raw provider stdout/stderr, a recap, a prompt, a source
excerpt, tool input or output, or arbitrary diagnostic prose. W61599/W43972/
W39357 already ruled those bytes credential-capable, and this Work does not
create a sink for them. The event documents carry closed protocol facts and a
bounded safe fault CODE, and §13's durable-secret walk runs over every document
this manager authors.
"""

import json
import os
import re
import stat

from ..contracts import (ContractRefusal, check_no_durable_secret, digest,
                         digest_of_bytes)
from ..contracts.errors import name_value
from . import boundaries
from . import workspaces

__all__ = ["COMMAND_DIRECTORY", "COMMAND_MEMBERS", "COMMAND_SCHEMA",
           "COMMAND_TARGET", "ENDINGS", "EVENT_DIRECTORY", "EVENT_DOCUMENTS",
           "EVENT_TARGET", "EXCHANGE_TRANSPORT", "MAX_EXCHANGE_BYTES",
           "OPERATIONS", "RECEIPT_DOCUMENT", "RECEIPT_MEMBERS",
           "RECEIPT_SCHEMA", "STATES", "STATE_MEMBERS", "STATE_SCHEMA",
           "TERMINAL_DOCUMENT", "TERMINAL_MEMBERS", "TERMINAL_SCHEMA",
           "ExchangeDelivery", "adopt", "command_document", "discard",
           "materialize", "observation", "publish_command", "sequence_of",
           "worker_operation_id"]

# THE VERSION IS IN THE NAME, exactly as `baton.worker-entry/1` and
# `baton.worker-launch/1` carry theirs. The launch document SELECTS this
# transport by naming this exact string, so a worker and a manager from two
# generations refuse by an equality test rather than negotiating.
EXCHANGE_TRANSPORT = "baton.worker-exchange/1"

# THE FIXED CONTAINER PATHS, constants of the contract at BOTH ends. A path a
# caller could vary is a path a runtime can be pointed at wrongly, so there is
# no locator environment variable and no caller-selected target -- the worker
# is told where to look by this contract and the adapter composes exactly these
# two targets and refuses to compose another.
COMMAND_TARGET = "/run/baton/exchange/command"
EVENT_TARGET = "/run/baton/exchange/events"

# The two host directory names inside the launch root. Named here rather than
# by the launch module because the SHAPE of this delivery is this component's;
# what `launch.py` owns is where the root is and when it is closed.
COMMAND_DIRECTORY = "command"
EVENT_DIRECTORY = "events"

COMMAND_SCHEMA = "baton.worker-exchange.command/1"
RECEIPT_SCHEMA = "baton.worker-exchange.receipt/1"
STATE_SCHEMA = "baton.worker-exchange.state/1"
TERMINAL_SCHEMA = "baton.worker-exchange.terminal/1"

# ONE SEQUENCE PER ATTEMPT, and the two operations in it. This bootstrap needs
# a command, not a queue: the ordered pair is the whole vocabulary, and a
# general queue would be scheduling policy W71877 owns.
OPERATIONS = ("describe", "work")

# The worker's own closed ending vocabulary, the same three words the
# diagnostic transport answers with. They mean the same things and are
# deliberately not renamed: two vocabularies for one outcome is how an operator
# stops being able to compare a diagnostic run with a production one.
ENDINGS = ("answered", "faulted", "lost")

# What the worker may say about one operation it actually reached.
# `dispatched` is published BEFORE the provider is asked and `answered` after
# the answer is in hand, so an operator can tell "the turn is running" from
# "the turn is over" without interpreting silence.
STATES = ("dispatched", "answered", "faulted")

# W81857 review 2026-09-04T03-43-45Z [P1]: THE WORKER'S FAULT CODES, CLOSED.
#
# `fault_code` used to be "any bounded string", and a byte ceiling is not a
# credential-safety boundary. The provider runs under the container identity
# that owns the event namespace, so it can replace these files -- and a
# manager that accepted arbitrary text there put worker-chosen bytes into the
# status document and the sweep report. These are the codes `baton_worker`
# actually raises; anything else is refused rather than carried.
FAULT_CODES = ("agent", "answer", "entitlement", "exchange", "input",
               "launch", "output", "protocol", "replay", "session")

# The worker disposition vocabulary, mirrored from `schema.DISPOSITIONS`
# rather than imported, for the reason every other constant here is mirrored:
# this module is read by both ends of a boundary and the test holds the copies
# together. An answered `work` carries one of these and nothing else.
DISPOSITIONS = ("completed", "unable", "plan-rejected", "cancelled")

# THE SHAPES EACH MEMBER MUST HAVE. A closed vocabulary where there is one, a
# canonical grammar where there is not, and `None` only where the ending says
# the member does not apply. Nothing here is a length check.
_INSTANT = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}"
                      r"T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z\Z")
_SHA256 = re.compile(r"\Asha256:[0-9a-f]{64}\Z")

COMMAND_MEMBERS = ("schema", "session", "attempt_id", "sequence_id",
                   "operations")
COMMAND_OPERATION_MEMBERS = ("operation", "operation_id")

# THE WORKER'S THREE DOCUMENTS, at FIXED NAMES. A name the worker chooses is a
# name the manager would have to discover, and discovery over a directory the
# worker can write is how a foreign entry becomes protocol state. Anything else
# found in the event namespace is reported as a foreign entry and read by
# nothing.
RECEIPT_DOCUMENT = "receipt.json"
TERMINAL_DOCUMENT = "terminal.json"


def state_document(operation):
    """The fixed event name carrying one operation's state.

    DERIVED FROM THE CLOSED OPERATION SET rather than from anything a document
    says: the caller passes one of `OPERATIONS` and gets a constant back, so
    there is no path component a worker-written value could reach.
    """
    if operation not in OPERATIONS:
        _refuse(f"this exchange carries {', '.join(OPERATIONS)}; this is "
                f"{name_value(operation)}")
    return f"state-{operation}.json"


EVENT_DOCUMENTS = ((RECEIPT_DOCUMENT,)
                   + tuple(f"state-{one}.json" for one in OPERATIONS)
                   + (TERMINAL_DOCUMENT,))

RECEIPT_MEMBERS = ("schema", "session", "attempt_id", "sequence_id",
                   "command_digest", "accepted_at")
STATE_MEMBERS = ("schema", "session", "attempt_id", "sequence_id",
                 "command_digest", "operation", "operation_id", "state")
# THE TERMINAL DOCUMENT'S CLOSED SET, and every member of it is a bounded
# protocol fact. `disposition` is the worker's answer for an answered `work`
# and null otherwise; `fault_code` is a bounded safe CODE and never a message;
# `manifest_digest` names the completion envelope the worker published under
# the existing `/output/output.json` contract, so the manager can hold the two
# against each other without this document carrying any output.
TERMINAL_MEMBERS = ("schema", "session", "attempt_id", "sequence_id",
                    "command_digest", "ending", "answered", "disposition",
                    "fault_code", "manifest_digest")

# The whole of any one document, bounded before it is read into memory. A
# reader with no bound is bounded by whoever writes the file, and half of these
# files are written by the least trusted program in the deployment.
MAX_EXCHANGE_BYTES = 65536                     # 64 KiB
MAX_EXCHANGE_VALUE = 4096

# How many entries the event namespace may hold before this manager stops
# listing it. The worker publishes four documents; a directory holding
# thousands is a worker doing something this contract does not describe, and
# enumerating it is not this reader's job.
MAX_EVENT_ENTRIES = 64

# THE COMMAND DIRECTORY IS MANAGER-WRITABLE AND WORLD-READABLE, and both halves
# are deliberate. The command is published AFTER the runtime starts -- that is
# what makes the publication level-triggered rather than a launch-time act --
# so this directory cannot be frozen the way the launch document's root is. The
# container's fixed uid 65532 is not this manager's, and a bind mount carries
# the host mode through, so `other` must be able to read and traverse or the
# worker sees an empty directory forever. It is mounted READ-ONLY, which is
# what actually stops the worker writing here, and the worker proves that for
# itself rather than trusting the mode.
COMMAND_DIR = 0o755
COMMAND_FILE = 0o444


def _refuse(message, code="schema"):
    raise ContractRefusal("integrity", code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _untrusted(message):
    """A worker-written document this manager will not adopt.

    A SEPARATE CATEGORY from an integrity refusal, because the two are
    different questions to an operator: `integrity` means this build and its
    own durable state disagree, and this means the least trusted program in
    the deployment wrote something outside its contract. Neither is success and
    only one is a bug here.
    """
    raise ContractRefusal("refused", "precondition", message)


def sequence_of(attempt_id):
    """THE ONE SEQUENCE IDENTITY of one attempt, derived and not supplied.

    DERIVED, because a caller-supplied sequence name is a caller-supplied
    FILENAME: the published document's final name comes from this value, and a
    manager that accepted one from anywhere would be accepting a path. Deriving
    it from the attempt also makes two managers racing the same attempt author
    the same name, which is what turns the race into one identical document
    instead of two.
    """
    attempt = boundaries.identity(attempt_id, "an exchange attempt id")
    return "sequence-" + digest(f"{EXCHANGE_TRANSPORT}:{attempt}")[7:39]


def worker_operation_id(attempt_id, operation):
    """One operation's stable, attempt-derived identity.

    The SAME spelling the diagnostic transport uses, deliberately. A worker
    consumes an operation id once per session and the durable receipt is what
    fences it across sessions -- so this value is a correlation LABEL, and the
    finding is explicit that it is necessary and not sufficient.
    """
    attempt = boundaries.identity(attempt_id, "an exchange attempt id")
    if operation not in OPERATIONS:
        _refuse(f"this exchange carries {', '.join(OPERATIONS)}; this is "
                f"{name_value(operation)}")
    return f"{operation}:{attempt}"


def _value(given, name):
    value = boundaries.text(given, "an exchange document value")
    if len(value) > MAX_EXCHANGE_VALUE:
        _denied(f"an exchange document's {name} is wider than "
                f"{MAX_EXCHANGE_VALUE} characters")
    if "\x00" in value:
        _refuse(f"an exchange document's {name} carries a NUL; a value that "
                f"truncates where it is read is not one this manager writes")
    return value


def command_document(*, session, attempt_id):
    """The complete, closed command sequence for one attempt.

    AUTHORED HERE RATHER THAN ASSEMBLED BY A CALLER, and rebuilt over the
    member tuples rather than copied from a mapping, exactly as the launch
    document is: a caller supplies two identities, not a document shape, and
    not an operation order.

    THE ORDER IS THIS CONTRACT'S. `describe` then `work`, because the manager
    is not a scheduler that picks operations and the worker is not one that
    reorders them -- the pair is the sequence, and a document that named
    anything else would be a queue this Work is explicitly not building.

    §13 WALKS THE RESULT. The document is durable for the life of an attempt
    and is world-readable through a read-only mount, so a live bearer arriving
    through a session or attempt identity would sit in a file the worker reads.
    """
    held = _value(session, "session")
    attempt = _value(attempt_id, "attempt_id")
    boundaries.identity(attempt, "an exchange attempt id")
    document = {"schema": COMMAND_SCHEMA,
                "session": held,
                "attempt_id": attempt,
                "sequence_id": sequence_of(attempt),
                "operations": [{"operation": one,
                                "operation_id": worker_operation_id(attempt,
                                                                    one)}
                               for one in OPERATIONS]}
    check_no_durable_secret(document, what="a worker exchange command")
    return document


def _bytes(document):
    """The exact bytes the worker will read, bounded before they are written.

    Sorted and separator-free for the reason every document this campaign
    writes is: two readers that canonicalize differently do not agree about
    what was delivered, and the DIGEST of these bytes is what every worker
    document is correlated by.
    """
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_EXCHANGE_BYTES:
        _denied(f"this exchange command is {len(payload)} bytes and the "
                f"worker reads at most {MAX_EXCHANGE_BYTES}; a document the "
                f"worker would refuse is not one this manager writes")
    return payload


class ExchangeDelivery:
    """The TYPED capability the adapter receives, and the only one.

    The adapter is handed this object rather than two paths or a mount plan.
    Path operands would be caller-selected locators -- the thing the fixed
    targets exist to take away -- and what the adapter can do with this is ask
    for exactly two mounts whose targets are this contract's constants.

    THE TWO ROOTS ARE DERIVED FROM THE ONE ROOT rather than supplied beside it.
    A delivery whose command directory and event directory could name unrelated
    places would be a delivery with no shape, and the shape is what makes the
    worker unable to reach the command namespace through the writable one.
    """

    __slots__ = ("attempt_id", "root", "command_root", "event_root")

    def __init__(self, *, attempt_id, root):
        self.attempt_id = boundaries.identity(attempt_id,
                                              "an exchange attempt id")
        self.root = boundaries.text(root, "an exchange delivery root")
        self.command_root = os.path.join(self.root, COMMAND_DIRECTORY)
        self.event_root = os.path.join(self.root, EVENT_DIRECTORY)

    def mounts(self):
        """The TWO binds this delivery authorizes, and their direction.

        Triples rather than mount documents: `writable` is not a parameter a
        caller may relax here. A writable command namespace would be a command
        the worker could rewrite between reading it and being asked about it,
        and a read-only event namespace would be a worker that cannot answer.
        """
        return ((self.command_root, COMMAND_TARGET, False),
                (self.event_root, EVENT_TARGET, True))


def _own_directory(place, mode, what):
    """One directory this manager established, proved on its own descriptor.

    EVERY PROOF IS DESCRIPTOR-RELATIVE AND NO-FOLLOW, for the reason
    `launch.adopt` gives: checking with `isdir`, mode-checking with `lstat` and
    then opening by name is three lookups of a path that can change between
    them. The descriptor is the one thing a racing replacement cannot have
    changed.
    """
    try:
        opened = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _denied(f"{what} is not a directory this manager made "
                f"({type(failure).__name__}); an entry of another type is "
                f"state this build cannot account for")
    held = os.stat(opened)
    if stat.S_IMODE(held.st_mode) != mode:
        os.close(opened)
        _denied(f"{what} is mode {oct(stat.S_IMODE(held.st_mode))} and this "
                f"manager established {oct(mode)}; a delivery whose modes have "
                f"moved is not the one it wrote")
    return opened


def materialize(root, *, attempt_id, workspace_group):
    """Create this attempt's exchange namespaces under an existing root.

    CALLED BEFORE THE RUNTIME STARTS and never after: the mounts are fixed when
    the container is created, so a namespace that did not exist then is one
    nothing will ever hold. What happens after the start is PUBLICATION, which
    is a write into a directory that already exists and is already mounted.

    THE EVENT NAMESPACE IS GROUP-WRITABLE, through the same owner that grants
    the assignment workspace. The container's fixed uid 65532 is not this
    manager's and cannot be; `--group-add` is what gives it a share, and
    `adopt_workspace_group` is what puts the directory in that group and
    establishes the mode exactly rather than requesting it through a umask.

    THE COMMAND NAMESPACE IS NOT IN THAT GROUP and is not group-writable. It is
    this manager's directory, world-readable so the container's uid can
    traverse it, and mounted read-only so the container cannot write it.
    """
    place = boundaries.text(root, "an exchange delivery root")
    delivery = ExchangeDelivery(attempt_id=attempt_id, root=place)
    os.makedirs(delivery.command_root, mode=0o700, exist_ok=False)
    os.chmod(delivery.command_root, COMMAND_DIR)
    os.makedirs(delivery.event_root, mode=0o700, exist_ok=False)
    workspaces.adopt_workspace_group({"workspace": delivery.event_root},
                                     workspaces.check_workspace_group(
                                         _gid(workspace_group)))
    return delivery


def _gid(workspace_group):
    """The configured group, taken only from this manager's own frozen answer.

    The same rule `workspaces.assignment_workspace` states: only
    `configured_workspace_group` mints a `WorkspaceGroup`, so a caller holding
    one means the deployment configured it. An integer here would be
    validating whatever the caller chose.
    """
    if type(workspace_group) is not workspaces.WorkspaceGroup:
        _denied(f"an exchange event namespace is created in the deployment's "
                f"configured workspace group, obtained from this manager's "
                f"own record; this is {name_value(workspace_group)}")
    return workspace_group.gid


def adopt(root, *, attempt_id, workspace_group):
    """Recover the delivery THIS MANAGER already made, or FAIL CLOSED.

    ABSENT ADOPTS NOTHING, and that is an ordinary answer for an attempt whose
    launch predates this transport: `None` is what lets a caller tell that
    apart from a delivery it failed to prove. A caller for whom absence is
    contradictory -- one whose launch document SELECTS this transport -- is the
    caller that must refuse, and this component does not decide that for it.

    WHAT IS PROVED IS SHAPE AND MODE, not content. The command document's
    content is proved where it is read, against the bytes this manager would
    have authored; the worker's documents are proved every time they are read,
    because they can change between two reads and a proof that has to stay true
    between them is not a proof.
    """
    place = boundaries.text(root, "an exchange delivery root")
    delivery = ExchangeDelivery(attempt_id=attempt_id, root=place)
    if not os.path.lexists(delivery.command_root) \
            and not os.path.lexists(delivery.event_root):
        return None
    os.close(_own_directory(delivery.command_root, COMMAND_DIR,
                            f"attempt {name_value(delivery.attempt_id)}'s "
                            f"exchange command namespace"))
    opened = _own_directory(delivery.event_root, workspaces.WORKSPACE_DIR,
                            f"attempt {name_value(delivery.attempt_id)}'s "
                            f"exchange event namespace")
    try:
        held = os.stat(opened)
        gid = workspaces.check_workspace_group(_gid(workspace_group))
        if held.st_gid != gid:
            _denied(f"attempt {name_value(delivery.attempt_id)}'s exchange "
                    f"event namespace is in group {held.st_gid} and this "
                    f"deployment configured {gid}; a namespace the worker's "
                    f"container does not share is one it cannot answer in")
    finally:
        os.close(opened)
    return delivery


def publish_command(delivery, document):
    """Publish the one command sequence, ATOMICALLY, or replay the identical
    one already there.

    THE FILENAME IS DERIVED, NEVER SUPPLIED. It comes from the document's own
    sequence identity, which `command_document` derived from the attempt -- so
    two managers racing this attempt compose the same bytes under the same
    name, and the second one finds the first one's document and adopts it.

    PUBLICATION IS FIVE STEPS AND ALL FIVE MATTER: exclusive no-follow staging
    so nothing already at the staging name is written through; the complete
    bounded canonical write; `fsync` on the file so the bytes survive the
    machine; `rename` WITHIN the directory so the final name never exists half
    written; and `fsync` on the directory so the rename itself survives. A
    reader that scanned this namespace mid-publication sees the staging name,
    which is not the derived name and is therefore not a command.

    A DIFFERENT DOCUMENT UNDER THE SAME NAME REFUSES. One attempt has one
    sequence; two different byte strings claiming it means this build and
    whatever wrote the other one disagree about what was commanded, and
    replacing it would make the worker's already-published receipt name a
    command that no longer exists.
    """
    if type(delivery) is not ExchangeDelivery:
        _denied(f"a command is published through this component's own typed "
                f"delivery; this is {name_value(delivery)}")
    held = boundaries.document(document, "an exchange command",
                               required=COMMAND_MEMBERS)
    if held["attempt_id"] != delivery.attempt_id:
        _denied(f"this command names attempt "
                f"{name_value(held['attempt_id'])} and the delivery belongs "
                f"to {name_value(delivery.attempt_id)}; one delivery carries "
                f"one attempt's sequence")
    payload = _bytes(held)
    name = held["sequence_id"] + ".json"
    place = os.path.join(delivery.command_root, name)
    existing = _read_exact(delivery.command_root, name, what="the command")
    if existing is not None:
        if existing != payload:
            _denied(f"attempt {name_value(delivery.attempt_id)} already "
                    f"carries a different command under "
                    f"{name_value(name)}; one attempt has one sequence, and "
                    f"replacing it would leave the worker's receipt naming a "
                    f"command that no longer exists")
        return {"published": False, "place": place,
                "command_digest": digest_of_bytes(payload)}
    published = _publish_once(delivery.command_root, name, payload)
    if not published:
        # LOST THE RACE TO THE FINAL NAME, which is an ordinary outcome and not
        # a failure: the linking publication below never clobbers, so somebody
        # else's document is still there to be compared. An identical one is
        # adopted; a different one refuses, exactly as an existing document
        # found before staging does.
        existing = _read_exact(delivery.command_root, name, what="the command")
        if existing != payload:
            _denied(f"attempt {name_value(delivery.attempt_id)} already "
                    f"carries a different command under {name_value(name)}; "
                    f"one attempt has one sequence, and replacing it would "
                    f"leave the worker's receipt naming a command that no "
                    f"longer exists")
    return {"published": published, "place": place,
            "command_digest": digest_of_bytes(payload)}


def _publish_once(root, name, payload):
    """Stage, sync, and LINK into the final name. Answers whether we made it.

    W81857 review 2026-09-04T03-43-45Z [P1], and both halves of that finding
    are fixed here.

    THE STAGING NAME IS UNIQUE PER ATTEMPT AT PUBLISHING, not one fixed
    `.publishing`. A fixed name plus `O_EXCL` means a process that died between
    creation and rename leaves a file that makes every later incarnation fail
    `FileExistsError` forever -- a permanent wedge created by a crash, on the
    one path this whole transport exists to survive. Two live managers racing
    hit the same refusal. A unique name cannot collide, and a stale one is
    invisible: readers open the derived final name and `_foreign` reports what
    it does not recognise, so leftover staging is garbage the teardown removes
    rather than state anybody adopts.

    THE FINAL NAME IS TAKEN WITH `link`, NOT `rename`. `rename` silently
    replaces whatever is at the destination, so a publication that raced
    another one would clobber a document the worker may already have receipted.
    `link` is equally atomic and fails closed on an existing name, which turns
    the race into a comparison the caller can make.

    THE STAGING FILE IS ALWAYS REMOVED on the way out, whichever way this ends,
    so the ordinary paths leave nothing behind and only an actual process death
    can strand one.
    """
    staged = os.path.join(root, f".{name}.{os.getpid()}."
                                f"{os.urandom(8).hex()}.publishing")
    handle = os.open(staged,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o000)
    # ONE CLEANUP BOUNDARY OVER EVERYTHING AFTER THE CREATE, and review
    # 2026-09-04T04-17-15Z [P2] is why it is one rather than two. The unwind
    # used to begin only after the write, the mode and the file sync had all
    # succeeded, so an ordinary transient failure in any of them closed the
    # handle and left the staging file behind -- unique names stopped that
    # being a permanent wedge and did not stop it being a leak, one file per
    # failure, contradicting this function's own stated invariant.
    #
    # THE HANDLE IS CLOSED INSIDE IT, so the descriptor is released before the
    # name is removed whichever way this ends, and no path can reach the exit
    # with either still held.
    try:
        try:
            _write_whole(handle, payload)
            os.fchmod(handle, COMMAND_FILE)
            os.fsync(handle)
        finally:
            os.close(handle)
        try:
            os.link(staged, os.path.join(root, name))
        except FileExistsError:
            return False
        opened = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(opened)
        finally:
            os.close(opened)
        return True
    finally:
        # THE STAGED NAME ALWAYS GOES, and the FINAL name is untouched by it:
        # `link` made a second name for the same inode, so removing this one
        # removes a name and not the document.
        try:
            os.unlink(staged)
        except OSError:
            pass


def _write_whole(handle, payload):
    """Every byte, or a refusal. `os.write` is allowed to write fewer.

    The same rule `launch._write_whole` states, for the same reason: a short
    write is ordinary rather than exotic, it is not an error the call reports,
    and a TRUNCATED command is one the worker refuses while this manager
    believes it delivered a whole one.
    """
    written = 0
    while written < len(payload):
        step = os.write(handle, payload[written:])
        if type(step) is not int or step <= 0:
            _refuse(f"writing the exchange command made no progress after "
                    f"{written} of {len(payload)} bytes; a partly written "
                    f"command is one the worker refuses and this manager "
                    f"believes it delivered")
        written += step
    return written


def _read_exact(place, name, *, what):
    """One named regular file's whole bytes, or absence -- NO-FOLLOW, BOUNDED.

    The four properties are the launch reader's and each one is a way a
    container can hand this manager something other than a document:
    NO-FOLLOW so a link at a fixed name is refused rather than resolved,
    NON-BLOCKING so a FIFO cannot stop this manager inside `open` before the
    descriptor check runs, REGULAR proved on the DESCRIPTOR rather than on the
    path, and BOUNDED at one byte past the ceiling.
    """
    try:
        opened = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError:
        return None
    try:
        try:
            handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=opened)
        except FileNotFoundError:
            return None
        except OSError as failure:
            _untrusted(f"{what} at {name_value(name)} could not be opened as "
                       f"an ordinary file ({type(failure).__name__}); a link "
                       f"or a device at a name this contract fixes is not a "
                       f"document")
    finally:
        os.close(opened)
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode):
            _untrusted(f"{what} at {name_value(name)} is not a regular file")
        raw = os.read(handle, MAX_EXCHANGE_BYTES + 1)
    finally:
        os.close(handle)
    if len(raw) > MAX_EXCHANGE_BYTES:
        _untrusted(f"{what} at {name_value(name)} is wider than "
                   f"{MAX_EXCHANGE_BYTES} bytes; a reader with no bound is "
                   f"bounded by whoever writes the file")
    return raw


def _decoded(raw, name, *, what, members, nested=()):
    """One worker-written document, held to its closed member set.

    A CLOSED SET, not an allowlist, and every value bounded text. An extra
    member is how a second contract alias would arrive from a program this
    manager does not trust, and refusing it is the same rule the launch
    document is held to at the other end.
    """
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        _untrusted(f"{what} at {name_value(name)} is not UTF-8 JSON")
    if type(document) is not dict:
        _untrusted(f"{what} at {name_value(name)} is one JSON object")
    missing = sorted(one for one in members if one not in document)
    extra = sorted(one for one in document if one not in members)
    if missing or extra:
        _untrusted(f"{what} at {name_value(name)} is exactly "
                   f"{', '.join(members)}"
                   + (f"; missing {', '.join(missing)}" if missing else "")
                   + (f"; unexpected {', '.join(extra)}" if extra else ""))
    for member, value in document.items():
        if member in nested:
            # THE MEMBER'S OWN OWNER VALIDATES IT. `operations` is a list of
            # closed objects and every other member of every document here is
            # bounded text; one rule that tried to describe both would be a
            # rule that describes neither, so the structured member is checked
            # where its shape is actually known.
            continue
        if value is None:
            continue
        if type(value) is str and len(value) <= MAX_EXCHANGE_VALUE:
            continue
        if type(value) is list and len(value) <= len(OPERATIONS) \
                and all(type(one) is str and len(one) <= MAX_EXCHANGE_VALUE
                        for one in value):
            continue
        _untrusted(f"{what} at {name_value(name)} carries a {member} that is "
                   f"not bounded text, a bounded list of it, or null")
    return document


def _instant(value, name, what):
    """A canonical manager-grammar instant, or a refusal.

    W81857 review [P1]: this member used to be "bounded text", and the
    reproduction put a registered live bearer in it and watched it reach the
    status projection. A timestamp has a shape; holding it to that shape is
    what makes it a timestamp rather than a place to put forty characters.

    THE GRAMMAR AND THE CALENDAR, both, for the reason `boundaries.instant`
    states: `2026-99-99T99:99:99.999Z` has the shape and is not a date.
    """
    if type(value) is not str or not _INSTANT.match(value):
        _untrusted(f"{what} carries a {name} that is not one canonical "
                   f"instant")
    try:
        boundaries.instant(value, f"a worker document's {name}")
    except ContractRefusal:
        _untrusted(f"{what} carries a {name} with the grammar of an instant "
                   f"and no calendar behind it")
    return value


def _vocabulary(value, allowed, name, holder, what):
    """One member held to a closed set.

    NAMED `_vocabulary` RATHER THAN `_one_of`, and that is not a style choice.
    `test_boundary_inventory` resolves private helper returns by BARE FUNCTION
    NAME across the whole package, first module in sorted order winning -- so a
    second `_one_of` here silently retargeted `oci.py:OciAdapter.observe`'s
    `document.Running` entry to this function's parameter name, and a
    registry entry for a module this Work never touched went stale. A private
    helper's name is package-global to that inventory whether or not it is
    package-global to Python.
    """
    if value not in allowed:
        _untrusted(f"{what} at {name_value(holder)} carries a {name} this "
                   f"build does not know; the vocabulary is closed and an "
                   f"unrecognised value is not read as the calmest member of "
                   f"it")
    return value


def _sha256(value, name, holder, what):
    if type(value) is not str or not _SHA256.match(value):
        _untrusted(f"{what} at {name_value(holder)} carries a {name} that is "
                   f"not one lower-case sha256 digest")
    return value


def _absent(value, name, holder, what):
    if value is not None:
        _untrusted(f"{what} at {name_value(holder)} carries a {name} its "
                   f"ending does not have; a member that does not apply is "
                   f"null rather than whatever the writer had to hand")
    return None


def _correlated(document, delivery, command, name, *, what):
    """Every worker document, bound to the command THIS MANAGER authored.

    THE DIGEST IS THE BINDING and the identities are the readable half of it. A
    document naming another session, attempt, sequence or command is not this
    exchange's -- it is a stale document from a previous delivery, a copy from
    another attempt, or something the provider wrote -- and none of those is a
    fact about the turn this manager commanded.
    """
    for member, expected in (("session", command["session"]),
                             ("attempt_id", delivery.attempt_id),
                             ("sequence_id", command["sequence_id"]),
                             ("command_digest", command["command_digest"])):
        if document.get(member) != expected:
            _untrusted(f"{what} at {name_value(name)} names {member} "
                       f"{name_value(document.get(member))} and this "
                       f"manager commanded {name_value(expected)}; a "
                       f"document that is merely well formed proves which "
                       f"KIND of thing it is and not which exchange")
    return document


def _command_view(delivery):
    """What this manager published, read back from the durable file.

    READ BACK RATHER THAN REMEMBERED, which is the whole design: a restarted
    manager holds nothing, and the command is either on disk or it was never
    published. What is returned carries the digest every worker document is
    correlated by.

    EVERYTHING EXCEPT THE SESSION IS DERIVED FROM THE ATTEMPT, so this read is
    a comparison against what this manager would have authored rather than a
    second parser: the filename, the sequence identity, the operation order and
    each operation's identity all come from `sequence_of` and
    `worker_operation_id`. A document that is merely well formed proves which
    KIND of thing it is and not which delivery, which is the rule `launch.adopt`
    is held to at the other end.

    THE SESSION IS TAKEN, NOT DERIVED, because this component does not own how
    a deployment mints one. It is not thereby unchecked: it is what every
    worker document is then correlated against, so a command carrying a session
    the container was not launched under produces an exchange whose worker
    documents are all foreign, and the worker itself refuses a command naming
    another session before it publishes anything at all.
    """
    name = sequence_of(delivery.attempt_id) + ".json"
    raw = _read_exact(delivery.command_root, name, what="the command")
    if raw is None:
        return None
    document = _decoded(raw, name, what="the command", members=COMMAND_MEMBERS,
                        nested=("operations",))
    if document["sequence_id"] != sequence_of(delivery.attempt_id) \
            or document["attempt_id"] != delivery.attempt_id \
            or document["schema"] != COMMAND_SCHEMA:
        _untrusted(f"the command at {name_value(name)} names attempt "
                   f"{name_value(document['attempt_id'])} sequence "
                   f"{name_value(document['sequence_id'])}, and this delivery "
                   f"carries attempt {name_value(delivery.attempt_id)}")
    ordered = document["operations"]
    wanted = [{"operation": one,
               "operation_id": worker_operation_id(delivery.attempt_id, one)}
              for one in OPERATIONS]
    if ordered != wanted:
        _untrusted(f"the command at {name_value(name)} carries an operation "
                   f"sequence this manager would not have authored for "
                   f"attempt {name_value(delivery.attempt_id)}")
    return {"sequence_id": document["sequence_id"],
            "session": document["session"],
            "operations": list(OPERATIONS),
            "command_digest": digest_of_bytes(raw)}


def _event(delivery, command, name, members, schema, what):
    """One worker document, held to its KIND before anything else about it.

    W81857 review 2026-09-04T04-17-15Z [P1]: `schema` was in every closed
    member set and was compared with nothing, so a document explicitly
    identifying itself as another protocol was read as this one merely because
    it had the right member names at the right filename. Schema identity is the
    type and version discriminator -- it is what `launch.py` and the worker
    both check by equality, for exactly this reason -- and a bounded string
    nobody compares is decoration.

    THE KIND IS CHECKED BEFORE THE CORRELATION, deliberately: "this is not a
    receipt" is a different and prior answer to "this is not THIS exchange's
    receipt", and asking them in the other order would report a foreign
    protocol as a correlation failure.
    """
    raw = _read_exact(delivery.event_root, name, what=what)
    if raw is None:
        return None
    document = _decoded(raw, name, what=what, members=members)
    if document["schema"] != schema:
        _untrusted(f"{what} at {name_value(name)} says it is "
                   f"{name_value(document['schema'])} and this exchange reads "
                   f"{name_value(schema)}; a document from another protocol is "
                   f"not one to read the recognised parts out of")
    return _correlated(document, delivery, command, name, what=what)


def observation(delivery):
    """This attempt's whole exchange, from the durable files and nothing else.

    THE FULL SCAN IS AUTHORITATIVE and there is no cursor. A follower -- a
    tailer, a poll, a filesystem notification -- may reduce latency, and losing
    one costs latency and nothing else, because this function reconstructs the
    same answer from the same files every time it is called.

    WHAT IT ANSWERS IS OBSERVATION, NEVER SETTLEMENT. An `answered` terminal is
    the worker's claim; the caller still validates `/output/output.json`,
    observes the exact runtime, and applies the existing freeze and intake
    gates. `incomplete` is a real answer and is deliberately not rounded to
    `lost`: a receipt with no terminal means the provider may still be running,
    and only positive evidence about the runtime may turn that into an ending.

    A REFUSAL FROM A WORKER DOCUMENT IS AN OBSERVATION, NOT AN EXCEPTION.
    Malformed, foreign, oversized, linked or conflicting worker material is
    reported as `unreadable` with a bounded safe reason, because a manager that
    raised here would let the least trusted program in the deployment stop the
    sweep for every other stage.
    """
    if type(delivery) is not ExchangeDelivery:
        _denied(f"an exchange is observed through this component's own typed "
                f"delivery; this is {name_value(delivery)}")
    view = {"transport": EXCHANGE_TRANSPORT,
            "sequence_id": sequence_of(delivery.attempt_id),
            "command": None, "receipt": None, "states": [], "terminal": None,
            "foreign": [], "unreadable": None, "state": "not-requested"}
    try:
        command = _command_view(delivery)
    except ContractRefusal as refusal:
        view["unreadable"] = _safe(refusal)
        view["state"] = "unreadable"
        return view
    if command is None:
        return view
    view["command"] = {"sequence_id": command["sequence_id"],
                       "command_digest": command["command_digest"],
                       "operations": list(command["operations"])}
    view["state"] = "waiting"
    try:
        view["foreign"] = _foreign(delivery)
        receipt = _event(delivery, command, RECEIPT_DOCUMENT,
                         RECEIPT_MEMBERS, RECEIPT_SCHEMA,
                         "the worker receipt")
        if receipt is not None:
            view["receipt"] = {
                "accepted_at": _instant(receipt["accepted_at"],
                                        "accepted_at",
                                        "the worker receipt")}
            view["state"] = "working"
        for operation in OPERATIONS:
            found = _event(delivery, command, state_document(operation),
                           STATE_MEMBERS, STATE_SCHEMA,
                           "a worker state event")
            if found is None:
                continue
            if found["operation"] != operation:
                _untrusted(f"a worker state event at "
                           f"{name_value(state_document(operation))} reports "
                           f"operation {name_value(found['operation'])}")
            if found["operation_id"] != worker_operation_id(
                    delivery.attempt_id, operation):
                _untrusted(f"a worker state event for {operation} names "
                           f"operation id "
                           f"{name_value(found['operation_id'])}")
            _vocabulary(found["state"], STATES, "state",
                    state_document(operation), "a worker state event")
            view["states"].append({"operation": operation,
                                   "state": found["state"]})
        terminal = _event(delivery, command, TERMINAL_DOCUMENT,
                          TERMINAL_MEMBERS, TERMINAL_SCHEMA,
                          "the worker terminal result")
        if terminal is not None:
            view["terminal"] = _terminal(terminal, delivery)
            _caused(view, receipt)
            view["state"] = view["terminal"]["ending"]
        elif receipt is not None:
            # A RECEIPT WITHOUT A TERMINAL IS NOT AN ENDING. The provider may
            # still be running, and this manager cannot tell that apart from a
            # worker that died mid-turn without asking the engine. Saying
            # `working` and letting the runtime observation decide is the only
            # answer that does not interpret silence as either progress or
            # failure.
            view["state"] = "working"
        # W81857 review [P1]: THE DURABLE-SECRET WALK, OVER THE WHOLE ANSWER
        # AND INSIDE THE GUARD. Every member above is already held to a closed
        # vocabulary or a canonical grammar, and this is the second line rather
        # than the first: §13 is the shipped rule about what may cross a
        # durable surface, the projection is exactly such a surface, and a
        # future member added without a shape check must not be able to walk
        # past it. A registered live bearer here makes the exchange
        # `unreadable`, which is a refusal the operator can see, rather than a
        # value that reaches a status document.
        check_no_durable_secret(view, what="a worker exchange projection")
    except ContractRefusal as refusal:
        view["unreadable"] = _safe(refusal)
        view["state"] = "unreadable"
        # EVERY WORKER-AUTHORED MEMBER IS DROPPED, and the manager's own
        # command is kept. Review [P1]: leaving the members that happened to
        # parse standing beside a refusal hands a reader half of a
        # disagreement with nothing saying which half -- and one of those
        # halves is exactly the value that was refused for carrying something
        # it should not. What this manager wrote is not in question and is
        # what tells an operator which sequence the refusal is about.
        view["receipt"] = None
        view["states"] = []
        view["terminal"] = None
    return view


def _caused(view, receipt):
    """A terminal is the END of a sequence, so its whole history has to fit.

    W81857 review 2026-09-04T04-17-15Z [P1]. The receipt, the state events and
    the terminal were read independently and a correlated terminal decided the
    ending on its own -- so a worker or provider that wrote ONLY an answered
    terminal skipped the pre-dispatch replay fence and the per-operation
    evidence and was projected as a successful answer. That is the one document
    it must not be possible to forge alone: the receipt is the durable proof
    that dispatch was fenced BEFORE any provider ran, and a result whose fence
    never existed is a result about a turn nobody can say happened once.

    W81857 review 2026-09-04T04-31-34Z [P1] SUPERSEDES THE WEAKER RULE that
    correction first shipped. Requiring the answered prefix and rejecting only
    a LATER `answered` state left every other impossible tail acceptable: a
    `work` event before `describe` completed, a `lost` ending beside a
    positively observed fault, a `lost` ending after the whole sequence was
    answered, and a `dispatched` event for an operation the sequence had
    already stopped faulted before. Each is a history the reference worker
    cannot publish, and "the parts I checked agree" is not the same claim as
    "this is a history".

    SO THE EXACT REACHABLE VECTOR IS COMPOSED AND COMPARED. The ending decides
    what the whole state map must be, member for member:

      `answered` -- every commanded operation answered, and nothing else;
      `faulted`  -- the answered prefix, the next operation FAULTED, and no
                    state after it, because the sequence stopped there;
      `lost`     -- the answered prefix, at most the next operation
                    DISPATCHED, no fault anywhere, and not a completed
                    sequence: loss is the absence of an observation, so a
                    worker that saw a fault saw one, and a sequence that
                    finished did not go missing.

    `lost` IS THE ONE ENDING WITH AN OPTIONAL SLOT, and that is the honest
    shape rather than laxity: a process that died between publishing
    `dispatched` and getting an answer leaves exactly that event, and one that
    died before publishing it leaves none. Both are real crash boundaries; a
    third state at that slot is not.
    """
    terminal = view["terminal"]
    if receipt is None:
        _untrusted("a worker terminal result arrived with no receipt; the "
                   "receipt is the durable proof that dispatch was fenced "
                   "before any provider ran, and an ending whose fence never "
                   "existed is not evidence that the turn happened once")
    held = {one["operation"]: one["state"] for one in view["states"]}
    answered = terminal["answered"]
    ending = terminal["ending"]
    remaining = list(OPERATIONS[len(answered):])
    wanted = {operation: "answered" for operation in answered}
    optional = None
    if ending == "faulted":
        if not remaining:
            _untrusted("the worker terminal result is faulted and answers "
                       "every commanded operation; a fault happened to one of "
                       "them")
        wanted[remaining[0]] = "faulted"
    elif ending == "lost":
        if not remaining:
            _untrusted("the worker terminal result is lost and answers every "
                       "commanded operation; a sequence that finished is not "
                       "one nobody could observe the end of")
        # THE ONE OPTIONAL SLOT. `dispatched` and nothing else: a fault is an
        # observation, and an ending that claims nobody observed the outcome
        # cannot sit beside one.
        optional = (remaining[0], "dispatched")
    for operation, state in sorted(wanted.items()):
        if held.get(operation) != state:
            _untrusted(f"the worker terminal result is {name_value(ending)} "
                       f"with {answered!r} answered, so {operation!r} is "
                       f"{name_value(state)}; its state event says "
                       f"{name_value(held.get(operation))}")
    for operation, state in sorted(held.items()):
        if operation in wanted:
            continue
        if optional is not None and (operation, state) == optional:
            continue
        _untrusted(f"the worker terminal result is {name_value(ending)} with "
                   f"{answered!r} answered, and {operation!r} carries a "
                   f"{name_value(state)} event the sequence could not have "
                   f"reached; a terminal and its own evidence disagreeing is "
                   f"not a result to read either half of")
    return view


def _terminal(terminal, delivery):
    """The worker's terminal claim, held to the closed vocabulary.

    NOTHING IS DEFAULTED. A terminal naming an ending outside the three, or
    answering operations this exchange did not command, is refused rather than
    read as the least alarming member of the set -- the worker's vocabulary is
    closed, so an unknown value means this build and that container disagree
    about what an ending is.
    """
    ending = _vocabulary(terminal["ending"], ENDINGS, "ending", TERMINAL_DOCUMENT,
                     "the worker terminal result")
    answered = terminal["answered"]
    if type(answered) is not list:
        _untrusted("the worker terminal result answers a list of operation "
                   "names")
    if answered != list(OPERATIONS[:len(answered)]):
        _untrusted(f"the worker terminal result answers {answered!r} and this "
                   f"exchange commanded {list(OPERATIONS)!r} in that order")
    if ending == "answered" and list(answered) != list(OPERATIONS):
        _untrusted(f"the worker terminal result claims {name_value(ending)} "
                   f"and answered only {answered!r}; an ending that did not "
                   f"complete the sequence is not an answer to it")
    # W81857 review [P1]: EVERY REMAINING MEMBER IS ENDING-DEPENDENT, and the
    # shape is enforced rather than the length.
    #
    # An answered ending is the only one that carries a disposition, and it
    # MUST carry the digest of the completion envelope the worker published --
    # that digest is the whole reason this member exists, and a terminal that
    # answered `null` or arbitrary text used to drive the entire success path
    # on the strength of a separately valid `output.json`. A faulted ending
    # carries one code from this build's closed set and nothing else; a lost
    # one carries none of the three.
    if ending == "answered":
        disposition = _vocabulary(terminal["disposition"], DISPOSITIONS,
                              "disposition", TERMINAL_DOCUMENT,
                              "the worker terminal result")
        manifest = _sha256(terminal["manifest_digest"], "manifest_digest",
                           TERMINAL_DOCUMENT, "the worker terminal result")
        fault = _absent(terminal["fault_code"], "fault_code",
                        TERMINAL_DOCUMENT, "the worker terminal result")
    else:
        disposition = _absent(terminal["disposition"], "disposition",
                              TERMINAL_DOCUMENT,
                              "the worker terminal result")
        manifest = _absent(terminal["manifest_digest"], "manifest_digest",
                           TERMINAL_DOCUMENT, "the worker terminal result")
        fault = (_vocabulary(terminal["fault_code"], FAULT_CODES, "fault_code",
                         TERMINAL_DOCUMENT, "the worker terminal result")
                 if ending == "faulted"
                 else _absent(terminal["fault_code"], "fault_code",
                              TERMINAL_DOCUMENT,
                              "the worker terminal result"))
    return {"ending": ending, "answered": list(answered),
            "disposition": disposition, "fault_code": fault,
            "manifest_digest": manifest}


def _foreign(delivery):
    """Every entry in the event namespace this contract does not name.

    REPORTED RATHER THAN READ. The worker can create files here -- that is what
    the writable mount is for -- and an entry outside the four fixed names is
    not protocol state. Listing them is how an operator sees a container doing
    something this contract does not describe; opening them would be this
    manager deciding that whatever the provider wrote is worth reading.
    """
    try:
        opened = os.open(delivery.event_root,
                         os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError:
        return []
    try:
        entries = sorted(os.listdir(opened))
    finally:
        os.close(opened)
    if len(entries) > MAX_EVENT_ENTRIES:
        _untrusted(f"attempt {name_value(delivery.attempt_id)}'s exchange "
                   f"event namespace holds {len(entries)} entries and this "
                   f"contract describes {len(EVENT_DOCUMENTS)}; enumerating a "
                   f"namespace that size is not this reader's job")
    return [one for one in entries if one not in EVENT_DOCUMENTS]


def _safe(refusal):
    """A refusal reduced to what may be kept durably beside an attempt.

    THE CATEGORY AND THE CODE, AND NOT THE MESSAGE. A refusal's prose is
    composed from values this manager read -- including values a worker wrote
    -- and the finding is explicit that raw worker material does not become
    durable evidence. What an operator needs from here is which KIND of
    disagreement this was; the message is available to whoever is reading the
    live sweep report.
    """
    return {"category": refusal.category, "code": refusal.code}


def discard(root):
    """Remove this attempt's exchange namespaces, WORKER ENTRIES INCLUDED.

    A DESCRIPTOR-RELATIVE, NO-FOLLOW WALK rather than the flat by-name loop the
    launch root uses, and the difference is the whole reason this function
    exists. `launch.discard` removes names it wrote in a directory nothing else
    may write; the event namespace is writable by the container, so the entries
    here are DYNAMIC and none of them was authored by this manager. Following a
    link out of it would be this manager deleting whatever a worker pointed at.

    ANSWERS WHETHER IT IS GONE, and never raises for an entry it could not
    remove: this runs on the ending path, where the caller's next act depends
    on what is actually left rather than on an exception.
    """
    for name in (COMMAND_DIRECTORY, EVENT_DIRECTORY):
        place = os.path.join(root, name)
        if not os.path.lexists(place):
            continue
        try:
            opened = os.open(place,
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
        except OSError:
            # NOT A DIRECTORY THIS MANAGER MADE. Removing whatever is there by
            # name would be acting on state this build cannot account for, so
            # it is left for the caller to see.
            continue
        try:
            os.fchmod(opened, 0o700)
            for entry in sorted(os.listdir(opened)):
                try:
                    os.unlink(entry, dir_fd=opened)
                except OSError:
                    # A DIRECTORY, OR SOMETHING THIS MANAGER MAY NOT REMOVE.
                    # `unlink` answers `EISDIR` on Linux and `EPERM` on other
                    # kernels for the same case, so the second attempt is
                    # decided by what actually failed rather than by which
                    # errno this platform chose.
                    try:
                        os.rmdir(entry, dir_fd=opened)
                    except OSError:
                        pass
        finally:
            os.close(opened)
        try:
            os.rmdir(place)
        except OSError:
            pass
    return not any(os.path.lexists(os.path.join(root, name))
                   for name in (COMMAND_DIRECTORY, EVENT_DIRECTORY))
