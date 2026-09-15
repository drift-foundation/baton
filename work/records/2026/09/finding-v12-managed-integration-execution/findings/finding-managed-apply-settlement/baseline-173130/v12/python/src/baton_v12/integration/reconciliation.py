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
from ..contracts import (ContractRefusal, canonical_text, digest,
                        digest_of_bytes)
from ..contracts.errors import name_value, sample_of
from ..worker_manager import boundaries
from . import admission, managed_execution, schema
from .git_profile import PROFILE_NAME, PROFILE_VERSION
from .store import integration_signature

__all__ = ["EVIDENCE_KIND", "IMPORT_KIND", "INTENT_KIND", "OBSERVATION_KIND",
           "OUTCOME_KIND", "PUBLISH_KIND", "MANAGED_KIND",
           "attach_managed_phase", "prepare_result", "publish_result",
           "record_causal_observations", "record_imported",
           "record_managed_result", "record_result_evidence",
           "resolve_import_account", "result_identity", "result_of",
           "managed_result_of", "PUBLICATION_OPERANDS", "publication_of",
           "adopt_prepared_candidate", "PREPARED_CANDIDATE_SCHEMA",
           "PREPARED_CANDIDATE_MEMBERS", "PREPARATION_REPORT_SCHEMA",
           "PREPARATION_REPORT_OUTPUT", "PREPARED_CANDIDATE_OUTPUT",
           "record_publication_intent", "record_publication_effect"]

INTENT_KIND = "result.prepare"
OUTCOME_KIND = "result.prepared"
OBSERVATION_KIND = "result.observed"
EVIDENCE_KIND = "result.evidence"
PUBLISH_KIND = "result.publish"

# THE TERMINAL IMPORT ACT. Review 2026-09-10T05:41:11Z [R3]: `imported` was
# reachable in a corrupted row and the reader accepted it, because published
# and imported were checked as the same four acts. The chain below demands THIS
# act for an imported row.
#
# W133120 SUPPLIES IT, under owner return136677's approved
# AMENDMENT-terminal-custody-paths-v1: P deliberately left
# `_expected_signature` answering None here, so no legitimate terminal success
# could read back either. `record_imported` is that owner, and it proves the
# integrated entry and the Authority's own integration receipt rather than
# accepting a caller's word that an import happened.
IMPORT_KIND = "result.imported"

# W161230 slice1 condition 4: the act that records what ONE managed phase left
# behind. It is not a result state transition and never becomes one -- a
# managed result is an account of an execution, and which target verb it earns
# is still decided by the owners that hold the target.
MANAGED_KIND = "result.managed"

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
            # W161230 slice1 condition 4: THE SHARED KEY, claimed here too. A
            # managed result already holding this target snapshot for this
            # submission is the same collision the table's own UNIQUE would
            # refuse if both rows lived in one relation.
            _claim_result_key(connection, operands["canonical_target_id"],
                              operands["source_proposal_id"],
                              operands["target_revision"],
                              writing="integration_results")
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


# W156162, owner ruling M157653 (Slawomir 2026-09-13T09:19:44Z) approving
# HOST-FAILURE-PROPOSAL-2026-09-13.md. A HOST VERIFICATION THAT PRODUCED NO
# EXIT STATUS, told as itself.
#
# THE PROBLEM THE RULING ANSWERS. `_observation` requires an actual integer
# status, and a required test that outlasted its ceiling or could not be started
# has none. Returning `None` through the success shape was refused before
# anything was retained, so nothing was recorded and every poll re-ran the
# command; raising instead preserved the reason and left no custody at all.
#
# SO THE FAILURE IS A SEPARATE, CLOSED ANSWER. It is tagged, it never carries a
# guessed return code, and the SUCCESSFUL integer shape above is untouched --
# `_OBSERVATIONS` and `_observation` mean exactly what they meant, so every
# completed legacy observation reads back the same.
FAILURE_TAG = "host-verification-failed"
FAILURE_SCHEMA = "baton.v12.host-verification-failure/1"

# THE PHASES A HOST VERIFICATION CAN FAIL IN, in the order the causal owner runs
# them. `post-import` is the second host boundary and is adopted by `execution`,
# not here; it is named in one place so the two owners cannot drift.
CAUSAL_PHASES = ("combined", "base", "isolated")
POST_IMPORT_PHASE = "post-import"
FAILURE_PHASES = CAUSAL_PHASES + (POST_IMPORT_PHASE,)

# AND THE ONLY TWO WAYS A CHILD SUPPLIES NO STATUS: it ran past its bound, or it
# never started. A third word would be this build inventing a category, and a
# generic exception is not relabelled into either of these.
FAILURE_REASONS = ("timeout", "start-failed")

# THE ONE EXECUTION ENVIRONMENT THIS OWNER CONFIGURES. The successful
# observations already carry it as a fixed word; a failure that named another
# one would be a failure of some other execution.
EXECUTION_ENVIRONMENT = "configured-required-test"

FAILURE_MEMBERS = ("schema", "phase", "reason", "detail", "seconds",
                   "command", "test_identity", "test_digest", "environment",
                   "execution", "input_commit", "input_tree", "completed",
                   "not_run")


def failed_observation(*, phase, reason, detail, seconds, command,
                       test_identity, test_digest, environment, execution,
                       input_commit, input_tree, completed, not_run):
    """Compose one closed host-verification failure answer.

    COMPOSED HERE so the two host owners cannot spell it differently, and so a
    caller supplies facts rather than a document shape.
    """
    return {"schema": FAILURE_SCHEMA, "phase": phase, "reason": reason,
            "detail": detail, "seconds": seconds, "command": list(command),
            "test_identity": test_identity, "test_digest": test_digest,
            "environment": environment, "execution": execution,
            "input_commit": input_commit, "input_tree": input_tree,
            "completed": dict(completed), "not_run": list(not_run)}


def is_failed_observation(given):
    """Whether this answer is the failure branch rather than the success one."""
    return (type(given) is dict
            and given.get("schema") == FAILURE_SCHEMA)


def _failure(given, held, actor, *, phases, what, expected=None):
    """Validate one closed failure answer against the content it is about.

    EVERY BINDING THE RULING NAMES IS CHECKED HERE: the phase is one this owner
    runs, the reason is one of the two closed words, the bound is the positive
    number of seconds that was actually applied, no exit status is present
    anywhere, the completed PREFIX carries real integer statuses under the same
    pinned harness, the phases that did NOT run carry no evidence at all, and
    the attesting execution is the owner that answered.
    """
    taken = boundaries.document(given, what, required=FAILURE_MEMBERS)
    if taken["phase"] not in phases:
        _refuse(f"{what} names phase {name_value(taken['phase'])} and this "
                f"owner runs {sample_of(list(phases))}",
                category="integrity", code="schema")
    if taken["reason"] not in FAILURE_REASONS:
        _refuse(f"{what} names reason {name_value(taken['reason'])}; a command "
                f"that supplied no exit status either ran past its bound or "
                f"never started, and nothing else is relabelled into those",
                category="integrity", code="schema")
    if type(taken["seconds"]) is not int or type(taken["seconds"]) is bool \
            or taken["seconds"] < 1:
        _refuse(f"{what} carries the whole number of seconds that was actually "
                f"applied to the command", category="integrity", code="schema")
    for member in ("detail", "test_identity", "test_digest", "environment",
                   "execution", "input_commit", "input_tree"):
        boundaries.text(taken[member], f"{what}'s {member}")
    if type(taken["command"]) is not list or not taken["command"]:
        _refuse(f"{what} names the command words it ran",
                category="integrity", code="schema")
    for word in taken["command"]:
        boundaries.text(word, f"{what}'s command word")
    if taken["execution"] != actor:
        _refuse(f"{what} was produced by {name_value(taken['execution'])} and "
                f"this owner attested {name_value(actor)}",
                category="policy", code="denied")
    # THE COMPLETED PREFIX, AND THE REMAINDER THAT DID NOT RUN.
    if type(taken["completed"]) is not dict:
        _refuse(f"{what} records the phases that completed before it",
                category="integrity", code="schema")
    if type(taken["not_run"]) is not list:
        _refuse(f"{what} records the phases that did not run",
                category="integrity", code="schema")
    order = list(phases)
    where = order.index(taken["phase"])
    if sorted(taken["completed"]) != sorted(order[:where]):
        _refuse(f"{what} failed at {name_value(taken['phase'])} and names "
                f"{sample_of(sorted(taken['completed']))} as its completed "
                f"prefix; the prefix is exactly the phases this owner runs "
                f"before it", category="integrity", code="schema")
    if sorted(taken["not_run"]) != sorted(order[where + 1:]):
        _refuse(f"{what} failed at {name_value(taken['phase'])} and names "
                f"{sample_of(sorted(taken['not_run']))} as not run; a phase "
                f"after the failed one did not run and no other phase may "
                f"claim to be in that set", category="integrity", code="schema")
    for name, one in taken["completed"].items():
        held_one = _observation(one, f"{what}'s completed {name} observation")
        # EACH COMPLETED PHASE IS BOUND TO THE RESULT'S OWN CONTENT TOO. [P1]:
        # a base failure accepted a foreign completed-combined commit, tree or
        # environment independently of the failed phase's bindings.
        if held is not None:
            want = {"combined": (held["prepared"]["head"],
                                 held["prepared"]["tree"]),
                    "base": (held["source_base"], None),
                    "isolated": (held["source_candidate"], None)}.get(name)
            if want is not None:
                commit, tree = want
                if held_one["input_commit"] != commit:
                    _refuse(f"{what}'s completed {name} observation ran "
                            f"against {name_value(held_one['input_commit'])} "
                            f"and this result's {name} content is "
                            f"{name_value(commit)}",
                            category="integrity", code="digest")
                if tree is not None and held_one["input_tree"] != tree:
                    _refuse(f"{what}'s completed {name} observation ran "
                            f"against tree "
                            f"{name_value(held_one['input_tree'])} and this "
                            f"result prepared {name_value(tree)}",
                            category="integrity", code="digest")
        if held_one["environment"] != EXECUTION_ENVIRONMENT:
            _refuse(f"{what}'s completed {name} observation names environment "
                    f"{name_value(held_one['environment'])}",
                    category="integrity", code="schema")
        if held_one["test_digest"] != taken["test_digest"]:
            _refuse(f"{what}'s completed {name} observation ran another "
                    f"harness; one pinned harness is run against every state",
                    category="integrity", code="digest")
        if held_one["execution"] != actor:
            _refuse(f"{what}'s completed {name} observation was produced by "
                    f"{name_value(held_one['execution'])}",
                    category="policy", code="denied")
    # AND THE CONTENT IT RAN AGAINST IS THE RESULT'S OWN. Review
    # 2026-09-13T09:34:47Z [P1]: the first form of this validator DISCARDED
    # `held`, so a failure answer could name a foreign commit, tree, command,
    # harness or environment and be retained durably in blocked custody. A
    # failure this owner keeps is evidence about THIS result or it is not
    # evidence at all.
    #
    # WHICH CONTENT EACH PHASE IS ABOUT is the same table `_causal` enforces
    # for the successful observations, so the failed phase is held to exactly
    # what the completed one would have been.
    if held is not None:
        # NAMED `content` AND NOT `expected`: the parameter of that name is the
        # CONFIGURED expectation, and shadowing it here made the comparison
        # below silently skip every member -- caught by its own case failing.
        content = {
            "combined": (held["prepared"]["head"], held["prepared"]["tree"]),
            "base": (held["source_base"], None),
            "isolated": (held["source_candidate"], None)}.get(taken["phase"])
        if content is not None:
            commit, tree = content
            if taken["input_commit"] != commit:
                _refuse(f"{what} ran against commit "
                        f"{name_value(taken['input_commit'])} and this "
                        f"result's {taken['phase']} content is "
                        f"{name_value(commit)}",
                        category="integrity", code="digest")
            if tree is not None and taken["input_tree"] != tree:
                _refuse(f"{what} ran against tree "
                        f"{name_value(taken['input_tree'])} and this result "
                        f"prepared {name_value(tree)}",
                        category="integrity", code="digest")
    # AND THE COMMAND, TASK AND BOUND ARE THE CONFIGURED ONES. Review
    # 2026-09-13T09:48:11Z [P1]: a probe changed ONLY `seconds`, from the 77
    # this deployment applied to 999999, and both the causal custody and the
    # post-import adoption took it -- because every check here was about the
    # answer's SELF-CONSISTENCY. An unrelated command, task identity or harness
    # digest was accepted the same way. A positive-integer rule and a maximum
    # cannot fix that: what is needed is the value this deployment actually
    # configured, and the configured owner is what holds it.
    #
    # SO THE OWNER IS ASKED, exactly as it is asked for its participant. The
    # expectations arrive from the owner object, never from the document under
    # validation, and a failure that disagrees with them is not this
    # execution's.
    if expected is not None:
        for member in ("command", "test_identity", "test_digest", "seconds"):
            if member not in expected:
                continue
            wanted = expected[member]
            answered = taken[member]
            if member == "command":
                wanted, answered = list(wanted), list(answered)
            if answered != wanted:
                _refuse(f"{what} names {member} {name_value(answered)} and "
                        f"this deployment configured {name_value(wanted)}",
                        category="integrity", code="schema")
    if taken["environment"] != EXECUTION_ENVIRONMENT:
        _refuse(f"{what} names environment "
                f"{name_value(taken['environment'])}; this owner keeps "
                f"failures of the {name_value(EXECUTION_ENVIRONMENT)} it "
                f"configured", category="integrity", code="schema")
    # AND THE COMPLETED PREFIX AGREES WITH IT ABOUT THE COMMAND AND HARNESS.
    # A prefix that ran another command is not this failure's own execution.
    for name, one in taken["completed"].items():
        if list(one["command"]) != list(taken["command"]):
            _refuse(f"{what}'s completed {name} observation ran "
                    f"{sample_of(list(one['command']))} and the failed phase "
                    f"ran {sample_of(list(taken['command']))}; one configured "
                    f"command is run against every state",
                    category="integrity", code="schema")
        if one["test_identity"] != taken["test_identity"]:
            _refuse(f"{what}'s completed {name} observation names task "
                    f"{name_value(one['test_identity'])} and the failed phase "
                    f"names {name_value(taken['test_identity'])}",
                    category="integrity", code="schema")
    return taken


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
    # W156162, owner ruling M157653: EITHER THE THREE OBSERVATIONS OR ONE
    # CLOSED FAILURE. A host command that supplied no exit status cannot be
    # told in the success shape, and the answer that says so is retained here
    # with the same custody a failing combination already gets -- so the failed
    # execution is visible, the result is blocked, and no poll re-runs it.
    if is_failed_observation(answer["observations"]):
        causal = _failure(answer["observations"], held, execution,
                          phases=CAUSAL_PHASES,
                          what="the host verification failure",
                          expected=_expectations(observer))
        state = "blocked"
        reason = (f"the {causal['phase']} causal observation supplied NO EXIT "
                  f"STATUS ({causal['reason']}) under this Job's "
                  f"{causal['seconds']}s host_verification ceiling; "
                  f"{causal['detail']}. The phases before it are retained with "
                  f"their own statuses and the phases after it did not run")
    else:
        causal = _causal(answer["observations"], held, execution)
        passed = causal["combined"]["status"] == 0
        state = "awaiting-evidence" if passed else "blocked"
        reason = None if passed else (
            f"the combined result FAILED its own causal observation with "
            f"status {causal['combined']['status']}; a combined failure blocks "
            f"integration and is not verified away, and the isolated positive "
            f"is retained beside it")
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


