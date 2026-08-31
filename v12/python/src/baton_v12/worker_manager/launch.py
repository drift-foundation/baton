"""THE WORKER'S LAUNCH DOCUMENT: one versioned file, mounted read-only.

W26291, `work/records/2026/08/finding-v12-oci-worker-launch-environment/`. The
mechanism is not chosen here. The dossier's two supersessions and its pinned
contract of 2026-08-28 decide it, and this module implements that pin rather
than re-deciding it.

WHAT THIS REPLACED, and why the replacement is not an equivalent transport.
The first implementation of this Work delivered four `BATON_WORKER_*` values as
`--env` arguments. That is a vocabulary rather than a contract: every new fact
the worker needs is another variable, every variable is another thing a caller
could set, and the set has no version, so a manager and a worker from two
generations disagree silently rather than refusing. One VERSIONED DOCUMENT at a
FIXED path fails closed on exactly that disagreement, and it extends by adding
a member to a schema both ends are held to instead of by widening an
environment channel.

THERE IS NO FALLBACK, and that is the ruling rather than an omission. The
reference worker does not read `BATON_WORKER_POSTURE`, `BATON_WORKER_SESSION`,
`BATON_WORKER_CONTRACT` or `BATON_WORKER_ROLE`, and a container started with
only those refuses. A compatibility path would be the second live contract the
supersession exists to end.

WHAT THE DOCUMENT CARRIES: `schema`, `session`, `contract`, `role`. Four
members, closed. There is no `posture`: the consent-posture supersession
removed the axis, and a member carrying a constant would be transporting a fact
that no longer exists.

WHAT IT NEVER CARRIES: credentials or bearer material, source contents,
arbitrary environment, a Baton authority locator, or a host path. Credentials
are the separate transient read-only provider under `/run/baton/credentials`;
assignment input and worker output are on their own governed mounts. §13 walks
the authored document before it is written, so a live bearer cannot ride this
channel any more than it can ride the start vector.

WHERE THE FILE IS ALLOWED TO BE: one manager-owned regular file, mode 0444,
under a 0555 attempt-private root this module creates and owns outright. The
mode is the manager's own statement that the document is finished and that
anybody may read it; the READ-ONLY BIND is what makes it unwritable from inside
the container, and the worker proves that for itself rather than trusting
either. `READ_ONLY_FILE` says why world-readable is the correct mode here and
why it is only safe because §13 keeps this document non-secret.

AND THE MODE IS ESTABLISHED, NOT REQUESTED. Review [P0]: a creation mode is
filtered by the process umask, so a manager running under the ordinary service
umask 077 authored a 0400 document the container's fixed uid could not read —
the positive launch regressing to the unrunnable worker this Work exists to
fix, silently, on somebody else's machine. `materialize` now sets the exact
mode on the descriptor it wrote, and creates at 0000 first so no partial
document is readable at any instant.
"""

import json
import os
import stat

from ..contracts import ContractRefusal, check_no_durable_secret
from ..contracts.errors import name_value
from . import boundaries

__all__ = ["LAUNCH_MEMBERS", "LAUNCH_SCHEMA", "LAUNCH_TARGET",
           "MAX_LAUNCH_BYTES", "MAX_LAUNCH_VALUE", "MAX_SESSION",
           "READ_ONLY_DIR", "READ_ONLY_FILE", "LaunchDelivery",
           "adopt", "launch_document", "materialize"]

# THE FIXED CONTAINER PATH, a constant of the contract at BOTH ends. A path a
# caller could vary is a path a runtime can be pointed at wrongly, so there is
# no locator environment variable and no caller-selected target -- the worker
# is told where to look by this contract, and the adapter composes exactly this
# target and refuses to compose another.
LAUNCH_TARGET = "/run/baton/launch.json"

# THE VERSION IS IN THE NAME, exactly as `baton.worker-entry/1` carries the
# channel's. A document from another generation is then refused by an equality
# test rather than by parsing a separate version member and deciding what to do
# about it -- and "what to do about it" is where a compatibility path grows.
LAUNCH_SCHEMA = "baton.worker-launch/1"

