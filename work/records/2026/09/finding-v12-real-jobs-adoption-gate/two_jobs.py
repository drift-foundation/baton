"""The two-Job arrangement this adoption gate proposes, composed and held.

ASSESSMENT-249338.md G1: "prepare a fresh, create-only two-Job package using
the proposed accepted artifacts ... Specify one explicit arrangement (shared
manager with per-Job ports/allocations, or separately isolated managers) rather
than treating the alternatives as equivalent. Prefer the existing supported
multi-worker composition if it fits; no new scheduler or shared capacity
design."

THE ARRANGEMENT IS CHOSEN, AND IT IS NOT NEW. One manager, one pool, one
`baton.v12.stage-execution-deployment/2` document with FOUR workers -- two
implementation, two review -- and TWO `job_bindings`, one per Job. That is the
accepted multi-Job composition W119405 added and W130224 drove; this module
resolves its operands for the proposed deployment and holds the result against
the product's own `stage_execution.held_configuration`. It designs nothing.

WHY NOT TWO ISOLATED MANAGERS. Two managers over two stores would be two
deployments, and this gate asks whether ONE supported arrangement serves two
independent Jobs with overlapping execution. Two isolated managers would prove
that two single-Job deployments still work, which is what W239528 and W239533
already established one at a time; it would say nothing about shared capacity,
per-Job allocation or cross-Job isolation inside one pool -- the three things
an adoption decision actually turns on.

WHAT THIS MODULE DOES NOT DO. It starts nothing, opens no deployed store,
reaches no engine, image, network or credential, and creates no directory
outside the run root it is given. `held` is the real validator, not a local
imitation of it: a document this module composes is exactly as acceptable as
the manager finds it, including when the manager refuses it.
"""
import argparse
import hashlib
import json
import os
import pathlib

SCHEMA = "baton.v12.two-job-arrangement/1"
MULTI_CONFIG_SCHEMA = "baton.v12.stage-execution-deployment/2"

# THE INSTANCE MEMBERS THIS COMPOSER PUTS IN THE DEPLOYMENT DOCUMENT. The rest
# of the selections' `instance` is worker configuration, which reaches the
# document through `worker_document` instead.
_INSTANCE_MEMBERS = (
    "schema", "authority_store", "authority_uuid", "integration_store",
    "state_root", "pool_generation", "policy_generation", "checkpoint_profile",
    "integration_profile", "receipt_participants", "retention_policy_digest",
    "retention_disposition", "job_work_id", "review_work_id",
    "line_declared_base", "canonical_target_id")

# THE ROLES A BOUND JOB HAS, and the two this gate's limit admits. Integration
# is deliberately absent: ASSESSMENT-249338.md sets "no managed integration"
# and "human plus agent integrates results", so a deployment that configured an
# integrator would be configuring capacity nothing here is allowed to use.
LANES = ("implementation", "review")

# THE PRODUCT'S OWN WORD for declining the round, mirrored rather than spelled
# twice: `stage_execution.DECLINE_CORRECTION`. `two_jobs.held` compares them.
DECLINE_CORRECTION = "decline"

# THE PROPOSED INITIAL LIMIT, from the assessment, stated as data so the packet
# and the witness cannot disagree about it.
LIMITS = {
    "jobs": 2,
    "admissions": {"implementation": 2, "review": 2},
    "correction_rounds": 0,
    "retries": False,
    "managed_integration": False,
    "session_restoration": False,
    # PER INVOCATION, not per attempt. Review 2026-09-24T01:14:08Z:
    # `execution_limits` bounds ONE provider invocation and ONE
    # verification command; nothing in it bounds an attempt's whole
    # life, and this packet has no other mechanism that does. The
    # name said otherwise and the table repeated it.
    "per_invocation_seconds": 180,
    "total_seconds": 600,
    "cleanup_seconds": 60,
}

