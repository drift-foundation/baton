"""The managed-correction packet, GENERATED AND CHECKED rather than described.

W236087 item 3, answering review 2026-09-29T21-08-40Z. `PACKET-309306.md`
stated the question, the bindings, the bounds and the outcomes and then told an
operator to perform steps 2 and 3 through "the owner APIs" -- comments naming
functions, with no command, no input document and nothing that could refuse. A
preparation step that cannot be run is not a preparation step, which is the
same defect `prepare_instance.py` was written to correct one campaign earlier.

So this is the step. It has three subcommands, in the order the acts require:

    stage   Everything that needs nothing from a live instance: the bootstrap
            input document, the IMMUTABLE manager source this run's processes
            will import, the context profile, the Job submission carrying the
            selected documentation task and its acceptance requirements, and
            the exact commands. Refuses before it writes anything.
    bind    After `tools.bootstrap` has installed the instance and the owner
            acts have run: measure what actually exists -- the emitted
            deployment configuration, the minted Authority identity, the
            profile and the submission -- and emit the packet the supervisor
            reads.
    check   Re-prove an existing packet against the tree, which is what the
            supervisor does before it opens a store, available on its own so
            a reviewer can do it without serving anything.

WHAT IT DOES NOT DO, and the boundary is the point. It opens no store, mints
no identity, starts no container, builds no image, reads no credential byte and
performs no version-control act. It writes documents, and it copies source
files into a staging directory. Every act that changes the world belongs to the
commands it emits, which an owner runs by their own selection.

WHY THE MANAGER SOURCE IS COPIED. Review R3: the packet named a runtime distro
and then told the operator to serve with `PYTHONPATH` pointing at
`/home/sl/src/baton/v12/python`, a working tree that can change between the
review and the run. Hash listings do not pin imports. `staged_source` copies
the two import roots to a directory outside the run root and measures every
file, `baseline.verify_imported_sources` then refuses any package this process
resolved outside that directory, and `held_packet` refuses a staged file whose
bytes have moved. The bytes that are reviewed are the bytes that run, or the
run does not start.

WHY THE STAGING DIRECTORY IS OUTSIDE THE RUN ROOT, measured rather than
preferred. `stage_execution._checkout` walks three parents above its own
`__file__`, so a source staged at `<run root>/manager-source` answers the RUN
ROOT as the code boundary and the composition then refuses this run's own
stores for living inside it. The accepted single-implementation packet staged
its source under a different root for exactly this reason. `stage` refuses a
staging root that contains the run root or lies inside it, with the walk named.

WHAT IS AN OPERAND AND WHAT IS AN OUTPUT. Review R3 again, and it corrects
`PACKET-309306.md` section 6 directly: the Authority UUID and the bootstrap
input document are OUTPUTS of this preparation -- `stage` writes the input
document and `bind` reads the identity the bootstrap minted -- not external
authority anybody is waiting on. What genuinely needs owner input is the
immutable source and its declared base, and the credential reference the
profile resolves at launch; both are named `<OWNER ...>` in the selections and
refused until they are resolved.
"""
import argparse
import errno
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys

PACKET_SCHEMA = "baton.managed-correction-packet/1"
SELECTIONS_SCHEMA = "baton.managed-correction-selections/1"
# THE SUPPORTED SCHEMAS, mirrored from the modules that read them rather than
# spelled a second way. Review 2026-09-29T21-41-08Z R1 refused two documents I
# had written in schemas of my own invention; a constant named after the real
# reader is how that stops being possible to do quietly.
BOOTSTRAP_SCHEMA = "baton.v12.stack-bootstrap/1"      # tools.bootstrap.SCHEMA
SUBMISSION_SCHEMA = "baton.v12.job-submission/2"      # documents.SUBMISSION_SCHEMA
TASK_SCHEMA = "baton.dogfood-task/2"                  # the worker's task.json
WORKER_SCHEMA = "baton.v12.single-worker-deployment/5"  # the CONTEXT-capable one


def _accepted(expected=None):
    """The accepted instance's own descriptor set, imported rather than retyped.

    `prepare_two_jobs.ACCEPTED` is W247941's provenance-documented constant
    map: every digest in it is measured from an accepted record by
    `verify_247941.accepted()`, and its `_provenance` member names which
    record each was measured from. Reusing it is the same discipline as
    pinning `baseline.py` -- and the alternative is what my first draft did,
    which was to hash strings of my own making and call them policy digests.

    IMPORTED READ-ONLY AND NEVER EDITED. That dossier is accepted and closed.
    """
    import sys as _sys

    place = os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))), "finding-v12-real-jobs-adoption-gate")
    if not os.path.isdir(place):
        _refuse(f"the accepted two-Job preparation is not at {place!r}, so "
                f"this module cannot read the measured descriptor set it "
                f"binds instead of inventing one")
    whole = os.path.join(place, "prepare_two_jobs.py")
    if not os.path.exists(whole):
        _refuse(f"the reused descriptor supplier is not at {whole!r}")
    if place not in _sys.path:
        _sys.path.insert(0, place)
    import prepare_two_jobs

    # THE DIGEST IS CHECKED WHERE THE IMPORT HAPPENS when a caller supplies the
    # expectation. `stage` retains it and `bind` compares, so the descriptors
    # these documents are built from cannot move between the two unnoticed.
    if expected is not None and digest_of(whole) != expected:
        _refuse(f"the reused descriptor supplier {whole!r} has CHANGED since "
                f"`stage` reviewed it; the measured descriptors these "
                f"documents are built from are not the reviewed ones")
    return prepare_two_jobs.ACCEPTED

# THE TWO IMPORT ROOTS, in the order `PYTHONPATH` must name them: the package
# root first, then the directory `tools` is a package under. Both are copied,
# because both are imported.
IMPORT_ROOTS = ("src", ".")
IMPORTED_PACKAGES = ("baton_v12", "tools")

# The bounds, as this Job's own numbers. They are CONSTANTS here rather than
# selections: `PREPARATION-307667.md` fixed them, the supervisor enforces
# exactly these, and an operand would let a run quietly widen what was
# reviewed. `corrections` and `review_invocations` exist here and deliberately
# do NOT exist in the single-implementation packet -- that packet refuses a
# second implementer invocation by name, because a correction round is this
# Job's workload rather than a bigger version of that one.
BOUNDS = {
    "turn_seconds": 180,
    "verification_seconds": 180,
    "total_seconds": 900,
    "cleanup_seconds": 60,
    "implementer_invocations": 2,
    "review_invocations": 2,
    "corrections": 1,
    "restores": 1,
    "retry": False,
}

_PACKET = ("schema", "run_id", "work", "claim", "note", "worker_image",
           "manager_runtime", "manager_source", "supervisor", "code_boundary",
           "deployment", "composition", "context", "submission", "fixture",
           "bounds", "provenance", "compatibility", "outcome_path",
           # OWNER REROUTE 312164: the packet was bound to stores, modules,
           # documents and an image, and said NOTHING about the two filesystem
           # roots `baseline.prepare` configures first -- so a packet could be
           # proved complete over an instance that had neither, which is what
           # the live run discovered inside the supervisor.
           "filesystem_roots")
# THE GENERATED COMPOSITION, bound as its own artifact. `deployment` above is
# where this run's stores and identity live; this is the document the workers are
# configured in and the one `stage_execution.operations_from` reads.
# NO `path` AND NO `sha256`: the composition IS `deployment.config_path`, which
# is already pinned there. Carrying the same file twice is the "two places for
# one fact" the enclosing validator refuses in its own document, and the rule is
# no better here.
_COMPOSITION = ("workers", "producer_schema", "reviewer_schema",
                "contextual_worker")
_BOUNDS = tuple(sorted(BOUNDS))
_DEPLOYMENT = ("config_path", "config_sha256", "job_store", "control_store",
               "authority_store", "authority_uuid", "state_root")
_CONTEXT = ("storage_path", "excluded_roots", "runtime_uid", "profile_path",
            "profile_sha256", "profile_digest", "qualification",
            "layout_version", "job_id")
_IMAGE = ("reference", "config_digest", "worker_files", "adapter_descriptor",
          "policy_descriptor", "profile_descriptor")
_RUNTIME = ("path", "executable_sha256", "build_commit")
_SOURCE = ("path", "packages", "file_count", "files", "frozen_assets")
_SELF = ("path", "sha256")
# NO `participant` PER STAGE. Review 2026-09-29T21-41-08Z R1: the real
# `documents.STAGE_MEMBERS` is kind, work_id, profile_name, profile_digest and
# depends_on -- a stage names no participant, so the packet cannot read one out
# of the submission. The producer and reviewer principals are the DEPLOYMENT's,
# and the packet carries them beside the submission it binds.
_SUBMISSION = ("path", "sha256", "submission_id", "job_id", "work_id",
               "input_digest", "task_path", "task_sha256", "manifest_path",
               "manifest_sha256", "review_participant",
               "implementation_participant")
_FIXTURE = ("source_root", "declared_base", "files")

# WHAT THE OWNER STILL SELECTS. Everything else this module derives or measures.
_SELECTIONS = ("schema", "run_id", "work", "instance_root", "staging_root",
               "source", "manager_source_origin", "manager_runtime",
               "worker_image", "participants", "credential_reference",
               "runtime_uid", "context_profile", "receipts",
               "credential_delivery",
               "review_route", "context_storage", "workspace_storage",
               "stores")
# THE PROFILE'S OWN MEMBERS, mirrored from `provider_context._profile`'s closed
# document rather than invented. A profile this module composed from a shorter
# list would be refused by `certify_context_profile` AFTER the bootstrap had
# already installed an instance, which is the class of fault this whole file
# exists to move earlier.
_PROFILE = ("schema", "qualification", "evidence_digest", "cli_build",
            "image_digest", "adapter_digest", "runtime_profile_digest",
            "argv_policy_digest", "environment_policy_digest",
            "layout_version", "reported_model", "model", "cwd", "state_paths",
            "max_entries", "max_bytes", "retention_policy_digest")


class PacketRefusal(Exception):
    """Refused rather than prepared. Never a partial packet's excuse."""


def _refuse(message):
    raise PacketRefusal(message)


def _document(value, what, members):
    if type(value) is not dict:
        _refuse(f"{what} is one document, not {type(value).__name__}")
    absent = [name for name in members if name not in value]
    if absent:
        _refuse(f"{what} names no {', '.join(absent)}")
    extra = [name for name in sorted(value) if name not in members]
    if extra:
        _refuse(f"{what} carries unknown member(s) {', '.join(extra)}")
    return value


def digest_of(path):
    held = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            held.update(block)
    return held.hexdigest()


def _pin(path, expected, what):
    if not os.path.exists(path):
        _refuse(f"{what} is not at {path!r}")
    found = digest_of(path)
    if found != expected:
        _refuse(f"{what} at {path!r} is {found} and this packet is bound to "
                f"{expected}")
    return found


def _object_name(value, what):
    if type(value) is not str or len(value) != 40 \
            or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is one full lower-case object name; this is {value!r}")
    return value


def _absolute(value, what):
    if type(value) is not str or not os.path.isabs(value) \
            or os.path.normpath(value) != value:
        _refuse(f"{what} is one absolute canonical path; this is {value!r}")
    return value


def _inside(outer, inner):
    """Is `inner` at or under `outer`, asked of NORMALIZED real locations?

    Text containment answers the wrong question: `/a/b/../c` reads as neither,
    and a sibling whose name merely begins with the other's matches on spelling
    rather than on where the directory is.
    """
    whole = os.path.realpath(outer)
    held = os.path.realpath(inner)
    try:
        return os.path.commonpath([whole, held]) == whole
    except ValueError:                        # different drives cannot nest
        return False


# -- the selections ---------------------------------------------------------

def unresolved(value):
    """Every member still marked `<OWNER`, named at once rather than found at
    the first act that needs it."""
    found = []

    def walk(held, path):
        if isinstance(held, dict):
            for name in sorted(held):
                walk(held[name], f"{path}.{name}" if path else name)
        elif isinstance(held, list):
            for index, one in enumerate(held):
                walk(one, f"{path}[{index}]")
        elif isinstance(held, str) and held.startswith("<OWNER"):
            found.append(path)

    walk(value, "")
    return found


def held_selections(path):
    """The owner's selections, proved before anything is written."""
    with open(path, "rb") as handle:
        chosen = json.loads(handle.read().decode("utf-8"))
    _document(chosen, f"the selections at {path!r}", _SELECTIONS)
    if chosen["schema"] != SELECTIONS_SCHEMA:
        _refuse(f"this reads {SELECTIONS_SCHEMA!r} and {path!r} names "
                f"{chosen['schema']!r}")
    still = unresolved(chosen)
    if still:
        _refuse(f"{path!r} still carries unresolved owner operand(s): "
                f"{', '.join(still)}")
    run = chosen["run_id"]
    if type(run) is not str or not run:
        _refuse("the selections name no run_id")
    # THE WORK SELECTOR, CHECKED WHERE IT IS SELECTED. `prepare-work` composes
    # `<8 hex>-<work>` and the Authority refuses anything that is not
    # `<8 hex>-W<positive>`, so an unusable selector is refused here rather than
    # at the first act against a store.
    held = chosen["work"]
    if type(held) is not str or not held.startswith("W") \
            or not held[1:].isdigit() or int(held[1:]) <= 0:
        _refuse(f"the selected work {held!r} is the LOCAL selector this "
                f"preparation qualifies -- `W` followed by a positive number -- "
                f"because `authority.identity.check_work_id` accepts only "
                f"`<8 hex>-W<positive>`")
    root = _absolute(chosen["instance_root"], "the instance root")
    staging = _absolute(chosen["staging_root"], "the staging root")
    # THE BOUNDARY WALK, CHECKED RATHER THAN HOPED FOR. Both directions: a
    # staging root under the run root makes the run root the code boundary and
    # this run's own stores then live inside it; a run root under the staging
    # root is the same fault spelled the other way.
    if _inside(root, staging) or _inside(staging, root):
        _refuse(f"the staging root {staging!r} and the instance root {root!r} "
                f"nest. `stage_execution._checkout` walks three parents above "
                f"the staged `tools/stage_execution.py`, so a source staged "
                f"inside the run root answers the run root as the code "
                f"boundary and composition then refuses this run's own stores "
                f"for living inside it. They are separate directories.")
    if run not in [one for one in os.path.normpath(root).split(os.sep) if one]:
        _refuse(f"the instance root {root!r} does not name this run {run!r} in "
                f"its own path; a fresh run's state is its own")
    source = _document(chosen["source"], "the selected source",
                       ("root", "declared_base", "files"))
    _absolute(source["root"], "the selected source root")
    _object_name(source["declared_base"], "the declared base")
    if type(source["files"]) is not list or not source["files"] \
            or any(type(one) is not str or not one or os.path.isabs(one)
                   for one in source["files"]):
        _refuse("the selected source names at least one relative file to bind")
    _absolute(chosen["manager_source_origin"], "the manager source origin")
    _document(chosen["manager_runtime"], "the selected manager runtime",
              _RUNTIME)
    _document(chosen["worker_image"], "the selected worker image", _IMAGE)
    who = _document(chosen["participants"], "the selected participants",
                    ("implementation", "review", "integration"))
    # THE RECEIPT WRITERS ARE NOT THE WORKERS. A first version used the review
    # WORKER's participant as the review-receipt participant, and the Authority
    # refused the composition by name: "'baton.reviewer' writes this
    # deployment's review receipt and holds no review capability". They are
    # different roles -- one executes a review stage, one writes the deployment's
    # receipt -- and the accepted instance keeps them distinct too.
    receipts = _document(chosen["receipts"], "the selected receipt writers",
                         ("verification", "review", "approval"))
    for name, held in sorted(receipts.items()):
        if type(held) is not str or not held:
            _refuse(f"the {name} receipt names one participant")
    # THE REVIEW PRINCIPAL IS A DIFFERENT ONE, refused here rather than
    # discovered by a run in which the producer reviewed itself.
    if who["review"] == who["implementation"]:
        _refuse(f"the review principal and the implementer are both "
                f"{who['review']!r}; this Job's whole question is whether REAL "
                f"independent feedback drives the correction, and a producer "
                f"reviewing itself answers nothing")
    if type(chosen["runtime_uid"]) is not int or chosen["runtime_uid"] < 0:
        _refuse("the selections name one runtime uid")
    if type(chosen["credential_reference"]) is not str \
            or not chosen["credential_reference"]:
        _refuse("the selections name the profile's credential reference")
    delivery = _document(chosen["credential_delivery"],
                         "the selected credential delivery",
                         ("provider", "slots", "sources"))
    if type(delivery["slots"]) is not list or not delivery["slots"] \
            or any(type(one) is not str or not one for one in delivery["slots"]):
        _refuse("the credential delivery names at least one slot")
    if type(delivery["provider"]) is not str or not delivery["provider"]:
        _refuse("the credential delivery names one provider")
    if delivery["sources"] is not None \
            and not (type(delivery["sources"]) is str
                     and os.path.isabs(delivery["sources"])):
        _refuse("the credential registry is one absolute path, or null when the "
                "deployment resolves without one")
    # AND NOTHING THAT LOOKS LIKE A SECRET. The reference is a NAME the manager
    # resolves; a selections document carrying the bytes would put them in every
    # generated worker.
    for name in ("reference", "secret", "token", "password", "key"):
        if name in str(delivery.get("provider", "")).lower():
            _refuse(f"the credential provider name mentions {name!r}; this "
                    f"document names a provider and a reference, never a bearer")
    storage = _document(chosen["context_storage"],
                        "the selected private context storage",
                        ("path", "excluded"))
    _absolute(storage["path"], "the private context storage")
    if type(storage["excluded"]) is not list \
            or not all(type(one) is str and os.path.isabs(one)
                       for one in storage["excluded"]):
        _refuse("the context storage's excluded roots are absolute paths")
    _absolute(chosen["workspace_storage"], "the workspace storage")
    # THE STORES ARE DEPLOYMENT FACTS, so they are operands. An instance
    # installed by `tools.bootstrap` puts them under `<root>/db`, and a
    # disposable deterministic fixture puts them where it makes them; the
    # generator names what the run will actually open rather than a layout it
    # assumes.
    places = _document(chosen["stores"], "the selected stores",
                       ("authority", "job", "control", "integration",
                        "state_root"))
    for name, held in sorted(places.items()):
        _absolute(held, f"the {name} store")
    routes = _document(chosen["review_route"], "the selected review routes",
                       ("implementation", "review"))
    for name, held in sorted(routes.items()):
        if type(held) is not str or not held:
            _refuse(f"the {name} worker's outgoing review route is one name")
    profile = _document(chosen["context_profile"],
                        "the selected context profile", _PROFILE)
    # THE COMPOSITION, CHECKED HERE RATHER THAN DESCRIBED. Review R3: the
    # packet must bind "exact deployment/context-profile/image/descriptor
    # composition", and a profile certified against a DIFFERENT image is the
    # one way a reused artifact silently stops being the reviewed one.
    if profile["image_digest"] != chosen["worker_image"]["config_digest"]:
        _refuse(f"the context profile is composed against image "
                f"{profile['image_digest']!r} and this run's image is "
                f"{chosen['worker_image']['config_digest']!r}; a profile "
                f"certified for other bytes does not qualify these")
    if profile["adapter_digest"] != chosen["worker_image"]["adapter_descriptor"]:
        _refuse(f"the context profile names adapter descriptor "
                f"{profile['adapter_digest']!r} and the image carries "
                f"{chosen['worker_image']['adapter_descriptor']!r}")
    # AND IT IS A MANAGED-CONTEXT PROFILE, which is the claim
    # `claude-fresh-implementation` could not make. A restore consumes the
    # conversation file, so the allowlist must name it.
    if not any("{conversation_id}" in one for one in profile["state_paths"]):
        _refuse(f"the context profile's state allowlist {profile['state_paths']!r} "
                f"names no conversation file, so nothing it retains could be "
                f"restored; this Job needs a managed-context profile and this "
                f"is not one")
    return chosen


