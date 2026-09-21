"""One-time deployment setup for the persistent v12 stack. W183883.

THE REMAINDER OF PLAN STEP 3. `just setup` prepares the interpreter; this
prepares the DEPLOYMENT: the Authority this stack serves under, the Works its
Jobs are bound to, the routes and capability grants those Works need, the
external state layout, and the `stage_execution` configuration document the
manager composes from.

WHAT IT DOES NOT DO, and none of these is an oversight:

  it selects no production values -- the image, adapter, profile, credential,
    workload and target are the operator's, named in one input document, and a
    missing one is REFUSED by name rather than filled in with a fixture;
  it submits no Job and executes nothing;
  it never touches v11, and never runs a provider or an engine.

EVERYTHING DERIVABLE IS DERIVED. A principal is `Authority.principal_of`, not a
second place to spell an identity. The layout is one `state_root`. The Works,
the route handlers and the four receipt grants come from the participants and
Jobs already named. What the operator supplies is what nothing can compute.

VALIDATED BEFORE ANYTHING DURABLE. Every missing or malformed input is named in
one refusal, before a directory is made or a store is opened -- the rule
`stage_execution.operations_from` already keeps for the same reason: a refusal
that has already changed durable state is not a refusal.

REPEATING IT IS SAFE. An Authority that already exists is reused, not recreated;
a Work already bound as this document binds it is left alone; a Work bound
DIFFERENTLY is refused rather than rewritten, because a Job's line and target
are not something a setup command may quietly move.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import sys
import time

SCHEMA = "baton.v12.stack-bootstrap/1"
# What this helper writes about what IT prepared, in one shape whichever
# stage-execution variant is emitted. See `record_of`.
RECORD_SCHEMA = "baton.v12.stack-bootstrap-record/1"

# The roles a stage deployment serves, and the two schemas it may be written as.
# Both are `stage_execution`'s; they are named here because this module WRITES
# that document and a second opinion about its shape would be a second contract.
ROLES = ("implementation", "review", "integration")
ONE_JOB_SCHEMA = "baton.v12.stage-execution-deployment/1"
MULTI_JOB_SCHEMA = "baton.v12.stage-execution-deployment/2"

# The three receipt participants an accepted integration needs. The integrator
# is DERIVED from the integration profile and the publisher from the producing
# worker's own participant, so neither is configured here -- naming them twice
# is how two places for one fact drift apart.
RECEIPTS = ("verification", "review", "approval")

# What the operator must name. Everything else this module derives.
#
# NEITHER AN IDENTITY NOR A JOB IS AMONG THEM.
# OWNER-FRESH-INSTALL-20260916.md: "Why are we asking for any job, this is a
# fresh install". An installation initializes an instance -- its runtime, its
# empty stores, its pool and its profiles -- and a Work, a declared base, a
# canonical target and a producer assignment are facts about a JOB, supplied
# and validated when one is created. The Authority identity is likewise not an
# operator selection: it is generated ONCE here and persisted at the
# destination, so separate installs have separate identities and no two
# documents can name one.
REQUIRED = ("schema", "state_root", "checkpoint_profile",
            "integration_profile", "retention_policy_digest",
            "retention_disposition", "pool_generation", "policy_generation",
            "receipt_participants")
_WORKER = ("worker_id", "role", "participant", "deployment")
# A Job binds ONE Work. `stage_execution._held_bindings` requires the
# implementation and review Work IDs to be EQUAL within a binding -- the
# review-cycle provider keys one line by one `(authority, work)` pair and
# `attach_review` binds the reviewer to the writer's own Work -- so this input
# names `work_id` once rather than inviting two that could differ.
_JOB = ("job_id", "work_id", "line_declared_base", "canonical_target_id",
        "source_worker_id")
_PROFILE = ("profile_kind", "profile_version", "integrator_participant",
            "instructions_digest")

# WHAT ELSE A DEPLOYMENT MAY SELECT, and it is the accepted optional set rather
# than a shorter one this module happened to copy. REVIEW 2026-09-16T10-58-20Z
# [F3]: `integration_preparation: true` was ACCEPTED here and then left out of
# the emitted configuration, so the serving deployment defaulted it to false and
# the operator's requested managed preparation was silently disabled. Every one
# of these is carried through, and `job_bindings` is absent on purpose because
# this module DERIVES it from the Jobs.
OPTIONAL = ("integration_target", "integration_target_reference",
            "integration_workspace", "integration_observer",
            "integration_instructions", "integration_preparation",
            "result_judgment_workers")

# WHAT AN INPUT MAY STILL NAME AND THE EMITTED CONFIGURATION NEVER CARRIES.
# `jobs` is accepted and validated in full when it is supplied -- every rule
# about distinct identities, configured producers and complete bindings stands
# -- and its absence is the ordinary fresh install. It is kept OUT of
# `OPTIONAL` because that tuple is what travels verbatim into the
# `stage_execution` document, whose closed schema names `job_bindings` instead.
# AND `workers` IS ONE OF THEM. A worker is configured WITH the Job it serves:
# its `deployment` carries a digest-sealed input manifest naming an Authority
# and a Work, so it cannot be written for an instance that does not exist yet
# and it is not an instance selection. An installation configures no capacity;
# a repeated bootstrap that supplies workers is held to every rule they ever
# had.
DEFERRED = ("jobs", "workers")

# NOTHING INSTALLER-ONLY TRAVELS IN THE INPUT DOCUMENT ANY MORE.
# OWNER-VERSION-STAMP-20260916.md: "the bootstrap source is the repository
# containing the development v12/justfile, not a source location to communicate
# in deployed JSON". The source is INFERRED from this distribution's own
# checkout and may be overridden by a command operand; a document that still
# names it is refused with that said, rather than quietly ignored.
INSTALLER_ONLY = ()
SUPERSEDED = {
    "authority_uuid":
        "an instance generates its own Authority identity once, when it is "
        "installed, and persists it at the destination; every later lifecycle "
        "operation reuses it and separate installations have separate "
        "identities. Remove the member -- an input document that named one "
        "would be a second place for a fact this instance already owns.",
    "repository_source":
        "the repositories are cloned from the checkout this bootstrap runs "
        "from -- the repository containing v12/justfile -- so a deployment "
        "document no longer names a source. Remove the member; use "
        "`--repository-source` if you mean a different checkout, or "
        "`--no-repositories` if you mean none.",
}

# The grant each receipt actor needs, in the bound Work's own scope. The
# vocabulary is the Authority's.
GRANTS = {"verification": "verify", "review": "review", "approval": "approve"}
INTEGRATOR_GRANT = "integrate"

# The route each stage is served on. `review_route` on a worker names where its
# own ending hands the Work on to, which is why the last one is not a stage.
ROUTES = {"implementation": "impl", "review": "rview", "integration": "integration"}


class BootstrapRefusal(Exception):
    """An operator-facing refusal. Its text is the whole message."""


def jobs_of(document):
    """The Jobs this document names, which for a fresh installation is none."""
    return document.get("jobs") or []


def workers_of(document):
    """The pool this document configures, which for a fresh install is none."""
    return document.get("workers") or []


IDENTITY_SCHEMA = "baton.v12.instance-identity/1"
# HOW BIG AN IDENTITY RECORD MAY BE. It names a schema and 32 hexadecimal
# characters; anything approaching this is not one. The bound exists so a
# reader cannot be handed a file it will only partly see -- see `_identity_bytes`.
IDENTITY_LIMIT = 64 * 1024


def _identity_bytes(place):
    """This root's OWN identity record, read without following anything.

    Review 2026-09-16T22-27-59Z [F3]: this was `Path.read_bytes`, which follows
    a symlink -- so two separate destinations could each carry a LINK at this
    name pointing at one external file, and both would read the same identity,
    both report it as already persisted, and both believe they were installed
    independently. `O_NOFOLLOW` refuses the link itself and `fstat` refuses
    anything that is not a regular file, so what is read is a file this
    destination owns or nothing at all.

    THE FOREIGN BYTES ARE LEFT EXACTLY AS THEY ARE. A link somebody else put
    here is refused, not repaired: removing it would destroy state this command
    did not create, and following it would write through a name somebody else
    controls.
    """
    import stat

    try:
        # O_NONBLOCK, AND IT IS NOT A PERFORMANCE CHOICE. Review
        # 2026-09-16T22-36-58Z: a FIFO at this name made `os.open` BLOCK
        # waiting for a writer -- before `fstat` could say it was a FIFO. A
        # setup command that hangs forever on a named pipe somebody left in a
        # destination is worse than one that refuses it, and the refusal is the
        # right answer either way. Opening a FIFO read-only and non-blocking
        # succeeds at once with no writer, so the check below is reached.
        #
        # THE NO-FOLLOW PROOF IS UNCHANGED: O_NOFOLLOW still refuses the link
        # itself, and what is fstat'ed is this descriptor rather than the path.
        handle = os.open(str(place),
                         os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as failure:
        # ELOOP is the link case and is worth its own sentence, because "could
        # not be read" would send an operator looking for a permission problem.
        raise BootstrapRefusal(
            "the instance identity at " + str(place) + " is not a file this "
            "destination owns (" + type(failure).__name__ + ": "
            + str(failure) + "). A link or a dangling link at that name is "
            "refused rather than followed: an instance owns what is under its "
            "own destination, and two destinations pointing at one identity "
            "would be one Authority wearing two names. Nothing here removed "
            "it.")
    try:
        held = os.fstat(handle)
        if not stat.S_ISREG(held.st_mode):
            raise BootstrapRefusal(
                "the instance identity at " + str(place) + " is a "
                + _node_kind(held.st_mode) + " rather than a regular file, so "
                "what Authority this root is bound to is unknown. Nothing here "
                "replaced it.")
        # THE WHOLE FILE OR A REFUSAL, NEVER A PREFIX. Review
        # 2026-09-16T22-36-58Z: this was one `os.read(handle, 64 * 1024)`,
        # which silently discards everything after -- so a valid record padded
        # out past that bound and followed by rubbish PARSED, and the file that
        # is actually on disk does not. A reader that sees part of a document
        # is answering about a document nobody wrote.
        raw, chunk = b"", True
        while chunk:
            chunk = os.read(handle, 8192)
            raw += chunk
            if len(raw) > IDENTITY_LIMIT:
                raise BootstrapRefusal(
                    "the instance identity at " + str(place) + " is larger "
                    "than " + str(IDENTITY_LIMIT) + " bytes, which an identity "
                    "record is not; what Authority this root is bound to is "
                    "unknown and nothing here replaced it.")
        return raw
    finally:
        os.close(handle)


def _node_kind(mode):
    """What this descriptor actually is, said in the operator's words."""
    import stat

    for asking, name in ((stat.S_ISDIR, "directory"), (stat.S_ISFIFO, "named "
                         "pipe"), (stat.S_ISSOCK, "socket"),
                         (stat.S_ISCHR, "character device"),
                         (stat.S_ISBLK, "block device")):
        if asking(mode):
            return name
    return "special file"


def _identity_held(place):
    """The identity this root already persisted, or None."""
    raw = _identity_bytes(place)
    if raw is None:
        return None
    try:
        held = json.loads(raw)
    except ValueError as failure:
        raise BootstrapRefusal(
            "the instance identity at " + str(place) + " could not be read ("
            + type(failure).__name__ + "), so what Authority this root is "
            "bound to is unknown. Nothing here rebinds state it cannot "
            "identify.")
    if type(held) is not dict or held.get("schema") != IDENTITY_SCHEMA:
        raise BootstrapRefusal(
            "the instance identity at " + str(place) + " is not a "
            + IDENTITY_SCHEMA + " document, so what Authority this root is "
            "bound to is unknown.")
    uuid = held.get("authority_uuid")
    if type(uuid) is not str or len(uuid) != 32 or any(
            one not in "0123456789abcdef" for one in uuid):
        raise BootstrapRefusal(
            "the instance identity at " + str(place) + " does not name 32 "
            "lowercase hexadecimal characters, so what Authority this root is "
            "bound to is unknown.")
    return uuid


