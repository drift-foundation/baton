"""The fenced integration mount boundary, and the only thing that mints one.

W110934, `work/records/2026/09/finding-v12-integration-oci-delivery/`.

WHAT WAS MISSING, AND IT WAS NOT A COMPONENT. `runtime.py` owns the two
integration namespaces and their fixed container paths; `queue.py` owns the
live fenced grant; `source_boundary.py` owns proving a directory this manager
did not create; `oci.py` owns the closed argv. What did not exist is anything
that composes a MOUNT PLAN out of them -- and ordinary worker mounts cannot be
made to do it, because `oci._mounts` confines them to the two assignment roots
with only the workspace writable. The measured baseline is three
`policy/denied` refusals, one for each namespace this integration needs.

THREE FIXED BINDS AND NO FOURTH, and none of them is parameterized:

    adopted assignment namespace  -> /run/baton/integration/assignment  RO
    adopted result namespace      -> /run/baton/integration/result      RW
    configured canonical target   -> /target                            RW

The candidate evidence and instructions a runtime reads are NOT here. They stay
the already accepted read-only nominated source at `/input/source`, which is
the one deliberate nesting exception this campaign has ruled on; W110935 owns
that bundle. This module adds no extra-mount facility to anticipate it, because
an arbitrary mount array is exactly the thing a typed family exists to replace.

WHAT A NOMINATED TARGET IS AND IS NOT. `nominate_source` pins a real directory
inode. It does not prove content, approval, or that the runtime's fixed uid can
write there -- three separate questions, and collapsing them is how a nominal
bind gets mistaken for a granted one. A NOMINAL RW BIND DOES NOT MAKE THE
TARGET WRITABLE to the container's user; the deployment provisions that, the
worker's own whole-path preflight proves each affected file before it edits
anything, and this manager's `os.access` is not the worker's answer. An
incompatible target refuses for exact operator disposition: no recursive
permission repair, no user substitution, no ACL workaround, no stronger
container privilege.

AND THE FINAL PROOF IS A CUTPOINT, NOT REVOCATION. The coordinator has no
automatic lease expiry, and blocking or abandoning a grant AFTER a bind does not
unmount it -- no label, timeout or fence stops a running writer. What this
boundary guarantees is that nothing is bound without a grant that was live at
the last moment before the engine was asked, and that a grant which ended
before that moment refuses. The existing predecessor-runtime and settlement
gates are what keep a successor from starting behind an unquiesced writer. An
atomic guarantee across a hostile concurrent operator action and the daemon's
own resolution is NOT claimed here and is not proved by this plan.
"""

import json
import os
import stat
from types import MappingProxyType

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import boundaries, source_boundary, workspaces
from . import runtime

__all__ = ["BINDING_DOCUMENT", "BINDING_MEMBERS", "BINDING_SCHEMA",
           "TARGET_TARGET", "IntegrationMountBoundary", "IntegrationTarget",
           "adopt_mount_boundary", "boundary_mounts", "compatible_target",
           "compose_mount_boundary", "integration_target",
           "observed_disagreement", "prove_target_posture",
           "revalidate_boundary"]

# THE THIRD FIXED CONTAINER PATH, owned here because the other two are
# `runtime.py`'s and a constant belongs with the contract that fixes it. Proved
# free against every other fixed target this build composes -- `/input`,
# `/input/source`, `/output`, `/tmp`, `/dev/shm`, the launch document, the
# credential slots, the exchange namespaces and the two integration ones -- in
# both directions, which is the check the collision rules below can only be
# meaningful against.
TARGET_TARGET = "/target"

# THE PRIVATE IMMUTABLE COMPANION. It lives BESIDE the two mounted namespaces
# and never inside one: a document describing a mount, written where that mount
# exposes it, is a document the runtime could rewrite to describe itself.
BINDING_DOCUMENT = "mount-binding.json"
BINDING_SCHEMA = "baton.v12.integration-mount-binding/1"
BINDING_MEMBERS = ("schema", "attempt_id", "assignment_digest",
                   "canonical_target_id", "sources")
SOURCE_MEMBERS = ("container_target", "host_source", "device", "inode",
                  "writable")

# NO RUNTIME STATE LIVES IN THE COMPANION, and the omission is the decision.
# `oci.py` owns the runtime journal; a second document carrying a runtime id or
# a lifecycle word would be a second account of one lifecycle, and the two would
# disagree the first time either moved.


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


