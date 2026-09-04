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
  * THE RESTRICTIONS ARE UNCONDITIONAL, WITH ONE NAMED EXCEPTION. Every
    capability dropped, privilege escalation denied, no nested runtime or
    engine socket, a fixed non-root user, and read-only root with the workspace
    as the one writable mount. Those are not options a caller may relax: a
    policy that a caller can turn off is a default.

    THE EXCEPTION IS `--network`, and it is stated here rather than discovered
    at the vector. W38956 found that an unconditional `none` made this
    campaign's own first provider-backed task impossible rather than isolated:
    no runtime this adapter starts could reach a provider at all. The value is
    now one explicit deployment operand whose only default is `none`, so an
    adapter that names nothing composes exactly what it composed before and a
    grant is something somebody asked for. The flag itself is still always
    present; what a deployment may choose is its value.

    `--interactive` IS NOT AN EXCEPTION TO THIS and is not a restriction at
    all: it is absent by default and is what holds the worker's stdin open so
    `exec_vector` can speak the worker-entry channel to it.
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

from ..contracts import ContractRefusal, check_no_durable_secret
from ..contracts.pod import own
from ..contracts.errors import name_value
from . import (boundaries, credentials, documents, launch, sealing,
               workspaces)

__all__ = ["ENGINES", "EnginePort", "LABEL_PREFIX", "LABEL_CONTEXT",
           "MAX_DIAGNOSTIC",
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

# W16823: THE TRUSTED CONTEXT AN ADAPTER REQUEST CARRIES, and it is exactly the
# two label members the manager cannot derive from the assignment fence.
#
# WHY IT ARRIVES AS AN OPERAND rather than being looked up: this adapter holds
# no control store and no authority session, and giving it either so it could
# fetch a principal would be handing the isolation layer a capability the whole
# topology exists to keep out of it. The manager reads its own activated
# attempt row and passes what it read.
#
# THE WORKER SUPPLIES NONE OF IT. These requests are composed by the manager
# from durable columns the port is the only writer of; nothing a container
# says reaches this document.
LABEL_CONTEXT = ("principal", "effective_scope")

# How much engine prose ever reaches a refusal. Engine stderr is unbounded
# caller-controlled text and a refusal is the thing most likely to be logged --
# the same rule W1593 established for every other diagnostic in this manager.
MAX_DIAGNOSTIC = 240

# W38956: THE CLOSED NETWORK POSTURE, and the only value that is a default.
#
# `none` is what an execution container gets unless a deployment names another
# posture in the one operand below. It is spelled once, here, because it is
# both the table's entry and the operand's default and two spellings of one
# decision is how those stop agreeing.
NETWORK_NONE = "none"

# What an engine accepts as a network NAME, and nothing wider. Docker and
# Podman both take `[a-zA-Z0-9][a-zA-Z0-9_.-]*` for a user-defined network and
# reserve `none`, `host` and `bridge` besides. The grammar is what keeps this
# operand a network name rather than an opening for arbitrary engine
# vocabulary: a value carrying a space, a flag or a path is refused before the
# vector is composed, so a caller cannot smuggle a second argument through it.
_NETWORK = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}\Z")

# HOW MANY WORDS AN EXEC PROGRAM MAY BE. The program is a fact about the IMAGE
# and is composed by whoever resolved the image, so the ceiling is here rather
# than a matter of taste: an unbounded operand is an unbounded argv.
MAX_PROGRAM_WORDS = 16

# THERE IS DELIBERATELY NO DEFAULT SESSION BOUND HERE. Review [P2] found an
# `EXEC_SECONDS = 3600` constant nothing read, and removing it is the decision
# rather than wiring it up. How long a provider turn may take is the OPERATOR
# checkpoint's policy, not this adapter's; `worker_entry.converse` therefore
# requires the bound as an operand and refuses anything that is not whole
# positive seconds. A default here would be this module quietly owning a
# policy it cannot see the inputs to, and an unread constant is a claim that
# it does.

