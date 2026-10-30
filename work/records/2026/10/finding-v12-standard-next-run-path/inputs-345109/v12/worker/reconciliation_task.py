"""W161230 slice2: the preparation workload, run inside an ordinary worker.

WHAT THIS OWNS. Everything between a preparation request arriving on the
ordinary input namespace and the measured candidate, causal report and harness
material being written under the declared outputs: materializing the immutable
source objects into this container's OWN private scratch, performing the
bounded merge, and running the configured causal sequence against three
content states.

WHAT IT DELIBERATELY DOES NOT DO, and these are pinned decisions rather than
choices this file made:

  IT IMPORTS NO MANAGER. There is no `baton_v12` here at all -- no Authority
  session, no store, no capacity owner, no publisher. A workload that could
  import the manager's capabilities would be a manager running under a
  worker's name, and the recipe beside this file installs none of them.

  IT TOUCHES NO TARGET. It has no lease, no grant and no writable target: the
  merge happens in scratch this container created, and what leaves here is
  MEASURED CONTENT, not a reference somebody moved.

  IT CLAIMS NOTHING ABOUT COLLECTION. A workload cannot say its output was
  frozen, taken into custody or accepted -- those are the manager\'s acts, and
  a report asserting them would be a claim about somebody else\'s store. What
  it answers is what it RAN and what happened.

  AND IT INVENTS NO STATUS. A command that ran has the integer it exited with;
  a command that never ran is named as not-run; a sequence cut short says so.
  There is no synthesized exit code anywhere in this file, because every
  number a status could be already means something.

THE CAUSAL SEQUENCE IS THE EXISTING ONE. `combined`, `base` and `isolated`
carry the meaning `_CausalObserver` already gave them -- the combined harness
carried into the original base is what makes a base failure evidence about the
missing fix rather than about a missing test. A base that fails BECAUSE the fix
is absent is positive evidence; a combined failure or a conflict is not
success, and this file never reports one as the other.
"""

import hashlib
import json
import os
import select
import signal
import stat
import subprocess
import time

VCS = "git"

# THE ORDINARY NAMESPACES, and nothing else. These are the worker contract\'s
# own roots; this file introduces no second delivery mechanism.
INPUT_ROOT = "/input"
OUTPUT_ROOT = "/output"
SCRATCH_ROOT = "/tmp/baton-preparation"

# WHERE THE PRODUCER PUBLISHES THE IMMUTABLE SOURCE ARTIFACTS, spelled the same
# way on both sides. `integration_bundle.PREPARATION_SOURCE_DIRECTORY` is the
# producer's name for it; a conformance case holds the two spellings equal, as
# the assignment and result namespaces already are.
SOURCE_DIRECTORY = "source"

# THE ONE EXPORTED OBJECT FILE, spelled the same on both sides.
OBJECTS_NAME = "objects.bundle"

REQUEST_NAME = "preparation-request.json"
REQUEST_SCHEMA = "baton.v12.managed-preparation-request/1"
REPORT_SCHEMA = "baton.v12.managed-preparation-report/1"

# THE CLOSED CONTRACT, SPELLED INDEPENDENTLY AND ON PURPOSE.
#
# Review claim166129 defect 1: the first form validated a SUBSET -- five
# members and the three object names -- so a document the manager's
# `adopt_preparation_request` refuses was accepted here. Two readers of one
# contract that disagree about what the contract IS are not two
# implementations; they are one bug with two halves, and the half inside the
# container is the one nobody can see.
#
# These names are the manager's `REQUEST_MEMBERS`, `SOURCE_MEMBERS`,
# `AUTHORITY_MEMBERS`, RESTATED rather
# than imported -- a worker that could import the manager is a worker one bug
# away from holding the manager's capabilities, and that constraint is not
# negotiable. The agreement is therefore held by a CASE built from a real
# accepted producer document rather than by a shared import, because a
# restatement nobody checks is exactly how the halves drift apart again.
REQUEST_MEMBERS = ("schema", "orchestration_id", "canonical_target_id",
                   "job_id", "line_id", "source_proposal_id", "source",
                   "authority", "harness_digest", "profile_digest",
                   "input_digest", "execution_limits", "commands")
SOURCE_MEMBERS = ("base", "candidate", "target_revision")
AUTHORITY_MEMBERS = ("path_set_digest", "test_scope_digest")
# NO LIMITS OR BOUNDARY MEMBER SET LIVES HERE ANY MORE. Both were mine, both
# were a second spelling of `baton_worker`'s `LAUNCH_LIMIT_MEMBERS` and
# `LAUNCH_BOUNDARY_MEMBERS`, and a restatement nobody checks is how two
# readers come to disagree. `owned_limits` composes that owner instead.

# THE IDENTITY MEMBERS and THE DIGEST MEMBERS, by the rule each is read under.
IDENTITY_MEMBERS = ("orchestration_id", "canonical_target_id", "job_id",
                    "line_id", "source_proposal_id")
DIGEST_MEMBERS = ("harness_digest", "profile_digest", "input_digest")

# BOUNDED, NO-FOLLOW INPUT. A request is a small document; a named pipe, a
# device or a symlink out of the input namespace is not one, and reading an
# unbounded stream inside a container is how a workload stops answering at all.
MAX_REQUEST_BYTES = 262144

# THE SAME BOUND FOR ANY FILE A TREE MEASUREMENT OPENS. A measurement that
# would read an arbitrarily large file is one an input can stall.
MAX_MEASURED_BYTES = 16777216

