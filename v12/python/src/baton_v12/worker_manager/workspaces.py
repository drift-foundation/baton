"""ASSIGNMENT-PRIVATE WORKSPACES: where staged input sits, where a worker may
write, and what cleanup is allowed to remove.

W6631 built this component, and W15232 removed its acquisition half. What
remains is the generic manager-owned part of that Work, and the module contract
is written around it rather than around the operations that are gone.

FOUR THINGS THIS COMPONENT DOES:

  - `assignment_workspace` allocates two roots private to one assignment --
    `inputs`, read-only evidence, and `workspace`, the only writable tree. They
    are SIBLINGS rather than nested: a worker that could write into its own
    inputs would make the seal over them describe a tree that has since
    changed.
  - `directory_manifest` MEASURES a tree into the frozen `contentManifest`.
    Every entry is opened once with `O_NOFOLLOW`, and both its bytes and its
    size come from that one descriptor -- so a replacement between the check
    and the read is a file this component never sees rather than one it
    describes wrongly. Only bounded regular files; entries sorted bytewise,
    which is the order the tree digest is taken over and the order §12 rule 6
    checks.
  - containment, so a path that leaves the root it claims to be under is
    refused before anything opens it.
  - `discard_workspace` removes ONLY what this component created, including the
    read-only trees it made read-only, and says what it removed.

WHAT THIS COMPONENT NO LONGER DOES, and the ruling that ended it. The
2026-08-25 artifact-neutral supersession states that the Worker Manager "does
not understand Git, import bundles, resolve commits, prepare checkouts, or
choose a source-acquisition operation": it receives an ALREADY STAGED
read-only directory and its generic integrity envelope, and populating that
directory is a source stager's job, outside this package.

So the acquisition operations W6631 put here -- a repository port, and the
operations that delivered a version-controlled or copied source -- are gone
rather than re-homed, because re-homing requires an owner and the ledger has
none. Nothing here interprets an acquisition descriptor or names one.

NOR DOES IT ALLOCATE PRIVATE CAPACITY FOR ONE. There was a third root holding
version-control metadata, and every assignment got one whether its staged input
was a directory, an archive, a database snapshot, media or a format nobody has
written yet. Private ephemeral space is generic runtime capacity, not protocol
vocabulary this manager provisions; a stager or driver that needs it allocates
its own under an explicit owner.

The reasoning that was superseded lives in
`work/records/2026/08/finding-v12-artifact-neutral-source-stager/` and in
W6631's own record. It does not need to survive as the live module contract.
"""

import json
import os
import stat
from types import MappingProxyType

# W15232: `check_content_manifest` and `validate_fragment` went with the
# acquisition half. They were how this module READ a `gitSource` or
# `directorySource` descriptor and compared a claimed manifest against a
# measured one -- both acts of interpreting an acquisition contract, and
# neither one a manager that receives an already staged directory performs.
from ..contracts import (ContractRefusal, canonical_bytes, check_input_pair,
                        digest, digest_of_bytes)
from ..contracts.errors import label_of, name_value
from . import boundaries

# S_IFMT and S_IFREG, written out. The `stat` module is not on this package's
# declared standard-library allowlist and this is the only thing it would be
# imported for -- two constants a reader can check against `man 2 stat` are a
# smaller dependency than a module, and the alternative was widening a list a
# case exists to keep narrow.
_FILE_KIND = 0o170000
_REGULAR = 0o100000

# W15232: THE ACQUISITION HALF IS GONE, and what is left is the half the
# artifact-neutral ruling leaves with this manager.
#
# W6631 built `GitPort`, `materialize_git_source` and
# `materialize_directory_source` here. The 2026-08-25 supersession removed the
# duty they perform from the core manager entirely -- "the Worker Manager does
# not understand Git, import bundles, resolve commits, prepare checkouts, or
# choose a source-acquisition operation" -- and populating the staged input
# directory became a SOURCE STAGER's job, outside this package.
#
# REMOVED RATHER THAN RE-HOMED, and the difference was decided by looking. The
# assignment permits re-homing only behind an ALREADY PINNED stager or driver
# owner; the ledger has no such Work and the records name no such boundary, so
# inventing one to keep the code would have been inventing the second
# acquisition contract this Work exists to avoid. The behaviour is recoverable
# from W6631's own record and history if a stager is ever specified; what is
# not recoverable is the confusion of a manager that still exports it.
#
# WHAT STAYS IS GENERIC AND STILL THIS MANAGER'S: assignment-private paths, the
# read-only staged input tree, the measured `contentManifest` over a directory,
# containment, and cleanup. None of them knows where the bytes came from.
__all__ = ["INPUT_MANIFEST", "ASSIGNMENT_MANIFEST", "MAX_ENTRIES",
           "HOME_ENTRIES", "ROOT_NAMES", "WORKSPACE_DIR",
           "adopt_workspace_group", "check_workspace_group",
           "prove_workspace_group", "WorkspaceGroup", "AllocatedRoots",
           "WORKSPACE_GROUP_KEY", "CONFIGURE_OPERATION",
           "configure_workspace_group", "configured_workspace_group",
           "MAX_BYTES", "MAX_DEPTH", "READ_ONLY_DIR", "READ_ONLY_FILE",
           "assignment_workspace", "compose_input_root", "copied_manifest",
           "directory_manifest", "discard_tree", "discard_workspace",
           "read_input_root"]

# THE TWO MANAGER-AUTHORED PROTOCOL DOCUMENTS, at the names the contract fixes
# (§7.0). A path a manifest could vary is a path a runtime can be pointed at
# wrongly, so these are constants here for the same reason they are constants
# in the worker.
INPUT_MANIFEST = "input.json"
ASSIGNMENT_MANIFEST = "assignment.json"

# The frozen contract's own ceilings, so a manifest this component builds is one
# `contentManifest` can hold rather than one it would refuse after the work was
# done. `maxItems` on the entry array is 100,000; the byte total is the frozen
# safe-integer bound, and this component's own limit is far below it because a
# source larger than this is a configuration mistake rather than a workload.
# A protocol document this component reads back is a file from outside this
# call, so its size is not this function's decision and the bound has to be.
# The worker applies the same ceiling on the same two documents.
MAX_MANIFEST_BYTES = 4 * 1024 * 1024

MAX_ENTRIES = 100_000
MAX_BYTES = 4 * 1024 * 1024 * 1024
# Depth is bounded for the same reason the canonicalizer bounds it: a walk with
# no limit is a walk somebody else decides the cost of.
MAX_DEPTH = 64

# Read-only, and OWNER-ONLY. A delivered source is evidence: the worker reads
# it and nothing writes it again, and the mode says so on disk rather than in a
# comment. The execute bit stays on directories because a directory nobody may
# traverse is a directory nobody may read either.
# WORLD-READABLE, AND THAT IS THE POINT OF THE MODE RATHER THAN A RELAXATION
# OF IT.  W33935: these were 0o400 and 0o500 -- owner-only -- while the
# execution container runs as the fixed uid 65532 and the manager writes as
# whoever it happens to be.  Measured inside the real composed runtime, both
# `/input` documents were uid 1000 mode 0400 and BOTH READS FAILED WITH EACCES,
# so no worker could consume either of the two documents it is required to
# read.  The sibling launch delivery was 0o444 and readable, which is what
# demonstrated the shape rather than the diagnosis.
#
# WHAT MAKES THIS SAFE IS NOT THE MODE.  A worker cannot write here because the
# root is bind-mounted READ-ONLY -- the same probe got `EROFS` writing to
# `/input` itself, from the bind and not from any permission -- and it cannot
# reach the root through any other path because nothing else is mounted.  The
# mode's job is the HOST side: it says on disk that these bytes are finished,
# so this manager's own later mistake cannot rewrite the evidence a claim was
# made against.  Read permission was never part of that job, and taking it away
# protected nothing while breaking the one consumer.
#
# `launch.READ_ONLY_FILE` and `launch.READ_ONLY_DIR` are the same two values
# for the same reason, and `test_input_delivery` holds the two components to
# each other so a future edit cannot move one without the other.
READ_ONLY_FILE = 0o444
READ_ONLY_DIR = 0o555