def _expectations(owner):
    """What this CONFIGURED OWNER says it was configured with, or `None`.

    Asked of the owner object the same way its participant is, and never read
    from the document under validation -- which is the whole point: a failure
    answer cannot vouch for its own command, task or bound.

    `None` is an owner that does not publish them, and the bindings that do not
    depend on them still apply.
    """
    held = getattr(owner, "expectations", None)
    if held is None:
        return None
    if type(held) is not dict:
        _refuse("a configured owner's expectations are a document",
                category="integrity", code="schema")
    return dict(held)


def adopt_failed_post_import(answered, actor, basis, expected=None):
    """Adopt the POST-IMPORT host failure, bound to the imported content.

    W156162, owner ruling M157653 step 3. The same closed semantics the causal
    branch uses, with the imported binding: the phase is this boundary's own,
    and it has no completed prefix because it is one command rather than three.
    """
    taken = _failure(answered, None, actor, phases=(POST_IMPORT_PHASE,),
                     what="the post-import host verification failure",
                     expected=expected)
    for member in ("input_commit", "input_tree"):
        if taken[member] != basis[member]:
            _refuse(f"the post-import failure was recorded against {member} "
                    f"{name_value(taken[member])} and the imported result is "
                    f"{name_value(basis[member])}; evidence about other bytes "
                    f"is not this import's",
                    category="integrity", code="digest")
    return taken


def failed_host_verification(store, result_id):
    """The retained host-verification failure for one result, or `None`.

    W156162, owner ruling M157653 step 4: THE DURABLE CUSTODY A HOST OWNER
    CONSULTS BEFORE IT MATERIALIZES OR RUNS ANYTHING. A process-local memo
    forgets on reopen; this is the same JSON custody the successful
    observations live in, read back through the result's own public reader, so
    a fresh process reaches the same answer.

    IT ANSWERS ABOUT THIS RESULT AND NOTHING ELSE. Two results, two Jobs, or the
    causal and post-import phases of one result never reuse each other's
    outcome: the answer carries its own phase and the caller compares it.
    """
    held = result_of(store, result_id)
    if held is None:
        return None
    answer = held.get("causal_observations")
    return answer if is_failed_observation(answer) else None


def _observation_signature(held):
    """The signature the OBSERVATION act was recorded under, re-derived from
    the row rather than from the state it has reached since."""
    # W156162, owner ruling M157653: A RETAINED FAILURE HAS NO COMBINED STATUS
    # TO READ. It settled `blocked` and its reason is the row's own, so the
    # signature is re-derived from the same two members without asking the
    # success shape a question it cannot answer. Every completed legacy
    # observation still derives exactly as it did.
    answers = held["causal_observations"]
    passed = (False if is_failed_observation(answers)
              else answers["combined"]["status"] == 0)
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


# -- the terminal transition -------------------------------------------------


# The Authority's integration receipt, which is a receipt like the other three
# and is read through exactly the same closed member set.
_INTEGRATED = "integrated"


def _integrated_entry(store, held, entry_id):
    """The coordinator's own entry for this result, proved terminal.

    THE ENTRY IS THE COORDINATOR'S STATEMENT and this record does not take it
    on trust from the caller. It must exist, be on THIS result's target, be
    `integrated`, and retain an eligibility account naming this result's own
    derived proposal, derived result identity and digest, prepared candidate
    and pinned target. An entry admitted for anything else is somebody else's
    import.
    """
    boundaries.identity(entry_id, "an integration entry id")
    row = store._connection.execute(
        "SELECT entry_id, canonical_target_id, state, proposal_id, "
        "result_id, result_digest, candidate_digest, expected_target_revision "
        "FROM entries WHERE entry_id = ?", (entry_id,)).fetchone()
    if row is None:
        _refuse(f"this coordinator holds no entry {name_value(entry_id)}; a "
                f"terminal import is recorded against the entry that actually "
                f"integrated it", category="integrity", code="schema")
    if row["canonical_target_id"] != held["canonical_target_id"]:
        _refuse(f"entry {name_value(entry_id)} is on target "
                f"{name_value(row['canonical_target_id'])} and this result is "
                f"on {name_value(held['canonical_target_id'])}",
                category="integrity", code="schema")
    if row["state"] != _INTEGRATED:
        _refuse(f"entry {name_value(entry_id)} is {name_value(row['state'])}; "
                f"a result is imported through an entry the coordinator "
                f"actually integrated", category="integrity", code="schema")
    for member, expected in (
            ("proposal_id", held["derived_proposal_id"]),
            ("result_id", held["derived_result_id"]),
            ("result_digest", held["derived_result_digest"]),
            ("candidate_digest", held["prepared"]["head"]),
            ("expected_target_revision", held["target_revision"])):
        if row[member] != expected:
            _refuse(f"entry {name_value(entry_id)} was admitted with {member} "
                    f"{name_value(row[member])} and this result's is "
                    f"{name_value(expected)}; an entry for another candidate "
                    f"supplies no terminal authority",
                    category="integrity", code="digest")
    return {name: row[name] for name in row.keys()}


def _integration_receipt(authority, held):
    """The Authority's own integration receipt on the DERIVED proposal.

    The producer's proposal has its own receipts and its own history; this act
    is about the candidate THIS record published, so the receipt must be on
    that proposal, name this candidate and this target, and say `integrated`.
    """
    boundaries.capability(getattr(authority, "receipt", None),
                          "the Authority's receipt read")
    answer = authority.receipt(held["derived_proposal_id"], "integration")
    if answer is None:
        _refuse(f"the Authority holds no integration receipt on derived "
                f"proposal {name_value(held['derived_proposal_id'])}; an "
                f"import is terminal when the Authority says it integrated "
                f"this candidate, not when a caller says so",
                category="policy", code="denied")
    document = boundaries.document(answer, "the integration receipt",
                                   required=_RECEIPT_MEMBERS)
    boundaries.identity(document["receipt_id"], "an integration receipt id")
    if document["kind"] != "integration" \
            or document["proposal_id"] != held["derived_proposal_id"]:
        _refuse(f"the adopted receipt is the {name_value(document['kind'])} of "
                f"{name_value(document['proposal_id'])} and this result needs "
                f"the integration receipt of "
                f"{name_value(held['derived_proposal_id'])}",
                category="integrity", code="schema")
    if document["disposition"] != _INTEGRATED:
        _refuse(f"the Authority's integration receipt is "
                f"{name_value(document['disposition'])}",
                category="policy", code="denied")
    for member, expected in (("candidate_digest", held["prepared"]["head"]),
                             ("target", held["target_revision"])):
        if document[member] != expected:
            _refuse(f"the Authority's integration receipt names {member} "
                    f"{name_value(document[member])} and this result's is "
                    f"{name_value(expected)}",
                    category="integrity", code="digest")
    if document["decision"] is None:
        _refuse("the Authority's integration receipt names no authorization "
                "decision", category="integrity", code="schema")
    return document