# THE THREE CONTENT STATES, in the order the existing observer established.
# `_CausalObserver.observe` runs combined FIRST for a reason this file inherits
# rather than restates by convention: the base PREDATES the test the producer
# brought with its fix, so the one harness run against all three states is the
# COMBINED content's own -- read there and carried into the base run.
CAUSAL_ORDER = ("combined", "base", "isolated")

HARNESS_NAME = "harness.py"

MAX_OUTPUT = 4096
# THE THREE CONTENT STATES, in the order the existing observer established.
# `_CausalObserver.observe` runs combined FIRST for a reason this file inherits
# rather than restates by convention: the base PREDATES the test the producer
# brought with its fix, so the one harness run against all three states is the
# COMBINED content's own -- read there and carried into the base run.
CAUSAL_ORDER = ("combined", "base", "isolated")

HARNESS_NAME = "harness.py"

MAX_OUTPUT = 4096


def _digest(body):
    if isinstance(body, str):
        body = body.encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


class PreparationConflict(Exception):
    """Two independent changes to one region. An ANSWER, not a crash."""


class PreparationRefusal(Exception):
    """What this workload answers with when it cannot proceed honestly."""


def _refuse(message):
    raise PreparationRefusal(message)


def _directory(place, what):
    """A directory descriptor, opened WITHOUT FOLLOWING ANY COMPONENT.

    REVIEW claim166235 DEFECT 2: checking `islink` on the final filename, or
    passing `followlinks=False` to `os.walk`, says nothing about the ROOT or
    any ancestor. A symlinked input root was accepted, and so was a symlinked
    tree root -- so the thing that decides what runs, and the thing whose
    content becomes an identity, could both be chosen from somewhere nobody
    declared.

    So every component is walked from the filesystem root and each one is
    opened `O_NOFOLLOW | O_DIRECTORY`. A link anywhere along the way refuses
    rather than resolving, and what is returned is a DESCRIPTOR: everything
    downstream is then reached relative to it, so the path cannot be swapped
    out from under a check that already passed.
    """
    place = os.path.abspath(place)
    held = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for name in [one for one in place.split(os.sep) if one]:
            try:
                opened = os.open(name, os.O_RDONLY | os.O_DIRECTORY
                                 | os.O_NOFOLLOW, dir_fd=held)
            except OSError as failure:
                _refuse(what + " is not reachable without following a link at "
                        + repr(name) + " (" + type(failure).__name__ + ": "
                        + str(getattr(failure, "strerror", "")) + ")")
            os.close(held)
            held = opened
    except BaseException:
        os.close(held)
        raise
    return held


def _bounded_read(directory, name, bound, what):
    """One regular file, opened no-follow AND READ FROM THAT DESCRIPTOR.

    THE CHECK AND THE READ ARE THE SAME OBJECT. Checking a path's size and
    type and then opening it BY NAME leaves a window in which the name can be
    pointed somewhere else, so the bound and the type were established about a
    file that is no longer the one being read. Here the descriptor is opened
    once, `fstat` describes THAT descriptor, and the bytes come from it.
    """
    try:
        # O_NONBLOCK IS NOT AN OPTIMISATION. Opening a fifo for reading BLOCKS
        # until somebody opens the write end, so a workload that merely
        # measured a tree containing one would stop answering entirely --
        # which is exactly what happened the first time this ran. The flag
        # makes the open return so the descriptor can be REFUSED for what it
        # is; regular files are unaffected by it.
        held = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
    except OSError as failure:
        _refuse(what + " could not be opened without following a link ("
                + type(failure).__name__ + ")")
    try:
        described = os.fstat(held)
        if not stat.S_ISREG(described.st_mode):
            _refuse(what + " is not a regular file; a measurement describes "
                    "content and this entry has none to describe")
        if described.st_size > bound:
            _refuse(what + " is larger than " + str(bound) + " bytes")
        body = b""
        while len(body) <= bound:
            piece = os.read(held, 65536)
            if not piece:
                break
            body += piece
        if len(body) > bound:
            _refuse(what + " grew past " + str(bound) + " bytes while it was "
                    "being read")
    finally:
        os.close(held)
    return body


def _closed(held, members, what):
    """EXACTLY these members -- missing AND extra both refuse.

    An open document is one the two implementations can disagree about in
    silence: the manager rebuilds a request through its own composer and a
    surplus member makes the rebuild unequal, so a reader here that ignored
    surplus would accept what the manager refuses.
    """
    if type(held) is not dict:
        _refuse(what + " is not one document")
    missing = [one for one in members if one not in held]
    if missing:
        _refuse(what + " carries no " + ", ".join(sorted(missing)))
    extra = [one for one in held if one not in members]
    if extra:
        _refuse(what + " carries " + ", ".join(sorted(extra)) + ", which this "
                "contract does not have; a document with a member nobody "
                "agreed on is one the manager will refuse to rebuild")
    return held


def _identity(value, what):
    """`boundaries.identity` is `boundaries.text` today, so this is that rule
    and not a tighter one written here."""
    return _digest_member(value, what)