def identity(places):
    """This instance's Authority identity: the one already here, or a new one.

    OWNER-FRESH-INSTALL-20260916.md: "Generate the instance authority identity
    once and persist it at the destination; subsequent lifecycle operations
    reuse it. Separate installs have separate IDs."

    GENERATED, NEVER NAMED. An input document that carried one would be a
    second place for a fact this instance owns, and two roots installed from
    the SAME document would be one Authority wearing two destinations. A fresh
    identity is minted here; a root that already persisted one keeps it, which
    is what makes a repeated bootstrap a repeat rather than a rebinding.
    """
    import uuid as identities

    held = _identity_held(places["identity"])
    if held is not None:
        return held, False
    return identities.uuid4().hex, True


def persist_identity(places, uuid):
    """Write this instance's identity EXCLUSIVELY, once.

    O_EXCL, so two bootstraps racing for one fresh root cannot both believe
    they minted it: the loser reads what the winner wrote and is then held to
    it by `conflicts` like any other repeat.
    """
    place = Path(places["identity"])
    place.parent.mkdir(parents=True, exist_ok=True)
    document = json.dumps({"schema": IDENTITY_SCHEMA,
                           "authority_uuid": uuid}, sort_keys=True) + "\n"
    try:
        handle = os.open(str(place), os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | os.O_NOFOLLOW, 0o644)
    except FileExistsError:
        # THE SAME SAFE READ. [F3]: `O_EXCL` protects the CREATE and says
        # nothing about what is already at the name -- a link here means the
        # exclusive create failed against somebody else's name, and reading
        # through it is exactly what must not happen.
        held = _identity_held(place)
        if held != uuid:
            raise BootstrapRefusal(
                "this root persisted the identity " + repr(held)
                + " while this bootstrap was composing " + repr(uuid)
                + "; nothing here rebinds an instance somebody else installed.")
        return held
    with os.fdopen(handle, "w") as writing:
        writing.write(document)
    return uuid


def _unknown(document):
    """Every member this input document names that nothing reads.

    [F3]: the member set was never closed, so a misspelled operand was ignored
    in silence. A selection this module cannot carry is REFUSED rather than
    accepted and dropped -- the two are indistinguishable to an operator until
    the deployment behaves differently from what they asked for.
    """
    allowed = (set(REQUIRED) | set(OPTIONAL) | set(INSTALLER_ONLY)
               | set(DEFERRED))
    found = [name + " -- " + SUPERSEDED[name] if name in SUPERSEDED else name
             for name in document if name not in allowed]
    for index, worker in enumerate(document.get("workers") or []):
        if type(worker) is dict:
            found += ["workers[%d].%s" % (index, name) for name in worker
                      if name not in _WORKER]
    for index, job in enumerate(document.get("jobs") or []):
        if type(job) is dict:
            found += ["jobs[%d].%s" % (index, name) for name in job
                      if name not in _JOB]
    supplied = document.get("receipt_participants")
    if type(supplied) is dict:
        found += ["receipt_participants." + name for name in supplied
                  if name not in RECEIPTS]
    profile = document.get("integration_profile")
    if type(profile) is dict:
        found += ["integration_profile." + name for name in profile
                  if name not in _PROFILE]
    return found


def _missing(document):
    """Every input this document does not supply, named at once."""
    absent = [name for name in REQUIRED if document.get(name) in (None, "", [], {})]
    if document.get("schema") not in (None, SCHEMA):
        absent.append("schema (this reads " + SCHEMA + " and this document is "
                      + repr(document.get("schema")) + ")")
    for index, worker in enumerate(document.get("workers") or []):
        if type(worker) is not dict:
            absent.append("workers[%d] (a document)" % index)
            continue
        absent += ["workers[%d].%s" % (index, name) for name in _WORKER
                   if worker.get(name) in (None, "", {})]
    for index, job in enumerate(document.get("jobs") or []):
        if type(job) is not dict:
            absent.append("jobs[%d] (a document)" % index)
            continue
        absent += ["jobs[%d].%s" % (index, name) for name in _JOB
                   if job.get(name) in (None, "")]
    supplied = document.get("receipt_participants")
    if type(supplied) is dict:
        absent += ["receipt_participants." + name for name in RECEIPTS
                   if not supplied.get(name)]
    profile = document.get("integration_profile")
    if type(profile) is dict:
        absent += ["integration_profile." + name for name in _PROFILE
                   if profile.get(name) in (None, "")]
    return absent


def held(document):
    """The operator's selections, proved before anything durable happens.

    EVERY FAULT AT ONCE. An operator assembling this for the first time should
    see the whole list rather than discover it one run at a time, which is the
    same decision `stack.configured` already makes for its four operands.
    """
    if type(document) is not dict:
        raise BootstrapRefusal("the bootstrap input is one document, not "
                               + type(document).__name__)
    found = _unknown(document)
    if found:
        raise BootstrapRefusal(
            "this deployment cannot be prepared: nothing reads "
            + ", ".join(sorted(found)) + ". A selection this helper cannot "
            "carry is refused rather than accepted and dropped, because the "
            "two are indistinguishable to an operator until the deployment "
            "behaves differently from what they asked for. The supported "
            "optional selections are " + ", ".join(OPTIONAL) + ".")
    absent = _missing(document)
    if absent:
        raise BootstrapRefusal(
            "this deployment cannot be prepared: the following are not named "
            "and cannot be derived -- " + ", ".join(sorted(absent))
            + ". These are production selections; nothing here invents one, and "
              "a fixture digest, proof task or disposable credential is not a "
              "production selection. See v12/STACK.md.")

    faults = []
    if not os.path.isabs(document["state_root"]):
        faults.append("state_root must be absolute; runtime state resolves "
                      "against whatever directory a recipe ran from otherwise")
    by_role = {}
    for worker in workers_of(document):
        by_role.setdefault(worker["role"], []).append(worker)
    # EVERY REQUIRED ROLE, WHENEVER ANY WORKER IS CONFIGURED. An installation
    # configures none and serves none; a deployment that configures SOME is a
    # pool with a hole in it. The INTEGRATION role is optional -- owner
    # 2026-09-20T14:57:48Z (W202663, the PR model): integration is a human
    # act or an explicitly submitted ordinary Job, never an obligatory
    # worker, and `stage_execution`'s own coverage gate says the same.
    for role in (ROLES if workers_of(document) else ()):
        if role != "integration" and not by_role.get(role):
            faults.append("no worker is configured for the " + role + " stage")
    for role in set(by_role) - set(ROLES):
        faults.append("this deployment serves " + ", ".join(ROLES)
                      + " and a worker names the role " + repr(role))
    named = [one["worker_id"] for one in workers_of(document)]
    if len(set(named)) != len(named):
        faults.append("every worker_id is distinct; these are " + repr(named))

    # THE INDEPENDENCE RULE, held here rather than discovered after containers
    # have started. `stage_execution.INDEPENDENT` refuses a deployment whose
    # implementation and review could never produce an independent review.
    producers = {one["participant"] for one in by_role.get("implementation", [])}
    reviewers = {one["participant"] for one in by_role.get("review", [])}
    shared = producers & reviewers
    if shared:
        faults.append("implementation and review may share no participant, and "
                      + ", ".join(sorted(shared)) + " serves both")

    # EVERY JOB RULE, UNCHANGED, WHENEVER JOBS ARE SUPPLIED. The fresh install
    # names none; one that names some is held to exactly what it always was.
    producing = {one["worker_id"] for one in by_role.get("implementation", [])}
    bound = [job["job_id"] for job in jobs_of(document)]
    if len(set(bound)) != len(bound):
        faults.append("every job_id is distinct; these are " + repr(bound))
    for job in jobs_of(document):
        if job["source_worker_id"] not in producing:
            faults.append("job " + repr(job["job_id"]) + " names the producer "
                          + repr(job["source_worker_id"])
                          + ", which is not a configured implementation worker")

    # THE DISTINCT-BASE COUNT RULE NO LONGER LIVES HERE. W202663 owner212383
    # selects review212328's bounded amendment: this pure validator cannot
    # tell a RETAINED binding (whose base is history this root persisted)
    # from a NEW one, so counting distinct bases over the whole document
    # refused exactly the incremental preparation an advanced target
    # requires. The rule moved to `admissible_bases`, which runs in `prepare`
    # immediately after `conflicts` -- store-aware, still before ANY durable
    # effect, so both of this module's documented promises hold: nothing
    # durable happens until every check passes, and a fresh deployment still
    # refuses two bases before the first proposal. Each binding's base FORM
    # is still proved here, per job, above.
    if faults:
        raise BootstrapRefusal("this deployment cannot be prepared: "
                               + "; ".join(faults))
    return document


# -- the external layout ------------------------------------------------------


def layout(root):
    """Where each durable thing lives under the one root the operator chose."""
    root = Path(root)
    # THE FOUR STORES LIVE UNDER `db/`, and the stage deployment's own mutable
    # root beside them rather than under `state/`. W183883: `tools.instance`
    # derives exactly these places from a destination, and two layouts that
    # disagreed about where a Job store is would be two deployments sharing a
    # name. `state/` is the STACK's process records, which is a different thing
    # from the stage deployment's workspace root and is kept a different path.
    return {"state_root": str(root),
            # WHERE THIS INSTANCE'S IDENTITY PERSISTS, in its own file.
            # OWNER-FRESH-INSTALL-20260916.md: it is generated once and reused
            # by every later operation. It is NOT kept only in the record,
            # because a record is custody evidence about BINDINGS and is read
            # beside the emitted configuration -- an instance that binds
            # nothing still has an identity, and the identity has to be
            # readable before either of those documents exists.
            "identity": str(root / "authority-identity.json"),
            "authority_store": str(root / "db" / "authority.sqlite3"),
            "job_store": str(root / "db" / "jobs.sqlite3"),
            "control_store": str(root / "db" / "control.sqlite3"),
            "integration_store": str(root / "db" / "integration.sqlite3"),
            "deployment_state": str(root / "deployment-state"),
            "record": str(root / "bootstrap.json"),
            "configuration": str(root / "deployment.json")}


def variant(document):
    """Which accepted schema this deployment actually is.

    [F1]: this was chosen by Job COUNT alone, and `/1` permits only ONE worker
    per role. A single Job served by a two-producer pool therefore passed this
    helper and emitted a document the manager refuses. The shape of the POOL is
    half the answer.
    """
    by_role = {}
    for worker in workers_of(document):
        by_role.setdefault(worker["role"], []).append(worker["worker_id"])
    one_each = all(len(by_role.get(role, [])) == 1 for role in ROLES)
    # AN INSTANCE THAT BINDS NOTHING IS THE MULTI-JOB DOCUMENT WITH AN EMPTY
    # BINDING LIST. `/1` DERIVES its single binding from its own global Work,
    # base and target, so it cannot express "none" -- the shape that can is the
    # one that says its bindings out loud.
    return (ONE_JOB_SCHEMA if len(jobs_of(document)) == 1 and one_each
            else MULTI_JOB_SCHEMA)