def record_imported(store, authority, *, result_id, entry_id):
    """The terminal act: this result's bytes are ON the target, and accounted.

    OWNER return136677's AMENDMENT-terminal-custody-paths-v1. P named
    `IMPORT_KIND`, required it for an imported row and deliberately wrote no
    owner for it, so every terminal state -- fabricated OR legitimate --
    refused. This is that owner, and it is the last durable act of an import.

    IT PROVES, IT IS NOT TOLD. There is no success operand. The coordinator's
    entry must be integrated, on this result's target, and admitted with this
    result's own derived identity and pinned target; the Authority must hold
    an integration receipt on the DERIVED proposal naming this candidate and
    this target; and `result_of` has already re-derived every earlier act's
    signature from the row as it stands now.

    WHY IT IS LAST, AND WHY THAT IS SAFE. The Authority receipt, the
    coordinator settlement and the release each own their own act, and this
    records custody of what they did. An interruption before it leaves the
    entry integrated and this row authorized, which the same call settles on
    replay -- and it cannot import twice, because the dedicated target's
    reference has already advanced and `resolve_import_account` refuses a
    result whose target moved. The exhaustive crash-ordering matrix is parked
    at W136578 and nothing here claims it.

    AN EXACT RETRY REPLAYS, like every other act in this record.
    """
    held = result_of(store, result_id)
    operation_id = _operation_id(IMPORT_KIND, result_id)
    if held["state"] not in ("authorized", "imported"):
        _refuse(f"result {name_value(result_id)} is {name_value(held['state'])}"
                f"; a terminal import is recorded for a result its own owners "
                f"authorized")
    entry = _integrated_entry(store, held, entry_id)
    receipt = _integration_receipt(authority, held)
    signature = _import_signature(held, entry_id)
    if held["state"] == "imported":
        recorded = _recorded(store, operation_id)
        if recorded is not None and recorded["signature"] == signature:
            settled, _held = store.replay(operation_id, signature,
                                          kind=IMPORT_KIND, witness=_witness)
            if settled:
                return held
        _refuse(f"result {name_value(result_id)} is already imported through "
                f"entry {name_value(held['entry_id'])}; a terminal import is "
                f"not recorded twice", code="operation-collision")

    def act(connection):
        current = connection.execute(
            "SELECT state FROM integration_results WHERE result_id = ?",
            (result_id,)).fetchone()
        if current is None or current["state"] != "authorized":
            _refuse(f"result {name_value(result_id)} changed while its "
                    f"terminal import was being proved",
                    code="operation-collision")
        connection.execute(
            "UPDATE integration_results SET state = 'imported', "
            "entry_id = ?, operation_id = ? WHERE result_id = ?",
            (entry_id, operation_id, result_id))
        return {"result_id": result_id, "state": "imported",
                "entry_id": entry_id}

    store.transact(operation_id, IMPORT_KIND, signature, act, witness=_witness)
    return dict(result_of(store, result_id), integration_receipt=receipt,
                entry=entry)


def _import_signature(held, entry_id):
    """The operands the terminal act is signed under, ALL of them recoverable
    from the row -- which is what lets `result_of` re-derive it and refuse a
    row that was relabelled `imported` without one."""
    return _signature(IMPORT_KIND, {
        "result_id": held["result_id"], "entry_id": entry_id,
        "canonical_target_id": held["canonical_target_id"],
        "derived_proposal_id": held["derived_proposal_id"],
        "derived_result_id": held["derived_result_id"],
        "derived_result_digest": held["derived_result_digest"],
        "candidate_digest": held["prepared"]["head"],
        "target": held["target_revision"]})


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
    # AND THIS SUBMISSION IS HELD IN ONE REPRESENTATION. Review
    # 2026-09-13T18:51:48Z [P1]: the writers checked both tables and neither
    # READER did, so a store carrying a duplicate answered it normally from
    # whichever side was asked. Reader ownership is where that is decided -- a
    # writer's care is not a property of the bytes a later reader finds.
    if store.managed_results_available():
        _one_representation(store._connection, held["canonical_target_id"],
                            held["source_proposal_id"],
                            held["target_revision"],
                            expected="integration_results")
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
        # `eligibility` IS NOT A COLUMN, and P never found out. It is derived
        # by `queue._entry_row` from the fifteen members, and selecting it here
        # raised `OperationalError` out of a typed reader -- which nothing
        # reached, because P wrote no terminal act and every imported row
        # refused before this line. W133120's first real terminal readback is
        # what ran it. The three members this check actually uses are the ones
        # it now asks for.
        entry = store._connection.execute(
            "SELECT entry_id, canonical_target_id, state "
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
        # W133120 SUPPLIES THE OPERANDS P DELIBERATELY LEFT ABSENT. Every one
        # of them is recovered from the row itself, so a row relabelled
        # `imported` without the act -- or pointed at another entry than the
        # one the act named -- still fails this comparison.
        return _import_signature(held, held["entry_id"])
    return _signature(PUBLISH_KIND, {
        "result_id": result_id, "proposal_id": held["derived_proposal_id"],
        "derived_result_id": held["derived_result_id"],
        "derived_result_digest": held["derived_result_digest"],
        "candidate_digest": held["prepared"]["head"],
        "target": held["target_revision"]})


def _claim_result_key(connection, canonical_target_id, source_proposal_id,
                      target_revision, *, writing):
    """The (target, proposal, revision) key, held across BOTH representations.

    W161230 slice1 condition 4. Each table carries its own UNIQUE over these
    three columns, and SQLite cannot enforce one ACROSS two tables -- so this
    is the rule neither constraint can state alone, asked inside the caller's
    own transaction where the answer cannot go stale between the check and the
    write. `schema.RESULT_KEY` names the columns once so the two writers cannot
    drift to different keys.

    ONE LIVE RESULT PER SUBMISSION PER TARGET SNAPSHOT, whichever table holds
    it. A later target advance needs a NEW result from the same submission; it
    never mutates this one, and it never gets a second one alongside it in the
    other representation.
    """
    # BOTH TABLES, INCLUDING THE ONE BEING WRITTEN. Measured, step 66: asking
    # only about the OTHER representation left an in-table collision to the
    # column constraint, which arrives as a raw `sqlite3.IntegrityError` from
    # inside a transaction rather than as this coordinator's refusal. The
    # per-table UNIQUEs stay as the structural backstop -- they are what makes
    # the rule hold even if a future writer forgets to ask -- and this is what
    # makes the ordinary answer a refusal a caller can handle.
    for table in ("integration_results", "managed_integration_results"):
        found = connection.execute(
            f"SELECT 1 FROM {table} WHERE canonical_target_id = ? "
            f"AND source_proposal_id = ? AND target_revision = ?",
            (canonical_target_id, source_proposal_id,
             target_revision)).fetchone()
        if found is not None:
            _refuse(f"target {name_value(canonical_target_id)} already holds "
                    f"a result for proposal {name_value(source_proposal_id)} "
                    f"at revision {name_value(target_revision)} in {table}; "
                    f"one submission has one result per target snapshot, in "
                    f"either representation",
                    code="operation-collision")


# THE SUBMISSION IDENTITIES A MANAGED RESULT IS A RESULT *FOR*, named with
# the same words the legacy relation names them by -- taken from `_FIXED` so
# the two cannot drift to different spellings of one submission. The legacy
# operands this deliberately does NOT include are the ones that describe where
# a coordinator did the work: `workspace`, `target_source`, `profile_name` and
# `profile_version`. A managed result is portable, and the accepted design is
# explicit that a coordinator absolute path is exactly what must not travel in
# one.
_MANAGED_SOURCE = tuple(name for name in _FIXED
                        if name not in ("canonical_target_id",
                                        "integration_attempt_id",
                                        "integration_assignment", "workspace",
                                        "profile_name", "profile_version",
                                        "target_revision", "target_source",
                                        "target_reference"))


def _managed_submission(value):
    """The submission identities, owned by the same rules the legacy row's are.

    `_fixed_operands` owns the whole legacy operand set including the four
    location-bearing members a portable result must not carry, so this owns the
    SUBSET rather than calling it -- with each member under the identical rule:
    identities as identities, digests as text, and the two object names as full
    object names, so a revision expression cannot reach a record here either.
    """
    held = boundaries.document(value, "a managed result's submission",
                               required=_MANAGED_SOURCE)
    owned = {}
    for name in ("job_id", "work_id", "line_id", "source_checkpoint_id",
                 "source_verdict_id", "source_proposal_id",
                 "source_result_id"):
        owned[name] = boundaries.identity(held[name], f"a result's {name}")
    for name in ("authority_uuid", "source_result_digest",
                 "source_checkpoint_digest"):
        owned[name] = boundaries.text(held[name], f"a result's {name}")
    for name in ("source_base", "source_candidate"):
        owned[name] = _object(held[name], f"a result's {name}")
    return owned


def _one_representation(connection, canonical_target_id, source_proposal_id,
                        target_revision, *, expected):
    """Refuse a key held in BOTH representations, on the way OUT as well as in.

    REVIEW 2026-09-13T18:51:48Z [P1]: the writers checked both tables and the
    READERS checked neither, so a store carrying a duplicate -- however it came
    to carry one -- answered it normally from whichever side was asked. The
    accepted design says reads refuse a double representation, and reader
    ownership is where that is decided: a writer's care is not a property of
    the bytes a later reader finds.

    `expected` is the table the caller is reading from, so the refusal names
    the one that should not also hold it.
    """
    holding = [table for table in ("integration_results",
                                   "managed_integration_results")
               if connection.execute(
                   f"SELECT 1 FROM {table} WHERE canonical_target_id = ? "
                   f"AND source_proposal_id = ? AND target_revision = ?",
                   (canonical_target_id, source_proposal_id,
                    target_revision)).fetchone() is not None]
    if len(holding) > 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"target {name_value(canonical_target_id)} holds proposal "
            f"{name_value(source_proposal_id)} at revision "
            f"{name_value(target_revision)} in {' and '.join(holding)}; one "
            f"submission has one result per target snapshot, and a store "
            f"carrying two representations of it cannot be read as either")
    if expected not in holding:
        raise ContractRefusal(
            "integrity", "schema",
            f"the {expected} row for proposal "
            f"{name_value(source_proposal_id)} at revision "
            f"{name_value(target_revision)} is not held by its own table")


