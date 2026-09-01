"""THE ASSIGNMENT-SCOPED CREDENTIAL LIFECYCLE: slots in, nothing durable out.

W6634, `work/records/2026/08/finding-v12-sealed-output-credentials/`. The
mechanism is not chosen here -- it is the approver's ruling of 2026-08-26 and
its supersession in message 16691, recorded in that dossier's `FINDING.md`, and
this module implements it rather than re-deciding it.

THE FOUR PARTIES, and the whole design is the boundary between them:

  THE ASSIGNMENT names one or more authorized LOGICAL SLOTS and nothing else.
                 Never bearer bytes, never a host path, never a provider
                 reference -- an assignment that could name any of those could
                 point this manager at material nobody authorized.
  THE PROFILE    is TRUSTED deployment state. It maps each slot to a provider
                 and that provider's OPAQUE reference. Opaque is load-bearing:
                 this module proves the reference is text and never reads a
                 meaning out of it, because the moment it does, the profile has
                 become a second place that decides what a credential is.
  THE PROVIDER   is an injected capability. It is trusted to be the deployment's
                 and NOT trusted to be correct, so what it answers is owned like
                 any other injected value.
  THE WORKER     sees exactly one thing: the fixed read-only directory root
                 `/run/baton/credentials`, whose entries are the closed slot
                 names. It is told where to look by a constant of this contract,
                 not by an operand -- a path an assignment can vary is a path a
                 context can be pointed at wrongly.

WHERE THE BYTES ARE ALLOWED TO BE. In one manager-owned volatile file per slot,
mode 0640 in the deployment's configured workspace group, under a 0700
assignment-private root, and in the in-memory live-secret registry. W52800:
the mode was 0600 and the worker could not read what it was delivered -- the
group bits are the grant the execution runtime already holds, and `other` stays
empty because this is a bearer rather than evidence.

That is the entire list. §13 bars the value from argv, environment, image
layers, labels, logs, durable state, protocol Events and output metadata, and
every function below that produces a durable document walks it before it
returns.

THE REGISTRY IS THE POINT, not a formality. It is registered BEFORE the bytes
reach a file and released only after teardown is PROVED, which is what makes
every §13 walk between those two moments -- the sealed result, the collection
observation, the staged artifact CONTENT -- a real check rather than a walk over
an empty registry. A registry that is empty while a bearer is mounted into a
running worker is the vacuous shape this campaign has been corrected for
repeatedly: the check passes because there is nothing to find.

WHICH IS ALSO WHY A RESTART RE-REGISTERS. `adopt` reads this manager's own
volatile files back to put their values in the registry again. The superseded
one-file proposal said nothing reads the value back, and for the bearer's own
sake that is still true -- nothing publishes it, compares it or puts it in an
observation. But a restarted manager that adopted an attempt WITHOUT
re-registering would seal that attempt's output with the leak check silently
disarmed, and a check that cannot fail is worse than no check because it reads
as evidence.

TEARDOWN IS ONE ORDERED ACT ON EVERY ENDING -- success, failure, cancellation.
Files removed, root removed, durable state removed, each PROVED absent, and only
then is the bearer forgotten. If any of it cannot be proved, this refuses:
cleanup uncertainty is not settlement and is not a free worker slot, and the
frozen output may sit quarantined while the credential lifecycle stays open.
"""

import json
import os
import re
import stat

from ..contracts import (ContractRefusal, check_no_durable_secret,
                         forget_secret, remember_secret)
from ..contracts.errors import name_value
from . import boundaries

__all__ = ["CREDENTIAL_ROOT", "LIFECYCLE_STATES", "MAX_BEARER", "MAX_ORPHANS",
           "MAX_SLOTS", "VOLATILE_DIR", "VOLATILE_FILE", "CredentialHome",
           "Delivery", "OrphanTeardown", "resolved_delivery", "slot_name"]

# THE FIXED CONTAINER ROOT. A constant of this contract and not an operand --
# approver ruling, and the reason is the same one W14828 names for a launcher:
# a path a caller can vary is a path a context can be pointed at wrongly.
CREDENTIAL_ROOT = "/run/baton/credentials"

# A SLOT NAME BECOMES BOTH A FILENAME AND A CONTAINER PATH SEGMENT, so its
# grammar is a containment rule rather than a style. `boundaries.identity`
# proves it is storable text; this proves it cannot leave the root it names an
# entry of. Lower case because two spellings of one slot are two slots on a
# case-sensitive filesystem and one slot on an insensitive one.
_SLOT = re.compile(r"\A[a-z0-9][a-z0-9._-]{0,62}\Z")

# How many slots one assignment may authorize. Bounded because the delivery
# becomes that many mounts, that many files and that many registry entries, and
# an unbounded list is an unbounded act.
MAX_SLOTS = 16

# The widest bearer this manager will hold. §13's own note records that the
# contract admits 32 to 4096 characters; the upper bound is enforced because a
# value that cannot be a credential should not reach a file, and the lower one
# is NOT, because refusing a deployment's short-but-real credential would be
# this module overruling the provider about what a credential is.
MAX_BEARER = 4096

# How many stale volatile roots one cleanup pass removes. Bounded on purpose:
# the approver's ruling says orphan cleanup is bounded, and a pass that ran
# until the directory was empty would be an unbounded act inside an ending.
MAX_ORPHANS = 64

VOLATILE_DIR = 0o700

# THE LIVE SLOT'S EXACT MODE, and the ruling that decided it.
#
# W52800, approver ruling 2026-08-31, found by `attempt-w51487-run3`. This was
# `0o600` and manager-only, which is the right answer to "who owns the bearer"
# and the wrong answer to "who READS it": the execution container runs as the
# fixed uid 65532, so a manager-owned owner-only file is one the worker can
# `stat` and cannot open. Measured inside the real runtime, `os.path.exists`
# answered True, `os.access(R_OK)` answered False, and the provider reported
# `Not logged in` and exited 1 -- an opaque failure three layers from its cause.
#
# 0640 AND NOT 0444, and the difference is the whole ruling. `/input` is
# evidence and W33935 made it world-readable; this is a BEARER. The execution
# runtime already holds the deployment's configured workspace group as a
# supplementary group (W33936, `--group-add`), so the group bits are a grant
# that already exists and `other` stays empty.
#
# ONE NAME AND ONE ANSWER. Review 2026-08-31T13:56:33Z [P1]: the first cut
# added a SECOND constant at `0o640` and kept this one at `0o600` beside it
# "as decision history", so this module exported two authoritative-looking modes
# for one file and the suite asserted both. A future caller reaching for the
# established name would have recreated the defect with a constant that said
# it was the contract. Decision history belongs in the append-only finding;
# an exported constant is an executable claim about what is true NOW.
VOLATILE_FILE = 0o640

