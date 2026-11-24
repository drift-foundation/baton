"""THE TWO OWNER PORTS A PUBLICATION RECOVERY ADDS, composed over one
instance's own installation.

W385695 internal checkpoint 1, under DESIGN REC-9. A retained-recovery
admission already composes four owners -- the host's record of each prior
attempt, the Authority's answer about the Work, the deployment configuration's
binding and the instance guard -- and `tools.fresh_attempt_ports` is where
this deployment's adapters over them live. This slice needs two more, and they
are here rather than there because they are THIS capability's, not because two
files are tidier than one:

    HostOutput          the ORIGINAL output the failed attempt left on this
                        host: proved, measured and read through the workspace
                        owner, under a completed preparation and settled
                        writers. REC-9's trust root, and the only door to it.
    SourceCorrespondence the Git-aware consumer that says whether the measured
                        bundle really holds that candidate on that base and
                        whether its content is that path set.

NEITHER PORT DECIDES ANYTHING. Whether a measurement is big enough, whether a
producer's exit status may be reused, whether an owner may approve and whether
an admission may compose are `job_manager.publication_recovery`'s, enforced
inside the operation. An adapter that decided one of them would be the
script-side precheck REC-7 forbids, wearing the product's name.

AND NEITHER INTERPRETS THE OTHER'S DOMAIN. The workspace owner measures bytes
and knows nothing about commits; the Git-aware consumer resolves revisions and
is handed a path it was told to read rather than one it went looking for.
REC-9 states that boundary for the manager -- "the generic manager does not
interpret Git or scan the nominated source checkout" -- and the way to keep it
is for the thing that does interpret Git to be a separate owner with its own
confinement.
"""
import os
import shutil
import tempfile

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts.errors import name_value
from baton_v12.integration import git_profile
from baton_v12.worker_manager import retained_output_of

from tools.fresh_attempt_ports import _required

__all__ = ["HostOutput", "PriorAssignment", "SourceCorrespondence",
           "BUNDLE_ENTRY", "COMMAND_SECONDS", "bare_repository_vector",
           "publication_owners", "runner_for"]

# HOW LONG ONE CORRESPONDENCE COMMAND MAY RUN. This port's own bound rather
# than the recovery profile's: the profile's 900 s is the REVIEWER's per
# command ceiling, and borrowing it here would state a reviewer's policy over
# a read-only object-store command an owner is waiting on.
COMMAND_SECONDS = 300

# WHERE THE CANDIDATE'S OBJECTS LIVE INSIDE A RETAINED PROPOSAL, by the name
# the producing adapter writes them under. A CONSTANT OF THE PRODUCER'S
# CONTRACT rather than an operand: a path a caller could vary is a path this
# port could be pointed at wrongly, which is exactly what "never trust an
# arbitrary path" means one layer down from the trust root.
BUNDLE_ENTRY = "objects.bundle"


class HostOutput:
    """The original output of one attempt, through the owner that holds it.

    THE STORE MUST BE THIS INSTANCE'S, and it is proved at birth rather than
    at the first read -- `HostExclusion`'s rule and review R11/R14's reason: a
    port that could be constructed over another deployment's store and only
    refuse later is one a caller can hold while believing it is bound.

    THE READ IS `workspaces.retained_output_of` AND NOTHING ELSE. This class
    composes no path, opens no file and measures no tree; it hands the owner
    an attempt identity and the names of the measured entries whose bytes the
    qualification needs, and the owner proves the storage, the completed
    preparation, the settled writers, the object identity and the measurement
    before one byte is read. That is the whole point: a port that walked to
    `<storage>/<attempt>/workspace` itself would be this file choosing a trust
    root, and REC-9's rule is that the attempt's owner chooses it.
    """

    def __init__(self, control, identity):
        self._control = control
        self._identity = _required(identity, "a host output port")
        self._expected = self._identity["control_store"]
        here = getattr(control, "database", None)
        if os.path.realpath(str(here or "")) != self._expected:
            raise ContractRefusal(
                "refused", "precondition",
                f"this host's control store is {here!r} and instance "
                f"{self._identity['root']!r} owns {self._expected!r}; the "
                f"original output of a failed execution read through another "
                f"deployment's store is another deployment's output")

    def instance(self):
        return self._identity

    def output_of(self, attempt_id, *, read=(), output=None):
        """The proved, measured original, with the named entries' bytes.

        ONE COHERENT BOUNDARY, `HostExclusion.evidence_of`'s rule: the
        snapshot makes every answer describe ONE state of the control store,
        so a torn read cannot produce a preparation record and a measurement
        that never coexisted. The filesystem measurement itself happens
        outside any transaction, which is the contract's own requirement.
        """
        with self._control.snapshot() as control:
            # `output` IS THE DECLARED OUTPUT'S OWN PATH, from the selected
            # declaration and never from an operator: the owner then proves
            # and measures that one directory of the attempt's writable root
            # -- or of its development line -- rather than the root itself.
            return retained_output_of(
                control, attempt_id, names=tuple(read), output=output,
                what=f"the original output of attempt "
                     f"{name_value(attempt_id)}")