def _digest_member(value, what):
    """A digest member, under THE MANAGER\'S OWN PREDICATE and no stricter.

    THIS IS THE SECOND HALF OF DEFECT 1, AND IT POINTS THE OTHER WAY. The
    obvious rule here -- `sha256:` and sixty-four hex characters -- is one the
    manager does NOT apply: it reads these through `boundaries.text`, which
    asks for exact, non-empty, encodable text. A worker enforcing the stricter
    rule would refuse documents the manager composes and accepts, which is the
    same disagreement as accepting what it refuses, merely inverted. The
    agreement case built from a real accepted producer document is what caught
    this, and it is why that case exists rather than a fixture written here.

    So the digest FORM is the producer\'s business. What the worker refuses is
    what the manager refuses: a value that is not durable text.
    """
    if type(value) is not str or value == "":
        _refuse(what + " is not durable text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        _refuse(what + " carries text that is not encodable")
    return value


def verify_input(root, request, name=REQUEST_NAME):
    """The published source artifacts ARE the ones the request was composed
    over -- measured here, not taken on the request\'s word.

    THE REQUEST IS EXCLUDED FROM WHAT IT DESCRIBES, which is what makes this
    answerable at all. `integration_bundle.compose_preparation_input` measures
    the source tree BEFORE the request exists on disk and puts that digest in
    the request; a digest over a tree containing the request could never be
    satisfied, because writing the request would change the tree it describes.
    The same exclusion is applied here, so the two halves measure the same
    thing.

    WHAT THIS DOES AND DOES NOT ESTABLISH. It proves the source artifacts were
    not changed after the producer measured them. It does NOT make the request
    trustworthy -- that is the launch\'s job (`owned_limits`), because a digest
    a document carries about material beside it says nothing about the document
    itself.
    """
    directory = _directory(root, "the input namespace")
    try:
        held = os.stat(SOURCE_DIRECTORY, dir_fd=directory,
                       follow_symlinks=False)
    except OSError:
        _refuse("this input namespace publishes no " + SOURCE_DIRECTORY
                + " tree for the request to be about")
    finally:
        os.close(directory)
    if not stat.S_ISDIR(held.st_mode):
        _refuse(SOURCE_DIRECTORY + " is not a directory")
    measured = measure(os.path.join(root, SOURCE_DIRECTORY))
    published = request["input_digest"]
    if measured["tree_digest"] != published:
        _refuse("the published source artifacts are not the ones this request "
                "was composed over: it names " + repr(published) + " and this "
                "namespace measures " + repr(measured["tree_digest"]))
    return measured


# WHICH OBJECT EACH CAUSAL STATE IS ABOUT. This is `_CausalObserver.observe`'s
# own mapping, read out of `tools/stage_execution.py` rather than named by
# convention: the combined state is the merged workspace AT THE CANDIDATE, the
# base is the original base, and the isolated state is the candidate alone.
STATE_REVISION = {"combined": "candidate", "base": "base",
                  "isolated": "candidate"}


def materialize(root, request, scratch=SCRATCH_ROOT, seconds=600):
    """DERIVE the three causal states here, in this container\'s own scratch.

    REVIEW claim168049 [P1]. The first form copied already-constructed
    `source/<state>` trees and said the manager owned the merge. That put the
    required preparation on the wrong side of the boundary: a container handed
    a finished combined tree derives nothing, cannot retain the target\'s own
    changes, and can never meet a conflict -- so its success said nothing about
    where that content came from. Selected sequence 5 allows the coordinator a
    read-only object export and nothing more.

    SO THIS DOES THE MERGE. The published bundle carries exactly the three
    accepted revisions; this creates a repository in private scratch, imports
    those objects, and derives:

      `combined`   the ORIGINAL CANDIDATE merged into the PINNED TARGET
                   SNAPSHOT. This is the derived content, and its revision and
                   tree are NEW -- they are not `source.candidate`.
      `base`       the original base, untouched.
      `isolated`   the original candidate, untouched.

    THE DERIVED IDENTITY IS CARRIED SEPARATELY, which is the other half of the
    finding. `_CausalObserver.observe` uses `basis["candidate"]` for the
    prepared workspace and `self._candidate` for the original isolated line;
    those are two different identities and labelling a copied state does not
    make them one. Each state answers with the revision and tree it ACTUALLY
    has, plus whether that identity was derived here.

    A CONFLICT IS AN ANSWER, NOT A FAILURE TO REPORT. Two independent changes
    to one region cannot be combined, and a preparation that resolved that by
    preferring a side would be inventing a candidate nobody wrote.
    """
    os.makedirs(scratch, 0o700, exist_ok=True)
    os.chmod(scratch, 0o700)
    repository = os.path.join(scratch, "objects")
    if os.path.exists(repository):
        _refuse("this scratch already holds a repository; a preparation "
                "materializes into a directory it created, and reusing one "
                "would derive from content from somewhere else")
    os.mkdir(repository, 0o700)
    source = request["source"]
    _import_objects(root, repository, seconds)
    for name in ("base", "candidate", "target_revision"):
        _proved(repository, source[name], seconds)

    states, derived = {}, _derive_combined(repository, source, seconds)
    for name in request["commands"]:
        place = os.path.join(scratch, name)
        if os.path.exists(place):
            _refuse("this scratch already holds " + name)
        os.mkdir(place, 0o700)
        if name == "combined":
            revision = derived["revision"]
            _extract(repository, revision, place, seconds)
        else:
            revision = source[STATE_REVISION[name]]
            _extract(repository, revision, place, seconds)
        states[name] = {"path": place, "revision": revision,
                        "tree": _tree_of(repository, revision, seconds),
                        # WHETHER THIS IDENTITY WAS MADE HERE. A reader must be
                        # able to tell the derived candidate from the original.
                        "derived": name == "combined",
                        "original_revision": source[STATE_REVISION[name]]}
    states["__derived__"] = derived
    return {name: held for name, held in states.items()
            if name != "__derived__"}, derived


def _copy_tree(published, place):
    """Bytes only, through the same no-follow boundary `measure` uses.

    Used to hand DERIVED content out to a declared output: the state itself
    stays in private scratch, and what leaves is a copy the manager asked for.
    """
    holder = _directory(published, "the state " + published)
    try:
        for root, directories, names in os.walk(published, followlinks=False):
            where = os.path.relpath(root, published)
            if os.path.basename(root) == "." + VCS:
                directories[:] = []
                continue
            directories[:] = [one for one in sorted(directories)
                              if one != "." + VCS]
            for one in directories:
                if os.path.islink(os.path.join(root, one)):
                    _refuse("this state contains the symlinked directory "
                            + one)
                os.makedirs(os.path.join(place, where, one), 0o700,
                            exist_ok=True)
            for one in sorted(names):
                source = _directory(root, "the directory holding " + one)
                try:
                    body = _bounded_read(source, one, MAX_MEASURED_BYTES, one)
                finally:
                    os.close(source)
                target = os.path.normpath(os.path.join(place, where, one))
                with open(target, "wb") as handle:
                    handle.write(body)
                os.chmod(target, 0o600)
    finally:
        os.close(holder)


def export_derived_objects(repository, derived, states, destination, seconds):
    """Retain the exact commit and modes; reject harness-mutated content."""
    revision = derived["revision"]
    _proved(repository, revision, seconds)
    if _tree_of(repository, revision, seconds) != derived["tree"]:
        _refuse("the derived Git tree differs from the reported candidate")
    verified = os.path.join(os.path.dirname(repository), "exported-candidate")
    os.mkdir(verified, 0o700)
    _extract(repository, revision, verified, seconds)
    if measure(verified) != measure(states["combined"]["path"]):
        _refuse("the preparation harness changed the derived candidate; its output cannot substitute for the Git tree")
    reference = "refs/baton/prepared/candidate"
    _vcs_or_refuse(["-C", repository, "update-ref", reference, revision], repository, seconds, "retain the derived object identity")
    _vcs_or_refuse(["-C", repository, "bundle", "create", destination, reference], repository, seconds, "export the derived Git objects")


def _vcs_or_refuse(argv, cwd, seconds, what):
    answered = vcs(argv, cwd, seconds)
    if answered["status"] != 0:
        _refuse("the configured version-control tool could not " + what
                + (": " + answered["output"].strip()[:240]
                   if answered["output"].strip() else ""))
    return answered["output"]


def _import_objects(root, repository, seconds):
    """The published objects, and ONLY those.

    The bundle is the whole object supply: there is no remote, no network and
    no other line reachable from this container, so what a preparation can
    derive from is bounded by what was accepted and exported.
    """
    bundle = os.path.join(root, SOURCE_DIRECTORY, OBJECTS_NAME)
    if not os.path.isfile(bundle) or os.path.islink(bundle):
        _refuse("this input namespace publishes no " + SOURCE_DIRECTORY + "/"
                + OBJECTS_NAME + ", and a preparation derives from the "
                "accepted objects rather than from whatever is lying about")
    _vcs_or_refuse(["init", "--quiet", "--bare", repository], repository,
                   seconds, "create the private object store")
    _vcs_or_refuse(["-C", repository, "fetch", "--quiet", bundle,
                    "refs/*:refs/bundled/*"], repository, seconds,
                   "import the published objects")


def _proved(repository, revision, seconds):
    """The accepted revision is REALLY in what was published."""
    answered = vcs(["-C", repository, "cat-file", "-e", revision + "^{commit}"],
                   repository, seconds)
    if answered["status"] != 0:
        _refuse("the published objects do not contain " + revision
                + "; a preparation runs the snapshot it was accepted for")
    return revision


def _tree_of(repository, revision, seconds):
    return _vcs_or_refuse(["-C", repository, "rev-parse", revision + "^{tree}"],
                          repository, seconds,
                          "read the tree of " + revision).strip()


def _derive_combined(repository, source, seconds):
    """The original candidate merged INTO the pinned target snapshot.

    THE TARGET IS THE FIRST PARENT, which is what makes the target\'s own
    changes survive: a preparation that took the candidate\'s tree wholesale
    would silently discard everything the target gained since the base.
    """
    # THE STATUS IS READ BEFORE THE OUTPUT. `merge-tree` answers 0 for a clean
    # combination and 1 for a conflicted one, and a CONFLICT IS AN ANSWER: it
    # is not the tool failing, it is the tool reporting that these two changes
    # cannot both be kept. Treating it as a failure would lose the distinction
    # between "this cannot be combined" and "this could not be attempted".
    answered = vcs(["-C", repository, "merge-tree", "--write-tree",
                    "--merge-base=" + source["base"],
                    source["target_revision"], source["candidate"]],
                   repository, seconds)
    merged = (answered["output"] or "").splitlines()
    if answered["status"] == 1:
        raise PreparationConflict(
            "the candidate and the target snapshot changed the same content "
            "and cannot be combined; this workload does not resolve that by "
            "preferring a side: "
            + " ".join(one.strip() for one in merged[1:] if one.strip())[:400])
    if answered["status"] != 0:
        _refuse("the configured version-control tool could not combine the "
                "candidate with the target snapshot"
                + (": " + (answered["output"] or "").strip()[:240]
                   if (answered["output"] or "").strip() else ""))
    if not merged or not merged[0].strip():
        _refuse("the version-control tool answered no combined tree")
    tree = merged[0].strip()
    revision = _vcs_or_refuse(
        ["-C", repository, "commit-tree", tree,
         "-p", source["target_revision"], "-p", source["candidate"],
         "-m", "derived preparation candidate"],
        repository, seconds, "record the combined content").strip()
    return {"revision": revision, "tree": tree,
            "base": source["base"], "candidate": source["candidate"],
            "target_revision": source["target_revision"]}


def _extract(repository, revision, place, seconds):
    """One revision\'s content into one private directory. No worktree, no
    index in the caller\'s scratch, and nothing writable pointing anywhere but
    here."""
    _vcs_or_refuse(["-C", repository, "--work-tree=" + place, "checkout",
                    "--quiet", revision, "--", "."], repository, seconds,
                   "extract " + revision)


def owned_limits(launch):
    """THE JOB\'S ACTUAL RESOLVED LIMITS, through the boundary that already
    owns them in this image.

    REVIEW claim166368: generation 999 passed this workload and was refused by
    the manager, and neither a checksum echoed beside untrusted data nor the
    document\'s own self-consistency establishes what a Job actually resolved
    to. Both are true, and the reason the first two attempts here were wrong
    is the same: the REQUEST is untrusted input. Nothing carried inside it can
    make it trustworthy.

    The launch document is not. `baton_worker` already reads it, verifies
    `execution_limits` against `execution_limits_digest` -- "a bound this
    container cannot verify is a bound nobody agreed to" -- and holds the
    whole document to `LAUNCH_LIMIT_MEMBERS`, the settings it names, the
    origins it knows and the seconds range the Job owner admits. That is the
    manager-written, per-attempt, sealed anchor this container already has,
    and `baton_worker` imports no manager, so composing it costs nothing that
    matters.

    SO THIS RE-DERIVES NOTHING AND RESTATES NOTHING. My own `_limits` grew a
    shape check, then an invented `origin == "request"` rule -- a name that is
    not even in the owned vocabulary, which is `LAUNCH_ORIGINS` -- and it
    would have kept growing into a second resolution authority one corruption
    at a time. It is gone.
    """
    execution = launch.get("job_execution") if type(launch) is dict else None
    if type(execution) is not dict or "execution_limits" not in execution:
        _refuse("this container was launched without a Job execution, so it "
                "has no verified limits to run a preparation under")
    return execution["execution_limits"]


def _same_types(value, owned, where):
    """EQUALITY IS NOT ENOUGH, because Python\'s equality is not the
    contract\'s.

    Review/selection carry a strict numeric-type correction: `300 == 300.0` is
    True and so is `{"seconds": 300} == {"seconds": 300.0}`, so a float
    representation walks straight through a comparison that looks exact while
    the manager -- whose boundary is integer-owned -- refuses it. `True == 1`
    is the same hole one step further down. So the TYPES are compared
    alongside the values, recursively, and a number that is not the kind of
    number the contract is about is refused for what it is.
    """
    if type(value) is not type(owned):
        _refuse(where + " is " + type(value).__name__ + " where this contract "
                "is " + type(owned).__name__ + "; a float that compares equal "
                "to an integer is still not one")
    if type(owned) is dict:
        for name in owned:
            if name in value:
                _same_types(value[name], owned[name], where + "." + str(name))
    elif type(owned) is list:
        for index, one in enumerate(owned):
            if index < len(value):
                _same_types(value[index], one,
                            where + "[" + str(index) + "]")


def _limits(value, owned):
    """The request\'s limits, held to the LAUNCH\'S OWN VERIFIED DOCUMENT.

    Equality, and nothing weaker. The manager composed the request from the
    same resolution it sealed into the launch, so a request whose limits
    differ in ANY member -- a generation this build cannot reproduce, a unit
    nobody honours, a boundary moved by one second -- is not describing the
    Job this container was launched for. Which member differs does not need a
    rule here; that it differs is the whole answer.
    """
    if type(value) is not dict:
        _refuse("the execution limits are not one document")
    _same_types(value, owned, "the execution limits")
    if value != owned:
        differs = sorted(set(value) ^ set(owned)) or sorted(
            one for one in owned if value.get(one) != owned.get(one))
        _refuse("these limits are not the ones this container was launched "
                "under; they differ at " + ", ".join(differs) + ". A request "
                "is untrusted input and the launch document is the sealed "
                "resolution, so the launch decides")
    return value


def _commands(value):
    if type(value) is not list or not value:
        _refuse("this request asks for no command at all")
    if len(set(value)) != len(value):
        _refuse("this request names a command twice, and a phase that ran "
                "once cannot answer twice")
    for one in value:
        if one not in CAUSAL_ORDER:
            _refuse("this request asks for " + repr(one) + " and this "
                    "workload runs " + ", ".join(CAUSAL_ORDER))
    return list(value)


def read_request(root=INPUT_ROOT, name=REQUEST_NAME, *, owned):
    """The semantic request, read from the ordinary input namespace.

    THE VALUES ARE NOT RE-DERIVED. This container cannot recompute a digest the
    manager took over material it does not hold. What it CAN do -- and what
    defect 1 was about -- is refuse every document the manager's own reader
    would refuse, so that the two independent implementations accept exactly
    the same set.

    ITS LIMITS ARE THE LAUNCH\'S, NOT ITS OWN. `owned` is the verified
    resolution from `owned_limits(launched(...))`; see `_limits`.

    BOUNDED AND NO-FOLLOW. The request is opened only if it is a regular file
    reached without traversing a symlink, and only up to a bound: a link out of
    the input namespace would let the thing that decides what runs be chosen
    from somewhere nobody declared.
    """
    directory = _directory(root, "the input namespace")
    try:
        try:
            os.stat(name, dir_fd=directory, follow_symlinks=False)
        except OSError:
            _refuse("this worker was given no " + name + " on its input "
                    "namespace; a preparation runs what it was asked for")
        body = _bounded_read(directory, name, MAX_REQUEST_BYTES, name)
    finally:
        os.close(directory)
    try:
        held = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        _refuse(name + " is not readable as one document")
    _closed(held, REQUEST_MEMBERS, name)
    if held["schema"] != REQUEST_SCHEMA:
        _refuse(name + " is not a " + REQUEST_SCHEMA)
    for member in IDENTITY_MEMBERS:
        _identity(held[member], name + " member " + member)
    for member in DIGEST_MEMBERS:
        _digest_member(held[member], name + " member " + member)
    source = _closed(held["source"], SOURCE_MEMBERS, "the request source")
    for member in SOURCE_MEMBERS:
        value = source[member]
        if type(value) is not str or len(value) != 40 \
                or any(one not in "0123456789abcdef" for one in value):
            _refuse(name + " names " + member + " " + repr(value) + ", which "
                    "is not one full object name; a preparation is about an "
                    "immutable snapshot")
    authority = _closed(held["authority"], AUTHORITY_MEMBERS,
                        "the request authority")
    for member in AUTHORITY_MEMBERS:
        _digest_member(authority[member], "the authority's " + member)
    _limits(held["execution_limits"], owned)
    _commands(held["commands"])
    return held


def run_bounded(argv, cwd, seconds):
    """One bounded command, with its REAL status and its own bounded output.

    A TIMEOUT IS NOT AN EXIT CODE. It is reported as a command that produced
    NO STATUS, which is a different answer and stays a different answer all
    the way out of this file -- the manager\'s report vocabulary has a place
    for exactly that, and filling it with a number would destroy it.

    THE CHILD OWNS A PROCESS GROUP, AND THE GROUP IS WHAT ENDS. Review
    claim166235: `subprocess.run(timeout=...)` signals the DIRECT CHILD only,
    so a harness that forked left descendants running with the pipe still
    open -- the read would block on them, and the workload would have reported
    a timeout while the work it started was still going. `start_new_session`
    puts the child in its own group, the whole group is signalled, and the
    ending is then WAITED FOR rather than assumed: TERM first, and KILL if the
    group is still there. A signal that was sent is not a process that ended.

    THE OUTPUT IS DRAINED AS IT ARRIVES AND BOUNDED THERE. `capture_output`
    buffers everything and only then gets sliced, so `MAX_OUTPUT` bounded the
    report and not the memory: a harness printing without end could exhaust
    the container before the slice ever happened. Reading into a bounded
    buffer means what is not kept is never held.
    """
    try:
        child = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 start_new_session=True)
    except OSError as failure:
        return {"status": None, "tag": "start-failed",
                "output": "no status: " + type(failure).__name__}
    # THE GROUP IDENTITY IS TAKEN AT LAUNCH AND RETAINED. Review claim166368
    # [P1]: `_ended` asked `os.getpgid(child.pid)` at ending time, so a leader
    # that had already exited made the lookup fail and the function returned a
    # timeout WITHOUT SIGNALLING OR CHECKING THE SURVIVING GROUP. The group is
    # this workload's to end, so its identity is recorded while the leader is
    # certainly alive -- `start_new_session` makes the child its own leader, so
    # the group IS its pid -- and the ending never depends on looking it up
    # again.
    group = child.pid
    kept, dropped, ended = b"", 0, time.monotonic() + seconds
    try:
        os.set_blocking(child.stdout.fileno(), False)
        while True:
            left = ended - time.monotonic()
            if left <= 0:
                return _ended(child, group, "timeout",
                              "no status: the command exceeded "
                              + str(seconds) + "s", kept, dropped)
            try:
                select.select([child.stdout], [], [], min(left, 0.25))
                piece = child.stdout.read(65536)
            except (OSError, ValueError):
                # AN EXCEPTIONAL READER EXIT IS STILL AN ENDING. The group was
                # started by this workload and does not get to outlive the
                # thing that was reading it.
                return _ended(child, group, "reader-failed",
                              "no status: this workload could not go on "
                              "reading the command's output", kept, dropped)
            if piece:
                room = MAX_OUTPUT - len(kept)
                if room > 0:
                    kept += piece[:room]
                dropped += max(0, len(piece) - max(room, 0))
                continue
            if piece is None:
                # NOTHING READY YET, which is not end-of-file. A child that
                # merely has not written must not be mistaken for one that has
                # finished, or a slow harness would be cut off early.
                if child.poll() is not None:
                    break
                continue
            # EOF ON THE PIPE. Every writer is gone -- which is a statement
            # about the PIPE, not about the group: a descendant that closed
            # its inherited copy and kept running would produce exactly this.
            break
        while child.poll() is None:
            if time.monotonic() >= ended:
                return _ended(child, group, "timeout",
                              "no status: the command exceeded "
                              + str(seconds) + "s", kept, dropped)
            time.sleep(0.01)
    finally:
        try:
            child.stdout.close()
        except OSError:
            pass
    # ORDINARY COMPLETION IS STILL AN ENDING. Review claim166368: the leader
    # exiting zero says nothing about children it left behind, and this
    # workload does not hand back a measured status while work it started is
    # still running under its own group.
    status = child.returncode
    _exclude(child, group, "this command exited " + str(status)
             + " and left a process group that could not be ended")
    return {"status": status, "tag": None,
            "output": _output(kept, dropped)}