def configuration(document, principals=None):
    """The `stage_execution` document this deployment composes from.

    ONE JOB OR SEVERAL, and the schema follows the deployment rather than a
    preference. A `/1` document DERIVES its single binding from members it
    already carries and is refused if it also names `job_bindings`; a `/2`
    document names each Job's own Work, base, target and producer. Both are
    `stage_execution`'s rules, and this writes whichever one the operator's
    Jobs actually are.
    """
    places = layout(document["state_root"])
    jobs = jobs_of(document)
    # THE DERIVED IDENTITIES AND PATHS GO IN HERE, not afterwards. [F1]: they
    # used to be grafted on after the Authority had been composed, so what was
    # validated -- when anything was -- was not what was written.
    workers = []
    for one in workers_of(document):
        deployment = dict(one["deployment"],
                          participant=one["participant"],
                          authority_store=places["authority_store"],
                          authority_uuid=document["authority_uuid"],
                          launch_role=one["role"])
        if principals is not None:
            deployment["principal"] = principals[one["participant"]]
        workers.append({"worker_id": one["worker_id"], "role": one["role"],
                        "deployment": deployment})
    chosen = variant(document)
    built = {
        "schema": chosen,
        "authority_store": places["authority_store"],
        "authority_uuid": document["authority_uuid"],
        "integration_store": places["integration_store"],
        "state_root": places["deployment_state"],
        "pool_generation": document["pool_generation"],
        "policy_generation": document["policy_generation"],
        "checkpoint_profile": document["checkpoint_profile"],
        "integration_profile": document["integration_profile"],
        "retention_policy_digest": document["retention_policy_digest"],
        "retention_disposition": document["retention_disposition"],
        "receipt_participants": dict(document["receipt_participants"]),
        "workers": workers}
    if jobs:
        # THE SAME WORK ON BOTH AXES. `_held_bindings` requires the
        # implementation and review Work IDs to be equal, so one input member
        # answers for both rather than two that could disagree.
        built["job_work_id"] = jobs[0]["work_id"]
        built["review_work_id"] = jobs[0]["work_id"]
        built["line_declared_base"] = jobs[0]["line_declared_base"]
        built["canonical_target_id"] = jobs[0]["canonical_target_id"]
    if chosen == MULTI_JOB_SCHEMA:
        # AND THE EMPTY LIST WHEN THERE ARE NONE, which is the instance-only
        # deployment `stage_execution` admits: no global Work, base or target,
        # because those are facts about a Job and this binds none.
        built["job_bindings"] = [
            {"job_id": job["job_id"], "job_work_id": job["work_id"],
             "review_work_id": job["work_id"],
             "line_declared_base": job["line_declared_base"],
             "canonical_target_id": job["canonical_target_id"],
             "source_worker_id": job["source_worker_id"]} for job in jobs]
    for name in OPTIONAL:
        # PRESENT, not merely non-null. REVIEW 2026-09-16T11-14-19Z [G2]: this
        # read `is not None`, so an explicitly supplied `null` was dropped and
        # the consumer defaulted it -- turning an INVALID request into a
        # different VALID one, and hiding from the accepted validator what the
        # operator actually supplied. Omission stays omission; anything present
        # travels, and is refused downstream if it is not a legal value.
        if name in document:
            built[name] = document[name]
    return built


def capacity(document):
    """What this deployment can actually serve, said rather than implied.

    A PRODUCER COUNT IS NOT A CONCURRENCY CLAIM. Each Job is bound to ONE
    producer, one Work, one line and one canonical target; review and
    integration are served by the workers configured for those roles, and the
    accepted composition serializes against a shared target. So what this
    reports is what is CONFIGURED and how the Jobs are bound to it -- not a
    promise that arbitrary Jobs traverse review and integration at once.
    """
    by_role = {}
    for worker in workers_of(document):
        by_role.setdefault(worker["role"], []).append(worker["worker_id"])
    jobs = jobs_of(document)
    return {"schema": variant(document),
            "workers_by_role": {role: sorted(by_role.get(role, []))
                                for role in ROLES},
            "jobs": len(jobs),
            "job_affinity": {job["job_id"]: job["source_worker_id"]
                             for job in jobs},
            "targets": sorted({job["canonical_target_id"] for job in jobs}),
            "note": ("this instance binds no Job and configures no execution "
                     "capacity; it serves a real idle scheduler and publisher "
                     "over empty stores, and a worker, a Work, a declared "
                     "base, a canonical target and a producer are supplied "
                     "together when a Job is created"
                     if not jobs and not workers_of(document) else
                     "this instance configures a pool and binds no Job; a "
                     "Work, a declared base and a canonical target are "
                     "supplied when a Job is created" if not jobs else
                     "each Job is bound to one producer, one Work, one declared "
                     "base and one canonical target; Jobs sharing a canonical "
                     "target are serialized at integration by the accepted "
                     "composition, so this is configured capacity rather than "
                     "a concurrency guarantee")}


# -- the Authority ------------------------------------------------------------


def principals_for(places, document, *, opener=None):
    """Who each configured endpoint resolves to, CREATING NOTHING.

    [F1] requires the emitted configuration to be validated before anything
    durable happens, and a configuration carries principals -- so they have to
    be derivable without a store this run may end up refusing to build.

    They are. `Authority.principal_of` is a READ that writes nothing: it answers
    a binding when the deployment has made one, and the Authority's own default
    otherwise. So an Authority that already exists is ASKED, because an operator
    may have bound an endpoint; one that does not exist has no bindings to ask
    about, and `principal_for_endpoint` -- the Authority package's own function,
    not a second opinion about identity -- is the answer by construction.
    """
    from baton_v12.authority.principals import principal_for_endpoint

    wanted = sorted({one["participant"] for one in workers_of(document)}
                    | set(document["receipt_participants"].values())
                    | {document["integration_profile"]["integrator_participant"]})
    if not Path(places["authority_store"]).exists():
        return {who: principal_for_endpoint(who) for who in wanted}
    try:
        authority = _authority(places, document["authority_uuid"], opener=opener)
    except Exception as failure:                             # noqa: BLE001
        # An Authority already here under another uuid is an operator-facing
        # fact about this root, not a package exception to leak.
        raise BootstrapRefusal(
            "the Authority already at " + places["authority_store"]
            + " will not answer for this document: " + str(failure)
            + ". Nothing was changed.")
    try:
        return {who: authority.principal_of(who) for who in wanted}
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()


def _authority(places, uuid, *, opener=None):
    """Open this deployment's own Authority, creating it only if it is absent."""
    if opener is not None:
        return opener(places["authority_store"], uuid)
    from baton_v12.authority import Authority

    if Path(places["authority_store"]).exists():
        return Authority.open(places["authority_store"],
                              expected_authority_uuid=uuid)
    Path(places["authority_store"]).parent.mkdir(parents=True, exist_ok=True)
    return Authority.create(places["authority_store"], authority_uuid=uuid)


def _compose(authority, document, *, stream):
    """Identities, Works, routes and grants -- derived, and repeatable.

    A Work that already exists bound as this document binds it is left exactly
    as it is. One bound DIFFERENTLY is REFUSED: where a Job's line and target
    live is not something a setup command may quietly move.
    """
    created = []
    integrator = document["integration_profile"]["integrator_participant"]
    for worker in workers_of(document):
        route = ROUTES[worker["role"]]
        authority.add_route_handler(route, worker["participant"])
        print("route %-14s -> %s" % (route, worker["participant"]), file=stream)

    # NO JOB, NO WORK, NO GRANT. OWNER-FRESH-INSTALL-20260916.md: "Do not
    # create placeholder Work, Jobs or per-Work grants to satisfy the old
    # composition validator." A grant is made in a bound Work's OWN scope, so
    # an instance with no Work has no scope to grant anything in; the receipt
    # participants and the integrator are configured and granted when a Job
    # brings a Work with it.
    if not jobs_of(document):
        print("job   none; no Work, grant or placeholder was created",
              file=stream)
    for job in jobs_of(document):
        held_work = _work(authority, job["work_id"])
        if held_work is None:
            authority.create_work(job["work_id"], ROUTES["implementation"],
                                  operation_id="bootstrap-" + job["job_id"],
                                  contract="v12-assignment-1")
            created.append(job["work_id"])
            held_work = _work(authority, job["work_id"])
            print("work  %-14s created on %s"
                  % (job["work_id"], ROUTES["implementation"]), file=stream)
        else:
            print("work  %-14s already exists; left alone"
                  % job["work_id"], file=stream)
        scope = held_work["scope"]
        for name, capability in GRANTS.items():
            authority.grant_capability(document["receipt_participants"][name],
                                       capability, scope=scope)
        authority.grant_capability(integrator, INTEGRATOR_GRANT, scope=scope)
        print("grant %-14s %s in its own scope"
              % (job["work_id"], "/".join(sorted(GRANTS.values())
                                          + [INTEGRATOR_GRANT])), file=stream)
    _canonical_target(authority, document, stream=stream)
    return created


def _canonical_target(authority, document, *, stream):
    """THE REVISION THE FIRST PROPOSAL IS OFFERED AGAINST, established here.

    W197661, found by running the installed lifecycle to its first publication.
    `integration.driver.publish_candidate` compares the worker's declared base
    with `Authority.canonical_target()`, and nothing in a fresh deployment ever
    set it -- so it answered its own placeholder, `"base-1"`, and every first
    publication was refused with "the Authority's canonical target is a full
    lower-case object name ...; this is 'base-1'". The stage deferred
    `conclude` and asked again forever: a runtime that finished, a manager that
    looked well, and nothing that said why. That is the same shape as the
    incident this Work came from.

    `set_policy` ALREADY EXISTS for the other end of the line -- integration
    advances the target with it when a proposal is accepted. What was missing
    is the FIRST value, and a deployment that names `line_declared_base` per
    Job is a deployment that has already been told it.

    ONE VALUE, AND THE CONSTRAINT IS HELD IN PREFLIGHT. The policy is a single
    revision, so Jobs declaring DIFFERENT bases cannot all be expressed --
    which `held` refuses, before this module opens a writable Authority or
    composes one route, Work or grant. Review200179 [R2] found that refusal
    here instead, which left partial Authority state behind. By the time this
    runs the document has already been proved to name exactly one base.

    REPEATABLE, AND IT NEVER MOVES A TARGET THAT HAS ADVANCED. A deployment
    whose Authority already holds a real target keeps it: re-running setup
    after integration accepted a proposal must not rewind the line.
    """
    jobs = jobs_of(document)
    if not jobs:
        return
    declared = sorted({job["line_declared_base"] for job in jobs})
    # THE PLACEHOLDER BELONGS TO THE ACCESSOR THAT FALLS BACK TO IT, and is
    # read from `Core` rather than restated here: a second copy of the string
    # is how the two would drift. Taken from the CLASS rather than from the
    # instance, because a double standing in for an Authority answers
    # `canonical_target()` and need not carry its constants.
    from baton_v12.authority.core import UNESTABLISHED_TARGET

    held = authority.canonical_target()
    if held != UNESTABLISHED_TARGET:
        if len(declared) == 1 and declared[0] == held:
            print("target%-15s already established; left alone" % "", file=stream)
        else:
            print("target%-15s %s already established and NOT moved; this "
                  "setup declares %s" % ("", held, ", ".join(declared)),
                  file=stream)
        return
    if len(declared) != 1:
        # UNREACHABLE THROUGH `prepare`, and it is a refusal rather than an
        # assumption: this function is also importable, and a caller that
        # skipped the preflight must not silently establish one Job's base.
        raise BootstrapRefusal(
            "an Authority holds ONE canonical target and this deployment's "
            "Jobs declare %d different bases (%s); this is proved in preflight "
            "and reaching it here means the document was never held"
            % (len(declared), ", ".join(declared)))
    authority.set_policy("canonical_target", declared[0])
    print("target%-15s %s established from line_declared_base"
          % ("", declared[0]), file=stream)


def _work(authority, work_id):
    try:
        return authority.project_work(work_id)
    except Exception:                                        # noqa: BLE001
        return None


# -- the command --------------------------------------------------------------


def commands(places, configured):
    """The exact exports `just start` needs, ready to paste."""
    return "\n".join([
        'export BATON_V12_JOB_STORE="%s"' % places["job_store"],
        'export BATON_V12_CONTROL_STORE="%s"' % places["control_store"],
        'export BATON_V12_AUTHORITY_UUID="%s"' % configured["authority_uuid"],
        'export BATON_V12_STAGE_EXECUTION_CONFIG="%s"' % places["configuration"]])


def record_of(document):
    """What this bootstrap prepared, keyed by Job and independent of schema.

    [F2]: comparison used to read the EMITTED configuration, where a `/1`
    document has no Job identifiers at all -- so a `/2` deployment repeated as
    `/1` compared `None` against the previous Job keys, matched nothing, dropped
    a Job and rebound the other one, and reported success. What is compared now
    is this module's OWN record, written in one shape whichever variant is
    emitted, so a one-to-many or many-to-one repeat is comparable at all.
    """
    return {"schema": RECORD_SCHEMA,
            "authority_uuid": document["authority_uuid"],
            "bindings": {job["job_id"]: {
                "work_id": job["work_id"],
                "line_declared_base": job["line_declared_base"],
                "canonical_target_id": job["canonical_target_id"],
                "source_worker_id": job["source_worker_id"]}
                for job in jobs_of(document)}}