class PriorAssignment:
    """THE SUPPORTED ENDING OF THE ASSIGNMENT A RECOVERY'S WORK ALREADY HOLDS.

    W385695 checkpoint 2, and this is the "minimal public seam" the contract
    names. A publication recovery REUSES the original open Work, and a fresh
    assignment on a reused Work requires the previous one to be ended through
    "the Authority's existing exact-expect transition" -- `Session.end`, whose
    release dispositions are `release` and `recovered`. There is no other
    route: a host-only stopped-settlement receipt does not release an
    Authority claim, and this deployment holds no raw SQL path to the
    Authority's tables.

    THE SESSION IS THE HOLDER'S OWN AND IS NOT MINTED HERE. `Authority.end`
    compares-and-swaps the exact assignment, and a session refuses to act on
    one naming somebody else -- so the only session that can end the producer's
    claim is the producer participant's, which the deployment already mints for
    that worker. This adapter therefore takes a SESSION FACTORY keyed by
    participant and asks it for the holder of the assignment it was told to
    end. It cannot impersonate: it can only ask for the session of the
    participant the Authority itself reports as the live handler, and if the
    deployment does not hold one, the admission is refused with the exact held
    assignment rather than worked around.

    IT DECIDES NOTHING. Whether the live assignment is the failed execution's,
    whether the host proved cessation and whether the ending may happen at all
    are `job_manager.publication_recovery`'s, enforced inside the operation.
    This adapter reads one projection and performs one transition.
    """

    def __init__(self, authority, identity, *, sessions=None):
        self._authority = authority
        self._identity = _required(identity, "a prior-assignment port")
        # Only an already-held participant session may end its assignment.
        self._sessions = sessions

    def instance(self):
        return self._identity

    def assignment_of(self, work_id):
        """The Work's LIVE assignment, or `None`. A read."""
        return self._authority.assignment_of(work_id)

    def end(self, expect, *, operation_id, disposition="recovered",
            reason=None):
        """End exactly this assignment, through its own holder's session.

        THE OPERATION IDENTITY IS THE MANAGER'S and is passed through
        unchanged: the Authority replays its own transition under it, so a
        lost reply reaching this adapter twice ends one assignment once.
        """
        participant = expect["participant"]
        if self._sessions is None:
            raise ContractRefusal(
                "refused", "capability",
                f"no held session is available for {name_value(participant)}; "
                "the current assignment must be ended by its existing holder")
        session = self._sessions(participant)
        who = getattr(session, "participant", None)
        if who != participant:
            raise ContractRefusal(
                "refused", "capability",
                f"this deployment answered a session for "
                f"{name_value(who)} and the assignment to end is "
                f"{name_value(participant)}'s; an assignment is ended by its "
                f"own holder and this adapter does not impersonate one")
        return session.end({"expect": expect, "operation_id": operation_id,
                            "disposition": disposition, "reason": reason})


def bare_repository_vector(place):
    """One private, empty object store for a correspondence read.

    COMPOSED HERE AND NOT IN `git_profile`, and the boundary is the reason.
    That module owns the Git MECHANICS an integration result is made with --
    importing, verifying, listing, merging, retaining -- and every one of its
    vectors operates on a repository somebody else provisioned. Where the
    scratch for a read lives is a DEPLOYMENT fact, so the act that creates one
    belongs with the deployment's adapter rather than in the shared profile.

    `--bare` and nothing else: no worktree, no index, no checkout and no
    configuration inherited from a human, so the objects a bundle carries can
    be resolved without anything being written anywhere a checkout could be.
    """
    if type(place) is not str or not place or not os.path.isabs(place):
        raise ContractRefusal(
            "integrity", "path",
            "a private correspondence repository is an absolute path")
    return ["git", "init", "--bare", "--quiet", place]