class IntegrationTarget:
    """The deployment's binding of one configured target id to one directory.

    TRUSTED CONFIGURATION, AND DELIBERATELY NOT DERIVED. The canonical target
    id is an opaque coordinator identity; where that target LIVES on this host
    is a deployment fact, so it arrives as a nomination an operator configured
    rather than as a locator computed from the id or chosen by whatever
    composed the assignment. A host path derived from an opaque id would let
    whoever controls the id choose the directory.
    """

    __slots__ = ("canonical_target_id", "source")

    def __init__(self, canonical_target_id, source, _minted=None):
        if _minted is not _MINT:
            _denied("an integration target is answered by "
                    "`integration_target`, which proves its directory; a "
                    "target a caller can mint is a target a caller chose")
        object.__setattr__(self, "canonical_target_id", canonical_target_id)
        object.__setattr__(self, "source", source)

    def __setattr__(self, name, value):
        _refuse("an integration target is a frozen answer about one "
                "configured directory")

    def __delattr__(self, name):
        _refuse("an integration target is a frozen answer about one "
                "configured directory")


_MINT = object()


def integration_target(canonical_target_id, source):
    """Bind one configured target id to one proved directory."""
    boundaries.identity(canonical_target_id, "a canonical target identity")
    if type(source) is not source_boundary.NominatedSource:
        _denied(f"an integration target names a directory this manager proved "
                f"through `nominate_source`; this is {name_value(source)}")
    return IntegrationTarget(canonical_target_id, source, _minted=_MINT)


class IntegrationMountBoundary:
    """The frozen three-mount plan for one integration attempt.

    Minted only by `compose_mount_boundary`. A plain mapping, a bare mount
    array, a direct construction or a caller-authored writable flag never
    authorizes this path -- which is the same rule the credential, launch,
    exchange and source families are already under, for the same reason.
    """

    __slots__ = ("attempt_id", "canonical_target_id", "_assignment",
                 "assignment_digest", "_sources", "delivery", "target",
                 # THE GROUP THIS PLAN WAS PROVED UNDER. Review [P1]: the
                 # adapter and the delivery could each carry an unrelated
                 # group choice, so nothing compared the group the namespaces
                 # were adopted in with the one the container is given. It is
                 # bound here and re-adopted at the final proof.
                 "workspace_group",
                 # THE HANDLES THIS BOUNDARY RE-ASKS ITS OWN QUESTIONS WITH.
                 # `revalidate_boundary` is the final pre-engine proof and it
                 # must read the coordinator again -- so the boundary carries
                 # the exact stores and profile it was composed against rather
                 # than taking them at proof time. A caller that supplied them
                 # then could supply different ones, and a callback answering
                 # `True` is the substitute this design exists to refuse.
                 "store", "manager", "_profile")

    def __init__(self, _minted=None, **members):
        if _minted is not _MINT:
            _denied("an integration mount boundary is answered by "
                    "`compose_mount_boundary`, which proves the grant, the "
                    "published assignment and every directory it binds")
        # PRIVATELY OWNED COPIES, PUBLICLY READ-ONLY VIEWS. Review [P2]:
        # blocking attribute assignment while storing live dictionaries left
        # the assignment, the profile and every source editable through the
        # public attributes -- and `boundary_mounts` then answered a caller's
        # own access flag.
        #
        # THE COPY IS PRIVATE AND THE VIEW IS PUBLIC, rather than storing the
        # view: the accepted boundary readers take exact built-in documents
        # and refuse anything carrying behaviour, so a proxy in the slot would
        # make this object unusable by the very owners it must be re-proved
        # through. A caller still holding the original mutates nothing here,
        # and a caller reading the attribute cannot write through it.
        # THE THREE VIEWED MEMBERS ARE NAMED, not detected by type: `assignment`
        # and `profile` are `None` on a RECOVERED boundary, and a rule that
        # decided by value would try to write the property rather than its
        # private slot.
        for name, value in members.items():
            if name in ("assignment", "profile"):
                object.__setattr__(self, "_" + name,
                                   None if value is None else dict(value))
            elif name == "sources":
                object.__setattr__(self, "_sources",
                                   tuple(dict(one) for one in value))
            else:
                object.__setattr__(self, name, value)

    @property
    def assignment(self):
        return (None if self._assignment is None
                else MappingProxyType(self._assignment))

    @property
    def profile(self):
        return (None if self._profile is None
                else MappingProxyType(self._profile))

    @property
    def sources(self):
        return tuple(MappingProxyType(one) for one in self._sources)

    def __setattr__(self, name, value):
        _refuse("an integration mount boundary is a frozen answer about one "
                "attempt's mounts")

    def __delattr__(self, name):
        _refuse("an integration mount boundary is a frozen answer about one "
                "attempt's mounts")


