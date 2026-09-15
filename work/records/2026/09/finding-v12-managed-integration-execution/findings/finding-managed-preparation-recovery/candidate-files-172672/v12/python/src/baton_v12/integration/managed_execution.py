"""W161230 slice1, condition 4: what a managed integration phase IS asked to
do, what it may report, and what that report is allowed to mean.

THIS LEAF DECIDES THREE DOCUMENTS AND PERFORMS NOTHING. It starts no runtime,
writes no target, reads no store and settles nothing: every function here
composes or adopts one closed document, and the owners that act do so with
what this returned. `runtime.py` is the shape this follows -- the generic
contract here, the acting outside it.

  the TASK      what ONE phase of a managed integration was asked to do. It
                binds the actual execution identity, the Job's own admitted
                limits, the immutable content and harness it runs, and -- for
                an apply -- the real preparation it follows. It carries no host
                path, no argv and no location: a task that named where it ran
                would be this boundary deciding somebody else's deployment.
  the REPORT    what the phase's own execution produced, as THREE answers that
                are never read as each other:

                  MEASURED        a status this manager actually measured, an
                                  integer, from a command that ran to an end;
                  COLLECTED WITHOUT STATUS
                                  a report was collected and it carries no
                                  status -- the run was cut, the harness
                                  failed to report, the container vanished.
                                  It is TAGGED with which, and it is never an
                                  exit code;
                  NOT COLLECTED   no report exists at all. Absence, and its own
                                  answer.

                Collapsing any two of these is how "we did not look" becomes
                "it passed". A missing status NEVER becomes 0, and no host path
                or exit code is invented to fill a member out.
  the RESULT    the portable account a managed phase leaves behind: its
                identity, its report, and the content it collected. It is a
                CLAIM, exactly as `runtime.observed_result` is -- nothing here
                settles a target, a receipt or a Work.

THE COMPLETED PREFIX AND THE NOT-RUN SUFFIX ARE BOTH KEPT. A sequence that
stopped partway is not a shorter sequence that passed: the commands that ran
are retained in order with what each measured, the ones that never ran are
named, and the two together must be exactly the sequence that was declared. A
report that dropped its tail would say a phase did less work and succeeded.
"""

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value
from ..job_manager import execution_limits
from ..worker_manager import boundaries

__all__ = ["TASK_SCHEMA", "TASK_MEMBERS", "TASK_PHASES", "PARENT_MEMBERS",
           "REPORT_SCHEMA", "REPORT_MEMBERS", "REPORT_KINDS", "COMMAND_MEMBERS",
           "RESULT_SCHEMA", "RESULT_MEMBERS", "COLLECTED_MEMBERS",
           "LIMITS_MEMBERS", "BOUNDARY_MEMBERS",
           "REQUEST_SCHEMA", "REQUEST_MEMBERS", "SOURCE_MEMBERS",
           "AUTHORITY_MEMBERS", "managed_task", "adopt_managed_task",
           "collected_report", "adopt_collected_report", "managed_result",
           "adopt_managed_result", "preparation_request",
           "adopt_preparation_request", "request_digest"]

TASK_SCHEMA = "baton.v12.managed-integration-task/1"

TASK_PHASES = ("prepare", "apply")

# EVERY OPERAND A MANAGED PHASE IS ASKED WITH. The execution identity is here
# because a phase that could not name the attempt and assignment it runs under
# could not be refused when that assignment ends; the digests are here because
# WHAT it runs is part of what it was asked to do; `execution_limits` is here
# because the Job's own admitted configuration travels with the work rather
# than being re-decided by whoever launches it; and `parent` is here because an
# apply exists to import what a preparation produced.
TASK_MEMBERS = ("schema", "phase", "orchestration_id", "canonical_target_id",
                "execution_attempt_id", "assignment", "task_digest",
                "input_digest", "harness_digest", "execution_limits", "parent",
                "commands")