def _output(kept, dropped):
    body = kept.decode("utf-8", "replace")
    if dropped:
        # WHAT WAS DROPPED IS SAID, because output that silently stops looks
        # exactly like output that ended.
        body += ("\n[" + str(dropped) + " further bytes were not kept; this "
                 "workload bounds what it holds at " + str(MAX_OUTPUT) + "]")
    return body


def _group_is_gone(group):
    """Is the group EMPTY -- not, is the leader reaped.

    `killpg(group, 0)` delivers nothing and answers whether any process is
    still in it. `ProcessLookupError` is the only answer that means gone;
    `PermissionError` means something IS there and is not ours to signal,
    which is not an exclusion.
    """
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _exclude(child, group, complaint):
    """END THE GROUP AND OBSERVE THAT IT IS GONE.

    REVIEW claim166368 [P1]. The first form watched `child.poll()`, which
    reports only the LEADER: a descendant that ignored SIGTERM while the
    leader died broke the loop before SIGKILL was ever sent, and a leader that
    had already exited made the whole sequence a no-op. Leader reaping is not
    whole-tree ending, and this function does not infer one from the other.

    So the leader is reaped first -- a zombie is still a member of its own
    group and would make the group look occupied forever -- and then the
    GROUP is signalled and re-observed. TERM, then KILL, and if the group
    still answers after both, this workload REFUSES rather than reporting a
    bounded run whose processes it could not exclude.
    """
    for signalled, patience in ((signal.SIGTERM, 5.0), (signal.SIGKILL, 5.0)):
        try:
            os.killpg(group, signalled)
        except ProcessLookupError:
            # NOBODY LEFT TO SIGNAL. That is an exclusion observation, not a
            # reason to stop looking: it is confirmed below like any other.
            pass
        except PermissionError:
            break
        until = time.monotonic() + patience
        while time.monotonic() < until:
            # REAP THE LEADER so its own zombie does not hold the group open,
            # then ask about the GROUP rather than about the leader.
            child.poll()
            if _group_is_gone(group):
                return
            time.sleep(0.01)
    child.poll()
    if not _group_is_gone(group):
        _refuse(complaint)