def _directory_identity(place, what):
    """One existing directory's device and inode, proved no-follow AND with
    the spelling the kernel actually resolves.

    The same question `nominate_source` asks and the same one this module has
    to re-ask before the engine: a path re-pointed at another tree resolves to
    the same characters and a different inode.

    REVIEW 2026-09-07T16-34-08Z [P1]: `O_NOFOLLOW` binds the FINAL component
    only, so a symlink at an ANCESTOR was followed and the inode underneath was
    identical -- the reviewer moved a target's parent, put a link at its old
    name, and the start reached one run against the re-resolved path. The
    engine canonicalizes the source it is given, so the spelling this manager
    holds must already be the one the kernel resolves to; that is the check a
    no-follow open at the leaf cannot make, and it is `nominate_source`'s own
    rule applied at every later use point.
    """
    if os.path.realpath(place) != place:
        _denied(f"{what} at {name_value(place)} resolves to "
                f"{name_value(os.path.realpath(place))}; a link at an ancestor "
                f"is a directory somebody else chose and the engine binds what "
                f"the kernel resolves rather than what this manager spelled")
    try:
        opened = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    except OSError as failure:
        _denied(f"{what} at {name_value(place)} is not a directory this "
                f"manager can bind ({type(failure).__name__}); a replaced or "
                f"absent mount source is not one to re-resolve")
    try:
        held = os.fstat(opened)
    finally:
        os.close(opened)
    return held.st_dev, held.st_ino


def _canonical(place, what):
    """One absolute, canonical, engine-safe host path.

    `oci.canonical_source` applies these rules at the argv; they are applied
    HERE too, before a companion binds the spelling, because a document that
    recorded a path the engine would refuse is a record of a mount that could
    never happen.
    """
    boundaries.text(place, what)
    if not place.startswith("/") or place.startswith("-") \
            or "\x00" in place or ":" in place \
            or ".." in place.split("/") or os.path.normpath(place) != place:
        _denied(f"{what} at {name_value(place)} is not one canonical "
                f"engine-safe absolute path")
    return place


def _overlaps(one, other):
    """Whether two host paths are equal or one contains the other."""
    if one == other:
        return True
    return one.startswith(other.rstrip("/") + "/") \
        or other.startswith(one.rstrip("/") + "/")


def _sources(delivery, target):
    """The three host capabilities this boundary binds, with their identities.

    ORDERED AND CLOSED. The tuple is the mount plan; there is no fourth entry
    and no operand that could add one.
    """
    composed = []
    for place, container, writable, what in (
            (delivery.assignment_root, runtime.ASSIGNMENT_TARGET, False,
             "the integration assignment namespace"),
            (delivery.result_root, runtime.RESULT_TARGET, True,
             "the integration result namespace"),
            (target.source.place, TARGET_TARGET, True,
             "the configured canonical target")):
        host = _canonical(place, what)
        device, inode = _directory_identity(host, what)
        composed.append({"container_target": container, "host_source": host,
                         "device": device, "inode": inode,
                         "writable": writable})
    # THE TARGET'S IDENTITY IS THE ONE THE NOMINATION PROVED, compared rather
    # than re-derived. A target directory replaced between configuration and
    # composition resolves to the same spelling and a different inode, and
    # re-resolving it into a new acceptable directory is the one repair this
    # boundary must never perform.
    if (composed[2]["device"], composed[2]["inode"]) \
            != (target.source.device, target.source.inode):
        _denied(f"the configured canonical target at "
                f"{name_value(target.source.place)} is no longer the directory "
                f"this deployment nominated; a replaced target is refused for "
                f"operator disposition rather than adopted")
    return tuple(composed)


def _no_overlap(sources, extra=()):
    """No two host capabilities may contain one another, IN EITHER DIRECTION.

    A target equal to, inside, or containing one of the manager's own
    namespaces would put one directory behind two container paths with
    different access -- and which of the two a write reaches is the engine's
    decision rather than this manager's.

    REVIEW 2026-09-07T16-04-48Z [P1]: `extra` was never supplied, so this
    compared the three new sources against each other and against nothing
    else. The measured consequence was a start that bound ONE host directory
    writable at `/output` and writable at `/target` -- two names for one tree,
    with the ordinary workspace rules applying to one of them and none of them
    applying to the other. The fixed container-target enumeration cannot
    establish this: two different container paths is exactly the arrangement,
    and the question is about the HOST.
    """
    # REVIEW 2026-09-07T16-34-08Z [P1]: this compared every pair in the
    # CONCATENATION, so the two lists were also compared against each other --
    # and an assignment root is legitimately represented twice, once as the
    # logical root and once as the ordinary mount composed from it. A valid
    # `/output` bind therefore collided with its own workspace root. The same
    # rule threatened the accepted source-under-input nesting.
    #
    # SO THE PAIRS ARE THE INTEGRATION SOURCES AMONG THEMSELVES, and each
    # integration source against each other capability. Relationships among
    # the ordinary families stay with the owners that already decide them.
    mine = [(one["host_source"], one["container_target"]) for one in sources]
    pairs = [(mine[index], one) for index in range(len(mine))
             for one in mine[index + 1:]] \
        + [(one, other) for one in mine for other in extra]
    for (host, container), (other_host, other_container) in pairs:
        if _overlaps(host, other_host):
            _denied(f"this integration binds {name_value(host)} at "
                    f"{name_value(container)} and {name_value(other_host)} "
                    f"at {name_value(other_container)}; one host directory "
                    f"behind two container paths is a mount plan nobody "
                    f"can say the effective access of")