# EXACTLY FOUR, and the set is closed at both ends. The worker derives nothing
# from this tuple -- it cannot import this package, and a second copy is what
# `test_oci` holds against this one by reading the worker's own literal.
LAUNCH_MEMBERS = ("schema", "session", "contract", "role")

# The identity ceiling is the WORKER'S, deliberately. `session` is the value
# every frame on the worker-entry channel is bound to, and the worker refuses
# one wider than this -- so a value the worker would refuse is not one this
# manager may write. Writing it and letting the container fail would move a
# manager mistake inside a container, where the manager can no longer say why.
MAX_SESSION = 256

# A contract line and a role are operator PROSE, not identifiers, and a human
# contract legitimately carries newlines. The retired environment transport
# refused those because one `--env NAME=VALUE` argument cannot survive one;
# that ban is not carried forward, because it was a fact about the transport
# rather than about the value.
MAX_LAUNCH_VALUE = 4096

# The whole document, bounded so the worker's read is bounded. Comfortably
# above four members at their own ceilings and far below anything that would
# matter to a container.
MAX_LAUNCH_BYTES = 65536                       # 64 KiB

# READ-ONLY, AND READABLE BY ANYBODY. Both halves are deliberate and the
# second one is the interesting one.
#
# The container runs as the fixed non-root uid 65532 (the adapter's `--user`
# restriction and the recipe agree on it), and a bind mount carries the host
# file's ownership and mode through unchanged. So an owner-only mode would
# make delivery depend on the manager process happening to run as that uid --
# it does not, and it cannot chown its way there without privileges it must not
# have. A document the worker cannot read is a container that does not start,
# for a reason nothing in the mount table would show.
#
# That is only acceptable because of what this document IS: non-secret control
# metadata, and §13 is what keeps it that way rather than this comment --
# `launch_document` walks the authored document before any of it is written, so
# a bearer cannot arrive in a world-readable file by way of a `contract` line.
# Credentials are the opposite case and the narrow one: 0640 in the
# deployment's configured workspace group, under a 0700 manager-only root, in
# `credentials.py`, which is where secret material lives. W52800 ruled those
# group bits; `other` stays empty there, which is the whole difference from
# this document.
#
# WRITABLE BY NOBODY, including this manager after the write. The document is
# finished when it is written and nothing writes it again; the mode says so on
# disk rather than in a comment, and the READ-ONLY BIND is the separate
# statement the worker proves for itself.
READ_ONLY_FILE = 0o444
READ_ONLY_DIR = 0o555


