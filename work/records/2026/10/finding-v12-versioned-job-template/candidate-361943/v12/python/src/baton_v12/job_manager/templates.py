"""W361910 / DESIGN SCH-1a: the reusable ordinary Job template, and nothing
that reads one out of a file.

WHAT WAS MISSING, measured rather than asserted. `submission.submit` reaches
`documents.read_submission`, which requires a fully normalized
`baton.v12.job-submission/{1,2}` document: per Job an `input_digest`, a
`policy_digest`, a `test_scope` and a `terminal_policy`, and per stage a
`kind`, a `work_id`, a `profile_name`, a `profile_digest` and a `depends_on`
list that resolves inside the submission and carries no cycle. Every one of
those is required, closed and refused when wrong -- and until this module
there was nothing in the package that could PRODUCE one. So ordinary creation
was operator-authored, and `v12/w144813-submission.example.json` is what that
looks like: six `null` members a human fills in by hand, every one of which
`boundaries.text` refuses exactly as written.

AND HAND-AUTHORING GETS A REAL THING WRONG. `test_review_driver`'s
`one_work_submission` says it in its own docstring: the package's default
fixture names TWO Works across one Job's implementation and review stages,
"which the generic parser admits and the line provider can never attach,
because a line is one `(authority_uuid, work_id)` pair and its reviewer is an
assignment of that same Work". A generic document parser cannot refuse that --
two Works is a legitimate shape for some other submission -- so the only place
it can be refused is a template that knows what one development line is. This
module is that place, and both stages of a resolved Job name ONE Work.

WHAT A TEMPLATE IS HERE, AND WHAT IT IS NOT. It is a FROZEN, VERSIONED
definition compiled into this build: the stages an ordinary Job owes, their
roles, the dependency between them, which result each one consumes and
produces, the completion/correction/failure rules, and the single override the
request may state. It is NOT a template language, a workflow editor, a
manifest format or a registry a caller can extend -- `resolve` takes a request
and a deployment configuration and nothing that could introduce a stage. The
owner's ruling is explicit: "Start with implementation followed by independent
review, not a general workflow framework."

THE THREE DOCUMENTS, AND WHO OWNS EACH MEMBER.

  * a REQUEST is the caller's: the template selection, the task, the source,
    the scope, the acceptance criteria and the permitted overrides. It is
    owned member by member, exactly as a submission is.
  * a CONFIGURATION is the DEPLOYMENT's: which template a bare request means,
    and which runtime profile each role's workers were installed with. SCH-1a
    rules that "Deployment supplies workers, credentials and capacity; these
    are not operator-authored per-Job manifests", and a profile digest is the
    deployment's half of that -- `scheduler.reserve` matches a stage's
    `(lane, profile_name, profile_digest)` against the installed pool, so an
    operator who typed one would be configuring the pool from a Job.
  * a RESOLUTION is this build's own answer, and it carries the normalized
    submission inside it. `resolve` runs that submission through
    `documents.owned_submission` BEFORE answering, so a resolution this build
    composed and the real consumer would refuse is a refusal here rather than
    a document somebody submits later.

THE EXACT VERSION IS IN THE ANSWER AND SO IS WHERE IT CAME FROM. "A configured
default may save typing but MUST NOT hide that selection." So the resolution
names the exact template version AND the origin of that selection -- `request`
or `configured-default` -- and the two are separate members because a reader
that cannot tell them apart cannot tell whether anybody chose anything.

A LATER DEFAULT CANNOT REINTERPRET AN ALREADY-RESOLVED JOB, which is the same
rule `execution_limits` learned the hard way. Two mechanisms, and neither of
them is this module remembering anything: the resolution PINS the exact
version it selected, so re-resolving it by explicit selection reproduces these
bytes whatever the configured default has become; and the submission's durable
identity is its own normalized text, which `submission._unclaimed` already
holds one owner to. A changed configuration therefore produces a VISIBLY
different resolution rather than a quietly different reading of an old one.

WHAT THIS SLICE DOES NOT CLAIM. It performs no admission, opens no store,
takes no lock and reaches no CLI: `submission.submit` still owns uniqueness
and atomicity and `fresh_attempt.admit` still owns retry, both untouched. The
manager-owned admission that consumes a resolution, and the thin command that
requests it, are W361912's.
"""

from . import documents, execution_limits, fresh_attempt, review_driver
from ..contracts import ContractRefusal, check_relative_path, digest, own
from ..contracts.errors import name_value
from ..contracts.secrets import check_no_durable_secret
from ..worker_manager import boundaries

__all__ = ["ACCEPTANCE_LIMIT", "CANDIDATE_OUTPUT", "CONFIGURATION_MEMBERS",
           "CONFIGURATION_SCHEMA", "DEFAULT_TEMPLATE", "IMPLEMENTATION_REVIEW",
           "MAX_ACCEPTANCE", "MAX_STATEMENT", "OVERRIDE_MEMBERS",
           "PROFILE_MEMBERS", "REQUEST_MEMBERS", "REQUEST_OPTIONAL",
           "REQUEST_SCHEMA", "RESOLUTION_MEMBERS", "RESOLUTION_SCHEMA",
           "ROLE_MEMBERS", "SELECTION_ORIGINS", "SOURCE_MEMBERS",
           "TASK_MEMBERS", "TASK_OPTIONAL", "TEMPLATES", "check_template",
           "resolution_digest", "resolve", "submission_id_for", "template_of"]