# The two roots a container may be given, and every entry the assignment home
# holds.  They are different lists for a reason: `custody` is the material a
# worker must never reach after its freeze, and the two credential places are a
# bearer it is handed at one fixed path instead -- so none of the three is
# mountable, and all three are siblings under one home that has to be CLOSED
# once they exist.
# THE ONE WRITABLE ROOT'S EXACT MODE.  W33936: the workspace was left at
# whatever the process umask produced -- 0775 on the host this was measured on,
# and 0700 under the ordinary service umask 077.  Neither is a decision.
#
# 0770: OWNER AND GROUP MAY WRITE, AND NOBODY ELSE MAY DO ANYTHING.
#
# The narrowing is safe now and was not before, and the difference is the
# ruling: the execution container is given the configured workspace GROUP as a
# supplementary group, so it reaches this root through the group bits rather
# than through `other`.  An earlier cut narrowed to 0770 while the container
# held no share in the group, and the probe refuted it -- the worker lost read
# and traverse as well.  Narrowing belongs in the same change as the group, and
# this is that change.
#
# The superseded text below is kept as decision history.
#
# 0775 is EXACTLY WHAT THE UMASK HAPPENED TO PRODUCE on the host this was
# measured on, and that is the point: it is now a decision instead of an
# accident, and under the ordinary service umask 077 it no longer silently
# becomes 0700.
#
# NOT 0770, WHICH I TRIED FIRST AND THE PROBE REFUTED.  Dropping `other` looks
# like the narrower answer, and while the container still runs as 65532 with no
# share in this group it takes away the worker's READ and TRAVERSE as well --
# measured, `/workspace` went from `r=T x=T` to `r=F x=F`.  Narrowing to 0770
# belongs with the group wiring, in the same change, because it is only safe
# once the container holds the group.  The group bits here are what that wiring
# will use.
WORKSPACE_DIR = 0o2770

# Review [P0], approver ruling M34630: `02770` EXACTLY, and the setgid bit is
# not decoration.
#
# `0770` gives the group write.  What it does NOT give is the guarantee that
# what the WORKER creates stays in that group -- a container process whose
# primary gid is 65532 creates files owned `65532:65532`, and the manager, which
# is not 65532 and is not in that group, could then not collect the result it
# is required to collect.  Setgid on the directory makes every entry created
# inside it inherit the DIRECTORY's group instead, so the worker writes and the
# manager reads with no widening of anything.  Measured against a real daemon:
# a file the worker created came back `<worker>:<workspace group>`, and a
# directory it created carried the setgid bit onward.
#
# `other` HAS NOTHING, and that is the second half of the same choice.  This
# root is reachable only by its owner and by the one configured group; the
# earlier `0775` gave every process on the host read and traverse over an
# assignment's writable tree, which is authority nobody asked for.


# W33936 review [P1]: THE CONFIGURED GROUP IS A DEPLOYMENT FACT, AND THIS IS
# WHERE IT LIVES.
#
# The defect the review found: every layer took the same raw integer from its
# caller and every layer agreed, so a manager belonging to the configured group
# A and to some unrelated authority-bearing service group B could be handed B
# at allocation and at launch. The workspace was adopted into B, the pre-launch
# proof passed because it compared against the same operand, and `--group-add
# B` was composed. Four checks, one caller-selected value, and nothing to
# reject it with -- `check_workspace_group` can see shape, gid 0 and
# membership, and membership is exactly what B has.
#
# So there is one source of truth now and it is the control store's own
# metadata, written by a deployment act. `os.getgroups()` says what the manager
# CAN use; this says what the deployment SAID to use, and only the second
# authorizes anything.
WORKSPACE_GROUP_KEY = "workspace-group"

# The token that says this object came from the deployment's own record. A
# module-private sentinel rather than a flag, because a flag is something a
# caller can pass.
_MINT = object()


class WorkspaceGroup:
    """The deployment's configured group, as a FROZEN ANSWER.

    A capability rather than an integer, and that is the whole correction. An
    integer is a value any caller can compose; this can only be obtained from
    `configured_workspace_group`, which reads the deployment's own record. So
    the adapter and the run vector do not validate a number a caller supplied
    -- they refuse anything that is not this, and the only way to hold one for
    group B is for the deployment to have configured B.

    The same shape `credentials.Delivery` and `launch.LaunchDelivery` already
    have at this boundary, for the same reason: what crosses is a thing the
    manager made, not data describing one.
    """

    __slots__ = ("gid",)

    def __init__(self, gid, _minted=None):
        # MINTED ONLY BY THE READ OF THE DEPLOYMENT'S RECORD, which is what
        # makes this a capability rather than a wrapper. A type any caller can
        # construct would leave the hole exactly where the review found it:
        # the caller supplies group B, every layer type-checks happily, and
        # nothing has consulted what the deployment actually said.
        if _minted is not _MINT:
            _denied("a configured workspace group is obtained from this "
                    "manager's own record of what the deployment configured, "
                    "and is not constructed; a group a caller can mint is a "
                    "group a caller chose")
        object.__setattr__(self, "gid", check_workspace_group(gid))

    def __setattr__(self, name, value):
        _refuse("a configured workspace group is immutable", code="schema")

    def __repr__(self):
        return f"WorkspaceGroup({self.gid})"

    def __eq__(self, other):
        return isinstance(other, WorkspaceGroup) and other.gid == self.gid

    def __hash__(self):
        return hash(("WorkspaceGroup", self.gid))


def configure_workspace_group(store, gid):
    """The DEPLOYMENT's act: name the one dedicated workspace group.

    Approver rulings M34630 and M34916 divide this exactly: the deployment
    provisions one dedicated non-authority group and grants this manager
    permission to use it, and this manager never creates or modifies a host
    group. It validates what it is configured with -- and now it also RECORDS
    it, so a later caller cannot substitute another group the manager happens
    to hold.

    RE-CONFIGURING TO A DIFFERENT GROUP IS REFUSED rather than accepted. A
    manager already holding workspaces adopted into one group cannot be told
    the group is now another one without those roots becoming unreachable to
    the workers they were prepared for; a deployment that means to change it
    initializes a fresh store, which is the same clean-boundary rule the schema
    version is under. Re-affirming the SAME group is a no-op and commits.
    """
    from .store import manager_signature
    gid = check_workspace_group(gid)
    # THE JOURNAL, not the projection. Review [P1]: this asked `meta` whether
    # the manager was already configured, so a projection edit that made the
    # record disagree with the deployment's act also unlocked reconfiguring to
    # whatever the editor had put there. The committed operation is the one
    # account of this that a caller holding the store cannot rewrite without
    # the collision the journal is for.
    held = _committed_workspace_group(store)
    if held is not None and held != gid:
        _denied(f"this manager is already configured with workspace group "
                f"{held} and is being told to use {gid}; workspaces already "
                f"adopted into the first group would become unreachable to the "
                f"workers they were prepared for, so a changed group is a "
                f"fresh store rather than a reconfiguration")
    signature = manager_signature("workspace-group.configure", {"gid": gid})

    def act(connection):
        connection.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (WORKSPACE_GROUP_KEY, str(gid)))
        return {"workspace_group": gid}

    return store.transact("workspace-group.configure",
                          "workspace-group.configure", signature, act)


def _configured_gid(store):
    found = store._connection.execute(
        "SELECT value FROM meta WHERE key = ?",
        (WORKSPACE_GROUP_KEY,)).fetchone()
    if found is None:
        return None
    # ADOPTED, not trusted. This is a persisted value this process did not
    # write, and a store hand-edited to say `root` is exactly what the read
    # has to refuse rather than pass on.
    return check_workspace_group(int(boundaries.text(
        found["value"], "the configured workspace group's record"))
        if str(found["value"]).lstrip("-").isdigit() else found["value"],
        what="the recorded workspace group")


CONFIGURE_OPERATION = "workspace-group.configure"