def _ended(child, group, tag, why, kept, dropped):
    """A run that produced no status, ended and OBSERVED to be gone."""
    _exclude(child, group, "this command could not be ended after SIGTERM "
             "and SIGKILL; a run whose process group still answers has not "
             "been bounded, and this workload will not call that a timeout")
    return {"status": None, "tag": tag, "output": _output(kept, dropped)
            + "\n" + why}


def vcs(argv, cwd, seconds):
    """The configured version-control tool, named once."""
    return run_bounded([VCS] + list(argv), cwd, seconds)


def measure(place):
    """Every regular file under one tree, by path, digest and length.

    SORTED AND WHOLE. A manifest that skipped a file would describe a
    different tree, and one whose order varied would digest differently for
    the same content.

    AN UNSUPPORTED ENTRY REFUSES; IT IS NOT DROPPED. Review claim166129
    defect 2: the first form SKIPPED symlinks and other non-regular entries,
    and `os.walk` omits symlinked directories on its own. So one tree_digest
    could describe a tree with those entries and a tree without them -- two
    different trees with one identity, which is the whole thing a content
    identity exists to prevent. The link is not followed and it is not
    ignored: it is named, and the measurement stops.

    NO-FOLLOW IS THE OTHER HALF. Following a link would let a tree describe
    bytes that live outside it, which is the same defect pointed the other
    way.
    """
    # THE TREE ROOT ITSELF, through the same boundary as everything under it.
    # A symlinked root was accepted before, which let a measured tree be
    # chosen from outside the namespace that declared it.
    os.close(_directory(place, "the measured tree root"))
    entries = []
    for root, directories, files in os.walk(place, followlinks=False):
        # THE DIRECTORIES ARE INSPECTED BEFORE THEY ARE DESCENDED. `os.walk`
        # silently leaves a symlinked directory out of its traversal, so
        # checking only the files would let one disappear without a word.
        for name in sorted(directories):
            if name == "." + VCS:
                continue
            if os.path.islink(os.path.join(root, name)):
                _refuse("this tree contains the symlinked directory "
                        + os.path.relpath(os.path.join(root, name), place)
                        + "; a measurement that skipped it would give two "
                        "different trees one identity")
        directories[:] = sorted(one for one in directories
                                if one != "." + VCS)
        for name in sorted(files):
            full = os.path.join(root, name)
            where = os.path.relpath(full, place)
            if os.path.islink(full):
                _refuse("this tree contains the symlink " + where + "; its "
                        "target is not content this tree holds, and omitting "
                        "it would give two different trees one identity")
            # OPENED NO-FOLLOW AND READ FROM THAT DESCRIPTOR, so the type and
            # the bound are established about the same object the bytes come
            # from rather than about a name that can be repointed in between.
            holder = _directory(root, "the directory holding " + where)
            try:
                body = _bounded_read(holder, name, MAX_MEASURED_BYTES, where)
            finally:
                os.close(holder)
            entries.append({"path": where,
                            "content_digest": _digest(body),
                            "bytes": len(body)})
    entries.sort(key=lambda one: one["path"])
    return {"entries": entries, "entry_count": len(entries),
            "total_bytes": sum(one["bytes"] for one in entries),
            "tree_digest": _digest(_canonical(entries))}