# §policy: the restrictions, as ONE table rather than as flags spread through a
# builder. Written out so a reader can see the whole posture at once and a
# reviewer can diff it. EVERY ENTRY IS APPLIED, and exactly one of them --
# `--network` -- carries a value a deployment may substitute; see below.
#
# EVERY ENTRY IS APPLIED UNCONDITIONALLY EXCEPT ONE, and the exception is named
# here rather than discovered in `run_vector`. W38956: `--network` carries the
# DEFAULT posture and a deployment may substitute another by naming it. The
# table keeps the entry -- so this is still the one place the whole posture is
# readable, and a caller that names nothing still gets `none` -- and
# `run_vector` replaces exactly that one value and never appends a second
# `--network`.
#
# WHY IT HAD TO BECOME AN OPERAND. A worker backed by a REAL provider must
# reach it, and until this existed no runtime this manager started ever could:
# W17110 proved a real Claude CLI in Docker through the spike's own lifecycle,
# never through this adapter. An unconditional `none` therefore made this
# campaign's own first useful task impossible rather than isolated, and a run
# that reported success without egress would have been reporting something
# else. The grant is explicit, defaulted closed, bounded to an engine network
# NAME, and recorded in the attempt's evidence beside the image and the
# credential; this adapter gains no other network vocabulary.
RESTRICTIONS = (
    # No capability at all, and no way to acquire one back.
    ("--cap-drop", "ALL"),
    ("--security-opt", "no-new-privileges"),
    # A worker is not a runtime host. Without this, a compromised worker starts
    # its own containers with whatever posture it likes.
    ("--security-opt", "label=disable"),
    # A fixed non-root user. Root inside a user namespace is still root against
    # anything the namespace does not cover.
    #
    # W33936: the UID is fixed here and the GID is composed in `run_vector`
    # for an execution container, because a group is the only least-privilege
    # way to let uid 65532 write a root this manager owns. The manager cannot
    # `chown` without privilege it does not have, and the alternatives are
    # worse: world-writable widens the root to every local account, and a
    # matching uid would give the worker the manager's own identity. This
    # entry stays because a consent container -- which mounts nothing and has
    # nothing to write -- keeps exactly this pair.
    ("--user", "65532:65532"),
    # The root filesystem is evidence, not scratch: the workspace mount is the
    # one writable place, and it is named per assignment.
    ("--read-only", None),
    # THE ONE SUBSTITUTABLE ENTRY. `none` is the value a caller that names
    # nothing gets, and it is a DEFAULT rather than a constant -- see the note
    # above the table and `_network` below.
    ("--network", NETWORK_NONE),
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
# Execution may see `inputs` read-only and `workspace` read/write, and those
# two are the whole set -- see `ROOT_NAMES` below.
POSTURES = ("consent", "execution")
# W15232 review [P1]: TWO GENERIC ROOTS. This core closed over an
# acquisition-specific third root that no posture was ever allowed to mount, so
# `_roots` refused an otherwise complete generic root set -- the adapter still
# understood an acquisition format after the operations that consumed that root
# were gone. A stager or driver needing private capacity allocates its own
# under an explicit owner.
ROOT_NAMES = ("inputs", "workspace")
MOUNTABLE = {"consent": (), "execution": ("inputs", "workspace")}
WRITABLE = {"execution": ("workspace",)}

# THE WORKER'S FIXED INPUT PATH, as a constant of the contract (§7.0). The same
# string the worker reads its two documents from, and the same one the recipe
# gives it -- a path a mount plan could vary is a path a runtime can be pointed
# at wrongly.
INPUT_TARGET = "/input"


# THE ONE RESOLVED IDENTITY a delivery is made under. Review: the adapter
# held `image_digest` and `start` accepted labels independently, so what was
# STARTED and what the runtime was LABELLED with were two accounts nothing
# compared. Reconciliation after a restart finds a runtime by those labels and
# then reasons about it as though they described the image that is running.
#
# One record, owned at construction, is what makes the two accounts one: the
# image reaches the argv from it, the profile, policy and adapter digests
# reach the labels from it, and a request whose labels disagree is refused
# rather than started.
#
# FOUR DIGESTS, and the record has said four since it was confirmed. Review
# [P1]: the first version of this tuple carried three and actively refused
# `policy_digest`, which narrowed a confirmed contract without a supersession
# anybody had agreed to -- and a resolved identity missing the policy is one
# that cannot answer what a running worker was started to obey.
RESOLVED_IDENTITY = ("image_digest", "profile_digest", "policy_digest",
                     "adapter_digest")

# The members of the resolved identity a runtime's LABELS carry, so a restart
# can compare them. The image is deliberately not among them: the engine
# reports what it is running, and its own record beats a label this manager
# wrote about itself.
_LABELLED_IDENTITY = ("profile_digest", "policy_digest", "adapter_digest")

# THE CANDIDATE SELECTOR: which runtimes are THIS ATTEMPT'S, whatever they were
# delivered under. Everything in the frozen label set that is not part of the
# resolved identity -- the attempt, the four parts of the assignment.
#
# Review [P0]: the listing used to filter on all eight labels, and a real
# engine applies every filter BEFORE it returns a row. So a runtime from this
# exact attempt running under an OLD policy was omitted from stdout, never
# reached the identity comparison below, and `start` read the empty candidate
# set as "nothing exists" and created a second runtime for one attempt --
# which is the state the acceptance says no later reconciliation can undo.
#
# DISCOVERY HAS TO BE BROADER THAN COMPARISON. The engine answers which
# runtimes belong to this attempt; this adapter decides, in process, whether
# each one is this delivery's. A stale one is then REFUSED rather than
# filtered away, which is what the module docstring has claimed all along:
# it is not absent, it is wrong, and dropping it leaves a mislabelled runtime
# running.
#
# AND THE SELECTOR IS THE MINIMAL OWNERSHIP KEY, which took two corrections to
# get to. The first moved the three resolved digests out of the filters and
# stopped there -- leaving the attempt, the four parts of the assignment and
# the generation as exact filters -- so review [P0] found the same defect
# still standing in the same boundary: a runtime carrying THIS attempt id
# under generation 0 while the request says 1 is hidden by the engine, `start`
# reads absence, and it creates the duplicate.
#
# The general rule is the one that was missing. ANY assignment fact used as a
# filter hides a runtime that contradicts it, and a contradictory runtime is
# exactly what this adapter exists to refuse. So the ONE label that selects is
# the one that answers "is this runtime this attempt's" and can never
# disagree without meaning a different attempt entirely.
_CANDIDATE_LABELS = ("runtime_attempt_id",)

# What the engines call the image of a listed runtime. Docker's `ps` answers
# `Image`, and because this adapter starts a runtime BY DIGEST that field is
# the `sha256:` reference rather than a tag. Podman answers both, and its
# `ImageID` is the unambiguous one, so it is asked for first.
_LISTED_IMAGE = ("ImageID", "ImageId", "Image")


def _image_identity(value, what):
    """One image named as a digest, however the engine spells the prefix.

    An engine that cannot name a runtime's image by digest has not proved
    which image is running, and a tag is not an identity: it is a pointer that
    was true when somebody last pushed. Refused rather than compared loosely,
    because the comparison this feeds decides whether a restarted manager
    adopts a worker.
    """
    # A LITERAL LABEL at the owner, for the reason `_canonical` gives: the
    # inventory attributes an owned entry by the label written at the site, so
    # a computed one is a boundary it cannot place. `what` still names which
    # image disagreed in the refusal below.
    text = boundaries.text(value, "a runtime image")
    bare = text[len("sha256:"):] if text.startswith("sha256:") else text
    if not re.fullmatch(r"[0-9a-f]{64}", bare):
        _refuse(f"{what} is {name_value(text)}, which is not an image digest; "
                f"an engine that cannot name the image by digest has not "
                f"said which image is running", code="digest")
    return bare


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


# W6636: the three retention dispositions, and which of them KEEP the bytes.
# `retain` is policy keeping them and `quarantine` is doubt keeping them; the
# third discards. Spelled here rather than imported from `intake`, because this
# core answers facts about an engine and its own custody and does not depend on
# the manager that calls it.
#
# THE CLOSED SET IS THE POINT. Re-review [P1]: this branched on membership of
# the keeping pair and let EVERYTHING ELSE fall through to the discard, so a
# typo or a value from a later vocabulary removed the material and reported
# success. An adapter boundary that owns a destructive command may not make
# unknown mean delete.
_KEEPS_MATERIAL = ("retain", "quarantine")
_RETENTION_DISPOSITIONS = ("discard-after-intake",) + _KEEPS_MATERIAL


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

    def __call__(self, argv, *, seconds=None):
        """Answer `(status, stdout, stderr)` for one closed vector.

        `seconds` IS A DEADLINE THE CAPABILITY MUST HONOUR BY TERMINATING.
        W43974 review (2026-08-30T05:28:16Z) [P0]: a caller that merely stops
        waiting has not stopped the engine operation, and an abandoned call is
        free to mutate the engine after the caller has reported and acted on
        its absence. So a caller that needs a bound passes it through to the
        capability, whose contract is that it has terminated AND REAPED its
        child before it answers -- which is exactly `subprocess.run(argv,
        timeout=seconds)`.

        OPTIONAL, AND FORWARDED ONLY WHEN GIVEN. Every caller that does not
        pass one calls the capability exactly as before, so an injected
        operation that takes only an argv keeps working; a caller that DOES
        pass one is stating that its capability accepts the operand, and
        `custody.custody_act` proves that of its own before it runs anything.

        §13 OVER EVERY ARGV THAT REACHES AN ENGINE, and this is the one place
        that can say that. Review [P1]: `run_vector` swept the vector it
        composed, and nothing swept the others — so `start`'s duplicate probe
        and the refusal path's own listing reached the engine unswept. The
        candidate selector puts `runtime_attempt_id` into a `--filter`
        argument, and a provider answer is explicitly untrusted, so a bearer
        equal to that identity was handed to the daemon by the very call that
        was supposed to run before anything happened.

        MOVED HERE RATHER THAN COPIED. Adding the sweep to `list_vector`
        beside `run_vector`'s would have been four more copies of one rule and
        a fifth waiting for the next vector somebody adds. Every process on the
        host can read another's command line, so the property is about
        INVOCATION rather than composition — and invocation is exactly what
        this port is.
        """
        check_no_durable_secret(list(argv), what="an engine vector")
        if seconds is None:
            answer = self._run(argv)
        else:
            # VALIDATED BEFORE IT IS FORWARDED. W43974 review
            # (2026-08-30T05:44:32Z) [P1]: every non-`None` value reached the
            # injected capability, so zero, a negative, a bool, a float and
            # text all became whatever coercion the injector happened to
            # perform -- on a seam whose whole purpose is that a caller can
            # depend on the bound. The rule is `stop_vector`'s, because two
            # spellings of "a positive whole number of seconds" in one module
            # is two contracts.
            if type(seconds) is not int or type(seconds) is bool \
                    or not 0 < seconds:
                _refuse(f"an engine deadline is a positive whole number of "
                        f"seconds; this is {name_value(seconds)}")
            answer = self._run(argv, seconds=seconds)
        taken = boundaries.document(answer, "the engine's answer",
                                    required=("status", "stdout", "stderr"))
        # EACH MEMBER READ BY NAME, and W43977 [P0] is why the loop went.
        #
        # `for stream in ("stdout", "stderr")` reads through a LOOP VARIABLE,
        # so the boundary inventory cannot see which members this manager
        # consumes -- a member the universe cannot name is a crossing nobody
        # can be asked to own or witness. The two reads are the same rule and
        # the same owner; only the spelling changed, so the inventory can
        # discover them.
        _status(taken["status"])
        _stream(taken["stdout"], "the engine's stdout")
        _stream(taken["stderr"], "the engine's stderr")
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


def _status(value):
    """The engine's exit status: a whole number and never a bool.

    Named rather than inline for the reason `_stream` beside it is: a rule
    written into the middle of a caller is a rule the inventory cannot name,
    and this one decides whether an engine's act succeeded.
    """
    # NOT `boundaries.injected`, and the attempt is worth recording: that kind
    # proves an injected answer is DURABLE TEXT, so using it here refused
    # every integer status the engine has ever returned. An owner that makes
    # the rule wrong is not an owner. `run.status` therefore has no layer
    # owner the inventory can see, which is a real gap and is reported rather
    # than papered over with a table entry.
    if type(value) is not int or type(value) is bool:
        _refuse(f"the engine's exit status is a number; this is "
                f"{name_value(value)}")
    return value


def _stream(value, what):
    """Engine output: text that MAY BE EMPTY, and must be storable.

    Not `boundaries.text`, deliberately. That rule is for a durable operand and
    refuses the empty string, which is exactly what a quiet engine writes --
    "nothing on stderr" is the ordinary case and would otherwise be a fault.
    What still has to hold is that the text can be stored and put in a message,
    because a refusal quoting it is a durable value like any other.
    """
    # AND NOT `boundaries.injected` EITHER, for the reason this docstring
    # already gives: that kind refuses the empty string, which is exactly what
    # a quiet engine writes. Naming it here made "nothing on stderr" a fault.
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


def _network(network):
    """The engine network this runtime joins, as a NAME and nothing else.

    W38956. `none` is the default and is returned unchanged; anything else is
    a posture a deployment named DELIBERATELY, so it is held to the engines'
    own network grammar before it can reach an argv.

    THE REFUSAL IS THE POINT OF THE OPERAND. A value carrying a space, a
    leading dash or a path is not a network an engine would accept anyway --
    what refusing it buys is that this operand can never become a way to append
    a second argument to a vector this module composes closed.

    NOTHING HERE DECIDES WHETHER EGRESS IS APPROPRIATE. That is the
    deployment's decision and it is recorded where deployments are recorded;
    this refuses the values that are not a network at all.
    """
    boundaries.text(network, "an engine network")
    if not _NETWORK.match(network):
        _refuse(f"{name_value(network)} is not an engine network name; this "
                f"operand names a network and is not a way to add an argument "
                f"to a closed vector", code="schema")
    return network


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


def canonical_target(place, what):
    """One CONTAINER path, canonical as text and never resolved here.

    THE SPELLING IS CHECKED BEFORE `normpath` CAN ERASE IT. `/else/../input`
    normalizes to `/input`, so a rule that normalized first would accept a plan
    that names a path this manager never fixed and call it the fixed one --
    W19784 third review [P1], which found exactly that in the manager's
    pre-journal check while the adapter refused it correctly one layer later.

    AND IT IS NEVER RESOLVED. A target names a path inside a container that
    does not exist yet; resolving it against THIS host's filesystem would be
    asking the wrong machine. That is the whole difference from
    `canonical_source` below, and it is why they are two functions rather than
    one with a flag.
    """
    text = boundaries.text(place, "a container path")
    if ".." in text.split("/") or ":" in text:
        _refuse(f"{what} is not canonical; `..` and the engine's own `:` "
                f"separator are both refused, because a caller writing either "
                f"is asking this adapter to compute a path rather than name "
                f"one", code="path")
    target = os.path.normpath(text)
    if not target.startswith("/"):
        _refuse(f"{what} is {name_value(target)}, which is not an absolute "
                f"path", code="path")
    return target


def canonical_source(place, what):
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
    # THE MANAGER'S OWN PROOF SURVIVES TO THE USE, when there is one.
    #
    # W39358 review [P1]: every caller flattened `AllocatedRoots` to a plain
    # `dict` because the document check below refuses anything carrying
    # behaviour -- and the flattening threw away exactly the fact worth
    # keeping. `AllocatedRoots` is minted ONLY by `assignment_workspace` and
    # `adopted_assignment_workspace`, both of which prove each root is a real
    # directory of this attempt's own, not a link, resolving to its own path
    # under the configured store. A caller cannot construct one and cannot
    # retarget one.
    #
    # So a nominal answer is ADOPTED rather than re-derived: canonicalizing it
    # again would resolve the pathname a second time, which is the
    # check-then-open interval this correction exists to close. A plain
    # mapping is still accepted and still proved here, because callers outside
    # the allocation path legitimately have one.
    if type(assignment_roots) is workspaces.AllocatedRoots:
        # RETURNED AS ITSELF, not copied. Review 2026-08-30T19:10:03Z: my first
        # cut preserved the VALUES and dropped the type, so the adapter held a
        # plain mapping and `run_vector` re-entered here with it -- and
        # re-entry took the canonicalizing branch, which is the very
        # re-resolution this was meant to remove. Provenance that survives one
        # call and not the next is not provenance.
        real = assignment_roots
    else:
        taken = boundaries.document(assignment_roots,
                                    "the assignment's roots",
                                    required=ROOT_NAMES)
        real = {name: canonical_source(taken[name], f"the {name} root")
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
        source = canonical_source(one["source"], "a mount source")
        # ONE RULE, AT ONE OWNER. The spelling is checked before `normpath`
        # can erase it: `normpath` ran first here once, so the `..` test could
        # never see traversal that normalization had already consumed -- and a
        # workspace requested at `/workspace/../etc` was accepted and emitted
        # as `target=/etc`, moving the assignment's WRITABLE bind over the
        # image filesystem.
        #
        # W19784 third review [P1] found the same erasure in the manager's own
        # pre-journal check, written as a second copy of this rule. It is now
        # `canonical_target` and there is one of it.
        target = canonical_target(one["target"], "a mount target")
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


def _credential_mounts(pairs):
    """W6634: the delivered credential files, as read-only binds.

    A SEPARATE OWNER FROM `_mounts`, and the separation is the whole point.
    `_mounts` admits a source only because this manager created the assignment
    ROOT it lives under -- that is the posture contract, and W15232 has just
    finished removing a third root from it. A credential is not assignment
    material and must not become a third mountable root: it is delivered at a
    FIXED path of this contract's choosing, from a volatile root
    `credentials.py` owns outright.

    So the rules here are that contract's, not the posture's: every target is
    an entry of `CREDENTIAL_ROOT`, every source is inside the volatile root
    that produced it, and readonly is not a parameter.
    """
    taken = []
    seen = set()
    if len(pairs) > credentials.MAX_SLOTS:
        _denied(f"a delivery mounts at most {credentials.MAX_SLOTS} "
                f"credential slots; this one names {len(pairs)}")
    for pair in pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            _refuse(f"a credential mount is a source and a target; this is "
                    f"{name_value(pair)}")
        source = canonical_source(pair[0], "a credential mount source")
        target = boundaries.text(pair[1], "a credential mount target")
        head, _, slot = target.rpartition("/")
        if head != credentials.CREDENTIAL_ROOT:
            _denied(f"a credential mount lands on {name_value(target)}; the "
                    f"worker sees credentials only as entries of "
                    f"{credentials.CREDENTIAL_ROOT}, which is a constant of "
                    f"this contract rather than an operand")
        # THE SLOT'S OWN GRAMMAR, applied to the container side too, and
        # applied by the module that OWNS it rather than restated here. A
        # target whose last segment could name something else is a target this
        # adapter would be computing rather than naming.
        credentials.slot_name(slot)
        if os.path.basename(source) != slot:
            _denied(f"a credential mount exposes {name_value(source)} as "
                    f"{name_value(target)}; a slot is delivered under its own "
                    f"name, and a file renamed on the way in is one nobody "
                    f"can trace back to what was authorized")
        if target in seen:
            _refuse(f"two credential mounts land on {name_value(target)}; the "
                    f"second would hide the first")
        seen.add(target)
        taken.append((source, target))
    return tuple(taken)


# W26291: THE REFERENCE WORKER'S LAUNCH DOCUMENT, and it is a MOUNT rather
# than an environment.
#
# W6636's composition found that this adapter delivered nothing the reference
# worker needed, so every execution container it started from the reference
# image exited at once with no frame -- two closed components that could not
# meet. The first correction delivered four `BATON_WORKER_*` values as `--env`
# arguments and the dossier SUPERSEDED it before acceptance: one versioned
# document at a fixed read-only path, with no environment fallback and no
# compatibility path.
#
# NOT IN THE FROZEN `runtimeStartBody`, which has `additionalProperties: false`
# and no launch member. This is a manager/adapter seam rather than protocol
# state, which is what the finding says it is -- so the delivery is typed at
# `launch.py` and this boundary composes exactly one mount out of it.
#
# THE TARGET IS THIS CONTRACT'S CONSTANT and never an operand. `launch.py` owns
# it, the worker reads it, and the pair this adapter is handed is a source and
# that constant -- there is no caller-selected locator to point a container at
# something else.


def _launch_mount(pair):
    """The one read-only bind a launch delivery authorizes.

    THE SAME SHAPE `_credential_mounts` HAS, and for the same reason. What
    crosses to the ADAPTER is a typed capability -- a path operand would be the
    caller-selected locator the fixed target exists to remove, and a mapping
    would be the environment channel this Work replaced wearing a different
    name. What crosses to THIS function, which composes argv and nothing else,
    is the pair that capability answered with, owned here exactly as a
    credential delivery's pairs are.
    """
    if type(pair) not in (list, tuple) or len(pair) != 2:
        _refuse(f"a launch mount is a source and a target; this is "
                f"{name_value(pair)}")
    source = canonical_source(pair[0], "a launch document source")
    target = boundaries.text(pair[1], "a launch document target")
    if target != launch.LAUNCH_TARGET:
        _denied(f"a launch delivery lands on {name_value(target)}; the worker "
                f"reads its launch document at "
                f"{name_value(launch.LAUNCH_TARGET)}, which is a constant of "
                f"this contract rather than an operand")
    # A REGULAR FILE, PROVED HERE. A directory bound over the worker's fixed
    # document path is a path the worker cannot read a document out of, and a
    # link is a source this manager would be resolving on the worker's behalf.
    # `canonical_source` already resolved it, so this is the object that will
    # actually be mounted.
    if not os.path.isfile(source):
        _refuse(f"a launch delivery names {name_value(source)}, which is not "
                f"a regular file; the worker's launch document is one "
                f"document at one path", code="path")
    return source, target


def run_vector(engine, *, image_digest, labels, assignment_roots, posture,
               mounts=(), credentials_delivered=(), launch_delivered=None,
               name, workspace_group=None, network=NETWORK_NONE,
               interactive=False):
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
    # W38956: THE CHANNEL, HELD OPEN, and OFF unless a caller asks for it.
    #
    # Without `--interactive` a detached container's stdin is `/dev/null`: the
    # worker reads EOF at once, exits 0 and the container ends. That is the
    # right posture for a runtime nobody is going to speak to, and it is what
    # every accepted case in this campaign asserts -- so it stays the default.
    #
    # With it, PID 1 blocks on a stdin the daemon holds, the runtime stays up,
    # and `exec_vector` below opens the worker-entry conversation against it.
    # A start that composes this and is then never spoken to HANGS rather than
    # exiting, which is a real difference and is why it is never composed on
    # a caller's behalf.
    if interactive is True:
        argv.append("--interactive")
    elif interactive is not False:
        _refuse(f"an interactive channel is asked for or it is not; this is "
                f"{name_value(interactive)}")
    # THE CONFIGURED WORKSPACE GROUP, AS A SUPPLEMENTARY GROUP.
    #
    # W33936, approver ruling M34916.  The container's fixed 65532 is not this
    # manager's uid, so an engine-writable workspace bind was denied by
    # ordinary permissions and the worker could not write the outputs it is
    # required to declare.
    #
    # `--group-add`, AND THE PRIMARY IDENTITY IS UNTOUCHED.  My rejected cut
    # composed `--user 65532:<gid>`, which changes the pinned runtime identity
    # W6632 fixes and W6633's image asserts alongside it -- and it inherited
    # whatever group the workspace happened to carry, measured to be a user's
    # LOGIN group.  Measured against a real daemon, the supplementary form
    # leaves `uid_gid` at exactly `[65532, 65532]` and adds the group beside
    # it, which is the whole difference between the two.
    #
    # AN OPERAND RATHER THAN A `stat` HERE, and an earlier cut got that wrong
    # by reading the directory inside this function: every one of W6632's
    # vector cases broke, because a vector is provable without a filesystem.
    # The group is deployment CONFIGURATION and is validated by
    # `workspaces.check_workspace_group`, which refuses gid 0, a gid this
    # manager does not hold, and anything that is not a group id -- and which
    # has no default at all, because a group inherited from a service
    # directory is not a workspace grant.
    #
    # EXECUTION ONLY.  A consent container mounts nothing, so a group there
    # would be a grant with no object, and the ruling says so in terms.
    #
    # AN UNCONFIGURED EXECUTION REFUSES HERE, and my last cut had this exactly
    # backwards.
    #
    # I argued that composing no group left an unconfigured deployment
    # "unchanged", and that refusing would be this manager failing closed on
    # somebody else's provisioning step.  Review [P0] is right and the argument
    # was wrong: unchanged IS the defect.  A start with no group deterministically
    # produces the container this Work exists to correct -- one that cannot
    # write the workspace it was given -- and calling that a legacy posture
    # makes the correction opt-in.  There is no execution this manager may
    # start without knowing which group the worker holds, so there is no
    # default and no fallback; a deployment that has not provisioned the group
    # is told so before the engine is invoked rather than by a worker failing
    # halfway through its work.
    #
    # CONSENT IS NOT THE SAME QUESTION and is unaffected: it mounts nothing, so
    # a group there would be a grant with no object, and it is refused for that
    # reason rather than permitted for lack of one.
    # THE ONE SUBSTITUTION, at the table rather than after it. Composing the
    # restrictions and then appending a second `--network` would leave two in
    # one vector and let the engine decide which won; replacing the value in
    # place means there is exactly one network in the argv whatever was asked
    # for, and a reader can still see the whole posture in `RESTRICTIONS`.
    network = _network(network)
    for flag, value in RESTRICTIONS:
        argv.append(flag)
        if flag == "--network":
            value = network
        if value is not None:
            argv.append(value)
    roots, posture = _roots(assignment_roots, posture)
    if posture == "execution":
        if workspace_group is None:
            _denied("an execution runtime is given the deployment's configured "
                    "workspace group and this start names none; without it the "
                    "worker holds no share in its own workspace and cannot "
                    "write the outputs this assignment requires it to declare")
        # THE SAME CAPABILITY AT THE VECTOR, because a vector is composed
        # from operands and this one decides an authorization. Validating an
        # integer here would be validating whatever the caller chose.
        if type(workspace_group) is not workspaces.WorkspaceGroup:
            _denied(f"an execution runtime is given the deployment's "
                    f"configured workspace group, read from this manager's "
                    f"own record; this start names "
                    f"{name_value(workspace_group)}")
        argv += ["--group-add",
                 str(workspaces.check_workspace_group(workspace_group.gid))]
    elif workspace_group is not None:
        _denied("a consent runtime mounts nothing and is given no "
                "supplementary group; a grant with no object is still a grant")
    for key, value in _label_pairs(_labels(labels)):
        argv += ["--label", f"{key}={value}"]
    assigned = _mounts(mounts, roots, posture)
    for source, target, writable in assigned:
        argv += ["--mount",
                 f"type=bind,source={source},target={target},"
                 f"readonly={'false' if writable else 'true'}"]
    # W6634: THE CREDENTIALS, ALWAYS READ-ONLY and always under the fixed
    # root. Composed after the assignment mounts, and refused outright if one
    # of them would contain a delivery -- an assignment mount over
    # `/run/baton/credentials` would decide what the worker reads there, which
    # is the one thing the fixed root exists to take away from it.
    for source, target in _credential_mounts(credentials_delivered):
        for _source, taken, _writable in assigned:
            if taken == target or _within(target, taken):
                _denied(f"a credential mount lands on {name_value(target)}, "
                        f"which this assignment already mounts; the worker "
                        f"would read one of the two and neither this manager "
                        f"nor the engine says which")
        argv += ["--mount",
                 f"type=bind,source={source},target={target},readonly=true"]
    # W26291: THE LAUNCH DOCUMENT, ALWAYS READ-ONLY and always at the fixed
    # target. Composed LAST of the three mount families and refused outright
    # if either of the others would contain it -- an assignment or credential
    # mount over the worker's launch path would decide what the worker reads
    # there, which is the one thing a fixed target exists to take away from
    # everybody else. Read-only is not a parameter: a worker that could
    # rewrite its own launch document could change what it is between reading
    # that document and being asked about it.
    if launch_delivered is not None:
        source, target = _launch_mount(launch_delivered)
        for _source, taken, _writable in assigned:
            if taken == target or _within(target, taken):
                _denied(f"a launch document lands on {name_value(target)}, "
                        f"which this assignment already mounts; the worker "
                        f"would read one of the two and neither this manager "
                        f"nor the engine says which")
        argv += ["--mount",
                 f"type=bind,source={source},target={target},readonly=true"]
    # THE IMAGE, LAST and by digest. Every flag precedes it, so nothing a
    # caller supplies can be read as an argument to the engine itself.
    argv.append(image_digest)
    # NO §13 SWEEP HERE ANY MORE, and its absence is the correction rather
    # than an omission. Review [P1]: this function swept the argv IT composed
    # and no other, so `start`'s duplicate probe reached the engine first and
    # unswept. One rule with one owner is `EnginePort.__call__`, which is what
    # every vector — this one, the listing, the inspect, the stop, the
    # destroy, and whatever is added next — actually passes through.
    return argv


def exec_vector(engine, *, runtime_id, program):
    """The closed argv that opens ONE worker-entry conversation in a runtime
    this manager already started.

    W38956. THIS IS THE TRANSPORT AND IT IS NOT A SECOND START. `runtime_id` is
    the identity the engine answered when `run_vector`'s container was created
    and the manager journalled; nothing here creates, names, labels, mounts or
    restricts anything, because everything an exec session can see was decided
    when the runtime was started. An exec against the wrong runtime is an exec
    against another container's mounts, so the id is the whole authorization.

    `--interactive` AND NO `--tty`. Interactive is what makes the worker's
    stdin a real stream this manager can write frames to AND close: measured
    against a live daemon, `docker attach` on a detached interactive container
    never closes the worker's stdin, so a conversation driven that way could
    only ever be ended by killing the container --
    `evidence/w38956-transport-probe.txt` in W38956's record. No tty, because a
    tty MERGES stdout and stderr onto one stream: the worker's answers are
    stdout and its diagnostics are stderr, and a channel that could not tell
    them apart would let a diagnostic be read as a frame.

    THE PROGRAM IS AN OPERAND AND IS NOT COMPOSED HERE. `docker exec` does not
    apply the image's entrypoint, so the worker's program has to be named --
    and the manager does not own that name. It is a fact about the IMAGE, so
    the caller that resolved the image supplies it, exactly as it supplies the
    image digest.
    """
    engine = _engine(engine)
    boundaries.identity(runtime_id, "a runtime id")
    # THE SHAPE IS CHECKED BEFORE PYTHON GETS TO INVENT ONE. Review [P1]:
    # this began `list(program)`, and `list("python3")` is seven one-character
    # words -- so the commonest possible mistake composed
    # `docker exec ... p y t h o n 3`, a successfully closed engine vector
    # rather than a refusal. Iteration is not a contract: a string is iterable
    # and a program is a sequence of WORDS, and only one of those two facts is
    # about this operand.
    #
    # An explicitly supported sequence shape, therefore, and nothing that
    # merely happens to iterate. `str` and `bytes` are named in the refusal
    # because they are the ones a caller actually reaches for.
    if type(program) not in (list, tuple):
        _refuse(f"an exec program is a list or tuple of words; this is "
                f"{name_value(program)}. A string iterates one CHARACTER at a "
                f"time, so accepting one would compose a vector of "
                f"single-letter arguments rather than a program")
    named = list(program)
    if not named:
        _refuse("an exec session names the program that speaks the "
                "worker-entry channel; `docker exec` applies no entrypoint")
    if len(named) > MAX_PROGRAM_WORDS:
        _refuse(f"an exec program is at most {MAX_PROGRAM_WORDS} words; this "
                f"is {len(named)}")
    for one in named:
        boundaries.text(one, "an exec program word")
    return [engine, "exec", "--interactive", runtime_id] + named


def list_vector(engine, *, labels):
    """Ask the engine which runtimes belong to THIS ATTEMPT.

    The candidate selector, not the identity comparison -- see
    `_CANDIDATE_LABELS`. The whole label set is still OWNED here, so a
    malformed or invented label refuses before the engine is asked anything;
    what narrows is only which of those proved values become filters.
    """
    engine = _engine(engine)
    taken = _labels(labels)
    argv = [engine, "ps", "--all", "--no-trunc", "--format", "{{json .}}"]
    for key, value in _label_pairs(taken):
        if key[len(LABEL_PREFIX):] in _CANDIDATE_LABELS:
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


# THE ENGINES' OWN COMPLETE ABSENCE SENTENCES, each one CAPTURING the identity
# the sentence is about.
#
# Review [P0]: the previous version asked two separate questions -- does an
# absence phrase appear anywhere in stderr, and does the requested identity
# appear anywhere in stderr -- and answered "absent" when both were true. Two
# fragments of one diagnostic are not an association, so
#
#     Error: No such container: runtime-2; request was for runtime-1
#
# reported `runtime-1` dead. That is the exact branch that releases an
# assignment whose worker may still be running, which is the one mistake this
# whole module is arranged to avoid.
#
# So the sentence itself must name the runtime. Each pattern below is one
# engine's own complete form with the identity as a capture, and absence is
# reported only when a captured identity IS the one asked about.
#
# PER ENGINE, not pooled: a docker adapter reading podman's phrasing would be
# accepting evidence from a daemon it is not talking to.
_ABSENT_IDENTITY = r"(?P<runtime>[A-Za-z0-9][A-Za-z0-9_./-]*)"
_ABSENT_FORMS = {
    # `Error response from daemon: No such container: <id>`, and the same
    # sentence with `object` for `inspect --type container` on some versions.
    "docker": (re.compile(rf"no such container:\s*{_ABSENT_IDENTITY}", re.I),
               re.compile(rf"no such object:\s*{_ABSENT_IDENTITY}", re.I)),
    # `Error: no container with name or ID "<id>" found: no such container`,
    # and the bare `no such container <id>` older podman emitted.
    "podman": (re.compile(rf"no container with name or id\s+\"?"
                          rf"{_ABSENT_IDENTITY}", re.I),
               re.compile(rf"no such container\s+{_ABSENT_IDENTITY}", re.I)),
}

# Trailing punctuation an engine may put after the identity inside a longer
# diagnostic. Stripped from the CAPTURE rather than admitted into the pattern,
# because none of these characters is legal in a container name or an id.
_ABSENT_TRAILING = ".,;:\"'"


def _absent_prose(engine, stderr, runtime_id):
    """True only when THIS engine's own absence sentence names THIS identity.

    A sentence naming another runtime is evidence about that runtime and
    nothing at all about this one.
    """
    prose = stderr or ""
    for form in _ABSENT_FORMS[engine]:
        for found in form.finditer(prose):
            if found.group("runtime").rstrip(_ABSENT_TRAILING) == runtime_id:
                return True
    return False


def _named_runtime(document):
    """The one identity an inspection document names, or `None`.

    Docker and Podman spell it three ways between them and this adapter reads
    the engines it speaks; a document naming none is not evidence about any
    runtime, which is a different answer from naming the wrong one.
    """
    for member in ("Id", "ID", "ContainerID"):
        if type(document) is dict and member in document:
            named = document[member]
            return named if type(named) is str and named else None
    return None


def _observed_runtime(document):
    """One runtime the engine named, with ITS OWN state and the reason.

    W55758 review (2026-09-01T10:56:54Z) [P1]. `observe` kept candidate
    IDENTITIES and nothing else, so a recovery reporting what it left alone
    had to write `unidentified` for a runtime whose own inspection said
    `Running: true`, and copied the target's diagnostic as that candidate's
    explanation. Both members are in the document that was read; they are
    decided here rather than reconstructed by a caller from the runtime it
    expected.

    A MISSING STATE IS `uncertain` AND NOT A REFUSAL. This reads documents the
    engine volunteered ABOUT OTHER RUNTIMES while answering one exact
    question, so an incomplete one is an incomplete answer about a runtime
    nobody asked about -- while the exact target's own state record is still
    owned by `_one_of` at the one site that requires it.
    """
    named = _named_runtime(document)
    if named is None:
        return None
    state = document.get("State")
    if type(state) is not dict:
        return {"runtime_id": named, "state": "uncertain",
                "why": "the engine's inspection carries no state record"}
    return {"runtime_id": named, **_running_state(state.get("Running"))}


def _running_state(running):
    """The engine's `Running` member, in this manager's own vocabulary.

    ONE DECISION, made once. The exact target's own branch and the candidate
    reader above both need it, and two spellings of "what does `Running` mean"
    is the shape this report has already been corrected for twice.

    NEVER TRUSTED, ONLY COMPARED: the two exact singletons decide, and
    anything else -- absent, text, a number, `None` -- is `uncertain`, because
    a manager that treated confusion as death would release an assignment
    whose worker is still running.
    """
    if running is True:
        return {"state": "running", "why": "the engine reports it running"}
    if running is False:
        return {"state": "quiescent",
                "why": "the engine reports it not running"}
    return {"state": "uncertain",
            "why": f"the engine reports Running as {name_value(running)}, "
                   f"which is neither"}


def _observed_runtimes(documents):
    """Every runtime a listing answer named, each with its own observation."""
    found = [_observed_runtime(one) for one in documents
             if type(one) is dict]
    return [one for one in found if one is not None]


def _observed_mounts(document):
    """What the engine says this runtime's binds ACTUALLY are, or None.

    W6634 fourth review [P1]. Restart adoption compared a lifecycle record
    against locally derived paths and its own files, which proves that a
    document this manager wrote agrees with itself. It says nothing about the
    live container, and the container is the thing that holds the mount.

    `None` MEANS UNKNOWN and an empty tuple means "the engine reported no
    binds". Collapsing the two would let an engine that answered a shape this
    adapter cannot read stand in for one that answered "there is nothing
    mounted", and the second is grounds for adoption while the first is
    grounds for failing closed.

    NOTHING HERE REFUSES. This is one half of an observation whose other half
    is already an honest `uncertain`; a rule that raised would turn an engine's
    unfamiliar output into a fault escaping a method whose whole contract is
    that it answers rather than throws.
    """
    reported = None
    for member in ("Mounts", "mounts"):
        if type(document) is dict and member in document:
            reported = document[member]
            break
    if type(reported) is not list:
        return None
    found = []
    for entry in reported:
        if type(entry) is not dict:
            return None
        source = entry.get("Source", entry.get("source"))
        target = entry.get("Destination", entry.get("Destination".lower()))
        writable = entry.get("RW", entry.get("rw"))
        if type(source) is not str or type(target) is not str \
                or type(writable) is not bool:
            return None
        found.append({"source": source, "target": target,
                      "writable": writable})
    return tuple(found)


def _mounts_disagree(observed, record):
    """Why the live binds are not the recorded delivery, or None if they are.

    FOUR THINGS ARE CHECKED AND THEY ARE FOUR DIFFERENT MISTAKES:

      the engine could not be read       -> nothing is proved, so nothing is
                                            adopted;
      a recorded slot is not mounted     -> the container is not running the
                                            delivery this record describes;
      it is mounted from somewhere else  -> something replaced the source under
                                            the same container path;
      it is mounted WRITABLE             -> a credential the worker can rewrite
                                            is one this manager cannot say the
                                            contents of.

    And one more that is easy to forget: an EXTRA bind under the fixed root.
    The root's entries are the closed slot names, so a container carrying a
    sixth entry under it is carrying something nobody authorized -- and a
    comparison that only looked for what it expected would never see it.
    """
    if observed is None:
        return ("the engine did not report this runtime's binds, so nothing "
                "about its mounts is proved")
    root = record["credential_root"]
    for slot in record["slots"]:
        # ONE AND ONLY ONE. Fifth review [P1]: the observations were collapsed
        # into a dict keyed by target, so two binds on one path became one and
        # the second was never compared. Which of the two a path inside the
        # container reaches is the ENGINE's decision, not this manager's, so a
        # duplicate is a runtime nobody can say the contents of.
        live = [one for one in observed if one["target"] == slot["target"]]
        if len(live) != 1:
            return (f"the live runtime carries {len(live)} binds at "
                    f"{name_value(slot['target'])}; exact agreement is one")
        expected = os.path.join(root, slot["slot"])
        if live[0]["source"] != expected:
            return (f"the live bind at {name_value(slot['target'])} comes "
                    f"from {name_value(live[0]['source'])} and the record says "
                    f"{name_value(expected)}")
        if live[0]["writable"]:
            return (f"the live bind at {name_value(slot['target'])} is "
                    f"writable; a credential the worker can rewrite is one "
                    f"this manager cannot say the contents of")
    # AT OR BELOW THE FIXED ROOT, and `at` is the half that was missing.
    #
    # The previous version looked only for unexpected DESCENDANTS, so a bind
    # directly on `/run/baton/credentials` passed: every per-slot bind
    # underneath it agreed with the record, and the root bind shadowed all of
    # them. The worker would then read whatever that root contained while this
    # manager reported an exact agreement.
    recorded = {one["target"] for one in record["slots"]}
    fixed = credentials.CREDENTIAL_ROOT
    for one in observed:
        target = one["target"]
        if target in recorded:
            continue
        if target == fixed or target.startswith(fixed + "/"):
            return (f"the live runtime carries {name_value(target)} at or "
                    f"below {fixed}, which this assignment did not "
                    f"authorize")
    return None


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
                 posture, mounts=(), outputs=(), input_manifest_digest=None,
                 credential_delivery=None, credential_home=None,
                 credential_orphan=None, launch_delivery=None,
                 workspace_group=None, network=NETWORK_NONE,
                 interactive=False):
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
        # W6634: THE DECLARED OUTPUTS, OWNED AT CONSTRUCTION like everything
        # else that is assignment-scoped and fixed. What may be collected is
        # decided by the assignment, and taking it per call would make that a
        # per-call argument. Defaulted empty so the runtime half of this
        # adapter -- start, list, stop, destroy, observe -- is constructible
        # without them, exactly as it was before sealing existed.
        self.declared_outputs = (sealing.declared_outputs(outputs)
                                 if outputs else {})
        self.input_manifest_digest = input_manifest_digest
        # NO `completion_manifest_digest` OPERAND, deliberately. Sixth review
        # [P1]: this adapter took one and copied it into the receipt, which is
        # a CLAIM that a validation happened rather than evidence of one.
        # `sealing`'s own envelope reader opens the worker's document, owns it,
        # holds it against the declarations and recomputes its digest, so the
        # value the receipt binds is a measurement this manager made.
        # W6634: THE MATERIALIZED CREDENTIAL DELIVERY, and the manager made it.
        #
        # THIS ADAPTER DOES NOT RESOLVE CREDENTIALS, which is the approved
        # boundary read literally: the assignment names slots, the TRUSTED
        # PROFILE maps them, and "the manager resolves that mapping and
        # materializes one assignment-private file per slot". An adapter that
        # called the provider itself would put a credential decision inside the
        # component whose whole contract is that it decides nothing.
        #
        # What crosses here is a delivery that already exists, and what this
        # adapter owns is the two acts at the ends of its life: exposing it at
        # the fixed root when a runtime starts, and tearing it down when one is
        # proved gone.
        if credential_delivery is not None \
                and type(credential_delivery) is not credentials.Delivery:
            _refuse(f"a credential delivery is one this manager materialized; "
                    f"this is {name_value(credential_delivery)}")
        self.credential_delivery = credential_delivery
        # W55758: THE CREDENTIAL HOME, OWNED AT CONSTRUCTION when the
        # deployment has one, and this is the one-owner correction.
        #
        # THE DEFECT. `_credential_home()` derived a home from this adapter's
        # assignment workspace while the deployment materialized under the
        # operator-GRANTED home. Two `CredentialHome` objects each assumed the
        # volatile root and the lifecycle record were siblings below
        # themselves, and for a real attempt they were not: the root sat below
        # the granted home and the record below the assignment-derived one. So
        # adoption refused, the restart builder constructed no delivery, and
        # the ending misreported a delivered credential.
        #
        # A CAPABILITY, NOT A PATH, for the same reason the delivery is one:
        # the granted home is already validated where the grants are read, and
        # re-deriving it here would be a second owner for one deployment fact.
        # Absent, this adapter derives its own exactly as before -- every
        # caller that never had the split is untouched.
        if credential_home is not None \
                and type(credential_home) is not credentials.CredentialHome:
            _refuse(f"a credential home is this manager's own; this is "
                    f"{name_value(credential_home)}")
        self.credential_home = credential_home
        # W55758: THE ORPHAN ENDING, for a delivery this process did not make.
        #
        # A recovery holds no `Delivery` -- the object died with the process
        # that materialized it -- and the ending answered `not-delivered`,
        # positively claiming no credential was ever delivered. This is the
        # typed alternative: what the deployment durably knows, handed over
        # like the delivery it replaces.
        #
        # NEVER BOTH. An attempt has ONE credential ending, and an adapter
        # holding a live delivery beside an orphan teardown for the same
        # attempt would have two acts racing one root.
        if credential_orphan is not None \
                and type(credential_orphan) is not credentials.OrphanTeardown:
            _refuse(f"an orphan credential teardown is this manager's own; "
                    f"this is {name_value(credential_orphan)}")
        if credential_orphan is not None and credential_delivery is not None:
            _refuse("an attempt has one credential ending: the delivery this "
                    "manager materialized or the orphan teardown that stands "
                    "in for one it cannot hold, never both")
        self.credential_orphan = credential_orphan
        # W26291: THE LAUNCH DOCUMENT, OWNED AT CONSTRUCTION for exactly the
        # reasons the credential delivery is, and NOT as a member of the start
        # REQUEST.
        #
        # The start request is a document boundary -- `boundaries.document`
        # takes exact built-in data and refuses anything carrying behaviour --
        # and that rule is right rather than in the way. A capability is not
        # data, and a delivery reduced to something that fits in a JSON
        # document would be a PATH: a caller-selected locator, which is the one
        # thing the fixed target exists to remove.
        #
        # So what crosses is a delivery that already exists, authored,
        # bounded, §13-walked and frozen by `launch.materialize`, and what this
        # adapter owns is composing exactly one read-only bind out of it.
        if launch_delivery is not None \
                and type(launch_delivery) is not launch.LaunchDelivery:
            _refuse(f"a launch delivery is one this manager materialized; "
                    f"this is {name_value(launch_delivery)}")
        self.launch_delivery = launch_delivery
        # W33936: DEPLOYMENT CONFIGURATION, held like the resolved identity
        # and the assignment roots -- assignment-scoped, fixed, and proved
        # when the adapter is built rather than at every call.  `None` is a
        # consent adapter, which is given none.
        #
        # REVIEW [P1]: A `WorkspaceGroup`, NEVER AN INTEGER. An integer is a
        # value any caller can compose, so typing it here validated shape and
        # membership and nothing else -- and membership is exactly what an
        # unrelated authority-bearing service group the manager belongs to
        # also has. This capability can only be obtained from
        # `workspaces.configured_workspace_group`, which reads the
        # deployment's own record, so holding one for group B means the
        # deployment configured B. The same rule the credential and launch
        # deliveries are already under, for the same reason: what crosses is a
        # thing the manager made rather than data describing one.
        if workspace_group is not None \
                and type(workspace_group) is not workspaces.WorkspaceGroup:
            _refuse(f"a workspace group is the deployment's configured one, "
                    f"read from this manager's own record; this is "
                    f"{name_value(workspace_group)}")
        self.workspace_group = workspace_group
        # W38956: THE NETWORK POSTURE AND THE CHANNEL, both assignment-scoped
        # construction and both defaulted to what this adapter did before they
        # existed. An adapter that names neither composes exactly the argv it
        # composed yesterday, which is what keeps every accepted case's meaning
        # unchanged -- a grant nobody asked for is the one thing a default must
        # never be.
        #
        # PROVED AT CONSTRUCTION rather than at the vector, for the reason
        # every other operand here is: an adapter that cannot say what it is
        # allowed to reach should not survive being built.
        self.network = _network(network)
        # `type(...) is not bool`, NOT `not in (True, False)`. Review [P2]:
        # membership compares by EQUALITY, and `0 == False` and `1 == True` in
        # Python -- so integers were accepted here and then met `run_vector`'s
        # exact `is True` / `is not False` test, which is a refusal composed
        # one layer later than the operand that caused it. Two checks of one
        # operand disagreeing about what it is, is how an adapter constructs
        # successfully and then cannot start.
        if type(interactive) is not bool:
            _refuse(f"an interactive channel is asked for or it is not; this "
                    f"is {name_value(interactive)}")
        self.interactive = interactive
        # W76207 re-review 2026-09-03T22:20:58Z [P1]: WHAT THIS ADAPTER
        # DECIDED ABOUT THE TWO MOUNTS, kept so a caller can read it.
        #
        # `_undelivered` already asks the engine which runtimes carry this
        # attempt's labels and settles or refuses to settle each delivery on
        # the answer -- and it said so only in the refusal PROSE its caller
        # composes. A deployment holding the same two roots therefore had no
        # way to know an owner had already decided, and unwound them itself:
        # a start that created a container and then failed left that container
        # running over a credential root and a launch document this manager
        # had just removed. Prose is not an API, so the answer is kept beside
        # the deliveries it is about.
        #
        # `None` MEANS NOBODY DECIDED, which is the case a caller must handle
        # itself: every exit that never reached the settlement -- an
        # unmountable root, a delivery belonging to another attempt, a refusal
        # raised before `start` was called at all -- leaves this untouched.
        self.settlement = None

    def _mounts_the_authorized_root(self, authorized):
        """The one input bind this delivery may carry, and it is the proved one.

        REQUIRED, not merely compared. `_mounts` already proves containment and
        writability, and none of that says WHICH of an assignment's two roots a
        bind names or where it lands -- the sibling workspace is contained and
        readable too, and `/inputs` is a target this manager never fixes.

        Three things have to be true and they are three different failures:

          exactly ONE bind lands at the worker's fixed `/input`, because two
          would leave the engine deciding which the worker reads;
          its SOURCE is the directory the manager authorized, canonically, so
          a second allowed root cannot stand in for the proved one; and
          it is READ-ONLY, because the input is the evidence the result is
          measured against and a runtime that could edit it could edit what it
          is judged by.

        AND ABSENCE IS DECIDED TOO. With no authorized root there is nothing a
        `/input` bind could be, so one is refused rather than passed through --
        an execution container exposing an unproved directory at the path the
        worker trusts is the whole defect, and "the manager did not say" is not
        a reason to allow it.
        """
        landing = []
        for mount in self.mounts:
            one = boundaries.document(mount, "a runtime mount",
                                      required=("source", "target", "writable"))
            if canonical_target(one["target"], "a mount target") \
                    == INPUT_TARGET:
                landing.append(one)
        if authorized is None:
            if landing:
                _denied(f"this delivery mounts {name_value(INPUT_TARGET)} and "
                        f"no input root was authorized for it; a worker reads "
                        f"its assignment from that path and this manager has "
                        f"proved nothing about what is there")
            return
        proved = canonical_source(authorized, "an authorized input root")
        if len(landing) != 1:
            _denied(f"this delivery lands {len(landing)} mounts on "
                    f"{name_value(INPUT_TARGET)} and an authorized input root "
                    f"is mounted exactly once; the engine would decide which "
                    f"one the worker reads")
        one = landing[0]
        source = canonical_source(one["source"], "a mount source")
        if source != proved:
            _denied(f"this delivery mounts {name_value(source)} at "
                    f"{name_value(INPUT_TARGET)} and the authorized input root "
                    f"is {name_value(proved)}; the root that was proved is the "
                    f"root that is mounted")
        if one["writable"] is not False:
            _denied(f"this delivery mounts the authorized input root writable; "
                    f"the input is the evidence the result is measured against")

    # -- the seam ------------------------------------------------------------

    def start(self, request):
        """Start one runtime and answer WHAT WAS STARTED, not that it worked.

        A duplicate start fails closed: the engine is asked what already
        carries these labels BEFORE anything is created, because two runtimes
        for one assignment is the state no later reconciliation can undo.
        """
        taken = boundaries.document(
            request, "a start request", required=("labels", "operation_id"),
            optional=("input_root",))
        labels = _labels(taken["labels"])
        boundaries.identity(taken["operation_id"], "an operation identity")
        # W19784 second review [P0]: THE ROOT THAT WAS AUTHORIZED IS THE ROOT
        # THAT IS MOUNTED, and until this existed those were two operations.
        #
        # The manager proved one directory named the live assignment, this
        # attempt and the claimed input digest -- and then called an adapter
        # whose mount plan is owned at CONSTRUCTION and independent of it. The
        # plan could omit the input root, name the sibling workspace, or land
        # an allowed source somewhere other than `/input`. Every one of those
        # starts a worker over material nothing authorized, and the proof said
        # nothing about it because it was about a different value.
        #
        # So the authenticated source crosses the seam and is required here,
        # BEFORE the vector is composed and therefore before the engine can
        # have created anything.
        self._mounts_the_authorized_root(taken.get("input_root"))
        # W26291 re-review [P1]: A START WITHOUT A LAUNCH DOCUMENT IS REFUSED
        # HERE, and until this existed the canonical seam could create exactly
        # the unrunnable reference worker this Work exists to fix.
        #
        # The operand is optional at CONSTRUCTION because the runtime half of
        # this adapter -- list, observe, stop, destroy, seal, collect -- is
        # constructible without one, exactly as `outputs` is. It is not
        # optional at START: a container launched with nothing at
        # `/run/baton/launch.json` cannot correlate a single thing it says, and
        # "the worker refuses it later" is a container that died rather than a
        # delivery this manager declined.
        #
        # THE LABELS MUST BE THIS ADAPTER'S OWN IDENTITY. A runtime labelled
        # with a profile or adapter digest other than the one it is started
        # under is a runtime reconciliation would describe wrongly for the
        # rest of its life -- and the manager would be reading that
        # description rather than the image.
        # THE DELIVERY'S OWN ATTEMPT, before anything else and WITHOUT
        # settling it. Fifth review [P1]: nothing compared the mounted root's
        # attempt with the runtime's label, so an attempt-2-labelled container
        # could mount attempt-1's credential root -- and reconciliation and
        # restart would then look for that delivery under an identity it was
        # never recorded against.
        #
        # THIS EXIT DOES NOT TEAR ANYTHING DOWN, and that is the point. The
        # settlement asks the engine which runtimes carry THESE labels, and
        # these are the wrong attempt's: an empty answer about attempt-2 says
        # nothing about whether attempt-1's runtime holds the mount. A refusal
        # that acted on it would be inferring absence from the wrong question.
        # W26291: THE SAME RULE FOR THE LAUNCH DOCUMENT. One delivery belongs
        # to one attempt, and a container labelled for attempt 2 that mounts
        # attempt 1's launch document would be answering under attempt 1's
        # session -- every frame on the worker-entry channel binds to it, so
        # the mismatch would surface as a worker refusing its own manager.
        if self.launch_delivery is not None \
                and self.launch_delivery.attempt_id \
                != labels["runtime_attempt_id"]:
            _denied(f"this start labels the runtime for attempt "
                    f"{name_value(labels['runtime_attempt_id'])} and carries "
                    f"the launch document of attempt "
                    f"{name_value(self.launch_delivery.attempt_id)}; one "
                    f"delivery belongs to one attempt")
        if self.credential_delivery is not None \
                and self.credential_delivery.attempt_id \
                != labels["runtime_attempt_id"]:
            _denied(f"this start labels the runtime for attempt "
                    f"{name_value(labels['runtime_attempt_id'])} and mounts "
                    f"the credential root of attempt "
                    f"{name_value(self.credential_delivery.attempt_id)}; one "
                    f"delivery belongs to one attempt, and the credential "
                    f"lifecycle is untouched because nothing here can prove "
                    f"anything about the other attempt's runtimes")
        # W26291 second re-review [P1]: A MISSING LAUNCH DOCUMENT REFUSES
        # THROUGH THE SETTLEMENT, not past it.
        #
        # This check used to sit above, calling `_denied` directly, with a
        # comment saying "nothing has been created yet, so there is nothing to
        # settle". That is true only when no OTHER provider has materialized
        # anything -- and a canonical adapter may already hold a credential
        # delivery whose root and live registration exist before `start` is
        # called at all. The refusal therefore stranded a bearer on a path
        # with no runtime id for the ordinary destroy crossing to name, which
        # is exactly the W26284 invariant this manager was corrected for once.
        #
        # AND IT SITS AFTER BOTH ATTEMPT CHECKS, deliberately. `_refused_start`
        # settles by asking which runtimes carry THESE labels, so a delivery
        # belonging to a different attempt must refuse ABOVE this line: an
        # empty answer about attempt 2 says nothing about attempt 1's runtime,
        # and acting on it would be inferring absence from the wrong question.
        if self.launch_delivery is None:
            self._refused_start(
                labels,
                f"this start carries no launch document; the worker reads "
                f"what it is from {name_value(launch.LAUNCH_TARGET)}, and a "
                f"container started without one cannot correlate anything it "
                f"says")
        for name in _LABELLED_IDENTITY:
            if labels[name] != self.identity[name]:
                self._refused_start(
                    labels,
                    f"this start labels the runtime "
                    f"{name_value(labels[name])} for {name} and the "
                    f"resolved identity is "
                    f"{name_value(self.identity[name])}; one delivery "
                    f"carries one identity, and a label that disagrees "
                    f"with what is started is what reconciliation would "
                    f"believe afterwards")
        existing = self.list({"labels": labels})
        if existing:
            self._refused_start(
                labels,
                f"{len(existing)} runtime(s) already carry these assignment "
                f"labels; starting another would compound it")
        # EVERYTHING FROM HERE TO THE ENGINE IS A REFUSING EXIT TOO.
        #
        # Fifth review [P1]: `_refused_start` covered the checks above and the
        # engine's own answer, and a `ContractRefusal` raised while COMPOSING
        # the vector went straight past it -- a mount collision, a malformed
        # operation id, an unmountable delivery. Those are the exits where the
        # duplicate probe has already proved the candidate set empty, so they
        # are the ones where settling is both safe and most obviously owed.
        try:
            # W33936 review [P0]: THE ROOT IS PROVED IMMEDIATELY BEFORE THE
            # ENGINE, and argv is not the proof.
            #
            # `--group-add` grants the container a share in a group. It says
            # nothing about the directory the engine is about to bind, and a
            # root whose group was changed after allocation -- by a restart
            # under a different configuration, by an operator, by a
            # redeployment -- produces a container holding a group its
            # workspace does not carry. That fails at the WORKER, mid-work,
            # with an assignment already live; here it is an ordinary refusal
            # with nothing started.
            #
            # EXECUTION ONLY, because consent mounts nothing and holds no
            # group: there is no root for it to be about.
            if self.posture == "execution":
                if self.workspace_group is None:
                    _denied(
                        "an execution runtime is given the deployment's "
                        "configured workspace group and this adapter holds "
                        "none; without it the worker holds no share in its own "
                        "workspace and cannot write the outputs this "
                        "assignment requires it to declare")
                workspaces.prove_workspace_group(
                    self.assignment_roots["workspace"],
                    self.workspace_group.gid,
                    what="this assignment's workspace root")
            delivered = (self.credential_delivery.mounts()
                         if self.credential_delivery is not None else ())
            argv = run_vector(
                self.engine, image_digest=self.image_digest, labels=labels,
                assignment_roots=self.assignment_roots, posture=self.posture,
                mounts=self.mounts, credentials_delivered=delivered,
                launch_delivered=(self.launch_delivery.mount()
                                  if self.launch_delivery is not None
                                  else None),
                name=_runtime_name(taken["operation_id"]),
                workspace_group=self.workspace_group,
                network=self.network, interactive=self.interactive)
        except ContractRefusal as refusal:
            self._refused_start(labels, refusal.message)
        # FROM HERE THE ENGINE MAY ALREADY HAVE CREATED SOMETHING.
        #
        # Sixth review [P1]: the guard above stopped at the vector, so the run
        # itself, the reading of its answer and the ownership of the returned
        # identity all escaped without a lifecycle decision -- and those are
        # precisely the exits where a container may exist. The caller got a
        # refusal with no `torn-down` or `unresolved` in it, and nothing asked
        # the engine whether anything was holding the mount.
        try:
            answer = self.run(argv)
            if answer["status"] != 0:
                _denied(f"the engine refused to start this runtime: "
                        f"{name_value(answer['stderr'][:MAX_DIAGNOSTIC])}")
            runtime_id = answer["stdout"].strip()
            if runtime_id:
                boundaries.identity(runtime_id, "a started runtime id")
        except ContractRefusal as refusal:
            self._refused_start(labels, refusal.message)
        if not runtime_id:
            # THE ENGINE SAID NOTHING. That is not "started something unnamed";
            # it is an answer this adapter cannot turn into an identity, and
            # inventing one would make every later comparison meaningless.
            #
            # AND IT IS A FAILURE ENDING FOR THE CREDENTIAL TOO. There is no
            # runtime id to write a lifecycle record against, so nothing later
            # could ever adopt or tear this delivery down by name -- the whole
            # reason the record is written after the engine answers.
            # W26291 re-review [P1]: AND FOR THE LAUNCH DOCUMENT TOO, for the
            # same reason and on the same evidence -- two manager-owned mounts,
            # two named endings, one absence question.
            return {"runtime_id": None, "labels": None,
                    **self._undelivered(labels)}
        # THE LIFECYCLE RECORD, WRITTEN ONLY ONCE THERE IS A RUNTIME TO NAME.
        # It exists so a restarted manager can prove the attempt, container,
        # mount and root agree before it adopts anything; a record written
        # before the engine answered would name a container that may not have
        # started, which is the one thing adoption must not believe.
        #
        # AND ITS FAILURE IS A POST-CREATE EXIT LIKE THE OTHERS. A container is
        # running by now, so a record this manager cannot publish leaves a
        # delivery nothing can later adopt or name -- which is exactly the
        # state the settlement exists to report rather than to leak.
        if self.credential_delivery is not None:
            try:
                self._credential_home().written_state(
                    self.credential_delivery.attempt_id,
                    self.credential_delivery.record(runtime_id=runtime_id))
            except ContractRefusal as refusal:
                self._refused_start(labels, refusal.message)
        return {"runtime_id": runtime_id, "labels": labels}

    def recover_credentials(self, request):
        """W6634: restart recovery, against the LIVE runtime or not at all.

        Fourth review [P1], twice over. Adoption compared a self-authored
        record with locally derived paths and its own files -- document
        consistency rather than the approved boundary -- and nothing in
        production called it, `read_state` or `discard_orphans` at all. A
        recovery path that exists only in a test is a recovery path this
        manager does not have.

        THE APPROVED BOUNDARY, in the order it is written: recovery is admitted
        only when the ATTEMPT, the CONTAINER, the MOUNTS and the ROOT all
        agree. Three of those four are facts about a live container, so three
        of them come from the engine and are compared here; the record supplies
        what was intended and the engine supplies what is.

        AND THE DISAGREEMENT PATH IS THE POINT. It fails closed, accepts no
        output, stops the worker and performs bounded orphan cleanup -- and
        the cleanup is conditional on the stop being PROVED, because removing a
        mount source out from under a container this manager cannot say is gone
        is the one act worse than leaving it.
        """
        taken = boundaries.document(request, "a credential recovery request",
                                    required=("attempt_id", "assignment",
                                              "context"))
        attempt = boundaries.identity(taken["attempt_id"],
                                      "a credential attempt id")
        # THE ASSIGNMENT IS OWNED AT THIS DOOR rather than inside the helper
        # that composes the labels. A private helper's parameters are internal
        # values of the operation that called it -- owning them there would be
        # a second owner for one crossing, and the boundary inventory reports
        # the helper's rules as owning nothing.
        expect = boundaries.document(taken["assignment"],
                                     "a recovery assignment",
                                     required=("work_ref", "participant",
                                               "generation"))
        work = boundaries.document(expect["work_ref"], "a recovery work ref",
                                   required=("authority_uuid", "work_id"))
        # W16823: THE TRUSTED CONTEXT, owned at this door beside the
        # assignment and for the same reason -- it is now part of the label set
        # this recovery SELECTS on, so a recovery carrying the wrong principal
        # would list nothing and conclude a delivery was never made.
        context = boundaries.document(taken["context"],
                                      "a recovery authorization context",
                                      required=LABEL_CONTEXT)
        home = self._credential_home()
        record = home.read_state(attempt)
        labels = self._attempt_labels(attempt, expect, work, context)
        if record is None:
            # NOTHING TO ADOPT IS NOT NOTHING TO DO. A root with no record is
            # an attempt that was materialized and never launched, or one whose
            # record this manager already removed; either way no live delivery
            # owns it, so it is exactly what bounded orphan cleanup is for.
            # ONLY THIS ATTEMPT'S ROOT. A `CredentialHome` is
            # assignment-scoped and can hold sibling attempts, and "attempt-1
            # has no record" is not evidence about attempt-2.
            return {"lifecycle_state": "absent",
                    "orphans": home.discard_orphan(attempt)}
        existing = self.list({"labels": labels})
        if len(existing) != 1:
            # AMBIGUOUS, so nothing here is exactly identified and nothing is
            # acted on. M60437 / W32385.
            return self._recovery_failed(
                home, attempt, existing,
                f"{len(existing)} runtime(s) carry this attempt's labels; "
                f"recovery adopts one exactly identified container and "
                f"refuses every other count")
        runtime_id = existing[0]["runtime_id"]
        if record["runtime_id"] != runtime_id:
            # MISMATCHED, likewise: the engine's live runtime is not the one
            # this manager's own record names.
            return self._recovery_failed(
                home, attempt, existing,
                f"the live runtime is {name_value(runtime_id)} and the "
                f"lifecycle record names {name_value(record['runtime_id'])}")
        observed = self.observe(runtime_id)
        disagreement = _mounts_disagree(observed["mounts"], record)
        if disagreement is not None:
            # EXACTLY IDENTIFIED. The labels and the record agree on WHICH
            # runtime this is; what disagrees is what it has mounted. This is
            # the one candidate the ruling permits stopping.
            return self._recovery_failed(home, attempt, existing,
                                         disagreement, exact=runtime_id)
        # EVERY IDENTITY AGREED, so the record may now be believed about the
        # one thing the engine cannot answer: which bearer belongs to which
        # slot. `adopt` re-registers from this manager's own files.
        # W52800: RECOVERY PROVES THE RULED SLOT, so it needs the same grant
        # the start composed `--group-add` from. This adapter already holds it
        # -- it is the one it validated at construction -- so the two halves of
        # the grant are one capability rather than two lookups.
        return {"lifecycle_state": "adopted", "runtime_id": runtime_id,
                "delivery": home.adopt(record, attempt_id=attempt,
                                       runtime_id=runtime_id,
                                       workspace_group=self.workspace_group)}

    def _recovery_failed(self, home, attempt, existing, why, *, exact=None):
        """Fail closed: no output, stop only what is exactly identified,
        bounded orphan cleanup.

        THE ORDER MATTERS AND THE CLEANUP IS CONDITIONAL. A stop this adapter
        cannot prove leaves a container that may still be reading the mount, so
        the attempt's own root stays LIVE for the cleanup pass and the refusal
        says the credential lifecycle is unresolved. Reporting a clean ending
        there would be exactly the cleanup uncertainty the ruling forbids.

        AND `exact` IS WHAT MAY BE STOPPED AT ALL. W55758 review
        (2026-09-01T10:56:54Z) [P1]: this stopped EVERY candidate it had
        listed, including the ambiguous and mismatched ones. W32385's
        signed-off restart contract and M60437 both say identity mismatch,
        multiplicity and observation uncertainty fail closed WITHOUT removing
        unrelated candidates -- so only the caller that proved one identity
        exactly names it here, and every other runtime is left where it is and
        reported. W6634's stop-every-candidate wording is a terminal
        non-satisfying spike's provisional text, not the live rule.

        WHAT IS LEFT BEHIND TRAVELS WITH THE REFUSAL. Automatic reconciliation
        of an unknown runtime is out of scope for initial v12, which makes the
        REPORT the deliverable: each surviving candidate is observed once more
        after the stop and carried as its own exact locator, state and reason.
        """
        stopped = []
        for entry in existing:
            if entry["runtime_id"] != exact:
                continue
            answer = self.stop({"runtime_id": entry["runtime_id"],
                                "operation_id": f"runtime.stop:{attempt}"})
            stopped.append(answer["state"] == "absent")
        # ZERO CANDIDATES IS POSITIVE ABSENCE, not an unproved stop.
        #
        # Seventh review [P1]: `bool(stopped) and all(stopped)` is False for an
        # empty list, so a stale record whose exact engine query returned
        # nothing reported UNRESOLVED and kept both the root and the record --
        # and every later recovery repeated it. That is the same
        # non-convergence the last round corrected one layer up, arriving
        # through an empty-sequence idiom instead.
        #
        # A SUCCESSFUL query that names no runtime is the engine answering
        # about this exact attempt: there is nothing to stop, so nothing can be
        # holding the mount, and targeted cleanup may settle it. `list` refuses
        # rather than returning empty when it could not ask, so an empty answer
        # here is an answer.
        #
        # AND AN EMPTY `stopped` NO LONGER MEANS ABSENCE ON ITS OWN, because
        # this method now declines to stop candidates it may not touch. The
        # zero-candidate answer is still positive absence; a candidate left
        # standing is not.
        gone = all(stopped) if stopped else not existing
        orphans = (home.discard_orphan(attempt) if gone
                   else {"discarded": [], "remaining": 1, "bounded": False})
        left = [seen for seen in (self._left_behind(entry["runtime_id"])
                                  for entry in existing)
                if seen["state"] != "absent"]
        refusal = ContractRefusal(
            "refused", "precondition",
            f"this attempt cannot be recovered: {why}. No output is accepted, "
            f"{len(stopped)} exactly identified runtime(s) were stopped and "
            f"{len(left)} were left untouched and reported, and the "
            f"credential lifecycle is "
            f"{'settled by cleanup' if gone else 'UNRESOLVED'} after "
            f"discarding {len(orphans['discarded'])} orphaned root(s)")
        # THE EVIDENCE RIDES THE REFUSAL, because the refusal is the only
        # thing this operation returns to a caller that has to write the
        # recovery record. Both members are absent-safe on purpose: a caller
        # reading them off any other refusal gets nothing rather than a guess.
        refusal.runtime_zombies = tuple(left)
        refusal.stopped_runtime = exact if stopped else None
        raise refusal

    def _left_behind(self, runtime_id):
        """One runtime this refusal is leaving on the host, as the engine
        sees it AFTER the stop that was or was not issued.

        AN UNREADABLE ANSWER IS `uncertain` RATHER THAN A SECOND REFUSAL. This
        runs inside the composition of a refusal that already has its reason,
        and letting an engine's malformed answer about a bystander replace it
        would lose the account of what this recovery actually did.
        """
        try:
            seen = self.observe(runtime_id)
        except ContractRefusal as unreadable:
            return {"runtime_id": runtime_id, "state": "uncertain",
                    "why": f"the engine's answer about this runtime could "
                           f"not be read: "
                           f"{unreadable.message[:MAX_DIAGNOSTIC]}"}
        return {"runtime_id": runtime_id, "state": seen["state"],
                "why": seen["why"]}

    def _attempt_labels(self, attempt_id, expect, work, context):
        """The frozen label set that selects THIS attempt's runtimes.

        The same composition `_quiesced` performs: the request carries the
        attempt, the four parts of the assignment and W16823's trusted
        authorization context, and this adapter has owned the three resolved
        digests since construction. Every operand arrives already proved -- see
        the caller.
        """
        return documents.runtime_labels(
            runtime_attempt_id=attempt_id,
            authority_uuid=work["authority_uuid"],
            work_id=work["work_id"],
            participant=expect["participant"],
            generation=expect["generation"],
            principal=context["principal"],
            effective_scope=context["effective_scope"],
            profile_digest=self.identity["profile_digest"],
            policy_digest=self.identity["policy_digest"],
            adapter_digest=self.identity["adapter_digest"])

    def _refused_start(self, labels, why):
        """Refuse a start AND settle the credential it was going to deliver.

        EVERY refusing exit from `start` comes through here, because the
        materialization happened before this adapter was built: a start that
        raises without settling leaves a volatile root and a live registration
        that the single `destroy` path can never reach, since there is no
        runtime id to name them by. The fourth review found one such exit; the
        duplicate-start and disagreeing-label exits are the same shape and are
        corrected with it rather than after the next review.
        """
        # W55758 review [P1]: this exit has no destroy command and therefore
        # no `runtime_attempt_id` to bind an orphan teardown against. A start
        # this adapter never completed is not a path an unbound credential
        # ending may ride on, so it is refused rather than performed -- and it
        # is unreachable in practice, because a recovery adapter starts
        # nothing.
        self._bound_orphan(None, "a refused-start")
        settled = self._undelivered(labels)
        _denied(f"{why}; the credential delivery is "
                f"{settled['credentials']['lifecycle_state']} and the launch "
                f"document is {settled['launch']['lifecycle_state']}")

    def _undelivered(self, labels):
        """W6634: the credential ending for a start that produced no runtime.

        THE ANSWER IS KEPT ON THIS ADAPTER as well as returned, because the
        caller that composes the refusal is not the only one that needs it:
        see `settlement` for the deployment this was invisible to.

        Fourth review [P1]: a start the engine declined raised immediately, so
        the volatile root and the live registration stayed while no runtime id
        and no lifecycle record existed. The single `destroy` path this Work
        claims cannot reach a delivery it cannot name, so that bearer was
        stranded for the life of the process.

        THE ORDER IS STILL THE APPROVED ONE, which is why this cannot simply
        tear down: the registry is released only after nothing can be reading
        the mount. A declined start is strong evidence that nothing does, and
        it is not proof -- an engine can create a container and then fail, and
        it can fail while answering nothing about what it created. So this
        ASKS: if no runtime carries this attempt's labels, no runtime can hold
        the mount and the delivery settles; anything else is `unresolved`.

        UNRESOLVED IS AN ANSWER, NOT A FAILURE TO ANSWER. The caller's refusal
        carries it, so a start that failed and left a live credential is
        distinguishable from one that failed cleanly -- which is exactly what
        "cleanup uncertainty is not settlement" requires.
        """
        self.settlement = self._settling(labels)
        return self.settlement

    def _settling(self, labels):
        """The settlement itself. Split from the recording above so that every
        one of its exits is kept without repeating the assignment at each."""
        # ONE LISTING, TWO ENDINGS. W26291 re-review [P1]: the launch root had
        # no ending at all, so a refused start left it behind -- and it is not
        # the credential's dependent, because a delivery with no credential
        # still has a launch document. The absence question is asked once and
        # both mounts are settled on the answer.
        undelivered = {"lifecycle_state": "not-delivered"}
        # W55758: an orphan teardown is a credential ending exactly as a
        # delivery is, so it counts here too -- a start that never completed
        # for an attempt whose material this deployment can name still has
        # something to settle.
        held = (self.credential_delivery is not None
                or self.credential_orphan is not None)
        if not held and self.launch_delivery is None:
            return {"credentials": undelivered, "launch": undelivered}
        why = None
        try:
            existing = self.list({"labels": labels})
        except ContractRefusal as refusal:
            why = refusal.message
        else:
            if existing:
                why = (f"{len(existing)} runtime(s) carry this attempt's "
                       f"labels after a start this adapter did not complete, "
                       f"and any of them may hold the mount")
        launched = self._launch_ended(why is None, why)
        if why is not None:
            return {"credentials": ({"lifecycle_state": "unresolved",
                                     "why": why} if held else undelivered),
                    "launch": launched}
        if not held:
            return {"credentials": undelivered, "launch": launched}
        if self.credential_delivery is None:
            return {"credentials": self.credential_orphan.tear_down(),
                    "launch": launched}
        return {"credentials": self._credential_home()
                                   .tear_down(self.credential_delivery),
                "launch": launched}

    def _launch_ended(self, proved_absent, why):
        """W26291 re-review [P1]: the launch root's ONE ending.

        `launch.discard` existed and nothing production ever called it, so a
        refused start and a runtime proved absent both left an attempt-private
        root and a world-readable document behind for good -- unbounded manager
        storage, and an implementation claim that was simply false.

        DISCARDED ONLY ON THE EVIDENCE THAT NOTHING CAN HOLD THE MOUNT, which
        is why this is called from the two places that establish it rather than
        from `destroy` or `_refused_start` directly. A document removed under a
        container that may still be reading it is an ending reported before it
        happened -- the same rule the credential root is held to, on the mount
        beside it.

        Answers a state rather than nothing, so a caller can tell a launch
        document that ended from one that was never delivered.
        """
        if self.launch_delivery is None:
            # NOT `absent`, which is what the RUNTIME state beside this says.
            # One word meaning two things in one document is how a reader
            # concludes a launch document was removed because a container was.
            return {"lifecycle_state": "not-delivered"}
        if not proved_absent:
            return {"lifecycle_state": "unresolved", "why": why}
        if launch.discard(self.launch_delivery.root):
            return {"lifecycle_state": "torn-down"}
        return {"lifecycle_state": "unresolved",
                "why": f"the launch root "
                       f"{name_value(self.launch_delivery.root)} is still "
                       f"present after removal"}

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
            labels_of = self._labels_of(entry)
            # THE RUNNING IMAGE, AND IT IS THE ENGINE'S OWN FACT.
            #
            # Review [P1]: the image account was one-way. It chose the start
            # argv and was never asked about again, so a restarted adapter
            # resolved to image B adopted a runtime the engine says is running
            # image A the moment its profile and adapter labels still matched
            # -- and everything downstream then reasoned about B while A was
            # running.
            #
            # Read from the LISTING rather than from a label, because a label
            # is what this manager wrote about a delivery and the engine's
            # record is what is actually running. The two are only the same
            # while nobody has lied or replaced anything, which is precisely
            # the case reconciliation exists for.
            image = _image_identity(
                _one_of(entry, _LISTED_IMAGE, "an engine listing entry"),
                "a listed runtime's image")
            resolved = _image_identity(self.identity["image_digest"],
                                       "the resolved image")
            if image != resolved:
                _denied(f"runtime {name_value(runtime_id)} carries this "
                        f"assignment's labels and the engine reports it "
                        f"running a different image than the one this "
                        f"delivery resolved; one delivery carries one "
                        f"identity, and labels alone cannot make a stale "
                        f"image this adapter's runtime")
            # THE COMPLETE RETURNED RECORD, against the record that was
            # ASKED FOR.
            #
            # Review [P0]: engine-side selection is not proof that a returned
            # row has the values requested. A compatible engine may ignore a
            # filter, engine state may be stale or hand-edited, and -- now
            # that only the attempt id selects -- every other member arrives
            # unchecked unless this says otherwise. A candidate that carries
            # this attempt id and contradicts the request is WRONG, not
            # absent, and refusing it here is what stops `start` reading an
            # empty set and creating a duplicate.
            for name in documents.RUNTIME_LABELS:
                if labels_of[name] != labels[name]:
                    _denied(f"runtime {name_value(runtime_id)} carries this "
                            f"attempt's id and is labelled "
                            f"{name_value(labels_of[name])} for {name} where "
                            f"this delivery asked for "
                            f"{name_value(labels[name])}; one delivery "
                            f"carries one identity")
            # AND THE LABELLED HALF OF THE RESOLVED IDENTITY, which is a
            # different question: the loop above asks whether this runtime is
            # the one the CALLER named, and this asks whether it is the one
            # THIS ADAPTER resolved. `list` is reachable without `start`, so
            # neither implies the other.
            for name in _LABELLED_IDENTITY:
                if labels_of[name] != self.identity[name]:
                    _denied(f"runtime {name_value(runtime_id)} is labelled "
                            f"{name_value(labels_of[name])} for {name} and "
                            f"this delivery resolved "
                            f"{name_value(self.identity[name])}; one delivery "
                            f"carries one identity")
            found.append({"runtime_id": runtime_id, "labels": labels_of})
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

    def destroy(self, command):
        """Remove one runtime and PROVE it is gone.

        W6629 review [P1]: this took a bare runtime id, so the manager's whole
        `runtimeDestroyBody` -- the assignment, the attempt, the intake receipt
        digest and the retention policy digest that AUTHORIZE the destruction
        -- stopped at the boundary. The body crosses now.

        NOTHING IN IT IS INTERPRETED HERE. This core answers facts about an
        engine and decides nothing: the identity is what it acts on, and the
        rest is the manager's authorization travelling with its command rather
        than being reconstructed on this side.
        """
        # W6636: THE OPERATION RIDES BESIDE THE BODY, and this contract has to
        # say so. `intake.authorize_cleanup` delivers
        # `{**destroy_command(...), "operation": ...}` -- which this very
        # docstring describes -- while the member list named only the body, and
        # `boundaries.document` refuses an unrecognised member rather than
        # ignoring it. So the composed lifecycle refused at the destroy
        # crossing, one step past the retention seam that was missing
        # altogether. Surfaced by composing the arc; invisible to either side's
        # own suite, because each was right about its own half.
        taken = boundaries.document(command, "a destroy command",
                                    required=documents.DESTROY_COMMAND,
                                    optional=("operation",))
        return self._removed(taken["runtime_id"], "a destroyed",
                             attempt_id=taken["runtime_attempt_id"])

    def destroy_failed_start(self, command):
        """W34998: remove the runtime a FAILED START created, and prove it.

        A start that reached the engine, created a container and then failed
        leaves an exact runtime and NO INTAKE RECEIPT -- nothing was frozen,
        collected or admitted, so there is no receipt to authorize a removal
        with. `destroy` requires one, correctly, so this ending had no way
        through it at all: that is the gap approver ruling M34998/M34999
        creates this method to close.

        A SIBLING, AND DELIBERATELY NOT A UNION. `destroy` does not learn to
        accept this body and this does not fall back to `destroy`. A receiver
        that took either would let a caller authorize a removal with whichever
        digest it happened to be holding -- and the two digests mean opposite
        things: a receipt says material was taken into custody under a policy,
        a failure record says a start did not happen. Keeping the member sets
        closed is what makes a cross-called body a refusal rather than a
        silently accepted authorization.

        THE SAME CORE, ONE STEP LATER. What follows the body -- force-remove
        the exact identity, observe it, settle the credential and launch
        deliveries on positive absence and only on that -- is `_removed`,
        shared with `destroy` rather than written twice. Two implementations of
        an ordered teardown are two orders that agree until they do not.

        AND NOTHING HERE TOUCHES THE RESULT DIRECTORY. The unique directory a
        failed start left behind was created untrusted and stays in place
        untrusted: this method does not read, copy, validate, freeze, collect,
        admit, quarantine or delete it. W32648 owns what becomes of it.
        """
        taken = boundaries.document(
            command, "a failed-start destroy command",
            required=documents.FAILED_START_DESTROY_COMMAND,
            optional=("operation",))
        return self._removed(taken["runtime_id"], "a failed-start",
                             attempt_id=taken["runtime_attempt_id"])

    def destroy_refused_session(self, command):
        """W32576: remove the runtime a REFUSED HANDSHAKE leaves running.

        THE THIRD SIBLING, and a sibling for the reason the second one is. A
        session that answered a wire version this manager never certified has
        no intake receipt -- nothing was frozen, collected or admitted -- and
        it is not a failed start either: the container is RUNNING, and running
        an agent this manager cannot speak to. Neither existing body describes
        that, and a receiver that accepted whichever body arrived would let a
        caller spend one ending's authorization on another's.

        THE SAME CORE, AND THE SAME ORDER. `_removed` force-removes the exact
        identity, observes it, and settles the credential and launch
        deliveries on positive absence and only on that. Running is not a
        different teardown; it is the same teardown, and `docker rm --force`
        is what makes it one.

        AND NOTHING HERE TOUCHES THE RESULT DIRECTORY. Whatever the worker
        wrote before the handshake refused was written by a worker this
        manager never negotiated with, so it began untrusted and stays
        untrusted and in place. W32576 owns what becomes of it.
        """
        taken = boundaries.document(
            command, "a refused-session destroy command",
            required=documents.REFUSED_SESSION_DESTROY_COMMAND,
            optional=("operation",))
        return self._removed(taken["runtime_id"], "a refused-session",
                             attempt_id=taken["runtime_attempt_id"])

    # -- W43975: the typed directory-custody seam ---------------------------

    @property
    def custodian_image_digest(self):
        """The identity of the helper THIS adapter would run a custody act as.

        Exposed as a read rather than left to a caller to fish out of
        `identity`, because it is a SIGNATURE input for the per-root receipt:
        a changed custodian must collide rather than replay an answer about a
        different helper.
        """
        return self.identity["image_digest"]

    def normalize_directory(self, store, *, assignment_id, which):
        """Normalize ONE of this attempt's roots, composed entirely in here.

        W43975 review 2026-08-30T11:32:34Z: `intake.py` must not reach through
        a nominally generic adapter to its `engine`, `run` and `image_digest`
        fields to compose a custody act. Those are this object's, so the act
        is composed here and what crosses the seam is a typed call and a
        `CustodyAnswer`.

        THE STORE CROSSES AND IS NOT HELD. `custody_act` performs its own
        durable lookup in the same act that mounts, which is the property
        eleven review rounds bought; this adapter holds no store and no path.
        """
        from . import custody as _custody

        return _custody.custody_act(
            self.engine, self.run, image_digest=self.custodian_image_digest,
            store=store, assignment_id=assignment_id,
            operation="normalize", which=which)

    def destroy_abandoned(self, command):
        """W44716: remove the runtime an ABANDONED attempt leaves running.

        THE FOURTH SIBLING, on the rule that made the second and third.
        Approver ruling 2026-08-30. A runtime that started and whose worker
        then never answered has no intake receipt, no failed-start record and
        no refusal record -- the start succeeded, the handshake was never
        refused, and nothing was frozen or collected. What authorizes this is
        an OPERATOR'S declaration that the attempt is abandoned, and its own
        closed body says so rather than borrowing one of the other three.

        THE SAME CORE, AND THE SAME ORDER. `_removed` force-removes the exact
        identity, observes it, and settles the credential and launch
        deliveries on positive absence and only on that. The container is
        RUNNING here, as it is for a refused session, and `docker rm --force`
        is what makes running and stopped one teardown rather than two.

        AND NOTHING HERE TOUCHES THE RESULT DIRECTORY. Whatever the worker
        wrote before it stopped answering was written by a worker this manager
        never heard from, so it began untrusted and stays untrusted and in
        place -- the same rule M33800 set for the siblings.
        """
        taken = boundaries.document(
            command, "an abandoned-attempt destroy command",
            required=documents.ABANDONED_DESTROY_COMMAND,
            optional=("operation",))
        return self._removed(taken["runtime_id"], "an abandoned-attempt",
                             attempt_id=taken["runtime_attempt_id"])

    def _removed(self, named, what, *, attempt_id=None):
        """Force-remove one exact identity and answer what became of it.

        NOTHING IN THE COMMAND IS INTERPRETED HERE. This core answers facts
        about an engine and decides nothing: the identity is what it acts on,
        and the rest of either body is the manager's authorization travelling
        with its command rather than being reconstructed on this side.

        A LITERAL IN THE LABEL, even though the noun is the caller's. A shared
        owner that served two crossings with `what` alone would carry a label
        the boundary inventory cannot attribute and a probe cannot assert --
        which the inventory said in as many words the moment this helper was
        factored. The caller names WHICH command it is; the literal says what
        the value is.
        """
        runtime_id = boundaries.identity(named, f"{what} runtime id")
        # W55758 review (2026-09-01T04:57:06Z) [P1]: THE CREDENTIAL TARGET IS
        # BOUND TO THIS REMOVAL'S OWN ATTEMPT, and it is bound BEFORE the
        # engine is called.
        #
        # An `OrphanTeardown` carries its own attempt id and this adapter
        # checked only its nominal type, so a recovery built over one
        # assignment's roots with another attempt's teardown removed that
        # OTHER attempt's real credential material on positive absence.
        # Nothing in the path compared the two. Every destroy command already
        # names `runtime_attempt_id`; this is where that name becomes
        # load-bearing.
        #
        # BEFORE THE REMOVAL, because a refusal after the engine has acted is
        # not a refusal -- the mismatched attempt's container would already be
        # gone, and the wrong credential would be next.
        self._bound_orphan(attempt_id, what)
        self.run(destroy_vector(self.engine, runtime_id=runtime_id))
        observed = self.observe(runtime_id)
        return {"runtime_id": runtime_id, "state": observed["state"],
                "why": observed["why"],
                "credentials": self._torn_down(observed),
                # W26291 re-review [P1]: TWO MOUNTS, TWO ENDINGS, ONE PROOF.
                # The launch document is a separate manager-owned root and had
                # none at all, so a destroyed runtime left it behind for good.
                # It is settled on the SAME absence evidence and reported
                # beside the credential ending rather than folded into it: a
                # delivery with no credential still has a launch document.
                "launch": self._launch_ended(observed["state"] == "absent",
                                             observed["why"])}

    def _bound_orphan(self, attempt_id, what):
        """W55758: the orphan teardown acts for THIS attempt or not at all.

        A `Delivery` needs no such check -- `start` already refuses one whose
        attempt disagrees with the runtime it is delivering to -- but an
        orphan teardown is constructed from durable facts by a recovery, so
        the only thing tying it to a removal is this comparison. Without it
        the type was the whole check, and a type is not an identity.

        AN UNNAMED ATTEMPT REFUSES TOO. A removal that cannot say which
        attempt it is for is not one an exact credential ending may ride on,
        and every destroy command this adapter reads names one.
        """
        if self.credential_orphan is None:
            return
        if attempt_id is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} removal names no attempt and this adapter holds an "
                f"orphan credential teardown for "
                f"{name_value(self.credential_orphan.attempt_id)}; an ending "
                f"that cannot say whose material it is removing is not one "
                f"this manager performs")
        named = boundaries.identity(attempt_id, f"{what} runtime attempt id")
        if named != self.credential_orphan.attempt_id:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what} removal is for attempt {name_value(named)} and this "
                f"adapter's orphan credential teardown is for "
                f"{name_value(self.credential_orphan.attempt_id)}; one "
                f"attempt's ending never removes another's material")

    def _torn_down(self, observed):
        """W6634: the credential ending, ordered AFTER container removal.

        THE ORDER IS THE APPROVED ONE, and each step is a precondition of the
        next rather than a preference: the registry is held through quiescence,
        immutable staging and the leak checks; then the container is removed;
        then the credential root; and the in-memory bearer is discarded only
        once all of that is proved.

        SO A RUNTIME THAT IS NOT PROVED GONE STOPS THIS. A container this
        manager cannot say is absent may still be reading the mount, and
        removing the file under it would be reporting an ending that has not
        happened. `unresolved` is what this answers then -- never a state a
        caller can read as settlement, because `destroy`'s own `state` is
        already `uncertain` beside it.

        ONE ACT ON EVERY ENDING. Success, failure and cancellation all arrive
        here, because `destroy` is what runs on all three; there is no second
        teardown path that a cancellation could take instead and that could
        drift from this one.
        """
        if self.credential_delivery is None:
            # W55758: AND `not-delivered` IS A CLAIM, so it is only made when
            # nothing durable contradicts it.
            #
            # A recovery process is exactly the shape in which the in-memory
            # delivery is gone, and this answered `not-delivered` there --
            # positively recording that no credential was ever delivered for
            # an attempt whose bearer had been on the host for hours. The word
            # is deliberately not `absent` so a reader cannot conclude a
            # credential was torn down because a container was; unqualified it
            # made the opposite mistake, and no reader could tell that record
            # from a genuine no-credential attempt.
            #
            # An orphan teardown is the deployment saying, from durable facts,
            # that this attempt HAD one. With it the ending is a real ending;
            # without it, nothing was ever delivered and the old word is true.
            if self.credential_orphan is None:
                # NOT `absent`, which is what the RUNTIME state beside this
                # says. One word meaning two things in one document is how a
                # reader concludes a credential was torn down because a
                # container was.
                return {"lifecycle_state": "not-delivered"}
            if observed["state"] != "absent":
                return {"lifecycle_state": "unresolved",
                        "why": observed["why"]}
            return self.credential_orphan.tear_down()
        if observed["state"] != "absent":
            return {"lifecycle_state": "unresolved",
                    "why": observed["why"]}
        return self._credential_home().tear_down(self.credential_delivery)

    def seal(self, request):
        """W6634: the sealed result `output.request_freeze` asks for.

        Thin on purpose. The measurement, the quiescence gate and the frozen
        result's shape live in `sealing.py`, which is this Work's file; this
        method is the seam the manager already types as a capability.
        """
        self._quiesced(request)
        return sealing.sealed_result(
            request, roots=self.assignment_roots,
            declared=self.declared_outputs, identity=self.identity,
            custody=self._custody(request["attempt_id"]),
            input_manifest_digest=self.input_manifest_digest)

    def _custody(self, attempt_id):
        """Where this manager keeps the bytes it has taken custody of.

        A SIBLING of the assignment's roots and deliberately NOT one of them:
        `ROOT_NAMES` is the contract for what a container may MOUNT, and
        custody is precisely the material the worker must not be able to reach
        after it is frozen. Adding it there would hand the worker its own
        evidence back.
        """
        return os.path.join(self._home(), "custody", attempt_id)

    def _credential_home(self):
        """W6634: the credential home this adapter's assignment sits under.

        Built per call rather than held, because it is derived entirely from
        the roots this adapter already owns -- and a second copy of a value
        that is already owned is a second thing to keep true.

        W55758: UNLESS THE DEPLOYMENT OWNS ONE, in which case that is the
        home. Materialization, lifecycle publication, restart adoption and
        teardown then have one owner instead of two that agree only when the
        deployment happens to grant the path this derives.
        """
        if self.credential_home is not None:
            return self.credential_home
        return credentials.CredentialHome(self._home())

    def _home(self):
        """The manager-owned place this assignment's roots are siblings under.

        Custody and the volatile credential root are both under it and NEITHER
        is a mountable root: `ROOT_NAMES` is what a container may see as its
        own material, and these two are precisely the material it must not
        reach -- its own evidence after the freeze, and a bearer it is handed
        at one fixed path instead.
        """
        return os.path.dirname(self.assignment_roots["workspace"].rstrip("/"))

    def _quiesced(self, request):
        """Nothing this attempt started is still running, asked of the ENGINE.

        HERE RATHER THAN IN `sealing.py`, and the boundary inventory is what
        decided it: `list` and `observe` are injected capabilities with exactly
        one crossing each, and a second module calling them would give one
        capability two owners. Inside this adapter they are its own methods.

        The ten frozen label members split exactly -- the request carries the
        attempt, the four parts of the assignment and W16823's trusted
        principal and effective scope, this adapter has owned the three
        resolved digests since construction -- so the selector composes without
        the manager passing a runtime id it deliberately does not pass. Nothing is remembered between calls, so a manager restarted
        between start and freeze gates exactly as well as one that was never
        restarted.
        """
        expect = request["assignment"]
        context = boundaries.document(request["context"],
                                      "a seal authorization context",
                                      required=LABEL_CONTEXT)
        labels = documents.runtime_labels(
            runtime_attempt_id=request["attempt_id"],
            authority_uuid=expect["work_ref"]["authority_uuid"],
            work_id=expect["work_ref"]["work_id"],
            participant=expect["participant"],
            generation=expect["generation"],
            principal=context["principal"],
            effective_scope=context["effective_scope"],
            profile_digest=self.identity["profile_digest"],
            policy_digest=self.identity["policy_digest"],
            adapter_digest=self.identity["adapter_digest"])
        for entry in self.list({"labels": labels}):
            observed = self.observe(entry["runtime_id"])
            if observed["state"] not in sealing.QUIET_STATES:
                raise ContractRefusal(
                    "runtime-observation", "quiescence-unknown",
                    f"runtime {name_value(entry['runtime_id'])} for attempt "
                    f"{name_value(request['attempt_id'])} is "
                    f"{name_value(observed['state'])}; a result is sealed over "
                    f"a tree nobody is still writing to, and this one may be")

    def collect(self, operands):
        """W6634: the collection `intake.request_intake` asks for."""
        return sealing.collected_result(
            operands, custody=self._custody(operands["attempt_id"]),
            declared=self.declared_outputs)

    def retain(self, command):
        """W6636: the retention decision, delivered to the side holding the
        material.

        THE SEAM EXISTED ON THE MANAGER'S SIDE AND NOWHERE ELSE. `intake.
        decide_retention` types `adapter.retain` as a capability and delivers
        `outputRetainBody` to it, and this adapter simply had no such method --
        so a composed one-container lifecycle refused at retention and could
        never reach the destroy crossing at all. Surfaced by composing the arc,
        which is the only place a missing seam between two accepted components
        is visible.

        AND IT ENACTS THE DISPOSITION. The first version validated the command
        and returned `{"delivered": True}` for every disposition, which I
        recorded as an unspecified retention semantics. Review [P0]: it is not
        unspecified, and the manager's OWN settlement rule says so --
        `complete` means nothing was kept. An arc that discarded and then
        reported `complete` over surviving bytes was a false clean ending, not
        a policy question. W6629 already decided the boundary: `output.retain`
        is delivered to the side holding the material BECAUSE retention decides
        what happens to that material.

        THE PATH IS DERIVED, NEVER TAKEN. An artifact identity is
        `attempt:name` and the tree is this adapter's own custody place for
        that name -- so a caller cannot name a path, cannot reach another
        attempt's material, and cannot discard something this assignment never
        declared. Each of those is refused rather than resolved.

        ABSENCE IS ESTABLISHED, not ordered. `discard_tree` removes the tree
        and this asks the filesystem afterwards, for the same reason every
        other ending here does: a removal that returned is not evidence that
        anything is gone.

        AND IT IS IDEMPOTENT. An exact retry discards an already-absent tree,
        which is the state it asked for rather than a failure -- the manager
        delivers this before its own journal, so a crash between the two makes
        the next authorization repeat it.
        """
        taken = boundaries.document(
            command, "a retain command",
            required=("assignment_ref", "runtime_attempt_id", "artifact_ids",
                      "disposition", "retention_policy_digest"),
            optional=("operation",))
        attempt_id = boundaries.identity(taken["runtime_attempt_id"],
                                         "a runtime attempt id")
        disposition = boundaries.text(taken["disposition"],
                                      "a retention disposition")
        # BEFORE ANY FILESYSTEM MUTATION, and before the names are even
        # resolved. An unknown word is not a discard.
        if disposition not in _RETENTION_DISPOSITIONS:
            _denied(f"{name_value(disposition)} is not a retention "
                    f"disposition; the three this build enacts are "
                    f"{', '.join(sorted(_RETENTION_DISPOSITIONS))}")
        names = self._custodied(taken["artifact_ids"], attempt_id)
        home = self._custody(attempt_id)
        if disposition in _KEEPS_MATERIAL:
            # KEPT MEANS STILL THERE, AND THAT IS OBSERVED. Re-review [P0]:
            # this returned without looking, so custody that vanished between
            # intake and retention was journalled as kept -- and cleanup then
            # derived `retained`, whose whole meaning is that the material is
            # still there. That is the keep-side twin of the false `complete`
            # the previous review found, and it fails the same way: an ending
            # reported over bytes nobody saw.
            #
            # REFUSED BEFORE THE MANAGER JOURNALS, which is what makes it
            # actionable: `decide_retention` delivers this command and only
            # then records the decision, so a refusal here means no decision
            # was written about material that is not there.
            for name in names:
                place = os.path.join(home, name)
                if not os.path.isdir(place):
                    _denied(f"artifact "
                            f"{name_value(f'{attempt_id}:{name}')} is to be "
                            f"kept and its custody tree is not there; "
                            f"{name_value(disposition)} is an ending about "
                            f"material that still exists")
            return {"delivered": True, "discarded": []}
        discarded = []
        for name in names:
            place = os.path.join(home, name)
            workspaces.discard_tree(place)
            if os.path.exists(place):
                _denied(f"the custody tree for artifact "
                        f"{name_value(f'{attempt_id}:{name}')} is still "
                        f"present after removal; a discard that cannot be "
                        f"proved is not a discard")
            discarded.append(name)
        return {"delivered": True, "discarded": sorted(discarded)}

    def _custodied(self, artifact_ids, attempt_id):
        """The declared output names these artifact identities name.

        ONE SHAPE, AND IT IS `attempt:name`. `sealing.collected_result` mints
        every identity that way, so anything else is not an identity this
        adapter ever issued -- and resolving it anyway is how a caller-selected
        path gets in.
        """
        taken = own(artifact_ids, what="the retained artifact ids")
        if type(taken) is not list:
            _denied(f"a retention names a list of artifact ids; this is "
                    f"{name_value(artifact_ids)}")
        names = []
        for one in taken:
            identity = boundaries.text(one, "a retained artifact id")
            attempt, _, name = identity.partition(":")
            if not name or attempt != attempt_id:
                _denied(f"artifact {name_value(identity)} is not this "
                        f"attempt's; a retention acts on the material this "
                        f"adapter took custody of and nothing else")
            if name not in self.declared_outputs:
                _denied(f"artifact {name_value(identity)} names output "
                        f"{name_value(name)}, which this assignment does not "
                        f"declare")
            names.append(name)
        return names

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

        def unknown(state, why, candidates=()):
            # `mounts` IS `None` on every branch that read no document: the
            # honest value for "this adapter did not see what this runtime
            # has". `_mounts_disagree` refuses an unknown reading outright, so
            # nothing downstream has to interpret it.
            #
            # MEASURED AS AN EQUIVALENCE, and said so rather than claimed
            # otherwise: answering `()` here produces the identical refusal
            # today, because a lifecycle record names at least one slot and an
            # empty bind list therefore fails the "no bind at ..." rule anyway.
            # `None` is still the right value -- it is the true one -- but no
            # case can currently tell the two apart, and a comment claiming a
            # distinction nothing can drive is the vacuity this campaign keeps
            # correcting.
            # W55758 review (2026-09-01T10:35:20Z) [P1]: THE IDENTITIES THIS
            # ANSWER SAW, kept rather than reduced to prose.
            #
            # A recovery owes an operator the exact locator of every runtime
            # it left alone, and this method was discarding precisely those:
            # a mismatched inspection became a sentence naming the id, and an
            # ambiguous one became a count. A report reconstructed from the
            # EXPECTED target then named the wrong runtime and called it
            # untouched. Empty on every branch that saw none, which is the
            # true value rather than an absent member to interpret.
            #
            # W55758 review (2026-09-01T10:56:54Z) [P1]: AND EACH ONE'S OWN
            # STATE. Carrying bare identities left the caller nothing to say
            # about a candidate but `unidentified`, and it copied the
            # TARGET's diagnostic as that candidate's reason -- for a runtime
            # whose inspection said `Running: true`. The locator, the
            # observed state and the reason are one closed record per
            # runtime, decided here where the document was actually read.
            return {"state": state, "why": why, "mounts": None,
                    "candidates": tuple(candidates)}

        if answer["status"] != 0:
            # POSITIVE ABSENCE IS ABOUT THIS IDENTITY, and the engine has to
            # say so. Review [P1]: matching "no such" or "not found" anywhere
            # in stderr made any unrelated prose carrying those words --
            # a missing network, an absent volume, a daemon reporting a
            # missing socket -- read as this runtime being dead, which is the
            # one mistake that releases an assignment whose worker is running.
            # The contract is now engine-specific and names the runtime.
            #
            # Review [P0], the second correction of this one branch: naming
            # the runtime SOMEWHERE in stderr was still not association. The
            # engine's own absence sentence has to be the thing that names it.
            if _absent_prose(self.engine, answer["stderr"], runtime_id):
                return unknown("absent",
                               "the engine answered that this exact identity "
                               "does not exist")
            return unknown("uncertain",
                           f"the engine refused to inspect this runtime: "
                           f"{answer['stderr'][:MAX_DIAGNOSTIC]}")
        document = _decoded(answer["stdout"], "an engine inspection")
        if type(document) is list:
            if len(document) != 1:
                return unknown(
                    "uncertain",
                    f"the engine answered about {len(document)} "
                    f"runtimes for one exact identity",
                    candidates=_observed_runtimes(document))
            document = document[0]
        if type(document) is not dict:
            return unknown("uncertain",
                           "the engine's inspection is not one record")
        # AND A SUCCESSFUL INSPECTION MUST BE ABOUT THE RUNTIME WE ASKED
        # ABOUT. Review [P1]: this read `State` from whatever document came
        # back, so an engine answering about another container -- or about
        # nothing identifiable -- was reported as this one's state.
        named = _named_runtime(document)
        if named is None:
            return unknown("uncertain",
                           "the engine's inspection names no runtime, so it "
                           "is not evidence about this one")
        if named != runtime_id:
            return unknown("uncertain",
                           f"the engine answered about "
                           f"{name_value(named)} and this asked about "
                           f"{name_value(runtime_id)}",
                           candidates=_observed_runtimes([document]))
        state = _one_of(document, ("State",), "an engine inspection")
        if type(state) is not dict:
            return unknown("uncertain",
                           "the engine's inspection carries no state record")
        # THE MOUNTS THE ENGINE SAYS THIS RUNTIME ACTUALLY HAS. Read from the
        # SAME inspection that decided the state, so the two facts are one
        # observation of one runtime rather than two questions asked at two
        # moments -- which is what recovery needs them to be.
        mounts = _observed_mounts(document)
        # THE `Running` READ STAYS AT THIS CROSSING, which is where the
        # boundary inventory owns it and where its witness case drives it. The
        # VOCABULARY is shared with the candidate reader rather than spelled
        # twice, and the target is carried as a candidate record of its own so
        # a caller composing a report never has to reconstruct one.
        found = _running_state(state.get("Running"))
        return {"state": found["state"], "why": found["why"],
                "mounts": mounts,
                "candidates": ({"runtime_id": runtime_id, **found},)}

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
