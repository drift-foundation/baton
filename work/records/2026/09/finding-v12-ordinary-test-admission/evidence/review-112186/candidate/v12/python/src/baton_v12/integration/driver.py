"""Replay-safe composition of proposal publication and accepted integration.

W103077.  This module adds no new authority, queue, runtime, or recovery
state.  It gives the accepted operations stable identities, selects their
inputs from the stores that own them, and orders them so a restart adopts each
durable cutpoint before attempting the next one.

Publication is deliberately separate.  It must run while the implementation
assignment is still live; checkpoint freezing fences that assignment.  The
later accepted path writes the three configured receipts, admits the account,
and drives (or adopts) its one serialized integration.
"""

import re

from ..authority.errors import Refusal as AuthorityRefusal
from ..contracts import ContractRefusal, check_no_durable_secret, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from ..worker_manager.attempts import assignment_of
from ..worker_manager.manifests import load_manifest, retain_manifest
from ..worker_manager.output import frozen_output_of
from ..worker_manager.review_cycles import (checkpoint_of,
                                            integration_checkpoint,
                                            writer_of)
from . import admission, execution, recovery, runtime
from .admission import admit_candidate, resolved_account
from .queue import entries_of, lease_of, live_grant, target_of

__all__ = ["admit_accepted", "publish_candidate", "retain_proposal"]

# The one declared output type a proposal is made of.
PROPOSAL_OUTPUT = "git-change-proposal"

# THE WORKER'S OWN CLAIM, and its closed member set. `result_metadata` is the
# frozen schema's opaque per-output extension point: the worker writes it, the
# generic Worker Manager carries it without reading it, and THIS module is the
# format-specific party that finally interprets it.
#
# FOUR MEMBERS AND NO FIFTH. What the turn was built on, what it produced,
# where its objects sit inside its own measured output, and what it did in
# words. Every manager measurement and custody identity is composed here from
# the accepted producer instead -- a worker that named an artifact id, a
# content digest or an assignment reference would be certifying its own output,
# and an extra member is refused rather than ignored.
CLAIM_NAMESPACE = "baton.git-proposal/1"
CLAIM_MEMBERS = ("base", "head", "recap", "transport")

# `implementation_recap` and the transport locator's own frozen ceilings.
MAX_RECAP = 16000
MAX_TRANSPORT = 128

# THE OBJECT-NAME NAMESPACE IS THE WIDTH, and this is the accepted rule rather
# than a second opinion about it: `source_profiles.BASE_KINDS` fixes the same
# two widths for the same reason, and neither is ever converted into the other.
# Spelled here instead of imported because the worker's profile package is the
# CONSUMER of a mounted source, and an integration module reaching into it
# would couple two packages that have no other business together.
_OBJECT_NAMESPACES = {40: "sha1", 64: "sha256"}
_OBJECT_NAME = re.compile(r"\A[0-9a-f]+\Z")


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _authority(action, what, operands=None):
    try:
        return action() if operands is None else action(operands)
    except AuthorityRefusal as refused:
        _refuse(f"the Authority refused {what}: {refused}",
                category="refused", code="precondition")


def _capability(owner, name, what):
    return boundaries.capability(getattr(owner, name, None),
                                 f"{what}'s {name}")


def _identity(kind, account):
    """A bounded operation identity derived from its complete account."""
    return f"integration-driver.{kind}:" + digest(account)[len("sha256:"):]


def _assignment(manager, attempt_id):
    fixed = assignment_of(manager, attempt_id)
    return {
        "work_ref": {"authority_uuid": fixed["authority_uuid"],
                     "work_id": fixed["work_id"]},
        "participant": fixed["participant"],
        "generation": fixed["generation"]}


def _manifest(manager, manifest_digest, definition, what):
    found = load_manifest(manager, manifest_digest, definition)
    if found is None:
        _refuse(f"the Worker Manager holds no {what} at "
                f"{name_value(manifest_digest)}", category="refused",
                code="precondition")
    return found


def _one_output(result):
    """The single present proposal output of a frozen result.

    SELECTION ONLY, and separated from the cross-binding below because the two
    have different callers: the producer has no proposal to compare against
    yet, and one rule read twice is the thing this split exists to avoid.
    """
    matches = [one for one in result["outputs"]
               if one["type"] == PROPOSAL_OUTPUT]
    if len(matches) != 1:
        _refuse(f"the frozen result carries {len(matches)} "
                f"{PROPOSAL_OUTPUT} outputs; publication needs exactly one")
    output = matches[0]
    if output["status"] != "present" or output["artifact"] is None \
            or output["content_manifest"] is None:
        _refuse("the frozen proposal output is not present with both its "
                "artifact and content manifest")
    return output


def _one_proposal_output(result, proposal):
    output = _one_output(result)
    if output["artifact"] != proposal["proposal_artifact"]:
        _refuse("the proposal manifest's artifact is not the artifact frozen "
                "in its result")
    if proposal["output_digest"] != output["content_manifest"]["tree_digest"]:
        _refuse("the proposal manifest's output digest is not its frozen "
                "content-tree digest")
    return output


def _publish_signature(operands):
    """§4.2's operation identity over the durable publish operands.

    ONE SPELLING FOR TWO CALLERS. The producer composes this digest into the
    manifest it retains and the publisher recomputes it before calling the
    Authority; two copies of the payload rule would be two things to keep
    equal, and a producer whose signature its own consumer rejects is a Work
    that cannot publish at all.
    """
    return digest({"kind": "publish", "operands": {
        name: value for name, value in operands.items()
        if name != "operation_id"}})


def _expected_answer(operands, fixed):
    """The exact Authority answer these operands ask for, and it is one
    spelling for the same two callers."""
    return {
        "proposal_id": operands["proposal_id"],
        "assignment_ref": fixed,
        "result_id": operands["result_id"],
        "result_digest": operands["result_digest"],
        "candidate_digest": operands["candidate_digest"],
        "input_digest": operands["input_digest"],
        "policy_digest": operands["policy_digest"],
        "target": operands["target"]}