def _binding(boundary_members):
    """The closed companion document, composed and owned in one place."""
    document = {"schema": BINDING_SCHEMA,
                "attempt_id": boundary_members["attempt_id"],
                "assignment_digest": boundary_members["assignment_digest"],
                "canonical_target_id": boundary_members["canonical_target_id"],
                "sources": [dict(one) for one in boundary_members["sources"]]}
    return _owned_binding(document)


def _owned_binding(value):
    held = boundaries.document(value, "an integration mount binding",
                               required=BINDING_MEMBERS)
    if held["schema"] != BINDING_SCHEMA:
        _refuse(f"an integration mount binding is {name_value(BINDING_SCHEMA)};"
                f" this is {name_value(held['schema'])}")
    boundaries.identity(held["attempt_id"], "a mount binding's attempt")
    boundaries.identity(held["canonical_target_id"],
                        "a mount binding's canonical target")
    boundaries.text(held["assignment_digest"],
                    "a mount binding's assignment digest")
    if type(held["sources"]) is not list or len(held["sources"]) != 3:
        _refuse("an integration mount binding records exactly three sources")
    for one in held["sources"]:
        source = boundaries.document(one, "a mount binding source",
                                     required=SOURCE_MEMBERS)
        boundaries.text(source["container_target"], "a bound container target")
        boundaries.text(source["host_source"], "a bound host source")
        for name in ("device", "inode"):
            if type(source[name]) is not int or type(source[name]) is bool:
                _refuse(f"a mount binding source's {name} is an integer")
        if type(source["writable"]) is not bool:
            _refuse("a mount binding source's access is a boolean")
    return held


def _publish_binding(delivery, composed):
    """Publish this attempt's binding once, or prove the retained one is it.

    THE SAME NO-CLOBBER PUBLICATION `runtime.py` USES, and the reason is that
    module's own: a staging name that is unique, the whole bounded write, the
    mode established on the descriptor, and a link into the final name that
    fails rather than replacing a concurrent winner.

    A CONFLICTING BINDING IS AN INSPECTABLE REFUSAL. It is never reconstructed
    as though it had always been this one: an attempt whose recorded mounts
    disagree with the ones now composed is exactly the state an operator has to
    look at, and silently adopting the new plan would erase the evidence of
    what the old container was actually given.
    """
    runtime._publish_once(delivery.root, BINDING_DOCUMENT,
                          runtime._payload(composed))
    raw = runtime._read_bounded(delivery.root, BINDING_DOCUMENT,
                                what="the integration mount binding",
                                mode=runtime.ASSIGNMENT_FILE)
    if raw is None:
        _refuse(f"attempt {name_value(delivery.attempt_id)}'s integration "
                f"mount binding is absent immediately after publication; a "
                f"binding this manager cannot read back is not one it will "
                f"bind a runtime to", category="refused", code="precondition")
    if raw != runtime._payload(composed):
        _denied(f"attempt {name_value(delivery.attempt_id)}'s retained "
                f"integration mount binding is not the plan now composed; a "
                f"conflicting binding is returned for inspection rather than "
                f"replaced")
    return composed


def _adopted_binding(delivery):
    """The binding this attempt ALREADY has, required rather than created.

    REVIEW 2026-09-07T16-04-48Z [P1]: publication and recovery were one
    function, and it published whenever the companion was absent -- so a
    removed binding was silently recreated with identical bytes and the
    evidence that it had ever gone was destroyed by the act of looking. A
    recovery that can mint the thing it is recovering is not a recovery.
    """
    raw = runtime._read_bounded(delivery.root, BINDING_DOCUMENT,
                                what="the integration mount binding",
                                mode=runtime.ASSIGNMENT_FILE)
    if raw is None:
        _refuse(f"attempt {name_value(delivery.attempt_id)} has no retained "
                f"integration mount binding; a recovery adopts the plan this "
                f"manager recorded and never composes a replacement for it",
                category="refused", code="precondition")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as failure:
        _refuse(f"attempt {name_value(delivery.attempt_id)}'s retained "
                f"integration mount binding does not decode "
                f"({type(failure).__name__})", category="refused",
                code="precondition")
    return _owned_binding(document)


