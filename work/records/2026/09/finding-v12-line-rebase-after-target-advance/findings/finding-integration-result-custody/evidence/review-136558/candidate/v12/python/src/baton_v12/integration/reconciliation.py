"""The integration RESULT: one submission reconciled with one target snapshot.

W131409 replacement slice P, INTEGRATION-CONTRACT-v1 sections 1 to 3.

TWO IMMUTABLE OBJECTS, AND THIS OWNS THE SECOND. An eligible submission is the
producer's ORIGINAL proposal on its ORIGINAL base, with its own frozen result,
its own tests and its own independent review. Nothing here rewrites any of
that: the producer's line, checkpoint, verdict, proposal and base appear in
every record below as references it reads and never touches. An integration
RESULT is a different immutable candidate -- that submission reconciled with
one exact target snapshot -- and it earns its own content, its own tests, its
own review and approval, and its own derived Authority proposal.

AN OLD SUBMISSION BASE IS ALLOWED HERE, and that is the whole point of the
replacement direction: a producer does not chase a target that moved under it.
What is NOT relaxed is the RESULT's own target. A stale result still refuses
before import, and removing that guard is not this design.

THREE LESSONS FROM THE SUPERSEDED SLICE ARE BUILT IN RATHER THAN BOLTED ON.
A committed INTENT is not a settled OUTCOME, so a preparing record RESUMES from
its own recorded operands instead of replaying as though it had finished. The
operands an act is signed under are recovered from the committed intent before
any mutable state is consulted, so an exact retry signs identically. And the
public readers bind a materialized row to the journal by RE-DERIVING its
identity from the row's own immutable operands -- row existence, or agreement
between two documents a caller controls, is not a binding.
"""

import json
import os
import stat

from ..authority.errors import Refusal as AuthorityRefusal
from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries
from . import admission, schema
from .git_profile import PROFILE_NAME, PROFILE_VERSION
from .store import integration_signature

__all__ = ["EVIDENCE_KIND", "IMPORT_KIND", "INTENT_KIND", "OBSERVATION_KIND",
           "OUTCOME_KIND", "PUBLISH_KIND", "prepare_result", "publish_result",
           "record_causal_observations", "record_result_evidence",
           "resolve_import_account", "result_identity", "result_of"]

INTENT_KIND = "result.prepare"
OUTCOME_KIND = "result.prepared"
OBSERVATION_KIND = "result.observed"
EVIDENCE_KIND = "result.evidence"
PUBLISH_KIND = "result.publish"

# THE TERMINAL IMPORT ACT, NAMED HERE AND WRITTEN BY NOBODY YET. Review
# 2026-09-10T05:41:11Z [R3]: `imported` was reachable in a corrupted row and
# the reader accepted it, because published and imported were checked as the
# same four acts. The chain below demands THIS act for an imported row; no
# owner in P writes it, so an imported row is refused as unproved until Q
# supplies the terminal transition. That is the conservative direction: a
# state nothing can legitimately reach is a state nothing may claim.
IMPORT_KIND = "result.imported"

# THE THREE INDEPENDENT OWNERS A RESULT MUST SATISFY IN ITS OWN RIGHT. The
# producer's verification, review and approval prove the SUBMISSION; they say
# nothing about bytes that did not exist when they were recorded. So a result
# carries its own three, each naming the actor that gave it and the exact
# content it was given about.
_EVIDENCE_KINDS = ("verification", "review", "approval")
_DISPOSITIONS = {"verification": "passed", "review": "accepted",
                 "approval": "approved"}

# AND THEY ARE THE AUTHORITY'S OWN RECEIPTS, ADOPTED RATHER THAN INVENTED.
#
# Owner return136350 approved AMENDMENT-publication-before-authorization-v1 in
# full. Claim134000 MEASURED why: the only attributable evidence verbs a
# configured session has are `verify`/`review`/`approve`, every one of them is
# keyed by a PUBLISHED proposal, and all three refuse result-shaped operands.
# So evidence recorded before publication could only ever come from an owner
# that is not a configured Authority participant -- which is what reviewer
# 133787 objected to. The order is inverted instead: an ordinary derived
# publication creates the candidate identity, the three configured
# participants record ORDINARY receipts on it through their own scoped
# sessions, and this record ADOPTS those receipts. It writes none of them.
#
# These are the members `Core._receipt_document` actually answers -- claim
# 136400 read all three back from a real Authority, evidence/roundtrip-136400
# .json -- and the closed set this record retains.
_RECEIPT_MEMBERS = ("receipt_id", "kind", "proposal_id", "actor",
                    "disposition", "candidate_digest", "target",
                    "policy_generation", "recorded_at", "decision")
# And the proposal document the Authority answers, adopted whole. It is
# `admission._PROPOSAL_MEMBERS` deliberately re-stated rather than imported:
# both are readers of one Authority surface, and a boundary that names its own
# expectations is the shape this package keeps.
_PROPOSAL_MEMBERS = ("proposal_id", "assignment_ref", "decision", "result_id",
                     "result_digest", "candidate_digest", "input_digest",
                     "policy_digest", "target", "published_at")

# THE IMMUTABLE PROVENANCE ONE DERIVED RESULT DIGEST IS BOUND OVER. Real
# Authority receipts carry no `observations_digest` and no `observed_by`
# (reviewer134088), so the executions cannot be bound to a receipt field. They
# are bound through the PROPOSAL instead: every member below, plus the
# assignment, the prepared bytes, the pinned target, the accepted Job's input
# and policy digests, the observer and the observations digest, are digested
# into the frozen result digest the derived proposal publishes -- and every
# receipt names that proposal.
_SOURCE_PROVENANCE = ("job_id", "line_id", "source_checkpoint_id",
                      "source_verdict_id", "source_proposal_id",
                      "source_result_id", "source_result_digest",
                      "source_checkpoint_digest", "source_base",
                      "source_candidate")

# THE THREE CAUSAL OBSERVATIONS, RETAINED IN CUSTODY RATHER THAN BESIDE IT.
# CONTRACT-v1 section 4, and section 3's requirement that a record cannot omit
# its original causal observation references. Review [P1]: a dossier JSON is
# useful evidence and is not runtime custody, so the verification owner hands
# these over and this record keeps them, cross-bound to the content they were
# observed against.
_OBSERVATIONS = ("base", "isolated", "combined")
_OBSERVATION_MEMBERS = ("command", "test_identity", "input_commit",
                        "input_tree", "test_digest", "environment",
                        "status", "output", "execution", "harness_added")

# AND THE OWNER THAT PRODUCES THEM. Review 2026-09-10T05:41:11Z [R1]: the
# observations were an independent caller argument, so relabelling a failing
# combined run as a passing one authorized the result. They are an OWNER's
# answer now -- asked for through a capability, attributed to that owner's own
# participant and to the execution it names, and retained by their own act
# whether they passed or failed.
_OBSERVE_VERB = "observe"
_ATTESTATION_MEMBERS = ("result_id", "content_digest", "candidate", "tree",
                        "target", "execution", "observations")

# THE IMMUTABLE OPERANDS ONE RESULT IS DERIVED AND SIGNED FROM. They are the
# submission's identity, the integration role's own assignment, the pinned
# target and the workspace -- every one of them a fact that cannot change
# under a retry. A member that could move is deliberately absent: an identity
# derived from mutable state is one a retry re-derives differently.
_FIXED = ("canonical_target_id", "authority_uuid", "work_id", "job_id",
          "line_id", "source_checkpoint_id", "source_verdict_id",
          "source_proposal_id", "source_result_id", "source_result_digest",
          "source_checkpoint_digest", "source_base", "source_candidate",
          "integration_attempt_id", "integration_assignment", "workspace",
          "profile_name", "profile_version", "target_revision",
          "target_source", "target_reference")


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _object(value, what):
    """One full object name, so no revision expression reaches a record."""
    boundaries.text(value, what)
    if len(value) != 40 or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is one full lowercase object name",
                category="integrity", code="schema")
    return value


def _assignment(value, what):
    held = boundaries.document(value, what,
                               required=("work_ref", "participant",
                                         "generation"))
    ref = boundaries.document(held["work_ref"], f"{what}'s Work reference",
                              required=("authority_uuid", "work_id"))
    boundaries.text(ref["authority_uuid"], f"{what}'s Authority")
    boundaries.text(ref["work_id"], f"{what}'s Work id")
    boundaries.text(held["participant"], f"{what}'s participant")
    boundaries.generation(held["generation"], f"{what}'s generation")
    return held


def _place(value, what):
    return boundaries.document(value, what,
                               required=("path", "device", "inode"))


def _prove_storage(place, what):
    """The nominated storage IS the storage this record names.

    REVIEW 2026-09-10T05:41:11Z [R4]: the three members were shape-checked and
    never compared with anything, so a caller supplying the real path with a
    fabricated inode prepared, published and resolved an import account while
    the record described storage that did not exist. Contract sections 2 and 3
    nominate a path, device and inode precisely so that REPLACED storage is a
    refusal rather than a surprise: a directory swapped for another between
    preparation and import has a different inode, and that is the whole point
    of recording one.

    The profile is only ever handed a path string, so this is the boundary
    where the path is bound to the object it was nominated as.
    """
    held = _place(place, what)
    try:
        seen = os.stat(held["path"])
    except OSError as failure:
        _refuse(f"{what} names {name_value(held['path'])}, which this host "
                f"cannot stat ({type(failure).__name__}); nominated storage is "
                f"proved before it is used",
                category="integrity", code="path")
    if not stat.S_ISDIR(seen.st_mode):
        _refuse(f"{what} names {name_value(held['path'])}, which is not a "
                f"directory", category="integrity", code="file-type")
    if seen.st_dev != held["device"] or seen.st_ino != held["inode"]:
        _refuse(f"{what} was nominated as device {held['device']} inode "
                f"{held['inode']} and {name_value(held['path'])} is now device "
                f"{seen.st_dev} inode {seen.st_ino}; replaced or "
                f"misidentified storage refuses rather than being written to",
                category="integrity", code="path")
    return held