# THE REAL PREPARATION AN APPLY FOLLOWS -- its execution, and the content it
# actually collected. Both, because an attempt id alone would let an apply
# follow a preparation that collected something else, and a digest alone would
# let it follow no execution at all.
PARENT_MEMBERS = ("execution_attempt_id", "collected_digest")

# W161230 slice2: WHAT A PREPARATION IS ASKED TO PRODUCE, as an immutable
# document written BEFORE anything exists to name it by.
#
# WHY IT IS A SEPARATE ARTIFACT RATHER THAN A WIDER TASK. The accepted task
# describes ONE EXECUTION -- its attempt, its assignment, its limits -- and
# none of that exists yet when a preparation is requested: there is no claim,
# no offer, no runtime input manifest. A request is the thing that comes
# first, and relaxing the task to accept a few extra members before those
# facts exist would make one document mean two things at two times. The slice
# text says the same: use a separately named semantic artifact when richer
# fields are needed.
#
# AND IT CONTAINS NO FUTURE. No claim generation, no attempt id, no manifest
# digest of itself: everything here is either already true or is the immutable
# material the preparation is about.
REQUEST_SCHEMA = "baton.v12.managed-preparation-request/1"

# THE SUBMISSION'S OWN OBJECTS, bound by identity rather than by location. A
# base and a candidate are what the preparation merges; the target snapshot is
# what it merges INTO, and it is pinned here so that a target moving later
# does not retarget a run that already started.
SOURCE_MEMBERS = ("base", "candidate", "target_revision")

# WHAT THE ACCEPTED EVIDENCE AUTHORIZES, carried so the worker runs the paths
# and tests somebody actually accepted rather than whatever it finds.
AUTHORITY_MEMBERS = ("path_set_digest", "test_scope_digest")

REQUEST_MEMBERS = ("schema", "orchestration_id", "canonical_target_id",
                   "job_id", "line_id", "source_proposal_id", "source",
                   "authority", "harness_digest", "profile_digest",
                   "input_digest", "execution_limits", "commands")

REPORT_SCHEMA = "baton.v12.managed-integration-report/1"

# THE THREE ANSWERS, and they are a vocabulary rather than a status with
# special values. See the module docstring: a build that spelled "no status" as
# a status would have to pick a number, and every number it could pick already
# means something.
REPORT_KINDS = ("measured", "collected-without-status", "not-collected")

REPORT_MEMBERS = ("schema", "kind", "phase", "execution_attempt_id", "status",
                  "tag", "completed", "not_run")

# ONE COMMAND THAT RAN, and what it measured. `status` is the integer this
# manager observed; there is no member for what it "should" have been.
COMMAND_MEMBERS = ("name", "status")

RESULT_SCHEMA = "baton.v12.managed-integration-result/1"

COLLECTED_MEMBERS = ("result_id", "manifest_digest", "disposition")

# THE JOB LIMITS DOCUMENT, AS ITS OWN OWNER PRODUCES IT. Review
# 2026-09-13T18:21:26Z [P1]: this leaf required `effective` and `generation`,
# which is a shape I invented -- so the GENUINE answer from
# `execution_limits.resolved` was refused, while `{"effective": {},
# "generation": 999}` was accepted. A handwritten fixture with two numbers
# proves nothing about preserving a Job's configuration.
#
# These names are `resolved`'s, read from it rather than restated, and every
# value below is checked with that owner's own vocabulary -- its units, its
# scope, its closed origin pair, its supported generations and its shared
# seconds range. There is no second limits authority here and no third meaning
# for numbers that already have two.
LIMITS_MEMBERS = ("units", "scope", "compatibility_generation", "requested",
                  "boundaries")
BOUNDARY_MEMBERS = ("seconds", "origin", "setting", "default_seconds")
# NO LOCAL ORIGIN OR SECONDS RULE LIVES HERE ANY MORE. Both were mine, both
# were weaker than the owner's, and a value that satisfied them could still
# describe a resolution this build would never produce -- which is exactly what
# review 2026-09-13T18:34:36Z measured. `_resolved_limits` compares against the
# owner's rebuild instead.