def adopt_mount_boundary(manager, *, delivery, target, workspace_group):
    """Recover the boundary a previous incarnation bound, READ-ONLY.

    W110934 review [P1]. `compose_mount_boundary` requires a live grant,
    correctly: it is the act that authorizes a writable bind. But an operator
    inspecting or stopping an exact runtime after that grant has ended needs
    the capability WITHOUT regranting anything, and a manager whose only
    minting path demanded a fresh grant had no safe way to reach one -- so a
    blocked target left a running container nobody could name through the
    public surface.

    SO THIS GRANTS NOTHING AND COMPOSES NOTHING. It requires the retained
    provenance, re-adopts the namespaces at their exact modes and configured
    group, re-identifies every recorded directory, and answers a boundary
    marked read-only. `revalidate_boundary` refuses it, because the one thing
    an adopted plan may never do is start a runtime.
    """
    if type(target) is not IntegrationTarget:
        _denied(f"a recovered mount boundary names the configured target this "
                f"deployment nominated; this is {name_value(target)}")
    adopted = runtime.adopt_delivery(_delivery_root(delivery),
                                     attempt_id=delivery.attempt_id,
                                     workspace_group=workspace_group)
    if adopted is None:
        _refuse(f"attempt {name_value(delivery.attempt_id)} has no integration "
                f"delivery to recover", category="refused",
                code="precondition")
    held = _adopted_binding(adopted)
    if held["attempt_id"] != delivery.attempt_id \
            or held["canonical_target_id"] != target.canonical_target_id:
        _denied(f"the retained mount binding names attempt "
                f"{name_value(held['attempt_id'])} and target "
                f"{name_value(held['canonical_target_id'])}; a recovery adopts "
                f"the plan recorded for the delivery it was handed")
    # THE SUPPLIED NOMINATION IS THE ONE THIS BINDING RECORDED. Review [P2]:
    # only the opaque id was compared, so a DIFFERENT real directory nominated
    # under the same id was accepted -- the recovered object pointed at one
    # tree while its mounts still named another. Configuration drift is
    # refused rather than presented as an exact recovery.
    recorded = {one["container_target"]: one for one in held["sources"]}
    bound = recorded.get(TARGET_TARGET)
    if bound is None:
        _refuse(f"the retained mount binding records no "
                f"{name_value(TARGET_TARGET)} source",
                category="refused", code="precondition")
    if (target.source.place, target.source.device, target.source.inode) \
            != (bound["host_source"], bound["device"], bound["inode"]):
        _denied(f"this deployment now nominates "
                f"{name_value(target.source.place)} for target "
                f"{name_value(target.canonical_target_id)} and the retained "
                f"binding recorded {name_value(bound['host_source'])}; a "
                f"recovery reports the plan it found rather than the one the "
                f"configuration currently describes")
    for one in held["sources"]:
        device, inode = _directory_identity(
            one["host_source"], f"the recorded {one['container_target']} "
                                f"source")
        if (device, inode) != (one["device"], one["inode"]):
            _denied(f"the directory recorded at "
                    f"{name_value(one['container_target'])} is no longer the "
                    f"one this binding names; a recovery reports what it "
                    f"found rather than re-resolving it")
    return IntegrationMountBoundary(
        _minted=_MINT, attempt_id=held["attempt_id"],
        canonical_target_id=held["canonical_target_id"], assignment=None,
        assignment_digest=held["assignment_digest"],
        sources=tuple(held["sources"]), delivery=adopted, target=target,
        workspace_group=workspace_group, store=None, manager=manager,
        profile=None)