def runner_for(engine=None):
    """The command runner `GitIntegrationProfile` answers through.

    THE ENGINE IS AN OPERAND, which is `status --observe`'s rule and
    `recovery_decision.owners`': which boundary a command's children run at is
    a DEPLOYMENT fact. The default is the ordinary host subprocess, bounded
    and non-interactive, with no inherited standard input.
    """
    if engine is not None:
        return engine

    def run(argv, input=None):
        import subprocess

        held = subprocess.run(list(argv), capture_output=True, text=True,
                              input=input if input is not None else "",
                              timeout=COMMAND_SECONDS)
        return {"returncode": held.returncode, "stdout": held.stdout,
                "stderr": held.stderr}

    return run


class SourceCorrespondence:
    """THE GIT-AWARE CONSUMER, in its own confinement, answering ONE question.

    "Does the candidate this retained output declares really exist, on the
    base it declares, carrying the path set it declares?" -- and the answer is
    composed out of `git_profile`'s own vectors rather than out of commands
    this file writes, so what runs is the product's Git mechanics and what is
    faked in a focused case is the ENGINE those vectors are handed to.

    THE ORDER IS THE PROOF:

      a private BARE repository is created under this port's own scratch root,
        so nothing is read into, or written beside, any repository that
        matters;
      the CANDIDATE is fetched FROM THE MEASURED BUNDLE, by the path the
        trust-root owner measured -- not from a remote and not from a path a
        caller named;
      the BASE is fetched from that same bundle when the original has no line
        record (the first cut's rule, unchanged); and, by owner selection
        M385913, FROM THE LINE'S OWN DURABLY RECORDED SOURCE REPOSITORY when
        the host owner answered one. A real producer's bundle is a thin
        `base..HEAD` transport and does not carry its base, so bundle-only
        could correspond no real output. The source is used only after its
        recorded `device:inode` is proved again HERE, the base is asked for
        by its exact full object name, that name must be the base the line
        was declared on, and there is no fallback -- not a branch tip, not
        the producer's writable line home and not a caller's path;
      both are RESOLVED, which is what proves the objects are really there and
        are really commits with trees, rather than names somebody wrote down;
      and the two trees are listed and compared, which is what produces the
        changed path set the producer's own account is then held against.

    THE SCRATCH IS REMOVED WHETHER OR NOT THE READ SUCCEEDS, and it is removed
    by this port rather than by its caller: a private object store left behind
    by a refusal is host state nothing owns.
    """

    def __init__(self, identity, *, scratch=None, engine=None):
        self._identity = _required(identity, "a source correspondence port")
        self._scratch = scratch or self._identity["root"]
        self._profile = git_profile.GitIntegrationProfile(runner_for(engine))
        self._engine = runner_for(engine)
        self.asked = []

    def instance(self):
        return self._identity

    @staticmethod
    def _base_origin(request, bundle):
        return _base_origin_of(request, bundle)

    def correspondence_of(self, request):
        root = request["root"]
        named = [one for one in request["entries"]
                 if os.path.basename(one) == BUNDLE_ENTRY]
        if len(named) != 1:
            raise ContractRefusal(
                "refused", "precondition",
                f"the measured original carries {len(named)} entries named "
                f"{name_value(BUNDLE_ENTRY)}; the candidate's own objects are "
                f"exactly one measured file, and a correspondence read does "
                f"not go looking for them anywhere else")
        bundle = os.path.join(root, named[0])
        place = tempfile.mkdtemp(prefix="publication-correspondence-",
                                 dir=self._scratch)
        repository = os.path.join(place, "objects.git")
        vectors = []
        try:
            held = self._engine(tuple(bare_repository_vector(repository)))
            vectors.append(bare_repository_vector(repository))
            if type(held) is not dict or held.get("returncode") != 0:
                raise ContractRefusal(
                    "refused", "precondition",
                    "this port could not create a private object store for "
                    "the correspondence read; nothing was read")
            origin = self._base_origin(request, bundle)
            for revision, origin_of in ((request["base"], origin),
                                        (request["candidate"], bundle)):
                vectors.append(git_profile.import_vector(repository,
                                                        origin_of, revision))
                held = self._engine(tuple(vectors[-1]))
                if type(held) is not dict or held.get("returncode") != 0:
                    if origin_of != bundle:
                        raise ContractRefusal(
                            "refused", "precondition",
                            f"the line's recorded source does not hold the "
                            f"admitted base {name_value(revision)}; a base "
                            f"that cannot be read from the recorded source "
                            f"holds, and it is not looked for anywhere else")
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"the measured bundle does not carry "
                        f"{name_value(revision)}; a candidate the retained "
                        f"output cannot supply is not corresponded, and this "
                        f"read does not go looking for it elsewhere")
            base = self._profile.held(repository, request["base"],
                                      "the declared base")
            candidate = self._profile.held(repository, request["candidate"],
                                           "the retained candidate")
            vectors.append(git_profile.verify_vector(repository,
                                                     request["candidate"]))
            before, after = self._profile.corresponding_content(
                repository, request["base"], request["candidate"])
            vectors.append(git_profile.tree_entries_vector(
                repository, request["candidate"]))
        finally:
            shutil.rmtree(place, ignore_errors=True)
        changed = sorted(set(before) ^ set(after)
                         | {path for path in set(before) & set(after)
                            if before[path] != after[path]})
        self.asked.append(dict(request))
        return {"base": base["commit"], "candidate": candidate["commit"],
                "base_tree": base["tree"], "candidate_tree": candidate["tree"],
                "changed_paths": changed,
                "vectors": [list(one) for one in vectors]}