def _directory_identity(path):
    """The (device, inode) of one directory, THROUGH its links.

    `_prove_storage` deliberately compares an UNRESOLVED path against the
    device and inode this record nominated, because that is what catches
    replaced storage. This resolves symlinks first, because that is what
    catches an ALIAS -- two names for one directory, which the nomination
    check happily accepts twice.
    """
    try:
        held = os.stat(os.path.realpath(path))
    except OSError:
        return None
    return (held.st_dev, held.st_ino)


def _repository_identity(profile, path, what):
    """Which repository a path belongs to, or None if it is not one."""
    try:
        answer = profile.storage(path)
    except Exception:
        # A PROTECTED PLACE THIS HOST CANNOT RESOLVE IS NOT A LICENCE. It
        # simply cannot be compared by repository identity, and the directory
        # comparison below still runs against it. Said plainly rather than
        # swallowed: only the workspace's own resolution is required.
        return None
    held = boundaries.document(answer, f"{what}'s repository identity",
                               required=("git_common_dir", "device", "inode"))
    return (held["device"], held["inode"])


def _prove_isolation(profile, manager, workspace, target_source, line_id):
    """THE WORKSPACE IS NOT THE PRODUCER'S LINE, ITS SOURCE OR THE TARGET.

    AMENDMENT-publication-before-authorization-v1, "Finish the existing
    storage-isolation requirement". Reviewer134088 nominated the producer's own
    line as the preparation workspace: every device and inode this record had
    recorded MATCHED, `prepare_result` succeeded, and the profile wrote
    `refs/baton/integration/prepared/result-...` into the producer's
    repository. Proving that a directory is the one that was nominated is not
    proving that it is an integration-owned workspace, and contract sections 1
    to 3 require the second.

    THE MANAGER ALREADY OWNS THE ANSWER. `line_of` carries the line's own
    `line_path`/`line_device`/`line_inode` and the protected `source_path`,
    so no Manager schema or source change is needed to ask which storage
    belongs to the producer.

    TWO COMPARISONS, BECAUSE A CANONICAL PATH COMPARISON COVERS NEITHER CASE.
    The REPOSITORY identity is the profile's resolved Git common directory, so
    a linked worktree and a symlinked repository answer the producer's own
    identity even though their working paths differ. The DIRECTORY identity is
    the resolved (device, inode) of the place itself, so an aliased path is
    caught even where Git cannot be asked at all. Claim136400 measured both
    against real Git: evidence/roundtrip-136400.json.
    """
    line = admission.line_of(manager, line_id)
    protected = [("the dedicated target repository", target_source["path"])]
    for what, member in (("the producer's development line", "line_path"),
                         ("the producer's protected source", "source_path")):
        if line.get(member):
            protected.append((what, line[member]))
    mine = _repository_identity(profile, workspace["path"],
                                "the private workspace")
    if mine is None:
        _refuse(f"the private workspace "
                f"{name_value(workspace['path'])} does not resolve to a "
                f"repository this profile can identify; isolation is proved "
                f"before anything is written, not assumed",
                category="integrity", code="path")
    here = _directory_identity(workspace["path"])
    for what, path in protected:
        if _repository_identity(profile, path, what) == mine:
            _refuse(f"the private workspace {name_value(workspace['path'])} "
                    f"is the same repository as {what} "
                    f"({name_value(path)}); an integration result is composed "
                    f"in storage the integration role owns, and a shared Git "
                    f"directory is that repository however it was reached",
                    category="integrity", code="path")
        if here is not None and _directory_identity(path) == here:
            _refuse(f"the private workspace {name_value(workspace['path'])} "
                    f"is {what} ({name_value(path)}) under another name; "
                    f"aliased storage is the same storage",
                    category="integrity", code="path")
    return mine


def _live_assignment(authority, given):
    """The integration assignment the Authority says is LIVE, right now.

    Review 2026-09-10T05:41:11Z [R2]. `assignment_of` is the Authority's own
    answer to "who holds this Work"; a released or reassigned Work answers
    None or somebody else, and either way this role has no authority to start
    or resume effects under the assignment it was handed.
    """
    held = _assignment(given, "the integration assignment")
    boundaries.capability(getattr(authority, "assignment_of", None),
                          "the Authority's assignment read")
    try:
        live = authority.assignment_of(held["work_ref"]["work_id"])
    except AuthorityRefusal as refused:
        _refuse(f"the Authority refused the assignment read for Work "
                f"{name_value(held['work_ref']['work_id'])}: {refused}",
                category="stale-assignment", code="generation")
    if live is None:
        _refuse(f"Work {name_value(held['work_ref']['work_id'])} has no live "
                f"assignment; a result is prepared under an assignment this "
                f"role actually holds",
                category="stale-assignment", code="generation")
    if live != held:
        _refuse(f"the integration assignment names "
                f"{name_value(held['participant'])} at generation "
                f"{held['generation']} and this Work is now held by "
                f"{name_value(live['participant'])} at generation "
                f"{live['generation']}",
                category="stale-assignment", code="generation")
    return held


def result_identity(operands):
    """The identity one result is derived from, and only from what cannot move.

    Deriving it here, from the closed fixed-operand set, is what lets a reader
    RE-DERIVE it from a materialized row and refuse a row whose recorded
    identity does not follow from its own contents.
    """
    held = {name: operands[name] for name in _FIXED}
    return "result-" + digest(held).split(":", 1)[1]


def _fixed_operands(given):
    """The closed operand set, each member owned before it is signed."""
    held = {}
    for name in ("canonical_target_id", "line_id", "source_checkpoint_id",
                 "source_verdict_id", "source_proposal_id",
                 "source_result_id", "integration_attempt_id", "job_id",
                 "work_id"):
        held[name] = boundaries.identity(given[name], f"a result's {name}")
    for name in ("authority_uuid", "source_result_digest",
                 "source_checkpoint_digest", "profile_name",
                 "target_reference"):
        held[name] = boundaries.text(given[name], f"a result's {name}")
    for name in ("source_base", "source_candidate", "target_revision"):
        held[name] = _object(given[name], f"a result's {name}")
    held["integration_assignment"] = _assignment(
        given["integration_assignment"], "the integration assignment")
    held["workspace"] = _place(given["workspace"], "the private workspace")
    held["target_source"] = _place(given["target_source"],
                                   "the nominated target source")
    boundaries.generation(given["profile_version"], "a profile version")
    held["profile_version"] = given["profile_version"]
    if held["integration_assignment"]["work_ref"] != {
            "authority_uuid": held["authority_uuid"],
            "work_id": held["work_id"]}:
        _refuse("the integration assignment names another Work; a result is "
                "prepared under the assignment of the Work it belongs to",
                code="operation-collision")
    if held["source_base"] == held["target_revision"]:
        _refuse(f"the submission is already based on "
                f"{name_value(held['target_revision'])}; a reconciliation "
                f"answers a target that moved and there is nothing here to "
                f"re-express")
    return held


# -- the intent, the outcome, and the resume between them --------------------