# The two documents a caller hands in and the one this build answers with.
# Each version is IN its name, for the reason `documents` gives for the
# submission's: a control plane that reads an unrecognised document as its own
# turns an old operator into a wrong one.
REQUEST_SCHEMA = "baton.v12.job-template-request/1"
CONFIGURATION_SCHEMA = "baton.v12.job-template-configuration/1"
RESOLUTION_SCHEMA = "baton.v12.job-template-resolution/1"

# THE ONE TEMPLATE THIS BUILD CARRIES, and its exact version. The name says
# which workflow it is and the suffix says which revision of it, so a second
# revision is a second entry in the table below rather than an edit to this
# one -- the same shape `execution_limits.GENERATIONS` uses, and for the same
# reason: an edited entry is the reinterpretation the structure exists to
# prevent.
IMPLEMENTATION_REVIEW = "baton.v12.job-template.implementation-review/1"

# WHICH DECLARED OUTPUT CARRIES THE CANDIDATE, spelled here and held to its
# owners by a case rather than by this sentence. `v12/worker/claude_agent.py`
# declares `IMPLEMENTATION_OUTPUTS = ("proposal",)` and nothing from
# `baton_v12` travels into that image; `tools/authoring_baseline.py` spells it
# `PROPOSAL_OUTPUT` and `tools` is not importable from the package. The review
# half needs no such spelling: `review_driver` owns `FINDINGS_OUTPUT` and
# `LOGS_OUTPUT` in this package, and those are imported rather than copied.
CANDIDATE_OUTPUT = "proposal"

# Where a template selection came from, as a closed vocabulary of two.
SELECTION_ORIGINS = ("request", "configured-default")

# What a role declaration carries. Closed, and asserted against every
# registered template at import, so a table entry that grows a member nobody
# resolves fails the build rather than being half-read.
ROLE_MEMBERS = ("role", "kind", "depends_on", "consumes", "produces")

# And what a template declaration carries. Same rule, one level up.
TEMPLATE_MEMBERS = ("version", "terminal_policy", "permitted_overrides",
                    "roles", "completion", "correction", "failure")

# -- the frozen table --------------------------------------------------------
#
# TUPLES, NOT LISTS, AND THAT IS DELIBERATE. `resolve` copies what it needs
# into fresh built-in lists, so a caller holding a resolution cannot reach
# back through it and append a stage to the table every later Job resolves
# against. `contracts.own` would refuse a tuple anyway, which is what makes
# the copy impossible to forget.
TEMPLATES = {
    IMPLEMENTATION_REVIEW: {
        "version": IMPLEMENTATION_REVIEW,
        # ONE TERMINAL POLICY, taken from the vocabulary that has one member.
        # `documents.TERMINAL_POLICIES` is an enum of one because W71830 ruled
        # that a wedged Job is reported and contained; a template that let a
        # request choose would be offering a decision nobody has made.
        "terminal_policy": documents.TERMINAL_POLICIES[0],
        # THE ONE OVERRIDE AN ORDINARY REQUEST MAY STATE. SCH-1a asks for
        # "default execution/verification limits with permitted overrides",
        # and `execution_limits` is exactly that surface -- already owned,
        # already ranged, already generation-pinned. Nothing else is
        # permitted: the stage set, the dependency, the terminal policy and
        # the output contracts are the template's, and a request that could
        # move them would be the per-Job manifest the owner forbade.
        "permitted_overrides": ("execution_limits",),
        "roles": (
            {"role": "implementation", "kind": "implementation",
             "depends_on": (), "consumes": (),
             "produces": (CANDIDATE_OUTPUT,)},
            # THE DEPENDENCY IS THE TEMPLATE'S, not a request's. SCH-4:
            # "Dependencies name the stage they constrain", and what
            # constrains an independent review is the implementation whose
            # candidate it reads -- so this gate is declared once here and
            # every resolved Job carries it.
            {"role": "review", "kind": "review",
             "depends_on": ("implementation",),
             "consumes": (CANDIDATE_OUTPUT,),
             "produces": (review_driver.FINDINGS_OUTPUT,
                          review_driver.LOGS_OUTPUT)},
        ),
        # THE THREE RULES, each member a word an owning module already
        # decides, so this table reports them rather than deciding them a
        # second time. REV-1 keeps verification, review, acceptance and
        # integration separate acts; what a template owes a reader is which
        # act ends an ordinary Job, which one sends it round again, and what
        # happens when neither can.
        "completion": {
            # `review_driver.VERDICT_OUTCOMES` is ("accepted", "correction",
            # "held"); `accepted` is the one that hands a producer account on.
            "outcome": review_driver.VERDICT_OUTCOMES[0],
            "deciding_role": "review",
            # Read from exactly one output, because "two outputs offering a
            # verdict is a reviewer with two answers".
            "verdict_output": review_driver.FINDINGS_OUTPUT,
            # REV-4: the delivered product is the reviewed proposal, durably
            # available rather than silently merged.
            "delivers": CANDIDATE_OUTPUT,
        },
        "correction": {
            "outcome": review_driver.VERDICT_OUTCOMES[1],
            # `documents.CORRECTION_ENDINGS` is the closed set that is
            # deliberately NOT an offer ending: the offer was accepted, the
            # claim was taken, the worker answered and a reviewer read it.
            "episode_ending": documents.CORRECTION_ENDINGS[0],
            # REV-3: routine repairs iterate directly on the same line.
            # Both roles are attempted again, which is why the ending opens
            # two successors inside one transaction.
            "repeats": ("implementation", "review"),
        },
        "failure": {
            "outcome": review_driver.VERDICT_OUTCOMES[2],
            "terminal_policy": documents.TERMINAL_POLICIES[0],
            # What an operator reads on a stage this control plane owes
            # nothing further for.
            "stage_state": "exceptional",
            # REC-7's supported repeat, named by the operation that owns it
            # rather than described. It is a SEPARATE act on a separate
            # request; naming it here is not performing it.
            "recovery_operation": fresh_attempt.ADMIT_KIND,
        },
    },
}