def _object_name(value, what):
    """One `gitObject`, with its namespace taken from the object-name width.

    THE WIDTH IS THE NAMESPACE and neither name is ever converted into the
    other: a sha1 name under a sha256 repository is a different object, not a
    shorter digest. Lower case only, for the reason the profile package gives:
    the same object in two spellings is two objects to every comparison
    downstream.
    """
    boundaries.text(value, what)
    kind = _OBJECT_NAMESPACES.get(len(value))
    if kind is None or not _OBJECT_NAME.match(value):
        widths = sorted(str(one) for one in _OBJECT_NAMESPACES)
        _refuse(f"{what} is a full lower-case object name at one of "
                f"{' or '.join(str(one) for one in widths)}"
                f" characters; this is {name_value(value)}")
    return {"algorithm": kind, "hex": value}


def _claim_of(output):
    """The worker's own proposal facts, adopted and never extended.

    ADOPTED AS A CLOSED DOCUMENT. An extra member is refused rather than
    ignored, because the members this producer would be tempted to accept are
    exactly the ones it must compose itself -- an artifact id, a content
    digest, an assignment reference. A worker that supplied one of those would
    be certifying the manager's measurement of its own output.

    THE TRANSPORT IS BOUND TO THE MEASUREMENT. A worker names where its objects
    sit inside its declared output; whether anything is there is the manager's
    content manifest to say. Checking the name against that measured entry list
    is what keeps the locator from being a claim about bytes nobody weighed.
    """
    metadata = output["result_metadata"]
    if type(metadata) is not dict or CLAIM_NAMESPACE not in metadata:
        _refuse(f"the frozen proposal output carries no "
                f"{name_value(CLAIM_NAMESPACE)} claim; the proposal head and "
                f"the base it was built on are the worker's own facts and "
                f"this producer will not invent them")
    claim = boundaries.document(metadata[CLAIM_NAMESPACE],
                                "a worker proposal claim",
                                required=CLAIM_MEMBERS)
    boundaries.text(claim["recap"], "the worker's implementation recap")
    if len(claim["recap"]) > MAX_RECAP:
        _refuse(f"the worker's implementation recap is wider than "
                f"{MAX_RECAP} characters")
    transport = claim["transport"]
    boundaries.text(transport, "the worker's object transport")
    if len(transport) > MAX_TRANSPORT:
        _refuse(f"the worker's object transport name is wider than "
                f"{MAX_TRANSPORT} characters")
    measured = output["content_manifest"]["entries"]
    entries = {entry["path"] for entry in measured}
    if transport not in entries:
        _refuse(f"the worker names its object transport at "
                f"{name_value(transport)} and the frozen content manifest "
                f"measured nothing there")
    return claim