RESULT_MEMBERS = ("schema", "orchestration_id", "phase",
                  "execution_attempt_id", "assignment", "canonical_target_id",
                  "report", "collected")


def request_digest(request):
    """This request's own stable name, over its canonical bytes.

    NOT A MEMBER OF ITSELF. A document carrying the digest of its own final
    bytes cannot be built without circularity, and the slice text forbids it
    in as many words: `task_digest` names the stable request material, and
    this is that material's digest.
    """
    return digest(canonical_text(
        boundaries.document(request, "a preparation request",
                            required=REQUEST_MEMBERS)))


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _measured(value, what):
    """An integer this manager OBSERVED, and `bool` is not one.

    `True` is an `int` in this language and would pass an `isinstance` check,
    so a report carrying `True` where a status belongs would be read as exit
    code 1 -- a failure invented out of a flag. The type is established
    exactly.
    """
    if type(value) is not int:
        _refuse(f"{what} is the integer status this manager measured; this is "
                f"{name_value(value)}")
    return value


def _assignment(value, what):
    held = boundaries.document(value, what,
                               required=("work_ref", "participant",
                                         "generation"))
    boundaries.document(held["work_ref"], f"{what}'s Work",
                        required=("authority_uuid", "work_id"))
    boundaries.text(held["work_ref"]["authority_uuid"], f"{what}'s authority")
    boundaries.identity(held["work_ref"]["work_id"], f"{what}'s Work")
    boundaries.text(held["participant"], f"{what}'s participant")
    boundaries.generation(held["generation"], f"{what}'s generation")
    return held


def _sequence(value, what):
    """The declared command names, in order, each named once."""
    if type(value) is not tuple and type(value) is not list:
        _refuse(f"{what} is the ordered list of commands this phase runs; "
                f"this is {name_value(value)}")
    taken = [boundaries.text(one, f"a command name in {what}") for one in value]
    if not taken:
        _refuse(f"{what} is empty; a phase that runs nothing has nothing to "
                f"report and is not a task")
    if len(set(taken)) != len(taken):
        _refuse(f"{what} names one command more than once; a report is keyed "
                f"by name and two entries would be one answer")
    return taken