def prepare_result(store, profile, manager, jobs, authority, *, line_id,
                   proposal_id, workspace, target_source, target_reference,
                   integration_attempt_id, integration_assignment,
                   canonical_target_id, target_revision=None):
    """Reconcile one eligible submission with one pinned target snapshot.

    THE SUBMISSION IS RESOLVED, NOT ACCEPTED. Review 2026-09-10T05:14:36Z [P1]:
    this used to take a `submission` document from its caller, so a caller
    could name a proposal the Authority never published and a checkpoint and
    verdict nobody ever created, and reach a real derived publication on them.
    `line_id` and `proposal_id` are SELECTORS now -- which is what
    CONTRACT-v1 section 3's own signature says -- and
    `admission.source_submission` re-reads the accepted checkpoint, its
    writer's assignment and frozen output, the Authority proposal with its
    three policy receipts and the Job that owns the input, policy and scope.
    Every member of the submission comes back from those producers.

    IT IS SOURCE ELIGIBILITY AND NOT FRESHNESS, deliberately: the target has
    moved, which is why there is a reconciliation at all.

    THE INTENT COMMITS BEFORE ANY PROFILE EFFECT, which is what makes a death
    in the middle answerable rather than invisible. A committed intent says
    this exact submission is being reconciled onto this exact target revision
    in this exact workspace, under this exact integration assignment, and every
    one of those is fixed for the life of the record.

    AND A COMMITTED INTENT RESUMES RATHER THAN REPLAYING. This is the
    correction the superseded slice's review named: an exact retry of a
    preparing record used to answer "already done" and call the profile zero
    times, leaving a record that could never finish. Here the intent's own
    recorded operands are recovered and the profile is asked again -- with the
    ORIGINAL target revision, never a freshly selected one -- and the profile
    validates and reuses whatever it already retained instead of reconciling
    twice. Only the OUTCOME replays.

    AND THE ASSIGNMENT IS PROVED LIVE BEFORE ANY EFFECT. Review
    2026-09-10T05:41:11Z [R2]: the integration assignment was a shaped caller
    operand, so after the integration session passed its Work back -- leaving
    `assignment_of` answering None -- preparation still ran, wrote objects and
    retained a prepared reference. Publication refused later, which does not
    unwrite what preparation did. The Authority is asked WHO holds this Work
    now, and an obsolete assignment stops here.

    READ-ONLY RECOVERY OF AN EXISTING RECORD IS NOT NEW EXECUTION and is not
    what this guards: `result_of` and `resolve_import_account` still read a
    historical record. What refuses is starting or resuming EFFECTS under an
    assignment that is no longer live.

    THE NOMINATED STORAGE IS PROVED TOO, review [R4]: the workspace and the
    target source are stat-ed and their device and inode compared with what
    this record nominates, so replaced or misidentified storage refuses before
    the profile is handed a path.

    AND IT IS PROVED TO BE THIS ROLE'S OWN. Reviewer134088 nominated the
    producer's line as the workspace, matched every stat, and watched
    preparation write a prepared reference into the producer's repository.
    `_prove_isolation` resolves the Manager's owned line and source storage and
    refuses overlap with the workspace -- by repository identity, so a shared
    Git common directory counts, and by resolved directory, so an alias does.
    """
    _profile_capabilities(profile)
    # THE CERTIFICATION IS ASKED BEFORE THE PROFILE IS, and that ordering is
    # the point: `_prove_isolation` now asks the profile to resolve repository
    # identities before any effect, so a profile this owner does not compose
    # with must be turned away before it is asked anything at all.
    if getattr(profile, "name", None) != PROFILE_NAME \
            or getattr(profile, "version", None) != PROFILE_VERSION:
        _refuse(f"this owner composes {PROFILE_NAME}/{PROFILE_VERSION} and the "
                f"supplied profile is "
                f"{name_value(getattr(profile, 'name', None))}/"
                f"{getattr(profile, 'version', None)}",
                category="policy", code="profile-uncertified")
    submission = admission.source_submission(
        manager, jobs, authority, line_id=line_id, proposal_id=proposal_id)
    workspace = _prove_storage(workspace, "the private workspace")
    target_source = _prove_storage(target_source, "the nominated target source")
    _prove_isolation(profile, manager, workspace, target_source, line_id)
    _live_assignment(authority, integration_assignment)
    # THE TARGET IS PINNED HERE, from the dedicated target's own configured
    # reference, and then it is an IMMUTABLE operand of this result. A caller
    # may name one explicitly to resume or re-derive an existing record; it
    # supplies no default, because a result whose target its caller chose
    # freely would be one nothing pinned.
    #
    # AND A MOVED TARGET IS A NEW RESULT, not a silent continuation of an old
    # one: the revision is part of the derived identity, so pinning a later
    # revision yields a different record and leaves the earlier one exactly as
    # it was. That is the contract's rule rather than an accident of hashing.
    if target_revision is None:
        target_revision = profile.revision(target_source["path"],
                                           target_reference)
    operands = _fixed_operands(dict(
        submission, workspace=workspace, target_source=target_source,
        target_reference=target_reference,
        integration_attempt_id=integration_attempt_id,
        integration_assignment=integration_assignment,
        canonical_target_id=canonical_target_id,
        target_revision=target_revision,
        profile_name=getattr(profile, "name", None),
        profile_version=getattr(profile, "version", None)))
    result_id = result_identity(operands)
    intent_id = INTENT_KIND + ":" + result_id
    outcome_id = OUTCOME_KIND + ":" + result_id
    intent_signature = _signature(INTENT_KIND, operands)

    # 1. THE OUTCOME FIRST. A settled result is settled; nothing below it runs
    #    again, and this is the only branch that may answer without asking the
    #    profile anything.
    settled, _held = store.replay(outcome_id, _outcome_signature(
        store, result_id, operands), kind=OUTCOME_KIND, witness=_witness) \
        if _recorded(store, outcome_id) else (False, None)
    if settled:
        return result_of(store, result_id)

    # 2. THE INTENT. Committed already means RESUME; absent means commit it.
    recorded = _recorded(store, intent_id)
    if recorded is None:
        def intend(connection):
            now = store._now()
            connection.execute(
                "INSERT INTO integration_results (result_id, operation_id, "
                + ", ".join(_FIXED) + ", state, recorded_at) VALUES (?, ?, "
                + ", ".join("?" for _ in _FIXED) + ", 'preparing', ?)",
                (result_id, intent_id)
                + tuple(_stored(operands[name]) for name in _FIXED) + (now,))
            return {"result_id": result_id, "state": "preparing"}

        store.transact(intent_id, INTENT_KIND, intent_signature, intend,
                       witness=_witness)
    elif recorded["signature"] != intent_signature:
        _refuse(f"result {name_value(result_id)} is already being prepared "
                f"under different operands; an identity derived from these "
                f"operands cannot describe others",
                code="operation-collision")

    # 3. THE OPERANDS THE PROFILE IS ASKED WITH ARE THE RECORD'S OWN, recovered
    #    rather than recomputed -- so a resume cannot select a later target.
    held = _row(store, result_id)
    answer = profile.prepare(
        held["workspace"]["path"], result_id=result_id,
        base=held["source_base"], candidate=held["source_candidate"],
        target=held["target_revision"],
        candidate_source=held["workspace"]["path"],
        target_source=held["target_source"]["path"])
    return _settle(store, result_id, operands, answer)