def retain_proposal(manager, publisher, *, attempt_id):
    """Compose, validate and retain ONE proposal manifest; answer its digest.

    W103874, and the seam it fills is `publish_candidate`'s: that operation
    takes a retained `proposalManifest` as a selector and re-reads every
    publication member out of it. Nothing produced one. This does, from the
    exact frozen result and nowhere else.

    THE TWO HALVES ARE COMPOSED BY THE PARTY THAT OWNS EACH. The worker-owned
    half -- the base it built on, the head it made, where its objects are, and
    what it did -- arrives opaquely through `result_metadata` and is ADOPTED.
    Every other member is read back here from its accepted producer: the fixed
    assignment, the frozen result summary and its retained manifest, that
    result's retained input manifest, the manager's own measurement of the
    proposal output, and the Authority's current canonical target. Neither side
    may manufacture the other's half, which is why the claim is a closed
    four-member document and why nothing below reads a mutable `/output` path
    or a custody byte.

    IT REFUSES TARGET DRIFT AND RETAINS NOTHING. A proposal is offered against
    the revision it was built on; if the Authority has moved on, the manifest
    that would be composed is one `publish_candidate` must reject anyway, and
    retaining it would leave a second durable account of one frozen result for
    a publication that never happens.

    REPLAY IS BY CONSTRUCTION RATHER THAN BY A JOURNAL. Every member is derived
    from immutable evidence -- including `created_at`, which is the frozen
    result's own `manager_observed_at` and NOT a fresh clock read: retention is
    keyed by the digest of the bytes, so a clock would retain a differently
    keyed account of the same result on every call and the exact-replay
    guarantee would be silently false.
    """
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")
    boundaries.identity(attempt_id, "an implementation attempt id")
    _capability(publisher, "canonical_target", "the publisher session")
    frozen = frozen_output_of(manager, attempt_id)
    if frozen is None or frozen["disposition"] != "completed":
        _refuse(f"attempt {name_value(attempt_id)} has no completed frozen "
                "result to propose", category="refused", code="precondition")
    result = _manifest(manager, frozen["manifest_digest"], "resultManifest",
                       "result manifest")
    given = _manifest(manager, result["input_manifest_digest"],
                      "inputManifest", "input manifest")
    fixed = _assignment(manager, attempt_id)
    if result["assignment_ref"] != fixed:
        _refuse("the frozen result and the implementation attempt do not name "
                "one assignment")
    if result["result_id"] != frozen["result_id"]:
        _refuse("the frozen result summary and its retained manifest name "
                "different results")
    output = _one_output(result)
    claim = _claim_of(output)
    source_base = _object_name(claim["base"], "the worker's declared base")
    proposal_head = _object_name(claim["head"], "the worker's proposal head")
    current = _authority(publisher.canonical_target,
                         "the canonical target read")
    target_revision = _object_name(current, "the Authority's canonical target")
    if source_base != target_revision:
        _refuse(f"the worker built on {name_value(claim['base'])} and the "
                f"Authority target is {name_value(current)}; a proposal "
                f"is offered against the revision it was built from",
                category="refused", code="precondition")
    if proposal_head["algorithm"] != target_revision["algorithm"]:
        _refuse("the proposal head and target revision use different object "
                "namespaces")

    # THE ACCOUNT BOTH DERIVED IDENTITIES ARE TAKEN FROM. One dictionary rather
    # than two spellings of it, because the whole property they carry is that
    # two different frozen results never produce the same identity and one
    # frozen result always produces the same one.
    account = {"assignment_ref": fixed, "result_id": result["result_id"],
               "result_digest": frozen["manifest_digest"],
               "candidate_digest": proposal_head["hex"]}
    operands = {
        "expect": fixed,
        "proposal_id": _identity("proposal", account),
        "result_id": result["result_id"],
        "result_digest": frozen["manifest_digest"],
        "candidate_digest": proposal_head["hex"],
        "input_digest": result["input_manifest_digest"],
        "policy_digest": result["policy_digest"],
        "target": target_revision["hex"]}
    signature = _publish_signature(operands)
    body = {
        "version": {"major": 1, "minor": 0},
        # DERIVED, NOT PREFIXED. W103874 candidate review 2026-09-07: a result
        # id and a manifest id are both `opaqueId`, which is bounded at 160
        # characters -- so `proposal-<result_id>` is longer than its own type
        # allows for every result id from 152 characters up, and the producer
        # refused perfectly valid frozen results at retention. A prefix is a
        # composition whose length is the INPUT's; a digest over the account is
        # one whose length is this module's, which is the only kind of identity
        # a bounded member can carry. It stays deterministic and stays distinct
        # -- the account is the same one `proposal_id` is taken from -- and
        # nothing is truncated, because truncation is how two distinct results
        # become one name.
        "manifest_id": _identity("proposal-manifest", account),
        # THE FROZEN INSTANT, NOT THIS CALL'S. See the docstring: a clock read
        # here would make every replay a new document.
        "created_at": result["manager_observed_at"],
        "extensions": {},
        "schema": "baton.worker-manifest/proposal",
        "proposal_id": operands["proposal_id"],
        "assignment_ref": fixed,
        "result_id": operands["result_id"],
        "result_manifest_digest": operands["result_digest"],
        "input_manifest_digest": operands["input_digest"],
        "policy_digest": operands["policy_digest"],
        "runtime_profile_digest": given["runtime_profile_digest"],
        "output_digest": output["content_manifest"]["tree_digest"],
        "source_base": source_base,
        "target_revision": target_revision,
        "proposal_head": proposal_head,
        "proposal_artifact": output["artifact"],
        # A WORKER CANNOT MINT CUSTODY IDENTITIES, and an `evidenceRef` is
        # made of one. The empty lists are the honest answer rather than a
        # placeholder: this producer has no independent certification to offer
        # and will not present the worker's word as one.
        "author_tests": [],
        "implementation_recap": claim["recap"],
        "dossier_evidence": [],
        "publish_operation": {
            "operation_id": _identity("publish-operation",
                                      {"signature_digest": signature}),
            "signature_digest": signature},
        "publish_receipt_digest": digest(_expected_answer(operands, fixed))}
    # §13 BEFORE IT BECOMES DURABLE, exactly as the seal does it: a
    # proposal is composed from identities and locators this producer was
    # handed, and a locator is the kind of member a credential rides in.
    check_no_durable_secret(body, what="a retained proposal")
    return retain_manifest(manager, {**body, "manifest_digest": digest(body)},
                           "proposalManifest")["digest"]


def _publish_operands(manager, attempt_id, proposal_manifest_digest):
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")
    boundaries.identity(attempt_id, "an implementation attempt id")
    boundaries.identity(proposal_manifest_digest,
                        "a retained proposal manifest digest")
    frozen = frozen_output_of(manager, attempt_id)
    if frozen is None or frozen["disposition"] != "completed":
        _refuse(f"attempt {name_value(attempt_id)} has no completed frozen "
                "result to publish", category="refused", code="precondition")
    proposal = _manifest(manager, proposal_manifest_digest,
                         "proposalManifest", "proposal manifest")
    result = _manifest(manager, frozen["manifest_digest"], "resultManifest",
                       "result manifest")
    fixed = _assignment(manager, attempt_id)

    if proposal["assignment_ref"] != fixed \
            or result["assignment_ref"] != fixed:
        _refuse("the retained proposal, frozen result and implementation "
                "attempt do not name one assignment")
    if proposal["result_id"] != frozen["result_id"] \
            or proposal["result_id"] != result["result_id"]:
        _refuse("the retained proposal does not name the frozen result")
    if proposal["result_manifest_digest"] != frozen["manifest_digest"]:
        _refuse("the retained proposal does not bind the frozen result bytes")
    if result["input_manifest_digest"] != proposal["input_manifest_digest"] \
            or result["policy_digest"] != proposal["policy_digest"]:
        _refuse("the retained proposal and frozen result disagree about their "
                "input or policy")
    _one_proposal_output(result, proposal)
    if proposal["source_base"] != proposal["target_revision"]:
        _refuse("the proposal was not built from the target revision it asks "
                "the Authority to replace")
    if proposal["proposal_head"]["algorithm"] \
            != proposal["target_revision"]["algorithm"]:
        _refuse("the proposal head and target revision use different object "
                "namespaces")

    candidate = proposal["proposal_head"]["hex"]
    target = proposal["target_revision"]["hex"]
    operands = {
        "expect": fixed,
        "operation_id": proposal["publish_operation"]["operation_id"],
        "proposal_id": proposal["proposal_id"],
        "result_id": proposal["result_id"],
        "result_digest": proposal["result_manifest_digest"],
        "candidate_digest": candidate,
        "input_digest": proposal["input_manifest_digest"],
        "policy_digest": proposal["policy_digest"],
        "target": target}
    signature = _publish_signature(operands)
    if proposal["publish_operation"]["signature_digest"] != signature:
        _refuse("the proposal manifest's publish operation does not bind its "
                "exact Authority operands")
    expected = _expected_answer(operands, fixed)
    if proposal["publish_receipt_digest"] != digest(expected):
        _refuse("the proposal manifest's publish receipt digest does not bind "
                "the Authority answer it requests")
    return proposal, operands, expected