def _resolved_limits(value):
    """The Job's OWN resolved configuration, REBUILT THROUGH ITS OWNER.

    REVIEW 2026-09-13T18:34:36Z [P1]: the first form checked each member's
    shape -- units, scope, a known generation, seconds inside the shared range,
    a setting that matches, an origin that agrees with the request -- and never
    asked the owner what the numbers ACTUALLY ARE. So `provider_turn` could
    carry 7200 seconds, or a `default_seconds` of 7200, or both, under a
    generation whose frozen table pins 3600, and every one of those checks
    passed. A document can be internally consistent and still describe a
    resolution this build would never produce.

    SO NOTHING IS RE-DERIVED HERE. The requested settings and the generation
    are the only two INPUTS a Job's resolution has; both are owned by the Job
    Manager's own rules, the whole document is recomputed from them with
    `execution_limits.resolved`, and what arrived must EQUAL what the owner
    produces. This is `adopt_collected_report`'s shape one layer down and it is
    here for the same reason: a second spelling of somebody else's rule is how
    two readers come to disagree, and a comparison against a REBUILD cannot be
    walked past by a value that merely looks plausible.

    THE LEGACY GENERATION IS ORDINARY. A Job admitted before per-Job limits
    existed resolves under generation 0, and its preserved defaults are what it
    ran under; refusing it would make a managed phase impossible for every Job
    older than the feature.
    """
    held = boundaries.document(value, "a task's execution limits",
                               required=LIMITS_MEMBERS)
    # THE TWO INPUTS, EACH THROUGH THE OWNER'S OWN RULE.
    # `owned_execution_limits` refuses an unknown setting and any seconds
    # outside the shared range; `owned_generation` refuses a generation this
    # build cannot reproduce, and a resolution it cannot reproduce is one it
    # would have to guess at.
    requested = execution_limits.owned_execution_limits(held["requested"])
    generation = execution_limits.owned_generation(
        held["compatibility_generation"])
    rebuilt = execution_limits.resolved(requested, generation)
    # THE TYPES BEFORE THE EQUALITY. Review 2026-09-13T18:51:48Z [P2]: Python
    # document equality treats `True` as `1`, so a Job that legitimately
    # requested one second had a resolved boundary of `True` compared equal to
    # it and handed back AS `True`. A rebuild comparison is exact about values
    # and says nothing about their types, and a flag reaching a seconds field
    # is precisely the confusion the owner's own `_seconds` rule exists to
    # refuse. The owner decides the RANGE; this insists the compared value is
    # the kind of thing that range is about.
    for name, boundary in sorted(
            (held["boundaries"] if type(held["boundaries"]) is dict
             else {}).items()):
        if type(boundary) is not dict:
            continue
        for member in ("seconds", "default_seconds"):
            value = boundary.get(member)
            if type(value) is bool or (value is not None
                                       and type(value) is not int):
                _refuse(f"the {name} boundary's {member} is "
                        f"{name_value(value)}; a resolved ceiling is whole "
                        f"seconds, and a value that merely compares equal to "
                        f"one is not one")
    if held != rebuilt:
        parts = []
        for name in LIMITS_MEMBERS:
            if held[name] == rebuilt[name]:
                continue
            if name != "boundaries":
                parts.append(f"{name} {name_value(held[name])} where this "
                             f"Job's own resolution says "
                             f"{name_value(rebuilt[name])}")
                continue
            # PER BOUNDARY, because "a dict and a dict" would leave a reader
            # diffing two nested documents by eye to find the tampered number.
            for boundary in sorted(rebuilt["boundaries"]):
                mine = held["boundaries"].get(boundary)
                theirs = rebuilt["boundaries"][boundary]
                if mine == theirs:
                    continue
                # DOWN TO THE MEMBER. Measured, step 64: comparing whole
                # boundary documents rendered both sides as "a dict", so a
                # tampered `seconds` produced a refusal that named neither the
                # number that arrived nor the one the owner resolved -- a
                # diagnostic that cannot be acted on.
                if type(mine) is not dict:
                    parts.append(f"the {boundary} boundary "
                                 f"{name_value(mine)} where this Job's own "
                                 f"resolution has one")
                    continue
                for member in BOUNDARY_MEMBERS:
                    if mine.get(member) != theirs[member]:
                        parts.append(
                            f"the {boundary} boundary's {member} "
                            f"{name_value(mine.get(member))} where this Job's "
                            f"own resolution says {name_value(theirs[member])}")
                for member in sorted(set(mine) - set(BOUNDARY_MEMBERS)):
                    parts.append(f"the {boundary} boundary's unknown "
                                 f"{name_value(member)}")
        _refuse(f"this task carries {'; '.join(parts)}; a Job's limits are "
                f"what its own owner resolves from the settings it requested "
                f"and the generation it was admitted under, not a document "
                f"that resembles one")
    return held


