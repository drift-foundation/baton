"""Materialize one immutable integration evidence bundle from public owners.

W112630, `work/records/2026/09/finding-v12-integration-worker-workload/
findings/finding-integration-evidence-bundle/`.

WHAT WAS MISSING, AND IT IS NOT A VERIFIER. Every fact this module publishes
already has an accepted owner: `admission.resolved_account` re-resolves the
fifteen-member eligibility account, `driver.ordinary_test_evidence` answers what
the candidate's own producer observed, `review_cycles.integration_checkpoint`
and `checkpoint_of` answer the accepted checkpoint, `audit_checkpoint`
re-validates its retained reference without consulting a mutable HEAD, and the
Authority answers the proposal and its three receipts. What did not exist is
anything that turns those answers into BYTES a runtime with no manager, no
store and no Authority can read. This is that, and it decides nothing.

IT IS A DEPLOYMENT TOOL AND NOT A COMPONENT, which is why it lives here. It
owns the deployment's read-only version-control reading, and `baton_v12`'s
generic core stays free of Git exactly as W71918 arranged.

WHY THE RUNNER ANSWERS BYTES. `checkpoint_profiles` takes a runner whose
streams are TEXT, because every answer it needs -- an object name, a status,
a NUL-separated path list -- is text. Candidate content is not: a reviewed file
may hold any byte sequence, and a text runner would have already destroyed it
by the time this module saw it. So this module takes its own runner contract,
and the two are deliberately different rather than one loosened to cover both.

AND WHY IT TAKES A DESCRIPTOR RATHER THAN A PATHNAME:

    runner(argv, *, directory) -> {"returncode", "stdout", "stderr"}

`argv` carries no repository pathname, and `directory` is an open directory
descriptor the command MUST run with as its working directory -- a deployment
reaches that with `os.fchdir` on this descriptor in the child it forks. The
descriptor is valid for the duration of the call only: a runner must not retain
it, close it, or use it afterwards, and this module closes it when extraction
ends.

THAT IS THE BINDING, and the version this replaced was not one. `-C <path>`
makes the kernel resolve a NAME on every invocation, so a rename between two
reads changes what the second one reads; review 2026-09-07T19:51:54Z [P1]
demonstrated exactly that, with a substitution restored before the check that
was supposed to catch it. A descriptor names ONE inode for as long as it is
open, and the name is no longer part of the command. What this module still
cannot do is audit an injected runner: the contract above is what a deployment
owes, and the post-extraction owner re-resolution answers a different question
-- whether the manager's own account still agrees -- rather than standing in
for it.

WHAT IS READ AND WHAT IS NEVER RUN. `rev-parse --verify`, `ls-tree` and
`cat-file` against the revalidated retained checkpoint, with
`--no-optional-locks` so no read incidentally refreshes an index. There is no
clone, fetch, checkout, reset, update-ref, stage, commit or write of any kind,
and no second pack decoder: a missing object refuses with the exact producer
gap it found. `cat-file blob` is the read, deliberately, because it answers the
OBJECT and applies no smudge filter, no end-of-line conversion and no external
diff driver -- `git show :path` and `git archive` all do.

AND THE PUBLICATION IS ATOMIC OR ABSENT. The bundle is composed under a
staging name and renamed into place; the destination never exists in a partial
state, an existing destination refuses rather than being appended to, and every
emitted file is read-only before the rename that makes it reachable.
"""

import json
import os
import shutil
import stat

from baton_v12.checkpoint_profiles import GIT_PROFILE
from baton_v12.contracts import (ContractRefusal, check_relative_path, digest,
                                 digest_of_bytes)
from baton_v12.contracts.errors import name_value
from baton_v12.integration import admission, driver, runtime
from baton_v12.job_manager.submission import job_rows, stages_of
from baton_v12.source_profiles.checkout import check_declared_base
from baton_v12.worker_manager import boundaries, launch as launch_module
from baton_v12.worker_manager.attempts import assignment_of
from baton_v12.worker_manager.output import frozen_output_of
from baton_v12.worker_manager.review_cycles import (audit_checkpoint,
                                                    checkpoint_of,
                                                    integration_checkpoint,
                                                    line_of, review_of,
                                                    verdict_of, writer_of)
from baton_v12.worker_manager.manifests import load_manifest
from baton_v12.worker_manager.source_boundary import nominate_source

__all__ = ["BLOB_DIRECTORY", "BUNDLE_SCHEMA", "ENVELOPE_DOCUMENT",
           "ENVELOPE_MEMBERS", "EVIDENCE_DIRECTORY", "EVIDENCE_DOCUMENTS",
           "FIXED_FILES", "INSTRUCTIONS_DOCUMENT", "MAX_BLOB_BYTES",
           "MAX_BUNDLE_FILES", "MAX_ENVELOPE_BYTES",
           "MAX_EVIDENCE_BYTES", "MAX_INSTRUCTION_BYTES", "MAX_PATHS",
           "MODES", "OPERATIONS", "PATH_MEMBERS", "SIDE_MEMBERS",
           "compose_bundle", "content_vector", "entry_vector",
           "reviewed_path_table", "size_vector", "tree_vector"]