def _settle(store, result_id, operands, answer):
    """Record what the profile answered, once, under this same intent."""
    if type(answer) is not dict or answer.get("state") not in ("prepared",
                                                               "held"):
        _refuse("a reconciliation profile answers a prepared or held outcome",
                category="integrity", code="schema")
    prepared = None
    content_digest = None
    reason = None
    if answer["state"] == "prepared":
        prepared = _prepared(answer["prepared"], operands["target_revision"])
        content_digest = digest(prepared["content"])
    else:
        reason = boundaries.text(answer.get("reason"), "a hold reason")
        conflicts = answer.get("conflicts")
        if type(conflicts) is not list:
            _refuse("a held reconciliation answers the paths it conflicted on",
                    category="integrity", code="schema")
        for one in conflicts:
            boundaries.text(one, "a conflicted path")
        if conflicts:
            reason = reason + " (" + ", ".join(conflicts) + ")"
    outcome_id = OUTCOME_KIND + ":" + result_id
    signature = _signature(OUTCOME_KIND, {
        "result_id": result_id, "state": answer["state"],
        "prepared": prepared, "content_digest": content_digest,
        "reason": reason, **{name: operands[name] for name in _FIXED}})

    def act(connection):
        current = connection.execute(
            "SELECT state FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()
        if current is None or current["state"] != "preparing":
            _refuse(f"result {name_value(result_id)} is no longer preparing",
                    code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = ?, reason = ?, "
            "prepared = ?, content_digest = ?, operation_id = ? "
            "WHERE result_id = ? AND state = 'preparing'",
            (answer["state"], reason,
             None if prepared is None else canonical_text(prepared),
             content_digest, outcome_id, result_id))
        return {"result_id": result_id, "state": answer["state"]}

    store.transact(outcome_id, OUTCOME_KIND, signature, act, witness=_witness)
    return result_of(store, result_id)


def _outcome_signature(store, result_id, operands):
    """The signature a SETTLED outcome was recorded under, re-derived.

    Read from the materialized row rather than from the caller, so an exact
    retry compares against what this owner actually committed -- and from the
    state that act SETTLED rather than whatever the record has reached since,
    which is review [P2]'s correction. An exact `prepare_result` retry after
    authorization now replays the prepared outcome instead of refusing an
    operation-collision against a signature nothing ever recorded.
    """
    held = _row(store, result_id)
    return _signature(OUTCOME_KIND, {
        "result_id": result_id, "state": _settled_state(held),
        "prepared": held["prepared"], "content_digest": held["content_digest"],
        "reason": _settled_reason(held),
        **{name: operands[name] for name in _FIXED}})


# -- the result's OWN independent evidence -----------------------------------


def _basis(held):
    """WHAT AN OWNER IS ASKED ABOUT, derived here and never accepted.

    An owner that is handed the question can only answer this result. The
    content digest names the prepared bytes themselves, so an answer about
    another tree over the same paths no longer matches.
    """
    return {"result_id": held["result_id"],
            "content_digest": held["content_digest"],
            "candidate": held["prepared"]["head"],
            "tree": held["prepared"]["tree"],
            "target": held["target_revision"]}


def _custody_basis(held, derived_result_id, input_digest, policy_digest):
    """THE ONE CLOSED BASIS THIS RESULT'S FROZEN IDENTITY IS DERIVED FROM.

    AMENDMENT-publication-before-authorization-v1, "Receipt-to-execution
    binding without new Authority fields". Real Authority receipts carry no
    `observations_digest` and no `observed_by`, so pretending an adapter could
    read them would be exactly the shape-invention the amendment forbids. Every
    member the evidence must be ABOUT is digested into the result digest the
    derived proposal publishes instead, and the receipts name that proposal.

    EVERY MEMBER IS IMMUTABLE CUSTODY, which is what lets this be re-derived
    at admission and compared with what the Authority still holds. The input
    and policy digests are the accepted owning Job's, read back from the
    producer's own proposal rather than accepted as text.
    """
    return {"derived_result_id": derived_result_id,
            "result_id": held["result_id"],
            "source": {name: held[name] for name in _SOURCE_PROVENANCE},
            "integration_assignment": held["integration_assignment"],
            "prepared": {"head": held["prepared"]["head"],
                         "tree": held["prepared"]["tree"],
                         "content_digest": held["content_digest"]},
            "target": held["target_revision"],
            "input_digest": input_digest,
            "policy_digest": policy_digest,
            "observed_by": held["observed_by"],
            "observations": digest(held["causal_observations"])}


def _accepted_digests(reader, held):
    """The accepted owning Job's input and policy digests, PROVED.

    The amendment requires publication to pin these against the accepted Job
    rather than accept arbitrary strings. It needs no new reader and no
    `admission` change: `admission._proved` already refuses unless the
    producer's proposal and the owning Job agree on both members, so the
    producer's own proposal -- re-read here, through the caller's ordinary
    Authority proposal read -- IS the accepted Job's answer. Claim136400
    measured that read from a real scoped session.
    """
    boundaries.capability(getattr(reader, "proposal", None),
                          "the Authority's proposal read")
    try:
        answer = reader.proposal(held["source_proposal_id"])
    except AuthorityRefusal as refused:
        _refuse(f"the Authority refused the producer's proposal "
                f"{name_value(held['source_proposal_id'])}: {refused}",
                category="stale-assignment", code="precondition")
    document = boundaries.document(answer, "the producer's own proposal",
                                   required=_PROPOSAL_MEMBERS)
    for member, expected in (("proposal_id", held["source_proposal_id"]),
                             ("result_id", held["source_result_id"]),
                             ("result_digest", held["source_result_digest"])):
        if document[member] != expected:
            _refuse(f"the producer's proposal names {member} "
                    f"{name_value(document[member])} and this result was "
                    f"prepared from {name_value(expected)}",
                    category="stale-assignment", code="precondition")
    return (boundaries.text(document["input_digest"], "an input digest"),
            boundaries.text(document["policy_digest"], "a policy digest"))


def _observation(value, what):
    """One causal observation, with everything section 4 requires named."""
    held = boundaries.document(value, what, required=_OBSERVATION_MEMBERS)
    if type(held["command"]) is not list or not held["command"]:
        _refuse(f"{what} names the command that produced it",
                category="integrity", code="schema")
    for one in held["command"]:
        boundaries.text(one, f"{what}'s command word")
    for name in ("test_identity", "test_digest", "environment", "output",
                 "execution"):
        boundaries.text(held[name], f"{what}'s {name}")
    for name in ("input_commit", "input_tree"):
        _object(held[name], f"{what}'s {name}")
    if type(held["status"]) is not int or type(held["status"]) is bool:
        _refuse(f"{what} carries the actual exit status it observed",
                category="integrity", code="schema")
    # SECTION 4, SAID OUT LOUD RATHER THAN IMPLIED: a harness that did not
    # exist in the content it ran against was ADDED there, and the observation
    # records that instead of letting a reader assume the state carried it.
    if type(held["harness_added"]) is not bool:
        _refuse(f"{what} says whether its harness was added to the content it "
                f"ran against", category="integrity", code="schema")
    return held


def _causal(given, held, actor):
    """The three observations, cross-bound to the content they are about.

    SECTION 4, ENFORCED RATHER THAN DESCRIBED. The defect reproduction failed
    on the submission's ORIGINAL base, the same pinned harness passed with the
    isolated fix, and the third observation is what that harness did on the
    COMBINED result -- which is this record's own tree, so a combined
    observation about some other content is not this result's.

    ONE HARNESS, PINNED ONCE. Three different test digests would be three
    different questions, and section 4 asks for one question asked three times.

    AND A COMBINED FAILURE STAYS VISIBLE. It does not erase the isolated
    positive and it does not become a passed verification; it blocks.
    """
    observations = boundaries.document(given, "the causal observations",
                                       required=_OBSERVATIONS)
    taken = {name: _observation(observations[name],
                                f"the {name} causal observation")
             for name in _OBSERVATIONS}
    digests = {one["test_digest"] for one in taken.values()}
    if len(digests) != 1:
        _refuse("the three causal observations name different harnesses; one "
                "pinned harness is run against three content states",
                category="integrity", code="digest")
    if taken["base"]["input_commit"] != held["source_base"]:
        _refuse(f"the base observation ran against "
                f"{name_value(taken['base']['input_commit'])} and this "
                f"submission's original base is "
                f"{name_value(held['source_base'])}",
                category="integrity", code="digest")
    if taken["isolated"]["input_commit"] != held["source_candidate"]:
        _refuse(f"the isolated observation ran against "
                f"{name_value(taken['isolated']['input_commit'])} and this "
                f"submission's candidate is "
                f"{name_value(held['source_candidate'])}",
                category="integrity", code="digest")
    if taken["combined"]["input_commit"] != held["prepared"]["head"] \
            or taken["combined"]["input_tree"] != held["prepared"]["tree"]:
        _refuse("the combined observation ran against other content than this "
                "result prepared", category="integrity", code="digest")
    if not taken["base"]["harness_added"]:
        _refuse("the base observation does not say the harness was added; a "
                "regression harness the submission brings with it did not "
                "exist on the original base, and section 4 records that "
                "rather than pretending the base ran it",
                category="integrity", code="schema")
    for name in ("isolated", "combined"):
        if taken[name]["harness_added"]:
            _refuse(f"the {name} observation added its harness; that content "
                    f"carries the submission's own harness and an added one "
                    f"is a different question",
                    category="integrity", code="schema")
    if taken["base"]["status"] == 0:
        _refuse("the base observation PASSED on the original base; a causal "
                "witness is a reproduction that fails there",
                category="policy", code="denied")
    if taken["isolated"]["status"] != 0:
        _refuse("the isolated observation did not pass with the submission's "
                "own fix", category="policy", code="denied")
    # AND THE COMBINED STATUS IS NOT JUDGED HERE. Review 2026-09-10T05:41:11Z
    # [R1]: refusing a failing combination at this point threw the failed
    # execution away -- the row stayed `prepared` with no observations at all,
    # which is the opposite of section 4's "the combined failure stays
    # visible". Whether it passed decides the STATE the observation act
    # settles, and `record_causal_observations` decides that after these are
    # durably stored.
    for name in _OBSERVATIONS:
        if taken[name]["execution"] != actor:
            _refuse(f"the {name} observation was produced by "
                    f"{name_value(taken[name]['execution'])} and this "
                    f"observation owner attested {name_value(actor)}",
                    category="policy", code="denied")
    return taken


def _owner_participant(owner, kind, held):
    """WHOSE receipt this record will accept as the result's `kind`.

    The three owners are still INJECTED and are still held to independence --
    what changed under the approved amendment is that this record no longer
    asks them anything. They completed their decisions through their own scoped
    Authority sessions, on the derived proposal, as ordinary receipts. All this
    needs from them is the participant whose receipt it may adopt.
    """
    actor = boundaries.text(getattr(owner, "participant", None),
                            f"the configured {kind} owner's participant")
    if actor == held["integration_assignment"]["participant"]:
        _refuse(f"{name_value(actor)} prepared this result and cannot also "
                f"give its {kind}; the integration owner does not review its "
                f"own composition", category="policy", code="denied")
    return actor


def _adopted_receipt(authority, kind, actor, held, basis_digest):
    """ONE ACTUAL AUTHORITY RECEIPT, cross-bound to this exact custody.

    FIVE BINDINGS, NONE OF THEM INVENTED. The receipt must be on THIS result's
    derived proposal, be of THIS kind, be written by the configured actor, be
    ACCEPTING, and name back the candidate digest and target the Authority
    recorded it against -- which are the prepared head and the pinned snapshot.
    The executions and the observer ride the proposal's own frozen result
    digest, `basis_digest`, because a real receipt carries no field for them.

    A MISSING RECEIPT IS AN UNAPPROVED CANDIDATE and says so. That is what
    `published` now means, and it is the state the whole amendment exists to
    make representable: the proposal is real, nobody has judged it yet, and it
    resolves no import account.
    """
    answer = authority.receipt(held["derived_proposal_id"], kind)
    if answer is None:
        _refuse(f"the Authority holds no {kind} receipt on derived proposal "
                f"{name_value(held['derived_proposal_id'])}; a published "
                f"result is a candidate and is authorized only by the "
                f"independent receipts its own owners record on it",
                category="policy", code="denied")
    document = boundaries.document(answer, f"the result's {kind} receipt",
                                   required=_RECEIPT_MEMBERS)
    boundaries.identity(document["receipt_id"], f"a {kind} receipt identity")
    if document["kind"] != kind \
            or document["proposal_id"] != held["derived_proposal_id"]:
        _refuse(f"the adopted receipt is the {name_value(document['kind'])} of "
                f"{name_value(document['proposal_id'])} and this result needs "
                f"the {kind} of "
                f"{name_value(held['derived_proposal_id'])}",
                category="integrity", code="schema")
    if document["actor"] != actor:
        _refuse(f"this result's {kind} owner is {name_value(actor)} and the "
                f"Authority's {kind} receipt was written by "
                f"{name_value(document['actor'])}",
                category="policy", code="denied")
    if document["disposition"] != _DISPOSITIONS[kind]:
        _refuse(f"the Authority's {kind} receipt is "
                f"{name_value(document['disposition'])} and an authorized "
                f"result carries {name_value(_DISPOSITIONS[kind])}; a "
                f"nonaccepting decision is retained by its owner and is not "
                f"an authorization", category="policy", code="denied")
    for member, expected in (("candidate_digest", held["prepared"]["head"]),
                             ("target", held["target_revision"])):
        if document[member] != expected:
            _refuse(f"the Authority's {kind} receipt names {member} "
                    f"{name_value(document[member])} and this result's is "
                    f"{name_value(expected)}; a receipt about other bytes or "
                    f"another target is not this result's",
                    category="integrity", code="digest")
    if document["decision"] is None:
        _refuse(f"the Authority's {kind} receipt names no authorization "
                f"decision", category="integrity", code="schema")
    # AND THE EXECUTIONS, THROUGH THE ONLY MEMBER THAT CAN CARRY THEM. The
    # receipt's own proposal names the frozen result digest this record derived
    # from its immutable custody -- source provenance, assignment, prepared
    # bytes, target, accepted input/policy digests, observer and observations.
    # A receipt on a proposal whose result digest is not that one is evidence
    # about a different composition.
    if held["derived_result_digest"] != basis_digest:
        _refuse("the derived proposal this receipt is on does not name the "
                "result digest this result's own custody derives",
                category="integrity", code="digest")
    return document


def record_causal_observations(store, observer, *, result_id):
    """Ask the observation OWNER what its harness actually did, and keep it.

    REVIEW 2026-09-10T05:41:11Z [R1], BOTH HALVES.

    THE OBSERVATIONS ARE AN OWNER'S ANSWER, NOT A CALLER'S ARGUMENT. They used
    to arrive beside the call, so relabelling a failing combined run as a
    passing one and handing it to the same accepting owner authorized the
    result. This asks a configured owner through its own capability, with a
    question this record derives, and records the owner's participant and the
    execution it attests. A caller has nothing left to relabel.

    AND A FAILURE IS RETAINED RATHER THAN REFUSED. A failing combined run used
    to be rejected before anything was stored, so the row stayed `prepared`
    with no observations and the failed execution had NO custody at all --
    exactly backwards from section 4's "the combined failure stays visible and
    blocks integration; it does not invalidate or erase the isolated
    positive". The observations commit either way. A passing combination
    settles `awaiting-evidence`; a failing one settles `blocked`, with its
    reason, its retained runs and no route to authorization.

    A base that passed or an isolated run that failed still refuse: those are
    not a causal witness at all, and there is nothing to retain about them.
    """
    held = result_of(store, result_id)
    if held["prepared"] is None:
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; a causal observation is about prepared content and never "
                f"about content that does not exist yet")
    boundaries.capability(getattr(observer, _OBSERVE_VERB, None),
                          f"the configured observation owner's "
                          f"{_OBSERVE_VERB} capability")
    actor = boundaries.text(getattr(observer, "participant", None),
                            "the configured observation owner's participant")
    if actor == held["integration_assignment"]["participant"]:
        _refuse(f"{name_value(actor)} prepared this result and cannot also "
                f"observe it; the integration owner does not witness its own "
                f"composition", category="policy", code="denied")
    basis = _basis(held)
    answer = boundaries.document(getattr(observer, _OBSERVE_VERB)(dict(basis)),
                                 "the observation owner's attestation",
                                 required=_ATTESTATION_MEMBERS)
    for member in ("result_id", "content_digest", "candidate", "tree",
                   "target"):
        if answer[member] != basis[member]:
            _refuse(f"the attestation was made about {member} "
                    f"{name_value(answer[member])} and this result's is "
                    f"{name_value(basis[member])}",
                    category="integrity", code="digest")
    execution = boundaries.text(answer["execution"],
                                "the attested execution identity")
    causal = _causal(answer["observations"], held, execution)
    passed = causal["combined"]["status"] == 0
    state = "awaiting-evidence" if passed else "blocked"
    reason = None if passed else (
        f"the combined result FAILED its own causal observation with status "
        f"{causal['combined']['status']}; a combined failure blocks "
        f"integration and is not verified away, and the isolated positive is "
        f"retained beside it")
    operation_id = _operation_id(OBSERVATION_KIND, result_id)
    signature = _signature(OBSERVATION_KIND, {
        "result_id": result_id, "content_digest": held["content_digest"],
        "state": state, "reason": reason, "causal_observations": causal,
        "observed_by": actor})
    if held["state"] != "prepared":
        # SETTLED IS SETTLED, and an identical retry gets the record this act
        # made rather than a refusal -- the same rule the outcome and evidence
        # acts follow.
        recorded = _recorded(store, operation_id)
        if recorded is not None and recorded["signature"] == signature:
            replayed, _held = store.replay(operation_id, signature,
                                           kind=OBSERVATION_KIND,
                                           witness=_witness)
            if replayed:
                return held
        _refuse(f"result {name_value(result_id)} is already "
                f"{name_value(held['state'])} under other observations; a "
                f"witnessed result is not re-observed in place",
                code="operation-collision")

    def act(connection):
        current = connection.execute(
            "SELECT state, content_digest FROM integration_results "
            "WHERE result_id = ?", (result_id,)).fetchone()
        if current is None or current["state"] != "prepared" \
                or current["content_digest"] != held["content_digest"]:
            _refuse(f"result {name_value(result_id)} changed while it was "
                    f"being observed", code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = ?, reason = ?, "
            "causal_observations = ?, observed_by = ?, operation_id = ? "
            "WHERE result_id = ?",
            (state, reason, canonical_text(causal), actor, operation_id,
             result_id))
        return {"result_id": result_id, "state": state}

    store.transact(operation_id, OBSERVATION_KIND, signature, act,
                   witness=_witness)
    return result_of(store, result_id)


