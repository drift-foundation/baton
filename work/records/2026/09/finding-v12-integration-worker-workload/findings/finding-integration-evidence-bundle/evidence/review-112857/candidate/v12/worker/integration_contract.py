"""The immutable integration evidence bundle, as the WORKER sees it.

W112630, `work/records/2026/09/finding-v12-integration-worker-workload/
findings/finding-integration-evidence-bundle/`.

STANDARD LIBRARY ONLY, AND THAT IS THE POINT OF THE FILE. The image this
module ships in copies worker modules and no manager, Authority or store
package, so anything this file imported would have to be copied too --
and a packaging mistake would then be discovered by a container that
cannot start rather than by a test. `json`, `os` and `stat` are the whole
import list, and one case asserts that.

WHAT IT OWNS. The fixed `/input/source` layout, the closed
`baton.integration-input/1` envelope, the bounded no-follow readers that turn
those bytes into documents, the provider report's closed shape, and the outer
assignment/result names this worker is launched under. What it does NOT own is
the workload: nothing here imports a target, invokes a provider, edits a path
or decides an outcome. W110935 owns that, and it consumes this.

WHY THE OUTER NAMES ARE REPEATED HERE. `baton_v12.integration.runtime` is the
manager's owner of the assignment and result contracts and stays the owner; a
worker in a container cannot import it, so the members are spelled a second
time and `tests/tools/test_integration_bundle.py` holds the two spellings
equal. A conformance test is the mechanism this campaign already uses for the
same problem, and it fails the moment either side moves.

EVERY BOUND IS FINITE AND CHECKED BEFORE ALLOCATION. A bundle is material this
worker did not create: it is read with `O_NOFOLLOW` at every component, proved
to be a regular file by `fstat` on the descriptor that will be read, and
refused when it is larger than its declared size rather than truncated. An
oversized input is a refusal and never a prefix.
"""

import json
import os
import stat

__all__ = ["ASSIGNMENT_DOCUMENT", "ASSIGNMENT_MEMBERS", "ASSIGNMENT_SCHEMA",
           "ASSIGNMENT_TARGET", "BLOB_DIRECTORY", "BUNDLE_SCHEMA",
           "BUNDLE_TARGET", "BundleRefusal", "CHECKPOINT_MEMBERS",
           "ELIGIBILITY_MEMBERS", "ENVELOPE_DOCUMENT", "ENVELOPE_MEMBERS",
           "EVIDENCE_DIRECTORY", "EVIDENCE_DOCUMENTS", "EVIDENCE_MEMBERS",
           "FILE_MEMBERS", "HOLD_MEMBERS", "HOLD_REASONS", "HOLD_SCHEMA",
           "INSTRUCTIONS_DOCUMENT", "LAUNCH_MEMBERS", "MAX_BLOB_BYTES",
           "MAX_ENVELOPE_BYTES", "MAX_EVIDENCE_BYTES",
           "MAX_INSTRUCTION_BYTES", "MAX_PATHS", "MAX_REPORT_BYTES",
           "MAX_RESULT_BYTES", "MODES", "OPERATIONS", "PATH_MEMBERS",
           "REPORT_CODES", "REPORT_DOCUMENT", "REPORT_MEMBERS",
           "REPORT_OUTCOMES", "REPORT_PHASES", "REPORT_SCHEMA",
           "RESULT_DOCUMENT", "RESULT_MEMBERS", "RESULT_OUTCOMES",
           "RESULT_SCHEMA", "RESULT_TARGET", "SIDE_MEMBERS",
           "bundle_blob", "check_bundle_path", "check_report",
           "read_assignment", "read_bundle", "sha256_hex"]


# -- the fixed bundle layout ------------------------------------------------

BUNDLE_SCHEMA = "baton.integration-input/1"