# THE LAYOUT, SPELLED A SECOND TIME AND HELD EQUAL BY CONFORMANCE.
# `v12/worker/integration_contract.py` is the owner a container reads; it
# imports no `baton_v12` package, so this module cannot import it and a manager
# that reached into the worker tree at runtime would be a packaging dependency
# nobody declared. `tests/tools/test_integration_bundle.py` asserts every
# constant below equals the worker contract's, which fails the moment either
# side moves.
BUNDLE_SCHEMA = "baton.integration-input/1"
ENVELOPE_DOCUMENT = "integration.json"
INSTRUCTIONS_DOCUMENT = "instructions.txt"
EVIDENCE_DIRECTORY = "evidence"
BLOB_DIRECTORY = "blobs"
ENVELOPE_MEMBERS = ("schema", "assignment_digest", "launch", "eligibility",
                    "checkpoint", "evidence", "instructions", "paths")
LAUNCH_MEMBERS = ("schema", "role", "digest")
EVIDENCE_DOCUMENTS = ("checkpoint.json", "job.json", "proposal.json",
                      "receipts.json", "result.json", "review.json",
                      "tests.json")
EVIDENCE_MEMBERS = ("name", "digest", "bytes")
PATH_MEMBERS = ("path", "operation", "base", "candidate")
SIDE_MEMBERS = ("object", "blob", "bytes", "mode")
OPERATIONS = ("add", "delete", "edit")
MODES = ("100644", "100755")

MAX_ENVELOPE_BYTES = 1024 * 1024
MAX_INSTRUCTION_BYTES = 64 * 1024
MAX_BLOB_BYTES = 64 * 1024 * 1024
MAX_EVIDENCE_BYTES = 1024 * 1024

# EVERY FILE ONE BUNDLE MAY HOLD, and `MAX_PATHS` DERIVED FROM IT rather than
# chosen. The publication manifest is one array with one entry per emitted
# file, and `contracts.canonical` freezes an array at 512 members -- so a
# bundle with more files than that cannot be measured, cannot be digested and
# must never be written. The first correction of the proposed 4096 stopped at
# 512 and got this wrong: review 2026-09-07T19:29:28Z [P1] published 513 files
# from 252 two-sided edits and only then refused, leaving a consumable
# destination and no digest. Nine files are fixed and an edit emits at most two
# blobs, so the ceiling is (512 - 9) // 2.
MAX_BUNDLE_FILES = 512
FIXED_FILES = 2 + len(EVIDENCE_DOCUMENTS)
MAX_PATHS = (MAX_BUNDLE_FILES - FIXED_FILES) // 2

# THE MODES THE PUBLICATION EMITS. A bundle is immutable material: every file
# is unwritable and every directory is unwritable before the rename that makes
# any of it reachable, so "read-only" is a property of the bytes rather than a
# promise about how the mount was composed.
BUNDLE_FILE = 0o444
BUNDLE_DIR = 0o555
STAGING_DIR = 0o700
STAGING_FILE = 0o600

_RECEIPT_KINDS = ("verification", "review", "approval")


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _drifted(message):
    """What changed under this producer between two of its own reads."""
    raise ContractRefusal("runtime-observation", "identity-mismatch", message)


def _custody(repository, line):
    """The line directory, nominated and compared with the manager's row."""
    held = nominate_source(repository)
    if (held.device, held.inode) != (line["line_device"], line["line_inode"]):
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the private line at {name_value(repository)} is not the "
            f"directory this manager recorded")
    return held


def _gap(message):
    """The producer gap a missing retained object is, and nothing else.

    A REFUSAL IS THE WHOLE ANSWER HERE. The parent finding is explicit that a
    missing object is not an invitation to fetch, unpack or decode: this
    deployment reads what its own line retained, and if that is gone an
    operator decides what happened to it.
    """
    raise ContractRefusal("refused", "precondition", message)


# -- the read-only version-control seam -------------------------------------


def _repository(place, what):
    if type(place) is not str or not place or not os.path.isabs(place):
        _refuse(f"{what} is an absolute non-empty path", category="integrity",
                code="path")
    if "\x00" in place or ".." in place.split("/") or ":" in place:
        _refuse(f"{what} is a canonical engine-safe path",
                category="integrity", code="path")
    if os.path.normpath(place) != place:
        _refuse(f"{what} has one canonical spelling", category="integrity",
                code="path")
    return place


# NO REPOSITORY OPERAND IN ANY VECTOR. Where the command runs is the
# descriptor's business, and a word that named the repository would put the
# pathname back into the one place this module removed it from.
_GIT = ["git", "--no-optional-locks"]