def preparation_request(*, orchestration_id, canonical_target_id, job_id,
                        line_id, source_proposal_id, source, authority,
                        harness_digest, profile_digest, input_digest,
                        execution_limits, commands):
    """What ONE preparation is asked to produce, before anything runs.

    COMPOSED FROM VALUES AND REBUILT OVER `REQUEST_MEMBERS`, which is this
    package's rule: a caller supplies values, never a document shape.

    EVERY OBJECT IS AN IDENTITY. `source` names the base, the candidate and
    the pinned target snapshot; `authority` names the accepted path set and
    test scope by digest. Nothing here is a path, a workspace or a machine --
    a request travels to a node that has none of those.
    """
    held = boundaries.document(source, "a request's source",
                               required=SOURCE_MEMBERS)
    for name in SOURCE_MEMBERS:
        _object_name(held[name], f"the request's {name}")
    accepted = boundaries.document(authority, "a request's accepted evidence",
                                   required=AUTHORITY_MEMBERS)
    for name in AUTHORITY_MEMBERS:
        boundaries.text(accepted[name], f"the accepted {name}")
    return {
        "schema": REQUEST_SCHEMA,
        "orchestration_id": boundaries.identity(orchestration_id,
                                                "an orchestration id"),
        "canonical_target_id": boundaries.identity(canonical_target_id,
                                                   "a canonical target id"),
        "job_id": boundaries.identity(job_id, "a Job id"),
        "line_id": boundaries.identity(line_id, "a line id"),
        "source_proposal_id": boundaries.identity(source_proposal_id,
                                                  "a source proposal id"),
        "source": held, "authority": accepted,
        "harness_digest": boundaries.text(harness_digest, "a harness digest"),
        "profile_digest": boundaries.text(profile_digest,
                                          "a preparation profile digest"),
        # THE PREPARATION'S OWN INPUT, kept separate from the original Job's.
        # They are different documents about different executions, and the
        # slice text keeps them apart for that reason.
        "input_digest": boundaries.text(input_digest,
                                        "the preparation's input digest"),
        "execution_limits": _resolved_limits(execution_limits),
        "commands": _sequence(commands, "a request's commands"),
    }


def adopt_preparation_request(value):
    """One request arriving as a DOCUMENT, rebuilt through its own composer.

    The rule every other artifact here is under: what makes it a request is
    that the composer's own rules produce it, and the rebuild must equal what
    arrived.
    """
    held = boundaries.document(value, "a preparation request",
                               required=REQUEST_MEMBERS)
    if held["schema"] != REQUEST_SCHEMA:
        _refuse(f"a preparation request is {name_value(REQUEST_SCHEMA)}; this "
                f"is {name_value(held['schema'])}")
    rebuilt = preparation_request(
        orchestration_id=held["orchestration_id"],
        canonical_target_id=held["canonical_target_id"],
        job_id=held["job_id"], line_id=held["line_id"],
        source_proposal_id=held["source_proposal_id"], source=held["source"],
        authority=held["authority"], harness_digest=held["harness_digest"],
        profile_digest=held["profile_digest"],
        input_digest=held["input_digest"],
        execution_limits=held["execution_limits"], commands=held["commands"])
    if held != rebuilt:
        _refuse(f"this preparation request does not survive being rebuilt "
                f"from its own fields; what arrived and what its values "
                f"produce are different documents")
    return rebuilt


def _object_name(value, what):
    """One full lowercase object name, so no revision EXPRESSION travels.

    `HEAD~1` and a branch name both resolve to something different tomorrow;
    a preparation is about an immutable snapshot, so what it carries is the
    object rather than a way of finding one.
    """
    boundaries.text(value, what)
    if len(value) != 40 or any(one not in "0123456789abcdef" for one in value):
        _refuse(f"{what} is one full lowercase object name; this is "
                f"{name_value(value)}")
    return value