# -- the documentation Job -------------------------------------------------

# THE SELECTED TASK, from `PREPARATION-307667.md`'s "Useful development Job to
# prepare, not execute". Its utility is an operator guide for the restore
# workflow this campaign connected -- a document the next operator actually
# needs -- rather than a contrived edit that exists to be corrected.
TASK_PATH = "docs/v12-context-correction.md"
TASK = (
    "Write {path} -- an operator guide for the managed context-correction "
    "workflow: how a qualified producer's conversation is retained, when it "
    "may be restored, and what an operator does at each step. Write it for an "
    "operator who has the supported CLI in front of them and has not read the "
    "implementation."
).format(path=TASK_PATH)

# THE ACCEPTANCE REQUIREMENTS, COMPLETE, and the SAME text reaches the
# implementer and the reviewer. `PREPARATION-307667.md`: "Give implementer and
# reviewer the SAME complete acceptance requirements... Do not omit
# requirements to induce correction. No hidden acceptance criterion."
#
# THAT RULE IS WHY THIS IS ONE CONSTANT AND NOT TWO. Two lists that are meant
# to be equal are two lists that can drift, and a producer held to a
# requirement it was never given is a manufactured correction -- which is
# exactly the outcome this run must not fabricate.
CRITERIA = (
    "The document is accepted only if ALL of the following hold. They are the "
    "complete requirements: there is no further hidden criterion, and nothing "
    "here is withheld from either party.",
    "1. It states which context and checkpoint are ELIGIBLE for a restore, "
    "and that actual independent review feedback is required -- a restore is "
    "not a retry an operator may ask for.",
    "2. It distinguishes the FRESH execution identity from the RETAINED "
    "conversation: the successor runs in a new container under a new "
    "execution, and what travels is the conversation and checkpoint, not the "
    "predecessor's runtime.",
    "3. It gives the supported command sequence, in order, with each command "
    "exactly as the pinned CLI accepts it.",
    "4. It handles all four endings separately and honestly: ACCEPTED WITH NO "
    "CORRECTION (a complete result that makes no restore claim), "
    "CHANGES-REQUESTED then corrected, REJECTED, and FAILED SAVE OR UNKNOWN.",
    "5. It states the exact cessation rule -- the predecessor's runtime is "
    "positively excluded before the successor activates -- and that a failed "
    "context save is NOT successful reuse and is not evidence a stopped "
    "runtime still runs.",
    "6. It never instructs an operator to read, copy or print private context "
    "state or credential bytes.",
    "7. Every claim it makes about behaviour is true of the CURRENT "
    "implementation and DESIGN, not of an intended one.",
)
REVIEW_TASK = (
    "Review {path} against the acceptance requirements below, which are the "
    "COMPLETE requirements the producer was given -- the same text, with "
    "nothing added here. Check every command independently against the pinned "
    "supported CLI and every behavioural claim against DESIGN and the current "
    "implementation. Accept, request changes, or reject: all three verdicts "
    "are valid results and none is preferred. Do not request changes to "
    "produce a correction round, and do not accept to end the run."
).format(path=TASK_PATH)


def submission_document(chosen, *, job_id, work_id, input_digest,
                        profile):
    """The ONE Job, IN THE REAL SUBMISSION CONTRACT.

    Review R1 drove `read_submission` at my first draft and it refused before
    reaching anything interesting: "a job submission needs submission_id". The
    whole shape was invented. The real contract is
    `documents.SUBMISSION_MEMBERS` -- schema, submission_id, jobs -- with
    `JOB_MEMBERS` job_id, input_digest, policy_digest, test_scope,
    terminal_policy, stages, and `STAGE_MEMBERS` kind, work_id, profile_name,
    profile_digest, depends_on. There is no `participant`, no `task`, no
    `acceptance_requirements` and no `outputs` member: those belong to the
    worker deployment and the task document, which is where this now puts them.

    THE SCHEMA IS `/2` BECAUSE THE LIMITS ARE. `execution_limits` is admitted
    only by `SUBMISSION_LIMITS_SCHEMAS`, which is `/2` alone -- so my draft's
    `/1` document carrying limits was refused for the member and would have
    silently dropped this Job's 180-second ceiling if it had not been. The
    member names are the contract's own: `provider_turn_seconds` and
    `verification_command_seconds`, not the `verification_seconds` I invented.

    THE REVIEW STAGE DEPENDS ON THE IMPLEMENTATION, which is how the real
    contract expresses "review after the work" -- `depends_on` with the
    predecessor's job and kind, rather than an ordering this packet asserts.

    THE WORK ID IS THE AUTHORITY-QUALIFIED ONE. `bind` reads it from the
    installed instance; a bare `W236087` is not what a stage names.
    """
    accepted = _accepted()
    # THE PROFILE THE STAGES REQUEST IS THE ONE THE WORKERS OFFER.
    workload = workload_profile(profile)
    return {
        "schema": SUBMISSION_SCHEMA,
        "submission_id": f"submission-{chosen['run_id']}",
        "jobs": [{
            "job_id": job_id,
            "input_digest": input_digest,
            "policy_digest": accepted["policy_digest"],
            "test_scope": [TASK_PATH],
            "terminal_policy": "report-and-hold",
            "execution_limits": {
                "provider_turn_seconds": BOUNDS["turn_seconds"],
                "verification_command_seconds": BOUNDS["verification_seconds"],
            },
            "stages": [
                {"kind": "implementation", "work_id": work_id,
                 "profile_name": workload["name"],
                 "profile_digest": workload["digest"],
                 "depends_on": []},
                {"kind": "review", "work_id": work_id,
                 "profile_name": workload["name"],
                 "profile_digest": workload["digest"],
                 "depends_on": [{"job_id": job_id,
                                 "kind": "implementation"}]},
            ],
        }],
    }


def retention_of(chosen):
    """The retention policy digest EVERY document in this packet names.

    Review 2026-09-29T23-04-18Z captured the first real finalization refusal --
    "old runtime exclusion is unproved" -- and found why: the context profile and
    the generated worker named the profile's retention digest while the enclosing
    composition named the accepted instance's. `provider_context` finalizes by
    querying `intake.cleanup_of` under the PROFILE's retention, and the ending
    records its cleanup under the COMPOSITION's, so a positive cleanup committed
    under one identity could not satisfy the lookup under the other and the use
    stayed held with `custody-invalid`.

    ONE SOURCE, AND IT IS THE CERTIFIED PROFILE, for the same reason the workload
    profile, the image digest and the adapter digest are read from it: the owner
    certified that document, and every other document in the packet is derived.
    """
    return chosen["context_profile"]["retention_policy_digest"]


def bootstrap_document(chosen):
    """The bootstrap input document, IN THE SUPPORTED SCHEMA.

    Review 2026-09-29T21-41-08Z R1 drove the real validator at this document
    and it refused: the supported schema is `baton.v12.stack-bootstrap/1`, and
    my invented `baton.v12.bootstrap-input/1` was a parallel schema nothing
    reads. It also named `jobs`, which a FRESH INSTALL does not: `bootstrap`
    keeps `jobs` and `workers` out of an installation on purpose -- a Work, a
    declared base and a producer are facts about a JOB, supplied when one is
    created -- so naming them here described a different act.

    THE VALUES ARE THE ACCEPTED INSTANCE'S, not composed here. Every member
    comes from `prepare_two_jobs.ACCEPTED`, the provenance-documented constant
    set an accepted two-Job instance was installed from, so the digests are
    measured rather than invented: my first draft hashed strings of my own
    making for `retention_policy_digest` and `instructions_digest`, and wrote
    `profile_version` as text where the accepted document has an integer.

    `checkpoint_profile` IS `git`. I had written `managed-correction`, which is
    not a checkpoint profile this build knows.
    """
    accepted = _accepted()
    return {
        "schema": BOOTSTRAP_SCHEMA,
        "state_root": chosen["stores"]["state_root"],
        "checkpoint_profile": accepted["checkpoint_profile"],
        # THE INTEGRATOR IS A SELECTION, not the accepted instance's. The
        # Authority refused the composition by name when this carried
        # `baton.merge` into a world that had granted `integrate` to somebody
        # else: "a receipt is written by the configured actor and the actor is
        # authorized here".
        "integration_profile": dict(
            accepted["integration_profile"],
            integrator_participant=chosen["participants"]["integration"]),
        "retention_policy_digest": retention_of(chosen),
        "retention_disposition": accepted["retention_disposition"],
        "pool_generation": accepted["pool_generation"],
        "policy_generation": accepted["policy_generation"],
        "receipt_participants": dict(chosen["receipts"]),
    }


def task_document(chosen, *, job_id):
    """The Job's frozen task -- and the ONE place the criteria live.

    Review R1: "Prove that the selected source, worker profiles, credentials
    reference, task and same criteria reach the real deployment and worker
    input." They reach it HERE. The submission contract carries no task and no
    acceptance text -- `documents.STAGE_MEMBERS` is kind, work_id,
    profile_name, profile_digest and depends_on -- so my first draft put the
    task and the criteria in members the real parser refuses outright. This is
    the document the worker receives as `task.json`, and
    `single_worker._held` compares its BYTES against the input manifest's
    `human_contract` digest, which is what makes "the same criteria reached
    both parties" a checkable fact rather than a claim.

    ONE INSTRUCTIONS STRING FOR BOTH STAGES, for the reason
    `PREPARATION-307667.md` gives: the implementer and the reviewer get the
    same complete requirements, so there is one text and the review stage is
    handed this same document rather than a second one that could drift.
    """
    return {
        "schema": TASK_SCHEMA,
        "task_id": f"{chosen['run_id']}-{job_id}",
        "declared_base": chosen["source"]["declared_base"],
        "source_profile": "git-line",
        "source_root": "source",
        "instructions": instructions(),
        "verification": ["python3", "-c",
                         "import pathlib,sys;"
                         "p=pathlib.Path('" + TASK_PATH + "');"
                         "sys.exit(0 if p.is_file() and p.read_text() else 1)"],
    }


# WHAT THE FIRST LIVE RUN SPENT ON READING, measured from the retained session
# transcript rather than estimated: 216 entries, 73 assistant turns and 47 shell
# commands between 09:05:36.852Z and 09:08:29.260Z. Stated in the contract
# because the number is the argument.
FIRST_RUN_READING = "172 seconds"
# AND WHAT A SECOND, INTERRUPTED SESSION SPENT BEFORE WRITING ANYTHING, under a
# contract that stated the bound and asked for a file "within the first
# quarter": 15 further reads and no file (INTERRUPTED-RUN-314263.json).
SECOND_RUN_READING = "51 seconds"


def instructions():
    """The task and the complete criteria, as the bytes the worker reads.

    A REVIEWER READS THIS TEXT TOO. It says what the change is, states every
    acceptance requirement, and says plainly that judging is not the
    implementation stage's job -- W239528's live run learned at an owner's
    expense that a task document which scripts several stages gets handed to
    the implementation role as work to do, and the agent reviewed its own
    change.
    """
    return "\n".join((
        TASK,
        "",
        "`" + TASK_PATH + "` is the only file this Job may add or alter.",
        "",
        "THE COMPLETE ACCEPTANCE REQUIREMENTS, given to the implementer and "
        "the reviewer in these same words:",
        *CRITERIA,
        "",
        "JUDGING IS NOT THIS STAGE. An independent reviewer, a different "
        "principal, checks this document against the requirements above and "
        "against the supported CLI and the current implementation. Do not "
        "grade your own work and do not assume a verdict.",
        "",
        # WHAT THE FIRST LIVE RUN MEASURED, AND WHAT IT COST. Owner reroute
        # 312164/312403 delivered a run that reached the provider; it then spent
        # 172.4 of its 180 allowed seconds READING -- 47 shell commands, 73
        # turns, no repetition and no error -- and was stopped with the file
        # never created. The contract had told it what to write and what would
        # be accepted, and had never told it that the turn was BOUNDED. An agent
        # that does not know it is on a clock reads until the clock ends.
        "YOUR TURN IS BOUNDED AT " + str(BOUNDS["turn_seconds"]) + " SECONDS "
        "OF WALL TIME, and it is stopped at that point whether or not the file "
        "exists. The first run of this Job spent " + FIRST_RUN_READING + " of "
        "its " + str(BOUNDS["turn_seconds"]) + " seconds reading the "
        "repository, wrote nothing, and was stopped with no deliverable at "
        "all.",
        "",
        # WHOSE INSTRUCTION THIS IS. Review 314389 R1: this document is the
        # SHARED task -- the implementation stage and the review stage both
        # receive these same bytes, and a resumed implementer receives them
        # again with its own earlier document already on disk. An unconditional
        # "create a skeleton first" told the reviewer to write the proposal and
        # told a restored implementer to throw its own correction away. So the
        # order is scoped to the one situation it was measured against, and the
        # other two are stated instead of left to inference.
        "WHAT TO DO FIRST DEPENDS ON WHICH OF THREE SITUATIONS YOU ARE IN, and "
        "you can tell from the repository in front of you:",
        "",
        "IF YOU ARE THE IMPLEMENTER AND `" + TASK_PATH + "` DOES NOT EXIST "
        "YET, your FIRST action creates it -- before reading anything beyond "
        "the instructions you were given -- as a skeleton with one section per "
        "numbered requirement above and, under each, a sentence saying what you "
        "still need to confirm. Then read, and rewrite each section as you "
        "learn. Every later minute improves a document that already exists.",
        "",
        "IF YOU ARE THE IMPLEMENTER AND THE FILE ALREADY EXISTS -- you are "
        "resuming after review feedback -- then READ IT FIRST AND PRESERVE IT. "
        "Your work is to correct exactly what the feedback identified and to "
        "improve what is weak, in place. Do NOT reset it to a skeleton, do not "
        "start it again from nothing, and do not discard a section because you "
        "would now write it differently: the bytes already there are the work "
        "the review was given.",
        "",
        "IF YOU ARE THE REVIEWER, you write no part of it. Read the document "
        "and judge it against the numbered requirements above and against the "
        "current implementation, and say what is wrong with what is there. "
        "Creating or rewriting the proposal is not review and is not this "
        "stage's work.",
        "",
        # WHY THE INSTRUCTION IS AN ORDER AND NOT A BUDGET. A SECOND measured
        # session, under an earlier version of this contract that stated the
        # bound and said "write within the first quarter", spent its first 51.6
        # seconds on 15 more reads and had still written nothing. Telling an
        # agent it is on a clock does not change what it does first; telling it
        # what to do first does.
        "A ROUGH COMPLETE DOCUMENT THAT NAMES WHAT IT IS UNSURE OF IS WORTH "
        "EVERYTHING; a perfect understanding with no file is worth nothing, and "
        "is what the first run delivered. A second measured session, told only "
        "that its turn was bounded, still spent its first "
        + SECOND_RUN_READING + " reading and had written nothing -- which is "
        "why the first situation above is an order about your first action "
        "rather than advice about your pace. An early skeleton is not "
        "acceptance and guarantees nothing: it is the floor, and the numbered "
        "requirements are still the whole of what is judged.",
        "",
        "READ WITH A BUDGET, not until you are satisfied. Every requirement "
        "above is checkable against a handful of places, and the requirements "
        "are the whole of what is judged: nothing rewards breadth beyond them. "
        "If something cannot be confirmed in the time you have, WRITE DOWN "
        "WHAT YOU DID NOT CONFIRM rather than spending the turn confirming it "
        "-- an honest gap in a delivered document is a fact a reviewer can act "
        "on.",
    ))


