"""W39358 — the minimal supervised dogfood operator.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-minimal-supervised-operator/`.

WHAT THIS IS. One documented composition of capabilities other Work already
delivered and other Work already reviewed: the accepted Worker Manager
lifecycle (W6636), the Docker worker-entry transport (W39356) and the real
Claude worker image (W39357). It is a DEPLOYMENT, and the whole of its value
is that it is the only place where those three meet.

WHAT IT IS EMPHATICALLY NOT, and each line is a boundary somebody could
reasonably have crossed:

  NOT A SECOND MANAGER. Every durable decision here goes through a public
  `baton_v12.worker_manager` operation. This module journals nothing, opens no
  control store table, recomputes no signature and invents no state. If a
  question can only be answered by reaching past those operations, that
  inability is the finding.
  NOT AN AUTHORITY. `DeploymentSession` is a FACADE over one already-minted
  `baton_v12.authority.Session`; it mints nothing and widens nothing.
  NOT A MERGE TOOL. It derives the candidate's diff and the task's own
  verification result INDEPENDENTLY, and it never stages, merges, or writes
  into the canonical checkout. What it produces is a proposal an operator
  reads.
  NOT AN AUTHORIZATION. Every grant is an explicit operand: the exact source
  subset, the frozen task, the image DIGEST, the engine, the manager's own
  roots, the configured workspace group, the credential source and the network
  name. There is no home credential, no mutable image tag and no open-network
  default anywhere in this file, because a default is a grant nobody made.

THE ORDER, and it is the accepted arc rather than this module's invention:

  1. offer, accept, record, claim, activate       -- the authority half
  2. workspace roots, input root, staged source   -- the delivery half
  3. launch document, credential delivery         -- the two manager roots
  4. runtime start, worker-entry conversation     -- the one container
  5. freeze, intake, retention                    -- output custody
  6. destroy, positive absence, teardown          -- the ending

WHAT AN UNRESOLVED ATTEMPT IS. Whenever runtime absence, output custody or
credential cleanup cannot be PROVED, this reports `unresolved` and says which
proof is missing. It never relabels an unproved ending as a clean one -- that
is the one failure mode a supervised pilot must not have, because the operator
reading the evidence is deciding whether to run another.
"""

import json
import os
import re

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts import validate_fragment as _validate_fragment
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.oci import _network as _engine_network
from baton_v12.worker_manager.authority_port import SESSION_OPERATIONS

__all__ = ["DeploymentSession", "MAX_SOURCE_ENTRIES", "MAX_SOURCE_BYTES",
           "PROPOSAL_TARGET", "POLICY_DIGESTS", "SOURCE_TARGET",
           "OperatorRefusal", "assignment_manifest", "frozen_task",
           "held_task", "input_manifest", "preflight", "stage_source"]


# WHERE THE STAGED SOURCE LANDS INSIDE THE INPUT ROOT, and it is fixed for the
# reason every other path in this campaign is: a path a payload can vary is a
# path a runtime can be pointed at wrongly. `claude_agent.SOURCE_ROOT` is the
# other half of this agreement and holds the same constant by equality.
SOURCE_TARGET = "source"

# WHERE THE PROPOSAL LANDS, relative to the fixed `/output` root. The parent
# finding's accepted tree is `/output/proposal/`, and W39357's adapter joins
# the declared path directly below `/output` -- so this is the same constant
# seen from the two ends of one agreement.
PROPOSAL_TARGET = "proposal"

# WHAT A DIGEST LOOKS LIKE. Held on the way in because every policy identity
# this deployment names is one it is accountable for, and "sha256:" plus 64
# hex is what the manager compares.
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")

# WHAT THE OPERATOR MAY STAGE, bounded on both axes at the party that walks
# it. The manager bounds its own roots; this is the second bound, at the one
# place a human names a directory.
MAX_SOURCE_ENTRIES = 2000
MAX_SOURCE_BYTES = 64 * 1024 * 1024


class OperatorRefusal(Exception):
    """Something this operator will not proceed from.

    Deliberately not a `ContractRefusal`: those are the manager's judgements
    about its own contracts, and this one is a deployment saying it was asked
    for something it does not do. Conflating them would let an operator
    mistake a composition mistake for a protocol refusal.
    """


class DeploymentSession:
    """The authority face this deployment gives the manager, and no more.

    SIX MEMBERS DELEGATE, one refuses. `AuthorityPort` names exactly seven
    session operations and checks all of them are callable at construction, so
    a facade that simply omitted `publish_answer` would be refused before the
    first offer -- and one that quietly forwarded it would be promising a
    Baton publication this pilot does not perform.

    WHY `publish_answer` IS A TYPED REFUSAL RATHER THAN A NO-OP. It is the
    manager's route for a conversational `inquire` answer, and this pilot runs
    no `inquire` at all. A no-op would answer "published" to something nobody
    published; a refusal says the deployment does not carry that capability,
    which is true and is what an operator needs to read.

    IT MINTS NOTHING. What it holds is one already-minted participant-bound
    `Session`; there is no route from here to a second one, which is the
    property the authority's own mint rule exists to give.
    """

    def __init__(self, session):
        for member in SESSION_OPERATIONS:
            if member == "publish_answer":
                continue
            if not callable(getattr(session, member, None)):
                raise OperatorRefusal(
                    f"the authority session this deployment was given has no "
                    f"callable {member}; a facade cannot supply an operation "
                    f"the session it delegates to does not have")
        self._session = session

    @property
    def participant(self):
        """The bound identity, read from the session rather than configured."""
        return self._session.participant

    def project_work(self, *arguments):
        return self._session.project_work(*arguments)

    def slot_holder(self, *arguments):
        return self._session.slot_holder(*arguments)

    def claim(self, *documents):
        return self._session.claim(*documents)

    def settle_operation(self, *documents):
        return self._session.settle_operation(*documents)

    def assignment_of(self, *arguments):
        return self._session.assignment_of(*arguments)

    def cancel(self, *documents):
        return self._session.cancel(*documents)

    def publish_answer(self, *documents):
        """The one member this deployment does not carry."""
        raise OperatorRefusal(
            "this dogfood deployment publishes no conversational answer: it "
            "runs no `inquire`, so there is no answer to publish and a "
            "successful-looking no-op would be a publication nobody made")