# WHERE THE BUNDLE IS BOUND, and it is the accepted read-only nominated source
# rather than a fourth integration namespace. W110934 ruled that `/input/source`
# is the one deliberate nesting exception this campaign carries; a new fixed
# target for the same material would be a second answer to a settled question.
BUNDLE_TARGET = "/input/source"

ENVELOPE_DOCUMENT = "integration.json"
INSTRUCTIONS_DOCUMENT = "instructions.txt"
EVIDENCE_DIRECTORY = "evidence"
BLOB_DIRECTORY = "blobs"

# THE ENVELOPE'S CLOSED MEMBER LIST. Each one has exactly one named producer,
# recorded beside it in the producer, and none of them is a place a caller can
# put something extra: an envelope with a member this tuple does not name is
# refused rather than ignored, because a bundle is the only thing the runtime
# reads and an ignored member is a channel.
ENVELOPE_MEMBERS = ("schema", "assignment_digest", "launch", "eligibility",
                    "checkpoint", "evidence", "instructions", "paths")

# WHAT THE BUNDLE SAYS ABOUT THE LAUNCH, AND WHAT IT DELIBERATELY OMITS. The
# launch document carries the worker's SESSION, which is a live control-API
# credential; copying it into a bundle that is mounted read-only for the whole
# runtime would widen that secret's blast radius for no gain. The bundle
# carries the launch's DIGEST instead, so a workload can prove the launch it
# was given is the launch this bundle was made for without the bundle ever
# holding the token.
LAUNCH_MEMBERS = ("schema", "role", "digest")

# EXACTLY WHAT `integration_checkpoint` ANSWERS. Re-spelled rather than
# summarized: W112029 shipped a consumer that read a top-level `head` because
# it described the owner's answer instead of copying it, and the objects live
# inside `evidence`.
CHECKPOINT_MEMBERS = ("line_id", "checkpoint_id", "verdict_id",
                      "checkpoint_digest", "evidence")
CHECKPOINT_EVIDENCE_MEMBERS = ("profile", "base", "head", "tree", "paths",
                               "path_set_digest", "reference")

# EXACTLY WHAT `admission.resolved_account` ANSWERS -- fifteen members, in that
# owner's own spellings.
ELIGIBILITY_MEMBERS = ("authority_uuid", "work_id", "assignment_generation",
                       "line_id", "checkpoint_id", "verdict_id",
                       "checkpoint_digest", "proposal_id", "candidate_digest",
                       "result_id", "result_digest", "profile_kind",
                       "expected_target_revision", "path_set_digest",
                       "scope_digest")

# THE EVIDENCE PROJECTIONS, WITH THEIR PRODUCERS. The set is CLOSED and every
# name is present: a bundle missing one of these is missing an account the
# workload's instructions require the model to evaluate, and "absent" and
# "empty" are not the same claim.
#
#   job.json        the accepted Job row and its test scope (Job store)
#   checkpoint.json `checkpoint_of`, the frozen checkpoint row
#   review.json     `verdict_of` plus `review_of`, the frozen independent review
#   proposal.json   the Authority's published proposal
#   receipts.json   the Authority's verification, review and approval receipts
#   result.json     `frozen_output_of` plus the retained result manifest
#   tests.json      `driver.ordinary_test_evidence`, the producer's observation
EVIDENCE_DOCUMENTS = ("checkpoint.json", "job.json", "proposal.json",
                      "receipts.json", "result.json", "review.json",
                      "tests.json")

EVIDENCE_MEMBERS = ("name", "digest", "bytes")
FILE_MEMBERS = ("digest", "bytes")

# ONE PATH ROW. `base` and `candidate` are the two sides, and exactly one of
# them is null for an add or a delete.
PATH_MEMBERS = ("path", "operation", "base", "candidate")

# ONE SIDE OF ONE ROW. `object` is the VERSION CONTROL name of the content and
# `blob` is the bundle's own content address; they are separate members because
# their producers compute different identities and a single interchangeable
# digest member is how two identities become one bug.
SIDE_MEMBERS = ("object", "blob", "bytes", "mode")