def _observation_signature(held):
    """The signature the OBSERVATION act was recorded under, re-derived from
    the row rather than from the state it has reached since."""
    passed = held["causal_observations"]["combined"]["status"] == 0
    return _signature(OBSERVATION_KIND, {
        "result_id": held["result_id"],
        "content_digest": held["content_digest"],
        "state": "awaiting-evidence" if passed else "blocked",
        "reason": held["reason"] if held["state"] == "blocked" else None,
        "causal_observations": held["causal_observations"],
        "observed_by": held["observed_by"]})


def record_result_evidence(store, authority, verification, reviewer, approver,
                           *, result_id):
    """ADOPT the three real receipts this result's own owners recorded.

    THE ORDER IS OWNER return136350'S, AND THE MEASUREMENT BEHIND IT IS
    CLAIM134000'S. Every attributable evidence verb a configured session has is
    keyed by a published proposal, so evidence recorded BEFORE publication
    could only come from an owner outside the Authority -- the exact objection
    reviewer133787 raised against the previous shape. Publication therefore
    comes first and confers nothing: it creates the candidate identity, and
    THESE receipts are what authorize it.

    NOTHING HERE WRITES A RECEIPT, and that is the whole point. The three
    configured participants completed their decisions through their own scoped
    sessions on the derived proposal. This reads them back, holds each to this
    result's exact custody, and stores a digest-bound authorization. Missing or
    nonaccepting receipts leave the candidate published and unapproved.

    THE POLICY GENERATION IS THE APPROVAL RECEIPT'S OWN. Claim136400 measured
    that verification and review receipts carry it as NULL and only the
    approval carries a value, so the approval's is read and compared with the
    Authority's CURRENT generation. A caller no longer supplies one at all,
    which is the amendment's "remove the caller-supplied generation as a source
    of approval authority".

    THE EXECUTIONS RIDE THE PROPOSAL. A receipt has no `observations_digest`
    field, so the observer and the causal runs are bound through the frozen
    result digest the derived proposal names, re-derived here from immutable
    custody by `_custody_basis`.

    AN EXACT RETRY REPLAYS. A settled act is settled; what an identical retry
    gets is the record that act made.
    """
    held = result_of(store, result_id)
    operation_id = _operation_id(EVIDENCE_KIND, result_id)
    if held["state"] == "blocked":
        _refuse(f"result {name_value(result_id)} is blocked: {held['reason']}",
                category="policy", code="denied")
    if held["state"] not in ("published", "authorized"):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; its owners record their receipts on the derived proposal, "
                f"so it is published first and authorized by them afterwards")
    for name in ("proposal", "receipt", "policy_generation"):
        boundaries.capability(getattr(authority, name, None),
                              f"the Authority's {name} read")
    document = _derived_still_stands(authority, held)
    input_digest, policy_digest = _accepted_digests(authority, held)
    for member, expected in (("input_digest", input_digest),
                             ("policy_digest", policy_digest)):
        if document[member] != expected:
            _refuse(f"the derived proposal names {member} "
                    f"{name_value(document[member])} and the accepted Job's "
                    f"is {name_value(expected)}",
                    category="integrity", code="digest")
    basis_digest = digest(_custody_basis(held, held["derived_result_id"],
                                         input_digest, policy_digest))
    given = {"verification": verification, "review": reviewer,
             "approval": approver}
    actors = {kind: _owner_participant(given[kind], kind, held)
              for kind in _EVIDENCE_KINDS}
    if len(set(actors.values())) != len(_EVIDENCE_KINDS):
        _refuse("one actor gave more than one of this result's three "
                "independent judgements; independence is what they are for",
                category="policy", code="denied")
    if held["observed_by"] in set(actors.values()):
        _refuse(f"{name_value(held['observed_by'])} produced this result's "
                f"causal observations and cannot also judge them; the runs and "
                f"the judgement about them are two independent owners",
                category="policy", code="denied")
    evidence = {kind: _adopted_receipt(authority, kind, actors[kind], held,
                                       basis_digest)
                for kind in _EVIDENCE_KINDS}
    policy_generation = evidence["approval"]["policy_generation"]
    boundaries.generation(policy_generation,
                          "the approval receipt's policy generation")
    current = authority.policy_generation()
    boundaries.generation(current, "the Authority's policy generation")
    if policy_generation != current:
        _refuse(f"this result's approval was granted under policy generation "
                f"{policy_generation} and the Authority is at {current}; an "
                f"approval under a superseded policy is given again rather "
                f"than adopted", category="policy", code="denied")
    signature = _signature(EVIDENCE_KIND, {
        "result_id": result_id, "content_digest": held["content_digest"],
        "derived_result_digest": held["derived_result_digest"],
        "evidence": evidence, "causal_observations": held["causal_observations"],
        "policy_generation": policy_generation})
    if held["state"] != "published":
        # A RECORD THAT HAS MOVED ON, AND WHAT AN IDENTICAL CALL DESERVES.
        # Review [P2]: this used to refuse before it reached the journal, so
        # an exact retry after authorization failed. It replays now -- but the
        # comparison is made against the receipts the Authority holds NOW, not
        # against whatever the row holds, so an adoption over changed receipts
        # or a moved generation still collides instead of quietly replaying
        # somebody else's settled act.
        recorded = _recorded(store, operation_id)
        if recorded is not None and recorded["signature"] == signature:
            settled, _held = store.replay(operation_id, signature,
                                          kind=EVIDENCE_KIND,
                                          witness=_witness)
            if settled:
                return held
        _refuse(f"result {name_value(result_id)} is already "
                f"{name_value(held['state'])} under other evidence; an "
                f"authorized result is not re-judged in place",
                code="operation-collision")

    def act(connection):
        row = connection.execute(
            "SELECT state, content_digest, derived_result_digest "
            "FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()
        if row is None or row["state"] != "published" \
                or row["content_digest"] != held["content_digest"] \
                or row["derived_result_digest"] != held["derived_result_digest"]:
            _refuse(f"result {name_value(result_id)} changed while its "
                    f"evidence was being proved", code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = 'authorized', "
            "evidence = ?, policy_generation = ?, operation_id = ? "
            "WHERE result_id = ?",
            (canonical_text(evidence), policy_generation, operation_id,
             result_id))
        return {"result_id": result_id, "state": "authorized"}

    store.transact(operation_id, EVIDENCE_KIND, signature, act,
                   witness=_witness)
    return result_of(store, result_id)


def _evidence_signature(held):
    """The signature the EVIDENCE act was recorded under, re-derived from the
    row it made rather than from whatever state the row has reached since."""
    return _signature(EVIDENCE_KIND, {
        "result_id": held["result_id"],
        "content_digest": held["content_digest"],
        "derived_result_digest": held["derived_result_digest"],
        "evidence": held["evidence"],
        "causal_observations": held["causal_observations"],
        "policy_generation": held["policy_generation"]})


# -- the derived Authority proposal ------------------------------------------


def publish_result(store, publisher, *, result_id, input_digest,
                   policy_digest):
    """Publish the OBSERVED result as its OWN Authority proposal -- unapproved.

    W133117's gate proved this expressible with no Authority change: the
    proposal is an ordinary one under the INTEGRATION role's own live
    assignment, carrying a frozen result identity this record owns, the
    combined candidate, and the pinned snapshot as its target. The producer's
    proposal is untouched and its result identity is never borrowed -- the
    Authority refuses that itself, which is why this derives its own.

    WHAT PUBLICATION CONFERS IS AN IDENTITY, AND NOTHING ELSE. Owner
    return136350: an ordinary derived publication creates the candidate that
    independent participants record receipts on. It grants no queue rank, no
    lease, no target write and no import permission, and `published` is
    precisely the state in which none of those are available yet.

    ONLY AN OBSERVED, PASSING RESULT PUBLISHES. A `blocked` combination never
    reaches here, so a failing composition can never acquire a candidate
    identity to collect receipts on.

    AND THE FROZEN DIGEST IS ITS WHOLE CUSTODY, not just its bytes. The result
    digest is derived from `_custody_basis`, so the source provenance, the
    assignment, the prepared tree, the pinned target, the accepted Job's input
    and policy digests, the observer and the causal observations are all bound
    into the identity every later receipt is written against. The input and
    policy digests are PROVED against the producer's own proposal -- which
    `admission` already binds to the accepted Job -- rather than accepted as
    caller text.
    """
    held = result_of(store, result_id)
    if held["state"] == "blocked":
        _refuse(f"result {name_value(result_id)} is blocked: {held['reason']}",
                category="policy", code="denied")
    # `authorized` IS HERE FOR THE EXACT RETRY AND FOR NOTHING ELSE. Review
    # [P2]: an identical call after the record moved on used to refuse a
    # collision against a signature nothing ever recorded. An authorized row
    # necessarily already carries this act's committed operation -- publication
    # is how it got its proposal -- so `store.transact` replays it and the act
    # below never runs. There is no path from `authorized` to a NEW proposal.
    if held["state"] not in ("awaiting-evidence", "published", "authorized"):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; a result is published once its own causal observations are "
                f"in custody, and its independent owners judge it after that")
    if getattr(publisher, "participant", None) != held[
            "integration_assignment"]["participant"]:
        _refuse(f"the publishing session acts for "
                f"{name_value(getattr(publisher, 'participant', None))} and "
                f"this result's assignment names "
                f"{name_value(held['integration_assignment']['participant'])}",
                code="capability")
    _live_assignment(publisher, held["integration_assignment"])
    accepted_input, accepted_policy = _accepted_digests(publisher, held)
    for what, given, expected in (
            ("an input digest", input_digest, accepted_input),
            ("a policy digest", policy_digest, accepted_policy)):
        if boundaries.text(given, what) != expected:
            _refuse(f"this result was published with {what} "
                    f"{name_value(given)} and its accepted Job's is "
                    f"{name_value(expected)}; a derived publication carries "
                    f"the owning Job's own input and policy",
                    category="integrity", code="digest")
    derived_result_id = "derived-" + result_id
    derived_result_digest = digest(_custody_basis(
        held, derived_result_id, accepted_input, accepted_policy))
    proposal_id = "proposal-" + result_id
    operation_id = PUBLISH_KIND + ":" + result_id
    signature = _signature(PUBLISH_KIND, {
        "result_id": result_id, "proposal_id": proposal_id,
        "derived_result_id": derived_result_id,
        "derived_result_digest": derived_result_digest,
        "candidate_digest": held["prepared"]["head"],
        "target": held["target_revision"]})
    proposal = publisher.publish({
        "expect": held["integration_assignment"],
        "operation_id": "integration-publish:" + result_id,
        "proposal_id": proposal_id, "result_id": derived_result_id,
        "result_digest": derived_result_digest,
        "candidate_digest": held["prepared"]["head"],
        "input_digest": accepted_input, "policy_digest": accepted_policy,
        "target": held["target_revision"]})
    _published(proposal, held, proposal_id, derived_result_id,
               derived_result_digest)

    def act(connection):
        current = connection.execute(
            "SELECT state FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()
        if current is None or current["state"] not in ("awaiting-evidence",
                                                       "published",
                                                       "authorized"):
            _refuse(f"result {name_value(result_id)} is no longer an observed "
                    f"result awaiting its owners",
                    code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = 'published', "
            "derived_proposal_id = ?, derived_result_id = ?, "
            "derived_result_digest = ?, operation_id = ? WHERE result_id = ?",
            (proposal_id, derived_result_id, derived_result_digest,
             operation_id, result_id))
        return {"result_id": result_id, "state": "published",
                "derived_proposal_id": proposal_id}

    store.transact(operation_id, PUBLISH_KIND, signature, act,
                   witness=_witness)
    return result_of(store, result_id)


def _published(proposal, held, proposal_id, result_id, result_digest):
    """The Authority's own answer, held to what this result requires."""
    document = boundaries.document(proposal, "the derived proposal",
                                   required=("proposal_id", "assignment_ref",
                                             "result_id", "result_digest",
                                             "candidate_digest",
                                             "input_digest", "policy_digest",
                                             "target"))
    if document["proposal_id"] != proposal_id \
            or document["result_id"] != result_id \
            or document["result_digest"] != result_digest:
        _refuse("the derived proposal does not name this result's own frozen "
                "identity", category="integrity", code="digest")
    if document["assignment_ref"] != held["integration_assignment"]:
        _refuse("the derived proposal was published under another assignment",
                category="stale-assignment", code="generation")
    if document["candidate_digest"] != held["prepared"]["head"]:
        _refuse("the derived proposal names other bytes than this result "
                "prepared", category="integrity", code="digest")
    if document["target"] != held["target_revision"]:
        _refuse("the derived proposal names another target than the snapshot "
                "this result was prepared onto",
                category="integrity", code="digest")
    return document


def _derived_still_stands(authority, held):
    """The derived proposal the Authority holds NOW is this record's own.

    Review [R2]: nothing re-read the result's own publication at admission, so
    an account could be resolved for a record whose derived proposal had never
    been read back since the moment it was written.
    """
    boundaries.capability(getattr(authority, "proposal", None),
                          "the Authority's proposal read")
    answer = authority.proposal(held["derived_proposal_id"])
    if answer is None:
        _refuse(f"the Authority holds no proposal "
                f"{name_value(held['derived_proposal_id'])}; a published "
                f"result names one it can read back",
                category="integrity", code="schema")
    # THE ORDINARY READER'S DOCUMENT, which carries the Authority's own
    # decision and instant beside what this record published. Only the members
    # this record owns are compared; the rest belong to the Authority.
    document = boundaries.document(
        answer, "the derived proposal as the Authority now holds it",
        required=_PROPOSAL_MEMBERS)
    for member, expected in (
            ("proposal_id", held["derived_proposal_id"]),
            ("result_id", held["derived_result_id"]),
            ("result_digest", held["derived_result_digest"]),
            ("candidate_digest", held["prepared"]["head"]),
            ("target", held["target_revision"])):
        if document[member] != expected:
            _refuse(f"the derived proposal the Authority holds names {member} "
                    f"{name_value(document[member])} and this record's is "
                    f"{name_value(expected)}",
                    category="integrity", code="digest")
    if document["assignment_ref"] != held["integration_assignment"]:
        _refuse("the derived proposal the Authority holds was published under "
                "another assignment",
                category="stale-assignment", code="generation")
    return document


# -- what admission may act on -----------------------------------------------


def resolve_import_account(store, profile, manager, jobs, authority, *,
                           result_id):
    """Revalidate everything an import admission needs, at the moment it asks.

    A RESULT IS NOT ELIGIBLE BECAUSE IT ONCE WAS. Its content is re-proved
    against the workspace it was prepared in, its own evidence is re-read, and
    the dedicated target's CURRENT revision is compared with the snapshot it
    was prepared onto. A target that moved again refuses HERE, before the
    queue, with the stale-result guard the contract keeps rather than removes.

    AND THE ORIGINAL ELIGIBILITY IS RE-READ THROUGH ITS OWNERS. Review
    2026-09-10T05:14:36Z [P1]: this could not reach the accepted producers
    through its old signature, so a record whose source stopped being an
    accepted candidate -- a withdrawn checkpoint, a receipt that no longer
    agrees, a Job whose scope moved -- resolved an import account anyway.
    `source_submission` answers from those producers now, and every member it
    answers must be the one this record was prepared from. A submission that
    no longer resolves refuses; a submission that resolves DIFFERENTLY refuses
    with the member that moved.

    AND THE RESULT'S OWN SIDE IS REVALIDATED TOO. Review 2026-09-10T05:41:11Z
    [R2]: this re-read the source and the target and NOTHING about the result
    -- so an account resolved after the integration assignment was released
    and after the approval policy generation advanced, still answering the
    stale assignment. Four things are proved here now, at the moment an import
    admission asks:

    - the integration assignment is still the live one for this Work;
    - the derived proposal still reads back from the Authority as this
      record's own, with its own frozen result and the pinned target;
    - the three actual receipts are still on that proposal, still accepting,
      still by the recorded actors, and the approval's policy generation is
      still the Authority's current one; and
    - the nominated workspace and target storage are still the objects this
      record names, and still isolated from the producer (review [R4] and the
      approved amendment).

    PUBLISHED ALONE ALWAYS REFUSES. Owner return136350 made publication the
    step BEFORE authorization, so the state that once meant "fully judged and
    announced" now means "announced and not yet judged". An import account is
    resolved for an AUTHORIZED result, and a published one is turned away here
    rather than given the benefit of the older meaning of its own name.
    """
    _profile_capabilities(profile)
    held = result_of(store, result_id)
    if held["state"] != "authorized":
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; an import account is resolved for an authorized result, "
                f"and a published one is a candidate its owners have not "
                f"accepted yet")
    resolved = admission.source_submission(
        manager, jobs, authority, line_id=held["line_id"],
        proposal_id=held["source_proposal_id"])
    for member, value in sorted(resolved.items()):
        if held[member] != value:
            _refuse(f"this result was prepared from {member} "
                    f"{name_value(held[member])} and its accepted producers "
                    f"now say {name_value(value)}; a result whose source "
                    f"moved is not imported on the strength of what was true "
                    f"then", category="stale-assignment", code="precondition")
    _live_assignment(authority, held["integration_assignment"])
    document = _derived_still_stands(authority, held)
    input_digest, policy_digest = _accepted_digests(authority, held)
    for member, expected in (("input_digest", input_digest),
                             ("policy_digest", policy_digest)):
        if document[member] != expected:
            _refuse(f"the derived proposal names {member} "
                    f"{name_value(document[member])} and the accepted Job's "
                    f"is {name_value(expected)}",
                    category="integrity", code="digest")
    # THE WHOLE AUTHORIZATION CHAIN AGAIN, at the moment the import asks.
    # Amendment: "Verify the chain again at admission." The digest is
    # re-derived from immutable custody rather than read off the row, and each
    # receipt is re-read from the Authority and compared with the one this
    # record adopted -- so a receipt that changed, disappeared or was never
    # about these executions refuses here even though the row still says
    # authorized.
    boundaries.capability(getattr(authority, "receipt", None),
                          "the Authority's receipt read")
    basis_digest = digest(_custody_basis(held, held["derived_result_id"],
                                         input_digest, policy_digest))
    for kind in _EVIDENCE_KINDS:
        adopted = boundaries.document(held["evidence"][kind],
                                      f"the retained {kind} receipt",
                                      required=_RECEIPT_MEMBERS)
        current = _adopted_receipt(authority, kind, adopted["actor"], held,
                                   basis_digest)
        if current != adopted:
            _refuse(f"this result adopted a {kind} receipt the Authority no "
                    f"longer holds in that form; an authorization is re-proved "
                    f"at admission rather than remembered",
                    category="integrity", code="digest")
    boundaries.capability(getattr(authority, "policy_generation", None),
                          "the Authority's approval policy generation read")
    generation = authority.policy_generation()
    boundaries.generation(generation, "the Authority's policy generation")
    if generation != held["policy_generation"]:
        _refuse(f"this result was approved under policy generation "
                f"{held['policy_generation']} and the Authority is at "
                f"{generation}; a result approved under a superseded policy is "
                f"judged again rather than imported",
                category="policy", code="denied")
    _prove_storage(held["workspace"], "the private workspace")
    _prove_storage(held["target_source"], "the nominated target source")
    _prove_isolation(profile, manager, held["workspace"],
                     held["target_source"], held["line_id"])
    profile.validate(held["workspace"]["path"], held["prepared"],
                     target=held["target_revision"])
    current = profile.revision(held["target_source"]["path"],
                               held["target_reference"])
    if current != held["target_revision"]:
        _refuse(f"this result was prepared onto "
                f"{name_value(held['target_revision'])} and the dedicated "
                f"target now holds {name_value(current)}; a result whose "
                f"target moved is reconciled again rather than imported",
                category="stale-assignment", code="target")
    return {"result_id": result_id,
            "canonical_target_id": held["canonical_target_id"],
            "authority_uuid": held["authority_uuid"],
            "work_id": held["work_id"], "job_id": held["job_id"],
            "source_proposal_id": held["source_proposal_id"],
            "source_checkpoint_id": held["source_checkpoint_id"],
            "derived_proposal_id": held["derived_proposal_id"],
            "derived_result_id": held["derived_result_id"],
            "derived_result_digest": held["derived_result_digest"],
            "candidate_digest": held["prepared"]["head"],
            "expected_target_revision": held["target_revision"],
            "content": dict(held["prepared"]["content"]),
            "content_digest": held["content_digest"],
            "evidence": held["evidence"],
            "causal_observations": held["causal_observations"],
            "integration_assignment": held["integration_assignment"]}


