"""The integration workload: an accepted bundle, one provider turn, and proof.

W110935, `work/records/2026/09/finding-v12-integration-worker-workload/`.

WHAT THIS OWNS. Everything between an integration assignment arriving on a
mounted namespace and an `baton.v12.integration-result/1` document being
composed for it: the correlation that proves this bundle is THIS runtime's,
the whole-path preflight that runs before any target is touched, the one
provider turn taken through `ClaudeAgent.invoke_provider`, this module's OWN
read-back of every scheduled path's bytes and modes, and the conservative
ending. `integration_contract` owns the bundle's shape and this consumes it;
`integration_entry` composes this with the durable files and publishes what it
answers.

WHAT IT DELIBERATELY DOES NOT DO. It never writes into the target. The PROVIDER
performs the import -- that is the whole point of a model-driven workload, and
a host-side copier in this file wearing the provider's name would be a
different capability with the same result document. It also never repairs: no
mode change to make a target writable, no candidate redesign, no conflict
resolution, no version-control mutation of any kind.

THE FOUR THINGS A REVIEWER SHOULD CHECK FIRST, because they are the pinned
decisions this file implements rather than choices it made:

  THE BUNDLE IDENTITY IS THE PRODUCER'S `bundle_digest`, which is the canonical
  digest of the measured whole-file manifest -- one entry per emitted file --
  and NOT `envelope_digest`, which covers `integration.json` alone. It is
  MEASURED here by walking the mounted bundle, because a number a bundle
  states about itself is a claim and this comparison exists to test claims.

  THE CORRELATION SET IS COMPLETE BEFORE THE PROVIDER STARTS. An internally
  consistent bundle has proved nothing about being this runtime's bundle,
  which is why `read_bundle` deliberately answers no verdict: the assignment
  digest, the launch digest, the instruction digest, the accepted path set,
  the scheduled test scope, the frozen review and the expected target revision
  are all compared here.

  THE PREFLIGHT IS WHOLE AND PRECEDES EVERY WRITE, so a later invalid row
  cannot follow an earlier successful one.

  THE ENDING IS CONSERVATIVE. `refused` is published ONLY when no provider was
  started -- which is the one thing this workload can positively establish
  about a mutation-free refusal. Once a provider has had writable work,
  anything short of a verified complete import is `held`; unchanged final
  bytes do not establish absence of mutation, because restoration is not
  absence.

WHAT IS NOT CLAIMED. These checks are not a kernel-enforced per-path write
allowlist. The provider runs with the granted target mount and may leave
descendants after its leader exits, so this file proves what it OBSERVED about
the scheduled paths and one bounded version-control witness -- not whole-
repository equivalence and not runtime quiescence. The manager owns positive
quiescence before settlement.

TWO CAPABILITIES ARE SPELLED HERE THAT THE CONTRACT DOES NOT EXPOSE, and the
duplication is deliberate rather than unnoticed. `integration_contract` has no
public whole-bundle measurement and no public bounded no-follow file reader --
its `_read_exact` and `_descend` are private -- and it owns no canonical JSON
serializer, which the manifest digest and the accepted path-set digest are both
taken over. Reaching around an accepted module's own boundary into its private
helpers would bind this file to bytes that boundary does not promise, and
editing that accepted file is not this Work's authority. So both are
implemented here, under the same rules, and held equal to their owners by
conformance cases in `tests/manager/test_integration_worker.py` rather than by
this paragraph. The gap is recorded in the dossier's FINDING.
"""

import json
import os
import stat
import subprocess

import integration_contract as contract


# -- what a launch must be for this workload --------------------------------

# THE ROLE THIS RUNTIME IS LAUNCHED UNDER, by equality. A container that is
# some other kind of worker is not one this file may drive a target from.
INTEGRATION_ROLE = "integrator"

# THE `/1` FORM AND NOTHING ELSE. `/2` selects the ordinary file-exchange
# transport, and this workload runs ONCE from durable files: it consumes no
# command frames and writes no worker terminal. A launch claiming that
# transport is refused rather than silently ignored, because a manager
# expecting an exchange and a container that will never speak one is exactly
# the silent disagreement the versioned document replaced.
LAUNCH_SCHEMA = "baton.worker-launch/1"
LAUNCH_MEMBERS = ("schema", "session", "contract", "role")


# -- the two closed vocabularies --------------------------------------------
#
# THEY ARE THIS MODULE'S OWN WORDS. Nothing the provider writes reaches a
# manager-visible document through them: a reason here is chosen by this file
# from these tuples, and the provider's prose has no member anywhere.

# PUBLISHED ONLY WHEN NO PROVIDER WAS STARTED. Every one of these is decided
# before `invoke_provider`, so a refusal carries the positive fact that this
# runtime performed no work at all -- which is what makes `refused` honest.
REFUSAL_REASONS = ("launch-uncorrelated", "assignment-uncorrelated",
                   "bundle-unreadable", "bundle-uncorrelated",
                   "instructions-uncorrelated", "evidence-uncorrelated",
                   "scope-unauthorized", "review-unaccepted",
                   "target-unavailable", "target-drift", "target-unwritable",
                   "path-unsupported", "result-published", "workload-failed")

# AND EVERYTHING AFTER THE PROVIDER HAD WRITABLE WORK, short of a verified
# complete import.
HOLD_REASONS = ("provider-failed", "report-missing", "report-unreadable",
                "report-foreign", "report-outside-scope", "import-incomplete",
                "repository-mutated", "provider-uncertain", "result-oversized")


# -- bounds ------------------------------------------------------------------

# THE BUNDLE IS TWO LEVELS DEEP AND NO MORE: the root, then `evidence` and
# `blobs`. A deeper tree is not a bundle this producer publishes, and walking
# one would be walking material nobody composed.
MAX_BUNDLE_DEPTH = 1

# THE WHOLE COMPOSED PROMPT. The instructions are bounded at 64 KiB by the
# contract and the rendered table is bounded by its 251 rows, so this is a
# ceiling on the sum rather than a new limit on either.
MAX_PROMPT_BYTES = 512 * 1024