def compose_mount_boundary(store, manager, *, profile, delivery, assignment,
                           target, workspace_group):
    """Mint the immutable three-mount boundary for one integration attempt.

    EVERY OPERAND IS A CAPABILITY OR IS PROVED HERE. The delivery is
    `runtime.IntegrationDelivery`; the target is an `IntegrationTarget` minted
    over a proved directory; the workspace group is the one this manager's own
    record answers; the profile is owned by `runtime`; and the assignment is
    compared THREE ways -- against the document published in the namespace the
    runtime will read, against a freshly composed one, and by digest.

    THE FRESH COMPOSITION IS THE LIVE PROOF AND THE PUBLISHED ONE IS THE
    IDENTITY, and they are different questions. An assignment stays readable
    after the grant that authorized it has ended, so a boundary that compared
    only the published document would compose a mount plan for a lease nobody
    holds. `compose_assignment` reads the grant from the coordinator in the
    same call, so a blocked, abandoned or re-fenced target refuses here.
    """
    taken = runtime._owned_profile(profile)
    if type(delivery) is not runtime.IntegrationDelivery:
        _denied(f"an integration mount boundary is composed over this "
                f"component's own typed delivery; this is "
                f"{name_value(delivery)}")
    if type(target) is not IntegrationTarget:
        _denied(f"an integration mount boundary binds a configured target this "
                f"deployment nominated; this is {name_value(target)}")
    expected = runtime._owned_assignment(assignment)
    if expected["canonical_target_id"] != target.canonical_target_id:
        _denied(f"this assignment integrates target "
                f"{name_value(expected['canonical_target_id'])} and the "
                f"configured target is "
                f"{name_value(target.canonical_target_id)}; a runtime writes "
                f"the target its grant names")
    if expected["attempt_id"] != delivery.attempt_id:
        _denied(f"this assignment is for attempt "
                f"{name_value(expected['attempt_id'])} and the delivery "
                f"belongs to {name_value(delivery.attempt_id)}; one delivery "
                f"belongs to one attempt")
    if expected["instructions_digest"] != taken["instructions_digest"]:
        _denied(f"this assignment names instructions "
                f"{name_value(expected['instructions_digest'])} and the "
                f"selected profile wires "
                f"{name_value(taken['instructions_digest'])}")
    # THE NAMESPACES THIS MANAGER MADE, adopted rather than assumed. `absent`
    # is an ordinary answer for a delivery nobody materialized, and it is not
    # one this composition can proceed from.
    adopted = runtime.adopt_delivery(_delivery_root(delivery),
                                     attempt_id=delivery.attempt_id,
                                     workspace_group=workspace_group)
    if adopted is None:
        _refuse(f"attempt {name_value(delivery.attempt_id)} has no integration "
                f"delivery to mount; the namespaces are created before a "
                f"runtime starts and never after",
                category="refused", code="precondition")
    published = runtime.published_assignment(adopted)
    if published is None:
        _refuse(f"attempt {name_value(delivery.attempt_id)}'s integration "
                f"assignment namespace carries no published assignment; a "
                f"runtime reads what it was asked to do from there",
                category="refused", code="precondition")
    if published != expected:
        _denied(f"the assignment published for attempt "
                f"{name_value(delivery.attempt_id)} is not the one this "
                f"boundary was composed against; the whole document is "
                f"compared because a mount plan binds an exact assignment")
    # THE LIVE GRANT, READ FROM THE COORDINATOR IN THIS CALL.
    fresh = runtime.compose_assignment(
        store, manager, profile=taken,
        canonical_target_id=expected["canonical_target_id"],
        entry_id=expected["entry_id"], lease_id=expected["lease_id"],
        fence=expected["fence"], attempt_id=expected["attempt_id"])
    if fresh != expected:
        _denied(f"the grant this target currently holds composes a different "
                f"assignment than the one published for attempt "
                f"{name_value(delivery.attempt_id)}; a mount plan is bound to "
                f"the assignment the coordinator answers now")
    sources = _sources(adopted, target)
    _no_overlap(sources)
    members = {"attempt_id": expected["attempt_id"],
               "canonical_target_id": expected["canonical_target_id"],
               "assignment": expected,
               "assignment_digest": runtime.assignment_digest(expected),
               "sources": sources, "delivery": adopted, "target": target,
               "workspace_group": workspace_group,
               "store": store, "manager": manager, "profile": taken}
    composed = IntegrationMountBoundary(_minted=_MINT, **members)
    # THE TARGET'S POSTURE IS PROVED AT COMPOSITION, not merely offered as a
    # helper. Review [P1]: `prove_target_posture` had no production caller, so
    # a start reached the engine with a target the runtime's group could not
    # work in and the deployment learned about it from a failing integrator.
    prove_target_posture(composed, workspace_group)
    _publish_binding(adopted, _binding(members))
    return composed


def _delivery_root(delivery):
    """The root a delivery was constructed over.

    `IntegrationDelivery` appends its own directory name to what it is given,
    so re-adopting one means handing back the parent rather than the composed
    root -- and deriving that with string surgery in a caller is how the two
    ends stop agreeing.
    """
    return os.path.dirname(delivery.root)


def boundary_mounts(boundary):
    """The three `(source, target, writable)` triples, in their fixed order."""
    if type(boundary) is not IntegrationMountBoundary:
        _denied(f"integration mounts are composed from this module's own "
                f"boundary; this is {name_value(boundary)}")
    return tuple((one["host_source"], one["container_target"], one["writable"])
                 for one in boundary._sources)