def managed_task(*, phase, orchestration_id, canonical_target_id,
                 execution_attempt_id, assignment, task_digest, input_digest,
                 harness_digest, execution_limits, commands, parent=None):
    """What ONE phase was asked to do, composed from values.

    REBUILT OVER `TASK_MEMBERS` RATHER THAN COPIED FROM A MAPPING, which is
    this package's rule: a caller supplies values, never a document shape, so
    how a caller happened to build its dict cannot reach a document this
    boundary then treats as its own.

    THE LIMITS ARE THE JOB'S OWN, RESOLVED BY THE JOB'S OWN OWNER. What is
    checked here is that the document IS one -- its effective boundaries and
    the generation they were resolved under -- and never what the numbers ought
    to be: this leaf does not own execution limits and would be a second
    opinion on them if it tried.
    """
    if phase not in TASK_PHASES:
        _refuse(f"a managed phase is one of {', '.join(TASK_PHASES)}; this is "
                f"{name_value(phase)}")
    limits = _resolved_limits(execution_limits)
    # AN APPLY FOLLOWS A REAL PREPARATION, AND A PREPARATION FOLLOWS NOTHING.
    # The content an apply imports does not exist when the preparation is
    # asked, so a preparation naming a parent would be naming content nobody
    # has produced.
    if phase == "apply":
        followed = boundaries.document(parent, "an apply's parent",
                                       required=PARENT_MEMBERS)
        boundaries.identity(followed["execution_attempt_id"],
                            "an apply's parent execution")
        boundaries.text(followed["collected_digest"],
                        "an apply's parent content digest")
        if followed["execution_attempt_id"] == execution_attempt_id:
            _refuse(f"an apply names itself as its own parent "
                    f"{name_value(execution_attempt_id)}; a phase does not "
                    f"import what it has not produced yet")
    elif parent is not None:
        _refuse(f"a preparation names parent {name_value(parent)}; a "
                f"preparation imports nothing, and content it could import "
                f"does not exist when it is asked")
    else:
        followed = None
    return {
        "schema": TASK_SCHEMA,
        "phase": phase,
        "orchestration_id": boundaries.identity(orchestration_id,
                                                "an orchestration id"),
        "canonical_target_id": boundaries.identity(canonical_target_id,
                                                   "a canonical target id"),
        "execution_attempt_id": boundaries.identity(execution_attempt_id,
                                                     "an execution attempt id"),
        "assignment": _assignment(assignment, "a task's assignment"),
        "task_digest": boundaries.text(task_digest, "a task digest"),
        "input_digest": boundaries.text(input_digest, "a task's input digest"),
        # THE HARNESS IS IMMUTABLE AND IS NAMED BY DIGEST, for the reason a
        # profile is: "the harness we agreed on" is a byte identity, and a
        # later edit to a file would otherwise silently re-authorize itself.
        "harness_digest": boundaries.text(harness_digest, "a harness digest"),
        "execution_limits": limits,
        "parent": followed,
        "commands": _sequence(commands, "a task's commands"),
    }


def collected_report(task, *, kind, completed=(), not_run=(), status=None,
                     tag=None):
    """What the phase's execution produced, as ONE of three answers.

    THE PREFIX AND THE SUFFIX ARE BOTH REQUIRED TO ADD UP. `completed` is the
    commands that ran, in the order they ran, each with the status this manager
    measured; `not_run` is the suffix that never started. Together they must be
    exactly the task's declared sequence, in its order -- a report that dropped
    its tail would describe a shorter phase that succeeded, and one that
    reordered its head would describe a different phase entirely.

    NOTHING IS FILLED IN. A command that ran carries a measured integer; one
    that did not is in `not_run` and carries nothing at all. There is no member
    for an exit code nobody observed.
    """
    held = boundaries.document(task, "the task this reports on",
                               required=TASK_MEMBERS)
    if held["schema"] != TASK_SCHEMA:
        _refuse(f"a managed task is {name_value(TASK_SCHEMA)}; this is "
                f"{name_value(held['schema'])}")
    if kind not in REPORT_KINDS:
        _refuse(f"a collected report is one of {', '.join(REPORT_KINDS)}; "
                f"this is {name_value(kind)}")
    ran = [boundaries.document(one, "a completed command",
                               required=COMMAND_MEMBERS)
           for one in completed]
    for one in ran:
        boundaries.text(one["name"], "a completed command's name")
        _measured(one["status"], "a completed command's status")
    remaining = [boundaries.text(one, "a command that did not run")
                 for one in not_run]
    if [one["name"] for one in ran] + remaining != held["commands"]:
        _refuse(f"this report accounts "
                f"{name_value([one['name'] for one in ran] + remaining)} and "
                f"the task declares {name_value(held['commands'])}; the "
                f"completed prefix and the not-run suffix are the sequence "
                f"that was asked for, in its order")
    # WHICH ANSWER THIS IS, AND WHAT EACH ONE MAY CARRY.
    if kind == "measured":
        _measured(status, "a measured report's status")
        if tag is not None:
            _refuse(f"a measured report is tagged {name_value(tag)}; a tag "
                    f"says why there is NO status, and this one has one")
        if not ran:
            _refuse("a measured report ran no command; a status this manager "
                    "measured comes from a command that ran")
    elif kind == "collected-without-status":
        if status is not None:
            _refuse(f"a report collected without a status carries status "
                    f"{name_value(status)}; if a status was measured this is "
                    f"a measured report")
        boundaries.text(tag, "the tag saying why no status was measured")
    else:
        if status is not None or tag is not None:
            _refuse(f"nothing was collected, and this carries status "
                    f"{name_value(status)} and tag {name_value(tag)}; absence "
                    f"is its own answer and describes no run")
        if ran:
            _refuse(f"nothing was collected, and this reports "
                    f"{len(ran)} completed commands; a report that does not "
                    f"exist cannot say what ran")
    return {"schema": REPORT_SCHEMA, "kind": kind, "phase": held["phase"],
            "execution_attempt_id": held["execution_attempt_id"],
            "status": status, "tag": tag, "completed": ran,
            "not_run": remaining}