def publish_candidate(manager, publisher, *, attempt_id,
                      proposal_manifest_digest):
    """Publish one manager-owned proposal while its producer remains live.

    The manifest digest is only a selector.  Every publication member is read
    back from the retained manifest, frozen result, fixed assignment, and live
    Authority target before ``publish`` is called.
    """
    _capability(publisher, "publish", "the publisher session")
    _capability(publisher, "proposal", "the publisher session")
    _capability(publisher, "canonical_target", "the publisher session")
    proposal, operands, expected = _publish_operands(
        manager, attempt_id, proposal_manifest_digest)
    current = _authority(publisher.canonical_target,
                         "the canonical target read")
    if current != operands["target"]:
        _refuse(f"the Authority target is {name_value(current)} and the "
                f"proposal was built from {name_value(operands['target'])}",
                category="refused", code="precondition")
    answer = _authority(publisher.publish, "proposal publication", operands)
    if answer != expected:
        _refuse("the Authority's publication answer is not the exact proposal "
                "the manager requested")
    recorded = _authority(
        lambda: publisher.proposal(proposal["proposal_id"]),
        "published proposal read")
    for name, value in expected.items():
        if recorded.get(name) != value:
            _refuse(f"the recorded Authority proposal disagrees about {name}")
    return recorded


def _receipt(session, kind, basis, **members):
    verb = {"verification": "verify", "review": "review",
            "approval": "approve"}[kind]
    _capability(session, verb, f"the configured {kind} session")
    participant = boundaries.text(getattr(session, "participant", None),
                                  f"the configured {kind} participant")
    receipt_basis = dict(basis, kind=kind)
    receipt_id = _identity(f"{kind}-receipt", receipt_basis)
    operation_basis = dict(receipt_basis, actor=participant, **members)
    operands = {"proposal_id": basis["proposal_id"],
                {"verification": "verification_id", "review": "review_id",
                 "approval": "approval_id"}[kind]: receipt_id,
                "operation_id": _identity(f"{kind}-operation",
                                          operation_basis), **members}
    return _authority(getattr(session, verb), f"the {kind} receipt", operands)



# -- W112029: the ordinary-test observation, and what it may authorize --------
#
# `work/records/2026/09/finding-v12-ordinary-test-admission/`.
#
# WHAT WAS WRONG, AND IT WAS ONE WORD. `_accepted_receipts` published the
# Authority's verification receipt with `observation="passed"` unconditionally,
# for every accepted checkpoint, whatever any test had done. An accepted
# TECHNICAL REVIEW is a human-or-model judgement about a change; it is not a
# statement that the required commands ran and exited zero, and publishing one
# as the other made the strongest receipt in the protocol the least evidenced.
#
# WHAT REPLACES IT IS NOT A NEW PRODUCER. Owner ruling M111752: this milestone's
# verification is the implementer running the ordinary required tests plus an
# independent review. The worker ALREADY runs the frozen task's own verification
# argv, and W112029's worker half exposes that same answer on the frozen
# proposal output. So this reads an observation somebody already made rather
# than commissioning one, and it says so in the receipt's own identity.
#
# AND IT IS HONEST ABOUT WHAT IT IS. This is author-container testing plus
# independent review. It is NOT clean candidate-merge certification, no part of
# it claims to be, and the ordinary-tests marker in the operation identity is
# there so a later reader cannot mistake one for the other.

ORDINARY_TESTS_NAMESPACE = "baton.git-ordinary-tests/1"
ORDINARY_TESTS_MEMBERS = ("argv", "base", "head", "status", "task_digest",
                          "task_id")

# WHAT A DEPLOYMENT SUPPLIES AS ITS REQUIREMENT, and every member of it is a
# SELECTION rather than an answer. There is no `status` here and there never
# will be: a caller that could supply the observation would be certifying its
# own candidate, which is the exact defect the unconditional `passed` was.
REQUIRED_TESTS_MEMBERS = ("argv", "input_manifest_digest", "task_digest",
                          "task_id")

# The marker that rides in the receipt and operation identity. Deliberately not
# a word like `verified` or `certified`: what happened is that the author's own
# container ran the required command.
ORDINARY_TESTS_WORKFLOW = "ordinary-tests/1"


def _owned_requirements(required_tests):
    """The deployment's closed required-test selection.

    W103083 derives this from the implementation task bytes it already holds
    for this Job's producer, including correction attempts. It is trusted
    configuration in exactly the sense the integration profile is: this module
    proves the OBSERVATION against it and never the other way round.
    """
    held = boundaries.document(required_tests, "a required-test selection",
                               required=REQUIRED_TESTS_MEMBERS)
    boundaries.identity(held["task_id"], "a required-test task id")
    boundaries.text(held["task_digest"], "a required-test task digest")
    boundaries.text(held["input_manifest_digest"],
                    "a required-test input manifest digest")
    argv = held["argv"]
    if type(argv) is not list or not argv \
            or not all(type(one) is str and one for one in argv):
        _refuse("a required-test selection names its command as a non-empty "
                "list of words; a command this module would have to assemble "
                "from a string is a shell, and there is no shell here")
    return held