def context_profile_document(chosen):
    """The CANDIDATE context profile this run's qualification grant serves.

    ITS MEMBERS ARE THE CONTRACT'S, not a convenient subset.
    `provider_context._profile` holds a closed document -- seven digests, four
    text fields, `cwd` exactly `/output`, and a positive state allowlist under
    `.claude/projects/` -- and `certify_context_profile` refuses anything else.
    So the selections carry those operands and this composes them; a profile
    assembled from a shorter list would refuse at step 2, after the instance
    was already installed.

    `candidate` AND NOT `production`. The production branch of `_qualified`
    compares a deployment and is a stated coverage limit of this campaign's
    deterministic work; a packet that selected it would claim coverage the
    tests do not have. `held_packet` refuses any other value.

    THE SUBSTITUTED CONVERSATION PATH IS THE POINT. `state_paths` names
    `{conversation_id}.jsonl` under the session schema, which is the file a
    restore consumes -- this is what makes the profile a MANAGED-CONTEXT
    profile rather than a fresh-run one.
    """
    profile = dict(chosen["context_profile"])
    profile["qualification"] = "candidate"
    return profile


# -- the immutable manager source -----------------------------------------

# WHAT A STAGED SOURCE HOLDS, AND WHY IT IS TWO RULES RATHER THAN ONE.
# Modules are not the whole of a distribution: the packages ship FROZEN
# RESOURCES that are read at IMPORT time. Both are staged. What is DERIVED from
# what is staged (`__pycache__`, `.pyc`) and what is build METADATA the run
# never imports (`.egg-info`) is not.
_DERIVED_DIRECTORIES = ("__pycache__",)
_DERIVED_SUFFIXES = (".pyc", ".pyo")
_METADATA_SUFFIXES = (".egg-info",)
# Resources are taken from the PACKAGE root only, and only from inside an
# importable package. `src` is where the distribution's packages live; a build
# output tree, a cache or a scratch run directory beside them is not a package
# and holds no resource this run imports.
_PACKAGE_ROOT = "src"


def _packaged(here, known):
    """`here` is inside an importable package under the package root.

    A directory is inside a package when it holds an `__init__.py` or descends
    from one that does -- which is how `baton_v12/contracts/schema/` qualifies
    while holding no `__init__.py` of its own. Measured from the tree rather
    than from a list of directory names, so a new resource directory beside the
    schema needs no edit here.
    """
    return (here in known
            or os.path.isfile(os.path.join(here, "__init__.py")))


def _source_files(origin):
    """The DECLARED packages' modules and frozen resources, relative to the root.

    OWNER REPORT 311736, and this function held the defect. It staged only
    `.py` files, so the staged source lacked
    `src/baton_v12/contracts/schema/worker-control-1.0.schema.json`. The
    distribution SHIPS that file and `agent-session-1.0.schema.json` --
    `tools.bootstrap.EXPECTED_ASSETS` names both, and the tool says they "are
    read at import time, so a bundle without them refuses every document it is
    given". The operator's bootstrap therefore failed, and `prepare-work`,
    `bind` and `check` then failed for want of the documents bootstrap never
    wrote. A MODULE LIST IS NOT A SOURCE TREE.

    WHAT IS STAGED IS WHAT IS DECLARED. `IMPORTED_PACKAGES` already names what
    this run imports, so the walk follows those packages where they live under
    the import roots, plus any module sitting directly in a root. Inside a
    declared package, modules AND frozen resources are staged; a directory that
    is not a declared package is not walked at all.

    WHY NOT `EVERYTHING BUT DERIVED`, WHICH I WROTE FIRST AND MEASURED. Against
    the real origin `/home/sl/src/baton/v12/python` that rule staged 2874
    further files and 132M: a whole PyInstaller bundle under `build/out/distro`,
    a `.pytest_cache`, and 44 `v12-w71917-*` scratch run directories. Even
    restricted to `.py` it staged 378 files rather than the 106 the accepted
    records measured, because `build/lib` and those scratch trees hold modules
    too. Staging build output and run state into a source bundle is a worse
    defect than the one being corrected. The declared rule stages 108 from that
    same origin: the 106 modules the accepted packets recorded, and the two
    frozen assets that were missing.

    A `.pyc` is neither copied nor measured: it is derived, it is not what a
    reviewer read, and `PYTHONDONTWRITEBYTECODE` keeps the staged tree clean.
    """
    found = {}
    homes = {}
    for root in IMPORT_ROOTS:
        base = os.path.normpath(os.path.join(origin, root))
        if not os.path.isdir(base):
            _refuse(f"the manager source origin has no {root!r} import root "
                    f"at {base!r}")
        # A module directly in a root is staged; the root itself is not walked,
        # so a build tree or a scratch run directory beside the packages is
        # never copied.
        for name in sorted(os.listdir(base)):
            whole = os.path.join(base, name)
            if name.endswith(".py") and os.path.isfile(whole):
                found[os.path.relpath(whole, origin)] = whole
        for package in IMPORTED_PACKAGES:
            home = os.path.join(base, package)
            if not os.path.isdir(home):
                continue
            homes.setdefault(package, home)
            found.update(_package_files(origin, home,
                                        resources=root == _PACKAGE_ROOT))
    absent = [one for one in IMPORTED_PACKAGES if one not in homes]
    if absent:
        _refuse(f"the manager source origin {origin!r} holds no "
                f"{', '.join(absent)} package under {', '.join(IMPORT_ROOTS)}, "
                f"so the run it stages could not import what it declares")
    if not found:
        _refuse(f"the manager source origin {origin!r} holds no module to run")
    return found


def _package_files(origin, home, *, resources):
    """One declared package's files, keyed relative to the staged root."""
    found = {}
    known = set()
    for here, directories, names in os.walk(home):
        directories[:] = [one for one in sorted(directories)
                          if one not in _DERIVED_DIRECTORIES
                          and not one.endswith(_METADATA_SUFFIXES)]
        packaged = resources and _packaged(here, known)
        if packaged:
            known.update(os.path.join(here, one) for one in directories)
        for name in sorted(names):
            if name.endswith(_DERIVED_SUFFIXES):
                continue
            if not name.endswith(".py") and not packaged:
                continue
            whole = os.path.join(here, name)
            if os.path.islink(whole) or not os.path.isfile(whole):
                # A LINK IS NOT A FILE THIS COPIES. Following one would stage
                # bytes from outside the tree that was reviewed.
                continue
            found[os.path.relpath(whole, origin)] = whole
    return found


# WHAT THE STAGED TREE IS ASKED, in its own interpreter with its own import
# path. `baton_v12.contracts.frozen` reads its two schema documents at MODULE
# level, and `tools.bootstrap.EXPECTED_ASSETS` names what the distribution
# ships -- so the staged tree can be asked BOTH what it needs and whether it
# can load it, and neither answer is retyped here.
_REPORT = """
import json, os, pathlib, sys
import tools.bootstrap as bootstrap
import tools.stage_execution as stage_execution
_checkout = getattr(stage_execution, "_checkout", None)
import baton_v12
import baton_v12.contracts.frozen as frozen
package = os.path.dirname(os.path.realpath(baton_v12.__file__))
print(json.dumps({
    "package": os.path.basename(package),
    "checkout": _checkout() if _checkout is not None else None,
    "schema_directory": os.path.relpath(str(frozen._SCHEMA_DIRECTORY),
                                        package),
    "assets": sorted(bootstrap.EXPECTED_ASSETS),
    "bootstrap_schema": bootstrap.SCHEMA,
    "loaded": {"worker-control-1.0": len(frozen.WORKER_CONTROL_BYTES),
               "agent-session-1.0": len(frozen.AGENT_SESSION_BYTES)},
}))
"""


def staged_report(staged):
    """ASK THE STAGED TREE, in a child whose import path is that tree.

    OWNER REPORT 311736 was an IMPORT failure -- `frozen.py` reads its schema
    documents at module level -- and the one honest way to know a staged tree
    can import is to import it. The child's path is the staged source and
    nothing else, which is exactly the condition the run executes under, so
    this refuses at the copy what the operator otherwise meets at the
    installer.

    It runs no store, no engine and no provider: one interpreter, two imports.
    """
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                       PYTHONPATH=os.path.join(staged, _PACKAGE_ROOT)
                       + os.pathsep + staged)
    try:
        done = subprocess.run([sys.executable, "-B", "-c", _REPORT],
                              capture_output=True, text=True, timeout=300,
                              cwd=staged, env=environment)
    except (OSError, subprocess.SubprocessError) as failure:
        _refuse(f"the staged manager source at {staged!r} could not be asked "
                f"what it imports ({failure})")
    if done.returncode != 0:
        said = (done.stdout + done.stderr).strip().splitlines()
        _refuse(f"the staged manager source at {staged!r} DOES NOT IMPORT with "
                f"its own tree as the import path: "
                f"{said[-1] if said else 'no output'}. "
                f"`baton_v12.contracts.frozen` reads its schema documents at "
                f"module level, so a staged tree that cannot import them "
                f"refuses every document it is given -- which the operator "
                f"meets as a bootstrap failure several steps after the cause.")
    try:
        return json.loads(done.stdout)
    except ValueError:
        _refuse(f"the staged manager source at {staged!r} did not answer with "
                f"one document when asked what it imports")


def verify_staged_assets(staged, report=None):
    """The staged tree carries the frozen assets it says it needs.

    The names and their location come from the STAGED TREE ITSELF through
    `staged_report`, so nothing here is a list that could drift from the
    product, and a loader that moves its schema directory moves this with it.
    """
    report = staged_report(staged) if report is None else report
    inside = os.path.join(_PACKAGE_ROOT, report["package"],
                          report["schema_directory"])
    absent = sorted(os.path.join(inside, name + ".schema.json")
                    for name in report["assets"]
                    if not os.path.isfile(os.path.join(
                        staged, inside, name + ".schema.json")))
    if absent:
        _refuse(f"the staged manager source at {staged!r} is missing the frozen "
                f"schema asset(s) {', '.join(absent)}. "
                f"`tools.bootstrap.EXPECTED_ASSETS` declares them and "
                f"`baton_v12.contracts.frozen` reads them at IMPORT time, so "
                f"this source refuses every document it is given -- which "
                f"surfaces as a bootstrap failure several steps later rather "
                f"than here.")
    return sorted(report["assets"])


def verify_instance_outside_checkout(chosen, report):
    """The instance is not inside the tree the STAGED CODE calls its checkout.

    MEASURED, NOT REASONED ABOUT, under claim 311743 by running the staged tree
    against `tools.bootstrap`. `stage_execution._checkout()` answers three
    parents above its own file, so a source staged at
    `<staging_root>/manager-source` makes the checkout `dirname(staging_root)`
    -- and `bootstrap.admit` refuses any destination inside it, because the
    whole point of an installed instance is that development in the code's tree
    cannot change a running Job.

    THE DELIVERED PLAN PUT BOTH UNDER `/home/sl/baton-instances`: the staged
    source at `managed-correction-309356-source` and the instance at
    `managed-correction-309356`, siblings, so the checkout the staged code
    answers CONTAINS the instance and step 1 could not have succeeded whatever
    the assets did. The owner met the asset failure first, which is the only
    reason this went unseen. The answer comes from the staged tree itself, so a
    build that changes the rule changes this check with it.
    """
    tree = report.get("checkout")
    if not tree:
        return None
    tree = os.path.realpath(tree)
    instance = os.path.realpath(chosen["instance_root"])
    if instance == tree or instance.startswith(tree.rstrip("/") + os.sep):
        _refuse(f"the instance root {chosen['instance_root']!r} is INSIDE the "
                f"tree the staged code answers as its checkout ({tree!r}), so "
                f"`tools.bootstrap` will refuse the destination: an installed "
                f"instance exists so that development in the code's own tree "
                f"cannot change a running Job. The staged source sits at "
                f"{chosen['staging_root']!r}, and `stage_execution._checkout()` "
                f"answers three parents above its own file -- so choose a "
                f"`staging_root` whose PARENT does not contain the instance "
                f"root, rather than a sibling of it.")
    return tree


def asset_locations(report):
    """Where the report says each frozen asset sits in a staged tree."""
    inside = os.path.join(_PACKAGE_ROOT, report["package"],
                          report["schema_directory"])
    return {name: os.path.join(inside, name + ".schema.json")
            for name in report["assets"]}