def _committed_workspace_group(store):
    """The DEPLOYMENT'S OWN ACT, read out of the journal.

    Review [P1]: `configured_workspace_group` read `meta` and nothing else, so
    the capability was minted from a MUTABLE PROJECTION. A caller holding the
    store could leave the committed operation untouched, edit one row of
    `meta` to a second group it happened to hold, and be handed a capability
    for that group -- which then adopts workspaces and crosses `--group-add`.
    That is the arbitrary-held-service-group defect this Work exists to close,
    surviving in a second place.

    So the journal is the authority and `meta` is a cache of it. Three things
    are asked of the committed row, in the order that makes each meaningful:

    THE KIND, because a row of some other kind sitting at this identity is not
    a configuration however well its result reads.

    THE ANSWER THROUGH `replay`, so the committed result is decoded by the
    journal's own reader against the recorded signature rather than adopted as
    stored bytes -- and so a refused configuration is reproduced as the
    refusal it was rather than read past.

    THE SIGNATURE RECOMPUTED from the gid the answer names. The signature is a
    deterministic function of the operands, so a `result` column edited in
    place to name another group no longer agrees with the signature that was
    written beside it, and the disagreement is visible without a second copy
    of the value.
    """
    from .store import manager_signature
    held = store.operation_record(CONFIGURE_OPERATION)
    if held is None:
        return None
    if held["kind"] != CONFIGURE_OPERATION:
        _refuse(f"the journalled operation {CONFIGURE_OPERATION!r} is recorded "
                f"as kind {name_value(held['kind'])}; a row of another kind is "
                f"not this deployment's workspace group configuration",
                code="schema")
    _, committed = store.replay(CONFIGURE_OPERATION, held["signature"],
                                kind=CONFIGURE_OPERATION)
    answer = boundaries.document(committed,
                                 "the committed workspace group configuration",
                                 required=("workspace_group",))
    gid = check_workspace_group(answer["workspace_group"],
                                what="the committed workspace group")
    if held["signature"] != manager_signature(CONFIGURE_OPERATION,
                                              {"gid": gid}):
        _refuse(f"the journalled workspace group configuration names group "
                f"{gid}, which is not the group its recorded signature was "
                f"written for; the committed answer and the operands it was "
                f"committed under disagree", code="schema")
    return gid


def configured_workspace_group(store):
    """The deployment's frozen answer, or a refusal.

    THE ONLY WAY TO OBTAIN A `WorkspaceGroup`. Allocation and launch consume
    this; nothing else mints one, which is what makes "the configured group"
    a fact about the deployment rather than about whoever called.

    THE TWO ACCOUNTS MUST AGREE. The committed operation is the deployment's
    act and `meta` is this manager's projection of it, and a capability is
    minted only when they name the same group. A disagreement is `integrity/
    schema` and NOT a repair: this manager cannot say which of the two
    describes the deployment, and picking the journal silently would let an
    edit that should have been refused become an edit that was tolerated.
    Every direction of disagreement fails closed, including a projection that
    is merely absent -- a record this build cannot cross-check is not a record
    it will mint a group grant from.
    """
    projected = _configured_gid(store)
    committed = _committed_workspace_group(store)
    if projected is None and committed is None:
        _denied("this manager has no configured workspace group; the "
                "deployment provisions one dedicated non-authority group and "
                "records it before any execution workspace is allocated, and "
                "a group inferred from what the manager happens to hold is "
                "not a workspace grant")
    if committed is None:
        _refuse(f"this manager's record names workspace group {projected} with "
                f"no committed configuration behind it; a projection nobody "
                f"configured is not a deployment's act", code="schema")
    if projected is None:
        _refuse(f"the deployment configured workspace group {committed} and "
                f"this manager's record of it is gone; a configuration this "
                f"build cannot cross-check is not one it mints a group grant "
                f"from", code="schema")
    if projected != committed:
        _refuse(f"this manager's record names workspace group {projected} and "
                f"the deployment's committed configuration names {committed}; "
                f"a group the record was edited to name is not a group the "
                f"deployment configured", code="schema")
    return WorkspaceGroup(committed, _MINT)


def check_workspace_group(gid, *, what="the configured workspace group"):
    """The deployment's dedicated workspace group, validated and owned.

    W33936, approver ruling M34916.  The deployment provisions ONE dedicated
    non-authority group and grants this manager permission to use it.  This
    manager NEVER creates or modifies a host group: it validates the one it was
    configured with and fails closed on everything else.

    THERE IS NO DEFAULT, and that absence is the correction.  The rejected
    design read the workspace root's own gid, which measured as a user's LOGIN
    group -- reaching that user's home and everything in it, and on a gid-0
    manager reaching root's.  A group inherited from a service directory is not
    a workspace grant, so this refuses to infer one at all.

    THREE REFUSALS, each a different way for a configured value to be wrong:

      * gid 0 is the root group and carries authority over the whole host;
      * a gid this manager is not a member of is unusable -- it could neither
        `chgrp` the root to it nor be granted it -- and a configuration nobody
        can act on is a silent no-op rather than a policy;
      * a non-integer, a bool or a negative number is not a group id.
    """
    what = label_of(what)
    if type(gid) is bool or type(gid) is not int or gid < 0:
        _refuse(f"{what} is {name_value(gid)}; a group id is a non-negative "
                f"integer", code="schema")
    if gid == 0:
        _refuse(f"{what} is the root group; the workspace group is a "
                f"dedicated non-authority group provisioned for this purpose, "
                f"and root is the opposite of that", code="schema")
    held = set(os.getgroups()) | {os.getgid()}
    if gid not in held:
        _refuse(f"{what} is not a group this manager holds; a group it cannot "
                f"use is a configuration nothing can act on, and this manager "
                f"never creates or modifies a host group to make one work",
                code="schema")
    return gid


def prove_workspace_group(place, gid, *, what="the workspace root"):
    """The exact root still carries the configured group, and can be written.

    Review [P0], approver ruling M34630: "before the engine call, the adapter
    must prove that the canonical workspace root's group equals the configured
    group".  A grant established at allocation is not a grant at LAUNCH: a
    restart, a redeployment under a changed configuration, or an operator
    `chgrp` between the two leaves a root the worker cannot write and a
    container that finds out by failing halfway through its work.

    THE EXACT ROOT, and `lstat` rather than `stat`.  A symlink whose target
    carries the right group is not this root carrying it -- and this is the
    path the engine is about to bind, so what the engine will act on is what
    has to be proved.

    THE MODE IS PROVED TOO, because the group alone is not the grant.  A root
    in the right group at `0700` denies exactly what this whole correction is
    for, and it fails at the worker rather than here unless it is checked.
    """
    what = label_of(what)
    check_workspace_group(gid)
    try:
        found = os.lstat(place)
    except OSError as failure:
        _refuse(f"{what} at {name_value(place)} could not be measured before "
                f"the engine call: {type(failure).__name__}; a runtime is not "
                f"started over a root this manager cannot describe",
                code="path")
    if not stat.S_ISDIR(found.st_mode):
        _refuse(f"{what} at {name_value(place)} is not a directory", code="path")
    if found.st_gid != gid:
        # `policy.denied` rather than an integrity code, and the pairing is the
        # reason: nothing here is malformed. The root is well-formed and this
        # deployment is not permitted to run a worker over it, which is what
        # §9's policy category means.
        _denied(f"{what} carries group {found.st_gid} and this deployment is "
                f"configured with {gid}; the worker is granted the configured "
                f"group and would find the root in another one")
    if found.st_mode & 0o7777 != WORKSPACE_DIR:
        _denied(f"{what} is mode {oct(found.st_mode & 0o7777)} and an "
                f"execution workspace is {oct(WORKSPACE_DIR)}; the group's "
                f"write and the setgid inheritance are the grant, and a root "
                f"without them denies the worker the work it was started for")
    return place


def adopt_workspace_group(roots, gid):
    """Put the writable root in the configured group, exactly.

    `os.chown` with `-1` for the owner changes only the GROUP, which an
    unprivileged manager may do for a group it is a member of -- which
    `check_workspace_group` has already proved.  The mode is established here
    too, because group-writable is the whole point of the group and leaving it
    to the umask is what W33935 corrected at the two protocol documents.
    """
    place = roots["workspace"]
    gid = check_workspace_group(gid)
    try:
        os.chown(place, -1, gid)
    except OSError as failure:
        # NAMED, not swallowed.  A deployment whose manager cannot put its own
        # workspace in the configured group has a provisioning fault, and a
        # silently un-adopted root is the original defect arriving later and
        # from further away.
        _denied(f"the manager could not put {name_value(place)} in the "
                f"configured workspace group {gid}: "
                f"{type(failure).__name__}; the deployment provisions this "
                f"group and grants this manager membership, and without it "
                f"the worker cannot write the outputs it must declare")
    os.chmod(place, WORKSPACE_DIR)
    return place

ROOT_NAMES = ("inputs", "workspace")
HOME_ENTRIES = ("credential-state", "credentials", "custody") + ROOT_NAMES