def tree_vector(revision):
    """The tree one reviewed revision names."""
    return _GIT + ["rev-parse", "--verify",
                   f"{check_declared_base(revision)}^{{tree}}"]


def entry_vector(tree, path):
    """One path's entry in one tree, or nothing at all."""
    return _GIT + ["ls-tree", "--full-tree", "-z", check_declared_base(tree),
                   "--", _relative(path)]


def size_vector(name):
    return _GIT + ["cat-file", "-s", check_declared_base(name)]


def content_vector(name):
    return _GIT + ["cat-file", "blob", check_declared_base(name)]


def _run(runner, directory, argv, what):
    """One bounded read, with the runner's answer proved before it is used."""
    answer = runner(tuple(argv), directory=directory)
    if type(answer) is not dict or set(answer) != {"returncode", "stdout",
                                                   "stderr"}:
        _refuse(f"the Git runner's {what} answer has the closed "
                f"command-result shape")
    if type(answer["returncode"]) is not int \
            or type(answer["returncode"]) is bool:
        _refuse(f"the Git runner's {what} status is an integer")
    for stream in ("stdout", "stderr"):
        if type(answer[stream]) is not bytes:
            _refuse(f"the Git runner's {what} streams are exact bytes; "
                    f"candidate content is not text and a decoded stream has "
                    f"already lost it")
    if answer["returncode"] != 0:
        detail = answer["stderr"].decode("utf-8", "replace").strip()[:240]
        _gap(f"the retained line cannot answer {what}" +
             (f": {detail}" if detail else ""))
    return answer["stdout"]


def _one_line(payload, what):
    text = payload.decode("utf-8", "strict").strip()
    if "\n" in text:
        _refuse(f"the Git runner answered more than one line for {what}")
    return text


# -- the reviewed path table ------------------------------------------------


def _relative(value, what="a reviewed path"):
    if type(value) is not str or not value:
        _refuse(f"{what} is non-empty text")
    if len(value) > 4096:
        _refuse(f"{what} is longer than the bound of 4096 bytes")
    if value.startswith("/"):
        _denied(f"{what} is relative to the target and not absolute")
    if "\x00" in value or "\\" in value:
        _refuse(f"{what} carries no NUL and no backslash")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        _denied(f"{what} has one canonical spelling with no empty, current or "
                f"parent component")
    if ".git" in parts:
        _denied(f"{what} reaches into version-control metadata, which no "
                f"reviewed candidate imports")
    return value


def _entry(runner, directory, tree, path, what):
    """One `ls-tree` row, or `None` when the tree does not carry the path."""
    payload = _run(runner, directory, entry_vector(tree, path),
                   f"the {what} entry for a reviewed path")
    if payload == b"":
        return None
    rows = [one for one in payload.split(b"\x00") if one]
    if len(rows) != 1:
        _refuse(f"the {what} tree answered {len(rows)} entries for one "
                f"reviewed path")
    try:
        head, named = rows[0].split(b"\t", 1)
        mode, kind, name = head.decode("utf-8").split(" ")
    except (ValueError, UnicodeDecodeError):
        _refuse(f"the {what} tree answered an entry this reader cannot parse")
    if named.decode("utf-8", "replace") != path:
        _refuse(f"the {what} tree answered an entry for another path")
    if kind != "blob" or mode not in MODES:
        _denied(f"reviewed path {name_value(path)} is a {kind} with mode "
                f"{mode} in the {what}; this slice imports regular files "
                f"only, and an unsupported kind refuses the whole proposal "
                f"rather than dropping a row")
    return {"object": check_declared_base(name), "mode": mode}


def _content(runner, directory, side, remaining, what):
    """One object's exact bytes, refused before allocation when oversized."""
    declared = _one_line(
        _run(runner, directory, size_vector(side["object"]),
             f"the size of the {what} object"), "an object size")
    if not declared.isdigit():
        _refuse(f"the Git runner answered a non-numeric size for the {what} "
                f"object")
    size = int(declared)
    if size > remaining:
        _refuse(f"the reviewed candidate needs more than the bound of "
                f"{MAX_BLOB_BYTES} blob bytes; an oversized proposal refuses "
                f"and is never truncated")
    payload = _run(runner, directory, content_vector(side["object"]),
                   f"the content of the {what} object")
    if len(payload) != size:
        _refuse(f"the {what} object's content is {len(payload)} bytes and it "
                f"declared {size}")
    return payload