OPERATIONS = ("add", "delete", "edit")

# THE TWO REGULAR FILE MODES THIS SLICE ADMITS. A symlink (120000), a submodule
# (160000) and a directory (040000) refuse the WHOLE proposal rather than
# dropping a row: a partially imported candidate is not the reviewed one.
MODES = ("100644", "100755")


# -- the finite bounds ------------------------------------------------------
#
# ADOPTED AT THE VALUES THE PARENT FINDING PROPOSED, with one addition and one
# MEASURED CORRECTION. Nothing here was relaxed.
#
# `MAX_EVIDENCE_BYTES` is new: the parent bounded the envelope, the
# instructions, the paths, the blobs and the report and left the evidence
# projections unbounded, and an unbounded document is an unbounded allocation
# whatever the rest of the table says.
#
# `MAX_PATHS` is 512 AND NOT THE PROPOSED 4096, because 4096 is a bound this
# build cannot honour. Every digest in this campaign is taken over
# `contracts.canonical`, whose frozen `MAX_MEMBERS` is 512: an envelope with a
# 4096-row path table could not be canonicalized, so it could not be digested,
# so it could never be published or read back. Declaring a ceiling the
# serializer refuses below would be a bound that reads as generous and refuses
# at a number nobody wrote down.

MAX_ENVELOPE_BYTES = 1024 * 1024
MAX_INSTRUCTION_BYTES = 64 * 1024
MAX_PATHS = 512
MAX_BLOB_BYTES = 64 * 1024 * 1024
MAX_EVIDENCE_BYTES = 1024 * 1024
MAX_REPORT_BYTES = 64 * 1024

# THE OUTER RESULT'S BOUND, which is `runtime.MAX_DELIVERY_BYTES`. Held equal
# by conformance rather than by this comment.
MAX_RESULT_BYTES = 65536


# -- the outer namespaces, mirrored from the manager's owner ----------------

ASSIGNMENT_TARGET = "/run/baton/integration/assignment"
RESULT_TARGET = "/run/baton/integration/result"
ASSIGNMENT_DOCUMENT = "assignment.json"
RESULT_DOCUMENT = "result.json"

ASSIGNMENT_SCHEMA = "baton.v12.integration-assignment/1"
ASSIGNMENT_MEMBERS = ("schema", "canonical_target_id", "entry_id", "lease_id",
                      "fence", "attempt_id", "integrator_participant",
                      "profile_kind", "profile_version", "instructions_digest",
                      "target_access")

RESULT_SCHEMA = "baton.v12.integration-result/1"
RESULT_MEMBERS = ("schema", "attempt_id", "lease_id", "canonical_target_id",
                  "entry_id", "fence", "outcome", "detail")
RESULT_OUTCOMES = ("integrated", "refused", "held")

HOLD_SCHEMA = "baton.v12.integration-hold/1"
HOLD_MEMBERS = ("schema", "reason", "observed", "detail")
HOLD_REASONS = ("runtime-interrupted", "runtime-ambiguous",
                "result-unreadable", "result-foreign")


# -- the provider's own bounded report --------------------------------------
#
# IT LIVES IN PRIVATE SCRATCH AND IS NOT THE RESULT. The workload reads it,
# compares it with its OWN read-back of the target, and composes the outer
# result itself; a provider that authored the outer result would be authoring
# the manager's account of what happened. Arbitrary provider diagnostics have
# no member here, which is deliberate: an exception string is how a credential
# reaches a manager-visible document.

REPORT_DOCUMENT = "report.json"
REPORT_SCHEMA = "baton.integration-report/1"
REPORT_MEMBERS = ("schema", "assignment_digest", "bundle_digest", "outcome",
                  "phase", "paths", "verification", "code")
REPORT_OUTCOMES = ("imported", "refused", "held")