def _refuse(message, code="path"):
    raise ContractRefusal("integrity", code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- canonical, contained roots ----------------------------------------------


def _real(path, what):
    """The canonical path, with every link already resolved.

    LEXICAL CONTAINMENT IS NOT CONTAINMENT. `..` in the spelling is the obvious
    escape and the one a normalizer catches; a symlink component is the one that
    looks perfectly ordinary until it is followed, and only the real path sees
    it.
    """
    # A LITERAL LABEL at the owner, and the caller's noun only in the prose
    # after it. The inventory attributes an owned entry by the label written at
    # the site, so a shared helper that owned under its caller's word would be a
    # boundary nothing could place -- and this helper is the single owner for
    # every path this component is handed.
    boundaries.text(path, "a filesystem root")
    if not os.path.isabs(path):
        _refuse(f"{what} is not an absolute path; a root this build cannot "
                f"name exactly is not a root")
    return os.path.realpath(path)


def _within(child, parent):
    """Strictly inside, and never merely sharing a prefix.

    `/srv/work-2` starts with `/srv/work` and is not inside it, which is why
    this compares SEGMENTS rather than characters.
    """
    if child == parent:
        return False
    return child.startswith(parent.rstrip(os.sep) + os.sep)


def _contained(path, root, what):
    real = _real(path, what)
    if not _within(real, root):
        _refuse(f"{what} resolves outside the storage this manager owns")
    return real


# -- the ceilings, and the ORDER they are applied in --------------------------


def _entry_ceilings(what, taken, max_entries):
    """The entry ceilings, checked BEFORE the next file is opened.

    TWO CEILINGS, TWO REFUSALS, and the difference is not cosmetic. This
    module's own `MAX_*` are POLICY -- what this build will handle at all,
    whoever asked. A caller's ceiling is part of a DELIVERY's declared
    contract, and a tree that exceeds it is an integrity failure of that
    delivery rather than a request this build declines. The taxonomy already
    distinguishes them and callers already depend on which one they get. When
    both are crossed the global one answers, because what this build will not
    do at all is decided before what this delivery was allowed.

    Review [P1]: this ran AFTER the crossing file had already been read, so
    the file the ceiling exists to refuse was read first -- work and memory a
    worker chose, spent on material this manager had already decided it would
    not take. `taken` is the count already accepted, so the file about to be
    opened is number `taken + 1`.
    """
    if taken + 1 > MAX_ENTRIES:
        _denied(f"{what} carries more than {MAX_ENTRIES} files")
    if max_entries is not None and taken + 1 > max_entries:
        _refuse(f"{what} carries more than the {max_entries} files its "
                f"declaration allows", code="limit")


def _byte_allowance(total, max_bytes):
    """How many more bytes this pass may accept, over BOTH ceilings.

    The SMALLER remaining allowance, because a read bounded by only one of
    them is unbounded with respect to the other. The reader takes this plus
    one byte: one byte past the line is what proves the line was crossed, and
    reading any further is work the crossing already made pointless.
    """
    allowance = MAX_BYTES - total
    if max_bytes is not None:
        allowance = min(allowance, max_bytes - total)
    return allowance


def _byte_ceilings(what, total, added, max_bytes):
    """The byte ceilings, over what the bounded read actually returned.

    This one CANNOT move before the read -- how large a file is, is what the
    read finds out. What makes it a bound rather than an observation is that
    the read it judges was itself given `_byte_allowance`, so `added` is at
    most one byte past the line however large the file grew while open. The
    same global-before-declared precedence `_entry_ceilings` states.
    """
    if total + added > MAX_BYTES:
        _denied(f"{what} carries more than {MAX_BYTES} bytes")
    if max_bytes is not None and total + added > max_bytes:
        _refuse(f"{what} carries more than the {max_bytes} bytes its "
                f"declaration allows", code="limit")


# -- measuring a directory ----------------------------------------------------


def directory_manifest(root):
    """The frozen `contentManifest` for a tree, MEASURED rather than declared.

    Every entry is opened once, with `O_NOFOLLOW`, and both its bytes and its
    size come from that one descriptor -- so a replacement between the check and
    the read is a file this component never sees rather than a file it
    describes wrongly.

    The entries come back sorted BYTEWISE, which is the order §12 rule 6 checks
    and the order the tree digest is taken over. Sorting by anything else would
    produce a manifest that recomputes to a different digest on a different
    locale.

    THE CEILINGS BOUND THE MEASUREMENT ITSELF rather than judging it after the
    fact: the entry count is checked before the next file is opened, and each
    read is given only the allowance still remaining. See `_entry_ceilings`
    and `_byte_allowance`.
    """
    what = "a source directory"
    real = _real(root, what)
    entries = []
    total = 0
    for place, relative in _walk(real, what):
        _entry_ceilings(what, len(entries), None)
        content = _read_exactly(place, relative, what,
                                allowance=_byte_allowance(total, None))
        _byte_ceilings(what, total, len(content), None)
        entries.append({"path": relative,
                        "bytes": len(content),
                        "content_digest": digest_of_bytes(content)})
        total += len(content)
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    return {"entries": entries,
            "entry_count": len(entries),
            "total_bytes": total,
            "tree_digest": digest(entries)}


def copied_manifest(root, into, *, max_entries=None, max_bytes=None,
                    admits=None):
    """Measure a tree and COPY it, in ONE no-follow pass.

    W26283. `directory_manifest` above is race-safe: it descends by opened
    directory identity and reads every file through a descriptor it proved is a
    regular file. A caller that measured with it and then copied by REOPENING
    each path threw that away -- and that is what W6634's staging did. Two
    harms were driven against it rather than argued:

      a measured subdirectory renamed and replaced with a symbolic link made
      the copy read THROUGH the link, so material from outside the tree
      entirely landed in the destination; and

      a measured regular file replaced with a FIFO made the copy's `open`
      block forever, which is one `mkfifo` stalling the caller indefinitely.

    Both are the defect this module's own walker records having fixed once --
    "a no-follow open of the FINAL file does not stop a raced ANCESTOR from
    becoming a symbolic link" -- reappearing in whoever copies afterwards. So
    the copy is not a second pass over path strings: the bytes WRITTEN are the
    bytes MEASURED, from the one descriptor that produced them, and there is no
    window between the two for anything to be replaced in.

    `max_entries` and `max_bytes` are the CALLER's declared ceilings, enforced
    as the walk runs rather than after it. A tree that exceeds them stops being
    copied at the entry that crosses the line, instead of being written whole
    and refused afterwards. Review [P1] tightened "as the walk runs" into
    BEFORE THE WORK IT REFUSES: the entry ceilings answer with nothing opened,
    and the read is handed the smaller remaining allowance so a file the
    worker grows while it is open cannot outrun the byte ceiling either.

    `admits(relative, content)` is a rule the caller applies to each file's
    bytes before they are written, and it raises to refuse. It exists so a
    caller's own content rule -- §13 live-secret scanning, for one -- runs at
    the one moment the content is in hand, without this function knowing what
    the rule is.

    Answers the same `contentManifest` shape `directory_manifest` does, over
    what was actually written.
    """
    what = "a source directory"
    real = _real(root, what)
    entries = []
    total = 0
    os.makedirs(into, exist_ok=True)
    for place, relative in _walk(real, what):
        # THE CEILING COMES BEFORE THE FILE IT REFUSES. Review [P1]: both
        # ceilings used to be judged on a file this loop had already read, so
        # the over-limit entry was opened and held in memory before anything
        # declined it -- and the byte read it judged had no bound of its own,
        # so a file growing while open could keep that refusal from ever being
        # reached. The entry count is decided here, with nothing opened; the
        # read below is given only what is left.
        _entry_ceilings(what, len(entries), max_entries)
        content = _read_exactly(place, relative, what,
                                allowance=_byte_allowance(total, max_bytes))
        _byte_ceilings(what, total, len(content), max_bytes)
        if admits is not None:
            admits(relative, content)
        target = os.path.join(into, relative)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        # THE DESTINATION IS OPENED NO-FOLLOW AND EXCLUSIVELY TOO. This
        # function is what makes bytes the caller's own, so a link left at a
        # destination name by an interrupted attempt -- or by anything else
        # that can write there -- must not become the thing written through.
        # `O_EXCL` is what makes it exclusive: the caller clears a partial
        # tree before calling, so an entry that already exists here is not one
        # this pass created.
        handle = os.open(target,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600)
        try:
            os.write(handle, content)
        finally:
            os.close(handle)
        entries.append({"path": relative,
                        "bytes": len(content),
                        "content_digest": digest_of_bytes(content)})
        total += len(content)
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    return {"entries": entries,
            "entry_count": len(entries),
            "total_bytes": total,
            "tree_digest": digest(entries)}


def _walk(real, what):
    """Every regular file under a canonical root, with its relative path.

    Refuses ON SIGHT, before anything is read: a link of either kind, a special
    file, a directory that is really a link, and a path that leaves the root.
    """
    # THE DESCENT IS BY OPENED DIRECTORY IDENTITY, not by path string.
    # Review [P1]: a no-follow open of the FINAL file does not stop a raced
    # ANCESTOR from becoming a symbolic link -- the listing said `deep` was a
    # directory, and by the time a later path string was resolved through it,
    # `deep` was a door out of the tree. Every directory is opened
    # `O_NOFOLLOW|O_DIRECTORY` and read THROUGH THAT DESCRIPTOR, and each
    # child is opened relative to it with `dir_fd`, so a component replaced
    # after it was listed is a directory this walk never entered.
    root = _open_directory(None, real, "", what)
    # EVERY DESCRIPTOR THIS WALK OPENS, so the `finally` can close all of them.
    # Review [P1]: the stack only held directories not yet descended into, so a
    # directory that WAS descended into leaked its descriptor for the life of
    # the generator -- and a deep tree exhausted the process's table. A walk
    # that owns descriptors owns closing them.
    opened = [root]
    stack = [(root, "", 0)]
    try:
        while stack:
            handle, prefix, depth = stack.pop()
            if depth > MAX_DEPTH:
                _denied(f"{what} nests deeper than {MAX_DEPTH} directories")
            # `scandir` on a descriptor lists THAT directory, whatever its
            # name now refers to.
            with os.scandir(handle) as listing:
                found = sorted(listing, key=lambda entry: entry.name)
            for entry in found:
                relative = f"{prefix}{entry.name}"
                if entry.is_symlink():
                    _refuse(f"{what} carries the symbolic link "
                            f"{name_value(relative)}; this build "
                            f"delivers only what a source directory literally "
                            f"contains, because a link materializes as content "
                            f"the assignment was never given")
                if entry.is_dir(follow_symlinks=False):
                    child = _open_directory(handle, entry.name, relative, what)
                    opened.append(child)
                    stack.append((child, f"{relative}/", depth + 1))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    _refuse(f"{what} carries "
                            f"{name_value(relative)}, which is "
                            f"neither a regular file nor a directory")
                yield (handle, entry.name), relative
    finally:
        for handle in opened:
            os.close(handle)


def _open_directory(parent, name, relative, what):
    """One directory, opened NO-FOLLOW and proved to be a directory.

    `O_DIRECTORY` is the second half: without it a name that became a regular
    file between the listing and this open would succeed, and the walk would
    then scandir something that is not a directory.
    """
    try:
        return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                       dir_fd=parent)
    except OSError as error:
        _refuse(f"{what} cannot enter "
                f"{name_value(relative or name)}: {error.strerror}; a "
                f"component replaced after it was listed is not one this walk "
                f"follows")