# WHAT EACH JOB OWNS ALONE, and the list is shorter than it first looked.
#
# THE STORAGE ROOTS ARE NOT ON IT. `workspace_storage`, `launch_home` and
# `credential_home` are INSTANCE members in the supported composition: one
# manager owns them and every attempt gets its own directory beneath.
# Demanding one root per Job would have invented a rule the product does not
# have, and the witness would have had to synthesize paths nothing mounted.
#
# NEITHER IS THE SOURCE OR THE BASE, and that one cost a broken witness to
# learn. Two Jobs may be TWO DEVELOPMENT LINES OF ONE TARGET at one base --
# which is exactly the accepted two-Job traversal, and the arrangement that
# refused it was refusing the supported shape. An Authority holds one
# canonical revision, so two Jobs that both publish are two lines of it.
#
# WHAT ACTUALLY MAKES THEM TWO JOBS is below: their identities, their Work,
# the four participants, and the task each one is given. Everything else that
# has to be separate -- the LINE, the WORKSPACE, the ATTEMPT -- is a fact
# about a run rather than about a document, and the witness asserts those on
# a run rather than declaring them here.
PER_JOB = ("job_id", "work_id", "producer_participant", "reviewer_participant",
           "task_document")


# EVERY OPERAND `worker_document` AND `submission` READ. Review
# 2026-09-23T17:17:50Z R1: the shipped template lacked `implementation_principal`
# and others, so a composer that looked complete refused at the first missing
# key. These two tuples are what `compose` checks the template against BEFORE
# building anything, so a drift is named rather than raised as a KeyError.
INSTANCE_OPERANDS = (
    "authority_store", "authority_uuid", "integration_store", "state_root",
    "pool_generation", "policy_generation", "checkpoint_profile",
    "integration_profile", "receipt_participants", "retention_policy_digest",
    "retention_disposition", "job_work_id", "review_work_id",
    "line_declared_base", "canonical_target_id", "policy_digest",
    "adapter_name", "adapter_digest", "engine", "image_digest",
    "provider_network", "workspace_storage", "workspace_group", "launch_home",
    "credential_home", "credential_sources", "credential_slots",
    "credential_profile", "workspace_capacity", "launch_contract",
    "review_route", "reviewed_route", "submission_id")
JOB_OPERANDS = (
    "job_id", "work_id", "producer_worker_id", "reviewer_worker_id",
    "producer_participant", "reviewer_participant", "implementation_principal",
    "review_principal", "nominated_source", "declared_base", "task_document",
    "canonical_target_id", "input_digest", "test_scope", "profile_name",
    "profile_digest", "review_profile_name", "review_profile_digest",
    "implementation_input_manifest", "review_input_manifest")


class ArrangementRefusal(Exception):
    """This arrangement cannot be composed as asked."""


def _refuse(message):
    raise ArrangementRefusal(message)


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def _disjoint(jobs, member):
    """One member's value, proved different across the two Jobs.

    ISOLATION IS CHECKED, NOT DECLARED. Two Jobs that named one workspace or
    one participant would compose and serve, and the run would look like a
    two-Job run while being one Job wearing two labels.
    """
    held = [one[member] for one in jobs if one.get(member) is not None]
    if len(set(held)) != len(held):
        _refuse(f"both Jobs name the same {member} ({held[0]!r}); two Jobs "
                f"that share it are not independent, whatever the binding "
                f"says")
    return held


def workers(jobs, *, worker_of):
    """Four participant-bound workers: each Job's producer and its reviewer.

    `worker_of` is the caller's own worker builder -- the fixture's in the
    witness, the deployment's in the packet -- so this function composes the
    POOL rather than inventing worker documents whose rules live elsewhere.
    """
    held = []
    for one in jobs:
        held.append(worker_of(
            "implementation", worker_id=one["producer_worker_id"],
            participant=one["producer_participant"], job=one))
        held.append(worker_of(
            "review", worker_id=one["reviewer_worker_id"],
            participant=one["reviewer_participant"], job=one))
    return held