def _managed_operands(row):
    """The EXACT immutable request this RESULT was created by.

    Rebuilt from the materialized row, member for member, as the writer signed
    it -- and carrying no phase, because creation retains none. This is the
    whole of the journal binding for the result itself: if the rebuild does
    not reproduce the committed signature, some part of what is stored is not
    what was asked for.
    """
    return {"managed_result_id": row["managed_result_id"],
            "orchestration_id": row["orchestration_id"],
            "canonical_target_id": row["canonical_target_id"],
            "target_revision": row["target_revision"],
            "submission": {name: row[name] for name in _MANAGED_SOURCE},
            "phases": []}


def _attachment_operands(row, phase, account):
    return {"managed_result_id": row["managed_result_id"], "phase": phase,
            "task": account["task"], "result": account["result"]}


def _creation_id(managed_result_id):
    """The identity a managed result's CREATION act commits under.

    LENGTH-PREFIXED, AND SO IS THE ATTACHMENT BELOW, because the two sets must
    not intersect. Review 2026-09-13T23:28:58Z [P2]: creation of a result named
    `root/prepare` and the preparation attached to a result named `root` both
    composed `result.managed:root/prepare`, so two different acts about two
    different results shared one journal identity -- and each collided with the
    other in both orders. Forbidding a slash in an orchestration id would be
    the narrowed grammar the previous review already rejected.

    WHY THE PREFIX IS ENOUGH. Every identity here begins with the decimal
    length of the result id and a colon. For a creation `<n>:<id>` to equal an
    attachment `<m>:<other>/<phase>` the digits before the first colon must be
    equal, so n == m; but then `<id>` equals `<other>/<phase>` while their
    lengths differ by `len(phase) + 1`. The two families cannot meet.

    THE STORE THIS SLICE ADDS IS UNRELEASED. Schema 6 is introduced by this
    Work and no coordinator in the world holds the earlier spelling, so there
    is no old identity to keep reading -- and the reader below derives these
    rather than trusting what a row points at.
    """
    return f"{MANAGED_KIND}:{len(managed_result_id)}:{managed_result_id}"


def _attachment_id(managed_result_id, phase):
    """The identity ONE phase's attachment act commits under."""
    return (f"{MANAGED_KIND}:{len(managed_result_id)}:{managed_result_id}"
            f"/{phase}")


def _signed_attachment(record):
    """The result an ATTACHMENT act belongs to, read from its own operands.

    Absence is the answer for a creation act and for anything this owner
    cannot read as one of its own: the caller is asking which attachments a
    result has, and a document that does not say is not an attachment of it.
    """
    try:
        operands = json.loads(record["signature"])["operands"]
    except (TypeError, ValueError, KeyError):
        return None
    if type(operands) is not dict or "phase" not in operands:
        return None
    # A PUBLICATION IS NOT A PHASE ATTACHMENT, though both are acts of this
    # kind about one result and both name a phase. Measured, step 123: the
    # reverse scan counted publication acts as attachments and then demanded a
    # phase row for each, so recording a publication made its own result
    # unreadable. The publication's operands name the publication; an
    # attachment's do not.
    if "publication_id" in operands:
        return None
    return operands.get("managed_result_id")


def _signed_result(record):
    """The result ANY act of this kind belongs to, attachment or creation."""
    try:
        operands = json.loads(record["signature"])["operands"]
    except (TypeError, ValueError, KeyError):
        return None
    return operands.get("managed_result_id") \
        if type(operands) is dict else None


def _committed_act(store, operation_id, signature):
    """One committed act of this owner's kind, at this identity, signed thus.

    THE THREE TOGETHER. The identity alone says an act with this name
    committed; the kind alone says an act of this sort did; the signature is
    what says it was THIS request. A row bound by fewer than three is bound to
    a neighbour of itself.
    """
    # THE ONE ACT BETWEEN ITS WRITE AND ITS RECORD is this store's own known
    # window, and it is excused HERE by its signed operands rather than by its
    # identity. An act reads back the rows it has just written and its journal
    # row does not exist yet; what that window may excuse is exactly the act
    # asking, signed over exactly what these rows produce -- never a general
    # "this row has no record yet" allowance, which would readmit every
    # fabricated row.
    pending = store._pending
    if pending is not None and pending["operation_id"] == operation_id:
        if pending["kind"] != MANAGED_KIND \
                or pending["signature"] != signature:
            raise ContractRefusal(
                "integrity", "schema",
                f"the act committing as {name_value(operation_id)} is signed "
                f"over operands these rows do not produce")
        return pending
    found = store._connection.execute(
        "SELECT * FROM operations WHERE operation_id = ?",
        (operation_id,)).fetchone()
    if found is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"this store holds no act {name_value(operation_id)}; a managed "
            f"row whose own act is not in the journal is a row nobody is "
            f"recorded as having written")
    record = boundaries.row(found, "a persisted operation record",
                            schema.OPERATION_COLUMNS)
    if record["state"] != "committed" or record["kind"] != MANAGED_KIND:
        raise ContractRefusal(
            "integrity", "schema",
            f"the act {name_value(operation_id)} is "
            f"{name_value(record['state'])} {name_value(record['kind'])}; a "
            f"managed row is bound to a committed "
            f"{name_value(MANAGED_KIND)} act")
    if record["signature"] != signature:
        raise ContractRefusal(
            "integrity", "schema",
            f"the act {name_value(operation_id)} was signed over operands "
            f"these rows do not produce; what is stored is not what was asked "
            f"for")
    return record


# WHICH COMMITTED ACT EACH STATE RESTS ON. Creation materializes `preparing`
# and nothing else, so every other state is one a later act must have
# journalled -- and this slice has written none of those acts yet. A row
# sitting in another state is therefore a row whose transition nobody
# recorded, and it is refused rather than reported. The mapping is here, and
# not a `!= "preparing"` test, so a later act slots into it by being named.
_MANAGED_STATE_ACT = {"preparing": None}