def staged_source(origin, destination):
    """COPY the modules this run will import, then MEASURE what was copied.

    Measured from the copy and never from the origin. Hashing the origin and
    copying it are two acts, and a tree that changed between them would be
    bound to bytes nowhere on disk -- which is the drift this exists to refuse.
    """
    origin = os.path.realpath(origin)
    destination = os.path.realpath(destination)
    if _inside(origin, destination) or _inside(destination, origin):
        _refuse(f"the staged source {destination!r} and its origin {origin!r} "
                f"nest; a copy inside what it copies is not a copy")
    for name, whole in sorted(_source_files(origin).items()):
        target = os.path.join(destination, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(whole, target)
    files = {name: digest_of(os.path.join(destination, name))
             for name in sorted(_source_files(destination))}
    # REFUSED AT THE COPY, not at the installer. The owner's run discovered a
    # missing asset as a bootstrap failure with three later steps failing after
    # it; this is the moment the omission exists.
    report = staged_report(destination)
    assets = verify_staged_assets(destination, report)
    verify_nothing_unbound(destination, files)
    for name, relative in sorted(asset_locations(report).items()):
        if relative not in files:
            _refuse(f"the staged manager source at {destination!r} imports the "
                    f"frozen asset {relative!r} that NO DIGEST BINDS; a packet "
                    f"cannot promise the run executes reviewed bytes over a "
                    f"resource it does not measure")
    return {"path": destination, "packages": list(IMPORTED_PACKAGES),
            "file_count": len(files), "files": files,
            "frozen_assets": assets}


# -- the filesystem roots the RUN needs -------------------------------------
#
# OWNER REROUTE 312164, measured from a LIVE run: bootstrap, `prepare-work`,
# `bind` and `check` all succeeded and the supervisor then failed inside
# `baseline.prepare` at `configure_workspace_storage`, because
# `<instance>/run/workspaces` did not exist. Nothing created it. `tools.bootstrap`
# creates `stores`, `repository`, `logs`, `state`, the state root and the
# destination -- not these -- and the accepted CONNECTED FIXTURE creates them
# itself (`os.makedirs(self.storage)`, `os.makedirs(producer["launch_home"])`),
# which is exactly why no deterministic case ever noticed: the fixture supplied
# what the operator sequence omitted.
#
# ONLY THESE TWO, and that is measured rather than assumed. `launch_home` and
# `credential_home` are created BY THE PRODUCT when it uses them --
# `launch.materialize` calls `os.makedirs(root, mode=0o700, exist_ok=False)` and
# `credentials` its own `os.makedirs(..., mode=VOLATILE_DIR)` -- and the
# per-attempt workspace roots are established by `workspaces` itself with
# `adopt_workspace_group`. The two below are the ones the product requires to
# ALREADY EXIST when it is configured, so they are the deployment's to provide.


# WHICH RULE DECIDES EACH ROOT, in one place so a refusal reads the same
# whether it came from the selection or from the packet's own record. The live
# failure named a path and nothing else, and left an operator to work out which
# of five roots it was, which rule wanted it and who was supposed to make it.
_ROOT_RULES = {
    "workspace_storage": {
        "required_by": "baton_v12.worker_manager.workspaces."
                       "configure_workspace_storage, through "
                       "check_workspace_storage",
        "what_the_rule_requires": "an absolute canonical path that is a real "
                                  "directory -- asked with lstat, so a link is "
                                  "refused -- owned by the uid the manager "
                                  "runs as",
        "why_it_must_pre_exist": "`configure_workspace_storage` is the "
                                 "deployment's act and creates nothing; this "
                                 "is where the live run stopped",
    },
    "context_storage": {
        "required_by": "baton_v12.worker_manager.context_delivery."
                       "configure_context_storage, through _open_absolute and "
                       "_private",
        "what_the_rule_requires": "an absolute canonical path whose whole "
                                  "ancestry can be opened, owned by the "
                                  "running uid, readable AND writable by the "
                                  "owner, with no group or other permission "
                                  "bit set at all",
        "why_it_must_pre_exist": "the same act configures it immediately after "
                                 "the workspace store, so a run that got past "
                                 "the first would have stopped here",
    },
}


def filesystem_roots(chosen):
    """Each root the run needs first, with the rule that decides it.

    THE MODES COME FROM THE PRODUCT. The workspace store is created with
    `workspaces.WORKSPACE_DIR` -- the same mode `adopt_workspace_group`
    establishes on the roots the manager itself creates inside it, so the store
    is exactly as reachable as its contents and no more: the configured
    workspace group may traverse it, nothing else may. The private-context store
    is `0o700` because `context_delivery._private` refuses ANY group or other
    bit on it.
    """
    from baton_v12.worker_manager import workspaces

    return (
        dict(_ROOT_RULES["workspace_storage"],
             role="workspace_storage",
             path=chosen["workspace_storage"],
             mode=workspaces.WORKSPACE_DIR,
             group=_accepted()["workspace_group"]),
        dict(_ROOT_RULES["context_storage"],
             role="context_storage",
             path=chosen["context_storage"]["path"],
             mode=0o700,
             group=None),
    )


# HOW A DIRECTORY IS OPENED HERE, and it is the whole of review 312285's R1.
# `O_NOFOLLOW` with `O_DIRECTORY` refuses a symlink at the name with ELOOP
# instead of opening what it points at, so every component is the component and
# not a redirection. The mode and the group are then established on the
# DESCRIPTOR this walk opened -- `fchmod`/`fchown`, never `chmod`/`chown` by
# name -- because a name can be something else by the time the second call
# happens.
_DIR_OPEN = (os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
             | getattr(os, "O_CLOEXEC", 0))
# The mode an absent ANCESTOR is created with. Only the leaf's mode is a
# product rule; an ancestor inside the instance is left as permissive as the
# ones `tools.bootstrap` creates beside it, because the worker's group must be
# able to traverse `run/` to reach the workspace store inside it.
_ANCESTOR_DIR = 0o755


def _open_no_follow(place, *, role, create):
    """Walk `place` component by component, NEVER following a link.

    REVIEW 312285 R1, and it was a real defect with a real effect. This used
    `os.makedirs(exist_ok=True)` and then `os.chmod`/`os.chown` BY NAME -- all
    three of which follow a symlink -- and verified afterwards. The reviewer
    pointed the selected private-context root at an unrelated `0755` directory
    and measured the consequence: creation changed THAT directory to `0700` and
    only then did validation refuse. A refusal after the change is not a
    refusal, and a bind the packet correctly rejects had already modified a path
    it was never given.

    So the type check comes FIRST and is structural: a link or a non-directory
    at any component refuses here, before anything is created and before any
    mode or group is touched. Absent components are created with `mkdir` at the
    parent's own descriptor, which cannot be redirected between the check and
    the creation.
    """
    if not os.path.isabs(place) or os.path.normpath(place) != place.rstrip("/"):
        _refuse(f"the {role} root {place!r} is not an absolute canonical path")
    parts = [one for one in place.split(os.sep) if one]
    if not parts:
        _refuse(f"the {role} root {place!r} names no directory")
    handle = os.open(os.sep, _DIR_OPEN)
    created = False
    try:
        for index, part in enumerate(parts):
            leaf = index == len(parts) - 1
            whole = os.sep + os.sep.join(parts[:index + 1])
            try:
                child = os.open(part, _DIR_OPEN, dir_fd=handle)
            except OSError as failure:
                # WHICH IT IS, ASKED WITH `lstat`, WHICH CHANGES NOTHING AND
                # FOLLOWS NOTHING. `O_NOFOLLOW | O_DIRECTORY` opens the LINK
                # rather than its target, so a link to a directory arrives here
                # as ENOTDIR rather than ELOOP -- both are refusals, and an
                # operator needs to be told which one they have.
                if failure.errno in (errno.ELOOP, errno.ENOTDIR):
                    try:
                        found = os.lstat(whole)
                        linked = stat.S_ISLNK(found.st_mode)
                    except OSError:
                        linked = failure.errno == errno.ELOOP
                    if linked:
                        _refuse(f"the {role} root {place!r} passes through a "
                                f"SYMLINK at {whole!r}; a link at that name is "
                                f"a directory somebody else chose, and this "
                                f"step establishes the deployment's own. "
                                f"NOTHING WAS CHANGED: no directory was "
                                f"created and no mode or group was touched, "
                                f"here or at whatever the link points at")
                    _refuse(f"the {role} root {place!r} passes through "
                            f"{whole!r}, which is not a directory. NOTHING WAS "
                            f"CHANGED")
                if failure.errno != errno.ENOENT:
                    _refuse(f"the {role} root {place!r} could not be opened at "
                            f"{whole!r} ({type(failure).__name__}: "
                            f"{failure.strerror}). NOTHING WAS CHANGED")
                if not create:
                    _refuse(f"the {role} root {place!r} does not exist at "
                            f"{whole!r}")
                try:
                    os.mkdir(part, 0o700 if leaf else _ANCESTOR_DIR,
                             dir_fd=handle)
                except OSError as making:
                    _refuse(f"the {role} root {place!r} could not be created "
                            f"at {whole!r} ({type(making).__name__}: "
                            f"{making.strerror})")
                # OPENED NO-FOLLOW IMMEDIATELY AFTER CREATING IT, so what is
                # measured and modified below is what this call made.
                child = os.open(part, _DIR_OPEN, dir_fd=handle)
                created = created or leaf
            os.close(handle)
            handle = child
    except BaseException:
        os.close(handle)
        raise
    return handle, created


def create_filesystem_roots(chosen):
    """Establish the roots, EXACTLY, before anything registers them.

    `os.mkdir` filters its mode through the umask -- the product says so itself
    where it corrected the same thing -- so the mode is established with
    `os.fchmod`, which is exact, and the group with `os.fchown(fd, -1, gid)`,
    which an unprivileged owner may do for a group it belongs to. Both act on
    the descriptor `_open_no_follow` pinned, so neither can be redirected to
    something this program was not given.

    Repeating this is a no-op: an existing root is re-affirmed rather than
    replaced, and nothing is ever deleted here.
    """
    established = []
    for root in filesystem_roots(chosen):
        place, mode = root["path"], root["mode"]
        handle, created = _open_no_follow(place, role=root["role"],
                                          create=True)
        try:
            held = os.fstat(handle)
            if held.st_uid != os.getuid():
                _refuse(f"the {root['role']} root {place!r} is owned by uid "
                        f"{held.st_uid} and this step runs as uid "
                        f"{os.getuid()}; a directory this deployment does not "
                        f"own is not one it establishes. NOTHING WAS CHANGED")
            try:
                os.fchmod(handle, mode)
                if root["group"] is not None and held.st_gid != root["group"]:
                    os.fchown(handle, -1, root["group"])
            except OSError as failure:
                _refuse(f"the {root['role']} root {place!r} could not be "
                        f"established as mode {oct(mode)}"
                        + (f" in group {root['group']}"
                           if root["group"] is not None else "")
                        + f": {type(failure).__name__}: {failure.strerror}. "
                        f"{root['required_by']} requires it to exist already, "
                        f"and this is the step that provides it")
            measured = os.fstat(handle)
        finally:
            os.close(handle)
        established.append({"role": root["role"], "path": place,
                            "mode": oct(stat.S_IMODE(measured.st_mode)),
                            "uid": measured.st_uid, "gid": measured.st_gid,
                            "created": created})
    return established


def verify_filesystem_roots(chosen=None, *, roots=None):
    """Hold every root to the PRODUCT'S OWN rule, not to a rule restated here.

    `check_workspace_storage` and `_open_absolute`/`_private` are the functions
    the run itself calls; driving them is the only check that cannot drift from
    what `baseline.prepare` will decide. A refusal names the root, the rule and
    the step that establishes it, because the live failure named a path and left
    an operator to work out which of five roots it was and who owned it.
    """
    try:
        from baton_v12.worker_manager import context_delivery, workspaces
        from baton_v12.contracts import ContractRefusal
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the filesystem "
                f"roots cannot be proved with the rules that will read them "
                f"({failure})")
    if roots is None:
        wanted = filesystem_roots(chosen)
    else:
        # DRIVEN FROM THE PACKET'S OWN RECORD, so `check` and the supervisor's
        # preflight prove the same roots `bind` established without needing the
        # selection document beside them.
        known = {one["role"]: one for one in filesystem_roots(chosen)} \
            if chosen is not None else {}
        wanted = []
        for one in roots:
            rule = dict(_ROOT_RULES.get(one["role"], {}),
                        **known.get(one["role"], {}))
            wanted.append(dict(rule, role=one["role"], path=one["path"]))
    held = []
    for root in wanted:
        place = root["path"]
        if root["role"] not in ("workspace_storage", "context_storage"):
            _refuse(f"the packet binds a filesystem root of unknown role "
                    f"{root['role']!r}; this program knows the workspace store "
                    f"and the private-context store, and a root it cannot "
                    f"place is one it cannot prove")
        try:
            if root["role"] == "workspace_storage":
                workspaces.check_workspace_storage(place)
            else:
                handle, _pins = context_delivery._open_absolute(place)
                try:
                    context_delivery._private(handle, writable=True)
                finally:
                    os.close(handle)
        except ContractRefusal as refusal:
            _refuse(f"the {root['role']} root {place!r} is not one this run "
                    f"can be configured with: {refusal}. The rule is "
                    f"{root['required_by']}, which requires "
                    f"{root['what_the_rule_requires']}. `bind` establishes it; "
                    f"re-run the bind step for this instance rather than "
                    f"making it by hand")
        measured = os.stat(place)
        held.append({"role": root["role"], "path": place,
                     "mode": oct(stat.S_IMODE(measured.st_mode)),
                     "uid": measured.st_uid, "gid": measured.st_gid,
                     "proved_by": root["required_by"]})
    return held


def verify_nothing_unbound(staged, files):
    """The staged tree holds EXACTLY what the manifest binds, and nothing else.

    MEASURED FROM THE OWNER'S PARTIAL PREPARATION, read-only, under claim
    311743: `<staging_root>/manager-source` holds 376 `.py` files and no
    resource at all -- the whole of `build/lib`, `tests/`, and 44
    `v12-w71917-*` scratch run trees, because the old walk followed the `.`
    import root into everything beside the packages. The corrected walk stages
    108.

    WHY AN EXTRA FILE IS A REFUSAL RATHER THAN A TIDY-UP. A copy into a
    directory that already holds a different staging leaves files NO DIGEST
    BINDS, and `PYTHONPATH` makes them importable; a packet whose promise is
    "this runs the reviewed bytes" cannot keep it over a tree with unmeasured
    modules in it. Deleting them is not this program's act either -- it did not
    put them there and they may be someone's evidence. So it refuses, names the
    count and the first few, and the recovery is a FRESH staging root.
    """
    stale = []
    for here, directories, names in os.walk(staged):
        directories[:] = [one for one in sorted(directories)
                          if one not in _DERIVED_DIRECTORIES]
        for name in sorted(names):
            if name.endswith(_DERIVED_SUFFIXES):
                continue
            relative = os.path.relpath(os.path.join(here, name), staged)
            if relative not in files:
                stale.append(relative)
    if stale:
        _refuse(f"the staged manager source at {staged!r} holds "
                f"{len(stale)} file(s) THIS STAGING DID NOT WRITE and no "
                f"digest binds -- {', '.join(stale[:5])}"
                f"{' ...' if len(stale) > 5 else ''}. `PYTHONPATH` makes them "
                f"importable, so the packet could not promise the run executes "
                f"the reviewed bytes. Nothing is deleted here: stage into a "
                f"FRESH `staging_root` and leave this tree as it is.")
    return len(files)


# -- the packet ------------------------------------------------------------

def _read_submission(text):
    """The submission, OWNED BY THE PRODUCT'S OWN PARSER.

    Reaching for `documents.read_submission` rather than restating its rules is
    the whole correction here: review 2026-09-29T21-41-08Z R1 drove it at my
    generated document and it refused at the first member, because I had
    written a parallel submission schema nothing reads.
    """
    try:
        from baton_v12.job_manager.documents import read_submission
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the submission "
                f"cannot be proved with the parser that will read it "
                f"({failure}). Run with PYTHONPATH naming the staged source's "
                f"`src` and its root.")
    from baton_v12.contracts import ContractRefusal

    try:
        return read_submission(text)
    except ContractRefusal as refusal:
        _refuse(f"the generated Job submission is not one this build accepts: "
                f"{refusal}")


def certified_digest(profile):
    """The profile digest `certify_context_profile` will answer.

    ASKED OF THE MANAGER, NOT COMPUTED HERE. `certify_context_profile` keys the
    certification on `digest(_profile(profile))` -- a normalized document under
    the contracts' canonical text -- which is NOT the profile file's sha256. A
    first draft of this module bound `"sha256:" + <file digest>`, and the
    accepted single-implementation packet shows the two values differing in its
    own `context` block; `baseline.prepare` compares the certified digest
    against the packet's and would have refused the run AFTER the instance was
    installed and the grant minted.

    So this imports the reader and uses it. A tree that cannot be imported is
    refused with the reason, rather than guessed around.
    """
    try:
        from baton_v12.contracts import digest
        from baton_v12.worker_manager.provider_context import _profile
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the certified "
                f"profile digest cannot be computed the way the manager "
                f"computes it ({failure}). Run `bind` with PYTHONPATH naming "
                f"the staged source's `src` and its root, which is what "
                f"`stage`'s commands already set.")
    return digest(_profile(profile))