def _observation_of(output):
    """The worker's own ordinary-test observation, adopted and never extended.

    ADOPTED AS A CLOSED DOCUMENT, for `_claim_of`'s reason: the members this
    reader would be tempted to accept are exactly the ones it must read from
    their owners. There is no `passed` in it and no boolean; a status is what
    the worker's `wait` answered, and deciding about it is this module's job.
    """
    metadata = output["result_metadata"]
    if type(metadata) is not dict \
            or ORDINARY_TESTS_NAMESPACE not in metadata:
        _refuse(f"the frozen proposal output carries no "
                f"{name_value(ORDINARY_TESTS_NAMESPACE)} observation; what the "
                f"required tests did is the producer's own fact and this "
                f"module will not assume it", category="refused",
                code="precondition")
    held = boundaries.document(metadata[ORDINARY_TESTS_NAMESPACE],
                               "a worker ordinary-test observation",
                               required=ORDINARY_TESTS_MEMBERS)
    boundaries.identity(held["task_id"], "an observed task id")
    boundaries.text(held["task_digest"], "an observed task digest")
    for member in ("base", "head"):
        boundaries.text(held[member], f"an observed {member} object")
    argv = held["argv"]
    if type(argv) is not list or not argv \
            or not all(type(one) is str and one for one in argv):
        _refuse("an ordinary-test observation names its command as a "
                "non-empty list of words")
    status = held["status"]
    # UNRUN IS `None` AND IS NOT A FAILURE TO PARSE. The worker writes null
    # when the command did not produce a status at all -- skipped, timed out,
    # or unable to start -- and all three are "no evidence", which is a
    # different refusal from "evidence of a non-zero exit".
    if status is not None \
            and (type(status) is bool or type(status) is not int):
        _refuse("an ordinary-test observation's status is a whole number or "
                "null")
    return held


def ordinary_test_evidence(manager, authority, *, line_id, proposal_id):
    """The observation an accepted checkpoint's own producer actually made.

    PUBLIC AND READ-ONLY. It writes nothing and decides nothing: it resolves
    the accepted checkpoint's producer, re-reads that attempt's frozen result
    and retained manifest through their accepted owners, and answers the
    worker's observation cross-bound to the proposal the Authority holds.

    EVERY IDENTITY IS COMPARED THROUGH AN OWNER. The retained proposal manifest
    names the result and the assignment; the frozen summary names the same
    result; the published proposal names the same candidate and input and
    policy digests; and the observation's own base and head are the ones the
    proposal manifest recorded. A consumer that skipped any of these would be
    reading SOME container's test result rather than this candidate's.

    IT SURVIVES ORDINARY CLEANUP, which is the property that makes it usable at
    admission: every fact above comes from a retained manifest or a durable
    row, and none from a runtime, a workspace or an output directory that
    cleanup removes.
    """
    accepted = integration_checkpoint(manager, line_id)
    if accepted is None:
        _refuse(f"development line {name_value(line_id)} has no accepted "
                f"integration checkpoint", category="refused",
                code="precondition")
    writer = writer_of(
        manager, checkpoint_of(
            manager, accepted["checkpoint_id"])["writer_id"])
    producer = writer["runtime_attempt_id"]
    frozen = frozen_output_of(manager, producer)
    if frozen is None or frozen["disposition"] != "completed":
        _refuse(f"the accepted checkpoint's producer "
                f"{name_value(producer)} has no completed frozen result",
                category="refused", code="precondition")
    result = _manifest(manager, frozen["manifest_digest"], "resultManifest",
                       "result manifest")
    if result["result_id"] != frozen["result_id"]:
        _refuse("the frozen result summary and its retained manifest name "
                "different results")
    fixed = _assignment(manager, producer)
    if result["assignment_ref"] != fixed:
        _refuse("the frozen result and the producing attempt do not name one "
                "assignment")
    proposal = admission._proposal(authority, proposal_id)
    if proposal["result_id"] != result["result_id"] \
            or proposal["result_digest"] != frozen["manifest_digest"]:
        _refuse("the published proposal and the producer's frozen result name "
                "different results; the observation must be about the "
                "candidate this admission is for")
    if proposal["input_digest"] != result["input_manifest_digest"] \
            or proposal["policy_digest"] != result["policy_digest"]:
        _refuse("the published proposal and the frozen result name different "
                "input or policy identities")
    output = _one_output(result)
    claim = _claim_of(output)
    observed = _observation_of(output)
    for member in ("base", "head"):
        if observed[member] != claim[member]:
            _refuse(f"the ordinary-test observation says it ran over {member} "
                    f"{name_value(observed[member])} and the proposal claim "
                    f"names {name_value(claim[member])}; an observation about "
                    f"another candidate is not this one's evidence")
    if _object_name(claim["head"],
                    "the worker's proposal head")["hex"] \
            != proposal["candidate_digest"]:
        _refuse("the proposal claim's head and the published candidate digest "
                "disagree")
    if accepted["head"] != claim["head"]:
        _refuse(f"the accepted checkpoint records head "
                f"{name_value(accepted['head'])} and the producer's proposal "
                f"claims {name_value(claim['head'])}")
    return {"attempt_id": producer, "checkpoint_id": accepted["checkpoint_id"],
            "assignment_ref": fixed,
            "input_manifest_digest": result["input_manifest_digest"],
            "result_id": result["result_id"],
            "result_digest": frozen["manifest_digest"],
            "observation": observed}