def _read_exactly(place, relative, what, *, allowance):
    """One file, opened once, with the descriptor deciding what it was.

    `O_NOFOLLOW` refuses a link AT the open rather than after it, and the
    identity is taken from `fstat` on the descriptor that produced the bytes.
    Anything a racing writer swaps in afterwards is a different file, and this
    never held it.

    A HARD LINK IS REFUSED HERE and not in the walk, because `st_nlink` is a
    property of the inode and the descriptor is what has one. A second name for
    the same inode is the same disclosure a symlink is, with nothing on the
    directory entry to see.

    `O_NONBLOCK` IS WHAT MAKES THE `fstat` REFUSAL REACHABLE. Review [P1]:
    `O_NOFOLLOW` protects only against a final symbolic link, and the walk's
    `is_file` answer is about the moment it LISTED the entry. A name that was a
    regular file then and is a FIFO now blocks this open until somebody writes
    -- so the descriptor-level proof below, the one guard a racing replacement
    cannot defeat, never runs at all, and one `mkfifo` stalls the manager
    indefinitely. This is the same interval `_open_directory` already covers
    for directories, on the file side of the walk. On a regular file the flag
    changes nothing: regular files are always ready, and the kind is proved
    from the descriptor before a byte is read either way.

    `allowance` IS A BOUND ON THE READ, and it is required because a reader
    with no bound is the defect. Review [P1]: `st_size` below was the only
    thing standing between a worker and an unbounded read, and it is not a
    bound at all -- it is one observation of a file the worker may keep
    writing to while this descriptor is open. The caller passes what is left
    of the smaller of its two ceilings; at most that plus one byte is taken,
    so growth after the `fstat` widens neither the work nor the memory, and
    the caller's refusal is reached rather than outrun.
    """
    # RELATIVE TO THE DIRECTORY WE OPENED, so the file is the one that
    # directory holds rather than the one its name resolves to now.
    parent, name = place
    try:
        descriptor = os.open(name,
                             os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent)
    except OSError as error:
        _refuse(f"{what} cannot read {name_value(relative)}: "
                f"{error.strerror}")
    try:
        stated = os.fstat(descriptor)
        # THE DESCRIPTOR'S OWN ANSWER, not the directory entry's. The walk
        # already refused anything that was not a regular file by name; this is
        # the same question asked of the thing actually opened, which is the
        # only one a racing replacement cannot have changed underneath.
        if stated.st_mode & _FILE_KIND != _REGULAR:
            _refuse(f"{what} entry {name_value(relative)} is not a regular "
                    f"file")
        if stated.st_nlink > 1:
            _refuse(f"{what} carries {name_value(relative)}, which "
                    f"is a hard link; a second name for one inode delivers "
                    f"content the assignment was never given, and leaves "
                    f"nothing on the directory entry to see")
        if stated.st_size > MAX_BYTES:
            _denied(f"{what} entry {name_value(relative)} is larger "
                    f"than {MAX_BYTES} bytes")
        content = _read_all(descriptor, allowance)
    finally:
        os.close(descriptor)
    return content


def _read_all(descriptor, allowance):
    """At most `allowance` + 1 bytes, however large the file becomes.

    ONE BYTE PAST THE LINE is exactly what the caller needs and no more: it
    proves the ceiling was crossed without reading however far past it the
    file went. A file that fits answers whole, because it stops at EOF first.
    """
    remaining = allowance + 1
    pieces = []
    while remaining > 0:
        piece = os.read(descriptor, min(remaining, 1 << 20))
        if not piece:
            break
        pieces.append(piece)
        remaining -= len(piece)
    return b"".join(pieces)


# -- one private workspace per assignment -------------------------------------