# -- the public reader -------------------------------------------------------


def result_of(store, result_id):
    """One custody record, bound to the journal by EVERY act that made it.

    WHAT MAKES THIS A BINDING. The row is adopted against its closed column
    contract, its nested documents are adopted against theirs, its identity is
    RE-DERIVED from the fixed operands the row itself carries, and the journal
    is asked for each act this record's state says it passed through -- whose
    recorded signature must be the one the row's own current contents produce.

    REVIEW 2026-09-10T05:14:36Z [P1]: ONLY THE LATEST ACT USED TO BE CHECKED,
    and every earlier one was taken on trust the moment the record moved on.
    So an AUTHORIZED row could have its prepared head and tree replaced with
    object names nothing holds, a PUBLISHED row could have its evidence
    emptied, and both still read -- because the evidence act, and then the
    publish act, were the only signatures anyone compared. An earlier valid
    write is not a current typed read. Every act in `_CHAIN_FOR_STATE` is
    re-derived from the row as it stands NOW, so tampering with what an
    earlier act settled breaks that act's signature whatever the row has
    become since.

    AND THE STATE'S OWN REQUIRED FIELDS ARE STRUCTURAL. `imported` with no
    entry is not a terminal linkage, and the schema and this reader both say
    so.
    """
    held = _row(store, result_id)
    operands = {name: held[name] for name in _FIXED}
    if result_identity(operands) != held["result_id"]:
        _refuse(f"result {name_value(result_id)} does not derive its own "
                f"identity from its recorded operands",
                category="integrity", code="digest")
    chain = _CHAIN_FOR_STATE[held["state"]]
    if held["operation_id"] != _operation_id(chain[-1], result_id):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f" and names operation {name_value(held['operation_id'])}, "
                f"which is not the act that reaches that state",
                category="integrity", code="schema")
    for kind in chain:
        operation_id = _operation_id(kind, result_id)
        recorded = _recorded(store, operation_id)
        if recorded is None or recorded["kind"] != kind:
            _refuse(f"result {name_value(result_id)} is "
                    f"{name_value(held['state'])}, which this store's journal "
                    f"does not hold as a committed {kind}",
                    category="integrity", code="schema")
        expected = _expected_signature(kind, result_id, held, operands)
        if recorded["signature"] != expected:
            _refuse(f"result {name_value(result_id)} does not match the "
                    f"operands its own {kind} was signed under",
                    category="integrity", code="digest")
    if held["state"] == "imported":
        # THE ENTRY MUST BE ONE THIS STORE ACTUALLY HOLDS, FOR THIS RESULT.
        # Review [R3]: `entry_id` was checked for being non-null, so
        # `entry-never-created` satisfied it. A text value is not a linkage.
        entry = store._connection.execute(
            "SELECT entry_id, canonical_target_id, state, eligibility "
            "FROM entries WHERE entry_id = ?", (held["entry_id"],)).fetchone()
        if entry is None:
            _refuse(f"result {name_value(result_id)} is imported through entry "
                    f"{name_value(held['entry_id'])}, which this coordinator "
                    f"does not hold", category="integrity", code="schema")
        if entry["canonical_target_id"] != held["canonical_target_id"]:
            _refuse(f"result {name_value(result_id)} names an entry on another "
                    f"target", category="integrity", code="schema")
        if entry["state"] != "integrated":
            _refuse(f"result {name_value(result_id)} is imported through entry "
                    f"{name_value(held['entry_id'])}, which is "
                    f"{name_value(entry['state'])}; an unrelated or "
                    f"unfinished entry supplies no import authority",
                    category="integrity", code="schema")
    return held