# HOW MUCH OF THIS MODULE'S OWN PROSE TRAVELS in one refusal or hold.
MAX_OBSERVED = 400

# HOW MANY PATHS A REFUSAL OR HOLD NAMES. The complete table is in the bundle
# the manager composed; a detail document is an account, not a copy of it.
MAX_NAMED_PATHS = 16

# CANONICAL JSON'S TWO FROZEN LIMITS, in the owner's own values.
MAX_MEMBERS = 512
MAX_DEPTH = 64
MAX_SAFE_INTEGER = 2 ** 53 - 1

# THE VERSION-CONTROL READ'S CEILING. A `rev-parse` that has not answered in a
# minute is not going to.
REVISION_SECONDS = 60

# THE TWO REVIEWED REGULAR FILE MODES, in the filesystem's spelling. The
# version-control mode in the reviewed table is what selects between them; a
# bundle file's own custody mode never does.
FILE_MODES = {"100644": 0o644, "100755": 0o755}

_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


class WorkloadRefusal(Exception):
    """Something no result can be composed for, with no operand bytes in it."""


class _Refused(Exception):
    """A pre-provider refusal, on its way to becoming a `refused` result."""

    def __init__(self, reason, observed, detail=None):
        super().__init__(observed)
        self.reason = reason
        self.observed = observed
        self.detail = detail or {}


class _Held(Exception):
    """An ending after the provider had writable work."""

    def __init__(self, reason, observed, detail=None):
        super().__init__(observed)
        self.reason = reason
        self.observed = observed
        self.detail = detail or {}


def _refuse(reason, observed, detail=None):
    raise _Refused(reason, observed, detail)


def _hold(reason, observed, detail=None):
    raise _Held(reason, observed, detail)


# -- canonical JSON, restricted to what this file digests --------------------


def canonical_text(value):
    """RFC 8785 canonical text, for the documents this workload digests.

    THE SAME RULES AS `baton_v12.contracts.canonical`, which this worker
    cannot import, and a conformance case holds the two spellings equal over
    real documents rather than over this comment. Exact built-in types tested
    with `type(x) is T`: a `dict` subclass, an `IntEnum` or a `bool` where an
    integer is meant would each serialize as something other than what the
    caller meant, and a digest over "something else" is the one failure a
    canonical form exists to prevent.
    """
    return _canonical(value, 0)


def _canonical(value, depth):
    if depth > MAX_DEPTH:
        raise WorkloadRefusal("this document nests deeper than the frozen "
                              "canonical limit")
    if value is None:
        return "null"
    kind = type(value)
    # `bool` BEFORE `int`, because `True` is an `int` in Python and `1` is not
    # `true`; the other order gives two documents one digest.
    if kind is bool:
        return "true" if value else "false"
    if kind is int:
        if value < 0 or value > MAX_SAFE_INTEGER:
            raise WorkloadRefusal("canonical JSON here admits only "
                                  "non-negative JSON-safe integers")
        return str(value)
    if kind is str:
        _no_lone_surrogate(value)
        return json.dumps(value, ensure_ascii=False)
    if kind is list:
        if len(value) > MAX_MEMBERS:
            raise WorkloadRefusal("this array is above the frozen canonical "
                                  "limit")
        return "[" + ",".join(_canonical(one, depth + 1)
                              for one in value) + "]"
    if kind is dict:
        if len(value) > MAX_MEMBERS:
            raise WorkloadRefusal("this object is above the frozen canonical "
                                  "limit")
        names = []
        for name in value:
            if type(name) is not str:
                raise WorkloadRefusal("canonical JSON names members with text")
            _no_lone_surrogate(name)
            names.append(name)
        # THE UTF-16 CODE-UNIT ORDER, big-endian so comparing bytes compares
        # code units. Sorting by code POINT differs above the BMP.
        names.sort(key=lambda one: one.encode("utf-16-be"))
        return "{" + ",".join(f"{json.dumps(one, ensure_ascii=False)}:"
                              f"{_canonical(value[one], depth + 1)}"
                              for one in names) + "}"
    raise WorkloadRefusal("canonical JSON has no representation for this "
                          "value; a digest over something else is not a "
                          "digest over the document")


def _no_lone_surrogate(text):
    try:
        text.encode("utf-16-be")
    except UnicodeEncodeError:
        raise WorkloadRefusal("this text carries a lone UTF-16 surrogate; "
                              "invalid Unicode fails rather than being "
                              "repaired into a digestible document") from None


def canonical_digest(value):
    """The identity every digest in this campaign is taken as."""
    from hashlib import sha256

    return "sha256:" + sha256(
        canonical_text(value).encode("utf-8")).hexdigest()


# -- bounded, no-follow reading ----------------------------------------------


def _read_file(holder, name, *, limit, what):
    """One regular file's whole bytes, proved on the descriptor that reads it.

    NO-FOLLOW so a link at a fixed name is refused rather than resolved,
    NON-BLOCKING so a FIFO cannot stop this program inside `open` before the
    type is asked, REGULAR proved by `fstat` on the descriptor a racing
    replacement cannot have changed, and BOUNDED -- an oversized input refuses
    and is never truncated.
    """
    try:
        handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=holder)
    except OSError as failed:
        raise WorkloadRefusal(f"{what} is not readable as an ordinary file "
                              f"({failed.errno})") from None
    try:
        held = os.fstat(handle)
        if not stat.S_ISREG(held.st_mode):
            raise WorkloadRefusal(f"{what} is not a regular file")
        if held.st_size > limit:
            raise WorkloadRefusal(f"{what} is {held.st_size} bytes, above the "
                                  f"bound of {limit}")
        os.set_blocking(handle, True)
        payload = b""
        while True:
            chunk = os.read(handle, 65536)
            if not chunk:
                break
            payload += chunk
            if len(payload) > limit:
                raise WorkloadRefusal(f"{what} grew past the bound of {limit}")
        if len(payload) != held.st_size:
            raise WorkloadRefusal(f"{what} changed size while it was read")
        return payload
    finally:
        os.close(handle)