def adopt_managed_task(value):
    """One task arriving as a DOCUMENT, rebuilt through its own composer.

    The same rule the report and the result are under: a stored task is text
    this process did not necessarily write, and what makes it a task is that
    the composer's own rules produce it. So its members become the arguments a
    caller would have supplied, `managed_task` builds it, and the rebuild must
    EQUAL what arrived -- which is what refuses a document whose limits, parent
    or command sequence were edited after it was written.
    """
    held = boundaries.document(value, "a managed integration task",
                               required=TASK_MEMBERS)
    if held["schema"] != TASK_SCHEMA:
        _refuse(f"a managed task is {name_value(TASK_SCHEMA)}; this is "
                f"{name_value(held['schema'])}")
    rebuilt = managed_task(
        phase=held["phase"], orchestration_id=held["orchestration_id"],
        canonical_target_id=held["canonical_target_id"],
        execution_attempt_id=held["execution_attempt_id"],
        assignment=held["assignment"], task_digest=held["task_digest"],
        input_digest=held["input_digest"],
        harness_digest=held["harness_digest"],
        execution_limits=held["execution_limits"],
        commands=held["commands"], parent=held["parent"])
    if held != rebuilt:
        _refuse(f"this task does not survive being rebuilt from its own "
                f"fields; what arrived and what its values produce are "
                f"different documents")
    return rebuilt


def adopt_collected_report(task, value):
    """One report arriving as a DOCUMENT, held to the same rules as one built.

    REVIEW 2026-09-13T18:21:26Z [P1]: `managed_result` checked a received
    report's outer member set, its schema and its phase/attempt and then
    carried it through -- so the kind vocabulary, the integer status, the
    legal kind/status/tag combinations and the prefix/suffix accounting
    applied to ONE CONSTRUCTOR and not to the boundary that reads stored and
    collected results. The reviewer's probe adopted an unknown kind, a boolean
    status, an undeclared command with a dropped suffix, and a `not-collected`
    report carrying status 0 and completed commands. Every one was adopted
    unchanged.

    THE RULES ARE NOT RE-STATED HERE. This takes the document apart into the
    values a composer would have been given and hands them to
    `collected_report`, which is the one place those rules live; a second
    spelling of them is how two crossings come to disagree. What comes back is
    REBUILT, and the rebuild must equal what arrived -- so a document that
    passed each rule individually while carrying something else is refused too.
    """
    answered = boundaries.document(value, "this phase's report",
                                   required=REPORT_MEMBERS)
    if answered["schema"] != REPORT_SCHEMA:
        _refuse(f"a collected report is {name_value(REPORT_SCHEMA)}; this is "
                f"{name_value(answered['schema'])}")
    rebuilt = collected_report(task, kind=answered["kind"],
                               completed=answered["completed"],
                               not_run=answered["not_run"],
                               status=answered["status"], tag=answered["tag"])
    # AND THE PHASE AND EXECUTION IT CLAIMS, against the task it answers.
    # `collected_report` derives both FROM the task, so this compares what
    # arrived with what the task actually says rather than with itself.
    for member in ("phase", "execution_attempt_id"):
        if answered[member] != rebuilt[member]:
            raise ContractRefusal(
                "policy", "denied",
                f"this report accounts {member} "
                f"{name_value(answered[member])} and the task names "
                f"{name_value(rebuilt[member])}; a phase reports the work it "
                f"was asked to do")
    if answered != rebuilt:
        _refuse(f"this report does not survive being rebuilt from its own "
                f"fields; what arrived and what its values produce are "
                f"different documents")
    return rebuilt