def assignment_workspace(workspace_group, storage, assignment_id):
    """TWO ROOTS, private to one assignment and never overlapping.

    `inputs` is read-only evidence and `workspace` is the only writable tree.
    They are siblings rather than nested for the reason the fourth rule states:
    a worker that could write into its own inputs would make the seal over them
    describe a tree that has since changed.

    W15232 review [P1]: there was a THIRD root holding version-control metadata
    for one assignment. It is gone, and the correction is worth naming because
    my own cut missed it. I separated this module's two halves by closing the
    CALL GRAPH over each, which treats a function as one node -- so this one
    came out "generic" while the acquisition-specific work sat INSIDE it. Every
    assignment got that metadata area whether its staged input was a directory,
    an archive, a database snapshot, media or a format nobody has written yet.
    That is the core manager understanding an acquisition format, which is
    exactly what the ruling removed.

    A future source stager or driver allocates its own private capacity under
    an explicit owner. Private ephemeral space is generic runtime capacity, not
    protocol vocabulary this manager provisions.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    # W33936 review [P0] then [P1]: THE GROUP IS THE DEPLOYMENT'S, AND THIS
    # FUNCTION READS IT RATHER THAN BEING TOLD IT.
    #
    # [P0] made it a required operand, because the previous cut left
    # `adopt_workspace_group` reachable and uncalled -- a grant that existed as
    # a function and not as a permission bit. That was necessary and not
    # sufficient: a required operand still lets a caller name any group the
    # manager happens to hold, including an authority-bearing service group,
    # and every later check agreed because every later check compared against
    # the same supplied value.
    #
    # So what crosses now is the FROZEN ANSWER rather than a number. Only
    # `configured_workspace_group` mints a `WorkspaceGroup`, and it mints one
    # by reading the deployment's own record -- so a caller holding one for
    # group B means the deployment configured B, and a caller that wants the
    # workspace in another group has to change the deployment.
    #
    # THE CAPABILITY RATHER THAN THE STORE, and the difference is not
    # cosmetic. This function is a filesystem operation; giving it a store
    # would give it a thread affinity it has no other reason to have, and a
    # concurrent allocation is exactly what it already promises to be safe
    # for. Consuming the answer is what the correction asks for; holding the
    # thing that produced it is not.
    if type(workspace_group) is not WorkspaceGroup:
        _denied(f"an assignment workspace is allocated into the deployment's "
                f"configured group, obtained from this manager's own record; "
                f"this is {name_value(workspace_group)}")
    workspace_group = workspace_group.gid
    root = _real(storage, "the manager's workspace storage")
    if not os.path.isdir(root):
        _refuse("the manager's workspace storage is not a directory")
    home = os.path.join(root, assignment_id)
    made = {}
    # EVERY ENTRY THE HOME WILL EVER HOLD IS PROVISIONED HERE, and the two
    # mountable roots are still the only thing this function ANSWERS with.
    #
    # W33935 re-review [P0]: freezing the `inputs` directory protects what is
    # inside it and nothing else -- rename and replacement of the entry ITSELF
    # are permissions of its PARENT, and the home was left at the process
    # default.  So the whole `0555` root could be renamed aside and a writable
    # one put at the same canonical path with different bytes in it.
    #
    # A parent can only be closed once nothing more needs to be created in it,
    # which is why `custody`, `credentials` and `credential-state` are made
    # now.  Those three are the adapter's and the credential home's, and
    # naming them here is coupling made explicit rather than coupling avoided:
    # the home is ONE directory with ONE layout, and
    # `test_input_delivery.TheHomeLayoutIsDeclaredWhereItIsFrozen` holds the
    # other two components to this list rather than trusting this comment.
    # EXCLUSIVE FIRST ALLOCATION, SEPARATED FROM RESTART LOOKUP.
    #
    # Approver ruling M34768 asks for unique never-reused per-attempt
    # directories and exclusive creation with collision refusal.  My first cut
    # put a publication check here, the restart path refuted it, and I then
    # concluded the two could not be separated at all -- which was wrong, and
    # the re-review proved it with a case I had not thought of: a stale home
    # whose `inputs` entry is a SYMLINK to another attempt's root.  That alias
    # is still contained by manager storage, so containment accepted it and a
    # second attempt received the first attempt's input root.
    #
    # The two ARE separable, and the proof is structural rather than a new
    # durable record.  A home is named by its attempt, so a home at this path
    # IS this attempt's -- provided its entries are genuinely its own
    # directories.  So every entry that already exists must be a real
    # directory, not a link, resolving to exactly the path under this home; an
    # entry that is anything else is stale or aliased state and fails closed.
    # An entry that does not exist is created here, which is the first
    # allocation.
    #
    # THIS KEEPS THE RESTART PATH, which is what the previous cut broke: a
    # restarted manager asking for the same attempt's roots finds real
    # directories at their own paths and is answered, because reopening an
    # attempt is not reusing an identity.
    # THE HOME IS PROVED BEFORE IT ANCHORS ANYTHING.
    #
    # Re-review [P0]: the first cut of this proof checked only
    # `os.path.isdir(home)`, which FOLLOWS SYMLINKS -- so a home that was
    # itself a link to another attempt passed, and the child proofs then
    # anchored on `realpath(home)`, which is the wrong sibling. Both sides of
    # every child comparison were relocated together and compared equal. A
    # structural proof applied to the children and not to the thing they are
    # measured against is not applied.
    expected_home = os.path.join(os.path.realpath(root), assignment_id)
    _own_directory(home, expected_home, "assignment home")
    for name in HOME_ENTRIES:
        place = os.path.join(home, name)
        _own_directory(place, os.path.join(expected_home, name),
                       f"{name} root")
        held = _contained(place, root, f"the assignment's {name} root")
        if name in ROOT_NAMES:
            made[name] = held
    # ESTABLISHED, NOT REQUESTED, and the GROUP with it.  `os.makedirs`
    # filters its mode through the umask; `os.chmod` on a directory that
    # already exists is exact, which is the same distinction W33935 corrected
    # at the two protocol documents.  `adopt_workspace_group` performs both,
    # so allocation and the grant are one step and a workspace this function
    # returns is one the worker can write.
    adopt_workspace_group(made, workspace_group)
    # W36540 review [P0]: THE ANSWER CARRIES ITS OWN PROVENANCE.
    #
    # A custody act has to be able to tell "this manager allocated these roots"
    # from "somebody made two directories with the expected names". Directory
    # SHAPE cannot make that distinction: any caller in this process can
    # `mkdir inputs; mkdir workspace` under a parent it owns and reproduce
    # every structural property. Shape may VALIDATE authority; it cannot
    # create it.
    #
    # So allocation mints a nominal type. It is still exactly a mapping --
    # every existing caller reads `roots["workspace"]` unchanged -- and a
    # plain dict is not an instance of it, which is the whole difference.
    return AllocatedRoots(made, _MINT)


class AllocatedRoots:
    """The roots THIS FUNCTION allocated, as an immutable READ-ONLY mapping.

    NOT A `dict` SUBCLASS, AND NOT A HOLDER OF ONE EITHER, and review [P0] is
    why that distinction is the whole design rather than a detail. Two rounds ago I minted a nominal type
    so shape could not manufacture authority. One round ago I overrode
    `__setitem__`, `update`, `pop` and the rest to stop a holder retargeting
    it. Both were bypassable in the same way, because a subclass of a mutable
    builtin still IS one:

        dict.update(roots, {"workspace": somewhere_else})
        dict.__setitem__(roots, "workspace", somewhere_else)
        roots |= {"workspace": somewhere_else}

    Every one of those reaches the base implementation without ever calling an
    override. **Overriding more methods cannot close explicit base-class
    invocation** -- the paths were stored in something whose mutators are part
    of its type, and the only fix is not to store them there.

    So the members live behind a `MappingProxyType` over a dict referenced
    nowhere else, and this class implements the read half of the mapping
    protocol and nothing else. The round after that one found the private
    attribute itself -- `roots._members.update(...)` needs no method of this
    class at all -- which is what the proxy closes.

    AND THE AUTHORITY NO LONGER RESTS ON ANY OF IT. `custody.attempt_custody_
    root` derives the attempt's workspace from the allocation operands instead
    of reading it out of this object, so what this class guarantees is that the
    ANSWER is not quietly edited, not that a mount is safe. Those were the same
    question for six review rounds and they are not the same question. There is no inherited
    mutator to call, `dict(roots)` and `roots["workspace"]` still work for
    every existing caller, and `dict.update(roots, ...)` now fails on its own
    argument type rather than quietly succeeding.
    """

    __slots__ = ("_members",)

    def __init__(self, made, _minted=None):
        if _minted is not _MINT:
            _denied("allocated roots are answered by `assignment_workspace` "
                    "and are not constructed; roots a caller can mint are "
                    "roots a caller chose")
        # A READ-ONLY VIEW OVER A DICT NOTHING ELSE HOLDS. W36540 review [P0],
        # sixth round: the members were an ordinary dict reachable through
        # ordinary attribute access, so `roots._members.update(...)` retargeted
        # both paths in place -- no method call to override, and therefore
        # nothing another round of overrides could have caught.
        #
        # `MappingProxyType` is not another override. The proxy has no mutating
        # operation at all, and the dict it wraps is created here and referenced
        # nowhere else, so there is no object left for a holder to edit.
        #
        # WHAT THIS STILL CANNOT PROMISE, said plainly: `object.__setattr__`
        # reaches any slot in this language, and no representation closes that.
        # That is why the real correction is elsewhere --
        # `custody.attempt_custody_root` no longer READS a path from this
        # object at all, it derives one from the allocation operands. This
        # makes the complaint false at its own site as well; it is not what the
        # guarantee rests on.
        object.__setattr__(self, "_members", MappingProxyType(dict(made)))

    # -- the read half of the mapping protocol, and only the read half ------
    #
    # `keys` and `__getitem__` are what `dict(roots)` and `**roots` are built
    # on, so every existing consumer keeps working unchanged.

    def __getitem__(self, key):
        return self._members[key]

    def __iter__(self):
        return iter(self._members)

    def __len__(self):
        return len(self._members)

    def __contains__(self, key):
        return key in self._members

    def keys(self):
        return self._members.keys()

    def items(self):
        return self._members.items()

    # NO `get` AND NO `values`. Nothing reads the roots that way, and adding
    # them would put `key` and `default` -- mapping-protocol words, not this
    # manager's operands -- into the declared operand vocabulary. The
    # dependency guard said so, and it is right: a public parameter here is a
    # domain operand or it should not exist.

    def __eq__(self, other):
        return dict(self._members) == other

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None

    def __repr__(self):
        return f"AllocatedRoots({self._members!r})"

    def __setattr__(self, name, value):
        _refuse("allocated roots are the answer this manager gave about one "
                "assignment and are immutable", code="schema")

    def __delattr__(self, name):
        self.__setattr__(name, None)

    def copy(self):
        """A PLAIN dict, deliberately.

        A copy is not the answer this manager gave; it is a caller's own
        mapping that happens to hold the same strings, and typing it as one
        would hand back exactly the forgery the mint refuses.
        """
        return dict(self._members)

    # -- every mutating door this type OWNS, refused in our own words -------
    #
    # It does not inherit any, so these exist for the DIAGNOSTIC rather than
    # for the guarantee: a caller reaching for one gets a sentence about why
    # the answer is fixed instead of a bare TypeError. The guarantee is that
    # the members are not in a mutable builtin at all.
    #
    # `dict.update(roots, ...)` and `dict.__setitem__(roots, ...)` are NOT on
    # this list and cannot be: they fail in Python, on the argument type,
    # because this is not a dict. That refusal is stronger than one we could
    # write, and it is the one the previous two cuts could not produce.

    def _frozen(self, *args, **members):
        _refuse("allocated roots are the answer this manager gave about one "
                "assignment and are immutable; a holder that could retarget "
                "them would be choosing the directory the answer names",
                code="schema")

    __setitem__ = _frozen
    __delitem__ = _frozen
    __ior__ = _frozen
    update = _frozen
    setdefault = _frozen
    pop = _frozen
    popitem = _frozen
    clear = _frozen


def _own_directory(place, expected, what):
    """Create this directory, or PROVE the one already there is ours.

    ONE OPERATION, not a test and then a create.  Re-review [P1]: those were
    two steps -- `lexists` and then `makedirs` -- and two callers could both
    observe absence, after which one created the directory and the other
    received a raw `FileExistsError` from the OS.  An ordinary manager race
    became an unexpected fault, and a fault is not a contract answer.

    So the create is ATTEMPTED and its collision is the branch.  A caller that
    loses the race falls through to exactly the proof a pre-existing directory
    gets, and reopens it when it really is this attempt's own -- which is the
    same question, asked once, whether the directory has been there for a
    week or for a microsecond.

    THE PROOF IS NO-LINK AND EXACT-PATH.  A link is refused even when it
    points inside manager storage: what makes a root private is that it IS
    this attempt's directory, not that it lands somewhere this manager owns.
    """
    try:
        os.mkdir(place)
        return place
    except FileExistsError:
        pass
    except OSError as failure:
        _refuse(f"the manager's {what} could not be created at "
                f"{name_value(place)}: {type(failure).__name__}", code="path")
    if os.path.islink(place) or not os.path.isdir(place) \
            or os.path.realpath(place) != expected:
        _refuse(
            f"{name_value(place)} already exists and is not this attempt's "
            f"own {what} at its own path; a stale or aliased "
            f"directory is refused rather than adopted, because material "
            f"under it would be another attempt's",
            code="path")
    return place


def compose_input_root(inputs, input_manifest, assignment_manifest, *,
                       assignment, runtime_attempt_id):
    """Materialize BOTH `/input/` documents, in the order the ruling fixes.

    W19784, approved 2026-08-26. §7.0's lifecycle is normative and this is the
    one place that performs it:

      `input.json` is authored BEFORE claim and its bytes and digest never
      change afterwards -- it is the pre-claim evidence the result is measured
      against;
      `assignment.json` is materialized AFTER the claim commits, carrying the
      live assignment identity the completion envelope must copy;
      NO CONTAINER OBSERVES THE ROOT DURING THAT TRANSITION, and only once both
      documents are complete is the whole surface exposed read-only.

    So this refuses rather than repairs when the root is already composed. A
    manager that rewrote `input.json` here would be changing the evidence after
    the claim that was made against it, and one that replaced `assignment.json`
    would be moving an identity a running worker may already have copied.

    THE PAIR IS VALIDATED BEFORE ANYTHING IS WRITTEN (§12 rule 16). Two
    documents that are not one delivery must never exist on disk together: a
    mount is not the last chance to notice, it is the first moment it is too
    late.

    AND THE PAIR IS HELD TO THE MANAGER'S OWN LIVE IDENTITY. W19784 review
    [P0]: this took the two documents alone, so it could prove only that they
    AGREE WITH EACH OTHER -- and a self-consistent pair minted for a superseded
    generation or another runtime attempt agrees with itself perfectly. It
    would have been written, mounted, and caught only at the freeze, after the
    agent had already run against material this manager never authorized.

    So `assignment` and `runtime_attempt_id` are REQUIRED KEYWORD OPERANDS,
    the manager's own values out of the attempt row, and there is no default:
    a caller that could omit them would be a caller that composes an
    unauthenticated root, which is the defect. The generation and the attempt
    are proved here, BEFORE the root exists, rather than at custody.

    Returns the two absolute paths it wrote.
    """
    root = _real(inputs, "the assignment's inputs root")
    if not os.path.isdir(root):
        _refuse("the assignment's inputs root is not a directory")
    expected = boundaries.document(
        assignment, "the manager's own assignment",
        required=("work_ref", "participant", "generation"))
    boundaries.identity(runtime_attempt_id, "a runtime attempt identity")
    # VALIDATED FIRST, AND BY THE SHIPPED RULE rather than a second copy of it.
    owned_input, owned_assignment = check_input_pair(
        input_manifest, assignment_manifest,
        what="the execution input root")
    # THEN AGAINST WHAT THIS MANAGER OWNS. The order is the content: the pair
    # rule proves the documents are one delivery, and this proves that one
    # delivery is THIS one. Neither implies the other.
    if owned_assignment["assignment_ref"] != expected:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the assignment manifest for this input root names "
            f"{name_value(owned_assignment['assignment_ref'])}, and this "
            f"manager is composing a root for "
            f"{name_value(expected)}; a pair that agrees with itself is not "
            f"thereby the delivery that was authorized")
    if owned_assignment["runtime_attempt_id"] != runtime_attempt_id:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the assignment manifest names runtime attempt "
            f"{name_value(owned_assignment['runtime_attempt_id'])} and this "
            f"root is being composed for "
            f"{name_value(runtime_attempt_id)}; a worker mounting it would "
            f"publish an envelope this attempt cannot settle")
    written = []
    for name, owned in ((INPUT_MANIFEST, owned_input),
                        (ASSIGNMENT_MANIFEST, owned_assignment)):
        place = os.path.join(root, name)
        if os.path.lexists(place):
            _refuse(f"{name_value(place)} already exists; the input root is "
                    f"composed once and then frozen, and rewriting a protocol "
                    f"document under a claim that was made against it would "
                    f"change the evidence the result is measured by",
                    code="path")
        written.append(_write_read_only(place, canonical_bytes(owned), name))
    # AND THEN THE ROOT IS FROZEN, which is the half the file modes cannot do.
    #
    # W33935 review [P0]: `READ_ONLY_DIR` existed, was exported, and NOTHING
    # applied it -- this function wrote both documents at 0444 and returned,
    # leaving the root at 0775.  A 0444 file inside a writable directory is not
    # protected: unlink and rename are permissions of the DIRECTORY, so the
    # manager's own uid, or anything sharing its group, could remove either
    # document and put a different one at the same name -- underneath a worker
    # that had already mounted it.  The read-only bind stops the container
    # writing; it does not stop the host replacing a bound file.
    #
    # AFTER BOTH DOCUMENTS ARE DURABLY INSTALLED, because a root frozen between
    # them could not receive the second one.  §7.0 fixes that order: the pair
    # is composed and only then is the whole surface exposed.
    #
    # `os.chmod` ON THE ROOT is exact and was never umask-filtered -- the umask
    # applies to CREATION, and this directory already exists.  0555 rather than
    # 0500 for the same reason the files are 0444: the container's fixed uid is
    # not this manager's, and a root it cannot traverse is a root whose
    # readable documents it cannot reach.
    #
    # THE CLEANUP PATH IS UNAFFECTED AND THAT IS MEASURED, not assumed:
    # `_remove` makes each directory writable as it goes, inside a tree
    # `discard_workspace` has already proved contained, so a frozen root is
    # removable by the manager that owns it and by nothing else.
    os.chmod(root, READ_ONLY_DIR)
    # AND THE PARENT, which is the only thing that governs the root's own
    # ENTRY.  Re-review [P0]: `0555` on `inputs` denies create, unlink and
    # rename INSIDE it; renaming or replacing `inputs` itself is a write to
    # the home, and the home was writable -- so the frozen root could be moved
    # aside and a `0775` one put at the same canonical path.
    #
    # Safe to close now because `assignment_workspace` provisioned every entry
    # this home will ever hold.  What still happens afterwards -- an attempt's
    # custody tree, a volatile credential root, a durable credential record --
    # is created INSIDE those entries, which this mode does not govern.
    os.chmod(os.path.dirname(root.rstrip("/")), READ_ONLY_DIR)
    return tuple(written)


def read_input_root(inputs):
    """The two composed `/input/` documents, read back OFF DISK and validated.

    W19784 review [P0]: the launch path has to prove the root a runtime is
    about to mount, and what the runtime mounts is the disk -- not a value
    threaded down from whoever composed it. So this reads the bytes and puts
    them through the same shipped `check_input_pair` the composition used.

    It deliberately does NOT take an expected identity. Holding the pair to the
    manager's live assignment is `attempts.authorize_input_root`, which is
    where the attempt row is: this component owns paths and documents, and
    which assignment is live is not a fact it has.
    """
    root = _real(inputs, "the assignment's inputs root")
    if not os.path.isdir(root):
        _refuse("the assignment's inputs root is not a directory")
    found = {}
    for name in (INPUT_MANIFEST, ASSIGNMENT_MANIFEST):
        place = os.path.join(root, name)
        try:
            with open(place, "rb") as reading:
                raw = reading.read(MAX_MANIFEST_BYTES + 1)
        except OSError:
            _refuse(f"the input root carries no readable {name_value(name)}; "
                    f"a root missing a protocol document is one no runtime "
                    f"may mount", code="path")
        if len(raw) > MAX_MANIFEST_BYTES:
            _refuse(f"{name_value(name)} is wider than "
                    f"{MAX_MANIFEST_BYTES} bytes", code="limit")
        try:
            found[name] = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            _refuse(f"{name_value(name)} is not a readable document",
                    code="schema")
    return check_input_pair(found[INPUT_MANIFEST], found[ASSIGNMENT_MANIFEST],
                            what="the composed input root")


def _write_read_only(place, payload, name):
    """One protocol document, published atomically and then made evidence.

    ATOMIC because a half-written protocol document under its final name is
    indistinguishable from a complete one, and this root is about to be handed
    to a container that reads exactly these two names.

    READ-ONLY because the mode says on disk what the contract says in prose. A
    bind mounted read-only protects the container's view; it does not protect
    the host copy from this manager's own later mistake.
    """
    staged = place + ".composing"
    # CREATED UNREADABLE AND NO-FOLLOW, then made evidence on the DESCRIPTOR.
    #
    # W33935, and it is the second time this exact defect has been corrected in
    # this distribution: W26291 review [P0] found it at the launch delivery and
    # fixed it there, and the same line here was never revisited.  A creation
    # mode is FILTERED BY THE PROCESS UMASK, so passing `READ_ONLY_FILE` to
    # `os.open` authors 0444 under umask 022 and 0400 under the ordinary
    # service umask 077 -- the unreadable document arriving silently, and only
    # on some hosts.  Requesting a mode is not establishing one.
    #
    # `O_NOFOLLOW` so a link left at the staging name is refused rather than
    # written through, mode 0 so the file is never readable while it is still
    # partial, and `fchmod` ON THE DESCRIPTOR THIS FUNCTION WROTE rather than a
    # second `chmod` by name -- the name could be something else by then and
    # the descriptor cannot be.  It runs after the last byte, so the document
    # becomes readable exactly when it becomes complete.
    handle = os.open(staged,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o000)
    try:
        written = 0
        while written < len(payload):
            moved = os.write(handle, payload[written:])
            if moved <= 0:
                _refuse(f"the manager's {name_value(name)} could not be "
                        f"written whole", code="limit")
            written += moved
        os.fsync(handle)
        os.fchmod(handle, READ_ONLY_FILE)
    finally:
        os.close(handle)
    os.replace(staged, place)
    return place


def discard_workspace(storage, assignment_id):
    """Remove ONLY what this component created, and say what it removed.

    Recoverable rather than exact: a tree already gone is the state this asks
    for, so it answers `False` instead of refusing. What it will not do is
    delete anything outside the storage root it was given -- the containment
    check runs before the removal and not after.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    root = _real(storage, "the manager's workspace storage")
    home = os.path.join(root, assignment_id)
    if not os.path.exists(home):
        return False
    _contained(home, root, "the assignment's workspace")
    _remove(home)
    return True