# -- the bundle's own measured identity --------------------------------------


def measure_bundle(root):
    """Walk the mounted bundle and recompute the producer's whole manifest.

    WHY THIS IS MEASURED AND NOT READ. `bundle_digest` is the canonical digest
    of one entry per EMITTED FILE, and the envelope cannot carry it -- a
    document cannot state a digest taken over itself. So the only way to hold
    the provider's reported bundle identity to anything is to compute the same
    manifest from the same bytes, which is also the only check that notices a
    file the envelope never named sitting in the mounted bundle.

    EVERY COMPONENT IS PROVED. The root is the contract's own descriptor-bound
    walk, each child is opened relative to its parent's descriptor, and
    anything that is neither a directory nor a regular file refuses the whole
    measurement rather than being skipped -- a skipped entry is a file in the
    bundle that no digest covers.
    """
    held = contract.open_bundle_root(root)
    manifest = []
    try:
        _measured(held, "", 0, manifest)
    finally:
        os.close(held)
    if len(manifest) < contract.FIXED_FILES:
        raise WorkloadRefusal(f"this bundle holds {len(manifest)} files and "
                              f"every bundle has at least "
                              f"{contract.FIXED_FILES}")
    manifest.sort(key=lambda one: one["path"].encode("utf-8"))
    return {"manifest": manifest, "bundle_digest": canonical_digest(manifest)}


def _measured(holder, prefix, depth, manifest):
    for name in sorted(os.listdir(holder)):
        if name in (".", "..") or "/" in name:
            raise WorkloadRefusal("a bundle component is one ordinary name")
        place = name if not prefix else f"{prefix}/{name}"
        held = os.stat(name, dir_fd=holder, follow_symlinks=False)
        if stat.S_ISDIR(held.st_mode):
            if depth >= MAX_BUNDLE_DEPTH:
                raise WorkloadRefusal(f"the bundle nests deeper at {place!r} "
                                      f"than a published bundle does")
            try:
                child = os.open(name, _DIRECTORY, dir_fd=holder)
            except OSError as failed:
                raise WorkloadRefusal(f"{place!r} is not a directory this "
                                      f"reader can open without following a "
                                      f"link ({failed.errno})") from None
            try:
                _measured(child, place, depth + 1, manifest)
            finally:
                os.close(child)
            continue
        if not stat.S_ISREG(held.st_mode):
            raise WorkloadRefusal(f"{place!r} is neither a directory nor a "
                                  f"regular file; a bundle carries no link, "
                                  f"device or FIFO")
        payload = _read_file(holder, name, limit=contract.MAX_BLOB_BYTES,
                             what=f"bundle file {place!r}")
        manifest.append({"path": place, "bytes": len(payload),
                         "digest": "sha256:" + contract.sha256_hex(payload)})
        if len(manifest) > contract.MAX_BUNDLE_FILES:
            raise WorkloadRefusal(f"this bundle holds more than the bound of "
                                  f"{contract.MAX_BUNDLE_FILES} files")


# -- the target, read and never written --------------------------------------


def revision_argv(target_root):
    """The one read-only version-control query this workload makes.

    `--no-optional-locks` because a read must not write an index refresh into
    a tree this workload is about to prove unchanged. Nothing here clones,
    fetches, checks out, resets, stages or commits, and there is no fallback
    that would.
    """
    return ["git", "--no-optional-locks", "-C", target_root, "rev-parse",
            "HEAD"]


def revision_environment():
    """A composed environment, so no ambient configuration decides this read.

    The two configuration files are pointed at `/dev/null` so no `include`,
    alias or filter an operator happens to have set can change what a revision
    query answers or make it touch the network.
    """
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0"}


def git_revision(target_root, *, run=None):
    """The target's current revision, through one bounded READ-ONLY query."""
    runner = subprocess.run if run is None else run
    try:
        done = runner(revision_argv(target_root), capture_output=True,
                      timeout=REVISION_SECONDS, env=revision_environment())
    except (OSError, subprocess.SubprocessError):
        _refuse("target-unavailable",
                "the target's current revision could not be read")
    if done.returncode != 0:
        _refuse("target-unavailable",
                "the target is not a version-controlled tree this runtime can "
                "read a revision from")
    # THE PROGRAM'S OWN OUTPUT AND NOT ITS PROSE: one line, and it has to look
    # like a revision before it is compared with one.
    found = (done.stdout or b"").decode("utf-8", "replace").strip()
    if not found or len(found) > 200 or any(one not in "0123456789abcdef"
                                            for one in found):
        _refuse("target-unavailable",
                "the target's revision reader did not answer one revision")
    return found


def _target_state(holder, path, *, limit):
    """What is at one scheduled path right now: kind, digest, mode, writable.

    NOTHING IS RESOLVED THROUGH A LINK. Every component is opened relative to
    its parent's descriptor with `O_NOFOLLOW`, so a link planted anywhere on
    the way to a scheduled path cannot make this reader answer about some
    other file.
    """
    parts = path.split("/")
    opened = []
    try:
        for name in parts[:-1]:
            try:
                holder = os.open(name, _DIRECTORY, dir_fd=holder)
            except OSError:
                # THE DEEPEST EXISTING ANCESTOR IS WHAT THE QUESTION IS ABOUT.
                # An addition whose directory does not exist yet is ordinary --
                # the provider creates it -- so what has to be already writable
                # is the last directory that DOES exist. An entry of another
                # type at that name is not a missing directory.
                try:
                    os.stat(name, dir_fd=holder, follow_symlinks=False)
                except OSError:
                    return {"kind": "absent", "digest": None, "mode": None,
                            "writable": _owner_writable(os.fstat(holder))}
                return {"kind": "other", "digest": None, "mode": None,
                        "writable": False}
            opened.append(holder)
        try:
            held = os.stat(parts[-1], dir_fd=holder, follow_symlinks=False)
        except OSError:
            return {"kind": "absent", "digest": None, "mode": None,
                    "writable": _owner_writable(os.fstat(holder))}
        if not stat.S_ISREG(held.st_mode):
            return {"kind": "other", "digest": None, "mode": None,
                    "writable": False}
        if held.st_size > limit:
            return {"kind": "oversized", "digest": None,
                    "mode": stat.S_IMODE(held.st_mode), "writable": False}
        payload = _read_file(holder, parts[-1], limit=limit,
                             what="a scheduled target path")
        return {"kind": "regular", "digest": contract.sha256_hex(payload),
                "mode": stat.S_IMODE(held.st_mode),
                "writable": _owner_writable(held)
                            and _owner_writable(os.fstat(holder))}
    finally:
        for one in opened:
            os.close(one)