def record_managed_result(store, submission, *, orchestration_id,
                          canonical_target_id, target_revision):
    """Create ONE portable managed result. It holds no phase yet.

    REVIEW 2026-09-13T19:07:44Z: creation used to take the whole phase set at
    once, so a preparation retained on its own could never be joined by an
    apply -- the later call changed the one immutable creation operation and
    collided. The accepted sequence is a preparation that runs, is retained,
    and is FOLLOWED by an apply, so phases attach through their own journalled
    acts and creation replays exactly whatever has attached since.

    IT SETTLES NOTHING. `preparing` is a committed intent, not an outcome.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    boundaries.identity(canonical_target_id, "a canonical target id")
    boundaries.text(target_revision, "a target revision")
    held = _managed_submission(submission)
    managed_result_id = orchestration_id
    operation_id = _creation_id(managed_result_id)
    operands = {"managed_result_id": managed_result_id,
                "orchestration_id": orchestration_id,
                "canonical_target_id": canonical_target_id,
                "target_revision": target_revision,
                "submission": held, "phases": []}
    signature = _signature(MANAGED_KIND, operands)

    def create(connection):
        _claim_result_key(connection, canonical_target_id,
                          held["source_proposal_id"], target_revision,
                          writing="managed_integration_results")
        connection.execute(
            "INSERT INTO managed_integration_results (managed_result_id, "
            "operation_id, canonical_target_id, orchestration_id, "
            "authority_uuid, work_id, job_id, line_id, source_checkpoint_id, "
            "source_verdict_id, source_proposal_id, source_result_id, "
            "source_result_digest, source_checkpoint_digest, source_base, "
            "source_candidate, target_revision, state, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "'preparing', ?)",
            (managed_result_id, operation_id, canonical_target_id,
             orchestration_id, held["authority_uuid"], held["work_id"],
             held["job_id"], held["line_id"], held["source_checkpoint_id"],
             held["source_verdict_id"], held["source_proposal_id"],
             held["source_result_id"], held["source_result_digest"],
             held["source_checkpoint_digest"], held["source_base"],
             held["source_candidate"], target_revision, store._now()))
        return managed_result_of(store, managed_result_id)

    return store.transact(operation_id, MANAGED_KIND, signature, create,
                          witness=_managed_witness)


def attach_managed_phase(store, *, managed_result_id, task, result):
    """Attach ONE executed phase to a managed result, by its own act.

    THE APPLY IS BOUND TO THE PREPARATION BESIDE IT, not to a shared foreign
    key. Review 2026-09-13T19:07:44Z [P1]: each phase was checked against the
    orchestration and the target independently, so an apply naming a foreign
    preparation and a different collected digest was accepted next to this
    result's actual preparation. Sharing a parent row is not parentage.

    IT IS A SEPARATE JOURNALLED ACT under this owner's one kind, so the
    sequence the design accepts -- prepare, retain, then apply -- happens
    without rewriting the creation act, and an exact repeat of either replays.
    """
    boundaries.identity(managed_result_id, "a managed result identity")
    owned = managed_execution.adopt_managed_task(task)
    account = {"task": owned,
               "result": managed_execution.adopt_managed_result(owned, result)}
    phase = owned["phase"]
    operation_id = _attachment_id(managed_result_id, phase)
    signature = _signature(
        MANAGED_KIND, {"managed_result_id": managed_result_id, "phase": phase,
                       "task": account["task"], "result": account["result"]})

    def attach(connection):
        found = connection.execute(
            "SELECT * FROM managed_integration_results "
            "WHERE managed_result_id = ?", (managed_result_id,)).fetchone()
        if found is None:
            _refuse(f"no managed integration result "
                    f"{name_value(managed_result_id)}")
        row = {key: found[key] for key in found.keys()}
        if owned["orchestration_id"] != row["orchestration_id"] \
                or owned["canonical_target_id"] != row["canonical_target_id"]:
            _refuse(f"this {phase} task names orchestration "
                    f"{name_value(owned['orchestration_id'])} on target "
                    f"{name_value(owned['canonical_target_id'])} and the "
                    f"result is {name_value(row['orchestration_id'])} on "
                    f"{name_value(row['canonical_target_id'])}",
                    category="integrity", code="schema")
        if phase == "apply":
            beside = connection.execute(
                "SELECT * FROM managed_integration_phases "
                "WHERE managed_result_id = ? AND phase = 'prepare'",
                (managed_result_id,)).fetchone()
            if beside is None:
                _refuse(f"managed result {name_value(managed_result_id)} "
                        f"retains no preparation; an apply imports what a "
                        f"preparation produced and there is none")
            prepared = {key: beside[key] for key in beside.keys()}
            parent = owned["parent"]
            if parent["execution_attempt_id"] \
                    != prepared["execution_attempt_id"]:
                _refuse(f"this apply follows preparation "
                        f"{name_value(parent['execution_attempt_id'])} and "
                        f"the preparation retained beside it is "
                        f"{name_value(prepared['execution_attempt_id'])}",
                        category="integrity", code="schema")
            # AND THE CONTENT IT IMPORTS IS WHAT THAT PREPARATION ACTUALLY
            # COLLECTED, read from the retained account rather than from the
            # apply's own word for it.
            collected = (json.loads(prepared["collected"])
                         if prepared["collected"] is not None else None)
            if collected is None:
                _refuse(f"preparation "
                        f"{name_value(prepared['execution_attempt_id'])} "
                        f"collected no content; an apply imports a digest and "
                        f"absence is not one")
            if parent["collected_digest"] != collected["manifest_digest"]:
                _refuse(f"this apply imports "
                        f"{name_value(parent['collected_digest'])} and its "
                        f"preparation collected "
                        f"{name_value(collected['manifest_digest'])}",
                        category="integrity", code="schema")
        connection.execute(
            "INSERT INTO managed_integration_phases (managed_result_id, "
            "phase, execution_attempt_id, operation_id, assignment, task, "
            "report, collected, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, "
            "?)",
            (managed_result_id, phase, owned["execution_attempt_id"],
             operation_id, _stored(owned["assignment"]), _stored(owned),
             _stored(account["result"]["report"]),
             None if account["result"]["collected"] is None
             else _stored(account["result"]["collected"]), store._now()))
        return managed_result_of(store, managed_result_id)

    return store.transact(operation_id, MANAGED_KIND, signature, attach,
                          witness=_managed_witness)


# -- W161230 slice2 A.4: adopting what a preparation ACTUALLY collected -----
#
# THE TWO DECLARED OUTPUTS A PREPARATION PRODUCES, stated here rather than
# imported. `v12/worker/reconciliation_entry.py` is the CONTAINER's module: it
# runs where this package does not exist and this package holds no capability
# to import it, which is the same boundary `integration_worker`'s required
# credential slot is named across. A name stated on both sides can disagree;
# a name IMPORTED across that boundary would mean the manager had reached into
# the container, which is the larger wrong.
PREPARATION_REPORT_OUTPUT = "preparation-report"
PREPARED_CANDIDATE_OUTPUT = "prepared-candidate"

# AND THE WORKLOAD'S OWN SEMANTIC REPORT, which is NOT this manager's report.
# `managed_execution.REPORT_SCHEMA` is what a manager says about a phase;
# this is what the workload says about what it ran, and the adoption below is
# where one becomes the other under proof. Folding them into one schema would
# make "the worker claimed it" and "this manager measured it" the same
# sentence.
PREPARATION_REPORT_SCHEMA = "baton.v12.managed-preparation-report/1"

PREPARED_CANDIDATE_SCHEMA = "baton.v12.managed-prepared-candidate/1"
PREPARED_CANDIDATE_MEMBERS = (
    "schema", "managed_result_id", "orchestration_id", "canonical_target_id",
    "target_revision", "execution_attempt_id", "assignment", "request_digest",
    "harness_digest", "source", "states", "report", "collected", "candidate")


def _ended_preparation(jobs, orchestration_id):
    """The preparation membership, ENDED, from the capacity owner's reader.

    IMPORTED INSIDE THE FUNCTION, deliberately and for the reason the capacity
    owner defers its own import of this package: the two owners each read the
    other at one act and a module-level pair would bind them at import time
    for every caller of either.

    AND WHAT IT REFUSES IS THE WHOLE POINT. An apply imports what a
    preparation LEFT BEHIND, so a membership that is still admitted, is held
    for recovery, was cancelled or ended on any outcome but success has
    nothing for it to import -- and absence of a collected account is not an
    empty one.
    """
    from ..job_manager import integration_capacity as capacity

    held = capacity.integration_capacity_of(jobs, orchestration_id)
    if held["root"]["lifecycle"] != "open":
        _refuse(f"integration capacity {name_value(orchestration_id)} is "
                f"{name_value(held['root']['lifecycle'])}; a preparation is "
                f"adopted while its root is still held, because the apply "
                f"that imports it runs under that same reservation")
    prepared = [one for one in held["members"] if one["phase"] == "prepare"]
    if len(prepared) != 1:
        _refuse(f"integration capacity {name_value(orchestration_id)} holds "
                f"{len(prepared)} preparation memberships; one orchestration "
                f"prepares once")
    member = prepared[0]
    if member["state"] != "ended":
        _refuse(f"preparation {name_value(member['execution_attempt_id'])} is "
                f"{name_value(member['state'])}; a preparation is adopted "
                f"after it ended, and an execution that may still be running "
                f"has produced nothing final to adopt")
    if member["outcome"] != "succeeded":
        _refuse(f"preparation {name_value(member['execution_attempt_id'])} "
                f"ended {name_value(member['outcome'])}; a preparation that "
                f"did not succeed contributes no importable candidate")
    if member["collected_report"] is None:
        _refuse(f"preparation {name_value(member['execution_attempt_id'])} "
                f"ended successfully and its membership retains no collected "
                f"account; absence is not content")
    # AND THE APPLY IS STILL PLANNED. Slice2 finishes with the preparation
    # ended, the apply NOT yet run and the one root still held; an apply that
    # had already started would make this adoption an account of something
    # already consumed.
    applying = [one for one in held["members"] if one["phase"] == "apply"]
    for one in applying:
        if one["state"] != "planned":
            _refuse(f"the apply for {name_value(orchestration_id)} is "
                    f"{name_value(one['state'])}; a preparation is adopted "
                    f"while its apply is still planned")
    return member, held["root"]


def _retained_outputs(control, collected, attempt_id):
    """The frozen result, PROVED against the manifest actually retained.

    TWO READERS AND BOTH ARE ASKED. `frozen_output_of` is the manager's
    INDEXED half -- one row per output with its artifact -- and the retained
    manifest at `manifest_digest` is the sealed document that row was written
    from. Reading only the index would trust a summary; reading only the
    manifest would lose the manager's own account of which artifact answers
    which output. A build where the two disagree is one whose durable record
    cannot be read as either, and that is worth refusing rather than picking
    a side of.
    """
    from ..worker_manager.manifests import load_manifest
    from ..worker_manager.output import frozen_output_of

    frozen = frozen_output_of(control, attempt_id)
    if frozen is None:
        _refuse(f"this manager holds no frozen output for "
                f"{name_value(attempt_id)}; the membership's collected "
                f"account names one and the owner that would hold it does not")
    for name in ("result_id", "manifest_digest", "disposition"):
        if frozen[name] != collected[name]:
            _refuse(f"the frozen output for {name_value(attempt_id)} names "
                    f"{name} {name_value(frozen[name])} and the collected "
                    f"account names {name_value(collected[name])}")
    retained = load_manifest(control, collected["manifest_digest"],
                             "resultManifest")
    if retained is None:
        _refuse(f"the result manifest {name_value(collected['manifest_digest'])} "
                f"is not retained by this manager; a preparation is adopted "
                f"from the document it actually sealed, not from a digest")
    for name in ("result_id", "disposition"):
        if retained[name] != collected[name]:
            _refuse(f"the retained result manifest names {name} "
                    f"{name_value(retained[name])} and the collected account "
                    f"names {name_value(collected[name])}")
    indexed = {one["output_name"]: one for one in frozen["artifacts"]}
    custody = {one["artifact_id"]: one for one in collected["artifacts"]}
    return retained, indexed, custody


def _adopted_artifact(retained, indexed, custody, name, attempt_id):
    """ONE declared output's measured identity, agreed by all three owners.

    The retained manifest says which artifact answers this output; the indexed
    row says the same from the manager's own table; and the intake receipt
    says what was taken into CUSTODY. A later phase imports by digest and
    length, so all three must name one artifact with one measurement -- an
    output whose custody says something else is not importable content however
    complete the manifest looks.
    """
    declared = [one for one in retained["outputs"] if one["name"] == name]
    if len(declared) != 1:
        _refuse(f"preparation {name_value(attempt_id)} sealed "
                f"{len(declared)} outputs named {name_value(name)}; a "
                f"preparation declares each of its outputs once")
    artifact = declared[0]["artifact"]
    if artifact is None:
        _refuse(f"preparation {name_value(attempt_id)} answered output "
                f"{name_value(name)} with no artifact at all; a declared "
                f"output an apply imports is content, and absence is not")
    if name not in indexed:
        _refuse(f"this manager's frozen output for {name_value(attempt_id)} "
                f"indexes no {name_value(name)}, and its retained manifest "
                f"seals one")
    row = indexed[name]
    taken = custody.get(artifact["artifact_id"])
    if taken is None:
        _refuse(f"artifact {name_value(artifact['artifact_id'])} answers "
                f"output {name_value(name)} and was never taken into custody; "
                f"a freeze is not a collection")
    for holder, held in (("the indexed output artifact", row),
                         ("the intake receipt", taken)):
        for member in ("artifact_id", "content_digest", "bytes"):
            if held[member] != artifact[member]:
                _refuse(f"{holder} for output {name_value(name)} names "
                        f"{member} {name_value(held[member])} and the "
                        f"retained manifest names "
                        f"{name_value(artifact[member])}")
    return {"artifact_id": artifact["artifact_id"],
            "content_digest": artifact["content_digest"],
            "bytes": artifact["bytes"]}


def _measured_body(body, artifact, what):
    """The bytes, held to the identity this manager MEASURED.

    THIS IS WHY A JSON REPORT IS NOT TRUSTED CUSTODY. The document below is
    read out of a payload somebody handed this function; what makes it the
    preparation's report is that its bytes digest to the artifact the manager
    froze and took into custody, at the length it recorded. A document that
    cannot be weighed against custody is a caller's assertion, and the slice
    says in those words that no direct JSON report becomes trusted custody.
    """
    if type(body) is not bytes:
        _refuse(f"{what} is adopted from exact bytes; this is "
                f"{name_value(body)}", category="integrity", code="schema")
    if len(body) != artifact["bytes"]:
        _refuse(f"{what} is {len(body)} bytes and this manager measured "
                f"{artifact['bytes']}")
    measured = digest_of_bytes(body)
    if measured != artifact["content_digest"]:
        _refuse(f"{what} digests to {name_value(measured)} and this manager "
                f"took {name_value(artifact['content_digest'])} into custody")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as broken:
        _refuse(f"{what} is not one readable document: {sample_of(str(broken))}",
                category="integrity", code="schema")


def _preparation_account(answered, owned_request, task):
    """The workload's own report, held to what it was ASKED to do.

    THE WORKLOAD REPORTS THE HARNESS TWICE ON PURPOSE -- the digest the
    request asked for and the digest of the bytes it actually pinned and ran
    -- and it deliberately does not compare them: "echoing only the former
    would let this report assert an identity it never observed". Comparing
    them is THIS owner's act, and it is the one that matters: a preparation
    that measured a different harness measured a different test, and the
    accepted evidence authorized the one in the request.
    """
    held = boundaries.document(answered, "the preparation's own report")
    if held.get("schema") != PREPARATION_REPORT_SCHEMA:
        _refuse(f"a preparation report is "
                f"{name_value(PREPARATION_REPORT_SCHEMA)}; this is "
                f"{name_value(held.get('schema'))}", category="integrity",
                code="schema")
    if held.get("orchestration_id") != owned_request["orchestration_id"]:
        _refuse(f"this report accounts orchestration "
                f"{name_value(held.get('orchestration_id'))} and the request "
                f"is {name_value(owned_request['orchestration_id'])}")
    if held.get("source") != owned_request["source"]:
        _refuse(f"this report prepared {name_value(held.get('source'))} and "
                f"the request names {name_value(owned_request['source'])}; a "
                f"preparation is about the snapshot it was asked for")
    if held.get("harness_digest") != owned_request["harness_digest"]:
        _refuse(f"this report echoes harness "
                f"{name_value(held.get('harness_digest'))} and the request "
                f"authorized {name_value(owned_request['harness_digest'])}")
    measured = held.get("harness_measured_digest")
    if held.get("kind") != "not-collected":
        if measured != owned_request["harness_digest"]:
            _refuse(f"this preparation RAN harness {name_value(measured)} and "
                    f"the accepted evidence authorized "
                    f"{name_value(owned_request['harness_digest'])}; a "
                    f"different harness measures a different test")
    elif measured is not None:
        _refuse(f"this report collected nothing and names a harness it "
                f"measured, {name_value(measured)}")
    # AND THE COMMANDS ARE THE MANAGER'S THREE ANSWERS, composed through the
    # owner that decides what a report may carry rather than copied across.
    completed = [{"name": one.get("name"), "status": one.get("status")}
                 for one in held.get("completed", [])]
    return managed_execution.collected_report(
        task, kind=held.get("kind"), completed=completed,
        not_run=held.get("not_run", []), status=held.get("status"),
        tag=held.get("tag")), held


def _requested_task(task, owned_request, member, attempt_id):
    """The task this phase ran, held to the request and to the MEMBERSHIP.

    A task is composed before an execution and travels with it, so it arrives
    here as untrusted input like everything else. What makes it this
    preparation's task is that every operand it names is one an owner already
    committed: the attempt and the assignment the capacity owner admitted, and
    the target, harness, limits, input and command sequence the request fixed.
    """
    owned = managed_execution.adopt_managed_task(task)
    if owned["phase"] != "prepare":
        _refuse(f"this is a {name_value(owned['phase'])} task; a preparation "
                f"is adopted from the phase that prepared")
    if owned["parent"] is not None:
        _refuse("a preparation follows nothing; this task names a parent "
                "execution, which is an apply's operand")
    if owned["execution_attempt_id"] != attempt_id:
        _refuse(f"this task ran {name_value(owned['execution_attempt_id'])} "
                f"and the ended preparation is {name_value(attempt_id)}")
    admitted = json.loads(member["assignment"])
    if owned["assignment"] != admitted:
        _refuse(f"this task ran under {name_value(owned['assignment'])} and "
                f"the membership was admitted for {name_value(admitted)}")
    # AND THE TASK'S OWN IDENTITY, against the membership that was ADMITTED
    # for it. Review [P2]: this compared phase, parent, attempt, assignment and
    # the request's fields and omitted `task_digest` -- so a foreign digest was
    # journalled into the preparation phase beside a correct account of
    # everything else. The capacity owner already retains it, which is why
    # this is a comparison rather than a new fact: `register_integration_
    # capacity` wrote it from the registered plan and `admit_integration_
    # execution` is what made that member live.
    #
    # `input_digest` IS DELIBERATELY NOT COMPARED HERE. The member's is the
    # original Job input the plan registered and the task's is the runtime
    # manifest the attempt actually ran under; they are two meanings and the
    # request above is what owns the task's. Collapsing them would repair a
    # composition mismatch by weakening what one of them means.
    if owned["task_digest"] != member["task_digest"]:
        _refuse(f"this task is {name_value(owned['task_digest'])} and the "
                f"membership admitted for it registered "
                f"{name_value(member['task_digest'])}")
    for member_name in ("orchestration_id", "canonical_target_id",
                        "harness_digest", "input_digest", "execution_limits",
                        "commands"):
        if owned[member_name] != owned_request[member_name]:
            _refuse(f"this task names {member_name} "
                    f"{name_value(owned[member_name])} and the request fixes "
                    f"{name_value(owned_request[member_name])}")
    return owned


def _owned_submission(store, intent, owned_request):
    """The submission identities, RESOLVED FROM THEIR OWNERS.

    REVIEW [P1], AND THE DEFECT IS WORTH STATING EXACTLY. This used to be a
    caller operand handed straight to `record_managed_result`. That owner
    validates a submission's SHAPE and journals it; it holds no preparation
    request to compare its source identities against, and neither this
    composition nor `attach_managed_phase` established the relation. So
    changing one member -- `source_candidate` -- produced a durable account
    that named a candidate this preparation never prepared, beside a report
    and a request that still described the original. That is false attribution
    in the very account a later judgment reads, not a malformed caller turned
    away at the door.

    THE CORRECTION IS STRUCTURAL RATHER THAN A CHECK. There is no submission
    operand any more, so there is nothing left to substitute. Every member
    comes from an owner:

      * the COMMITTED REQUEST -- itself proved against the `request_digest`
        the intent fixed before the child Work existed -- owns `job_id`,
        `line_id`, `source_proposal_id` and the two Git objects. The objects
        must come from there: the queue entry carries CONTENT digests, which
        name the same candidate in a different language and cannot stand in
        for it, exactly as `admission.source_submission` says of the same two
        members;
      * the COORDINATOR'S OWN ENTRY owns the checkpoint, verdict and result
        identities and their digests, and the Authority and Work the accepted
        candidate belongs to. It is this store's own already-proved account.

    AND THE SOURCE WORK IS NOT THE CHILD EXECUTION WORK. They are different
    identities for different things -- the Work the accepted candidate belongs
    to, and the separate Work this preparation ran under -- so the one relation
    asserted between them is that they DIFFER. Nothing here invents an
    equality to fill a fact no owner answered.
    """
    from .queue import entries_of

    target = owned_request["canonical_target_id"]
    proposal = owned_request["source_proposal_id"]
    entries = [one for one in entries_of(store, target)
               if one["proposal_id"] == proposal]
    if len(entries) != 1:
        _refuse(f"this coordinator holds {len(entries)} entries for proposal "
                f"{name_value(proposal)} on target {name_value(target)}; a "
                f"preparation is attributed to the accepted candidate its own "
                f"coordinator retains, and neither absence nor a pair is one")
    entry = entries[0]
    if entry["line_id"] != owned_request["line_id"]:
        _refuse(f"the accepted entry for {name_value(proposal)} is on line "
                f"{name_value(entry['line_id'])} and the committed request "
                f"names {name_value(owned_request['line_id'])}")
    if entry["authority_uuid"] != intent["authority_uuid"]:
        _refuse(f"the accepted entry belongs to authority "
                f"{name_value(entry['authority_uuid'])} and this "
                f"orchestration decided {name_value(intent['authority_uuid'])}")
    if entry["work_id"] == intent["execution_work_id"]:
        _refuse(f"the accepted candidate's Work and this preparation's own "
                f"child Work are both {name_value(entry['work_id'])}; a "
                f"preparation runs on a Work of its own and the submission "
                f"names the Work the candidate came from")
    return {"authority_uuid": entry["authority_uuid"],
            "work_id": entry["work_id"],
            "job_id": owned_request["job_id"],
            "line_id": owned_request["line_id"],
            "source_checkpoint_id": entry["checkpoint_id"],
            "source_verdict_id": entry["verdict_id"],
            "source_proposal_id": proposal,
            "source_result_id": entry["result_id"],
            "source_result_digest": entry["result_digest"],
            "source_checkpoint_digest": entry["checkpoint_digest"],
            "source_base": owned_request["source"]["base"],
            "source_candidate": owned_request["source"]["candidate"]}


def adopt_prepared_candidate(store, jobs, control, *, orchestration_id,
                             request, task, report_body, authority=None):
    """W161230 A.4: retain what a preparation actually collected, as a
    PORTABLE candidate a later phase can judge.

    EVERY FACT COMES FROM THE OWNER THAT HOLDS IT, and nothing is taken on a
    caller's word:

      * the CAPACITY owner says the preparation ended, that it succeeded, that
        its apply is still planned and that its root is still held;
      * the WORKER MANAGER says what was frozen, what the sealed manifest
        declared and what was taken into ACCEPTED custody, with each declared
        output's measured digest and length;
      * the REQUEST -- proved against the intent this orchestration committed
        before its child Work existed -- says which snapshot, which harness,
        which limits and which commands were authorized, and the SUBMISSION
        this result is attributed to is resolved from that request and the
        coordinator's own accepted entry rather than supplied (see
        `_owned_submission`);
      * and the REPORT is adopted from bytes that weigh the same and digest
        the same as the artifact this manager took into custody. A JSON
        document that cannot be weighed against custody is an assertion.

    IT SETTLES NOTHING ABOUT THE TARGET. What comes back is an account plus
    the retained identity of the prepared candidate; no byte is applied, no
    entry is settled, no receipt is dispatched and no verdict is composed.
    Those are slice3's and they are a different authority entirely.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    from ..job_manager import integration_capacity as capacity

    intent = capacity.preparation_intent_of(jobs, orchestration_id)
    if intent is None:
        _refuse(f"orchestration {name_value(orchestration_id)} committed no "
                f"preparation intent; there is no decision here to adopt the "
                f"result of")
    owned_request = managed_execution.adopt_preparation_request(request)
    asked = managed_execution.request_digest(owned_request)
    if asked != intent["request_digest"]:
        _refuse(f"this request is {name_value(asked)} and the committed "
                f"intent decided {name_value(intent['request_digest'])}; a "
                f"preparation is adopted against the request it ran for")
    # RESOLVED BEFORE ANY WRITE, and before the expensive owner reads below,
    # so a submission this coordinator cannot attribute refuses without having
    # touched the result table or consumed its one-per-target-snapshot slot.
    if authority is None:
        submission = _owned_submission(store, intent, owned_request)
    else:
        # A preparation precedes import admission. Resolve historical source
        # eligibility directly from its owners without enqueuing an import.
        from .admission import source_submission

        submission = source_submission(control, jobs, authority,
                                       line_id=owned_request["line_id"],
                                       proposal_id=owned_request["source_proposal_id"])
        expected = {"authority_uuid": intent["authority_uuid"],
                    "job_id": owned_request["job_id"],
                    "line_id": owned_request["line_id"],
                    "source_proposal_id": owned_request["source_proposal_id"],
                    "source_base": owned_request["source"]["base"],
                    "source_candidate": owned_request["source"]["candidate"]}
        if any(submission[name] != value for name, value in expected.items()) or submission["work_id"] == intent["execution_work_id"]:
            _refuse("the preparation request and accepted source submission disagree")
    member, root = _ended_preparation(jobs, orchestration_id)
    attempt_id = member["execution_attempt_id"]
    collected = json.loads(member["collected_report"])
    owned_task = _requested_task(task, owned_request, member, attempt_id)
    retained, indexed, custody = _retained_outputs(control, collected,
                                                   attempt_id)
    reported = _adopted_artifact(retained, indexed, custody,
                                 PREPARATION_REPORT_OUTPUT, attempt_id)
    candidate = _adopted_artifact(retained, indexed, custody,
                                  PREPARED_CANDIDATE_OUTPUT, attempt_id)
    output = next(one for one in retained["outputs"] if one["name"] == PREPARATION_REPORT_OUTPUT)
    entries = [one for one in output["content_manifest"]["entries"] if one["path"] == "report.json"]
    if len(entries) != 1:
        _refuse("the retained preparation output needs exactly one report.json")
    # The artifact identifies a directory; the report bytes identify one file
    # in its sealed content manifest. They are not interchangeable digests.
    answered = _measured_body(report_body, entries[0], "the preparation report")
    account, raw = _preparation_account(answered, owned_request, owned_task)
    result = managed_execution.managed_result(
        owned_task, account,
        collected={"result_id": collected["result_id"],
                   "manifest_digest": collected["manifest_digest"],
                   "disposition": collected["disposition"]})
    target_revision = owned_request["source"]["target_revision"]
    record_managed_result(store, submission,
                          orchestration_id=orchestration_id,
                          canonical_target_id=owned_request[
                              "canonical_target_id"],
                          target_revision=target_revision)
    held = attach_managed_phase(store, managed_result_id=orchestration_id,
                                task=owned_task, result=result)
    return {"schema": PREPARED_CANDIDATE_SCHEMA,
            "managed_result_id": held["managed_result_id"],
            "orchestration_id": orchestration_id,
            "canonical_target_id": owned_request["canonical_target_id"],
            "target_revision": target_revision,
            "execution_attempt_id": attempt_id,
            "assignment": owned_task["assignment"],
            "request_digest": asked,
            "harness_digest": owned_request["harness_digest"],
            "source": dict(owned_request["source"]),
            # WHAT THE WORKER ACTUALLY DERIVED, carried whole rather than
            # summarized: a later judgment asks which revision and which
            # content each state had, and a digest alone answers neither.
            "states": raw.get("states"),
            "report": account,
            "collected": {"result_id": collected["result_id"],
                          "manifest_digest": collected["manifest_digest"],
                          "disposition": collected["disposition"],
                          "custody": collected["custody"],
                          "report": reported},
            "candidate": candidate}