def _ordinary_tests_passed(evidence, requirements):
    """Whether these EXACT requirements actually ran and exited zero.

    THE ONLY ROUTE TO A `passed` RECEIPT, and every clause is a way an
    observation can be about something else: another task, another version of
    the same task, another command, or another attempt's inputs. A status of
    zero for a command nobody required proves nothing about the requirement.

    A NON-ZERO STATUS AND AN UNRUN COMMAND ARE BOTH REFUSALS AND ARE NOT THE
    SAME ONE. The first is evidence that the required tests failed; the second
    is the absence of evidence. Neither may be admitted, and reporting one as
    the other would tell an operator to look in the wrong place.
    """
    held = _owned_requirements(requirements)
    observed = evidence["observation"]
    for member in ("task_id", "task_digest"):
        if observed[member] != held[member]:
            _refuse(f"the required tests name {member} "
                    f"{name_value(held[member])} and this producer observed "
                    f"{name_value(observed[member])}; an observation of "
                    f"another task is not evidence about this requirement",
                    category="refused", code="precondition")
    if list(observed["argv"]) != list(held["argv"]):
        _refuse(f"the required tests name the command "
                f"{name_value(' '.join(held['argv']))} and this producer "
                f"observed {name_value(' '.join(observed['argv']))}",
                category="refused", code="precondition")
    if evidence["input_manifest_digest"] != held["input_manifest_digest"]:
        _refuse("the required tests were selected for another attempt's input "
                "manifest", category="refused", code="precondition")
    if observed["status"] is None:
        _refuse(f"the required tests for task "
                f"{name_value(held['task_id'])} did not run in this "
                f"producer's container, so nothing about them is proved; an "
                f"accepted technical review is not a substitute",
                category="refused", code="precondition")
    if observed["status"] != 0:
        _refuse(f"the required tests for task {name_value(held['task_id'])} "
                f"exited {observed['status']} in this producer's container; a "
                f"failing required command is not admitted and an accepted "
                f"technical review is not a substitute", category="policy",
                code="denied")
    return held


def _accepted_receipts(manager, authority, verification, reviewer, approver,
                       *, line_id, proposal_id, policy_generation,
                       required_tests):
    _capability(authority, "proposal", "the Authority")
    _capability(authority, "policy_generation", "the Authority")
    for session, kind, verb in ((verification, "verification", "verify"),
                                (reviewer, "review", "review"),
                                (approver, "approval", "approve")):
        _capability(session, verb, f"the configured {kind} session")
        boundaries.text(getattr(session, "participant", None),
                        f"the configured {kind} participant")
    boundaries.identity(line_id, "an accepted development line id")
    boundaries.identity(proposal_id, "an Authority proposal id")
    boundaries.generation(policy_generation,
                          "the configured approval policy generation")
    if policy_generation < 1:
        _refuse("the configured approval policy generation counts from one")
    current_generation = _authority(
        authority.policy_generation, "the approval policy generation read")
    boundaries.generation(current_generation,
                          "the Authority's approval policy generation")
    if current_generation != policy_generation:
        _refuse(f"the deployment pins approval policy generation "
                f"{policy_generation} and the Authority is at "
                f"{name_value(current_generation)}", category="policy",
                code="denied")
    accepted = integration_checkpoint(manager, line_id)
    if accepted is None:
        _refuse(f"development line {name_value(line_id)} has no accepted "
                "integration checkpoint", category="refused",
                code="precondition")
    proposal = admission._proposal(authority, proposal_id)
    # THE EVIDENCE IS PROVED BEFORE ANY RECEIPT SIDE EFFECT. Nothing below this
    # line is reached by a candidate whose required tests failed, did not run,
    # or were somebody else's -- so a refusal here writes no verification,
    # review or approval receipt and admits nothing.
    evidence = ordinary_test_evidence(manager, authority, line_id=line_id,
                                      proposal_id=proposal_id)
    requirements = _ordinary_tests_passed(evidence, required_tests)
    witness = {"workflow": ORDINARY_TESTS_WORKFLOW,
               "ordinary_tests": digest(evidence["observation"]),
               "required_tests": digest(requirements),
               "producer_attempt_id": evidence["attempt_id"],
               "result_digest": evidence["result_digest"]}
    basis = {"proposal_id": proposal_id,
             "candidate_digest": proposal["candidate_digest"],
             "target": proposal["target"],
             "line_id": accepted["line_id"],
             "checkpoint_id": accepted["checkpoint_id"],
             "verdict_id": accepted["verdict_id"],
             "checkpoint_digest": accepted["checkpoint_digest"]}
    # W112029: THE VERIFICATION RECEIPT IS EVIDENCE-DRIVEN. `observation` was
    # the literal `passed` for every accepted checkpoint; it is now published
    # only after `_ordinary_tests_passed` has proved an actual status-zero run
    # of the EXACT required command by this candidate's own producer, and the
    # receipt and operation identities carry the observation and requirement
    # digests plus an ordinary-tests marker so the receipt says what kind of
    # evidence it rests on.
    answers = {
        "verification": _receipt(verification, "verification",
                                 dict(basis, **witness),
                                 observation="passed"),
        "review": _receipt(reviewer, "review", basis,
                           disposition="accepted"),
        "approval": _receipt(approver, "approval", basis,
                             disposition="approved",
                             policy_generation=policy_generation)}
    return accepted, proposal, answers


def _same_account(entry, current):
    admitted = entry["eligibility"]
    for name in sorted(admitted):
        if current.get(name) != admitted[name]:
            _refuse(f"entry {name_value(entry['entry_id'])} was admitted with "
                    f"{name} {name_value(admitted[name])} and its accepted "
                    f"producers now say {name_value(current.get(name))}",
                    category="refused", code="precondition")


def _current_entry(store, canonical_target_id, entry_id, account):
    """Refresh the materialized entry after immutable enqueue replay."""
    standing = [one for one in entries_of(store, canonical_target_id)
                if one["entry_id"] == entry_id]
    if len(standing) != 1:
        _refuse(f"target {name_value(canonical_target_id)} holds "
                f"{len(standing)} current entries named "
                f"{name_value(entry_id)}; exactly one admitted entry is "
                f"required")
    current = standing[0]
    if current["eligibility"] != account:
        _refuse(f"entry {name_value(entry_id)} does not retain the exact "
                f"accepted eligibility account resolved for this proposal",
                category="refused", code="precondition")
    return current