def bindings(jobs):
    """One `job_bindings` entry per Job, each naming its own producer.

    The implementation and review Work are the SAME identity on purpose: the
    accepted review-cycle provider keys one line by one `(authority, work)`
    pair and `attach_review` binds the reviewer to the writer's own Work, so a
    review Work that differed could never attach. `_held_bindings` refuses it
    by name, and this composes what that validator accepts.
    """
    return [{"job_id": one["job_id"],
             "job_work_id": one["work_id"],
             "review_work_id": one["work_id"],
             "line_declared_base": one["declared_base"],
             "canonical_target_id": one["canonical_target_id"],
             "source_worker_id": one["producer_worker_id"]}
            for one in jobs]


def arrangement(*, instance, jobs, worker_of, extra_workers=(), schema=None):
    """The whole `/2` document: the pool, the bindings and the instance.

    Every rule that decides whether it could serve belongs to
    `held_configuration`, and `held` below runs it. What this refuses first is
    the thing that validator has no way to see: two Jobs that are secretly one.
    """
    if len(jobs) != LIMITS["jobs"]:
        _refuse(f"this arrangement binds exactly {LIMITS['jobs']} Jobs and was "
                f"given {len(jobs)}; a third Job is a different selection with "
                f"its own capacity question")
    for member in PER_JOB:
        _disjoint(jobs, member)
    # AND NO PARTICIPANT SERVES BOTH SIDES OF ONE REVIEW, or both Jobs. The
    # product refuses the first by name; the second is this gate's own limit,
    # because a reviewer shared across Jobs is a single point that sees both
    # subjects.
    everyone = [one[name] for one in jobs
                for name in ("producer_participant", "reviewer_participant")]
    if len(set(everyone)) != len(everyone):
        _refuse(f"these four roles resolve to {len(set(everyone))} distinct "
                f"participants: {sorted(set(everyone))}. Each Job's producer "
                f"and reviewer, and both Jobs, are independent identities")
    held = dict(instance)
    # THE POOL THIS GATE COMPOSES IS THE FOUR STAGE WORKERS. `extra_workers`
    # is carried through rather than silently dropped, because a deployment
    # may configure roles this gate does not admit STAGES for -- the fixture's
    # integrator is exactly that -- and a composer that quietly deleted a
    # configured worker would be changing somebody else's deployment. What
    # keeps the limit is the submission: no integration stage is submitted, so
    # no integration capacity is ever allocated.
    held["workers"] = workers(jobs, worker_of=worker_of) + list(extra_workers)
    held["job_bindings"] = bindings(jobs)
    # AND THE CORRECTION BOUNDARY IS SET HERE, not assumed. Review
    # 2026-09-23T17:12:02Z R3: the packet claimed `correction_policy:
    # "decline"` and the composed document carried no such member, which
    # means `open` -- today's behaviour -- so the claim was prose. It is now
    # the arrangement's own act, and `test_two_jobs` asserts it on the
    # document that actually serves.
    held["correction_policy"] = DECLINE_CORRECTION
    # THE INSTANCE'S OWN MEMBERS ARE LEFT ALONE, including the four a one-Job
    # document uses to bind its single Job. The first version of this removed
    # them, on the reading that "two places for one fact is how they drift" --
    # but that rule is `_held_bindings` refusing `job_bindings` in a `/1`
    # document, not the `/2` document dropping members `_MEMBERS` still
    # requires. `held_configuration` refused every document composed that way,
    # which is the product saying so directly. What makes the per-Job facts
    # authoritative here is that ALLOCATION reads `job_bindings`.
    if schema is not None:
        held["schema"] = schema
    return held


def imported_from(root):
    """Any package that did NOT resolve inside the pinned source."""
    import baton_v12
    import tools
    root = os.path.realpath(str(root))
    held = []
    for module in (tools, baton_v12):
        place = os.path.realpath(module.__file__ or "")
        if os.path.commonpath([place, root]) != root:
            held.append(f"{module.__name__} resolved to {place}")
    return held