def managed_result_of(store, managed_result_id):
    """One portable managed result, PROVED against the journal that made it.

    REVIEW 2026-09-13T19:07:44Z [P1]: this adopted the current documents and
    returned the current state, and nothing compared either with what was
    committed. So a persisted harness digest could be replaced with another
    valid one, every phase row could be deleted, and a `preparing` row could
    be moved to `held` with a reason -- and the reader answered all three
    normally, because each was individually well formed. An earlier valid
    write is not a current typed read.

    WHAT IS PROVED HERE, on the rows as they stand NOW:

      the CREATION act, rebuilt from the result row's own identities and the
        set of phases attached to it;
      EACH PHASE's own attachment act, rebuilt from that phase's stored task
        and result;
      and the STATE, which must rest on a committed act -- creation
        materializes `preparing` and nothing else, so any other state is a
        transition nobody journalled.

    A row that survives all three is one the journal actually accounts for.
    """
    boundaries.identity(managed_result_id, "a managed result identity")
    if not store.managed_results_available():
        _refuse(f"this integration coordinator is schema "
                f"{store.schema_version} and holds no managed results; a "
                f"store that predates them has none rather than an empty one",
                category="refused", code="precondition")
    # ONE SNAPSHOT for the row, its phases, the cross-representation proof and
    # the journal: reads at four instants would be a composite that never
    # existed.
    with store.snapshot():
        found = store._connection.execute(
            "SELECT * FROM managed_integration_results "
            "WHERE managed_result_id = ?", (managed_result_id,)).fetchone()
        if found is None:
            _refuse(f"no managed integration result "
                    f"{name_value(managed_result_id)}")
        row = {key: found[key] for key in found.keys()}
        # THE IDENTITY IS DERIVED, NOT FOLLOWED. Review 2026-09-13T23:28:58Z
        # [P2]: the reader looked the act up at whatever identity the row
        # pointed to, so renaming the operation row and the pointer together
        # left the original signature valid and the read passed. A row does
        # not get to say which act made it; the writer's own derivation does.
        if row["operation_id"] != _creation_id(managed_result_id):
            raise ContractRefusal(
                "integrity", "schema",
                f"managed result {name_value(managed_result_id)} points at "
                f"act {name_value(row['operation_id'])} and its own creation "
                f"identity is {name_value(_creation_id(managed_result_id))}")
        _one_representation(store._connection, row["canonical_target_id"],
                            row["source_proposal_id"], row["target_revision"],
                            expected="managed_integration_results")
        stored = [{key: one[key] for key in one.keys()}
                  for one in store._connection.execute(
                      "SELECT * FROM managed_integration_phases "
                      "WHERE managed_result_id = ? ORDER BY phase",
                      (managed_result_id,))]
        accounts = {}
        for one in stored:
            task = managed_execution.adopt_managed_task(
                json.loads(one["task"]))
            accounts[one["phase"]] = {
                "task": task,
                "result": managed_execution.adopt_managed_result(task, {
                    "schema": managed_execution.RESULT_SCHEMA,
                    "orchestration_id": row["orchestration_id"],
                    "phase": one["phase"],
                    "execution_attempt_id": one["execution_attempt_id"],
                    "assignment": json.loads(one["assignment"]),
                    "canonical_target_id": row["canonical_target_id"],
                    "report": json.loads(one["report"]),
                    "collected": None if one["collected"] is None
                    else json.loads(one["collected"])})}
        # THE CREATION ACT, over the result's own identities.
        _committed_act(store, row["operation_id"],
                       _signature(MANAGED_KIND, _managed_operands(row)))
        # AND EACH ATTACHMENT, at ITS OWN derived identity too.
        for one in stored:
            if one["operation_id"] != _attachment_id(managed_result_id,
                                                     one["phase"]):
                raise ContractRefusal(
                    "integrity", "schema",
                    f"the {one['phase']} phase of "
                    f"{name_value(managed_result_id)} points at act "
                    f"{name_value(one['operation_id'])} and its own "
                    f"attachment identity is "
                    f"{name_value(_attachment_id(managed_result_id, one['phase']))}")
            _committed_act(store, one["operation_id"],
                           _signature(MANAGED_KIND,
                                      _attachment_operands(
                                          row, one["phase"],
                                          accounts[one["phase"]])))
        # AND THE OTHER DIRECTION, which is what catches a DELETION. Every
        # attachment this store committed for this result must have a phase
        # standing beside it: an act with nothing materialized is a row
        # somebody removed, and the whole point of asking the journal is that
        # removal stops being invisible. Review 2026-09-13T19:07:44Z: deleting
        # every phase row left both the read and the replay answering with an
        # empty phase map.
        attached = {one["operation_id"] for one in stored}
        if store._pending is not None:
            attached.add(store._pending["operation_id"])
        # THE ACTS THIS RESULT OWNS ARE THE ONES WHOSE OPERANDS SAY SO.
        # Review 2026-09-13T23:19:08Z [P2]: this asked SQL for identities
        # matching `<kind>:<id>/%`, and LIKE reads `_` as a wildcard and
        # compares ASCII case-insensitively -- so a result named `root_`
        # claimed `rootA`'s attachments and `root` claimed `ROOT`'s, and two
        # perfectly independent results refused each other. A pattern over a
        # composed identity is a GRAMMAR, and this owner already has the
        # authoritative answer: each act is signed over the result it belongs
        # to, so that is what is asked.
        committed = {found["operation_id"] for found in
                     store._connection.execute(
                         "SELECT operation_id, signature FROM operations "
                         "WHERE kind = ? AND state = 'committed'",
                         (MANAGED_KIND,))
                     if _signed_attachment(found) == managed_result_id}
        missing = sorted(committed - attached)
        if missing:
            raise ContractRefusal(
                "integrity", "schema",
                f"this store committed {', '.join(missing)} and retains no "
                f"phase for {'it' if len(missing) == 1 else 'them'}; an act "
                f"with nothing materialized is a row somebody removed")
        if row["state"] not in _MANAGED_STATE_ACT:
            raise ContractRefusal(
                "integrity", "schema",
                f"managed result {name_value(managed_result_id)} is "
                f"{name_value(row['state'])}, which this build holds no "
                f"committed act for; a state nobody journalled a transition "
                f"to is not one this result reached")
        held = _MANAGED_STATE_ACT[row["state"]]
        if held is not None:                              # pragma: no cover
            _committed_act(store, held + ":" + managed_result_id, None)
        # AND THE STATE'S OWN REQUIRED FIELDS, carried rather than dropped. A
        # reader returning selected members could not report a held reason, a
        # blocked record's retained observations or an authorization at all.
        for name, required in (("reason", row["state"] in ("held", "blocked")),
                               ("prepared", row["state"] not in ("preparing",
                                                                 "held")),
                               ("content_digest",
                                row["state"] not in ("preparing", "held"))):
            if required and row[name] is None:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"managed result {name_value(managed_result_id)} is "
                    f"{name_value(row['state'])} and carries no "
                    f"{name_value(name)}")
    answer = {"managed_result_id": row["managed_result_id"],
              "orchestration_id": row["orchestration_id"],
              "canonical_target_id": row["canonical_target_id"],
              "target_revision": row["target_revision"]}
    # THE WHOLE SUBMISSION IT IS A RESULT FOR, not a selection of it. A
    # consumer asking which queued work these bytes answer needs every
    # identity the queue admitted the entry under, and a reader handing back
    # three of them leaves the other six to be guessed at.
    answer.update({name: row[name] for name in _MANAGED_SOURCE})
    return {**answer,
            "state": row["state"], "reason": row["reason"],
            "prepared": None if row["prepared"] is None
            else json.loads(row["prepared"]),
            "content_digest": row["content_digest"],
            "evidence": None if row["evidence"] is None
            else json.loads(row["evidence"]),
            "causal_observations": None if row["causal_observations"] is None
            else json.loads(row["causal_observations"]),
            "observed_by": row["observed_by"],
            "policy_generation": row["policy_generation"],
            "derived_proposal_id": row["derived_proposal_id"],
            "derived_result_id": row["derived_result_id"],
            "derived_result_digest": row["derived_result_digest"],
            "entry_id": row["entry_id"],
            "recorded_at": row["recorded_at"], "phases": accounts}