def _previous(places):
    """This root's own record: absent, unreadable, or what it says.

    UNREADABLE IS NOT ABSENT. A corrupt record, or one this helper did not
    write, means the identity of whatever is already configured here is
    UNKNOWN -- not proven to be nothing -- and overwriting unknown state is
    exactly what a repeated setup must not do.
    """
    place = Path(places["record"])
    emitted = Path(places["configuration"])
    try:
        held = json.loads(place.read_bytes())
    except FileNotFoundError:
        if emitted.exists():
            return {"unreadable": True,
                    "detail": "there is a configuration at " + str(emitted)
                              + " but no record at " + str(place)
                              + ", so what it binds cannot be established"}
        return None
    except (ValueError, OSError) as failure:
        return {"unreadable": True,
                "detail": "the record at " + str(place) + " could not be read ("
                          + type(failure).__name__ + ")"}
    problem = _malformed_record(held, place)
    if problem is not None:
        return {"unreadable": True, "detail": problem}
    drifted = _drifted(places, held)
    if drifted is not None:
        return {"unreadable": True, "detail": drifted}
    return held


_BINDING = ("work_id", "line_declared_base", "canonical_target_id",
            "source_worker_id")


def _malformed_record(held, place):
    """Why this is not custody evidence, or None.

    [G1]: the schema label alone was checked, so a recognizable record whose
    binding was `{}` said nothing about that Job's prior Work, base, target or
    producer -- and `conflicts`, which compared only the members it FOUND,
    authorized every one of them to be replaced. A record that does not say
    what is bound is not evidence about what is bound.
    """
    if type(held) is not dict or held.get("schema") != RECORD_SCHEMA:
        return ("the record at " + str(place) + " is not a " + RECORD_SCHEMA
                + " document")
    uuid = held.get("authority_uuid")
    if type(uuid) is not str or len(uuid) != 32:
        return ("the record at " + str(place) + " names no readable Authority")
    bindings = held.get("bindings")
    # AN EMPTY MAPPING IS AN ANSWER NOW, AND [G1]'s FAULT IS NOT.
    # OWNER-FRESH-INSTALL-20260916.md: an installed instance binds zero Jobs,
    # so "this root holds no bindings" is a thing a record has to be able to
    # SAY. What [G1] found remains refused below: a record that names a Job and
    # then does not say that Job's Work, base, target or producer is not
    # evidence about it, and `conflicts` would authorize every one of them to
    # be replaced.
    if type(bindings) is not dict:
        return ("the record at " + str(place) + " names its bindings as "
                + type(bindings).__name__ + " rather than a mapping, so what "
                "this root holds cannot be established")
    for job_id, binding in bindings.items():
        if type(job_id) is not str or not job_id:
            return ("the record at " + str(place) + " names a Job that is not "
                    "an identifier")
        if type(binding) is not dict:
            return ("the record at " + str(place) + " binds job " + repr(job_id)
                    + " to " + type(binding).__name__ + " rather than a document")
        absent = [name for name in _BINDING if type(binding.get(name)) is not str
                  or not binding[name]]
        if absent:
            return ("the record at " + str(place) + " does not say job "
                    + repr(job_id) + "'s " + ", ".join(absent))
    return None


def _drifted(places, held):
    """Why the configuration beside this record does not match it, or None.

    [H1]: this used to read the emitted document through a hand-written partial
    projection of my own -- one that chose its representation from the
    truthiness of `job_bindings` rather than from the schema, and that dropped
    the review Work in both variants and the producer identity in `/1`. So a
    changed review Work, an unsupported schema and a changed sole producer all
    passed. A second, more permissive copy of the deployment contract is exactly
    what this must not become, and this was one.

    THE ACCEPTED VALIDATOR RESOLVES IT INSTEAD. `held_configuration` already
    reads `/1` and `/2` through `_held_bindings`, requires the implementation and
    review Works to match, and DERIVES `/1`'s `source_worker_id` from its sole
    producer -- so its normalized `job_bindings` is the one shape to compare,
    and a document it refuses is one whose meaning cannot be established at all.
    """
    from baton_v12.contracts import ContractRefusal
    from tools import stage_execution

    place = Path(places["configuration"])
    try:
        emitted = json.loads(place.read_bytes())
    except FileNotFoundError:
        return ("there is a record at " + str(places["record"]) + " but no "
                "configuration at " + str(place))
    except (ValueError, OSError) as failure:
        return ("the configuration at " + str(place) + " could not be read ("
                + type(failure).__name__ + "), so what it binds is unknown")
    if type(emitted) is not dict:
        return ("the configuration at " + str(place)
                + " is not one deployment document")
    try:
        normalized = stage_execution.held_configuration(emitted)
    except ContractRefusal as refusal:
        return ("the configuration at " + str(place) + " is not one the manager "
                "would accept (" + refusal.message + "), so what it binds is "
                "unknown")
    if normalized["authority_uuid"] != held["authority_uuid"]:
        return ("the configuration at " + str(place) + " names Authority "
                + repr(normalized["authority_uuid"]) + " and its record names "
                + repr(held["authority_uuid"]))

    bound = {one["job_id"]: one for one in normalized["job_bindings"]}
    recorded = held["bindings"]
    if None in bound:
        # A `/1` deployment binds one Job and names no identifier for it, so
        # its record must name exactly one too.
        if len(recorded) != 1:
            return ("the configuration at " + str(place) + " binds one Job and "
                    "its record names " + str(len(recorded)))
        pairs = [(list(recorded.values())[0], bound[None], None)]
    else:
        if set(bound) != set(recorded):
            return ("the configuration at " + str(place) + " binds "
                    + repr(sorted(bound)) + " and its record names "
                    + repr(sorted(recorded)))
        pairs = [(recorded[job_id], bound[job_id], job_id) for job_id in bound]
    for previous, binding, job_id in pairs:
        named = "" if job_id is None else "job " + repr(job_id) + "'s "
        # ONE AXIS, NOT TWO. A reversal probe showed that comparing
        # `review_work_id` as well proves nothing: `held_configuration` has
        # already refused any document whose two Works differ, so after
        # validation the second comparison is the first one again. A changed
        # review Work is caught -- by the validator, above -- rather than here.
        if binding["job_work_id"] != previous["work_id"]:
            return ("the configuration at " + str(place) + " binds "
                    + named + "job_work_id " + repr(binding["job_work_id"])
                    + " and its record says " + repr(previous["work_id"]))
        for member in ("line_declared_base", "canonical_target_id",
                       "source_worker_id"):
            if binding[member] != previous[member]:
                return ("the configuration at " + str(place) + " binds "
                        + named + member + " " + repr(binding[member])
                        + " and its record says " + repr(previous[member]))
    return None


# WHAT AN INSTALLATION DERIVED AND A LATER REPEAT MUST NOT LOSE.
# Review 2026-09-16T23-16-06Z [P2]: the destination branch runs
# `workspace_bound`, `repositories_bound` and `storage_bound`; the one-operand
# branch does not. So the documented reconfiguration returned zero and quietly
# removed `integration_workspace` from the emitted configuration -- the
# selector, the runtime and the identity were all unchanged, and the
# deployment had stopped naming where integration works.
DERIVED_PATHS = ("integration_target", "integration_workspace")
_DERIVED_WORKER_PATHS = ("workspace_storage", "nominated_source")


def dropped_selections(places, configured):
    """Everything the emitted configuration here names and this one does not.

    A REPEAT PRESERVES. `conflicts` already refuses a CHANGED binding; this is
    the other half, and it is the half an installed instance actually needs:
    a member that simply stops being named is not thereby unselected, for
    exactly the reason a Job that stops being named is not unconfigured.
    """
    place = Path(places["configuration"])
    try:
        held = json.loads(place.read_bytes())
    except (FileNotFoundError, ValueError, OSError):
        return []
    if type(held) is not dict:
        return []
    found = [name for name in DERIVED_PATHS
             if held.get(name) and not configured.get(name)]
    previous = {one.get("worker_id"): one.get("deployment") or {}
                for one in held.get("workers") or [] if type(one) is dict}
    for one in configured.get("workers") or []:
        was = previous.get(one.get("worker_id"))
        if type(was) is not dict:
            continue
        deployment = one.get("deployment") or {}
        found += ["workers[" + str(one.get("worker_id")) + "]." + name
                  for name in _DERIVED_WORKER_PATHS
                  if was.get(name) and not deployment.get(name)]
    return sorted(found)


def conflicts(places, record):
    """What this root already holds that this document would change.

    A repeated bootstrap must PRESERVE state. Where a Job's Work, declared base
    or canonical target lives is not something a setup command may quietly
    move, and a Job that simply STOPS being named is not thereby unconfigured:
    its Work, its grants and whatever it has already produced are still there.
    """
    held = _previous(places)
    if held is None:
        return []
    if held.get("unreadable"):
        return [held["detail"] + ". Nothing here overwrites state it cannot "
                "identify."]
    found = []
    if held.get("authority_uuid") != record["authority_uuid"]:
        found.append("this root is already bound to Authority "
                     + repr(held.get("authority_uuid")) + " and this document "
                     "names " + repr(record["authority_uuid"]))
    for job_id, binding in held["bindings"].items():
        if job_id not in record["bindings"]:
            found.append("job %r is already prepared here and this document "
                         "does not name it; a Job that stops being named is "
                         "not thereby unconfigured" % job_id)
            continue
        # EVERY MEMBER, not only the ones this record happens to carry. [G1]:
        # iterating what was found meant an empty binding compared nothing and
        # authorized everything. `_malformed_record` has already refused a
        # record that does not carry all four.
        for member in _BINDING:
            if record["bindings"][job_id].get(member) != binding.get(member):
                found.append("job %r is already bound with %s %r and this "
                             "document names %r"
                             % (job_id, member, binding.get(member),
                                record["bindings"][job_id].get(member)))
    return found


def _publish(place, document):
    """Atomically, so an interrupted write cannot turn a known configuration
    into partial JSON."""
    temporary = Path(str(place) + ".tmp")
    temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, place)


def validated(configured):
    """The emitted configuration, held to the rules the MANAGER will hold it to.

    [F1]: nothing here validated what it wrote. The nested worker `deployment`
    merely had to be nonempty, so a document missing twenty-two required worker
    members -- adapter, runtime profile, credential selection, workload,
    workspace, launch contract, review route -- was written out and an Authority
    composed for it, and the refusal arrived from `held_configuration` later,
    with durable state already made.

    THE ACCEPTED VALIDATOR IS CALLED, not reimplemented. A second, more
    permissive copy of the deployment contract is exactly what this must not
    become: the rules have one owner, and a helper that agreed with itself
    would prove nothing about what the manager accepts.
    """
    from baton_v12.contracts import ContractRefusal
    from tools import stage_execution

    try:
        stage_execution.held_configuration(configured)
    except ContractRefusal as refusal:
        raise BootstrapRefusal(
            "the deployment this document describes is not one the manager "
            "would accept, so nothing was prepared: " + refusal.message
            + ". Each worker's `deployment` member is the single-worker launch "
              "document v12/python/DEPLOYMENT.md specifies; this helper fills "
              "in only participant, principal, authority_store, authority_uuid "
              "and launch_role, and names the rest as yours to select.")
    return configured


def without_installer_members(document):
    """The document the MANAGER'S rules are applied to.

    [R1]: `repository_source` is the installer's operand. Carried into the
    emitted `stage_execution` document it is refused by that closed schema --
    so a perfectly valid input composed an Authority and then exited 2 on the
    validator. It is stripped here, once, rather than remembered at each use.
    """
    return {name: value for name, value in document.items()
            if name not in INSTALLER_ONLY}