def held_packet(path, *, supervisor=None):
    """Read the packet and PROVE every artifact it binds, before anything opens.

    The single-implementation baseline's own discipline, with this Job's bounds
    and this Job's two stages. Nothing durable is touched and no store is
    opened: a packet whose staged modules, deployment configuration,
    submission, context profile, runtime, image or supervisor have moved since
    it was reviewed is refused with the artifact named -- which is the
    difference between running a reviewed packet and running whatever happens
    to be on disk under its name.
    """
    with open(path, "rb") as handle:
        packet = json.loads(handle.read().decode("utf-8"))
    _document(packet, f"the managed-correction packet at {path!r}", _PACKET)
    if packet["schema"] != PACKET_SCHEMA:
        _refuse(f"this reads {PACKET_SCHEMA!r} and the packet names "
                f"{packet['schema']!r}")

    bounds = _document(packet["bounds"], "the packet's bounds", _BOUNDS)
    for name, want in sorted(BOUNDS.items()):
        if bounds[name] != want:
            _refuse(f"this Job's {name} is {want!r} and the packet declares "
                    f"{bounds[name]!r}; the bounds are what the supervisor "
                    f"enforces, and widening them in the packet would widen "
                    f"the run without widening the review")
    if bounds["cleanup_seconds"] >= bounds["total_seconds"]:
        _refuse("the reserved cleanup bound is INSIDE the overall bound, not "
                "beside it")

    deployment = _document(packet["deployment"], "the packet's deployment",
                           _DEPLOYMENT)
    _pin(deployment["config_path"], deployment["config_sha256"],
         "the deployment configuration")

    context = _document(packet["context"], "the packet's context selection",
                        _CONTEXT)
    _pin(context["profile_path"], context["profile_sha256"],
         "the context profile document")
    if type(context["excluded_roots"]) is not list \
            or not all(type(one) is str and os.path.isabs(one)
                       for one in context["excluded_roots"]):
        _refuse("the context storage's excluded roots are absolute paths")
    if type(context["runtime_uid"]) is not int or context["runtime_uid"] < 0:
        _refuse("the context storage names one runtime uid")
    if context["qualification"] != "candidate":
        _refuse(f"this packet drives ONE candidate qualification run and its "
                f"profile is {context['qualification']!r}; the production "
                f"comparison is a stated coverage limit of this campaign, not "
                f"a path this packet may select")
    with open(context["profile_path"], "rb") as handle:
        profiled = json.loads(handle.read().decode("utf-8"))
    _document(profiled, "the certified context profile", _PROFILE)
    if profiled["qualification"] != context["qualification"] \
            or profiled["layout_version"] != context["layout_version"]:
        _refuse("the packet's context selection and the profile document it "
                "binds disagree about the qualification or the layout")
    # THE COMPOSITION, AGAIN AND ON THE BOUND BYTES. `held_selections` checked
    # the operands; this checks the document the run will certify, because the
    # packet is what the supervisor reads and the selections are not.
    image = packet["worker_image"]
    if type(image) is not dict:
        _refuse("the packet's worker image is one document")
    if profiled["image_digest"] != image.get("config_digest"):
        _refuse(f"the certified profile is composed against image "
                f"{profiled['image_digest']!r} and this packet binds "
                f"{image.get('config_digest')!r}")
    if profiled["adapter_digest"] != image.get("adapter_descriptor"):
        _refuse(f"the certified profile names adapter descriptor "
                f"{profiled['adapter_digest']!r} and this packet binds "
                f"{image.get('adapter_descriptor')!r}")
    if not any("{conversation_id}" in one for one in profiled["state_paths"]):
        _refuse("the certified profile retains no conversation file, so this "
                "packet's correction could restore nothing")

    submission = _document(packet["submission"], "the packet's submission",
                           _SUBMISSION)
    _pin(submission["path"], submission["sha256"], "the Job submission")
    _pin(submission["task_path"], submission["task_sha256"],
         "the Job's task document")
    _pin(submission["manifest_path"], submission["manifest_sha256"],
         "the worker's input manifest")
    # THE REAL PARSER OWNS THE SUBMISSION, not a member walk of this module's
    # own design. Review R1 found the whole shape invented, so the check is
    # now the product's: `read_submission` normalizes and refuses, and what
    # follows reads the OWNED document rather than the bytes.
    with open(submission["path"], "r", encoding="utf-8") as handle:
        submitted = _read_submission(handle.read())
    jobs = submitted["jobs"]
    if len(jobs) != 1 or jobs[0]["job_id"] != submission["job_id"]:
        _refuse(f"this packet serves exactly one Job "
                f"{submission['job_id']!r} and its submission does not")
    kinds = [stage["kind"] for stage in jobs[0]["stages"]]
    if kinds != ["implementation", "review"]:
        _refuse(f"this Job is one implementation and one independent review; "
                f"its submission carries stages {kinds!r}")
    stages = {stage["kind"]: stage for stage in jobs[0]["stages"]}
    # THE ORDERING IS THE CONTRACT'S OWN. `depends_on` is how a review stage
    # says it follows the work; asserting the order beside the document would
    # leave the manager free to admit them in either.
    if [(one["job_id"], one["kind"])
            for one in stages["review"]["depends_on"]] \
            != [(submission["job_id"], "implementation")]:
        _refuse("the review stage does not depend on this Job's "
                "implementation, so nothing orders the review after the work "
                "it reviews")
    if stages["implementation"]["depends_on"]:
        _refuse("the implementation stage depends on something; this Job's "
                "opening invocation waits for nothing")
    # THE DECLARED BOUNDS SURVIVED THE PARSER. A limit the contract drops is a
    # limit this run does not have, whatever the packet says.
    limits = jobs[0].get("execution_limits") or {}
    if limits.get("provider_turn_seconds") != BOUNDS["turn_seconds"] \
            or limits.get("verification_command_seconds") \
            != BOUNDS["verification_seconds"]:
        _refuse(f"the submitted Job's execution limits are {limits!r} and this "
                f"packet declares a {BOUNDS['turn_seconds']}s provider turn "
                f"and a {BOUNDS['verification_seconds']}s verification command")
    if jobs[0]["input_digest"] != submission["input_digest"]:
        _refuse("the submitted Job's input digest is not the one the packet "
                "binds")
    for stage in jobs[0]["stages"]:
        if stage["work_id"] != submission["work_id"]:
            _refuse(f"the {stage['kind']} stage names Work "
                    f"{stage['work_id']!r} and the packet binds "
                    f"{submission['work_id']!r}")
    if submission["review_participant"] \
            == submission["implementation_participant"]:
        _refuse("the producer and the reviewer are one participant; this Job "
                "answers whether REAL independent feedback drives a "
                "correction, which a self-review cannot")

    # THE COMPLETE CRITERIA, CHECKED WHERE THEY ACTUALLY LIVE. R1: the
    # submission carries no acceptance text, so a packet checking two stages'
    # `acceptance_requirements` was comparing members the parser refuses. They
    # reach the worker as the task document's instructions, and the input
    # manifest's human contract is those exact bytes -- which is what makes
    # "the same complete requirements reached both parties" checkable.
    with open(submission["task_path"], "rb") as handle:
        task_bytes = handle.read()
    task = json.loads(task_bytes.decode("utf-8"))
    if task.get("schema") != TASK_SCHEMA:
        _refuse(f"the task document is {task.get('schema')!r} and the worker "
                f"reads {TASK_SCHEMA!r}")
    if task.get("declared_base") != packet["fixture"]["declared_base"]:
        _refuse("the task document declares a different base from the "
                "packet's fixture")
    said = task.get("instructions")
    if type(said) is not str or not said:
        _refuse("the task document carries no instructions, so the Job states "
                "no requirement")
    absent = [one for one in CRITERIA if one not in said]
    if absent:
        _refuse(f"the task document omits {len(absent)} of this Job's "
                f"acceptance requirements; `PREPARATION-307667.md` forbids a "
                f"hidden criterion, and a producer held to a requirement it "
                f"never received is a manufactured correction")
    with open(submission["manifest_path"], "rb") as handle:
        manifest = json.loads(handle.read().decode("utf-8"))
    contract = manifest.get("human_contract") or {}
    if contract.get("content_digest") != "sha256:" + hashlib.sha256(
            task_bytes).hexdigest() or contract.get("bytes") != len(task_bytes):
        _refuse("the worker's input manifest does not bind these task bytes as "
                "its human contract, so the requirements the worker receives "
                "are not the ones this packet checked")
    if context["job_id"] != submission["job_id"]:
        _refuse("the qualification grant and the submission name different "
                "Jobs; one grant serves exactly one Job")

    # THE GENERATED COMPOSITION, PROVED BY THE PREFLIGHT THAT WILL READ IT.
    # Review 2026-09-29T22-02-59Z item 1: pinning bytes says nothing about
    # whether the deployment is one this build composes, so `held_packet` drives
    # `single_worker._held` at both configurations before a store opens.
    composition = _document(packet["composition"],
                            "the packet's composition", _COMPOSITION)
    with open(deployment["config_path"], "rb") as handle:
        composed = json.loads(handle.read().decode("utf-8"))
    workers = {one.get("worker_id"): one.get("deployment")
               for one in composed.get("workers") or []}
    if sorted(workers) != list(composition["workers"]) \
            or sorted(workers) != ["implementation-worker", "review-worker"]:
        _refuse(f"this run is one producer and one independent reviewer; the "
                f"composition configures {sorted(workers)}")
    verify_workers(workers)
    verify_composition(composed, checkout=boundary_of(packet))
    # THE STAGE'S REQUEST AND THE WORKER'S OFFER ARE ONE FACT, checked ACROSS the
    # two documents. Review 2026-09-29T22-36-24Z: the connected run deferred
    # forever because they disagreed -- "no worker this deployment configures for
    # the 'implementation' stage can serve Job 'job-a': {'implementation-worker':
    # ['the workload profile', 'the workload profile digest']}" -- with zero
    # admissions and no runtime. Neither document alone is wrong; the pair is.
    offered = {(one.get("profile_name"), one.get("profile_digest"))
               for one in workers.values()}
    requested = {(one["profile_name"], one["profile_digest"])
                 for one in jobs[0]["stages"]}
    # AND THE RETENTION IDENTITY IS ONE ACROSS EVERY DOCUMENT. Review
    # 2026-09-29T23-04-18Z: the finalizer queries `intake.cleanup_of` under the
    # PROFILE's retention digest while the ending records cleanup under the
    # COMPOSITION's, so two identities leave a positive cleanup unable to satisfy
    # the lookup and the context use held with `custody-invalid`.
    retentions = {profiled["retention_policy_digest"],
                  composed.get("retention_policy_digest")}
    retentions.update(one.get("retention_policy_digest")
                      for one in workers.values())
    if len(retentions) != 1:
        _refuse(f"this packet names {len(retentions)} retention policy "
                f"identities across its profile, workers and composition "
                f"({sorted(one for one in retentions if one)}); the finalizer "
                f"looks a cleanup up under the profile's and the ending records "
                f"it under the composition's, so two identities leave a "
                f"positive cleanup unable to satisfy the lookup")
    if not requested <= offered:
        _refuse(f"the submission requests workload profile(s) "
                f"{sorted(requested - offered)} and this deployment's workers "
                f"offer {sorted(offered)}; a stage no configured worker can "
                f"serve is deferred forever rather than refused, so it is "
                f"refused here")
    if composed.get("job_work_id") != packet["submission"]["work_id"]:
        _refuse(f"the composition binds Work "
                f"{composed.get('job_work_id')!r} and the submission names "
                f"{packet['submission']['work_id']!r}")

    fixture = _document(packet["fixture"], "the packet's fixture", _FIXTURE)
    _object_name(fixture["declared_base"], "the fixture's declared base")
    if type(fixture["files"]) is not dict or not fixture["files"]:
        _refuse("the fixture names at least one file and its digest")
    for name, expected in sorted(fixture["files"].items()):
        _pin(os.path.join(fixture["source_root"], name), expected,
             f"the fixture file {name!r}")

    image = _document(packet["worker_image"], "the packet's worker image",
                      _IMAGE)
    if type(image["worker_files"]) is not dict or not image["worker_files"]:
        _refuse("the worker image binds the effective worker bytes it carries")
    for name in ("adapter_descriptor", "policy_descriptor",
                 "profile_descriptor", "config_digest"):
        if type(image[name]) is not str or not image[name].startswith("sha256:"):
            _refuse(f"the worker image's {name} is one sha256 digest; this is "
                    f"{image[name]!r}")

    runtime = _document(packet["manager_runtime"],
                        "the packet's manager runtime", _RUNTIME)
    _pin(os.path.join(runtime["path"], "baton-v12-stack"),
         runtime["executable_sha256"], "the installed manager runtime")

    source = _document(packet["manager_source"],
                       "the packet's manager source", _SOURCE)
    if type(source["packages"]) is not list or not source["packages"]:
        _refuse("the manager source names the packages it provides")
    if type(source["files"]) is not dict or not source["files"]:
        _refuse("the manager source binds the files it is made of")
    if source["file_count"] != len(source["files"]):
        _refuse(f"the manager source declares {source['file_count']} files "
                f"and binds {len(source['files'])}")
    for name, expected in sorted(source["files"].items()):
        _pin(os.path.join(source["path"], name), expected,
             f"the manager source file {name!r}")
    # AND IT STILL IMPORTS, CARRYING THE ASSETS IT SAYS IT CARRIES, so a packet
    # bound to a source that cannot import is refused before a store opens
    # rather than at the installer.
    if verify_staged_assets(source["path"]) != source["frozen_assets"]:
        _refuse(f"the packet binds the frozen assets "
                f"{source['frozen_assets']} and the staged source at "
                f"{source['path']!r} now imports a different set")

    # THE FILESYSTEM ROOTS, held to the product's own rules before a store is
    # opened. OWNER REROUTE 312164: the live run reached `baseline.prepare` and
    # stopped at the first of these, so a packet that proved everything else and
    # not these was a packet that could pass `check` and fail the run.
    recorded = packet["filesystem_roots"]
    if type(recorded) is not list or not recorded:
        _refuse("the packet names the filesystem roots this run configures "
                "before it registers them")
    for one in recorded:
        _document(one, "a bound filesystem root",
                  ("role", "path", "mode", "uid", "gid", "proved_by"))
    if sorted(one["role"] for one in recorded) != ["context_storage",
                                                   "workspace_storage"]:
        _refuse(f"the packet binds the roots "
                f"{sorted(one['role'] for one in recorded)}; this run "
                f"configures the workspace store and the private-context "
                f"store, and a missing one is the failure this exists to "
                f"refuse")
    measured = verify_filesystem_roots(roots=recorded)
    for was, now in zip(sorted(recorded, key=lambda one: one["role"]),
                        sorted(measured, key=lambda one: one["role"])):
        for name in ("path", "mode", "uid", "gid"):
            if was[name] != now[name]:
                _refuse(f"the packet binds the {was['role']} root with "
                        f"{name} {was[name]!r} and it is now {now[name]!r}; a "
                        f"root that moved, changed owner or changed mode since "
                        f"the packet was bound is not the root the run was "
                        f"proved against")

    program = _document(packet["supervisor"], "the packet's supervisor", _SELF)
    _pin(program["path"], program["sha256"], "the supervisor program")
    if supervisor is not None \
            and os.path.realpath(supervisor) \
            != os.path.realpath(program["path"]):
        _refuse(f"this process is running {os.path.realpath(supervisor)!r} and "
                f"the packet binds {program['path']!r}")

    # CANONICAL PROVENANCE FOR EVERY REUSED BYTE, pinned rather than cited.
    # Review R3: "Name canonical provenance records for reused runtime/image
    # bytes". A record named and not checked is a footnote; each of these is
    # bound to its digest, so a rewritten provenance record refuses the run.
    provenance = packet["provenance"]
    if type(provenance) is not dict or not provenance:
        _refuse("the packet names no canonical provenance record for the "
                "runtime and image bytes it reuses")
    for what, held in sorted(provenance.items()):
        _document(held, f"the provenance record for {what}", ("path", "sha256"))
        _pin(held["path"], held["sha256"], f"the provenance record for {what}")

    # WHAT COMPATIBILITY IS AND IS NOT ESTABLISHED, carried in the packet.
    # Review R3: the `claude-fresh-implementation` label alone is not proof
    # that the reused image serves a MANAGED-CONTEXT profile. The packet says
    # which composition was checked and which was not, and `bind` measures the
    # checked part rather than asserting it.
    compatibility = _document(
        packet["compatibility"], "the packet's compatibility statement",
        ("adapter_source_sha256", "context_capable", "established",
         "not_established"))
    if compatibility["context_capable"] is not True:
        _refuse("the packet does not state that the bound image's adapter is "
                "context-capable; a reused fresh-Job image is not "
                "automatically one")
    for name in ("established", "not_established"):
        if type(compatibility[name]) is not list or not compatibility[name]:
            _refuse(f"the compatibility statement's {name!r} is a non-empty "
                    f"list; an unstated limit reads as coverage")

    boundary = _absolute(packet["code_boundary"], "the code boundary")
    if not os.path.isdir(boundary):
        _refuse(f"the code boundary {boundary!r} is not a directory")
    if os.path.realpath(boundary) != os.path.realpath(source["path"]):
        _refuse(f"the code boundary {boundary!r} is not the staged manager "
                f"source {source['path']!r}; the boundary is where the code "
                f"lives, and binding another directory leaves the check "
                f"answering about bytes nobody runs")
    for what, place in (("the Job store", deployment["job_store"]),
                        ("the control store", deployment["control_store"]),
                        ("the deployment state root", deployment["state_root"]),
                        ("the context storage", context["storage_path"]),
                        ("the retained outcome",
                         os.path.dirname(packet["outcome_path"]))):
        if _inside(boundary, place):
            _refuse(f"{what} at {place!r} is inside the code boundary "
                    f"{boundary!r}; mutable deployment state is never written "
                    f"into the tree the code lives in, and composition would "
                    f"refuse this after the owner acts had already committed")
    return packet


def packet_document(chosen, *, claim, staged, roots, deployment, composition,
                    context, submission, fixture, supervisor, provenance,
                    compatibility, outcome_path):
    """Assemble, in the shape `held_packet` proves. Measures nothing itself."""
    return {
        "schema": PACKET_SCHEMA,
        "run_id": chosen["run_id"],
        "work": chosen["work"],
        "claim": claim,
        "note": "the managed-correction packet; W236087 item 3",
        "worker_image": dict(chosen["worker_image"]),
        "manager_runtime": dict(chosen["manager_runtime"]),
        "manager_source": staged,
        "filesystem_roots": roots,
        "supervisor": supervisor,
        "code_boundary": staged["path"],
        "deployment": deployment,
        "composition": composition,
        "context": context,
        "submission": submission,
        "fixture": fixture,
        "bounds": dict(BOUNDS),
        "provenance": provenance,
        "compatibility": compatibility,
        "outcome_path": outcome_path,
    }


# -- the commands ----------------------------------------------------------