def _base_origin_of(request, bundle):
    """WHERE THE DECLARED BASE IS IMPORTED FROM for this request.

    THE BUNDLE, when the host owner answered no line source: the attempt
    layout, unchanged. THE LINE'S RECORDED SOURCE otherwise, and only when
    every one of these holds -- each a refusal that leaves the inspection
    HELD:

      the owner said the source is still the recorded object;
      the object at that path, asked again here immediately before use, has
        that same `device:inode` and is a real directory, not a link;
      the base being asked for is the exact base the line was declared on --
        so a result naming another base is not given the source's objects;
      and it is a FULL object name. A short name is a search, and a search
        can be answered by more than one object.
    """
    source = request.get("base_source")
    if source is None:
        return bundle
    members = ("path", "identity", "declared_base", "verified", "why")
    if type(source) is not dict or sorted(source) != sorted(members):
        raise ContractRefusal(
            "integrity", "schema",
            f"the line's recorded source is exactly {', '.join(members)}")
    taken = dict(source)
    if taken["verified"] is not True:
        raise ContractRefusal(
            "refused", "precondition",
            f"the declared base cannot be read: "
            f"{taken['why'] or 'the line source is unverified'}; a missing, "
            f"replaced or unverifiable source holds")
    place = taken["path"]
    if type(place) is not str or not os.path.isabs(place) \
            or os.path.islink(place) or not os.path.isdir(place) \
            or os.path.realpath(place) != place:
        raise ContractRefusal(
            "refused", "precondition",
            "the line's recorded source is no longer its own directory; a "
            "replaced source holds")
    found = os.lstat(place)
    if f"{found.st_dev}:{found.st_ino}" != taken["identity"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the line's recorded source was object "
            f"{name_value(taken['identity'])} and the entry there now is "
            f"another; a replaced source holds")
    base = request["base"]
    if type(base) is not str or len(base) not in (40, 64) \
            or any(one not in "0123456789abcdef" for one in base):
        raise ContractRefusal(
            "refused", "precondition",
            f"the declared base {name_value(base)} is not one full object "
            f"name; a base is imported by its exact name or not at all")
    if base != taken["declared_base"]:
        raise ContractRefusal(
            "refused", "precondition",
            f"the retained result declares base {name_value(base)} and its "
            f"line was declared on {name_value(taken['declared_base'])}; the "
            f"recorded source is read for the line's own admitted base and "
            f"for no other revision")
    return place


def publication_owners(request):
    """The two ports beside the four a recovery admission already composes.

    THE DEFAULT FACTORY, and the reason there is an operand for it at all is
    `recovery_decision.owners`': which owners a command acts through is a
    DEPLOYMENT fact, and a tool that could only ever compose one set would be
    this file deciding it for every installation.
    """
    identity = request["identity"]
    held = {"host": HostOutput(request["control_handle"], identity),
            "source": SourceCorrespondence(identity,
                                           scratch=request.get("scratch"),
                                           engine=request.get("engine"))}
    # W385695 checkpoint 2: AND THE ENDING PORT, when this deployment supplied
    # an Authority handle to compose it over. It is conditional rather than
    # required because `publication-inspect` and `publication-decide` perform
    # no assignment transition at all, and a factory that demanded an
    # Authority for a read-only inspection would be asking for a capability
    # that read does not use.
    if request.get("authority") is not None:
        held["ending"] = PriorAssignment(
            request["authority"], identity,
            sessions=request.get("sessions"))
    return held