# WHERE THE PROVIDER SAYS IT STOPPED. The workload uses this to decide whether
# a complete pre-mutation refusal was positively established; it is evidence
# for that decision and never the decision.
REPORT_PHASES = ("preflight", "import", "verification")

# THE CLOSED REFUSAL AND HOLD CODES. `null` is the only value for a report that
# claims `imported`.
REPORT_CODES = ("scope-exceeded", "path-unsupported", "target-drift",
                "target-unwritable", "verification-failed",
                "partial-import", "provider-unable")


class BundleRefusal(Exception):
    """One refusal from this contract, with no operand bytes in its text."""


def _refuse(message):
    raise BundleRefusal(message)


def sha256_hex(payload):
    """The content address this bundle names blobs by."""
    from hashlib import sha256

    if type(payload) is not bytes:
        _refuse("a content address is computed over exact bytes")
    return sha256(payload).hexdigest()


def _hex64(value, what):
    if type(value) is not str or len(value) != 64 \
            or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is a lowercase 64-character hexadecimal digest")
    return value


def _count(value, what, ceiling):
    if type(value) is bool or type(value) is not int or value < 0:
        _refuse(f"{what} is an exact non-negative whole number")
    if value > ceiling:
        _refuse(f"{what} is above this contract's bound of {ceiling}")
    return value


def _text(value, what):
    if type(value) is not str or not value:
        _refuse(f"{what} is non-empty text")
    return value


def _pairs(pairs):
    """Reject duplicate JSON member names instead of keeping the last one."""
    held = {}
    for name, value in pairs:
        if name in held:
            _refuse("a bundle document repeats a member name; two values for "
                    "one member have no tie-break and this contract invents "
                    "none")
        held[name] = value
    return held


def _document(payload, what, members):
    try:
        taken = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs)
    except UnicodeDecodeError:
        _refuse(f"{what} is not valid UTF-8")
    except ValueError:
        _refuse(f"{what} is not one readable JSON document")
    if type(taken) is not dict:
        _refuse(f"{what} is a JSON object")
    if set(taken) != set(members):
        _refuse(f"{what} carries exactly its {len(members)} closed members")
    return taken


def check_bundle_path(value, what="a bundle path"):
    """One relative target path, with every escape refused.

    THE RULES ARE ABOUT THE SPELLING AND NOT ABOUT THE FILESYSTEM. Nothing is
    resolved here: this runs before a target exists and its job is to refuse a
    row that could never be a safe relative path whatever the target holds.
    """
    if type(value) is not str or not value:
        _refuse(f"{what} is non-empty text")
    if len(value) > 4096:
        _refuse(f"{what} is longer than this contract's 4096-byte bound")
    if value.startswith("/"):
        _refuse(f"{what} is relative to the target and not absolute")
    if "\x00" in value or "\\" in value:
        _refuse(f"{what} carries no NUL and no backslash")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        _refuse(f"{what} has one canonical spelling with no empty, current or "
                f"parent component")
    if parts[0] == ".git" or ".git" in parts:
        _refuse(f"{what} reaches into version-control metadata, which no "
                f"reviewed candidate imports")
    return value


# -- bounded, no-follow reading ---------------------------------------------


def _read_exact(place, *, limit, what):
    """Read one regular file with no symlink anywhere and a hard ceiling."""
    if type(place) is not str or not place:
        _refuse(f"{what} is named by a path")
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as failed:
        _refuse(f"{what} is not readable as an ordinary file ({failed.errno})")
    try:
        held = os.fstat(handle)
        # THE PROOF IS ON THE DESCRIPTOR THAT WILL BE READ. A `stat` by name
        # answers about whatever the name resolved to a moment ago; a FIFO
        # opened by name blocks forever, which is why `O_NONBLOCK` is on the
        # open and the regular-file question is asked afterwards.
        if not stat.S_ISREG(held.st_mode):
            _refuse(f"{what} is not a regular file")
        if held.st_size > limit:
            _refuse(f"{what} is {held.st_size} bytes, above this contract's "
                    f"bound of {limit}; an oversized input refuses and is "
                    f"never truncated")
        os.set_blocking(handle, True)
        payload = b""
        while True:
            chunk = os.read(handle, 65536)
            if not chunk:
                break
            payload += chunk
            if len(payload) > limit:
                _refuse(f"{what} grew past this contract's bound of {limit}")
        if len(payload) != held.st_size:
            _refuse(f"{what} changed size while it was being read")
        return payload
    finally:
        os.close(handle)