def held_submission(document):
    """The PUBLIC reader's own judgment on the document about to be written.

    Review 2026-09-23T17:25:40Z: `composed` accepted an invalid
    `terminal_policy` and the serialized reader rejected it later. A composer
    that writes a document its own reader refuses has moved the failure from
    composition to submission, where an operator meets it instead.

    `owned_submission` is the reader `submit` uses and it takes no store, so
    this is the same judgment without touching one.
    """
    from baton_v12.job_manager.documents import owned_submission
    try:
        owned_submission(document)
    except Exception as failure:                             # noqa: BLE001
        _refuse(f"this composition produced a submission its own public "
                f"reader refuses: {type(failure).__name__}: {failure}")
    return document


def held(document, *, checkout=None):
    """The PRODUCT's validator, imported here rather than approximated."""
    from tools import stage_execution
    if stage_execution.DECLINE_CORRECTION != DECLINE_CORRECTION:
        _refuse(f"this arrangement declines corrections with "
                f"{DECLINE_CORRECTION!r} and the product's word is "
                f"{stage_execution.DECLINE_CORRECTION!r}")
    return stage_execution.held_configuration(document, checkout=checkout)


def worker_document(instance, job, role, *, worker_id, participant):
    """One configured worker, from the operands the selections resolved.

    EVERY MEMBER IS NAMED HERE because `single_worker`'s validator requires a
    closed `baton.v12.single-worker-deployment/4` document and a composer that
    guessed would be refused at the first offer rather than at composition.
    The two members that differ per ROLE are the launch role and the review
    route; the two that differ per JOB are the source and the task.
    """
    return {"worker_id": worker_id, "role": role, "deployment": {
        "schema": "baton.v12.single-worker-deployment/4",
        "authority_store": instance["authority_store"],
        "authority_uuid": instance["authority_uuid"],
        "participant": participant,
        "principal": job[f"{role}_principal"],
        "profile_name": (job["profile_name"] if role == "implementation"
                         else job["review_profile_name"]),
        "profile_digest": (job["profile_digest"] if role == "implementation"
                           else job["review_profile_digest"]),
        "policy_digest": instance["policy_digest"],
        "adapter_name": instance["adapter_name"],
        "adapter_digest": instance["adapter_digest"],
        "engine": instance["engine"],
        "image_digest": instance["image_digest"],
        "network": instance["provider_network"],
        "workspace_storage": instance["workspace_storage"],
        "workspace_group": instance["workspace_group"],
        "launch_home": instance["launch_home"],
        "credential_home": instance["credential_home"],
        "credential_sources": instance["credential_sources"],
        "credential_slots": instance["credential_slots"],
        "credential_profile": instance["credential_profile"],
        "nominated_source": job["nominated_source"],
        "workspace_capacity": instance["workspace_capacity"],
        # ONE MANIFEST PER JOB, for BOTH its workers. `input_digest` is a JOB
        # fact in `baton.v12.job-submission/1`, and a worker whose manifest
        # hashes to a different identity cannot serve that Job's stages: with
        # a separate review manifest the review stage stayed QUEUED while the
        # implementations admitted, which is the same shape W239533 met.
        "input_manifest": job["implementation_input_manifest"],
        "task_document": job["task_document"],
        "launch_contract": instance["launch_contract"],
        "launch_role": role,
        "review_route": (instance["review_route"] if role == "implementation"
                         else instance["reviewed_route"]),
        "retention_policy_digest": instance["retention_policy_digest"],
        "retention_disposition": instance["retention_disposition"]}}


# THE SUBMISSION SCHEMA THAT CAN CARRY A CEILING. Owner 2026-09-24T00:58Z
# saw the live run bounded at 3600 compatibility seconds while this packet
# declared 180, and the reason runs deeper than a missing member:
# `documents.SUBMISSION_LIMITS_SCHEMAS` is `/2` alone, so on `/1` the
# per-Job `execution_limits` member is REFUSED as unrecognised. The
# selected bound could not be expressed in the document this packet was
# composing at all. Both versions are supported; this is the one that
# carries what the packet promises.
SUBMISSION_SCHEMA = "baton.v12.job-submission/2"
# WHAT A SUBMITTED JOB DECLARES BESIDES ITS STAGES. Review
# 2026-09-23T17:17:50Z: the generated document omitted both and the public
# reader refused it. They are Job facts rather than deployment ones -- which
# tests a terminal result is judged against, and what happens when it is
# reached -- so they are per-Job operands rather than constants here.
TERMINAL_POLICY = "report-and-hold"


