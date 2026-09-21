"""Compose the DETERMINISTIC heterogeneous verification pool. W202663 step 8.

claim208217, on the owner's replacement instance
`/home/sl/baton-v12/instance-2026-09-19T02-05-20Z` (pass event 208215), whose
installed runtime is sha256 `48b12f15...` -- the artefact built from the
corrected tree.

WHAT THIS PROVES THAT THE CLAUDE POOL CANNOT. Owner 206702 forbids live models,
and the Claude pool's implementation and review workers enter a real provider.
This pool runs the SAME lifecycle on two DETERMINISTIC fixture images built in
this claim -- W198667's reviewed worker bytes at two entrypoints,
`proposing_entry` for the producer and reviewer and `importing_entry` for the
integrator -- so the Job can be submitted and carried to a terminal state with
no model anywhere.

AND IT IS HETEROGENEOUS ON PURPOSE. W197661's fixture recipe had to be ONE image
because a Job named one input identity; its own comment records that a second
image was built and "three validators refused the composition". Two images here
is the composition that was refused then, served now, through the INSTALLED
runtime.

IT COMPOSES ONLY. Bootstrapping, starting and submitting are separate operator
steps, run and recorded in the dossier rather than performed here.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/home/sl/src/baton")
sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

DEST = Path("/home/sl/baton-v12/instance-2026-09-19T02-05-20Z")
UUID = "cf92cbff7ffc456c96e9a6345de293f5"
WORK = "cf92cbff-W2"
JOB = "w202663-deterministic-verification-2"
TARGET_ID = "w202663-verification-target"
CREATED = "2026-09-19T02:35:00.000Z"
ROLES = ("implementation", "review", "integration")


def select_pr():
    """Compose the owner-selected PR shape: producer and reviewer only.

    OWNER-HANDOFF-PR-JOBS (claim220329): a Job's success is a durable
    REVIEWED candidate -- attributable commit, base, changed paths, test
    evidence, independent review -- and integration is a human act (or a
    separately submitted ordinary Job), never an obligatory automatic
    stage. So a PR-mode Job composes TWO stages and TWO workers, no
    integration worker at all: `integration_served`'s one-integrator gate
    is never reached, `worker_for` never meets an integration allocation,
    and the whole D10 contradiction has nothing to bind to. The deployment
    keeps its integration_target/workspace/observer members -- deployment
    facts, harmless while nothing integrates.
    """
    global ROLES
    ROLES = ("implementation", "review")
    return {"pr": True, "roles": list(ROLES)}

# THE OWNER'S OWN WORDS, resolved to identities. "Configure distinct Claude
# coder and reviewer identities": two participants, never one, so
# `stage_execution._independent` is satisfied by construction rather than by
# convention. The integrator is `baton.merge`, which `AGENTS.md` names as the
# proposal-integration identity and which the instance's own
# `integration_profile` already carries.
# ONE PARTICIPANT PER WORKER, ACROSS THE WHOLE POOL. Measured in this claim:
# adding a second Job whose workers reused the first Job's three participants
# refused at start with "a worker pool names one participant per worker;
# duplicate participant values are not distinct capacity". Six workers need six
# identities -- the rule is about the POOL, not about one Job -- so this run's
# three carry their own suffix and the first run's three are preserved exactly
# as they were recorded.
ACTORS = {"implementation": "baton.fixture-coder-2",
          "review": "baton.fixture-reviewer-2",
          "integration": "baton.fixture-integrator-2"}

# THE ARTEFACTS W202663 BUILT, by digest. Not tags: a tag is a name
# somebody can move, and what a manager pins is a content digest.
#
# REBUILT AT CLAIM219950, review219927: the task-derived candidate
# correction lived in `fixture-context/worker/proposing_agent.py` and in NO
# image -- the recipes COPY those bytes at build time, so editing the host
# file changed nothing any container launches. Both consumers of
# `ProposingAgent` were rebuilt from the corrected context
# (FIXTURE-IMAGE-INPUTS-219950.json records the exact COPY inputs BEFORE the
# builds; the two IMAGE-TASK-DERIVATION-*-219950.json records prove each
# built image emits the task-derived file for two successive distinct
# tasks, the second based on the first's output). The HISTORICAL digests
# stay recorded here because every already-bound Job keeps the image it was
# bound to: silent producer sha256:6ae290f9135c4c79bf2a74c2425deb839bccf771
# 90927bf6529cf34bd622423f (claim207111), emitting producer sha256:e48e72df
# aaed321a34f1bfdd8ceca260c63d852c3fdc625da1458b02eaf7e9e8 (claim208916).
# The integrator copies `importing_agent.py`, not `ProposingAgent`, and is
# unchanged.
PROVIDER_IMAGE = ("sha256:3c43c4e3ffa6e40e005f32a378738fc60fd897c0f93ba"
                  "6fd2edcee4b9627fe57")
INTEGRATION_IMAGE = ("sha256:9944eef7363e8f8fd0d917bd71fbe19dfb177b6232b70"
                     "64f3c3a4785f307be0f")
IMAGES = {"implementation": PROVIDER_IMAGE,
          "review": PROVIDER_IMAGE,
          "integration": INTEGRATION_IMAGE}

# WHICH BUILD CONTEXT EACH IMAGE WAS MADE FROM, measured per image, because the
# two recipes copy different file sets and a toolchain digest that described
# the union would describe neither artefact.
RECIPES = {"implementation": "fixture-context/Dockerfile.producer",
           "review": "fixture-context/Dockerfile.producer",
           "integration": "fixture-context/Dockerfile.integrator"}

# THE EMITTING PRODUCER, built in claim208916 for review208890: the same
# reviewed candidate production plus deterministic prose on the wrapper's
# stdout and stderr, because a silent fixture cannot satisfy nonempty retained
# logs. Selected by `--emitting` for the IMPLEMENTATION role only; the review
# worker stays on the silent producer image so one lifecycle measures both an
# emitting and a silent capture, and the pool stays heterogeneous three ways.
# Rebuilt at claim219950 from the corrected context (see PROVIDER_IMAGE's
# note); the claim208916 digest e48e72df... stays recorded there as history.
EMITTING_IMAGE = ("sha256:4638bae661096c8169c446058b09c63507f06b63707349525"
                  "f814c6ad5125c38")
EMITTING_RECIPE = "fixture-context/Dockerfile.emitting"


def select_emitting():
    """Serve the implementation role from the emitting producer image."""
    IMAGES["implementation"] = EMITTING_IMAGE
    RECIPES["implementation"] = EMITTING_RECIPE
    return {"implementation_image": EMITTING_IMAGE,
            "implementation_recipe": EMITTING_RECIPE}

# THE CREDENTIAL SLOT, and what is behind it. `tools/integration_worker`
# requires the literal "claude" slot, and `tools/single_worker` refuses an
# empty slot list, so a deployment cannot express "this worker reads no
# bearer". W197661 recorded that as a deployment limitation and it is unchanged
# here.
#
# WHAT THIS COMPOSITION PUTS BEHIND THE SLOT IS THE OPERATOR'S OWN SOURCE,
# NAMED AND NOT READ. This package neither opens, copies, hashes nor stages any
# credential; it writes a registry LOCATOR into the deployment and the operator
# supplies what is behind it. Composing this grants no access to anything and
# claims no authentication coverage.
SLOT = "claude"
# THE SYNTHETIC NON-BEARER SOURCE, written by this run, exactly as W197661
# did it and for the reason it recorded: `single_worker` calls
# `credentials.resolved_delivery` unconditionally and refuses an empty slot
# list, so a deployment cannot express "this worker reads no bearer", and
# `integration_worker.REQUIRED_CREDENTIAL_SLOT` fixes the NAME to "claude".
# What is behind the name is a marker that authorizes nothing, and the fixture
# agents never open the slot. No real credential is read, reused or harvested,
# and no authentication coverage is claimed.
FIXTURE_PROVIDER = "w202663-synthetic-fixture"
FIXTURE_REFERENCE = "non-bearer-marker"
NOT_A_CREDENTIAL = (
    "NOT-A-CREDENTIAL w202663 synthetic fixture marker; this file authorizes "
    "nothing, authenticates to nothing and was written by "
    "compose-verification-208217.py to satisfy a deployment that cannot "
    "express an empty credential delivery\n")
CREDENTIAL_SOURCES = str(DEST / "credentials/registry.json")
CREDENTIAL_REFERENCE = {"provider": FIXTURE_PROVIDER,
                        "reference": FIXTURE_REFERENCE}

# WHAT ONE BOOTSTRAP RUN DOES TO THIS AUTHORITY'S APPROVAL POLICY GENERATION,
# MEASURED HERE rather than assumed. A first capacity bootstrap over a fresh
# install also creates the Work, its routes, its grants and the canonical
# target, so it moves further than a repeat does. Observations of THIS
# instance, not a contract: 1 -> 9 on the first (claim207219).
FIRST_BOOTSTRAP_BUMP = 8
REPEAT_BOOTSTRAP_BUMP = 7

_REVISION = re.compile(r"\A[0-9a-f]{40}\Z")


class Unmeasured(Exception):
    """A fact this composition refuses to invent."""


def digest(value):
    from baton_v12.contracts import canonical

    return canonical.digest(value)


def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


# -- measured provenance ------------------------------------------------------


ACCEPTED_BASE = None


def select_base(reference):
    """Compose against an EXPLICIT accepted reference (review221919).

    Owner 2026-09-20T14:57:48Z: the successor Job's base is the
    human-accepted reference, an OPAQUE input carried verbatim into the
    task, the line binding and the manifests -- never derived from any
    deployment repository. `--base <reference>` supplies it; without the
    flag, `declared_base` keeps reading the dedicated target's own refs
    exactly as before, which remains right for the integration-flow
    compositions this file's history records.
    """
    global ACCEPTED_BASE
    if not _REVISION.match(reference or ""):
        raise Unmeasured("--base carries a 40-lowercase-hex reference")
    ACCEPTED_BASE = reference
    return {"accepted_base": ACCEPTED_BASE}


def declared_base(target=None):
    """The instance target's own current main revision, read from its refs.

    A file read and never a version-control mutation, exactly as W197661's
    composer does it: `line_declared_base` is the revision every checkpoint on
    this line is declared against, and a constant would describe some other
    repository.

    THE DEFAULT IS RESOLVED AT CALL TIME, NOT AT DEFINITION TIME. Measured on
    the first installed run (claim208777): `target=DEST / "repo/target.git"`
    in the signature bound the HISTORICAL instance's path when the module
    loaded, so `--instance` selected every other fact for the new destination
    while the line's declared base still read the old target -- the same
    import-time-default defect review208585 [R2] named in the pin check. The
    integration then refused with target-drift, correctly: the candidate was
    reviewed against a revision its target was never at.
    """
    if target is None:
        target = DEST / "repo/target.git"
    loose = Path(target) / "refs/heads/main"
    if loose.is_file():
        found = loose.read_text().strip()
    else:
        packed = Path(target) / "packed-refs"
        if not packed.is_file():
            raise Unmeasured(f"{target} has neither refs/heads/main nor "
                             f"packed-refs")
        found = ""
        for line in packed.read_text().splitlines():
            if line.endswith(" refs/heads/main"):
                found = line.split(" ", 1)[0].strip()
                break
    if not _REVISION.match(found):
        raise Unmeasured(f"the target's main ref reads {found!r}, which is not "
                         f"one revision")
    return found


def principals(*, opener=None):
    """Who each participant IS, asked of the instance's own Authority."""
    from tools import bootstrap

    places = bootstrap.layout(str(DEST))
    document = {
        "authority_uuid": UUID,
        "receipt_participants": dict(RECEIPTS),
        "integration_profile": {
            "integrator_participant": ACTORS["integration"]},
        # EVERY PARTICIPANT IN THE FINAL POOL, not just this run's three.
        # `bootstrap.configuration` derives each worker's principal by looking
        # it up here, and the preserved workers from the first Job are in that
        # pool too -- asking only for the new ones raised
        # `KeyError: 'baton.fixture-coder'` inside this composer's own
        # validation while the installed command, which derives them itself,
        # was perfectly happy. A composer that validates a narrower document
        # than it writes is not validating what it writes.
        "workers": [{"participant": one} for one in sorted(
            set(ACTORS.values())
            | {one["participant"] for one in prepared_workers()})]}
    return bootstrap.principals_for(places, document, opener=opener)