def _owner_writable(held):
    """ALREADY owner-writable, and never made so.

    Repository policy is explicit that a read-only target refuses the whole
    import for exact operator repair: no `chmod`, no `install`, no privileged
    replacement and no ACL workaround. So this asks the question and the
    caller's only move on a `False` is to refuse.
    """
    return held.st_uid == os.geteuid() and bool(held.st_mode & stat.S_IWUSR)


def _repository_witness(holder):
    """One BOUNDED account of the target's version-control metadata.

    NOT A PROOF OF ANYTHING ABOUT THE WHOLE REPOSITORY, and it is named a
    witness for that reason. `.git` is the one place this candidate may never
    touch -- `check_bundle_path` refuses a path that reaches into it -- so its
    own identity, and that of `index` and `HEAD`, are recorded before the
    provider and compared after. A change is `held`; it is never repaired and
    never explained away.
    """
    found = {}
    try:
        held = os.stat(".git", dir_fd=holder, follow_symlinks=False)
    except OSError:
        return found
    found[".git"] = (stat.S_IFMT(held.st_mode), held.st_ino)
    if not stat.S_ISDIR(held.st_mode):
        return found
    try:
        inside = os.open(".git", _DIRECTORY, dir_fd=holder)
    except OSError:
        return found
    try:
        for name in ("index", "HEAD"):
            try:
                one = os.stat(name, dir_fd=inside, follow_symlinks=False)
            except OSError:
                continue
            found[f".git/{name}"] = (stat.S_IFMT(one.st_mode), one.st_ino,
                                     one.st_size, one.st_mtime_ns)
    finally:
        os.close(inside)
    return found


# -- correlation -------------------------------------------------------------


def checked_launch(document):
    """This container's own launch document, held to what a bundle can name."""
    if type(document) is not dict or set(document) != set(LAUNCH_MEMBERS):
        _refuse("launch-uncorrelated",
                "the launch document is not the four-member "
                f"{LAUNCH_SCHEMA} form this workload runs under")
    if document["schema"] != LAUNCH_SCHEMA:
        _refuse("launch-uncorrelated",
                "this workload runs once from durable files and consumes no "
                "exchange transport; a launch from another generation is not "
                "one to read the recognised parts out of")
    if document["role"] != INTEGRATION_ROLE:
        _refuse("launch-uncorrelated",
                f"this container was launched under another role and only "
                f"{INTEGRATION_ROLE!r} integrates a canonical target")
    for name in LAUNCH_MEMBERS:
        if type(document[name]) is not str or not document[name]:
            _refuse("launch-uncorrelated",
                    f"the launch document's {name} is not bounded non-empty "
                    f"text")
    return document


def checked_assignment(document):
    """The assignment this runtime was launched under, re-owned before use.

    Raised rather than refused: without a whole assignment there is no attempt,
    lease, target, entry or fence to compose a result document ABOUT, so this
    is the case the entry hands back to the Worker Manager rather than one it
    can answer in the delivery.
    """
    if type(document) is not dict \
            or set(document) != set(contract.ASSIGNMENT_MEMBERS):
        raise WorkloadRefusal("an integration assignment carries exactly its "
                              "closed members")
    if document["schema"] != contract.ASSIGNMENT_SCHEMA:
        raise WorkloadRefusal("the integration assignment declares another "
                              "schema")
    for name in ("canonical_target_id", "entry_id", "lease_id", "attempt_id",
                 "integrator_participant", "profile_kind",
                 "instructions_digest"):
        if type(document[name]) is not str or not document[name]:
            raise WorkloadRefusal(f"an assignment's {name} is durable text")
    for name in ("fence", "profile_version"):
        value = document[name]
        if type(value) is bool or type(value) is not int or value < 1:
            raise WorkloadRefusal(f"an assignment's {name} counts from one")
    if document["target_access"] != "writable":
        raise WorkloadRefusal("an integration runtime that cannot write the "
                              "target cannot perform the integration it was "
                              "launched for")
    return document


def _correlated(taken, measured, assignment, launch):
    """Every account that has to agree before a provider is started."""
    envelope = taken["envelope"]
    if envelope["assignment_digest"] != canonical_digest(assignment):
        _refuse("assignment-uncorrelated",
                "this bundle was composed for another assignment; an "
                "internally consistent bundle has proved nothing about being "
                "this runtime's")
    expected = envelope["launch"]
    if expected["schema"] != launch["schema"] \
            or expected["role"] != launch["role"] \
            or expected["digest"] != canonical_digest(launch):
        _refuse("launch-uncorrelated",
                "this bundle names another launch than the one this container "
                "was started with")
    instructions = taken["instructions"]
    if "sha256:" + contract.sha256_hex(instructions) \
            != assignment["instructions_digest"]:
        _refuse("instructions-uncorrelated",
                "the instruction bytes in this bundle are not the ones the "
                "assignment's profile names")
    try:
        instructions.decode("utf-8")
    except UnicodeDecodeError:
        _refuse("instructions-uncorrelated",
                "the profile's instruction bytes are not valid UTF-8")

    eligibility = envelope["eligibility"]
    checkpoint = envelope["checkpoint"]
    evidence = taken["evidence"]
    _correlated_evidence(envelope, eligibility, checkpoint, evidence)
    _authorized_scope(envelope["paths"], evidence)
    if canonical_digest([one["path"] for one in envelope["paths"]]) \
            != eligibility["path_set_digest"]:
        _refuse("bundle-uncorrelated",
                "the envelope's path table is not the accepted path set")
    if eligibility["path_set_digest"] \
            != checkpoint["evidence"]["path_set_digest"]:
        _refuse("evidence-uncorrelated",
                "the eligibility account and the accepted checkpoint name "
                "different path sets")
    return {"envelope": envelope, "eligibility": eligibility,
            "checkpoint": checkpoint, "instructions": instructions,
            "bundle_digest": measured["bundle_digest"]}