def observe(request, states, seconds):
    """Run the pinned harness against each state, in the pinned order.

    THE HARNESS IS THE COMBINED CONTENT\'S OWN, and it is CARRIED into the base
    run. This is `_CausalObserver.observe`\'s rule, not a choice made here: the
    base predates the test the producer brought with its fix, so running the
    base against whatever harness the base happens to contain would measure a
    test that cannot exercise the fix -- and a base failure would then be
    evidence about a missing file rather than about the missing fix. The
    isolated state carries the producer\'s own harness already, because the fix
    and its test arrived together.

    THE COMPLETED PREFIX AND THE NOT-RUN SUFFIX ARE BOTH KEPT. A sequence that
    stopped partway is not a shorter sequence that passed: the first command
    that produces no status ends the run, and the ones after it are NAMED as
    not-run rather than silently dropped.
    """
    completed, not_run, tag = [], [], None
    # THE PHASE THAT WAS ATTEMPTED AND PRODUCED NO STATUS. Review claim166129
    # defect 3: the first form appended that phase to `not_run` AND then
    # appended the suffix, so a base timeout answered [base, isolated] -- which
    # says the base never ran. It DID run; it produced no status. The accepted
    # `_CausalObserver` reports phase=base with suffix=[isolated], and these
    # two facts stay separate here for the same reason: a phase that was
    # attempted is evidence, and one that never started is not.
    failed_phase = None
    harness = None
    harness_measured = None
    for name in request["commands"]:
        if name not in states:
            _refuse("this request asks for " + repr(name) + " and this "
                    "workload runs " + ", ".join(CAUSAL_ORDER))
        if tag is not None:
            # GENUINELY UNEXECUTED, and only these. The phase that was cut
            # short is carried as `failed_phase`, not here.
            not_run.append(name)
            continue
        place = states[name]["path"]
        added = False
        pinned = None
        if name == "base":
            if harness is None:
                # THE CARRY HAS NO SOURCE. The combined state is what pins the
                # harness, so a sequence that asks for the base without having
                # run the combined state first cannot honestly measure it --
                # and substituting the base\'s own file would answer a
                # different question under this one\'s name.
                _refuse("the base state is measured with the combined "
                        "content\'s harness, and this sequence has not run "
                        "the combined state; order is " +
                        ", ".join(CAUSAL_ORDER))
            with open(os.path.join(place, HARNESS_NAME), "wb") as handle:
                handle.write(harness)
            added = True
        if name == "combined":
            # PINNED BEFORE IT RUNS, not after. Review claim166129: the first
            # form read the harness only once the run had finished, so a
            # harness that rewrote itself would have had DIFFERENT bytes
            # carried into the base than the ones whose status was just
            # measured -- and the report would still have called them the same
            # harness. What is measured and what is carried must be the same
            # bytes, so they are taken before execution can touch them.
            try:
                with open(os.path.join(place, HARNESS_NAME), "rb") as handle:
                    pinned = handle.read()
            except OSError:
                _refuse("the combined state has no " + HARNESS_NAME + " to "
                        "pin; its status would measure something else")
        answered = run_bounded(["python3", HARNESS_NAME], place, seconds)
        if answered["status"] is None:
            tag = answered["tag"]
            failed_phase = name
            continue
        if name == "combined":
            # AND IT MUST STILL BE THOSE BYTES. A harness that rewrote itself
            # during its own run did not measure what this report is about to
            # say it measured, and carrying the rewritten copy into the base
            # would compare two states against two different tests.
            try:
                with open(os.path.join(place, HARNESS_NAME), "rb") as after:
                    unchanged = after.read()
            except OSError:
                _refuse("the combined " + HARNESS_NAME + " did not survive "
                        "its own run")
            if unchanged != pinned:
                _refuse("the combined " + HARNESS_NAME + " rewrote itself "
                        "while running; the bytes that produced this status "
                        "are not the bytes that would reach the base")
            harness = pinned
            harness_measured = _digest(pinned)
        completed.append({"name": name, "status": answered["status"],
                          "harness_added": added,
                          "output": answered["output"]})
    return completed, not_run, tag, failed_phase, harness_measured