def managed_result(task, report, *, collected=None):
    """The portable account one managed phase leaves behind.

    A CLAIM, NOT A SETTLEMENT. It says what this phase was asked to do, what
    its execution reported and what it collected; which target verb any of that
    earns is decided by the owners that hold the target, against the live grant
    at that moment.

    THE REPORT AND THE COLLECTED CONTENT ARE SEPARATE MEMBERS BECAUSE THEY ARE
    SEPARATE FACTS. A phase can measure a status and collect nothing, and a
    phase can collect a report that carries no status at all; a document that
    folded one into the other would make those two indistinguishable.
    """
    held = boundaries.document(task, "the task this accounts for",
                               required=TASK_MEMBERS)
    if held["schema"] != TASK_SCHEMA:
        _refuse(f"a managed task is {name_value(TASK_SCHEMA)}; this is "
                f"{name_value(held['schema'])}")
    # THE REPORT GOES THROUGH ITS OWN OWNER, whichever direction it came from.
    # A result composed here and a result read back from storage reach this
    # line by different routes and leave it having passed the same rules.
    answered = adopt_collected_report(held, report)
    if collected is not None:
        custody = boundaries.document(collected, "the collected content",
                                      required=COLLECTED_MEMBERS)
        boundaries.identity(custody["result_id"], "the collected result id")
        boundaries.text(custody["manifest_digest"],
                        "the collected manifest digest")
        boundaries.text(custody["disposition"], "the collected disposition")
        # AND CONTENT WITHOUT A REPORT IS A CONTRADICTION. `not-collected`
        # means no report exists; custody for content that no report describes
        # would be exactly the "we did not look, so it passed" reading.
        if answered["kind"] == "not-collected":
            _refuse(f"this result carries collected content "
                    f"{name_value(custody['manifest_digest'])} and reports "
                    f"that nothing was collected")
    else:
        custody = None
    return {"schema": RESULT_SCHEMA,
            "orchestration_id": held["orchestration_id"],
            "phase": held["phase"],
            "execution_attempt_id": held["execution_attempt_id"],
            "assignment": held["assignment"],
            "canonical_target_id": held["canonical_target_id"],
            "report": answered, "collected": custody}


def adopt_managed_result(task, value):
    """One managed result arriving as UNTRUSTED INPUT, held to this task.

    The composer above is for a document this process builds. This is for one
    that CROSSES a boundary -- from a relocated node, a portable store, a
    later incarnation -- and the difference is that nothing about it is known
    until it has been compared with the task it claims to answer.
    """
    held = boundaries.document(task, "the task this answers",
                               required=TASK_MEMBERS)
    answer = boundaries.document(value, "a managed integration result",
                                 required=RESULT_MEMBERS)
    if answer["schema"] != RESULT_SCHEMA:
        _refuse(f"a managed integration result is {name_value(RESULT_SCHEMA)}; "
                f"this is {name_value(answer['schema'])}")
    rebuilt = managed_result(held, answer["report"],
                             collected=answer["collected"])
    for member in ("orchestration_id", "phase", "execution_attempt_id",
                   "canonical_target_id", "assignment"):
        if answer[member] != rebuilt[member]:
            raise ContractRefusal(
                "policy", "denied",
                f"this result accounts {member} "
                f"{name_value(answer[member])} and the task it answers names "
                f"{name_value(rebuilt[member])}; a phase answers the "
                f"integration it was composed for")
    return rebuilt