def discard_tree(place):
    """Remove one tree this manager owns, whatever its modes are now.

    W26283. `copied_manifest` refuses a destination that already holds an
    entry, so a caller whose earlier attempt stopped part-way needs a way to
    take that prefix away -- and custody is FROZEN READ-ONLY when it is
    complete, so a partial tree from a stopped process may be unwritable too.
    `_remove` already makes each directory writable as it goes and never
    follows a link out of the tree, which is the whole duty.

    It is here rather than in the caller because the caller would otherwise
    reach for `shutil.rmtree`, and the manager's ruled dependency set does not
    include it -- a rule the repository enforces and which caught exactly that
    import. `rmtree` would also be the weaker answer: it has followed links
    out of a tree before, and this module already owns not doing that.

    Answers whether anything was there, so an absent tree is the state asked
    for rather than a refusal.
    """
    if not os.path.isdir(place):
        return False
    _remove(place)
    return True


def _thaw(place):
    """Open this directory enough to empty it, IF this manager may.

    W33936: it may not always, and that is a fact about the corrected
    mechanism rather than a fault here.  `chmod` is the OWNER's operation, and
    once the worker can write the workspace it creates directories it owns --
    so a manager holding only the configured group is refused `EPERM` on them.
    Swallowing that is right: the thaw is an ATTEMPT to make removal possible,
    and whether removal is possible is answered by removal.  What is not right
    is letting the raw error out of a helper whose caller cannot tell it from
    a missing directory, which is why the two are separated here.
    """
    try:
        os.chmod(place, 0o700)
    except PermissionError:
        return False
    return True