def admissible_bases(places, document, *, opener=None):
    """Which declared bases this root may admit, decided BEFORE any effect.

    W202663 owner212383, review212328's bounded amendment. The distinct-base
    count rule lived in the pure `held` and could not tell RETAINED bindings
    from NEW ones, so a root whose target had legitimately ADVANCED (the
    approved direct-target finalization) could never admit a new Job: the
    preserved completed binding carries its historical base, the new binding
    carries the advanced one, and counting refused both together.

    THE SPLIT, on validated PERSISTED evidence and never an input assertion:

    - retained bindings are the ones this root's own persisted record names;
      `conflicts` has ALREADY refused their mutation or omission before this
      runs, so their historical bases are exactly what this root recorded;
    - a FRESH root (no persisted record, no retained binding) keeps the
      first-establishment rule byte for byte: exactly ONE distinct base
      across the whole document, refused otherwise before the first proposal;
    - an ESTABLISHED root admits NEW bindings only when they agree on ONE
      base and that base equals the Authority's CURRENT canonical target,
      read WITHOUT writing -- a stale new base, an unreadable store, or a
      root whose record exists while its target was never established all
      refuse by name.

    IT RUNS AFTER `conflicts` AND BEFORE ANYTHING DURABLE, so the module's
    no-effects-on-refusal promise is unchanged. It waives nothing: pool
    live-allocation checks, `dropped_selections` and every later validation
    stand exactly as they were.
    """
    jobs = jobs_of(document)
    if not jobs:
        return
    # THE CALLER'S LAYOUT MAY BE `tools.instance`'s (the install path hands
    # that one to `prepare_repositories`), which derives the same store and
    # record paths but not this module's `configuration` key -- and
    # `_previous` reads it. One root, one layout: recompute this module's own
    # from the document's state_root, which both callers have already set.
    places = layout(document["state_root"])
    held = _previous(places)
    retained = (set() if held is None or held.get("unreadable")
                else set(held.get("bindings") or {}))
    fresh = [job for job in jobs if job["job_id"] not in retained]
    if not retained:
        declared = sorted({job["line_declared_base"] for job in jobs})
        if len(declared) > 1:
            raise BootstrapRefusal(
                "this deployment cannot be prepared: an Authority holds ONE "
                "canonical target and this fresh deployment's Jobs declare "
                + str(len(declared)) + " different bases ("
                + ", ".join(declared) + "); the first publication compares a "
                "worker's declared base against that one value, so a "
                "deployment that cannot express its own bases is refused "
                "here rather than at the first proposal")
        return
    if not fresh:
        return
    # AN ESTABLISHED ROOT ADMITS NEW BINDINGS AT THEIR OWN DECLARED BASES.
    # Owner 2026-09-20T14:57:48Z (W202663, the generic-reference ruling): a
    # binding's declared base is OPAQUE reference metadata carried to the
    # agents that interpret it -- "take commit X, make changes, offer PR" --
    # and the coordinator neither compares it against the Authority's
    # canonical target nor forces every new binding to one value.
    # Independent Jobs run concurrently from explicit accepted bases, and
    # an accepted RESULT reaches a successor as an explicit input rather
    # than through a globally enforced Git base. The two equality rules
    # this branch used to apply (one base across new Jobs; that base equal
    # to the current canonical target) were the selected-core
    # interpretation that ruling explicitly supersedes. The FRESH-root
    # one-base rule above stays: a fresh deployment's first publication
    # still compares a worker's declared base against the one canonical
    # target the integration flow establishes, and the PR flow never
    # reaches that comparison. Retained-binding conflict checks stand
    # exactly as they were.
    for job in fresh:
        if (type(job["line_declared_base"]) is not str
                or not job["line_declared_base"]):
            raise BootstrapRefusal(
                "this deployment cannot be prepared: a new Job's "
                "line_declared_base is an explicit nonempty reference; the "
                "coordinator carries it to the Job's agents verbatim")


def prepare(document, *, stream=sys.stdout, opener=None, installing=False):
    """Prove everything, then compose. In that order, and the order is the point.

    NOTHING DURABLE HAPPENS UNTIL EVERY CHECK HAS PASSED: the input document,
    the derived identities, the emitted configuration under the manager's own
    rules, this root's existing record, and the checkout boundary. Principals
    are derivable without building anything -- `principal_of` is a read, and an
    Authority that does not exist yet has no bindings to ask about -- so the
    whole configuration can be proved before a directory is made.
    """
    document = held(without_installer_members(document))
    places = layout(document["state_root"])

    tree = checkout()
    resolved = os.path.realpath(document["state_root"])
    if resolved == tree or resolved.startswith(tree.rstrip("/") + "/"):
        raise BootstrapRefusal(
            "the state root at " + document["state_root"] + " is inside the "
            "checkout at " + tree + "; mutable deployment state belongs "
            "outside the working tree, and `stage_execution` would refuse this "
            "deployment for the same reason after it had been created.")

    # THE IDENTITY IS THIS INSTANCE'S, AND IT IS RESOLVED BEFORE ANYTHING IS
    # COMPARED. A root that already has a record keeps the Authority that
    # record names; a fresh one is given a new identity here, which is what
    # makes two installations two instances rather than two names for one.
    uuid, generated = identity(places)
    document = dict(document, authority_uuid=uuid)
    print("authority %-14s %s" % (uuid[:8] + "...",
                                  "generated for this instance" if generated
                                  else "reused from this root's record"),
          file=stream)

    # THE EXISTING ROOT IS SETTLED FIRST, before this even READS an Authority.
    # [F2] asks for exactly that: uncertain existing state must be refused
    # before anything is opened, and opening a store whose uuid disagrees would
    # otherwise surface the Authority's own refusal instead of this one.
    record = record_of(document)
    found = conflicts(places, record)
    if found:
        raise BootstrapRefusal(
            "this root already holds a different deployment and nothing was "
            "changed: " + "; ".join(found) + ". A repeated bootstrap preserves "
            "what is there; if you mean a different deployment, give it its own "
            "state_root.")
    # THE DECLARED BASES, judged against what this root PERSISTED and what
    # its Authority established -- after `conflicts` proved the retained
    # bindings byte-exact, still before anything durable. W202663
    # owner212383; the rule that lived in `held` moved here so an
    # incremental preparation over an advanced target is expressible at all.
    admissible_bases(places, document, opener=opener)

    principals = principals_for(places, document, opener=opener)
    configured = validated(configuration(document, principals))

    # AND WHAT THIS ROOT IS ALREADY CONFIGURED WITH IS NOT SILENTLY LOST.
    # [P2]: the installation DERIVES the repository and storage paths under the
    # destination; a later one-operand repeat composes from the input alone and
    # dropped them, returning zero.
    lost = dropped_selections(places, configured)
    if lost:
        raise BootstrapRefusal(
            "this root is already configured with " + ", ".join(lost)
            + " and this document does not name " + ("it" if len(lost) == 1
                                                     else "them")
            + ". A repeated bootstrap preserves what is there, and a selection "
              "that stops being named is not thereby unselected -- an "
              "installation DERIVES these under its destination, and composing "
              "from the input alone would quietly unconfigure where "
              "integration works. Copy the current values out of "
            + places["configuration"] + " into your input document, or install "
              "a new destination if you mean a different deployment. Nothing "
              "was changed.")

    # -- and only now -----------------------------------------------------
    Path(places["state_root"]).mkdir(parents=True, exist_ok=True)
    # THE IDENTITY IS PERSISTED BEFORE THE AUTHORITY IT NAMES IS CREATED, so a
    # store that exists is always one this root can still account for.
    uuid = persist_identity(places, uuid)
    Path(places["deployment_state"]).mkdir(parents=True, exist_ok=True)
    Path(places["authority_store"]).parent.mkdir(parents=True, exist_ok=True)
    authority = _authority(places, document["authority_uuid"], opener=opener)
    try:
        created = _compose(authority, document, stream=stream)
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()

    _publish(Path(places["record"]), record)
    _publish(Path(places["configuration"]), configured)

    print("configuration " + places["configuration"], file=stream)
    print("capacity      " + json.dumps(capacity(document), sort_keys=True),
          file=stream)
    print("no Job was submitted and nothing was executed", file=stream)
    if not installing:
        # THE OPERANDS ARE THE SOURCE-RUN FORM'S. An installed instance carries
        # all four in its own selector, so telling an operator who is
        # installing to export them and run `just start` from the checkout
        # would be advice for the deployment they did not ask for.
        print("\nNow export these and run `just start` from v12/:\n",
              file=stream)
        print(commands(places, configured), file=stream)
    return {"places": places, "configuration": configured,
            "principals": principals, "created_works": created,
            "record": record, "capacity": capacity(document),
            "authority_uuid": uuid, "authority_generated": generated}


# THE REPOSITORY git, named once. It is the host's -- this distribution
# bundles a Python runtime, not an operating system -- and every invocation
# below goes through `_ran` so a caller can watch, stub or refuse them.
REPOSITORY_COMMAND = "git"
# What the owner names to have repositories prepared at all. Absent, nothing is
# cloned and the deployment is installed without them: "missing choices do not
# prevent building and testing the generic owner-run command"
# (OWNER-STANDALONE-INTERFACE-20260916.md).
# The operand name an operator sees when a refusal has to name the way out.
SOURCE_OPERAND = "--repository-source / --no-repositories"


def _ran(runner, argv, what):
    """One repository-tool invocation, refused by name when it fails."""
    import subprocess

    runner = subprocess.run if runner is None else runner
    done = runner(list(argv), capture_output=True, text=True, timeout=1800)
    if done.returncode != 0:
        raise BootstrapRefusal(
            what + " failed (" + " ".join(argv) + "):\n"
            + (done.stderr or done.stdout or "").strip()[-600:])
    return (done.stdout or "").strip()


def _safe_name(worker_id):
    """One path component, and nothing that could leave the destination.

    [R2]: a `worker_id` of `x/../../../escape` planned a clone OUTSIDE the
    destination. A worker id is a name, not a path.
    """
    said = str(worker_id)
    if not said or said in (".", "..") or "/" in said or "\\" in said \
            or said.startswith("-") or "\0" in said:
        raise BootstrapRefusal(
            "worker_id " + repr(worker_id) + " is not a name this bootstrap "
            "can make a repository directory from; it must be one path "
            "component, and a repository is prepared under the destination or "
            "not at all")
    return said


def repository_plan(document, places):
    """Which repositories this deployment needs, and where they go.

    THREE ROLES, THREE REPOSITORIES, all under the destination:
    `integration_target` is what a reconciled result is imported into, the
    workspace is integration's own preparation area, and each worker has its
    own nominated source. `reconciliation._prove_isolation` refuses if any two
    of them turn out to be ONE repository -- by resolved common directory and
    by resolved device and inode -- so each is a separate clone rather than a
    worktree or a hardlinked copy.
    """
    root = Path(places["repository"])
    planned = [("target", str(root / "target.git"), True),
               ("workspace", str(root / "workspace"), False)]
    for worker in document.get("workers") or []:
        if type(worker) is dict and worker.get("worker_id"):
            name = _safe_name(worker["worker_id"])
            planned.append(("source-" + name, str(root / ("source-" + name)),
                            False))
    inside = os.path.realpath(places["destination"])
    for name, place, _mirror in planned:
        held = os.path.realpath(place)
        if held != inside and not held.startswith(inside.rstrip("/") + "/"):
            raise BootstrapRefusal(
                "the " + name + " repository would be at " + place
                + ", which resolves to " + held + " -- outside the destination "
                "at " + inside + ". Everything this deployment owns lives under "
                "its own destination.")
    return planned


def repositories_agree(document, places):
    """What the configuration SELECTS must be what this prepares. [R4]

    The paths are fixed by the destination, and an input that names a
    different target, workspace or source is not quietly overridden and not
    quietly prepared elsewhere: it is REFUSED, before any effect, naming both
    sides. Owner isolation puts every one of them under the destination, so an
    external selection and `repository_source` cannot both be honoured.
    """
    planned = {name: place for name, place, _ in repository_plan(document, places)}
    disagreements = []
    named = document.get("integration_target")
    if isinstance(named, str) and named and named != planned["target"]:
        disagreements.append(("integration_target", named, planned["target"]))
    workspace = document.get("integration_workspace")
    if isinstance(workspace, str) and workspace not in (
            planned["workspace"], places["repository"]):
        disagreements.append(("integration_workspace", workspace,
                              planned["workspace"]))
    for worker in document.get("workers") or []:
        if type(worker) is not dict or type(worker.get("deployment")) is not dict:
            continue
        source = worker["deployment"].get("nominated_source")
        wanted = planned["source-" + _safe_name(worker["worker_id"])]
        if isinstance(source, str) and source and source != wanted:
            disagreements.append(
                ("workers[" + str(worker["worker_id"]) + "].nominated_source",
                 source, wanted))
    for worker in document.get("workers") or []:
        if type(worker) is not dict or type(worker.get("deployment")) is not dict:
            continue
        named = worker["deployment"].get("workspace_storage")
        if not isinstance(named, str) or not named:
            continue
        held = os.path.realpath(named)
        inside = os.path.realpath(places["destination"])
        if held != inside and not held.startswith(inside.rstrip("/") + "/"):
            disagreements.append(
                ("workers[" + str(worker.get("worker_id"))
                 + "].workspace_storage", named,
                 os.path.join(places["destination"], "workers",
                              str(worker.get("worker_id")), "storage")))
    if disagreements:
        raise BootstrapRefusal(
            "this input asks for repositories to be prepared AND names "
            "different ones:\n"
            + "\n".join("  " + name + " is " + given + ", and this bootstrap "
                         "prepares " + wanted
                         for name, given, wanted in disagreements)
            + "\nNothing here silently overrides a selection or prepares a "
              "repository nobody will use. Install with --no-repositories to "
              "keep your own paths, or drop the paths to have them prepared.")
    return planned