def commands(chosen, *, prepared, job_id, authority_uuid=None):
    """The exact commands, with no comment standing in for one.

    Review 2026-09-29T21-41-08Z R1: the previous packet named APIs in comments,
    and the one command that did carry an operand carried a SHELL SUBSTITUTION
    as a single argv element -- text no shell expands when the vector is run.
    Every step below is an argument vector of literal values.

    THE STATUS STEP IS COMPLETED BY `bind`, NOT GUESSED BY `stage`. It needs the
    Authority identity the bootstrap mints, which does not exist yet at `stage`
    time, so `stage` lists it as pending and `bind` -- which has read the real
    identity -- writes the whole list with the value in it. An operand this
    module does not have is named as pending rather than filled with a string
    that looks like one.
    """
    root = chosen["instance_root"]
    staged = os.path.join(chosen["staging_root"], "manager-source")
    here = os.path.dirname(os.path.realpath(__file__))
    imports = f"{os.path.join(staged, 'src')}:{staged}"
    # STEP 0 IMPORTS THE ORIGIN, NOT THE STAGED TREE, because the staged tree is
    # what step 0 CREATES. The delivered sequence ran `stage` with no
    # `PYTHONPATH` at all and relied on whatever the operator's interpreter
    # happened to have installed; owner report 311736's recovery is run from a
    # named tree or from none.
    origin = chosen["manager_source_origin"]
    beginning = f"{os.path.join(origin, 'src')}:{origin}"
    return [
        # THE SEQUENCE BEGINS WHERE THE FAILURE BEGAN. `stage` was step 0 of the
        # operator document and absent from this list, so the one command whose
        # defect stopped the run was the one command the machine-readable
        # sequence did not carry.
        {"step": 0, "what": "STAGE: write the input documents and COPY the "
                            "modules and frozen resources this run will "
                            "import, measuring every one. Refuses before it "
                            "writes, refuses a staged tree that does not "
                            "import, and refuses a staging root whose parent "
                            "holds the instance.",
         "command": ["python3", os.path.join(here, "correction_packet.py"),
                     "stage", "--selections", prepared["selections"],
                     "--destination", prepared["destination"],
                     "--claim", str(prepared["claim"]),
                     "--provenance", prepared["provenance"]],
         "environment": {"PYTHONPATH": beginning,
                         "PYTHONDONTWRITEBYTECODE": "1"}},
        {"step": 1, "what": "the instance, from the accepted runtime. "
                            "Installs; starts nothing.",
         "command": ["python3", "-m", "tools.bootstrap",
                     "--inputs", prepared["bootstrap_inputs"],
                     "--destination", root,
                     "--distro", chosen["manager_runtime"]["path"],
                     "--no-repositories"],
         "environment": {"PYTHONPATH": imports,
                         "PYTHONDONTWRITEBYTECODE": "1"}},
        # REVIEW 2026-09-29T23-17-24Z R1: the commands went straight from the
        # bootstrap to `bind`, which needs the qualified Work id -- and a FRESH
        # installation binds no Job by design, so there was nothing to read. This
        # is the missing supported step, and it submits NO Job: `baseline.survey`
        # refuses a Job identity the store already records, rightly.
        {"step": 2, "what": "the Authority acts this Job needs: create the Work "
                            "under the assignment contract, register the impl, "
                            "rview and integration route handlers, grant the "
                            "four receipt capabilities in the Work's own scope, "
                            "and set the canonical target. Journalled under a "
                            "derived identity, so a repeat replays.",
         "command": ["python3", os.path.join(here, "correction_packet.py"),
                     "prepare-work", "--selections", prepared["selections"],
                     "--destination", prepared["destination"]],
         "environment": {"PYTHONPATH": imports,
                         "PYTHONDONTWRITEBYTECODE": "1"}},
        {"step": 3, "what": "bind the packet to what the instance ACTUALLY "
                            "holds: the emitted deployment configuration, the "
                            "Authority identity the bootstrap minted and the "
                            "staged modules as copied. Opens no store.",
         "command": ["python3", os.path.join(here, "correction_packet.py"),
                     "bind", "--selections", prepared["selections"],
                     "--destination", prepared["destination"],
                     "--claim", str(prepared["claim"]),
                     "--provenance", prepared["provenance"]],
         "environment": {"PYTHONPATH": imports,
                         "PYTHONDONTWRITEBYTECODE": "1"}},
        # REVIEW 2026-09-29T23-17-24Z R2: this step omitted the staged
        # PYTHONPATH, and `held_packet` drives the REAL product validators --
        # `read_submission`, `single_worker._held`,
        # `stage_execution.held_configuration`, the certified profile digest. It
        # would have imported whatever was ambient, which is the exact thing the
        # staging exists to prevent.
        {"step": 4, "what": "prove the packet against the tree, with the real "
                            "product validators over the STAGED imports. Opens "
                            "no store; refuses on any drift.",
         "command": ["python3", os.path.join(here, "correction_packet.py"),
                     "check", "--packet", prepared["packet"]],
         "environment": {"PYTHONPATH": imports,
                         "PYTHONDONTWRITEBYTECODE": "1"}},
        {"step": 5, "what": "serve it, BOUNDED, in the foreground. This one "
                            "command performs the owner acts first -- the "
                            "workspace and private context storage, the "
                            "candidate profile's certification and ONE "
                            "qualification grant, each journalled under an "
                            "identity derived from its own operands, so "
                            "repeating it replays rather than composing a "
                            "second grant -- and then serves. It holds the "
                            "900s total with 60s reserved INSIDE it, caps the "
                            "invocations at the gate, stops on the first "
                            "terminal state and retains the outcome even when "
                            "interrupted.",
         "command": ["python3",
                     os.path.join(here, "correction_supervisor.py"),
                     "--packet", prepared["packet"]],
         "environment": {"PYTHONPATH": imports,
                         "PYTHONDONTWRITEBYTECODE": "1",
                         # THE GENERATED COMPOSITION, which is the document the
                         # run is composed from and the one the packet pins as
                         # `deployment.config_path`. The installer's own
                         # configuration binds no Job; this one binds this Job's
                         # two workers.
                         "BATON_V12_STAGE_EXECUTION_CONFIG":
                             os.path.join(prepared["destination"],
                                          "deployment.json")}},
        # THE ARGUMENT IS A VALUE, NOT A SHELL EXPRESSION. Review
        # 2026-09-29T21-41-08Z R1: this carried `$(python3 -c ...)` as a single
        # argv element, which no shell expands when the vector is executed
        # directly -- the manager would have been handed that text as the
        # Authority uuid. And `--job` is not an option `tools.job_manager
        # status` has; its options are `--control` and `--observe`. Both are
        # corrected: the identity is the one `bind` already read from the
        # instance, and the Job filtering is the reader's own.
        {"step": 6, "what": "read status from another terminal. READ-ONLY: it "
                            "opens the stores for reading and admits nothing. "
                            "Reports EVERY Job in the store; this run's is "
                            + job_id + ".",
         # THE SELECTED STORES, not a layout this command assumed. R2: these
         # were hardcoded under the instance root while `bind` binds the selected
         # ones, so a deployment whose stores live elsewhere would have been read
         # at the wrong paths -- or not at all.
         "command": ["python3", "-m", "tools.job_manager",
                     "--store", chosen["stores"]["job"],
                     "--authority-uuid", authority_uuid,
                     "--incarnation", chosen["run_id"],
                     "status", "--control", chosen["stores"]["control"]],
         "environment": {"PYTHONPATH": imports,
                         "PYTHONDONTWRITEBYTECODE": "1"}},
        {"step": 7, "what": "the result, after the supervisor returns. The "
                            "outcome document is the run's own answer.",
         "command": ["python3", "-c",
                     "import json,sys;print(json.dumps(json.load("
                     "open(sys.argv[1])), indent=2, sort_keys=True))",
                     os.path.join(root, "run", "outcome.json")],
         "environment": {"PYTHONDONTWRITEBYTECODE": "1"}},
    ]


# -- the subcommands -------------------------------------------------------

def job_id_of(chosen):
    return f"job-{chosen['run_id']}"


def stage(chosen, destination, *, copy=True, selections=None, claim=0,
          provenance=None):
    """Everything that needs no live instance. Refuses before it writes.

    THE OPERANDS OF THE LATER STEPS TRAVEL INTO THE COMMANDS. `bind` needs the
    selections, the destination, the claim and the provenance document, so the
    emitted step 2 carries them rather than leaving an operator to reconstruct
    a command line from prose.
    """
    job_id = job_id_of(chosen)
    source = chosen["source"]
    for name in source["files"]:
        whole = os.path.join(source["root"], name)
        if not os.path.exists(whole):
            _refuse(f"the selected source names {name!r}, which is not at "
                    f"{whole!r}")
    # AND THE TASK'S OWN OUTPUT MUST NOT ALREADY BE THERE. A documentation Job
    # whose file exists at the declared base is not the Job this packet
    # describes, and the reviewer would be reading someone else's work.
    if os.path.exists(os.path.join(source["root"], TASK_PATH)):
        _refuse(f"{TASK_PATH!r} already exists in the selected source; this "
                f"Job produces it, and a base that already carries it is a "
                f"different Job")
    os.makedirs(destination, exist_ok=True)
    staging = os.path.join(chosen["staging_root"], "manager-source")
    prepared = {
        "run_id": chosen["run_id"],
        "job_id": job_id,
        "destination": destination,
        "claim": claim,
        "selections": selections or os.path.join(destination,
                                                 "selections.json"),
        "provenance": provenance or os.path.join(destination,
                                                 "provenance.json"),
        "bootstrap_inputs": os.path.join(destination, "bootstrap-inputs.json"),
        "context_profile": os.path.join(destination, "context-profile.json"),
        "task": os.path.join(destination, "task.json"),
        "submission": os.path.join(destination, "submission.json"),
        "packet": os.path.join(destination, "packet.json"),
        "manager_source": staging,
    }
    # THE SUBMISSION IS NOT WRITTEN HERE, and that is a consequence of the real
    # contract rather than a preference. Its `input_digest` is
    # `job_input_identity(input_manifest)`, and the input manifest names the
    # Authority the bootstrap has not minted yet -- so the document belongs to
    # `bind`, after the instance exists. Review R1's own instruction: generate
    # the minted-identity operands AFTER binding.
    written = {
        prepared["bootstrap_inputs"]: bootstrap_document(chosen),
        prepared["context_profile"]: context_profile_document(chosen),
        prepared["task"]: task_document(chosen, job_id=job_id),
    }
    for path, document in sorted(written.items()):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
    staged = (staged_source(chosen["manager_source_origin"], staging)
              if copy else None)
    if staged is not None:
        # AND THE INSTANCE MUST NOT SIT INSIDE THE TREE THE STAGED CODE CALLS
        # ITS CHECKOUT, which is asked of the staged tree now that it exists.
        # Refused here rather than at step 1, where the delivered plan met it.
        staged["checkout"] = verify_instance_outside_checkout(
            chosen, staged_report(staging))
    every = commands(chosen, prepared=prepared, job_id=job_id)
    prepared["commands"] = [one for one in every if one["step"] != 6]
    prepared["commands_pending"] = [
        {"step": 6, "why": "needs the Authority identity `tools.bootstrap` "
                           "mints at step 1. `bind` writes the complete "
                           "command into commands.json once it has read it."}]
    prepared["staged_source"] = staged
    prepared["digests"] = {path: digest_of(path) for path in sorted(written)}
    # THE EXECUTABLE PREPARATION'S OWN BYTES, retained so `bind` can refuse a
    # change to the programs themselves rather than only to what they copied.
    prepared["preparation_modules"] = {
        name: digest_of(whole)
        for name, whole in sorted(_helper_modules().items())}
    with open(os.path.join(destination, "prepared.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(prepared, indent=2, sort_keys=True) + "\n")
    return prepared


# -- the workers, and what each of them may see ----------------------------

# THE PRODUCER'S CONFIGURATION IS `/5` AND THE REVIEWER'S IS `/4`, and that is
# the whole custody rule expressed as two schemas rather than as a sentence in a
# document. `single_worker._held` admits the `provider_context` member only for
# `/5`, so a `/4` configuration CANNOT carry one: the reviewer is structurally
# incapable of being handed the producer's private conversation. This is the
# accepted single Job's own composition -- its implementation worker is `/5` with
# `provider_context` and its review worker is `/4` without it.
PRODUCER_SCHEMA = "baton.v12.single-worker-deployment/5"
REVIEWER_SCHEMA = "baton.v12.single-worker-deployment/4"
DEPLOYMENT_SCHEMA = "baton.v12.stage-execution-deployment/1"

# THE CONTEXT PROFILE NAME A CONTEXT WORKER IS CONFIGURED WITH. Measured from
# the accepted context-capable deployment rather than reused from the fresh-run
# label: `review_driver._profile_of` compares a line's profile name to the
# profile it is handed, and `claude-fresh-implementation` is what the FRESH Jobs
# ran under.
CONTEXT_PROFILE_NAME = "claude-context-implementation"


def workload_profile(profile):
    """The workload profile BOTH documents name, from one source.

    Review 2026-09-29T22-36-24Z found the concrete blocker in a connected run:
    `submission_document` named `accepted['profile_name']`/`['profile_digest']`
    -- the FRESH workload -- while `worker_deployments` named
    `CONTEXT_PROFILE_NAME` and the certified profile's own
    `runtime_profile_digest`. So no worker this deployment configured could serve
    the implementation stage, and the manager's deferral said exactly that: "no
    worker this deployment configures for the 'implementation' stage can serve
    Job 'job-a': {'implementation-worker': ['the workload profile', 'the
    workload profile digest']}". Zero admissions, no runtime.

    TWO PLACES FOR ONE FACT, AGAIN, and this time across two documents rather
    than inside one. The stage REQUESTS a workload profile and the worker OFFERS
    one; they are the same fact, so they are derived here and nowhere else.
    """
    return {"name": CONTEXT_PROFILE_NAME,
            "digest": profile["runtime_profile_digest"]}


def worker_deployments(chosen, *, job_id, work_id, authority_uuid, manifest,
                       task_path, profile_digest, storage, profile):
    """The producer's and the reviewer's configurations, as this build reads them.

    Review 2026-09-29T22-02-59Z item 1. The previous claim generated no worker
    at all, so nothing established that the selected source, the worker
    profiles, the credential REFERENCE, the task and the criteria reach the real
    deployment -- `single_worker._held` had never been driven at this packet.
    These are the documents it reads, and the tests drive it at them.

    WHAT EACH WORKER GETS, and why the two differ:

      THE PRODUCER gets the provider context -- `mode: required`, the certified
      profile digest and the private storage root -- because its conversation is
      what a correction restores. `required` and not `optional`: a run whose
      context silently did not attach would answer the provider question with a
      fresh session and look like a success.
      THE REVIEWER gets NONE of it, and gets its own credential home and its own
      principal. It reads the proposal through the ordinary review path.

    NO CREDENTIAL BYTE IS NAMED ANYWHERE. `credential_profile` carries a
    REFERENCE the manager resolves at launch through the operator's own registry,
    and `credential_sources` is the path of that registry -- not its contents.
    Nothing here reads, copies or digests a credential.
    """
    accepted = _accepted()
    who = chosen["participants"]
    root = chosen["instance_root"]
    run = os.path.join(root, "run")
    shared = {
        "authority_store": chosen["stores"]["authority"],
        "authority_uuid": authority_uuid,
        "profile_name": workload_profile(profile)["name"],
        # ONE SOURCE, shared with the submission's requested profile: the real
        # preflight compares the worker's against the manifest's ("names another
        # runtime profile") and the scheduler compares the stage's request
        # against what a worker offers.
        "profile_digest": workload_profile(profile)["digest"],
        "policy_digest": accepted["policy_digest"],
        "adapter_name": accepted["adapter_name"],
        # DERIVED FROM THE CERTIFIED PROFILE, which is the third time the real
        # preflight taught this lesson: `single_worker._context_preflight`
        # requires the worker's adapter, image and retention digests to EQUAL the
        # certified profile's ("required context configuration disagrees with
        # its preconfigured owner"). One fact belongs in one place, and the place
        # is the profile the owner certified.
        "adapter_digest": profile["adapter_digest"],
        "engine": accepted["engine"],
        # ALSO DERIVED FROM THE MANIFEST, for the same reason and found the
        # same way: the preflight compares them ("names another worker image").
        "image_digest": manifest["worker_image_digest"],
        "network": accepted["provider_network"],
        "workspace_storage": chosen["workspace_storage"],
        "workspace_group": accepted["workspace_group"],
        "launch_home": os.path.join(run, "launch"),
        # THE CREDENTIAL DELIVERY IS A DEPLOYMENT FACT, so it is an operand.
        # `credentials.resolved_delivery` reads the slots and the profile
        # together, and a deployment whose provider or slot names differ from
        # this campaign's accepted ones is a different deployment rather than a
        # wrong one -- the connected fixture is exactly such a deployment. The
        # REFERENCE is still all that travels: no credential byte appears in any
        # document this module writes.
        "credential_sources": chosen["credential_delivery"]["sources"],
        "credential_slots": list(chosen["credential_delivery"]["slots"]),
        "credential_profile": {
            name: {"provider": chosen["credential_delivery"]["provider"],
                   "reference": chosen["credential_reference"]}
            for name in chosen["credential_delivery"]["slots"]},
        "nominated_source": chosen["source"]["root"],
        "workspace_capacity": dict(accepted["workspace_capacity"]),
        "input_manifest": manifest,
        "task_document": task_path,
        "launch_contract": accepted["launch_contract"],
        "review_route": chosen["review_route"]["implementation"],
        "retention_policy_digest": retention_of(chosen),
        "retention_disposition": accepted["retention_disposition"],
    }
    producer = dict(shared, schema=PRODUCER_SCHEMA,
                    participant=who["implementation"],
                    principal=f"principal:{who['implementation']}",
                    launch_role="implementation",
                    credential_home=os.path.join(run, "credentials",
                                                 "implementation"),
                    provider_context={"mode": "required",
                                      "profile_digest": profile_digest,
                                      # THE CONFIGURED STORAGE, not a second
                                      # path: `_context_preflight` compares the
                                      # worker's against the owner's.
                                      "storage": storage})
    reviewer = dict(shared, schema=REVIEWER_SCHEMA,
                    participant=who["review"],
                    principal=f"principal:{who['review']}",
                    launch_role="review",
                    # THE REVIEWER'S OWN OUTGOING ROUTE, which is not the
                    # producer's: each worker carries the route its own ending
                    # hands the Work on to.
                    review_route=chosen["review_route"]["review"],
                    credential_home=os.path.join(run, "credentials", "review"))
    del job_id, work_id
    return {"implementation-worker": producer, "review-worker": reviewer}


def deployment_document(chosen, *, job_id, work_id, authority_uuid, workers):
    """The stage-execution deployment this run is composed from.

    ONE JOB, so the bindings are the top-level ones the accepted single Job's
    deployment carries rather than a `job_bindings` list -- `bind` reads either.
    """
    accepted = _accepted()
    root = chosen["instance_root"]
    return {
        "schema": DEPLOYMENT_SCHEMA,
        "authority_store": chosen["stores"]["authority"],
        "authority_uuid": authority_uuid,
        "integration_store": chosen["stores"]["integration"],
        "state_root": chosen["stores"]["state_root"],
        "checkpoint_profile": accepted["checkpoint_profile"],
        "integration_profile": dict(
            accepted["integration_profile"],
            integrator_participant=chosen["participants"]["integration"]),
        "receipt_participants": dict(chosen["receipts"]),
        # THE COMPOSITION'S RETENTION IS THE PROFILE'S. The finalizer looks the
        # cleanup up under the profile's identity and the ending records it under
        # this one; two identities meant a positive cleanup could not satisfy the
        # lookup, and the use stayed held as `custody-invalid`.
        "retention_policy_digest": retention_of(chosen),
        "retention_disposition": accepted["retention_disposition"],
        "policy_generation": accepted["policy_generation"],
        "pool_generation": accepted["pool_generation"],
        "line_declared_base": chosen["source"]["declared_base"],
        "canonical_target_id": chosen["source"]["declared_base"],
        # ONE JOB THROUGH THE DOCUMENT'S OWN MEMBERS, AND NO `job_bindings`.
        # Review 2026-09-29T22-15-01Z asked for the ENCLOSING validator to be
        # driven, and it refused the first generated composition for exactly
        # this: "a baton.v12.stage-execution-deployment/1 deployment binds one
        # Job through its own members and names no job_bindings; two places for
        # one fact is how they drift". Worker validity proved nothing about the
        # composition around them, which is the reviewer's whole point.
        "job_work_id": work_id,
        "review_work_id": work_id,
        "workers": [{"worker_id": name, "role": held["launch_role"],
                     "deployment": held}
                    for name, held in sorted(workers.items())],
    }


def boundary_of(packet):
    """The code boundary the packet binds, as both ends read it."""
    held = packet.get("code_boundary")
    return held if type(held) is str else None


def verify_composition(composed, *, checkout):
    """Drive the ENCLOSING composition validator at the generated deployment.

    Review 2026-09-29T22-15-01Z: "worker validity alone does not prove
    composition, source bindings, role coverage or instance-to-Job
    preparation." `stage_execution.held_configuration` is the reading the
    serving process performs -- it owns the whole closed document, re-derives
    every worker through `single_worker._held`, checks the roles cover what the
    deployment needs, and refuses mutable state inside the code boundary. It
    found a real fault in the first generated composition, which is why it is
    here rather than trusted.

    THE BOUNDARY IS PASSED, not inferred: `operations_from` would otherwise
    derive it from `stage_execution.__file__`, which for a relocated manager
    source answers the run root's parent.
    """
    try:
        from tools import stage_execution
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the generated "
                f"composition cannot be proved with the reading the serving "
                f"process performs ({failure})")
    from baton_v12.contracts import ContractRefusal

    try:
        return stage_execution.held_configuration(composed, checkout=checkout)
    except ContractRefusal as refusal:
        _refuse(f"the generated deployment is not one this build composes: "
                f"{refusal}")


def verify_workers(workers):
    """Drive the REAL worker preflight at the generated configurations.

    `single_worker._held` is what the composition runs before an offer exists:
    it owns every static choice, resolves the credential DELIVERY from the slots
    and the profile (never the bytes), validates the input manifest's structure,
    compares the task document's bytes against the manifest's human contract,
    nominates the source through the boundary walk, and authors the exact launch
    document version this deployment will write. A configuration it refuses is
    one no run could ever compose, so it is refused here -- before an instance
    is installed -- rather than at the first launch.

    THE ROLE TRAVELS WITH THE DOCUMENT. `_held(document, roles=...)` is asked
    for the role that worker actually serves, so the reviewer's configuration is
    proved as a REVIEW worker rather than as a second producer.
    """
    try:
        from tools.single_worker import _held
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the generated worker "
                f"configurations cannot be proved with the preflight that will "
                f"read them ({failure})")
    from baton_v12.contracts import ContractRefusal

    proved = {}
    for name, held in sorted(workers.items()):
        try:
            proved[name] = _held(held, roles=(held["launch_role"],))
        except ContractRefusal as refusal:
            _refuse(f"the generated {name} configuration is not one this build "
                    f"accepts: {refusal}")
    # AND THE CUSTODY RULE, asked of the proved documents rather than of the
    # intent that wrote them: exactly one worker may carry a provider context,
    # and it is the producer.
    contextual = sorted(name for name, held in workers.items()
                        if "provider_context" in held)
    if contextual != ["implementation-worker"]:
        _refuse(f"the provider context belongs to the producer alone; these "
                f"workers carry it: {contextual}. Handing a reviewer the "
                f"producer's private conversation is the one thing this "
                f"composition must not do.")
    return proved