# WHICH TEMPLATE A BARE REQUEST MEANS WHEN A DEPLOYMENT CONFIGURES NOTHING.
# It is still RESOLVED and still SHOWN: the saving is typing, not visibility.
DEFAULT_TEMPLATE = IMPLEMENTATION_REVIEW

# -- the request -------------------------------------------------------------

REQUEST_MEMBERS = ("schema", "task", "source", "scope", "acceptance")
# `template` absent is the configured default; `overrides` absent is an empty
# selection. Both are OPTIONAL rather than nullable, for the reason
# `documents._job` gives: an absent member and a present null are different
# intents, and only one of them is a document somebody wrote on purpose.
REQUEST_OPTIONAL = ("template", "overrides")

TASK_MEMBERS = ("job_id", "work_id", "statement")
# Derived from the Job id when omitted, exactly as `fresh_attempt.admit`
# derives it, so no operator has to invent a name.
TASK_OPTIONAL = ("submission_id",)

SOURCE_MEMBERS = ("input_digest", "policy_digest")
OVERRIDE_MEMBERS = ("execution_limits",)
PROFILE_MEMBERS = ("profile_name", "profile_digest")

# Bounds on the prose a request carries into a durable record. The statement
# and the criteria are the only free text here, and free text with no bound is
# an unbounded durable write from one call -- the rule `documents.MAX_JOBS`
# states, applied to the members that are words rather than identities.
MAX_STATEMENT = 4096
MAX_ACCEPTANCE = 32
ACCEPTANCE_LIMIT = 1024

CONFIGURATION_MEMBERS = ("schema", "profiles")
# A deployment that names no default means this build's; naming one is how a
# second template revision becomes the ordinary one without an operator
# retyping it per Job.
CONFIGURATION_OPTIONAL = ("default_template",)

RESOLUTION_MEMBERS = ("schema", "template", "task", "source", "scope",
                      "acceptance", "overrides", "stages", "rules",
                      "execution_limits", "submission")


# THE ONE SENTINEL THIS MODULE NEEDS, and why `None` cannot be it. An absent
# `overrides` member and a present `overrides: null` are different intents --
# the same distinction `documents._job` keeps for the submission's own optional
# member -- so "nothing was stated" needs a value no document can carry.
_ABSENT = object()


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def _exactly(value, members, what):
    """One exact declaration with EXACTLY these members, and nothing owned.

    `boundaries._members`' rule, applied to this build's own table: a missing
    member is named and an extra one is refused rather than ignored, because
    an unresolved member in a frozen declaration is a resolution somebody
    believes happens.
    """
    if type(value) is not dict:
        _refuse(f"{what} is one declaration; this is {name_value(value)}")
    missing = [member for member in members if member not in value]
    if missing:
        _refuse(f"{what} needs {', '.join(missing)}")
    extra = sorted(member for member in value if member not in members)
    if extra:
        _refuse(f"{what} also carries {', '.join(extra)}, which this build "
                f"does not resolve; an unresolved member in a frozen "
                f"declaration is a rule somebody believes applies")
    return dict(value)


def _entries(value, what):
    """One declared sequence, as a list, from either spelling.

    The table writes tuples and a case driving a fault writes whichever it
    finds convenient; what matters is that neither a string nor a mapping is
    silently iterated as a sequence of its characters or its keys.
    """
    if type(value) not in (tuple, list):
        _refuse(f"{what} is a declared sequence; this is "
                f"{name_value(value)}")
    return list(value)