def repository_source(named=None):
    """Where this bootstrap clones the deployment's repositories FROM.

    OWNER-VERSION-STAMP-20260916.md: the repository that contains this
    distribution's own `v12/justfile`, found from this file rather than from
    the caller's working directory, which is where somebody happened to be
    standing. An operand overrides it for a developer installing from another
    checkout.
    """
    from tools import build_stamp

    if named:
        return str(named)
    found = build_stamp.checkout()
    return str(found) if found else None


def prepare_repositories(document, places, *, runner=None, stream=sys.stdout,
                         wait=120.0, source=None):
    """Create this deployment's independent repositories, then PROVE them.

    OWNER-STANDALONE-INTERFACE-20260916.md: "Finish the agreed two-argument
    bootstrap: it creates the bundled distro, databases and independent
    repositories." The owner invokes this; nothing here runs on an implementer's
    behalf, and the checks afterwards are the ones
    OPERATOR-INDEPENDENT-REPOSITORY.md spells out, applied by the command that
    did the work rather than pasted by hand.

    PREPARED ONCE, like everything else under a destination. An existing path
    at any planned repository is refused and left exactly as it is.
    """
    if source not in (None, "", {}):
        # STRUCTURE BEFORE EFFECTS. [R2]: a source-only input made two clones
        # and only then hit "this input does not supply workers, jobs, ...".
        # The whole document is proved first -- by the same rules `prepare`
        # applies -- so a refusal here has changed nothing.
        held(without_installer_members(document))
        # AND THE DECLARED BASES, review212438 [R1]: when the distinct-base
        # count rule moved out of the pure `held` into `admissible_bases`,
        # THIS caller kept only `held` -- so on the install path, which runs
        # before `prepare`, a fresh multi-base input created the destination
        # and reached the clone runner before anything refused it. The same
        # store-aware rule runs here now, before the mkdir below: a fresh
        # destination has no persisted record, so this is the pure one-base
        # first-establishment refusal, with nothing changed.
        admissible_bases(places, document)
        repositories_agree(document, places)
        custody(places, places["destination"])
    if source in (None, "", {}):
        print("repositories  not prepared: no source checkout was found or "
              "named, so the deployment has no target, workspace or worker "
              "sources yet and will schedule without reconciling",
              file=stream)
        return None
    if type(source) is not str:
        raise BootstrapRefusal(
            "the repository source is " + repr(source) + "; it names the "
            "checkout every one of this deployment's own repositories is "
            "cloned from")

    planned = repository_plan(document, places)
    Path(places["destination"]).mkdir(parents=True, exist_ok=True)
    # SERIALIZED WITH EVERY OTHER PREPARATION OF THIS DESTINATION, and the
    # existence checks are inside that lock: two bootstraps preparing one
    # destination would otherwise each find the repositories absent.
    with serialized(places, wait):
        # AGAIN, HOLDING THE LOCK. [R2 remainder]: custody was asked before the
        # wait, so a foreign distro, selector or justfile that appeared while
        # this attempt queued for the lock was not seen -- and five clones went
        # ahead into a destination somebody else had taken. The answer that
        # matters is the one taken immediately before the effects.
        custody(places, places["destination"])
        repositories_agree(document, places)
        for name, place, _mirror in planned:
            if os.path.lexists(place):
                raise BootstrapRefusal(
                    "there is already something at " + place + ", which this "
                    "deployment's " + name + " repository would be. Nothing "
                    "here replaces one; prepare a new destination.")
        Path(places["repository"]).mkdir(parents=True, exist_ok=True)
        return _cloned(document, places, planned, source, runner, stream)


def _cloned(document, places, planned, source, runner, stream):
    """The clones themselves, with what was made reported when one fails.

    [R2]: a failure part-way through leaves what the earlier commands made.
    Removing it would be destroying repository data this command created but
    cannot re-derive; naming it is what lets an operator decide.
    """
    made = []
    target = planned[0][1]
    try:
        return _cloning(document, places, planned, source, runner, stream, made)
    except BootstrapRefusal as refusal:
        if made:
            raise BootstrapRefusal(
                str(refusal) + "\n\nWhat this attempt had already prepared is "
                "STILL THERE and was not removed: "
                + ", ".join(one["path"] for one in made)
                + ". Repository data this command cannot re-derive is not "
                "something it deletes on the way out; remove them yourself, or "
                "prepare a new destination, before retrying.")
        raise


def _cloning(document, places, planned, source, runner, stream, made):
    target = planned[0][1]
    for name, place, mirror in planned:
        # THE TARGET COMES FROM THE OWNER'S SOURCE; EVERY OTHER ROLE IS CLONED
        # FROM THE TARGET, so each has its own object store. `--no-local`
        # forces an object-by-object copy rather than hardlinks into another
        # repository, which is what keeps the identities distinct.
        argv = [REPOSITORY_COMMAND, "clone", "--no-local"]
        argv += ["--mirror", str(source)] if mirror else [target]
        argv += [place]
        _ran(runner, argv, "preparing this deployment's " + name + " repository")
        made.append({"role": name, "path": place})

    held = repositories_proved(document, places, planned, runner=runner)
    print("repositories  " + str(len(made)) + " prepared under "
          + places["repository"] + ": " + ", ".join(one["role"] for one in made),
          file=stream)
    return {"source": str(source), "prepared": made, "proved": held}


def repositories_proved(document, places, planned, *, runner=None):
    """Every read-only check the operator packet spells out, applied here.

    NOTHING IS WRITTEN BY ANY OF THIS. Each repository must identify itself,
    no two may be one repository or one directory, none may borrow objects, and
    the target must already hold every declared base and the configured import
    reference.
    """
    identities, places_seen = {}, {}
    for name, place, _mirror in planned:
        answered = _ran(runner,
                        [REPOSITORY_COMMAND, "-C", place, "rev-parse",
                         "--path-format=absolute", "--git-common-dir"],
                        "asking what " + name + " is")
        if not answered:
            raise BootstrapRefusal(
                "the " + name + " repository at " + place + " answered no "
                "common directory, so isolation cannot be proved and nothing "
                "will be run against it")
        common = os.path.realpath(answered)
        if not os.path.isdir(common):
            raise BootstrapRefusal(
                "the " + name + " repository's common directory " + answered
                + " is not a directory here")
        borrowed = os.path.join(common, "objects", "info", "alternates")
        if os.path.exists(borrowed) and os.path.getsize(borrowed):
            raise BootstrapRefusal(
                "the " + name + " repository borrows objects from elsewhere ("
                + borrowed + "); an independent repository is the whole point "
                "of preparing one here")
        held = os.stat(os.path.realpath(place))
        for other, seen in identities.items():
            if seen == common:
                raise BootstrapRefusal(
                    "the " + name + " and " + other + " repositories are ONE "
                    "repository (" + common + "); integration refuses a "
                    "workspace that is the target or a producer's own line")
        for other, seen in places_seen.items():
            if seen == (held.st_dev, held.st_ino):
                raise BootstrapRefusal(
                    "the " + name + " and " + other + " repositories are one "
                    "directory (" + place + ")")
        identities[name] = common
        places_seen[name] = (held.st_dev, held.st_ino)

    target = planned[0][1]
    bases = {job.get("line_declared_base") for job in document.get("jobs") or []
             if type(job) is dict}
    for base in sorted(one for one in bases if isinstance(one, str) and one):
        _ran(runner, [REPOSITORY_COMMAND, "-C", target, "cat-file", "-e",
                      base + "^{commit}"],
             "proving the declared base " + base + " is a commit in the target")
    reference = document.get("integration_target_reference")
    if isinstance(reference, str) and reference:
        _ran(runner, [REPOSITORY_COMMAND, "-C", target, "rev-parse", "--verify",
                      "--quiet", reference],
             "proving the import reference " + reference + " exists in the target")
    return {"identities": identities,
            "declared_bases": sorted(one for one in bases if isinstance(one, str)),
            "reference": reference}


def storage_bound(document, places, preparing=True):
    """Each worker's mutable storage, under the destination it belongs to.

    [R4 remainder]: `workspace_storage` was neither derived nor checked, so a
    deployment whose repositories were prepared under its own destination
    still wrote its workers' storage somewhere else entirely -- and that
    somewhere could be shared with another deployment.

    DERIVED WHEN ABSENT, REFUSED WHEN IT LEAVES. Two workers of the SAME
    instance sharing a path inside it is the operator's business and is left
    alone; a path outside the destination is not. Nothing here touches
    `credential_sources`: the registry is the owner's and does not move.
    """
    if not preparing:
        return document
    inside = os.path.realpath(places["destination"])
    workers, outside = [], []
    for worker in document.get("workers") or []:
        if type(worker) is not dict or type(worker.get("deployment")) is not dict:
            workers.append(worker)
            continue
        deployment = dict(worker["deployment"])
        named = deployment.get("workspace_storage")
        if named in (None, ""):
            deployment["workspace_storage"] = os.path.join(
                places["destination"], "workers",
                _safe_name(worker["worker_id"]), "storage")
        elif isinstance(named, str):
            held = os.path.realpath(named)
            if held != inside and not held.startswith(inside.rstrip("/") + "/"):
                outside.append((str(worker.get("worker_id")), named, held))
        workers.append(dict(worker, deployment=deployment))
    if outside:
        raise BootstrapRefusal(
            "this input asks for repositories to be prepared under "
            + places["destination"] + " AND puts worker storage outside it:\n"
            + "\n".join("  " + who + " stores at " + named + " (" + held + ")"
                         for who, named, held in outside)
            + "\nA self-contained deployment keeps its mutable state under its "
              "own destination. Drop the member to have it derived, name one "
              "inside the destination, or install with --no-repositories.")
    return dict(document, workers=workers)


def repositories_bound(document, places, preparing=True):
    """Name the repositories this bootstrap is about to prepare.

    DERIVED ONLY WHEN IT IS PREPARING THEM, and only where the input has not
    already chosen. A deployment whose owner named an `integration_target`
    elsewhere keeps it: what is derived here is where THIS bootstrap puts the
    repositories it creates.
    """
    if not preparing:
        return document
    planned = {name: place for name, place, _ in repository_plan(document, places)}
    document = dict(document)
    document.setdefault("integration_target", planned["target"])
    if document.get("integration_workspace") == places["repository"]:
        # `workspace_bound` derives the repository ROOT when nothing is named;
        # with repositories under it, the workspace is one of them.
        document["integration_workspace"] = planned["workspace"]
    workers = []
    for worker in document.get("workers") or []:
        if type(worker) is dict and worker.get("worker_id") and type(
                worker.get("deployment")) is dict:
            deployment = dict(worker["deployment"])
            deployment.setdefault("nominated_source",
                                  planned["source-" + str(worker["worker_id"])])
            worker = dict(worker, deployment=deployment)
        workers.append(worker)
    document["workers"] = workers
    return document


def workspace_bound(document, places):
    """The destination owns its integration workspace. W183883.

    Review 2026-09-16T14-06-35Z: `repo/` was created and then bound to nothing,
    so an installed deployment had a directory for a working area and a
    configuration that never mentioned it.

    DERIVED, NOT SELECTED, and only when ABSENT. A workspace is mutable
    deployment state, which is exactly what a destination is for. An explicit
    null still travels verbatim and is refused in the consumer's own words
    [G2], and `integration_target` -- the repository this deployment integrates
    INTO -- stays the owner's selection, because that one is not this
    deployment's state and outlives any instance.
    """
    if "integration_workspace" not in document:
        return dict(document, integration_workspace=places["repository"])
    named = document["integration_workspace"]
    if type(named) is str and named:
        held = os.path.realpath(named)
        inside = os.path.realpath(places["destination"])
        if held != inside and not held.startswith(inside.rstrip("/") + "/"):
            raise BootstrapRefusal(
                "the integration workspace at " + named + " resolves to "
                + held + ", outside the destination at " + inside + ". An "
                "installed instance keeps its own mutable state under its own "
                "destination; a workspace somewhere else is another "
                "deployment's.")
    return document