def _existing_assignment(profile, held):
    taken = runtime._owned_profile(profile)
    if held["integrator_participant"] != taken["integrator_participant"]:
        _refuse("the retained lease belongs to another configured integrator",
                category="policy", code="denied")
    return runtime._owned_assignment({
        "schema": runtime.ASSIGNMENT_SCHEMA,
        "canonical_target_id": held["canonical_target_id"],
        "entry_id": held["entry_id"], "lease_id": held["lease_id"],
        "fence": held["fence"], "attempt_id": held["attempt_id"],
        "integrator_participant": taken["integrator_participant"],
        "profile_kind": taken["profile_kind"],
        "profile_version": taken["profile_version"],
        "instructions_digest": taken["instructions_digest"],
        "target_access": "writable"})


def _integrate_receipt(session, basis):
    _capability(session, "integrate", "the configured integration session")
    _capability(session, "receipt", "the configured integration session")
    participant = boundaries.text(getattr(session, "participant", None),
                                  "the configured integration participant")
    integration_id = _identity("integration-receipt", basis)
    operands = {"proposal_id": basis["proposal_id"],
                "integration_id": integration_id,
                "operation_id": _identity(
                    "integration-operation", dict(basis, actor=participant))}
    _authority(session.integrate, "the integration receipt", operands)
    return _read_integrate_receipt(session, basis)


def _read_integrate_receipt(session, basis):
    """Read and cross-bind an existing Authority integration receipt."""
    _capability(session, "receipt", "the configured integration session")
    participant = boundaries.text(getattr(session, "participant", None),
                                  "the configured integration participant")
    integration_id = _identity("integration-receipt", basis)
    recorded = _authority(
        lambda: session.receipt(basis["proposal_id"], "integration"),
        "integration receipt read")
    expected = {"kind": "integration", "receipt_id": integration_id,
                "proposal_id": basis["proposal_id"], "actor": participant,
                "disposition": "integrated",
                "candidate_digest": basis["candidate_digest"],
                "target": basis["target"]}
    if recorded is None:
        _refuse("the Authority holds no integration receipt for the terminal "
                "proposal", category="refused", code="precondition")
    for name, value in expected.items():
        if recorded.get(name) != value:
            _refuse(f"the recorded Authority integration receipt disagrees "
                    f"about {name}")
    return recorded


def _terminal(store, manager, delivery, profile, held, entry, integrator,
              basis):
    if entry["state"] == "integrated":
        receipt = _read_integrate_receipt(integrator, basis)
        if held is None:
            _refuse(f"integrated entry {name_value(entry['entry_id'])} has no "
                    f"lease whose terminal ending can be proved")
        if held["entry_id"] != entry["entry_id"]:
            _refuse(f"lease {name_value(held['lease_id'])} is over entry "
                    f"{name_value(held['entry_id'])}, not integrated entry "
                    f"{name_value(entry['entry_id'])}")
        if held["canonical_target_id"] != entry["canonical_target_id"]:
            _refuse(f"lease {name_value(held['lease_id'])} is over target "
                    f"{name_value(held['canonical_target_id'])}, not the "
                    f"integrated entry's target "
                    f"{name_value(entry['canonical_target_id'])}")
        if held["state"] == "live":
            # SETTLEMENT AND RELEASE ARE TWO DURABLE COORDINATOR ACTS. A
            # process may die after the first, leaving this terminal entry
            # behind its still-live exclusion. Reconstruct the owner-bound
            # assignment and replay the stored settlement: the first act is
            # already journalled, and the second drains the exact lease. The
            # Authority receipt above is READ ONLY on this restart path.
            assignment = _existing_assignment(profile, held)
            execution.complete_integrated(store, assignment,
                                          entry["settlement"])
        elif held["state"] != "released":
            _refuse(f"integrated entry {name_value(entry['entry_id'])} has "
                    f"lease {name_value(held['lease_id'])} in state "
                    f"{name_value(held['state'])}; terminal replay owns only "
                    f"a live release tail or an already released lease")
        return {"outcome": "integrated", "entry": entry["entry_id"],
                "assignment": None, "observed": None,
                "authority_receipt": receipt}
    if entry["state"] == "refused":
        return {"outcome": "refused", "entry": entry["entry_id"],
                "assignment": None, "observed": None,
                "authority_receipt": None}
    if entry["state"] == "held":
        if held is None:
            _refuse(f"entry {name_value(entry['entry_id'])} is held without "
                    "the lease whose fence owns its recovery")
        assignment = _existing_assignment(profile, held)
        status = (None if delivery is None else
                  recovery.held_status(store, manager, delivery, assignment))
        return {"outcome": "held", "entry": entry["entry_id"],
                "assignment": assignment, "observed": status,
                "authority_receipt": None}
    return None