# -- the supported Work preparation, between the bootstrap and `bind` -------

def installed_layout(root):
    """Where the bootstrap ACTUALLY put things, asked of the tool itself.

    Review 2026-09-29T23-17-24Z R1: `bind` read `<root>/run/deployment.json`
    while `tools.bootstrap.layout` emits the configuration at
    `<root>/deployment.json` and the stores under `<root>/db/`. Two layouts that
    disagree about where a Job store is are two deployments sharing a name, so
    this asks the installer rather than assuming its shape.
    """
    try:
        from tools import bootstrap
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the installed "
                f"layout cannot be read from the tool that emits it "
                f"({failure}). Run with PYTHONPATH naming the staged source's "
                f"`src` and its root.")
    return bootstrap.layout(root)


def prepare_work(authority, chosen, *, work_id):
    """The Authority acts this Job needs, against an ALREADY OPEN handle.

    Review 2026-09-29T23-17-24Z R1: a fresh installation binds no Job -- by
    design, and `bootstrap_document` emits none on purpose -- so the emitted
    configuration carries `job_bindings: []` and no `job_work_id`, and
    `qualified_work_id` correctly refused it. The commands went straight from
    the bootstrap to `bind`, which needs exactly that identity. This is the step
    that was missing.

    THE ACTS ARE THE ACCEPTED ONES, in the shape `prepare_instance.prepare`
    uses: create the Work under the assignment contract, register the route
    handlers the stages need, grant the four receipt capabilities in the Work's
    own scope, and set the canonical target. Taking an OPEN handle rather than
    opening one is what lets a disposable instance drive this exact function.

    IDEMPOTENT BY JOURNALLED IDENTITY, not by a flag: `create_work` is
    journalled under the identity DERIVED HERE, so running this twice against the
    same Authority replays the same act rather than creating a second Work.

    THE IDENTITY IS NOT AN OPERAND, and that is the whole of review
    2026-09-29T23-49-58Z. A previous version accepted `operation_id` from its
    caller and the CLI passed `--operation-id` straight through, so
    `--operation-id fixed-operator-id` with the base changed from `a*40` to
    `b*40` succeeded TWICE, reported a replay, and really moved the canonical
    target. Deriving it here closes that for the CLI and for every direct caller
    at once: there is no parameter left to disagree with the operands.

    AND THIS SUBMITS NO JOB. `baseline.survey` refuses a Job identity the store
    already records -- rightly -- so the execution Job is submitted by the
    supervisor and by nothing before it.
    """
    who = chosen["participants"]
    receipts = chosen["receipts"]
    base = chosen["source"]["declared_base"]
    operation_id = preparation_identity(chosen, work_id)

    # THE PRODUCT'S OWN IDENTITY GATE DECIDES, and this no longer steps around
    # it. Review 2026-09-29T23-40-17Z R1: a previous version SKIPPED
    # `create_work` whenever a Work of this name already existed under the
    # ordinary `v12-assignment-1` contract, and then granted four capabilities in
    # THAT Work's scope and set the global canonical target. The reviewer created
    # `W236087` under an unrelated act with `scope:unrelated`, and this
    # preparation adopted it; changing the declared base from `a*40` to `b*40`
    # was likewise accepted as a "replay". A COMMON CONTRACT IS NOT PREPARATION
    # IDENTITY.
    #
    # `create_work` is journalled under `operation_id`, so it replays THIS act
    # and refuses a name reached under any other. Calling it UNCONDITIONALLY is
    # what separates the three cases:
    #
    #   SAME OPERANDS, run again  -> the journal replays, so a preparation that
    #                                stopped part-way is finished by repeating
    #                                the command.
    #   ANOTHER ACT'S WORK        -> refused: this operation never created it.
    #   CHANGED OPERANDS          -> refused, because `operation_id` is DERIVED
    #                                FROM the operands, so different inputs are a
    #                                different act reaching an existing name.
    #
    # AND THE REFUSAL COMES FIRST. Nothing below runs -- no capability granted, no
    # policy set -- until the gate has admitted this act.
    from baton_v12.authority.errors import Refusal

    probed = None
    try:
        probed = authority.project_work(work_id)
    except Refusal:
        probed = None
    try:
        authority.create_work(work_id, "impl", contract="v12-assignment-1",
                              operation_id=operation_id)
    except Refusal as refusal:
        _refuse(f"this preparation cannot claim Work {work_id!r}: {refusal}. "
                f"Its creation is journalled under {operation_id!r}, derived "
                f"from THIS preparation's operands, so the name is held either "
                f"by another act or by this preparation with DIFFERENT operands "
                f"-- a shared assignment contract is not preparation identity. "
                f"Nothing was granted and no policy was changed. Select an "
                f"unused Work, or repeat the preparation with the operands it "
                f"was journalled with.")
    # REPORTED, NOT DECIDED: the probe says whether the name existed before, which
    # is useful in the record and is not what admitted the act.
    replayed = probed is not None
    scope = authority.project_work(work_id)["scope"]
    authority.add_route_handler("impl", who["implementation"])
    # THE REVIEW ROUTE IS REGISTERED HERE, unlike the single-implementation
    # packet's: this Job submits a REVIEW stage, so the reviewer's claim would
    # otherwise refuse against a route nobody handles.
    authority.add_route_handler("rview", who["review"])
    authority.add_route_handler("integration", who["integration"])
    granted = []
    for participant, capability in ((receipts["verification"], "verify"),
                                    (receipts["review"], "review"),
                                    (receipts["approval"], "approve"),
                                    (who["integration"], "integrate")):
        authority.grant_capability(participant, capability, scope=scope)
        granted.append({"participant": participant, "capability": capability})
    authority.set_policy("canonical_target", base)
    return {"work_id": work_id, "scope": scope, "canonical_target": base,
            "operation_id": operation_id,
            "operands": preparation_operands(chosen, work_id),
            "created": not replayed,
            "route_handlers": {"impl": who["implementation"],
                               "rview": who["review"],
                               "integration": who["integration"]},
            "granted": granted}


def preparation_operands(chosen, work_id):
    """EXACTLY what this preparation would bind, as one comparable document.

    Review 2026-09-29T23-40-17Z: the preparation must be bound to its operation
    AND OPERAND identity. These are the values the acts actually use, so a change
    to any of them is a different act rather than a replay of this one.
    """
    who = chosen["participants"]
    return {"work_id": work_id,
            "contract": "v12-assignment-1",
            "canonical_target": chosen["source"]["declared_base"],
            "route_handlers": {"impl": who["implementation"],
                               "rview": who["review"],
                               "integration": who["integration"]},
            "receipts": dict(chosen["receipts"])}


def preparation_identity(chosen, work_id):
    """The journalled identity this preparation acts under.

    DERIVED FROM THE OPERANDS, which is what makes `create_work`'s own gate
    refuse a changed replay: different operands are a different identity, and a
    different identity reaching an existing name is refused BY THE PRODUCT rather
    than by a rule restated here.
    """
    try:
        from baton_v12.contracts import digest
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the preparation "
                f"identity cannot be derived with the product's own digest "
                f"({failure})")
    return "w236087-prepare:" + digest(
        preparation_operands(chosen, work_id))[7:39]


def prepared_work_id(chosen, identity):
    """The Work id this preparation creates, and it is a VALID one.

    Review 2026-09-29T23-28-53Z R1: this composed the name from the RUN ID and
    produced `7ea319da-Wmanaged-correction-309356`, which
    `authority.identity.check_work_id` refuses -- "a Work id is the full
    canonical <8 hex>-W<positive> identity and a local selector is not one". The
    CLI used this generator while the connected harness passed an existing
    fixture Work, so the fresh identity path was never exercised at all.

    THE NAME COMES FROM THE SELECTED WORK and the qualifier from the instance the
    bootstrap minted: `<8 hex>-W<positive>`. The selections' `work` is already a
    `W<number>` selector, which is what makes the composition valid, and the
    PRODUCT'S OWN CHECKER is asked rather than a pattern restated here -- that is
    how the previous version's invalid identity would have been caught before a
    store was opened.
    """
    if type(identity) is not str or len(identity) < 8:
        _refuse(f"the Authority identity {identity!r} is not one this "
                f"installation minted")
    held = f"{identity[:8]}-{chosen['work']}"
    try:
        from baton_v12.authority.identity import check_work_id
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the Work identity "
                f"cannot be validated by the checker that will read it "
                f"({failure})")
    from baton_v12.authority.errors import Refusal

    try:
        return check_work_id(held)
    except Refusal as refusal:
        _refuse(f"the Work identity this preparation would create is not one "
                f"this Authority accepts: {refusal}. The selections' `work` is "
                f"the local selector -- `W` followed by a positive number -- and "
                f"{chosen['work']!r} is not one.")


def reviewed_manifest(prepared_path, staged_root):
    """The manifest `stage` RETAINED, proved against the bytes on disk now.

    Review 2026-09-29T21-41-08Z R4, and the finding is exactly right: `bind`
    re-hashed whatever was staged at that moment and wrote those digests into
    the packet, so a module edited between `stage` and `bind` was SIGNED rather
    than refused. Re-signing drift is worse than not checking, because the
    packet then testifies to bytes nobody reviewed.

    So the comparison is against the retained manifest, in both directions: a
    changed file, a file that disappeared, and a file that APPEARED are each a
    difference between the reviewed preparation and this one.
    """
    with open(prepared_path, "rb") as handle:
        retained = json.loads(handle.read().decode("utf-8"))
    held = (retained.get("staged_source") or {}).get("files")
    if type(held) is not dict or not held:
        _refuse(f"{prepared_path!r} retains no staged-source manifest, so "
                f"`bind` cannot tell the reviewed preparation from the "
                f"current one; re-run `stage`")
    found = {name: digest_of(os.path.join(staged_root, name))
             for name in sorted(_source_files(staged_root))}
    moved = sorted(name for name in set(held) | set(found)
                   if held.get(name) != found.get(name))
    if moved:
        _refuse(f"the staged manager source has CHANGED since `stage` "
                f"reviewed it: {', '.join(moved)}. `bind` refuses drift rather "
                f"than re-signing it; re-run `stage` and have the result "
                f"reviewed again.")
    # AND THE EXECUTABLE PREPARATION ITSELF, which R4 also names: this module
    # and the supervisor are imported by the run and were outside the staged
    # packages entirely, so nothing bound them at all.
    for name, whole in sorted(_helper_modules().items()):
        expected = (retained.get("preparation_modules") or {}).get(name)
        if expected is None:
            _refuse(f"{prepared_path!r} binds no digest for the preparation "
                    f"module {name!r}; re-run `stage`")
        if digest_of(whole) != expected:
            _refuse(f"the preparation module {name!r} has CHANGED since "
                    f"`stage` reviewed it; `bind` refuses drift rather than "
                    f"re-signing it")
    return found