def reviewed_path_table(runner, directory, evidence):
    """The sorted unique add/edit/delete table, read from retained objects.

    PUBLIC BECAUSE IT IS THE DEPLOYMENT'S OWN VERSION-CONTROL READING, and
    hiding it inside the composition would put the one part of this module that
    talks to Git behind a door no reviewer can open on its own.

    THE EVIDENCE IS THE AUTHORITY ON WHICH PATHS EXIST. This never asks Git for
    a diff and never discovers a path: it takes the accepted checkpoint's own
    sorted path set and asks, for each of those paths, what the two reviewed
    trees hold. A path the checkpoint names that neither tree carries is a
    producer disagreement and refuses -- inventing a side for it would be this
    module deciding what the reviewer approved.
    """
    if not callable(runner):
        boundaries.capability(runner, "the deployment's read-only Git runner")
    if type(directory) is not int or type(directory) is bool:
        _denied("the reviewed objects are read through an open directory "
                "descriptor; a pathname is resolved again on every use and "
                "that is the thing this boundary exists to stop")
    if not stat.S_ISDIR(os.fstat(directory).st_mode):
        _denied("the descriptor this producer reads through is a directory")
    if type(evidence) is not dict or set(evidence) != {
            "profile", "base", "head", "tree", "paths", "path_set_digest",
            "reference"}:
        _refuse("reviewed path evidence has the checkpoint profile's closed "
                "shape")
    if evidence["profile"] != GIT_PROFILE:
        _denied(f"this producer reads {name_value(GIT_PROFILE)} checkpoints "
                f"and the accepted evidence names "
                f"{name_value(evidence['profile'])}")
    paths = evidence["paths"]
    if type(paths) is not list:
        _refuse("a checkpoint's reviewed path set is an array")
    if len(paths) > MAX_PATHS:
        _refuse(f"the accepted checkpoint names {len(paths)} reviewed paths, "
                f"above the bound of {MAX_PATHS}")
    owned = [_relative(one) for one in paths]
    if owned != sorted(owned) or len(set(owned)) != len(owned):
        _refuse("a checkpoint's reviewed path set is sorted and unique")
    for path in owned:
        prefix = ""
        for part in path.split("/")[:-1]:
            prefix = part if not prefix else prefix + "/" + part
            if prefix in set(owned):
                _denied(f"the reviewed path set names both "
                        f"{name_value(prefix)} and a path beneath it; one name "
                        f"cannot be a file and a directory")
    if evidence["path_set_digest"] != digest(owned):
        _refuse("the accepted checkpoint's path-set digest is not the digest "
                "of its own paths")

    base_tree = _one_line(
        _run(runner, directory, tree_vector(evidence["base"]),
             "the reviewed base tree"), "a tree name")
    head_tree = _one_line(
        _run(runner, directory, tree_vector(evidence["head"]),
             "the reviewed candidate tree"), "a tree name")
    check_declared_base(base_tree)
    if check_declared_base(head_tree) != evidence["tree"]:
        _refuse(f"the retained candidate revision names tree "
                f"{name_value(head_tree)} and the accepted checkpoint recorded "
                f"{name_value(evidence['tree'])}")

    rows = []
    blobs = {}
    # WHAT HAS ALREADY BEEN READ, KEYED BY THE OBJECT NAME. Review
    # 2026-09-07T19:51:54Z [P2]: the remaining budget was charged BEFORE the
    # content address was known, so a blob two rows share was read a second
    # time and could refuse as oversized while adding nothing -- the producer
    # refusing input its own reader accepts. A version-control object name is
    # a content identity, so a second reference to one is answerable without a
    # second read and without a second charge.
    held = {}
    total = 0
    for path in owned:
        base = _entry(runner, directory, base_tree, path, "reviewed base")
        candidate = _entry(runner, directory, head_tree, path,
                           "reviewed candidate")
        if base is None and candidate is None:
            _gap(f"the accepted checkpoint names reviewed path "
                 f"{name_value(path)} and neither retained tree carries it")
        if base is not None and candidate is not None \
                and base["object"] == candidate["object"] \
                and base["mode"] == candidate["mode"]:
            _refuse(f"reviewed path {name_value(path)} is identical on both "
                    f"sides; a reviewed change that changes nothing is a "
                    f"disagreement between the checkpoint and its objects")
        row = {"path": path,
               "operation": ("edit" if base is not None and candidate is not None
                             else "add" if base is None else "delete")}
        for name, side in (("base", base), ("candidate", candidate)):
            if side is None:
                row[name] = None
                continue
            if side["object"] in held:
                address, measured = held[side["object"]]
            else:
                payload = _content(runner, directory, side,
                                   MAX_BLOB_BYTES - total, name)
                address = digest_of_bytes(payload).split(":", 1)[1]
                measured = len(payload)
                held[side["object"]] = (address, measured)
                if address not in blobs:
                    blobs[address] = payload
                    total += measured
                    if total > MAX_BLOB_BYTES:
                        _refuse(f"the reviewed candidate needs more than the "
                                f"bound of {MAX_BLOB_BYTES} blob bytes")
                elif blobs[address] != payload:
                    _refuse("two retained objects address one content and "
                            "hold different bytes")
            row[name] = {"object": side["object"], "blob": address,
                         "bytes": measured, "mode": side["mode"]}
        rows.append(row)
    return {"paths": rows, "blobs": blobs, "total_bytes": total}