RECEIPTS = {"verification": "baton.fixture-verifier",
            "review": "baton.fixture-judge",
            "approval": "baton.fixture-approver"}

# THE INTEGRATION OBSERVER, review212187's find: an APPROVED, IMPLEMENTED
# decision already covers consecutive-Job continuity --
# AMENDMENT-direct-target-finalization-v1.md (owner137905): the coordinator
# delivers the accepted candidate and CAS-advances the configured target
# reference BEFORE Authority completion, so the repository moves WITH the
# canonical-target policy. `driver._authority_completed` runs
# `execution.finalize_direct_target` only when the deployment supplies
# `finalize`, and `Integration._run` supplies it only when
# `deployment.reconciles()` -- which requires `integration_target`,
# `integration_workspace` AND `integration_observer`. This composition set
# the first two and never the third, so every measured divergence (D5's
# poisoned successor, the claim212143 publication refusal) ran with the
# finalizer silently disabled. The observer is a PARTICIPANT, the identity
# that runs a reconciled result's causal harness, and W133117 requires it
# distinct from the three judges and the integrator -- so it is a fourth
# fixture identity, deployment-scoped, not per-Job.
OBSERVER = "baton.fixture-observer"


def policy_pin(*, opener=None):
    """The generation this composition predicts the bootstrap will leave.

    ASKED, then CHECKED afterwards by `check_policy_pin`. W197661 measured that
    `bootstrap` bumps the Authority's approval policy generation on every run
    while the pin travels IN to that same run, so a composition that restated a
    literal would emit a deployment which cannot satisfy its own pin and would
    defer at its first integration with the reason only in a tick report.

    THE NUMBERS ARE OBSERVATIONS OF THAT TREE, NOT A CONTRACT. W197661 measured
    1 -> 9 for a first capacity bootstrap over a fresh install and seven per
    repeat afterwards. They are used only to PROPOSE a pin.
    """
    from baton_v12.authority import Authority

    open_authority = opener or Authority.open_readonly
    authority = open_authority(str(DEST / "db/authority.sqlite3"),
                               expected_authority_uuid=UUID)
    try:
        held = authority.policy_generation()
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()
    if type(held) is not int or held < 1:
        raise Unmeasured("the Authority did not answer a policy generation")
    # THE BUMPS ARE MEASURED ON THIS INSTANCE, not copied from W197661's tree.
    #
    # claim207219 ran the first capacity bootstrap here and the Authority moved
    # 1 -> 9: a bump of EIGHT, where W197661 observed 8 on its own first run and
    # 7 per repeat. My first prediction used 8 and `check_policy_pin` reported
    # configured 8 against generation 9 -- the prediction was of the generation
    # BEFORE the bootstrap plus the bump, and I had added the bump to a reading
    # taken when the generation was 1 while the pin has to equal what the
    # bootstrap LEAVES. The reading and the bump are both right; only which
    # bootstrap they describe was wrong.
    #
    # STILL A PREDICTION, AND STILL CHECKED. `check_policy_pin` runs after the
    # bootstrap against the Authority itself and is what decides whether this
    # was right; a number that agreed with itself would prove nothing.
    # THE BUMP IS PER WORK, MEASURED HERE. With one Work this destination
    # moved 9 -> 16 and 16 -> 23, seven each. With TWO Works it moved 23 -> 37
    # and 37 -> 51, FOURTEEN each -- because a bootstrap certifies contracts
    # and permits transitions for every Work it prepares, so the cost scales
    # with how many there are. A prediction that kept adding seven was wrong
    # twice in this claim and `check_policy_pin` said so both times.
    #
    # STILL A PREDICTION. What decides is the check after the bootstrap.
    # PER JOB PREPARED, NOT PER DISTINCT WORK. Measured on
    # instance-2026-09-19T04-02-31Z (claim209102): a repeat bootstrap adding
    # one new Job beside one preserved Job -- BOTH bound to the same Work --
    # moved the generation 9 -> 24 while the per-Work model predicted +7. The
    # old instance's two-Job bootstraps (each Job on its own Work) moved +14
    # per repeat, which the per-Work model matched only by coincidence of one
    # Work per Job. STILL A PREDICTION, checked by check_policy_pin after
    # every apply; the gate is what caught this one.
    # AND THE REPEAT COST IS NOT UNIFORM PER JOB, measured at claim220080 on
    # instance-2026-09-20T10-23-11Z: an apply ADDING a job beside one held
    # moved 9 -> 24 (+15 = 7x2 + 1), while re-applies preparing the same two
    # jobs moved 24 -> 37 and 37 -> 50 (+13 each = 7x2 - 1) -- the per-job
    # seven double-counts something shared exactly once per NEW preparation.
    # The gate caught the flat per-job model twice in one claim. STILL a
    # prediction, still checked after every apply.
    # PR MODE COSTS ONE LESS PER PREPARATION, measured at claim222138 on
    # the fresh 15-53-26Z instance: the first PR bootstrap moved 1 -> 8
    # (+7) where the three-stage first apply measured +8 -- the absent
    # integration stage certifies one transition fewer. Same reduction per
    # job on repeats, and the gate still checks every prediction.
    pr = "integration" not in ROLES
    # FIRST means NO DEPLOYMENT RECORD, not no job store (claim222138,
    # measured on the fresh PR instance): the JOB STORE is created by the
    # first START, so a deployment composed and re-composed before any
    # start read every compose as "first" and predicted the fresh bump on
    # repeat applies -- the gate caught it three times in a row. The
    # record `bootstrap` itself persists is what distinguishes a prepared
    # root from a fresh one.
    first = _prepared() is None
    jobs = len(_all_jobs()) or 1
    if first:
        return held + FIRST_BOOTSTRAP_BUMP - (1 if pr else 0)
    selected_already = any(
        one["worker_id"].startswith(JOB + "-")
        for one in (_prepared() or {}).get("workers", []))
    # PR REPEATS COST EXACTLY SIX PER JOB, no extra either way
    # (claim222268, measured twice: 26 -> 38 adding verification-2 and
    # 38 -> 50 re-applying both, +12 = 6x2 each time); the three-stage
    # extras stand as measured on their own instances.
    extra = 0 if pr else ((1 if not selected_already else 1 - jobs))
    return held + (REPEAT_BOOTSTRAP_BUMP - (1 if pr else 0)) * jobs + extra