def checkout():
    """The tree this code lives in -- and FROZEN, the bundle itself.

    ONE RULE, ASKED OF ITS OWNER. `stage_execution._checkout` is the accepted
    owner of "mutable deployment state must never be written into the code's
    own tree", and it already answers the BUNDLE when frozen [K4]. This module
    had two inline copies of the unfrozen half, and the first real installed
    run found what that costs: frozen, walking three parents up from `__file__`
    answered the INSTANCE DESTINATION, so a repeated bootstrap into a prepared
    destination was refused for being "inside the checkout at <that same
    destination>" -- a true-sounding refusal naming the wrong thing, in place
    of the honest "there is already a runtime here".
    """
    from tools import stage_execution

    return stage_execution._checkout()


def admit(destination, distro):
    """Everything about a destination and a runtime that can be known first.

    [K3]. Called BEFORE `prepare` composes anything, and again from `install`
    so a direct caller cannot skip it. A refusal that has already created an
    Authority, written a configuration or replaced a selector is not a refusal,
    which is the rule this module already keeps for its own inputs.
    """
    from tools import instance

    if not os.path.isabs(destination):
        raise BootstrapRefusal(
            "the destination at " + destination + " must be absolute; an "
            "instance is addressed absolutely or it is addressed differently "
            "from wherever a command happened to run")
    places = instance.layout(destination)
    tree = checkout()
    resolved = os.path.realpath(destination)
    if resolved == tree or resolved.startswith(tree.rstrip("/") + "/"):
        raise BootstrapRefusal(
            "the destination at " + destination + " is inside the checkout at "
            + tree + ", and the whole point of an installed instance is "
            "that development in that checkout cannot change a running Job.")
    custody(places, destination)
    if not distro:
        raise BootstrapRefusal(
            "installing into " + destination + " needs a built runtime; name "
            "it with --distro, or build one with `just build` from v12/.")
    if not Path(distro).is_dir():
        raise BootstrapRefusal(
            "there is no built runtime at " + str(distro)
            + ". Build one with `just build` from v12/ first.")
    # AND THE RUNTIME IS DIGESTIBLE AND SUITABLE BEFORE ANYTHING IS COPIED.
    # [K3]: the identity was asked of the INSTALLED command, so a digestible
    # but unsuitable runtime got as far as a composed Authority, a created
    # destination and a copied distro before being refused -- leaving all of it
    # behind. It is asked of the SOURCE command instead, before any effect.
    runtime = instance.manifest(distro)
    identity = _identity_of(Path(distro) / "baton-v12-stack", runtime, distro)
    return places, runtime, identity


def custody(places, destination):
    """Is this destination still one this attempt may install into?

    ASKED TWICE, AND THAT IS THE POINT. [K1/K3]: installing into a destination
    whose `state` was a link out of it SUCCEEDED and published a selector the
    very next read rejected. Admission then moved the check before any effect
    -- and review 2026-09-16T13-09-22Z showed the other half: an admission is a
    decision about a RUNTIME, and it cannot promise that the destination will
    still look the same when the copy finally happens. `install` asks again,
    holding the destination's lock, and only then has effects.

    What may legitimately be here is what this attempt's own `prepare` made:
    the stores, the logs, the state root, the configuration and the record. The
    runtime and the selector may not, which is what "prepared once" means.
    """
    resolved_destination = os.path.realpath(destination)
    for name in ("distro", "instance", "lock", "stores", "repository", "logs",
                 "state", "deployment_state", "deployment", "record",
                 "identity", "justfile"):
        owned = places[name]
        if not os.path.lexists(owned):
            continue
        # LEXISTS, NOT EXISTS. [K3]: `exists` follows the final link, so a
        # DANGLING `instance.json` link read as absent and was then overwritten
        # -- through the link, into wherever it pointed.
        if os.path.islink(owned):
            raise BootstrapRefusal(
                "the destination already carries a link at " + owned + " (to "
                + os.path.realpath(owned) + "); an instance owns what is under "
                "its own destination, and nothing here writes through a name "
                "somebody else controls.")
        inside = os.path.realpath(owned)
        if inside != resolved_destination and not inside.startswith(
                resolved_destination.rstrip("/") + "/"):
            raise BootstrapRefusal(
                "the destination derives " + name + " " + owned
                + ", which resolves to " + inside + " -- outside "
                + resolved_destination + ". An instance owns what is under its "
                "own destination.")
    if os.path.lexists(places["distro"]):
        # A DESTINATION IS PREPARED ONCE. Replacing a runtime under a stack
        # that may be serving is not something a setup command may do.
        raise BootstrapRefusal(
            "there is already a runtime at " + places["distro"] + "; nothing "
            "here upgrades a deployment in place. Stop that instance and "
            "prepare a new destination if you mean a different runtime.")
    if os.path.lexists(places["justfile"]):
        # [R3]: an existing deployed interface is state this command did not
        # create. Refusing it here means the refusal comes before any effect;
        # the exclusive create in `install` is what closes the interval after.
        raise BootstrapRefusal(
            "there is already a justfile at " + places["justfile"]
            + ". Nothing here replaces one; prepare a new destination.")
    if os.path.lexists(places["instance"]):
        # [K3]: an existing selector -- valid, partial or corrupt -- is state
        # this command did not create and may not overwrite while deciding
        # whether it can even install.
        raise BootstrapRefusal(
            "there is already an instance selector at " + places["instance"]
            + ". Nothing here replaces one; prepare a new destination.")