# -- the accepted evidence --------------------------------------------------


def _authority_read(authority, name, what, *operands):
    boundaries.capability(getattr(authority, name, None),
                          f"the Authority's {name} read")
    return admission._authority_call(getattr(authority, name), what, *operands)


def _job_evidence(jobs, account):
    """The accepted Job that owns this Work's input, policy and test scope.

    SELECTED THE WAY ADMISSION SELECTS IT and then BOUND to what admission
    already resolved: the scope digest this composes must equal the one in the
    fifteen-member account, so a second reading of the Job store that drifted
    from the first refuses instead of quietly shipping a different scope.
    """
    matches = []
    for job in job_rows(jobs):
        for stage in stages_of(jobs, job["job_id"]):
            if stage["kind"] == "implementation" \
                    and stage["work_id"] == account["work_id"]:
                matches.append((job, stage))
    if len(matches) != 1:
        _refuse(f"Work {name_value(account['work_id'])} belongs to "
                f"{len(matches)} Job implementation stages; a bundle carries "
                f"one accepted test scope", category="refused",
                code="precondition")
    job, stage = matches[0]
    # THE ROW ANSWERS TEXT AND ADMISSION PARSES IT, so this parses it the same
    # way rather than assuming a list. The real Job store is what found this:
    # the first version of this reader treated the column as already-parsed and
    # refused every genuine Job, which is the same shape of mistake W112029
    # shipped against `integration_checkpoint` and the reason the real owners
    # drive this suite.
    try:
        parsed = json.loads(job["test_scope"])
    except (TypeError, ValueError):
        _refuse(f"Job {name_value(job['job_id'])} has no readable test scope")
    if type(parsed) is not list:
        _refuse("an accepted Job's test scope is an array")
    scope = [check_relative_path(one, "an accepted Job test-scope path")
             for one in parsed]
    if digest(scope) != account["scope_digest"]:
        _refuse("the Job store's test scope is not the scope this admission "
                "resolved; a bundle never carries a second scope")
    return {"job_id": job["job_id"], "submission_id": job["submission_id"],
            "input_digest": job["input_digest"],
            "policy_digest": job["policy_digest"],
            "test_scope": list(scope), "scope_digest": account["scope_digest"],
            "terminal_policy": job["terminal_policy"],
            "stage_id": stage["stage_id"], "work_id": stage["work_id"],
            "stage_kind": stage["kind"]}


def _accepted_evidence(manager, jobs, authority, *, line_id, proposal_id,
                       checkpoint_profile):
    """Every projection the bundle carries, from its own accepted owner.

    THIS IS THE RE-RESOLUTION, and it happens before one byte is written. The
    parent finding requires the producer to refuse disagreement rather than
    publish anything consumable, so the whole account is assembled, compared
    and only then materialized.
    """
    account = admission.resolved_account(manager, jobs, authority,
                                         line_id=line_id,
                                         proposal_id=proposal_id)
    tests = driver.ordinary_test_evidence(manager, authority, line_id=line_id,
                                          proposal_id=proposal_id)
    accepted = integration_checkpoint(manager, line_id)
    if accepted is None:
        _refuse(f"development line {name_value(line_id)} lost its accepted "
                f"integration checkpoint between two reads",
                category="refused", code="precondition")
    line = line_of(manager, line_id)
    checkpoint = checkpoint_of(manager, accepted["checkpoint_id"])
    writer = writer_of(manager, checkpoint["writer_id"])
    frozen = frozen_output_of(manager, writer["runtime_attempt_id"])
    if frozen is None:
        _refuse(f"the checkpoint writer "
                f"{name_value(writer['runtime_attempt_id'])} has no frozen "
                f"result", category="refused", code="precondition")
    result = load_manifest(manager, frozen["manifest_digest"], "resultManifest")

    # THE RETAINED REFERENCE, RE-VALIDATED WITHOUT A MUTABLE HEAD. This is the
    # one check that asks the version control whether the objects the manager
    # recorded are still the ones its own retained reference names.
    audited = audit_checkpoint(manager, accepted["checkpoint_id"],
                               checkpoint_profile)
    if audited != checkpoint["evidence"] \
            or audited != accepted["evidence"]:
        _refuse("the audited checkpoint evidence and the recorded checkpoint "
                "disagree")

    verdict = verdict_of(manager, accepted["verdict_id"])
    attachment = review_of(manager, verdict["attachment_id"])
    proposal = admission._proposal(authority, proposal_id)
    receipts = {kind: admission._receipt(authority, proposal, kind)
                for kind in _RECEIPT_KINDS}
    job = _job_evidence(jobs, account)

    return {
        "account": account,
        "line": line,
        "checkpoint": accepted,
        "documents": {
            "checkpoint.json": {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "line_id": checkpoint["line_id"],
                "writer_id": checkpoint["writer_id"],
                "state": checkpoint["state"],
                "revision": checkpoint["revision"],
                "profile_name": checkpoint["profile_name"],
                "checkpoint_digest": checkpoint["checkpoint_digest"],
                "path_set_digest": checkpoint["path_set_digest"],
                "reference_name": checkpoint["reference_name"],
                "evidence": checkpoint["evidence"]},
            "job.json": job,
            "proposal.json": proposal,
            "receipts.json": receipts,
            "result.json": {
                "result_id": frozen["result_id"],
                "disposition": frozen["disposition"],
                "manifest_digest": frozen["manifest_digest"],
                "assignment_ref": assignment_of(
                    manager, writer["runtime_attempt_id"]),
                "input_manifest_digest": result["input_manifest_digest"],
                "policy_digest": result["policy_digest"],
                "completion_manifest_digest":
                    result["completion_manifest_digest"]},
            "review.json": {
                "verdict_id": verdict["verdict_id"],
                "attachment_id": verdict["attachment_id"],
                "disposition": verdict["disposition"],
                "reviewer_participant": attachment["reviewer_participant"],
                "reviewer_principal": attachment["reviewer_principal"],
                "reviewer_worker_id": attachment["reviewer_worker_id"],
                "assignment_generation": attachment["assignment_generation"],
                "state": attachment["state"],
                "review_result": verdict["review_result"],
                "review_result_digest": verdict["review_result_digest"],
                "recorded_at": verdict["recorded_at"]},
            "tests.json": tests}}