def admit_accepted(store, manager, jobs, authority, verification, reviewer,
                   approver, integrator, port, *, canonical_target_id,
                   line_id, proposal_id, policy_generation, profile,
                   attempt_id, launch_root, workspace_group, required_tests):
    """Write accepted receipts and drive or adopt one serialized integration.

    No identity or fence is accepted from the caller.  Entry and lease
    identities are derived from the re-resolved accepted account and the
    manager-owned integration attempt.  A retained delivery with a runtime
    that may have been asked is never run again: it is handed to the accepted
    interrupted-hold operation.
    """
    boundaries.capability(getattr(store, "_connection", None),
                          "the integration coordinator store")
    boundaries.capability(getattr(manager, "_connection", None),
                          "the Worker Manager store")
    boundaries.capability(getattr(jobs, "_connection", None),
                          "the Job store")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.identity(attempt_id, "an integrator attempt id")
    _capability(port, "run", "the integration runtime port")
    taken_profile = runtime._owned_profile(profile)
    _capability(integrator, "integrate",
                "the configured integration session")
    _capability(integrator, "receipt",
                "the configured integration session")
    integration_participant = boundaries.text(
        getattr(integrator, "participant", None),
        "the configured integration participant")
    if integration_participant != taken_profile["integrator_participant"]:
        _refuse("the integration session and runtime profile name different "
                "participants", category="policy", code="denied")
    accepted, proposal, receipts = _accepted_receipts(
        manager, authority, verification, reviewer, approver,
        line_id=line_id, proposal_id=proposal_id,
        policy_generation=policy_generation, required_tests=required_tests)

    account = resolved_account(manager, jobs, authority, line_id=line_id,
                               proposal_id=proposal_id)
    identity_basis = {"canonical_target_id": canonical_target_id,
                      "eligibility": account}
    entry_id = _identity("entry", identity_basis)
    lease_basis = dict(identity_basis, entry_id=entry_id,
                       attempt_id=attempt_id)
    lease_id = _identity("lease", lease_basis)
    admit_candidate(
        store, manager, jobs, authority,
        canonical_target_id=canonical_target_id, entry_id=entry_id,
        line_id=line_id, proposal_id=proposal_id)
    # `enqueue` replay returns its immutable FIRST result (`queued`) even when
    # the entry has since settled. Terminal dispatch needs the coordinator's
    # current semantic state, cross-bound to the newly resolved account, not
    # that historical operation result.
    entry = _current_entry(store, canonical_target_id, entry_id, account)
    basis = {"proposal_id": proposal_id, "entry_id": entry_id,
             "candidate_digest": proposal["candidate_digest"],
             "target": proposal["target"],
             "checkpoint_id": accepted["checkpoint_id"],
             "verdict_id": accepted["verdict_id"]}

    held = lease_of(store, lease_id)
    delivery = runtime.adopt_delivery(
        launch_root, attempt_id=attempt_id, workspace_group=workspace_group)
    terminal = _terminal(store, manager, delivery, taken_profile, held, entry,
                         integrator, basis)
    if terminal is not None:
        return dict(terminal, receipts=receipts)

    if held is not None:
        target = target_of(store, canonical_target_id)
        assignment = _existing_assignment(taken_profile, held)
        if target is not None and target["state"] == "blocked":
            answer = recovery.held_status(store, manager, delivery, assignment)
            return {"outcome": "held", "entry": entry_id,
                    "assignment": assignment, "observed": answer,
                    "authority_receipt": None, "receipts": receipts}
        if held["state"] != "live":
            _refuse(f"lease {name_value(lease_id)} is {held['state']} while "
                    f"entry {name_value(entry_id)} is {entry['state']}")
        if held["entry_id"] != entry_id:
            _refuse(f"lease {name_value(lease_id)} is over entry "
                    f"{name_value(held['entry_id'])}, not this proposal's "
                    f"entry {name_value(entry_id)}")
        assignment = runtime.compose_assignment(
            store, manager, profile=taken_profile,
            canonical_target_id=canonical_target_id, entry_id=entry_id,
            lease_id=lease_id, fence=held["fence"], attempt_id=attempt_id)
        if delivery is None:
            answer = execution.integrate_next(
                store, manager, jobs, authority, port,
                canonical_target_id=canonical_target_id,
                entry_id=entry_id,
                profile=taken_profile,
                lease_id=lease_id, attempt_id=attempt_id,
                launch_root=launch_root, workspace_group=workspace_group)
        else:
            witness = runtime.prior_runtime_witness(manager, attempt_id)
            observed = runtime.observed_delivery(delivery, assignment)
            if witness["execution_runtime"] != execution.UNSTARTED:
                status = recovery.hold_interrupted(
                    store, manager, delivery, assignment)
                answer = {"outcome": "held", "entry": entry_id,
                          "assignment": assignment, "observed": status}
            elif observed["state"] not in ("not-assigned", "waiting"):
                status = recovery.hold_interrupted(
                    store, manager, delivery, assignment)
                answer = {"outcome": "held", "entry": entry_id,
                          "assignment": assignment, "observed": status}
            else:
                current = resolved_account(manager, jobs, authority,
                                           line_id=line_id,
                                           proposal_id=proposal_id)
                _same_account(entry, current)
                runtime.publish_assignment(delivery, assignment)
                live_grant(store, lease_id=lease_id,
                           canonical_target_id=canonical_target_id,
                           entry_id=entry_id, fence=held["fence"])
                port.run(delivery, assignment)
                answer = execution.settle_observed(store, manager, delivery,
                                                   assignment)
    else:
        answer = execution.integrate_next(
            store, manager, jobs, authority, port,
            canonical_target_id=canonical_target_id, entry_id=entry_id,
            profile=taken_profile,
            lease_id=lease_id, attempt_id=attempt_id,
            launch_root=launch_root, workspace_group=workspace_group)

    receipt = None
    if answer["outcome"] == "integrated":
        try:
            receipt = _integrate_receipt(integrator, basis)
            execution.complete_integrated(store, answer["assignment"],
                                          answer["settlement"])
        except ContractRefusal:
            standing = [one for one in entries_of(
                store, canonical_target_id) if one["entry_id"] == entry_id]
            if len(standing) != 1:
                _refuse(f"target {name_value(canonical_target_id)} does not "
                        f"hold exactly one entry "
                        f"{name_value(entry_id)} after completion refused")
            if standing[0]["state"] == "integrated":
                # Settlement committed, so this is no longer a recoverable
                # leased entry and `hold_interrupted` cannot own it. Preserve
                # the live exclusion and fail closed; the terminal restart
                # path above replays the settlement and drains its release.
                raise
            status = recovery.hold_interrupted(
                store, manager, delivery or runtime.adopt_delivery(
                    launch_root, attempt_id=attempt_id,
                    workspace_group=workspace_group), answer["assignment"])
            return dict(answer, outcome="held", observed=status,
                        authority_receipt=None, receipts=receipts)
    return dict(answer, authority_receipt=receipt, receipts=receipts)