def _all_jobs():
    """Every Job the next bootstrap will prepare: the held ones and this one."""
    return prepared_jobs() + [{"job_id": JOB, "work_id": WORK}]


def check_policy_pin(*, opener=None, pin=None):
    """The post-bootstrap equality, as an executable gate rather than a note."""
    from baton_v12.authority import Authority

    if pin is None:
        configured = json.loads((DEST / "deployment.json").read_text())
        pin = configured.get("policy_generation")
    open_authority = opener or Authority.open_readonly
    authority = open_authority(str(DEST / "db/authority.sqlite3"),
                               expected_authority_uuid=UUID)
    try:
        held = authority.policy_generation()
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()
    return {"configured_pin": pin, "authority_generation": held,
            "equal": pin == held}


def image_present(image, *, run=None):
    """Whether the engine really holds this image. Starts no container."""
    runner = run or (lambda argv: subprocess.run(
        argv, capture_output=True, text=True, timeout=60))
    try:
        found = runner(["docker", "image", "inspect", "--format", "{{.Id}}",
                        image])
    except Exception as failure:                             # noqa: BLE001
        return {"asked": True, "held": None,
                "why": type(failure).__name__}
    held = (found.stdout or "").strip()
    return {"asked": True, "held": held == image, "reported_id": held or None}


def toolchain_of(recipe):
    """What ONE fixture recipe was built from: its own bytes and its context.

    NOT `copied-inputs-207111.py`'s reader. That one resolves a recipe's COPY
    sources against the `v12` build context, which is the right root for the
    two supported images and the wrong one for these: the fixture recipes and
    every byte they copy live under this dossier, snapshotted with attribution
    in `fixture-context/`. Pointing the other reader here would have it look
    for `v12/fixture-context/...`, which is the failure this replaces.

    THE WHOLE CONTEXT IS MEASURED, not just the copied set, because the context
    IS the fixture: it holds exactly the files the two recipes carry and
    nothing else, so a byte that appeared in it without a COPY would still be a
    change to what was built and should still move this digest.
    """
    place = HERE / recipe
    root = place.parent
    found = {}
    for one in sorted(root.rglob("*")):
        if one.is_file() and "__pycache__" not in one.parts:
            found[str(one.relative_to(root))] = sha(one)
    if not found:
        raise Unmeasured(f"the fixture build context {root} holds no file")
    return digest({"recipe": recipe, "recipe_sha256": sha(place),
                   "context": found})


def adapter_identity():
    """The adapter's measured bytes, as a durable identity."""
    place = REPO / "v12/python/src/baton_v12/worker_manager/oci.py"
    return {"adapter_name": "docker-single-worker", "sha256": sha(place),
            "path": str(place.relative_to(REPO)),
            "what_it_does_not_prove": "a file digest identifies the adapter "
                                      "this deployment names; it is not "
                                      "evidence that the adapter ran"}


def record_binding():
    """This Work's own canonical dossier, digested where it actually lives."""
    finding = HERE / "FINDING.md"
    plan = HERE / "PLAN.md"
    for place in (finding, plan):
        if not place.is_file():
            raise Unmeasured(f"{place} is not here; a record binding names a "
                             f"record that exists")
    return {"root": "baton",
            "path": "work/records/2026/09/finding-v12-initial-claude-worker-pool",
            "finding_digest": sha(finding), "plan_digest": sha(plan)}


# -- the documents ------------------------------------------------------------