def revalidate_boundary(boundary, *, participant=None, workspace_group=None):
    """The FINAL proof, immediately before the engine is asked to run.

    THIS IS A CUTPOINT AND NOT REVOCATION, and the distinction is the whole of
    what this can honestly claim. Everything between this call and the daemon's
    own resolution is outside any lock this deployment holds: a grant blocked
    after the bind does not unmount it, and no label, timeout or fence stops a
    writer that is already running. What this establishes is that the grant was
    live, the assignment was unchanged and every bound directory was still the
    one proved, at the last moment this manager could ask.

    IT RE-ASKS EVERY QUESTION rather than trusting the composition. The grant
    is read from the coordinator again, the published assignment is read from
    the namespace again, the retained binding is compared again, and each of
    the three directories is re-identified by device and inode. A composition
    that happened seconds ago is evidence about seconds ago.
    """
    if type(boundary) is not IntegrationMountBoundary:
        _denied(f"an integration start is proved through this module's own "
                f"boundary; this is {name_value(boundary)}")
    if boundary._assignment is None or boundary.store is None:
        _denied(f"attempt {name_value(boundary.attempt_id)}'s mount boundary "
                f"was RECOVERED rather than composed; a read-only adoption "
                f"exists to inspect and stop an exact runtime and never to "
                f"start one")
    taken = boundary._profile
    expected = boundary._assignment
    # THE RUNTIME BEING STARTED IS THE ONE THE GRANT NAMES. Review [P1]: the
    # proof compared the stored assignment against a fresh composition through
    # its own profile -- which is the document agreeing with itself -- and
    # nothing compared the PARTICIPANT the start was labelled for. One engine
    # runtime was started as `baton.foreign` under a grant held by
    # `baton.merge`, and every check passed because none of them asked.
    if participant is not None \
            and expected["integrator_participant"] != participant:
        _denied(f"this start is labelled for participant "
                f"{name_value(participant)} and the grant was given to "
                f"{name_value(expected['integrator_participant'])}; a runtime "
                f"runs under the grant it was given, not beside it")
    published = runtime.published_assignment(boundary.delivery)
    if published != expected:
        _denied(f"the assignment published for attempt "
                f"{name_value(boundary.attempt_id)} changed after this mount "
                f"plan was composed")
    fresh = runtime.compose_assignment(
        boundary.store, boundary.manager, profile=taken,
        canonical_target_id=expected["canonical_target_id"],
        entry_id=expected["entry_id"], lease_id=expected["lease_id"],
        fence=expected["fence"], attempt_id=expected["attempt_id"])
    if fresh != expected:
        _denied(f"the grant for attempt {name_value(boundary.attempt_id)} no "
                f"longer composes the assignment this mount plan binds")
    # THE NAMESPACES ARE RE-ADOPTED, not merely re-identified. Review [P1]:
    # comparing inodes says the directory is the same one and says nothing
    # about its mode or its group -- and a result namespace changed to 0777
    # during the duplicate lookup still reached the engine. `adopt_delivery`
    # is the accepted owner of exactly those questions, so it is asked again.
    # THE GROUP THE ADAPTER ACTUALLY HOLDS, compared against the one this plan
    # was proved under. Review [P1]: storing the boundary's own group and
    # checking it against itself is not that comparison -- the container is
    # given the ADAPTER's group, and until this crossed nothing established
    # that the two were the same grant.
    if workspace_group is not None \
            and workspaces.check_workspace_group(workspace_group.gid) \
            != workspaces.check_workspace_group(boundary.workspace_group.gid):
        _denied(f"this mount plan was proved under group "
                f"{boundary.workspace_group.gid} and the runtime is given "
                f"{workspace_group.gid}; the namespaces the container must "
                f"answer in are the ones it holds a share of")
    if runtime.adopt_delivery(_delivery_root(boundary.delivery),
                              attempt_id=boundary.attempt_id,
                              workspace_group=boundary.workspace_group) is None:
        _refuse(f"attempt {name_value(boundary.attempt_id)}'s integration "
                f"delivery is gone", category="refused", code="precondition")
    prove_target_posture(boundary, boundary.workspace_group)
    for one in boundary._sources:
        device, inode = _directory_identity(
            one["host_source"], f"the bound {one['container_target']} source")
        if (device, inode) != (one["device"], one["inode"]):
            _denied(f"the directory bound at "
                    f"{name_value(one['container_target'])} is no longer the "
                    f"one this mount plan proved; a replaced source is refused "
                    f"rather than re-resolved")
    raw = runtime._read_bounded(boundary.delivery.root, BINDING_DOCUMENT,
                                what="the integration mount binding",
                                mode=runtime.ASSIGNMENT_FILE)
    if raw != runtime._payload(_binding({
            "attempt_id": boundary.attempt_id,
            "assignment_digest": boundary.assignment_digest,
            "canonical_target_id": boundary.canonical_target_id,
            "sources": boundary._sources})):
        _denied(f"attempt {name_value(boundary.attempt_id)}'s retained mount "
                f"binding is not the plan about to be started")
    return boundary