def _correlated_evidence(envelope, eligibility, checkpoint, evidence):
    """The seven projections, bound to the account they are evidence FOR.

    A PROJECTION IS EVIDENCE ONLY WHEN IT IS ABOUT THIS CANDIDATE. Each of
    these is one producer's answer, and a bundle that carried an unrelated but
    internally valid document for one of them would read back cleanly and be
    about something else entirely.
    """
    for name, member, expected in (
            ("checkpoint.json", "checkpoint_id", checkpoint["checkpoint_id"]),
            ("checkpoint.json", "path_set_digest",
             checkpoint["evidence"]["path_set_digest"]),
            ("review.json", "verdict_id", checkpoint["verdict_id"]),
            ("job.json", "work_id", eligibility["work_id"]),
            ("job.json", "scope_digest", eligibility["scope_digest"]),
            ("tests.json", "checkpoint_id", checkpoint["checkpoint_id"])):
        document = evidence.get(name)
        if type(document) is not dict or member not in document:
            _refuse("evidence-uncorrelated",
                    f"evidence {name} records no {member}")
        if document[member] != expected:
            _refuse("evidence-uncorrelated",
                    f"evidence {name} names a {member} the accepted account "
                    f"does not")
    if checkpoint["checkpoint_id"] != eligibility["checkpoint_id"] \
            or checkpoint["verdict_id"] != eligibility["verdict_id"] \
            or checkpoint["checkpoint_digest"] \
            != eligibility["checkpoint_digest"]:
        _refuse("evidence-uncorrelated",
                "the envelope's checkpoint and its eligibility account "
                "disagree about which checkpoint was accepted")
    if [one["name"] for one in envelope["evidence"]] \
            != list(contract.EVIDENCE_DOCUMENTS):
        _refuse("evidence-uncorrelated",
                "the envelope does not name the closed evidence set")


def is_test_path(path):
    """Whether a target path is an EXISTING TEST for scope purposes.

    DELIBERATELY OVER-INCLUSIVE, and the direction matters: a predicate that
    called too much a test can only demand that the accepted Job's scope name
    it, and one that called too little a test would let an existing test be
    modified on no authority at all. Being wrong the safe way costs a refusal
    the operator can see; being wrong the other way is the exact failure the
    scope check exists for.
    """
    parts = path.split("/")
    if any(one in ("test", "tests", "testing") for one in parts):
        return True
    name = parts[-1]
    return name.startswith("test_") or name.startswith("test-") \
        or name.endswith("_test.py") or name.endswith("-test.py") \
        or name.startswith("Test")


def _within_scope(path, scope):
    """Whether one changed path is inside the accepted Job's scheduled scope.

    A SCOPE ENTRY IS A PATH PREFIX, because a real accepted Job's scope names
    directories -- `v12/python/tests/job_manager` -- rather than every file
    beneath them. Matching on exact equality alone would refuse every genuine
    scheduled change and, worse, would teach a reader that the check is
    stricter than it is. The boundary is a COMPONENT boundary: a scope of
    `tests/a` admits `tests/a/one.py` and does not admit `tests/abc.py`.
    """
    return any(path == one or path.startswith(one.rstrip("/") + "/")
               for one in scope)


def _authorized_scope(rows, evidence):
    """The scheduled test scope and the frozen review, evaluated SEMANTICALLY.

    AN INTERNALLY CONSISTENT BUNDLE IS NOT BLANKET AUTHORITY. Repository policy
    is explicit that adding tests needs no case-specific confirmation and that
    changing an EXISTING test's assertions or expected behaviour does -- an
    accepted Work or plan that scheduled that exact change within a bounded
    scope. So an `edit` or a `delete` of a path this build reads as a test is
    admitted only when the accepted Job's own test scope names it, and a
    generic approval receipt is not consulted at all, because it does not
    answer this question.

    MISSING OR CONTRADICTORY EVIDENCE REFUSES BEFORE THE PROVIDER IS CALLED,
    rather than being read as permission by absence.
    """
    review = evidence.get("review.json")
    if type(review) is not dict or "disposition" not in review:
        _refuse("review-unaccepted",
                "this bundle carries no frozen independent review disposition")
    if review["disposition"] != "accepted":
        _refuse("review-unaccepted",
                "the frozen independent review did not accept this candidate")
    job = evidence.get("job.json")
    if type(job) is not dict or type(job.get("test_scope")) is not list:
        _refuse("scope-unauthorized",
                "this bundle carries no accepted Job test scope; absent and "
                "empty are not one claim")
    scope = []
    for one in job["test_scope"]:
        if type(one) is not str or not one:
            _refuse("scope-unauthorized",
                    "the accepted Job's test scope names a path that is not "
                    "durable text")
        scope.append(one)
    unauthorized = sorted(row["path"] for row in rows
                          if row["operation"] in ("edit", "delete")
                          and is_test_path(row["path"])
                          and not _within_scope(row["path"], scope))
    if unauthorized:
        _refuse("scope-unauthorized",
                "this candidate changes an existing test the accepted Job's "
                "scheduled scope does not name",
                {"paths": unauthorized[:MAX_NAMED_PATHS],
                 "path_count": len(unauthorized)})


# -- the whole preflight, before any target is touched -----------------------


