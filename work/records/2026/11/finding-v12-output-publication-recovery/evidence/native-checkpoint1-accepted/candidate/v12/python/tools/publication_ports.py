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

__all__ = ["HostOutput", "SourceCorrespondence", "BUNDLE_ENTRY",
           "COMMAND_SECONDS", "bare_repository_vector", "publication_owners",
           "runner_for"]

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

    def output_of(self, attempt_id, *, read=()):
        """The proved, measured original, with the named entries' bytes.

        ONE COHERENT BOUNDARY, `HostExclusion.evidence_of`'s rule: the
        snapshot makes every answer describe ONE state of the control store,
        so a torn read cannot produce a preparation record and a measurement
        that never coexisted. The filesystem measurement itself happens
        outside any transaction, which is the contract's own requirement.
        """
        with self._control.snapshot() as control:
            return retained_output_of(
                control, attempt_id, names=tuple(read),
                what=f"the original output of attempt "
                     f"{name_value(attempt_id)}")


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
      the candidate and the base are FETCHED FROM THE MEASURED BUNDLE, by the
        path the trust-root owner measured -- not from a nominated checkout,
        not from a remote and not from a path a caller named;
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
            for revision in (request["base"], request["candidate"]):
                vectors.append(git_profile.import_vector(repository, bundle,
                                                        revision))
                held = self._engine(tuple(vectors[-1]))
                if type(held) is not dict or held.get("returncode") != 0:
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
            before = self._profile.content(repository, request["base"])
            after = self._profile.content(repository, request["candidate"])
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


def publication_owners(request):
    """The two ports beside the four a recovery admission already composes.

    THE DEFAULT FACTORY, and the reason there is an operand for it at all is
    `recovery_decision.owners`': which owners a command acts through is a
    DEPLOYMENT fact, and a tool that could only ever compose one set would be
    this file deciding it for every installation.
    """
    identity = request["identity"]
    return {"host": HostOutput(request["control_handle"], identity),
            "source": SourceCorrespondence(identity,
                                           scratch=request.get("scratch"),
                                           engine=request.get("engine"))}