def _checked_operands(*, integration_profile, assignment, launch,
                      instructions):
    """The three trusted deployment operands, proved against the account."""
    profile = boundaries.document(integration_profile,
                                  "the configured integration profile",
                                  required=runtime.PROFILE_MEMBERS)
    if profile["schema"] != runtime.PROFILE_SCHEMA:
        _refuse("the configured integration profile declares another schema")
    fixed = boundaries.document(assignment, "the composed integration "
                                "assignment",
                                required=runtime.ASSIGNMENT_MEMBERS)
    if fixed["schema"] != runtime.ASSIGNMENT_SCHEMA:
        _refuse("the composed integration assignment declares another schema")
    for member in ("profile_kind", "profile_version", "instructions_digest"):
        if fixed[member] != profile[member]:
            _refuse(f"the composed assignment's {member} is not the "
                    f"configured profile's; one runtime is launched under one "
                    f"profile")
    # AND THE TWO `profile_kind`s ARE DELIBERATELY NOT COMPARED. The
    # assignment's is the INTEGRATION profile's -- how this deployment
    # integrates one canonical target -- and the account's is the CHECKPOINT
    # profile's, which is how the candidate was produced. They are two
    # vocabularies owned by two components, and this finding's own rule is that
    # identities with different producers do not get collapsed into one member
    # merely because they are often spelled alike. Both travel in the envelope,
    # each under its own producer's name.
    held = boundaries.document(launch, "the expected worker launch",
                               required=launch_module.members_for(launch))
    if held["schema"] not in launch_module.TRANSPORTS:
        _refuse("the expected worker launch declares another schema")
    boundaries.text(held["role"], "the expected launch's role")
    if type(instructions) is not bytes:
        _refuse("the profile's instruction bytes are exact bytes")
    if len(instructions) > MAX_INSTRUCTION_BYTES:
        _refuse(f"the profile's instructions are {len(instructions)} bytes, "
                f"above the bound of {MAX_INSTRUCTION_BYTES}")
    if digest_of_bytes(instructions) != profile["instructions_digest"]:
        _refuse("the supplied instruction bytes are not the ones the "
                "configured profile's digest names")
    return {"assignment_digest": runtime.assignment_digest(fixed),
            "launch": {"schema": held["schema"], "role": held["role"],
                       "digest": digest(held)}}


# -- atomic publication -----------------------------------------------------


def _destination(place):
    if type(place) is not str or not place or not os.path.isabs(place):
        _refuse("a bundle destination is one absolute path",
                category="integrity", code="path")
    if os.path.normpath(place) != place or place.endswith("/"):
        _refuse("a bundle destination has one canonical spelling",
                category="integrity", code="path")
    parent = os.path.dirname(place)
    if os.path.realpath(parent) != parent:
        _refuse(f"the bundle destination's parent {name_value(parent)} is "
                f"reached through a link; a publication root is canonical",
                category="integrity", code="path")
    if not os.path.isdir(parent):
        _refuse(f"the bundle destination's parent {name_value(parent)} is not "
                f"a directory this deployment owns", category="refused",
                code="precondition")
    if os.path.lexists(place):
        _refuse(f"{name_value(place)} already exists; an immutable bundle is "
                f"published once and never appended to",
                category="refused", code="operation-collision")
    staging = place + ".incomplete"
    if os.path.lexists(staging):
        _refuse(f"{name_value(staging)} already exists; a previous publication "
                f"stopped and an operator decides what happened to it",
                category="refused", code="operation-collision")
    return staging