def _refuse(message, code="schema"):
    raise ContractRefusal("integrity", code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _value(given, name, ceiling):
    """One of the three values, owned under ONE LITERAL LABEL.

    The label is a constant and the member's name is in the prose after it,
    which is the rule this package's shared owners follow -- the inventory
    attributes an owned entry by the label written at the site, so a helper
    that owned under its caller's word would be a boundary nothing could place.
    """
    value = boundaries.text(given, "a launch document value")
    if len(value) > ceiling:
        _denied(f"the launch document's {name} is wider than {ceiling} "
                f"characters")
    # `U+0000` AND NOTHING ELSE. It is the one character that truncates a value
    # on the way into a path, an argument or a C string, and JSON will happily
    # carry it. Every other character survives this document, which is the
    # point of replacing an argv-shaped transport with one.
    if "\x00" in value:
        _refuse(f"the launch document's {name} carries a NUL; a value that "
                f"truncates where it is read is not one this manager writes")
    return value


def launch_document(*, session, contract, role):
    """The complete four-member document, or a refusal.

    AUTHORED HERE RATHER THAN ASSEMBLED BY A CALLER, and rebuilt over
    `LAUNCH_MEMBERS` rather than copied from a mapping, so how a caller
    happened to build its dict cannot reach the file. A caller supplies three
    values; it does not supply a document shape.

    §13 WALKS THE RESULT. Every function in this package that produces a
    durable document walks it before it returns, and this one is durable for
    the life of a container: a live bearer arriving as a `contract` line would
    otherwise sit in a file the worker reads, which is precisely the surface
    the rule names.
    """
    document = {"schema": LAUNCH_SCHEMA,
                "session": _value(session, "session", MAX_SESSION),
                "contract": _value(contract, "contract", MAX_LAUNCH_VALUE),
                "role": _value(role, "role", MAX_LAUNCH_VALUE)}
    check_no_durable_secret(document, what="a worker launch document")
    return document


def _bytes(document):
    """The exact bytes the worker will read, bounded before they are written.

    Sorted and separator-free for the same reason every other document this
    campaign writes is: two readers that canonicalize differently do not agree
    about what was delivered. The bound is checked on the ENCODED bytes rather
    than on the members, because the worker's ceiling is a byte ceiling and a
    four-byte character is four bytes to it.
    """
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_LAUNCH_BYTES:
        _denied(f"this launch document is {len(payload)} bytes and the worker "
                f"reads at most {MAX_LAUNCH_BYTES}; a document the worker "
                f"would refuse is not one this manager writes")
    return payload


def _write_whole(handle, payload):
    """Every byte, or a refusal. `os.write` is allowed to write fewer.

    The same rule `credentials._write_whole` states, for the same reason: a
    short write is ordinary rather than exotic, it is not an error the call
    reports, and a TRUNCATED launch document is one the worker refuses as
    malformed while this manager believes it delivered a whole one. No
    progress twice is a refusal rather than a spin.
    """
    written = 0
    while written < len(payload):
        step = os.write(handle, payload[written:])
        if type(step) is not int or step <= 0:
            _refuse(f"writing the launch document made no progress after "
                    f"{written} of {len(payload)} bytes; a partly written "
                    f"document is one the worker refuses and this manager "
                    f"believes it delivered")
        written += step
    return written


class LaunchDelivery:
    """The TYPED capability the adapter receives, and the only one.

    The adapter is handed this object rather than a path, a mapping or a mount
    plan. A path operand would be a caller-selected locator -- the thing the
    fixed target exists to take away -- and a mapping would be the environment
    channel this Work replaced, wearing a different name. What the adapter can
    do with this is ask for one mount, and the target of that mount is this
    contract's constant rather than anything it was told.
    """

    def __init__(self, *, attempt_id, root, place, document):
        self.attempt_id = attempt_id
        self.root = root
        self.place = place
        self.document = document

    def mount(self):
        """The ONE read-only bind this delivery authorizes.

        A pair rather than a mount document: `readonly` is not a parameter
        here, and a delivery that could ask to be writable would be a launch
        document the worker could rewrite between reading and being asked
        about it.
        """
        return (self.place, LAUNCH_TARGET)


def materialize(storage, *, attempt_id, session, contract, role):
    """Author one launch document and put it on disk as this manager's own.

    `storage` is the manager's own launch storage, NOT an assignment root. The
    document is not assignment material: mounting it out of `inputs` would make
    it something the input digest describes, and mounting it out of `workspace`
    would put the worker's own launch contract inside the one tree the worker
    may WRITE -- so a worker could rewrite the document that says what it is.
    A separate manager-owned root is the same separation `credentials` draws
    for the same reason, and it is drawn here rather than argued.

    AN EXISTING ROOT IS A REFUSAL, not a place to write into. It is a live
    delivery or an orphan, and either way replacing bytes this manager cannot
    account for is how one attempt's container reads another attempt's launch
    contract.
    """
    attempt = boundaries.identity(attempt_id, "a launch attempt id")
    home = boundaries.text(storage, "the manager's launch storage")
    if not os.path.isabs(home):
        _refuse(f"the manager's launch storage is not an absolute path; a "
                f"root this build cannot name exactly is not a root",
                code="path")
    document = launch_document(session=session, contract=contract, role=role)
    payload = _bytes(document)
    root = os.path.join(os.path.realpath(home), attempt)
    if os.path.lexists(root):
        raise ContractRefusal(
            "refused", "precondition",
            f"a launch root already exists for attempt {name_value(attempt)}; "
            f"an existing root is a live delivery or an orphan, and writing "
            f"into either would replace bytes this manager cannot account for")
    place = os.path.join(root, os.path.basename(LAUNCH_TARGET))
    # 0700 WHILE IT IS BEING BUILT, and read-only-for-everybody only once the
    # document is whole. A half-written document nobody can see is a delivery
    # that failed; a half-written document a container could read is one it
    # would refuse in a way that looks like a manager bug.
    os.makedirs(root, mode=0o700, exist_ok=False)
    try:
        # EXCLUSIVE CREATION, NO-FOLLOW, AND CREATED UNREADABLE. `O_EXCL` so
        # nothing already at this name is written through, `O_NOFOLLOW` so a
        # link left there is refused rather than followed, and mode 0 so the
        # file is never WRITABLE and never readable while it is still partial.
        #
        # Review [P0]: this passed `READ_ONLY_FILE` as the creation mode and
        # stopped there. A creation mode is FILTERED BY THE UMASK, so a manager
        # under the ordinary service umask 077 authored 0400 — a document the
        # container's fixed uid 65532 cannot read, which is the unrunnable
        # worker this Work exists to fix, arriving silently and only on a host
        # with a restrictive umask. `os.chmod` on the ROOT was always exact and
        # was never affected; only the file was.
        #
        # `fchmod` ON THE DESCRIPTOR THIS FUNCTION WROTE, not a second `chmod`
        # by name: the name could be something else by then, and the descriptor
        # cannot be. It runs after the last byte, so the document becomes
        # readable exactly when it becomes complete, and there is still no
        # instant at which anything could open it for writing.
        handle = os.open(place,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o000)
        try:
            _write_whole(handle, payload)
            os.fchmod(handle, READ_ONLY_FILE)
        finally:
            os.close(handle)
        os.chmod(root, READ_ONLY_DIR)
    except BaseException:
        # A FAILED MATERIALIZATION TEARS ITSELF DOWN. Half a delivery is a root
        # holding a partial document that nothing is going to remove, and the
        # ending that would have removed it never starts, because the attempt
        # never launched.
        discard(root)
        raise
    return LaunchDelivery(attempt_id=attempt, root=root, place=place,
                          document=document)


def adopt(storage, *, attempt_id, session, contract, role):
    """Recover the delivery THIS MANAGER already made, or FAIL CLOSED.

    W47225. `materialize` refuses an existing root and `discard` removes one,
    so a restarted process had no way to hold a delivery it had already made
    -- and W39358's narrow handoff retry, which runs in a FRESH process after
    the original exited, reconstructed its cleanup adapter with
    `launch_delivery=None`. `authorize_cleanup` could then remove the runtime
    while `_launch_ended` reported `not-delivered`, and the launch root the
    ordinary attempt materialized was left on disk with nothing that would
    ever come back for it.

    WHAT PROVES THE DELIVERY IS THE BYTES, and review 2026-08-30T15:05:35Z
    [P0] is why nothing weaker will do. Holding the document to its member
    NAMES and schema proves only that it is *a* launch document: a valid
    four-member document copied out of another attempt's root passed every
    one of those checks and came back as this attempt's delivery. Member
    values were not held either, so an integer `session` -- which
    `materialize` refuses before writing -- was adopted after the fact.

    So adoption AUTHORS what this component would have written, through the
    same `launch_document` and `_bytes` owners that wrote it, and requires the
    canonical bytes to match exactly. That one comparison closes identity and
    value drift together, and it reuses the authoring rules rather than
    copying them -- including the whole-document secret check, which a
    re-implementation here would have quietly dropped.

    AND THE ROOT IS HELD TO THE ONE ENTRY `materialize` CREATES. `discard`
    removes every name in the root it is given, so a sibling entry accepted
    here is a foreign file this component would later delete. [P0] again, and
    it is the difference between recovering a delivery and adopting a
    directory.

    EVERY PROOF IS DESCRIPTOR-RELATIVE AND NO-FOLLOW. [P1]: checking with
    `islink`/`isfile`, mode-checking with `lstat` and then reopening by name
    is three lookups of a path that can change between them, so the bytes
    could arrive through a link the earlier checks never inspected. The root
    is opened once with `O_NOFOLLOW|O_DIRECTORY`, the document is opened
    relative to THAT descriptor with `O_NOFOLLOW`, and the type, mode and
    bytes all come from the descriptor that is already open.

    ABSENT ADOPTS NOTHING, and that is an ordinary answer: an attempt may have
    had no launch delivery, and `None` is what lets a caller tell that apart
    from a delivery it failed to prove. A caller for whom absence is
    contradictory -- one whose attempt demonstrably started a runtime -- is
    the caller that must refuse, and this component does not decide that for
    it.
    """
    attempt = boundaries.identity(attempt_id, "a launch attempt id")
    home = boundaries.text(storage, "the manager's launch storage")
    if not os.path.isabs(home):
        _refuse(f"the manager's launch storage is not an absolute path; a "
                f"root this build cannot name exactly is not a root",
                code="path")
    # AUTHORED FIRST, through the owner that writes it. A document this
    # component would refuse to WRITE is one it must refuse to adopt, and
    # deriving the expectation before touching the disk is what makes the
    # comparison below a comparison rather than a second rule set.
    expected = _bytes(launch_document(session=session, contract=contract,
                                      role=role))
    root = os.path.join(os.path.realpath(home), attempt)
    if not os.path.lexists(root):
        return None
    name = os.path.basename(LAUNCH_TARGET)
    try:
        opened = os.open(root, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _denied(f"the launch root for attempt {name_value(attempt)} is not a "
                f"directory this manager made ({type(failure).__name__}); an "
                f"entry of another type is state this build cannot account "
                f"for")
    try:
        held = os.stat(opened)
        if stat.S_IMODE(held.st_mode) != READ_ONLY_DIR:
            _denied(f"attempt {name_value(attempt)}'s launch root is mode "
                    f"{oct(stat.S_IMODE(held.st_mode))} and this manager "
                    f"established {oct(READ_ONLY_DIR)}; a delivery whose "
                    f"modes have moved is not the one it wrote")
        # EXACTLY THE ONE ENTRY, because `discard` deletes every name here.
        entries = sorted(os.listdir(opened))
        if entries != [name]:
            _denied(f"attempt {name_value(attempt)}'s launch root holds "
                    f"{entries!r} and this manager creates exactly "
                    f"{[name]!r}; adopting a widened root would authorize "
                    f"deleting an entry this component never wrote")
        try:
            document = os.open(name, os.O_RDONLY | os.O_NOFOLLOW,
                               dir_fd=opened)
        except OSError as failure:
            _denied(f"attempt {name_value(attempt)}'s launch document could "
                    f"not be opened as this manager wrote it "
                    f"({type(failure).__name__})")
        try:
            found = os.stat(document)
            if not stat.S_ISREG(found.st_mode):
                _denied(f"attempt {name_value(attempt)}'s launch document is "
                        f"not a regular file")
            if stat.S_IMODE(found.st_mode) != READ_ONLY_FILE:
                _denied(f"attempt {name_value(attempt)}'s launch document is "
                        f"mode {oct(stat.S_IMODE(found.st_mode))} and this "
                        f"manager established {oct(READ_ONLY_FILE)}; a "
                        f"writable launch document is one the worker could "
                        f"rewrite between being given it and being asked "
                        f"about it")
            raw = os.read(document, MAX_LAUNCH_BYTES + 1)
        finally:
            os.close(document)
    finally:
        os.close(opened)
    # THE ONE COMPARISON, and it is exact. Canonical bytes, so a document that
    # merely MEANS the same thing in a different spelling is not this
    # delivery's document either -- `_bytes` is what wrote it and there is
    # only one serialization of a given launch document.
    if raw != expected:
        _denied(f"attempt {name_value(attempt)}'s launch document is not the "
                f"one this manager would have written for it; a document that "
                f"is merely well formed proves which KIND of thing it is and "
                f"not which delivery")
    place = os.path.join(root, name)
    return LaunchDelivery(attempt_id=attempt, root=root, place=place,
                          document=launch_document(session=session,
                                                   contract=contract,
                                                   role=role))


def discard(root):
    """Remove one launch root WITHOUT reading anything in it.

    Answers whether it is gone. Removal is by name inside a directory this
    module created, never by walking something a worker could have replaced --
    the document is read-only and the root is the manager's, so there is
    nothing here to discover.
    """
    if not os.path.isdir(root):
        return not os.path.lexists(root)
    os.chmod(root, 0o700)
    for name in sorted(os.listdir(root)):
        try:
            os.remove(os.path.join(root, name))
        except OSError:
            pass
    try:
        os.rmdir(root)
    except OSError:
        pass
    return not os.path.lexists(root)