def check_template(definition):
    """One table entry, held to the shape every resolution depends on.

    THE RULE IS CHECKED AT IMPORT FOR EVERY REGISTERED TEMPLATE, which is why
    it is a function rather than a paragraph: `documents` asserts its own
    vocabulary relationships the same way, and an entry that cannot be
    resolved should fail where it is written rather than on the first request
    that selects it.

    WHAT "DEPENDENCY/RESULT MISMATCH" MEANS, and it is two faults rather than
    one. A role may gate on a role this template does not carry -- a gate
    nothing in the Job can ever open, which is `documents._resolvable`'s
    refusal one level up. And a role may CONSUME a result no role it depends
    on PRODUCES -- which is the worse of the two, because the dependency graph
    is satisfiable and the stage still cannot do its work. An independent
    review that is eligible and has no candidate to read is exactly the shape
    this template exists to make impossible.

    AND IT IS NOT `boundaries.document`, deliberately. That owner exists to
    ADOPT a document crossing a trust boundary, and `own` is how it does it --
    which refuses a tuple, because a tuple is not JSON data. A template
    declaration is not a crossing document: it is this build's own frozen
    source, its sequences are tuples precisely so nothing can append to the
    table every later Job resolves against, and the right check for it is the
    one `documents` performs on its own vocabularies.
    """
    taken = _exactly(definition, TEMPLATE_MEMBERS, "a job template")
    version = boundaries.text(taken["version"], "a template version")
    if taken["terminal_policy"] not in documents.TERMINAL_POLICIES:
        _refuse(f"template {name_value(version)} names the terminal policy "
                f"{name_value(taken['terminal_policy'])}, which is not one of "
                f"{', '.join(documents.TERMINAL_POLICIES)}")
    for one in _entries(taken["permitted_overrides"],
                        f"template {version}'s permitted overrides"):
        if one not in OVERRIDE_MEMBERS:
            _refuse(f"template {name_value(version)} permits the override "
                    f"{name_value(one)}, and this build resolves "
                    f"{', '.join(OVERRIDE_MEMBERS)}; an override nothing "
                    f"applies is a selection a request would be told it made")
    roles = _entries(taken["roles"], f"template {version}'s roles")
    if not roles:
        _refuse(f"template {name_value(version)} carries no role; a Job with "
                f"no stage is not a workflow")
    if len(roles) > documents.MAX_STAGES:
        _refuse(f"template {name_value(version)} carries {len(roles)} roles "
                f"and a Job admits {documents.MAX_STAGES} stages")
    named = {}
    for one in roles:
        role = _exactly(one, ROLE_MEMBERS,
                        f"a role of template {version}")
        name = boundaries.text(role["role"], "a template role name")
        for member in ("depends_on", "consumes", "produces"):
            role[member] = _entries(
                role[member], f"template {version}'s role {name}'s {member}")
        if name in named:
            _refuse(f"template {name_value(version)} names the role "
                    f"{name_value(name)} twice; one role naming two stages is "
                    f"the conflict this table refuses rather than resolves")
        if role["kind"] not in documents.STAGE_KINDS:
            _refuse(f"template {name_value(version)}'s role "
                    f"{name_value(name)} names the stage kind "
                    f"{name_value(role['kind'])}, which is not one of "
                    f"{', '.join(documents.STAGE_KINDS)}")
        named[name] = role
    # ONE STAGE OF EACH KIND, because that is what a stage identity IS.
    # `documents.stage_id` derives it from the Job and the kind, so two roles
    # on one kind would be two stages this build cannot tell apart -- and
    # `documents._job` refuses the submission rather than the template, which
    # is the wrong place to discover it.
    kinds = [role["kind"] for role in named.values()]
    if len(set(kinds)) != len(kinds):
        _refuse(f"template {name_value(version)} carries two roles of one "
                f"stage kind; a stage is identified by its Job and its kind, "
                f"so the two would resolve to one stage identity")
    for name, role in named.items():
        missing = [one for one in role["depends_on"] if one not in named]
        if missing:
            _refuse(f"template {name_value(version)}'s role "
                    f"{name_value(name)} gates on "
                    f"{', '.join(name_value(one) for one in missing)}, which "
                    f"it does not carry; a gate nothing in the Job can open "
                    f"is never eligible")
        if name in role["depends_on"]:
            _refuse(f"template {name_value(version)}'s role "
                    f"{name_value(name)} gates on itself")
        supplied = set()
        for upstream in role["depends_on"]:
            supplied |= set(named[upstream]["produces"])
        unsupplied = sorted(set(role["consumes"]) - supplied)
        if unsupplied:
            _refuse(f"template {name_value(version)}'s role "
                    f"{name_value(name)} consumes "
                    f"{', '.join(name_value(one) for one in unsupplied)}, "
                    f"which no role it depends on produces; a stage that is "
                    f"eligible and has no result to read cannot do its work, "
                    f"and a satisfiable dependency graph does not say it can")
    return taken


for _version, _definition in TEMPLATES.items():
    # The key and the entry's own `version` are held together, because a table
    # whose key says one revision and whose body says another is one nobody
    # could pin a resolution to.
    assert _version == _definition["version"], _version
    check_template(_definition)
