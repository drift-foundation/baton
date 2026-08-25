"""THE CONSTRAINED OCI ADAPTER CORE: closed argv, typed observations.

W6632 (`work/records/2026/08/finding-v12-oci-adapter-core`), the second bounded
child of W5. Runtime-neutral across Docker and compatible Podman.

THE ONE SENTENCE THIS MODULE IS BUILT AROUND: **the engine reports facts; it
never decides assignment authority, settlement or retry.** Everything below
follows from taking that literally.

  * NO SHELL, EVER. Every invocation is a closed argument VECTOR handed to a
    process capability. There is no string to quote, so there is nothing for an
    image name, a label value or a mount path to escape out of -- the class of
    defect this module cannot have rather than the class it guards against.
  * ABSENCE IS PROVED, NOT INFERRED. An empty listing, a stop acknowledgement
    and engine prose are three different things and none of them is death. A
    runtime is `absent` only when the engine is asked about that exact identity
    and answers that it does not exist; anything else is `uncertain`, which is
    the answer the manager can act on safely.
  * EXACT IDENTITY. A listing that matches several runtimes for one assignment
    is ambiguous and fails closed. A stale identity -- one whose labels are not
    this assignment's -- is refused rather than filtered away, because it is not
    absent, it is WRONG, and dropping it leaves a mislabelled runtime running.
  * THE RESTRICTIONS ARE UNCONDITIONAL. Every capability dropped, privilege
    escalation denied, no nested runtime or engine socket, a fixed non-root
    user, and read-only root with the workspace as the one writable mount. They
    are not options a caller may relax: a policy that a caller can turn off is a
    default.
  * LABELS CARRY NO SECRET. Reconciliation needs to find a runtime again after
    a restart, so the labels are exactly the frozen `runtime.labels` document --
    identities and digests, which are already public facts about an assignment.
    A bearer, a token or a credential in a label would be readable by anything
    that can list containers.

WHAT IS DELIBERATELY NOT HERE, because the assignment says so: source
materialization, provider code, output acceptance, credential delivery and
manager lifecycle orchestration. This module is called BY `attempts.py` through
the `start`/`list`/`stop` seam that already exists; it does not call back.

THE ENGINE IS INJECTED. `EnginePort` types the one thing this core does to the
world -- run a closed argv and hand back exit status, stdout and stderr -- so
the vectors and the parsing are provable without this package deciding how a
process is spawned. The isolated smoke test that drives a real engine is named
in the record as its own cut, for the same reason the acceptance names it
separately: it is a mutable test of somebody else's daemon.
"""

import json
import os
import re

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries, documents

__all__ = ["ENGINES", "EnginePort", "LABEL_PREFIX", "MAX_DIAGNOSTIC",
           "POSTURES", "ROOT_NAMES", "MOUNTABLE", "RESOLVED_IDENTITY",
           "RESTRICTIONS", "OciAdapter", "destroy_vector", "inspect_vector",
           "list_vector", "run_vector", "stop_vector"]

# The two engines this core speaks, and nothing else. A name outside this set is
# refused rather than passed to a process: "docker" and "podman" are the two
# whose argv this module was written against, and an engine that merely accepts
# the same flags is not the same evidence.
ENGINES = ("docker", "podman")

# The frozen `digest` pattern, applied to an image reference.
_IMAGE = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
# The frozen `digest` pattern, for every label that carries one.
_DIGEST = _IMAGE

# Every label this adapter writes carries this prefix, so a runtime this manager
# owns is distinguishable from every other container on the host WITHOUT reading
# its contents.
LABEL_PREFIX = "baton.v12."

# How much engine prose ever reaches a refusal. Engine stderr is unbounded
# caller-controlled text and a refusal is the thing most likely to be logged --
# the same rule W1593 established for every other diagnostic in this manager.
MAX_DIAGNOSTIC = 240