@contextlib.contextmanager
def serialized(places, wait):
    """Hold this destination against another COOPERATING bootstrap.

    WHAT THIS IS AND IS NOT. Two bootstraps preparing the same destination
    would interleave a copy and a publication; holding one lock across both
    makes the second wait and then be refused by `custody` for what the first
    one left. It coordinates attempts that both take this lock. It is NOT a
    defence against arbitrary hostile mutation of the destination, and nothing
    here claims to be -- the exclusive publication is what makes the last step
    safe regardless.
    """
    import errno
    import fcntl

    deadline = time.monotonic() + wait
    # O_NOFOLLOW: `custody` refuses a link at this name, but the lock is OPENED
    # -- and opening through a link somebody else controls would write into
    # whatever it names.
    held = os.open(places["lock"],
                   os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        while True:
            try:
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as failure:
                if failure.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise BootstrapRefusal(
                        "another bootstrap is holding " + places["lock"]
                        + " and did not finish within " + str(wait)
                        + "s; a destination is prepared once, so nothing here "
                        "installed alongside it.")
                time.sleep(0.02)
        yield held
    finally:
        os.close(held)


def _resources_of(identity, runtime, distro):
    """Is the native validator the identity reports one of the files WE admitted?

    [K3]: `native_rpds` was accepted as any non-empty string, so a build that
    had imported the HOST's rpds answered perfectly well. The first correction
    then anchored it to the identity's OWN `resources`, which the identity also
    reports -- so `resources: "/"` made every path on the host qualify, and a
    prefix fallback admitted a file that was not in the manifest at all, or did
    not exist.

    It is anchored HERE to the distro this admission digested, and to the
    entries that manifest actually binds. Nothing the identity says about
    itself is allowed to widen what counts.
    """
    named = identity.get("native_rpds")
    if type(named) is not str or not named:
        return "did not say where its native validator came from"
    held = os.path.realpath(named)
    root = os.path.realpath(distro)
    for relative in runtime["entries"]:
        if os.path.realpath(os.path.join(root, relative)) == held:
            return None
    return ("reports its native validator at " + named + ", which is not one "
            "of the " + str(runtime["files"]) + " files this bundle binds -- "
            "it imported one from somewhere else")


DEPLOYED_JUSTFILE = """\
# The deployed v12 stack. Written by `just bootstrap`; do not edit by hand.
#
# OWNER-STANDALONE-INTERFACE-20260916.md selects this interface: once a
# deployment is installed, its lifecycle needs NOTHING but the destination.
#
#     cd {destination} && just status
#     just --justfile {justfile} status      # from anywhere at all
#
# EVERY PATH IS RESOLVED FROM THIS FILE'S OWN DIRECTORY, never from the
# caller's working directory, which is what makes the second form mean the same
# deployment as the first. The instance selector beneath is unchanged: the
# command still verifies the runtime it is about to run and still refuses to
# drive an instance that is not its own.
# NOT A LOGIN SHELL. A deployed command must not depend on whoever's
# profile happens to be readable where it runs; the first live run of
# this interface printed a profile permission error before every recipe.
set shell := ["bash", "-euo", "pipefail", "-c"]
set quiet

HERE := justfile_directory()
COMMAND := HERE / "distro" / "baton-v12-stack"
INSTANCE := HERE / "instance.json"

default: status

# The scheduler and its snapshot publisher. Repeatable.
start:
	"{{{{COMMAND}}}}" start --instance "{{{{INSTANCE}}}}"

# Only the processes this deployment owns. Stores and evidence are retained.
stop:
	"{{{{COMMAND}}}}" stop --instance "{{{{INSTANCE}}}}"

# Process health, snapshot freshness, observed Jobs, the runtime boundary.
status:
	"{{{{COMMAND}}}}" status --instance "{{{{INSTANCE}}}}"

# The read-only monitor. INTERVAL is seconds between refreshes; Ctrl-C leaves
# it, and leaving it does not stop scheduling -- that is `just stop`.
monitor INTERVAL="5":
	"{{{{COMMAND}}}}" monitor --instance "{{{{INSTANCE}}}}" --interval "{{{{INTERVAL}}}}"

# What this deployment's repositories actually are. Read-only.
repository:
	"{{{{COMMAND}}}}" repository --instance "{{{{INSTANCE}}}}"

# What this build IS: frozen, platform, packaged assets, digests.
identity:
	"{{{{COMMAND}}}}" identity
"""


def _identity_of_handle(handle):
    """What this attempt created, by (device, inode) rather than by path.

    [R3 remainder]: ownership was a flag set AFTER the write finished, so a
    partial write left bytes nobody would remove and blocked the retry; and a
    file REPLACED between the create and the publication was deleted by the
    unwind, which then said nothing else had been touched. A path is not an
    identity; the file this attempt opened is.
    """
    held = os.fstat(handle)
    return (held.st_dev, held.st_ino)


def _remove_if_still_ours(place, identity, what):
    """Remove `place` only while it IS the thing this attempt made.

    Answers what happened, in one line, for the record: removed, already gone,
    left because it is no longer ours, or left because we could not tell.
    Nothing here raises: cleanup that fails is reported, not re-thrown over the
    refusal that caused it.
    """
    if identity is None:
        return None
    try:
        held = os.lstat(place)
    except FileNotFoundError:
        return None
    except OSError as failure:
        return ("left " + place + " alone: this attempt could not tell whether "
                "it is still the " + what + " it made (" +
                type(failure).__name__ + ")")
    if (held.st_dev, held.st_ino) != identity:
        return ("left " + place + " alone: it is no longer the " + what
                + " this attempt made, so it belongs to whoever replaced it")
    try:
        if os.path.isdir(place) and not os.path.islink(place):
            import shutil

            shutil.rmtree(place)
        else:
            os.unlink(place)
    except OSError as failure:
        return ("could not remove " + place + ", which this attempt made ("
                + type(failure).__name__ + "): it is still there")
    return "unwound " + place


def deployed_justfile(places):
    """The text of the destination's own justfile."""
    return DEPLOYED_JUSTFILE.format(destination=places["destination"],
                                    justfile=places["justfile"])


def install(destination, distro, document, *, stream=sys.stdout, now=None,
            admitted=None, wait=120.0):
    """Prepare an external destination and emit the one selector for it.

    W183883, OWNER-INSTANCE-DESTINATION-20260916.md. The deployment this
    already composes goes to `destination/`, beside a COPY of the one-folder
    runtime -- so the running stack reads nothing from the development checkout
    and work can continue there while Jobs run.

    NOTHING IS OVERWRITTEN AND NOTHING IS UPGRADED. A destination already
    holding a runtime is refused with what differs named; a destination already
    holding a different deployment is refused by the custody checks this module
    already keeps. Safe refusal is the whole answer the owner selected.
    """
    import shutil

    from tools import instance

    # THE ADMISSION IS CARRIED, NOT REPEATED. [K3]: `main` admitted, threw the
    # answer away, and `install` admitted again -- so a source distro CHANGED
    # while `prepare` was composing was re-admitted and installed, exit 0, with
    # a digest nobody had agreed to. One admission decides, and everything
    # after it is held to that decision.
    places, runtime_before, identity = (
        admit(destination, distro) if admitted is None else admitted)
    if os.path.realpath(places["destination"]) != os.path.realpath(destination):
        raise BootstrapRefusal(
            "this admission was made for " + places["destination"]
            + " and is being used to install into " + destination)
    # THE PINNED RUNTIME IS THE ONE THAT WAS AGREED TO, and this is asked
    # before the destination is so much as created -- a refusal here leaves
    # nothing behind at all.
    current = instance.manifest(distro)
    if current["digest"] != runtime_before["digest"]:
        raise BootstrapRefusal(
            "the runtime at " + str(distro) + " changed after it was admitted: "
            "it digested " + runtime_before["digest"][:16] + "... and now "
            "digests " + current["digest"][:16] + "... Nothing here installs a "
            "runtime it did not verify.")

    Path(places["destination"]).mkdir(parents=True, exist_ok=True)
    with serialized(places, wait):
        # THE DESTINATION IS ASKED ABOUT AGAIN, HOLDING THE LOCK. An admission
        # decides about the RUNTIME; it cannot promise the destination stayed
        # the way it was while `prepare` composed an Authority into it.
        custody(places, destination)
        for name in ("stores", "repository", "logs", "state"):
            Path(places[name]).mkdir(parents=True, exist_ok=True)
        shutil.copytree(distro, places["distro"], symlinks=True)
        copied = os.lstat(places["distro"])
        runtime_identity = (copied.st_dev, copied.st_ino)
        justfile_identity = None
        try:
            runtime = instance.manifest(places["distro"])
            if runtime["digest"] != runtime_before["digest"]:
                raise BootstrapRefusal(
                    "the runtime copied into " + places["distro"] + " does not "
                    "digest as the one admitted from " + str(distro)
                    + "; nothing here installs a runtime it did not verify.")
            selector = instance.emit(
                destination, authority_uuid=document["authority_uuid"],
                identity=identity, runtime=runtime, now=now)
            # NOT `publish`. A selector that appeared since `custody` looked
            # would be REPLACED by an atomic rewrite; `create` refuses the name
            # it cannot have, and leaves whatever is there exactly as it is.
            # THE DEPLOYED INTERFACE IS PART OF THE INSTALL, written before
            # the selector so a destination carrying a selector always carries
            # the justfile that drives it -- and EXCLUSIVELY. [R3]: a regular
            # file already at that name was overwritten and the selector
            # published over it, because custody only refused a LINK there.
            try:
                handle = os.open(places["justfile"],
                                 os.O_WRONLY | os.O_CREAT | os.O_EXCL
                                 | os.O_NOFOLLOW, 0o644)
            except FileExistsError:
                raise BootstrapRefusal(
                    "there is already a justfile at " + places["justfile"]
                    + ", which this install would be the deployed interface "
                    "at. It was left exactly as it is; a destination is "
                    "prepared once.")
            # OWNED FROM THE MOMENT IT EXISTS, not from the moment it is
            # finished: a write that fails part-way still leaves a file this
            # attempt created, and leaving it would block this attempt's own
            # retry.
            justfile_identity = _identity_of_handle(handle)
            with os.fdopen(handle, "w") as writing:
                writing.write(deployed_justfile(places))
            try:
                instance.create(places["instance"], selector)
            except instance.InstanceRefusal as refusal:
                # SAID IN THIS COMMAND'S OWN VOICE, so `main` prints "refused:"
                # and exits 2 rather than raising through a setup command.
                raise BootstrapRefusal(str(refusal))
        except (BootstrapRefusal, OSError) as failure:
            # ONLY WHAT THIS ATTEMPT MADE IS UNWOUND, and ALL of it. `custody`
            # proved the runtime, the selector and the justfile absent moments
            # ago under this same lock, so both the copied distro and the
            # justfile written here are provably ours.
            #
            # [R3 remainder]: the justfile was NOT unwound, so a transient
            # publication failure left it behind -- and the retry then refused
            # for that leftover, which this attempt had created. Nothing
            # foreign is touched either way: the selector, if one appeared, is
            # somebody else's and is left exactly as it is.
            said = [_remove_if_still_ours(places["justfile"],
                                          justfile_identity, "justfile"),
                    _remove_if_still_ours(places["distro"],
                                          runtime_identity, "runtime")]
            for line in [one for one in said if one]:
                print("cleanup       " + line, file=stream)
            raise

    print("instance      " + places["instance"], file=stream)
    print("runtime       %d files, digest %s"
          % (runtime["files"], runtime["digest"][:16] + "..."), file=stream)
    print("stores        " + places["stores"], file=stream)
    print("repository    " + places["repository"], file=stream)
    print("justfile      " + places["justfile"], file=stream)
    print("\nThe deployment is operated from the destination, and needs "
          "nothing else:\n", file=stream)
    print("    cd " + places["destination"] + " && just status", file=stream)
    print("    just --justfile " + places["justfile"] + " start"
          "        # from anywhere", file=stream)
    print("\nor the command directly, which is the same program:\n",
          file=stream)
    print("    " + places["command"] + " status --instance "
          + places["instance"], file=stream)
    return selector


# The frozen assets this distribution ships, by name. [K3]: `schema_assets` was
# accepted as any dict of positive integers, so an empty one -- or one carrying
# an arbitrary key -- passed.
EXPECTED_ASSETS = ("agent-session-1.0", "worker-control-1.0")


def _identity_of(command, runtime=None, distro=None):
    """What the built command says it is, asked of the command itself."""
    import subprocess

    try:
        done = subprocess.run([str(command), "identity"], capture_output=True,
                              text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as failure:
        raise BootstrapRefusal("the built command at " + str(command)
                               + " would not run: " + str(failure))
    if done.returncode != 0:
        raise BootstrapRefusal("the built command at " + str(command)
                               + " refused to say what it is:\n" + done.stderr)
    try:
        said = json.loads(done.stdout)
    except ValueError:
        raise BootstrapRefusal("the built command at " + str(command)
                               + " did not answer with one document")
    # [K3]: EXIT 0 IS NOT AN IDENTITY. A command that ran unfrozen, or whose
    # packaged schema assets or native validator did not travel, answers
    # perfectly well and would then fail inside a child a supervisor had
    # already started.
    if type(said) is not dict or said.get("frozen") is not True:
        raise BootstrapRefusal(
            "the command at " + str(command) + " is not a frozen build; an "
            "installed instance runs a bundle, not an interpreter reading a "
            "checkout.")
    assets = said.get("schema_assets")
    if type(assets) is not dict or sorted(assets) != sorted(EXPECTED_ASSETS) \
            or not all(type(one) is int and one > 0 for one in assets.values()):
        raise BootstrapRefusal(
            "the command at " + str(command) + " did not bring exactly the "
            "frozen schema assets this distribution ships "
            + repr(sorted(EXPECTED_ASSETS)) + "; it reports " + repr(assets)
            + ". They are read at import time, so a bundle without them "
            "refuses every document it is given.")
    if runtime is not None:
        problem = _resources_of(said, runtime, distro)
        if problem is not None:
            raise BootstrapRefusal(
                "the command at " + str(command) + " " + problem
                + ". `rpds` has no pure-Python fallback, so a bundle that "
                "borrowed the host's is not self-contained.")
    return said


def main(argv=None, *, stream=sys.stdout, runner=None):
    parser = argparse.ArgumentParser(
        prog="bootstrap",
        description="Prepare the v12 stack's one-time deployment.")
    parser.add_argument("--inputs", required=True,
                        help="the " + SCHEMA + " document naming this "
                             "deployment's production selections")
    parser.add_argument("--destination", default=None,
                        help="an absolute external destination to install into; "
                             "the instance.json emitted there selects every "
                             "lifecycle command")
    parser.add_argument("--distro", default=None,
                        help="the built one-folder runtime to install")
    parser.add_argument("--repository-source", default=None,
                        help="the checkout this deployment's repositories are "
                             "cloned from; the default is the one containing "
                             "this distribution's own v12/justfile")
    parser.add_argument("--no-repositories", action="store_true",
                        help="install without preparing any repository, which "
                             "leaves a deployment that schedules and never "
                             "reconciles")
    taken = parser.parse_args(argv)
    try:
        try:
            document = json.loads(Path(taken.inputs).read_bytes())
        except FileNotFoundError:
            raise BootstrapRefusal("there is no input document at " + taken.inputs
                                   + ". See v12/STACK.md for what it names.")
        except ValueError as failure:
            raise BootstrapRefusal(taken.inputs + " is not one JSON document: "
                                   + str(failure))
        if taken.destination:
            # THE DESTINATION'S OWN LAYOUT IS WHAT THE DEPLOYMENT IS COMPOSED
            # INTO, so the configuration this writes already names the stores
            # the instance will select.
            from tools import instance

            places = instance.layout(taken.destination)
            document = dict(document, state_root=places["destination"])
            # PREPARED BY DEFAULT, because the owner's two-operand command
            # "creates the bundled distro, databases and independent
            # repositories" -- and the source is this checkout rather than a
            # member of the document. `--no-repositories` is the way to say
            # otherwise, and it is said in the output either way.
            source = (None if taken.no_repositories
                      else repository_source(taken.repository_source))
            preparing = source is not None
            document = workspace_bound(document, places)
            document = repositories_bound(document, places, preparing)
            document = storage_bound(document, places, preparing)
            # [K3]: EVERY ADMISSION IS SETTLED BEFORE `prepare` HAS EFFECTS.
            # This used to compose the Authority and write the configuration
            # and only then discover there was no runtime to install -- so a
            # missing `--distro` left a half-prepared destination behind.
            admitted = admit(taken.destination, taken.distro)
            # BEFORE `prepare`, because `nominate_source` proves each worker's
            # source directory with an lstat and an O_DIRECTORY|O_NOFOLLOW
            # open: a configuration naming repositories that do not exist yet
            # is refused there, before an Authority is composed.
            prepared_repositories = prepare_repositories(
                document, places, stream=stream, runner=runner, source=source)
        prepared = prepare(document, stream=stream,
                           installing=bool(taken.destination))
        if taken.destination:
            # THE IDENTITY `prepare` RESOLVED, not one the input named: the
            # input names none, and the selector installed at the destination
            # has to select the Authority that was actually composed.
            install(taken.destination, taken.distro,
                    dict(document, authority_uuid=prepared["authority_uuid"]),
                    stream=stream, admitted=admitted)
        return 0
    except BootstrapRefusal as refusal:
        print("refused: " + str(refusal), file=stream)
        return 2
    except OSError as failure:
        # AN EXPECTED INSTALLATION FAILURE, ANSWERED HERE. `install` raises the
        # OSError on purpose -- its callers, including the tests, need the real
        # exception -- but the PUBLIC command is an operator's, and a traceback
        # after a clean unwind tells them nothing they can act on. Only OSError:
        # a programming fault is not an operator's to read as a refusal.
        # A POINTER, NOT A GUARANTEE. Review 2026-09-16T19-25-41Z: this said
        # "anything this attempt made was unwound" unconditionally -- and a
        # cleanup whose unlink is refused prints "could not remove ...: it is
        # still there" and then that. The cleanup lines above say what was
        # removed and what was retained; this refusal says where to read them.
        print("refused: the installation could not finish ("
              + type(failure).__name__ + ": " + str(failure) + "). See the "
              "cleanup messages above for what was removed and what was "
              "retained; anything this attempt did not make was left exactly "
              "as it is.", file=stream)
        return 2


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