def preflight(holder, rows):
    """Every scheduled path proved BEFORE any of them is written.

    THE WHOLE SET OR NONE OF IT. A row-at-a-time check that wrote as it went
    would let a later invalid member follow an earlier successful write, and a
    partially imported candidate is not the reviewed one. So this answers the
    complete before-state and refuses the whole proposal on the first row it
    cannot account for.

    WHAT IT PROVES PER ROW: the relative-path shape; the declared base side's
    exact bytes and mode where one exists; the absence of a path an `add`
    would create; that the entry is a regular file rather than a link, a
    directory or a device; and that the runtime ALREADY has owner write on
    what it must change. It never establishes that access itself.
    """
    before = {}
    for row in rows:
        path = contract.check_bundle_path(row["path"], "a scheduled path")
        base, candidate = row["base"], row["candidate"]
        declared = [one["bytes"] for one in (base, candidate)
                    if one is not None]
        state = _target_state(holder, path, limit=max(max(declared), 1))
        before[path] = state
        if row["operation"] == "add":
            if state["kind"] != "absent":
                _refuse("target-drift",
                        "an addition names a path the target already carries",
                        {"paths": [path]})
            if not state["writable"]:
                _refuse("target-unwritable",
                        "the directory an addition lands in is not already "
                        "writable by this runtime, and this workload never "
                        "makes a target writable",
                        {"paths": [path]})
            continue
        if state["kind"] == "other":
            _refuse("path-unsupported",
                    "a scheduled path is not a regular file in the target; no "
                    "link, directory or special file is imported by this "
                    "slice", {"paths": [path]})
        if state["kind"] != "regular" or state["digest"] != base["blob"]:
            _refuse("target-drift",
                    "a scheduled path does not carry the exact reviewed base "
                    "bytes", {"paths": [path]})
        if state["mode"] != FILE_MODES[base["mode"]]:
            _refuse("target-drift",
                    "a scheduled path is not at the reviewed base mode; a "
                    "mode this candidate did not review is not one it imports "
                    "over", {"paths": [path]})
        if not state["writable"]:
            _refuse("target-unwritable",
                    "a scheduled path or its directory is not already "
                    "writable by this runtime; a read-only target is repaired "
                    "by an operator and never here", {"paths": [path]})
    return before


# -- the provider's instruction document -------------------------------------


def compose_prompt(*, instructions, bundle_root, target_root, report_place,
                   assignment, assignment_digest, bundle_digest, rows):
    """The one prompt this workload hands a provider.

    EVERY PATH IS RENDERED FROM THE VALIDATED TABLE and nothing else. The
    provider never names a path this document then repeats, which is what
    keeps a report from being able to widen its own scope by describing one.

    NO CREDENTIAL AND NO SESSION APPEARS HERE. The launch document carries this
    container's live control-API session and is deliberately not part of the
    prompt; the bundle carries the launch's DIGEST for exactly that reason.
    """
    lines = [instructions.decode("utf-8").rstrip("\n"), "",
             "-- this runtime's exact operands --", "",
             f"The approved evidence bundle is mounted read-only at "
             f"{bundle_root}.",
             f"Its measured identity is {bundle_digest}.",
             f"The assignment it answers is {assignment_digest}.",
             f"The candidate blobs are under {bundle_root}/"
             f"{contract.BLOB_DIRECTORY}/, named by the content address each "
             f"path row declares.",
             f"The target is {target_root} and it is the only tree you may "
             f"change.",
             f"Write your bounded {contract.REPORT_SCHEMA} report to "
             f"{report_place} and write no other file outside the target.",
             f"This integration is attempt {assignment['attempt_id']} of "
             f"target {assignment['canonical_target_id']}, entry "
             f"{assignment['entry_id']}, fence {assignment['fence']}.", "",
             "Import exactly these paths and no others:"]
    for row in rows:
        base = row["base"]
        candidate = row["candidate"]
        lines.append(
            f"  {row['operation']} {row['path']}"
            + (f" from base {base['blob']} mode {base['mode']}"
               if base else "")
            + (f" to candidate {candidate['blob']} mode {candidate['mode']}"
               if candidate else ""))
    lines += ["",
              "Do not change version-control state in any way. Do not repair "
              "permissions, redesign the candidate, resolve a conflict, or "
              "touch a path outside this table. If any of that is required, "
              "stop and report a refusal with its code."]
    prompt = "\n".join(lines) + "\n"
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        _refuse("bundle-uncorrelated",
                "the composed instruction document is above this workload's "
                "bound")
    return prompt


# -- the provider's report ---------------------------------------------------


def _report(place, expected, rows):
    """The bounded report, read from private scratch and held to this turn."""
    scratch, name = os.path.dirname(place), os.path.basename(place)
    try:
        holder = os.open(scratch, _DIRECTORY)
    except OSError:
        _hold("report-missing", "this runtime's private scratch is gone")
    try:
        try:
            os.stat(name, dir_fd=holder, follow_symlinks=False)
        except OSError:
            _hold("report-missing",
                  "the provider turn ended without a report; an exit status "
                  "alone says nothing about what a provider did")
        try:
            payload = _read_file(holder, name,
                                 limit=contract.MAX_REPORT_BYTES,
                                 what="the provider report")
        except WorkloadRefusal as failed:
            _hold("report-unreadable", str(failed))
    finally:
        os.close(holder)
    try:
        taken = contract.check_report(payload)
    except contract.BundleRefusal as failed:
        _hold("report-unreadable", str(failed))
    if taken["assignment_digest"] != expected["assignment_digest"] \
            or taken["bundle_digest"] != expected["bundle_digest"]:
        _hold("report-foreign",
              "the report names another assignment or another bundle than the "
              "one this runtime measured")
    scheduled = {row["path"] for row in rows}
    outside = sorted(set(taken["paths"]) - scheduled)
    if outside:
        _hold("report-outside-scope",
              "the provider reports changing a path the accepted table does "
              "not name",
              {"paths": outside[:MAX_NAMED_PATHS], "path_count": len(outside)})
    return taken


# -- the ending --------------------------------------------------------------