# §policy: the restrictions, as ONE table rather than as flags spread through a
# builder. Written out so a reader can see the whole posture at once and a
# reviewer can diff it, and applied unconditionally.
RESTRICTIONS = (
    # No capability at all, and no way to acquire one back.
    ("--cap-drop", "ALL"),
    ("--security-opt", "no-new-privileges"),
    # A worker is not a runtime host. Without this, a compromised worker starts
    # its own containers with whatever posture it likes.
    ("--security-opt", "label=disable"),
    # A fixed non-root user. Root inside a user namespace is still root against
    # anything the namespace does not cover.
    ("--user", "65532:65532"),
    # The root filesystem is evidence, not scratch: the workspace mount is the
    # one writable place, and it is named per assignment.
    ("--read-only", None),
    ("--network", "none"),
    ("--pids-limit", "512"),
    ("--memory", "2g"),
    ("--cpus", "2"),
    # `/tmp` and `/dev/shm` exist because ordinary tools need them, and both are
    # small, private and non-executable.
    ("--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m"),
    ("--tmpfs", "/dev/shm:rw,noexec,nosuid,nodev,size=16m"),
)

# THE POSTURE'S OWN ROOTS. Ruled 2026-08-25, and it replaces a denylist.
#
# A denylist answers "is this one of the bad ones" when the rule is "is this
# one of OURS" -- so a repository path that happened not to match a listed
# prefix was mountable, and every new spelling needed a new entry. Proof
# against the assignment's own roots inverts that: a source is admitted only
# because this manager created the root it lives under.
#
# ROOTS ALONE CANNOT CHOOSE THE TOPOLOGY, which is why the posture is a
# separate required input. Consent mounts NOTHING -- it has no assignment, no
# workspace and no output, and a consent container that could see the inputs
# would be the promotion the two-container topology exists to prevent.
# Execution may see `inputs` read-only and `workspace` read/write.
#
# The private `git` root is never mounted at either posture: it is the
# manager's own metadata, and a worker that could reach it could move another
# assignment's refs.
POSTURES = ("consent", "execution")
ROOT_NAMES = ("inputs", "workspace", "git")
MOUNTABLE = {"consent": (), "execution": ("inputs", "workspace")}
WRITABLE = {"execution": ("workspace",)}


# THE ONE RESOLVED IDENTITY a delivery is made under. Review: the adapter
# held `image_digest` and `start` accepted labels independently, so what was
# STARTED and what the runtime was LABELLED with were two accounts nothing
# compared. Reconciliation after a restart finds a runtime by those labels and
# then reasons about it as though they described the image that is running.
#
# One record, owned at construction, is what makes the two accounts one: the
# image reaches the argv from it, the profile and adapter digests reach the
# labels from it, and a request whose labels disagree is refused rather than
# started.
RESOLVED_IDENTITY = ("image_digest", "profile_digest", "adapter_digest")


def _identity(identity):
    """The resolved identity, exactly and by digest."""
    taken = boundaries.document(identity, "a resolved runtime identity",
                                required=RESOLVED_IDENTITY)
    for name in RESOLVED_IDENTITY:
        value = boundaries.text(taken[name], "a resolved identity digest")
        if not _DIGEST.match(value):
            _refuse(f"the resolved {name} is {name_value(value)}, which is "
                    f"not a sha256 digest; a delivery is made under an "
                    f"identity this manager can name exactly", code="digest")
    return taken