def policy_documents(facts):
    """This deployment's policy layer, over THIS destination's paths."""
    return {
        "policy": {"work": "W202663",
                   "ruling": "owner 206702: workers select their own immutable "
                             "images; provider image, credential profile, role "
                             "and participant remain separate",
                   "base": facts["declared_base"],
                   "submission": [JOB],
                   "automatic_retry": False,
                   "review_before_execution": True},
        "resource_policy": {"wall_seconds": 3600,
                            "implementation_attempt_seconds": 900,
                            "review_or_judge_attempt_seconds": 600,
                            "integration_seconds": 300,
                            "runtime_cpus": 2,
                            "runtime_memory_bytes": 4294967296,
                            "runtime_pids": 512,
                            "workspace_declared_capacity_bytes": 2147483648,
                            "workspace_capacity_is_quota": False,
                            "deadline_action": "stop; retain evidence; "
                                               "no retry"},
        "network_policy": {"engine_network": "none",
                           "purpose": "a deterministic fixture reaches nothing; "
                                      "the synthetic slot grants access to no "
                                      "service"},
        "mount_policy": {"source": "read-only nominated source and a "
                                   "manager-held private development line",
                         "mutable_storage": str(DEST / "workers/implementation/storage"),
                         "workspace_group": facts["workspace_group"],
                         "target": str(DEST / "repo/target.git"),
                         "target_reference": "refs/heads/main"},
        "tool_policy": {"provider_arguments": [],
                        "model_selection": "the provider image's own default; "
                                           "NO model is selected here and none "
                                           "is reached by composing this",
                        "verification": [],
                        "final_verification": []},
        "credential_policy": {"registry": CREDENTIAL_SOURCES,
                              "slots": {SLOT: dict(CREDENTIAL_REFERENCE)},
                              "payload_in_configuration": False,
                              "read_by_this_composition": False},
        "retention_policy": {"disposition": "retain", "root": str(DEST),
                             "automatic_deletion": False}}


def _pool_generation_prediction(dest, workers):
    """The generation the NEXT activation will answer, read, not restated.

    claim219702, sharpened at claim220080. The scheduler mints generation 1
    over an absent pool, re-answers the current generation for an identical
    membership, and mints the next one for a changed one. The first reading
    of that rule checked only whether the selected Job's implementation
    worker was already a member -- and the one-integrator correction
    (`prepared_workers`) changes membership by REMOVING a worker, which that
    check cannot see. So the prediction now compares the WHOLE composed
    membership -- (worker id, role, participant) triples -- against the
    current generation's own rows. A wrong prediction still refuses at
    activation while nothing has been written; the gate, not this
    arithmetic, is what protects the deployment.
    """
    place = dest / "db/jobs.sqlite3"
    if not place.is_file():
        return 1
    import sqlite3
    held = sqlite3.connect(f"file:{place}?mode=ro", uri=True)
    try:
        current = held.execute(
            "select max(generation) from pool_generations").fetchone()[0]
        if current is None:
            return 1
        rows = {(one, role, participant) for one, role, participant
                in held.execute(
                    "select worker_id, lane, participant from pool_workers "
                    "where generation = ?", (current,))}
    finally:
        held.close()
    # THE SCHEDULER'S LANE IS THE COMPOSED ROLE'S LANE: integration workers
    # serve on the implementation lane (`scheduler._lane`), so the composed
    # role is mapped the same way before comparing.
    composed = {(one["worker_id"],
                 "implementation" if one["role"] == "integration"
                 else one["role"],
                 one["participant"]) for one in workers}
    return current if composed == rows else current + 1


def task_document(facts):
    """The deterministic workload, in the contract the fixture image reads.

    THE SAME SHAPE W197661'S ACCEPTED LIFECYCLE USED, because `ProposingAgent`
    is that record's reviewed stand-in and this is the task it was written
    against: add exactly one named file with exactly one declared line, and
    change nothing else.

    THE FILENAME AND CONTENT ARE THE FIXTURE'S OWN, and review208349 is why.
    `ProposingAgent` writes `w197661-fixture.txt` holding
    "w197661 deterministic fixture candidate" and does NOT read the task
    instructions -- it is a deterministic stand-in, not a model. My first task
    asked for a `w202663-` name and its verification asserted that, so the
    producer's required tests exited 1 and the installed manager deferred the
    integration with "a failing required command is not admitted and an
    accepted technical review is not a substitute". The check is right; the
    task was wrong. Aligning the task to the artefact is the correction --
    weakening the verification, or manufacturing receipts, would be defeating
    the gate that caught it.

    THE VERIFICATION COMMAND IS REQUIRED AND IS A REAL CHECK.
    `Integration.required_tests` refuses a task naming none, and W197661
    measured that every integration tick deferred with exactly that reason
    while its two earlier stages sat completed. This asserts the one file the
    assignment exists to produce holds exactly the declared bytes; it reads and
    writes nothing else, and it is python with no shell -- the producer runs it
    inside a line whose cleanliness the freeze depends on, and the integrator
    runs the SAME argv again over the imported tree.
    """
    # THE CANDIDATE IS TASK-DERIVED, claim219702. The fixed name was measured
    # EMPTY on the first installed A-then-B run: Job A's candidate integrated
    # into the canonical target, Job B materialized AT that advanced base, and
    # B's identical fixed file staged nothing -- `git commit` exited 1 and the
    # turn faulted. A deterministic fixture must be deterministic PER
    # ASSIGNMENT, not identical ACROSS assignments whose base already carries
    # its output; deriving the name and line from `task_id` keeps two runs of
    # one assignment byte-identical while distinct Jobs propose distinct
    # candidates. The fixture derives the SAME strings from the same field.
    name = f"w197661-fixture-{JOB}.txt"
    line = f"w197661 deterministic fixture candidate for {JOB}"
    return {
        "schema": "baton.dogfood-task/2",
        "task_id": JOB,
        "instructions":
            f"Add exactly one file, {name}, at the root of the "
            "read-only source you are given a private line over. Its whole "
            "content is the single line "
            f"'{line}' followed by one "
            "newline. Change nothing else: no existing file, no mode, no "
            "version-control configuration. Then write the declared outputs "
            "and end the turn. This is a deterministic fixture assignment and "
            "no model is consulted for it.",
        "source_root": "source",
        "source_profile": "git-line",
        "declared_base": facts["declared_base"],
        "verification": ["python3", "-c",
                         f"import pathlib,sys;sys.exit(0 if pathlib.Path("
                         f"'{name}').read_text() == '{line}\\n' else 1)"]}


def role_instruction_documents():
    """What each stage is told. Different text per role, deliberately.

    The ROLE INSTRUCTIONS ARE PER-WORKER under owner ruling 206702 and are
    projected out of the Job input identity for exactly that reason: an
    implementer and a reviewer are not told the same thing.
    """
    return {
        "implementation": "You are the Claude coder. Produce the candidate the "
                          "frozen task describes and the tests that go with "
                          "it. Change nothing outside the scope it names.",
        "review": "You are the Claude reviewer, and you did not write this "
                  "candidate. Read the frozen checkpoint and accept it only if "
                  "it delivers the task's outcome without weakening an "
                  "existing rule; otherwise request changes and say which rule "
                  "was broken.",
        "integration": "Import exactly the accepted candidate onto the "
                       "canonical target. Refuse anything outside the "
                       "candidate rather than repairing it."}