del _version, _definition


def template_of(version):
    """One template this build carries, selected by its exact version.

    An unknown version REFUSES and names what this build holds. Guessing the
    nearest one would resolve a Job under a workflow nobody selected, which is
    the whole reason the version is in the name.
    """
    boundaries.text(version, "a job template version")
    if version not in TEMPLATES:
        _refuse(f"this build carries the job templates "
                f"{', '.join(name_value(one) for one in sorted(TEMPLATES))}; "
                f"{name_value(version)} is not one of them. A template this "
                f"build does not hold is a workflow it cannot resolve, and "
                f"resolving the nearest one would run a Job under stages, "
                f"gates and rules nobody selected")
    return TEMPLATES[version]


def submission_id_for(job_id):
    """The submission identity a request that states none resolves to.

    `fresh_attempt.admit`'s own derivation, spelled the same way, so the two
    ways a Job identity reaches this store derive one name rather than two.
    """
    return f"sub-{boundaries.identity(job_id, 'a Job id')}"


def resolve(request, *, configuration=None):
    """One request, resolved against one frozen template and one deployment.

    Answers a `baton.v12.job-template-resolution/1` document whose
    `submission` member is a normalized submission this build has already run
    through `documents.owned_submission`. Nothing is written, nothing is
    locked and no store is opened: admission is `submission.submit`'s and the
    operation that reaches it is W361912's.
    """
    # THE SECRET CHECK IS FIRST, which is `check_no_durable_secret`'s own rule
    # for wherever both apply. A request carries prose an operator pasted and
    # this answer is composed to be recorded, so a credential in it has to be
    # refused AS one rather than as whatever structural fault is also present.
    check_no_durable_secret(request, "a job template request")
    taken = boundaries.document(request, "a job template request",
                                required=REQUEST_MEMBERS,
                                optional=REQUEST_OPTIONAL)
    if taken["schema"] != REQUEST_SCHEMA:
        _refuse(f"a job template request is {name_value(REQUEST_SCHEMA)}; "
                f"this is {name_value(taken['schema'])}")
    held = _configuration(configuration)
    # EXPLICIT BEATS CONFIGURED AND BOTH ARE SHOWN. The origin travels with
    # the version because "a configured default may save typing but MUST NOT
    # hide that selection", and a reader handed a version alone cannot tell
    # whether this caller chose it or inherited it.
    if "template" in taken:
        version = boundaries.text(taken["template"],
                                  "a job template version")
        origin = SELECTION_ORIGINS[0]
    else:
        version = held["default_template"]
        origin = SELECTION_ORIGINS[1]
    definition = template_of(version)

    task = _task(taken["task"])
    source = _source(taken["source"])
    scope = _scope(taken["scope"], task["job_id"])
    acceptance = _acceptance(taken["acceptance"])
    # `taken.get` WOULD HAVE READ A PRESENT NULL AS AN ABSENT MEMBER, which
    # is the distinction this contract keeps everywhere else -- including one
    # level down, where `execution_limits: null` is refused as "neither". A
    # request that wrote `overrides: null` stated something, and reading it as
    # silence would answer a resolution it did not ask for.
    overrides = _overrides(taken["overrides"] if "overrides" in taken
                           else _ABSENT, definition)
    stages = _stages(definition, task, held["profiles"])
    submission = _submission(definition, task, source, scope, stages,
                             overrides)
    answer = {
        "schema": RESOLUTION_SCHEMA,
        "template": {"version": definition["version"], "origin": origin,
                     "permitted_overrides":
                         list(definition["permitted_overrides"])},
        # THE REQUEST'S OWN FOUR, PRESERVED EXACTLY. The submission has
        # nowhere to carry a statement or an acceptance criterion -- it names
        # Jobs, identities, stages, profiles, scope and policy, and SHOULD
        # not grow prose members -- so what the Work was asked for and what it
        # will be judged against live here, in the document a later admission
        # records. This leaf ENFORCES nothing with either, which is the same
        # split `documents._job` states for the test scope it stores.
        "task": task,
        "source": source,
        "scope": list(scope),
        "acceptance": list(acceptance),
        # The selections the request actually made, beside the permitted set
        # above. WHERE each resolved ceiling came from is not restated here:
        # `execution_limits.resolved` already reports `job` or `compatibility`
        # per boundary, and a second account of one fact is the one that goes
        # stale.
        "overrides": overrides,
        "stages": stages,
        "rules": {"completion": _rule(definition["completion"]),
                  "correction": _rule(definition["correction"]),
                  "failure": _rule(definition["failure"])},
        # RESOLVED THROUGH THE GENERATION THIS BUILD ADMITS, and the
        # generation is IN the answer. `execution_limits` learned this under
        # review: a Job that resolved against read-time constants reported
        # 3600 and then 7200 the moment a newer default existed, while its
        # identical submission still replayed.
        "execution_limits": execution_limits.resolved(
            overrides.get("execution_limits"),
            execution_limits.CURRENT_GENERATION),
        "submission": submission,
    }
    # OWNED ON THE WAY OUT, as the thing it is: an exact built-in document a
    # caller cannot reach back into and this module cannot leak a live
    # reference out of. It also proves the whole answer is within the frozen
    # structural bounds, which is what makes `resolution_digest` able to
    # exist at all.
    return own(answer, what="a job template resolution")