def preflight(*, task, policies, worker_image_digest, toolchain_digest,
              runtime_profile_digest, role_instructions_digest,
              record_binding, network):
    """EVERY EXPLICIT OPERAND, HELD BEFORE ANYTHING IS STAGED OR STARTED.

    Review 2026-08-30T05:53:19Z [P1]. The first round put the policy check
    inside `input_manifest`, which takes the already-produced staged manifest
    -- so the record claimed a refusal happened "while nothing has been
    staged" and the code could not deliver it. **Superseded:** that claim.
    This is the pure preflight it described, and it runs before
    `stage_source` writes anything.

    IT HOLDS VALUES AND NOT ONLY KEYS, which was the other half of the
    finding. `policy_digest="not-a-digest"` passed a key check and was left
    for the manager to refuse after the delivery existed; every digest operand
    is held to its shape here.

    IT DOES NOT VALIDATE THE TASK'S CONTENT, only that it is a task this
    deployment reads -- `frozen_task` owns that and is called with the
    operator's path. What this adds is that the task is checked in the same
    act as everything else, so one refusal reports the whole preflight rather
    than one operand at a time.
    """
    faults = _held_identities(
        policies=policies, worker_image_digest=worker_image_digest,
        toolchain_digest=toolchain_digest,
        runtime_profile_digest=runtime_profile_digest,
        role_instructions_digest=role_instructions_digest,
        record_binding=record_binding)
    # THE NETWORK IS A NAME AND NEVER A DEFAULT, and it is held to the
    # ENGINE'S OWN GRAMMAR rather than to a second one written here. Review
    # 2026-08-30T06:05:02Z [P1]: any non-empty string passed, including
    # `--network=host`, `../bridge` and `two words`, and `oci._network`
    # refused them only when the runtime vector was composed. Reusing that
    # owner is what keeps the operator and the adapter from drifting.
    try:
        _engine_network(network)
    except ContractRefusal:
        # EXACTLY THE TYPED OUTCOME, and nothing else. Review
        # 2026-08-30T06:20:54Z [P2]: `except Exception` here turned an
        # implementation defect in the owner into an `OperatorRefusal`, which
        # tells a human to edit a grant that is fine and hides the boundary
        # that actually failed. `OperatorRefusal`'s own docstring draws that
        # distinction; catching broadly erased it.
        faults.append("the engine network is one engine network name, named "
                      "explicitly")
    # THE WHOLE TASK, not its schema. See `held_task`.
    try:
        held_task(task)
    except OperatorRefusal as refused:
        faults.append(str(refused))
    if faults:
        raise OperatorRefusal(
            "this operator will not stage or start anything until every "
            "grant it was given is one it can name: " + "; ".join(faults))
    return True