def manifest_for(role, facts, *, seal):
    """ONE sealed input manifest per WORKER, sharing one Job input identity.

    THIS IS THE FIRST COMPOSITION THAT CAN DO THIS. W197661 needed one manifest
    for all three roles because `_matches` compared a Job's single input digest
    against a worker's WHOLE manifest digest; W202663 corrected that to the
    Job-scoped projection, so each worker now carries its own manifest naming
    its own image, and all three project to one value.

    WHAT DIFFERS PER ROLE is exactly the worker-runtime axis the correction
    projects out -- image, toolchain, role instructions, manifest id and
    creation instant. Everything the JOB owns is identical by construction,
    because it is composed from the same `facts`.
    """
    from tools import dogfood_operator
    from baton_v12.worker_manager import source_boundary

    empty = {"entries": [], "entry_count": 0, "total_bytes": 0,
             "tree_digest": facts["empty_tree_digest"]}
    given = dogfood_operator.input_manifest(
        work_ref={"authority_uuid": UUID, "work_id": WORK}, staged=empty,
        created_at=CREATED, manifest_id=f"input-{JOB}-{role}",
        assignment_contract="v12-assignment-1",
        human_contract={"artifact_id": JOB,
                        "media_type": "application/json",
                        "bytes": facts["task_bytes"],
                        "content_digest": facts["task_digest"],
                        "locator": f"artifact://contracts/{JOB}"},
        record_binding=facts["record_binding"],
        role_instructions_digest=facts["role_instructions_digest"][role],
        runtime_profile_digest=facts["profile_digest"],
        toolchain_digest=facts["toolchain_digest"][role],
        worker_image_digest=IMAGES[role], policies=facts["policy_digests"])
    given["sources"][0]["consumption"] = \
        source_boundary.source_consumption("git-line")
    constraints = {"max_bytes": 67108864, "max_entries": 2000,
                   "allowed_media_types": ["application/octet-stream",
                                           "text/plain"],
                   "link_policy": "forbid", "validator_digest": None}
    given["outputs"] = [
        {"name": one, "type": kind, "path": one, "required": False,
         "constraints": constraints}
        for one, kind in (("proposal", "git-change-proposal"),
                          ("findings", "directory-result"),
                          ("logs", "directory-result"))]
    given.pop("manifest_digest")
    given["manifest_digest"] = digest(given)
    return seal(given, "inputManifest")


def deployment_for(role, facts):
    """One role's complete single-worker deployment, on its OWN image."""
    return {
        "schema": "baton.v12.single-worker-deployment/4",
        "authority_store": str(DEST / "db/authority.sqlite3"),
        "authority_uuid": UUID,
        "participant": ACTORS[role],
        "principal": facts["principals"][ACTORS[role]],
        "profile_name": f"fixture-{JOB}",
        "profile_digest": facts["profile_digest"],
        "policy_digest": facts["policy_digests"]["policy_digest"],
        "adapter_name": facts["adapter"]["adapter_name"],
        "adapter_digest": facts["adapter"]["sha256"],
        "engine": "docker",
        "image_digest": IMAGES[role],
        "network": "none",
        # THE PATH IS THE ONE THIS MANAGER ALREADY HOLDS. A second start with
        # a different value refuses again -- "a changed store is a fresh store
        # rather than a reconfiguration" -- and the store this instance
        # recorded on its first start is the implementation worker's. Adopting
        # it costs nothing, avoids resetting a durable store to suit a
        # composition, and is exactly what the previous real deployment did:
        # its three workers all named the implementation worker's storage.
        #
        # ONE WORKSPACE STORE FOR THE WHOLE MANAGER, and it is not a
        # simplification. Measured in this claim's first live start through the
        # INSTALLED runtime: giving each role its own store refused with
        # "this manager is already configured with workspace store ... and is
        # being told to use ...; every attempt already allocated under the
        # first store would become unfindable, so a changed store is a fresh
        # store rather than a reconfiguration". The store is a MANAGER-scoped
        # fact; what is per-worker is the private launch and credential home,
        # which is where `stage_execution._independent` actually looks for
        # separation. W197661's accepted composition shares one store for the
        # same reason.
        "workspace_storage": str(DEST / "workers/implementation/storage"),
        "workspace_group": facts["workspace_group"],
        "launch_home": str(DEST / "workers" / role / "launch"),
        "credential_home": str(DEST / "workers" / role / "credentials"),
        "credential_sources": CREDENTIAL_SOURCES,
        "credential_slots": [SLOT],
        "credential_profile": {SLOT: dict(CREDENTIAL_REFERENCE)},
        "nominated_source": str(DEST / "repo/workspace"),
        "workspace_capacity": {"max_bytes": 2147483648},
        "input_manifest": facts["manifests"][role],
        "task_document": str(DEST / "jobs" / JOB / "task.json"),
        "launch_contract": "v12-assignment-1",
        "launch_role": role,
        "review_route": {"implementation": "rview", "review": "integration",
                         "integration": "integration"}[role],
        "retention_policy_digest":
            facts["policy_digests"]["retention_policy_digest"],
        "retention_disposition": "retain"}


def submission(facts):
    """The Job, naming the ONE Job input identity all three workers project to."""
    return {
        "schema": "baton.v12.job-submission/2",
        "submission_id": f"{JOB}-submission",
        "jobs": [{
            "job_id": JOB,
            "input_digest": facts["job_input_identity"],
            "policy_digest": facts["policy_digests"]["policy_digest"],
            "test_scope": [], "terminal_policy": "report-and-hold",
            "stages": [{"kind": kind, "work_id": WORK,
                        "profile_name": f"fixture-{JOB}",
                        "profile_digest": facts["profile_digest"],
                        "depends_on": (
                            [] if kind == "implementation" else
                            [{"job_id": JOB, "kind": "implementation"}]
                            if kind == "review" else
                            [{"job_id": JOB, "kind": "review"}])}
                       for kind in ROLES]}]}


def bootstrap_inputs(facts):
    """What the installed `bootstrap` command is handed to supply capacity."""
    workers = prepared_workers() + [
        {"worker_id": f"{JOB}-{role}", "role": role,
         "participant": ACTORS[role],
         "deployment": deployment_for(role, facts)}
        for role in ROLES]
    return {
        "schema": "baton.v12.stack-bootstrap/1",
        "state_root": str(DEST),
        "checkpoint_profile": "git",
        "integration_profile": {
            "profile_kind": "git", "profile_version": 1,
            "integrator_participant": ACTORS["integration"],
            "instructions_digest": facts["integration_instructions_digest"]},
        "retention_policy_digest":
            facts["policy_digests"]["retention_policy_digest"],
        "retention_disposition": "retain",
        # THE POOL GENERATION ADVANCES WITH THE POOL. Measured here: adding
        # this run's three workers beside the first Job's three changed the
        # pool, so the durable pool answers generation 2 while a configuration
        # still naming 1 refuses at activation -- "a deployment resuming
        # against a pool that has moved on refuses before it activates one
        # rather than after". Immutable pool generations are W71877's; a
        # changed membership is a new generation, not an edit to the old one.
        #
        # PREDICTED PER INSTANCE, not restated as a constant. The scheduler's
        # own rule (`stage_execution._pool_generation`): an ABSENT pool means
        # the next activation mints generation 1. Like the policy pin, this
        # is a PREDICTION and the activation itself is what checks it -- a
        # wrong one refuses at start while nothing has been written.
        #
        # READ FROM THE DURABLE POOL, claim219702. The previous two-state
        # prediction (2 when the store exists, else 1) was the claim208217
        # measurement generalized one step too little: the THIRD compose on
        # one instance predicted 2 while activation would mint 3, and the
        # start refused with exactly the recorded sentence -- the gate
        # working, the prediction stale. The rule it now follows is the
        # scheduler's own: a membership this compose CHANGES mints the next
        # generation; one it leaves identical re-answers the current one.
        "pool_generation": _pool_generation_prediction(DEST, workers),
        "policy_generation": facts["policy_generation"],
        "receipt_participants": dict(RECEIPTS),
        "integration_target": str(DEST / "repo/target.git"),
        "integration_target_reference": "refs/heads/main",
        "integration_workspace": str(DEST / "repo/workspace"),
        # WITH THE OBSERVER, `reconciles()` answers True and the approved
        # direct-target finalization (owner137905) actually runs: the target
        # reference advances with the policy at each integration, which is
        # what consecutive Jobs on one instance require. See OBSERVER above.
        "integration_observer": OBSERVER,
        "integration_instructions": str(DEST / "integration-instructions.txt"),
        "workers": workers,
        "jobs": prepared_jobs() + [
            {"job_id": JOB, "work_id": WORK,
             "line_declared_base": facts["declared_base"],
             "canonical_target_id": TARGET_ID,
             "source_worker_id": f"{JOB}-implementation"}]}