def _within(root, *parts):
    for part in parts:
        if type(part) is not str or not part or "/" in part or part in (".", ".."):
            _refuse("a bundle component is one ordinary name")
    return os.path.join(root, *parts)


def _file_reference(value, what):
    taken = value
    if type(taken) is not dict or set(taken) != set(FILE_MEMBERS):
        _refuse(f"{what} names its digest and its exact byte count")
    _hex64(taken["digest"], f"{what}'s digest")
    _count(taken["bytes"], f"{what}'s byte count", MAX_BLOB_BYTES)
    return taken


def _side(value, what):
    if value is None:
        return None
    if type(value) is not dict or set(value) != set(SIDE_MEMBERS):
        _refuse(f"{what} carries exactly {len(SIDE_MEMBERS)} closed members")
    _text(value["object"], f"{what}'s version-control object")
    _hex64(value["blob"], f"{what}'s content address")
    _count(value["bytes"], f"{what}'s byte count", MAX_BLOB_BYTES)
    if value["mode"] not in MODES:
        _refuse(f"{what} names a file mode this slice does not import; only "
                f"{' and '.join(MODES)} are regular reviewed files")
    return value


def _paths(rows):
    if type(rows) is not list:
        _refuse("the envelope's path table is an array")
    if len(rows) > MAX_PATHS:
        _refuse(f"the envelope carries more than the bound of {MAX_PATHS} "
                f"reviewed paths")
    seen = []
    total = 0
    for index, row in enumerate(rows):
        if type(row) is not dict or set(row) != set(PATH_MEMBERS):
            _refuse(f"path row {index} carries exactly "
                    f"{len(PATH_MEMBERS)} closed members")
        path = check_bundle_path(row["path"], f"path row {index}")
        if row["operation"] not in OPERATIONS:
            _refuse(f"path row {index} names an operation outside "
                    f"{OPERATIONS}")
        base = _side(row["base"], f"path row {index}'s base")
        candidate = _side(row["candidate"], f"path row {index}'s candidate")
        expected = {("add"): (False, True), ("delete"): (True, False),
                    ("edit"): (True, True)}[row["operation"]]
        if (base is not None, candidate is not None) != expected:
            _refuse(f"path row {index} is an {row['operation']} and its base "
                    f"and candidate sides do not match that claim")
        for side in (base, candidate):
            if side is not None:
                total += side["bytes"]
        seen.append(path)
    if total > MAX_BLOB_BYTES:
        _refuse(f"the envelope's path table declares {total} blob bytes, "
                f"above the bound of {MAX_BLOB_BYTES}")
    if seen != sorted(seen):
        _refuse("the envelope's path table is not sorted")
    if len(set(seen)) != len(seen):
        _refuse("the envelope's path table repeats a path")
    # ANCESTOR COLLISION, which duplication does not catch. Importing both
    # `a/b` and `a/b/c` asks one name to be a file and a directory.
    for path in seen:
        prefix = ""
        for part in path.split("/")[:-1]:
            prefix = part if not prefix else prefix + "/" + part
            if prefix in set(seen):
                _refuse(f"the envelope's path table names both {prefix!r} and "
                        f"a path beneath it")
    return rows