# What a lifecycle record may say a delivery IS. Durable state may name the
# logical slot, the provider identity and the lifecycle state -- never the
# bearer and never a reusable bearer digest, which is a bearer somebody can
# confirm a guess against.
LIFECYCLE_STATES = ("live", "adopted", "torn-down")

_STATE_MEMBERS = ("attempt_id", "runtime_id", "credential_root",
                  "container_root", "slots", "lifecycle_state")
_SLOT_MEMBERS = ("slot", "provider", "target")
_MAPPING_MEMBERS = ("provider", "reference")


def _refuse(message, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _list(value, what):
    """A caller's sequence, as a plain list.

    `boundaries` has no list kind because a list is not a boundary -- what
    crosses is the MEMBERS, and each is owned by its own rule. The same
    two-part shape `sealing._list` uses one file over.
    """
    if type(value) not in (list, tuple):
        _refuse(f"{what} is a list; this is {name_value(value)}")
    return list(value)


def slot_name(value):
    """One logical slot name, proved as an entry of the fixed root.

    PUBLIC because the adapter applies the same rule to the CONTAINER side of a
    mount, and one rule with two spellings is a rule that holds in one of the
    two places. `errors.py` says this about `name_of` in its own docstring and
    declines to reach past a package's surface for it; the answer here is to put
    the rule on the surface rather than to reach past it or copy it.

    AND IT TAKES NO CALLER NOUN, unlike every rule in `boundaries.py`. That
    layer is the one place a `what` parameter belongs: it is excluded from the
    derived inventory precisely because it IS the layer. A public function
    anywhere else that took one would be adding a receiving entry that carries
    nothing but prose -- so the label is this rule's own, and the refusal names
    the value that failed it.
    """
    # THE LABEL IS LITERAL. The boundary inventory attributes an owned entry by
    # the label written at the site, and a label that is only an f-string of a
    # parameter is one it cannot place -- the correction `sealing._relative`
    # was made for, one file over.
    name = boundaries.identity(value, "a credential slot name")
    if not _SLOT.match(name) or name in (".", ".."):
        _refuse(f"a credential slot name is a lower-case entry of "
                f"{CREDENTIAL_ROOT}; {name_value(name)} could name something "
                f"else", code="path")
    return name


def _authorized_slots(slots):
    """The assignment's closed logical slot names, and NOTHING else.

    The refusal a caller is most likely to hit here is the one worth having:
    an assignment that hands a document rather than a name is an assignment
    trying to carry a provider reference or a host path, which the approved
    boundary forbids by construction rather than by inspection.
    """
    if type(slots) not in (list, tuple):
        _refuse(f"an assignment's authorized credential slots are a list of "
                f"names; this is {name_value(slots)}")
    if len(slots) > MAX_SLOTS:
        _refuse(f"an assignment authorizes at most {MAX_SLOTS} credential "
                f"slots; this one names {len(slots)}", code="limit")
    if not slots:
        # A DELIVERY WITH NO SLOTS IS NOT A DELIVERY. It would be a root and a
        # lifecycle record describing nothing, and every mount comparison over
        # it would be vacuously satisfied -- a restart would adopt any container
        # at all. An assignment that authorizes no credential gets no delivery,
        # which the adapter already expresses as `credential_delivery=None`.
        _refuse("an assignment that authorizes a credential names at least "
                "one slot; a delivery describing nothing is one every "
                "comparison agrees with")
    taken = []
    for entry in slots:
        if type(entry) is not str:
            _refuse(f"an authorized credential slot is a logical NAME; this "
                    f"is {name_value(entry)}, and an assignment carries "
                    f"neither bearer bytes, a host path nor a provider "
                    f"reference")
        name = slot_name(entry)
        if name in taken:
            _refuse(f"credential slot {name_value(name)} is authorized twice; "
                    f"two authorizations of one slot is not two slots")
        taken.append(name)
    return tuple(taken)


def resolved_delivery(slots, *, profile):
    """Each authorized slot, through the TRUSTED profile, to a provider.

    TWO DIRECTIONS AND THEY ARE NOT THE SAME RULE.

      An authorized slot the profile does not map is REFUSED. The assignment
      asks for a credential this deployment does not grant, and materializing
      nothing for it would hand the worker a root missing an entry it was told
      to expect -- a failure it discovers by reading, at whatever moment.

      A profile entry for a slot the assignment did not authorize is IGNORED.
      A trusted profile is legitimately broader than one assignment; what the
      approved boundary says is that the CLOSED SLOT NAMES determine the root's
      entries, and that is a statement about what gets materialized rather than
      about what the profile may contain.
    """
    authorized = _authorized_slots(slots)
    if type(profile) is not dict:
        _refuse(f"a trusted runtime profile's credential mapping is one "
                f"document; this is {name_value(profile)}")
    resolution = []
    for name in authorized:
        if name not in profile:
            _refuse(f"the trusted runtime profile maps no provider for "
                    f"credential slot {name_value(name)}; an assignment may "
                    f"not name a slot this deployment does not grant",
                    category="policy", code="denied")
        mapped = boundaries.document(profile[name],
                                     "a credential slot's provider mapping",
                                     required=_MAPPING_MEMBERS)
        provider = boundaries.identity(mapped["provider"],
                                       "a credential provider identity")
        # OPAQUE, AND PROVED ONLY AS TEXT. This module never reads a meaning
        # out of a reference: the moment it did, the profile would be a second
        # place that decides what a credential is.
        reference = boundaries.text(mapped["reference"],
                                    "a credential provider reference")
        resolution.append({"slot": name, "provider": provider,
                           "reference": reference})
    return tuple(resolution)


def _proved_root(root, attempt):
    """The private root proved, BEFORE any child or bearer is read.

    W52800 review 2026-08-31T13:56:33Z [P0], and the reviewer is right that
    this is load-bearing rather than tidy. The approved argument has TWO
    halves: the slot is group-readable at `0640`, AND the root above it stays
    manager-owned at `0700` so host members of that group cannot traverse to
    the bearer. The first cut proved only the first half at recovery.

    WHY MATERIALIZATION IS NOT THE EVIDENCE. `adopt` exists precisely because
    this process did not create the state it is accepting -- that is the whole
    definition of a restart. "An earlier run set 0700" is a fact about a
    process that is gone; what governs the bytes now is what is on the disk
    now. A root widened to `0770` hands every host member of the configured
    group a traversal to a `0640` slot, and a root SUBSTITUTED means every
    child check below happens under a pathname whose custody nobody proved.

    `lstat` AND NOT `stat`, so a symbolic link standing where the root should
    be is refused as itself rather than resolved into whatever it points at.

    AND AN `lstat` THAT FAILS IS A REFUSAL, not an exception escaping a door
    that promises a typed answer: a root this manager cannot even interrogate
    is not one it may adopt a bearer out of.
    """
    try:
        found = os.lstat(root)
    except OSError as failure:
        _refuse(f"the volatile credential root for attempt "
                f"{name_value(attempt)} could not be interrogated "
                f"({type(failure).__name__}); a root this manager cannot ask "
                f"about is not one it adopts a bearer out of",
                category="refused", code="precondition")
    mode = found.st_mode & 0o7777
    if not stat.S_ISDIR(found.st_mode) or mode != VOLATILE_DIR \
            or found.st_uid != os.getuid():
        _refuse(f"the volatile credential root for attempt "
                f"{name_value(attempt)} is mode {oct(mode)} owned by "
                f"{found.st_uid}, and a live root is an ordinary directory at "
                f"{oct(VOLATILE_DIR)} owned by this manager. The slot's group "
                f"grant is only safe while the root above it admits nobody "
                f"else, so a widened or substituted root is refused before "
                f"any bearer is read",
                category="refused", code="precondition")


def _proved_slot(place, name, gid):
    """A live slot proved to be THIS deployment's, BEFORE it is read back.

    W52800. `adopt` proved the slot was a file and then read it; it proved
    neither who owns it nor who may read it. A recovered delivery is material
    this process did not write -- the whole reason recovery exists -- so a slot
    whose owner, group or mode is not the ruled one is not the slot this
    manager materialized, and reading a bearer back out of it would be
    registering a value somebody else's permissions govern.

    `lstat` AND NOT `stat`, because a symbolic link at this name resolving to a
    correct-looking file elsewhere is exactly the substitution this proves
    against.

    ASKED BEFORE THE READ, which is the ordering that matters: refusing after
    the bytes are in memory would be refusing a value already registered.
    """
    found = os.lstat(place)
    mode = found.st_mode & 0o7777
    if not stat.S_ISREG(found.st_mode) or mode != VOLATILE_FILE \
            or found.st_uid != os.getuid() or found.st_gid != gid:
        _refuse(f"the volatile credential for slot {name_value(name)} is not "
                f"the delivery this manager writes -- it is mode {oct(mode)} "
                f"owned by {found.st_uid}:{found.st_gid}, and a live slot is "
                f"a regular file at {oct(VOLATILE_FILE)} owned by this manager "
                f"in the configured workspace group. A bearer read out of "
                f"something else is a value another party's permissions "
                f"govern",
                category="refused", code="precondition")


def _reader_group(workspace_group):
    """WHO MAY READ A LIVE BEARER, as an explicit capability.

    W52800's ruling in one function. The slot's gid is a GRANT, so it arrives
    the way every other grant in this package does -- as the nominal
    capability this manager minted from its own configured record, never as a
    bare integer a caller composed and never as whatever group the parent
    directory happened to give the file.

    THE SAME HOLD `oci.run_vector` APPLIES TO THE SAME CAPABILITY, and
    deliberately so: that is the function that adds this group to the
    execution container with `--group-add`, and the two halves of one grant
    must be the same value proved the same way. An integer accepted here would
    be this module deciding who may read a bearer.
    """
    from . import workspaces

    if type(workspace_group) is not workspaces.WorkspaceGroup:
        _refuse(f"a credential delivery is given the deployment's configured "
                f"workspace group, read from this manager's own record; this "
                f"delivery names {name_value(workspace_group)}. The group is "
                f"who may READ the live bearer, so it is a capability rather "
                f"than a number",
                category="refused", code="precondition")
    return workspaces.check_workspace_group(workspace_group.gid)


class CredentialHome:
    """WHERE THIS MANAGER KEEPS CREDENTIAL MATERIAL, owned once.

    A CLASS RATHER THAN A `home` PARAMETER ON EIGHT FUNCTIONS, and the boundary
    inventory is what decided it: every public function taking the path made it
    a receiving entry, so one deployment fact became eight crossings with eight
    rules to keep true. It is the same shape `OciAdapter` uses for its resolved
    identity and its assignment roots -- assignment-scoped, fixed, and proved
    when the thing that holds it is built rather than at every call.

    The two places under it are SIBLINGS of the assignment's roots and
    deliberately not among them: `oci.ROOT_NAMES` is the contract for what a
    container may mount as its own material, and a credential is delivered at a
    fixed path of this contract's choosing instead.
    """

    __slots__ = ("place",)

    def __init__(self, place):
        home = boundaries.text(place, "a manager credential home")
        if not home.startswith("/"):
            _refuse(f"a manager credential home is an absolute path; this is "
                    f"{name_value(home)}", code="path")
        if ".." in home.split("/"):
            _refuse(f"a manager credential home traverses with `..`; a "
                    f"canonical path is what this manager writes under",
                    code="path")
        self.place = home

    def volatile_root(self, attempt_id):
        """Where one attempt's credential files live."""
        return os.path.join(
            self.place, "credentials",
            boundaries.identity(attempt_id, "a credential attempt id"))

    def state_path(self, attempt_id):
        """The durable lifecycle record for one attempt.

        OUTSIDE the volatile root, because teardown removes that root and the
        whole point of this record is that a restarted manager can still say
        what it is tearing down. It names the slot, the provider and the state
        -- never the bearer, and never a digest of one, which is a bearer
        somebody can confirm a guess against.
        """
        return os.path.join(
            self.place, "credential-state",
            boundaries.identity(attempt_id, "a credential attempt id")
            + ".json")

    def materialize(self, resolution, *, attempt_id, workspace_group,
                    credential_provider):
        """One private file per resolved slot, bearer registered FIRST.

        THE ORDER IS THE SECURITY PROPERTY, so it is written out rather
        than left to the reading:

          1. the provider answers, and its answer is owned like any
             injected value;
          2. the value is REGISTERED LIVE -- before any byte of it is
             anywhere this process did not put it, so every §13 walk from
             here on can see it;
          3. only then does it reach a 0640 file in the deployment's
             configured workspace group, under a 0700 manager-only root.

        Registering after the write would leave a window in which the bytes
        exist and the registry says there is nothing to find, which is the
        one shape a leak check cannot survive.

        AND A PRE-EXISTING ROOT REFUSES. A volatile root already on disk for
        this attempt is either a live delivery this call would trample or an
        orphan of a stopped process; neither is something to write into.
        `adopt` is the only way back to an existing root, and it proves
        identity before it does.
        """
        boundaries.capability(credential_provider, "a credential provider")
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        gid = _reader_group(workspace_group)
        # EVERY OPERAND PROVED BEFORE ANYTHING EXISTS ON DISK.
        #
        # The first version created the root and then read the resolution
        # inside the loop, so a resolution this module cannot read left a
        # directory behind -- and writing the witness for this rule is what
        # found it. A door that refuses AFTER making something is a door whose
        # refusal has a side effect.
        #
        # OWNED HERE AND NOT ONLY IN `resolved_delivery`, because this is a
        # public door: that function composes exactly this shape, and a caller
        # may hand one it composed itself. A resolution whose provider or
        # reference nothing proved is one this manager would call an injected
        # capability with.
        proved = []
        # THE SHAPE FIRST, THEN THE CALLER'S OWN SEQUENCE. Iterating the copy
        # `_list` returns would hide which operand these members came from:
        # the boundary inventory attributes a crossing by following the value,
        # and a member taken from a helper's return is a member it cannot
        # attribute to `resolution`. Nothing is lost -- `boundaries.document`
        # below takes the deep built-in copy that matters.
        _list(resolution, "a resolved credential delivery")
        for entry in resolution:
            one = boundaries.document(entry, "a resolved credential slot",
                                      required=("slot", "provider",
                                                "reference"))
            proved.append({
                "slot": slot_name(one["slot"]),
                "provider": boundaries.identity(
                    one["provider"], "a credential provider identity"),
                "reference": boundaries.text(
                    one["reference"], "a credential provider reference")})
        root = self.volatile_root(attempt)
        if os.path.exists(root):
            _refuse(f"a credential root already exists for attempt "
                    f"{name_value(attempt)}; an existing root is a live "
                    f"delivery or an orphan, and writing into either would "
                    f"replace bytes this manager cannot account for",
                    category="refused", code="precondition")
        slots = []
        bearers = {}
        os.makedirs(root, mode=VOLATILE_DIR, exist_ok=False)
        os.chmod(root, VOLATILE_DIR)
        try:
            for one in proved:
                name = one["slot"]
                answer = credential_provider(one["provider"], one["reference"])
                bearer = boundaries.injected(
                    answer, "a materialized credential")
                if len(bearer) > MAX_BEARER:
                    _refuse(f"the credential for slot {name_value(name)} is "
                            f"wider than {MAX_BEARER} characters; a value this"
                            f" manager cannot hold is not one it will "
                            f"write", code="limit")
                # LIVE BEFORE IT IS ANYWHERE ELSE.
                remember_secret(bearer)
                bearers[name] = bearer
                place = os.path.join(root, name)
                # THE CREATION ORDER IS THE SECURITY PROPERTY, and W52800's
                # ruling writes it out step by step because getting it in the
                # wrong order is how a bearer ends up briefly readable by
                # somebody it was never granted to.
                #
                #   1. exclusive-create the slot EMPTY, at a mode no broader
                #      than the ruled one. `O_EXCL` so nothing already at this
                #      name is written through, and the mode goes to `open`
                #      rather than being applied after.
                #   2. `fchown` the DESCRIPTOR to the configured gid. Only the
                #      group moves: `-1` leaves the owner, so lifecycle
                #      custody stays with this manager.
                #   3. `fchmod` the STILL-EMPTY descriptor to exactly the ruled
                #      mode. This is what makes the mode exact rather than
                #      whatever the umask left -- `os.open`'s mode is filtered
                #      by it, so a service umask of 077 would otherwise create
                #      an unreadable slot and nothing would say so.
                #   4. ONLY THEN the bearer bytes.
                #
                # Every step before the write is on an EMPTY inode, so a
                # failure at any of them unwinds a file that never held a
                # bearer. Doing the `fchown` afterwards would leave real bytes
                # sitting in whatever group the parent happened to give them.
                #
                # ALL THREE ON THE DESCRIPTOR rather than on the path, for the
                # reason this package applies everywhere: a name resolved a
                # second time is a name something else can have replaced.
                handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                                 VOLATILE_FILE)
                try:
                    os.fchown(handle, -1, gid)
                    os.fchmod(handle, VOLATILE_FILE)
                    _write_whole(handle, bearer.encode("utf-8"), name)
                finally:
                    os.close(handle)
                slots.append({"slot": name, "provider": one["provider"],
                              "target": f"{CREDENTIAL_ROOT}/{name}"})
        except BaseException as failure:
            # A FAILED MATERIALIZATION TEARS ITSELF DOWN. Half a delivery
            # is a root holding bearers nobody is going to remove, and the
            # ending that would have removed it never starts, because the
            # attempt never launched.
            #
            # AND THE REMOVAL'S OWN ANSWER DECIDES WHAT HAPPENS NEXT. Review
            # [P1]: this called `_discard`, IGNORED the boolean it exists to
            # return, and then forgot every bearer unconditionally. A
            # filesystem that refused the removal therefore left the bearer
            # bytes in the volatile root while the registry that guards every
            # later §13 scan was disarmed — a check that cannot fail, which is
            # worse than no check because it reads as evidence.
            #
            # `_discard` answers whether the root is GONE, which is the same
            # positive-absence rule `_gone` states for teardown: the removal's
            # own error is not the answer, the state afterwards is.
            if _discard(root):
                for value in bearers.values():
                    forget_secret(value)
                raise
            # UNRESOLVED, AND IT STAYS ARMED. Nothing is forgotten, because
            # forgetting is what would make the bytes still on disk invisible
            # to every scan that comes after. The ending is surfaced as what
            # it is rather than propagated as the caller's original failure,
            # which would say the provider broke and not that a bearer is
            # stranded.
            _refuse(f"a credential materialization for attempt "
                    f"{name_value(attempt)} failed and its volatile root "
                    f"{name_value(root)} could not be proved gone; the "
                    f"bearers it wrote stay REGISTERED rather than forgotten, "
                    f"because a registry disarmed over bytes still on disk is "
                    f"a §13 scan that cannot fail",
                    category="policy", code="credential-lifetime")
        return Delivery(attempt_id=attempt, root=root, slots=slots,
                        state="live", bearers=bearers)

    def adopt(self, record, *, attempt_id, runtime_id, workspace_group):
        """Recover one attempt after a manager restart, or FAIL CLOSED.

        The approved boundary admits recovery only on an EXACT agreement
        of the attempt, container, mount and root identities. Everything
        below is one of those four, and a disagreement is not a repair
        opportunity: it is an attempt this manager cannot say the shape of,
        so it refuses and leaves the caller to stop the worker and clean
        up.
        """
        taken = boundaries.document(record, "a credential lifecycle record",
                                    required=_STATE_MEMBERS)
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        runtime = boundaries.identity(runtime_id, "a credential runtime id")
        # THE SAME GRANT RECOVERY IS ABOUT, HELD THE SAME WAY. W52800: a
        # restart adopts a delivery it did not write, so "is this slot still
        # the thing this deployment ruled" is a question only recovery can
        # ask. Answering it needs the configured group, and the ordinary retry
        # builder already holds it.
        gid = _reader_group(workspace_group)
        root = self.volatile_root(attempt)
        for member, expected in (("attempt_id", attempt),
                                 ("runtime_id", runtime),
                                 ("credential_root", root),
                                 ("container_root", CREDENTIAL_ROOT)):
            if taken[member] != expected:
                _refuse(f"the recorded credential {member} is not the one this"
                        f" restart proved; recovery adopts an exactly agreeing"
                        f" attempt, container, mount and root, and refuses "
                        f"everything else",
                        category="refused", code="precondition")
        if taken["lifecycle_state"] not in ("live", "adopted"):
            _refuse(f"the recorded credential lifecycle is "
                    f"{name_value(taken['lifecycle_state'])}; only a live "
                    f"delivery is adoptable",
                    category="refused", code="precondition")
        # PROVE THE WHOLE DELIVERY, THEN REGISTER IT.
        #
        # Fourth review [P1]: validation, reading and registration happened in
        # one loop, so a later slot that was missing or malformed left the
        # earlier bearers LIVE with no `Delivery` returned to own them. The
        # registry is reference-counted and every entry is forgotten by the act
        # that acquired it -- and the act that acquired these had raised, so
        # nothing would ever release them. A registry holding a value no object
        # owns is a value that stays live for the process, which turns every
        # later §13 walk into a check against a bearer nobody is delivering.
        #
        # So this pass touches nothing global. Registration is one act at the
        # end, and it unwinds itself if it cannot finish.
        # THE RECORD'S OWN SHAPE FIRST, WITH NOTHING TOUCHED. Every slot the
        # caller named is proved as a DOCUMENT before this function asks the
        # filesystem anything -- the same rule `materialize` states in its own
        # words, "every operand proved before anything exists on disk". A door
        # that reads a disk to refuse a malformed operand is a door whose
        # refusal depends on state the operand has nothing to do with.
        recorded = []
        for entry in taken["slots"]:
            one = boundaries.document(entry, "a recorded credential slot",
                                      required=_SLOT_MEMBERS)
            name = slot_name(one["slot"])
            boundaries.identity(one["provider"],
                                "a credential provider identity")
            if one["target"] != f"{CREDENTIAL_ROOT}/{name}":
                _refuse(f"the recorded mount for slot {name_value(name)} is "
                        f"not an entry of {CREDENTIAL_ROOT}; a mount this "
                        f"manager cannot place is not one it will adopt",
                        category="refused", code="precondition")
            recorded.append((name, one))
        # THEN THE ROOT, BEFORE ANY CHILD OR BEARER IS READ. Review [P0]: this
        # proved each slot and never the directory holding them, so the second
        # half of the ruling -- a manager-owned 0700 root that nobody else may
        # traverse -- was unchecked at exactly the boundary that inherits
        # somebody else's filesystem state.
        #
        # AFTER THE SHAPE AND BEFORE THE DISK is the whole of the ordering:
        # nothing below this line has looked at a file yet, so "before any
        # child or bearer read" still holds exactly, and a caller handing a
        # malformed record still learns that rather than learning about a root.
        _proved_root(root, attempt)
        prepared = []
        for name, one in recorded:
            place = os.path.join(root, name)
            if not os.path.isfile(place):
                _refuse(f"the volatile credential for slot {name_value(name)} "
                        f"is not where the record says it is; a delivery "
                        f"missing a slot is not the delivery that was "
                        f"recorded",
                        category="refused", code="precondition")
            _proved_slot(place, name, gid)
            # READ BACK, and the module docstring argues why re-registration
            # is right. Reading the slot this manager wrote and `_proved_slot`
            # has just proved -- manager-owned, 0640, in the configured group --
            # is not publishing it; sealing an adopted attempt with an EMPTY
            # registry would be.
            try:
                with open(place, "rb") as reading:
                    # ONE MORE THAN THE BOUND, so a file that is too wide is
                    # DETECTED rather than silently truncated into a different
                    # value -- registering a prefix of a bearer would arm every
                    # later leak check against a string that is not the secret.
                    raw = reading.read(MAX_BEARER + 1)
                if len(raw) > MAX_BEARER:
                    raise ValueError("wider than this manager holds")
                bearer = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError, ValueError):
                _refuse(f"the volatile credential for slot {name_value(name)} "
                        f"cannot be read back; a delivery this manager cannot "
                        f"re-register is one whose leak checks would pass "
                        f"because there is nothing to find",
                        category="refused", code="precondition")
            # A TUPLE RATHER THAN A DOCUMENT, and the boundary inventory is
            # why. A dict literal keyed `bearer` beside members read from the
            # record made the derivation attribute a `record.slots.bearer`
            # crossing that does not exist: the bearer comes from this
            # manager's own file, never from the record. A shape that invents
            # an entry is a shape that would need a probe for a boundary
            # nothing crosses.
            prepared.append((name, one["provider"], one["target"], bearer))
        # THE ONE REGISTERING ACT, and it owns its own unwind.
        registered = []
        try:
            bearers = {}
            for name, _provider, _target, bearer in prepared:
                remember_secret(bearer)
                registered.append(bearer)
                bearers[name] = bearer
            return Delivery(
                attempt_id=attempt, root=root, state="adopted",
                bearers=bearers,
                slots=[{"slot": name, "provider": provider, "target": target}
                       for name, provider, target, _bearer in prepared])
        except BaseException:
            for value in registered:
                forget_secret(value)
            raise

    def tear_down(self, delivery):
        """The one ordered ending, whatever the attempt's outcome was.

        Files, then the root, then the durable record -- each PROVED gone
        before the next -- and only after all of it is the bearer forgotten.
        A registry released while a file still holds the value is a registry
        that says a credential is dead while it is readable on disk.

        UNCERTAINTY REFUSES. The approved boundary is explicit that cleanup
        uncertainty may not be reported as successful settlement or a free
        worker slot, so this raises rather than answering a state, and the
        bearers stay live so anything sealed afterwards is still checked
        against them.
        """
        if type(delivery) is not Delivery:
            _refuse(f"a credential teardown acts on a materialized delivery; "
                    f"this is {name_value(delivery)}")
        for source, _target in delivery.mounts():
            _gone(source, "a volatile credential", os.remove)
        _gone(delivery.root, "a credential root", os.rmdir)
        _gone(self.state_path(delivery.attempt_id),
              "a credential lifecycle record", os.remove)
        # PROVED, THEN RELEASED.
        for value in delivery.bearers().values():
            forget_secret(value)
        delivery.state = "torn-down"
        return {"attempt_id": delivery.attempt_id,
                "lifecycle_state": "torn-down",
                "slots": [one["slot"] for one in delivery.slots]}

    def discard_orphan(self, attempt_id):
        """Remove ONE attempt's volatile root, proved stale by its caller.

        Fifth review [P1]: a per-attempt recovery called `discard_orphans` with
        an empty live set, and a `CredentialHome` is ASSIGNMENT-scoped -- it can
        hold sibling attempts' roots. So recovering attempt-1 deleted
        attempt-2's materialized root while attempt-2's lifecycle record and
        live bearer were both still there.

        "No record for THIS attempt" is not evidence about any other. A pass
        that removes what it has not proved stale is not cleanup; it is a
        second failure caused by the first.

        This removes exactly what its caller proved, and `discard_orphans`
        stays for the broad pass -- which needs the COMPLETE live set and says
        so in its own signature.
        """
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        root = self.volatile_root(attempt)
        gone = _discard(root) if os.path.exists(root) else True
        if gone:
            # THE RECORD GOES WITH THE ROOT, and leaving it was a defect that
            # could not converge. Sixth review [P1]: a proved cleanup removed
            # the volatile root and left the lifecycle record saying `live`,
            # still naming a root and a container that no longer exist. The
            # next recovery then reads that record, finds no runtime, can
            # neither adopt nor reach ordinary absence -- and with an empty
            # candidate list the failure path proves nothing gone, so the
            # state stays unresolved for ever.
            #
            # An ending that cannot be reached twice is not an ending. The
            # record is removed in the SAME ordered act that removed what it
            # describes, and its absence is proved like everything else here.
            _gone(self.state_path(attempt), "a credential lifecycle record",
                  os.remove)
        return {"discarded": [attempt] if gone else [],
                "remaining": 0 if gone else 1, "bounded": False}

    def orphan_evidence(self, attempt_id):
        """What this home DURABLY holds for one attempt, without a read.

        W55758. Presence of the bounded root and of the lifecycle record, and
        nothing else: no slot is opened, no record is parsed, and no path
        inside either is followed. A recovery process needs to know whether a
        credential was ever delivered here, and that question is answered by
        this manager's own two locations rather than by a `credential_root`
        member the record carries -- a raw path out of a document is not
        authority for touching a filesystem.
        """
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        root = self.volatile_root(attempt)
        return {"home": self.place,
                "volatile_root": os.path.lexists(root),
                "lifecycle_record": os.path.isfile(self.state_path(attempt))}

    def tear_down_orphan(self, attempt_id):
        """The ending for a delivery THIS PROCESS did not materialize.

        W55758. `tear_down` acts on a `Delivery`, which is the object the
        materializing process held; a recovery is exactly the shape in which
        that object died with its process. Reading the slots back merely to
        rebuild one whose only next act is deletion would open a bearer for no
        reason at all, so this unlinks and PROVES, and no byte enters this
        process.

        THE SAME TWO LOCATIONS AS `discard_orphan`, and the same order --
        the root before the record, each proved gone before the next -- so a
        restart never finds a record still saying `live` beside a root that is
        already gone. What is different is the ANSWER: this one speaks the
        lifecycle vocabulary the runtime ending reports, because it IS that
        ending for an attempt whose delivery object is gone.

        AND IT IS EXACTLY ONE ATTEMPT'S. A `CredentialHome` is
        assignment-scoped and can hold sibling attempts' roots; "this attempt
        is over" is not evidence about any other one.
        """
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        root = self.volatile_root(attempt)
        found = self.orphan_evidence(attempt)
        _discard(root)
        _gone(root, "a credential root", os.rmdir)
        _gone(self.state_path(attempt), "a credential lifecycle record",
              os.remove)
        return {"home": self.place, "attempt_id": attempt,
                "held_root": found["volatile_root"],
                "held_record": found["lifecycle_record"]}

    def discard_orphans(self, *, live):
        """Bounded cleanup of volatile roots no live attempt owns.

        A restart that cannot adopt an attempt still has to leave the host
        clean, and this is that act -- unlink only, never a read, so a root
        belonging to an attempt this process knows nothing about is removed
        without its bytes ever entering this process.

        BOUNDED, and the bound is REPORTED. A pass that stopped at its
        limit and answered like one that finished would be cleanup
        uncertainty reported as success, which the ruling names outright.
        """
        if type(live) not in (list, tuple, set, frozenset):
            _refuse(f"the live attempts are a collection of ids; this is "
                    f"{name_value(live)}")
        holding = os.path.join(self.place, "credentials")
        keep = {boundaries.identity(one, "a live attempt id") for one in live}
        if not os.path.isdir(holding):
            return {"discarded": [], "remaining": 0, "bounded": False}
        stale = [name for name in sorted(os.listdir(holding))
                 if name not in keep]
        discarded = []
        for name in stale[:MAX_ORPHANS]:
            if _discard(os.path.join(holding, name)):
                discarded.append(name)
        remaining = len(stale) - len(discarded)
        return {"discarded": discarded, "remaining": remaining,
                "bounded": len(stale) > MAX_ORPHANS}

    def written_state(self, attempt_id, body):
        """Publish the lifecycle record, atomically and walked.

        The same publish discipline `sealing._commit` was corrected into:
        a private name, forced, then renamed -- because a restart reading a
        half-written lifecycle record would fail to adopt an attempt whose
        worker is running.
        """
        # OWNED, THEN WALKED, THEN WRITTEN. The shape first, because a
        # document missing `slots` is a record `adopt` would refuse forever
        # after this call had already reported success.
        # THE ATTEMPT IS OWNED AT THIS DOOR, not only inside `state_path`.
        # The inventory attributes an entry to the site the boundary call is
        # written at, and a public operation whose operand is proved somewhere
        # further in is one whose crossing nothing names.
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        taken = boundaries.document(body, "a credential lifecycle record",
                                    required=_STATE_MEMBERS)
        check_no_durable_secret(taken, what="a credential lifecycle record")
        place = self.state_path(attempt)
        os.makedirs(os.path.dirname(place), mode=VOLATILE_DIR, exist_ok=True)
        staged = place + ".committing"
        with open(staged, "wb") as writing:
            writing.write(json.dumps(taken, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8"))
            writing.flush()
            os.fsync(writing.fileno())
        os.replace(staged, place)
        return taken

    def read_state(self, attempt_id):
        attempt = boundaries.identity(attempt_id, "a credential attempt id")
        place = self.state_path(attempt)
        if not os.path.isfile(place):
            return None
        with open(place, "rb") as reading:
            raw = reading.read()
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            _refuse(f"the credential lifecycle record for attempt "
                    f"{name_value(attempt)} is not a readable document; a "
                    f"record this manager cannot read is not one it will adopt"
                    f" an attempt on", category="refused", code="precondition")

class Delivery:
    """One attempt's materialized credentials, with the bearers held PRIVATELY.

    A CLASS RATHER THAN A DOCUMENT, and that is the §13 decision rather than a
    style preference. Everything else this manager passes around is plain JSON
    data that gets walked, journaled, digested and returned; a bearer inside
    one of those is a bearer that reaches a durable surface the first time
    somebody serializes the thing it rides in. The bearers here are in
    `__slots__` on an object nothing serializes, and the only document this
    class produces is `record`, which is composed member by member and walked
    before it is returned.
    """

    __slots__ = ("attempt_id", "root", "slots", "state", "_bearers")

    def __init__(self, *, attempt_id, root, slots, state, bearers):
        # A CONSTRUCTOR IS A PUBLIC DOOR whatever calls it today. Everything
        # here is composed by `materialize` or `adopt` from values they already
        # proved -- and an object that teardown, mounting and the durable
        # record all read is one whose members should be true of it whoever
        # built it.
        self.attempt_id = boundaries.identity(attempt_id,
                                              "a credential attempt id")
        self.root = boundaries.text(root, "a credential root")
        _list(slots, "a delivery's credential slots")
        self.slots = tuple(
            boundaries.document(one, "a delivered credential slot",
                                required=_SLOT_MEMBERS)
            for one in slots)
        if state not in LIFECYCLE_STATES:
            _refuse(f"a credential delivery is one of "
                    f"{', '.join(LIFECYCLE_STATES)}; this is "
                    f"{name_value(state)}")
        self.state = state
        if type(bearers) is not dict:
            _refuse(f"a delivery's bearers are one document keyed by slot; "
                    f"this is {name_value(bearers)}")
        # THE VALUES ARE NOT NAMED. Every other rule in this package puts the
        # value it rejected into its refusal, and here that would be the one
        # thing §13 exists to keep off a durable surface -- so the KEY is
        # proved and the bearer is only counted.
        self._bearers = {slot_name(key): value
                         for key, value in bearers.items()}

    def mounts(self):
        """The (source, target) pairs this delivery is exposed through.

        ONE MOUNT PER SLOT, whose SOURCE IS THE FILE rather than its directory.
        The approved boundary fixes the container-side ROOT and says the closed
        slot names determine its entries; mounting each file names exactly
        those entries, so anything that ever lands in the manager's volatile
        directory beside them is unreachable regardless. Mounting the directory
        would satisfy the same sentence and make that guarantee depend on the
        directory only ever holding what this module put there.
        """
        return tuple((os.path.join(self.root, one["slot"]), one["target"])
                     for one in self.slots)

    def record(self, *, runtime_id):
        """The durable lifecycle record, walked before it is returned."""
        body = {
            "attempt_id": self.attempt_id,
            "runtime_id": boundaries.identity(runtime_id,
                                              "a credential runtime id"),
            "credential_root": self.root,
            "container_root": CREDENTIAL_ROOT,
            "slots": [{"slot": one["slot"], "provider": one["provider"],
                       "target": one["target"]} for one in self.slots],
            "lifecycle_state": self.state,
        }
        # §13 IS NOT REPEATED HERE, and measurement is why. `written_state` is
        # the act that makes this record durable and it walks what it writes;
        # a second walk at this composition point was code no case could drive
        # -- every path to durability already went through the other one. Two
        # copies of one rule is one rule holding in one of the two places.
        return body

    def bearers(self):
        """The live values, for the ONE caller that releases them.

        Named rather than reached into, so the inventory and a reader can both
        see that exactly one act consumes this.
        """
        return dict(self._bearers)


class OrphanTeardown:
    """W55758: a previously delivered credential whose OWNER PROCESS is gone.

    THE DEFECT THIS EXISTS FOR, measured rather than supposed. An interrupted
    supervised attempt leaves its runtime, its bounded credential root and its
    lifecycle record on the host, and the in-memory `Delivery` dies with the
    process. A recovery reconstructs the adapter with `credential_delivery
    is None` -- and the ending then answered `not-delivered`, which is a
    POSITIVE CLAIM THAT NO CREDENTIAL WAS EVER DELIVERED about an attempt that
    demonstrably had one and left a bearer on disk for hours. `oci.py` chooses
    that word so a reader cannot conclude a credential was torn down because a
    container was; here it made the opposite mistake, and nothing told that
    record apart from a genuine no-credential attempt.

    SO THIS IS A CAPABILITY AND NOT A PATH. A recovery constructs it from what
    the deployment durably knows -- the operator's granted home, the
    assignment-derived home, and the attempt's own granted slots -- and hands
    it to the adapter exactly as the ordinary arc hands over a `Delivery`. A
    caller-selected path is the one thing the fixed locations exist to remove,
    and the `credential_root` member of a record is precisely such a path.

    TWO HOMES, BECAUSE ONE LEGACY ATTEMPT REALLY HAS TWO. The deployment
    materialized under the operator-granted home while the adapter published,
    recovered and removed under its assignment-derived one, so run7's root and
    its record are under different homes. Both are proved `CredentialHome`
    capabilities and each is asked only about its own two locations; the split
    is handled by HOLDING both, never by deriving a third place or by
    following a path a document supplied.

    IT READS NOTHING. Presence, unlink, proof. A bearer is never opened, never
    registered, never hashed and never reported.
    """

    __slots__ = ("attempt_id", "homes", "ending")

    def __init__(self, attempt_id, *, homes):
        self.attempt_id = boundaries.identity(attempt_id,
                                              "a credential attempt id")
        held = _list(homes, "the credential homes a recovery holds")
        if not held:
            _refuse("an orphan credential teardown acts through at least one "
                    "credential home; a teardown with nowhere to act is not "
                    "an ending")
        for one in held:
            if type(one) is not CredentialHome:
                _refuse(f"an orphan credential teardown acts through this "
                        f"manager's own credential home; this is "
                        f"{name_value(one)}")
        # DEDUPLICATED BY PLACE, because the ordinary case is one home named
        # twice -- the granted one and the assignment-derived one agree for
        # every attempt this deployment starts from now on -- and tearing the
        # same two locations down twice would report a second ending for one.
        seen = {}
        for one in held:
            seen.setdefault(one.place, one)
        self.homes = tuple(seen.values())
        # WHAT THIS CAPABILITY DID, kept so the deployment can record it
        # without reading the adapter's internals or repeating the act.
        self.ending = None

    def evidence(self):
        """What each home holds right now. A read of PRESENCE, never bytes."""
        return [home.orphan_evidence(self.attempt_id) for home in self.homes]

    def tear_down(self):
        """Every held home's two locations, proved gone, as one ending.

        `torn-down` MEANS PROVED ABSENT, which is the same thing it means for
        `CredentialHome.tear_down`: the ending is a fact about the host, not a
        claim about which act removed the file. So an attempt whose material a
        separate emergency `discard_orphan` already removed still ends
        `torn-down` here -- what would be false is calling it `not-delivered`.
        """
        homes = [home.tear_down_orphan(self.attempt_id) for home in self.homes]
        # THE ANSWER IS THE PROVIDER-ENDING CONTRACT'S, and the per-home
        # detail is kept beside it rather than inside it.
        #
        # Found by the composition case: `intake._provider_ending` refuses an
        # unrecognised member outright -- "ignoring one silently assumes the
        # members we do recognise still mean what they did" -- so a richer
        # ending returned into `destroy_abandoned` refused the WHOLE
        # abandonment. What the crossing reads is `lifecycle_state` plus the
        # named optional members; what an operator's recovery record wants is
        # which homes were ended, and those are two different documents.
        self.ending = {"attempt_id": self.attempt_id,
                       "lifecycle_state": "torn-down",
                       "homes": homes}
        return {"attempt_id": self.attempt_id,
                "lifecycle_state": "torn-down"}


def _write_whole(handle, payload, slot):
    """Every byte, or a refusal. `os.write` is allowed to write fewer.

    Fourth review [P1]: the writer called `os.write` once and ignored its
    answer, so a short write delivered a TRUNCATED credential -- a file whose
    contents are a prefix of the bearer this manager registered. Nothing
    downstream could notice: the registry holds the whole value, the leak
    checks look for the whole value, and the worker reads a prefix that simply
    does not authenticate.

    A short write is ORDINARY rather than exotic. A pipe, a signal-interrupted
    call and a filesystem near its limit all produce one, and none of them is
    an error the call reports.

    NO PROGRESS IS A REFUSAL rather than a spin. A writer that accepts zero
    bytes twice is not going to accept them on the third attempt, and looping
    on it would hang inside a delivery instead of failing it.
    """
    written = 0
    while written < len(payload):
        step = os.write(handle, payload[written:])
        if type(step) is not int or step <= 0:
            _refuse(f"writing the credential for slot {name_value(slot)} "
                    f"made no progress after {written} of {len(payload)} "
                    f"bytes; a partly written credential is a value nobody "
                    f"can use and everybody would believe")
        written += step
    return written


def _gone(place, what, remove):
    """Remove one thing and PROVE it is not there.

    ONE PROOF, not one per kind of thing. My first version had a near-copy for
    files and another for the root, and measurement said the file half was
    unreachable: no real filesystem removes a directory while a file is still
    inside it, so the directory's proof answered for both and the file's rule
    was code no case could drive. A rule that exists twice holds in one of the
    two places -- `errors.py` says exactly that about `name_of` -- and here the
    second copy was the one that never ran.

    THE REMOVAL'S OWN ERROR IS NOT THE ANSWER. What matters is the state
    afterwards: an engine or a filesystem that reports success while the thing
    is still there is precisely the case this is here for, and one that reports
    failure after removing it is not a failed ending.
    """
    try:
        remove(place)
    except OSError:
        pass
    if os.path.lexists(place):
        _refuse(f"{what} is still present after teardown removed it; an "
                f"ending this manager cannot prove is not an ending it will "
                f"report", category="policy", code="credential-lifetime")


def _discard(root):
    """Remove a volatile root WITHOUT reading anything in it."""
    if not os.path.isdir(root):
        return not os.path.lexists(root)
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