def _verified(holder, rows):
    """This module's OWN read-back of every scheduled path.

    THE PROVIDER'S REPORT IS A CLAIM AND THIS IS THE MEASUREMENT. `integrated`
    is composed from what is actually on disk -- exact candidate bytes and the
    reviewed mode for every edit and add, and absence for every delete -- and
    never from a report agreeing with itself.
    """
    imported, missed, states = [], [], {}
    for row in rows:
        path = row["path"]
        candidate = row["candidate"]
        state = _target_state(holder, path,
                              limit=max(candidate["bytes"] if candidate else 1,
                                        1))
        states[path] = state
        if candidate is None:
            (imported if state["kind"] == "absent" else missed).append(path)
            continue
        if state["kind"] == "regular" \
                and state["digest"] == candidate["blob"] \
                and state["mode"] == FILE_MODES[candidate["mode"]]:
            imported.append(path)
        else:
            missed.append(path)
    return sorted(imported), sorted(missed), states


def _moved(before, after):
    """Which scheduled paths are not where the preflight recorded them.

    THE PREFLIGHT'S BEFORE-STATE IS EVIDENCE AND NOT BOOKKEEPING. An operator
    reading a hold needs to know whether an incomplete import left the target
    untouched or half-moved, and "the same paths that are not the candidate"
    and "the paths that moved" are two different numbers.
    """
    def summary(state):
        return (state["kind"], state["digest"], state["mode"])

    return sorted(path for path, state in after.items()
                  if path in before and summary(state) != summary(before[path]))


def _result(assignment, outcome, detail):
    return {"schema": contract.RESULT_SCHEMA,
            "attempt_id": assignment["attempt_id"],
            "lease_id": assignment["lease_id"],
            "canonical_target_id": assignment["canonical_target_id"],
            "entry_id": assignment["entry_id"],
            "fence": assignment["fence"],
            "outcome": outcome, "detail": detail}


def _account(reason, observed, detail, vocabulary):
    if reason not in vocabulary:
        raise WorkloadRefusal(f"{reason!r} is not one of this workload's "
                              f"closed words")
    return {"reason": reason,
            "detail": dict(detail or {}, observed=observed[:MAX_OBSERVED])}


def refused_result(assignment, reason, observed, detail=None):
    """The ending of a turn that started NO provider, which is what makes it
    a refusal rather than an uncertainty."""
    return _result(assignment, "refused",
                   _account(reason, observed, detail, REFUSAL_REASONS))


def held_result(assignment, reason, observed, detail=None):
    """The conservative ending. A failure after writable work was available is
    held, and unchanged final bytes do not turn it into a refusal: restoration
    of bytes is not absence of mutation."""
    return _result(assignment, "held",
                   _account(reason, observed, detail, HOLD_REASONS))


def integrate(*, agent, assignment, launch, bundle_root, target_root, scratch,
              result_root=None, revision=None):
    """One integration, from an accepted bundle to one composed result.

    THE ORDER IS THE CONTRACT: correlate, preflight the whole path set, take
    exactly one provider turn, read the target back independently, and only
    then compose an outcome. Nothing writes into the target from this file at
    any point.
    """
    fixed = checked_assignment(assignment)
    started = False
    try:
        checked_launch(launch)
        try:
            taken = contract.read_bundle(bundle_root)
        except contract.BundleRefusal as failed:
            _refuse("bundle-unreadable", str(failed))
        try:
            measured = measure_bundle(bundle_root)
        except (WorkloadRefusal, OSError) as failed:
            _refuse("bundle-unreadable", str(failed))
        correlated = _correlated(taken, measured, fixed, launch)
        rows = correlated["envelope"]["paths"]

        try:
            holder = os.open(target_root, _DIRECTORY)
        except OSError:
            _refuse("target-unavailable",
                    "the canonical target is not a directory this runtime can "
                    "open without following a link")
        try:
            found = (git_revision if revision is None else revision)(
                target_root)
            if found != correlated["eligibility"]["expected_target_revision"]:
                _refuse("target-drift",
                        "the target is not at the revision this candidate was "
                        "reviewed against")
            try:
                before = preflight(holder, rows)
            except WorkloadRefusal as failed:
                # A SCHEDULED PATH THIS RUNTIME CANNOT EVEN READ is a refusal
                # like any other preflight answer, and not a case with no
                # result: nothing has been written, and saying so in the
                # delivery is more use to an operator than an exit status.
                _refuse("target-unavailable", str(failed))
            witness = _repository_witness(holder)
            report_place = _prepared_report(scratch)
            if result_root is not None \
                    and existing_result(result_root) is not None:
                # THE WINDOW BETWEEN CORRELATION AND THE TURN, closed on the
                # same rule the entry opens with: one integration answers once
                # and a terminal result never earns a second provider turn.
                _refuse("result-published",
                        "this attempt already carries a terminal result")
            prompt = compose_prompt(
                instructions=correlated["instructions"],
                bundle_root=bundle_root, target_root=target_root,
                report_place=report_place, assignment=fixed,
                assignment_digest=correlated["envelope"]["assignment_digest"],
                bundle_digest=correlated["bundle_digest"], rows=rows)

            started = True
            answer = agent.invoke_provider(prompt=prompt, room=target_root)
            if type(answer) is not dict or "ok" not in answer:
                _hold("provider-uncertain",
                      "the provider turn did not answer this deployment's "
                      "closed document")
            if not answer["ok"]:
                # A FAILED TURN IS NOT A REFUSAL. The provider held writable
                # work, and its own word for why it stopped is this module's
                # closed vocabulary rather than the provider's prose.
                _hold("provider-failed",
                      f"the provider turn did not complete "
                      f"({answer.get('failure_reason')})")
            report = _report(report_place,
                             {"assignment_digest":
                                  correlated["envelope"]["assignment_digest"],
                              "bundle_digest": correlated["bundle_digest"]},
                             rows)
            if _repository_witness(holder) != witness:
                _hold("repository-mutated",
                      "the target's version-control metadata moved during "
                      "this turn, and no candidate imports it")
            imported, missed, after = _verified(holder, rows)
            if missed:
                _hold("import-incomplete",
                      "the target is not the approved candidate at every "
                      "scheduled path after a turn that had writable work",
                      {"paths": missed[:MAX_NAMED_PATHS],
                       "imported": len(imported), "missing": len(missed),
                       "moved": len(_moved(before, after))})
            if report["outcome"] != "imported":
                _hold("provider-uncertain",
                      "every scheduled path carries the approved candidate "
                      "and the provider's own report does not claim an import")
            return _integrated_result(fixed, imported, report["verification"])
        finally:
            os.close(holder)
    except _Refused as failed:
        return refused_result(fixed, failed.reason, failed.observed,
                              failed.detail)
    except _Held as failed:
        return held_result(fixed, failed.reason, failed.observed,
                           failed.detail)
    except Exception as failed:
        # AN UNEXPECTED FAILURE IS CLASSIFIED BY WHERE IT HAPPENED, which is
        # the same conservative rule stated once more: before the turn nothing
        # of this runtime's had written anything, and after it nobody can say
        # that. The type name travels and the message does not, because an
        # exception string is how a credential reaches a manager document.
        where = f"an unexpected {type(failed).__name__}"
        if started:
            return held_result(fixed, "provider-uncertain",
                               f"{where} ended this turn after the provider "
                               f"had writable work")
        return refused_result(fixed, "workload-failed",
                              f"{where} ended this turn before any provider "
                              f"was started")