def observed_disagreement(boundary, observed):
    """Why the live binds are not this boundary's, or `None` if they are.

    THE SAME FOUR MISTAKES `oci._mounts_disagree` NAMES, asked about this
    family: the engine could not be read, so nothing is proved; a bind is
    missing; it comes from somewhere else; or its access is not the one
    composed. And the fifth that is easy to forget -- an EXTRA bind at or below
    one of the three fixed targets, which a comparison that only looked for
    what it expected would never see.

    `None` FOR UNREADABLE OBSERVATION IS NOT AN OPTION HERE. `oci` answers
    `None` from `_observed_mounts` when the engine's shape is unfamiliar, and
    this returns a REASON for that case rather than agreement: an integration
    whose mounts cannot be read is uncertain, and uncertain is held.
    """
    if type(boundary) is not IntegrationMountBoundary:
        _denied(f"integration mounts are observed through this module's own "
                f"boundary; this is {name_value(boundary)}")
    if observed is None:
        return ("the engine did not report this runtime's binds, so nothing "
                "about its integration mounts is proved")
    expected = {one["container_target"]: one for one in boundary._sources}
    for target, one in sorted(expected.items()):
        live = [held for held in observed if held.get("target") == target]
        if len(live) != 1:
            return (f"the live runtime carries {len(live)} binds at "
                    f"{name_value(target)}; exact agreement is one")
        if live[0].get("source") != one["host_source"]:
            return (f"the live bind at {name_value(target)} comes from "
                    f"{name_value(live[0].get('source'))} and this plan binds "
                    f"{name_value(one['host_source'])}")
        if live[0].get("writable") is not one["writable"]:
            return (f"the live bind at {name_value(target)} is "
                    f"{'writable' if live[0].get('writable') else 'read-only'} "
                    f"and this plan composed "
                    f"{'writable' if one['writable'] else 'read-only'}")
    for held in observed:
        target = held.get("target")
        if target in expected or type(target) is not str:
            continue
        for fixed in expected:
            # BOTH DIRECTIONS. Review [P1]: this looked only for a bind at or
            # BELOW an expected target, so `/run/baton/integration` -- the
            # parent of two of the three -- was reported as agreement while
            # shadowing both of them. An ancestor bind decides what the
            # runtime reads at the paths underneath it, which is the same
            # defect from the other side.
            if target == fixed or target.startswith(fixed.rstrip("/") + "/") \
                    or fixed.startswith(target.rstrip("/") + "/"):
                return (f"the live runtime carries {name_value(target)}, which "
                        f"contains or is contained by "
                        f"{name_value(fixed)} and this integration did not "
                        f"authorize it")
    return None


def compatible_target(boundary):
    """Whether the bound target's own posture could admit the runtime's group.

    A DEPLOYMENT QUESTION ASKED BEFORE LAUNCH AND ANSWERED HONESTLY. This is
    not the worker's preflight and does not stand in for it: what a container's
    fixed uid may actually write is decided by the kernel over each affected
    file, and this manager's own `os.access` answers about this manager. What
    this establishes is the one thing a deployment can be told before a
    container exists -- that the target root carries the configured group and
    is group-writable, so a runtime holding that group has a posture it could
    work under.

    An incompatible target is refused for exact operator provisioning
    disposition. No recursive repair, no ownership change, no ACL workaround.
    """
    if type(boundary) is not IntegrationMountBoundary:
        _denied(f"a target posture is proved through this module's own "
                f"boundary; this is {name_value(boundary)}")
    place = boundary._sources[2]["host_source"]
    held = os.stat(place)
    return {"place": place, "gid": held.st_gid,
            "mode": stat.S_IMODE(held.st_mode)}


def prove_target_posture(boundary, workspace_group):
    """Refuse a target the configured group could not work in."""
    gid = workspaces.check_workspace_group(
        workspace_group.gid
        if type(workspace_group) is workspaces.WorkspaceGroup
        else workspace_group)
    held = compatible_target(boundary)
    # GROUP WRITE AND GROUP TRAVERSAL. Review [P1]: group-write alone does not
    # establish directory access -- a directory the runtime's group cannot
    # execute is one it cannot enter, so the write bit describes a permission
    # it can never reach.
    if held["gid"] != gid or not held["mode"] & stat.S_IWGRP \
            or not held["mode"] & stat.S_IXGRP:
        _denied(f"the canonical target at {name_value(held['place'])} is group "
                f"{held['gid']} mode {oct(held['mode'])} and this deployment "
                f"configured group {gid}; an integration runtime holds that "
                f"group as its only share in the target, and a target it "
                f"cannot work in is refused for operator provisioning rather "
                f"than repaired here")
    return held