def _remove(place):
    """A depth-first removal that never follows a link out of the tree."""
    for current, directories, files in os.walk(place, topdown=False,
                                               followlinks=False):
        # THAWED ONCE, BEFORE ANYTHING IN IT IS REMOVED.  Unlinking a file and
        # removing a subdirectory are both writes to THIS directory, so the
        # thaw belongs here rather than inside the file loop -- W33935
        # re-review: once the assignment home was frozen, a home holding only
        # directories never reached that loop and `rmdir` on its children was
        # denied by the home's own mode.
        _thaw(current)
        for name in files:
            _unlink(os.path.join(current, name), current)
        for name in directories:
            child = os.path.join(current, name)
            if os.path.islink(child):
                _unlink(child, current)
                continue
            # The child was already thawed when the walk visited it; this is
            # the one it could not have reached, a directory that is empty.
            _thaw(child)
            _unlink(child, current, directory=True)
    _thaw(place)
    os.rmdir(place)


def _unlink(child, parent, *, directory=False):
    """Remove one entry, and say WHOSE it is when it cannot be removed.

    W33936: a raw `PermissionError` out of a cleanup walk names a path and
    nothing else, and the situation this correction creates is specific enough
    to deserve a sentence.  The workspace is writable by the configured group,
    so the worker creates content this manager DOES NOT OWN -- and a directory
    the worker created under its own umask can be one the manager may neither
    open for writing nor `chmod`.  The removal fails closed, which is right;
    what a diagnostic has to add is which party owns the thing in the way, so
    an operator is not left comparing modes by hand.
    """
    try:
        os.rmdir(child) if directory else os.unlink(child)
        return
    except PermissionError:
        # ONLY THIS ONE IS REWORDED.  A non-empty directory, a vanished entry
        # or a device error mean what they say and are the walk's to raise; a
        # permission refusal is the one whose cause is invisible in the message.
        pass
    held = os.lstat(child)
    owner, mode = held.st_uid, oct(held.st_mode & 0o7777)
    _denied(f"the manager could not remove {name_value(child)}: it is owned "
            f"by uid {owner} at mode {mode} and this manager is uid "
            f"{os.getuid()}. A workspace the worker may write holds content "
            f"the worker owns, and neither `chmod` nor a write inside it is "
            f"this manager's to perform. Cleanup fails closed rather than "
            f"leaving a partly-removed tree.")