# -- what is already prepared here, preserved verbatim ------------------------
#
# A REPEATED BOOTSTRAP PRESERVES WHAT IS THERE, and the installed command says
# so in its own refusal: "job 'w202663-deterministic-verification' is already
# prepared here and this document does not name it; a Job that stops being
# named is not thereby unconfigured." Review208349 required the first run's
# immutable Job, task and attempt evidence to be preserved while a corrected
# one is added under fresh identities -- and the product enforces exactly that.
#
# THE OLD WORKERS TRAVEL AS THEY WERE RECORDED, read back out of the
# destination's own emitted configuration rather than recomposed. Recomposing
# them would re-derive digests from today's facts and silently rewrite the
# deployment the first run actually ran under, which is the rewrite this must
# not perform.


def _prepared():
    place = DEST / "deployment.json"
    if not place.is_file():
        return None
    return json.loads(place.read_text())


def prepared_workers():
    """Every retained worker except the selected Job's own -- INCLUDING, for
    now, prior integration workers, and D10 (claim220080) is why "for now"
    is pinned rather than silent.

    Measured installed on the first A-then-B run, BOTH directions:

    - WITH per-Job integrators retained (this shape), the second Job's
      integration LAUNCH defers every tick at
      `stage_execution.integration_served`: "this deployment names 2
      integration workers; one deployment names one integrator" -- while its
      line, checkpoint, verdict and eligibility all sit ready.
    - WITH prior integrators dropped (one integrator composed), the manager
      DIES at the first sweep instead: `stage_execution.worker_for` refuses
      observing SETTLED history ("stage 'verification-1/integration' is
      allocated to worker 'verification-1-integration', which this
      deployment does not configure") -- the same defect class D7 fixed at
      the scheduler, alive in the configuration-level resolver.

    With per-Job integrator IDENTITIES already durable in allocations, no
    configuration satisfies both gates, so consecutive Jobs cannot complete
    on one deployment. The resolutions are pinned in FINDING.md (a CONSTANT
    integrator identity composed from the first Job, and/or `worker_for`
    adopting D7's settled-history rule); choosing one moves either the
    measured one-participant-per-worker composition rule or a product
    contract, so it is returned for review/owner selection rather than
    taken here. This shape keeps the deployment STARTABLE and every
    already-allocated stage observable; the second Job's integration waits,
    deferred by name.
    """
    held = _prepared()
    if held is None:
        return []
    return [{"worker_id": one["worker_id"], "role": one["role"],
             "participant": one["deployment"]["participant"],
             "deployment": one["deployment"]}
            for one in held.get("workers", [])
            if not one["worker_id"].startswith(JOB + "-")]


def prepared_jobs():
    """Every Job this destination already holds, in the input's own shape.

    A `/1` configuration states its single Job's Work, base and target at the
    top level and names the producer through the worker set; a `/2` states each
    binding. Both are read here rather than assumed, because which one is on
    disk depends on how many Jobs were prepared last time.
    """
    held = _prepared()
    if held is None:
        return []
    bindings = held.get("job_bindings")
    if bindings:
        return [{"job_id": one["job_id"], "work_id": one["job_work_id"],
                 "line_declared_base": one["line_declared_base"],
                 "canonical_target_id": one["canonical_target_id"],
                 "source_worker_id": one["source_worker_id"]}
                for one in bindings if one["job_id"] != JOB]
    producing = [one["worker_id"] for one in held.get("workers", [])
                 if one["role"] == "implementation"]
    if not producing:
        return []
    # A `/1` DOCUMENT DOES NOT SPELL ITS JOB ID, so it is derived from the
    # producer's own name, which this package composes as `<job>-<role>`.
    job_id = producing[0][:-len("-implementation")]
    if job_id == JOB:
        return []
    return [{"job_id": job_id, "work_id": held["job_work_id"],
             "line_declared_base": held["line_declared_base"],
             "canonical_target_id": held["canonical_target_id"],
             "source_worker_id": producing[0]}]


# -- the validators, and the fail-closed run ----------------------------------

# `bootstrap.held` IS PURE and, since owner212383's amendment, no longer
# counts distinct bases -- that question is store-aware (`admissible_bases`,
# run by `prepare`/`prepare_repositories` against the root's persisted record
# and established target). So `complete: true` here claims document
# structure, NOT base admissibility; the apply is where that gate lives.
REQUIRED = ("check_manifest_structure", "bootstrap.held",
            "bootstrap.configuration", "stage_execution.held_configuration",
            "bootstrap.validated", "job_manager.documents.owned_submission")

AFTER_WRITING = "stage_execution.held_configuration (over the written files)"


def production_validators():
    """The canonical owner of each question, never a second opinion here."""
    from tools import bootstrap, stage_execution
    from baton_v12.contracts import check_manifest_structure
    from baton_v12.job_manager import documents as job_documents

    return {"check_manifest_structure": check_manifest_structure,
            "stage_execution.held_configuration":
                stage_execution.held_configuration,
            "job_manager.documents.owned_submission":
                job_documents.owned_submission,
            "bootstrap.held": bootstrap.held,
            "bootstrap.configuration": bootstrap.configuration,
            "bootstrap.validated": bootstrap.validated}


class Run:
    """One composition and the exact result of every validator it called."""

    def __init__(self, validators):
        self.validators = validators
        self.steps = []
        self.refused = []
        self.required = list(REQUIRED)

    def step(self, what, run):
        try:
            answer = run()
        except Exception as failure:                         # noqa: BLE001
            self.steps.append({"validator": what, "result": "REFUSED",
                               "refusal": f"{type(failure).__name__}: "
                                          f"{str(failure)[:800]}"})
            self.refused.append(what)
            return None
        self.steps.append({"validator": what, "result": "accepted"})
        return answer

    @property
    def complete(self):
        ran = {one["validator"] for one in self.steps
               if one["result"] == "accepted"}
        return not self.refused and all(one in ran for one in self.required)