def read_bundle(root):
    """Every byte of one bundle, proved against its own envelope.

    WHAT THIS ANSWERS AND WHAT IT DOES NOT. It answers that the material at
    `root` is one internally consistent bundle: closed documents, bounded
    sizes, a sorted collision-free path table, and evidence and instruction
    bytes whose digests are the ones the envelope declares. It does NOT answer
    that the bundle is the one this runtime was assigned -- that is the
    workload's comparison against its own assignment and launch, and it needs
    the answers below to make it.

    THE BLOBS ARE NOT READ HERE. Sixty-four megabytes of candidate content has
    no business being resident because an envelope was parsed; `bundle_blob`
    reads one on demand, bounded by the byte count the table declared.
    """
    if type(root) is not str or not root or not os.path.isabs(root):
        _refuse("a bundle root is one absolute path")
    envelope = _document(
        _read_exact(_within(root, ENVELOPE_DOCUMENT),
                    limit=MAX_ENVELOPE_BYTES, what="the bundle envelope"),
        "the bundle envelope", ENVELOPE_MEMBERS)
    if envelope["schema"] != BUNDLE_SCHEMA:
        _refuse(f"the bundle envelope declares a schema this contract does "
                f"not implement; this build reads {BUNDLE_SCHEMA}")
    _text(envelope["assignment_digest"], "the envelope's assignment digest")

    launch = envelope["launch"]
    if type(launch) is not dict or set(launch) != set(LAUNCH_MEMBERS):
        _refuse("the envelope's expected launch carries its closed members")
    for member in LAUNCH_MEMBERS:
        _text(launch[member], f"the expected launch's {member}")

    eligibility = envelope["eligibility"]
    if type(eligibility) is not dict \
            or set(eligibility) != set(ELIGIBILITY_MEMBERS):
        _refuse("the envelope's eligibility account carries exactly the "
                "fifteen members its producer answers")

    checkpoint = envelope["checkpoint"]
    if type(checkpoint) is not dict \
            or set(checkpoint) != set(CHECKPOINT_MEMBERS):
        _refuse("the envelope's checkpoint carries exactly the members "
                "`integration_checkpoint` answers")
    evidence = checkpoint["evidence"]
    if type(evidence) is not dict \
            or set(evidence) != set(CHECKPOINT_EVIDENCE_MEMBERS):
        _refuse("the checkpoint's evidence carries its closed profile shape; "
                "the objects live in `evidence` and not beside it")

    instructions_reference = _file_reference(envelope["instructions"],
                                             "the envelope's instructions")
    if instructions_reference["bytes"] > MAX_INSTRUCTION_BYTES:
        _refuse(f"the instructions are above the bound of "
                f"{MAX_INSTRUCTION_BYTES} bytes")
    instructions = _read_exact(_within(root, INSTRUCTIONS_DOCUMENT),
                               limit=MAX_INSTRUCTION_BYTES,
                               what="the bundle instructions")
    if sha256_hex(instructions) != instructions_reference["digest"] \
            or len(instructions) != instructions_reference["bytes"]:
        _refuse("the instruction bytes are not the ones the envelope names")

    declared = envelope["evidence"]
    if type(declared) is not list \
            or [one.get("name") if type(one) is dict else None
                for one in declared] != list(EVIDENCE_DOCUMENTS):
        _refuse(f"the envelope names exactly the evidence projections "
                f"{EVIDENCE_DOCUMENTS} in that order")
    held = {}
    for reference in declared:
        if set(reference) != set(EVIDENCE_MEMBERS):
            _refuse("an evidence reference carries its closed members")
        name = reference["name"]
        _hex64(reference["digest"], f"evidence {name}'s digest")
        _count(reference["bytes"], f"evidence {name}'s byte count",
               MAX_EVIDENCE_BYTES)
        payload = _read_exact(_within(root, EVIDENCE_DIRECTORY, name),
                              limit=MAX_EVIDENCE_BYTES,
                              what=f"evidence {name}")
        if sha256_hex(payload) != reference["digest"] \
                or len(payload) != reference["bytes"]:
            _refuse(f"evidence {name} is not the document the envelope names")
        try:
            held[name] = json.loads(payload.decode("utf-8"),
                                    object_pairs_hook=_pairs)
        except UnicodeDecodeError:
            _refuse(f"evidence {name} is not valid UTF-8")
        except ValueError:
            _refuse(f"evidence {name} is not one readable JSON document")

    _paths(envelope["paths"])
    return {"root": root, "envelope": envelope, "instructions": instructions,
            "evidence": held}