def _held_identities(*, policies, worker_image_digest, toolchain_digest,
                     runtime_profile_digest, role_instructions_digest,
                     record_binding):
    """The digest and record-binding half of the preflight, as a fault list.

    Split out so `input_manifest` can apply the same hold at the composer
    without being handed a task it does not have. One owner, two callers, and
    no second spelling of what a policy identity is.
    """
    faults = []
    # THE CONTAINER BEFORE ITS CONTENTS. Review 2026-08-30T06:05:02Z [P1]:
    # `policies=None` leaked `TypeError` and a string leaked `ValueError`, so
    # the public promise of one collected `OperatorRefusal` over explicit
    # grants was false for exactly the operands most likely to arrive wrong.
    if type(policies) is not dict:
        raise OperatorRefusal(
            f"the policy identities are one document naming "
            f"{', '.join(POLICY_DIGESTS)}; this is a "
            f"{type(policies).__name__}")
    missing = sorted(one for one in POLICY_DIGESTS if one not in policies)
    extra = sorted(one for one in policies if one not in POLICY_DIGESTS)
    if missing or extra:
        faults.append(
            "the policy identities are exactly "
            + ", ".join(POLICY_DIGESTS)
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    named = dict(policies)
    named.update({"worker_image_digest": worker_image_digest,
                  "toolchain_digest": toolchain_digest,
                  "runtime_profile_digest": runtime_profile_digest,
                  "role_instructions_digest": role_instructions_digest})
    for name in sorted(named):
        value = named[name]
        if type(value) is not str or not _DIGEST.match(value):
            faults.append(f"{name} is not a sha256 digest")
    # THE RECORD BINDING'S VALUES, not only its four names. Review
    # 2026-08-30T06:05:02Z [P1]: four correctly named members passed with a
    # malformed digest, an empty root or an absolute path, and the frozen
    # input-manifest schema refused them only after the source was staged.
    if type(record_binding) is not dict \
            or sorted(record_binding) != sorted(_RECORD_BINDING):
        faults.append("the record binding is exactly "
                      + ", ".join(_RECORD_BINDING))
    else:
        for name in ("finding_digest", "plan_digest"):
            value = record_binding[name]
            if type(value) is not str or not _DIGEST.match(value):
                faults.append(f"the record binding's {name} is not a sha256 "
                              f"digest")
        # THE FROZEN CONTRACT'S OWN GRAMMAR, through its own owner. Review
        # 2026-08-30T06:13:35Z [P1]: the previous cut wrote an approximation
        # here -- any non-empty string as the root, `posixpath.normpath` plus
        # a few exclusions as the path -- so a root with spaces or 161
        # characters, and a path of `.`, with a backslash, with a NUL or 513
        # characters long, all reached `_sealed`, which refused them AFTER
        # `stage_source` had created the delivery. That is exactly the
        # interval this preflight exists to remove, and the record's claim
        # that both locators were held by value was stronger than the code.
        #
        # `validate_fragment` is the frozen document's own `$defs` owner, and
        # reusing it is the same rule the network operand is under: a second
        # approximation maintained here is a second grammar with nothing
        # comparing the two.
        for name, definition in (("root", "opaqueId"),
                                 ("path", "relativePath")):
            try:
                _validate_fragment(record_binding[name], definition,
                                   what=f"the record binding's {name}")
            except ContractRefusal as refused:
                # THE CONTRACT'S OWN SENTENCE, not a summary of it. The
                # refusal text is composed by the frozen validator and says
                # which rule the value broke, which is what an operator needs
                # to fix a launch; a class name would send them reading this
                # file instead of their own document.
                #
                # AND ONLY THE TYPED OUTCOME REACHES IT. Review
                # 2026-08-30T06:20:54Z [P2]: `except Exception` relabelled an
                # owner's implementation defect as a malformed grant, which is
                # the one thing `OperatorRefusal` is documented not to be.
                faults.append(f"the record binding's {name} is not a "
                              f"{definition}: {refused.message}")
    return faults


_RECORD_BINDING = ("root", "path", "finding_digest", "plan_digest")


def stage_source(source, inputs, *, max_entries=MAX_SOURCE_ENTRIES,
                 max_bytes=MAX_SOURCE_BYTES):
    """The exact source subset, copied into the input root, bounded.

    THROUGH THE MANAGER'S OWN COPIER. `workspaces.copied_manifest` is the
    reviewed bounded no-follow path -- it refuses a link at any depth, counts
    what it walks and answers a manifest of what it copied. Writing a second
    copier here would be a second party deciding what a delivery is, which is
    the first defect this campaign found.

    STAGED INTO THE INPUT ROOT AND NOWHERE ELSE. The input root is mounted
    read-only at `/input`, so the worker sees `/input/source` and cannot write
    to it; the adapter copies it into container-private scratch before the
    provider touches anything.
    """
    # THE OPERATOR CONSTANTS ARE A CEILING, not a default. Review
    # 2026-08-30T05:53:19Z [P1]: these were forwarded unchanged, so a caller
    # could widen the bound this module states -- which makes a stated bound
    # a suggestion. A LOWER value is still accepted, because a test or a
    # cautious operator narrowing its own delivery takes nothing away.
    # A NARROWED CEILING IS STILL A CEILING. Review 2026-08-30T06:05:02Z [P2]:
    # this accepted booleans and zero and leaked `TypeError` for text, and one
    # boolean reached `copied_manifest` and surfaced in a manager refusal as a
    # limit of `True` files. Positive exact integers, by the manager's own rule
    # for every other seconds-or-count operand.
    for name, value in (("max_entries", max_entries),
                        ("max_bytes", max_bytes)):
        if type(value) is not int or type(value) is bool or not 0 < value:
            raise OperatorRefusal(
                f"{name} is a positive whole number; this is "
                f"{type(value).__name__} {value!r}")
    if max_entries > MAX_SOURCE_ENTRIES or max_bytes > MAX_SOURCE_BYTES:
        raise OperatorRefusal(
            f"this operator stages at most {MAX_SOURCE_ENTRIES} entries and "
            f"{MAX_SOURCE_BYTES} bytes; a caller may narrow that and may not "
            f"widen it, because a bound a caller can raise is not one this "
            f"module states")
    place = os.path.join(inputs, SOURCE_TARGET)
    if os.path.exists(place):
        raise OperatorRefusal(
            f"{place} already exists; an attempt stages its source once, and "
            f"a second staging into a live input root would be replacing a "
            f"delivery the manager has already measured")
    return workspaces.copied_manifest(source, place, max_entries=max_entries,
                                      max_bytes=max_bytes)


def frozen_task(place):
    """The operator's frozen task document, read and held to its own shape.

    READ HERE AND VALIDATED HERE rather than passed through. The adapter holds
    it to `baton.dogfood-task/1` inside the container, and this reads it on the
    way in so an operator learns about a malformed task before a container
    starts rather than from a failed attempt's evidence.

    IT IS THE OPERATOR'S DOCUMENT. This module does not compose one, because
    a task an operator did not write is a task nobody chose.
    """
    try:
        with open(place, "rb") as reading:
            raw = reading.read(1 << 20)
    except OSError as failed:
        raise OperatorRefusal(
            f"this operator has no readable frozen task at {place} "
            f"({type(failed).__name__}); the task is the operator's own "
            f"document and is named explicitly") from None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise OperatorRefusal(f"{place} is not a readable document") from None
    return held_task(document, what=place)


def held_task(document, *, what="the frozen task"):
    """ONE task hold, applied everywhere a task is believed.

    Review 2026-08-30T06:05:02Z [P1]. `frozen_task` answered an ordinary
    mutable dict, `preflight` re-checked only its `schema`, and `_copied_task`
    serialized whatever it was handed -- so a task could be read valid, have
    its identity, instructions, verification vector or source root changed,
    pass preflight and be copied into `/input/task.json` as the changed thing.
    **Checking the schema a second time is not the same hold**, which is the
    review's own sentence and the reason this function exists.

    So there is one hold and it is applied at every place a task is believed:
    the first read, the preflight, and immediately before the copy. It is a
    pure function over a document, which is what lets it be applied three
    times without three chances to disagree.

    THE SAME CHECKS THE WORKER MAKES. `claude_agent._task` holds the identity
    grammar, the non-empty text and the non-empty list of words inside the
    container; an operator read that accepted what the container rejects would
    move the promised refusal back to the failed provider attempt it exists to
    avoid.
    """
    if type(document) is not dict:
        raise OperatorRefusal(f"{what} is one JSON object")
    missing = sorted(one for one in _TASK_MEMBERS if one not in document)
    extra = sorted(one for one in document if one not in _TASK_MEMBERS)
    if missing or extra:
        raise OperatorRefusal(
            f"{what} is exactly {', '.join(_TASK_MEMBERS)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if document["schema"] != _TASK_SCHEMA:
        raise OperatorRefusal(
            f"{what} says it is {document['schema']!r} and this deployment "
            f"stages {_TASK_SCHEMA!r}")
    if type(document["task_id"]) is not str \
            or not _TASK_ID.match(document["task_id"]):
        raise OperatorRefusal(f"{what} carries no usable task identity")
    for name in ("instructions", "source_root"):
        if type(document[name]) is not str or not document[name]:
            raise OperatorRefusal(
                f"{what} carries a {name} that is not bounded non-empty text")
    verification = document["verification"]
    if type(verification) is not list or not verification \
            or not all(type(one) is str and one for one in verification):
        raise OperatorRefusal(
            f"{what} carries a verification that is a non-empty list of "
            f"words; a command anybody has to assemble from a string is a "
            f"shell, and there is no shell in the worker")
    if document["source_root"] != SOURCE_TARGET:
        raise OperatorRefusal(
            f"{what} names source_root {document['source_root']!r} and this "
            f"deployment stages exactly {SOURCE_TARGET!r}")
    return document


# THE FROZEN TASK'S CONTRACT, and it is W39357's rather than this module's.
# Held here by equality so a document from another generation is refused on
# the way in; `v12/worker/claude_agent.py` holds the same closed set at the
# receiving end, which is the both-ends rule this campaign applies to every
# crossing.
_TASK_SCHEMA = "baton.dogfood-task/1"
_TASK_MEMBERS = ("schema", "task_id", "instructions", "verification",
                 "source_root")
_TASK_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\Z")


def _copied_task(document, inputs):
    """The frozen task, delivered beside the staged source.

    Written by this operator rather than by the manager, for the reason the
    parent finding gives: the task is a WORKLOAD convention and not
    worker-control protocol vocabulary, so the manager neither reads it nor
    carries it in its documents.
    """
    # HELD IMMEDIATELY BEFORE THE WRITE. Review 2026-08-30T06:05:02Z [P1]:
    # this serialized whatever it was handed, so a task read valid earlier and
    # changed afterwards was copied as the changed thing. The hold is the same
    # one `frozen_task` and `preflight` apply -- one function, three places, no
    # chance for three answers.
    document = held_task(document, what="the task being staged")
    place = os.path.join(inputs, "task.json")
    with open(place, "w", encoding="utf-8") as writing:
        json.dump(document, writing, sort_keys=True)
    os.chmod(place, 0o444)
    return place


POLICY_DIGESTS = ("policy_digest", "resource_policy_digest",
                  "network_policy_digest", "mount_policy_digest",
                  "tool_policy_digest", "credential_policy_digest",
                  "retention_policy_digest")


def input_manifest(*, work_ref, staged, created_at, manifest_id,
                   assignment_contract, human_contract, record_binding,
                   role_instructions_digest, runtime_profile_digest,
                   toolchain_digest, worker_image_digest, policies):
    """The manager-authored input manifest for one dogfood attempt.

    COMPOSED HERE BECAUSE THE MANAGER DOES NOT COMPOSE IT. `compose_input_root`
    takes both protocol documents as operands, so the party that knows what
    this delivery IS -- the deployment -- authors them, and the manager holds
    the root against what it was handed.

    EVERY POLICY IDENTITY IS AN OPERAND. The frozen schema requires seven of
    them plus the toolchain, the image and the record binding, and each names
    something the deployment is accountable for. A tool that filled one in
    would be making a grant on an operator's behalf, which is the one thing
    the parent finding forbids this composition to do.

    THE `sources` ENTRY DESCRIBES THE STAGED TREE and its `content_manifest`
    is the one `copied_manifest` answered, not a second measurement. A
    deployment that measured the tree twice would be two parties disagreeing
    about one delivery, which is the defect the manager's own copier exists to
    prevent.

    BOTH PATHS ARE RELATIVE TO A FIXED ROOT, and the first round got both
    wrong. `destination` is below `/input` and `path` is below `/output` --
    `contracts/manifest.py` says so where it checks their overlap, W39357's
    adapter reads `/input/source` and joins the declared output path directly
    below `/output`, and the parent finding's accepted proposal is at
    `/output/proposal`. The first cut wrote `workspace/source` and
    `workspace/proposal`, copied from a conformance vector, which described a
    delivery at `/input/workspace/source` that nothing makes and asked the
    worker to write somewhere nobody collects.

    **Superseded:** the first round's claim that `sources[].destination` is
    "consumed by nothing". It is not a materialization instruction in this
    build -- nothing copies a source to it -- but the MANIFEST RULES read it,
    and it is the durable description of the staged delivery. Filling it
    truthfully matters for that reason rather than merely for tidiness.

    THE FROZEN TASK'S IDENTITY IS NOT IN HERE, and that is the schema's ruling
    rather than a preference. `baton.worker-manifest/input` is closed and
    carries no task member; the task is a WORKLOAD convention that travels in
    `/input/task.json`, the same boundary the parent finding draws for Git. A
    first cut of this function added `task_id` and `compose_input_root` refused
    the document -- recorded because a reader will wonder where the task went.
    """
    # THE SAME HOLD, AGAIN, AT THE COMPOSER. `preflight` is where an operator
    # learns about a bad grant before anything is staged; this is the second
    # party proving it rather than assuming the first did, which is the rule
    # the manager applies to its own roots.
    faults = _held_identities(
        policies=policies, worker_image_digest=worker_image_digest,
        toolchain_digest=toolchain_digest,
        runtime_profile_digest=runtime_profile_digest,
        role_instructions_digest=role_instructions_digest,
        record_binding=record_binding)
    if faults:
        raise OperatorRefusal(
            "an input manifest carries identities this deployment named: "
            + "; ".join(faults))
    return _sealed({
        "version": {"major": 1, "minor": 0},
        "manifest_id": manifest_id,
        "created_at": created_at,
        "extensions": {},
        "schema": "baton.worker-manifest/input",
        "work_ref": dict(work_ref),
        "assignment_contract": assignment_contract,
        "human_contract": dict(human_contract),
        "record_binding": dict(record_binding),
        "sources": [{"name": SOURCE_TARGET,
                     "destination": SOURCE_TARGET,
                     "required": True,
                     "content_manifest": staged,
                     "consumption": {"baton.directory/1": {"layout": "flat"}}}],
        "outputs": [{"name": PROPOSAL_TARGET,
                     "type": "directory-result",
                     "path": PROPOSAL_TARGET, "required": True,
                     "constraints": {"max_bytes": MAX_SOURCE_BYTES,
                                     "max_entries": MAX_SOURCE_ENTRIES,
                                     "allowed_media_types":
                                         ["application/octet-stream",
                                          "text/plain"],
                                     "link_policy": "forbid",
                                     "validator_digest": None}}],
        "role_instructions_digest": role_instructions_digest,
        "runtime_profile_digest": runtime_profile_digest,
        "toolchain_digest": toolchain_digest,
        "worker_image_digest": worker_image_digest,
        **dict(policies)})


def assignment_manifest(*, given, work_ref, participant, generation,
                        attempt_id, offer_id, claim_receipt_digest,
                        claim_event_seq, created_at, activated_at,
                        assignment_contract, manifest_id):
    """The assignment minted for THIS attempt against THAT input manifest."""
    return _sealed({
        "version": {"major": 1, "minor": 0},
        "manifest_id": manifest_id,
        "created_at": created_at,
        "extensions": {},
        "schema": "baton.worker-manifest/assignment",
        "assignment_ref": {"work_ref": dict(work_ref),
                           "participant": participant,
                           "generation": generation},
        "assignment_contract": assignment_contract,
        "offer_id": offer_id,
        "runtime_attempt_id": attempt_id,
        "input_manifest_digest": given["manifest_digest"],
        "policy_digest": given["policy_digest"],
        "runtime_profile_digest": given["runtime_profile_digest"],
        "claim_receipt_digest": claim_receipt_digest,
        "claim_event_seq": claim_event_seq,
        "activated_at": activated_at})


def _sealed(document):
    """The document's own digest, over the document without it.

    Through the contracts package's canonical digest rather than a local
    hash: the manager recomputes it with that one, and two spellings of one
    digest is two documents.
    """
    from baton_v12.contracts import digest

    document.pop("manifest_digest", None)
    document["manifest_digest"] = digest(document)
    return document


# THE ONE DECLARED OUTPUT'S NAME, and the three files an operator reads out of
# it. `result.json` and `change.patch` are the WORKER's account and are never
# what this operator trusts -- the parent finding says so in terms, and
# `_derived` below is why: the diff and the verification are recomputed here
# from the collected bytes.
PROPOSAL_MEMBERS = ("candidate", "change.patch", "result.json",
                    "verification.txt")

# THE WORKER'S OWN PROGRAM, and the bound one conversation is given. Both are
# this deployment's constants rather than operands: the program is W6633's
# file at the image's own path, and a conversation a caller could lengthen is
# a bound a caller could remove.
WORKER_PROGRAM = ["python3", "/opt/baton/baton_worker.py"]
CONVERSATION_SECONDS = 3900

# WHAT THE CONVERSATION ASKS FOR, in order. `describe` first because a worker
# that cannot describe itself is one this operator should not hand an
# assignment to, and the ordering is the transport's own: one exec session,
# two correlated operations, each consumed once.
CONVERSATION = ("describe", "work")


def run_dogfood_task(*, engine, run, open_channel, store, port, adapter_of,
                     attempt_id, offer_id, source, task_path, storage,
                     launch_home, credential_delivery, image_digest, network,
                     work_ref, participant, generation, now, policies,
                     record_binding, assignment_contract, human_contract,
                     role_instructions_digest, runtime_profile_digest,
                     toolchain_digest, adapter_digest, adapter_name,
                     labels, retention_policy_digest, bearer,
                     seconds=CONVERSATION_SECONDS):
    """ONE supervised dogfood attempt, composed from public operations only.

    THE ORDER IS THE ACCEPTED ARC and this function's whole job is to be the
    one place it is written down: authority half, delivery half, the two
    manager roots, one container and one conversation, output custody, and
    the ending. Every step is a `baton_v12.worker_manager` operation; nothing
    here journals, reads a control-store table, or invents a state.

    IT ANSWERS EVIDENCE AND RAISES NOTHING IT CAN ACCOUNT FOR. What comes back
    is the retained record an operator reads -- identities, dispositions and
    the INDEPENDENTLY derived diff and verification result -- and `resolved`
    is false whenever a proof this arc requires was not obtained.
    """
    from baton_v12.worker_manager import (accept_offer, activate_assignment,
                                          authorize_cleanup, decide_retention,
                                          issue_offer, observe, record_attempt,
                                          reconcile_runtime, request_freeze,
                                          request_intake,
                                          request_runtime_start,
                                          retain_manifest, submit_claim)
    from baton_v12.worker_manager import launch, worker_entry, workspaces

    task = frozen_task(task_path)
    preflight(task=task, policies=policies,
              worker_image_digest=image_digest,
              toolchain_digest=toolchain_digest,
              runtime_profile_digest=runtime_profile_digest,
              role_instructions_digest=role_instructions_digest,
              record_binding=record_binding, network=network)

    # -- the delivery half, before the authority half touches anything ------
    #
    # STAGED FIRST BECAUSE THE OFFER FREEZES ITS DIGEST. `issue_offer` binds
    # the input manifest digest, and the manifest describes the staged tree --
    # so the tree has to exist before there is a digest to freeze.
    group = _configured_group(store)
    roots = workspaces.assignment_workspace(group, storage, attempt_id)
    staged = stage_source(source, roots["inputs"])
    given = input_manifest(
        work_ref=work_ref, staged=staged, created_at=now,
        manifest_id=f"input-{attempt_id}",
        assignment_contract=assignment_contract, human_contract=human_contract,
        record_binding=record_binding,
        role_instructions_digest=role_instructions_digest,
        runtime_profile_digest=runtime_profile_digest,
        toolchain_digest=toolchain_digest, worker_image_digest=image_digest,
        policies=policies)

    # -- the authority half -------------------------------------------------
    issue_offer(store, port, offer_id=offer_id,
                work_id=work_ref["work_id"], runtime_attempt_id=attempt_id,
                input_digest=given["manifest_digest"],
                policy_digest=given["policy_digest"],
                profile_digest=runtime_profile_digest,
                profile_name="dogfood", mint_bearer=lambda: bearer)
    accepted = accept_offer(store, port, offer_id=offer_id, decision="accept",
                            bearer=bearer, now=now,
                            runtime_attempt_id=attempt_id,
                            work_ref=dict(work_ref))
    record_attempt(store, attempt_id=attempt_id, adapter_name=adapter_name,
                   adapter_digest=adapter_digest,
                   profile_digest=runtime_profile_digest,
                   input_digest=given["manifest_digest"],
                   policy_digest=given["policy_digest"])
    # THE CLAIM'S OWN ANSWER IS KEPT. Review 2026-08-30T06:35:56Z [P0]: this
    # discarded it and populated the assignment manifest from the
    # `offer.accepted` document, which carries neither a claim event nor a
    # receipt digest -- so `_claim_receipt` wrote an all-zero digest and
    # `_claim_event` wrote 1. A syntactically valid placeholder in an
    # assignment manifest is INVENTED AUTHORITY EVIDENCE, which is worse than
    # an absent field because it reads as a fact.
    claimed = submit_claim(store, port, offer_id=offer_id)
    expect = {"work_ref": dict(work_ref), "participant": participant,
              "generation": generation}
    activate_assignment(store, port, attempt_id=attempt_id,
                        expect=dict(expect))

    assignment = assignment_manifest(
        given=given, work_ref=work_ref, participant=participant,
        generation=generation, attempt_id=attempt_id, offer_id=offer_id,
        claim_receipt_digest=_claim_receipt(claimed),
        claim_event_seq=_claim_event(claimed), created_at=now,
        activated_at=now, assignment_contract=assignment_contract,
        manifest_id=f"assignment-{attempt_id}")
    workspaces.compose_input_root(
        roots["inputs"], given, assignment,
        assignment=dict(assignment["assignment_ref"]),
        runtime_attempt_id=attempt_id)
    _copied_task(task, roots["inputs"])
    # THE MANAGER HOLDS THE MANIFEST IT WILL COMPARE AGAINST. A freeze refuses
    # an attempt whose input manifest this manager never retained.
    retain_manifest(store, given, "inputManifest")

    # -- the two manager roots, and the one container -----------------------
    delivery = launch.materialize(launch_home, attempt_id=attempt_id,
                                  session=f"session-{attempt_id}",
                                  contract=task["instructions"],
                                  role="implementer")
    declared = [dict(one) for one in given["outputs"]]
    # THE FACTORY IS GIVEN THE SAME GRANTS THIS RUN RECORDS. Review
    # 2026-08-30T06:35:56Z [P1]: it received neither the engine, the resolved
    # image digest, the network nor the labels -- so the evidence could name
    # one image and network while an unchecked closure built an adapter for
    # another. `run` and `labels` were accepted and unused for the same reason
    # and are passed through here rather than dropped, because an adapter that
    # cannot select this attempt's runtimes cannot reconcile them.
    adapter = adapter_of(engine=engine, run=run, image_digest=image_digest,
                         network=network, labels=dict(labels), roots=roots,
                         declared=declared, launch=delivery,
                         credential_delivery=credential_delivery,
                         input_manifest_digest=given["manifest_digest"])
    # THE RUNTIME IDENTITY COMES BACK FROM THE OPERATION, not from a row.
    # `request_runtime_start` journals the start and answers through
    # `reconcile_runtime`, whose `runtime.attached` document carries
    # `runtime_id` -- so the transport's operand is the manager's own answer
    # rather than something this deployment read out of a table it must not
    # open. An UNCERTAIN reconciliation carries no identity, and that is a
    # fact about the attempt rather than a value to go looking for.
    started = request_runtime_start(store, adapter, attempt_id=attempt_id,
                                    inputs=roots["inputs"])
    runtime_id = started.get("runtime_id") if type(started) is dict else None

    if runtime_id is None:
        decided = started.get("decision") if type(started) is dict else None
        raise OperatorRefusal(
            f"the start of attempt {attempt_id} reconciled to "
            f"{decided!r} without naming a runtime; a conversation needs the "
            f"exact runtime, and this deployment does not go looking for one "
            f"the manager did not name")

    evidence = {"schema": "baton.dogfood-evidence/1",
                "attempt_id": attempt_id, "task_id": task["task_id"],
                "input_manifest_digest": given["manifest_digest"],
                "assignment_manifest_digest": assignment["manifest_digest"],
                "source_tree_digest": staged["tree_digest"],
                "worker_image_digest": image_digest, "network": network,
                "runtime_id": runtime_id, "offer_id": offer_id,
                "conversation": None, "worker_disposition": None,
                "output": None, "cleanup": None,
                "independent": None, "resolved": False, "unresolved": []}

    # -- EVERYTHING AFTER THE START IS THE ENDING'S -------------------------
    #
    # Review 2026-08-30T06:44:13Z [P0]: the conversation used to happen HERE,
    # and its two failure branches returned before the guard -- so a container
    # this deployment had started was left running whenever the worker did not
    # answer, which is precisely the case the guard exists for. Successful
    # conversation is not a precondition for entering an ending; a STARTED
    # RUNTIME is.
    return _after_start(store, port, adapter, evidence,
                        engine=engine, open_channel=open_channel,
                        attempt_id=attempt_id, runtime_id=runtime_id,
                        roots=roots, task=task,
                        source=os.path.join(roots["inputs"], SOURCE_TARGET),
                        retention_policy_digest=retention_policy_digest,
                        seconds=seconds)


class _Lost(Exception):
    """One named reason this attempt cannot reach a supervised result.

    Raised rather than returned, so every one of them lands in the same
    ending. The sixth and seventh rounds both claimed a common ending while
    returning around it from three places; an exception is the shape that
    cannot be forgotten at a call site.
    """


def _after_start(store, port, adapter, evidence, *, engine, open_channel,
                 attempt_id, runtime_id, roots, task, source,
                 retention_policy_digest, seconds):
    """ONE owner for every branch after a runtime exists.

    Review 2026-08-30T06:44:13Z [P0], twice over. The conversation was outside
    the guard and the guard's own early returns skipped the ending, so the
    record's "the manager's own cleanup is attempted, whatever happened" was
    stronger than the code for the third round running. Everything is inside
    now, every named reason is raised rather than returned, and the ending
    runs in `finally`.

    AN UNEXPECTED FAULT IS RECORDED AND THEN PROPAGATES. Review [P1]: catching
    every `Exception` turned a `KeyError` in this module into a supervised
    attempt outcome. Cleanup still runs -- that is what `finally` is for -- but
    an implementation defect is not an ending an operator should read as one.
    """
    from baton_v12.worker_manager import worker_entry

    try:
        spoken = worker_entry.converse(
            worker_entry.ChannelPort(open_channel), engine=engine,
            runtime_id=runtime_id, program=WORKER_PROGRAM,
            session=f"session-{attempt_id}", operations=list(CONVERSATION),
            seconds=seconds,
            operation_ids=[f"{one}:{attempt_id}" for one in CONVERSATION])
        evidence["conversation"] = {
            "ending": spoken["ending"], "why": spoken["why"],
            "answered": [one.get("operation") for one in spoken["answers"]]}
        if spoken["ending"] != "answered":
            # THE TRANSPORT'S OWN VOCABULARY, reported rather than translated
            # into a disposition nobody observed.
            raise _Lost(f"the worker-entry conversation ended "
                        f"{spoken['ending']}")
        disposition = _disposition_of(spoken)
        if disposition is None:
            raise _Lost("the worker answered no disposition")
        evidence["worker_disposition"] = disposition
        _custody(store, port, adapter, evidence, attempt_id=attempt_id,
                 runtime_id=runtime_id, task=task, source=source,
                 disposition=disposition,
                 retention_policy_digest=retention_policy_digest)
    except _Lost as why:
        _unresolved(evidence, str(why))
    except ContractRefusal as refused:
        _unresolved(evidence, f"a manager contract declined: "
                              f"{refused.message}")
    except BaseException as failed:                        # noqa: BLE001
        _unresolved(evidence, f"the attempt ended on an unexpected "
                              f"{type(failed).__name__}")
        raise
    finally:
        _ended_however(store, port, adapter, evidence, attempt_id=attempt_id,
                       runtime_id=runtime_id,
                       retention_policy_digest=retention_policy_digest)
    return evidence


def _custody(store, port, adapter, evidence, *, attempt_id, runtime_id,
             task, source, disposition, retention_policy_digest):
    """Quiescence, freeze, intake, the independent derivation, and retention.

    EVERY REASON IT CANNOT PROCEED IS RAISED. `_after_start` owns the ending,
    so nothing here returns early -- the third round in a row that mistake was
    made is the reason this function has no `return` on a failure path at all.
    """
    from baton_v12.worker_manager import (decide_retention, observe,
                                          reconcile_runtime, request_freeze,
                                          request_intake)

    # QUIESCENCE IS ORDERED, NOT WAITED FOR. The accepted transport starts the
    # container INTERACTIVE so idle PID 1 outlives the exec'd worker program,
    # and `reconcile_runtime` observes rather than stops.
    stopped = adapter.stop({"runtime_id": runtime_id,
                            "operation_id": f"quiesce:{attempt_id}"})
    evidence["quiescence"] = {"ordered": stopped.get("ordered"),
                              "state": stopped.get("state"),
                              "why": stopped.get("why")}
    # ONLY `quiescent`, AND `absent` IS NOT THE SAME PROOF. Review
    # 2026-08-30T06:44:13Z [P1]: this accepted both and went on to freeze. The
    # freeze contract takes `quiescent` alone and says why -- a runtime that
    # is merely GONE was never observed to have finished writing, so freezing
    # its output would seal bytes nobody watched the end of.
    if stopped.get("state") != "quiescent":
        raise _Lost(f"the runtime was ordered to stop and observed "
                    f"{stopped.get('state')!r}; a freeze takes a positively "
                    f"quiescent runtime, and an absent one is not the same "
                    f"proof because its writer was never seen to finish")
    reconcile_runtime(store, adapter, attempt_id=attempt_id)
    observe(store, attempt_id=attempt_id, axis="worker_disposition",
            value=disposition)
    request_freeze(store, port, adapter, attempt_id=attempt_id,
                   disposition=disposition)
    receipt = request_intake(store, port, adapter, attempt_id=attempt_id)
    held = list(receipt["artifacts"])
    if not held:
        raise _Lost("intake took custody of nothing, so there is no proposal "
                    "to account for")
    # THE PUBLIC LOCATOR, from the receipt. `intake_artifact` carries
    # `custody_locator` precisely so a caller does not reach into the adapter.
    evidence["custody"] = [{"artifact_id": one["artifact_id"],
                            "content_digest": one["content_digest"],
                            "bytes": one["bytes"]} for one in held]
    # DERIVED BEFORE RETENTION DISCARDS THE BYTES, which is the ordering the
    # parent finding requires.
    evidence["independent"] = _derived(held[0]["custody_locator"], task,
                                       source)
    decide_retention(store, port, adapter, attempt_id=attempt_id,
                     artifact_ids=[one["artifact_id"] for one in held],
                     disposition="discard-after-intake",
                     retention_policy_digest=retention_policy_digest)
    evidence["intake_receipt"] = True


def _ended_however(store, port, adapter, evidence, *, attempt_id, runtime_id,
                   retention_policy_digest):
    """The ending, run whatever happened -- and HONEST about what it can end.

    Review 2026-08-30T06:44:13Z [P0]. The previous `finally` only observed,
    while the record claimed the manager's own cleanup was attempted. It is
    attempted here, through the manager's own operation and never through a
    second deployment-owned destroy.

    AND THERE IS A STATE THIS SURFACE CANNOT END, which is recorded rather
    than worked around. `authorize_cleanup` is authorized by the INTAKE
    RECEIPT; `authorize_failed_start_cleanup` is authorized by the manager's
    own `runtime.start-failed` record; `authorize_refused_session_cleanup` by
    a refused session. An attempt whose runtime STARTED and whose worker then
    failed to answer has none of the three, so no public operation ends it --
    and inventing a destroy here would be exactly the second removal boundary
    a deployment must not grow. That is a MANAGER finding, filed as W44716,
    and until it lands such an attempt is `unresolved` with the runtime named
    so an operator can act on it.
    """
    from baton_v12.contracts import ContractRefusal as _Refusal
    from baton_v12.worker_manager import authorize_cleanup

    # ENDING A STARTED RUNTIME BEGINS BY STOPPING IT, on every path and not
    # only the one that reached the freeze. Review 2026-08-30T06:44:13Z [P0]:
    # a lost conversation left the container running because the only stop was
    # inside the success branch. `adapter.stop` is the manager's own boundary
    # and it both orders and proves, so ordering it again where one already
    # happened would be a second act -- hence the record is what decides.
    if evidence.get("quiescence") is None:
        try:
            stopped = adapter.stop({"runtime_id": runtime_id,
                                    "operation_id": f"quiesce:{attempt_id}"})
            evidence["quiescence"] = {"ordered": stopped.get("ordered"),
                                      "state": stopped.get("state"),
                                      "why": stopped.get("why")}
        except Exception as failed:                        # noqa: BLE001
            evidence["quiescence"] = {"ordered": False,
                                      "state": "unobserved",
                                      "why": type(failed).__name__}
            _unresolved(evidence, f"the runtime could not be ordered to stop "
                                  f"({type(failed).__name__})")
    if evidence.get("intake_receipt"):
        try:
            settled = authorize_cleanup(
                store, port, adapter, attempt_id=attempt_id,
                retention_policy_digest=retention_policy_digest)
            evidence["cleanup"] = {"cleanup": settled.get("cleanup"),
                                   "state": settled.get("state")}
            if settled.get("cleanup") == "complete" \
                    and settled.get("state") == "absent" \
                    and not evidence["unresolved"]:
                evidence["resolved"] = True
            elif settled.get("cleanup") != "complete":
                _unresolved(evidence,
                            f"cleanup ended {settled.get('cleanup')!r} with "
                            f"the runtime {settled.get('state')!r}")
        except _Refusal as refused:
            _unresolved(evidence, f"the manager declined to end the attempt: "
                                  f"{refused.message}")
    else:
        _unresolved(
            evidence,
            "no public manager operation can end an attempt whose runtime "
            "started and whose worker produced no intake receipt: cleanup is "
            "authorized by that receipt, failed-start cleanup by a start "
            "failure that did not happen, and refused-session cleanup by a "
            "refusal that did not happen either. W44716 carries that gap; "
            "this deployment does not grow a second destroy boundary to hide "
            "it")
    evidence["observed_after"] = _observed_after(adapter, runtime_id)


def _observed_after(adapter, runtime_id):
    """What the engine says about the runtime once the arc has finished.

    A READ AND NEVER A REMOVAL. Removing here would be a second destroy
    boundary beside the manager's own, which is the one thing a deployment
    must not grow; what this adds is that an unresolved evidence record says
    whether the container is still running rather than leaving an operator to
    go and look.
    """
    try:
        return dict(adapter.observe(runtime_id))
    except Exception as failed:                            # noqa: BLE001
        return {"state": "unobserved", "why": type(failed).__name__}


def _derived(custody_locator, task, source):
    """The diff and the verification, RECOMPUTED by this operator.

    NEITHER READS THE WORKER'S ACCOUNT. `change.patch` and `result.json` are
    the worker's convenience and are collected as evidence; what an operator
    acts on is this — the candidate tree custody holds, diffed against the
    staged source it was made from, and the task's own frozen command rerun
    OUTSIDE the container over that tree.

    THE LOCATOR IS THE RECEIPT'S. Review [P1]: it used to be derived from the
    adapter's private `_custody`, which is OCI's business and not a
    deployment's.
    """
    import subprocess

    candidate = os.path.join(custody_locator, "candidate")
    changed = sorted(_changed_paths(source, candidate))
    verified = subprocess.run(list(task["verification"]), cwd=candidate,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=900)
    return {"changed_paths": changed,
            "verification_argv": list(task["verification"]),
            "verification_status": verified.returncode,
            "members_present": sorted(
                one for one in PROPOSAL_MEMBERS
                if os.path.exists(os.path.join(custody_locator, one)))}


def _changed_paths(source, candidate):
    """Which staged files the candidate differs from, by BYTES.

    Not by the worker's list and not by a digest the worker computed: the two
    trees are on this host and comparing them is the one derivation nothing
    inside the container can influence.
    """
    import filecmp

    found = set()
    for base, _directories, files in os.walk(source):
        for name in files:
            relative = os.path.relpath(os.path.join(base, name), source)
            theirs = os.path.join(candidate, relative)
            if not os.path.isfile(theirs) or not filecmp.cmp(
                    os.path.join(base, name), theirs, shallow=False):
                found.add(relative)
    for base, _directories, files in os.walk(candidate):
        for name in files:
            relative = os.path.relpath(os.path.join(base, name), candidate)
            if not os.path.isfile(os.path.join(source, relative)):
                found.add(relative)
    return found


def _unresolved(evidence, why):
    """An attempt whose required proof was not obtained, said out loud."""
    evidence["resolved"] = False
    evidence["unresolved"].append(why)
    return evidence


def _configured_group(store):
    from baton_v12.worker_manager import configured_workspace_group

    return configured_workspace_group(store)


def _claim_receipt(claimed):
    """The claim's receipt digest, DERIVED from the authority's own result.

    Review 2026-08-30T06:35:56Z [P0]. There is no placeholder branch, and that
    is the correction: a manifest that could fall back to a well-formed
    all-zero digest was one an operator would read as evidence. `submit_claim`
    answers the authority's exact assignment, claim event and decision, and
    the receipt digest is over those three — which is what makes it a digest
    OF the claim rather than a value this deployment chose.
    """
    from baton_v12.contracts import digest

    return digest(_claim_facts(claimed))


def _claim_event(claimed):
    """The authority's own claim event sequence, or a refusal."""
    return _claim_facts(claimed)["claim_event"]


def _claim_facts(claimed):
    """The three facts `submit_claim` answers, held before either is used."""
    if type(claimed) is not dict:
        raise OperatorRefusal(
            f"the claim answered a {type(claimed).__name__} rather than the "
            f"authority's closed result; an assignment manifest is bound to "
            f"that result and to nothing this deployment composed")
    missing = sorted(one for one in ("assignment", "claim_event", "decision")
                     if one not in claimed)
    if missing:
        raise OperatorRefusal(
            f"the claim result names none of {', '.join(missing)}; an "
            f"assignment manifest carries the authority's evidence and this "
            f"deployment does not invent the parts it was not given")
    return {one: claimed[one]
            for one in ("assignment", "claim_event", "decision")}


def _disposition_of(spoken):
    """What the worker SAID it did, out of the `work` answer and nowhere else."""
    for one in spoken["answers"]:
        if one.get("operation") == "work":
            body = one.get("answer") or {}
            return body.get("disposition")
    return None