def _helper_modules():
    """EVERY executable dependency this preparation imports, by name.

    NOT the staged packages: these live outside the bound manager source, so
    `verify_imported_sources` deliberately does not cover them.

    AND THAT INCLUDES THE SIBLING DOSSIER'S DESCRIPTOR SUPPLIER. Review
    2026-09-29T22-02-59Z item 4: `_accepted()` imports
    `prepare_two_jobs.ACCEPTED` and the candidate merely NOTED its digest, which
    is a note rather than an execution check -- the descriptors this packet's
    documents are built from could change under it and nothing would refuse. It
    is bound here with the rest, so a changed supplier is drift like any other.
    The file itself is never edited: that dossier is accepted and closed.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    held = {name: os.path.join(here, name)
            for name in ("correction_packet.py", "correction_supervisor.py")}
    held[_SUPPLIER] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "finding-v12-real-jobs-adoption-gate", "prepare_two_jobs.py")
    return held


# The reused descriptor supplier, named once so the importer and the drift
# check cannot disagree about which file they mean.
_SUPPLIER = "finding-v12-real-jobs-adoption-gate/prepare_two_jobs.py"


def qualified_work_id(config, chosen, *, prepared=None):
    """The Work id a STAGE names, from the supported preparation or the deployment.

    A stage's `work_id` is the Authority-qualified identity -- `<uuid
    prefix>-W…` -- and the bare `W236087` my first draft wrote is not one.

    THE PREPARATION RECORD IS THE FIRST SOURCE, because a FRESH installation
    binds no Job: review 2026-09-29T23-17-24Z R1 showed `tools.bootstrap`
    emitting `job_bindings: []` and no `job_work_id`, which this function
    correctly refused -- the missing step was the Authority preparation, not the
    read. `prepare-work` writes its record and `bind` hands it here.

    A DEPLOYMENT THAT DOES BIND ONE IS STILL ACCEPTED, and then the two must
    AGREE: an instance whose configuration names another Work is not the one
    this preparation prepared.
    """
    held = None
    if prepared is not None:
        held = prepared.get("work_id")
        if type(held) is not str or not held:
            _refuse(f"the preparation record at {prepared.get('path')!r} names "
                    f"no work_id")
    with open(config, "rb") as handle:
        configured = json.loads(handle.read().decode("utf-8"))
    bound = None
    for binding in configured.get("job_bindings") or []:
        if binding.get("job_id") == job_id_of(chosen):
            bound = binding.get("job_work_id")
    bound = bound or configured.get("job_work_id") or None
    if held is not None and bound and held != bound:
        _refuse(f"the preparation created Work {held!r} and {config!r} binds "
                f"{bound!r}; one instance, one Work")
    if held is not None:
        return held
    if type(bound) is str and bound:
        return bound
    _refuse(f"neither a preparation record nor {config!r} names a qualified "
            f"Work id for Job {job_id_of(chosen)!r}. A FRESH installation binds "
            f"no Job by design, so run the `prepare-work` command between the "
            f"bootstrap and `bind`.")


def input_manifest_for(chosen, *, job_id, work_id, authority_uuid, task_bytes,
                       profile):
    """One Job's input manifest, from the ACCEPTED builder.

    THE HUMAN CONTRACT IS THE TASK BYTES. `single_worker._held` compares the
    worker's `task.json` against this manifest's `human_contract` digest, so
    the two are derived together -- which is what makes "the same complete
    criteria reached the worker" a checkable fact.
    """
    import sys as _sys

    place = os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))), "finding-v12-real-jobs-adoption-gate")
    if place not in _sys.path:
        _sys.path.insert(0, place)
    import prepare_two_jobs

    manifest = prepare_two_jobs.input_manifest(
        authority_uuid=authority_uuid, work_id=work_id,
        task_path=os.path.join(chosen["instance_root"], "tasks",
                               f"{job_id}.json"),
        raw=task_bytes, artifact_id=f"{chosen['run_id']}-{job_id}-contract")
    return with_context_receipt(with_profile_facts(manifest, profile))


# THE RESERVED RECEIPT DECLARATION, in the EXACT shape the preflight admits.
# `single_worker._context_declaration` checks every one of these values, and the
# real preflight refused the first generated worker with "required context
# receipt declaration is missing" -- which is how this arrived here rather than
# in a comment claiming the receipt was declared. A context implementation
# worker MUST declare it; a review worker MAY carry the declaration and must not
# carry a provider context, which is the accepted composition.
CONTEXT_RECEIPT = {
    "name": "provider-context-receipt",
    "path": "provider-context-receipt",
    "type": "directory-result",
    "required": False,
    "constraints": {"allowed_media_types": ["application/octet-stream"],
                    "link_policy": "forbid", "max_bytes": 16384,
                    "max_entries": 1, "validator_digest": None},
}


def with_profile_facts(manifest, profile):
    """Make the manifest agree with the CERTIFIED PROFILE, then reseal.

    `single_worker._held` requires the worker's `profile_digest` and
    `image_digest` to be the manifest's `runtime_profile_digest` and
    `worker_image_digest`, and `_context_preflight` requires those same worker
    values to equal the CERTIFIED PROFILE's. Two constraints, one solution: the
    profile is the authority and the manifest is derived from it. The reused
    builder supplies this campaign's accepted values, which are right for the
    accepted instance and wrong for any other -- so they are replaced from the
    profile rather than assumed.
    """
    held = dict(manifest)
    held["runtime_profile_digest"] = profile["runtime_profile_digest"]
    held["worker_image_digest"] = profile["image_digest"]
    held["retention_policy_digest"] = profile["retention_policy_digest"]
    return _sealed(held)


def _sealed(manifest):
    """Reseal with the product's own digest rule.

    `verify_manifest_digest` refuses a manifest whose declared identity its own
    bytes do not produce, so this asks `contracts.digest` rather than hashing
    canonical text here.
    """
    try:
        from baton_v12.contracts import digest
    except ImportError as failure:                           # pragma: no cover
        _refuse(f"the manager source is not importable, so the manifest cannot "
                f"be sealed with the product's own rule ({failure})")
    held = dict(manifest)
    held.pop("manifest_digest", None)
    held["manifest_digest"] = digest(dict(held))
    return held


def with_context_receipt(manifest):
    """Declare the receipt, then RESEAL with the product's own digest rule.

    The receipt travels in `outputs`, which `job_input_identity` does NOT
    exclude -- so both workers' manifests carry the same outputs and therefore
    the same Job input identity, exactly as the accepted context-capable
    deployment does. Resealing uses `contracts.digest` over every member but
    `manifest_digest`, because `verify_manifest_digest` refuses a manifest whose
    declared identity its own bytes do not produce.
    """
    held = dict(manifest)
    outputs = [one for one in held.get("outputs") or []
               if one.get("name") != CONTEXT_RECEIPT["name"]]
    held["outputs"] = outputs + [dict(CONTEXT_RECEIPT)]
    return _sealed(held)


def job_input_digest(manifest):
    """The Job's input digest, by the PRODUCT's rule.

    `contracts.job_input_identity` owns its operand and refuses a manifest that
    is not an input one, so this is a derivation rather than a hash this module
    chose.
    """
    try:
        from baton_v12.contracts import job_input_identity
    except ImportError as failure:
        _refuse(f"the manager source is not importable, so the Job's input "
                f"digest cannot be derived the way the product derives it "
                f"({failure}). Run `bind` with PYTHONPATH naming the staged "
                f"source's `src` and its root.")
    return job_input_identity(manifest)


def bind(chosen, destination, *, claim, provenance, compatibility):
    """Measure what the live instance actually holds, and emit the packet.

    Every value here is READ from the instance the commands built -- the
    emitted deployment configuration, the Authority identity the bootstrap
    minted, the staged modules as copied -- so the packet describes what
    exists rather than what was intended.
    """
    root = chosen["instance_root"]
    job_id = job_id_of(chosen)
    identity = os.path.join(root, "bootstrap.json")
    if not os.path.exists(identity):
        _refuse(f"{identity!r} does not exist; run the bootstrap command from "
                f"`stage`'s step 1 before binding the packet")
    with open(identity, "rb") as handle:
        recorded = json.loads(handle.read().decode("utf-8"))
    uuid = recorded.get("authority_uuid")
    if type(uuid) is not str or not uuid:
        _refuse(f"{identity!r} names no authority_uuid, so the packet cannot "
                f"bind the identity this instance actually has")
    # THE PATHS THE INSTALLER ACTUALLY EMITTED, read from `bootstrap.layout`
    # rather than assumed: R1 found `bind` reading `<root>/run/deployment.json`
    # while the tool emits `<root>/deployment.json`.
    installed = installed_layout(root)
    config = installed["configuration"]
    profile = os.path.join(destination, "context-profile.json")
    task = os.path.join(destination, "task.json")
    prepared_path = os.path.join(destination, "prepared.json")
    for what, path in (("the emitted deployment configuration", config),
                       ("the context profile", profile),
                       ("the Job's task document", task),
                       ("the retained preparation manifest", prepared_path)):
        if not os.path.exists(path):
            _refuse(f"{what} is not at {path!r}")
    with open(profile, "rb") as handle:
        profiled = json.loads(handle.read().decode("utf-8"))

    # -- R4: THE REVIEWED PREPARATION, NOT WHATEVER EXISTS NOW -------------
    # Review 2026-09-29T21-41-08Z R4: `bind` re-hashed the then-current staged
    # files and declared THOSE bytes the packet, so a change between `stage`
    # and `bind` was adopted rather than refused -- the signature moved to
    # cover the drift. `stage` retains its manifest; this compares against it
    # and refuses any difference before re-binding.
    staged_root = os.path.join(chosen["staging_root"], "manager-source")
    files = reviewed_manifest(prepared_path, staged_root)
    # AND THE TREE STILL IMPORTS, AND THE INSTANCE IS STILL OUTSIDE ITS
    # CHECKOUT. Both are asked of the staged tree at the moment the packet is
    # bound, because both are conditions the RUN needs rather than conditions
    # the copy needed: owner report 311736 was an asset absent at run time, and
    # the layout defect claim 311743 found would refuse the instance at step 1.
    report = staged_report(staged_root)
    assets = verify_staged_assets(staged_root, report)
    verify_instance_outside_checkout(chosen, report)
    # AND THE FILESYSTEM ROOTS THE RUN CONFIGURES FIRST, established here --
    # before the packet claims the instance is ready, and long before
    # `baseline.prepare` registers them. Owner reroute 312164: this step
    # existed and did not do this, so the supervisor met the absence.
    create_filesystem_roots(chosen)
    roots = verify_filesystem_roots(chosen)
    here = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "correction_supervisor.py"))

    # THE SUBMISSION, WITH THE IDENTITIES THE INSTANCE ACTUALLY HAS. The
    # qualified Work id and the Authority uuid come from the installed
    # deployment; `input_digest` is derived from the worker's own input
    # manifest by the product's rule rather than composed here.
    record = os.path.join(destination, "prepared-work.json")
    held = None
    if os.path.exists(record):
        with open(record, "rb") as handle:
            held = dict(json.loads(handle.read().decode("utf-8")),
                        path=record)
    work_id = qualified_work_id(config, chosen, prepared=held)
    with open(task, "rb") as handle:
        task_bytes = handle.read()
    manifest = input_manifest_for(chosen, job_id=job_id, work_id=work_id,
                                  authority_uuid=uuid, task_bytes=task_bytes,
                                  profile=profiled)
    submission = os.path.join(destination, "submission.json")
    with open(submission, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(
            submission_document(chosen, job_id=job_id, work_id=work_id,
                                input_digest=job_input_digest(manifest),
                                profile=profiled),
            indent=2, sort_keys=True) + "\n")
    with open(os.path.join(destination, "input-manifest.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    # THE WORKERS AND THE DEPLOYMENT, GENERATED AND THEN PROVED BY THE PROGRAM
    # THAT WILL READ THEM. Review 2026-09-29T22-02-59Z item 1: the previous
    # claim generated no worker at all, so nothing established that the selected
    # source, the worker profiles, the credential reference and the task reach
    # the real deployment. `verify_workers` drives `single_worker._held`, which
    # is the preflight the composition itself performs.
    workers = worker_deployments(
        chosen, job_id=job_id, work_id=work_id, authority_uuid=uuid,
        manifest=manifest, task_path=task,
        profile_digest=certified_digest(profiled),
        storage=chosen["context_storage"]["path"], profile=profiled)
    composed = deployment_document(chosen, job_id=job_id, work_id=work_id,
                                   authority_uuid=uuid, workers=workers)
    verify_workers(workers)
    verify_composition(composed, checkout=staged_root)
    with open(os.path.join(destination, "deployment.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps(composed, indent=2, sort_keys=True) + "\n")
    packet = packet_document(
        chosen, claim=claim,
        staged={"path": staged_root, "packages": list(IMPORTED_PACKAGES),
                "file_count": len(files), "files": files,
                "frozen_assets": assets},
        roots=roots,
        composition={"workers": sorted(workers),
                     "producer_schema": PRODUCER_SCHEMA,
                     "reviewer_schema": REVIEWER_SCHEMA,
                     "contextual_worker": "implementation-worker"},
        # THE CONFIGURATION THE RUN IS COMPOSED FROM IS THE GENERATED ONE.
        # The connected fixture found this: `baseline._retention_of` and
        # `baseline._compose` both read `deployment.config_path`, and pointing it
        # at the INSTANCE's own record left the cleanup identity with no
        # retention policy digest -- "the deployment configuration names no
        # retention policy digest, and the cleanup identity binds one".
        deployment={"config_path": os.path.join(destination,
                                                "deployment.json"),
                    "config_sha256": digest_of(
                        os.path.join(destination, "deployment.json")),
                    "job_store": chosen["stores"]["job"],
                    "control_store": chosen["stores"]["control"],
                    "authority_store": chosen["stores"]["authority"],
                    # (the SELECTED stores. A bootstrapped instance puts them
                    # under the installed layout's `db/`; a disposable fixture
                    # puts them where it makes them, which is why they are
                    # operands rather than derived.)
                    "authority_uuid": uuid,
                    "state_root": chosen["stores"]["state_root"]},
        context={"storage_path": chosen["context_storage"]["path"],
                 "excluded_roots": list(chosen["context_storage"]["excluded"]),
                 "runtime_uid": chosen["runtime_uid"],
                 "profile_path": profile, "profile_sha256": digest_of(profile),
                 "profile_digest": certified_digest(profiled),
                 "qualification": profiled["qualification"],
                 "layout_version": profiled["layout_version"],
                 "job_id": job_id},
        submission={"path": submission, "sha256": digest_of(submission),
                    "submission_id": f"submission-{chosen['run_id']}",
                    "job_id": job_id, "work_id": work_id,
                    "input_digest": job_input_digest(manifest),
                    "task_path": task, "task_sha256": digest_of(task),
                    "manifest_path": os.path.join(destination,
                                                  "input-manifest.json"),
                    "manifest_sha256": digest_of(
                        os.path.join(destination, "input-manifest.json")),
                    "implementation_participant":
                        chosen["participants"]["implementation"],
                    "review_participant": chosen["participants"]["review"]},
        fixture={"source_root": chosen["source"]["root"],
                 "declared_base": chosen["source"]["declared_base"],
                 "files": {name: digest_of(
                     os.path.join(chosen["source"]["root"], name))
                     for name in sorted(chosen["source"]["files"])}},
        supervisor={"path": here, "sha256": digest_of(here)},
        provenance=provenance, compatibility=compatibility,
        outcome_path=os.path.join(root, "run", "outcome.json"))
    # THE OUTCOME'S DIRECTORY EXISTS BEFORE THE RUN NEEDS IT. `_publish` writes
    # atomically through a `.partial` sibling and creates no directory, so a real
    # run would fail at the one moment it must not: while retaining its result.
    os.makedirs(os.path.dirname(packet["outcome_path"]), exist_ok=True)
    path = os.path.join(destination, "packet.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    # THE COMPLETE COMMAND LIST, now that the minted identity is known. `stage`
    # deferred step 5 rather than writing a shell expression into an argv
    # element; this writes it with the value the instance actually has.
    with open(prepared_path, "rb") as handle:
        retained = json.loads(handle.read().decode("utf-8"))
    whole = commands(chosen, prepared=retained, job_id=job_id,
                     authority_uuid=uuid)
    with open(os.path.join(destination, "commands.json"), "w",
              encoding="utf-8") as handle:
        handle.write(json.dumps({"run_id": chosen["run_id"], "job_id": job_id,
                                 "authority_uuid": uuid, "commands": whole},
                                indent=2, sort_keys=True) + "\n")
    return path


def main(argv=None, *, stream=None):
    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="correction_packet",
        description="Generate and check the managed-correction packet. Opens "
                    "no store, starts no container, reads no credential and "
                    "performs no version-control act.")
    sub = parser.add_subparsers(dest="action", required=True)
    for name, what in (("stage", "write the inputs and stage the source"),
                       ("bind", "measure the live instance and emit the "
                                "packet")):
        one = sub.add_parser(name, help=what)
        one.add_argument("--selections", required=True)
        one.add_argument("--destination", required=True)
        one.add_argument("--claim", required=(name == "bind"), type=int,
                         default=0)
        one.add_argument("--provenance", required=(name == "bind"),
                         default=None,
                         help="a JSON document of canonical record paths and "
                              "the compatibility statement")
    preparing = sub.add_parser(
        "prepare-work",
        help="the Authority acts this Job needs, between the bootstrap and bind")
    preparing.add_argument("--selections", required=True)
    preparing.add_argument("--destination", required=True)
    checking = sub.add_parser("check", help="prove an existing packet")
    checking.add_argument("--packet", required=True)
    taken = parser.parse_args(argv)

    if taken.action == "check":
        packet = held_packet(taken.packet)
        print(json.dumps({"packet": taken.packet, "run_id": packet["run_id"],
                          "job_id": packet["submission"]["job_id"],
                          "bounds": packet["bounds"],
                          "manager_source_files":
                              packet["manager_source"]["file_count"],
                          "proved": True},
                         indent=2, sort_keys=True), file=stream)
        return 0

    chosen = held_selections(taken.selections)
    if taken.action == "prepare-work":
        from baton_v12.authority import Authority

        installed = installed_layout(chosen["instance_root"])
        with open(installed["record"], "rb") as handle:
            recorded = json.loads(handle.read().decode("utf-8"))
        uuid = recorded.get("authority_uuid")
        if type(uuid) is not str or not uuid:
            _refuse(f"{installed['record']!r} names no authority_uuid; run the "
                    f"bootstrap command first")
        work_id = prepared_work_id(chosen, uuid)
        authority = Authority.open(installed["authority_store"],
                                   expected_authority_uuid=uuid)
        try:
            prepared = prepare_work(authority, chosen, work_id=work_id)
        finally:
            authority.dispose()
        prepared["authority_uuid"] = uuid
        prepared["authority_store"] = installed["authority_store"]
        os.makedirs(taken.destination, exist_ok=True)
        path = os.path.join(taken.destination, "prepared-work.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(prepared, indent=2, sort_keys=True) + "\n")
        print(json.dumps(dict(prepared, record=path), indent=2,
                         sort_keys=True), file=stream)
        return 0
    if taken.action == "stage":
        prepared = stage(chosen, taken.destination,
                         selections=os.path.realpath(taken.selections),
                         claim=taken.claim, provenance=taken.provenance)
        print(json.dumps(prepared, indent=2, sort_keys=True), file=stream)
        return 0

    with open(taken.provenance, "rb") as handle:
        supplied = json.loads(handle.read().decode("utf-8"))
    path = bind(chosen, taken.destination, claim=taken.claim,
                provenance=supplied["provenance"],
                compatibility=supplied["compatibility"])
    held_packet(path)
    print(json.dumps({"packet": path, "proved": True}, indent=2,
                     sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    try:
        raise SystemExit(main())
    except PacketRefusal as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        raise SystemExit(2)