def bundle_blob(root, side):
    """One content-addressed blob, bounded by the row that named it."""
    taken = _side(side, "a path row side")
    if taken is None:
        _refuse("a null side names no blob")
    payload = _read_exact(_within(root, BLOB_DIRECTORY, taken["blob"]),
                          limit=taken["bytes"],
                          what=f"blob {taken['blob'][:12]}")
    if len(payload) != taken["bytes"] or sha256_hex(payload) != taken["blob"]:
        _refuse("a bundle blob is not the content its own name addresses")
    return payload


# -- the outer namespaces ---------------------------------------------------


def read_assignment(root=ASSIGNMENT_TARGET):
    """The integration assignment this runtime was launched under."""
    taken = _document(
        _read_exact(_within(root, ASSIGNMENT_DOCUMENT),
                    limit=MAX_RESULT_BYTES, what="the integration assignment"),
        "the integration assignment", ASSIGNMENT_MEMBERS)
    if taken["schema"] != ASSIGNMENT_SCHEMA:
        _refuse("the integration assignment declares another schema")
    return taken


def check_report(payload):
    """The provider's bounded report, refused rather than interpreted.

    A REPORT IS A CLAIM. Everything here is shape: the workload compares the
    claim with its own read-back of the target and decides the outcome. An
    `imported` report over an unchanged target is still a held workload.
    """
    if type(payload) is not bytes:
        _refuse("a provider report is read as exact bytes")
    if len(payload) > MAX_REPORT_BYTES:
        _refuse(f"a provider report is bounded at {MAX_REPORT_BYTES} bytes")
    taken = _document(payload, "the provider report", REPORT_MEMBERS)
    if taken["schema"] != REPORT_SCHEMA:
        _refuse("the provider report declares another schema")
    for member in ("assignment_digest", "bundle_digest"):
        _text(taken[member], f"the report's {member}")
    if taken["outcome"] not in REPORT_OUTCOMES:
        _refuse(f"the report's outcome is one of {REPORT_OUTCOMES}")
    if taken["phase"] not in REPORT_PHASES:
        _refuse(f"the report's phase is one of {REPORT_PHASES}")
    paths = taken["paths"]
    if type(paths) is not list or len(paths) > MAX_PATHS:
        _refuse("the report's changed-path list is a bounded array")
    for one in paths:
        check_bundle_path(one, "a reported path")
    if paths != sorted(paths) or len(set(paths)) != len(paths):
        _refuse("the report's changed-path list is sorted and unique")
    verification = taken["verification"]
    if verification is not None:
        if type(verification) is not dict \
                or set(verification) != {"argv", "status"}:
            _refuse("the report's measured verification names its command and "
                    "its status")
        argv = verification["argv"]
        if type(argv) is not list or not argv \
                or any(type(one) is not str or not one for one in argv):
            _refuse("the reported verification names a non-empty command")
        status = verification["status"]
        if status is not None \
                and (type(status) is bool or type(status) is not int):
            _refuse("the reported verification status is a whole number or "
                    "null")
    code = taken["code"]
    if taken["outcome"] == "imported":
        if code is not None:
            _refuse("an imported report carries no refusal or hold code")
    elif code not in REPORT_CODES:
        _refuse(f"a {taken['outcome']} report names one of the closed codes "
                f"{REPORT_CODES}")
    return taken
