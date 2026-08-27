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
mode 0600 under a 0700 assignment-private root, and in the in-memory live-secret
registry. That is the entire list. §13 bars the value from argv, environment,
image layers, labels, logs, durable state, protocol Events and output metadata,
and every function below that produces a durable document walks it before it
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

from ..contracts import (ContractRefusal, check_no_durable_secret,
                         forget_secret, remember_secret)
from ..contracts.errors import name_value
from . import boundaries

__all__ = ["CREDENTIAL_ROOT", "LIFECYCLE_STATES", "MAX_BEARER", "MAX_ORPHANS",
           "MAX_SLOTS", "VOLATILE_DIR", "VOLATILE_FILE", "CredentialHome",
           "Delivery", "resolved_delivery", "slot_name"]

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
VOLATILE_FILE = 0o600

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

    def materialize(self, resolution, *, attempt_id,
                    credential_provider):
        """One private file per resolved slot, bearer registered FIRST.

        THE ORDER IS THE SECURITY PROPERTY, so it is written out rather
        than left to the reading:

          1. the provider answers, and its answer is owned like any
             injected value;
          2. the value is REGISTERED LIVE -- before any byte of it is
             anywhere this process did not put it, so every §13 walk from
             here on can see it;
          3. only then does it reach a 0600 file under a 0700 private root.

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
                # EXCLUSIVE CREATION AT 0600. `O_EXCL` so nothing that already
                # exists under this name is written through, and the mode
                # is given to `open` rather than applied after, so the
                # bytes are never readable at a wider mode even briefly.
                handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                                 VOLATILE_FILE)
                try:
                    _write_whole(handle, bearer.encode("utf-8"), name)
                finally:
                    os.close(handle)
                slots.append({"slot": name, "provider": one["provider"],
                              "target": f"{CREDENTIAL_ROOT}/{name}"})
        except BaseException:
            # A FAILED MATERIALIZATION TEARS ITSELF DOWN. Half a delivery
            # is a root holding bearers nobody is going to remove, and the
            # ending that would have removed it never starts, because the
            # attempt never launched.
            _discard(root)
            for value in bearers.values():
                forget_secret(value)
            raise
        return Delivery(attempt_id=attempt, root=root, slots=slots,
                        state="live", bearers=bearers)

    def adopt(self, record, *, attempt_id, runtime_id):
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
        prepared = []
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
            place = os.path.join(root, name)
            if not os.path.isfile(place):
                _refuse(f"the volatile credential for slot {name_value(name)} "
                        f"is not where the record says it is; a delivery "
                        f"missing a slot is not the delivery that was "
                        f"recorded",
                        category="refused", code="precondition")
            # READ BACK, and the module docstring argues why re-registration
            # is right. Reading this manager's own 0600 file is not publishing
            # it; sealing an adopted attempt with an EMPTY registry would be.
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