def _rule(held):
    """One rule document, copied into built-in lists.

    The table's sequences are tuples so nobody can append to them through an
    answer; `own` refuses a tuple, so the copy is not optional.
    """
    return {name: (list(value) if type(value) is tuple else value)
            for name, value in held.items()}


def _configuration(configuration):
    """The deployment's half, owned, with this build's answers for absences.

    A caller that supplies NONE gets this build's own default template and no
    profiles -- which resolves nothing, because every role needs one and the
    refusal below names the role. That is deliberate: a resolution with an
    invented profile digest would be admitted by `documents` and matched
    against the installed pool by `scheduler.reserve`, where it would fail as
    "no eligible worker" long after the operator could tell why.
    """
    if configuration is None:
        configuration = {"schema": CONFIGURATION_SCHEMA, "profiles": {}}
    taken = boundaries.document(configuration, "a job template configuration",
                                required=CONFIGURATION_MEMBERS,
                                optional=CONFIGURATION_OPTIONAL)
    if taken["schema"] != CONFIGURATION_SCHEMA:
        _refuse(f"a job template configuration is "
                f"{name_value(CONFIGURATION_SCHEMA)}; this is "
                f"{name_value(taken['schema'])}")
    default = taken.get("default_template", DEFAULT_TEMPLATE)
    # THE CONFIGURED DEFAULT IS PROVED HERE, not when a bare request happens
    # to reach it. A deployment whose default names a template this build does
    # not carry is misconfigured for every request, and discovering that on
    # the first one that omits a selection makes it look like that request's
    # fault.
    template_of(default)
    # The profile table is keyed by STAGE KIND, closed to the kinds this build
    # knows. It is deliberately not keyed by template role: a deployment
    # configures its installed workers once and several template revisions
    # read the same table, so an entry for a kind the SELECTED template does
    # not carry is a legitimate configuration rather than an error. What is
    # not legitimate is a key that is not a stage kind at all.
    profiles = boundaries.document(taken["profiles"],
                                   "a job template configuration's profiles",
                                   optional=documents.STAGE_KINDS)
    return {"default_template": default,
            "profiles": {kind: _profile(kind, profiles[kind])
                         for kind in profiles}}


def _profile(kind, entry):
    taken = boundaries.document(entry, f"the {kind} runtime profile",
                                required=PROFILE_MEMBERS)
    return {"profile_name": boundaries.text(taken["profile_name"],
                                            "a requested profile name"),
            "profile_digest": boundaries.text(taken["profile_digest"],
                                              "a requested profile digest")}


def _task(entry):
    taken = boundaries.document(entry, "a job template request's task",
                                required=TASK_MEMBERS,
                                optional=TASK_OPTIONAL)
    job_id = boundaries.identity(taken["job_id"], "a Job id")
    # ONE WORK FOR THE WHOLE JOB, which is the fact a generic parser cannot
    # enforce and a hand-authored document gets wrong. A development line is
    # one `(authority_uuid, work_id)` pair and the independent reviewer is an
    # assignment of that same Work, so a Job whose stages named two Works
    # would parse and never attach.
    work_id = boundaries.text(taken["work_id"], "the Work a Job runs under")
    statement = boundaries.text(taken["statement"], "a task statement")
    if len(statement) > MAX_STATEMENT:
        _refuse(f"a task statement is at most {MAX_STATEMENT} characters and "
                f"this is {len(statement)}; the authoritative statement is "
                f"the Work's own dossier and this is the request's record of "
                f"what was asked, not a second place to keep it")
    return {"job_id": job_id, "work_id": work_id,
            "submission_id": (boundaries.identity(taken["submission_id"],
                                                  "a submission id")
                              if "submission_id" in taken
                              else submission_id_for(job_id)),
            "statement": statement}


def _source(entry):
    """The Job's immutable input identity, which is what SOURCE means here.

    `documents._job` requires an `input_digest` and a `policy_digest` per Job
    and `integration.admission` correlates a producing worker's own runtime
    manifest against them. Neither is computed here: this module walks no
    tree, opens no store and reaches no manifest -- the digests are facts a
    source profile and a policy already established, and inventing either
    would put a syntactically valid placeholder where a reader expects
    evidence.
    """
    taken = boundaries.document(entry, "a job template request's source",
                                required=SOURCE_MEMBERS)
    return {"input_digest": boundaries.text(taken["input_digest"],
                                            "a Job's input digest"),
            "policy_digest": boundaries.text(taken["policy_digest"],
                                             "a Job's policy digest")}