def _integrated_result(assignment, imported, verification):
    """`integrated`, or a hold when its own account will not fit the delivery.

    THE RESULT IS BOUNDED AT 64 KiB by the manager's reader, and a candidate
    with enough long paths can compose an account above it. Truncating the
    imported-path list would publish a smaller claim than what happened, so
    the ending becomes a hold that says exactly that and carries the path
    count and the accepted path-set identity instead. The target IS imported
    in that case; what the deployment lost is the ability to record it in one
    bounded document, and that is an operator's to see rather than this file's
    to round off.
    """
    document = _result(assignment, "integrated",
                       {"imported_paths": imported,
                        "verification": verification})
    if len(result_payload(document)) <= contract.MAX_RESULT_BYTES:
        return document
    return held_result(assignment, "result-oversized",
                       "every scheduled path carries the approved candidate "
                       "and the account of it is above the delivery's bound",
                       {"path_count": len(imported),
                        "path_set_digest": canonical_digest(imported)})


def _prepared_report(scratch):
    """The private directory the provider's report is written into.

    CREATED EXCLUSIVELY AND NEVER REPAIRED. An existing name is not this
    runtime's merely because it has the desired spelling, and chmodding one
    can follow a link somebody else planted.
    """
    if type(scratch) is not str or not scratch or not os.path.isabs(scratch):
        raise WorkloadRefusal("a report is written into one absolute private "
                              "directory")
    made = os.path.join(scratch, "integration-report")
    try:
        os.mkdir(made, 0o700)
    except FileExistsError:
        raise WorkloadRefusal(f"the private report directory {made} already "
                              f"exists; predictable runtime paths are created "
                              f"exclusively and never repaired") from None
    os.chmod(made, 0o700)
    return os.path.join(made, contract.REPORT_DOCUMENT)


# -- the delivery ------------------------------------------------------------


def result_payload(document):
    """The exact bytes the manager reads back, in its own spelling."""
    return json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def existing_result(result_root):
    """The terminal result this attempt already carries, or `None`.

    ONE INTEGRATION ANSWERS ONCE. A published result means the provider turn
    already happened, whatever this incarnation believes; running a second one
    over a terminal answer is how an attempt integrates twice.
    """
    try:
        holder = os.open(result_root, _DIRECTORY)
    except OSError:
        return None
    try:
        try:
            os.stat(contract.RESULT_DOCUMENT, dir_fd=holder,
                    follow_symlinks=False)
        except OSError:
            return None
        return _read_file(holder, contract.RESULT_DOCUMENT,
                          limit=contract.MAX_RESULT_BYTES,
                          what="the published integration result")
    finally:
        os.close(holder)


def publish_result(result_root, document):
    """Publish the one result ATOMICALLY, or lose the race and say so.

    THE STEPS ARE THE MANAGER'S OWN, deliberately rather than by imitation: a
    UNIQUE no-follow staging name so a process that died mid-publication wedges
    nothing; the complete bounded write, every byte of it, because `os.write`
    may write fewer and report nothing; the mode established on the DESCRIPTOR
    rather than requested through a umask; `fsync` on the file; NO-CLOBBER
    `link` into the fixed name, which fails closed on a racing winner instead
    of replacing it; `fsync` on the directory; and removal of the staging name
    whichever way this ends. A manager reading this namespace mid-publication
    sees a staging name, which is not the fixed name and is therefore not a
    result.
    """
    payload = result_payload(document)
    if len(payload) > contract.MAX_RESULT_BYTES:
        raise WorkloadRefusal(f"this integration result is {len(payload)} "
                              f"bytes and the manager reads at most "
                              f"{contract.MAX_RESULT_BYTES}")
    holder = os.open(result_root, _DIRECTORY)
    try:
        staged = f".{contract.RESULT_DOCUMENT}.{os.getpid()}." \
                 f"{os.urandom(8).hex()}.publishing"
        handle = os.open(staged,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o000, dir_fd=holder)
        try:
            try:
                written = 0
                while written < len(payload):
                    step = os.write(handle, payload[written:])
                    if type(step) is not int or step <= 0:
                        raise WorkloadRefusal(
                            f"writing the integration result made no progress "
                            f"after {written} of {len(payload)} bytes")
                    written += step
                os.fchmod(handle, 0o444)
                os.fsync(handle)
            finally:
                os.close(handle)
            try:
                os.link(staged, contract.RESULT_DOCUMENT, src_dir_fd=holder,
                        dst_dir_fd=holder)
                published = True
            except FileExistsError:
                published = False
            os.fsync(holder)
        finally:
            try:
                os.unlink(staged, dir_fd=holder)
            except OSError:
                pass
    finally:
        os.close(holder)
    return {"published": published,
            "place": os.path.join(result_root, contract.RESULT_DOCUMENT)}