def measured(*, run=None, opener=None):
    """Every fact this composition refuses to invent, asked of its owner."""
    from baton_v12.worker_manager import workspaces
    from tools import single_worker

    facts = {"declared_base": (ACCEPTED_BASE if ACCEPTED_BASE is not None
                               else declared_base()),
             "record_binding": record_binding(),
             "adapter": adapter_identity(),
             "empty_tree_digest": single_worker.EMPTY_TREE_DIGEST,
             "workspace_group": workspaces.__dict__.get("DEFAULT_GROUP")
             or __import__("os").getgid()}
    facts["principals"] = principals(opener=opener)
    facts["policy_generation"] = policy_pin(opener=opener)
    facts["image_in_engine"] = {
        role: image_present(IMAGES[role], run=run) for role in ROLES}
    facts["toolchain_digest"] = {role: toolchain_of(RECIPES[role])
                                 for role in ROLES}

    instructions = role_instruction_documents()
    facts["role_instructions"] = instructions
    facts["role_instructions_digest"] = {role: digest(instructions[role])
                                         for role in ROLES}

    policies = policy_documents(facts)
    facts["policies"] = policies
    facts["policy_digests"] = {
        f"{name}_digest": digest(body) for name, body in policies.items()}
    facts["profile_digest"] = digest({
        "profile": f"fixture-{JOB}", "images": dict(IMAGES),
        "adapter": facts["adapter"]["sha256"]})

    task = task_document(facts)
    facts["task"] = task
    payload = json.dumps(task, sort_keys=True).encode("utf-8")
    facts["task_bytes"] = len(payload)
    facts["task_digest"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    facts["task_payload"] = payload

    text = ("Import exactly the accepted candidate onto the canonical target. "
            "Refuse anything outside it.\n")
    facts["integration_instructions"] = text
    facts["integration_instructions_digest"] = (
        "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest())
    return facts


def compose(run, *, facts):
    """Every document, with each validator called as it becomes answerable."""
    from baton_v12.contracts import job_input_identity

    seal = run.validators["check_manifest_structure"]
    documents = {}

    facts["manifests"] = {}
    for role in ROLES:
        held = run.step(
            "check_manifest_structure",
            lambda role=role: manifest_for(role, facts, seal=seal))
        if held is None:
            return facts, documents
        facts["manifests"][role] = held

    # THE ONE JOB INPUT IDENTITY, PROVED RATHER THAN ASSUMED. Three workers on
    # two different images must project to one value; if they do not, this
    # composition is wrong and says so here rather than at a launch.
    identities = {role: job_input_identity(facts["manifests"][role])
                  for role in ROLES}
    if len(set(identities.values())) != 1:
        run.steps.append({"validator": "one Job input identity",
                          "result": "REFUSED", "refusal": repr(identities)})
        run.refused.append("one Job input identity")
        return facts, documents
    facts["job_input_identity"] = identities["implementation"]
    run.steps.append({"validator": "one Job input identity",
                      "result": "accepted"})

    inputs = bootstrap_inputs(facts)
    documents["bootstrap_inputs"] = inputs
    documents["submission"] = submission(facts)

    # THE INPUT DOCUMENT DOES NOT NAME THE AUTHORITY, and `held` refuses one
    # that does: an instance generates its identity once at install and
    # persists it at the destination, so a document naming one would be a
    # second place for a fact this instance already owns. The identity is
    # supplied to `configuration`, which DERIVES it into each worker, exactly
    # as the installed command does.
    held = run.step("bootstrap.held",
                    lambda: run.validators["bootstrap.held"](inputs))
    if held is not None:
        configuration = run.step(
            "bootstrap.configuration",
            lambda: run.validators["bootstrap.configuration"](
                dict(held, authority_uuid=UUID), facts["principals"]))
        if configuration is not None:
            documents["stage_execution"] = configuration
            run.step("stage_execution.held_configuration",
                     lambda: run.validators[
                         "stage_execution.held_configuration"](configuration))
            # `validated` HOLDS THE EMITTED CONFIGURATION, not the input: it
            # exists because an earlier cut of this helper validated what it
            # read and not what it wrote.
            run.step("bootstrap.validated",
                     lambda: run.validators["bootstrap.validated"](
                         configuration))
    run.step("job_manager.documents.owned_submission",
             lambda: run.validators["job_manager.documents.owned_submission"](
                 documents["submission"]))
    return facts, documents


def stage_inputs(facts):
    """The two files the DEPLOYMENT itself names, written at the destination.

    A deployment reads its task document and its integrator instructions from
    its own directory -- a running instance reads nothing out of this checkout
    -- so these are the one thing this package writes outside itself.

    THIS IS NOT A BOOTSTRAP AND TOUCHES NO STORE. It creates
    `jobs/<job>/task.json` and `integration-instructions.txt` under the
    destination the owner selected, whose pool is empty and whose Job bindings
    are none. No database is opened for writing, no Authority is composed, no
    prior instance is reached.

    THE BYTES ARE THE MEASURED ONES. `task_bytes` and `task_digest` were taken
    over exactly this payload before any manifest was sealed, so what the
    human contract declares is what the deployment will actually open --
    W197661 paid two rounds for writing an indented copy over a measured one.
    """
    import os

    place = DEST / "jobs" / JOB
    place.mkdir(parents=True, exist_ok=True)
    (place / "task.json").write_bytes(facts["task_payload"])
    (DEST / "integration-instructions.txt").write_text(
        facts["integration_instructions"])
    # THE DEPLOYMENT'S OWN DIRECTORIES, created here because the manager
    # refuses to invent them: `check_workspace_storage` demands an EXISTING
    # directory owned by this uid -- "is not a directory this manager can
    # see", measured on the fresh install at start-208777.log and before that
    # on the previous instance at manager-log-208349.txt. Naming a store is a
    # deployment act, so the deployment's composer is where the named
    # directories are made: per-role launch and credential homes, and ONE
    # workspace store (the implementation worker's -- manager-scoped, see
    # `deployment_for`). `repo/workspace` and `repo/target.git` are the
    # installer's and already exist.
    for role in ROLES:
        (DEST / "workers" / role / "launch").mkdir(parents=True,
                                                   exist_ok=True)
        (DEST / "workers" / role / "credentials").mkdir(parents=True,
                                                        exist_ok=True)
    (DEST / "workers" / "implementation" / "storage").mkdir(parents=True,
                                                            exist_ok=True)
    # THE SYNTHETIC NON-BEARER SOURCE AND ITS REGISTRY, written 0600 by this
    # run. `tools/user_credentials._proved_read` requires an ordinary file
    # owned by this uid with no group or other permission, so both are created
    # that way. Nothing is harvested: the marker says in its own text that it
    # is not a credential, and the fixture agents never open the slot.
    root = DEST / "credentials"
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    source = root / "w202663-synthetic-non-bearer"
    registry = Path(CREDENTIAL_SOURCES)
    document = {"schema": "baton.user-credential-sources/1",
                "sources": [{"path": str(source),
                             "provider": FIXTURE_PROVIDER,
                             "reference": FIXTURE_REFERENCE}]}
    for where, payload in ((source, NOT_A_CREDENTIAL.encode()),
                           (registry, (json.dumps(document, indent=1,
                                                  sort_keys=True)
                                       + "\n").encode())):
        handle = os.open(where, os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                         | os.O_NOFOLLOW, 0o600)
        try:
            os.write(handle, payload)
        finally:
            os.close(handle)
        os.chmod(where, 0o600)


def select_job(job_id, work_number=None):
    """Compose a FRESH Job -- its participants AND ITS OWN WORK -- by id.

    WHY THIS EXISTS: claim208777 measured the declared-base defect below on
    the installed instance AFTER `w202663-deterministic-verification-2` was
    already durable there with a line declared against the wrong revision.
    The product refused it honestly (target-drift), the Job and its refusal
    are preserved evidence, and the correction is a NEW Job under fresh
    identities -- the same cadence review208349 required when the first Job's
    task document was wrong. One participant per worker across the WHOLE pool
    is the measured rule, so the three actors carry the job's own numeric
    suffix.

    AND THE WORK IS SELECTED WITH THE JOB, review209459's correction: this
    used to leave WORK on the instance's first Work, and a completed Work
    has been moved by its own lifecycle to the `integration` route -- so the
    reused Work met the new implementation claim there and the claim
    correctly refused ("route 'integration' does not resolve to ..."). A
    fresh INDEPENDENT Job carries a fresh authority-qualified Work id;
    `bootstrap._compose` creates a missing Work on the implementation route
    and leaves existing Works alone, so old identities are preserved
    untouched. The Work number defaults to the job's own numeric suffix and
    can be named explicitly.
    """
    global JOB, ACTORS, WORK

    suffix = job_id.rsplit("-", 1)[-1]
    if not suffix.isdigit():
        raise Unmeasured(f"--job {job_id!r} does not end in -<number>; the "
                         f"numeric suffix names the three fresh participants")
    JOB = job_id
    ACTORS = {"implementation": f"baton.fixture-coder-{suffix}",
              "review": f"baton.fixture-reviewer-{suffix}",
              "integration": f"baton.fixture-integrator-{suffix}"}
    number = suffix if work_number is None else str(work_number)
    if not number.isdigit() or int(number) < 1:
        raise Unmeasured(f"--work {number!r} is not a positive Work number")
    WORK = UUID[:8] + "-W" + number
    return {"job": JOB, "actors": dict(ACTORS), "work": WORK}


def select_instance(destination):
    """Point this composer at another installed instance, by path.

    REVIEW208507 [R2]: the verification commands must not require editing this
    file's historical constants. Those constants record the claim208217 run and
    stay exactly as they were; `--instance` overrides them for a new run
    instead, reading the destination's OWN persisted identity rather than
    taking an Authority uuid on the command line -- an instance generates its
    identity once at install and is the only thing that knows it.
    """
    global DEST, UUID, WORK, CREDENTIAL_SOURCES

    place = Path(destination)
    identity = place / "authority-identity.json"
    if not identity.is_file():
        raise Unmeasured(f"{identity} is not here; --instance names an "
                         f"installed destination")
    held = json.loads(identity.read_text())
    DEST = place
    UUID = held["authority_uuid"]
    # THE WORK ID CARRIES ITS AUTHORITY'S PREFIX, which `check_work_ref`
    # enforces; deriving it here is the same rule, not a second opinion.
    WORK = UUID[:8] + "-W1"
    CREDENTIAL_SOURCES = str(DEST / "credentials/registry.json")
    return {"instance": str(DEST), "authority_uuid": UUID, "work": WORK}


def main(argv=None, *, validators=None, write=True, run=None, opener=None):
    import argparse

    parser = argparse.ArgumentParser(prog="compose-verification-208217")
    parser.add_argument("--instance", default=None,
                        help="an installed destination to compose for; "
                             "omitted keeps this file's recorded constants")
    parser.add_argument("--job", default=None,
                        help="a fresh Job id ending in -<number>; its three "
                             "participants AND its Work number take the same "
                             "suffix (review209459: an independent Job "
                             "carries its own Work). Omitted keeps this "
                             "file's recorded Job")
    parser.add_argument("--work", default=None,
                        help="an explicit Work number for --job, overriding "
                             "the suffix-derived one")
    parser.add_argument("--emitting", action="store_true",
                        help="serve the implementation role from the "
                             "emitting producer image (claim208916), so the "
                             "lifecycle leaves nonempty retained worker "
                             "streams")
    parser.add_argument("--base", default=None,
                        help="compose against this explicit accepted "
                             "reference (opaque; owner 2026-09-20T14:57:48Z) "
                             "instead of reading the dedicated target")
    parser.add_argument("--pr", action="store_true",
                        help="compose the owner-selected PR shape "
                             "(OWNER-HANDOFF-PR-JOBS): producer and reviewer "
                             "only, no integration worker or stage; the "
                             "reviewed candidate is the deliverable")
    taken = parser.parse_args([] if argv is None else list(argv))
    if taken.pr:
        print(json.dumps(select_pr()))
    if taken.base is not None:
        print(json.dumps(select_base(taken.base)))
    if taken.instance is not None:
        print(json.dumps(select_instance(taken.instance)))
    if taken.job is not None:
        print(json.dumps(select_job(taken.job, work_number=taken.work)))
    elif taken.work is not None:
        raise Unmeasured("--work names a Work for --job and means nothing "
                         "without one")
    if taken.emitting:
        print(json.dumps(select_emitting()))
    state = Run(validators or production_validators())
    try:
        facts = measured(run=run, opener=opener)
    except Unmeasured as failure:
        print(json.dumps({"complete": False, "unmeasured": str(failure)},
                         indent=1))
        return 2
    if write:
        stage_inputs(facts)
    facts, documents = compose(state, facts=facts)
    if write and documents:
        (HERE / "pool-task.json").write_bytes(facts["task_payload"])
        (HERE / "pool-integration-instructions.txt").write_text(
            facts["integration_instructions"])
        for name, document in documents.items():
            (HERE / f"pool-{name.replace('_', '-')}.json").write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n")
    found = {
        "schema": "baton.w202663.pool-composition/1",
        "claim": 208217,
        "complete": state.complete,
        "composes_only": "writes documents; bootstraps nothing, starts "
                         "nothing, submits nothing, runs no provider",
        "validator_calls": state.steps,
        "required": list(state.required),
        "refused": state.refused,
        "instance": str(DEST),
        "authority_uuid": UUID,
        "declared_base": facts["declared_base"],
        "actors": dict(ACTORS),
        "images": dict(IMAGES),
        "heterogeneous": len(set(IMAGES.values())) > 1,
        "job_input_identity": facts.get("job_input_identity"),
        "runtime_manifest_digests": {
            role: one["manifest_digest"]
            for role, one in facts.get("manifests", {}).items()},
        "principals": facts["principals"],
        "policy_generation_predicted": facts["policy_generation"],
        "image_in_engine": facts["image_in_engine"],
        "adapter": facts["adapter"],
        "record_binding": facts["record_binding"],
        "no_live_model": "composing this reaches no provider and no model. The "
                         "provider image contains a real provider, so a Job "
                         "that reaches it makes a model turn -- which owner "
                         "206702 excludes from this Work. This package "
                         "configures and does not run.",
        "no_credential_read": "the credential registry and reference are "
                              "LOCATORS written into the deployment. Nothing "
                              "here opened, copied, hashed or staged a bearer.",
    }
    if write:
        (HERE / "POOL-COMPOSITION-207219.json").write_text(
            json.dumps(found, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"complete": found["complete"],
                      "refused": state.refused,
                      "job_input_identity": found["job_input_identity"],
                      "runtime_manifest_digests":
                          found["runtime_manifest_digests"]}, indent=1))
    if not found["complete"]:
        print("INCOMPLETE: a required validator did not accept; this "
              "composition is NOT validated readiness", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