def _managed_witness(store, row):
    """This act's semantic proof, which is the OWNER's and not a second one.

    `replay` hands a witness's return value back as the replayed answer, so
    this reads the result the act is about through the owner above -- whose
    every proof runs on the way out. A witness that re-derived those rules
    here would be the second spelling this campaign keeps removing.
    """
    if row["kind"] != MANAGED_KIND:
        _refuse(f"operation {name_value(row['operation_id'])} is a "
                f"{name_value(row['kind'])} and this owner witnesses "
                f"{name_value(MANAGED_KIND)}",
                code="operation-collision")
    # WHICH RESULT THIS ACT IS ABOUT, FROM ITS SIGNED OPERANDS. Review
    # 2026-09-13T23:19:08Z [P2]: this split the identity on the first slash,
    # which silently narrows the grammar of an orchestration id -- a result
    # legitimately named `root/child` replayed as `root`, so its own exact
    # retry answered about a different result or refused. The act says what it
    # is about; parsing its name is guessing at what it says.
    named = _signed_result(row)
    if named is None:
        _refuse(f"the act {name_value(row['operation_id'])} names no managed "
                f"result in its own operands",
                category="integrity", code="schema")
    return managed_result_of(store, named)


# W161230 slice1 condition 5: WHAT ONE PUBLICATION IS, as operands. The
# identity is derived from all of them, so a request differing anywhere is a
# different publication rather than a retry of this one -- which is what
# review 2026-09-14T00:04:25Z found missing when a completed retry accepted an
# unrelated lease and a fence 99 higher.
PUBLICATION_OPERANDS = ("managed_result_id", "phase", "canonical_target_id",
                        "entry_id", "lease_id", "fence",
                        "admitted_old_revision", "imported_revision",
                        "content_digest", "derived_proposal_id", "settlement")