# EVERY ACT A RECORD IN EACH STATE MUST HAVE PASSED THROUGH, in order.
#
# Review 2026-09-10T05:14:36Z [P1] replaced a `_KIND_FOR_STATE` map that named
# only the LAST one. A record does not stop being the thing its intent
# committed and its outcome settled just because it has since been authorized:
# each of those acts signed particular contents, and each signature is
# re-derived from the row as it stands now.
_CHAIN_FOR_STATE = {
    "preparing": (INTENT_KIND,),
    "prepared": (INTENT_KIND, OUTCOME_KIND),
    "held": (INTENT_KIND, OUTCOME_KIND),
    "awaiting-evidence": (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND),
    "blocked": (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND),
    # PUBLICATION COMES BEFORE AUTHORIZATION, owner return136350. The two acts
    # swapped places in the chain rather than merely in the call order, so a
    # row claiming `authorized` must hold a committed PUBLISH act whose
    # signature its own current contents still produce.
    "published": (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND, PUBLISH_KIND),
    "authorized": (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND, PUBLISH_KIND,
                   EVIDENCE_KIND),
    # AND `imported` DEMANDS A TERMINAL ACT NOTHING IN P WRITES. Review
    # 2026-09-10T05:41:11Z [R3]: published and imported were the same four
    # acts, so a corrupted row relabelled `imported` -- with an entry id
    # naming an entry that never existed -- read back as a terminal success.
    # The import transition belongs to Q. Until it exists, every imported row
    # refuses here, which is the conservative direction: a state nothing can
    # legitimately reach is a state nothing may claim.
    "imported": (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND, PUBLISH_KIND,
                 EVIDENCE_KIND, IMPORT_KIND),
}