def compose_report(request, states, completed, not_run, tag,
                   failed_phase=None, harness_measured=None):
    """What this workload actually observed, in the manager\'s own three
    answers -- measured, collected-without-status, or nothing collected.

    IT NEVER SAYS `integrated`, `accepted` or `collected`. Those are the
    manager\'s words about its own acts.
    """
    if not completed and tag is None:
        kind = "not-collected"
    elif tag is not None:
        kind = "collected-without-status"
    else:
        kind = "measured"
    status = None
    if kind == "measured":
        # THE SEQUENCE\'S OWN ANSWER: the first nonzero status, or zero when
        # every command that ran succeeded. Nothing is invented for the ones
        # that did not run, because none did.
        failed = [one for one in completed if one["status"] != 0]
        status = failed[0]["status"] if failed else 0
    return {"schema": REPORT_SCHEMA,
            "orchestration_id": request.get("orchestration_id"),
            "kind": kind, "status": status, "tag": tag,
            # THE PHASE THAT WAS ATTEMPTED, named separately from the suffix
            # that never started -- the accepted observer's own distinction.
            "phase": failed_phase,
            "completed": [{"name": one["name"], "status": one["status"],
                           "harness_added": one["harness_added"]}
                          for one in completed],
            "not_run": list(not_run),
            # WHAT THE REQUEST ASKED FOR, and -- separately -- WHAT WAS
            # ACTUALLY PINNED AND RUN. Echoing only the former would let this
            # report assert an identity it never observed.
            "harness_digest": request["harness_digest"],
            "harness_measured_digest": harness_measured,
            "source": dict(request["source"]),
            "states": {name: {"revision": held["revision"],
                              "content": measure(held["path"])}
                       for name, held in sorted(states.items())},
            "output": [{"name": one["name"], "output": one["output"]}
                       for one in completed]}