# THE CEILINGS THIS PACKET ASKS FOR, in the product's own setting names.
# `documents.JOB_LIMIT_MEMBER` is `execution_limits`, optional on this
# submission schema, and `execution_limits.LIMIT_MEMBERS` names exactly these
# two. A Job that omits it gets the compatibility defaults -- 3600 seconds for
# a provider turn -- which is what the live run of 2026-09-24T00:53Z was
# given while this packet's own table said 180.
def requested_limits():
    """What each Job asks the manager for, derived from `LIMITS`.

    ONE SOURCE. The declared bound and the submitted operand are the same
    number by construction; the defect this corrects is precisely that they
    were two.
    """
    return {"provider_turn_seconds": LIMITS["per_invocation_seconds"],
            "verification_command_seconds":
                LIMITS["per_invocation_seconds"]}


def submission(jobs, *, submission_id, policy_digest):
    from baton_v12.contracts import job_input_identity

    """One submission carrying both Jobs, review behind implementation.

    NO INTEGRATION STAGE, and that is what actually keeps this gate's
    no-integration limit -- review 2026-09-23T17:12:02Z R3 found the witness
    submitting one for both Jobs while the packet said there were none. A
    limit the documents assert and the submission contradicts is not a limit.
    """
    return {"schema": SUBMISSION_SCHEMA,
            "submission_id": submission_id,
            "jobs": [{"job_id": one["job_id"],
                      # THE SELECTED CEILINGS, ASKED FOR. Owner
                      # 2026-09-24T00:58Z observed 3600 from compatibility
                      # defaults on a run this packet said was bounded at
                      # 180, and the launch document's `requested: {}` is why.
                      "execution_limits": requested_limits(),
                      # THE JOB INPUT IDENTITY, not a manifest digest. W239533
                      # met this exact defect: a stage whose input_digest is
                      # not `job_input_identity` of the worker's own manifest
                      # stays QUEUED for a whole run, and the deferral says
                      # "no worker this deployment configures ... can serve".
                      "input_digest": job_input_identity(
                          one["implementation_input_manifest"]),
                      "policy_digest": policy_digest,
                      "test_scope": one["test_scope"],
                      "terminal_policy": one.get("terminal_policy",
                                                 TERMINAL_POLICY),
                      "stages": [
                          {"kind": "implementation", "work_id": one["work_id"],
                           "profile_name": one["profile_name"],
                           "profile_digest": one["profile_digest"],
                           "depends_on": []},
                          {"kind": "review", "work_id": one["work_id"],
                           "profile_name": one["review_profile_name"],
                           "profile_digest": one["review_profile_digest"],
                           "depends_on": [{"job_id": one["job_id"],
                                           "kind": "implementation"}]}]}
                     for one in jobs]}


def composed(selections):
    """The deployment and the submission this packet actually writes.

    Review 2026-09-23T17:12:02Z R1: the first version RETURNED THE SELECTIONS'
    own `arrangement` member unchanged -- it built no workers, no bindings and
    no submission, and what it handed to the validator was a description of a
    deployment rather than one. `held` refused it for the schema before ever
    reaching an operand, which is the product saying the composer had not run.
    """
    unresolved = sorted(_unresolved(selections))
    if unresolved:
        _refuse("this selections document is not resolved: "
                + ", ".join(unresolved) + ". A packet composed from an open "
                "choice would be naming an operator's decision for them.")
    given = selections["arrangement"]
    instance = given["instance"]
    jobs = given["jobs"]
    missing = sorted(f"instance.{one}" for one in INSTANCE_OPERANDS
                     if one not in instance)
    for index, one in enumerate(jobs):
        missing.extend(f"jobs[{index}].{name}" for name in JOB_OPERANDS
                       if name not in one)
    if missing:
        _refuse("this selections document is missing operands this "
                "composition consumes: " + ", ".join(sorted(missing))
                + ". A template and a composer that disagree produce a "
                "packet that refuses at its first offer instead of here.")
    deployment = arrangement(
        instance={name: value for name, value in instance.items()
                  if name in _INSTANCE_MEMBERS},
        jobs=jobs,
        worker_of=lambda role, *, worker_id, participant, job:
            worker_document(instance, job, role, worker_id=worker_id,
                            participant=participant),
        schema=MULTI_CONFIG_SCHEMA)
    held(deployment)
    return {"deployment.json": deployment,
            "submission.json": held_submission(submission(
                jobs, submission_id=instance["submission_id"],
                policy_digest=instance["policy_digest"]))}