_PUBLICATION_STATES = ("intended", "swapped", "settled")


def _publication_identity(operands):
    """This publication's own name, derived from everything it is about."""
    return "publication:" + digest(canonical_text(
        {name: operands[name] for name in PUBLICATION_OPERANDS}))


def _effect_id(publication_id, state):
    return MANAGED_KIND + ":" + publication_id + "/" + state


def publication_of(store, managed_result_id, phase):
    """This phase's durable publication account, PROVED against the journal.

    ABSENCE IS AN ORDINARY ANSWER and it is the one that matters most: a
    placement that finds no record has not begun, whatever the target happens
    to say.

    REVIEW 2026-09-14T00:17:42Z: the row derived its own identity from its
    operands and nothing else was checked -- and the identity deliberately
    excludes `state`, because the state changes while the publication is the
    same one. So editing `intended` to `settled` was accepted by this reader
    and by the placement's replay, and DELETING the creating intent act left
    the row reading normally. A row is not an account of an act until the act
    is there.

    WHAT IS PROVED, on the row as it stands NOW: the intent act, committed
    under this publication's own identity and signed over exactly these
    operands; each effect act the state claims; and that no effect act exists
    which the state does not claim -- a row saying `intended` beside a
    committed swap is a row whose state is behind its own journal.
    """
    boundaries.identity(managed_result_id, "a managed result identity")
    # ONE SNAPSHOT FOR THE WHOLE PROOF. Review 2026-09-14T00:26:30Z [P2]: the
    # row and its journal records were read in separate autocommit statements,
    # so an ORDINARY concurrent writer committing `swapped` between them
    # produced a composite that never existed -- and this reader called that
    # composite corruption. A proof assembled from independently committed
    # reads is not a proof, which is the correction the queue's own
    # relationship pass already carries.
    with store.snapshot():
        return _publication_row(store, managed_result_id, phase)


def _publication_row(store, managed_result_id, phase):
    found = store._connection.execute(
        "SELECT * FROM managed_publications WHERE managed_result_id = ? "
        "AND phase = ?", (managed_result_id, phase)).fetchone()
    if found is None:
        return None
    row = {key: found[key] for key in found.keys()}
    row["settlement"] = json.loads(row["settlement"])
    if row["state"] not in _PUBLICATION_STATES:
        _refuse(f"publication {name_value(row['publication_id'])} is "
                f"{name_value(row['state'])}, which this build does not own",
                category="integrity", code="schema")
    publication_id = row["publication_id"]
    if publication_id != _publication_identity(row):
        _refuse(f"publication {name_value(publication_id)} does not "
                f"derive its own identity from the operands it carries",
                category="integrity", code="schema")
    if row["operation_id"] != MANAGED_KIND + ":" + publication_id:
        _refuse(f"publication {name_value(publication_id)} points at act "
                f"{name_value(row['operation_id'])} and its own intent "
                f"identity is "
                f"{name_value(MANAGED_KIND + ':' + publication_id)}",
                category="integrity", code="schema")
    # THE INTENT ACT ITSELF.
    _committed_act(store, row["operation_id"],
                   _signature(MANAGED_KIND,
                              dict({name: row[name]
                                    for name in PUBLICATION_OPERANDS},
                                   publication_id=publication_id)))
    # AND EVERY EFFECT, BOTH WAYS. The state names which acts must be there,
    # and the journal names which acts are -- and they must be the same set.
    reached = _PUBLICATION_STATES[:_PUBLICATION_STATES.index(row["state"]) + 1]
    for state in ("swapped", "settled"):
        identity = _effect_id(publication_id, state)
        signature = _signature(MANAGED_KIND,
                               {"publication_id": publication_id,
                                "state": state})
        committed = store._connection.execute(
            "SELECT 1 FROM operations WHERE operation_id = ? "
            "AND state = 'committed'", (identity,)).fetchone() is not None
        if state in reached:
            _committed_act(store, identity, signature)
        elif committed:
            _refuse(f"publication {name_value(publication_id)} records "
                    f"{name_value(row['state'])} and this store committed "
                    f"{name_value(identity)}; a row whose state is behind its "
                    f"own journal is not an account of what happened",
                    category="integrity", code="schema")
    return row


def record_publication_intent(store, operands):
    """Commit what this publication is ABOUT to do, before it does it.

    THE INTENT CARRIES THE REVISION IT WILL IMPORT. That is the whole of the
    restart answer: afterwards, a target standing at that revision is this
    publication's own committed swap and a target standing anywhere else but
    the admitted old revision is somebody else's.
    """
    held = boundaries.document(operands, "a publication's operands",
                               required=PUBLICATION_OPERANDS)
    publication_id = _publication_identity(held)
    operation_id = MANAGED_KIND + ":" + publication_id
    signature = _signature(MANAGED_KIND, dict(held,
                                              publication_id=publication_id))

    def intend(connection):
        connection.execute(
            "INSERT INTO managed_publications (publication_id, operation_id, "
            "managed_result_id, phase, canonical_target_id, entry_id, "
            "lease_id, fence, admitted_old_revision, imported_revision, "
            "content_digest, derived_proposal_id, settlement, state, "
            "recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "'intended', ?)",
            (publication_id, operation_id, held["managed_result_id"],
             held["phase"], held["canonical_target_id"], held["entry_id"],
             held["lease_id"], held["fence"], held["admitted_old_revision"],
             held["imported_revision"], held["content_digest"],
             held["derived_proposal_id"], _stored(held["settlement"]),
             store._now()))
        return publication_of(store, held["managed_result_id"], held["phase"])

    return store.transact(operation_id, MANAGED_KIND, signature, intend,
                          witness=_publication_witness)


def record_publication_effect(store, publication_id, state):
    """Record that the swap, or the settlement, actually happened."""
    boundaries.identity(publication_id, "a publication identity")
    if state not in ("swapped", "settled"):
        _refuse(f"a publication effect is swapped or settled; this is "
                f"{name_value(state)}", category="integrity", code="schema")
    operation_id = MANAGED_KIND + ":" + publication_id + "/" + state
    signature = _signature(MANAGED_KIND,
                           {"publication_id": publication_id, "state": state})

    def record(connection):
        found = connection.execute(
            "SELECT * FROM managed_publications WHERE publication_id = ?",
            (publication_id,)).fetchone()
        if found is None:
            _refuse(f"no publication {name_value(publication_id)}")
        row = {key: found[key] for key in found.keys()}
        # THE ORDER IS THE LIFECYCLE'S. A settlement recorded before a swap
        # would be an account of a target mutation nobody made.
        if state == "swapped" and row["state"] != "intended":
            _refuse(f"publication {name_value(publication_id)} is "
                    f"{name_value(row['state'])}; a swap follows an intent")
        if state == "settled" and row["state"] != "swapped":
            _refuse(f"publication {name_value(publication_id)} is "
                    f"{name_value(row['state'])}; a settlement follows a swap")
        connection.execute(
            "UPDATE managed_publications SET state = ? WHERE "
            "publication_id = ?", (state, publication_id))
        return publication_of(store, row["managed_result_id"], row["phase"])

    return store.transact(operation_id, MANAGED_KIND, signature, record,
                          witness=_publication_witness)


def _publication_witness(store, row):
    """This act's proof: the publication it is about reads back as one."""
    if row["kind"] != MANAGED_KIND:
        _refuse(f"operation {name_value(row['operation_id'])} is a "
                f"{name_value(row['kind'])} and this owner witnesses "
                f"{name_value(MANAGED_KIND)}",
                code="operation-collision")
    try:
        operands = json.loads(row["signature"])["operands"]
    except (TypeError, ValueError, KeyError):
        operands = None
    if type(operands) is not dict or "publication_id" not in operands:
        _refuse(f"the act {name_value(row['operation_id'])} names no "
                f"publication in its own operands",
                category="integrity", code="schema")
    found = store._connection.execute(
        "SELECT managed_result_id, phase FROM managed_publications "
        "WHERE publication_id = ?", (operands["publication_id"],)).fetchone()
    if found is None:
        if store._pending is not None \
                and store._pending["operation_id"] == row["operation_id"]:
            return None
        _refuse(f"the act {name_value(row['operation_id'])} recorded no "
                f"publication", category="integrity", code="schema")
    return publication_of(store, found[0], found[1])


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
    row is not proof of what it materialized. For these kinds the proof is the
    record itself: an act named `<kind>:<result_id>` must have materialized a
    result whose own operands derive that identity, which is exactly what
    `result_of` establishes. W133120 adds the terminal act to the set, because
    the act that has an owner is the act that can be witnessed.
    """
    kind = row["kind"]
    if kind not in (INTENT_KIND, OUTCOME_KIND, OBSERVATION_KIND,
                    EVIDENCE_KIND, PUBLISH_KIND, IMPORT_KIND):
        _refuse(f"this owner does not witness {name_value(kind)} acts",
                category="integrity", code="schema")
    _prefix, _, result_id = row["operation_id"].partition(":")
    return result_of(store, result_id)


def _profile_capabilities(profile):
    for name in ("prepare", "validate", "content", "revision", "storage"):
        boundaries.capability(getattr(profile, name, None),
                              f"a reconciliation profile's {name} capability")
    return profile