def _scope(value, job_id):
    """The bounded test-change scope, as the submission's own path set.

    `documents._paths` is the rule and it is reached rather than restated:
    `check_relative_path` refuses anything that climbs out of the repository
    and a duplicate is refused because two spellings of one authority set are
    two things a reviewer could be reading. An EMPTY scope is legitimate --
    it is a Work that changes no test -- and that is why this is a list rather
    than a non-empty one.
    """
    if type(value) is not list:
        _refuse(f"a job template request's scope is a list of "
                f"repository-relative paths, empty when the Work changes no "
                f"test; this is {name_value(value)}")
    if len(value) > documents.MAX_JOBS:
        _refuse(f"a job template request's scope names {len(value)} paths and "
                f"a Job admits {documents.MAX_JOBS}")
    held = [check_relative_path(one, "a test-scope path") for one in value]
    if len(set(held)) != len(held):
        _refuse(f"Job {name_value(job_id)}'s scope names a test-scope path "
                f"more than once; one authority set has one spelling")
    return held


def _acceptance(value):
    """The acceptance criteria, preserved and enforced by nothing here.

    REV-2 gives an independent reviewer "a frozen candidate, selected
    requirement and test contract"; this is the selected requirement, carried
    where the resolution can be recorded with it. It is prose and it is
    bounded, for the reason every other bound in this package exists.
    """
    if type(value) is not list or value == []:
        _refuse(f"a job template request's acceptance is a non-empty list of "
                f"criteria; this is {name_value(value)}. A Job with nothing "
                f"to be judged against cannot be independently reviewed, "
                f"which is the stage this template's second role is")
    if len(value) > MAX_ACCEPTANCE:
        _refuse(f"a job template request states {len(value)} acceptance "
                f"criteria and this build admits {MAX_ACCEPTANCE}")
    held = []
    for one in value:
        criterion = boundaries.text(one, "an acceptance criterion")
        if len(criterion) > ACCEPTANCE_LIMIT:
            _refuse(f"an acceptance criterion is at most {ACCEPTANCE_LIMIT} "
                    f"characters and this is {len(criterion)}")
        held.append(criterion)
    if len(set(held)) != len(held):
        _refuse("a job template request states one acceptance criterion more "
                "than once; a duplicated requirement is one a reviewer could "
                "read as two")
    return held


def _overrides(value, definition):
    """The request's explicit overrides, held to the template's permitted set.

    AN ABSENT MEMBER AND AN EMPTY OBJECT BOTH RESOLVE TO THE PRESERVED
    DEFAULTS, and a FORBIDDEN one refuses rather than being dropped. Dropping
    it would hand back a resolution the caller believes carries a choice it
    does not -- which is the same defect `boundaries._members` refuses extra
    members for, at the one place a caller is actively trying to change
    behaviour.
    """
    permitted = definition["permitted_overrides"]
    if value is _ABSENT:
        return {}
    if type(value) is not dict:
        _refuse(f"a job template request's overrides are an object of "
                f"explicit selections, omitted entirely when the request "
                f"makes none; this is {name_value(value)}")
    # THE REFUSAL NAMES WHAT THIS TEMPLATE PERMITS, which `_members`' generic
    # one does not. A caller stating a forbidden override is actively trying
    # to change behaviour, and "that member is not named" sends them looking
    # for a spelling mistake when the answer is that the stage set, the
    # dependency, the terminal policy and the output contracts are the
    # template's and no request moves them.
    forbidden = sorted(one for one in value if one not in permitted)
    if forbidden:
        _refuse(f"template {name_value(definition['version'])} permits the "
                f"overrides {', '.join(name_value(one) for one in permitted)} "
                f"and this request states "
                f"{', '.join(name_value(one) for one in forbidden)}; the "
                f"stages, the gates, the terminal policy and the result "
                f"contracts are the template's, and a request that could "
                f"move them would be the operator-authored per-Job manifest "
                f"this creation path exists to remove")
    taken = boundaries.document(value, "a job template request's overrides",
                                optional=permitted)
    held = {}
    if "execution_limits" in taken:
        # `None` HERE IS NOT AN OMITTED OVERRIDE, which is the correction
        # `documents._job` already carries for the submission's own member:
        # `owned_execution_limits(None)` is an internal convenience for a Job
        # that stated nothing, and calling it for a member the request really
        # carries would admit `execution_limits: null` and preserve that null
        # as a selection.
        if taken["execution_limits"] is None:
            _refuse(f"a request's execution_limits override is an object of "
                    f"settings, omitted entirely when the request configures "
                    f"nothing; this is {name_value(None)}, which is neither")
        held["execution_limits"] = execution_limits.owned_execution_limits(
            taken["execution_limits"])
    return held