def _unresolved(value, path=""):
    held_open = []
    if isinstance(value, dict):
        for name, inner in value.items():
            held_open.extend(_unresolved(inner, f"{path}.{name}" if path
                                         else name))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            held_open.extend(_unresolved(inner, f"{path}[{index}]"))
    elif isinstance(value, str) and value.startswith("<OWNER:"):
        held_open.append(path)
    return held_open


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selections", required=True)
    parser.add_argument("--into", default=None,
                        help="the run root to write the packet into; it is "
                             "created and must not already exist")
    parser.add_argument("--check", action="store_true",
                        help="run every check this composition runs -- the "
                             "digest pins, the import provenance and the "
                             "whole composition -- and WRITE NOTHING. A "
                             "caller that needs the validation to happen "
                             "where the composition happens runs this first.")
    chosen = parser.parse_args(argv)
    if not chosen.check and chosen.into is None:
        parser.error("--into is required unless --check is given")
    selections = json.loads(
        pathlib.Path(chosen.selections).read_text("utf-8"))
    # THE PINS ARE CHECKED BEFORE ANYTHING IS COMPOSED. Review
    # 2026-09-23T17:17:50Z: "bind successful pin/import validation to
    # compose/start". Step 1 of the packet asks an operator to run the check;
    # a composition that proceeded on a drifted snapshot would be composing
    # against bytes nobody accepted, whether or not the operator remembered.
    import verify_247941
    held_pins = verify_247941.pins()
    if not held_pins["agree"]:
        _refuse("the selected artifacts no longer match what "
                "ASSESSMENT-249338.md pinned:\n"
                + json.dumps(held_pins, indent=2, sort_keys=True))
    # AND THE BYTES THAT ANSWERED ARE THE BYTES THAT WERE PINNED. Review
    # 2026-09-23T17:25:40Z: the pin helper checked the snapshot while the
    # process imported the checkout, so a passing check said nothing about
    # what actually composed. `tools` and `baton_v12` must resolve inside the
    # pinned source, which is what `PYTHONPATH="$BOUND:$DOSSIER"` in step 3
    # arranges.
    imported = imported_from(verify_247941.SNAPSHOT)
    if imported:
        _refuse("this composition is bound to the pinned manager source, and "
                "these packages resolved elsewhere:\n  - "
                + "\n  - ".join(imported)
                + f"\nBind PYTHONPATH to {verify_247941.SNAPSHOT} as step 3 "
                  f"of ADOPTION-247941.md prints it.")
    documents = composed(selections)
    if chosen.check:
        # NOTHING IS WRITTEN. The pins, the provenance and the composition
        # have all run in THIS process, which is the pinned one.
        print(json.dumps({"_checked": sorted(documents),
                          "_pins_agree": True, "_written": []},
                         indent=2, sort_keys=True))
        return 0
    into = pathlib.Path(chosen.into)
    if into.exists():
        _refuse(f"{into} already exists; this composition is create-only and "
                f"will not write into a root somebody else may be using")
    into.mkdir(parents=True)
    places = {}
    for name, body in sorted(documents.items()):
        place = into / name
        place.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
        places[name] = sha(place)
    places["_pins_agree"] = True
    print(json.dumps(places, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