def _refuse(message, code="schema"):
    raise ContractRefusal("integrity", code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


class EnginePort:
    """The ONE thing this core does to the world: run a closed argv.

    Typed at construction for the reason every capability in this package is:
    discovering that an injected operation is missing halfway through a start
    is discovering it after something has already happened.
    """

    def __init__(self, run):
        self._run = boundaries.capability(run, "the engine's run operation")

    def __call__(self, argv):
        """Answer `(status, stdout, stderr)` for one closed vector."""
        answer = self._run(argv)
        taken = boundaries.document(answer, "the engine's answer",
                                    required=("status", "stdout", "stderr"))
        if type(taken["status"]) is not int or type(taken["status"]) is bool:
            _refuse(f"the engine's exit status is a number; this is "
                    f"{name_value(taken['status'])}")
        for stream in ("stdout", "stderr"):
            _stream(taken[stream], f"the engine's {stream}")
        return taken


# What an engine accepts as a container name. Docker and Podman both take
# `[a-zA-Z0-9][a-zA-Z0-9_.-]*`, and the manager's real operation identity --
# `runtime.start:<digest>` -- carries a colon, which is not in it.
_NAME_SAFE = re.compile(r"[^a-zA-Z0-9_.-]")


def _runtime_name(operation_id):
    """An engine-valid name DERIVED from the manager's operation identity.

    Review [P1]: this interpolated the identity directly, producing
    `baton-runtime.start:<digest>` -- a name no engine accepts, so every start
    would have failed at the daemon. The fix is a DERIVATION and never a
    rewrite of the identity itself: the manager's `runtime.start:<digest>` is
    what the journal, the retry and the reconciliation all name, and weakening
    it to suit a container runtime would let the engine's alphabet decide what
    an operation is.

    The substitution is total rather than a strip, so two identities that
    differ only in characters an engine forbids cannot collapse to one name --
    and the digest that follows the prefix is what makes it unique anyway.
    """
    return "baton-" + _NAME_SAFE.sub("-", operation_id)


def _stream(value, what):
    """Engine output: text that MAY BE EMPTY, and must be storable.

    Not `boundaries.text`, deliberately. That rule is for a durable operand and
    refuses the empty string, which is exactly what a quiet engine writes --
    "nothing on stderr" is the ordinary case and would otherwise be a fault.
    What still has to hold is that the text can be stored and put in a message,
    because a refusal quoting it is a durable value like any other.
    """
    if type(value) is not str:
        _refuse(f"{what} is text; this is {name_value(value)}")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        _refuse(f"{what} carries text that is not encodable; an engine answer "
                f"this build cannot store is not one it can report")
    return value


# -- the closed vectors -------------------------------------------------------


def _engine(engine):
    boundaries.text(engine, "an engine name")
    if engine not in ENGINES:
        _refuse(f"{name_value(engine)} is not an engine this adapter speaks; "
                f"it speaks {', '.join(ENGINES)}")
    return engine


def _labels(labels):
    """The frozen `runtime.labels` document, and NOTHING ELSE.

    Exactly the contract's member set: a label this adapter invented would be
    one reconciliation could not rely on after a restart, and a label a caller
    supplied would be a place to put something that should not be readable by
    anything that can list containers.
    """
    taken = boundaries.document(labels, "a runtime's labels",
                                required=documents.RUNTIME_LABELS)
    # EVERY MEMBER BY ITS OWN SEMANTIC RULE, on the way out as well as on the
    # way back. Review [P1]: a digest label reading `profile-latest` and a
    # generation of `-1` were both written to a runtime and later reconciled
    # against. The adapter RECONCILES on these values, so a text-shaped
    # substitute is not the exact profile, adapter or assignment generation --
    # and the same rule that reads them back is the one that writes them.
    for name in documents.RUNTIME_LABELS:
        value = _label_value(name, taken[name])
        if type(value) is str and ("\n" in value or "\r" in value):
            _refuse(f"the {name} label carries a line break, which no engine "
                    f"can report back unambiguously")
    return taken


def _label_pairs(labels):
    """`--label` arguments, in the CONTRACT'S OWN member order.

    Deterministic order matters: a golden argv vector that depended on dict
    iteration would be a vector that passed for the wrong reason.
    """
    return [(f"{LABEL_PREFIX}{name}", str(labels[name]))
            for name in documents.RUNTIME_LABELS]


def _canonical(place, what):
    """One host path, as the KERNEL would resolve it.

    Review [P1]: containment was decided with `os.path.normpath`, which is a
    string operation. A symlink planted under the writable workspace and
    pointing anywhere at all therefore passed the lexical test, and the closed
    argv handed the engine the symlink spelling -- which the engine then
    resolved against foreign host state. Lexical containment is not mount
    authority, because the party that resolves the path is not this one.

    `realpath` on a path that does not exist yet returns it unchanged, so a
    root the manager has not created yet is still nameable; what it removes is
    the case where something DOES exist and is not what its spelling says.

    The `..` check runs on the SPELLING, before resolution collapses it: a
    caller writing `..` is asking this adapter to compute a path rather than
    name one, and refusing that is cheaper than proving where it landed.
    """
    # A LITERAL LABEL at the owner. The inventory attributes an owned entry by
    # the label written at the site, so a computed one is a boundary it cannot
    # place -- the same correction `certified_agent_session_profile` was made
    # for. `what` still names the caller's own noun in the refusals below,
    # where it says WHICH path disagreed rather than what the rule is called.
    text = boundaries.text(place, "a host path")
    if not text.startswith("/"):
        _refuse(f"{what} is {name_value(text)}, which is not an absolute "
                f"path; the engine would resolve it somewhere this manager "
                f"did not choose", code="path")
    if ".." in text.split("/"):
        _refuse(f"{what} traverses with `..`; a canonical path is what this "
                f"adapter mounts", code="path")
    if ":" in text:
        _refuse(f"{what} carries a colon, which is the engine's own "
                f"separator", code="path")
    return os.path.realpath(text)


def _roots(assignment_roots, posture):
    """The assignment's own roots, and the posture that decides which apply."""
    boundaries.text(posture, "a worker posture")
    if posture not in POSTURES:
        _refuse(f"{name_value(posture)} is not a worker posture; it is one of "
                f"{', '.join(POSTURES)}")
    taken = boundaries.document(assignment_roots, "the assignment's roots",
                                required=ROOT_NAMES)
    real = {name: _canonical(taken[name], f"the {name} root")
            for name in ROOT_NAMES}
    # NO ROOT CONTAINS ANOTHER. Review: with `workspace` beneath `inputs`, a
    # source inside both has no unique posture authority -- `_mounts` would
    # classify it by whichever root matched first, and whether it may be
    # WRITTEN would depend on that order. Ambiguity about writability is not a
    # thing this adapter may resolve by iteration order.
    for name, place in real.items():
        for other, elsewhere in real.items():
            if other != name and _within(place, elsewhere):
                _refuse(f"the {name} root {name_value(place)} lies inside the "
                        f"{other} root {name_value(elsewhere)}; a source "
                        f"inside two roots has no unique posture authority",
                        code="path")
    return real, posture


def _within(child, parent):
    """Strictly inside, or the root itself -- and never merely sharing a
    prefix, because `/srv/work-2` starts with `/srv/work` and is not in it."""
    return child == parent or child.startswith(parent.rstrip("/") + "/")


def _mounts(mounts, roots, posture):
    """Canonical, absolute, non-overlapping mount sources.

    A mount is how the manager's own material reaches a worker, so this is the
    boundary where "the workspace" and "the authority's database" are told
    apart. Relative sources, forbidden system paths and duplicate targets all
    refuse.
    """
    taken = []
    seen = set()
    permitted = MOUNTABLE[posture]
    if mounts and not permitted:
        _denied(f"a {posture} container mounts nothing; it has no assignment, "
                f"no workspace and no output, and one that could see the "
                f"inputs would be the promotion the two-container topology "
                f"exists to prevent")
    for mount in mounts:
        one = boundaries.document(mount, "a runtime mount",
                                  required=("source", "target", "writable"))
        # THE SOURCE IS RESOLVED; THE TARGET IS NOT. A source is a HOST path
        # and the engine will resolve it, so this adapter proves the thing the
        # engine will act on. A target is a path INSIDE a container that does
        # not exist yet, and resolving it against this host would be resolving
        # somebody else's filesystem.
        source = _canonical(one["source"], "a mount source")
        target = os.path.normpath(
            boundaries.text(one["target"], "a mount target"))
        if not target.startswith("/"):
            _refuse(f"a mount target is {name_value(target)}, which is not an "
                    f"absolute path", code="path")
        if ".." in target.split("/") or ":" in target:
            _refuse(f"a mount target is not canonical; `..` and the engine's "
                    f"own `:` separator are both refused", code="path")
        # PROVED TO BE OURS, rather than proved not to be one of theirs.
        under = [name for name in permitted if _within(source, roots[name])]
        if not under:
            _denied(f"a mount names {name_value(source)}, which is not this "
                    f"assignment's material; a {posture} container may mount "
                    f"only {', '.join(permitted)} or a descendant of one")
        if type(one["writable"]) is not bool:
            _refuse(f"a mount says it is writable {name_value(one['writable'])}"
                    f"; that is a yes or a no")
        if one["writable"] and under[0] not in WRITABLE.get(posture, ()):
            _denied(f"a mount asks to write {name_value(source)}; a "
                    f"{posture} container writes only under its workspace, "
                    f"and delivered inputs are evidence rather than scratch")
        if target in seen:
            _refuse(f"two mounts land on {name_value(target)}; the second "
                    f"would hide the first")
        # NEITHER SIDE MAY CONTAIN THE OTHER. Equal targets hide; NESTED ones
        # alias -- the inner mount shadows part of the outer, and which of the
        # two a path inside the container reaches depends on the engine's own
        # ordering rather than on anything this manager decided. Nested
        # SOURCES are the same question on the host: one mount would expose a
        # subtree of another under a second name and a possibly different
        # writability.
        for before_source, before_target, _writable in taken:
            if _within(source, before_source) or _within(before_source, source):
                _refuse(f"mount sources {name_value(before_source)} and "
                        f"{name_value(source)} contain one another; one mount "
                        f"would expose a subtree of the other under a second "
                        f"name", code="path")
            if _within(target, before_target) or _within(before_target, target):
                _refuse(f"mount targets {name_value(before_target)} and "
                        f"{name_value(target)} contain one another; the inner "
                        f"one would shadow part of the outer", code="path")
        seen.add(target)
        taken.append((source, target, one["writable"]))
    return taken


def run_vector(engine, *, image_digest, labels, assignment_roots, posture,
               mounts=(), name):
    """The closed argv that STARTS one runtime, restrictions and all.

    The image is named BY DIGEST. A tag is a name somebody can move, and a
    runtime started from a moved tag is a runtime nobody can say the contents
    of afterwards -- which makes every digest the assignment records a
    description of something else.
    """
    engine = _engine(engine)
    boundaries.text(image_digest, "an image digest")
    # LOWER-CASE HEX, and the length alone was not enough: an upper-case
    # digest is the same 71 characters and a different string, so two spellings
    # of one image would be two images to every comparison downstream.
    if not _IMAGE.match(image_digest):
        _refuse(f"{name_value(image_digest)} is not a sha256 image digest; a "
                f"runtime is started from an image this manager can name "
                f"exactly", code="digest")
    boundaries.identity(name, "a runtime name")
    argv = [engine, "run", "--detach", "--name", name]
    for flag, value in RESTRICTIONS:
        argv.append(flag)
        if value is not None:
            argv.append(value)
    for key, value in _label_pairs(_labels(labels)):
        argv += ["--label", f"{key}={value}"]
    roots, posture = _roots(assignment_roots, posture)
    for source, target, writable in _mounts(mounts, roots, posture):
        argv += ["--mount",
                 f"type=bind,source={source},target={target},"
                 f"readonly={'false' if writable else 'true'}"]
    # THE IMAGE, LAST and by digest. Every flag precedes it, so nothing a
    # caller supplies can be read as an argument to the engine itself.
    argv.append(image_digest)
    return argv


def list_vector(engine, *, labels):
    """Ask the engine which runtimes carry EXACTLY this assignment's labels."""
    engine = _engine(engine)
    argv = [engine, "ps", "--all", "--no-trunc", "--format", "{{json .}}"]
    for key, value in _label_pairs(_labels(labels)):
        argv += ["--filter", f"label={key}={value}"]
    return argv


def inspect_vector(engine, *, runtime_id):
    engine = _engine(engine)
    boundaries.identity(runtime_id, "a runtime id")
    return [engine, "inspect", "--type", "container", "--format", "{{json .}}",
            runtime_id]


def stop_vector(engine, *, runtime_id, seconds=30):
    engine = _engine(engine)
    boundaries.identity(runtime_id, "a runtime id")
    if type(seconds) is not int or type(seconds) is bool or not 0 < seconds:
        _refuse(f"a stop timeout is a positive whole number of seconds; this "
                f"is {name_value(seconds)}")
    return [engine, "stop", "--time", str(seconds), runtime_id]


def destroy_vector(engine, *, runtime_id):
    engine = _engine(engine)
    boundaries.identity(runtime_id, "a runtime id")
    return [engine, "rm", "--force", "--volumes", runtime_id]


# -- reading what the engine said ---------------------------------------------


# The engines' own exact absence sentences, pinned rather than matched
# loosely. Docker says `No such container: <id>` and `No such object: <id>`;
# Podman says `no such container <id>` and `no container with name or ID <id>`.
# Every one NAMES the identity, which is what makes the answer positive.
_ABSENT = ("no such container", "no such object",
           "no container with name or id")


def _absent_prose(stderr, runtime_id):
    """True only when the engine says THIS identity does not exist."""
    prose = (stderr or "").lower()
    if runtime_id.lower() not in prose:
        return False
    return any(sentence in prose for sentence in _ABSENT)


def _decoded(payload, what):
    """One JSON document from engine stdout, owned as text before it is parsed.

    Engine output is a caller input: a build that printed a warning first, a
    daemon that answered nothing, and a version that emitted a different shape
    are all ordinary, and none of them may become a fault escaping this layer.
    """
    # A literal label at the owner; `what` names which document the prose is
    # about, which is a message concern rather than the rule's identity.
    boundaries.text(payload, "an engine document")
    try:
        return json.loads(payload)
    except ValueError:
        _refuse(f"{what} is not the JSON document this adapter asked for: "
                f"{name_value(payload[:MAX_DIAGNOSTIC])}")


def _one_of(document, names, what):
    """The first member present, across the two engines' spellings.

    Docker and Podman answer the same facts under different keys, and the
    adapter is runtime-NEUTRAL: one vocabulary for the manager, two spellings
    read here, and an answer carrying neither refuses rather than defaulting.
    """
    for name in names:
        if type(document) is dict and name in document:
            return document[name]
    _refuse(f"{what} carries none of {', '.join(names)}; this adapter reads "
            f"the engines it speaks and guesses at nothing")


class OciAdapter:
    """The `start`/`list`/`stop` seam `attempts.py` already calls.

    Everything it answers is a FACT ABOUT THE ENGINE and nothing it answers is
    a decision: the manager reconciles, and this reports.
    """

    def __init__(self, engine, run, *, identity, assignment_roots,
                 posture, mounts=()):
        self.engine = _engine(engine)
        self.run = run if isinstance(run, EnginePort) else EnginePort(run)
        # ONE RESOLVED IDENTITY, owned at construction and never re-supplied
        # per request. It is what the argv names and what the labels must
        # agree with, so the started image and the reconciliation labels are
        # one account rather than two.
        self.identity = _identity(identity)
        self.image_digest = self.identity["image_digest"]
        # Owned at CONSTRUCTION, so an adapter that cannot say what its
        # assignment owns never reaches a delivery -- and the RESOLVED roots
        # are kept, so what was proved is what is later mounted.
        self.assignment_roots, self.posture = _roots(assignment_roots, posture)
        self.mounts = tuple(mounts)

    # -- the seam ------------------------------------------------------------

    def start(self, request):
        """Start one runtime and answer WHAT WAS STARTED, not that it worked.

        A duplicate start fails closed: the engine is asked what already
        carries these labels BEFORE anything is created, because two runtimes
        for one assignment is the state no later reconciliation can undo.
        """
        taken = boundaries.document(request, "a start request",
                                    required=("labels", "operation_id"))
        labels = _labels(taken["labels"])
        boundaries.identity(taken["operation_id"], "an operation identity")
        # THE LABELS MUST BE THIS ADAPTER'S OWN IDENTITY. A runtime labelled
        # with a profile or adapter digest other than the one it is started
        # under is a runtime reconciliation would describe wrongly for the
        # rest of its life -- and the manager would be reading that
        # description rather than the image.
        for name in ("profile_digest", "adapter_digest"):
            if labels[name] != self.identity[name]:
                _denied(f"this start labels the runtime "
                        f"{name_value(labels[name])} for {name} and the "
                        f"resolved identity is "
                        f"{name_value(self.identity[name])}; one delivery "
                        f"carries one identity, and a label that disagrees "
                        f"with what is started is what reconciliation would "
                        f"believe afterwards")
        existing = self.list({"labels": labels})
        if existing:
            _denied(f"{len(existing)} runtime(s) already carry these "
                    f"assignment labels; starting another would compound it")
        name = _runtime_name(taken["operation_id"])
        answer = self.run(run_vector(
            self.engine, image_digest=self.image_digest, labels=labels,
            assignment_roots=self.assignment_roots, posture=self.posture,
            mounts=self.mounts, name=name))
        if answer["status"] != 0:
            _denied(f"the engine refused to start this runtime: "
                    f"{name_value(answer['stderr'][:MAX_DIAGNOSTIC])}")
        runtime_id = answer["stdout"].strip()
        if not runtime_id:
            # THE ENGINE SAID NOTHING. That is not "started something unnamed";
            # it is an answer this adapter cannot turn into an identity, and
            # inventing one would make every later comparison meaningless.
            return {"runtime_id": None, "labels": None}
        boundaries.identity(runtime_id, "a started runtime id")
        return {"runtime_id": runtime_id, "labels": labels}

    def list(self, request):
        """Every runtime carrying EXACTLY these labels, each one typed."""
        taken = boundaries.document(request, "a list request",
                                    required=("labels",))
        labels = _labels(taken["labels"])
        answer = self.run(list_vector(self.engine, labels=labels))
        if answer["status"] != 0:
            _denied(f"the engine could not list runtimes: "
                    f"{name_value(answer['stderr'][:MAX_DIAGNOSTIC])}")
        found = []
        for line in answer["stdout"].splitlines():
            if not line.strip():
                continue
            entry = _decoded(line, "an engine listing entry")
            if type(entry) is not dict:
                _refuse(f"an engine listing entry is one record; this is "
                        f"{name_value(entry)}")
            runtime_id = _one_of(entry, ("ID", "Id", "ContainerID"),
                                 "an engine listing entry")
            boundaries.identity(runtime_id, "a listed runtime id")
            found.append({"runtime_id": runtime_id,
                          "labels": self._labels_of(entry)})
        return found

    def stop(self, request):
        """Order a stop, then PROVE what became of the runtime.

        A stop acknowledgement is the engine saying it accepted an order. What
        the manager needs is what is true afterwards, so this inspects the exact
        identity and answers `quiescent`, `running`, `absent` or `uncertain` --
        and `uncertain` is the honest answer whenever the engine's account does
        not settle the question.
        """
        taken = boundaries.document(request, "a stop request",
                                    required=("runtime_id", "operation_id"))
        runtime_id = boundaries.identity(taken["runtime_id"], "a runtime id")
        boundaries.identity(taken["operation_id"], "an operation identity")
        ordered = self.run(stop_vector(self.engine, runtime_id=runtime_id))
        observed = self.observe(runtime_id)
        return {"runtime_id": runtime_id,
                "ordered": ordered["status"] == 0,
                "state": observed["state"],
                "why": observed["why"]}

    def destroy(self, runtime_id):
        """Remove one runtime and PROVE it is gone."""
        runtime_id = boundaries.identity(runtime_id, "a runtime id")
        self.run(destroy_vector(self.engine, runtime_id=runtime_id))
        observed = self.observe(runtime_id)
        return {"runtime_id": runtime_id, "state": observed["state"],
                "why": observed["why"]}

    def observe(self, runtime_id):
        """POSITIVE ABSENCE, or an honest `uncertain`.

        An empty listing is not death: it is one question answered about a
        filter. This asks the engine about THIS EXACT IDENTITY, and only an
        engine that says the identity does not exist produces `absent`.
        Anything else -- a non-zero status this adapter does not recognise,
        prose it cannot parse, a document missing the members it needs -- is
        `uncertain`, because a manager that treated confusion as death would
        release an assignment whose worker is still running.
        """
        runtime_id = boundaries.identity(runtime_id, "a runtime id")
        answer = self.run(inspect_vector(self.engine, runtime_id=runtime_id))
        if answer["status"] != 0:
            # POSITIVE ABSENCE IS ABOUT THIS IDENTITY, and the engine has to
            # say so. Review [P1]: matching "no such" or "not found" anywhere
            # in stderr made any unrelated prose carrying those words --
            # a missing network, an absent volume, a daemon reporting a
            # missing socket -- read as this runtime being dead, which is the
            # one mistake that releases an assignment whose worker is running.
            # The contract is now engine-specific and names the runtime.
            if _absent_prose(answer["stderr"], runtime_id):
                return {"state": "absent",
                        "why": "the engine answered that this exact identity "
                               "does not exist"}
            return {"state": "uncertain",
                    "why": f"the engine refused to inspect this runtime: "
                           f"{answer['stderr'][:MAX_DIAGNOSTIC]}"}
        document = _decoded(answer["stdout"], "an engine inspection")
        if type(document) is list:
            if len(document) != 1:
                return {"state": "uncertain",
                        "why": f"the engine answered about {len(document)} "
                               f"runtimes for one exact identity"}
            document = document[0]
        if type(document) is not dict:
            return {"state": "uncertain",
                    "why": "the engine's inspection is not one record"}
        # AND A SUCCESSFUL INSPECTION MUST BE ABOUT THE RUNTIME WE ASKED
        # ABOUT. Review [P1]: this read `State` from whatever document came
        # back, so an engine answering about another container -- or about
        # nothing identifiable -- was reported as this one's state.
        named = None
        for member in ("Id", "ID", "ContainerID"):
            if member in document:
                named = document[member]
                break
        if type(named) is not str or not named:
            return {"state": "uncertain",
                    "why": "the engine's inspection names no runtime, so it "
                           "is not evidence about this one"}
        if named != runtime_id:
            return {"state": "uncertain",
                    "why": f"the engine answered about "
                           f"{name_value(named)} and this asked about "
                           f"{name_value(runtime_id)}"}
        state = _one_of(document, ("State",), "an engine inspection")
        if type(state) is not dict:
            return {"state": "uncertain",
                    "why": "the engine's inspection carries no state record"}
        running = state.get("Running")
        if running is True:
            return {"state": "running", "why": "the engine reports it running"}
        if running is False:
            return {"state": "quiescent",
                    "why": "the engine reports it not running"}
        return {"state": "uncertain",
                "why": f"the engine reports Running as "
                       f"{name_value(running)}, which is neither"}

    def _labels_of(self, entry):
        """The labels the engine reports, back in the manager's vocabulary.

        Docker answers a record and Podman has answered a comma-joined string;
        both are read, and a label set that is not exactly this contract's
        member set refuses rather than being padded out -- a runtime whose
        labels this adapter had to guess at is one reconciliation cannot use.
        """
        reported = _one_of(entry, ("Labels", "labels"),
                           "an engine listing entry")
        if type(reported) is str:
            pairs = {}
            for piece in reported.split(","):
                if not piece:
                    continue
                key, sep, value = piece.partition("=")
                if not sep:
                    _refuse(f"an engine label list carries "
                            f"{name_value(piece[:MAX_DIAGNOSTIC])}, which is "
                            f"not `key=value`")
                pairs[key] = value
            reported = pairs
        if type(reported) is not dict:
            _refuse(f"an engine listing entry reports labels as "
                    f"{name_value(reported)}")
        # NO UNKNOWN `baton.v12.*` LABEL. Review [P1]: an extra
        # manager-owned label was silently ignored, so anything that could
        # write one -- including a worker that reached the engine -- could
        # attach `baton.v12.bearer` to a runtime this manager then reconciled
        # on without ever seeing it. The namespace is this manager's, so a
        # member of it that this build does not name is a refusal.
        ours = sorted(key for key in reported
                      if key.startswith(LABEL_PREFIX))
        expected = [f"{LABEL_PREFIX}{name}"
                    for name in documents.RUNTIME_LABELS]
        if ours != sorted(expected):
            _refuse(f"a listed runtime's {LABEL_PREFIX}* labels are "
                    f"{', '.join(ours) or 'absent'}; this adapter reconciles "
                    f"on the whole label set and no other member of its own "
                    f"namespace")
        return {name: _label_value(name, reported[f"{LABEL_PREFIX}{name}"])
                for name in documents.RUNTIME_LABELS}


def _label_value(name, value):
    """Each label back in the type its RULE gives it, not as engine text.

    Review [P1]: every label came back as whatever the engine printed, so a
    digest label reading `profile-latest` and a generation of `-1` were both
    accepted and compared. A label is reconciliation evidence; a member whose
    semantic rule it fails is not this assignment's label however it is
    spelled.
    """
    if name == "generation":
        return _whole(value)
    if type(value) is not str:
        _refuse(f"the {name} label is {name_value(value)}; a label is text")
    if name.endswith("_digest"):
        if not _DIGEST.match(value or ""):
            _refuse(f"the {name} label is {name_value(value)}, which is not a "
                    f"sha256 digest; a runtime this manager cannot bind to an "
                    f"exact image, profile or adapter is not reconcilable")
        return value
    return boundaries.text(value, "a runtime label")


def _whole(value):
    """A generation comes back from an engine as TEXT and is a number.

    The manager compares the label set it minted against the set the engine
    reports, so `1` and `"1"` are the same fact spelled two ways -- and a
    comparison that called them different would report every reconciliation as
    a mismatch.
    """
    if type(value) is int and type(value) is not bool:
        # A GENERATION IS COUNTED UP FROM ONE. `-1` is an int and is not a
        # generation; the type alone was never the rule.
        if value < 1:
            _refuse(f"a generation label is counted up from one; this is "
                    f"{name_value(value)}")
        return value
    boundaries.text(value, "a generation label")
    # `isdigit` is the whole rule: it refuses a sign, so `-1` never reaches
    # `int` and a generation is a counter that was only ever incremented.
    if not value.isdigit():
        _refuse(f"a generation label is a whole number that was counted up "
                f"from one; this is {name_value(value)}")
    return int(value)