def _discard(staging):
    for root, directories, _ in os.walk(staging):
        for one in directories:
            try:
                os.chmod(os.path.join(root, one), STAGING_DIR)
            except OSError:
                pass
    shutil.rmtree(staging, ignore_errors=True)


def _emit(staging, parts, payload):
    place = os.path.join(staging, *parts)
    handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_NOFOLLOW, STAGING_FILE)
    try:
        written = 0
        while written < len(payload):
            written += os.write(handle, payload[written:])
        os.fsync(handle)
    finally:
        os.close(handle)
    return place


def _sync(place):
    handle = os.open(place, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def _publish(place, staging, files):
    """Write, measure, digest -- and only then make any of it reachable.

    THE RENAME IS THE LAST ACT AND EVERY ANSWER PRECEDES IT. Review
    2026-09-07T19:29:28Z [P1]: this renamed first and digested second, so a
    manifest that could not be represented refused AFTER a complete, readable,
    consumable bundle existed at the destination -- and the caller got no
    digest, no nomination, and a retry that collided with the material the
    failed call had left behind. Everything that can refuse now refuses while
    the only thing on disk is a staging directory this function will remove.
    """
    if len(files) > MAX_BUNDLE_FILES:
        _refuse(f"this bundle would hold {len(files)} files and a publication "
                f"manifest is bounded at {MAX_BUNDLE_FILES}; a bundle whose "
                f"own manifest cannot be digested is not published")
    manifest = []
    os.mkdir(staging, STAGING_DIR)
    try:
        for name in (EVIDENCE_DIRECTORY, BLOB_DIRECTORY):
            os.mkdir(os.path.join(staging, name), STAGING_DIR)
        for parts, payload in files:
            _emit(staging, parts, payload)
        for root, directories, names in os.walk(staging):
            for one in names:
                os.chmod(os.path.join(root, one), BUNDLE_FILE)
            _sync(root)
            for one in directories:
                os.chmod(os.path.join(root, one), BUNDLE_DIR)
        os.chmod(staging, BUNDLE_DIR)
        # MEASURED OFF THE STAGED BYTES rather than off what was intended to be
        # written, because the manifest is the publication's identity and an
        # identity derived from the operands would agree with itself.
        manifest = _measured(staging)
        if len(manifest) != len(files):
            _refuse(f"the staged bundle holds {len(manifest)} files and "
                    f"{len(files)} were composed")
        answer = {"manifest": manifest, "bundle_digest": digest(manifest)}
        os.rename(staging, place)
    except BaseException:
        _discard(staging)
        raise
    _sync(os.path.dirname(place))
    return answer


def _measured(staging):
    """Every staged file, read back from its own descriptor."""
    manifest = []
    for root, _, names in os.walk(staging):
        for one in names:
            place = os.path.join(root, one)
            with open(place, "rb") as handle:
                payload = handle.read()
            manifest.append({"path": os.path.relpath(place, staging),
                             "bytes": len(payload),
                             "digest": digest_of_bytes(payload)})
    manifest.sort(key=lambda one: one["path"].encode("utf-8"))
    return manifest


def compose_bundle(destination, *, manager, jobs, authority,
                   checkpoint_profile, integration_profile, assignment,
                   launch, instructions, line_id, proposal_id, runner):
    """Publish one immutable bundle and answer what it measured.

    THE ORDER IS THE CONTRACT. Every accepted owner is re-resolved and every
    disagreement refuses BEFORE the destination is touched; the version-control
    reading happens next, because a missing object must also refuse before
    anything is written; and only then is the material staged and renamed into
    place. Nothing consumable exists at any earlier point.

    WHAT IT RETURNS, AND WHY IT IS THIS. W110774 needs two things at its final
    grant boundary: the measured identity of everything published, and the
    manager's own nomination of the directory it will bind. A path is not a
    capability, so this answers a `NominatedSource` rather than a string.
    """
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")
    boundaries.capability(getattr(jobs, "_connection", None), "the Job store")
    for method in ("freeze", "validate"):
        boundaries.capability(getattr(checkpoint_profile, method, None),
                              f"the checkpoint profile's {method} capability")
    resolved = _accepted_evidence(manager, jobs, authority, line_id=line_id,
                                  proposal_id=proposal_id,
                                  checkpoint_profile=checkpoint_profile)
    account = resolved["account"]
    operands = _checked_operands(integration_profile=integration_profile,
                                 assignment=assignment, launch=launch,
                                 instructions=instructions)

    # THE LINE'S OWN CUSTODY, PROVED BEFORE IT IS READ. A public locator is not
    # host access: the row's recorded directory identity is compared with what
    # is on disk now, so a line path re-pointed between the manager's record
    # and this read refuses instead of being cloned into a bundle.
    line = resolved["line"]
    repository = _repository(line["line_path"], "the private line repository")
    proved = _custody(repository, line)

    # THE EXTRACTION IS BOUND TO ONE DIRECTORY, AND THE ACCOUNT IS RESOLVED
    # AGAIN AFTER IT. These are two different questions and the correction
    # history is why they are both here.
    #
    # Review 2026-09-07T19:29:28Z [P1]: the line was nominated once, before the
    # reads, and nothing looked again. Review 2026-09-07T19:51:54Z [P1]: the
    # answer to that -- nominating a second time -- is DETECTION and not the
    # binding the first review asked for, and a substitution restored before
    # the second look publishes with both measurements agreeing. I described
    # that check as if it closed the finding; it did not.
    #
    # So the reads now go through a DESCRIPTOR. It names one inode for as long
    # as it is open and the pathname is no longer part of any command, so
    # re-pointing the name cannot redirect a read. The second nomination and
    # the complete owner re-resolution below are KEPT, because they answer
    # whether the manager's own account still agrees -- which the binding does
    # not. W110774's grant check at the final start boundary remains separate.
    evidence = resolved["checkpoint"]["evidence"]
    directory = os.open(repository, os.O_RDONLY | os.O_DIRECTORY
                        | os.O_NOFOLLOW)
    try:
        opened = os.fstat(directory)
        # THE WINDOW BETWEEN PROVING AND OPENING, which this one does close:
        # the nomination answered about a name and this answers about the
        # descriptor every later read goes through, so a swap between the two
        # acts refuses here rather than being read from.
        if (opened.st_dev, opened.st_ino) != (proved.device, proved.inode):
            _drifted("the directory this producer opened is not the one it "
                     "nominated")
        table = reviewed_path_table(runner, directory, evidence)
    finally:
        os.close(directory)
    again = _accepted_evidence(manager, jobs, authority, line_id=line_id,
                               proposal_id=proposal_id,
                               checkpoint_profile=checkpoint_profile)
    for name in ("account", "checkpoint", "line", "documents"):
        if again[name] != resolved[name]:
            _drifted(f"the accepted {name} changed while this bundle was "
                     f"being extracted")
    after = _custody(repository, again["line"])
    if (after.device, after.inode) != (proved.device, proved.inode):
        _drifted(f"the private line at {name_value(repository)} was replaced "
                 f"while this bundle was being extracted")
    if digest([one["path"] for one in table["paths"]]) \
            != account["path_set_digest"]:
        _refuse("the composed path table is not the accepted path set")

    documents = resolved["documents"]
    files = []
    references = []
    for name in EVIDENCE_DOCUMENTS:
        payload = _canonical(documents[name], f"evidence {name}")
        # THE BOUND THIS MODULE DECLARED AND DID NOT CHECK. Review
        # 2026-09-07T19:29:28Z: `MAX_EVIDENCE_BYTES` existed in both spellings
        # of the contract and no producer path enforced it.
        if len(payload) > MAX_EVIDENCE_BYTES:
            _refuse(f"evidence {name} is {len(payload)} bytes, above the bound "
                    f"of {MAX_EVIDENCE_BYTES}")
        references.append({"name": name, "digest": _address(payload),
                           "bytes": len(payload)})
        files.append(((EVIDENCE_DIRECTORY, name), payload))
    envelope = {"schema": BUNDLE_SCHEMA,
                "assignment_digest": operands["assignment_digest"],
                "launch": operands["launch"],
                "eligibility": dict(account),
                "checkpoint": dict(resolved["checkpoint"]),
                "evidence": references,
                "instructions": {"digest": _address(instructions),
                                 "bytes": len(instructions)},
                "paths": table["paths"]}
    body = _canonical(envelope, "the bundle envelope")
    if len(body) > MAX_ENVELOPE_BYTES:
        _refuse(f"the composed envelope is {len(body)} bytes, above the bound "
                f"of {MAX_ENVELOPE_BYTES}")
    files.append(((ENVELOPE_DOCUMENT,), body))
    files.append(((INSTRUCTIONS_DOCUMENT,), instructions))
    for address, payload in sorted(table["blobs"].items()):
        files.append(((BLOB_DIRECTORY, address), payload))

    envelope_digest = digest_of_bytes(body)
    staging = _destination(destination)
    published = _publish(destination, staging, files)
    return {"root": destination,
            "bundle_digest": published["bundle_digest"],
            "envelope_digest": envelope_digest,
            "manifest": published["manifest"],
            "source": nominate_source(destination),
            "path_count": len(table["paths"]),
            "blob_bytes": table["total_bytes"],
            "eligibility": dict(account)}


def _canonical(document, what):
    from baton_v12.contracts.canonical import canonical_bytes

    try:
        return canonical_bytes(document)
    except ContractRefusal:
        raise
    except (TypeError, ValueError):
        _refuse(f"{what} is not one canonically representable document")


def _address(payload):
    return digest_of_bytes(payload).split(":", 1)[1]