def _stages(definition, task, profiles):
    """The template's roles, resolved into this Job's stages.

    Every member here is either the template's or the deployment's. The
    request supplies none of them: it named a task, and which stages that task
    owes, which gates them and which worker profile each one requests is what
    selecting a template MEANS.
    """
    job_id = task["job_id"]
    kinds = {role["role"]: role["kind"] for role in definition["roles"]}
    held = []
    for role in definition["roles"]:
        kind = role["kind"]
        if kind not in profiles:
            _refuse(f"template {name_value(definition['version'])} carries a "
                    f"{kind} stage and this deployment configures no {kind} "
                    f"runtime profile; the profile a stage requests is "
                    f"matched against the installed pool, so an operator "
                    f"cannot supply one and a Job must not invent one")
        profile = profiles[kind]
        held.append({
            "role": role["role"],
            "kind": kind,
            "stage_id": documents.stage_id(job_id, kind),
            # ONE WORK, EVERY STAGE. See `_task`.
            "work_id": task["work_id"],
            "profile_name": profile["profile_name"],
            "profile_digest": profile["profile_digest"],
            "depends_on": [{"job_id": job_id, "kind": kinds[one]}
                           for one in role["depends_on"]],
            "consumes": list(role["consumes"]),
            "produces": list(role["produces"]),
        })
    return held


def _submission(definition, task, source, scope, stages, overrides):
    """The normalized submission, PROVED BY ITS REAL OWNER before it is
    answered.

    `documents.owned_submission` is the contract `submission.submit` reaches,
    so running the composed document through it here is what makes "this
    resolution is submittable" a fact rather than an intention -- and a defect
    in this composition surfaces at the request that caused it rather than at
    whatever later call tried to submit it. It is also what returns the
    document in THIS BUILD'S member order, which is the identity a
    resubmission is compared against.

    ONE JOB PER REQUEST. A request names one task, and bundling several into
    one submission would make one caller's refusal another caller's -- which
    is the atomicity `submission._unclaimed` keeps for the document it is
    given, not a property this module should quietly widen.
    """
    entry = {"job_id": task["job_id"],
             "input_digest": source["input_digest"],
             "policy_digest": source["policy_digest"],
             "test_scope": list(scope),
             "terminal_policy": definition["terminal_policy"],
             "stages": [{"kind": stage["kind"], "work_id": stage["work_id"],
                         "profile_name": stage["profile_name"],
                         "profile_digest": stage["profile_digest"],
                         "depends_on": [dict(gate)
                                        for gate in stage["depends_on"]]}
                        for stage in stages]}
    # THE OPTIONAL MEMBER IS PRESENT ONLY WHEN THE REQUEST STATED IT, and the
    # schema is chosen to match. A `/1` document may not carry the member at
    # all, so a request that overrides nothing resolves to `/1` -- the exact
    # document, and the exact durable identity, that this pipeline already
    # admits -- and only a request that configures a ceiling needs `/2`.
    # Rewriting every Job as `/2` would give one intent two identities and
    # would hand a reader a configured member for a Job that configured
    # nothing.
    if "execution_limits" in overrides:
        entry["execution_limits"] = dict(overrides["execution_limits"])
        schema = documents.SUBMISSION_SCHEMA
    else:
        schema = documents.SUBMISSION_SCHEMAS[0]
    document = {"schema": schema, "submission_id": task["submission_id"],
                "jobs": [entry]}
    owned = documents.owned_submission(document)
    _agrees(definition, task, stages, owned)
    return owned


def _agrees(definition, task, stages, owned):
    """The normalized document still encodes the template's declared graph.

    WHY THIS IS CHECKED AFTER NORMALIZATION RATHER THAN TRUSTED BEFORE IT.
    `owned_submission` is a separately owned contract with its own refusals,
    its own member order and its own bounds, and this module's whole claim is
    that a resolved template produces a submittable document -- so the claim
    is made against the document that actually came back, not against the one
    that went in. A mismatch here is this module's defect, surfaced before a
    caller can record it.
    """
    entry = owned["jobs"][0]
    declared = {documents.stage_id(task["job_id"], stage["kind"]):
                sorted(documents.stage_id(gate["job_id"], gate["kind"])
                       for gate in stage["depends_on"])
                for stage in stages}
    resolved = {documents.stage_id(entry["job_id"], stage["kind"]):
                sorted(documents.stage_id(gate["job_id"], gate["kind"])
                       for gate in stage["depends_on"])
                for stage in entry["stages"]}
    if declared != resolved:
        _refuse(f"template {name_value(definition['version'])} declares the "
                f"stage dependencies {declared} and the normalized submission "
                f"carries {resolved}; a resolution whose document does not "
                f"encode the selected template's own graph is this build's "
                f"defect and is refused rather than answered")
    for stage in stages:
        if stage["work_id"] != task["work_id"]:
            _refuse(f"stage {name_value(stage['stage_id'])} resolved onto a "
                    f"Work other than the task's; one Job is one development "
                    f"line and its reviewer is an assignment of that same "
                    f"Work")


def resolution_digest(resolution):
    """The durable identity of one resolved intent.

    The canonical digest of the whole answer -- selection, origin, preserved
    request, resolved stages, rules, effective limits and submission -- so a
    later admission can bind the exact resolution it consumed. It is NOT the
    submission's identity: `documents.submission_signature` is that, and the
    two are different facts, because two resolutions that differ only in a
    preserved acceptance criterion carry one submission.
    """
    return digest(own(resolution, what="a job template resolution"))