def _operation_id(kind, result_id):
    return kind + ":" + result_id


def _settled_reason(held):
    """The reason the OUTCOME act settled, which only a HOLD has.

    Review 2026-09-10T05:41:11Z [R1] gave `blocked` a reason of its own, and
    that reason belongs to the OBSERVATION act. Reading the row's current
    reason back into the outcome's signature would make every blocked record
    fail its own earlier act.
    """
    return held["reason"] if held["state"] == "held" else None


def _settled_state(held):
    """WHICH STATE THE OUTCOME ACT SETTLED, recovered rather than read off the
    row's current one.

    Review [P2]: `_outcome_signature` derived the outcome's signature from
    whatever state the record had reached SINCE, so an exact retry after
    authorization compared against a signature that act never used and refused
    an operation-collision on an identical call. A held outcome stays held; any
    record that went further settled as `prepared`.
    """
    return "held" if held["state"] == "held" else "prepared"


def _expected_signature(kind, result_id, held, operands):
    if kind == INTENT_KIND:
        return _signature(INTENT_KIND, operands)
    if kind == OUTCOME_KIND:
        return _signature(OUTCOME_KIND, {
            "result_id": result_id, "state": _settled_state(held),
            "prepared": held["prepared"],
            "content_digest": held["content_digest"],
            "reason": _settled_reason(held), **operands})
    if kind == OBSERVATION_KIND:
        return _observation_signature(held)
    if kind == EVIDENCE_KIND:
        return _evidence_signature(held)
    if kind == IMPORT_KIND:
        # NOBODY WRITES THIS YET. The signature cannot be re-derived because
        # the terminal act has no operands in P, so an imported row can never
        # match and is refused -- deliberately, until Q supplies the act.
        return None
    return _signature(PUBLISH_KIND, {
        "result_id": result_id, "proposal_id": held["derived_proposal_id"],
        "derived_result_id": held["derived_result_id"],
        "derived_result_digest": held["derived_result_digest"],
        "candidate_digest": held["prepared"]["head"],
        "target": held["target_revision"]})


def _row(store, result_id):
    boundaries.identity(result_id, "an integration result identity")
    found = store._connection.execute(
        "SELECT * FROM integration_results WHERE result_id = ?",
        (result_id,)).fetchone()
    if found is None:
        _refuse(f"no integration result {name_value(result_id)}")
    held = boundaries.row(found, "a persisted integration result",
                          schema.RESULT_COLUMNS)
    held["integration_assignment"] = _assignment(
        json.loads(held["integration_assignment"]),
        "a persisted integration assignment")
    held["workspace"] = _place(json.loads(held["workspace"]),
                               "a persisted workspace")
    held["target_source"] = _place(json.loads(held["target_source"]),
                                   "a persisted target source")
    if held["prepared"] is not None:
        held["prepared"] = _prepared(json.loads(held["prepared"]),
                                     held["target_revision"])
        if held["content_digest"] != digest(held["prepared"]["content"]):
            _refuse("a persisted result's content digest does not match its "
                    "own path and mode set",
                    category="integrity", code="digest")
    if held["evidence"] is not None:
        held["evidence"] = json.loads(held["evidence"])
    if held["causal_observations"] is not None:
        held["causal_observations"] = json.loads(held["causal_observations"])
    return held


def _prepared(value, target_revision):
    """The profile's closed prepared-evidence shape, adopted as its own."""
    held = boundaries.document(value, "prepared result evidence",
                               required=("profile", "version", "base", "head",
                                         "tree", "reference", "content"))
    if held["profile"] != PROFILE_NAME or held["version"] != PROFILE_VERSION:
        _refuse("prepared evidence names another profile",
                category="integrity", code="schema")
    for name in ("base", "head", "tree"):
        _object(held[name], f"prepared evidence's {name}")
    boundaries.text(held["reference"], "a prepared reference")
    if held["base"] != target_revision:
        _refuse("prepared evidence names another target snapshot than the "
                "record it belongs to", category="integrity", code="digest")
    content = held["content"]
    if type(content) is not dict or not content:
        _refuse("prepared evidence carries its target-relative content set",
                category="integrity", code="schema")
    for path, entry in content.items():
        boundaries.text(path, "a prepared content path")
        if path.startswith("/") or ".." in path.split("/"):
            _refuse("a prepared content path is relative and canonical",
                    category="integrity", code="path")
        # REVIEW [P1]: A PATH SET IS NOT CONTENT. Each entry names the OBJECT
        # its bytes are as well as its mode, so this record's content digest
        # is a statement about bytes rather than about file names -- which is
        # what let two different combined trees share one digest, and one
        # result's evidence authorize another's.
        taken = boundaries.document(entry, f"the prepared entry at {path!r}",
                                    required=("mode", "object"))
        if taken["mode"] not in ("100644", "100755"):
            _refuse(f"a prepared content path carries mode "
                    f"{name_value(taken['mode'])}; this import owns ordinary "
                    f"file content", category="integrity", code="file-type")
        _object(taken["object"], f"the prepared object at {path!r}")
    return held


# -- the pieces the acts above are composed from -----------------------------


def _signature(kind, operands):
    """This store's own signature text, so a journal row round-trips.

    `integration_signature` is the coordinator's constructor: it sweeps for a
    durable secret and answers CANONICAL TEXT, which is what the operations
    table's `signature` column is contracted to decode. A digest would compare
    just as well and would not be a persisted JSON value.
    """
    return integration_signature(kind, operands)


def _stored(value):
    return canonical_text(value) if isinstance(value, (dict, list)) else value


def _recorded(store, operation_id):
    found = store._connection.execute(
        "SELECT * FROM operations WHERE operation_id = ?",
        (operation_id,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a persisted operation record",
                          schema.OPERATION_COLUMNS)


def _witness(store, row):
    """This owner's semantic proof of one recorded act.

    `IntegrationStore.replay` requires a witness because presence of a journal
    row is not proof of what it materialized. For these two kinds the proof is
    the record itself: an act named `<kind>:<result_id>` must have materialized
    a result whose own operands derive that identity, which is exactly what
    `result_of` establishes.
    """
    kind = row["kind"]
    if kind not in (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND,
                    EVIDENCE_KIND, PUBLISH_KIND):
        _refuse(f"this owner does not witness {name_value(kind)} acts",
                category="integrity", code="schema")
    _prefix, _, result_id = row["operation_id"].partition(":")
    return result_of(store, result_id)


def _profile_capabilities(profile):
    for name in ("prepare", "validate", "content", "revision", "storage"):
        boundaries.capability(getattr(profile, name, None),
                              f"a reconciliation profile's {name} capability")
    return profile
